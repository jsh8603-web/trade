"""validation-merit-regional-fed-diffusion.py

Follow-up to validation-merit-cyclical-leading.py.

credential-free-substitute-probe (2026-06-01) found the regional-Fed diffusion NEW ORDERS
series are FREE on FRED and are the closest match to the (paid) ISM new-orders 50-line format:
  NOCDISA066MSFRBNY  - Empire State (NY) new orders diffusion   (2001-07~, n=299)
  NOCDFSA066MSFRBPHI - Philadelphia Fed new orders diffusion    (1968-05~, n=697)

Diffusion indices are already 0-centered (+ = expansion). ALFRED probe shows they are
released ~14-17 days after the survey month -- far more TIMELY than census new orders
(DGORDER/NEWORDER/AMTMNO/ACOGNO publication lag 56-64 days).

QUESTION: does the timeliness advantage translate into superior FORWARD predictive power
on cyclical sectors (SOXX/XLB/XLI/XLE), vs the census-DGORDER->XLE best candidate?

Methodology mirrors validation-merit-cyclical-leading.py exactly:
  - ADF pre-test -> stationary transform
  - contemporaneous(k=0) + forward(k=1/3/6m) Spearman Rank-IC
  - Newey-West HAC t on rank-IC regression (overlapping windows -> inflate NW lag)
  - block bootstrap 95% CI (autocorr-robust)
  - n / p / CI cross-zero
  - LIVE (PIT, signal shifted to first-release date) vs NAIVE
  - Bonferroni + BH-FDR multiple comparison (m disclosed)
  - half-split OOS sign consistency
No synthetic data: fetch failures raise upstream (fetch_regional_fed.py).
"""
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata
from statsmodels.tsa.stattools import adfuller
import statsmodels.api as sm

warnings.filterwarnings('ignore')
rng = np.random.default_rng(20260601)

ROOT = Path(r'D:/projects/Inv/study-research/eq_us_cyclical/raw')
FRED = ROOT / 'fred'
TARGETS = ['SOXX', 'XLB', 'XLI', 'XLE']

# regional-Fed diffusion publication lag (days) from ALFRED probe (regional-fed-pit-probe.json)
PUB_LAG_DAYS = {
    'NOCDISA066MSFRBNY': 14,   # Empire State new orders
    'NOCDFSA066MSFRBPHI': 17,  # Philly Fed new orders
}
# census DGORDER lag for the head-to-head comparison (merit-pit-probe.json)
DGORDER_LAG = 56


def load_fred(ticker):
    df = pd.read_csv(FRED / f'{ticker}.csv', parse_dates=['observation_date'])
    df = df.rename(columns={'observation_date': 'date', ticker: 'val'})
    df['val'] = pd.to_numeric(df['val'], errors='coerce')
    return df.dropna().set_index('date').sort_index()['val']


# ---------------------------------------------------------------------------
# Returns: monthly log-returns of target sectors
# ---------------------------------------------------------------------------
close = pd.read_csv(ROOT / 'yfinance/sector_etf_close.csv', parse_dates=['Date'], index_col='Date')
logret_d = np.log(close[TARGETS]).diff()
ret_m = logret_d.resample('ME').sum().dropna(how='all')

print('=' * 95)
print('REGIONAL-FED DIFFUSION NEW-ORDERS -- forward predictivity on cyclical sectors')
print('Targets:', TARGETS, ' | monthly log-returns')
print('=' * 95)

candidates = {}   # name -> raw monthly series (period month-end indexed)
pub_avail = {}    # name -> first-release availability date per period


def to_month_end(s):
    s = s.copy()
    s.index = s.index + pd.offsets.MonthEnd(0)
    return s


# --- regional-Fed diffusion: transform variants (level + own-history 12m z) ---
empire = load_fred('NOCDISA066MSFRBNY')
philly = load_fred('NOCDFSA066MSFRBPHI')

raw_series = {'NOCDISA066MSFRBNY': empire, 'NOCDFSA066MSFRBPHI': philly}

