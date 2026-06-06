# -*- coding: utf-8 -*-
"""_breadth_sweep.py — ★breadth 후보 전수 B″ size-valid sweep (사용자 지적 = 우선순위만 측정 갭).

REWORK-B2 + 사용자 명시. 변경된 B″ 프레임(fixed-b CV + wild-cluster + 단일 FDR family + effective_n)으로
defensive 나머지 breadth 후보 전수 측정. _b2_stats.py(공용) + measure.py 재사용. measure.py 미변경(별 파일).

## 측정 6종 (즉시 = 신규 fetch 0, 보유 concept/price/volume)
1. net_issuance ((issuance−repurchase)/mktcap, 음) — Pontiff-Woodgate(2008 JF). 발행 多 → forward↓.
2. high_52w (현재가/52주최고, 양) — George-Hwang(2004 JF). 신고가 근접 → momentum.
3. amihud (|ret|/dollar volume, 양) — Amihud(2002 JFM). 비유동성 프리미엄.
4. op_profitability (OpIncome/equity, 양) — Fama-French(2015) RMW. 운영수익성.
5. roe (TTM NI/equity, 양) — quality. 자기자본수익률.
6. accruals ((NI−CFO)/assets, 음) — Sloan(1996 AR). 발생액 多 → 저품질 earnings → forward↓.

## 측정 못 함 (ledger 이연 사유)
- SUE-PEAD: 8-K Item 2.02 furnish date anchor 필요 = EDGAR 8-K 파싱 별도 작업 = 데이터게이트. 이번 제외.

## 방법: 각 후보 IC + fixed-b CV size-valid + ★단일 FDR family(기존 ep/idio/rmom 9 + 신규, M_eff 재계산) BY.
★합성 0. go-live 미접촉. measure.py byte-identical.
"""
from __future__ import annotations
import sys, json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure as M
import _b2_stats as B2
import _step4_add_factors as S4   # build_idio_vol / build_residual_mom 재사용

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def build_breadth_panels(px, ed, amt):
    """6 breadth 후보 월말 패널 (PIT). price/volume = forward-shift safe, EDGAR = filed PIT."""
    pxm = px.resample("ME").last()
    midx = pxm.index
    ed = M._ed_prep(ed)
    by_t = {t: ed[ed["ticker"] == t] for t in px.columns}

    keys = ["net_issuance", "high_52w", "amihud", "op_profitability", "roe", "accruals"]
    panels = {k: {} for k in keys}

    # price-based (52w_high, amihud) — fetch 0
    roll_max_52w = px.rolling(252, min_periods=120).max().resample("ME").last()
    high52 = (pxm / roll_max_52w)  # 1 에 가까울수록 신고가 근접 (양)
    ret_d = px.pct_change().abs()
    amtd = amt.replace(0, np.nan)
    amihud_d = (ret_d / amtd)  # |ret|/dollar volume (일별 illiquidity)
    amihud_m = amihud_d.rolling(60, min_periods=30).mean().resample("ME").last() * 1e6  # 스케일

    for t in px.columns:
        sub = by_t[t]
        g = lambda c: sub[sub["concept"] == c].sort_values("filed_dt")
        eq, ni, assets = g("equity"), g("net_income"), g("assets")
        opi, cfo, iss, rep = g("op_income"), g("cfo"), g("issuance"), g("repurchase")
        ser = {k: pd.Series(index=midx, dtype=float) for k in keys}
        for dt in midx:
            price = pxm.loc[dt, t]
            if np.isnan(price):
                continue
            # price-based
            if t in high52.columns and dt in high52.index:
                v = high52.loc[dt, t]
                if not np.isnan(v):
                    ser["high_52w"][dt] = v
            if t in amihud_m.columns and dt in amihud_m.index:
                v = amihud_m.loc[dt, t]
                if not np.isnan(v):
                    ser["amihud"][dt] = v
            # EDGAR-based (filed PIT)
            a = M._latest_pit(assets, dt)
            equity = M._latest_pit(eq, dt)
            ttm_ni = M._ttm(ni, dt)
            ttm_op = M._ttm(opi, dt)
            ttm_cfo = M._ttm(cfo, dt)
            ttm_iss = M._ttm(iss, dt); ttm_rep = M._ttm(rep, dt)
            shares = M._latest_pit(g("shares"), dt)
            mktcap = price * shares if (shares and shares > 0) else np.nan
            # net_issuance = (issuance − repurchase)/mktcap (양 = 순발행 → forward↓ 예상, IC 음)
            if not np.isnan(mktcap) and mktcap > 0 and (not np.isnan(ttm_iss) or not np.isnan(ttm_rep)):
                iss_v = ttm_iss if not np.isnan(ttm_iss) else 0
                rep_v = ttm_rep if not np.isnan(ttm_rep) else 0
                ser["net_issuance"][dt] = (iss_v - rep_v) / mktcap
            # op_profitability = OpIncome/equity
            if not np.isnan(ttm_op) and equity and equity > 0:
                ser["op_profitability"][dt] = ttm_op / equity
            # roe = TTM NI/equity
            if not np.isnan(ttm_ni) and equity and equity > 0:
                ser["roe"][dt] = ttm_ni / equity
            # accruals = (NI − CFO)/assets (양 = 고accrual → forward↓, IC 음)
            if not np.isnan(ttm_ni) and not np.isnan(ttm_cfo) and a and a > 0:
                ser["accruals"][dt] = (ttm_ni - ttm_cfo) / a
        for k in keys:
            panels[k][t] = ser[k]
    return {k: pd.DataFrame(v) for k, v in panels.items()}


