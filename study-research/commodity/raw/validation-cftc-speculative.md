---
tags: [type/validation, domain/commodity, indicator/cftc-speculative, phase/m3-merit-collector]
date: 2026-05-31
producer: main (btn-Codlearn) 직접 — collector 구현 + study
trigger: 사용자 지시 2026-05-31 "merit 있으면 collector 없어도 main이 구현 → study → 12축 audit → 반영"
collector_built: raw/m3-cftc-speculative.py (CFTC Socrata 6dca-aqww, 무료·키불요)
result_json: raw/m3-cftc-speculative-results.json
---

# validation — CFTC speculative positioning(copper) → forward 수익률

> **merit 배경**: `mm_net_long_oi_z`(H8) 는 yaml 에 등록됐으나 "CFTC collector 미구축"으로 실검증 이연.
> 사용자 지시로 collector 직접 구현 → 실데이터 검증. ★China impulse(전부 비유의)와 달리 **유의 신호 발견**.

## ① collector (★main 구현)
- CFTC Socrata public API `6dca-aqww` (Legacy COT Futures-only, 무료·키불요).
- copper COMEX(cftc_market_code=CMX) noncommercial(=speculative proxy) long/short/OI.
- **n=1736 주간 (1986-01 ~ 2025-07)** — 실데이터.
- ★proxy 라벨 정직: 정통 H8 = Disaggregated 'Money Manager'. legacy noncommercial = 더 긴 history speculative proxy (1986~ vs MM 2006~).

## ② 측정 (net_spec = (long−short)/OI → 36m rolling z, copper forward 수익률)
| forward | Spearman ρ | raw p | **Newey-West HAC p** | block-boot ρ 95%CI | n |
|---|---|---|---|---|---|
| **1m** | **+0.223** | <0.0001 | **0.0025 ✅** | **[+0.106, +0.328] (0 배제)** | 405 |
| 2m | +0.156 | 0.0019 | 0.099 | [+0.012, +0.286] | 404 |
| 3m | +0.113 | 0.025 | 0.381 | [−0.043, +0.253] | 403 |
| 6m | +0.096 | 0.057 | 0.784 | [−0.084, +0.260] | 400 |
| 12m | +0.065 | 0.201 | 0.724 | [−0.163, +0.258] | 394 |

**다중비교 5 test**: Bonferroni α=0.01 → **1m·2m 생존** / Newey-West HAC p<0.05 → **1m 생존(t=3.03)**.

## ③ verdict (empirical-claim rule)
★**CONFIRMED (1m forward predictive)** — 단 독립 alpha 는 PENDING:
- 1m forward: n=405(≥100) + HAC p=0.0025(<0.01) + Bonferroni 생존 + bootstrap CI 0 배제 + 1→12m monotonic decay(positioning-momentum 정합). **자기상관·다중비교 보정 후 생존** = 실 신호.
- ⚠️ **momentum 교란 미해소**: speculative net long 은 최근 가격추세를 추종(positioning follows momentum) → 1m forward 예측력이 **독립 alpha 인지 momentum 재포장인지 불명**. edge_type=common_cause(momentum 매개) caveat 유효.
- ⚠️ **PIT 타이밍**: CFTC = 화요일 포지션 금요일 공시(T+3). 월말 resample 시 마지막 보고는 월말 전 공시되나, daily 정밀화 시 T+3 lag 엄수 필요(월별은 대부분 흡수).

## ④ yaml 반영 방침 (★5금지 준수)
- ⛔ 점추정 ρ=0.22 covariance prior 박제 X.
- → `mm_net_long_oi_z` 관계를 **forward-predictive(1m) 유의**로 갱신하되 **validated_alpha = PENDING(momentum orthogonalization 전)**.
- **승격 falsifier**: momentum_12_1 통제 후(partial-corr 또는 FF-style residual) 1m forward IC 가 유의 유지 → validated_alpha=true 승격. momentum 흡수 시 → structural(momentum proxy) 격하.
- base_weight 즉시 상향 금지 — orthogonalization 후 IC 추적값으로.

## ⑤ 의의
사용자 "merit 있으면 collector 직접 구현" 지시 실증: collector(무료 CFTC) 구현으로 **이연돼 있던 merit 지표가 실 신호로 검증**됨. China impulse(비유의 격하)와 대비 = "검증해서 있으면 살리고, 없으면 버린다"의 양쪽 사례 확보.
