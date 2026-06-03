# H4 ETF net flow probation — 실데이터 검증

as_of: 2026-06-02T12:15:20.129950+00:00
data: Farside Investors daily ETF flow (musd)
  n=613, 2024-01-11 ~ 2026-05-29
  total cumulative inflow = +55,714.1 M USD

## 1. ETF net flow 분포
```
count     613.000000
mean       90.887602
std       342.446036
min     -1113.700000
5%       -416.380000
25%      -114.800000
50%        48.800000
75%       260.200000
95%       675.880000
max      1373.800000
```
- 양 inflow 일수: 362 / 613
- 음 outflow 일수: 235

## 2. ETF flow vs BTC forward return
- merged n=613 (Binance klines ∩ Farside)
- post-2024-01 N effective = ~613d (probation)
- daily flow -> log_ret_7d_fwd: Rank-IC = +0.0172, n=606
- 5d cum flow -> log_ret_7d_fwd: Rank-IC = +0.0811, n=602
  block-bootstrap 95% CI = (-0.1407, +0.2188)
- daily flow -> log_ret_30d_fwd: Rank-IC = +0.0478, n=583
- 5d cum flow -> log_ret_30d_fwd: Rank-IC = +0.0572, n=579
  block-bootstrap 95% CI = (-0.1613, +0.2328)

## 3. Hit rate — flow_5d_cum > 0 진입 후 fwd_30d > 0
- n=374, hits=212, rate=0.5668, binomial p(>0.5)=0.0056

## 4. Effective N (autocorr-adjusted)
- ETF flow effective N = 196.8 (raw N = 613)
- 1.5~2yr sample 짧음 명시 -> observe-only prior 0.05 유지

## 5. 가설 판정
- Rank-IC 양 + CI 0 미포함 + binomial p<0.05 = 1차 검증 (단 N 작음 강조)
- prior = observe-only 0.05 (probation) 유지 -- 데이터 누적 시 confidence_hooks 가 OOS reject_signal 발화

## 6. 미해결 의문
- post-2024 1.5~2yr 만 -> effective N 적음, CI 매우 넓음
- Farside 단일 free source 의존 (스키마 변동 위험)
- 역인과 위험: ETF flow 가 price-chasing (reflexive) 일 수 있음 -> 후속 lead-lag 검증 권고
- OTC / non-US ETF / futures basis 누락 -> 'institutional demand' 전체 아님