# validation-tsy_short — tsy_short (SHY) sub-cluster (2026-05-31)

> Phase 5 본격 (main option A 승인 후). small-N rigor 5 의무 + AUDIT-GUIDE B/C/D/E/F/G/H/I/J/K 박제.

## §0 spec / coverage / sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | tsy_short |
| 대표 ETF | SHY (duration ≈ 2, credit AAA) |
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
| MOVE_Z       |     5 | 4580 |   -0.009  |    0.54202 |          -0.0839 |           0.0498 |  1e-06    | 4.7e-05  |   0.02  | 0.98368 |   -9.1e-05  |    9.3e-05  | False             | ★REJECTED             |
| MOVE_Z       |    20 | 4580 |   -0.0398 |    0.00713 |          -0.15   |           0.0506 | -0.000115 | 0.000199 |  -0.581 | 0.56157 |   -0.000505 |    0.000274 | False             | PARTIAL CONFIRMED     |
| MOVE_Z       |    60 | 4580 |   -0.129  |    0       |          -0.2933 |           0.0239 | -0.001021 | 0.000581 |  -1.759 | 0.07864 |   -0.002159 |    0.000117 | False             | PARTIAL CONFIRMED     |
| ACM_TP10     |     5 | 4580 |    0.0977 |    0       |           0.0292 |           0.1723 |  0.000109 | 5.8e-05  |   1.885 | 0.05942 |   -4e-06    |    0.000221 | False             | PARTIAL CONFIRMED     |
| ACM_TP10     |    20 | 4580 |    0.1216 |    0       |           0.0152 |           0.2269 |  0.000411 | 0.000235 |   1.746 | 0.08086 |   -5e-05    |    0.000872 | False             | PARTIAL CONFIRMED     |
| ACM_TP10     |    60 | 4580 |    0.14   |    0       |          -0.056  |           0.322  |  0.00088  | 0.000714 |   1.233 | 0.21739 |   -0.000518 |    0.002279 | False             | PARTIAL CONFIRMED     |
| DGS10_chg20  |     5 | 4580 |    0.0051 |    0.73232 |          -0.0574 |           0.0717 | -0.000124 | 0.000243 |  -0.51  | 0.60973 |   -0.000601 |    0.000353 | False             | ★REJECTED             |
| DGS10_chg20  |    20 | 4580 |   -0.0169 |    0.2531  |          -0.1183 |           0.074  | -0.000474 | 0.000922 |  -0.515 | 0.60678 |   -0.002281 |    0.001332 | False             | TENTATIVE DIRECTIONAL |
| DGS10_chg20  |    60 | 4580 |   -0.0071 |    0.6321  |          -0.1117 |           0.1052 |  0.000609 | 0.001856 |   0.328 | 0.74286 |   -0.003028 |    0.004246 | False             | ★REJECTED             |
| T10Y2Y       |     5 | 4580 |   -0.019  |    0.19885 |          -0.0924 |           0.0519 | -9.8e-05  | 7e-05    |  -1.401 | 0.16118 |   -0.000236 |    3.9e-05  | False             | TENTATIVE DIRECTIONAL |
| T10Y2Y       |    20 | 4580 |   -0.1023 |    0       |          -0.2146 |           0.0226 | -0.000399 | 0.000271 |  -1.471 | 0.14134 |   -0.00093  |    0.000133 | False             | PARTIAL CONFIRMED     |
| T10Y2Y       |    60 | 4580 |   -0.1666 |    0       |          -0.3633 |           0.0538 | -0.001473 | 0.000795 |  -1.853 | 0.06394 |   -0.003032 |    8.5e-05  | False             | PARTIAL CONFIRMED     |
| BAA10Y_chg20 |     5 | 4580 |    0.022  |    0.13739 |          -0.0426 |           0.07   |  0.000439 | 0.000258 |   1.704 | 0.08845 |   -6.6e-05  |    0.000944 | False             | TENTATIVE DIRECTIONAL |
| BAA10Y_chg20 |    20 | 4580 |    0.0187 |    0.20577 |          -0.0807 |           0.1106 |  0.00137  | 0.001035 |   1.323 | 0.18575 |   -0.000659 |    0.003399 | False             | TENTATIVE DIRECTIONAL |
| BAA10Y_chg20 |    60 | 4580 |   -0.014  |    0.34449 |          -0.1338 |           0.1025 |  0.00132  | 0.002284 |   0.578 | 0.56343 |   -0.003158 |    0.005797 | False             | TENTATIVE DIRECTIONAL |

