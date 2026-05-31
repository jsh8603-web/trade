
-- ============================================================
-- 수동 DDL (build_sqlite_schema.py 가 자동 생성하지 않는 항목).
-- 변환기가 generated 테이블 뒤에 이 파일을 그대로 append 함.
-- ============================================================

-- performance_reviews: run_analysis.ps1 이 db.select(order=reviewed_at.desc) 로 조회.
-- migration 에 정의 부재(aspirational) -> no such table 회피용 최소 스키마.
CREATE TABLE IF NOT EXISTS performance_reviews (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    reviewed_at     TEXT DEFAULT CURRENT_TIMESTAMP,
    period_start    TEXT,
    period_end      TEXT,
    review_type     TEXT,
    total_evaluated INTEGER,
    wins            INTEGER,
    losses          INTEGER,
    win_rate_pct    REAL,
    avg_profit_loss REAL,
    assessment      TEXT,
    summary         TEXT,
    details         TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_perf_reviews_reviewed_at ON performance_reviews(reviewed_at DESC);

-- ============================================================
-- v_* 회상/회고 뷰 (수동 이식: PG migration -> SQLite 호환)
-- 출처: supabase/migrations/009,010,011,012,013,032.
-- build_sqlite_schema.py 는 CREATE VIEW 를 제외하므로 여기 수동 append.
-- 재생성 시 변환기가 이 블록을 덮어쓰지 않음(append-only, header 부터 테이블까지만 생성).
-- 변환 요지: FILTER(WHERE)->SUM(CASE WHEN), LATERAL->상관 서브쿼리,
--   ::numeric/::date->제거/date(), NOW()-INTERVAL->datetime('now',...),
--   SUBSTRING->substr, EXTRACT/ABS 시간차 매칭->decision_id 직접 JOIN(032).
-- ============================================================

-- V1: 단타 거래 전체 맥락 (032 최적화본: decision_id 직접 JOIN + cycle_id fallback)
CREATE VIEW IF NOT EXISTS v_trade_recall AS
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
  bs.total_score AS buy_total,
  bs.fgi_score AS buy_fgi,
  bs.rsi_score AS buy_rsi,
  bs.sma_score AS buy_sma,
  bs.news_score AS buy_news,
  bs.external_bonus AS buy_ext,
  bs.agent_type,
  bs.threshold AS buy_threshold,
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
  COALESCE(es1.fusion_score,    esf.fusion_score)    AS ext_fusion,
  COALESCE(es1.fusion_signal,   esf.fusion_signal)   AS ext_signal,
  COALESCE(es1.binance_score,   esf.binance_score)   AS ext_binance,
  COALESCE(es1.whale_score,     esf.whale_score)     AS ext_whale,
  COALESCE(es1.macro_score,     esf.macro_score)     AS ext_macro,
  COALESCE(es1.coingecko_score, esf.coingecko_score) AS ext_coingecko,
  COALESCE(es1.eth_btc_score,   esf.eth_btc_score)   AS ext_ethbtc
FROM decisions d
LEFT JOIN buy_score_detail bs ON bs.decision_id = d.id
LEFT JOIN market_context_log mc ON mc.decision_id = d.id
LEFT JOIN external_signal_log es1 ON es1.decision_id = d.id
LEFT JOIN external_signal_log esf ON esf.id = (
  SELECT e.id FROM external_signal_log e
  WHERE es1.id IS NULL AND e.decision_id IS NULL AND e.cycle_id = d.cycle_id
  LIMIT 1
)
ORDER BY d.created_at DESC;

-- V2: 초단타 거래 전체 맥락
CREATE VIEW IF NOT EXISTS v_scalp_recall AS
SELECT
  t.id, t.cycle_id, t.session_date, t.trade_no, t.strategy,
  t.entry_time, t.exit_time, t.entry_price, t.exit_price, t.amount_krw,
  t.pnl_pct, t.pnl_krw, t.exit_reason, t.signal_reason, t.confidence,
  t.market_trend, t.news_sentiment, t.news_score, t.fgi_value, t.rsi_value,
  t.sma20_vs_price, t.was_good_trade, t.lesson, t.dry_run
FROM scalp_trade_log t
ORDER BY t.entry_time DESC;

-- V3: 일별 요약
CREATE VIEW IF NOT EXISTS v_daily_summary AS
SELECT
  trade_date,
  total_decisions,
  buys,
  sells,
  holds,
  avg_confidence,
  total_pnl,
  avg_buy_score,
  (SELECT COUNT(*) FROM scalp_trade_log s WHERE s.session_date = sub.trade_date) AS scalp_trades,
  (SELECT SUM(s.pnl_krw) FROM scalp_trade_log s WHERE s.session_date = sub.trade_date) AS scalp_pnl,
  avg_fgi,
  avg_rsi
FROM (
  SELECT
    date(d.created_at) AS trade_date,
    COUNT(*) AS total_decisions,
    SUM(CASE WHEN d.decision = '매수' THEN 1 ELSE 0 END) AS buys,
    SUM(CASE WHEN d.decision = '매도' THEN 1 ELSE 0 END) AS sells,
    SUM(CASE WHEN d.decision = '관망' THEN 1 ELSE 0 END) AS holds,
    ROUND(AVG(d.confidence), 2) AS avg_confidence,
    SUM(d.profit_loss) AS total_pnl,
    ROUND(AVG(bs.total_score), 1) AS avg_buy_score,
    ROUND(AVG(mc.fgi_value), 0) AS avg_fgi,
    ROUND(AVG(mc.rsi_14), 1) AS avg_rsi
  FROM decisions d
  LEFT JOIN buy_score_detail bs ON bs.decision_id = d.id
  LEFT JOIN market_context_log mc ON mc.decision_id = d.id
  GROUP BY date(d.created_at)
) sub
ORDER BY trade_date DESC;

-- V4: cycle 단위 조회 (032 최적화본)
CREATE VIEW IF NOT EXISTS v_cycle_detail AS
SELECT
  d.cycle_id,
  d.source,
  d.created_at,
  d.decision AS action,
  d.current_price AS price,
  d.trade_amount,
  d.confidence,
  d.profit_loss,
  substr(d.reason, 1, 100) AS reason_short,
  bs.total_score,
  bs.agent_type,
  mc.fgi_value,
  mc.rsi_14,
  mc.danger_score,
  mc.opportunity_score,
  COALESCE(es1.fusion_signal, esf.fusion_signal) AS ext_signal,
  COALESCE(es1.fusion_score,  esf.fusion_score)  AS ext_score
FROM decisions d
LEFT JOIN buy_score_detail bs ON bs.decision_id = d.id
LEFT JOIN market_context_log mc ON mc.decision_id = d.id
LEFT JOIN external_signal_log es1 ON es1.decision_id = d.id
LEFT JOIN external_signal_log esf ON esf.id = (
  SELECT e.id FROM external_signal_log e
  WHERE es1.id IS NULL AND e.decision_id IS NULL AND e.cycle_id = d.cycle_id
  LIMIT 1
)
WHERE d.cycle_id IS NOT NULL
ORDER BY d.created_at DESC;

-- 결정 정확도 분석 (010)
CREATE VIEW IF NOT EXISTS v_decision_accuracy AS
SELECT
  decision,
  source,
  COUNT(*) AS total,
  ROUND(AVG(outcome_1h_pct), 2) AS avg_1h_pct,
  SUM(CASE WHEN was_correct_1h = 1 THEN 1 ELSE 0 END) AS correct_1h,
  ROUND(SUM(CASE WHEN was_correct_1h = 1 THEN 1.0 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN was_correct_1h IS NOT NULL THEN 1 ELSE 0 END), 0) * 100, 1) AS accuracy_1h,
  ROUND(AVG(outcome_4h_pct), 2) AS avg_4h_pct,
  SUM(CASE WHEN was_correct_4h = 1 THEN 1 ELSE 0 END) AS correct_4h,
  ROUND(SUM(CASE WHEN was_correct_4h = 1 THEN 1.0 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN was_correct_4h IS NOT NULL THEN 1 ELSE 0 END), 0) * 100, 1) AS accuracy_4h,
  ROUND(AVG(outcome_24h_pct), 2) AS avg_24h_pct,
  SUM(CASE WHEN was_correct_24h = 1 THEN 1 ELSE 0 END) AS correct_24h,
  ROUND(SUM(CASE WHEN was_correct_24h = 1 THEN 1.0 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN was_correct_24h IS NOT NULL THEN 1 ELSE 0 END), 0) * 100, 1) AS accuracy_24h
