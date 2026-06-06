# -*- coding: utf-8 -*-
"""_b2_quality_single.py — ★W1 quality 단일축 + value stacking (exploratory family, team-lead 2026-06-04).
자문 2채널 수렴 = value 1축 편중 해소 = quality(gross_prof) 단일 cross-sectional alpha + value 음상관 등가중 stacking.
★exploratory FDR family(value confirmatory 와 별 family). 등가중만(weight 표본추정 금지=overfitting). 직교성 측정.
재현: python _b2_quality_single.py → _b2_quality_single_results.json
"""
import sys, json; from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M
sys.path.append("D:/projects/Inv/study-research/eq_us/industries/us_defensive/raw-v3")
from _b2_stats import effective_n, fixed_b_cv, wild_cluster_boot, persistence_block
from _b2_cyclical_interactions import build_signals, size_valid_block
ROOT = Path(__file__).resolve().parent; H = 12


def cross_corr(a, b):
    """월별 cross-sectional Spearman corr(a,b) 평균 = 직교성 측정."""
    idx = a.index.intersection(b.index); cs = []
    for dt in idx:
        d = pd.DataFrame({"a": a.loc[dt], "b": b.loc[dt]}).dropna()
        if len(d) < 10:
            continue
        r, _ = stats.spearmanr(d.a, d.b)
        if not np.isnan(r):
            cs.append(r)
    return float(np.mean(cs)) if cs else np.nan


def ir_proxy(ic_series):
    """IC 시계열 IR = mean/std (월별, annualize X = raw IR). + breadth √n_eff."""
    s = pd.Series(ic_series).dropna()
    if len(s) < 12:
        return None
    eff = effective_n(s.values)
    return dict(ir_raw=round(float(s.mean() / s.std()), 3) if s.std() > 0 else None,
                ir_neff=round(float(s.mean() / s.std() * np.sqrt(eff["n_eff"])), 3) if s.std() > 0 else None,
                n_eff=eff["n_eff"])


def main():
    px, ed, uni, macro = M.load(); secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last(); P = M.build_pit_panels(px, ed)
    Z = build_signals(px, ed, P, secmap)
    fwd = pxm.shift(-H) / pxm - 1
    z = lambda p: M.cs_z(p, secmap)
    # composites (cheap=high z, quality=high z)
    val = z((-Z["pbr"] + -Z["ev_ebitda"]) / 2)       # value: 저PBR·저EV = cheap → +z
    qual = z((Z["gross_prof"] + Z["op_prof"]) / 2)    # quality: 고gross·고op → +z
    combo = z((val + qual) / 2)                        # ★등가중 stacking (weight 표본추정 X)
    out = {"meta": {"H": H, "family": "us_equity_exploratory_v1 (★value confirmatory 와 별 family)",
                    "note": "quality 단일축 + value 등가중 stacking. 직교성 cross-corr. raw IC + fixed-b + IR proxy."}}
    sigs = {"gross_prof": Z["gross_prof"], "op_prof": Z["op_prof"], "quality_comp": qual,
            "value_comp": val, "value+quality_stack": combo}
    for nm, sig in sigs.items():
        ic, _ = M.cs_ic(sig, fwd)
        blk = size_valid_block(ic, nm)
        out[nm] = dict(size_valid=blk, ir=ir_proxy(ic))
    # 직교성: value ↔ quality cross-sectional corr
    out["orthogonality"] = dict(
        value_quality_cross_corr=round(cross_corr(val, qual), 4),
        gross_op_cross_corr=round(cross_corr(Z["gross_prof"], Z["op_prof"]), 4),
        note="value↔quality 음상관이면 등가중 stacking 분산 이득(결합 IR↑)")
    # 결합 IR vs value-only (stacking 이득 정량)
    ir_v = out["value_comp"]["ir"]; ir_c = out["value+quality_stack"]["ir"]
    out["stacking_gain"] = dict(value_only_ir_neff=ir_v.get("ir_neff") if ir_v else None,
                                stack_ir_neff=ir_c.get("ir_neff") if ir_c else None,
                                note="stack IR > value IR 이면 quality 추가 분산 이득 실증")
    (ROOT / "_b2_quality_single_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("=" * 78)
    for nm in ["gross_prof", "op_prof", "quality_comp", "value_comp", "value+quality_stack"]:
        b = out[nm]["size_valid"]; ir = out[nm]["ir"]
        print(f"{nm:22} IC={b.get('ic_mean')} t={b.get('t_nw')} fb_sig={b.get('fixed_b_sig')} wildP={b.get('p_wild_cluster')} n_eff={b.get('n_eff')} UP={b.get('underpowered')} | IR_neff={ir.get('ir_neff') if ir else None}")
    o = out["orthogonality"]; print(f"\n직교성: value↔quality cross-corr={o['value_quality_cross_corr']} (음수=분산이득) / gross↔op={o['gross_op_cross_corr']}")
    s = out["stacking_gain"]; print(f"stacking 이득: value-only IR={s['value_only_ir_neff']} → value+quality IR={s['stack_ir_neff']}")


main()
