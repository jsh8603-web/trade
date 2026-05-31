---
tags: [type/theory-notes, study/eq_us_cyclical, phase/2-2]
date: 2026-05-30
note: 2-2 산출(승인된 ①②③ 방향대로 정독·정리). 가격결정 원리 + 지표 의미·관계도 + 우리 시스템 코드화 매핑. 6 최상위 + 5 보완 + 1 비판적 자각(Investment Clock).
---

# theory-notes.md — eq_us_cyclical 이론학습 정리

> direction.md ① 최상위 6 + 보완 5 + 비판적 자각 1. 각 이론마다 (a)명제 (b)핵심 수식·관계 (c)우리 시스템 코드화 (d)함정. 경기민감주(equity.us cyclical) sub-panel 관점.

---

## A. 가격결정 원리 — Master Equation

경기민감주 가격 = 멀티플 M × 정상화 이익 E_norm × 사이클 조정 C.

```
P_t = M_norm(r_e, g, normalized_ROE) × E_t^norm × C(regime, capital_cycle, credit_cycle)
```

- **M_norm**: 펀더멘털만으로 산출한 정당화 배수 (스팟 멀티플 미포함, 동어반복 차단). `M_norm = (1-g/ROE_norm)/(r_e-g)` with `g ≤ 명목 GDP`.
- **E_t^norm**: 정상화 이익 = 중기 정상화 마진 × 추세매출. 사이클 마진성·구조 매출성장 분리.
- **C**: regime modulation. 4국면(Reflation/Recovery/Overheat/Slowdown) 또는 2국면(확장/수축).

**왜 경기민감주에 사이클이 핵심인가**: 매출(GDP/산업생산 탄력) + 영업레버리지(DOL) + 재무레버리지(DFL) 3중 증폭 → 이익이 GDP 진폭의 3-5배 진폭. peak에 이익이 정점이고 trough에 이익이 붕괴. **스팟 P/E를 그대로 쓰면 정점에서 멀티플 낮고 바닥에서 멀티플 높은 역설 → peak_trap의 원인 그 자체**.

---

## B. 최상위 이론 6 (시스템 골격 결정)

### B1. Damodaran — Valuation of Cyclical Companies
**출처**: Damodaran, *Investment Valuation* (3rd ed., 2012, Wiley); "Ups and Downs: Valuing Cyclical and Commodity Companies" (NYU Stern working paper, 2009).

**(a) 명제**: 사이클 종목은 스팟 펀더(매출·이익·마진)가 사이클 위치에 따라 극단 변동 → **정상화(normalize)** 후 가치평가해야 한다. 정상화의 본질 = 사이클(cyclical) 성분과 구조(structural) 성분 분리.

**(b) 핵심 수식·관계**:
1. **정상화 이익**: 정상화 마진 회귀가 표준.
   ```
   E_t^norm = (mid-cycle EBIT margin × 추세 매출_t) × (1 - 세율_normal)
   추세 매출 = OLS or Hodrick-Prescott(매출_t) 추세 성분
   mid-cycle margin = 섹터 7-10년 평균 EBIT/매출 (침체 1회 강제 포함)
   ```
2. **정당화 배수**: Gordon 형태, 펀더멘털만.
   ```
   M_norm = P/E_norm = (1 - g/ROE_norm) / (r_e - g)
   ```
   - `ROE_norm`: 정상화 ROE = 종목 자체 평균 + 섹터 평균 credibility weighting `ω = n_own/(n_own + k)`, k = 섹터간분산/종목내분산.
   - `r_e`: 자본비용 = **bottom-up beta** (산업 무차입 베타 → 종목 D/E relever) × **Damodaran implied ERP** (월별 vintage).
   - `g`: 지속가능 성장률 = `min(ROE_norm·(1-b), 장기 명목 GDP 3.5-4%)` — Damodaran stable-growth cap.
