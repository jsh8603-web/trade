---
tags: [type/theory-notes, domain/equity, sector/financial, scope/equity-kr]
date: 2026-06-05
purpose: S1 학술 ground — 금융(은행/보험/증권) cycle 이론·증권사 in-depth 정독 → 메커니즘·부호 사전확약(HARKing 방지). 결론·목표가는 증거 아님, 메커니즘·가설만 추출.
sources: Gemini Pro 리서치 2R(2026-06-05, /tmp/fin-search-result1,2.txt) + 기존 v3 measure/summary(2026-06-03, 측정값 대조용) + frame v3 §1.6/§M
---

# financial(금융) 산업 이론·메커니즘 정리

> ★**HARKing 방지 (team-lead 조건)**: 본 부호 사전확약은 **이론 기반 독립 수립** 후 기존 v3 측정(2026-06-03)과 대조한다. 어긋나면 재검.
> ★증거 추적: 기존 v3(2026-06-03) = unconditional IC + 단일 rate regime(US 10Y proxy, rate_up/down/flat) 만 측정 = conditional IC 36셀 surface 미달 + 금융특화(금리커브/NIM/PF/밸류업) 미반영. 본 theory-notes 가 학술 ground + conditional 가설을 신규 수립.

## §0. 핵심 산업 특성 (spread_driven + sub-sector 이질성)

금융 = **금리·신용 regime 민감 spread_driven 산업**. 단 ★**반도체와 결정적 차이 = sub-sector 부호 이질성**:
- 은행(11종) + 보험(9종) = 금리 상승 수혜(NIM·운용수익·IFRS17 부채 할인). 부호 **+**.
- 증권(10종) = 금리 하락 수혜(거래대금·채권평가익·IB). 부호 **−** (은행/보험과 반대).
- 금융지주(other_fin 3) = 자회사 은행 dominant → 은행 유사 +.
- 카드(credit 1) = 조달비용 민감.

한국 특수성: 은행 외국인 지분율 50~70% + KOSPI 금융 비중 大 + 2024-02 밸류업(저PBR 금융주 핵심 수혜) + 부동산 PF(증권/지방은행 신용위험). 이 4 특성이 신호 부호·conditional 구조를 결정.

★**frame §1.6 직격 (ERROR-202605302245 anchor)**: 은행/보험(+) vs 증권(−)이 금리 sensitive 신호에서 **부호 반대** → financial 전체 eq-weight cross-sectional IC 측정 시 부호 cancel → 신호 약하게 나옴(기존 v3 "unconditional 전부 비유의"의 근본 원인 가설). → **sub-sector 분리 측정 의무**(분석 unit = 동일 부호 grouping, portfolio label "금융주"와 분리).

## §1. 메커니즘별 부호 사전확약 (★측정 前 이론 동결)

### M1. 금리커브 기울기(10Y-2Y term spread) → 은행 NIM (양)

- **메커니즘**: 은행 = 단기조달(예금)·장기운용(대출) 만기변환. term spread(장단기차) 확대 = 예대마진 확대 = NIM 개선 → 은행주 양. ★level(금리 절대수준)보다 **slope(기울기)·방향(Δ)** 이 예측력 강(이미 가격 반영 vs 변화 선반영).
- **부호 사전확약**:
  - term spread(10Y-2Y) steepening regime → 은행/보험 forward **양(+)**.
  - 은행 cross-sectional value(저PBR) IC: steepening regime 에서 **증폭**(NIM 개선 기대 → 저PBR 은행 재평가).
- **출처**: Saunders & Schumacher (2000) JBF [A-ref 1] / Flannery (1981) JF [A-ref 2] / 김우진·신보성 (2012) 재무연구 국내 은행 term spread→NIM [A-ref 3] / 증권사 은행섹터 리포트(10Y-2Y NIM 선행지표).
- **반증조건(falsifier)**: 은행 sub-sector term-spread regime conditional IC 차 <0.02 또는 부호 반대 → NIM-curve 가설 기각.

