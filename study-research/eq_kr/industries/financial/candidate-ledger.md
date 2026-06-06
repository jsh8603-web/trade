---
tags: [type/candidate-ledger, domain/equity, sector/financial, purpose/easy-review]
date: 2026-06-05
purpose: 자문·이론·실측에서 거론된 금융 지표 후보 전체 + 채택/이연/미채택 + 사유. 다음 세션이 "뭐가 왜 빠졌나" 한눈에.
source_artifacts: Gemini Pro 리서치 2R(2026-06-05) + 기존 v2 measure/summary/valuation(2026-06-03) + conditional/oos-event/attack v3(2026-06-05) + frame v3 §1.6/§M
---

# financial(금융) 지표 후보 원장

> ★범위 = financial capsule 한정 (12산업 독립 ledger). 기존 v2 측정 흡수 + conditional IC v3 신규.
> ★verdict 라벨 = small-n rule (CONFIRMED/PARTIAL/TENTATIVE/INSUFFICIENT/REJECTED).
> ★핵심 한 줄: 금융 = **sub-sector 부호 이질**(은행/보험 금리+ vs 증권 금리−). 은행 저PBR value(IC 음) vs 증권 반대(IC 양) **차이 = 통합 cross-sectional IC cancel = frame §1.6** (★자기상관 보정: naive t=−3.18 → NW-HAC lag3 t=−2.64 / wc_p=0.0045 / CI[−0.60,−0.14] 0배제, fin-audit 독립재현). financial 진짜 산출 = "신호 강도" 아닌 "분리 구조".

## ✅ 채택 (yaml 등록 + 검증 통과)

| 지표 | family | tier | 근거 (source·n·검증) |
|---|---|---|---|
| ★**sub-sector 부호 이질 (PBR)** | value(분리 구조) | PARTIAL (핵심 발견) | ★은행 pbr_z y60d IC −0.161 wc_p=0.0165(value premium) vs 증권 +0.146 wc_p=0.024(반대) → 차이 **t=−3.18 n=27 유의**(S5 반증3). leave-top2-out −0.202 강화(대형주 의존 아님). ★단 DART 2023~ 제약 n=27 = magnitude tentative. source=validation-conditional-v3.json + validation-attack-v3.json |
| cs_rev_1m (단기 reversal) | reversal | PARTIAL | rate_POS rev_1m y20d uncond −0.058 wc_p=0.061, KRW_weak −0.16 wc_p=0.003 / Slowdown −0.17 wc_p=0.007. ★**IS/OOS 부호유지**(bank y5d IS−0.056→OOS−0.173 / ratePOS y20d IS−0.061→OOS−0.055) = 가장 robust. leave-2020-out 유지. source=validation-conditional-v3.json + validation-oos-event-v3.json |
| ★**금리 regime 축 (rate/curve/credit)** | regime 축 | 측정완료 | ★financial 특화 신설(반도체 DRAM cycle 대응). ECOS 국고채3Y 6M Δ / 10Y-3Y term / AA−-국고3Y credit. 전부 powered(rate_up 30/curve_steepen 43/credit_wide 36). = NIM/신용 conditioning 축. source=regime_labels.parquet |
| cs_mom_12_1 (은행 long-momentum) | momentum | TENTATIVE (structural break) | bank mom_12_1 y60d uncond +0.0905 wc_p=0.0445 / KRW_neutral +0.214 wc_p=0.0005. ★단 **structural break**: 2020-22 음(reversal) → 2023-26 양(continuation) = IS−0.054→OOS+0.228 부호반전. = regime 의존(밸류업 추세), magnitude 단정 금지. source=validation-conditional + oos-event |

## 🧪 밸류업 event study 측정완료 (★이연 금지 = financial 고유 지금 측정)

> 사용자 박제 "이연 금지" → 2024-02-26(1차)/2024-05-02(2차) Market Model CAAR 측정완료. 결과 정직 박제(1차 음/2차 양 갈림).

| event | window | 저PBR CAAR | 고PBR CAAR | spread(저-고) | verdict |
|---|---|---|---|---|---|
| 1차 2024-02-26 (세미나) | [-5,+5] | **−0.077** | +0.006 | −0.083 | ★예상 반대(음). "sell the news"/세미나 실망 |
| 1차 2024-02-26 | [+1,+60] | −0.054 | −0.009 | −0.045 | 음 지속 |
| 2차 2024-05-02 (가이드라인) | [-5,+5] | +0.014 | −0.003 | +0.016 | 양전 |
| 2차 2024-05-02 | [+1,+60] | **+0.034** | −0.042 | **+0.076** | ★re-rating 발현(구체 가이드라인) |

★밸류업 종합: **1차 음/2차 양 = single event 단정 불가**(theory M3 부분 지지/부분 기각). 정직 박제 = "효과는 2차 가이드라인에서 발현, 1차 세미나는 무반응/역행". n=8-9종 small-n = TENTATIVE.

