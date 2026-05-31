"""v2 2-3 commodity 실데이터 시계열 검증 — H5/H7-raw/H4/H3-proxy/H1-context.

KIT v2 §2-3 필수 산출. direction.md 가설 11개 중 Phase 1/1.5 (즉시 가능) 검증.
산출 = console + validation-*.md 입력.

데이터:
- Yahoo (yfinance): ^GSPC, ^VIX, GC=F, CL=F, HG=F, DBC, DBA, ^TNX
- FRED (pandas_datareader, no key): DCOILWTICO, CFNAI, INDPRO, BAMLH0A0HYM2, T10Y2Y
"""
from __future__ import annotations
import sys, json, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf
import pandas_datareader.data as pdr
from datetime import datetime
from scipy import stats

OUT = {}


def fetch_yf(symbols, start="1998-01-01", end="2026-05-30"):
    print(f"[yf] fetching {symbols} {start}->{end}", flush=True)
    df = yf.download(symbols, start=start, end=end, progress=False, auto_adjust=True)["Close"]
    if isinstance(df, pd.Series):
        df = df.to_frame(symbols[0])
    return df.dropna(how="all")


def fetch_fred(series_ids, start="1998-01-01", end="2026-05-30"):
    out = {}
    for sid in series_ids:
        try:
            s = pdr.DataReader(sid, "fred", start, end)
            out[sid] = s[sid]
            print(f"[fred] {sid} n={len(s)}", flush=True)
        except Exception as e:
            print(f"[fred] {sid} FAIL: {e}", flush=True)
    return pd.DataFrame(out)


def hyp_h5_financialization():
    """H5-outcome: 4-sleeve cross-corr 60일 rolling 평균.
    Tang-Xiong 2012 명제: 2004 이후 cross-corr 비정상 상승."""
    print("\n=== H5 financialization_reflexivity (outcome side) ===", flush=True)
    yf_syms = ["CL=F", "HG=F", "GC=F", "ZC=F"]   # WTI / Copper / Gold / Corn
    px = fetch_yf(yf_syms)
    if px.empty:
        return {"error": "no data"}
    ret = np.log(px).diff().dropna()
    print(f"[H5] return df shape={ret.shape} cols={list(ret.columns)}", flush=True)

    # 60일 rolling pairwise correlation 평균
    pairs = [(i, j) for i in range(len(yf_syms)) for j in range(i+1, len(yf_syms))]
    rolling_corrs = []
    for i, j in pairs:
        ci, cj = ret.columns[i], ret.columns[j]
        rc = ret[ci].rolling(60).corr(ret[cj])
        rolling_corrs.append(rc.rename(f"{ci}_{cj}"))
    rc_df = pd.concat(rolling_corrs, axis=1).dropna()
    mean_corr = rc_df.mean(axis=1)
    print(f"[H5] mean_corr n={len(mean_corr)} {mean_corr.index[0].date()}->{mean_corr.index[-1].date()}", flush=True)

    # Pre-2004 vs Post-2004 평균 비교 (Tang-Xiong financialization 명제)
    cutoff = pd.Timestamp("2004-01-01")
    pre = mean_corr[mean_corr.index < cutoff]
    post_2004_2010 = mean_corr[(mean_corr.index >= cutoff) & (mean_corr.index < "2011-01-01")]
    post_2011_2020 = mean_corr[(mean_corr.index >= "2011-01-01") & (mean_corr.index < "2021-01-01")]
    post_2021_now = mean_corr[mean_corr.index >= "2021-01-01"]

    # 2008 crisis subset (2008-09 ~ 2009-06)
    crisis_2008 = mean_corr["2008-09":"2009-06"]

    # VIX > 30 시점 mean cross-corr (falsification: <0.2)
    vix = fetch_yf(["^VIX"])["^VIX" if isinstance(fetch_yf(["^VIX"]), pd.DataFrame) else 0].reindex(mean_corr.index, method="nearest")
    hi_vix_mask = vix > 30
    hi_vix_corr = mean_corr[hi_vix_mask]

    summary = {
        "n_total_obs_days": len(mean_corr),
        "mean_corr_pre2004": float(pre.mean()) if len(pre) else None,
        "mean_corr_2004_2010": float(post_2004_2010.mean()),
        "mean_corr_2011_2020": float(post_2011_2020.mean()),
        "mean_corr_2021_now": float(post_2021_now.mean()),
        "mean_corr_2008_crisis": float(crisis_2008.mean()),
        "vix_gt_30_days": int(hi_vix_mask.sum()),
        "mean_corr_when_vix_gt_30": float(hi_vix_corr.mean()) if len(hi_vix_corr) else None,
        # Chow-like break test (mean shift Welch t-test)
        "welch_t_pre_vs_2004_2010": float(stats.ttest_ind(pre.dropna(), post_2004_2010.dropna(), equal_var=False).statistic) if len(pre) else None,
        "welch_p_pre_vs_2004_2010": float(stats.ttest_ind(pre.dropna(), post_2004_2010.dropna(), equal_var=False).pvalue) if len(pre) else None,
    }
    print(f"[H5] summary={json.dumps(summary, indent=2, default=str)}", flush=True)
    return summary


