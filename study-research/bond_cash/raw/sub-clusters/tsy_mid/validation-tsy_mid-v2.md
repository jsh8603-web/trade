# validation-tsy_mid-v2 — tsy_mid (IEF) v2 격하·재검정 (2026-05-31)

> ★ main 12축 audit verdict 격하 5건 반영 (raw/evaluation-bond_cash-20260531.md).
> v1 산출 (`validation-tsy_mid.md`) 와 병행. v2 = stationary 차분 driver + BH-FDR + half-split OOS + magnitude freeze.

## §0 v1 → v2 변경점
- driver: T10Y2Y level / ACM_TP10 level → **T10Y2Y_d20 / ACM_TP10_d20 차분** (★ non-stationary spurious 차단, ADF p_lev T10Y2Y=0.553 → diff 5pct PASS)
- 다중검정: Bonferroni α/420 (보수) → **BH-FDR q=0.1 on effective ~84** (PCA 4 component / 5 driver)
- HAC lag: f → **max(2f, 60)** (overlap nested 보수)
- verdict: magnitude prior 박제 ★금지★ → **sign/direction prior only** (4 라벨 → sign_prior_robust / fdr_pass_sign_unstable / sign_prior_descriptive / no_signal)
- regime cell: walk-forward OOS 부재 → **descriptive only 격하** (v1 의 regime_conditional_findings bonferroni_pass=true 박제 ★취소★)

## §1 sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | tsy_mid |
| 대표 ETF | IEF (duration ≈ 8, credit AAA) |
| n_panel | 4,580 |

## §2 Rank-IC (v2 차분 driver + HAC lag 2× + half-split OOS + BH-FDR)
| driver       |   fwd |    n |      ic |    ic_p |   ci_lo |   ci_hi |      beta |   hac_se |   hac_t_lag2x |   hac_p |   ic_is |   ic_oos |   halfsplit_sign_match | sign_prior   | fdr_pass   | verdict_v2             |
|:-------------|------:|-----:|--------:|--------:|--------:|--------:|----------:|---------:|--------------:|--------:|--------:|---------:|-----------------------:|:-------------|:-----------|:-----------------------|
| MOVE_Z       |     5 | 4580 |  0.0087 | 0.5579  | -0.0583 |  0.0618 | -2.2e-05  | 0.000265 |        -0.084 | 0.93278 |  0.0083 |   0.0169 |                      1 | +            | False      | no_signal              |
| MOVE_Z       |    20 | 4580 |  0.0181 | 0.21992 | -0.0897 |  0.1121 |  0.000118 | 0.000983 |         0.12  | 0.90459 |  0.0474 |  -0.0051 |                      0 | +            | False      | no_signal              |
| MOVE_Z       |    60 | 4580 | -0.0599 | 5e-05   | -0.2026 |  0.0771 | -0.001497 | 0.002722 |        -0.55  | 0.58233 | -0.0232 |  -0.1026 |                      1 | -            | False      | sign_prior_descriptive |
| ACM_TP10_d20 |     5 | 4580 |  0.001  | 0.94598 | -0.0577 |  0.0602 | -0.000759 | 0.001109 |        -0.684 | 0.49398 | -0.0089 |   0.0193 |                      0 | +            | False      | no_signal              |
| ACM_TP10_d20 |    20 | 4580 | -0.0115 | 0.43659 | -0.1147 |  0.0846 |  0.002023 | 0.004362 |         0.464 | 0.64276 | -0.0248 |   0.0168 |                      0 | -            | False      | no_signal              |
| ACM_TP10_d20 |    60 | 4580 |  0.0332 | 0.02483 | -0.0743 |  0.1458 |  0.01784  | 0.011154 |         1.599 | 0.10972 | -0.0226 |   0.1124 |                      0 | +            | False      | no_signal              |
| DGS10_chg20  |     5 | 4580 | -0.0071 | 0.63113 | -0.0699 |  0.0542 | -0.001276 | 0.001395 |        -0.914 | 0.36046 |  0.0243 |  -0.0365 |                      0 | -            | False      | no_signal              |
| DGS10_chg20  |    20 | 4580 | -0.0151 | 0.30813 | -0.1166 |  0.0742 | -0.003433 | 0.004049 |        -0.848 | 0.39654 |  0.0452 |  -0.0701 |                      0 | -            | False      | no_signal              |
| DGS10_chg20  |    60 | 4580 | -0.0262 | 0.07655 | -0.131  |  0.0898 | -0.000598 | 0.007451 |        -0.08  | 0.93598 | -0.0109 |  -0.0348 |                      1 | -            | False      | no_signal              |
| T10Y2Y_d20   |     5 | 4580 |  0.0257 | 0.08253 | -0.03   |  0.079  | -0.000229 | 0.001888 |        -0.121 | 0.90356 |  0.0172 |   0.0345 |                      1 | +            | False      | no_signal              |
| T10Y2Y_d20   |    20 | 4580 |  0.0176 | 0.23491 | -0.0803 |  0.1133 |  0.004312 | 0.006011 |         0.717 | 0.47314 | -0.0162 |   0.0563 |                      0 | +            | False      | no_signal              |
| T10Y2Y_d20   |    60 | 4580 |  0.0592 | 6e-05   | -0.0669 |  0.191  |  0.027538 | 0.017492 |         1.574 | 0.11542 | -0.0243 |   0.1512 |                      0 | +            | False      | no_signal              |
| BAA10Y_chg20 |     5 | 4580 |  0.0568 | 0.00012 | -0.0016 |  0.1105 |  0.0024   | 0.001325 |         1.81  | 0.07022 |  0.0469 |   0.0643 |                      1 | +            | False      | sign_prior_descriptive |
| BAA10Y_chg20 |    20 | 4580 |  0.0566 | 0.00013 | -0.0376 |  0.1402 |  0.009578 | 0.005157 |         1.857 | 0.06328 |  0.0425 |   0.0685 |                      1 | +            | False      | sign_prior_descriptive |
| BAA10Y_chg20 |    60 | 4580 |  0.0494 | 0.00082 | -0.0652 |  0.1622 |  0.016932 | 0.013909 |         1.217 | 0.22346 |  0.0243 |   0.0788 |                      1 | +            | False      | sign_prior_descriptive |

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
