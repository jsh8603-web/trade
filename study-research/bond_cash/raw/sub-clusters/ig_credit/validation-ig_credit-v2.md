# validation-ig_credit-v2 — ig_credit (LQD) v2 격하·재검정 (2026-05-31)

> ★ main 12축 audit verdict 격하 5건 반영 (raw/evaluation-bond_cash-20260531.md).
> v1 산출 (`validation-ig_credit.md`) 와 병행. v2 = stationary 차분 driver + BH-FDR + half-split OOS + magnitude freeze.

## §0 v1 → v2 변경점
- driver: T10Y2Y level / ACM_TP10 level → **T10Y2Y_d20 / ACM_TP10_d20 차분** (★ non-stationary spurious 차단, ADF p_lev T10Y2Y=0.553 → diff 5pct PASS)
- 다중검정: Bonferroni α/420 (보수) → **BH-FDR q=0.1 on effective ~84** (PCA 4 component / 5 driver)
- HAC lag: f → **max(2f, 60)** (overlap nested 보수)
- verdict: magnitude prior 박제 ★금지★ → **sign/direction prior only** (4 라벨 → sign_prior_robust / fdr_pass_sign_unstable / sign_prior_descriptive / no_signal)
- regime cell: walk-forward OOS 부재 → **descriptive only 격하** (v1 의 regime_conditional_findings bonferroni_pass=true 박제 ★취소★)

## §1 sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | ig_credit |
| 대표 ETF | LQD (duration ≈ 8, credit A-/BBB+) |
| n_panel | 4,580 |

## §2 Rank-IC (v2 차분 driver + HAC lag 2× + half-split OOS + BH-FDR)
| driver       |   fwd |    n |      ic |    ic_p |   ci_lo |   ci_hi |      beta |   hac_se |   hac_t_lag2x |   hac_p |   ic_is |   ic_oos |   halfsplit_sign_match | sign_prior   | fdr_pass   | verdict_v2             |
|:-------------|------:|-----:|--------:|--------:|--------:|--------:|----------:|---------:|--------------:|--------:|--------:|---------:|-----------------------:|:-------------|:-----------|:-----------------------|
| MOVE_Z       |     5 | 4580 |  0.0086 | 0.55978 | -0.0572 |  0.0663 | -0.000214 | 0.000399 |        -0.536 | 0.59195 |  0.0114 |   0.0086 |                      1 | +            | False      | no_signal              |
| MOVE_Z       |    20 | 4580 |  0.0035 | 0.81118 | -0.1057 |  0.0898 |  0.000479 | 0.001232 |         0.389 | 0.69738 |  0.0444 |  -0.0315 |                      0 | +            | False      | no_signal              |
| MOVE_Z       |    60 | 4580 | -0.0433 | 0.00334 | -0.1865 |  0.1108 | -0.000126 | 0.003863 |        -0.033 | 0.97406 | -0.0351 |  -0.0663 |                      1 | -            | False      | sign_prior_descriptive |
| ACM_TP10_d20 |     5 | 4580 |  0.0045 | 0.75859 | -0.0562 |  0.0651 |  0.000188 | 0.00247  |         0.076 | 0.93948 |  0.0113 |   0.0021 |                      1 | +            | False      | no_signal              |
| ACM_TP10_d20 |    20 | 4580 | -0.0032 | 0.82624 | -0.101  |  0.0877 | -0.002392 | 0.006135 |        -0.39  | 0.69656 | -0.0658 |   0.0633 |                      0 | -            | False      | no_signal              |
| ACM_TP10_d20 |    60 | 4580 |  0.0314 | 0.03348 | -0.0873 |  0.1405 |  0.027499 | 0.014841 |         1.853 | 0.06389 | -0.0736 |   0.1428 |                      0 | +            | False      | no_signal              |
| DGS10_chg20  |     5 | 4580 | -0.0082 | 0.57714 | -0.0711 |  0.0507 | -0.001063 | 0.002924 |        -0.363 | 0.71627 |  0.0541 |  -0.0658 |                      0 | -            | False      | no_signal              |
| DGS10_chg20  |    20 | 4580 | -0.0354 | 0.01662 | -0.1292 |  0.0583 | -0.009333 | 0.00764  |        -1.222 | 0.22187 | -0.0018 |  -0.0645 |                      1 | -            | False      | sign_prior_descriptive |
| DGS10_chg20  |    60 | 4580 | -0.0597 | 5e-05   | -0.1753 |  0.0586 | -0.002499 | 0.011582 |        -0.216 | 0.82919 | -0.0655 |  -0.0543 |                      1 | -            | False      | sign_prior_descriptive |
| T10Y2Y_d20   |     5 | 4580 |  0.0289 | 0.05054 | -0.0335 |  0.0836 |  0.000835 | 0.00348  |         0.24  | 0.81027 |  0.0279 |   0.0309 |                      1 | +            | False      | no_signal              |
| T10Y2Y_d20   |    20 | 4580 |  0.0412 | 0.00525 | -0.0481 |  0.1237 |  0.003143 | 0.009743 |         0.323 | 0.74699 | -0.0306 |   0.1126 |                      0 | +            | False      | no_signal              |
| T10Y2Y_d20   |    60 | 4580 |  0.0872 | 0       | -0.0273 |  0.2055 |  0.052027 | 0.021208 |         2.453 | 0.01416 | -0.0226 |   0.1978 |                      0 | +            | False      | no_signal              |
| BAA10Y_chg20 |     5 | 4580 |  0.0455 | 0.00206 | -0.0195 |  0.1044 |  0.005254 | 0.003219 |         1.632 | 0.10263 |  0.0177 |   0.0722 |                      1 | +            | False      | sign_prior_descriptive |
| BAA10Y_chg20 |    20 | 4580 |  0.0622 | 2e-05   | -0.0488 |  0.1514 |  0.019646 | 0.009524 |         2.063 | 0.03912 |  0.061  |   0.0625 |                      1 | +            | False      | sign_prior_descriptive |
| BAA10Y_chg20 |    60 | 4580 |  0.0692 | 0       | -0.0368 |  0.2045 |  0.035016 | 0.021971 |         1.594 | 0.111   |  0.024  |   0.1268 |                      1 | +            | False      | sign_prior_descriptive |

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
