"""H3 stablecoin net creation lead-lag -- 실데이터 검증.

가설: stablecoin net creation (Δsupply z-score) > 1 -> 7~30d 가격 상승
반증조건: rolling Granger p > 0.05 OR CCF lag-dominant 역전 (가격 -> supply 역인과)
- level 사용 금지, growth (Δsupply) 만
- ADF stationarity 선행
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import pandas as pd
from scipy import stats
from lib_common import load_stablecoin, load_btc_klines, rank_ic, block_bootstrap_ci

OUT = Path(__file__).resolve().parent.parent / "raw" / "validation-h3-stablecoin.md"

def main():
    sc = load_stablecoin()
    klines = load_btc_klines()
    df = klines.merge(sc, on="date", how="inner")
    df["log_ret_7d_fwd"] = np.log(df["close"].shift(-7)/df["close"])
    df["log_ret_30d_fwd"] = np.log(df["close"].shift(-30)/df["close"])
    df["log_ret_90d_fwd"] = np.log(df["close"].shift(-90)/df["close"])
    df["log_ret_1d"] = np.log(df["close"]/df["close"].shift(1))
    # net creation = daily diff of supply
    df["net_creation"] = df["total_supply"].diff()
    # growth = log diff
    df["log_supply"] = np.log(df["total_supply"])
    df["supply_log_growth_1d"] = df["log_supply"].diff()
    df["supply_log_growth_7d"] = df["log_supply"].diff(7)

    lines = []
    def w(s=""): lines.append(s)

    w("# H3 Stablecoin net creation lead-lag -- 실데이터 검증")
    w()
    w(f"as_of: {pd.Timestamp.utcnow().isoformat()}")
    w(f"stablecoin: DefiLlama total supply, n={len(sc)}, {sc['date'].min().date()} ~ {sc['date'].max().date()}")
    w(f"BTC klines: Binance daily, merged n={len(df)}")
    w()

    # ===== 1. ADF stationarity =====
    w("## 1. ADF stationarity 선행")
    from statsmodels.tsa.stattools import adfuller
    series = {
        "log_supply (level)": df["log_supply"].dropna(),
        "supply_log_growth_1d": df["supply_log_growth_1d"].dropna(),
        "supply_log_growth_7d": df["supply_log_growth_7d"].dropna(),
        "log_close (level)": np.log(df["close"]).dropna(),
        "log_ret_1d (BTC)": df["log_ret_1d"].dropna(),
    }
    for name, s in series.items():
        try:
            adf = adfuller(s, autolag="AIC")
            w(f"- {name}: ADF stat={adf[0]:.3f}, p={adf[1]:.4f}, n={len(s)} -> {'STATIONARY' if adf[1]<0.05 else 'non-stationary'}")
        except Exception as e:
            w(f"- {name}: ADF FAIL ({e})")
    w()

    # ===== 2. Lead-lag Cross-correlation (X=supply_growth, Y=log_ret) =====
    w("## 2. Cross-correlation function (CCF) -- supply_growth vs BTC log_ret")
    valid = df[["supply_log_growth_7d", "log_ret_1d"]].dropna()
    if len(valid) > 100:
        from statsmodels.tsa.stattools import ccf
        try:
            x = valid["supply_log_growth_7d"].values
            y = valid["log_ret_1d"].values
            # x leads y at positive lag
            ccf_lead = ccf(y, x, adjusted=True)[:60]
            ccf_lag  = ccf(x, y, adjusted=True)[:60]
            # 양의 lag (x->y) 강함 = stablecoin 가 BTC 선행
            w(f"- supply 가 BTC 선행 (positive lag X->Y):")
            for k in [1, 3, 7, 14, 30]:
                w(f"  - lag {k}d: corr={ccf_lead[k]:+.4f}")
            w(f"- BTC 가 supply 선행 (X<-Y, 역인과 정황):")
            for k in [1, 3, 7, 14, 30]:
                w(f"  - lag {k}d: corr={ccf_lag[k]:+.4f}")
            # peak detection
            lead_peak = int(np.argmax(np.abs(ccf_lead[:30])))
            lag_peak = int(np.argmax(np.abs(ccf_lag[:30])))
            w(f"- supply->BTC peak abs lag = {lead_peak}d, corr={ccf_lead[lead_peak]:+.4f}")
            w(f"- BTC->supply peak abs lag = {lag_peak}d, corr={ccf_lag[lag_peak]:+.4f}")
            w(f"- 역인과 위험: {'HIGH (BTC->supply peak 이 더 강)' if abs(ccf_lag[lag_peak]) > abs(ccf_lead[lead_peak]) else 'LOW (supply->BTC peak 우세)'}")
        except Exception as e:
            w(f"- CCF FAIL ({e})")
    w()

    # ===== 3. Granger bidirectional =====
    w("## 3. Bidirectional Granger causality (growth series, maxlag=14)")
    valid = df[["supply_log_growth_7d", "log_ret_1d"]].dropna()
    if len(valid) > 200:
        from statsmodels.tsa.stattools import grangercausalitytests
        # silent
        import io
        import contextlib
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                g_x_to_y = grangercausalitytests(valid[["log_ret_1d", "supply_log_growth_7d"]].values, maxlag=14)
                g_y_to_x = grangercausalitytests(valid[["supply_log_growth_7d", "log_ret_1d"]].values, maxlag=14)
            w(f"- supply growth -> BTC ret (F-test p-values by lag):")
            for lag in [1, 7, 14]:
                p = g_x_to_y[lag][0]["ssr_ftest"][1]
                w(f"  - lag {lag}d: p={p:.4f}")
            w(f"- BTC ret -> supply growth (F-test p-values by lag, 역인과):")
            for lag in [1, 7, 14]:
                p = g_y_to_x[lag][0]["ssr_ftest"][1]
                w(f"  - lag {lag}d: p={p:.4f}")
        except Exception as e:
            w(f"- Granger FAIL: {e}")
    w()

    # ===== 4. Rank-IC supply growth -> fwd ret =====
    w("## 4. Rank-IC supply_log_growth_7d -> fwd_{7,30,90}d")
    for h_col in ["log_ret_7d_fwd", "log_ret_30d_fwd", "log_ret_90d_fwd"]:
        rho, n = rank_ic(df["supply_log_growth_7d"], df[h_col])
        w(f"- {h_col}: Rank-IC = {rho:+.4f}, n={n}")
        valid = df[["supply_log_growth_7d", h_col]].dropna()
        if len(valid) > 200:
            def stat_rho(idx):
                idx = np.asarray(idx, dtype=int) % len(valid)
                return stats.spearmanr(valid["supply_log_growth_7d"].values[idx], valid[h_col].values[idx])[0]
            lo, mu, hi = block_bootstrap_ci(np.arange(len(valid)).astype(float), stat_rho, n_boot=300, block_len=30)
            w(f"  block-bootstrap 95% CI = ({lo:+.4f}, {hi:+.4f})")
    w()

    # ===== 5. 가설 판정 =====
    w("## 5. 가설 판정")
    w("- 1장: level 비정상 + growth 정상 확인 (필수 stationarity)")
    w("- 2장 CCF peak: supply->BTC peak 이 BTC->supply peak 보다 절대값 큰가? 작으면 역인과 정황")
    w("- 3장 Granger: supply->BTC F-test 유의 + BTC->supply 미유의 = lead 확인 / 둘 다 유의 = reflexive")
    w("- 4장 Rank-IC: 7/30d 양 + CI 0 미포함 = direction.md H3 가설 1차 검증")
    w()
    w("## 6. 미해결 의문")
    w("- DefiLlama total supply 가 DeFi 담보·OTC·bridge 포함 -> 진짜 'dry powder' 아님")
    w("- 거래소向 stablecoin inflow 가 더 깨끗하지만 무료 단위 불가")
    w("- 2020 DeFi summer / 2022 UST 붕괴 같은 regime break -> 단일 ADF/Granger 안정성 의심")
    w("- 우리 검증 = 양방향 Granger, 일변량 level 차분만 (multivariate VECM 추가 권고)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] H3 -> {OUT}")

if __name__ == "__main__":
    main()
