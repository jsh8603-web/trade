# -*- coding: utf-8 -*-
"""_b2_w2_accruals.py — ★W2 accruals horizon 완결 (defensive, exploratory family, 2026-06-04).
breadth sweep 서 accruals wild p=None(n<24 미완) → 3/6/12/24M horizon size_valid 마감(테스트 완전성, 발견 기대 낮음).
accruals=(NI−CFO)/assets, Sloan(1996) 부호 음(고accrual→저forward). 재현: python _b2_w2_accruals.py
"""
import sys, json; from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M
from _b2_stats import effective_n, fixed_b_cv, wild_cluster_boot, persistence_block
from _breadth_sweep import build_breadth_panels
from _b2_quality_single import size_valid_block
ROOT = Path(__file__).resolve().parent; DATA = ROOT / "data"


def main():
    px, ed, uni, macro = M.load(); secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last()
    amt = pd.read_parquet(DATA / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    B = build_breadth_panels(px, ed, amt); acc = M.cs_z(B["accruals"], secmap)
    out = {"meta": {"signal": "accruals (NI-CFO)/assets, Sloan 부호 음", "family": "us_equity_exploratory_v1"}}
    for H in [3, 6, 12, 24]:
        fwd = pxm.shift(-H) / pxm - 1
        ic, _ = M.cs_ic(acc, fwd)
        out[f"{H}M"] = size_valid_block(ic, f"accruals_{H}M")
    (ROOT / "_b2_w2_accruals_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("=" * 70)
    for H in [3, 6, 12, 24]:
        b = out[f"{H}M"]
        print(f"accruals {H:2}M  IC={b.get('ic_mean')} t={b.get('t_nw')} fb_sig={b.get('fixed_b_sig')} wildP={b.get('p_wild_cluster')} n_eff={b.get('n_eff')} UP={b.get('underpowered')}")


main()
