# validation-tsy_short-v2 — tsy_short (SHY) v2 격하·재검정 (2026-05-31)

> ★ main 12축 audit verdict 격하 5건 반영 (raw/evaluation-bond_cash-20260531.md).
> v1 산출 (`validation-tsy_short.md`) 와 병행. v2 = stationary 차분 driver + BH-FDR + half-split OOS + magnitude freeze.

## §0 v1 → v2 변경점
- driver: T10Y2Y level / ACM_TP10 level → **T10Y2Y_d20 / ACM_TP10_d20 차분** (★ non-stationary spurious 차단, ADF p_lev T10Y2Y=0.553 → diff 5pct PASS)
- 다중검정: Bonferroni α/420 (보수) → **BH-FDR q=0.1 on effective ~84** (PCA 4 component / 5 driver)
- HAC lag: f → **max(2f, 60)** (overlap nested 보수)
- verdict: magnitude prior 박제 ★금지★ → **sign/direction prior only** (4 라벨 → sign_prior_robust / fdr_pass_sign_unstable / sign_prior_descriptive / no_signal)
- regime cell: walk-forward OOS 부재 → **descriptive only 격하** (v1 의 regime_conditional_findings bonferroni_pass=true 박제 ★취소★)

## §1 sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | tsy_short |
| 대표 ETF | SHY (duration ≈ 2, credit AAA) |
| n_panel | 4,580 |

## §2 Rank-IC (v2 차분 driver + HAC lag 2× + half-split OOS + BH-FDR)
| driver       |   fwd |    n |      ic |    ic_p |   ci_lo |   ci_hi |      beta |   hac_se |   hac_t_lag2x |   hac_p |   ic_is |   ic_oos |   halfsplit_sign_match | sign_prior   | fdr_pass   | verdict_v2             |
|:-------------|------:|-----:|--------:|--------:|--------:|--------:|----------:|---------:|--------------:|--------:|--------:|---------:|-----------------------:|:-------------|:-----------|:-----------------------|
| MOVE_Z       |     5 | 4580 | -0.009  | 0.54202 | -0.0839 |  0.0498 |  1e-06    | 7.2e-05  |         0.013 | 0.98937 |  0.042  |  -0.0552 |                      0 | -            | False      | no_signal              |
| MOVE_Z       |    20 | 4580 | -0.0398 | 0.00713 | -0.15   |  0.0506 | -0.000115 | 0.000257 |        -0.449 | 0.65322 |  0.0864 |  -0.1497 |                      0 | -            | False      | no_signal              |
| MOVE_Z       |    60 | 4580 | -0.129  | 0       | -0.2933 |  0.0239 | -0.001021 | 0.000676 |        -1.51  | 0.13108 | -0.0089 |  -0.2464 |                      1 | -            | False      | sign_prior_descriptive |
| ACM_TP10_d20 |     5 | 4580 |  0.0306 | 0.03823 | -0.0332 |  0.0877 |  0.000215 | 0.000238 |         0.904 | 0.36606 |  0.0317 |   0.033  |                      1 | +            | False      | sign_prior_descriptive |
| ACM_TP10_d20 |    20 | 4580 |  0.0524 | 0.00039 | -0.0434 |  0.1445 |  0.00146  | 0.000909 |         1.606 | 0.10838 |  0.0573 |   0.0301 |                      1 | +            | False      | sign_prior_descriptive |
| ACM_TP10_d20 |    60 | 4580 |  0.0534 | 0.0003  | -0.0491 |  0.1583 |  0.004198 | 0.001713 |         2.45  | 0.01427 |  0.0139 |   0.0966 |                      1 | +            | False      | sign_prior_descriptive |
| DGS10_chg20  |     5 | 4580 |  0.0051 | 0.73232 | -0.0574 |  0.0717 | -0.000124 | 0.000263 |        -0.471 | 0.63733 |  0.0619 |  -0.0463 |                      0 | +            | False      | no_signal              |
| DGS10_chg20  |    20 | 4580 | -0.0169 | 0.2531  | -0.1183 |  0.074  | -0.000474 | 0.001004 |        -0.473 | 0.63655 |  0.0662 |  -0.1035 |                      0 | -            | False      | no_signal              |
| DGS10_chg20  |    60 | 4580 | -0.0071 | 0.6321  | -0.1117 |  0.1052 |  0.000609 | 0.001859 |         0.327 | 0.74331 |  0.0547 |  -0.0496 |                      0 | -            | False      | no_signal              |
| T10Y2Y_d20   |     5 | 4580 |  0.0838 | 0       |  0.0192 |  0.1394 |  0.000654 | 0.000405 |         1.616 | 0.10619 |  0.0731 |   0.0937 |                      1 | +            | False      | sign_prior_descriptive |
| T10Y2Y_d20   |    20 | 4580 |  0.1187 | 0       |  0.0231 |  0.2095 |  0.003322 | 0.001413 |         2.351 | 0.01872 |  0.1    |   0.1187 |                      1 | +            | False      | sign_prior_descriptive |
| T10Y2Y_d20   |    60 | 4580 |  0.0924 | 0       | -0.0201 |  0.2005 |  0.007614 | 0.003445 |         2.211 | 0.02707 |  0.0432 |   0.1373 |                      1 | +            | False      | sign_prior_descriptive |
| BAA10Y_chg20 |     5 | 4580 |  0.022  | 0.13739 | -0.0426 |  0.07   |  0.000439 | 0.000302 |         1.455 | 0.14576 | -0.0031 |   0.0463 |                      0 | +            | False      | no_signal              |
| BAA10Y_chg20 |    20 | 4580 |  0.0187 | 0.20577 | -0.0807 |  0.1106 |  0.00137  | 0.00123  |         1.114 | 0.2654  |  0.012  |   0.0309 |                      1 | +            | False      | no_signal              |
| BAA10Y_chg20 |    60 | 4580 | -0.014  | 0.34449 | -0.1338 |  0.1025 |  0.00132  | 0.002477 |         0.533 | 0.59417 | -0.09   |   0.0439 |                      0 | -            | False      | no_signal              |

