"""v2 2-3 commodity 시계열 검증 보강 — H4 alignment fix, H7 multi-threshold, H10 GHR proxy, H1-ref gold."""
from __future__ import annotations
import json, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, yfinance as yf
import pandas_datareader.data as pdr
from scipy import stats

OUT = {}


def fetch_yf(symbols, start="1998-01-01", end="2026-05-30"):
    df = yf.download(symbols, start=start, end=end, progress=False, auto_adjust=True)["Close"]
    if isinstance(df, pd.Series):
        df = df.to_frame(symbols[0])
    return df.dropna(how="all")


def fetch_fred(ids, start="1998-01-01", end="2026-05-30"):
    out = {}
    for sid in ids:
        try:
            out[sid] = pdr.DataReader(sid, "fred", start, end)[sid]
        except Exception as e:
            print(f"[fred] {sid} FAIL: {e}", flush=True)
    return pd.DataFrame(out)


def h4_china_copper_fix():
    """H4 fix — copper monthly resample, INDPRO YoY 명시적 정렬"""
    print("\n=== H4-fix china_demand (copper ~ INDPRO YoY, lag 3m) ===", flush=True)
    cu = fetch_yf(["HG=F"])
    cu_col = cu.columns[0]
    cu_m = cu[cu_col].resample("ME").last().rename("cu")
    cu_ret_3m = cu_m.pct_change(3).rename("cu_ret_3m")

    indpro = fetch_fred(["INDPRO"])["INDPRO"]
    indpro_m = indpro.resample("ME").mean()
    indpro_yoy = indpro_m.pct_change(12).rename("indpro_yoy")

    # 정렬 (월말 기준 명시)
    indpro_yoy_lag3 = indpro_yoy.shift(-3).rename("indpro_yoy_t3")  # 현재 INDPRO -> 3m 뒤 copper
    df = pd.concat([cu_ret_3m, indpro_yoy_lag3], axis=1).dropna()
    print(f"[H4-fix] aligned n={len(df)} period={df.index[0].date()}->{df.index[-1].date()}", flush=True)

    if len(df) > 20:
        # Pearson
        pr, pp = stats.pearsonr(df["indpro_yoy_t3"], df["cu_ret_3m"])
        # Spearman (robust)
        sr, sp = stats.spearmanr(df["indpro_yoy_t3"], df["cu_ret_3m"])
        # OLS
        slope, intercept, r, p_reg, _ = stats.linregress(df["indpro_yoy_t3"], df["cu_ret_3m"])
        # 확장 vs 수축 비교
        expand = df[df["indpro_yoy_t3"] > 0.03]["cu_ret_3m"]
        contract = df[df["indpro_yoy_t3"] < -0.01]["cu_ret_3m"]
        t_stat, t_p = stats.ttest_ind(expand, contract, equal_var=False) if len(expand)>3 and len(contract)>3 else (np.nan, np.nan)
        # IC (Rank-correlation = Spearman 동일)
        # 다른 lag 검사 (0, 6m, 12m)
        ics_by_lag = {}
        for lag in [0, 3, 6, 12]:
            ind_lag = indpro_yoy.shift(-lag).rename("indpro_yoy_lag")
            d2 = pd.concat([cu_ret_3m, ind_lag], axis=1).dropna()
            if len(d2) > 20:
                rho, pv = stats.spearmanr(d2["indpro_yoy_lag"], d2["cu_ret_3m"])
                ics_by_lag[lag] = {"n": len(d2), "spearman_rho": float(rho), "p": float(pv)}
    else:
        pr=pp=sr=sp=slope=r=p_reg=t_stat=t_p = np.nan; ics_by_lag = {}; expand=contract=pd.Series()

    summary = {
        "n_aligned": int(len(df)),
        "period": f"{df.index[0].date()}..{df.index[-1].date()}" if len(df) else None,
        "pearson_r_indpro_yoy_to_cu_ret_3m": float(pr) if not np.isnan(pr) else None,
        "pearson_p": float(pp) if not np.isnan(pp) else None,
        "spearman_rho": float(sr) if not np.isnan(sr) else None,
        "spearman_p": float(sp) if not np.isnan(sp) else None,
        "regression_slope": float(slope) if not np.isnan(slope) else None,
        "regression_p": float(p_reg) if not np.isnan(p_reg) else None,
        "n_expand_indpro_gt_3pct": int(len(expand)),
        "n_contract_indpro_lt_neg1pct": int(len(contract)),
        "expand_cu_ret_3m_mean": float(expand.mean()) if len(expand) > 0 else None,
        "contract_cu_ret_3m_mean": float(contract.mean()) if len(contract) > 0 else None,
        "welch_t_expand_vs_contract": float(t_stat) if not np.isnan(t_stat) else None,
        "welch_p_expand_vs_contract": float(t_p) if not np.isnan(t_p) else None,
        "spearman_ic_by_lag": ics_by_lag,
        "caveat": "INDPRO proxy for global activity. Caixin 별도 검증 = Phase 1.5 신규 collector",
    }
    print(f"[H4-fix] {json.dumps(summary, indent=2, default=str)}", flush=True)
    return summary


