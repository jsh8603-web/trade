# progress-T1 — 데이터·PIT 기반층 (Phase2 트랙 T1)

> plan: [plan-T1-data-pit.md](./plan-T1-data-pit.md) · schema 계약: [PANEL-SCHEMA-phase2.md](./PANEL-SCHEMA-phase2.md) · spec: [SPEC-T1-data-pit.md](./SPEC-T1-data-pit.md)
> 세션: btn-Inv. master progress.md(Phase -1~R)와 분리된 T1 트랙 추적.

## §진입 스냅샷 (handoff-plan-wf)
- **현재 step**: Phase 2 구현 완료(WP-T1-A~E), Phase 3 검증 PASS(15/15). codlearn 통지 + 회귀 확인 잔여.
- **계약 상태**: 계약1(panel schema) 확정 v1 박제+공유 / 계약0(as_of_resolver) = T3 producer 대기(seam 처리, set_as_of_resolver 주입점)
- **재개 지점**: 전체 회귀 재확인(bash 출력채널 일시 끊김) + codlearn psmux 통지

## Steps
- [x] **Phase 1 — 설계/계약** ✅ 완료(2026-05-29)
  - PANEL-SCHEMA-phase2.md 확정 v1(4계약 그래프·bitemporal 3축·PIT 조회규약·빌드 파이프라인). T3 계약0(as_of_resolver) 의존 반영(seam). T2/T3 공유.
- [x] **Phase 2 — 구현** · model: opus ✅ 완료(2026-05-29)
  - [x] WP-T1-A `core/data/pit_query.py` (AS OF view/query + 계약0 `set_as_of_resolver` seam + PitPanel 래퍼)
  - [x] WP-T1-B `core/data/pit_panel.py` (PanelAssembler 조립층, filter_pit_fundamentals/UniverseManager 재사용, RoutingFundamentalsProvider KR/US 라우팅)
  - [x] WP-T1-C silent revision: build_record sys_time 기본=knowable_from, 정정 시 명시 sys_time row append(불변식②)
  - [x] WP-T1-D `core/data/corp_action.py`(split/buyback adjust+미기록분할 탐지) + `stock/data/sector_multiples.py`(Damodaran/French49, offline cache·N-T1-SECTORMULT deferral)
  - [x] WP-T1-E `scripts/build_panel.py` (parquet + manifest content-hash vintage)
- [x] **Phase 3 — 검증** ✅ 15/15 PASS (exitcode=0)
  - [x] RESTATED 거부 / filing-lag PIT / look-ahead 0(knowable+sys_time 게이트) / silent revision 재현 / survivorship 상폐포함 / as_of_resolver seam / multiples / corp_action 5종
  - **회귀 확인**: 전체 pytest = 48 failed / 4227 passed. 48 실패 = `tests/KNOWN_FAILURES.md` 박제 집합과 **파일별 실패 수까지 정확히 일치**(kis 14·macro_vintage 8·e2e 7·integration_gate 6·build_imports 6·dashboard 4·build_config 4·golden_rule 3 +나머지). 신규 실패 0 + T1 모듈(pit_panel/pit_query/corp_action/sector_multiples/build_panel) 참조 실패 0. **직교 판정**: T1 = 전부 신규 파일, 기존 소스 0수정 → 구조적 회귀 0.

## ★ 발견·수정 (Phase 2 진행 중)
- **버그 fix**: build_record `sys_time` 기본값을 build 시각으로 두면 미래 빌드 패널이 과거 백테스트를 전부 막음(sys_time>as_of). → 기본=`knowable_from` 으로 수정(silent revision 시에만 명시 override). schema 문서 §2.1 정합.
- **인터페이스 정합**: provider 진입점 = `fetch_filings`(fetch 아님). UniverseManager.get_backtest_universe(all_tickers) = date-agnostic → assemble 에서 상폐일 date-aware 필터 별도 적용.