3. **음 ROE 처리**: ROE를 직접 정상화하지 말고 **operating margin을 정상화 → 자산회전율 × 레버리지로 ROE 재구성**.

**(c) 우리 시스템 코드화**:
- 블록2 indicators: `fwd_ep_normalized` (id) family=valuation is_core=true (★스팟 fwd_ep 대체 또는 보완). transform=own_history_z. source = EDGAR 펀더 + Damodaran implied ERP + FRED GDP cap.
- 블록3 relationships: `normalized E/P → forward 12M return` (direct, pos, conditioning on regime).
- 블록4 weight_rules: fwd_ep_normalized base 0.28, modulate_by [regime, industry], "trough → valuation 가중 추가↑(peak_trap 차단). peak → 진입 자제".
- 블록7 code_change_plan card: `core/assume/weight_card.py` fair_mult 입력 노드 추가 + (r-g)≥2% guardrail + Monte Carlo Band 산출 모듈 신규.

**(d) 함정**:
- **항등식 함정**: `g = ROE·b` 대입하면 `M_norm = (1-b)/(r-g) = payout/(r-g)`로 항등식 회귀, H10 동어반복 다른 형태로 부활. **g는 별도 GDP 앵커로 강제 차단** (Gordon "내부 일관성" 포기 정당).
- **(r-g) → 0**: 분모 폭주, 50bp 변화가 배수 30-50% 흔듦. (r-g) ≥ 2% 코드 guardrail 강제.
- bottom-up beta가 회귀 베타보다 PIT-safe하나 산업 분류 부정확하면 오염 — GICS 정확 라벨 필요.

---

### B2. Edward Chancellor — Capital Cycle Theory
**출처**: Chancellor (ed.), *Capital Returns: Investing Through the Capital Cycle* (Palgrave Macmillan, 2015). Marathon Asset Management 케이스 모음.

**(a) 명제**: 산업 수익성↑ → 신규 capex 유입 → 공급 과잉 → 수익성 파괴. 사이클 후반 capex 과열 = peak 신호. **자본의 양(공급) 측면이 수요 측면보다 더 신뢰할 만한 미래 수익률 예측자**.

**(b) 핵심 관계도**:
```
산업 수익성 high ROIC
        ↓ (자본 유입 자극)
    capex 가속 (자체 + 신규 진입자)
        ↓ (생산능력 확장 lag 2-3년)
    공급 과잉
        ↓
    가격 압박 + 마진 붕괴
        ↓
    수익성 회복 (생존자만)
```
**경기민감 섹터별 사이클 길이**: 반도체 ~3-4년, 에너지 ~5-7년, 해운 ~10년, 광업 ~10-15년. 사이클 길수록 capex 과열 검출이 더 명확.

**(c) 우리 시스템 코드화**:
- 블록2 indicators: `capex_to_rev` (already added), `industry_capex_growth_qoq` (산업 총 capex 변화율), `installed_capacity_to_demand`.
- 블록3 relationships: `industry_capex_growth → t+(6~12M) industry_margin` (direct, lagged, neg, prior 0.6). 산업 단위 분해 필수.
- 블록4 weight_rules: industry-level. "산업 capex 과열 분위(상위 20%) → 해당 산업 진입 자제 또는 short bias".
- 블록5 confidence_hook: hypothesis_id=capital_cycle_peak_overcapex, confirm/reject signal 코드화.

**(d) 함정**:
- 사이클 길이가 산업마다 다름 → 단일 lookback 무력. 산업별 lookback 캘리브레이션 필요.
- 신규 진입자(외국 자본) 미포함 시 capacity 추정 누락 — Chancellor가 강조하는 "글로벌 공급" 관점.
- M&A로 capacity 통합 시 capex 신호 왜곡 (구조조정으로 공급 감소).

---

