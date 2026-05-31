---
tags: [type/consult-brief, domain/inv, study/eq_us, phase/3-R1]
date: 2026-05-30
study_id: eq_us
round: 1
target_channels: [gemini-web, claude-web]
parallel: true
brief_format: self-contained (4-section, 외부 모델 컨텍스트 무필요)
---

# eq_us — Phase 3 R1 자문 브리핑 (4 섹션 자기완결)

> 본 brief = `/gemini-web` (Gemini 2.5 Pro, 참신·다른 모델) + `/claude-web` (Opus 4.7 1M fresh context, 실무) 병렬 동시 호출용. 외부 모델은 우리 컨텍스트 모름 → 4 섹션 자기완결.

---

## §A. 배경 & 목적

### A.1 누가·무엇을

- 한국 (eq_kr) baseline study 가 v2 7-Phase 방법론으로 사용자 검증 완료 (2026-05-30). 이제 **미국 주식 전체 (eq_us)** 같은 방법론으로 수행.
- 목표 = **미국 주식 GICS 11 sector Tier 차등 분할 × regime (Investment Clock epoch × dollar × credit/rate) 동적 가중** 평가 시스템.
- 최종 산출 = `study_session.yaml` 7블록 (lens / indicators / relationships / weight_rules / confidence_hooks / collector_plan / code_change_plan) + 산업별 sub-study.

### A.2 시스템 컨텍스트 (외부 모델 이해용)

- 평가 시스템 = 종목 buy 시 `score = Σ wᵢ · zᵢ(indicator)` (정형 합성 + LLM down-only). **wᵢ 가 regime·산업·종목특성에 따라 동적 변화** = 본 study 의 산출물.
- 산업별로 어떤 지표 가중치를 어떤 상황에서 어떻게 바꿀지를 종목 단위까지 잘게 쪼갠 규칙 도출.
- 본 study 는 **이론 + 실데이터 검증** 둘 다 필수 (자문 → yaml 직접 X). 가설 → 5게이트 (N≥24 / SE CI / Power MDE / FDR / OOS skfolio CPCV) 통과 후만 weight_rule 후보.

### A.3 외부 모델이 알아야 할 5 금지

1. **점추정 prior 박제 금지** — IC 점추정 → base_weight 직접 X. 분포 + CI + 게이트.
2. **합성·시뮬 데이터 금지** — random walk / 합성 panel / 가상 ticker / random IC. 실제 수집기 PIT만.
3. **자문 그대로 코드화 금지** — gemini/claude 답 → yaml 직접 X. supervisor 비판·환각 cross-verify 후 채택.
4. **Single-source 단정 금지** — 1 출처 "확정" X. 학술 + 실무 + 1차 데이터 3중.
5. **Small-N 단정 금지** — cell N<24 "유의" 주장 X. 5게이트 §N gate 우선.

### A.4 본 R1 의 산출 목표

본 R1 응답 → `raw/consult-round-1-{gemini,claude}.md` 박제 → R2 빈틈 보충 → R3 수렴 → `direction.md` (①이론수집 ②검증방향 ③핵심가설 N) → main 승인 → Phase 4+.

---

## §B. 이미 있는 입력 자료 (재사용 baseline)

### B.1 한국 (eq_kr) baseline — 12 가설 미러링 후보

