# -*- coding: utf-8 -*-
"""measure_rotation_consumer.py — 소비재 업종 자체 rotation 신호 (fundamental driver, 이론→통계검증).

★rotation v2(_rotation/measure_rotation_v2.py)는 consumer 를 NO_DIRECT(고유 cycle 직접 부재)로 분류,
momentum proxy 만 썼다(rel_mom_6 reversal -0.328). 본 측정 = ★소비재 전문성으로 고유 cycle 직접지표 수집·측정:
  - 화장품(cosmetics) sub-cluster: 중국 경기/관광/면세 = ★中CLI / 항셍·상하이 / USDCNY (中구매력·따이공)
  - 음식료(food) sub-cluster: 곡물 cost(ZC/ZW/ZS) + 내수 소비
  - 전체(industry) eq-weight + sub-cluster 분리 패널 (A-4 이질 = 화장품 中cyclical vs 음식료 내수 defensive)

================================================================================
★이론 부호 사전확약 (측정 前 동결, theory-notes §1 + 증권사 소비재 리포트)
================================================================================
| driver | sub-cluster | 메커니즘 | 사전확약 부호 (forward) |
|---|---|---|---|
| 中CLI yoy | cosmetics | 중국 경기↑ → 화장품 중국 매출·따이공·면세 수요↑ | ★양(+) |
| 항셍/상하이 mom | cosmetics | 중국 주식 risk-on = 中소비 sentiment | ★양(+) |
| USDCNY (위안약세=CNY down) | cosmetics | 위안 강세(USDCNY↓) → 中구매력↑ → 화장품 OW | ★음(USDCNY와 -) |
| 곡물 yoy (ZC/ZW/ZS) | food | 곡물↑ → 음식료 COGS↑ → 마진↓ (cost-push) | ★음(-) (cross 측정 null) |
| 내수 소매판매 | food/retail | 내수↑ → 음식료/유통 매출↑ | ★양(+) (data 2024-03 제약) |
| rel_mom_6 reversal | industry | 내수 방어주 평균회귀 (rotation v2 발견 -0.328) | ★음(-, mean-reversion) |

★data mining 차단: 이론 근거 없는 신호 채택 불가. 위 6 driver = 전부 소비재 cycle 이론 사전확약.
================================================================================
★G-F 7항 = measure_rotation_v2.py 준용 (eff-n=block / 단일 BY-FDR / wild-cluster / t_obs⋚2.802 / PIT lag).
raw 재현: consumer prices.parquet(sub-cluster) + FRED中CLI/USDCNY + yfinance 항셍/곡물 + 본 .py.
"""
from __future__ import annotations
import sys, io, os, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import pandas as pd
from scipy import stats
import requests

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ENV = Path("D:/projects/Inv/.env")
if ENV.exists():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"'))
FRED = os.environ.get("FRED_API_KEY", "")

HORIZONS_M = {"y_20d": 1, "y_60d": 3}
OOS_SPLIT = "2023-01-01"
T_BREAKEVEN = 2.802
START, END = "2018-01-01", "2026-05-29"


# ──────── 통계 인프라 (measure_rotation_v2.py 동일) ────────
def nw_se(x, lag):
    n = len(x)
    if n < 3: return np.nan
    e = x - x.mean(); var = (e @ e) / n
    for k in range(1, min(lag, n - 1) + 1):
        var += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def n_eff_autocorr(x, max_lag=12):
    n = len(x)
    if n < 4: return float(n)
    e = x - x.mean(); v = (e @ e) / n
    if v <= 0: return float(n)
    s = 0.0
    for k in range(1, min(max_lag, n - 1) + 1):
        rk = (e[k:] @ e[:-k]) / n / v
        if rk <= 0: break
        s += (1 - k / (max_lag + 1)) * rk
    return float(n / (1 + 2 * s))


def wild_cluster_p(x, B=2000, seed=42):
    n = len(x)
    if n < 4: return np.nan
    rng = np.random.default_rng(seed); sd = x.std(ddof=1)
    t_obs = abs(x.mean() / (sd / np.sqrt(n))) if sd > 0 else 0.0
    e = x - x.mean(); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n); xn = w * e; sb = xn.std(ddof=1)
        tb = abs(xn.mean() / (sb / np.sqrt(n))) if sb > 0 else 0.0
        if tb >= t_obs: cnt += 1
    return (cnt + 1) / (B + 1)


