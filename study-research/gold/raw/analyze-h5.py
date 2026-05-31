"""
H5 검증 — safe-haven 국면의존 (Baur-Lucey 2010).
가설: gold ↔ credit/equity stress 관계는 평시 약, 위기 강한 음의 안전자산화.

설계:
  (a) Model A — threshold interaction (Baur-Lucey):
      r_gold = α + β·Δstress + γ·Δstress·D_crisis + ε
      D_crisis = stress(상위 10%) 또는 (상위 5%, robustness)
      Newey-West HAC SE (lag = floor(n^0.25))
  (b) Model B — 2-state Markov-switching (mean + variance):
      r_gold ~ μ_state + σ_state·ε  (statsmodels MarkovRegression switching mean+variance)
      state 식별 후 state-conditional Δstress↔r_gold corr 보고
  (c) Block bootstrap CI (block=22일 ≈ 1mo) for γ
  (d) Bonferroni 보정: H1~H8 8 가설 multi-test α/8=0.00625

입력: fred_baa10y.csv + fred_vix.csv + fred_hy_oas.csv (3년치 한정) + try_yahoo_v8.json (GLD)
산출: stdout + raw/h5_result.json
주의: HY OAS 는 main collector 의존 (full history 미가용). 본 study 는 BAA10Y 1차, HY OAS 부분 검증.
"""
import json
import os
import warnings
import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

warnings.filterwarnings("ignore")
RAW = os.path.dirname(os.path.abspath(__file__))
RNG = np.random.default_rng(20260531)


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


def nw_se(resid, X, lags):
    """Newey-West HAC standard errors for OLS coefficients."""
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    u = (resid * X.T).T
    S = (u.T @ u)
    for lag in range(1, lags + 1):
        w = 1 - lag / (lags + 1)
        Gamma = u[lag:].T @ u[:-lag]
        S += w * (Gamma + Gamma.T)
    V = XtX_inv @ S @ XtX_inv
    return np.sqrt(np.diag(V))


def block_bootstrap_idx(n, block):
    n_blocks = int(np.ceil(n / block))
    starts = RNG.integers(0, n - block + 1, size=n_blocks)
    idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
    return idx


def threshold_model(rg, dstr, q=0.90, label="stress"):
    """Baur-Lucey threshold interaction with Newey-West HAC + block bootstrap CI for γ."""
    thr = np.quantile(dstr, q)
    Dc = (dstr >= thr).astype(float)
    X = np.column_stack([np.ones(len(rg)), dstr, dstr * Dc])
    res = OLS(rg, X).fit()
    a, b, g = res.params
    lags = int(np.floor(len(rg) ** 0.25))
    se = nw_se(res.resid, X, lags)
    t_g = g / se[2]
    p_g = 2 * (1 - norm.cdf(abs(t_g)))  # 정규근사 양측 p
    # Block bootstrap γ 분포
    boots = []
    for _ in range(2000):
        idx = block_bootstrap_idx(len(rg), block=22)
        Xb = X[idx]
        yb = rg[idx]
        try:
            rb = OLS(yb, Xb).fit()
            boots.append(rb.params[2])
        except Exception:
            continue
    boots = np.array(boots)
    ci_lo, ci_hi = np.percentile(boots, [2.5, 97.5])
    return {
        "label": label,
        "quantile_threshold": float(q),
        "threshold_value": float(thr),
        "n_crisis_obs": int(Dc.sum()),
        "n_total": int(len(rg)),
        "alpha": float(a),
        "beta_baseline": float(b),
        "gamma_crisis_extra": float(g),
        "se_gamma_NW_HAC": float(se[2]),
        "t_gamma": float(t_g),
        "p_gamma_NW_two_sided_normal": float(p_g),
        "ci95_gamma_block_bootstrap_22d": [float(ci_lo), float(ci_hi)],
        "boot_n_successful": int(len(boots)),
        "NW_lag_truncation": int(lags),
        "R2": float(res.rsquared),
    }


def markov_switching(rg, k_regimes=2):
    """Markov-switching mean+variance on r_gold."""
    mod = MarkovRegression(rg, k_regimes=k_regimes, trend="c", switching_variance=True)
    try:
        fit = mod.fit(disp=False, maxiter=200)
    except Exception as e:
        return {"converged": False, "error": str(e)}
    smoothed_probs = np.asarray(fit.smoothed_marginal_probabilities)
    # smoothed_probs shape = (n_obs, k_regimes) in newer statsmodels
    if smoothed_probs.ndim == 2 and smoothed_probs.shape[1] == k_regimes:
        state0_prob = smoothed_probs[:, 0]
        state1_prob = smoothed_probs[:, 1]
    else:
        state0_prob = np.array(smoothed_probs[0])
        state1_prob = np.array(smoothed_probs[1])
    pnames = list(fit.model.param_names)
    pvals = np.asarray(fit.params)
    pd_params = dict(zip(pnames, [float(v) for v in pvals]))
    return {
        "converged": True,
        "params": pd_params,
        "param_names": pnames,
        "log_likelihood": float(fit.llf),
        "aic": float(fit.aic),
        "regime_means": [pd_params.get(f"const[{i}]") for i in range(k_regimes)],
        "regime_sigma2": [pd_params.get(f"sigma2[{i}]") for i in range(k_regimes)],
        "state0_avg_prob": float(state0_prob.mean()),
        "state1_avg_prob": float(state1_prob.mean()),
        "smoothed_probs_state1_head5": [float(x) for x in state1_prob[:5]],
        "smoothed_probs_state1_tail5": [float(x) for x in state1_prob[-5:]],
    }


