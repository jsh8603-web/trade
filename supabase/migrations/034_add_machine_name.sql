-- 034: 머신별 식별자 컬럼 추가
-- 4대 컴퓨터(pc128, pc36, mac-mini, jsh8603) 동시 실행 시
-- 매매 기록 중복 방지 + 머신별 성과 비교를 위한 태그

-- 매매 결정
ALTER TABLE decisions
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

-- 포트폴리오 스냅샷
ALTER TABLE portfolio_snapshots
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

-- 에이전트 전환 이력
ALTER TABLE agent_switches
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

-- 실행 로그
ALTER TABLE execution_logs
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

-- 단타 관련
ALTER TABLE scalp_trades
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

ALTER TABLE scalp_trade_log
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

ALTER TABLE scalp_sessions
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

ALTER TABLE scalp_settlements
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

-- 김치랑
ALTER TABLE kimchirang_trades
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

ALTER TABLE kimchirang_kp_history
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

-- 외부 시그널/뉴스
ALTER TABLE external_signal_log
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

-- 훈련 관련 (머신별 성과 비교)
ALTER TABLE scalp_training_tasks
  ADD COLUMN IF NOT EXISTS machine_name TEXT;

-- 인덱스: 머신별 조회 최적화
CREATE INDEX IF NOT EXISTS idx_decisions_machine ON decisions (machine_name);
CREATE INDEX IF NOT EXISTS idx_scalp_trades_machine ON scalp_trades (machine_name);
CREATE INDEX IF NOT EXISTS idx_kimchirang_trades_machine ON kimchirang_trades (machine_name);
CREATE INDEX IF NOT EXISTS idx_scalp_sessions_machine ON scalp_sessions (machine_name);

COMMENT ON COLUMN decisions.machine_name IS '실행 머신 식별자 (pc128/pc36/mac-mini/jsh8603)';
