# validation-v3-cross-sectional.md — telecom(통신) §M v3

> frame v3 §M.1~M.7. raw 재현: `raw-v3/{collect, measure, collect_dart, measure_valuation, measure_cross, exposure_card}.py`.
> ★universe 협소 경계 케이스. consumer(asset_stable value) 재현 + small-n 한계.

## §0. ★universe 협소 (양식 경계 케이스)

| 정의 | 종목 | cross-sectional |
|---|---|---|
| 통신서비스(전기통신업, asset_stable) | **3종** (SKT/KT/LGU+) | ❌ 불가 (n=3) = INSUFFICIENT |
| 통신서비스 + 장비 | **14종** (service 3 + equipment 11) | ⚠️ 빠듯 (avgN 13) = magnitude 과대 우려 |
| 통신장비 65종 中 floor 통과 | 11종 | cyclical(5G capex) 혼재 |

★**삼성전자/LG전자 = "통신 및 방송 장비" 오분류 → 제외**(telecom 아님). ★ADV floor 10억 완화(장비주 소형).
★supervisor 경고 정합: 통신서비스(asset_stable) 단독 = n=3 = cross-sectional 불가. 장비 포함 14종도 협소 + archetype 혼재.

## §1. universe (§M.6)

- 전기통신업 + 통신방송장비 − 삼성/LG전자 − 우선주. 시총≥3000억 ∧ ADV≥10억 → **14종**(service 3 + equipment 11).
- ★sub-cluster archetype 혼재: service = asset_stable(배당) / equipment = cyclical(5G capex). §1.6 분리 주의.

## §2. forward 횡단면 IC (momentum) — 비유의

16 테스트 BY 0, raw_p_min=0.127. vol_60(저변동성)이 가장 강(IC -0.11)이나 비유의. momentum 무신호 = asset_stable 정합. ★avgN 13(협소).

## §3. ★valuation 횡단면 (value premium 강 but magnitude 과대)

DART 357 rows(2019~) → PBR/PER cross-sectional z. PIT. coverage PBR 1124 / PER 887 cells.

| signal__h | IC | t_NW | p | n | within | avgN | BY |
|---|---|---|---|---|---|---|---|
| **pbr_z→24M** | **-0.542** | **-12.08** | 0.000 | 61 | **1.00** | 13.0 | ★생존 |
| per_z→24M | -0.280 | -5.12 | 0.000 | 61 | 0.83 | 10.8 | 생존 |
| pbr_z→12M | -0.335 | -3.10 | 0.003 | 73 | 0.71 | 13.1 | 생존 |
| per_z→12M | -0.222 | -3.09 | 0.003 | 73 | 0.86 | 10.7 | 생존 |
| pbr_z→3M/6M | -0.16/-0.20 | -2.7/-2.4 | 0.01/0.02 | 82/79 | 0.75/0.71 | 13.2 | 생존 |

- ★**value premium 방향 매우 강**: 전 horizon 음, **BY 6개 생존**, within 100%@24M, block-boot CI [-0.497, -0.210] 0 배제.
- ★**LOO robust**: 14종 각 제외 시 IC range **[-0.614, -0.456] 전부 음** = 단일 종목(통신3사) 의존 아님 = 신호 robust.
- ★**BUT magnitude 과대평가**: IC -0.54, t=-12.08 = ★n=13 종목 협소 = Spearman rank correlation 극단화 artifact. battery(26종 +0.086 t=3.87) 대비 비현실적 큼.
- → **small-n rule: 방향 신뢰(robust, BY, within, LOO), magnitude hedge(보수 cap)**.

## §4. cross (§M.3)

- 공통인자 β 전부 비유의 (dollar t=-1.55 최강이나 무유의, CI 넓음). ★n 협소로 β 추정 불안정.
- customer-supplier momentum = skip (통신서비스↔장비 내부 supply-chain이나 universe 협소로 무의미).
- regime-conditional (금리): mom_6 IC rate_up +0.135 / rate_down -0.014 (n=21/19, n small).

## §5. PIT + 생존편향

- PIT: 가격 forward-shift safe, valuation rcept_dt 이후, regime ex-ante 금리.
- 생존편향(I PARTIAL): 통신 = 합병 잦음(LG텔레콤/데이콤 통합). 14종 中 1종 부분 이력. ★universe 협소 자체가 더 큰 제약.

## §6. exposure card (§M.7)

14종 peer-relative z. 상위 mom_6_z: 빛과전자 +2.89 / 삼지전자 +0.65. 전체 = `raw-v3/exposure-card-v3.json`. ⛔ 조립 = supervisor.

## §7. net-cost (§M.4)

왕복 33bps / 월 16.5bps. ★valuation(저회전 장기) net 유리 but ★n=13 = 분산 효과 제한, concentration cap 주의.

## §8. verdict

- ★**telecom = asset_stable value 산업** (consumer 재현·강화). PBR/PER value premium 방향 강(BY 6 생존, LOO robust, within 100%).
- ★**universe 협소(14종)** → IC magnitude(-0.54) 과대평가(small-universe Spearman 극단화). 방향 신뢰/magnitude hedge.
- service sub(3종) 단독 = INSUFFICIENT. archetype asset_stable + 장비 cyclical 혼재.
- **verdict_label = PARTIAL** (value premium 방향 강하나 magnitude 과대 + universe 협소).
- ★**consumer(asset_stable valuation 유효)와 동일 archetype 재현** = valuation 산업 분기 강화. ★universe 협소 = 양식 경계 케이스(cross-sectional 최소 종목 ~13 = magnitude 신뢰 하한) = 6산업 batch 시 협소 산업 magnitude hedge 의무.