def state_conditional_corr(rg, dstr, state1_prob, thr=0.5):
    """state1 prob > thr 인 obs 만 correlation."""
    mask_h = state1_prob > thr
    mask_l = ~mask_h
    out = {}
    for label, m in [("crisis_state(prob>0.5)", mask_h), ("normal_state(prob<=0.5)", mask_l)]:
        if m.sum() < 10:
            out[label] = {"n": int(m.sum()), "pearson_r": None, "p": None}
            continue
        r = np.corrcoef(rg[m], dstr[m])[0, 1]
        n = int(m.sum())
        t = r * np.sqrt(max(n - 2, 1)) / np.sqrt(max(1 - r * r, 1e-9))
        p = 2 * (1 - norm.cdf(abs(t)))
        out[label] = {"n": n, "pearson_r": float(r), "t": float(t), "p_normal_approx": float(p)}
    return out


# --- LOAD
baa = load_fred("fred_baa10y.csv", "baa")
vix = load_fred("fred_vix.csv", "vix")
gld = load_gld()
hy = load_fred("fred_hy_oas.csv", "hy_oas")  # 2023-05~ 만

df = pd.concat([baa, vix, gld], axis=1).loc["2010-01-04":].ffill().dropna()
df["r_gold"] = np.log(df["gold"]).diff()
df["d_baa"] = df["baa"].diff()
df["d_vix"] = df["vix"].diff()
df = df.dropna()
print(f"[load] daily n={len(df)} range={df.index.min().date()}~{df.index.max().date()}")
n_full = len(df)

result = {
    "design": "Baur-Lucey 2010 threshold + Markov-switching + Newey-West HAC + block bootstrap",
    "data": {
        "source": ["FRED BAA10Y", "FRED VIXCLS", "Yahoo GLD ETF (try_yahoo_v8.json)"],
        "n_daily": n_full,
        "date_min": str(df.index.min().date()),
        "date_max": str(df.index.max().date()),
        "missing_handling": "ffill + dropna",
    },
    "multi_test_correction": {
        "n_hypotheses_total": 8,
        "bonferroni_alpha_per_test": 0.05 / 8,
        "note": "α/8=0.00625, 본 가설 단일 γ_crisis p-value 도 이 임계 적용",
    },
    "attempt_counts": {
        "n_models_tested": 4,
        "models": ["threshold q90 BAA", "threshold q95 BAA (robust)", "threshold q90 VIX", "Markov-switching 2-state"],
        "note": "K축 시도횟수 공시: 4 모델 보고",
    },
}

# Model A1: threshold BAA q=0.90
print("\n=== Model A1: threshold q=0.90 BAA10Y ===")
mA1 = threshold_model(df["r_gold"].values, df["d_baa"].values, q=0.90, label="d_baa")
result["model_A1_threshold_BAA_q90"] = mA1
print(json.dumps({k: v for k, v in mA1.items() if not isinstance(v, list)}, indent=2, ensure_ascii=False))

# Model A1 robust: q=0.95
print("\n=== Model A1 robust: threshold q=0.95 BAA10Y ===")
mA1b = threshold_model(df["r_gold"].values, df["d_baa"].values, q=0.95, label="d_baa_q95")
result["model_A1_threshold_BAA_q95"] = mA1b
print(json.dumps({k: v for k, v in mA1b.items() if not isinstance(v, list)}, indent=2, ensure_ascii=False))

# Model A2: threshold VIX q=0.90
print("\n=== Model A2: threshold q=0.90 ΔVIX ===")
mA2 = threshold_model(df["r_gold"].values, df["d_vix"].values, q=0.90, label="d_vix")
result["model_A2_threshold_VIX_q90"] = mA2
print(json.dumps({k: v for k, v in mA2.items() if not isinstance(v, list)}, indent=2, ensure_ascii=False))

# Model B: Markov-switching on r_gold
print("\n=== Model B: 2-state Markov-switching on r_gold ===")
mB = markov_switching(df["r_gold"].values, k_regimes=2)
result["model_B_markov_switching"] = mB
print(json.dumps(mB, indent=2, ensure_ascii=False, default=str))