def block_boot_ci(x, block, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block + 1: return [np.nan, np.nan]
    nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        means.append(np.concatenate([x[s:s + block] for s in st])[:n].mean())
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0: return {"m": 0, "note": "powered cell 0"}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1)); surv = []
    for ri, (k, p) in enumerate(items, 1):
        if p <= (ri / m) * q / c_m: surv = [items[j][0] for j in range(ri)]
    return {"m": m, "by_factor": round(c_m, 3), "survivors_BY": surv,
            "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0], "bonferroni_alpha": round(0.05 / m, 5)}


def signal_forward_stat(sig, fwd, h_months, label, expected_sign, oos_split=OOS_SPLIT):
    common = sig.dropna().index.intersection(fwd.dropna().index)
    if len(common) < 12:
        return {"label": label, "n": len(common), "status": "INSUFFICIENT(n<12)"}
    sv, fv = sig.loc[common].values, fwd.loc[common].values
    rho, _ = stats.spearmanr(sv, fv)
    sr = stats.rankdata(sv) / len(sv) - 0.5; fr = stats.rankdata(fv) / len(fv) - 0.5
    prod = sr * fr; n = len(prod)
    neff = n_eff_autocorr(prod); se = nw_se(prod, h_months)
    t_nw = prod.mean() / se if se and se > 0 else np.nan
    wc_p = wild_cluster_p(prod); ci = block_boot_ci(prod, max(2, h_months))
    t_power = abs(rho) * np.sqrt(max(neff, 1.0))
    powered = (n >= 24) and (neff >= 6) and (t_power >= T_BREAKEVEN)
    is_idx = [d for d in common if str(d) < oos_split]; oos_idx = [d for d in common if str(d) >= oos_split]
    oos = {"is_n": len(is_idx), "oos_n": len(oos_idx)}
    if len(is_idx) >= 8 and len(oos_idx) >= 8:
        rho_is = stats.spearmanr(sig.loc[is_idx].values, fwd.loc[is_idx].values)[0]
        rho_oos = stats.spearmanr(sig.loc[oos_idx].values, fwd.loc[oos_idx].values)[0]
        oos.update({"rho_is": round(float(rho_is), 4), "rho_oos": round(float(rho_oos), 4)})
        sign_hold = (np.sign(rho_is) == np.sign(rho_oos)) and abs(rho_oos) >= 0.5 * abs(rho_is)
        oos["eligible"] = bool(sign_hold and abs(rho_oos) > 0.02)
        oos["verdict"] = ("OOS 부호+mag 유지" if sign_hold else
                          ("OOS 부호유지 mag약" if np.sign(rho_is) == np.sign(rho_oos) else "OOS flip"))
    else:
        oos["eligible"] = None; oos["verdict"] = "OOS n<8"
    # ★이론 사전확약 부호 일치 검증 (data mining 차단)
    sign_match = None
    if expected_sign != 0 and not np.isnan(rho):
        sign_match = (np.sign(rho) == expected_sign)
    return {"label": label, "n": n, "n_eff": round(neff, 1), "spearman_rho": round(float(rho), 4),
            "expected_sign": expected_sign, "theory_sign_match": sign_match,
            "t_power_mde": round(float(t_power), 2),
            "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
            "ci95_block_boot_prod": [round(c, 5) for c in ci] if not np.isnan(ci[0]) else None,
            "walk_forward_oos": oos, "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT")}


# ──────── 데이터 로드 ────────
def fred_series(sid):
    r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                     params=dict(series_id=sid, api_key=FRED, file_type="json",
                                 observation_start=START, observation_end=END), timeout=40).json()
    idx, val = [], []
    for o in r.get("observations", []):
        if o["value"] in (".", ""): continue
        idx.append(pd.Timestamp(o["date"])); val.append(float(o["value"]))
    return pd.Series(val, index=idx).sort_index()


