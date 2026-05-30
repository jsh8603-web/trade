"""m3_macro_linkage.py — REIT sleeve M3 거시연관 분석 (macro/timeline.md §4 가이드).

목적:
  (1) regime별(E1~E4 epoch) REIT 종목 평균수익·변동성 분해
  (2) REIT ~ [rate(Δus10y bp), dollar(Δlog DXY), oil(Δlog WTI)] OLS factor loading B
      전체 + epoch 조건부. ★M1 발견(주식 rate≈0, dollar rate-up 2배) REIT 검증.
  (3) cross-asset-class(REIT factor loading) vs within-sleeve(9 sub-sector pairwise 평균 ρ
      = equity factor proxy, L축 caveat) 구분.

★U3 reflexive 차단: 실현수익률 전용(belief/flag 不유입). ⛔ 합성無, yfinance + FRED 실데이터.
factor 정의는 M1 raw/m1_factor_linkage.py 와 정합:
  - rate = us10y.diff() (단위 변환 bp = ×100 일치 위해 본 script 도 bp 로 통일)
  - dollar = log(DXY).diff()
  - oil = log(WTI).diff()
종목 수익 = log(close).diff() (auto_adjust=True).
"""
from __future__ import annotations
import io
import sys
import urllib.request

import numpy as np
import pandas as pd
import yfinance as yf

# Windows console cp949 → utf-8 강제 (⛔ / ★ 등 emoji 출력 호환)
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass


# === Ticker map (REIT VNQ + 9 sub-sector representative) ===
TICKERS = {
    'VNQ':        'VNQ',   # broad REIT ETF
    'Industrial': 'PLD',   # Prologis
    'Apartment':  'AVB',   # AvalonBay
    'Office':     'BXP',   # Boston Properties
    'Healthcare': 'WELL',  # Welltower
    'Datacenter': 'EQIX',  # Equinix
    'Storage':    'PSA',   # Public Storage
    'Retail':     'SPG',   # Simon Property
    'Hotel':      'HST',   # Host Hotels
    'Tower':      'AMT',   # American Tower (cell tower / specialty)
}
SUB_SECTORS = ['Industrial', 'Apartment', 'Office', 'Healthcare', 'Datacenter',
               'Storage', 'Retail', 'Hotel', 'Tower']
ALL_SLEEVES = ['VNQ'] + SUB_SECTORS
FACTORS = ['rate', 'dollar', 'oil']

# === Epoch (M1 timeline.md §3 정합) ===
EPOCHS = {
    'E1_긴축충격':   ('2022-01-01', '2022-09-30'),
    'E2_전환·반등':  ('2022-10-01', '2023-06-30'),
    'E3_금리재상승': ('2023-07-01', '2023-09-30'),
    'E4_pivot·인하': ('2023-10-01', '2024-12-31'),
}
FULL_START, FULL_END = '2022-01-01', '2024-12-31'  # M1 timeline 범위 정합


