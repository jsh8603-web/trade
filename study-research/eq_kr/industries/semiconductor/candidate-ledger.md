---
tags: [type/candidate-ledger, domain/equity, sector/semiconductor, purpose/easy-review]
date: 2026-06-05
purpose: 자문·이론·실측에서 거론된 반도체 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
source_artifacts: round-1.md(H1~H8, 2026-05-31) + summary.yaml/validation-v3-cross-sectional.md(v3 측정, 2026-06-03~04) + frame v3 §M.11~M.12
---

# semiconductor(반도체) 지표 후보 원장

> ★범위 = 반도체 capsule 한정 (12산업 독립 ledger). 기존 round-1 가설 8 + v3 횡단면 측정 흡수.
> ★verdict 라벨 = small-n rule (CONFIRMED/PARTIAL/TENTATIVE/INSUFFICIENT/REJECTED).
> ★핵심 한 줄: 반도체 = cyclical(peak). 가격 momentum 이 **음(reversal)** = battery(양)와 반대 = archetype 판별 결정 증거. valuation = PBR○ PER✗(peak-EPS trap).

## ✅ 채택 (yaml 등록 + 검증 통과)

| 지표 | family | tier | 근거 (source·n·검증) |
|---|---|---|---|
| cs_pbr_z_24m | value | PARTIAL (24M eff_N degenerate hedge) | PBR cross-sectional z → 24M forward IC -0.114, t_NW -4.23, BY **유일 생존**, CPCV oos 1.00, within 100%(2019-24 전연도 음). ★단 24M overlap eff_indep_N≈2.5 = significance overlap inflation → breadth-adj IR -1.52 (mom_6 와 유사 수준). source=validation-valuation-v3.json:pbr_z__24M_value |
| cs_mom_6m_reversal | momentum(음=reversal) | PARTIAL | 6M 모멘텀 z → 12M forward IC **-0.065**(reversal), t_NW -2.90, CI(NW+boot) 0배제, CPCV oos 1.00, within 100%, leave-episode 생존(ex-peak -0.087 강화), cap-weighted -0.092(대형주 강=microcap 아티팩트 아님). ★BY/Bonferroni **미생존**(raw_p 0.005 > 임계). source=validation-metrics-v3.json:mom_6__12M_mom |
| cs_mom_12_1_reversal | momentum(음) | PARTIAL | 12-1 모멘텀 z → 12M reversal IC -0.068, CPCV 0.87(mom_6 보다 약), within 0.83, BY 미생존. |
| cs_rev_1m | reversal | TENTATIVE | 1M 단기수익 z → 1M forward IC -0.043(단기 reversal), CPCV 1.00, BY 미생존. 약효. |
| ★**conditional IC surface** (regime별) | value/momentum × KRW_weak | PARTIAL→conditional 강 | ★S2 신규 측정완료(measure_conditional.py, 2026-06-05). KRW_weak regime서 pbr_z y_5d wc_p=0.0005 / mom_6 -0.096 / rev_1m -0.091 증폭. flow_strong_buy서 momentum 소멸. = "어느 국면에 어느 지표" surface. source=validation-conditional-v3.json |
| ★**family_2 interaction** (KRW_weak × signal) | momentum/reversal | 유의(t=-2.95/-2.33) | ★frame A-5 의무 충족. main 비유의인데 interaction 유의 = 신호 conditional(약함 아님). pooled panel month-clustered SE. |
| ★**외국인flow regime** (ECOS 28d z) | regime 축 | 측정완료 | ★round-1 H5 Tier1 핵심을 ECOS 802Y001/0030000 일별로 해소(EWY proxy 불필요). flow_strong_buy서 momentum IC 감소(theory M3 정합). |
| ★**size-orthogonal PBR** (Fama-MacBeth) | value | 독립 입증 | ★Q6 비판 기각. PBR\|Size 통제후 b=-0.043 t=-2.47 유의 유지(Size\|PBR b=-0.018 비유의) = small-cap 위장 아님. |

## 🧪 신규 cycle 지표 측정완료 (★이연 금지 = 지금 측정, verdict 박제)

> 사용자 박제 "이연 금지" → DART 분기 재구성으로 측정완료(measure_fundamentals_cycle.py → validation-fundamentals-cycle-v3.json). 결과 정직 박제(약신호 다수).

