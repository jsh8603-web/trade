"""crypto validation 공용 라이브러리.

PIT 보존, Rank-IC, e-CUSUM 단측, Newey-West SE, block bootstrap CI, partial-corr.
⛔ 합성 데이터 금지 — 모든 통계는 실측 CSV 입력.
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

DATA = Path(__file__).resolve().parent.parent / "raw" / "data"


# ===========================================================================
# 데이터 로더 (모두 PIT — 결측 forward fill X, raw 유지)
# ===========================================================================
def _parse_iso(series):
    """ISO8601 mixed format safely parse, drop invalid."""
    return pd.to_datetime(series, format="ISO8601", errors="coerce", utc=True).dt.tz_localize(None)


def load_btc_klines() -> pd.DataFrame:
    """Binance BTCUSDT daily klines. cols: date(datetime), open, high, low, close, volume."""
    p = DATA / "binance-klines-btcusdt-1d.csv"
    df = pd.read_csv(p)
    df["date"] = pd.to_datetime(df["date_utc"], format="%Y-%m-%d", errors="coerce")
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df[["date", "open", "high", "low", "close", "volume"]]


def load_coinmetrics() -> pd.DataFrame:
    p = DATA / "coinmetrics-btc-daily.csv"
    df = pd.read_csv(p)
    df["date"] = _parse_iso(df["time"]).dt.normalize()
    for c in ["CapMVRVCur", "CapRealUSD", "CapMrktCurUSD", "PriceUSD", "ReferenceRateUSD"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date").reset_index(drop=True)
    return df


def load_coinmetrics_v2() -> pd.DataFrame:
    """v2 신규 4 metric (P0-A 2026-05-31): AdrActCnt / TxCnt / HashRate / BlkCnt.

    anonymous tier probe 후 확정 (TxTfrValAdjUSD / SOPR / RevUSD = 403, 별도).
    range: 2009-01-03 ~ 2026-05-30 (6357 daily).
    """
    p = DATA / "coinmetrics-btc-daily-v2.csv"
    df = pd.read_csv(p)
    df["date"] = _parse_iso(df["time"]).dt.normalize()
    for c in ["AdrActCnt", "TxCnt", "HashRate", "BlkCnt"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date").reset_index(drop=True)
    return df


def load_fgi() -> pd.DataFrame:
    p = DATA / "fgi-daily.csv"
    df = pd.read_csv(p)
    df["date"] = pd.to_datetime(df["date_utc"], format="%Y-%m-%d", errors="coerce")
    df["fgi"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)[["date", "fgi", "classification"]]


def load_funding() -> pd.DataFrame:
    p = DATA / "binance-funding-btcusdt.csv"
    df = pd.read_csv(p)
    df["datetime"] = _parse_iso(df["datetime_utc"])
    df["funding_rate"] = pd.to_numeric(df["funding_rate"], errors="coerce")
    df = df.dropna(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)
    df["date"] = df["datetime"].dt.normalize()
    return df


def load_funding_daily() -> pd.DataFrame:
    """funding 8h → daily mean·max·min·sign change count."""
    df = load_funding()
    g = df.groupby("date")["funding_rate"].agg(
        mean="mean", max="max", min="min", count="count",
        absmax=lambda x: x.abs().max(),
    ).reset_index()
    return g


def load_yfinance(symbol: str) -> pd.DataFrame:
    """yfinance daily close loader. symbol = 'ixic' / 'gspc' / 'vix' / 'gold-gcf'."""
    p = DATA / f"yfinance-{symbol}.csv"
    df = pd.read_csv(p)
    df["date"] = pd.to_datetime(df["date_utc"], format="%Y-%m-%d", errors="coerce")
    for c in ["Open", "High", "Low", "Close", "Volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date").reset_index(drop=True)
    return df[[c for c in ["date", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]]


def load_fred(code: str) -> pd.DataFrame:
    """FRED series loader. code = 'dfii10' / 'dtwexbgs' / 'm2sl'."""
    p = DATA / f"fred-{code}.csv"
    df = pd.read_csv(p)
    df["date"] = pd.to_datetime(df["date_utc"], format="%Y-%m-%d", errors="coerce")
    # 컬럼명 = FRED code 대문자
    upper = code.upper()
    if upper in df.columns:
        df[upper] = pd.to_numeric(df[upper], errors="coerce")
    return df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date").reset_index(drop=True)


def load_stablecoin() -> pd.DataFrame:
    p = DATA / "defillama-stablecoin-total.csv"
    df = pd.read_csv(p)
    df["date"] = pd.to_datetime(df["date_utc"], format="%Y-%m-%d", errors="coerce")
    df["total_supply"] = pd.to_numeric(df["total_circulating_peggedUSD"], errors="coerce")
    return df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)[["date", "total_supply"]]


# ===========================================================================
# 통계 도구
# ===========================================================================
def rank_ic(x: pd.Series, y: pd.Series) -> tuple[float, int]:
    """Spearman rank-IC."""
    mask = x.notna() & y.notna()
    if mask.sum() < 5:
        return (np.nan, int(mask.sum()))
    rho, p = stats.spearmanr(x[mask], y[mask])
    return (float(rho), int(mask.sum()))


def newey_west_se(x: np.ndarray, lags: int) -> float:
    """Newey-West 보정 표준오차 (long-run variance)."""
    n = len(x)
    if n < 5:
        return np.nan
    x = x - x.mean()
    s = (x ** 2).mean()
    for k in range(1, lags + 1):
        w = 1 - k / (lags + 1)
        c = (x[k:] * x[:-k]).mean()
        s += 2 * w * c
    return float(np.sqrt(max(s, 0) / n))


def effective_n(x: np.ndarray) -> float:
    """autocorrelation-adjusted effective N (Bartlett-like)."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 10:
        return float(n)
    # AR(1) 추정
    m = x.mean()
    num = ((x[1:] - m) * (x[:-1] - m)).sum()
    den = ((x - m) ** 2).sum()
    if den <= 0:
        return float(n)
    rho1 = num / den
    rho1 = max(min(rho1, 0.99), -0.99)
    # effective N = n * (1 - rho) / (1 + rho)
    return float(n * (1 - rho1) / (1 + rho1))


