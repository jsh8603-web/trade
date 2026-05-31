"""
H6 검증 — breakeven common-cause + 항등식 게이트.
basis {real_rate, breakeven} (nominal 제외) partial-corr 에서:
  gold-BE |partial| < 0.20 AND gold-real |partial| > 0.20 → H6 SUPPORTED (BE 가 common_cause 매개, 직접 효과 부재)
  inverse → 독립 인플레기대 채널 지지 (BE force_include 승격 정당)

항등식 게이트:
  nominal=real+BE 항등식. basis 에 nominal+real+BE 셋 동시 포함 시 condition number 발산 + VIF→∞ → glasso 무효.
  Q2 합의: {real_rate, breakeven} 채택, nominal 제외.

입력: fred_dfii10·t10yie·dgs10·dtwexbgs + GLD
산출: stdout + raw/h6_result.json
"""
import json, os
import numpy as np
import pandas as pd

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
be   = load_fred("fred_t10yie.csv", "breakeven")
nom  = load_fred("fred_dgs10.csv", "nominal")
dol  = load_fred("fred_dtwexbgs.csv", "dollar")
gld  = load_gld()
df = pd.concat([real, be, nom, dol, gld], axis=1).loc["2010-01-01":].ffill().dropna()
print(f"[load] n={len(df)} range={df.index.min().date()}~{df.index.max().date()}")

chg = pd.DataFrame(index=df.index)
chg["d_real_bp"] = df["real_rate"].diff() * 100.0
chg["d_be_bp"] = df["breakeven"].diff() * 100.0
chg["d_nom_bp"] = df["nominal"].diff() * 100.0
chg["r_dollar"] = np.log(df["dollar"]).diff()
chg["r_gold"] = np.log(df["gold"]).diff()
chg = chg.dropna()
print(f"[delta] n={len(chg)}")

# === (1) 항등식 확인: nominal ≈ real + breakeven ===
nom_check = chg["d_real_bp"] + chg["d_be_bp"]
diff_nom = chg["d_nom_bp"] - nom_check
print(f"\n=== (1) 항등식 확인 nominal ≈ real + BE ===")
print(f"  diff (d_nom - (d_real+d_be)): mean={diff_nom.mean():.4f} std={diff_nom.std():.4f} max|diff|={diff_nom.abs().max():.2f} bp")
print(f"  → 항등식 거의 정확 (소수 디지트 오차)")

# === (2) basis A: {real_rate, breakeven, dollar} (Q2 채택) partial-corr ===
def partial_corr_matrix(X_cols, chg_df):
    M = chg_df[X_cols].dropna().values
    if M.shape[0] < 30: return None
    K = M.shape[1]
    cov = np.cov(M.T)
    try:
        P = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        return None
    pc = np.zeros((K, K))
    for i in range(K):
        for k in range(K):
            if i == k: pc[i, k] = 1.0
            else: pc[i, k] = -P[i, k] / np.sqrt(P[i, i] * P[k, k])
    return pd.DataFrame(pc, index=X_cols, columns=X_cols)

print("\n=== (2) basis A: {real_rate, breakeven, dollar, gold} partial-corr ===")
basis_A = ["d_real_bp", "d_be_bp", "r_dollar", "r_gold"]
pcA = partial_corr_matrix(basis_A, chg)
print(pcA.round(4).to_string())
gold_real_pc_A = pcA.loc["r_gold", "d_real_bp"]
gold_be_pc_A = pcA.loc["r_gold", "d_be_bp"]
gold_dollar_pc_A = pcA.loc["r_gold", "r_dollar"]
print(f"  → gold-real partial = {gold_real_pc_A:+.4f}, gold-BE partial = {gold_be_pc_A:+.4f}, gold-dollar partial = {gold_dollar_pc_A:+.4f}")

