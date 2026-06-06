# -*- coding: utf-8 -*-
"""_b2_defensive_interactions.py — ★DEF-1~5 interaction 가설 검증 (team-lead 직접, 2026-06-04).

pre-reg: REWORK-prereg-11hypotheses-20260604.md (DEF-1~5).
방법: cyclical _b2_cyclical_interactions 와 동형 — interaction_z(z1·z2) sector-neutral →
  raw IC + FWL incremental IC(⊥{main들}) → fixed-b CV + wild-cluster(B=9999) + n_eff(floor30).
  DEF-4 = Tier2 연속 slope (ep_yield IC_t ~ Δreal_rate). predicted_sign one-sided pre-commit.
raw stat 만. FDR 통합은 team-lead 11개 합쳐서.

빌더 재사용: measure.build_pit_panels(ep_yield/dividend_yield/earnings_cv/gross_prof) +
  _breadth_sweep.build_breadth_panels(net_issuance/op_profitability) + vol_60 inline + macro.real_rate.
재현: python _b2_defensive_interactions.py → _b2_defensive_interactions_results.json
"""
from __future__ import annotations
import sys, json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M
import _b2_stats as B2
from _breadth_sweep import build_breadth_panels

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
NEFF_FLOOR = 30
WILD_B = 9999
H = 12


def interaction_z(z1, z2, secmap):
    return M.cs_z(z1 * z2, secmap)


def fwl_incremental_ic(inter_sig, main_sigs, fwd, min_n=10):
    idx = inter_sig.index.intersection(fwd.index); ics, dates = [], []
    for dt in idx:
        iv = inter_sig.loc[dt].dropna(); mains = [m.loc[dt] for m in main_sigs]; rv = fwd.loc[dt].dropna()
        common = iv.index
        for m in mains:
            common = common.intersection(m.dropna().index)
        common = common.intersection(rv.index)
        if len(common) < min_n:
            continue
        y = iv.loc[common].values
        X = np.column_stack([m.loc[common].values for m in mains] + [np.ones(len(common))])
        try:
            beta, *_ = np.linalg.lstsq(X, y, rcond=None); resid = y - X @ beta
        except Exception:
            continue
        rho, _ = stats.spearmanr(resid, rv.loc[common].values)
        if not np.isnan(rho):
            ics.append(rho); dates.append(dt)
    return pd.Series(ics, index=dates)


def size_valid_block(ic, label):
    ic = pd.Series(ic).dropna(); n = len(ic)
    if n < 12:
        return dict(label=label, n=n, note="insufficient")
    blk = B2.persistence_block(ic.values); eff = B2.effective_n(ic.values); mean = float(ic.mean())
    x = ic.values; e = x - x.mean(); g0 = (e @ e) / n; var = g0
    for k in range(1, min(blk, n - 1) + 1):
        var += 2 * (1 - k / (blk + 1)) * (e[k:] @ e[:-k]) / n
    se = float(np.sqrt(max(var, 1e-12) / n)); t = mean / se if se > 0 else np.nan
    fb = B2.fixed_b_cv(n, blk)
    Xc = pd.DataFrame({"const": np.ones(n)}, index=ic.index)
    wc = B2.wild_cluster_boot(pd.Series(ic.values, index=ic.index), Xc, "const", block=blk, B=WILD_B)
    return dict(label=label, ic_mean=round(mean, 4), n=n, hac_lag=blk,
                t_nw=round(float(t), 2) if not np.isnan(t) else None,
                n_eff=eff["n_eff"], underpowered=bool(eff["n_eff"] < NEFF_FLOOR),
                fixed_b_cv=fb["cv_5pct"], fixed_b_b=fb["b"],
                fixed_b_sig=bool(not np.isnan(t) and abs(t) > fb["cv_5pct"]),
                asymptotic_sig=bool(not np.isnan(t) and abs(t) > 1.96),
                p_wild_cluster=wc.get("p_wild_cluster"))