| 지표 | prior 부호 | 측정결과 (y_20d/y_60d) | walk-forward OOS | verdict |
|---|---|---|---|---|
| ★**ppe_yoy** (CAPEX asset growth, 유형자산 yoy) | 음 | y_60d IC=-0.034 wc_p=0.0155(유의 근접) / KRW_neutral -0.065 wc_p=0.0005 | IS -0.042 → OOS -0.028 ✅부호유지 | **TENTATIVE DIRECTIONAL** (asset growth anomaly 정합, prior 음 일치, 장기 horizon, ★BY 미생존 m=183) |
| **inv_ratio** (재고/총자산) | 음 | y_60d IC=**+0.045** wc_p=0.002 | IS +0.031 → OOS +0.063 ✅부호유지(양) | ★**prior 반증** — 일관되게 **양**(prior 음과 반대). 재고순환 가설(재고peak→주가bottom) 반대. 메커니즘 재해석: 재고/자산 高 = 성장/생산확대 종목 prox 가능 |
| **capex_ratio** (유형/총자산) | 음 | y_20d IC=+0.010 비유의 | IS +0.036 → OOS +0.009 약화 | INSUFFICIENT (비유의, OOS 약화) |
| **inv_yoy** (재고 yoy) | 음 | y_20d IC=+0.003 비유의 | — | INSUFFICIENT (비유의) |
| **rnd_ratio** (무형/총자산) | 양 | y_20d IC=-0.004 비유의 | — | INSUFFICIENT (비유의, prior 양과 약하게 반대) |

★신규지표 종합: **대부분 약/비유의** = 가격(mom/rev)·valuation(PBR) 신호보다 현저히 약. ppe_yoy(CAPEX)만 TENTATIVE(부호 정합+OOS 생존+장기 horizon). inv_ratio prior 반증(메커니즘 재해석 후보). 통합 FDR m=183 survivors=0(garden-of-forking-paths 차단으로 신규 추가시 더 엄격). = 정직 보고(over-claim 0).

## ⏳ data-gate (현 데이터 측정 불가 — deferral 아님)

| 후보 | 출처 | 상태 | unblock 조건 |
|---|---|---|---|
| **종목레벨 외국인 flow** (cs-signal) | 2차리서치 Q9 + Grinblatt-Keloharju 2000 | ★**DATA-GATE**(deferral 아님) | ★KRX 종목별 외국인 net buy = 인증 차단(pykrx KeyError). 현 데이터 **측정 불가** = data-gate(데이터 부재, 불확실성 deferral 아님). 시장레벨 regime(ECOS 일별)은 측정완료. unblock = KRX 인증 OR 증권사 API |
| EV-EBITDA (cyclical primary_metric) | frame archetype | ⏳DART 부채/현금 계정 추가 필요 | DART fnlttSinglAcntAll 부채총계+현금성자산 (현 데이터로 가능 = 후속 측정 대상, deferral 아님) |
| **2축 merge conditional IC** (Macro×flow) | frame §M3 collapse 2단계 | 36셀 full N≥24=0(단일축만 powered). 2축 merge N 확보 어려움 | supervisor 통합단계 또는 N 누적 후 |
| **M_eff 통합 FDR 보정** | G-F §3 | naive m=105 과대(pbr/per·mom 강상관). 산업은 naive+M_eff_signal(3.0) 박제 | supervisor 통합단계(M.7 분담) |
| **삼성/SK 각각 제외 LOO** | 2차리서치 Q5 + Hou-Xue-Zhang 2020 | momentum reversal 대형주 의존 점검 미실시(cap-weighted IC -0.092 로 부분점검됨) | 005930/000660 각각 drop 후 재IC |
| EV-EBITDA (cyclical primary_metric) | frame archetype | DART BS 부채/현금 계정 미수집. primary_metric 인데 미산출 | DART 부채총계+현금성자산 추가 fetch |
| family-neutralized IC (FF5/KR-factor) | frame §M5 | 산업 = unconditional 까지. region-matched neutralize = 통합단계(M.7) | 통합 supervisor |
| partial_corr_ratio | capsule robustness | RegimeGlasso conditioning = 통합단계 | 통합 단계 |
| IC term-structure 단조성 | frame §M.12 누락축 | premium이면 horizon 단조, artifact면 들쭉 — 명시 체크 미박제(데이터는 단조 관찰됨) | horizon sweep 표에 단조성 verdict 1줄 |

## ❌ 미채택 / proxy 대체

| 후보 | 사유 |
|---|---|
| per_z (전 horizon) | ★PER cross-sectional 전 horizon IC -0.024~-0.046, p_NW>0.10 **전부 비유의** = peak-EPS trap(사이클 정점 EPS 高→PER 低 왜곡). cyclical 정의 지지(auto 동형). E/P 대체 권고. |
| customer-supplier momentum (SOXX/NVDA lagged) | ★REJECTED as alpha — 전 lag(0-3) 비유의(p 0.32~0.94). 한국 반도체=글로벌 cycle **contemporaneous** 동조(corr>0.7)지 forward 예측력 부재(§D falsifier 작동). 동조성분=RegimeGlasso Ω 흡수. |
| dollar β (USDKRW 수출주 가설 H1) | β -1.68, t -1.26 **비유의**(CI 넓음). round-1 H1(USDKRW 강세→메모리 outperform) = 약/비유의. ★단 36셀 KRW regime 축에서 conditional 재검 의무(unconditional 약 ≠ conditional 약). |
| oil/VIX/rate β | 전부 비유의 (t<1.2). |
| sector-rotation business-cycle clock | 학술 myth(Molchanov 2024). 모멘텀 rotation 만 tentative. |
| TSMC capex yoy / HBM 이벤트 ledger (round-1 S7/S9) | N=20-30 / N=4-6 = INSUFFICIENT. 탐색적 only. |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)

| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| cs_mom_6m_reversal | BY 미생존 = 다중검정 후 비유의. 방향만 robust. live 에서 reversal 지속? | e-CUSUM 부호반전 모니터(reject_signal). 2nd cyclical down 까지 보류 |
| cs_pbr_z_24m | 24M eff_indep≈2.5 degenerate. t=-4.23 overlap inflation. 진짜 강신호인가 universe artifact 인가 | 3M/6M PBR 재배치(eff_N 큼) + breadth-adj IR + size-orthogonal 점검 후 magnitude 확정 |
| credit β -0.190 | US HY OAS proxy(KR HY 부재), n=35 small-n tentative | KR 회사채 spread(금투협/한신평) 확보 후 재측정 |
| KRW(dollar) unconditional 약 | conditional(KRW regime split)에서도 약한가? round-1 H1 수출주 가설 | ★측정완료 = KRW_weak regime서 신호 증폭(family_2 t=-2.95), unconditional 약은 conditional 발현. |

## 🔄 flip-register (regime-conditional sign flip — ★pristine OOS 게이트, 현 vintage 확정 금지)

> team-lead 주의3 (2026-06-05): regime별 부호반전 cell = 흥미롭지만 in-sample only → flip-register 박제 + **차기 vintage pristine OOS 게이트**(현 vintage 확정 금지). 미국 CYC-3/DEF-2-dollar 패턴 동일. ⛔ flip을 신호로 채택 금지(OOS 전).

| flip cell | uncond → conditional 부호 | n / wc_p / status | 해석 (가설) | OOS 게이트 |
|---|---|---|---|---|
| mom_6 [KRW_strong] | 음(-0.029) → **양(+0.059)** | n=10 / wc_p=0.19 / INSUFFICIENT | 원화강세(수출 둔화) regime서 momentum continuation? | n<12 = 차기 vintage 2026+ 누적 후 |
| mom_6 [flow_strong_buy] | 음 → 양(+0.007) | n=18 / wc_p=0.87 / underpowered | 외국인 강매수서 momentum 소멸(passive 지배, theory M3) | OOS 누적 |
| mom_12_1 [KRW_strong] | 음 → 양(+0.033) | n=10 / INSUFFICIENT | 동상 (KRW_strong momentum 반전) | n<12 누적 |
| rev_1m [KRW_strong] | 음 → 양(+0.035) | n=10 / INSUFFICIENT | KRW_strong서 reversal 약화/반전 | n<12 누적 |
| mom_6 [Reflation] | 음 → 양(+0.029) | n=20 / wc_p=0.42 / underpowered | 확장국면 momentum continuation? | OOS 누적 |

★flip-register 원칙: 전부 n<24 (INSUFFICIENT/underpowered) = ⛔현 vintage 확정 금지. 차기 vintage(2026년 이후 신규 데이터) pristine OOS 에서 부호·유의 재현 시만 신호 승격. 현재 = "관찰 등록"만.

## 📌 자산화 enum 분류

| enum | 후보 | 목적 |
|---|---|---|
| rule | (없음 — BY 생존 PBR 24M 도 degenerate hedge 로 rule 승격 보류) | 검증된 정량 규칙 |
| memory | "반도체 momentum=음(reversal) = cyclical peak 판별. battery(양)와 부호 반대" | 다음 cycle 자문 prior + archetype 판별 규칙 |
| memory | "PBR 24M IC t=-4.23 은 eff_indep≈2.5 overlap inflation. breadth-adj IR 로는 -1.52 = mom_6 와 유사 약~중" | 24M_value degenerate 재발 방지 (§M.12 anchor) |
| observe-only | cs_mom_6m_reversal / cs_pbr_z_24m | BY 미생존·degenerate → N 누적 + 2nd cycle 후 promotion |
| evt | (G-B 재자문 미발동 — BY 생존 0 AND 최강 raw_p>2×thresh 조건 점검 필요) | promotion-log ERROR 후보 |
| pointer | "conditional IC 36셀 = 이번 dispatch 본체, 선행 누락. measure.py 확장 1순위" | 다음 세션 SSOT 정독 우선순위 |

## ⚠️ G-B 재자문 트리거 점검 (dispatch §G-B)

- 조건 = BY 생존 0/m **AND** 최강 raw_p > 2×thresh.
- 현황: momentum family BY 생존 0/16, 최강 raw_p=0.00498. BY rank1 thresh=0.00185 → 2×thresh=0.00370. **0.00498 > 0.00370 = 트리거 조건 충족 가능성**.
- ★단 valuation family 에서 pbr_z_24M BY 생존(m=8) = "BY 생존 0" 조건은 family 단위. momentum family 만 보면 트리거, 전체(valuation 포함) 보면 생존 1.
- → S2 conditional IC 확장 후 family 정의 확정하고 G-B 판정 (현재 = 보류, team-lead 판단 요청 대상).