def yf_monthly(sym):
    import yfinance as yf
    s = yf.download(sym, start=START, end=END, progress=False, auto_adjust=True)["Close"].squeeze()
    s.index = pd.to_datetime(s.index)
    return s.resample("ME").last()


def ecos_csi(item):
    """ECOS 511Y002(소비자동향조사) item 월별 시계열 (분할 fetch, 500 row 제한 우회)."""
    ECOS = os.environ.get("ECOS_API_KEY", "")
    pieces = {}
    for yr in range(2018, 2027):
        url = (f"https://ecos.bok.or.kr/api/StatisticSearch/{ECOS}/json/kr/1/100/"
               f"511Y002/M/{yr}01/{yr}12/{item}")
        try:
            r = requests.get(url, timeout=30).json()
            for row in r.get("StatisticSearch", {}).get("row", []):
                t = row.get("TIME", ""); dv = row.get("DATA_VALUE", "")
                if t and dv not in ("", None):
                    pieces[pd.Timestamp(f"{t[:4]}-{t[4:6]}-01")] = float(dv)
        except Exception:
            pass
    if not pieces:
        return pd.Series(dtype=float)
    s = pd.Series(pieces).sort_index()
    return s.resample("ME").last()


def load_subcluster_panels():
    """consumer prices → 전체 + sub-cluster(cosmetics/food/retail) 월간 eq-weight 패널수익."""
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    uni = pd.read_parquet(DATA / "universe.parquet"); uni = uni[uni["pass_floor"]].set_index("Code")
    subcl = uni["subcl"].to_dict()
    pxm = px.resample("ME").last(); ret = pxm.pct_change()
    panels = {"industry": ret.mean(axis=1, skipna=True)}
    for sc in ["cosmetics", "food", "retail"]:
        codes = [c for c in px.columns if subcl.get(c) == sc]
        if len(codes) >= 3:
            panels[sc] = ret[codes].mean(axis=1, skipna=True)
    return panels


