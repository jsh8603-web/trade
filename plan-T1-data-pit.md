---
tags: [type/plan, domain/inv, phase/II, track/T1]
date: 2026-05-29
session: btn-Inv
spec: ./SPEC-T1-data-pit.md
schema: ./PANEL-SCHEMA-phase2.md
progress: ./progress-T1-data-pit.md
note: Phase2 T1(데이터·PIT) 트랙 전용. master plan.md(tracked, Phase -1~R)와 분리.
---

# plan-T1 — 데이터·PIT 기반층 (Phase2 트랙 T1)

## 목표
rule·구조모델(T2,T3)이 딛고 설 bitemporal PIT 패널. 이 층 오염되면 위 전부 허상(look-ahead).
바닥부터 최후 — 기존 provider(dart/edgar/krx/macro_vintage·walk_forward) **조립**이 핵심.

## 3 Phase (remote 프로토콜)
### Phase 1 — 설계/계약 ✅ 완료
- PANEL-SCHEMA-phase2.md 확정 v1 (계약1) + T3 계약0(as_of_resolver) 의존 반영 + T2/T3 공유.

### Phase 2 — 구현
- **WP-T1-A** `core/data/pit_query.py`: AS OF 조회 인터페이스 + 계약0 seam(`_resolve_as_of` 주입점). T3 resolver 도착 전 항등.
- **WP-T1-B** `core/data/pit_panel.py`: 조립층. dart/edgar→Fundamentals→filter_pit_fundamentals(RESTATED 제외) + KrxStatus 플래그 + UniverseManager(상폐 포함) → bitemporal 3축(sys_time=build, append-only) → parquet 발행.
- **WP-T1-C** silent revision store: 같은 knowable_from 다른 sys_time row append, AS OF 가 최신 sys_time 선택.
- **WP-T1-D** US 멀티플 vintage 수집: Damodaran xls(read_excel URL) + French49. corp action 전처리(액면분할·자사주 보정).
- **WP-T1-E** 패널 빌드 스크립트 `scripts/build_panel.py` (--market --start --end → parquet + manifest content-hash).

### Phase 3 — 검증
- PIT 무결성: look-ahead 0 (knowable_from>as_of row 가 query_as_of 에서 안 나옴).
- silent revision 재현: 과거 조용한 수정 후에도 as_of 시점 값 동일(sys_time 분리 검증).
- survivorship: 상폐 종목이 백테스트 universe 에 포함(UniverseManager).
- RESTATED 거부: filing_source=restated row 패널 미적재.

## 의존/계약
- 上: 없음(최선행). 下: T2(패널 schema 소비), T3(AS OF + 계약0 producer).
- ⏳ 계약0(as_of_resolver) = T3 producer 대기. seam 으로 비워두고 도착 시 wire.

## 불변식 4 (전 트랙 공통)
①position=entry version 고정 ②rollback=append만(mutate0) ③rule⊂emergency_stop ④opportunity cost 계상.
T1 매핑: ② = sys_time append-only(옛 row 불변). ① = multiple_def_version/regime_model_version 동결.

## SACRED (회귀 금지)
- 기존 dart/edgar/krx/macro_vintage provider 본체 + Fundamentals 계약 = 증분만(폐기/시그니처 변경 금지).
- filter_pit_fundamentals·UniverseManager = 재사용(재구현 금지).