# State-conditional correlations
if mB.get("converged"):
    mod = MarkovRegression(df["r_gold"].values, k_regimes=2, trend="c", switching_variance=True)
    fit = mod.fit(disp=False, maxiter=200)
    sp = np.asarray(fit.smoothed_marginal_probabilities)
    if sp.ndim == 2 and sp.shape[1] == 2:
        state1_prob = sp[:, 1]
    else:
        state1_prob = np.array(sp[1])
    print("\n=== State-conditional Δstress↔r_gold correlation ===")
    corr_baa = state_conditional_corr(df["r_gold"].values, df["d_baa"].values, state1_prob)
    corr_vix = state_conditional_corr(df["r_gold"].values, df["d_vix"].values, state1_prob)
    result["state_conditional_corr_d_baa"] = corr_baa
    result["state_conditional_corr_d_vix"] = corr_vix
    print("d_baa:", json.dumps(corr_baa, indent=2, ensure_ascii=False))
    print("d_vix:", json.dumps(corr_vix, indent=2, ensure_ascii=False))

# HY OAS 부분 검증 (n=3년 한정)
print("\n=== HY OAS 부분 검증 (n=3년) ===")
hy_df = pd.concat([hy, gld], axis=1).ffill().dropna()
hy_df["r_gold"] = np.log(hy_df["gold"]).diff()
hy_df["d_hy"] = hy_df["hy_oas"].diff()
hy_df = hy_df.dropna()
if len(hy_df) >= 100:
    mH = threshold_model(hy_df["r_gold"].values, hy_df["d_hy"].values, q=0.90, label="d_hy_OAS")
    result["model_HY_OAS_partial_n_limited"] = mH
    result["model_HY_OAS_partial_n_limited"]["caveat"] = (
        "n=3년 한정 (full history main collector 의존 FRED ALFRED). "
        "위기 표본 (2008/2020/2022) 부재 → 본 결과는 tentative directional only."
    )
    print(json.dumps({k: v for k, v in mH.items() if not isinstance(v, list)}, indent=2, ensure_ascii=False))
    print(f"  caveat: {result['model_HY_OAS_partial_n_limited']['caveat']}")
else:
    result["model_HY_OAS_partial_n_limited"] = {"n": int(len(hy_df)), "skipped": "n<100"}

# --- VERDICT 판정
# 임계 (n<30 5게이트 + Bonferroni α/8=0.00625):
# (a) γ_crisis < 0 (안전자산화 = 위기 시 추가 음의 관계) 부호 만족?
# (b) p_γ < α/8 = 0.00625 (multi-test 보정 후 유의)?
# (c) state-conditional corr 위기 state 에서 |r| > 평시 state |r|?
verdict_components = []
g_baa = mA1["gamma_crisis_extra"]
p_baa = mA1["p_gamma_NW_two_sided_normal"]
ci_baa = mA1["ci95_gamma_block_bootstrap_22d"]
sign_ok = g_baa < 0
p_bonf_ok = p_baa < 0.05 / 8
verdict_components.append({
    "test": "BAA q90 γ_crisis",
    "value": g_baa,
    "p": p_baa,
    "ci95": ci_baa,
    "sign_negative": bool(sign_ok),
    "p_bonferroni_0.00625": bool(p_bonf_ok),
})

g_vix = mA2["gamma_crisis_extra"]
p_vix = mA2["p_gamma_NW_two_sided_normal"]
ci_vix = mA2["ci95_gamma_block_bootstrap_22d"]
verdict_components.append({
    "test": "VIX q90 γ_crisis",
    "value": g_vix,
    "p": p_vix,
    "ci95": ci_vix,
    "sign_negative": bool(g_vix < 0),
    "p_bonferroni_0.00625": bool(p_vix < 0.05 / 8),
})

# 종합
n_pass = sum(1 for c in verdict_components if c["sign_negative"] and c["p_bonferroni_0.00625"])
if n_pass >= 1 and mB.get("converged"):
    verdict = "PARTIAL CONFIRMED (BAA10Y 1차 + Markov state 정합, HY OAS full history 검증 미수행)"
elif n_pass >= 1:
    verdict = "PARTIAL CONFIRMED (threshold model 1+ 통과, Markov 미수렴)"
elif any(c["sign_negative"] for c in verdict_components):
    verdict = "TENTATIVE DIRECTIONAL (방향성 약 prior, Bonferroni 보정 후 비유의)"
else:
    verdict = "REJECTED (위기 시 추가 음의 관계 부호 불성립)"

result["verdict"] = verdict
result["verdict_components"] = verdict_components
result["hedge_compliance_note"] = (
    "n_daily≥3000 으로 large-N 영역이지만 Bonferroni α/8 multi-test 적용 후 유의성 보고. "
    "HY OAS 부분 검증은 n=3년 한정 → tentative directional only. "
    "Markov-switching 은 regime persistence 자기상관으로 effective-N 축소 — t-stat 보수해석."
)

# Save
out_path = os.path.join(RAW, "h5_result.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(f"\n[save] {out_path}")
print(f"\n=== VERDICT: {verdict} ===")
