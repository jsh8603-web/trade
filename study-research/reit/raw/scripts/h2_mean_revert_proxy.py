"""H2 mean-reversion validation — VNQ proxy approach.

Direct H2 hypothesis: implied cap rate − private appraisal spread Z < -1.5 → 12m fwd Rank-IC > +0.15.
Primary spread time-series sparse (n=4 quarters confirmed). Use VNQ price-level Z-score as PROXY
for REIT undervaluation mean-reversion mechanism.

VNQ proxy logic: when VNQ price is significantly below its trailing 24m mean (Z<-1.5), it implies
either:
  (a) REIT discount widened (analogous to cap rate spread expansion), or
  (b) elevated risk discount → rebound mechanism
forward 12m total return positive expectation if mean-reversion holds.
"""
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr

print("=== H2 Mean-Reversion (VNQ Proxy) Validation ===", flush=True)

# Fetch VNQ (Vanguard Real Estate ETF — broad REIT proxy) and FTSE NAREIT All Equity (use VNQ as primary)
data = yf.download(['VNQ'], start='2005-01-01', end='2026-05-29', auto_adjust=True, progress=False)
prices = data['Close']
if isinstance(prices, pd.DataFrame):
    prices = prices['VNQ']
print(f"VNQ data: {prices.index[0].date()} ~ {prices.index[-1].date()}, n={len(prices)}", flush=True)

# Log return cumulative for stability
log_p = np.log(prices)

# 24-month (504 trading days) rolling mean + std of log price level
ROLL = 504
mu = log_p.rolling(ROLL).mean()
sd = log_p.rolling(ROLL).std()
z = (log_p - mu) / sd

# 12-month forward total return (252 trading days)
FWD = 252
fwd_ret = (prices.shift(-FWD) / prices) - 1.0

# Filter to non-NA both
df = pd.DataFrame({'z': z, 'fwd_ret': fwd_ret}).dropna()
print(f"Effective sample (both z + fwd defined): n={len(df)}", flush=True)
print(f"z range: [{df['z'].min():.2f}, {df['z'].max():.2f}], mean={df['z'].mean():.2f}", flush=True)

# Verdict by bucket: z < -1.5 (deep discount), -1.5..-0.5, -0.5..0.5, 0.5..1.5, > 1.5
def bucket(zv):
    if zv < -1.5: return 'A_z<-1.5_DEEP_DISC'
    if zv < -0.5: return 'B_z[-1.5,-0.5)_MILD_DISC'
    if zv < 0.5:  return 'C_z[-0.5,0.5)_NEUTRAL'
    if zv < 1.5:  return 'D_z[0.5,1.5)_MILD_PREM'
    return 'E_z>=1.5_DEEP_PREM'

df['bucket'] = df['z'].apply(bucket)
print()
print("=== Bucket-conditional 12m forward total return (mean / median / n) ===")
print(f"{'bucket':<28} {'n':>5} {'mean fwd%':>12} {'med fwd%':>12} {'frac>0':>9}")
print("-" * 70)
for b in sorted(df['bucket'].unique()):
    g = df[df['bucket'] == b]['fwd_ret']
    if len(g) > 0:
        print(f"{b:<28} {len(g):>5} {g.mean()*100:>11.1f}% {g.median()*100:>11.1f}% "
              f"{(g>0).mean()*100:>8.1f}%")

# Whole-sample Rank-IC (Spearman z vs fwd_ret)
rho, p = spearmanr(df['z'], df['fwd_ret'])
print(f"\nSpearman Rank-IC (z vs 12m fwd ret), n={len(df)}: rho={rho:+.3f} p={p:.4f}")
print("(Negative rho expected if mean-reversion holds: low z → high fwd ret)")

# Deep discount focused — z < -1.5 events
deep = df[df['z'] < -1.5]
print()
print(f"=== Deep discount events (z < -1.5) ===")
print(f"n events (daily granularity): {len(deep)}")
if len(deep) > 0:
    # Group consecutive deep events as 'episodes' (gap > 60 trading days = new episode)
    deep_sorted = deep.sort_index()
    gaps = deep_sorted.index.to_series().diff().dt.days
    episode_starts = (gaps > 90) | gaps.isna()
    n_episodes = episode_starts.sum()
    print(f"n distinct episodes (>=90d gap): {n_episodes}")
    print(f"Mean 12m fwd return in deep discount: {deep['fwd_ret'].mean()*100:+.1f}%")
    print(f"Median: {deep['fwd_ret'].median()*100:+.1f}%")
    print(f"Fraction positive: {(deep['fwd_ret']>0).mean()*100:.1f}%")
    # Sample episode starts
    print("\nSample deep-discount episode starts:")
    starts = deep_sorted.index[episode_starts.fillna(True)]
    for s in starts[:10]:
        z_at = df.loc[s, 'z']
        fwd_at = df.loc[s, 'fwd_ret']
        print(f"  {s.date()}  z={z_at:+.2f}  fwd12m={fwd_at*100:+.1f}%")

# Premium analogue
prem = df[df['z'] > 1.5]
print(f"\n=== Deep premium events (z > 1.5) ===")
print(f"n: {len(prem)}, mean 12m fwd: {prem['fwd_ret'].mean()*100:+.1f}% (negative = mean-revert from premium expected)")

print()
print("=== H2 verdict (proxy via VNQ price Z-score, NOT exact cap rate spread) ===")
print(f"Whole-sample Spearman Rank-IC (z vs 12m fwd ret): {rho:+.3f}")
deep_mean = deep['fwd_ret'].mean() if len(deep) > 0 else None
if deep_mean is not None:
    print(f"Deep-discount (z<-1.5) mean 12m fwd ret: {deep_mean*100:+.1f}% over {len(deep)} obs")
print()
print("Note: This is a PRICE-LEVEL proxy, not exact implied-private cap rate spread.")
print("Direct cap rate spread time series requires Nareit T-tracker Excel direct download (TODO).")
print("Primary-confirmed spread anchors (sparse): Q3'22=243bp, Q4'23=123bp, Q2'24=130bp, Q3'24=60bp est.")
