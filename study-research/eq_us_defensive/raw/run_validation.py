"""eq_us_defensive — H1/H2/H3/H4 real-data validation.

Inputs:
  raw/fred/{DGS10,DGS2,DFII10,T10YIE,BAMLH0A0HYM2,VIXCLS,UNRATE,DTWEXBGS}.csv
  raw/yfinance/sector_etf_close.csv (reused from cyclical room — 2000-01 onward)
  raw/yfinance/xlc_close.csv (XLC since 2018-06)

Outputs:
  console + raw/validation-metrics.json
  - H1 real rate dichotomy (util/staples vs banks/insurance sign split)
  - H2 yield curve slope -> XLF NIM lead-lag (CCF 0~12M)
  - H3 HY OAS regime -> sleeve excess return (Credit/Inflation/Normal regimes)
  - H4 dividend_yield z + credit_beta sign (proxy via XLP/XLU rolling rate beta)
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr, pearsonr

ROOT = Path('D:/projects/Inv/study-research/eq_us_defensive/raw')
fred = ROOT / 'fred'
yfin = ROOT / 'yfinance'

def load_fred(ticker):
    df = pd.read_csv(fred / f'{ticker}.csv', parse_dates=['observation_date'])
    df = df.rename(columns={'observation_date': 'date', ticker: 'val'})
    df['val'] = pd.to_numeric(df['val'], errors='coerce')
    df = df.dropna().set_index('date').sort_index()
    return df['val']

# Load ETF panel from cyclical room (covers XLP/XLU/XLV/XLF/SPY)
close = pd.read_csv(yfin / 'sector_etf_close.csv', parse_dates=['Date'], index_col='Date')
print('=' * 78)
print('Data loaded')
print('=' * 78)
print(f'ETF cols: {list(close.columns)}')
print(f'ETF range: {close.index.min().date()} -> {close.index.max().date()} (n={len(close)} days)')

# Merge XLC (since 2018-06)
xlc = pd.read_csv(yfin / 'xlc_close.csv', parse_dates=['Date'], index_col='Date')
close = close.join(xlc, how='left')
print(f'After XLC merge: cols {list(close.columns)}')

# Daily returns
ret = close.pct_change().dropna(how='all')

DEF_SECTORS = ['XLP', 'XLU', 'XLV', 'XLC']  # defensive subset (XLC added but limited to post-2018)
FIN_SECTORS = ['XLF']  # combined banks/insurance/payments
ALL_DEF_FIN = ['XLP', 'XLU', 'XLV', 'XLF']  # excludes XLC for full-period analysis
# Per task spec sleeve = defensive + financial (combined)
SLEEVE = ['XLP', 'XLU', 'XLV', 'XLF', 'XLC']  # full sleeve
SLEEVE_FULL_PERIOD = ['XLP', 'XLU', 'XLV', 'XLF']  # 2000-01 onward

# ============================================================================
# H1: Real Rate Sensitivity Dichotomy (DFII10 -> XLU/XLP vs XLF)
# Hypothesis: real rate ↑ -> XLU/XLP RETURN negative, XLF RETURN positive
# Method: daily ΔDFII10 vs daily sector returns + rolling beta + Spearman IC
# ============================================================================
print('\n' + '=' * 78)
print('H1: Real Rate Dichotomy — ΔDFII10 → sector return sign split')
print('=' * 78)

dfii10 = load_fred('DFII10')
d_dfii10 = dfii10.diff().dropna()  # daily Δreal rate

joined_h1 = ret.join(d_dfii10.rename('d_DFII10'), how='inner').dropna(subset=['d_DFII10'])
print(f'Joint daily period: {joined_h1.index.min().date()} -> {joined_h1.index.max().date()}, n={len(joined_h1)}')

# Add SPY return for partial-corr conditioning
def beta(y, x):
    cov = np.cov(y, x)[0,1]
    var = np.var(x, ddof=1)
    return cov/var if var > 0 else np.nan

def partial_spearman(x, y, z_arr):
    """Spearman partial correlation of x,y controlling z columns."""
    Z = np.atleast_2d(z_arr)
    if Z.shape[0] != len(x):
        Z = Z.T
    Zc = np.column_stack([np.ones(len(x)), Z])
    bx = np.linalg.lstsq(Zc, x, rcond=None)[0]
    rx = x - Zc @ bx
    by = np.linalg.lstsq(Zc, y, rcond=None)[0]
    ry = y - Zc @ by
    ic, p = spearmanr(rx, ry)
    return float(ic), float(p)

sectors_h1 = ['XLU', 'XLP', 'XLV', 'XLF', 'XLC', 'SPY']
h1 = {}
print('\nFull-sample β (rate sensitivity, daily ΔDFII10) and Spearman IC:')
print(f"  {'sector':<8s} {'β':>9s} {'rankIC':>8s} {'p':>7s}  {'partial|SPY':>14s}  {'p':>7s}   n")
for s in sectors_h1:
    cols = [s, 'd_DFII10'] if s == 'SPY' else [s, 'd_DFII10', 'SPY']
    df_s = joined_h1[cols].dropna()
    b = beta(df_s[s].values, df_s['d_DFII10'].values)
    ic, p = spearmanr(df_s['d_DFII10'], df_s[s])
    if s == 'SPY':
        pic, pp = np.nan, np.nan  # SPY = conditioner itself
    else:
        spy_arr = df_s['SPY'].values
        pic, pp = partial_spearman(df_s['d_DFII10'].values, df_s[s].values, spy_arr)
    h1[s] = {'beta': round(float(b), 4), 'rankIC': round(float(ic), 3), 'p': round(float(p), 4),
             'partial_IC_given_SPY': round(pic, 3) if not np.isnan(pic) else None,
             'partial_p': round(pp, 4) if not np.isnan(pp) else None, 'n': len(df_s)}
    pic_str = f"{pic:+.3f}" if not np.isnan(pic) else "  N/A"
    pp_str = f"{pp:.4f}" if not np.isnan(pp) else "  N/A"
    print(f"  {s:<8s} {b:+.4f}   {ic:+.3f}   {p:.4f}    {pic_str}        {pp_str}  {len(df_s)}")

print('\n[H1 verdict]')
xlu_pic = h1['XLU']['partial_IC_given_SPY']
xlp_pic = h1['XLP']['partial_IC_given_SPY']
xlf_pic = h1['XLF']['partial_IC_given_SPY']
print(f"  XLU partial IC|SPY = {xlu_pic:+.3f} (prior NEG)")
print(f"  XLP partial IC|SPY = {xlp_pic:+.3f} (prior NEG)")
print(f"  XLF partial IC|SPY = {xlf_pic:+.3f} (prior POS)")
sign_split_ok = (xlu_pic < 0) and (xlp_pic < 0) and (xlf_pic > 0)
print(f"  Sign split (util/staples NEG, banks POS): {'CONFIRMED' if sign_split_ok else 'FAILED'}")

# Rolling 60D beta time-variation
print('\nRolling 60D rate beta time-variation:')
for s in sectors_h1[:-1]:
    df_s = joined_h1[[s, 'd_DFII10']].dropna()
    if len(df_s) < 120: continue
    roll_b = df_s[s].rolling(60).cov(df_s['d_DFII10']) / df_s['d_DFII10'].rolling(60).var()
    roll_b = roll_b.dropna()
    sign_flip = ((roll_b > 0) != (roll_b.mean() > 0)).sum() / len(roll_b)
    print(f"  {s}: mean={roll_b.mean():+.4f} std={roll_b.std():.4f} sign-flip-pct={sign_flip*100:.1f}%")

# ============================================================================
# H2: Yield Curve Slope (DGS10-DGS2) -> XLF NIM leading (CCF 0~12M lag)
# Hypothesis: slope steepening -> XLF excess return rises with 3-6M lag
# Method: monthly Δslope_{t-k} vs XLF excess (vs SPY)_{t}, Spearman IC for k=0..12
# ============================================================================
print('\n' + '=' * 78)
print('H2: Yield Curve Slope NIM Leading — Δ(DGS10-DGS2) -> XLF excess (lead-lag)')
print('=' * 78)

dgs10 = load_fred('DGS10').resample('ME').mean()
dgs2 = load_fred('DGS2').resample('ME').mean()
slope = (dgs10 - dgs2).rename('slope')
d_slope = slope.diff().rename('d_slope')

# Monthly returns
xlf_m = (1 + ret['XLF']).resample('ME').prod() - 1
spy_m = (1 + ret['SPY']).resample('ME').prod() - 1
xlf_excess = (xlf_m - spy_m).rename('xlf_excess')

df_h2 = pd.concat([d_slope, xlf_excess], axis=1, join='inner').dropna()
print(f'Monthly joint period: {df_h2.index.min().date()} -> {df_h2.index.max().date()}, n={len(df_h2)}')

h2 = {}
print('\nLead-lag scan (slope_{t-k} -> XLF_excess_{t}):')
print(f"  {'lag_k(months)':<14s} {'rankIC':>8s} {'p':>7s}   n")
for k in [0, 1, 2, 3, 4, 5, 6, 8, 12]:
    if k == 0:
        x = df_h2['d_slope'].values
        y = df_h2['xlf_excess'].values
    else:
        x = df_h2['d_slope'].iloc[:-k].values
        y = df_h2['xlf_excess'].iloc[k:].values
    ic, p = spearmanr(x, y)
    h2[f'lag_{k}'] = {'rankIC': round(float(ic), 3), 'p': round(float(p), 4), 'n': len(x)}
    star = ' *' if p < 0.05 else ('  .' if p < 0.10 else '')
    print(f"  k={k:<10d}  {ic:+.3f}    {p:.4f}  {len(x)}{star}")

best_lag = max(h2.keys(), key=lambda k: h2[k]['rankIC'])
print(f"\n[H2 verdict] Best lag={best_lag} IC={h2[best_lag]['rankIC']:+.3f} p={h2[best_lag]['p']:.4f}")
prior_satisfied = h2['lag_3']['rankIC'] > 0 and h2['lag_6']['rankIC'] > 0
print(f"  Prior 3-6M positive lag: {'CONFIRMED' if prior_satisfied else 'WEAK'}")

# ============================================================================
# H3: HY OAS Regime -> Sleeve Excess Return (Credit/Inflation/Normal regimes)
# Hypothesis: Credit Crisis -> sleeve outperform SPY; Inflation Shock -> effect weakened/absent
# Method: monthly regime classify + sleeve - SPY excess + Bootstrap t-test by regime
# ============================================================================
print('\n' + '=' * 78)
print('H3: HY OAS Defensive Outperformance — regime-conditional test')
print('=' * 78)

hy = load_fred('BAMLH0A0HYM2').resample('ME').mean()
vix = load_fred('VIXCLS').resample('ME').mean()
t10yie = load_fred('T10YIE').resample('ME').mean()
ffr = load_fred('FEDFUNDS').resample('ME').mean()
unrate = load_fred('UNRATE').resample('ME').mean()

# Compute z-scores (rolling 60M, then deviation from 60M mean / 60M std)
def zroll(s, w=60):
    return (s - s.rolling(w).mean()) / s.rolling(w).std()

z_hy = zroll(hy)
z_vix = zroll(vix)
z_t10yie = zroll(t10yie)
d_ffr_6m = ffr.diff(6)
d_unrate_3m = unrate.diff(3)

# Regime classification — simplified to top-quartile based markers
# Credit Stress: HY OAS in top 25% (p75+) for that month
# Inflation Shock: T10YIE z > 0.5 OR T10YIE > p75 AND Fed tightening (d_ffr_6m > 0.25)
# Priority: Inflation > Credit when both fire (2022 case)
hy_p75 = hy.quantile(0.75)
hy_p90 = hy.quantile(0.90)
t10y_p75 = t10yie.quantile(0.75)
print(f'\nRegime thresholds: HY p75={hy_p75:.3f}, p90={hy_p90:.3f}, T10YIE p75={t10y_p75:.3f}')

def classify_regime(idx):
    """Returns DataFrame with independent dummies — Credit + Inflation can co-occur."""
    creds, infls = [], []
    for t in idx:
        try:
            hyv = hy.loc[t]
            t10v = t10yie.loc[t]
            df_ffr = d_ffr_6m.loc[t]
        except KeyError:
            creds.append(False); infls.append(False); continue
        cred = pd.notna(hyv) and hyv > hy_p75
        infl = pd.notna(t10v) and t10v > t10y_p75 and pd.notna(df_ffr) and df_ffr > 0.25
        creds.append(cred); infls.append(infl)
    return pd.DataFrame({'credit': creds, 'inflation': infls}, index=idx)

# Sleeve monthly excess (XLP+XLU+XLV+XLF equal-weighted, vs SPY)
sleeve_m = pd.DataFrame({
    s: (1 + ret[s]).resample('ME').prod() - 1
    for s in SLEEVE_FULL_PERIOD
})
sleeve_m['sleeve_eq'] = sleeve_m.mean(axis=1)
sleeve_excess = (sleeve_m['sleeve_eq'] - spy_m).rename('excess')

# Defensive-only excess (XLP+XLU+XLV — drops XLF since financials aren't classical defensive)
defonly_m = pd.DataFrame({s: (1 + ret[s]).resample('ME').prod() - 1 for s in ['XLP','XLU','XLV']}).mean(axis=1)
defonly_excess = (defonly_m - spy_m).rename('def_excess')

# Align all
common_idx = sleeve_excess.dropna().index
regime_df = classify_regime(common_idx)
df_h3 = pd.concat([sleeve_excess, defonly_excess, regime_df], axis=1, join='inner').dropna()
print(f'Monthly period: {df_h3.index.min().date()} -> {df_h3.index.max().date()}, n={len(df_h3)}')

print(f'\nRegime distribution (n={len(df_h3)} months) — independent dummies:')
print(f"  Credit Stress (HY OAS>p75):   n={df_h3['credit'].sum()}")
print(f"  Inflation Shock:               n={df_h3['inflation'].sum()}")
print(f"  Both (credit & inflation):     n={(df_h3['credit'] & df_h3['inflation']).sum()}")
print(f"  Normal (neither):              n={((~df_h3['credit']) & (~df_h3['inflation'])).sum()}")

print('\nMean monthly excess return by regime (sleeve = XLP+XLU+XLV+XLF eq, def_only = XLP+XLU+XLV):')
h3 = {}
rng = np.random.default_rng(20260530)
def bootstrap_ci(x, n=10000, alpha=0.05):
    n_obs = len(x)
    means = np.array([np.mean(rng.choice(x, n_obs, replace=True)) for _ in range(n)])
    lo, hi = np.percentile(means, [100*alpha/2, 100*(1-alpha/2)])
    p_two_sided = 2 * min((means > 0).mean(), (means < 0).mean())
    return float(np.mean(x)), float(lo), float(hi), float(p_two_sided)

print(f"  {'regime':<22s} {'n':>5s}  {'sleeve_mean':>13s}  {'95%CI':>22s}  {'p':>6s}   {'def_only_mean':>14s}  {'def_p':>7s}")
regimes_to_test = {
    'Credit Stress (all)': df_h3['credit'] == True,
    'Credit only (~infl)': (df_h3['credit'] == True) & (df_h3['inflation'] == False),
    'Inflation Shock (all)': df_h3['inflation'] == True,
    'Inflation only (~cred)': (df_h3['inflation'] == True) & (df_h3['credit'] == False),
    'Both regimes': (df_h3['credit'] == True) & (df_h3['inflation'] == True),
    'Normal': (df_h3['credit'] == False) & (df_h3['inflation'] == False),
}
for r, mask in regimes_to_test.items():
    sub = df_h3[mask]
    if len(sub) < 4:
        print(f"  {r:<22s} {len(sub):>5d}  insufficient")
        h3[r] = {'n': len(sub), 'note': 'insufficient'}
        continue
    sx = sub['excess'].values
    mx, lo, hi, p_x = bootstrap_ci(sx)
    dx = sub['def_excess'].values
    mdx, dlo, dhi, p_dx = bootstrap_ci(dx)
    h3[r] = {
        'n': len(sub),
        'sleeve_mean_mo': round(mx, 4),
        'sleeve_95CI': [round(lo, 4), round(hi, 4)],
        'sleeve_p': round(p_x, 4),
        'def_only_mean_mo': round(mdx, 4),
        'def_only_95CI': [round(dlo, 4), round(dhi, 4)],
        'def_only_p': round(p_dx, 4),
    }
    print(f"  {r:<22s} {len(sub):>5d}  {mx:+.4f}     [{lo:+.4f}, {hi:+.4f}]  {p_x:.4f}    {mdx:+.4f}        {p_dx:.4f}")

print('\n[H3 verdict]')
if 'Credit' in h3 and 'note' not in h3['Credit']:
    credit_pos = h3['Credit']['sleeve_mean_mo'] > 0
    credit_sig = h3['Credit']['sleeve_p'] < 0.10
    print(f"  Credit regime: sleeve excess {h3['Credit']['sleeve_mean_mo']:+.4f}/mo, p={h3['Credit']['sleeve_p']:.4f} — {'CONFIRMED' if credit_pos and credit_sig else 'WEAK/REJECT'}")
if 'Inflation' in h3 and 'note' not in h3['Inflation']:
    infl_weaker = h3['Inflation']['sleeve_mean_mo'] < h3['Credit']['sleeve_mean_mo'] if 'Credit' in h3 and 'note' not in h3['Credit'] else None
    print(f"  Inflation regime: sleeve excess {h3['Inflation']['sleeve_mean_mo']:+.4f}/mo, p={h3['Inflation']['sleeve_p']:.4f} — {'CONFIRMED weaker than Credit' if infl_weaker else 'UNEXPECTED'}")

# ============================================================================
# H4: dividend_yield z + credit_beta (proxy via daily ΔHY OAS vs sector returns)
# H4a: credit_beta sign split — XLP/XLU defensive POS (cheap when risk-off), XLF NEG (provisioning)
# H4b: dividend_yield z proxy — use rolling SPY dividend yield change (no per-stock data) or skip
# We do H4a fully; H4b deferred (no per-stock data).
# ============================================================================
print('\n' + '=' * 78)
print('H4a: Credit Beta — Δ(HY OAS) -> sector return sign')
print('=' * 78)

hy_d = load_fred('BAMLH0A0HYM2')
d_hy = hy_d.diff().dropna()
joined_h4 = ret.join(d_hy.rename('d_HY'), how='inner').dropna(subset=['d_HY'])
print(f'Joint daily: {joined_h4.index.min().date()} -> {joined_h4.index.max().date()}, n={len(joined_h4)}')

sectors_h4 = ['XLU', 'XLP', 'XLV', 'XLF', 'XLC', 'SPY']
h4 = {}
print(f"\n  {'sector':<8s} {'β(d_HY)':>9s} {'rankIC':>8s} {'p':>7s}  {'partial|SPY':>14s}  {'p':>7s}  n")
for s in sectors_h4:
    cols = [s, 'd_HY'] if s == 'SPY' else [s, 'd_HY', 'SPY']
    df_s = joined_h4[cols].dropna()
    b = beta(df_s[s].values, df_s['d_HY'].values)
    ic, p = spearmanr(df_s['d_HY'], df_s[s])
    if s == 'SPY':
        pic, pp = np.nan, np.nan
    else:
        pic, pp = partial_spearman(df_s['d_HY'].values, df_s[s].values, df_s['SPY'].values)
    h4[s] = {'beta_dHY': round(float(b), 4), 'rankIC': round(float(ic), 3), 'p': round(float(p), 4),
             'partial_IC_given_SPY': round(pic, 3) if not np.isnan(pic) else None,
             'partial_p': round(pp, 4) if not np.isnan(pp) else None, 'n': len(df_s)}
    pic_str = f"{pic:+.3f}" if not np.isnan(pic) else "  N/A"
    pp_str = f"{pp:.4f}" if not np.isnan(pp) else "  N/A"
    print(f"  {s:<8s} {b:+.4f}   {ic:+.3f}   {p:.4f}    {pic_str}        {pp_str}  {len(df_s)}")

print('\n[H4a verdict]')
xlu_h4 = h4['XLU']['partial_IC_given_SPY']
xlp_h4 = h4['XLP']['partial_IC_given_SPY']
xlf_h4 = h4['XLF']['partial_IC_given_SPY']
print(f"  XLU partial IC|SPY (vs ΔHY) = {xlu_h4:+.3f}")
print(f"  XLP partial IC|SPY = {xlp_h4:+.3f}")
print(f"  XLF partial IC|SPY = {xlf_h4:+.3f}")
# After SPY absorbs broad risk-off, residual credit signal: prior says XLF more negative
# than defensive (provisioning channel beyond market beta)

# ============================================================================
# Save metrics
# ============================================================================
out = {
    'date': '2026-05-30',
    'data_period_daily': f"{joined_h1.index.min().date()} -> {joined_h1.index.max().date()}",
    'h1_real_rate_dichotomy': h1,
    'h1_sign_split_confirmed': sign_split_ok,
    'h2_yield_curve_lead_lag': h2,
    'h2_best_lag': best_lag,
    'h3_hy_oas_regime': h3,
    'h4_credit_beta': h4,
}
with open(ROOT / 'validation-metrics.json', 'w') as f:
    json.dump(out, f, indent=2, default=str)
print(f'\nSaved metrics to {ROOT}/validation-metrics.json')
