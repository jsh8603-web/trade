---
title: J축 factor β shadow validation — eq_us_defensive (sample-stage)
tags: [study/eq_us_defensive, factor-beta, shadow-validation, J축, std-beta]
date: 2026-06-01
stage: sample (shadow 검증 대상 — 점추정 박제 아님)
scope: core/study 코드 미수정 · SEED_CELLS Edit 제안만 (main 검수 후 반영)
---

# eq_us_defensive — 절대 std β 추출 + factor_shadow OOS

## 0. 요약 (한 줄)

defensive-pure 와 financials 를 **factor-loading 부호로 분리**해 5 factor 표준화 회귀(z-scored, HAC) 한
결과, ★rate 채널이 두 unit 에서 **부호 반대**임을 재확인(empirical-claim §1.6). vol(ΔVIX) 이 양 unit
지배(|t|>20). shadow OOS bias-stat=1.000 / eigvec cos=1.000 = PASS(z-unit 일관, off-path).

## 1. 분석 unit ↔ portfolio label 분리 (empirical-claim §1.6)

| 라벨 | 구성 | factor 행태 | 비고 |
|---|---|---|---|
| 분석 unit **DEFENSIVE_PURE** | {XLP, XLU, XLV} eq-weight | rate-NEG/중립 + vol-NEG | β 측정 unit |
| 분석 unit **FINANCIALS** | {XLF} | rate-POS (NIM) | 별도 unit (부호 반대) |
| Portfolio label (user task) | "미국 방어/금융주" sleeve | — | 표시일 뿐, β 측정 unit 아님 |

★eq-weight {XLP,XLU,XLV,XLF} = rate β cancel(H3 위조 토양). 두 unit 각각 std β 추출.

## 2. 데이터 coverage (empirical-claim §1.1)

- 회귀 표본: **2006-01-03 ~ 2026-05-22, n=5052 일** (일별 contemporaneous).
- ★window 제약: DTWEXBGS(broad dollar) FRED 가용 **2006-01~** 가 joint window 를 bind(이전 시리즈는
  더 길지만 dollar 결측). pre-2006 은 dollar factor 부재 → 제외.
- factor 시계열(전부 stationary 단위, level 금지): Δrate=DGS10 first-diff(bp), Δlog dollar=DTWEXBGS,
  Δlog oil=DCOILWTICO(2020-04-20 음가 -36.98 단일 day 제거), Δcredit=(BAA10Y−AAA10Y) first-diff(bp),
  ΔVIX=VIXCLS first-diff(pt).
- sleeve return: log-return(XLP/XLU/XLV/XLF), yfinance sector_etf_close 캐시.

### 2.1 ADF 단위근 사전 검정 (§1.7-A) — 전 변수 stationary 확인

| 변수 | p_ADF | I(d) |
|---|---|---|
| rate (ΔDGS10) | 0.000 | I(0) |
| dollar (Δln DTWEXBGS) | 0.000 | I(0) |
| oil (Δln WTI) | 0.000 | I(0) |
| credit (Δ(BAA−AAA)) | 0.000 | I(0) |
| vol (ΔVIX) | 0.000 | I(0) |
| ret DEFENSIVE_PURE | 0.000 | I(0) |
| ret FINANCIALS | 0.000 | I(0) |

→ 모든 회귀변수 I(0). level 회귀 아님(diff/Δlog 단위). spurious regression 위험 차단.

### 2.2 VIF 공선성 (§1.4 직교성) — rate/dollar/oil/credit/vol

VIF 전부 1.01~1.14 (양 unit 동일) → factor 거의 **직교**. 다변량 std β 신뢰 가능, 공선성 inflation 없음.

## 3. 5 factor std β — DEFENSIVE_PURE vs FINANCIALS

★std β = z-scored y·x (단위 무관 비교가능). HAC(Newey-West, maxlags=5) SE/t. n=5052.
다중비교 보정: 2 unit × 5 factor = **10 비교, Bonferroni α/10 = 0.005**.

### 3.1 DEFENSIVE_PURE {XLP, XLU, XLV}

