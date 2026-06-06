# -*- coding: utf-8 -*-
"""within_industry_residual_us.py — 미국 eq_us sleeve 종목 selection 변별력 등급 (한국 within v2 패턴 이식).

★Phase 0-2 (ETF fallback plan, 2026-06-06): 미국 eq_us 3 sleeve 의 measured selection IC(summary.yaml SSOT)를
한국 within_industry_residual_kr.py 패턴(measured IC SSOT + N_eff PR + ρ_i 등급)으로 등급화.
약변별(低/불가) sleeve = ETF fallback 후보 식별. ⛔ 새 cross-sectional 측정 X (summary.yaml SSOT).

★한미 비대칭(핸드오프 §6): 미국 = sleeve 3개(cyclical 大N cross-sectional 작동 / defensive 약 / mega_tech void basket).
  한국 = 12 산업 granular. ★미국 sleeve = multi-sector pooled(cyclical 5 sector) = 측정단위 한국 산업과 다름(caveat 박제).
★EB 메타 생략: 미국 3 sleeve = DerSimonian-Laird τ² between-group var 부적합(n=3). raw |IC| breadth×signal×gate.
  n0/ic0 = 한국 within v2 JSON 차용(한미 공통 척도, prior 풍부). gate = measured verdict 직접 박제(3 sleeve, 정직).
⛔ production 무접촉. 산출 = validation-within-residual-us-v1.json.
"""
from __future__ import annotations
import json
from pathlib import Path
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent            # eq_us/industries/_rotation
US_IND = ROOT.parent                              # eq_us/industries
KR_JSON = US_IND.parent.parent / "eq_kr" / "industries" / "_rotation" / "validation-within-residual-v2.json"

# ★미국 measured selection IC (summary.yaml SSOT, Phase 0-2 추출 2026-06-06).
#   gate = measured selection verdict 직접 박제 (CONFIRMED 1.0 / PARTIAL-marginal 0.6 / void None).
CAPSULE_IC_US = {
    "us_cyclical": {
        "signal": "cs_pbr_z 12M(+ev_ebitda)", "ic": -0.117, "by": True, "gate": 1.0, "start": "2015-01-01",
        "caveat": "CONFIRMED — PBR/EV-EBITDA value premium sector-neutral BY8생존+전robustness. 大N 60종(5섹터) cross-sectional 작동. ev_ebitda -0.110 병행. survivorship(현 holdings) PARTIAL. = selection 강변별, ETF fallback 불필요 경향"},
    "us_defensive": {
        "signal": "cs_net_issuance 12M", "ic": +0.082, "by": True, "gate": 0.6, "start": "2010-01-01",
        "caveat": "PARTIAL marginal — net_issuance 단일FDR BY생존(raw_p 3e-05) but incremental only(⊥ep t3.71/⊥payout t2.41). 부호 양=Pontiff-Woodgate 문헌반대. ep_yield anti-value TENTATIVE 동반. value/quality/payout 모두 약/역방향(BY 0). OOS·cross-market 미검 = 약변별 ETF fallback 후보"},
    "us_mega_tech": {
        "signal": "cross-sectional void", "ic": None, "by": False, "gate": None, "start": "2015-01-01",
        "caveat": "종목선택 불가 — exposure_timing_overlay(verdict 폐기). 유효 cross-section n≈8 통계적 void. 11종 custom basket 자체보유=fallback 동형(한국 refining 과점 대응). PER expensive_trap null. real_rate duration overlay 본질"},
}
SLEEVES = list(CAPSULE_IC_US)


def participation_ratio(sleeve, start):
    """N_eff = prices.parquet idio 분산 participation ratio (한국 패턴 동일, 과점 자동감지)."""
    try:
        px = pd.read_parquet(US_IND / sleeve / "raw-v3" / "data" / "prices.parquet")
        px.index = pd.to_datetime(px.index)
        ret = px.resample("ME").last().pct_change().loc[start:]
        n_codes = int(ret.notna().any().sum())
        idio = ret.sub(ret.mean(axis=1), axis=0)
        v = idio.var().dropna(); v = v[v > 1e-12]
        neff = float((v.sum() ** 2) / (v ** 2).sum()) if len(v) else 0.0
        return round(neff, 2), n_codes
    except Exception as e:
        return 0.0, 0


