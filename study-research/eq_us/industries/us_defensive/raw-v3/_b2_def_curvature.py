# -*- coding: utf-8 -*-
"""_b2_def_curvature.py — ★자문 수렴 결정적 검정: own-curvature confound (team-lead, 2026-06-04).

Claude+Gemini R1 양채널 수렴 = z1·z2 교호항이 선형 직교화 후에도 z1²·z2² 와 상관 →
선형 main 에만 직교화하면 단일인자 곡률을 교호로 흡수(false interaction).
★결정적 검정 = 직교화 basis 에 z1²·z2² 추가 후 incr IC 생존?
+ FM 전체회귀(fwd~z1+z2+z1·z2 [+z1²+z2²]) 교호계수(해석·magnitude, 양채널 권고).
대상 = 생존자 DEF-2(div×op_prof), DEF-1(net_iss×ep) + 월별 VIF(공선성, Gemini).
재현: python _b2_def_curvature.py → _b2_def_curvature_results.json
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M
from _b2_stats import effective_n, fixed_b_cv, wild_cluster_boot, persistence_block
from _breadth_sweep import build_breadth_panels

ROOT = Path(__file__).resolve().parent; DATA = ROOT / "data"; H = 12
SPLIT = pd.Timestamp("2022-01-01")


def stat_block(ic):
    ic = pd.Series(ic).dropna(); n = len(ic)
    if n < 12:
        return dict(n=n, note="insufficient")
    blk = persistence_block(ic.values); eff = effective_n(ic.values); mean = float(ic.mean())
    x = ic.values; e = x - x.mean(); g0 = (e @ e) / n; var = g0
    for k in range(1, min(blk, n - 1) + 1):
        var += 2 * (1 - k / (blk + 1)) * (e[k:] @ e[:-k]) / n
    se = float(np.sqrt(max(var, 1e-12) / n)); t = mean / se if se > 0 else np.nan
    fb = fixed_b_cv(n, blk)
    wc = wild_cluster_boot(pd.Series(x, index=ic.index), pd.DataFrame({"const": np.ones(n)}, index=ic.index),
                           "const", block=blk, B=9999)
    return dict(ic_mean=round(mean, 4), n=n, n_eff=eff["n_eff"], block_G=int(np.ceil(n/blk)),
                t_nw=round(float(t), 2) if not np.isnan(t) else None, fixed_b_cv=fb["cv_5pct"],
                fixed_b_sig=bool(not np.isnan(t) and abs(t) > fb["cv_5pct"]),
                wild_p=wc.get("p_wild_cluster"), sign=int(np.sign(mean)))


def incremental_ic(inter, basis_panels, fwd, secmap, min_n=10):
    """inter 를 basis(선형 또는 +곡률)에 횡단면 직교화 후 잔차 IC."""
    from scipy import stats
    idx = inter.index.intersection(fwd.index); ics, dates = [], []
    for dt in idx:
        iv = inter.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        cols = [b.loc[dt] for b in basis_panels]
        common = iv.index
        for c in cols:
            common = common.intersection(c.dropna().index)
        common = common.intersection(rv.index)
        if len(common) < min_n:
            continue
        y = iv.loc[common].values
        X = np.column_stack([c.loc[common].values for c in cols] + [np.ones(len(common))])
        try:
            b, *_ = np.linalg.lstsq(X, y, rcond=None); resid = y - X @ b
        except Exception:
            continue
        rho, _ = stats.spearmanr(resid, rv.loc[common].values)
        if not np.isnan(rho):
            ics.append(rho); dates.append(dt)
    return pd.Series(ics, index=dates)


def fm_interaction_coef(z1, z2, fwd, inter, add_sq=False, min_n=12):
    """FM 전체회귀 fwd~const+z1+z2+z1z2[+z1²+z2²] 교호계수 시계열 + 평균 VIF."""
    idx = z1.index.intersection(fwd.index); betas, vifs, dates = [], [], []
    for dt in idx:
        d = pd.DataFrame({"z1": z1.loc[dt], "z2": z2.loc[dt], "inter": inter.loc[dt], "y": fwd.loc[dt]})
        if add_sq:
            d["z1sq"] = z1.loc[dt]**2; d["z2sq"] = z2.loc[dt]**2
        d = d.dropna()
        if len(d) < min_n:
            continue
        cols = ["z1", "z2", "inter"] + (["z1sq", "z2sq"] if add_sq else [])
        X = sm.add_constant(d[cols])
        try:
            fit = sm.OLS(d["y"], X).fit(); betas.append(float(fit.params["inter"])); dates.append(dt)
            # VIF(inter) = 1/(1-R²) of inter ~ 나머지 회귀자
            others = [c for c in cols if c != "inter"]
            r2 = sm.OLS(d["inter"], sm.add_constant(d[others])).fit().rsquared
            vifs.append(1.0/max(1e-6, 1-r2))
        except Exception:
            continue
    bs = pd.Series(betas, index=dates)
    return bs, (float(np.nanmean(vifs)) if vifs else None)


def main():
    px, ed, uni, macro = M.load(); secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last(); P = M.build_pit_panels(px, ed)
    amt = pd.read_parquet(DATA / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    B = build_breadth_panels(px, ed, amt); z = lambda p: M.cs_z(p, secmap)
    ep, div, nis, opp = z(P["ep_yield"]), z(P["dividend_yield"]), z(B["net_issuance"]), z(B["op_profitability"])
    fwd = pxm.shift(-H) / pxm - 1
    out = {"meta": {"H": H, "note": "own-curvature confound 결정검정. linear-basis vs +z²-basis incr IC + FM coef + VIF."}}

    for name, z1, z2 in [("DEF-2", div, opp), ("DEF-1", nis, ep)]:
        inter = z(z1 * z2)
        ic_lin = incremental_ic(inter, [z1, z2], fwd, secmap)                    # 선형 basis (기존)
        ic_cur = incremental_ic(inter, [z1, z2, z(z1*z1), z(z2*z2)], fwd, secmap)  # +곡률 basis
        fmb_lin, vif_lin = fm_interaction_coef(z1, z2, fwd, inter, add_sq=False)
        fmb_cur, vif_cur = fm_interaction_coef(z1, z2, fwd, inter, add_sq=True)
        out[name] = dict(
            incr_linear=stat_block(ic_lin), incr_curvature=stat_block(ic_cur),
            fm_coef_linear=stat_block(fmb_lin), fm_coef_curvature=stat_block(fmb_cur),
            mean_vif_inter_linear=round(vif_lin, 2) if vif_lin else None,
            mean_vif_inter_curvature=round(vif_cur, 2) if vif_cur else None)
    (ROOT / "_b2_def_curvature_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    for nm in ["DEF-2", "DEF-1"]:
        r = out[nm]; il, ic = r["incr_linear"], r["incr_curvature"]; fl, fc = r["fm_coef_linear"], r["fm_coef_curvature"]
        try:
            print(f"\n{nm}:")
            print(f"  incr IC  linear : {il.get('ic_mean')} t={il.get('t_nw')} fb_sig={il.get('fixed_b_sig')} wildP={il.get('wild_p')} G={il.get('block_G')}")
            print(f"  incr IC +곡률    : {ic.get('ic_mean')} t={ic.get('t_nw')} fb_sig={ic.get('fixed_b_sig')} wildP={ic.get('wild_p')}  ← 생존?")
            print(f"  FM coef  linear : {fl.get('ic_mean')} t={fl.get('t_nw')} fb_sig={fl.get('fixed_b_sig')} wildP={fl.get('wild_p')}")
            print(f"  FM coef +곡률    : {fc.get('ic_mean')} t={fc.get('t_nw')} fb_sig={fc.get('fixed_b_sig')} wildP={fc.get('wild_p')}")
            print(f"  mean VIF(inter) linear={r['mean_vif_inter_linear']} / +곡률={r['mean_vif_inter_curvature']}")
        except Exception as e:
            print(nm, "skip", e)


if __name__ == "__main__":
    main()
