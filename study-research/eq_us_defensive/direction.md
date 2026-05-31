---
tags: [type/direction, domain/inv, study/eq_us_defensive, phase/2-1]
date: 2026-05-30
study_id: eq_us_defensive
as_of: "2026-05-30"
status: 2-1 완료 → main 승인 대기 (2-2 진입 금지)
rounds: 4 (Gemini Pro 자문)
---

# direction.md — eq_us_defensive 방향성 (v2 §2-1 산출)

> **STUDY-KIT §2-1 준수**: ① 이론 수집 방향 + ② 이론 검증 방향 + ③ 가설 초안 (반증조건 포함)
> **자문 라운드**: R1 이론 prior + R2 검증 방법론 + R3 가설 9 + R4 빈틈 보충 (총 4R 수렴)
> **다음 단계 (승인 후)**: 2-2 theory-notes.md (이론 학습) → 2-3 validation-{지표}.md (실데이터 검증) → study_session.yaml

---

## 0. 자산군 범위 정의

본 sleeve = 미국 **방어주 + 금융주** 통합 (task spec):
- **방어 코어**: XLP(Consumer Staples) · XLU(Utilities) · XLV(Healthcare) · XLC mature(VZ/T/CMCSA)
- **금융**: XLF(Banks · Insurance · BD/AM · Payments)
- 분류상 financials = NOT classical defensive 이지만 task 그대로. **intra-sleeve dispersion 가장 큰 sleeve** → industry archetype 강제 분해 없이 신호 cancel.

---

## ① 이론 수집 방향 (R1 + R4 통합)

### 1.1 가격결정·자산이론 — 핵심 학술/실무 reference 17

**방어주 일반 valuation**:
| # | Reference | 핵심 통찰 |
|---|---|---|
| 1 | Damodaran NYU Stern *Sector-Specific Valuation* | 유틸리티 = stable growth DCF / staples = brand equity 무형자산 기반 pricing power. 섹터별 multiple·beta·COE 차별화 |
| 2 | Frazzini & Pedersen (2014) *Betting Against Beta* JFE | 저베타 알파 (BAB). 레버리지 제약 투자자 = 고베타 과대평가 → 방어주 *안전 자산* 프리미엄 학술 근거 |
| 3 | Asness, Frazzini & Pedersen (2019) *Quality Minus Junk* RFS | 수익성·성장성·안정성·배당 기준 quality factor. 방어주 본질 quality 특성 = 초과 성과 |
| 4 | Ilmanen (2011) *Expected Returns* Defensive Equity 챕터 | ★방어주 = "채권 대리 자산" (bond proxy). 안정 배당 + 긴 cash flow duration → 실질금리 민감 메커니즘의 교과서 anchor |

**금융주 valuation**:
| # | Reference | 핵심 통찰 |
|---|---|---|
| 5 | Damodaran (2012) *Investment Valuation* Ch16 Financial Services | 은행 = 잔여이익 모델 (RIM). `V = BV + Σ[(ROE-COE)·BV]/(1+COE)^t`. ROE-COE 스프레드 핵심 |
| 6 | Society of Actuaries — Embedded Value/MCEV | 생명보험 = EV (Adjusted NW + Value of In-force). 부채 duration·자산 duration 매칭 |
| 7 | 업계 KBW/MS *Asset Managers & Payments* | AUM × Fee Rate / 명목GDP × 카드사용률 모델, 영업 레버리지 高 |

**유틸리티 특화**:
| # | Reference | 핵심 통찰 |
|---|---|---|
| 8 | FERC/PUC rate case filings | `EPS = Rate Base × Allowed ROE`. capex 사이클이 Rate Base 성장 핵심 |
| 9 | CRS (2022) *IRA* | ITC/PTC 신재생 세액공제 → util Rate Base 성장 5-10Y driver |

**헬스케어 특화**:
| # | Reference | 핵심 통찰 |
|---|---|---|
| 10 | Kaiser Family Foundation *IRA Prescription Drug Provisions* | Medicare 가격 협상권 = pharma multiple 디레이팅 |
| 11 | Census/CMS projections | 65+ 인구 증가 → Medicare 등록 구조적 증가. pharma/MD/HMO 모두 demographic tailwind |
| 12 | Goldman/JPM Healthcare sub-sector | pharma(방어+규제) / biotech(임상) / MD(elective procedure 경기민감) / HMO(고용·금리). ★sub-archetype 분기 |

