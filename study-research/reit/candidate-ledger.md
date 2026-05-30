---
tags: [type/candidate-ledger, study_id/reit, purpose/work-queue, status/main-priority-corrected-20260531]
date: 2026-05-31
purpose: ★main 정정 후 = merit 후보 작업큐. (1순위) merit 후보 추가 study (이론→실데이터→상관·Rank-IC) + main collector 구현 요청. (2순위·종착) study 후도 빠진 것만 "merit 없음 or 실측 무상관" 사유 기록.
note: ⏳이연 = 탈락 사유 부적격 (main 정정). 모든 ⏳후보 → merit 작업큐 전환 + collector 요청 main 송신 의무.
---

# REIT 지표·변수 후보 원장 (candidate ledger)

## ✅ 채택 (study_session.yaml v2 + direction.md §1-§8 박제, structural prior tier)

### A. M3 거시 driver (실측 회귀, 2022-01 ~ 2024-12, n=753 daily)
| 변수 | tier | 근거 |
|---|---|---|
| **VNQ β_rate (Δus10y bp)** | structural_prior | M3 실측 −3.82 bp t=−5.65, M1 us_stock +0.008 ≈0 패턴과 정반대 = REIT 채권성 듀레이션 실증 |
| **VNQ β_dollar (Δlog DXY)** | structural_prior | M3 −0.841 t=−8.33, M1 us_stock −0.879 동일 강도 |
| VNQ β_oil (Δlog WTI) | structural_prior | M3 −0.008 t=−0.42 ≈0 (영향 없음) |
| rate-UP 시 dollar loading ratio | observation | M3 |E1|/|E4| 1.11~1.52배, M1 us_stock 1.68배 대비 약화 |
| within-sleeve mean ρ=0.547 | structural_prior | M3 9 sub-sector pairwise, M1 us_stock~tech 0.96 대비 낮음 → sector effect |
| Hotel β_rate=+1.79 paradox | observation | 단독 양수, cyclical demand proxy 가설 (R2/R3 합의) |
| Tower E4 β_rate=−12.01 paradox | observation | longest-duration REIT, R3 3 채널 mechanism (escalator + capex/churn + USD EM) |
| E1 9 sub-sector 일관 음수 / E4 광범위 폭주 | observation | Retail +70.04%, Healthcare +58.60% (cum) E4 |

### B. 학설 ref (direction.md §8-1-D 박제, ⛔ 환각/phantom 제외)
| ref | tier | 근거 |
|---|---|---|
| Boudry et al. 2012 JREFE | structural | WALT positive escalator option 학설 (Q8 R3) |
| Harrison-Panjian-Seiler 2011 JREFE | structural | WAM negative refinancing risk + LTV confounding (Q8 R3) |
| Allen-Madura-Springer 2000 JREFE 21(2) | structural | specialization·leverage 가 β_rate modulate anchor (mid) |
| **He-Xiong 2012 Journal of Finance 67(2)** | structural | "Rollover Risk and Credit Risk" — long WAM 이론적 protective. **M3 H3 negative = 부호 반대 → confounding 의심 anchor** |
| Mueller-Pauley 1995 JRER 10(3) | structural | REIT-rate 저상관 + 횡보국면 의존 (정성적 inconclusive primary, ★ Liu-Mei 정량 인용 대체) |
| Giliberto-Shulman 2017 | structural | bond-like + equity component 시변 |
| Yobaccio 1995 RealEstFin 11(1) | structural | REIT 빈약한 인플레 헤지 |
| Glascock-Lu-So 2002 | structural | REIT-inflation 음의 관계 = 통화정책 spurious |
| **Beracha-Feng-Hardin 2019 RealEstateEconomics** | structural | REIT-inflation hedging + illusion 공존, illusion dominant (★ Beracha-Krautz 환각 대체) |
| Holland-Ott-Riddiough 2000 | structural | Hotel short-lease pass-through |
| **Ling-Naranjo 1997 JREFE 14(3)** | method | Economic Risk Factors and CRE Returns (★ Ling-Naranjo 2014/2015 phantom 대체) |
| **Ling-Naranjo 1999 RealEstateEconomics 27(3)** | method | The Integration of CRE Markets and Stock Markets (★ phantom 대체) |
| Plazzi-Torous-Valkanov 2010 RFS 23(9) | structural | cap rate mean-revert + CRE growth predictability (H6 anchor) |
| Roig-Luchtenberg 2014 JREPM | structural | Healthcare REIT properties + performance (mid, H9 anchor) |
| Coval-Stafford 2007 JFE 86(2) | method | Asset Fire Sales 일반 flow predictability (H10 generic anchor) |
| Ben-Rephael-Kandel-Wermers 2012 JFE 104(2) | method | mutual fund flow investor sentiment (H10) |
| Ben-David-Franzoni-Moussawi 2018 JF 73(6) | method | ETF volatility channel (H10) |
| Ledoit-Wolf 2003/2004 | method | covariance shrinkage 표준 (panel-level pooling) |
| Jorion 1986 JFQA | method | Bayes-Stein shrinkage covariance |

