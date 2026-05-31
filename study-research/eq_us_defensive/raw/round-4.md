# Round 4 — eq_us_defensive R3 빈틈 보충 자문 (Gemini Pro 원문)

**일시**: 2026-05-30
**자문 채널**: Gemini Pro (gemini-search.js promo, 4th of day, 8 credits used)
**아카이브**: `~/.claude/docs/archive/research-raw/eq_us_defensive-round4-20260530.txt`
**프롬프트**: `C:/Users/jsh86/AppData/Local/Temp/search-r4-eq-us-defensive.md`
**응답 길이**: 6143 chars, 79 lines (간결 보충 — (c)(d)(e)(f) 4 항목)

---

## (c) Bond Proxy Attribution — Rolling Multi-Regression

**Regression spec**:
```
XLU_rate_beta_rolling(t) = α + β1·ΔDFII10 + β2·ΔT10YIE + β3·IRA_dummy + β4·crisis_dummy + ε
```
- 종속변수: XLU 의 36M rolling rate beta (XLU 수익률을 국채 금리 변화에 회귀)
- 독립변수: 실질금리·기대 인플레이션·IRA 정책·위기 dummy

**β(t) 시계열 해석**:
- **β1(t)** 실질금리: 시장이 XLU 를 *실질 성장 연동 자산* 으로 보는 정도
- **β2(t)** 기대 인플레이션: 시장이 util 의 *pricing power* (인플레 헤지) 를 평가하는 정도. **2022 이후 중요성 ↑ 가능성**
- **β3(t)** IRA dummy: 법안 통과 후 capex 증가·Rate Base 성장 기대의 *구조적 변화*
- **β4(t)** crisis dummy: 위기 시 flight-to-quality 로 채권 동조화 강화 / 약화 판단

**시스템 코드 매핑**:
- 경로: `core/structure/factor_beta_decomposition.py` (신규) — meta-signal 또는 interpretation layer
- 역할: H1 신호 강도 *해석* + 어느 매크로 변수 conditioning 강화할지 결정 ("β2 가 지배적일 때 기대 인플레 데이터 가중↑")
- 직접 매매 신호 X — H1 가설 신호의 attribution 만 수행

## (d) 선형 vs 비선형 partial-corr — 단계별 도입

**가설별 필요성 평가**:

| 가설 | 선형 충분 | 비선형 필요 | 근거 |
|---|---|---|---|
| H1, H2, H4, H5, H6, H8 | ✓ | | 선형 관계 1차 검증 가능 |
| **H3** (위기 유형별 dispersion) | | ✓ | OAS 작은 변동 무영향, 임계 넘으면 *상전이* — 비선형 phase transition |
| **H9** (VIX term structure) | | ✓ | Contango→Backwardation 전환 시 low-beta 비선형 개선 |

**단계별 도입 priority**:

**Priority 1 (즉시)**: Spearman Rank Correlation
- 방법: `df.corr(method='pearson')` → `df.corr(method='spearman')` 한 줄 변경
- 효과: H3 "OAS↑ → dispersion↑" 단조적 관계 효과적 capture (비선형 있어도)
- 시스템 매핑: `conditional_correlation.py` 의 nonparanormal 처리에 자연스럽게 통합

**Priority 2 (H3·H9 심화)**: Kernel-based Partial Correlation (KCI test)
- 방법: Python `kci` 라이브러리, `is_dispersion_independent_of(X) given HY_OAS_change(Z)` 조건부 독립성 테스트
- 검증: OAS Z 임계 이하 → 독립성 기각 X / 임계 초과 → 강한 조건부 의존성. H3 nonlinear *switch* 통계적 입증

**Priority 3 (보류)**: Gaussian Copula
- 용도: 자산 간 tail dependence 모델링 (위기 동반 하락)
- 평가: 방향성 예측 신호 개발에는 *과도* (overkill). 리스크 관리 모듈에서나 고려

## (e) 다중 KPI → 단일 score 결합 — IC-Weighted 하이브리드

**4 방법 trade-off**:

| 방법 | 장점 | 단점 |
|---|---|---|
| 단순 평균 z | 해석 쉬움, anchor 명확 | KPI 동등 중요 가정 오류. 이질 sub-archetype 신호 희석 |
| 역변동성 가중 (IVW) | noisy KPI 영향 축소 | 본 sleeve 저변동 → KPI 변동성 차이 자체가 *신호* (NIM 변동 = 노이즈 X, 핵심 정보). IVW 가 과소평가 위험 |
| **IC-Weighted** | 성과 지향, 가장 논리적 (예측력 비례 가중) | IC 자체 instability + overfitting 위험 |
| PCA | 객관적 공통 요인 추출 | 제1주성분 경제적 의미 해석 어려움 (블랙박스) |

**Priority 1 권고 (하이브리드)**:
- **주력**: IC-Weighted (성과 직접 기여 KPI 에 높은 가중)
- **보조**: 단순 평균 z-score (robustness check)
- **안정화**: 긴 rolling window 60M + ICAR (IC-to-Annualized-Risk) Sharp-ratio 형태 가중
- **안전장치**: 두 score 간 큰 괴리 발생 → 모델 이상 징후 → 심층 분석 trigger

