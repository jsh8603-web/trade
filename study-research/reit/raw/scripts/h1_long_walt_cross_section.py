"""H1 (long-WALT cross-section rate-shock underperformance) validation.

Hypothesis: After rate-shock window entry (DGS10 4w Δ > +50bp), 90d forward,
long-WALT REIT < short-WALT REIT cross-sectional return.
Confirm: cross-section Rank-IC (WALT_rank vs fwd_60d_return) < -0.05 on average.
Reject: Rank-IC e-CUSUM-equivalent positive (sign mismatch).

WALT sector-average proxy (NAREIT/practitioner standard):
  Healthcare 12y > Datacenter 8y > Specialty 8y > Retail 7y > Office 6y >
  Industrial 5y > Apartment 1y, Hotel 1y, Storage 1y (month-to-month)
"""
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr
import urllib.request, io

TICKERS = {
    'Healthcare': ('WELL', 12.0),
    'Datacenter': ('EQIX', 8.0),
    'Specialty':  ('AMT',  8.0),
    'Retail':     ('SPG',  7.0),
    'Office':     ('BXP',  6.0),
    'Industrial': ('PLD',  5.0),
    'Apartment':  ('AVB',  1.0),
    'Hotel':      ('HST',  1.0),
    'Storage':    ('PSA',  1.0),
}

print("=== H1 Long-WALT Cross-section Rate-shock Validation ===", flush=True)

# Fetch DGS10 from FRED (CSV public endpoint)
fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"
print(f"Fetching FRED DGS10 from: {fred_url}", flush=True)
req = urllib.request.Request(fred_url, headers={'User-Agent': 'reit-study/1.0'})
with urllib.request.urlopen(req, timeout=30) as r:
    csv_bytes = r.read()
dgs = pd.read_csv(io.BytesIO(csv_bytes))
dgs.columns = [c.strip() for c in dgs.columns]
date_col = 'observation_date' if 'observation_date' in dgs.columns else dgs.columns[0]
value_col = 'DGS10' if 'DGS10' in dgs.columns else dgs.columns[1]
dgs[date_col] = pd.to_datetime(dgs[date_col])
dgs.set_index(date_col, inplace=True)
dgs[value_col] = pd.to_numeric(dgs[value_col], errors='coerce')
dgs = dgs[[value_col]].rename(columns={value_col: 'dgs10'}).dropna()
print(f"DGS10 sample: {dgs.index[0].date()} ~ {dgs.index[-1].date()}, n={len(dgs)}", flush=True)

tickers_list = [t[0] for t in TICKERS.values()]
data = yf.download(tickers_list, start='2018-01-01', end='2026-05-29',
                   auto_adjust=True, progress=False)
prices = data['Close'].reindex(columns=tickers_list)
prices.columns = list(TICKERS.keys())
prices = prices.dropna()
print(f"Price data: {prices.index[0].date()} ~ {prices.index[-1].date()}, n={len(prices)}", flush=True)

# WALT rank vector (high to low) — same order as columns
walt_years = np.array([TICKERS[s][1] for s in prices.columns])
walt_rank = pd.Series(walt_years, index=prices.columns).rank(ascending=False)
print(f"WALT (years): {dict(zip(prices.columns, walt_years))}", flush=True)
print(f"WALT rank (1=longest): {walt_rank.to_dict()}", flush=True)

# Rate-shock window: DGS10 over 4-week (20 trading days) rolling change
dgs_aligned = dgs['dgs10'].reindex(prices.index, method='ffill')
dgs_4w_chg_bp = (dgs_aligned - dgs_aligned.shift(20)) * 100  # rate diff in bp

# Identify rate-shock entry dates: DGS10 4w Δ > +50bp first crossing
SHOCK_BP = 50.0
shock_today = (dgs_4w_chg_bp > SHOCK_BP)
shock_entry = shock_today & ~shock_today.shift(1).fillna(False)
entry_dates = dgs_4w_chg_bp.index[shock_entry]
print(f"Rate-shock entry dates (DGS10 4w Δ > {SHOCK_BP}bp first crossings): n={len(entry_dates)}", flush=True)
if len(entry_dates) <= 30:
    for d in entry_dates:
        print(f"  {d.date()}  4w_Δ={dgs_4w_chg_bp.loc[d]:.0f}bp", flush=True)

# For each entry: 60d / 90d forward return cross-section
FWD_DAYS = 60
results = []
for ed in entry_dates:
    if ed not in prices.index:
        idx = prices.index.get_indexer([ed], method='nearest')[0]
    else:
        idx = prices.index.get_loc(ed)
    if idx + FWD_DAYS >= len(prices):
        continue
    fwd_ret = prices.iloc[idx + FWD_DAYS] / prices.iloc[idx] - 1.0
    fwd_rank = fwd_ret.rank(ascending=False)
    rho, p = spearmanr(walt_rank.values, fwd_rank.values)
    results.append({
        'entry_date': ed.date(),
        'shock_bp': dgs_4w_chg_bp.loc[ed],
        'fwd_ret': fwd_ret.to_dict(),
        'rank_ic': rho,
        'p_value': p,
    })

print()
print(f"=== Per-entry Rank-IC (WALT_rank vs fwd_{FWD_DAYS}d_return_rank, n_sectors=9) ===")
print(f"{'entry':<12} {'shock_bp':>10} {'Rank-IC':>10} {'p':>8}")
print("-" * 45)
ics = []
for r in results:
    print(f"{str(r['entry_date']):<12} {r['shock_bp']:>9.0f}  {r['rank_ic']:>+9.3f} {r['p_value']:>8.3f}")
    ics.append(r['rank_ic'])

print()
print(f"Total rate-shock entries: {len(ics)}")
if ics:
    print(f"Mean Rank-IC: {np.mean(ics):+.3f}")
    print(f"Std  Rank-IC: {np.std(ics):.3f}")
    print(f"Median:        {np.median(ics):+.3f}")
    print(f"Min/Max:       {min(ics):+.3f} / {max(ics):+.3f}")
    print(f"Fraction negative: {sum(1 for ic in ics if ic < 0)/len(ics)*100:.1f}%")
    # Block-bootstrap-ish via simple std-of-mean approx
    se = np.std(ics) / np.sqrt(len(ics))
    z = np.mean(ics) / se if se > 0 else float('nan')
    print(f"Approx z (mean/SE): {z:+.2f}")

print()
print("=== H1 verdict ===")
mean_ic = np.mean(ics) if ics else None
if mean_ic is not None:
    if mean_ic < -0.05:
        print(f"→ H1 CONFIRMED: mean Rank-IC {mean_ic:+.3f} < -0.05 (long-WALT underperform after rate-shock)")
    elif mean_ic > 0.05:
        print(f"→ H1 REJECTED: mean Rank-IC {mean_ic:+.3f} > +0.05 (sign mismatch — long-WALT outperform!)")
    else:
        print(f"→ H1 INCONCLUSIVE: mean Rank-IC {mean_ic:+.3f} in [-0.05, +0.05] (no strong direction)")
else:
    print("→ No rate-shock entry dates; cannot test")
