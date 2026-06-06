# -*- coding: utf-8 -*-
"""_wire3_selection_sim.py — WIRE3 selection 실데이터 정합 시뮬 (2026-06-04).

목적: stock/cross_sectional_selection.select_cross_sectional 의 top-K 픽이
measure.py 가 입증한 IC (cyclical PBR/EV value) 와 정합하는지 1회 실데이터 시뮬.

검증 2축:
  (1) selection top-K(매수) forward 12M return − bottom 평균 = long-short spread > 0
      (= "싼 게 forward↑" measure IC 부호와 정합하는가)
  (2) demean 레벨 A(sector-neutral, measure 기준) vs B(sleeve-level, 현 selection 모듈)
      → measure 가 "multi-sector = sector-neutral 필수, universe-demean = 신호 희석 버그" 박음.
        selection 은 sleeve-level robust z 만 → 정합 갭인지 spread 차이로 확인.

variant 4:
  A  sector-neutral + std z      (measure 그대로)
  B  sleeve-level  + robust z     (현 cross_sectional_selection.select_cross_sectional)
  C  sector-neutral + robust z    (selection 에 sector-neutral 옵션 넣었을 때)
  Bz sleeve-level  + std z        (demean 레벨만 분리 측정)

재현: python _wire3_selection_sim.py  (합성 0 = 실 prices/edgar PIT, go-live 무접촉)
"""
import sys
import numpy as np
import pandas as pd
from scipy import stats

INV = "D:/projects/Inv"
CYC = INV + "/study-research/eq_us/industries/us_cyclical/raw-v3"
sys.path.insert(0, INV)
sys.path.insert(0, CYC)

import measure as M
from stock.cross_sectional_selection import (
    select_cross_sectional, SelectionConfig,
)

H = 12       # forward horizon (월)
TOP_K = 10   # 매수 후보 (selection default)


def monthly_long_short(cheap_df: pd.DataFrame, fwd: pd.DataFrame, k: int = TOP_K):
    """매월 cheapness 상위 k(매수) forward 평균 − 하위 k(매도) forward 평균 = spread.
    cheap_df: 높을수록 쌈. 반환 (spread 시계열, top-k 종목별 excess-vs-universe 시계열 평균)."""
    idx = cheap_df.index.intersection(fwd.index)
    spreads, topexc = [], []
    for dt in idx:
        cv = cheap_df.loc[dt].dropna()
        rv = fwd.loc[dt].dropna()
        c = cv.index.intersection(rv.index)
        if len(c) < 2 * k:
            continue
        cv, rv = cv.loc[c], rv.loc[c]
        ranked = cv.sort_values(ascending=False)
        top = ranked.index[:k]
        bot = ranked.index[-k:]
        spreads.append(rv.loc[top].mean() - rv.loc[bot].mean())
        topexc.append(rv.loc[top].mean() - rv.mean())
    s = pd.Series(spreads)
    return s, pd.Series(topexc)


def robust_z_df(panel: pd.DataFrame, secmap=None) -> pd.DataFrame:
    """median/MAD robust z. secmap 주입 시 sector 내에서 robust demean (= variant C)."""
    def _rz(sub: pd.DataFrame) -> pd.DataFrame:
        med = sub.median(axis=1)
        mad = (sub.sub(med, axis=0)).abs().median(axis=1)
        scale = 1.4826 * mad
        return sub.sub(med, axis=0).div(scale.replace(0, np.nan), axis=0)
    if secmap is None:
        return _rz(panel)
    out = panel.copy() * np.nan
    secs = {}
    for t in panel.columns:
        secs.setdefault(secmap.get(t, "_"), []).append(t)
    for _, cols in secs.items():
        out[cols] = _rz(panel[cols])
    return out