def main():
    px, ed, uni, macro = M.load()
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    amt = pd.read_parquet(DATA / "amount.parquet"); amt.index = pd.to_datetime(amt.index)
    pxm = px.resample("ME").last()
    P = M.build_pit_panels(px, ed)
    B = build_breadth_panels(px, ed, amt)

    # sector-neutral z (신규 6 + 기존 ep/idio/rmom)
    ep_z = M.cs_z(P["ep_yield"], secmap)
    idio = S4.build_idio_vol(px); idio_z = M.cs_z(idio, secmap)
    rmom = S4.build_residual_mom(px, secmap); rmom_z = M.cs_z(rmom, secmap)
    new = {k: M.cs_z(B[k], secmap) for k in B}

    signals = {"ep_yield": ep_z, "idio_vol": idio_z, "residual_mom": rmom_z, **new}
    # 방향 메모(참고): net_issuance 음/high_52w 양/amihud 양/op_prof 양/roe 양/accruals 음/ep 음/idio 음/rmom 양

    results, pvals, ic_series = {}, {}, {}
    print("=" * 100)
    print("★breadth 전수 B″ size-valid sweep (fixed-b CV + 단일 FDR family)")
    print(f"{'signal__h':<24}{'IC':>9}{'t_NW':>7}{'n':>5}{'n_eff':>7}{'fb_CV':>7}{'sizeOK':>7}{'cov':>6}")
    for name, sig in signals.items():
        for h in [12, 6, 3]:
            fwd = pxm.shift(-h) / pxm - 1
            ic, ns = M.cs_ic(sig, fwd)
            if len(ic) < 12:
                continue
            tv = B2.ic_size_valid_test(ic)
            key = f"{name}__{h}M"
            p = float(2 * (1 - stats.t.cdf(abs(tv["t_nw"]), df=max(tv["effective_n"]["n_eff"] - 1, 1)))) if tv.get("t_nw") else np.nan
            cov = int(sig.notna().sum().sum())
            results[key] = dict(ic_mean=tv["ic_mean"], t_nw=tv["t_nw"], n=tv["n"],
                                n_eff=tv["effective_n"]["n_eff"], fixed_b_cv=tv["fixed_b"]["cv_5pct"],
                                size_valid_sig=tv["size_valid_sig"], asymptotic_sig=tv["asymptotic_sig"],
                                p_value_eff=round(p, 4) if not np.isnan(p) else None,
                                avg_universe_n=round(float(ns.mean()), 1), coverage_cells=cov)
            pvals[key] = p; ic_series[key] = ic
            mark = "★" if tv["size_valid_sig"] else " "
            print(f"{mark}{key:<23}{tv['ic_mean']:>+9.4f}{(tv['t_nw'] or 0):>7.2f}{tv['n']:>5}"
                  f"{tv['effective_n']['n_eff']:>7.1f}{tv['fixed_b']['cv_5pct']:>7.2f}{str(tv['size_valid_sig']):>7}{cov:>6}")

    # ── ★단일 FDR family BY (전 후보 통합, M_eff 재계산) ──
    keys = list(ic_series.keys())
    ic_df = pd.DataFrame({k: ic_series[k] for k in keys})
    tcorr = ic_df.corr().fillna(0).values; np.fill_diagonal(tcorr, 1.0)
    m_eff = M.m_eff_liji(tcorr)
    by = M.benjamini_yekutieli({k: pvals[k] for k in keys if k in pvals}, m_override=m_eff)
    size_valid_survivors = [k for k in by.get("survivors_BY", []) if results.get(k, {}).get("size_valid_sig")]
    # size-valid 개별 유의 신호 목록 (FDR 무관)
    size_valid_any = [k for k, v in results.items() if v["size_valid_sig"]]

    out = {"design": "breadth 전수 B″ sweep (신규 6 + 기존 ep/idio/rmom). 단일 FDR family fixed-b size-valid.",
           "candidates_measured": list(signals.keys()),
           "deferred": {"SUE_PEAD": "8-K Item 2.02 furnish date anchor 필요 = EDGAR 8-K 파싱 별도 작업(데이터게이트). 이번 제외."},
           "indicators": results,
           "single_fdr_family_BY": {**by, "m_eff": round(m_eff, 2), "n_tests": len(keys),
                                    "note": "★전 breadth 후보 단일 alpha budget. M_eff 재계산."},
           "size_valid_survivors_BY": size_valid_survivors,
           "size_valid_individual": size_valid_any}
    (ROOT / "_breadth_sweep.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print(f"\n★단일 FDR family BY: n_tests={len(keys)} raw m={by['m_raw']} M_eff={round(m_eff,2)} threshold={by['rank1_threshold']}")
    print(f"   BY survivors={by['survivors_BY']}")
    print(f"   ★size-valid survivors(BY ∩ fixed-b)={size_valid_survivors}")
    print(f"   ★size-valid 개별 유의(FDR 무관)={size_valid_individual if (size_valid_individual:=size_valid_any) else '없음'}")
    print(f"   raw_p_min={by['raw_p_min']} [{by['raw_p_min_key']}]")
    print("\nsaved _breadth_sweep.json")


if __name__ == "__main__":
    main()
