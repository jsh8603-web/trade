---
tags: [type/collector-queue, study/eq_us_cyclical, purpose/main-collector-request]
date: 2026-05-31
purpose: |
  main 정정 지시 (2026-05-31) — candidate-ledger 의 이연 후보를 "merit 근거 + 필요 collector + 
  무료 데이터소스 후보" 박제 작업큐로 전환. 이연·후순위 단순 박제 = 탈락 사유 부적격.
  흐름: main collector 구현 → 본 워크룸 study (이론 → 실데이터 → 상관·Rank-IC) → 12축 audit → yaml 반영.
basis_raw:
  - candidate-ledger.md (이연 카테고리 출처)
  - direction.md ③ (가설 H1-H10), ④ Q3 (collector 자체평가)
  - audit-self.md (a) 데이터 인프라 5건
  - m3-findings.md §4 (system 코드화 시사)
  - study_session.yaml 블록6 (collector_plan 우선순위)
deliver_to: btn-Codlearn (main)
---

# Collector Request Queue — eq_us_cyclical merit 후보 전수

> 각 후보: ① merit 근거 (왜 가치 있나, 학술/실측) ② 필요 collector (어떤 데이터·인터페이스) ③ 무료 데이터소스 후보 (URL/API). 흐름 = main collector 구현 → 워크룸 study (이론 → 실데이터 → 상관·Rank-IC) → 12축 audit → yaml 반영.

## 🔴 Tier 1 — ★★★ 시스템 골격 (즉시 collector 의무, 5 가설 의존)

### T1-A. EDGAR 분기 펀더 (10-Q 재무제표)

