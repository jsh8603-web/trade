"""batch-std-beta-5sleeve.py — J축 factor β shadow validation (batch-stage).

나머지 5 sleeve (gold·eq_us_cyclical·eq_intl·reit·commodity) 의 raw return 을 ★공통 5 factor
(rate/dollar/oil/credit/vol) 에 표준화 회귀해 절대 std β 추출. sample-stage
(eq_us_defensive) 와 ★동일 방법 (factor-beta-shadow-defensive.py 템플릿):

  - Δrate = DGS10 first-diff (bp), Δlog dollar = DTWEXBGS, Δlog oil = DCOILWTICO
    (2020-04-20 음가 1일 제거), Δcredit = (BAA10Y-AAA10Y) first-diff (bp), ΔVIX = VIXCLS diff
  - factor 시계열 = eq_us_defensive/raw/fred 캐시 (sample 과 동일 source, 일관성)
  - 표준화 회귀 (y·x z-score → std β), HAC(Newey-West) SE+t, n, ADF 사전, VIF, multivariate+univariate
  - ★vol(ΔVIX) factor 반드시 포함 (rate β 가 vol 통제 시 흡수되는지 sleeve별 확인)

분석 unit ↔ portfolio label 분리 (empirical-claim §1.6):
  - eq_us_cyclical: CYCLICAL_PRO = {XLB, XLI, SOXX} (pro-cyclical), XLE = anti/energy 별도 unit
  - gold = 재현 검증용 (기존 SEED -0.295/-0.328/+0.230 와 부호·크기대 일치 = 방법 신뢰성 게이트)

★코드(core/study/) 미수정. 본 스크립트는 산출물 작성·실행 전용(off-path).
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tsa.stattools import adfuller

warnings.filterwarnings("ignore")

ROOT = Path(r"D:\projects\Inv\study-research")
# factor 캐시 = defensive sleeve fred (sample 과 동일 source = 방법 일관성)
FRED = ROOT / "eq_us_defensive" / "raw" / "fred"
OUT = ROOT / "_factor_shadow"

FACTORS = ["rate", "dollar", "oil", "credit", "vol"]

# sleeve 대표 자산 (yfinance 무료 fetch, full history). §1.6 unit 분리:
#   eq_us_cyclical: pro-cyclical {XLB,XLI,SOXX} 별 unit, XLE(anti/energy) 별 unit
SLEEVE_UNITS = {
    "gold": {"GOLD": ["GLD"]},
    "eq_us_cyclical": {"CYCLICAL_PRO": ["XLB", "XLI", "SOXX"], "XLE_ENERGY": ["XLE"]},
    "eq_intl": {"EQ_INTL": ["EFA", "EEM"]},   # DM + EM sleeve-avg
    "reit": {"REIT": ["VNQ"]},
    "commodity": {"COMMODITY": ["DBC"]},      # 일별 ETF 로 n 확대 (vs n=12 분기)
}

ALL_TICKERS = sorted({t for u in SLEEVE_UNITS.values() for ts in u.values() for t in ts})


def _load_fred(name: str) -> pd.Series:
    df = pd.read_csv(FRED / f"{name}.csv")
    df.columns = ["date", "val"]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df["val"], errors="coerce")
    s.index = df["date"]
    return s.dropna()


def build_factors() -> pd.DataFrame:
    dgs10 = _load_fred("DGS10")
    dxy = _load_fred("DTWEXBGS")
    oil = _load_fred("DCOILWTICO")
    oil = oil[oil > 0]  # 2020-04-20 WTI 음가 제거 (log 정의불가)
    baa = _load_fred("BAA10Y")
    aaa = _load_fred("AAA10Y")
    vix = _load_fred("VIXCLS")
    credit_spread = (baa - aaa).dropna()
    f = pd.DataFrame({
        "rate": dgs10.diff() * 100.0,
        "dollar": np.log(dxy).diff(),
        "oil": np.log(oil).diff(),
        "credit": credit_spread.diff() * 100.0,
        "vol": vix.diff(),
    })
    return f.dropna()


def fetch_prices(tickers: list) -> pd.DataFrame:
    import yfinance as yf
    cols = {}
    for t in tickers:
        h = yf.Ticker(t).history(period="max", auto_adjust=True)
        if len(h) == 0:
            raise RuntimeError(f"yfinance EMPTY for {t}")
        px = h["Close"].copy()
        px.index = pd.to_datetime(px.index).tz_localize(None)
        cols[t] = px
    px = pd.DataFrame(cols)
    return px


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


def tier_suggest(t, p, bonf_alpha):
    """multivariate HAC t + p 기반 tier 제안 (sample-stage 와 동일 규칙)."""
    if not np.isfinite(t):
        return "hold"
    at = abs(t)
    if at >= 2.0 and p <= bonf_alpha:
        return "validated"
    if at >= 1.6:
        return "structural"
    return "reject"


def analyze_unit(y: pd.Series, fac: pd.DataFrame, bonf_alpha: float) -> dict:
    df = fac.join(y.rename("y"), how="inner").dropna()
    yy = df["y"]
    X = df[FACTORS]
    uni = {}
    for f in FACTORS:
        r = hac_reg(yy, X[[f]])
        uni[f] = {"beta": round(r[f][0], 4), "se": round(r[f][1], 4),
                  "t": round(r[f][2], 3), "p": round(r[f][3], 5), "n": r["_n"]}
    mr = hac_reg(yy, X)
    multi = {}
    for f in FACTORS:
        multi[f] = {"beta": round(mr[f][0], 4), "se": round(mr[f][1], 4),
                    "t": round(mr[f][2], 3), "p": round(mr[f][3], 5)}
    multi["_n"] = mr["_n"]
    multi["_r2"] = round(mr["_r2"], 4)
    vif = {k: round(v, 3) for k, v in compute_vif(X).items()}
    tiers = {f: tier_suggest(multi[f]["t"], multi[f]["p"], bonf_alpha) for f in FACTORS}
    return {
        "coverage_start": str(df.index.min().date()),
        "coverage_end": str(df.index.max().date()),
        "n": len(df),
        "adf_ret": round(adf_p(yy), 5),
        "univariate": uni,
        "multivariate": multi,
        "vif": vif,
        "tier_suggest": tiers,
    }


def main():
    factors = build_factors()
    adf_fac = {f: round(adf_p(factors[f]), 6) for f in FACTORS}

    px = fetch_prices(ALL_TICKERS)
    ret = np.log(px).diff()

    # Bonferroni: count units x factors
    n_units = sum(len(u) for u in SLEEVE_UNITS.values())
    n_comp = n_units * len(FACTORS)
    bonf_alpha = 0.05 / n_comp

    results = {
        "_frontmatter": {
            "title": "J축 factor β shadow validation — batch 5 sleeve (gold 재현 + 4 sleeve)",
            "tags": ["study/factor-beta", "shadow-validation", "J축", "batch-stage"],
            "date": "2026-06-01",
            "stage": "batch (점추정 박제 아님, shadow 검증 대상)",
            "scope": "core/study 미수정 · SEED Edit 제안만",
        },
        "meta": {
            "factors": FACTORS,
            "factor_source": "eq_us_defensive/raw/fred (DGS10/DTWEXBGS/DCOILWTICO/BAA10Y/AAA10Y/VIXCLS)",
            "price_source": "yfinance period=max auto_adjust=True (free)",
            "factor_coverage": [str(factors.index.min().date()), str(factors.index.max().date())],
            "adf_factor": adf_fac,
            "n_units": n_units,
            "n_comparisons": n_comp,
            "bonferroni_alpha": round(bonf_alpha, 6),
            "method": "z-score std beta, HAC(NW maxlag=5), univariate+multivariate(5f), VIF, ADF pre-test",
        },
        "sleeves": {},
    }

    for sleeve, units in SLEEVE_UNITS.items():
        results["sleeves"][sleeve] = {}
        for uname, tickers in units.items():
            avail = [t for t in tickers if t in ret.columns and ret[t].notna().sum() > 50]
            y = ret[avail].mean(axis=1).dropna()
            res = analyze_unit(y, factors, bonf_alpha)
            res["tickers"] = avail
            results["sleeves"][sleeve][uname] = res

    OUT.mkdir(exist_ok=True)
    (OUT / "batch-std-beta-5sleeve.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # console summary
    print(f"factor coverage {results['meta']['factor_coverage']}  ADF(factor)={adf_fac}")
    print(f"Bonferroni alpha = {bonf_alpha:.5f} ({n_comp} comparisons)\n")
    for sleeve, units in results["sleeves"].items():
        for uname, r in units.items():
            print(f"=== {sleeve} / {uname} {r['tickers']} n={r['multivariate']['_n']} "
                  f"cov {r['coverage_start']}~{r['coverage_end']} R2={r['multivariate']['_r2']} "
                  f"adf_ret={r['adf_ret']} ===")
            for f in FACTORS:
                m = r["multivariate"][f]
                u = r["univariate"][f]
                print(f"  {f:7s} multiβ={m['beta']:+.3f} t={m['t']:+.2f} p={m['p']:.4f} "
                      f"| uniβ={u['beta']:+.3f} t={u['t']:+.2f} | VIF={r['vif'][f]:.2f} "
                      f"-> {r['tier_suggest'][f]}")
            print()
    print("WROTE", OUT / "batch-std-beta-5sleeve.json")
    return results


if __name__ == "__main__":
    main()