**Comm Services mature**:
| # | Reference | 핵심 통찰 |
|---|---|---|
| 13 | New Street/MoffettNathanson | 통신 = 유틸리티형 구독 CF + 5G/fiber capex. FCF+배당 평가 |
| 14 | Leichtman Research Group *Pay-TV* | 케이블 cord-cutting 구조적 감소. 광대역·ARPU 상쇄 여부 |

**Consumer Staples**:
| # | Reference | 핵심 통찰 |
|---|---|---|
| 15 | Bernstein/Barclays CPG | 마진 = pricing power vs commodity input cost 힘겨루기 |
| 16 | NielsenIQ/IRI 시장 데이터 | WMT private label + Amazon 이커머스 disruption |
| 17 | 10-K Geographic Segment | KO/PG/PEP/PM 신흥시장 매출 비중 高 → DXY 환차손 직접 노출 |

### 1.2 거시 driver - sector 분기 메커니즘 (정량 관계도)

| Driver | 메커니즘 | 방어주 부호 | 금융주 부호 | 학술 anchor |
|---|---|---|---|---|
| **Real rate (DFII10)** | 할인율 + duration | **음 (-)** util/staples bond proxy | **양 (+)** NIM·book yield 개선 | Ilmanen (2011); Boyd-Gertler-Bernanke (1994) |
| **2-10Y slope** | 은행 borrow short lend long | 직접 영향 약 | **양 (+)** NIM 3-6M lag | Stigum's Money Market (2007) |
| **HY OAS** | risk-off flight-to-quality | **양 (+) 상대** outperform | **음 (-)** provisioning Q+1~2 lag | Frazzini-Pedersen BAB |
| **DXY** | 환산 매출 | **음 (-)** multinational staples | mix | 10-K Geographic Segment |
| **WTI** | 원가 input | util 단기 마진 / staples 종목별 부호 분기 | 약 | 업계 표준 |

### 1.3 보고서·실무 표준 KPI (sector 별)

- **XLF**: NIM 추이/가이던스, Loan Growth, NPL, CET1, ROE/ROA, Efficiency Ratio, BVPS
- **XLU**: Rate Base Growth, Allowed ROE, EPS·Dividend Growth, Payout Ratio, FFO/Debt
- **XLV**: R&D Pipeline, Patent Cliff, Drug/Device Sales, Medical Loss Ratio, Medicare 수가
- **XLP**: Organic Sales Growth, Pricing vs Volume, Margin, Brand Share, EM 매출 비중

Top-down → Bottom-up: Fed rate path → 매크로 시나리오 → sector KPI 전망 → 종목 EPS revision → 목표주가.

### 1.4 OSS 데이터/툴 (Phase 2-3 검증 인프라)

| 소스 | 용도 | 접근 난이도 |
|---|---|---|
| FinanceDatabase (MIT) | GICS sub-industry 매핑 | 하 |
| Ken French data library | 팩터·산업 포트폴리오 | 하 |
| FRED API (DGS10/DGS2/DFII10/BAMLH0A0HYM2/DTWEXBGS/WTISPLC/T10YIE/UNRATE/VIXCLS) | 거시 모델링 | 중 (PIT=ALFRED) |
| EDGAR (Y-9C 은행 파싱) | NIM/NPL/CET1 | 상 (regex+NLP) — **Priority 3** (R4 권고) |
| CMS.gov | 약가·Medicare | 중 |

---

## ② 이론 검증 방향 (R2 + R4 통합)

### 2.1 Regime 분류 axis — 2D 결합 (위기 유형 × HY OAS z)

