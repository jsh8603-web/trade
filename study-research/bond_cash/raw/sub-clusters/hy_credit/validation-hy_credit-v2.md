# validation-hy_credit-v2 — hy_credit (HYG) v2 격하·재검정 (2026-05-31)

> ★ main 12축 audit verdict 격하 5건 반영 (raw/evaluation-bond_cash-20260531.md).
> v1 산출 (`validation-hy_credit.md`) 와 병행. v2 = stationary 차분 driver + BH-FDR + half-split OOS + magnitude freeze.

## §0 v1 → v2 변경점
- driver: T10Y2Y level / ACM_TP10 level → **T10Y2Y_d20 / ACM_TP10_d20 차분** (★ non-stationary spurious 차단, ADF p_lev T10Y2Y=0.553 → diff 5pct PASS)
- 다중검정: Bonferroni α/420 (보수) → **BH-FDR q=0.1 on effective ~84** (PCA 4 component / 5 driver)
- HAC lag: f → **max(2f, 60)** (overlap nested 보수)
- verdict: magnitude prior 박제 ★금지★ → **sign/direction prior only** (4 라벨 → sign_prior_robust / fdr_pass_sign_unstable / sign_prior_descriptive / no_signal)
- regime cell: walk-forward OOS 부재 → **descriptive only 격하** (v1 의 regime_conditional_findings bonferroni_pass=true 박제 ★취소★)

## §1 sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | hy_credit |
| 대표 ETF | HYG (duration ≈ 4, credit B+/BB) |
| n_panel | 4,580 |

## §2 Rank-IC (v2 차분 driver + HAC lag 2× + half-split OOS + BH-FDR)
| driver       |   fwd |    n |      ic |    ic_p |   ci_lo |   ci_hi |      beta |   hac_se |   hac_t_lag2x |   hac_p |   ic_is |   ic_oos |   halfsplit_sign_match | sign_prior   | fdr_pass   | verdict_v2             |
|:-------------|------:|-----:|--------:|--------:|--------:|--------:|----------:|---------:|--------------:|--------:|--------:|---------:|-----------------------:|:-------------|:-----------|:-----------------------|
| MOVE_Z       |     5 | 4580 |  0.0072 | 0.62503 | -0.0513 |  0.0696 | -0.000255 | 0.000557 |        -0.457 | 0.64748 |  0.0025 |   0.0165 |                      1 | +            | False      | no_signal              |
| MOVE_Z       |    20 | 4580 | -0.0079 | 0.59493 | -0.1108 |  0.0872 | -0.000505 | 0.001317 |        -0.383 | 0.70158 | -0.0143 |   0.0058 |                      0 | -            | False      | no_signal              |
| MOVE_Z       |    60 | 4580 | -0.0026 | 0.85951 | -0.1511 |  0.1409 | -0.000311 | 0.002565 |        -0.121 | 0.90362 |  0.0404 |  -0.0318 |                      0 | -            | False      | no_signal              |
| ACM_TP10_d20 |     5 | 4580 | -0.0595 | 6e-05   | -0.1189 | -0.0014 | -0.006626 | 0.004039 |        -1.641 | 0.1009  | -0.0905 |  -0.0273 |                      1 | -            | False      | sign_prior_descriptive |
| ACM_TP10_d20 |    20 | 4580 | -0.0958 | 0       | -0.1895 |  0.0022 | -0.028751 | 0.013229 |        -2.173 | 0.02976 | -0.205  |   0.0371 |                      0 | -            | False      | no_signal              |
| ACM_TP10_d20 |    60 | 4580 |  0.0408 | 0.00573 | -0.0775 |  0.1447 |  0.00673  | 0.008501 |         0.792 | 0.42851 | -0.0478 |   0.1454 |                      0 | +            | False      | no_signal              |
| DGS10_chg20  |     5 | 4580 | -0.0919 | 0       | -0.154  | -0.0328 | -0.005901 | 0.004113 |        -1.434 | 0.15143 | -0.0953 |  -0.095  |                      1 | -            | False      | sign_prior_descriptive |
| DGS10_chg20  |    20 | 4580 | -0.1466 | 0       | -0.2384 | -0.0545 | -0.024274 | 0.012619 |        -1.924 | 0.05441 | -0.1955 |  -0.0896 |                      1 | -            | False      | sign_prior_descriptive |
| DGS10_chg20  |    60 | 4580 | -0.0703 | 0       | -0.1916 |  0.0542 | -0.00522  | 0.01204  |        -0.434 | 0.66463 | -0.0844 |  -0.0565 |                      1 | -            | False      | sign_prior_descriptive |
| T10Y2Y_d20   |     5 | 4580 | -0.0202 | 0.17068 | -0.0819 |  0.0366 | -0.007935 | 0.006614 |        -1.2   | 0.23024 | -0.0678 |   0.0335 |                      0 | -            | False      | no_signal              |
| T10Y2Y_d20   |    20 | 4580 | -0.0252 | 0.08785 | -0.1041 |  0.0644 | -0.028379 | 0.02007  |        -1.414 | 0.15736 | -0.144  |   0.1145 |                      0 | -            | False      | no_signal              |
| T10Y2Y_d20   |    60 | 4580 |  0.1264 | 0       |  0.0096 |  0.2351 |  0.029605 | 0.015286 |         1.937 | 0.05277 |  0.0347 |   0.2225 |                      1 | +            | False      | sign_prior_descriptive |
| BAA10Y_chg20 |     5 | 4580 |  0.0687 | 0       |  0.0097 |  0.1356 |  0.003359 | 0.004433 |         0.758 | 0.4486  |  0.0644 |   0.0741 |                      1 | +            | False      | sign_prior_descriptive |
| BAA10Y_chg20 |    20 | 4580 |  0.0914 | 0       | -0.0174 |  0.1967 |  0.008512 | 0.014698 |         0.579 | 0.56247 |  0.085  |   0.1098 |                      1 | +            | False      | sign_prior_descriptive |
| BAA10Y_chg20 |    60 | 4580 |  0.0182 | 0.21836 | -0.1044 |  0.1701 |  0.007498 | 0.017828 |         0.421 | 0.67405 | -0.0402 |   0.1147 |                      0 | +            | False      | no_signal              |

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
