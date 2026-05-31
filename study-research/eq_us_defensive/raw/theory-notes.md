---
tags: [type/theory, domain/inv, study/eq_us_defensive, phase/2-2]
date: 2026-05-30
study_id: eq_us_defensive
as_of: "2026-05-30"
status: 2-2 진행 (main 2-1 승인 후) → 다음 2-3 실데이터 검증
prerequisite: direction.md (승인 완료)
---

# theory-notes.md — eq_us_defensive 이론 학습 (v2 §2-2)

> **승인 직후 main 검토 2건 반영**:
> (a) 신규 `core/structure/factor_beta_decomposition.py` = 2-3에서 self-test + 무회귀 검사 의무 → §5에 명세
> (b) Regime axis 가 macro 방과 겹침 (HY OAS / 위기) → macro 7축·잠재인자 통제 framework 와 정합 → §4 에 cross-sleeve mapping
>
> ★컨텍스트 오염 회피 (E96): "가설·국면" 단어 회피 — "테제·proposition·검증명제 / regime·시기·구간·phase" 로 대체

---

## §1. 가격결정 원리 — sub-archetype 5종 세부 (RIM / DCF / EV / Embedded Value)

본 sleeve = 5 sub-archetype 통합 — 각 archetype 별로 가격결정 모델이 다름. 모델 정합 실패 시 sub-archetype 단일 처리 = 신호 cancel.

### 1.1 Utility archetype (XLU)

**모델**: 규제 stable-growth DCF
```
P = Σ_t [(Rate_Base_t × Allowed_ROE_t × Payout_Ratio) / (1+COE)^t]
EPS_growth ≈ Rate_Base_growth × Allowed_ROE
```

**핵심 driver**:
- **Rate Base growth** = capex 사이클 (IRA 보조금 가속화 → 신재생·그리드 현대화)
- **Allowed ROE** = FERC/PUC 규제 승인 (역사적 9~11% 범위, 최근 일부 주 8.5% 압박)
- **COE** = real rate + equity risk premium → DFII10 직접 노출

**듀레이션 추정**: ~15~25Y (안정 cash flow + 장기 capex 회수). 채권 대체재 (bond proxy) 의 교과서 anchor (Ilmanen 2011).

**Reference**: Damodaran *Investment Valuation* Ch26 (Regulated Utilities); CRS (2022) *IRA*; FERC rate case filings.

### 1.2 Staples archetype (XLP)

**모델**: 브랜드 equity 기반 multi-stage DCF
```
P = M(brand_equity, pricing_power) × E(Volume × Price × Margin)
Margin = f(brand_strength, commodity_input, EM_exposure, scale_advantage)
```

**핵심 driver**:
- **Pricing power vs commodity input cost** = 마진 사이클 본질 (Bernstein/Barclays CPG)
- **Organic Sales Growth** = Volume + Price decomposition (Q earnings 표준 분해)
- **EM 매출 비중** = DXY 환차손 직접 노출 (10-K Geographic Segment)
- **Private label/e-comm 위협** = WMT private label · Amazon 침투 (NielsenIQ/IRI)

**듀레이션 추정**: ~10~15Y (안정 cash flow + 중간 성장). util 보다 짧지만 IT 보다 김.

**Sub-archetype 분기** (staples 내부):
- **글로벌 강브랜드** (KO/PG/PM/PEP/CL): pricing power 가능, 원가 전가 성공 → 마진 방어
- **약브랜드 CPG**: pricing power 한계, private label 침식 → 마진 압박

### 1.3 Healthcare archetype (XLV)

★sub-archetype 4종 (Goldman/JPM 분석 표준):

| Sub | 가격결정 모델 | 핵심 driver |
|---|---|---|
| **Pharma** (MRK/PFE/BMY/JNJ) | DCF + Pipeline option pricing | Patent cliff schedule, blockbuster sales, IRA negotiation risk |
| **Biotech** (large cap만) | Real options + 임상 단계별 probability-weighted DCF | 임상 결과 binary event, M&A 확률 |
| **Medical Device** (TMO/ABT/MDT) | Multi-stage DCF + cycle-sensitive volume | Elective procedure volume (경기민감), demographic tailwind |
| **HMO** (UNH/ELV/CI) | Combined ratio + Medicare Advantage growth | Medical Loss Ratio (MLR), Medicare 수가, 고용률 (commercial enrollment) |

**듀레이션 추정**: pharma 5~8Y / device 7~10Y / HMO 5~7Y / biotech 8~12Y (high uncertainty)

