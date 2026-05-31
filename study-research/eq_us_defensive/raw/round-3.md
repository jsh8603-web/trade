# Round 3 — eq_us_defensive 핵심 가설 + 반증조건 (Gemini Pro 자문 원문)

**일시**: 2026-05-30
**자문 채널**: Gemini Pro (gemini-search.js promo, 3rd of day)
**아카이브**: `~/.claude/docs/archive/research-raw/eq_us_defensive-round3-20260530.txt`
**프롬프트**: `C:/Users/jsh86/AppData/Local/Temp/search-r3-eq-us-defensive.md`
**응답**: 11743 chars, 223 lines (H1~H9 + (a)(b) 완료, (c)~(f) 절단 — R4 보충)

---

## 핵심 가설 9 (H1~H9) — 라이브 운영용

> 각 H{N} 구조: 재정의 / 이론 anchor / 검증 design / 확신 조건 / 반증 조건 / Action / Lens 갱신 / Priority

### H1 — Real Rate Sensitivity Dichotomy (Priority 1 필수)

**재정의**: 다른 매크로 변수 통제 시, DFII10 1σ 상승 충격은 XLU/XLP 향후 3M 선도수익률에 음의 영향, XLF 에 양의 영향.

**anchor**: Ilmanen (2011) bond proxy; Boyd-Gertler-Bernanke (1994, 1999) 은행 대차대조표 채널.

**design**: 120M rolling p.corr(Sector_Return_fwd3m, ΔDFII10_lag1m | SPY_lag1m, ΔVIX_lag1m, ΔOAS_lag1m). conditioning set 확장.

**confirm**:
- XLU/XLP p.corr < -0.15 (window 75% 기간 유지)
- XLF p.corr > +0.10 (window 75% 기간 유지)
- 두 조건 동시 → 확신도 최고

**reject**:
- 부호 반전 12M 이상
- e-CUSUM 임계 h=5 초과 (구조적 변화)
- rolling p-value > 0.1 가 24M 이상

**action**:
- confirm → 금리 path 기반 XLU/XLP vs XLF 반대 조절
- reject → real rate driver 가중 0 강등

**lens 갱신**:
- confirm → regime_reading "real rate↑ = 방어 multiple 압박 + 금융 NIM 개선" 유지
- reject → estimation_note "real rate 채널이 IRA Capex 사이클 / 디레버리징 등에 의해 중화"

### H2 — Yield Curve Slope NIM Leading (Priority 1 필수)

**재정의**: (DGS10-DGS2) 월별 변화량이 3~6M lag 로 XLF 내 은행 sub-group 의 *excess return vs SPY* 에 양의 선행성.

**anchor**: Stigum's Money Market (2007).

**design**: CCF scan 0~12M → 최적 k* → 120M rolling p.corr(Bank_Excess_Return_fwd_k*, Δslope | SPY).

**confirm**:
- CCF 최적 lag 3~6M + p<0.05
- rolling p.corr > +0.2 (window 80% 기간 유지)

**reject**:
- 최적 lag 0 또는 음으로 이동 (선행성 소멸)
- 부호 반전 12M (장기 침체 우려가 단기 NIM 효과 압도)
- Rank-IC < sleeve median baseline 12M 이상

**action**:
- confirm → 슬립 = XLF 비중 조절 핵심 선행 input
- reject → slope driver 가중 0, 단기금리(SOFR/FFR) 대체

**lens 갱신**:
- confirm → "장단기 금리차 확대는 Q+1~2 은행 실적 개선 선반영"
- reject → "예금 베타 상승·단기자금 시장 왜곡으로 slope-NIM 채널 약화"

### H3 — HY OAS Defensive Outperformance Trigger (Priority 1 필수)

**재정의**: HY OAS 가 임계 (200D MA + 1.5σ) 상회하는 *신용위기* 국면에서 sleeve 전체 (SPY 대비) excess return > 0. 단, *인플레이션 충격* 국면에서는 효과 약화/소멸.

**anchor**: Frazzini-Pedersen (2014) BAB.

**design**:
- Regime 정의: (1) Credit Crisis = ΔOAS > 90 percentile AND VIX > 90 / (2) Inflation Shock = YoY CPI > 90 AND ΔFFR > 0 / (3) Normal
- Bootstrap t-test on (Sleeve - SPY) mean

