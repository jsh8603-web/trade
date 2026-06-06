---
tags: [type/rotation-signals, domain/equity, sector/steel, scope/equity-kr]
date: 2026-06-05
purpose: 철강 업종 자체 rotation 신호 (업종 OW/UW timing, 종목 selection 아님). 이론→통계검증→판정.
mirror_of: rotation-analyst v2 (_rotation/validation-rotation-v2.json) 검증·심화
---

# steel(철강) 업종 rotation 신호

> ★capsule 본체(summary.yaml) = 종목 cross-sectional selection. 본 문서 = **업종 자체 rotation**("어느 국면에 철강 업종 OW/UW") = 별 차원.
> ★★team-lead universe 오염 체크 의무: rotation-analyst v2가 산업 디렉토리 prices.parquet 전체 패널 사용 → 부수종목 오염 가능(정유 "crack +0.241"=가스9종 섞임 가짜). ★철강 = strict 화이트리스트로 재현·비교 필수.

## §0. ★★strict universe vs v2 비교 (오염 검증 — team-lead CRITICAL)

| 항목 | 결과 |
|---|---|
| 철강 prices.parquet universe | **23종 (1차 철강 제조업 정밀필터)** = pass_floor 23종과 **정확히 일치** (부수종목 0) |
| 화이트리스트 | POSCO홀딩스/현대제철/세아베스틸/동국제강/세아제강/KG스틸/대한제강/휴스틸/태웅(단조)/성광벤드(피팅) 등 순수 철강 |
| ★iron_ore_d3 재현 (strict 23종) | **raw IC = +0.348** (wc_p=0.0025, OOS 부호유지) |
| v2 값 (디렉토리 전체 패널) | +0.341 |
| **차이** | **+0.348 vs +0.341 = 거의 일치 (±0.007)** |

★★**결론: 철강은 오염 없음** (정유와 다름). 철강 prices.parquet은 작업 초반 "1차 철강 제조업" Industry 정밀필터 + 명시 제외(발전설비/상사/전선)로 구성 = v2 패널 = strict 화이트리스트 = 동일 23종. → ★v2 "iron_ore +0.341 STRONG"은 **진짜 철강 신호**(가짜 아님). 정유처럼 부수종목 섞인 게 아님.

## §1. 이론 + 부호 사전확약 (증권 리서치/논문 기반, 측정 前 동결)

철강 업종 rotation = **중국 수요 cycle + 철광석 원가 + 마진 spread**가 driver. ★철강 = 중국 조강생산 ~55% 점유 → 중국 부동산·인프라 수요가 글로벌 철강가격·spread 좌우.

| # | 신호 | source(proxy) | 이론 메커니즘 | ★사전확약 부호 |
|---|---|---|---|---|
| 1 | **iron_ore_yoy** | TIO=F 철광석 yoy | 원가↑(음) vs 수요동행↑(양) 양면 | 데이터판정(양/음) |
| 2 | **iron_ore_d3** | TIO=F 3M change | 철광석 3M 모멘텀 = 중국 수요 cycle proxy(가격↑=수요강) | **양 prior** (수요 동행) |
| 3 | **china_fxi_yoy** | FXI 중국 ETF yoy | 중국 수요 = 철강 최대 driver(조강 55%) | **양 prior** |
| 4 | **china_fxi_d3** | FXI 3M change | 중국 수요 모멘텀 | 양 prior |
| 5 | **slx_steel_yoy** | SLX 글로벌 철강 ETF yoy | 글로벌 철강 cycle 동조 | 양 prior |
| 6 | **slx_iron_spread** | SLX/TIO 3M change | 철강 마진 proxy(열연-철광석 spread, 마진↑→주가) | **양 prior** (마진) |
| 7 | **coking_coal_d3** | BTU 원료탄 3M | 원료탄 원가 | **음 prior** (원가) |
| 8 | **usdkrw_d3** | DEXKOUS 3M | 원화약세→수출 양 | 양 약 prior |

★후보 = **8개** (철광석 2 + 중국 2 + 글로벌철강 1 + 마진spread 1 + 원료탄 1 + 환율 1). China PMI/property/credit impulse = FRED 직접 부재(CHNPMINDXM discontinued) → FXI(중국 ETF)로 수요 proxy 통합.

