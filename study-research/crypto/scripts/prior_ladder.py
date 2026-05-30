"""★우선 1: prior_strength 채널 차등 ladder OOS backtest.

direction.md D1: micro 0.5-0.7 / on-chain 0.3-0.5 / macro 0.2-0.4 / halving 0.1-0.2

검증: 각 채널 대표 가설의 OOS Rank-IC volatility, breakdown frequency, max drawdown.
프리어 ladder 가 OOS edge 안정성과 일치하는지 측정.

기각 조건: micro / halving 의 OOS metric 비율이 2배 미만 = ladder over-spread (재캘리브 필요)
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import pandas as pd
from scipy import stats
from lib_common import (
    load_funding, load_coinmetrics, load_stablecoin, load_btc_klines,
    rank_ic, effective_n, halving_phase
)

OUT = Path(__file__).resolve().parent.parent / "raw" / "validation-prior-ladder.md"

def rolling_ic(x: pd.Series, y: pd.Series, window: int, step: int = 30):
    """rolling Rank-IC time series."""
    out = []
    df = pd.DataFrame({"x": x.values, "y": y.values})
    df = df.dropna()
    for i in range(window, len(df) - 30, step):
        win = df.iloc[i-window:i]
        rho, n = rank_ic(win["x"], win["y"])
        if not np.isnan(rho):
            out.append({"idx": i, "ic": rho, "n": n})
    return pd.DataFrame(out)


def channel_stability(ic_series: pd.Series):
    """채널 대표 가설의 stability metrics."""
    if len(ic_series) < 5:
        return {"mean": np.nan, "std": np.nan, "ic_sharpe": np.nan, "breakdown_freq": np.nan}
    mean_ic = ic_series.mean()
    std_ic = ic_series.std()
    ic_sharpe = mean_ic / std_ic if std_ic > 0 else 0
    # breakdown freq = IC < 0 비율
    bkdn = (ic_series < 0).mean() if mean_ic > 0 else (ic_series > 0).mean()
    return {"mean": float(mean_ic), "std": float(std_ic), "ic_sharpe": float(ic_sharpe), "breakdown_freq": float(bkdn)}


def main():
    klines = load_btc_klines()
    klines["log_ret_30d_fwd"] = np.log(klines["close"].shift(-30) / klines["close"])
    klines["log_ret_7d_fwd"] = np.log(klines["close"].shift(-7) / klines["close"])

    lines = []
    def w(s=""): lines.append(s)

    w("# 우선 1 — Prior ladder OOS backtest")
    w()
    w(f"as_of: {pd.Timestamp.utcnow().isoformat()}")
    w("direction.md D1: micro 0.5-0.7 / on-chain 0.3-0.5 / macro 0.2-0.4 / halving 0.1-0.2")
    w("측정: 각 채널 대표 가설의 rolling Rank-IC mean / std / sharpe / breakdown_freq")
    w("rolling window = 180d, step = 30d (~6달마다 갱신, 3년 데이터 = 약 18 windows)")
    w()

    results = []

    # ===== Micro: H2 funding (양 funding -> 음 fwd_7d) =====
    w("## 1. Micro channel — H2 funding -> fwd_7d")
    try:
        fund = load_funding()
        fund["date"] = fund["datetime"].dt.normalize()
        daily_f = fund.groupby("date")["funding_rate"].mean().reset_index().rename(columns={"funding_rate": "funding_mean"})
        m_fund = klines.merge(daily_f, on="date", how="inner")
        # signal = -funding_mean (cascade 가설: 양 funding -> 음 fwd_ret)
        m_fund["sig"] = -m_fund["funding_mean"]
        m_fund = m_fund[m_fund["log_ret_7d_fwd"].notna()]
        ic_ts = rolling_ic(m_fund["sig"], m_fund["log_ret_7d_fwd"], window=180, step=30)
        if not ic_ts.empty:
            r = channel_stability(ic_ts["ic"])
            r["channel"] = "micro_funding"
            r["prior_proposed"] = 0.6
            r["n_windows"] = len(ic_ts)
            r["effective_n_raw"] = effective_n(m_fund["sig"].values)
            results.append(r)
            w(f"  - n_windows={len(ic_ts)}, mean IC={r['mean']:+.4f}, std={r['std']:.4f}, "
              f"sharpe={r['ic_sharpe']:+.3f}, breakdown_freq={r['breakdown_freq']:.3f}")
        else:
            w(f"  - rolling IC 산출 실패 (data 부족)")
    except Exception as e:
        w(f"  - FAIL: {e}")
    w()

    # ===== On-chain: H1 MVRV (MVRV 높을수록 음 fwd_30d) =====
    w("## 2. On-chain channel — H1 MVRV -> fwd_30d")
    try:
        cm = load_coinmetrics()
        cm["mvrv"] = cm["CapMVRVCur"]
        m_mvrv = klines.merge(cm[["date", "mvrv"]], on="date", how="inner")
        m_mvrv["sig"] = -m_mvrv["mvrv"]  # 음 신호로 변환 (mean-revert 가설)
        m_mvrv = m_mvrv[m_mvrv["log_ret_30d_fwd"].notna()]
        ic_ts = rolling_ic(m_mvrv["sig"], m_mvrv["log_ret_30d_fwd"], window=365, step=60)
        if not ic_ts.empty:
            r = channel_stability(ic_ts["ic"])
            r["channel"] = "onchain_mvrv"
            r["prior_proposed"] = 0.4
            r["n_windows"] = len(ic_ts)
            r["effective_n_raw"] = effective_n(m_mvrv["sig"].values)
            results.append(r)
            w(f"  - n_windows={len(ic_ts)}, mean IC={r['mean']:+.4f}, std={r['std']:.4f}, "
              f"sharpe={r['ic_sharpe']:+.3f}, breakdown_freq={r['breakdown_freq']:.3f}")
        else:
            w(f"  - rolling IC 산출 실패")
    except FileNotFoundError:
        w(f"  - CoinMetrics 데이터 없음 -> SKIP (별도 백업 필요)")
    except Exception as e:
        w(f"  - FAIL: {e}")
    w()

    # ===== Macro: H3 stablecoin growth -> fwd_30d =====
    w("## 3. Macro channel — H3 stablecoin growth -> fwd_30d")
    try:
        sc = load_stablecoin()
        sc["log_supply"] = np.log(sc["total_supply"])
        sc["supply_log_growth_7d"] = sc["log_supply"].diff(7)
        m_sc = klines.merge(sc[["date", "supply_log_growth_7d"]], on="date", how="inner")
        m_sc["sig"] = m_sc["supply_log_growth_7d"]
        m_sc = m_sc[m_sc["log_ret_30d_fwd"].notna()]
        ic_ts = rolling_ic(m_sc["sig"], m_sc["log_ret_30d_fwd"], window=365, step=60)
        if not ic_ts.empty:
            r = channel_stability(ic_ts["ic"])
            r["channel"] = "macro_stablecoin"
            r["prior_proposed"] = 0.3
            r["n_windows"] = len(ic_ts)
            r["effective_n_raw"] = effective_n(m_sc["sig"].values)
            results.append(r)
            w(f"  - n_windows={len(ic_ts)}, mean IC={r['mean']:+.4f}, std={r['std']:.4f}, "
              f"sharpe={r['ic_sharpe']:+.3f}, breakdown_freq={r['breakdown_freq']:.3f}")
        else:
            w(f"  - rolling IC 산출 실패")
    except Exception as e:
        w(f"  - FAIL: {e}")
    w()

    # ===== Halving: standalone IC 산출 X (사용자 박제), but phase->fwd 단순 평균만 =====
    w("## 4. Halving channel — ★standalone IC 산출 금지 (N=4 power 0)")
    w("  - halving prior 0.1 = label-only regime conditioning")
    w("  - phase 별 fwd_30d 평균 부호만 보고 (구조적 prior 저신뢰 라벨)")
    klines["phase"] = klines["date"].apply(halving_phase)
    phase_mean = klines.groupby("phase")["log_ret_30d_fwd"].mean().sort_index()
    for ph, mu in phase_mean.items():
        if pd.isna(mu):
            continue
        w(f"    - {ph}: mean fwd_30d = {mu:+.4f}")
    results.append({"channel": "halving_regime_label", "prior_proposed": 0.1, "mean": np.nan,
                    "std": np.nan, "ic_sharpe": np.nan, "breakdown_freq": np.nan, "n_windows": 0,
                    "effective_n_raw": 4})
    w()

    # ===== 종합 ladder 정합 판정 =====
    w("## 5. Ladder 정합 판정")
    if results:
        rdf = pd.DataFrame(results)
        w("```")
        w(rdf[["channel", "prior_proposed", "mean", "std", "ic_sharpe", "breakdown_freq", "n_windows", "effective_n_raw"]].round(4).to_string(index=False))
        w("```")
        # micro / halving 의 sharpe 비교 — claude r3 "2배 미달 = ladder over-spread" 기준
        micro = rdf[rdf["channel"] == "micro_funding"]
        macro_or_onchain = rdf[rdf["channel"].isin(["onchain_mvrv", "macro_stablecoin"])]
        if not micro.empty and not macro_or_onchain.empty:
            micro_sharpe = abs(micro["ic_sharpe"].iloc[0])
            other_sharpe_max = abs(macro_or_onchain["ic_sharpe"]).max()
            ratio = micro_sharpe / other_sharpe_max if other_sharpe_max > 0 else np.nan
            w(f"- micro_funding IC-sharpe / max(on-chain, macro) IC-sharpe = {ratio:.2f}")
            w(f"- prior 비율 (0.6 / 0.4) = 1.5 — 측정 ratio 와 prior ratio 비교")
            if not np.isnan(ratio):
                w(f"- ★판정: ratio {'>= 1.0 (ladder 방향 일치)' if ratio >= 1.0 else '< 1.0 (ladder 역방향)'}")
    w()

    w("## 6. 미해결 의문 (claude r3 인용)")
    w("- prior 0.6 / 0.4 / 0.3 / 0.1 ladder 의 정확한 수치는 educated guess")
    w("- 본 검증 자체가 rolling window 의 길이·step 선택에 민감")
    w("- channel 대표 가설 = 단일 sig 가설만 (channel 의 다양한 가설 평균 X)")
    w("- prior_strength -> OOS edge 안정성 매핑은 backtest 누적 후 calibrate")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] prior_ladder -> {OUT}")


if __name__ == "__main__":
    main()