def main():
    # 한미 공통 척도 = 한국 within v2 n0/ic0 차용 (prior 풍부)
    kr = json.loads(KR_JSON.read_text(encoding="utf-8"))
    n0 = float(kr["meta"]["n0"]); ic0 = float(kr["meta"]["ic0"])

    rows = {}
    for sl, cap in CAPSULE_IC_US.items():
        neff, n_codes = participation_ratio(sl, cap["start"])
        r = {**cap, "n_eff": neff, "n_codes": n_codes}
        if r["ic"] is None:
            r["rho_i"] = 0.0; r["selection_등급"] = "불가(종목선택 X = basket)"
        else:
            breadth = r["n_eff"] / (r["n_eff"] + n0)          # 과점 수축
            signal = abs(r["ic"]) / (abs(r["ic"]) + ic0)      # |IC| 크기 (EB shrink 생략, raw)
            r["rho_i"] = round(breadth * signal * r["gate"], 3)
            r["selection_등급"] = ("高" if r["rho_i"] >= 0.45 else "中" if r["rho_i"] >= 0.25 else "低")
            r["_breadth"] = round(breadth, 3); r["_signal"] = round(signal, 3)
        rows[sl] = r

    out = {
        "meta": {
            "purpose": "미국 eq_us sleeve 종목 selection 변별력 등급 (Phase 0-2, ETF fallback 후보 식별)",
            "★패턴": "한국 within_industry_residual_kr.py 이식 (measured IC SSOT + N_eff PR + ρ_i). 새 측정 X.",
            "capsule_ic_source": "각 sleeve summary.yaml (재작업 v3, sector-neutral). 추출 2026-06-06.",
            "★EB_생략": "미국 3 sleeve = τ² between-group var 부적합. raw |IC| 사용. gate=measured verdict 직접.",
            "n0_ic0_차용": f"한국 within v2 (n0={n0}, ic0={ic0}) = 한미 공통 척도.",
            "★한미_비대칭": "미국 sleeve=multi-sector pooled(cyclical 5섹터) = 측정단위 한국 산업과 다름. 미국 종목 多→cyclical cross-sectional 작동.",
            "등급_임계": "高≥0.45 / 中≥0.25 / 低<0.25 (한국 동일). 低·불가 = ETF fallback 후보.",
        },
        "per_sleeve": rows,
    }
    fp = ROOT / "validation-within-residual-us-v1.json"
    fp.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    import sys as _s; _s.stdout.reconfigure(encoding="utf-8")
    print(f"Saved {fp}\n")
    print(f"=== 미국 eq_us sleeve 종목 selection 변별력 (measured IC SSOT + N_eff PR) ===")
    print(f"  n0={n0:.2f} ic0={ic0:.3f} (한미 공통 척도, 한국 within v2 차용)\n")
    print(f"  {'sleeve':14s} {'signal':22s} {'IC':>7s} {'BY':>3s} {'N_eff':>6s} {'n종':>4s} {'ρ_i':>5s} 등급")
    for sl in sorted(rows, key=lambda x: -(rows[x]["rho_i"])):
        r = rows[sl]
        ic_s = f"{r['ic']:+.3f}" if r["ic"] is not None else "  None"
        by_s = "✓" if r["by"] else "·"
        print(f"  {sl:14s} {r['signal']:22s} {ic_s:>7s} {by_s:>3s} {r['n_eff']:6.1f} {r['n_codes']:4d} {r['rho_i']:5.2f} {r['selection_등급']}")
    print(f"\n  ★ETF fallback 후보 (低/불가):")
    for sl, r in rows.items():
        if r["selection_등급"].startswith(("低", "불가")):
            print(f"    {sl}: ρ={r['rho_i']:.3f} {r['selection_등급']} — {r['caveat'][:60]}")
    print(f"\n  ★강변별(中↑) = fallback 불필요 경향:")
    for sl, r in rows.items():
        if r["selection_등급"] in ("高", "中"):
            print(f"    {sl}: ρ={r['rho_i']:.3f} {r['selection_등급']} (cross-sectional 작동)")


if __name__ == "__main__":
    main()
