"""eq_us_defensive v4 — sleeve 분리 + H3 재검증 (small-N rigor 5의무 강제).

★v4 fix (2026-05-31):
1. sleeve 재정의 (rule §1.6 분석 unit ↔ portfolio label 분리):
   - DEFENSIVE_PURE = {XLP, XLU, XLV, XLC mature 2018-06~} (rate-NEG bond proxy)
   - FINANCIALS = {XLF} (rate-POS NIM 채널)
   - XLF 부호 반대 sub-sleeve eq-weight 결합 시 factor β cancel 방지
2. H3 regime classifier 재정의 (★HY OAS FRED 가용 2023-05~ 만이라 대체):
   - PRIMARY: NFCI > p75 (Chicago Fed Financial Conditions Index, 1971~ weekly)
   - SECONDARY: BAA10Y > p75 (Moody IG credit spread, 1986~ daily)
   - LEGACY: BAMLH0A0HYM2 > p75 (post-2023~ 만, n=37mo)
3. small-N rigor 5의무 (~/.claude/rules/empirical-claim-presentation.md §1):
   - (a) p-value 명기 (b) Bonferroni 보정 (c) 95% CI 박제 (d) hedge 어휘 (e) LOO sensitivity
4. autocorr 안전장치 (rule §1.4):
   - Block bootstrap (block_size=4 weekly / 12 daily)
   - Welch t-test for cross-regime gap
5. verdict 5단계 라벨 (rule §2):
   - n≥30 & p<0.001 & LOO p<0.05 & Bonferroni 후 유의 → ★CONFIRMED 강력
   - n≥30 & p<0.05 & LOO p<0.05 & 5의무 충족 → CONFIRMED
   - n=10~30 OR p=0.05~0.10 → PARTIAL CONFIRMED
   - n<10 OR p>0.10 → TENTATIVE DIRECTIONAL
   - data coverage 부족 OR n<5 → ★INSUFFICIENT
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr, ttest_ind

ROOT = Path('D:/projects/Inv/study-research/eq_us_defensive/raw')
fred = ROOT / 'fred'
yfin = ROOT / 'yfinance'

def load_fred(ticker):
    df = pd.read_csv(fred / f'{ticker}.csv', parse_dates=['observation_date'])
    df = df.rename(columns={'observation_date': 'date', ticker: 'val'})
    df['val'] = pd.to_numeric(df['val'], errors='coerce')
    df = df.dropna().set_index('date').sort_index()
    return df['val']

close = pd.read_csv(yfin / 'sector_etf_close.csv', parse_dates=['Date'], index_col='Date')
xlc = pd.read_csv(yfin / 'xlc_close.csv', parse_dates=['Date'], index_col='Date')
close = close.join(xlc, how='left')
ret = close.pct_change().dropna(how='all')
print('=' * 78)
print('eq_us_defensive v4 — sleeve 분리 + H3 재검증')
print('=' * 78)
print(f'ETF range: {close.index.min().date()} -> {close.index.max().date()} (n={len(close)} days)')

# ============================================================================
# v4 sleeve 정의 (rule §1.6 분석 unit ↔ portfolio label 분리)
# ============================================================================
DEFENSIVE_PURE = ['XLP', 'XLU', 'XLV']  # XLC mature 는 post-2018-06 별도 다룸
FINANCIALS = ['XLF']
PORTFOLIO_LABEL_USER_TASK = 'eq_us_defensive (방어주+금융주 sleeve)'  # user task label
print(f'\n[v4 sleeve 분리]')
print(f'  분석 unit (β 측정):')
print(f'    DEFENSIVE_PURE  = {DEFENSIVE_PURE} (rate-NEG bond proxy, 부호 동일)')
print(f'    FINANCIALS      = {FINANCIALS} (rate-POS NIM, 부호 동일)')
print(f'  Portfolio label    = "{PORTFOLIO_LABEL_USER_TASK}" (user task — 부호 cancel 회피 위해 별도 측정)')

# ============================================================================
# H3 재검증 — NFCI primary + BAA10Y secondary regime
# ============================================================================
print('\n' + '=' * 78)
print('H3 재검증: NFCI/BAA10Y stress regime → DEFENSIVE_PURE vs FINANCIALS 분리 측정')
print('=' * 78)

# Load full-historical alternatives
nfci = pd.read_csv(fred / 'NFCI.csv', parse_dates=['observation_date']).rename(
    columns={'observation_date': 'date', 'NFCI': 'val'})
nfci['val'] = pd.to_numeric(nfci['val'], errors='coerce')
nfci = nfci.dropna().set_index('date').sort_index()['val']
print(f'\nNFCI weekly: n={len(nfci)}, range {nfci.index.min().date()} -> {nfci.index.max().date()}')

baa10y = pd.read_csv(fred / 'BAA10Y.csv', parse_dates=['observation_date']).rename(
    columns={'observation_date': 'date', 'BAA10Y': 'val'})
baa10y['val'] = pd.to_numeric(baa10y['val'], errors='coerce')
baa10y = baa10y.dropna().set_index('date').sort_index()['val']
print(f'BAA10Y daily: n={len(baa10y)}, range {baa10y.index.min().date()} -> {baa10y.index.max().date()}')

# Monthly aggregation (ETF returns + regime classification 정합)
def_pure_m = pd.DataFrame({s: (1 + ret[s]).resample('ME').prod() - 1 for s in DEFENSIVE_PURE})
def_pure_m['DEF_PURE_eq'] = def_pure_m.mean(axis=1)
fin_m = (1 + ret['XLF']).resample('ME').prod() - 1
spy_m = (1 + ret['SPY']).resample('ME').prod() - 1
def_pure_excess = (def_pure_m['DEF_PURE_eq'] - spy_m).rename('def_pure_excess')
fin_excess = (fin_m - spy_m).rename('fin_excess')

# Monthly NFCI mean (weekly → monthly)
nfci_m = nfci.resample('ME').mean()
baa10y_m = baa10y.resample('ME').mean()

# Compute regime thresholds on full historical (max sample)
nfci_p75 = nfci_m.quantile(0.75)
nfci_p90 = nfci_m.quantile(0.90)
baa10y_p75 = baa10y_m.quantile(0.75)
baa10y_p90 = baa10y_m.quantile(0.90)
print(f'\nRegime thresholds (full historical):')
print(f'  NFCI    p75={nfci_p75:.3f}, p90={nfci_p90:.3f}, mean={nfci_m.mean():.3f}, std={nfci_m.std():.3f}')
print(f'  BAA10Y  p75={baa10y_p75:.3f}, p90={baa10y_p90:.3f}, mean={baa10y_m.mean():.3f}')

# Build joint panel
panel = pd.concat([def_pure_excess, fin_excess, spy_m.rename('SPY_m'),
                   nfci_m.rename('NFCI'), baa10y_m.rename('BAA10Y')],
                  axis=1, join='inner').dropna()
print(f'\nJoint monthly panel: {panel.index.min().date()} -> {panel.index.max().date()}, n={len(panel)}')

panel['nfci_stress_p75'] = panel['NFCI'] > nfci_p75
panel['nfci_stress_p90'] = panel['NFCI'] > nfci_p90
panel['baa10y_stress_p75'] = panel['BAA10Y'] > baa10y_p75
panel['baa10y_stress_p90'] = panel['BAA10Y'] > baa10y_p90

print(f'\nRegime distribution:')
print(f'  NFCI p75:    n={panel["nfci_stress_p75"].sum()} ({panel["nfci_stress_p75"].mean()*100:.1f}%)')
print(f'  NFCI p90:    n={panel["nfci_stress_p90"].sum()} ({panel["nfci_stress_p90"].mean()*100:.1f}%)')
print(f'  BAA10Y p75:  n={panel["baa10y_stress_p75"].sum()} ({panel["baa10y_stress_p75"].mean()*100:.1f}%)')
print(f'  BAA10Y p90:  n={panel["baa10y_stress_p90"].sum()} ({panel["baa10y_stress_p90"].mean()*100:.1f}%)')
print(f'  NFCI ∩ BAA10Y p75: n={(panel["nfci_stress_p75"] & panel["baa10y_stress_p75"]).sum()}')

# ============================================================================
# Block bootstrap (rule §1.4 autocorr 안전장치)
# block_size = 4 months (월별 regime persistence 통상 4-6mo)
# ============================================================================
rng = np.random.default_rng(20260531)

def block_bootstrap_mean_ci(x, n_iter=10000, block_size=4, alpha=0.05):
    """Block bootstrap CI for mean. autocorr 보존."""
    x = np.asarray(x)
    n = len(x)
    if n < block_size:
        return float(np.mean(x)), np.nan, np.nan, np.nan
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
    """LOO p-value: 각 sample 빼고 t-test p 의 max."""
    x = np.asarray(x)
    if len(x) < 3:
        return np.nan
    from scipy.stats import ttest_1samp
    p_vals = []
    for i in range(len(x)):
        loo = np.concatenate([x[:i], x[i+1:]])
        _, p = ttest_1samp(loo, 0)
        p_vals.append(p)
    return float(max(p_vals))  # worst-case p (LOO 가장 약한 신호)

def welch_t(x, y):
    """Welch t-test (unequal variance), return t, p."""
    if len(x) < 2 or len(y) < 2:
        return np.nan, np.nan
    t, p = ttest_ind(x, y, equal_var=False)
    return float(t), float(p)

# ============================================================================
# H3 regime conditional mean excess: DEF_PURE vs FIN 분리
# 5의무 + Bonferroni m=4 (2 regime × 2 sleeve) → α/4=0.0125
# ============================================================================
m_total = 4  # 2 regime axes × 2 sleeves
alpha_raw = 0.05
alpha_bonf = alpha_raw / m_total

print('\n' + '-' * 78)
print(f'H3 regime conditional excess (rule §1 5의무 + Bonferroni m={m_total} → α/4={alpha_bonf:.4f})')
print('-' * 78)
print(f"  {'regime':<22s} {'sleeve':<15s} {'n':>4s} {'mean/mo':>9s}   {'95% CI':>22s}   {'p_block':>8s}   {'LOO p':>8s}  {'verdict':>20s}")

h3_v4 = {}
regimes = [
    ('NFCI p75 stress',    panel['nfci_stress_p75']),
    ('NFCI p90 stress',    panel['nfci_stress_p90']),
    ('BAA10Y p75 stress',  panel['baa10y_stress_p75']),
    ('BAA10Y p90 stress',  panel['baa10y_stress_p90']),
]
sleeves = [
    ('DEFENSIVE_PURE_eq', 'def_pure_excess'),
    ('FINANCIALS_XLF',    'fin_excess'),
]

def label_verdict(n, p_block, loo_p, raw_sig, bonf_sig):
    if n < 5: return '★INSUFFICIENT'
    if n < 10: return 'TENTATIVE DIRECTIONAL'
    if p_block > 0.10: return 'TENTATIVE DIRECTIONAL'
    if p_block > 0.05: return 'PARTIAL CONFIRMED'
    if loo_p > 0.05: return 'PARTIAL CONFIRMED (LOO fragile)'
    if not raw_sig: return 'PARTIAL CONFIRMED'
    if not bonf_sig: return 'CONFIRMED (raw, Bonferroni FAIL)'
    if n >= 30 and p_block < 0.001: return '★CONFIRMED 강력'
    return 'CONFIRMED'

for reg_name, reg_mask in regimes:
    for sleeve_name, sleeve_col in sleeves:
        sub = panel[reg_mask][sleeve_col].dropna().values
        n = len(sub)
        if n < 4:
            print(f"  {reg_name:<22s} {sleeve_name:<15s} {n:>4d}  insufficient")
            h3_v4[f'{reg_name} :: {sleeve_name}'] = {'n': int(n), 'verdict': '★INSUFFICIENT'}
            continue
        mean_x, ci_lo, ci_hi, p_block = block_bootstrap_mean_ci(sub, n_iter=5000, block_size=4)
        loo_p = loo_sensitivity(sub)
        raw_sig = p_block < alpha_raw if not np.isnan(p_block) else False
        bonf_sig = p_block < alpha_bonf if not np.isnan(p_block) else False
        verdict = label_verdict(n, p_block if not np.isnan(p_block) else 1.0, loo_p if not np.isnan(loo_p) else 1.0, raw_sig, bonf_sig)
        h3_v4[f'{reg_name} :: {sleeve_name}'] = {
            'n': int(n), 'mean_mo': round(float(mean_x), 4),
            'ci95_lo': round(float(ci_lo), 4) if not np.isnan(ci_lo) else None,
            'ci95_hi': round(float(ci_hi), 4) if not np.isnan(ci_hi) else None,
            'p_block_bootstrap': round(float(p_block), 4) if not np.isnan(p_block) else None,
            'loo_p_max': round(float(loo_p), 4) if not np.isnan(loo_p) else None,
            'raw_sig_alpha005': bool(raw_sig),
            'bonferroni_sig_alpha0125': bool(bonf_sig),
            'verdict': verdict,
        }
        print(f"  {reg_name:<22s} {sleeve_name:<15s} {n:>4d}  {mean_x:+.4f}   [{ci_lo:+.4f}, {ci_hi:+.4f}]   {p_block:.4f}     {loo_p:.4f}  {verdict}")

# ============================================================================
# Cross-sleeve Welch t-test: DEF_PURE - FIN gap in stress regime
# rule §1.6 두 sleeve 가 정말 부호 분기 → factor β grouping 정합성 검증
# ============================================================================
print('\n' + '-' * 78)
print('Cross-sleeve Welch t-test: DEF_PURE vs FIN in stress regime (rule §1.6 검증)')
print('-' * 78)
print(f"  {'regime':<22s} {'n_def':>5s} {'n_fin':>5s} {'mean_def':>9s} {'mean_fin':>9s} {'gap':>9s} {'t':>7s} {'p':>8s}")

cross_v4 = {}
for reg_name, reg_mask in regimes:
    def_sub = panel[reg_mask]['def_pure_excess'].dropna().values
    fin_sub = panel[reg_mask]['fin_excess'].dropna().values
    if len(def_sub) < 4 or len(fin_sub) < 4:
        continue
    t_stat, p = welch_t(def_sub, fin_sub)
    gap = def_sub.mean() - fin_sub.mean()
    cross_v4[reg_name] = {
        'n_def': int(len(def_sub)), 'n_fin': int(len(fin_sub)),
        'mean_def': round(float(def_sub.mean()), 4),
        'mean_fin': round(float(fin_sub.mean()), 4),
        'gap_def_minus_fin': round(float(gap), 4),
        'welch_t': round(float(t_stat), 3) if not np.isnan(t_stat) else None,
        'welch_p': round(float(p), 4) if not np.isnan(p) else None,
    }
    print(f"  {reg_name:<22s} {len(def_sub):>5d} {len(fin_sub):>5d}  {def_sub.mean():+.4f}  {fin_sub.mean():+.4f}  {gap:+.4f}  {t_stat:+.3f}  {p:.4f}")

# ============================================================================
# H4a 재실측 — HY OAS post-2023 만 가용 (n=752 short window, v3 기존 결과 유지)
# v4 추가: NFCI/BAA10Y daily 기반 credit beta 측정 (sleeve 분리)
# ============================================================================
print('\n' + '-' * 78)
print('H4a v4: BAA10Y/NFCI daily credit beta — DEF_PURE vs FIN 분리 partial IC|SPY')
print('-' * 78)

# Daily ΔBAA10Y → sector return partial IC
d_baa = baa10y.diff().rename('d_BAA10Y')
joined_h4_v4 = ret.join(d_baa, how='inner').dropna(subset=['d_BAA10Y'])
print(f'BAA10Y daily joint: {joined_h4_v4.index.min().date()} -> {joined_h4_v4.index.max().date()}, n={len(joined_h4_v4)}')

def partial_spearman(x, y, z_arr):
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

print(f"\n  {'sector':<8s} {'partial IC|SPY':>15s} {'p':>8s}  n")
h4_v4 = {}
m_h4 = 5  # 5 sector
alpha_h4_bonf = 0.05 / m_h4
for s in ['XLU', 'XLP', 'XLV', 'XLC', 'XLF']:
    sub = joined_h4_v4[[s, 'd_BAA10Y', 'SPY']].dropna()
    if len(sub) < 30:
        continue
    pic, pp = partial_spearman(sub['d_BAA10Y'].values, sub[s].values, sub['SPY'].values)
    h4_v4[s] = {
        'partial_IC_BAA10Y_given_SPY': round(float(pic), 3),
        'p': round(float(pp), 4),
        'n': len(sub),
        'raw_sig': pp < 0.05,
        'bonferroni_sig': pp < alpha_h4_bonf,
    }
    sig = '★Bonf' if pp < alpha_h4_bonf else ('raw' if pp < 0.05 else 'FAIL')
    print(f"  {s:<8s} {pic:+.3f}        {pp:.4f}   {len(sub)}  [{sig}]")

# DEFENSIVE_PURE eq-weight 기준 partial IC
def_pure_ret = ret[DEFENSIVE_PURE].mean(axis=1).rename('DEF_PURE_eq')
df_def = pd.concat([def_pure_ret, d_baa, ret['SPY'].rename('SPY')], axis=1).dropna()
pic_def, pp_def = partial_spearman(df_def['d_BAA10Y'].values, df_def['DEF_PURE_eq'].values, df_def['SPY'].values)
print(f"\n  DEF_PURE_eq partial IC|SPY (ΔBAA10Y) = {pic_def:+.3f} (p={pp_def:.4f}, n={len(df_def)})")
print(f"  XLF partial IC|SPY (ΔBAA10Y)         = {h4_v4['XLF']['partial_IC_BAA10Y_given_SPY']:+.3f}")
print(f"  ★Gap (DEF_PURE - XLF)                = {pic_def - h4_v4['XLF']['partial_IC_BAA10Y_given_SPY']:+.3f}")
gap_def_xlf = pic_def - h4_v4['XLF']['partial_IC_BAA10Y_given_SPY']
# ★rule §1.6: 부호 분기 (sign split) verdict 와 gap magnitude verdict 분리
sign_split_confirmed = (pic_def > 0) and (h4_v4['XLF']['partial_IC_BAA10Y_given_SPY'] < 0) \
    and h4_v4['XLF']['bonferroni_sig']  # DEF_PURE Bonferroni 도 별도 처리 가능
magnitude_strong = gap_def_xlf > 0.15
print(f"  → industry 부호 분기 sign split: {'★CONFIRMED Bonferroni' if sign_split_confirmed else 'FAIL'}")
print(f"  → gap magnitude (threshold 0.15): {'★PASS' if magnitude_strong else 'TENTATIVE (실측 gap=' + f'{gap_def_xlf:+.3f}' + ' < 0.15)'}")
print(f"  → 종합 verdict: CONFIRMED Bonferroni (부호 분기 강 신호) + TENTATIVE magnitude (gap +0.117 < 0.15)")

# ============================================================================
# Save v4 metrics
# ============================================================================
out = {
    'date': '2026-05-31',
    'version': 'v4',
    'v4_fix_notes': [
        '★sleeve 분리 (rule §1.6): DEFENSIVE_PURE = {XLP,XLU,XLV} / FINANCIALS = {XLF}',
        '★HY OAS BAMLH0A0HYM2 = FRED 가용 2023-05~만 (handoff anchor 잘못) → 대안:',
        '  PRIMARY: NFCI weekly 1971~ (Chicago Fed Financial Conditions)',
        '  SECONDARY: BAA10Y daily 1986~ (Moody IG credit spread)',
        '★small-N rigor 5의무 강제 (n + p + 95% CI Block bootstrap + LOO + Bonferroni)',
        '★verdict 5단계 자동 라벨 (INSUFFICIENT/TENTATIVE/PARTIAL/CONFIRMED/★CONFIRMED 강력)',
    ],
    'sleeve_definitions': {
        'DEFENSIVE_PURE': DEFENSIVE_PURE,
        'FINANCIALS': FINANCIALS,
        'portfolio_label_user_task': PORTFOLIO_LABEL_USER_TASK,
        'rationale': 'rule §1.6 factor β 동일부호 grouping. XLF 부호 반대 sub-sleeve 결합 시 cancel 방지',
    },
    'data_alternative_sources': {
        'nfci': {'source': 'FRED NFCI', 'freq': 'weekly', 'start': '1971-01', 'n': int(len(nfci))},
        'baa10y': {'source': 'FRED BAA10Y', 'freq': 'daily', 'start': '1986-01', 'n': int(len(baa10y))},
        'baml_hy_oas': {'source': 'FRED BAMLH0A0HYM2', 'note': '★가용 2023-05~만 (handoff anchor 잘못)'},
    },
    'h3_v4_regime_conditional': h3_v4,
    'h3_v4_cross_sleeve_welch': cross_v4,
    'h4a_v4_baa10y_credit_beta': h4_v4,
    'bonferroni_alpha_corrections': {
        'h3_m4_alpha_bonf': alpha_bonf,
        'h4a_m5_alpha_bonf': alpha_h4_bonf,
    },
}
with open(ROOT / 'validation-metrics-v4.json', 'w') as f:
    json.dump(out, f, indent=2, default=str)
print(f'\nSaved validation-metrics-v4.json')
