-- 037: machine_name 컬럼이 누락된 테이블들에 추가
-- PC36 등 여러 머신에서 실행 시 데이터 출처 추적용

ALTER TABLE scalp_market_snapshot ADD COLUMN IF NOT EXISTS machine_name TEXT;
ALTER TABLE signal_attempt_log ADD COLUMN IF NOT EXISTS machine_name TEXT;
ALTER TABLE news_sentiment_log ADD COLUMN IF NOT EXISTS machine_name TEXT;

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_scalp_market_snapshot_machine ON scalp_market_snapshot(machine_name);
CREATE INDEX IF NOT EXISTS idx_signal_attempt_log_machine ON signal_attempt_log(machine_name);
