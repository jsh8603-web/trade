"""liq-incremental-freq.py — M3 유동성 factor 증분 판정 (frequency-matched, 0-inflation 제거).

★일별 버전(liq-incremental.py) 의 결함: net_liq/nfci(주별)·m2(월별)를 일별 ffill-diff →
변화 없는 날 0 폭주(m2 비0 279/4400) → spurious 저상관(VIF≈1.0 인위, orth≈0.99 인위).
spec/code match 위반(empirical-claim §1.3 frequency axis). frequency-matched 재측정으로 정정.

설계:
- WEEKLY(W-FRI): net_liq/nfci 네이티브 주별 + 기존 7 factor·sleeve return 주별 집계(혁신 sum / level last-diff).
- MONTHLY(ME): m2 네이티브 월별 + 동일 월별 집계.
- 각 후보를 8번째 factor 로 기존 7 에 추가 → joint VIF · FWL incremental · NW HAC · Bonferroni · tier.

base factor 변환: real/credit/vol/breakeven = level → period-last first-diff(Δ over period).
  dollar/oil/fx = Δlog over period(log(last)-log(prev last)). credit_mode hyoas|proxy 병행.
sleeve return = log(last_px)-log(prev last_px) (주별/월별 누적수익).
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

warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONUTF8", "1")
from dotenv import load_dotenv
load_dotenv("D:/projects/Inv/.env")

ROOT = Path(r"D:\projects\Inv\study-research")
FRED = ROOT / "eq_us_defensive" / "raw" / "fred"
LIQ = ROOT / "_factor_shadow" / "_liq_cache"
OUT = ROOT / "_factor_shadow"

BASE_FACTORS = ["real", "dollar", "oil", "credit", "vol", "breakeven", "fx"]
SLEEVE_TICKERS = {"us_stock": "SPY", "kr_stock": "EWY", "commodity": "DBC",
                  "gold": "GLD", "bond": "BND", "coin": "BTC-USD"}


def _load_fred(name: str) -> pd.Series:
    df = pd.read_csv(FRED / f"{name}.csv"); df.columns = ["date", "val"]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df["val"], errors="coerce"); s.index = df["date"]
    return s.dropna()


def _load_liq(name: str) -> pd.Series:
    df = pd.read_csv(LIQ / f"{name}.csv", index_col=0, parse_dates=True)
    return pd.to_numeric(df["val"], errors="coerce").dropna()


def base_levels(credit_mode: str = "proxy") -> dict:
    """factor 레벨 시리즈 dict. 변환은 freq 집계 시 적용."""
    out = {
        "real": _load_fred("DFII10"),
        "dollar": _load_fred("DTWEXBGS"),
        "oil": _load_fred("DCOILWTICO").pipe(lambda s: s[s > 0]),
        "vol": _load_fred("VIXCLS"),
        "breakeven": _load_liq("T5YIE"),
        "fx": _load_liq("DEXKOUS"),
    }
    if credit_mode == "hyoas":
        out["credit"] = _load_liq("BAMLH0A0HYM2")
    else:
        out["credit"] = (_load_fred("BAA10Y") - _load_fred("AAA10Y")).dropna()
    return out


LOG_FACTORS = {"dollar", "oil", "fx"}   # Δlog
DIFF_FACTORS = {"real", "credit", "vol", "breakeven"}  # first-diff of level


def resample_factor(s: pd.Series, rule: str, is_log: bool) -> pd.Series:
    last = s.resample(rule).last().dropna()
    return np.log(last).diff().dropna() if is_log else last.diff().dropna()


def liq_levels() -> dict:
    walcl = _load_liq("WALCL"); wtregen = _load_liq("WTREGEN"); rrp = _load_liq("RRPONTSYD")
    # net liq level on union daily index then we take period-last in resample
    idx = pd.date_range("2003-01-01", "2026-06-01", freq="D")
    nl = (walcl.reindex(idx, method="ffill") - wtregen.reindex(idx, method="ffill")
          - rrp.reindex(idx, method="ffill") * 1000.0)
    return {"net_liq": nl.dropna(), "nfci": _load_liq("NFCI"), "m2": _load_liq("M2SL")}


def resample_liq(name: str, s: pd.Series, rule: str) -> pd.Series:
    last = s.resample(rule).last().dropna()
    if name == "net_liq":
        return np.log(last.clip(lower=1)).diff().dropna()     # Δlog balance
    if name == "m2":
        return np.log(last).diff().dropna()                   # Δlog M2
    return last.diff().dropna()                               # nfci first-diff


def fetch_prices(tickers):
    import yfinance as yf
    cols = {}
    for t in tickers:
        h = yf.Ticker(t).history(period="max", auto_adjust=True)
        px = h["Close"].copy(); px.index = pd.to_datetime(px.index).tz_localize(None)
        cols[t] = px
    return pd.DataFrame(cols)


def sleeve_returns(px: pd.DataFrame, rule: str) -> pd.DataFrame:
    last = px.resample(rule).last()
    return np.log(last).diff().dropna(how="all")


def zscore(s):
    sd = s.std(ddof=0)
    return (s - s.mean()) / sd if sd > 0 else s * 0.0


def hac_reg(y, X, maxlags):
    yz = zscore(y); Xz = X.apply(zscore); Xc = sm.add_constant(Xz)
    m = sm.OLS(yz.values, Xc.values).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    names = ["const"] + list(X.columns)
    out = {nm: (float(m.params[i]), float(m.bse[i]), float(m.tvalues[i]), float(m.pvalues[i]))
           for i, nm in enumerate(names)}
    out["_n"] = int(m.nobs); out["_r2"] = float(m.rsquared); return out


def vif_of(X):
    Xz = X.apply(zscore); Xc = sm.add_constant(Xz).values; cols = ["const"] + list(X.columns)
    return {cols[i]: float(variance_inflation_factor(Xc, i)) for i in range(1, len(cols))}


def tier(t, p, alpha, vif, fwl_t):
    if vif >= 5.0:
        return "reject_doublecount"
    at = abs(t)
    if at >= 2.0 and p <= alpha and abs(fwl_t) >= 2.0:
        return "validated"
    if at >= 2.0 and abs(fwl_t) >= 2.0:
        return "structural"      # 유의하나 Bonferroni 미생존
    if at < 1.6:
        return "reject"
    return "reject_absorbed" if abs(fwl_t) < 2.0 else "structural"


def analyze(y, base_df, liq_s, cand, alpha, maxlags):
    facs = BASE_FACTORS + [cand]
    X = base_df.join(liq_s.rename(cand), how="inner")
    df = X.join(y.rename("y"), how="inner").dropna()
    if len(df) < 40:
        return {"n": len(df), "error": "insufficient"}
    yy = df["y"]; XX = df[facs]
    ur = hac_reg(yy, XX[[cand]], maxlags)
    uni = {"beta": round(ur[cand][0], 4), "t": round(ur[cand][2], 3), "p": round(ur[cand][3], 6)}
    mr = hac_reg(yy, XX, maxlags)
    jt = {"beta": round(mr[cand][0], 4), "t": round(mr[cand][2], 3), "p": round(mr[cand][3], 6)}
    multi = {f: round(mr[f][0], 4) for f in facs}
    v = {k: round(vv, 3) for k, vv in vif_of(XX).items()}
    cob = sm.OLS(zscore(XX[cand]).values, sm.add_constant(XX[BASE_FACTORS].apply(zscore)).values).fit()
    orth = pd.Series(cob.resid, index=df.index)
    orth_share = float(np.var(orth) / np.var(zscore(XX[cand]).values))
    inc = hac_reg(yy, orth.to_frame("o"), maxlags)
    fwl = {"beta": round(inc["o"][0], 4), "t": round(inc["o"][2], 3), "p": round(inc["o"][3], 6),
           "orth_var_share": round(orth_share, 4)}
    corr = {f: round(float(np.corrcoef(XX[cand], XX[f])[0, 1]), 3) for f in BASE_FACTORS}
    tl = tier(jt["t"], jt["p"], alpha, v[cand], fwl["t"])
    return {"coverage": [str(df.index.min().date()), str(df.index.max().date())], "n": len(df),
            "univariate": uni, "joint": jt, "joint_betas": multi, "vif": v,
            "incremental_fwl": fwl, "corr_with_base": corr, "tier": tl}


def run_freq(rule, cand_names, credit_mode, px, maxlags):
    bl = base_levels(credit_mode)
    base_cols = {f: resample_factor(bl[f], rule, f in LOG_FACTORS) for f in BASE_FACTORS}
    base_df = pd.DataFrame(base_cols).dropna()
    ll = liq_levels()
    liq_cols = {c: resample_liq(c, ll[c], rule) for c in cand_names}
    rets = sleeve_returns(px, rule)
    n_comp = len(SLEEVE_TICKERS) * len(cand_names)
    alpha = 0.05 / n_comp
    out = {"rule": rule, "credit_mode": credit_mode, "bonferroni_alpha": round(alpha, 6),
           "n_comparisons": n_comp, "base_coverage": [str(base_df.index.min().date()),
           str(base_df.index.max().date())], "base_n": len(base_df), "sleeves": {}}
    print(f"\n#### freq={rule} credit={credit_mode} cands={cand_names} "
          f"base n={len(base_df)} {base_df.index.min().date()}~{base_df.index.max().date()} "
          f"Bonf α={alpha:.5f}")
    for sleeve, tk in SLEEVE_TICKERS.items():
        if sleeve not in rets.columns:
            continue
        y = rets[sleeve].dropna()
        out["sleeves"][sleeve] = {}
        for c in cand_names:
            res = analyze(y, base_df, liq_cols[c], c, alpha, maxlags)
            out["sleeves"][sleeve][c] = res
            if "error" in res:
                print(f"  {sleeve:9s}/{c:8s} INSUFFICIENT n={res['n']}"); continue
            u, j, f = res["univariate"], res["joint"], res["incremental_fwl"]
            cmax = max(res["corr_with_base"].items(), key=lambda kv: abs(kv[1]))
            print(f"  {sleeve:9s}/{c:8s} n={res['n']:4d} uni β={u['beta']:+.3f} t={u['t']:+.2f} | "
                  f"joint β={j['beta']:+.3f} t={j['t']:+.2f} p={j['p']:.4f} | VIF={res['vif'][c]:.2f} | "
                  f"FWL t={f['t']:+.2f} | maxcorr {cmax[0]}={cmax[1]:+.2f} -> {res['tier']}")
    return out


def main():
    px = fetch_prices(list(SLEEVE_TICKERS.values()))
    px = px.rename(columns={v: k for k, v in SLEEVE_TICKERS.items()})
    results = {"_meta": {"title": "M3 유동성 factor 증분 — frequency-matched(0-inflation 제거)",
                         "date": "2026-06-02",
                         "method": "weekly(W-FRI) net_liq/nfci + monthly(ME) m2, z-score std β, HAC NW, VIF, FWL incremental, Bonferroni",
                         "base_factors": BASE_FACTORS,
                         "note": "일별 ffill-diff 0-inflation artifact 정정. NW maxlags: weekly=4 monthly=3"},
               "weekly": {}, "monthly": {}}
    for cm in ["proxy", "hyoas"]:
        results["weekly"][cm] = run_freq("W-FRI", ["net_liq", "nfci"], cm, px, maxlags=4)
    for cm in ["proxy", "hyoas"]:
        results["monthly"][cm] = run_freq("ME", ["m2", "net_liq", "nfci"], cm, px, maxlags=3)
    OUT.mkdir(exist_ok=True)
    (OUT / "liq-incremental-freq.json").write_text(json.dumps(results, indent=2, ensure_ascii=False),
                                                   encoding="utf-8")
    print("\nWROTE", OUT / "liq-incremental-freq.json")


if __name__ == "__main__":
    main()
