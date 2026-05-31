"""eq_us_defensive v4 walk-forward — main 보강 (1) D축: NFCI/BAA10Y p75 walk-forward backtest.

★main 12축 audit 보강 (1) D축: NFCI/BAA10Y p75 walk-forward (10Y rolling) backtest
→ H3 structural → validated 승격 가능성 검토.

이전 v4 (run_validation_v4.py): full-historical p75 = lookahead 잠재.
본 walk-forward: 매 month t threshold = 직전 10Y (120 mo) 의 p75 quantile (★lookahead 차단).

방법:
1. 매 month t 의 threshold_t = quantile_p75(history[t-120 : t])
2. regime_t = NFCI_t > threshold_t (또는 BAA10Y_t > threshold_t)
3. 동일 sleeve excess + Block bootstrap + Welch + Bonferroni + LOO 적용
4. v4 (lookahead) vs walk-forward 결과 비교 → tier 승격 판정
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import ttest_ind

ROOT = Path('D:/projects/Inv/study-research/eq_us_defensive/raw')
fred = ROOT / 'fred'
yfin = ROOT / 'yfinance'

def load_fred_to_series(ticker, col_name=None):
    col_name = col_name or ticker
    df = pd.read_csv(fred / f'{ticker}.csv', parse_dates=['observation_date']).rename(
        columns={'observation_date': 'date', col_name: 'val'})
    df['val'] = pd.to_numeric(df['val'], errors='coerce')
    return df.dropna().set_index('date').sort_index()['val']

print('=' * 78)
print('v4 walk-forward backtest — H3 regime threshold 10Y rolling (lookahead 차단)')
print('=' * 78)

# Load ETF
close = pd.read_csv(yfin / 'sector_etf_close.csv', parse_dates=['Date'], index_col='Date')
xlc = pd.read_csv(yfin / 'xlc_close.csv', parse_dates=['Date'], index_col='Date')
close = close.join(xlc, how='left')
ret = close.pct_change().dropna(how='all')

DEFENSIVE_PURE = ['XLP', 'XLU', 'XLV']

def_pure_m = pd.DataFrame({s: (1 + ret[s]).resample('ME').prod() - 1 for s in DEFENSIVE_PURE})
def_pure_m['DEF_PURE_eq'] = def_pure_m.mean(axis=1)
fin_m = (1 + ret['XLF']).resample('ME').prod() - 1
spy_m = (1 + ret['SPY']).resample('ME').prod() - 1
def_pure_excess = (def_pure_m['DEF_PURE_eq'] - spy_m).rename('def_pure_excess')
fin_excess = (fin_m - spy_m).rename('fin_excess')

# Load NFCI + BAA10Y monthly
nfci = load_fred_to_series('NFCI').resample('ME').mean()
baa10y = load_fred_to_series('BAA10Y').resample('ME').mean()

print(f'NFCI monthly: {nfci.index.min().date()} -> {nfci.index.max().date()}, n={len(nfci)}')
print(f'BAA10Y monthly: {baa10y.index.min().date()} -> {baa10y.index.max().date()}, n={len(baa10y)}')

# Build joint panel
panel = pd.concat([def_pure_excess, fin_excess, nfci.rename('NFCI'), baa10y.rename('BAA10Y')],
                  axis=1, join='inner').dropna()
print(f'Joint panel: {panel.index.min().date()} -> {panel.index.max().date()}, n={len(panel)}')

# ============================================================================
# Walk-forward regime: threshold_t = p75 of history[t-120 : t]
# 본 작업 = lookahead 차단 → 첫 120mo 데이터는 OutOfSample (regime 분류 불가)
# ============================================================================
ROLLING_WINDOW = 120  # 10 years

print(f'\nWalk-forward threshold (rolling window {ROLLING_WINDOW} months):')
panel['nfci_p75_wf'] = panel['NFCI'].rolling(ROLLING_WINDOW).quantile(0.75).shift(1)  # t-1 까지 history
panel['baa10y_p75_wf'] = panel['BAA10Y'].rolling(ROLLING_WINDOW).quantile(0.75).shift(1)
panel['nfci_stress_wf'] = panel['NFCI'] > panel['nfci_p75_wf']
panel['baa10y_stress_wf'] = panel['BAA10Y'] > panel['baa10y_p75_wf']

# Drop OOS (첫 120mo)
panel_in = panel.dropna(subset=['nfci_p75_wf', 'baa10y_p75_wf'])
print(f'In-sample (walk-forward): {panel_in.index.min().date()} -> {panel_in.index.max().date()}, n={len(panel_in)}')

print(f'\nRegime distribution (walk-forward):')
print(f'  NFCI p75 stress (wf):    n={panel_in["nfci_stress_wf"].sum()} ({panel_in["nfci_stress_wf"].mean()*100:.1f}%)')
print(f'  BAA10Y p75 stress (wf):  n={panel_in["baa10y_stress_wf"].sum()} ({panel_in["baa10y_stress_wf"].mean()*100:.1f}%)')
print(f'  NFCI ∩ BAA10Y p75 (wf):  n={(panel_in["nfci_stress_wf"] & panel_in["baa10y_stress_wf"]).sum()}')

# ============================================================================
# Block bootstrap + LOO + Welch (동일 v4 method)
# ============================================================================
rng = np.random.default_rng(20260531)

def block_bootstrap_mean_ci(x, n_iter=5000, block_size=4, alpha=0.05):
    x = np.asarray(x)
    n = len(x)
    if n < block_size:
        return float(np.mean(x)) if n > 0 else np.nan, np.nan, np.nan, np.nan
    n_blocks = n // block_size + 1
    means = []
    for _ in range(n_iter):
        starts = rng.integers(0, n - block_size + 1, size=n_blocks)
        sample = np.concatenate([x[s:s+block_size] for s in starts])[:n]
        means.append(sample.mean())
    means = np.array(means)
    lo, hi = np.percentile(means, [100*alpha/2, 100*(1-alpha/2)])
    p_two_sided = 2 * min((means > 0).mean(), (means < 0).mean())
    return float(np.mean(x)), float(lo), float(hi), float(p_two_sided)

def loo_sensitivity(x):
    x = np.asarray(x)
    if len(x) < 3:
        return np.nan
    from scipy.stats import ttest_1samp
    p_vals = []
    for i in range(len(x)):
        loo = np.concatenate([x[:i], x[i+1:]])
        _, p = ttest_1samp(loo, 0)
        p_vals.append(p)
    return float(max(p_vals))

def welch_t(x, y):
    if len(x) < 2 or len(y) < 2:
        return np.nan, np.nan
    t, p = ttest_ind(x, y, equal_var=False)
    return float(t), float(p)

# ============================================================================
# H3 walk-forward conditional excess
# m=4 (2 regime × 2 sleeve) Bonferroni α/4=0.0125
# ============================================================================
m_total = 4
alpha_bonf = 0.05 / m_total
print(f'\n--- H3 walk-forward conditional excess (Bonferroni α/4={alpha_bonf:.4f}) ---')
print(f"  {'regime':<22s} {'sleeve':<18s} {'n':>4s} {'mean':>9s}   {'95% CI':>22s}   {'p_block':>8s}   {'LOO p':>8s}")

h3_wf = {}
regimes_wf = [
    ('NFCI p75 wf', panel_in['nfci_stress_wf']),
    ('BAA10Y p75 wf', panel_in['baa10y_stress_wf']),
]
sleeves = [
    ('DEFENSIVE_PURE_eq', 'def_pure_excess'),
    ('FINANCIALS_XLF',    'fin_excess'),
]

for reg_name, reg_mask in regimes_wf:
    for sleeve_name, sleeve_col in sleeves:
        sub = panel_in[reg_mask][sleeve_col].dropna().values
        n = len(sub)
        if n < 4:
            print(f"  {reg_name:<22s} {sleeve_name:<18s} {n:>4d}  insufficient")
            continue
        mean_x, ci_lo, ci_hi, p_block = block_bootstrap_mean_ci(sub, n_iter=5000, block_size=4)
        loo_p = loo_sensitivity(sub)
        h3_wf[f'{reg_name} :: {sleeve_name}'] = {
            'n': int(n), 'mean_mo': round(float(mean_x), 4),
            'ci95_lo': round(float(ci_lo), 4) if not np.isnan(ci_lo) else None,
            'ci95_hi': round(float(ci_hi), 4) if not np.isnan(ci_hi) else None,
            'p_block': round(float(p_block), 4) if not np.isnan(p_block) else None,
            'loo_p_max': round(float(loo_p), 4) if not np.isnan(loo_p) else None,
            'raw_sig': p_block < 0.05 if not np.isnan(p_block) else False,
            'bonferroni_sig': p_block < alpha_bonf if not np.isnan(p_block) else False,
        }
        print(f"  {reg_name:<22s} {sleeve_name:<18s} {n:>4d}  {mean_x:+.4f}   [{ci_lo:+.4f}, {ci_hi:+.4f}]   {p_block:.4f}     {loo_p:.4f}")

# Cross-sleeve Welch walk-forward
print(f'\n--- Cross-sleeve Welch (walk-forward): DEF_PURE vs FIN ---')
print(f"  {'regime':<22s} {'n_def':>5s} {'n_fin':>5s} {'mean_def':>9s} {'mean_fin':>9s} {'gap':>9s} {'t':>7s} {'p':>8s}")
cross_wf = {}
for reg_name, reg_mask in regimes_wf:
    def_sub = panel_in[reg_mask]['def_pure_excess'].dropna().values
    fin_sub = panel_in[reg_mask]['fin_excess'].dropna().values
    if len(def_sub) < 4 or len(fin_sub) < 4:
        continue
    t_stat, p = welch_t(def_sub, fin_sub)
    gap = def_sub.mean() - fin_sub.mean()
    cross_wf[reg_name] = {
        'n_def': int(len(def_sub)), 'n_fin': int(len(fin_sub)),
        'mean_def': round(float(def_sub.mean()), 4),
        'mean_fin': round(float(fin_sub.mean()), 4),
        'gap': round(float(gap), 4),
        'welch_t': round(float(t_stat), 3) if not np.isnan(t_stat) else None,
        'welch_p': round(float(p), 4) if not np.isnan(p) else None,
    }
    print(f"  {reg_name:<22s} {len(def_sub):>5d} {len(fin_sub):>5d}  {def_sub.mean():+.4f}  {fin_sub.mean():+.4f}  {gap:+.4f}  {t_stat:+.3f}  {p:.4f}")

# ============================================================================
# v4 (lookahead) vs walk-forward 비교 → tier 승격 판정
# ============================================================================
print('\n--- v4 (lookahead) vs walk-forward 비교 ---')
print('  walk-forward 가 v4 (lookahead) 와 방향 일관 유지 → structural prior 안정성 검증')
print('  walk-forward gap > 0 (4/2 wf regime) 유지 시 structural validated 승격 가능성')

# tier 승격 판정 logic
wf_pass_direction = all(
    cross_wf.get(r, {}).get('gap', -1) > 0 for r in [reg_name for reg_name, _ in regimes_wf]
)
wf_any_bonf = any(
    cross_wf.get(r, {}).get('welch_p', 1) < alpha_bonf
    for r in [reg_name for reg_name, _ in regimes_wf]
)
print(f'\n  walk-forward sign split 4/4 direction 일관: {wf_pass_direction}')
print(f'  walk-forward Welch Bonferroni 1+ PASS: {wf_any_bonf}')
if wf_pass_direction and wf_any_bonf:
    print('  → ★structural prior VALIDATED 승격 가능 (방향 + 강도 모두 통과)')
elif wf_pass_direction:
    print('  → structural prior TENTATIVE 유지 (방향 일관 단 통계 비유의 — magnitude 약)')
else:
    print('  → structural prior 부분 격하 (방향 일관성 missing)')

# Save
out = {
    'date': '2026-05-31',
    'version': 'v4-walkforward',
    'method': {
        'rolling_window_months': ROLLING_WINDOW,
        'threshold': 'quantile p75 of history[t-120 : t]',
        'lookahead_block': True,
    },
    'walk_forward_regime_distribution': {
        'nfci_p75_wf': {'n': int(panel_in['nfci_stress_wf'].sum()), 'pct': float(panel_in['nfci_stress_wf'].mean())},
        'baa10y_p75_wf': {'n': int(panel_in['baa10y_stress_wf'].sum()), 'pct': float(panel_in['baa10y_stress_wf'].mean())},
        'intersection': int((panel_in['nfci_stress_wf'] & panel_in['baa10y_stress_wf']).sum()),
    },
    'h3_wf_regime_conditional': h3_wf,
    'h3_wf_cross_sleeve_welch': cross_wf,
    'in_sample_period': {
        'start': str(panel_in.index.min().date()),
        'end': str(panel_in.index.max().date()),
        'n': len(panel_in),
    },
    'tier_promotion_verdict': {
        'walk_forward_direction_consistent': wf_pass_direction,
        'walk_forward_any_bonferroni_pass': wf_any_bonf,
        'tier_recommendation': (
            'structural VALIDATED' if (wf_pass_direction and wf_any_bonf)
            else 'structural TENTATIVE (방향 유지, magnitude 약)' if wf_pass_direction
            else 'structural 부분 격하 (방향 missing)'
        ),
    },
}
with open(ROOT / 'validation-metrics-v4-walkforward.json', 'w') as f:
    json.dump(out, f, indent=2, default=str)
print(f'\nSaved validation-metrics-v4-walkforward.json')
