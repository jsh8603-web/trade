"""
H4 검증 — sys_priors β reconciliation (4-case dimensional decision tree).
실측: 일별·월별 × gold_USD·gold/SDR 의 2x2 패널에서 표준화 다중회귀 |β̂| 측정.
정량 게이트: 일별 표준화 다중회귀 |β̂_rate|<0.40 AND |β̂_dollar|<0.55 → sys_priors [-0.5, -0.8] 기각.
sys_priors → posterior shrink. dollar β numeraire trap 보정 후 30~50% 약화 예상.
입력: fred_dfii10·dtwexbgs·dexuseu·dexjpus·dexchus·dexusuk + GLD
산출: stdout + raw/h4_result.json
"""
import json, os
import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import OLS
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
    df = pd.DataFrame({"date": pd.to_datetime(ts, unit="s").normalize(), "gold": close}).dropna()
    return df.set_index("date").sort_index()

real = load_fred("fred_dfii10.csv", "real_rate")
dol  = load_fred("fred_dtwexbgs.csv", "dollar")
eur  = load_fred("fred_dexuseu.csv", "eur")  # USD per EUR
jpy  = load_fred("fred_dexjpus.csv", "jpy")  # JPY per USD
cny  = load_fred("fred_dexchus.csv", "cny")  # CNY per USD
gbp  = load_fred("fred_dexusuk.csv", "gbp")  # USD per GBP
gld  = load_gld()

# SDR/USD value (USD per 1 SDR) — IMF 2022 weights (constant approximation)
W = {"USD": 0.4338, "EUR": 0.2931, "CNY": 0.1228, "JPY": 0.0759, "GBP": 0.0744}
df = pd.concat([real, dol, eur, jpy, cny, gbp, gld], axis=1).loc["2010-01-01":].ffill().dropna()
df["sdr_usd"] = (W["USD"]*1.0
                 + W["EUR"]*df["eur"]
                 + W["CNY"]*(1.0/df["cny"])
                 + W["JPY"]*(1.0/df["jpy"])
                 + W["GBP"]*df["gbp"])
df["gold_sdr"] = df["gold"] / df["sdr_usd"]
df["ln_gold_usd"] = np.log(df["gold"])
df["ln_gold_sdr"] = np.log(df["gold_sdr"])
df["ln_dollar"] = np.log(df["dollar"])
print(f"[load] daily n={len(df)} range={df.index.min().date()}~{df.index.max().date()}")

# Daily changes
chg_d = pd.DataFrame(index=df.index)
chg_d["d_real_bp"] = df["real_rate"].diff() * 100.0
chg_d["r_dollar"] = np.log(df["dollar"]).diff()
chg_d["r_gold_usd"] = df["ln_gold_usd"].diff()
chg_d["r_gold_sdr"] = df["ln_gold_sdr"].diff()
chg_d = chg_d.dropna()

# Monthly resample (last value, then diff)
mo = df.resample("ME").last().dropna()
chg_m = pd.DataFrame(index=mo.index)
chg_m["d_real_bp"] = mo["real_rate"].diff() * 100.0
chg_m["r_dollar"] = np.log(mo["dollar"]).diff()
chg_m["r_gold_usd"] = mo["ln_gold_usd"].diff()
chg_m["r_gold_sdr"] = mo["ln_gold_sdr"].diff()
chg_m = chg_m.dropna()
print(f"[monthly] n={len(chg_m)}")

def standardized_multi_reg(chg, target_col, regressors=("d_real_bp", "r_dollar")):
    """Return standardized β, SE, VIF, R², n."""
    sub = chg[list(regressors) + [target_col]].dropna()
    # z-score each variable
    z = sub.apply(lambda x: (x - x.mean()) / x.std())
    y = z[target_col].values
    X = z[list(regressors)].values
    Xc = add_constant(X)
    res = OLS(y, Xc).fit()
    # VIF for each regressor
    vifs = []
    for i in range(X.shape[1]):
        Xj = np.delete(X, i, axis=1)
        Xjc = add_constant(Xj)
        r2j = OLS(X[:, i], Xjc).fit().rsquared
        vifs.append(1.0 / max(1e-9, 1.0 - r2j))
    # Marginal Pearson for each regressor
    marginal_r = [float(np.corrcoef(z[r], z[target_col])[0, 1]) for r in regressors]
    return {
        "n": int(len(sub)),
        "alpha_z": float(res.params[0]),
        "beta_std": {regressors[i]: float(res.params[i+1]) for i in range(len(regressors))},
        "se_std": {regressors[i]: float(res.bse[i+1]) for i in range(len(regressors))},
        "marginal_pearson": {regressors[i]: marginal_r[i] for i in range(len(regressors))},
        "vif": {regressors[i]: float(vifs[i]) for i in range(len(regressors))},
        "r2": float(res.rsquared),
    }

# 2×2 panel
panel = {}
for freq, chg in [("daily", chg_d), ("monthly", chg_m)]:
    for num, ycol in [("gold_USD", "r_gold_usd"), ("gold_SDR", "r_gold_sdr")]:
        key = f"{freq}__{num}"
        panel[key] = standardized_multi_reg(chg, ycol)
        r = panel[key]
        print(f"\n=== {freq} × {num} ===")
        print(f"  n={r['n']} R²={r['r2']:.4f}")
        print(f"  β̂_rate (std)   = {r['beta_std']['d_real_bp']:+.4f}  SE={r['se_std']['d_real_bp']:.4f}  | Pearson(marginal)={r['marginal_pearson']['d_real_bp']:+.4f}  VIF={r['vif']['d_real_bp']:.3f}")
        print(f"  β̂_dollar (std) = {r['beta_std']['r_dollar']:+.4f}  SE={r['se_std']['r_dollar']:.4f}  | Pearson(marginal)={r['marginal_pearson']['r_dollar']:+.4f}  VIF={r['vif']['r_dollar']:.3f}")