def main():
    px, ed, uni, macro = M.load()
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last(); P = M.build_pit_panels(px, ed)
    amt = pd.read_parquet(DATA / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    B = build_breadth_panels(px, ed, amt)
    z = lambda panel: M.cs_z(panel, secmap)

    ep_z = z(P["ep_yield"]); div_z = z(P["dividend_yield"]); ecv_z = z(P["earnings_cv"])
    gprof_z = z(P["gross_prof"]); nissu_z = z(B["net_issuance"]); opp_z = z(B["op_profitability"])
    vol60 = (px.pct_change().rolling(60).std() * np.sqrt(252)).resample("ME").last()
    vol_z = z(vol60)
    fwd = pxm.shift(-H) / pxm - 1
    results = {"meta": {"H_months": H, "neff_floor": NEFF_FLOOR, "wild_B": WILD_B, "z_method": "sector-neutral",
                        "data_range": f"{px.index.min().date()}~{px.index.max().date()}", "n_tickers": px.shape[1],
                        "note": "raw stat only, FDR X(team-lead). cheap-dir: ep_yield 고=cheap(+z). stable: -earnings_cv/-vol(저=stable)."}}

    # DEF-1 net_issuance × ep_yield. pred +1 (two_sided_review). ⊥{net_issuance(confirmed), ep_yield}
    i1 = interaction_z(nissu_z, ep_z, secmap)
    results["DEF-1"] = dict(spec="net_issuance x ep_yield", predicted_sign=1, two_sided_review=True,
        raw_interaction_ic=size_valid_block(M.cs_ic(i1, fwd)[0], "DEF-1_raw"),
        incremental_ic=size_valid_block(fwl_incremental_ic(i1, [nissu_z, ep_z], fwd), "DEF-1_incr"))

    # DEF-2 dividend_yield(고) × op_prof(고). pred +1. ⊥{dividend_yield, op_prof}
    i2 = interaction_z(div_z, opp_z, secmap)
    results["DEF-2"] = dict(spec="dividend_yield(고) x op_prof(고)", predicted_sign=1,
        raw_interaction_ic=size_valid_block(M.cs_ic(i2, fwd)[0], "DEF-2_raw"),
        incremental_ic=size_valid_block(fwl_incremental_ic(i2, [div_z, opp_z], fwd), "DEF-2_incr"))

    # DEF-3 earnings_cv(저=-ecv) × vol_60(저=-vol). pred +1. ⊥{earnings_cv, vol_60}
    i3 = interaction_z(-ecv_z, -vol_z, secmap)
    results["DEF-3"] = dict(spec="earnings_cv(저) x vol_60(저) stable교집합", predicted_sign=1,
        raw_interaction_ic=size_valid_block(M.cs_ic(i3, fwd)[0], "DEF-3_raw"),
        incremental_ic=size_valid_block(fwl_incremental_ic(i3, [ecv_z, vol_z], fwd), "DEF-3_incr"),
        m_eff_note="earnings_cv·vol_60 near-duplicate 가능 → corr 점검")

    # DEF-5 ep_yield × gross_prof. pred +1. ⊥{ep_yield, gross_prof}
    i5 = interaction_z(ep_z, gprof_z, secmap)
    results["DEF-5"] = dict(spec="ep_yield x gross_prof anti-value quality decomp", predicted_sign=1,
        raw_interaction_ic=size_valid_block(M.cs_ic(i5, fwd)[0], "DEF-5_raw"),
        incremental_ic=size_valid_block(fwl_incremental_ic(i5, [ep_z, gprof_z], fwd), "DEF-5_incr"))

    # DEF-4 Tier2: ep_yield IC_t ~ Δreal_rate slope. pred −1 (금리상승→ep IC 하락)
    ic_ep, _ = M.cs_ic(ep_z, fwd)
    mm = macro.resample("ME").last(); d_rr = mm["real_rate"].diff()
    df = pd.concat([ic_ep.rename("ic"), d_rr.rename("reg")], axis=1).dropna()
    if len(df) >= 24:
        X = sm.add_constant(df[["reg"]]); blk = B2.persistence_block(df["ic"].values)
        m = sm.OLS(df["ic"], X).fit(cov_type="HAC", cov_kwds={"maxlags": blk})
        t_hac = float(m.tvalues["reg"]); fb = B2.fixed_b_cv(len(df), blk)
        wc = B2.wild_cluster_boot(df["ic"], X, "reg", block=blk, B=WILD_B)
        results["DEF-4"] = dict(spec="ep_yield IC_t ~ Δreal_rate slope", predicted_sign=-1, tier=2,
            ep_main_ic=round(float(ic_ep.mean()), 4), slope_beta=round(float(m.params["reg"]), 4),
            slope_t_hac=round(t_hac, 2), n=len(df), fixed_b_cv=fb["cv_5pct"],
            slope_fixed_b_sig=bool(abs(t_hac) > fb["cv_5pct"]),
            sign_match=bool(np.sign(m.params["reg"]) == -1), slope_p_wild=wc.get("p_wild_cluster"))
    else:
        results["DEF-4"] = dict(note="insufficient real_rate overlap", n=len(df))

    (ROOT / "_b2_defensive_interactions_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    try:
        for d in ["DEF-1", "DEF-2", "DEF-3", "DEF-5"]:
            r = results[d]; raw = r["raw_interaction_ic"]; inc = r["incremental_ic"]
            so = "OK" if np.sign(raw.get("ic_mean", 0)) == r["predicted_sign"] else "X"
            print(f"{d} [{r['spec'][:38]}] pred={r['predicted_sign']:+d}")
            print(f"   raw  IC={raw.get('ic_mean')} t={raw.get('t_nw')} n_eff={raw.get('n_eff')} CV={raw.get('fixed_b_cv')} fb_sig={raw.get('fixed_b_sig')} wildP={raw.get('p_wild_cluster')} UP={raw.get('underpowered')} sign={so}")
            print(f"   incr IC={inc.get('ic_mean')} t={inc.get('t_nw')} fb_sig={inc.get('fixed_b_sig')} wildP={inc.get('p_wild_cluster')} n_eff={inc.get('n_eff')}")
        d4 = results["DEF-4"]
        print(f"DEF-4 Tier2 ep_main_ic={d4.get('ep_main_ic')} | slope b={d4.get('slope_beta')} t={d4.get('slope_t_hac')} fb_sig={d4.get('slope_fixed_b_sig')} sign={d4.get('sign_match')} wildP={d4.get('slope_p_wild')}")
    except Exception as e:
        print("print skip:", e)


if __name__ == "__main__":
    main()
