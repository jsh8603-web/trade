---
tags: [type/validation, study/crypto, cycle/2, hypothesis/h7]
date: 2026-05-31
hypothesis: H7 — AdrActCnt → fwd_30d_ret (Pagnotta&Buraschi 2018 sub-Metcalfe)
audit_axes: [A, B, D, F, G, I, K]
---

# validation-h7 — AdrActCnt network value → fwd_30d_ret (BTC)

## Data Coverage
- 시리즈: CoinMetrics community `AdrActCnt` daily (anonymous tier 확인)
- 기간: 2017-08-17 ~ 2026-05-30 (full v2)
- Binance klines inner join 후: n_total (Δlog + fwd_30d 모두 valid) = **3178**
- 결측·갭: dropna 후 3178 (Binance 2017-08-17 시작 → 2017 pre-Binance 시기 제외)
- N_eff (autocorr 보정): full sample = 47

## 변수 정의 + measurement axis (5축)
- (a) 시제: Δlog(addr_t) contemporaneous → fwd_30d_ret (close[t+30]/close[t])
- (b) frequency: daily
- (c) transform: log + first difference
- (d) conditioning: macro epoch × halving phase
- (e) regime: full sample / 4 epoch (pre_2017 / 2017_2020 / 2020_2024_pre_etf / post_2024_etf) × 6 halving

## H7 검증 결과 (full sample)
- Rank-IC (Spearman) = **0.0085** (n=3178)
- β OLS 1변수 = 1.510350e-02
- Block bootstrap CI95% (block=60d, B=2000) = [-2.753517e-03, 3.474361e-02]
- Newey-West HAC SE (lag=30d for fwd_30d) = 1.721981e-02
- post-2024 ETF sub-sample Rank-IC = 0.0085 (n=841, N_eff=15)

## Cell breakdown (epoch × halving, n≥24)
| epoch | halving phase | n | N_eff | Rank-IC |
|---|---|---|---|---|
| 2017_2020 | post_6_18m | 143 | 3 | 0.0186 |
| 2017_2020 | post_18_24m | 183 | 6 | 0.0042 |
| 2017_2020 | post_24_36m | 365 | 5 | 0.0008 |
| 2017_2020 | pre_next_halving | 235 | 6 | -0.0476 |
| 2020_2024_pre_etf | post_0_6m | 183 | 3 | 0.0147 |
| 2020_2024_pre_etf | post_6_18m | 365 | 6 | 0.0293 |
| 2020_2024_pre_etf | post_18_24m | 183 | 6 | 0.0085 |
| 2020_2024_pre_etf | post_24_36m | 365 | 6 | 0.0115 |
| 2020_2024_pre_etf | pre_next_halving | 315 | 11 | -0.0149 |
| post_2024_etf | post_0_6m | 183 | 6 | 0.0412 |
| post_2024_etf | post_6_18m | 365 | 8 | 0.0150 |
| post_2024_etf | post_18_24m | 183 | 4 | -0.0611 |
| post_2024_etf | pre_next_halving | 99 | 2 | 0.0592 |

## 12축 박제 자가 점검
- **A 학술**: Pagnotta&Buraschi 2018 (SSRN) sub-Metcalfe α∈[0.5,1.2] 균형해 + Liu&Tsyvinski 2021 RFS (factor null 반증)
- **B SE 보정**: Newey-West HAC lag=30d (forward window length 일치) + Block bootstrap (block=60d, B=2000). full Rank-IC 0.0085 ≤ 0.03 (B threshold FAIL)
- **D PIT**: AdrActCnt = T+1 release (CoinMetrics community 익일 02:00 UTC), fwd_ret close-to-close (lookahead 회피)
- **E 자문 환각**: Pagnotta α 정량 미박제 (학술 prior, 본 표본 재현 결과 우선). Liu&Tsyvinski factor null reference 보존.
- **F 반증조건**: (i) β CI 0 포함? CI=[-2.7535e-03, 3.4744e-02] 포함 (REJECT 신호) (ii) Rank-IC<0.03? YES (REJECT) (iii) post-2024 부호반전? sign post=1.0 vs full=1.0, 일관
- **G effective N tier**: full N_eff=47, post-2024 N_eff=15 — n<30 cell ★INSUFFICIENT 라벨
- **I 생존편향**: BTC only 명시 (멀티코인 확장 시 ETH·상폐 ICO token 별도 처리)
- **K 시도횟수**: K=24 (4 epoch × 6 halving cell, n≥24 cell only). Bonferroni α/24=0.00208 임계. 보고 시 raw p + 보정 p 병기 (β t-stat·p 본 라운드 미수행, cycle 2 후속).

## verdict
**★REJECTED (Rank-IC<0.03 hard B threshold 미달)**

## hedge 어휘 (small-N rigor)
- 본 결과는 *방향성 약 prior* 또는 *비유의* 라벨. 점추정 magnitude (Pagnotta α 등) 박제 금지.
- ★점추정 covariance prior 박제 금지 — 후속 라운드 SE 보정 + walk-forward OOS holdout 후 재평가.

## 후속 의문 (cycle 3 자료)
- (i) Pagnotta α 추정 (log-log 회귀 1년 rolling window) — α∈[0.5, 1.2] 학술 prior 안에 들어오는지
- (ii) cluster (거래소 hot-wallet) 영향 = unique active address ≠ unique user 의 측정 편의
- (iii) post-2024 custodian cluster 효과: ETF 도입 후 active addr 가 감소했는데 가격 ↑ — sub-Metcalfe 약화
- (iv) lag k 변동성 (1d / 7d / 30d / 90d) 4종 K=4 비교 시 Bonferroni