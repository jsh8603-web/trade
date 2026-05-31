"""
H1 검증 — 변화율 베타 안정.
3-layer 통합 반증조건:
  Layer 1: 252d rolling Pearson Δreal_rate ↔ Δln_gold 부호반전 0회 (v1 재현 + 확장)
  Layer 2: rolling 252d OLS β (Δgold ~ Δreal + Δdollar) 의 부호반전·QLR sup-F break
  Layer 3 (별도, H8): Δ-beta e-process vs level 잔차 e-process ordering
입력: raw/fred_dfii10.csv + raw/fred_dtwexbgs.csv + raw/try_yahoo_v8.json (GLD)
산출: stdout 요약 + raw/h1_rolling_beta.csv + raw/h1_result.json
"""
import json, os
import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
from statsmodels.stats.diagnostic import breaks_cusumolsresid

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
    ts = r["timestamp"]
    close = r["indicators"]["quote"][0]["close"]
    df = pd.DataFrame({"date": pd.to_datetime(ts, unit="s").normalize(), "gold": close}).dropna()
    return df.set_index("date").sort_index()

real = load_fred("fred_dfii10.csv", "real_rate")
dol  = load_fred("fred_dtwexbgs.csv", "dollar")
gld  = load_gld()
df = pd.concat([real, dol, gld], axis=1).loc["2010-01-01":].ffill().dropna()
print(f"[load] n={len(df)} range={df.index.min().date()}~{df.index.max().date()}")

chg = pd.DataFrame(index=df.index)
chg["d_real_bp"] = df["real_rate"].diff() * 100.0
chg["r_dollar"]  = np.log(df["dollar"]).diff()
chg["r_gold"]    = np.log(df["gold"]).diff()
chg = chg.dropna()

# === LAYER 1: 252d rolling Pearson Δreal ↔ Δgold (v1 재현) ===
roll_p = chg["d_real_bp"].rolling(252).corr(chg["r_gold"]).dropna()
n_pos = int((roll_p > 0).sum())
n_weak = int((roll_p.abs() < 0.10).sum())
total = len(roll_p)
print(f"\n=== LAYER 1: 252d rolling Pearson Δreal-Δgold ===")
print(f" n_windows={total} median={roll_p.median():.4f} min={roll_p.min():.4f} max={roll_p.max():.4f}")
print(f" 부호반전(>0) days: {n_pos} ({100*n_pos/total:.2f}%)")
print(f" 약화(|r|<0.10) days: {n_weak} ({100*n_weak/total:.2f}%) — 베이스라인(가설) 3.1%")

# === LAYER 2: 252d rolling OLS β (Δgold ~ const + Δreal + Δdollar) ===
WIN = 252
betas = []
for i in range(WIN, len(chg)+1):
    sub = chg.iloc[i-WIN:i]
    X = add_constant(sub[["d_real_bp", "r_dollar"]].values)
    y = sub["r_gold"].values
    try:
        res = OLS(y, X).fit()
        betas.append({
            "date": sub.index[-1],
            "b_real": res.params[1],
            "b_dollar": res.params[2],
            "se_real": res.bse[1],
            "se_dollar": res.bse[2],
            "r2": res.rsquared,
        })
    except Exception:
        pass
rb = pd.DataFrame(betas).set_index("date")
rb.to_csv(os.path.join(RAW, "h1_rolling_beta.csv"))

n_beta_sign_flip = int((rb["b_real"] > 0).sum())
b_real_changepct = 100 * (rb["b_real"].iloc[-252:].mean() - rb["b_real"].iloc[:252].mean()) / abs(rb["b_real"].iloc[:252].mean())
print(f"\n=== LAYER 2: 252d rolling OLS β (Δreal | Δdollar) ===")
print(f" n={len(rb)} b_real mean={rb['b_real'].mean():.5f} (sd {rb['b_real'].std():.5f})")
print(f" b_real range=[{rb['b_real'].min():.5f}, {rb['b_real'].max():.5f}]")
print(f" 부호반전(b_real>0) days: {n_beta_sign_flip} ({100*n_beta_sign_flip/len(rb):.2f}%)")
print(f" b_real pre-2022 vs 2024+ change: {b_real_changepct:+.1f}%")

