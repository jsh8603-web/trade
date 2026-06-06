# -*- coding: utf-8 -*-
"""measure_capex_cycle.py — 정유 capex 사이클 시계열 측정 (dispatch ★★최우선 가설).

★dispatch 인계: 자동차서 capex_ratio(유형자산/총자산 asset growth, prior 음)가 OOS robust +
  size독립 + FDR생존(structural_prior_high_confidence). 정유 = 초자산집약 장치산업이라 capex 우선 검증.
  ★실측 확인: 정유 코어 capex_ratio = SK이노 0.33~0.54 / S-Oil 0.45~0.64 = 자동차보다 자산집약 극심.

★측정 = 2 path (cross-sectional 불가 → 시계열 + 정직 INSUFFICIENT 박제):
  (A) cross-sectional capex IC: 코어 strict2(SK이노/S-Oil) = 2종 → ★INSUFFICIENT(min 8종 불가, 정직 박제)
  (B) 시계열 capex cycle: 정유 코어 패널평균 capex_ratio(level + yoy) → forward 산업수익 (증설→되돌림 가설)
      Cooper-Gulen-Schill 2008 asset growth anomaly = 산업 aggregate 버전. prior 음(과잉투자→공급과잉→마진하락).

★PIT: rcept_dt(공시일) 이후만. 분기→월말 forward-fill.
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


def spearman_neff(x, y, label):
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
    ext = pd.read_parquet(DATA / "dart_extended.parquet").copy()
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    uni = pd.read_parquet(DATA / "universe.parquet")
    ext["rcept_dt"] = pd.to_datetime(ext["rcept_dt"], format="%Y%m%d", errors="coerce")
    ext = ext.dropna(subset=["rcept_dt"])

    core = uni[uni["is_refining_core"]]["Code"].tolist()
    core = [c for c in core if c in px.columns]
    strict2 = uni[uni["is_refining_core"] & uni["pass_floor_strict"]]["Code"].tolist()
    strict2 = [c for c in strict2 if c in px.columns]
    pxm = px.resample("ME").last()
    ret = pxm[strict2].pct_change().mean(axis=1)

    out = {"meta": {
        "purpose": "dispatch ★★최우선 capex 가설 — 정유 초자산집약(capex_ratio 0.33~0.64) capex cycle",
        "panel_core": core, "strict2": strict2,
        "cross_sectional_verdict": "★INSUFFICIENT — 코어 strict2 = 2종(SK이노/S-Oil), 횡단면 IC(min 8종) 불가. capex cross-sectional 측정 불능(정직 박제, deferral 아님).",
        "approach": "(A) cross-sectional=INSUFFICIENT 박제 / (B) 산업 시계열 capex cycle 측정 (Cooper-Gulen-Schill 2008 aggregate 버전)",
    }, "capex_ratio_by_firm": {}, "industry_capex_cycle": {}, "forward": {}, "walk_forward_oos": {}}

    # ── 종목별 capex_ratio (PIT, 월말) ──
    cap_panel = {}
    for code in core:
        cf = ext[ext["code"] == code].sort_values("rcept_dt").drop_duplicates("rcept_dt", keep="last")
        if len(cf) < 4:
            continue
        s = pd.Series(index=pxm.index, dtype=float)
        for dt in pxm.index:
            av = cf[cf["rcept_dt"] <= dt]
            if len(av) == 0:
                continue
            last = av.iloc[-1]
            a, p = last.get("assets"), last.get("ppe")
            if a and a > 0 and pd.notna(p):
                s[dt] = p / a
        cap_panel[code] = s
        valid = s.dropna()
        if len(valid):
            out["capex_ratio_by_firm"][code] = {"mean": round(float(valid.mean()), 3),
                                                "min": round(float(valid.min()), 3),
                                                "max": round(float(valid.max()), 3), "n_months": len(valid)}
    cap_df = pd.DataFrame(cap_panel)

    # ── 산업 aggregate capex_ratio (코어 패널 평균) + yoy ──
    ind_capex = cap_df.mean(axis=1)               # 산업 평균 capex_ratio (level)
    ind_capex_yoy = ind_capex / ind_capex.shift(12) - 1   # capex_ratio yoy (증설 가속)
    out["industry_capex_cycle"] = {
        "level_mean": round(float(ind_capex.loc["2019":].dropna().mean()), 3),
        "level_range": [round(float(ind_capex.loc["2019":].dropna().min()), 3),
                        round(float(ind_capex.loc["2019":].dropna().max()), 3)],
        "yoy_mean": round(float(ind_capex_yoy.loc["2019":].dropna().mean()), 4),
        "note": "정유 코어 패널 평균 capex_ratio(유형자산/총자산). level 0.4~0.5 = 자동차(0.2~0.3)보다 초자산집약.",
    }

    # ── forward: capex_ratio level + yoy → 정유 forward 3M 수익 (asset growth anomaly aggregate) ──
    fwd3 = pxm[strict2].pct_change(3).mean(axis=1).shift(-3)
    for nm, s in [("capex_ratio_level", ind_capex), ("capex_ratio_yoy", ind_capex_yoy)]:
        out["forward"][nm] = spearman_neff(s.loc["2019":], fwd3.loc["2019":], f"{nm}__fwd3")
        # OOS
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

    (ROOT / "validation-capex-cycle-v3.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print("=== 정유 capex (dispatch ★★최우선 가설) ===")
    print(f"코어 패널: {core} / strict2: {strict2}")
    print("\n종목별 capex_ratio(유형자산/총자산):")
    for c, d in out["capex_ratio_by_firm"].items():
        print(f"  {c}: mean={d['mean']} range[{d['min']},{d['max']}] n={d['n_months']}")
    print(f"\n산업 aggregate: level {out['industry_capex_cycle']['level_range']} (자동차 0.2~0.3 대비 초자산집약)")
    print("\n--- (A) cross-sectional capex IC ---")
    print("  ★INSUFFICIENT — strict2 = 2종, 횡단면 IC(min 8) 불가 (정직 박제)")
    print("\n--- (B) 산업 시계열 capex cycle → forward 3M ---")
    for nm, st in out["forward"].items():
        if st.get("status") == "INSUFFICIENT(n<8)":
            print(f"  {nm:20s} INSUFFICIENT"); continue
        oos = out["walk_forward_oos"][nm]
        print(f"  {nm:20s} rho={st['spearman_rho']:+.3f} wc_p={st['wild_cluster_p']} n={st['n']} n_eff={st['n_eff']} t_eff={st['t_eff_corrected']} | OOS IS={oos['is_rho']}/OOS={oos['oos_rho']} {'HOLD' if oos['sign_hold'] else 'FLIP'}")
    print("\nSaved validation-capex-cycle-v3.json")


if __name__ == "__main__":
    main()
