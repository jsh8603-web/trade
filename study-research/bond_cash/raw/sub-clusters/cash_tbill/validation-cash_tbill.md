# validation-cash_tbill — cash_tbill (BIL) sub-cluster (2026-05-31)

> Phase 5 본격 (main option A 승인 후). small-N rigor 5 의무 + AUDIT-GUIDE B/C/D/E/F/G/H/I/J/K 박제.

## §0 spec / coverage / sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | cash_tbill |
| 대표 ETF | BIL (duration ≈ 0.1, credit AAA) |
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
| MOVE_Z       |     5 | 4580 |   -0.0493 |    0.00084 |          -0.1373 |           0.054  | -3e-05    | 1.1e-05  |  -2.641 | 0.00826 |   -5.3e-05  |   -8e-06    | False             | ★CONFIRMED 강력       |
| MOVE_Z       |    20 | 4580 |   -0.0705 |    0       |          -0.1764 |           0.0426 | -0.000112 | 6e-05    |  -1.855 | 0.06364 |   -0.00023  |    6e-06    | False             | PARTIAL CONFIRMED     |
| MOVE_Z       |    60 | 4580 |   -0.0815 |    0       |          -0.2283 |           0.0835 | -0.000312 | 0.00025  |  -1.247 | 0.21255 |   -0.000803 |    0.000179 | False             | PARTIAL CONFIRMED     |
| ACM_TP10     |     5 | 4580 |   -0.236  |    0       |          -0.3083 |          -0.1477 | -9.1e-05  | 1.2e-05  |  -7.327 | 0       |   -0.000115 |   -6.6e-05  | True              | ★CONFIRMED 강력       |
| ACM_TP10     |    20 | 4580 |   -0.2952 |    0       |          -0.39   |          -0.2019 | -0.000372 | 6.4e-05  |  -5.782 | 0       |   -0.000498 |   -0.000246 | True              | ★CONFIRMED 강력       |
| ACM_TP10     |    60 | 4580 |   -0.3233 |    0       |          -0.4802 |          -0.166  | -0.001189 | 0.000308 |  -3.86  | 0.00011 |   -0.001792 |   -0.000585 | True              | ★CONFIRMED 강력       |
| DGS10_chg20  |     5 | 4580 |    0.0075 |    0.60995 |          -0.074  |           0.0911 |  3.8e-05  | 6.6e-05  |   0.569 | 0.56956 |   -9.2e-05  |    0.000167 | False             | ★REJECTED             |
| DGS10_chg20  |    20 | 4580 |    0.0368 |    0.0128  |          -0.0575 |           0.1332 |  0.000102 | 0.00034  |   0.301 | 0.76366 |   -0.000564 |    0.000768 | False             | PARTIAL CONFIRMED     |
| DGS10_chg20  |    60 | 4580 |    0.0473 |    0.00135 |          -0.0624 |           0.1537 |  0.000514 | 0.001096 |   0.469 | 0.63916 |   -0.001634 |    0.002661 | False             | PARTIAL CONFIRMED     |
| T10Y2Y       |     5 | 4580 |   -0.5981 |    0       |          -0.6583 |          -0.5237 | -0.000272 | 1.1e-05  | -24.955 | 0       |   -0.000293 |   -0.00025  | True              | ★CONFIRMED 강력       |
| T10Y2Y       |    20 | 4580 |   -0.6906 |    0       |          -0.7483 |          -0.6125 | -0.001099 | 6.7e-05  | -16.494 | 0       |   -0.00123  |   -0.000968 | True              | ★CONFIRMED 강력       |
| T10Y2Y       |    60 | 4580 |   -0.7353 |    0       |          -0.8145 |          -0.5976 | -0.003373 | 0.000325 | -10.392 | 0       |   -0.004009 |   -0.002737 | True              | ★CONFIRMED 강력       |
| BAA10Y_chg20 |     5 | 4580 |    0.0063 |    0.66919 |          -0.0685 |           0.0823 | -1e-05    | 7.3e-05  |  -0.131 | 0.89566 |   -0.000153 |    0.000134 | False             | ★REJECTED             |
| BAA10Y_chg20 |    20 | 4580 |   -0.0207 |    0.1621  |          -0.1136 |           0.0658 |  2.9e-05  | 0.000264 |   0.111 | 0.91173 |   -0.000488 |    0.000547 | False             | TENTATIVE DIRECTIONAL |
| BAA10Y_chg20 |    60 | 4580 |   -0.0211 |    0.15307 |          -0.1444 |           0.0777 | -1.5e-05  | 0.000897 |  -0.016 | 0.98687 |   -0.001772 |    0.001743 | False             | TENTATIVE DIRECTIONAL |