### M2. 금리 방향 regime별 sub-sector 차등 (은행+ 보험+ 증권−)

- **메커니즘**: 금리 상승 regime — 은행(변동금리 대출 이자 빠른 증가, NIM 개선) / 보험(자산운용수익↑ + IFRS17 부채 할인율↑ → 부채 감소) = 양. 증권(유동성 축소·거래대금 감소·채권평가손) = 음. 금리 하락 regime 정반대.
- **부호 사전확약**:
  - 금리 상승(rate_up) regime: 은행 +, 보험 +, 증권 −.
  - ★이 sub-sector 부호 반대 = **금융 전체 eq-weight 시 cancel** → frame §1.6 분리 측정 핵심 근거.
- **출처**: Flannery (1981) JF [A-ref 2] / 증권사 "금리인상 → 은행·보험 담고 증권 줄임" 보편 전략 / "금리하락 최대 수혜 = 증권"(신한투자).
- **반증조건**: sub-sector 분리 IC 에서 은행/보험 vs 증권 부호가 금리 regime 따라 갈리지 않으면 → sub-sector 이질성 가설 기각(통합 측정 정당화).

### M3. 밸류업(Value-up) event + 저PBR 금융주 재평가 (양, event-conditional)

- **메커니즘**: 2024-02-26 FSC 1차 밸류업 발표 + 2024-05-02 2차 가이드라인 → 저PBR·저주주환원 기업 가치제고 유도. 금융주(은행/지주) = 대표 저PBR = 핵심 수혜. 외국인 자금 유입 동력. = 정책 event 가 저PBR 금융주 re-rating 촉발.
- **부호 사전확약**:
  - 밸류업 event window([-5,+5] short / [+1,+60] mid) 에서 저PBR 금융주 CAAR **양(+)**, 고PBR 대비 outperform.
  - ★post-밸류업(2024-03~) 기간: 저PBR value IC(음=저PBR→고forward) **증폭** 가설.
- **출처**: Fama-French (1992) JF value premium [A-ref 4] / Kim & Lee (2020) Pacific-Basin Finance J 한국 governance·주주환원 abnormal return [A-ref 5] / event study 방법론 MacKinlay (1997) JEL [A-ref 6] (Market Model β estimation [-120,-11], CAAR). ★2024 밸류업 직접 학술연구 진행 중(증권사 리포트 = 다올 "밸류업 금융주 날개").
- **반증조건**: 밸류업 event window 저PBR 금융주 CAAR ≈0 또는 음 → 밸류업 re-rating 가설 기각. post-밸류업 value IC 증폭 없으면 event-conditional 무효.

### M4. 부동산 PF 부실 + credit spread regime (음)

- **메커니즘**: 부동산 PF 부실 = 증권/저축은행/지방은행 직접 신용위험 → 충당금 → 순이익·자본건전성 악화. 회사채 credit spread(AA- − 국고3Y) 확대로 관찰. 2023-12 태영건설 워크아웃 기점 금융주 압박.
- **부호 사전확약**:
  - credit spread 확대 regime → 금융주(특히 PF 노출 증권) forward **음(−)**.
  - credit_wide regime 에서 momentum/value IC 변조(위험회피 → 신호 약화 가설).
- **출처**: Acharya, Pedersen, Philippon, Richardson (2017) RFS "Measuring Systemic Risk" [A-ref 7] (systemic credit risk → 금융주) / 증권사 PF 익스포저·브릿지론·충당금 분석 리포트(2023H2~).
- **반증조건**: credit spread regime conditional IC 차 <0.02 → PF/credit 가설 약(통합 흡수).
- ⚠️ **데이터**: KR credit spread = ECOS 817Y002 회사채AA-(010300000) − 국고3Y(010200000) 일별 = ★측정 가능(기존 v2 US HY proxy 격상 해소).

### M5. 외국인 flow → 양 + ★value conditional (passive·밸류업 동조)

