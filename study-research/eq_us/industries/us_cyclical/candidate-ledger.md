---
tags: [type/candidate-ledger, domain/equity, sector/us_cyclical, purpose/easy-review]
date: 2026-06-03
purpose: 자문·이론·실측에서 거론된 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에. ★S1 리서치(Gemini 2-Phase + citation 환각검증 + EDGAR concept 실측) 기반.
---

# us_cyclical 지표 후보 원장

> ★S1 framing: cyclical = peak-EPS trap (사이클 정점 EPS高→P/E低 함정). peak-EPS-robust 신호(balance-sheet/sales/forward-expectation)가 핵심. 기존 per/pbr/vol/mom = 일부. 출처 = theory-notes.md + research-log.md.

## ✅ 채택 후보 (S1 발굴 → §2 측정 대상, 검증 전)
| 지표 | family | 방향 | 근거 (source·환각검증·데이터) |
|---|---|---|---|
| **asset_growth** (Assets YoY) | investment | 음 | ★최우선 신규. Cooper-Gulen-Schill (2008) JF 63(4) **CONFIRMED**. capex boom-bust = peak-EPS 유발 cycle 직접 포착, balance-sheet 면역. EDGAR `Assets` = ★전 60종 가용(실측). decay 경고(McLean-Pontiff ~26%, 2015~ crowding) → 약 prior 가능 |
| **gross_profitability** (GP/Assets) | quality | 양 | Novy-Marx (2013) JFE 108(1) **CONFIRMED**. cyclical COGS 변동 큰데 GP 안정 = 고품질 변별. ★EDGAR GrossProfit/CostOfRevenue = semi·industrials만 가용, materials/energy/fin=0 → 부분 sub-universe + fallback 태그 |
| **sales_yield** (Revenues/Price) | value | 양 | ★peak-EPS-robust value 대표. Barbee-Mukherji-Raines (1996) FAJ **CORRECTED**(Phase1 "2008" 오류). 매출=earnings보다 사이클 안정→earnings trap 면역. 자문: Sales/Price > EV/Sales (cash/debt noise 회피). Revenues 태그 일부 fallback 필요 |
| per_z / pbr_z | value | 음 | 기존(재작업 대상). per_z 24M IC −0.119 t−2.76 block-boot 유의 but ★BY 미생존+24M degenerate→TENTATIVE. 3M t−2.47 primary. ★Sales/Price 가 peak-EPS-robust 대체 가설 |
| vol_60 | volatility | 양 | 기존. IC +0.151(고베타 보상, US large-cap). BY 미생존 |
| mom_6 / mom_12_1 | momentum | 양 | 기존. mom_6 3M t+2.40 유의 but BY 미생존. ★cyclical turning point crash 위험(2009/2022) |

## ⏳ 이연 (식별됐으나 미투입)
| 후보 | 출처 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|
| **ev_ebitda** | direction R1 보조 / Phase1 | OperatingIncomeLoss+D&A+debt+cash 가용(실측 일부) but cash/debt 변동 noise(자문: Sales/Price 우월) | sales_yield 측정 후 보조 추가 측정 |
| **accruals (Sloan)** | Phase1 / Sloan(1996) | NOA=(Assets−Cash)−(Liab−Debt) 분해 = 현 EDGAR 3-concept 부족(current/noncurrent liab·debt 세분 미수집) | EDGAR concept 확장 fetch |
| **ERB (earnings revision breadth)** | direction R1 alpha 1순위 / Stickel | ★free API-accessible 데이터 부재(IBES/FactSet/Refinitiv 유료). EDGAR=actuals only, expectation 없음 | 유료 IBES 또는 Yahoo/SeekingAlpha scraping(fragile) |
| **credit-spread β (cross-sec)** | Phase1 / Friewald-Wagner-Zechner(2014) | β_credit rolling 추정 noise + ΔSpread↔R_mkt 다중공선성(orthogonalize 필요) + HY 36mo 제약 | Baa-Aaa 장기로 추정 가능, 별 측정 |
| **BAB (betting-against-beta)** | direction / Frazzini-Pedersen(2014) JFE | beta sort = 보조 risk factor. cyclical universe 내 저베타 변별 가능하나 우선순위 낮 | core 측정 후 보조 |
| **PMI/ISM (NAPM)** | Phase1 / Koenig(2002) | ★시계열 timing(cross-sectional 아님). leading. sleeve cross-sectional 측정 직접 부적합 | supervisor regime feature(보고만) |
| **INDPRO/ISRATIO/TCUTIL** | Phase1 / Chen-Roll-Ross(1986) | ★시계열 coincident conditioner. cross-sectional 직접 부적합 | supervisor regime |
| **oil β (DCOILWTICO)** | Phase1 | energy·materials = 직접 β but sector-concentrated. broader=timing | cross β 보고(energy/materials sub) |
| **operating leverage (DOL)** | Phase1 / Novy-Marx(2011) | ★sign state-dependent(recovery 양/peak 음) = risk char, 단독 alpha 아님. macro interaction 필요 | ISM interaction term 측정 시 |

