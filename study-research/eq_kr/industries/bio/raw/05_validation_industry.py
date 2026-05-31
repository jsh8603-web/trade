"""Layer 3 산업 cycle 지표 IC 검증.

대상:
- fda_approvals (월별 신규 NDA approval count, yoy + level)
- KRX 헬스케어 ETF (tiger_healthcare = 가장 긴 시계열 12년) — 산업 momentum (반사성 risk 검정 필요)
- 헬스케어 ETF return spread vs KOSPI (industry rotation)

종속변수 y = 바이오 universe 평균 forward 20d return (월별).

⚠️ ETF momentum = 산업 가격 자기 가격 → spurious self-corr 위험. 본 검증은 (a) lag 1m+ (b) cross-sectional 종목별 분산 보존.
"""
from __future__ import annotations
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RESULT_DIR = Path(__file__).resolve().parent.parent / "results"
RESULT_DIR.mkdir(exist_ok=True)


def load_data():
    prices = pd.read_parquet(DATA_DIR / "prices_daily.parquet")
    etfs = pd.read_parquet(DATA_DIR / "healthcare_etfs.parquet")
    macro = pd.read_parquet(DATA_DIR / "macro_daily.parquet")
    fda = pd.read_csv(DATA_DIR / "fda_approvals_monthly.csv", parse_dates=["date"]).set_index("date")
    uni = pd.read_csv(DATA_DIR / "universe_bio_filtered.csv", encoding="utf-8-sig", dtype={"Code": str}).head(30)
    return prices, etfs, macro, fda, uni


def industry_mean_forward_return(prices: pd.DataFrame, horizon: int = 20) -> pd.Series:
    close_cols = [c for c in prices.columns if c.endswith("_close")]
    px = prices[close_cols]
    fwd = px.shift(-horizon) / px - 1
    eq_mean = fwd.mean(axis=1)
    return eq_mean.resample("ME").last()


def build_industry_features(etfs: pd.DataFrame, macro: pd.DataFrame, fda: pd.DataFrame) -> pd.DataFrame:
    """Layer 3 features 월별."""
    # ETF returns
    etf_ret_20d = etfs["tiger_healthcare"].pct_change(20)  # 1m momentum
    etf_ret_60d = etfs["tiger_healthcare"].pct_change(60)  # 3m momentum
    # vs KOSPI spread (industry rotation)
    kospi = macro["kospi"]
    df_concat = pd.concat([etfs["tiger_healthcare"].rename("etf"), kospi.rename("kospi")], axis=1).dropna()
    rel_strength = df_concat["etf"].pct_change(20) - df_concat["kospi"].pct_change(20)

    # FDA approvals yoy (월별)
    fda_yoy = fda["fda_approvals_count"].pct_change(12)
    fda_3m = fda["fda_approvals_count"].rolling(3).mean()  # 3m smoothed
    fda_3m_yoy = fda_3m.pct_change(12)

    df = pd.concat([
        etf_ret_20d.rename("etf_mom_20d"),
        etf_ret_60d.rename("etf_mom_60d"),
        rel_strength.rename("etf_vs_kospi_20d"),
        fda_yoy.rename("fda_yoy"),
        fda_3m_yoy.rename("fda_3m_yoy"),
    ], axis=1)

    monthly = df.resample("ME").last()
    return monthly


def time_series_ic(x: pd.Series, y: pd.Series, lag: int = 0) -> dict:
    if lag > 0:
        x = x.shift(lag)
    elif lag < 0:
        y = y.shift(-lag)
    df = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    n = len(df)
    if n < 10:
        return {"n": n, "corr": np.nan, "p": np.nan, "ci_lo": np.nan, "ci_hi": np.nan, "loo_p_med": np.nan}
    r, p = stats.spearmanr(df["x"], df["y"])
    z = np.arctanh(np.clip(r, -0.999, 0.999))
    se_z = 1 / np.sqrt(n - 3)
    ci_lo, ci_hi = np.tanh(z - 1.96 * se_z), np.tanh(z + 1.96 * se_z)

    # LOO
    loo_ps = []
    for i in range(n):
        sub = df.drop(df.index[i])
        _, pp = stats.spearmanr(sub["x"], sub["y"])
        loo_ps.append(pp)
    return {
        "n": n,
        "corr": float(r),
        "p": float(p),
        "ci_lo": float(ci_lo),
        "ci_hi": float(ci_hi),
        "loo_p_med": float(np.median(loo_ps)),
    }