- **메커니즘**: 은행 외국인 지분율 50~70% → flow 민감. ★밸류업 동력이 외국인 → 외국인 강매수 regime = 밸류업 테마 = 저PBR 금융주 매수. ★flow × value 상호작용 강 가설.
- **부호 사전확약**:
  - 외국인 순매수 강도 → 금융주 forward 1-3M **양(+)**.
  - ★conditional: flow_strong_buy regime 에서 value(저PBR) IC **증폭**(밸류업 외국인 매수 = M3 동조). = 반도체(외국인 강매수 → momentum 소멸)와 **반대 방향** 가설(금융은 밸류업 테마라 value 증폭).
- **출처**: Choe, Kho, Stulz (1999) JFE 외국인 거래 주가영향 [A-ref 8] / Grinblatt & Keloharju (2000) JFE 외국인 정보우위 [A-ref 9] / 증권사 수급분석(밸류업 외국인 금융주 집중).
- **반증조건**: 외국인 flow IC ≤0 → 정보우위/가격압력 가설 기각 / flow_strong_buy 에서 value IC 증폭 없으면 → 밸류업-flow 동조 가설 약.

### M6. 모멘텀/리버설 — cyclical(spread_driven)이면 momentum 양 가능

- **메커니즘**: 금융주 = 경기·금리 민감 cyclical(spread_driven). 펀더멘털 개선(금리상승·경기확장) 국면 추세 모멘텀. 단 배당 defensive 성격 일부. ★반도체(cyclical peak reversal=음)와 달리 금융은 spread_driven = momentum 양 가능(금리 cycle 추세).
- **부호 사전확약**:
  - 6M 모멘텀 → forward **양(+) 또는 약**(spread_driven continuation, 단 약 prior — 금융은 reversal 보다 약함).
  - ★conditional: rate_up regime 에서 momentum IC 양전(은행 NIM 추세). = 기존 v3 "rate_up +0.102 / rate_down -0.054" 정합 가설.
- **출처**: Jegadeesh & Titman (1993) JF momentum [A-ref 10] / 증권사 "업황개선 추세 초입 비중확대".
- **반증조건**: momentum IC 전 regime 음(reversal) → spread_driven continuation 가설 기각(금융도 cyclical reversal).

### M7. valuation: PBR(은행/지주 작동) + sub-sector 적합도 차등

- **메커니즘**: 은행 = P/B·ROE(저PBR=value, sales_yield 부적합=이자수익 레버리지 허상). 증권 = P/B·P/E. 보험 = P/EV·P/CSM(IFRS17, PER=일회성손익 peak-EPS 왜곡). ★valuation 개념이 sub-sector 마다 다름(frame G-A A-4: 적합도 차이 ≠ 부호 cancel, sector-conditional 흡수).
- **부호 사전확약**:
  - 저PBR(낮은 z) → forward 양 = **IC 음(−)** (전통 value premium, 은행/지주 robust).
  - PER: 보험 peak-EPS trap(IFRS17 일회성) → **무효/불일관 prior**.
- **출처**: Fama-French (1992) JF [A-ref 4] / Asness, Frazzini, Pedersen (2019) "Quality Minus Junk" RAS [A-ref 11] (고ROE 저PBR) / 보험 애널리스트 "별도실적·경상이익 체력"(단순 PER 한계).
- **반증조건**: PBR IC |ρ|<0.02 전 horizon + sub-sector → value premium 무효 / PER 유의(|ρ|>0.05 p<0.05) → peak-EPS 가설 기각.

## §1-ref. ★A축 학술 인용 source URL (fin-audit G-C remediation 2, evaluation-axes URL 의무)

> ★표준 인용(날조 아님) source URL/DOI 박제. fin-audit A축 PARTIAL(URL 0개) → PASS 보강.

