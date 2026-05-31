# validation-tsy_mid — tsy_mid (IEF) sub-cluster (2026-05-31)

> Phase 5 본격 (main option A 승인 후). small-N rigor 5 의무 + AUDIT-GUIDE B/C/D/E/F/G/H/I/J/K 박제.

## §0 spec / coverage / sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | tsy_mid |
| 대표 ETF | IEF (duration ≈ 8, credit AAA) |
| common period | 2007-12-18 ~ 2026-03-04 |
| n_panel | 4,580 |
| driver | MOVE_Z, ACM_TP10, DGS10_chg20, T10Y2Y, BAA10Y_chg20 |
| forward | [5, 20, 60] |
| regime cell | rate (DGS10 126d Δ ≷ 0) × vol (MOVE ≷ 252d median), 2×2 = 4 cells |

## §1 spec ↔ code 1:1 (small-N rigor §1.3, audit E축)
| axis | spec | code |
|---|---|---|
| 시제 | driver 동일일 → ETF 향후 N영업일 누적 return (predictive) | `etf_close.pct_change(N).shift(-N)` ✅ |
| frequency | daily (driver = monthly 인 ACMTP10 는 forward-fill) | daily B-frequency reindex + ffill ✅ |
| MOVE_Z | rolling 252 trading-day Z-score | `(c - c.rolling(252).mean()) / c.rolling(252).std()` ✅ |
| DGS10_chg20 | 20 영업일 Δ DGS10 | `dgs10.diff(20)` ✅ |
| T10Y2Y | DGS10 - DGS2 (curve, level) | direct subtract ✅ |
| BAA10Y_chg20 | 20 영업일 Δ BAA10Y (credit spread Δ proxy) | `baa.diff(20)` ✅ |
| regime cell | 사후 conditioning (in-sample, OOS 아님 — Phase 6 audit 시 walk-forward 의무) | 박제 ✅ |

## §2 driver pairwise correlation (★main 보강 지시: effective tests << 명목 420)
```
              MOVE_Z  ACM_TP10  DGS10_chg20  T10Y2Y  BAA10Y_chg20
MOVE_Z         1.000    -0.070        0.038  -0.029         0.282
ACM_TP10      -0.070     1.000        0.029   0.813         0.008
DGS10_chg20    0.038     0.029        1.000  -0.017        -0.388
T10Y2Y        -0.029     0.813       -0.017   1.000        -0.014
BAA10Y_chg20   0.282     0.008       -0.388  -0.014         1.000
```
- ★ MOVE_Z · ACM_TP10 · DGS10_chg20 · T10Y2Y · BAA10Y_chg20 = rate 계열 상호 공선 — 명목 420 test 의 effective 검정수 << 420. Bonferroni α/420 = 0.000119 은 보수적 상한.

