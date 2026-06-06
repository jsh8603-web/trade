---
tags: [type/candidate-ledger, domain/equity, sector/consumer, purpose/easy-review]
date: 2026-06-05
purpose: 자문·이론·실측에서 거론된 소비재 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
---

# consumer(소비재) 지표 후보 원장

> ★archetype = asset_stable (방어·배당, per primary 1차 가설) + secondary cyclical(화장품 中의존). 
> ★핵심 발견 = **A-4 sub-sector 부호 CANCEL** (화장품 cyclical value 작동 vs 음식료 defensive 무신호).
> verdict = **PARTIAL** (화장품 per_z TENTATIVE DIRECTIONAL + dollar β 유의 risk-monitor + A-4 분리 트리거).

## ✅ 채택 (yaml 등록 + 검증 통과)

| 지표 | family | tier | 근거 (source·n·검증) |
|---|---|---|---|
| cs_per_z (화장품 sub-cluster) | value | TENTATIVE DIRECTIONAL | 화장품 4사 per_z IC=-0.258 (n=19, wc_p=0.047, t_obs=-2.19, 5d/20d/60d 부호일관). ★단 leave-episode 비유의(single-episode 의존) + within 음비율 71% + n_codes=4 small-n → 방향 약 prior, magnitude haircut. source=validation-conditional-v3.json:subsector_sign_check.per_z.cosmetics |
| dollar β (common factor) | risk-monitor | structural_prior | dollar β=-1.19 (t=-2.57, n=35, HAC lag3, R²=0.21). 원화약세→소비재 약세(수입원가↑/내수). contemporaneous risk. source=validation-cross-v3.json:dollar |
| rev_1m × KRW_weak (conditional) | reversal | TENTATIVE (conditional) | KRW_weak 국면 rev_1m IC=-0.082 (n=34, wc_p=0.0625, t_obs=-1.98). family_2 interaction t=-2.36 유의. OOS 부호유지(✓). source=validation-conditional-v3.json:conditional_ic_surface.rev_1m + family_2_interaction |

## ⏳ 이연 (식별됐으나 미투입)

| 후보 | 출처 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|
| K-food 수출 yoy (관세청) | theory §1.2 | ★시계열 macro 신호 = 산업평균 lag-corr 용도. cross-sectional 종목선택(§K) 에 직접 안 들어감 (전 종목 공통). KRW regime 으로 부분 흡수(수출형 vs 내수형 부호분리). | 통합단계 산업평균 forward 매핑 (M2 lag-corr) |
| 소매판매액/CCSI (통계청·ECOS) | theory §1.4 | ★macro cycle 지표 = regime 라벨링 보강 후보. 현 regime = Macro(CLI)/KRW/flow 3축으로 충분(36셀 N부족). 소비심리 추가 = 셀 폭발. | collector_plan medium. regime 4축 확장 시 |
| 곡물 cost (ZC=F yoy) | theory §1.1 | ★음식료 sub-cluster 한정 cost pass-through(60-120일 lag). 종목 cross-sectional 아닌 산업 마진 driver = forward IC 약 prior. | 음식료 sub-sleeve 분리 후 sub-cluster별 cost-corr |
| EV-EBITDA / 배당수익률 | frame Layer1 / asset_stable primary 보완 | DART stockTotqySttus(주식수 PIT) + 배당 공시 미수집. 현 = FDR 현재주식수 근사. | DART 배당 공시 + 주식수 PIT 수집 |
| size-orthogonal per_z | §M.12 누락축 | 화장품 4사 small-cap value 위장 점검 = n_codes=4 라 demean 효과≈0. 통합단계 size factor 직교 의무. | 통합 register (sleeve 횡단 size factor) |

## ❌ 미채택 / proxy 대체