| ID | eq_kr 가설 (한국) | eq_us 미러링 핵심 의문 (R1 자문에 답해주기 바람) |
|---|---|---|
| H1 | 외국인 순매수 → 대형 KOSPI t+5~20d return 양 선행 (1순위 alpha) | 미국은 외국인 flow ≠ driver. 미국 1순위 alpha 후보는? (Fed path / Mag7 capex / buyback / HY OAS regime / FII flow into US ETF) |
| H2 | 밸류업 Index 편입 종목 re-rating (일본 baseline 2-3년) | 미국 동등 policy event 후보? (Inflation Reduction Act 2022 / SAB 121 폐기 2025 / Magnificent 7 index inclusion) |
| H3 | USDKRW × export_share 교호항 (수출주 양·내수주 음) | 미국은 DXY × foreign revenue share 교호 (Damodaran multinational vs domestic) — 부호 반대? S&P 500 ≒ 40% foreign revenue. 분기 메커니즘? |
| H4 | 반도체 cycle (DRAM yoy/$SMH) → fwd EPS lag 1-2Q | 미국 SOXX 자체 = cycle 본진. AI capex cycle (NVDA 2023+) 가 전통 DRAM cycle 와 별개 채널? 분리 메커니즘? |
| H5 | 한국 모멘텀 약효 (12-1 IC < 0.03) | 미국 모멘텀 = Jegadeesh-Titman 학술 원본. Russell 1000 12-1 IC ≈ 0.05~0.10 (정설). 단, momentum crash (2009, 2020) regime 의존. 어떤 regime 에서 강·약? |
| H6 | KOSDAQ 개인 주도 = 단기+ / 중기- 반전 | 미국 retail 비중 (Robinhood post-2020 ≈ 25%), meme stock 단기/중기 반전 동등? |
| H7 | HY OAS↑ → 외국인 매도 + KRW 약세 + 대형주 디레이팅 (3 동조) | 미국 HY OAS↑ = risk-off, defensive outperform (XLU/XLP) + Russell 2000 underperform. 어떤 sector 가 가장 sensitive? |
| H8 | G-score → 가격 무관 (한국 학술) | 미국 거버넌스 score (ESG-G / GMI) → fwd return 유의? (e.g., Gompers-Ishii-Metrick 2003 G-Index 학술 양 → post-2002 결과 반전?). |
| H9 | breadth_kospi 음 = 반도체 dominance 단기 alpha | 미국 breadth (NYSE A/D, S&P 500 EW vs CW, Mag7 vs rest) 음 = 어떤 alpha? (2023-2024 Mag7 dominance 명확) |
| H10 | 일본 baseline 한국 적용 시차 2-3년 | 미국은 leader, 다른 시장의 baseline. 그러나 미국 안 sub-segment 시차 가설 가능? (e.g., AI 채택 2023 LLM 도입 → fwd EPS 2025+) |
| H11 | R&D·Intangible 종목 outperform (e-KJFS 학술) | 미국 R&D-intensive = 이미 Mag7 reward. factor crowding 위험 (Eisfeldt-Papanikolaou 2013 intangible factor saturation). 추가 alpha 여지? |
| H12 | 외국인 flow regime × 산업 Tier 교호 (T1 효과 강) | 미국 macro regime × Tier 교호 (R1 ★critical) — 이미 cyclical study (B.2) 가 epoch swing 검증. 다른 regime 분류? |

### B.2 미국 cyclical 기존 산출 (재사용 — 재작업 금지)