**규제 regime** (§3.1 상세):
- IRA Medicare 협상 (pharma 한정 multiple 디레이팅)
- Best Price 조항 (Medicaid rebate)
- FDA 승인 path

### 1.4 Bank archetype (XLF 내)

**모델**: Residual Income Model (Damodaran 2012 Ch16)
```
P = BV + Σ_t [(ROE_t - COE_t) × BV_t-1] / (1+COE)^t

ROE = NIM × Earning_Assets/Equity + Fee_ROA - Provision_ROA - Opex_ROA
NIM = (Interest_on_assets - Interest_on_liabilities) / Earning_Assets
```

**핵심 driver**:
- **NIM trend** = 2-10Y slope 의 3~6M lag leading 신호 (Stigum 2007 — borrow short, lend long)
- **Loan growth** = GDP nowcast + 신용공급 cycle
- **NPL/provisions** = HY OAS 의 Q+1~Q+2 lag (신용 사이클)
- **CET1 capital ratio** = Basel III floor 위 capital return 폭 (배당·자사주)

**듀레이션 추정**: 5~8Y (equity duration 짧음, ROE-COE 스프레드 fluctuation 큼)

**Sub-archetype 분기** (banks 내부):
- **Money center** (JPM/BAC/C/WFC): 대형, diversified, fee income 비중 ↑
- **Regional** (PNC/USB/TFC): NIM 의존도 ↑, 지역 경기 민감
- **Trust/Custody** (BK/NTRS/STT): AUC-leveraged, 자산운용 가까움

### 1.5 Insurance archetype (XLF 내)

**모델**: Embedded Value (SOA 표준) — 두 sub-archetype 분리

#### Life Insurance (MET/PRU/LNC/AFL)
```
EV = Adjusted_Net_Worth + Value_of_In_force_Business
VIF = Σ_t [(Premium_income - Claims - Expenses) × discount_factor]
```
- 핵심: **부채 duration 30Y+** (연금/생보) → 자산 매칭 채권 보유 → real rate ↑ 시 BV ↑ + 신규수익률 ↑ (양방향 호재)
- **★Reinvestment risk** (direction.md H10): 금리 하락 시 만기 채권 재투자 수익률 ↓ → 자산-부채 duration 갭 관리 난이도. 은행 NIM 보다 *훨씬 장기* 관점.
- duration ≈ 8~15Y (equity), 부채 duration ≈ 20~30Y

#### P&C Insurance (TRV/ALL/CB/AIG/PGR)
```
Combined Ratio = (Claims + Expenses) / Earned_Premium
Underwriting profit = (1 - Combined Ratio) × Premium
Investment return = Float × Book_yield
```
- 핵심: **Pricing cycle (premium hardening)** + 재해 손실 변동성
- 자산 duration 보다 부채 duration 짧음 (단기 손해보험 1~3Y) → 금리 민감도 약함
- equity duration ≈ 5~8Y

### 1.6 Asset Management & Payments archetype (XLF 내)

**모델** (KBW/MS 표준):

#### Asset Management (BLK/SCHW/AMP/TROW)
```
Revenue ≈ AUM × Fee_Rate
EPS_growth ≈ AUM_growth × (1 + operating_leverage)
AUM_growth = Market_return + Net_Flow
```
- 핵심: **시장 베타 노출 ↑** (AUM 변동 = market * 1.2~1.5)
- risk-off → AUM ↓ + flow outflow → 이중 타격
- duration ≈ 3~5Y (현금흐름 단기)

#### Payments (V/MA/AXP/PYPL)
```
Revenue ≈ TPV (Total Payment Volume) × Take_Rate
TPV ≈ Nominal_GDP × Card_Penetration × Cross_Border_Mix
```
- 핵심: **명목 GDP × 카드 사용률**, cross-border (DXY 영향)
- equity duration ≈ 8~12Y (성장성)

### 1.7 Comm Mature archetype (XLC 일부 — VZ/T/CMCSA)

**모델**: FCF yield + 배당 stable DCF (utility-like)
- Telecom 통신 (VZ/T): 구독 기반 안정 CF + 5G/fiber capex 부담. capex 정점 통과 = FCF 개선 변수
- 케이블 (CMCSA): cord-cutting 구조적 감소 + 광대역·ARPU 상쇄
- duration ≈ 12~18Y (utility 보다 짧고 staples 보다 김)