| 후보 | 사유 |
|---|---|
| 종목별 외국인 flow | KRX login 차단 = DATA-GATE (theory §5 H5 INSUFFICIENT). regime 의 KOSPI 전체 flow(ECOS)로 대체. ⛔deferral 아닌 data-gate. |
| credit β (KR HY) | KR HY OAS 부재 → US HY proxy. β -0.032 t=-1.28 **비유의** → 미채택(소비재 = credit 무노출). |
| momentum (mom_6/12) | uncond IC≈0 (wc_p>0.7), family_2 비유의. ★asset_stable 방어주 = 모멘텀 무신호 정합(battery 대조). 미채택 정직. |
| vol_60 (저변동성) | uncond IC -0.006 비유의. flow_strong_buy 셀 -0.128(n=18 underpowered). 미채택. |
| pbr_z (전체) | uncond IC -0.028 비유의. 화장품 pbr 도 -0.022(per 보다 약). per_z(화장품)가 우세 → pbr 보조. |
| customer-supplier momentum | 소비재 upstream=농산물/원자재 다양 → 부적합. skip(battery/financial 동일). |
| sector-rotation clock | 학술 myth(Molchanov 2024). 미채택. |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)

| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| 화장품 per_z value premium | n_codes=4 small-n + leave-episode 비유의(single-episode 의존). 中소비 cycle(따이공/면세) regime 미분리. ★S5 역공격: size 통제 후 IC-0.172(partial/marginal=0.67>0.5)=genuine value(small-cap 위장 아님) but wc_p0.22 비유의(자유도 소모) = TENTATIVE 정당. | (a) ★화장품 universe 확장(n_codes 4→7+: 코스맥스엔비티/콜마비앤에이치/애경산업/클리오 등) (b) 中소비 regime 분리(면세점 매출/따이공 z) (c) 2026+ pristine OOS 부호유지 |
| rev_1m × KRW_weak | ★[audit 정정] KRW_weak=38개월·12 episode(overfit 우려 완화, "episode≈2" 오류 정정). wc_p0.0625 borderline 잔존 + magnitude small-n. | interaction term magnitude haircut + 2026+ pristine OOS |
| dollar β | contemporaneous(forward 아님) = risk-monitor 용도지 alpha 아님. | forward dollar β 측정 (현 동시노출만) |
| A-4 sub-sector 분리 | 화장품/음식료 분리 시 각 sub-sleeve N 충분성(화장품 4종) + factor β cancel 정량. | sub-sleeve별 독립 measure (통합단계 supervisor) |

## 📌 자산화 enum 분류

| enum | 후보 | 목적 |
|---|---|---|
| rule | (없음 — 단일 BY 생존 0. ★[audit 정정] well-powered cell = 5개 존재(wc_p<0.01)하나 105 multiplicity BY 못넘음) | 검증된 정량 규칙 (현 단계 미충족, M_eff 통합단계) |
| memory | ★A-4 sub-sector 부호 CANCEL (화장품 cyclical vs 음식료 defensive) = consumer 분리 트리거 | 통합 단계 sub-sleeve 분리 입력 + 다음 cycle 자문 prior |
| observe-only | 화장품 per_z (n_codes=4) / rev_1m×KRW_weak (★episode 12, n_months 34) | N 더 누적 후 promotion 결정 |
| evt | (G-B 재자문 미발동 — family_2 살아있음 = "약함" 아님 판정) | promotion-log ERROR 후보 |
| pointer | frame v3 §M.12 (24M degen / small-n haircut / peak-EPS) + §M.11(화이트리스트 결함) | 다음 세션 SSOT 정독 우선순위 |

---

# ★ROTATION 후보 원장 (업종 자체 timing, 2026-06-06 재발굴 — team-lead 규칙 ≥8 후보/≥2 채택)

> 종목 capsule(위) = 소비재 안 종목 selection. 본 섹션 = 소비재 업종 OW/UW timing. raw = raw-v3/measure_rotation_consumer.py.
> ★14 driver(68 측정 셀) 전수 enumerate → 이론 사전확약 → 통계검증 → 채택 4 / 미채택 사유 박제. data-mining 무리발굴 금지.

## ✅ rotation 채택 4 (★G-C 재audit 반영 2026-06-06: primary = cosmetics reversal, CSI tentative 격하)

