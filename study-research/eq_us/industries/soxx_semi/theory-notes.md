---
tags: [type/theory-notes, domain/equity-us, sector/soxx_semi, phase/sector-granular, status/active]
date: 2026-06-08
purpose: SOXX(미국 반도체) R1 학술 ground — within-sector value-selection(primary) + semi cycle timing(secondary, falsify 방향) + 미국 regime 축 재설계. 자문 복붙 아님, Gemini 2-Phase 리서치 + 인용 환각검증(E축) + FRED series id 실존검증.
sources: >
  Gemini Pro 2-Phase 리서치 4건 (raw: C:/msys64/tmp/soxx-r1-result{1,2,3,4}.txt) + 인용 교차검증
  + FRED CSV endpoint series id 실존검증 (2026-06-08) + 기존 us_cyclical theory-notes (prior 흡수)
ssot_prior: [eq_us/industries/us_cyclical/theory-notes.md (peak-EPS / asset-growth / credit-regime prior 흡수)]
---

# SOXX(미국 반도체) 이론 노트 (R1 학술 ground)

> ★핵심 framing (자문 3R 수렴 + R1 보강): **진짜 엣지 = within-sector value-selection(ρ 채널)**. rotation/timing(κ)은
> ~30% 회의적 = **falsify 대상**. 본 노트는 (1) value premium 학술 토대·반도체 적용성·한계, (2) semi cycle
> lead 지표의 lead/lag 실증(κ falsify 강화) + 대체 lead 검증, (3) 한국↔미국 구조 차이 + 미국 regime 축 재설계,
> (4) 추가 신호 후보 + 사전등록 반증조건을 박제한다.

---

## ★0. R1 보강 핵심 결론 요약 (3-5줄)

1. **value premium 작동 가능, 단 within-semiconductor 에선 "value+quality 결합" 이 필수** — 단순 저PER/저PBR =
   value-trap(Intel legacy vs NVDA leading-edge). EV/EBITDA 가 peak-EPS trap 에 상대적으로 강건(Damodaran 실무 통설).
   ⛔ 단 "EV/EBITDA 최강" 은 single-source 실무 통설 = R3 본인 실측 의무.
2. **H2(κ, book-to-bill timing) falsify 강화 확인** — 다수 출처가 "SOX 주가가 book-to-bill 을 **선행**(주가 leading)"
   에 수렴. SEMI bookings 2016 종료 / billings 2022 월별 무료공개 단절 = 데이터 가용성도 사망. ★대체 lead(대만/한국 수출)
   도 **leading 아니라 coincident** = κ 전반 약. ★단 이건 자문 통설 수렴 = 본인 forward-IC 실측으로 재확인 의무.
3. **미국 regime 축 = 한국 KRW_weak 직접이식 불가** — 미국 후보 = (i) 실질금리/DFII10(long-duration growth
   할인율, Lettau-Wachter 2007) (ii) HY credit spread(risk-on/off, Fama-French 1989) (iii) dollar(약, Bruno-Shin
   US large-cap 도달 약). primary 가설 = 실질금리·credit 2축.
4. **★sub-industry 이질성 = 측정 1급 오염원** — 팹리스/메모리/장비/아날로그 비즈니스모델 상이 → R&D·Capex 신호가
   "style bias(팹리스 vs non-팹리스)" 대리 위험. N≈12 small-N + sub-industry dummy 통제 자유도 부재 = 결정적 한계.
5. **★E축 환각 적발(아래 §6)**: Gemini 가 제시한 FRED series id 중 **3건 날조**(TWNEXPCESEMIT/KORXTOTLSEMISME/SINI =
   모두 404) + UMCSENT 라벨오류. collector_plan 박제 전 실존검증 필수 = 본 노트가 그 검증 수행.

---

## 1. Value premium 학술 토대 + 반도체 적용성 (primary, ρ 채널)

### 1.1 핵심 인용 (저자·연도·저널, ★환각검증 표기)

