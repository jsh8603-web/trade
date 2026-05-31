---
tags: [type/consult-prompt, domain/commodity, phase/study-system, round/1]
date: 2026-05-30
note: R1 자문 prompt — /gemini-web + /claude-web 병렬 동시 송신용. 자기완결 4섹션.
---

# R1 자문 — commodity 자산군 전문 애널리스트 방향성 설계

## §1. 컨텍스트 (자기완결 — 답변자에게 외부 추가 정보 없이 답할 수 있게)

**시스템**: Quant 가정 검증 시스템 R15. 자산군마다 스터디 작업방이 산출하는 **6블록 산출 계약**
(lens · indicators · relationships · weight_rules · confidence_hooks · collector_plan + code_change_plan)
을 main 이 통합해 production wiring 한다. 본 작업방 담당 = **commodity** (원자재 전 범위).

**스터디 구조 (산출 정의)**:
- **lens**: 정성 렌즈 (pricing_principle / report_relations / regime_reading / estimation_note)
  → Judge LLM 평가 시 prompt 로 주입. 가변(블록5 flag 누적이 미세변동).
- **indicators**: 정량 지표 (family ∈ {valuation, quality, momentum, revision, macro_sensitivity, risk, macro_driver},
  source_or_collector, transform ∈ {own_history_z, rank, level, yoy}, vintage_policy=point_in_time).
- **relationships**: **partial-corr** 기준 관계 가설 (glasso prior). conditioning_set 필수 명시.
  edge_type ∈ {direct, common_cause, undetermined}.
- **weight_rules**: 종목별 동적 가중치 (modulate_by ∈ {regime, industry, size, name_specific}).
- **confidence_hooks**: 매 거래마다 (확신/거부) flag → 신뢰도 누적 (e-value 또는 Beta posterior) →
  lens·가중치 미세변동. 단순 정의 금지 — 어느 코드에서 emit/accumulate/store/action 까지.

**파이프라인 (4단계)**:
1. learn: regime-conditional graphical lasso (nonparanormal + EBIC + EB shrink) → belief-mixed Ω_eff
2. card: Ω·IC → derive_weights (Grinold w∝Ω·IC + 1/N blend + capped-simplex) → WeightAssumptionCard
3. inject: 종목 buy 시 S_L1 = clamp_floor(Σ wᵢ·zᵢ) → Judge LLM down-only attenuation (S_out ≤ S_L1)
4. falsify: Rank-IC e-CUSUM 단측 → primary_kill / Ω drift → secondary_refit

**우리 데이터 가용성** (commodity 한정):
- 거시 (FRED 17 시리즈): T10Y2Y, NFCI, BAA10Y, HY OAS, CFNAI, CPI/PCE 등. 단 **DFII10 (real rate)·NAPM (ISM PMI)·DCOILWTICO·POILBREUSDM 미포함** — dict 추가 1줄로 가능.
- FxStore (PIT vintage): DXY/USDKRW (main 선구축 진행 중).
- 신규 collector 필요 (블록6): **EIA crude/petroleum stocks** (free API), **USDA WASDE stock-to-use** (grains, free), **CME 지연 EOD futures term structure** (F1/F2/F3 — roll_yield 핵심), **CFTC COT** (public API, weekly), **LME warehouse** (1차 stub 보수 band).
- 이미 코드 보유: `core/structure/commodity_assumptions.py` — carry_forward_slope (prequential sign_flip),
  seasonal_f_test, variance_ratio (Lo-MacKinlay), threshold_regression (Hansen), oversupply_decoupling.
  `config/archetypes/commodity_carry.yaml` — primary=roll_yield, value_trap_guards.

**commodity sub-sleeve** (산업 차이 있음 — 4분류 검토):
1. **Energy** (crude oil WTI/Brent, natural gas, gasoline)
2. **Industrial metals** (Cu/Al/Ni/Zn — China demand · LME 재고)
3. **Precious metals** (gold·silver·platinum — monetary · real rate)
4. **Agricultural** (corn/wheat/soybean — USDA WASDE · 기상 · stock-to-use)

**v1 산출의 결함 (사용자 지적)**: 자문 결과를 그대로 yaml 에 옮기고 끝냈음. 시계열 데이터 검증 부재. v2 = 전문 애널리스트로 다시 — 이론 → 데이터 검증 → 코드화 3단계 강제.

## §2. R1 질문 — 3 섹션, **모두 답해주십시오**

