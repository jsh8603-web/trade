"""M3 macro linkage analysis for eq_us_cyclical.
Period: 2021-12-01 ~ 2024-12-31 (M1 timeline).
Inputs: yfinance sector ETF + data/historical_*/macro_yahoo_raw.json (us10y, dxy, oil).
Outputs: regime/epoch decomposition + driver loading + within-sleeve corr.
⛔ No synthetic data. PIT: cumulative returns aligned to actual release dates.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr, pearsonr

ROOT = Path('D:/projects/Inv/study-research/eq_us_cyclical/raw')
INV = Path('D:/projects/Inv')

# Load sector ETF closes
close = pd.read_csv(ROOT / 'yfinance/sector_etf_close.csv',
                    parse_dates=['Date'], index_col='Date')
# Restrict to M1 timeline
START, END = pd.Timestamp('2021-12-01'), pd.Timestamp('2024-12-31')
close = close.loc[START:END]
print(f'ETF window: {close.index.min().date()} -> {close.index.max().date()} n={len(close)}')

# Load macro_yahoo_raw merged
macro_frames = []
for yr in [2022, 2023, 2024]:
    with open(INV / f'data/historical_{yr}/macro_yahoo_raw.json') as f:
        d = json.load(f)
    rows = []
    for date_str in [v['date'] for v in d['sp500']]:
        rows.append(date_str)
    df = pd.DataFrame({'date': pd.to_datetime([v['date'] for v in d['sp500']]),
                       'us10y': [v['close'] for v in d['us10y']],
                       'dxy':   [v['close'] for v in d['dxy']],
                       'oil':   [v['close'] for v in d['oil']],
                       'gold':  [v['close'] for v in d['gold']]})
    macro_frames.append(df)
macro = pd.concat(macro_frames).drop_duplicates('date').set_index('date').sort_index()
macro = macro.loc[START:END]
print(f'Macro window: {macro.index.min().date()} -> {macro.index.max().date()} n={len(macro)}')

# Daily returns and changes
ret = close.pct_change().dropna(how='all')
macro_d = pd.DataFrame({
    'd_us10y': macro['us10y'].diff(),       # bp-ish change (% point of yield)
    'r_dxy':   macro['dxy'].pct_change(),
    'r_oil':   macro['oil'].pct_change(),
}).dropna()

# Cyclical sleeve = mean of XLY/XLI/XLB/XLE/XLF + SOXX. Defensive = XLP/XLU/XLV.
CYC = ['XLY','XLI','XLB','XLE','XLF','SOXX']
DEF = ['XLP','XLU','XLV']
cyc_d = ret[CYC].mean(axis=1)
def_d = ret[DEF].mean(axis=1)
excess_d = (cyc_d - def_d).rename('excess_d')

# ==============================================================================
# Epoch definition (M1 timeline §3)
# ==============================================================================
epochs = [
    ('E1_tightening_shock',   '2022-01-01', '2022-09-30', 'rate↑↑·dollar↑↑·risk-off'),
    ('E2_transition_rally',   '2022-10-01', '2023-06-30', 'rate plateau→ease, AI growth'),
    ('E3_rate_re_rise',       '2023-07-01', '2023-10-31', 'rate↑·oil↑'),
    ('E4_pivot_cuts',         '2023-11-01', '2024-12-31', 'rate↓·dollar↓'),
]

# ==============================================================================
# §1. regime/epoch별 sleeve 평균수익 + 변동성
# ==============================================================================
print('\n' + '='*78)
print('§1. Epoch decomposition — cyclical sleeve mean ret & vol')
print('='*78)
print(f'{"epoch":24s} {"period":24s} {"days":>5s} {"cyc_ann":>9s} {"def_ann":>9s} {"excess_ann":>11s} {"vol_cyc":>9s} {"sharpe_cyc":>11s}')
epoch_metrics = {}
for name, start, end, desc in epochs:
    mask = (cyc_d.index >= start) & (cyc_d.index <= end)
    cd = cyc_d[mask]; dd = def_d[mask]; ed = excess_d[mask]
    n = len(cd)
    cyc_ann = (1 + cd).prod() ** (252/max(n,1)) - 1
    def_ann = (1 + dd).prod() ** (252/max(n,1)) - 1
    ex_ann = (1 + ed).prod() ** (252/max(n,1)) - 1
    vol = cd.std() * np.sqrt(252)
    sh = (cyc_ann - 0.04) / vol if vol > 0 else float('nan')
    print(f'{name:24s} {start} ~ {end[:10]} {n:>5d} {cyc_ann:>+8.2%} {def_ann:>+8.2%} {ex_ann:>+10.2%} {vol:>+8.2%} {sh:>+10.2f}')
    epoch_metrics[name] = {'n': int(n), 'cyc_ann': float(cyc_ann), 'def_ann': float(def_ann),
                          'excess_ann': float(ex_ann), 'cyc_vol_ann': float(vol)}

print('\n  Per-sector annualized return by epoch:')
print(f'{"epoch":20s} ' + ' '.join(f'{s:>7s}' for s in CYC + DEF))
for name, start, end, _ in epochs:
    mask = (ret.index >= start) & (ret.index <= end)
    sub = ret[mask]
    n = len(sub)
    line = f'{name:20s} '
    for s in CYC + DEF:
        ann = (1 + sub[s]).prod() ** (252/max(n,1)) - 1
        line += f'{ann:>+7.1%} '
    print(line)

# ==============================================================================
# §2. Macro driver loading — full sample + epoch conditional
# ==============================================================================
print('\n' + '='*78)
print('§2. Driver loading: r_sleeve ~ Δus10y + r_dxy + r_oil (full + epoch)')
print('='*78)

joined = pd.concat([cyc_d.rename('r_cyc'), def_d.rename('r_def'), excess_d, macro_d], axis=1).dropna()
print(f'  joined daily n={len(joined)}')

def ols(y, X):
    """OLS with intercept. Returns (betas, R²)."""
    X1 = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    pred = X1 @ beta
    ss_res = np.sum((y - pred)**2); ss_tot = np.sum((y - y.mean())**2)
    r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0.0
    return beta, r2

print(f'\n  Full sample (2021-12 ~ 2024-12, n={len(joined)}):')
for target, label in [('r_cyc','cyclical sleeve'), ('r_def','defensive'), ('excess_d','excess')]:
    y = joined[target].values
    X = joined[['d_us10y','r_dxy','r_oil']].values
    beta, r2 = ols(y, X)
    print(f'    {label:18s} α={beta[0]*252:+.3f} β_us10y={beta[1]*100:+.3f}/bp·100 β_dxy={beta[2]:+.3f} β_oil={beta[3]:+.3f}  R²={r2:.3f}')

# Per-sector betas (cross-asset)
print(f'\n  Per-sector loading (cross-asset driver):')
print(f'  {"sector":7s} {"β_us10y":>10s} {"β_dxy":>10s} {"β_oil":>10s} {"R²":>7s}')
sector_loadings = {}
for s in CYC + DEF:
    y = joined[s].values if s in joined.columns else None
    if y is None:
        sub = pd.concat([ret[s], macro_d], axis=1).dropna()
        y = sub[s].values
        X = sub[['d_us10y','r_dxy','r_oil']].values
    else:
        X = joined[['d_us10y','r_dxy','r_oil']].values
    beta, r2 = ols(y, X)
    sector_loadings[s] = {'b_us10y': float(beta[1]), 'b_dxy': float(beta[2]),
                          'b_oil': float(beta[3]), 'r2': float(r2)}
    print(f'  {s:7s} {beta[1]:>+10.4f} {beta[2]:>+10.4f} {beta[3]:>+10.4f} {r2:>7.3f}')

# Epoch-conditional
print(f'\n  Epoch-conditional cyclical sleeve loading (★국면조건부):')
print(f'  {"epoch":24s} {"n":>5s} {"β_us10y":>10s} {"β_dxy":>10s} {"β_oil":>10s} {"R²":>7s}')
epoch_loadings = {}
for name, start, end, _ in epochs:
    sub = joined[(joined.index >= start) & (joined.index <= end)]
    if len(sub) < 20: continue
    y = sub['r_cyc'].values
    X = sub[['d_us10y','r_dxy','r_oil']].values
    beta, r2 = ols(y, X)
    epoch_loadings[name] = {'n': int(len(sub)), 'b_us10y': float(beta[1]),
                             'b_dxy': float(beta[2]), 'b_oil': float(beta[3]), 'r2': float(r2)}
    print(f'  {name:24s} {len(sub):>5d} {beta[1]:>+10.4f} {beta[2]:>+10.4f} {beta[3]:>+10.4f} {r2:>7.3f}')

# ==============================================================================
# §3. cross-asset vs within-sleeve corr (★L축 caveat 검증)
# ==============================================================================
print('\n' + '='*78)
print('§3. cross-asset vs within-sleeve corr (L축 caveat)')
print('='*78)

cyc_ret = ret[CYC].dropna()
within_corr = cyc_ret.corr()
print(f'  within-cyclical-sleeve pairwise corr matrix:')
print(within_corr.round(2).to_string())
mean_off_diag = (within_corr.values.sum() - len(CYC)) / (len(CYC)*(len(CYC)-1))
print(f'\n  mean off-diagonal corr (within-cyclical sleeve) = {mean_off_diag:.3f}')

# Cyclical-vs-Defensive average corr
cd_corrs = []
for c in CYC:
    for d in DEF:
        cd_corrs.append(ret[[c,d]].dropna().corr().iloc[0,1])
print(f'  cyclical-defensive mean pairwise corr = {np.mean(cd_corrs):.3f}')

# Cyclical-vs-macro driver
cyc_macro_corr = {}
for c in CYC:
    sub = pd.concat([ret[c].rename('r'), macro_d], axis=1).dropna()
    for drv in ['d_us10y','r_dxy','r_oil']:
        ic, _ = spearmanr(sub['r'], sub[drv])
        cyc_macro_corr.setdefault(c, {})[drv] = float(ic)
print(f'\n  per-sector vs macro driver (rank-IC):')
print(f'  {"sector":7s} {"d_us10y":>10s} {"r_dxy":>10s} {"r_oil":>10s}')
for c in CYC + DEF:
    sub = pd.concat([ret[c].rename('r'), macro_d], axis=1).dropna()
    ic_u, _ = spearmanr(sub['r'], sub['d_us10y'])
    ic_d, _ = spearmanr(sub['r'], sub['r_dxy'])
    ic_o, _ = spearmanr(sub['r'], sub['r_oil'])
    print(f'  {c:7s} {ic_u:>+10.3f} {ic_d:>+10.3f} {ic_o:>+10.3f}')

# Effective N (Kish design effect)
eff_n_cross = len(CYC) / (1 + (len(CYC)-1)*mean_off_diag)
print(f'\n  ★Kish design eff_N (within cyclical sleeve) = {len(CYC)}/(1+(N-1)·{mean_off_diag:.3f}) = {eff_n_cross:.2f}')

# Save
out = {
    'period': {'start': '2021-12-01', 'end': '2024-12-31', 'n_days': int(len(joined))},
    'epochs': [{'name': n, 'start': s, 'end': e, 'desc': d} for n,s,e,d in epochs],
    'epoch_metrics': epoch_metrics,
    'sector_loadings_full': sector_loadings,
    'epoch_loadings_cyclical': epoch_loadings,
    'within_sleeve_mean_corr': float(mean_off_diag),
    'cyc_def_mean_corr': float(np.mean(cd_corrs)),
    'eff_n_within_cyclical': float(eff_n_cross),
    'per_sector_macro_rank_ic': cyc_macro_corr,
}
with open(ROOT / 'm3-metrics.json', 'w') as f:
    json.dump(out, f, indent=2)
print(f'\nSaved {ROOT}/m3-metrics.json')
