# -*- coding: utf-8 -*-
"""measure_subcluster.py — ★aitech sub-cluster A-4 부호점검 + flow_strong_buy interaction 정식 측정.

frame _dispatch-gates G-A A-4: 채택 신호 IC 부호가 sub-cluster(internet/game/saas)에서 cancel 되는지 점검.
  - cancel 시 분리 트리거 + team-lead 보고.
frame A-5 / G-B: family_2 interaction = aitech 핵심 conditioning(flow_strong_buy) 정식 측정.

측정:
  1) sub-cluster 별 primary 신호(pbr_z / per_z / mom_12_1 / rev_1m) IC 부호 — cancel 점검.
  2) flow_strong_buy interaction term (pooled panel, month-clustered SE) — aitech 핵심 conditioning.

measure_conditional.py 함수 재사용 (drift 0).
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT))
from measure_conditional import (
    load, build_price_signals, build_valuation_signals, forward_returns_daily,
    ic_series, measure_interaction_terms, csz,
)

# stdout UTF-8 (measure_conditional import 후 1회만)
if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass


def subcluster_ic(all_sigs, px, anchor, uni, horizon_d=60):
    """sub-cluster 별 신호 IC 부호 점검 (A-4). universe-relative z-score 는 전체 유지,
    IC 계산 시 sub-cluster 종목만 sub-setting (cluster 내 횡단면)."""
    fwd = forward_returns_daily(px, anchor, horizon_d)
    clusters = uni.groupby("sub_cluster").groups  # {cluster: index(codes)}
    out = {}
    for sig_name in ["pbr_z", "per_z", "mom_12_1", "rev_1m", "vol_60"]:
        sig = all_sigs[sig_name]
        out[sig_name] = {}
        # 전체
        ic_all = ic_series(sig, fwd, min_n=5)
        out[sig_name]["ALL"] = {"ic": round(float(ic_all.mean()), 4), "n_mo": len(ic_all)}
        # cluster 별 (cluster 내 종목만 z-score 재계산 = peer-relative within cluster)
        for cl, codes in clusters.items():
            codes = [c for c in codes if c in sig.columns]
            if len(codes) < 3:
                out[sig_name][cl] = {"ic": None, "note": f"n_codes={len(codes)}<3 INSUFFICIENT"}
                continue
            # cluster 내 peer-relative z 재계산 (raw 패널 있으면), 없으면(pbr/per) 전체 z 의 cluster subset
            if ("_raw_" + sig_name) in all_sigs:
                sub_sig = csz(all_sigs["_raw_" + sig_name][codes])
            else:
                sub_sig = sig[[c for c in codes if c in sig.columns]]
            ic_cl = ic_series(sub_sig, fwd, min_n=3)   # ic_series 가 sig/fwd 컬럼 교집합 자동 처리
            out[sig_name][cl] = {"ic": round(float(ic_cl.mean()), 4) if len(ic_cl) else None,
                                 "n_mo": len(ic_cl), "n_codes": len(codes)}
        # cancel 판정
        cluster_ics = {k: v["ic"] for k, v in out[sig_name].items() if k != "ALL" and v.get("ic") is not None}
        signs = {k: np.sign(v) for k, v in cluster_ics.items() if abs(v) > 0.02}
        pos = [k for k, s in signs.items() if s > 0]
        neg = [k for k, s in signs.items() if s < 0]
        out[sig_name]["_cancel_check"] = {
            "positive_clusters": pos, "negative_clusters": neg,
            "cancel": bool(pos and neg),
            "verdict": ("★CANCEL — 분리 트리거 (cluster 부호 반대)" if (pos and neg)
                        else "부호 일관 (sub-cluster 통합 유지 가능)"),
        }
    return out


def main():
    px, lab, fin, uni = load()
    price_sigs = build_price_signals(px)
    val_sigs = build_valuation_signals(px, fin, uni)
    # raw (z-score 전) 패널 보존 = cluster 내 재 z-score 용
    pxm = px.resample("ME").last()
    ret_d = px.pct_change()
    raw_panels = {
        "_raw_mom_12_1": pxm.shift(1) / pxm.shift(12) - 1,
        "_raw_rev_1m": pxm / pxm.shift(1) - 1,
        "_raw_vol_60": (ret_d.rolling(60).std() * np.sqrt(252)).resample("ME").last(),
    }
    all_sigs = {**price_sigs, **val_sigs, **raw_panels}
    anchor = price_sigs["mom_6"].dropna(how="all").index
    lab19 = lab.loc["2019-01-01":]

    results = {"note": "aitech sub-cluster A-4 부호점검(internet/game/saas) + flow_strong_buy interaction(family_2 핵심)"}

    # ── 1) sub-cluster A-4 부호점검 (y_60d 본진) ──
    results["subcluster_signcheck"] = subcluster_ic(all_sigs, px, anchor, uni, horizon_d=60)

    # ── 2) flow_strong_buy interaction term (aitech 핵심 conditioning, family_2) ──
    fsb = measure_interaction_terms(
        {**price_sigs, "pbr_z": val_sigs["pbr_z"], "per_z": val_sigs["per_z"]},
        px, anchor, lab19, dummy_regime=("flow_regime", "flow_strong_buy"), horizon_d=20)
    results["family_2_flow_strong_buy"] = fsb

    # ── 3) macro Recovery interaction (mom 음 reversal 강한 cell) ──
    rec = measure_interaction_terms(
        price_sigs, px, anchor, lab19, dummy_regime=("macro_regime", "Recovery"), horizon_d=60)
    results["family_2_macro_recovery"] = rec

    out = ROOT / "validation-subcluster-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}\n")

    print("=== sub-cluster A-4 부호점검 (y_60d, cluster 내 peer-relative z) ===")
    for sig, d in results["subcluster_signcheck"].items():
        cc = d["_cancel_check"]
        cl_str = " ".join(f"{k}={d[k]['ic']:+.3f}" if d[k].get("ic") is not None else f"{k}=NA"
                          for k in ["internet", "game", "saas"] if k in d)
        print(f"  {sig:10s} ALL={d['ALL']['ic']:+.4f} | {cl_str} | {cc['verdict']}")

    print("\n=== flow_strong_buy interaction (aitech 핵심, y_20d) ===")
    for r in fsb["results"]:
        if r.get("status") == "INSUFFICIENT":
            print(f"  {r['signal']:10s} INSUFFICIENT")
        else:
            print(f"  {r['signal']:10s} b_main={r['b_main']:+.4f}(t={r['t_main']:+.2f}) "
                  f"b_inter={r['b_interaction']:+.4f}(t={r['t_interaction']:+.2f}) {r['verdict']}")

    print("\n=== macro Recovery interaction (y_60d) ===")
    for r in rec["results"]:
        if r.get("status") == "INSUFFICIENT":
            print(f"  {r['signal']:10s} INSUFFICIENT")
        else:
            print(f"  {r['signal']:10s} b_main={r['b_main']:+.4f}(t={r['t_main']:+.2f}) "
                  f"b_inter={r['b_interaction']:+.4f}(t={r['t_interaction']:+.2f}) {r['verdict']}")


if __name__ == "__main__":
    main()
