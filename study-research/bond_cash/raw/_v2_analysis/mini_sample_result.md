# mini sample 결과 — TLT forward 20d × MOVE Z (2026-05-31)

## 데이터 coverage (small-N rigor §1.1)
- TLT inception 2002-07-30, MOVE yfinance start 2002-11-12 → **aligned start = 2002-11-12**, end = 2026-05-29
- aligned n_days = 5,821
- effective n_obs (after rolling 252 + fwd 20 + dropna) = **5,550**

## spec↔code 1:1 (small-N rigor §1.3)
| axis | spec | code |
|---|---|---|
| 시제 | MOVE 동일일 → TLT 향후 20d 누적 return (predictive) | `df["TLT_AdjClose"].pct_change(20).shift(-20)` ✅ predictive 20d forward |
| frequency | daily | daily ✅ |
| transform | MOVE = rolling 252 z-score / TLT = simple 20d cumulative return | matches ✅ |
| conditioning | unconditional | unconditional ✅ |
| regime | full sample (regime split = Phase 5 본격) | full ✅ |

## Spearman Rank-IC
- IC = **+0.0141**, raw p = 0.2945, n = 5,550

## OLS β (HAC SE, lag=20)
- β = **+0.000760**, HAC SE = 0.001460
- HAC t = **+0.520** (gate |t|>2.0: FAIL)
- HAC p = 0.6028
- 95% CI = [-0.002101, +0.003621]

## MOVE_Z quintile bucket
```
                 mean       std  count  t_vs_zero
MOVE_Z_q                                         
Q1_low_vol  -0.000974  0.032272   1110  -1.005957
Q2           0.004024  0.033021   1110   4.059947
Q3_mid       0.003637  0.037019   1110   3.272860
Q4           0.008029  0.039110   1110   6.840037
Q5_high_vol  0.002186  0.046432   1110   1.568550
```

## AUDIT-GUIDE B축 gate
- rank_ic_gate (>0.03): FAIL
- hac_t_gate (>2.0): FAIL
- rank_ic_p_gate (<0.05): FAIL
- hac_p_gate (<0.05): FAIL

## verdict (TENTATIVE DIRECTIONAL)
- **TENTATIVE DIRECTIONAL** (small-N rigor §2 라벨 5단계)
- 점추정 prior 박제 ★금지★ — Phase 5 본격 시 Block Bootstrap CI + Bonferroni (sub-cluster × 지표 × regime cell) 적용 필수.

## 다음 단계 (Phase 5 본격)
- 7 sub-cluster × MOVE_Z + ACM_TP10 + DGS10_chg + HY OAS + curve 5 driver × forward 5d/20d/60d × regime cell (4 IC국면)
- 다중 비교 = 7 × 5 × 3 × 4 = 420 tests → Bonferroni α/420 ≈ 0.00012 임계
- Newey-West HAC + Block Bootstrap (block = max(autocorr decay, n/10))
