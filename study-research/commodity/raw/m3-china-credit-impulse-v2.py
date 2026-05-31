# -*- coding: utf-8 -*-
"""
M3 누락지표 실 study v2: China credit impulse → commodity(copper) 수익률 상관/Rank-IC
DBnomics 경유 실데이터 (FRED 호스트 timeout 회피). BIS·IMF 원천 = 합성 아님.

데이터 (전부 DBnomics, 키 불요):
  - BIS/WS_TC/Q.CN.P.A.M.770.A   = China 민간비금융 Credit-to-GDP %, break 조정 (분기) — impulse 원천
  - BIS/WS_CREDIT_GAP/Q.CN.P.A.C = China Credit-to-GDP gap (actual-trend), BIS 신용사이클 지표 (분기)
  - IMF/PCPS/M.W00.PCOPP.USD     = Global copper price USD/mt (월) — China 수요 bellwether

credit impulse (spec/code 1:1):
  R_t = credit-to-GDP %.
  - flow4_creditgrowth = R_t - R_{t-4}           (4q 변화 = 신용/GDP 증분, loose impulse)
  - biggs_accel        = (R_t-R_{t-4})-(R_{t-4}-R_{t-8})  (Biggs 2009 정통 credit impulse=가속도)
  - bis_gap_level      = WS_CREDIT_GAP 직접 (BIS 공식 신용갭, level 편차)

★5금지: 합성 금지(fetch 실패=raise) / small-N rigor(n·p·Newey-West HAC·block bootstrap·Bonferroni).
"""
import json
import urllib.request
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

DBN = "https://api.db.nomics.world/v22/series/{prov}/{ds}/{sc}?observations=1"


def fetch_dbnomics(prov, ds, sc):
    url = DBN.format(prov=prov, ds=ds, sc=sc)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (M3-study)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode("utf-8"))
    docs = d.get("series", {}).get("docs", [])
    if not docs:
        raise RuntimeError(f"{prov}/{ds}/{sc}: docs 비어있음 — 실데이터 없음, 합성 대체 금지 중단")
    doc = docs[0]
    periods = doc.get("period_start_day") or doc.get("period")
    values = doc.get("value")
    idx = pd.to_datetime(periods)
    s = pd.Series([np.nan if v is None else float(v) for v in values], index=idx).dropna()
    s.name = sc
    if len(s) < 8:
        raise RuntimeError(f"{sc}: 관측 {len(s)} — 부족, 중단")
    return s


def block_bootstrap_ci(x, y, block, n_boot=4000, seed=7):
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float); y = np.asarray(y, float); n = len(x)
    nb = int(np.ceil(n / block)); rhos = []
    for _ in range(n_boot):
        starts = rng.integers(0, n, size=nb)
        idx = np.concatenate([(np.arange(s, s + block) % n) for s in starts])[:n]
        rr = stats.spearmanr(x[idx], y[idx]).correlation
        if np.isfinite(rr): rhos.append(rr)
    return float(np.percentile(rhos, 2.5)), float(np.percentile(rhos, 97.5))


