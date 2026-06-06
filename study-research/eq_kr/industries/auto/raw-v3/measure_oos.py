# -*- coding: utf-8 -*-
"""measure_oos.py — auto conditional IC walk-forward OOS split (S2 보강, team-lead 의무).
IS 2019-22 / OOS 2023-26 split → 핵심 cell 부호+magnitude OOS 유지 여부 = in-sample artifact 판별.
measure_conditional.py 의 함수 재사용. JSON 에 walk_forward_oos 추가 박제."""
from __future__ import annotations
import sys, io, json
import numpy as np, pandas as pd
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parent
# mc 모듈은 import 시 sys.stdout 을 wrap+close 하므로, fd 1 을 직접 새 wrapper 로 연다.
spec = importlib.util.spec_from_file_location("mc", str(ROOT / "measure_conditional.py"))
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)
import os
sys.stdout = io.TextIOWrapper(io.FileIO(os.dup(1), "w"), encoding="utf-8", write_through=True)


def split_report(label, ic, rows):
    is_ic = ic[(ic.index >= "2019-01-01") & (ic.index <= "2022-12-31")]
    oos_ic = ic[(ic.index >= "2023-01-01") & (ic.index <= "2026-12-31")]
    if len(is_ic) >= 3 and len(oos_ic) >= 3:
        im, om = float(is_ic.mean()), float(oos_ic.mean())
        sh = bool(np.sign(im) == np.sign(om))
        print(f"{label:40s} IS={im:+.4f}(n{len(is_ic)})  OOS={om:+.4f}(n{len(oos_ic)})  {'OK' if sh else 'FLIP'}")
        rows[label.strip()] = {"is_ic": round(im, 4), "is_n": len(is_ic),
                               "oos_ic": round(om, 4), "oos_n": len(oos_ic), "sign_hold": sh}


def main():
    px, lab, fin, uni = mc.load()
    price_sigs = mc.build_price_signals(px)
    val_sigs = mc.build_valuation_signals(px, fin, uni)
    all_sigs = {**price_sigs, **val_sigs}
    anchor = price_sigs["mom_6"].dropna(how="all").index
    lab19 = lab.loc["2019-01-01":]

    print("=== walk-forward OOS (IS 2019-22 / OOS 2023-26) ===")
    rows = {}
    for sname, sig in all_sigs.items():
        for hname, h in [("y_20d", 20), ("y_60d", 60)]:
            fwd = mc.forward_returns_daily(px, anchor, h)
            ic_all = mc.ic_series(sig, fwd)
            if len(ic_all) < 6:
                continue
            split_report(f"{sname}__{hname} [uncond]", ic_all, rows)
            for axis, rg in [("krw_regime", "KRW_weak"), ("macro_regime", "Slowdown"),
                             ("macro_regime", "Recovery"), ("flow_regime", "flow_strong_buy")]:
                months = lab19[lab19[axis] == rg].index
                sub = ic_all[ic_all.index.isin(months)]
                split_report(f"  {sname}__{hname} [{axis}={rg}]", sub, rows)

    val = json.loads((ROOT / "validation-conditional-v3.json").read_text(encoding="utf-8"))
    val["walk_forward_oos"] = {"split": "IS 2019-01~2022-12 / OOS 2023-01~2026-05", "cells": rows}
    (ROOT / "validation-conditional-v3.json").write_text(
        json.dumps(val, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n박제 완료: walk_forward_oos {len(rows)} cells")


if __name__ == "__main__":
    main()