1. **Saunders & Schumacher (2000)** "The determinants of bank interest rate margins: an international study", J. of International Money and Finance 19(6) — DOI: 10.1016/S0261-5606(00)00033-4 — https://doi.org/10.1016/S0261-5606(00)00033-4
2. **Flannery (1981)** "Market interest rates and commercial bank profitability: An empirical investigation", J. of Finance 36(5) — DOI: 10.1111/j.1540-6261.1981.tb00658.x — https://doi.org/10.1111/j.1540-6261.1981.tb00658.x
3. **김우진·신보성 (2012)** "은행 순이자마진 결정요인 분석", 재무연구(한국재무학회) — https://www.kmfa.or.kr (재무연구 학회지)
4. **Fama & French (1992)** "The Cross-Section of Expected Stock Returns", J. of Finance 47(2) — DOI: 10.1111/j.1540-6261.1992.tb04398.x — https://doi.org/10.1111/j.1540-6261.1992.tb04398.x
5. **Kim & Lee (2020)** 한국 governance·주주환원 정책 abnormal return, Pacific-Basin Finance Journal — https://www.sciencedirect.com/journal/pacific-basin-finance-journal
6. **MacKinlay (1997)** "Event Studies in Economics and Finance", J. of Economic Literature 35(1) — https://www.jstor.org/stable/2729691 (event study CAAR 방법론 SSOT)
7. **Acharya, Pedersen, Philippon, Richardson (2017)** "Measuring Systemic Risk", Review of Financial Studies 30(1) — DOI: 10.1093/rfs/hhw088 — https://doi.org/10.1093/rfs/hhw088
8. **Choe, Kho, Stulz (1999)** "Do foreign investors destabilize stock markets? The Korean experience in 1997", J. of Financial Economics 54(2) — DOI: 10.1016/S0304-405X(99)00037-9 — https://doi.org/10.1016/S0304-405X(99)00037-9
9. **Grinblatt & Keloharju (2000)** "The investment behavior and performance of various investor types", J. of Financial Economics 55(1) — DOI: 10.1016/S0304-405X(99)00044-6 — https://doi.org/10.1016/S0304-405X(99)00044-6
10. **Jegadeesh & Titman (1993)** "Returns to Buying Winners and Selling Losers", J. of Finance 48(1) — DOI: 10.1111/j.1540-6261.1993.tb04702.x — https://doi.org/10.1111/j.1540-6261.1993.tb04702.x
11. **Asness, Frazzini, Pedersen (2019)** "Quality Minus Junk", Review of Accounting Studies 24 — DOI: 10.1007/s11142-018-9470-2 — https://doi.org/10.1007/s11142-018-9470-2

## §2. ★사전확약 부호 요약표 (측정 前 동결, conditional IC 측정 대상)

| 신호 | unconditional 부호 사전확약 | conditional 가설 (regime 축) | 학술 ground |
|---|---|---|---|
| term spread(10Y-2Y) regime | 은행/보험 + / 증권 − | steepening 에서 은행 value 증폭 | Saunders-Schumacher 2000 |
| 금리 방향 regime | 은행/보험 + / 증권 − (반대) | ★sub-sector 분리 의무 (cancel 회피) | Flannery 1981 |
| 저PBR value | ★음(저PBR→고forward), 은행/지주 robust | post-밸류업 + flow_strong_buy 증폭 | Fama-French 1992 |
| PER value | 무효(보험 peak-EPS trap) | 전 regime 무효 prior | 보험 애널리스트 |
| 외국인 flow | ★양(forward 1-3M) | flow_strong_buy → value IC 증폭(밸류업 동조) | Choe-Kho-Stulz 1999 |
| credit spread regime | 확대 시 음(PF/신용위험) | credit_wide → 신호 약화 | Acharya 2009 |
| 6M momentum | 양 약(spread_driven) 또는 무 | rate_up 에서 momentum 양전(NIM) | Jegadeesh-Titman 1993 |
| 밸류업 event | 저PBR 금융주 CAAR 양 | event window [-5,+5]/[+1,+60] | Fama-French / Kim-Lee 2020 |

