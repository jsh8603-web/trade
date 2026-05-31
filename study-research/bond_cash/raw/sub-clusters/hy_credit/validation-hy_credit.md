# validation-hy_credit — hy_credit (HYG) sub-cluster (2026-05-31)

> Phase 5 본격 (main option A 승인 후). small-N rigor 5 의무 + AUDIT-GUIDE B/C/D/E/F/G/H/I/J/K 박제.

## §0 spec / coverage / sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | hy_credit |
| 대표 ETF | HYG (duration ≈ 4, credit B+/BB) |
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
| MOVE_Z       |     5 | 4580 |    0.0072 |    0.62503 |          -0.0513 |           0.0696 | -0.000255 | 0.000513 |  -0.496 | 0.61968 |   -0.00126  |    0.000751 | False             | ★REJECTED             |
| MOVE_Z       |    20 | 4580 |   -0.0079 |    0.59493 |          -0.1108 |           0.0872 | -0.000505 | 0.001397 |  -0.361 | 0.71787 |   -0.003243 |    0.002234 | False             | ★REJECTED             |
| MOVE_Z       |    60 | 4580 |   -0.0026 |    0.85951 |          -0.1511 |           0.1409 | -0.000311 | 0.002153 |  -0.144 | 0.8853  |   -0.004531 |    0.00391  | False             | ★REJECTED             |
| ACM_TP10     |     5 | 4580 |    0.028  |    0.05797 |          -0.0261 |           0.0905 |  8.9e-05  | 0.0006   |   0.148 | 0.88256 |   -0.001087 |    0.001264 | False             | TENTATIVE DIRECTIONAL |
| ACM_TP10     |    20 | 4580 |    0.0589 |    7e-05   |          -0.0564 |           0.1716 |  0.000971 | 0.002137 |   0.454 | 0.64953 |   -0.003218 |    0.00516  | False             | PARTIAL CONFIRMED     |
| ACM_TP10     |    60 | 4580 |    0.1511 |    0       |          -0.0209 |           0.3227 |  0.005144 | 0.004789 |   1.074 | 0.28279 |   -0.004243 |    0.01453  | False             | PARTIAL CONFIRMED     |
| DGS10_chg20  |     5 | 4580 |   -0.0919 |    0       |          -0.154  |          -0.0328 | -0.005901 | 0.003401 |  -1.735 | 0.08275 |   -0.012566 |    0.000765 | False             | PARTIAL CONFIRMED     |
| DGS10_chg20  |    20 | 4580 |   -0.1466 |    0       |          -0.2384 |          -0.0545 | -0.024274 | 0.011121 |  -2.183 | 0.02906 |   -0.046071 |   -0.002477 | False             | ★CONFIRMED 강력       |
| DGS10_chg20  |    60 | 4580 |   -0.0703 |    0       |          -0.1916 |           0.0542 | -0.00522  | 0.011637 |  -0.449 | 0.65376 |   -0.028027 |    0.017588 | False             | PARTIAL CONFIRMED     |
| T10Y2Y       |     5 | 4580 |    0.0262 |    0.07648 |          -0.0338 |           0.0911 |  0.000161 | 0.000437 |   0.368 | 0.71287 |   -0.000696 |    0.001018 | False             | TENTATIVE DIRECTIONAL |
| T10Y2Y       |    20 | 4580 |    0.0472 |    0.00139 |          -0.0602 |           0.1548 |  0.001084 | 0.001549 |   0.7   | 0.48409 |   -0.001952 |    0.00412  | False             | PARTIAL CONFIRMED     |
| T10Y2Y       |    60 | 4580 |    0.0968 |    0       |          -0.0683 |           0.2617 |  0.004075 | 0.003652 |   1.116 | 0.26457 |   -0.003084 |    0.011234 | False             | PARTIAL CONFIRMED     |
| BAA10Y_chg20 |     5 | 4580 |    0.0687 |    0       |           0.0097 |           0.1356 |  0.003359 | 0.004789 |   0.701 | 0.48305 |   -0.006028 |    0.012747 | False             | PARTIAL CONFIRMED     |
| BAA10Y_chg20 |    20 | 4580 |    0.0914 |    0       |          -0.0174 |           0.1967 |  0.008512 | 0.013453 |   0.633 | 0.52689 |   -0.017854 |    0.034879 | False             | PARTIAL CONFIRMED     |
| BAA10Y_chg20 |    60 | 4580 |    0.0182 |    0.21836 |          -0.1044 |           0.1701 |  0.007498 | 0.01861  |   0.403 | 0.68701 |   -0.028976 |    0.043973 | False             | TENTATIVE DIRECTIONAL |

