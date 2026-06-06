---
tags: [type/candidate-ledger, domain/equity, sector/steel, purpose/easy-review]
date: 2026-06-05
purpose: 자문·이론·실측에서 거론된 철강 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
source_artifacts: theory-notes.md + round-1.md(H1~H11, 측정前) + summary.yaml/validation-*(v3 측정) + frame v3 §M.11~M.12
---

# steel(철강·금속) 지표 후보 원장

> ★범위 = 철강 capsule 한정 (12산업 독립 ledger). semiconductor 미러.
> ★verdict 라벨 = small-n rule (CONFIRMED/PARTIAL/TENTATIVE/INSUFFICIENT/REJECTED).
> ★핵심 한 줄: 철강 = cyclical 초자산집약. 가격 momentum **음(reversal, -0.181)** = battery(양)와 반대 = archetype 판별. ★capex_ratio 음(★자산집약도 레벨 anomaly = low-turnover value-like, steel-audit 정정: 증설 cycle 아님) = dispatch capex 일반화 입증. valuation = PBR○ PER✗(peak/trough-EPS).
> ★업종 rotation: ★iron_ore_d3 STRONG 단일(+0.348, 중국 수요 cycle proxy, v2 +0.341 재현=오염0) + 보조 부재(전 후보 iron 통제 후 중복). 상세 = rotation-signals.md.
> ★★small-universe(23종, avg 20) = magnitude inflation 위험 = point estimate literal 금지 + breadth-adj IR + 50% haircut 일관 적용.

## ✅ 채택 (yaml 등록 + 검증 통과)

| 지표 | family | tier | 근거 (source·n·검증) |
|---|---|---|---|
| cs_mom_12_1_reversal | momentum(음=reversal) | PARTIAL→강 (small-universe magnitude hedge) | 12-1 모멘텀 z → 12M forward IC **-0.181**, t_NW -4.42, CI(NW+boot) 0배제, CPCV 1.00, within 100%, leave-episode 생존, cap-weighted -0.244(대형주 강=microcap 아님), ★BY 생존(measure.py m=16). ★small-universe magnitude inflation = breadth-adj IR -0.81 + 50% haircut. source=validation-metrics-v3.json:mom_12_1__12M_mom |
| cs_vol_60_lowvol | lowvol_quality | PARTIAL→강 | 60일 변동성 z → 6M/12M forward IC -0.117/-0.134(저변동 outperform), BY 생존, conditional y_60d wc_p=0.0005(BY top), within 100%, hi_adv 강. theory M6(defensive quality) 정합. |
| cs_mom_6_reversal | momentum(음) | PARTIAL | 6M 모멘텀 z → 3M forward -0.095(reversal), CPCV 1.00, within 100%, BY 생존, conditional y_60d -0.102(wc_p=0.003). |
| ★**cs_capex_ratio** (유형/총자산) | ★asset_intensity_level | TENTATIVE DIRECTIONAL | ★★dispatch capex 일반화 핵심. y_60d IC=**-0.084** wc_p=0.0005, walk-forward OOS 부호유지(IS -0.111→OOS -0.053), prior 음 일치 = ★자산집약도 레벨 anomaly(low-turnover value-like, steel-audit 정정: ppe_yoy 증설변화율 무신호 + 종목내 시계열 std 0.04 vs 종목간 0.115 = 레벨 고정특성, 증설 cycle 아님). regime: Slowdown/KRW_neutral/flow_neutral 모두 음 유의. ★자동차(high_confidence) 재현 = 자산집약 4섹터 일반화 1보. ★단 통합 BY(m=180) 미생존 + y_20d 약. CGS asset growth = 부수 인용. source=validation-fundamentals-cycle-v3.json |
| cs_pbr_z (3M/6M/12M) | value | PARTIAL→강 | PBR cross-sectional z → 3M/6M/12M forward IC -0.10~-0.16(단조 일관), t_NW -2.6~-3.1, ★BY 생존 3개(m=8), CPCV 1.00, within 0.86~0.88. ★PER 무신호(peak/trough-EPS trap). small-universe magnitude haircut. source=validation-valuation-v3.json |
| ★**conditional IC surface** (regime별) | value/momentum/lowvol × KRW_neutral | PARTIAL→conditional 강 | ★S2 본체(measure_conditional.py). ★KRW_neutral regime서 mom_6 y_5d -0.169(wc_p=0.0015) / vol_60 -0.121 / pbr_z -0.105 / capex -0.111 증폭(반도체 KRW_weak과 다름=철강 특수성). flow_strong_buy서 약화. walk-forward OOS 전부 부호유지. source=validation-conditional-v3.json |
| ★**외국인flow regime** (ECOS 28d z) | regime 축 | 측정완료 | round-1 H10을 ECOS 802Y001/0030000 일별로 해소. flow regime 축 conditional 측정완료. |

