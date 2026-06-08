---
tags: [type/candidate-ledger, domain/equity-us, sector/soxx_semi, purpose/easy-review]
date: 2026-06-08
purpose: SOXX(미국 반도체) 자문·이론에서 거론된 지표 후보 전체 + 채택예정/이연/미채택/falsifier + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
source_artifacts: round-1.md(H1~H5, 2026-06-08) + theory-notes.md(R1 학술 ground) + 기존 us_cyclical(prior 흡수)
status: ★R3 conditional 측정 완료 — FREEZE 철회, value/low_vol(BAB) 살아남(TENTATIVE). R4 = FDR+DFII10 재fetch+audit.
---

# SOXX(미국 반도체) 지표 후보 원장 (R3 conditional 측정 후)

> ★범위 = soxx_semi capsule 한정 (미국 섹터 granular 파일럿 1번).
> ★verdict 라벨 = small-n rule (CONFIRMED/PARTIAL/TENTATIVE/INSUFFICIENT/REJECTED).
> ★핵심 한 줄: 미국 반도체 within-sector value-selection(ρ) = (D) 부분 정당. ★R3 unconditional 단일 horizon freeze 는
> horizon 누락 오판 → conditional×y_60d×OOS 로 **value(+0.104) + low_vol/BAB(−0.118) 살아남**(TENTATIVE). quality 무신호.
> 한국과 차이 = KRW_weak 이식불가 → 미국 = nominal금리×credit regime. ★sub-industry 이질성 = 측정 1급 오염.
> ★자문 통설 2건 반증: Novy-Marx value+quality 결합강화(quality 희석) + momentum 미국 작동(OOS 부호반전).

## 📊 R3+R4 측정 verdict (★R4 보정 후 확정, validation-conditional.md §5-bis)

| 지표 | uncond y_60d | NW-HAC 보정 | BY-FDR | AI episode | ★최종 verdict |
|---|---|---|---|---|---|
| **value** | +0.104 (wc_p 0) | ★y20 t=3.24/y60 t=2.73 유의 | ★생존 | pre-AI(rate_low p=0.003) robust | ★**PARTIAL_CONFIRMED**(uncond, 생존편향 상한) |
| **low_vol(BAB)** | −0.118 (wc_p 0) | ★y20 t=−3.11/y60 t=−2.83 유의 | ★생존 | pre-AI 방향유지 | ★**PARTIAL_CONFIRMED**(uncond, 생존편향 상한) |
| conditional 증폭(family-2) | — | ★block-cluster t=1.3~1.4 붕괴 | — | rate_high=AI 의존 | ★**격하**(day-cluster t 부풀림 artifact) |
| momentum 12-1 | 약 | t=1.11 비유의 | 미생존 | — | ★REJECTED (OOS 부호반전) |
| rev_1m | −0.060 | y60 t=−2.52 | 생존 | — | conditional/약(block-cluster t=2.07 유일 잔존) |
| quality(ROIC) | 무 | 비유의 | 미생존 | — | ★REJECTED(무신호) = 결합 희석 원인 |
| value+quality 결합 | +0.030 | — | — | — | ★REJECTED(Novy-Marx 통설 반증) |

## 🚫 코드화 불가 / null result (★R6 3관문 확정 — 사용자 "코드화 못 가면 더 봐")

| 지표 | family | ★최종 verdict | 근거 (R6 G1~G4, validation-r6-g1/g2.json) |
|---|---|---|---|
| **value** (저PBR/저EV-EBITDA z) | value | ★**코드화 불가 / NVDA·AVGO 2-name position** (factor 미입증) | G1 lag PASS(non-overlap y60 t=2.11, block60 CI 0배제 = artifact 아님) BUT ★G2 breadth FAIL: 광의 33종(중소형 21 추가) 확장 시 IC 0.109→**0.024**(t=0.36 소멸) + leave-NVDA·AVGO retention(broad)=**−0.257**(부호반전). G3 생존편향 data-gate. = ★value premium은 대형주 2-name(NVDA·AVGO)에만, 중소형엔 부재 |

> ★value = 코드화 가능 systematic factor **아님**(2-name position). ⛔§방향보존: "value 무효" 단정 **아님** = 현 측정 틀
> (대형주 12종 / 광의 33종 EW)서 코드화 factor 신호 아닌 **범위한정**. 대형주 2-name엔 존재(position). ★사용자 "breadth
> 확장하면 살아난다" 가설 = 데이터 반박(중소형 추가 시 소멸). ★승격 잔여 = CRSP 생존편향-free + 딥밸류 소형(XSD보다 광의)
> data unblock 후 재측정. 그 전 ⛔ ledger/yaml 채택 금지(null result).

