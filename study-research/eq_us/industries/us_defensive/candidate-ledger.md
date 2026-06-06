---
tags: [type/candidate-ledger, domain/equity, sector/us_defensive, purpose/easy-review]
date: 2026-06-03
purpose: 자문·이론·실측에서 거론된 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에. ★S1 리서치(Gemini 2-Phase Pro+Flash + citation 환각검증) 기반. ★측정 결과(§2)는 측정 후 갱신.
---

# us_defensive 지표 후보 원장

> ★S1 framing: defensive(asset_stable) = 안정 현금흐름·배당·bond-proxy 듀레이션. cyclical 의 peak-EPS trap 과 **반대** = PER value 정상 작동 **가설**(단 PBR noise-trap·FCF/EV 우월·crowding 경고). 기존 rev_1m/vol_60/real_rate = 일부 — 누락 = quality/payout-yield/earnings-stability. 출처 = theory-notes.md + research-log.md.

## ✅ 채택 후보 (S1 발굴 → §2 측정 대상, 검증 전)
| 지표 | family | 방향 | 근거 (source·환각검증·데이터) |
|---|---|---|---|
| **gross_profitability** (GP/Assets) | quality | 양 | ★BY 생존 1순위 예상(자문). Novy-Marx (2013) JFE 108(1) **CONFIRMED** + AFP (2019) RAS 24(1) QMJ **CONFIRMED**. defensive 고품질 universe 내 진짜 우수운영자 변별. EDGAR GrossProfit/COGS+Assets(가용성 측정 의무). crowding 경고(smart-beta) |
| **payout_yield** (div+repurchase−issuance / mktcap) | value/payout | 양 | ★defensive 핵심. Boudoukh-Michaely-Richardson-Roberts (2007) JF 62(2) **CONFIRMED**(payout>dividend 단독). ★crowding critical: 고yield=distress proxy(post-2010 ZIRP reach-for-yield). EDGAR PaymentsOfDividendsCommonStock/PaymentsForRepurchaseOfCommonStock/ProceedsFromIssuanceOfCommonStock |
| **dividend_yield** (div / mktcap) | value/payout | 양(?) | payout_yield 의 clean subset. ★sub-sector sign flip 경고(자문): staples/healthcare alpha vs utilities risk → universe-demean cancel → sector-neutral 필수 |
| **per_z / ep_z** (E/P earnings yield) | value | 음/양 | ★핵심 가설(cyclical 반대): defensive EPS 안정 → PER value 정상? Basu (1977) JF 32(3) **CONFIRMED** + Lakonishok-Shleifer-Vishny (1994) JF 49(5). ★E/P 권장(negative earnings monotone). 한국 consumer/telecom asset_stable value premium 방향 동형 |
| **ev_ebitda / fcf_yield** | value | 음/양 | ★자문 = FCF/EV > E/P > PER(CAPEX-heavy 보정). EV/EBITDA = PBR 대체. EDGAR OpIncome+D&A+debt+cash |
| **pbr_z** | value | 음(?) | ★기존(재작업 대상). 현 24M IC +0.062 **역방향**(value trap) = ★문헌적 설명 = buyback book value 왜곡 noise-trap(자문). sector-neutral 후 within-sector value 회복 가능성 검증 |
| **earnings_stability** (CV NI) | quality | 양(약 prior) | asset_stable 직결. ★단 Ball-Gerakos-Linnainmaa-Nikolaev (2015) JFE 117(2) **CORRECTED**(="Deflating Profitability" NOT "Defensive Equity JFE 119"): low earnings-vol = tail-risk 감소이지 평균수익 상승 아님 → 약 prior |
| vol_60 | low_volatility | 음 | 기존. 현 12M IC +0.076(저변동성 프리미엄, NW 0포함 TENTATIVE). Frazzini-Pedersen (2014) JFE 111(1) BAB **CONFIRMED** + Baker-Bradley-Wurgler (2011) FAJ 67(1). ★beta residualize 권고(rate-sensitivity 혼입 회피) |
| rev_1m | reversal | 음 | 기존. 현 3M IC −0.045 t−2.70 유의(BY 미생존). Jegadeesh (1990) JF 45(3) **CONFIRMED**. ★BY 생존 2순위 예상(small panel 독립) |