def h7_multi_threshold():
    """H7-raw 다단 threshold — 10%, 15%, 20%, 30%."""
    print("\n=== H7-multi NOI threshold ladder ===", flush=True)
    wti = fetch_fred(["DCOILWTICO"])["DCOILWTICO"].dropna()
    cfnai = fetch_fred(["CFNAI"])["CFNAI"].dropna()
    wti_m = wti.resample("ME").last()
    cfnai_m = cfnai.resample("ME").mean()
    rolling_max_12m = wti_m.rolling(12).max().shift(1)
    noi_pct = (wti_m - rolling_max_12m).clip(lower=0) / rolling_max_12m

    # 정렬해 lag 0, 6, 12, 18m forward CFNAI mean
    results_by_thr = {}
    for thr in [0.05, 0.10, 0.15, 0.20, 0.30]:
        shock_dates = noi_pct[noi_pct > thr].index
        fwd_by_lag = {}
        for lag in [0, 6, 12, 18]:
            fwd_vals = []
            for d in shock_dates:
                v_window = cfnai_m.loc[d + pd.DateOffset(months=lag - 3): d + pd.DateOffset(months=lag + 3)]
                if len(v_window) >= 3:
                    fwd_vals.append(v_window.mean())
            if fwd_vals:
                fwd_by_lag[lag] = {"n": len(fwd_vals), "mean_cfnai": float(np.mean(fwd_vals)), "std": float(np.std(fwd_vals))}
        results_by_thr[thr] = {"n_shocks": int(len(shock_dates)), "fwd_cfnai_by_lag": fwd_by_lag}

    # 회귀 NOI -> CFNAI(t+12)
    aligned = pd.DataFrame({"noi": noi_pct, "cfnai_t12": cfnai_m.shift(-12)}).dropna()
    if len(aligned) > 20:
        slope, intercept, r, p, _ = stats.linregress(aligned["noi"], aligned["cfnai_t12"])
        # nonlinear: NOI^2
        sq = aligned["noi"] ** 2
        slope_sq, _, r_sq, p_sq, _ = stats.linregress(sq, aligned["cfnai_t12"])
    else:
        slope=r=p=slope_sq=r_sq=p_sq = np.nan

    # CFNAI 평상 시 평균 (no shock)
    normal_cfnai_mean = float(cfnai_m[noi_pct <= 0.05].mean())

    summary = {
        "n_obs": int(len(aligned)),
        "normal_cfnai_mean": normal_cfnai_mean,
        "shocks_by_threshold": results_by_thr,
        "linreg_slope_noi_to_cfnai_t12": float(slope) if not np.isnan(slope) else None,
        "linreg_r": float(r) if not np.isnan(r) else None,
        "linreg_p": float(p) if not np.isnan(p) else None,
        "nonlinear_NOI_sq_slope": float(slope_sq) if not np.isnan(slope_sq) else None,
        "nonlinear_NOI_sq_r": float(r_sq) if not np.isnan(r_sq) else None,
        "nonlinear_NOI_sq_p": float(p_sq) if not np.isnan(p_sq) else None,
        "interpretation": "Hamilton: NOI 단조 증가에 따라 12m 후 CFNAI 점차 음수. nonlinear R² 가 단조 회귀보다 의미.",
    }
    print(f"[H7-multi] {json.dumps(summary, indent=2, default=str)}", flush=True)
    return summary


