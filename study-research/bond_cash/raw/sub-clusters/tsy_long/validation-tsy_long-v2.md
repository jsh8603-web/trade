# validation-tsy_long-v2 — tsy_long (TLT) v2 격하·재검정 (2026-05-31)

> ★ main 12축 audit verdict 격하 5건 반영 (raw/evaluation-bond_cash-20260531.md).
> v1 산출 (`validation-tsy_long.md`) 와 병행. v2 = stationary 차분 driver + BH-FDR + half-split OOS + magnitude freeze.

## §0 v1 → v2 변경점
- driver: T10Y2Y level / ACM_TP10 level → **T10Y2Y_d20 / ACM_TP10_d20 차분** (★ non-stationary spurious 차단, ADF p_lev T10Y2Y=0.553 → diff 5pct PASS)
- 다중검정: Bonferroni α/420 (보수) → **BH-FDR q=0.1 on effective ~84** (PCA 4 component / 5 driver)
- HAC lag: f → **max(2f, 60)** (overlap nested 보수)
- verdict: magnitude prior 박제 ★금지★ → **sign/direction prior only** (4 라벨 → sign_prior_robust / fdr_pass_sign_unstable / sign_prior_descriptive / no_signal)
- regime cell: walk-forward OOS 부재 → **descriptive only 격하** (v1 의 regime_conditional_findings bonferroni_pass=true 박제 ★취소★)

## §1 sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | tsy_long |
| 대표 ETF | TLT (duration ≈ 17, credit AAA) |
| n_panel | 4,580 |

## §2 Rank-IC (v2 차분 driver + HAC lag 2× + half-split OOS + BH-FDR)
| driver       |   fwd |    n |      ic |    ic_p |   ci_lo |   ci_hi |      beta |   hac_se |   hac_t_lag2x |   hac_p |   ic_is |   ic_oos |   halfsplit_sign_match | sign_prior   | fdr_pass   | verdict_v2             |
|:-------------|------:|-----:|--------:|--------:|--------:|--------:|----------:|---------:|--------------:|--------:|--------:|---------:|-----------------------:|:-------------|:-----------|:-----------------------|
| MOVE_Z       |     5 | 4580 |  0.0109 | 0.46215 | -0.0498 |  0.0623 |  2.5e-05  | 0.000535 |         0.046 | 0.96321 |  0.0061 |   0.0208 |                      1 | +            | False      | no_signal              |
| MOVE_Z       |    20 | 4580 |  0.0084 | 0.5699  | -0.0984 |  0.1073 |  0.000333 | 0.001962 |         0.17  | 0.86535 |  0.0395 |  -0.0169 |                      0 | +            | False      | no_signal              |
| MOVE_Z       |    60 | 4580 | -0.053  | 0.00033 | -0.193  |  0.0863 | -0.002873 | 0.005415 |        -0.531 | 0.59567 | -0.0311 |  -0.0839 |                      1 | -            | False      | sign_prior_descriptive |
| ACM_TP10_d20 |     5 | 4580 | -0.0121 | 0.41452 | -0.0718 |  0.0448 | -0.003044 | 0.002346 |        -1.298 | 0.19437 | -0.0284 |   0.011  |                      0 | -            | False      | no_signal              |
| ACM_TP10_d20 |    20 | 4580 | -0.004  | 0.78694 | -0.1145 |  0.0894 |  0.002447 | 0.009085 |         0.269 | 0.78764 | -0.039  |   0.0429 |                      0 | -            | False      | no_signal              |
| ACM_TP10_d20 |    60 | 4580 |  0.0243 | 0.10029 | -0.0847 |  0.1342 |  0.035214 | 0.02386  |         1.476 | 0.13998 | -0.02   |   0.0923 |                      0 | +            | False      | no_signal              |
| DGS10_chg20  |     5 | 4580 | -0.0002 | 0.98821 | -0.0644 |  0.0664 | -0.003743 | 0.003272 |        -1.144 | 0.25257 |  0.0289 |  -0.0272 |                      0 | -            | False      | no_signal              |
| DGS10_chg20  |    20 | 4580 |  0.0053 | 0.71876 | -0.1022 |  0.0992 | -0.007878 | 0.009044 |        -0.871 | 0.38373 |  0.0484 |  -0.0335 |                      0 | +            | False      | no_signal              |
| DGS10_chg20  |    60 | 4580 | -0.0261 | 0.07709 | -0.1304 |  0.0778 | -0.001247 | 0.016602 |        -0.075 | 0.94012 | -0.0098 |  -0.0361 |                      1 | -            | False      | no_signal              |
| T10Y2Y_d20   |     5 | 4580 | -0.0004 | 0.97712 | -0.0528 |  0.0543 | -0.002243 | 0.00388  |        -0.578 | 0.56314 | -0.0127 |   0.0105 |                      0 | -            | False      | no_signal              |
| T10Y2Y_d20   |    20 | 4580 |  0.0128 | 0.38717 | -0.0833 |  0.1083 |  0.005916 | 0.012553 |         0.471 | 0.63745 | -0.0424 |   0.0705 |                      0 | +            | False      | no_signal              |
| T10Y2Y_d20   |    60 | 4580 |  0.0524 | 0.00039 | -0.0804 |  0.1847 |  0.056856 | 0.037548 |         1.514 | 0.12997 | -0.0359 |   0.1495 |                      0 | +            | False      | no_signal              |
| BAA10Y_chg20 |     5 | 4580 |  0.0457 | 0.00199 | -0.0125 |  0.1009 |  0.005908 | 0.003177 |         1.86  | 0.06293 |  0.0443 |   0.046  |                      1 | +            | False      | sign_prior_descriptive |
| BAA10Y_chg20 |    20 | 4580 |  0.0495 | 0.00081 | -0.0507 |  0.1364 |  0.0222   | 0.009827 |         2.259 | 0.02387 |  0.0407 |   0.059  |                      1 | +            | False      | sign_prior_descriptive |
| BAA10Y_chg20 |    60 | 4580 |  0.0658 | 1e-05   | -0.0487 |  0.1783 |  0.035411 | 0.026781 |         1.322 | 0.1861  |  0.0843 |   0.0494 |                      1 | +            | False      | sign_prior_descriptive |

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
