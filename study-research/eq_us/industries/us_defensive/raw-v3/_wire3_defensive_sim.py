# -*- coding: utf-8 -*-
"""_wire3_defensive_sim.py — WIRE3 defensive selection 정합 시뮬 (2026-06-04).

cyclical(_wire3_selection_sim.py) 와 동형, defensive sleeve(48종) 버전.
defensive 특수: 신호 부호가 반직관(net_issuance IC 양 = buyback-aversion/anti-value, ep_yield 음 = anti-value).
→ selection 이 measure 입증 IC *부호를 그대로 따르는지* 가 핵심(cheapness sign = IC 부호 자동).

검증 3축:
  (1) selection top-K(net_issuance primary, sign=IC 부호) excess vs universe > 0 (측정 IC 부호 정합)
  (2) demean 레벨 A(sector-neutral std=measure) vs B(sleeve robust=현 모듈) vs C(sector-neutral robust)
  (3) comm_mature(n=4 < min_sector_n=8) sleeve-pool fallback 동작 (mega 보호 로직 동일)

재현: python _wire3_defensive_sim.py  (합성 0, go-live 무접촉)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

INV = "D:/projects/Inv"
HERE = str(Path(__file__).resolve().parent)
sys.path.insert(0, INV)
sys.path.insert(0, HERE)

import measure as M
import _breadth_sweep as BS
from stock.cross_sectional_selection import select_cross_sectional, SelectionConfig

H = 12
TOP_K = 10


def monthly_long_short(cheap_df, fwd, k=TOP_K):
    idx = cheap_df.index.intersection(fwd.index)
    spreads, topexc = [], []
    for dt in idx:
        cv = cheap_df.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = cv.index.intersection(rv.index)
        if len(c) < 2 * k:
            continue
        cv, rv = cv.loc[c], rv.loc[c]
        ranked = cv.sort_values(ascending=False)
        spreads.append(rv.loc[ranked.index[:k]].mean() - rv.loc[ranked.index[-k:]].mean())
        topexc.append(rv.loc[ranked.index[:k]].mean() - rv.mean())
    return pd.Series(spreads), pd.Series(topexc)


def robust_z_df(panel, secmap=None):
    def _rz(sub):
        med = sub.median(axis=1)
        mad = (sub.sub(med, axis=0)).abs().median(axis=1)
        return sub.sub(med, axis=0).div((1.4826 * mad).replace(0, np.nan), axis=0)
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
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    amt = pd.read_parquet(Path(HERE) / "data" / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    P = M.build_pit_panels(px, ed)
    B = BS.build_breadth_panels(px, ed, amt)
    pxm = px.resample("ME").last()
    fwd = pxm.shift(-H) / pxm - 1.0

    ni, ep = B["net_issuance"], P["ep_yield"]

    # ── measure 입증 IC (sector-neutral std z) + cheapness sign 자동 ──
    ni_z, ep_z = M.cs_z(ni, secmap), M.cs_z(ep, secmap)
    ic_ni, _ = M.cs_ic(ni_z, fwd); ic_ep, _ = M.cs_ic(ep_z, fwd)
    sign_ni = 1 if ic_ni.mean() > 0 else -1
    sign_ep = 1 if ic_ep.mean() > 0 else -1
    print("=" * 76)
    print("[measure 입증 IC] (sector-neutral std z, raw 부호)")
    print(f"  net_issuance  IC = {ic_ni.mean():+.4f}  → cheapness sign={sign_ni:+d}  (양=발행多 forward↑=buyback-aversion), n={len(ic_ni)}")
    print(f"  ep_yield      IC = {ic_ep.mean():+.4f}  → cheapness sign={sign_ep:+d}  (음=ep高 forward↓=anti-value), n={len(ic_ep)}")
    print(f"  comm_mature bucket n = {sum(1 for v in secmap.values() if v=='comm_mature')} (<8 → sleeve-pool fallback 대상)")

    # cheapness composite (높을수록 매수) — sign = IC 부호
    A = (sign_ni * ni_z + sign_ep * ep_z) / 2.0                       # sector-neutral std
    ni_zs, ep_zs = M.cs_z(ni, None), M.cs_z(ep, None)
    Bz = (sign_ni * ni_zs + sign_ep * ep_zs) / 2.0                    # sleeve std
    ni_rz, ep_rz = robust_z_df(ni, None), robust_z_df(ep, None)
    Bv = (sign_ni * ni_rz + sign_ep * ep_rz) / 2.0                    # sleeve robust (현 모듈 z)
    ni_rzs, ep_rzs = robust_z_df(ni, secmap), robust_z_df(ep, secmap)
    Cv = (sign_ni * ni_rzs + sign_ep * ep_rzs) / 2.0                  # sector-neutral robust

    print("=" * 76)
    print(f"[long-short spread] top{TOP_K} − bottom{TOP_K}, forward {H}M (net_iss+ep composite, sign=IC)")
    for name, ch in [("A sector-neutral·std (measure)", A), ("Bz sleeve·std            ", Bz),
                     ("B  sleeve·robust (현 selection)", Bv), ("C  sector-neutral·robust  ", Cv)]:
        sp, ex = monthly_long_short(ch, fwd)
        se = M.nw_se(sp, lags=H) if len(sp) > 3 else np.nan
        t = sp.mean() / se if (se and not np.isnan(se)) else np.nan
        print(f"  {name:34s} spread={sp.mean():+.4f}  NW_t={t:+.2f}  top_excess={ex.mean():+.4f}  n={len(sp)}")

    # ── selection 모듈 직접 호출: net_issuance primary, off/on ──
    print("=" * 76)
    print("[selection 모듈] net_issuance primary (sign=IC 부호) off(sleeve)/on(sector-neutral)")
    idx = ni.index.intersection(fwd.index)

    def run_module(by_sector, metrics):
        cfg = SelectionConfig(top_k=TOP_K, market_cap_floor=0.0,
                              demean_by_sector=by_sector, min_sector_n=8)
        signs = {"net_issuance": sign_ni, "ep_yield": sign_ep}
        exc, ns = [], []
        for dt in idx:
            cols = {}
            for mname, panel in metrics.items():
                v = panel.loc[dt].dropna()
                cols[mname] = v
            tk = sorted(set().union(*[set(v.index) for v in cols.values()]))
            rv = fwd.loc[dt].dropna()
            if len(set(tk) & set(rv.index)) < 2 * TOP_K:
                continue
            panel = {m: {t: cols[m].get(t) for t in tk} for m in cols}
            caps = {t: 1e9 for t in tk}
            cands = select_cross_sectional(panel, caps, {m: signs[m] for m in cols},
                                           sectors=secmap, config=cfg)
            picks = [c.ticker for c in cands if c.target_weight > 0 and c.ticker in rv.index]
            if not picks:
                continue
            exc.append(rv.loc[picks].mean() - rv.mean()); ns.append(len(picks))
        return pd.Series(exc), np.mean(ns) if ns else 0

    for label, metrics in [("net_iss only ", {"net_issuance": ni}),
                           ("net_iss+ep   ", {"net_issuance": ni, "ep_yield": ep})]:
        eo, no = run_module(False, metrics)
        en, nn = run_module(True, metrics)
        print(f"  {label} off excess={eo.mean():+.4f}(n={len(eo)})  on excess={en.mean():+.4f}  Δ={en.mean()-eo.mean():+.4f}  picks={no:.1f}")

    print("=" * 76)
    print("[해석] module excess>0 = selection top-K 가 측정 IC 부호(anti-value) 정합 / comm_mature n=4 fallback 무오류")


if __name__ == "__main__":
    main()
