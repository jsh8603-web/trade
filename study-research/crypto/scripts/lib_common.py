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