### B3. Asset Growth Anomaly (CMA family)
**출처**: Cooper, Gulen, Schill (2008), "Asset Growth and the Cross-Section of Stock Returns", *Journal of Finance* 63(4); Titman, Wei, Xie (2004), "Capital Investments and Stock Returns", *JFQA* 39(4). Fama-French 5-factor (2015)의 CMA(Conservative Minus Aggressive).

**(a) 명제**: 총자산 성장률 상위 그룹 = 미래 수익률 저조. **Capital Cycle의 학술적 정본**(Chancellor의 정성을 통계로 입증). 메커니즘 = (i) Q-theory: 자본 한계수익 체감 (ii) 과잉투자 행태(empire-building) (iii) 회계 보수주의 사후 발견.

**(b) 핵심 수식**:
```
AG_it = (Assets_it - Assets_i,t-1) / Assets_i,t-1
횡단 분위 분해: AG decile 1 (low) - AG decile 10 (high) → 양의 spread (annual ~5-9%)
```
CMA 팩터 = AG low - AG high 매월 long-short.

**(c) 우리 시스템 코드화**:
- 블록2 indicators: `asset_growth_yoy` family=quality is_core=false (CMA proxy).
- 블록3 relationships: `asset_growth_yoy → fwd 12M return` (direct, lagged 12M, neg, prior 0.65).
- 블록4 weight_rules: 음부호 가중, sleeve 또는 industry granularity, regime modulate (Overheat 국면 가중 강화).
- H9 검증: 반도체 밖 multi-sector OOS Rank-IC ≥ 0 (음 IC 단조)이면 CMA 확정.

**(d) 함정**:
- 작은 종목 + 책상 가치 회사가 anomaly 결과를 견인 — value-weighted vs equal-weighted 차이.
- M&A로 자산 급증 시 자기 capex 아닌데 신호로 잡힘.
- recent decade에서 anomaly 약화 (Fama-French 2015 보완 후 더 약함) → factor crowding 의심.

---

### B4. Excess Bond Premium (EBP) — Gilchrist-Zakrajšek
**출처**: Gilchrist, Zakrajšek (2012), "Credit Spreads and Business Cycle Fluctuations", *American Economic Review* 102(4). 후속: Favara, Gilchrist, Lewis, Zakrajšek (2016 FEDS Notes) GZ 지표 갱신.

**(a) 명제**: 회사채 스프레드를 (i) 기대 디폴트 손실 (ii) 신용위험 프리미엄(EBP)으로 분해할 때, **EBP는 거시 사이클 선행성이 단순 OAS보다 훨씬 강함**. EBP 확대 = 향후 4-8 분기 GDP·산업생산 둔화 강력 예측.

**(b) 핵심 산출 (정공법)**:
1. 채권별 duration-matched 국채 대비 스프레드 S_ijt.
2. `log(S_ijt) = α + β·Merton_DD_it + γ·Bond_chars_jt + firm_FE_i + time_FE_t + ε_ijt`
   - Merton DD = distance-to-default = log(V_assets/D) / σ_V (Black-Scholes 기반).
   - Bond_chars = duration, coupon, age, rating, callability, 유동성.
3. EBP_t = ε_ijt 잔차의 횡단평균. (default risk로 설명 안 되는 부분.)

**빈자판** (TRACE/issuer 펀더 부재 시): `HY OAS (BAMLH0A0HYM2) ~ 기대디폴트율 proxy(BAA-AAA spread) + VIX(VIXCLS)` 회귀 잔차. 정확성 열등.

**(c) 우리 시스템 코드화**:
- 블록2 indicators: `ebp_residual` family=macro_driver is_core=true. source = 자체 산출(빈자판) → 후속 정공법 적재.
- 블록3 relationships: `ebp_residual → fwd_4-8Q cyclical excess return` (direct, lagged, neg, prior 0.7). 다른 거시 변수와 partial-corr.
- 블록4 weight_rules: `credit_beta` modulate by EBP 상태. "EBP 확대 국면 → cyclical 비중 축소, defensive 로테이션".
- 블록5: H4 hypothesis_id=ebp_common_cause. **★전략적 가지치기**: EBP 검증 결과로 H3·H5 일부 파생 트리 결정.