### A. 이론 수집 방향 (sub-sleeve 별 차이 명시)
원자재를 이해하려면 반드시 읽어야 할 **이론·교과서·핵심 논문·증권사 보고서 시리즈**는?
- 보편 (4 sub-sleeve 공통): 가격결정 이론 (Theory of Storage Kaldor 1939 / Working 1949 / Brennan 1958, hedging pressure Hicks·Keynes, normal backwardation), risk premium 분해 (Erb-Harvey 2006 "Tactical and Strategic Value of Commodity Returns").
- sub-sleeve 특화:
  - **Energy**: OPEC 정책 분석 (EIA STEO), shale break-even economics, refinery crack spread 이론
  - **Industrial metals**: China demand cycle (Caixin PMI), LME warehouse queue 동학, copper-as-bellwether 가설
  - **Precious metals**: gold monetary theory (Erb-Harvey gold valuation 2013), real rate ↔ gold partial-corr literature
  - **Agricultural**: USDA WASDE 발표 효과 연구, ENSO 기상 risk 분석, ethanol 정책 ↔ corn

**필수 보완 요청**: 우리가 (a) 놓친 학파 (b) 최신 SOTA (c) buy-side quant 실무 표준 (Asness-Moskowitz-Pedersen 2013 "Value and Momentum Everywhere" 의 commodity 부분, Yang 2013 carry, Bakshi-Gao-Rossi 2019 commodity risk premia) 별로 명시.

### B. 이론 검증 방향 (우리 데이터 시계열 검증법)
A 의 이론들을 우리 가용 데이터로 시계열상 어떻게 검증하나? **검증 통계 + 데이터 매핑** 정량 명시.
- 예시: Theory of Storage 의 F(t,T) = S·exp((r+u−y)(T−t)) — F/S spread 를 (DFII10 real rate r, EIA storage cost u proxy, 추정 convenience yield y) 로 회귀 → R² · partial-coef 부호 일치 확인. sub-sleeve 별 데이터 가용성 차이 (LME 무료 stub vs EIA free).
- carry-momentum (Asness 2013): roll_yield + 12-1 momentum 결합 portfolio → Sharpe / max DD / IC stability.
- 평균회귀 가설: variance_ratio (Lo-MacKinlay), threshold_regression (Hansen) — 우리 commodity_assumptions.py 에 이미 구현. 이걸 어떻게 활용하나.
- regime 조건부 검증: cglasso (asset_core | macro ~ N(B·macro, Ω_asset)) — sub-sleeve 별 conditioning_set 결정.

**필수 보완 요청**: 우리가 놓친 통계 (예: Westerlund-Hosseinkouchack panel cointegration, FIGARCH long-memory in commodity vol, Hamilton 1996 oil-recession nonlinear) 적극 제시.

### C. 핵심 가설 초안 (반증조건 정량 명시 — 5~10개)
검증할 핵심 가설 5~10개. 각 가설:
```
- hypothesis_id: <snake_case>
  statement: <한 줄, 검증 가능한 명제>
  sub_sleeve: <energy|industrial|precious|agri|all>
  falsification_criterion: <정량 — 예: "36m rolling partial-corr |r|<0.2 OR 부호반전 6개월 지속">
  data_required: <시리즈 ID 또는 collector — 예: gold price + DFII10 + DXY (FRED+FxStore)>
  lag: <periods — 예: "contemporaneous" or "1-3 month">
  prior_strength: <0~1 — 이론 확신도>
```

**가설 예시 우선순위** (이론 강한 것 위주):
- gold ↔ real_rate negative partial-corr (controlling DXY)
- inventory↓ → convenience_yield↑ → backwardation (Working theory 정의식)
- contango_flip → roll cost drag → carry premium 붕괴 (Erb-Harvey)
- China PMI ↑ → industrial metal demand → 3 month lag price
- ENSO regime → corn/soybean yield → 6 month seasonal price
- OPEC+ 감산 발표 → WTI 즉시 jump (event study) — discrete
- COT speculator net long → momentum common cause (Sanders-Irwin: COT 자체 약함)
- gold vol ↔ real rate vol (1-2017 vs 2018-present regime 분리)
- commodity index roll cost drag (BCOM·GSCI) — contango regime 누적 손실

**필수 보완 요청**: 위 9개 외 **반드시 검증해야 할 가설** 추가 제시. 우리가 놓친 reflexivity·tail risk·structural break 가설.

## §3. 형식 요청

- **3 섹션 A/B/C 모두**. 각 섹션 최소 5문단.
- **sub-sleeve 별 차이**가 있는 항목은 명시.
- C 의 가설은 위 5필드 yaml-like 양식 그대로.
- 모든 인용 (Asness 2013, Erb-Harvey 등) **출판년·저자명·핵심 발견** 한 줄 요약 동봉.
- ⛔ **"검토하라" 류 추상 금지** — 구체적 학파·논문·통계·반증조건.

## §4. 다음 단계 (R2 이후)

R1 응답 후 본 작업방이 두 모델 응답 비교 → 차이/공통점/빈틈 식별 → R2 질문 (반증조건 정량화 + 시계열 검증 통계 디테일 + 결정적 단일 가설 선정). 3~7R 수렴 후 direction.md 작성 → main 승인 게이트.

답변 길이 제한 없음 — **완전성·정확성 우선**.