## 🔧 약신호 부활 측정완료 (★team-lead 지시 2026-06-05, 이연 후보 부활 시도)

> candidate-ledger 이연 후보(ROE/quality + PF 익스포저) 자체 데이터 부활 시도. measure_quality.py → validation-quality-v3.json. ★결과 정직 박제(부활 OR 약).

| 지표 | 측정결과 | walk-forward OOS | verdict |
|---|---|---|---|
| ★**securities roe_z** (증권 고ROE quality) | y60d IC=**+0.317** wc_p=0.0025, by_year 전부 양(2024 +0.51/2025 +0.19/2026 +0.35), leave-2024 +0.21/leave-2025 +0.47 부호유지 | ★IS(2019-22) n=0 (DART 2023~) = OOS split 불가 = **data-gate** | **TENTATIVE (부분 부활, 미tradeable)** — 증권 고ROE quality premium within-period 일관 + sub-sector 차이 강. ★단 DART 2023~ IS n=0 + BY 미생존(m=22) + n_eff 보정 MDE 미달 = magnitude tentative, OOS 검증 불가 |
| ★**insurance roe_z** (보험 고ROE) | y60d IC=**−0.177** wc_p=0.0285 (★증권과 반대 부호) | data-gate | ★sub-sector 부호 이질 = PBR cancel 구조 ROE축 재확인. 증권 roe(+) vs 보험 roe(−) 차이 **t_naive=5.57 / NW-HAC lag3=5.28** 강함 |
| roe_pbr_qmj (고ROE 저PBR 결합 QMJ) | bank y60d +0.183 wc_p=0.07 / ALL 약 | data-gate (IS n=0) | TENTATIVE — bank 에서 QMJ 약 양(고ROE저PBR), 단 underpowered + OOS 불가 |
| PF 익스포저 종목별 | ★미측정 (DART 주석 충당금 파싱 복잡) | — | credit_regime(거시) 부분 대리. team-lead "어려우면 ROE 우선" 지시 따라 ROE 우선. DART 주석 파싱 = 후속 |

★**약신호 부활 종합**: ROE/quality 측정 결과 = ★financial sub-sector 부호 이질이 ROE 축에서도 재확인(증권 고ROE+ vs 보험 고ROE−, 차이 t=5.28). securities roe_z within-period 일관(+0.317, leave-year 부호유지)이나 ★DART 2023~ IS n=0 = OOS split 불가 + BY 미생존 = **TENTATIVE, tradeable 미승격**(data-gate). = "측정했으나 데이터 제약으로 약"(이연 금지 이행, 정직 박제). PBR cancel 구조와 동형 = sub-sector 분리 필요성 ROE 축 추가 입증. ★unblock = DART 2019-22 확보 → IS/OOS split → securities roe quality tradeable 재판정.

## 🔄 ROTATION 신호 측정완료 (★team-lead 지시 2026-06-05, 금융 업종 비중 timing)

> 금융 업종 ★자체 rotation(어느 국면→금융 OW/UW). 종목selection과 별 차원. measure_rotation.py → validation-rotation-v3.json. ★판별 = 상대수익(financial−KOSPI) 예측=금융고유 / 절대만=시장timing. rotation-signals.md SSOT.

| 신호 | 절대60d | 상대60d(금융고유 판별) | 이론부호 | 판정 |
|---|---|---|---|---|
| term_spread_d3 (금리커브 NIM) | +0.292 wc_p=0.0075 | **−0.216**(이론+ 반대, 은행만도 −0.21) | + (Flannery-James) | ★**시장 timing (이론 반증)** — 금리커브 절대수익 강하나 상대수익 미예측 = 금융 고유 아님 |
| credit_spread_d3 | −0.169 | −0.085 wc_p=0.47 OOS flip | − (Merton) | ★시장 timing (상대 미예측) |
| loan_growth_yoy | −0.148 | +0.157 OOS+0.398 hold wc_p=0.22 | + | TENTATIVE (이론 부호 일치 + OOS 유지, 단 비유의 + by_year 불안정 = monitor-only) |
| mom_3 / mom_6 | +0.298/+0.229 powered | −0.08/−0.05 OOS flip | market×beta | ★**data mining (시장 momentum×beta 재포장)** = 이론 Q5 입증 |

★rotation 종합: **금융 = 시장 cyclical beta 업종. 금융 고유 rotation 신호 약/반증.** term spread(금리커브)가 절대수익은 강 예측하나 ★상대수익(vs KOSPI) 미예측/부호반대 = NIM 프리미엄 < 시장 cyclical 동조 = ★이론(Flannery-James 1984) 한국 데이터(2019-26) 반증(무비판 채택 안 함). momentum = market×beta data mining. loan_growth 만 약 금융 고유 후보(TENTATIVE 비유의). = rotation-analyst v2 cli_chg type=MACRO 판정을 금리커브로 직접 입증. ★supervisor 권고 = 금융 rotation tilt 보류(default weight 0). financial primary alpha = 종목selection(sub-sector 분리), rotation 은 secondary 약.

