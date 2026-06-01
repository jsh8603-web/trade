---
tags: [type/progress, domain/inv, topic/local-db-migration, session/btn-Inv]
date: 2026-05-30
session: btn-Inv
plan: ./plan-local-db-migration.md
handoff: ./handoff-local-db-migration-20260530.md
note: Supabase→로컬 SQLite 전환 추적. 루트 progress.md 미변경(격리 신규 파일).
---

# Progress — Supabase → 로컬 SQLite 전환

> plan: [plan-local-db-migration.md](./plan-local-db-migration.md) · 인계: [handoff-local-db-migration-20260530.md](./handoff-local-db-migration-20260530.md)

## §진입 스냅샷
- 사용자 확정: 실 운영 Supabase 미사용 → 로컬 SQLite 전체 전환(범위 무관 전체). BGE/Qwen 로컬과 정합.
- 조사 완료: 75 비테스트 파일 Supabase 의존(REST 65+psycopg2 6), 중앙추상화 없음. SQLite 내장 OK, numpy 코사인 벡터.
- 설계 확정: core/db/ 어댑터 계층(base/sqlite_backend/supabase_backend/schema.sql) + INV_DB_BACKEND 스위치.
- 다음: L0 스키마 추출+골격. 자문 ⑧(DB migration) 권장. 큰 작업=harness2.
- ⛔ SACRED: execute_trade 실주문 로직·live_trader run_cycle 본체 미변경(DB 호출부만 어댑터화). DRY_RUN 유지.

## Steps
- [x] **L0 — 스키마 추출 + 어댑터 골격** · `model: opus` ✅ (commit 4e67b0f)
  - scripts/build_sqlite_schema.py: migrations 50 → core/db/schema.sql 48테이블, **failures=0** (재생성 결정론, diff=0)
  - core/db/: base(추상) + filters(PostgREST→SQL) + sqlite_backend(+numpy 벡터) + supabase_backend(레거시) + __init__(INV_DB_BACKEND 스위치)
  - tests/test_db_adapter_smoke.py **7 passed**
  - ⚠️ python 경로 = `C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe` (PATH에 `python` 없음 — bash `python` 호출 시 command not found)
- [x] **L1 — PostgREST→SQL 변환 엔진** · `model: opus` ✅ (L0에 통합, core/db/filters.py)
  - eq/ne/gt/gte/lt/lte/like/ilike/in/is/not + order(.desc/.asc) 변환. NOW()-INTERVAL은 caller가 ISO 문자열로 전달(어댑터 규약). test_filter_operators/test_order passed
- [x] **L2 — 핵심 쓰기 경로 전환** (save_decision·execute_trade DB부·run_agents) · `model: opus` ✅ (commit b459d87) 6파일 전부 REST=0+AST OK(2회 일관)+module import OK+**round-trip PASS**(save_decision→SQLite id 발급, execution_logs 저장/조회). schema 재적용 버그 수정(already another table or index catch). SACRED 보존: execute_trade 실주문 orders/JWT·live_trader run_cycle 미변경. 핸드오프=.l2-handoff.md
- [ ] **L3 — 읽기/학습 경로 전환** (dynamic_risk·strategy_health·model_retrainer·regime_learner·evaluate_switches) · `wf: harness2`
- [ ] **L4 — RL/RAG 경로** (data_collector psycopg2→sqlite, embedding numpy 코사인) · `wf: harness2`
- [ ] **L5 — 잔여 75파일 일괄 전환** · `wf: harness2`
- [ ] **L6 — 회귀 + 실구동** (run_agents·live_trader DRY_RUN SQLite, 전체 0 fail) · `model: sonnet`

## Working Notes
> [ckpt-202606010630:btn-Inv] **★★ SQLite 전환 100% 완결 (잔여 전부 처리)**
> - **완료**: (1) v_뷰 11개 `core/db/views.sql` sidecar 이식 (commit) — build_sqlite_schema.py 가 변환기 재생성 시에도 보존하도록 배선. PG→SQLite 변환(COUNT FILTER→SUM CASE, LATERAL→상관서브쿼리, ::type→CAST, bool→1/0). (2) timestamp 예약어 버그 수정(타입치환 regex lookbehind+quote). (3) performance_reviews 최소 스키마. (4) **run_agents.sh DRY_RUN e2e: SQLite/Supabase/psycopg2 에러 0, inv.db 생성+decisions/execution_logs 기록 확인** = 매매 파이프라인 로컬 DB 완주. pytest 37 유지(회귀 0).
> - **최종 상태**: 전 프로젝트 rest/v1=0, psycopg2=0. pytest 82→37(baseline 48 이하, DB 신규 fail 0). 매매 e2e SQLite 정상. **전체 SQLite 전환 완결**.
> - **잔여(미미, 별도 과제)**: v_tag_index(원본 정의 부재+PG cs 문법, recall `tag` 1명령만 영향) / 환경 fail 37(qrcode·msgpack·credential·ollama·playwright 미설치 = 사용자 환경 설정, DB 무관) / agent_switches RL학습 컬럼(data_collector graceful [] 처리).

