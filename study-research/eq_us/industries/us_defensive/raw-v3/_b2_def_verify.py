# -*- coding: utf-8 -*-
"""_b2_def_verify.py — ★자문 적용 타당성 독립 검증 (team-lead, 2026-06-04).

사용자 지적: 자문은 이론만 차용, 실제 코드 적용 타당성은 별도 검증 의무.
curvature/FM 검정(DEF-2 생존/DEF-1 격하)이 ★내 구현 artifact 인지, 진짜인지를
구현 무관 독립 방법으로 재확인:
 1. ★2×2 double-sort diff-in-diff (직교화·rank·회귀 안 씀 = FM/rank 구현 독립).
    DEF-2 진짜면 DiD 양·유의 / DEF-1 rank-artifact 면 DiD 비유의여야 일관.
 2. 구현 진단: 월별 횡단면 n, FM 설계행렬 조건수, 유효 월 비율, outlier 월 trim 민감도.
 3. hand-built FM 재확인(별 함수, DEF-1 FM 비유의가 내 fm_interaction_coef 버그 아닌지).
재현: python _b2_def_verify.py → _b2_def_verify_results.json
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


def size_test(series, label=""):
    s = pd.Series(series).dropna(); n = len(s)
    if n < 12:
        return dict(label=label, n=n, note="insufficient")
    blk = persistence_block(s.values); eff = effective_n(s.values); mean = float(s.mean())
    x = s.values; e = x - x.mean(); g0 = (e @ e) / n; var = g0
    for k in range(1, min(blk, n - 1) + 1):
        var += 2 * (1 - k / (blk + 1)) * (e[k:] @ e[:-k]) / n
    se = float(np.sqrt(max(var, 1e-12) / n)); t = mean / se if se > 0 else np.nan
    fb = fixed_b_cv(n, blk)
    wc = wild_cluster_boot(pd.Series(x, index=s.index), pd.DataFrame({"const": np.ones(n)}, index=s.index),
                           "const", block=blk, B=9999)
    return dict(label=label, mean=round(mean, 5), n=n, n_eff=eff["n_eff"], t_nw=round(float(t), 2) if not np.isnan(t) else None,
                fixed_b_cv=fb["cv_5pct"], fixed_b_sig=bool(not np.isnan(t) and abs(t) > fb["cv_5pct"]),
                wild_p=wc.get("p_wild_cluster"), sign=int(np.sign(mean)))


def double_sort_did(z1, z2, fwd, min_grp=3):
    """2×2 median 분할 quadrant forward 수익 → diff-in-diff = (HH−HL)−(LH−LL).
    교호 부호: 양이면 z1·z2 시너지(둘 다 高=초과). 직교화/rank/회귀 안 씀."""
    idx = z1.index.intersection(z2.index).intersection(fwd.index)
    dids, quad_means = {}, {"HH": [], "HL": [], "LH": [], "LL": []}
    rows = []
    for dt in idx:
        d = pd.DataFrame({"z1": z1.loc[dt], "z2": z2.loc[dt], "y": fwd.loc[dt]}).dropna()
        if len(d) < 4 * min_grp:
            continue
        m1, m2 = d["z1"].median(), d["z2"].median()
        hh = d[(d.z1 > m1) & (d.z2 > m2)]["y"]; hl = d[(d.z1 > m1) & (d.z2 <= m2)]["y"]
        lh = d[(d.z1 <= m1) & (d.z2 > m2)]["y"]; ll = d[(d.z1 <= m1) & (d.z2 <= m2)]["y"]
        if min(len(hh), len(hl), len(lh), len(ll)) < min_grp:
            continue
        did = (hh.mean() - hl.mean()) - (lh.mean() - ll.mean())
        rows.append((dt, did))
        for k, g in [("HH", hh), ("HL", hl), ("LH", lh), ("LL", ll)]:
            quad_means[k].append(g.mean())
    did_s = pd.Series([r[1] for r in rows], index=[r[0] for r in rows])
    qm = {k: round(float(np.nanmean(v)), 4) for k, v in quad_means.items() if v}
    return did_s, qm


def fm_handbuilt(z1, z2, fwd, min_n=12):
    """독립 hand-built FM: fwd~const+z1+z2+(z1·z2) 월별 OLS, 교호계수 + 월별 n + 조건수."""
    idx = z1.index.intersection(fwd.index); coefs, ns, conds, valid = [], [], [], 0
    for dt in idx:
        d = pd.DataFrame({"z1": z1.loc[dt], "z2": z2.loc[dt], "y": fwd.loc[dt]}).dropna()
        d["i12"] = d["z1"] * d["z2"]
        if len(d) < min_n:
            continue
        X = sm.add_constant(d[["z1", "z2", "i12"]]).values
        try:
            cond = float(np.linalg.cond(X))
            beta, *_ = np.linalg.lstsq(X, d["y"].values, rcond=None)
            coefs.append((dt, float(beta[3]))); ns.append(len(d)); conds.append(cond); valid += 1
        except Exception:
            continue
    cs = pd.Series([c[1] for c in coefs], index=[c[0] for c in coefs])
    return cs, dict(valid_months=valid, median_cs_n=int(np.median(ns)) if ns else None,
                    median_cond=round(float(np.median(conds)), 1) if conds else None,
                    max_cond=round(float(np.max(conds)), 1) if conds else None)


def main():
    px, ed, uni, macro = M.load(); secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last(); P = M.build_pit_panels(px, ed)
    amt = pd.read_parquet(DATA / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    B = build_breadth_panels(px, ed, amt); z = lambda p: M.cs_z(p, secmap)
    ep, div, nis, opp = z(P["ep_yield"]), z(P["dividend_yield"]), z(B["net_issuance"]), z(B["op_profitability"])
    fwd = pxm.shift(-H) / pxm - 1
    out = {"meta": {"H": H, "note": "자문 적용 타당성 독립검증. double-sort(구현독립) + hand-built FM + 진단."}}

    for name, z1, z2, pred in [("DEF-2", div, opp, +1), ("DEF-1", nis, ep, +1)]:
        did_s, qm = double_sort_did(z1, z2, fwd)
        did_stat = size_test(did_s, f"{name}_DiD")
        # outlier 민감도: |DiD| 상위 5% 월 trim 후 재검정
        thr = did_s.abs().quantile(0.95); did_trim = did_s[did_s.abs() <= thr]
        did_trim_stat = size_test(did_trim, f"{name}_DiD_trim5%")
        fm_cs, diag = fm_handbuilt(z1, z2, fwd)
        fm_stat = size_test(fm_cs, f"{name}_FMhandbuilt")
        out[name] = dict(pred_sign=pred, double_sort_DiD=did_stat, quadrant_fwd_means=qm,
                         DiD_trim5pct=did_trim_stat, fm_handbuilt=fm_stat, fm_diag=diag)
    (ROOT / "_b2_def_verify_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    for nm in ["DEF-2", "DEF-1"]:
        r = out[nm]; ds, fm, dg = r["double_sort_DiD"], r["fm_handbuilt"], r["fm_diag"]
        dt = r["DiD_trim5pct"]
        try:
            print(f"\n{nm} (pred=+1):")
            print(f"  quadrant fwd: {r['quadrant_fwd_means']}")
            print(f"  ★double-sort DiD: mean={ds.get('mean')} t={ds.get('t_nw')} fb_sig={ds.get('fixed_b_sig')} wildP={ds.get('wild_p')} n={ds.get('n')} sign={ds.get('sign')}")
            print(f"    trim5% 후      : mean={dt.get('mean')} t={dt.get('t_nw')} fb_sig={dt.get('fixed_b_sig')} wildP={dt.get('wild_p')}")
            print(f"  hand-built FM coef: mean={fm.get('mean')} t={fm.get('t_nw')} fb_sig={fm.get('fixed_b_sig')} wildP={fm.get('wild_p')}")
            print(f"  진단: valid월={dg.get('valid_months')} 월중앙n={dg.get('median_cs_n')} 조건수 median={dg.get('median_cond')} max={dg.get('max_cond')}")
        except Exception as e:
            print(nm, "skip", e)


if __name__ == "__main__":
    main()
