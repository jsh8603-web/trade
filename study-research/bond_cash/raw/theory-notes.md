---
tags: [type/theory-notes, domain/inv, asset/bond, asset/cash, phase/study-2-2]
date: 2026-05-30
study_id: bond_cash
note: STUDY-KIT v2 §2-2 산출 — 이론 정독·정리. direction.md 승인 방향(A~G) 기반.
source: direction.md ①이론 수집방향 + raw/round-{1..5}.md (URL 46건)
review-by-main: HY OAS / yield curve / BAA10Y 가 macro / eq_us_defensive 와 겹침 → §8 정합 섹션
---

# bond_cash 이론 노트 (2-2 산출)

> direction.md 승인된 ①이론 수집방향 A~G 를 본 문서로 정독·정리.
> §8 = main 검토 요구사항: macro / eq_us_defensive 와의 driver 중복정의 회피·정합.

---

## §1. 채권 가격결정 1차 원리 (R1 정제)

### 1-1. Return 분해 (3-항)
한 채권의 일별 return 은 세 항으로 분해된다:

```
ΔP/P  ≈  -D·Δy  +  0.5·C·(Δy)²  +  carry
        ─────────  ──────────────  ──────
         duration   convexity       carry
         (1차 선형)  (2차 비선형)    (쿠폰+roll-down)
```

| 항 | 의미 | 부호 | 크기 결정 요인 |
|---|---|:---:|---|
| Duration term | yield 변동에 대한 1차 가격민감도 | y↑이면 P↓ (음) | D = 가중평균 만기 |
| Convexity term | 비선형 보정. 항상 양수 (positive convexity) | + (양수, 투자자 우호) | C ≈ D² (zero-coupon) |
| Carry | 쿠폰 + roll-down (steep 커브 시 추가) | + (정상커브) | 쿠폰율 + 커브 기울기 |

**핵심 통찰**:
- **Asymmetric payoff**: y 가 -Δ 만큼 하락 → P 상승이, y 가 +Δ 만큼 상승 → P 하락보다 *크다* (convexity gain)
- → yield volatility 가 클수록 expected return 이 *커진다* (convexity premium)
- → long-duration 채권일수록 convexity 가 크므로, 큰 yield shock 환경에서 더 유리할 수 있음 (단 1차 페널티가 압도하면 net 손실)

### 1-2. 듀레이션 정의
- **Macaulay duration**: 가중평균 만기 (= 현금흐름 시점의 PV 가중평균)
- **Modified duration** = Macaulay duration / (1 + y/n). **가격 변동의 % 표현** 시 사용
- **Effective duration**: option-embedded bond (callable 등) 에 사용. ΔP / (P·Δy) 의 수치 미분
- Zero-coupon: D = time-to-maturity, C = (maturity)²
- Coupon bond: cash-flow value-weighted

### 1-3. Fisher 분해 (회계항등)
```
nominal_yield  =  real_yield  +  expected_inflation  +  (small risk premium)
   DGS10       =    DFII10    +       T5YIE
```
- 실증: v1 raw 분석에서 Pearson(nominal, real+breakeven) = 0.9999 확인됨
- → **듀레이션 리스크 = real rate 변동에 대한 노출** 이 본체
- → **인플레 hedge = breakeven 변동에 대한 노출** = TIPS 의 본질
- 명목채는 (real + breakeven) 동시 노출 → Overheat (real↑+breakeven↑) 에서 double penalty

### 1-4. Credit Spread Duration
HY/IG 채권은 명목채 위에 **spread duration** 항이 추가:
```
ΔP_credit/P  ≈  -D_tsy · Δy_tsy   -  SD · Δspread   + carry
                  (treasury 항)      (credit 항)
```
- SD (spread duration) ≈ D_tsy (1:1 가산 근사)
- → spread widening 시 credit 채권은 1차 페널티 2회 (treasury yield + spread)
- → flight-to-quality 시: long Tsy 는 yield↓ rally, HY 는 spread↑ sell-off = **카운터-사이클**

---

## §2. 채권 분류 체계 (Duration × Credit)