- **study-research/eq_us_cyclical/** = 경기민감 4 산업 (반도체 SOXX / 소재 XLB / 산업재 XLI / 에너지 XLE) M3 검증 완료 (2026-05-30, n=756 daily 2021-12 ~ 2024-12).
- **★핵심 발견 1**: β_dxy ≫ β_us10y (1자리 차이) — rate 가 주식에 미치는 영향은 거의 dollar 채널 경유. 전 cyclical sector β_dxy ∈ [−0.58, −1.62], β_us10y ≈ 0.
- **★핵심 발견 2**: 국면조건부 dollar 강도 가변. E1 (긴축충격 2022-01~09) R²=0.21 / E2 (전환반등 2022-10~2023-06) R²=0.29 / E3 (금리재상승) R²=0.13 / E4 (pivot/완화) R²=0.07.
- **★핵심 발견 3**: SOXX = 고듀레이션 amplifier (epoch swing −50.4% → +88.7%). XLE = anti-cyclical hedge (oil rank-IC +0.602, others corr 0.26~0.51 outlier).
- **★핵심 발견 4**: within-cyclical sleeve 평균 corr 0.617 → Kish eff_N=1.47. 거시 1회 계상은 cross-asset 차원 (cyclical vs defensive sleeve), within-sleeve 종목간은 equity factor 영역.

### B.3 미국 defensive 기존 산출 (★합성 의심, R4 자문 수렴 후 P0 재검증 대상)

- **study-research/eq_us_defensive/** = 방어주+금융 통합 sleeve (XLP·XLU·XLV·XLC mature + XLF), R4 Gemini Pro 자문 수렴.
- **★핵심 발견 1**: 5 archetype 부호 반대 — real rate↑ 시 utility/staples 압박 (-) / bank 호재 (+, NIM 확장). HY OAS↑ 시 defensive 양 (+) / bank 음 (-). curve 스티프닝 동등 분기.
- **★핵심 발견 2**: 5 archetype = staples / utility / healthcare / bank / insurance. `composed_weights(pi)` 보간으로 종목별 부호 흡수.
- **★핵심 발견 3**: 방어 = quality + dividend safety + rate beta. valuation 부차. 모멘텀 강등 (base 0.12 → 0.06, mean-reversion 우위).
- ⚠️ **⛔ 합성 데이터 의심 (Hard-fail B 위반 가능성)**: `raw/lens-hypothesis-quickcheck.txt` = "synthetic 240m, seed 20260530". H1~H4 "CONFIRMED" 가 실데이터 아닌 prior-consistent simulation. → 본 eq_us study 에서 P0 재검증 필요 (실데이터 EDGAR + FRED 로 가설 재실행).

### B.4 시스템 인프라 (수집기 가용)

**이미 있음** (그대로 쓰면 PIT 자동 보호):
- FRED 17 시리즈 + ALFRED vintage (`core/brain/fred_adapter.py`)
- US ETF (yfinance) sector ETF 6591일 (`raw/yfinance/sector_etf_close.csv`)
- EDGAR (미국 펀더멘털, `edgar_provider.py`) — 단, 은행 Y-9C / EPS revision breadth 등은 추가 파싱 필요

**부족 → 자문에서 OSS 추천 받고 싶음**:
- 미국 fwd EPS revision (Refinitiv/IBES 유료 대체 OSS?)
- buyback yield (S&P Indices vs SEC Form 4)
- Ken French 5-factor / Mom / BAB / QMJ panel (FF library + Pedersen 공개?)
- survivorship-bias-free universe (CRSP-like OSS?)
- AI capex / hyperscaler tracking (Visible Alpha 대체?)
- Mag7 / index concentration metric (S&P 500 EW vs CW IWY/RSP)

---

## §C. 자문 질문 Q1-Q10 (R1 핵심)

### Q1. GICS 11 sector Tier 차등 — 적합성

**제안 분류** (MAIN-DISPATCH §2):
- **T1** (시총 집중 ≥40%): IT (XLK, AAPL/MSFT/NVDA) + Communication Services (XLC, GOOGL/META) — sub-cluster: AI semis (NVDA/AMD/AVGO) / hyperscaler (MSFT/GOOGL/AMZN) / software platform (META/ORCL/CRM)
- **T2** (각 5-12%): Financials (XLF) / Health Care (XLV) / Consumer Disc (XLY) / Industrials (XLI) / Energy (XLE)
- **T3** (각 2-5%): Consumer Staples (XLP) / Materials (XLB) / Utilities (XLU) / Real Estate (XLRE)

**질문**: 이 Tier 분류가 미국 시장의 실측 시총 분포 + factor 노출 구조에 정합? 또는 다음 대안이 더 우월?
- (a) **factor-노출 기반 5 sleeve** (growth / value / quality / low-vol / cyclical) — Russell 1000 style box
- (b) **macro 민감도 기반 4 sleeve** (rate-sensitive bond proxy / dollar-sensitive multinational / credit-sensitive levered / pure equity factor)
- (c) **Mag7 단독 sleeve + 나머지 10 GICS** — 30%+ 시총 집중 격리 (reflexive loop 차단)

### Q2. 미국 시장 driver 1-3 순위

한국 (eq_kr) 1순위 = 외국인 순매수 (15세션 50조 매도 driver 확정). 미국은 외국인 flow ≠ driver (기축통화). 미국 1순위 alpha driver 후보 5:
- (a) **Fed funds path expectation** (FOMC dot plot vs OIS curve, dovish/hawkish surprise event study)
- (b) **AI capex concentration** (Mag7 capex yoy, NVDA fwd EPS revision breadth)
- (c) **buyback yield** (S&P 500 buyback yield + dividend yield = total shareholder yield, vs 10Y Treasury)
- (d) **HY OAS regime** (BAML HY OAS, 4 regime: low<300bp / mid 300-500 / high 500-800 / crisis >800)
- (e) **earnings revision breadth** (NDR / FactSet, 4-week up vs down ratio)

**질문**: 학술 + 실무 종합 시 미국 1-3 순위는? 각 driver 의 (a) measurable signal source (b) 평균 IC magnitude (c) regime stability?

### Q3. cyclical M3 finding vs defensive — 통합 reconcile

- cyclical: β_dxy ≫ β_us10y, 모든 sector β_dxy 음 (-0.58 ~ -1.62)
- defensive: real rate↑ 시 utility 음 / bank 양 — **rate 직접 영향 강** (cyclical 와 1자리 차이 반대)
- 통합 시 의문: (a) cyclical 의 dollar 채널 우위는 표본 기간 (2022-2024 강달러) 한정? (b) defensive 의 rate 직접 우위는 sub-sleeve 효과 (bank NIM)? (c) GICS 11 sector 통합 sleeve 정의 시 어떤 channel 을 default 로?

### Q4. 5 archetype sub-sleeve (defensive) 의 GICS 11 sector 매핑

defensive 의 5 archetype (staples / utility / healthcare / bank / insurance) 을 eq_us 통합 시:
- staples → XLP
- utility → XLU
- healthcare → XLV (단, pharma vs biotech vs MD vs HMO sub 분기)
- bank → XLF 안 (단, asset managers BLK/MS / payments V/MA / insurance MET/PRU 분리)
- insurance → XLF 안 또는 별도?

**질문**: 미국 GICS 11 sector + 학술 (Damodaran sector valuation) 정합 sub-sleeve 분류는? Tier 1 (IT+Comm) 안 sub-cluster (AI semis / hyperscaler / software platform) 도 학술 baseline 있나?

### Q5. Mag7 / AI capex 집중 → reflexive loop 위험

- 2023-2024 S&P 500 return ≒ 60%+ Mag7 기여. Mag7 weight 30%+ → 시장 corr 자체가 7 종목 corr 와 거의 동등.
- reflexive loop 위험: AI capex thesis 강화 → Mag7 weight 증가 → 시장 corr 증가 → AI thesis 더 강해 보임 → over-positioning → 단일 thesis 붕괴 시 cascade (2024-08 mini-crash 사례).

**질문**: Mag7 / AI capex 집중을 어떻게 study 에 반영?
- (a) **Mag7 단독 sleeve** + 나머지 10 GICS = 격리
- (b) **toraniko factor model** factor-neutralized IC (AI factor 추출 후 residual)
- (c) **ticker-level shrinkage** (composed_weights pi, Mag7 weight cap 0.2)
- (d) **regime-conditional 분리** (AI capex yoy > +30% regime = Mag7 weight ↑ / < +10% = weight ↓)

### Q6. Real Estate (XLRE) — reit study 중복 경계

- Inv 시스템에 별도 `reit` study (v2 v1 미산출, H1 REJECT 이력) 존재.
- GICS 11 sector 안 Real Estate (XLRE) 가 reit study 범위와 겹침.

**질문**:
- (a) XLRE 를 eq_us 안 포함 (Tier 3) 하고 reit study 와 partial-corr 통합 시 중복 계상 우려는?
- (b) XLRE 를 분리 (eq_us = GICS 10 sector) 하고 reit study 단독 운영?
- (c) reit study 의 v2 산출 (`study-research/reit/study_session.yaml`) 을 input 으로 수용?

### Q7. PIT/lookahead — 미국 시장 검증 인프라

미국 시장 5게이트 #4 PIT (point-in-time) 가능 인프라:
- EDGAR filing 발표 지연: 10-Q 45일 / 10-K 90일 (SEC rule). 정확한 지연 시계열은 EDGAR 헤더 `filed_date` (★ 이미 정확)?
- ALFRED vintage (거시 first-release): 가용 (`fred_adapter` 적재됨)
- ★survivorship-bias-free universe: CRSP (유료, MIT/Wharton 학술 접근만). **OSS 대안 후보**:
  - (1) Sharadar Equity Prices (Quandl, 부분 free?)
  - (2) Norgate Data (유료 but 저렴)
  - (3) yfinance + 자체 historical ticker list (S&P 500 changes Wikipedia + 상폐 ticker 보존)
  - (4) FinanceDatabase (MIT) + EDGAR XBRL + 자체 PIT universe 구축

**질문**: OSS only 로 survivorship-bias-free + PIT universe 구축 가능? 정확도 / 누락 trade-off?

### Q8. validate 인프라 — 미국 시장 OSS

- **skfolio CombinatorialPurgedKFoldSplit** (frame §M4 #5 OOS gate) — 미국 데이터에 그대로 적용 가능?
- **toraniko factor model** (frame §M5 baseline) — 미국 시장 first mover 아님 (Barra / Axioma 학술 baseline 다수). OSS 권고?
  - (a) toraniko (MIT, polars+numpy)
  - (b) zipline-reloaded (Quantopian fork, 무료)
  - (c) Ken French data library + 자체 5-factor 회귀
- **Newey-West HAC SE** + **block bootstrap** — 표준
- **추가 권고 OSS** (미국 특화):
  - QMJ factor (Asness-Frazzini-Pedersen) public data?
  - BAB (Betting Against Beta) — Pedersen 공개?
  - PRICING 데이터 OSS (alphalens, pyportfolioopt)?

### Q9. 핵심 가설 5-10개 초안 (반증조건 포함)

위 Q1-Q8 답에 기반하여 본 eq_us study 의 핵심 가설 5-10 개 (반증조건 포함) 초안을 제안. eq_kr 12 가설 양식 미러링 (예: "H1: 외국인 순매수 → 대형 KOSPI t+5~20d return 양 선행 / 반증: e-CUSUM baseline +0.05 단측 붕괴"). 미국 특화 가설:
- AI capex × Mag7 fwd EPS lag 1-2Q
- HY OAS regime × sector rotation (defensive vs cyclical)
- buyback yield × total shareholder yield > 10Y Treasury → value alpha
- Fed funds path surprise event study
- earnings revision breadth → fwd 3M return
- 그 외 추천 가설

### Q10. 미해결·confound·bias

미국 시장 study 시 confound·selection bias·데이터 한계 우려 (eq_kr 의 외국인 flow 같은 핵심 driver 결측 우려 포함). 본 R1 단계에서 명시 권장 5+.

---

## §D. 출력 양식 (강제 — 본 R1 응답 형식)

### D.1 각 Q1-Q10 에 대해 다음 5 필드 응답

```markdown
## Q{N}. [질문 제목]

### 답변 (1-3 paragraph, 핵심 결론 먼저)
[직접 답변]

### 근거 (학술 + 실무 + 1차 데이터 3중 — single-source 단정 금지)
- 학술: [저자 (연도) - 제목 / 학술지. DOI 또는 URL]
- 실무: [증권사 리포트 / 정책 문서 / 업계 표준 — 발행자 + 연도]
- 1차 데이터: [어떤 source 에서 어떤 metric 으로 검증 가능 — FRED 시리즈 ID / SEC filing 형식 / OSS 라이브러리]

### 정량 magnitude (가용 시)
[IC mean ± 표준오차 / R² / lag period / regime stability 등 — 점추정 단독 X, range 또는 CI 포함]

### 반증조건 (Q9 가설 답변 시 필수)
[가설이 어떤 조건에서 reject 되는가 — e-value, CI bound, regime transition signal]

### confound·confidence
[교란 변수, 표본 한계, 미국 특화 의문점, confidence level low/medium/high]
```

### D.2 R1 응답 길이 가이드

- Q1-Q10 각 200-500 단어 (총 3000-5000 단어)
- 핵심 결론 먼저, 근거 뒤
- ⛔ 환각 reference 금지 (실제 DOI / URL / SEC filing form 명 명시)
- ⛔ 점추정 단독 박제 금지 (range, CI, regime 의존성 명시)

---

## §E. R1/R2/R3 자문 진행 계획

- **R1 (지금)**: 본 brief 두 채널 (gemini-web + claude-web) 병렬 호출 → `raw/consult-round-1-{gemini,claude}.md` 박제 → 두 응답 비교 (일치/공통/공백) → R2 빈틈 보충 질문 설계
- **R2**: R1 공백 + 두 모델 disagree 항목 + R1 답에서 cited reference 1차 source 환각 cross-verify (DA-20260422-search-engine-hallucination-check) → 1-2 라운드
- **R3**: 수렴 (두 모델 일치 + 새 의문 무 + supervisor 충분 판정) → direction.md 작성

수렴 판정 3 조건 (DA-20260427):
1. 두 모델 답변 의미상 일치 또는 명확한 trade-off 합의
2. 새로운 의문 비생성
3. supervisor (본 작업방) 가 direction.md 작성 가능 판정

자문 채널 경합·타임아웃 시 WebSearch/WebFetch 폴백.

---

## §F. 출력 의무 (외부 모델 강제)

1. ⛔ **자문 그대로 yaml 박제 위험 인지** — 본 R1 응답은 supervisor 가 비판적으로 받아 검증·환각 cross-verify 후 채택. 단정 어휘 회피, "권고" / "후보" 어휘.
2. ⛔ **점추정 prior 박제 위험 인지** — "IC = 0.4" 같은 점추정 단독 보고 X. range / CI / regime 의존성 명시.
3. ⛔ **single-source 단정 회피** — 학술 + 실무 + 1차 데이터 3중 (D.1 §근거).
4. ⛔ **환각 reference 금지** — DOI / URL / SEC form 명 / FRED ID 정확 명시. 불확실 시 "tentative reference" 라벨.
5. ⛔ **미국 한정 답변** — 한국 / 일본 cross-applicability 일반론은 weak signal 만, 명확히 미국 시장 데이터 priors 우선.
