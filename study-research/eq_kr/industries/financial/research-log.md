---
tags: [type/research-log, domain/equity, sector/financial]
date: 2026-06-05
purpose: financial 지표 탐구 시계열 — 시도/막힘/해결/환경함정. 다음 세션 재현용. append-only.
---

# financial 리서치 로그

## 데이터 소스 탐구

| 지표 | 후보 소스 | 시도 결과 | 최종 채택 | 함정·교훈 |
|---|---|---|---|---|
| 가격 패널 | pykrx OHLCV 개별종목 loop | ✅ 작동 (34종, 1818일, 2019-2026) | ✅ prices.parquet | 반도체 동일. pykrx 시장 스냅샷 API는 KRX 인증 차단, 개별 OHLCV loop 는 작동 |
| valuation 횡단면 | DART fnlttSinglAcntAll | ✅ 작동 단 ★2023~만 (IFRS 은행/보험 별도양식) | ✅ dart_financials.parquet(312rows/33종) | ★금융 재무 = 2023 회계연도부터만. 2019-2022 status 013(데이터 없음). valuation forward IC n 제약(PBR n=27~29) = 근본 데이터 한계 |
| ★금리 regime (financial 특화) | ECOS 817Y002 시장금리 일별 | ✅ 작동 (국고채2Y/3Y/10Y + 회사채AA-/BBB-) | ✅ regime_series.parquet | ★기존 v2 US 10Y proxy → KR 국고채 직접 교체 해소. 국고채2Y 는 2019초 결측(발행 본격화 2021) → ★10Y-3Y term spread 로 대체 |
| 외국인flow (시장레벨) | ECOS 802Y001/0030000 | ✅ 일별 2018~2026 | ✅ regime_labels | 반도체 동일 경로. KRX 종목별 차단 → 시장레벨 regime 만 |
| Macro/KRW regime | FRED KORLOLITOAASTSAM / DEXKOUS | ✅ 작동 | ✅ regime_labels | 반도체 collect_regime.py 재사용 |
| credit spread regime | ECOS 회사채AA-(010300000) − 국고3Y(010200000) | ✅ 작동 (레고랜드 2022-11 spread 1.77 실재) | ✅ credit_regime | ★기존 v2 US HY OAS proxy → KR credit spread 직접 교체 해소 |
| 밸류업 event | prices + DART PBR | ✅ 측정완료 (2024-02-26/2024-05-02 CAAR) | ✅ validation-oos-event | ★financial 고유. Market Model β estimation [-120,-11], event window [-5,+5]/[+1,+60] |
| PF 익스포저 (증권 충당금) | DART 충당금 계정 | ⏳ 미수집 | ⏳ 이연 | credit_regime(거시) 으로 부분 대리. 종목별 PF 노출 = DART 주석 파싱 필요(후속) |
| 종목레벨 외국인 flow | KRX 종목별 net buy | ❌ KRX 인증 차단 | ⏳ data-gate | 반도체 동일. 시장레벨 regime 만 측정. unblock = KRX 인증/증권사 API |

## 막힘·해결 로그 (시계열)

- [2026-06-05] 진입: financial capsule = 기존 v2 산출(summary.yaml/measure/measure_valuation/measure_cross/interaction_t + validation json) 존재. → 진단: 기존 = unconditional IC + 단일 rate regime(US 10Y proxy, rate_up/down/flat 3국면)만 = 반도체 conditional IC 36셀 surface 양식 미달 + ★금융특화(금리커브/NIM/PF/밸류업) 전혀 미반영 + theory-notes/candidate-ledger/research-log/conditional measure 부재. → 해결: 기존 valuation/cross json 부분 활용(PBR/PER PIT 패널·common factor β) + conditional IC 심화 양식으로 업그레이드. 교훈: 진입 시 기존 산출의 "양식 세대" 점검(unconditional v2 vs conditional v3) = 무조건 재작성도 무조건 재사용도 아님.

