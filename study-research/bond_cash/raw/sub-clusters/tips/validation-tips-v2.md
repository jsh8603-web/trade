# validation-tips-v2 — tips (TIP) v2 격하·재검정 (2026-05-31)

> ★ main 12축 audit verdict 격하 5건 반영 (raw/evaluation-bond_cash-20260531.md).
> v1 산출 (`validation-tips.md`) 와 병행. v2 = stationary 차분 driver + BH-FDR + half-split OOS + magnitude freeze.

## §0 v1 → v2 변경점
- driver: T10Y2Y level / ACM_TP10 level → **T10Y2Y_d20 / ACM_TP10_d20 차분** (★ non-stationary spurious 차단, ADF p_lev T10Y2Y=0.553 → diff 5pct PASS)
- 다중검정: Bonferroni α/420 (보수) → **BH-FDR q=0.1 on effective ~84** (PCA 4 component / 5 driver)
- HAC lag: f → **max(2f, 60)** (overlap nested 보수)
- verdict: magnitude prior 박제 ★금지★ → **sign/direction prior only** (4 라벨 → sign_prior_robust / fdr_pass_sign_unstable / sign_prior_descriptive / no_signal)
- regime cell: walk-forward OOS 부재 → **descriptive only 격하** (v1 의 regime_conditional_findings bonferroni_pass=true 박제 ★취소★)

## §1 sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | tips |
| 대표 ETF | TIP (duration ≈ 7, credit AAA(TIPS)) |
| n_panel | 4,580 |

## §2 Rank-IC (v2 차분 driver + HAC lag 2× + half-split OOS + BH-FDR)
| driver       |   fwd |    n |      ic |    ic_p |   ci_lo |   ci_hi |      beta |   hac_se |   hac_t_lag2x |   hac_p |   ic_is |   ic_oos |   halfsplit_sign_match | sign_prior   | fdr_pass   | verdict_v2             |
|:-------------|------:|-----:|--------:|--------:|--------:|--------:|----------:|---------:|--------------:|--------:|--------:|---------:|-----------------------:|:-------------|:-----------|:-----------------------|
| MOVE_Z       |     5 | 4580 | -0.0051 | 0.72924 | -0.0619 |  0.0462 | -0.000248 | 0.000238 |        -1.043 | 0.29699 | -0.0189 |   0.0152 |                      0 | -            | False      | no_signal              |
| MOVE_Z       |    20 | 4580 | -0.0026 | 0.85824 | -0.0971 |  0.0915 | -0.000319 | 0.000752 |        -0.424 | 0.67184 |  0.0076 |  -0.0072 |                      0 | -            | False      | no_signal              |
| MOVE_Z       |    60 | 4580 | -0.0685 | 0       | -0.2012 |  0.0682 | -0.001562 | 0.001831 |        -0.853 | 0.3938  | -0.0469 |  -0.0919 |                      1 | -            | False      | sign_prior_descriptive |
| ACM_TP10_d20 |     5 | 4580 | -0.0011 | 0.93831 | -0.0528 |  0.0578 | -0.001241 | 0.001635 |        -0.759 | 0.44772 |  0.004  |  -0.0045 |                      0 | -            | False      | no_signal              |
| ACM_TP10_d20 |    20 | 4580 | -0.0052 | 0.72506 | -0.0852 |  0.0722 | -0.003359 | 0.003362 |        -0.999 | 0.31781 | -0.0316 |   0.0296 |                      0 | -            | False      | no_signal              |
| ACM_TP10_d20 |    60 | 4580 |  0.0029 | 0.84251 | -0.0934 |  0.0933 |  0.005514 | 0.004468 |         1.234 | 0.21717 | -0.0833 |   0.1151 |                      0 | +            | False      | no_signal              |
| DGS10_chg20  |     5 | 4580 |  0.0307 | 0.03757 | -0.0324 |  0.0918 |  8e-06    | 0.001484 |         0.005 | 0.99576 |  0.1023 |  -0.0484 |                      0 | +            | False      | no_signal              |
| DGS10_chg20  |    20 | 4580 |  0.0411 | 0.00545 | -0.0495 |  0.1359 | -0.001552 | 0.003787 |        -0.41  | 0.68202 |  0.1106 |  -0.0338 |                      0 | +            | False      | no_signal              |
| DGS10_chg20  |    60 | 4580 | -0.0179 | 0.22577 | -0.1237 |  0.0896 | -0.001078 | 0.006154 |        -0.175 | 0.86098 |  0.0144 |  -0.0551 |                      0 | -            | False      | no_signal              |
| T10Y2Y_d20   |     5 | 4580 |  0.0248 | 0.09276 | -0.0302 |  0.0783 | -0.00073  | 0.002837 |        -0.257 | 0.7968  |  0.0158 |   0.0347 |                      1 | +            | False      | no_signal              |
| T10Y2Y_d20   |    20 | 4580 |  0.0305 | 0.03883 | -0.0531 |  0.1062 | -0.000771 | 0.006141 |        -0.126 | 0.90009 | -0.0191 |   0.0866 |                      0 | +            | False      | no_signal              |
| T10Y2Y_d20   |    60 | 4580 |  0.0735 | 0       | -0.0384 |  0.1724 |  0.015438 | 0.009552 |         1.616 | 0.10604 | -0.0542 |   0.2226 |                      0 | +            | False      | no_signal              |
| BAA10Y_chg20 |     5 | 4580 | -0.0233 | 0.11565 | -0.0854 |  0.0282 | -1.4e-05  | 0.002699 |        -0.005 | 0.99601 | -0.0768 |   0.0428 |                      0 | -            | False      | no_signal              |
| BAA10Y_chg20 |    20 | 4580 | -0.084  | 0       | -0.1653 | -0.011  | -0.001478 | 0.006593 |        -0.224 | 0.8226  | -0.1444 |  -0.0163 |                      1 | -            | False      | sign_prior_descriptive |
| BAA10Y_chg20 |    60 | 4580 | -0.1039 | 0       | -0.2256 |  0.0053 | -0.002405 | 0.007539 |        -0.319 | 0.74974 | -0.1953 |   0.0201 |                      0 | -            | False      | no_signal              |

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
