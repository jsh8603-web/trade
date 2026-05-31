"""Long-frame Scenario A — 4 sector OLS regression with Newey-West HAC SE.

Spec (1:1 match verify):
  y_{i,t} = α_i + β_{i,us10y} · Δus10y_t + β_{i,dxy} · r_dxy_t + β_{i,oil} · r_oil_t + ε_{i,t}
  i ∈ {SOXX, XLB, XLI, XLE}, daily frequency.
  Δus10y_t = DGS10_t - DGS10_{t-1} (yield level first-difference, % point)
  r_dxy_t  = pct_change of DX-Y.NYB close
  r_oil_t  = pct_change of CL=F close
  Newey-West HAC SE, lag = floor(4 * (n/100)^(2/9))
  95% CI = β ± 1.96 * SE; Bonferroni alpha = 0.05/12 = 0.00417 (4 industries × 3 drivers)

Frame: 2001-07-13 (SOXX inception) ~ 2026-05-29 (last yfinance available).
Compare with M3 frame (2021-12 ~ 2024-12) β from raw/m3-metrics.json.

⛔ No synthetic data. yfinance fetch + raw/fred/DGS10.csv + raw/yfinance/sector_etf_close.csv.
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import yfinance as yf

ROOT = Path('D:/projects/Inv/study-research/eq_us_cyclical/raw')
OUT_TXT = ROOT / 'scenarioA_output.txt'

FRAME_START = '2001-07-13'
FRAME_END = '2026-05-29'
INDUSTRIES = ['SOXX', 'XLB', 'XLI', 'XLE']
N_INDUSTRIES = 4
N_DRIVERS = 3
N_COMPARISONS = N_INDUSTRIES * N_DRIVERS  # 12
ALPHA = 0.05
BONFERRONI = ALPHA / N_COMPARISONS  # 0.00417

lines = []
def log(msg=''):
    print(msg)
    lines.append(msg)

log('='*78)
log(f'Long-frame Scenario A — frame {FRAME_START} ~ {FRAME_END}')
log(f'Industries: {INDUSTRIES}  Drivers: Δus10y, r_dxy, r_oil')
log(f'Bonferroni α/12 = {BONFERRONI:.5f} (raw α=0.05)')
log('='*78)

# ---- Load sector ETF closes ----
close_csv = ROOT / 'yfinance/sector_etf_close.csv'
etf = pd.read_csv(close_csv, parse_dates=['Date'], index_col='Date')
etf = etf.loc[FRAME_START:FRAME_END, INDUSTRIES]
log(f'\n[Data] sector ETF closes: {close_csv}')
log(f'       columns: {INDUSTRIES} | rows: {len(etf)}')
log(f'       first non-null per industry:')
for s in INDUSTRIES:
    first = etf[s].first_valid_index()
    last = etf[s].last_valid_index()
    log(f'         {s}: {first.date() if first is not None else "N/A"} ~ {last.date() if last is not None else "N/A"} (n={etf[s].notna().sum()})')

# ---- Load DGS10 (us10y) ----
dgs10_csv = ROOT / 'fred/DGS10.csv'
dgs10 = pd.read_csv(dgs10_csv, parse_dates=['observation_date'], index_col='observation_date')
dgs10 = dgs10.loc[FRAME_START:FRAME_END]
dgs10.columns = ['us10y']
log(f'\n[Data] us10y (DGS10): {dgs10_csv}')
log(f'       rows: {len(dgs10)} | window: {dgs10.index.min().date()} ~ {dgs10.index.max().date()}')

# ---- Fetch dxy (^DXY) + oil (CL=F) via yfinance ----
log(f'\n[Data] yfinance fetch: DX-Y.NYB (dxy) + CL=F (oil WTI futures)')
log(f'       period: {FRAME_START} ~ {FRAME_END}')
try:
    dxy_raw = yf.download('DX-Y.NYB', start=FRAME_START, end=FRAME_END, progress=False, auto_adjust=False)
    if 'Close' in dxy_raw.columns:
        dxy = dxy_raw['Close']
        if isinstance(dxy, pd.DataFrame):
            dxy = dxy.iloc[:, 0]
    else:
        dxy = dxy_raw.iloc[:, 0]
    dxy.name = 'dxy'
    log(f'       dxy fetched: n={len(dxy)} | {dxy.index.min().date()} ~ {dxy.index.max().date()}')
except Exception as e:
    log(f'       dxy fetch FAILED: {e}')
    sys.exit(1)

try:
    oil_raw = yf.download('CL=F', start=FRAME_START, end=FRAME_END, progress=False, auto_adjust=False)
    if 'Close' in oil_raw.columns:
        oil = oil_raw['Close']
        if isinstance(oil, pd.DataFrame):
            oil = oil.iloc[:, 0]
    else:
        oil = oil_raw.iloc[:, 0]
    oil.name = 'oil'
    log(f'       oil fetched: n={len(oil)} | {oil.index.min().date()} ~ {oil.index.max().date()}')
except Exception as e:
    log(f'       oil fetch FAILED: {e}')
    sys.exit(1)

# ---- Build daily panel ----
# tz-naive 정렬
for df in [etf, dgs10]:
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
dxy.index = dxy.index.tz_localize(None) if dxy.index.tz is not None else dxy.index
oil.index = oil.index.tz_localize(None) if oil.index.tz is not None else oil.index

# Derive returns/changes
etf_ret = etf.pct_change()
d_us10y = dgs10['us10y'].diff()  # first difference (yield level change, % point)
r_dxy = dxy.pct_change()
r_oil = oil.pct_change()

panel = pd.concat([etf_ret, d_us10y.rename('d_us10y'), r_dxy.rename('r_dxy'), r_oil.rename('r_oil')], axis=1)
# Inner join (drop any row with NaN in driver or any industry)
panel = panel.dropna(subset=['d_us10y', 'r_dxy', 'r_oil'])
log(f'\n[Panel] after driver inner-join: n={len(panel)} | {panel.index.min().date()} ~ {panel.index.max().date()}')

# Industry별로 가용한 부분만 사용 (SOXX 2001-07-13 시작과 자동 정합)
log(f'\n[Panel] per-industry valid rows (after driver join):')
industry_n = {}
for s in INDUSTRIES:
    sub = panel.dropna(subset=[s])
    industry_n[s] = len(sub)
    log(f'         {s}: n={industry_n[s]}')

# ---- Newey-West lag ----
n_for_lag = panel.dropna(subset=INDUSTRIES + ['d_us10y', 'r_dxy', 'r_oil']).shape[0]
NW_LAG = int(np.floor(4 * (n_for_lag / 100) ** (2/9)))
log(f'\n[HAC] Newey-West lag = floor(4·(n/100)^(2/9)) = floor(4·({n_for_lag}/100)^(2/9)) = {NW_LAG}')

# ---- Regression per industry ----
log(f'\n' + '='*78)
log(f'§1. Long-frame OLS + Newey-West HAC SE per industry')
log('='*78)
log(f'Spec: r_{{i,t}} = α_i + β_{{us10y}} · Δus10y_t + β_{{dxy}} · r_dxy_t + β_{{oil}} · r_oil_t + ε_{{i,t}}')
log(f'Bonferroni-adjusted α = {BONFERRONI:.5f}  (12 simultaneous comparisons)')
log(f'')
log(f'{"industry":>8s} {"n":>6s} {"coef":>10s} {"point":>10s} {"NW_SE":>10s} {"t-stat":>8s} {"p-raw":>10s} {"CI95_low":>10s} {"CI95_high":>10s} {"Bonf_pass":>10s}')

results = {}
for s in INDUSTRIES:
    sub = panel.dropna(subset=[s, 'd_us10y', 'r_dxy', 'r_oil'])
    y = sub[s].values
    X = sub[['d_us10y', 'r_dxy', 'r_oil']].values
    X1 = sm.add_constant(X)
    model = sm.OLS(y, X1)
    res = model.fit(cov_type='HAC', cov_kwds={'maxlags': NW_LAG})
    n = len(sub)

    coefs = ['alpha', 'beta_us10y', 'beta_dxy', 'beta_oil']
    industry_res = {'n': int(n)}
    for i, c in enumerate(coefs):
        point = res.params[i]
        se = res.bse[i]
        t_stat = res.tvalues[i]
        p_raw = res.pvalues[i]
        ci_low, ci_high = point - 1.96 * se, point + 1.96 * se
        bonf_pass = 'PASS' if p_raw < BONFERRONI else 'fail'
        industry_res[c] = {
            'point': float(point), 'se_NW': float(se), 't_stat': float(t_stat),
            'p_raw': float(p_raw), 'ci95_low': float(ci_low), 'ci95_high': float(ci_high),
            'bonferroni_pass': bool(p_raw < BONFERRONI),
        }
        if c == 'alpha':
            log(f'{s:>8s} {n:>6d} {c:>10s} {point:>+10.5f} {se:>10.5f} {t_stat:>+8.2f} {p_raw:>10.4f} {ci_low:>+10.5f} {ci_high:>+10.5f} {bonf_pass:>10s}')
        else:
            log(f'{"":>8s} {"":>6s} {c:>10s} {point:>+10.4f} {se:>10.4f} {t_stat:>+8.2f} {p_raw:>10.4e} {ci_low:>+10.4f} {ci_high:>+10.4f} {bonf_pass:>10s}')
    industry_res['r_squared'] = float(res.rsquared)
    industry_res['r_squared_adj'] = float(res.rsquared_adj)
    log(f'{"":>8s} {"":>6s} {"R²":>10s} {res.rsquared:>+10.4f} {"adj R²":>10s} {res.rsquared_adj:>+10.4f}')
    log('')
    results[s] = industry_res

# ---- Compare with M3 frame (2021-12 ~ 2024-12) ----
log('='*78)
log('§2. Frame-conditional bias — long-frame vs M3 frame (2021-12 ~ 2024-12)')
log('='*78)

m3_metrics_path = ROOT / 'm3-metrics.json'
with open(m3_metrics_path) as f:
    m3 = json.load(f)

m3_loadings = m3['sector_loadings_full']
log(f'M3 frame β (raw/m3-metrics.json sector_loadings_full):')
log(f'{"industry":>8s} {"β_us10y_M3":>12s} {"β_dxy_M3":>10s} {"β_oil_M3":>10s} {"R²_M3":>8s}')
for s in INDUSTRIES:
    if s in m3_loadings:
        m = m3_loadings[s]
        log(f'{s:>8s} {m["b_us10y"]:>+12.4f} {m["b_dxy"]:>+10.4f} {m["b_oil"]:>+10.4f} {m["r2"]:>8.3f}')

log(f'\nLong-frame β (this run, 2001-07 ~ 2026-05):')
log(f'{"industry":>8s} {"β_us10y_LF":>12s} {"β_dxy_LF":>10s} {"β_oil_LF":>10s} {"R²_LF":>8s}')
for s in INDUSTRIES:
    r = results[s]
    log(f'{s:>8s} {r["beta_us10y"]["point"]:>+12.4f} {r["beta_dxy"]["point"]:>+10.4f} {r["beta_oil"]["point"]:>+10.4f} {r["r_squared"]:>8.3f}')

log(f'\nFrame difference (long-frame − M3, structural break candidate signal):')
log(f'{"industry":>8s} {"Δβ_us10y":>12s} {"Δβ_dxy":>10s} {"Δβ_oil":>10s} {"ΔR²":>8s}')
for s in INDUSTRIES:
    if s in m3_loadings:
        m = m3_loadings[s]
        r = results[s]
        d_u = r["beta_us10y"]["point"] - m["b_us10y"]
        d_d = r["beta_dxy"]["point"] - m["b_dxy"]
        d_o = r["beta_oil"]["point"] - m["b_oil"]
        d_r2 = r["r_squared"] - m["r2"]
        log(f'{s:>8s} {d_u:>+12.4f} {d_d:>+10.4f} {d_o:>+10.4f} {d_r2:>+8.3f}')

# ---- Save ----
out = {
    'frame': {'start': FRAME_START, 'end': FRAME_END, 'spec': '24.8 year, SOXX inception bottleneck'},
    'data_coverage': {s: industry_n[s] for s in INDUSTRIES},
    'newey_west_lag': NW_LAG,
    'bonferroni_alpha': BONFERRONI,
    'n_comparisons': N_COMPARISONS,
    'industries': results,
    'm3_frame_comparison': {s: m3_loadings[s] for s in INDUSTRIES if s in m3_loadings},
}
json_path = ROOT / 'scenarioA_metrics.json'
with open(json_path, 'w') as f:
    json.dump(out, f, indent=2)
log(f'\n[Saved] {json_path}')

with open(OUT_TXT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
log(f'[Saved] {OUT_TXT}')
