---
tags: [type/validation, study/crypto, cycle/2, hypothesis/h8]
date: 2026-05-31
hypothesis: H8 — TxCnt utility count proxy → fwd_30d_ret (Catalini&Gans 2020)
audit_axes: [A, B, D, F, G, I, K]
note: 원래 TxTfrValAdjUSD (value-weighted) 권장이나 community 403 → TxCnt (count) 대체
---

# validation-h8 — TxCnt utility → fwd_30d_ret (BTC)

## Data Coverage
- 시리즈: CoinMetrics community `TxCnt` daily (TxTfrValAdjUSD=403 대체)
- 기간: 2017-08-17 ~ 2026-05-30
- Binance klines inner join 후: n_total = **3178**
- N_eff full: 47

## 변수 정의 (TxCnt count proxy 한계 명시)
- (a) 시제: contemporaneous + fwd_30d
- (b) frequency: daily
- (c) transform: log + first difference
- (d) conditioning: macro epoch × halving + BlkCnt control (mining capacity 분리)
- (e) regime: full + epoch 4종 × halving
- ⚠️ count proxy 한계: average tx size 정보 손실. value-weighted (TxVolUSD) 후속 paid tier 권고.

## H8 검증 결과
- **full Rank-IC (Δlog_tx → fwd_30d_ret) = 0.0022** (n=3178)
- **β OLS = 2.775578e-03**, Block bootstrap CI95% (block=60d, B=2000) = [-1.325703e-02, 1.804660e-02]
- Newey-West HAC SE (lag=30d) = 1.721981e-02
- contemporaneous (Δlog_tx vs Δlog_close) Rank-IC = **0.0262** (mechanical co-move 검정 — 절대값>0.3 시 utility signal 의심)
- partial Rank-IC (Δlog_tx | Δlog_blk residual → fwd_30d) = -0.0042 (n=3178)

## Cell breakdown
| epoch | halving | n | N_eff | Rank-IC |
|---|---|---|---|---|
| 2017_2020 | post_6_18m | 143 | 3 | 0.0223 |
| 2017_2020 | post_18_24m | 183 | 6 | -0.0099 |
| 2017_2020 | post_24_36m | 365 | 5 | -0.0101 |
| 2017_2020 | pre_next_halving | 235 | 6 | -0.0428 |
| 2020_2024_pre_etf | post_0_6m | 183 | 3 | -0.0257 |
| 2020_2024_pre_etf | post_6_18m | 365 | 6 | 0.0096 |
| 2020_2024_pre_etf | post_18_24m | 183 | 6 | -0.0002 |
| 2020_2024_pre_etf | post_24_36m | 365 | 6 | 0.0191 |
| 2020_2024_pre_etf | pre_next_halving | 315 | 11 | 0.0144 |
| post_2024_etf | post_0_6m | 183 | 6 | -0.0107 |
| post_2024_etf | post_6_18m | 365 | 8 | 0.0118 |
| post_2024_etf | post_18_24m | 183 | 4 | 0.0470 |
| post_2024_etf | pre_next_halving | 99 | 2 | -0.0617 |

## 12축 박제
- **A 학술**: Athey 2016, Catalini&Gans 2020 (utility), Yermack 2015 (mechanical shuffle 반증)
- **B SE 보정**: Newey-West HAC lag=30 + Block bootstrap block=60d B=2000. FAIL (|Rank-IC|=0.0022 ≤ 0.03)
- **D PIT**: TxCnt T+1 release (community 익일 02:00 UTC)
- **F 반증조건**: (i) β CI 0 포함? YES (REJECT 신호) (ii) Rank-IC<0.03? YES (REJECT) (iii) mechanical co-move (|contemp|>0.3)? NO (iv) partial-corr 후 잔존? NO
- **G effective N**: full N_eff=47. cell N<30 ★INSUFFICIENT.
- **I 생존편향**: BTC only.
- **K 시도횟수**: K=24 cell + 2 axis (full / partial-blk-residual) = 50. Bonferroni α/50=0.00100 임계.

## verdict
**★REJECTED (Rank-IC<0.03 hard B threshold 미달)**

## hedge 어휘
- count proxy = 방향성 약 prior (value-weighted 후속 필요)
- mechanical co-move (0.0262): 약하므로 utility 잔존 가능성

## 후속 의문
- (i) TxTfrValAdjUSD (value-weighted) paid tier — count vs value-weighted 비교
- (ii) lag k=1d / 7d / 30d / 90d 4 horizon
- (iii) regime conditional: bull (MVRV>1.5) vs bear
- (iv) partial-corr 분리 = tx_resid → fwd_ret 의 robust 회귀계수 + CI