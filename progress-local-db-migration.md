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
- [ ] **L2 — 핵심 쓰기 경로 전환** (save_decision·execute_trade DB부·run_agents) · `model: opus` 🔶 진행중. ✅완전(REST=0+AST+import OK): save_decision/execute_trade/dynamic_risk. 🔶부분(DB호출 일부만, REST 잔존): run_agents.py(3 잔존:portfolio/feedback), evaluate_switches.py(3 잔존:실코드구조 불일치로 미적용), run_agents.sh(5 잔존:Phase5/5b/5c `$PYTHON -c` 블록). ⚠️**smoke 실패**: schema 재적용 버그(altrang_trades 중복, catch 보강함) + 테스트 execution_mode 오류. 재검증 필요. SACRED 실주문·run_cycle 미변경. 핸드오프=.l2-handoff.md
- [ ] **L3 — 읽기/학습 경로 전환** (dynamic_risk·strategy_health·model_retrainer·regime_learner·evaluate_switches) · `wf: harness2`
- [ ] **L4 — RL/RAG 경로** (data_collector psycopg2→sqlite, embedding numpy 코사인) · `wf: harness2`
- [ ] **L5 — 잔여 75파일 일괄 전환** · `wf: harness2`
- [ ] **L6 — 회귀 + 실구동** (run_agents·live_trader DRY_RUN SQLite, 전체 0 fail) · `model: sonnet`

## Working Notes
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