def h10_ghr_inv_state_proxy():
    """H10 GHR inventory state — EIA crude stocks via FRED (WCESTUS1 weekly) + WTI return.

    inventory state hypothesis: normalized inventory 가 basis (단순 return proxy) 와 prior return 동시 설명.
    EIA data: 'WCESTUS1' = US Crude Oil Ending Stocks (FRED).
    """
    print("\n=== H10 GHR inventory state (EIA crude proxy) ===", flush=True)
    inv = fetch_fred(["WCESTUS1"])
    if inv.empty:
        return {"error": "no inventory data (EIA WCESTUS1 not in FRED)"}
    inv_s = inv["WCESTUS1"].dropna()
    print(f"[H10] EIA inv n={len(inv_s)} {inv_s.index[0].date()}->{inv_s.index[-1].date()}", flush=True)

    wti = fetch_yf(["CL=F"])
    wti_s = wti.iloc[:, 0]

    # weekly resample
    inv_w = inv_s.resample("W-FRI").last()
    wti_w = wti_s.resample("W-FRI").last()

    # HP filter for normalized inventory
    try:
        from statsmodels.tsa.filters.hp_filter import hpfilter
        inv_clean = inv_w.dropna()
        cycle, trend = hpfilter(inv_clean, lamb=129600)  # weekly λ
        norm_inv = (cycle / trend).rename("norm_inv")
    except Exception as e:
        norm_inv = ((inv_w - inv_w.rolling(52).mean()) / inv_w.rolling(52).std()).rename("norm_inv")
        print(f"[H10] hpfilter fail, fallback z: {e}", flush=True)

    # WTI return forward 12-week
    wti_ret_12w = wti_w.pct_change(12).shift(-12).rename("wti_ret_12w_fwd")

    df = pd.concat([norm_inv, wti_ret_12w], axis=1).dropna()
    print(f"[H10] aligned n={len(df)}", flush=True)

    if len(df) > 30:
        # 두 회귀: norm_inv → wti_ret_12w_fwd (GHR 핵심 명제)
        slope, intercept, r, p, _ = stats.linregress(df["norm_inv"], df["wti_ret_12w_fwd"])
        # Spearman
        sr, sp = stats.spearmanr(df["norm_inv"], df["wti_ret_12w_fwd"])
        # 분위 검정: top quartile (재고 잉여) vs bottom (타이트)
        q_thr = df["norm_inv"].quantile([0.25, 0.75])
        bot = df[df["norm_inv"] <= q_thr.iloc[0]]["wti_ret_12w_fwd"]
        top = df[df["norm_inv"] >= q_thr.iloc[1]]["wti_ret_12w_fwd"]
        t_stat, t_p = stats.ttest_ind(bot, top, equal_var=False)
    else:
        slope=r=p=sr=sp=t_stat=t_p=np.nan
        bot=top=pd.Series()

    summary = {
        "n_eia_inv_obs": int(len(inv_w.dropna())),
        "n_aligned": int(len(df)),
        "linreg_slope": float(slope) if not np.isnan(slope) else None,
        "linreg_r": float(r) if not np.isnan(r) else None,
        "linreg_p": float(p) if not np.isnan(p) else None,
        "spearman_rho": float(sr) if not np.isnan(sr) else None,
        "spearman_p": float(sp) if not np.isnan(sp) else None,
        "bot_quartile_inv_n": len(bot), "bot_wti_ret_12w_fwd_mean": float(bot.mean()) if len(bot) else None,
        "top_quartile_inv_n": len(top), "top_wti_ret_12w_fwd_mean": float(top.mean()) if len(top) else None,
        "welch_t_bot_minus_top": float(t_stat) if not np.isnan(t_stat) else None,
        "welch_p": float(t_p) if not np.isnan(t_p) else None,
        "interpretation": "GHR 명제: 낮은 norm_inv (bot quartile) -> 양의 12w forward return; 높은 norm_inv (top) -> 음. slope < 0 + bot > top + p < 0.05 = 가설 지지.",
    }
    print(f"[H10] {json.dumps(summary, indent=2, default=str)}", flush=True)
    return summary


