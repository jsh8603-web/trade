"""validation-regime-conditional-poc.py

PROOF-OF-CONCEPT: does regime-conditional splitting RESCUE forward predictivity that
full-sample pooled forward IC misses?

Core hypothesis under test:
  "Full-sample pooled forward IC may be insignificant/weak, yet conditioning on a macro
   regime (e.g. high vs low inflation) the relationship can come alive."

This script tests that claim on cyclical leading-var signals as a PoC. It is a
SAMPLE-STAGE exploration -- NO yaml / code edits, NO commits. Validation output only.

Signals (deliberately mixed by full-sample strength, to see the split effect):
  1. DGORDER_yoy -> XLE   (full-sample LIVE k=6 IC=+0.31 p=0.0016 SIGNIFICANT)
  2. NEWORDER_yoy -> XLE  (full-sample LIVE collapses: k=3 IC=+0.137 p=0.0999; k=6 p=0.0545) <- most interesting
  3. T10Y2Y (curve) -> XLI and -> SOXX (full-sample DEAD: all p>0.5) <- can a regime revive it?

Regime definitions (ALL disclosed -- snooping transparency; we tried these, not cherry-picked):
  R1  CPI-yoy  high vs low   (CPIAUCSL yoy, median split)   -- macro inflation, PIT-lagged ~12d
  R2  BREAKEVEN high vs low  (T5YIE 5yr breakeven, median split) -- market inflation, PIT-clean daily
  R3  GROWTH curve+/- : T10Y2Y sign (>0 normal vs <0 inverted) -- PIT-clean; NOT used to condition the curve signal itself (self-conditioning ban)

PIT-safety (lookahead avoidance -- the central rigor concern):
  - Each SIGNAL observation is already mapped to its first-release availability month-end
    (reused from validation-merit-cyclical-leading: pub-lag shift). Returns measured strictly
    AFTER that.
  - The REGIME LABEL attached to a signal observation must ALSO be known at that availability
    month. We align the regime series to ITS OWN release availability and take the last value
    knowable at-or-before the signal availability month. NO forward regime info.
  - Median thresholds are EXPANDING (computed only from regime history up to the signal's
    availability month) so the split itself is PIT-safe (not a full-sample median lookahead).

Two regime treatments:
  (a) HARD split: subset IC within each regime bucket.
  (b) BELIEF-weighted: soft regime probability b(t) in [0,1] via logistic of standardized
      distance from the expanding threshold; weighted Spearman-equivalent (weighted rank corr)
      computed per regime-tilt. System uses belief mix b(t), so hard split over-simplifies.

Stats obligations (empirical-claim-presentation + small-n-rigor):
  - per-bucket n reported; n<30 bucket flagged INSUFFICIENT
  - Newey-West HAC t on Fisher-z rank corr (overlapping forward windows -> inflated lag)
  - block-bootstrap 95% CI
  - Bonferroni + BH-FDR over ALL regime-conditional comparisons (m disclosed, > full-sample m)
  - half-split-within-regime sign check where bucket n permits
No synthetic data.
"""
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, rankdata, norm
from statsmodels.tsa.stattools import adfuller
import statsmodels.api as sm

warnings.filterwarnings('ignore')
rng = np.random.default_rng(20260601)

ROOT = Path(r'D:/projects/Inv/study-research/eq_us_cyclical/raw')
FRED = ROOT / 'fred'

# publication lags (days) -- signals from merit-pit-probe; CPI probed in this session (~12d)
PUB_LAG_DAYS = {'NEWORDER': 56, 'DGORDER': 56, 'CPIAUCSL': 12}


def load_fred(ticker):
    df = pd.read_csv(FRED / f'{ticker}.csv', parse_dates=['observation_date'])
    df = df.rename(columns={'observation_date': 'date', ticker: 'val'})
    df['val'] = pd.to_numeric(df['val'], errors='coerce')
    return df.dropna().set_index('date').sort_index()['val']


# ---------------------------------------------------------------------------
# Returns: monthly log-returns
# ---------------------------------------------------------------------------
close = pd.read_csv(ROOT / 'yfinance/sector_etf_close.csv', parse_dates=['Date'], index_col='Date')
TARGETS = ['SOXX', 'XLE', 'XLI']
logret_d = np.log(close[TARGETS]).diff()
ret_m = logret_d.resample('ME').sum().dropna(how='all')


def fwd_sum_return(target, k):
    if k == 0:
        return ret_m[target]
    return ret_m[target].rolling(k).sum().shift(-k)


