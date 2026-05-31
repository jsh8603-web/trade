---
tags: [type/direction, domain/commodity, phase/study-system, gate/pre-2-2]
date: 2026-05-30
note: STUDY-KIT §2-1 v2 산출 — 자문 다회 (R1+R2+R3, claude-web + gemini-web 각 3R 총 6 응답) 수렴 결과. main 승인 게이트 입력.
study_id: commodity
sub_sleeves: [energy, industrial, precious, agri]
---

# direction.md — commodity 방향성 (R1+R2+R3 수렴)

> **이 문서의 위치**: STUDY-KIT §2-1 산출 (방향성·자문 다회 결과).
> ★여기서 멈춤 → main(btn-Codlearn) 승인 대기 → 승인 후 2-2 (이론학습 raw/theory-notes.md) 진입.

## §0. 자문 수행 메타

| Round | 채널 | 응답 크기 | 핵심 |
|---|---|---|---|
| R1 | gemini-web (Pro) | 8441 자 | 학파 8개 + 검증 통계 5종 + 가설 8개 yaml |
| R1 | claude-web (Opus 4.8 High) | 600 자 | web-search 도중 끊김 (미완) |
| R2 | gemini-web | 8511 자 | 구현 디테일 7개 (BGR 식, FIGARCH, Bai-Perron, e-CUSUM, financialization, B matrix, ENSO) |
| R2 | claude-web | 330 자 | 또 web-search 끊김 (미완) |
| R3 | gemini-web | 6851 자 | priority, cross-sleeve, tail risk, collector ranking + 신규 가설 1개 |
| R3 | claude-web (no-search prefix) | 14864 자 | **★결정적 critique**: H5≠H8 분리, PELT≠Bai-Perron, Kilian/GHR 누락, ALFRED vintage 경고 |

raw 누적: `raw/round-1-prompt.md`, `raw/round-1-gemini.md`, `raw/round-1-claude.md`, `raw/round-2-*.md`, `raw/round-3-*.md`. R1·R2 claude-web 은 미완이라 R3 에서 명시 "DO NOT SEARCH" prefix 로 보완 → 14k 풍부 응답.

**수렴 판정**: (a) 두 모델 답변이 R3 에서 의미 차이 명확 (claude 가 gemini critique → 통계적 정합성 보강), (b) 새 의문 비생성, (c) R3 후 가설/검증 디테일 안정. 3R 진행 후 수렴 선언.

---

## §1. 이론 수집 방향 (① 무엇을 읽어야 하나)

### 1.1 보편 학파 (4 sub-sleeve 공통, 필수 정독)

| 학파 | 핵심 명제 |
|---|---|
| **Kaldor (1939) / Working (1949) / Brennan (1958)** | Theory of Storage — convenience yield 정립. F(t,T) = S·exp((r+u−y)(T−t)) |
| **Hicks-Keynes Normal Backwardation** | 생산자 헤징 압력 → 투기자가 risk premium 요구 → 평균 backwardation |
| **Erb-Harvey (2006, FAJ)** | 원자재 수익 = spot + roll + collateral 3분해 |
| **★Gorton-Hayashi-Rouwenhorst (2013, Rev Finance)** ★R3 누락 보강 | inventory-as-state-variable — KWB(storage) + HK(backwardation) 를 normalized inventory 로 통합. basis·prior return 동시 설명 |
| **★Deaton-Laroque (1992, REStud)** ★R3 누락 보강 | Competitive Storage Model — 재고 zero lower bound → 가격 분포 positive skewness. 공급부족 시 spike, 공급과잉 시 mean revert |

### 1.2 Buy-side Quant SOTA (필수)