> [ckpt-202606010600:btn-Inv] **★ 전체 이관 완료 — rest/v1=0, psycopg2=0, pytest 82→37 (baseline 48 이하, DB 신규 fail 0)**
> - **마지막 결정**: 배치1(25모듈 commit da96578) + 배치2(rl_hybrid/scalp_ml/train/psycopg2 27모듈 commit 9d656c3) + admin/r2 test 갱신(커밋됨) 완료. **전체 프로젝트 rest/v1=0, psycopg2=0**. 최종 pytest **37 fail** = 전부 사전존재 환경/flaky known (so5_kis credential 7·so3_macro apikey 4·dashboard qrcode 4·build* 7·so6/so7 gate 6·so1 ollama 1·so4 1·capture_chart playwright 1·execute_trade Upbit네트워크 2·kimchirang_e2e 라이브 2·e2e 자정경계 flaky 2). **DB 이관으로 새로 깨진 test 0** (82→37, 45개 해소, baseline 48 이하). 어댑터 일괄정상화(neq/시간datetime/boolean/TEXT-PK-uuid)로 19+27 모듈 시간·boolean·neq 일괄 커버.
> - **다음 의도 (잔여 — 핵심 회귀와 무관)**: (1) **v_뷰 12개 schema.sql 이식** — build_sqlite_schema.py 가 CREATE VIEW 의도적 제외(0개), recall/retrospective(CLI 조회 도구)가 v_* 를 db.select 하면 OperationalError. pytest(mock 통과)·매매 e2e(매매경로는 뷰 미사용)와 무관하나 recall/retrospective CLI 실행 시 필요. (2) **스키마 갭**: system_health_logs.timestamp(예약어)·performance_reviews 테이블 결측·agent_switches 일부 컬럼(data_collector RL학습 PG원본 조회, graceful [] 처리됨). (3) run_agents.sh DRY_RUN 전체 e2e 미실행(외부 API 의존). 매매 DB round-trip(save_decision id발급·dynamic_risk fetch·orchestrator switch)은 개별 검증 완료.
> - **동기화 필요**: long-mode ON. python=Python312. core/brain·portfolio·risk_gate M=peer 미커밋(SACRED 격리, 미변경). 커밋 체인: b5e0583(L3일부)→fc98e7c(어댑터정상화)→3d0db24(decision라벨)→8a40c2c(배치A)→11435e3(test갱신)→da96578(배치1)→9d656c3(배치2)→admin/r2.

> [ckpt-202606010230:btn-Inv] **L3 잔여 이관 + 어댑터 일괄 정상화 + 깨진 test 갱신 (pytest 82→37, baseline 48 이하)**
> - **마지막 결정**: (1) 어댑터 일괄 정상화 `core/db/{filters,sqlite_backend}.py` (commit fc98e7c): neq 연산자 추가 / 시간컬럼(*_at·*_time) `datetime()` 정규화(PG timestamptz→SQLite TEXT 비교 깨짐) / boolean `eq.true/false`→1/0 / TEXT PK uuid4 자동주입. (2) decision 라벨 한국어 복구 dynamic_risk·phase_cache·strategy_health (commit 3d0db24): DB 저장은 한국어(매수/매도, CHECK 강제)인데 조회 필터 영문 buy/sell이라 항상 0건이던 휴면버그. dynamic_risk SUPABASE 가드 잔재 제거. (3) 배치A 11모듈 이관 (commit 8a40c2c): recall/memory/model_retrainer/auto_learner/regime_learner/model_diversity/feedback/feedback_hub/nl_feedback/retrospective/coin_track. (4) 깨진 test 52개 db mock 갱신 (commit 11435e3): requests.get/patch/post→core.db.db.* mock, 검증 의도 보존. **pytest 82→37 fail (남은 37=환경known: qrcode 미설치/credential/ollama/build/자정경계 flaky, DB 무관)**.
> - **다음 의도**: 남은 **49 rest/v1 + 5 psycopg2** 모듈 이관 (대응 test 동반 갱신). 배치1(G5 일회성·G6 agents/telegram/worker_admin/기타/lifeline) → 배치2(G3 rl_hybrid psycopg2 ★live_trader run_cycle SACRED·G4 scalp_ml·train_*·recall_rag). 이후 **v_뷰 12개 schema.sql 이식**(recall/retrospective는 test mock으로 통과하나 실 조회는 OperationalError — supabase/migrations 의 CREATE VIEW 미이식) → **최종 48 회귀 + run_agents.sh DRY_RUN e2e**.
> - **동기화 필요**: long-mode ON(cap 500k). python=`C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`. core/brain·portfolio_orchestrator·risk_gate M = peer 미커밋(SACRED R15/brain 격리, 미변경). 어댑터 일괄정상화로 이미 이관된 19모듈+향후 전부 시간/boolean/neq 커버됨. test 갱신 패턴=`<module>.db.<method>` 또는 `core.db.db.<method>` mock.