FROM decisions
WHERE aftermath_updated_at IS NOT NULL
GROUP BY decision, source;

-- 놓친 기회 (010)
CREATE VIEW IF NOT EXISTS v_missed_opportunities AS
SELECT
  id, cycle_id, created_at, current_price,
  outcome_1h_pct, outcome_4h_pct, outcome_24h_pct,
  reason, confidence, fear_greed_value, rsi_value
FROM decisions
WHERE decision = '관망'
  AND outcome_24h_pct > 1.5
  AND aftermath_updated_at IS NOT NULL
ORDER BY outcome_24h_pct DESC;

-- 잘못된 거래 (010)
CREATE VIEW IF NOT EXISTS v_bad_trades AS
SELECT
  id, cycle_id, created_at, current_price, trade_amount,
  outcome_1h_pct, outcome_4h_pct, outcome_24h_pct,
  reason, confidence, fear_greed_value, rsi_value
FROM decisions
WHERE decision = '매수'
  AND outcome_4h_pct < -0.5
  AND aftermath_updated_at IS NOT NULL
ORDER BY outcome_4h_pct ASC;

-- 필터 효과 분석 (011)
CREATE VIEW IF NOT EXISTS v_filter_effectiveness AS
SELECT
  block_filter,
  COUNT(*) AS total_blocked,
  SUM(CASE WHEN would_have_won = 1 THEN 1 ELSE 0 END) AS would_have_won_count,
  SUM(CASE WHEN would_have_won = 0 THEN 1 ELSE 0 END) AS would_have_lost_count,
  ROUND(SUM(CASE WHEN would_have_won = 0 THEN 1.0 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN would_have_won IS NOT NULL THEN 1 ELSE 0 END), 0) * 100, 1) AS filter_save_rate,
  ROUND(AVG(outcome_1h_pct), 2) AS avg_outcome_if_traded