### 2-1. 2축 분류
```
              Duration (만기)
       Short      Mid       Long
       (≤3Y)     (3-10Y)    (10Y+)
  ┌──────────┬──────────┬──────────┐
  │  BIL     │   IEF    │   TLT    │  Tsy (AAA)
  │  SHV     │          │   TLH    │
  │  SHY     │          │   EDV    │
  ├──────────┼──────────┼──────────┤
  │          │   LQD    │          │  IG (A-/BBB+)
  ├──────────┼──────────┼──────────┤
  │          │  HYG     │  (HY 장기 거의 없음)  │  HY (B+/BB)
  │          │  JNK     │          │
  └──────────┴──────────┴──────────┘
  + TIPS 행: STIP(short), VTIP(mid), TIP(long)
  + Cash:   MMF, 직접 T-Bill (1-3M)
```

### 2-2. 부록 B Hierarchical Pooling 적용
ETF 단위 학습은 obs 부족 → archetype shrinkage:
```
종목(ETF) 가중  =  w_global  +  δ_regime  +  δ_arch(duration_bucket)  +  ticker_shrinkage
```
- archetype `duration_bucket` ∈ {long, mid, short, cash_like}
- soft membership (`delta_arch_by_type`):
  - TLT = {long: 1.0}
  - IEF = {mid: 0.7, long: 0.3}
  - SHY = {short: 1.0}
  - BIL = {cash_like: 1.0}
  - HYG = {mid: 1.0, +credit_quality=HY}
- → ETF 마다 hard 한 single bucket 강제 X, soft membership 으로 보간

---

## §3. Investment Clock × 채권 거동 (R2 정제)

### 3-1. 4국면 표 (성장 × 인플레)

| 국면 | 성장 | 인플레 | 우위 자산 | 명목채(Bond) | TIPS | Cash | HY 신용 |
|------|:---:|:---:|---|---|---|---|---|
| **Reflation** | ↓ | ↓ | **Bond** | **TOP** (real rate↓ + 정책완화) | neutral | neutral | 압축(carry 우위) |
| **Recovery** | ↑ | ↓ | **Stock** | down (금리정상화) | neutral | down | 압축 지속 |
| **Overheat** | ↑ | ↑ | **Commodity** | down (CB 인상) | **UP** (인플레 보호) | neutral~down | 균열 시작 |
| **Stagflation** | ↓ | ↑ | **Cash** | down (double penalty: 인플레+신용) | **UP** | **TOP** | 확대 (default 위험) |

### 3-2. 핵심 인용 (R2 원전)
- **Reflation**: "bonds are expected to be the most welcomed asset thanks to the generous monetary and fiscal support" (Richard L, Medium)
- **Overheat**: "Rising inflation spurs the central bank to hike rates, usually causing bond yields to increase. The bond market enters a bear market." (Richard L)
- **Stagflation**: "you normally see negative real returns from stocks and bonds and commodities are your saviour" (Dr Wealth)
- **TIPS 분리 채널**: "inflation-protected bonds outperform conventional bonds during Overheat and Stagflation" (RLAM)

### 3-3. 현재 코드 vs 본 표 차이
`core/brain/regime_to_weights.py L74~79`:
```python
REGIME_DIRECTION = {
    RegimeLabel.REFLATION:   {... "bond": "top",  "cash": "neutral", ...},  # ✅ 일치
    RegimeLabel.RECOVERY:    {... "bond": "down", "cash": "down",    ...},  # ✅ 일치
    RegimeLabel.OVERHEAT:    {... "bond": "down", "cash": "down",    ...},  # ⚠️ 본 표는 neutral~down
    RegimeLabel.STAGFLATION: {... "bond": "down", "cash": "top",     ...},  # ✅ 일치
}
```
- ⚠️ **OVERHEAT 의 cash = "down"** 은 R5 Duffee fact ("5Y 이하 Tsy Sharpe > SPY") 와 약간 모순
- → 가설 #5 (`cash_sharpe_competitive`) 검증 결과로 동적 보정 (블록5 cash_optionality_value hook)