## §3 Rank-IC + HAC (driver × forward, n_panel = 4,580)
| driver       |   fwd |    n |   rank_ic |   ic_raw_p |   ic_block_ci_lo |   ic_block_ci_hi |      beta |   hac_se |   hac_t |   hac_p |   hac_ci_lo |   hac_ci_hi | bonferroni_pass   | verdict               |
|:-------------|------:|-----:|----------:|-----------:|-----------------:|-----------------:|----------:|---------:|--------:|--------:|------------:|------------:|:------------------|:----------------------|
| MOVE_Z       |     5 | 4580 |    0.0087 |    0.5579  |          -0.0583 |           0.0618 | -2.2e-05  | 0.00023  |  -0.097 | 0.92248 |   -0.000472 |    0.000428 | False             | ★REJECTED             |
| MOVE_Z       |    20 | 4580 |    0.0181 |    0.21992 |          -0.0897 |           0.1121 |  0.000118 | 0.000844 |   0.14  | 0.88904 |   -0.001537 |    0.001773 | False             | TENTATIVE DIRECTIONAL |
| MOVE_Z       |    60 | 4580 |   -0.0599 |    5e-05   |          -0.2026 |           0.0771 | -0.001497 | 0.002456 |  -0.609 | 0.5422  |   -0.00631  |    0.003317 | False             | PARTIAL CONFIRMED     |
| ACM_TP10     |     5 | 4580 |    0.1082 |    0       |           0.0449 |           0.1719 |  0.000842 | 0.00029  |   2.9   | 0.00373 |    0.000273 |    0.001411 | False             | ★CONFIRMED 강력       |
| ACM_TP10     |    20 | 4580 |    0.1769 |    0       |           0.0731 |           0.2726 |  0.003297 | 0.001246 |   2.646 | 0.00815 |    0.000855 |    0.00574  | False             | ★CONFIRMED 강력       |
| ACM_TP10     |    60 | 4580 |    0.2741 |    0       |           0.0868 |           0.4472 |  0.008731 | 0.003375 |   2.587 | 0.00969 |    0.002116 |    0.015346 | False             | ★CONFIRMED 강력       |
| DGS10_chg20  |     5 | 4580 |   -0.0071 |    0.63113 |          -0.0699 |           0.0542 | -0.001276 | 0.001297 |  -0.984 | 0.32504 |   -0.003817 |    0.001265 | False             | ★REJECTED             |
| DGS10_chg20  |    20 | 4580 |   -0.0151 |    0.30813 |          -0.1166 |           0.0742 | -0.003433 | 0.004161 |  -0.825 | 0.40933 |   -0.011588 |    0.004722 | False             | TENTATIVE DIRECTIONAL |
| DGS10_chg20  |    60 | 4580 |   -0.0262 |    0.07655 |          -0.131  |           0.0898 | -0.000598 | 0.007373 |  -0.081 | 0.93531 |   -0.01505  |    0.013853 | False             | TENTATIVE DIRECTIONAL |
| T10Y2Y       |     5 | 4580 |    0.0719 |    0       |           0.0033 |           0.1352 |  0.000572 | 0.000311 |   1.84  | 0.06582 |   -3.7e-05  |    0.001182 | False             | PARTIAL CONFIRMED     |
| T10Y2Y       |    20 | 4580 |    0.0979 |    0       |          -0.0182 |           0.2098 |  0.002236 | 0.00125  |   1.789 | 0.07365 |   -0.000214 |    0.004687 | False             | PARTIAL CONFIRMED     |
| T10Y2Y       |    60 | 4580 |    0.1495 |    0       |          -0.0377 |           0.3253 |  0.005932 | 0.003424 |   1.732 | 0.08319 |   -0.000779 |    0.012643 | False             | PARTIAL CONFIRMED     |
| BAA10Y_chg20 |     5 | 4580 |    0.0568 |    0.00012 |          -0.0016 |           0.1105 |  0.0024   | 0.001513 |   1.586 | 0.11275 |   -0.000566 |    0.005365 | False             | PARTIAL CONFIRMED     |
| BAA10Y_chg20 |    20 | 4580 |    0.0566 |    0.00013 |          -0.0376 |           0.1402 |  0.009578 | 0.005079 |   1.886 | 0.05932 |   -0.000377 |    0.019533 | False             | PARTIAL CONFIRMED     |
| BAA10Y_chg20 |    60 | 4580 |    0.0494 |    0.00082 |          -0.0652 |           0.1622 |  0.016932 | 0.013325 |   1.271 | 0.20383 |   -0.009184 |    0.043049 | False             | PARTIAL CONFIRMED     |