### C. 가설 5건 validation 결과 (raw/validation-H{1..5}.md)
| 가설 | 결과 | tier |
|---|---|---|
| H4 window flip (Kendall τ=0.077, swap rate 88%, n=77) | CONFIRMED | structural_prior |
| H2 cap-rate spread mean-revert (VNQ proxy ρ=−0.361) | PARTIAL | structural_prior |
| H5 regime-stable rank falsification (inter-regime ρ=+0.087 random) | CONFIRMED falsification | structural_prior |
| H1 long-WALT positive | REJECT sign mismatch | F축 박제 |
| H3 long-WAM Debt positive | REJECT sign mismatch | F축 박제, confounding R4 carry |

### D. 신규 가설 H6-H10 (direction.md §8-3, 정량 반증조건)
| 가설 | 학설 anchor | 반증조건 | tier |
|---|---|---|---|
| H6 cap-rate spread > 200bp → +12m mean-revert | Plazzi-Torous-Valkanov 2010 RFS | episode dwell + Hansen-Hodrick + hit-rate binomial CI 하한 | structural_prior |
| H7 datacenter capex EQIX lead 6-9m | academic 약함 (Boudry et al. 2020) | CCF peak [6,9]m + Granger (capex→FFO 비유의 reject) | structural_low |
| H8a Tower organic revenue ~ CPI 계수<1 | mechanism 자기완결 | 계수 ≥ 1 또는 <1 비유의 = reject | structural_prior |
| H8b Tower 가격 (rate 통제 후) | mechanism | rate 통제 후 잔존 시 duration 효과 | structural_prior |
| H9 Healthcare event-study (CMS final-rule CAR) | Allen-Madura-Springer 2000 + Roig-Luchtenberg 2014 | event CAR 비유의 AND β_rate net-lease CI 구분 불가 = reject | structural_low |
| H10 broad ETF flow vs sub-sector divergence regime | Coval-Stafford 2007 + Ben-Rephael 2012 + Ben-David 2018 (generic) | orthogonalized flow innovation forward 5게이트 (panel) 미충족 | structural_low |
| H1 재정식화: long-WALT + escalator option = conditional outperform | Boudry 2012 | escalator 구조 (CPI-linked vs fixed) cross-section 검증 | structural_prior |

### E. Sub-cluster 분할 (direction.md §8-1-A, 8 cluster)
- C1 Residential (AVB), C2 Commercial-Retail (BXP, SPG), C3 Industrial-Logistics (PLD), C4 Datacenter-Infra (EQIX, AMT), C5 Healthcare (WELL), **C6a Lodging (HST)**, **C6b Storage (PSA)**, **C8 mREIT 별도 (NLY/AGNC/MFA)**

### F. 방법론 (direction.md §8-2)
- 2-stage Ling-Naranjo decomposition (sub-sector ~ VNQ + market 1차 → 잔차 ρ unique)
- **panel-level / pooled cross-section + Newey-West t-stat** (per-cell 검정 폐기)
- shrinkage 의무 (Ledoit-Wolf 2003/2004 + Jorion 1986 + Ridge L2)
- Posterior shrinkage 생존 (95% CrI 0 제외) + prior-sensitivity λ grid + posterior predictive check
- Event-study CAR (H9 Medicare)
- pricing principle DCF: P ≈ AFFO / (r_f + ERP_REIT + ΔCapRate − g_NOI)
- AFFO/FFO sector standard: triple-net 95-100% / industrial-multifamily 85-95% / office-retail-lodging 70-85%

---

## ⏳ 이연 (이론·후보 식별됐으나 collector / R4 carry / Phase 5 dispatch 후)

