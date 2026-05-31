"""
H8 검증 — 이중 e-process + ordering falsification (R2 Q6 합의).

설계:
  e-process = anytime-valid test, Ville's inequality: under H_0, P(sup_t e_t ≥ 1/α) ≤ α
  e_t = ∏_{s=1}^t m_s with E[m_s | F_{s-1}] ≤ 1 under H_0
  단순 GROW betting (Grünwald 2024): m_s = 1 + λ · (z_s² - 1) where z_s ~ N(0,1) under H_0
    → E[m_s | H_0] = 1 + λ·0 = 1 (mean-zero perturbation)
    → e_t martingale → α=0.05 임계 e>20

  H_0_level (균형식 안정): pre-2022 OLS (ln_gold ~ const + real_rate + ln_dollar) 잔차 IID N(0, σ²_pre)
  H_0_dbeta (변화율 β 안정): pre-2022 rolling β (252d) 의 일변동량 z_t IID N(0,1) (정규화)

  Ordering: τ_level = min{t: e_level_t > 20}, τ_dbeta = min{t: e_dbeta_t > 20}
  결론:
    τ_level < τ_dbeta → ★level mechanism 우선 (H2 STRONGLY SUPPORTED 정합)
    τ_dbeta < τ_level → ★변화율 β mechanism 우선
    둘 다 도달 X → 귀무 유지

입력: fred_dfii10 + fred_dtwexbgs + try_yahoo_v8.json
산출: stdout + raw/h8_result.json + raw/h8_eprocess.csv

⚠️ 본 e-process 는 단순 GROW (학습률 λ=0.1 고정). 정식 mixture method (Howard et al 2021) 또는
    universal portfolio adaptive λ 보다 보수적 (lower power, higher Type-I robust).
    Bonferroni α/8 = 0.00625 통합 보정 시 e>1/0.00625 = 160 임계 고려.
"""
import json
import os
import warnings
import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

warnings.filterwarnings("ignore")
RAW = os.path.dirname(os.path.abspath(__file__))

LAMBDA = 0.1  # GROW betting 학습률 (보수적)
BREAK = "2022-01-01"
ETHRESH_A05 = 20  # α=0.05 Ville threshold
ETHRESH_BONF = 160  # α/8=0.00625 Bonferroni 통합


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


def grow_eprocess(z_post, lam=LAMBDA):
    """Sequential e-process e_t = prod(1 + lam·(z_t² - 1))."""
    m = 1 + lam * (z_post ** 2 - 1)
    m = np.clip(m, 1e-9, None)  # negative 방지 (z_t² 매우 작을 때)
    log_e = np.cumsum(np.log(m))
    return np.exp(log_e), m


def find_first_cross(e_arr, thresh):
    cross = np.where(e_arr > thresh)[0]
    return int(cross[0]) if len(cross) > 0 else None


# --- LOAD
real = load_fred("fred_dfii10.csv", "real_rate")
dol = load_fred("fred_dtwexbgs.csv", "dollar")
gld = load_gld()
df = pd.concat([real, dol, gld], axis=1).loc["2010-01-04":].ffill().dropna()
df["ln_gold"] = np.log(df["gold"])
df["ln_dollar"] = np.log(df["dollar"])
df["r_gold"] = df["ln_gold"].diff()
df["d_real"] = df["real_rate"].diff()
df["d_lndol"] = df["ln_dollar"].diff()
df = df.dropna()
n_full = len(df)
print(f"[load] daily n={n_full} range={df.index.min().date()}~{df.index.max().date()}")

# --- Pre-2022 calibration (H_0)
pre = df.loc[df.index < BREAK]
post = df.loc[df.index >= BREAK]
n_pre, n_post = len(pre), len(post)
print(f"[split] pre={n_pre} ({pre.index.min().date()}~{pre.index.max().date()}) | "
      f"post={n_post} ({post.index.min().date()}~{post.index.max().date()})")

