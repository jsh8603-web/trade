"""
H2 검증 — level intercept shift (척추).
ln_gold = α + b·real_rate + c·ln_dollar + ε
검정:
  (1) 단위근 (ADF): 각 시리즈 I(1) 확인
  (2) Engle-Granger 2단계 cointegration: 잔차 ADF (귀무 = no coint)
  (3) Johansen trace + max-eigenvalue: 다변량 coint rank
  (4) Gregory-Hansen 수작업: 각 break 점 trim=0.15 에서 EG 잔차 ADF → sup-ADF (1996 cv)
  (5) RBC 재현: rolling 252d level R² (2010-21 vs 2022-26)
  (6) Subsample OLS α + 95% CI difference (pre-2022 vs 2022+)
  (7) Bai-Perron 대용 α QLR sup-F on level OLS
입력: fred_dfii10 + dtwexbgs + GLD
산출: stdout + raw/h2_result.json + raw/h2_rolling_r2.csv
"""
import json, os
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.tsa.vector_ar.vecm import coint_johansen
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
gld  = load_gld()
df = pd.concat([real, dol, gld], axis=1).loc["2010-01-01":].ffill().dropna()
df["ln_gold"] = np.log(df["gold"])
df["ln_dollar"] = np.log(df["dollar"])
print(f"[load] n={len(df)} range={df.index.min().date()}~{df.index.max().date()}")

# (1) Unit-root ADF on each series (귀무 = unit root)
print("\n=== (1) ADF on each series (level) ===")
for c in ["ln_gold", "real_rate", "ln_dollar"]:
    s = df[c].dropna()
    res = adfuller(s, regression="c", autolag="AIC")
    print(f"  {c}: ADF stat={res[0]:.3f} p={res[1]:.4f} → {'I(0) reject H0' if res[1]<0.05 else 'I(1) (cannot reject unit root)'}")

# (2) Engle-Granger cointegration: y = ln_gold, X = [real_rate, ln_dollar]
print("\n=== (2) Engle-Granger 2-step cointegration ===")
y = df["ln_gold"].values
X = df[["real_rate", "ln_dollar"]].values
Xc = add_constant(X)
res_full = OLS(y, Xc).fit()
alpha_full, b_full, c_full = res_full.params
resid = res_full.resid
print(f"  full-sample OLS: α={alpha_full:.4f}  b(real)={b_full:.4f}  c(ln$)={c_full:.4f}  R²={res_full.rsquared:.4f}")
adf_eg = adfuller(resid, regression="n", autolag="AIC")
print(f"  EG residual ADF: stat={adf_eg[0]:.3f} p={adf_eg[1]:.4f}")
print(f"  → {'cointegration 지지 (잔차 stationary)' if adf_eg[1]<0.05 else 'cointegration 부정 (잔차 non-stationary)'}")

# (3) Johansen cointegration test (trace + max-eig)
print("\n=== (3) Johansen cointegration test ===")
Y3 = df[["ln_gold", "real_rate", "ln_dollar"]].values
joh = coint_johansen(Y3, det_order=0, k_ar_diff=1)
trace_stats = joh.lr1; trace_cv95 = joh.cvt[:, 1]
eig_stats = joh.lr2; eig_cv95 = joh.cvm[:, 1]
for i in range(3):
    print(f"  r<={i}: trace={trace_stats[i]:.3f} cv95={trace_cv95[i]:.3f} {'REJECT' if trace_stats[i]>trace_cv95[i] else 'cannot reject'} | maxeig={eig_stats[i]:.3f} cv95={eig_cv95[i]:.3f} {'REJECT' if eig_stats[i]>eig_cv95[i] else 'cannot reject'}")
joh_rank = sum(1 for i in range(3) if trace_stats[i] > trace_cv95[i])
print(f"  → estimated coint rank = {joh_rank}")

# (4) Gregory-Hansen: 각 break 점 trim=0.15 에서 EG (level shift model "C") 잔차 ADF → sup-ADF
print("\n=== (4) Gregory-Hansen regime-shift cointegration (model C, level shift) ===")
n = len(df); trim = 0.15
lo = int(n*trim); hi = int(n*(1-trim))
best = {"sup_adf": np.inf, "break_idx": -1}  # sup over min ADF (most negative)
for tau in range(lo, hi):
    D = np.zeros(n); D[tau:] = 1.0
    X_gh = np.column_stack([X, D[:, None]])
    Xc_gh = add_constant(X_gh)
    try:
        res = OLS(y, Xc_gh).fit()
        a = adfuller(res.resid, regression="n", autolag=None, maxlag=1)
        if a[0] < best["sup_adf"]:
            best = {"sup_adf": a[0], "break_idx": tau}
    except Exception:
        pass