def hyp_h7_raw_noi():
    """H7-raw: Hamilton NOI 비선형 oil-macro.
    NOI_t = max(0, p_t - max(p_{t-12..t-1})). NOI > threshold 후 12m CFNAI."""
    print("\n=== H7-raw oil_macro_NOI_threshold ===", flush=True)
    wti = fetch_fred(["DCOILWTICO"])["DCOILWTICO"].dropna()
    cfnai = fetch_fred(["CFNAI"])["CFNAI"].dropna()
    print(f"[H7] wti n={len(wti)} cfnai n={len(cfnai)}", flush=True)

    # monthly resample
    wti_m = wti.resample("ME").last()
    cfnai_m = cfnai.resample("ME").mean()

    # NOI 계산
    rolling_max_12m = wti_m.rolling(12).max().shift(1)
    noi = (wti_m - rolling_max_12m).clip(lower=0)
    noi_pct = noi / rolling_max_12m  # 백분율 NOI (Hamilton 정의)

    # NOI > 30% 시점 12m forward CFNAI 평균
    shock_mask = noi_pct > 0.30
    shock_dates = noi_pct[shock_mask].index
    fwd_12m_cfnai = []
    for d in shock_dates:
        fwd_window = cfnai_m.loc[d:d + pd.DateOffset(months=12)]
        if len(fwd_window) >= 6:
            fwd_12m_cfnai.append(fwd_window.mean())

    # 평상시 (NOI < 30%) CFNAI 평균
    normal_dates = noi_pct[~shock_mask].index
    normal_cfnai_means = []
    for d in normal_dates[::12]:  # 1년 간격 샘플링
        fwd_window = cfnai_m.loc[d:d + pd.DateOffset(months=12)]
        if len(fwd_window) >= 6:
            normal_cfnai_means.append(fwd_window.mean())

    # 직접 회귀: NOI vs CFNAI lag 12m
    aligned = pd.DataFrame({"noi": noi_pct, "cfnai_t12": cfnai_m.shift(-12)}).dropna()
    if len(aligned) > 10:
        slope, intercept, r_val, p_val, _ = stats.linregress(aligned["noi"], aligned["cfnai_t12"])
    else:
        slope = r_val = p_val = np.nan

    summary = {
        "n_wti_obs": len(wti_m),
        "n_cfnai_obs": len(cfnai_m),
        "n_noi_shock_30pct": int(shock_mask.sum()),
        "fwd_12m_cfnai_after_shock_mean": float(np.mean(fwd_12m_cfnai)) if fwd_12m_cfnai else None,
        "fwd_12m_cfnai_after_shock_std": float(np.std(fwd_12m_cfnai)) if fwd_12m_cfnai else None,
        "fwd_12m_cfnai_normal_mean": float(np.mean(normal_cfnai_means)) if normal_cfnai_means else None,
        "fwd_12m_cfnai_normal_std": float(np.std(normal_cfnai_means)) if normal_cfnai_means else None,
        "regression_slope_noi_to_cfnai_t12": float(slope) if not np.isnan(slope) else None,
        "regression_r": float(r_val) if not np.isnan(r_val) else None,
        "regression_p": float(p_val) if not np.isnan(p_val) else None,
        "interpretation": "shock_mean << normal_mean → Hamilton NOI 가설 성립 (NOI 후 12m CFNAI 음수)",
    }
    print(f"[H7] summary={json.dumps(summary, indent=2, default=str)}", flush=True)
    return summary


