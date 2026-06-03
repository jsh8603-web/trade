# -*- coding: utf-8 -*-
"""interaction_t.py — financial cs_mom_6m_rate_up "rate_up에서만 양" claim 통계 근거.

supervisor #21 (S6 audit soft): regime split 점추정만 → interaction t 부착.
  (a) 회귀 interaction: IC_t ~ const + ΔRate_3M_t (NW HAC t) — IC가 금리변화에 선형 의존하는지
  (b) Welch t: rate_up regime IC vs (rate_down+rate_flat pooled), unequal-var
  (c) regime별 block-boot CI (block=horizon 비례)
★정직 게이트: interaction t 비유의(p>0.05) → "rate_up only 양" = hypothesis-generating 격하.
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


def load_signals_fwd():
    """mom_6 cross-sectional z + 12M forward (measure.py 로직 복제)."""
    px = pd.read_parquet(DATA / "prices.parquet"); px.index = pd.to_datetime(px.index)
    pxm = px.resample("ME").last()
    mom_6 = pxm / pxm.shift(6) - 1
    mu = mom_6.mean(axis=1); sd = mom_6.std(axis=1, ddof=1)
    sig = mom_6.sub(mu, axis=0).div(sd.replace(0, np.nan), axis=0)
    fwd = pxm.shift(-12) / pxm - 1
    return sig, fwd, pxm


def monthly_ic(sig, fwd, min_n=5):
    """월별 cross-sectional Spearman IC."""
    idx = sig.index.intersection(fwd.index); ics, dates = [], []
    for dt in idx:
        sv = sig.loc[dt].dropna(); rv = fwd.loc[dt].dropna()
        c = sv.index.intersection(rv.index)
        if len(c) < min_n:
            continue
        rho, _ = stats.spearmanr(sv.loc[c], rv.loc[c])
        if not np.isnan(rho):
            ics.append(rho); dates.append(dt)
    return pd.Series(ics, index=dates)


def get_rate_chg():
    """TNX 3M diff (regime driver), ex-ante."""
    import yfinance as yf
    tnx = yf.download("^TNX", start="2019-01-01", end="2026-05-29", progress=False, auto_adjust=True)["Close"].squeeze()
    tnx.index = pd.to_datetime(tnx.index)
    tnx_m = tnx.resample("ME").last()
    return tnx_m.diff(3)


def nw_se_slope(y, x, lags):
    """OLS y~x 의 slope NW HAC SE. (slope, se, t)."""
    import statsmodels.api as sm
    X = sm.add_constant(x)
    model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(model.params.iloc[1]), float(model.bse.iloc[1]), float(model.tvalues.iloc[1])


def block_boot_ci(x, block, B=2000, seed=42):
    if len(x) < block + 1:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed); n = len(x); nb = int(np.ceil(n / block)); m = []
    for _ in range(B):
        st = rng.integers(0, n - block + 1, size=nb)
        m.append(np.concatenate([x[s:s+block] for s in st])[:n].mean())
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    sig, fwd, pxm = load_signals_fwd()
    ic = monthly_ic(sig, fwd)
    rate_chg = get_rate_chg()
    # align
    df = pd.concat([ic.rename("ic"), rate_chg.rename("drate")], axis=1).dropna()
    print(f"aligned: n={len(df)} months")

    out = {"meta": {"n": len(df), "signal": "cs_mom_6m → 12M forward IC", "regime_driver": "ΔRate_3M (TNX)"}}

    # (a) 회귀 interaction: IC_t ~ const + ΔRate_t (NW HAC, lag=12=horizon)
    slope, se, t = nw_se_slope(df["ic"], df["drate"], lags=12)
    p = float(2 * (1 - stats.t.cdf(abs(t), df=max(len(df) - 2, 1))))
    out["interaction_regression"] = dict(
        spec="IC_t ~ const + ΔRate_3M_t (NW HAC lag=12)",
        slope=round(slope, 4), se=round(se, 4), t_nw=round(t, 2), p_value=round(p, 4),
        interpretation="slope>0 = 금리상승 시 IC↑ = rate_up 모멘텀 강 가설 통계근거")

    # (b) Welch t: rate_up vs pooled(rate_down+flat)
    regime = pd.Series(np.where(df["drate"] > 0.3, "rate_up",
                                np.where(df["drate"] < -0.3, "rate_down", "rate_flat")), index=df.index)
    ic_up = df["ic"][regime == "rate_up"].values
    ic_pool = df["ic"][regime != "rate_up"].values
    welch_t, welch_p = stats.ttest_ind(ic_up, ic_pool, equal_var=False)
    out["welch_test"] = dict(
        spec="rate_up IC vs (rate_down+rate_flat) pooled IC, unequal-var",
        rate_up_mean=round(float(ic_up.mean()), 4), rate_up_n=len(ic_up),
        pooled_mean=round(float(ic_pool.mean()), 4), pooled_n=len(ic_pool),
        welch_t=round(float(welch_t), 2), welch_p=round(float(welch_p), 4))

    # (c) regime별 block-boot CI (block=horizon 12 비례 → 작은 n 고려 block=6)
    out["regime_block_boot_ci"] = {}
    for reg in ["rate_up", "rate_down", "rate_flat"]:
        x = df["ic"][regime == reg].values
        block = min(6, max(2, len(x) // 4))
        lo, hi = block_boot_ci(x, block) if len(x) >= 6 else (np.nan, np.nan)
        out["regime_block_boot_ci"][reg] = dict(
            ic_mean=round(float(x.mean()), 4) if len(x) else None, n=len(x),
            ci95_block_boot=[round(lo, 4), round(hi, 4)] if not np.isnan(lo) else None, block=block)

    # ★정직 게이트
    interaction_sig = p < 0.05
    welch_sig = welch_p < 0.05
    out["verdict_gate"] = dict(
        interaction_significant=bool(interaction_sig), welch_significant=bool(welch_sig),
        verdict=("regime-conditional 신호 강화(단 n<30 magnitude hedge 유지)" if (interaction_sig or welch_sig)
                 else "★hypothesis-generating 격하 — 'rate_up only 양' claim 통계근거 부재(interaction p=%.3f welch p=%.3f >0.05). verdict TENTATIVE + live 제외 유지." % (p, welch_p)),
        live_excluded=True, tentative=True)

    (ROOT / "validation-interaction-v3.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print("\n=== (a) interaction 회귀 (IC ~ ΔRate) ===")
    r = out["interaction_regression"]
    print(f"  slope={r['slope']:+.4f} NW_t={r['t_nw']:+.2f} p={r['p_value']:.4f}")
    print("=== (b) Welch t (rate_up vs pooled) ===")
    w = out["welch_test"]
    print(f"  rate_up IC={w['rate_up_mean']:+.4f}(n{w['rate_up_n']}) vs pooled={w['pooled_mean']:+.4f}(n{w['pooled_n']}) → Welch t={w['welch_t']:+.2f} p={w['welch_p']:.4f}")
    print("=== (c) regime block-boot CI ===")
    for reg, v in out["regime_block_boot_ci"].items():
        print(f"  {reg}: IC={v['ic_mean']} n={v['n']} CI={v['ci95_block_boot']} (block={v['block']})")
    print(f"\n★게이트: interaction_sig={interaction_sig} welch_sig={welch_sig}")
    print(f"  → {out['verdict_gate']['verdict']}")


if __name__ == "__main__":
    main()