## ⏳ 이연 (식별됐으나 미투입)
| 후보 | 출처 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|
| **accruals (Sloan)** | Sloan (1996) AR 71(3) | NI − CFO 필요 = CFO concept(NetCashProvidedByUsedInOperatingActivities) 추가 fetch | EDGAR concept 확장 fetch (collect.py) |
| **rate-duration β (cross-sec)** | Gormsen-Lazarus (2023) JF | ★unconditional cross-sectional IC ≈0(risk factor, regime-dependent sign) = cross-sectional alpha 부적합 | family_3 attribution + regime tilt 으로만 (cross-sectional alpha 아님) |
| **defensive-specific KPI** | Phase1 #9 / Lev-Gu (2016) [tentative] | utilities ROE/rate-base, healthcare R&D/patent, staples brand/ARPU = ★XBRL 미표준화(NLP/유료) | 유료 데이터 또는 10-K NLP 추출 |
| **mom_6 / mom_12_1** | 기존 | ★asset_stable momentum 무효 예상(한국 consumer/telecom 동형) | 측정해서 무효 확인(falsifier) |
| **QMJ growth/safety 성분** | AFP (2019) RAS | profitability 외 성분 = composite 복잡. safety = universe 에 내재(저베타) | gross_profitability 측정 후 보조 |
| **HY OAS regime split (직접)** | Phase1 #8 | FRED 2023-05~ 37mo만 = INSUFFICIENT(us_cyclical 동일 제약) | Baa-Aaa(1919~) proxy 대체 |

## ❌ 미채택 / proxy 대체
| 후보 | 사유 |
|---|---|
| HY OAS regime (BAMLH0A0HYM2 직접) | ★FRED 가용 2023-05~ 37mo만 → **Baa-Aaa(1919~) proxy 대체**(family_2, ρ>0.85) |
| PBR primary | ★buyback book value 왜곡 noise-trap(자문) → EV/EBITDA·FCF/EV 우월. 단 비교용 측정은 유지 |
| PER (raw P/E) | negative earnings undefined → **E/P(earnings yield) monotone 대체** |
| rate-duration cross-sectional alpha | unconditional IC ≈0 = risk factor → family_3/regime tilt 만 |

## 🔬 후속 재검증 falsifier (★측정 후 결과 반영)
| 가설/지표 | 측정 결과 | unblock (validated 승격) 조건 |
|---|---|---|
| ★PER/E-P value 정상 작동 (cyclical 반대) | ★**가설 기각 → anti-value(역방향)**. E/P IC −0.056(저PER→저forward = value premium 역방향). cyclical PBR value 작동과 반대. ep_yield = TENTATIVE_DIRECTIONAL regime-conditional | (anti-value 방향) ep_yield BY 생존 + quality 통제 후 잔존 + cross-market 재현 |
| gross_profitability 양 | ★**기각 → 무신호**. ≈0(staples +0.059/util +0.036/health −0.081 불일치). partial-coverage(COGS fallback: utilities 5종·comm 3종 일부) | sub-universe IC CI 0배제 + BY 생존 |
| payout_yield 양 | ★**기각 → anti-yield QE artifact**. regime FLIP(QE −0.122→2022+ +0.054). rejected_provisional | 부활 트리거(Fed<2%/VIX>25/HY>300bp) regime-conditional 재측정 |
| pbr_z 역방향 | ★**확인 → 약/역방향 + sector-neutral 무회복**. sector_z_decomposition uni/secN/sectorLevel 모두 약·동부호 = sector-mixing 주범 아님, buyback noise-trap | (회복 없음) collector_plan: buyback-adjusted book |
| earnings_stability 양 | ★**기각 → 위험보상**. earnings_cv IC 양(불안정→고forward, Ball et al. tail-risk≠평균수익) | (방향 반대) unconditional alpha 부재 |
| ★ep_yield anti-value (신규 falsifier) | ★TENTATIVE_DIRECTIONAL — regime consist True + quality 독립 + LOO/leave-sub-sector 안정 but BY 미생존 | BY 생존 + FF5+QMJ neutralize 후 잔존 + cross-market 재현(미국 외 시장) |

