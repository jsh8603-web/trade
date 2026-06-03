---
tags: [type/handoff, domain/inv, topic/local-db-migration, session/btn-Inv]
date: 2026-05-30
session: btn-Inv
plan: ./plan-local-db-migration.md
progress: ./progress-local-db-migration.md
note: Supabase→로컬 SQLite 전환 세션 인계. 다음 세션 동등 재개용.
---

# Handoff — Supabase → 로컬 SQLite 전체 전환

## 1. 사용자 의도 (verbatim 핵심)
- "실 운영에서 Supabase 안 쓸거라서 파이프라인을 지금 변경하자. 테스트는 부수적."
- "범위가 얼마가 되었든 전체를 바꾸자. 큰 이슈 없으면."
- "로컬에서 돌릴거니까 (BGE/Qwen이 로컬이라 필수) 로컬에서 돌아가는 환경." → SQLite 선택.
- 규제로 코인 단타·차익거래(김치랑) 제외, 일반 트레이드만.

## 2. 직전 세션 완료분 (전부 commit, HEAD=6eb41d6)
- 무인 안전패치 SO-1~8 + Phase Gate E4 6건 패치(2f46607): FSM infra_hard 재집행·frozen 재시작복구·cooldown 상한·watchdog JSON guard.
- e2e P1~P4(b1076d2): automation batch 격리(SUPABASE_URL/KEY rebind), 전체 427 passed.
- 매매경로 6분할 M1~M6(6eb41d6): tests/test_trading_path_guarantee.py 18 passed.
- 설치 완료: gymnasium 1.2.3 / stable-baselines3 2.8.0 / feedparser 6.0.12 / psycopg2-binary 2.9.12 (torch 2.11 기존).

## 3. 조사 결과 (재조사 불요)
- Supabase 의존 비테스트 **75파일** (`.supadeps.txt`에 목록). REST 직접호출 65 + psycopg2 6.
- ⛔ 중앙 추상화 **없음** — 75파일이 제각각 `requests.post(SUPABASE_URL/rest/v1/{table}?{filter})`.
- psycopg2 직접: data_collector.py(RL), 그 외 5. 나머지는 REST.
- pgvector(임베딩): rag_analysis_vectors·decision_embeddings. 파일 15개(recall_rag·embedding_store·rag_pipeline·memory·feedback_hub·save_decision 등).
- 스키마: supabase/migrations/*.sql 48개, 핵심 테이블 ~40.
- config SSOT: rl_hybrid/config.py:54 SupabaseConfig. save_decision.py:288 _get_session.
- 대표 패턴: save_decision.py:321 insert(`rest/v1/{table}` POST), dynamic_risk.py:69 select(GET+params gte/in/order).
- 설치현황: SQLite 내장 OK / sqlite_vec·faiss·chromadb·lancedb 미설치 / numpy OK → 벡터는 numpy 코사인 기본.

## 4. 설계 확정 (plan §설계)
- `core/db/` 어댑터 계층: base.py(추상 insert/select/update/delete/rpc_match) + sqlite_backend.py(PostgREST필터→SQL, NOW()-INTERVAL→datetime, vector→BLOB+numpy코사인) + supabase_backend.py(레거시옵션) + schema.sql(48 migration→SQLite DDL).
- `INV_DB_BACKEND=sqlite|supabase` 스위치, 기본 sqlite. `data/inv.db`(.gitignore).
- 전환: replace-not-deprecate(75곳 REST→`db.xxx()`, 호출자 수정). 정형패턴 일괄=harness2 batch.

## 5. 재개 포인트 (다음 세션 첫 행동)
1. (권장) 자문 ⑧ DB migration: `/gemini-web`+`/claude-web` 병렬 — 어댑터 설계(PostgREST→SQLite 변환, 벡터 numpy vs sqlite-vec) 검증.
2. L0 착수: `core/db/schema.sql` 생성(supabase/migrations/*.sql 변환 — SERIAL→INTEGER AUTOINCREMENT, JSONB→TEXT, vector(N)→BLOB, timestamptz→TEXT ISO, RLS/GRANT 제거) + `core/db/base.py` + `core/db/sqlite_backend.py` 골격.
3. L1 PostgREST→SQL 변환엔진(필터 파서).
- 큰 작업이라 EnterPlanMode 거쳐 plan 승인 후 harness2 dispatch.

## 6. SACRED (불변 제약)
- ⛔ execute_trade.py 실주문 경로(body·:457 volume·:153 nonce)·rl_hybrid/rl/live_trader.py run_cycle 본체 미변경. DB 호출부(save_decision 등)만 어댑터 경유.
- DRY_RUN·EMERGENCY_STOP·MAX_TRADE_AMOUNT 안전장치 기본값 보존. 실거래 flip=사람게이트.
- R15/brain M파일 6종(README·core/brain/regime_*·portfolio_orchestrator·progress·progress-inv-v2) 격리.
- 루트 plan.md·progress.md·progress-inv-v2.md 미변경(격리 신규 파일만).
- 무인 안전패치(core/derisk_executor·unattended_fsm·watchdog·reconciliation) 회귀 0 유지.

## 7. 미해결/리스크
- execute_trade.py도 Supabase 의존(save_decision 호출)이라 DB부만 어댑터화 — 실주문 로직과 분리 주의.
- 벡터검색: rag_analysis_vectors 데이터 규모 확인 필요(크면 sqlite-vec/faiss 검토, 작으면 numpy 코사인).
- 실 운영 데이터 마이그레이션(기존 Supabase 데이터→SQLite)은 별도 — 신규 시작이면 빈 DB로 OK, 이력 필요하면 export 스크립트.
