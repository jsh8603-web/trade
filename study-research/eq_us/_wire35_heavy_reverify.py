# -*- coding: utf-8 -*-
"""_wire35_heavy_reverify.py — 자문 무거운 결함 2종 실데이터 재검증 (Gf+Gg, 2026-06-05).

자문(3R) 지적 중 무거운 시뮬 필요분 2개를 background 로 측정:
  Gf [최대결함] horizon mismatch: 신호 12M forward 검증 ↔ 월간 rebal+no-trade band 정책 미검증.
       → 월간 정책(1M excess 누적) vs 12M signal excess 괴리 실측 + block-bootstrap CI.
  Gg trap-veto selection bias: veto 가 value 와 상관(싼 종목이 trap 잘 걸림) → 좌측꼬리 제거 →
       value alpha 잠식. full top-K excess vs post-veto(최상위 cheapness 제거) excess Δ 실측.

cyclical 60종 데이터(pbr/ev value CONFIRMED). 합성 0 = 실 prices/EDGAR PIT, go-live 무접촉.
재현: python _wire35_heavy_reverify.py > _wire35_heavy_results.txt 2>&1
"""
import sys
import numpy as np
import pandas as pd

INV = "D:/projects/Inv"
CYC = INV + "/study-research/eq_us/industries/us_cyclical/raw-v3"
sys.path.insert(0, INV)
sys.path.insert(0, CYC)

import measure as M
from stock.cross_sectional_selection import select_cross_sectional, SelectionConfig

H = 12
TOP_K = 10
EXIT_K = 30
SIGNS = {"pbr": -1, "ev_ebitda": -1}


def _panel(P, *names):
    for n in names:
        if n in P:
            return P[n]
    raise KeyError(f"none of {names} in panel keys={list(P)[:10]}")


def block_boot_ci(x, n_boot=2000, block=6, seed=12345):
    x = np.asarray([v for v in x if v == v])
    L = len(x)
    if L < 4:
        return (np.nan, np.nan)
    rng = np.random.RandomState(seed)
    nb = int(np.ceil(L / block))
    means = []
    for _ in range(n_boot):
        idx = []
        for _ in range(nb):
            s = rng.randint(0, L)
            idx.extend((s + k) % L for k in range(block))
        means.append(np.mean(x[idx[:L]]))
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def main():
    px, ed, uni, macro = M.load()
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    P = M.build_pit_panels(px, ed)
    pbr = _panel(P, "pbr", "pbr_z", "cs_pbr_z")
    ev = _panel(P, "ev_ebitda", "ev", "cs_ev_ebitda")
    pxm = px.resample("ME").last()
    fwd12 = pxm.shift(-H) / pxm - 1.0
    fwd1 = pxm.shift(-1) / pxm - 1.0
    idx = pbr.index.intersection(fwd1.index)

    print("=" * 76)
    print("[Gf — horizon mismatch] 월간 rebal+no-trade band 정책(1M) vs 12M signal")
    cfg = SelectionConfig(top_k=TOP_K, top_k_exit=EXIT_K, market_cap_floor=0.0)
    held = {}
    pol1, sig12 = [], []
    for dt in idx:
        pv = pbr.loc[dt].dropna(); evv = ev.loc[dt].dropna()
        tk = sorted(set(pv.index) | set(evv.index))
        r1 = fwd1.loc[dt].dropna() if dt in fwd1.index else pd.Series(dtype=float)
        if len(set(tk) & set(r1.index)) < 2 * TOP_K:
            held = {}
            continue
        panel = {"pbr": {t: pv.get(t) for t in tk}, "ev_ebitda": {t: evv.get(t) for t in tk}}
        caps = {t: 1e9 for t in tk}
        cands = select_cross_sectional(panel, caps, SIGNS, sectors=secmap, config=cfg,
                                       held_ranks=held or None)
        picks = [c.ticker for c in cands if c.target_weight > 0 and c.ticker in r1.index]
        held = {c.ticker: c.rank for c in cands if c.target_weight > 0}
        if picks:
            pol1.append(float(r1.loc[picks].mean() - r1.mean()))
        if dt in fwd12.index:
            r12 = fwd12.loc[dt].dropna()
            p12 = [t for t in picks if t in r12.index]
            if p12:
                sig12.append(float(r12.loc[p12].mean() - r12.mean()))
    ci1 = block_boot_ci(pol1)
    print(f"  월간 정책 1M excess = {np.mean(pol1)*100:+.3f}%/월 (연율 {np.mean(pol1)*1200:+.2f}%), n={len(pol1)}")
    print(f"    block-boot 95%CI(block6) = [{ci1[0]*100:+.3f}, {ci1[1]*100:+.3f}]%/월"
          f"  {'(0 포함=비유의)' if ci1[0] < 0 < ci1[1] else '(0 불포함)'}")
    print(f"  12M signal excess = {np.mean(sig12)*100:+.3f}%/12M, n={len(sig12)}")
    print(f"  → 괴리: 월간 연율 {np.mean(pol1)*1200:+.1f}% vs 12M {np.mean(sig12)*100:+.1f}% "
          f"= traded(월간) {'≈' if abs(np.mean(pol1)*1200 - np.mean(sig12)*100) < 1 else '≠'} validated(12M)")

    print("=" * 76)
    print("[Gg — trap-veto bias] full top-K vs post-veto(최상위 cheapness 5% 제거) value excess")
    full_exc, veto_exc = [], []
    for dt in idx:
        pv = pbr.loc[dt].dropna(); evv = ev.loc[dt].dropna()
        tk = sorted(set(pv.index) | set(evv.index))
        if dt not in fwd12.index:
            continue
        r = fwd12.loc[dt].dropna()
        c = [t for t in tk if t in r.index]
        if len(c) < 3 * TOP_K:
            continue
        panel = {"pbr": {t: pv.get(t) for t in c}, "ev_ebitda": {t: evv.get(t) for t in c}}
        caps = {t: 1e9 for t in c}
        cands = select_cross_sectional(panel, caps, SIGNS, sectors=secmap,
                                       config=SelectionConfig(top_k=TOP_K, market_cap_floor=0.0))
        ranked = [cc.ticker for cc in cands if cc.ticker in r.index]   # cheapness 내림차순
        if len(ranked) < 3 * TOP_K:
            continue
        full_exc.append(float(r.loc[ranked[:TOP_K]].mean() - r.mean()))
        n_veto = max(1, int(0.05 * len(ranked)))
        post = ranked[n_veto:]                                         # 최상위(가장 싼) 제거 가정
        veto_exc.append(float(r.loc[post[:TOP_K]].mean() - r.mean()))
    dfull, dveto = np.mean(full_exc), np.mean(veto_exc)
    print(f"  full top-K excess     = {dfull*100:+.3f}%/12M, n={len(full_exc)}")
    print(f"  post-veto top-K excess= {dveto*100:+.3f}%/12M")
    print(f"  Δ(veto−full) = {(dveto-dfull)*100:+.3f}pp "
          f"→ {'★value alpha 잠식(좌측꼬리=싼 종목 제거 손실)' if dveto < dfull else 'veto 무해/개선(trap 제거가 이득)'}")
    print("=" * 76)
    print("[종합] Gf horizon mismatch = 월간/12M 괴리 크면 정책 재설계 / Gg = Δ<0 이면 post-veto IC 재측정 의무")


if __name__ == "__main__":
    main()