# === E-process 1: Level residual (균형식 안정 귀무) ===
print("\n=== E-process 1: Level residual (균형식 안정) ===")
y_pre = pre["ln_gold"].values
X_pre = add_constant(pre[["real_rate", "ln_dollar"]].values)
res_pre = OLS(y_pre, X_pre).fit()
alpha_pre, b_pre, c_pre = res_pre.params
sigma_pre = np.sqrt(np.mean(res_pre.resid ** 2))
print(f"  pre-2022 OLS: α={alpha_pre:.4f}  b(real)={b_pre:.4f}  c(ln$)={c_pre:.4f}  σ={sigma_pre:.4f}")

# Post-2022 residual normalized by pre-σ
y_post = post["ln_gold"].values
X_post = add_constant(post[["real_rate", "ln_dollar"]].values)
yhat_post = X_post @ np.array([alpha_pre, b_pre, c_pre])
resid_post = y_post - yhat_post
z_level = resid_post / sigma_pre
e_level, m_level = grow_eprocess(z_level, lam=LAMBDA)
tau_level_a05 = find_first_cross(e_level, ETHRESH_A05)
tau_level_bonf = find_first_cross(e_level, ETHRESH_BONF)
print(f"  post-2022 잔차 z: mean={z_level.mean():.3f} std={z_level.std():.3f} (귀무 N(0,1) 가정 위반 정도)")
print(f"  e_level final = {e_level[-1]:.3e}")
print(f"  τ_level (e>20, α=0.05) = {tau_level_a05} → "
      f"{post.index[tau_level_a05].date() if tau_level_a05 is not None else 'NOT REACHED'}")
print(f"  τ_level (e>160, Bonf α/8) = {tau_level_bonf} → "
      f"{post.index[tau_level_bonf].date() if tau_level_bonf is not None else 'NOT REACHED'}")

# === E-process 2: Δ-beta (변화율 β 안정 귀무) ===
print("\n=== E-process 2: Δ-beta (변화율 β 안정) ===")
WIN = 252  # rolling window for β
# pre-period: 일별 rolling β (Δgold ~ Δreal + Δlndol)
def rolling_beta(df_, win=WIN):
    betas_real, betas_dol = [], []
    for i in range(win, len(df_)):
        sub = df_.iloc[i - win:i]
        Xs = add_constant(sub[["d_real", "d_lndol"]].values)
        ys = sub["r_gold"].values
        try:
            rs = OLS(ys, Xs).fit()
            betas_real.append(rs.params[1])
            betas_dol.append(rs.params[2])
        except Exception:
            betas_real.append(np.nan)
            betas_dol.append(np.nan)
    return np.array(betas_real), np.array(betas_dol), df_.index[win:]


beta_real_full, beta_dol_full, beta_idx = rolling_beta(df, win=WIN)
beta_pre_mask = beta_idx < pd.Timestamp(BREAK)
beta_real_pre = beta_real_full[beta_pre_mask]
beta_dol_pre = beta_dol_full[beta_pre_mask]
mu_br, sigma_br = np.nanmean(beta_real_pre), np.nanstd(beta_real_pre)
mu_bd, sigma_bd = np.nanmean(beta_dol_pre), np.nanstd(beta_dol_pre)
print(f"  pre-2022 rolling β: real μ={mu_br:.3f} σ={sigma_br:.3f} | dollar μ={mu_bd:.3f} σ={sigma_bd:.3f}")

# Post: z_t = (β_t - μ_pre) / σ_pre, e-process on combined |z|² (sum 2-dim)
beta_post_mask = ~beta_pre_mask
beta_real_post = beta_real_full[beta_post_mask]
beta_dol_post = beta_dol_full[beta_post_mask]
beta_idx_post = beta_idx[beta_post_mask]