| 학파 | 발견 |
|---|---|
| **Asness-Moskowitz-Pedersen (2013, JF)** | "Value and Momentum Everywhere" — commodity Value(carry) + 12-1 Momentum universality |
| **★Bakshi-Gao-Rossi (2019, Mgmt Sci)** | basis + relative-basis 결합 BasisMomentum 시그널 (단순 carry/momentum 우월) |
| **★Tang-Xiong (2012, RFS)** | Index investment financialization — 인덱스 자금 유입 시 sub-sector·commodity-equity 교차 상관 비정상 상승 |
| **★Kilian (2009, AER)** ★R3 누락 보강 | SVAR oil shock decomposition — supply / aggregate demand / precautionary 3분해. **macro 효과는 source 의존** (supply-driven 유가↑ = equity−, demand-driven = equity+) |
| **★Szymanowska et al. (2014, JF)** | Basis premium cross-sectional factor — 곡선 구조가 단순 roll yield 넘어 가치 |
| **★Hamilton (1996 JME, 2003 JoE)** | Net Oil Price Increase (NOI) 비선형 — 1년 최고치 경신폭만 침체 예측, 비대칭. (Kilian 으로 sharpen) |
| **Fama-French (1987, JB)** | theory of storage 실증 — H2 정식 reference |
| **Koijen-Moskowitz-Pedersen-Vrugt (2018, JFE) "Carry"** | cross-asset carry universality (Q3 cross-sleeve 권고) |
| **Acharya-Lochstoer-Ramadorai (2013, JFE)** | producer hedging demand + financial constraints — hedging pressure 정련 |
| **Singleton (2014, Mgmt Sci)** | investor flows & 2008 oil boom/bust — Tang-Xiong 보완 |
| **Hong-Yogo (2012, JFE)** | open interest 의 macro 예측력 — H8 보강 |

### 1.3 Sub-sleeve 특화

| Sleeve | 학파 |
|---|---|
| **Energy** | Kilian (★supply/demand 분해), Hamilton (NOI), EIA STEO shale break-even economics, refinery crack spread |
| **Industrial metals** | China demand cycle (Caixin PMI), LME warehouse queue 동학, copper bellwether 가설 |
| **Precious metals** | Erb-Harvey (2013, FAJ) "Golden Dilemma", Baur-Lucey (2010, FR) "Is Gold a Safe Haven?", real rate ↔ gold partial-corr 문헌 |
| **Agricultural** | USDA WASDE surprise 효과, Roberts-Schlenker (2013) ENSO 기상 risk yield, ★bioenergy (RFS mandate, ethanol crush margin) |

### 1.4 메타 누락 (claude R3 추가 — 반드시 보강)

- **★Look-ahead bias / vintage**: CFNAI·WASDE 등은 final vintage 가 대폭 revise. final 로 predictive 검정 = look-ahead 누수. **ALFRED real-time vintage 필수** (H6/H7 validity 직접 위협).
- **★Deseasonalization 전처리**: agri·natgas 의 price·vol 결정적 계절성. 안 하면 Bai-Perron 이 seasonal 을 break 로 오인.
- **★Overlapping return SE 보정**: Fama-MacBeth + overlapping holding period 시 SE underestimate. **Hansen-Hodrick / Newey-West** 보정 필수.

---

## §2. 이론 검증 방향 (② 어떻게 시계열 검증)

### 2.1 Theory of Storage 검증

- F(t,T) = S·exp((r+u−y)(T−t)) → **y(convenience yield) 역산** → 재고(EIA/LME/USDA) 와 회귀
- **Westerlund-Hosseinkouchack (2016) panel cointegration** — 비정상 시계열(재고 level vs F-S spread) 장기균형 검정. 공적분 벡터 부호 일치 확인
- 우리 코드: `commodity_assumptions.carry_forward_slope` + 신규 panel cointegration util

### 2.2 Carry-Momentum (BGR + AMP)

- **BGR basis_momentum** (R2 식 확정):
  ```
  Basis_t = ln(F1) − ln(F2)
  RelBasis_t = Basis_t − (1/12)·Σ_{i=1..12} Basis_{t−i}
  BasisMom_t = sign(Basis_t) × sign(RelBasis_t)  ∈ {−1, 0, +1}
  ```
