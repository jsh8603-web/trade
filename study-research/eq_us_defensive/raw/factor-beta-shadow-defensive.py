"""factor-beta-shadow-defensive.py — J축 factor β shadow validation (sample-stage).

eq_us_defensive sleeve raw return 을 5 factor (rate/dollar/oil/credit/vol) 에 ★표준화 회귀해
절대 std β 추출. 분석 unit ↔ portfolio label 분리 (empirical-claim §1.6):
  - DEFENSIVE_PURE = {XLP, XLU, XLV} (rate-NEG)
  - FINANCIALS     = {XLF}          (rate-POS, NIM) — 별도 unit

회귀 방법 (§1.7 ADF 사전 + §1.4 HAC):
  - Δrate = DGS10 first-diff (bp), Δlog dollar = DTWEXBGS, Δlog oil = DCOILWTICO,
    Δcredit = (BAA10Y - AAA10Y) first-diff (bp), ΔVIX = VIXCLS first-diff
  - ADF 사전 (level 금지 확인), z-score 표준화 → std β, HAC(Newey-West) SE + t
  - univariate + multivariate(5 factor 동시) + VIF 공선성

shadow OOS: 추출 std β 로 SEED 갱신 가정 → build_seed_betas → factor_implied_cross_cov →
  sigma_model vs sigma_realized(defensive sleeve 실현 표본공분산) → run_shadow bias/eigvec.

★코드(core/study/) 미수정. 본 스크립트는 산출물 작성·실행 전용(off-path).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tsa.stattools import adfuller

RAW = Path(r"D:\projects\Inv\study-research\eq_us_defensive\raw")
FRED = RAW / "fred"
YF = RAW / "yfinance"

FACTORS = ["rate", "dollar", "oil", "credit", "vol"]
DEFENSIVE_PURE = ["XLP", "XLU", "XLV"]
FINANCIALS = ["XLF"]
ALL_ETF = DEFENSIVE_PURE + FINANCIALS


def _load_fred(name: str, col: str) -> pd.Series:
    df = pd.read_csv(FRED / f"{name}.csv")
    df.columns = ["date", col]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df[col], errors="coerce")
    s.index = df["date"]
    return s.dropna()


def build_factors() -> pd.DataFrame:
    """daily factor changes (stationary 단위)."""
    dgs10 = _load_fred("DGS10", "DGS10")
    dxy = _load_fred("DTWEXBGS", "DTWEXBGS")
    oil = _load_fred("DCOILWTICO", "DCOILWTICO")
    oil = oil[oil > 0]  # 2020-04-20 WTI=-36.98 단일 음가 제거(log 정의불가, 1/5051 day)
    baa = _load_fred("BAA10Y", "BAA10Y")
    aaa = _load_fred("AAA10Y", "AAA10Y")
    vix = _load_fred("VIXCLS", "VIXCLS")

    credit_spread = (baa - aaa).dropna()  # IG credit spread proxy (bp)

    f = pd.DataFrame({
        "rate": dgs10.diff() * 100.0,                 # Δyield in bp
        "dollar": np.log(dxy).diff(),                 # Δlog broad dollar
        "oil": np.log(oil).diff(),                    # Δlog WTI
        "credit": credit_spread.diff() * 100.0,       # Δ(BAA-AAA) in bp
        "vol": vix.diff(),                            # ΔVIX (level points)
    })
    return f.dropna()


def build_returns() -> pd.DataFrame:
    df = pd.read_csv(YF / "sector_etf_close.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")
    px = df[ALL_ETF].apply(pd.to_numeric, errors="coerce")
    ret = np.log(px).diff()
    return ret.dropna(how="all")


def adf_p(s: pd.Series) -> float:
    s = s.dropna()
    if len(s) < 20:
        return float("nan")
    try:
        return float(adfuller(s.values, regression="c", autolag="AIC")[1])
    except Exception:
        return float("nan")


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=0)


def hac_reg(y: pd.Series, X: pd.DataFrame, maxlags: int = 5):
    """z-scored OLS with Newey-West HAC SE. returns dict of param/se/t per col."""
    yz = zscore(y)
    Xz = X.apply(zscore)
    Xc = sm.add_constant(Xz)
    model = sm.OLS(yz.values, Xc.values).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    out = {}
    names = ["const"] + list(X.columns)
    for i, nm in enumerate(names):
        out[nm] = (float(model.params[i]), float(model.bse[i]), float(model.tvalues[i]),
                   float(model.pvalues[i]))
    out["_n"] = int(model.nobs)
    out["_r2"] = float(model.rsquared)
    return out


def compute_vif(X: pd.DataFrame) -> dict:
    Xz = X.apply(zscore)
    Xc = sm.add_constant(Xz).values
    cols = ["const"] + list(X.columns)
    return {cols[i]: float(variance_inflation_factor(Xc, i)) for i in range(1, len(cols))}


def equal_weight_return(ret: pd.DataFrame, tickers: list) -> pd.Series:
    return ret[tickers].mean(axis=1)


def tier_suggest(beta, t, n, bonf_alpha, p):
    if beta is None or not np.isfinite(t):
        return "hold"
    at = abs(t)
    # Bonferroni-survival on multivariate p
    if at >= 2.0 and p <= bonf_alpha:
        return "validated"
    if at >= 1.6:
        return "structural"   # directional, not surviving Bonferroni
    return "reject"


def main():
    factors = build_factors()
    rets = build_returns()

    # align
    df = factors.join(rets, how="inner").dropna()
    n_total = len(df)
    cov_start, cov_end = df.index.min().date(), df.index.max().date()

    results = {
        "_frontmatter": {
            "title": "J축 factor β shadow validation — eq_us_defensive (sample-stage)",
            "tags": ["study/eq_us_defensive", "factor-beta", "shadow-validation", "J축"],
            "date": "2026-06-01",
            "stage": "sample (점추정 박제 아님, shadow 검증 대상)",
            "scope": "core/study 미수정 · SEED Edit 제안만",
        },
        "meta": {
            "coverage_start": str(cov_start),
            "coverage_end": str(cov_end),
            "n": n_total,
            "factors": FACTORS,
            "note": "DTWEXBGS broad dollar starts 2006-01 -> binds joint window",
        },
        "adf": {},
        "units": {},
        "vif": {},
        "tier_suggest": {},
    }

    # ADF pre-test (stationarity of factor regressors)
    for f in FACTORS:
        results["adf"][f] = adf_p(df[f])

    # Bonferroni: 2 units x 5 factors = 10 comparisons
    n_comp = 10
    bonf_alpha = 0.05 / n_comp

    units = {"DEFENSIVE_PURE": DEFENSIVE_PURE, "FINANCIALS": FINANCIALS}
    for uname, tickers in units.items():
        y = equal_weight_return(df.loc[:, tickers] if isinstance(tickers, list) else df[[tickers]], tickers) \
            if False else df[tickers].mean(axis=1)
        y = y.dropna()
        sub = df.loc[y.index]
        results["adf"][f"ret_{uname}"] = adf_p(y)

        # univariate
        uni = {}
        for f in FACTORS:
            r = hac_reg(y, sub[[f]])
            uni[f] = {"beta": r[f][0], "se": r[f][1], "t": r[f][2], "p": r[f][3],
                      "n": r["_n"], "r2": r["_r2"]}
        # multivariate
        mr = hac_reg(y, sub[FACTORS])
        multi = {}
        for f in FACTORS:
            multi[f] = {"beta": mr[f][0], "se": mr[f][1], "t": mr[f][2], "p": mr[f][3]}
        multi["_n"] = mr["_n"]
        multi["_r2"] = mr["_r2"]

        vif = compute_vif(sub[FACTORS])
        results["vif"][uname] = vif

        # tier from multivariate
        tiers = {}
        for f in FACTORS:
            tiers[f] = tier_suggest(multi[f]["beta"], multi[f]["t"], multi["_n"],
                                    bonf_alpha, multi[f]["p"])
        results["tier_suggest"][uname] = tiers

        results["units"][uname] = {"tickers": tickers, "univariate": uni, "multivariate": multi}

    results["meta"]["bonferroni_alpha"] = bonf_alpha
    results["meta"]["n_comparisons"] = n_comp

    # ---- shadow OOS ----
    shadow = run_shadow_oos(df, results)
    results["shadow"] = shadow

    out_json = RAW / "factor-beta-shadow-defensive.json"
    out_json.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print("WROTE", out_json)

    # console summary
    for uname in units:
        print(f"\n=== {uname} (multivariate std beta, HAC) n={results['units'][uname]['multivariate']['_n']} ===")
        for f in FACTORS:
            m = results["units"][uname]["multivariate"][f]
            print(f"  {f:7s} beta={m['beta']:+.3f} t={m['t']:+.2f} p={m['p']:.4f} tier={results['tier_suggest'][uname][f]}")
    print("\nADF p:", {k: round(v, 5) for k, v in results["adf"].items()})
    print("\nshadow:", shadow["summary"])
    return results


def run_shadow_oos(df: pd.DataFrame, results: dict) -> dict:
    """Extracted defensive std beta -> SEED override -> sigma_model vs realized -> run_shadow.

    ★z-unit 일관 (betas standardized): Λ = z-factor 상관행렬, idio = 1−R²(z-단위), sigma_model =
    B·Λ·Bᵀ + diag(idio). sigma_realized = z-scored sleeve return 표본공분산. 같은 z-space 라 bias-stat
    [0.9,1.1] 밴드가 해석가능. ★sleeve proxy 가능한 것만 realized 사용, 나머지는 OOS half-split.
    """
    sys.path.insert(0, r"D:\projects\Inv")
    from core.study.factor_betas_seed import (
        SEED_CELLS, FactorCell, build_seed_betas, TIER_VALIDATED, TIER_STRUCTURAL,
        TIER_HOLD, TIER_REJECT,
    )
    from core.study.system_priors import factor_implied_cross_cov
    from core.study.factor_shadow import run_shadow

    dp = results["units"]["DEFENSIVE_PURE"]["multivariate"]
    tiers = results["tier_suggest"]["DEFENSIVE_PURE"]
    tier_map = {"validated": TIER_VALIDATED, "structural": TIER_STRUCTURAL,
                "reject": TIER_REJECT, "hold": TIER_HOLD}

    # ---- in-sample / OOS half-split (walk-forward) on DEFENSIVE_PURE ----
    half = len(df) // 2
    df_is, df_oos = df.iloc[:half], df.iloc[half:]

    def fit_betas(sub):
        y = sub[DEFENSIVE_PURE].mean(axis=1)
        r = hac_reg(y, sub[FACTORS])
        return {f: r[f][0] for f in FACTORS}, r["_r2"]

    b_is, r2_is = fit_betas(df_is)
    b_oos, r2_oos = fit_betas(df_oos)
    b_full, r2_full = fit_betas(df)

    # ---- SEED override (eq_us_defensive HOLD -> extracted full-sample) ----
    new_cells = []
    for c in SEED_CELLS:
        if c.sleeve == "eq_us_defensive" and c.factor in FACTORS:
            m = dp[c.factor]
            new_cells.append(FactorCell(
                "eq_us_defensive", c.factor, round(m["beta"], 3),
                se=round(m["se"], 3), t=round(m["t"], 2), n=int(dp["_n"]),
                tier=tier_map[tiers[c.factor]], note="J축 shadow 추출(DEFENSIVE_PURE)"))
        else:
            new_cells.append(c)

    # ---- z-unit Lambda = factor correlation matrix (full sample) ----
    Fz = df[FACTORS].apply(zscore)
    Lam = np.cov(Fz.values, rowvar=False)  # ≈ correlation (z-scored)

    # idio override for eq_us_defensive = 1 - R² (z-unit residual variance)
    total_var = {"eq_us_defensive": 1.0}  # z-unit total = 1
    sb = build_seed_betas(cells=tuple(new_cells), factor_cov=Lam, total_var=total_var)
    res = factor_implied_cross_cov(sb.betas, Lam, factors=list(sb.factors), idio_var=sb.idio_var)
    Sm = res.cov
    sleeves = res.sleeves

    # ---- realized z-unit cov: only eq_us_defensive proxied; others keep model (neutral) ----
    Sr = np.array(Sm, dtype=float).copy()
    idx = sleeves.index("eq_us_defensive")
    dp_z = zscore(df[DEFENSIVE_PURE].mean(axis=1))
    var_def_z = float(np.var(dp_z.values, ddof=1))  # ≈ 1 by construction
    # model-implied defensive variance in z-units
    model_def_var = float(Sm[idx, idx])
    bias_def = float(np.sqrt(model_def_var / var_def_z))
    Sr[idx, idx] = var_def_z

    rep = run_shadow(sleeves, sb.betas, Sm, Sr, factor="dollar")

    # OOS beta stability (sign + magnitude consistency IS vs OOS)
    oos_consistency = {}
    for f in FACTORS:
        same_sign = (np.sign(b_is[f]) == np.sign(b_oos[f]))
        oos_consistency[f] = {
            "beta_IS": round(b_is[f], 3), "beta_OOS": round(b_oos[f], 3),
            "beta_full": round(b_full[f], 3), "sign_stable": bool(same_sign),
        }

    return {
        "override_cells": [
            {"factor": c.factor, "beta": c.beta, "se": c.se, "t": c.t, "n": c.n, "tier": c.tier}
            for c in new_cells if c.sleeve == "eq_us_defensive" and c.factor in FACTORS
        ],
        "lambda_note": "Λ = z-scored factor 공분산(≈상관). betas z-unit 과 일관.",
        "defensive_model_var_z": round(model_def_var, 4),
        "defensive_realized_var_z": round(var_def_z, 4),
        "defensive_bias_stat": round(bias_def, 4),
        "bias_by_portfolio": {k: (round(v, 4) if np.isfinite(v) else None)
                              for k, v in rep.bias_by_portfolio.items()},
        "bias_pass": bool(rep.bias_pass),
        "eigvec_cosine": round(rep.eigvec_cosine, 4),
        "eigvec_pass": bool(rep.eigvec_pass),
        "frobenius_corr": round(rep.frobenius_corr, 4),
        "overall_pass": bool(rep.overall_pass),
        "oos_halfsplit": {"r2_IS": round(r2_is, 4), "r2_OOS": round(r2_oos, 4),
                          "consistency": oos_consistency},
        "note": rep.note,
        "summary": (f"defensive bias_stat={bias_def:.3f}(밴드[0.9,1.1]) eigvec_cos={rep.eigvec_cosine:.3f} "
                    f"overall_pass={rep.overall_pass}"),
        "off_path": "run_shadow 순수함수 — production 상태 write 없음, 어떤 결정에도 미반영(off-path)",
    }


if __name__ == "__main__":
    main()
