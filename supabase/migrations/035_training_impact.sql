-- 035: 훈련 효과 추적 — rl_training_cycles에 사후 PnL 컬럼 + 뷰
-- 자율 학습 루프: 훈련 후 실제 포트폴리오 변화를 추적하여 효과 측정

-- 1) rl_training_cycles에 훈련 후 PnL 추적 컬럼 추가
ALTER TABLE rl_training_cycles
  ADD COLUMN IF NOT EXISTS pnl_24h_after double precision,
  ADD COLUMN IF NOT EXISTS pnl_72h_after double precision,
  ADD COLUMN IF NOT EXISTS training_meta jsonb DEFAULT '{}';

COMMENT ON COLUMN rl_training_cycles.pnl_24h_after IS '훈련 완료 후 24시간 포트폴리오 PnL (%)';
COMMENT ON COLUMN rl_training_cycles.pnl_72h_after IS '훈련 완료 후 72시간 포트폴리오 PnL (%)';
COMMENT ON COLUMN rl_training_cycles.training_meta IS '메타 결정 이유 (왜 이 훈련을 선택했는지)';

-- 2) 알고리즘별 훈련 효과 집계 뷰
CREATE OR REPLACE VIEW v_training_impact AS
SELECT
  algorithm,
  COUNT(*) AS total_trainings,
  COUNT(pnl_24h_after) AS measured_count,
  ROUND(AVG(pnl_24h_after)::numeric, 4) AS avg_pnl_24h,
  ROUND(AVG(pnl_72h_after)::numeric, 4) AS avg_pnl_72h,
  ROUND(AVG(avg_sharpe)::numeric, 4) AS avg_sharpe,
  ROUND(
    (COUNT(*) FILTER (WHERE pnl_24h_after > 0))::numeric
    / NULLIF(COUNT(pnl_24h_after), 0),
    4
  ) AS improved_rate,
  MAX(completed_at) AS last_trained_at
FROM rl_training_cycles
WHERE status = 'completed'
  AND created_at > NOW() - INTERVAL '30 days'
GROUP BY algorithm
ORDER BY improved_rate DESC NULLS LAST;

COMMENT ON VIEW v_training_impact IS '알고리즘별 훈련 효과 집계 (최근 30일)';

-- 3) 훈련 후 PnL 자동 업데이트용 함수
-- 24시간/72시간 후 portfolio_snapshots와 비교하여 PnL 계산
CREATE OR REPLACE FUNCTION update_training_pnl()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
  rec RECORD;
  snap_before double precision;
  snap_after_24h double precision;
  snap_after_72h double precision;
BEGIN
  FOR rec IN
    SELECT id, completed_at
    FROM rl_training_cycles
    WHERE status = 'completed'
      AND completed_at IS NOT NULL
      AND pnl_24h_after IS NULL
      AND completed_at < NOW() - INTERVAL '24 hours'
    LIMIT 20
  LOOP
    -- 훈련 직전 포트폴리오 스냅샷
    SELECT total_evaluation INTO snap_before
    FROM portfolio_snapshots
    WHERE created_at <= rec.completed_at
    ORDER BY created_at DESC
    LIMIT 1;

    -- 24시간 후 스냅샷
    SELECT total_evaluation INTO snap_after_24h
    FROM portfolio_snapshots
    WHERE created_at >= rec.completed_at + INTERVAL '24 hours'
    ORDER BY created_at ASC
    LIMIT 1;

    -- 72시간 후 스냅샷
    SELECT total_evaluation INTO snap_after_72h
    FROM portfolio_snapshots
    WHERE created_at >= rec.completed_at + INTERVAL '72 hours'
    ORDER BY created_at ASC
    LIMIT 1;

    IF snap_before IS NOT NULL AND snap_before > 0 THEN
      UPDATE rl_training_cycles
      SET
        pnl_24h_after = CASE
          WHEN snap_after_24h IS NOT NULL
          THEN ROUND(((snap_after_24h - snap_before) / snap_before * 100)::numeric, 4)
          ELSE NULL
        END,
        pnl_72h_after = CASE
          WHEN snap_after_72h IS NOT NULL
          THEN ROUND(((snap_after_72h - snap_before) / snap_before * 100)::numeric, 4)
          ELSE NULL
        END
      WHERE id = rec.id;
    END IF;
  END LOOP;
END;
$$;

COMMENT ON FUNCTION update_training_pnl() IS '훈련 후 24h/72h PnL을 portfolio_snapshots에서 계산하여 업데이트';