def hyp_h4_china_copper():
    """H4: copper ↔ global industrial activity (FRED INDPRO 대체).
    Caixin 무료 X → 미국 INDPRO 대체 (글로벌 활동 proxy). Phase 1 한정 검증."""
    print("\n=== H4 china_demand_bellwether (INDPRO proxy) ===", flush=True)
    cu = fetch_yf(["HG=F"])["HG=F" if isinstance(fetch_yf(["HG=F"]), pd.DataFrame) else 0]
    indpro = fetch_fred(["INDPRO"])["INDPRO"].dropna()
    print(f"[H4] cu n={len(cu)} indpro n={len(indpro)}", flush=True)

    cu_m = cu.resample("ME").last()
    cu_ret_3m = np.log(cu_m).diff(3)
    indpro_yoy = indpro.pct_change(12).rename("indpro_yoy")

    # IPNROYoY → copper 3m forward return (Phase 1 검증: 3m lag)
    aligned = pd.DataFrame({"indpro_yoy": indpro_yoy.shift(3), "cu_ret_3m": cu_ret_3m}).dropna()
    if len(aligned) > 20:
        slope, intercept, r_val, p_val, _ = stats.linregress(aligned["indpro_yoy"], aligned["cu_ret_3m"])
        # Spearman (robust)
        sp_r, sp_p = stats.spearmanr(aligned["indpro_yoy"], aligned["cu_ret_3m"])
    else:
        slope = r_val = p_val = sp_r = sp_p = np.nan

    # INDPRO YoY > +3% 구간 vs < -1% 구간의 cu_ret_3m 평균
    expand = aligned[aligned["indpro_yoy"] > 0.03]
    contract = aligned[aligned["indpro_yoy"] < -0.01]
    if len(expand) > 5 and len(contract) > 5:
        t_stat, t_p = stats.ttest_ind(expand["cu_ret_3m"], contract["cu_ret_3m"], equal_var=False)
    else:
        t_stat = t_p = np.nan

    summary = {
        "n_aligned_obs": len(aligned),
        "n_expand_indpro_gt_3pct": len(expand),
        "n_contract_indpro_lt_neg1pct": len(contract),
        "expand_cu_ret_3m_mean": float(expand["cu_ret_3m"].mean()) if len(expand) > 0 else None,
        "contract_cu_ret_3m_mean": float(contract["cu_ret_3m"].mean()) if len(contract) > 0 else None,
        "welch_t_expand_vs_contract": float(t_stat) if not np.isnan(t_stat) else None,
        "welch_p_expand_vs_contract": float(t_p) if not np.isnan(t_p) else None,
        "regression_slope_indpro_yoy_to_cu_ret_3m": float(slope) if not np.isnan(slope) else None,
        "pearson_r": float(r_val) if not np.isnan(r_val) else None,
        "pearson_p": float(p_val) if not np.isnan(p_val) else None,
        "spearman_r": float(sp_r) if not np.isnan(sp_r) else None,
        "spearman_p": float(sp_p) if not np.isnan(sp_p) else None,
        "caveat": "INDPRO 가 Caixin proxy. 실제 Caixin 검증은 Phase 1.5 (별도 collector)",
    }
    print(f"[H4] summary={json.dumps(summary, indent=2, default=str)}", flush=True)
    return summary


def hyp_h3_proxy_roll_drag():
    """H3-proxy: BCOM/GSCI ETF (DBC) 의 12m return vs WTI spot 12m return.
    contango regime 에서 DBC < WTI spot (roll cost drag). CME 없이 ETF proxy."""
    print("\n=== H3-proxy roll_cost_drag (DBC vs WTI spot) ===", flush=True)
    yf_syms = ["DBC", "CL=F"]
    px = fetch_yf(yf_syms, start="2006-01-01")
    if px.empty or px.shape[1] < 2:
        return {"error": "no data"}
    print(f"[H3] px shape={px.shape}", flush=True)

    # 12m return 비교
    ret_12m = px.pct_change(252).dropna()
    diff_dbc_wti = ret_12m["DBC"] - ret_12m["CL=F"]
    print(f"[H3] return_12m n={len(ret_12m)}", flush=True)

    # 연도별 mean drag
    annual = diff_dbc_wti.groupby(diff_dbc_wti.index.year).mean()
    summary = {
        "n_obs_252d_overlap": len(ret_12m),
        "mean_dbc_minus_wti_12m": float(diff_dbc_wti.mean()),
        "std_dbc_minus_wti_12m": float(diff_dbc_wti.std()),
        "fraction_dbc_lt_wti": float((diff_dbc_wti < 0).mean()),
        "annual_means_drag": {int(y): float(v) for y, v in annual.items()},
        "interpretation": (
            "mean(DBC-WTI) < 0 + fraction_lt > 0.6 → 장기 roll drag 존재 (contango dominant)."
            " DBC = optimized contango-resistant index 이므로 단순 SPGSCI 보다 약하게 나타날 수 있음."
        ),
    }
    print(f"[H3] summary={json.dumps(summary, indent=2, default=str)}", flush=True)
    return summary


def main():
    print(f"=== v2 commodity 시계열 검증 시작 {datetime.now()} ===", flush=True)

    OUT["H5_financialization_outcome"] = hyp_h5_financialization()
    OUT["H7_raw_oil_NOI"] = hyp_h7_raw_noi()
    OUT["H4_china_copper_indpro_proxy"] = hyp_h4_china_copper()
    OUT["H3_proxy_roll_drag_DBC_WTI"] = hyp_h3_proxy_roll_drag()

    # 최종 출력
    print("\n=== 종합 ===", flush=True)
    print(json.dumps(OUT, indent=2, default=str), flush=True)

    # JSON dump
    with open("study-research/commodity/raw/v2-validate-results.json", "w") as f:
        json.dump(OUT, f, indent=2, default=str)
    print(f"\nsaved: study-research/commodity/raw/v2-validate-results.json", flush=True)


if __name__ == "__main__":
    main()
