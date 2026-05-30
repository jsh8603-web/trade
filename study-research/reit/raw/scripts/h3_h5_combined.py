"""H3 + H5 combined validation (sector-level proxy, regime-conditional).

H3 (debt maturity stratify): ticker-level debt WAM unavailable without EDGAR text NLP.
Use sector-average debt WAM proxy (practitioner standard) + rate-shock window. Limited power.

H5 (sub-sector x regime mapping 반증 잔여): regime label (FRED-based Investment Clock proxy)
x sub-sector cross-section consistency. 2018-2024 yearly Rank-IC matrix.

⛔ Synthetic/simulated data NOT used — Yahoo prices + FRED real GDP/CPI/DGS10 only.
"""
import sys, io
import numpy as np
import pandas as pd
import yfinance as yf
import urllib.request
from scipy.stats import spearmanr

# 9 sub-sectors with Yahoo ticker + sector-average debt WAM proxy (practitioner standard, years)
TICKERS = {
    'Healthcare': ('WELL', 7.0),   # Healthcare REITs typical debt WAM ~7y
    'Datacenter': ('EQIX', 5.5),    # Datacenter ~5-6y
    'Specialty':  ('AMT',  6.0),    # Cell tower ~6y
    'Retail':     ('SPG',  6.5),    # Retail REITs ~6-7y
    'Office':     ('BXP',  6.0),    # Office ~6y
    'Industrial': ('PLD',  6.0),    # Industrial ~6y
    'Apartment':  ('AVB',  7.0),    # Apartment (long mortgage) ~7y
    'Hotel':      ('HST',  4.5),    # Hotel/CMBS heavier ~4-5y
    'Storage':    ('PSA',  6.0),    # Storage ~6y
}

print("=" * 70, flush=True)
print("=== H3 + H5 Combined Validation (sector proxy, regime-conditional) ===", flush=True)
print("=" * 70, flush=True)

# --- Fetch FRED macro ---
def fred_csv(sid):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
    req = urllib.request.Request(url, headers={'User-Agent': 'reit-study/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        df = pd.read_csv(io.BytesIO(r.read()))
    df.columns = [c.strip() for c in df.columns]
    date_col = 'observation_date' if 'observation_date' in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col])
    df.set_index(date_col, inplace=True)
    vcol = sid if sid in df.columns else df.columns[0]
    df[vcol] = pd.to_numeric(df[vcol], errors='coerce')
    return df[[vcol]].rename(columns={vcol: sid.lower()}).dropna()

dgs10 = fred_csv('DGS10')
print(f"DGS10: {dgs10.index[0].date()} ~ {dgs10.index[-1].date()}, n={len(dgs10)}", flush=True)
# GDP growth proxy: YoY change in real GDP (GDPC1, quarterly) -> daily ffill
gdp = fred_csv('GDPC1')
gdp_yoy = (gdp['gdpc1'].pct_change(4) * 100).dropna()
print(f"Real GDP YoY: n={len(gdp_yoy)}, last={gdp_yoy.iloc[-1]:.2f}%", flush=True)
# CPI proxy: YoY change in CPI-U (CPIAUCSL)
cpi = fred_csv('CPIAUCSL')
cpi_yoy = (cpi['cpiaucsl'].pct_change(12) * 100).dropna()
print(f"CPI YoY: n={len(cpi_yoy)}, last={cpi_yoy.iloc[-1]:.2f}%", flush=True)

# --- Fetch prices ---
tlist = [v[0] for v in TICKERS.values()]
data = yf.download(tlist, start='2018-01-01', end='2026-05-29', auto_adjust=True, progress=False)
prices = data['Close'].reindex(columns=tlist)
prices.columns = list(TICKERS.keys())
prices = prices.dropna()
print(f"Price data: {prices.index[0].date()} ~ {prices.index[-1].date()}, n={len(prices)}", flush=True)

# ====================================================================
# H3: debt-WAM cross-section in rate-shock window (60d forward)
# ====================================================================
print()
print("=" * 70, flush=True)
print("=== H3: debt WAM cross-section in rate-shock window ===", flush=True)
print("=" * 70, flush=True)

debt_wam = np.array([TICKERS[s][1] for s in prices.columns])
debt_wam_rank = pd.Series(debt_wam, index=prices.columns).rank(ascending=False)
print(f"Debt WAM (years, sector-avg proxy): {dict(zip(prices.columns, debt_wam))}", flush=True)
print(f"Debt WAM rank (1=longest): {debt_wam_rank.to_dict()}", flush=True)

dgs_aligned = dgs10['dgs10'].reindex(prices.index, method='ffill')
dgs_4w_chg_bp = (dgs_aligned - dgs_aligned.shift(20)) * 100
shock_today = (dgs_4w_chg_bp > 50.0)
shock_entry = shock_today & ~shock_today.shift(1).fillna(False).infer_objects(copy=False)
entry_dates = dgs_4w_chg_bp.index[shock_entry]
print(f"Rate-shock entries: n={len(entry_dates)}", flush=True)

FWD = 60
h3_ics = []
for ed in entry_dates:
    idx = prices.index.get_indexer([ed], method='nearest')[0]
    if idx + FWD >= len(prices):
        continue
    fwd_ret = prices.iloc[idx + FWD] / prices.iloc[idx] - 1.0
    fwd_rank = fwd_ret.rank(ascending=False)
    rho, _ = spearmanr(debt_wam_rank.values, fwd_rank.values)
    if not np.isnan(rho):
        h3_ics.append(rho)

