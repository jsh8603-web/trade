-- 임베딩 통일: OpenAI 1536d → Gemini 3072d
-- decisions.state_embedding 차원 변경 + match_similar_decisions RPC 업데이트

-- 1. 기존 HNSW 인덱스 삭제 (1536d용이므로 더 이상 사용 불가)
DROP INDEX IF EXISTS idx_decisions_embedding;

-- 2. 기존 임베딩 컬럼 삭제 후 3072d로 재생성
ALTER TABLE decisions DROP COLUMN IF EXISTS state_embedding;
ALTER TABLE decisions ADD COLUMN state_embedding vector(3072);

-- 3. 유사도 검색 RPC 함수 업데이트 (1536 → 3072)
CREATE OR REPLACE FUNCTION match_similar_decisions(
  query_embedding vector(3072),
  match_limit int DEFAULT 3
)
RETURNS TABLE (
  id uuid,
  decision text,
  reason text,
  confidence decimal,
  current_price bigint,
  trade_amount bigint,
  profit_loss decimal,
  fear_greed_value integer,
  rsi_value decimal,
  created_at timestamptz,
  cycle_id text,
  source text,
  outcome_1h_pct decimal,
  outcome_4h_pct decimal,
  outcome_24h_pct decimal,
  was_correct_24h boolean,
  embedding_text text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
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
    1 - (d.state_embedding <=> query_embedding) AS similarity
  FROM decisions d
  WHERE d.state_embedding IS NOT NULL
  ORDER BY d.state_embedding <=> query_embedding
  LIMIT match_limit;
END;
$$;