FROM signal_attempt_log
WHERE signal_type = 'blocked' AND aftermath_updated_at IS NOT NULL
GROUP BY block_filter
ORDER BY total_blocked DESC;

-- 니어미스 분석 (012)
CREATE VIEW IF NOT EXISTS v_near_miss_analysis AS
SELECT
  recorded_at,
  agent_type,
  total_score,
  threshold,
  points_from_threshold,
  was_ai_vetoed,
  ai_veto_reason,
  action,
  price_at_decision,
  outcome_1h_pct,
  outcome_4h_pct,
  would_have_profited,
  CASE
    WHEN would_have_profited = 1 AND action = 'hold' THEN '놓친 기회'
    WHEN would_have_profited = 0 AND action = 'hold' THEN '올바른 관망'
    WHEN would_have_profited = 1 AND action IN ('buy', '매수') THEN '좋은 매수'
    WHEN would_have_profited = 0 AND action IN ('buy', '매수') THEN '나쁜 매수'
    ELSE '미평가'
  END AS evaluation
FROM buy_score_detail
WHERE is_near_miss = 1 OR was_ai_vetoed = 1
ORDER BY recorded_at DESC;

-- AI 거부권 효과 분석 (012)
CREATE VIEW IF NOT EXISTS v_ai_veto_effectiveness AS
SELECT
  ai_veto_reason,
  COUNT(*) AS total_vetoes,
  SUM(CASE WHEN would_have_profited = 0 THEN 1 ELSE 0 END) AS saved_from_loss,
  SUM(CASE WHEN would_have_profited = 1 THEN 1 ELSE 0 END) AS missed_profit,
  ROUND(SUM(CASE WHEN would_have_profited = 0 THEN 1.0 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN would_have_profited IS NOT NULL THEN 1 ELSE 0 END), 0) * 100, 1) AS veto_accuracy_pct,
  ROUND(AVG(outcome_4h_pct), 2) AS avg_outcome_if_bought
FROM buy_score_detail
WHERE was_ai_vetoed = 1 AND aftermath_updated_at IS NOT NULL
GROUP BY ai_veto_reason
ORDER BY total_vetoes DESC;

-- 시스템 건강도 (013, 최근 24시간)
CREATE VIEW IF NOT EXISTS v_system_health AS
SELECT
  execution_mode,
  COUNT(*) AS total_runs,
  SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS success_count,
  SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) AS failure_count,
  ROUND(SUM(CASE WHEN success = 1 THEN 1.0 ELSE 0 END)
        / NULLIF(COUNT(*), 0) * 100, 1) AS success_rate,
  ROUND(AVG(duration_ms), 0) AS avg_duration_ms,
  MAX(duration_ms) AS max_duration_ms,
  MAX(created_at) AS last_run
FROM execution_logs
WHERE created_at > datetime('now', '-24 hours')
GROUP BY execution_mode;
