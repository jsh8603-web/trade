# -*- coding: utf-8 -*-
"""measure_walkforward.py — battery 핵심 conditional 신호 walk-forward OOS verdict (S2/S5).

team-lead 지시 = IS(2019-22)/OOS(2023-26) split. in-sample 정합이 artifact 인지 OOS 로 직접 검정.
★battery 핵심 = (a) momentum 양 continuation (mom_6/mom_12_1) (b) flow_strong_buy interaction 음 flip.
   = "2022 단일 episode(리튬 하이퍼사이클 붕괴) 종속?" 을 walk-forward 가 직접 답.

측정:
  1) unconditional mom_6/mom_12_1 (y_60d 본진) IS vs OOS IC 부호+magnitude.
  2) flow_neutral regime cell (momentum 증폭축) IS vs OOS.
  3) flow_strong_buy interaction term IS vs OOS (t-stat 생존).

measure_conditional.py 의 함수 재사용 (동일 신호 정의 = drift 0).
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT))
from measure_conditional import (
    load, build_price_signals, forward_returns_daily, ic_series, measure_interaction_terms,
)

IS = ("2019-01-01", "2022-12-31")
OOS = ("2023-01-01", "2026-12-31")


def split_ic(ic: pd.Series):
    is_ic = ic[(ic.index >= IS[0]) & (ic.index <= IS[1])]
    oos_ic = ic[(ic.index >= OOS[0]) & (ic.index <= OOS[1])]
    if len(is_ic) < 3 or len(oos_ic) < 3:
        return None
    im, om = float(is_ic.mean()), float(oos_ic.mean())
    return {"is_ic": round(im, 4), "is_n": len(is_ic), "oos_ic": round(om, 4), "oos_n": len(oos_ic),
            "sign_hold": bool(np.sign(im) == np.sign(om)),
            "verdict": ("✅부호유지" if np.sign(im) == np.sign(om) else "❌부호반전(artifact)") +
                       (" +magnitude" if abs(om) >= abs(im) * 0.7 else " (magnitude 약화)")}


def interaction_split(price_sigs, px, anchor, lab19, dummy, signal, horizon_d=20):
    """flow_strong_buy interaction term 을 IS/OOS 기간별 재측정 (t-stat 생존)."""
    out = {}
    for tag, (lo, hi) in [("IS", IS), ("OOS", OOS)]:
        anchor_sub = anchor[(anchor >= lo) & (anchor <= hi)]
        res = measure_interaction_terms(
            {signal: price_sigs[signal]}, px, anchor_sub, lab19, dummy_regime=dummy, horizon_d=horizon_d)
        r0 = res["results"][0] if res["results"] else {}
        out[tag] = {"b_interaction": r0.get("b_interaction"), "t_interaction": r0.get("t_interaction"),
                    "n_months": r0.get("n_months"), "status": r0.get("status", "ok")}
    return out


def main():
    px, lab, fin, uni = load()
    price_sigs = build_price_signals(px)
    anchor = price_sigs["mom_6"].dropna(how="all").index
    lab19 = lab.loc["2019-01-01":]

    results = {"split": {"IS": IS, "OOS": OOS},
               "note": "battery momentum 양 continuation + flow_strong_buy interaction 음 flip 의 walk-forward OOS 검정.",
               "unconditional": {}, "regime_cell": {}, "interaction": {}}

    # 1) unconditional momentum (y_60d 본진 + y_20d 메인)
    for sig in ["mom_6", "mom_12_1", "rev_1m"]:
        for h, hd in [("y_60d", 60), ("y_20d", 20)]:
            fwd = forward_returns_daily(px, anchor, hd)
            ic = ic_series(price_sigs[sig], fwd)
            sp = split_ic(ic)
            if sp:
                results["unconditional"][f"{sig}__{h}"] = sp

    # 2) regime cell: flow_neutral (momentum 증폭축) — IS/OOS
    flow_neutral_months = lab19["flow_regime"][lab19["flow_regime"] == "flow_neutral"].index
    for sig in ["mom_6", "mom_12_1"]:
        for h, hd in [("y_60d", 60), ("y_20d", 20)]:
            fwd = forward_returns_daily(px, anchor, hd)
            ic = ic_series(price_sigs[sig], fwd)
            ic_fn = ic[ic.index.isin(flow_neutral_months)]
            sp = split_ic(ic_fn)
            if sp:
                results["regime_cell"][f"{sig}__{h}__flow_neutral"] = sp

    # 3) flow_strong_buy interaction term IS/OOS (battery primary conditional)
    for sig in ["mom_6", "mom_12_1"]:
        results["interaction"][f"{sig}__flow_strong_buy"] = interaction_split(
            price_sigs, px, anchor, lab19, ("flow_regime", "flow_strong_buy"), sig, horizon_d=20)

    out = ROOT / "validation-walkforward-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}\n")
    print("=== unconditional momentum walk-forward (IS 2019-22 / OOS 2023-26) ===")
    for k, v in results["unconditional"].items():
        print(f"  {k:18s} IS={v['is_ic']:+.4f}(n={v['is_n']}) OOS={v['oos_ic']:+.4f}(n={v['oos_n']}) {v['verdict']}")
    print("\n=== flow_neutral regime cell walk-forward ===")
    for k, v in results["regime_cell"].items():
        print(f"  {k:28s} IS={v['is_ic']:+.4f}(n={v['is_n']}) OOS={v['oos_ic']:+.4f}(n={v['oos_n']}) {v['verdict']}")
    print("\n=== flow_strong_buy interaction term walk-forward (t 생존) ===")
    for k, v in results["interaction"].items():
        print(f"  {k}: IS t_inter={v['IS'].get('t_interaction')}(n_mo={v['IS'].get('n_months')}) → "
              f"OOS t_inter={v['OOS'].get('t_interaction')}(n_mo={v['OOS'].get('n_months')})")


if __name__ == "__main__":
    main()