def main():
    px, ed, uni, macro = M.load()
    secmap = M.sector_map()
    P = M.build_pit_panels(px, ed)
    pxm = px.resample("ME").last()
    fwd = pxm.shift(-H) / pxm - 1.0

    pbr, ev = P["pbr"], P["ev_ebitda"]

    # ── measure 입증 IC (sector-neutral std z, cheapness 부호 미적용 raw) ──
    pbr_z = M.cs_z(pbr, secmap)
    ev_z = M.cs_z(ev, secmap)
    ic_pbr, _ = M.cs_ic(pbr_z, fwd)
    ic_ev, _ = M.cs_ic(ev_z, fwd)
    print("=" * 72)
    print("[measure 입증 IC] (sector-neutral std z, raw 부호 = z 클수록 forward 방향)")
    print(f"  pbr_z       IC mean = {ic_pbr.mean():+.4f}  (음 = pbr 높을수록 forward↓ = value 정합), n_mo={len(ic_pbr)}")
    print(f"  ev_ebitda_z IC mean = {ic_ev.mean():+.4f}  (음 = ev 높을수록 forward↓ = value 정합), n_mo={len(ic_ev)}")

    # ── cheapness composite (높을수록 쌈) 4 variant ──
    # A sector-neutral std:  -(pbr_z + ev_z)/2  (measure z 의 cheapness 부호)
    A = -(pbr_z.add(ev_z)) / 2.0
    # Bz sleeve-level std:  M.cs_z(panel, None) = universe demean std
    pbr_zs, ev_zs = M.cs_z(pbr, None), M.cs_z(ev, None)
    Bz = -(pbr_zs.add(ev_zs)) / 2.0
    # B sleeve-level robust (현 selection 모듈과 동일 z)
    pbr_rz, ev_rz = robust_z_df(pbr, None), robust_z_df(ev, None)
    B = -(pbr_rz.add(ev_rz)) / 2.0
    # C sector-neutral robust
    pbr_rzs, ev_rzs = robust_z_df(pbr, secmap), robust_z_df(ev, secmap)
    C = -(pbr_rzs.add(ev_rzs)) / 2.0

    print("=" * 72)
    print(f"[long-short spread] top{TOP_K} 매수 − bottom{TOP_K} 매도, forward {H}M, 월별 평균 + NW t")
    rows = []
    for name, cheap in [("A sector-neutral·std (measure)", A),
                        ("Bz sleeve·std            ", Bz),
                        ("B  sleeve·robust (현 selection)", B),
                        ("C  sector-neutral·robust  ", C)]:
        sp, ex = monthly_long_short(cheap, fwd)
        ic_l = M.nw_se(sp, lags=H) if len(sp) > 3 else np.nan
        t = sp.mean() / ic_l if (ic_l and not np.isnan(ic_l)) else np.nan
        rows.append((name, sp.mean(), t, ex.mean(), len(sp)))
        print(f"  {name:34s} spread={sp.mean():+.4f}  NW_t={t:+.2f}  top_excess={ex.mean():+.4f}  n_mo={len(sp)}")

    # ── selection 모듈 직접 호출: off(byte-identical)=B / on=sector-neutral=C 회복 ──
    print("=" * 72)
    print(f"[selection 모듈 직접 호출] off(sleeve)=B 정합 / on(sector-neutral)=C 회복 검증")
    idx = pbr.index.intersection(fwd.index)

    def run_module(demean_by_sector: bool):
        cfg = SelectionConfig(top_k=TOP_K, market_cap_floor=0.0,
                              demean_by_sector=demean_by_sector, min_sector_n=8)
        exc, ns, ovl = [], [], []
        ref = C if demean_by_sector else B
        for dt in idx:
            pv = pbr.loc[dt].dropna(); evv = ev.loc[dt].dropna()
            tk = sorted(set(pv.index) | set(evv.index))
            rv = fwd.loc[dt].dropna()
            if len(set(tk) & set(rv.index)) < 2 * TOP_K:
                continue
            panel = {"pbr": {t: pv.get(t) for t in tk}, "ev_ebitda": {t: evv.get(t) for t in tk}}
            caps = {t: 1e9 for t in tk}
            cands = select_cross_sectional(
                panel, caps, {"pbr": -1, "ev_ebitda": -1}, sectors=secmap, config=cfg,
            )
            picks = [c.ticker for c in cands if c.target_weight > 0 and c.ticker in rv.index]
            if not picks:
                continue
            exc.append(rv.loc[picks].mean() - rv.mean()); ns.append(len(picks))
            rc = ref.loc[dt].dropna(); rci = rc.index.intersection(rv.index)
            rtop = set(rc.loc[rci].sort_values(ascending=False).index[:TOP_K])
            ovl.append(len(set(picks) & rtop) / max(len(picks), 1))
        return pd.Series(exc), np.mean(ns), np.mean(ovl)

    me_off, n_off, ov_off = run_module(False)
    me_on, n_on, ov_on = run_module(True)
    print(f"  off(sleeve robust) : excess={me_off.mean():+.4f}  n_mo={len(me_off)}  ∩B top{TOP_K}={ov_off:.0%}  avg_picks={n_off:.1f}")
    print(f"  on (sector-neutral): excess={me_on.mean():+.4f}  n_mo={len(me_on)}  ∩C top{TOP_K}={ov_on:.0%}  avg_picks={n_on:.1f}")
    print(f"  → on−off excess 상승 = {me_on.mean()-me_off.mean():+.4f} (sector-neutral 신호 보존 효과)")

    print("=" * 72)
    print("[해석 가이드]")
    print("  · A spread 가 B/Bz 보다 유의 높으면 → sector-neutral 이 sleeve-level 보다 신호 보존 (measure 주장 실증)")
    print("  · module excess > 0 + measure IC 음(value) → selection top-K 가 입증 IC 와 부호 정합")
    print("  · module ∩ B overlap ≈ 100% → 모듈 z 경로(sleeve robust) 가 B variant 와 일치 (구현 sanity)")


if __name__ == "__main__":
    main()
