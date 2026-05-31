---
tags: [type/theory-notes, domain/commodity, phase/study-system, gate/2-2]
date: 2026-05-30
note: STUDY-KIT §2-2 강제 산출. direction.md 승인된 ①②③ 정독·정리. 가격결정 원리 + 지표 의미·관계도 + 우리 시스템 매핑.
study_id: commodity
sub_sleeves: [energy, industrial_metals, precious_metals, agricultural]
gold_note: gold 는 별도 방 study_id=gold — 본 방 precious 는 silver/platinum 위주 (main 통합 시 조율)
archetype_pooling: 부록B 명시 — ticker 독립 학습 X. 산업 archetype prior + soft membership (composed_weights.delta_arch_by_type)
---

# theory-notes — commodity 이론 학습 정리 (2-2)

> ★ main 승인 (2026-05-30): ①보편학파+Buy-side SOTA+sub-sleeve ②검증방향(claude critique 반영). 검토: archetype pooling(부록B), gold 방 중복 조율, inventory→days_of_supply 명명 유지.
> 본 문서는 direction.md §1·§2 의 학파/방법론을 깊이 정독해 (a) 가격결정 원리 (b) 지표 의미·관계도 (c) 우리 시스템 매핑(이론→코드→가설→flag) 3계층으로 정리한다.

---

## Part A. 보편 학파 (4 sub-sleeve 공통, 가격결정 원리)

### A.1 Theory of Storage — Kaldor (1939) / Working (1949) / Brennan (1958)

**핵심 명제**: 원자재 선물 가격은 **현물가 + 보유비용 − convenience yield** 로 결정. 재고 보유가 갖는 옵션 가치 (생산 중단 회피, 즉시 인도 능력) = convenience yield.

**가격결정 방정식 (cost-of-carry 모형)**:
```
F(t,T) = S(t) · exp((r + u − y)(T − t))

  F(t,T) = 만기 T 의 선물 가격
  S(t)   = 시점 t 의 현물가
  r      = 무위험 실질금리 (DFII10 proxy)
  u      = 단위 시간당 저장비용 (storage cost, 창고료 + 보험 + 손실)
  y      = convenience yield (현물 보유의 비명시적 효용. 재고 타이트할수록 ↑)
  T − t  = 만기까지 시간
```

**유도 원리** (no-arbitrage):
- spot 매수 + 만기까지 보유 + 만기에 인도 = forward 매수 와 동일한 cash flow
- 보유비용 (r·S + u·S) 만큼 forward 가 비싸야 하나, 보유의 옵션 가치(y·S) 만큼 차감
- → F = S + (r + u − y)·S·Δt (선형 근사) 또는 exp form

**Backwardation vs Contango 정의**:
- **Backwardation** (F<S, 곡선 우하향): y > r+u → 재고 타이트, 현물 프리미엄, 보유 매력 (carry+)
- **Contango** (F>S, 곡선 우상향): r+u > y → 재고 잉여, 저장비용 우세, 보유 손실 (carry−)

**convenience yield 의 경제적 의미**:
- 산업 사용자 (정유사·제분사) 가 재고를 보유하는 가치: 갑작스런 수요 대응 능력, 생산 중단 회피, 옵션성 보유
- 재고 ↓ → 잠재 부족 위험 ↑ → y ↑ → backwardation 심화
- 재고 ↑ → 옵션 가치 약화 → y ↓ → contango 진입

**Basis 정의**:
```
Basis = F − S       (forward premium, 양수 = contango)
또는
log(F1) − log(F2)   (term structure slope, BGR 정의)
```

**우리 시스템 매핑**:
- `commodity_assumptions.carry_forward_slope` → carry slope·sign_flip 검증
- `commodity_assumptions.carry_convenience_zscore` → y 의 rolling z (현재 carry 스트레치)
- 가설 H2 (theory_of_storage_backwardation) 핵심 메커니즘
- 신규 indicator: `roll_yield`, `term_structure_slope`, `convenience_yield_z`

---

### A.2 Hicks-Keynes Normal Backwardation (Hicks 1939 / Keynes 1930)

**핵심 명제**: 생산자 (헤저) 가 선도 시장에서 매도 헤지를 하므로, 투기자 (long side) 가 risk premium 을 요구 → 평균적으로 F < E[S(T)] → **정상 backwardation**.

**모형**:
- 헤저 (producer): 가격 변동 위험 회피 → short forward
- 투기자 (long): risk premium 요구 → F(t,T) < E[S(T)]
- expected return = E[S(T)] / F(t,T) − 1 > 0 (long holder 가 음의 risk premium = 양의 수익)

**우리 시스템에서**:
- 단순히 모든 commodity 가 long-only 우수해야 한다는 게 아니라, **헤지 압력이 강한 시기에만** premium 작동
- Hong-Yogo (2012) — open interest 가 macro 예측력 갖는 이유 (헤저 활동 proxy)
- 가설 H8 (cot_momentum_amplification — MM net long 측정) 의 이론적 근거

**비판/한계**:
- Bessembinder (1992) — 평균 backwardation 은 실증상 일관되지 않음. period 의존.
- Erb-Harvey (2006) — long-only commodity 전략의 spot return 은 평균 0 근사. 수익은 collateral + roll 에서.

---

### A.3 Erb-Harvey (2006, FAJ) Spot/Roll/Collateral 3-분해

