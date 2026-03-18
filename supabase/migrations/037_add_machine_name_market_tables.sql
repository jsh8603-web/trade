-- 037: market_data, market_context_log 테이블에 machine_name 컬럼 추가
-- 034에서 누락된 테이블 보완

ALTER TABLE market_data
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

ALTER TABLE market_context_log
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

CREATE INDEX IF NOT EXISTS idx_market_data_machine ON market_data (machine_name);
CREATE INDEX IF NOT EXISTS idx_market_context_log_machine ON market_context_log (machine_name);
