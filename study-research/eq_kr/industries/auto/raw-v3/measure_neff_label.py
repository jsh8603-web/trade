# -*- coding: utf-8 -*-
"""measure_neff_label.py — capex y_60d effective-N + AR(1) 보정 라벨 (G-C remediation 2).
team-lead 지시: capex y_60d IC AR(1)=0.416(60d 중첩) → eff-N=37.6. NW-HAC t 를 effective-N 으로 보정.
검증 = 실제 IC 시계열 AR(1) + eff-N + t_naive vs t_eff."""
from __future__ import annotations
import sys, io, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import importlib.util

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mc", str(ROOT / "measure_conditional.py"))
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)
import os
sys.stdout = io.TextIOWrapper(io.FileIO(os.dup(1), "w"), encoding="utf-8", write_through=True)
DATA = ROOT / "data"


def build_capex(px, monthly_idx):
    ext = pd.read_parquet(DATA / "dart_extended.parquet").copy()
    ext["rcept_dt"] = pd.to_datetime(ext["rcept_dt"], format="%Y%m%d", errors="coerce")
    ext = ext.dropna(subset=["rcept_dt"])
    panel = {}
    for code in px.columns:
        cf = ext[ext["code"] == code].sort_values("rcept_dt").drop_duplicates("rcept_dt", keep="last")
        if len(cf) < 4:
            continue
        s = pd.Series(index=monthly_idx, dtype=float)
        for dt in monthly_idx:
            av = cf[cf["rcept_dt"] <= dt]
            if len(av) == 0:
                continue
            last = av.iloc[-1]; a, p = last.get("assets"), last.get("ppe")
            if a and a > 0 and pd.notna(p):
                s[dt] = p / a
        panel[code] = s
    return mc.csz(pd.DataFrame(panel))


def main():
    px, lab, fin, uni = mc.load()
    pxm = px.resample("ME").last()
    capex = build_capex(px, pxm.index)
    pbr = mc.build_valuation_signals(px, fin, uni)["pbr_z"]
    anchor = capex.dropna(how="all").index

    out = {"meta": {"purpose": "effective-N + AR(1) 보정 라벨 (G-C remediation 2, hedge 강화)"}, "signals": {}}
    for sname, sig in [("capex_ratio", capex), ("pbr_z", pbr)]:
        for hname, h in [("y_20d", 20), ("y_60d", 60)]:
            fwd = mc.forward_returns_daily(px, anchor, h)
            ic = mc.ic_series(sig, fwd).values.astype(float)
            n = len(ic)
            if n < 5:
                continue
            mean = ic.mean()
            # AR(1)
            ar1 = np.corrcoef(ic[:-1], ic[1:])[0, 1]
            # effective-N = n * (1-ar1)/(1+ar1)  (AR(1) 근사)
            neff_ar1 = n * (1 - ar1) / (1 + ar1) if ar1 < 1 else n
            # n_eff (full autocorr, measure_conditional 방식)
            neff_full = mc.n_eff_autocorr(ic, max_lag=12)
            # t naive (IID) vs t_eff (eff-N 보정)
            sd = ic.std(ddof=1)
            t_naive = mean / (sd / np.sqrt(n)) if sd > 0 else np.nan
            t_eff_ar1 = mean / (sd / np.sqrt(neff_ar1)) if (sd > 0 and neff_ar1 > 1) else np.nan
            t_eff_full = mean / (sd / np.sqrt(neff_full)) if (sd > 0 and neff_full > 1) else np.nan
            out["signals"][f"{sname}__{hname}"] = {
                "ic_mean": round(mean, 4), "n_months": n,
                "ar1": round(float(ar1), 3),
                "eff_n_ar1": round(float(neff_ar1), 1),
                "eff_n_full_autocorr": round(float(neff_full), 1),
                "t_naive_iid": round(float(t_naive), 2),
                "t_eff_ar1_corrected": round(float(t_eff_ar1), 2) if not np.isnan(t_eff_ar1) else None,
                "t_eff_full_corrected": round(float(t_eff_full), 2) if not np.isnan(t_eff_full) else None,
            }
            print(f"{sname}__{hname}: IC={mean:+.4f} n={n} AR1={ar1:.3f} eff_N(AR1)={neff_ar1:.1f} eff_N(full)={neff_full:.1f} "
                  f"| t_naive={t_naive:+.2f} t_eff(AR1)={t_eff_ar1:+.2f} t_eff(full)={t_eff_full:+.2f}")

    (ROOT / "validation-neff-label-v3.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("\nSaved validation-neff-label-v3.json")


if __name__ == "__main__":
    main()