| 인용 | 출처 | 환각검증 | 반도체 적용 |
|---|---|---|---|
| HML value factor | Fama-French (1992) *J.Finance* "Cross-Section of Expected Stock Returns" + (1993) *JFE* "Common risk factors" | ✅ CONFIRMED (표준 인용) | book-to-market value premium 기반 |
| Quality Minus Junk | Asness-Frazzini-Pedersen (2019) *JFE* "Quality Minus Junk" (초기 2013 AQR WP) | ✅ CONFIRMED (저널·연도 정합) | high-growth 반도체에 value 단독 부족 → quality 결합 |
| Gross Profitability | Novy-Marx (2013) *JFE* 108(1) "The Other Side of Value: The Gross Profitability Premium" | ✅ CONFIRMED (기존 us_cyclical 노트와 동일 박제) | GP/Assets 양, value 와 음상관 = 분산 |
| Fact/Fiction Value | Asness-Frazzini-Israel-Moskowitz (2014) AQR White Paper (★학술저널 아님, 운용사 리서치) | ⚠️ 저널 아님 명시 — **within-industry value 유효** 주장은 WP 근거 (peer-review 아님) | 산업 내 상대 value 작동 주장의 1차 근거 (단 학술 weight 낮음) |
| Duration-based value | Lettau-Wachter (2007) *J.Finance* "Why Is Long-Horizon Equity Less Risky? Duration-Based Explanation of Value Premium" | ⚠️ **재확인 필요** (제목·연도 Gemini 제시, peer 교차검증 1회 권장 R2) | growth=long-duration → 금리 민감, regime 축 §3 연결 |

★**미검증 인용 (R2 cross-verify 의무, 환각 의심)**:
- "Asness-Porter-Stevens (2000) Predicting Stock Returns Using Industry-Relative Firm Characteristics (WP)" — within-industry
  value 실증 근거로 Gemini 인용. ★제목·저자 그럴듯하나 **미확인** → R2 검증 전 박제 금지.
- "Cohen-Polk-Vuolteenaho (2003) The Value Spread *J.Finance*" — value spread 가설. ★연도·저널 미확인 → R2 검증.

### 1.2 ★반도체 내 value 의 핵심 위험 = value-trap (Intel vs NVDA)

- 반도체 = cyclical + high-growth + capex-intensive. 상승기 = growth/momentum 지배. 단 그 변동성이 over/under-shooting
  → value 기회 창출(자문 주장, 통설). ★단 **저multiple = value-trap 위험 高** (기술경쟁 탈락·구조성장 상실 기업이 싸 보임).
- 사례: Intel(저PER·고배당 = 전통 value 처럼 보였으나 DC 점유율 상실·AI 경쟁력 붕괴 = 펀더멘털 악화 반영) vs
  NVDA(항상 고밸류, AI 성장으로 정당화). → ⛔ value 단독 = 위험, **quality(ROIC/마진/moat) 결합 필수**.
- ★peak-EPS trap (기존 us_cyclical 노트 §0 흡수): 사이클 정점 EPS 高 → PER 低 함정. 트로프 적자 → PER 무용.
  → balance-sheet 기반(P/B, asset growth) + sales 기반(Sales/Price) + EV/EBITDA(D&A 전 = capex 중립) 가 peak-EPS 면역.

### 1.3 valuation metric 선택 (사전 가설, R3 실측 falsify 대상)

| metric | predicted | 논리 | ★주의 |
|---|---|---|---|
| EV/EBITDA | ★primary | D&A 전 이익 = capex 중립 + 부채 포함 = 재무구조 중립. cyclical 통설 best | single-source 실무 통설(Damodaran) = R3 본인 IC 측정 의무 |
| P/B | 보조 | capex/R&D 大 → 장부가 무형자산 미반영 단 사이클 변동 면역 | 한국 반도체 pbr_z IC −0.114 (BY 생존) = 대응 prior |
| Sales/Price (1/PSR) | 보조 | 트로프 적자에도 매출 capacity = 진짜 value | Barbee-Mukherji-Raines (1996) FAJ. 수익성 미반영 한계 |
| PER | ✗ 회의 | peak-EPS trap | 한국 반도체 PER 전 horizon 비유의(peak-EPS 실증) = 대응 |