# 4-case dimensional decision tree
sys_prior = {"rate": -0.5, "dollar": -0.8}
print(f"\n=== sys_priors decision tree ===")
print(f"sys_priors gold loading: rate={sys_prior['rate']}, dollar={sys_prior['dollar']}")

# Gate (Q3): 일별 표준화 다중회귀 |β̂_rate|<0.40 AND |β̂_dollar|<0.55
daily_usd = panel["daily__gold_USD"]
beta_r_daily = abs(daily_usd["beta_std"]["d_real_bp"])
beta_d_daily = abs(daily_usd["beta_std"]["r_dollar"])
gate_rate = beta_r_daily < 0.40
gate_dollar = beta_d_daily < 0.55
gate_pass = gate_rate and gate_dollar
print(f"\nGate (daily × gold_USD): |β̂_rate|={beta_r_daily:.3f} <0.40 = {gate_rate} AND |β̂_dollar|={beta_d_daily:.3f} <0.55 = {gate_dollar}")
print(f"→ sys_priors {'기각 (posterior shrink 정당)' if gate_pass else '유지 (prior magnitude 합당)'}")

# numeraire trap: dollar β attenuation USD → SDR
beta_d_sdr_daily = abs(panel["daily__gold_SDR"]["beta_std"]["r_dollar"])
attenuation = (beta_d_daily - beta_d_sdr_daily) / beta_d_daily if beta_d_daily > 0 else 0
print(f"\nnumeraire trap (daily): dollar β USD→SDR")
print(f"  |β̂_dollar| USD={beta_d_daily:.4f} → SDR={beta_d_sdr_daily:.4f} (attenuation {100*attenuation:+.1f}%)")
print(f"  expected 30~50% attenuation: {'within range' if 30 <= 100*attenuation <= 50 else 'outside range (' + str(round(100*attenuation,1)) + '%)'}")

# Case 결판
print(f"\n=== 4-case case 판정 (Claude R2 dimensional decision tree) ===")
case = {}
beta_r_monthly = abs(panel["monthly__gold_USD"]["beta_std"]["d_real_bp"])
beta_d_monthly = abs(panel["monthly__gold_USD"]["beta_std"]["r_dollar"])
print(f"  case (1) 일별 표준화 다중: |β̂_rate|={beta_r_daily:.3f} vs sys |-0.5| → ratio {beta_r_daily/0.5:.2f}; |β̂_dollar|={beta_d_daily:.3f} vs |0.8| → ratio {beta_d_daily/0.8:.2f}")
print(f"  case (4) 월별 표준화 다중: |β̂_rate|={beta_r_monthly:.3f} vs |-0.5| → ratio {beta_r_monthly/0.5:.2f}; |β̂_dollar|={beta_d_monthly:.3f} vs |0.8| → ratio {beta_d_monthly/0.8:.2f}")
print(f"  Pearson 단변량 일별: rate {panel['daily__gold_USD']['marginal_pearson']['d_real_bp']:.3f}, dollar {panel['daily__gold_USD']['marginal_pearson']['r_dollar']:.3f}")

# 가장 가까운 case 결판 (lowest |sys_prior - empirical|)
def closest_case():
    distances = {
        "case1_daily_std_multi": abs(panel["daily__gold_USD"]["beta_std"]["d_real_bp"] + 0.5) + abs(panel["daily__gold_USD"]["beta_std"]["r_dollar"] + 0.8),
        "case2_daily_univar":    abs(panel["daily__gold_USD"]["marginal_pearson"]["d_real_bp"] + 0.5) + abs(panel["daily__gold_USD"]["marginal_pearson"]["r_dollar"] + 0.8),
        "case4_monthly_std_multi": abs(panel["monthly__gold_USD"]["beta_std"]["d_real_bp"] + 0.5) + abs(panel["monthly__gold_USD"]["beta_std"]["r_dollar"] + 0.8),
    }
    return min(distances, key=distances.get), distances
best_case, dists = closest_case()
print(f"\n★ closest case (가장 작은 L1 distance to sys_priors[-0.5,-0.8]): {best_case}")
for k, v in dists.items():
    print(f"  {k}: distance = {v:.3f}")

result = {
    "panel_2x2": panel,
    "sys_priors_gate": {
        "abs_beta_rate_daily_USD": float(beta_r_daily),
        "abs_beta_dollar_daily_USD": float(beta_d_daily),
        "gate_rate_pass": bool(gate_rate),
        "gate_dollar_pass": bool(gate_dollar),
        "gate_overall_pass": bool(gate_pass),
        "decision": "기각·shrink" if gate_pass else "유지",
    },
    "numeraire_trap_daily": {
        "abs_beta_dollar_USD": float(beta_d_daily),
        "abs_beta_dollar_SDR": float(beta_d_sdr_daily),
        "attenuation_pct": float(100*attenuation),
        "expected_30_50_pct": (30 <= 100*attenuation <= 50),
    },
    "closest_case_to_sys_priors": best_case,
    "case_distances": dists,
}
with open(os.path.join(RAW, "h4_result.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, default=str)
print(f"\n[save] raw/h4_result.json")