**우리 시스템 코드 매핑**:
- 경로: `core/data/weight_panel.py` 또는 신규 `core/structure/normalize_kpi.py`
- 2단계 정규화 (R2 권고) 와 결합:
  - 1단계 within-industry z
  - 2단계 sleeve-wide rank z
  - 3단계 sub-archetype 내 IC-weighted aggregate (본 R4 추가)

## (f) 누락 가설 후보 — H10, H11, H13 추가 + H12 기각

**H10 — Reinvestment Risk in Insurance (Priority 1 시급)**
- **내용**: 생명보험 long-duration liability 보유 → 금리 하락 시 만기 재투자 수익률 ↓ → 자산-부채 듀레이션 갭 관리 난이도. 은행 NIM 과 유사하지만 훨씬 *장기* 관점
- **위치**: XLF 내 은행 vs 보험 성과 분기 설명의 핵심 — **H2 (NIM) 보완**해 금융 sector 정교화

**H11 — Dividend Safety as Crisis Defensive (Priority 2 중요)**
- **내용**: 배당 수익률 *높은* 주식보다 위기 시 배당 *삭감 안 할 확률* (낮은 payout ratio, 강한 FCF) 高 "고품질 배당주" 가 추가 알파
- **위치**: H4 (quality slowdown) *구체화·심화*. '퀄리티' 막연 개념을 '배당 안정성' 측정 가능 지표로 좁힘

**H13 — Energy Transition Capex Cycle (Priority 1 시급)**
- **내용**: IRA 후속, util 신재생·그리드 현대화 대규모 capex → 성장성 분화. "전환 선도 그룹" vs "전통 자산 의존 그룹" Rate Base/EPS/Valuation 구조적 차이
- **위치**: H7 (정책 이벤트) 보다 H13 (구조적 변화) 가 *5~10Y 장기 테마*. util 섹터 내 승자·패자 가르는 가장 중요한 장기 driver

**H12 — GICS Reclassification Arbitrage (Priority 3 기각 권고)**
- **내용**: GICS 분류 변경 시 종목 sector 이동 수급 효과
- **기각 사유**: 본 sleeve 의 매크로 regime 기반 systematic 전략과 *직교*. 단발성 event-driven 전략 → 지속 알파 source 모델링 어려움. 별도 전략으로 분리 권고

---

## 최종 가설 list (12개) + Priority

| # | 가설 | 우선순위 |
|---|---|---|
| **H1** | Real rate sensitivity dichotomy (util/staples - / banks/insurance +) | 1 필수 |
| **H2** | Yield curve slope NIM leading (3-6M lag) | 1 필수 |
| **H3** | HY OAS defensive outperformance (위기 유형별 dispersion) | 1 필수 |
| **H8** | Great rotation within sleeve (XLF/XLU log ratio vs slope/VIX) | 1 필수 |
| **H10** | Insurance reinvestment risk (장기 duration gap) | 1 필수 |
| **H13** | Energy transition capex cycle (utility IRA structural) | 1 필수 |
| H4 | Quality factor efficacy in Slowdown | 2 중요 |
| H5 | Quality banks in inflation+rate spike | 2 중요 |
| H9 | VRP + low-beta defensives (Contango) | 2 중요 |
| H11 | Dividend safety as crisis defensive | 2 중요 |
| H6 | DXY beta + EM revenue exposure (staples) | 3 보류 |
| H7 | IRA drug pricing event study | 3 보류 |
| ~~H12~~ | ~~GICS reclassification~~ | ~~기각~~ |

---

## R4 → 코드 매핑 통합 summary

| 권고 | 코드 매핑 |
|---|---|
| (c) Bond proxy attribution rolling regression | 신규 `core/structure/factor_beta_decomposition.py` — interpretation layer |
| (d) Spearman rank corr 도입 Priority 1 | `conditional_correlation.py` method 'pearson' → 'spearman' (1 line change), nonparanormal 처리에 자연 통합 |
| (d) KCI test Priority 2 (H3·H9 한정) | 신규 `core/structure/kci_test.py` — H3·H9 alarm 시 사후 분석 |
| (e) IC-weighted 하이브리드 score | 신규 `core/structure/normalize_kpi.py` 또는 `weight_panel.py` 확장 — 3단계 normalize (within-industry → sleeve rank → IC-weighted aggregate) |
| (f) H10 보험 reinvestment risk | 추가 indicators: liability_duration_gap, reinvestment_yield_spread (보험 한정) |
| (f) H13 energy transition capex | 추가 indicators: capex_to_rate_base, IRA_subsidy_exposure (util 한정 sub-archetype) |

---

## R1+R2+R3+R4 종합 → direction.md 합성 준비 완료

자가 점검:
- ① 이론 수집 방향: 학술 17 ref + 거시 driver 부호 분기 + 4 sector KPI ✓
- ② 이론 검증 방향: regime axis · lag · rolling p.corr · 2단계 정규화 + IC-weighted (R4 보강) · OR-gate IC+Ω drift ✓
- ③ 핵심 가설 초안 12 + 반증조건 + Priority + (R4 추가 비선형 / KPI 결합 / 추가 가설) ✓
- 빈틈 (c)~(f) 메움 ✓

→ direction.md 합성 단계 진입 가능.

---

## 원문 reference (전문)

전문 → `~/.claude/docs/archive/research-raw/eq_us_defensive-round4-20260530.txt`
