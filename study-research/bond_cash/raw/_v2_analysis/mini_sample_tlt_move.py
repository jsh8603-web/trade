"""mini_sample_tlt_move.py — Phase 5 mechanism 검증 sample 1건 (2026-05-31, btn-powerbi).

목표: TLT (tsy_long sleeve 대표) forward 20d return vs MOVE Z-score 의
       Spearman Rank-IC + Newey-West HAC t-stat.
       AUDIT-GUIDE B축 (실데이터 Rank-IC + t>2.0 HAC SE) 게이트 검증 시제품.

★ 본 sample 결과 = 단정 X (tentative directional). small-N rigor:
  (a) p-value + n 명기
  (b) ≥4 비교 시 Bonferroni — 본 sample = 단일 spec → 보정 N=1 (다중 비교 X)
  (c) 95% CI 박제 (Newey-West HAC SE bootstrap)
  (d) hedge 어휘 (단정 금지 list 회피)
  (e) 점추정 prior 박제 금지 (분포 + CI 보고)
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

# --- load ----------------------------------------------------------------
tlt = pd.read_parquet(DATA / "YF_TLT.parquet")
move = pd.read_parquet(DATA / "YF_MOVE.parquet")

# TLT total return: Adj Close (배당 재투자)
tlt_close = tlt["TLT_adj_close"].rename("TLT_AdjClose")
move_close = move["^MOVE_close"].rename("MOVE_Close")

# --- align daily ---------------------------------------------------------
df = pd.concat([tlt_close, move_close], axis=1).dropna()
print(f"aligned period: {df.index.min().date()} ~ {df.index.max().date()}, n_days = {len(df):,}")

# --- features ------------------------------------------------------------
FWD = 20  # forward 20 trading days return
WIN_Z = 252  # rolling 1y Z-score

df["TLT_fwd20"] = df["TLT_AdjClose"].pct_change(FWD).shift(-FWD)
df["MOVE_Z"] = (df["MOVE_Close"] - df["MOVE_Close"].rolling(WIN_Z).mean()) / df["MOVE_Close"].rolling(WIN_Z).std()

panel = df[["MOVE_Z", "TLT_fwd20"]].dropna()
n_obs = len(panel)
print(f"effective n_obs (after dropna) = {n_obs:,}")

# --- Spearman Rank-IC ----------------------------------------------------
ic, ic_p = stats.spearmanr(panel["MOVE_Z"], panel["TLT_fwd20"])
print(f"\n[Spearman Rank-IC]  MOVE_Z → TLT_fwd20")
print(f"  IC = {ic:+.4f}   raw p = {ic_p:.4g}   n = {n_obs:,}")

# --- Newey-West HAC t-stat on linear corr (small-N rigor §1.4) -----------
# OLS y = β·x + ε, β t-stat with HAC SE (Bartlett kernel, lag = FWD due overlap).
import statsmodels.api as sm
x = sm.add_constant(panel["MOVE_Z"].values)
y = panel["TLT_fwd20"].values
ols = sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": FWD})
beta = ols.params[1]
beta_se_hac = ols.bse[1]
beta_t_hac = ols.tvalues[1]
beta_p_hac = ols.pvalues[1]
ci_lo, ci_hi = ols.conf_int(alpha=0.05)[1]
print(f"\n[OLS β with HAC SE (lag={FWD})]")
print(f"  β       = {beta:+.6f}")
print(f"  HAC SE  = {beta_se_hac:.6f}")
print(f"  HAC t   = {beta_t_hac:+.3f}  (gate: |t| > 2.0 ?  {'PASS' if abs(beta_t_hac) > 2.0 else 'FAIL'})")
print(f"  HAC p   = {beta_p_hac:.4g}")
print(f"  95% CI  = [{ci_lo:+.6f}, {ci_hi:+.6f}]")

# --- bucket analysis (MOVE Z quintile → mean fwd20 return) ---------------
panel["MOVE_Z_q"] = pd.qcut(panel["MOVE_Z"], 5, labels=["Q1_low_vol", "Q2", "Q3_mid", "Q4", "Q5_high_vol"])
bucket = panel.groupby("MOVE_Z_q", observed=True)["TLT_fwd20"].agg(["mean", "std", "count"])
bucket["t_vs_zero"] = bucket["mean"] / (bucket["std"] / np.sqrt(bucket["count"]))
print(f"\n[bucket: MOVE_Z quintile → mean TLT fwd20 return]")
print(bucket.to_string())

# --- AUDIT-GUIDE B축 게이트 평가 -----------------------------------------
b_gate = {
    "rank_ic_gate (>0.03)":   abs(ic) > 0.03,
    "hac_t_gate (>2.0)":      abs(beta_t_hac) > 2.0,
    "rank_ic_p_gate (<0.05)": ic_p < 0.05,
    "hac_p_gate (<0.05)":     beta_p_hac < 0.05,
}
print(f"\n[AUDIT-GUIDE B축 gate]")
for k, v in b_gate.items():
    print(f"  {k:30s}: {'PASS' if v else 'FAIL'}")

# --- verdict label (5단계) -----------------------------------------------
all_pass = all(b_gate.values()) and n_obs >= 100
if all_pass and n_obs >= 100 and ic_p < 0.001:
    verdict = "★CONFIRMED 강력"
elif all_pass:
    verdict = "CONFIRMED"
elif sum(b_gate.values()) >= 2:
    verdict = "PARTIAL CONFIRMED"
elif abs(ic) > 0.01:
    verdict = "TENTATIVE DIRECTIONAL"
else:
    verdict = "★REJECTED"
print(f"\n[verdict] {verdict}  (small-N rigor §2 라벨)")

# --- summary save --------------------------------------------------------
out_md = ROOT / "mini_sample_result.md"
out_md.write_text(
    f"""# mini sample 결과 — TLT forward 20d × MOVE Z (2026-05-31)

