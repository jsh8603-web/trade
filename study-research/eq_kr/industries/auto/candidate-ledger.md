---
tags: [type/candidate-ledger, domain/equity, sector/auto, purpose/easy-review]
date: 2026-06-05
purpose: 자문·이론·실측에서 거론된 자동차 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
source_artifacts: theory-notes.md(S1, 2026-06-05) + validation-conditional/fundamentals-cycle/critique/merged-fdr-v3.json(S2, 2026-06-05) + 기존 v3 측정(2026-06-03) + frame v3 §M.12
---

# automobile(자동차) 지표 후보 원장

> ★범위 = 자동차 capsule 한정 (12산업 독립 ledger). conditional IC surface(dispatch 본체) + 기존 v3 횡단면 흡수.
> ★verdict 라벨 = small-n rule (CONFIRMED/PARTIAL/TENTATIVE/INSUFFICIENT/REJECTED).
> ★핵심 한 줄: 자동차 = cyclical(volume cycle). 가격 momentum = **OOS flip 무효**(반도체보다 약) / ★진짜 신호 = PBR value(y_60d OOS robust) + capex_ratio(asset growth, 신규 발견). PER = peak-EPS trap 무신호.

## ✅ 채택 (yaml 등록 + 검증 통과)

| 지표 | family | tier | 근거 (source·n·검증) |
|---|---|---|---|
| cs_pbr_z (y_60d) | value | PARTIAL CONFIRMED (OOS robust, tier=**structural_prior_high_confidence**, magnitude hedge) | PBR cross-sectional z → y_60d forward IC=-0.108, uncond IS=-0.108/OOS=-0.117 ★OOS 부호+magnitude 유지. Slowdown regime. ★size 통제 후 독립(Fama-MacBeth t=-2.67, size t=-0.38 비유의). ★[remediation] eff-N 보정(AR1=0.494, eff-N=34.2) t=-3.72→-2.40(여전 유의). ★단 universe 17종 = magnitude 과대(방향+권역만). ⛔validated alpha 단정 보류. source=validation-conditional-v3.json:pbr_z + validation-critique/neff-label-v3.json |
| ★**cs_capex_ratio** (유형자산/총자산) | investment(asset growth) | PARTIAL CONFIRMED (OOS robust, tier=**structural_prior_high_confidence**, ★자동차 신규 진짜 신호) | ★유형자산/총자산 → forward IC y_60d=-0.103 wc_p=**0.0015**. walk-forward IS=-0.044→OOS=**-0.172** ★OOS 강화. ★통합 단일 FDR m=168 survivors=5 中 capex 3 cell 생존(★G-C: LOO 17종 전부 음 + PIT-safe + size 독립 3중). multivariate t=-3.38. prior 음(Cooper-Gulen-Schill 2008) 정합. ★[remediation] eff-N 보정(AR1=0.426, eff-N=39.7) y_60d t=-3.61→-2.52(여전 유의) + survivors wc_p floor-censored(magnitude 비교 금지). ⛔validated alpha 단정 보류. source=validation-fundamentals-cycle-v3.json:capex_ratio + validation-neff-label-v3.json |
| ★**conditional IC surface** (regime별) | dispatch 본체 | 측정완료 | ★S2 신규(measure_conditional.py, 2026-06-05). "어느 국면에 어느 지표" = 가격신호 전 regime OOS flip / PBR Slowdown·flow_strong_buy서 강 / capex 전 regime robust. source=validation-conditional-v3.json + walk_forward_oos |
| ★**walk-forward OOS** (IS2019-22/OOS2023-26) | 검증축 | 측정완료 | ★team-lead 의무. 58 cell IS/OOS split. 가격신호 cell 대부분 FLIP(in-sample artifact) / PBR y_60d·capex = OOS robust. source=validation-conditional-v3.json:walk_forward_oos |
| ★**size-orthogonal 검정** (Fama-MacBeth) | 비판검토 | 측정완료 | ★Q6 기각: PBR·capex 모두 size 통제 후 독립. ★단 size factor 자체도 유의(t=-2.2~-2.5) = 자동차 small-cap effect 공존 정직 명시. source=validation-critique-v3.json |
| ★**외국인flow regime** (ECOS 28d z) | regime 축 | 측정완료 | ★시장레벨 flow regime = ECOS 802Y001/0030000 일별로 측정(반도체 재사용). flow_strong_buy regime서 PBR value 강(theory M3 risk-on 펀더멘털 자금 정합). |

