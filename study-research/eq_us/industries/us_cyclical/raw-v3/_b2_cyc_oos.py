# -*- coding: utf-8 -*-
"""_b2_cyc_oos.py — ★CYC-3/CYC-4 split-sample 견고성 (team-lead, 2026-06-04).

pre-reg 가 약속한 OOS 게이트인데 interaction full-sample run 에서 빠짐 → 마감.
★정직 framing: full-sample 부호를 이미 봤으므로 "pristine pre-reg OOS" 아닌
  split-sample 방향지속성/견고성 체크(in-sample ≤2021-12 / OOS 2022-01~).
  reversal(wrong-sign 유의)이 sub-period 안정=진짜 신호 vs 단일구간 artifact 분리.
재사용: _b2_cyclical_interactions(build_signals/interaction_z/fwl_incremental_ic).
재현: python _b2_cyc_oos.py → _b2_cyc_oos_results.json
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M
from _b2_cyclical_interactions import build_signals, interaction_z, fwl_incremental_ic
from _b2_stats import effective_n, fixed_b_cv, wild_cluster_boot, persistence_block

ROOT = Path(__file__).resolve().parent
SPLIT = pd.Timestamp("2022-01-01")
H = 12


def stat_block(ic):
    ic = pd.Series(ic).dropna(); n = len(ic)
    if n < 8:
        return dict(n=n, note="insufficient")
    blk = persistence_block(ic.values); eff = effective_n(ic.values); mean = float(ic.mean())
    x = ic.values; e = x - x.mean(); g0 = (e @ e) / n; var = g0
    for k in range(1, min(blk, n - 1) + 1):
        var += 2 * (1 - k / (blk + 1)) * (e[k:] @ e[:-k]) / n
    se = float(np.sqrt(max(var, 1e-12) / n)); t = mean / se if se > 0 else np.nan
    fb = fixed_b_cv(n, blk)
    wc = wild_cluster_boot(pd.Series(x, index=ic.index), pd.DataFrame({"const": np.ones(n)}, index=ic.index),
                           "const", block=blk, B=9999) if n >= 12 else {"p_wild_cluster": None}
    return dict(ic_mean=round(mean, 4), n=n, n_eff=eff["n_eff"], t_nw=round(float(t), 2) if not np.isnan(t) else None,
                fixed_b_cv=fb["cv_5pct"], fixed_b_sig=bool(not np.isnan(t) and abs(t) > fb["cv_5pct"]),
                wild_p=wc.get("p_wild_cluster"), sign=int(np.sign(mean)))


def split_eval(ic_series, pred_sign):
    s = ic_series.dropna().sort_index()
    ins = s[s.index < SPLIT]; oos = s[s.index >= SPLIT]
    bi, bo = stat_block(ins), stat_block(oos)
    persist = (bi.get("sign") == bo.get("sign")) if ("sign" in bi and "sign" in bo) else None
    return dict(in_sample=bi, oos=bo, sign_persistent_in_to_oos=persist,
               flip_sign_pred=-pred_sign,
               flip_consistent=bool(bi.get("sign") == -pred_sign and bo.get("sign") == -pred_sign))


def main():
    px, ed, uni, macro = M.load()
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last(); P = M.build_pit_panels(px, ed)
    Z = build_signals(px, ed, P, secmap)
    fwd = pxm.shift(-H) / pxm - 1
    low_ag = -Z["asset_growth"]

    # CYC-3 op_prof × asset_growth(저), incr ⊥{op_prof, low_ag, net_issuance}. pred +1 (관측 −)
    i3 = interaction_z(Z["op_prof"], low_ag, secmap)
    ic3 = fwl_incremental_ic(i3, [Z["op_prof"], low_ag, Z["net_issuance"]], fwd, secmap)
    # CYC-4 ep_yield × residual_mom, incr ⊥{ep_yield, residual_mom}. pred +1 (관측 −)
    i4 = interaction_z(Z["ep_yield"], Z["residual_mom"], secmap)
    ic4 = fwl_incremental_ic(i4, [Z["ep_yield"], Z["residual_mom"]], fwd, secmap)

    out = {"meta": {"split": str(SPLIT.date()), "H": H,
                    "note": "split-sample 견고성(방향지속성). full-sample 부호 旣관측→pristine OOS 아님. reversal 안정성 진단."},
           "CYC-3": dict(spec="op_prof(고)×asset_growth(저) incr", pred=+1, **split_eval(ic3, +1)),
           "CYC-4": dict(spec="ep_yield(고)×residual_mom incr", pred=+1, **split_eval(ic4, +1))}
    (ROOT / "_b2_cyc_oos_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    for k in ["CYC-3", "CYC-4"]:
        r = out[k]; i, o = r["in_sample"], r["oos"]
        try:
            print(f"{k} {r['spec']} pred=+1 (flip={r['flip_sign_pred']})")
            print(f"   in-sample(≤2021): IC={i.get('ic_mean')} t={i.get('t_nw')} n={i.get('n')} n_eff={i.get('n_eff')} fb_sig={i.get('fixed_b_sig')} wildP={i.get('wild_p')} sign={i.get('sign')}")
            print(f"   OOS(2022~)      : IC={o.get('ic_mean')} t={o.get('t_nw')} n={o.get('n')} n_eff={o.get('n_eff')} fb_sig={o.get('fixed_b_sig')} wildP={o.get('wild_p')} sign={o.get('sign')}")
            print(f"   → 방향지속 in→OOS={r['sign_persistent_in_to_oos']} / flip(−)일관={r['flip_consistent']}")
        except Exception as e:
            print(k, "print skip", e)


if __name__ == "__main__":
    main()