## ❌ 측정했으나 미달 / KILL (R3~R5 forward-IC 박제, 정직)

| 지표 | family | predicted_sign | 측정 결과 | verdict |
|---|---|---|---|---|
| **low_vol / BAB** | low_vol | 음(저β→fwd+) | ★raw IC=−0.118 = **anti-BAB**(고변동 outperform=BAB 반대) + pre-AI t=−1.33 + 직교(beta·mom) t=1.71 | ★**REJECTED-as-constructed** (KILL) — AI 고베타를 저변동으로 misspec 포장. R4 "신규 발견" = over-claim 정정 |
| quality (ROIC) | quality | 양 | uncond NW-HAC t=0.78 / 전 regime·horizon 비유의 / BY 미생존 | ★REJECTED(무신호) = value+quality 결합 희석 원인 |
| momentum 12-1 | momentum | 양 (한국 reversal 반대 가설) | uncond NW-HAC t=1.11 / OOS 부호반전 / BY 미생존 / family-2 block-cluster t=1.38 | ★REJECTED (미국 momentum도 한국 reversal도 미입증) |
| value+quality 결합 | value+quality | 음(결합 강화 가설) | IC +0.030 < MDE 0.107 (value 0.068 대비 희석) | ★REJECTED — Novy-Marx "결합 강화" 통설 반증(quality 무신호) |
| rev_1m (단기반전) | reversal | 음 | uncond y60 NW-HAC t=−2.52 / family-2 credit_high block-cluster t=2.07 | conditional/약 — y60 장기 reversal만 |

## 🧪 신규 신호 후보 (★측정 의무 = 이연 금지, R3 forward-IC 박제)

| 지표 | family | predicted_sign | 학술 (환각검증) | ★주의 |
|---|---|---|---|---|
| asset growth (Assets YoY) | asset_growth | **음** | Cooper-Gulen-Schill (2008) J.Finance ✅ | capital cycle. ★EDGAR assets 12종 ✅ 재사용 |
| R&D intensity (R&D/market-equity) | rnd | ★**양**(R2 정정, 음→양) | Chan-Lakonishok-Sougiannis (2001) JF 56(6) ✅실존 | ★시장 과소평가설(underreaction). ⛔ EDGAR R&D concept 부재=**data-gate**. R&D/Sales↔R&D/market-eq 정의차 R3 |
| capex intensity (Capex/Assets) | asset_growth | **음** | Cooper-Gulen-Schill 하위 ✅ | ★메모리/IDM 상위 쏠림 = style bias |
| momentum 12-1 | momentum | **양**(★한국 reversal 과 반대 가설) | Jegadeesh-Titman (1993) ✅ | ★부호 검정 = pilot 핵심 falsifier (음=reversal 유의면 기각) |
| low-vol / BAB | low_vol | **음**(저β→fwd+) | Frazzini-Pedersen (2014) JFE ✅ | 섹터 내 TXN/MCHP vs NVDA/AMD |

## ⏳ data-gate (현 데이터 측정 불가 / fetch 필요 — deferral 아님)

| 후보 | 출처 | 상태 | unblock |
|---|---|---|---|
| ★**R&D intensity** | EDGAR | ⛔ **R&D concept 부재** (EDGAR parquet 13 concept 中 R&D 없음) | `ResearchAndDevelopmentExpense` 별도 fetch OR 측정 보류 |
| EV-EBITDA (cyclical primary 보조) | EDGAR ✅ 재사용 | ✅ op_income+dep_amort+lt_debt+st_debt+cash 존재 | dep_amort 0종(ADI/TXN/QCOM) = EBIT proxy fallback |
| GP·Revenue·margin | EDGAR ✅ | △ QCOM gross_profit=0 / revenues 부족(ADI/KLAC/LRCX/MU<25) | fallback 태그(Revenues−cogs) + 부분측정 hedge |
| ★생존편향 보정 (delisted/M&A 종목) | CRSP / SOXX-ICE historical | ⛔ ★현 12종=현 holdings + prices 2015~ + fetch 시도 실패(yfinance=현재만, CRSP 유료) | CRSP delisting OR SOXX/ICE PIT membership = ★CONFIRMED 승격 조건(I축 hard-fail PARTIAL) |
| ★DFII10 실질금리 (regime 재측정) | FRED DFII10 | ⛔ ★sandbox 네트워크 timeout(fredgraph/stooq/data page 실패) = data-gate | network 복구 시 fetch → nominal(현 rate10y) → 실질 regime 재해석 |
| ★EW-semi universe | 사전등록 ✅ **SOXX/ICE(~30) 결정** | XSD 미채택. 현 raw 12종 측정 → 30종 확장 미완 | SOXX/ICE historical constituent fetch (자기일관, 생존편향 동시 해소) |