break_date = df.index[best["break_idx"]] if best["break_idx"] >= 0 else None
print(f"  GH sup-ADF (model C) = {best['sup_adf']:.3f}  break date = {break_date}")
# Gregory-Hansen 1996 cv for model C, k=2 regressors: 5% ≈ -4.92, 10% ≈ -4.69 (Table 1)
gh_cv5 = -4.92; gh_cv10 = -4.69
gh_reject5 = best["sup_adf"] < gh_cv5
print(f"  GH cv (1996 model C k=2): 5% = -4.92, 10% = -4.69")
print(f"  → {'REJECT no-coint-with-break (5%): cointegration with level shift 지지' if gh_reject5 else 'cannot reject (5%): regime-shift coint 미확정'}")

# (5) RBC reproduction: rolling 252d level R² (ln_gold ~ real_rate + ln_dollar) per window
print("\n=== (5) RBC reproduction: rolling 252d level R² ===")
WIN = 252
r2_series = []
for i in range(WIN, n+1):
    sub = df.iloc[i-WIN:i]
    Xs = add_constant(sub[["real_rate", "ln_dollar"]].values)
    res = OLS(sub["ln_gold"].values, Xs).fit()
    r2_series.append({"date": sub.index[-1], "r2": res.rsquared,
                     "alpha": res.params[0], "b_real": res.params[1], "c_dollar": res.params[2]})
rr = pd.DataFrame(r2_series).set_index("date")
rr.to_csv(os.path.join(RAW, "h2_rolling_r2.csv"))
periods = {"2010_21": ("2010-01-01", "2021-12-31"),
           "2022_23": ("2022-01-01", "2023-12-31"),
           "2024_26": ("2024-01-01", "2026-05-29")}
for p, (s, e) in periods.items():
    sub = rr.loc[s:e]
    print(f"  {p}: n={len(sub)} R² mean={sub['r2'].mean():.3f} (range [{sub['r2'].min():.3f}, {sub['r2'].max():.3f}])")
    print(f"      α mean={sub['alpha'].mean():.3f}  b_real={sub['b_real'].mean():.4f}  c_dollar={sub['c_dollar'].mean():.4f}")

# (6) Subsample OLS α difference
print("\n=== (6) Subsample OLS α (pre-2022 vs 2022+) ===")
pre = df.loc["2010-01-01":"2021-12-31"]
post = df.loc["2022-01-01":]
res_pre = OLS(pre["ln_gold"].values, add_constant(pre[["real_rate", "ln_dollar"]].values)).fit()
res_post = OLS(post["ln_gold"].values, add_constant(post[["real_rate", "ln_dollar"]].values)).fit()
a_pre, b_pre, c_pre = res_pre.params
a_post, b_post, c_post = res_post.params
print(f"  pre-2022:  α={a_pre:.4f} ± {res_pre.bse[0]:.4f}  b_real={b_pre:.4f}  c_dollar={c_pre:.4f}  R²={res_pre.rsquared:.4f}")
print(f"  post-2022: α={a_post:.4f} ± {res_post.bse[0]:.4f}  b_real={b_post:.4f}  c_dollar={c_post:.4f}  R²={res_post.rsquared:.4f}")
delta_alpha = a_post - a_pre
se_delta = np.sqrt(res_pre.bse[0]**2 + res_post.bse[0]**2)
ci95 = [delta_alpha - 1.96*se_delta, delta_alpha + 1.96*se_delta]
print(f"  ★Δα = {delta_alpha:+.4f} (SE {se_delta:.4f}, 95% CI [{ci95[0]:.4f}, {ci95[1]:.4f}])  excludes 0 = {0 < ci95[0] or 0 > ci95[1]}")
# 정량 기대 (≥15% 재평가): exp(Δα) - 1
pct_revaluation = (np.exp(delta_alpha) - 1) * 100
print(f"  ★implied level revaluation: {pct_revaluation:+.1f}% (정량 기대 ≥15%)")

# (7) QLR sup-F on full-period α (level OLS, against H0 stable α)
print("\n=== (7) QLR sup-F on level OLS (α-only break) ===")
def qlr_alpha_supF(y, X, trim=0.15):
    n = len(y); k = X.shape[1] + 1  # +1 for α dummy
    lo = int(n*trim); hi = int(n*(1-trim))
    Xc0 = add_constant(X)
    full = OLS(y, Xc0).fit()
    rss_full = full.ssr
    sup_f = -np.inf; sup_idx = -1
    for tau in range(lo, hi):
        D = np.zeros(n); D[tau:] = 1.0
        Xb = add_constant(np.column_stack([X, D[:, None]]))
        try:
            r = OLS(y, Xb).fit()
            F = ((rss_full - r.ssr) / 1) / (r.ssr / (n - Xb.shape[1]))
            if F > sup_f: sup_f = F; sup_idx = tau
        except: pass
    return sup_f, sup_idx
