# -*- coding: utf-8 -*-
"""measure_cross.py — us_defensive §M.3 cross 축 (공통인자 β). 한국 measure_cross 미러 (FRED).

§M.3 cross = 3소비자 라우팅 (산업 = 보고만):
  (1) 공통인자 exposure β (rate/real_rate/dollar/HY OAS/VIX) — contemporaneous, Σ_return 입력
      ★H5: bank rate+/utility rate− (defensive sub-sector β 분기) — utilities=rate 음(듀레이션), healthcare=중립
      ★H2: TSY(long duration) 노출 — utilities 가 TSY-like (rate sensitive)
  (2) customer-supplier momentum = defensive 는 supply-chain lead-lag 약 → sector-rotation 만 보고

★FRED 데이터 = 기존 eq_us_defensive/raw/fred/ CSV (실데이터 §1.7-D 통과: DGS10/DFII10/DTWEXBGS/HY OAS/VIX).
★sub-sector β 분기 (staples/utilities/healthcare/comm) = asset_stable 핵심 (rate 민감도 상이).
★block bootstrap / NW HAC (IID 아님, small-n rule §1.4).
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
FRED = Path("D:/projects/Inv/study-research/eq_us_defensive/raw/fred")


def load_fred(ticker):
    csv = FRED / f"{ticker}.csv"
    df = pd.read_csv(csv, parse_dates=[0])
    s = df.set_index(df.columns[0]).iloc[:, 0]
    s = pd.to_numeric(s, errors="coerce").dropna()
    s.index = pd.to_datetime(s.index)
    return s


def load_panels():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    uni = json.loads((DATA / "universe.json").read_text(encoding="utf-8"))
    tags = uni["tickers"]
    return px, tags


def sector_returns(px, tags):
    """sub-sector eq-weight 월간 수익 + 전체 defensive eq-weight."""
    pxm = px.resample("ME").last(); ret = pxm.pct_change()
    out = {"DEFENSIVE_ALL": ret.mean(axis=1)}
    for sec in set(tags.values()):
        cols = [t for t, s in tags.items() if s == sec and t in ret.columns]
        if cols:
            out[sec] = ret[cols].mean(axis=1)
    return pd.DataFrame(out).dropna(how="all")


def common_factors_monthly():
    """FRED 월간 변화 (rate/real_rate/dollar/HY OAS/VIX)."""
    feat = {}
    feat["rate"] = load_fred("DGS10").resample("ME").last().diff()
    feat["real_rate"] = load_fred("DFII10").resample("ME").last().diff()
    feat["dollar"] = load_fred("DTWEXBGS").resample("ME").last().pct_change()
    feat["hy_oas"] = load_fred("BAMLH0A0HYM2").resample("ME").last().diff()
    feat["vix"] = load_fred("VIXCLS").resample("ME").last().diff()
    return pd.DataFrame(feat)


def beta_regression(y, feat):
    """y(sector ret) ~ factors, Newey-West HAC."""
    df = pd.concat([y.rename("y"), feat], axis=1).dropna()
    if len(df) < 24:
        return {"note": "insufficient", "n": len(df)}
    X = sm.add_constant(df.drop(columns="y"))
    model = sm.OLS(df["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    out = {}
    for f in df.columns.drop("y"):
        out[f] = dict(beta=round(float(model.params[f]), 4), se=round(float(model.bse[f]), 4),
                      t=round(float(model.tvalues[f]), 2),
                      ci95=[round(float(model.conf_int().loc[f, 0]), 4), round(float(model.conf_int().loc[f, 1]), 4)],
                      contemporaneous=True)
    out["_meta"] = dict(n=len(df), r2=round(float(model.rsquared), 3))
    return out


def main():
    px, tags = load_panels()
    secret = sector_returns(px, tags)
    feat = common_factors_monthly()
    print(f"sector returns: {list(secret.columns)}, n_months={len(secret)}", flush=True)

    results = {"sub_sector_factor_beta": {}, "meta": {
        "note": "★H5 sub-sector rate β 분기: utilities rate 음(듀레이션) vs healthcare/staples. HAC maxlags=6. FRED 실데이터.",
        "factors": "rate(DGS10 Δ)/real_rate(DFII10 Δ)/dollar(DTWEXBGS %)/hy_oas(Δ)/vix(Δ)"}}
    for sec in secret.columns:
        results["sub_sector_factor_beta"][sec] = beta_regression(secret[sec], feat)

    (ROOT / "validation-cross-v3.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("Saved validation-cross-v3.json\n", flush=True)
    print("=== sub-sector factor β (contemporaneous, HAC maxlags=6) ===")
    print(f"{'sector':<14}{'rate':>9}{'real_rate':>11}{'dollar':>9}{'hy_oas':>9}{'vix':>9}{'R2':>7}{'n':>5}")
    for sec, b in results["sub_sector_factor_beta"].items():
        if "_meta" not in b:
            continue
        def g(f): return f"{b[f]['beta']:+.3f}({b[f]['t']:+.1f})" if f in b else "--"
        print(f"{sec:<14}{g('rate'):>14}{g('real_rate'):>14}{g('dollar'):>13}{g('hy_oas'):>13}{g('vix'):>13}"
              f"{b['_meta']['r2']:>7}{b['_meta']['n']:>5}")


if __name__ == "__main__":
    main()