### A. 거시 driver 6종 확장 (R1+R2 합의, methodology-brief §B + direction.md §8-1-B)
| 후보 | 사유 (왜 안 들어갔나) | unblock 조건 |
|---|---|---|
| **D1 Real rate (FRED DFII10)** | M3 에선 nominal Δus10y 만 회귀. 2003-01부터 daily continuous (★claude fact 정정 적용) | Phase 5 cluster 별 validation-macro 시 다중회귀 (real + breakeven) |
| **D5 HY OAS (FRED BAMLH0A0HYM2)** | REIT 고leverage refinancing channel, cap-rate spread 와 부분 collinear 만 별도 정보. R1 양 모델 mandatory 합의 | Phase 5 collector_plan |
| **D6 Inflation Breakeven (FRED T10YIE)** | lease escalator 가치, real rate 분해 의무. Fisher collinearity invariant (nominal 제외, real+breakeven만) | Phase 5 collector_plan |
| **D2 Cap-rate spread (Nareit T-Tracker)** | Q3 2022 peak 243bp / Q4 2023 = 123bp primary 확인. ★ Q4 2024 120bp 는 primary 미확인 → baseline 제외 (E축). | Nareit T-Tracker API 또는 분기 CSV |
| **D4 Sector supply** | Census Construction Put in Place 월별 (C30 series) + CMBS Delinquency Rate. CBRE/CoStar appraisal lag (~4분기) 회피 best practice | Census Bureau public API + FRED CMBS delinquency |

### B. mREIT C8 전용 driver (R3 carry)
| 후보 | 사유 | unblock 조건 |
|---|---|---|
| **yield curve slope (10Y-2Y, 10Y-3M)** | mREIT asset-liability mismatch driver | FRED T10Y2Y/T10Y3M (이미 가용) + C8 cluster Phase 5 dispatch |
| **MBS OAS (FNCL/GNCL Bloomberg or proxy)** | mREIT spread risk | Bloomberg 유료 또는 FRED proxy (ICE BofA US MBS OAS) |
| **prepayment convexity (PSA 모델)** | mREIT 음의 convexity | 자체 모델 또는 Bloomberg API |
| **book value MTM 시계열** | mREIT book/share 추세 | SEC 10-Q 분기 추출 |
| **C8 신규 가설**: empirical duration gap × curve slope | R3 carry, equity REIT 9 와 분리 | Phase 5 C8 cluster dispatch 시 작성 |

### C. R4 carry 3건 (Phase 5 dispatch + 별도 트랙)
| 후보 | 사유 | unblock 조건 |
|---|---|---|
| **Beracha-Feng-Hardin 2019 primary PDF** | claude R2 인용 "Beracha-Krautz" 환각 의심 → gemini "Beracha-Feng-Hardin 2019 RealEstateEconomics" 대체 권고. 정확 ref 검증 | Real Estate Economics 2019 vol/issue 정독 |
| **AMT India VIL $3.22B Goodwill Impairment 10-K 2023** | gemini R3 정량 박제, claude R3 "방향성 high 정확 수치 단정 금지". 10-K 원문 풀 필요 | SEC EDGAR AMT 2023 10-K Item 7 (impairment) |
| **CCI/AMT churn schedule ($200M-$400M/yr 2021-24)** | gemini R3 정량, claude R3 단정 금지. 공식 가이던스 원문 | CCI/AMT 10-K + analyst day disclosure |

### D. Universe 확장 후보 (R3 carry, equity REIT 9 외)
| 후보 | tier | 사유 |
|---|---|---|
| **Gaming (VICI/GLPI)** | structural_low | Triple-net (NNN) + 긴 WALT + 인플레 전가 강함 — 별도 lens 가능성 |
| **SFR (INVH/AMH)** | structural_low | mortgage-rate inverse (rate↑ → 주택 구매력 저하 → 렌트 수요↑), residential sub Apartment 와 분리 driver |
| **Timberland (WY/RYN)** | structural_low | commodity 가격 + 인플레 hedge, C7 Alternative 별도 cluster |
| **Farmland** | structural_low | C7 Alternative |
| **Healthcare 세분화: SNF-heavy (OHI/SBRA) vs senior-housing (WELL/VTR)** | structural | H9 event-study cross-section 의무 (gov-pay 노출 차이) |