# ---------------------------------------------------------------------------
# Signals -> PIT first-release availability month-end (live alignment)
# ---------------------------------------------------------------------------
def macro_yoy_live(sid):
    s = load_fred(sid)
    sig = s.pct_change(12).dropna()
    period_end = sig.index + pd.offsets.MonthEnd(0)
    avail = period_end + pd.Timedelta(days=PUB_LAG_DAYS[sid])
    avail_me = (avail + pd.offsets.MonthEnd(0))
    out = pd.Series(sig.values, index=avail_me)
    out = out[~out.index.duplicated(keep='last')].sort_index()
    return out  # indexed at availability month-end


def curve_live(sid):
    s = load_fred(sid).resample('ME').last().dropna()  # market-priced, same-day knowable
    return s


SIGNALS = {
    'DGORDER_yoy': macro_yoy_live('DGORDER'),
    'NEWORDER_yoy': macro_yoy_live('NEWORDER'),
    'T10Y2Y': curve_live('T10Y2Y'),
}
# signal -> target pairings of interest
PAIRS = [('DGORDER_yoy', 'XLE'), ('NEWORDER_yoy', 'XLE'),
         ('T10Y2Y', 'XLI'), ('T10Y2Y', 'SOXX')]
HORIZONS = [3, 6]  # forward months (where full-sample DGORDER->XLE peaked)

# ---------------------------------------------------------------------------
# Regime series -> PIT-aligned availability month-end, with EXPANDING median threshold
# ---------------------------------------------------------------------------
# R1 CPI yoy (lagged ~12d). R2 T5YIE breakeven (daily PIT-clean). R3 curve sign (PIT-clean).
cpi = load_fred('CPIAUCSL')
cpi_yoy = cpi.pct_change(12).dropna()
_cpi_pe = cpi_yoy.index + pd.offsets.MonthEnd(0)
_cpi_av = (_cpi_pe + pd.Timedelta(days=PUB_LAG_DAYS['CPIAUCSL']) + pd.offsets.MonthEnd(0))
cpi_live = pd.Series(cpi_yoy.values, index=_cpi_av)
cpi_live = cpi_live[~cpi_live.index.duplicated(keep='last')].sort_index()

t5 = pd.read_csv(FRED / 'T5YIE.csv', parse_dates=['observation_date']).rename(
    columns={'observation_date': 'date', 'T5YIE': 'val'})
t5 = t5.dropna().set_index('date').sort_index()['val']
be_live = t5.resample('ME').last().dropna()  # market, same-day knowable

curve_lvl = load_fred('T10Y2Y').resample('ME').last().dropna()  # for R3 growth regime


def expanding_median_label(series, min_hist=24):
    """PIT-safe high/low label: at each month, threshold = expanding median of history
    up to and including that month. label 1 = >= threshold (high), 0 = < (low).
    Also returns standardized distance for belief weighting."""
    s = series.sort_index()
    med = s.expanding(min_periods=min_hist).median()
    std = s.expanding(min_periods=min_hist).std()
    label = (s >= med).astype(float)
    z = (s - med) / std.replace(0, np.nan)
    label[med.isna()] = np.nan
    return label, z


cpi_label, cpi_z = expanding_median_label(cpi_live)
be_label, be_z = expanding_median_label(be_live)
# R3 growth: curve sign is an absolute PIT threshold (0), no expanding needed
curve_label = (curve_lvl > 0).astype(float)
curve_z = curve_lvl / curve_lvl.expanding(min_periods=24).std().replace(0, np.nan)

REGIMES = {
    'CPI_inflation': (cpi_label, cpi_z, {1: 'highInfl', 0: 'lowInfl'}),
    'BE_breakeven': (be_label, be_z, {1: 'highBE', 0: 'lowBE'}),
    'GROWTH_curve': (curve_label, curve_z, {1: 'normalCurve', 0: 'invertedCurve'}),
}


def regime_known_at(label_series, target_index):
    """For each target month-end, last regime label knowable AT-OR-BEFORE that month (PIT)."""
    lab = label_series.dropna().sort_index()
    out = lab.reindex(lab.index.union(target_index)).ffill().reindex(target_index)
    return out


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------
def nw_lag(n, extra=0):
    return max(int(np.floor(4 * (n / 100) ** (2 / 9))), 1) + extra


def rank_ic_hac(x, y, extra_overlap=0):
    n = len(x)
    if n < 10:
        return np.nan, np.nan, np.nan, n
    ry = rankdata(y); rx = rankdata(x)
    rx = (rx - rx.mean()) / rx.std(); ry = (ry - ry.mean()) / ry.std()
    ic, _ = spearmanr(x, y)
    X = sm.add_constant(rx)
    res = sm.OLS(ry, X).fit(cov_type='HAC', cov_kwds={'maxlags': nw_lag(n, extra_overlap)})
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