> [ckpt-202605311400:btn-Inv] **L0/L1 완료**
> - **마지막 결정**: L0/L1 실제 완료 + 커밋 (HEAD=7b22f2e). 산출물: scripts/build_sqlite_schema.py(변환기) + core/db/{base,filters,sqlite_backend,supabase_backend,__init__}.py(어댑터 6파일) + core/db/schema.sql(48테이블, failures=0, 재생성 결정론) + tests/test_db_adapter_smoke.py(**10 passed**: CRUD/PostgREST필터/JSON/벡터코사인). INV_DB_BACKEND=sqlite 기본.
> - **다음 의도**: L2 착수 — 핵심 쓰기 경로 전환. save_decision.py(311줄, 순수 Supabase REST 확인됨)의 `_post_with_retry`→`db.insert("decisions",...)`, execute_trade DB호출부, run_agents. **L2~L5는 75파일 정형 전환 = harness2 위임 권장** (plan §실행엔진). 전환 패턴: `from core.db import db` 후 `requests.post(SUPABASE_URL/rest/v1/{table})` → `db.insert(table, row)`, GET+params(gte/in/order) → `db.select(table, filters={...}, order=..., limit=...)`.
> - **동기화 필요**: ⚠️ **python 경로 = `C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`** (bash `python` = command not found, 이게 직전 세션 4h 손실 root cause). pytest = `<위경로> -m pytest`. ⚠️ 이 세션 도구출력 간헐 손상(internal error) — L2 정밀전환은 도구 안정 후. SACRED 유지: execute_trade 실주문로직·live_trader run_cycle 본체 미변경(DB호출부만), R15/brain M파일 6종 격리. peer btn-button fabda53 stale — L2 전 git pull --rebase 검토.

> [ckpt-202605302010:btn-Inv]
> - **마지막 결정**: Supabase→로컬 SQLite 전체 전환 설계 확정. core/db/ 어댑터 계층(base 추상 insert/select/update/delete/rpc_match + sqlite_backend PostgREST필터→SQL변환 + supabase_backend 레거시옵션 + schema.sql). INV_DB_BACKEND=sqlite 기본. 벡터=numpy 코사인. 의존 75파일·중앙추상화 부재 조사 완료. plan/progress/handoff 작성. long-mode MAX, ctx 89% 강제compact 임박.
> - **다음 의도**: L0 착수 — supabase/migrations/*.sql 48개 → core/db/schema.sql(SQLite DDL: SERIAL→INTEGER AUTOINCREMENT, JSONB→TEXT, vector→BLOB, timestamptz→TEXT ISO, RLS제거) + core/db/base.py 인터페이스 + sqlite_backend 골격. 그 전 자문 ⑧(gemini+claude 병렬, 어댑터 설계 검증) 권장.
> - **동기화 필요**: 직전 완료분 모두 commit됨(HEAD 6eb41d6 매매경로 6분할). 무인 안전패치(SO-1~8+E4)·e2e(P1~P4)·매매경로(M) 다 끝남. 미커밋 = plan/progress-local-db-migration.md(신규). 설치됨: gymnasium/sb3/feedparser/psycopg2. RL run_cycle은 실 SUPABASE_DB_URL 필요해 이 전환이 그것도 해소. SACRED: execute_trade 실주문·live_trader run_cycle 본체 미변경, R15/brain M파일 6종 격리 유지.
- (2026-05-30) 조사: REST 패턴 정형(rest/v1/{table}?{filter}), save_decision:321 insert·dynamic_risk:69 select 대표. config.py:54 SupabaseConfig SSOT.

> [ckpt-202605311600:btn-Inv] **L2 완료 — 매매 핵심 경로 6파일 SQLite 전환 + smoke 검증**
> - **완료**: save_decision/execute_trade/dynamic_risk/run_agents.py/run_agents.sh/evaluate_switches → `from core.db import db` + REST(requests.post/get/patch)→db.insert/select/update. 전부 REST=0+AST OK. **smoke**: INV_DB_BACKEND=sqlite 로 save_decision(sample)→decisions id=1 INSERT(매핑·정규화 정상)+execution_logs+SELECT 정상, data/inv.db 생성. **매매 파이프라인 로컬 실동작 확인**. SACRED 보존: execute_trade 실주문 orders POST·JWT·live_trader run_cycle 미변경.
> - **다음**: L3~L5 = 남은 ~44 REST 파일(strategy_health/model_retrainer/regime_*/recall_rag/feedback*/report*/rl_hybrid psycopg2 6/scalp_ml/train_*/collect_*/통합·기타) + L6 회귀(run_agents.sh DRY_RUN e2e + pytest). 전환규약·그룹분류·SACRED 전부 **.l2-handoff.md** 박제.
> - **동기화**: python=`C:/Users/jsh86/AppData/Local/Programs/Python/Python312/python.exe`. ⚠️ 이 세션 (1)Agent 서브 채널 사망(8회 internal error→메인 직접만) (2)도구출력 간헐 손상(grep/Read truncate→정확 Read 후 Edit+매번 grep 재검증). 도구·Agent 회복된 새 세션이면 .l2-handoff.md 규약으로 G1~G6 서브 병렬 가속 가능.