# 일별 z (β_t 자체), 단 변화율 β 안정성 검증이므로 increment Δβ_t 사용도 가능
# 보수적: β_t 의 level deviation from pre-mean / pre-sd 가 단발 deviation
z_br = (beta_real_post - mu_br) / max(sigma_br, 1e-6)
z_bd = (beta_dol_post - mu_bd) / max(sigma_bd, 1e-6)
# 결합: z² = (z_br² + z_bd²) / 2 (평균, χ²(2)/2 ≈ chi-bar-1 단위로 정규화)
z_combined_sq = (z_br ** 2 + z_bd ** 2) / 2
# under H_0 E[z²]=1 → m_t = 1 + λ·(z² - 1)
m_dbeta = 1 + LAMBDA * (z_combined_sq - 1)
m_dbeta = np.clip(m_dbeta, 1e-9, None)
log_e_dbeta = np.cumsum(np.log(m_dbeta))
e_dbeta = np.exp(log_e_dbeta)
tau_dbeta_a05 = find_first_cross(e_dbeta, ETHRESH_A05)
tau_dbeta_bonf = find_first_cross(e_dbeta, ETHRESH_BONF)
print(f"  post-2022 β z_real mean={z_br.mean():.3f} std={z_br.std():.3f}")
print(f"  post-2022 β z_dol  mean={z_bd.mean():.3f} std={z_bd.std():.3f}")
print(f"  e_dbeta final = {e_dbeta[-1]:.3e}")
print(f"  τ_dbeta (e>20, α=0.05) = {tau_dbeta_a05} → "
      f"{beta_idx_post[tau_dbeta_a05].date() if tau_dbeta_a05 is not None else 'NOT REACHED'}")
print(f"  τ_dbeta (e>160, Bonf α/8) = {tau_dbeta_bonf} → "
      f"{beta_idx_post[tau_dbeta_bonf].date() if tau_dbeta_bonf is not None else 'NOT REACHED'}")

# === Ordering falsification ===
print("\n=== Ordering falsification ===")
# Date 단위로 비교 (둘의 시작점·길이 다름)
date_level = post.index[tau_level_a05] if tau_level_a05 is not None else None
date_dbeta = beta_idx_post[tau_dbeta_a05] if tau_dbeta_a05 is not None else None

if date_level is not None and date_dbeta is not None:
    if date_level < date_dbeta:
        ordering = f"★ LEVEL mechanism 우선 (τ_level {date_level.date()} < τ_dbeta {date_dbeta.date()}, H2 정합)"
    elif date_dbeta < date_level:
        ordering = f"★ Δ-BETA mechanism 우선 (τ_dbeta {date_dbeta.date()} < τ_level {date_level.date()}, H1 정합)"
    else:
        ordering = f"동시 발화 ({date_level.date()})"
elif date_level is not None:
    ordering = f"★ LEVEL only (τ_level={date_level.date()}, τ_dbeta NOT REACHED, H2 단독 정합)"
elif date_dbeta is not None:
    ordering = f"★ Δ-BETA only (τ_dbeta={date_dbeta.date()}, τ_level NOT REACHED, H1 단독 정합)"
else:
    ordering = "둘 다 NOT REACHED — 귀무 유지 (mechanism 미식별)"
print(f"  {ordering}")

