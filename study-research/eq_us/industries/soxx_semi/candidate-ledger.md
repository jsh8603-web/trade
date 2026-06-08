---
tags: [type/candidate-ledger, domain/equity-us, sector/soxx_semi, purpose/easy-review]
date: 2026-06-08
purpose: SOXX(미국 반도체) 자문·이론에서 거론된 지표 후보 전체 + 채택예정/이연/미채택/falsifier + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
source_artifacts: round-1.md(H1~H5, 2026-06-08) + theory-notes.md(R1 학술 ground) + 기존 us_cyclical(prior 흡수)
status: ★R1 단계 = 후보 enumerate + predicted_sign 사전고정 (실측 IC 전). 6분류 verdict 는 R3 실측 후 확정.
---

# SOXX(미국 반도체) 지표 후보 원장 (R1 — 실측 전)

> ★범위 = soxx_semi capsule 한정 (미국 섹터 granular 파일럿 1번). round-1 H1~H5 + theory-notes 학술 ground 흡수.
> ★verdict 라벨 = small-n rule (CONFIRMED/PARTIAL/TENTATIVE/INSUFFICIENT/REJECTED). ★R1 = 아직 측정 전 = 모두 "검증 대기".
> ★핵심 한 줄: 미국 반도체 = within-sector **value-selection(ρ)** primary, rotation/timing(κ) 회의(~30%, falsify 대상).
> 한국과 차이 = KRW_weak regime 이식불가 → 미국 = 실질금리×credit 2축. ★sub-industry 이질성 = 측정 1급 오염.

## 🎯 채택 예정 (primary, R3 측정 → 통과 시 ✅채택)

| 지표 | family | predicted_sign | 근거 (학술) | R3 게이트 |
|---|---|---|---|---|
| value (저PBR/저EV-EBITDA z, sector-neutral) | value | **음**(cheap→fwd+) | Fama-French (1992/93). 한국 pbr_z IC −0.114 대응 | MDE\|IC\|>0.107 + CI 0배제 + OOS 부호유지 + BY |
| gross profitability (GP/Assets) | quality | **양** | Novy-Marx (2013) JFE. value 와 음상관=분산 | 동상 + GP concept 가용 sub-universe |
| sales/price (1/PSR) | value | **양** | Barbee-Mukherji-Raines (1996) FAJ. peak-EPS 면역 | 동상 + Revenue 태그 fallback |
| margin level+momentum | quality | **양** | Novy-Marx + QMJ. leading-edge vs commoditized | 동상 |
| quality (ROIC, low leverage) | quality | **양** | Asness-Frazzini-Pedersen (2019) QMJ | 동상 |

## 🧪 신규 신호 후보 (★측정 의무 = 이연 금지, R3 forward-IC 박제)

| 지표 | family | predicted_sign | 학술 (환각검증) | ★주의 |
|---|---|---|---|---|
| asset growth (Assets YoY) | asset_growth | **음** | Cooper-Gulen-Schill (2008) J.Finance ✅ | capital cycle. us_cyclical 전 universe 가용 |
| R&D intensity (R&D/Sales) | rnd | **음** | Chan-Lakonishok-Sougiannis (2001) J.Finance ⚠️R2확인 | ★팹리스 상위 쏠림 = style bias 위험 |
| capex intensity (Capex/Assets) | asset_growth | **음** | Cooper-Gulen-Schill 하위 ✅ | ★메모리/IDM 상위 쏠림 = style bias |
| momentum 12-1 | momentum | **양**(★한국 reversal 과 반대 가설) | Jegadeesh-Titman (1993) ✅ | ★부호 검정 = pilot 핵심 falsifier (음=reversal 유의면 기각) |
| low-vol / BAB | low_vol | **음**(저β→fwd+) | Frazzini-Pedersen (2014) JFE ✅ | 섹터 내 TXN/MCHP vs NVDA/AMD |

## ⏳ data-gate (현 데이터 측정 불가 / fetch 필요 — deferral 아님)