def weighted_rank_corr(x, y, w):
    """Belief-weighted Spearman: weighted Pearson on ranks. w >=0 soft regime membership."""
    if w.sum() < 1e-6 or len(x) < 10:
        return np.nan, np.nan
    rx = rankdata(x).astype(float); ry = rankdata(y).astype(float)
    wm = w / w.sum()
    mx = (wm * rx).sum(); my = (wm * ry).sum()
    cov = (wm * (rx - mx) * (ry - my)).sum()
    vx = (wm * (rx - mx) ** 2).sum(); vy = (wm * (ry - my) ** 2).sum()
    if vx <= 0 or vy <= 0:
        return np.nan, np.nan
    r = cov / np.sqrt(vx * vy)
    # effective n via Kish, approximate p via Fisher-z
    n_eff = (w.sum() ** 2) / (w ** 2).sum()
    if n_eff < 4:
        return float(r), np.nan
    z = np.arctanh(np.clip(r, -0.999, 0.999)) * np.sqrt(n_eff - 3)
    p = 2 * (1 - norm.cdf(abs(z)))
    return float(r), float(p)


# ---------------------------------------------------------------------------
# Full-sample baselines (LIVE, for reference) + regime-conditional tests
# ---------------------------------------------------------------------------
print('=' * 100)
print('REGIME-CONDITIONAL PoC -- does regime split rescue forward predictivity?')
print('ret range:', ret_m.index.min().date(), '->', ret_m.index.max().date())
print('=' * 100)

# ADF on regime drivers (1.7-A awareness)
adf = {}
for nm, s in [('CPI_yoy', cpi_live), ('T5YIE', be_live), ('T10Y2Y', curve_lvl)]:
    st, p, *_ = adfuller(s.dropna().values, regression='c', autolag='AIC')
    adf[nm] = {'adf_p': round(float(p), 4), 'n': int(len(s))}
print('[ADF regime drivers]', adf)

results = {}
full_base = {}
reg_pvals = []      # all regime-conditional HARD forward p-values for multiple comparison
reg_keys = []

for sig_name, tgt in PAIRS:
    sig = SIGNALS[sig_name]
    for k in HORIZONS:
        fwd = fwd_sum_return(tgt, k)
        base = pd.concat([sig.rename('sig'), fwd.rename('fwd')], axis=1, join='inner').dropna()
        if len(base) >= 24:
            ic, t, p, n = rank_ic_hac(base['sig'].values, base['fwd'].values, extra_overlap=k - 1)
            lo, hi = block_boot_ci(base['sig'].values, base['fwd'].values, block=k)
            full_base[f'{sig_name}|{tgt}|k{k}'] = {
                'ic': round(ic, 3), 'p': round(p, 4), 'n': n,
                'ci95': [round(lo, 3), round(hi, 3)]}
        else:
            full_base[f'{sig_name}|{tgt}|k{k}'] = {'ic': None, 'note': 'n<24'}

        for reg_name, (label_s, z_s, lab_map) in REGIMES.items():
            # self-conditioning ban: don't condition curve signal on growth-curve regime
            if sig_name == 'T10Y2Y' and reg_name == 'GROWTH_curve':
                continue
            reg_lab = regime_known_at(label_s, base.index)
            reg_zz = regime_known_at(z_s, base.index)
            df = base.copy()
            df['reg'] = reg_lab.values
            df['z'] = reg_zz.values
            df = df.dropna()
            if len(df) < 20:
                continue
            # ---- HARD split ----
            for bucket_val, bucket_nm in lab_map.items():
                sub = df[df['reg'] == bucket_val]
                key = f'{sig_name}|{tgt}|k{k}|{reg_name}|{bucket_nm}'
                if len(sub) < 12:
                    results[key] = {'mode': 'hard', 'n': int(len(sub)),
                                    'verdict': 'INSUFFICIENT(n<12)'}
                    continue
                ic, t, p, n = rank_ic_hac(sub['sig'].values, sub['fwd'].values,
                                          extra_overlap=k - 1)
                lo, hi = block_boot_ci(sub['sig'].values, sub['fwd'].values, block=k)
                rec = {'mode': 'hard', 'ic': round(ic, 3), 't_nw': round(t, 2),
                       'p': round(p, 4), 'n': int(n), 'ci95': [round(lo, 3), round(hi, 3)],
                       'ci_cross_zero': bool(lo < 0 < hi),
                       'insufficient': bool(n < 30)}
                results[key] = rec
                reg_pvals.append(p); reg_keys.append(key)
            # ---- BELIEF-weighted (soft membership via logistic of z) ----
            # b_high = sigmoid(z) ; b_low = 1 - b_high. Use temperature 1.
            b_high = 1.0 / (1.0 + np.exp(-df['z'].values))
            for tilt, w in [('highTilt', b_high), ('lowTilt', 1.0 - b_high)]:
                r, p = weighted_rank_corr(df['sig'].values, df['fwd'].values, np.asarray(w))
                n_eff = (w.sum() ** 2) / (np.asarray(w) ** 2).sum()
                results[f'{sig_name}|{tgt}|k{k}|{reg_name}|BELIEF_{tilt}'] = {
                    'mode': 'belief', 'wic': None if r is None or np.isnan(r) else round(r, 3),
                    'p': None if p is None or np.isnan(p) else round(p, 4),
                    'n_eff': round(float(n_eff), 1)}

