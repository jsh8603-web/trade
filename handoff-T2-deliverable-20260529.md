---
tags: [type/handoff, domain/inv, phase/II, track/T2]
date: 2026-05-29
session: btn-button
spec: ./SPEC-T2-structure-model.md
progress: ./progress-T2-structure-20260529.md
consumer: T3 (btn-Codlearn)
status: 3 계약 확정 + T2-7 STOP gate = GO (합성, 실데이터 T1 대기)
---

# T2 인계 — cheapness_z·ArchetypeCard 확정 (T3 소비용)

> btn-button(T2) → btn-Codlearn(T3). 게임체인저 = **cheap = 구조모델 잔차**. 밸류트랩 = 잔차≈0 dual.

## ★ T2-7 STOP gate 결과 = **GO** (프로젝트 전체 전제 통과)

반도체(cyclical) 라벨 에피소드에서 **잔차(cheapness_z) vs raw 멀티플 분위 head-to-head** (walk-forward OOS):

| 방법 | PR-AUC | P@top20% | Recall | F1 |
|---|---|---|---|---|
| **residual (cheapness_z)** | **0.854** | 0.661 | 0.841 | **0.740** |
| raw_percentile (현 설계) | 0.513 | 0.450 | 0.576 | 0.505 |
| **lift** | **+0.341** | +0.211 | +0.265 | +0.235 |

- **판정 GO**: 잔차가 raw 분위를 PR-AUC +0.341 우위. DGP 가 structural_trap(나쁜 드라이버→낮은 멀티플, 잔차≈0)과 real(정상 드라이버→actual≪fair, 잔차≪0)의 **raw 멀티플을 겹치게** 설계 → raw 는 둘을 못 가르고 잔차만 가름 = claude R4 thesis 입증.
- 위상별: trough real 1.04 vs trap −0.64 / mid real 2.85 vs trap −0.41 (잔차 분별 압도). peak(전부 trap) 잔차 −1.24 = "안 싸다" 올바름.
- GBM 진단 lift ≈ 0 → 비선형 누락 없음 = 선형 부분풀링이 producer 로 충분 (GBM=진단기로만, claude R8).

⚠️ **정직 표기**: 본 검증은 **합성 fixture**(T1 실패널 미도착) — "분리 가능성이 존재할 때 추정기가 raw 대비 회복하는가"(machinery + 상대우위)를 입증. **실데이터 STOP gate = T1 반도체 패널 도착 후 동일 하니스(`run_validation(panel=실패널)`) 재실행으로 확정**. 산출물: `data/fixtures/t2_7_validation_report.{txt,json}`.

## 계약 #1 — 패널 schema (T1 → T2/T3)

`core/structure/panel_schema.py`. 필수 컬럼 (`validate_panel()` 강제):
- 식별·시간(bitemporal): `firm` · `sector`(as-of) · `date` · `knowable_from`(PIT: ≤ as_of) · `regime_id`
- 종속변수(R8①): `multiple` · `multiple_def_version`
- 생존편향(R8②): `delist_flag` · `delist_ret`(Shumway)
- 드라이버: `drv_*` prefix (≥1)

**mock parquet 제공**: `data/fixtures/semiconductor_panel_v1.parquet` (1440 row, 상폐 80, 정의 2버전). T3 는 이걸로 병렬 개발.

## 계약 #2 — cheapness_z (T2 → T3)

```python
from core.structure.structure_model import StructureModel, StructureModelConfig
model = StructureModel(config=StructureModelConfig(purge_days=90),
                       as_of_resolver=<T3 canonical resolver>)   # ← 계약0
model.fit(panel, as_of)                       # purged/expanding OOS, delisted 포함(R8②)
z = model.cheapness_z(firm, sector, date, as_of)   # float, 음수 클수록 저평가, 잔차≈0=trap
```
- `cheapness_z = (actual − E[multiple|drivers,sector,regime]) / σ_resid` (SPEC 의 `E−actual` 와 부호만 반대 동치, **T3 계약 = 음수=싸다** 고정).
- E[multiple] = statsmodels RLM(Huber robust) fixed-effect + **섹터 empirical-Bayes shrinkage**(계층 부분풀링; pymc 부재 대체). σ = **regime별 robust scale**(MAD×1.4826; 패닉 regime 분산 격리). z 는 ±8σ clamp + 멀티플 외삽 밴드 clip.
- R8① = `multiple_def_version` 를 fixed-effect 더미로 흡수. R8② = delisted row 적합 포함.
- 행 단위 배치: `model.cheapness_z_rows(df) -> np.ndarray`.

