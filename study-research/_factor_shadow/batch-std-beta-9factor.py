"""batch-std-beta-9factor.py — Y5 factor codify: 8 measured factor 통일 multivariate 재측정.

P2 독립 opus audit(a8f746b2) 가 sign/sleeve/robustness 를 확정한 신규 축(real/MOVE/breakeven/slope)을
기존 5축(rate→real 교체·dollar·oil·credit·vol)과 ★단일 multivariate 설계에서 재측정한다. SEED_CELLS
최종 magnitude 는 이 통일 batch 산출에서 나온다(audit=sign/sleeve verdict, batch=magnitude — §6 codify).

batch-std-beta-5sleeve.py 방법론 미러(동일 source·z-score std β·HAC NW=5·VIF·univariate+multivariate):
  - real    = DFII10 first-diff (★rate=DGS10 교체, VIF 0.914 공선 회피, 조합B)
  - dollar  = DTWEXBGS Δlog
  - oil     = DCOILWTICO Δlog (2020-04-20 음가 제거)
  - credit  = (BAA10Y-AAA10Y) first-diff (5sleeve 와 동일 measure)
  - vol     = VIXCLS first-diff (5sleeve 와 동일 — diff, dlog 아님)
  - move    = ^MOVE Δlog (Yahoo, FRED 미존재 / §6: Δln)
  - breakeven = T5YIE first-diff (FRED)
  - slope   = (DGS10 - DGS2) first-diff (= T10Y2Y, FRED 직접 캐시 없어 구성)
  - fx      = denomination 구조값(측정 대상 아님 — 본 스크립트 미포함, SEED 에서 +1.0 직접 부여)

★z-score 표준화라 *100 bp 스케일 무관(washed out). VIF 게이트: 전 factor < 5 필수(real+slope+breakeven
공선 폭발 차단). gold 재현 = 기존 SEED dollar/oil 부호·크기대 일치 → 방법 신뢰성 게이트.

★core/study 미수정. 산출물 작성·실행 전용(off-path).
"""
from __future__ import annotations

import json
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tsa.stattools import adfuller

warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONUTF8", "1")
from dotenv import load_dotenv
load_dotenv("D:/projects/Inv/.env")

ROOT = Path(r"D:\projects\Inv\study-research")
FRED = ROOT / "eq_us_defensive" / "raw" / "fred"
OUT = ROOT / "_factor_shadow"

FACTORS = ["real", "dollar", "oil", "credit", "vol", "move", "breakeven", "slope"]

SLEEVE_UNITS = {
    "gold": {"GOLD": ["GLD"]},
    "eq_us_cyclical": {"CYCLICAL_PRO": ["XLB", "XLI", "SOXX"]},
    "eq_intl": {"EQ_INTL": ["EFA", "EEM"]},
    "reit": {"REIT": ["VNQ"]},
    "commodity": {"COMMODITY": ["DBC"]},
}
ALL_TICKERS = sorted({t for u in SLEEVE_UNITS.values() for ts in u.values() for t in ts})


def _load_fred(name: str) -> pd.Series:
    df = pd.read_csv(FRED / f"{name}.csv")
    df.columns = ["date", "val"]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df["val"], errors="coerce")
    s.index = df["date"]
    return s.dropna()


def _fetch_fred_api(series_id: str) -> pd.Series:
    from fredapi import Fred
    fred = Fred(api_key=os.environ.get("FRED_API_KEY"))
    return fred.get_series(series_id).dropna()


def _fetch_move() -> pd.Series:
    import yfinance as yf
    h = yf.Ticker("^MOVE").history(period="max", auto_adjust=True)
    px = h["Close"].copy()
    px.index = pd.to_datetime(px.index).tz_localize(None)
    return px.dropna()