def h1_ref_gold_real_rate():
    """H1 reference — gold 방에서 검증 종결이지만 본 방 cross-sleeve 차원에서 partial-corr 측정.
    DFII10 (FRED) 가용 + DXY (FRED DTWEXBGS) + Gold (Yahoo GC=F)."""
    print("\n=== H1-ref gold_real_rate_nexus (partial-corr) ===", flush=True)
    fred = fetch_fred(["DFII10", "DTWEXBGS"])
    if fred.empty or "DFII10" not in fred or "DTWEXBGS" not in fred:
        return {"error": f"missing FRED data: {fred.columns.tolist()}"}
    real = fred["DFII10"].dropna()
    dxy = fred["DTWEXBGS"].dropna()
    gold = fetch_yf(["GC=F"]).iloc[:, 0]

    # daily 정렬
    df = pd.concat([gold.rename("gold"), real.rename("real"), dxy.rename("dxy")], axis=1).dropna()
    print(f"[H1] aligned n={len(df)}", flush=True)

    # log returns
    ret = np.log(df).diff().dropna()

    # full-period partial corr (gold, real | dxy) via residualization
    # gold_resid = gold ~ dxy 잔차, real_resid = real ~ dxy 잔차, corr(resid_gold, resid_real)
    from numpy.linalg import lstsq
    X_dxy = np.column_stack([np.ones(len(ret)), ret["dxy"]])
    beta_g, *_ = lstsq(X_dxy, ret["gold"], rcond=None); gold_resid = ret["gold"] - X_dxy @ beta_g
    beta_r, *_ = lstsq(X_dxy, ret["real"], rcond=None); real_resid = ret["real"] - X_dxy @ beta_r
    full_partial, full_p = stats.pearsonr(gold_resid, real_resid)
    full_simple, _ = stats.pearsonr(ret["gold"], ret["real"])

    # 36m rolling partial-corr
    win = 252 * 3
    rolling = []
    for i in range(win, len(ret)):
        seg = ret.iloc[i-win:i]
        X = np.column_stack([np.ones(len(seg)), seg["dxy"]])
        bg, *_ = lstsq(X, seg["gold"], rcond=None); gr = seg["gold"] - X @ bg
        br, *_ = lstsq(X, seg["real"], rcond=None); rr = seg["real"] - X @ br
        rho, _ = stats.pearsonr(gr, rr)
        rolling.append((ret.index[i], rho))
    roll_df = pd.DataFrame(rolling, columns=["date", "partial_corr"]).set_index("date")

    summary = {
        "period": f"{ret.index[0].date()}..{ret.index[-1].date()}",
        "n_obs_daily": int(len(ret)),
        "simple_pearson_gold_real": float(full_simple),
        "partial_corr_full_period": float(full_partial),
        "partial_corr_full_p": float(full_p),
        "rolling_36m_partial_corr_n": int(len(roll_df)),
        "rolling_36m_partial_corr_mean": float(roll_df["partial_corr"].mean()),
        "rolling_36m_partial_corr_min": float(roll_df["partial_corr"].min()),
        "rolling_36m_partial_corr_max": float(roll_df["partial_corr"].max()),
        "rolling_36m_last_value": float(roll_df["partial_corr"].iloc[-1]),
        "fraction_below_neg_0p4": float((roll_df["partial_corr"] < -0.4).mean()),
        "fraction_below_neg_0p1": float((roll_df["partial_corr"] < -0.1).mean()),
        "fraction_positive": float((roll_df["partial_corr"] > 0).mean()),
        "interpretation": "H1 falsification = 36m partial > -0.1 6m 지속. mean < -0.4 = 강하게 지지, mean > -0.1 = 기각",
    }
    print(f"[H1-ref] {json.dumps(summary, indent=2, default=str)}", flush=True)
    return summary


if __name__ == "__main__":
    OUT["H4_fix"] = h4_china_copper_fix()
    OUT["H7_multi_threshold"] = h7_multi_threshold()
    OUT["H10_ghr_inv_state_proxy"] = h10_ghr_inv_state_proxy()
    OUT["H1_ref_gold_real_rate"] = h1_ref_gold_real_rate()
    print("\n=== 종합 ===", flush=True)
    print(json.dumps(OUT, indent=2, default=str), flush=True)
    with open("study-research/commodity/raw/v2-validate-v2-results.json", "w") as f:
        json.dump(OUT, f, indent=2, default=str)
    print(f"saved: study-research/commodity/raw/v2-validate-v2-results.json", flush=True)