### E. Phase 5/6/7 dispatch 후 작업
| 후보 | 사유 |
|---|---|
| 8 cluster summary.yaml (lens + indicators + corr_prior + weight_rules + confidence_hooks + collector_plan + code_change_plan) | Phase 5 dispatch ★현재 보류 (subagent 기능 장애, main 지시) |
| Phase 6 평가 subagent (12축 audit, ★supervisor 직접 평가 금지) | Phase 5 산출 도착 후 |
| Phase 7 통합 study_session.yaml v3 (8 cluster + 6 driver + H6-H10) | Phase 5 + Phase 6 완료 후 |

---

## ❌ 미채택 / proxy 대체 / 환각 catch / Fisher 제외 / tautology

### A. ★ 환각 / phantom ref catch (R3 supervisor cross-verify)
| 후보 | 사유 |
|---|---|
| **Beracha-Krautz 2022** | 환각/Working Paper 오류 개연 (gemini R3 + claude R3 모두 confidence low) → **Beracha-Feng-Hardin 2019 RealEstateEconomics 대체** |
| **Ling-Naranjo 2014/2015** | phantom 가능 (Ling-Naranjo-Scheick 2014 "Information Dynamics" 연도 혼용 외 별 신뢰 인용 X) → **Ling-Naranjo 1997 JREFE 14(3) + 1999 RealEstateEconomics 27(3) 대체** |
| **Green Street tower longest-duration citation** | proprietary 구독, 학술 citation 부적합 (claude R3) → **mechanism 자기완결 박제** (5-10y term + renewal option + 고정 ~3% escalator) |
| **Liu-Mei 1992 정량 β range (-1.5~-2.5)** | 오귀속 risk high (claude R3) — 논문 주제 = predictability/market timing, clean rate-beta 추정 아님. **정성적 inconclusive primary 만 인용** |

### B. ★ Fisher 항등식 collinearity 제외 (R1 claude critique)
| 후보 | 사유 |
|---|---|
| **nominal + real + breakeven 동시 회귀 투입** | Fisher 항등식 collinearity (nominal = real + breakeven) — **real + breakeven 만 다중회귀 의무** |
| **β_rate (nominal) yaml 박제** | M3 nominal β_rate=−3.82 는 학설 분해 (real + breakeven) 안 된 raw — yaml 박제 시 real β + breakeven β 분리 의무 (Phase 5 validation-macro) |

