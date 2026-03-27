-- ============================================================================
-- 046: Claude Code Brain-Inspired Memory System
--
-- 인간 뇌 기억 구조 모방:
--   short_term: 최근 7일 이내, 상세, 자주 접근
--   long_term:  7일+ 경과, 압축/병합, 필요 시 리콜
--   pinned:     절대 규칙, decay 면역
-- ============================================================================

CREATE TABLE IF NOT EXISTS claude_memories (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

  -- 분류
  memory_tier TEXT NOT NULL DEFAULT 'short_term'
    CHECK (memory_tier IN ('short_term', 'long_term')),
  category TEXT NOT NULL
    CHECK (category IN ('user', 'feedback', 'project', 'reference', 'known_issue')),

  -- 내용
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  summary TEXT,                           -- long_term 압축 요약
  tags TEXT[] DEFAULT '{}',
  source_file TEXT,                       -- 마이그레이션 원본 파일명

  -- 관련성 스코어링
  access_count INTEGER DEFAULT 0,
  last_accessed TIMESTAMPTZ,
  relevance_score FLOAT DEFAULT 1.0,      -- 1.0=fresh, 0.05=forgotten
  pinned BOOLEAN DEFAULT FALSE,           -- decay/consolidate 면역

  -- 시맨틱 검색
  embedding vector(3072),                 -- Gemini embedding-001

  -- 생명주기
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  consolidated_at TIMESTAMPTZ,
  consolidated_from UUID[],               -- 병합 원본 ID 추적

  machine_name TEXT DEFAULT 'mac-mini'
);

-- 인덱스
CREATE INDEX idx_mem_tier ON claude_memories(memory_tier);
CREATE INDEX idx_mem_category ON claude_memories(category);
CREATE INDEX idx_mem_tags ON claude_memories USING GIN(tags);
CREATE INDEX idx_mem_relevance ON claude_memories(relevance_score DESC);
CREATE INDEX idx_mem_last_accessed ON claude_memories(last_accessed DESC NULLS LAST);
CREATE INDEX idx_mem_created ON claude_memories(created_at DESC);
CREATE INDEX idx_mem_pinned ON claude_memories(pinned) WHERE pinned = TRUE;

-- RLS
ALTER TABLE claude_memories ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_all" ON claude_memories
  FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 시맨틱 검색 RPC
CREATE OR REPLACE FUNCTION match_similar_memories(
  query_embedding vector(3072),
  match_limit int DEFAULT 5,
  tier_filter text DEFAULT NULL,
  category_filter text DEFAULT NULL,
  min_relevance float DEFAULT 0.1
)
RETURNS TABLE (
  id uuid,
  memory_tier text,
  category text,
  title text,
  content text,
  summary text,
  tags text[],
  relevance_score float,
  pinned boolean,
  created_at timestamptz,
  last_accessed timestamptz,
  access_count integer,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    m.id,
    m.memory_tier,
    m.category,
    m.title,
    m.content,
    m.summary,
    m.tags,
    m.relevance_score::float,
    m.pinned,
    m.created_at,
    m.last_accessed,
    m.access_count,
    (1 - (m.embedding <=> query_embedding))::float AS similarity
  FROM claude_memories m
  WHERE m.embedding IS NOT NULL
    AND m.relevance_score >= min_relevance
    AND (tier_filter IS NULL OR m.memory_tier = tier_filter)
    AND (category_filter IS NULL OR m.category = category_filter)
  ORDER BY m.embedding <=> query_embedding
  LIMIT match_limit;
END;
$$;

-- 관련성 decay 함수 (daily-maintenance에서 호출)
CREATE OR REPLACE FUNCTION decay_memory_relevance()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE claude_memories
  SET relevance_score = GREATEST(0.05,
    CASE
      WHEN pinned THEN 1.0
      WHEN last_accessed IS NULL THEN
        POWER(0.93, EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400.0)
      ELSE
        POWER(0.95, EXTRACT(EPOCH FROM (NOW() - last_accessed)) / 86400.0)
    END
    * (1.0 + LN(GREATEST(access_count, 1)) * 0.1)
  ),
  updated_at = NOW()
  WHERE NOT pinned;
END;
$$;
