# -*- coding: utf-8 -*-
"""_b2_stats.py — ★B″ 공용 통계 인프라 (STEP 2/3 게이트, 전 sleeve 재사용).

REWORK-B2-adjustment-plan + .consult-us-rework-3R-results.md (대안 B″).
defensive payout_interaction 에서 추출 → cyclical/타 sleeve 공용 모듈화 (team-lead 지시).

제공:
- effective_n(x): ⑤ autocorr-deflated n_eff = n/(1+2Σρ_k) (NW VIF). regime persistence 반영.
- fixed_b_cv(n, nw_lag): ⑦ Kiefer-Vogelsang(2005) fixed-b critical value (size-valid, small-block).
- wild_cluster_boot(y, X, col): ⑦ wild-cluster(block) bootstrap p-value (size-valid).
- persistence_block(ic): regime persistence → HAC lag (AR1 기반).
- ridge_lambda_pit(...): ⑥ expanding-window PIT λ 동결 + 3점 hedge table.

★합성 0. asymptotic NW t 의 small-block size-invalidity(R3 Claude) 교정 = fixed-b + wild-cluster.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


# ── ⑤ effective-n (n_eff = n/(1+2Σρ_k), Newey-West variance inflation) ──
def effective_n(x, max_lag=None):
    """autocorr-deflated effective n. n_eff = n / (1 + 2 Σ_k (1-k/(L+1)) ρ_k). Bartlett-weighted (NW kernel)."""
    x = np.asarray(x, float); n = len(x)
    if n < 4:
        return dict(n=n, n_eff=float(n), vif=1.0, rho1=None, nw_lag=1)
    L = max_lag if max_lag is not None else int(np.floor(4 * (n / 100) ** (2 / 9)))  # NW auto bandwidth
    L = max(1, min(L, n - 2))
    e = x - x.mean(); g0 = (e @ e) / n
    if g0 <= 0:
        return dict(n=n, n_eff=float(n), vif=1.0, rho1=0.0, nw_lag=L)
    vif = 1.0
    rho1 = float((e[1:] @ e[:-1]) / n / g0) if n > 2 else None
    for k in range(1, L + 1):
        w = 1 - k / (L + 1)
        vif += 2 * w * ((e[k:] @ e[:-k]) / n / g0)
    vif = max(vif, 1e-6)
    return dict(n=n, n_eff=round(float(n / vif), 1), vif=round(float(vif), 3),
                rho1=round(rho1, 3) if rho1 is not None else None, nw_lag=L)


# ── ⑦ fixed-b CV (Kiefer-Vogelsang 2005, Bartlett kernel, 5% two-sided) ──
_KV_B_GRID = [0.02, 0.06, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
_KV_CV_5PCT = [2.08, 2.30, 2.49, 3.00, 3.54, 4.77, 6.10, 8.13]  # Bartlett 5% two-sided


def fixed_b_cv(n, nw_lag):
    """fixed-b(=nw_lag/n) 에 해당하는 KV 5% two-sided CV 보간. asymptotic 1.96 대비 small-block inflation."""
    b = nw_lag / n if n > 0 else 1.0
    cv = float(np.interp(b, _KV_B_GRID, _KV_CV_5PCT))
    return dict(b=round(b, 3), cv_5pct=round(cv, 2), asymptotic=1.96,
                note="Kiefer-Vogelsang(2005) fixed-b Bartlett 5% two-sided. |t|>cv 면 size-valid 유의.")


# ── ⑦ wild-cluster(block) bootstrap p-value ──
def wild_cluster_boot(y, X, col, block=6, B=2000, seed=42):
    """H0 β_col=0 wild-cluster(block) bootstrap. block Rademacher weight(regime persistence 보존).
    restricted 잔차 재표집 → t 분포. y=Series, X=add_constant DataFrame, col=검정 컬럼명."""
    import statsmodels.api as sm
    rng = np.random.default_rng(seed)
    df = pd.concat([y.rename("y"), X], axis=1).dropna()
    if len(df) < 24:
        return dict(p_wild_cluster=None, n=len(df), note="insufficient")
    Y = df["y"].values; cols = list(df.drop(columns=["y"]).columns)
    XX = df[cols].values; ci = cols.index(col)
    full = sm.OLS(Y, XX).fit(cov_type="HAC", cov_kwds={"maxlags": max(1, block // 2)})
    t_obs = float(full.tvalues[ci])
    keep = [c for c in cols if c != col]
    if keep:
        Xr = df[keep].values
        rfit = sm.OLS(Y, Xr).fit()
        resid_r = rfit.resid; yhat_r = rfit.fittedvalues
    else:
        # ★intercept-only / single-regressor 검정: 제약모형(H0 β=0)에 회귀항 없음 → yhat=0, resid=Y
        yhat_r = np.zeros(len(Y)); resid_r = Y.copy()
    n = len(Y); nblk = int(np.ceil(n / block))
    t_boot = []
    for _ in range(B):
        w = np.repeat(rng.choice([-1.0, 1.0], size=nblk), block)[:n]
        yb = yhat_r + resid_r * w
        try:
            fb = sm.OLS(yb, XX).fit(cov_type="HAC", cov_kwds={"maxlags": max(1, block // 2)})
            t_boot.append(float(fb.tvalues[ci]))
        except Exception:
            continue
    if not t_boot:
        return dict(p_wild_cluster=None, n=n)
    t_boot = np.array(t_boot)
    return dict(t_obs=round(t_obs, 2), p_wild_cluster=round(float((np.abs(t_boot) >= abs(t_obs)).mean()), 4),
                n=n, B=len(t_boot), block=block)


# ── regime persistence → HAC lag ──
def persistence_block(ic):
    """AR(1) 기반 effective block (ρ1 높을수록 lag↑). HAC maxlags = regime persistence."""
    x = np.asarray(ic, float); n = len(x)
    if n < 4:
        return 3
    e = x - x.mean(); g0 = (e @ e) / n
    rho1 = (e[1:] @ e[:-1]) / n / g0 if g0 > 0 else 0
    if rho1 <= 0.05:
        return 3
    blk = int(np.ceil(-1.0 / np.log(max(rho1, 0.06))))
    return int(np.clip(blk, 3, 12))


# ── ⑥ Ridge λ PIT expanding-window 동결 + 3점 hedge ──
def ridge_lambda_pit(target_ic, feature, train_frac=0.6, lam_lo=-3, lam_hi=2, n_grid=20):
    """★λ = expanding-window PIT 동결(train CV → eval 미접촉). λ∈{0.1λ*, λ*, 10λ*} 3점 hedge.
    target_ic = IC 시계열(Series), feature = interaction 변수(Series)."""
    from sklearn.linear_model import Ridge
    df = pd.concat([target_ic.rename("ic"), feature.rename("feat")], axis=1).dropna().sort_index()
    if len(df) < 40:
        return dict(note="insufficient", n=len(df))
    k = int(len(df) * train_frac)
    train, evalset = df.iloc[:k], df.iloc[k:]
    Xtr, ytr = train[["feat"]].values, train["ic"].values
    Xev, yev = evalset[["feat"]].values, evalset["ic"].values
    lam_grid = np.logspace(lam_lo, lam_hi, n_grid)
    best_lam, best_cv = 1.0, -np.inf
    for lam in lam_grid:
        errs = []
        for split in range(max(10, k // 3), k):
            r = Ridge(alpha=lam).fit(train[["feat"]].iloc[:split].values, train["ic"].iloc[:split].values)
            xn = train[["feat"]].iloc[split:split+1].values; yn = train["ic"].iloc[split:split+1].values
            errs.append((yn[0] - r.predict(xn)[0]) ** 2)
        if errs and -np.mean(errs) > best_cv:
            best_cv, best_lam = -np.mean(errs), lam
    hedge = {}
    for tag, lam in [("0.1λ*", 0.1 * best_lam), ("λ*", best_lam), ("10λ*", 10 * best_lam)]:
        r = Ridge(alpha=lam).fit(Xtr, ytr)
        coef = float(r.coef_[0])
        ec = float(np.corrcoef(r.predict(Xev), yev)[0, 1]) if len(yev) > 2 else None
        hedge[tag] = dict(lam=round(lam, 4), coef=round(coef, 4), sign=int(np.sign(coef)),
                          eval_pred_corr=round(ec, 3) if ec is not None and not np.isnan(ec) else None)
    signs = [hedge[t]["sign"] for t in hedge]
    return dict(lambda_star=round(best_lam, 4), train_n=k, eval_n=len(evalset),
                train_split_date=str(train.index[-1].date()), eval_start=str(evalset.index[0].date()),
                hedge_table=hedge, sign_stable=bool(len(set(signs)) == 1),
                note="★λ=expanding-window PIT(train CV→eval 미접촉). 3점 격자 부호 안정성.")


# ── 단일 IC 시계열 size-valid 유의성 검정 (fixed-b + effective-n) ──
def ic_size_valid_test(ic, block=None):
    """IC 시계열 평균의 size-valid 유의성: NW t + fixed-b CV + effective-n. mean≠0 검정."""
    ic = pd.Series(ic).dropna()
    n = len(ic)
    if n < 12:
        return dict(n=n, note="insufficient")
    blk = block if block is not None else persistence_block(ic.values)
    eff = effective_n(ic.values)
    mean = float(ic.mean())
    # NW SE
    x = ic.values; e = x - x.mean(); g0 = (e @ e) / n; var = g0
    for k in range(1, min(blk, n - 1) + 1):
        var += 2 * (1 - k / (blk + 1)) * (e[k:] @ e[:-k]) / n
    se = float(np.sqrt(max(var, 1e-12) / n))
    t = mean / se if se > 0 else np.nan
    fb = fixed_b_cv(eff["n"], eff.get("nw_lag", blk))
    return dict(ic_mean=round(mean, 4), n=n, t_nw=round(float(t), 2) if not np.isnan(t) else None,
                hac_lag=blk, effective_n=eff, fixed_b=fb,
                size_valid_sig=bool(not np.isnan(t) and abs(t) > fb["cv_5pct"]),
                asymptotic_sig=bool(not np.isnan(t) and abs(t) > 1.96))