**핵심 명제**: long-only commodity index 의 총 수익은 3 성분으로 분해:
```
Total Return = Spot Return + Roll Return + Collateral Yield

  Spot     = 현물가 변동 (장기 평균 ≈ 0, 인플레 헤지)
  Roll     = 만기 도래 시 새 contract 로 roll 하면서 발생 (backwardation = +, contango = −)
  Collateral = futures 의 notional 을 cash 로 보유하면서 받는 이자 (≈ T-bill yield)
```

**Roll Return 핵심**:
- backwardation → 만기 가까운 contract 가 비쌈 → 매도 (만기 가까운) + 매수 (만기 먼) = 가격 상승 (carry+)
- contango → 만기 가까운 contract 가 쌈 → 매도 + 매수 (비싼) = 가격 하락 (carry−)
- 장기 buy-and-hold 의 핵심 driver

**우리 시스템 시사점**:
- 가설 H3 (roll_cost_drag_collapse) — contango regime 의 누적 roll loss
- BCOM/GSCI index 의 historical underperformance 이유 (2010s contango 대부분)
- **3 성분 분해를 indicator family 로 사용**: spot return 은 momentum, roll yield 는 valuation, collateral 은 macro_driver

---

### A.4 Gorton-Hayashi-Rouwenhorst (2013, Rev Finance) — Inventory as State Variable ★R3 누락 보강

**핵심 명제**: KWB (storage theory) + HK (backwardation) 가 경쟁 가설이 아니라 **inventory 를 통해 통합**된다. **Normalized inventory** 가 basis 와 prior return 을 동시에 설명.

**증거**:
- 재고 데이터 (~31 commodities, 1969-2010) 분석
- inventory 낮음 → backwardation + 양의 expected return
- inventory 높음 → contango + 음의 expected return
- normalized inventory 가 basis 회귀에서 1차 변수, prior return 회귀에서 1차 변수 (R² > 0.30 둘 다)

**Normalized inventory** 정의:
```
norm_inv = (현재 inventory − Hodrick-Prescott trend) / HP trend
또는
norm_inv = days_of_supply z-score
```

**우리 시스템에서 결정적 통찰** (★중요):
- 가설 H2 (theory_of_storage_backwardation), H3 (roll_cost_drag), BGR basis_momentum 이 **redundant 가능성** — 셋 다 같은 scarcity state variable (inventory) 의 다른 proxy
- 가설 H10 (ghr_inventory_state_variable) — 우리 시스템 검정: normalized_inventory 가 basis 와 prior return 의 공동 설명력 갖는지 검증
- **단일 inventory state variable 가설이 성립하면** weight_rules 에서 days_of_supply 의 base_weight ↑, 나머지 carry indicator 들은 redundancy 로 감액

**구현 의의**:
- 새 함수: `core/structure/commodity_assumptions.normalized_inventory_state(inv, basis, fwd_return)` — 공동 R² 산출
- delta_arch_by_type 의 archetype 분리 시 inventory-state 가 primary scope 일 가능성

---

### A.5 Deaton-Laroque (1992, REStud) — Competitive Storage Model ★R3 누락 보강

**핵심 명제**: 저장 가능 commodity 의 가격 분포는 **고유한 비대칭성 (positive skewness)** 을 갖는다. 재고 = 0 lower bound → 공급 부족 시 가격 spike, 공급 과잉 시 재고 누적으로 가격 하락 완만.

**모형 구조**:
- 경쟁적 저장업자 + 합리적 기대
- 상태 변수 = 재고 level (≥ 0)
- 재고 0 → 가격 = 즉시 수급 균형 (스파이크 가능)
- 재고 > 0 → arbitrage 조건 (F = (1+r)·S − u + y) 이 가격을 제약

**예측**:
- positive skewness — 가격 분포의 오른쪽 꼬리가 두꺼움
- 분산의 nonlinearity — 재고 낮을 때 분산 증가 (heteroskedasticity)
- 자기상관 패턴 — 평균회귀 (재고 누적 시) + 폭발 (재고 고갈 시)

**우리 시스템 시사점**:
- 가설 H9 (storage_limit_nonlinearity) — 2020-04 negative WTI 의 이론적 base
- 가격 분포 검정에 **skewness 통계** 추가 (FIGARCH 입력의 정상화 가정 위반 점검)
- nonlinear 가격-재고 관계 → threshold_regression (Hansen, 보유 코드) 적용 정당화

---

## Part B. Buy-side Quant SOTA (필수)

### B.1 Tang-Xiong (2012, RFS) — "Index Investment and the Financialization of Commodities"

**핵심 명제**: 2004년 이후 commodity index fund (GSCI, BCOM 추종 passive long-only) 의 급증으로 commodity sub-sector 간·commodity-equity 간 교차상관이 **구조적·비정상적**으로 상승. "common ownership" → comovement.

**증거**:
- index 포함 commodity 의 페어 상관 (e.g. crude oil ↔ wheat) 이 1998-2004 대비 2004-2010 에 0.1 → 0.5 급등
- 비포함 commodity (e.g. propane) 는 변화 없음 — cross-section identification
- equity↔commodity 상관도 0.1 → 0.4 상승

**측정 방법** (Tang-Xiong 원본):
- CFTC IID (Index Investment Data, 2007-2015 quarterly) — index trader 의 commodity 별 포지션
- "index membership" dummy × time interaction → diff-in-diff
- **핵심**: 측정 대상이 index trader 의 passive long-only, MM (active speculator) 아님