def main():
    out = {"data_caveat": (
        "BIS credit-to-GDP(분기 stock 비율) = TSF flow/GDP(gold standard)의 accessible 실 proxy. "
        "TSF 직접 시리즈 공개 API 부재 → BIS 비율로 impulse 구성. spec/code 1:1 라벨 박제."),
        "series": {}, "tests": [], "meta": {}, "verdict": {}}

    # 1. 실데이터
    try:
        ratio = fetch_dbnomics("BIS", "WS_TC", "Q.CN.P.A.M.770.A")
        gap = fetch_dbnomics("BIS", "WS_CREDIT_GAP", "Q.CN.P.A.C")
        copper = fetch_dbnomics("IMF", "PCPS", "M.W00.PCOPP.USD")
    except Exception as e:
        out["verdict"] = {"status": "INSUFFICIENT", "reason": f"실데이터 fetch 실패: {e}"}
        print(json.dumps(out, ensure_ascii=False, indent=2)); return

    for nm, s in [("credit_to_gdp", ratio), ("bis_credit_gap", gap), ("copper", copper)]:
        out["series"][nm] = {"n": int(len(s)), "start": str(s.index[0].date()), "end": str(s.index[-1].date())}

    # 2. impulse 구성 (분기 정렬)
    R = ratio.resample("QE").last().dropna()
    G = gap.resample("QE").last().dropna()
    impulses = {
        "flow4_creditgrowth": (R - R.shift(4)).dropna(),
        "biggs_accel": ((R - R.shift(4)) - (R.shift(4) - R.shift(8))).dropna(),
        "bis_gap_level": G,
    }
    cq = copper.resample("QE").last().dropna()

    # 3. forward 수익률 상관/Rank-IC (lag 1..6 분기 forward)
    raw_p = []
    for iname, imp in impulses.items():
        for fq in [1, 2, 3, 4, 5, 6]:
            fwd = (cq.shift(-fq) / cq - 1.0).rename("fwd")
            df = pd.concat([imp.rename("imp"), fwd], axis=1).dropna()
            if len(df) < 20:
                continue
            rho, p = stats.spearmanr(df["imp"], df["fwd"]); n = len(df)
            # Newey-West HAC (overlap = fq 분기)
            X = sm.add_constant(df["imp"].values)
            m = sm.OLS(df["fwd"].values, X).fit(cov_type="HAC", cov_kwds={"maxlags": max(fq, 2)})
            ci = m.conf_int(alpha=0.05)[1]
            try:
                bb_lo, bb_hi = block_bootstrap_ci(df["imp"].values, df["fwd"].values, block=max(fq, 4))
            except Exception:
                bb_lo = bb_hi = None
            rec = {"impulse": iname, "fwd_q": fq, "n": int(n),
                   "spearman_rho": round(float(rho), 4), "spearman_p_raw": round(float(p), 5),
                   "nw_beta": round(float(m.params[1]), 5), "nw_t_hac": round(float(m.tvalues[1]), 3),
                   "nw_p_hac": round(float(m.pvalues[1]), 5),
                   "nw_ci95": [round(float(ci[0]), 5), round(float(ci[1]), 5)],
                   "boot_rho_ci95": [None if bb_lo is None else round(bb_lo, 4),
                                     None if bb_hi is None else round(bb_hi, 4)]}
            out["tests"].append(rec); raw_p.append(rec["spearman_p_raw"])

    # 4. 다중비교 보정
    m_ = len(raw_p)
    if m_:
        bonf = 0.05 / m_
        surv_b = [t for t in out["tests"] if t["spearman_p_raw"] < bonf]
        surv_hac = [t for t in out["tests"] if t["nw_p_hac"] < 0.05]
        order = np.argsort(raw_p)
        bh = {i: raw_p[i] * m_ / rank for rank, i in enumerate(order, 1)}
        surv_fdr = [out["tests"][i] for i in range(m_) if bh[i] < 0.05]
        out["meta"]["multiple_comparison"] = {
            "n_tests": m_, "bonferroni_alpha": round(bonf, 6),
            "survive_bonferroni_rawp": [(t["impulse"], t["fwd_q"], t["spearman_rho"], t["spearman_p_raw"]) for t in surv_b],
            "survive_newey_west_hac_p05": [(t["impulse"], t["fwd_q"], t["nw_t_hac"], t["nw_p_hac"]) for t in surv_hac],
            "survive_bh_fdr05": [(t["impulse"], t["fwd_q"], t["spearman_rho"]) for t in surv_fdr],
        }
    out["meta"]["note"] = ("분기+forward overlap → 자기상관 강함. raw Spearman-p 는 IID 과대평가. "
                           "실질 유의 = Newey-West HAC p_hac AND block bootstrap CI 0 미포함 동시.")
    out["verdict"] = {"status": "MEASURED",
                      "note": "verdict 라벨(CONFIRMED/STRUCTURAL/REJECT)은 main 이 small-N rigor 로 판정. "
                              "n<30 + HAC 미생존이면 structural_prior(저신뢰) 격하."}

    print(json.dumps(out, ensure_ascii=False, indent=2))
    with open("study-research/commodity/raw/m3-china-credit-impulse-results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