# composite = average of the two diffusion indices over the overlapping window
comp = pd.concat([empire.rename('e'), philly.rename('p')], axis=1, join='inner').mean(axis=1)
raw_series['COMPOSITE_EMP_PHIL'] = comp
PUB_LAG_DAYS['COMPOSITE_EMP_PHIL'] = 17  # bounded by the slower (Philly) release


def add_candidate(name, sig, lag):
    sig = sig.dropna()
    period_end = sig.index + pd.offsets.MonthEnd(0)
    avail = period_end + pd.Timedelta(days=lag)
    sig2 = sig.copy()
    sig2.index = period_end
    candidates[name] = sig2
    pub_avail[name] = pd.Series(avail.values, index=sig2.index)


for sid, s in raw_series.items():
    lag = PUB_LAG_DAYS[sid]
    # level (diffusion already 0-centered)
    add_candidate(sid + '_lvl', s, lag)
    # own-history 12m rolling z-score (captures regime-relative momentum)
    z = (s - s.rolling(12).mean()) / s.rolling(12).std()
    add_candidate(sid + '_z12', z, lag)

# --- census DGORDER yoy (head-to-head reference, same as cyclical-leading) ---
dg = load_fred('DGORDER')
add_candidate('DGORDER_yoy', dg.pct_change(12), DGORDER_LAG)

# ---------------------------------------------------------------------------
# ADF pre-test (1.7-A)
# ---------------------------------------------------------------------------
print('\n[ADF pre-test] H0: unit root. p<0.05 => stationary (usable as-is)')
adf_res = {}
for name, s in candidates.items():
    stat, p, *_ = adfuller(s.dropna().values, regression='c', autolag='AIC')
    adf_res[name] = {'adf_stat': float(stat), 'adf_p': float(p), 'n': int(len(s.dropna()))}
    flag = 'I(0) stationary' if p < 0.05 else 'I(1)? CAUTION'
    print(f'  {name:26s} ADF p={p:.4f}  n={len(s.dropna()):4d}  {flag}')


# ---------------------------------------------------------------------------
# Helpers (identical to cyclical-leading)
# ---------------------------------------------------------------------------
def nw_lag(n):
    return max(int(np.floor(4 * (n / 100) ** (2 / 9))), 1)


def rank_ic_hac(x, y, extra_overlap=0):
    n = len(x)
    if n < 10:
        return np.nan, np.nan, np.nan, n
    rx = rankdata(x); ry = rankdata(y)
    rx = (rx - rx.mean()) / rx.std()
    ry = (ry - ry.mean()) / ry.std()
    ic, _ = spearmanr(x, y)
    X = sm.add_constant(rx)
    lag = nw_lag(n) + extra_overlap
    res = sm.OLS(ry, X).fit(cov_type='HAC', cov_kwds={'maxlags': lag})
    return float(ic), float(res.tvalues[1]), float(res.pvalues[1]), n


def block_boot_ci(x, y, block=6, B=3000):
    n = len(x)
    if n < 10:
        return np.nan, np.nan
    x = np.asarray(x); y = np.asarray(y)
    nb = int(np.ceil(n / block))
    out = np.empty(B)
    for b in range(B):
        starts = rng.integers(0, n, size=nb)
        idx = np.concatenate([np.arange(s, s + block) % n for s in starts])[:n]
        ic, _ = spearmanr(x[idx], y[idx])
        out[b] = ic
    return float(np.nanpercentile(out, 2.5)), float(np.nanpercentile(out, 97.5))


# ---------------------------------------------------------------------------
# Main test
# ---------------------------------------------------------------------------
HORIZONS = [0, 1, 3, 6]
results = {}
all_pvals = []
pval_keys = []


def fwd_sum_return(target, k):
    if k == 0:
        return ret_m[target]
    return ret_m[target].rolling(k).sum().shift(-k)