## 데이터 coverage (small-N rigor §1.1)
- TLT inception 2002-07-30, MOVE yfinance start 2002-11-12 → **aligned start = {df.index.min().date()}**, end = {df.index.max().date()}
- aligned n_days = {len(df):,}
- effective n_obs (after rolling 252 + fwd 20 + dropna) = **{n_obs:,}**

## spec↔code 1:1 (small-N rigor §1.3)
| axis | spec | code |
|---|---|---|
| 시제 | MOVE 동일일 → TLT 향후 20d 누적 return (predictive) | `df["TLT_AdjClose"].pct_change(20).shift(-20)` ✅ predictive 20d forward |
| frequency | daily | daily ✅ |
| transform | MOVE = rolling 252 z-score / TLT = simple 20d cumulative return | matches ✅ |
| conditioning | unconditional | unconditional ✅ |
| regime | full sample (regime split = Phase 5 본격) | full ✅ |

## Spearman Rank-IC
- IC = **{ic:+.4f}**, raw p = {ic_p:.4g}, n = {n_obs:,}

## OLS β (HAC SE, lag={FWD})
- β = **{beta:+.6f}**, HAC SE = {beta_se_hac:.6f}
- HAC t = **{beta_t_hac:+.3f}** (gate |t|>2.0: {'PASS' if abs(beta_t_hac) > 2.0 else 'FAIL'})
- HAC p = {beta_p_hac:.4g}
- 95% CI = [{ci_lo:+.6f}, {ci_hi:+.6f}]

## MOVE_Z quintile bucket
```
{bucket.to_string()}
```

## AUDIT-GUIDE B축 gate
{chr(10).join(f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in b_gate.items())}

## verdict ({verdict})
- **{verdict}** (small-N rigor §2 라벨 5단계)
- 점추정 prior 박제 ★금지★ — Phase 5 본격 시 Block Bootstrap CI + Bonferroni (sub-cluster × 지표 × regime cell) 적용 필수.

## 다음 단계 (Phase 5 본격)
- 7 sub-cluster × MOVE_Z + ACM_TP10 + DGS10_chg + HY OAS + curve 5 driver × forward 5d/20d/60d × regime cell (4 IC국면)
- 다중 비교 = 7 × 5 × 3 × 4 = 420 tests → Bonferroni α/420 ≈ 0.00012 임계
- Newey-West HAC + Block Bootstrap (block = max(autocorr decay, n/10))
""",
    encoding="utf-8",
)
print(f"\n[saved] {out_md}")
