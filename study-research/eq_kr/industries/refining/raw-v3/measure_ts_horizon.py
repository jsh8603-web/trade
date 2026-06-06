# -*- coding: utf-8 -*-
"""measure_ts_horizon.py — 정유 시계열 패널 horizon sweep 5d/20d/60d (team-lead 승인 보강).

team-lead 2-track 승인: 시계열 패널(frame M2) = 정유2종 동일가중 섹터수익 vs 정제마진/유가/가동률
  lag-corr + regime conditional, ★horizon 5d/20d/60d. G-G v2: walk-forward OOS + 단일 FDR + wild-cluster.

기존 measure_timeseries(월간 forward 1M/3M)를 ★일간 horizon 5d/20d/60d 로 명시 보강.
측정: driver(월말 anchor) → 정유섹터 forward h일 수익 IC(시계열 rank corr) + regime cell + OOS + FDR.
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
IP_PUB_LAG = 2


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


def wild_cluster_p(x, B=2000, seed=42):
    n = len(x)
    if n < 4: return np.nan
    rng = np.random.default_rng(seed)
    t_obs = abs(x.mean() / (x.std(ddof=1) / np.sqrt(n))) if x.std(ddof=1) > 0 else 0.0
    e = x - x.mean(); cnt = 0
    for _ in range(B):
        w = rng.choice([-1.0, 1.0], size=n); xn = w * e; sb = xn.std(ddof=1)
        tb = abs(xn.mean() / (sb / np.sqrt(n))) if sb > 0 else 0.0
        if tb >= t_obs: cnt += 1
    return (cnt + 1) / (B + 1)


def block_boot_ci(x, block, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block + 1: return [np.nan, np.nan]
    nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        means.append(np.concatenate([x[s:s + block] for s in st])[:n].mean())
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def sector_fwd(px, strict2, anchor_dates, h_days):
    """월말 anchor → 정유섹터(2종 동일가중) forward h일 수익."""
    out = {}
    for dt in anchor_dates:
        pos = px.index.searchsorted(dt)
        if pos >= len(px.index): continue
        p0i = min(pos, len(px.index) - 1); p1i = p0i + h_days
        if p1i >= len(px.index): continue
        r = (px[strict2].iloc[p1i] / px[strict2].iloc[p0i] - 1).mean()
        out[dt] = r
    return pd.Series(out).sort_index()


def driver_signal_corr(driver_m, sector_fwd_s, h_days, label):
    """driver(월말) vs 정유섹터 forward h일 = 시계열 rank corr + G-F."""
    common = driver_m.dropna().index.intersection(sector_fwd_s.dropna().index)
    common = [i for i in common if i >= pd.Timestamp("2019-01-01")]
    if len(common) < 8:
        return {"label": label, "n": len(common), "status": "INSUFFICIENT(n<8)"}
    dv = driver_m.loc[common].values; rv = sector_fwd_s.loc[common].values
    rho, _ = stats.spearmanr(dv, rv)
    prod = (stats.rankdata(dv) / len(dv) - 0.5) * (stats.rankdata(rv) / len(rv) - 0.5)
    n = len(prod); neff = n_eff_autocorr(rv)
    h_m = max(1, round(h_days / 21))
    wc_p = wild_cluster_p(prod); ci = block_boot_ci(prod, max(2, h_m))
    t_eff = rho * np.sqrt((neff - 2) / (1 - rho ** 2)) if (abs(rho) < 1 and neff > 2) else np.nan
    return {"label": label, "n": n, "n_eff": round(neff, 1),
            "spearman_rho": round(float(rho), 4),
            "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
            "t_eff_corrected": round(float(t_eff), 2) if not np.isnan(t_eff) else None,
            "ci95_block_boot_prod": [round(c, 5) for c in ci] if not np.isnan(ci[0]) else None,
            "status": "powered" if (n >= 24 and neff >= 6) else ("underpowered" if n >= 12 else "INSUFFICIENT")}


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    cyc = pd.read_parquet(DATA / "refining_cycle.parquet"); cyc.index = pd.to_datetime(cyc.index)
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    uni = pd.read_parquet(DATA / "universe.parquet")
    strict2 = [c for c in uni[uni["is_refining_core"] & uni["pass_floor_strict"]]["Code"] if c in px.columns]
    pxm = px.resample("ME").last()
    cycm = cyc.resample("ME").last(); cycm["refinery_ip"] = cycm["refinery_ip"].shift(IP_PUB_LAG)
    lab19 = lab.loc["2019-01-01":]
    anchor = pxm.index

    # driver = level + Δ (정유 cycle)
    drivers = {
        "brent_level": cycm["brent"], "oil_yoy": cycm["oil_yoy"],
        "blended_crack_level": cycm["blended_crack"], "d_blended_crack": cycm["blended_crack"].diff(),
        "diesel_crack_level": cycm["diesel_crack"], "refinery_ip": cycm["refinery_ip"],
    }
    out = {"meta": {"panel": strict2, "horizons": HORIZONS_D,
                    "method": "정유섹터(2종 동일가중) forward h일 vs driver 시계열 rank corr (team-lead 승인 horizon sweep)",
                    "gf": "wild-cluster + block-boot + eff-N + 단일 FDR(BY) + walk-forward OOS"},
           "horizon_surface": {}, "walk_forward_oos": {}, "regime_conditional": {}}
    pvals = {}

    for hname, h in HORIZONS_D.items():
        sfwd = sector_fwd(px, strict2, anchor, h)
        out["horizon_surface"][hname] = {}
        for dname, dser in drivers.items():
            st = driver_signal_corr(dser, sfwd, h, f"{dname}__{hname}")
            out["horizon_surface"][hname][dname] = st
            if st.get("status") == "powered" and st.get("wild_cluster_p") is not None:
                pvals[f"{dname}__{hname}"] = st["wild_cluster_p"]
        # OOS (brent_level 주신호)
        x = drivers["brent_level"]
        is_idx = pd.date_range("2019-01-01", "2022-12-31", freq="ME")
        oos_idx = pd.date_range("2023-01-01", "2026-05-31", freq="ME")
        def srho(idx):
            xi = x.reindex(idx).dropna(); yi = sfwd.reindex(idx).dropna()
            c = xi.index.intersection(yi.index)
            return (round(float(stats.spearmanr(xi.loc[c], yi.loc[c])[0]), 4), len(c)) if len(c) >= 6 else (None, len(c))
        ir, inn = srho(is_idx); orr, onn = srho(oos_idx)
        out["walk_forward_oos"][f"brent_level__{hname}"] = {
            "is_rho": ir, "is_n": inn, "oos_rho": orr, "oos_n": onn,
            "sign_hold": bool(ir is not None and orr is not None and np.sign(ir) == np.sign(orr))}

    # regime conditional (brent_level × y_20d 메인)
    sfwd20 = sector_fwd(px, strict2, anchor, 20)
    bl = drivers["brent_level"]
    for axis in ["macro_regime", "krw_regime", "flow_regime"]:
        la = lab19[axis].dropna()
        for rg in sorted(la.unique()):
            months = la[la == rg].index
            xs = bl[bl.index.isin(months)]; ys = sfwd20[sfwd20.index.isin(months)]
            st = driver_signal_corr(xs, ys, 20, f"brent_level_y20__{axis}={rg}")
            out["regime_conditional"][f"{axis}={rg}"] = st
            if st.get("status") == "powered" and st.get("wild_cluster_p") is not None:
                pvals[f"brent_regime__{axis}={rg}"] = st["wild_cluster_p"]

    # 단일 FDR (BY)
    items = [(k, v) for k, v in pvals.items() if v is not None]
    m = len(items)
    if m:
        items.sort(key=lambda x: x[1]); c_m = sum(1.0 / i for i in range(1, m + 1)); surv = []
        for ri, (k, p) in enumerate(items, 1):
            if p <= (ri / m) * 0.10 / c_m: surv = [items[j][0] for j in range(ri)]
        out["fdr_family"] = {"m": m, "by_factor": round(c_m, 3), "survivors_BY": surv,
                             "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0]}
    else:
        out["fdr_family"] = {"m": 0}

    (ROOT / "validation-ts-horizon-v3.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("=== 정유섹터 horizon sweep (5d/20d/60d) — driver → forward IC ===")
    for hname in HORIZONS_D:
        print(f"\n[{hname}]")
        for dname, st in out["horizon_surface"][hname].items():
            if st.get("status", "").startswith("INSUFF"): continue
            print(f"  {dname:22s} rho={st['spearman_rho']:+.3f} wc_p={st['wild_cluster_p']} t_eff={st['t_eff_corrected']} n={st['n']} {st['status']}")
    print("\n=== walk-forward OOS (brent_level) ===")
    for k, v in out["walk_forward_oos"].items():
        print(f"  {k:24s} IS={v['is_rho']}(n{v['is_n']}) OOS={v['oos_rho']}(n{v['oos_n']}) {'HOLD' if v['sign_hold'] else 'FLIP'}")
    print("\n=== regime conditional (brent_level y_20d) ===")
    for k, v in out["regime_conditional"].items():
        if v.get("status") in ("powered", "underpowered"):
            star = "★" if v["status"] == "powered" else " "
            print(f"  {star}{k:34s} rho={v['spearman_rho']:+.3f} wc_p={v['wild_cluster_p']} n={v['n']} {v['status']}")
    print(f"\nFDR family: {out['fdr_family']}")
    print("\nSaved validation-ts-horizon-v3.json")


if __name__ == "__main__":
    main()