def run_block(mode):
    print('\n' + '=' * 95)
    print(f'[{mode.upper()}] rank-IC  k=0(contemp) + forward(1/3/6m)   '
          + ('(signal -> first-release date)' if mode == 'live'
             else '(signal at survey period, no pub-lag)'))
    print('=' * 95)
    print(f'{"candidate":26s} {"tgt":5s}' + ''.join(f'  k={k}:IC(t)' for k in HORIZONS))
    for name, sig in candidates.items():
        for tgt in TARGETS:
            row = f'{name:26s} {tgt:5s}'
            for k in HORIZONS:
                fwd = fwd_sum_return(tgt, k)
                if mode == 'live':
                    avail = pub_avail[name]
                    avail_me = (avail + pd.offsets.MonthEnd(0))
                    s_live = pd.Series(sig.values, index=avail_me.values)
                    s_live = s_live[~s_live.index.duplicated(keep='last')].sort_index()
                    df = pd.concat([s_live.rename('sig'), fwd.rename('fwd')], axis=1,
                                   join='inner').dropna()
                else:
                    df = pd.concat([sig.rename('sig'), fwd.rename('fwd')], axis=1,
                                   join='inner').dropna()
                if len(df) < 24:
                    row += '   n/a    '
                    continue
                ic, t, p, n = rank_ic_hac(df['sig'].values, df['fwd'].values,
                                          extra_overlap=max(k - 1, 0))
                lo, hi = block_boot_ci(df['sig'].values, df['fwd'].values, block=max(k, 6))
                key = '|'.join([mode, name, tgt, str(k)])
                results[key] = {'ic': round(ic, 3), 't_nw': round(t, 2), 'p': round(p, 4),
                                'n': n, 'ci95': [round(lo, 3), round(hi, 3)],
                                'ci_cross_zero': bool(lo < 0 < hi)}
                if mode == 'live' and k > 0:
                    all_pvals.append(p)
                    pval_keys.append(key)
                star = '*' if (p < 0.05 and not (lo < 0 < hi)) else ' '
                row += f'  {ic:+.2f}({t:+.1f}){star}'
            print(row)


run_block('naive')
run_block('live')

# ---------------------------------------------------------------------------
# Multiple comparison (LIVE forward predictive tests)
# ---------------------------------------------------------------------------
print('\n' + '=' * 95)
print('[MULTIPLE COMPARISON] LIVE forward predictive tests (k>0)')
print('=' * 95)
m = len(all_pvals)
pv = np.array(all_pvals)
bonf = 0.05 / m if m else np.nan
order = np.argsort(pv)
sp = pv[order]
bh_crit = 0.0
for kk in range(m, 0, -1):
    if sp[kk - 1] <= kk / m * 0.05:
        bh_crit = sp[kk - 1]; break
bonf_surv = [pval_keys[i] for i in range(m) if pv[i] < bonf]
bh_surv = [pval_keys[i] for i in range(m) if pv[i] <= bh_crit]
print(f'  m = {m} forward predictive comparisons')
print(f'  Bonferroni alpha = 0.05/{m} = {bonf:.5f}  -> survivors: {len(bonf_surv)}')
for k_ in bonf_surv:
    print(f'      {k_}  p={results[k_]["p"]}')
print(f'  BH-FDR q=0.05 crit p = {bh_crit:.5f}  -> survivors: {len(bh_surv)}')
for k_ in bh_surv:
    print(f'      {k_}  p={results[k_]["p"]} IC={results[k_]["ic"]} CI={results[k_]["ci95"]}')