## ❌ 미채택 / drop (R1 실증으로 제거)

| 후보 | 사유 |
|---|---|
| **book-to-bill (κ)** | ★drop 확정 — 주가가 지표 선행(coincident-to-lagging) + SEMI bookings 2016-12 공개중단 + billings 2022 무료단절. 데이터 사망 |
| ~~FRED TWNEXPCESEMIT / KORXTOTLSEMISME / SINI~~ | ⛔ **환각 (404 날조)** — Gemini 제시, 실존 안 함. collector_plan 제거 |
| WSTS billings (κ) | 명백한 lagging (실제 매출 집계, 주가 3~6M 후행) + PIT ~2M 지연 |
| hyperscaler capex guidance (κ lead) | guidance = 주가 coincident, 실집행 = lagging. leading 아님 |
| dollar β (단독 신호) | Bruno-Shin (2015) EM/sovereign → US large-cap 도달 약. us_cyclical β=−0.228 t=−1.02 비유의. 2차 필터만 |

## 🔬 후속 재검증 falsifier (채택했으나 조건부 — CONFIRMED 승격 조건)

| 지표 | 현 tier | 미해결 의문 | unblock (PARTIAL_CONFIRMED → CONFIRMED 승격) 조건 |
|---|---|---|---|
| value | PARTIAL_CONFIRMED | ★생존편향 I축 PARTIAL(현 holdings) = magnitude 신뢰 제한 | SOXX/ICE historical membership + delisted 보강 → 생존편향-free 재측정서 IC 유지 |
| low_vol/BAB | PARTIAL_CONFIRMED | 동상 + OOS wc_p 0.10 경계 | 생존편향 보강 + OOS 누적(2026+ pristine) |
| value rate-extreme conditional | 격하(TENTATIVE) | ★rate_high 증폭 = AI episode 의존(2023-26) | ★DFII10 실질금리 재측정(nominal→실질) + 차기 vintage OOS서 conditional 재현 |
| ~~decomposition γ~~ | — | R3 unconditional γ null 이었으나 = horizon 누락 측정 = 무효 | conditional 측정서 value/low_vol 발현 = freeze 철회로 대체 |

## 🔄 flip-register (regime-conditional sign flip — ★pristine OOS 게이트, 현 vintage 확정 금지)

> ⛔ 한국 전례 (team-lead 주의): regime flip = in-sample only → pristine OOS 게이트 전 신호 채택 금지.

| flip cell | uncond → conditional | n / 보정 후 status | 해석 | OOS 게이트 |
|---|---|---|---|---|
| value [rate_mid] | 양(+0.068) → **소멸(−0.004)** | n=953d / wc_p 0.917 | rate 중간국면 value 소멸(U자 골) | 차기 vintage 재현 확인 |
| mom_12_1 [IS→OOS] | 음(IS −0.012) → **양(OOS +0.080)** | family-2 block-cluster t=1.38 비유의 | AI 시기 momentum 반전(passive 지배?) | OOS 누적, 현 격하 |
| value [rate_high] | 양 증폭(+0.105) but ★AI episode | n=833d(거의 AI 시기) | AI 붐 금리상승기 value 리프라이싱 | ★DFII10 실질 + 차기 vintage pristine |

★flip-register 원칙: conditional 증폭 = overlapping 보정 후 붕괴(block-cluster) = ⛔현 vintage 확정 금지. 차기 vintage
(2026+ 신규) pristine OOS 부호·유의 재현 시만 conditional 승격. 현재 = "관찰 등록"만.

## 📌 자산화 enum 분류 (R1 = pointer 중심)

| enum | 후보 | 목적 |
|---|---|---|
| pointer | "★E축 환각: FRED id 3건 날조(TWNEXPCESEMIT/KORXTOTLSEMISME/SINI). collector_plan 박제 전 실존검증 의무" | R2 fetch 안전장치 |
| pointer | "★sub-industry 이질성(팹리스/메모리/장비/아날로그) = Capex·R&D style-bias. R3 sub-industry-neutral z 1순위 점검" | R3 측정 설계 |
| memory(후보) | "미국 반도체 κ(book-to-bill·수출 lead) = coincident → 한국과 달리 timing 약. value-selection(ρ) 만 엣지 가설" | 다음 미국 섹터(XLE 등) prior |
| observe-only | momentum 12-1 부호 (양 가설 vs 한국 reversal) | R3 부호 검정 = archetype 판별 |
| evt(후보) | 미검증 인용 4건(Lettau-Wachter/Chan-Lakonishok-Sougiannis/Asness-Porter-Stevens/Cohen-Polk-Vuolteenaho) | R2 cross-verify 전 박제 금지 |
