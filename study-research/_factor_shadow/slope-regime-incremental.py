"""slope-regime-incremental.py — M4-A: slope(T10Y2Y) = regime layer 신호인가 (재판정).

자문 주장: slope 예측력은 business-cycle 주파수(12-18M 침체 선행)에 있다. 일별 indicator 로
쓰니 죽은 것(Y5 joint commod +0.015 비유의 drop). regime layer state 로 이사해야.

판정 설계 (horizon/조건 바꿔도 증분 진짜 있나):
- slope = (DGS10 - DGS2) level + Δ, 월(ME)·분기(QE) 빈도.
- y = forward k-month 자산 누적수익 (us_stock=SPY, bond=BND/IEF, commodity=DBC), k∈{3,6,12}.
- 증분(FWL): 기존 regime 통제축 = inflation_z(breakeven Δ + core) + vol_z(VIX level) 통제 후
  slope 잔차계수가 유의한가. = "물가+vol regime 위에 slope 가 더 설명하나".
- 침체더미: USREC(NBER, 학습라벨 — 사후확정) 를 slope level 로 probit, forward 6/12M lead.
- NW-HAC(forward overlap → maxlags=k), LOO(leave-one-year-out), Bonferroni.

★주의: Y5 에서 drop 된 신호. "자문이 살리라 했으니 살린다" 아님. 증분 0 이면 폐기 확정.
★core/study 미수정. off-path 산출 전용.
"""
from __future__ import annotations

import json
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONUTF8", "1")
from dotenv import load_dotenv
load_dotenv("D:/projects/Inv/.env")

ROOT = Path(r"D:\projects\Inv\study-research")
FRED = ROOT / "eq_us_defensive" / "raw" / "fred"
LIQ = ROOT / "_factor_shadow" / "_liq_cache"
OUT = ROOT / "_factor_shadow"

# forward 수익 자산. bond 는 IEF(7-10Y, slope 와 가장 직접) + BND(agg) 둘 다.
SLEEVE_TICKERS = {"us_stock": "SPY", "bond_ief": "IEF", "bond_agg": "BND", "commodity": "DBC"}


def _load_fred(name: str) -> pd.Series:
    df = pd.read_csv(FRED / f"{name}.csv"); df.columns = ["date", "val"]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df["val"], errors="coerce"); s.index = df["date"]
    return s.dropna()


def _load_liq(name: str) -> pd.Series:
    df = pd.read_csv(LIQ / f"{name}.csv", index_col=0, parse_dates=True)
    return pd.to_numeric(df["val"], errors="coerce").dropna()


def _fred_api(series_id: str) -> pd.Series:
    from fredapi import Fred
    fred = Fred(api_key=os.environ.get("FRED_API_KEY"))
    return fred.get_series(series_id).dropna()


def fetch_prices(tickers):
    import yfinance as yf
    cols = {}
    for t in tickers:
        h = yf.Ticker(t).history(period="max", auto_adjust=True)
        px = h["Close"].copy(); px.index = pd.to_datetime(px.index).tz_localize(None)
        cols[t] = px
    return pd.DataFrame(cols)


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


def loo_by_year(y, X, col, maxlags):
    """leave-one-year-out: drop each calendar year, re-fit, collect target t/beta."""
    years = sorted(set(y.index.year))
    ts, betas = [], []
    for yr in years:
        mask = y.index.year != yr
        if mask.sum() < 24:
            continue
        try:
            r = hac_reg(y[mask], X[mask], maxlags)
            betas.append(r[col][0]); ts.append(r[col][2])
        except Exception:
            continue
    if not ts:
        return None
    return {"loo_n_folds": len(ts), "beta_min": round(min(betas), 4), "beta_max": round(max(betas), 4),
            "t_min": round(min(ts), 3), "t_max": round(max(ts), 3),
            "sign_stable": bool(min(betas) * max(betas) > 0),
            "t_all_sig": bool(all(abs(t) >= 2.0 for t in ts))}


