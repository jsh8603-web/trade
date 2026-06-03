# -*- coding: utf-8 -*-
"""measure_cross.py — us_mega_tech §M.3 cross (공통인자 β). us_defensive 미러 (FRED).

★compounder = long-duration growth → real_rate(DFII10) 민감 예상(성장주 듀레이션, 방어주와 동방향 음).
basket 전체 β + Mag7 vs AI-semi sub 비교. HAC + n 명시. ★FRED = eq_us_defensive/raw/fred 재사용.
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


def load_fred(t):
    df = pd.read_csv(FRED / f"{t}.csv", parse_dates=[0])
    s = df.set_index(df.columns[0]).iloc[:, 0]
    s = pd.to_numeric(s, errors="coerce").dropna(); s.index = pd.to_datetime(s.index)
    return s


def factors_monthly():
    feat = {}
    feat["rate"] = load_fred("DGS10").resample("ME").last().diff()
    feat["real_rate"] = load_fred("DFII10").resample("ME").last().diff()
    feat["dollar"] = load_fred("DTWEXBGS").resample("ME").last().pct_change()
    feat["vix"] = load_fred("VIXCLS").resample("ME").last().diff()
    try:
        feat["hy_oas"] = load_fred("BAMLH0A0HYM2").resample("ME").last().diff()
    except Exception:
        pass
    return pd.DataFrame(feat)


def beta(y, feat):
    df = pd.concat([y.rename("y"), feat], axis=1).dropna()
    if len(df) < 24:
        return {"note": "insufficient", "n": len(df)}
    X = sm.add_constant(df.drop(columns="y"))
    model = sm.OLS(df["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    out = {}
    for f in df.columns.drop("y"):
        out[f] = dict(beta=round(float(model.params[f]), 4), t=round(float(model.tvalues[f]), 2),
                      ci95=[round(float(model.conf_int().loc[f, 0]), 4), round(float(model.conf_int().loc[f, 1]), 4)])
    out["_meta"] = dict(n=len(df), r2=round(float(model.rsquared), 3))
    return out


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    uni = json.loads((DATA / "universe.json").read_text(encoding="utf-8")); tags = uni["tickers"]
    pxm = px.resample("ME").last(); retm = pxm.pct_change()
    feat = factors_monthly()

    out = {"basket_factor_beta": {}, "meta": {
        "note": "★compounder long-duration growth → real_rate(DFII10) 민감 예상. HAC maxlags=6. FRED 실데이터(defensive 재사용).",
        "factors": "rate(DGS10 Δ)/real_rate(DFII10 Δ)/dollar(DTWEXBGS %)/vix(Δ)/hy_oas(Δ)"}}
    out["basket_factor_beta"]["MEGA_TECH_ALL"] = beta(retm.mean(axis=1), feat)
    for sub in ["mag7", "ai_semi"]:
        cols = [t for t, s in tags.items() if s == sub and t in retm.columns]
        if cols:
            out["basket_factor_beta"][sub] = beta(retm[cols].mean(axis=1), feat)

    (ROOT / "validation-cross-v3.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("Saved validation-cross-v3.json\n")
    print(f"{'group':<16}{'rate':>14}{'real_rate':>14}{'dollar':>13}{'vix':>13}{'R2':>7}{'n':>5}")
    for g, b in out["basket_factor_beta"].items():
        if "_meta" not in b:
            continue
        def gg(f): return f"{b[f]['beta']:+.3f}({b[f]['t']:+.1f})" if f in b else "--"
        print(f"{g:<16}{gg('rate'):>14}{gg('real_rate'):>14}{gg('dollar'):>13}{gg('vix'):>13}{b['_meta']['r2']:>7}{b['_meta']['n']:>5}")


if __name__ == "__main__":
    main()
