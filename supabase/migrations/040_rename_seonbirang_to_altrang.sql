-- =============================================================================
-- seonbirang → altrang 테이블 리네임
-- 기존 데이터 보존, 인덱스/RLS/정책 재생성
-- =============================================================================

-- 1. 기존 RLS 정책 삭제
DROP POLICY IF EXISTS "service_role_full_sb_trades" ON seonbirang_trades;
DROP POLICY IF EXISTS "service_role_full_sb_rankings" ON seonbirang_coin_rankings;
DROP POLICY IF EXISTS "service_role_full_sb_snapshots" ON seonbirang_snapshots;

-- 2. 테이블 리네임
ALTER TABLE seonbirang_trades RENAME TO altrang_trades;
ALTER TABLE seonbirang_coin_rankings RENAME TO altrang_coin_rankings;
ALTER TABLE seonbirang_snapshots RENAME TO altrang_snapshots;

-- 3. 인덱스 리네임
ALTER INDEX IF EXISTS idx_sb_trades_created RENAME TO idx_ar_trades_created;
ALTER INDEX IF EXISTS idx_sb_trades_strategy RENAME TO idx_ar_trades_strategy;
ALTER INDEX IF EXISTS idx_sb_trades_symbol RENAME TO idx_ar_trades_symbol;
ALTER INDEX IF EXISTS idx_sb_rankings_created RENAME TO idx_ar_rankings_created;
ALTER INDEX IF EXISTS idx_sb_snapshots_created RENAME TO idx_ar_snapshots_created;

-- 4. RLS 정책 재생성
CREATE POLICY "service_role_full_ar_trades" ON altrang_trades
  FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_full_ar_rankings" ON altrang_coin_rankings
  FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_full_ar_snapshots" ON altrang_snapshots
  FOR ALL TO service_role USING (true) WITH CHECK (true);