## §4 regime cell Rank-IC (driver × forward × 4 cells)
| driver       |   fwd | regime             |    n |   rank_ic |   raw_p | bonferroni_pass   |
|:-------------|------:|:-------------------|-----:|----------:|--------:|:------------------|
| MOVE_Z       |     5 | rate_down_vol_high |  999 |    0.0596 | 0.05948 | False             |
| MOVE_Z       |     5 | rate_down_vol_low  | 1405 |    0.0317 | 0.23512 | False             |
| MOVE_Z       |     5 | rate_up_vol_high   | 1036 |    0.0236 | 0.44713 | False             |
| MOVE_Z       |     5 | rate_up_vol_low    | 1140 |   -0.016  | 0.58987 | False             |
| MOVE_Z       |    20 | rate_down_vol_high |  999 |    0.0304 | 0.33753 | False             |
| MOVE_Z       |    20 | rate_down_vol_low  | 1405 |    0.0606 | 0.02303 | False             |
| MOVE_Z       |    20 | rate_up_vol_high   | 1036 |   -0.0753 | 0.01539 | False             |
| MOVE_Z       |    20 | rate_up_vol_low    | 1140 |    0.0489 | 0.09869 | False             |
| MOVE_Z       |    60 | rate_down_vol_high |  999 |   -0.0494 | 0.11861 | False             |
| MOVE_Z       |    60 | rate_down_vol_low  | 1405 |    0.0392 | 0.14188 | False             |
| MOVE_Z       |    60 | rate_up_vol_high   | 1036 |   -0.1513 | 0       | True              |
| MOVE_Z       |    60 | rate_up_vol_low    | 1140 |    0.0293 | 0.32223 | False             |
| ACM_TP10     |     5 | rate_down_vol_high |  999 |   -0.0176 | 0.57876 | False             |
| ACM_TP10     |     5 | rate_down_vol_low  | 1405 |   -0.0042 | 0.87371 | False             |
| ACM_TP10     |     5 | rate_up_vol_high   | 1036 |    0.1016 | 0.00106 | False             |
| ACM_TP10     |     5 | rate_up_vol_low    | 1140 |    0.0894 | 0.00252 | False             |
| ACM_TP10     |    20 | rate_down_vol_high |  999 |   -0.0419 | 0.18598 | False             |
| ACM_TP10     |    20 | rate_down_vol_low  | 1405 |    0.0525 | 0.04912 | False             |
| ACM_TP10     |    20 | rate_up_vol_high   | 1036 |    0.1944 | 0       | True              |
| ACM_TP10     |    20 | rate_up_vol_low    | 1140 |    0.1112 | 0.00017 | False             |
| ACM_TP10     |    60 | rate_down_vol_high |  999 |    0.1735 | 0       | True              |
| ACM_TP10     |    60 | rate_down_vol_low  | 1405 |    0.0083 | 0.75601 | False             |
| ACM_TP10     |    60 | rate_up_vol_high   | 1036 |    0.4067 | 0       | True              |
| ACM_TP10     |    60 | rate_up_vol_low    | 1140 |    0.1145 | 0.00011 | True              |
| DGS10_chg20  |     5 | rate_down_vol_high |  999 |   -0.2019 | 0       | True              |
| DGS10_chg20  |     5 | rate_down_vol_low  | 1405 |   -0.0552 | 0.03855 | False             |
| DGS10_chg20  |     5 | rate_up_vol_high   | 1036 |   -0.0331 | 0.28724 | False             |
| DGS10_chg20  |     5 | rate_up_vol_low    | 1140 |   -0.0203 | 0.49406 | False             |
| DGS10_chg20  |    20 | rate_down_vol_high |  999 |   -0.351  | 0       | True              |
| DGS10_chg20  |    20 | rate_down_vol_low  | 1405 |   -0.1063 | 7e-05   | True              |
| DGS10_chg20  |    20 | rate_up_vol_high   | 1036 |    0.0707 | 0.02278 | False             |
| DGS10_chg20  |    20 | rate_up_vol_low    | 1140 |   -0.117  | 7e-05   | True              |
| DGS10_chg20  |    60 | rate_down_vol_high |  999 |   -0.2041 | 0       | True              |
| DGS10_chg20  |    60 | rate_down_vol_low  | 1405 |   -0.0966 | 0.00029 | False             |
| DGS10_chg20  |    60 | rate_up_vol_high   | 1036 |    0.2034 | 0       | True              |
| DGS10_chg20  |    60 | rate_up_vol_low    | 1140 |   -0.0307 | 0.30063 | False             |
| T10Y2Y       |     5 | rate_down_vol_high |  999 |   -0.0446 | 0.15882 | False             |
| T10Y2Y       |     5 | rate_down_vol_low  | 1405 |    0.0294 | 0.2703  | False             |
| T10Y2Y       |     5 | rate_up_vol_high   | 1036 |    0.0316 | 0.30932 | False             |
| T10Y2Y       |     5 | rate_up_vol_low    | 1140 |    0.0829 | 0.00509 | False             |
| T10Y2Y       |    20 | rate_down_vol_high |  999 |   -0.0678 | 0.03225 | False             |
| T10Y2Y       |    20 | rate_down_vol_low  | 1405 |    0.0964 | 0.00029 | False             |
| T10Y2Y       |    20 | rate_up_vol_high   | 1036 |    0.0546 | 0.07896 | False             |
| T10Y2Y       |    20 | rate_up_vol_low    | 1140 |    0.0905 | 0.00221 | False             |
| T10Y2Y       |    60 | rate_down_vol_high |  999 |    0.1743 | 0       | True              |
| T10Y2Y       |    60 | rate_down_vol_low  | 1405 |    0.0839 | 0.00165 | False             |
| T10Y2Y       |    60 | rate_up_vol_high   | 1036 |    0.1648 | 0       | True              |
| T10Y2Y       |    60 | rate_up_vol_low    | 1140 |    0.0334 | 0.25965 | False             |
| BAA10Y_chg20 |     5 | rate_down_vol_high |  999 |    0.1609 | 0       | True              |
| BAA10Y_chg20 |     5 | rate_down_vol_low  | 1405 |    0.0893 | 0.0008  | False             |
| BAA10Y_chg20 |     5 | rate_up_vol_high   | 1036 |   -0.0302 | 0.33098 | False             |
| BAA10Y_chg20 |     5 | rate_up_vol_low    | 1140 |    0.0101 | 0.73288 | False             |
| BAA10Y_chg20 |    20 | rate_down_vol_high |  999 |    0.2504 | 0       | True              |
| BAA10Y_chg20 |    20 | rate_down_vol_low  | 1405 |    0.1185 | 1e-05   | True              |
| BAA10Y_chg20 |    20 | rate_up_vol_high   | 1036 |   -0.0688 | 0.02679 | False             |
| BAA10Y_chg20 |    20 | rate_up_vol_low    | 1140 |    0.0067 | 0.82188 | False             |
| BAA10Y_chg20 |    60 | rate_down_vol_high |  999 |    0.2366 | 0       | True              |
| BAA10Y_chg20 |    60 | rate_down_vol_low  | 1405 |    0.03   | 0.26036 | False             |
| BAA10Y_chg20 |    60 | rate_up_vol_high   | 1036 |   -0.145  | 0       | True              |
| BAA10Y_chg20 |    60 | rate_up_vol_low    | 1140 |   -0.1125 | 0.00014 | False             |

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
