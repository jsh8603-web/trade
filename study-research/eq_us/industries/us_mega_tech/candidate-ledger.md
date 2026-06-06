---
tags: [type/candidate-ledger, domain/equity, sector/us_mega_tech, purpose/easy-review]
date: 2026-06-03
purpose: 자문·이론·실측에서 거론된 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에. ★S1 리서치(WebSearch 7주제 + citation 환각검증) 기반. ★재작업 = 자문 R2 수정4(basket화) 반영.
---

# us_mega_tech 지표 후보 원장

> ★S1 framing: compounder = long-duration growth + quality. value premium **부재**(expensive_trap = 고PER 정상) = archetype 정의. ★측정 단위 = N=11 custom basket → cross-sectional rank-IC 통계력 약(Grinold breadth) → **basket-level time-series factor timing 우선 + cross-sectional small-basket hedge**(자문 R2 수정4). ⛔ sector-neutral z 비적용(단일 archetype, peer 부재). 출처 = theory-notes.md + research-log.md.

## ✅ 채택 후보 (S1 발굴 → §2 측정 대상, 검증 전)

### basket-level (★수정4 우선 — N=11 small-basket time-series timing)
| 지표 | family | 방향 | 근거 (source·환각검증·라우팅) |
|---|---|---|---|
| **real_rate β timing** | duration | 음 | ★최우선 신규(compounder 본질). Gormsen-Lazarus (2023) JF 78(3) 1393-1447 **CONFIRMED**. long-duration growth = value/profitability/투자/저위험 프리미엄의 반대편 = ★expensive_trap 학술 입증 + real-rate β 강. basket-level β + lead-lag. 기존 cross-v3 −0.030 비유의 = ★multivariate 재측정 의무(이론상 강해야) |
| **VIX β timing** | risk-on | 음 | 기존 측정 강(basket −0.008 t−2.5, mag7 t−4.0). ★고베타 risk-on. BAB 함의 = high-beta risk-adj underperform = ★alpha 아닌 risk overlay·timing feature. L축 1회 계상(supervisor) |
| **quality(low-beta) basket** | low_volatility | 양 | BAB Frazzini-Pedersen (2014) JFE 111 **CONFIRMED** + QMJ Asness-Frazzini-Pedersen. ★단 broad cross-section 전제 = N=11 cross-sec 약 → basket-level low-beta exposure timing 병행 |
| **momentum basket timing** + crash tail | momentum | 양 약 | Daniel-Moskowitz (2016) JFE 122 221-247 **CONFIRMED**(crash 좌측꼬리, panic state). growth persistence 약 양. ★concentration 좌측꼬리 증폭 = reflexivity 연동 |

### cross-sectional (★small-basket hedge — breadth-IR + 50~70% haircut, 단독 verdict 금지)
| 지표 | family | 방향 | 근거 (source·환각검증·데이터) |
|---|---|---|---|
| **vol_60** | low_volatility | 양 | 기존 dominant(IC +0.241 t3.10 breadth-IR 2.56). ★n=11 basket BY 미생존(small-basket). magnitude haircut 의무. quality(안정 mega-cap) |
| **mom_6 / mom_12_1** | momentum | 양 약 | 기존. mom_6 1M t1.56 비유의(growth persistence 약) |
| **per_z** | value | ≈0 (expected null) | ★expensive_trap 직접 검증. 기존 3/6/12M ≈0 = 고PER 정상 = archetype 지지. ★REJECT 아닌 expected null. Gormsen-Lazarus duration 설명 |
| **pbr_z** | value | 약 음 | 기존 12M −0.167 t−1.58 비유의. n=8 small-basket |
| **capex_z (H6)** | investment | ★부호 불확실 | Cooper-Gulen-Schill (2008) JF 63(4) **CONFIRMED**(asset growth top decile 6% vs bottom 26%) = 高 capex 음. ★단 compounder AI capex = productive growth 가능성 = 부호 데이터 판정. 기존 약 음 비유의 |

## ★B″ factor breadth 후보 전수 검토 (★2026-06-04, "다 봤다" 확인용 = 측정 안 한 것도 사유 박제)
> ★요점 = "안 쟀다" 아니라 ★"검토 후 구조적 void 판정". us_mega_tech = B″ STEP 0 재분류 = exposure/timing overlay = ★cross-sectional factor sleeve 아님(유효 cross-section n≈8 = factor 추정 통계적 void = 강제 시 spurious factor 제조). → 아래 breadth 후보 = 전부 ★측정 무의미(구조적 void) 또는 데이터게이트.