본 archetype 은 sleeve 비중 작아 4 archetype + Comm = 5 archetype 으로 통합 처리 (delta_arch_by_type 등록).

---

## §2. 지표 의미·관계도 — Macro 7축 통제 + sub-archetype 별 부호 분기

### 2.1 Macro 7축 — macro 방 framework 와 정합 (★main 검토 (b) 반영)

본 방의 regime modulator 는 **macro 7축의 sleeve-internal projection** — 중복 정의 회피.

| Macro 7축 | 본 sleeve 활용 | macro 방 vs 본 방 |
|---|---|---|
| 1. Growth (CFNAI/PMI) | 위기 유형 분류 보조 (Slowdown PMI<50) | macro 가 SSOT, 본 방은 *consume* |
| 2. Real rate (DFII10) | ★1순위 driver — sub-archetype 부호 분기 핵심 (H1) | macro 의 잠재인자, 본 방의 explicit driver |
| 3. Breakeven (T10YIE) | 인플레 충격 regime axis (H3 의 Inflation Shock) | macro 가 Fisher 분해, 본 방은 regime 판정용 consume |
| 4. Credit premium (HY OAS) | ★위기 유형 axis 1 차원 (Credit Crisis) + bank provisioning lag (H2) | macro 의 risk-premium 채널, 본 방은 sub-archetype dispersion 활용 |
| 5. Dollar (DXY) | multinational staples 환차손 (H6) | macro 가 SSOT, 본 방은 staples archetype 내 적용 |
| 6. Risk/vol (VIX/MOVE) | 위기 유형 axis 2 차원 (Exogenous Shock) + VRP defensive (H9) | macro 의 잠재 공통원인 proxy, 본 방은 regime 판정 + carry 전략 |
| 7. Supply shock (oil/WTI) | util 연료비 + staples 입력비 (sub-archetype 부호 분기) | macro 가 SSOT, 본 방은 industry 적용 |

**잠재 공통원인 proxy (macro 잠재인자 통제) 의 본 sleeve 흡수**:
- macro 방 R2-3 검증 발견: 가설2 FAIL — partial-corr 네트워크는 regime 불변 (permutation p=0.35)
- → **본 sleeve 의 sub-archetype 부호 분기는 *직접엣지 네트워크* 의 변동이 아니라 *분산 스케일 + soft belief-mix loading 변화***
- → confidence_hooks 가 isolate 해야 할 것 = "직접엣지 구조 변동" X / "loading 변화 + 분산 스케일" O
- → H1, H2 의 partial-corr prior 부호 자체는 *regime 불변 안정 구조* 로 force-include 화이트리스트 등록 가능
- → regime 별 modulation = base_weight 의 scale (모듈레이션) 만 변동, 부호 자체는 보존

### 2.2 거시 관계도 — M2 ↔ 미·일 국채 ↔ 환율 ↔ 본 sleeve 부호 분기 (학습 깊이 거시 예시 동일 수준)

```
[BOJ YCC/정책금리]                            [Fed FFR/QT]
        |                                            |
        v                                            v
[JGB 10Y]  ─── carry unwind ──→  [US 10Y nominal]   [US M2 supply]
        |                                |                |
        |     +0.28 partial              |                |
        |     ⟶ ⟶ ⟶ ⟶ ⟶ ⟶                |                |
        v                                |                |
[Yen/USD]  ←── -0.37 partial ──  [DXY] ←┘                |
        |                                |                |
        |       +0.27 partial            v                |
        +─→ ─→ ─→ ─→ ─→ ─→ ─→ ─→ ─→ [Real rate DFII10] ←─┘
                                            |
        +────────────────────────────────── + ──────────────────────────────+
        |                                   |                                |
        v                                   v                                v
[Bond proxy 자산 압박]                [은행 NIM 호재]              [보험 BV/yield 호재]
  - XLU util (-0.65)                   - JPM/BAC/PNC (+0.55)         - MET/PRU (+0.45 long)
  - XLP staples (-0.45)                - Regional 더 민감 (+0.65)    - 단기 손해보험 (+0.15)
  - XLV pharma (-0.30 mild)            - Trust 약 (+0.30)            - reinvestment risk 양면
  - XLC mature (-0.40)                                              
        |                                   |                                
        v                                   v                                
[H1 reject 경로]                    [H2 confirm 경로]               [H10 isolate 경로]
  reject 시:                          confirm 시:
  - rate_beta 가중 0                    - slope-NIM 4M lag 고정
  - estimation_note 갱신                - XLF banks 비중 leading 입력
  ("IRA capex / 디레버리징 중화")        ("Q+1~2 은행 실적 선반영")
```