## 🧪 신규 cycle 지표 측정완료 (★이연 금지 = 지금 측정, verdict 박제)

> 사용자 박제 "이연 금지" → DART 분기 재구성(measure_fundamentals_cycle.py → validation-fundamentals-cycle-v3.json). 결과 정직 박제.

| 지표 | prior 부호 | 측정결과 (y_20d/y_60d) | walk-forward OOS | verdict |
|---|---|---|---|---|
| ★**capex_ratio** (유형/총자산) | 음 | y_60d IC=-0.103 wc_p=**0.0015** / y_20d -0.075 wc_p=0.0125 | IS-0.044→OOS-0.172 ✅강화 | **PARTIAL CONFIRMED(OOS robust)** — ★자동차 진짜 신호. asset growth anomaly 정합 + 통합 FDR 생존 + size 독립 |
| **inv_ratio** (재고/총자산) | 음 | y_20d IC=-0.034 wc_p=0.290 / y_60d -0.051 | IS-0.025→OOS-0.045 ✅(y20) / y60 FLIP | **TENTATIVE DIRECTIONAL** — 부호 음(prior 정합) but 약·비유의. capex 대비 약 |
| **ppe_yoy** (유형 yoy) | 음 | y_20d IC=0.0003 비유의 | OOS flip | INSUFFICIENT (비유의. ★level capex_ratio 가 yoy 보다 강 = stock 변수 우위) |
| **inv_yoy** (재고 yoy) | 음 | y_20d IC=+0.016 (prior 반대) | OOS 부호유지(양) | INSUFFICIENT (비유의, prior 음과 반대) |
| **rnd_ratio** (무형/총자산) | 양 | y_20d IC=-0.015 비유의 | OOS flip | INSUFFICIENT (비유의, prior 양과 약하게 반대) |

★신규지표 종합: ★**capex_ratio = 자동차 진짜 신규 신호**(OOS 강화 + 통합 FDR 생존 + size 독립). 나머지(inv/ppe/rnd) = 약/비유의. ★반도체는 신규지표 BY 생존 0(ppe_yoy TENTATIVE만)이었으나 자동차는 capex_ratio 생존 = **산업별 다름**(자동차 = 자산집약 장치산업 = asset growth anomaly 강).

## ⏳ data-gate / 이연 (현 데이터 측정 불가 또는 후속 — deferral 아님)

| 후보 | 출처 | 상태 | unblock 조건 |
|---|---|---|---|
| **EV-EBITDA** (cyclical primary_metric) | frame archetype | ⏳DART EBITDA(영업이익+감가상각) 재구성 후속 | DART fnlttSinglAcntAll 영업이익+감가상각비 추가 fetch (현 데이터로 가능, ★PBR·capex 진짜신호 입증되어 우선순위 일부 완화) |
| **미국 신차 SAAR yoy** | theory-notes §6 + GS Autos 2023 | ⏳외부 fetch 후속 (종목 cs 아닌 산업 timing) | FRED TOTALSA fetch → regime conditioning 변수 (반도체 PPI 자리 = 자동차 SAAR) |
| **종목레벨 외국인 flow** (cs-signal) | theory-notes M3 + Grinblatt-Keloharju 2000 | ★**DATA-GATE**(deferral 아님) | KRX 종목별 외국인 net buy = 인증 차단(pykrx KeyError). 시장레벨 regime(ECOS)은 측정완료. unblock = KRX 인증 OR 증권사 API |
| **PIT universe 멤버십** (delisted/M&A) | frame I축 생존편향 | ⏳FDR 현재 스냅샷만 | KRX PIT 섹터분류 인증. ★자동차 = 쌍용차→KG모빌리티 구조조정 多 = 생존편향 우려 큼 |
| **인센티브·재고일수** (자동차 고유 cycle) | theory-notes §M5 + GS Autos | ⏳외부 데이터 (종목 cs 아님) | 딜러 인센티브/재고 = 산업 timing, 종목 cross-sectional 부적합 → regime 변수 후보 |
| **2축 merge conditional IC** (Macro×flow) | frame §M3 collapse | 36셀 full N≥24=0(단일축만 powered) | supervisor 통합단계 또는 N 누적 후 |
| **M_eff 통합 FDR 보정** | G-F §3 | naive m=168 과대(pbr/per·mom 강상관) | supervisor 통합단계(M.7 분담) |
| **삼성/SK 격 LOO** (자동차=현대/기아 drop) | frame robustness | 현대차/기아 각 제외 LOO 미실시 | 005380/000270 각 drop 후 재IC (PBR·capex 대형주 의존 점검) |