sup_f, sup_idx = qlr_alpha_supF(y, X)
sup_break_date = df.index[sup_idx] if sup_idx >= 0 else None
# QLR cv (Andrews 1993, single break, m=1 unknown break, 5% ≈ 8.85, 1% ≈ 12.16)
print(f"  α QLR sup-F = {sup_f:.3f}  break date = {sup_break_date}")
print(f"  cv (m=1, trim=0.15): 5% ≈ 8.85, 1% ≈ 12.16")
print(f"  → {'REJECT H0 stable α' if sup_f > 8.85 else 'cannot reject H0'}")

# === H2 verdict ===
in_window = (best["break_idx"] >= 0) and (pd.Timestamp("2022-07-01") <= break_date <= pd.Timestamp("2024-12-31"))
H2_VERDICT = (joh_rank >= 1 and adf_eg[1] < 0.10 and (gh_reject5 or in_window) and ci95[0] > 0 and pct_revaluation >= 15)
print(f"\n★ H2 verdict = {'SUPPORTED' if H2_VERDICT else 'PARTIAL or REJECTED'}")
print(f"  components: Johansen rank≥1={joh_rank>=1}  EG p<0.10={adf_eg[1]<0.10}  GH break/window={gh_reject5 or in_window}  Δα 95%CI>0={ci95[0]>0}  revaluation≥15%={pct_revaluation>=15}")

# === 박제 ===
result = {
    "n_obs": int(n),
    "date_range": [str(df.index.min().date()), str(df.index.max().date())],
    "unit_root_adf": {
        c: {"stat": float(adfuller(df[c].dropna(), regression="c", autolag="AIC")[0]),
            "p": float(adfuller(df[c].dropna(), regression="c", autolag="AIC")[1])}
        for c in ["ln_gold", "real_rate", "ln_dollar"]
    },
    "engle_granger": {
        "full_sample": {"alpha": float(alpha_full), "b_real": float(b_full), "c_dollar": float(c_full), "r2": float(res_full.rsquared)},
        "residual_adf": {"stat": float(adf_eg[0]), "p": float(adf_eg[1]), "coint_support": bool(adf_eg[1] < 0.10)}
    },
    "johansen": {
        "trace_stats": [float(x) for x in trace_stats],
        "trace_cv95": [float(x) for x in trace_cv95],
        "max_eig_stats": [float(x) for x in eig_stats],
        "max_eig_cv95": [float(x) for x in eig_cv95],
        "estimated_rank": int(joh_rank),
    },
    "gregory_hansen": {
        "sup_adf": float(best["sup_adf"]),
        "break_date": str(break_date.date()) if break_date is not None else None,
        "cv5_model_C_k2": -4.92,
        "cv10_model_C_k2": -4.69,
        "reject_5pct": bool(gh_reject5),
        "break_in_window_2022Q3_2024": bool(in_window),
    },
    "rolling_252d_r2_by_period": {
        p: {"n": int(len(rr.loc[s:e])), "r2_mean": float(rr.loc[s:e, "r2"].mean()),
            "alpha_mean": float(rr.loc[s:e, "alpha"].mean()),
            "b_real_mean": float(rr.loc[s:e, "b_real"].mean()),
            "c_dollar_mean": float(rr.loc[s:e, "c_dollar"].mean())}
        for p, (s, e) in periods.items()
    },
    "subsample_alpha_diff": {
        "pre_2022": {"alpha": float(a_pre), "se": float(res_pre.bse[0]), "b_real": float(b_pre), "c_dollar": float(c_pre), "r2": float(res_pre.rsquared)},
        "post_2022": {"alpha": float(a_post), "se": float(res_post.bse[0]), "b_real": float(b_post), "c_dollar": float(c_post), "r2": float(res_post.rsquared)},
        "delta_alpha": float(delta_alpha),
        "se_delta": float(se_delta),
        "ci95": [float(ci95[0]), float(ci95[1])],
        "ci95_excludes_zero": bool(ci95[0] > 0 or ci95[1] < 0),
        "implied_level_revaluation_pct": float(pct_revaluation),
        "ge_15pct": bool(pct_revaluation >= 15),
    },
    "qlr_alpha_supF": {
        "sup_f": float(sup_f),
        "break_date": str(sup_break_date.date()) if sup_break_date is not None else None,
        "cv5_m1_trim015": 8.85,
        "cv1_m1_trim015": 12.16,
        "reject_5pct": bool(sup_f > 8.85),
    },
    "H2_supported": bool(H2_VERDICT),
}
with open(os.path.join(RAW, "h2_result.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, default=str)
print(f"\n[save] raw/h2_rolling_r2.csv + raw/h2_result.json")