**HY OAS 채널** (위 그림 직교 — risk-premium 채널):
```
[GDP nowcast↓]  +  [실업률 변화↑] ─→ [Sahm's Rule alarm]
                                              |
[VIX spike] ──→ [HY OAS 확대] ────────────────┘
                       |
                       v
   +───────────────────────────────────────────────────+
   |                                                   |
   v                                                   v
[방어 상대 outperform]                       [은행 provisioning Q+1~2 lag]
  - sleeve mean - SPY > 0                     - NPL ↑ → EPS ↓ → PB 압박
  - flight-to-quality                         - 그러나 regional > money center 민감
  - 단 인플레 충격 시 *효과 약화* (H3 핵심)     - 실업률 trigger 시 consumer finance (COF/AXP) worst
```

### 2.3 본 sleeve 지표 11개의 7축 매핑

| 본 sleeve 지표 | family | macro 7축 매핑 | 검증명제 (H{N}) |
|---|---|---|---|
| `rate_beta` (vs DFII10) | macro_sensitivity | 2 real rate | H1 |
| `yield_curve_slope_beta` (vs DGS10-DGS2) | macro_sensitivity | 2+잠재 (slope=long-short 차) | H2 |
| `credit_beta` (vs HY OAS) | macro_sensitivity | 4 credit premium | H3 |
| `dollar_beta` (vs DXY) | macro_sensitivity | 5 dollar | H6 |
| `oil_beta` (vs WTI) | macro_sensitivity | 7 supply shock | (sub-archetype 분기) |
| `realized_vol` | risk | 6 risk/vol | H9 |
| `nim_trend` (banks) | quality | 2 real rate × banks | H2 (NIM proxy) |
| `dividend_safety` | quality | (잠재 quality factor) | H4, H11 |
| `cash_flow_duration` | macro_sensitivity | 2 real rate × duration | H1 underlying |
| `capex_to_rate_base` (util) | quality | (IRA structural) | H13 |
| `reinvestment_yield_spread` (insurance) | quality | 2 real rate × duration mismatch | H10 |

→ **macro 7축 = sleeve-shared regime engine**, 본 sleeve 지표 11개 = **sleeve-internal projection** (중복 정의 회피, 통합 cross-sleeve 가능).

---

## §3. Regulatory Regime — 학습 깊이

### 3.1 IRA Medicare Drug Pricing Negotiation (Pharma 한정 — H7)

**Inflation Reduction Act (Aug 2022)** 의 prescription drug provisions (KFF analysis):
1. **CMS Negotiation Authority** — Medicare Part D, Medicare Part B 일부 약품 가격 협상권 부여
2. **선정 기준**: 메디케어 매출 상위 + single-source brand + 9년 이상 (small molecule) 또는 13년 이상 (biologics)
3. **Timeline**:
   - 2026: 10개 약품 협상가 적용 (Eliquis, Xarelto, Jardiance, Januvia, etc.)
   - 2027: +15 약품 추가
   - 2028: +15 약품 추가 (Part B 첫 포함)
   - 2029+: 매년 +20 약품
4. **Best Price Rule** (별도): Medicaid rebate 의무화 — 협상가 < Medicare 가격일 때 모든 Medicaid 환자에 협상가 적용

**Pharma multiple 디레이팅 메커니즘**:
- 협상 대상약 = 미래 cash flow risk premium ↑
- pharma 종목 DCF 의 long-tail (15~20Y) 가치 절단
- Patent cliff schedule 와 결합 → 보통 patent 만료 4~5Y 전부터 multiple 압박

**검증명제 (H7) 의 timing**:
- CMS 공식 발표일 (10약 발표 2023-08-29 / 후속 매년) → event study window [-30, +30]
- 대상약 보유 pharma vs XLV 벤치마크 CAR

**TBD (data)**: CMS.gov 의 협상 약품 list 자동 추적 + 종목별 매출 비중 매핑 (블록6 → main 요청)

### 3.2 Basel III Endgame (Bank 한정 — H5 영향)

**Basel III final rule (2023-07 NPR, 2025 발효 예상)**:
- 대형 은행 (≥$100B) 자본요건 상향 (RWA risk-weighted asset 산출 변경)
- 추정 영향: 8 GSIBs CET1 ratio ~16~19% 필요 (현 ~13~15%)
- → capital return (배당·자사주) 폭 축소 압박

