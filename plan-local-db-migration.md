---
tags: [type/plan, domain/inv, topic/local-db-migration, session/btn-Inv]
date: 2026-05-30
session: btn-Inv
handoff: ./handoff-local-db-migration-20260530.md
note: Supabase(원격) → 로컬 SQLite 전체 전환. 실 운영 로컬화(BGE/Qwen 로컬 필수와 정합). 루트 plan.md 미변경(격리 신규 파일).
---

# Plan — Supabase → 로컬 SQLite 전체 전환

> 인계: [handoff-local-db-migration-20260530.md](./handoff-local-db-migration-20260530.md)
> 사용자 확정(2026-05-30): "실 운영에서 Supabase 안 씀 → 로컬에서 돌아가는 환경으로 파이프라인 전체 변경. 범위 무관 전체. BGE/Qwen 로컬이라 DB도 로컬 필수."

## 목표
원격 Supabase(PostgreSQL+pgvector+REST) 의존을 전부 제거하고 **로컬 SQLite 단일 DB**로 운영. 임베딩 검색은 numpy 코사인(decisions 규모 충분, sqlite-vec 옵션). 실 운영 완전 로컬화.

## 현황 (조사 완료 2026-05-30)
- **Supabase 의존 = 75개 비테스트 파일.** REST 직접호출 65 + psycopg2 6.
- ⛔ **중앙 추상화 계층 없음** (`db_writer.py` 부재, DBWRITER_IMPORTERS=0). 75파일이 제각각 `requests.post(SUPABASE_URL/rest/v1/...)` 직접 호출.
- 스키마 = `supabase/migrations/*.sql` 48개 파일, 핵심 테이블 ~40개 (decisions·portfolio_snapshots·market_data·feedback·execution_logs·strategy_history·agent_switches·external_signal_log·rag_analysis_vectors·rl_training_* 등).
- pgvector 사용 = rag_analysis_vectors(임베딩 검색), decision_embeddings. 파일: recall_rag·embedding_store·rag_pipeline·memory·feedback_hub·save_decision 등 15개.
- 공통헬퍼 `scripts/supabase_query.py`(176줄, execute_sql) 존재하나 사용처 2개뿐.
- 설정 SSOT: `rl_hybrid/config.py:54 SupabaseConfig`(url/service_role_key/db_url). save_decision.py:288 `_get_session()` requests.Session 풀.
- SQLite 내장 OK. sqlite_vec/faiss/chromadb/lancedb 미설치. numpy OK → 코사인 검색 기본.

## 설계 (확정)
### 어댑터 계층 신설 — `core/db/`
- `core/db/__init__.py` — 백엔드 스위치(`INV_DB_BACKEND=sqlite|supabase`, 기본 sqlite)
- `core/db/base.py` — 추상 인터페이스: `insert(table, row)` / `select(table, filters, order, limit)` / `update(table, filters, patch)` / `delete` / `rpc_match(table, embedding, k)` (벡터검색)
- `core/db/sqlite_backend.py` — SQLite 구현. PostgREST 필터문법(`gte.`/`in.(...)`/`eq.`) → SQL WHERE 변환. `NOW() - INTERVAL` → datetime. 벡터 = BLOB(float32) + numpy 코사인 top-k.
- `core/db/supabase_backend.py` — 기존 REST 래핑(레거시 옵션 보존, replace-not-deprecate 원칙상 호출자 전환).
- `core/db/schema.sql` — supabase/migrations 48개를 SQLite DDL로 통합(SERIAL→INTEGER AUTOINCREMENT, JSONB→TEXT, vector→BLOB, timestamptz→TEXT ISO, RLS 제거).
- `data/inv.db` — 로컬 SQLite 파일(.gitignore).

### 전환 원칙
- replace-not-deprecate: REST 직접호출 75곳 → `from core.db import db; db.insert(...)` 로 교체, 호출자도 수정.
- PostgREST 필터 패턴이 정형적이라 대규모 일괄(grep 패턴 동일) → harness2 batch 적합.
- ⛔ SACRED: execute_trade.py 실주문 경로(body·:457·:153)·live_trader run_cycle 본체 미변경. 단 execute_trade도 Supabase 의존(save_decision 호출)이라 DB 호출부만 어댑터 경유로(실주문 로직 불변). DRY_RUN·안전장치 기본값 보존.
- 회귀: 기존 e2e(202)+무인(74)+매매경로(18) 테스트가 mock이라 어댑터 경유로 재배선 후 통과 유지.

## 작업 단계 (Phase)
### L0 — 스키마 추출 + 어댑터 골격
- supabase/migrations/*.sql → core/db/schema.sql(SQLite DDL). core/db/base.py 인터페이스 + sqlite_backend 골격.
### L1 — PostgREST→SQL 변환 엔진
- 필터문법 파서(gte/lte/eq/in/like/order/select/limit) → SQL. NOW()-INTERVAL·::text·RealDictCursor 대응.
### L2 — 핵심 쓰기 경로 전환 (save_decision·execute_trade·run_agents)
- decisions/portfolio_snapshots/execution_logs insert 어댑터화. 라이브 파이프라인 우선.
### L3 — 읽기/학습 경로 전환 (dynamic_risk·strategy_health·model_retrainer·regime_learner·evaluate_switches·orchestrator 학습)
### L4 — RL/RAG 경로 전환 (data_collector psycopg2→sqlite, embedding_store/recall_rag 벡터 numpy 코사인)
### L5 — 잔여 75파일 일괄 전환 (backtest·collect_*·lifeline·feedback·memory·telegram 등)
### L6 — 회귀 + 실구동 (run_agents.py·live_trader run_cycle DRY_RUN SQLite로 끝까지, 전체 테스트 0 fail)

## 검증 게이트
- 각 L단계: 전환 파일 단위 테스트 통과 + SQLite 실파일 read/write 확인.
- L6: run_agents EXIT=0(SQLite), live_trader run_cycle 도달(실 DB 없이), 전체 회귀 0 fail.
- ⛔ execute_trade 실주문 로직 diff 최소(DB 호출부만), DRY_RUN 유지.

## 실행 엔진
- L0/L1 = opus 설계(추상화·변환엔진 핵심). L2~L5 = harness2(대규모 정형 일괄, 회귀민감). L6 = 검증.
- 자문 트리거 ⑧(Risk 변경: DB migration) 해당 → L0 착수 전 gemini+claude 병렬 자문 권장(어댑터 설계 검증).

## 자율주행
- progress-local-db-migration.md 완료까지 자율. 발견 즉시 패치. 실거래 flip·실주문=사람게이트(범위 밖).
