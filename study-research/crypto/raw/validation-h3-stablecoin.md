# H3 Stablecoin net creation lead-lag -- 실데이터 검증

as_of: 2026-06-02T12:15:18.091145+00:00
stablecoin: DefiLlama total supply, n=3105, 2017-11-29 ~ 2026-05-30
BTC klines: Binance daily, merged n=3105

## 1. ADF stationarity 선행
- log_supply (level): ADF stat=-4.862, p=0.0000, n=3105 -> STATIONARY
- supply_log_growth_1d: ADF stat=-11.402, p=0.0000, n=3104 -> STATIONARY
- supply_log_growth_7d: ADF stat=-8.120, p=0.0000, n=3098 -> STATIONARY
- log_close (level): ADF stat=-0.865, p=0.7991, n=3105 -> non-stationary
- log_ret_1d (BTC): ADF stat=-38.848, p=0.0000, n=3104 -> STATIONARY

## 2. Cross-correlation function (CCF) -- supply_growth vs BTC log_ret
- supply 가 BTC 선행 (positive lag X->Y):
  - lag 1d: corr=-0.0383
  - lag 3d: corr=-0.0190
  - lag 7d: corr=+0.0114
  - lag 14d: corr=-0.0139
  - lag 30d: corr=+0.0254
- BTC 가 supply 선행 (X<-Y, 역인과 정황):
  - lag 1d: corr=-0.0492
  - lag 3d: corr=-0.0295
  - lag 7d: corr=+0.0019
  - lag 14d: corr=-0.0115
  - lag 30d: corr=+0.0224
- supply->BTC peak abs lag = 19d, corr=-0.0915
- BTC->supply peak abs lag = 25d, corr=-0.0616
- 역인과 위험: LOW (supply->BTC peak 우세)

## 3. Bidirectional Granger causality (growth series, maxlag=14)
- supply growth -> BTC ret (F-test p-values by lag):
  - lag 1d: p=0.0202
  - lag 7d: p=0.0005
  - lag 14d: p=0.0022
- BTC ret -> supply growth (F-test p-values by lag, 역인과):
  - lag 1d: p=0.9763
  - lag 7d: p=0.0138
  - lag 14d: p=0.0000

## 4. Rank-IC supply_log_growth_7d -> fwd_{7,30,90}d
- log_ret_7d_fwd: Rank-IC = +0.0524, n=3091
  block-bootstrap 95% CI = (-0.0303, +0.1274)
- log_ret_30d_fwd: Rank-IC = +0.0752, n=3068
  block-bootstrap 95% CI = (-0.0651, +0.1922)
- log_ret_90d_fwd: Rank-IC = +0.0116, n=3008
  block-bootstrap 95% CI = (-0.1441, +0.1656)

## 5. 가설 판정
- 1장: level 비정상 + growth 정상 확인 (필수 stationarity)
- 2장 CCF peak: supply->BTC peak 이 BTC->supply peak 보다 절대값 큰가? 작으면 역인과 정황
- 3장 Granger: supply->BTC F-test 유의 + BTC->supply 미유의 = lead 확인 / 둘 다 유의 = reflexive
- 4장 Rank-IC: 7/30d 양 + CI 0 미포함 = direction.md H3 가설 1차 검증

## 6. 미해결 의문
- DefiLlama total supply 가 DeFi 담보·OTC·bridge 포함 -> 진짜 'dry powder' 아님
- 거래소向 stablecoin inflow 가 더 깨끗하지만 무료 단위 불가
- 2020 DeFi summer / 2022 UST 붕괴 같은 regime break -> 단일 ADF/Granger 안정성 의심
- 우리 검증 = 양방향 Granger, 일변량 level 차분만 (multivariate VECM 추가 권고)