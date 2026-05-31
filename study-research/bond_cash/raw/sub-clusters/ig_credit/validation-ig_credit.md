# validation-ig_credit — ig_credit (LQD) sub-cluster (2026-05-31)

> Phase 5 본격 (main option A 승인 후). small-N rigor 5 의무 + AUDIT-GUIDE B/C/D/E/F/G/H/I/J/K 박제.

## §0 spec / coverage / sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | ig_credit |
| 대표 ETF | LQD (duration ≈ 8, credit A-/BBB+) |
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
| driver       |   fwd |    n |   rank_ic |   ic_raw_p |   ic_block_ci_lo |   ic_block_ci_hi |      beta |   hac_se |   hac_t |   hac_p |   hac_ci_lo |   hac_ci_hi | bonferroni_pass   | verdict           |
|:-------------|------:|-----:|----------:|-----------:|-----------------:|-----------------:|----------:|---------:|--------:|--------:|------------:|------------:|:------------------|:------------------|
| MOVE_Z       |     5 | 4580 |    0.0086 |    0.55978 |          -0.0572 |           0.0663 | -0.000214 | 0.000466 |  -0.46  | 0.64575 |   -0.001127 |    0.000699 | False             | ★REJECTED         |
| MOVE_Z       |    20 | 4580 |    0.0035 |    0.81118 |          -0.1057 |           0.0898 |  0.000479 | 0.001064 |   0.451 | 0.65228 |   -0.001605 |    0.002564 | False             | ★REJECTED         |
| MOVE_Z       |    60 | 4580 |   -0.0433 |    0.00334 |          -0.1865 |           0.1108 | -0.000126 | 0.003368 |  -0.037 | 0.97024 |   -0.006727 |    0.006476 | False             | PARTIAL CONFIRMED |
| ACM_TP10     |     5 | 4580 |    0.0776 |    0       |           0.0112 |           0.1372 |  0.000778 | 0.000396 |   1.965 | 0.04942 |    2e-06    |    0.001554 | False             | PARTIAL CONFIRMED |
| ACM_TP10     |    20 | 4580 |    0.1413 |    0       |           0.0216 |           0.2432 |  0.002907 | 0.001443 |   2.015 | 0.04395 |    7.9e-05  |    0.005736 | False             | ★CONFIRMED 강력   |
| ACM_TP10     |    60 | 4580 |    0.2178 |    0       |           0.024  |           0.3889 |  0.008295 | 0.003775 |   2.198 | 0.02798 |    0.000897 |    0.015693 | False             | ★CONFIRMED 강력   |
| DGS10_chg20  |     5 | 4580 |   -0.0082 |    0.57714 |          -0.0711 |           0.0507 | -0.001063 | 0.00262  |  -0.406 | 0.68501 |   -0.006197 |    0.004072 | False             | ★REJECTED         |
| DGS10_chg20  |    20 | 4580 |   -0.0354 |    0.01662 |          -0.1292 |           0.0583 | -0.009333 | 0.00741  |  -1.259 | 0.20787 |   -0.023856 |    0.005191 | False             | PARTIAL CONFIRMED |
| DGS10_chg20  |    60 | 4580 |   -0.0597 |    5e-05   |          -0.1753 |           0.0586 | -0.002499 | 0.010884 |  -0.23  | 0.81842 |   -0.023831 |    0.018834 | False             | PARTIAL CONFIRMED |
| T10Y2Y       |     5 | 4580 |    0.0545 |    0.00023 |          -0.0094 |           0.1183 |  0.000583 | 0.000343 |   1.7   | 0.08913 |   -8.9e-05  |    0.001255 | False             | PARTIAL CONFIRMED |
| T10Y2Y       |    20 | 4580 |    0.1002 |    0       |          -0.0087 |           0.2076 |  0.002253 | 0.00136  |   1.657 | 0.09757 |   -0.000412 |    0.004917 | False             | PARTIAL CONFIRMED |
| T10Y2Y       |    60 | 4580 |    0.1553 |    0       |          -0.0391 |           0.3243 |  0.00604  | 0.003428 |   1.762 | 0.07808 |   -0.000679 |    0.012759 | False             | PARTIAL CONFIRMED |
| BAA10Y_chg20 |     5 | 4580 |    0.0455 |    0.00206 |          -0.0195 |           0.1044 |  0.005254 | 0.004256 |   1.234 | 0.21706 |   -0.003088 |    0.013597 | False             | PARTIAL CONFIRMED |
| BAA10Y_chg20 |    20 | 4580 |    0.0622 |    2e-05   |          -0.0488 |           0.1514 |  0.019646 | 0.008851 |   2.22  | 0.02643 |    0.0023   |    0.036993 | False             | ★CONFIRMED 강력   |
| BAA10Y_chg20 |    60 | 4580 |    0.0692 |    0       |          -0.0368 |           0.2045 |  0.035016 | 0.021646 |   1.618 | 0.10573 |   -0.007409 |    0.07744  | False             | PARTIAL CONFIRMED |

