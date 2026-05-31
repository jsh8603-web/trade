"""validation-merit-cyclical-leading.py

M6 consult flagged cyclical needs leading vars (ISM new orders / PMI / fwd EPS revision breadth),
all paid. This explores FREE FRED alternatives for forward predictive power on cyclical sectors.

Targets: SOXX / XLB / XLI / XLE monthly log-returns.
Candidates (ISM-free leading proxies):
  - NEWORDER  (nondefense capital goods ex-aircraft new orders; capex lead)
  - AMTMNO    (mfg new orders)
  - DGORDER   (durable goods new orders)
  - ACOGNO    (consumer goods new orders)
  - PERMIT    (building permits; housing lead)
  - T10Y2Y / T10Y3M (yield-curve recession lead)
  - COPPER_GOLD (copper/gold ratio; market-priced global-growth gauge, PIT-clean)

CRITICAL PIT design (eq_intl credit-impulse lookahead trap avoidance):
  FRED monthly macro = REVISED + published with ~48-130 day lag (ALFRED probe).
  observation_date is the *period* it refers to, NOT when it was knowable.
  -> Forward-return tests use LIVE alignment: candidate value for period P is only
     usable from its first-release date (period_end + median pub lag). We shift the
     macro signal so it is matched to returns that occur strictly AFTER it was public.
  -> We ALSO report a NAIVE (revised, no-lag) variant to quantify the lookahead illusion.
  Copper/gold is market-priced daily -> PIT-clean, no lag adjustment.

Stats obligations (empirical-claim-presentation + small-n-rigor):
  - ADF pre-test -> stationary transform (yoy / diff / z)
  - contemporaneous + forward(1/3/6m) Spearman Rank-IC
  - Newey-West HAC t-stat on Fisher-z of rank-corr (overlapping windows)
  - n / p / 95% bootstrap CI (block bootstrap for autocorr)
  - Bonferroni + BH-FDR multiple comparison (m disclosed)
  - half-split OOS sign consistency
No synthetic data.
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

# median publication lag (days) from ALFRED probe (merit-pit-probe.json)
PUB_LAG_DAYS = {
    'NEWORDER': 56, 'AMTMNO': 64, 'DGORDER': 56, 'ACOGNO': 64, 'PERMIT': 48,
}


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
# monthly compounded log-return, indexed at month-end
ret_m = logret_d.resample('ME').sum()
ret_m = ret_m.dropna(how='all')

# ---------------------------------------------------------------------------
# Build candidate signals (monthly, transformed to stationary), with PIT variants
# ---------------------------------------------------------------------------
print('=' * 90)
print('MERIT LEADING-VAR EXPLORATION -- free FRED ISM-alternatives for cyclical forward predictivity')
print('Targets:', TARGETS, ' | monthly log-returns')
print('=' * 90)

candidates = {}      # name -> raw monthly series (period-indexed, month-end)
pub_avail = {}       # name -> first-release availability date per period (for live align)


def to_month_end(s):
    s = s.copy()
    s.index = s.index + pd.offsets.MonthEnd(0)
    return s


# --- monthly FRED macro (revised, published with lag) ---
fred_monthly = {
    'NEWORDER': ('yoy', PUB_LAG_DAYS['NEWORDER']),
    'AMTMNO':   ('yoy', PUB_LAG_DAYS['AMTMNO']),
    'DGORDER':  ('yoy', PUB_LAG_DAYS['DGORDER']),
    'ACOGNO':   ('yoy', PUB_LAG_DAYS['ACOGNO']),
    'PERMIT':   ('yoy', PUB_LAG_DAYS['PERMIT']),
}
for sid, (tf, lag) in fred_monthly.items():
    s = load_fred(sid)
    if tf == 'yoy':
        sig = s.pct_change(12)
    else:
        sig = s.diff()
    sig = sig.dropna()
    # period reference = observation_date (period start). Period END = +MonthEnd.
    period_end = sig.index + pd.offsets.MonthEnd(0)
    avail = period_end + pd.Timedelta(days=lag)  # first-release knowable date
    sig.index = period_end
    candidates[sid + '_yoy'] = sig
    pub_avail[sid + '_yoy'] = pd.Series(avail.values, index=sig.index)

# --- yield curve (daily, market-priced, PIT-clean) -> month-end level ---
for sid in ['T10Y2Y', 'T10Y3M']:
    s = load_fred(sid).resample('ME').last()
    candidates[sid] = s.dropna()
    pub_avail[sid] = pd.Series(candidates[sid].index, index=candidates[sid].index)  # same-day knowable

# --- copper-gold ratio (daily market price, PIT-clean) -> month-end yoy ---
cg = pd.read_csv(ROOT / 'copper_gold_ratio.csv', parse_dates=['Date'], index_col='Date')['COPPER_GOLD']
cg_m = cg.resample('ME').last()
cg_yoy = cg_m.pct_change(12).dropna()
candidates['COPPER_GOLD_yoy'] = cg_yoy
pub_avail['COPPER_GOLD_yoy'] = pd.Series(cg_yoy.index, index=cg_yoy.index)

# ---------------------------------------------------------------------------
# ADF pre-test (1.7-A) on each transformed candidate
# ---------------------------------------------------------------------------
print('\n[ADF pre-test] H0: unit root. p<0.05 => stationary (usable as-is)')
adf_res = {}
for name, s in candidates.items():
    stat, p, *_ = adfuller(s.dropna().values, regression='c', autolag='AIC')
    adf_res[name] = {'adf_stat': float(stat), 'adf_p': float(p), 'n': int(len(s))}
    flag = 'I(0) stationary' if p < 0.05 else 'I(1)? CAUTION'
    print(f'  {name:18s} ADF p={p:.4f}  n={len(s):4d}  {flag}')


# ---------------------------------------------------------------------------
# Helpers: Newey-West HAC t on overlapping forward-return rank-IC + block-boot CI
# ---------------------------------------------------------------------------
def nw_lag(n):
    return max(int(np.floor(4 * (n / 100) ** (2 / 9))), 1)


def rank_ic_hac(x, y, extra_overlap=0):
    """Spearman rank-IC + Newey-West HAC t-stat via regression of ranked-y on ranked-x.
    extra_overlap = forward horizon-1 for overlapping windows -> inflate NW lag.
    """
    n = len(x)
    if n < 10:
        return np.nan, np.nan, np.nan, n
    rx = rankdata(x)
    ry = rankdata(y)
    rx = (rx - rx.mean()) / rx.std()
    ry = (ry - ry.mean()) / ry.std()
    ic, p_sp = spearmanr(x, y)
    X = sm.add_constant(rx)
    lag = nw_lag(n) + extra_overlap
    res = sm.OLS(ry, X).fit(cov_type='HAC', cov_kwds={'maxlags': lag})
    t = float(res.tvalues[1])
    return float(ic), t, float(res.pvalues[1]), n


def block_boot_ci(x, y, block=6, B=3000):
    """Block bootstrap 95% CI for Spearman rank-IC (autocorr-robust)."""
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
# Main test: contemporaneous + forward(1/3/6m), LIVE-PIT vs NAIVE-revised
# ---------------------------------------------------------------------------
HORIZONS = [0, 1, 3, 6]  # 0 = contemporaneous month; >0 = forward k-month sum

results = {}     # (mode, name, target, k) -> dict
all_pvals = []   # for multiple comparison across the FORWARD predictive tests
pval_keys = []


def fwd_sum_return(target, k):
    """Forward k-month summed log-return ending k months ahead; k=0 = same month."""
    if k == 0:
        return ret_m[target]
    return ret_m[target].rolling(k).sum().shift(-k)


def run_block(mode):
    """mode = 'live' (PIT-aligned) or 'naive' (revised, no pub-lag)."""
    print('\n' + '=' * 90)
    print(f'[{mode.upper()}] rank-IC  contemporaneous(k=0) + forward(k=1/3/6m)   '
          + ('(signal shifted to its first-release date)' if mode == 'live'
             else '(signal at observation period, REVISED data -> lookahead-prone)'))
    print('=' * 90)
    print(f'{"candidate":18s} {"tgt":5s}'
          + ''.join(f'  k={k}:IC(t)' for k in HORIZONS))
    for name, sig in candidates.items():
        for tgt in TARGETS:
            row_disp = f'{name:18s} {tgt:5s}'
            for k in HORIZONS:
                fwd = fwd_sum_return(tgt, k)
                if mode == 'live':
                    # signal usable only from first-release date; for forward test the
                    # signal at availability-month t predicts returns over (t, t+k].
                    avail = pub_avail[name]
                    # map each signal period to the month-end of its availability date
                    avail_me = (avail + pd.offsets.MonthEnd(0))
                    s_live = pd.Series(sig.values, index=avail_me.values)
                    s_live = s_live[~s_live.index.duplicated(keep='last')].sort_index()
                    df = pd.concat([s_live.rename('sig'), fwd.rename('fwd')], axis=1,
                                   join='inner').dropna()
                else:
                    df = pd.concat([sig.rename('sig'), fwd.rename('fwd')], axis=1,
                                   join='inner').dropna()
                if len(df) < 24:
                    row_disp += '   n/a    '
                    continue
                ic, t, p, n = rank_ic_hac(df['sig'].values, df['fwd'].values,
                                          extra_overlap=max(k - 1, 0))
                lo, hi = block_boot_ci(df['sig'].values, df['fwd'].values,
                                       block=max(k, 6))
                key = (mode, name, tgt, k)
                results['|'.join(map(str, key))] = {
                    'ic': round(ic, 3), 't_nw': round(t, 2), 'p': round(p, 4),
                    'n': n, 'ci95': [round(lo, 3), round(hi, 3)],
                    'ci_cross_zero': bool(lo < 0 < hi)}
                # collect forward predictive p-values for multiple comparison (live, k>0)
                if mode == 'live' and k > 0:
                    all_pvals.append(p)
                    pval_keys.append('|'.join(map(str, key)))
                star = '*' if (p < 0.05 and not (lo < 0 < hi)) else ' '
                row_disp += f'  {ic:+.2f}({t:+.1f}){star}'
            print(row_disp)


run_block('naive')
run_block('live')

# ---------------------------------------------------------------------------
# Multiple comparison on LIVE forward predictive tests
# ---------------------------------------------------------------------------
print('\n' + '=' * 90)
print('[MULTIPLE COMPARISON] LIVE forward predictive tests (k>0)')
print('=' * 90)
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
# Half-split OOS sign consistency (LIVE, forward k=3 as representative)
# ---------------------------------------------------------------------------
print('\n' + '=' * 90)
print('[HALF-SPLIT OOS] sign consistency, LIVE forward k=3m')
print('=' * 90)
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
            print(f'  {name:18s} {tgt:5s} h1={ic1:+.2f} h2={ic2:+.2f}  MATCH (both>0.1) n={len(df)}')
n_match = sum(v['sign_match'] for v in oos.values())
print(f'  sign-match: {n_match}/{len(oos)} (chance=50%)')

# ---------------------------------------------------------------------------
# Save metrics
# ---------------------------------------------------------------------------
out = {
    'targets': TARGETS,
    'ret_range': [str(ret_m.index.min().date()), str(ret_m.index.max().date())],
    'pub_lag_days': PUB_LAG_DAYS,
    'adf': adf_res,
    'results': results,
    'multiple_comparison': {'m': m, 'bonferroni_alpha': float(bonf),
                            'bonf_survivors': bonf_surv,
                            'bh_crit_p': float(bh_crit), 'bh_survivors': bh_surv},
    'half_split_oos_k3': oos,
    'oos_sign_match': f'{n_match}/{len(oos)}',
}
with open(ROOT / 'validation-merit-cyclical-leading.json', 'w') as f:
    json.dump(out, f, indent=2)
print(f'\n[Saved] {ROOT / "validation-merit-cyclical-leading.json"}')