## ⏳ data-gate / 이연 (현 데이터 측정 불가 — deferral 아님)

| 후보 | 출처 | 상태 | unblock 조건 |
|---|---|---|---|
| **DART 금융재무 2019-2022** | DART fnlttSinglAcntAll | ★**data-gate** | 금융업 IFRS 별도양식 = 2023~만(status 013). PBR value premium magnitude·OOS split 불가 원인. unblock = 데이터벤더/사업보고서 원문 파싱 |
| **PF 익스포저 종목별** | DART 주석 충당금 | ⏳ 이연 | credit_regime(거시) 부분 대리. 종목별 = DART 주석 파싱(후속 측정 대상, 데이터는 존재) |
| **종목레벨 외국인 flow** | KRX 종목별 net buy | ★**data-gate** | KRX 인증 차단(pykrx KeyError). 시장레벨 regime(ECOS)은 측정완료. unblock = KRX 인증/증권사 API |
| **ROE/quality** (순이익/자본) | DART | ★**측정완료**(2026-06-05, §약신호 부활) | securities roe_z +0.317(부분 부활 TENTATIVE) / 보험 −0.177(부호반대). DART 2023~ IS n=0 = OOS data-gate. unblock = DART 2019-22 |
| **국고채2Y term spread** | ECOS 010195000 | proxy 대체 | 2년물 2019초 결측(발행 2021~) → 10Y-3Y term spread 대체 사용 |
| **M_eff 통합 FDR** | G-F §3 | supervisor | naive m=862 과대(sub-sector 6그룹 중복 + 신호상관). 독립 = sub-sector 3 + M_eff_signal → 통합단계 |
| **sub-sector sleeve 분리** | frame §1.6 | supervisor | rate_POS(은행/보험/지주) vs 증권 별 sleeve = portfolio label 분리(통합 단계 권고) |

## ❌ 미채택 / proxy 대체

| 후보 | 사유 |
|---|---|
| per_z (전 horizon) | ★PER cross-sectional 비유의(uncond +0.034 wc_p=0.54). bank per_z y20d −0.19 = 은행만 약. 보험 IFRS17 일회성 peak-EPS 왜곡. ★기존 v2 per_z 24M t=21.2 = n=7 허수(eff_indep 0.3 degenerate) 확정. |
| cs_mom_6m (6M momentum) | uncond 비유의(ALL −0.02 / bank −0.02). spread_driven continuation 약. mom_12_1 이 더 신호(단 structural break). |
| vol_60 (저변동성) | uncond 비유의(ALL −0.02). Slowdown −0.14 underpowered. |
| common factor (credit/VIX/dollar/oil/rate level β) | ★기존 v2 전부 비유의(US proxy). 단 level β ≠ regime effect → 금리 regime conditional 로 재측정(rate/curve/credit regime 신설). |
| customer-supplier momentum | financial 부적합(upstream 정의 불분명). macro(금리/credit) regime 의존이 dominant. |
| sector-rotation business-cycle clock | 학술 myth(Molchanov 2024). |
| US 10Y proxy regime (기존 v2) | ★KR 국고채(ECOS) 직접 측정 가능 → proxy 격하. rate_regime 으로 교체. |
| US HY OAS proxy credit (기존 v2) | ★KR credit spread(ECOS 회사채AA-) 직접 측정 가능 → proxy 격하. credit_regime 으로 교체. |

## 🔬 후속 재검증 falsifier (채택했으나 조건부)

| 가설/지표 | 미해결 의문 | unblock (validated 승격) 조건 |
|---|---|---|
| 은행 PBR value premium | DART 2023~ n=27, IS/OOS split 불가. 진짜 강신호인가 short-sample artifact 인가 | DART 2019-2022 확보 → 장기 IC + within-period ≥4년 + magnitude 확정 |
| sub-sector cancel (은행− vs 증권+) | t=−3.18 유의하나 n=27 short-sample. structural 인가 sample 우연인가 | DART 장기 + 2nd 금리cycle + supervisor sleeve 분리 검증 |
| 밸류업 event (2차 양) | 1차 음/2차 양 = 일관성 부재. 2차만 진짜 effect 인가 noise 인가 | 후속 밸류업 정책 event(2025+) 추가 + 저PBR 금융주 long-run re-rating 추적 |
| 은행 mom_12_1 structural break | 2023~ continuation = 밸류업 추세 종속? 차기 cycle 반전? | 2nd 금리/밸류업 cycle pristine OOS |
| rev_1m reversal | IS/OOS 부호유지하나 magnitude 약(−0.05). live 지속? | e-CUSUM 부호반전 모니터 |

