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
- [ ] **L0 — 스키마 추출 + 어댑터 골격** · `model: opus` (설계)
- [ ] **L1 — PostgREST→SQL 변환 엔진** · `model: opus`
- [ ] **L2 — 핵심 쓰기 경로 전환** (save_decision·execute_trade DB부·run_agents) · `wf: harness2`
- [ ] **L3 — 읽기/학습 경로 전환** (dynamic_risk·strategy_health·model_retrainer·regime_learner·evaluate_switches) · `wf: harness2`
- [ ] **L4 — RL/RAG 경로** (data_collector psycopg2→sqlite, embedding numpy 코사인) · `wf: harness2`
- [ ] **L5 — 잔여 75파일 일괄 전환** · `wf: harness2`
- [ ] **L6 — 회귀 + 실구동** (run_agents·live_trader DRY_RUN SQLite, 전체 0 fail) · `model: sonnet`

## Working Notes
> [ckpt-202605302010:btn-Inv]
> - **마지막 결정**: Supabase→로컬 SQLite 전체 전환 설계 확정. core/db/ 어댑터 계층(base 추상 insert/select/update/delete/rpc_match + sqlite_backend PostgREST필터→SQL변환 + supabase_backend 레거시옵션 + schema.sql). INV_DB_BACKEND=sqlite 기본. 벡터=numpy 코사인. 의존 75파일·중앙추상화 부재 조사 완료. plan/progress/handoff 작성. long-mode MAX, ctx 89% 강제compact 임박.
> - **다음 의도**: L0 착수 — supabase/migrations/*.sql 48개 → core/db/schema.sql(SQLite DDL: SERIAL→INTEGER AUTOINCREMENT, JSONB→TEXT, vector→BLOB, timestamptz→TEXT ISO, RLS제거) + core/db/base.py 인터페이스 + sqlite_backend 골격. 그 전 자문 ⑧(gemini+claude 병렬, 어댑터 설계 검증) 권장.
> - **동기화 필요**: 직전 완료분 모두 commit됨(HEAD 6eb41d6 매매경로 6분할). 무인 안전패치(SO-1~8+E4)·e2e(P1~P4)·매매경로(M) 다 끝남. 미커밋 = plan/progress-local-db-migration.md(신규). 설치됨: gymnasium/sb3/feedparser/psycopg2. RL run_cycle은 실 SUPABASE_DB_URL 필요해 이 전환이 그것도 해소. SACRED: execute_trade 실주문·live_trader run_cycle 본체 미변경, R15/brain M파일 6종 격리 유지.
- (2026-05-30) 조사: REST 패턴 정형(rest/v1/{table}?{filter}), save_decision:321 insert·dynamic_risk:69 select 대표. config.py:54 SupabaseConfig SSOT.
