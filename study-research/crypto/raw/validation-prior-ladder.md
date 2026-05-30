# 우선 1 — Prior ladder OOS backtest

as_of: 2026-05-30T14:40:45.964178+00:00
direction.md D1: micro 0.5-0.7 / on-chain 0.3-0.5 / macro 0.2-0.4 / halving 0.1-0.2
측정: 각 채널 대표 가설의 rolling Rank-IC mean / std / sharpe / breakdown_freq
rolling window = 180d, step = 30d (~6달마다 갱신, 3년 데이터 = 약 18 windows)

## 1. Micro channel — H2 funding -> fwd_7d
  - n_windows=75, mean IC=+0.1312, std=0.1353, sharpe=+0.970, breakdown_freq=0.160

## 2. On-chain channel — H1 MVRV -> fwd_30d
  - n_windows=47, mean IC=+0.2714, std=0.2129, sharpe=+1.275, breakdown_freq=0.128

## 3. Macro channel — H3 stablecoin growth -> fwd_30d
  - n_windows=45, mean IC=-0.0853, std=0.1979, sharpe=-0.431, breakdown_freq=0.333

## 4. Halving channel — ★standalone IC 산출 금지 (N=4 power 0)
  - halving prior 0.1 = label-only regime conditioning
  - phase 별 fwd_30d 평균 부호만 보고 (구조적 prior 저신뢰 라벨)
    - post_0_6m: mean fwd_30d = +0.0659
    - post_18_24m: mean fwd_30d = -0.0751
    - post_24_36m: mean fwd_30d = +0.0106
    - post_6_18m: mean fwd_30d = +0.0849
    - pre_next_halving: mean fwd_30d = +0.0344

## 5. Ladder 정합 판정
```
             channel  prior_proposed    mean    std  ic_sharpe  breakdown_freq  n_windows  effective_n_raw
       micro_funding             0.6  0.1312 0.1353     0.9701          0.1600         75         233.4428
        onchain_mvrv             0.4  0.2714 0.2129     1.2748          0.1277         47          15.9749
    macro_stablecoin             0.3 -0.0853 0.1979    -0.4312          0.3333         45         225.4311
halving_regime_label             0.1     NaN    NaN        NaN             NaN          0           4.0000
```
- micro_funding IC-sharpe / max(on-chain, macro) IC-sharpe = 0.76
- prior 비율 (0.6 / 0.4) = 1.5 — 측정 ratio 와 prior ratio 비교
- ★판정: ratio < 1.0 (ladder 역방향)

## 6. 미해결 의문 (claude r3 인용)
- prior 0.6 / 0.4 / 0.3 / 0.1 ladder 의 정확한 수치는 educated guess
- 본 검증 자체가 rolling window 의 길이·step 선택에 민감
- channel 대표 가설 = 단일 sig 가설만 (channel 의 다양한 가설 평균 X)
- prior_strength -> OOS edge 안정성 매핑은 backtest 누적 후 calibrate