# ---------------------------------------------------------------------------
# Half-split OOS sign consistency (LIVE forward k=3)
# ---------------------------------------------------------------------------
print('\n' + '=' * 95)
print('[HALF-SPLIT OOS] sign consistency, LIVE forward k=3m')
print('=' * 95)
oos = {}
for name in candidates:
    for tgt in TARGETS:
        sig = candidates[name]
        avail_me = (pub_avail[name] + pd.offsets.MonthEnd(0))
        s_live = pd.Series(sig.values, index=avail_me.values)
        s_live = s_live[~s_live.index.duplicated(keep='last')].sort_index()
        fwd = fwd_sum_return(tgt, 3)
        df = pd.concat([s_live.rename('sig'), fwd.rename('fwd')], axis=1, join='inner').dropna()
        if len(df) < 48:
            continue
        mid = len(df) // 2
        ic1, _ = spearmanr(df['sig'].iloc[:mid], df['fwd'].iloc[:mid])
        ic2, _ = spearmanr(df['sig'].iloc[mid:], df['fwd'].iloc[mid:])
        match = np.sign(ic1) == np.sign(ic2)
        oos[f'{name}|{tgt}'] = {'ic_h1': round(float(ic1), 3), 'ic_h2': round(float(ic2), 3),
                                'sign_match': bool(match), 'n': len(df)}
        if match and abs(ic1) > 0.1 and abs(ic2) > 0.1:
            print(f'  {name:26s} {tgt:5s} h1={ic1:+.2f} h2={ic2:+.2f}  MATCH (both>0.1) n={len(df)}')
n_match = sum(v['sign_match'] for v in oos.values())
print(f'  sign-match: {n_match}/{len(oos)} (chance=50%)')

# ---------------------------------------------------------------------------
# Head-to-head vs census DGORDER->XLE (timeliness payoff check)
# ---------------------------------------------------------------------------
print('\n' + '=' * 95)
print('[HEAD-TO-HEAD] regional-Fed NEW ORDERS vs census DGORDER_yoy -> XLE (LIVE)')
print('=' * 95)
h2h = {}
for nm in ['DGORDER_yoy', 'NOCDISA066MSFRBNY_lvl', 'NOCDFSA066MSFRBPHI_lvl',
           'COMPOSITE_EMP_PHIL_lvl', 'NOCDISA066MSFRBNY_z12',
           'NOCDFSA066MSFRBPHI_z12', 'COMPOSITE_EMP_PHIL_z12']:
    h2h[nm] = {}
    for k in HORIZONS:
        key = '|'.join(['live', nm, 'XLE', str(k)])
        if key in results:
            r = results[key]
            h2h[nm][f'k{k}'] = {'ic': r['ic'], 't': r['t_nw'], 'p': r['p'],
                                'n': r['n'], 'cross0': r['ci_cross_zero']}
    print(f'  {nm:26s} ' + '  '.join(
        f"k{k}:{h2h[nm].get(f'k{k}',{}).get('ic','--')}({h2h[nm].get(f'k{k}',{}).get('t','--')})"
        for k in HORIZONS))

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
out = {
    'targets': TARGETS,
    'ret_range': [str(ret_m.index.min().date()), str(ret_m.index.max().date())],
    'pub_lag_days': PUB_LAG_DAYS,
    'dgorder_lag_days': DGORDER_LAG,
    'series_coverage': {
        'NOCDISA066MSFRBNY': [str(empire.index.min().date()), str(empire.index.max().date()), int(len(empire))],
        'NOCDFSA066MSFRBPHI': [str(philly.index.min().date()), str(philly.index.max().date()), int(len(philly))],
        'COMPOSITE_EMP_PHIL': [str(comp.index.min().date()), str(comp.index.max().date()), int(len(comp))],
    },
    'adf': adf_res,
    'results': results,
    'multiple_comparison': {'m': m, 'bonferroni_alpha': float(bonf),
                            'bonf_survivors': bonf_surv,
                            'bh_crit_p': float(bh_crit), 'bh_survivors': bh_surv},
    'half_split_oos_k3': oos,
    'oos_sign_match': f'{n_match}/{len(oos)}',
    'head_to_head_xle': h2h,
}
with open(ROOT / 'validation-merit-regional-fed-diffusion.json', 'w') as f:
    json.dump(out, f, indent=2)
print(f'\n[Saved] {ROOT / "validation-merit-regional-fed-diffusion.json"}')
