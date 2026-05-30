# H2 Funding cascade -- 실데이터 검증

as_of: 2026-05-30T14:39:35.520986+00:00
funding: Binance BTCUSDT 8h, n=7363, 2019-09-10 08:00:00 ~ 2026-05-30 08:00:00.001000
klines: Binance BTCUSDT daily, n=3209, 2017-08-17 ~ 2026-05-30

## 1. Funding rate 8h 분포
```
count    7363.000000
mean        0.000108
std         0.000210
min        -0.003000
1%         -0.000189
5%         -0.000057
50%         0.000100
95%         0.000471
99%         0.001061
max         0.003000
```
- |funding| 95th percentile = 0.000488
- |funding| 99th percentile = 0.001065
- direction.md 임계 0.05%/8h = 0.0005 비교: 4.6992% 의 시점이 0.0005 초과

## 2. Event study -- |funding| > 95th percentile 진입 시점의 fwd 24h/72h return
- daily absmax p95 = 0.000645, p99 = 0.001354
- p95: n=123, fwd_1d mean=+0.2471%, fwd_3d mean=+0.8047%, baseline_1d=+0.0724%
  - extreme LONG funding (mean>0): n=118, fwd_1d=+0.1864% (cascade 가설 = neg 기대)
    t-stat=+0.46, p(<0)=0.6766
  - extreme SHORT funding (mean<0): n=5, fwd_1d=+1.6794% (squeeze 가설 = pos 기대)
    t-stat=+0.54, p(>0)=0.3094
- p99: n=25, fwd_1d mean=+1.1616%, fwd_3d mean=+1.9225%, baseline_1d=+0.0700%
  - extreme LONG funding (mean>0): n=24, fwd_1d=+1.5253% (cascade 가설 = neg 기대)
    t-stat=+1.42, p(<0)=0.9160
- abs>0.0005: n=179, fwd_1d mean=-0.0166%, fwd_3d mean=+0.6870%, baseline_1d=+0.0888%
  - extreme LONG funding (mean>0): n=169, fwd_1d=-0.0520% (cascade 가설 = neg 기대)
    t-stat=-0.16, p(<0)=0.4378
  - extreme SHORT funding (mean<0): n=10, fwd_1d=+0.5807% (squeeze 가설 = pos 기대)
    t-stat=+0.33, p(>0)=0.3754

## 3. Cascade binomial test -- extreme long funding 진입 후 fwd_3d < 0 확률
- absmax_p95+long: n=118, hits(fwd_3d<0)=57, rate=0.4831, binomial p (one-sided > 0.5) = 0.6773
- absmax_p99+long: n=24, hits(fwd_3d<0)=8, rate=0.3333, binomial p (one-sided > 0.5) = 0.9680

## 4. Spearman Rank-IC funding -> forward return (전체 기간)
- fwd_1d: Rank-IC = -0.0232, n=2454
  block-bootstrap 95% CI = (-0.0587, +0.0132)
- fwd_3d: Rank-IC = -0.0407, n=2452
  block-bootstrap 95% CI = (-0.1089, +0.0207)

## 5. Effective N (autocorr-adjusted)
- funding_mean: raw N=2455, effective N=234.1
- fwd_1d log_ret: raw N=2454, effective N=2830.4

## 6. 가설 판정
- 2장 event study cascade (extreme long -> neg 3d) p<0.05 -> 가설 1차 검증
- 3장 binomial hit rate < 0.5 + p > 0.05 -> 가설 기각
- 4장 marginal Rank-IC 부호 = funding -> fwd_ret 방향

## 7. 미해결 의문
- funding 8h -> daily aggregate 시 정보 손실 (intra-day cascade 미포착)
- p95/p99 임계 자체가 sample-fit; OOS 분리 검증 필요
- OI history 30d 만 가용 (Binance public) -> conditioning_set [RSI, OI] 부분 검증 한계
- 2022 LUNA / FTX 같은 비대칭 이벤트 outlier 영향 (block bootstrap 으로 부분 완화)