| breadth 후보 | family | 출처 | ★검토 결과 (void 사유 박제) |
|---|---|---|---|
| **F-score (Piotroski)** | quality | direction / Piotroski(2000) | ★B″ cross-sectional void(n≈8 spurious) + ★설계 mismatch = F-score는 **high-BM 부실주** 재무건전성 변별 설계 → mega-cap growth(저BM·고품질 균질)엔 dispersion 0. ⛔ 측정 안 함(exposure overlay sleeve) |
| **net-issuance (net stock issues)** | issuance | direction / Pontiff-Woodgate(2008) | ★B″ cross-sectional void(n≈8) + ★n=11 동질 buyback → dispersion 고갈 → IC degenerate(전부 자사주 매입 mega-cap). ⛔ 측정 안 함 |
| **operating-profitability (OP/equity)** | quality | Fama-French(2015) RMW | ★B″ cross-sectional void(n≈8 spurious factor). mega-cap 전부 고수익성 균질 = dispersion 낮음. ⛔ 측정 안 함(overlay sleeve) |
| **ROE** | quality | direction | ★B″ cross-sectional void(n≈8). OP 와 중복 + mega-cap 균질. ⛔ 측정 안 함 |
| **gross_profitability (GP/Assets)** | quality | Novy-Marx(2013) JFE | ★B″ cross-sectional void(n≈8) + 데이터게이트(EDGAR 4 concept만, GrossProfit/COGS 미수집). 둘 다 = ⛔ 측정 안 함 |
| **asset_growth (Assets YoY)** | investment | Cooper-Gulen-Schill(2008) | ★B″ cross-sectional void(n≈8) + capex_z 와 중복(investment anomaly). ⛔ 측정 안 함(capex 이미 diagnostic) |
| **SUE / PEAD (earnings surprise)** | momentum | Foster-Olsen-Shevlin(1984) | ★B″ cross-sectional void(n≈8) + 데이터게이트(EDGAR 분기 EPS SRW 필요, 8-K Item 2.02 furnish date anchor 미구현). compounder=peak-EPS 아님(cyclical 영역). ⛔ 측정 안 함 |
| **residual-momentum (12-1 orthog)** | momentum | Blitz(2011) / cyclical STEP 4 | ★B″ cross-sectional void(n≈8). mom_6/mom_12_1 이미 diagnostic(약 양 비유의). residual화해도 n≈8 void 동일. ⛔ 측정 안 함(cyclical breadth 후보, mega_tech 부적합) |
| **idiosyncratic-vol** | low_volatility | Ang-Hodrick-Xing-Zhang(2006) | ★B″ cross-sectional void(n≈8). vol_60(총변동성) 이미 diagnostic = idio-vol 중복 + n≈8 void. ⛔ 측정 안 함 |
| **52w-high / Amihud illiquidity** | momentum/liquidity | George-Hwang(2004) / Amihud(2002) | ★B″ cross-sectional void(n≈8) + ★mega-cap = Amihud illiquidity 무의미(전부 최고유동성, dispersion 0). ⛔ 측정 안 함 |
| **fwd EPS growth / ERB** | growth | direction R1 / Chan-Jegadeesh-Lakonishok(1996) | ★compounder primary 인데 ★데이터게이트(IBES/FactSet 유료 = free API 부재, EDGAR=actuals only). + B″ cross-sectional void(n≈8). ⛔ 측정 불가(데이터) + 무의미(void). proxy=forward-looking 아님 |
| **FF5+Mom+QMJ+BAB neutralize** | factor model | direction H12 / Ken French + AQR | ★concentration β 분리 = ★supervisor 통합 단계(L축, sleeve 몫 아님). mega_tech 자체 측정 대상 아님 |

★**전수 검토 결론**: us_mega_tech cross-sectional breadth 후보 11종 = ★전부 측정 안 함. 사유 = (A) B″ 구조적 void(유효 n≈8 = spurious factor 제조, 9종) + (B) 데이터게이트(F-score 일부/SUE/fwd EPS = 유료·concept 부재, 3종 중첩) + (C) mega-cap 균질성(F-score/net-issuance/OP/Amihud = dispersion 고갈). ★sleeve = exposure/timing overlay(basket-level real_rate/vix 노출 + reflexivity + regime-beta) = cross-sectional factor 적층 무의미. = ★"검토 후 구조적 void 판정"(안 잰 게 아님).