**(d) 함정**:
- Merton DD 산출은 issuer 주식 변동성·자본구조 필요 → EDGAR + 주가 결합 정교한 적재.
- 빈자판은 디폴트 위험 제거가 부정확 — "default-adjusted residual"이라 부르기 곤란.
- EBP 자체가 monetary policy 변화에 민감 (Fed BS expansion 시 EBP 인위 감소).

---

### B5. Grinold-Kahn Fundamental Law of Active Management
**출처**: Grinold (1989), "The Fundamental Law of Active Management", *Journal of Portfolio Management* 15(3); Grinold, Kahn, *Active Portfolio Management* (2nd ed., 2000, McGraw-Hill); Clarke, de Silva, Thorley (2002), "Portfolio Constraints and the Fundamental Law of Active Management", *Financial Analysts Journal* 58(5).

**(a) 명제**: 액티브 성과(Information Ratio) = 신호 품질(IC) × 베팅 수의 제곱근(√breadth) × 제약하 효율(Transfer Coefficient).

**(b) 핵심 수식**:
```
IR = IC × √breadth × TC
breadth_effective = N / [1 + (N-1)·ρ̄]    (Choueifaty-Coignard 2008)
TC = corr(actual weights, unconstrained optimal weights)
```
- IC: 신호의 정보계수(Rank-IC, Pearson IC).
- √breadth: 독립 베팅 수. **N=40 반도체에 ρ̄≈0.5 → breadth_eff≈2, √breadth_eff≈1.4** (★ 40종목이 실질 1.4 베팅).
- TC: 제약(turnover, weight cap, sector neutral 등)이 IC를 IR로 옮기는 효율.

**(c) 우리 시스템 코드화**:
- 블록4 weight_rules: cap=0.40 (현재) → TC 측정 후 캘리브레이션. cap 너무 작으면 TC↓.
- 블록5 confidence_metric: IC만 보지 말고 **IC × √breadth_eff × TC = expected IR** 산출. 라이브 IR < 0.5 면 신호 자체 의문.
- 블록7 weight_card.derive_weights에 breadth_eff 산출 추가 (호출자 횡단 ρ̄ 측정 입력).

**(d) 함정**:
- ρ̄ 시변 (위기 시 → 1) → breadth_eff 위기 시 붕괴. rolling 측정 필수.
- 섹터 추가 ≠ breadth 증가 (공통 사이클 공변). multi-sector 확장 시 effective_breadth 별도 측정.
- TC는 측정 어려움 (실제 weight vs 가상 unconstrained). 백테스트 후행 추정.

---

### B6. Markov-switching + BOCD — Regime Identification
**출처**: Hamilton (1989), "A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle", *Econometrica* 57(2); Adams, MacKay (2007), "Bayesian Online Changepoint Detection", arxiv 0710.3742.

**(a) 명제**:
- **Hamilton MS**: 경제 시계열의 평균·분산이 잠재 regime S_t (이산, Markov chain)에 의존 → 관측 데이터에서 regime 확률 P(S_t|·) 추출.
- **BOCD**: run-length r_t(현 segment 시작 후 경과) 사후확률을 온라인 업데이트 → break-point 실시간 탐지. **반복되는 4국면 분류 X** (segment 탐지만).

**(b) 핵심 수식 (Hamilton filtered vs predicted)**:
```
filtered: π_{t|t}(s) = P(S_t=s | y_{1:t})  ← y_t 포함 → b(t) NOT predictable
predicted: π_{t|t-1}(s) = π_{t-1|t-1}·P    ← y_t 미포함 → b(t) predictable ✓
```
★ **mixture e-process supermartingale 보존엔 predicted prob 필수**. filtered를 belief로 쓰면 martingale 깨짐.