def build_factors() -> pd.DataFrame:
    dgs10 = _load_fred("DGS10")
    dgs2 = _load_fred("DGS2")
    dfii10 = _load_fred("DFII10")
    dxy = _load_fred("DTWEXBGS")
    oil = _load_fred("DCOILWTICO"); oil = oil[oil > 0]
    baa = _load_fred("BAA10Y"); aaa = _load_fred("AAA10Y")
    vix = _load_fred("VIXCLS")
    t5yie = _fetch_fred_api("T5YIE")
    move = _fetch_move()
    slope_level = (dgs10 - dgs2).dropna()
    credit_spread = (baa - aaa).dropna()
    f = pd.DataFrame({
        "real": dfii10.diff(),
        "dollar": np.log(dxy).diff(),
        "oil": np.log(oil).diff(),
        "credit": credit_spread.diff(),
        "vol": vix.diff(),
        "move": np.log(move).diff(),
        "breakeven": t5yie.diff(),
        "slope": slope_level.diff(),
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
    return pd.DataFrame(cols)


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
    yy = df["y"]; X = df[FACTORS]
    uni = {}
    for f in FACTORS:
        r = hac_reg(yy, X[[f]])
        uni[f] = {"beta": round(r[f][0], 4), "se": round(r[f][1], 4),
                  "t": round(r[f][2], 3), "p": round(r[f][3], 5), "n": r["_n"]}
    mr = hac_reg(yy, X)
    multi = {f: {"beta": round(mr[f][0], 4), "se": round(mr[f][1], 4),
                 "t": round(mr[f][2], 3), "p": round(mr[f][3], 5)} for f in FACTORS}
    multi["_n"] = mr["_n"]; multi["_r2"] = round(mr["_r2"], 4)
    vif = {k: round(v, 3) for k, v in compute_vif(X).items()}
    tiers = {f: tier_suggest(multi[f]["t"], multi[f]["p"], bonf_alpha) for f in FACTORS}
    return {"coverage_start": str(df.index.min().date()), "coverage_end": str(df.index.max().date()),
            "n": len(df), "adf_ret": round(adf_p(yy), 5),
            "univariate": uni, "multivariate": multi, "vif": vif, "tier_suggest": tiers}


def main():
    factors = build_factors()
    adf_fac = {f: round(adf_p(factors[f]), 6) for f in FACTORS}
    print(f"factor coverage {factors.index.min().date()}~{factors.index.max().date()} n={len(factors)}")
    print(f"ADF(factor)={adf_fac}")

    px = fetch_prices(ALL_TICKERS)
    ret = np.log(px).diff()
    n_units = sum(len(u) for u in SLEEVE_UNITS.values())
    n_comp = n_units * len(FACTORS)
    bonf_alpha = 0.05 / n_comp
    print(f"Bonferroni alpha = {bonf_alpha:.6f} ({n_comp} comparisons)\n")

    results = {
        "_frontmatter": {"title": "Y5 factor codify — 8-factor 통일 multivariate 재측정",
                         "tags": ["study/factor-beta", "Y5-codify", "9factor"],
                         "date": "2026-06-02",
                         "scope": "core/study 미수정 · SEED 재측정 산출"},
        "meta": {"factors": FACTORS,
                 "factor_source": "FRED 캐시(DFII10/DTWEXBGS/DCOILWTICO/BAA10Y/AAA10Y/VIXCLS/DGS10/DGS2) + fredapi(T5YIE) + yfinance(^MOVE)",
                 "factor_coverage": [str(factors.index.min().date()), str(factors.index.max().date())],
                 "adf_factor": adf_fac, "n_comparisons": n_comp, "bonferroni_alpha": round(bonf_alpha, 6),
                 "method": "z-score std beta, HAC(NW=5), multivariate(8f)+univariate, VIF, ADF; rate→real 교체"},
        "sleeves": {},
    }
    max_vif = 0.0
    for sleeve, units in SLEEVE_UNITS.items():
        results["sleeves"][sleeve] = {}
        for uname, tickers in units.items():
            avail = [t for t in tickers if t in ret.columns and ret[t].notna().sum() > 50]
            y = ret[avail].mean(axis=1).dropna()
            res = analyze_unit(y, factors, bonf_alpha)
            res["tickers"] = avail
            results["sleeves"][sleeve][uname] = res
            max_vif = max(max_vif, max(res["vif"].values()))
            print(f"=== {sleeve}/{uname} {avail} n={res['multivariate']['_n']} "
                  f"cov {res['coverage_start']}~{res['coverage_end']} R2={res['multivariate']['_r2']} ===")
            for f in FACTORS:
                m = res["multivariate"][f]
                print(f"  {f:10s} multiβ={m['beta']:+.4f} t={m['t']:+.2f} p={m['p']:.4f} "
                      f"VIF={res['vif'][f]:.2f} -> {res['tier_suggest'][f]}")
            print()
    results["meta"]["max_vif"] = round(max_vif, 3)
    print(f"★MAX VIF across all units = {max_vif:.3f}  ({'PASS <5' if max_vif < 5 else 'FAIL ≥5 공선'})")
    OUT.mkdir(exist_ok=True)
    (OUT / "batch-std-beta-9factor.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print("WROTE", OUT / "batch-std-beta-9factor.json")
    return results


if __name__ == "__main__":
    main()