## ★측정 결과 반영 (§2 sector-neutral 2026-06-03 + G-B 자체검증 + G-B 자문 수렴, ★family_1 BY 0/48)
| 신호 | verdict (G-B 자문 수렴) | family_1 BY | 근거 (regime split 핵심) |
|---|---|---|---|
| **ep_yield (E/P)** | ★**TENTATIVE_DIRECTIONAL (regime-conditional)** | ❌ 미생존 | IC 음 일관(12M −0.056 t−2.2). ★regime consist **True**(QE −0.061→2022+ −0.040 유지) + quality partial 잔존(−0.051 t−1.55) + LOO 안정 + leave-sub-sector(ex_health −0.062 비의존). = anti-value(value premium 역방향). cyclical PBR value 작동과 ★반대. ⛔unconditional 금지+quality 미통제 한계 |
| **payout_yield** | ★**rejected (B″ 후 강화, NO_INTERACTION)** | ❌ | ★B″ STEP 1~3: split QE −0.122 t−2.86 → ΔReal_rate continuous interaction β0.028 t0.43 **fixed-b 비유의**(wild-cluster p0.68) = split 이 garden-of-forking-paths + size-invalid artifact 였음 입증. armed-pending 미진입. 부활 트리거 Fed<2%/VIX>25/HY>300bp(observe-only reserve) |
| **dividend_yield** | ★**rejected (B″ 후 강화)** | ❌ | payout 과 동일 NO_INTERACTION(split FLIP = size-invalid artifact) |
| **residual_mom** (STEP 4 add) | ★**TENTATIVE_DIRECTIONAL** | ❌ | 12M IC+0.039 t2.55 fixed-b size-valid 개별 유의(price-based, sector·beta 직교). 단 6M/3M 약 + 단일 FDR family BY 미생존. observe-only |
| **idio_vol** (STEP 4 add) | ★INSUFFICIENT (무신호) | ❌ | 전 horizon t0.46~0.73 비유의. 저변동성 프리미엄 약 |
| **net_issuance** (breadth sweep) | ★★**PARTIAL_CONFIRMED (defensive 첫 FDR 생존, incremental)** | ✅ 생존(3M/6M/12M) | ★(issuance−repurchase)/mktcap IC+0.082 t4.40(3M)/+0.082 t3.31(12M) = fixed-b size-valid + 단일 FDR family(27test M_eff19) BY 생존(raw_p 3e-05). ★**직교화(advisory §1) = INCREMENTAL**: ⊥ep_yield 잔존(12M IC+0.084 t3.71 size-valid) + ⊥payout 잔존(12M IC+0.055 t2.41 size-valid) = buyback-aversion specific 채널(anti-value cluster 너머). ★부호 양=anti-issuance(Pontiff-Woodgate 음 ★반대=defensive 자사주 가치파괴, sleeve 내 ep anti-value 와 부호 정합). regime QE+0.087→2022+ +0.067 ★유지(payout FLIP 과 다름)+LOO stable+sub-sector 3/4 양. ★hedge: 부호 vs 문헌 반대 / payout corr −0.53 부분중복(직교 후 잔존) / comm_mature 반대 small-n / OOS·cross-market 미검증 |
| **amihud** (breadth sweep) | ★TENTATIVE (개별 약) | ❌ | 12M IC+0.078 t1.98(개별 경계, FDR 미생존). 비유동성 프리미엄 약 |
| high_52w/op_profitability/roe/accruals (breadth sweep) | ★INSUFFICIENT (무신호) | ❌ | high_52w t1.04 / op_prof t−0.59 / roe t−0.92 / accruals t−1.00 전부 비유의 |
| per_z | ★INSUFFICIENT (unstable) | ❌ | IC 양(저PER→저forward 역방향). regime flip(QE +0.051→2022+ −0.013) |
| pbr_z | ★INSUFFICIENT | ❌ | sector_z_decomposition uni+0.021/secN+0.016/sectorLevel+0.009 = ★sector-mixing 주범 아님(us_cyclical 무회복 대조), buyback noise-trap 부분지지 |
| ev_ebitda/fcf_yield | ★INSUFFICIENT | ❌ | ev 비유의(t<0.8). fcf 약 음(value 역방향 일관) |
| earnings_cv | ★INSUFFICIENT (위험보상) | ❌ | IC 양(불안정→고forward, Ball et al. tail-risk≠평균수익 + 위험보상). regime consist True(약) |
| gross_prof | ★INSUFFICIENT (무신호) | ❌ | ≈0 (staples +0.059/util +0.036/health −0.081 약·불일치). ★partial-coverage(COGS fallback: utilities 5종 203obs·comm 3종 111obs + staples/healthcare 주력, NaN tri-state) |
| **real_rate β** (family_3) | ★**QUALIFIED (sleeve 본질)** | n/a | β−0.066 t−6.78 robust = 듀레이션 bond-proxy. supervisor regime overlay 몫(cross-sectional 아님) |
| vol_60 | 약 양 | ❌ | 저변동성 프리미엄 약(NW 비유의) |
| rev_1m | 약 음 | ❌ | sector-neutral 후 약화(기존 −0.045 → −0.012) |
| **sleeve 종합** | ★**PARTIAL_CONFIRMED** (breadth sweep 후 변동) | net_issuance ✅ 1 생존 | ★net_issuance 단일 FDR family BY 생존 + incremental(직교 후 잔존) = ★cross-sectional alpha 존재(이전 INSUFFICIENT 격상). 단 net_issuance 1개 + 부호 문헌 반대 + payout 중복 hedge + comm small-n + OOS 미검 = PARTIAL(CONFIRMED 강력 아님). ep/residual_mom TENTATIVE 동반. real_rate 듀레이션 QUALIFIED. |