## 계약 #3 — ArchetypeCard (T2 → T3)

`core/structure/archetype.py`. pydantic v2 **discriminated union**(판별자=`archetype`), 5종:

| archetype | primary_metric | cheapness_sign | percentile_overfit_risk |
|---|---|---|---|
| cyclical | ev_ebitda | low_multiple | ✅ (raw 신호 역전) |
| event_driven | ev_sales | low_multiple | ✅ |
| spread_driven | price_to_book | low_multiple | — |
| asset_stable | dividend_discount_value | low_multiple | — |
| compounder | roic_durability | **expensive_trap** | ✅ (함정이 비싼 쪽) |

- 공통 core: `primary_metric` · `companion_signals[]` · `value_trap_guards[]` · `valid_from`(시변, claude R7) · `cheapness_sign` · `percentile_overfit_risk`.
- config = `config/archetypes/*.yaml`. 로드: `archetype.load_cards_from_config()`. 섹터 매핑: `archetype_for_sector(sector)`.
- ⚠️ **compounder 는 cheapness_sign=expensive_trap** — T3 게이트는 archetype dispatch 로 저멀티플을 "싸다"로 해석하면 안 되는 경우를 분기해야 함.

## 계약 0 — canonical as_of resolver (T3 가 SSOT, T2 경유만)

`structure_model.AsOfResolver` Protocol. T2 는 as_of 를 **자체 해석 안 함** (claude R7 reconcile 발산 방지). T3 가 공통 resolver 구현 → `StructureModel(as_of_resolver=...)` 주입. 미주입 시 `IdentityAsOfResolver`(passthrough, ⚠️ production 금지).

## 산출물 파일
- `core/structure/panel_schema.py` · `structure_model.py` · `archetype.py` · `validate_semiconductor.py`
- `config/archetypes/{cyclical,event_driven,spread_driven,asset_stable,compounder}.yaml`
- `data/fixtures/semiconductor_panel_v1.parquet` · `t2_7_validation_report.{txt,json}`
- `tests/structure/test_contracts.py` (계약 잠금)

## T3 가 이어서 할 것 (의존 해소)
1. canonical as_of resolver 구현 → T2 StructureModel 에 주입 (계약0).
2. RuleProvider 가 `value_stock` 래핑 시 `cheapness_z` + ArchetypeCard 주입 (shadow-only, IMPL-OUTLINE §6.3).
3. L1 게이트 archetype dispatch (compounder = expensive_trap 분기).
4. T1 실패널 도착 시 `run_validation(panel=실패널)` 재실행 → 실데이터 STOP gate 확정.

## T2-3 드라이버 식별 (완료)
`StructureModel.driver_diagnostics()` = grouped 표준화 importance(공선성 하 partial effect, raw SHAP 함정 회피) + regime-stratified 상관(국면의존). `driver_2x2(narrative_drivers)` = 서사×통계 2×2 (confirmed/folklore/unmodeled/noise) — 서사 축은 T3/LLM 키워드를 set 으로 주입. claude R4 A1 "정보 최대 = 불일치 2×2".

## 미완 (T2 잔여, v2)
- T2-6 D4 Book(ruptures 분절→narrative) = v2 (ruptures 미설치).
- T2-5 D1 비모수 regime(bnpy sticky HDP-HMM) = 후순위. 현 v1 = `core/regime/pit_regime.py`(고정-K=3) + 기존 `regime_classifier.py`(JumpModel) adapt.
- 계층베이즈: pymc 부재로 RLM+empirical-Bayes shrinkage 대체. pymc 도입 시 완전 베이즈 부분풀링 업그레이드 가능.