### C. ★ Estimand / 5게이트 임계 변경 (R3 claude critique)
| 후보 | 사유 |
|---|---|
| **5게이트 OOS Rank-IC threshold 완화 (0.05→0.03)** | claude R3 = Type I error 폭증 (cell n=60 SE 0.13, 임계 0.05 도 noise 매몰). **threshold 완화 금지, estimand 변경 (per-cell 폐기 → panel-level / pooled cross-section + Newey-West)** |
| **per-cell rank-IC 검정** | 9 sub-sector × monthly cell n≈60 → SE 0.13 noise 매몰. **panel-level (sector fixed/random effect) 또는 pooled cross-section 변경 의무** |
| **"75% confidence" point estimate H6** | claude R3 = point 주장 금지, CI 박제 (5금지 #1 점추정 prior 박제 금지) |
| **H6 반증 "2 consecutive episode"** | n=2 power 0 부적합 → **episode dwell + Hansen-Hodrick/Newey-West + hit-rate binomial CI 하한 < base rate** |
| **H8 단일 가격 검정** | rate level confound 심각 (CPI>3% ≈ 고금리 → tower long-duration price hit 이 escalator 스토리 오염) → **H8 분할 (H8a organic revenue ~ CPI / H8b 가격 rate 통제 후)** |
| **H9 단순 contemporaneous monthly ρ>0.3** | dilution 부적합 → **event-study (CMS final-rule CAR + cross-section SNF-heavy vs senior-housing)** |

### D. Primary 미확인 / baseline 제외 (E축)
| 후보 | 사유 |
|---|---|
| **Q4 2024 cap-rate spread 120bp** | primary 미확인 (Q4'23 123bp 와 혼동 의심) → baseline 제외, theory-notes.md E축 박제 |
| **Hotel +1.79 inflation hedge 인용 그대로 채택** | R2/R3 = "cyclical demand proxy, orthogonalize 시 0 수렴 expect" + 2008/2020 RevPAR 붕괴 counter-example → **단순 hedge 인용 금지, orthogonalize 후 결정** |

### E. 자문 그대로 코드화 금지 (5금지 #3)
| 후보 | 사유 |
|---|---|
| gemini R2 β_rate −1.5~−2.5 range 직접 yaml 박제 | Liu-Mei 1992 오귀속 risk + small-N inconclusive → **inconclusive 정직보고만 박제, 정량 range 인용 금지** |
| 자문 답변 본문 직접 yaml lens 인용 | ⛔ supervisor 비판 + 환각 cross-verify 후 채택만 |

---

## 🔬 후속 재검증 falsifier (채택했으나 조건부)

### A. ★ H1/H3 sign mismatch 후속
- **H1 재정식화** ("long-WALT + escalator option = conditional outperform"): Phase 5 validation-fundamental 에서 escalator 구조 (CPI-linked vs fixed) cross-section 검증. 잔존 outperform 비유의 = H1 완전 reject.
- **H3 confounding orthogonalize** (R4 carry): long-WAM 표본의 sector/leverage 와 H3 Rank-IC partial out. 잔존 negative 잔존 + leverage proxy 비유의 = H3 진짜 mechanism (잔존 reject 시 confounding 확정, He-Xiong 2012 이론 정합).

### B. Hotel paradox 후속
- **Hotel β_rate +1.79 orthogonalize**: GDP/소비/equity market factor 통제 후 잔존 β_rate. 잔존 ≈ 0 또는 음수 = cyclical proxy 확정 (R2/R3 합의 정합). 잔존 양수 = inflation hedge 가설 부분 부활.
- 2008 GFC + 2020 COVID counter-example: Hotel RevPAR 붕괴 = rate-up+recession 시 양 loading 격렬 반전 실증.

### C. Tower paradox 후속
- **H8a fundamental (organic revenue ~ CPI 계수<1)**: AFFO/share 또는 organic revenue growth vs realized CPI 회귀. 계수 < 1 + 유의 = incomplete pass-through 확정.
- **H8b 가격 (rate 통제 후)**: H8a mechanism 박제 후, 가격 검정 = rate level 통제 후 잔존 만. 잔존 = duration 효과.
- AMT India $3.22B VIL Goodwill Impairment + CCI Sprint churn $200M-$400M/yr = R4 primary verify 후 cum return 분해.

### D. C8 mREIT 별도 트랙
- **empirical duration gap × curve slope 가설** (R4 carry): NLY/AGNC asset-liability duration gap 실측 + curve slope (10Y-2Y) 회귀. mREIT 특유 driver = yield curve slope + MBS OAS + prepayment convexity (음의 convexity) + book value MTM.
- equity REIT 9 cluster 와 driver set 분리 의무 (R1+R2+R3 합의).

### E. M3 정량 분해 후속
- **VNQ β_rate=−3.82 분해**: Phase 5 validation-macro 시 [real rate (DFII10) + breakeven (T10YIE)] 다중회귀. R2 expect = real β ≈ −4~−6 / breakeven β ≈ 0~소폭 양수 (sample-dependent). 실측 split 이 유일 ground truth.
- 1990-2020 long-run β_rate 추정: 2022-2024 epoch 상한 추정치 가설 → 장기 시계열 확장 시 |β| 더 작음 expect (학설 inconclusive).

### F. 다중검정 보정
- H1-H10 = 10 가설 + 8 sub-cluster × 6 driver = 48 회귀 = 다중검정. **Benjamini-Hochberg FDR (q=0.10) 또는 Bonferroni (α/N) 보정 의무**. 보정 후 잔존 유의 가설만 yaml 박제.

---

## 산출 cross-ref

- `methodology-brief.md` (Phase 2)
- `direction.md` §1-§8 (Phase 2-1 5 가설 + Phase 3.5 v2-mirror supplement)
- `raw/consult-round-{1,2,3}.md` (Phase 3 자문 R1+R2+R3 supervisor cross-verify §5)
- `raw/m3-macro-linkage.md` + `raw/validation-{H1..H5}.md` + `raw/theory-notes.md`
- `raw/evidence-map.md` (C 축 추적성)
- `evaluation-axes.md` (Phase 1, Phase 6 평가 SSOT)
- `plan.md` (Phase 4 작업 계약, Phase 5/6/7 prompt + coder-readiness)
- archive raw 6건: `~/.claude/docs/archive/research-raw/reit-v2mirror-phase3-r{1,2,3}-{gemini,claude}-2026053{0,1}.txt`
- `study_session.yaml` (v2 = 861 lines structural prior tier) + `study_session.yaml.v1.bak` 폐기 X 보존