**(c) 우리 시스템 코드화**:
- 블록2 indicators (regime input): T10Y2Y + EBP + ISM proxy (SOI/AMTMNO) + DTWEXBGS — 3-4개 절제.
- 블록7 brain/regime_classifier.py: filtered HMM 대신 **predicted prob 산출 경로 추가**. b(t) = π_{t-1|t-1}·P 로 적재.
- 블록7 weight_card.belief_vector: predicted prob 동결 (decision 시점 frozen, replay 보장).
- 룰베이스 BMA를 주(primary), HMM 교차검증, BOCD break-overlay로 계층.

**(d) 함정**:
- **label-switching**: regime 라벨이 라이브에서 뒤바뀜 → 평균성장률 순서제약 고정(예: regime 0 mean ≤ regime 1 mean).
- 파라미터(전이행렬·평균·분산) 전표본 추정 = 미래 누설. **expanding window 재추정 필수**.
- BOCD는 recurring 4국면 매핑 불가 → break 알람으로만.
- CFNAI × HMM 이중 평활화 (CFNAI 이미 차원축소된 지표) → 원천 M3 직접.

---

## C. 보완 이론 5

### C1. Fama-French + Carhart + QMJ
**출처**: Fama-French (1993) 3-factor *JFE* 33(1); Fama-French (2015) 5-factor *JFE* 116(1); Carhart (1997) momentum *JF* 52(1); Asness, Frazzini, Pedersen (2019), "Quality Minus Junk", *Review of Accounting Studies* 24(1).

**(a) 명제**: 횡단 평균수익 변동의 80%가 5팩터(market, size, value, profitability, investment) + momentum + quality로 설명. **알파 주장 시 이 팩터들로 통제(neutralize)** 필수.

**(b) 우리 시스템 코드화**:
- 블록2 indicators 일부와 직접 매핑: HML(value) ≈ fwd_ep, MOM ≈ price_mom_12_1, CMA(investment) ≈ asset_growth_yoy/capex_to_rev.
- 블록5 confidence_hook: 신호 알파 검정 시 FF5+MOM 회귀 잔차로 측정.
- ★ **QMJ + 초기 회복기 정크 랠리**: trough/early-recovery에서 quality 음 알파(저품질 경기민감주 랠리) → H1·H6 검증 시 quality 교호항 필수.

**(d) 함정**: Ken French 데이터는 미국·월간·일부 분기로 PIT 정확하나 종목 단위 적용 시 산업 분류 차이.

---

### C2. Yield Curve Inversion — Estrella-Mishkin
**출처**: Estrella, Mishkin (1998), "Predicting U.S. Recessions: Financial Variables as Leading Indicators", *Review of Economics and Statistics* 80(1).

**(a) 명제**: 10Y-2Y 또는 10Y-3M 역전 → 12-18개월 후 NBER 침체 확률 logit 추정. ★ **모든 거시 변수 중 침체 선행성 최강**.

**(b) 핵심**:
```
P(recession_{t+12}) = Φ(α + β · (10Y-3M)_t)
β < 0 (음의 spread → 침체 확률↑)
1968-2024년 미국 침체 9회 중 8회 사전 역전 (false positive 1회 = 1966)
```

**(c) 우리 시스템 코드화**:
- 블록2: `yield_curve_10y_2y` (already in v1) — regime input 필수.
- 블록3: `yield_curve → 12M 후 recession_prob` (direct, lagged 12M, neg).
- 블록4: 역전 진입 시 cyclical 비중 점진 축소 (12-18M lag 인지).

**(d) 함정**: 정책 왜곡(Fed QE, YCC) 시 spread 신호 약화. 2008-2014 zero-bound, 2020-2022 QE 무력화 가능. 최근 사이클에서 false positive 위험.

---