## 🧪 신규 cycle 지표 측정완료 (★이연 금지 = 지금 측정, verdict 박제)

> 사용자 박제 "이연 금지" → DART 분기 재구성 측정완료(measure_fundamentals_cycle.py). 결과 정직 박제.

| 지표 | prior 부호 | 측정결과 (y_20d/y_60d) | walk-forward OOS | verdict |
|---|---|---|---|---|
| ★**capex_ratio** (유형/총자산, ★자산집약도 레벨) | 음 | y_60d IC=**-0.084** wc_p=0.0005(강유의) / y_20d -0.030 비유의 / KRW_neutral -0.111 wc_p=0.001 | IS -0.111 → OOS -0.053 ✅부호유지 | ★**TENTATIVE DIRECTIONAL** (★dispatch capex 가설 입증 = 자동차 재현. ★자산집약도 레벨 anomaly=low-turnover value-like[steel-audit 정정, ppe_yoy 증설변화율 무신호], prior 음 일치, 장기 horizon, ★통합 BY 미생존 m=180) |
| **ppe_yoy** (유형자산 yoy, 증설 가속) | 음 | y_60d IC=+0.006 비유의 | IS +0.041 → OOS -0.024 ❌반전 | INSUFFICIENT (OOS 부호반전 = artifact). capex 수준(ratio)은 작동, 증가율(yoy)은 약 = 정직 보고 |
| **inv_ratio** (재고/총자산) | 음 | y_60d IC=**+0.047** wc_p=0.18 | IS +0.003 → OOS +0.098 ✅부호유지(양) | ★**prior 반증** — y_60d 양(prior 음 반대). ★반도체 동일 패턴(inv_ratio 양). 메커니즘 재해석: 재고/자산 高=생산확대 prox. 비유의 |
| **inv_yoy** (재고 yoy) | 음 | y_20d IC=-0.002 비유의 | — | INSUFFICIENT (비유의) |
| **rnd_ratio** (무형/총자산) | 양 | y_20d IC=+0.025 wc_p=0.38 | — | INSUFFICIENT (비유의, prior 양과 약 정합이나 비유의. 철강 R&D 미미) |

★신규지표 종합: **capex_ratio(★자산집약도 레벨 anomaly = low-turnover value-like)만 TENTATIVE DIRECTIONAL** = ★dispatch capex 가설 입증(자동차 재현). ★ppe_yoy(증설 변화율) 무신호 = 신호 source=레벨(고정특성)이지 증설 cycle 아님(steel-audit 정정). inv_ratio prior 반증(반도체 동형). 통합 FDR m=180 survivors=0(garden-of-forking-paths 차단). = 정직 보고(over-claim 0).

### ★capex 종목 selection vs 섹터 timing 검증 (team-lead prior 정정, 2026-06-05)

team-lead 정정: 화학 capex REJECTED(NCC 동시증설=섹터 timing 누수, 종목 spread 부재) / 조선 무신호 / auto만 예외. → ★철강 cross-sectional spread 검증 의무(one-sided 음 단정 회피).

| 검증 | 결과 | 판정 |
|---|---|---|
| cross-sectional spread (CV) | CV=0.32 (>0.3). 종목별 capex_ratio range [0.16 하이록 가공 ~ 0.61 태웅 단조] | ★종목 분산 충분 |
| 분산분해 within/(within+between) | within(종목)=0.0146 vs between(섹터동시)=0.0006 → ratio **0.96** | ★종목 selection 압도적 우세 |