---

## 2. Semi cycle timing (κ, secondary) — ★falsify 방향 강화

> ★결론 선언: 자문 다수 출처가 **"book-to-bill 류 업황지표가 주가를 선행한다"** 가설을 **기각** 에 수렴. 오히려
> 주가(SOX)가 지표를 수개월 선행. = H2(κ) falsify 강화. ★단 이건 자문 통설 = R3 본인 forward-IC 실측으로 재확인.

### 2.1 book-to-bill — lead/lag 실증 + 데이터 사망

- **lead/lag**: ★**coincident-to-lagging** (주가가 book-to-bill 선행). 2000년대 이후 시장참여자가 채널체크로 선반영
  → 지표 선행성 소멸. book-to-bill 1 하회 피크아웃 신호 전 주가 이미 고점. = "뉴스 아닌 확인" (자문 통설).
- **데이터 가용성 사망** (★내 사전조사 H2 caveat 확인):
  - SEMI North America **bookings = 2016-12 마지막**으로 월별 공개 중단 → book-to-bill(=bookings/billings) 계산 불가.
  - billings = 2022~ global 분기 발표 + 월별은 유료 구독 only → 무료 월별 시계열 단절.
  - → ★book-to-bill = **유효한 공개 선행지표 아님**. round-1.md H2 collector_plan "SEMI(유료?)" 의문 = 확정 = drop.

### 2.2 WSTS billings — 명백한 lagging

- billings = "실제 발생 매출" 집계 결과 → 변곡점이 주가보다 3~6M 후행. PIT 지연 ~2M(5월 데이터 7월초 발표) = 실시간 부적합.
- 무료 = SIA 요약 차트(월별). 상세 국가/제품별 = WSTS 유료.

### 2.3 대체 lead 후보 검증 — ★대부분 coincident (leading 아님)

| 후보 | lead/lag | PIT 지연 | 가용성 | ★FRED id 검증 |
|---|---|---|---|---|
| 대만 반도체수출 / TSMC 월매출 | **coincident** (월별 중 선행성 최고이나 SOX 수개월 선행 아님) | TSMC 월매출 ~10일 / 대만수출 ~7-10일 (★빠름) | 무료 (TSMC IR / 대만 재정부) | ⛔ `TWNEXPCESEMIT` = **404 날조** |
| 한국 반도체수출 (관세청 잠정) | **coincident** (메모리 업황 직접) | ★전세계 최速: 1-10일치 매월11일 / 1-20일치 21일 / 월간 익월1일 | 무료 (관세청) | ⛔ `KORXTOTLSEMISME` = **404 날조** |
| 반도체 재고/출하비율 | coincident-to-lagging | US Census ~6-8주 | 무료 (FRED) | ⛔ `SINI` = **404 날조** / 실존 = `ISRATIO`(전 제조, 반도체 비특정) |
| DRAM/NAND 현물가 | **highly coincident** (메모리주 일부 선행) | 거의 없음 (일별) | 유료 (TrendForce/DRAMeXchange) | FRED 미제공 (id 없음 = 정직) |

★**핵심 함의**: κ 채널의 "선행" lead 후보가 모두 coincident → H2 predicted_sign(+, lagged→forward) 의 **lagged 선행성
자체가 의심**. eff_N≈1(3MMA 평활 시) + coincident = κ 단독 graduation 사실상 불가. ★단 "coincident contemporaneous
신호"로서 regime conditioning 변수 가치는 별도(한국 반도체 dram_asp_ppi 가 regime conditioner 로 재배치된 패턴 대응).

### 2.4 ★실존 FRED 후보 (R2 fetch 대상, 환각 제거 후)

- 반도체 PPI: `PCU33443344` (✅ 실존) — 한국 반도체 dram_asp_ppi 와 대응, timing/regime conditioner 후보.
- 신규주문(일반 제조, 반도체 비특정): `A34SNO` (✅ 실존, 단 반도체 특정 아님 = κ 부적합).
- 재고/출하: `ISRATIO` (✅ 실존, 전 제조업) — 반도체 특정 시리즈는 무료 FRED 부재.
- ★한국·대만 수출 반도체 특정 = 무료 FRED 부재 확정 → 관세청/대만 재정부 직접 fetch (R2 PoC) 또는 drop.

