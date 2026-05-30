"""H2 funding cascade — 실데이터 검증.

가설: |funding| > 95th percentile (8h) -> 24/72h 가격 급변 (cascade)
반증조건:
  - hit rate < 0.5, binomial p > 0.05
  - partial-corr(funding, fwd_24h | RSI, OI_change) 95% CI 0 포함
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import pandas as pd
from scipy import stats
from lib_common import (
    load_funding, load_btc_klines, rank_ic, e_cusum_one_sided, block_bootstrap_ci, effective_n
)

OUT = Path(__file__).resolve().parent.parent / "raw" / "validation-h2-funding.md"

def main():
    fund = load_funding()
    klines = load_btc_klines()
    klines["log_ret_1d"] = np.log(klines["close"]/klines["close"].shift(1))
    klines["log_ret_3d"] = np.log(klines["close"].shift(-3)/klines["close"])  # fwd 3d (~72h)
    klines["log_ret_1d_fwd"] = np.log(klines["close"].shift(-1)/klines["close"])

    lines = []
    def w(s=""): lines.append(s)

    w("# H2 Funding cascade -- 실데이터 검증")
    w()
    w(f"as_of: {pd.Timestamp.utcnow().isoformat()}")
    w(f"funding: Binance BTCUSDT 8h, n={len(fund)}, {fund['datetime'].min()} ~ {fund['datetime'].max()}")
    w(f"klines: Binance BTCUSDT daily, n={len(klines)}, {klines['date'].min().date()} ~ {klines['date'].max().date()}")
    w()

    # ===== 1. funding 분포 =====
    w("## 1. Funding rate 8h 분포")
    desc = fund["funding_rate"].describe(percentiles=[0.01, 0.05, 0.5, 0.95, 0.99])
    w("```")
    w(desc.to_string())
    w("```")
    p95 = fund["funding_rate"].abs().quantile(0.95)
    p99 = fund["funding_rate"].abs().quantile(0.99)
    w(f"- |funding| 95th percentile = {p95:.6f}")
    w(f"- |funding| 99th percentile = {p99:.6f}")
    w(f"- direction.md 임계 0.05%/8h = 0.0005 비교: {(fund['funding_rate'].abs() > 0.0005).mean():.4%} 의 시점이 0.0005 초과")
    w()

    # ===== 2. event study: |funding| > p95 -> 72h forward return =====
    w("## 2. Event study -- |funding| > 95th percentile 진입 시점의 fwd 24h/72h return")
    fund["abs_funding"] = fund["funding_rate"].abs()
    fund["date"] = fund["datetime"].dt.normalize()
    # daily aggregate
    daily_f = fund.groupby("date").agg(
        funding_mean=("funding_rate", "mean"),
        funding_max=("funding_rate", "max"),
        funding_min=("funding_rate", "min"),
        absmax=("abs_funding", "max"),
    ).reset_index()
    # merge with klines
    m = klines.merge(daily_f, on="date", how="inner")
    p95_d = m["absmax"].quantile(0.95)
    p99_d = m["absmax"].quantile(0.99)
    w(f"- daily absmax p95 = {p95_d:.6f}, p99 = {p99_d:.6f}")

    for thr_label, thr_val in [("p95", p95_d), ("p99", p99_d), ("abs>0.0005", 0.0005)]:
        sub = m[(m["absmax"] > thr_val) & m["log_ret_1d_fwd"].notna()]
        base = m[(m["absmax"] <= thr_val) & m["log_ret_1d_fwd"].notna()]
        if len(sub) < 5:
            continue
        # event signed: funding 양 -> negative fwd ret 예상 (cascade)
        sub_long = sub[sub["funding_mean"] > 0]
        sub_short = sub[sub["funding_mean"] < 0]
        w(f"- {thr_label}: n={len(sub)}, fwd_1d mean={sub['log_ret_1d_fwd'].mean():+.4%}, "
          f"fwd_3d mean={sub['log_ret_3d'].mean():+.4%}, "
          f"baseline_1d={base['log_ret_1d_fwd'].mean():+.4%}")
        if len(sub_long) >= 5:
            w(f"  - extreme LONG funding (mean>0): n={len(sub_long)}, fwd_1d={sub_long['log_ret_1d_fwd'].mean():+.4%} (cascade 가설 = neg 기대)")
            t, tp = stats.ttest_1samp(sub_long["log_ret_1d_fwd"].dropna(), 0, alternative="less")
            w(f"    t-stat={t:+.2f}, p(<0)={tp:.4f}")
        if len(sub_short) >= 5:
            w(f"  - extreme SHORT funding (mean<0): n={len(sub_short)}, fwd_1d={sub_short['log_ret_1d_fwd'].mean():+.4%} (squeeze 가설 = pos 기대)")
            t, tp = stats.ttest_1samp(sub_short["log_ret_1d_fwd"].dropna(), 0, alternative="greater")
            w(f"    t-stat={t:+.2f}, p(>0)={tp:.4f}")
    w()

    # ===== 3. binomial test (cascade hit rate) =====
    w("## 3. Cascade binomial test -- extreme long funding 진입 후 fwd_3d < 0 확률")
    for thr_label, thr_val in [("absmax_p95+long", p95_d), ("absmax_p99+long", p99_d)]:
        sub = m[(m["absmax"] > thr_val) & (m["funding_mean"] > 0) & m["log_ret_3d"].notna()]
        n = len(sub)
        if n < 5:
            continue
        hits = int((sub["log_ret_3d"] < 0).sum())
        rate = hits / n
        p = stats.binomtest(hits, n, 0.5, alternative="greater").pvalue
        w(f"- {thr_label}: n={n}, hits(fwd_3d<0)={hits}, rate={rate:.4f}, binomial p (one-sided > 0.5) = {p:.4f}")
    w()

    # ===== 4. Spearman rank-IC funding vs fwd_3d =====
    w("## 4. Spearman Rank-IC funding -> forward return (전체 기간)")
    for horizon, col in [("fwd_1d", "log_ret_1d_fwd"), ("fwd_3d", "log_ret_3d")]:
        rho, n = rank_ic(m["funding_mean"], m[col])
        w(f"- {horizon}: Rank-IC = {rho:+.4f}, n={n}")
        # block bootstrap CI
        valid = m[[col, "funding_mean"]].dropna()
        if len(valid) > 200:
            def stat_rho(idx):
                idx = np.asarray(idx, dtype=int) % len(valid)
                return stats.spearmanr(valid["funding_mean"].values[idx], valid[col].values[idx])[0]
            lo, mu, hi = block_bootstrap_ci(np.arange(len(valid)).astype(float), stat_rho, n_boot=300, block_len=30)
            w(f"  block-bootstrap 95% CI = ({lo:+.4f}, {hi:+.4f})")
    w()

    # ===== 5. effective N =====
    w("## 5. Effective N (autocorr-adjusted)")
    eff_funding = effective_n(m["funding_mean"].values)
    eff_ret = effective_n(m["log_ret_1d_fwd"].dropna().values)
    w(f"- funding_mean: raw N={m['funding_mean'].notna().sum()}, effective N={eff_funding:.1f}")
    w(f"- fwd_1d log_ret: raw N={m['log_ret_1d_fwd'].notna().sum()}, effective N={eff_ret:.1f}")
    w()

    w("## 6. 가설 판정")
    w("- 2장 event study cascade (extreme long -> neg 3d) p<0.05 -> 가설 1차 검증")
    w("- 3장 binomial hit rate < 0.5 + p > 0.05 -> 가설 기각")
    w("- 4장 marginal Rank-IC 부호 = funding -> fwd_ret 방향")
    w()
    w("## 7. 미해결 의문")
    w("- funding 8h -> daily aggregate 시 정보 손실 (intra-day cascade 미포착)")
    w("- p95/p99 임계 자체가 sample-fit; OOS 분리 검증 필요")
    w("- OI history 30d 만 가용 (Binance public) -> conditioning_set [RSI, OI] 부분 검증 한계")
    w("- 2022 LUNA / FTX 같은 비대칭 이벤트 outlier 영향 (block bootstrap 으로 부분 완화)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] H2 -> {OUT}")

if __name__ == "__main__":
    main()