## §3. 측정 결과 (철강 업종 forward IC, strict 23종 eq-weight index)

측정: `raw-v3/measure_rotation.py` → `validation-rotation-steel-v1.json`. residualize(공통인자 d_usdkrw/foreign/semi_ppi) = idiosyncratic. NW HAC + wild-cluster + walk-forward OOS.

| 신호 | raw IC (y_60d) | wc_p | resid IC | walk-forward OOS | 사전확약 |
|---|---|---|---|---|---|
| ★**iron_ore_d3** | **+0.348** | **0.0025** | +0.290 | ✅부호유지(IS/OOS) | 양 ✅ |
| slx_iron_spread | -0.196 | 0.090 | -0.131 | ✅부호유지 | 양 ✗(반대) |
| china_fxi_yoy | +0.170 | 0.081 | -0.030 | ✅부호유지 | 양 ✅ |
| usdkrw_d3 | -0.098 | 0.385 | -0.134 | ❌flip | 양 ✗ |
| iron_ore_yoy | -0.092 | 0.369 | -0.169 | ❌flip | 양/음 |
| china_fxi_d3 | +0.122 | 0.269 | +0.049 | ❌flip | 양 |
| slx_steel_yoy | +0.041 | 0.719 | +0.160 | ❌flip | 양 |
| coking_coal_d3 | -0.029 | 0.808 | +0.105 | ❌flip | 음 |

### robustness (iron_ore_d3 = 최강 신호)
- **부호 메커니즘**: iron_ore_d3 vs china_fxi corr = +0.171 → 철광석 가격↑ = 중국 수요↑ 동행 = ★**부호 양 = "원가"가 아니라 "중국 수요 cycle proxy"** 입증 (이론 정합, 철강 중국 dominant).
- **leave-episode**: full +0.348 → ex-2021 +0.299 / ex-2022 +0.356 = 둘 다 생존 (단일 episode 종속 아님).
- **FDR**: m=16, raw_p_min=0.0025(iron_ore_d3) ≈ Bonferroni α=0.0031 → ★iron_ore_d3 **Bonferroni 간발 생존**. BY는 m=16 미생존(small-n).
- **residualize**: 공통인자 제거 후 +0.290 유지 = idiosyncratic(공통 cyclical 잔여 아님).

## §4. 판정 (STRONG / TENTATIVE / REJECTED / data-mining)

| 신호 | 판정 | 근거 |
|---|---|---|
| ★**iron_ore_d3** | ★**STRONG (tentative, small-n)** | 이론(중국 수요 cycle proxy)+통계(IC +0.348, wc_p=0.0025, Bonferroni 간발 생존, OOS 부호유지, leave-episode 생존, residualize 유지) 양립. ★단 BY 미생존 + n=84 = magnitude tentative |
| china_fxi_yoy | ★중복(보조 불가) | 이론(중국 수요 양)+통계(IC +0.170, OOS 유지) but wc_p=0.081 marginal + ★iron_ore_d3 통제 후 incremental t=1.05 비유의 = 중복(§4.5) |
| slx_iron_spread | ★중복(보조 불가) | IC -0.196(OOS 유지)이나 사전확약 양과 반대(SLX 주가 선반영 mean-reversion?) + ★iron 통제 후 t=0.11 = 중복(§4.5) |
| iron_ore_yoy / coking_coal / slx_steel_yoy / usdkrw / china_fxi_d3 | REJECTED | OOS flip 또는 비유의. data-mining 채택불가 |

### ★종합 판정
- **iron_ore_d3 = STRONG rotation 신호** (tentative): ★철광석 3M 모멘텀 = 중국 수요 cycle proxy → 철강 업종 OW/UW timing. "철광석 가격 상승기 = 중국 수요 강세 = 철강 업종 OW". v2 +0.341 재현 = 오염 아닌 진짜.
- ★**부호 정정(이론 심화)**: 사전확약 "철광석=원가(음)"가 아니라 **"철광석 가격 = 중국 수요 cycle 선행지표(양)"**. 데이터가 수요 동행 우세 판정(원가 효과는 spread에 흡수, iron_ore_yoy 음은 OOS flip).
- ★capsule 종목 selection(KRW_neutral 증폭, capex level)과 정합: 둘 다 **중국 cycle dominant**(환율 부차) 결론.