---

## 3. 미국 regime 축 재설계 (한국 KRW_weak 직접이식 불가)

### 3.1 한국 ↔ 미국 구조 차이

| 항목 | 한국 (삼성/SK) | 미국 (SOXX 12종) |
|---|---|---|
| 모델 | 메모리 IDM (DRAM/NAND commodity) | 다각화 (팹리스 NVDA/AMD/QCOM + 장비 LRCX/KLAC/AMAT + 아날로그 TXN/ADI + 메모리 MU + IDM INTC) |
| cyclicality | 메모리 수급 (negative feedback) | 복합 (AI capex + consumer + industrial) |
| ★AI reflexivity | 약 | ★강 (NVDA/AVGO 시총지배 → 하이퍼스케일러 capex positive feedback, Soros reflexivity) |
| 환율 | ★KRW_weak = 실적개선 직접신호 | dollar = 여러 요인 중 하나, 영향 제한 |

### 3.2 미국 regime 축 우선순위 (사전 가설, R3 falsify)

1. **실질금리 / DFII10 (primary, valuation 압박)**: 반도체 growth = long-duration asset → 미래 CF 의존 → 실질금리=할인율.
   상승 시 valuation 압박. 학술 = Lettau-Wachter (2007) duration-based value premium (★R2 재확인). 2022~ 금리변동기 설명력 高.
   FRED `DFII10` ✅ 실존 (macro.parquet rate10y 보유).
2. **HY credit spread (primary, risk sentiment)**: spread 확대(risk-off) = cyclical 반도체 약세(고베타·earnings 변동·다운턴
   민감). 학술 = Fama-French (1989) *JFE* default spread 예측력 (✅ 기존 us_cyclical 노트 동일 박제). ★데이터 = `BAMLH0A0HYM2`
   ✅ 실존 단 **2023-05~ 37mo only**(us_cyclical 노트 §2.1 실측 = macro.parquet hy_oas 805 obs 일별 정합) → 장기 regime
   불가. ★대체 = **Baa-Aaa** (`BAA`✅ + `AAA`✅ 실존, macro.parquet baa_aaa 3468 obs = 월별 장기) = us_cyclical 채택 winner 흡수.
3. **dollar (secondary filter, 약)**: 해외매출 환산역풍. ★단 Bruno-Shin (2015) 메커니즘 = EM/sovereign → US large-cap 도달
   약(자문·R2 정합). 기존 us_cyclical dollar β = −0.228 t=−1.02 **비유의** 흡수. = 2차 필터, primary regime 아님. `DTWEXBGS` ✅ 실존.

★사전 가설: within-sector value 신호를 가장 잘 conditioning = **실질금리(rate10y 4분위) × credit(Baa-Aaa/HY 4분위)** 2축.
한국의 KRW3×flow3 (36셀) → 미국 Macro4×HY4×dollar2 (32셀, GUIDE M3 정합). ⛔ N≥24 cell gate (한국에서 36셀 full 0개 = collapse).

### 3.3 AI capex reflexivity = 측정 1급 함정

- 2023-2026 AI 랠리 = 표본 지배 → episode-dependence/overfitting 위험. NVDA/AVGO momentum 이 全 팩터 압도 = AI 꺾이면 무용.
  → ★IS(2010-2021)/OOS(2022-2026) walk-forward 필수(M4 OOS CPCV), regime 사전지정(forking-paths 방화벽).
- hyperscaler capex: **guidance = 주가 coincident** (발표 즉시 반영), 실집행 capex = lagging. → capex guidance 도 leading 아님
  = κ 보강 불가. (단 consensus 대비 surprise 의 변화 = 별도, IBES 유료 = 이연).

---

## 4. 추가 신호 후보 + 사전등록 반증조건 (predicted_sign 고정)

### 4.1 신호 후보 (기존 prior 4 + 신규, predicted_sign)

