# -*- coding: utf-8 -*-
"""measure_sector_timing.py — 조선 섹터 timing 신호 (★약신호 부활 측정, team-lead 지시 2026-06-05).

★cross-sectional 종목선택이 아니라 frame M2 ★섹터 timing:
  "조선 산업 eq-weight PBR 밴드(시계열) 저밴드 = 산업 비중↑, 고밴드 = ↓".
  = 정유 유가 mean-reversion 과 같은 섹터 timing 신호 (종목선택 0 이나 산업 timing 유효 가능성).

배경: 조선 cross-sectional selection = 구조적 약(산업 베타 지배 H9). 단 ★시계열 PBR 밴드는 별개:
  증권사 표준 = 조선 PBR 밴드(불황 0.5x → 호황 1.5-2x) mean-reversion timing. cross-sectional 무효 ≠ 시계열 무효.

측정:
  - 산업 합산 PBR(t) = Σ시총(t) / Σ자본(book, PIT rcept_dt) — aggregate book multiple 시계열.
  - PBR_z(t) = rolling z-score (own-history 36M window) = 밴드 위치.
  - timing IC = PBR_z(t) → 산업 eq-weight forward return(t+h). ★저밴드(낮은 z)→고forward = IC 음(mean-reversion).
  - horizon: 1M/3M/6M/12M (timing = 중기). walk-forward OOS + wild-cluster + regime conditional.

★G-F 7항 (measure_conditional 헤더 준용):
  - 단일 시계열 (n=85 month) → effective-n = n/(1+2Σρ). PBR_z 강한 자기상관(persistence) → n_eff 작음 명시.
  - null = IC=0. wild-cluster bootstrap(Rademacher B=2000) per p-value (small-block size-invalid 회피).
  - PIT: 자본 = rcept_dt 이후만. rolling z = expanding 아닌 trailing window(미래 누설 없음).
  - ★단일 신호라 FDR family = {PBR_z × 4 horizon × regime cell}. garden-of-forking-paths = horizon/regime multiplicity.
  - 비대칭 search 금지: rolling window 36M 사전 동결(도메인 표준), horizon 4종 사전.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "D:/projects/Inv")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

ROLL_WIN = 36   # ★PBR 밴드 z rolling window (36M = 3년, 사전 동결). cycle 길이 고려.
HORIZONS_M = {"1M": 1, "3M": 3, "6M": 6, "12M": 12}


def load_shares():
    import FinanceDataReader as fdr
    uni = pd.read_parquet(DATA / "universe.parquet"); uni = uni[uni["pass_floor"]]
    lst = pd.concat([fdr.StockListing("KOSPI")[["Code", "Close", "Marcap"]],
                     fdr.StockListing("KOSDAQ")[["Code", "Close", "Marcap"]]])
    lst = lst[lst["Code"].isin(uni["Code"])].copy()
    lst["shares"] = lst["Marcap"] / lst["Close"]
    return dict(zip(lst["Code"], lst["shares"]))


def build_industry_pbr(px, fin, shares):
    """산업 합산 PBR 시계열 = Σ시총 / Σ자본 (PIT rcept_dt 이후만)."""
    fin = fin.copy()
    fin["rcept"] = pd.to_datetime(fin["rcept_dt"], format="%Y%m%d", errors="coerce")
    pxm = px.resample("ME").last()
    agg_mc = pd.Series(index=pxm.index, dtype=float)
    agg_bk = pd.Series(index=pxm.index, dtype=float)
    for dt in pxm.index:
        mc_sum, bk_sum = 0.0, 0.0
        for code in px.columns:
            if code not in shares:
                continue
            p = pxm.loc[dt, code]
            if pd.isna(p):
                continue
            sub = fin[(fin["code"] == code) & (fin["rcept"] <= dt)].sort_values("rcept")
            if len(sub) == 0:
                continue
            eq = sub["equity"].iloc[-1]
            if pd.notna(eq) and eq > 0:
                mc_sum += p * shares[code]
                bk_sum += eq
        if bk_sum > 0:
            agg_mc[dt] = mc_sum
            agg_bk[dt] = bk_sum
    return (agg_mc / agg_bk).dropna()


def industry_eqw_return(px):
    """산업 eq-weight 월간 수익."""
    pxm = px.resample("ME").last()
    return pxm.pct_change().mean(axis=1)


def nw_se(x, lag):
    n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean(); var = (e @ e) / n
    for k in range(1, min(lag, n - 1) + 1):
        var += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
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
        w = rng.choice([-1.0, 1.0], size=n)
        xn = w * e; sb = xn.std(ddof=1)
        tb = abs(xn.mean() / (sb / np.sqrt(n))) if sb > 0 else 0.0
        if tb >= t_obs:
            cnt += 1
    return (cnt + 1) / (B + 1)


def block_boot_ci(x, block=6, B=2000, seed=42):
    rng = np.random.default_rng(seed); n = len(x)
    if n < block + 1:
        return [np.nan, np.nan]
    nb = int(np.ceil(n / block)); means = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        means.append(np.concatenate([x[s:s + block] for s in st])[:n].mean())
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def timing_ic(pbr_z, fwd_ret, h):
    """★섹터 timing IC = PBR_z(t) 와 forward return(t+h) 상관 (시계열, cross-sectional 아님).
    저밴드(낮은 z) → 고 forward = 음의 상관 (mean-reversion). Spearman.
    단일 시계열이라 'IC' = 전 표본 1개 corr (cross-sectional IC 처럼 월별 분포 아님).
    → 대신 pair (pbr_z(t), ret(t→t+h)) 시계열의 Spearman + wild-cluster 로 유의성."""
    df = pd.concat([pbr_z.rename("z"), fwd_ret.rename("r")], axis=1).dropna()
    if len(df) < 12:
        return None
    rho, p_param = stats.spearmanr(df["z"], df["r"])
    # wild-cluster on the product-deviation series (mean-zero null of corr)
    zc = (df["z"] - df["z"].mean()).values
    rc = (df["r"] - df["r"].mean()).values
    prod = zc * rc / (df["z"].std() * df["r"].std() + 1e-12)
    wc_p = wild_cluster_p(prod)
    neff = n_eff_autocorr(df["z"].values)   # PBR_z persistence
    ci = block_boot_ci(prod, block=max(6, h))
    return {"ic_spearman": round(float(rho), 4), "p_param": round(float(p_param), 4),
            "wild_cluster_p": round(wc_p, 4) if not np.isnan(wc_p) else None,
            "n_pairs": len(df), "n_eff_pbr_z": round(neff, 1),
            "ci95_block_boot": [round(v, 4) for v in ci],
            "status": "powered" if neff >= 6 else "underpowered(PBR_z persistence)"}


def main():
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    fin = pd.read_parquet(DATA / "dart_financials.parquet")
    lab = pd.read_parquet(DATA / "regime_labels.parquet"); lab.index = pd.to_datetime(lab.index)
    shares = load_shares()

    ind_pbr = build_industry_pbr(px, fin, shares)
    eqw_ret = industry_eqw_return(px)
    # PBR 밴드 z (rolling, trailing — 미래 누설 없음, min_periods 로 초기 expanding)
    pbr_z = (ind_pbr - ind_pbr.rolling(ROLL_WIN, min_periods=18).mean()) / \
            ind_pbr.rolling(ROLL_WIN, min_periods=18).std()
    pbr_z = pbr_z.dropna()

    print(f"산업 PBR 시계열 n={len(ind_pbr)} ({ind_pbr.index.min().date()}~{ind_pbr.index.max().date()})")
    print(f"PBR 범위 {ind_pbr.min():.2f}~{ind_pbr.max():.2f}, 현재 {ind_pbr.iloc[-1]:.2f}")
    print(f"PBR_z (rolling{ROLL_WIN}M) n={len(pbr_z)}, 현재 z={pbr_z.iloc[-1]:.2f}")

    results = {"meta": {
        "method": "★섹터 timing (frame M2): 산업 합산 PBR(Σ시총/Σ자본 PIT) rolling z → 산업 eq-weight forward return. cross-sectional 아님.",
        "pbr_range": [round(float(ind_pbr.min()), 2), round(float(ind_pbr.max()), 2), round(float(ind_pbr.iloc[-1]), 2)],
        "roll_window": ROLL_WIN, "n_pbr_z": len(pbr_z),
        "sign_note": "저밴드(낮은 z)→고 forward = IC 음(mean-reversion). ★현재 z 高(슈퍼사이클 정점) = 밴드 상단.",
        "gf_note": "단일 시계열 n_eff 작음(PBR_z persistence). wild-cluster + block-boot. FDR = horizon×regime multiplicity.",
    }, "unconditional": {}, "regime_conditional": {}, "walk_forward": {}}

    pvals = {}
    # forward return = t → t+h 누적
    pxm = px.resample("ME").last()
    for hname, h in HORIZONS_M.items():
        fwd = pxm.mean(axis=1)  # placeholder; use eqw cumulative
        fwd_ret = (pxm.shift(-h) / pxm - 1).mean(axis=1)  # 산업 eq-weight forward h개월
        r = timing_ic(pbr_z, fwd_ret, h)
        if r:
            results["unconditional"][hname] = r
            if r.get("wild_cluster_p") is not None:
                pvals[f"pbr_band__{hname}__uncond"] = r["wild_cluster_p"]
        # regime conditional (Macro/KRW/flow)
        lab19 = lab.loc["2019-01-01":]
        rc = {}
        for axis in ["macro_regime", "krw_regime", "flow_regime"]:
            la = lab19[axis].dropna()
            for rg in sorted(la.unique()):
                months = la[la == rg].index
                sub_z = pbr_z[pbr_z.index.isin(months)]
                sub_r = fwd_ret[fwd_ret.index.isin(months)]
                cr = timing_ic(sub_z, sub_r, h)
                if cr and cr["n_pairs"] >= 12:
                    rc[f"{axis}={rg}"] = cr
                    if cr.get("wild_cluster_p") is not None and cr.get("status") == "powered":
                        pvals[f"pbr_band__{hname}__{axis}={rg}"] = cr["wild_cluster_p"]
        results["regime_conditional"][hname] = rc
        # walk-forward OOS
        df = pd.concat([pbr_z.rename("z"), fwd_ret.rename("r")], axis=1).dropna()
        is_df = df[df.index <= "2022-12-31"]; oos_df = df[df.index >= "2023-01-01"]
        if len(is_df) >= 8 and len(oos_df) >= 6:
            is_rho = stats.spearmanr(is_df["z"], is_df["r"])[0]
            oos_rho = stats.spearmanr(oos_df["z"], oos_df["r"])[0]
            results["walk_forward"][hname] = {
                "is_ic": round(float(is_rho), 4), "is_n": len(is_df),
                "oos_ic": round(float(oos_rho), 4), "oos_n": len(oos_df),
                "sign_hold": bool(np.sign(is_rho) == np.sign(oos_rho)),
                "verdict": "OOS 부호유지" if np.sign(is_rho) == np.sign(oos_rho) else "★OOS 부호반전(artifact)"}

    # 단일 FDR family (BY)
    results["fdr_family"] = by_fdr(pvals)

    out = ROOT / "validation-sector-timing-v3.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {out}")
    print("\n=== ★PBR 밴드 timing IC (산업 forward, 저밴드→고forward=음) ===")
    for hname, r in results["unconditional"].items():
        print(f"  {hname:4s}: IC={r['ic_spearman']:+.4f} wc_p={r['wild_cluster_p']} n={r['n_pairs']} n_eff={r['n_eff_pbr_z']} CI={r['ci95_block_boot']} {r['status']}")
    print("\n=== walk-forward OOS (IS 2019-22 / OOS 2023-26) ===")
    for hname, w in results["walk_forward"].items():
        print(f"  {hname:4s}: IS={w['is_ic']:+.4f}(n{w['is_n']}) OOS={w['oos_ic']:+.4f}(n{w['oos_n']}) {w['verdict']}")
    print(f"\nFDR family: {results['fdr_family']}")
    print("\n=== regime conditional (powered cell, 3M) ===")
    for ck, cv in results["regime_conditional"].get("3M", {}).items():
        if cv.get("status") == "powered":
            print(f"  {ck:24s} IC={cv['ic_spearman']:+.4f} wc_p={cv['wild_cluster_p']} n={cv['n_pairs']}")


def by_fdr(pvals, q=0.10):
    items = [(k, v) for k, v in pvals.items() if v is not None and not np.isnan(v)]
    m = len(items)
    if m == 0:
        return {"m": 0, "note": "powered cell 0"}
    items.sort(key=lambda x: x[1])
    c_m = sum(1.0 / i for i in range(1, m + 1)); surv = []
    for ri, (k, p) in enumerate(items, 1):
        if p <= (ri / m) * q / c_m:
            surv = [items[j][0] for j in range(ri)]
    return {"m": m, "by_factor": round(c_m, 3), "bonferroni_alpha": round(0.05 / m, 5),
            "survivors_BY": surv, "raw_p_min": round(items[0][1], 5), "raw_p_min_key": items[0][0]}


if __name__ == "__main__":
    main()