- [2026-06-05] ★S1 리서치 2R (Gemini Pro, web-guard 차단 → gemini-search.js 경유). 1R = 금융 cycle 7 메커니즘(금리커브/NIM/sub-sector차등/밸류업/PF/외국인/momentum) 학술+실무 ground. 2R = 비판검토 6Q. → ★핵심 발견(Q2 비판): 은행/보험(금리+) vs 증권(금리−) 부호 반대 → 금융 전체 eq-weight cross-sectional IC 측정 시 부호 cancel → 신호 약하게 나옴. = 기존 v2 "unconditional 전부 비유의"의 근본 원인 가설. = frame §1.6(분석unit↔portfolio label 분리, ERROR-202605302245 anchor) 직격. → 해결: sub-sector 분리 측정 의무(ALL/bank/securities/insurance/rate_POS/rate_NEG). 교훈: 금융은 반도체(동일부호 cyclical)와 달리 sub-sector 부호 이질 = 통합 cross-sectional IC 부적합.

- [2026-06-05] ★금리 regime 데이터 확정 (collect_regime.py): ECOS 817Y002 = 국고채2Y(010195000)/3Y/10Y + 회사채AA-(010300000)/BBB- 일별 2018~2026 전부 가용. → ★국고채2Y 2019초 결측(2년물 발행 2021~) → 10Y-3Y term spread 대체. 금리 3축 신설: rate_regime(국고3Y 6M Δ ±0.3%p) / curve_regime(10Y-3Y 분위 70%) / credit_regime(AA−-국고3Y 분위 70%). 합성지문 PASS: USDKRW 2022-10 1440.3 / KTB10Y 2020-08 1.281→2022-10 4.632(금리쇼크) / credit spread 2022-11 1.77(레고랜드) 실재. ★금리 regime 전부 powered(rate_up 30/down 26/flat 33, curve_steepen 43, credit_wide 36) = 반도체보다 cell N 충분. 교훈: ECOS StatisticItemList 로 시장금리 일별(817Y002) 항목코드 탐색 → 국고채/회사채 직접 = US proxy 불필요.

- [2026-06-05] ★conditional IC surface 측정 (measure_conditional.py, G-F 7항 헤더). 6신호 × horizon(y_5d/20d/60d) × regime 6축(rate/curve/credit/krw/flow/macro) × ★sub-sector 6그룹. per-cell wild-cluster bootstrap p + n_eff + block-boot CI.
  - ★발견1 (cancel 입증): pbr_z uncond = bank **−0.0905**(value premium) vs securities **+0.0415**(반대 부호) → ALL −0.0313 약화. bank pbr_z y60d −0.1614 wc_p=0.0165(powered 유의) vs securities y60d +0.1464 wc_p=0.024. = 은행 저PBR value / 증권 반대 → 통합 cancel.
  - ★발견2 (bank momentum): bank mom_12_1 y60d credit_normal +0.1753 / KRW_neutral +0.2136 wc_p=0.0005 / uncond +0.0905 wc_p=0.0445 = 은행 long-horizon continuation(spread_driven).
  - ★발견3: rev_1m 단기 reversal = rate_POS y20d KRW_weak −0.16 / Slowdown −0.17 wc_p<0.01 (위험회피 국면 reversal 강).
  - FDR family m=862(naive) BY survivors=[] raw_p_min=0.0005(bank mom_12_1 KRW_neutral). ★M_eff 주의: m=862 = sub-sector 6그룹(ALL⊃분리, rate_POS⊃중복) × 신호상관 과대. 독립 = bank/secur/insur 3 + 신호 M_eff≈3-4 → supervisor 통합단계.