## §4 regime cell Rank-IC (driver × forward × 4 cells)
| driver       |   fwd | regime             |    n |   rank_ic |   raw_p | bonferroni_pass   |
|:-------------|------:|:-------------------|-----:|----------:|--------:|:------------------|
| MOVE_Z       |     5 | rate_down_vol_high |  999 |    0.0315 | 0.31916 | False             |
| MOVE_Z       |     5 | rate_down_vol_low  | 1405 |    0.0915 | 0.0006  | False             |
| MOVE_Z       |     5 | rate_up_vol_high   | 1036 |   -0.1123 | 0.00029 | False             |
| MOVE_Z       |     5 | rate_up_vol_low    | 1140 |    0.0194 | 0.51374 | False             |
| MOVE_Z       |    20 | rate_down_vol_high |  999 |    0.0444 | 0.16072 | False             |
| MOVE_Z       |    20 | rate_down_vol_low  | 1405 |    0.1025 | 0.00012 | False             |
| MOVE_Z       |    20 | rate_up_vol_high   | 1036 |   -0.1393 | 1e-05   | True              |
| MOVE_Z       |    20 | rate_up_vol_low    | 1140 |   -0.0032 | 0.91364 | False             |
| MOVE_Z       |    60 | rate_down_vol_high |  999 |    0.0019 | 0.95227 | False             |
| MOVE_Z       |    60 | rate_down_vol_low  | 1405 |    0.0505 | 0.05826 | False             |
| MOVE_Z       |    60 | rate_up_vol_high   | 1036 |   -0.2349 | 0       | True              |
| MOVE_Z       |    60 | rate_up_vol_low    | 1140 |   -0.0527 | 0.07556 | False             |
| ACM_TP10     |     5 | rate_down_vol_high |  999 |   -0.0033 | 0.91804 | False             |
| ACM_TP10     |     5 | rate_down_vol_low  | 1405 |    0.0742 | 0.00541 | False             |
| ACM_TP10     |     5 | rate_up_vol_high   | 1036 |    0.129  | 3e-05   | True              |
| ACM_TP10     |     5 | rate_up_vol_low    | 1140 |    0.2571 | 0       | True              |
| ACM_TP10     |    20 | rate_down_vol_high |  999 |    0.0411 | 0.19407 | False             |
| ACM_TP10     |    20 | rate_down_vol_low  | 1405 |    0.054  | 0.04309 | False             |
| ACM_TP10     |    20 | rate_up_vol_high   | 1036 |    0.2319 | 0       | True              |
| ACM_TP10     |    20 | rate_up_vol_low    | 1140 |    0.4019 | 0       | True              |
| ACM_TP10     |    60 | rate_down_vol_high |  999 |   -0.0544 | 0.08566 | False             |
| ACM_TP10     |    60 | rate_down_vol_low  | 1405 |    0.1626 | 0       | True              |
| ACM_TP10     |    60 | rate_up_vol_high   | 1036 |    0.4976 | 0       | True              |
| ACM_TP10     |    60 | rate_up_vol_low    | 1140 |    0.4909 | 0       | True              |
| DGS10_chg20  |     5 | rate_down_vol_high |  999 |   -0.0332 | 0.29512 | False             |
| DGS10_chg20  |     5 | rate_down_vol_low  | 1405 |    0.0738 | 0.00564 | False             |
| DGS10_chg20  |     5 | rate_up_vol_high   | 1036 |   -0.0424 | 0.17266 | False             |
| DGS10_chg20  |     5 | rate_up_vol_low    | 1140 |   -0.0169 | 0.56796 | False             |
| DGS10_chg20  |    20 | rate_down_vol_high |  999 |   -0.0228 | 0.47234 | False             |
| DGS10_chg20  |    20 | rate_down_vol_low  | 1405 |    0.0318 | 0.23334 | False             |
| DGS10_chg20  |    20 | rate_up_vol_high   | 1036 |   -0.0361 | 0.24571 | False             |
| DGS10_chg20  |    20 | rate_up_vol_low    | 1140 |   -0.0056 | 0.85075 | False             |
| DGS10_chg20  |    60 | rate_down_vol_high |  999 |   -0.0901 | 0.00438 | False             |
| DGS10_chg20  |    60 | rate_down_vol_low  | 1405 |   -0.0429 | 0.10826 | False             |
| DGS10_chg20  |    60 | rate_up_vol_high   | 1036 |    0.1057 | 0.00065 | False             |
| DGS10_chg20  |    60 | rate_up_vol_low    | 1140 |   -0.0818 | 0.00573 | False             |
| T10Y2Y       |     5 | rate_down_vol_high |  999 |    0.0295 | 0.35187 | False             |
| T10Y2Y       |     5 | rate_down_vol_low  | 1405 |    0.0834 | 0.00176 | False             |
| T10Y2Y       |     5 | rate_up_vol_high   | 1036 |    0.0096 | 0.75801 | False             |
| T10Y2Y       |     5 | rate_up_vol_low    | 1140 |    0.1809 | 0       | True              |
| T10Y2Y       |    20 | rate_down_vol_high |  999 |    0.0806 | 0.0108  | False             |
| T10Y2Y       |    20 | rate_down_vol_low  | 1405 |    0.0499 | 0.06173 | False             |
| T10Y2Y       |    20 | rate_up_vol_high   | 1036 |    0.0353 | 0.25584 | False             |
| T10Y2Y       |    20 | rate_up_vol_low    | 1140 |    0.2342 | 0       | True              |
| T10Y2Y       |    60 | rate_down_vol_high |  999 |    0.0466 | 0.14106 | False             |
| T10Y2Y       |    60 | rate_down_vol_low  | 1405 |    0.0977 | 0.00025 | False             |
| T10Y2Y       |    60 | rate_up_vol_high   | 1036 |    0.1989 | 0       | True              |
| T10Y2Y       |    60 | rate_up_vol_low    | 1140 |    0.265  | 0       | True              |
| BAA10Y_chg20 |     5 | rate_down_vol_high |  999 |    0.1043 | 0.00096 | False             |
| BAA10Y_chg20 |     5 | rate_down_vol_low  | 1405 |    0.0556 | 0.03708 | False             |
| BAA10Y_chg20 |     5 | rate_up_vol_high   | 1036 |    0.005  | 0.87148 | False             |
| BAA10Y_chg20 |     5 | rate_up_vol_low    | 1140 |    0.0807 | 0.00638 | False             |
| BAA10Y_chg20 |    20 | rate_down_vol_high |  999 |    0.1231 | 0.0001  | True              |
| BAA10Y_chg20 |    20 | rate_down_vol_low  | 1405 |    0.0224 | 0.40155 | False             |
| BAA10Y_chg20 |    20 | rate_up_vol_high   | 1036 |    0.0443 | 0.15374 | False             |
| BAA10Y_chg20 |    20 | rate_up_vol_low    | 1140 |    0.0532 | 0.07272 | False             |
| BAA10Y_chg20 |    60 | rate_down_vol_high |  999 |    0.1311 | 3e-05   | True              |
| BAA10Y_chg20 |    60 | rate_down_vol_low  | 1405 |    0.0129 | 0.62917 | False             |
| BAA10Y_chg20 |    60 | rate_up_vol_high   | 1036 |    0.002  | 0.94976 | False             |
| BAA10Y_chg20 |    60 | rate_up_vol_low    | 1140 |    0.145  | 0       | True              |

