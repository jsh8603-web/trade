# -*- coding: utf-8 -*-
"""_step4_add_factors.py — ★STEP 4 일부 (add factor, 단일 FDR family, B″).

REWORK-B2-adjustment-plan §STEP 4 + .consult-us-rework-3R B″. payout NO_INTERACTION(rejected) →
sleeve 에 다른 살아있는 cross-sectional 신호 있는지 확인. ★payout 게이트와 무관한 독립 채널
(idio-vol low-risk / residual-mom)이라 "오염 추론 위 적층" 아님 = 측정 정당(team-lead 승인).

add factor (price-based, PIT-free):
- idio_vol: CAPM 잔차 변동성(market-residual). 저idio-vol → 고forward 예상(음 IC, low-vol anomaly).
  Ang-Hodrick-Xing-Zhang(2006). market = sleeve equal-weight return proxy.
- residual_mom: 12-1 month return 을 sector + market beta 에 orthogonalize 한 잔차 momentum.
  price-based, peak-EPS 오염 없음(가격 먼저 원칙).

★단일 FDR family: ep_yield(기존 TENTATIVE) + idio_vol + residual_mom = 하나의 alpha budget(BY).
★size-valid: fixed-b CV + effective-n (_b2_stats 공용 재사용).
★합성 0. measure.py 미변경(별 파일, byte-identical).
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

ROOT = Path(__file__).resolve().parent


def build_idio_vol(px, window=60):
    """★idio_vol = CAPM 잔차 변동성(market-residual). market = universe equal-weight daily return.
    각 종목 daily ret ~ market ret rolling 회귀 잔차의 rolling std → 월말 z 입력 패널."""
    ret_d = px.pct_change()
    mkt = ret_d.mean(axis=1)  # equal-weight market proxy (sleeve 내)
    idio = pd.DataFrame(index=ret_d.index, columns=ret_d.columns, dtype=float)
    # rolling beta 잔차 (간이: 전체기간 beta 로 잔차 후 rolling std — small-n robust)
    for t in ret_d.columns:
        df = pd.concat([ret_d[t].rename("r"), mkt.rename("m")], axis=1).dropna()
        if len(df) < window * 2:
            continue
        # expanding beta (PIT-safe 근사: 전체 beta 는 lookahead 미미 = 변동성 신호라 약). rolling 250d beta.
        beta = df["r"].rolling(250).cov(df["m"]) / df["m"].rolling(250).var()
        resid = df["r"] - beta * df["m"]
        idio[t] = resid.rolling(window).std() * np.sqrt(252)
    return idio.resample("ME").last()


def build_residual_mom(px, secmap):
    """★residual_mom = 12-1 month return 을 sector dummy + market beta 에 orthogonalize 한 잔차.
    각 월 cross-sectional 회귀: mom_12_1 ~ market_beta + sector dummies → 잔차 = residual momentum."""
    pxm = px.resample("ME").last()
    mom = pxm.shift(1) / pxm.shift(12) - 1  # 12-1 month return
    ret_d = px.pct_change(); mkt = ret_d.mean(axis=1)
    # market beta (250d rolling, 월말)
    beta_panel = pd.DataFrame(index=pxm.index, columns=pxm.columns, dtype=float)
    for t in pxm.columns:
        df = pd.concat([ret_d[t].rename("r"), mkt.rename("m")], axis=1).dropna()
        if len(df) < 250:
            continue
        b = (df["r"].rolling(250).cov(df["m"]) / df["m"].rolling(250).var()).resample("ME").last()
        beta_panel[t] = b.reindex(pxm.index)
    secs = sorted(set(secmap.values()))
    resid_mom = pd.DataFrame(index=mom.index, columns=mom.columns, dtype=float)
    for dt in mom.index:
        y = mom.loc[dt].dropna()
        if len(y) < 12:
            continue
        cols = y.index
        Xb = beta_panel.loc[dt, cols] if dt in beta_panel.index else pd.Series(np.nan, index=cols)
        # design: const + beta + sector dummies
        rows = []
        for t in cols:
            row = [1.0, Xb.get(t, np.nan)]
            sec_t = secmap.get(t, "_")
            for s in secs[1:]:  # drop first (baseline)
                row.append(1.0 if sec_t == s else 0.0)
            rows.append(row)
        Xmat = np.array(rows, float)
        yv = y.values
        good = ~np.isnan(Xmat).any(axis=1)
        if good.sum() < 10:
            continue
        Xg, yg, cg = Xmat[good], yv[good], cols[good]
        try:
            coef, *_ = np.linalg.lstsq(Xg, yg, rcond=None)
            resid = yg - Xg @ coef
            for c, r in zip(cg, resid):
                resid_mom.loc[dt, c] = r
        except Exception:
            continue
    return resid_mom


def main():
    px, ed, uni, macro = M.load()
    secmap = dict(zip(uni["ticker"], uni["subcl"]))
    pxm = px.resample("ME").last()
    P = M.build_pit_panels(px, ed)

    # signals (sector-neutral z)
    ep_z = M.cs_z(P["ep_yield"], secmap)
    idio = build_idio_vol(px); idio_z = M.cs_z(idio, secmap)
    rmom = build_residual_mom(px, secmap); rmom_z = M.cs_z(rmom, secmap)

    # 방향: idio_vol 음(저변동성 프리미엄) / residual_mom 양(momentum) / ep_yield 음(anti-value, 기존)
    signals = {"ep_yield": ep_z, "idio_vol": idio_z, "residual_mom": rmom_z}

    results, pvals = {}, {}
    print("=" * 92)
    print("★STEP 4 add factor (단일 FDR family, size-valid fixed-b)")
    print(f"{'signal__h':<22}{'IC':>9}{'t_NW':>7}{'n':>5}{'n_eff':>7}{'fixedb_CV':>10}{'sizeOK':>7}{'asyOK':>6}")
    for name, sig in signals.items():
        for h in [12, 6, 3]:
            fwd = pxm.shift(-h) / pxm - 1
            ic, ns = M.cs_ic(sig, fwd)
            if len(ic) < 12:
                continue
            tv = B2.ic_size_valid_test(ic)
            key = f"{name}__{h}M"
            # p-value (asymptotic, FDR 용) — size-valid 는 별도 플래그
            p = float(2 * (1 - stats.t.cdf(abs(tv["t_nw"]), df=max(tv["effective_n"]["n_eff"] - 1, 1)))) if tv.get("t_nw") else np.nan
            results[key] = dict(ic_mean=tv["ic_mean"], t_nw=tv["t_nw"], n=tv["n"],
                                n_eff=tv["effective_n"]["n_eff"], fixed_b_cv=tv["fixed_b"]["cv_5pct"],
                                size_valid_sig=tv["size_valid_sig"], asymptotic_sig=tv["asymptotic_sig"],
                                p_value_eff=round(p, 4) if not np.isnan(p) else None,
                                avg_universe_n=round(float(ns.mean()), 1))
            pvals[key] = p
            print(f"{key:<22}{tv['ic_mean']:>+9.4f}{(tv['t_nw'] or 0):>7.2f}{tv['n']:>5}"
                  f"{tv['effective_n']['n_eff']:>7.1f}{tv['fixed_b']['cv_5pct']:>10.2f}"
                  f"{str(tv['size_valid_sig']):>7}{str(tv['asymptotic_sig']):>6}")

    # ── 단일 FDR family BY (ep_yield + idio_vol + residual_mom 공유 budget) ──
    # ★size-valid p 기반 (effective-n adjusted). M_eff = Li-Ji on IC corr.
    ic_series = {}
    for name, sig in signals.items():
        for h in [12, 6, 3]:
            fwd = pxm.shift(-h) / pxm - 1
            ic, _ = M.cs_ic(sig, fwd)
            if len(ic) >= 12:
                ic_series[f"{name}__{h}M"] = ic
    keys = list(ic_series.keys())
    ic_df = pd.DataFrame({k: ic_series[k] for k in keys})
    tcorr = ic_df.corr().fillna(0).values; np.fill_diagonal(tcorr, 1.0)
    m_eff = M.m_eff_liji(tcorr)
    by = M.benjamini_yekutieli({k: pvals[k] for k in keys if k in pvals}, m_override=m_eff)

    # ★size-valid 생존: BY survivor 중 size_valid_sig=True 만
    size_valid_survivors = [k for k in by.get("survivors_BY", []) if results.get(k, {}).get("size_valid_sig")]

    out = {"design": "STEP 4 add factor (단일 FDR family: ep_yield + idio_vol + residual_mom). size-valid fixed-b.",
           "indicators": results,
           "single_fdr_family_BY": {**by, "m_eff": round(m_eff, 2),
                                    "note": "★단일 FDR family(ep+idio+rmom 공유 alpha budget). size-valid 생존 = BY survivor ∩ fixed-b 유의."},
           "size_valid_survivors": size_valid_survivors}
    (ROOT / "_step4_add.json").write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print(f"\n★단일 FDR family BY: raw m={by['m_raw']} M_eff={round(m_eff,2)} threshold={by['rank1_threshold']}")
    print(f"   BY survivors(asymptotic p)={by['survivors_BY']}")
    print(f"   ★size-valid survivors(BY ∩ fixed-b)={size_valid_survivors}")
    print(f"   raw_p_min={by['raw_p_min']} [{by['raw_p_min_key']}]")
    print("\nsaved _step4_add.json")


if __name__ == "__main__":
    main()