| 신호 | predicted_sign | 학술 (저자·연도·저널) | 환각검증 | 반도체 논리 |
|---|---|---|---|---|
| value (저PBR/저EV-EBITDA) | **음** (cheap→fwd+) | Fama-French (1992/93) | ✅ | primary. 한국 pbr_z −0.114 대응 |
| gross profitability (GP/A) | **양** | Novy-Marx (2013) JFE | ✅ | quality, value 와 음상관 |
| asset growth (Assets YoY) | **음** | Cooper-Gulen-Schill (2008) J.Finance | ✅ (us_cyclical 박제) | capital cycle, capex boom-bust |
| sales/price (1/PSR) | **양** | Barbee-Mukherji-Raines (1996) FAJ | ✅ (us_cyclical 정정 박제) | peak-EPS 면역 value |
| **R&D intensity** (R&D/Sales) | **음** | Chan-Lakonishok-Sougiannis (2001) J.Finance | ⚠️ R2 재확인 | glamour 과대평가 → fwd− (Asset Growth 유사). ★sub-industry style bias 위험(팹리스 상위 쏠림) |
| **capex intensity** (Capex/Assets) | **음** | = Asset Growth 하위 (Cooper-Gulen-Schill) | ✅ | capital cycle. ★메모리/IDM 상위 쏠림 = style bias 위험 |
| **margin level+momentum** | **양** | Novy-Marx (2013) + QMJ | ✅ | leading-edge vs commoditized 변별 |
| **quality (ROIC, low leverage)** | **양** | Asness-Frazzini-Pedersen (2019) QMJ | ✅ | 자본집약·기술변화 산업 생존 |
| **momentum (12-1)** | **양** (★한국 reversal 과 반대 가설) | Jegadeesh-Titman (1993) J.Finance | ✅ | 미국 기관 중심 = momentum 작동 가설. ★단 한국 반도체 = reversal(음) → 부호 검정이 핵심 falsifier |
| **low vol / BAB** | **음** (저β→fwd+) | Frazzini-Pedersen (2014) JFE | ✅ | 섹터 내 저변동(TXN/MCHP) vs 고변동(NVDA/AMD) |

### 4.2 ★사전등록 반증조건 (공통, 모든 신호)

1. **부호 불일치**: 장기 월별 IC 평균 부호가 predicted_sign 반대 + 유의(|t_NW|>2) → 기각.
2. **유의성 부재**: IC 95% CI 가 0 포함 → 기각 (점추정 박제 금지).
3. **★MDE 미달**: mean(|Rank-IC|) < **0.107** (small-N N≈12-30 MDE) → dead-on-arrival 기각. ★value pool −0.117 = 경계.
4. **OOS 부호반전**: IS/OOS 분할 후 OOS IC 부호가 predicted_sign 반대 → 기각 (forking-paths/overfitting 차단).
5. **momentum 특칙**: predicted_sign=양 사전고정 → 한국처럼 음(reversal) 유의 시 = predicted 반대 = ★기각 (부호 검정 = pilot 핵심 가치).

### 4.3 ★small-N 검정력 한계 (결정적 caveat)

- N=12 단일 월 cross-section: Rank-IC SE ≈ 1/√(N−1) = 1/√11 ≈ **0.302** → 단월 유의(t>2) 위해 IC>0.6 필요 = 비현실.
  → ★**검정력은 시계열에서** (수십~수백 개월 IC 평균의 Fama-MacBeth t / Newey-West). round-1.md M1 정합.
- ★**sub-industry 이질성 = 1급 오염**: Capex/Assets 순위 = 항상 메모리/IDM 상위 + 팹리스 하위 = "팹리스 vs non-팹리스
  비즈니스모델 팩터" 대리 (alpha 아님). R&D/Sales = 팹리스 상위 쏠림. → ★**sub-industry-neutral z (산업내 정규화)** 또는
  dummy 통제 필요하나 N=12 자유도 부재 = 사실상 불가. → ★측정 시 style-bias 인지 + 부분측정 small-N hedge 의무.

---

