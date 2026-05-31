"""run_neutralized.py — factor-neutralized IC (frame §M5, J축).

toraniko 한국 KOSPI 적용 어려움 → numpy/pandas Fama-French style fallback.

방법 (단순): KOSPI return (market) + USDKRW yoy (FX factor) + SMH yoy (sector spillover)
를 OLS로 회귀해 종목 residual return 추출 → residual 에 대한 IC 측정.

이 산출의 목적 = raw vs neutralized IC 둘 다 보고 (frame J축).
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

UNIVERSE = ["373220", "006400", "247540", "003670"]
CELL = ["373220", "006400"]
CATHODE = ["247540", "003670"]


def load_data():
    prices = {tk: pd.read_parquet(DATA / f"{tk}.parquet") for tk in UNIVERSE}
    macro = pd.read_parquet(DATA / "macro.parquet")
    return prices, macro


def compute_residual_returns(prices, macro):
    """월간 return 회귀: r_i = α + β_m·KOSPI_m + β_fx·dlnFX_m + β_smh·SMH_m + ε."""
    # 월말 종가 → 월간 return
    out = {}
    macro_m = macro.resample("M").last()
    kospi_m = macro_m["KOSPI"].pct_change()
    usdkrw_m = macro_m["USDKRW"].apply(np.log).diff()
    smh_m = macro_m["SMH"].pct_change()
    lit_m = macro_m["LIT"].pct_change()

    factors = pd.concat([kospi_m, usdkrw_m, smh_m], axis=1, keys=["KOSPI", "FX", "SMH"]).dropna()

    residuals = {}
    raw_returns = {}
    for tk in UNIVERSE:
        c = prices[tk]["Close"].resample("M").last()
        ret = c.pct_change()
        df = pd.concat([ret.rename("r"), factors], axis=1).dropna()
        if len(df) < 24:
            continue
        # OLS via numpy
        X = np.column_stack([np.ones(len(df)), df["KOSPI"], df["FX"], df["SMH"]])
        y = df["r"].values
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        y_hat = X @ beta
        resid = y - y_hat
        residuals[tk] = pd.Series(resid, index=df.index)
        raw_returns[tk] = df["r"]

    return pd.DataFrame(residuals), pd.DataFrame(raw_returns), factors, lit_m


def panel_lag_corr(driver: pd.Series, panel_returns: pd.DataFrame, lags=[0, 1, 3]):
    """panel mean에 대한 lag-corr."""
    panel_mean = panel_returns.mean(axis=1)
    out = {}
    for L in lags:
        x = driver.shift(L)
        df = pd.concat([x, panel_mean], axis=1, keys=["x", "y"]).dropna()
        if len(df) < 12:
            out[L] = {"corr": np.nan, "n": len(df), "p_value": np.nan}
            continue
        rho, p = stats.spearmanr(df["x"], df["y"])
        out[L] = {"corr": float(rho), "n": int(len(df)), "p_value": float(p)}
    return out


def main():
    print("[1/3] Loading data...")
    prices, macro = load_data()

    print("[2/3] Computing residuals (factor-neutralized monthly returns)...")
    residuals, raw_returns, factors, lit_m = compute_residual_returns(prices, macro)
    print(f"  Residual panel shape: {residuals.shape}")

    print("[3/3] LIT lag-corr (raw vs neutralized)...")
    out = {"meta": {"note": "factor neutralization via KOSPI + FX + SMH OLS residuals"}}

    # H2 LIT → cathode (가장 강력한 finding)
    raw_cathode = panel_lag_corr(lit_m, raw_returns[CATHODE], lags=[0, 1, 3])
    neutr_cathode = panel_lag_corr(lit_m, residuals[CATHODE], lags=[0, 1, 3])
    out["H2_cathode_raw"] = raw_cathode
    out["H2_cathode_neutralized"] = neutr_cathode

    # H1 USDKRW → cell
    fx_m = factors["FX"]
    raw_cell = panel_lag_corr(fx_m, raw_returns[CELL], lags=[0, 1])
    neutr_cell = panel_lag_corr(fx_m, residuals[CELL], lags=[0, 1])
    out["H1_cell_raw"] = raw_cell
    out["H1_cell_neutralized"] = neutr_cell

    # H7 cathode - cell spread (LIT)
    spread_raw = raw_returns[CATHODE].mean(axis=1) - raw_returns[CELL].mean(axis=1)
    spread_neutr = residuals[CATHODE].mean(axis=1) - residuals[CELL].mean(axis=1)
    h7_raw = {}
    h7_neutr = {}
    for L in [0, 1, 3]:
        x = lit_m.shift(L)
        df = pd.concat([x, spread_raw], axis=1).dropna()
        if len(df) >= 12:
            rho, p = stats.spearmanr(df.iloc[:, 0], df.iloc[:, 1])
            h7_raw[L] = {"corr": float(rho), "n": int(len(df)), "p_value": float(p)}
        df2 = pd.concat([x, spread_neutr], axis=1).dropna()
        if len(df2) >= 12:
            rho, p = stats.spearmanr(df2.iloc[:, 0], df2.iloc[:, 1])
            h7_neutr[L] = {"corr": float(rho), "n": int(len(df2)), "p_value": float(p)}
    out["H7_spread_raw"] = h7_raw
    out["H7_spread_neutralized"] = h7_neutr

    # Save
    out_path = ROOT / "validation-neutralized.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print(f"Saved: {out_path}")

    # Print summary
    def fmt(d):
        if not d:
            return "n/a"
        return f"ρ={d.get('corr', float('nan')):+.3f} p={d.get('p_value', float('nan')):+.3f} n={d.get('n', 0)}"

    print("\nH2 LIT → cathode panel mean:")
    for L in [0, 1, 3]:
        print(f"  lag{L} raw: {fmt(raw_cathode.get(L))}")
        print(f"  lag{L} neutralized: {fmt(neutr_cathode.get(L))}")

    print("\nH7 LIT → (cathode - cell) spread:")
    for L in [0, 1, 3]:
        print(f"  lag{L} raw: {fmt(h7_raw.get(L))}")
        print(f"  lag{L} neutralized: {fmt(h7_neutr.get(L))}")

    print("\nH1 FX → cell panel mean (monthly dlnFX):")
    for L in [0, 1]:
        print(f"  lag{L} raw: {fmt(raw_cell.get(L))}")
        print(f"  lag{L} neutralized: {fmt(neutr_cell.get(L))}")


if __name__ == "__main__":
    main()
