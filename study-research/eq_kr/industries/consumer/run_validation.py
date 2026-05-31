"""
consumer industry validation — Layer 2 (macro) + Layer 3 (industry cycle) 실측.

산출:
- monthly returns (forward 1M / 3M) per ticker + sub-cluster eq-weight
- USDKRW yoy, CME 농산물 yoy, K-food 수출 (FRED proxy) yoy, retail sales (FRED) yoy
- M1: cross-sectional Rank-IC (monthly)
- M2: time-series lag-corr (subcluster panel)
- M3: regime breakdown (USDKRW regime × KRW regime)
- M4: 5-gate evaluation (N, SE, power, FDR, OOS)
- raw + factor-neutralized IC

실행: python run_validation.py
출력: validation-metrics.json + (call하는) validation-*.md 의 numeric data
"""

import json
import math
import time
from pathlib import Path
import numpy as np
import pandas as pd
import FinanceDataReader as fdr
import yfinance as yf
from pandas_datareader import data as pdr
from scipy import stats

# ============================================================
# Universe + sub-clusters
# ============================================================
UNIVERSE = {
    'A_domestic_food': ['097950', '271560', '004370'],   # CJ제일제당, 오리온, 농심
    'B_kfood_export':  ['003230', '005180', '035250'],   # 삼양, 빙그레, 대상
    'C_retail':        ['023530', '139480', '282330'],   # 롯데쇼핑, 이마트, BGF리테일
}
ALL_TICKERS = [t for c in UNIVERSE.values() for t in c]

START = '2018-01-01'
END   = '2026-05-30'

OUT_DIR = Path(__file__).parent
RAW_DIR = OUT_DIR / 'raw_data'
RAW_DIR.mkdir(exist_ok=True)

# ============================================================
# Data fetch
# ============================================================
def fetch_prices():
    """fetch daily close per ticker; return wide DataFrame (date × ticker)."""
    prices = {}
    for t in ALL_TICKERS:
        df = fdr.DataReader(t, START, END)
        prices[t] = df['Close']
    px = pd.DataFrame(prices)
    px.index = pd.to_datetime(px.index)
    return px

def fetch_usdkrw():
    df = fdr.DataReader('USD/KRW', START, END)
    s = df['Close'].copy()
    s.index = pd.to_datetime(s.index)
    return s.rename('USDKRW')

def fetch_cme_ag():
    """corn, wheat, soybean daily close from yfinance, eq-weight log-price index."""
    df = yf.download(['ZC=F','ZW=F','ZS=F'], start=START, end=END,
                     progress=False, auto_adjust=False)['Close']
    df = df.dropna(how='all')
    # eq-weight log-index (each series log-normalized then averaged)
    logp = np.log(df)
    z = (logp - logp.iloc[0]).mean(axis=1)  # eq-weight log-relative
    ag_index = np.exp(z).rename('CME_AG_EW')
    return ag_index, df

def fetch_fred_korea_retail():
    """FRED KORSARTMISMEI (monthly, lag, OECD MEI). last updated 2024-03 risk."""
    try:
        df = pdr.DataReader('KORSARTMISMEI', 'fred', '2015-01-01', END)
        return df['KORSARTMISMEI']
    except Exception as e:
        print('FRED retail FAIL', e)
        return None

def fetch_fred_kospi():
    """KOSPI index for baseline. fdr."""
    df = fdr.DataReader('KS11', START, END)
    s = df['Close'].copy()
    s.index = pd.to_datetime(s.index)
    return s.rename('KOSPI')

# ============================================================
# Returns + transforms
# ============================================================
def monthly_returns(px, fwd_periods=1):
    """compute month-end forward returns. px = daily close."""
    monthly = px.resample('ME').last()
    fwd = monthly.shift(-fwd_periods) / monthly - 1.0
    return fwd

def yoy_monthly(series):
    """monthly yoy. series = daily or monthly."""
    if series.index.freqstr is None:
        m = series.resample('ME').last()
    else:
        m = series
    return m / m.shift(12) - 1.0

def yoy_change(series):
    """compute yoy of a level series at the natural frequency."""
    s = series.copy()
    if hasattr(s.index, 'freq') and s.index.freq is None:
        # if monthly
        return s / s.shift(12) - 1.0
    return s / s.shift(12) - 1.0