### 3-4. TIPS 분리 archetype 필요성
- 현재: bond sleeve = 명목채 + TIPS 혼재 (단일 카드)
- 제안: bond sleeve 안에 sub-archetype `nominal_duration` vs `real_duration` (TIPS) 분리
- → Overheat·Stagflation 국면 분기 시 TIPS 가중↑ 자동 처리 (modulate_by 에 `inflation_regime` 추가)
- → main 의사결정 사항 (direction.md ★요청 #2)

---

## §4. Credit Cycle — HY OAS (R3 정제)

### 4-1. 시계열 사양
- **BAMLH0A0HYM2** = ICE BofA US High Yield Index Option-Adjusted Spread
- 정의: below-investment-grade US corporate bonds 가 같은 만기 Treasury 대비 지불하는 daily 프리미엄
- 데이터: FRED 배포 1996-12 시작 (≈30년 historical)
- 현재 `fred_adapter.FRED_SERIES[BAMLH0A0HYM2]` 등록됨 ✅

### 4-2. 600 bps Threshold
- 1996-2024 분석: HY OAS ≥ 600 bps → 12-18개월 내 침체 발생 **~85%**
- 평시 분포: 평균 ~450 bps, std 200, normal regime 300-500 bps
- → Z-score 보다 *level threshold* 이 의미 있는 시그널

### 4-3. Credit Cycle Phase
| Phase | HY OAS 상태 | 매수 전략 | 우리 시스템 액션 |
|---|---|---|---|
| **압축 (carry)** | 좁고 안정 (300~400 bps) | 보유 → carry 수익 | base_weight 유지 |
| **확대 진행 (widening)** | 빠르게 확대 중 | 매도 (default 위험) | HY 가중↓ + long Tsy 가중↑ |
| **Peak (panic)** | 정점 (600 bps+, 1000+) | **Contrarian 매수** (15-25%/yr 2-3년) | HY 가중↑ |
| **회복 (normalization)** | 정상화 진행 | 보유 → spread 압축 capital gain | base_weight 회복 |

→ "highest-quality junk bonds purchased at peak spreads have historically delivered 15-25% annual returns over the subsequent 2-3 years" (Money365)

### 4-4. Multi-Signal Warning System
- 단일 HY OAS 보다 **3-signal 합성** 이 4-8개월 lead time 제공:
  1. HY OAS (credit risk)
  2. yield curve (10Y-2Y or 10Y-3M)
  3. VIX (주식 implied vol)
- → **VIX (FRED VIXCLS) collector_plan 추가 권고** (direction.md ★요청 #3)

---

## §5. Yield Curve 신호학 (R4 정제)

### 5-1. 역전 → 침체 lead time
- **평균 = 48주 ≈ 11개월** (역전 첫 음수 → 침체 시작)
- **IQR = 6-18개월**
- WWII 이후 모든 역전 → 6-18개월 내 침체 (단 false signal 도 1995, 1998)

### 5-2. Bull Steepening Event
- 역전 해소 (steepening back to positive) = **long-duration ETF 매수 시점**
- 2007-2009 사례: rate cut → "longer-term bond prices in iShares 10-20 Year Treasury Bond ETF (TLH)" 급등 → 커브 정상화
- 메커니즘:
  1. 침체 진입 → CB 가 rate cut
  2. 단기금리 (2Y) 급락 (Fed funds 따라)
  3. 장기금리 (10Y) 도 하락하나 단기보다 덜 → curve steepening
  4. 동시에 모든 만기 yield 하락 → long-duration 1차 페널티 *해소* + duration gain

### 5-3. Lag 신뢰성 한계
- "the relationship is not mechanical, as inversions are not precise timing tools and do not always precede recessions in a consistent way"
- → false signal: 1995, 1998 등
- → **anytime-valid e-process** (Ville 부등식) 로 false-positive 통제 필수
- → `score_ic_breakdown_eprocess` 의 alpha=0.05 임계

### 5-4. 우리 코드 매핑
- `T10Y2Y` 시리즈 → 부호 flip event 추출 → forward 6/12/18M panel
- `RECPROUSM156N` 침체확률 lag 통제 conditioning
- `CFNAI` 활동 통제 (lag 매개)

---

## §6. Cash Sleeve 정량 가치 (R5 정제)

### 6-1. Rate-Cut Optionality
- Short-T-Bill ETF (VGSH, SHV, BIL) = "Cash-Plus Carry With Rate-Cut Optionality"
- 메커니즘:
  - carry: 정책금리에 연동된 단기 yield (현재 4-5% 수준)
  - option value: Fed cut 발표 시 price appreciation (단기채 → 인하 후 새 단기금리 < 보유채 yield = capital gain)
- → cash 는 단순 *기회비용 최소화*가 아니라 **(carry + 조건부 option) 결합 자산**

### 6-2. Short-Tsy Sharpe (Duffee, JHU)
- 발견: "bond portfolio containing Treasury bonds with **less than five years to maturity** has a **monthly Sharpe ratio that slightly exceeds** the monthly Sharpe ratio of the stock market"
- → cash + short-Tsy 결합이 risk-adjusted 로 주식 sleeve 와 *경쟁력*
- → 우리 backtest 에서 가설 #5 (`cash_sharpe_competitive`) 로 재현 검증

### 6-3. Stagflation 방어
- Thrivent: "TIPS adjust with inflation, preserving purchasing power, and can work well as part of a stagflation defense strategy"
- 즉 Stagflation 방어 = **cash + TIPS 결합** (cash = nominal 보존, TIPS = real 보존)

### 6-4. T-Bill 공급량 외력
- Ainvest: "Surging short-term Treasury bill issuance is poised to flatten the yield curve"
- 정책요인 (적자/부채) 으로 T-Bill 공급 급증 → 단기금리 상승 → curve flatten → bond/cash 가격에 영향
- → **collector_plan 후보**: FRED Treasury bill outstanding 시리즈

---

## §7. KR 채권 / Fed Spillover (R5 정제, KR sleeve 확장 시)

### 7-1. KTB 3-Driver
ING THINK: KTB 시장은 다음 3 driver 가 핵심
1. **Fed rate cut** (외부 금리 anchor)
2. **BoK rate** (내부 정책)
3. **WGBI 편입** (외국인 자금 흐름 dummy)

→ KR sleeve 의 bond 부분은 us bond 의 단순 mirror 가 아님. 별도 driver 셋 필요.

### 7-2. Fed Spillover 비대칭
arXiv 2402.07266: "spillover effects are significantly amplified when US monetary policy tightening is accompanied by an increase in monetary policy uncertainty"
- 즉 Fed 인상 alone < Fed 인상 + EPU 상승 (compound shock)
- → **EPU index** (Baker-Bloom-Davis, FRED `USEPUINDXD`) collector_plan 후보

### 7-3. Dollar Liquidity Channel
BIS WP 1145: 달러 유동성 ↔ KTB 시장 유동성 직접 연결
- 메커니즘: 달러 funding stress → 외국인 KTB 매도
- → DXY 또는 cross-currency basis swap 이 KTB risk 채널
- → macro 방의 DXY 와 직접 공유 (본 방은 *수신*, 별도 추가 없음)

### 7-4. 최근 KR 상황 (2026-05)
- CNBC 2026-05-28: BoK 금리동결 + 인플레 전망 2.7% 상향 (oil spillover 반영)
- → KR 채권은 *국제* 인플레 spillover 에 노출 → 단순 한국 인플레만 모니터 부족

---

## §8. ★중복 driver 정합 (main 검토 요구)

### 8-1. 공유 driver 매핑 표

| Raw 시리즈 (SSOT) | macro 방 | eq_us_defensive 방 | bond_cash 방 | 충돌 여부 |
|---|---|---|---|:---:|
| **BAMLH0A0HYM2** (HY OAS) | `credit_spread_hy_oas` (regime 분류 입력, level) | `credit_beta` 회귀 베이스 (종목 vs HY OAS) | `credit_spread_hy_oas` + `credit_quality_id` modulate (sleeve forward driver) | ✅ 무충돌 (사용목적 분리) |
| **T10Y2Y** (yield curve) | `yield_10y_2y` (regime/transition) | (없음 — 거시 sensitivity 만) | `yield_10y_2y` (sleeve transition anchor) | ✅ 무충돌 |
| **BAA10Y** (IG spread) | `credit_spread_baa` (IG 보완) | `credit_beta` 보조 | `credit_spread_baa` (HY 보완) | ✅ 무충돌 |
| **T5YIE** (breakeven) | `breakeven_5y` (인플레 축) | (없음) | `breakeven_5y` (TIPS 분기축) | ✅ 무충돌 |
| **NFCI** | `nfci` (금융상황) | (없음) | `nfci` (위험 보조) | ✅ 무충돌 |
| **RECPROUSM156N** (침체확률) | `fred_recession_prob` (매개통제) | (없음) | `fred_recession_prob` (lag 통제) | ✅ 무충돌 |
| **CFNAI** | `cfnai` (성장축) | (없음) | (블록3 conditioning_set 용 참조만) | ✅ 무충돌 |
| **DFII10** (10Y TIPS = real rate) | `real_rate_10y` (분해축, 요청) | (없음) | `real_rate_10y` (듀레이션 본체, 요청) | ✅ **공통 요청** — main 통합 시 1회만 추가 |
| **DGS10/DGS2/FEDFUNDS** | (없음) | (없음) | bond_cash 신규 요청 | ✅ bond_cash 전용 |

### 8-2. 정합 원칙 (충돌 회피)

#### 원칙 1: Raw 시계열 SSOT 유일
- `fred_adapter.FRED_SERIES` dict 가 *유일한 SSOT*
- 같은 series_id 를 두 방에서 다른 이름으로 등록 금지
- main 이 통합 시 union 으로 단일 dict (중복 키는 한 번만)

#### 원칙 2: Indicator id 명명 일치
- 모든 방에서 같은 series → 같은 indicator id 사용
- 예: HY OAS → 모두 `credit_spread_hy_oas` (macro 방 명명 채택)
- bond_cash 방은 macro 명명 그대로 사용 ✅ (블록2 일관)

#### 원칙 3: 사용 목적 (family / 해석 layer) 다양화 허용
- 같은 raw 라도 **family** 가 다르면 OK:
  - macro 방: `family: macro_driver` (regime 라벨 입력)
  - eq_us_defensive: `family: macro_sensitivity` (종목 beta 계산용)
  - bond_cash 방: `family: macro_driver` (sleeve forward driver)
- → derivation pathway 가 다른 *derived* indicator 가 갈라짐
- → 블록3 relationships 의 conditioning_set 도 방마다 다름 (각 layer 의 partial-corr)

#### 원칙 4: weight_rules 의 영향 범위 분리
- macro 방: sleeve 간 배분 조절 (regime_to_weights 의 belief cov override)
- eq_us_defensive: 종목간 가중 (stock_track 의 _extract_indicator_z)
- bond_cash: sleeve 내부 ETF 가중 (etf_track 신설 or stock_track 분기 — direction.md ★요청 #4)
- → 같은 raw 가 *3 layer* 에서 동작. 충돌 X.

#### 원칙 5: Falsification 카드 ID 분리
- macro: `weight.macro.{regime}`, `weight.macro.transition`
- eq_us_defensive: `weight.equity.us.defensive.{regime|industry}`
- bond_cash: `weight.bond.{regime}`, `weight.cash.{regime}`, `weight.bond.credit`, `weight.bond.transition`, `weight.bond.carry`, `weight.cash.optionality`, `weight.bond.omega_drift`
- → 같은 raw 시그널의 신뢰도가 각 카드에서 독립적으로 갱신

### 8-3. 잠재 충돌 (해소 방안)

#### A. HY OAS 의 *역할 모순*
- macro: HY OAS Z↑ → Stagflation 분류 weight↑
- eq_us_defensive: HY OAS Z↑ → 방어주 *상대* outperform (+) **AND** 은행 provisioning Q+1~Q+2 lag (-)
- bond_cash: HY OAS Z↑ → HY 가중↓ + long Tsy 가중↑ (flight-to-quality)
- **해소**: 같은 signal 이 3 layer 에서 *합쳐서* 일관 (모두 risk-off 방향). 부호 모순 없음.

#### B. 자체 *내부* 모순 (eq_us_defensive 명시)
- eq_us_defensive 의 raw 인용: "방어주 *상대* outperform / 금융 provisioning Q+1~2 lag → 한 sleeve 내 정반대 부호"
- → sleeve 내부의 sub-industry (방어주 vs 은행) 분기로 해소 (그 방의 책임)
- → bond_cash 와는 무관

#### C. Curve 신호의 분기
- macro: curve 역전 = transition anchor (Recovery → 다음 국면)
- bond_cash: curve 역전 해소 = bull steepening = long-Tsy 매수 시점
- **해소**: macro 는 *언제 국면 바뀌나*, bond_cash 는 *언제 long-duration 매수하나* — 시간축에서 일관 (역전 해소 = Recovery 시작)

### 8-4. 통합 시 main 액션 체크리스트
1. ✅ `fred_adapter.FRED_SERIES` union — bond_cash 요청 6종 (DGS10/DGS2/DGS3MO/DFII10/FEDFUNDS/MORTGAGE30US) + macro 요청 DFII10 중복 → 1회만 추가
2. ✅ `credit_spread_hy_oas` indicator id = 단일 (블록2 일관)
3. ✅ 카드 id namespace 분리 (`weight.macro.*` ⊥ `weight.equity.*` ⊥ `weight.bond.*` ⊥ `weight.cash.*`)
4. ✅ corr_prior force-include 통합 — macro 의 (dxy~real_rate, dxy~gold 등) ⊥ bond_cash 의 (fed_funds~yield_2y, duration~yield_10y 등). 직교 → block-diagonal 결합
5. ❓ TIPS / VIX / EPU collector_plan 추가 — main 의사결정 (direction.md ★요청 #2~3)
6. ❓ etf_track 모듈 신설 vs stock_track 분기 — main 의사결정 (direction.md ★요청 #4)

---

## §9. 가격결정 관계도 (텍스트 다이어그램)

```
[정책 anchor]
    Fed Funds (FEDFUNDS) ─┐
                          ├──→  DGS2 (단기금리)
                          │        │
                          │        ↓ term structure expectations + term premium
                          │     DGS10 (장기금리)  ←─── 글로벌 자본 (JGB 금리차, 엔캐리)
                          │        │
                          │        ↓ Fisher 분해
                          │     ┌──┴──┐
                          │     │     │
                          │  DFII10  T5YIE
                          │ (real)  (breakeven)
                          │     │     │
                          │     ↓     ↓
                          │  ┌─────────────┐
                          │  │ 명목채 가격 │ ← Duration · Convexity · Carry
                          │  │  (TLT/IEF) │
                          │  └─────────────┘
                          │     │
                          │     ↓ (inflation expectations 분기)
                          │  ┌─────────────┐
                          │  │ TIPS 가격   │ ← Overheat·Stagflation 우위
                          │  │  (TIP/STIP) │
                          │  └─────────────┘
                          │
                          └──→  DGS3MO (T-Bill) ──→ Cash sleeve (BIL/SHV)
                                                    │
                                                    ↓ Rate-cut event optionality
                                                  price appreciation

[Credit 채널]
    HY OAS (BAMLH0A0HYM2) ──→ HYG/JNK 가격 = -D·Δy_tsy - SD·Δspread + carry
       │
       └──→ Multi-signal warning (with T10Y2Y + VIX) → recession lead 4-8M
       │
       └──→ Flight-to-quality (Z↑ 시점) → TLT 매수 (카운터-사이클)

[국면 분류 입력 — macro 방 출력]
    CFNAI (성장축) × T5YIE (인플레축) → Investment Clock 4국면
       │
       ↓ belief b(t)
    bond/cash sleeve 가중 (REGIME_DIRECTION 표)
       │
       ↓ within-sleeve
    duration bucket × credit quality 가중 (블록4 weight_rules)
       │
       ↓ ticker
    ETF soft membership (delta_arch_by_type)
```

---

## §10. 2-3 단계로 넘기는 검증 작업

direction.md ② 검증방향 1~8 그대로 + 가설 12개 (③). 추가로:
1. **§8 정합 검증**: macro / eq_us_defensive 와 indicator id 일치 + 같은 raw 시계열로 sanity check
2. **§3-4 TIPS archetype 검증**: TIP vs TLT 의 4국면별 누적 spread (Overheat/Stagflation 양수 검증)
3. **§6-2 Duffee 재현**: SHY+BIL+SHV 의 36M rolling Sharpe vs SPY 동일 윈도 (1976-2024)
4. **§4-2 600bps event study**: BAMLH0A0HYM2 ≥ 600 → forward 12-18M bond - cash spread 분포

→ validation-*.md 파일들 (2-3 산출) 로 분리.