| 신호 | rho(60d) | wc_p | 판정 | 근거 (이론 + OOS + robustness) |
|---|---|---|---|---|
| **mom_6 reversal** (cosmetics) | −0.324 | 0.004 | ★**primary** (진짜 consumer-specific) | 화장품 변동성 평균회귀(최강). ★외부시장 resid 후 −0.425 강화 = market×beta 아닌 genuine idiosyncratic → primary 승격. OOS −0.75 유지 |
| **mom_6 reversal** (industry) | −0.251 | 0.018 | 채택 | 내수 방어주 평균회귀. residual −0.361 강화 + OOS −0.55 유지 |
| **CSI 소비지출 3M모멘텀** (industry) | +0.325 | 0.001 | ⚠️**TENTATIVE 격하** (was ★STRONG) | ★G-C 재audit: theory-family(m=12) 한정 BY 생존, **m=68 single 미생존 + Bonferroni 미통과 = underpowered**. yoy 부호반대→d3 채택은 사후 '기저효과' mild 정당화. ★C축 robustness 수치(residual +0.370 / LOY +0.24~0.41) = **코드 미산출 추적불가**(아래 falsifier) → STRONG 격하 |
| **홍콩 3M모멘텀** (관광/면세) | +0.254 | 0.044 | TENTATIVE | 리오프닝/면세 risk-on→화장품. OOS적격 but underpowered |

> ⚠️**C축 robustness 추적불가(G-C 재audit 부분결함)**: 위 CSI의 "residual +0.370 / LOY 전부 양(+0.24~0.41)" 및 mom_6 "residual −0.361/−0.335" 수치가 raw-v3 code/json에 산출 함수 부재 = 검증 추적불가. → 코드 추가 OR md 수치 삭제 필요(consumer-analyst 이연, yaml엔 hedge 박제 완료).

## ⏳ rotation TENTATIVE 보조 (이론 일치, underpowered)

| 후보 | best | 사유 |
|---|---|---|
| 곡물 cost-push (음식료) | soy food −0.221 (wc_p0.0695) | corn/wheat/soy 전부 음 일치 + OOS유지 but underpowered(단일 BY 생존 0). 음식료 한정 방향 prior |

## ❌ rotation 미채택 / 사유 박제

| 후보 | result | 미채택 사유 |
|---|---|---|
| **CSI 소비지출/여행비/의류비 yoy** | ★부호 반대 | yoy=level 기저효과(高수준=고점=forward 평균회귀 음). d3(단기변화)와 mechanism 분리 = d3 채택, yoy 기각 |
| 항셍/상하이 3M모멘텀 | 부호 혼재(sse 음) | 中주식 모멘텀 = 과열 reversal? 사전확약(양) 미성립 |
| USDCNY yoy | y_20d 일치/y_60d 반대 | 혼재, 약 |
| 中CLI yoy/d3 | 약신호(n<12 다수) | OECD CLI 발표지연 + 가용 짧음 |
| WTI유가 yoy | −0.261 wc_p0.0165 but OOS flip | 이론일치(원가 음)·in-sample 강하나 ★OOS flip(−0.35→+0.08) = 채택불가 |
| 한국 소매판매 yoy | DATA-GATE | ★KORSARTMISMEI 2024-03 제약(OECD MEI discontinuation) = 구조빈약 사유 박제(이연 아님) |
| XLP-XLY 상대모멘텀 | y_20d 양/y_60d 음 혼재 | 글로벌 ETF rotation = 한국 소비재 매핑 약 |

## 📌 rotation 자산화 enum

| enum | 후보 | 목적 |
|---|---|---|
| rule | (CSI 소비지출 d3 = BY 생존, 단 underpowered tier = observe-only 경계) | M_eff 통합단계 재평가 |
| memory | ★CSI 소비지출 d3(내수 소비심리 모멘텀) = 소비재 OW 핵심 rotation 신호 / yoy는 기저효과 부호반대 | 통합 rotation tilt 입력 + 다음 cycle prior |
| observe-only | 홍콩 관광 모멘텀(underpowered) / 곡물 cost-push(음식료) | N 누적 후 promotion |
| pointer | ★구조빈약 = 中소비 직접지표(면세/따이공) 무료 부재 + 내수 소매판매 2024-03 제약 | collector_plan high (中소비 regime) |
