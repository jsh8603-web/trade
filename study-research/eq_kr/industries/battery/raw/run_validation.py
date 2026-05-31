"""run_validation.py — 2차전지 산업 실측 validation 통합 스크립트.

frame.md v2 §M1 (Rank-IC) + §M2 (lag-corr) + §M3 (regime) + §M4 (5게이트) 매핑.

산출:
- raw/data/{ticker}.parquet — 종목 가격 (FDR)
- raw/data/macro.parquet — USDKRW, KOSPI, LIT, BATT, SMH, TSLA
- raw/validation-metrics.json — 모든 IC / lag-corr / regime cell 결과 (JSON)
- raw/validation-summary.txt — 사람이 읽는 요약

SSOT: D:/projects/Inv/study-research/eq_kr/frame.md v2
universe: 373220 LG에너지솔루션, 006400 삼성SDI, 247540 에코프로비엠, 003670 포스코퓨처엠
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Paths
ROOT = Path(__file__).resolve().parent  # raw/
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

# Universe (frame §1 Tier 2)
UNIVERSE = {
    "373220": ("LG에너지솔루션", "cell"),
    "006400": ("삼성SDI", "cell"),
    "247540": ("에코프로비엠", "cathode"),
    "003670": ("포스코퓨처엠", "cathode"),
}

START_DATE = "2018-01-01"
END_DATE = "2026-05-29"


# ============================================================
# 1. Data Load
# ============================================================

def load_prices() -> Dict[str, pd.DataFrame]:
    """FDR 종목 가격 + Adj Close 의존. cache 후 재사용."""
    import FinanceDataReader as fdr
    out = {}
    for tk in UNIVERSE:
        cache = DATA / f"{tk}.parquet"
        if cache.exists():
            df = pd.read_parquet(cache)
        else:
            df = fdr.DataReader(tk, START_DATE, END_DATE)
            df.to_parquet(cache)
        out[tk] = df
    return out


def load_macro() -> pd.DataFrame:
    """USDKRW, KOSPI, LIT, BATT, SMH, TSLA — 일별 종가 wide format."""
    import FinanceDataReader as fdr
    import yfinance as yf

    cache = DATA / "macro.parquet"
    if cache.exists():
        return pd.read_parquet(cache)

    fx = fdr.DataReader("USD/KRW", START_DATE, END_DATE)["Close"].rename("USDKRW")
    kospi = fdr.DataReader("KS11", START_DATE, END_DATE)["Close"].rename("KOSPI")

    yf_syms = ["LIT", "BATT", "SMH", "TSLA"]
    yf_data = yf.download(yf_syms, start=START_DATE, end=END_DATE, progress=False, auto_adjust=True)["Close"]
    yf_data.columns = [c if isinstance(c, str) else c[0] for c in yf_data.columns]

    df = pd.concat([fx, kospi, yf_data], axis=1)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index().ffill(limit=5)  # 환율/주가 mismatch 5d ffill
    df.to_parquet(cache)
    return df


# ============================================================
# 2. Returns + features
# ============================================================

def compute_forward_returns(prices: Dict[str, pd.DataFrame], horizons: List[int] = [5, 20, 60]) -> pd.DataFrame:
    """종목별 forward return 계산. wide format (date × ticker_h)."""
    out = {}
    for tk, df in prices.items():
        close = df["Close"]
        for h in horizons:
            fwd = close.shift(-h) / close - 1
            out[f"{tk}_y{h}d"] = fwd
    return pd.concat(out, axis=1).dropna(how="all")


def compute_yoy(series: pd.Series, window: int = 252) -> pd.Series:
    """일별 yoy = level / level.shift(252) - 1."""
    return series / series.shift(window) - 1


# ============================================================
# 3. Rank-IC (월간 횡단면, frame §M1)
# ============================================================

def monthly_rank_ic(
    feature: pd.Series,
    fwd_returns: pd.DataFrame,
    horizon: int = 20,
) -> Tuple[float, float, float, int]:
    """월말 cross-sectional Spearman corr (feature vs forward return).

    Returns:
        (ic_mean, ic_se, t_stat, n_months)
    """
    monthly_idx = feature.resample("M").last().index
    ic_series = []
    for dt in monthly_idx:
        if dt not in feature.index:
            # nearest preceding
            try:
                feat_dt = feature.loc[:dt].iloc[-1]
            except IndexError:
                continue
        else:
            feat_dt = feature.loc[dt]
        # cross-sec at dt: feature 값은 단일 (시계열 driver) → 무의미
        # 본 함수는 시계열 lag-corr 용으로 부적합. 단순 placeholder.
        pass
    return (np.nan, np.nan, np.nan, 0)


def panel_rank_ic_cross_sectional(
    feature_panel: pd.DataFrame,  # date × ticker
    fwd_panel: pd.DataFrame,       # date × ticker (same shape)
    monthly: bool = True,
) -> Dict:
    """월말마다 종목 횡단면 Spearman corr → IC 시계열.

    feature_panel = 각 종목별 feature (z-score) 패널.
    fwd_panel = 각 종목별 forward return.
    """
    if monthly:
        f = feature_panel.resample("M").last()
        r = fwd_panel.resample("M").last()
    else:
        f = feature_panel
        r = fwd_panel
    common_idx = f.index.intersection(r.index)
    common_cols = f.columns.intersection(r.columns)
    ics = []
    ns = []
    for dt in common_idx:
        fv = f.loc[dt, common_cols].dropna()
        rv = r.loc[dt, common_cols].dropna()
        common = fv.index.intersection(rv.index)
        if len(common) < 3:
            continue
        rho, _ = stats.spearmanr(fv.loc[common], rv.loc[common])
        if not np.isnan(rho):
            ics.append(rho)
            ns.append(len(common))
    ics = np.array(ics)
    if len(ics) < 3:
        return {"ic_mean": np.nan, "ic_sd": np.nan, "ic_se": np.nan, "t_stat": np.nan,
                "n_months": len(ics), "ci95_low": np.nan, "ci95_high": np.nan}
    ic_mean = float(np.mean(ics))
    ic_sd = float(np.std(ics, ddof=1))
    ic_se = ic_sd / np.sqrt(len(ics))
    t_stat = ic_mean / ic_se if ic_se > 0 else np.nan
    return {
        "ic_mean": ic_mean, "ic_sd": ic_sd, "ic_se": ic_se, "t_stat": t_stat,
        "n_months": len(ics),
        "ci95_low": ic_mean - 1.96 * ic_se, "ci95_high": ic_mean + 1.96 * ic_se,
        "avg_universe_n": float(np.mean(ns)),
    }


# ============================================================
# 4. lag-corr (시계열, frame §M2)
# ============================================================

def lag_corr_with_newey_west(
    x: pd.Series,
    y: pd.Series,
    lags: List[int] = [0, 1, 3, 6],
    freq: str = "M",
    nw_lags: int = 3,
) -> Dict[int, Dict]:
    """월간 lag-corr + Newey-West HAC SE.

    x = driver (yoy), y = forward return panel mean.
    """
    x_m = x.resample(freq).last()
    y_m = y.resample(freq).last()
    out = {}
    for L in lags:
        x_shift = x_m.shift(L)
        df = pd.concat([x_shift, y_m], axis=1, keys=["x", "y"]).dropna()
        if len(df) < 12:
            out[L] = {"corr": np.nan, "n": len(df), "p_value": np.nan, "nw_se": np.nan}
            continue
        # Spearman corr
        rho, p = stats.spearmanr(df["x"], df["y"])
        # Newey-West HAC SE for Pearson (approx, monthly autocorr)
        # variance ratio: SE_NW = sqrt(var * (1 + 2 sum_k=1^L rho_k))
        n = len(df)
        try:
            x_demean = df["x"].rank() - df["x"].rank().mean()
            y_demean = df["y"].rank() - df["y"].rank().mean()
            prod = x_demean * y_demean
            v0 = float(np.var(prod, ddof=1))
            nw_factor = 1.0
            for k in range(1, nw_lags + 1):
                if len(prod) <= k:
                    break
                gamma_k = float(np.cov(prod.values[:-k], prod.values[k:])[0, 1]) if len(prod) > k else 0
                w = 1 - k / (nw_lags + 1)
                nw_factor += 2 * w * (gamma_k / v0) if v0 > 0 else 0
            nw_se = np.sqrt(max(v0 * max(nw_factor, 0.1), 0.0)) / (n * float(np.std(x_demean, ddof=1) * np.std(y_demean, ddof=1) + 1e-9))
        except Exception:
            nw_se = np.nan
        out[L] = {
            "corr": float(rho), "n": int(n), "p_value": float(p),
            "nw_se": float(nw_se) if not np.isnan(nw_se) else None,
        }
    return out


# ============================================================
# 5. Regime 분해 (frame §M3)
# ============================================================

def classify_krw_regime(usdkrw_yoy: pd.Series) -> pd.Series:
    """USDKRW yoy > +5% = 약세, < -5% = 강세, else 중립."""
    out = pd.Series(index=usdkrw_yoy.index, dtype=object)
    out[usdkrw_yoy > 0.05] = "krw_weak"
    out[usdkrw_yoy < -0.05] = "krw_strong"
    out[(usdkrw_yoy >= -0.05) & (usdkrw_yoy <= 0.05)] = "krw_neutral"
    return out


def classify_lit_regime(lit_yoy: pd.Series) -> pd.Series:
    """LIT yoy > +20% = bull, < -20% = bear, else neutral. (리튬 hyper-volatile)"""
    out = pd.Series(index=lit_yoy.index, dtype=object)
    out[lit_yoy > 0.20] = "lit_bull"
    out[lit_yoy < -0.20] = "lit_bear"
    out[(lit_yoy >= -0.20) & (lit_yoy <= 0.20)] = "lit_neutral"
    return out


def regime_breakdown_corr(
    driver_yoy: pd.Series,
    fwd_mean: pd.Series,
    regime: pd.Series,
    freq: str = "M",
) -> Dict[str, Dict]:
    """regime별 lag-0 corr 분해."""
    d = driver_yoy.resample(freq).last()
    f = fwd_mean.resample(freq).last()
    r = regime.resample(freq).last()
    df = pd.concat([d, f, r], axis=1, keys=["d", "f", "r"]).dropna()
    out = {}
    for reg in df["r"].unique():
        sub = df[df["r"] == reg]
        if len(sub) < 5:
            out[reg] = {"corr": np.nan, "n": len(sub), "verdict": "INSUFFICIENT"}
            continue
        rho, p = stats.spearmanr(sub["d"], sub["f"])
        out[reg] = {"corr": float(rho), "n": int(len(sub)), "p_value": float(p),
                    "verdict": "PASS" if (not np.isnan(p) and p < 0.10 and len(sub) >= 24) else "TENTATIVE"}
    return out


# ============================================================
# 6. OOS split (IS 2018-2022, OOS 2023-2026)
# ============================================================

def is_oos_split(series: pd.DataFrame, split_date: str = "2023-01-01") -> Tuple[pd.DataFrame, pd.DataFrame]:
    split = pd.Timestamp(split_date)
    return series[series.index < split], series[series.index >= split]


# ============================================================
# 7. Run All Validation
# ============================================================

def run_all():
    print("[1/6] Loading prices...")
    prices = load_prices()
    print("[2/6] Loading macro...")
    macro = load_macro()

    print("[3/6] Computing returns + yoy...")
    fwd = compute_forward_returns(prices, [5, 20, 60])
    # ticker × horizon panel
    fwd_panel_20 = pd.DataFrame({tk: fwd[f"{tk}_y20d"] for tk in UNIVERSE})
    fwd_panel_60 = pd.DataFrame({tk: fwd[f"{tk}_y60d"] for tk in UNIVERSE})

    # sub-cluster
    cell_tks = [tk for tk, (_, c) in UNIVERSE.items() if c == "cell"]
    cathode_tks = [tk for tk, (_, c) in UNIVERSE.items() if c == "cathode"]

    fwd_industry_mean = fwd_panel_20.mean(axis=1)
    fwd_cell_mean = fwd_panel_20[cell_tks].mean(axis=1)
    fwd_cathode_mean = fwd_panel_60[cathode_tks].mean(axis=1)

    # macro yoy
    usdkrw_yoy = compute_yoy(macro["USDKRW"])
    lit_yoy = compute_yoy(macro["LIT"])
    batt_yoy = compute_yoy(macro["BATT"])
    smh_yoy = compute_yoy(macro["SMH"])
    tsla_yoy = compute_yoy(macro["TSLA"])
    kospi_yoy = compute_yoy(macro["KOSPI"])

    results = {
        "meta": {
            "as_of": END_DATE,
            "universe": list(UNIVERSE.keys()),
            "sub_cluster": {"cell": cell_tks, "cathode": cathode_tks},
            "start_date": START_DATE,
            "end_date": END_DATE,
            "n_trading_days": len(macro),
        },
        "data_coverage": {
            tk: {"first": str(prices[tk].index[0].date()), "last": str(prices[tk].index[-1].date()),
                 "n_rows": len(prices[tk])}
            for tk in UNIVERSE
        },
    }

    print("[4/6] H1 USDKRW → cell sub (panel cross-sec rank-IC)...")
    # H1: USDKRW yoy 종목별 z-score (단순화: 전체 panel 동일 driver)
    # 본 가설은 cross-section 이 아닌 time-series single-driver → lag-corr 로 측정 (cell sub mean)
    h1_lag = lag_corr_with_newey_west(usdkrw_yoy, fwd_cell_mean, lags=[0, 1, 3], freq="M", nw_lags=3)
    results["H1_usdkrw_to_cell"] = {"type": "lag_corr", "monthly": True, "lags": h1_lag,
        "note": "USDKRW yoy (driver) → cell sub mean y20d. 셀 = 373220, 006400."}

    # H1 regime breakdown
    h1_krw_regime = regime_breakdown_corr(usdkrw_yoy, fwd_cell_mean, classify_krw_regime(usdkrw_yoy))
    results["H1_regime_krw"] = h1_krw_regime

    # H1 IS/OOS
    split = pd.Timestamp("2023-01-01")
    h1_is = lag_corr_with_newey_west(usdkrw_yoy[usdkrw_yoy.index < split],
                                       fwd_cell_mean[fwd_cell_mean.index < split], lags=[0, 1], freq="M")
    h1_oos = lag_corr_with_newey_west(usdkrw_yoy[usdkrw_yoy.index >= split],
                                        fwd_cell_mean[fwd_cell_mean.index >= split], lags=[0, 1], freq="M")
    results["H1_is_oos"] = {"is_lag0": h1_is.get(0), "is_lag1": h1_is.get(1),
                            "oos_lag0": h1_oos.get(0), "oos_lag1": h1_oos.get(1)}

    print("[5/6] H2 LIT → cathode lag-corr...")
    h2_lag = lag_corr_with_newey_west(lit_yoy, fwd_cathode_mean, lags=[0, 1, 3, 6], freq="M", nw_lags=3)
    results["H2_lit_to_cathode"] = {"type": "lag_corr", "lags": h2_lag,
        "note": "LIT yoy (driver) → cathode sub mean y60d. 양극재 = 247540, 003670. y60d (분기 forward)."}

    h2_lit_regime = regime_breakdown_corr(lit_yoy, fwd_cathode_mean, classify_lit_regime(lit_yoy))
    results["H2_regime_lit"] = h2_lit_regime

    # H2 IS/OOS
    split2 = pd.Timestamp("2023-01-01")
    h2_is = lag_corr_with_newey_west(lit_yoy[lit_yoy.index < split2],
                                       fwd_cathode_mean[fwd_cathode_mean.index < split2], lags=[0, 1], freq="M")
    h2_oos = lag_corr_with_newey_west(lit_yoy[lit_yoy.index >= split2],
                                        fwd_cathode_mean[fwd_cathode_mean.index >= split2], lags=[0, 1], freq="M")
    results["H2_is_oos"] = {"is_lag0": h2_is.get(0), "oos_lag0": h2_oos.get(0)}

    print("[6/6] H3 TSLA → industry, H5 KOSPI, H7 spread...")
    h3_lag = lag_corr_with_newey_west(tsla_yoy, fwd_industry_mean, lags=[0, 1, 3], freq="M", nw_lags=3)
    results["H3_tsla_to_industry"] = {"type": "lag_corr", "lags": h3_lag,
        "note": "TSLA yoy → 4종 평균 y20d. EV sentiment proxy."}

    # H7: cathode - cell spread vs LIT
    spread_60 = fwd_cathode_mean - fwd_panel_60[cell_tks].mean(axis=1)
    h7_lag = lag_corr_with_newey_west(lit_yoy, spread_60, lags=[0, 1, 3], freq="M", nw_lags=3)
    results["H7_lit_to_cathode_minus_cell_spread"] = {"type": "lag_corr", "lags": h7_lag,
        "note": "LIT yoy → (cathode mean y60d - cell mean y60d) spread."}

    # SMH (반도체 cycle spillover)
    h_smh = lag_corr_with_newey_west(smh_yoy, fwd_industry_mean, lags=[0, 1, 3], freq="M", nw_lags=3)
    results["B5_smh_to_industry"] = {"type": "lag_corr", "lags": h_smh,
        "note": "SMH yoy → 4종 평균. 반도체 cycle spillover (BMS 수요)."}

    # KOSPI baseline (control)
    h_kospi = lag_corr_with_newey_west(kospi_yoy, fwd_industry_mean, lags=[0], freq="M")
    results["control_kospi_to_industry"] = h_kospi

    # H6 Momentum 12-1 (단순화)
    # 종목별 12M 모멘텀 vs 다음 1M forward, panel cross-sec
    mom_panel = {}
    for tk in UNIVERSE:
        c = prices[tk]["Close"]
        mom_panel[tk] = (c.shift(20) / c.shift(252) - 1)  # 12-1 = t-252 ~ t-20
    mom_df = pd.DataFrame(mom_panel)
    ic_mom = panel_rank_ic_cross_sectional(mom_df, fwd_panel_20)
    results["H6_momentum_12_1"] = ic_mom
    results["H6_momentum_12_1"]["note"] = "월말 12-1 모멘텀 z-score → 다음 월 t+20d. 한국 약효 가설."

    # OOS for H6
    is_mom = mom_df[mom_df.index < pd.Timestamp("2023-01-01")]
    oos_mom = mom_df[mom_df.index >= pd.Timestamp("2023-01-01")]
    is_fwd = fwd_panel_20[fwd_panel_20.index < pd.Timestamp("2023-01-01")]
    oos_fwd = fwd_panel_20[fwd_panel_20.index >= pd.Timestamp("2023-01-01")]
    results["H6_is_oos"] = {
        "is": panel_rank_ic_cross_sectional(is_mom, is_fwd),
        "oos": panel_rank_ic_cross_sectional(oos_mom, oos_fwd),
    }

    # Cross-sectional realized vol (control)
    vol_panel = {}
    for tk in UNIVERSE:
        ret = prices[tk]["Close"].pct_change()
        vol_panel[tk] = ret.rolling(60).std() * np.sqrt(252)
    vol_df = pd.DataFrame(vol_panel)
    ic_vol = panel_rank_ic_cross_sectional(vol_df, fwd_panel_20)
    results["control_realized_vol_IC"] = ic_vol

    # ============================================================
    # 5게이트 자동 판정 (각 finding 별)
    # ============================================================
    def gate_check(metric: Dict) -> Dict:
        """5게이트 자동: N / SE / Power / FDR / OOS."""
        out = {}
        # gate 1: N ≥ 24
        n = metric.get("n_months", metric.get("n", 0))
        out["g1_n_pass"] = bool(n >= 24)
        # gate 2: SE CI 0 비포함 (Rank-IC 양식)
        ci_low = metric.get("ci95_low")
        ci_high = metric.get("ci95_high")
        if ci_low is not None and ci_high is not None and not np.isnan(ci_low) and not np.isnan(ci_high):
            out["g2_se_pass"] = bool((ci_low > 0) or (ci_high < 0))
        else:
            # lag_corr 양식 — p_value 사용
            p = metric.get("p_value")
            out["g2_se_pass"] = bool(p is not None and not np.isnan(p) and p < 0.05)
        # gate 3: Power MDE > 0.05 (n>=24 일 때 detectable)
        # MDE for Spearman ~ 2.8 / sqrt(n) (rule of thumb α=0.05 power=0.80)
        if n >= 24:
            mde = 2.8 / np.sqrt(n)
            out["g3_power_mde"] = float(mde)
            out["g3_power_pass"] = bool(mde < 0.50)
        else:
            out["g3_power_pass"] = False
        # gate 4: FDR — 본 분석 7 hypothesis, BH q < 0.10 → 단발 p < 0.10/7 ≈ 0.014 임계 (conservative)
        p = metric.get("p_value")
        if p is not None and not np.isnan(p):
            out["g4_fdr_pass"] = bool(p < 0.10 / 7)  # Bonferroni (conservative FDR upper bound)
        else:
            out["g4_fdr_pass"] = None  # not applicable
        # gate 5: OOS — separate check (caller)
        out["g5_oos_pass"] = None  # filled by caller
        return out

    gates = {}
    # H1 cell USDKRW: lag 0
    h1_metric = results["H1_usdkrw_to_cell"]["lags"][0]
    h1_gates = gate_check(h1_metric)
    h1_is_corr = results["H1_is_oos"]["is_lag0"].get("corr", np.nan) if results["H1_is_oos"]["is_lag0"] else np.nan
    h1_oos_corr = results["H1_is_oos"]["oos_lag0"].get("corr", np.nan) if results["H1_is_oos"]["oos_lag0"] else np.nan
    if not np.isnan(h1_is_corr) and abs(h1_is_corr) > 0.01:
        h1_gates["g5_oos_ratio"] = abs(h1_oos_corr / h1_is_corr) if not np.isnan(h1_oos_corr) else None
        h1_gates["g5_oos_pass"] = bool(h1_gates["g5_oos_ratio"] is not None and h1_gates["g5_oos_ratio"] >= 0.5 and np.sign(h1_is_corr) == np.sign(h1_oos_corr))
    gates["H1"] = h1_gates

    # H2 lag 1 (cathode 양극재 typically 1Q lag)
    h2_metric = results["H2_lit_to_cathode"]["lags"][1]
    h2_gates = gate_check(h2_metric)
    h2_is_corr = results["H2_is_oos"]["is_lag0"].get("corr", np.nan) if results["H2_is_oos"]["is_lag0"] else np.nan
    h2_oos_corr = results["H2_is_oos"]["oos_lag0"].get("corr", np.nan) if results["H2_is_oos"]["oos_lag0"] else np.nan
    if not np.isnan(h2_is_corr) and abs(h2_is_corr) > 0.01:
        h2_gates["g5_oos_ratio"] = abs(h2_oos_corr / h2_is_corr) if not np.isnan(h2_oos_corr) else None
        h2_gates["g5_oos_pass"] = bool(h2_gates["g5_oos_ratio"] is not None and h2_gates["g5_oos_ratio"] >= 0.5 and np.sign(h2_is_corr) == np.sign(h2_oos_corr))
    gates["H2"] = h2_gates

    # H3 TSLA lag 0
    h3_metric = results["H3_tsla_to_industry"]["lags"][0]
    gates["H3"] = gate_check(h3_metric)

    # H6 Momentum
    gates["H6"] = gate_check(ic_mom)
    is_ic_mean = results["H6_is_oos"]["is"].get("ic_mean", np.nan)
    oos_ic_mean = results["H6_is_oos"]["oos"].get("ic_mean", np.nan)
    if not np.isnan(is_ic_mean) and abs(is_ic_mean) > 0.01:
        gates["H6"]["g5_oos_ratio"] = abs(oos_ic_mean / is_ic_mean) if not np.isnan(oos_ic_mean) else None
        gates["H6"]["g5_oos_pass"] = bool(gates["H6"]["g5_oos_ratio"] is not None and gates["H6"]["g5_oos_ratio"] >= 0.5 and np.sign(is_ic_mean) == np.sign(oos_ic_mean))

    # H7 spread
    h7_metric = results["H7_lit_to_cathode_minus_cell_spread"]["lags"][0]
    gates["H7"] = gate_check(h7_metric)

    # B5 SMH
    b5_metric = results["B5_smh_to_industry"]["lags"][0]
    gates["B5"] = gate_check(b5_metric)

    results["gate_check"] = gates

    # Save
    out_path = ROOT / "validation-metrics.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"Saved: {out_path}")
    return results


if __name__ == "__main__":
    res = run_all()
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    def fmt(d, key="corr"):
        v = d.get(key)
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "n/a"
        return f"{v:+.3f}"

    h1 = res["H1_usdkrw_to_cell"]["lags"]
    print(f"H1 USDKRW→cell  lag0 ρ={fmt(h1[0])} p={fmt(h1[0],'p_value')} n={h1[0]['n']}")
    print(f"H1 USDKRW→cell  lag1 ρ={fmt(h1[1])} p={fmt(h1[1],'p_value')} n={h1[1]['n']}")
    print(f"  IS lag0 ρ={fmt(res['H1_is_oos']['is_lag0'])} OOS lag0 ρ={fmt(res['H1_is_oos']['oos_lag0'])}")

    h2 = res["H2_lit_to_cathode"]["lags"]
    print(f"H2 LIT→cathode  lag0 ρ={fmt(h2[0])} p={fmt(h2[0],'p_value')} n={h2[0]['n']}")
    print(f"H2 LIT→cathode  lag1 ρ={fmt(h2[1])} p={fmt(h2[1],'p_value')} n={h2[1]['n']}")
    print(f"H2 LIT→cathode  lag3 ρ={fmt(h2[3])} p={fmt(h2[3],'p_value')} n={h2[3]['n']}")
    print(f"  IS lag0 ρ={fmt(res['H2_is_oos']['is_lag0'])} OOS lag0 ρ={fmt(res['H2_is_oos']['oos_lag0'])}")

    h3 = res["H3_tsla_to_industry"]["lags"]
    print(f"H3 TSLA→industry lag0 ρ={fmt(h3[0])} p={fmt(h3[0],'p_value')} n={h3[0]['n']}")

    h7 = res["H7_lit_to_cathode_minus_cell_spread"]["lags"]
    print(f"H7 LIT→(cathode-cell) lag0 ρ={fmt(h7[0])} p={fmt(h7[0],'p_value')} n={h7[0]['n']}")

    b5 = res["B5_smh_to_industry"]["lags"]
    print(f"B5 SMH→industry lag0 ρ={fmt(b5[0])} p={fmt(b5[0],'p_value')} n={b5[0]['n']}")

    mom = res["H6_momentum_12_1"]
    print(f"H6 Mom 12-1 IC={mom['ic_mean']:+.3f} t={mom['t_stat']:+.2f} n_months={mom['n_months']}")
    print(f"  IS IC={res['H6_is_oos']['is']['ic_mean']:+.3f} OOS IC={res['H6_is_oos']['oos']['ic_mean']:+.3f}")

    vol = res["control_realized_vol_IC"]
    print(f"control RealVol IC={vol['ic_mean']:+.3f} t={vol['t_stat']:+.2f} n_months={vol['n_months']}")

    print("\nRegime breakdown (H1 KRW):")
    for reg, m in res["H1_regime_krw"].items():
        if m.get("verdict") != "INSUFFICIENT":
            print(f"  {reg}: ρ={m.get('corr', np.nan):+.3f} n={m.get('n', 0)} p={m.get('p_value', np.nan):+.3f}")

    print("\nRegime breakdown (H2 LIT):")
    for reg, m in res["H2_regime_lit"].items():
        if m.get("verdict") != "INSUFFICIENT":
            print(f"  {reg}: ρ={m.get('corr', np.nan):+.3f} n={m.get('n', 0)} p={m.get('p_value', np.nan):+.3f}")

    print("\nGate check (★ 5게이트):")
    for hid, g in res["gate_check"].items():
        passes = [k for k, v in g.items() if k.startswith("g") and v == True]
        fails = [k for k, v in g.items() if k.startswith("g") and v == False]
        print(f"  {hid}: pass={passes} fail={fails}")