## ❌ 미채택 / proxy 대체

| 후보 | 사유 |
|---|---|
| cs_mom_6 / mom_12_1 / rev_1m / vol_60 (가격신호) | ★**REJECTED(OOS)** — unconditional 비유의 + conditional cell 거의 전부 walk-forward OOS 부호반전(in-sample artifact). 자동차 momentum/reversal 무효(volume cycle = 반도체 ASP cycle 보다 약). family_2 interaction(mom_12_1/vol_60 KRW_weak t=2.18/2.75) 유의하나 해당 cell OOS flip = 채택 보류(flip-register). |
| per_z (전 horizon) | ★PER 횡단면 IC≈0(uncond wc_p=1.00) = **peak-EPS trap**(정점 EPS↑→저PER 왜곡). cyclical 정의 지지(자동차=peak-EPS trap 대표산업). E/P·EV-EBITDA 대체 권고. |
| customer-supplier momentum (CARZ/SLX lagged) | ★REJECTED as alpha — CARZ contemporaneous 동조 유의(lag0 +0.22 p=0.043) but forward(lag1-3) 비유의 = 글로벌 자동차 수요 동조(forward 예측 부재). 동조성분 RegimeGlasso Ω 흡수. |
| dollar β (USDKRW 수출주) | unconditional β -0.084 비유의(CI 넓음). ★자동차 환율 희석(해외생산·헤징·경쟁통화 = 반도체보다 약 prior 정합). conditional KRW_weak 도 가격신호서 OOS flip = 환율 alpha 약. |
| oil/VIX/rate/credit β | 전부 비유의(t<1.6). 자동차 idiosyncratic(반도체 credit 강과 대조). |
| sector-rotation business-cycle clock | 학술 myth(Molchanov 2024). |
| inv_yoy / ppe_yoy / rnd_ratio | 비유의(위 신규지표 표). level capex_ratio 가 yoy 보다 강(stock 변수 우위). |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)

| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| cs_pbr_z (y_60d) | universe 17종 magnitude 과대(point -0.108 vs breadth-adj). 진짜 강신호인가 small-universe artifact 인가 | EV/EBITDA 보강 + 현대/기아 LOO + breadth-adj IR 확정 후 magnitude. OOS robust 는 확인됨(차기 vintage 재현) |
| ★cs_capex_ratio | ★size factor 공존(t=-2.23). capex 가 size 의 proxy 아닌가? multivariate서 독립(t=-3.38)이나 collinear 잔존 | 현대/기아 LOO + size-bucket 내 capex IC(대형주만/소형주만 분리) + 차기 vintage OOS 재현 |
| 가격신호 OOS flip | flip = small-sample 우연인가 진짜 무효인가 | 차기 vintage(2026+) pristine OOS 에서 flip 재현 시 무효 확정. 현 = REJECTED(OOS) |
| KRW_weak interaction (mom_12_1/vol_60) | interaction 유의(t=2.18/2.75)인데 해당 cell OOS flip = in-sample only | flip-register(차기 vintage pristine OOS 게이트). 현 vintage 확정 금지 |

## 🔄 flip-register (regime-conditional sign flip — ★pristine OOS 게이트, 현 vintage 확정 금지)

> regime별 부호반전 cell = 흥미롭지만 in-sample only → flip-register 박제 + 차기 vintage pristine OOS 게이트. ⛔flip을 신호로 채택 금지(OOS 전).

