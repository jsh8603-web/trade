# validation-tips — tips (TIP) sub-cluster (2026-05-31)

> Phase 5 본격 (main option A 승인 후). small-N rigor 5 의무 + AUDIT-GUIDE B/C/D/E/F/G/H/I/J/K 박제.

## §0 spec / coverage / sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | tips |
| 대표 ETF | TIP (duration ≈ 7, credit AAA(TIPS)) |
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
| MOVE_Z       |     5 | 4580 |   -0.0051 |    0.72924 |          -0.0619 |           0.0462 | -0.000248 | 0.000303 |  -0.82  | 0.41243 |   -0.000842 |    0.000345 | False             | ★REJECTED             |
| MOVE_Z       |    20 | 4580 |   -0.0026 |    0.85824 |          -0.0971 |           0.0915 | -0.000319 | 0.000777 |  -0.41  | 0.68174 |   -0.001841 |    0.001204 | False             | ★REJECTED             |
| MOVE_Z       |    60 | 4580 |   -0.0685 |    0       |          -0.2012 |           0.0682 | -0.001562 | 0.001577 |  -0.99  | 0.32219 |   -0.004653 |    0.00153  | False             | PARTIAL CONFIRMED     |
| ACM_TP10     |     5 | 4580 |    0.0658 |    1e-05   |           0.0019 |           0.1274 |  0.00045  | 0.000302 |   1.492 | 0.13582 |   -0.000141 |    0.001041 | False             | PARTIAL CONFIRMED     |
| ACM_TP10     |    20 | 4580 |    0.1159 |    0       |           0.014  |           0.2185 |  0.001729 | 0.000932 |   1.856 | 0.06351 |   -9.7e-05  |    0.003555 | False             | PARTIAL CONFIRMED     |
| ACM_TP10     |    60 | 4580 |    0.2105 |    0       |           0.0239 |           0.388  |  0.004955 | 0.002253 |   2.199 | 0.02787 |    0.000539 |    0.00937  | False             | ★CONFIRMED 강력       |
| DGS10_chg20  |     5 | 4580 |    0.0307 |    0.03757 |          -0.0324 |           0.0918 |  8e-06    | 0.001705 |   0.005 | 0.99631 |   -0.003334 |    0.003349 | False             | PARTIAL CONFIRMED     |
| DGS10_chg20  |    20 | 4580 |    0.0411 |    0.00545 |          -0.0495 |           0.1359 | -0.001552 | 0.003748 |  -0.414 | 0.67891 |   -0.008899 |    0.005795 | False             | PARTIAL CONFIRMED     |
| DGS10_chg20  |    60 | 4580 |   -0.0179 |    0.22577 |          -0.1237 |           0.0896 | -0.001078 | 0.00623  |  -0.173 | 0.86265 |   -0.013288 |    0.011133 | False             | TENTATIVE DIRECTIONAL |
| T10Y2Y       |     5 | 4580 |    0.0532 |    0.00031 |          -0.0103 |           0.1148 |  0.000381 | 0.000259 |   1.473 | 0.14085 |   -0.000126 |    0.000889 | False             | PARTIAL CONFIRMED     |
| T10Y2Y       |    20 | 4580 |    0.0803 |    0       |          -0.0277 |           0.1844 |  0.001483 | 0.000913 |   1.623 | 0.10455 |   -0.000308 |    0.003273 | False             | PARTIAL CONFIRMED     |
| T10Y2Y       |    60 | 4580 |    0.1446 |    0       |          -0.0466 |           0.3298 |  0.00418  | 0.002354 |   1.775 | 0.07585 |   -0.000435 |    0.008794 | False             | PARTIAL CONFIRMED     |
| BAA10Y_chg20 |     5 | 4580 |   -0.0233 |    0.11565 |          -0.0854 |           0.0282 | -1.4e-05  | 0.002756 |  -0.005 | 0.99609 |   -0.005414 |    0.005387 | False             | TENTATIVE DIRECTIONAL |
| BAA10Y_chg20 |    20 | 4580 |   -0.084  |    0       |          -0.1653 |          -0.011  | -0.001478 | 0.006281 |  -0.235 | 0.81393 |   -0.013788 |    0.010832 | False             | PARTIAL CONFIRMED     |
| BAA10Y_chg20 |    60 | 4580 |   -0.1039 |    0       |          -0.2256 |           0.0053 | -0.002405 | 0.008256 |  -0.291 | 0.77084 |   -0.018587 |    0.013777 | False             | PARTIAL CONFIRMED     |

