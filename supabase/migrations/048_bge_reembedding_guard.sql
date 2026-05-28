-- Phase 1 SO-3: BGE-m3 1024 재임베딩 + M4 가드
-- decisions.state_embedding(3072 Gemini) 는 유지하고
-- BGE-m3 1024 전용 컬럼/인덱스를 별도 추가.
-- reembedding_status 플래그: 재임베딩 완료 전에는 BGE 인덱스 사용 차단(M4 가드).

-- 1. BGE-m3 1024 임베딩 컬럼 추가 (idempotent)
ALTER TABLE decisions
  ADD COLUMN IF NOT EXISTS state_embedding_bge vector(1024);

-- 2. BGE HNSW 인덱스 — 재임베딩 완료 후 활성화
--    M4 가드: reembedding_status != 'completed' 시 이 인덱스를 우회하도록
--    match_similar_decisions_bge 함수가 확인.
CREATE INDEX IF NOT EXISTS idx_decisions_embedding_bge
  ON decisions
  USING hnsw (state_embedding_bge vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- 3. 재임베딩 상태 추적 테이블 (M4 가드 원천)
CREATE TABLE IF NOT EXISTS reembedding_status (
  id          serial PRIMARY KEY,
  target      text NOT NULL DEFAULT 'decisions.state_embedding_bge',
  status      text NOT NULL DEFAULT 'pending'   -- pending | in_progress | completed
    CHECK (status IN ('pending', 'in_progress', 'completed')),
  total_rows  integer,
  done_rows   integer DEFAULT 0,
  started_at  timestamptz,
  completed_at timestamptz,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

-- 초기 행 삽입 (없으면)
INSERT INTO reembedding_status (target, status)
SELECT 'decisions.state_embedding_bge', 'pending'
WHERE NOT EXISTS (
  SELECT 1 FROM reembedding_status
   WHERE target = 'decisions.state_embedding_bge'
);

-- 4. BGE 기반 유사도 검색 RPC — M4 가드 포함
--    reembedding_status.status != 'completed' → RAISE EXCEPTION (신규 인덱스 차단)
CREATE OR REPLACE FUNCTION match_similar_decisions_bge(
  query_embedding vector(1024),
  match_limit int DEFAULT 3
)
RETURNS TABLE (
  id           uuid,
  decision     text,
  reason       text,
  confidence   decimal,
  current_price bigint,
  trade_amount  bigint,
  profit_loss   decimal,
  fear_greed_value integer,
  rsi_value    decimal,
  created_at   timestamptz,
  cycle_id     text,
  source       text,
  outcome_1h_pct  decimal,
  outcome_4h_pct  decimal,
  outcome_24h_pct decimal,
  was_correct_24h boolean,
  embedding_text  text,
  similarity   float
)
LANGUAGE plpgsql
AS $$
DECLARE
  _status text;
BEGIN
  -- M4 가드: 재임베딩 미완료 시 신규 BGE 인덱스 사용 차단
  SELECT rs.status INTO _status
  FROM reembedding_status rs
  WHERE rs.target = 'decisions.state_embedding_bge'
  ORDER BY rs.id DESC
  LIMIT 1;

  IF _status IS DISTINCT FROM 'completed' THEN
    RAISE EXCEPTION 'BGE 재임베딩 미완료(status=%). match_similar_decisions_bge 사용 불가. 재임베딩 완료 후 재시도.', COALESCE(_status, 'none');
  END IF;

  RETURN QUERY
  SELECT
    d.id,
    d.decision,
    d.reason,
    d.confidence,
    d.current_price,
    d.trade_amount,
    d.profit_loss,
    d.fear_greed_value,
    d.rsi_value,
    d.created_at,
    d.cycle_id,
    d.source,
    d.outcome_1h_pct,
    d.outcome_4h_pct,
    d.outcome_24h_pct,
    d.was_correct_24h,
    d.embedding_text,
    1 - (d.state_embedding_bge <=> query_embedding) AS similarity
  FROM decisions d
  WHERE d.state_embedding_bge IS NOT NULL
  ORDER BY d.state_embedding_bge <=> query_embedding
  LIMIT match_limit;
END;
$$;

-- 5. Gemini 기반 기존 match_similar_decisions 는 그대로 유지
--    (재임베딩 완료 전까지 라이브 경로는 3072 Gemini 사용)
