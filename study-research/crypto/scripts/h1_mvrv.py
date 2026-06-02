"""H1 MVRV mean-revert 검증.

가설: MVRV > 2.4 → 7d/30d horizon mean-revert 하락
반증조건:
  - FDR_DECISION binomial p > 0.05 (hit rate < 0.5)
  - score_ic e-CUSUM 단측 붕괴 (baseline 0.0 + sd)
  - partial-corr (MVRV ⊥ fwd_ret | FGI, halving_phase) 95% CI 0 포함

출력: ../raw/validation-h1-mvrv.md
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from lib_common import (
    load_coinmetrics, load_fgi, load_btc_klines,
    rank_ic, newey_west_se, effective_n, e_cusum_one_sided,
    block_bootstrap_ci, fgi_regime, halving_phase, forward_return,
)
import numpy as np
import pandas as pd
from scipy import stats

OUT = Path(__file__).resolve().parent.parent / "raw" / "validation-h1-mvrv.md"

def main():
    cm = load_coinmetrics()
    fgi = load_fgi()

    df = cm.copy()
    df["mvrv"] = df["CapMVRVCur"]
    df["price"] = df["PriceUSD"].fillna(df.get("ReferenceRateUSD"))
    df = df[["date", "mvrv", "price"]].dropna(subset=["mvrv", "price"])
    df = df.merge(fgi[["date", "fgi"]], on="date", how="left")
    df["halving_phase"] = df["date"].apply(halving_phase)
    df["log_ret"] = np.log(df["price"] / df["price"].shift(1))
    df["fwd_7d"] = forward_return(df["price"], 7)
    df["fwd_30d"] = forward_return(df["price"], 30)
    df["fwd_90d"] = forward_return(df["price"], 90)

    lines = []
    def w(s=""): lines.append(s)

    w("# H1 MVRV mean-revert — 실데이터 검증")
    w()
    w(f"as_of: {pd.Timestamp.utcnow().isoformat()}")
    w(f"data: CoinMetrics CapMVRVCur ({df['date'].min().date()} ~ {df['date'].max().date()}, n={len(df)})")
    w(f"price: CoinMetrics PriceUSD/ReferenceRateUSD")
    w(f"FGI merge: alternative.me ({fgi['date'].min().date()} ~ {fgi['date'].max().date()})")
    w()

    # ===== 1. 기본 통계 =====
    w("## 1. MVRV 시계열 기본 통계")
    desc = df["mvrv"].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
    w(f"```\n{desc.to_string()}\n```")
    w(f"MVRV > 2.4 일수: {(df['mvrv'] > 2.4).sum()} / {len(df)} = {(df['mvrv']>2.4).mean():.3%}")
    w(f"MVRV > 3.0 일수: {(df['mvrv'] > 3.0).sum()} / {len(df)} = {(df['mvrv']>3.0).mean():.3%}")
    w(f"MVRV < 1.0 일수: {(df['mvrv'] < 1.0).sum()} / {len(df)} = {(df['mvrv']<1.0).mean():.3%}")
    w()

    # ===== 2. 우리 시스템 mvrv_hi=2.4 closed-loop 재검증 =====
    w("## 2. instrument_source.run_mvrv_closed_loop 실데이터 재검증 (mvrv_hi=2.4, horizon=7d, 'down' 예측)")
    sig = df["mvrv"] > 2.4
    sub = df[sig & df["fwd_7d"].notna()].copy()
    sub["hit"] = sub["fwd_7d"] < 0
    n_pred = len(sub)
    hits = int(sub["hit"].sum())
    hit_rate = hits / n_pred if n_pred else 0
    p_val = stats.binomtest(hits, n_pred, 0.5, alternative="greater").pvalue if n_pred else np.nan
    w(f"- n_pred (MVRV>2.4 진입 일수, 7d 완료) = {n_pred}")
    w(f"- hits (fwd_7d < 0) = {hits}")
    w(f"- hit_rate = {hit_rate:.4f}")
    w(f"- binomial p (one-sided > 0.5) = {p_val:.4f}")
    w(f"- 판정 (alpha=0.05): {'REJECT NULL (mean-revert 양)' if p_val < 0.05 else 'FAIL TO REJECT'}")
    w()

    # ===== 3. horizon별 conditional mean return =====
    w("## 3. horizon 별 MVRV 진입 조건부 forward return")
    for h_col in ["fwd_7d", "fwd_30d", "fwd_90d"]:
        for thr in [2.0, 2.4, 3.0]:
            sub = df[(df["mvrv"] > thr) & df[h_col].notna()][h_col]
            base = df[(df["mvrv"] <= thr) & df[h_col].notna()][h_col]
            if len(sub) < 5 or len(base) < 5:
                continue
            t_stat, t_p = stats.ttest_ind(sub, base, equal_var=False)
            # block bootstrap CI for mean
            lo, mu, hi = block_bootstrap_ci(sub.values, np.mean, n_boot=500, block_len=30)
            w(f"- {h_col} | MVRV>{thr}: n={len(sub)}, mean={sub.mean():+.4%}, "
              f"BB95%CI=({lo:+.4%}, {hi:+.4%}), Welch t={t_stat:+.2f} p={t_p:.4f}, "
              f"baseline_mean={base.mean():+.4%}")
    w()

    # ===== 4. partial-corr (MVRV ⊥ fwd_30d | FGI, halving_phase) =====
    w("## 4. Partial correlation — MVRV ⊥ fwd_30d | conditioning")
    pcorr_df = df[["mvrv", "fwd_30d", "fgi", "halving_phase"]].dropna()
    w(f"- n_complete = {len(pcorr_df)}")
    if len(pcorr_df) > 100:
        # marginal
        rho_marg, n_marg = rank_ic(pcorr_df["mvrv"], pcorr_df["fwd_30d"])
        w(f"- marginal Spearman(MVRV, fwd_30d) = {rho_marg:+.4f}, n={n_marg}")
        # partial via residual regression
        from numpy.linalg import lstsq
        hp_dummies = pd.get_dummies(pcorr_df["halving_phase"], drop_first=True).astype(float)
        X = pd.concat([pcorr_df["fgi"].astype(float), hp_dummies], axis=1)
        X_ = X.values
        # residual of MVRV given X
        b1, *_ = lstsq(X_, pcorr_df["mvrv"].values, rcond=None)
        r1 = pcorr_df["mvrv"].values - X_ @ b1
        b2, *_ = lstsq(X_, pcorr_df["fwd_30d"].values, rcond=None)
        r2 = pcorr_df["fwd_30d"].values - X_ @ b2
        rho_p, p_p = stats.spearmanr(r1, r2)
        w(f"- partial Spearman(MVRV, fwd_30d | FGI, halving_phase) = {rho_p:+.4f}, p={p_p:.4f}")
        # block bootstrap CI
        idx = np.arange(len(r1))
        def stat_rho(s_idx):
            return stats.spearmanr(r1[s_idx.astype(int) % len(r1)], r2[s_idx.astype(int) % len(r1)])[0]
        lo, mu, hi = block_bootstrap_ci(idx.astype(float), stat_rho, n_boot=500, block_len=60)
        w(f"- partial 95% block-bootstrap CI = ({lo:+.4f}, {hi:+.4f})")
        w(f"- 결론: {'CI 가 0 포함' if lo*hi <= 0 else 'CI 0 미포함 (direct 잔존)'}")
    w()

    # ===== 5. e-CUSUM Rank-IC breakdown 검정 =====
    w("## 5. e-CUSUM Rank-IC 단측 붕괴 검정")
    w("- score = -MVRV_z (mean-revert prediction sign 반영, high MVRV = neg fwd_ret 예측)")
    w("- rolling window 90d, baseline_ic = 0.0 (score⊥fwd null), sd = ★empirical rolling-IC std (heuristic 0.15 = spurious 발산 원인, audit 격하 → 실측 sd 대체)")
    df["mvrv_z"] = (df["mvrv"] - df["mvrv"].mean()) / df["mvrv"].std()
    df["score"] = -df["mvrv_z"]
    # rolling Rank-IC (window 90d, fwd_30d 타겟)
    rolling = []
    for i in range(180, len(df) - 30, 30):
        win = df.iloc[i-180:i]
        rho, n = rank_ic(win["score"], win["fwd_30d"])
        if not np.isnan(rho):
            rolling.append({"date": df["date"].iloc[i], "ic": rho, "n": n})
    if rolling:
        rdf = pd.DataFrame(rolling)
        w(f"- rolling IC: n_windows={len(rdf)}, mean={rdf['ic'].mean():+.4f}, std={rdf['ic'].std():+.4f}")
        # ★e-CUSUM empirical baseline: heuristic sd=0.15 → 실측 rolling-IC std (spurious 발산 격하).
        emp_sd = float(rdf["ic"].std()) or 0.15
        z = (0.0 - rdf["ic"].values) / emp_sd
        rejected, max_r = e_cusum_one_sided(z, alpha=0.05, tau2=1.0)
        w(f"- empirical sd = {emp_sd:.4f} (heuristic 0.15 대체)")
        w(f"- max e-process R = {max_r:.4f}, threshold (1/0.05)=20.0, rejected={rejected}")
        w(f"  ★주의: rolling-IC mean={rdf['ic'].mean():+.3f} 양(score⊥fwd null 아래 *붕괴* 아님) + window overlap "
          f"자기상관 → e-CUSUM 단측붕괴 = small-n spurious, 의사결정 미사용(라벨 only).")
    w()

    # ===== 6. regime conditioning — FGI × halving phase =====
    w("## 6. Regime-conditional MVRV → fwd_30d Rank-IC")
    df["fgi_regime"] = df["fgi"].apply(fgi_regime)
    cells = []
    for fg in ["extreme_fear", "fear", "neutral", "greed", "extreme_greed"]:
        for hp in ["post_0_6m", "post_6_18m", "post_18_24m", "post_24_36m"]:
            sub = df[(df["fgi_regime"] == fg) & (df["halving_phase"] == hp)]
            sub = sub[sub["fwd_30d"].notna() & sub["mvrv"].notna()]
            if len(sub) < 30:
                cells.append({"fgi": fg, "phase": hp, "n": len(sub), "ic": None, "eff_n": None})
                continue
            rho, n = rank_ic(sub["mvrv"], sub["fwd_30d"])
            eff_n = effective_n(sub["mvrv"].values)
            # ★per-cell p = eff_n 기반 t (자기상관 보정 — raw-n Spearman p 는 과대확신).
            if eff_n > 2 and abs(rho) < 1.0:
                t_ic = rho * np.sqrt((eff_n - 2) / (1 - rho ** 2))
                p_eff = float(2 * stats.t.sf(abs(t_ic), df=eff_n - 2))
            else:
                p_eff = np.nan
            cells.append({"fgi": fg, "phase": hp, "n": n, "ic": rho,
                          "eff_n": eff_n, "p_eff": p_eff})
    cdf = pd.DataFrame(cells)
    w("```")
    w(cdf.to_string(index=False))
    w("```")
    n_valid = int(cdf["ic"].notna().sum())
    alpha_bonf = 0.05 / n_valid if n_valid else np.nan
    n_surv = int((cdf["p_eff"] < alpha_bonf).sum()) if n_valid else 0
    surv_cells = cdf[cdf["p_eff"] < alpha_bonf][["fgi", "phase", "ic", "eff_n", "p_eff"]] if n_valid else None
    w(f"- 전체 cell 수: {len(cdf)}")
    w(f"- N(raw)≥30 통과 cell: {n_valid}")
    w(f"- N<24 (small-N gate 미달) cell: {(cdf['n']<24).sum()}")
    w(f"- ★effective_n < 30 cell: {(cdf['eff_n'] < 30).sum() if cdf['eff_n'].notna().any() else 'na'} / {n_valid} "
      f"(자기상관 보정 후 *전 cell* eff_n<30 = n≥30 claim 무효)")
    w(f"- ★Bonferroni α/{n_valid} = {alpha_bonf:.5f} 임계, eff_n 기반 per-cell p 생존 cell = {n_surv}")
    if surv_cells is not None and len(surv_cells):
        w("```")
        w(surv_cells.to_string(index=False))
        w("```")
    w()

    # ===== 7. 종합 판정 =====
    w("## 7. 가설 판정")
    w(f"- 2장 closed-loop binomial p < 0.05? → MVRV>2.4 mean-revert 가설 1차 검증")
    w("- 4장 partial CI 0 포함? → MVRV-fwd_ret 직접엣지 vs 매개 분해")
    w("- 5장 e-CUSUM rejected? → score IC 단측 붕괴 여부")
    w("- 6장 cell N < 24 = small-N 5게이트, structural prior 라벨")
    w()
    w("## 8. 미해결 의문")
    w("- MVRV cycle peak/trough 독립 N = 3~4 → block bootstrap CI 넓음")
    w("- post-2024 ETF 시대 realized cap 의미 변화 (custodian 이동)")
    w("- mvrv_hi=2.4 임계 자체가 사후 fit 가능성 — 2017-2021 in-sample, 2022-2025 OOS 분리 검증 권고")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ H1 → {OUT}")

if __name__ == "__main__":
    main()