def main():
    panels = load_subcluster_panels()
    print(f"panels: {[(k, int(v.dropna().shape[0])) for k, v in panels.items()]}")

    # ── fundamental driver 수집 (사전검증 완료 source) ──
    print("[수집] FRED 中CLI / USDCNY ...")
    chn_cli = fred_series("CHNLOLITOAASTSAM")      # 중국 경기선행 (화장품 中수요)
    usdcny = fred_series("DEXCHUS")                # 위안 (中구매력)
    kor_retail = fred_series("KORSARTMISMEI")      # 한국 소매판매 (내수, 2024-03 제약)
    print("[수집] yfinance 항셍/상하이/곡물/ETF/유가 ...")
    hsi = yf_monthly("^HSI")                       # 항셍 (中 risk-on)
    sse = yf_monthly("000001.SS")                  # 상하이종합
    corn = yf_monthly("ZC=F"); wheat = yf_monthly("ZW=F"); soy = yf_monthly("ZS=F")
    xlp = yf_monthly("XLP")                         # 美방어소비 ETF
    xly = yf_monthly("XLY")                         # 美경기소비 ETF
    wti = yf_monthly("CL=F")                        # WTI 유가 (원가/소비여력)
    hk_travel = yf_monthly("1379.HK")              # 홍콩 (관광/면세 proxy, 약)
    print("[수집] ECOS CSI 소비심리 (소비지출/여행비/의류비/향후경기) ...")
    csi_spend = ecos_csi("FMCB")                    # 소비지출전망 CSI
    csi_travel = ecos_csi("FMCCD")                  # 여행비 지출전망 (리오프닝/면세)
    csi_cloth = ecos_csi("FMCCB")                   # 의류비 지출전망 (화장품/의류)
    csi_econ = ecos_csi("FMBB")                     # 향후경기전망 CSI

    # XLP/XLY 상대모멘텀 (글로벌 방어 vs 경기소비 = 한국 소비재 OW timing proxy)
    xlp_xly_rel = (xlp.pct_change(3) - xly.pct_change(3))  # 방어 상대강도 (XLP>XLY = 방어 우위)

    # ── driver 신호 변형 + 사전확약 부호 ──
    # (signal_series, expected_sign, target_subcluster, label)
    CLI_LAG = 2  # OECD CLI vintage lag
    drivers = {
        # ── 화장품 中경기 (中소비/관광) ──
        "chn_cli_yoy": (chn_cli.shift(CLI_LAG).pct_change(12), +1, "cosmetics", "中CLI yoy→화장품(中경기 양)"),
        "chn_cli_d3": (chn_cli.shift(CLI_LAG).pct_change(3), +1, "cosmetics", "中CLI 3M모멘텀→화장품"),
        "hsi_mom3": (hsi.pct_change(3), +1, "cosmetics", "항셍 3M모멘텀→화장품(中risk-on 양)"),
        "sse_mom3": (sse.pct_change(3), +1, "cosmetics", "상하이 3M모멘텀→화장품"),
        "usdcny_yoy": (usdcny.pct_change(12), -1, "cosmetics", "USDCNY yoy→화장품(위안약세=음)"),
        "hk_travel_mom3": (hk_travel.pct_change(3), +1, "cosmetics", "홍콩 3M모멘텀→화장품(관광/면세 risk-on 양)"),
        # ── 음식료 cost (곡물/유가) ──
        "corn_yoy": (corn.pct_change(12), -1, "food", "옥수수 yoy→음식료(cost-push 음)"),
        "wheat_yoy": (wheat.pct_change(12), -1, "food", "밀 yoy→음식료(cost-push 음)"),
        "soy_yoy": (soy.pct_change(12), -1, "food", "대두 yoy→음식료(cost-push 음)"),
        "wti_yoy": (wti.pct_change(12), -1, "food", "WTI유가 yoy→소비재(원가↑/소비여력↓ 음)"),
        # ── 내수 소비 cycle (소매판매/CSI) ──
        "kor_retail_yoy": (kor_retail.pct_change(12), +1, "food", "한국소매판매 yoy→음식료/유통(내수 양, 2024-03 제약)"),
        "csi_spend_yoy": (csi_spend.pct_change(12), +1, "retail", "CSI 소비지출전망 yoy→유통/내수(소비심리 양)"),
        "csi_spend_d3": (csi_spend.pct_change(3), +1, "retail", "CSI 소비지출 3M모멘텀→유통(내수 양)"),
        "csi_travel_yoy": (csi_travel.pct_change(12), +1, "cosmetics", "CSI 여행비전망 yoy→화장품/면세(리오프닝 양)"),
        "csi_cloth_yoy": (csi_cloth.pct_change(12), +1, "cosmetics", "CSI 의류비전망 yoy→화장품/의류(내수 양)"),
        "csi_econ_yoy": (csi_econ.pct_change(12), +1, "industry", "CSI 향후경기전망 yoy→소비재(경기심리 양)"),
        # ── 글로벌 소비재 상대모멘텀 ──
        "xlp_xly_rel3": (xlp_xly_rel, +1, "industry", "XLP-XLY 상대모멘텀→소비재(글로벌 방어 우위 양)"),
    }

    results = {"meta": {
        "method": "consumer 업종 rotation — fundamental driver(이론 사전확약→통계검증). rotation v2 NO_DIRECT 보강.",
        "theory_precommit": "中CLI/항셍/위안=화장품(中경기 양) / 곡물=음식료(cost-push 음) / 내수=양. data mining 차단=이론 근거 필수.",
        "drivers": {k: {"expected_sign": v[1], "target": v[2], "desc": v[3]} for k, v in drivers.items()},
        "source_verified": "FRED 中CLI(CHNLOLITOAASTSAM 2026-04)/USDCNY(DEXCHUS 일별)/KOR소매(KORSARTMISMEI 2024-03 제약) + yfinance 항셍/상하이/곡물/XLP/XLY/WTI/1379.HK + ECOS CSI(511Y002 소비지출FMCB/여행비FMCCD/의류비FMCCB/향후경기FMBB).",
        "horizons_months": HORIZONS_M, "oos_split": OOS_SPLIT, "t_breakeven": T_BREAKEVEN,
    }, "rotation_signals": {}, "subcluster_signals": {}}

    fdr_theory, fdr_all = {}, {}

    # ── 측정: 각 driver × target sub-cluster 패널 × horizon ──
    for dname, (dsig, esign, target, desc) in drivers.items():
        dsig = dsig.loc["2019-01-01":]
        for panel_name in ["industry", target]:
            if panel_name not in panels:
                continue
            pret = panels[panel_name].loc["2019-01-01":]
            cum = (1 + pret.fillna(0)).cumprod()
            for hl, hm in HORIZONS_M.items():
                fwd = cum.pct_change(hm).shift(-hm)
                key = f"{dname}__{panel_name}__{hl}"
                st = signal_forward_stat(dsig, fwd, hm, key, esign)
                st["desc"] = desc
                results["rotation_signals"][key] = st
                if st.get("status") in ("powered", "underpowered") and st.get("wild_cluster_p") is not None:
                    fdr_all[key] = st["wild_cluster_p"]
                    # ★이론 채택 후보 = 사전확약 부호 일치 + OOS eligible
                    if st.get("theory_sign_match") and st["walk_forward_oos"].get("eligible"):
                        fdr_theory[key] = st["wild_cluster_p"]

    # ── secondary: rel_mom reversal (rotation v2 발견 재현, industry/sub) ──
    for panel_name, pret in panels.items():
        cum = (1 + pret.loc["2019-01-01":].fillna(0)).cumprod()
        for mname, lb in [("mom_6", 6), ("rel_mom_6", 6)]:
            sig = cum.pct_change(lb).loc["2019-01-01":]
            for hl, hm in HORIZONS_M.items():
                fwd = cum.pct_change(hm).shift(-hm)
                key = f"{mname}__{panel_name}__{hl}"
                # mean-reversion 사전확약 = 음
                st = signal_forward_stat(sig, fwd, hm, key, -1)
                results["subcluster_signals"][key] = st
                if st.get("status") in ("powered", "underpowered") and st.get("wild_cluster_p") is not None:
                    fdr_all[key] = st["wild_cluster_p"]

    results["fdr_theory_drivers"] = benjamini_yekutieli(fdr_theory)
    results["fdr_all_single"] = benjamini_yekutieli(fdr_all)
    out = ROOT / "validation-rotation-consumer-v1.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}\n")
    print_summary(results)
    return results


