# -*- coding: utf-8 -*-
"""_wire35_gfc_overlap_reverify.py — Gf-C (12-vintage overlap) 자문 재검증 (advisory-protocol).

자문 R1 수렴(2026-06-05, Claude+Gemini 만장일치): Gf horizon mismatch 해소책 = (C) 12-vintage
  overlapping portfolio. 근거(자문=reference): 매월 1/12 트랜치가 12M 보유 → 실효 horizon=12M 정합,
  turnover 1/12, no-trade band·MA window 같은 점추정 파라미터 불필요.
본인 verification(의무): overlap 정책의 실현 1M excess(연율) 가 검증된 12M signal(+6.687%/12M)에
  수렴하는지 + block-boot CI 0 불포함 회복하는지 실측. null(여전히 비유의)도 정직 보고 → 자문 기각.

baseline(_wire35_heavy_results.txt):
  월간 full-rebal+band(exit_K=30) = +0.365%/월(연율 +4.38%) CI[-0.001,+0.757] = 0포함 비유의, n=136.
  12M signal excess = +6.687%/12M, n=125.

cyclical 실데이터(pbr/ev value CONFIRMED), 합성 0 = 실 prices/EDGAR PIT, go-live 무접촉.
재현: python _wire35_gfc_overlap_reverify.py > _wire35_gfc_overlap_results.txt 2>&1
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
N_VINT = 12   # 12-vintage overlap (매월 1/12 트랜치, 12M 보유)


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
    fwd1 = pxm.shift(-1) / pxm - 1.0
    idx = pbr.index.intersection(fwd1.index)

    cfg = SelectionConfig(top_k=TOP_K, top_k_exit=EXIT_K, market_cap_floor=0.0)

    print("=" * 76)
    print(f"[Gf-C — {N_VINT}-vintage overlap] 매월 1/{N_VINT} 트랜치 12M 보유 vs 12M signal")
    print(f"  자문 권고(reference) = (C) overlap. 본인 verification = 실현 excess 가 12M 회복?")

    vintages = []        # [(entry_dt, picks)] — 최근 N_VINT 만 유지
    overlap_exc = []     # overlap 1M excess (활성 빈티지 동일비중)
    single_exc = []      # 동일 selection 의 단일-빈티지 1M (turnover 비교 sanity)
    turnovers = []
    prev_holdings = set()
    for dt in idx:
        pv = pbr.loc[dt].dropna(); evv = ev.loc[dt].dropna()
        tk = sorted(set(pv.index) | set(evv.index))
        r1 = fwd1.loc[dt].dropna() if dt in fwd1.index else pd.Series(dtype=float)
        if len(set(tk) & set(r1.index)) < 2 * TOP_K:
            continue
        panel = {"pbr": {t: pv.get(t) for t in tk}, "ev_ebitda": {t: evv.get(t) for t in tk}}
        caps = {t: 1e9 for t in tk}
        cands = select_cross_sectional(panel, caps, SIGNS, sectors=secmap, config=cfg)
        picks = [c.ticker for c in cands if c.target_weight > 0]
        # 새 빈티지 진입 + 12M 초과 청산 (월간 index = 최근 N_VINT 개 유지)
        vintages.append((dt, picks))
        vintages = vintages[-N_VINT:]
        # 활성 빈티지 다음 1M 수익 (동일 1/n 비중)
        vint_rets = []
        cur_holdings = set()
        for (_m, p) in vintages:
            pp = [t for t in p if t in r1.index]
            if pp:
                vint_rets.append(float(r1.loc[pp].mean()))
                cur_holdings.update(pp)
        if vint_rets:
            overlap_exc.append(float(np.mean(vint_rets) - r1.mean()))
            new_pp = [t for t in picks if t in r1.index]
            if new_pp:
                single_exc.append(float(r1.loc[new_pp].mean() - r1.mean()))
            if prev_holdings:
                churn = len(cur_holdings ^ prev_holdings) / max(1, len(cur_holdings | prev_holdings))
                turnovers.append(churn)
            prev_holdings = cur_holdings

    ci = block_boot_ci(overlap_exc)
    ann = np.mean(overlap_exc) * 1200
    sig = (ci[0] > 0) if (ci[0] == ci[0]) else False
    print(f"  overlap 1M excess = {np.mean(overlap_exc)*100:+.3f}%/월 (연율 {ann:+.2f}%), n={len(overlap_exc)}")
    print(f"    block-boot 95%CI(block6) = [{ci[0]*100:+.3f}, {ci[1]*100:+.3f}]%/월"
          f"  {'★(0 불포함=유의)' if sig else '(0 포함=비유의)'}")
    print(f"  단일-빈티지(reference) 1M excess = {np.mean(single_exc)*100:+.3f}%/월 (연율 {np.mean(single_exc)*1200:+.2f}%)")
    print(f"  overlap 평균 turnover = {np.mean(turnovers)*100:.1f}%/월")
    print(f"  ── baseline(기존 결과) ──")
    print(f"  월간 full-rebal+band = +4.38%/yr CI[-0.001,+0.757] 비유의")
    print(f"  12M signal           = +6.687%/12M")
    gap = abs(ann - 6.687)
    verdict = ("★수렴+유의 (horizon mismatch 해소, Gf-C 적용 타당)"
               if (gap < 2.5 and sig)
               else ("부분(연율 회복하나 CI 0포함=power부족, TENTATIVE)" if gap < 2.5
                     else "미수렴 (자문 기각 가능, null result)"))
    print(f"  → overlap 연율 vs 12M 괴리 {gap:.2f}pp / 유의={sig} → {verdict}")
    print("=" * 76)
    print("[advisory-protocol] 자문=reference(overlap 권고). 위 = 본인 정량 verification + null.")


if __name__ == "__main__":
    main()
