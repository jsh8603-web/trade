-- 036: Feedback Hub 상태 + 레짐 감지 로그
-- 자율 개선 파이프라인: confidence 보정, RL 모델 품질 추적, 레짐 기반 가중치 조정

-- 1) v_confidence_calibration: decisions 테이블에서 confidence 구간별 정확도
CREATE OR REPLACE VIEW v_confidence_calibration AS
SELECT
  CASE
    WHEN confidence < 0.4 THEN '0.0-0.4'
    WHEN confidence < 0.6 THEN '0.4-0.6'
    WHEN confidence < 0.8 THEN '0.6-0.8'
    ELSE '0.8-1.0'
  END AS confidence_bucket,
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE was_correct_4h = true) AS correct_4h,
  ROUND(
    (COUNT(*) FILTER (WHERE was_correct_4h = true))::numeric
    / NULLIF(COUNT(*) FILTER (WHERE was_correct_4h IS NOT NULL), 0),
    4
  ) AS accuracy_4h,
  ROUND(AVG(confidence)::numeric, 3) AS avg_confidence,
  ROUND(AVG(outcome_4h_pct)::numeric, 3) AS avg_outcome_4h_pct
FROM decisions
WHERE created_at > NOW() - INTERVAL '14 days'
  AND confidence IS NOT NULL
GROUP BY confidence_bucket
ORDER BY confidence_bucket;

COMMENT ON VIEW v_confidence_calibration IS 'Feedback Hub: confidence 구간별 4h 정확도 (최근 14일)';

-- 2) v_regime_performance: 레짐별 결정 성과 (향후 가중치 최적화용)
-- regime 정보는 market_data_snapshot JSON에 저장됨
CREATE OR REPLACE VIEW v_regime_performance AS
SELECT
  market_data_snapshot->>'regime' AS regime,
  COUNT(*) AS total_decisions,
  ROUND(AVG(outcome_4h_pct)::numeric, 3) AS avg_outcome_4h,
  ROUND(AVG(outcome_24h_pct)::numeric, 3) AS avg_outcome_24h,
  COUNT(*) FILTER (WHERE was_correct_4h = true) AS correct_4h,
  ROUND(
    (COUNT(*) FILTER (WHERE was_correct_4h = true))::numeric
    / NULLIF(COUNT(*) FILTER (WHERE was_correct_4h IS NOT NULL), 0),
    4
  ) AS accuracy_4h
FROM decisions
WHERE created_at > NOW() - INTERVAL '30 days'
  AND market_data_snapshot->>'regime' IS NOT NULL
GROUP BY regime
ORDER BY total_decisions DESC;

COMMENT ON VIEW v_regime_performance IS '시장 레짐별 결정 성과 (최근 30일)';