**★construct 분리 (claude R3)**:
- Tang-Xiong financialization = passive long-only index 자금 → common ownership comovement
- MM (Money Manager) = active CTA/hedge fund → momentum/positioning pressure (Hicks-Keynes)
- 두 가설이 다른 메커니즘 검증

**우리 시스템 매핑** (★H5 ≠ H8 분리):
- H5 driver: pre-2015 IID + post-2015 Barclays/Bloomberg index AUM 분기 + Supplemental CIT 12 농산물
- H5 outcome: 60일 rolling cross-correlation 평균 (Yahoo 가격만으로 즉시 측정)
- H8 driver: MM net long / total OI z-score (CFTC DCOT)
- 단절 2015: IID 중단 → post-2015 reduced-form (cross-corr outcome) 또는 외부 데이터 (Barclays)

**Singleton (2014, Mgmt Sci) 보강**:
- investor flows 2008 oil boom/bust 직접 설명
- Tang-Xiong 보완 — flow-driven price impact mechanism

---

### B.2 Bakshi-Gao-Rossi (2019, Management Science) — "A Better Measure of Commodity Risk Premia"

**핵심 명제**: **basis-momentum** (basis 의 시계열 변화) 가 단순 carry 또는 momentum 단독보다 commodity risk premium 을 더 잘 예측.

**시그널 정의** (R2 확정):
```
Basis_t        = ln(F1_t) − ln(F2_t)              # term structure slope
RelBasis_t     = Basis_t − (1/12)·Σ_{i=1..12} Basis_{t−i}  # 12개월 이동평균 대비
BasisMom_t     = sign(Basis_t) × sign(RelBasis_t) ∈ {−1, 0, +1}
```

**해석**:
- BasisMom = +1: 현재 backwardation (Basis<0 → carry+) **그리고** 과거 12m 평균보다 더 강한 backwardation → strong long
- BasisMom = −1: 현재 contango (Basis>0) **그리고** 과거 평균보다 더 강한 contango → strong short
- BasisMom = 0: 상충 (carry sign 과 momentum sign 다름) → 중립

**구현 디테일** (Python 단편 R2 gemini):
```python
def calc_bgr_basis_momentum(f1_prices, f2_prices, window=12):
    basis = np.log(f1_prices) - np.log(f2_prices)
    rolling_mean_basis = basis.rolling(window=window, min_periods=window).mean()
    relative_basis = basis - rolling_mean_basis
    return (np.sign(basis) * np.sign(relative_basis)).rename('bgr_basis_momentum_12m')
```

**우리 시스템 매핑**:
- 신규 indicator id: `bgr_basis_momentum_12m` (family=valuation, is_core=true)
- 가설 H3 (roll_cost_drag_collapse) 의 핵심 시그널
- CME EOD 무료 데이터 (F1, F2) — 신규 collector 필요

**H10 와의 관계**: GHR 명제 = inventory 가 basis+prior return 동시 설명 → basis_momentum 도 inventory 의 proxy 일 가능성. 공동 회귀로 R² 분리 검증.

---

### B.3 Asness-Moskowitz-Pedersen (2013, JF) — "Value and Momentum Everywhere"

**핵심 명제**: Value (carry) 와 Momentum (12-1 가격 모멘텀) 이 **모든 자산군에서 보편적**으로 작동. commodity 도 예외 아님.

**commodity 특정**:
- Value = roll yield (carry)
- Momentum = 12-1 month total return (직전 1개월 제외, look-ahead 차단)
- 둘은 **음의 상관** (carry+ 종목과 momentum+ 종목은 겹치지 않는 경향) → diversification benefit
- carry+momentum 결합 portfolio 의 Sharpe 가 둘 단독보다 ~50% 높음

**구현**:
- ranking 기반 long-short portfolio (top 1/3 long, bottom 1/3 short)
- 매월 rebalance
- transaction cost 후에도 alpha > 0

**우리 시스템 매핑**:
- 신규 indicator: `momentum_12_1` (family=momentum, is_core=true)
- weight_rules 에서 carry (roll_yield) + momentum (12_1) 결합
- Fama-MacBeth cross-section 회귀로 IC 산출

**Koijen-Moskowitz-Pedersen-Vrugt (2018, JFE) "Carry" 확장**:
- carry 의 cross-asset 정의 (equity, bond, FX, commodity)
- commodity carry = roll yield 가 가장 직접적
- Q3 cross-sleeve portfolio 에서 BL view 로 사용 가능

---

### B.4 Kilian (2009, AER) — SVAR Oil Shock Decomposition ★R3 누락 보강

**핵심 명제**: oil price 변동을 단일 source 로 보지 말고 **3 shock 으로 SVAR 분해**. macro 영향은 source 의존.

**SVAR 모형** (3-variable):
```
변수: [oil supply (글로벌 생산), real economic activity (Kilian index = BDI proxy), oil price]
shock 분해 (sign restriction + recursive identification):
  ε^supply        = supply shock (e.g. OPEC 감산, 셰일 증산)
  ε^aggregate_demand = global real activity demand (e.g. China growth)
  ε^precautionary    = oil-specific demand (e.g. inventory build for fear of war)
```

**macro 효과의 source 의존성** (★결정적):
- **Supply-driven oil↑**: 부정적 supply shock (감산) → 비용 충격 → equity 마진 압박 (equity−)
- **Demand-driven oil↑**: 글로벌 활동 활성 → pro-cyclical (equity+)
- **Precautionary oil↑**: fear premium → 일시적, recession lead

