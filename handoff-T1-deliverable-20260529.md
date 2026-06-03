---
tags: [type/handoff, domain/inv, phase/II, track/T1]
date: 2026-05-29
session: btn-Inv
spec: ./SPEC-T1-data-pit.md
schema: ./PANEL-SCHEMA-phase2.md
progress: ./progress-T1-data-pit.md
consumer: [T2 btn-button, T3 btn-Codlearn]
status: Phase1~3 완주 — 계약1 확정 + 조립층 구현 + 검증 15/15 PASS (회귀 0)
---

# T1 인계 — bitemporal PIT 패널 (T2/T3 소비용)

> btn-Inv(T1) → T2(btn-button)·T3(btn-Codlearn). 핵심 = rule·구조모델이 딛고 설 "땅". 이 층 오염되면 위 전부 허상(look-ahead).
> ⚠️ "바닥부터"가 아니라 기존 provider(dart/edgar/krx/macro_vintage·walk_forward) **조립**. SACRED: 기존 소스 0수정(전부 신규 파일).

## 계약1 — panel schema (확정 v1, SSOT = PANEL-SCHEMA-phase2.md)

`panel/{market}/{vintage}.parquet`, market∈{KR,US}, vintage=content-hash. 48컬럼.

**bitemporal 3축 (PIT 핵심)**:
- `effective_from` = 회계기간 적용 시작 (fiscal period end)
- `knowable_from` = 공시 시점 = filing_timestamp. **PIT 게이트 키** (≤ as_of)
- `sys_time` = 값 버전 기록 시점. 기본 = knowable_from. **silent revision 시에만** 정정 시점으로 새 row append(불변식② append-only). ⚠️ build 시각 쓰면 안 됨(미래 빌드가 과거 백테스트 차단).

기타: firm·date·sector(as-of)·sector_scheme·sector_valid_from / features 20종(Fundamentals 매핑)·fiscal_period·filing_source(restated 거부)·currency·is_pit_clean / multiple 4종(per·pbr·ev_ebitda·ps)·multiple_def_version(R8 GAAP drift) / delist_flag·delist_date·delist_ret(Shumway) / regime_id·regime_model_version(**T1=NULL, T2 producer**) / KR 상태 6종.

## ★ T2 schema와의 정합 (btn-button 인계 대조)

T2 `core/structure/panel_schema.py` 필수 컬럼 ⊆ T1 panel:
| T2 요구 | T1 제공 | 비고 |
|---|---|---|
| firm·sector·date·knowable_from·regime_id | ✅ 동일 | regime_id=T1 NULL→T2 채움(합의대로) |
| multiple·multiple_def_version | ✅ per/pbr/ev_ebitda/ps + multiple_def_version | T2 가 archetype별 primary_metric 선택 |
| delist_flag·delist_ret | ✅ 동일(+delist_date) | survivorship |
| `drv_*` 드라이버 prefix | ⚠️ **미발행** — T1 features(revenue 등 raw)는 있으나 `drv_` 가공은 T2 몫 | T2 가 raw feature→drv_ 파생 |

→ **drv_ 파생만 T2 책임**, 나머지 계약1 전부 충족. T2 mock(`semiconductor_panel_v1.parquet`)과 컬럼명 호환(firm/sector/date/knowable_from/multiple/delist_*).

## 계약0 — canonical as_of resolver (T3 SSOT, T1은 seam만)

`core/data/pit_query.py:set_as_of_resolver(resolver)`. T1은 as_of 자체 해석 안 함(R7 reconcile 발산 방지). T3가 resolver 구현 → 이 1곳 wire. 미주입 시 항등(passthrough, ⚠️production 금지). **T2도 동일 계약0 대기 중** — T3 resolver 1개를 T1·T2 양쪽에 주입하면 3트랙 as_of 의미론 통일.

## 산출물 파일 (위치)
- 계약: `PANEL-SCHEMA-phase2.md`
- 코드: `core/data/{__init__,pit_query,pit_panel,corp_action}.py` · `stock/data/sector_multiples.py` · `scripts/build_panel.py`
- 테스트: `tests/{test_pit_panel,test_corp_action}.py` (15 passed)
- 산출 예: `panel/KR/empty.parquet` + `panel/_manifest/empty.json` (credential 부재 빈 패널 — 스키마/manifest 경로 검증용)

## API 요약 (T2/T3 소비)
```python
from core.data.pit_query import PitPanel, set_as_of_resolver
pp = PitPanel.load("panel/KR/<vintage>.parquet")
view = pp.as_of(as_of)              # as_of 시점 PIT-correct 전체 슬라이스(firm/date별 최신 sys_time)
row  = pp.query(firm, date, as_of)  # 단일 (firm,date) PIT row
set_as_of_resolver(t3_resolver)     # 계약0 wire (T3 도착 시)

from core.data.pit_panel import PanelAssembler, RoutingFundamentalsProvider
# 조립: dart/edgar→Fundamentals(RESTATED 거부)→filter_pit_fundamentals→bitemporal 3축
```

## 검증 (Phase 3)
- 15/15 PASS: RESTATED 거부 / filing-lag PIT / look-ahead 0 / silent revision 재현 / survivorship 상폐포함 / as_of_resolver seam / multiples / corp_action.
- **회귀 0**: 전체 48 failed = `tests/KNOWN_FAILURES.md` 박제 집합과 파일별 정확히 일치(신규 실패 0). T1=신규 파일만, 기존 소스 0수정.

## 이연 (go-live 의존, N-P4 패턴)
- **N-T1-SECTORMULT**: Damodaran/French49 라이브 fetch — 외부망/offline cache. 조립 로직은 fixture 검증 완료.
- 실 DART/EDGAR/quote 라이브 왕복 = credential(N-P4-DART/KIS/FRED). PanelAssembler 조립 로직은 fixture provider 로 검증, credential 부재 시 빈 패널 graceful degrade.

## T2/T3 가 이어서 할 것
1. **T3**: canonical as_of resolver 구현 → `set_as_of_resolver()` (T1) + `StructureModel(as_of_resolver=)` (T2) 양쪽 주입.
2. **T2**: 실패널 도착 시 raw feature→`drv_` 파생 + `run_validation(panel=실패널)` STOP gate 재실행.
3. **T3**: RuleProvider 가 `pp.query()` 로 패널 조회 → cheapness_z 입력. raw multiple(per/pbr/ev_ebitda/ps) 준비됨.
