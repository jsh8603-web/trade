# -*- coding: utf-8 -*-
"""_b2_cyc_rankfm.py — ★CYC Rank-based Fama-MacBeth over-kill 재판정 (team-lead, 2026-06-04).
def 측 _b2_def_rankfm.py 와 동일 방법(매월 rank(pct) OLS 교호계수 시계열 → fixed-b+wild).
대상: CYC-1(Novy-Marx theory-pinned) + rank-IC↔linear 불일치 CYC-3/4/5 (re-z artifact 의심 전수).
outlier-robust(rank) + 연속정보 보존(median 2x2 double-sort 의 검정력 손실 회피). 재현: python _b2_cyc_rankfm.py
"""
import sys; from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M
sys.path.append("D:/projects/Inv/study-research/eq_us/industries/us_defensive/raw-v3")
from _b2_stats import effective_n, fixed_b_cv, wild_cluster_boot, persistence_block
from _b2_cyclical_interactions import build_signals
ROOT = Path(__file__).resolve().parent; H = 12; SPLIT = pd.Timestamp("2022-01-01")


def stest(s):
    s = pd.Series(s).dropna(); n = len(s)
    if n < 12: return dict(n=n, note="insuf")
    blk = persistence_block(s.values); eff = effective_n(s.values); mean = float(s.mean())
    x = s.values; e = x - x.mean(); g0 = (e @ e) / n; var = g0
    for k in range(1, min(blk, n - 1) + 1): var += 2 * (1 - k / (blk + 1)) * (e[k:] @ e[:-k]) / n
    se = float(np.sqrt(max(var, 1e-12) / n)); t = mean / se if se > 0 else np.nan; fb = fixed_b_cv(n, blk)
    wc = wild_cluster_boot(pd.Series(x, index=s.index), pd.DataFrame({"const": np.ones(n)}, index=s.index), "const", block=blk, B=9999)
    return dict(coef=round(mean, 5), n=n, n_eff=eff["n_eff"], t_nw=round(float(t), 2) if not np.isnan(t) else None,
        fixed_b_cv=fb["cv_5pct"], fixed_b_sig=bool(not np.isnan(t) and abs(t) > fb["cv_5pct"]), wild_p=wc.get("p_wild_cluster"), sign=int(np.sign(mean)))


def rank_fm(z1, z2, fwd, min_n=10):
    idx = z1.index.intersection(z2.index).intersection(fwd.index); coefs = []
    for dt in idx:
        d = pd.DataFrame({"z1": z1.loc[dt], "z2": z2.loc[dt], "y": fwd.loc[dt]}).dropna()
        if len(d) < min_n: continue
        r1 = d.z1.rank(pct=True); r2 = d.z2.rank(pct=True); ry = d.y.rank(pct=True)
        ri = (r1 - 0.5) * (r2 - 0.5)
        X = sm.add_constant(pd.DataFrame({"r1": r1, "r2": r2, "ri": ri}))
        try: coefs.append((dt, float(sm.OLS(ry, X).fit().params["ri"])))
        except: pass
    return pd.Series([c[1] for c in coefs], index=[c[0] for c in coefs])


def main():
    px, ed, uni, macro = M.load(); secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last(); P = M.build_pit_panels(px, ed)
    Z = build_signals(px, ed, P, secmap)
    fwd = pxm.shift(-H) / pxm - 1
    cheap_ev = -Z["ev_ebitda"]; low_ag = -Z["asset_growth"]; low_vol = -Z["idio_vol"]
    pairs = [
        ("CYC-1", cheap_ev, Z["gross_prof"], +1, "ev(저cheap)×gross_prof(고) Novy-Marx"),
        ("CYC-3", Z["op_prof"], low_ag, +1, "op_prof(고)×asset_growth(저) q-factor"),
        ("CYC-4", Z["ep_yield"], Z["residual_mom"], +1, "ep_yield(고)×residual_mom"),
        ("CYC-5", Z["ep_yield"], low_vol, +1, "ep_yield(고)×idio_vol(저)"),
    ]
    out = {"meta": {"method": "rank-based Fama-MacBeth, H=12, B=9999, SPLIT=2022-01"}}
    for nm, z1, z2, pred, spec in pairs:
        cs = rank_fm(z1, z2, fwd); full = stest(cs)
        ins = stest(cs[cs.index < SPLIT]); oos = stest(cs[cs.index >= SPLIT])
        out[nm] = dict(spec=spec, pred=pred, full=full, in_sample=ins, oos=oos, sign_match=bool(full.get("sign") == pred))
    (ROOT / "_b2_cyc_rankfm_results.json").write_text(__import__("json").dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    for nm, *_ in pairs:
        r = out[nm]; f = r["full"]; i = r["in_sample"]; o = r["oos"]
        print(f"{nm} [{r['spec']}] pred={r['pred']:+d} sign_match={r['sign_match']}")
        print(f"  full   coef={f.get('coef')} t={f.get('t_nw')} fb_sig={f.get('fixed_b_sig')} wildP={f.get('wild_p')} n_eff={f.get('n_eff')}")
        print(f"  in≤21  coef={i.get('coef')} t={i.get('t_nw')} fb_sig={i.get('fixed_b_sig')} | OOS coef={o.get('coef')} t={o.get('t_nw')} fb_sig={o.get('fixed_b_sig')}")


main()