def fetch_dgs10():
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"
    req = urllib.request.Request(url, headers={'User-Agent': 'reit-m3/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        csv_bytes = r.read()
    df = pd.read_csv(io.BytesIO(csv_bytes))
    date_col = 'observation_date' if 'observation_date' in df.columns else df.columns[0]
    val_col = 'DGS10' if 'DGS10' in df.columns else df.columns[1]
    df[date_col] = pd.to_datetime(df[date_col])
    df[val_col] = pd.to_numeric(df[val_col], errors='coerce')
    df = df.set_index(date_col).rename(columns={val_col: 'us10y'})
    return df[['us10y']].dropna()


def fetch_yf(tickers, start, end):
    """yfinance auto_adjust=True 일별 Close. Multi-ticker → 'Close' subframe."""
    data = yf.download(tickers, start=start, end=end, auto_adjust=True,
                       progress=False, threads=True)
    if isinstance(data.columns, pd.MultiIndex):
        return data['Close']
    return pd.DataFrame({tickers[0]: data['Close']})


def build_panel():
    """REIT 가격 + DXY + WTI + DGS10 일별 panel → factor·sleeve return 계산."""
    print("[1/4] fetching REIT prices (10 tickers, 2021-12 ~ 2025-01)…", flush=True)
    # 2021-12 부터 fetch (factor diff 첫날 NA 방지)
    reit_px = fetch_yf(list(TICKERS.values()), '2021-12-01', '2025-01-15')
    reit_px = reit_px.reindex(columns=list(TICKERS.values()))
    reit_px.columns = list(TICKERS.keys())
    print(f"  REIT shape={reit_px.shape}, span={reit_px.index[0].date()}~{reit_px.index[-1].date()}", flush=True)
    print(f"  NA per ticker:\n{reit_px.isna().sum().to_string()}", flush=True)

    print("\n[2/4] fetching DXY (DX-Y.NYB) + WTI (CL=F)…", flush=True)
    dxy = fetch_yf(['DX-Y.NYB'], '2021-12-01', '2025-01-15')
    dxy.columns = ['DXY']
    wti = fetch_yf(['CL=F'], '2021-12-01', '2025-01-15')
    wti.columns = ['WTI']
    print(f"  DXY n={dxy['DXY'].notna().sum()}, WTI n={wti['WTI'].notna().sum()}", flush=True)

    print("\n[3/4] fetching FRED DGS10…", flush=True)
    dgs = fetch_dgs10()
    print(f"  DGS10 span={dgs.index[0].date()}~{dgs.index[-1].date()}, n={len(dgs)}", flush=True)

    # Merge daily on trading day index = REIT index
    panel = reit_px.copy()
    panel['DXY'] = dxy['DXY'].reindex(panel.index).ffill()
    panel['WTI'] = wti['WTI'].reindex(panel.index).ffill()
    panel['us10y'] = dgs['us10y'].reindex(panel.index).ffill()
    panel = panel.dropna()
    print(f"\n[4/4] merged panel shape={panel.shape}, span={panel.index[0].date()}~{panel.index[-1].date()}", flush=True)

    # Build factor + sleeve return frame
    f = pd.DataFrame(index=panel.index)
    # rate = Δus10y in bp (M1 timeline bp 단위 통일)
    f['rate'] = panel['us10y'].diff() * 100.0
    f['dollar'] = np.log(panel['DXY']).diff()
    f['oil'] = np.log(panel['WTI']).diff()
    for s in ALL_SLEEVES:
        f[s] = np.log(panel[s]).diff()
    f = f.dropna()
    print(f"  factor+sleeve return frame: n={len(f)}, span={f.index[0].date()}~{f.index[-1].date()}", flush=True)
    return f


def fit_B_Lambda(f):
    """OLS: sleeve ~ factors (+intercept) → B(S,F), Λ(F,F), idio var. M1 fit 동일."""
    Fm = f[FACTORS].values
    Fc = np.column_stack([np.ones(len(Fm)), Fm])
    betas, idio, tvals = {}, {}, {}
    for s in ALL_SLEEVES:
        y = f[s].values
        coef, *_ = np.linalg.lstsq(Fc, y, rcond=None)
        betas[s] = coef[1:]
        resid = y - Fc @ coef
        n, k = Fc.shape
        sse = float(np.sum(resid**2))
        sigma2 = sse / (n - k)
        try:
            cov_beta = sigma2 * np.linalg.inv(Fc.T @ Fc)
            se = np.sqrt(np.diag(cov_beta))[1:]
            tvals[s] = coef[1:] / se
        except np.linalg.LinAlgError:
            tvals[s] = np.array([np.nan] * 3)
        idio[s] = float(np.var(resid))
    Lam = np.cov(Fm, rowvar=False)
    return betas, Lam, idio, tvals


def summarize_returns(f, sleeves):
    """평균 일별수익 (bp), 연환산 std (%, ×√252)."""
    rows = []
    for s in sleeves:
        y = f[s].dropna()
        rows.append({
            'sleeve': s,
            'n': len(y),
            'mean_daily_bp': y.mean() * 1e4,
            'annvol_pct': y.std() * np.sqrt(252) * 100,
            'cum_pct': (np.exp(y.sum()) - 1) * 100,
        })
    return pd.DataFrame(rows).set_index('sleeve')


def mean_offdiag_corr(f, sleeves):
    """9 sub-sector pairwise correlation 평균 (within-sleeve = equity factor proxy)."""
    sub = f[sleeves].dropna()
    if len(sub) < 30:
        return np.nan, np.nan, 0
    C = sub.corr().values
    n = len(sleeves)
    iu = np.triu_indices(n, k=1)
    offs = C[iu]
    return float(np.mean(offs)), float(np.min(offs)), int(len(offs))


def main():
    f = build_panel()
    print("\n" + "=" * 88, flush=True)
    print("M3 거시-종목 factor linkage | REIT VNQ + 9 sub-sector ETF", flush=True)
    print(f"factors={FACTORS} (rate=Δus10y bp, dollar=Δlog DXY, oil=Δlog WTI)", flush=True)
    print("⛔ 실현수익률 전용(U3 reflexive 차단) · 합성無 · yfinance auto_adjust + FRED DGS10", flush=True)
    print("=" * 88, flush=True)

    # === 1. 전체 + epoch 별 수익분해 ===
    print("\n## 1. regime별 수익분해 (epoch × sleeve)", flush=True)
    for label, (s, e) in [('전체', (FULL_START, FULL_END))] + list(EPOCHS.items()):
        sub = f.loc[(f.index >= s) & (f.index <= e)]
        if len(sub) < 5:
            print(f"\n[{label}] {s}~{e} n={len(sub)} (insufficient)", flush=True)
            continue
        summ = summarize_returns(sub, ALL_SLEEVES)
        print(f"\n[{label}] {s}~{e} n_days={len(sub)}", flush=True)
        print(summ[['n', 'mean_daily_bp', 'annvol_pct', 'cum_pct']].round(2).to_string(), flush=True)

    # === 2. factor loading B (전체 + epoch 조건부) ===
    print("\n\n## 2. factor loading B (REIT sleeve ~ [rate, dollar, oil] OLS)", flush=True)
    print("rate 단위: bp (e.g. β_rate=+0.5 → us10y +1bp 시 sleeve 일별 +0.5e-4)", flush=True)
    print("t-stat |t|>2 ≈ 95% 유의. ★M1 비교: 주식 us_stock rate=+0.008(~0), dollar=-0.879", flush=True)

    all_results = {}
    for label, (s, e) in [('전체', (FULL_START, FULL_END))] + list(EPOCHS.items()):
        sub = f.loc[(f.index >= s) & (f.index <= e)].dropna()
        if len(sub) < 30:
            print(f"\n[{label}] insufficient n={len(sub)}", flush=True)
            continue
        betas, Lam, idio, tv = fit_B_Lambda(sub)
        all_results[label] = (betas, Lam, idio, tv)
        print(f"\n[{label}] n={len(sub)} ({s}~{e})", flush=True)
        print(f"  {'sleeve':<12} {'β_rate':>10} {'t_rate':>8} {'β_dollar':>10} {'t_dol':>8} "
              f"{'β_oil':>10} {'t_oil':>8} {'idio_var':>12}", flush=True)
        for sl in ALL_SLEEVES:
            b = betas[sl]
            t = tv[sl]
            print(f"  {sl:<12} {b[0]*1e4:+10.3f} {t[0]:+8.2f} {b[1]:+10.4f} {t[1]:+8.2f} "
                  f"{b[2]:+10.4f} {t[2]:+8.2f} {idio[sl]:12.2e}", flush=True)

    # === 3. cross-asset (factor loading) vs within-sleeve (sub-sector pairwise ρ) ===
    print("\n\n## 3. cross-asset vs within-sleeve 구분 (L축 caveat)", flush=True)
    print("within-sleeve = 9 sub-sector pairwise ρ 평균(equity factor proxy, M1 us_stock~tech 0.96 와 유사 기대)", flush=True)
    print(f"  {'epoch':<14} {'n_days':>8} {'mean_ρ':>10} {'min_ρ':>10} {'n_pair':>8}", flush=True)
    for label, (s, e) in [('전체', (FULL_START, FULL_END))] + list(EPOCHS.items()):
        sub = f.loc[(f.index >= s) & (f.index <= e)]
        m, mn, npair = mean_offdiag_corr(sub, SUB_SECTORS)
        if np.isnan(m):
            print(f"  {label:<14} {len(sub):>8d} insufficient", flush=True)
        else:
            print(f"  {label:<14} {len(sub):>8d} {m:+10.3f} {mn:+10.3f} {npair:>8d}", flush=True)

    # === 4. epoch 별 loading 차이 (M1 핵심: 거시→REIT 국면조건부?) ===
    print("\n\n## 4. epoch별 loading 변동 — VNQ + 주요 sub-sector (M1 발견 검증)", flush=True)
    print("M1 us_stock rate-UP − rate-DOWN: Δrate -0.025 / Δdollar -0.405 (rate-up 시 dollar loading 2배)", flush=True)
    key_sleeves = ['VNQ', 'Industrial', 'Office', 'Apartment', 'Healthcare', 'Tower']
    print(f"\n  {'sleeve':<12} " + " ".join(f"{e:>22}" for e in EPOCHS.keys()), flush=True)
    print(f"  {'(β_rate)':<12} " + " ".join(f"{'(β_rate / β_dollar)':>22}" for _ in EPOCHS), flush=True)
    for sl in key_sleeves:
        line = f"  {sl:<12} "
        for ep in EPOCHS.keys():
            if ep in all_results:
                b = all_results[ep][0][sl]
                line += f"  {b[0]*1e4:+7.2f}bp / {b[1]:+7.3f}  "
            else:
                line += " " * 24
        print(line, flush=True)

    # === 5. M1 finding REIT 검증 summary ===
    print("\n\n## 5. M1 finding REIT 검증 (rate loading ≈ 0 / dollar loading rate-UP 2배?)", flush=True)
    if '전체' in all_results:
        b, _, _, t = all_results['전체']
        print("  [전체 기간] sleeve | β_rate (bp scale) | t | β_dollar | t", flush=True)
        for sl in ['VNQ', 'Industrial', 'Office', 'Apartment', 'Healthcare', 'Tower']:
            print(f"    {sl:<12} β_rate={b[sl][0]*1e4:+7.3f} (t={t[sl][0]:+.2f}) "
                  f"β_dollar={b[sl][1]:+7.3f} (t={t[sl][1]:+.2f})", flush=True)

    # E1 vs E4 dollar loading 비교 (rate-UP epoch vs rate-DOWN epoch)
    if 'E1_긴축충격' in all_results and 'E4_pivot·인하' in all_results:
        print("\n  [E1 긴축충격 (rate↑↑) vs E4 pivot·인하 (rate↓) dollar loading 차이]", flush=True)
        b1 = all_results['E1_긴축충격'][0]
        b4 = all_results['E4_pivot·인하'][0]
        for sl in ['VNQ', 'Industrial', 'Office', 'Apartment', 'Healthcare', 'Tower']:
            d_dollar = b1[sl][1] - b4[sl][1]
            ratio = b1[sl][1] / b4[sl][1] if abs(b4[sl][1]) > 1e-6 else np.nan
            print(f"    {sl:<12} E1 dollar={b1[sl][1]:+.3f} / E4 dollar={b4[sl][1]:+.3f} "
                  f"Δ={d_dollar:+.3f} ratio(E1/E4)={ratio:+.2f}x", flush=True)

    print("\n해석 (자동 stub):", flush=True)
    print("  - VNQ β_rate ≈ 0 면 M1(주식) 패턴과 정합 → REIT 도 rate 직접 loading 약함, dollar 채널 가설.", flush=True)
    print("  - E1 |β_dollar| / E4 |β_dollar| > 1.5 면 M1 'rate-UP 시 dollar loading 2배' 패턴 REIT 검증.", flush=True)
    print("  - within-sleeve mean ρ > 0.7 → equity factor 지배 (L축 caveat: cross-asset 외 within 별도 처리).", flush=True)

    print("\n=== M3 done ===", flush=True)


if __name__ == "__main__":
    main()
