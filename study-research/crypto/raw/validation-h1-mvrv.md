# H1 MVRV mean-revert — 실데이터 검증

as_of: 2026-06-02T12:14:03.999529+00:00
data: CoinMetrics CapMVRVCur (2010-07-18 ~ 2026-05-29, n=5795)
price: CoinMetrics PriceUSD/ReferenceRateUSD
FGI merge: alternative.me (2018-02-01 ~ 2026-05-30)

## 1. MVRV 시계열 기본 통계
```
count    5795.000000
mean        1.975237
std         2.466299
min         0.386829
5%          0.824280
25%         1.290876
50%         1.733384
75%         2.243852
90%         3.017332
95%         3.677041
99%         5.773829
max       146.038332
```
MVRV > 2.4 일수: 1154 / 5795 = 19.914%
MVRV > 3.0 일수: 590 / 5795 = 10.181%
MVRV < 1.0 일수: 775 / 5795 = 13.374%

## 2. instrument_source.run_mvrv_closed_loop 실데이터 재검증 (mvrv_hi=2.4, horizon=7d, 'down' 예측)
- n_pred (MVRV>2.4 진입 일수, 7d 완료) = 1154
- hits (fwd_7d < 0) = 456
- hit_rate = 0.3951
- binomial p (one-sided > 0.5) = 1.0000
- 판정 (alpha=0.05): FAIL TO REJECT

## 3. horizon 별 MVRV 진입 조건부 forward return
- fwd_7d | MVRV>2.0: n=1993, mean=+3.8753%, BB95%CI=(+1.7456%, +6.7376%), Welch t=+8.18 p=0.0000, baseline_mean=+0.5278%
- fwd_7d | MVRV>2.4: n=1154, mean=+5.9186%, BB95%CI=(+2.8317%, +9.9627%), Welch t=+8.65 p=0.0000, baseline_mean=+0.6250%
- fwd_7d | MVRV>3.0: n=590, mean=+8.5623%, BB95%CI=(+4.3106%, +15.2589%), Welch t=+7.32 p=0.0000, baseline_mean=+0.8993%
- fwd_30d | MVRV>2.0: n=1993, mean=+16.9643%, BB95%CI=(+8.3871%, +26.7295%), Welch t=+14.59 p=0.0000, baseline_mean=+2.1811%
- fwd_30d | MVRV>2.4: n=1154, mean=+22.8550%, BB95%CI=(+10.9629%, +37.1895%), Welch t=+12.94 p=0.0000, baseline_mean=+3.3967%
- fwd_30d | MVRV>3.0: n=590, mean=+29.5725%, BB95%CI=(+17.4482%, +50.1327%), Welch t=+11.32 p=0.0000, baseline_mean=+4.7515%
- fwd_90d | MVRV>2.0: n=1993, mean=+41.2294%, BB95%CI=(+22.2508%, +60.3245%), Welch t=+14.95 p=0.0000, baseline_mean=+11.6322%
- fwd_90d | MVRV>2.4: n=1154, mean=+50.0544%, BB95%CI=(+24.2748%, +78.9013%), Welch t=+12.83 p=0.0000, baseline_mean=+14.8508%
- fwd_90d | MVRV>3.0: n=590, mean=+64.2632%, BB95%CI=(+30.5937%, +101.5607%), Welch t=+12.42 p=0.0000, baseline_mean=+17.0936%

## 4. Partial correlation — MVRV ⊥ fwd_30d | conditioning
- n_complete = 3006
- marginal Spearman(MVRV, fwd_30d) = -0.0713, n=3006
- partial Spearman(MVRV, fwd_30d | FGI, halving_phase) = -0.0847, p=0.0000
- partial 95% block-bootstrap CI = (-0.2349, +0.0734)
- 결론: CI 가 0 포함

## 5. e-CUSUM Rank-IC 단측 붕괴 검정
- score = -MVRV_z (mean-revert prediction sign 반영, high MVRV = neg fwd_ret 예측)
- rolling window 90d, baseline_ic = 0.0 (score⊥fwd null), sd = ★empirical rolling-IC std (heuristic 0.15 = spurious 발산 원인, audit 격하 → 실측 sd 대체)
- rolling IC: n_windows=187, mean=+0.3467, std=+0.3453
- empirical sd = 0.3453 (heuristic 0.15 대체)
- max e-process R = 3801288240233.8188, threshold (1/0.05)=20.0, rejected=True
  ★주의: rolling-IC mean=+0.347 양(score⊥fwd null 아래 *붕괴* 아님) + window overlap 자기상관 → e-CUSUM 단측붕괴 = small-n spurious, 의사결정 미사용(라벨 only).

## 6. Regime-conditional MVRV → fwd_30d Rank-IC
```
          fgi       phase   n        ic     eff_n    p_eff
 extreme_fear   post_0_6m   4       NaN       NaN      NaN
 extreme_fear  post_6_18m  69 -0.653014 14.555514 0.009535
 extreme_fear post_18_24m 240 -0.487070 12.767881 0.095035
 extreme_fear post_24_36m 233 -0.531693  4.474817 0.409843
         fear   post_0_6m 129 -0.332553  6.491991 0.492084
         fear  post_6_18m 100 -0.315716 10.993188 0.344454
         fear post_18_24m 208 -0.394658 10.966214 0.230609
         fear post_24_36m 246 -0.386739  6.580687 0.414103
      neutral   post_0_6m  83  0.038328  3.448889 0.968715
      neutral  post_6_18m  98 -0.294264  9.384772 0.429000
      neutral post_18_24m  46 -0.145853  9.820677 0.691194
      neutral post_24_36m  95 -0.512738  6.289137 0.279549
        greed   post_0_6m 116 -0.341752  7.216911 0.442545
        greed  post_6_18m 278 -0.483754  5.460170 0.370300
        greed post_18_24m  27       NaN       NaN      NaN
        greed post_24_36m 146 -0.150172  5.996786 0.776533
extreme_greed   post_0_6m  34 -0.142246  3.132768 0.901077
extreme_greed  post_6_18m 184 -0.065154  5.733342 0.906106
extreme_greed post_18_24m   1       NaN       NaN      NaN
extreme_greed post_24_36m  20       NaN       NaN      NaN
```
- 전체 cell 수: 20
- N(raw)≥30 통과 cell: 16
- N<24 (small-N gate 미달) cell: 3
- ★effective_n < 30 cell: 16 / 16 (자기상관 보정 후 *전 cell* eff_n<30 = n≥30 claim 무효)
- ★Bonferroni α/16 = 0.00313 임계, eff_n 기반 per-cell p 생존 cell = 0

## 7. 가설 판정
- 2장 closed-loop binomial p < 0.05? → MVRV>2.4 mean-revert 가설 1차 검증
- 4장 partial CI 0 포함? → MVRV-fwd_ret 직접엣지 vs 매개 분해
- 5장 e-CUSUM rejected? → score IC 단측 붕괴 여부
- 6장 cell N < 24 = small-N 5게이트, structural prior 라벨

## 8. 미해결 의문
- MVRV cycle peak/trough 독립 N = 3~4 → block bootstrap CI 넓음
- post-2024 ETF 시대 realized cap 의미 변화 (custodian 이동)
- mvrv_hi=2.4 임계 자체가 사후 fit 가능성 — 2017-2021 in-sample, 2022-2025 OOS 분리 검증 권고