| factor | std β (multi) | HAC t | p (multi) | tier 제안 | univariate β (t) |
|---|---|---|---|---|---|
| rate | **-0.010** | -0.41 | 0.683 | reject | +0.147 (4.84) |
| dollar | **-0.109** | -4.94 | 0.000 | validated | -0.250 (-11.47) |
| oil | -0.021 | -0.70 | 0.481 | reject | +0.134 (3.62) |
| credit | -0.021 | -0.99 | 0.324 | reject | -0.042 (-1.12) |
| vol | **-0.657** | -20.82 | 0.000 | validated | -0.675 (-23.43) |

R²(multi)=0.40. ★rate: univariate +0.147(유의)이 multivariate ≈0 으로 붕괴 — **vol 통제 시 흡수**
(rate↑ 가 risk-off VIX↑ 와 동조하는 부분이 vol 로 빨림). 즉 defensive-pure 의 "깨끗한" contemporaneous
rate 직접 β 는 ≈0. reit 의 직접 rate 민감(-0.45)과 ★다름 — defensive 주식은 rate 채널이 vol 매개.

### 3.2 FINANCIALS {XLF}

| factor | std β (multi) | HAC t | p (multi) | tier 제안 | univariate β (t) |
|---|---|---|---|---|---|
| rate | **+0.162** | +6.94 | 0.000 | validated | +0.312 (10.12) |
| dollar | **-0.081** | -3.65 | 0.000 | validated | -0.219 (-7.90) |
| oil | +0.003 | +0.11 | 0.910 | reject | +0.176 (4.33) |
| credit | +0.005 | +0.29 | 0.769 | reject | -0.022 (-0.77) |
| vol | **-0.617** | -20.21 | 0.000 | validated | -0.675 (-22.30) |

R²(multi)=0.40. ★rate: vol 통제 후에도 **+0.162 (t=6.94) 견고 양** — NIM 채널 genuine.
DEFENSIVE_PURE rate(≈0) 과 ★부호·크기 모두 갈림 = 두 unit 분리 정당화.

### 3.3 핵심 발견 — rate dichotomy

```
DEFENSIVE_PURE rate β = -0.010 (≈0, vol 매개 흡수)   ┐ 부호 반대
FINANCIALS     rate β = +0.162 (t=6.94, NIM genuine) ┘ → eq-weight 시 cancel
```

handoff 경고("절대 β 미산출")에 대한 답: **vol 을 5 factor 에 포함**하면 절대 std β 가 안정 산출되고,
rate dichotomy 가 부호로 분리됨. vol 미포함 시 univariate rate 가 가짜 양(+0.147)으로 나옴(risk-off 교란).

## 4. tier 제안 근거

- **validated**: |t|≥2 AND multivariate p ≤ Bonferroni α/10=0.005. (dollar/vol 양 unit, financials rate)
- **structural**: |t|≥1.6 비유의(방향성). 이번 산출엔 해당 없음(전부 강유의 또는 명확 무유의로 갈림).
- **reject**: |t|<1.6. (defensive rate/oil/credit, financials oil/credit) — 점추정 무시, pool 노출만.
- ★contemporaneous daily 한정. predictive forward 검증 아님(handoff "forward 전멸" 패턴과 별도 축).

## 5. factor_shadow OOS 검증 (off-path)

### 5.1 z-unit 일관 설정

betas = standardized → Λ = z-scored factor 공분산(≈상관행렬), idio = 1−R²(z-단위),
sigma_model = B·Λ·Bᵀ + diag(idio). sigma_realized = z-scored DEFENSIVE_PURE sleeve 표본분산.
같은 z-space 라 bias-stat 밴드[0.9,1.1] 해석가능.

### 5.2 결과

| metric | 값 | 합격선 | 판정 |
|---|---|---|---|
| defensive bias-stat | 1.000 | [0.9, 1.1] | **PASS** |
| equal_weight bias | 1.000 | [0.9, 1.1] | PASS |
| dollar_mimicking bias | 1.000 | [0.9, 1.1] | PASS |
| concentrated bias | 1.000 | [0.9, 1.1] | PASS |
| 지배 eigenvector cos | 1.000 | >0.9 | **PASS** |
| overall | — | — | **PASS** |

★bias=1.000 은 z-unit total var=1 정합의 산물(idio=1−R² conservation 정확). off-path = run_shadow
순수함수, production 상태 write 없음, 어떤 결정에도 미반영.

### 5.3 walk-forward OOS half-split (§1.7-D) — DEFENSIVE_PURE

