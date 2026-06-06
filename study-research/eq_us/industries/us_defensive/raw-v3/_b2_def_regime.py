# -*- coding: utf-8 -*-
"""_b2_def_regime.py — ★국면 조건부 재검 (team-lead, 2026-06-04, 사용자 "국면 섞어 본 것 아니냐").

DEF-2/DEF-1 교호 검정은 전 국면 pooled(unconditional). 특정 국면서만 유의한데 희석됐는지 확인.
★방법 2종:
 1. 연속 regime interaction (size-valid): 월별 double-sort DiD_t ~ const + regime_t 1-slope, HAC + fixed-b + wild.
    = full panel 보존(split 아님) → small-block artifact 회피. "국면 강도에 따라 교호가 변하나".
 2. ★split 진단 (★비-size-valid 플래그): regime 상위40% vs 하위40% 월 DiD 평균 + Welch t.
    = 우리가 이미 죽인 small-block 함정 그대로라 ★참고용. 유의 나와도 forking-paths.
regime = 형성월 macro level (vix/baa_aaa/real_rate/dollar). DiD = 직교화·rank 안 쓰는 double-sort.
재현: python _b2_def_regime.py → _b2_def_regime_results.json
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M
from _b2_stats import fixed_b_cv, wild_cluster_boot, persistence_block
from _breadth_sweep import build_breadth_panels
from _b2_def_verify import double_sort_did

ROOT = Path(__file__).resolve().parent; DATA = ROOT / "data"; H = 12


def cont_regime_slope(did, regime):
    """DiD_t ~ const + regime_t 연속 slope, HAC + fixed-b + wild-cluster (size-valid)."""
    df = pd.concat([did.rename("did"), regime.rename("reg")], axis=1).dropna()
    if len(df) < 24:
        return dict(note="insufficient", n=len(df))
    X = sm.add_constant(df[["reg"]]); blk = persistence_block(df["did"].values)
    m = sm.OLS(df["did"], X).fit(cov_type="HAC", cov_kwds={"maxlags": blk})
    t = float(m.tvalues["reg"]); fb = fixed_b_cv(len(df), blk)
    wc = wild_cluster_boot(df["did"], X, "reg", block=blk, B=9999)
    return dict(slope=round(float(m.params["reg"]), 5), t_hac=round(t, 2), n=len(df),
                fixed_b_cv=fb["cv_5pct"], fixed_b_sig=bool(abs(t) > fb["cv_5pct"]),
                wild_p=wc.get("p_wild_cluster"))


def split_diag(did, regime, q=0.4):
    """★비-size-valid 진단: regime 상위 q vs 하위 q 월 DiD 평균 + Welch t. forking-paths 플래그."""
    df = pd.concat([did.rename("did"), regime.rename("reg")], axis=1).dropna()
    if len(df) < 30:
        return dict(note="insufficient", n=len(df))
    hi = df[df["reg"] >= df["reg"].quantile(1 - q)]["did"]; lo = df[df["reg"] <= df["reg"].quantile(q)]["did"]
    tt = stats.ttest_ind(hi, lo, equal_var=False)
    return dict(hi_mean=round(float(hi.mean()), 4), hi_n=len(hi), lo_mean=round(float(lo.mean()), 4), lo_n=len(lo),
                welch_t=round(float(tt.statistic), 2), welch_p=round(float(tt.pvalue), 4),
                hi_sign=int(np.sign(hi.mean())), note="★비-size-valid(small-block forking-paths). 참고용.")


def main():
    px, ed, uni, macro = M.load(); secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last(); P = M.build_pit_panels(px, ed)
    amt = pd.read_parquet(DATA / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    B = build_breadth_panels(px, ed, amt); z = lambda p: M.cs_z(p, secmap)
    ep, div, nis, opp = z(P["ep_yield"]), z(P["dividend_yield"]), z(B["net_issuance"]), z(B["op_profitability"])
    fwd = pxm.shift(-H) / pxm - 1
    mm = macro.resample("ME").last()
    regimes = {r: mm[r] for r in ["vix", "baa_aaa", "real_rate", "dollar"] if r in mm}

    out = {"meta": {"H": H, "note": "국면 조건부 재검. 연속 slope=size-valid / split=비-size-valid 진단(forking-paths 플래그)."}}
    for name, z1, z2 in [("DEF-2", div, opp), ("DEF-1", nis, ep)]:
        did, _ = double_sort_did(z1, z2, fwd)
        cont = {r: cont_regime_slope(did, reg) for r, reg in regimes.items()}
        splt = {r: split_diag(did, reg) for r, reg in regimes.items()}
        out[name] = dict(continuous_regime_slope=cont, split_diagnostic=splt, did_n=len(did))
    (ROOT / "_b2_def_regime_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    for nm in ["DEF-2", "DEF-1"]:
        r = out[nm]
        print(f"\n{nm} (DiD n={r['did_n']}):")
        print("  [연속 regime slope = size-valid]")
        for rg, v in r["continuous_regime_slope"].items():
            if "slope" in v:
                print(f"    {rg:10} slope={v['slope']:+.5f} t={v['t_hac']:+.2f} CV={v['fixed_b_cv']} fb_sig={v['fixed_b_sig']} wildP={v['wild_p']}")
        print("  [split 상위40%vs하위40% = ★비-size-valid 진단]")
        for rg, v in r["split_diagnostic"].items():
            if "hi_mean" in v:
                print(f"    {rg:10} hi={v['hi_mean']:+.4f}(n{v['hi_n']}) lo={v['lo_mean']:+.4f}(n{v['lo_n']}) WelchT={v['welch_t']:+.2f} p={v['welch_p']}")


if __name__ == "__main__":
    main()