## ❌ 미채택 / proxy 대체
| 후보 | 사유 |
|---|---|
| HY OAS regime split (BAMLH0A0HYM2 직접) | ★FRED 가용 2023-05~ 37mo만(실측) = regime split INSUFFICIENT(eq_us_defensive H3 ERROR). → **Baa-Aaa(1919~) proxy 대체** (ρ>0.85, IG가 HY 3~6M 선행, 자문 winner) |
| EV/Sales (M&A valuation) | equity factor selection 엔 Sales/Price 우월(자문). cash/debt 변동 noise. → sales_yield 대체 |
| RevenueFromContractWithCustomerExcludingAssessedTax | EDGAR 404(실측, CAT). → `Revenues` 표준 concept 사용 |
| LongTermDebt (단일) | EDGAR 404(실측). → LongTermDebtNoncurrent + ShortTermDebt 조합 |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)
| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| asset_growth 음 | 2015~ decay/crowding 으로 alpha 소멸 가능 | 우리 표본 IC CI 0배제 + LOO sector robust + family_1 BY 생존 |
| sales_yield 양 (peak-EPS robust) | per_z 보다 우월한가? revenue 태그 커버리지 충분한가 | Sales/Price IC > per_z IC + 커버리지 ≥35종 |
| gross_profitability 양 | semi·industrials 한정 sub-universe = N 협소 → small-n hedge | sub-universe N≥24 cell + 방향 robust |
| credit regime (Baa-Aaa) | HY OAS 와 정합? cyclical rotation 실재? | Baa-Aaa regime split IC 차 CI 0배제 + 36mo HY 와 부호 일치 |

## ★측정 결과 반영 (2026-06-03, sector-neutral z)
| 신호 | verdict | family_1 BY | 근거 |
|---|---|---|---|
| **cs_pbr_z** | ★CONFIRMED | ✅ 생존(3M/6M/12M/24M + nondegen 3개) | IC −0.117 t−3.19. OOS+within 0.91+LOO+leave-year+long-only net +10%. 한국 PBR○ 정합 |
| **cs_ev_ebitda** | ★CONFIRMED | ✅ 생존(3M/6M/12M/24M) | IC −0.110 t−3.39. financials 개념차 제외. peak-EPS-robust |
| cs_per_z | TENTATIVE | ❌ 미생존 | 약(peak-EPS trap). 3M t−2.14. 한국 PER✗ 정합 |
| cs_sales_yield | TENTATIVE | ❌ | 24M 양 t+2.02 but OOS 불안정. sub-sector 전5 양 일관 |
| asset_growth | ★REJECTED | ❌ | unconditional/secN 무신호 + OOS 부호반전 = 2015~ decay 확정(문헌·자문 예측) |
| mom/vol | 약 | ❌ | sector-neutral 후 비유의(universe-demean sector-level 인위신호 소거) |

## 📌 자산화 enum 분류
| enum | 후보 | 목적 |
|---|---|---|
| rule | ★cs_pbr_z(CONFIRMED, BY 생존) + cs_ev_ebitda(CONFIRMED) = peak-EPS-robust value sector-neutral | 검증된 정량 규칙(supervisor 통합 큐) |
| memory | ★sector-neutral z 필수(multi-sector sleeve, universe-demean 결함) / peak-EPS-robust = PBR/EV-EBITDA○ PER✗ / HY OAS 37mo→Baa-Aaa proxy / asset_growth 2015~ decay | 다음 cycle·sleeve 자문 prior |
| observe-only | sales_yield(sub-sector 양 일관 but OOS 불안정 N 누적) / Baa-Aaa regime(HY 직접 정합 미검) | N 누적 후 promotion |
| evt | ★**universe-demean → sector-neutral z 방법결함**(frame §M.7 계약 위반, BY 0→8 회복, mechanism=sector-level value trap) + ★**per_z coverage artifact**(shares 47→60 t−2.48→−1.16) | promotion-log ERROR 후보(방법 정정 자산) |
| pointer | theory-notes.md(S1) / research-log.md(★sector_z_decomposition mechanism) / measure.py(sector-neutral 정식 + 4수정) / 15axis-audit.md(G-A.5 mechanism 입증) | 다음 sleeve 정독 우선순위 |

## ★evt 자산 상세 (research-log + promotion-log ERROR 후보)
1. **방법결함 universe-demean → sector-neutral z**: 기존 measure.py cs_z = universe-wide demean. frame §M.7 line 267-269 "within-industry peer-relative sector-neutral z" 계약 위반. multi-sector sleeve(미국 5 sector)에서 sector mixing 으로 신호 희석 = family_1 BY 생존 0. → sector-neutral 전환 = BY 8 회복. ★mechanism = sector-level value trap(검증 b): within value 양수익(−0.117) + sector-level value 음(+0.140) → universe-demean 두 반대성분 mixing 희석. 단일산업(한국)은 byte-identical 무회귀. ★전 sleeve(defensive/mega_tech) 적용 의무.
2. **per_z coverage artifact**: shares concept 47/60종(dei:EntityCommonStockSharesOutstanding 13종 결측). 기존 per_z 24M "유의"(t−2.48) = 누락 13종 sub-universe artifact. 60종 보강 시 t−1.16 약화. → fundamentals coverage 검증 의무(dei 네임스페이스 fallback).

## ★S1 자문 raw → 산출 매핑 (consult-raw-output-mapping-checklist)
S1 리서치 raw 후보 enumerate → ledger 매핑:
- Phase1 factors raw 후보 13 → 채택 3(asset_growth/gross_prof/sales_yield) + 이연 6(ev_ebitda/accruals/ERB/BAB/DOL/credit-β) + 미채택 1(EV/Sales→Sales/Price) + 기존 3(per/pbr/B/M=pbr 대응)
- Phase1 macro raw 후보 6축 → regime conditioner 1(Baa-Aaa) + 보고 β 4(dollar/rate/vix/oil) + 시계열 이연 3(PMI/INDPRO/ISRATIO·TCUTIL)
- ★누락 0건 확인: factors 13 + macro 6축 전부 위 표에 매핑(채택/이연/미채택 사유 박제).