## 📌 자산화 enum 분류
| enum | 후보 | 목적 |
|---|---|---|
| rule | ★**net_issuance** (PARTIAL_CONFIRMED, 단일 FDR family BY 생존 + incremental size-valid) = anti-issuance/buyback-aversion(순발행→고forward, 부호 양). ★PARTIAL hedge(부호 문헌 반대+payout 중복+comm small-n+OOS 미검) → supervisor 보수 weight. real_rate 듀레이션 β = family_3 driver(macro overlay) | 검증된 정량 규칙(supervisor 통합 큐) |
| memory | ★sector-neutral 효과 sleeve별 상이(us_cyclical 회복 vs us_defensive 무회복) / ★defensive = anti-value(cyclical PBR value 반대, cross-market 시장 의존) / payout=reach-for-yield QE artifact(regime FLIP) / ★**split size-invalid**(small-n regime split NW asymptotic t = over-rejection, fixed-b CV/wild-cluster 필수, continuous interaction 우월) / rate-duration unconditional IC≈0 risk factor / Ball et al. earnings-stability=tail-risk≠평균수익 / PBR buyback noise-trap | 다음 cycle·sleeve 자문 prior |
| observe-only | ★**net_issuance OOS·cross-market**(PARTIAL_CONFIRMED 채택했으나 부호 문헌 반대 = OOS holdout + 미국 외 시장 재현 검증 후 CONFIRMED 승격 판정) / ★**ep_yield anti-value**(TENTATIVE_DIRECTIONAL, fixed-b size-valid but FDR 미생존 = FF5+QMJ neutralize 후 재평가) / ★**residual_mom 12M**(STEP 4 add, t2.55 fixed-b 유의 but 6M/3M 약+FDR 미생존) / ★**payout regime interaction**(부활 트리거 Fed<2%/VIX>25/HY>300bp 충족 시 재측정) | N 누적/OOS/regime 후 promotion |
| evt | ★**defensive anti-value/anti-yield = G-B 트리거 + 자문 수렴**(BY 0/48, sector-neutral 무회복 = us_cyclical 방법결함 ★아님 = 신호 본질. G-B 자문 = sleeve INSUFFICIENT) + ★**payout split→interaction = size-invalid artifact 입증(B″ STEP 1~3)**: regime split QE −0.122 t−2.86 "유의" 가 ΔReal_rate continuous interaction + fixed-b CV(Kiefer-Vogelsang) size-valid 전환 시 β0.028 t0.43 비유의 = ★small-block NW asymptotic over-rejection(size-invalid) + garden-of-forking-paths artifact = 자문 R3 Claude 경고 실증. ★**split 검정 일반 위험**(small-n regime split 의 NW asymptotic t = size-invalid, fixed-b/wild-cluster 필수) + ★**ep anti-value fixed-b size-valid 개별 유의**(power 우려 부분 반박, artifact 아님 but FDR 미생존 TENTATIVE) + ★**sleeve별 sector-neutral 효과 상이**(us_cyclical 결함교정 ↔ us_defensive 무회복) + ★**cross-market 불일치**(미국 anti-value ↔ 한국 value premium 정방향) | promotion-log ERROR/K 후보(자문 정정 + ★split size-invalid 방법 자산) |
| pointer | theory-notes.md(S1) / research-log.md / us_cyclical measure.py(sector-neutral 정식 + sector_z_decomposition 양식자산) / 15axis-audit.md | 다음 sleeve 정독 우선순위 |

