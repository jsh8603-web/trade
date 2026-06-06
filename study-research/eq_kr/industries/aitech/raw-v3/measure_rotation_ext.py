# -*- coding: utf-8 -*-
"""measure_rotation_ext.py — ★AItech rotation 후보 ≥13개 전수 검증 (team-lead 재보강).

measure_rotation.py 의 통계 인프라 재사용. cycle_aitech_ext.parquet(10종) + 파생 3종 = 13 후보 전수.
파이프라인: 이론(부호 사전확약) → forward 20d/60d IC + OOS + wild-cluster → 채택판정(data-mining 차단).

================================================================================
★부호 사전확약 (데이터 접촉 前 동결 = PIT pre-commit, ≥13 후보):
  [기존 4]
  rate_10y     음 (growth long-duration: 금리↑→멀티플 압축) ★primary
  nasdaq_qqq   양 (글로벌 tech cycle 동조)
  ai_capex_nvda 양 (AI capex/GPU 수요)
  soxx_semi    양 (반도체 cycle 연동)
  [신규 6]
  hyperscaler_capex 양 (MSFT/GOOGL/AMZN 클라우드 capex = SaaS 수혜)
  power_demand_xlu  양 (AI 데이터센터 전력수요 = 유틸리티 = AI 인프라 cycle 확장)
  global_sw_igv     양 (글로벌 SW ETF = SaaS 업황)
  game_espo         양 (글로벌 게임 ETF = 게임 신작 cycle / 글로벌 흥행)
  vix               음 (growth 고베타: risk-off VIX↑→AItech 약세)
  cloud_skyy        양 (클라우드 인프라 cycle)
  [파생 3]
  soxx_qqq_spread   양 (SOXX/QQQ 반도체 상대강도 = tech 위험선호 risk-on)
  usdkrw            양 (원화약세→수출 SW/게임[크래프톤·펄어비스] 환산매출↑)
  rel_mom_kr        음 (AItech 업종 자체 모멘텀 reversal = 종목selection reversal 정합)
================================================================================
★좀비 마스킹(셀바스AI 284일 halt) + 공통인자 residualize + OOS(2023 split) + wild-cluster B=2000.
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
from measure_rotation import (
    nw_se, n_eff_autocorr, wild_cluster_p, block_boot_ci, benjamini_yekutieli,
    signal_forward_stat, zombie_mask,
)

HORIZONS_M = {"y_20d": 1, "y_60d": 3}
SEMI_PPI_LAG = 1

PRIOR_SIGN = {
    "rate_10y": "음", "nasdaq_qqq": "양", "ai_capex_nvda": "양", "soxx_semi": "양",
    "hyperscaler_capex": "양", "power_demand_xlu": "양", "global_sw_igv": "양",
    "game_espo": "양", "vix": "음", "cloud_skyy": "양",
    "soxx_qqq_spread": "양", "usdkrw": "양", "rel_mom_kr": "음",
}
# 신호 변형: 금리/vix = level diff (Δ), 나머지 = pct_change (모멘텀). spread/usdkrw = ratio/level.
DIFF_SIGNALS = {"rate_10y", "vix"}   # level Δ 가 본질 (yield/지수)


def transform(base: pd.Series, col: str, kind: str):
    """kind = d3(3M) / yoy(12M). 금리·VIX = diff, 나머지 = pct_change."""
    if col in DIFF_SIGNALS:
        return base.diff(3) if kind == "d3" else base.diff(12)
    return base.pct_change(3) if kind == "d3" else base.pct_change(12)


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    amt = pd.read_parquet(DATA / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    rs = pd.read_parquet(DATA / "regime_series.parquet"); rs.index = pd.to_datetime(rs.index)
    cyc = pd.read_parquet(DATA / "cycle_aitech_ext.parquet"); cyc.index = pd.to_datetime(cyc.index)

    # 좀비 마스킹 업종 eq-weight 월수익
    px_clean = zombie_mask(px, amt)
    pret = px_clean.resample("ME").last().pct_change().mean(axis=1, skipna=True).loc["2019-01-01":]
    cum = (1 + pret.fillna(0)).cumprod()

    rsm = rs.resample("ME").last()
    cycm = cyc.resample("ME").last()

    # ── 파생 신호 ──
    # soxx_qqq_spread = SOXX/QQQ ratio (반도체 상대강도)
    cycm = cycm.copy()
    cycm["soxx_qqq_spread"] = cycm["soxx_semi"] / cycm["nasdaq_qqq"]
    # usdkrw = regime_series (월말)
    cycm["usdkrw"] = rsm["usdkrw"].reindex(cycm.index)
    # rel_mom_kr = AItech 업종 자체 누적수익 (업종 모멘텀 = cum)
    cycm["rel_mom_kr"] = cum.reindex(cycm.index)

    results = {"meta": {
        "industry": "aitech",
        "method": "★rotation 후보 ≥13개 전수 검증 (team-lead 재보강). 업종 eq-weight(좀비 마스킹) forward IC + OOS + wild-cluster.",
        "n_candidates": len(PRIOR_SIGN),
        "prior_signs": PRIOR_SIGN,
        "transform": "금리/VIX = level Δ3/Δ12, 나머지 = pct_change 3M/12M. spread=ratio, usdkrw=level Δ, rel_mom_kr=업종 cum Δ",
        "zombie_mask": "셀바스AI 284일 halt NaN",
        "oos_split": "2023-01-01", "t_breakeven": 2.802, "n_months": int(pret.dropna().shape[0]),
    }, "candidates": {}}
    fdr_all = {}

    for col in PRIOR_SIGN.keys():
        if col not in cycm.columns:
            results["candidates"][col] = {"status": "DATA_MISSING"}
            continue
        prior = PRIOR_SIGN[col]
        base = cycm[col]
        results["candidates"][col] = {"prior_sign": prior, "signals": {}}
        for kind in ["d3", "yoy"]:
            sig = transform(base, col, kind).loc["2019-01-01":]
            for hl, hm in HORIZONS_M.items():
                fwd = cum.pct_change(hm).shift(-hm)
                st = signal_forward_stat(sig, fwd, hm, f"aitech__{col}_{kind}__{hl}", prior=prior)
                results["candidates"][col]["signals"][f"{kind}__{hl}"] = st
                if st.get("status") in ("powered", "underpowered") and st.get("wild_cluster_p") is not None:
                    fdr_all[f"{col}_{kind}__{hl}"] = st["wild_cluster_p"]

    results["fdr_all_single"] = benjamini_yekutieli(fdr_all)

    # ── 후보별 best 판정 요약 ──
    summary = {}
    for col, cd in results["candidates"].items():
        if "signals" not in cd:
            summary[col] = {"verdict": cd.get("status", "?")}; continue
        # best = OOS eligible + 부호 일치 + wc_p 최소
        best = None
        for sk, st in cd["signals"].items():
            if "spearman_rho" not in st: continue
            oos = st.get("walk_forward_oos", {})
            score = (1 if (st.get("prior_match") and oos.get("eligible")) else 0,
                     -(st.get("wild_cluster_p") or 1.0))
            if best is None or score > best[0]:
                best = (score, sk, st)
        if best is None:
            summary[col] = {"verdict": "INSUFFICIENT"}; continue
        _, sk, st = best
        oos = st.get("walk_forward_oos", {})
        match = st.get("prior_match"); wcp = st.get("wild_cluster_p")
        if match and oos.get("eligible") and wcp is not None and wcp < 0.10:
            v = "★TENTATIVE채택 (이론+통계 부호일치+OOS+wc_p<0.10, underpowered)"
        elif match and oos.get("eligible"):
            v = "약-TENTATIVE (부호일치+OOS but wc_p>0.10)"
        elif match is False and oos.get("verdict", "").startswith("OOS flip"):
            v = "★REJECTED (부호 사전확약 반증 + OOS flip)"
        elif match is False:
            v = "REJECTED (부호 반증)"
        else:
            v = "data-mining/무신호 (부호일치 약 or OOS flip)"
        summary[col] = {"best_signal": sk, "rho": st["spearman_rho"], "prior": st.get("prior_sign"),
                        "obs": st.get("obs_sign"), "wc_p": wcp, "oos": oos.get("verdict"), "verdict": v}
    results["candidate_verdict_summary"] = summary

    out = ROOT / "validation-rotation-ext-v1.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Saved {out}\n")
    print(f"{'='*92}\n★AItech rotation 후보 {len(PRIOR_SIGN)}개 전수 검증 (best signal per candidate)\n{'='*92}")
    for col, sm in summary.items():
        if "rho" not in sm:
            print(f"  {col:18s} {sm['verdict']}"); continue
        print(f"  {col:18s} [{sm['best_signal']:9s}] rho={sm['rho']:+.3f}({sm['obs']}/{sm['prior']}) wc_p={sm['wc_p']} OOS:{sm['oos']} → {sm['verdict']}")
    print(f"\nFDR all single: {json.dumps(results['fdr_all_single'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