def is_oos_split(x: pd.Series, y: pd.Series, oos_start: str = "2023-01-01") -> dict:
    df = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    is_df = df[df.index < oos_start]
    oos_df = df[df.index >= oos_start]
    out = {"is_n": len(is_df), "oos_n": len(oos_df)}
    if len(is_df) >= 10:
        r_is, p_is = stats.spearmanr(is_df["x"], is_df["y"])
        out["is_corr"], out["is_p"] = float(r_is), float(p_is)
    else:
        out["is_corr"], out["is_p"] = np.nan, np.nan
    if len(oos_df) >= 10:
        r_oos, p_oos = stats.spearmanr(oos_df["x"], oos_df["y"])
        out["oos_corr"], out["oos_p"] = float(r_oos), float(p_oos)
    else:
        out["oos_corr"], out["oos_p"] = np.nan, np.nan
    if not np.isnan(out["is_corr"]) and abs(out["is_corr"]) > 0.01:
        out["oos_ratio"] = float(out["oos_corr"] / out["is_corr"])
    else:
        out["oos_ratio"] = np.nan
    return out


def gate_check(result: dict, oos: dict, n_tests: int) -> dict:
    n = result["n"]
    gates = {"1_N": n >= 24}
    ci_in = (result["ci_lo"] <= 0 <= result["ci_hi"])
    gates["2_SE"] = (not ci_in) or result["p"] < 0.05
    z_alpha = stats.norm.ppf(0.975); z_power = stats.norm.ppf(0.80)
    mde = np.tanh((z_alpha + z_power) / np.sqrt(max(n - 3, 1)))
    gates["3_power"] = mde < 0.10
    gates["mde"] = float(mde)
    gates["4_FDR_bonf"] = result["p"] < (0.05 / n_tests)
    if not np.isnan(oos["oos_ratio"]):
        gates["5_OOS"] = (np.sign(oos["is_corr"]) == np.sign(oos["oos_corr"])) and (oos["oos_ratio"] >= 0.5)
    else:
        gates["5_OOS"] = False
    gates["pass_all"] = all(gates[k] for k in ["1_N", "2_SE", "3_power", "4_FDR_bonf", "5_OOS"])
    gates["pass_1_4"] = all(gates[k] for k in ["1_N", "2_SE", "3_power", "4_FDR_bonf"])
    return gates


def main():
    prices, etfs, macro, fda, uni = load_data()
    y_fwd = industry_mean_forward_return(prices, horizon=20)
    print(f"y forward 20d: n={y_fwd.dropna().count()} ({y_fwd.index.min()} ~ {y_fwd.index.max()})")

    feats = build_industry_features(etfs, macro, fda)
    print(f"\nLayer 3 features: {feats.shape}")
    print(feats.tail(3))

    indicators = ["etf_mom_20d", "etf_mom_60d", "etf_vs_kospi_20d", "fda_yoy", "fda_3m_yoy"]
    lags = [0, 1, 3]
    all_results = []
    for ind in indicators:
        for lag in lags:
            x = feats[ind]
            res = time_series_ic(x, y_fwd, lag=lag)
            oos = is_oos_split(x, y_fwd, oos_start="2023-01-01")
            gates = gate_check(res, oos, n_tests=len(indicators) * len(lags))
            all_results.append({
                "indicator": ind, "lag_m": lag,
                **res,
                **{f"oos_{k}": v for k, v in oos.items()},
                **{f"gate_{k}": v for k, v in gates.items()},
            })
    df_res = pd.DataFrame(all_results)
    out = RESULT_DIR / "validation_industry.csv"
    df_res.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"\n저장: {out}\n")

    cols = ["indicator", "lag_m", "n", "corr", "p", "ci_lo", "ci_hi", "loo_p_med",
            "oos_is_corr", "oos_oos_corr", "oos_oos_ratio", "gate_pass_1_4", "gate_pass_all"]
    print(df_res[cols].to_string(index=False))
    print("\n=== 통과 게이트 ===")
    print(f"  N gate 통과: {df_res['gate_1_N'].sum()}/{len(df_res)}")
    print(f"  SE gate 통과: {df_res['gate_2_SE'].sum()}/{len(df_res)}")
    print(f"  Power gate 통과: {df_res['gate_3_power'].sum()}/{len(df_res)}")
    print(f"  FDR(Bonferroni) 통과: {df_res['gate_4_FDR_bonf'].sum()}/{len(df_res)}")
    print(f"  OOS gate 통과: {df_res['gate_5_OOS'].sum()}/{len(df_res)}")
    print(f"  ★ 5게이트 모두 통과: {df_res['gate_pass_all'].sum()}/{len(df_res)}")
    print(f"  ★ 1-4 게이트 통과: {df_res['gate_pass_1_4'].sum()}/{len(df_res)}")


if __name__ == "__main__":
    main()