# ============================================================
# Statistical helpers
# ============================================================
def spearman_ic(x, y):
    """Spearman rank correlation; return (ic, p, n)."""
    valid = (~pd.isna(x)) & (~pd.isna(y))
    n = valid.sum()
    if n < 3:
        return (np.nan, np.nan, n)
    rho, p = stats.spearmanr(x[valid], y[valid])
    return (rho, p, int(n))

def pearson_corr(x, y):
    valid = (~pd.isna(x)) & (~pd.isna(y))
    n = valid.sum()
    if n < 3:
        return (np.nan, np.nan, n)
    r, p = stats.pearsonr(x[valid], y[valid])
    return (r, p, int(n))

def newey_west_se(x, y, lag=3):
    """OLS slope + Newey-West HAC SE. returns (beta, se, t, n)."""
    valid = (~pd.isna(x)) & (~pd.isna(y))
    x_v = x[valid].values
    y_v = y[valid].values
    n = len(x_v)
    if n < 5:
        return (np.nan, np.nan, np.nan, n)
    X = np.column_stack([np.ones(n), x_v])
    beta = np.linalg.lstsq(X, y_v, rcond=None)[0]
    resid = y_v - X @ beta
    # NW variance
    XtX_inv = np.linalg.inv(X.T @ X)
    S = (resid[:, None] * X).T @ (resid[:, None] * X) / n
    for l in range(1, lag+1):
        w = 1 - l/(lag+1)
        for i in range(l, n):
            S += w * np.outer(resid[i]*X[i], resid[i-l]*X[i-l]) / n
            S += w * np.outer(resid[i-l]*X[i-l], resid[i]*X[i]) / n
    cov = n * XtX_inv @ S @ XtX_inv
    se = math.sqrt(cov[1,1])
    t = beta[1] / se if se > 0 else np.nan
    return (float(beta[1]), float(se), float(t), int(n))

def fdr_bh(pvals, alpha=0.10):
    """Benjamini-Hochberg FDR. returns list of (p, q, passed)."""
    arr = np.array([p for p in pvals if not np.isnan(p)])
    if len(arr) == 0:
        return []
    n = len(arr)
    order = np.argsort(arr)
    ranked = arr[order]
    q = ranked * n / (np.arange(1, n+1))
    # monotone
    for i in range(n-2, -1, -1):
        q[i] = min(q[i], q[i+1])
    # unorder
    q_unordered = np.empty_like(q)
    q_unordered[order] = q
    return [(float(p), float(qq), bool(qq < alpha))
            for p, qq in zip(arr, q_unordered)]

def power_mde(n, alpha=0.05, power=0.80):
    """approximate minimum detectable effect (Spearman IC) for given n.
       formula: t_alpha/2 + t_beta approx, ic_min = (z_alpha/2 + z_beta) / sqrt(n-3)."""
    z_a = stats.norm.ppf(1 - alpha/2)
    z_b = stats.norm.ppf(power)
    return (z_a + z_b) / math.sqrt(max(n - 3, 1))