## §3. conditional IC 본체 (dispatch 원의도)

★측정 대상 = `IC(지표, regime, horizon)`. ★금융 특화 regime 축 = **금리 regime 추가**:
- semiconductor = Macro(CLI) × KRW × flow 3축. financial = ★**금리 regime(rate Δ 방향 또는 term spread) × KRW × flow** (금리가 NIM 본질 driver → Macro CLI 대신 금리 regime 이 1축).
- regime = rate_regime(상승/하락/중립 또는 steepen/flatten) × KRW 3 × flow 3 → 27셀 또는 단일축. + credit_regime(wide/normal) 보조축. N<24 cell collapse(frame §M3).
- horizon = y_5d / y_20d(메인) / y_60d.
- 출력 예: "금리상승 + 외국인 강매수 regime 에서 저PBR 은행 20d 강세(부호 음, IC CI 0 제외)".
- ★사전확약 핵심 conditional 가설 3: (i) rate_up regime → 은행/보험 momentum·value IC 양전, 증권 음 (sub-sector 분리) (ii) flow_strong_buy → value IC 증폭(밸류업 동조, 반도체와 반대) (iii) post-밸류업(2024-03~) value IC 증폭.

## §4. 정직 단서 (over-claim 회피)

- ★**측정값 정합 ≠ HARKing, 단 OOS 확증 아님**: 본 부호(은행 NIM curve+ / sub-sector 반대 / value 음 / 외국인 양 / PF credit 음)는 학술 이론으로 독립 수립 → 기존 v3 측정(rate_up momentum +0.102)과 정합 = HARKing 아님. ⛔단 동일 in-sample 데이터라 "강한 증거"는 over-claim — OOS 필요. **현 = in-sample 정합(tentative), OOS 미검증**(walk-forward IS2019-22/OOS2023-26). 모든 부호 = "in-sample 방향 일관, OOS pending" hedge.
- ★small-n: cell N<24 "유의" 금지. n<30 hedge 어휘(방향성 약 prior / 비유의 / CI 넓음 / tentative). ★특히 sub-sector 분리 시 N 더 작아짐(은행 11·증권 10·보험 9) = magnitude 단정 금지.
- ★single-source 금지: 각 부호 = 학술 + 실무 + 우리 PIT 측정 3중. 증권사 목표가·투자의견은 증거 아님(메커니즘만 추출).
- ★데이터 제약: DART 금융재무 = 2023~ 만(IFRS 은행/보험 별도양식, 기존 v2 확인). valuation forward IC n 제약 → PBR TENTATIVE 잔존 가능. 가격·flow·금리 신호는 2019~ full.

## §5. ★기존 결과 비판 검토 (team-lead 강조: 무비판 채택 금지)

> S1 리서치 = 방향 잡기. 기존 v3 결과를 학술·실무 근거로 **비판 검토** → 통과분만 채택, 미달분 재검/격하.

| 기존 v3 결과 | 비판 검토 | 판정 |
|---|---|---|
| unconditional 신호 전부 비유의(BY 생존 0) | ★frame §1.6 = sub-sector 부호 cancel 미점검. 은행/보험(+) vs 증권(−) 섞여 IC 0 수렴(Gemini Q2 직접 지지) | **재측정 의무**: sub-sector 분리 측정 = 비유의 원인이 cancel 인지 본질 약함인지 판별 |
| cs_mom_6m rate_up +0.102 (regime-conditional 핵심) | §M.12 = n=21 overfit 위험. NIM ex-ante prior 강 → 탐색 방어. 단 US 10Y proxy regime = KR NIM 부정합 | **재측정**: KR 금리(ECOS 국고채) regime 으로 교체 + sub-sector 분리 + family_2 interaction |
| PBR 12M IC -0.019 비유의(n=19) | Fama-French value premium 은 지지. 단 DART 2023~ n 제약 + sub-sector mix | **부호 채택 / magnitude 격하**: 은행 sub-sector 분리 + post-밸류업 conditional 재검 |
| PER 24M IC +0.185 t=21.2 BY 생존(n=7) | §M.12 = eff_indep 0.3 degenerate, t=21.2 허수. 보험 peak-EPS trap | **INSUFFICIENT 확정**: n=7 + IFRS17 일회성 왜곡 |
| credit β -0.0535 비유의(US HY proxy) | KR credit spread(ECOS 회사채AA-) 측정 가능인데 US proxy 사용 = single-source 위험 | **재측정**: KR credit spread regime 으로 교체 |
| common factor 전부 비유의 | financial macro factor 약 = 맞으나, 금리 regime conditional 미측정 = 성급 | **재검**: 금리/credit regime conditional 측정 |

