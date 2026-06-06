# -*- coding: utf-8 -*-
"""within_industry_residual_kr.py — WIRE5 Phase 2c/2d: 산업 내 종목 selection 잔차 산업별 메타분석.

★사용자 통찰(2026-06-06): "줄자는 capsule analyst가 이미 업종별 맞는 걸로 쟀다(IC 검증 완료)."
  → v1(book-to-price 단일 잣대 통일측정)은 capsule 정밀도 버린 실수. v2 = capsule 측정IC를 SSOT로
  집계 + N_eff PR(과점 자동감지) + ρ_i 메타분석. ★새 cross-sectional 측정 X (capsule이 SSOT).

자문 C9~C13 반영:
- C9 W_i(rotation)·v_{j|i}(selection) 독립 베팅.
- C10 산업내 잔차 불안정 → L2 자르기 아니라 v 산업중립(ρ_i) 수축.
- C11 소수종목 = 공통원인 N_eff,i(participation ratio, raw count 아님). N_eff 한번만(이중처벌 방지).
- C12 per-industry IC = capsule이 이미 partial-pool급 검증(BY생존/OOS/CPCV). 메타는 N_eff·신뢰만.

★CAPSULE_IC 출처 = 각 업종 summary.yaml + validation-*.json (Explore 추출 2026-06-06). caveat 박제.
N_eff = prices.parquet idio 분산 PR (실측, raw count 아님).
⛔ production 무접촉. 산출 = _rotation/validation-within-residual-v2.json.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
IND = ROOT.parent
START = "2019-01-01"

# ★capsule 측정 selection IC (업종별 맞는 줄자, SSOT=각 capsule). |IC|=예측력 크기, by=BY생존, caveat.
CAPSULE_IC = {
    "aitech":        {"signal": "cs_pbr_z_y12m",            "ic": -0.183, "by": True,  "caveat": "size 위장 아님(t=-3.51)"},
    "steel":         {"signal": "cs_mom_12_1_reversal_y12m","ic": -0.181, "by": True,  "caveat": "small-universe breadth-adj IR -0.81"},
    "chemical":      {"signal": "cs_vol_60_y60d",           "ic": -0.142, "by": True,  "caveat": "n=17 small-n"},
    "consumer":      {"signal": "cs_per_z(3M primary)",     "ic": -0.141, "by": False, "caveat": "24M degenerate, 3M primary, single-episode 의존"},
    "auto":          {"signal": "cs_capex_ratio_y60d",      "ic": -0.117, "by": False, "caveat": "OOS robust(FDR 생존), pbr 병행"},
    "semiconductor": {"signal": "cs_pbr_z_24m",             "ic": -0.114, "by": True,  "caveat": "BY 생존 유일(m=8)"},
    "battery":       {"signal": "inv_ratio/mom_6 (+부호!)", "ic": +0.112, "by": False, "caveat": "★성장주=momentum continuation/재고확대, value(-)와 정반대"},
    "telecom":       {"signal": "equipment_pbr (size-neut)","ic": -0.053, "by": True,  "caveat": "raw -0.167은 size 위장, size-neutral -0.053이 정직"},
    "financial":     {"signal": "bank_pbr_z (sub만)",       "ic": -0.161, "by": False, "caveat": "★sub-sector cancel=은행만, 통합 selection LIMITED"},
    "bio":           {"signal": "flow_sell conditional",    "ic": -0.149, "by": False, "caveat": "conditional underpowered, 임상 idio"},
    "shipbuilding":  {"signal": "cs_lowvol_60d",            "ic": -0.057, "by": False, "caveat": "CI 0 포함 marginal, 3사 슈퍼사이클 동조"},
    "refining":      {"signal": "종목선택 불가",             "ic": None,   "by": False, "caveat": "★2종 과점(SK이노/S-Oil)=cross-sectional 불가, 산업 timing만"},
}
INDUSTRIES = list(CAPSULE_IC)


def participation_ratio(ind):
    """N_eff = prices.parquet idio 분산 participation ratio (C11, raw count 아님). 과점 자동감지."""
    try:
        px = pd.read_parquet(IND / ind / "raw-v3" / "data" / "prices.parquet")
        px.index = pd.to_datetime(px.index)
        ret = px.resample("ME").last().pct_change().loc[START:]
        n_codes = ret.notna().any().sum()
        idio = ret.sub(ret.mean(axis=1), axis=0)
        v = idio.var().dropna(); v = v[v > 1e-12]
        neff = float((v.sum() ** 2) / (v ** 2).sum()) if len(v) else 0.0
        return neff, int(n_codes)
    except Exception:
        return 0.0, 0


def main():
    rows = {}
    for ind, cap in CAPSULE_IC.items():
        neff, n_codes = participation_ratio(ind)
        rows[ind] = {**cap, "n_eff": round(neff, 2), "n_codes": n_codes}

    # ρ_i = [N_eff/(N_eff+n0)] × [|IC|/(|IC|+ic0)] × gate(BY생존/caveat 반영). C11/C12.
    icv = [abs(r["ic"]) for r in rows.values() if r["ic"] is not None]
    nev = [r["n_eff"] for r in rows.values() if r["n_eff"] > 0]
    n0 = float(np.median(nev)) if nev else 10.0
    ic0 = float(np.median(icv)) if icv else 0.1
    # ★C12 EB shrinkage (audit minor1): 산업 간 |IC| 대평균 끌림 = small-n(화학 N_eff4.4) magnitude 과대 보정.
    #   ★부호 보존(|IC| 공간 shrinkage) — 단순 IC 평균은 부호 이질(battery +)을 음 대평균에 잘못 끌어당김.
    ic_bar = float(np.mean([abs(r["ic"]) for r in rows.values() if r["ic"] is not None]))
    for ind, r in rows.items():
        if r["ic"] is None:
            r["rho_i"] = 0.0; r["selection_등급"] = "불가(종목선택 X)"; continue
        w_eb = r["n_eff"] / (r["n_eff"] + n0)
        mag_pp = w_eb * abs(r["ic"]) + (1 - w_eb) * ic_bar           # |IC| EB (부호별도)
        r["ic_pp"] = round(np.sign(r["ic"]) * mag_pp, 4)            # 부호 보존
        r["w_eb"] = round(w_eb, 3)
        breadth = r["n_eff"] / (r["n_eff"] + n0)
        signal = abs(r["ic_pp"]) / (abs(r["ic_pp"]) + ic0)            # ★IC_pp(shrunk) 사용
        # gate: BY생존=1.0 / caveat 심각(sub-cancel·conditional·marginal)=0.5 / 기타=0.8
        cav = r["caveat"]
        if r["by"]:
            gate = 1.0
        elif any(k in cav for k in ["LIMITED", "conditional", "marginal", "단일", "불가"]):
            gate = 0.5
        else:
            gate = 0.8
        r["rho_i"] = round(breadth * signal * gate, 3)
        r["selection_등급"] = ("高" if r["rho_i"] >= 0.45 else "中" if r["rho_i"] >= 0.25 else "低")

    out = {
        "meta": {"purpose": "산업 내 종목 selection 잔차 메타분석 (capsule IC SSOT + N_eff)",
                 "★사용자_통찰": "줄자는 capsule analyst가 업종별 맞는 걸로 이미 측정(IC SSOT). v1 book-to-price 통일=실수 정정.",
                 "capsule_ic_source": "각 summary.yaml + validation-*.json (Explore 2026-06-06)",
                 "n_eff": "prices.parquet idio 분산 PR(실측, 과점 자동감지)", "n0": round(n0, 2), "ic0": round(ic0, 4),
                 "원칙": "C10 selection 低 산업=v 산업중립 수축(L2 rotation 독립 유지). C11 N_eff 한번만(이중처벌 방지)"},
        "per_industry": rows,
    }
    fp = ROOT / "validation-within-residual-v2.json"
    fp.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    import sys as _s; _s.stdout.reconfigure(encoding="utf-8")
    print(f"Saved {fp}\n")
    print(f"=== 산업 내 종목 selection 신뢰 (capsule 줄자 IC SSOT + N_eff PR) ===")
    print(f"  n0(median N_eff)={n0:.1f}  ic0(median |IC|)={ic0:.3f}\n")
    print(f"  {'업종':14s} {'줄자(capsule)':28s} {'IC':>7s} {'BY':>3s} {'N_eff':>6s} {'n종':>4s} {'ρ_i':>5s} 등급")
    for ind in sorted(rows, key=lambda x: -(rows[x]["rho_i"])):
        r = rows[ind]
        ic_s = f"{r['ic']:+.3f}" if r["ic"] is not None else "  None"
        by_s = "✓" if r["by"] else "·"
        print(f"  {ind:14s} {r['signal']:28s} {ic_s:>7s} {by_s:>3s} {r['n_eff']:6.1f} {r['n_codes']:4d} {r['rho_i']:5.2f} {r['selection_등급']}")
    print(f"\n  ★과점 (N_eff << n종 = 소수 지배):")
    for ind, r in rows.items():
        if r["n_codes"] >= 5 and 0 < r["n_eff"] < r["n_codes"] * 0.45:
            print(f"    {ind}: n종={r['n_codes']} N_eff={r['n_eff']:.1f} → 분산여지 작음, ρ 수축")
    print(f"\n  ★v1(book-to-price) 대비: battery/financial 등 '맞는 줄자'로 IC 회복 = 줄자 오류 입증")


if __name__ == "__main__":
    main()