- Fama-MacBeth 횡단면 회귀 + Rolling Portfolio Sharpe/MDD
- **Newey-West / Hansen-Hodrick SE 보정** (overlapping return)
- 신규 indicator id: `bgr_basis_momentum_12m`

### 2.3 Variance regime (long memory + volatility)

- monthly N=30~50 → **weekly resample** (N=120~200) 권장
- 옵션 1 (도전): **FIGARCH(1,d,1)** with `arch` package — d 추정 SE 확보
- 옵션 2 (안정 권장 — claude R3): **GARCH(1,1) + Hurst exponent** — N=50에서도 수렴, regime vol 군집 파악 충분
- 우리 표본 검정력 부족 시 옵션 2 default, 옵션 1 sub-sleeve 일부에 한정

### 2.4 Structural break — ★claude critique 반영 후 수정

**기각**: 이전 안 (PELT + 경제이벤트 ±3m confirm).
- claude critique: (a) PELT ≠ Bai-Perron 명명 오류. PELT(Killick 2012) = penalized cost segmentation, 분포이론 검정통계량 없음. (b) 이벤트 confirm = **HARKing / selection on dependent variable** — shale/COVID/우크라는 이미 큰 충격으로 알려져 out-of-sample 정보 0.

**채택 (수정안)**:
1. **진짜 Bai-Perron (1998, 2003)**: 15% trimming + max break 사전 고정 + sup-F sequential test + **break date 95% CI** (Bai 1997)
2. 경제 이벤트는 **CI 포함 시 confirmation** 만 (분석자 결정 ❌ → 데이터 결정 ✓). attribution/communication 용도 분리
3. PELT 굳이 쓰면 `model="rbf"` (mean+variance 동시) + `mBIC` 또는 `Lavielle adaptive penalty`. `model="linear"` 만 쓰면 variance regime shift 놓침
4. 옵션 추가: **Bayesian change point** (Barry-Hartigan PPM, `bcp` R/Python) — posterior break probability, heavy tail robust

**Two-speed 설계** (claude R3 핵심 권고):
- **Quarterly expanding-window Bai-Perron** = 구조적 break map (전체 history + full CI). 거시 구조변화 분기 단위 의미
- **Online e-CUSUM** = "이번 달 변화" cheap 탐지
- "current regime" 추정 = 별도 **rolling 10yr window** (고대 break 가 지배 방지)
- → R2 follow-up (monthly vs quarterly) 답: 둘 다, 역할 분리

### 2.5 e-CUSUM K adaptive — claude R3 정합성 확인 후 수정

**공식 유지**: K_sleeve = K_base × (σ_sleeve/σ_stock) × √((1+ρ)/(1−ρ))
- σ ratio: Page (1954) K = δσ/2 → 정확 ✓
- √((1+ρ)/(1−ρ)) = √VIF, n_eff = n·(1−ρ)/(1+ρ) textbook ✓
- BUT: **Page/Lorden i.i.d. 코어와는 정합하지 않고**, 후대 보정 (Johnson-Bagshaw 1974, Vasilopoulos-Stamboulis 1978, Runger-Willemain 1995) heuristic

**Caveat 필수 준수**:
- **returns/log-diff 에서만** 작동 (price level near-unit-root → ρ→1 blow-up)
- |ρ| < 0.3 유지 권장 (보정 작아 안전)
- σ_sleeve = **marginal (1-step) vol** 고정 (long-run vol 이면 double-counting)
- 더 rigorous 대안: **pre-whitening** — ARMA fit → residual i.i.d. → 표준 CUSUM (Alwan-Roberts 1988). Lorden optimality 유지

### 2.6 Financialization 측정 — ★H5≠H8 분리 (claude R3 결정적 critique)