## 🔄 flip-register (regime/sub-sector sign flip — ★pristine OOS 게이트, 현 vintage 확정 금지)

> regime/sub-sector별 부호반전 = 흥미롭지만 in-sample only → flip-register 박제 + 차기 vintage pristine OOS 게이트.

| flip cell | 부호 패턴 | n / 근거 | 해석 (가설) | OOS 게이트 |
|---|---|---|---|---|
| ★pbr_z [bank vs securities] | bank −0.161 / 증권 +0.146 | n=27 / 차이 t=−3.18 유의 | ★sub-sector 부호 반대(cancel). 은행 value / 증권 반대 | DART 2019-22 확보 후 장기 재현 |
| mom_12_1 [bank pre vs post 2023] | 2020-22 음 / 2023-26 양 | structural break | 밸류업 추세상승(2023~) momentum continuation | 2nd cycle pristine OOS |
| rev_1m [rate_up vs rate_flat] | rate_up −0.135 / rate_flat +0.069 (증권) | n=28/31 underpowered | 금리상승 국면 reversal 강 | OOS 누적 |
| pbr_z [밸류업 1차 vs 2차] | 1차 CAAR −0.077 / 2차 +0.034 | n=8-9 small | 1차 세미나 무반응 / 2차 가이드라인 re-rating | 후속 정책 event |

★flip-register 원칙: 전부 short-sample(n<30) = ⛔현 vintage 확정 금지. 차기 vintage pristine OOS 재현 시만 승격. 현재 = "관찰 등록"만.

## 📌 자산화 enum 분류

| enum | 후보 | 목적 |
|---|---|---|
| rule | (없음 — 은행 PBR도 DART 2023~ short-sample tentative, rule 승격 보류) | 검증된 정량 규칙 |
| memory | "금융 = sub-sector 부호 이질(은행/보험 금리+ vs 증권 금리−). 은행 저PBR value(IC−) vs 증권 반대(IC+) 차이 = 통합 cross-sectional IC cancel = frame §1.6 분리 의무. ★자기상관 보정(60d overlapping) NW-HAC lag3 t=−2.64 / wc_p=0.0045 / CI 0배제 = 부호 robust(naive t=−3.18은 자기상관 미보정 과대)" | 다음 cycle 자문 prior + sleeve 분리 규칙 |
| memory | "금융 valuation 데이터 = DART 2023~만(IFRS 별도양식). PBR n=27 short-sample. 제조(fnlttSinglAcntAll 충분)와 다름 = 산업별 데이터 양식 차이" | DART 금융 제약 재발 방지 |
| memory | "밸류업 event = 1차 세미나(2024-02-26) 무반응/역행 / 2차 가이드라인(2024-05-02) 저PBR re-rating(+0.076 spread). single event 단정 금지" | 정책 event 부분효과 prior |
| observe-only | 은행 PBR value / rev_1m reversal | DART 장기 확보 + N 누적 후 promotion |
| evt | (G-B 트리거 형식상 충족하나 = M_eff 과대 + sub-sector split 발견 = "약함" 아님. 자문 보류) | promotion-log ERROR 후보 |
| pointer | "★sub-sector 부호 cancel = financial 의 본질. supervisor 통합 시 rate_POS(은행/보험/지주) sleeve vs 증권 sleeve 분리 = portfolio label 결정 1순위" | 다음 세션 SSOT 정독 우선순위 |

## ⚠️ G-B 재자문 트리거 점검 (dispatch §G-B)

- 조건 = BY 생존 0/m **AND** 최강 raw_p > 2×thresh.
- 현황: m=862 BY survivors=[], raw_p_min=0.0005. BY rank1 thresh=0.000016 → 2×=0.000032. **0.0005 > 0.000032 = 형식상 트리거 충족**.
- ★단 (a) **m=862 naive 과대** = sub-sector 6그룹(ALL⊃분리, rate_POS⊃중복 = 같은 종목 4중 계상) × 신호상관(pbr/per·mom_6/mom_12_1) → 실 독립 family ≈ sub-sector 3 × M_eff_signal 3-4 (b) ★**sub-sector split 에서 발견 살아있음**(은행 PBR value t=−3.18, rev_1m OOS 부호유지) = "약함" 아니라 "통합 측정이 cancel" = frame §1.6 구조 발견.
- → 내 판정 = G-B "신호 본질 약함" **부적합**(반도체 family_2 와 동일 논리). cancel 구조 + sub-sector 분리 발견 = 신호 살아있음. M_eff 보정 + sub-sector 분리 박제가 우선. team-lead 에 G-B 자동자문 발동 여부 = "M_eff 과대 + 분리 발견" 근거로 보류 권고.
