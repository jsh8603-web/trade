# validation-tsy_long — tsy_long (TLT) sub-cluster (2026-05-31)

> Phase 5 본격 (main option A 승인 후). small-N rigor 5 의무 + AUDIT-GUIDE B/C/D/E/F/G/H/I/J/K 박제.

## §0 spec / coverage / sub-cluster meta
| 항목 | 값 |
|---|---|
| sub-cluster | tsy_long |
| 대표 ETF | TLT (duration ≈ 17, credit AAA) |
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
| MOVE_Z       |     5 | 4580 |    0.0109 |    0.46215 |          -0.0498 |           0.0623 |  2.5e-05  | 0.00049  |   0.05  | 0.95984 |   -0.000936 |    0.000985 | False             | TENTATIVE DIRECTIONAL |
| MOVE_Z       |    20 | 4580 |    0.0084 |    0.5699  |          -0.0984 |           0.1073 |  0.000333 | 0.001686 |   0.197 | 0.84354 |   -0.002972 |    0.003637 | False             | ★REJECTED             |
| MOVE_Z       |    60 | 4580 |   -0.053  |    0.00033 |          -0.193  |           0.0863 | -0.002873 | 0.004954 |  -0.58  | 0.56191 |   -0.012584 |    0.006837 | False             | PARTIAL CONFIRMED     |
| ACM_TP10     |     5 | 4580 |    0.0795 |    0       |           0.0228 |           0.1388 |  0.001542 | 0.000592 |   2.602 | 0.00927 |    0.00038  |    0.002703 | False             | ★CONFIRMED 강력       |
| ACM_TP10     |    20 | 4580 |    0.1571 |    0       |           0.0541 |           0.258  |  0.006188 | 0.002578 |   2.4   | 0.0164  |    0.001134 |    0.011241 | False             | ★CONFIRMED 강력       |
| ACM_TP10     |    60 | 4580 |    0.2449 |    0       |           0.0545 |           0.416  |  0.016386 | 0.007017 |   2.335 | 0.01953 |    0.002633 |    0.030138 | False             | ★CONFIRMED 강력       |
| DGS10_chg20  |     5 | 4580 |   -0.0002 |    0.98821 |          -0.0644 |           0.0664 | -0.003743 | 0.002943 |  -1.272 | 0.20337 |   -0.00951  |    0.002024 | False             | ★REJECTED             |
| DGS10_chg20  |    20 | 4580 |    0.0053 |    0.71876 |          -0.1022 |           0.0992 | -0.007878 | 0.009496 |  -0.83  | 0.40675 |   -0.026489 |    0.010733 | False             | ★REJECTED             |
| DGS10_chg20  |    60 | 4580 |   -0.0261 |    0.07709 |          -0.1304 |           0.0778 | -0.001247 | 0.017074 |  -0.073 | 0.94177 |   -0.034712 |    0.032218 | False             | TENTATIVE DIRECTIONAL |
| T10Y2Y       |     5 | 4580 |    0.0652 |    1e-05   |           0.0029 |           0.1269 |  0.00139  | 0.000618 |   2.248 | 0.02458 |    0.000178 |    0.002601 | False             | ★CONFIRMED 강력       |
| T10Y2Y       |    20 | 4580 |    0.1194 |    0       |           0.0216 |           0.2271 |  0.00547  | 0.002519 |   2.172 | 0.02986 |    0.000534 |    0.010406 | False             | ★CONFIRMED 강력       |
| T10Y2Y       |    60 | 4580 |    0.1882 |    0       |          -0.0091 |           0.3585 |  0.014906 | 0.006956 |   2.143 | 0.03211 |    0.001274 |    0.028539 | False             | ★CONFIRMED 강력       |
| BAA10Y_chg20 |     5 | 4580 |    0.0457 |    0.00199 |          -0.0125 |           0.1009 |  0.005908 | 0.003351 |   1.763 | 0.07795 |   -0.000661 |    0.012476 | False             | PARTIAL CONFIRMED     |
| BAA10Y_chg20 |    20 | 4580 |    0.0495 |    0.00081 |          -0.0507 |           0.1364 |  0.0222   | 0.009835 |   2.257 | 0.02399 |    0.002924 |    0.041477 | False             | ★CONFIRMED 강력       |
| BAA10Y_chg20 |    60 | 4580 |    0.0658 |    1e-05   |          -0.0487 |           0.1783 |  0.035411 | 0.025029 |   1.415 | 0.15713 |   -0.013645 |    0.084467 | False             | PARTIAL CONFIRMED     |