# ============================================================
# Main analysis
# ============================================================
def main():
    print('=== consumer validation pipeline ===')
    print('1. fetching prices')
    px = fetch_prices()
    px.to_csv(RAW_DIR / 'prices.csv')
    print(f'  prices: shape={px.shape}, range={px.index.min().date()} ~ {px.index.max().date()}')

    print('2. fetching USDKRW')
    usdkrw = fetch_usdkrw()
    usdkrw.to_csv(RAW_DIR / 'usdkrw.csv')
    print(f'  USDKRW: n={len(usdkrw)}, last={usdkrw.iloc[-1]:.2f}')

    print('3. fetching CME ag (corn/wheat/soybean)')
    ag_idx, ag_raw = fetch_cme_ag()
    ag_raw.to_csv(RAW_DIR / 'cme_ag_raw.csv')
    ag_idx.to_csv(RAW_DIR / 'cme_ag_eqw.csv')
    print(f'  CME ag: n={len(ag_idx)}, last={ag_idx.iloc[-1]:.4f}')

    print('4. fetching FRED Korea retail')
    retail = fetch_fred_korea_retail()
    if retail is not None:
        retail.to_csv(RAW_DIR / 'fred_korea_retail.csv')
        print(f'  retail: n={len(retail)}, range={retail.index.min()} ~ {retail.index.max()}')

    print('5. fetching KOSPI baseline')
    kospi = fetch_fred_kospi()
    kospi.to_csv(RAW_DIR / 'kospi.csv')
    print(f'  KOSPI: n={len(kospi)}, last={kospi.iloc[-1]:.2f}')

    # ============================================================
    # Monthly aggregation
    # ============================================================
    print('\n=== monthly aggregation ===')
    monthly_px = px.resample('ME').last()
    monthly_ret = monthly_px.pct_change()
    fwd_1m = monthly_px.shift(-1) / monthly_px - 1.0
    fwd_3m = monthly_px.shift(-3) / monthly_px - 1.0

    # sub-cluster eq-weight monthly returns
    cluster_ret = {}
    cluster_fwd_1m = {}
    cluster_fwd_3m = {}
    for c, tickers in UNIVERSE.items():
        cluster_ret[c] = monthly_ret[tickers].mean(axis=1)
        cluster_fwd_1m[c] = fwd_1m[tickers].mean(axis=1)
        cluster_fwd_3m[c] = fwd_3m[tickers].mean(axis=1)
    cluster_ret = pd.DataFrame(cluster_ret)
    cluster_fwd_1m = pd.DataFrame(cluster_fwd_1m)
    cluster_fwd_3m = pd.DataFrame(cluster_fwd_3m)

    # macro factors monthly
    usdkrw_m = usdkrw.resample('ME').last()
    usdkrw_yoy = usdkrw_m / usdkrw_m.shift(12) - 1.0
    ag_m = ag_idx.resample('ME').last()
    ag_yoy = ag_m / ag_m.shift(12) - 1.0
    kospi_m = kospi.resample('ME').last()
    kospi_ret = kospi_m.pct_change()

    if retail is not None:
        retail_m = retail.copy()
        retail_m.index = pd.to_datetime(retail_m.index)
        retail_yoy = retail_m / retail_m.shift(12) - 1.0
    else:
        retail_yoy = None

    macro = pd.DataFrame({
        'USDKRW_yoy': usdkrw_yoy,
        'AG_yoy': ag_yoy,
        'KOSPI_ret': kospi_ret,
    })
    if retail_yoy is not None:
        macro['RETAIL_yoy'] = retail_yoy

    macro.to_csv(RAW_DIR / 'macro_monthly.csv')
    cluster_fwd_1m.to_csv(RAW_DIR / 'cluster_fwd_1m.csv')
    cluster_fwd_3m.to_csv(RAW_DIR / 'cluster_fwd_3m.csv')

    print(f'  cluster monthly returns: shape={cluster_ret.shape}')
    print(f'  macro monthly: shape={macro.shape}')

    # ============================================================
    # M2: time-series lag correlation (sub-cluster panel)
    # ============================================================
    print('\n=== M2: lag-corr (cluster fwd return vs macro) ===')
    results = {'M2_lag_corr': []}

    for fwd_label, fwd_df in [('fwd_1m', cluster_fwd_1m), ('fwd_3m', cluster_fwd_3m)]:
        for cluster, fwd_series in fwd_df.items():
            for macro_name in macro.columns:
                ms = macro[macro_name]
                # contemporaneous + lag 1, 3, 6
                for lag in [0, 1, 3, 6]:
                    if lag == 0:
                        x = ms
                    else:
                        x = ms.shift(lag)
                    rho, p, n = spearman_ic(x, fwd_series)
                    beta, se, t, _ = newey_west_se(x, fwd_series, lag=max(3, lag+1))
                    results['M2_lag_corr'].append({
                        'cluster': cluster, 'fwd': fwd_label, 'macro': macro_name,
                        'lag_months': lag, 'spearman_ic': rho, 'p': p, 'n': n,
                        'beta': beta, 'nw_se': se, 'nw_t': t,
                    })

    # ============================================================
    # M1: cross-sectional Rank-IC (monthly)
    #    each month: rank tickers by macro exposure (here: own 12m yoy ret as momentum sign-flipped)
    #    OR by ticker-level factor exposure (here using simple sub-cluster as factor)
    # ============================================================
    print('\n=== M1: cross-sectional Rank-IC ===')
    # Simple cross-sectional IC: rank tickers by "USDKRW yoy regime" (each month, same value across tickers)
    # → degenerate. Better: rank tickers by their *own* trailing 12m beta to USDKRW.
    # We compute trailing 12m beta (rolling) per ticker × USDKRW yoy, then cross-sectional IC vs fwd return.
    monthly_ret_df = monthly_ret  # date × ticker
    # rolling 12m beta to USDKRW yoy
    betas = {}
    for t in ALL_TICKERS:
        b_series = []
        for end_idx in range(12, len(monthly_ret_df)):
            window = monthly_ret_df[t].iloc[end_idx-12:end_idx]
            macro_window = usdkrw_yoy.reindex(window.index)
            valid = (~window.isna()) & (~macro_window.isna())
            if valid.sum() < 6:
                b_series.append((monthly_ret_df.index[end_idx], np.nan))
                continue
            cov = np.cov(window[valid], macro_window[valid])
            var = np.var(macro_window[valid], ddof=1)
            b = cov[0,1] / var if var > 0 else np.nan
            b_series.append((monthly_ret_df.index[end_idx], b))
        b_df = pd.Series(dict(b_series))
        betas[t] = b_df
    betas_df = pd.DataFrame(betas)
    betas_df.to_csv(RAW_DIR / 'usdkrw_betas_rolling12m.csv')

    # cross-sectional IC each month: betas (z-score) vs fwd_1m
    ic_series = []
    for dt in betas_df.index:
        if dt not in fwd_1m.index:
            continue
        b_row = betas_df.loc[dt].dropna()
        f_row = fwd_1m.loc[dt].reindex(b_row.index).dropna()
        common = b_row.index.intersection(f_row.index)
        if len(common) < 4:
            continue
        b_z = (b_row[common] - b_row[common].mean()) / b_row[common].std(ddof=1)
        rho, p = stats.spearmanr(b_z, f_row[common])
        ic_series.append({'date': dt, 'ic': rho, 'p': p, 'n_cross': len(common)})
    ic_df = pd.DataFrame(ic_series).set_index('date')
    ic_df.to_csv(RAW_DIR / 'm1_cross_sectional_ic.csv')

    n_ic = len(ic_df)
    ic_mean = ic_df['ic'].mean()
    ic_sd = ic_df['ic'].std(ddof=1)
    ic_se = ic_sd / math.sqrt(n_ic) if n_ic > 1 else np.nan
    ic_t = ic_mean / ic_se if ic_se and ic_se > 0 else np.nan
    ic_ci = [ic_mean - 1.96*ic_se, ic_mean + 1.96*ic_se]
    results['M1_cross_sectional_ic_usdkrw_beta'] = {
        'ic_mean': float(ic_mean) if not np.isnan(ic_mean) else None,
        'ic_sd': float(ic_sd) if not np.isnan(ic_sd) else None,
        'ic_se': float(ic_se) if ic_se and not np.isnan(ic_se) else None,
        'ic_t': float(ic_t) if ic_t and not np.isnan(ic_t) else None,
        'ic_ci_95': [float(c) if not np.isnan(c) else None for c in ic_ci],
        'n_months': int(n_ic),
        'mde': float(power_mde(n_ic)) if n_ic > 5 else None,
    }

    # ============================================================
    # M3: regime breakdown (USDKRW yoy regime × cluster fwd return)
    # ============================================================
    print('\n=== M3: regime breakdown ===')
    regimes = {'M3_regime_usdkrw': []}
    for cluster, fwd_series in cluster_fwd_3m.items():
        df_r = pd.DataFrame({'fwd': fwd_series, 'usdkrw_yoy': usdkrw_yoy}).dropna()
        # 3 regime: yoy < -0.05 (KRW 강세) / -0.05~+0.05 / yoy > +0.05 (KRW 약세)
        df_r['regime'] = pd.cut(df_r['usdkrw_yoy'],
                                bins=[-np.inf, -0.05, 0.05, np.inf],
                                labels=['KRW_strong', 'neutral', 'KRW_weak'])
        for reg, grp in df_r.groupby('regime', observed=True):
            n = len(grp)
            mean = grp['fwd'].mean()
            sd = grp['fwd'].std(ddof=1) if n > 1 else np.nan
            se = sd / math.sqrt(n) if n > 1 else np.nan
            t = mean / se if se and se > 0 else np.nan
            regimes['M3_regime_usdkrw'].append({
                'cluster': cluster, 'regime': str(reg), 'n': int(n),
                'mean_fwd_3m': float(mean) if not np.isnan(mean) else None,
                'se': float(se) if se and not np.isnan(se) else None,
                't': float(t) if t and not np.isnan(t) else None,
            })

    # ============================================================
    # H6: sub-cluster spread (B - A) partial-corr after USDKRW + KOSPI control
    # ============================================================
    print('\n=== H6: B-A spread partial-corr ===')
    spread = cluster_ret['B_kfood_export'] - cluster_ret['A_domestic_food']
    spread_df = pd.DataFrame({
        'spread': spread,
        'usdkrw_yoy': usdkrw_yoy,
        'kospi_ret': kospi_ret,
    }).dropna()
    # residualize spread on KOSPI return; then corr with USDKRW yoy
    if len(spread_df) > 10:
        from numpy.linalg import lstsq
        X = np.column_stack([np.ones(len(spread_df)), spread_df['kospi_ret']])
        beta_kospi = lstsq(X, spread_df['spread'], rcond=None)[0]
        resid = spread_df['spread'] - X @ beta_kospi
        partial_rho, partial_p = stats.spearmanr(resid, spread_df['usdkrw_yoy'])
        results['H6_spread_partial'] = {
            'n': len(spread_df),
            'partial_spearman': float(partial_rho),
            'partial_p': float(partial_p),
            'note': 'spread = B(export) - A(domestic); residualized on KOSPI return; vs USDKRW yoy',
        }

    # ============================================================
    # OOS gate: IS (2018-2022) vs OOS (2023-2026)
    # ============================================================
    print('\n=== OOS gate (IS 2018-2022 / OOS 2023-2026) ===')
    is_end = '2022-12-31'
    oos_start = '2023-01-01'

    oos_results = {}
    for fwd_label, fwd_df in [('fwd_1m', cluster_fwd_1m), ('fwd_3m', cluster_fwd_3m)]:
        for cluster, fwd_series in fwd_df.items():
            for macro_name, lag in [('USDKRW_yoy', 0), ('AG_yoy', 3), ('KOSPI_ret', 0)]:
                ms = macro[macro_name].shift(lag) if lag > 0 else macro[macro_name]
                df_io = pd.DataFrame({'x': ms, 'y': fwd_series}).dropna()
                if len(df_io) < 20:
                    continue
                is_part = df_io.loc[:is_end]
                oos_part = df_io.loc[oos_start:]
                if len(is_part) < 6 or len(oos_part) < 6:
                    continue
                is_rho, is_p = stats.spearmanr(is_part['x'], is_part['y'])
                oos_rho, oos_p = stats.spearmanr(oos_part['x'], oos_part['y'])
                oos_results[f'{cluster}.{fwd_label}.{macro_name}.lag{lag}'] = {
                    'is_n': len(is_part), 'is_ic': float(is_rho), 'is_p': float(is_p),
                    'oos_n': len(oos_part), 'oos_ic': float(oos_rho), 'oos_p': float(oos_p),
                    'oos_ratio': float(oos_rho / is_rho) if is_rho != 0 else None,
                }
    results['OOS_gate'] = oos_results

    # ============================================================
    # FDR correction across M2 lag-corr p-values
    # ============================================================
    print('\n=== FDR correction (BH q<0.10) ===')
    m2_pvals = [r['p'] for r in results['M2_lag_corr'] if r['p'] is not None and not np.isnan(r['p'])]
    fdr_result = fdr_bh(m2_pvals, alpha=0.10)
    # match back
    results['FDR_summary'] = {
        'n_tests': len(m2_pvals),
        'n_passed_q010': sum(1 for _, _, ok in fdr_result if ok),
        'alpha': 0.10,
    }

    results.update(regimes)

    # ============================================================
    # save
    # ============================================================
    out_path = OUT_DIR / 'validation-metrics.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f'\n[OK] saved {out_path}')

    return results

if __name__ == '__main__':
    main()