**confirm**:
- Credit Crisis 평균 excess > 0, p < 0.05
- Inflation Shock 신뢰구간 0 포함 (효과 부재 확인)

**reject**:
- Credit Crisis 평균 excess ≤ 0 (p < 0.1)
- Inflation Shock 에 Credit Crisis 보다 더 강한 양의 excess (역전)

**action**:
- confirm → OAS+VIX = risk appetite 바로미터, OAS 급등 → sleeve 비중 확대
- reject → OAS 신호 가치 재평가, sleeve 방어 정체성 변화 가능성

**lens 갱신**:
- confirm → "본 sleeve = 신용 경색 국면 flight-to-quality 강력"
- reject → "전통적 신용위기 피난처 역할 변화, 인플레 헤지 등 다른 성격 부각"

### H4 — Quality Factor Efficacy in Slowdown (Priority 2 중요)

**재정의**: 2단계 정규화 Quality 복합 z (ROE·FCF/Asset·D/E z avg) 가 Slowdown 국면 (ISM PMI < 50 + 3M 연속 하락) 에서 3M forward Rank-IC ≥ +0.08 유지.

**anchor**: Asness-Frazzini-Pedersen (2019) Quality Minus Junk.

**design**: regime-conditional Spearman Rank-IC (Slowdown month only). Baseline = unconditional median IC. Bootstrap p-test 차이.

**confirm**:
- Slowdown 평균 Rank-IC > +0.08, Bootstrap p < 0.1
- Rank-IC 양 비율 > 70%

**reject**:
- Slowdown 평균 IC ≤ baseline
- IC < 0 가 2 Slowdown 사이클 연속

**action**:
- confirm → Slowdown 진입 시 Quality 상위 포트폴리오 tilt
- reject → Quality 정의 재검토 (수익성 안정성 추가) 또는 Slowdown 가중 0

**lens 갱신**:
- confirm → "경기 둔화기 Quality 종목 선별이 초과수익 핵심"
- reject → "전통적 Quality factor가 경기 둔화기 무효. 매크로 베타가 종목 펀더멘털 압도"

### H5 — Quality Banks Outperform during Inflation Shocks (Priority 2 중요)

**재정의**: 인플레+금리상승 국면에서 XLF 내 은행 Quality 상위 20% (CET1, ROE) 그룹이 하위 20% 대비 월 50bp 이상 long-short spread 기록.

**anchor**: Damodaran RIM; Basel III + KBW.

**design**:
- 매월 말 Quality(CET1, ROE rank avg) 5분위 → Q5-Q1 spread
- Bootstrap 90% CI

**confirm**:
- Q5-Q1 월평균 > 0.5%
- CI 하단 > 0

**reject**:
- Spread ≤ 0
- Q1 > Q5 (저퀄리티가 outperform) — 강력 반증

**action**:
- confirm → 금리상승+인플레 시 XLF 내 JPM/BAC 등 고품질 은행 집중
- reject → XLF 종목 선택에서 Quality factor 가중↓

**lens 갱신**:
- confirm → "금리 상승기 건전 대차대조표 은행 = 예금 유출 방어 + 대출 성장 유리"
- reject → "금리 급등 시 Quality 보다 M&A 가능성·비용구조 차별화 야기"

### H6 — DXY Beta + EM Revenue Exposure in Staples (Priority 3 보류)

**재정의**: XLP 내 multinational (PG/KO/PM/PEP/CL) DXY 베타 (36M rolling) 가 EM 매출 비중과 통계적 유의한 음의 cross-sectional 상관.

**anchor**: 10-K Geographic Segment, currency exposure 이론.

**design**:
- 매 분기 LTM EM 매출 비중 + 36M rolling DXY beta
- cross-sectional regression: β_dxy_i = γ_0 + γ_1·EM_Rev_%_i + ν_i
- γ_1 시계열 t-test (Newey-West SE)

**confirm**:
- γ_1 평균 < -0.1, |t| > 2
- 음수 관측 전체기간 70% 이상

**reject**:
- γ_1 평균 ≈ 0 또는 양수 (환헤지 고도화로 관계 약화)

**action**:
- confirm → DXY 강세 시 EM 매출 낮은 내수 staples 비중↑
- reject → DXY 를 staples 종목 차별화 요인에서 제외

