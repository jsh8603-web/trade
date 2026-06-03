# -*- coding: utf-8 -*-
"""measure_valuation.py — us_mega_tech valuation 횡단면 IC (§M.7, EDGAR PIT). us_defensive 미러.

★compounder = expensive_trap: 고PER 정상(growth-duration). PER value premium 가설 ★반대 —
  저PER→고forward(value)가 아니라, mega-tech은 성장 프리미엄(고PER 종목이 성장 지속 가능).
  → PER IC 부호 해석 주의. ★capex(H6 AI capex)/fwd EPS 가 본질(value 아님).

★frame §M.12 정정 반영:
  - 24M_value horizon = eff_indep_N=n/24≈degenerate → primary 강등, 3/6/12M 우선. 24M = "방향만" 라벨.
  - block bootstrap block = horizon 비례(≥horizon_months, degenerate 부차개선).
  - small-n(n=11 basket) magnitude haircut/breadth-IR 병기 의무.

EDGAR companyconcept(equity/net_income/shares + capex) filed PIT → PBR/PER/capex_intensity cross-sectional z.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "D:/projects/Inv")
from core.assume.weight_falsification import score_ic_breakdown_eprocess

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    ed = pd.read_parquet(DATA / "edgar_fundamentals.parquet")
    return px, ed


def build_pit_valuation(px, ed):
    pxm = px.resample("ME").last(); monthly_idx = pxm.index
    ed = ed.copy(); ed["filed_dt"] = pd.to_datetime(ed["filed"], errors="coerce")
    ed = ed.dropna(subset=["filed_dt", "val"])
    pbr_p, per_p, capex_p = {}, {}, {}
    for t in px.columns:
        sub = ed[ed["ticker"] == t]
        eq = sub[sub["concept"] == "equity"].sort_values("filed_dt")
        ni = sub[sub["concept"] == "net_income"].sort_values("filed_dt")
        sh = sub[sub["concept"] == "shares"].sort_values("filed_dt")
        cx = sub[sub["concept"] == "capex"].sort_values("filed_dt")
        if len(eq) == 0 or len(sh) == 0:
            continue
        pbr_s = pd.Series(index=monthly_idx, dtype=float)
        per_s = pd.Series(index=monthly_idx, dtype=float)
        capex_s = pd.Series(index=monthly_idx, dtype=float)  # capex/equity intensity (H6)
        for dt in monthly_idx:
            eq_av = eq[eq["filed_dt"] <= dt]; sh_av = sh[sh["filed_dt"] <= dt]
            if len(eq_av) == 0 or len(sh_av) == 0:
                continue
            price = pxm.loc[dt, t] if (dt in pxm.index and t in pxm.columns) else np.nan
            if np.isnan(price):
                continue
            shares = sh_av["val"].iloc[-1]
            if not shares or shares <= 0:
                continue
            mktcap = price * shares
            equity = eq_av["val"].iloc[-1]
            if equity and equity > 0:
                pbr_s[dt] = mktcap / equity
            ni_av = ni[ni["filed_dt"] <= dt]; ttm = ttm_sum(ni_av)
            if ttm and ttm > 0:
                per_s[dt] = mktcap / ttm
            cx_av = cx[cx["filed_dt"] <= dt]; cxttm = ttm_sum(cx_av)
            if cxttm and equity and equity > 0:
                capex_s[dt] = cxttm / equity  # ★capex intensity (H6 AI capex)
        pbr_p[t] = pbr_s; per_p[t] = per_s; capex_p[t] = capex_s
    return pd.DataFrame(pbr_p), pd.DataFrame(per_p), pd.DataFrame(capex_p)


def ttm_sum(df):
    if len(df) == 0:
        return None
    fy = df[df["fp"] == "FY"]
    if len(fy):
        return fy["val"].iloc[-1]
    q = df[df["fp"].isin(["Q1", "Q2", "Q3", "Q4"])].drop_duplicates("end").tail(4)
    if len(q) >= 4:
        return q["val"].sum()
    return None


def cs_z(panel):
    mu = panel.mean(axis=1); sd = panel.std(axis=1, ddof=1)
    return panel.sub(mu, axis=0).div(sd.replace(0, np.nan), axis=0)


def cs_ic(sig, fwd, min_n=6):
    idx = sig.index.intersection(fwd.index); ics, ns, dates = [], [], []
    for dt in idx:
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = sv.index.intersection(rv.index)
        if len(c) < min_n:
            continue
        rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
        if not np.isnan(rho):
            ics.append(rho); ns.append(len(c)); dates.append(dt)
    return pd.Series(ics, index=dates), pd.Series(ns, index=dates)


def nw_se(ic, lags):
    x = ic.values.astype(float); n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean(); g0 = (e @ e) / n; var = g0
    for k in range(1, min(lags, n - 1) + 1):
        w = 1 - k / (lags + 1); var += 2 * w * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


def block_boot(x, block, B=2000, seed=42):
    """★block = horizon 비례(§M.12, ≥horizon_months)."""
    block = max(int(block), 1)
    rng = np.random.default_rng(seed); n = len(x); nb = int(np.ceil(n / block)); m = []
    for _ in range(B):
        if n - block + 1 <= 0:
            return (np.nan, np.nan)
        st = rng.integers(0, n - block + 1, size=nb)
        m.append(np.concatenate([x[s:s+block] for s in st])[:n].mean())
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def cpcv(sig, fwd, h, n_splits=6, n_test=2):
    ic, _ = cs_ic(sig, fwd)
    if len(ic) < n_splits * 2:
        return dict(oos_hit=np.nan, n_folds=0)
    months = ic.index.tolist(); fs = len(months) // n_splits
    folds = [months[i*fs:(i+1)*fs] for i in range(n_splits)]
    from itertools import combinations
    oos = []
    for combo in combinations(range(n_splits), n_test):
        tm = set()
        for fi in combo: tm.update(folds[fi])
        sub = ic[ic.index.isin(tm)]
        if len(sub) >= 2: oos.append(sub.mean())
    oos = np.array(oos); fsign = np.sign(ic.mean())
    return dict(oos_hit=float((np.sign(oos) == fsign).mean()), n_folds=len(oos))


def within_period(ic):
    if len(ic) < 12:
        return None
    by = ic.groupby(ic.index.year).mean(); fs = np.sign(ic.mean())
    return float((np.sign(by) == fs).mean())


def measure_sig(sig, fwd, h, name):
    ic, ns = cs_ic(sig, fwd)
    if len(ic) < 6:
        return None
    n = len(ic); mean = float(ic.mean())
    se = nw_se(ic, h); t = mean / se if se and se > 0 else np.nan
    p = float(2 * (1 - stats.t.cdf(abs(t), df=max(n-1, 1)))) if not np.isnan(t) else np.nan
    ci = block_boot(ic.values, block=h, B=2000)  # ★block=horizon
    eff_n = round(n / max(h, 1), 1)   # ★eff_indep_N = n_months / horizon (§M.12 degenerate 지표)
    breadth = round(float(ns.mean()), 1)
    ir_breadth = round(mean * np.sqrt(breadth * eff_n), 3) if not np.isnan(mean) else None  # breadth-IR
    return dict(signal=name, h_months=h, ic_mean=round(mean, 4), n_months=n,
                eff_indep_n=eff_n,   # ★§M.12: <5 = degenerate (24M는 ~2)
                se_nw=round(se, 4) if not np.isnan(se) else None,
                t_nw=round(t, 2) if not np.isnan(t) else None,
                p_value_nw=round(p, 4) if not np.isnan(p) else None,
                ci95_nw=[round(mean-1.96*se, 4), round(mean+1.96*se, 4)] if se and not np.isnan(se) else None,
                ci95_block_boot=[round(ci[0], 4), round(ci[1], 4)] if not np.isnan(ci[0]) else None,
                breadth_ir=ir_breadth,
                cpcv=cpcv(sig, fwd, h), within_period=within_period(ic), avg_universe_n=breadth)


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0}
    items.sort(key=lambda x: x[1]); cm = sum(1.0 / i for i in range(1, m + 1)); surv = []
    for r, (k, p) in enumerate(items, 1):
        if p <= (r / m) * q / cm: surv = [items[j][0] for j in range(r)]
    return dict(m=m, by_factor=round(cm, 3), survivors_BY=surv,
                raw_p_min=round(items[0][1], 5), raw_p_min_key=items[0][0])


def main():
    px, ed = load()
    pxm = px.resample("ME").last()
    print(f"universe {px.shape[1]}, edgar {len(ed)} rows", flush=True)

    pbr, per, capex = build_pit_valuation(px, ed)
    print(f"PBR cov {pbr.notna().sum().sum()} / PER cov {per.notna().sum().sum()} / capex cov {capex.notna().sum().sum()} cells", flush=True)

    signals = {"pbr_z": cs_z(pbr), "per_z": cs_z(per), "capex_z": cs_z(capex)}  # ★capex H6
    # ★§M.12: 3/6/12M primary, 24M = degenerate(방향만 라벨)
    horizons = {"3M": 3, "6M": 6, "12M": 12, "24M_value_DEGEN": 24}

    results, pvals = {}, {}
    for sname, sig in signals.items():
        for hname, h in horizons.items():
            fwd = pxm.shift(-h) / pxm - 1
            r = measure_sig(sig, fwd, h, f"{sname}__{hname}")
            if r:
                key = f"{sname}__{hname}"; results[key] = r
                if "DEGEN" not in hname:   # ★24M는 BY 풀에서 제외(degenerate)
                    pvals[key] = r["p_value_nw"]

    out = {"meta": {"universe_n": int(px.shape[1]),
                    "pbr_coverage_cells": int(pbr.notna().sum().sum()),
                    "per_coverage_cells": int(per.notna().sum().sum()),
                    "capex_coverage_cells": int(capex.notna().sum().sum()),
                    "pit_note": "EDGAR filed date 이후만(lookahead 회피, 한국 DART rcept_dt 대응).",
                    "archetype_note": "★compounder=expensive_trap: 고PER 정상(growth-duration). PER value premium 반대 — 성장주는 고PER 종목이 성장 지속. capex(H6 AI)/fwd EPS 본질.",
                    "m12_note": "★frame §M.12: 24M_value = eff_indep_N≈2 degenerate(primary 강등, 방향만). block=horizon 비례. n=11 basket small-n magnitude haircut/breadth-IR 병기.",
                    "sign_note": "z-score signal. ★compounder PER: 저PER→고forward(value) 면 IC<0, but 성장주는 고PER→고forward(IC>0=expensive 정상) 가능."},
            "indicators": results,
            "multiple_testing": benjamini_yekutieli(pvals)}
    (ROOT / "validation-valuation-v3.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print("\n" + "=" * 84)
    print(f"{'signal__h':<24}{'IC':>9}{'t_NW':>7}{'eff_N':>7}{'p_NW':>8}{'breadthIR':>10}{'cpcv':>7}{'avgN':>6}")
    for k, v in sorted(results.items(), key=lambda x: -abs(x[1]["ic_mean"] or 0)):
        deg = " ★DEGEN" if "DEGEN" in k else ""
        print(f"{k:<24}{(v['ic_mean'] or 0):>+9.4f}{(v['t_nw'] or 0):>7.2f}{v['eff_indep_n']:>7.1f}"
              f"{(v['p_value_nw'] or 0):>8.3f}{(v['breadth_ir'] or 0):>10.3f}{(v['cpcv'].get('oos_hit') or 0):>7.2f}{v['avg_universe_n']:>6.1f}{deg}")
    mt = out["multiple_testing"]
    print(f"\nBY(24M제외): m={mt['m']} raw_p_min={mt.get('raw_p_min')} ({mt.get('raw_p_min_key')}) survivors={mt.get('survivors_BY')}")


if __name__ == "__main__":
    main()