**Hamilton (1996/2003) NOI 와의 관계**:
- Hamilton: NOI > threshold 면 recession 예측 (단일 nonlinear threshold)
- Kilian: NOI 가 어떤 shock 으로 발생했는지에 따라 효과 다름 → Hamilton 의 sharpen

**구현**:
- statsmodels VAR + structural identification 또는 별도 `bvars` 패키지
- 변수: WTI (FRED DCOILWTICO) + 글로벌 생산 (EIA STEO) + Kilian index (BDI Yahoo BDIY=F 또는 OECD real activity)

**우리 시스템 매핑**:
- 가설 H7-K (oil_macro_kilian_decomposition) — 단순 NOI threshold → source-conditional
- Q3(b) energy↔equity cross-sleeve covariance prior — **단일 정적 prior 금지**, supply vs demand source 조건부
- 신규 모듈: `core/structure/kilian_oil_svar.py`

---

### B.5 Szymanowska et al. (2014, JF) — "An Anatomy of Commodity Futures Risk Premia"

**핵심 명제**: 곡선 구조 (term structure) 가 단순 roll yield 를 넘어선 cross-sectional risk premium 정보 보유. **spot premia** vs **term premia** 분리.

**분해**:
- spot premium = 만기 가까운 contract 의 expected excess return
- term premium = 만기 먼 contract 의 expected excess return − spot premium
- 둘은 다른 cross-sectional driver 의해 결정

**시사점**:
- BGR basis_momentum 의 보완 — F1/F2 만 보지 말고 F1/F2/F3 또는 F1/F6 도 (다른 만기 spread)
- backwardation 의 깊이 (F1-F2) vs 모양 (F1-F6 또는 F1-F12) 분리 검증

**우리 시스템 매핑**:
- CME term structure collector 에서 F1/F2/F3 또는 F1/F6 까지 수집 (Phase 2)
- 가설 H3 의 보조 indicator: `term_structure_curvature` (F1-F2 vs F2-F6 비교)

---

### B.6 Hamilton (1996 JME, 2003 JoE) — NOI (Net Oil Price Increase) Nonlinear

**핵심 명제**: oil price 변동의 macro 효과는 **비대칭**. **NOI (1년 최고치 경신폭)** > 임계 일 때만 recession 예측. 가격 하락은 비례적 호황 효과 없음.

**NOI 정의**:
```
NOI_t = max(0, p_t − max(p_{t-12}, p_{t-13}, ..., p_{t-1}))
      = 직전 12개월 최고치를 초과한 부분만 (0 floor)
```

**Hamilton 발견**:
- 일반 변동률 (% change) 사용 시 — oil ↔ recession 비유의 (β 작음)
- NOI 사용 시 — oil ↔ recession 강한 nonlinear (Granger causality 회복)

**우리 시스템 매핑**:
- 가설 H7-raw (oil_macro_NOI_threshold) — Phase 1.5 (FRED WTI + CFNAI 즉시)
- 신규 indicator: `wti_noi_1yr` (transform=level, family=macro_sensitivity)
- 가설 H7-K (Kilian SVAR) 와 분리 — raw NOI 는 baseline, Kilian 은 source-conditional sharpen

---

### B.7 추가 학파 (보강, 빠른 정리)

| 학파 | 핵심 발견 | 우리 시스템 시사 |
|---|---|---|
| **Fama-French (1987, JB)** | theory of storage 실증 — basis 가 expected return 예측 | H2 정식 reference. carry indicator 의 정당화 |
| **Acharya-Lochstoer-Ramadorai (2013, JFE)** | producer hedging demand + financial constraints | H8 보강 — speculator pressure 는 producer hedging 상대편 |
| **Singleton (2014, Mgmt Sci)** | investor flows & 2008 oil boom/bust | Tang-Xiong 보완 — flow-driven price impact |
| **Hong-Yogo (2012, JFE)** | open interest 의 macro 예측력 | H8 보강 — OI 변화가 헤징 활동 proxy |
| **Bessembinder (1992, RFS)** | risk premia 의 period 의존성 | Normal backwardation 의 한계 |
| **Yang (2013, JFE) "Investment Shocks"** | commodity carry 와 macro investment shock 결합 | cross-asset carry literature |

---

## Part C. Sub-sleeve 특화 학파

### C.1 Energy (crude oil, natural gas, gasoline)

**가격 결정 driver**:
1. **공급 충격** (OPEC+ 정책, shale 생산, geopolitical) — discrete jump risk
2. **수요 사이클** (글로벌 PMI, 중국 활동, 계절성)
3. **재고 cushion** (EIA crude stocks, Cushing 가동률)
4. **거시 driver** (USD, real rate, credit spread)

**핵심 학파**:
- **Kilian (2009)** — SVAR 분해 (이미 B.4)
- **Hamilton (2003)** — NOI 비선형 (이미 B.6)
- **Baumeister-Kilian (2016, JEEA)** — VAR shocks 와 oil-macro 동학 정밀화
- **EIA STEO** — Short-Term Energy Outlook, 매월 발표, shale break-even economics

**Refinery crack spread** (정유 마진):
- gasoline crack = RBOB gasoline − WTI crude
- heating oil crack = ULSD − WTI crude
- 정유사 마진 → 정유 가동률 → crude demand 영향
- 3-2-1 spread = 3×crack(gasoline) + 2×crack(heating)/3 (정유 산업 표준)