# ---------------------------------------------------------------------------
# Multiple comparison over ALL hard regime-conditional forward tests
# ---------------------------------------------------------------------------
m = len(reg_pvals)
pv = np.array(reg_pvals)
bonf = 0.05 / m if m else np.nan
order = np.argsort(pv); sp = pv[order]
bh_crit = 0.0
for kk in range(m, 0, -1):
    if sp[kk - 1] <= kk / m * 0.05:
        bh_crit = sp[kk - 1]; break
bonf_surv = [reg_keys[i] for i in range(m) if pv[i] < bonf]
bh_surv = [reg_keys[i] for i in range(m) if pv[i] <= bh_crit]

print('\n' + '=' * 100)
print('[MULTIPLE COMPARISON] hard regime-conditional forward tests')
print(f'  m = {m}  (vs full-sample m=24 in parent study -> bigger penalty)')
print(f'  Bonferroni alpha = 0.05/{m} = {bonf:.5f}  survivors: {len(bonf_surv)} {bonf_surv}')
print(f'  BH-FDR q=0.05 crit p = {bh_crit:.5f}  survivors: {len(bh_surv)}')
for kk in bh_surv:
    print('     ', kk, results[kk])

# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------
print('\n' + '=' * 100)
print('[SUMMARY] full-sample vs regime-split (HARD)  -- signal|tgt|k')
print('=' * 100)
for sig_name, tgt in PAIRS:
    for k in HORIZONS:
        fb = full_base[f'{sig_name}|{tgt}|k{k}']
        print(f'\n{sig_name} -> {tgt}  fwd k={k}m')
        print(f'   FULL : IC={fb.get("ic")} p={fb.get("p")} n={fb.get("n")} ci={fb.get("ci95")}')
        for reg_name, (_, _, lab_map) in REGIMES.items():
            if sig_name == 'T10Y2Y' and reg_name == 'GROWTH_curve':
                continue
            for bucket_val, bucket_nm in lab_map.items():
                key = f'{sig_name}|{tgt}|k{k}|{reg_name}|{bucket_nm}'
                r = results.get(key)
                if not r:
                    continue
                if r.get('verdict'):
                    print(f'   {reg_name:14s} {bucket_nm:12s} {r["verdict"]} n={r["n"]}')
                else:
                    surv = 'BONF-SURV' if key in bonf_surv else ('BH-SURV' if key in bh_surv else '')
                    insf = ' INSUFFICIENT(n<30)' if r.get('insufficient') else ''
                    print(f'   {reg_name:14s} {bucket_nm:12s} IC={r["ic"]:+.3f} p={r["p"]:.4f} '
                          f'n={r["n"]} ci={r["ci95"]} {surv}{insf}')

out = {
    'ret_range': [str(ret_m.index.min().date()), str(ret_m.index.max().date())],
    'pub_lag_days': PUB_LAG_DAYS,
    'adf_regime_drivers': adf,
    'regimes_tried': list(REGIMES.keys()),
    'pairs': [f'{s}->{t}' for s, t in PAIRS],
    'horizons': HORIZONS,
    'full_sample_baseline': full_base,
    'regime_conditional': results,
    'multiple_comparison': {
        'm': m, 'bonferroni_alpha': float(bonf), 'bonf_survivors': bonf_surv,
        'bh_crit_p': float(bh_crit), 'bh_survivors': bh_surv},
}
with open(ROOT / 'validation-regime-conditional-poc.json', 'w') as f:
    json.dump(out, f, indent=2)
print(f'\n[Saved] {ROOT / "validation-regime-conditional-poc.json"}')