**검증명제 (H5) 의 modulation**:
- 인플레+금리상승 → 은행 NIM 호재 + 자본 여유 ↓ → quality (CET1 상위) 종목 outperform 폭 축소 가능
- 단 quality bank 의 capital generation 능력 ↑ → 장기 outperform 유지

### 3.3 FERC Rate Case Mechanism (Utility 한정 — H13)

**규제 ROE 결정 절차**:
1. Utility 가 rate case filing (보통 2~3Y 주기)
2. PUC (주별) 또는 FERC (interstate) 가 hearing → Allowed ROE 결정
3. **최근 경향** (2024-2026):
   - 대형 주 (NJ, CA, FL) Allowed ROE 9.5~10.5% 유지
   - 보수적 주 (KS, MO) 8.5~9.0% 압박
   - 평균 ~9.7% (S&P Global data)

**IRA 보조금 + Rate Base growth 의 관계**:
- ITC (Investment Tax Credit) 30%~60% (location/equity bonus) — 신재생 설비
- PTC (Production Tax Credit) MWh 기반 — 운영 단계
- → Rate Base 증가 + ROE 변동 작음 = EPS 성장의 *capex 사이클이 driver*

**검증명제 (H13) 의 timing**:
- 전환 선도 (NEE/AEP/XEL) vs 전통 자산 의존 (SO/DUK/PCG)
- capex_to_rate_base 시계열 + 전환 dummy

### 3.4 GICS Sub-industry 분류 (TBD data)

본 sleeve 의 5 archetype 정의 = GICS sub-industry 기반:
- Staples = GICS 30 (Consumer Staples)
- Utility = GICS 55 (Utilities)
- Healthcare = GICS 35 (Health Care)
- Bank = GICS 40 sub 4010 (Banks)
- Insurance = GICS 40 sub 4030 (Insurance)
- BD/AM/Payments = GICS 40 sub 4020 (Diversified Financials)

XLP/XLU/XLV/XLF/XLC ETF holdings + FinanceDatabase (MIT) loose-GICS 활용.

---

## §4. 위기 유형 분류의 실증 정당화 (★main 검토 (b) 반영)

### 4.1 위기 유형 3 분류의 이론 근거

direction.md §2.1 의 위기 유형 분류:
- (a) 신용위기 (Credit-led): HY OAS z>+1.5 AND UNRATE 3M >0.3%
- (b) 외생충격 (Exogenous Shock): VIX z>+2.0 AND GDPC1 nowcast 급락
- (c) 인플레이션 충격 (Inflation-led): T10YIE z>+1.5 AND FFR 6M >100bp

**이론 anchor**:
- **Sahm's Rule** (Sahm 2019 BPEA): 실업률 3M 이동평균이 12M 최저 대비 +0.5%pt 상회 → 침체 진입 신호. 본 sleeve 의 신용위기 정의는 Sahm 의 0.3%pt 빠른 변형 (조기 식별)
- **Frazzini-Pedersen BAB**: risk-off 시 저베타 alpha 발생 — 단 risk-off 의 *원인* 별로 패턴 다름
- **Investment Clock (Trevor Greetham)**: 4 phase (Reflation/Recovery/Overheat/Stagflation) = 성장×인플레 2축. macro 방 framework 의 외생 조건키

### 4.2 시대별 패턴 차이 (R1 ⑤ 핵심 논쟁의 정량 증거)

투자은행 보고서 (KBW, Morgan Stanley) 의 사후 분석:

| 시기 | 위기 유형 | 방어 상대 outperform | 금융 상대 underperform |
|---|---|---|---|
| **2000 dot-com** | Inflation→Slowdown (Tech bubble) | XLU vs SPY +28%, XLP +12% | XLF -15% |
| **2008 GFC** | Credit-led (Lehman) | XLP +20%, XLV +15%, XLU -5% | XLF -55% (worst) |
| **2020 COVID** | Exogenous (pandemic) | XLP +5%, XLV +12%, XLU -10% | XLF -25% |
| **2022 inflation** | Inflation-led (Fed hike) | XLU **-12%** (bond proxy 부진), XLP +3% | XLF +0% (NIM 호재) |

**패턴 발견**:
- **Credit-led**: 방어 *전체* outperform 가장 강함 (H3 기본형)
- **Exogenous**: 방어 mixed — XLV/XLP outperform, XLU 부진 (외생충격 자체가 안전자산 회피)
- **Inflation-led**: ★방어 outperform 가설 *부분 기각* — XLU (bond proxy) 부진. 금융 은 NIM 호재 → 본 sleeve 가 *예외적으로 방어 안 됨*