**shale break-even**:
- Permian basin break-even ≈ $35-45/bbl (2020s)
- Bakken ≈ $50-60/bbl
- Eagle Ford ≈ $40-50/bbl
- WTI < break-even → shale 생산 감소 (lagged 3-6m)
- WTI > break-even → drilling 증가 (rig count proxy)

**OPEC+ 분석**:
- 감산 발표 → discrete jump (event study)
- 시장점유율 전략 vs 가격 보호 전략 (1986/2014 = 점유율 → crash)
- Saudi marginal producer 역할

**우리 시스템 매핑**:
- 가설 H7 (oil_macro), H9 (storage_limit), H10 (GHR inventory)
- 신규 indicator: `cushing_utilization_pct`, `wti_noi_1yr`, `gasoline_crack_spread`, `opec_quota_z`
- Collector: EIA Open Data API (free), CME term structure

---

### C.2 Industrial Metals (copper, aluminum, nickel, zinc)

**가격 결정 driver**:
1. **글로벌 산업 수요** (Caixin PMI, ISM, 중국 credit impulse) — 1-3m lag
2. **공급 (mining)** — supply schedule 안정적, 단 strike/사고 risk
3. **LME warehouse 재고** (queue dynamics)
4. **거시 driver** (USD, 인플레, China credit cycle)

**핵심 학파**:
- **Hong-Yogo (2012)** — base metal carry 가 macro 예측력
- **Yang (2013)** — investment shocks → metal demand
- **Frankel (2014, Federal Reserve)** — interest rate ↔ commodity 평균 (real rate hypothesis)
- **Stuermer (2018, Macroeconomic Dynamics)** — supply vs demand shock 분해 (Kilian 응용)

**Copper Bellwether** (Dr. Copper):
- copper 가 가장 산업 전반 (전기·건설·자동차) 에 폭넓게 사용
- 글로벌 경기 선행 지표로 사용
- IMF (2016) 검증 — copper ↔ global GDP 1-2 분기 lag

**China demand cycle**:
- Caixin Manufacturing PMI > 52 = 확장
- 부동산 사이클 (중국 신규 시공 면적) → 건설 metal (Cu, steel)
- 중국 credit impulse (M2 + TSF growth) → 6-12m lag → metal demand

**LME warehouse queue dynamics**:
- LME 가 transparent (재고 데이터 일별 공개)
- queue length (인출 대기시간) → 실질 가용 재고 부족 신호
- 2014-2015 aluminum queue squeeze (Goldman-Metro warehouse)

**Nickel 특수성** (2022 squeeze 학습):
- LME 거래정지 사례 — exchange tail risk
- 집중 short (Xiang Guangda) → squeeze
- battery 수요 (EV) 로 구조적 demand shift

**우리 시스템 매핑**:
- 가설 H4 (china_demand_bellwether)
- 신규 indicator: `caixin_pmi_z`, `china_credit_impulse_z`, `lme_cu_stocks_z`, `lme_queue_days`
- Collector: Caixin (FRED 미보유 → 신규), LME (1차 stub)
- **archetype pooling**: copper 와 aluminum 별도 학습 X → "industrial_metals" archetype prior + soft membership (Cu 0.5, Al 0.3, Ni 0.2 등)

---

### C.3 Precious Metals (silver, platinum, palladium — gold 는 별도 방)

★main 조율 노트: gold 는 study_id=gold 별도 방 담당. 본 sub-sleeve 는 silver/platinum/palladium 위주.

**가격 결정 driver**:
1. **Monetary** (real rate ↔ 비현금자산 = silver/Pt 도 영향, 단 gold 보다 약)
2. **Industrial demand** (silver = 50% 산업, Pt = 자동차 촉매, Pd = 자동차 촉매)
3. **Investment demand** (ETF, central bank — gold 중심이라 silver/Pt 는 보조)
4. **공급 제약** (mining, by-product 비율)

**핵심 학파 (gold 위주 정리, silver/Pt 응용)**:
- **Erb-Harvey (2013, FAJ) "The Golden Dilemma"** — gold 가치평가 모델, real rate ↔ gold 상관
- **Baur-Lucey (2010, FR) "Is Gold a Safe Haven?"** — risk-off 시 gold 양수
- **silver 의 dual nature** (Christie-David et al. 2000) — silver 는 gold beta 0.8 + 산업 demand. 산업 사이클 시 silver 가 gold 와 디커플
- **Pt/Pd 의 자동차 촉매** — 가솔린 (Pt+Pd) vs 디젤 (Pt 우세). EV 전환 → Pt/Pd demand 구조 변화

**Silver 특수성**:
- gold/silver 비율 (gold-silver ratio) — 50-80 사이가 평균, 100 초과 시 silver 저평가 신호
- 산업 비중 → 글로벌 PMI 영향
- gold 보다 vol 1.5-2x 높음

**Pt/Pd 특수성**:
- South Africa 공급 의존 (Pt 70%+, Pd 40%+)
- mining strike → discrete supply shock
- EV transition → 자동차 촉매 demand 감소 long-term

**우리 시스템 매핑**:
- 가설 H1 (gold_real_rate_nexus) 는 gold 방 담당. 본 방은 **silver_real_rate_attenuated** 응용 (β 더 작고 industrial demand 노이즈)
- 신규 indicator: `silver_industrial_demand_z`, `pt_auto_catalyst_demand_z`
- **archetype pooling**: precious = silver + platinum + palladium archetype. gold 는 별도 sleeve

