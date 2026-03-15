-- 031: FK 제약 일관성 수정
-- buy_score_detail, market_context_log, external_signal_log에 decision_id FK 추가
-- 모든 decision_id FK를 ON DELETE SET NULL로 통일

-- 1) buy_score_detail: decision_id FK 추가
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'buy_score_detail_decision_id_fkey'
  ) THEN
    ALTER TABLE buy_score_detail
      ADD CONSTRAINT buy_score_detail_decision_id_fkey
      FOREIGN KEY (decision_id) REFERENCES decisions(id) ON DELETE SET NULL;
  END IF;
END $$;

-- 2) market_context_log: decision_id FK 추가
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'market_context_log_decision_id_fkey'
  ) THEN
    ALTER TABLE market_context_log
      ADD CONSTRAINT market_context_log_decision_id_fkey
      FOREIGN KEY (decision_id) REFERENCES decisions(id) ON DELETE SET NULL;
  END IF;
END $$;

-- 3) external_signal_log: decision_id FK 추가
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'external_signal_log_decision_id_fkey'
  ) THEN
    ALTER TABLE external_signal_log
      ADD CONSTRAINT external_signal_log_decision_id_fkey
      FOREIGN KEY (decision_id) REFERENCES decisions(id) ON DELETE SET NULL;
  END IF;
END $$;

-- 4) execution_logs: 기존 FK를 ON DELETE SET NULL로 변경
DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'execution_logs_decision_id_fkey'
    AND table_name = 'execution_logs'
  ) THEN
    ALTER TABLE execution_logs DROP CONSTRAINT execution_logs_decision_id_fkey;
    ALTER TABLE execution_logs
      ADD CONSTRAINT execution_logs_decision_id_fkey
      FOREIGN KEY (decision_id) REFERENCES decisions(id) ON DELETE SET NULL;
  END IF;
END $$;

-- 5) 성능 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_decisions_created_at_source
  ON decisions(created_at DESC, source);

CREATE INDEX IF NOT EXISTS idx_market_context_log_decision_id
  ON market_context_log(decision_id, recorded_at);
