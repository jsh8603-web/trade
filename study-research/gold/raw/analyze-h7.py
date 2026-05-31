"""
H7 검증 — γ 분해 + GPR quantile q90.
γ 부분: H2 의 Johansen rank=0 + EG cointegration 부정 = γ 붕괴의 극한 (H7 의 직접 confirmation).
       추가: rolling cointegration 잔차 ADF stat 시계열 — γ proxy
GPR 부분: GPR Index → Δgold quantile regression q90 vs OLS — tail-amplified 검증
입력: fred_dfii10/dtwexbgs + GLD + raw/gpr_daily.xls
산출: stdout + raw/h7_result.json + raw/h7_rolling_eg.csv
"""
import json, os
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller
from statsmodels.regression.linear_model import OLS
from statsmodels.regression.quantile_regression import QuantReg
from statsmodels.tools.tools import add_constant

RAW = os.path.dirname(os.path.abspath(__file__))

def load_fred(name, col):
    df = pd.read_csv(os.path.join(RAW, name))
    df.columns = ["date", col]
    df["date"] = pd.to_datetime(df["date"])
    df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.set_index("date").sort_index()

def load_gld():
    with open(os.path.join(RAW, "try_yahoo_v8.json"), "r", encoding="utf-8") as f:
        j = json.load(f)
    r = j["chart"]["result"][0]
    ts = r["timestamp"]; close = r["indicators"]["quote"][0]["close"]
    return pd.DataFrame({"date": pd.to_datetime(ts, unit="s").normalize(), "gold": close}).dropna().set_index("date").sort_index()

real = load_fred("fred_dfii10.csv", "real_rate")
dol  = load_fred("fred_dtwexbgs.csv", "dollar")
gld  = load_gld()
# GPR XLS load
gpr_xls = pd.read_excel(os.path.join(RAW, "gpr_daily.xls"))
gpr_xls = gpr_xls.dropna(subset=["DAY", "GPRD"])
gpr_xls["date"] = pd.to_datetime(gpr_xls["DAY"].astype(int).astype(str), format="%Y%m%d")
gpr = gpr_xls.set_index("date")[["GPRD"]].sort_index()

df = pd.concat([real, dol, gld, gpr], axis=1).loc["2010-01-01":].ffill().dropna()
df["ln_gold"] = np.log(df["gold"])
df["ln_dollar"] = np.log(df["dollar"])
print(f"[load] daily n={len(df)} range={df.index.min().date()}~{df.index.max().date()}")

# === (1) γ proxy: rolling 504d Engle-Granger 잔차 ADF stat ===
print("\n=== (1) γ proxy: rolling 504d EG 잔차 ADF stat ===")
WIN = 504  # 2 years
results = []
for i in range(WIN, len(df), 21):  # monthly sampling
    sub = df.iloc[i-WIN:i]
    X = add_constant(sub[["real_rate", "ln_dollar"]].values)
    y = sub["ln_gold"].values
    try:
        res = OLS(y, X).fit()
        adf = adfuller(res.resid, regression="n", autolag=None, maxlag=1)
        results.append({"date": sub.index[-1], "adf_stat": adf[0], "adf_p": adf[1], "r2": res.rsquared,
                       "alpha": res.params[0], "b_real": res.params[1], "c_dollar": res.params[2]})
    except Exception:
        pass
rec = pd.DataFrame(results).set_index("date")
rec.to_csv(os.path.join(RAW, "h7_rolling_eg.csv"))
periods = {"2012_19": ("2012-01-01", "2019-12-31"),
           "2020_21": ("2020-01-01", "2021-12-31"),
           "2022_26": ("2022-01-01", "2026-05-29")}
print(f"  {'period':<12} {'n':>5} {'ADF stat':>12} {'ADF p':>10} {'R²':>8}")
for p, (s, e) in periods.items():
    sub = rec.loc[s:e]
    print(f"  {p:<12} {len(sub):>5} {sub['adf_stat'].mean():>12.3f} {sub['adf_p'].mean():>10.4f} {sub['r2'].mean():>8.3f}")
adf_pre = rec.loc["2012-01-01":"2021-12-31", "adf_stat"]
adf_post = rec.loc["2022-01-01":, "adf_stat"]
print(f"  pre-2022 mean ADF stat: {adf_pre.mean():.3f} (cv5% Engle-Granger no-coint = ~-3.34, more negative = stronger reject H0=non-stationary = stronger cointegration)")
print(f"  post-2022 mean ADF stat: {adf_post.mean():.3f}")
gamma_decline_pct = 100 * (adf_post.mean() - adf_pre.mean()) / abs(adf_pre.mean()) if adf_pre.mean() != 0 else 0
print(f"  → γ proxy change: pre-2022 ADF {adf_pre.mean():.3f} → post-2022 {adf_post.mean():.3f} (Δ={adf_post.mean() - adf_pre.mean():+.3f})")
print(f"  → H7 γ flavor: cointegration {'점진 붕괴 (γ→0)' if adf_post.mean() > adf_pre.mean() + 0.5 else '유지'}")

# === (2) GPR quantile regression q90 vs OLS ===
print("\n=== (2) GPR Quantile Regression q90 vs OLS ===")
chg = pd.DataFrame(index=df.index)
chg["d_real_bp"] = df["real_rate"].diff() * 100
chg["r_dollar"] = np.log(df["dollar"]).diff()
chg["r_gold"] = np.log(df["gold"]).diff()
chg["gpr_level"] = df["GPRD"]
chg["d_gpr"] = df["GPRD"].diff()
chg = chg.dropna()