**기각**: Gemini R2 의 MM_net_long / OI 12m z-score = financialization measure.
- claude critique: MM (Money Manager) = active speculator (CTA/hedge fund) = Hicks-Keynes hedging pressure 또는 Working speculative T-index → **H8 (speculative pressure)** 매핑이 정확. Tang-Xiong financialization 은 passive long-only index 자금이라 **construct 가 다름**.

**3-track 분리 (채택)**:

| Construct | 측정 | 가설 |
|---|---|---|
| Financialization **driver** | (a) pre-2015 CFTC IID (Index Investment Data) (b) Barclays/Bloomberg commodity index AUM 분기 (c) Supplemental CIT 12 농산물 시장 index position | H5 financialization_reflexivity |
| Speculative pressure | MM net long / total OI z-score | H8 cot_momentum_amplification |
| Financialization **outcome** | 비에너지↔WTI↔S&P500 60일 rolling cross-correlation 평균 | H5 falsification 의 dependent var |

**z-score 정규화 수정**:
- 12m rolling z → **expanding-window z** 또는 **EWMA-vol-adjusted z** (regime-dependent normalization 회피)
- 정규화 대안: Working T = 1 + SS/(HL+HS)
- OI 분모 내생성: financialization 으로 OI 부풀려진 시기엔 ratio 둔감 — 보조 measure 병행

### 2.7 Kilian (2009) oil shock decomposition — ★H7 + cross-sleeve 결정적

- **SVAR** (3 shock identification): supply / aggregate demand / oil-specific demand (precautionary)
- 구현: Kilian-Park (2009) 또는 Baumeister-Hamilton (2019) ZIP
- H7 (oil_macro_nonlinear_shock) 을 **단일 NOI threshold → source-conditional** 로 sharpen
- Q3(b) energy↔equity 부호: supply-driven oil↑ = equity − (cost shock), demand-driven oil↑ = equity + (pro-cyclical). **단일 정적 prior 금지**

### 2.8 Vintage 보호 (★중대 — R1·R2 침묵)

- **ALFRED real-time vintage** 필수 (CFNAI/WASDE/PMI 대폭 revise)
- 우리 `RealFredAdapter.pit_mode="first_release"` 이미 보유 — point_in_time 강제
- 신규 collector (EIA, USDA, CFTC) 도 vintage_knowable_from 필드 의무

### 2.9 평균회귀 가설 검증

- 기존 보유: `variance_ratio` (Lo-MacKinlay), `threshold_regression` (Hansen), `oversupply_decoupling`
- 보강: **deseasonalization** 전처리 (agri/natgas, claude R3) — STL 또는 X-13 ARIMA-SEATS

---

## §3. 핵심 가설 초안 (③ 11개 — 반증조건 정량)

R1 (8개) + R3 (3개 신규/수정) = **11개**. claude critique 반영 (H5 measure 수정, H7 Kilian 확장).

### Phase 1 (FRED + Yahoo + 기존 collector — 즉시 검증 가능)