---

### C.4 Agricultural (corn, wheat, soybean, sugar, cotton)

**가격 결정 driver**:
1. **재고 vs 수요** (USDA WASDE stock-to-use)
2. **기상** (ENSO, drought, frost) — discrete supply shock
3. **bioenergy** (corn ethanol RFS, soy biodiesel) — energy 와 연동
4. **글로벌 무역** (USD, 중국 수입, 우크라이나/러시아 수출)

**핵심 학파**:
- **USDA WASDE** (월간 보고) — surprise 효과가 implied vol spike
- **Roberts-Schlenker (2013, AER)** — ENSO ↔ corn/soybean yield, 기상 모델
- **Stout-Babcock (2007)** — RFS mandate ↔ corn-ethanol 가격 연동
- **Bjorndal-Brorsen (2009, AJAE)** — WASDE 발표 이벤트 효과
- **Joseph-Lipper (2018, Agricultural Economics)** — climate change 의 봄/여름 ENSO 패턴 변화

**ENSO 분류**:
- **El Niño** (Pacific 동부 SST 양 anomaly) → 미국 중서부 건조 → corn/soy 수확 감소 → 가격 상승
- **La Niña** (Pacific 동부 SST 음 anomaly) → 미국 중서부 강수 정상 또는 과잉 → 양호
- **ONI index** (Oceanic Niño Index) = Niño 3.4 SST 의 3개월 이동평균. ±0.5 = ENSO event 기준
- lag: 봄 ONI → 여름 yield → 가을 가격 (3-6 month)
- wheat 은 글로벌 분산 (지역별 수확기 다름) → 영향 6-12 month

**bioenergy 연결** (★energy↔agri):
- 미국 RFS (Renewable Fuel Standard, 2007 → 2nd) — corn ethanol blend 의무 (E10)
- WTI 상승 → ethanol margin → corn 수요 증가
- soy biodiesel → 동일 메커니즘 (작은 비중)
- Brazil sugar ethanol → 글로벌 ethanol-sugar 가격 연동
- **claude R3 정밀화**: 단순 WTI return 추가 ❌ → "biofuel 채널 (빠름) + input cost 채널 (lagged natgas/비료, 느림)" 분리

**WASDE 발표**:
- 매월 11일경 (오전 12pm EST)
- Stock-to-use ratio = ending_stocks / total_use × 100
- consensus (Reuters/Bloomberg survey) 대비 actual surprise → implied vol spike
- surprise z-score > 2σ → 일일 가격 점프 ±3-5%

**우리 시스템 매핑**:
- 가설 H6 (usda_surprise_jump) — expectation 데이터 hardest
- 신규 indicator: `oni_3m_ma`, `stock_to_use_corn`, `stock_to_use_wheat`, `stock_to_use_soy`, `ethanol_crush_margin`, `nat_gas_lag_3m_for_fertilizer`
- Collector: USDA WASDE (free) + NOAA ONI (free ASCII) + survey consensus (외부 구매)
- **archetype pooling**: agri = corn + wheat + soy + sugar + cotton archetype. weather sensitivity 다름.
- **B matrix WTI inclusion** (claude refinement): biofuel 채널만 B 에. input cost (lagged natgas) Ω 에. VIF 점검.

---

## Part D. 메타 학파 (vintage·seasonality·SE 보정)

### D.1 ★Look-ahead Bias / ALFRED Real-time Vintage (★claude R3 발견)

**문제**:
- CFNAI, WASDE, PMI 등은 발표 후 **대폭 revise** (수 차례 vintage 변경)
- 최종 vintage 로 "예측력" 검정 = 미래 정보 누수 = look-ahead bias
- 결과 R² / IC 가 부풀려져 OOS 에서 무너짐

**해결**:
- **ALFRED real-time vintage** 데이터베이스 사용 (FRED 의 vintage 변형)
- `RealFredAdapter.pit_mode = "first_release"` (발표 시점 첫 값) — 이미 보유
- 신규 collector (EIA, USDA, CFTC) 도 `vintage_knowable_from` 필드 의무

**검증 지표**:
- vintage 데이터의 1차 vs 최종 차이 > 5σ 인 시리즈 → look-ahead bias risk 높음 (CFNAI, GDP, JOLTS, payrolls)
- ENSO ONI 는 revision 거의 없음 (★Gemini R2 정확히 지적)

**우리 시스템에서**:
- 모든 신규 collector 의 `VintageProvider.realtime(series, period, as_of)` 인터페이스 강제
- 검정에서 final vintage 사용 시 explicit comment 필수

---

### D.2 Deseasonalization (★R3 claude 보강)

**문제**:
- agri (corn/wheat/soy) — 결정적 계절성 (수확기 가격 패턴)
- natural gas — winter heating demand
- gasoline — summer driving season
- 안 제거하면 Bai-Perron 이 **seasonal cycle 을 structural break 로 오인**

**해결**:
- **STL** (Seasonal-Trend decomposition using Loess) — robust, statsmodels.tsa.seasonal_decompose
- **X-13 ARIMA-SEATS** — Census Bureau 표준, statsmodels.tsa.x13_arima_analysis
- monthly: period=12, weekly: period=52

**구현**:
```python
from statsmodels.tsa.seasonal import STL
result = STL(series, period=12, robust=True).fit()
deseasonalized = series - result.seasonal
```

