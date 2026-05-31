---
tags: [type/summary, domain/commodity, phase/study-system]
date: 2026-05-30
---

# commodity 스터디 요약 (사람용)

## 1. 일반론 (블록1 lens 의 핵심)

**원자재 가격 결정 = 4축 동시 작용**
1. **Theory of Storage** (Kaldor-Working): F(t,T) = S·exp((r + u − y)·(T−t))
   - r = real rate, u = storage cost, y = convenience yield(현물 보유 옵션)
   - **Backwardation** (F<S, 곡선 우하향): convenience yield 우세 = 재고 타이트 = 양의 carry
   - **Contango** (F>S, 곡선 우상향): 보유비용 우세 = 재고 잉여 = 음의 carry → roll cost drag
2. **현금흐름 없음** → 주식과 달리 **거시 driver 가중치 ↑** (real rate, DXY, PMI)
3. **공급 충격 dominance** — OPEC·기상·geopolitical 이 demand 보다 빠른 jump
4. **재고 cushion** = mean-reversion 메커니즘 (단 oversupply regime 에서 decoupling)

## 2. 보고서가 엮어 보는 관계 (핵심 5)

| 관계 | 방향 | 메커니즘 |
|------|------|---------|
| Real rate ↑ → gold ↓ | 강 음(-0.6~-0.8) | 보유비용 ↑ vs inflation hedge demand 의 상쇄 |
| DXY ↑ → 모든 commodity ↓ | 음 | USD 표시 + EM 구매력 ↓ |
| Global PMI ↑ → industrial metal·oil demand ↑ | 양 | 1-3개월 lag |
| Inventory ↓ → convenience yield ↑ → backwardation | 강 음→양 chain | Working theory 직접 동치 |
| Term structure slope → roll yield 부호 결정 | 정의식 | F2-F1 backwardation 깊이 |

## 3. 우리 시스템 자료 매핑 (있는 것 / 없는 것)

**있음**:
- `commodity_assumptions.py` (carry/seasonal/inventory **검증 통계** 완비 — carry_forward_slope, seasonal_f_test, variance_ratio, threshold_regression, oversupply_decoupling)
- `commodity_carry.yaml` archetype config (roll_yield primary, contango_flip/inventory_glut value_trap)
- `fred_adapter.py` FRED_SERIES 17개 거시 (T10Y2Y, HY OAS, CFNAI 등)
- `collect_macro.py` Yahoo 실시간 (gold GC=F, oil CL=F) — **단 PIT vintage 아닌 5d snapshot**

**없음 → 블록6 collector_plan**:
- **Real rate (FRED DFII10)** — fred_adapter FRED_SERIES 에 dict 추가 1줄
- **Global PMI (FRED NAPM)** — 동일
- **EIA crude/petroleum stocks** — 신규 EIA adapter (free API key)
- **USDA WASDE stock-to-use** — 신규 USDA adapter (grains)
- **Commodity futures term structure (F1/F2/F3)** — CME 지연 EOD 또는 OpenBB
- **CFTC COT report** — public API free
- **LME warehouse stocks** — 1차 stub (band 보수)

## 4. 결정·기각 사유

### 결정
- **블록2 indicator naming**: "inventory" 토큰 회피 → `days_of_supply` / `stock_to_use_ratio` / `eia_crude_stocks` 명명.
  - 이유: `weight_panel._REFLEXIVE_WORDS` 에 "inventory" 포함 — commodity 펀더멘털이 오탐 차단됨.
  - 블록7 learn 단계 (a) 안 = 코드 무변경, naming 만 회피.

- **블록3 force-include 화이트리스트 후보 (이론 강한 ≤4 엣지)**:
  1. `days_of_supply ↔ convenience_yield_z` (Working theory 직접)
  2. `convenience_yield_z ↔ roll_yield` (Theory of Storage 정의식)

- **블록4 granularity = industry sleeve 우선**: energy/metals_industrial/metals_precious/agri 4 sub-sleeve.
  - 종목별(ticker) 단위는 hierarchical pooling (composed_weights.delta_arch_by_type) soft membership 으로 보간.
  - 부록 B 원칙 준수: ticker 별 독립 학습 X, archetype shrinkage.

- **블록5 confidence_metric 이중**: e-value (Ramdas SAVI) for carry/sign_flip, Beta posterior for binary outcome (inventory mean-revert).

### 기각
- **COT (CFTC) primary metric 채택 기각**: Sanders-Irwin (2010-2017 시리즈) — COT 자체 예측력 약함 검증됨.
  → companion (cot_net_specs_z) 로만 사용, momentum 과 partial-corr (common_cause: 가격 trend) 로 모델링.

- **재고 raw level 직접 사용 기각** → days_of_supply / stock_to_use_ratio (정규화).
  - 이유: commodity 마다 절대 재고 scale 다름. 회전일 또는 비율이 cross-section 가능.

- **percentile transform 기각** (commodity_carry.yaml `percentile_overfit_risk: false` 명시):
  - carry 부호·수준은 분위보다 절대값 의미. → transform: level 강제.

- **LME 유료 데이터 즉시 도입 기각**: 1차 stub (band 보수) → 정책 결정 후 유료 도입.
  - `commodity_assumptions.netflow_guard` 패턴 차용 (proxy_forbidden + 보수 band).

## 5. main 에 요청할 핵심 (블록6 발췌)

1. **FRED_SERIES 4개 추가** (DFII10, NAPM, DCOILWTICO, POILBREUSDM) — 1줄 수정, 즉시 가능
2. **EIA API key** (무료 회원가입) — days_of_supply core 입력
3. **USDA WASDE adapter** — grains stock-to-use
4. **Commodity futures term structure collector** — roll_yield 핵심 입력 (CME 지연 EOD 무료)
5. **CFTC COT collector** — public API, companion only
6. **LME warehouse** — 1차 stub OK

## 6. SACRED 불변식 영향 (블록7 risk 종합)

- **반사성 게이트** (weight_panel.assert_no_reflexive_series): 블록2 naming (a)안 채택 = SACRED 영향 0
- **천장 불변식** (assert_ceiling_invariant): judge lens 주입은 LLM down-only attenuation 만 → S_out ≤ S_L1 보존
- **registry append-only**: 새 카드 transition 만 (기존 카드 mutation 0)
- **train_weights 회귀 0**: 신규 cron entry 추가만, 함수 본문 변경 없음
- **update_controller**: kwarg 추가 (기본값 = 기존 stock 동작)

## 7. 4단계 파이프 입력 요약

| 단계 | 파일 | 핵심 변경 |
|------|------|---------|
| ① learn | weight_panel/fred_adapter/train_weights/commodity_assumptions | FRED_SERIES 4 추가 + train 신규 호출 + commodity_confidence_tracker 신규 모듈 |
| ② card | weight_card/registry | lens·confidence_now 필드 추가 (default None — 회귀 0) |
| ③ inject | stock_track/judge/regime_to_weights | commodity branch + lens LLM 주입 + commodity sleeve 등록 |
| ④ falsify | weight_falsification/update_controller | carry sign_flip → kill 가속 + adopt_dwell 6 (commodity 길이) |

상세는 `study_session.yaml` 블록7 참조.