## ⏳ 이연 (식별됐으나 미투입)
| 후보 | 출처 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|---|
| **fwd EPS growth / ERB** | direction R1 alpha 1순위 / Chan-Jegadeesh-Lakonishok(1996) / Stickel(1991) | ★compounder primary 인데 IBES/FactSet/Refinitiv 유료 = free API 부재. EDGAR=actuals only(expectation 없음). fwd EPS proxy(net_income TTM YoY 외삽) 가능하나 forward-looking 아님 | 유료 IBES 또는 Yahoo/SeekingAlpha scraping(fragile). proxy 는 보조 측정 |
| **gross_profitability (GP/Assets)** | Novy-Marx(2013) JFE / us_cyclical 미러 | quality 신호. ★기존 EDGAR 4 concept만(equity/ni/shares/capex) — GrossProfit/COGS 미수집. EDGAR concept 확장 필요 | collect.py concept 확장 fetch(us_cyclical 12 concept 미러) |
| **FF5+Mom+QMJ+BAB neutralize** | direction H12 / Ken French + AQR | ★concentration β 분리(잔존 alpha 진위). 모든 alpha time-series 회귀 intercept NW t. = supervisor 통합 단계(L축) | supervisor 조립 단계 |
| **AI capex→Mag7 supply-chain lead-lag** | direction H6 / Cooper-Gulen-Schill | hyperscaler capex→반도체 momentum lead-lag = ★cross 구조(supervisor DY) | supervisor DY 단계. sleeve = capex intensity cross-sec(보조)만 |
| **asset_growth (Assets YoY)** | Cooper-Gulen-Schill(2008) | capex_z 와 중복(둘 다 investment anomaly). compounder = productive growth 가능 부호불확 | capex_z 측정 후 보조(중복 M_eff 흡수) |

## ❌ 미채택 / proxy 대체
| 후보 | 사유 |
|---|---|
| **sector-neutral z (us_cyclical pilot)** | ⛔ us_mega_tech 비적용 — 단일 archetype(compounder) basket, 11종 모두 mega-tech 그룹 = sub-sector demean 할 peer 구조 없음. us_cyclical = multi-sector(5 sector) 라 sector-neutral 필수였으나, mega_tech 는 universe-demean = sector-neutral 동치(별 sector 없음). 15axis G-A.5 사유 명시 |
| **cross-sectional rank-IC 단독 verdict** | ★N=11 = Grinold breadth 협소 = 통계력 약. 단독 verdict 금지(자문 R2 #4). basket-level + small-basket hedge 병기 |
| EV/EBITDA value | compounder = value premium 부재(expensive_trap). value metric 무신호 = 정상. 측정하되 verdict 강조 X |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)
| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| real_rate β (음, duration) | 기존 cross-v3 −0.030 비유의 = Gormsen 이론(강해야)과 불일치. 측정 부족인가 실제 약인가 | basket-level multivariate(level vs Δ) + lead-lag β CI 0배제 + us_defensive utilities(−0.213) 대비 |
| vol_60 (양, quality) | ★n=11 basket BY 미생존 = small-basket. magnitude literal 신뢰 불가 | basket-level low-beta timing 병행 유의 + breadth-IR 양 + leave-episode |
| per_z (≈0 expensive_trap) | 정말 무신호(archetype 정합)인가 측정 artifact 인가 | 재측정 IC CI 0 포함(무신호 확인) + duration 으로 설명 |
| capex_z (H6 부호 불확실) | over-investment 음 vs productive growth 양 어느 쪽 | cross-sec IC 부호 + CI + AI capex regime(2023~) split |

## ★측정 결과 반영 (2026-06-03 §2 basket화 → ★2026-06-04 B″ 3R STEP 0/5 재분류)
> ★B″ 재분류: sleeve_type = exposure_timing_overlay(verdict 생성 폐기). cross-sectional factor = DIAGNOSTIC ONLY(유효 n≈8 void). 보고 3종(exposure/concentration/regime-beta).