**우리 시스템 매핑**:
- agri/energy(natgas) 지표 학습 전 deseasonalization pipeline
- 가설 H10 (GHR inventory) 검증 시 inventory 시계열도 deseasonalize

---

### D.3 Overlapping Return SE 보정 (★R3 claude 보강)

**문제**:
- monthly + holding period 12m → 동일 데이터점이 12번 중복 사용
- OLS SE 가 underestimate (실제 분산 더 큼)
- t-statistic 부풀려짐 → false positive

**해결**:
- **Newey-West HAC** (Heteroskedasticity-Autocorrelation Consistent) SE
- **Hansen-Hodrick** SE (overlapping return 특화)
- lag: holding period 와 일치 (12m holding → 12 lag)

**구현** (statsmodels):
```python
import statsmodels.api as sm
model = sm.OLS(y, X)
results = model.fit(cov_type='HAC', cov_kwds={'maxlags': 12})
```

**우리 시스템에서**:
- Fama-MacBeth cross-section 회귀 시 표준
- IC 산출 시 — `effective_n_ar1` (이미 보유 `conditional_correlation.py`) 와 정합
- `block_bootstrap_se` (이미 보유) 가 보완 — non-parametric

---

## Part E. 우리 시스템 매핑 (이론 → 코드 → 가설 → flag)

### E.1 KWB Theory of Storage → 검증·indicator

| 이론 항목 | 코드 매핑 | 가설 | flag |
|---|---|---|---|
| F=S·exp((r+u−y)(T−t)) | y 역산 회귀 (신규) | H2 | carry_sign_flip |
| convenience yield y | `carry_convenience_zscore` (보유) | H2 | convenience_z extreme |
| Backwardation/Contango | `carry_forward_slope` (보유) | H2/H3 | contango_persistence |
| Basis 정의 | log(F1)−log(F2) (BGR) | H3 | basis_extreme |

### E.2 GHR (2013) inventory-as-state-variable → 신규

```python
# core/structure/commodity_assumptions.py 신규 함수
def normalized_inventory_state(inv_z, basis, fwd_return, hp_lambda=1600):
    """GHR 2013 — normalized inventory 가 basis + prior return 동시 설명력 검정.
    공동 R² > 0.30 + basis 회귀 prior_sign=neg + return 회귀 prior_sign=neg.
    """
    # HP filter detrend
    from statsmodels.tsa.filters.hp_filter import hpfilter
    cycle_inv, trend_inv = hpfilter(inv_z, lamb=hp_lambda)
    norm_inv = cycle_inv / trend_inv

    # 공동 회귀
    basis_r2 = sm.OLS(basis, sm.add_constant(norm_inv)).fit().rsquared
    return_r2 = sm.OLS(fwd_return, sm.add_constant(norm_inv)).fit().rsquared

    return {"norm_inv_state": norm_inv, "basis_r2": basis_r2, "return_r2": return_r2,
            "joint_explanation": basis_r2 > 0.15 and return_r2 > 0.15}
```

- 가설 H10 (ghr_inventory_state_variable)
- flag: `inventory_state_dominant` (basis_r2 + return_r2 > 0.30 → H2/H3/BGR 가중치 축소)

### E.3 BGR (2019) basis-momentum → 신규 indicator

- `bgr_basis_momentum_12m` (family=valuation, transform=level ∈ {−1,0,+1})
- 가설 H3 (roll_cost_drag_collapse) 의 핵심 시그널
- Phase 2 (CME term structure collector 필요)

### E.4 Kilian (2009) SVAR → 신규 모듈

```python
# core/structure/kilian_oil_svar.py 신규
class KilianOilSVAR:
    """3-shock SVAR identification: supply / aggregate demand / precautionary.
    Cholesky 또는 sign restriction. Hamilton NOI 의 source-conditional 확장."""
    def fit(self, oil_supply, real_activity, oil_price):
        # statsmodels VAR + structural decomposition
        ...
    def shock_at(self, as_of):
        """as_of 시점의 dominant shock 분류 (supply / demand / precautionary)"""
        ...
```

- 가설 H7-K (oil_macro_kilian_decomposition)
- Q3(b) energy↔equity cross-sleeve covariance — shock source 조건부

### E.5 Tang-Xiong financialization → 3-track 분리

| Track | 측정 | 매핑 |
|---|---|---|
| Driver (H5) | CIT position (pre-2015 IID + post-2015 Barclays) | indicator: `cit_long_position_z` |
| Outcome (H5 falsification) | 60일 rolling cross-corr 평균 | indicator: `cross_sleeve_mean_corr_60d` |
| Speculator (H8) | MM net long / OI z-score (CFTC DCOT) | indicator: `mm_net_long_oi_z` |

### E.6 Hamilton NOI → 신규 indicator

- `wti_noi_1yr` = max(0, WTI_t − max(WTI_{t-12..t-1}))
- 가설 H7-raw (Phase 1.5, FRED 즉시)
- Kilian SVAR 와 분리 검증

### E.7 Deaton-Laroque positive skewness → 검정

- 가격 분포 skewness 측정 (scipy.stats.skew)
- 가설 H9 (storage_limit_nonlinearity) 의 base
- flag: `price_skewness_extreme` (skew > 1.5 → distribution 정상화 가정 위반, FIGARCH 적합성 의심)

### E.8 우리 보유 검증 통계 + 신규 모듈

