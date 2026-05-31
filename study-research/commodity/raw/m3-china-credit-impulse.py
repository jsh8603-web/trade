# -*- coding: utf-8 -*-
"""
M3 누락지표 실 study: China credit impulse → commodity 수익률 상관/Rank-IC
=========================================================================
사용자 정정(2026-05-31): register≠지표추가. 최초 M3 흐름(이론→실데이터→상관→yaml) 그대로.

★5 금지 준수:
  ② 합성·시뮬 데이터 금지 → 실데이터만(FRED public CSV, 키 불요). fetch 실패 시 raise(합성 대체 X).
  ⑤ small-N 단정 금지 → n·p·Newey-West HAC·block-bootstrap CI·lag별 Bonferroni 전부 박제.

데이터(전부 FRED public CSV endpoint = API key 불요):
  - China 신용:  QCNPAM770A = Credit to Private Non-Financial Sector from All sectors,
                 Adjusted for Breaks, China, % of GDP, Quarterly (BIS 원천).
                 (대체 후보: QCNPAMUSDA = USD bn 절대액)
  - copper:      PCOPPUSDM = Global price of Copper, USD/metric ton, Monthly (IMF 원천)
  - 산업금속:    PINDUINDEXM = Global price index of Industrial Materials, Monthly (대체: PALLFNFINDEXM)

credit impulse 정의(실데이터 한계 명시):
  R_t = credit-to-GDP ratio(%). BIS 비율 = stock 기반.
  - flow4  = R_t - R_{t-4}            (4q 변화 = leverage 증분, '신용 갭 flow' loose impulse)
  - biggs  = (R_t-R_{t-4})-(R_{t-4}-R_{t-8})  (Biggs et al. 2009 acceleration = 정통 credit impulse)
  ★TSF flow/GDP 가 gold standard 이나 FRED 미보유 → BIS 비율 proxy. spec/code 1:1 라벨 박제.
"""
import io
import sys
import json
import urllib.request
import numpy as np
import pandas as pd

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"


def fetch_fred(sid):
    """FRED public CSV (no API key). 실패 시 raise — 합성 대체 절대 금지(5금지 ②)."""
    url = FRED_CSV.format(sid=sid)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (M3-study)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8")
    df = pd.read_csv(io.StringIO(raw))
    # FRED CSV: 컬럼 = [observation_date 또는 DATE, <SID>]
    date_col = df.columns[0]
    val_col = df.columns[1]
    df[date_col] = pd.to_datetime(df[date_col])
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
    s = df.set_index(date_col)[val_col].dropna()
    s.name = sid
    if len(s) < 8:
        raise RuntimeError(f"{sid}: 관측 {len(s)}개 — 실데이터 부족, 합성 대체 금지 → 중단")
    return s


def spearman_with_pvalue(x, y):
    from scipy import stats
    rho, p = stats.spearmanr(x, y)
    return rho, p, len(x)


def newey_west_tstat_pearson(x, y, lags):
    """overlapping forward-return 회귀 b의 Newey-West HAC t-stat (자기상관 보정)."""
    import statsmodels.api as sm
    X = sm.add_constant(np.asarray(x, float))
    model = sm.OLS(np.asarray(y, float), X).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    beta = model.params[1]
    t_hac = model.tvalues[1]
    p_hac = model.pvalues[1]
    ci = model.conf_int(alpha=0.05)[1]
    return beta, t_hac, p_hac, (ci[0], ci[1])