- [2026-06-05] ★walk-forward OOS (measure_oos_event.py, IS2019-22/OOS2023-26 split, team-lead 지시):
  - ★**bank mom_12_1 y60d = structural break 발견**: 2020-22 음(-0.04/-0.06/-0.06=reversal) → 2023-26 양(+0.25/+0.11/+0.25/+0.67=continuation). IS −0.054 → OOS +0.228 ★부호반전 = **in-sample artifact 아니라 regime/structural break**(밸류업 2024~ 은행주 추세상승 정합). = momentum 신호 NOT robust(단정 금지).
  - **rev_1m: IS/OOS 부호유지** (bank rev1m y5d IS -0.056→OOS -0.173 / ratePOS rev1m y20d IS -0.061→OOS -0.055) = 가장 robust 신호.
  - bank pbr_z y60d: ★DART 2023~ 제약 = IS(2019-22) n=0 → OOS-only = OOS verdict 불가(data-gate). within-period 2023(+0.14)/2024(-0.02)/2025(-0.36)/2026(+0.02) 부호 불안정 = magnitude tentative.
  - 교훈: walk-forward 가 momentum 의 structural break(시기별 부호반전)를 정확히 노출. valuation 은 DART 데이터 부재로 split 자체 불가 = data-gate(deferral 아님).

- [2026-06-05] ★밸류업 event study (measure_oos_event.py, ★이연 금지 = 지금 측정):
  - 1차(2024-02-26 세미나): 저PBR 금융주 CAAR [-5,+5] **−0.077** / [+1,+60] −0.054 = ★예상과 반대(음). "sell the news" 또는 1차 세미나 실망.
  - 2차(2024-05-02 가이드라인): 저PBR CAAR [-5,+5] +0.014 / [+1,+60] **+0.034**, spread(저-고) +0.076 = ★re-rating 발현(구체적 가이드라인).
  - ★종합: 1차 음/2차 양 = single event 단정 불가(theory M3 부분 지지/부분 기각). 정직 박제 = "밸류업 effect = 2차 가이드라인에서 발현, 1차는 무반응/역행". n=8-9종 small-n.

- [2026-06-05] ★S5 역공격 3 반증 (validation-attack-v3.json):
  - **★반증3 (결정적)**: 은행 PBR IC −0.161 vs 증권 PBR IC +0.146, **차이 t=−3.18(n=27) 유의** = sub-sector 부호 반대 통계 입증 = cancel 구조 확정(frame §1.6). financial 통합 측정 부적합 = 결정적.
  - 반증1: bank PBR value = leave-top2-out −0.161→−0.202 강화 = 대형주 의존 아님(중형 은행 강).
  - 반증2: rate_POS rev_1m reversal = leave-2020-out −0.039 / leave-2022-out −0.026 (full −0.042) = 2020 무관, 2022 부분 의존(약화). 부호 유지.
  - 교훈: 금융 핵심 발견 = "신호 강도"가 아니라 ★"sub-sector 부호 이질 구조"(은행 value / 증권 반대). cancel 입증이 financial capsule 의 진짜 산출.

- [2026-06-05 후속] ★team-lead 기술 가이드 흡수 (cell 곱셈 금지): "금융특화 금리regime 축을 base 36셀(Macro4×KRW3×flow3)에 ⛔곱하지 마라 — 4×3×3×금리3 = 108셀이면 cell N 전부 붕괴. (a) family_2 interaction conditioning OR (b) 별도 1D 금리regime IC(금융전용 보조 surface)로 분리. base 36셀은 12산업 공통 유지, 금융특화는 그 위 추가 layer." → 진단: 내 measure_conditional.py REGIME_AXES loop 점검 = ★이미 각 축 **독립 1D 분해**(곱셈 cross product 아님). 실측 cell candidate = 단일축 합 4+3+3+3+3+2 = 18 (곱셈 648 회피). 금리 3축 = 독립 1D surface(권고 b) + family_2 interaction rate×signal(권고 a) 둘 다 정합. → 해결: 곱셈 미발생 입증(json cell key 패턴 = "axis=value" 단일축만, 복합 "axis1=v1&axis2=v2" 없음). measure_conditional.py 헤더 §1 + summary.yaml cycle_reading 에 "cell 곱셈 금지 + base 36셀 공통 보존 + 금리축 별도 layer" 명시 박제. 교훈: regime 축 추가 시 ★곱셈(cross product)이 아닌 독립 1D 분해가 cell N 보존 + 12산업 공통 base 유지의 정답.