def build_regime_controls(rule):
    """기존 regime 통제축: inflation_z(breakeven Δ rolling z) + vol_z(VIX level z)."""
    vix = _load_fred("VIXCLS").resample(rule).last()
    be = _load_liq("T5YIE").resample(rule).last()
    # inflation regime proxy: breakeven level z (rolling own-history) — _inflation_signal 정합 방향
    be_z = (be - be.rolling(36, min_periods=12).mean()) / be.rolling(36, min_periods=12).std()
    vix_z = (vix - vix.rolling(36, min_periods=12).mean()) / vix.rolling(36, min_periods=12).std()
    return pd.DataFrame({"infl_z": be_z, "vol_z": vix_z}).dropna()


def run_slope_forward(rule, horizons, px, maxlags_base):
    dgs10 = _load_fred("DGS10"); dgs2 = _load_fred("DGS2")
    slope_lvl = (dgs10 - dgs2).resample(rule).last().dropna()
    slope_d = slope_lvl.diff().dropna()
    ctrls = build_regime_controls(rule)
    rets = np.log(px.resample(rule).last()).diff()  # 1-period log return per sleeve

    out = {"rule": rule, "results": {}}
    sleeves = [s for s in SLEEVE_TICKERS if s in rets.columns]
    n_comp = len(sleeves) * len(horizons) * 2  # level+delta
    alpha = 0.05 / n_comp
    out["n_comparisons"] = n_comp; out["bonferroni_alpha"] = round(alpha, 6)
    print(f"\n#### freq={rule} sleeves={sleeves} horizons={horizons} Bonf α={alpha:.5f}")

    for sleeve in sleeves:
        r1 = rets[sleeve].dropna()
        out["results"][sleeve] = {}
        for k in horizons:
            # forward k-period cumulative return
            fwd = r1.rolling(k).sum().shift(-k).dropna()
            maxlags = maxlags_base if rule == "ME" else max(1, maxlags_base // 3)
            maxlags = max(maxlags, k - 1) if rule == "ME" else maxlags
            for label, sl in [("slope_level", slope_lvl), ("slope_delta", slope_d)]:
                # base regime model
                base_df = pd.concat([fwd.rename("y"), ctrls], axis=1).dropna()
                # full model with slope
                full_df = pd.concat([fwd.rename("y"), ctrls, sl.rename("slope")], axis=1).dropna()
                if len(full_df) < 36:
                    out["results"][sleeve][f"{label}_fwd{k}"] = {"n": len(full_df), "error": "insufficient"}
                    continue
                y = full_df["y"]; X = full_df[["infl_z", "vol_z", "slope"]]
                # univariate slope
                ur = hac_reg(y, X[["slope"]], maxlags)
                # joint (with regime controls) = FWL incremental
                jr = hac_reg(y, X, maxlags)
                # FWL orthogonalize slope ⊥ controls
                cob = sm.OLS(zscore(X["slope"]).values,
                             sm.add_constant(X[["infl_z", "vol_z"]].apply(zscore)).values).fit()
                orth = pd.Series(cob.resid, index=full_df.index)
                orth_share = float(np.var(orth) / np.var(zscore(X["slope"]).values))
                fwl = hac_reg(y, orth.to_frame("o"), maxlags)
                loo = loo_by_year(y, X, "slope", maxlags)
                rec = {
                    "coverage": [str(y.index.min().date()), str(y.index.max().date())], "n": len(full_df),
                    "univariate": {"beta": round(ur["slope"][0], 4), "t": round(ur["slope"][2], 3),
                                   "p": round(ur["slope"][3], 5)},
                    "joint_with_regime": {"beta": round(jr["slope"][0], 4), "t": round(jr["slope"][2], 3),
                                          "p": round(jr["slope"][3], 5),
                                          "infl_t": round(jr["infl_z"][2], 2), "vol_t": round(jr["vol_z"][2], 2)},
                    "fwl_incremental": {"beta": round(fwl["o"][0], 4), "t": round(fwl["o"][2], 3),
                                        "p": round(fwl["o"][3], 5), "orth_var_share": round(orth_share, 4)},
                    "loo": loo, "maxlags": maxlags,
                    "survives_bonferroni": bool(jr["slope"][3] <= alpha and abs(jr["slope"][2]) >= 2.0),
                }
                out["results"][sleeve][f"{label}_fwd{k}"] = rec
                j = rec["joint_with_regime"]; f = rec["fwl_incremental"]
                loos = "" if not loo else f"LOO t[{loo['t_min']:+.1f},{loo['t_max']:+.1f}] stable={loo['sign_stable']}"
                print(f"  {sleeve:9s} {label:11s} fwd{k:2d}m n={rec['n']:3d} | uni β={rec['univariate']['beta']:+.3f} "
                      f"t={rec['univariate']['t']:+.2f} | joint(+regime) β={j['beta']:+.3f} t={j['t']:+.2f} p={j['p']:.4f} "
                      f"| FWL incr t={f['t']:+.2f} share={f['orth_var_share']:.2f} | bonf={rec['survives_bonferroni']} {loos}")
    return out


def run_recession_probit():
    """slope level → USREC forward 6/12M lead (probit). 학습라벨(NBER 사후확정) 한정."""
    dgs10 = _load_fred("DGS10"); dgs2 = _load_fred("DGS2")
    slope_lvl = (dgs10 - dgs2).resample("ME").last().dropna()
    usrec = _fred_api("USREC").resample("ME").last().dropna()
    out = {}
    for lead in [6, 12]:
        # predict USREC at t+lead from slope at t
        rec_fwd = usrec.shift(-lead)
        df = pd.concat([slope_lvl.rename("slope"), rec_fwd.rename("rec")], axis=1).dropna()
        df = df[df.index >= "2003-01-01"]  # align with TIPS-era / consistent sample
        if len(df) < 50:
            out[f"lead{lead}m"] = {"n": len(df), "error": "insufficient"}; continue
        X = sm.add_constant(zscore(df["slope"]).values)
        try:
            m = sm.Probit(df["rec"].values, X).fit(disp=0, cov_type="HAC", cov_kwds={"maxlags": lead})
            beta, t, p = float(m.params[1]), float(m.tvalues[1]), float(m.pvalues[1])
            # pseudo R2
            out[f"lead{lead}m"] = {"n": len(df), "slope_beta": round(beta, 4), "t": round(t, 3),
                                   "p": round(p, 5), "pseudo_r2": round(float(m.prsquared), 4),
                                   "n_recession_months": int(df["rec"].sum()),
                                   "coverage": [str(df.index.min().date()), str(df.index.max().date())]}
        except Exception as e:
            out[f"lead{lead}m"] = {"n": len(df), "error": str(e)[:80]}
        r = out[f"lead{lead}m"]
        if "error" not in r:
            print(f"  USREC probit lead{lead}m n={r['n']} (rec={r['n_recession_months']}) "
                  f"slope β={r['slope_beta']:+.3f} t={r['t']:+.2f} p={r['p']:.4f} pseudoR2={r['pseudo_r2']}")
    return out


def main():
    px = fetch_prices(list(SLEEVE_TICKERS.values()))
    px = px.rename(columns={v: k for k, v in SLEEVE_TICKERS.items()})
    results = {"_meta": {"title": "M4-A slope(T10Y2Y) regime-layer 증분 재판정",
                         "date": "2026-06-02",
                         "method": "월(ME)·분기(QE) slope level+Δ → forward 3/6/12M 자산수익 회귀, "
                                   "inflation_z+vol_z regime FWL 증분, NW-HAC, LOO leave-one-year, "
                                   "Bonferroni; + USREC probit lead 6/12m",
                         "note": "Y5 일별 joint drop(commod +0.015). 자문=business-cycle freq 로 이사 주장. "
                                 "horizon/조건 바꿔 증분 진짜 있나 판정. USREC=NBER 사후확정 학습라벨."},
               "monthly": {}, "quarterly": {}, "recession_probit": {}}
    print("=" * 80, "\nMONTHLY forward")
    results["monthly"] = run_slope_forward("ME", [3, 6, 12], px, maxlags_base=12)
    print("=" * 80, "\nQUARTERLY forward")
    results["quarterly"] = run_slope_forward("QE", [2, 4], px, maxlags_base=4)
    print("=" * 80, "\nRECESSION PROBIT (USREC 학습라벨)")
    results["recession_probit"] = run_recession_probit()
    OUT.mkdir(exist_ok=True)
    (OUT / "slope-regime-incremental.json").write_text(json.dumps(results, indent=2, ensure_ascii=False),
                                                       encoding="utf-8")
    print("\nWROTE", OUT / "slope-regime-incremental.json")


if __name__ == "__main__":
    main()