# === (3) basis B (위반): {nominal, real, BE, dollar, gold} — 항등식 게이트 fail 확인 ===
print("\n=== (3) basis B: {nominal, real, BE, dollar, gold} — 항등식 게이트 검증 ===")
basis_B = ["d_nom_bp", "d_real_bp", "d_be_bp", "r_dollar", "r_gold"]
M_B = chg[basis_B].dropna().values
cov_B = np.cov(M_B.T)
cond_B = np.linalg.cond(cov_B)
print(f"  cov condition number = {cond_B:.2e}")
print(f"  → {'★발산 (≥1e10): 항등식 collinearity 실증' if cond_B > 1e10 else 'condition OK'}")
try:
    P_B = np.linalg.inv(cov_B)
    print(f"  precision matrix 추정 가능 (단 의미 없음 — perfect collinearity 위에서)")
    pcB = pd.DataFrame(np.zeros((5,5)), index=basis_B, columns=basis_B)
    for i in range(5):
        for k in range(5):
            if i==k: pcB.iloc[i,k]=1.0
            else: pcB.iloc[i,k] = -P_B[i,k]/np.sqrt(P_B[i,i]*P_B[k,k])
    print(pcB.round(4).to_string())
except Exception as e:
    print(f"  precision matrix invert 실패: {e}")

# === (4) VIF 비교: basis A vs B ===
print("\n=== (4) VIF for basis A (Q2 채택) vs basis B (위반) ===")
def vif_calc(X):
    """X = numpy array (N, K). Return VIF per col."""
    K = X.shape[1]
    vifs = []
    for i in range(K):
        Xj = np.delete(X, i, axis=1)
        from statsmodels.regression.linear_model import OLS
        from statsmodels.tools.tools import add_constant
        Xjc = add_constant(Xj)
        r2j = OLS(X[:, i], Xjc).fit().rsquared
        vifs.append(1.0 / max(1e-12, 1.0 - r2j))
    return vifs

# basis A regressors (excluding gold)
A_regs = ["d_real_bp", "d_be_bp", "r_dollar"]
X_A = chg[A_regs].dropna().values
vifs_A = vif_calc(X_A)
print(f"  basis A {A_regs}: VIF = {[f'{v:.3f}' for v in vifs_A]}")

# basis B regressors (excluding gold)
B_regs = ["d_nom_bp", "d_real_bp", "d_be_bp", "r_dollar"]
X_B = chg[B_regs].dropna().values
vifs_B = vif_calc(X_B)
print(f"  basis B {B_regs}: VIF = {[f'{v:.3f}' for v in vifs_B]}")

# === (5) H6 verdict ===
print("\n=== (5) H6 verdict ===")
H6_BE_weak = abs(gold_be_pc_A) < 0.20
H6_REAL_strong = abs(gold_real_pc_A) > 0.20
H6_SUPPORTED = H6_BE_weak and H6_REAL_strong
print(f"  gold-BE partial |corr|={abs(gold_be_pc_A):.4f} < 0.20 = {H6_BE_weak}")
print(f"  gold-real partial |corr|={abs(gold_real_pc_A):.4f} > 0.20 = {H6_REAL_strong}")
print(f"  ★ H6 verdict = {'SUPPORTED (BE common-cause, real_rate 직접)' if H6_SUPPORTED else 'PARTIAL or REJECTED'}")

# === 박제 ===
result = {
    "n_obs": int(len(chg)),
    "identity_check": {
        "diff_d_nom_minus_d_real_plus_d_be_mean_bp": float(diff_nom.mean()),
        "diff_std_bp": float(diff_nom.std()),
        "max_abs_diff_bp": float(diff_nom.abs().max()),
        "approx_identity_holds": bool(diff_nom.abs().max() < 1.0),
    },
    "basis_A_partial_corr": {
        "gold_real_rate": float(gold_real_pc_A),
        "gold_breakeven": float(gold_be_pc_A),
        "gold_dollar": float(gold_dollar_pc_A),
        "real_breakeven": float(pcA.loc["d_real_bp", "d_be_bp"]),
        "real_dollar": float(pcA.loc["d_real_bp", "r_dollar"]),
        "breakeven_dollar": float(pcA.loc["d_be_bp", "r_dollar"]),
    },
    "basis_B_collinearity_gate": {
        "cov_condition_number": float(cond_B),
        "gate_fail_condition_gt_1e10": bool(cond_B > 1e10),
    },
    "vif_comparison": {
        "basis_A_regs": A_regs, "vifs_A": [float(v) for v in vifs_A],
        "basis_B_regs": B_regs, "vifs_B": [float(v) for v in vifs_B],
    },
    "H6_verdict": {
        "gold_BE_partial_weak": bool(H6_BE_weak),
        "gold_real_partial_strong": bool(H6_REAL_strong),
        "supported": bool(H6_SUPPORTED),
    },
}
with open(os.path.join(RAW, "h6_result.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, default=str)
print(f"\n[save] raw/h6_result.json")