## §3 verdict 요약 (★ magnitude freeze)
- BH-FDR q=0.1 통과 = **0/15** test
- sign_prior_robust (FDR 통과 AND half-split 부호 일치 AND |IC|>0.03) = **0/15**
- ⛔ 점추정 IC/β magnitude 박제 금지 — sign/direction prior 만 yaml v4 에 진입

## §4 ★ tier (audit 격하 = structural_prior_low_confidence, 전 7 sub-cluster 공통)
- tier = `structural_prior_low_confidence`
- validated_alpha = **false** (★ audit verdict 격하)
- 근거: (a) driver 차분 후 신호 magnitude 소멸 다수 (b) regime cell walk-forward OOS 미수행 (c) ACM vintage 미처리 (D축 PIT 한계)

## §5 D축 PIT 한계 (audit 격하 D=FAIL 대응)
- ACM_TP10 = NY Fed Adrian-Crump-Moench full-history **revised series** (모델 재적합 시 과거 일자 값도 변경).
- 본 v2 = published xlsx (2026-05-31 fetch) 의 latest revision 사용 = **lookahead 잔존 가능성**.
- 정정 옵션: (a) Kim-Wright real-time (FRB H.15 / SSRN replication, R3 후속) (b) ACM monthly publish lag 1-month forward-shift 보수 (c) PIT 한계 명시만.
- 본 v2 산출 = **(c) PIT 한계 명시** (yaml v4 에 박제) — Kim-Wright fetch 는 Phase 7 진입 전 R3 query 우선순위.

## §6 BAA10Y proxy 등급 mismatch (audit hy_credit 지적)
- BAA10Y = Moody's BAA (IG 등급) Δ proxy. **hy_credit 의 HYG = B+/BB (HY)** 와 등급 mismatch.
- 정당화 (audit ✅): BAMLH0A0HYM2 FRED 2023-05~ short sample (786 rows), 1996-2023 historical 부재 (ICE 라이센스). BAA1986~ proxy = DA eq_us_defensive H3 검증 경로 재사용.
- 한계 명시 의무 — yaml v4 confidence_hooks 에 'credit_grade_mismatch' 박제.
