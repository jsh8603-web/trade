# -*- coding: utf-8 -*-
"""_b2_quality_single.py — ★W1 quality 단일축 + 기존alpha stacking (defensive, exploratory family, 2026-06-04).
defensive value=ep_yield(anti-value 약) + primary alpha=net_issuance(PARTIAL). quality=op_profitability/gross_prof.
quality 단일 cross-sectional IC + net_issuance/ep 직교성 + stacking IR. ★등가중만. exploratory FDR family.
재현: python _b2_quality_single.py → _b2_quality_single_results.json
"""
import sys, json; from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M
from _b2_stats import effective_n, fixed_b_cv, wild_cluster_boot, persistence_block
from _breadth_sweep import build_breadth_panels
ROOT = Path(__file__).resolve().parent; DATA = ROOT / "data"; H = 12


def size_valid_block(ic, label=""):
    ic = pd.Series(ic).dropna(); n = len(ic)
    if n < 12:
        return dict(label=label, n=n, note="insufficient")
    blk = persistence_block(ic.values); eff = effective_n(ic.values); mean = float(ic.mean())
    x = ic.values; e = x - x.mean(); g0 = (e @ e) / n; var = g0
    for k in range(1, min(blk, n - 1) + 1):
        var += 2 * (1 - k / (blk + 1)) * (e[k:] @ e[:-k]) / n
    se = float(np.sqrt(max(var, 1e-12) / n)); t = mean / se if se > 0 else np.nan; fb = fixed_b_cv(n, blk)
    Xc = pd.DataFrame({"const": np.ones(n)}, index=ic.index)
    wc = wild_cluster_boot(pd.Series(ic.values, index=ic.index), Xc, "const", block=blk, B=9999)
    return dict(label=label, ic_mean=round(mean, 4), n=n, n_eff=eff["n_eff"], underpowered=bool(eff["n_eff"] < 30),
                t_nw=round(float(t), 2) if not np.isnan(t) else None, fixed_b_cv=fb["cv_5pct"],
                fixed_b_sig=bool(not np.isnan(t) and abs(t) > fb["cv_5pct"]), p_wild_cluster=wc.get("p_wild_cluster"))


def cross_corr(a, b):
    idx = a.index.intersection(b.index); cs = []
    for dt in idx:
        d = pd.DataFrame({"a": a.loc[dt], "b": b.loc[dt]}).dropna()
        if len(d) < 10:
            continue
        r, _ = stats.spearmanr(d.a, d.b)
        if not np.isnan(r):
            cs.append(r)
    return float(np.mean(cs)) if cs else np.nan


def ir_proxy(ic):
    s = pd.Series(ic).dropna()
    if len(s) < 12 or s.std() == 0:
        return None
    eff = effective_n(s.values)
    return dict(ir_neff=round(float(s.mean() / s.std() * np.sqrt(eff["n_eff"])), 3), n_eff=eff["n_eff"])


def main():
    px, ed, uni, macro = M.load(); secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last(); P = M.build_pit_panels(px, ed)
    amt = pd.read_parquet(DATA / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    B = build_breadth_panels(px, ed, amt); z = lambda p: M.cs_z(p, secmap)
    fwd = pxm.shift(-H) / pxm - 1
    ep = z(P["ep_yield"]); nis = z(B["net_issuance"]); opp = z(B["op_profitability"])
    gp = z(P["gross_prof"]) if "gross_prof" in P else None
    qual = z((opp + (gp if gp is not None else opp)) / 2) if gp is not None else opp
    out = {"meta": {"H": H, "family": "us_equity_exploratory_v1 (★별 family)",
                    "note": "defensive quality 단일 + net_issuance(primary alpha)/ep 직교성 + stacking. anti-value ep 부호 음 주의."}}
    sigs = {"op_profitability": opp, "net_issuance": nis, "ep_yield": ep}
    if gp is not None:
        sigs["gross_prof"] = gp; sigs["quality_comp"] = qual
    # ★stacking: net_issuance(primary +) + quality(op_prof) 등가중
    stack_nq = z((nis + opp) / 2); sigs["net_iss+quality_stack"] = stack_nq
    for nm, sig in sigs.items():
        ic, _ = M.cs_ic(sig, fwd)
        out[nm] = dict(size_valid=size_valid_block(ic, nm), ir=ir_proxy(ic))
    out["orthogonality"] = dict(
        netiss_quality=round(cross_corr(nis, opp), 4), ep_quality=round(cross_corr(ep, opp), 4),
        note="net_issuance↔quality, ep↔quality cross-corr. 직교(≈0/음)면 stacking 이득")
    ir_n = out["net_issuance"]["ir"]; ir_s = out["net_iss+quality_stack"]["ir"]
    out["stacking_gain"] = dict(netiss_only_ir=ir_n.get("ir_neff") if ir_n else None,
                                stack_ir=ir_s.get("ir_neff") if ir_s else None)
    (ROOT / "_b2_quality_single_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("=" * 78)
    order = ["op_profitability", "gross_prof", "quality_comp", "net_issuance", "ep_yield", "net_iss+quality_stack"]
    for nm in order:
        if nm not in out:
            continue
        b = out[nm]["size_valid"]; ir = out[nm]["ir"]
        print(f"{nm:22} IC={b.get('ic_mean')} t={b.get('t_nw')} fb_sig={b.get('fixed_b_sig')} wildP={b.get('p_wild_cluster')} n_eff={b.get('n_eff')} UP={b.get('underpowered')} | IR={ir.get('ir_neff') if ir else None}")
    o = out["orthogonality"]; print(f"\n직교성: net_iss↔quality={o['netiss_quality']} / ep↔quality={o['ep_quality']}")
    s = out["stacking_gain"]; print(f"stacking: net_iss-only IR={s['netiss_only_ir']} → net_iss+quality IR={s['stack_ir']}")


main()
