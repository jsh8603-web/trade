-- 047_b3_determinism_columns.sql
-- B3 결정성: decisions 테이블에 model_id / prompt_hash / temperature 컬럼 추가
-- Phase -1 SO-4

ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS model_id TEXT,
    ADD COLUMN IF NOT EXISTS prompt_hash TEXT,
    ADD COLUMN IF NOT EXISTS temperature NUMERIC(5,4);

COMMENT ON COLUMN decisions.model_id IS 'B3: LLM 모델 식별자 (예: gemini-2.5-flash)';
COMMENT ON COLUMN decisions.prompt_hash IS 'B3: 프롬프트 SHA256 앞 16자 — 프롬프트 변경 감지용';
COMMENT ON COLUMN decisions.temperature IS 'B3: 생성 temperature (0=결정론적)';