- [2026-06-05 후속] ★fin-audit G-C remediation 2건 흡수: (1) cancel diff t=−3.18 자기상관 보정 — 데이터 직접 재현(lag-1 ac=0.452, NW-HAC lag3 t=−2.64 / n_eff 14.7 t=−2.35 / wc_p=0.0045 / CI[−0.60,−0.14] 0배제) = 부호 robust 유지. naive 단독→보정 병기(validation-attack json + summary.yaml + 15axis + ledger). 다른 지표엔 wild-cluster 적용했는데 cancel diff만 naive였던 것 정정. (2) theory-notes §1-ref 인용 11명 DOI/URL 박제(A축 PARTIAL→PASS). 교훈: cross-sectional IC 차(diff) 도 overlapping 이면 자기상관 보정 의무(개별 IC 만 보정하고 diff 빠뜨리지 말 것).

- [2026-06-05 약신호 부활] ★team-lead 지시(이연 후보 ROE/quality + PF 부활). measure_quality.py → DART TTM 순이익/자본 ROE z + 고ROE 저PBR QMJ 결합. conditional IC regime×horizon + walk-forward OOS + 단일 FDR(m=22) + per-cell wc_p + MDE/power(G-G v2).
  - ★발견: **securities roe_z y60d IC=+0.317 wc_p=0.0025** = 증권 고ROE quality premium. by_year 전부 양(2024 +0.51/2025 +0.19/2026 +0.35), leave-2024-out +0.21/leave-2025-out +0.47 = 부호유지(단일 episode 종속 아님). ↔ **insurance roe_z −0.177**(반대 부호). 증권 vs 보험 차이 t_naive=5.57/NW-HAC lag3=5.28 = ★PBR cancel 구조 ROE축 재확인.
  - ★막힘/한계: (a) DART 금융재무 2023~ → IS(2019-22) n=0 = walk-forward OOS split **불가**(PBR 동일 data-gate) (b) BY 미생존(m=22) (c) n_eff 보정 MDE 미달(small-N n=22~28). → verdict = **TENTATIVE, tradeable 미승격**(부분 부활). within-period 일관이 유일 신뢰 증거.
  - ★PF 익스포저 종목별 = DART 주석 충당금 파싱 복잡 → team-lead "어려우면 ROE 우선" 따라 ROE 우선. credit_regime(거시) 부분 대리. DART 주석 파싱 = 후속.
  - 교훈: ★ROE/quality 도 PBR 과 동일 sub-sector 부호 이질(증권+ vs 보험−) + DART 2023~ data-gate. financial 약신호의 본질 = "신호 부재" 아니라 "(i) sub-sector cancel (ii) DART short-sample" 2중 제약. = 이연 금지 이행(측정했으나 데이터 제약으로 tentative, 정직 박제).

- [2026-06-05 rotation] ★team-lead 지시(금융 업종 자체 rotation = 어느 국면→금융 OW/UW, 종목selection과 별 차원). rotation-analyst v2 = financial cli_chg type=MACRO(N_eff≈1 시장timing) → 금융 고유 driver(금리커브/credit/대출) 판별. measure_rotation.py.
  - ★데이터 신규: KOSPI 벤치마크(FDR KS11, 상대수익 판별용) + ECOS 104Y016 총대출금(BDCA1) 월별. 기존 ECOS 금리(term/credit spread) 재활용.
  - ★측정 설계 핵심 = 종속변수 2종: (a) 절대 forward(financial eq-weight) (b) ★상대 forward(financial − KOSPI). 판별 = 상대 예측=금융고유 / 절대만=시장timing (Gemini 이론 Q1 회귀 β 유의 기준).
  - ★발견(이론 반증): **term_spread(금리커브) 절대 +0.292(wc_p 0.0075 강) but 상대수익 −0.216(이론 Flannery-James NIM+ 부호 반대)**. ★은행만 분리해도 상대 −0.21 = sub-sector mix 아님, NIM 직접 종목 은행도 시장 대비 outperform 못함. = 금리상승=경기확장=시장 전체 상승(cyclical), 금융 NIM 프리미엄 < 시장 동조 = ★이론 한국 데이터 반증. momentum = 절대 강(+0.298) but 상대 무(−0.08)+OOS flip = market×beta data mining(이론 Q5 입증). loan_growth = 상대 +0.157 OOS+0.398 부호유지(이론+ 일치) but wc_p=0.22 비유의+by_year 불안정 = TENTATIVE.
  - ★판정: 금융 = 시장 cyclical beta 업종. 금융 고유 rotation 신호 약/반증. supervisor 권고 = rotation tilt 보류(default weight 0). financial primary alpha = 종목selection(sub-sector 분리), rotation secondary 약.
  - 교훈: ★rotation 판별의 핵심 = **절대 vs 상대수익**. 절대 강해도 상대(vs 벤치마크) 미예측이면 = 시장 timing(cyclical beta), 산업 고유 rotation 아님. 미국 학술 prior(Flannery-James)도 한국에서 반증될 수 있음(무비판 채택 금지, single-source 단정 금지). = team-lead "이론을 통계가 검증" + data mining 차단 파이프라인.