| 후보 | 출처 | 상태 | unblock |
|---|---|---|---|
| EV-EBITDA (cyclical primary 보조) | EDGAR | ⏳ 부채/현금 계정 추가 fetch | OperatingIncome+D&A+debt+cash (us_cyclical 일부 가용) |
| GP·Revenue (gross profit / sales) | EDGAR concept | △ semi 부분 가용 | fallback 태그 (Revenues − CostOfGoodsAndServicesSold) |
| 생존편향 보정 (delisted/M&A 종목) | CRSP / S&P semi historical | ★현 12종 = 현 holdings only | CRSP delisting return OR S&P semi PIT membership (I축 hard-fail) |
| EW-semi universe (SOXX/ICE vs S&P semi select/XSD) | 사전등록 | ⏳ 미확정 | 횡단 자기일관 universe 결정 |
| regime 32셀 (실질금리×credit×dollar) | macro.parquet | ✅ 컬럼 보유 | N≥24 collapse 사전점검 (한국 36셀 full 0개 전례) |

## ❌ 미채택 / drop (R1 실증으로 제거)

| 후보 | 사유 |
|---|---|
| **book-to-bill (κ)** | ★drop 확정 — 주가가 지표 선행(coincident-to-lagging) + SEMI bookings 2016-12 공개중단 + billings 2022 무료단절. 데이터 사망 |
| ~~FRED TWNEXPCESEMIT / KORXTOTLSEMISME / SINI~~ | ⛔ **환각 (404 날조)** — Gemini 제시, 실존 안 함. collector_plan 제거 |
| WSTS billings (κ) | 명백한 lagging (실제 매출 집계, 주가 3~6M 후행) + PIT ~2M 지연 |
| hyperscaler capex guidance (κ lead) | guidance = 주가 coincident, 실집행 = lagging. leading 아님 |
| dollar β (단독 신호) | Bruno-Shin (2015) EM/sovereign → US large-cap 도달 약. us_cyclical β=−0.228 t=−1.02 비유의. 2차 필터만 |

## 🔬 후속 재검증 falsifier (R1 가설 → R3 반증조건)

| 가설/지표 | predicted_sign | ★반증조건 (사전등록) |
|---|---|---|
| H1 value-selection | 음(cheap→fwd+) | CI 0 포함 or wrong-sign 유의 → 기각 → (C) freeze 발동 |
| H2 κ (수출 lagged→forward) | 양 | predictive t<2(fixed-b) or eff_N<벽 or lead 자체 부재(coincident) → κ 폐기 |
| H3 decomposition γ | within 비-null | γ null → (C) freeze (granular 폐기) |
| momentum 12-1 | 양 | ★한국처럼 음(reversal) 유의 → predicted 반대 = 기각 (부호 검정) |
| 모든 신호 공통 | — | MDE\|IC\|<0.107 dead-on-arrival / OOS 부호반전 / CI 0 포함 |

## 🔄 flip-register (R3 이후 — regime-conditional sign flip 관찰, 현재 공란)

> ★R1 = 측정 전이라 flip 후보 없음. R3 regime 32셀 측정 후 uncond→conditional 부호반전 cell 을 여기 등록.
> ⛔ 한국 전례 (team-lead 주의): regime flip = in-sample only → pristine OOS 게이트 전 신호 채택 금지.

## 📌 자산화 enum 분류 (R1 = pointer 중심)

| enum | 후보 | 목적 |
|---|---|---|
| pointer | "★E축 환각: FRED id 3건 날조(TWNEXPCESEMIT/KORXTOTLSEMISME/SINI). collector_plan 박제 전 실존검증 의무" | R2 fetch 안전장치 |
| pointer | "★sub-industry 이질성(팹리스/메모리/장비/아날로그) = Capex·R&D style-bias. R3 sub-industry-neutral z 1순위 점검" | R3 측정 설계 |
| memory(후보) | "미국 반도체 κ(book-to-bill·수출 lead) = coincident → 한국과 달리 timing 약. value-selection(ρ) 만 엣지 가설" | 다음 미국 섹터(XLE 등) prior |
| observe-only | momentum 12-1 부호 (양 가설 vs 한국 reversal) | R3 부호 검정 = archetype 판별 |
| evt(후보) | 미검증 인용 4건(Lettau-Wachter/Chan-Lakonishok-Sougiannis/Asness-Porter-Stevens/Cohen-Polk-Vuolteenaho) | R2 cross-verify 전 박제 금지 |