### C3. Operating Leverage — Novy-Marx
**출처**: Novy-Marx (2011), "Operating Leverage", *Review of Finance* 15(1).

**(a) 명제**: 고정비 비중(fixed costs / total costs) 높은 종목 = 매출 변동에 EPS 베타 증폭. 교과서 DOL(Brealey-Myers)은 산식만, Novy-Marx는 **횡단 alpha** 실증.

**(b) 핵심 수식**:
```
DOL = ΔEBIT/ΔRevenue  (시계열 elasticity)
Novy-Marx proxy = fixed_costs / book_assets (재무제표 항목 → 인건비·감가상각·R&D 등 추정)
high-DOL portfolio 평균 알파 ≈ +4%/년 (1962-2008)
```

**(c) 우리 시스템 코드화**:
- 블록2: `operating_leverage` family=quality. ★ **gross_margin은 약한 proxy** (v1 검증 IC +0.084 약함) — Novy-Marx 본 proxy(fixed_costs/total_costs) 적용 필요.
- 블록3: `operating_leverage × revenue_growth_yoy → t+1 EPS growth` (교호항, direct, lagged, pos).
- 블록5: H7 reject 후보 (proxy 무효 가능, |corr(margin, DOL)|<0.3이면 보류).

**(d) 함정**: 고정비/변동비 분해가 EDGAR 재무에서 깨끗치 않음. R&D를 고정 vs 변동으로 보는 회계 처리 차이.

---

### C4. PEAD / Revision Breadth
**출처**: Bernard, Thomas (1989), "Post-Earnings-Announcement Drift", *JAR* 27 Suppl.; Chan, Jegadeesh, Lakonishok (1996), "Momentum Strategies", *JF* 51(5); Womack (1996), "Do Brokerage Analysts' Recommendations Have Investment Value?", *JF* 51(1).

**(a) 명제**:
- **PEAD**: 어닝 서프라이즈 후 가격 drift 60-90일 지속 (분명한 inefficiency).
- **Revision breadth**: 컨센서스 EPS revision의 (상향 - 하향) 비율 = 다음 분기 수익률 선행. 국면전환에서 turning-point alpha.

**(b) 우리 시스템 코드화**:
- 블록2: `earnings_revision_breadth` (already in v1) family=revision is_core=true. **★IBES 가용 불가 → FINNHUB 무료 또는 8-K 가이던스 파싱**.
- 블록3: `revision_breadth → fwd 1-3M return` (direct, lagged 1M, pos, prior 0.55).
- 블록4: Recovery 초입 가중↑.
- H8 보류: 데이터 가용 X로 2-3 단계 단기 검증 불가.

**(d) 함정**: 컨센서스 데이터 라이선스 비용. 무료 대체(yahoo earnings) 커버리지 불완전.

---

### C5. Damodaran Implied ERP (vintage)
**출처**: Damodaran, *Equity Risk Premiums: Determinants, Estimation and Implications* (NYU Stern, 매년 갱신).

**(a) 명제**: ERP를 historical 5% 고정으로 쓰면 **위기 시(주가 폭락 → 기대수익 상승) ERP가 오히려 낮게 잡히는 치명적 오류**. Damodaran은 implied ERP를 매월 산출·공표.

**(b) 핵심**:
```
S&P 500 = Σ_t (Expected Dividends_t / (1+r)^t)
implied r = S&P 500 가격이 정확히 시장 ≈ 추정 미래 배당과 일치하는 r
implied ERP = implied r - 10Y T-yield
```
역사적: 1961-2024 implied ERP 평균 ≈ 4.1%, 2008-Q4 폭등 ≈ 6.5%.

**(c) 우리 시스템 코드화**:
- 블록2: `damodaran_implied_erp` family=macro_driver is_core=false, source=Damodaran 월별 적재 (블록6 collector_plan).
- 블록7 weight_card fair_mult 입력: r_e = r_f + β_bottomup × implied_ERP.

