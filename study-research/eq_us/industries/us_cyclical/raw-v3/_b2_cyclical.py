# -*- coding: utf-8 -*-
"""_b2_cyclical.py — ★B″ STEP 2/4 (us_cyclical, team-lead 지시 2026-06-04).

REWORK-B2-adjustment-plan STEP 2(per-test calib) + STEP 4(breadth) + family_2 surface.
★singles only (interaction pair = HOLD, 자문 curate 예정).

내용:
 1. family_1 fixed-b 재검정 (pbr_z/ev_ebitda/per_z) — asymptotic NW t → fixed-b CV + wild-cluster.
    ★핵심: pbr/ev_ebitda CONFIRMED 가 size-valid 에서도 유지되나?
 2. family_2 interaction — regime_conditional split(size-invalid) → regime_interaction(IC_t~Δbaa_aaa continuous) fixed-b.
 3. residual_momentum — 12-1 return을 sector+market beta 회귀 잔차 (price-based, PIT-free, 첫 add).
 4. breadth sweep — net_issuance/52w_high/amihud/op_prof/roe/accruals 단일 FDR family (size-valid).
모두 sector-neutral z + 단일 FDR family(M_eff 재계산) + fixed-b size-valid.
재현: python _b2_cyclical.py [--sample] → _b2_cyclical_results.json
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
# ★measure = cyclical 로컬(script dir, sys.path[0]) 우선. _b2_stats 만 defensive 에서 → append(끝)로 shadow 회피.
sys.path.append("D:/projects/Inv/study-research/eq_us/industries/us_defensive/raw-v3")

import numpy as np
import pandas as pd
import statsmodels.api as sm

import measure as M  # ★cyclical 로컬 measure (build_pit_panels: pbr/per/sales_yield/gross_prof/asset_growth/ev_ebitda)
from _b2_stats import (effective_n, fixed_b_cv, wild_cluster_boot, persistence_block,
                       ic_size_valid_test)

ROOT = Path(__file__).resolve().parent


def cs_z_sn(panel, secmap):
    """sector-neutral z (measure.cs_z 와 동일 로직)."""
    return M.cs_z(panel, secmap)


def size_valid_ic(ic):
    """IC 시계열 size-valid 검정 + verdict (fixed-b + wild-cluster intercept)."""
    base = ic_size_valid_test(ic.values)
    if "ic_mean" not in base:
        return base
    # wild-cluster: IC_t = const + e (intercept 검정)
    df = pd.DataFrame({"y": ic.values}); X = sm.add_constant(pd.Series(np.ones(len(ic)), name="const").to_frame()*0+1)
    Xc = pd.DataFrame({"const": np.ones(len(ic))}, index=ic.index)
    wc = wild_cluster_boot(pd.Series(ic.values, index=ic.index), Xc, "const",
                           block=base["hac_lag"], B=2000)
    base["p_wild_cluster"] = wc.get("p_wild_cluster")
    base["wild_cluster_sig"] = bool(wc.get("p_wild_cluster") is not None and wc["p_wild_cluster"] < 0.05)
    base["verdict_size_valid"] = ("SURVIVE" if (base["size_valid_sig"] and base["wild_cluster_sig"])
                                  else "DIE (asymptotic artifact)" if base["asymptotic_sig"] else "weak")
    return base


# ── 1. family_1 fixed-b 재검정 ──
def family1_fixed_b(signals, pxm, horizons):
    out = {}
    for sn, sig in signals.items():
        for hn, h in horizons.items():
            fwd = pxm.shift(-h) / pxm - 1
            ic, _ = M.cs_ic(sig, fwd)
            if len(ic) < 12:
                continue
            r = size_valid_ic(ic)
            r["h_months"] = h
            out[f"{sn}__{hn}"] = r
    return out


# ── 2. family_2 interaction (IC_t ~ Δbaa_aaa continuous, fixed-b) ──
def family2_interaction(signals, pxm, macro, h=12):
    mm = macro.resample("ME").last()
    if "baa_aaa" not in mm:
        return {"note": "baa_aaa 부재"}
    reg_chg = mm["baa_aaa"].diff()    # Δbaa_aaa continuous (split 아님)
    fwd = pxm.shift(-h) / pxm - 1
    out = {}
    for sn, sig in signals.items():
        ic, _ = M.cs_ic(sig, fwd)
        if len(ic) < 12:
            continue
        df = pd.concat([ic.rename("ic"), reg_chg.rename("reg")], axis=1).dropna()
        if len(df) < 24:
            continue
        X = sm.add_constant(df[["reg"]])
        blk = persistence_block(df["ic"].values)
        m = sm.OLS(df["ic"], X).fit(cov_type="HAC", cov_kwds={"maxlags": blk})
        t_hac = float(m.tvalues["reg"])
        fb = fixed_b_cv(len(df), blk)
        wc = wild_cluster_boot(df["ic"], X, "reg", block=blk, B=2000)
        out[sn] = dict(interaction_beta=round(float(m.params["reg"]), 4), t_hac=round(t_hac, 2),
                       n=len(df), hac_lag=blk, fixed_b_cv=fb["cv_5pct"], fixed_b_b=fb["b"],
                       size_valid_fixed_b=bool(abs(t_hac) > fb["cv_5pct"]),
                       asymptotic_sig=bool(abs(t_hac) > 1.96),
                       p_wild_cluster=wc.get("p_wild_cluster"),
                       wild_cluster_sig=bool(wc.get("p_wild_cluster") is not None and wc["p_wild_cluster"] < 0.05),
                       verdict_size_valid=("SURVIVE" if (abs(t_hac) > fb["cv_5pct"] and
                                           wc.get("p_wild_cluster") is not None and wc["p_wild_cluster"] < 0.05)
                                           else "DIE (asymptotic artifact)" if abs(t_hac) > 1.96 else "weak"))
    return dict(regime_var="d_baa_aaa", h=h, results=out,
                note="★IC_t~Δbaa_aaa continuous interaction(split 아님). fixed-b CV + wild-cluster size-valid.")


# ── 3. residual momentum (12-1 return, sector+market beta 회귀 잔차) ──
def residual_momentum(px, secmap):
    """12-1 month return을 sector dummy + market beta 에 cross-sectionally 회귀 → 잔차 = residual-mom.
    price-based, PIT-free. 매 월 횡단면 회귀."""
    pxm = px.resample("ME").last()
    raw_mom = pxm.shift(1) / pxm.shift(12) - 1     # 12-1 month return
    mkt = pxm.pct_change().mean(axis=1)             # equal-weight market proxy
    # rolling 36m market beta per stock
    rets = pxm.pct_change()
    betas = pd.DataFrame(index=pxm.index, columns=pxm.columns, dtype=float)
    for t in pxm.columns:
        cov = rets[t].rolling(36).cov(mkt)
        var = mkt.rolling(36).var()
        betas[t] = cov / var
    resid_panel = pd.DataFrame(index=raw_mom.index, columns=raw_mom.columns, dtype=float)
    secs = sorted(set(secmap.get(t, "_") for t in pxm.columns))
    for dt in raw_mom.index:
        y = raw_mom.loc[dt].dropna()
        if len(y) < 12:
            continue
        b = betas.loc[dt].reindex(y.index)
        rows = []
        for t in y.index:
            row = {"beta": b.get(t, np.nan)}
            for s in secs[1:]:    # sector dummy (drop first)
                row[f"sec_{s}"] = 1.0 if secmap.get(t) == s else 0.0
            rows.append(row)
        Xdf = pd.DataFrame(rows, index=y.index).dropna()
        yy = y.reindex(Xdf.index)
        if len(yy) < 10:
            continue
        try:
            Xc = sm.add_constant(Xdf)
            fit = sm.OLS(yy.values, Xc.values).fit()
            resid_panel.loc[dt, Xdf.index] = fit.resid
        except Exception:
            continue
    return resid_panel


# ── 4. breadth sweep candidates ──
def build_breadth_panels(px, ed, P, secmap):
    """breadth 후보 패널: net_issuance / 52w_high / amihud / op_prof / roe / accruals.
    ★전부 sector-neutral z, EDGAR PIT(filed) 또는 price-based."""
    pxm = px.resample("ME").last()
    ed = M._ed_prep(ed)
    cand = {}
    # 52w high proximity (price-based, PIT-free) = price / rolling 12m max
    roll_max = pxm.rolling(12).max()
    cand["p52w_high"] = pxm / roll_max     # 1에 가까울수록 신고가 (momentum proxy, 양 예상)
    # Amihud illiquidity (|ret|/dollar-vol proxy; dollar-vol 부재 → |ret| only rough) = price-based
    rets_d = px.pct_change()
    amihud = (rets_d.abs().resample("ME").mean())   # rough illiquidity proxy (no volume)
    cand["amihud"] = amihud
    # EDGAR 기반: net_issuance (shares YoY), op_prof (OpIncome/Assets), roe (NI/equity), accruals
    by_t = {t: ed[ed["ticker"] == t] for t in px.columns}
    midx = pxm.index
    ni_pan = {k: {} for k in ["net_issuance", "op_prof", "roe", "accruals"]}
    for t in px.columns:
        sub = by_t[t]; g = lambda c: sub[sub["concept"] == c].sort_values("filed_dt")
        sh, opi, ni, eq, assets = g("shares"), g("op_income"), g("net_income"), g("equity"), g("assets")
        s = {k: pd.Series(index=midx, dtype=float) for k in ni_pan}
        prev_assets = {}
        for dt in midx:
            # net_issuance = shares YoY (양 = 발행 = 음 예상 수익)
            sh_now = M._latest_pit(sh, dt)
            sh_yr = sh[(sh["filed_dt"] <= dt)]
            if len(sh_yr) >= 2 and not np.isnan(sh_now):
                sh_yr2 = sh_yr.copy(); sh_yr2["end_dt"] = pd.to_datetime(sh_yr2["end"], errors="coerce")
                sh_yr2 = sh_yr2.dropna(subset=["end_dt"]).sort_values("end_dt")
                cur = sh_yr2.iloc[-1]
                prev = sh_yr2[(sh_yr2["end_dt"] <= cur["end_dt"] - pd.Timedelta(days=265)) &
                              (sh_yr2["end_dt"] >= cur["end_dt"] - pd.Timedelta(days=465))]
                if len(prev) and prev.iloc[-1]["val"] > 0:
                    s["net_issuance"][dt] = cur["val"] / prev.iloc[-1]["val"] - 1
            a = M._latest_pit(assets, dt)
            opv = M._ttm(opi, dt)
            if not np.isnan(opv) and a and a > 0:
                s["op_prof"][dt] = opv / a
            niv = M._ttm(ni, dt); eqv = M._latest_pit(eq, dt)
            if not np.isnan(niv) and eqv and eqv > 0:
                s["roe"][dt] = niv / eqv
            # accruals = ΔAssets-based rough (ΔNOA proxy = ΔAssets/avgAssets, 음 예상)
            if a and a > 0:
                if t in prev_assets and prev_assets[t][1] > 0:
                    pa_dt, pa_v = prev_assets[t]
                    if (dt - pa_dt).days >= 300:
                        s["accruals"][dt] = (a - pa_v) / ((a + pa_v) / 2)
                        prev_assets[t] = (dt, a)
                else:
                    prev_assets[t] = (dt, a)
        for k in ni_pan:
            ni_pan[k][t] = s[k]
    for k in ni_pan:
        cand[k] = pd.DataFrame(ni_pan[k])
    return cand


def main(sample=False):
    px, ed, uni, macro = M.load()
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last()
    P = M.build_pit_panels(px, ed)

    # sector-neutral z (CONFIRMED 신호)
    per_z = cs_z_sn(P["per"], secmap); pbr_z = cs_z_sn(P["pbr"], secmap)
    ev_ebitda_z = cs_z_sn(P["ev_ebitda"], secmap)
    sales_yield_z = cs_z_sn(P["sales_yield"], secmap)
    mom_6 = cs_z_sn(pxm / pxm.shift(6) - 1, secmap)
    vol_60 = cs_z_sn((px.pct_change().rolling(60).std() * np.sqrt(252)).resample("ME").last(), secmap)

    horizons = {"3M": 3, "6M": 6, "12M": 12, "24M_value": 24}

    # 1. family_1 fixed-b
    fam1 = family1_fixed_b({"pbr_z": pbr_z, "ev_ebitda": ev_ebitda_z, "per_z": per_z}, pxm, horizons)

    # 2. family_2 interaction (Δbaa_aaa)
    fam2_int = family2_interaction(
        {"pbr_z": pbr_z, "ev_ebitda": ev_ebitda_z, "per_z": per_z, "sales_yield": sales_yield_z,
         "vol_60": vol_60, "mom_6": mom_6}, pxm, macro, h=12)

    # 3. residual momentum
    resid_mom_panel = residual_momentum(px, secmap)
    resid_mom_z = cs_z_sn(resid_mom_panel, secmap)
    rm = {}
    for hn, h in horizons.items():
        fwd = pxm.shift(-h) / pxm - 1
        ic, _ = M.cs_ic(resid_mom_z, fwd)
        if len(ic) >= 12:
            rm[hn] = size_valid_ic(ic)

    # 4. breadth sweep
    cand = build_breadth_panels(px, ed, P, secmap)
    breadth = {}
    for name, panel in cand.items():
        z = cs_z_sn(panel, secmap)
        for hn, h in horizons.items():
            fwd = pxm.shift(-h) / pxm - 1
            ic, _ = M.cs_ic(z, fwd)
            if len(ic) >= 12:
                breadth[f"{name}__{hn}"] = size_valid_ic(ic)

    # ── 단일 FDR family (family_1 CONFIRMED + residual-mom + breadth, M_eff 재계산) ──
    # p-value 모음 (size-valid 우선: wild-cluster p 있으면 그것, 없으면 asymptotic 변환)
    all_tests = {}
    for k, v in fam1.items():
        if v.get("p_wild_cluster") is not None:
            all_tests[f"fam1_{k}"] = v["p_wild_cluster"]
    for k, v in rm.items():
        if v.get("p_wild_cluster") is not None:
            all_tests[f"rmom_{k}"] = v["p_wild_cluster"]
    for k, v in breadth.items():
        if v.get("p_wild_cluster") is not None:
            all_tests[f"brd_{k}"] = v["p_wild_cluster"]
    by_single = M.benjamini_yekutieli(all_tests)

    results = {
        "meta": {"note": "★B″ STEP 2/4 us_cyclical. fixed-b CV(KV) + wild-cluster size-valid. singles only(interaction HOLD).",
                 "z_method": "sector-neutral", "sample": sample},
        "family_1_fixed_b": fam1,
        "family_2_interaction": fam2_int,
        "residual_momentum": rm,
        "breadth_sweep": breadth,
        "single_fdr_family": {"tests": all_tests, "by": by_single,
                              "note": "size-valid wild-cluster p 기반 단일 FDR family(fam1 confirmed + residual-mom + breadth)."},
    }
    (ROOT / "_b2_cyclical_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    # print 요약
    print("=" * 80)
    print("1. family_1 fixed-b retention (pbr/ev_ebitda CONFIRMED size-valid?):")
    for k, v in fam1.items():
        if "verdict_size_valid" in v:
            print(f"   {k:22} t={v['t_nw']:+.2f} fixedCV={v['fixed_b']['cv_5pct']} n_eff={v['effective_n']['n_eff']} "
                  f"wildP={v.get('p_wild_cluster')} → {v['verdict_size_valid']}")
    print("\n2. family_2 interaction (IC~Δbaa_aaa, fixed-b):")
    for k, v in fam2_int.get("results", {}).items():
        print(f"   {k:14} β={v['interaction_beta']:+.4f} t={v['t_hac']:+.2f} CV={v['fixed_b_cv']} wildP={v['p_wild_cluster']} → {v['verdict_size_valid']}")
    print("\n3. residual-mom:")
    for k, v in rm.items():
        if "verdict_size_valid" in v:
            print(f"   {k:8} IC={v['ic_mean']:+.4f} t={v['t_nw']:+.2f} CV={v['fixed_b']['cv_5pct']} wildP={v.get('p_wild_cluster')} → {v['verdict_size_valid']}")
    print("\n4. breadth sweep:")
    for k, v in sorted(breadth.items(), key=lambda x: x[1].get('p_wild_cluster') or 1):
        if "verdict_size_valid" in v:
            print(f"   {k:22} IC={v['ic_mean']:+.4f} t={v['t_nw']:+.2f} CV={v['fixed_b']['cv_5pct']} wildP={v.get('p_wild_cluster')} → {v['verdict_size_valid']}")
    print(f"\n★ 단일 FDR family: m={by_single.get('m_raw')} M_eff={by_single.get('m_eff')} survivors={by_single.get('survivors_BY')}")
    print(f"   raw_p_min={by_single.get('raw_p_min')} ({by_single.get('raw_p_min_key')})")


if __name__ == "__main__":
    main(sample="--sample" in sys.argv)