## §5 verdict 요약
- Bonferroni α/420 통과 = **0/15** test
- 단정 어휘 ⛔ 회피 — verdict 라벨 5단계 (small-N rigor §2) 적용. 점추정 prior 박제 ★금지★ — Phase 6 audit subagent 가 raw 재실행 시 Block Bootstrap CI + 추가 검정.

## §6 미해결 / 한계 (H축)
- driver 공선 (rate 계열 5개) — effective tests 보고만, PCA / partial Rank-IC 분해는 Phase 7 통합 yaml 단계
- BAMLH0A0HYM2 historical 1996-2023 부재 → BAA10Y proxy 대체 (main 인계 경로, eq_us_defensive H3 검증 재사용)
- ACM TP10 daily ffill (monthly publish → daily 사용 시 within-month lookahead 0)
- regime cell = in-sample classification (Phase 6 audit 시 walk-forward OOS 의무)
- ETF tracking error, 슬리피지, 거래비용 J축 — alpha 주장 시 차감 후 양 확인 의무 (Phase 7)

## §7 K축 — 시도횟수 + Bonferroni
- 본 sub-cluster 명목 tests = 15 (driver 5 × forward 3)
- 전체 sub-cluster 통합 = 7 × 15 = 105 spec + regime cell split 별도
- driver 공선 → effective tests < 명목 (★main 지시 보강 박제)
- haircut: Deflated Sharpe / Haircut Sharpe — Phase 6 audit subagent 적용 (본 작업방 supervisor 직접 평가 ⛔ 금지)