**(d) 함정**: vintage 정렬. Damodaran 월말 산출 → t+1 영업일 발표 lag 인지.

---

## D. 비판적 자각 — Investment Clock
**출처**: Greetham, Hartnett (2004), "The Investment Clock: Special Report", Merrill Lynch.

**(a) 명제**: 성장(PMI) × 인플레이션(CPI) 2×2 매트릭스로 4국면 분류 → 자산군별 우위 (Reflation: 채권/duration / Recovery: 주식/cyclical / Overheat: 원자재 / Stagflation: 현금/금).

**(b) 자각 — ground truth 금지**:
- ★ **단일 휴리스틱이지 검증된 통계 모델 X**. ML 자체 백테스트도 표본 짧고 데이터 선택 후행.
- 4국면 정의가 ad-hoc (PMI/CPI 둘 다 50/연 2% 단순 컷오프).
- 다른 매크로 패러다임(monetary regime, secular bull/bear, China growth dependence) 무시.
- **가설 생성기로만 사용**: H2(val↔mom 위상교차), 블록1 lens regime_reading의 정성 anchor. 검정은 별도(H1·H6·H4·H5·H3 데이터로).

**(c) 우리 시스템 코드화**:
- 블록1 lens.regime_reading: Investment Clock 4국면 명시하되 "ground truth 아님, regime BMA/HMM 산출 우선" 주석.
- 블록7 regime_classifier: Investment Clock 룰을 룰베이스 BMA의 한 모델로만 (다른 후보 = NBER probit, ISM-기반 binary 등과 BMA 앙상블).

---

## E. 관계도 (지표 의미 — direction.md 통합)

```
[규모 거시 driver]                          [경기민감 종목 펀더]
─────────────────────                       ─────────────────────
T10Y2Y (Estrella-Mishkin) ──────┐
ISM SOI / AMTMNO (선행)         │
EBP (GZ 2012, 공통원인)         ├──→ regime BMA/HMM ──→ predicted prob b(t)
DTWEXBGS                        │       │                       │
VIX (스트레스 augment)──────────┘       │                       │
                                        ↓                       ↓
                            cyclical-defensive    delta_regime (2국면 group + 4국면 shrinkage overlay)
                            상대수익 lead-lag              │
                                                            ↓
                                              composed_weights(pi, regime, archetype)
                                                            │
                                                            ↓
[종목 펀더]                                  S_L1 = clamp_floor(Σ w_i z_i)
─────────────                                            │
fwd_ep_normalized (Damodaran) ───→ z_fwd_ep              │
asset_growth_yoy (Cooper-Gulen-Schill) → z_AG           ↓
operating_leverage (Novy-Marx) ──→ z_DOL            judge.py
revision_breadth (PEAD) ─────────→ z_rev          (LLM down-only attenuation, lens 주입)
realized_vol ────────────────────→ z_vol                 │
rate_beta / oil_beta / credit_beta → z_macro            ↓
                                                  final = S_L1 × a2 × a3
                                                  (천장 불변식: final ≤ S_L1)
```

---

## F. 2-2 → 2-3 인계
- 2-3 우선순위: H1(정상화 E/P trough) + H6(peak_trap, H1과 쌍) + H4(EBP 공통원인) + H5(rate_beta name-specific) + H3(ISM 선행).
- 데이터 적재 필요: EDGAR 펀더(ROE·매출·자산), FRED(T10Y2Y, BAMLH0A0HYM2, VIXCLS, DGS10, AMTMNO, BUSINV, CFNAI subindex via ALFRED), Damodaran implied ERP 월별.
- 데이터 가용성 점검 후 가용한 만큼 라이브 검증 진행, 부재한 자료는 블록6 collector_plan으로 누적.
- ★합성 픽스처(semiconductor_panel_v1.parquet)는 v1 분석 한계 인정 — 실 multi-sector로 재검증 의도.
