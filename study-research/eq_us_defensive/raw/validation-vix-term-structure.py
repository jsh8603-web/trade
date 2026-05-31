"""eq_us_defensive — VIX term structure (H-VIXTS) 검증.

M6 자문 "방어주 누락 critical 지표" = VIX term structure.

★spec (가설):
  term ratio = VIX3M / VIX (또는 VIX / VIX9D).
  backwardation (VIX > VIX3M, ratio<1) = 급성 스트레스 → 방어주 상대강세.
  contango (ratio>1) = 정상.
  부호 prior: backwardation 심화(ratio↓) → 방어주(XLP/XLU/XLV) − SPY 상대수익 = 양.
              즉 corr(term_ratio, def_excess) 부호 = 음 (ratio↓ 시 def_excess↑).

★측정 (12축 audit-ready, rule empirical-claim-presentation §1 5의무 + AUDIT-GUIDE 12축):
  (a) term ratio level + own-history z-score. ADF 사전검정 (§1.7-A 단위근).
  (b) 방어주 sleeve − SPY 일별 상대 log-return 과의
      - 동시 (contemporaneous) Rank-IC + Newey-West HAC t
      - 예측 (forward 5d / 20d) Rank-IC + NW HAC t  ← eq_intl lead 전부 비유의 패턴 주의, 분리 측정
  (c) regime split (backwardation vs contango)에서 방어주 상대성과 차이 (Welch).
  (d) ★L축 중복 점검: VIX term ratio 가 기존 H1 real-rate / H4a credit(BAA10Y) 와 겹치는지 corr.

★데이터 (★합성 금지, PIT 종가, daily):
  - VIX (30d):  FRED VIXCLS.csv (1990~)
  - VIX3M (3m): yfinance vix3m_close.csv (2007-12~) ← 1차 ratio, binding window
  - VIX9D (9d): yfinance vix9d_close.csv (2011-01~) ← 보조 ratio
  - ETF: XLP/XLU/XLV (DEFENSIVE_PURE) + XLF (FINANCIALS) + SPY (벤치) — sector_etf_close.csv

★sleeve (rule §1.6 분석 unit ↔ portfolio label):
  DEFENSIVE_PURE = {XLP, XLU, XLV} (eq-weight, factor β 동일부호 grouping)
  FINANCIALS = {XLF}
  Portfolio label (user task) = "미국 방어주 + 금융주" sleeve

★재현: PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python validation-vix-term-structure.py
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr, ttest_ind
from statsmodels.tsa.stattools import adfuller

ROOT = Path('D:/projects/Inv/study-research/eq_us_defensive/raw')
fred = ROOT / 'fred'
yfin = ROOT / 'yfinance'

SEED = 20260601
rng = np.random.default_rng(SEED)

DEFENSIVE_PURE = ['XLP', 'XLU', 'XLV']
FINANCIALS = ['XLF']
PORTFOLIO_LABEL = '미국 방어주 + 금융주 sleeve'

print('=' * 80)
print('eq_us_defensive — VIX term structure (H-VIXTS) 검증')
print('=' * 80)

# ============================================================================
# Load (★실데이터, 합성 금지 — fetch 실패 시 raise)
# ============================================================================
def load_fred(name, col):
    df = pd.read_csv(fred / f'{name}.csv', parse_dates=['observation_date'])
    df = df.rename(columns={'observation_date': 'date', col: 'val'})
    df['val'] = pd.to_numeric(df['val'], errors='coerce')
    return df.dropna().set_index('date').sort_index()['val']

def load_yf(fname, col):
    df = pd.read_csv(yfin / fname, parse_dates=['Date'], index_col='Date')
    s = pd.to_numeric(df[col], errors='coerce')
    return s.dropna().sort_index()

vix = load_fred('VIXCLS', 'VIXCLS')          # 30d VIX
vix3m = load_yf('vix3m_close.csv', 'VIX3M')  # 3m VIX
vix9d = load_yf('vix9d_close.csv', 'VIX9D')  # 9d VIX
print(f'VIX (30d, FRED VIXCLS):  n={len(vix)},   {vix.index.min().date()} -> {vix.index.max().date()}')
print(f'VIX3M (yfinance):        n={len(vix3m)}, {vix3m.index.min().date()} -> {vix3m.index.max().date()}')
print(f'VIX9D (yfinance):        n={len(vix9d)}, {vix9d.index.min().date()} -> {vix9d.index.max().date()}')

# ★합성 지문 검사 (AUDIT-GUIDE §0): 알려진 이벤트 실재 확인
print('\n[합성 지문 검사 §0] 알려진 위기 이벤트 VIX 실재 확인:')
for ev, dt in [('COVID 2020-03', '2020-03-16'), ('2008 GFC', '2008-10-24'), ('2018 Volmageddon', '2018-02-05')]:
    try:
        v = vix.loc[dt]
        print(f'  {ev:<20s} VIX={v:.2f}')
    except KeyError:
        print(f'  {ev:<20s} (날짜 부재)')

close = pd.read_csv(yfin / 'sector_etf_close.csv', parse_dates=['Date'], index_col='Date')
ret = np.log(close).diff()  # daily log-return (rule §1.7-B: log-return for prices)
print(f'\nETF log-return: {close.index.min().date()} -> {close.index.max().date()}, n={len(close)} days')

# ============================================================================
# Term structure ratio 구성
#  primary:   VIX3M / VIX  (contango>1 정상 / backwardation<1 스트레스)
#  secondary: VIX / VIX9D  (>1 = near-term 스트레스. 같은 방향 정보)
# ============================================================================
ts = pd.DataFrame({'VIX': vix, 'VIX3M': vix3m, 'VIX9D': vix9d}).dropna(subset=['VIX'])
ts['ratio_3m_vix'] = ts['VIX3M'] / ts['VIX']          # primary; <1 = backwardation
ts['ratio_vix_9d'] = ts['VIX'] / ts['VIX9D']          # secondary; >1 = near stress
ts_primary = ts.dropna(subset=['ratio_3m_vix'])
print(f'\nTerm ratio VIX3M/VIX: n={len(ts_primary)}, {ts_primary.index.min().date()} -> {ts_primary.index.max().date()}')
print(f'  ratio mean={ts_primary["ratio_3m_vix"].mean():.4f}, std={ts_primary["ratio_3m_vix"].std():.4f}, '
      f'min={ts_primary["ratio_3m_vix"].min():.4f}, max={ts_primary["ratio_3m_vix"].max():.4f}')
backw = (ts_primary['ratio_3m_vix'] < 1.0)
print(f'  backwardation (ratio<1) days: n={backw.sum()} ({backw.mean()*100:.1f}%)')

# ============================================================================
# §1.7-A ADF 단위근 사전검정 (level vs z vs diff 결정)
# ============================================================================
print('\n' + '-' * 80)
print('§1.7-A ADF 단위근 사전검정 (level I(0)? 아니면 z/diff)')
print('-' * 80)
adf_results = {}
for name, s in [('ratio_3m_vix_level', ts_primary['ratio_3m_vix']),
                ('ratio_vix_9d_level', ts['ratio_vix_9d'].dropna()),
                ('VIX_level', ts_primary['VIX'])]:
    stat, p, *_ = adfuller(s.values, regression='c', autolag='AIC')
    cls = 'I(0) stationary' if p < 0.05 else 'I(1) 의심'
    adf_results[name] = {'adf_stat': round(float(stat), 4), 'p_adf': round(float(p), 5),
                         'n': int(len(s)), 'class': cls}
    print(f'  {name:<22s} ADF={stat:+.3f}  p={p:.5f}  n={len(s)}  -> {cls}')

# own-history rolling z-score (rule §1.7-B index z; 252d ~ 1Y window)
ZWIN = 252
ts_primary = ts_primary.copy()
ts_primary['ratio_z'] = ((ts_primary['ratio_3m_vix'] - ts_primary['ratio_3m_vix'].rolling(ZWIN).mean())
                         / ts_primary['ratio_3m_vix'].rolling(ZWIN).std())
stat_z, p_z, *_ = adfuller(ts_primary['ratio_z'].dropna().values, regression='c', autolag='AIC')
adf_results['ratio_z_252d'] = {'adf_stat': round(float(stat_z), 4), 'p_adf': round(float(p_z), 5),
                               'n': int(ts_primary['ratio_z'].notna().sum()),
                               'class': 'I(0) stationary' if p_z < 0.05 else 'I(1) 의심'}
print(f'  {"ratio_z_252d":<22s} ADF={stat_z:+.3f}  p={p_z:.5f}  n={ts_primary["ratio_z"].notna().sum()}  '
      f'-> {adf_results["ratio_z_252d"]["class"]}')

# ============================================================================
# sleeve excess log-return (daily)
# ============================================================================
def_pure_ret = ret[DEFENSIVE_PURE].mean(axis=1).rename('DEF_PURE')   # eq-weight log-ret
fin_ret = ret['XLF'].rename('FIN')
spy_ret = ret['SPY'].rename('SPY')
def_excess = (def_pure_ret - spy_ret).rename('def_excess')          # 방어주 − SPY 상대수익
fin_excess = (fin_ret - spy_ret).rename('fin_excess')

# ============================================================================
# Newey-West HAC t for Spearman-rank IC via rank-regression
#  (rank IC 의 SE 를 중첩 윈도우 autocorr 보정 — AUDIT-GUIDE L축 / rule §1.4)
#  방법: rank(x), rank(y) → OLS slope, HAC SE (lag = forward horizon + 5)
# ============================================================================
import statsmodels.api as sm

def rank_ic_nw(x, y, hac_lag):
    """Spearman rank-IC + Newey-West HAC t (rank-OLS slope 기반)."""
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    n = len(x)
    if n < 30:
        return np.nan, np.nan, np.nan, n
    rx = pd.Series(x).rank().values
    ry = pd.Series(y).rank().values
    rx = (rx - rx.mean()) / rx.std()
    ry = (ry - ry.mean()) / ry.std()
    ic, _ = spearmanr(x, y)
    X = sm.add_constant(rx)
    model = sm.OLS(ry, X).fit(cov_type='HAC', cov_kwds={'maxlags': hac_lag})
    t = model.tvalues[1]
    p = model.pvalues[1]
    return float(ic), float(t), float(p), n

# ============================================================================
# (b) 동시 + 예측(forward 5d/20d) Rank-IC  ★동시 vs 예측 분리 측정
#   signal = ratio_z (낮을수록 backwardation/스트레스)
#   prior: backwardation(z↓) → def_excess↑ ⇒ corr(ratio_z, def_excess) = 음
# ============================================================================
print('\n' + '-' * 80)
print('(b) term ratio_z → sleeve excess: 동시(contemp) + 예측(fwd 5d/20d) Rank-IC + NW HAC t')
print('   prior: backwardation(ratio_z↓) → 방어주 outperform ⇒ corr(ratio_z, def_excess) 음')
print('-' * 80)

panel_d = pd.concat([ts_primary['ratio_z'], ts_primary['ratio_3m_vix'].rename('ratio'),
                     def_excess, fin_excess], axis=1, join='inner').dropna(subset=['ratio_z'])

# multiple comparison: signal(ratio_z) × {def,fin} × {contemp, fwd5, fwd20} = 6 비교
m_total = 6
alpha_bonf = 0.05 / m_total
print(f'  ★다중비교 m={m_total} (2 sleeve × 3 horizon), Bonferroni α/{m_total}={alpha_bonf:.4f}\n')
print(f"  {'signal':<10s} {'sleeve':<10s} {'horizon':<10s} {'RankIC':>8s} {'NW t':>8s} {'p':>9s}   {'n':>6s}  {'sig':>10s}")

ic_results = {}
horizons = [('contemp', 0, 5), ('fwd_5d', 5, 10), ('fwd_20d', 20, 25)]
for sleeve_name, sleeve_col in [('DEF_PURE', 'def_excess'), ('FIN', 'fin_excess')]:
    for hname, h, hac_lag in horizons:
        if h == 0:
            y = panel_d[sleeve_col].values
        else:
            # forward cumulative excess log-return over next h days (예측)
            yf_ = panel_d[sleeve_col].shift(-1).rolling(h).sum().shift(-(h-1))
            y = yf_.values
        x = panel_d['ratio_z'].values
        ic, t, p, n = rank_ic_nw(x, y, hac_lag)
        raw_sig = (not np.isnan(p)) and p < 0.05
        bonf_sig = (not np.isnan(p)) and p < alpha_bonf
        sig = '★Bonf' if bonf_sig else ('raw' if raw_sig else 'ns')
        ic_results[f'ratio_z::{sleeve_name}::{hname}'] = {
            'rank_ic': round(ic, 4) if not np.isnan(ic) else None,
            'nw_hac_t': round(t, 3) if not np.isnan(t) else None,
            'p': round(p, 5) if not np.isnan(p) else None,
            'n': int(n), 'raw_sig': bool(raw_sig), 'bonferroni_sig': bool(bonf_sig),
        }
        print(f"  {'ratio_z':<10s} {sleeve_name:<10s} {hname:<10s} {ic:+.4f} {t:+8.3f} {p:9.5f}   {n:>6d}  {sig:>10s}")

# ============================================================================
# (c) regime split: backwardation vs contango — 방어주 상대성과 차이 (Welch)
#   regime = ratio_3m_vix < 1 (backwardation) vs >= 1 (contango)
#   ★contemp (당일) 측정 — mechanical co-movement 인지 분리 보고
# ============================================================================
print('\n' + '-' * 80)
print('(c) regime split: backwardation(ratio<1) vs contango(ratio>=1) — def_excess 차이 (Welch)')
print('-' * 80)
reg = pd.concat([ts_primary['ratio_3m_vix'].rename('ratio'), def_excess, fin_excess],
                axis=1, join='inner').dropna()
bw_mask = reg['ratio'] < 1.0
n_bw = int(bw_mask.sum())
n_co = int((~bw_mask).sum())
print(f'  backwardation days n={n_bw} / contango days n={n_co}')

def block_bootstrap_mean_ci(x, n_iter=10000, block_size=10, alpha=0.05):
    """Block bootstrap CI for mean (daily autocorr 보존, block=10d ~ 2주)."""
    x = np.asarray(x)
    n = len(x)
    if n < block_size:
        return float(np.mean(x)) if n else np.nan, np.nan, np.nan, np.nan
    n_blocks = n // block_size + 1
    means = np.empty(n_iter)
    for i in range(n_iter):
        starts = rng.integers(0, n - block_size + 1, size=n_blocks)
        sample = np.concatenate([x[s:s+block_size] for s in starts])[:n]
        means[i] = sample.mean()
    lo, hi = np.percentile(means, [100*alpha/2, 100*(1-alpha/2)])
    p_two = 2 * min((means > 0).mean(), (means < 0).mean())
    return float(np.mean(x)), float(lo), float(hi), float(p_two)

regime_results = {}
for sleeve_name, col in [('DEF_PURE', 'def_excess'), ('FIN', 'fin_excess')]:
    bw = reg.loc[bw_mask, col].dropna().values
    co = reg.loc[~bw_mask, col].dropna().values
    mbw, lobw, hibw, pbw = block_bootstrap_mean_ci(bw, n_iter=5000)
    mco, loco, hico, pco = block_bootstrap_mean_ci(co, n_iter=5000)
    t, p = ttest_ind(bw, co, equal_var=False)
    regime_results[sleeve_name] = {
        'backwardation': {'n': len(bw), 'mean_daily': round(mbw, 6),
                          'ci95': [round(lobw, 6), round(hibw, 6)], 'p_block': round(pbw, 4)},
        'contango': {'n': len(co), 'mean_daily': round(mco, 6),
                     'ci95': [round(loco, 6), round(hico, 6)], 'p_block': round(pco, 4)},
        'welch_t': round(float(t), 3), 'welch_p': round(float(p), 5),
        'gap_bw_minus_co_daily': round(mbw - mco, 6),
    }
    print(f'\n  {sleeve_name}:')
    print(f'    backwardation mean={mbw:+.6f}/d [{lobw:+.6f},{hibw:+.6f}] p_block={pbw:.4f} n={len(bw)}')
    print(f'    contango      mean={mco:+.6f}/d [{loco:+.6f},{hico:+.6f}] p_block={pco:.4f} n={len(co)}')
    print(f'    Welch gap (bw-co) = {mbw-mco:+.6f}/d  t={t:+.3f}  p={p:.5f}')

# ============================================================================
# (d) ★L축 중복/공통인자 점검: VIX term ratio vs 기존 H1 real-rate / H4a credit
#   ΔDFII10 (H1 real rate) / ΔBAA10Y (H4a credit) 와 ratio_z 의 corr
# ============================================================================
print('\n' + '-' * 80)
print('(d) ★L축 중복 점검: VIX term ratio_z vs real-rate(ΔDFII10) / credit(ΔBAA10Y)')
print('-' * 80)
dfii10 = load_fred('DFII10', 'DFII10')
baa10y = load_fred('BAA10Y', 'BAA10Y')
overlap = pd.concat([ts_primary['ratio_z'], ts_primary['ratio_3m_vix'].rename('ratio'),
                     dfii10.diff().rename('d_DFII10'), baa10y.diff().rename('d_BAA10Y'),
                     vix.rename('VIX_lvl')],
                    axis=1, join='inner').dropna()
overlap_results = {}
for other in ['d_DFII10', 'd_BAA10Y']:
    c_ratio, p1 = spearmanr(overlap['ratio'], overlap[other])
    c_z, p2 = spearmanr(overlap['ratio_z'], overlap[other])
    overlap_results[other] = {'corr_ratio': round(float(c_ratio), 4), 'p': round(float(p1), 5),
                              'corr_ratio_z': round(float(c_z), 4), 'p_z': round(float(p2), 5),
                              'n': int(len(overlap))}
    print(f'  corr(ratio, {other})   = {c_ratio:+.4f} (p={p1:.5f})   '
          f'corr(ratio_z, {other}) = {c_z:+.4f} (p={p2:.5f})  n={len(overlap)}')
# VIX level 자체와 term ratio 분리도 (term structure 가 level 과 다른 정보인지)
c_lvl, p_lvl = spearmanr(overlap['ratio'], overlap['VIX_lvl'])
overlap_results['VIX_level'] = {'corr_ratio_vs_VIX': round(float(c_lvl), 4), 'p': round(float(p_lvl), 5)}
print(f'  corr(ratio, VIX_level)   = {c_lvl:+.4f} (p={p_lvl:.5f})  '
      f'[term structure 가 level 과 구분되는 정보인지 — 음의 강상관 = backwardation↔고VIX 동조]')

# ============================================================================
# half-split OOS 부호 일치 (rule §1.7-D walk-forward)
# ============================================================================
print('\n' + '-' * 80)
print('half-split OOS 부호 일치 (contemp def_excess RankIC)')
print('-' * 80)
half = len(panel_d) // 2
oos_results = {}
for label, sl in [('first_half', slice(0, half)), ('second_half', slice(half, None))]:
    sub = panel_d.iloc[sl]
    ic, _ = spearmanr(sub['ratio_z'].values, sub['def_excess'].values, nan_policy='omit')
    oos_results[label] = {'rank_ic_def_excess': round(float(ic), 4), 'n': int(len(sub)),
                          'period': f'{sub.index.min().date()}~{sub.index.max().date()}'}
    print(f'  {label:<12s} ({sub.index.min().date()}~{sub.index.max().date()}, n={len(sub)}): '
          f'contemp RankIC(ratio_z, def_excess) = {ic:+.4f}')
sign_consistent = (np.sign(oos_results['first_half']['rank_ic_def_excess'])
                   == np.sign(oos_results['second_half']['rank_ic_def_excess']))
print(f'  → 부호 일치: {"YES" if sign_consistent else "NO"}')

# ============================================================================
# Save metrics
# ============================================================================
out = {
    'date': '2026-06-01',
    'hypothesis': 'H-VIXTS VIX term structure (VIX3M/VIX) → 방어주 상대강세',
    'spec': {
        'signal': 'ratio_3m_vix = VIX3M / VIX (own-history 252d z-score)',
        'prior_sign': 'backwardation(ratio<1) → def_excess↑ ⇒ corr(ratio_z, def_excess) 음',
        'def_pure_sleeve': DEFENSIVE_PURE,
        'fin_sleeve': FINANCIALS,
        'portfolio_label': PORTFOLIO_LABEL,
    },
    'data': {
        'VIX_30d': {'source': 'FRED VIXCLS', 'n': int(len(vix)),
                    'range': f'{vix.index.min().date()}~{vix.index.max().date()}'},
        'VIX3M': {'source': 'yfinance ^VIX3M', 'n': int(len(vix3m)),
                  'range': f'{vix3m.index.min().date()}~{vix3m.index.max().date()}',
                  'note': '★binding window — term ratio 2007-12~'},
        'VIX9D': {'source': 'yfinance ^VIX9D', 'n': int(len(vix9d)),
                  'range': f'{vix9d.index.min().date()}~{vix9d.index.max().date()}'},
        'term_ratio_panel': {'n': int(len(ts_primary)),
                             'range': f'{ts_primary.index.min().date()}~{ts_primary.index.max().date()}'},
    },
    'adf_pretest': adf_results,
    'b_rank_ic_contemp_vs_forward': ic_results,
    'multiple_comparison': {'m': m_total, 'alpha_bonferroni': round(alpha_bonf, 5)},
    'c_regime_split_welch': regime_results,
    'd_overlap_with_existing_factors': overlap_results,
    'oos_half_split': oos_results,
    'oos_sign_consistent': bool(sign_consistent),
    'seed': SEED,
}
with open(ROOT / 'validation-metrics-vix-term-structure.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, ensure_ascii=False, default=str)
print(f'\nSaved validation-metrics-vix-term-structure.json')
print('=' * 80)