```yaml
- hypothesis_id: gold_real_rate_nexus
  statement: 금 가격은 달러 통제 시 실질금리(DFII10)와 강한 음의 부분 상관관계를 갖는다
  sub_sleeve: precious
  falsification_criterion: |
    36m rolling partial-corr(Au, DFII10 | DXY) > -0.1 6개월 이상 OR 부호 전환 6m 지속
  data_required: FRED(DFII10) + FxStore(DXY) + Yahoo(GC=F)
  lag: contemporaneous
  prior_strength: 0.9
  phase: 1
  rationale: "Erb-Harvey 2013, Baur-Lucey 2010. 20+ 년 데이터 즉시 가용. ★압도적 최우선 ROI"

- hypothesis_id: financialization_reflexivity
  statement: VIX 급등 regime 에서 commodity sub-sector 간 교차 상관관계가 비정상 상승한다
  sub_sleeve: all
  falsification_criterion: |
    FRED(VIX) > 30 AND 60일 rolling cross-corr(energy/agri/metal/precious) 평균 < 0.2
  data_required: |
    outcome side (Phase 1): Yahoo (VIX·sector ETF) — 가격만으로 산출 가능
    driver side (Phase 2): pre-2015 IID + post-2015 Barclays index AUM (분기) OR Supplemental CIT
  lag: contemporaneous (outcome) / quarterly (driver)
  prior_strength: 0.7   # claude critique 후 0.8→0.7 (driver-outcome 분리 복잡성)
  phase: 1 (outcome) / 2 (driver)
  rationale: "Tang-Xiong 2012, Singleton 2014. outcome 은 가격만으로 2004 전후 Chow break 검증 가능"

- hypothesis_id: china_demand_bellwether
  statement: 중국 제조업 팽창 국면은 1분기 후 산업금속 가격 구조적 상승을 견인한다
  sub_sleeve: industrial
  falsification_criterion: |
    Caixin_PMI > 52 (or China credit impulse > +1σ) 3개월 지속 시, LME copper 3m return < 0
  data_required: Yahoo(HG=F copper) + FRED(NAPM, China data 별도) + 신규 Caixin collector
  lag: 3 month
  prior_strength: 0.75
  phase: 1.5
  rationale: "copper bellwether 가설. Yahoo copper 즉시, Caixin 수집은 미국 ISM 경유 또는 신규"
```

### Phase 1.5 (collector 쉬움)

```yaml
- hypothesis_id: cot_momentum_amplification
  statement: |
    MM (Money Manager) net long 의 극단 쏠림 (speculative pressure)은 모멘텀 붕괴 선행
  sub_sleeve: all
  falsification_criterion: |
    MM net long / total OI z-score rank > 95th percentile 3m 후 가격 지속 상승
  data_required: CFTC DCOT (Money Manager 카테고리) + CME front month price
  lag: 1-3 month
  prior_strength: 0.65
  phase: 1.5
  rationale: "Hong-Yogo 2012, Sanders-Irwin 약 예측력. MM = speculative pressure 정확 매핑 (financialization X)"

- hypothesis_id: oil_macro_raw_threshold
  statement: 유가 1년 최고치 경신폭(NOI)이 30% 초과 시 12개월 후 실물경기 위축
  sub_sleeve: energy
  falsification_criterion: WTI_1yr_NOI > 30% AND 12개월 후 CFNAI > 0 유지
  data_required: FRED(DCOILWTICO + CFNAI) — ALFRED real-time vintage 필수
  lag: 6-12 month
  prior_strength: 0.7
  phase: 1.5
  rationale: "Hamilton 1996/2003. raw threshold 만 Phase 1.5. Kilian 분해는 H7-K 로 Phase 2 별도"
```

### Phase 2 (신규 collector 필요)

