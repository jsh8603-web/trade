# -*- coding: utf-8 -*-
"""_b2_w4_lowvol.py — ★W4 low-vol/BAB 단일축 1회 확인 (cyclical, exploratory family, 2026-06-04).
자문 Claude = sector-neutral within-demean 이 cross-sector low-vol(BAB 본질) 제거 → 구조적 약화 prior.
1회 확인만(후순위). low_vol=−idio_vol(저vol=고z). 3/6/12/24M size_valid. 재현: python _b2_w4_lowvol.py
"""
import sys, json; from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M
sys.path.append("D:/projects/Inv/study-research/eq_us/industries/us_defensive/raw-v3")
from _b2_stats import effective_n, fixed_b_cv, wild_cluster_boot, persistence_block
from _b2_cyclical_interactions import build_signals, size_valid_block
ROOT = Path(__file__).resolve().parent


def main():
    px, ed, uni, macro = M.load(); secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last(); P = M.build_pit_panels(px, ed)
    Z = build_signals(px, ed, P, secmap)
    low_vol = M.cs_z(-Z["idio_vol"], secmap)   # 저vol=고z (BAB long leg)
    out = {"meta": {"signal": "low_vol = -idio_vol (BAB, sector-neutral within-demean)", "family": "us_equity_exploratory_v1",
                    "caveat": "자문 Claude: within-demean 이 cross-sector low-vol 제거 → 구조적 약화"}}
    for H in [3, 6, 12, 24]:
        fwd = pxm.shift(-H) / pxm - 1
        ic, _ = M.cs_ic(low_vol, fwd)
        out[f"{H}M"] = size_valid_block(ic, f"low_vol_{H}M")
    (ROOT / "_b2_w4_lowvol_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("=" * 70)
    for H in [3, 6, 12, 24]:
        b = out[f"{H}M"]
        print(f"low_vol {H:2}M  IC={b.get('ic_mean')} t={b.get('t_nw')} fb_sig={b.get('fixed_b_sig')} wildP={b.get('p_wild_cluster')} n_eff={b.get('n_eff')} UP={b.get('underpowered')}")


main()