## §4 regime cell Rank-IC (driver × forward × 4 cells)
| driver       |   fwd | regime             |    n |   rank_ic |   raw_p | bonferroni_pass   |
|:-------------|------:|:-------------------|-----:|----------:|--------:|:------------------|
| MOVE_Z       |     5 | rate_down_vol_high |  999 |   -0.02   | 0.52873 | False             |
| MOVE_Z       |     5 | rate_down_vol_low  | 1405 |    0.1063 | 7e-05   | True              |
| MOVE_Z       |     5 | rate_up_vol_high   | 1036 |   -0.0757 | 0.01478 | False             |
| MOVE_Z       |     5 | rate_up_vol_low    | 1140 |   -0.0093 | 0.7531  | False             |
| MOVE_Z       |    20 | rate_down_vol_high |  999 |   -0.0243 | 0.44221 | False             |
| MOVE_Z       |    20 | rate_down_vol_low  | 1405 |    0.1445 | 0       | True              |
| MOVE_Z       |    20 | rate_up_vol_high   | 1036 |   -0.0761 | 0.01427 | False             |
| MOVE_Z       |    20 | rate_up_vol_low    | 1140 |   -0.0063 | 0.8307  | False             |
| MOVE_Z       |    60 | rate_down_vol_high |  999 |   -0.0952 | 0.00259 | False             |
| MOVE_Z       |    60 | rate_down_vol_low  | 1405 |    0.0809 | 0.00239 | False             |
| MOVE_Z       |    60 | rate_up_vol_high   | 1036 |   -0.2801 | 0       | True              |
| MOVE_Z       |    60 | rate_up_vol_low    | 1140 |   -0.0824 | 0.00535 | False             |
| ACM_TP10     |     5 | rate_down_vol_high |  999 |   -0.0363 | 0.25191 | False             |
| ACM_TP10     |     5 | rate_down_vol_low  | 1405 |    0.0509 | 0.05635 | False             |
| ACM_TP10     |     5 | rate_up_vol_high   | 1036 |    0.0806 | 0.00942 | False             |
| ACM_TP10     |     5 | rate_up_vol_low    | 1140 |    0.2074 | 0       | True              |
| ACM_TP10     |    20 | rate_down_vol_high |  999 |   -0.0005 | 0.98809 | False             |
| ACM_TP10     |    20 | rate_down_vol_low  | 1405 |    0.0168 | 0.5304  | False             |
| ACM_TP10     |    20 | rate_up_vol_high   | 1036 |    0.1605 | 0       | True              |
| ACM_TP10     |    20 | rate_up_vol_low    | 1140 |    0.3332 | 0       | True              |
| ACM_TP10     |    60 | rate_down_vol_high |  999 |    0.0152 | 0.63066 | False             |
| ACM_TP10     |    60 | rate_down_vol_low  | 1405 |    0.0559 | 0.03629 | False             |
| ACM_TP10     |    60 | rate_up_vol_high   | 1036 |    0.4142 | 0       | True              |
| ACM_TP10     |    60 | rate_up_vol_low    | 1140 |    0.394  | 0       | True              |
| DGS10_chg20  |     5 | rate_down_vol_high |  999 |   -0.0011 | 0.97336 | False             |
| DGS10_chg20  |     5 | rate_down_vol_low  | 1405 |    0.1211 | 1e-05   | True              |
| DGS10_chg20  |     5 | rate_up_vol_high   | 1036 |   -0.0511 | 0.10004 | False             |
| DGS10_chg20  |     5 | rate_up_vol_low    | 1140 |    0.0854 | 0.00392 | False             |
| DGS10_chg20  |    20 | rate_down_vol_high |  999 |   -0.0265 | 0.40321 | False             |
| DGS10_chg20  |    20 | rate_down_vol_low  | 1405 |    0.133  | 0       | True              |
| DGS10_chg20  |    20 | rate_up_vol_high   | 1036 |    0.0142 | 0.6481  | False             |
| DGS10_chg20  |    20 | rate_up_vol_low    | 1140 |    0.0913 | 0.00204 | False             |
| DGS10_chg20  |    60 | rate_down_vol_high |  999 |   -0.1297 | 4e-05   | True              |
| DGS10_chg20  |    60 | rate_down_vol_low  | 1405 |    0.0318 | 0.23347 | False             |
| DGS10_chg20  |    60 | rate_up_vol_high   | 1036 |    0.1395 | 1e-05   | True              |
| DGS10_chg20  |    60 | rate_up_vol_low    | 1140 |   -0.0268 | 0.36685 | False             |
| T10Y2Y       |     5 | rate_down_vol_high |  999 |   -0.0259 | 0.41371 | False             |
| T10Y2Y       |     5 | rate_down_vol_low  | 1405 |    0.0517 | 0.05271 | False             |
| T10Y2Y       |     5 | rate_up_vol_high   | 1036 |    0.0186 | 0.54882 | False             |
| T10Y2Y       |     5 | rate_up_vol_low    | 1140 |    0.1642 | 0       | True              |
| T10Y2Y       |    20 | rate_down_vol_high |  999 |   -0.0282 | 0.37363 | False             |
| T10Y2Y       |    20 | rate_down_vol_low  | 1405 |    0.0441 | 0.09854 | False             |
| T10Y2Y       |    20 | rate_up_vol_high   | 1036 |    0.0617 | 0.04696 | False             |
| T10Y2Y       |    20 | rate_up_vol_low    | 1140 |    0.2205 | 0       | True              |
| T10Y2Y       |    60 | rate_down_vol_high |  999 |    0.014  | 0.6581  | False             |
| T10Y2Y       |    60 | rate_down_vol_low  | 1405 |    0.0398 | 0.13581 | False             |
| T10Y2Y       |    60 | rate_up_vol_high   | 1036 |    0.2579 | 0       | True              |
| T10Y2Y       |    60 | rate_up_vol_low    | 1140 |    0.2473 | 0       | True              |
| BAA10Y_chg20 |     5 | rate_down_vol_high |  999 |    0.0225 | 0.47652 | False             |
| BAA10Y_chg20 |     5 | rate_down_vol_low  | 1405 |   -0.0174 | 0.51366 | False             |
| BAA10Y_chg20 |     5 | rate_up_vol_high   | 1036 |   -0.022  | 0.47926 | False             |
| BAA10Y_chg20 |     5 | rate_up_vol_low    | 1140 |   -0.069  | 0.01974 | False             |
| BAA10Y_chg20 |    20 | rate_down_vol_high |  999 |    0.0146 | 0.64496 | False             |
| BAA10Y_chg20 |    20 | rate_down_vol_low  | 1405 |   -0.1322 | 0       | True              |
| BAA10Y_chg20 |    20 | rate_up_vol_high   | 1036 |   -0.0379 | 0.22239 | False             |
| BAA10Y_chg20 |    20 | rate_up_vol_low    | 1140 |   -0.1854 | 0       | True              |
| BAA10Y_chg20 |    60 | rate_down_vol_high |  999 |    0.0766 | 0.01548 | False             |
| BAA10Y_chg20 |    60 | rate_down_vol_low  | 1405 |   -0.1091 | 4e-05   | True              |
| BAA10Y_chg20 |    60 | rate_up_vol_high   | 1036 |   -0.2055 | 0       | True              |
| BAA10Y_chg20 |    60 | rate_up_vol_low    | 1140 |   -0.1487 | 0       | True              |

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