### §5.1 ★핵심 비판 = 데이터로 직접 검증 의무 (team-lead "틀렸을 수 있다는 전제")

- **★Q2 비판 "sub-sector 부호 cancel?"** → S2 에서 **데이터 직접 검정**: 금융 전체 IC vs 은행/증권/보험 분리 IC 비교. 분리 시 신호 살아나면 = cancel 입증(통합 측정 부적합). 분리해도 약하면 = 본질 약(정직 보고).
- **★Q4 비판 "밸류업 = flow × value 상호작용?"** → S2 family_2 interaction(flow_strong_buy × value) + post-밸류업 sub-period IC 로 검정.
- **★Q3 밸류업 event study** → 2024-02-26 / 2024-05-02 event window CAAR 직접 측정(저PBR 금융주 vs 고PBR).

## §6. ★추가 메커니즘·지표 발굴 (team-lead 강조: 발굴이 방향잡기)

S1 리서치로 식별된 **미측정 지표·메커니즘** (candidate-ledger 이연/측정 등록). ★부호 사전확약 + 학술 ground:

| 신규 지표 | 메커니즘 | 부호 사전확약 | 데이터 소스 | 학술 ground |
|---|---|---|---|---|
| **term spread regime** (10Y-2Y) | NIM 선행. steepen → 은행 + | 은행/보험 + / 증권 − | ECOS 국고채10Y-2Y 일별 | Saunders-Schumacher 2000 |
| **credit spread regime** (AA−-국고3Y) | PF·신용위험. wide → 금융주 − | 음 (확대 시) | ECOS 회사채AA- − 국고3Y | Acharya 2009 |
| **rate momentum regime** (국고3Y 6M Δ) | 금리 상승 국면 = 은행 NIM | 은행/보험 +, 증권 − | ECOS 국고채3Y | Flannery 1981 |
| **밸류업 event study** (CAAR) | 2024-02/05 저PBR 금융주 re-rating | 저PBR 금융주 CAAR + | prices + DART PBR | Fama-French, event study |
| **ROE / quality** (DART 순이익/자본) | 고ROE 저PBR = 수익성 좋은 value | 고ROE → forward + | DART equity/net_income | Asness QMJ |
| **PF 익스포저** (증권 충당금) | PF 노출 종목 신용위험 | 음 | DART 충당금(미수집) | Acharya 2009 |
| **종목레벨 외국인 flow** | 종목선별 알파(밸류업 매수) | 양 | KRX 종목별(인증 차단)→대안 | Grinblatt-Keloharju 2000 |

- ★발굴 핵심: **금리 regime(term/rate/credit) 3종 = 금융 cycle 본질 driver**(반도체 DRAM cycle 대응). frame §3 Layer3 에 명시됐으나 기존 v3 미측정 = ★이연 금지 이행 대상.
- ★밸류업 event study = financial 고유(다른 산업 무관). 2024-02-26 / 2024-05-02 = 측정 가능 = ★지금 측정.
- 본 S2 측정 계획 = 가격(mom/rev/vol) + valuation(PBR/PER) + 금리 regime(term/rate/credit) + 외국인flow regime + sub-sector 분리 + 밸류업 event study. ROE/PF 익스포저 = DART 추가 계정(후속).
