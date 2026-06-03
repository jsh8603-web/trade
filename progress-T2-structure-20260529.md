---
tags: [type/progress, domain/inv, phase/II, track/T2]
date: 2026-05-29
session: btn-button
spec: ./SPEC-T2-structure-model.md
split_index: ./SPLIT-INDEX-phase2.md
owner: button (T2 위임)
---

# progress-T2 — 구조모델·archetype·regime 층

> 위임: btn-Inv supervisor → button (T2). 산출 = cheapness_z·ArchetypeCard 확정 → T3(btn-Codlearn) 공유.
> 의존: T1 패널 schema (btn-Inv 확정중) → **mock fixture parquet 으로 병렬 개발**.

## 게임체인저 (전제)
cheap = raw 멀티플 분위 ❌ → **구조모델 잔차** `cheapness_z = (E[multiple|drivers,sector,regime] − actual) / σ_resid`.
밸류트랩 = 잔차≈0 (drivers 가 낮은 멀티플을 다 설명) → dual 로 자동 도출.

## 환경 제약 (확정)
- Python 3.12.10 (`/c/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`)
- 가용: numpy 2.4 · pandas 2.2 · sklearn 1.8 · scipy 1.17 · statsmodels 0.14 · pydantic 2.12 · pyarrow 24
- **없음**: pymc · numpyro · ruptures → 계층베이즈 = **statsmodels MixedLM (REML ≈ empirical-Bayes 부분풀링)**, GBM 진단 = sklearn HistGBR
- 차용: `_refs/jumpmodels` (regime, Apache) · `_refs/ai-hedge-fund/.../valuation.py` (actual multiple, MIT, 이미 stock/valuation.py 에 어댑트됨)

## R8 바닥 2 (필수 선결 — 안 풀면 cheapness_z 허상)
- [x] ① 종속변수 비정상성: `MultipleDefinition` 버전 레지스트리 + `multiple_def_version` fixed-effect 흡수 (panel_schema.py)
- [x] ② 생존편향: fixture 에 상폐 80 row 포함 + 적합 표본 포함 (delist_flag/delist_ret), validate_panel 강제

## 인터페이스 3계약 (T3 소비 — 먼저 고정)
- [x] #1 panel schema (panel_schema.py, validate_panel 강제) + mock parquet (data/fixtures/semiconductor_panel_v1.parquet)
- [x] #2 `StructureModel.cheapness_z(firm,sector,date,as_of)->float` (음수=싸다, structure_model.py)
- [x] #3 `ArchetypeCard` discriminated union 5종 (archetype.py + config/archetypes/*.yaml)
- [x] #0 canonical as_of resolver seam (AsOfResolver Protocol, T3 주입 — 자체 해석 금지)

## WP 진행
- [x] T2-1 structure model: RLM Huber robust + 섹터 empirical-Bayes shrinkage(부분풀링) + regime별 σ + purged/expanding OOS + 외삽 clamp
- [x] T2-2 estimand 분리: descriptive 만 (forward return 미혼입, 문서/코드 명시)
- [x] T2-3 드라이버 식별: grouped 표준화 importance + regime-stratified 상관 + 서사×통계 2×2 (driver_diagnostics/driver_2x2). 서사 축 = 외부 LLM 키워드 주입
- [x] T2-4 archetype 5종 discriminated union (pydantic) + valid_from (시변) + cheapness_sign(compounder=expensive_trap)
- [x] T2-5 regime PIT: classify_pit(수익률곡선·PMI) + regime_model_version + classifier adapt (core/regime/pit_regime.py)
- [ ] T2-6 D4 Book: 후순위 (v2)
- [x] **★ T2-7 검증 = GO**: 잔차 PR-AUC 0.854 vs raw 0.513 (lift +0.341), F1 0.740 vs 0.505. claude R4 thesis 입증. ⚠️ 합성 — 실데이터 게이트 = T1 패널 도착 후 재실행

## ★ 결과 요약 (ckpt 2026-05-29 btn-button)
- **STOP gate = GO** (합성 adversarial fixture). 11/11 계약 테스트 PASS.
- 인계 문서: [handoff-T2-deliverable-20260529.md](./handoff-T2-deliverable-20260529.md) (T3 소비).
- 실데이터 STOP gate = T1 반도체 패널 도착 후 `run_validation(panel=실패널)` 재실행으로 확정 (미완).

## 검증 설계 (T2-7 — non-circular)
- DGP: 반도체 사이클 구조 (peak-EPS trap: 멀티플 낮지만 drivers 가 다 설명 → 잔차≈0 / trough real: 멀티플 정상이나 expected 더 낮음 → 잔차 강한 음수)
- H0(claude R4 thesis): cheapness_z(잔차) 가 raw 멀티플 분위보다 trap vs real 분별 우위
- 메트릭: precision/recall + PR-AUC, **잔차 vs raw분위 동일 데이터 head-to-head**
- ⚠️ 합성 DGP = "분리 가능성이 존재할 때 추정기가 회복하는가" 검증 (machinery + power). **실데이터 게이트 = T1 반도체 패널 도착 후** (정직 표기)

## 산출물
`core/structure/{panel_schema,structure_model,archetype,validate_semiconductor}.py` · `config/archetypes/*.yaml` · `core/regime/pit_regime.py` · T2-7 리포트

## Working Notes
- ckpt 2026-05-29 진입 (btn-button): 필독 5문서 흡수 완료, GREENFIELD 확인, 환경 제약 확정. 착수.