def block_bootstrap_ci(x, y, block, n_boot=5000, seed=12345):
    """stationary/circular block bootstrap → Spearman rho 95% CI (자기상관 보정)."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = len(x)
    from scipy import stats
    rhos = []
    n_blocks = int(np.ceil(n / block))
    for _ in range(n_boot):
        starts = rng.integers(0, n, size=n_blocks)
        idx = np.concatenate([(np.arange(s, s + block) % n) for s in starts])[:n]
        rhos.append(stats.spearmanr(x[idx], y[idx]).correlation)
    rhos = np.array([r for r in rhos if np.isfinite(r)])
    return float(np.percentile(rhos, 2.5)), float(np.percentile(rhos, 97.5))


def main():
    out = {"meta": {}, "series": {}, "tests": [], "verdict": {}}

    # ---- 1. 실데이터 수집 ----
    credit = None
    for sid in ["QCNPAM770A", "QCNPAMUSDA"]:
        try:
            credit = fetch_fred(sid)
            out["series"]["credit"] = {"id": sid, "n": int(len(credit)),
                                       "start": str(credit.index[0].date()),
                                       "end": str(credit.index[-1].date())}
            break
        except Exception as e:
            out["series"].setdefault("credit_errors", []).append(f"{sid}: {e}")
    if credit is None:
        out["verdict"] = {"status": "INSUFFICIENT", "reason": "China 신용 실데이터 fetch 전부 실패 — 합성 금지로 중단"}
        print(json.dumps(out, ensure_ascii=False, indent=2)); return

    commodities = {}
    for name, candidates in {
        "copper": ["PCOPPUSDM"],
        "industrial": ["PINDUINDEXM", "PALLFNFINDEXM"],
    }.items():
        for sid in candidates:
            try:
                commodities[name] = fetch_fred(sid)
                out["series"][name] = {"id": sid, "n": int(len(commodities[name])),
                                       "start": str(commodities[name].index[0].date()),
                                       "end": str(commodities[name].index[-1].date())}
                break
            except Exception as e:
                out["series"].setdefault(f"{name}_errors", []).append(f"{sid}: {e}")

    if not commodities:
        out["verdict"] = {"status": "INSUFFICIENT", "reason": "commodity 가격 실데이터 fetch 실패"}
        print(json.dumps(out, ensure_ascii=False, indent=2)); return

    # ---- 2. credit impulse 구성 (분기) ----
    R = credit.resample("QE").last().dropna()  # quarter-end 비율
    flow4 = (R - R.shift(4)).rename("flow4")            # loose impulse
    biggs = (R - R.shift(4)) - (R.shift(4) - R.shift(8))  # Biggs acceleration
    biggs = biggs.rename("biggs")

    impulses = {"flow4_creditgap": flow4, "biggs_acceleration": biggs}

    # ---- 3. forward 수익률 정렬 + 상관/Rank-IC (lag = 1..6 분기 forward) ----
    LAGS_Q = [1, 2, 3, 4, 5, 6]  # forward quarters
    raw_pvals = []
    for cname, cseries in commodities.items():
        cq = cseries.resample("QE").last().dropna()
        for iname, impulse in impulses.items():
            imp = impulse.dropna()
            for fq in LAGS_Q:
                fwd_ret = (cq.shift(-fq) / cq - 1.0).rename("fwd")
                df = pd.concat([imp.rename("imp"), fwd_ret], axis=1).dropna()
                if len(df) < 20:
                    continue
                rho, p, n = spearman_with_pvalue(df["imp"], df["fwd"])
                nw_lags = max(fq, int(np.ceil(n ** 0.25)))  # overlap = fq 분기
                try:
                    beta, t_hac, p_hac, ci_hac = newey_west_tstat_pearson(df["imp"], df["fwd"], nw_lags)
                except Exception as e:
                    beta = t_hac = p_hac = None; ci_hac = (None, None)
                try:
                    bb_lo, bb_hi = block_bootstrap_ci(df["imp"].values, df["fwd"].values,
                                                      block=max(fq, 4))
                except Exception:
                    bb_lo, bb_hi = None, None
                rec = {
                    "commodity": cname, "impulse": iname, "fwd_quarters": fq,
                    "n": int(n), "spearman_rho": round(float(rho), 4),
                    "spearman_p_raw": round(float(p), 5),
                    "nw_beta": (round(float(beta), 5) if beta is not None else None),
                    "nw_tstat_hac": (round(float(t_hac), 3) if t_hac is not None else None),
                    "nw_p_hac": (round(float(p_hac), 5) if p_hac is not None else None),
                    "nw_ci95": [None if ci_hac[0] is None else round(float(ci_hac[0]), 5),
                                None if ci_hac[1] is None else round(float(ci_hac[1]), 5)],
                    "block_boot_rho_ci95": [bb_lo if bb_lo is None else round(bb_lo, 4),
                                            bb_hi if bb_hi is None else round(bb_hi, 4)],
                }
                out["tests"].append(rec)
                raw_pvals.append(rec["spearman_p_raw"])

    # ---- 4. 다중비교 보정 (Bonferroni + BH-FDR) ----
    m = len(raw_pvals)
    if m:
        bonf_alpha = 0.05 / m
        out["meta"]["multiple_comparison"] = {
            "n_tests": m, "bonferroni_alpha": round(bonf_alpha, 6),
            "survive_bonferroni": [t for t in out["tests"] if t["spearman_p_raw"] < bonf_alpha],
        }
        # BH-FDR
        order = np.argsort(raw_pvals)
        bh = {}
        for rank, idx in enumerate(order, start=1):
            bh[idx] = raw_pvals[idx] * m / rank
        survive_fdr = [out["tests"][i] for i in range(m) if bh[i] < 0.05]
        out["meta"]["multiple_comparison"]["survive_bh_fdr_0.05"] = survive_fdr

    out["meta"]["effective_n_note"] = (
        "분기 데이터 + forward overlap → 자기상관 강함. Spearman raw-p 는 IID 가정 과대평가. "
        "Newey-West HAC p_hac + block bootstrap CI 가 실질 유의성. 단정은 양쪽 충족 시만."
    )
    out["meta"]["data_caveat"] = (
        "BIS credit-to-GDP(stock 비율) = TSF flow/GDP(gold standard)의 proxy. "
        "TSF FRED 미보유 → BIS 비율로 impulse 구성. spec/code 1:1: '신용 펄스'=credit-to-GDP 4q차분/acceleration."
    )

    # 정직한 verdict 후보(스크립트는 데이터만, 최종 라벨은 main 감사)
    survivors = out["meta"].get("multiple_comparison", {}).get("survive_bonferroni", [])
    out["verdict"] = {
        "status": "MEASURED",
        "n_tests": m,
        "bonferroni_survivors": len(survivors),
        "note": "verdict 라벨(CONFIRMED/STRUCTURAL/REJECT)은 main 이 small-N rigor 로 판정",
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))
    with open("study-research/commodity/raw/m3-china-credit-impulse-results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
