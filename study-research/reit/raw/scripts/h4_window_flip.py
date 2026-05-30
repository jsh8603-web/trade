"""H4 (window flip meta-가설) validation.

Hypothesis: REIT sub-sector cross-sectional ranking is non-monotonic in window length.
Confirm: mean swap rate (>=1 tier difference) > 30% across window pairs.
Reject: Kendall tau > 0.7 across window pairs (consistent ranking).
"""
import sys
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import kendalltau

TICKERS = {
    'Industrial': 'PLD',     # Prologis
    'Apartment': 'AVB',       # AvalonBay
    'Office': 'BXP',          # Boston Properties
    'Healthcare': 'WELL',     # Welltower
    'Datacenter': 'EQIX',     # Equinix
    'Storage': 'PSA',         # Public Storage
    'Retail': 'SPG',          # Simon Property
    'Hotel': 'HST',           # Host Hotels
    'Specialty': 'AMT',       # American Tower (cell tower)
}

print("=== H4 Window Flip Validation (REIT sub-sector) ===", flush=True)
print(f"Tickers: {TICKERS}", flush=True)

data = yf.download(list(TICKERS.values()), start='2018-01-01', end='2026-05-29',
                   auto_adjust=True, progress=False)
prices = data['Close']
prices = prices.reindex(columns=[v for v in TICKERS.values()])
prices.columns = list(TICKERS.keys())
prices = prices.dropna(how='all')
print(f"Price data: {prices.index[0].date()} ~ {prices.index[-1].date()}, n_days={len(prices)}", flush=True)
print(f"Missing per ticker:\n{prices.isna().sum()}", flush=True)
prices = prices.dropna()
print(f"After dropna full rows: n_days={len(prices)}", flush=True)

WINDOWS = [1, 30, 90, 365, 730]  # trading days

def window_ret(anchor_idx, w):
    if anchor_idx < w:
        return None
    return (prices.iloc[anchor_idx] / prices.iloc[anchor_idx - w] - 1.0)

# Monthly anchors (last trading day of month) 2020-01 ~ 2026-05
month_end_dates = prices.resample('ME').last().index
month_end_idx = [prices.index.get_indexer([d], method='nearest')[0] for d in month_end_dates]
# Filter to 2020-01 onwards
month_end_idx = [i for i in month_end_idx if prices.index[i] >= pd.Timestamp('2020-01-31')]
print(f"Anchors (month-end): {len(month_end_idx)} from {prices.index[month_end_idx[0]].date()} to {prices.index[month_end_idx[-1]].date()}", flush=True)

records = []
for ai in month_end_idx:
    ranks = {}
    for w in WINDOWS:
        r = window_ret(ai, w)
        if r is None or r.isna().any():
            continue
        ranks[w] = r.rank(ascending=False).astype(int).values
    if len(ranks) >= 2:
        records.append((prices.index[ai], ranks))

# Pair comparisons
pairs = [(1, 30), (30, 90), (90, 365), (365, 730), (1, 365), (30, 730), (1, 730)]
print()
print(f"{'Window pair':<22} {'n':>5} {'mean τ':>9} {'std τ':>9} {'mean swap%':>13} {'frac swap>=2 tier':>20}")
print("-" * 80)
for w1, w2 in pairs:
    taus, swaps, big_swaps = [], [], []
    for d, ranks in records:
        if w1 not in ranks or w2 not in ranks:
            continue
        r1, r2 = ranks[w1], ranks[w2]
        tau, _ = kendalltau(r1, r2)
        if np.isnan(tau):
            continue
        taus.append(tau)
        diff = np.abs(r1 - r2)
        swaps.append((diff >= 1).mean())          # 1+ tier swap
        big_swaps.append((diff >= 2).mean())       # 2+ tier (more strict)
    if taus:
        print(f"{w1:>4}d vs {w2:>4}d{'':<10} {len(taus):>5} {np.mean(taus):>9.3f} {np.std(taus):>9.3f} "
              f"{np.mean(swaps)*100:>12.1f}% {np.mean(big_swaps)*100:>19.1f}%")

# Per-sector flip frequency (specific evidence)
print()
print("=== Per-sector window flip frequency (1d vs 365d ranking absolute change distribution) ===")
diffs = {s: [] for s in TICKERS.keys()}
for d, ranks in records:
    if 1 in ranks and 365 in ranks:
        for i, s in enumerate(TICKERS.keys()):
            diffs[s].append(abs(int(ranks[1][i]) - int(ranks[365][i])))
print(f"{'Sector':<15} {'n':>5} {'mean |Δrank|':>15} {'frac |Δ|>=3':>13}")
print("-" * 55)
for s, ds in diffs.items():
    if ds:
        print(f"{s:<15} {len(ds):>5} {np.mean(ds):>15.2f} {(np.array(ds)>=3).mean()*100:>12.1f}%")

print()
print("=== H4 verdict ===")
mean_tau_short_long = np.mean([t for (w1,w2) in [(1,365),(30,730),(1,730)]
                                for d,r in records if w1 in r and w2 in r
                                for t in [kendalltau(r[w1], r[w2])[0]] if not np.isnan(t)])
mean_swap_short_long = np.mean([(np.abs(r[w1]-r[w2])>=1).mean() for (w1,w2) in [(1,365),(30,730),(1,730)]
                                 for d,r in records if w1 in r and w2 in r])
print(f"Mean Kendall τ (short vs long window pairs): {mean_tau_short_long:.3f}")
print(f"Mean swap rate (>=1 tier): {mean_swap_short_long*100:.1f}%")
if mean_swap_short_long > 0.30 and mean_tau_short_long < 0.7:
    print("→ H4 CONFIRMED: window flip evidence (swap > 30% + τ < 0.7)")
else:
    print(f"→ H4 inconclusive or partial reject")
