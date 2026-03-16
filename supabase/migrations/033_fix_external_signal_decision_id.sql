-- 033: external_signal_log에 decision_id 컬럼 추가
-- 031에서 FK를 걸었으나 컬럼 자체가 누락되어 있었음

ALTER TABLE external_signal_log
  ADD COLUMN IF NOT EXISTS decision_id UUID REFERENCES decisions(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_external_signal_log_decision_id
  ON external_signal_log(decision_id);

-- telegram_contacts / telegram_messages RLS 활성화 (030에서 누락)
ALTER TABLE telegram_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_messages ENABLE ROW LEVEL SECURITY;