## §4 regime cell Rank-IC (driver × forward × 4 cells)
| driver       |   fwd | regime             |    n |   rank_ic |   raw_p | bonferroni_pass   |
|:-------------|------:|:-------------------|-----:|----------:|--------:|:------------------|
| MOVE_Z       |     5 | rate_down_vol_high |  999 |    0.0696 | 0.02788 | False             |
| MOVE_Z       |     5 | rate_down_vol_low  | 1405 |    0.0748 | 0.00504 | False             |
| MOVE_Z       |     5 | rate_up_vol_high   | 1036 |   -0.1396 | 1e-05   | True              |
| MOVE_Z       |     5 | rate_up_vol_low    | 1140 |   -0.0029 | 0.92095 | False             |
| MOVE_Z       |    20 | rate_down_vol_high |  999 |    0.0479 | 0.13012 | False             |
| MOVE_Z       |    20 | rate_down_vol_low  | 1405 |    0.0821 | 0.00207 | False             |
| MOVE_Z       |    20 | rate_up_vol_high   | 1036 |   -0.1544 | 0       | True              |
| MOVE_Z       |    20 | rate_up_vol_low    | 1140 |   -0.0217 | 0.4646  | False             |
| MOVE_Z       |    60 | rate_down_vol_high |  999 |    0.0406 | 0.20014 | False             |
| MOVE_Z       |    60 | rate_down_vol_low  | 1405 |   -0.0235 | 0.37796 | False             |
| MOVE_Z       |    60 | rate_up_vol_high   | 1036 |   -0.2891 | 0       | True              |
| MOVE_Z       |    60 | rate_up_vol_low    | 1140 |   -0.0371 | 0.21038 | False             |
| ACM_TP10     |     5 | rate_down_vol_high |  999 |   -0.0372 | 0.2401  | False             |
| ACM_TP10     |     5 | rate_down_vol_low  | 1405 |    0.0413 | 0.12198 | False             |
| ACM_TP10     |     5 | rate_up_vol_high   | 1036 |    0.1978 | 0       | True              |
| ACM_TP10     |     5 | rate_up_vol_low    | 1140 |    0.1952 | 0       | True              |
| ACM_TP10     |    20 | rate_down_vol_high |  999 |   -0.071  | 0.02488 | False             |
| ACM_TP10     |    20 | rate_down_vol_low  | 1405 |    0.0215 | 0.42086 | False             |
| ACM_TP10     |    20 | rate_up_vol_high   | 1036 |    0.3058 | 0       | True              |
| ACM_TP10     |    20 | rate_up_vol_low    | 1140 |    0.2325 | 0       | True              |
| ACM_TP10     |    60 | rate_down_vol_high |  999 |   -0.1868 | 0       | True              |
| ACM_TP10     |    60 | rate_down_vol_low  | 1405 |    0.0845 | 0.00152 | False             |
| ACM_TP10     |    60 | rate_up_vol_high   | 1036 |    0.4296 | 0       | True              |
| ACM_TP10     |    60 | rate_up_vol_low    | 1140 |    0.1841 | 0       | True              |
| DGS10_chg20  |     5 | rate_down_vol_high |  999 |   -0.0263 | 0.40618 | False             |
| DGS10_chg20  |     5 | rate_down_vol_low  | 1405 |    0.0927 | 0.00051 | False             |
| DGS10_chg20  |     5 | rate_up_vol_high   | 1036 |   -0.0063 | 0.84067 | False             |
| DGS10_chg20  |     5 | rate_up_vol_low    | 1140 |   -0.0139 | 0.63969 | False             |
| DGS10_chg20  |    20 | rate_down_vol_high |  999 |   -0.0722 | 0.02239 | False             |
| DGS10_chg20  |    20 | rate_down_vol_low  | 1405 |    0.0899 | 0.00074 | False             |
| DGS10_chg20  |    20 | rate_up_vol_high   | 1036 |   -0.0092 | 0.76761 | False             |
| DGS10_chg20  |    20 | rate_up_vol_low    | 1140 |   -0.027  | 0.36167 | False             |
| DGS10_chg20  |    60 | rate_down_vol_high |  999 |    0.0214 | 0.4989  | False             |
| DGS10_chg20  |    60 | rate_down_vol_low  | 1405 |   -0.0089 | 0.73871 | False             |
| DGS10_chg20  |    60 | rate_up_vol_high   | 1036 |    0.0765 | 0.01375 | False             |
| DGS10_chg20  |    60 | rate_up_vol_low    | 1140 |   -0.0943 | 0.00144 | False             |
| T10Y2Y       |     5 | rate_down_vol_high |  999 |   -0.0662 | 0.03644 | False             |
| T10Y2Y       |     5 | rate_down_vol_low  | 1405 |   -0.0545 | 0.04092 | False             |
| T10Y2Y       |     5 | rate_up_vol_high   | 1036 |   -0.0132 | 0.67208 | False             |
| T10Y2Y       |     5 | rate_up_vol_low    | 1140 |    0.0463 | 0.11841 | False             |
| T10Y2Y       |    20 | rate_down_vol_high |  999 |   -0.1292 | 4e-05   | True              |
| T10Y2Y       |    20 | rate_down_vol_low  | 1405 |   -0.1963 | 0       | True              |
| T10Y2Y       |    20 | rate_up_vol_high   | 1036 |   -0.0208 | 0.50464 | False             |
| T10Y2Y       |    20 | rate_up_vol_low    | 1140 |   -0.0739 | 0.01258 | False             |
| T10Y2Y       |    60 | rate_down_vol_high |  999 |   -0.2789 | 0       | True              |
| T10Y2Y       |    60 | rate_down_vol_low  | 1405 |   -0.2529 | 0       | True              |
| T10Y2Y       |    60 | rate_up_vol_high   | 1036 |    0.038  | 0.22146 | False             |
| T10Y2Y       |    60 | rate_up_vol_low    | 1140 |   -0.2053 | 0       | True              |
| BAA10Y_chg20 |     5 | rate_down_vol_high |  999 |    0.0663 | 0.03614 | False             |
| BAA10Y_chg20 |     5 | rate_down_vol_low  | 1405 |   -0.0091 | 0.73464 | False             |
| BAA10Y_chg20 |     5 | rate_up_vol_high   | 1036 |    0.0139 | 0.65419 | False             |
| BAA10Y_chg20 |     5 | rate_up_vol_low    | 1140 |    0.0482 | 0.10408 | False             |
| BAA10Y_chg20 |    20 | rate_down_vol_high |  999 |    0.1111 | 0.00044 | False             |
| BAA10Y_chg20 |    20 | rate_down_vol_low  | 1405 |   -0.0489 | 0.06682 | False             |
| BAA10Y_chg20 |    20 | rate_up_vol_high   | 1036 |    0.0414 | 0.18277 | False             |
| BAA10Y_chg20 |    20 | rate_up_vol_low    | 1140 |    0.0404 | 0.17267 | False             |
| BAA10Y_chg20 |    60 | rate_down_vol_high |  999 |   -0.054  | 0.08815 | False             |
| BAA10Y_chg20 |    60 | rate_down_vol_low  | 1405 |   -0.0369 | 0.16678 | False             |
| BAA10Y_chg20 |    60 | rate_up_vol_high   | 1036 |    0.0293 | 0.34589 | False             |
| BAA10Y_chg20 |    60 | rate_up_vol_low    | 1140 |    0.1276 | 2e-05   | True              |

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