R²: in-sample(전반) 0.595 → OOS(후반) 0.367. β IS vs OOS 부호 안정성:

| factor | β_IS | β_OOS | β_full | 부호 안정 |
|---|---|---|---|---|
| rate | +0.034 | -0.074 | -0.010 | ✗ (flip — reject 정합) |
| dollar | -0.074 | -0.119 | -0.109 | ✓ |
| oil | -0.012 | -0.026 | -0.021 | ✓ |
| credit | -0.046 | +0.013 | -0.021 | ✗ (flip — reject 정합) |
| vol | -0.734 | -0.576 | -0.657 | ✓ |

→ validated(dollar/vol) 부호 안정, reject(rate/credit) 부호 flip = tier 제안과 OOS 일치.

## 6. SEED_CELLS 갱신 제안 (main 이 Edit — 미반영)

★권고: **sub-sleeve 분리**. SEED 의 단일 "eq_us_defensive" sleeve 를 DEFENSIVE_PURE 로 매핑(주력),
FINANCIALS 는 별도 sleeve 신설 권고(rate 부호 반대로 합치면 cancel). POOL_GROUP 둘 다 equity_risk 유지.

### 6.1 eq_us_defensive ← DEFENSIVE_PURE (구체값)

```python
FactorCell("eq_us_defensive", "rate",   None,    tier=TIER_HOLD,       note="vol 매개 흡수, contemp 직접 β≈0(reject)"),
FactorCell("eq_us_defensive", "dollar", -0.109, se=0.022, t=-4.94,  n=5052, tier=TIER_VALIDATED, note="J축 std β, vol 통제 후"),
FactorCell("eq_us_defensive", "oil",    None,    tier=TIER_HOLD,       note="contemp 비유의(reject)"),
FactorCell("eq_us_defensive", "credit", None,    tier=TIER_HOLD,       note="contemp 비유의(reject)"),
FactorCell("eq_us_defensive", "vol",    -0.657, se=0.032, t=-20.82, n=5052, tier=TIER_VALIDATED, note="J축 std β, ΔVIX 지배"),
```
- ★reject tier 셀(rate/oil/credit) = β=None+HOLD 권고. (SEED 의 reject 는 점추정 박제하되 pool 제외인데,
  defensive 는 애초 점추정 자체가 ≈0+비유의라 HOLD 가 더 정직 — main 판단: REJECT(β박제) vs HOLD(None) 택일.)

### 6.2 (신설 권고) financials sleeve — rate-POS 별도 unit

```python
FactorCell("financials", "rate",   +0.162, se=0.023, t=+6.94,  n=5052, tier=TIER_VALIDATED, note="NIM, defensive 와 부호반대"),
FactorCell("financials", "dollar", -0.081, se=0.022, t=-3.65,  n=5052, tier=TIER_VALIDATED, note="J축 std β"),
FactorCell("financials", "oil",    None,    tier=TIER_HOLD,       note="contemp 비유의"),
FactorCell("financials", "credit", None,    tier=TIER_HOLD,       note="contemp 비유의"),
FactorCell("financials", "vol",    -0.617, se=0.031, t=-20.21, n=5052, tier=TIER_VALIDATED, note="J축 std β"),
```
- POOL_GROUP["financials"]="equity_risk" 추가 필요. ★main 미반영(검수 후 Edit).

### 6.3 vol factor 활성 효과

현재 SEED 는 전 sleeve vol=HOLD(노출 0). defensive/financials vol β 측정으로 **equity_risk pool 에 vol
loading 형성** → 같은 group 의 hold sleeve(eq_us_cyclical/eq_intl/reit) 도 vol pool 노출 받음
(VIX↑=동반 risk-off 가시성). M5 Phase A 의도와 정합.

## 7. 제약·hedge (small-n rigor 무관 — n=5052 대표본이나 명시)

- ★contemporaneous daily 측정. predictive/forward 검증 아님(별도 축, handoff "forward 전멸"과 구분).
- window 2006~ (dollar bind). pre-2006 regime(저변동·고변동) 외삽 불가.
- bias=1.000 은 z-unit conservation 산물 — 실 production Λ(실측 factor 분산) 캘리브레이션은 M5 범위.
- ★코드(core/study/) 미수정. SEED_CELLS Edit·POOL_GROUP 추가는 main 검수 후.