```yaml
- hypothesis_id: theory_of_storage_backwardation
  statement: 재고 감소 → convenience yield 상승 → 선물 곡선 backwardation 역전
  sub_sleeve: energy, industrial
  falsification_criterion: |
    inventory_z < -1.5 (재고 타이트) 인데 (F1-F2)/F1 > 0 (contango) 가 4주 지속
  data_required: EIA(crude stocks) + LME(warehouse stub) + CME(WTI F1·F2)
  lag: 1-4 week
  prior_strength: 0.85
  phase: 2
  rationale: "Kaldor-Working-Brennan, Fama-French 1987. CME term structure 필수"

- hypothesis_id: roll_cost_drag_collapse
  statement: 구조적 contango 국면에서 commodity 인덱스 roll cost 누적은 carry premium 파괴
  sub_sleeve: all (특히 energy)
  falsification_criterion: contango 지속 > 6m 인데 commodity_index_return > spot_return + 2%
  data_required: GSCI/BCOM index + CME(F1, F2 chain)
  lag: contemporaneous
  prior_strength: 0.95
  phase: 2
  rationale: "Bakshi-Gao-Rossi 2019, Szymanowska 2014. BGR basis_momentum 함께 검증"

- hypothesis_id: usda_surprise_jump
  statement: WASDE stock-to-use 발표치가 컨센서스 크게 하회 시 당일 비대칭 양의 점프
  sub_sleeve: agri
  falsification_criterion: WASDE_surprise_z < -2.0 AND F1 daily return < 0 (즉각 상승 실패)
  data_required: USDA WASDE actual + survey consensus (expectation 데이터 hardest)
  lag: 0-1 day (event study)
  prior_strength: 0.8   # claude critique: expectation 데이터 어려움
  phase: 2 (low priority — collector hardest)
  rationale: "Roberts-Schlenker 2013. expectation 데이터 외부 구매 또는 자체 forecast 필요"

- hypothesis_id: oil_macro_kilian_decomposition   # H7 → H7-K (확장)
  statement: |
    유가 변동의 macro 효과는 source 의존 — supply shock 은 equity 음, demand shock 은 양
  sub_sleeve: energy
  falsification_criterion: |
    Kilian SVAR 분해 후 supply-shock-driven WTI↑ 5+ 이벤트에서 S&P500 12m 평균 > 0 (음효과 부재)
  data_required: |
    WTI(FRED) + 글로벌 원유 생산(EIA) + 글로벌 활동지수(Kilian index, Yahoo BDI 대체) + S&P500
  lag: 6-12 month
  prior_strength: 0.8
  phase: 2 (SVAR 구현 + 데이터 조립)
  rationale: "Kilian 2009 AER. H7 raw 와 분리 — Kilian source 분해가 더 정확. cross-sleeve energy↔equity 부호 결정"

- hypothesis_id: storage_limit_nonlinearity   # ★신규 (claude R3)
  statement: |
    저장 가동률 > capacity 임계 시 가격-재고 관계가 convex/explosive (음수 가격 가능)
  sub_sleeve: energy, industrial
  falsification_criterion: |
    EIA Cushing 가동률 > 90% AND (F1-F2)/F1 > +5% 미달 (super-contango 미발현)
    AND 60일 realized vol < 평균 (vol 급등 미발현)
  data_required: EIA(Cushing utilization) + CME(WTI F1·F2) + Yahoo(realized vol)
  lag: weekly
  prior_strength: 0.8
  phase: 2
  rationale: "2020-04 negative WTI 메커니즘. 기존 8개 가설은 mean response 만 잡고 nonlinear tail 놓침"

- hypothesis_id: ghr_inventory_state_variable   # ★신규 (claude R3)
  statement: |
    normalized inventory 가 basis + prior return 을 동시에 설명 (단일 state variable 가설)
  sub_sleeve: all
  falsification_criterion: |
    inventory_z 로 설명되는 basis R² 와 prior return R² 가 둘 다 < 0.15 (공동 설명력 부재)
  data_required: EIA + LME + USDA inventory + CME term structure + 가격
  lag: contemporaneous
  prior_strength: 0.75
  phase: 2
  rationale: |
    Gorton-Hayashi-Rouwenhorst 2013. KWB(storage) + HK(backwardation) 통합.
    ★H2/H3/BGR basis_momentum 이 redundant 가능성 검정 (셋 다 같은 scarcity proxy)
```

### Phase 3 (장기 — 시스템 통합 후)

```yaml
- hypothesis_id: liquidity_storage_constraint_crash   # ★신규 (gemini R3)
  statement: |
    실물 재고 한계율 + 금융 유동성 경색이 동시 임계 도달 시 crash regime → 비상 셧다운
  sub_sleeve: all
  falsification_criterion: |
    저장 가동률 > 90% AND TED/FRA-OIS > +2σ AND 60일 후 sleeve return > 0 (crash 미발현)
  data_required: EIA + FRED(TED spread, FRA-OIS) + 가격
  lag: contemporaneous + 60일 forward
  prior_strength: 0.85
  phase: 3 (시스템 통합 후 — kill switch 역할)
  rationale: "2008/2020 deleveraging + storage 결합 메커니즘. weight 0 강제 clamp 의 트리거"
```