# 모델: r_gold ~ Δreal + Δdollar + ΔGPR (force_include 4)
# OLS
y = chg["r_gold"].values
X = chg[["d_real_bp", "r_dollar", "d_gpr"]].values
Xc = add_constant(X)
ols = OLS(y, Xc).fit()
print(f"  OLS: r_gold ~ Δreal + Δdollar + ΔGPR")
print(f"    α={ols.params[0]:+.5f} b_real={ols.params[1]:+.6f} c_dollar={ols.params[2]:+.4f} d_gpr={ols.params[3]:+.6f} (SE={ols.bse[3]:.6f})")
print(f"    R²={ols.rsquared:.4f}")
ols_gpr_t = ols.params[3] / ols.bse[3]
ols_gpr_pval = ols.pvalues[3]
print(f"    GPR β t-stat = {ols_gpr_t:.3f}  p={ols_gpr_pval:.4f}")

# Quantile q=0.90 (upper tail of gold returns)
qr90 = QuantReg(y, Xc).fit(q=0.90)
print(f"\n  QuantReg q=0.90 (gold 상위 10% return tail):")
print(f"    α={qr90.params[0]:+.5f} b_real={qr90.params[1]:+.6f} c_dollar={qr90.params[2]:+.4f} d_gpr={qr90.params[3]:+.6f}")
print(f"    GPR β q90 = {qr90.params[3]:+.6f}  (OLS = {ols.params[3]:+.6f})")
ratio_q90_to_ols = qr90.params[3] / ols.params[3] if ols.params[3] != 0 else float("inf")
print(f"    ratio q90/OLS = {ratio_q90_to_ols:.2f}")

# Quantile q=0.10 (lower tail)
qr10 = QuantReg(y, Xc).fit(q=0.10)
print(f"\n  QuantReg q=0.10 (gold 하위 10% return tail):")
print(f"    GPR β q10 = {qr10.params[3]:+.6f}")

# H7 GPR 반증: q90 GPR β ≈ OLS GPR β (유의 차이 없음) → linear (국면비의존)
# 반증 임계: |β_q90 - β_OLS| / SE(β_OLS) < 1.96 (95%) = linear; >= 1.96 = tail amplification 확정
gap = qr90.params[3] - ols.params[3]
gap_sigma = gap / ols.bse[3]
print(f"\n  ★H7 GPR linearity 반증 (q90 β = OLS β):")
print(f"    gap = {gap:+.6f}, gap/SE(OLS) = {gap_sigma:+.3f}σ (|3|σ = 99%, |1.96| = 95%)")
H7_gpr_tail_amplification = abs(gap_sigma) >= 1.96
print(f"    → tail amplification {'확정 (|gap| >= 1.96σ)' if H7_gpr_tail_amplification else '미확정 (linear 가설 미기각)'}")

# === H7 통합 verdict ===
H7_gamma_flavor = adf_post.mean() > adf_pre.mean() + 0.5
H7_gpr_force_role = abs(ols_gpr_t) > 1.96
print(f"\n=== H7 통합 verdict ===")
print(f"  γ 분해 (cointegration 붕괴): {H7_gamma_flavor}")
print(f"  GPR force_include 정당 (OLS β 유의): {H7_gpr_force_role} (t={ols_gpr_t:.2f})")
print(f"  GPR tail-amplified (q90 vs OLS): {H7_gpr_tail_amplification}")
H7_SUPPORTED = H7_gamma_flavor or (H7_gpr_force_role and H7_gpr_tail_amplification)
print(f"  ★ H7 verdict = {'SUPPORTED (γ flavor OR GPR force+tail)' if H7_SUPPORTED else 'PARTIAL'}")

result = {
    "n_obs": int(len(df)),
    "gamma_proxy_rolling_eg_adf": {
        "pre_2022_mean_adf_stat": float(adf_pre.mean()),
        "post_2022_mean_adf_stat": float(adf_post.mean()),
        "delta_adf": float(adf_post.mean() - adf_pre.mean()),
        "gamma_decline_or_break": bool(H7_gamma_flavor),
        "interpretation": "ADF 음의 절댓값 작아짐 = cointegration 약화 = γ 붕괴 신호. H2 의 Johansen rank=0 (γ 극한 0) 과 정합.",
    },
    "ols_gpr": {
        "beta": float(ols.params[3]),
        "se": float(ols.bse[3]),
        "t_stat": float(ols_gpr_t),
        "p_value": float(ols_gpr_pval),
        "force_include_justified": bool(H7_gpr_force_role),
    },
    "qr_gpr_q90": {
        "beta_q90": float(qr90.params[3]),
        "beta_ols": float(ols.params[3]),
        "ratio_q90_to_ols": float(ratio_q90_to_ols),
        "gap": float(gap),
        "gap_sigma": float(gap_sigma),
        "tail_amplified_at_95pct": bool(H7_gpr_tail_amplification),
    },
    "qr_gpr_q10": {"beta_q10": float(qr10.params[3])},
    "H7_supported": bool(H7_SUPPORTED),
}
with open(os.path.join(RAW, "h7_result.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, default=str)
print(f"\n[save] raw/h7_rolling_eg.csv + raw/h7_result.json")