| 신호 | role/measurement | 결과 | 근거 |
|---|---|---|---|
| **basket_real_rate_beta** | ①exposure 한계기여 (basket-level) | ★EXPOSURE(노출≠alpha) | ★duration factor **노출** 강. β −0.154 단독/−0.210 multivariate(t−5.14). Gormsen-Lazarus(defensive 3배). robustness 전부. ⛔ 노출(contemp β)≠alpha(예측 ts_IC −0.191 약) = ★supervisor macro overlay 입력(sleeve weight 아님) |
| **basket_vix_beta** | ①exposure (basket-level) | ★risk overlay | β −0.0073 t−6.79 고베타 risk-on. alpha 아님(BAB) = de-risk throttle·L축 |
| **reflexivity (H9)** | ②concentration/crowding | 정점 아님 | intra-corr 0.355<0.70 + breadth +0.08 = cap-down 미발동. ★신호 아님 |
| **capex IC~VIX interaction** | ③regime-beta 안정성 (family_2b) | ★MIXED(post-AI 사망) | ★B″ fixed-b 재검정(2026-06-04): (전체 n=125) t_HAC +2.43>CV 2.19 + p_wild 0.044 = SURVIVE but pre-AI 무신호 희석 / ★(post-AI n=29 = 신호 −0.404 강한 구간) t_HAC +1.94<CV 2.86 + p_wild 0.234 = ★DIE(payout 동일 Kiefer-Vogelsang artifact). ⛔ timing 신호 자격 = post-AI size-valid 미통과 |
| **cs_lowvol (vol_60)** | ★DIAGNOSTIC ONLY (cross-sec) | 참고 지표 | IC +0.241 but ★유효 n≈8 = factor void → ★verdict/PASS-FAIL 폐기(B″ STEP 0, spurious factor 회피). weight 0 |
| **per_z** | ★DIAGNOSTIC (cross-sec) | 참고(expensive_trap) | ≈0 = 고PER 정상 archetype 지지 참고치. verdict 아님 |
| **capex_z (H6)** | ★DIAGNOSTIC (cross-sec) | 참고(underpowered) | post-AI −0.404(n=29 OOS 없음) = over-investment 가능성 참고치(미입증) |
| **pbr_z/mom** | ★DIAGNOSTIC (cross-sec) | 참고 | pbr 약 음 비유의 / mom growth persistence 약 |
| **spillover (CF lagged)** | DY 후보 (G-A.3, ★B″ STEP 5) | underpowered null | ★기존 k=0 +0.69=Cohen-Frazzini 오용(동조, tradeable 아님). CF 정합(고객 hyper_t→공급사 semi_{t+1}) lead 1-3m 비유의(−0.07~−0.09) + ★UNDERPOWERED(power 0.13, MDE\|ρ\|=0.238). 증거부재≠부재증거. semi↔hyperscaler 한정 |
| **F-score/net-issuance** | ★측정 폐기 (B″ STEP 0) | 미측정 | F-score=high-BM 부실주 설계 mismatch / net-issuance=n=11 동질 buyback dispersion 고갈 = mega-cap growth 부적합 |

## ★B″ STEP 2(⑦) capex×VIX interaction fixed-b size-valid 재검정 (2026-06-04)
> ★사용자 지적 = "특정 국면에서 산다던 지표들 frame 바꾸고 살았나" → capex×VIX(family_2b t+2.34)가 구 asymptotic HAC 그대로 = payout(split t−2.86→fixed-b 2.09 사망)과 동일 Kiefer-Vogelsang size-invalid 위험. `_b2_stats.py`(fixed_b_cv+wild_cluster_boot+effective_n) 재검정.

| 표본 | 구 t_HAC(maxlags) | effective_n | fixed-b CV(KV) | wild-cluster p | ★size-valid 판정 |
|---|---|---|---|---|---|
| capex_z **전체 n=125** | +2.43 (lag=5) | 33.1 | 2.19 | 0.044 | ★SURVIVE (t>CV + p_wild<0.05) — ★단 pre-AI 무신호 구간 섞인 희석 |
| capex_z **★post-AI n=29** (신호 −0.404 강한 구간) | +1.94 (lag=5) | 9.1 | ★2.86 (small-block inflation) | 0.234 | ★**DIE** (t 1.94<CV 2.86 + p_wild 0.234 비유의) = NW over-rejection artifact |

