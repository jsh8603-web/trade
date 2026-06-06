# -*- coding: utf-8 -*-
"""_b2_cyc_verify_regime.py — ★CYC 교호 독립검증 + regime 조건부 (team-lead, 2026-06-04).

사용자 "11개 중 볼 가치 있는거 다 봐봐". + ★cyclical 드라이버도 교호항 재-z(cs_z(z1*z2)) 결함
동일 적용 → CYC-3/4 wrong-sign 유의가 재-z artifact 인지 raw double-sort 로 재판별.
대상: CYC-1(Novy-Marx,부호OK) / CYC-3·CYC-4(wrong-sign 유의) / CYC-5(near-null).
방법: 2×2 double-sort DiD(raw, 재-z·rank·회귀 안씀) + hand-built FM(raw곱) + 연속 regime slope(size-valid).
재현: python _b2_cyc_verify_regime.py → _b2_cyc_verify_regime_results.json
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M
sys.path.append("D:/projects/Inv/study-research/eq_us/industries/us_defensive/raw-v3")
from _b2_stats import effective_n, fixed_b_cv, wild_cluster_boot, persistence_block
from _b2_cyclical_interactions import build_signals

ROOT = Path(__file__).resolve().parent; H = 12


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
    idx = z1.index.intersection(z2.index).intersection(fwd.index); rows = []; qm = {"HH": [], "HL": [], "LH": [], "LL": []}
    for dt in idx:
        d = pd.DataFrame({"z1": z1.loc[dt], "z2": z2.loc[dt], "y": fwd.loc[dt]}).dropna()
        if len(d) < 4 * min_grp:
            continue
        m1, m2 = d["z1"].median(), d["z2"].median()
        g = {"HH": d[(d.z1 > m1) & (d.z2 > m2)]["y"], "HL": d[(d.z1 > m1) & (d.z2 <= m2)]["y"],
             "LH": d[(d.z1 <= m1) & (d.z2 > m2)]["y"], "LL": d[(d.z1 <= m1) & (d.z2 <= m2)]["y"]}
        if min(len(v) for v in g.values()) < min_grp:
            continue
        rows.append((dt, (g["HH"].mean() - g["HL"].mean()) - (g["LH"].mean() - g["LL"].mean())))
        for k in qm:
            qm[k].append(g[k].mean())
    did = pd.Series([r[1] for r in rows], index=[r[0] for r in rows])
    return did, {k: round(float(np.nanmean(v)), 4) for k, v in qm.items() if v}


def fm_handbuilt(z1, z2, fwd, min_n=10):
    idx = z1.index.intersection(fwd.index); coefs = []
    for dt in idx:
        d = pd.DataFrame({"z1": z1.loc[dt], "z2": z2.loc[dt], "y": fwd.loc[dt]}).dropna()
        d["i12"] = d["z1"] * d["z2"]
        if len(d) < min_n:
            continue
        X = sm.add_constant(d[["z1", "z2", "i12"]]).values
        try:
            b, *_ = np.linalg.lstsq(X, d["y"].values, rcond=None); coefs.append((dt, float(b[3])))
        except Exception:
            continue
    return pd.Series([c[1] for c in coefs], index=[c[0] for c in coefs])


def cont_regime_slope(did, regime):
    df = pd.concat([did.rename("did"), regime.rename("reg")], axis=1).dropna()
    if len(df) < 24:
        return dict(note="insufficient", n=len(df))
    X = sm.add_constant(df[["reg"]]); blk = persistence_block(df["did"].values)
    m = sm.OLS(df["did"], X).fit(cov_type="HAC", cov_kwds={"maxlags": blk})
    t = float(m.tvalues["reg"]); fb = fixed_b_cv(len(df), blk)
    wc = wild_cluster_boot(df["did"], X, "reg", block=blk, B=9999)
    return dict(slope=round(float(m.params["reg"]), 5), t_hac=round(t, 2), n=len(df),
                fixed_b_cv=fb["cv_5pct"], fixed_b_sig=bool(abs(t) > fb["cv_5pct"]), wild_p=wc.get("p_wild_cluster"))


def main():
    px, ed, uni, macro = M.load(); secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last(); P = M.build_pit_panels(px, ed)
    Z = build_signals(px, ed, P, secmap)
    fwd = pxm.shift(-H) / pxm - 1
    mm = macro.resample("ME").last()
    regimes = {r: mm[r] for r in ["vix", "baa_aaa", "dollar", "rate10y"] if r in mm}

    pairs = {
        "CYC-1": (-Z["ev_ebitda"], Z["gross_prof"], +1, "ev(저cheap)×gross_prof(고)"),
        "CYC-3": (Z["op_prof"], -Z["asset_growth"], +1, "op_prof(고)×asset_growth(저)"),
        "CYC-4": (Z["ep_yield"], Z["residual_mom"], +1, "ep_yield(고)×residual_mom"),
        "CYC-5": (Z["ep_yield"], -Z["idio_vol"], +1, "ep_yield(고)×idio_vol(저)"),
    }
    out = {"meta": {"H": H, "note": "CYC 교호 raw double-sort(재-z 없음)+hand-built FM+연속 regime. 재-z artifact 판별."}}
    for nm, (z1, z2, pred, spec) in pairs.items():
        did, qm = double_sort_did(z1, z2, fwd)
        out[nm] = dict(spec=spec, pred_sign=pred, quadrant_fwd=qm,
                       double_sort_DiD=size_test(did, f"{nm}_DiD"),
                       hand_fm=size_test(fm_handbuilt(z1, z2, fwd), f"{nm}_FM"),
                       regime_slope={r: cont_regime_slope(did, reg) for r, reg in regimes.items()})
    (ROOT / "_b2_cyc_verify_regime_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    for nm in pairs:
        r = out[nm]; ds, fm = r["double_sort_DiD"], r["hand_fm"]
        print(f"\n{nm} [{r['spec']}] pred={r['pred_sign']:+d}")
        print(f"  ★double-sort DiD(raw): mean={ds.get('mean')} t={ds.get('t_nw')} fb_sig={ds.get('fixed_b_sig')} wildP={ds.get('wild_p')} sign={ds.get('sign')}")
        print(f"  hand FM coef(raw)    : mean={fm.get('mean')} t={fm.get('t_nw')} fb_sig={fm.get('fixed_b_sig')} wildP={fm.get('wild_p')} sign={fm.get('sign')}")
        sigreg = [f"{rg}:t{v['t_hac']:+.2f}/p{v['wild_p']}{'★sig' if v.get('fixed_b_sig') else ''}" for rg, v in r["regime_slope"].items() if "slope" in v and v.get("fixed_b_sig")]
        print(f"  regime slope size-valid: {sigreg if sigreg else '없음(전 regime n.s.)'}")


if __name__ == "__main__":
    main()
