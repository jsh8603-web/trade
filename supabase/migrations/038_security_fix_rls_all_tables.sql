-- 038_security_fix_rls_all_tables.sql
-- Supabase Security Advisor 경고 해결
-- 16개 RLS 미적용 테이블에 RLS 활성화 + 정책 추가
-- 2026-03-19

-- ════════════════════════════════════════════════
-- A. RLS 활성화 (16개 누락 테이블)
-- ════════════════════════════════════════════════

ALTER TABLE IF EXISTS ai_signal_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS buy_score_detail ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS external_signal_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS kimchirang_rl_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS market_context_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS news_sentiment_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rag_analysis_vectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rl_model_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rl_model_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rl_parameter_tuning ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rl_training_cycles ENABLE ROW LEVEL SECURITY;
-- NOTE: rl_training_results 테이블이 DB에 없음 (마이그레이션 미적용)
-- ALTER TABLE IF EXISTS rl_training_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS strategy_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS system_health_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS trade_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS whale_detections ENABLE ROW LEVEL SECURITY;


-- ════════════════════════════════════════════════
-- B. RLS 정책: service_role 전체 접근 + worker 읽기 전용
-- ════════════════════════════════════════════════

-- B1. ai_signal_log
CREATE POLICY "srv_full" ON ai_signal_log
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON ai_signal_log
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B2. buy_score_detail
CREATE POLICY "srv_full" ON buy_score_detail
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON buy_score_detail
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B3. external_signal_log
CREATE POLICY "srv_full" ON external_signal_log
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON external_signal_log
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B4. kimchirang_rl_models
CREATE POLICY "srv_full" ON kimchirang_rl_models
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON kimchirang_rl_models
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B5. market_context_log
CREATE POLICY "srv_full" ON market_context_log
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON market_context_log
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B6. news_sentiment_log
CREATE POLICY "srv_full" ON news_sentiment_log
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON news_sentiment_log
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B7. rag_analysis_vectors
CREATE POLICY "srv_full" ON rag_analysis_vectors
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON rag_analysis_vectors
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B8. rl_model_predictions
CREATE POLICY "srv_full" ON rl_model_predictions
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON rl_model_predictions
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B9. rl_model_versions
CREATE POLICY "srv_full" ON rl_model_versions
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON rl_model_versions
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B10. rl_parameter_tuning
CREATE POLICY "srv_full" ON rl_parameter_tuning
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON rl_parameter_tuning
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B11. rl_training_cycles
CREATE POLICY "srv_full" ON rl_training_cycles
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON rl_training_cycles
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B12. rl_training_results (테이블 미존재 — 생성 시 적용)
-- CREATE POLICY "srv_full" ON rl_training_results
--   FOR ALL USING (is_service_role());
-- CREATE POLICY "worker_read" ON rl_training_results
--   FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B13. strategy_alerts
CREATE POLICY "srv_full" ON strategy_alerts
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON strategy_alerts
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B14. system_health_logs
CREATE POLICY "srv_full" ON system_health_logs
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON system_health_logs
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B15. trade_reviews
CREATE POLICY "srv_full" ON trade_reviews
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON trade_reviews
  FOR SELECT USING (get_worker_tier() IS NOT NULL);

-- B16. whale_detections
CREATE POLICY "srv_full" ON whale_detections
  FOR ALL USING (is_service_role());
CREATE POLICY "worker_read" ON whale_detections
  FOR SELECT USING (get_worker_tier() IS NOT NULL);


-- ════════════════════════════════════════════════
-- C. anon/public 기본 권한 명시적 제거
-- ════════════════════════════════════════════════

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM anon;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon;

-- authenticated 역할에 기본 SELECT 허용 (RLS가 필터링)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- worker helper 함수만 authenticated에 허용
GRANT EXECUTE ON FUNCTION get_worker_tier() TO authenticated;
GRANT EXECUTE ON FUNCTION get_worker_id() TO authenticated;
GRANT EXECUTE ON FUNCTION is_service_role() TO authenticated;


-- ════════════════════════════════════════════════
-- D. RPC 함수 보안 강화
-- ════════════════════════════════════════════════

-- pgvector 함수 미설치 — 설치 시 아래 적용
-- REVOKE ALL ON FUNCTION match_similar_decisions(vector, float, int) FROM anon, authenticated;
-- GRANT EXECUTE ON FUNCTION match_similar_decisions(vector, float, int) TO service_role;
-- REVOKE ALL ON FUNCTION match_similar_analyses(vector, float, int) FROM anon, authenticated;
-- GRANT EXECUTE ON FUNCTION match_similar_analyses(vector, float, int) TO service_role;


-- ════════════════════════════════════════════════
-- E. telegram_contacts PII 보호 강화
-- ════════════════════════════════════════════════

-- viewer 역할에서 연락처 읽기 차단 (owner/coworker만 허용)
DROP POLICY IF EXISTS "contacts_worker_read" ON telegram_contacts;
CREATE POLICY "contacts_worker_read" ON telegram_contacts
  FOR SELECT USING (
    get_worker_tier() IN ('owner', 'coworker')
    AND is_active = true
  );
