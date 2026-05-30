# 우선 2 — Internal glasso effective-N gate 영구폐쇄 위험 검증

as_of: 2026-05-30T14:40:47.572484+00:00
indicator 후보 (가용): ['mvrv', 'fgi', 'funding_mean', 'supply_g7d', 'log_ret_1d']
전체 일수: 3209, complete-case 일수: 2453 (76.441%)
complete-case 기간: 2019-09-10 00:00:00 ~ 2026-05-29 00:00:00

## 1. Indicator 별 가용 시작 일자 (joint complete-case window 제약)
- mvrv: 2017-08-17 ~ 2026-05-29, n=3208
- fgi: 2018-02-01 ~ 2026-05-30, n=3037
- funding_mean: 2019-09-10 ~ 2026-05-30, n=2455
- supply_g7d: 2017-12-06 ~ 2026-05-30, n=3098
- log_ret_1d: 2017-08-18 ~ 2026-05-30, n=3208
- ★joint complete-case 시작 = 2019-09-10 00:00:00

## 2. Regime cell 분포 (FGI 5 × vol 3 = 15 cell)
```
vol_regime     low_vol  mid_vol  high_vol
fgi_regime                               
extreme_fear       101      137       239
extreme_greed       39      119       102
fear               232      277       133
greed              341      205        90
neutral            252      120        66
```

## 3. Cell 별 effective N (autocorr-adjusted, log_ret_1d 기준)
```
          fgi      vol  n_raw  n_eff
 extreme_fear high_vol    239  404.8
 extreme_fear  low_vol    101  119.8
 extreme_fear  mid_vol    137  126.3
extreme_greed high_vol    102   74.9
extreme_greed  low_vol     39   36.6
extreme_greed  mid_vol    119  118.3
         fear high_vol    133  111.9
         fear  low_vol    232  188.1
         fear  mid_vol    277  238.1
        greed high_vol     90   65.6
        greed  low_vol    341  327.9
        greed  mid_vol    205  252.8
      neutral high_vol     66   61.4
      neutral  low_vol    252  236.8
      neutral  mid_vol    120  131.4
```

## 4. Threshold 별 admit rate (gate 영구폐쇄 위험 평가)
- effective N >= 24: 15/15 cells (100.0%) - OK
- effective N >= 50: 14/15 cells (93.3%) - OK
- effective N >= 100: 11/15 cells (73.3%) - OK
- effective N >= 200: 5/15 cells (33.3%) - WARN
- effective N >= 500: 0/15 cells (0.0%) - ★HIGH 영구폐쇄 위험

## 5. 가설 판정 (direction.md §5 의문 #4)
- threshold 50  admit rate = 93.3%
- threshold 100 admit rate = 73.3%
- threshold 200 admit rate = 33.3%
- ★결론: gate 통과 cell 충분 -> direction.md D4 hybrid 권고 유지 가능

## 6. 미해결 의문
- effective N = AR(1) 가정 단순 보정. 실제 autocorr 구조가 복잡 (MA/GARCH/regime-switching)
- vol regime tertile 은 in-sample 분류 (post-hoc) -> 실시간 적용 시 lookahead 위험 주의
- joint complete-case 시작 = funding (2020-09) 의 제약. CoinMetrics MVRV 가 합류하면 더 짧아짐
- bootstrap edge stability 시뮬은 미수행 (긴 연산) — gate 통과 cell 에 한해 별도 검증 권고