---

## §4. 검증 우선순위 + Collector ranking

### 4.1 Collector 우선순위 (양쪽 모델 합의)

| 순위 | Collector | 비용 | Unlock 가설 | 비고 |
|---|---|---|---|---|
| 1 | **DFII10 (FRED)** | 1줄 추가 | H1 (★최고 ROI) | FRED_SERIES dict 수정만 |
| 2 | **CFTC COT** | 신규, 무료/주간/쉬움 | H8 (speculative) + Q4 squeeze flag | CFTC public API |
| 3 | **CME term structure** | 신규, 최고 effort (chain handling, roll) | H2 + H3 + BGR + H10 + storage_limit | 거의 모든 carry 검증의 입력 |
| 4 | **EIA inventory** | 신규, free API | H2 (energy 측) + storage_limit flag | EIA Open Data API |
| 5 | **NOAA ENSO/ONI** | 무료 ASCII, revision 없음 | agri conditioning | cpc.ncep.noaa.gov |
| 6 | **USDA WASDE** | 신규 + expectation 데이터 hardest | H6 만 | survey consensus 외부 구매 또는 자체 forecast |

### 4.2 검증 Phase 분류

- **Phase 1 (즉시, 추가 자원 0)**: H1, H5 (outcome), H4 (Yahoo copper 부분)
- **Phase 1.5 (collector 쉬움)**: H8 (CFTC), H7-raw (FRED), H4 (Caixin)
- **Phase 2 (CME + EIA + USDA + Kilian SVAR)**: H2, H3, H6, H7-K, H9 (storage_limit), H10 (GHR), H5 (driver)
- **Phase 3 (시스템 통합 후)**: H11 (liquidity_storage_constraint_crash, kill switch)

### 4.3 ★최우선 3 가설 (즉시 시작 권고)

1. **H1 gold_real_rate_nexus** — 데이터 zero-effort, 20년+ 시계열, falsification 깔끔
2. **H5 financialization (outcome side)** — 가격만으로 2004 전후 Chow break 검증
3. **H4 china_demand_bellwether** — Yahoo copper 즉시 + Caixin Phase 1.5

---

## §5. Cross-sleeve portfolio construction (Q3 합의)

### 5.1 Weight allocation (Risk Parity + BL)

- ❌ Equal weight (1/4) — vol 격차 (energy 35-45% vs precious 15-20%) 무시
- ✓ **Risk parity (inverse vol) 를 equilibrium prior** + 1/N(0.3) shrinkage + Grinold w∝Ω·IC tilt
- Architecture 정합: 기존 R15 cap(0.4) + clamp_floor(0.25) 그대로 + BL view 로 IC 주입

### 5.2 Cross-sleeve covariance prior (regime conditional)

- **단일 정적 prior 금지** (★energy↔equity 부호는 Kilian shock source 의존)
- Risk-off / deleveraging regime: industrial↔equity +0.5~+0.7, precious↔bond + (flight-to-quality, unstable), energy↔equity = source 분해 조건부
- Inflationary boom: energy↔bond −, energy↔equity − (cost shock margin 압박)
- Risk-on: 모든 상관 commodity-beta 로 압축

### 5.3 SLEEVE_BLOC 등록 (★수정)

**기각**: "cyclical(energy+industrial) / defensive(precious+agri)" 2×2 대칭.
- claude critique: agri 는 weather/supply-driven idiosyncratic, **defensive 아님** (safe-haven 역할 없음). precious 와 묶으면 category error.

**채택**:
- **Group A — Cyclical Commodity** (energy + industrial): pro-cyclical, China demand 민감
- **Group B — Defensive/Monetary** (precious): safe-haven, real rate driven
- **Group C — Idiosyncratic/Supply** (agri): weather/USDA-driven, macro beta 낮음