## §4 regime cell Rank-IC (driver × forward × 4 cells)
| driver       |   fwd | regime             |    n |   rank_ic |   raw_p | bonferroni_pass   |
|:-------------|------:|:-------------------|-----:|----------:|--------:|:------------------|
| MOVE_Z       |     5 | rate_down_vol_high |  999 |    0.0063 | 0.84133 | False             |
| MOVE_Z       |     5 | rate_down_vol_low  | 1405 |    0.071  | 0.00776 | False             |
| MOVE_Z       |     5 | rate_up_vol_high   | 1036 |   -0.1479 | 0       | True              |
| MOVE_Z       |     5 | rate_up_vol_low    | 1140 |    0.0573 | 0.05298 | False             |
| MOVE_Z       |    20 | rate_down_vol_high |  999 |    0.0099 | 0.75404 | False             |
| MOVE_Z       |    20 | rate_down_vol_low  | 1405 |    0.0611 | 0.022   | False             |
| MOVE_Z       |    20 | rate_up_vol_high   | 1036 |   -0.2451 | 0       | True              |
| MOVE_Z       |    20 | rate_up_vol_low    | 1140 |    0.0343 | 0.24659 | False             |
| MOVE_Z       |    60 | rate_down_vol_high |  999 |   -0.0425 | 0.17917 | False             |
| MOVE_Z       |    60 | rate_down_vol_low  | 1405 |    0.0423 | 0.1134  | False             |
| MOVE_Z       |    60 | rate_up_vol_high   | 1036 |   -0.3123 | 0       | True              |
| MOVE_Z       |    60 | rate_up_vol_low    | 1140 |   -0.0105 | 0.72433 | False             |
| ACM_TP10     |     5 | rate_down_vol_high |  999 |   -0.0273 | 0.38868 | False             |
| ACM_TP10     |     5 | rate_down_vol_low  | 1405 |    0.0525 | 0.04921 | False             |
| ACM_TP10     |     5 | rate_up_vol_high   | 1036 |    0.1138 | 0.00024 | False             |
| ACM_TP10     |     5 | rate_up_vol_low    | 1140 |    0.2049 | 0       | True              |
| ACM_TP10     |    20 | rate_down_vol_high |  999 |    0.0109 | 0.7306  | False             |
| ACM_TP10     |    20 | rate_down_vol_low  | 1405 |    0.0357 | 0.18151 | False             |
| ACM_TP10     |    20 | rate_up_vol_high   | 1036 |    0.2542 | 0       | True              |
| ACM_TP10     |    20 | rate_up_vol_low    | 1140 |    0.3896 | 0       | True              |
| ACM_TP10     |    60 | rate_down_vol_high |  999 |   -0.0972 | 0.0021  | False             |
| ACM_TP10     |    60 | rate_down_vol_low  | 1405 |    0.1187 | 1e-05   | True              |
| ACM_TP10     |    60 | rate_up_vol_high   | 1036 |    0.4964 | 0       | True              |
| ACM_TP10     |    60 | rate_up_vol_low    | 1140 |    0.5142 | 0       | True              |
| DGS10_chg20  |     5 | rate_down_vol_high |  999 |   -0.0265 | 0.4025  | False             |
| DGS10_chg20  |     5 | rate_down_vol_low  | 1405 |    0.049  | 0.0661  | False             |
| DGS10_chg20  |     5 | rate_up_vol_high   | 1036 |   -0.0384 | 0.21684 | False             |
| DGS10_chg20  |     5 | rate_up_vol_low    | 1140 |    0.0095 | 0.74748 | False             |
| DGS10_chg20  |    20 | rate_down_vol_high |  999 |    0.0276 | 0.38403 | False             |
| DGS10_chg20  |    20 | rate_down_vol_low  | 1405 |    0.0397 | 0.13663 | False             |
| DGS10_chg20  |    20 | rate_up_vol_high   | 1036 |   -0.0668 | 0.0315  | False             |
| DGS10_chg20  |    20 | rate_up_vol_low    | 1140 |    0.0293 | 0.32245 | False             |
| DGS10_chg20  |    60 | rate_down_vol_high |  999 |   -0.0406 | 0.1996  | False             |
| DGS10_chg20  |    60 | rate_down_vol_low  | 1405 |   -0.0199 | 0.45504 | False             |
| DGS10_chg20  |    60 | rate_up_vol_high   | 1036 |    0.0473 | 0.12775 | False             |
| DGS10_chg20  |    60 | rate_up_vol_low    | 1140 |   -0.0846 | 0.00424 | False             |
| T10Y2Y       |     5 | rate_down_vol_high |  999 |    0.019  | 0.54831 | False             |
| T10Y2Y       |     5 | rate_down_vol_low  | 1405 |    0.079  | 0.00303 | False             |
| T10Y2Y       |     5 | rate_up_vol_high   | 1036 |    0.0311 | 0.31716 | False             |
| T10Y2Y       |     5 | rate_up_vol_low    | 1140 |    0.1509 | 0       | True              |
| T10Y2Y       |    20 | rate_down_vol_high |  999 |    0.0941 | 0.00291 | False             |
| T10Y2Y       |    20 | rate_down_vol_low  | 1405 |    0.0639 | 0.01655 | False             |
| T10Y2Y       |    20 | rate_up_vol_high   | 1036 |    0.1083 | 0.00048 | False             |
| T10Y2Y       |    20 | rate_up_vol_low    | 1140 |    0.2465 | 0       | True              |
| T10Y2Y       |    60 | rate_down_vol_high |  999 |    0.0364 | 0.25028 | False             |
| T10Y2Y       |    60 | rate_down_vol_low  | 1405 |    0.1209 | 1e-05   | True              |
| T10Y2Y       |    60 | rate_up_vol_high   | 1036 |    0.265  | 0       | True              |
| T10Y2Y       |    60 | rate_up_vol_low    | 1140 |    0.3419 | 0       | True              |
| BAA10Y_chg20 |     5 | rate_down_vol_high |  999 |    0.0804 | 0.01099 | False             |
| BAA10Y_chg20 |     5 | rate_down_vol_low  | 1405 |    0.0779 | 0.00346 | False             |
| BAA10Y_chg20 |     5 | rate_up_vol_high   | 1036 |   -0.0129 | 0.67818 | False             |
| BAA10Y_chg20 |     5 | rate_up_vol_low    | 1140 |    0.0449 | 0.12955 | False             |
| BAA10Y_chg20 |    20 | rate_down_vol_high |  999 |    0.1049 | 0.0009  | False             |
| BAA10Y_chg20 |    20 | rate_down_vol_low  | 1405 |    0.0208 | 0.43687 | False             |
| BAA10Y_chg20 |    20 | rate_up_vol_high   | 1036 |    0.0433 | 0.16352 | False             |
| BAA10Y_chg20 |    20 | rate_up_vol_low    | 1140 |    0.0429 | 0.14762 | False             |
| BAA10Y_chg20 |    60 | rate_down_vol_high |  999 |    0.1589 | 0       | True              |
| BAA10Y_chg20 |    60 | rate_down_vol_low  | 1405 |    0.0303 | 0.25563 | False             |
| BAA10Y_chg20 |    60 | rate_up_vol_high   | 1036 |   -0.0216 | 0.48701 | False             |
| BAA10Y_chg20 |    60 | rate_up_vol_low    | 1140 |    0.1649 | 0       | True              |

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
