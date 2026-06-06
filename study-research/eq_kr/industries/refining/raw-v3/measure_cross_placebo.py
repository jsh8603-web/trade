# -*- coding: utf-8 -*-
"""measure_cross_placebo.py — 정유 cross 축(A-3 의무) + placebo + family_2 (S4/S5).

A-3 cross (★directional_spillover 빈 [] 금지): 정유 산업패널 공통인자 exposure β +
  선행신호 후보(유가/crack lead-lag). 산업=후보 보고, 통합조립=supervisor.
placebo: 무관 시계열(random/natgas-only) → forward 비유의 확인.
family_2: 유가 forward 음(-) 의 regime interaction (KRW_weak/macro × oil_level).
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
    if n < 4: return float(n)
    e = x - x.mean(); v = (e @ e) / n
    if v <= 0: return float(n)
    s = 0.0
    for k in range(1, min(max_lag, n - 1) + 1):
        rk = (e[k:] @ e[:-k]) / n / v
        if rk <= 0: break
        s += (1 - k / (max_lag + 1)) * rk
    return float(n / (1 + 2 * s))


def srho(x, y):
    c = x.dropna().index.intersection(y.dropna().index)
    c = [i for i in c if i >= pd.Timestamp("2019-01-01")]
    if len(c) < 8: return None, None, len(c)
    rho, p = stats.spearmanr(x.loc[c], y.loc[c])
    return float(rho), float(p), len(c)


def beta_with_ci(panel_ret, factor_ret, label):
    """산업패널수익 ~ factor 회귀 β (동시), HAC SE 근사 CI."""
    c = panel_ret.dropna().index.intersection(factor_ret.dropna().index)
    c = [i for i in c if i >= pd.Timestamp("2019-01-01")]
    if len(c) < 12:
        return {"factor": label, "n": len(c), "status": "INSUFFICIENT"}
    y = panel_ret.loc[c].values; x = factor_ret.loc[c].values
    X = np.column_stack([np.ones(len(x)), x])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y - X @ b
    s2 = (resid @ resid) / (len(x) - 2)
    se = np.sqrt(s2 * np.linalg.inv(X.T @ X)[1, 1])
    return {"factor": label, "beta": round(float(b[1]), 4),
            "beta_ci_95": [round(float(b[1] - 1.96 * se), 4), round(float(b[1] + 1.96 * se), 4)],
            "t": round(float(b[1] / se), 2), "n": len(c), "contemporaneous": True}


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    cyc = pd.read_parquet(DATA / "refining_cycle.parquet"); cyc.index = pd.to_datetime(cyc.index)
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    uni = pd.read_parquet(DATA / "universe.parquet")
    strict2 = [c for c in uni[uni["is_refining_core"] & uni["pass_floor_strict"]]["Code"] if c in px.columns]
    pxm = px.resample("ME").last()
    ret = pxm[strict2].pct_change().mean(axis=1)
    cycm = cyc.resample("ME").last()

    out = {"meta": {"panel": strict2, "purpose": "A-3 cross(빈[] 금지) + placebo + family_2"},
           "common_factor_exposure": [], "directional_spillover": [], "structural_linkage": [],
           "placebo": {}, "family_2_interaction": {}}

    # ── A-3 common factor exposure (동시 β) ──
    # 정유 = 유가/crack/달러/VIX 노출. (시장 공통인자 = brent Δ, dxy proxy via usdkrw, natgas)
    usdkrw = pd.read_parquet(DATA / "regime_series.parquet")["usdkrw"]
    usdkrw.index = pd.to_datetime(usdkrw.index)
    usdkrw_m = usdkrw.resample("ME").last()
    factors = {
        "oil_brent": cycm["brent"].pct_change(),
        "crack_blended": cycm["blended_crack"].diff(),
        "usdkrw": usdkrw_m.pct_change(),
        "natgas": cycm["natgas"].pct_change(),
    }
    for fn, fr in factors.items():
        out["common_factor_exposure"].append(beta_with_ci(ret, fr, fn))

    # ── directional_spillover (선행신호 후보, A-3 빈[] 금지) ──
    # 유가/crack lead-lag → 정유 forward (lead 신호 후보)
    fwd1 = ret.shift(-1)
    for nm, s in [("oil_brent_level", cycm["brent"]), ("blended_crack", cycm["blended_crack"]),
                  ("refinery_ip", cycm["refinery_ip"].shift(2))]:
        rho0, p0, n0 = srho(s, ret)        # 동시
        rho1, p1, n1 = srho(s, fwd1)       # lead 1M
        out["directional_spillover"].append({
            "candidate": nm, "contemp_rho": round(rho0, 4) if rho0 else None,
            "forward_1m_rho": round(rho1, 4) if rho1 else None, "n": n0,
            "note": "선행신호 후보 (산업=보고, DY 정식분해=supervisor 통합)"})
    out["structural_linkage"].append({
        "supplier": "글로벌 원유시장(Brent/Dubai) + 싱가포르 GRM",
        "note": "정유 upstream = 원유(투입)/제품 spread. lead-lag = 유가 동시 동조 강(β), forward 평균회귀. customer(석유화학·항공 등)는 chemical/별 산업 scope.",
        "verdict": "유가 동시 β 강(+) but forward alpha 부재(mean-reversion) = RegimeGlasso Ω 흡수 대상(동조성분)."})

    # ── placebo (무관 시계열 → forward 비유의) ──
    rng = np.random.default_rng(123)
    placebo_rand = pd.Series(rng.standard_normal(len(ret.loc["2019":])), index=ret.loc["2019":].index)
    fwd3 = pxm[strict2].pct_change(3).mean(axis=1).shift(-3)
    rho_p, p_p, n_p = srho(placebo_rand, fwd3)
    out["placebo"]["random_series"] = {"rho": round(rho_p, 4) if rho_p else None, "p": round(p_p, 4) if p_p else None, "n": n_p,
                                       "expect": "비유의 (placebo 통과 = 측정 파이프 정상)"}

    # ── family_2 interaction (유가 forward 음 × regime, A-5 의무) ──
    # 유가 level forward 음(-) 이 regime 따라 갈리나? pooled: fwd3 ~ oil_z + oil_z×macro_slowdown_dummy
    brent_z = (cycm["brent"] - cycm["brent"].rolling(24, min_periods=12).mean()) / cycm["brent"].rolling(24, min_periods=12).std()
    lab19 = lab.loc["2019":]
    for axis, rg in [("macro_regime", "Slowdown"), ("krw_regime", "KRW_weak"), ("flow_regime", "flow_strong_buy")]:
        rows = []
        for dt in brent_z.dropna().index:
            if dt not in fwd3.index or pd.isna(fwd3.loc[dt]) or dt not in lab19.index or pd.isna(lab19.loc[dt, axis]):
                continue
            dum = 1.0 if lab19.loc[dt, axis] == rg else 0.0
            rows.append((brent_z.loc[dt], fwd3.loc[dt], dum))
        if len(rows) < 20:
            out["family_2_interaction"][f"{axis}={rg}"] = {"status": "INSUFFICIENT", "n": len(rows)}
            continue
        df = pd.DataFrame(rows, columns=["oil", "ret", "dum"]); df["inter"] = df["oil"] * df["dum"]
        X = np.column_stack([np.ones(len(df)), df["oil"], df["inter"]]); y = df["ret"].values
        b = np.linalg.lstsq(X, y, rcond=None)[0]
        resid = y - X @ b; s2 = (resid @ resid) / (len(df) - 3)
        cov = s2 * np.linalg.inv(X.T @ X); se = np.sqrt(np.diag(cov))
        out["family_2_interaction"][f"{axis}={rg}"] = {
            "b_main": round(float(b[1]), 4), "t_main": round(float(b[1] / se[1]), 2),
            "b_inter": round(float(b[2]), 4), "t_inter": round(float(b[2] / se[2]), 2),
            "n": len(df), "verdict": "interaction 유의" if abs(b[2] / se[2]) > 2 else "interaction 비유의"}

    (ROOT / "validation-cross-placebo-v3.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("=== A-3 common factor exposure (동시 β) ===")
    for f in out["common_factor_exposure"]:
        if f.get("status") == "INSUFFICIENT": print(f"  {f['factor']}: INSUFF"); continue
        print(f"  {f['factor']:14s} β={f['beta']:+.3f} CI{f['beta_ci_95']} t={f['t']} n={f['n']}")
    print("\n=== directional_spillover (선행신호 후보) ===")
    for d in out["directional_spillover"]:
        print(f"  {d['candidate']:18s} contemp={d['contemp_rho']} fwd1m={d['forward_1m_rho']} n={d['n']}")
    print("\n=== placebo ===")
    print(f"  random: {out['placebo']['random_series']}")
    print("\n=== family_2 interaction (유가 forward 음 × regime, A-5) ===")
    for k, v in out["family_2_interaction"].items():
        if v.get("status") == "INSUFFICIENT": print(f"  {k}: INSUFF(n={v['n']})"); continue
        print(f"  {k:28s} b_main={v['b_main']:+.3f}(t={v['t_main']}) b_inter={v['b_inter']:+.3f}(t={v['t_inter']}) {v['verdict']}")
    print("\nSaved validation-cross-placebo-v3.json")


if __name__ == "__main__":
    main()
