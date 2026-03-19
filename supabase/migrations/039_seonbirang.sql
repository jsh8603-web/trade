-- =============================================================================
-- SeonbiRang (선비랑): 펀딩비 수확 + 알트코인 로테이션
-- =============================================================================

-- 1. 거래 기록
CREATE TABLE IF NOT EXISTS seonbirang_trades (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  strategy TEXT NOT NULL CHECK (strategy IN ('funding', 'rotation')),
  action TEXT NOT NULL,
  symbol TEXT NOT NULL,
  funding_rate DECIMAL(10,8),
  momentum_score DECIMAL(8,4),
  pnl_pct DECIMAL(8,4),
  pnl_usdt DECIMAL(12,4),
  size_usdt DECIMAL(12,4),
  reason TEXT,
  dry_run BOOLEAN DEFAULT TRUE,
  success BOOLEAN DEFAULT FALSE,
  machine_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sb_trades_created ON seonbirang_trades(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sb_trades_strategy ON seonbirang_trades(strategy);
CREATE INDEX IF NOT EXISTS idx_sb_trades_symbol ON seonbirang_trades(symbol);

-- 2. 코인 순위 스냅샷
CREATE TABLE IF NOT EXISTS seonbirang_coin_rankings (
  id BIGSERIAL PRIMARY KEY,
  scan_type TEXT CHECK (scan_type IN ('funding', 'momentum')),
  rankings JSONB NOT NULL,
  universe_size INTEGER,
  machine_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sb_rankings_created ON seonbirang_coin_rankings(created_at DESC);

-- 3. 포트폴리오 스냅샷
CREATE TABLE IF NOT EXISTS seonbirang_snapshots (
  id BIGSERIAL PRIMARY KEY,
  total_balance_usdt DECIMAL(12,4),
  funding_positions JSONB,
  rotation_positions JSONB,
  funding_count INTEGER,
  rotation_count INTEGER,
  total_funding_collected DECIMAL(12,6),
  total_unrealized_pnl DECIMAL(12,4),
  machine_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sb_snapshots_created ON seonbirang_snapshots(created_at DESC);

-- 4. RLS 활성화
ALTER TABLE seonbirang_trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE seonbirang_coin_rankings ENABLE ROW LEVEL SECURITY;
ALTER TABLE seonbirang_snapshots ENABLE ROW LEVEL SECURITY;

-- service_role 전체 접근
CREATE POLICY "service_role_full_sb_trades" ON seonbirang_trades
  FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_full_sb_rankings" ON seonbirang_coin_rankings
  FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_full_sb_snapshots" ON seonbirang_snapshots
  FOR ALL TO service_role USING (true) WITH CHECK (true);
