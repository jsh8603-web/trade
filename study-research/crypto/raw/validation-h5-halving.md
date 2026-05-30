# H5 Halving phase regime — 실데이터 검증

as_of: 2026-05-30T14:40:44.552962+00:00
★N=4 사실상 검정 불가 명시 (PlanB S2F OOS 붕괴 교보재). standalone IC 산출 금지.
본 검증 = phase 별 conditioning 변수로서 H1 (MVRV) IC 안정성 확인만.

## 0. Halving events 가용 범위
- 2012-11-28
- 2016-07-09
- 2020-05-11
- 2024-04-19

## 1. Phase 별 N (klines 일수)
```
phase
post_0_6m           366
post_18_24m         549
post_24_36m         771
post_6_18m          874
pre_next_halving    649
```

## 2. Phase 별 BTC fwd_30d 분포 (★across-phase 통계검정 X — N=4 power 0)
```
                  count    mean     std     min     25%     50%     75%     max
phase                                                                          
post_0_6m         366.0  0.0659  0.1418 -0.2277 -0.0356  0.0507  0.1514  0.4286
post_18_24m       549.0 -0.0751  0.1743 -0.6735 -0.2059 -0.0675  0.0422  0.3806
post_24_36m       741.0  0.0106  0.2042 -0.6707 -0.0909  0.0105  0.1211  0.5029
post_6_18m        874.0  0.0849  0.2444 -0.9000 -0.0561  0.0409  0.2252  1.0345
pre_next_halving  649.0  0.0344  0.1825 -0.7560 -0.0671  0.0319  0.1586  0.4617
```

- ★구조적 prior (저신뢰) 라벨: 4 사이클 데이터로 phase 효과 통계 검정 X
- post_6_18m / post_18_24m 단순 평균이 양 / 음 부호인지만 보고

## 3. Phase 별 MVRV -> fwd_30d Rank-IC (conditioning 안정성)
- post_0_6m: Rank-IC = -0.2847, raw N=366, effective N=5.3
- post_18_24m: Rank-IC = -0.6113, raw N=549, effective N=15.7
- post_24_36m: Rank-IC = -0.1945, raw N=741, effective N=7.2
- post_6_18m: Rank-IC = -0.0311, raw N=874, effective N=9.5
- pre_next_halving: Rank-IC = -0.3086, raw N=649, effective N=5.1

- ★해석: phase 별 IC 부호 일관성 = MVRV 가 phase 전반에 걸쳐 안정한 mean-revert 신호 / 부호 반전 / 절대값 차이 = phase modulator 필요 신호

## 4. Effective N gate (G축 tier)
- post_0_6m: N raw=366, effective=5.3 -> tier: small-N 차단
- post_18_24m: N raw=549, effective=15.7 -> tier: small-N 차단
- post_24_36m: N raw=770, effective=7.2 -> tier: small-N 차단
- post_6_18m: N raw=874, effective=9.5 -> tier: small-N 차단
- pre_next_halving: N raw=649, effective=5.1 -> tier: small-N 차단

## 5. 결론
- ★H5 standalone IC 산출 = 수행 안 함 (사용자 명시 N=4 power 0)
- phase 는 regime label only (belief b(t) regime 입력)
- conditioning 효과만 H1 (MVRV) 의 phase 별 IC 로 간접 평가
- prior_strength = 0.1 (channel 최하, direction.md D1 합의)

## 6. 미해결 의문
- 각 halving 이 다른 macro epoch 와 confound (2012 태동 / 2016 ICO / 2020 COVID / 2024 ETF)
- phase modulator 가 진짜 supply 효과인지 epoch artifact 인지 식별 불가
- 채굴자 매도 압력 (hashrate / miner outflow) 연속 보조 지표 추가 권고 (별도 collector 필요)