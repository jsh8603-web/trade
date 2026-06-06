# -*- coding: utf-8 -*-
"""_b2_def_oos.py — ★DEF-2/DEF-1 split-sample 견고성 (team-lead, 2026-06-04).

생존 2개(DEF-2 CONFIRM / DEF-1 TENTATIVE)의 in-sample(≤2021-12) vs OOS(2022~) 방향지속성·견고성.
재사용: _b2_defensive_interactions(interaction_z/fwl_incremental_ic) + measure + _breadth_sweep.
재현: python _b2_def_oos.py → _b2_def_oos_results.json
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M
from _b2_stats import effective_n, fixed_b_cv, wild_cluster_boot, persistence_block
from _b2_defensive_interactions import interaction_z, fwl_incremental_ic
from _breadth_sweep import build_breadth_panels

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
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
    bi, bo = stat_block(s[s.index < SPLIT]), stat_block(s[s.index >= SPLIT])
    return dict(in_sample=bi, oos=bo,
               sign_persistent=(bi.get("sign") == bo.get("sign")) if ("sign" in bi and "sign" in bo) else None,
               oos_sign_matches_pred=bool(bo.get("sign") == pred_sign) if "sign" in bo else None)


def main():
    px, ed, uni, macro = M.load()
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last(); P = M.build_pit_panels(px, ed)
    amt = pd.read_parquet(DATA / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    B = build_breadth_panels(px, ed, amt)
    z = lambda p: M.cs_z(p, secmap)
    ep_z, div_z = z(P["ep_yield"]), z(P["dividend_yield"])
    nissu_z, opp_z = z(B["net_issuance"]), z(B["op_profitability"])
    fwd = pxm.shift(-H) / pxm - 1

    i2 = interaction_z(div_z, opp_z, secmap)      # DEF-2 pred +1 (CONFIRM)
    ic2 = fwl_incremental_ic(i2, [div_z, opp_z], fwd)
    i1 = interaction_z(nissu_z, ep_z, secmap)     # DEF-1 pred +1, 관측 − (TENTATIVE PW)
    ic1 = fwl_incremental_ic(i1, [nissu_z, ep_z], fwd)

    out = {"meta": {"split": str(SPLIT.date()), "H": H, "note": "생존 2개 견고성. DEF-2 정방향/DEF-1 PW역방향 견고성 진단."},
           "DEF-2": dict(spec="dividend_yield(고)×op_prof(고) incr", pred=+1, **split_eval(ic2, +1)),
           "DEF-1": dict(spec="net_issuance×ep_yield incr", pred=+1, observed="negative(PW)", **split_eval(ic1, +1))}
    (ROOT / "_b2_def_oos_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    for k in ["DEF-2", "DEF-1"]:
        r = out[k]; i, o = r["in_sample"], r["oos"]
        try:
            print(f"{k} {r['spec']} pred=+1")
            print(f"   in-sample(≤2021): IC={i.get('ic_mean')} t={i.get('t_nw')} n={i.get('n')} n_eff={i.get('n_eff')} fb_sig={i.get('fixed_b_sig')} wildP={i.get('wild_p')} sign={i.get('sign')}")
            print(f"   OOS(2022~)      : IC={o.get('ic_mean')} t={o.get('t_nw')} n={o.get('n')} n_eff={o.get('n_eff')} fb_sig={o.get('fixed_b_sig')} wildP={o.get('wild_p')} sign={o.get('sign')}")
            print(f"   → 방향지속={r['sign_persistent']} / OOS부호=pred매칭={r['oos_sign_matches_pred']}")
        except Exception as e:
            print(k, "skip", e)


if __name__ == "__main__":
    main()