## 측정 방법 결정 로그

- **★regime 축 = 독립 1D 분해 (곱셈 금지, team-lead 가이드)**: base 36셀(Macro4×KRW3×flow3) = 12산업 공통 보존. 금융특화 금리 3축(rate/curve/credit)은 ⛔곱하지 않고(108셀 붕괴 회피) 독립 1D 보조 surface + family_2 interaction. 실측 = 단일축 합 18 cell candidate. 2축 cross merge = supervisor 통합 또는 N 누적 후.
- **★sub-sector 분리 측정 (frame §1.6)**: 금융 = 은행/보험(금리+) vs 증권(금리−) 부호 반대 → 통합 cross-sectional IC cancel. ALL vs bank/securities/insurance/rate_POS/rate_NEG 6그룹 분리. = Q2 비판 데이터 검정(분리 시 신호 살아나면 cancel 입증).
- **★금리 regime 축 신설 (반도체 대비 차이)**: 반도체 = Macro CLI × KRW × flow 3축. financial = ★금리 3축(rate/curve/credit) 추가 = NIM 본질 driver(반도체 DRAM cycle 대응). frame §3 Layer3 명시됐으나 기존 v2 미반영 = 이연 금지 이행.
- **valuation = PBR(은행/지주 작동) + PER 무효**: 은행 P/B·ROE(sales_yield 부적합=이자수익 레버리지). 보험 PER = IFRS17 일회성 peak-EPS 왜곡(기존 v2 per_z 24M t=21.2 = n=7 허수 확정).
- **G-F 7항 헤더**: fixed-b/wild-cluster per-test calibration = small cell block 한자릿수 NW-HAC asymptotic t size-invalid(Kiefer-Vogelsang) → 재계산.
- **밸류업 event study**: financial 고유. Market Model(estimation [-120,-11]) CAAR(저PBR vs 고PBR). 2024-02-26/2024-05-02.

## 미해결 / 다음 세션 우선 작업

1. ★DART 금융재무 2019-2022 확보(IFRS 별도양식 OR 데이터벤더) → valuation IC n 확대 → bank PBR value premium magnitude 확정(현 n=27 tentative, OOS split 불가).
2. PF 익스포저 종목별(DART 주석 파싱) → 증권/지방은행 신용위험 cross-sectional 신호.
3. 종목레벨 외국인 flow(KRX 인증) → 밸류업 종목선별 알파.
4. ROE/quality 지표(DART 순이익/자본) cross-sectional → 고ROE 저PBR 결합(Asness QMJ).
5. sub-sector 부호반대 = supervisor 통합 시 ★rate_POS(은행/보험/지주) sleeve vs 증권 별 sleeve 분리 권고(frame §1.6 portfolio label).
6. M_eff 통합 FDR(naive m=862 과대, 독립 sub-sector 3 + 신호 M_eff) = supervisor 통합단계.