def e_cusum_one_sided(z: np.ndarray, alpha: float = 0.05, tau2: float = 1.0) -> tuple[bool, float]:
    """단측 e-CUSUM (mixture supermartingale, log_R = max(0, ·) reset).

    z_t = (baseline - ic_t) / sd. ic 가 baseline 아래로 떨어질수록 z↑ → kill.
    P(거짓 kill) ≤ alpha (Ville).
    """
    z = np.asarray(z, dtype=float)
    z = z[~np.isnan(z)]
    log_R = 0.0
    max_R = 1.0
    for zi in z:
        # mixture: E[exp(λz - λ²/2)] over λ ~ N(0, τ²)
        # log E = z²τ² / (2(1+τ²)) - 0.5 log(1+τ²)
        log_eR = (zi ** 2 * tau2) / (2 * (1 + tau2)) - 0.5 * np.log(1 + tau2)
        log_R = max(0.0, log_R + log_eR)
        max_R = max(max_R, np.exp(log_R))
    threshold = 1.0 / alpha
    return (bool(max_R >= threshold), float(max_R))


def block_bootstrap_ci(x: np.ndarray, fn, n_boot: int = 1000, block_len: int = 30,
                       seed: int = 42, ci: float = 0.95) -> tuple[float, float, float]:
    """block bootstrap CI for arbitrary statistic fn(x). returns (lower, mean, upper)."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < block_len * 2:
        return (np.nan, np.nan, np.nan)
    n_blocks = n // block_len
    stats_b = np.empty(n_boot)
    for i in range(n_boot):
        starts = rng.integers(0, n - block_len + 1, size=n_blocks)
        sample = np.concatenate([x[s:s+block_len] for s in starts])
        stats_b[i] = fn(sample)
    a = (1 - ci) / 2
    lo = float(np.quantile(stats_b, a))
    hi = float(np.quantile(stats_b, 1 - a))
    return (lo, float(stats_b.mean()), hi)


# ===========================================================================
# Regime 분류
# ===========================================================================
def fgi_regime(fgi: float) -> str:
    if pd.isna(fgi):
        return "na"
    if fgi <= 24:
        return "extreme_fear"
    if fgi <= 44:
        return "fear"
    if fgi <= 55:
        return "neutral"
    if fgi <= 75:
        return "greed"
    return "extreme_greed"


HALVING_DATES = [
    pd.Timestamp("2012-11-28"),
    pd.Timestamp("2016-07-09"),
    pd.Timestamp("2020-05-11"),
    pd.Timestamp("2024-04-19"),
]


def halving_phase(date: pd.Timestamp) -> str:
    """0-6m / 6-18m / 18-24m / 24-36m / pre (before any halving)."""
    if pd.isna(date):
        return "na"
    last = None
    for h in HALVING_DATES:
        if date >= h:
            last = h
        else:
            break
    if last is None:
        return "pre_first_halving"
    months = (date - last).days / 30.44
    if months < 6:
        return "post_0_6m"
    if months < 18:
        return "post_6_18m"
    if months < 24:
        return "post_18_24m"
    if months < 36:
        return "post_24_36m"
    return "pre_next_halving"


# ===========================================================================
# Forward return 계산
# ===========================================================================
def forward_return(close: pd.Series, horizon: int) -> pd.Series:
    """log(close[t+h] / close[t]). 미래 lookahead OK (검증 대상). PIT 시점 = t."""
    return np.log(close.shift(-horizon) / close)


# ===========================================================================
# On-chain valuation (MVRV-derived; collector 무관 — CoinMetrics 보유)
# theory-notes §1(i) Glassnode framework. H1 conditioning 확장 후보 (P1-2, 2026-05-31).
# ===========================================================================
def nupl(market_cap=None, realized_cap=None, mvrv=None) -> pd.Series:
    """Net Unrealized Profit/Loss = (M - R) / M = 1 - 1/MVRV (회계 동치).

    두 진입점:
    - (market_cap, realized_cap) 모두 제공: 직접 정의
    - mvrv 만 제공: 1 - 1/mvrv 회계 동치 (CoinMetrics anonymous tier 폴백)

    Glassnode regime band: >0.75 Euphoria / 0.5-0.75 Belief / 0.25-0.5 Optimism /
    0-0.25 Hope / <0 Capitulation.
    """
    if mvrv is not None:
        v = pd.Series(mvrv, dtype=float).reset_index(drop=True)
        return 1.0 - 1.0 / v
    if market_cap is None or realized_cap is None:
        raise ValueError("nupl(): mvrv 또는 (market_cap, realized_cap) 둘 다 필수")
    m = pd.Series(market_cap, dtype=float).reset_index(drop=True)
    r = pd.Series(realized_cap, dtype=float).reset_index(drop=True)
    return (m - r) / m


def mvrv_z(market_cap=None, realized_cap=None, mvrv=None, window: int = 1460) -> pd.Series:
    """MVRV-Z = (M - R) / σ(M) over rolling window (4y = 1460d, Glassnode 표준).

    두 진입점:
    - (market_cap, realized_cap) 직접 정의
    - (market_cap, mvrv) 제공: R = M/mvrv 역산 후 동일 계산 (anonymous tier 폴백)

    ⚠️ 4y warmup — 첫 1460d 구간 NaN.
    """
    if market_cap is None:
        raise ValueError("mvrv_z(): market_cap 필수")
    m = pd.Series(market_cap, dtype=float).reset_index(drop=True)
    if realized_cap is not None:
        r = pd.Series(realized_cap, dtype=float).reset_index(drop=True)
    elif mvrv is not None:
        v = pd.Series(mvrv, dtype=float).reset_index(drop=True)
        r = m / v
    else:
        raise ValueError("mvrv_z(): realized_cap 또는 mvrv 둘 중 하나 필수")
    sigma = m.rolling(window=window, min_periods=window // 2).std()
    return (m - r) / sigma


if __name__ == "__main__":
    # ⚠️ anonymous tier = CapRealUSD 빈칸. MVRV+MarketCap 으로 역산 폴백.
    cm = load_coinmetrics()
    cm = cm.dropna(subset=["CapMrktCurUSD", "CapMVRVCur"]).reset_index(drop=True)
    n_total = len(cm)
    n_real = cm["CapRealUSD"].notna().sum() if "CapRealUSD" in cm.columns else 0
    print(f"[lib_common sanity] n_obs (MVRV+MarketCap) = {n_total}, "
          f"CapRealUSD 비어있지 않음 = {n_real} (anonymous tier 확인)")

    cm["nupl_val"] = nupl(mvrv=cm["CapMVRVCur"])
    cm["mvrv_z_val"] = mvrv_z(market_cap=cm["CapMrktCurUSD"], mvrv=cm["CapMVRVCur"], window=1460)
    n_zwarmed = cm["mvrv_z_val"].notna().sum()
    print(f"mvrv_z warmup-passed (4y 후): {n_zwarmed} days")
    print(f"NUPL range: [{cm['nupl_val'].min():.4f}, {cm['nupl_val'].max():.4f}]")
    q = cm["nupl_val"].quantile([0.25, 0.5, 0.75]).values
    print(f"NUPL p25/p50/p75: [{q[0]:.4f}, {q[1]:.4f}, {q[2]:.4f}]")
    z = cm["mvrv_z_val"].dropna()
    print(f"MVRV-Z range (4y warmup 후): [{z.min():.4f}, {z.max():.4f}]")
    nupl_euph = (cm["nupl_val"] > 0.75).sum()
    nupl_capi = (cm["nupl_val"] < 0).sum()
    print(f"NUPL >0.75 Euphoria days: {nupl_euph} ({100*nupl_euph/n_total:.1f}%)")
    print(f"NUPL <0 Capitulation days: {nupl_capi} ({100*nupl_capi/n_total:.1f}%)")
    rho_nm = cm[["nupl_val", "CapMVRVCur"]].corr().iloc[0, 1]
    print(f"⚠️ corr(NUPL, MVRV) = {rho_nm:.4f} (회계 동치 — 단조변환)")