**lens 갱신**:
- confirm → "강달러 = EM 매출 다국적 staples 부담"
- reject → "정교한 환헤지로 매출 지역만으로 달러 민감도 판단 불가"

### H7 — IRA Drug Pricing Negotiation Impact (Priority 3 보류)

**재정의**: CMS IRA 약가 협상 대상 약품 발표일 [-1,0,+1] 전후 30일 window 에서 대상약 매출 비중 高 제약사 (MRK/BMY/JNJ 등) 가 XLV 벤치마크 대비 유의한 음의 CAR.

**anchor**: KFF IRA, Event Study.

**design**:
- Event date = CMS 공식 발표일
- Estimation window [-120, -31]
- Event window [-30, +30]
- AR_it = R_it - (α_i + β_i·R_XLV_t), CAR_i = Σ AR_it
- 그룹 평균 CAR < 0 t-test

**confirm**:
- Event window [0, +30] 평균 CAR < -3%, p < 0.05

**reject**:
- CAR ≈ 0 (시장 선반영)
- CAR > 0 (불확실성 해소 해석)

**action**:
- confirm → IRA 이벤트 시 관련 종목 비중 축소 또는 숏 고려
- reject → IRA 뉴스 = 단기 트레이딩 신호 미사용

**lens 갱신**:
- confirm → "IRA 약가 협상 = 특정 제약주 유의 negative catalyst"
- reject → "시장 IRA 리스크 상당 선반영"

---

## 누락 보강 가설 — H8, H9 (R3 자문 추가 도출)

### H8 — Great Rotation within Sleeve (Priority 1 필수)

**가설**: log(XLF/XLU) 상대 강도가 (DGS10-DGS2) 와 양의 관계, VIX 와 음의 관계. 경기 회복기 = sleeve 내 자금이 방어 → 금융 이동.

**anchor**: 경기 사이클 sector rotation.

**design**: VECM 또는 다중회귀. Δlog(XLF/XLU)_t = c + β1·Δslope_{t-1} + β2·Δlog(VIX)_{t-1} + ε.

**confirm**: β1 > 0 (유의), β2 < 0 (유의).

**action**: 경기 회복 신호 → XLF 비중 XLU/XLP 대비 오버웨이트. 직접 sleeve 동적 배분 논리.

### H9 — VRP + Low-Beta Defensives (Priority 2 중요)

**가설**: VIX Term Structure (VIX3M/VIX) Contango 시 XLU/XLP/XLV 가 SPY 대비 excess. VRP 매도 전략과 유사 수익 패턴.

**anchor**: VRP 이론, BAB 와 저변동성 관계.

**design**: Contango (>1) vs Backwardation (<1) 월별 (XLU - SPY) mean 차이 t-test.

**action**: Contango 깊을 때 저베타 방어 비중↑ ("Carry" 전략).

---

## R3 (a)(b) 빈틈 답변

### (a) Regime threshold 민감도 분석 — Grid Search + 3D Surface

**방법**:
- OAS 임계 +1.0z ~ +2.5z (0.1z 단위)
- VIX 임계 80%~95% percentile (1pt 단위)
- 각 격자에 대해 H3 초과수익률 (또는 t-stat) 계산
- 3D surface plot → 임계 안정성 시각화

**해석**: 결과가 특정 값에만 민감 → regime 정의 위험. 안정적 "고원" 영역 → 강건.

### (b) EDGAR Y-9C 자체 파싱 우선순위 — Priority 3 (낮음)

**근거**: H5 검증에 필요한 CET1/ROE 는 Bloomberg/FactSet/Capital IQ 등 상용 벤더 정제 제공. 자체 파싱은 (1) 특수 변수 발굴 (2) 비용 절감 목적일 때만.

**단 본 시스템 제약**: 단일 사용자 1인 환경 → 상용 벤더 라이선스 부재. **EDGAR 자체 파싱은 backup option 으로 유지**, 우선순위는 가설 검증 critical path 가 아닌 정교화 단계.

---

## (c)~(f) 빈틈 → R4 후속 자문 (별도 round-4.md)

R3 응답 11743 chars 절단으로 (c) 부분 + (d)(e)(f) 미완성. Round 4 보충 자문에서 메움.

---

## 원문 reference (전문)

전문 → `~/.claude/docs/archive/research-raw/eq_us_defensive-round3-20260530.txt`