# === Bai-Perron 대용: QLR sup-F (Quandt-Andrews) on b_real ===
# Approximation: trimmed window F-stat each candidate break point in inner 70%
def qlr_sup_f(series_y, X_with_const, trim=0.15):
    n = len(series_y)
    k = X_with_const.shape[1]
    lo = int(n*trim); hi = int(n*(1-trim))
    full = OLS(series_y, X_with_const).fit()
    rss_full = full.ssr
    sup_f = -np.inf; sup_idx = -1
    for tau in range(lo, hi):
        X1 = X_with_const[:tau]; X2 = X_with_const[tau:]
        y1 = series_y[:tau]; y2 = series_y[tau:]
        try:
            r1 = OLS(y1, X1).fit(); r2 = OLS(y2, X2).fit()
            rss = r1.ssr + r2.ssr
            F = ((rss_full - rss) / k) / (rss / (n - 2*k))
            if F > sup_f: sup_f = F; sup_idx = tau
        except: pass
    # Andrews 1993 critical values (k=3, trim=0.15): 5% ≈ 16.45, 1% ≈ 20.0
    return sup_f, sup_idx

# Apply QLR on full sample (Δgold ~ const + Δreal + Δdollar)
X_full = add_constant(chg[["d_real_bp", "r_dollar"]].values)
y_full = chg["r_gold"].values
sup_f, sup_idx = qlr_sup_f(y_full, X_full)
sup_date = chg.index[sup_idx] if sup_idx >= 0 else None
print(f"\n=== QLR sup-F (Quandt-Andrews break test, trim=0.15) ===")
print(f" sup-F = {sup_f:.3f}  (Andrews '93 cv k=3 trim=0.15: 5%≈16.45, 1%≈20.0)")
print(f" sup break date = {sup_date}")

# === 3-layer 통합 판정 ===
layer1_pass = (n_pos == 0)
weak_baseline = 0.031  # v1 보고 베이스라인 3.1%
weak_ratio = n_weak / total
layer1_weak_pass = (weak_ratio < 3 * weak_baseline)
layer2_signflip_pass = (n_beta_sign_flip / len(rb)) < 0.05
layer2_break_pass_loose = (sup_f < 16.45)  # 5% Andrews critical
layer2_break_pass_strict = (sup_f < 20.0)  # 1% Andrews critical
print(f"\n=== 3-layer 통합 판정 (반증조건) ===")
print(f" Layer 1 Pearson 부호반전: pass={layer1_pass} (조건: 0회)")
print(f" Layer 1 약화 비율: pass={layer1_weak_pass} ({100*weak_ratio:.2f}% < 9.3%=3.1%×3)")
print(f" Layer 2 β 부호반전: pass={layer2_signflip_pass} ({100*n_beta_sign_flip/len(rb):.2f}% < 5%)")
print(f" Layer 2 QLR sup-F (5%): pass={layer2_break_pass_loose} ({sup_f:.2f} < 16.45)")
print(f" Layer 2 QLR sup-F (1%): pass={layer2_break_pass_strict} ({sup_f:.2f} < 20.0)")
H1_VERDICT = layer1_pass and layer1_weak_pass and layer2_signflip_pass  # break 는 보조
print(f"\n★ H1 verdict (Layer 1+2 부호반전): {'SUPPORTED' if H1_VERDICT else 'REJECTED'}")

# === 결과 박제 ===
result = {
    "n_obs": int(len(chg)),
    "date_range": [str(chg.index.min().date()), str(chg.index.max().date())],
    "layer1_pearson": {
        "n_windows": total,
        "median": float(roll_p.median()),
        "min": float(roll_p.min()),
        "max": float(roll_p.max()),
        "positive_days": n_pos,
        "positive_pct": 100*n_pos/total,
        "weak_days": n_weak,
        "weak_pct": 100*n_weak/total,
        "baseline_weak_pct": 3.1,
        "pass": layer1_pass,
        "weak_pass": layer1_weak_pass,
    },
    "layer2_rolling_beta": {
        "n_windows": int(len(rb)),
        "b_real_mean": float(rb["b_real"].mean()),
        "b_real_std": float(rb["b_real"].std()),
        "b_real_range": [float(rb["b_real"].min()), float(rb["b_real"].max())],
        "b_real_sign_flips": n_beta_sign_flip,
        "b_real_sign_flips_pct": 100*n_beta_sign_flip/len(rb),
        "b_real_pre_vs_post_change_pct": float(b_real_changepct),
        "sign_flip_pass": layer2_signflip_pass,
    },
    "qlr_sup_f": {
        "sup_f": float(sup_f),
        "sup_break_date": str(sup_date.date()) if sup_date is not None else None,
        "cv_5pct_andrews1993_k3_trim015": 16.45,
        "cv_1pct_andrews1993_k3_trim015": 20.0,
        "pass_5pct": bool(layer2_break_pass_loose),
        "pass_1pct": bool(layer2_break_pass_strict),
    },
    "H1_supported": H1_VERDICT,
}
with open(os.path.join(RAW, "h1_result.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, default=str)
print(f"\n[save] raw/h1_rolling_beta.csv + raw/h1_result.json")