def print_summary(r):
    print("=" * 84)
    print("★소비재 ROTATION fundamental driver (이론 사전확약 부호 + 통계검증)")
    print("=" * 84)
    for key, st in r["rotation_signals"].items():
        if st.get("status") == "INSUFFICIENT(n<12)":
            continue
        oos = st.get("walk_forward_oos", {})
        match = "✓이론일치" if st.get("theory_sign_match") else "✗부호반대"
        elig = "OOS적격" if oos.get("eligible") else ("OOS약" if oos.get("eligible") is False else "OOS n<8")
        flag = "★" if (st.get("theory_sign_match") and oos.get("eligible") and (st.get("wild_cluster_p") or 1) < 0.10) else " "
        print(f"{flag}{key:38s} rho={st['spearman_rho']:+.3f}(exp{st['expected_sign']:+d}) {match} "
              f"wc_p={st.get('wild_cluster_p')} t_pow={st.get('t_power_mde')} OOS{oos.get('rho_is')}->{oos.get('rho_oos')} {elig} {st['status'][:5]}")
    print("\n--- secondary momentum/reversal (mean-reversion 사전확약 음) ---")
    for key, st in r["subcluster_signals"].items():
        if st.get("status") == "INSUFFICIENT(n<12)": continue
        oos = st.get("walk_forward_oos", {})
        print(f"  {key:30s} rho={st['spearman_rho']:+.3f} wc_p={st.get('wild_cluster_p')} OOS{oos.get('rho_is')}->{oos.get('rho_oos')} {oos.get('verdict','')}")
    print(f"\n★FDR theory drivers (이론일치+OOS적격): {json.dumps(r['fdr_theory_drivers'], ensure_ascii=False)}")
    print(f"FDR all single: {json.dumps(r['fdr_all_single'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