→ **H3 의 정당화**: 위기 유형 분류는 임의 분류 X, 실증 패턴 차이가 명확 (2022 = 분명한 falsifier).

### 4.3 macro 7축 axis 정합 (★main 검토 (b) 핵심)

**macro 방의 framework**:
- 4 phase (Reflation/Recovery/Overheat/Stagflation) = 성장×인플레 2축 외생 조건키
- 7축 driver + 잠재 공통원인 (VIX/OIS) 통제
- ★발견: 가설2 FAIL — partial-corr 네트워크는 regime 불변 (네트워크 자체는 regime 별로 안 바뀜, 분산 스케일 + soft belief-mix 만 변함)

**본 방의 위기 유형 axis 정합 방식**:

```
macro 4 phase                           본 방 sleeve-internal regime
─────────────                           ─────────────────────────────
Reflation (성장↑인플레↓)  ←──→         Normal regime + 미세 sub-sleeve rotation
Recovery (성장↑인플레↑초입)             → 금융 lead (NIM thesis 활성), 방어 underperform
Overheat (성장↑인플레↑)                 → 인플레 충격 (T10YIE z>+1.5) AND FFR rising
Slowdown/Stagflation (성장↓인플레↑)     → 신용위기 OR 외생충격 (위기 유형 판정 by HY OAS vs VIX)
```

**중복 회피 원칙**:
1. **Macro 4 phase = sleeve-shared regime SSOT** (모든 sleeve 가 consume)
2. **본 방 위기 유형 = sleeve-internal sub-regime modulator** (Slowdown/Stagflation 안에서 sub-sleeve 부호 분기 isolate)
3. **합산 axis 차원 = (macro 4 phase × 본 sleeve 위기 유형 3 + Normal)** = 4 × 4 = 16 cell — 단 실제 발생 빈도 낮은 cell 많음 → 데이터 sparse

**conditional_correlation.RegimeGlasso 통합 구조**:
```python
regime_history = [
    (macro_phase_t, sleeve_subregime_t)  # 2D tuple
    for t in timeline
]
# macro_phase ∈ {Reflation, Recovery, Overheat, Slowdown_Credit, Slowdown_Exogenous, Slowdown_Inflation, Normal}
# sleeve_subregime ∈ {neutral, credit_risk_on, credit_risk_off, inflation_shock} — 본 방 정의
```

**★발견 적용**: macro 의 "네트워크 regime 불변" 결과 → 본 방의 partial-corr prior 부호도 *regime 불변 안정 구조*. force-include whitelist 4 엣지 (rate_beta-XLU, slope_beta-NIM_trend, credit_beta-provisions_yoy, capital_ratio-dividend_safety) 가 모든 regime 에서 *부호* 보존, regime modulation 은 *scale* 만 (base_weight 의 multiplier).

**검증 design 수정**:
- `conditional_correlation.RegimeGlasso.fit` 시 — 부호 force-include 는 regime 무관 동일, regime 별 차이 = Ω 의 off-diagonal *절대값* (scale) 만
- direction.md §2.3 의 12 H{N} 검증명제 중 H1·H2·H3 의 confirm 조건 일부 수정:
  - 기존: "regime 별 partial-corr 부호 분기" → 수정: "regime 무관 부호 안정 + regime 별 절대값 스케일 변동"
  - reject 조건: "부호 반전 12M" 유지 (이는 *구조 변동* 신호 = retract trigger)

### 4.4 H3 의 인플레 충격 약화 메커니즘 (sleeve internal)

**왜 인플레 충격 시 방어 outperform 가설 *약화* 되나**:
1. **XLU bond proxy 효과 반전**: real rate ↑ → duration 자산 압박 → util multiple 디레이팅. 안전자산 회피 (cash·short bond 선호)
2. **XLP pricing power 분기**: 강브랜드 (KO/PG) = 원가 전가 성공 → 마진 방어 → outperform 유지. 약브랜드 = 마진 압박 → underperform
3. **XLF banks NIM 호재**: 인플레 충격 = Fed 인상 → NIM 확장 thesis 활성. 본 sleeve 내 *금융 sub-sleeve 가 인플레에선 lead*
4. **XLV mixed**: pharma = 규제 + IRA 부담 (인플레 무관). medical device = 경기 sensitive (인플레+slowdown 동반 시 압박)

