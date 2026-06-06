# -*- coding: utf-8 -*-
"""measure_quality.py — financial ROE/quality 신호 부활 측정 (약신호 부활, team-lead 지시).

candidate-ledger 이연 후보 부활: ROE/quality(DART 순이익/자본) + 고ROE 저PBR 결합(Asness QMJ).
★theory: 은행/보험 ROE 차별(증권 ROE 낮음) → quality 종목선택 신호 부활 시도.

측정 (conditional IC regime×horizon + walk-forward OOS + 단일 FDR + per-cell wc_p + MDE/power):
  1. roe_z: cross-sectional ROE z-score (고ROE=quality). 부호 사전확약 = ★양(+, 고ROE→고forward, quality premium).
  2. roe_pbr_combo: 고ROE 저PBR 결합(QMJ). z(ROE) − z(PBR) = quality-value 복합. 부호 = 양(+).
  3. sub-sector 분리(ALL/bank/securities/insurance/rate_POS) + regime 축(rate/credit/krw/flow).
  4. walk-forward OOS = ★DART 2023~ 제약 = IS(2019-22) n=0 가능성 점검 → within-period 대체.

★데이터 제약: DART 금융재무 2023~ (PBR과 동일 short-sample). ROE = quality 신호도 n 제약.
★PF 익스포저 종목별 = DART 주석 충당금 파싱 필요(복잡) → credit_regime 부분 대리, ROE 우선(team-lead 지시).

★G-G v2 tradeable 검정: OOS 부호유지 + per-cell wc_p + MDE/power. 부활 OR 약 정직 박제.
raw 재현: dart_financials/prices/regime_labels/universe parquet + 본 .py.
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
HORIZONS_D = {"y_5d": 5, "y_20d": 20, "y_60d": 60}
REGIME_AXES = ["rate_regime", "curve_regime", "credit_regime", "krw_regime", "flow_regime"]
SUBSECTOR_GROUPS = {
    "ALL": None, "bank": ["bank"], "securities": ["securities"],
    "insurance": ["insurance"], "rate_POS": ["bank", "insurance", "other_fin", "credit"],
}
STT_SELL, COMMISSION, SPREAD_HALF = 0.0020, 0.00015, 0.0005


def load():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    fin = pd.read_parquet(DATA / "dart_financials.parquet")
    uni = pd.read_parquet(DATA / "universe.parquet"); uni = uni[uni["pass_floor"]].set_index("Code")
    return px, lab, fin, uni


def csz(panel):
    return panel.sub(panel.mean(axis=1), axis=0).div(panel.std(axis=1, ddof=1).replace(0, np.nan), axis=0)


def ttm_or_fy_ni(ni_df):
    """TTM 순이익: FY 우선(가장 안정), 없으면 분기 annualize. (measure_valuation 미러)"""
    if len(ni_df) == 0:
        return None
    fy = ni_df[ni_df["quarter"] == "FY"]
    if len(fy):
        return fy["net_income"].iloc[-1]
    last = ni_df.iloc[-1]
    q_mult = {"Q1": 4, "H1": 2, "Q3": 4 / 3, "FY": 1}.get(last["quarter"], 1)
    return last["net_income"] * q_mult


def build_quality_signals(px, fin, uni):
    """PIT-safe ROE/quality + QMJ 결합 월말 z (rcept_dt 이후만)."""
    pxm = px.resample("ME").last()
    shares = {}
    for code in px.columns:
        lp = px[code].dropna()
        if len(lp) and code in uni.index:
            mc = uni.loc[code, "Marcap"]
            if pd.notna(mc) and lp.iloc[-1] > 0:
                shares[code] = mc / lp.iloc[-1]
    fin = fin.copy()
    fin["rcept_dt"] = pd.to_datetime(fin["rcept_dt"], format="%Y%m%d", errors="coerce")
    roe_panel, pbr_panel = {}, {}
    for code in px.columns:
        if code not in shares:
            continue
        cf = fin[fin["code"] == code].sort_values("rcept_dt")
        if len(cf) == 0:
            continue
        sh = shares[code]
        roe_s = pd.Series(index=pxm.index, dtype=float)
        pbr_s = pd.Series(index=pxm.index, dtype=float)
        for dt in pxm.index:
            avail = cf[cf["rcept_dt"] <= dt]   # ★PIT: 공시일 이후만
            if len(avail) == 0 or pd.isna(pxm.loc[dt, code]):
                continue
            eq = avail["equity"].iloc[-1]
            ni_avail = avail.dropna(subset=["net_income"])
            ttm_ni = ttm_or_fy_ni(ni_avail)
            if eq and eq > 0:
                if ttm_ni is not None:
                    roe_s[dt] = ttm_ni / eq          # ★ROE = TTM 순이익 / 자본
                pbr_s[dt] = pxm.loc[dt, code] * sh / eq
        roe_panel[code] = roe_s
        pbr_panel[code] = pbr_s
    roe_df = pd.DataFrame(roe_panel)
    pbr_df = pd.DataFrame(pbr_panel)
    roe_z = csz(roe_df)
    pbr_z = csz(pbr_df)
    # ★QMJ 결합: 고ROE(quality, +z) 저PBR(value, -z) → z(ROE) - z(PBR) = quality-value 복합 (고ROE+저PBR=고score)
    qmj = roe_z - pbr_z
    return {"roe_z": roe_z, "roe_pbr_qmj": csz(qmj)}


def forward_returns_daily(px, anchor_dates, h_days):
    out = {}
    for dt in anchor_dates:
        pos = px.index.searchsorted(dt)
        if pos >= len(px.index):
            continue
        p0 = min(pos, len(px.index) - 1); p1 = p0 + h_days
        if p1 >= len(px.index):
            continue
        out[dt] = (px.iloc[p1] / px.iloc[p0] - 1)
    return pd.DataFrame(out).T


def ic_series(sig, fwd, codes=None, min_n=6):
    out = {}
    for dt in sig.index.intersection(fwd.index):
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = sv.index.intersection(rv.index)
        if codes is not None:
            c = c.intersection(codes)
        if len(c) < min_n:
            continue
        rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
        if not np.isnan(rho):
            out[dt] = rho
    return pd.Series(out).sort_index()


def nw_se(x, lag):
    n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean(); var = (e @ e) / n
    for k in range(1, min(lag, n - 1) + 1):
        w = 1 - k / (lag + 1); var += 2 * w * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(max(var, 1e-12) / n))


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
        w = rng.choice([-1.0, 1.0], size=n); xb_null = w * e
        sb = xb_null.std(ddof=1)
        tb = abs(xb_null.mean() / (sb / np.sqrt(n))) if sb > 0 else 0.0
        if tb >= t_obs:
            cnt += 1
    return (cnt + 1) / (B + 1)


def block_boot_ci(x, block, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block + 1:
        return (np.nan, np.nan)
    nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        starts = rng.integers(0, n - block + 1, size=nb)
        means.append(np.concatenate([x[s:s + block] for s in starts])[:n].mean())
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def mde_power(ic_sd, n, alpha=0.05, power=0.8):
    """MDE = detectable |IC| at given n (G-G v2). 2-sided t, power 0.8 → ~2.8 SE."""
    if n < 4 or np.isnan(ic_sd):
        return None
    se = ic_sd / np.sqrt(n)
    return round(2.8 * se, 4)   # z_{0.975}+z_{0.8} ≈ 1.96+0.84 = 2.8


def measure_cell(ic, h_days):
    x = ic.values.astype(float); n = len(x)
    if n < 4:
        return {"n_months": n, "ic_mean": float(x.mean()) if n else np.nan, "status": "INSUFFICIENT(n<4)"}
    h_months = max(1, round(h_days / 21)); block = max(2, h_months)
    mean = float(x.mean()); sd = float(x.std(ddof=1))
    neff = n_eff_autocorr(x, max_lag=12); wc_p = wild_cluster_p(x); ci = block_boot_ci(x, block=block)
    powered = (n >= 24) and (neff >= 6)
    return {
        "n_months": n, "n_eff": round(neff, 1), "ic_mean": round(mean, 4),
        "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
        "ci95_block_boot": [round(ci[0], 4), round(ci[1], 4)] if not np.isnan(ci[0]) else None,
        "mde": mde_power(sd, neff), "ic_abs_vs_mde": ("detectable" if mde_power(sd, neff) and abs(mean) >= mde_power(sd, neff) else "underpowered"),
        "status": "powered" if powered else ("underpowered" if n >= 12 else "INSUFFICIENT(n<12)"),
    }


def benjamini_yekutieli(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1)); survivors = []
    for rank_i, (k, p) in enumerate(items, 1):
        if p <= (rank_i / m) * q / c_m:
            survivors = [items[j][0] for j in range(rank_i)]
    return {"m": m, "by_factor": round(c_m, 3), "bonferroni_alpha": round(0.05 / m, 5),
            "survivors_BY": survivors, "raw_p_min": round(items[0][1], 5) if items else None,
            "raw_p_min_key": items[0][0] if items else None}


def walk_forward(sig, px, anchor, codes, h):
    """IS(2019-22)/OOS(2023-26) + within-period (DART 2023~ 제약 시 OOS-only)."""
    fwd = forward_returns_daily(px, anchor, h)
    ic_all = ic_series(sig, fwd, codes)
    IS = set(pd.date_range("2019-01-01", "2022-12-31", freq="ME"))
    OOS = set(pd.date_range("2023-01-01", "2026-12-31", freq="ME"))
    ic_is = ic_all[ic_all.index.isin(IS)]; ic_oos = ic_all[ic_all.index.isin(OOS)]
    is_m = float(ic_is.mean()) if len(ic_is) else None
    oos_m = float(ic_oos.mean()) if len(ic_oos) else None
    by_year = {int(y): round(float(ic_all[ic_all.index.year == y].mean()), 3)
               for y in sorted(set(ic_all.index.year)) if len(ic_all[ic_all.index.year == y])}
    sign_hold = (is_m is not None and oos_m is not None and np.sign(is_m) == np.sign(oos_m))
    return {"IS_ic": round(is_m, 4) if is_m is not None else None, "IS_n": len(ic_is),
            "OOS_ic": round(oos_m, 4) if oos_m is not None else None, "OOS_n": len(ic_oos),
            "by_year": by_year, "sign_hold": bool(sign_hold),
            "note": "DART 2023~ 제약 = IS n 작을 수 있음 → within-period(by_year) 대체"}


def main():
    px, lab, fin, uni = load()
    code_map = uni["subcl"].to_dict()
    sigs = build_quality_signals(px, fin, uni)
    print(f"quality signals: {list(sigs.keys())}")
    print(f"  roe_z coverage: {sigs['roe_z'].notna().sum().sum()} cells / qmj: {sigs['roe_pbr_qmj'].notna().sum().sum()}")

    anchor = sigs["roe_z"].dropna(how="all").index
    lab19 = lab.loc["2019-01-01":]

    results = {"meta": {
        "signals": {"roe_z": "고ROE quality (DART TTM 순이익/자본), 부호확약 +",
                    "roe_pbr_qmj": "고ROE 저PBR 결합 QMJ z(ROE)-z(PBR), 부호확약 +"},
        "data_constraint": "★DART 금융재무 2023~ (PBR 동일 short-sample). ROE n 제약.",
        "pf_note": "★PF 익스포저 종목별 = DART 주석 충당금 파싱 복잡 → credit_regime 부분 대리, ROE 우선(team-lead).",
        "gg_v2": "tradeable 검정 = OOS 부호유지 + per-cell wc_p + MDE/power.",
    }}

    pvals = {}; surface = {}; oos = {}
    for skey, scls in SUBSECTOR_GROUPS.items():
        gcodes = None if scls is None else [c for c, sc in code_map.items() if sc in scls]
        surface[skey] = {}
        for sname, sig in sigs.items():
            surface[skey][sname] = {}
            for hname, h in HORIZONS_D.items():
                fwd = forward_returns_daily(px, anchor, h)
                ic_all = ic_series(sig, fwd, gcodes)
                if len(ic_all) < 6:
                    continue
                uncond = measure_cell(ic_all, h)
                cb = {"unconditional": uncond}
                for axis in REGIME_AXES:
                    la = lab19[axis].dropna()
                    for rg in sorted(la.unique()):
                        s2 = ic_all[ic_all.index.isin(la[la == rg].index)]
                        if len(s2) >= 4:
                            cb[f"{axis}={rg}"] = measure_cell(s2, h)
                            m = cb[f"{axis}={rg}"]
                            if m.get("status") == "powered" and m.get("wild_cluster_p") is not None:
                                pvals[f"{skey}__{sname}__{hname}__{axis}={rg}"] = m["wild_cluster_p"]
                if uncond.get("status") == "powered" and uncond.get("wild_cluster_p") is not None:
                    pvals[f"{skey}__{sname}__{hname}__uncond"] = uncond["wild_cluster_p"]
                surface[skey][sname][hname] = cb
                if hname == "y_60d":
                    oos[f"{skey}__{sname}__y_60d"] = walk_forward(sig, px, anchor, gcodes, h)
    results["quality_ic_surface"] = surface
    results["fdr_family"] = benjamini_yekutieli(pvals)
    results["walk_forward_oos"] = oos

    out = ROOT / "validation-quality-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")
    print_summary(results)
    return results


def print_summary(r):
    print("\n" + "=" * 76)
    print("QUALITY IC SURFACE — uncond + powered cell (sub-sector별, y_60d)")
    print("=" * 76)
    for skey, ssurf in r["quality_ic_surface"].items():
        print(f"\n##### sub-sector = {skey} #####")
        for sname, hd in ssurf.items():
            for hn in ["y_20d", "y_60d"]:
                cells = hd.get(hn, {}); unc = cells.get("unconditional", {})
                if not unc:
                    continue
                print(f"[{sname} {hn}] uncond IC={unc.get('ic_mean')} (n={unc.get('n_months')}, wc_p={unc.get('wild_cluster_p')}, mde={unc.get('mde')}, {unc.get('ic_abs_vs_mde')}, {unc.get('status')})")
                for ck, cv in cells.items():
                    if ck == "unconditional" or cv.get("status") != "powered" or cv.get("wild_cluster_p") is None or cv["wild_cluster_p"] >= 0.15:
                        continue
                    print(f"   ★{ck:22s} IC={cv['ic_mean']:+.4f} n={cv['n_months']} wc_p={cv['wild_cluster_p']} {cv.get('ic_abs_vs_mde')}")
    fdr = r["fdr_family"]
    print(f"\nFDR family: m={fdr.get('m')} BY_survivors={fdr.get('survivors_BY')} raw_p_min={fdr.get('raw_p_min')}({fdr.get('raw_p_min_key')})")
    print("\n=== walk-forward OOS (y_60d) ===")
    for k, v in r["walk_forward_oos"].items():
        print(f"  {k}: IS={v['IS_ic']}(n{v['IS_n']}) OOS={v['OOS_ic']}(n{v['OOS_n']}) sign_hold={v['sign_hold']} by_year={v['by_year']}")


if __name__ == "__main__":
    main()
