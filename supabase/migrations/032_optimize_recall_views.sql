-- 032: v_trade_recall, v_cycle_detail LATERAL JOIN → 직접 JOIN 최적화
-- external_signal_log에 decision_id FK가 추가되었으므로 (031)
-- 시간 기반 LATERAL JOIN 대신 decision_id 직접 JOIN 사용

-- V1: 단타 거래 전체 맥락 (LATERAL → LEFT JOIN on decision_id)
CREATE OR REPLACE VIEW v_trade_recall AS
SELECT
  d.id AS decision_id,
  d.cycle_id,
  d.source,
  d.created_at,
  d.decision AS action,
  d.confidence,
  d.current_price AS price,
  d.trade_amount,
  d.reason,
  d.profit_loss,
  d.executed,
  -- 매수 점수 상세
  bs.total_score AS buy_total,
  bs.fgi_score AS buy_fgi,
  bs.rsi_score AS buy_rsi,
  bs.sma_score AS buy_sma,
  bs.news_score AS buy_news,
  bs.external_bonus AS buy_ext,
  bs.agent_type,
  bs.threshold AS buy_threshold,
  -- 시장 컨텍스트
  mc.rsi_14,
  mc.sma_20,
  mc.fgi_value,
  mc.fgi_class,
  mc.funding_rate,
  mc.long_short_ratio,
  mc.kimchi_premium,
  mc.whale_flow,
  mc.macro_sentiment,
  mc.eth_btc_trend,
  mc.active_agent,
  mc.danger_score,
  mc.opportunity_score,
  mc.position_ratio,
  -- 외부 시그널 (decision_id 직접 JOIN, 없으면 cycle_id fallback)
  COALESCE(es1.fusion_score, es2.fusion_score) AS ext_fusion,
  COALESCE(es1.fusion_signal, es2.fusion_signal) AS ext_signal,
  COALESCE(es1.binance_score, es2.binance_score) AS ext_binance,
  COALESCE(es1.whale_score, es2.whale_score) AS ext_whale,
  COALESCE(es1.macro_score, es2.macro_score) AS ext_macro,
  COALESCE(es1.coingecko_score, es2.coingecko_score) AS ext_coingecko,
  COALESCE(es1.eth_btc_score, es2.eth_btc_score) AS ext_ethbtc
FROM decisions d
LEFT JOIN buy_score_detail bs ON bs.decision_id = d.id
LEFT JOIN market_context_log mc ON mc.decision_id = d.id
-- 1순위: decision_id 직접 매칭
LEFT JOIN external_signal_log es1 ON es1.decision_id = d.id
-- 2순위: cycle_id fallback (decision_id 없는 기존 데이터)
LEFT JOIN LATERAL (
  SELECT * FROM external_signal_log e
  WHERE es1.id IS NULL
    AND e.decision_id IS NULL
    AND e.cycle_id = d.cycle_id
  LIMIT 1
) es2 ON true
ORDER BY d.created_at DESC;

-- V4: cycle 단위 조회 (이미 cycle_id 사용, 변경 불필요하지만 일관성 위해 재생성)
CREATE OR REPLACE VIEW v_cycle_detail AS
SELECT
  d.cycle_id,
  d.source,
  d.created_at,
  d.decision AS action,
  d.current_price AS price,
  d.trade_amount,
  d.confidence,
  d.profit_loss,
  SUBSTRING(d.reason, 1, 100) AS reason_short,
  bs.total_score,
  bs.agent_type,
  mc.fgi_value,
  mc.rsi_14,
  mc.danger_score,
  mc.opportunity_score,
  COALESCE(es1.fusion_signal, es2.fusion_signal) AS ext_signal,
  COALESCE(es1.fusion_score, es2.fusion_score) AS ext_score
FROM decisions d
LEFT JOIN buy_score_detail bs ON bs.decision_id = d.id
LEFT JOIN market_context_log mc ON mc.decision_id = d.id
LEFT JOIN external_signal_log es1 ON es1.decision_id = d.id
LEFT JOIN LATERAL (
  SELECT * FROM external_signal_log e
  WHERE es1.id IS NULL
    AND e.decision_id IS NULL
    AND e.cycle_id = d.cycle_id
  LIMIT 1
) es2 ON true
WHERE d.cycle_id IS NOT NULL
ORDER BY d.created_at DESC;
