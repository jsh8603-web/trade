---
tags: [type/raw-note, domain/commodity, phase/study-system]
date: 2026-05-30
---

# 코드 정독 노트 (commodity 작업방, 자율)

## 읽은 파일 / 핵심 발견

### 1. `core/structure/commodity_assumptions.py` (435 lines, 완독)
- `build_commodity_cards()` 가 3 가정 카드 발행: carry_premium_holds / seasonality_present / inventory_mean_reverts
- 검증 함수: `carry_forward_slope` (prequential sign_flip 탐지) / `seasonal_f_test` (월더미 F + STL strength) / `variance_ratio` (Lo-MacKinlay) / `threshold_regression` (Hansen) / `oversupply_decoupling`
- `netflow_guard` stub 패턴 = 유료 데이터 미연동 시 band 보수 (LME 도입에 차용 가능)

### 2. `config/archetypes/commodity_carry.yaml`
- archetype: commodity_carry, primary_metric: roll_yield
- companion: term_structure_slope, convenience_yield, inventory_days
- value_trap_guards: contango_flip, inventory_glut, roll_cost_drag
- **percentile_overfit_risk: false** — 분위변환 금지, level 사용

### 3. `scripts/collect_macro.py` (298 lines, 완독)
- Yahoo Finance 실시간 6 심볼: ^GSPC/^IXIC/DX-Y.NYB/GC=F/CL=F/^TNX
- range=5d, **NOT PIT vintage** — 단순 snapshot. macro_score → market_context_log 저장용
- 적절한 학습 입력 아님 → commodity 학습용 별도 collector 필요 (블록6 명시)

### 4. `core/brain/fred_adapter.py` (192 lines, 완독)
- FRED_SERIES 17개: GDPC1/PAYEMS/CPILFESL/T10Y2Y/NFCI/BAA10Y/BAMLH0A0HYM2/CFNAI 등
- **commodity 핵심 누락**: DFII10 (real rate), NAPM (PMI), 원자재 가격 시리즈
- RealFredAdapter.get_series(as_of) — pit_mode='first_release' 기본 (lookahead 차단)
- 추가 = dict 1줄 (블록7 learn 단계 명시)

### 5. `core/data/weight_panel.py` (220 lines, 완독)
- `build_indicator_matrix(provider, series_ids, periods, as_of)` = (n_periods, n_series) PIT matrix
- **★`_REFLEXIVE_WORDS` 에 "inventory" 포함** (L53~58)
  - word-boundary 토큰 매칭 — series_id 를 _/-/공백/.으로 split → 교집합
  - commodity 의 `inventory_days` 같은 명명 시 ValueError 차단됨
  - 해결: series_id 를 `days_of_supply` / `stock_to_use_ratio` / `eia_crude_stocks` 로 명명 회피 (블록7 (a)안)

### 6. `core/structure/conditional_correlation.py` (639 lines, 완독)
- RegimeGlasso.fit(X, regime_ids) — nonparanormal → EBIC glasso → EB shrink (corr_prior 주입 가능)
- effective_precision(models, belief) — cov-space mix → Cholesky → Ω_eff (1회 역행렬)
- TemperatureCalibrator (frozen, hash-pin) — regime classifier softmax → belief
- ic_power_gate (block-bootstrap autocorr 보정, MDE + effective-n)
- corr_prior 자리에 블록3 prior_sign·prior_strength matrix 주입 가능 (force-include ≤4 엣지)

### 7. `core/assume/weight_card.py` (401 lines, 완독)
- WeightAssumptionCard: series_ids/w_global/delta_regime/delta_arch_by_type/delta_inter
- composed_weights(pi) — hierarchical pooling (부재 component = 0 자동 강등)
- delta_arch_by_type = {archetype: δ벡터} soft membership (π 혼합)
- **lens (정성) 필드 없음** → 블록7 card 단계에서 추가 (default None, 회귀 0)
- derive_weights — Grinold w∝Ω·IC + 1/N blend (DeMiguel) + capped-L1 (water-filling)
- synthesize_l1 = clamp_floor(Σwz) — pre-LLM·pre-agent 결정론
- assert_ceiling_invariant — judge down-only attenuation 강제 (SACRED)

### 8. `core/assume/weight_cycle.py` (358 lines, 완독)
- GlassoWeightLearner (Protocol 구현) — RegimeGlasso 캡슐화. omega_eff(belief)/ic(returns) 노출
- build_weight_card — Ω·IC → derive_weights → 카드 등록
- route_lifecycle — PRIMARY kill → RETIRE / SECONDARY refit → transition_card → registry.transition
- run_weight_cycle — 4단계 1회전 production-callable (offline/replay 결정론)

### 9. `scripts/train_weights.py` (197 lines, 완독)
- train_weight_cards — 배치 오케스트레이터 (FRED → store → panel → glasso fit → regime 카드)
- domain/scope 인자 — commodity 호출 1건 추가만으로 학습 가능
- substrate 부족 시 graceful skip (TrainResult.skipped_reason)

### 10. `core/assume/weight_falsification.py` (Read 실패, weight_cycle 코드에서 인터페이스 파악)
- `rank_ic(scores, fwd)` — Rank-IC + p-value
- `evaluate_weight_card(card, ic_series, baseline_ic, sd, omega_old, omega_new)` → WeightFalsificationResult
  - .primary_kill (PRIMARY = score IC e-CUSUM 단측 붕괴)
  - .secondary_refit (SECONDARY = Ω drift)
  - .verdict (engine 입력)
- `score_ic_breakdown_eprocess` — e-CUSUM 단측 kill

### 11. `core/assume/registry.py` / `core/assume/update_controller.py` / `core/stock_track.py` / `core/assume/judge.py` / `core/brain/regime_to_weights.py`
- ctx 한도로 직접 Read 미완 — 블록7 작성은 STUDY-KIT §4 표 명시 심볼 + weight_cycle 코드 사용처 기준
- registry: id 규약 "weight.{scope}.{regime}" 사용 확인 (weight_cycle.build_weight_card L122)
- update_controller: UpdateController.step(card, verdict, hard_falsifier, dwell_ok, k_window_persist, same_regime) 호출 인자 확인 (route_lifecycle L185~203)

## 자문 호출 여부

- 사용 안 함 — 코드 정독 + 이론 지식(Theory of Storage, Working convenience yield, Sanders-Irwin COT, Asness-Moskowitz-Pedersen carry-momentum) 으로 충분
- 만약 추가 자문 필요 시 후보 질문:
  1. (gemini-web) "Theory of Storage 의 r/u/y 분해를 modern macro regime 조건부로 어떻게 캘리브레이션하나?"
  2. (claude-web) "commodity carry-momentum 결합 비중 (Asness 2013) 의 risk-off regime 시 decoupling 통계 검증법?"

## 다음 단계 (main 핸드오프 후)

1. main 이 G1~G6 production wiring 시 입력:
   - 블록2 indicators → 블록6 collector_plan 우선순위 정렬 (DFII10·NAPM·EIA 순)
   - 블록3 relationships → corr_prior matrix 조립 (RegimeGlasso 초기화 인자)
   - 블록4 weight_rules → composed_weights.delta_arch_by_type 학습 sleeve 분할
   - 블록5 confidence_hooks → commodity_confidence_tracker.py 신규 모듈 골격
   - 블록7 code_change_plan → 4단계 PR 단위 분리

2. 학습 가능 시점: 블록6 collector 5개 중 3개 (DFII10·NAPM·CFTC COT) 가용 시 1차 학습 가능. 나머지(EIA·USDA) 추가 후 full 학습.