---

## §6. Tail risk / Confidence hooks (Q4 합의)

5 historical crash 분석 → 공통 thread 5종:

| Crash | 메커니즘 | 선행 신호 | Confidence Hook Flag |
|---|---|---|---|
| 1986 oil | OPEC quota 붕괴 | quota cheating, contango 확대 | `oversupply_decoupling` (commodity_assumptions 보유) |
| 2008 동반 crash | Deleveraging, margin call | TED↑, LIBOR-OIS↑, cross-asset corr→1 | `systemic_liquidity_drain` (신규) |
| 2014-16 oil | Shale + OPEC 감산 거부 | US 생산↑, EIA_inv↑, contango steepening, rig count | `oversupply_decoupling` (기존) |
| 2020-04 WTI < 0 | Cushing 저장 한계 | super-contango, 저장가동률>80%, negative time spread | `storage_limit_constraint` (★신규 H9) |
| 2022 nickel | 집중 숏 squeeze + LME 거래취소 | 극단 backwardation, top-4 trader %↑, vol 폭발 | `oi_collapse_in_uptrend` (신규) |

**5 신규 flag (블록5 confidence_hooks)**:
1. `term_structure_z_extreme` (|contango/backwardation| > threshold) — storage stress
2. `physical_storage_limit` (Cushing 가동률 > 85%) — 2020 negative price
3. `cot_concentration_squeeze` (top-4 trader %, MM net z > 95pct) — nickel-type
4. `cross_asset_corr_spike + funding_stress` (TED/FRA-OIS) — 2008-type deleveraging
5. `vol_regime_shift` — 이미 e-CUSUM 보유

---

## §7. 가장 먼저 반영할 두 가지 (claude R3 강조)

1. **H5≠H8 분리** — financialization measure 를 MM(speculator) 에서 **CIT (index trader)** 로 재배치. Tang-Xiong 원리 보존.
2. **Kilian 2009 oil-shock 분해** — H7 raw threshold 를 SVAR source-conditional 로 확장. Q3(b) energy↔equity 부호 결정.

이 둘이 ②검증방향 + ③가설초안의 가장 큰 변경.

---

## §8. 미해결 결정 (main 승인 대상)

main(btn-Codlearn) 에게 다음 사항 승인/조정 요청:

1. **가설 11개 전부 채택? 일부 폐기?** — 특히 H6 (USDA expectation 데이터 hardest) 와 H11 (Phase 3 kill switch) 의 우선순위 확정
2. **Phase 1 최우선 3가설 (H1+H5-outcome+H4) 으로 2-3단계 진입 동의?** — Phase 2/3 는 collector 구축 일정 따라 후순위
3. **Collector ranking 확정?** — DFII10 > CFTC > CME > EIA > NOAA > USDA. USDA WASDE 도입 보류?
4. **SLEEVE_BLOC 3-group (cyclical/defensive/idiosyncratic) 채택?** — 2x2 대칭 거부 확정
5. **Bai-Perron two-speed (quarterly + e-CUSUM) 채택?** — 신규 모듈 (bai_perron_breaks.py) 구현 승인?
6. **Look-ahead bias 차단 (ALFRED real-time vintage)** 추가 요구사항으로 확정? — 신규 collector 5개에 vintage_knowable_from 필드 의무?
7. **Kilian SVAR 분해 도입?** — 외부 라이브러리 (statsmodels VAR + structural identification 또는 별도) 필요
8. **자문 추가 라운드 필요?** — 본 작업방 판단 = 3R 수렴 충분. 그러나 main 이 R4 (예: Phase 2 collector spec 디테일) 추가 지시 가능

---

> ★STUDY-KIT §2-1 완료. main(btn-Codlearn) 승인 시 2-2 (이론 학습 → raw/theory-notes.md) 진입.
> 승인 전 2-2 금지 (KIT v2 §2-1 명시 게이트).