## §4.5 ★보조 신호 보강 재판정 (team-lead 지시 "채택 2개 이상" → ★억지 발굴 금지, 정직 결론)

사용자 지시 "살아남는 채택 ≥2"에 따라 보조 후보 ≥8 전수 재판정 + ★iron_ore_d3 통제 후 incremental 검정(독립 예측력 = 중복 차단).

| 보조 후보 | prior | raw IC(y_60d) | wc_p | OOS | ★iron_ore_d3 통제 후 incremental t | 판정 |
|---|---|---|---|---|---|---|
| **mom_3_self** (업종 3M 모멘텀) | data-mining 의심 | +0.228 | 0.031 | ✅유지 | **t=0.87** | ★중복(iron에 흡수) — 보조 불가 |
| **china_fxi_yoy** (중국 수요) | 양 | +0.170 | 0.081 | ✅유지 | **t=1.05** | ★중복 — 보조 불가 |
| **slx_iron_spread** (마진) | 양 | -0.196 | 0.090 | ✅유지 | **t=0.11** | ★중복 + 부호반대 — 보조 불가 |
| credit_baa_d3 (전방 수요) | 음 | +0.020 | 0.85 | ❌flip | — | REJECTED |
| valuation_band_yoy (mean-rev) | 음 | -0.035 | 0.79 | ❌flip | — | REJECTED |
| hrc_margin_yoy (열연마진) | 양 | -0.015 | 0.90 | ❌flip | — | REJECTED |
| coking_coal_d3 (원료탄) | 음 | -0.029 | 0.81 | ❌flip | — | REJECTED |
| usdkrw_d3 (수출, L축 아님 확인) | 양 | -0.098 | 0.38 | ❌flip | — | REJECTED |
| iron_ore_yoy | 양/음 | -0.092 | 0.37 | ❌flip | — | REJECTED |

★**보조 신호 부재 (정직 결론, 억지 발굴 금지)**: 살아남은 후보(mom_3/china_fxi/slx_iron_spread)가 ★전부 iron_ore_d3 통제 후 incremental **t<2** (0.87/1.05/0.11) = **iron_ore_d3와 중복**(독립 예측력 0). 나머지 5후보 = OOS flip REJECTED.
- ★메커니즘: 철강 rotation은 **단일 dominant driver(중국 수요 cycle = 철광석 모멘텀)**로 수렴. 업종 자체 모멘텀(mom_3)·중국 ETF(china_fxi)·마진(spread)은 모두 그 cycle의 다른 표현 = 중복 계상. = 철강 = 중국 cycle 단일축 산업 본질 반영.
- ★foreign_flow = 전산업 공통 L축이라 steel 고유 채택 안 함(중복 차단, team-lead 규칙 준수).
- ★결론 = **iron_ore_d3 STRONG 단일 + 보조 부재**(채택 1개). 사용자 "≥2" 목표 미달이나 ★억지 발굴 시 garden-of-forking-paths = 데이터가 보조 부재 판정(정직 유지). 종목 selection(capsule, momentum reversal/vol/pbr/capex)은 별 차원으로 다수 신호 존재.

## §5. 한계·정직단서
- ★proxy 한계: 철광석=TIO=F(US-listed futures), 중국=FXI(US-listed ETF) = 글로벌 proxy(KR 직접 아님). China PMI/property/credit impulse 직접 = FRED 부재(discontinued) → FXI 통합.
- ★small-n: n=84 month, BY 미생존(Bonferroni 간발) = magnitude tentative, 부호·방향만 신뢰.
- slx_iron_spread 부호 반대 = 마진 spread proxy(SLX/TIO) 부적합 가능(SLX 주가 선반영) → 직접 열연-철광석 spread(한국철강협회) collector_plan.
- ★종목 selection(capsule) vs 업종 rotation(본 문서) = 별 차원, 통합 시 L축 1회계상(supervisor).