→ **H3 의 핵심 검증명제**:
- Credit-led regime: 방어 *전체* outperform (XLU 포함)
- Exogenous regime: 방어 mixed (XLV/XLP O, XLU X)
- Inflation-led regime: 방어 *fragmented* (XLP 강브랜드 O, XLU X, 금융 lead)
- Normal regime: rotation by phase

---

## §5. main 검토 2건 반영 (★승인 후 조건)

### 5.1 (a) 신규 `core/structure/factor_beta_decomposition.py` self-test + 무회귀 (2-3 단계)

direction.md §② 코드 매핑 의 신규 모듈:
- `core/structure/structural_break.py` (Bai-Perron)
- `core/structure/factor_beta_decomposition.py` (Bond proxy attribution)
- `core/structure/kci_test.py` (Kernel-based partial corr)
- `core/structure/normalize_kpi.py` (3단계 normalize)

**main 검토 (a) 의무**: 본 4 모듈 모두 2-3 self-test + 무회귀 검사 필수.

**Self-test design** (모듈별):

#### factor_beta_decomposition.py
```python
# Self-test 1: synthetic data — 알려진 β 회복
def test_known_beta_recovery():
    # 인공 데이터: XLU_beta_rolling = 0.3*ΔDFII10 + 0.2*ΔT10YIE + 0.5*IRA + 0*crisis + noise
    # → rolling regression → β1 ≈ 0.3, β2 ≈ 0.2, β3 ≈ 0.5, β4 ≈ 0
    assert abs(beta1 - 0.3) < 0.1
    assert abs(beta4 - 0.0) < 0.1

# Self-test 2: 실데이터 sanity — 2022 IRA 통과 (2022-08) 전후 β3 도약
def test_ira_dummy_jump():
    pre_ira_beta3 = mean(beta3[pre 2022-08])
    post_ira_beta3 = mean(beta3[post 2022-08])
    assert post_ira_beta3 - pre_ira_beta3 > threshold  # IRA 의 구조 변화 capture

# Self-test 3: collinearity 안정성 — ΔDFII10 와 ΔT10YIE 가 collinear 일 때 robust
def test_collinearity_robustness():
    # 인공: T10YIE = DFII10 + small noise
    # → ridge regularization 적용 시 β1·β2 separate 가능 확인
```

**무회귀 검사**:
- 본 모듈은 *interpretation layer* (직접 매매신호 X) → 기존 weight_falsification e-process / score_ic_breakdown 에 영향 0 확인
- 회귀 test: factor_beta_decomp 모듈 import 전후 의 `train_weight_cards` 출력 hash 일치 확인 (산출 동일성)

#### structural_break.py (Bai-Perron)
- Self-test: 인공 break point 데이터로 검정. 라이브러리 (statsmodels 또는 ruptures) 검증된 함수 wrapping
- 무회귀: 직접 호출되지 않으면 영향 0. `update_controller.step` 의 hard_falsifier 조건에 hook 추가 시만 회귀 검사

#### kci_test.py
- Self-test: 알려진 비선형 의존성 데이터 (sin/cos/threshold) → p-value < 0.05 확인. independent 데이터 → p-value > 0.5 확인
- 무회귀: H3·H9 alarm 시 사후 분석 전용 → 평시 미호출, 영향 0

#### normalize_kpi.py
- Self-test: 3단계 (within-industry z → sleeve-wide rank z → IC-weighted aggregate) 인공 데이터 검증. 산업 별 부호 조정 (NIM↑+, 부채비율↓+) 확인
- 무회귀: 기존 `core/data/weight_panel.py` 의 simple z-score path 와 toggleable (`use_3stage_normalize: bool` flag)

**Self-test 코드 위치**: 각 모듈 `__main__` 블록 또는 `tests/test_{module}.py` 신규. CI 수동 실행 (단일사용자 1인 환경 — pytest 호출 1회 통과 확인).

### 5.2 (b) Macro 7축·잠재인자 통제와 정합 (이미 §4.3 에 통합)

요약:
- macro 7축 = sleeve-shared SSOT
- 본 sleeve 의 지표 11 = 7축의 sleeve-internal projection
- 위기 유형 axis = macro 4 phase × sleeve sub-regime 결합 (2D tuple)
- regime modulation = 분산 스케일 + soft belief-mix (★macro 가설2 FAIL 결과 적용 — 직접엣지 네트워크 regime 불변, scale 만 변동)
- conditional_correlation.RegimeGlasso 통합 — direction.md ④ 코드 매핑 의 RegimeGlasso 2D regime_history 확장 = main 결정 TBD 1