| 통계 | 보유 / 신규 | 용도 |
|---|---|---|
| variance_ratio (Lo-MacKinlay) | 보유 (commodity_assumptions.py) | H10 mean reversion |
| threshold_regression (Hansen) | 보유 | H9 nonlinear, H2 분할 |
| oversupply_decoupling | 보유 | 1986/2014 oil crash 감지 |
| carry_forward_slope (sign_flip) | 보유 | H3 carry premium 붕괴 |
| seasonal_f_test | 보유 (agri) | deseasonalization 입력 |
| e-CUSUM K adaptive | 보유 (weight_falsification) | 보강 — returns 기반, |ρ|<0.3 caveat |
| **panel cointegration** (W-H 2016) | 신규 | H2 재고-가격 장기균형 |
| **FIGARCH 또는 GARCH+Hurst** | 신규 (선택) | weekly resample, long-memory |
| **Bai-Perron sup-F sequential** | 신규 | structural break (PELT 아님) |
| **Kilian SVAR** | 신규 | H7-K source 분해 |
| **GHR inventory state R²** | 신규 | H10 통합 검정 |
| **STL deseasonalization** | 신규 | agri/natgas 전처리 |
| **HAC SE / Hansen-Hodrick** | statsmodels 활용 | overlapping return |
| **HP filter + skewness** | scipy/statsmodels | H9 정상화 검정 |

---

## Part F. 가설 11개 ↔ 학파 매핑 표

| 가설 ID | 핵심 학파 | 측정 indicator | 데이터 | Phase |
|---|---|---|---|---|
| H1 gold_real_rate_nexus | Erb-Harvey 2013, Baur-Lucey 2010 (gold 방) | partial_corr(Au,DFII10|DXY) | FRED+Yahoo | 1 (gold방) |
| H2 theory_of_storage_backwardation | Kaldor-Working-Brennan, Fama-French 1987 | inv_z, F1-F2, convenience_z | EIA+CME | 2 |
| H3 roll_cost_drag_collapse | Erb-Harvey 2006, BGR 2019, Szymanowska 2014 | bgr_basis_momentum, term_slope | CME+GSCI | 2 |
| H4 china_demand_bellwether | Yang 2013, Hong-Yogo 2012 | Caixin_z, copper_return | Yahoo+Caixin | 1.5 |
| H5 financialization_reflexivity | Tang-Xiong 2012, Singleton 2014 | cit_long_z (driver), cross_corr_60d (outcome) | IID/Barclays + Yahoo | 1 (outcome) / 2 (driver) |
| H6 usda_surprise_jump | Bjorndal-Brorsen 2009, Roberts-Schlenker 2013 | wasde_surprise_z | USDA + consensus | 2 (hardest) |
| H7-raw oil_macro_NOI | Hamilton 1996/2003 | wti_noi_1yr, CFNAI | FRED | 1.5 |
| H7-K oil_macro_kilian | Kilian 2009 SVAR | kilian_shock_classification | EIA+BDI+FRED | 2 |
| H8 cot_momentum (speculator) | Hicks-Keynes, Hong-Yogo 2012 | mm_net_long_oi_z | CFTC DCOT | 1.5 |
| H9 storage_limit_nonlinearity | Deaton-Laroque 1992 | cushing_util_pct, skew, threshold | EIA + CME | 2 |
| H10 ghr_inventory_state | Gorton-Hayashi-Rouwenhorst 2013 | norm_inv_state, joint_R² | EIA+LME+USDA | 2 |
| H11 liquidity_storage_crash | composite (D-L + Tang-Xiong + 2008 deleveraging) | storage>90% + TED/FRA-OIS>2σ | EIA+FRED | 3 (kill switch) |

---

## Part G. 미해결 질문 → 2-3 실데이터 검증으로 풀거나 추가 자문

1. **H10 (GHR) 의 R² 임계값 0.15 가 우리 표본에서 적합한가?** — 실데이터로 31 commodity 한정 검증 시 우리 가용 sub-sleeve (4) 에서도 같은가? → 2-3 H10 sub-sleeve 별 R² 측정
2. **BGR basis_momentum (H3) 의 monthly vs weekly frequency** — Phase 2 collector 가 daily 면 monthly resample 권장 vs weekly? → 2-3 검증
3. **Kilian SVAR (H7-K) identification scheme** — recursive Cholesky vs sign restriction vs Baumeister-Hamilton 2019? → 2-3 또는 R4 추가 자문 (statsmodels VAR 표준 + Kilian-Park 2009 코드 참조)
4. **CIT 단절 (2015) 후 driver 대체** — Barclays index AUM 분기 데이터 가용성/비용? 또는 reduced-form 으로 outcome 만? → main 결정 또는 외부 데이터 조사
5. **archetype delta_arch_by_type 의 sleeve 분류** — Cyclical 그룹(energy+industrial) 단일 archetype vs 2개 archetype? Group C (agri idiosyncratic) 의 weather conditioning 별도 sub-archetype? → 2-3 데이터로 cross-correlation 측정 후 결정

---

## §END

> KIT v2 §2-2 완료. theory-notes.md = 이론 정독 정리 (가격결정 원리 + 지표 의미·관계도 + 우리 시스템 매핑).
> 다음 단계: 2-3 실데이터 시계열 검증 (H1·H5·H4 우선) → validation-*.md + study_session.yaml.
> ⛔ 2-3 는 직접 실행 (KIT v2 §2-2 → §2-3 는 게이트 없음, §2-1 만 main 승인 게이트).
