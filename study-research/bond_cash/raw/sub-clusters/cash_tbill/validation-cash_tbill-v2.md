# validation-cash_tbill-v2 — cash_tbill (BIL) v2 격하·재검정 (2026-05-31)

> ★ main 12축 audit verdict 격하 5건 반영 (raw/evaluation-bond_cash-20260531.md).
> v1 산출 (`validation-cash_tbill.md`) 와 병행. v2 = stationary 차분 driver + BH-FDR + half-split OOS + magnitude freeze.

## §0 v1 → v2 변경점
- driver: T10Y2Y level / ACM_TP10 level → **T10Y2Y_d20 / ACM_TP10_d20 차분** (★ non-stationary spurious 차단, ADF p_lev T10Y2Y=0.553 → diff 5pct PASS)
- 다중검정: Bonferroni α/420 (보수) → **BH-FDR q=0.1 on effective ~84** (PCA 4 component / 5 driver)
- HAC lag: f → **max(2f, 60)** (overlap nested 보수)
- verdict: magnitude prior 박제 ★금지★ → **sign/direction prior only** (4 라벨 → sign_prior_robust / fdr_pass_sign_unstable / sign_prior_descriptive / no_signal)
- regime cell: walk-forward OOS 부재 → **descriptive only 격하** (v1 의 regime_conditional_findings bonferroni_pass=true 박제 ★취소★)

## §1 sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | cash_tbill |
| 대표 ETF | BIL (duration ≈ 0.1, credit AAA) |
| n_panel | 4,580 |

## §2 Rank-IC (v2 차분 driver + HAC lag 2× + half-split OOS + BH-FDR)
| driver       |   fwd |    n |      ic |    ic_p |   ci_lo |   ci_hi |      beta |   hac_se |   hac_t_lag2x |   hac_p |   ic_is |   ic_oos |   halfsplit_sign_match | sign_prior   | fdr_pass   | verdict_v2             |
|:-------------|------:|-----:|--------:|--------:|--------:|--------:|----------:|---------:|--------------:|--------:|--------:|---------:|-----------------------:|:-------------|:-----------|:-----------------------|
| MOVE_Z       |     5 | 4580 | -0.0493 | 0.00084 | -0.1373 |  0.054  | -3e-05    | 2.2e-05  |        -1.343 | 0.17932 |  0.0241 |  -0.2283 |                      0 | -            | False      | no_signal              |
| MOVE_Z       |    20 | 4580 | -0.0705 | 0       | -0.1764 |  0.0426 | -0.000112 | 8.5e-05  |        -1.31  | 0.19007 |  0.0046 |  -0.2359 |                      0 | -            | False      | no_signal              |
| MOVE_Z       |    60 | 4580 | -0.0815 | 0       | -0.2283 |  0.0835 | -0.000312 | 0.000297 |        -1.051 | 0.29326 | -0.0382 |  -0.2232 |                      1 | -            | False      | sign_prior_descriptive |
| ACM_TP10_d20 |     5 | 4580 |  0.0607 | 4e-05   | -0.0237 |  0.1517 |  0.000126 | 8.3e-05  |         1.518 | 0.12891 |  0.0782 |   0.023  |                      1 | +            | False      | sign_prior_descriptive |
| ACM_TP10_d20 |    20 | 4580 |  0.0735 | 0       | -0.0241 |  0.1738 |  0.000412 | 0.000299 |         1.377 | 0.16839 |  0.1435 |   0.0124 |                      1 | +            | False      | sign_prior_descriptive |
| ACM_TP10_d20 |    60 | 4580 |  0.0617 | 3e-05   | -0.0641 |  0.167  |  0.000872 | 0.000867 |         1.006 | 0.31441 |  0.1109 |   0.0383 |                      1 | +            | False      | sign_prior_descriptive |
| DGS10_chg20  |     5 | 4580 |  0.0075 | 0.60995 | -0.074  |  0.0911 |  3.8e-05  | 0.000102 |         0.368 | 0.71291 |  0.0485 |  -0.0708 |                      0 | +            | False      | no_signal              |
| DGS10_chg20  |    20 | 4580 |  0.0368 | 0.0128  | -0.0575 |  0.1332 |  0.000102 | 0.000371 |         0.275 | 0.78315 |  0.1193 |  -0.07   |                      0 | +            | False      | no_signal              |
| DGS10_chg20  |    60 | 4580 |  0.0473 | 0.00135 | -0.0624 |  0.1537 |  0.000514 | 0.000932 |         0.551 | 0.58148 |  0.0985 |  -0.0352 |                      0 | +            | False      | no_signal              |
| T10Y2Y_d20   |     5 | 4580 |  0.0779 | 0       | -0.0061 |  0.1653 |  0.000228 | 0.00014  |         1.632 | 0.10277 |  0.1021 |   0.0943 |                      1 | +            | False      | sign_prior_descriptive |
| T10Y2Y_d20   |    20 | 4580 |  0.067  | 1e-05   | -0.0297 |  0.166  |  0.000712 | 0.000503 |         1.418 | 0.15624 |  0.1535 |   0.0649 |                      1 | +            | False      | sign_prior_descriptive |
| T10Y2Y_d20   |    60 | 4580 |  0.0367 | 0.01307 | -0.0932 |  0.1385 |  0.001248 | 0.001485 |         0.84  | 0.40071 |  0.1292 |   0.0606 |                      1 | +            | False      | sign_prior_descriptive |
| BAA10Y_chg20 |     5 | 4580 |  0.0063 | 0.66919 | -0.0685 |  0.0823 | -1e-05    | 7.5e-05  |        -0.128 | 0.89796 | -0.0177 |   0.0561 |                      0 | +            | False      | no_signal              |
| BAA10Y_chg20 |    20 | 4580 | -0.0207 | 0.1621  | -0.1136 |  0.0658 |  2.9e-05  | 0.000278 |         0.105 | 0.91625 | -0.109  |   0.0666 |                      0 | -            | False      | no_signal              |
| BAA10Y_chg20 |    60 | 4580 | -0.0211 | 0.15307 | -0.1444 |  0.0777 | -1.5e-05  | 0.000886 |        -0.017 | 0.98671 | -0.0909 |   0.0505 |                      0 | -            | False      | no_signal              |

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