## Steps — 가정 라이프사이클 T1 (신규과제, TASK-T1-assumption-research)
> 산출물 3종 = RESEARCH-T1-assumption-data + DESIGN-T1-assumption-data + 본 구현계획. 코드 스텁 X(설계·리서치 깊이).
- [x] **A1 prior art 실조사** ✅ (Gemini Phase1 라이선스 확정, RESEARCH-T1 §1~6). 채택=Pandera(MIT)+OpenLineage스펙+onlineFDR논문구현, 통합OSS 부재 확정.
- [x] **A2 데이터층 설계** ✅ (DESIGN-T1: data_contract 게이트·3도메인 검증패널·lineage·knowable_from 합성·online FDR 상태영속·분담 인터페이스).
- [ ] **A3 구현 (fixture 우선, go-live 분리)** — 설계→코드 (다음 세션 또는 T3 합류 후):
  - [ ] `core/data/data_contract.py` (Pandera schema+domain Check+ContractResult) — **fixture 검증 가능**(합성 패널)
  - [ ] `core/data/lineage.py` (ProvenanceRef/LineageEvent emit/replay jsonl) — **fixture**
  - [ ] `core/data/online_fdr.py` (LORD++/SAFFRON+AlphaWealthState 영속) — **fixture**(논문 수식 재확인 선행)
  - [ ] `pit_query.py` 확장 (synth_knowable_from+assert_referential_pit) — **fixture** (단 assert_referential_pit는 T3 assumption_store.is_active 계약 의존)
  - [ ] `panel_schema.py` 확장 (instrument_kind/lifecycle_status/lifecycle_date, delist_* 하위호환) — **fixture**
  - [ ] `seed_builder.py` Signal.derived_from additive — **fixture**(하위호환 회귀0 확인)
  - [ ] `detectors.py` 추출 (rule_observer PageHinkley/psi+KS) — **fixture**
  - [ ] **go-live 분리**: 상품 무료소스 실연결(EIA/USDA/ETF NAV) = N-T1-COMMODITY-SRC / FRED 거시 vintage = N-P4-FRED 동반.

## 이연 항목
- **N-T1-COMMODITY-SRC**: 상품(ETF NAV/iNAV·선물 롤오버·계절성·재고 EIA/USDA) 무료 데이터소스 미조사. 확신<80% → 구현 전 Gemini Phase2 또는 자문 1회. (출처: DESIGN-T1 §2)
- (패널 트랙) 없음 — Phase1~3 완주.

## Working Notes
> 인계: [handoff-T1-assumption-20260529.md](./handoff-T1-assumption-20260529.md) — 신규과제(가정 라이프사이클 데이터·PIT 리서치+설계)
> [ckpt-202605291640:btn-Inv] — 신규과제 진입: 가정(Assumption) 라이프사이클 T1(데이터·PIT) 리서치+설계 (TASK-T1-assumption-research-20260529.md)
- **마지막 결정**: prior art 라이선스 실조사 완료(Gemini Phase1, archive 복사). 채택=Pandera(MIT,light)+OpenLineage(Apache,스펙만)+onlineFDR(논문서 직접구현, Python포트 없음). 기각=GE/Soda/Deequ(heavy/Spark)·Marquez(서버). drift=rule_observer 기존 PSI/PageHinkley 재사용+KS/MMD 참조. 통합 OSS 없음 확정. 코드현황 파악: T3가 core/pit/as_of.py(canonical resolver=계약0 충족)·bitemporal_store.py·rule_observer.py·promotion_gate.py(batch BH FDR=online 부재 확인)·seed_builder.py 보유. assumption 참조 0(greenfield).
- **다음 의도**: 산출물 3종 작성 — (1)RESEARCH-T1-assumption-data-20260529.md(prior art 표+권고) (2)DESIGN-T1-assumption-data.md(3도메인 PIT 패널 확장+data contract 게이트 pit_query 앞단+lineage provenance+online FDR 상태영속 스키마+생존편향+knowable_from 합성규칙) (3)구현계획(progress 스텝, fixture vs go-live). 코드 스텁 금지, 설계 깊이 요구.
- **다음 의도**: T1 Phase 1~3(패널) 완주(설계·구현·검증). 산출물 8파일 + 테스트 15/15 PASS. T3 계약0(as_of_resolver) = `core/data/pit_query.py:set_as_of_resolver` 주입점으로 비워둠(도착 시 1곳 wire).
- **다음 의도**: codlearn psmux 통지(작업내용+위치) + 전체 회귀 재확인(bash 출력채널 일시 끊김으로 미확인 — 복구 후 `pytest tests/` 전수).
- **동기화 필요**: T2(button)=PANEL-SCHEMA-phase2.md fixture mock 가능 / T3(btn-Codlearn)=as_of_resolver producer 후 T1 `set_as_of_resolver` wire + raw multiple(per/pbr/ev_ebitda/ps) → cheapness_z 입력.

## 산출물 (위치)
- 계약: `PANEL-SCHEMA-phase2.md` (계약1 확정 v1)
- 코드: `core/data/{__init__,pit_query,pit_panel,corp_action}.py`, `stock/data/sector_multiples.py`, `scripts/build_panel.py`
- 테스트: `tests/{test_pit_panel,test_corp_action}.py` (15 passed)
- 이연: **N-T1-SECTORMULT** (Damodaran/French49 라이브 fetch — 외부망/cache, go-live N-P4 동반) / 실 DART·EDGAR·quote 라이브 왕복 = credential(N-P4-DART/KIS) 의존, 조립 로직은 fixture 검증 완료.