# --- Save
result = {
    "design": "Dual e-process + ordering falsification (Ville's inequality, GROW betting λ=0.1)",
    "data": {
        "source": ["FRED DFII10", "FRED DTWEXBGS", "Yahoo GLD (try_yahoo_v8.json)"],
        "n_total_daily": int(n_full),
        "n_pre_2022": int(n_pre),
        "n_post_2022": int(n_post),
        "date_min": str(df.index.min().date()),
        "date_max": str(df.index.max().date()),
        "break_anchor": BREAK,
    },
    "method": {
        "GROW_lambda": LAMBDA,
        "e_threshold_a05_Ville": ETHRESH_A05,
        "e_threshold_bonferroni_a8": ETHRESH_BONF,
        "rolling_window_dbeta": WIN,
        "betting_formula": "m_t = 1 + λ·(z_t² - 1) under H_0 E[m_t]=1",
        "caveat": "단순 GROW (학습률 고정). mixture method 보다 보수적 (lower power)",
    },
    "eprocess_level_residual": {
        "H0": "ln_gold = α + b·real_rate + c·ln_dollar 균형식 잔차 IID N(0, σ²_pre)",
        "calibration_pre_2022": {
            "alpha": float(alpha_pre),
            "b_real_rate": float(b_pre),
            "c_ln_dollar": float(c_pre),
            "sigma_pre": float(sigma_pre),
        },
        "post_2022_z": {
            "mean": float(z_level.mean()),
            "std": float(z_level.std()),
            "abs_max": float(np.abs(z_level).max()),
            "violation_note": "귀무 N(0,1) 가정 위반 정도 (drift mean + scale std)",
        },
        "e_final": float(e_level[-1]),
        "tau_a05_idx": tau_level_a05,
        "tau_a05_date": str(post.index[tau_level_a05].date()) if tau_level_a05 is not None else None,
        "tau_bonf_idx": tau_level_bonf,
        "tau_bonf_date": str(post.index[tau_level_bonf].date()) if tau_level_bonf is not None else None,
    },
    "eprocess_dbeta": {
        "H0": "rolling 252d β (real, dollar) 의 deviation z IID N(0,1) under pre-2022 calibration",
        "calibration_pre_2022": {
            "mu_beta_real": float(mu_br),
            "sigma_beta_real": float(sigma_br),
            "mu_beta_dollar": float(mu_bd),
            "sigma_beta_dollar": float(sigma_bd),
        },
        "post_2022_z_real": {
            "mean": float(z_br.mean()),
            "std": float(z_br.std()),
            "abs_max": float(np.abs(z_br).max()),
        },
        "post_2022_z_dollar": {
            "mean": float(z_bd.mean()),
            "std": float(z_bd.std()),
            "abs_max": float(np.abs(z_bd).max()),
        },
        "e_final": float(e_dbeta[-1]),
        "tau_a05_idx": tau_dbeta_a05,
        "tau_a05_date": str(beta_idx_post[tau_dbeta_a05].date()) if tau_dbeta_a05 is not None else None,
        "tau_bonf_idx": tau_dbeta_bonf,
        "tau_bonf_date": str(beta_idx_post[tau_dbeta_bonf].date()) if tau_dbeta_bonf is not None else None,
    },
    "ordering_verdict": ordering,
    "attempt_counts": {
        "n_e_processes": 2,
        "n_thresholds": 2,
        "note": "K축 시도횟수 공시: 2 e-process × 2 threshold (α=0.05 + Bonferroni α/8)",
    },
    "verdict_summary": (
        "H8 ordering = " + (
            "LEVEL mechanism 우선 (H2 SUPPORTED), Δ-beta 미발화 / 후순위"
            if (date_level is not None and (date_dbeta is None or date_level < date_dbeta))
            else (
                "Δ-BETA mechanism 우선 (H1 SUPPORTED)" if (date_dbeta is not None and (date_level is None or date_dbeta < date_level))
                else "mechanism 미식별 (귀무 유지)"
            )
        )
    ),
    "hedge_compliance_note": (
        "단순 GROW λ=0.1 은 mixture method 대비 보수적 — e>20 도달은 강한 증거. "
        "Bonferroni α/8=0.00625 통합 보정 시 e>160 임계 별도 보고. "
        "ordering 발화 일자는 mechanism 활성 시점의 lower-bound 추정."
    ),
}

out_json = os.path.join(RAW, "h8_result.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(f"\n[save] {out_json}")

# e-process series CSV
edf = pd.DataFrame({
    "date_level": list(post.index) + [pd.NaT] * max(0, len(e_dbeta) - len(e_level)),
    "e_level": list(e_level) + [np.nan] * max(0, len(e_dbeta) - len(e_level)),
})
# 두 series 길이 맞추기는 복잡 — 별도 두 CSV
pd.DataFrame({"date": post.index, "e_level": e_level, "z_level": z_level}).to_csv(
    os.path.join(RAW, "h8_eprocess_level.csv"), index=False
)
pd.DataFrame({
    "date": beta_idx_post,
    "e_dbeta": e_dbeta,
    "beta_real": beta_real_post,
    "beta_dollar": beta_dol_post,
    "z_combined_sq": z_combined_sq,
}).to_csv(os.path.join(RAW, "h8_eprocess_dbeta.csv"), index=False)
print(f"[save] h8_eprocess_level.csv + h8_eprocess_dbeta.csv")
print(f"\n=== H8 VERDICT: {result['verdict_summary']} ===")