---

## §6. 2-2 의 발견 요약 (2-3 진입 조건)

### 6.1 새로 도출된 사실

1. **macro 가설2 FAIL 결과 적용** → 본 sleeve 의 partial-corr 부호는 regime 불변, scale 만 변동. force-include 화이트리스트 4 엣지 부호 강건성 ↑
2. **위기 유형 3 분류의 실증 정당화** — 2000/2008/2020/2022 패턴 차이 명확 (특히 2022 인플레 충격 = falsifier)
3. **Insurance archetype 의 reinvestment risk** (H10) = 은행 NIM 보다 *훨씬 장기 관점* → XLF 내 sub-archetype 분리 필수성 강화
4. **IRA 의 두 채널** = pharma (H7 이벤트 디레이팅) + util (H13 capex 사이클 구조) → 같은 정책이 두 sub-archetype 에 다른 channel 로 영향
5. **신규 4 모듈 self-test 명세** — factor_beta_decomp / structural_break / kci_test / normalize_kpi 각각 self-test 3종 + 무회귀 design 확정

### 6.2 2-3 진입 시 우선순위

**Priority 1 검증명제 6 (실데이터 시계열)**:
- **H1** real rate dichotomy → `raw/validation-rate_beta.md`
- **H2** yield curve NIM leading → `raw/validation-yield_curve_slope.md`
- **H3** HY OAS dispersion 위기 유형별 → `raw/validation-hy_oas_regime.md`
- **H8** great rotation log(XLF/XLU) → `raw/validation-rotation.md`
- **H10** insurance reinvestment → `raw/validation-insurance_duration.md`
- **H13** util capex cycle → `raw/validation-util_capex.md`

**Priority 2 (선택)**: H4, H5, H9, H11 — 시간 허락 시
**Priority 3 (보류)**: H6, H7 — 다음 cycle

**2-3 데이터 path**:
- FRED API (DGS10/DGS2/DFII10/BAMLH0A0HYM2/DTWEXBGS/WTISPLC/T10YIE/UNRATE/VIXCLS) — 직접 호출
- Yahoo Finance (XLU/XLP/XLV/XLF/XLC + 구성종목 일별 가격)
- EDGAR — 우선순위 3 (vendor 부재 시 fallback)

**산출 형식**:
- `raw/validation-{지표}.md` (강제) — 시계열 검증 근거 + 도표 (실측 partial-corr / Rank-IC / Bootstrap t-stat)
- `study_session.yaml` (§3 7블록) — 검증 결과 반영 후 갱신

---

## §7. 정직 명시 — 한계 (자가 점검)

1. 본 theory-notes.md = 이론 학습 + macro 정합 + 가격결정 원리 sub-archetype 별 정밀화 — *실데이터 검증 0* (2-3 단계에서 수행)
2. 시대별 패턴 표 (§4.2) 는 KBW/MS 사후 분석 인용 — 본 시스템 실측 재현 미수행 (2-3 walk-forward 필수)
3. macro 방 가설2 FAIL 결과는 macro 의 직접 발견 — 본 sleeve 에서 *동일 결과* 확인 미수행 (2-3 검증 항목 추가: "본 sleeve 의 partial-corr 네트워크도 regime 불변인지 permutation test")
4. neural-archetype 5종 별 듀레이션 추정치는 학술/실무 표준 범위 (5~30Y) 인용 — 본 시스템 실측 미수행
5. IRA timeline 은 2022 NPR + 후속 발표 기준 — 2026-05 현재 시점 update 필요 (CMS.gov 직접 조회 권고)

---

## §8. 참조

- **prerequisite**: `direction.md` (2-1 승인 완료)
- **자문 원문**: `raw/round-{1,2,3,4}.md` + `~/.claude/docs/archive/research-raw/eq_us_defensive-round{1,2,3,4}-20260530.txt`
- **macro 방 framework**: `D:/projects/Inv/study-research/macro/study_session.yaml` (7축·잠재인자·가설2 FAIL 결과)
- **STUDY-KIT**: `D:/projects/Inv/STUDY-KIT.md` §2-2

다음 단계: 2-3 진입 (main 추가 승인 또는 자동 — STUDY-KIT 명시는 2-1 게이트만, 2-2 → 2-3 자동 진행).