★**verdict: 철강 capex = genuine 종목 selection anomaly (섹터 timing 누수 기각)**. 고로/가공/강관/단조 자산집약도 상이 = 종목 spread 충분 → 화학(NCC 동시증설, REJECTED)과 근본적 다름. one-sided 음 단정 회피 = 데이터(분산분해)가 selection 유효 판정. source=validation-capex-spread-v3.json. ★단 small-universe magnitude hedge 유지(메커니즘 입증, magnitude tentative).

## ⏳ data-gate (현 데이터 측정 불가 — deferral 아님)

| 후보 | 출처 | 상태 | unblock 조건 |
|---|---|---|---|
| **종목레벨 외국인 flow** (cs-signal) | round-1 H10 | ★**DATA-GATE**(deferral 아님) | KRX 종목별 외국인 net buy = 인증 차단. 현 데이터 측정 불가. 시장레벨 regime(ECOS 일별)은 측정완료. unblock = KRX 인증 OR 증권사 API |
| **중국 조강생산 / 철광석(Platts) / 후판·열연 가격** (산업 cycle timing) | theory M4 / frame §M.3 | ⏳ proxy 사용 중 | 현 = SLX/VALE proxy. 직접 = 중국 NBS 조강(월별 무료)·Platts·한국철강협회. cross-sectional 아닌 timing/regime 변수 |
| EV-EBITDA (cyclical 차선 metric) | frame archetype | ⏳DART 부채/현금 계정 추가 | DART fnlttSinglAcntAll 부채총계+현금성자산. ★PBR 작동하므로 우선순위 medium |
| **2축 merge conditional IC** (Macro×flow) | frame §M3 collapse | 36셀 full N≥24=0(small-universe). 단일축만 powered | supervisor 통합단계 또는 N 누적 |
| **M_eff 통합 FDR 보정** | G-F §3 | naive m=180 과대(pbr·mom 강상관). 산업=naive+M_eff_signal(3.0) | supervisor 통합단계(M.7) |
| **배당수익률** (asset_stable secondary, theory M6) | round-1 H6 보조 | DART 배당 미수집 | DART 배당 공시 + 가격 (저우선) |
| **size-orthogonal PBR 완전 입증** | frame §M.12 / S5-B | Fama-MacBeth PBR\|Size t=-1.98 경계(small-universe) | universe 확장 또는 N 누적 후 t>2 확정 |
| family-neutralized IC (FF5/KR-factor) | frame §M5 | 산업 = unconditional 까지. region-matched = 통합단계 | 통합 supervisor |

## ❌ 미채택 / proxy 대체

| 후보 | 사유 |
|---|---|
| per_z (전 horizon) | ★PER cross-sectional 전 horizon IC -0.034~-0.108, p_NW>0.10 **전부 비유의** = peak/trough-EPS trap(정점 peak-EPS + 다운 적자 trough 양방향 왜곡). cyclical 정의 지지(반도체/자동차 동형). E/P 대체 권고. |
| ppe_yoy (capex 증가율) | walk-forward OOS 부호반전 = artifact. capex 수준(ratio)은 작동, 증가율(yoy)은 약. |
| customer-supplier momentum (SLX/VALE lagged) | ★REJECTED as alpha — 전 lag(0-3) 비유의(p 0.18~0.49). 한국 철강=글로벌 cycle/철광석 **contemporaneous** 동조지 forward 예측력 부재(§D falsifier 작동). 동조성분=RegimeGlasso Ω 흡수. |
| dollar β (강달러→철강 가설) | β -1.38, t -1.67 **비유의**(CI 0포함). 약 prior. ★단 KRW regime 축 conditional 재검(measure_conditional) = 약. |
| VIX/rate β | 전부 비유의 (t<1.2). |
| sector-rotation business-cycle clock | 학술 myth(Molchanov 2024). |
| inv_yoy / rnd_ratio | 비유의. |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)

| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| cs_mom_12_1_reversal | ★small-universe(20종) magnitude inflation. -0.181 진짜인가 universe artifact인가. BY 통합 미생존 | breadth-adj IR(-0.81) + universe 확장(소형주 floor 완화) 후 magnitude 확정. e-CUSUM 부호반전 모니터 |
| cs_capex_ratio | ★dispatch capex 가설. y_60d만 강(y_20d 약). 통합 BY 미생존. ★자산집약도 레벨 anomaly(value-like) 진짜인가 | ★자산집약 4섹터(화학/정유/조선) cross-sector 일관성(메인 종합, ★레벨 anomaly로 종합) + N 누적 OOS |
| cs_pbr_z | size 위장 점검(S5-B) t=-1.98 경계. small-universe demean 효과 약 | universe 확장 후 Fama-MacBeth t>2 확정 + breadth-adj |
| credit/oil β | US HY OAS proxy(KR HY 부재), n=35 small-n tentative | KR 회사채 spread 확보 후 재측정 |
| conditional KRW_neutral | walk-forward OOS 생존(✅)하나 interaction term 비유의(t=-1.63 small-n) | N 누적 후 interaction t>2 또는 차기 vintage OOS |

## 🔄 flip-register (regime-conditional sign flip — ★pristine OOS 게이트, 현 vintage 확정 금지)

| flip cell | uncond → conditional 부호 | n / wc_p / status | 해석 (가설) | OOS 게이트 |
|---|---|---|---|---|
| pbr_z [macro=Slowdown] | 음(-0.063) → **양(+0.017)** | n=25 / wc_p=0.78 / powered | 침체국면서 저PBR value 무효(역발상) | 비유의 = 관찰만 |
| mom_6 [krw=KRW_weak] | 음 → 양(sign-flip detect) | underpowered | 원화약세서 momentum 반전? | n<24 차기 vintage |

★flip-register 원칙: 전부 비유의/underpowered = ⛔현 vintage 확정 금지. 차기 vintage pristine OOS 재현 시만 승격. 현재 = "관찰 등록"만.

## 📌 자산화 enum 분류

| enum | 후보 | 목적 |
|---|---|---|
| rule | (없음 — BY 통합 미생존 + small-universe hedge 로 rule 승격 보류) | 검증된 정량 규칙 |
| memory | "철강 momentum=음(reversal -0.181) = cyclical peak 판별. battery(양)와 부호 반대" | archetype 판별 규칙 |
| memory | "★capex_ratio 음(asset growth anomaly) = 철강(초자산집약)서 자동차 재현 = 자산집약 4섹터 일반화 1보" | dispatch capex 일반화 입력 |
| memory | "철강 conditional 증폭축 = KRW_neutral (반도체 KRW_weak과 다름). 철강=중국 cycle dominant, 환율 부차" | regime 해석 |
| memory | "★small-universe(23종, avg 20) momentum -0.181 = magnitude inflation. breadth-adj IR -0.81 = 중강. point estimate literal 금지" | small-universe 재발 방지 (frame §M.12 anchor) |
| observe-only | cs_mom_12_1 / cs_capex_ratio / cs_pbr_z | BY 통합 미생존·small-universe → N 누적 + 2nd cycle 후 promotion |
| evt | (G-B 재자문 미발동 — walk-forward + family BY 생존으로 "약함" 반증) | promotion-log ERROR 후보 |
| pointer | "★capex 일반화 = 자산집약 4섹터 cross-sector 종합(메인). conditional 36셀 = dispatch 본체" | 다음 세션 SSOT 우선순위 |

## ⚠️ G-B 재자문 트리거 점검 (dispatch §G-B)

- 조건 = BY 생존 0/m **AND** 최강 raw_p > 2×thresh.
- 현황: 통합 family(m=180) BY 생존 0, raw_p_min=0.0005. ★단 momentum/vol family(measure.py m=16)는 BY 생존 7개 + conditional cell wc_p 강(0.0005~0.011) + walk-forward OOS 전부 생존 + capex 가설 입증.
- → ★"신호 약함" 반증 명확(walk-forward + family BY 생존) = G-B 자동자문 **skip 권고**(supervisor 판단). 통합 m 과대 = M_eff 미통합 + small-universe.

