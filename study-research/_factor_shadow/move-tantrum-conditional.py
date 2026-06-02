"""move-tantrum-conditional.py — M4-B: bond vol(MOVE) = 조건부로 살아나나 (재판정).

자문 주장: MOVE 독립 정보는 rate-tantrum(금리주도 스트레스, VIX 잠잠한데 MOVE만 튐)에 집중.
pooled 회귀선 희석. equity-vol(VIX) 직교화는 과잉통제(bad controls).

판정 설계:
- rate-tantrum 더미 = {|Δ10y| 상위 decile ∧ VIX 중앙값 이하}. = 금리는 출렁이는데 주식 vol 잠잠.
- 그 국면 *안에서* MOVE(Δlog 또는 level)가 rate level(DGS10) 통제 후 자산수익에 incremental β.
- 대조: ① full-sample(Y5 재현) ② tantrum-only ③ non-tantrum. 조건부서만 살아나면 부활 후보.
- bad-control 검증: VIX 통제 有/無 둘 다(자문 "과잉통제" 주장 검증).
- NW-HAC, LOO(leave-one-episode/year), Bonferroni.

★MOVE = Yahoo ^MOVE 2002-11~. 자산 = us_stock/bond/commodity/gold (rate-tantrum 노출 다른 sleeve).
★Y5 에서 joint β→0 drop. 조건부도 0 이면 폐기 확정(자문 반박).
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
OUT = ROOT / "_factor_shadow"

SLEEVE_TICKERS = {"us_stock": "SPY", "bond_ief": "IEF", "commodity": "DBC", "gold": "GLD"}


def _load_fred(name: str) -> pd.Series:
    df = pd.read_csv(FRED / f"{name}.csv"); df.columns = ["date", "val"]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df["val"], errors="coerce"); s.index = df["date"]
    return s.dropna()


def _fetch_move():
    import yfinance as yf
    h = yf.Ticker("^MOVE").history(period="max", auto_adjust=True)
    px = h["Close"].copy(); px.index = pd.to_datetime(px.index).tz_localize(None)
    return px.dropna()


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


def loo_year(y, X, col, maxlags):
    years = sorted(set(y.index.year)); ts, betas = [], []
    for yr in years:
        mask = y.index.year != yr
        if mask.sum() < 30:
            continue
        try:
            r = hac_reg(y[mask], X[mask], maxlags); betas.append(r[col][0]); ts.append(r[col][2])
        except Exception:
            continue
    if not ts:
        return None
    return {"folds": len(ts), "beta_min": round(min(betas), 4), "beta_max": round(max(betas), 4),
            "t_min": round(min(ts), 3), "t_max": round(max(ts), 3),
            "sign_stable": bool(min(betas) * max(betas) > 0),
            "t_all_sig": bool(all(abs(t) >= 2.0 for t in ts))}


def build_daily():
    dgs10 = _load_fred("DGS10"); vix = _load_fred("VIXCLS"); move = _fetch_move()
    d10 = dgs10.diff().abs()  # |Δ10y| daily
    df = pd.DataFrame({"dgs10": dgs10, "abs_d10y": d10, "vix": vix,
                       "move_dlog": np.log(move).diff(), "move_lvl": move}).dropna()
    return df


def reg_block(y, X, col, maxlags, alpha, want_loo=True):
    df = pd.concat([y.rename("y"), X], axis=1).dropna()
    if len(df) < 30:
        return {"n": len(df), "error": "insufficient"}
    r = hac_reg(df["y"], df[list(X.columns)], maxlags)
    rec = {"n": len(df), "beta": round(r[col][0], 4), "t": round(r[col][2], 3), "p": round(r[col][3], 5),
           "survives_bonferroni": bool(r[col][3] <= alpha and abs(r[col][2]) >= 2.0)}
    if want_loo and len(df) >= 60:
        rec["loo"] = loo_year(df["y"], df[list(X.columns)], col, maxlags)
    return rec


def main():
    daily = build_daily()
    px = fetch_prices(list(SLEEVE_TICKERS.values()))
    px = px.rename(columns={v: k for k, v in SLEEVE_TICKERS.items()})
    rets = np.log(px).diff()

    # rate-tantrum 더미: |Δ10y| 상위 decile (rolling 정의 회피 = 전표본 분위, 학습라벨 성격)
    #  ∧ VIX 중앙값 이하. = 금리 급변 + 주식 vol 잠잠.
    thr_d10 = daily["abs_d10y"].quantile(0.90)
    vix_med = daily["vix"].median()
    tantrum = (daily["abs_d10y"] >= thr_d10) & (daily["vix"] <= vix_med)
    print(f"abs_d10y p90={thr_d10:.3f} bp/day, VIX median={vix_med:.1f}")
    print(f"tantrum days={int(tantrum.sum())}/{len(daily)} ({100*tantrum.mean():.1f}%)  "
          f"coverage {daily.index.min().date()}~{daily.index.max().date()}")

    sleeves = [s for s in SLEEVE_TICKERS if s in rets.columns]
    n_comp = len(sleeves) * 3  # full / tantrum / nontantrum (joint w/ vix)
    alpha = 0.05 / n_comp
    print(f"Bonferroni α = {alpha:.5f} ({n_comp} comparisons)\n")

    results = {"_meta": {"title": "M4-B MOVE rate-tantrum 조건부 재판정", "date": "2026-06-02",
                         "tantrum_def": f"|Δ10y|>=p90({thr_d10:.3f}) AND VIX<=median({vix_med:.1f})",
                         "tantrum_days": int(tantrum.sum()), "total_days": len(daily),
                         "method": "daily MOVE Δlog → sleeve return, rate(DGS10 level) 통제, VIX 통제 有/無, "
                                   "full/tantrum/nontantrum split, NW-HAC=5, LOO year, Bonferroni",
                         "note": "Y5 joint β→0(VIX 흡수). 자문=tantrum 국면 한정 살아있다+VIX직교 bad-control 주장. "
                                 "조건부도 0이면 폐기 확정."},
               "bonferroni_alpha": round(alpha, 6), "sleeves": {}}

    for sleeve in sleeves:
        y = rets[sleeve].dropna()
        idx = daily.index.intersection(y.index)
        dd = daily.loc[idx]; yy = y.loc[idx]; tt = tantrum.loc[idx]
        # 통제축: rate level(DGS10 z), VIX(Δ). MOVE = move_dlog.
        ctrl_with_vix = pd.DataFrame({"rate": dd["dgs10"], "vix_d": dd["vix"].diff(), "move": dd["move_dlog"]})
        ctrl_no_vix = pd.DataFrame({"rate": dd["dgs10"], "move": dd["move_dlog"]})
        block = {}
        # full sample joint (with VIX) = Y5 재현
        block["full_with_vix"] = reg_block(yy, ctrl_with_vix, "move", 5, alpha)
        block["full_no_vix"] = reg_block(yy, ctrl_no_vix, "move", 5, alpha)
        # tantrum-only (자문 핵심)
        block["tantrum_with_vix"] = reg_block(yy[tt], ctrl_with_vix.loc[tt], "move", 3, alpha)
        block["tantrum_no_vix"] = reg_block(yy[tt], ctrl_no_vix.loc[tt], "move", 3, alpha)
        # non-tantrum 대조
        block["nontantrum_no_vix"] = reg_block(yy[~tt], ctrl_no_vix.loc[~tt], "move", 5, alpha)
        results["sleeves"][sleeve] = block
        print(f"=== {sleeve} ===")
        for k, r in block.items():
            if "error" in r:
                print(f"  {k:20s} INSUFF n={r['n']}"); continue
            lo = r.get("loo")
            loos = "" if not lo else f"LOO t[{lo['t_min']:+.1f},{lo['t_max']:+.1f}] stab={lo['sign_stable']}"
            print(f"  {k:20s} n={r['n']:4d} MOVE β={r['beta']:+.4f} t={r['t']:+.2f} p={r['p']:.4f} "
                  f"bonf={r['survives_bonferroni']} {loos}")
        print()

    OUT.mkdir(exist_ok=True)
    (OUT / "move-tantrum-conditional.json").write_text(json.dumps(results, indent=2, ensure_ascii=False),
                                                       encoding="utf-8")
    print("WROTE", OUT / "move-tantrum-conditional.json")


if __name__ == "__main__":
    main()