## ★S1 자문 raw → 산출 매핑 (consult-raw-output-mapping-checklist)
S1 리서치 raw 후보 enumerate → ledger 매핑:
- Phase1 signals raw 후보 9 → 채택 8(gross_prof/payout_yield/dividend_yield/per-ep/ev_ebitda-fcf/pbr/earnings_stability/vol_60/rev_1m 일부 묶음) + 이연 4(accruals/rate-duration/defensive-KPI/mom) + 미채택 4(HY직접/PBR-primary/raw-PER/rate-duration-alpha)
- Phase2 deep-dive raw → EDGAR concept 확정(payout 3 tag) + sector-neutral 필수 + sub-sector sign flip 경고 + BY 생존 우선순위(quality>reversal>low-vol>value) + E/P·FCF/EV>PER
- citecheck 16 → CONFIRMED 14 + CORRECTED 2(Ball "Deflating Profitability" JFE 117(2) / Greenwood-Vayanos reach-for-yield 출처 약화)
- ★누락 0건 확인: Phase1 9 signals + Phase2 6 측정축 전부 위 표에 매핑(채택/이연/미채택 사유 박제).

## ★G-B 자문 raw → 산출 매핑 (consult-raw-output-mapping-checklist, team-lead 실행 자문)
G-B 자문(gemini-web+claude-web 병렬, .consult-us-defensive-R1) raw verdict 후보 enumerate → 산출 매핑:
- **sleeve INSUFFICIENT** → summary.yaml verdict_label=INSUFFICIENT + 15axis G-A.6 박제
- **ep_yield TENTATIVE_DIRECTIONAL regime-conditional** → indicators_passed.cs_ep_yield(hedge_note: quality축 미통제+healthcare 기여+small-n) + weight_rule(regime-conditional, unconditional 금지)
- **payout/dividend rejected_provisional + 부활트리거(Fed<2%/VIX>25/HY>300bp)** → indicators_passed.cs_payout_yield(rejected_provisional) + confidence_hooks(PROHIBITED + 부활 트리거) + candidate-ledger observe-only
- **per_z/earnings_cv INSUFFICIENT** → valuation_cross_sectional.indicators verdict
- **duration/credit overlay QUALIFIED** → cross.common_factor_exposure.real_rate(QUALIFIED sleeve 본질) + family_3
- **claude 지적 healthcare 지배** → leave-sub-sector 추가검증(ex_health −0.062 비의존 = 기각) → 15axis G-A.4 + summary robustness 박제
- ★cross-market 함의(미국 anti-value ≠ 한국 value premium) → summary.yaml cross_market_implication 블록(G-E 입력)
- ★누락 0건 확인: G-B verdict 6항목 + claude 지적 1 + cross-market 1 전부 산출 매핑(skip 0).