---

## 🔄 업종 rotation 신호 후보 원장 (rotation-signals.md 정합, 2026-06-05)

> ★종목 selection(위 본체)과 별 차원 = 업종 자체 OW/UW timing. team-lead "채택 ≥2" 지시 → ★억지 발굴 금지 전수 재판정.
> ★★universe 오염 검증: 철강 prices.parquet = strict 23종(1차 철강 제조업) = pass_floor 정확 일치 = 오염 0. iron_ore_d3 strict 재현 +0.348 ≈ v2 +0.341 = 정유(가스9종 섞임)와 달리 진짜 신호.

### ✅ 채택 (rotation)
| 신호 | source | IC(y_60d) | 검증 | 판정 |
|---|---|---|---|---|
| ★**iron_ore_d3** | TIO=F 철광석 3M | +0.348 | wc_p=0.0025(Bonferroni 간발 생존), OOS 부호유지, leave-2021/2022 생존, residualize +0.290, 부호 양=중국 수요 cycle proxy(iron vs china_fxi corr +0.17) | ★STRONG (tentative, small-n) |

### ❌ 미채택 (rotation, 사유별)
| 후보 | source | 사유 |
|---|---|---|
| mom_3_self (업종 3M 모멘텀) | 업종 index | raw +0.228 살아남으나 ★iron_ore_d3 통제 후 incremental t=0.87 = 중복(iron에 흡수). v1 "data-mining" → residualize 후 유지하나 iron과 중복이라 보조 불가 |
| china_fxi_yoy (중국 수요) | FXI ETF | raw +0.170 OOS 유지하나 wc_p=0.081 marginal + iron 통제 후 t=1.05 = 중복 |
| slx_iron_spread (철강 마진) | SLX/TIO | raw -0.196(부호 사전확약 양과 반대) + iron 통제 후 t=0.11 = 중복 + 부호반대 |
| credit_baa_d3 (전방 수요) | FRED BAA10Y | OOS flip, wc_p=0.85 비유의 |
| valuation_band_yoy (mean-rev) | 업종 yoy | OOS flip, 비유의 |
| hrc_margin_yoy (열연마진) | SLX/TIO yoy | OOS flip, 비유의 |
| coking_coal_d3 (원료탄) | BTU | OOS flip, 비유의 |
| usdkrw_d3 (수출) | DEXKOUS | OOS flip, 비유의 |
| iron_ore_yoy | TIO=F yoy | OOS flip (d3는 살아남으나 yoy는 무효) |
| foreign_flow | ECOS | ★전산업 공통 L축 = steel 고유 채택 금지(중복 계상 차단, team-lead 규칙) |

### 📌 rotation 결론 (정직)
★**iron_ore_d3 STRONG 단일 + 보조 부재**. 사용자 "≥2" 목표 미달이나 = 철강 rotation은 ★단일 dominant driver(중국 수요 cycle = 철광석 모멘텀)로 수렴 = 다른 후보 전부 그 cycle의 중복 표현. 억지 발굴 시 garden-of-forking-paths → 데이터가 보조 부재 판정(정직 유지). 종목 selection(본체)은 별 차원으로 다수 신호 채택(momentum reversal/vol/pbr/capex).
★China PMI/property/credit impulse 직접 = FRED 부재(CHNPMINDXM discontinued) → FXI 통합. 직접 열연-철광석 spread(한국철강협회) = collector_plan.

### 📌 자산화 enum (rotation 추가)
| enum | 후보 | 목적 |
|---|---|---|
| memory | "철강 rotation = iron_ore_d3 단일 STRONG(중국 수요 cycle). 보조 전부 중복 = 단일 dominant driver 산업" | rotation 해석 |
| memory | "철강 universe strict 23종 = 오염 0 (1차 철강 제조업 정밀필터). v2 재현 일치 = 정유와 달리 진짜" | universe 오염 검증 패턴 |
| observe-only | iron_ore_d3 | BY 미생존(Bonferroni 간발) → N 누적 후 promotion |