- **merit**: H1 (정상화 E/P trough 최강) + H6 (peak_trap 차단) + H9 (Asset Growth Anomaly CMA) + H7 (Operating Leverage) + H10 (fair_mult re-rating) — 5 핵심 가설 동시 의존. Damodaran 정상화 마진 (mid-cycle EBIT × 추세매출) = 시스템 골격 핵심 (Round 1-3 자문 만장일치). Cooper-Gulen-Schill 2008 JF Asset Growth Anomaly 학술 정본 (CMA 팩터 사촌). 현재 미적재 = backbone 미입증 상태.
- **필요 collector**: EDGAR provider 확장 (분기 ROE / 영업마진 / 매출 / 총자산 / capex / 재고 / 비용 분해)
- **인터페이스**: `FundamentalsProvider` (블록7 stage learn, `core/data/weight_panel.py` symbol `build_indicator_matrix`)
- **무료 데이터소스**: **sec.gov EDGAR API** (https://www.sec.gov/edgar/sec-api-documentation, JSON facts endpoint 무료 무한, rate-limit 10 req/sec)
- **추가**: User-Agent 헤더 의무 (이메일 주소)
- **활성 indicators**: `fwd_ep_normalized` (base 0.30) / `roe_margin_trend` (0.10) / `asset_growth_yoy` (0.08) / `capex_to_rev` (0.04) / `fwd_eps_momentum` / `operating_leverage_nm` (0.04)

### T1-B. Damodaran implied ERP 월별 vintage

- **merit**: H1 fair_mult Band Monte Carlo 산출 핵심 입력 (Round 3 Claude 만 지적: g=ROE·b 대입 시 P/E=payout/(r-g) 동어반복 함정 — GDP cap g 강제 차단). historical 5% 대비 implied ERP (월별) 정밀도 압도. (r-g) ≥ 2% guardrail 강제 시 ERP vintage 미적재면 분모 폭주.
- **필요 collector**: NYU Stern 월간 CSV scraper
- **인터페이스**: `VintageProvider` (월별 frequency)
- **무료 데이터소스**: **NYU Stern Damodaran 데이터 페이지** (https://pages.stern.nyu.edu/~adamodar/New_Home_Page/dataarchived.html, "Implied ERP - monthly" CSV 무료)
- **활성**: fair_mult Band Monte Carlo (블록7 stage card, `core/assume/weight_card.py` 신규 모듈)

### T1-C. GZ EBP 정공법 (TRACE + Merton DD)

- **merit**: H4 (EBP 공통원인) lead 신호 정공법. 1차 실측 (BAA10Y-AAA10Y 빈자판) = lead 부재 (k≥1 IC<0.05). Gilchrist-Zakrajšek 2012 AER 학술 정본: HY OAS 단순 통제 ≠ EBP 잔차 (DD + 채권 chars + firm FE 회귀 후 잔차). 정공법 적재 시 H4 lead 신호 부활 가능성.
- **필요 collector**: EBP 잔차 산출 모듈 (TRACE 채권 데이터 + Merton DD + 발행자 firm-FE)
- **인터페이스**: `VintageProvider` (월별)
- **무료 데이터소스**: TRACE 자체 = FINRA 유료. **대안 = Favara/Gilchrist/Lewis/Zakrajšek 2016 FEDS Notes 부록 CSV** (https://www.federalreserve.gov/econres/notes/feds-notes/recession-risk-and-the-excess-bond-premium-20160408.html — 월별 EBP 시계열 무료 공개)
- **활성**: `ebp_residual` indicator + H4 lead 재검증

## 🟠 Tier 2 — ★★ 가설 보류 진입 (collector 의존, 즉시 검증 가능)

### T2-A. FINNHUB earnings revision breadth

- **merit**: H8 (revision breadth 전환점) 학술 정본 — Chan-Jegadeesh-Lakonishok 1996 JF + Bernard-Thomas 1989 JAR PEAD + Womack 1996 JF. 1차 검증 미수행 사유 = IBES (Refinitiv) 유료. FINNHUB 무료티어 (analyst earnings estimates) 로 대체 가능. revision breadth = (상향 - 하향) / 전체 → fwd 12M return 정밀 lead.
- **필요 collector**: FINNHUB adapter (consensus estimate + revision history)
- **인터페이스**: `FundamentalsProvider`
- **무료 데이터소스**: **finnhub.io 무료티어** (https://finnhub.io/docs/api/recommendation-trends, 60 calls/min, `FINNHUB_API_KEY` 무료 가입). 대안: **EDGAR 8-K 가이던스 자체 파싱** (T1-A 와 동시 적재 가능, NLP 필요)
- **활성**: `earnings_revision_breadth` indicator + H8 진입

### T2-B. SEMI book-to-bill (반도체 δ_arch)

- **merit**: 반도체 cycle 핵심 driver (1.0 = balance, >1 = up-cycle, <1 = down-cycle) — 학술 표준 산업 cycle 지표. SOXX M3 epoch swing 최대 (E1 −50% → E2 +89%), 거시 driver (β_dxy −1.62) 외 산업 고유 펀더 = book-to-bill. δ_arch 후보 1순위 (펀더멘털 only, 이중계상 회피).
- **필요 collector**: SEMI 협회 월별 scraper
- **인터페이스**: `FundamentalsProvider` (월별, industry-specific)
- **무료 데이터소스**: **semi.org Book-to-Bill** (https://www.semi.org/en/products-services/market-data/equipment, 월별 무료 — 단 가입 시 CSV 가능 / 또는 SEMI Newsroom 월간 보도자료 파싱)
- **활성**: `book_to_bill_ratio` (semi δ_arch, M6 Workflow 산업×regime δ 매트릭스 입력)

### T2-C. BKR rig count (에너지 δ_arch 경계)

- **merit**: XLE 추가 driver (M3 §4 권고). oil futures 단독으로 부족 → rig count = supply discipline lead 지표. ★단 cross-sleeve (전체 oil 영향) vs energy-specific 경계 — 자체 분석 필요 (산업-specific 분류 시 δ_arch, oil 1차 channel 면 배분레이어).
- **필요 collector**: FRED 또는 Baker Hughes 직접 scraper (주별)
- **인터페이스**: `VintageProvider` (주별)
- **무료 데이터소스**: **FRED `BKRRIGUSTOTAL`** (https://fred.stlouisfed.org/series/BKRRIGUSTOTAL, 주별 무료 + `FRED_API_KEY` 무료) / 대안: **bakerhughesrigcount.com** (주별 PDF/Excel)
- **활성**: `rig_count_yoy` (energy δ_arch 후보 + 경계 분류 study)

### T2-D. NBS Manufacturing PMI (중국, 소재 δ_arch)

- **merit**: XLB (소재) 중국 수요 driver — Chancellor capital cycle commodity rotation 핵심 (가격↑→CapEx↑→공급과잉). M3 XLB β_dxy=−1.18 R²=0.215 (cyclical 2등 설명력) — dollar 단독 외 중국 PMI 추가 시 정밀화 기대.
- **필요 collector**: NBS PMI scraper (월별)
- **인터페이스**: `VintageProvider` (월별)
- **무료 데이터소스**: **중국 국가통계국 NBS** (http://www.stats.gov.cn/sj/zxfb/ 월별 무료 — 단 한자 처리 필요) / 대안: **TradingEconomics china-manufacturing-pmi** (무료 페이지) / Caixin PMI = 유료
- **활성**: `china_pmi_yoy` (materials δ_arch)

### T2-E. ALFRED vintage (CFNAI/AMTMNO release-date)

- **merit**: D축 결함 보강 (audit-self.md D축 PARTIAL 사유). 1차 H3 검증 = FRED latest revised vintage 사용 → CFNAI 깊은 revision (Round 3 Gemini 경고: 2019말 지표가 2021에 크게 바뀜) look-ahead bias 잔존. ALFRED release-date vintage 적재 후 H3 (ISM 선행) 재검증 = 더 약화 또는 부활 결정.
- **필요 collector**: ALFRED adapter (vintage-date endpoint)
- **인터페이스**: `VintageProvider` (월별, release-date stamp)
- **무료 데이터소스**: **FRED ALFRED API** (https://alfred.stlouisfed.org/, `FRED_API_KEY` 무료, vintagesdates endpoint)
- **활성**: CFNAI / AMTMNO / NEWORDER PIT 재정렬 → H3 재검증 (validation-H3.md 재실행)

## 🟡 Tier 3 — ★ 정밀화 (Tier 1 종속, 후속)

### T3-A. GICS 정확 섹터 분류 + ETF holdings

- **merit**: 산업×regime δ 매트릭스 (현재 진행 Workflow wf_9ce20415-0d2) 의 종목 매핑 정확화. 현재 ETF (XLY/XLI/XLB/XLE/XLF + SOXX) 라벨 기반 → GICS 정확 분류 시 sub-sleeve (반도체↔하드웨어 분리, 화학↔금속 분리 등) 정밀.
- **필요 collector**: FinanceDatabase scraper + ETF holdings (SPDR/iShares)
- **인터페이스**: 신규 (`SectorClassifier`)
- **무료 데이터소스**: **FinanceDatabase MIT 라이선스** (https://github.com/JerBouma/FinanceDatabase, GitHub 무료) / **iShares SOXX holdings CSV** (https://www.ishares.com/us/products/239705/ishares-phlx-semiconductor-etf 무료 공개)
- **활성**: 산업 sub-sleeve 정밀 분류 + Workflow synthesis 후 적용

### T3-B. LME 산업금속 (소재 δ_arch 보조)

- **merit**: XLB Chancellor capital cycle 가격 신호 직접 — 구리 (Dr. Copper) 산업수요 bellwether. 단 무료 데이터 한정 (정밀 보고 유료).
- **필요 collector**: LME 공개 시세 scraper
- **인터페이스**: `VintageProvider` (일별)
- **무료 데이터소스**: **LME 공개 cash settlement** (https://www.lme.com/en/Metals/Non-ferrous, 구리/알루미늄 일부 무료) / 대안: **Yahoo Finance HG=F** (구리 선물, 무료)
- **활성**: `copper_yoy` (materials δ_arch 보조)

### T3-C. SEMI DRAM ASP (반도체 δ_arch 보조)

- **merit**: 반도체 가격 신호 (DRAMeXchange 표준). book-to-bill 보완. Memory cycle (Samsung/Micron/SK Hynix earnings drive) 직접 매핑.
- **필요 collector**: DRAMeXchange 또는 TrendForce 월별 scraper
- **인터페이스**: `VintageProvider` (월별)
- **무료 데이터소스**: **DRAMeXchange 일부 무료** (https://www.dramexchange.com/, 월별 평균 ASP 공개) / TrendForce = 유료
- **활성**: `dram_asp_yoy` (semi δ_arch 보조)

## 📊 collector 추가 X — 가용 데이터로 산출 가능 (코드 변경만)

| 후보 | 활용 데이터 | 산출 위치 |
|---|---|---|
| `dxy_beta_sector_1y` (M3 권고) | yfinance + FRED 가용 | `core/data/weight_panel.py` 신규 함수 |
| `oil_beta_xle_1y` (M3 권고) | yfinance + FRED 가용 | 위 동일 |
| epoch regime tag 매크로 (M3 §4) | M1 timeline 가용 | `core/brain/regime_classifier.py` 정밀화 |
| dollar→cyclical_eps prior 0.3→0.4 (M3 권고) | m3-metrics.json 가용 | study_session.yaml 블록3 수정만 |
| NEW oil→XLE_eps prior 0.7 (M3 권고) | 위 동일 | 위 동일 |

## 🛠️ 통계 모듈 (collector 아님 — 코드 변경, audit-self.md G축)

| 모듈 | merit | 위치 |
|---|---|---|
| Driscoll-Kraay panel HAC SE | G축 결함 보강 — overlapping window SE 정확화 | `core/assume/weight_falsification.py` 확장 |
| Politis-Romano stationary bootstrap | date-block 단위 횡단 통째 리샘플 | 위 동일 |
| Newey-West q≥3 + Andrews 1991 bandwidth | overlapping fwd 12M 보정 | 위 동일 |
| Bayesian shrinkage λ=τ²/(τ²+σ²/n) | 4슬롯 자동 강등 + effective_DoF | `core/assume/weight_card.py` 확장 |
| expanding-window PCA | look-ahead 100% 회피 | `core/data/weight_panel.py` 신규 함수 |
| Hamilton predicted prob P(S_t\|y_{1:t-1})=π_{t-1}·P | b(t) predictable 보존 | `core/brain/regime_classifier.py` 정밀화 |

## 🚦 우선순위 (즉시 collector 요청 권고)

| 순위 | 후보 | 의존 가설 | 무료 발급 절차 |
|---|---|---|---|
| **1** | T1-A EDGAR | H1·H6·H7·H9·H10 (5 가설) | sec.gov User-Agent 헤더 (이메일) — 즉시 사용 |
| **1** | T1-B Damodaran ERP | H1 fair_mult Band | NYU Stern CSV 직접 다운 — 즉시 사용 |
| **2** | T1-C GZ EBP (FEDS Notes 부록) | H4 lead 재검증 | Fed FEDS Notes 부록 다운 — 즉시 사용 |
| **3** | T2-A FINNHUB | H8 진입 | finnhub.io 무료 가입 (1분) — 즉시 사용 |
| **4** | T2-E ALFRED | H3 PIT 재검증 (D축) | FRED_API_KEY 무료 (1분) — 즉시 사용 |
| **5** | T2-B/C/D 산업 δ_arch | M6 Workflow 산업×regime δ 완료 후 통합 | SEMI/BKR/NBS 각 가입·scraper |
| **6** | T3 정밀화 | Tier 1 종속 | T1 적재 후 |

## 🔍 12축 audit 진입 (yaml 반영 전 의무, 별도 subagent)

★ main framing — "그러고도 빠지면 ledger 에 '왜 빠졌나' 기록" → collector 적재 → study → 12축 audit → yaml 반영 → 빠진 후보만 ledger.

12축 audit 정의 = main 측 SSOT (audit-self.md 의 8축 확장 또는 별도). 본 워크룸 요청 — **12축 SSOT 경로 main 측 명시 필요**.

## 📡 main 회신 양식

```
경로: study-research/eq_us_cyclical/collector-request-queue.md
즉시 collector 요청 (Tier 1 × 3):
  (1) EDGAR 10-Q 분기 펀더 — sec.gov API 무료
  (2) Damodaran implied ERP 월별 — NYU Stern CSV 무료
  (3) GZ EBP FEDS Notes 부록 — Fed 무료
다음 (Tier 2 × 4):
  T2-A FINNHUB / T2-B SEMI / T2-C BKR / T2-D NBS / T2-E ALFRED
가용 (코드만, collector 추가 X): 5건
통계 모듈 (코드 변경, collector 아님): 6건
의문: 12축 audit SSOT 경로 main 측 명시 요청
Workflow wf_9ce20415-0d2: kill X, 완주 → 별도 회신 (M6 핵심 박제)
```