**위기 유형 3 분류** (PIT regime detection, ALFRED vintage):
- **(a) 신용위기 (Credit-led)**: `BAMLH0A0HYM2` z>+1.5 AND `UNRATE` 3M 변화 > 0.3% (★**Sahm's Rule 근사**)
- **(b) 외생충격 (Exogenous Shock)**: `VIXCLS` z>+2.0 AND `GDPC1` FRED-MD nowcast 급락
- **(c) 인플레이션 충격 (Inflation-led)**: `T10YIE` z>+1.5 AND `FEDFUNDS` 6M 변화 > 100bp

**Regime axis 권고**: ★**2D tuple `(HY OAS z, 위기 유형 dummy)`** — 상호작용 효과 모델링. `conditional_correlation.py.RegimeGlasso` 의 `regime_history` 가 2D tuple 입력받도록 확장.

**민감도 분석** (R3-a): Grid Search + 3D surface plot
- OAS 임계 +1.0z ~ +2.5z (0.1z 단위)
- VIX 임계 80%~95% percentile (1pt 단위)
- 안정적 "고원" 영역 → 강건, 특정 값에 극도 민감 → 정의 위험

**성과 측정**: Bootstrap t-test (10,000 resampling) — N 작아도 (3~5 이벤트/유형) robust.

### 2.2 NIM Lag Specification — 단일 robust lag k* 고정

**Lag 탐색**:
1. CCF (Cross-Correlation Function) 0~12M
2. Partial-corr scan: `p.corr(XLF_ret(t), slope(t-k) | SPY(t), HY_OAS(t))` for k=0~12
3. 금리 사이클별 분해 (인상기/동결기/인하기, NBER 또는 Fed 발표)

**가설**: 인상기 단기 lag (2-3M) / 동결·인하기 장기 lag (5-7M) — 자산·부채 리프라이싱 속도 차

**Policy 권고**: ★**단일 robust lag `k*=4M` 고정**
- 근거: `weight_falsification.py` e-process 가 *안정적 null* (`baseline_ic`) 가정. Adaptive lag = null 시변성 → anytime-valid 보장 불가
- 보완: 모델 IC 악화 → e-process alarm → `update_controller` 가 "NIM lag 구조 변경" `lens.estimation_note` 생성

**NIM Proxy**: EDGAR 상위 10 은행 분기 NIM YoY (월별 보간) + KBW BKX 인덱스 (corr + Granger 동행성 검증).

### 2.3 Bond Proxy 시간 가변성 — 120M Rolling p.corr + Bai-Perron

**측정**:
- `p.corr(XLU(t), DFII10_change(t) | SPY(t))` — 120M rolling (★60M 노이즈, 240M 둔감, 120M 균형)
- **Bai-Perron multiple structural break test** — QE/Post-QE/ZIRP/정상화 구간 분기점 통계 검정
- 식별 break date → `regime_detection` 사전 지식 활용

**Bond Proxy 변화 원인 분해** (R4-c): rolling multi-regression attribution
```
XLU_rate_beta_rolling(t) = α + β1·ΔDFII10 + β2·ΔT10YIE + β3·IRA_dummy + β4·crisis_dummy + ε
```
- β1 = 실질금리 효과 / β2 = 인플레 기대 (2022+ ↑ 가능성) / β3 = IRA capex 구조변화 / β4 = 위기 flight-to-quality
- 위치: 신규 `core/structure/factor_beta_decomposition.py` — interpretation layer (직접 매매신호 X, H1 신호 해석 meta-signal)

**flag 발생** (`update_controller`):
- `(rolling_pcorr.sign() != historical_median_sign) AND (rolling_pcorr.abs() > threshold)` 6M 연속 (hysteresis)
- Frobenius drift e-process 와 **OR-gate** 연결

### 2.4 Partial-corr Conditioning Set — `{SPY, HY_OAS}` Default

**결정 기준**: ★**해석가능성 (interpretability) 최우선**, AIC/BIC 보조.

**Default**: `{SPY_return, HY_OAS_change}`
- `SPY_return`: systematic risk 통제 — 필수 전제
- `HY_OAS_change`: 신용 사이클·risk appetite 통제
- `WTI/DXY`: *대체 모델* 또는 *스트레스 시나리오* 에서만 (multicollinearity 위험)

**Partial corr 식** (glasso 결과 직결):
```
Ω = Σ⁻¹
p.corr(X, Y | Z) = -Ω_xy / sqrt(Ω_xx · Ω_yy)
```

**Whitelist 등록 절차**:
1. 가설 검증: `p.corr(real_rate, XLU) < 0` AND `p.corr(real_rate, XLF) > 0` 전체기간 + 주요 regime p<0.05
2. 검증된 ≤4 엣지만 `conditional_correlation.RegimeGlasso(corr_prior, force_include=[...])` 등록

### 2.5 Rank-IC 측정 design — 3M Forward + 2단계 정규화

**Forward return window**: ★**3M**
- 1M: 노이즈·단기 모멘텀 오염
- 12M: 사이클 변화 둔감
- 3M: 펀더멘털 반영 최소 시간 + regime 감응 균형

**Cross-sectional 범위**: ★sleeve 전체 N=80~120 (검정력 확보), normalization 단계에서 산업 특성 반영

**2단계 정규화 (★sub-archetype 부호 반대 문제 해결 핵심)**:
1. **Within-industry z**: 같은 GICS industry 내 종목 z. KPI 부호 이론에 맞게 조정 (은행 NIM↑ +, util 부채비율↓ +)
2. **Sleeve-wide rank z**: 1단계 z 를 sleeve cross-sectional rank z 변환

**효과**: "은행 중 우수 NIM" 과 "util 중 우수 부채비율" 동등 평가 — 산업 고유 성공 방정식 존중 + 통합 랭킹.

### 2.6 다중 KPI → 단일 score 결합 (R4-e)

**Priority 1 권고**: **IC-Weighted 하이브리드** (★주력 + 단순 평균 z 보조)
- 주력: IC-Weighted (성과 직접 기여 KPI 가중)
- 안정화: 60M rolling + **ICAR (IC-to-Annualized-Risk)** Sharp-ratio 형태 가중
- 보조: 단순 평균 z (robustness check, 두 score 큰 괴리 → 모델 이상 trigger)
- 기각: IVW (본 sleeve 저변동 → KPI 변동성 차이 자체가 신호) / PCA (블랙박스)

**3단계 normalize 통합** (R2 2단계 + R4 IC 가중):
```
1. within-industry z (R2)
2. sleeve-wide rank z (R2)
3. sub-archetype 내 IC-weighted aggregate (R4)
```

### 2.7 비선형 partial-corr (R4-d)

**가설별 필요성**:
- **선형 충분**: H1, H2, H4, H5, H6, H8 (선형 관계 1차 검증 가능)
- **비선형 필요**: H3 (phase transition at OAS 임계), H9 (Contango→Backwardation 비선형 개선)

**단계별 도입**:
- **Priority 1 (즉시)**: Spearman rank corr — `conditional_correlation.py` 의 nonparanormal 처리에 자연 통합
- **Priority 2 (H3·H9 심화)**: KCI test (Kernel-based conditional independence)
- **Priority 3 (보류)**: Gaussian Copula (overkill, 리스크 관리에서나)

### 2.8 Falsification e-process Baseline Calibration (R2-⑥)

- **baseline_ic**: 장기간 (2000-2020) IC 시계열 **median** (mean 은 outlier 민감)
- **sd**: ★**`0.8 × rolling_std(IC, 60M)`** (보수적, 미세 IC 하락에 민감)
- **tau**: ★**standard `1/alpha=20`** (Likelihood Ratio 명확 해석, 40 으로 높이면 Type II error 증가)
- **Dual-trigger OR-gate**: ★**Ω drift secondary 적극 활용** (방어주 sleeve 처럼 개별 팩터 효과 약하고 천천히 변하는 경우, 종목간 관계망 붕괴가 IC 하락 *전에* 조기 경보)
- **Regime 서브패밀리**: e-process 자체는 *단일 sleeve-wide IC* (검정력 최대화). 15 sub-family (3 regime × 5 archetype) 는 `update_controller` 진단·리포팅 단계에서만

---

## ③ 핵심 가설 초안 (R3 + R4 통합 = 12 가설)

> 각 H{N}: 가설 / 이론 anchor / 검증 design / 확신 / 반증 / Action / Lens 갱신 / Priority

### Priority 1 — 필수 6 가설 (1순위 검증)

#### H1 — Real Rate Sensitivity Dichotomy
- **가설**: 다른 매크로 통제 시 DFII10 1σ 상승 → XLU/XLP 3M 선도수익률 음의 영향 + XLF 양의 영향
- **anchor**: Ilmanen (2011); Boyd-Gertler-Bernanke (1994)
- **design**: 120M rolling p.corr(Sector_fwd3m, ΔDFII10 | SPY, ΔVIX, ΔOAS)
- **confirm**: XLU/XLP p.corr < -0.15 + XLF p.corr > +0.10 (window 75% 유지)
- **reject**: 부호 반전 12M / e-CUSUM h=5 초과 / rolling p-value > 0.1 가 24M 이상
- **Action confirm**: 금리 path → XLU/XLP vs XLF 반대 조절 / **reject**: real rate driver 가중 0
- **Lens**: regime_reading "real rate↑ = 방어 압박 + 금융 NIM 개선" 유지 / reject 시 estimation_note "IRA capex / 디레버리징 중화"

#### H2 — Yield Curve Slope NIM Leading
- **가설**: Δslope 가 3-6M lag 로 XLF 내 은행 excess return (vs SPY) 의 양의 leading 신호
- **anchor**: Stigum's Money Market (2007)
- **design**: CCF 0~12M → 최적 k* → 120M rolling p.corr(Bank_excess_fwd_k*, Δslope | SPY)
- **confirm**: CCF 최적 lag 3~6M + p<0.05 / rolling p.corr > +0.2 (window 80%)
- **reject**: 최적 lag 0 또는 음 / 부호 반전 12M / Rank-IC < sleeve baseline 12M
- **Action confirm**: 슬립 → XLF 비중 조절 핵심 input / **reject**: SOFR/FFR 대체
- **Lens confirm**: "장단기 금리차 확대 = Q+1~2 은행 실적 개선 선반영" / reject 시 "예금 베타 상승·단기자금 시장 왜곡으로 약화"

#### H3 — HY OAS Defensive Outperformance Trigger
- **가설**: HY OAS 가 임계 (200D MA + 1.5σ) 상회하는 *신용위기* 국면에서 sleeve excess > 0. *인플레 충격* 국면에서는 효과 약화/소멸 (★위기 유형별 dispersion)
- **anchor**: Frazzini-Pedersen BAB (2014)
- **design**: Regime 정의 (Credit/Inflation/Normal) → Bootstrap t-test on (Sleeve - SPY) mean
- **confirm**: Credit Crisis 평균 excess > 0, p<0.05 / Inflation Shock CI 0 포함
- **reject**: Credit 평균 excess ≤ 0 / Inflation 이 Credit 보다 강한 양의 excess
- **Action confirm**: OAS+VIX = risk appetite 바로미터 / **reject**: sleeve 방어 정체성 변화
- **Lens**: "본 sleeve = 신용 경색 flight-to-quality 강력" / reject 시 "인플레 헤지 등 다른 성격"
- **★비선형 검증 필요** (R4-d): KCI test (Priority 2) 로 phase transition 입증

#### H8 — Great Rotation within Sleeve
- **가설**: log(XLF/XLU) 상대 강도 ↔ slope 양의 관계 + VIX 음의 관계. 경기 회복기 = sleeve 내 방어 → 금융 이동
- **anchor**: 경기 사이클 sector rotation
- **design**: VECM 또는 다중회귀 — Δlog(XLF/XLU)_t = c + β1·Δslope_{t-1} + β2·Δlog(VIX)_{t-1} + ε
- **confirm**: β1 > 0 유의 + β2 < 0 유의
- **reject**: β 부호 반전 또는 무유의성
- **Action confirm**: 경기 회복 → XLF 비중 XLU/XLP 대비 오버웨이트 / **reject**: 정적 비중
- **Lens**: "sleeve 내 동적 배분 = slope·VIX 신호 기반" / reject 시 "정적 배분 회귀"

#### H10 — Insurance Reinvestment Risk
- **가설**: 생명보험 long-duration liability → 금리 하락 시 만기 재투자 수익률 ↓ → 자산-부채 듀레이션 갭. 은행 NIM 보다 *훨씬 장기* 관점
- **anchor**: SOA EV/MCEV
- **design**: 보험 종목 reinvestment_yield_spread 시계열 vs 10Y avg yield change, 3M forward Rank-IC
- **confirm**: 금리 하락 → 보험 종목 reinvestment_spread 양의 Rank-IC ≥ +0.08
- **reject**: 무관계 또는 부호 반전
- **Action confirm**: XLF 내 은행 vs 보험 분리 (인플레+금리상승 시 보험 추가 비중) / **reject**: XLF 단일 archetype 처리
- **Lens**: "XLF 내 은행-보험 분기 = duration 관점 필수" 신설 / reject 시 미신설

#### H13 — Energy Transition Capex Cycle (Utility 한정)
- **가설**: IRA 후속, util 신재생·그리드 현대화 대규모 capex → "전환 선도" vs "전통 자산 의존" Rate Base/EPS/Valuation 구조적 분기
- **anchor**: CRS IRA 분석
- **design**: util 종목 capex_to_rate_base 시계열 + 전환 선도 dummy (NEE/AEP vs SO/DUK 등) → 3M forward Rank-IC
- **confirm**: capex_to_rate_base 양 + 전환 선도 dummy 양 → Rank-IC > +0.10 (5Y window)
- **reject**: 무차별 또는 부호 반전
- **Action confirm**: util 내 전환 선도 가중↑ / **reject**: util 단일 archetype 처리
- **Lens**: "util 내 sub-archetype 분기 = 에너지 전환 capex 사이클" 신설

### Priority 2 — 중요 4 가설 (2순위 검증)

#### H4 — Quality Factor Efficacy in Slowdown
- **가설**: 2단계 정규화 Quality 복합 z (ROE·FCF/Asset·D/E) → Slowdown (ISM<50 + 3M 연속 하락) regime 3M forward Rank-IC ≥ +0.08
- **anchor**: Asness-Frazzini-Pedersen (2019) QMJ
- **design**: regime-conditional Spearman Rank-IC vs unconditional baseline. Bootstrap p-test
- **confirm**: Slowdown 평균 IC > +0.08, p<0.1 + 양 비율 > 70%
- **reject**: Slowdown 평균 IC ≤ baseline / IC < 0 2 cycle 연속
- **Action**: confirm → Quality tilt, reject → factor 정의 재검토 또는 가중 0
- **Lens**: "둔화기 Quality 선별 = 초과수익 핵심" / reject 시 "매크로 베타가 펀더멘털 압도"

#### H5 — Quality Banks during Inflation Shocks
- **가설**: 인플레+금리상승 국면 → XLF 내 은행 Quality 상위 20% (CET1, ROE) 가 하위 20% 대비 월 50bp 이상 long-short spread
- **anchor**: Damodaran RIM + Basel III + KBW
- **design**: 매월 Quality 5분위 → Q5-Q1 spread, Bootstrap 90% CI
- **confirm**: spread 월평균 > 0.5%, CI 하단 > 0
- **reject**: spread ≤ 0 / Q1 > Q5 (역전 = 강력 반증)
- **Action**: confirm → JPM/BAC 등 고품질 집중 / reject → Quality 가중↓
- **Lens**: "금리 상승기 건전 대차대조표 = 예금 유출 방어" / reject 시 "M&A·비용구조 차별화"

#### H9 — VRP + Low-Beta Defensives
- **가설**: VIX Term Structure (VIX3M/VIX) Contango → XLU/XLP/XLV 가 SPY 대비 excess. VRP 매도 전략 유사
- **anchor**: VRP 이론 + BAB·저변동성 관계
- **design**: Contango (>1) vs Backwardation (<1) 월별 (XLU - SPY) mean t-test
- **confirm**: Contango 평균 excess > 0, p<0.1
- **reject**: 두 regime 무차이
- **Action**: confirm → Contango 시 저베타 방어 비중↑ (Carry) / reject → VIX TS 미사용
- **Lens**: "Contango = VRP 수확 용이, 저베타 추가 알파" / reject 시 "VIX TS 무관"
- **★비선형 검증 필요** (R4-d): Contango→Backwardation 전환 시 비선형 개선 (KCI 권고)

#### H11 — Dividend Safety as Crisis Defensive
- **가설**: 위기 시 배당 *삭감 안 할 확률* 高 (낮은 payout, 강한 FCF) "고품질 배당주" 가 추가 알파 — H4 구체화
- **anchor**: Asness 등 quality + dividend factor 종합
- **design**: dividend_safety score (FCF 커버리지 + payout + 5Y CV) 종목 → 위기 regime 3M forward Rank-IC
- **confirm**: 위기 regime dividend_safety Rank-IC ≥ +0.10
- **reject**: 위기 vs Normal Rank-IC 무차이
- **Action**: confirm → 위기 진입 시 dividend_safety 상위 종목 tilt / reject → dividend safety 가중↓
- **Lens**: "위기 시 배당 안정 종목 = 방어 알파 핵심" / reject 시 "단순 yield = 방어 X"

### Priority 3 — 보류 2 가설 (3순위, 정교화 단계)

#### H6 — DXY Beta + EM Revenue Exposure (Staples 한정)
- **가설**: XLP 내 multinational (PG/KO/PM/PEP/CL) DXY 베타 (36M rolling) ↔ EM 매출 비중 음의 cross-sectional 상관
- **design**: 분기 LTM EM 매출 비중 + 36M DXY beta → cross-sectional regression β_dxy_i = γ_0 + γ_1·EM_Rev_% + ν_i
- **confirm**: γ_1 < -0.1, |t| > 2 (Newey-West SE), 음수 비율 > 70%
- **reject**: γ_1 ≈ 0 또는 양수 (환헤지 고도화)
- **Priority 3 사유**: XLP 내 일부 종목 미시 가설

#### H7 — IRA Drug Pricing Event Study (Pharma 한정)
- **가설**: CMS IRA 협상 대상약 발표 [-1,0,+1] 전후 30일 → 대상약 보유 pharma 음의 CAR
- **design**: Event window [-30,+30], Estimation window [-120,-31], CAR vs XLV
- **confirm**: 평균 CAR < -3%, p<0.05
- **reject**: CAR ≈ 0 (선반영) / CAR > 0 (불확실성 해소)
- **Priority 3 사유**: 특정 이벤트 국한, 상시 운용 영향 제한

### 기각

#### ~~H12 — GICS Reclassification Arbitrage~~
- **기각 사유** (R4-f): 본 sleeve 의 매크로 regime systematic 전략과 직교. 단발성 event-driven 전략. 별도 전략으로 분리 권고

---

## ④ 우리 시스템 코드 매핑 종합

| 권고 | 코드 매핑 |
|---|---|
| 2D regime axis (위기 유형 × HY OAS z) | `conditional_correlation.py.RegimeGlasso.regime_history` 입력 확장 (1D → 2D tuple) |
| 단일 robust lag k*=4M | `weight_falsification.py` input feature = `slope(t-4)` 고정 |
| 120M rolling p.corr + Bai-Perron | 신규 `core/structure/structural_break.py` (외부 라이브러리) |
| Conditioning `{SPY, HY_OAS}` + ≤4 force-include | `RegimeGlasso(corr_prior, force_include=[...])` |
| 3M forward + 2단계 정규화 + IC-weighted (R4) | 신규 `core/structure/normalize_kpi.py` 또는 `weight_panel.py` 확장 (3단계 normalize) |
| OR-gate IC + Ω drift | `weight_falsification.evaluate_weight_card` PRIMARY OR SECONDARY |
| Spearman rank corr (Priority 1) | `conditional_correlation.py` method 'pearson' → 'spearman' (1 line) |
| KCI test (Priority 2, H3·H9) | 신규 `core/structure/kci_test.py` — alarm 시 사후 분석 |
| Bond Proxy attribution (R4-c) | 신규 `core/structure/factor_beta_decomposition.py` — interpretation layer |
| 15 sub-family 진단 | `update_controller.py` reporting 단계 (e-process 외부) |
| baseline median + sd 0.8×rolling + tau standard | `weight_falsification.py` 파라미터 calibration |

---

## ⑤ 다음 단계 (Phase 2-2·2-3 진입 조건)

### 2-2 (이론 학습) → raw/theory-notes.md 작성 항목
1. **가격결정 원리** — 본 sleeve sub-archetype 5종 (staples·utility·healthcare·bank·insurance) 별 RIM/DCF/EV 모델 상세
2. **지표 의미·관계도** — Real rate·slope·HY OAS·DXY·WTI 의 macro 관계도 (M2 ↔ 미·일 국채 ↔ 환율 거시 예시 수준)
3. **regulatory regime** — IRA Medicare 협상, Basel III endgame, FERC rate case 메커니즘
4. **위기 유형 분류 의의** — 신용/외생/인플레 3분류의 실증 정당화

### 2-3 (실데이터 검증) → raw/validation-{지표}.md
- 가설 12 (Priority 1×6 + Priority 2×4 + Priority 3×2) 별 시계열 검증 도표
- 우선 검증: Priority 1 6 가설 → 산출은 partial-corr / Rank-IC / Bootstrap t-stat 도표

### 산출 무결성
- 모든 round-{1~4}.md + theory-notes.md + validation-*.md 존재 → main 이 study_session.yaml 수용
- 하나라도 누락 → yaml 거부 (STUDY-KIT §★바탕 raw 강제)

---

## ⑥ 빈틈 / TBD (main 결정 필요)

1. **2D regime tuple → conditional_correlation.RegimeGlasso 확장** — 현재 1D regime_history 만 지원. 사용자 승인 후 변경 또는 별도 wrapper
2. **EDGAR Y-9C 자체 파싱 우선순위** — R4 권고 Priority 3 (vendor 데이터 사용 권고 / 본 시스템 1인 환경 = vendor 부재) → 결국 EDGAR 자체 파싱 fallback 채택 필요 여부 main 판단
3. **Insurance long-duration data** — H10 검증의 reinvestment_yield_spread 데이터 수집 경로 (FRED Treasury yield curve 활용 가능, 보험사 보유 채권 vintage 는 EDGAR 추가 파싱)
4. **HKCI Test 라이브러리 채택** — Python `kci` 또는 `causal-learn` 라이브러리 도입 (외부 의존성 신규)
5. **VECM 라이브러리 채택** — H8 의 VECM 검증 시 `statsmodels.tsa.vector_ar` 사용 또는 자체 OLS

---

## ⑦ 정직 명시 — 한계 (자가 점검)

- 자문 4R 으로 13 가설 (H1~H13) 도출 + 검증 방법론 완비 + 코드 매핑 명확화 — 본 직조는 *이론 + 방법론* 차원 완성
- **실데이터 검증 0** — 2-3 단계가 핵심 falsifiability test (라이브 데이터 PIT 시계열 검증). 본 direction.md = "검증할 것의 design", 데이터 통과 후에야 yaml 자격
- 자문은 Gemini Pro 단독 — claude-web 채널 경합 회피 위해 사용 안 함. 다른 모델 perspectives 부재 (R1 의 학술 ref 는 검증 가능, R2 의 methodology 권고는 single source — 다음 자문 가능 시 cross-check 권고)
- 합성 데이터 시뮬 (v1 산출 raw/lens-hypothesis-quickcheck.txt) 은 prior 정합 확인 수준 — *실데이터 검증 아님* → 본 v2 에서 폐기 동등

---

## ⑧ 보고 → main(btn-Codlearn)

본 direction.md 완성 → main 승인 대기. **승인 전 2-2 진입 금지** (STUDY-KIT §2-1 게이트).

승인 시 옵션:
- (A) **전체 승인** → 2-2 진입 (raw/theory-notes.md 작성)
- (B) **부분 승인** → 특정 가설/방법론 수정 요청 → R5 재자문 또는 직접 수정 → 재제출
- (C) **반려** → R1~R4 재검토 또는 방향 전환

---

## 참조

- **자문 원문 (raw/)**:
  - `raw/round-1.md` (R1 이론 17 ref)
  - `raw/round-2.md` (R2 검증 방법론)
  - `raw/round-3.md` (R3 가설 9 + (a)(b))
  - `raw/round-4.md` (R4 (c)(d)(e)(f) 보충 + 가설 13 까지)
- **archive 전문**: `~/.claude/docs/archive/research-raw/eq_us_defensive-round{1,2,3,4}-20260530.txt`
- **v1 산출** (참고용, 폐기 X — STUDY-KIT 지시):
  - `study_session.yaml` (v1, 7블록)
  - `summary.md` (v1)
  - `raw/lens-research-notes.md` (v1)
  - `raw/lens-hypothesis-quickcheck.txt` (v1, synthetic — 폐기 동등)
- **STUDY-KIT**: `D:/projects/Inv/STUDY-KIT.md` §2 (v2)