if h3_ics:
    print(f"H3 mean Rank-IC (debt_WAM_rank vs fwd_{FWD}d_return_rank), n={len(h3_ics)}: "
          f"{np.mean(h3_ics):+.3f}")
    print(f"std: {np.std(h3_ics):.3f}, median: {np.median(h3_ics):+.3f}, "
          f"frac_negative: {sum(1 for ic in h3_ics if ic < 0)/len(h3_ics)*100:.1f}%")
    se = np.std(h3_ics)/np.sqrt(len(h3_ics))
    z = np.mean(h3_ics)/se if se > 0 else float('nan')
    print(f"Approx z (mean/SE): {z:+.2f}")
    print()
    if np.mean(h3_ics) > 0.05:
        print(f"=> H3 CONFIRMED: long-WAM REITs OUTPERFORM in rate-shock (mean +{np.mean(h3_ics):.3f})")
    elif np.mean(h3_ics) < -0.05:
        print(f"=> H3 REJECTED: long-WAM underperform (sign mismatch from hypothesis +)")
    else:
        print(f"=> H3 INCONCLUSIVE: |mean Rank-IC| < 0.05. Limited power due to narrow WAM range "
              f"({debt_wam.min()}y - {debt_wam.max()}y).")
    print(f"Caveat: sector-average debt WAM proxy = range only {debt_wam.max()-debt_wam.min():.1f}y. "
          "Ticker-level WAM via EDGAR NLP for tighter test.")

# ====================================================================
# H5: regime-conditional sub-sector ranking consistency
# ====================================================================
print()
print("=" * 70, flush=True)
print("=== H5: regime x sub-sector cross-section Rank-IC matrix ===", flush=True)
print("=" * 70, flush=True)

# Build regime label per quarter from GDP YoY + CPI YoY (FRED quarterly + monthly)
# Investment Clock 5 regimes (simplified):
#   Reflation: gdp_yoy > 2, cpi_yoy < 3 (growth up, inflation low)
#   Recovery:  gdp_yoy > 2, 3 <= cpi_yoy < 5
#   Overheat:  gdp_yoy > 2, cpi_yoy >= 5
#   Stagflation: gdp_yoy <= 2, cpi_yoy >= 3
#   Recession: gdp_yoy <= 0 (any inflation)
def regime_label(g, c):
    if pd.isna(g) or pd.isna(c):
        return None
    if g <= 0:
        return 'Recession'
    if g > 2 and c < 3:
        return 'Reflation'
    if g > 2 and c < 5:
        return 'Recovery'
    if g > 2 and c >= 5:
        return 'Overheat'
    if g <= 2 and c >= 3:
        return 'Stagflation'
    return 'Mid'

# Resample to quarterly + label
gdp_q = gdp_yoy.resample('QE').last()
cpi_q = cpi_yoy.resample('QE').last()
common_q = gdp_q.index.intersection(cpi_q.index)
labels = pd.Series([regime_label(gdp_q[d], cpi_q[d]) for d in common_q], index=common_q)
labels_in_sample = labels[labels.index >= '2018-01-01']
print(f"Regime labels (quarterly, 2018+): n={len(labels_in_sample)}", flush=True)
print(f"Regime distribution:\n{labels_in_sample.value_counts()}", flush=True)

# Per regime, gather all sub-sector quarterly total return + rank
prices_q_last = prices.resample('QE').last()
prices_q_first = prices.resample('QE').first()
q_ret = (prices_q_last / prices_q_first - 1.0).dropna()

regime_returns = {}
for q, lbl in labels_in_sample.items():
    if lbl is None: continue
    if q not in q_ret.index: continue
    if lbl not in regime_returns:
        regime_returns[lbl] = []
    regime_returns[lbl].append(q_ret.loc[q])

print()
print("=== Per-regime average rank by sub-sector (1 = best, 9 = worst) ===")
print(f"{'Regime':<14} {'n_q':>4} ", end='')
for s in prices.columns:
    print(f"{s:>11}", end='')
print()
print("-" * (18 + 11 * len(prices.columns)))
regime_ranks = {}
for lbl, rets in regime_returns.items():
    df_r = pd.DataFrame(rets)
    avg_rank = df_r.rank(axis=1, ascending=False).mean()
    regime_ranks[lbl] = avg_rank
    print(f"{lbl:<14} {len(rets):>4} ", end='')
    for s in prices.columns:
        print(f"{avg_rank[s]:>11.2f}", end='')
    print()

# Pairwise regime consistency (Spearman of avg ranks across regimes)
print()
print("=== Pairwise regime rank Spearman consistency ===")
regs = list(regime_ranks.keys())
for i, r1 in enumerate(regs):
    for r2 in regs[i+1:]:
        rho, p = spearmanr(regime_ranks[r1].values, regime_ranks[r2].values)
        print(f"  {r1:<14} vs {r2:<14}: rho={rho:+.3f}  p={p:.3f}")

# Overall H5 verdict: regime mapping consistency
# If sub-sector ranking is SAME across regimes -> regime label has no information
# If different -> single mapping is partial (sector x regime conditional)
rhos = []
for i, r1 in enumerate(regs):
    for r2 in regs[i+1:]:
        rho, _ = spearmanr(regime_ranks[r1].values, regime_ranks[r2].values)
        if not np.isnan(rho):
            rhos.append(rho)
if rhos:
    print()
    print(f"Mean inter-regime Spearman rho: {np.mean(rhos):+.3f}")
    if np.mean(rhos) > 0.7:
        print("=> regimes produce CONSISTENT sub-sector rankings (regime label adds little info)")
    elif np.mean(rhos) < 0.3:
        print("=> H5 CONFIRMED: regimes produce DIVERGENT rankings (regime label matters BUT not "
              "single static mapping)")
    else:
        print("=> H5 PARTIAL: some regime conditioning, but not strong (mean rho in 0.3-0.7)")
print()
print("Note: 'Reflation' rank for industrial is the key v1 hypothesis test point.")
