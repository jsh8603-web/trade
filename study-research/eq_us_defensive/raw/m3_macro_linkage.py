"""eq_us_defensive — M3 거시연관 산출.
study-research/macro/timeline.md §4 가이드 따름:
  1. regime/epoch 별 sleeve 수익률 분해
  2. sleeve ~ [rate, dollar, credit, oil] 거시 driver loading 회귀 (β + R²)
  3. cross-asset-class vs within-sleeve 구분 메모
  4. main M4 factor seed 입력

Epoch (timeline §3):
  E1 긴축충격     2022Q1~Q3   (rate↑↑·dollar↑↑·risk-off)
  E2 전환·반등    2022Q4~2023Q2 (rate 고원→완화초입)
  E3 금리재상승   2023Q3       (rate↑·oil↑)
  E4 pivot·인하   2023Q4~2024Q4 (rate↓·dollar↓)
  E0 pre-epoch    ~2021Q4 이전 (baseline)
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr

ROOT = Path('D:/projects/Inv/study-research/eq_us_defensive/raw')
fred = ROOT / 'fred'
yfin = ROOT / 'yfinance'

def load_fred(t):
    df = pd.read_csv(fred / f'{t}.csv', parse_dates=['observation_date'])
    df = df.rename(columns={'observation_date': 'date', t: 'val'})
    df['val'] = pd.to_numeric(df['val'], errors='coerce')
    return df.dropna().set_index('date').sort_index()['val']

close = pd.read_csv(yfin / 'sector_etf_close.csv', parse_dates=['Date'], index_col='Date')
xlc = pd.read_csv(yfin / 'xlc_close.csv', parse_dates=['Date'], index_col='Date')
close = close.join(xlc, how='left')
ret = close.pct_change().dropna(how='all')

# Macro drivers (daily)
dgs10 = load_fred('DGS10'); d_dgs10 = dgs10.diff().rename('d_rate')
dfii10 = load_fred('DFII10'); d_dfii10 = dfii10.diff().rename('d_real_rate')
dxy = load_fred('DTWEXBGS'); r_dxy = dxy.pct_change().rename('r_dxy')
hy = load_fred('BAMLH0A0HYM2'); d_hy = hy.diff().rename('d_hy')
# Oil proxy not in our FRED set; skip (or load DCOILWTICO if needed)

# Build daily macro factor panel
factors_daily = pd.concat([d_dgs10, d_dfii10, r_dxy, d_hy], axis=1).dropna()
print('Macro factor panel:')
print(f'  daily n={len(factors_daily)}, range {factors_daily.index.min().date()} -> {factors_daily.index.max().date()}')

# Sector returns of interest
SECTORS = ['XLP', 'XLU', 'XLV', 'XLF', 'XLC', 'SPY']

# Epoch labels (timeline §3)
def label_epoch(d):
    q = pd.Timestamp(d).to_period('Q')
    if q <= pd.Period('2021Q4'): return 'E0_pre'
    if q <= pd.Period('2022Q3'): return 'E1_tighten_shock'
    if q <= pd.Period('2023Q2'): return 'E2_transition_rebound'
    if q == pd.Period('2023Q3'): return 'E3_rate_resurge'
    return 'E4_pivot_easing'

# ============================================================================
# (1) Epoch별 sleeve return + factor 평균
# ============================================================================
print('\n' + '=' * 78)
print('M3-(1): Epoch별 sleeve 수익률 + factor 평균')
print('=' * 78)

# Monthly aggregation
ret_m = (1 + ret[SECTORS]).resample('ME').prod() - 1
ret_m['SLEEVE_DEF_FIN'] = ret_m[['XLP','XLU','XLV','XLF']].mean(axis=1)
ret_m['DEF_ONLY'] = ret_m[['XLP','XLU','XLV']].mean(axis=1)
ret_m['epoch'] = [label_epoch(d) for d in ret_m.index]

# Macro factors monthly
factors_m = factors_daily.resample('ME').mean()
panel_m = ret_m.join(factors_m, how='inner')
panel_m['epoch'] = [label_epoch(d) for d in panel_m.index]

print('\nMonthly excess (sleeve - SPY) by epoch (n months in each epoch):')
print(f"  {'epoch':<22s} {'n':>4s}  {'XLP-SPY':>8s} {'XLU-SPY':>8s} {'XLV-SPY':>8s} {'XLF-SPY':>8s} {'XLC-SPY':>8s} {'sleeve-SPY':>11s}")
m3_epoch = {}
for ep in ['E0_pre', 'E1_tighten_shock', 'E2_transition_rebound', 'E3_rate_resurge', 'E4_pivot_easing']:
    sub = panel_m[panel_m['epoch'] == ep]
    if len(sub) == 0: continue
    spy_m = sub['SPY']
    row = {'n_months': len(sub)}
    excesses = []
    for s in ['XLP','XLU','XLV','XLF','XLC','SLEEVE_DEF_FIN']:
        e = (sub[s] - spy_m).mean()
        row[f'{s}_minus_SPY_mo'] = round(float(e), 4)
        excesses.append(e)
    m3_epoch[ep] = row
    print(f"  {ep:<22s} {len(sub):>4d}  {excesses[0]:+.4f} {excesses[1]:+.4f} {excesses[2]:+.4f} {excesses[3]:+.4f} {excesses[4]:+.4f}    {excesses[5]:+.4f}")

# ============================================================================
# (2) Sleeve ~ [rate, real_rate, dollar, credit] OLS β + R²
#     Daily regression — full sample + epoch-conditional
# ============================================================================
print('\n' + '=' * 78)
print('M3-(2): Macro factor loading OLS regression — daily')
print('=' * 78)

# Build daily panel
panel_d = ret[SECTORS].join(factors_daily, how='inner').dropna()
print(f'Daily panel n={len(panel_d)}, range {panel_d.index.min().date()} -> {panel_d.index.max().date()}')

def ols_loading(y, X):
    """Returns betas + R²."""
    Xc = np.column_stack([np.ones(len(X)), X])
    b, *_ = np.linalg.lstsq(Xc, y, rcond=None)
    yhat = Xc @ b
    ss_res = np.sum((y - yhat)**2)
    ss_tot = np.sum((y - y.mean())**2)
    r2 = 1 - ss_res/ss_tot if ss_tot > 0 else np.nan
    return b, r2

m3_loadings = {}
factor_cols = ['d_rate', 'd_real_rate', 'r_dxy', 'd_hy']
print('\nFull-sample β (sector ~ rate + real_rate + dxy + credit):')
print(f"  {'sector':<7s} {'α':>9s} {'β_rate':>9s} {'β_real':>9s} {'β_dxy':>9s} {'β_hy':>9s} {'R²':>7s}   n")
for s in SECTORS:
    y = panel_d[s].values
    X = panel_d[factor_cols].values
    b, r2 = ols_loading(y, X)
    m3_loadings[s] = {
        'alpha': round(float(b[0]), 6),
        'beta_rate_dgs10': round(float(b[1]), 4),
        'beta_real_rate_dfii10': round(float(b[2]), 4),
        'beta_dxy': round(float(b[3]), 4),
        'beta_credit_hy_oas': round(float(b[4]), 4),
        'R2': round(float(r2), 4),
        'n': len(panel_d),
    }
    print(f"  {s:<7s} {b[0]:+.6f} {b[1]:+.4f}   {b[2]:+.4f}   {b[3]:+.4f}   {b[4]:+.4f}   {r2:.4f}  {len(panel_d)}")

# Epoch-conditional
print('\nEpoch-conditional β (★rate-up vs pivot 분기 핵심):')
panel_d['epoch'] = [label_epoch(d) for d in panel_d.index]
m3_epoch_loadings = {}
for ep in ['E1_tighten_shock', 'E2_transition_rebound', 'E3_rate_resurge', 'E4_pivot_easing']:
    sub = panel_d[panel_d['epoch'] == ep]
    if len(sub) < 30: continue
    print(f'\n  [{ep}] n_days={len(sub)}')
    print(f"    {'sector':<7s} {'β_rate':>9s} {'β_real':>9s} {'β_dxy':>9s} {'β_hy':>9s} {'R²':>7s}")
    m3_epoch_loadings[ep] = {}
    for s in SECTORS:
        y = sub[s].values
        X = sub[factor_cols].values
        b, r2 = ols_loading(y, X)
        m3_epoch_loadings[ep][s] = {
            'beta_rate': round(float(b[1]), 4),
            'beta_real_rate': round(float(b[2]), 4),
            'beta_dxy': round(float(b[3]), 4),
            'beta_credit': round(float(b[4]), 4),
            'R2': round(float(r2), 4),
            'n': len(sub),
        }
        print(f"    {s:<7s} {b[1]:+.4f}   {b[2]:+.4f}   {b[3]:+.4f}   {b[4]:+.4f}   {r2:.4f}")

# ============================================================================
# (3) Within-sleeve corr (cross-asset-class vs within-sleeve 구분 — M1 caveat)
# ============================================================================
print('\n' + '=' * 78)
print('M3-(3): Within-sleeve correlation (자산군간 vs 자기 sleeve 구분)')
print('=' * 78)

corr_sleeve = ret[['XLP','XLU','XLV','XLF','XLC','SPY']].corr()
print('\nDaily return Pearson corr (full sample):')
print(corr_sleeve.round(3))

# Subset XLF excluded (financials) for pure defensive corr
print('\nDefensive subset (XLP/XLU/XLV/XLC) Pearson corr:')
print(corr_sleeve.loc[['XLP','XLU','XLV','XLC'], ['XLP','XLU','XLV','XLC']].round(3))

# Average within-sleeve correlation
def_pairs = [('XLP','XLU'),('XLP','XLV'),('XLP','XLC'),('XLU','XLV'),('XLU','XLC'),('XLV','XLC')]
def_avg = np.mean([corr_sleeve.loc[a,b] for a,b in def_pairs])
print(f'\nAvg within-defensive pair corr = {def_avg:.3f}')
# vs SPY
spy_corrs = [corr_sleeve.loc[s,'SPY'] for s in ['XLP','XLU','XLV','XLC']]
print(f'Avg defensive ~ SPY corr = {np.mean(spy_corrs):.3f}')

# ============================================================================
# Save
# ============================================================================
out = {
    'date': '2026-05-30',
    'panel_n_daily': len(panel_d),
    'panel_n_monthly': len(panel_m),
    'date_range': f"{panel_d.index.min().date()} -> {panel_d.index.max().date()}",
    'm3_epoch_excess': m3_epoch,
    'm3_full_sample_loadings': m3_loadings,
    'm3_epoch_loadings': m3_epoch_loadings,
    'within_sleeve_avg_corr_defensive': round(float(def_avg), 3),
    'avg_def_to_spy_corr': round(float(np.mean(spy_corrs)), 3),
}
with open(ROOT / 'm3-metrics.json', 'w') as f:
    json.dump(out, f, indent=2)
print(f'\nSaved m3-metrics.json')