## §4 regime cell Rank-IC (driver × forward × 4 cells)
| driver       |   fwd | regime             |    n |   rank_ic |   raw_p | bonferroni_pass   |
|:-------------|------:|:-------------------|-----:|----------:|--------:|:------------------|
| MOVE_Z       |     5 | rate_down_vol_high |  999 |    0.0494 | 0.11841 | False             |
| MOVE_Z       |     5 | rate_down_vol_low  | 1405 |    0.1165 | 1e-05   | True              |
| MOVE_Z       |     5 | rate_up_vol_high   | 1036 |   -0.0987 | 0.00147 | False             |
| MOVE_Z       |     5 | rate_up_vol_low    | 1140 |    0.0425 | 0.1513  | False             |
| MOVE_Z       |    20 | rate_down_vol_high |  999 |    0.0429 | 0.17575 | False             |
| MOVE_Z       |    20 | rate_down_vol_low  | 1405 |    0.1602 | 0       | True              |
| MOVE_Z       |    20 | rate_up_vol_high   | 1036 |   -0.1707 | 0       | True              |
| MOVE_Z       |    20 | rate_up_vol_low    | 1140 |    0.081  | 0.00621 | False             |
| MOVE_Z       |    60 | rate_down_vol_high |  999 |   -0.0235 | 0.45823 | False             |
| MOVE_Z       |    60 | rate_down_vol_low  | 1405 |    0.0535 | 0.04507 | False             |
| MOVE_Z       |    60 | rate_up_vol_high   | 1036 |   -0.1994 | 0       | True              |
| MOVE_Z       |    60 | rate_up_vol_low    | 1140 |   -0.0131 | 0.65834 | False             |
| ACM_TP10     |     5 | rate_down_vol_high |  999 |   -0.0349 | 0.27107 | False             |
| ACM_TP10     |     5 | rate_down_vol_low  | 1405 |    0.0454 | 0.08871 | False             |
| ACM_TP10     |     5 | rate_up_vol_high   | 1036 |    0.1506 | 0       | True              |
| ACM_TP10     |     5 | rate_up_vol_low    | 1140 |    0.1987 | 0       | True              |
| ACM_TP10     |    20 | rate_down_vol_high |  999 |   -0.0707 | 0.0254  | False             |
| ACM_TP10     |    20 | rate_down_vol_low  | 1405 |    0.0656 | 0.01398 | False             |
| ACM_TP10     |    20 | rate_up_vol_high   | 1036 |    0.3347 | 0       | True              |
| ACM_TP10     |    20 | rate_up_vol_low    | 1140 |    0.3407 | 0       | True              |
| ACM_TP10     |    60 | rate_down_vol_high |  999 |   -0.1225 | 0.0001  | True              |
| ACM_TP10     |    60 | rate_down_vol_low  | 1405 |    0.1529 | 0       | True              |
| ACM_TP10     |    60 | rate_up_vol_high   | 1036 |    0.5123 | 0       | True              |
| ACM_TP10     |    60 | rate_up_vol_low    | 1140 |    0.4113 | 0       | True              |
| DGS10_chg20  |     5 | rate_down_vol_high |  999 |   -0.0877 | 0.00553 | False             |
| DGS10_chg20  |     5 | rate_down_vol_low  | 1405 |    0.0861 | 0.00124 | False             |
| DGS10_chg20  |     5 | rate_up_vol_high   | 1036 |   -0.0231 | 0.45807 | False             |
| DGS10_chg20  |     5 | rate_up_vol_low    | 1140 |    0.0181 | 0.541   | False             |
| DGS10_chg20  |    20 | rate_down_vol_high |  999 |   -0.1819 | 0       | True              |
| DGS10_chg20  |    20 | rate_down_vol_low  | 1405 |    0.1006 | 0.00016 | False             |
| DGS10_chg20  |    20 | rate_up_vol_high   | 1036 |    0.0304 | 0.32812 | False             |
| DGS10_chg20  |    20 | rate_up_vol_low    | 1140 |   -0.016  | 0.58905 | False             |
| DGS10_chg20  |    60 | rate_down_vol_high |  999 |   -0.2137 | 0       | True              |
| DGS10_chg20  |    60 | rate_down_vol_low  | 1405 |   -0.0568 | 0.0332  | False             |
| DGS10_chg20  |    60 | rate_up_vol_high   | 1036 |    0.1465 | 0       | True              |
| DGS10_chg20  |    60 | rate_up_vol_low    | 1140 |   -0.0722 | 0.01471 | False             |
| T10Y2Y       |     5 | rate_down_vol_high |  999 |   -0.0537 | 0.0899  | False             |
| T10Y2Y       |     5 | rate_down_vol_low  | 1405 |    0.0715 | 0.00733 | False             |
| T10Y2Y       |     5 | rate_up_vol_high   | 1036 |    0.0429 | 0.16738 | False             |
| T10Y2Y       |     5 | rate_up_vol_low    | 1140 |    0.1485 | 0       | True              |
| T10Y2Y       |    20 | rate_down_vol_high |  999 |   -0.0722 | 0.0225  | False             |
| T10Y2Y       |    20 | rate_down_vol_low  | 1405 |    0.0956 | 0.00033 | False             |
| T10Y2Y       |    20 | rate_up_vol_high   | 1036 |    0.1536 | 0       | True              |
| T10Y2Y       |    20 | rate_up_vol_low    | 1140 |    0.2097 | 0       | True              |
| T10Y2Y       |    60 | rate_down_vol_high |  999 |   -0.0184 | 0.56063 | False             |
| T10Y2Y       |    60 | rate_down_vol_low  | 1405 |    0.1689 | 0       | True              |
| T10Y2Y       |    60 | rate_up_vol_high   | 1036 |    0.2473 | 0       | True              |
| T10Y2Y       |    60 | rate_up_vol_low    | 1140 |    0.2478 | 0       | True              |
| BAA10Y_chg20 |     5 | rate_down_vol_high |  999 |    0.1338 | 2e-05   | True              |
| BAA10Y_chg20 |     5 | rate_down_vol_low  | 1405 |    0.0444 | 0.09652 | False             |
| BAA10Y_chg20 |     5 | rate_up_vol_high   | 1036 |   -0.0207 | 0.505   | False             |
| BAA10Y_chg20 |     5 | rate_up_vol_low    | 1140 |    0.0426 | 0.15099 | False             |
| BAA10Y_chg20 |    20 | rate_down_vol_high |  999 |    0.2586 | 0       | True              |
| BAA10Y_chg20 |    20 | rate_down_vol_low  | 1405 |   -0.0072 | 0.78738 | False             |
| BAA10Y_chg20 |    20 | rate_up_vol_high   | 1036 |   -0.0007 | 0.98094 | False             |
| BAA10Y_chg20 |    20 | rate_up_vol_low    | 1140 |    0.0043 | 0.88435 | False             |
| BAA10Y_chg20 |    60 | rate_down_vol_high |  999 |    0.2734 | 0       | True              |
| BAA10Y_chg20 |    60 | rate_down_vol_low  | 1405 |    0.0917 | 0.00058 | False             |
| BAA10Y_chg20 |    60 | rate_up_vol_high   | 1036 |   -0.0508 | 0.10245 | False             |
| BAA10Y_chg20 |    60 | rate_up_vol_low    | 1140 |    0.0173 | 0.55963 | False             |

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