## 5. R2 진입 의제 (collector_plan 정정 + 검증 latch)

- ★**환각 id 제거**: round-1.md H2 / collector_plan 에 TWNEXPCESEMIT/KORXTOTLSEMISME/SINI 박제 금지 (404 날조 확정).
- value/quality fundamental = EDGAR 10-K/Q PIT (edgar_fundamentals.parquet 재사용, filed 컬럼 PIT). EV/EBITDA = 부채/현금
  계정 추가 fetch (한국 반도체 collector_plan high 대응).
- regime 축 = DFII10(rate10y) + Baa-Aaa(BAA/AAA 장기) + HY OAS(37mo, 단기 보조) + dollar(2차) — macro.parquet 보유 확인.
- ★생존편향(I축 hard-fail): 현 12종 = 현 holdings → CRSP delisting / S&P semi historical membership 보강 (XLNX 피인수 등 누락).
- κ(book-to-bill) = drop 또는 PCU33443344(반도체 PPI) regime conditioner 재배치. 한국·대만 수출 = 관세청/재정부 직접 fetch PoC.

---

## 6. ★E축 환각검증 로그 (인용·FRED id 실존 박제)

### 6.1 FRED series id 실존검증 (2026-06-08, fredgraph CSV endpoint http code)

| id | Gemini 라벨 | http | 판정 |
|---|---|---|---|
| `TWNEXPCESEMIT` | 대만 전자부품 수출 | **404** | ⛔ 날조 (환각) |
| `KORXTOTLSEMISME` | 한국 반도체 수출 | **404** | ⛔ 날조 (환각) |
| `SINI` | 반도체 재고/출하 | **404** | ⛔ 날조 (환각) |
| `UMCSENT` | "반도체 출하액" 주장 | 200 | ⚠️ 실존하나 = Univ.Michigan Consumer Sentiment (라벨 오류=환각) |
| `NAPM` | ISM Mfg PMI | **404** | ⛔ discontinued (환각, 현 PMI 별 id) |
| `BAMLH0A0HYM2` | HY OAS | 200 | ✅ 실존 (단 2023-05~ 37mo, macro.parquet 805 obs 정합) |
| `BAA` / `AAA` | Baa/Aaa corp yield | 200/200 | ✅ 실존 (Baa-Aaa 장기 proxy = macro.parquet baa_aaa) |
| `ISRATIO` | 제조 재고/출하 | 200 | ✅ 실존 (전 제조, 반도체 비특정) |
| `PCU33443344` | 반도체 PPI | 200 | ✅ 실존 (regime conditioner 후보) |
| `A34SNO` | 신규주문 | 200 | ✅ 실존 (일반 제조, 반도체 비특정 = κ 부적합) |
| `DFII10` / `DTWEXBGS` | 실질금리 / broad dollar | 000(timeout) | ✅ 실존 (404 아님, 일별 대용량 timeout. macro.parquet rate10y/dollar 보유 = us_cyclical 검증) |

### 6.2 학술 인용 환각 상태

- ✅ CONFIRMED: Fama-French(1992/93), Novy-Marx(2013 JFE), Asness-Frazzini-Pedersen(2019 JFE QMJ), Cooper-Gulen-Schill(2008
  J.Finance), Jegadeesh-Titman(1993), Frazzini-Pedersen(2014 JFE BAB), Fama-French(1989 default spread) — 표준 인용 + 기존
  us_cyclical 노트 교차.
- ⚠️ R2 재확인 의무: Lettau-Wachter(2007 duration value), Chan-Lakonishok-Sougiannis(2001 R&D), Barbee-Mukherji-Raines(1996 FAJ).
- ⛔ R2 검증 전 박제 금지: Asness-Porter-Stevens(2000 WP), Cohen-Polk-Vuolteenaho(2003 Value Spread) — within-industry value
  핵심 근거이나 미확인 → R2 cross-verify 통과 전 yaml prior 박제 금지.
- AQR Fact/Fiction(2014) = ★학술저널 아님(운용사 WP) 명시 = within-industry value 주장의 peer-review weight 낮음.
