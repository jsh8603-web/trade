# -*- coding: utf-8 -*-
"""measure_rotation_valband.py — 산업 aggregate valuation band → forward (rotation, plan §10 S5.5).

★team-lead 명시 "valuation밴드" + plan "지표 이연 금지" 이행.
산업 aggregate PBR = Σ(시총_PIT) / Σ(equity_PIT, DART rcept_dt 이후) → rolling z(24M) → forward 예측.
= "산업 valuation 이 자기 역사 대비 비싸면(z高) forward 약세(mean-reversion)" rotation 신호.

PIT: equity = DART rcept_dt(공시일) 이후만 적용(lookahead 회피). 시총 = price[t]×shares_approx.
shares_approx = universe Marcap / 최근 종가 (정밀 PIT shares 부재 = collector_plan, 근사 명시).
"""
from __future__ import annotations
import sys, io, json, os
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
IND_ROOT = ROOT.parent
INDUSTRIES = ["semiconductor", "auto", "financial", "battery", "chemical", "refining",
              "shipbuilding", "steel", "bio", "consumer", "telecom", "aitech"]
HORIZONS_M = {"y_20d": 1, "y_60d": 3}
OOS_SPLIT = "2023-01-01"
T_BREAKEVEN = 2.802

# measure_rotation.py 통계 인프라 재사용
import importlib.util as _ilu
spec = _ilu.spec_from_file_location("mr", ROOT / "measure_rotation.py")
mr = _ilu.module_from_spec(spec); spec.loader.exec_module(mr)
try:
    sys.stdout = io.TextIOWrapper(os.fdopen(os.dup(1), "wb"), encoding="utf-8")
except Exception:
    pass


def industry_pbr(sector):
    """산업 aggregate PBR 월간 시계열 (PIT-safe). = Σ(price×shares) / Σ(equity as-of, rcept_dt 이후)."""
    d = IND_ROOT / sector / "raw-v3" / "data"
    px = pd.read_parquet(d / "prices.parquet"); px.index = pd.to_datetime(px.index)
    u = pd.read_parquet(d / "universe.parquet"); u["Code"] = u["Code"].astype(str).str.zfill(6)
    try:
        dart = pd.read_parquet(d / "dart_financials.parquet")
    except Exception:
        return None
    dart["code"] = dart["code"].astype(str).str.zfill(6)
    dart["rcept"] = pd.to_datetime(dart["rcept_dt"], format="%Y%m%d")
    dart = dart[dart["equity"] > 0].sort_values("rcept")

    last_px = px.iloc[-1]
    shares = {row["Code"]: row["Marcap"] / last_px[row["Code"]]
              for _, row in u.iterrows()
              if row["Code"] in px.columns and pd.notna(row.get("Marcap")) and last_px.get(row["Code"], 0) > 0}
    pxm = px.resample("ME").last().loc["2019-01-01":]
    codes = [c for c in shares if c in dart["code"].unique() and c in pxm.columns]
    if len(codes) < 3:
        return None

    pbr = pd.Series(index=pxm.index, dtype=float)
    for dt in pxm.index:
        tot_mcap = tot_eq = 0.0
        for c in codes:
            p = pxm.loc[dt, c]
            if pd.isna(p):
                continue
            # PIT: dt 시점 공시된 최신 equity (rcept <= dt)
            sub = dart[(dart["code"] == c) & (dart["rcept"] <= dt)]
            if sub.empty:
                continue
            eq = sub.iloc[-1]["equity"]
            tot_mcap += p * shares[c]
            tot_eq += eq
        pbr.loc[dt] = tot_mcap / tot_eq if tot_eq > 0 else np.nan
    return pbr.dropna()


def main():
    results = {"meta": {
        "method": "산업 aggregate PBR(PIT) rolling-z(24M) → forward 예측 (valuation-band rotation)",
        "임무": "산업이 자기 역사 대비 비싸면(z高) forward 약세(mean-reversion) = valuation timing",
        "pit": "equity = DART rcept_dt 이후만 / 시총 = price×shares_approx(Marcap/최근종가, PIT shares 부재 근사)",
        "horizons_months": HORIZONS_M, "oos_split": OOS_SPLIT,
        "caveat": "★shares_approx = 현 발행주식수 근사(자사주/증자 미반영) = PBR level 절대값보다 z-score(상대) 신뢰. collector_plan: PIT shares."},
        "industries": {}}
    fdr = {}
    for s in INDUSTRIES:
        pbr = industry_pbr(s)
        if pbr is None or len(pbr) < 36:
            results["industries"][s] = {"status": "INSUFFICIENT(pbr n<36 or 산출불가)"}
            continue
        # rolling z (24M, min 18)
        z = (pbr - pbr.rolling(24, min_periods=18).mean()) / pbr.rolling(24, min_periods=18).std()
        # 산업 패널 forward (eq-weight)
        px = pd.read_parquet(IND_ROOT / s / "raw-v3" / "data" / "prices.parquet"); px.index = pd.to_datetime(px.index)
        pret = mr.panel_monthly_return(px).loc["2019-01-01":]
        cum = (1 + pret.fillna(0)).cumprod()
        sec = {"pbr_n": len(pbr), "pbr_mean": round(float(pbr.mean()), 2),
               "pbr_z_last": round(float(z.dropna().iloc[-1]), 2) if z.dropna().size else None, "signals": {}}
        for hl, hm in HORIZONS_M.items():
            fwd = cum.pct_change(hm).shift(-hm)
            st = mr.signal_forward_stat(z, fwd, hm, f"{s}__pbr_z__{hl}")
            sec["signals"][hl] = st
            if st.get("status") == "powered" and st.get("wild_cluster_p") is not None:
                fdr[f"{s}__pbr_z__{hl}"] = st["wild_cluster_p"]
        results["industries"][s] = sec

    results["fdr_family_valband"] = mr.benjamini_yekutieli(fdr)
    fp = ROOT / "validation-rotation-valband-v1.json"
    fp.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {fp}\n")
    print(f"{'산업':14s} pbr_n  pbr_z_last  | y_20d rho(OOS)         | y_60d rho(OOS)")
    print("-" * 92)
    for s, sd in results["industries"].items():
        if "signals" not in sd:
            print(f"{s:14s} {sd.get('status')}")
            continue
        def fmt(hl):
            st = sd["signals"][hl]; oos = st.get("walk_forward_oos", {})
            el = oos.get("eligible"); m = "Y" if el else ("?" if el is None else "X")
            return f"[{m}]rho={st.get('spearman_rho'):+.3f} OOS{oos.get('rho_is')}->{oos.get('rho_oos')} {st.get('status','')[:4]}"
        print(f"{s:14s} {sd['pbr_n']:4d}  {str(sd['pbr_z_last']):9s} | {fmt('y_20d'):34s} | {fmt('y_60d')}")
    print(f"\nFDR valband: {json.dumps(results['fdr_family_valband'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
