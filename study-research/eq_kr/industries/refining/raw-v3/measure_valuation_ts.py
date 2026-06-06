# -*- coding: utf-8 -*-
"""measure_valuation_ts.py — 정유 valuation 측정 (M5: PBR○ / PER✗ peak-EPS, data-gate 대응).

★cross-sectional PBR/PER IC = INSUFFICIENT (정유 코어 strict 2종) → 정직 박제.
★시계열 valuation: 정유2종 평균 PBR(cycle 위치 = 밴드 하단 저평가 신호?) → forward 수익.
  실무 = PBR 밴드 차트 = 정유 핵심 valuation. 저PBR(밴드 하단) → 사이클 바닥 기대 → forward 양?

★PER = net_income 적자 빈발(SK이노 2024 -2.4조, S-Oil 2020/24/25 적자) + FY만(연1회) → 무효 확정 박제.
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


def n_eff_autocorr(x, max_lag=12):
    n = len(x)
    if n < 4:
        return float(n)
    e = x - x.mean(); v = (e @ e) / n
    if v <= 0:
        return float(n)
    s = 0.0
    for k in range(1, min(max_lag, n - 1) + 1):
        rk = (e[k:] @ e[:-k]) / n / v
        if rk <= 0:
            break
        s += (1 - k / (max_lag + 1)) * rk
    return float(n / (1 + 2 * s))


def wild_cluster_p(x, B=2000, seed=42):
    n = len(x)
    if n < 4:
        return np.nan
    rng = np.random.default_rng(seed)
    t_obs = abs(x.mean() / (x.std(ddof=1) / np.sqrt(n))) if x.std(ddof=1) > 0 else 0.0
    e = x - x.mean(); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n)
        xn = w * e; sb = xn.std(ddof=1)
        tb = abs(xn.mean() / (sb / np.sqrt(n))) if sb > 0 else 0.0
        if tb >= t_obs:
            cnt += 1
    return (cnt + 1) / (B + 1)


def spearman_full(x, y, label):
    common = x.dropna().index.intersection(y.dropna().index)
    if len(common) < 8:
        return {"label": label, "n": len(common), "status": "INSUFFICIENT(n<8)"}
    av, bv = x.loc[common].values, y.loc[common].values
    rho, p = stats.spearmanr(av, bv)
    prod = (stats.rankdata(av) / len(av) - 0.5) * (stats.rankdata(bv) / len(bv) - 0.5)
    neff = n_eff_autocorr(bv)
    t_eff = rho * np.sqrt((neff - 2) / (1 - rho ** 2)) if (abs(rho) < 1 and neff > 2) else np.nan
    t_naive = rho * np.sqrt((len(common) - 2) / (1 - rho ** 2)) if abs(rho) < 1 else np.nan
    return {"label": label, "n": len(common), "n_eff": round(neff, 1),
            "spearman_rho": round(float(rho), 4), "p_param": round(float(p), 4),
            "wild_cluster_p": round(wild_cluster_p(prod), 4),
            "t_naive": round(float(t_naive), 2) if not np.isnan(t_naive) else None,
            "t_eff_corrected": round(float(t_eff), 2) if not np.isnan(t_eff) else None,
            "status": "powered" if (len(common) >= 24 and neff >= 6) else ("underpowered" if len(common) >= 12 else "INSUFFICIENT")}


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    fin = pd.read_parquet(DATA / "dart_financials.parquet").copy()
    uni = pd.read_parquet(DATA / "universe.parquet")
    fin["rcept_dt"] = pd.to_datetime(fin["rcept_dt"], format="%Y%m%d", errors="coerce")
    fin = fin.dropna(subset=["rcept_dt"])
    strict2 = [c for c in uni[uni["is_refining_core"] & uni["pass_floor_strict"]]["Code"] if c in px.columns]
    pxm = px.resample("ME").last()

    # 발행주식수 근사 (universe Marcap / 최근가격)
    shares = {}
    for code in strict2:
        lp = px[code].dropna()
        mc = uni[uni["Code"] == code]["Marcap"]
        if len(lp) and len(mc) and pd.notna(mc.iloc[0]) and lp.iloc[-1] > 0:
            shares[code] = mc.iloc[0] / lp.iloc[-1]

    # PBR 시계열 (종목별 PIT, equity 기반)
    pbr_panel = {}
    for code in strict2:
        cf = fin[fin["code"] == code].sort_values("rcept_dt")
        s = pd.Series(index=pxm.index, dtype=float)
        for dt in pxm.index:
            av = cf[cf["rcept_dt"] <= dt]
            if len(av) == 0 or pd.isna(pxm.loc[dt, code]) or code not in shares:
                continue
            eq = av["equity"].iloc[-1]
            if eq and eq > 0:
                s[dt] = pxm.loc[dt, code] * shares[code] / eq
        pbr_panel[code] = s
    pbr_df = pd.DataFrame(pbr_panel)

    out = {"meta": {
        "panel": strict2, "purpose": "M5 valuation — cross-sectional INSUFFICIENT 박제 + 시계열 PBR cycle",
        "cross_sectional_verdict": "★INSUFFICIENT — strict2 = 2종, 횡단면 PBR/PER IC(min 8) ⛔불가.",
        "per_verdict": "★PER 무효 확정 — net_income 적자 빈발(SK이노2024 -2.4조/S-Oil 2020·24·25 적자) + FY만(연1회). peak-EPS trap + 음수EPS = PER cross-sectional·시계열 둘 다 무효.",
    }, "pbr_timeseries": {}, "pbr_industry_mean_forward": {}, "walk_forward_oos": {}}

    # 종목별 PBR 분포
    for code in strict2:
        v = pbr_df[code].dropna()
        if len(v):
            out["pbr_timeseries"][code] = {"mean": round(float(v.mean()), 3),
                                           "min": round(float(v.min()), 3),
                                           "max": round(float(v.max()), 3),
                                           "last": round(float(v.iloc[-1]), 3), "n": len(v)}

    # ── 시계열 PBR: 정유2종 평균 PBR(밴드 위치) → forward 3M ──
    # ★저PBR(밴드 하단) → 사이클 바닥 기대 → forward 양 prior = PBR level 음 corr
    ind_pbr = pbr_df.mean(axis=1)
    fwd3 = pxm[strict2].pct_change(3).mean(axis=1).shift(-3)
    # PBR own-history z (밴드 위치)
    ind_pbr_z = (ind_pbr - ind_pbr.rolling(24, min_periods=12).mean()) / ind_pbr.rolling(24, min_periods=12).std()
    for nm, s in [("pbr_level", ind_pbr), ("pbr_zscore_band", ind_pbr_z)]:
        out["pbr_industry_mean_forward"][nm] = spearman_full(s.loc["2019":], fwd3.loc["2019":], f"{nm}__fwd3")
        x, y = s, fwd3
        is_idx = pd.date_range("2019-01-01", "2022-12-31", freq="ME")
        oos_idx = pd.date_range("2023-01-01", "2026-05-31", freq="ME")
        def srho(idx):
            xi = x.reindex(idx).dropna(); yi = y.reindex(idx).dropna()
            c = xi.index.intersection(yi.index)
            return (float(stats.spearmanr(xi.loc[c], yi.loc[c])[0]), len(c)) if len(c) >= 6 else (None, len(c))
        ir, inn = srho(is_idx); orr, onn = srho(oos_idx)
        out["walk_forward_oos"][nm] = {"is_rho": round(ir, 4) if ir is not None else None, "is_n": inn,
                                       "oos_rho": round(orr, 4) if orr is not None else None, "oos_n": onn,
                                       "sign_hold": bool(ir is not None and orr is not None and np.sign(ir) == np.sign(orr))}

    (ROOT / "validation-valuation-ts-v3.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print("=== 정유 valuation (M5) ===")
    print(f"strict2: {strict2}")
    print("\n--- cross-sectional ---")
    print("  ★PBR/PER cross-sectional IC = INSUFFICIENT (2종, min 8 불가)")
    print("  ★PER = 무효 확정 (적자 빈발 + FY만)")
    print("\n종목별 PBR:")
    for c, d in out["pbr_timeseries"].items():
        print(f"  {c}: mean={d['mean']} range[{d['min']},{d['max']}] last={d['last']} n={d['n']}")
    print("\n--- 시계열 PBR(밴드) → forward 3M (저PBR→바닥→forward양 prior=음corr) ---")
    for nm, st in out["pbr_industry_mean_forward"].items():
        if st.get("status") == "INSUFFICIENT(n<8)":
            print(f"  {nm}: INSUFFICIENT"); continue
        oos = out["walk_forward_oos"][nm]
        print(f"  {nm:18s} rho={st['spearman_rho']:+.3f} wc_p={st['wild_cluster_p']} n={st['n']} n_eff={st['n_eff']} t_eff={st['t_eff_corrected']} | OOS IS={oos['is_rho']}/OOS={oos['oos_rho']} {'HOLD' if oos['sign_hold'] else 'FLIP'}")
    print("\nSaved validation-valuation-ts-v3.json")


if __name__ == "__main__":
    main()