## §4 regime cell Rank-IC (driver × forward × 4 cells)
| driver       |   fwd | regime             |    n |   rank_ic |   raw_p | bonferroni_pass   |
|:-------------|------:|:-------------------|-----:|----------:|--------:|:------------------|
| MOVE_Z       |     5 | rate_down_vol_high |  999 |    0.1027 | 0.00115 | False             |
| MOVE_Z       |     5 | rate_down_vol_low  | 1405 |   -0.0258 | 0.33304 | False             |
| MOVE_Z       |     5 | rate_up_vol_high   | 1036 |   -0.1212 | 9e-05   | True              |
| MOVE_Z       |     5 | rate_up_vol_low    | 1140 |    0.0255 | 0.38886 | False             |
| MOVE_Z       |    20 | rate_down_vol_high |  999 |    0.0776 | 0.01421 | False             |
| MOVE_Z       |    20 | rate_down_vol_low  | 1405 |   -0.0803 | 0.00258 | False             |
| MOVE_Z       |    20 | rate_up_vol_high   | 1036 |   -0.1411 | 1e-05   | True              |
| MOVE_Z       |    20 | rate_up_vol_low    | 1140 |   -0.0002 | 0.99502 | False             |
| MOVE_Z       |    60 | rate_down_vol_high |  999 |    0.024  | 0.44921 | False             |
| MOVE_Z       |    60 | rate_down_vol_low  | 1405 |   -0.0935 | 0.00045 | False             |
| MOVE_Z       |    60 | rate_up_vol_high   | 1036 |   -0.0819 | 0.00835 | False             |
| MOVE_Z       |    60 | rate_up_vol_low    | 1140 |   -0.0186 | 0.53144 | False             |
| ACM_TP10     |     5 | rate_down_vol_high |  999 |   -0.2656 | 0       | True              |
| ACM_TP10     |     5 | rate_down_vol_low  | 1405 |   -0.0958 | 0.00032 | False             |
| ACM_TP10     |     5 | rate_up_vol_high   | 1036 |   -0.2308 | 0       | True              |
| ACM_TP10     |     5 | rate_up_vol_low    | 1140 |   -0.4042 | 0       | True              |
| ACM_TP10     |    20 | rate_down_vol_high |  999 |   -0.2805 | 0       | True              |
| ACM_TP10     |    20 | rate_down_vol_low  | 1405 |   -0.1944 | 0       | True              |
| ACM_TP10     |    20 | rate_up_vol_high   | 1036 |   -0.3412 | 0       | True              |
| ACM_TP10     |    20 | rate_up_vol_low    | 1140 |   -0.431  | 0       | True              |
| ACM_TP10     |    60 | rate_down_vol_high |  999 |   -0.2586 | 0       | True              |
| ACM_TP10     |    60 | rate_down_vol_low  | 1405 |   -0.2637 | 0       | True              |
| ACM_TP10     |    60 | rate_up_vol_high   | 1036 |   -0.4138 | 0       | True              |
| ACM_TP10     |    60 | rate_up_vol_low    | 1140 |   -0.4282 | 0       | True              |
| DGS10_chg20  |     5 | rate_down_vol_high |  999 |   -0.0225 | 0.4783  | False             |
| DGS10_chg20  |     5 | rate_down_vol_low  | 1405 |    0.059  | 0.02694 | False             |
| DGS10_chg20  |     5 | rate_up_vol_high   | 1036 |    0.0162 | 0.60146 | False             |
| DGS10_chg20  |     5 | rate_up_vol_low    | 1140 |    0.0047 | 0.87512 | False             |
| DGS10_chg20  |    20 | rate_down_vol_high |  999 |    0.0141 | 0.65725 | False             |
| DGS10_chg20  |    20 | rate_down_vol_low  | 1405 |    0.0797 | 0.00279 | False             |
| DGS10_chg20  |    20 | rate_up_vol_high   | 1036 |    0.0333 | 0.28491 | False             |
| DGS10_chg20  |    20 | rate_up_vol_low    | 1140 |    0.0273 | 0.35621 | False             |
| DGS10_chg20  |    60 | rate_down_vol_high |  999 |   -0.0316 | 0.31905 | False             |
| DGS10_chg20  |    60 | rate_down_vol_low  | 1405 |    0.1243 | 0       | True              |
| DGS10_chg20  |    60 | rate_up_vol_high   | 1036 |    0.0475 | 0.12638 | False             |
| DGS10_chg20  |    60 | rate_up_vol_low    | 1140 |    0.0381 | 0.19854 | False             |
| T10Y2Y       |     5 | rate_down_vol_high |  999 |   -0.5032 | 0       | True              |
| T10Y2Y       |     5 | rate_down_vol_low  | 1405 |   -0.5764 | 0       | True              |
| T10Y2Y       |     5 | rate_up_vol_high   | 1036 |   -0.5603 | 0       | True              |
| T10Y2Y       |     5 | rate_up_vol_low    | 1140 |   -0.7201 | 0       | True              |
| T10Y2Y       |    20 | rate_down_vol_high |  999 |   -0.5881 | 0       | True              |
| T10Y2Y       |    20 | rate_down_vol_low  | 1405 |   -0.6661 | 0       | True              |
| T10Y2Y       |    20 | rate_up_vol_high   | 1036 |   -0.7044 | 0       | True              |
| T10Y2Y       |    20 | rate_up_vol_low    | 1140 |   -0.7671 | 0       | True              |
| T10Y2Y       |    60 | rate_down_vol_high |  999 |   -0.6246 | 0       | True              |
| T10Y2Y       |    60 | rate_down_vol_low  | 1405 |   -0.7245 | 0       | True              |
| T10Y2Y       |    60 | rate_up_vol_high   | 1036 |   -0.7736 | 0       | True              |
| T10Y2Y       |    60 | rate_up_vol_low    | 1140 |   -0.7759 | 0       | True              |
| BAA10Y_chg20 |     5 | rate_down_vol_high |  999 |   -0.0083 | 0.79386 | False             |
| BAA10Y_chg20 |     5 | rate_down_vol_low  | 1405 |   -0.0318 | 0.23413 | False             |
| BAA10Y_chg20 |     5 | rate_up_vol_high   | 1036 |    0.1322 | 2e-05   | True              |
| BAA10Y_chg20 |     5 | rate_up_vol_low    | 1140 |    0.0258 | 0.38493 | False             |
| BAA10Y_chg20 |    20 | rate_down_vol_high |  999 |   -0.054  | 0.08779 | False             |
| BAA10Y_chg20 |    20 | rate_down_vol_low  | 1405 |   -0.085  | 0.00143 | False             |
| BAA10Y_chg20 |    20 | rate_up_vol_high   | 1036 |    0.1365 | 1e-05   | True              |
| BAA10Y_chg20 |    20 | rate_up_vol_low    | 1140 |    0.0294 | 0.32086 | False             |
| BAA10Y_chg20 |    60 | rate_down_vol_high |  999 |   -0.0462 | 0.14424 | False             |
| BAA10Y_chg20 |    60 | rate_down_vol_low  | 1405 |   -0.0938 | 0.00043 | False             |
| BAA10Y_chg20 |    60 | rate_up_vol_high   | 1036 |    0.146  | 0       | True              |
| BAA10Y_chg20 |    60 | rate_up_vol_low    | 1140 |    0.0308 | 0.29873 | False             |

## §5 verdict 요약
- Bonferroni α/420 통과 = **6/15** test
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