| flip cell | IS → OOS 부호 | n / status | 해석 (가설) | OOS 게이트 |
|---|---|---|---|---|
| mom_6 [KRW_weak] | 음(-0.098) → **양(+0.150)** | IS21/OOS13 / FLIP | KRW_weak서 momentum continuation? (theory M4 = 양 interaction 정합이나 OOS 불안정) | 차기 vintage 2026+ 재현 후 |
| rev_1m [KRW_weak] | 음(-0.121) → **양(+0.197)** | IS21/OOS13 / 극단 FLIP | KRW_weak서 reversal→momentum 극단 전환 = artifact 전형 | 채택 금지(OOS 전) |
| vol_60 [KRW_weak] | 양(+0.051) → 양(+0.281) | OK but magnitude 폭증 | low-vol → high-vol 선호 전환? magnitude 불안정 | OOS 누적 후 |
| mom_12_1 [KRW_weak] interaction | t=+2.18 유의(양) | family_2 | KRW_weak momentum continuation (반도체 reversal 증폭과 반대) | OOS flip 동반 = 보류 |

★flip-register 원칙: 전부 OOS flip 또는 magnitude 불안정 = ⛔현 vintage 확정 금지. 차기 vintage pristine OOS 재현 시만 승격. 현재 = "관찰 등록"만.

## 📌 자산화 enum 분류

| enum | 후보 | 목적 |
|---|---|---|
| rule | (없음 — PBR·capex tier=structural_prior_high_confidence 이나 ⛔validated alpha 단정 보류 = rule 승격 보류, observe-only. 차기 vintage pristine OOS 후 승격) | 검증된 정량 규칙 |
| memory | "자동차 가격 momentum=OOS flip 무효(반도체보다 약). volume cycle = ASP cycle 보다 momentum 약" | 다음 cycle 자문 prior + archetype 판별 |
| memory | "★자동차 = capex_ratio(asset growth) 진짜 신호 발견(G-C audit 충실 PASS). 자산집약 장치산업 = asset growth anomaly 강(반도체는 신규지표 무신호). ★자산집약 산업 일반화 후보(화학/정유/조선/철강 검증 대상)" | 산업별 신규지표 차등 prior |
| memory | "PBR/capex point estimate magnitude = universe 17종 = small-universe inflation. ★y_60d 중첩 자기상관(AR1≈0.43-0.49) → eff-N 보정 시 t -3.6→-2.5(여전 유의지만 t 박제 시 eff-N 병기 의무). 방향만, breadth-adj 권역" | small-universe + overlap inflation 재발 방지 |
| memory | "★wild-cluster bootstrap survivors wc_p floor(1/(B+1)=0.0005)에 censored 시 산업 간 magnitude 비교 금지(생존 여부만 비교). B↑로 floor 낮춰야 상대강도 구분" | FDR floor-censoring 재발 방지 |
| observe-only | cs_pbr_z(y_60d) / cs_capex_ratio | tier=structural_prior_high_confidence(G-C). OOS robust + 3중검증이나 17종 협소 + validated alpha 보류 → N 누적 + 차기 vintage 재현 후 rule 승격 |
| evt | (G-B 재자문 미발동 — 통합 FDR survivors=5 > 0 = "신호 약함" 조건 미충족. ★단 survivors floor-censored caveat 박제) | promotion-log ERROR 후보 |
| pointer | "conditional IC surface(measure_conditional.py) + capex(measure_fundamentals_cycle.py) = 이번 dispatch 본체. EV-EBITDA·SAAR fetch = 다음 우선" | 다음 세션 SSOT 정독 우선순위 |

## ⚠️ G-B 재자문 트리거 점검 (dispatch §G-B)

- 조건 = BY 생존 0/m **AND** 최강 raw_p > 2×thresh.
- 현황: ★통합 단일 FDR m=168 **survivors=5**(pbr_z 2 + capex_ratio 3) = "BY 생존 0" 조건 **미충족** → G-B 재자문 **미발동**.
- = 자동차는 신호 약함 아님(PBR value + capex asset growth 가 보정 후에도 생존). 반도체(survivors=0)와 결정적 차이.
- → G-B skip 정당(자문 거치기 전 "약함" 단정 아님 = 생존 5 데이터 근거).
