"""H3 + H4 + H5 cyclical equity validation.
Inputs: FRED CSVs + sector ETF closes. Outputs: console + saved JSON metrics.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr, pearsonr

ROOT = Path('D:/projects/Inv/study-research/eq_us_cyclical/raw')
fred = ROOT / 'fred'

def load_fred(ticker):
    df = pd.read_csv(fred / f'{ticker}.csv', parse_dates=['observation_date'])
    df = df.rename(columns={'observation_date': 'date', ticker: 'val'})
    df['val'] = pd.to_numeric(df['val'], errors='coerce')
    df = df.dropna().set_index('date').sort_index()
    return df['val']

close = pd.read_csv(ROOT / 'yfinance' / 'sector_etf_close.csv', parse_dates=['Date'], index_col='Date')
print('ETF cols:', list(close.columns))
print('ETF range:', close.index.min().date(), '->', close.index.max().date())

# Daily returns
ret = close.pct_change().dropna(how='all')

CYC = ['XLY', 'XLI', 'XLB', 'XLE', 'XLF']
DEF = ['XLP', 'XLU', 'XLV']
cyc_ret_d = ret[CYC].mean(axis=1)
def_ret_d = ret[DEF].mean(axis=1)
excess_d = (cyc_ret_d - def_ret_d).rename('excess')

# Monthly aggregation
cyc_m = (1 + cyc_ret_d).resample('ME').prod() - 1
def_m = (1 + def_ret_d).resample('ME').prod() - 1
excess_m = (cyc_m - def_m).rename('excess_m')
spy_m = (1 + ret['SPY']).resample('ME').prod() - 1

print(f'\nDaily excess: mean={excess_d.mean()*252:.4f}/yr std={excess_d.std()*np.sqrt(252):.4f} sharpe={excess_d.mean()/excess_d.std()*np.sqrt(252):.2f}')
print(f'Monthly excess: mean={excess_m.mean()*12:.4f}/yr std={excess_m.std()*np.sqrt(12):.4f} sharpe={excess_m.mean()/excess_m.std()*np.sqrt(12):.2f}')

# ============================================================================
# H3: ISM (AMTMNO, CFNAI, AMTMNO-BUSINV) leading cyclical excess return
# ============================================================================
print('\n' + '='*78)
print('H3: ISM proxy -> cyclical-defensive excess (lead-lag, monthly)')
print('='*78)

amtmno = load_fred('AMTMNO')   # monthly
busi = load_fred('BUSINV')     # monthly
cfnai = load_fred('CFNAI')     # monthly
neword = load_fred('NEWORDER') # monthly (core capex new orders)
dgord  = load_fred('DGORDER')  # monthly (durable goods)

# Monthly transforms
amtmno_yoy = amtmno.pct_change(12)
busi_yoy = busi.pct_change(12)
no_inv_ratio = (amtmno / busi).rename('NO_INV_RATIO')
no_inv_yoy = no_inv_ratio.pct_change(12)

# Align monthly index to end-of-month for join with excess_m
def to_month_end(s, name):
    s = s.copy()
    s.index = s.index + pd.offsets.MonthEnd(0)
    return s.rename(name)

leaders = {
    'AMTMNO_YoY': to_month_end(amtmno_yoy, 'AMTMNO_YoY'),
    'CFNAI': to_month_end(cfnai, 'CFNAI'),
    'NO_INV_RATIO_YoY': to_month_end(no_inv_yoy, 'NO_INV_RATIO_YoY'),
    'NEWORDER_YoY': to_month_end(neword.pct_change(12), 'NEWORDER_YoY'),
    'DGORDER_YoY': to_month_end(dgord.pct_change(12), 'DGORDER_YoY'),
}

h3_results = {}
for name, lead in leaders.items():
    df = pd.concat([lead, excess_m], axis=1, join='inner').dropna()
    if len(df) < 60: continue
    row = {'n': len(df)}
    for k in [0, 1, 3, 6]:
        # lead leads excess by k months: corr(lead_t, excess_{t+k})
        x = df[lead.name].iloc[:-k] if k > 0 else df[lead.name]
        y = df['excess_m'].iloc[k:] if k > 0 else df['excess_m']
        ic, p = spearmanr(x, y)
        row[f'rankIC_k{k}'] = round(float(ic), 3)
        row[f'p_k{k}'] = round(float(p), 4)
    h3_results[name] = row
    print(f'  {name:18s} n={row["n"]}  k=0 IC={row["rankIC_k0"]:+.3f} (p={row["p_k0"]:.3f})  k=1 {row["rankIC_k1"]:+.3f}  k=3 {row["rankIC_k3"]:+.3f}  k=6 {row["rankIC_k6"]:+.3f}')

# ============================================================================
# H4: Credit (BAA10Y - AAA10Y proxy EBP) + VIX -> cyclical excess (common cause check)
# ============================================================================
print('\n' + '='*78)
print('H4: credit (BAA10Y-AAA10Y) + VIX -> cyclical excess (partial correlation)')
print('='*78)

baa10 = load_fred('BAA10Y').resample('ME').mean()
aaa10 = load_fred('AAA10Y').resample('ME').mean()
vix_m = load_fred('VIXCLS').resample('ME').mean()
t10y2y_m = load_fred('T10Y2Y').resample('ME').mean()

ig_spread = (baa10 - aaa10).rename('IG_SPREAD')  # credit risk proxy
# Try EBP proxy: IG_SPREAD orthogonalized by VIX residual
df_e = pd.concat([ig_spread, vix_m.rename('VIX'), t10y2y_m.rename('T10Y2Y'), excess_m], axis=1, join='inner').dropna()
# Use changes (stationarity)
df_e['d_IG'] = df_e['IG_SPREAD'].diff()
df_e['d_VIX'] = df_e['VIX'].diff()
df_e['d_T10Y2Y'] = df_e['T10Y2Y'].diff()
df_e = df_e.dropna()

print(f'  joint period n={len(df_e)} months ({df_e.index.min().date()} -> {df_e.index.max().date()})')

# EBP proxy = residual of d_IG ~ d_VIX (Claude said: HY OAS orthogonalized by default risk + VIX)
# We use d_IG as credit risk proxy and d_VIX as risk premium. Residual:
import numpy as np
def partial_corr(x, y, z_list):
    """spearman partial correlation of x,y controlling z_list."""
    X = np.column_stack([np.asarray(df_e[col]) for col in z_list])
    def resid(v):
        beta, *_ = np.linalg.lstsq(np.column_stack([np.ones(len(v)), X]), v, rcond=None)
        return v - np.column_stack([np.ones(len(v)), X]) @ beta
    rx = resid(np.asarray(df_e[x]))
    ry = resid(np.asarray(df_e[y]))
    ic, p = spearmanr(rx, ry)
    return float(ic), float(p)

# IG spread leads excess
for k in [0, 1, 3, 6]:
    sub = df_e.copy()
    sub['excess_lead'] = sub['excess_m'].shift(-k)
    sub = sub.dropna()
    ic_ig, p_ig = spearmanr(sub['d_IG'], sub['excess_lead'])
    ic_vix, p_vix = spearmanr(sub['d_VIX'], sub['excess_lead'])
    # partial: d_IG | d_VIX
    df_e_sub = sub
    df_e_orig = df_e
    df_e = sub
    p_ig_partial, p_partial_p = partial_corr('d_IG', 'excess_lead', ['d_VIX'])
    p_vix_partial, p_vix_partial_p = partial_corr('d_VIX', 'excess_lead', ['d_IG'])
    df_e = df_e_orig
    print(f'  k={k}: d_IG IC={ic_ig:+.3f}(p={p_ig:.3f}) | d_VIX IC={ic_vix:+.3f}(p={p_vix:.3f}) | partial: d_IG|VIX={p_ig_partial:+.3f}, d_VIX|IG={p_vix_partial:+.3f}')

# H4 verdict: does d_IG retain partial IC after controlling VIX?
# ============================================================================
# H5: rate_beta name-specific by sector (longduration vs value-cyclical sign)
# ============================================================================
print('\n' + '='*78)
print('H5: rate_beta name-specific (sector-level, daily DGS10 deltas)')
print('='*78)

dgs10 = load_fred('DGS10')
dgs10_d = dgs10.diff().dropna()  # daily ΔDGS10

joined = ret.join(dgs10_d.rename('d_DGS10'), how='inner').dropna(subset=['d_DGS10'])
print(f'  joint daily n={len(joined)} ({joined.index.min().date()} -> {joined.index.max().date()})')

# Full-sample beta
def beta(y, x):
    cov = np.cov(y, x)[0,1]
    var = np.var(x, ddof=1)
    return cov/var

sectors = ['XLY','XLI','XLB','XLE','XLF','XLP','XLU','XLV','SOXX','SPY']
print('  full-sample β = cov(r, ΔDGS10) / var(ΔDGS10):')
betas = {}
for s in sectors:
    df_s = joined[[s, 'd_DGS10']].dropna()
    b = beta(df_s[s].values, df_s['d_DGS10'].values)
    ic, _ = spearmanr(df_s['d_DGS10'], df_s[s])
    betas[s] = round(float(b), 4)
    print(f'    {s}: β={b:+.4f}  rankIC(ΔDGS10, r)={ic:+.3f}  n={len(df_s)}')

# H5 verdict: sign of β for long-duration (XLY/SOXX) vs value-cyclical (XLE/XLF)
print()
print('  H5 sign check:')
print(f'    long-duration: XLY β={betas["XLY"]:+.4f}, SOXX β={betas["SOXX"]:+.4f}')
print(f'    value-cyclical: XLE β={betas["XLE"]:+.4f}, XLF β={betas["XLF"]:+.4f}')
print(f'    defensive: XLP β={betas["XLP"]:+.4f}, XLU β={betas["XLU"]:+.4f}, XLV β={betas["XLV"]:+.4f}')

# Rolling 60d beta to check time-variation
print('\n  rolling 60D β std (time-variation):')
for s in sectors:
    df_s = joined[[s, 'd_DGS10']].dropna()
    if len(df_s) < 100: continue
    roll_b = df_s[s].rolling(60).cov(df_s['d_DGS10']) / df_s['d_DGS10'].rolling(60).var()
    roll_b = roll_b.dropna()
    print(f'    {s}: mean={roll_b.mean():+.4f} std={roll_b.std():.4f} min={roll_b.min():+.4f} max={roll_b.max():+.4f}')

# Save metrics
out = {
    'period_days': len(joined),
    'period_months_h4': len(df_e),
    'h3_lead_lag': h3_results,
    'h5_full_sample_betas': betas,
    'excess_ann_mean': float(excess_d.mean()*252),
    'excess_ann_vol': float(excess_d.std()*np.sqrt(252)),
}
with open(ROOT / 'validation-metrics.json', 'w') as f:
    json.dump(out, f, indent=2)
print(f'\nSaved metrics to {ROOT}/validation-metrics.json')