★**판정 = MIXED → post-AI 사망 = 신호 자격 미달**:
- capex 신호 자체는 ★post-AI(2023~)에서만 IC −0.404 로 강함(pre-AI +0.009 무). 그 ★의미있는 표본(n=29)에서 regime interaction 은 ★fixed-b size-valid 미통과(payout 동일 artifact).
- 전체 n=125 SURVIVE = pre-AI 무신호 구간(capex IC≈0)이 섞여 분산 안정화된 산물 = capex 의 ★실질 regime-conditional timing 효과 입증 못함.
- → ★"capex×VIX timing overlay 신호" 라벨 = ★post-AI(신호 구간) size-valid 미통과 = **diagnostic(미입증)** 으로 정정. (summary overlay_report 3 + 측정결과 표 정정 완료.)
- ★다른 mega_tech 신호: basket real_rate β t−5.14 = n=185 time-series exposure(small-block 아님 = 해당 약, fixed-b 영향 적음). reflexivity=risk overlay(검정 아님). = ★small-block interaction 류만 capex 해당.

## 📌 자산화 enum 분류
| enum | 후보 | 목적 |
|---|---|---|
| rule | ★basket_real_rate_beta(duration factor **노출**, ★supervisor RegimeGlasso/macro overlay 입력 — sleeve weight 아님) + VIX 고베타 risk-on 노출 = ★exposure overlay 보고(verdict 아님) | exposure overlay(supervisor 통합 입력) |
| memory | ★us_mega_tech = ★exposure/timing overlay(B″ STEP 0, 유효 n≈8 cross-sectional void = verdict 폐기) / compounder = expensive_trap(Gormsen-Lazarus duration) / ★노출(contemp β)≠alpha(예측) / ★CF spillover = lagged firm-pair(contemporaneous 오용) / sector-neutral 비적용(단일 archetype) / ERB 유료 gap | 다음 cycle·sleeve 자문 prior |
| observe-only | cs_lowvol(diagnostic 참고, 유효 n≈8 void) / capex_z post-AI −0.404(n=29 OOS 없음 underpowered) / ★spillover CF lagged(underpowered null, power 0.13 — N 누적 후 재검) | N 누적 후 재검(verdict 아님) |
| evt | ★**B″ STEP 0 = mega_tech cross-sectional factor sleeve → exposure overlay 재분류**(유효 n≈7 void = spurious factor 회피) / ★**STEP 5 = spillover +0.69 contemporaneous = Cohen-Frazzini 오용 → lagged firm-pair 재측정**(동조≠tradeable) / ★**자문 R2 #4 basket화**(Grinold breadth) | promotion-log ERROR 후보(방법 정정 자산) |
| pointer | theory-notes.md(S1) / research-log.md(★B″ STEP 0/5 측정결정) / measure.py(★sleeve_type overlay + CF lagged spillover + MDE) / 15axis-audit.md(G-A.5/A.6 + verdict 폐기) | 다음 sleeve 정독 우선순위 |

## ★S1 자문 raw → 산출 매핑 (consult-raw-output-mapping-checklist)
S1 리서치 raw 후보 enumerate → ledger 매핑 (누락 0건 확인):
- WebSearch 7주제 신호 후보 → 채택 basket-level 4(real_rate/VIX/quality/momentum) + 채택 cross-sec 5(vol_60/mom×2/per_z/pbr_z/capex_z) + 이연 5(ERB/gross_prof/FF5neut/supply-chain/asset_growth) + 미채택 3(sector-neutral/cross-sec단독/EV-EBITDA)
- direction H1~H12 매핑: H6(AI capex)=capex_z 채택 / H9(reflexivity)=risk overlay 채택 / H12(factor neut)=이연(supervisor) / H1(ERB)=이연(유료) / 나머지 H = T1/T2 sleeve 영역
- 자문 R2 4수정 매핑: 수정1(family 3분리)+수정2(M_eff)+수정3(eff_N) = measure.py 이식 / ★수정4(basket화) = basket-level 4신호 신규 + cross-sec hedge
- ★누락 0건: WebSearch 7주제 전부 위 표 매핑(채택/이연/미채택 사유 박제). reflexivity = 신호 아닌 risk overlay 별도 분류.
