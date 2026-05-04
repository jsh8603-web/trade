#!/usr/bin/env python3
"""
Unit tests for scripts/ v6 coverage gaps.

Covers:
  1. short_term_trader.py: whale signal detection (v6 params: 200M threshold, 85% ratio, min 3 count)
  2. short_term_trader.py: exit logic (TP 0.30%, SL 0.25%, early stop 5min/-0.15%, trailing stop)
  3. execute_trade.py: safety checks (DRY_RUN, EMERGENCY_STOP, MAX_TRADE_AMOUNT, auto emergency)
  4. evaluate_switches.py: null price_at_switch handling
  5. get_portfolio.py: balance calculation, profit/loss calculation

All external API calls and file I/O are mocked.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(PROJECT_DIR))

# MACHINE_ROLE primary 강제는 conftest.force_machine_primary 픽스처가 담당.
# 모듈 임포트 시점에는 utils.machine 캐시가 비어 있으면 OK — TestEvaluateSwitchesNullPrice
# 의 setup_env 픽스처에서 force_machine_primary를 사용한다.

KST = timezone(timedelta(hours=9))


# ===========================================================================
# PART 1: short_term_trader.py — Whale Signal Detection (v6)
# ===========================================================================

class TestWhaleSignalDetectionV6:
    """Test whale signal detection with v6 parameters."""

    @pytest.fixture
    def make_bot(self):
        """Create a minimal ShortTermTrader with mocked internals."""
        # Defer import to allow patching at module level
        def _make(**kwargs):
            with patch.dict(os.environ, {
                "UPBIT_ACCESS_KEY": "test",
                "UPBIT_SECRET_KEY": "test",
                "DRY_RUN": "true",
                "EMERGENCY_STOP": "false",
            }):
                from short_term_trader import ShortTermTrader, Position, TradeSignal
                bot = object.__new__(ShortTermTrader)
                # Initialize minimal attributes
                bot.dry_run = True
                bot.whale_recent = []
                bot.positions = []
                bot.current_price = kwargs.get("current_price", 100_000_000)
                bot.daily_trade_count = 0
                bot.used_budget = 0
                bot.emergency_stopped = False
                bot._last_block_reason = set()
                return bot
        return _make

    def test_whale_signal_buy_strong(self, make_bot):
        """Buy signal when buy ratio >= 85% and total >= 200M and count >= 3."""
        bot = make_bot()
        now = time.time()
        # 3 whale buys totaling 250M, 1 small sell of 10M
        bot.whale_recent = [
            {"time": now - 10, "side": "BID", "krw": 100_000_000},
            {"time": now - 8, "side": "BID", "krw": 80_000_000},
            {"time": now - 5, "side": "BID", "krw": 70_000_000},
            {"time": now - 3, "side": "ASK", "krw": 10_000_000},
        ]
        signal = bot.check_whale_signal()
        assert signal is not None
        assert signal.action == "buy"
        assert signal.strategy == "whale"
        # buy_ratio = 250M / 260M ~= 0.961
        assert signal.confidence >= 0.85

    def test_whale_signal_sell_strong(self, make_bot):
        """Sell signal when sell ratio >= 85% and total >= 200M and count >= 3."""
        bot = make_bot()
        now = time.time()
        bot.whale_recent = [
            {"time": now - 10, "side": "ASK", "krw": 120_000_000},
            {"time": now - 7, "side": "ASK", "krw": 100_000_000},
            {"time": now - 4, "side": "ASK", "krw": 80_000_000},
            {"time": now - 2, "side": "BID", "krw": 5_000_000},
        ]
        signal = bot.check_whale_signal()
        assert signal is not None
        assert signal.action == "sell"
        assert signal.confidence >= 0.85

    def test_whale_signal_none_below_threshold(self, make_bot):
        """No signal when total KRW is below 200M threshold."""
        bot = make_bot()
        now = time.time()
        # Total = 150M, below 200M threshold
        bot.whale_recent = [
            {"time": now - 10, "side": "BID", "krw": 50_000_000},
            {"time": now - 8, "side": "BID", "krw": 50_000_000},
            {"time": now - 5, "side": "BID", "krw": 50_000_000},
        ]
        signal = bot.check_whale_signal()
        assert signal is None

    def test_whale_signal_none_low_ratio(self, make_bot):
        """No signal when buy/sell ratio is below 85%."""
        bot = make_bot()
        now = time.time()
        # buy=150M, sell=80M => buy_ratio=65%, below 85%
        bot.whale_recent = [
            {"time": now - 10, "side": "BID", "krw": 80_000_000},
            {"time": now - 8, "side": "BID", "krw": 70_000_000},
            {"time": now - 5, "side": "ASK", "krw": 80_000_000},
        ]
        signal = bot.check_whale_signal()
        assert signal is None

    def test_whale_signal_none_insufficient_count(self, make_bot):
        """No signal when whale trade count < 3 (v6 minimum)."""
        bot = make_bot()
        now = time.time()
        # Only 2 whale trades (< 3 minimum)
        bot.whale_recent = [
            {"time": now - 10, "side": "BID", "krw": 150_000_000},
            {"time": now - 5, "side": "BID", "krw": 100_000_000},
        ]
        signal = bot.check_whale_signal()
        assert signal is None

    def test_whale_signal_none_too_few_records(self, make_bot):
        """No signal when whale_recent has < 2 entries."""
        bot = make_bot()
        bot.whale_recent = [{"time": time.time() - 5, "side": "BID", "krw": 500_000_000}]
        signal = bot.check_whale_signal()
        assert signal is None

    def test_whale_signal_old_trades_excluded(self, make_bot):
        """Old trades outside 3-minute window are not counted."""
        bot = make_bot()
        now = time.time()
        # 3 old trades (> 180s ago) + 2 recent (< 3 minimum in window)
        bot.whale_recent = [
            {"time": now - 300, "side": "BID", "krw": 100_000_000},
            {"time": now - 250, "side": "BID", "krw": 100_000_000},
            {"time": now - 200, "side": "BID", "krw": 100_000_000},
            {"time": now - 10, "side": "BID", "krw": 100_000_000},
            {"time": now - 5, "side": "BID", "krw": 100_000_000},
        ]
        signal = bot.check_whale_signal()
        # Only 2 recent trades in window, count < 3
        assert signal is None

    def test_get_recent_whale_krw(self, make_bot):
        """_get_recent_whale_krw counts correctly within window."""
        bot = make_bot()
        now = time.time()
        bot.whale_recent = [
            {"time": now - 300, "side": "BID", "krw": 50_000_000},  # outside window
            {"time": now - 100, "side": "BID", "krw": 100_000_000},
            {"time": now - 50, "side": "ASK", "krw": 60_000_000},
            {"time": now - 10, "side": "BID", "krw": 80_000_000},
        ]
        buy_krw, sell_krw, count = bot._get_recent_whale_krw(now)
        assert count == 3  # 3 within 180s window
        assert buy_krw == 180_000_000
        assert sell_krw == 60_000_000

    def test_sell_pressure_blocking(self, make_bot):
        """Sell pressure blocks buy when sell >= 4x buy."""
        bot = make_bot()
        now = time.time()
        bot.whale_recent = [
            {"time": now - 10, "side": "ASK", "krw": 400_000_000},
            {"time": now - 5, "side": "BID", "krw": 50_000_000},
            {"time": now - 3, "side": "ASK", "krw": 100_000_000},
        ]
        assert bot.is_sell_pressure_blocking() is True

    def test_no_sell_pressure(self, make_bot):
        """No blocking when sell is not dominant."""
        bot = make_bot()
        now = time.time()
        bot.whale_recent = [
            {"time": now - 10, "side": "BID", "krw": 200_000_000},
            {"time": now - 5, "side": "ASK", "krw": 100_000_000},
            {"time": now - 3, "side": "BID", "krw": 100_000_000},
        ]
        assert bot.is_sell_pressure_blocking() is False


# ===========================================================================
# PART 2: short_term_trader.py — Exit Logic (v6)
# ===========================================================================

class TestPositionExitLogicV6:
    """Test position exit logic with v6 parameters."""

    @pytest.fixture
    def make_bot_with_position(self):
        """Create bot with a single position for exit testing."""
        def _make(entry_price=100_000_000, current_price=100_000_000,
                  hold_seconds=0, trailing_active=False, highest_pnl=0.0):
            with patch.dict(os.environ, {
                "UPBIT_ACCESS_KEY": "test",
                "UPBIT_SECRET_KEY": "test",
                "DRY_RUN": "true",
                "USE_RL_EXIT": "false",
            }):
                from short_term_trader import ShortTermTrader, Position
                bot = object.__new__(ShortTermTrader)
                bot.positions = []
                bot.current_price = current_price
                bot.whale_recent = []
                bot.dry_run = True

                entry_time = datetime.now(KST) - timedelta(seconds=hold_seconds)
                pos = Position(
                    strategy="whale",
                    side="bid",
                    entry_price=entry_price,
                    amount_krw=300_000,
                    btc_qty=0.003,
                    entry_time=entry_time,
                    trailing_stop_active=trailing_active,
                    highest_pnl_pct=highest_pnl,
                    stop_loss_pct=0.25,
                    take_profit_pct=0.30,
                    max_hold_min=15,
                )
                bot.positions.append(pos)
                return bot, pos
        return _make

    def test_take_profit_at_030_pct(self, make_bot_with_position):
        """TP triggers at +0.30% after fees (v6: TP=0.30%)."""
        # Need raw_pnl >= 0.30 + 0.10 (roundtrip fee) = 0.40%
        entry = 100_000_000
        # 0.40% gain => price = 100_400_000
        current = int(entry * 1.0040)
        bot, pos = make_bot_with_position(entry_price=entry, current_price=current)
        exits = bot.check_position_exit()
        assert len(exits) == 1
        assert "익절" in exits[0][1]

    def test_no_take_profit_below_threshold(self, make_bot_with_position):
        """No TP when pnl after fees is below 0.30%."""
        entry = 100_000_000
        # 0.30% raw gain => after 0.10% fee = 0.20%, below 0.30% TP
        current = int(entry * 1.003)
        bot, pos = make_bot_with_position(entry_price=entry, current_price=current)
        exits = bot.check_position_exit()
        assert len(exits) == 0

    def test_stop_loss_at_025_pct(self, make_bot_with_position):
        """SL triggers at -0.25% after fees (v6: SL=0.25%)."""
        entry = 100_000_000
        # pnl_after_fee = raw_pnl - 0.10; need pnl_after_fee <= -0.25
        # raw_pnl <= -0.15 => price drop of 0.15% => 99_850_000
        current = int(entry * (1 - 0.0035))  # -0.35% raw => -0.25% after fee
        bot, pos = make_bot_with_position(entry_price=entry, current_price=current)
        exits = bot.check_position_exit()
        assert len(exits) == 1
        assert "손절" in exits[0][1]

    def test_early_stop_5min_minus_015(self, make_bot_with_position):
        """Early stop after 5min with -0.15% loss (v6: 5min/-0.15%)."""
        entry = 100_000_000
        # Need pnl_pct <= -0.15% after fee, but NOT <= -0.25% (stop loss)
        # pnl_pct = raw_pnl - 0.10 (roundtrip fee)
        # Want pnl_pct = -0.15%, so raw_pnl = -0.05%
        current = int(entry * (1 - 0.0005))  # -0.05% raw => -0.15% after fee
        bot, pos = make_bot_with_position(
            entry_price=entry, current_price=current, hold_seconds=360  # 6 minutes
        )
        exits = bot.check_position_exit()
        assert len(exits) == 1
        assert "조기 손절" in exits[0][1]

    def test_no_early_stop_before_5min(self, make_bot_with_position):
        """No early stop before 5 minutes even with same loss level."""
        entry = 100_000_000
        # Same pnl as above: -0.05% raw => -0.15% after fee
        current = int(entry * (1 - 0.0005))
        bot, pos = make_bot_with_position(
            entry_price=entry, current_price=current, hold_seconds=180  # 3 min, < 5
        )
        exits = bot.check_position_exit()
        # Should not trigger: early stop needs > 5min, stop loss needs <= -0.25%
        assert len(exits) == 0

    def test_trailing_stop_activation(self, make_bot_with_position):
        """Trailing stop activates at +0.25% after fees (v6)."""
        entry = 100_000_000
        # Need pnl_pct >= 0.25 (TRAILING_STOP_ACTIVATE_PCT)
        # raw_pnl = pnl_pct + 0.10 = 0.35%
        current = int(entry * 1.0035)
        bot, pos = make_bot_with_position(entry_price=entry, current_price=current)
        assert pos.trailing_stop_active is False
        exits = bot.check_position_exit()
        # Should activate trailing stop but also TP at 0.30% triggers first
        # pnl_pct = 0.35 - 0.10 = 0.25, which is below TP 0.30%
        assert pos.trailing_stop_active is True

    def test_trailing_stop_triggers_on_drawdown(self, make_bot_with_position):
        """Trailing stop exits when drawdown >= 0.15% from peak (v6)."""
        entry = 100_000_000
        # Trailing already active, highest_pnl was 0.30%
        # Current pnl = 0.10% => drawdown = 0.30 - 0.10 = 0.20% >= 0.15%
        current = int(entry * 1.002)  # raw +0.20% => pnl_pct = 0.10%
        bot, pos = make_bot_with_position(
            entry_price=entry, current_price=current,
            trailing_active=True, highest_pnl=0.30,
        )
        exits = bot.check_position_exit()
        assert len(exits) == 1
        assert "트레일링 스탑" in exits[0][1]

    def test_trailing_stop_no_exit_small_drawdown(self, make_bot_with_position):
        """No trailing stop exit when drawdown < 0.15%."""
        entry = 100_000_000
        # highest_pnl = 0.30%, current pnl = 0.20% => drawdown = 0.10% < 0.15%
        current = int(entry * 1.003)  # raw +0.30% => pnl_pct = 0.20%
        bot, pos = make_bot_with_position(
            entry_price=entry, current_price=current,
            trailing_active=True, highest_pnl=0.30,
        )
        exits = bot.check_position_exit()
        assert len(exits) == 0

    def test_time_limit_exit(self, make_bot_with_position):
        """Position exits after max hold time (15 min)."""
        entry = 100_000_000
        bot, pos = make_bot_with_position(
            entry_price=entry, current_price=entry,  # flat, no PnL trigger
            hold_seconds=16 * 60,  # 16 minutes > 15 limit
        )
        exits = bot.check_position_exit()
        assert len(exits) == 1
        assert "시간 제한" in exits[0][1]

    def test_no_exit_on_zero_price(self, make_bot_with_position):
        """No exit check when current_price <= 0."""
        bot, pos = make_bot_with_position(current_price=0)
        exits = bot.check_position_exit()
        assert len(exits) == 0


# ===========================================================================
# PART 3: execute_trade.py — Safety Checks
# ===========================================================================

class TestExecuteTradeSafety:
    """Test execute_trade.py safety checks."""

    @pytest.fixture(autouse=True)
    def setup_env(self, tmp_path, monkeypatch):
        """Set up environment variables and mock paths."""
        monkeypatch.setenv("UPBIT_ACCESS_KEY", "test_key")
        monkeypatch.setenv("UPBIT_SECRET_KEY", "test_secret")
        monkeypatch.setenv("DRY_RUN", "true")
        monkeypatch.setenv("EMERGENCY_STOP", "false")
        monkeypatch.setenv("MAX_TRADE_AMOUNT", "100000")
        monkeypatch.setenv("MAX_DAILY_TRADES", "6")
        monkeypatch.setenv("MIN_TRADE_INTERVAL_HOURS", "4")
        monkeypatch.setenv("MAX_POSITION_RATIO", "0.5")
        self.tmp_path = tmp_path

    def test_dry_run_returns_success(self):
        """DRY_RUN=true returns success without executing."""
        from execute_trade import execute
        result = execute("bid", "KRW-BTC", "50000")
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["side"] == "bid"

    def test_dry_run_sell_also_succeeds(self):
        """DRY_RUN=true works for sell orders too."""
        from execute_trade import execute
        result = execute("ask", "KRW-BTC", "0.001")
        assert result["success"] is True
        assert result["dry_run"] is True

    def test_emergency_stop_blocks_buy(self, monkeypatch):
        """EMERGENCY_STOP=true blocks buy orders."""
        monkeypatch.setenv("EMERGENCY_STOP", "true")
        from execute_trade import execute
        result = execute("bid", "KRW-BTC", "50000")
        assert result["success"] is False
        assert "EMERGENCY_STOP" in result["error"]

    def test_emergency_stop_allows_sell(self, monkeypatch):
        """EMERGENCY_STOP=true allows sell for liquidation."""
        monkeypatch.setenv("EMERGENCY_STOP", "true")
        monkeypatch.setenv("DRY_RUN", "true")
        from execute_trade import execute
        result = execute("ask", "KRW-BTC", "0.001")
        # Should proceed to DRY_RUN check (not blocked by EMERGENCY_STOP)
        assert result["success"] is True
        assert result["dry_run"] is True

    def test_invalid_side_rejected(self):
        """Invalid side value is rejected."""
        from execute_trade import execute
        result = execute("invalid", "KRW-BTC", "50000")
        assert result["success"] is False
        assert "유효하지 않은 side" in result["error"]

    def test_max_trade_amount_blocks(self, monkeypatch):
        """Bid exceeding MAX_TRADE_AMOUNT is blocked (after DRY_RUN=false)."""
        monkeypatch.setenv("DRY_RUN", "false")
        monkeypatch.setenv("MAX_TRADE_AMOUNT", "100000")

        from execute_trade import execute, _get_daily_trades, _get_last_trade_time

        with patch("execute_trade._get_daily_trades", return_value={"date": "2026-03-16", "count": 0}), \
             patch("execute_trade._get_last_trade_time", return_value=None), \
             patch("execute_trade._get_btc_position_ratio", return_value=0.1):
            result = execute("bid", "KRW-BTC", "200000")
            assert result["success"] is False
            assert "상한 초과" in result["error"]

    def test_daily_trades_limit(self, monkeypatch):
        """Daily trade limit blocks execution."""
        monkeypatch.setenv("DRY_RUN", "false")
        monkeypatch.setenv("MAX_DAILY_TRADES", "6")

        from execute_trade import execute

        with patch("execute_trade._get_daily_trades", return_value={"date": "2026-03-16", "count": 6}):
            result = execute("bid", "KRW-BTC", "50000")
            assert result["success"] is False
            assert "일일 매매 횟수 상한" in result["error"]

    def test_min_trade_interval_blocks(self, monkeypatch):
        """Trade within minimum interval is blocked."""
        monkeypatch.setenv("DRY_RUN", "false")
        monkeypatch.setenv("MIN_TRADE_INTERVAL_HOURS", "4")

        from execute_trade import execute

        recent_time = datetime.now(KST) - timedelta(hours=1)  # only 1h ago

        with patch("execute_trade._get_daily_trades", return_value={"date": "2026-03-16", "count": 0}), \
             patch("execute_trade._get_last_trade_time", return_value=recent_time):
            result = execute("bid", "KRW-BTC", "50000")
            assert result["success"] is False
            assert "최소 매매 간격" in result["error"]

    def test_invalid_amount_rejected(self, monkeypatch):
        """Non-numeric amount is rejected."""
        monkeypatch.setenv("DRY_RUN", "false")

        from execute_trade import execute

        with patch("execute_trade._get_daily_trades", return_value={"date": "2026-03-16", "count": 0}), \
             patch("execute_trade._get_last_trade_time", return_value=None), \
             patch("execute_trade._get_btc_position_ratio", return_value=0.1):
            result = execute("bid", "KRW-BTC", "not_a_number")
            assert result["success"] is False
            assert "유효하지 않은 금액" in result["error"]

    def test_auto_emergency_blocks_buy(self, monkeypatch, tmp_path):
        """Auto emergency stop file blocks buy orders."""
        monkeypatch.setenv("EMERGENCY_STOP", "false")
        # Create auto_emergency.json
        import execute_trade
        auto_em_file = Path(execute_trade.PROJECT_DIR) / "data" / "auto_emergency.json"
        auto_em_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            auto_em_file.write_text(json.dumps({"active": True, "reason": "test crash"}), encoding="utf-8")
            result = execute_trade.execute("bid", "KRW-BTC", "50000")
            assert result["success"] is False
            assert "자동긴급정지" in result["error"]
        finally:
            auto_em_file.unlink(missing_ok=True)

    def test_auto_emergency_allows_sell(self, monkeypatch):
        """Auto emergency stop allows sell for liquidation."""
        monkeypatch.setenv("EMERGENCY_STOP", "false")
        monkeypatch.setenv("DRY_RUN", "true")
        import execute_trade
        auto_em_file = Path(execute_trade.PROJECT_DIR) / "data" / "auto_emergency.json"
        auto_em_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            auto_em_file.write_text(json.dumps({"active": True, "reason": "test"}), encoding="utf-8")
            result = execute_trade.execute("ask", "KRW-BTC", "0.001")
            # Should pass auto emergency (sell allowed) and hit DRY_RUN
            assert result["success"] is True
            assert result["dry_run"] is True
        finally:
            auto_em_file.unlink(missing_ok=True)

    def test_position_ratio_blocks_buy(self, monkeypatch):
        """Buy blocked when BTC position ratio exceeds MAX_POSITION_RATIO."""
        monkeypatch.setenv("DRY_RUN", "false")
        monkeypatch.setenv("MAX_POSITION_RATIO", "0.5")

        from execute_trade import execute

        with patch("execute_trade._get_daily_trades", return_value={"date": "2026-03-16", "count": 0}), \
             patch("execute_trade._get_last_trade_time", return_value=None), \
             patch("execute_trade._get_btc_position_ratio", return_value=0.6):
            result = execute("bid", "KRW-BTC", "50000")
            assert result["success"] is False
            assert "포지션 비율" in result["error"]


# ===========================================================================
# PART 4: evaluate_switches.py — Null price_at_switch Handling
# ===========================================================================

class TestEvaluateSwitchesNullPrice:
    """Test evaluate_switches.py with null price_at_switch (recently fixed bug)."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch, force_machine_primary):
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test_key")

    @patch("evaluate_switches.requests")
    @patch("evaluate_switches.get_current_price", return_value=100_000_000)
    def test_null_price_at_switch_marked_neutral(self, mock_price, mock_requests):
        """Switch with null price_at_switch is marked as neutral/unevaluable."""
        from evaluate_switches import evaluate_pending_switches

        cutoff = (datetime.now(KST) - timedelta(hours=5)).isoformat()

        # Mock GET response: one switch with null price
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = [
            {
                "id": "abc-123-null-price",
                "price_at_switch": None,
                "created_at": cutoff,
                "price_after_4h": None,
            }
        ]

        # Mock PATCH response
        mock_patch_resp = MagicMock()
        mock_patch_resp.status_code = 204

        mock_requests.get.return_value = mock_get_resp
        mock_requests.patch.return_value = mock_patch_resp

        evaluate_pending_switches()

        # Verify PATCH was called to mark it as neutral
        mock_requests.patch.assert_called_once()
        call_kwargs = mock_requests.patch.call_args
        patch_json = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert patch_json["outcome"] == "neutral"
        assert "누락" in patch_json["outcome_reason"]
        assert "evaluated_at" in patch_json

    @patch("evaluate_switches.requests")
    @patch("evaluate_switches.get_current_price", return_value=105_000_000)
    def test_valid_price_evaluated_good(self, mock_price, mock_requests):
        """Switch with valid price and +5% after 24h is marked good."""
        from evaluate_switches import evaluate_pending_switches

        created = (datetime.now(KST) - timedelta(hours=25)).isoformat()

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = [
            {
                "id": "def-456-good",
                "price_at_switch": 100_000_000,
                "created_at": created,
                "price_after_4h": None,
            }
        ]

        mock_patch_resp = MagicMock()
        mock_patch_resp.status_code = 204

        mock_requests.get.return_value = mock_get_resp
        mock_requests.patch.return_value = mock_patch_resp

        evaluate_pending_switches()

        mock_requests.patch.assert_called_once()
        call_kwargs = mock_requests.patch.call_args
        patch_json = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert patch_json["outcome"] == "good"
        assert patch_json["profit_after_24h"] == 5.0

    @patch("evaluate_switches.requests")
    @patch("evaluate_switches.get_current_price", return_value=97_000_000)
    def test_valid_price_evaluated_bad(self, mock_price, mock_requests):
        """Switch with -3% after 24h is marked bad."""
        from evaluate_switches import evaluate_pending_switches

        created = (datetime.now(KST) - timedelta(hours=25)).isoformat()

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = [
            {
                "id": "ghi-789-bad",
                "price_at_switch": 100_000_000,
                "created_at": created,
                "price_after_4h": None,
            }
        ]

        mock_patch_resp = MagicMock()
        mock_patch_resp.status_code = 204

        mock_requests.get.return_value = mock_get_resp
        mock_requests.patch.return_value = mock_patch_resp

        evaluate_pending_switches()

        call_kwargs = mock_requests.patch.call_args
        patch_json = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert patch_json["outcome"] == "bad"
        assert patch_json["profit_after_24h"] == -3.0

    @patch("evaluate_switches.requests")
    @patch("evaluate_switches.get_current_price", return_value=100_500_000)
    def test_4h_only_evaluation(self, mock_price, mock_requests):
        """Switch 5h old gets 4h evaluation but not 24h."""
        from evaluate_switches import evaluate_pending_switches

        created = (datetime.now(KST) - timedelta(hours=5)).isoformat()

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = [
            {
                "id": "jkl-012-4h",
                "price_at_switch": 100_000_000,
                "created_at": created,
                "price_after_4h": None,
            }
        ]

        mock_patch_resp = MagicMock()
        mock_patch_resp.status_code = 204

        mock_requests.get.return_value = mock_get_resp
        mock_requests.patch.return_value = mock_patch_resp

        evaluate_pending_switches()

        call_kwargs = mock_requests.patch.call_args
        patch_json = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "price_after_4h" in patch_json
        assert patch_json["price_after_4h"] == 100_500_000
        # Should NOT have 24h evaluation yet
        assert "outcome" not in patch_json

    @patch("evaluate_switches.requests")
    @patch("evaluate_switches.get_current_price", return_value=0)
    def test_zero_current_price_aborts(self, mock_price, mock_requests):
        """Evaluation aborts when current price is 0."""
        from evaluate_switches import evaluate_pending_switches

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = [
            {"id": "mno-345", "price_at_switch": 100_000_000,
             "created_at": (datetime.now(KST) - timedelta(hours=5)).isoformat(),
             "price_after_4h": None}
        ]

        mock_requests.get.return_value = mock_get_resp

        evaluate_pending_switches()

        # PATCH should NOT be called because current price is 0
        mock_requests.patch.assert_not_called()

    @patch("evaluate_switches.requests")
    def test_no_supabase_env_returns_early(self, mock_requests, monkeypatch):
        """Missing SUPABASE env vars causes early return."""
        monkeypatch.setenv("SUPABASE_URL", "")
        from evaluate_switches import evaluate_pending_switches
        evaluate_pending_switches()
        mock_requests.get.assert_not_called()

    @patch("evaluate_switches.requests")
    @patch("evaluate_switches.get_current_price", return_value=100_000_000)
    def test_mixed_null_and_valid_prices(self, mock_price, mock_requests):
        """Batch with both null and valid prices processes correctly."""
        from evaluate_switches import evaluate_pending_switches

        created_old = (datetime.now(KST) - timedelta(hours=25)).isoformat()

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = [
            {"id": "null-1", "price_at_switch": None,
             "created_at": created_old, "price_after_4h": None},
            {"id": "valid-1", "price_at_switch": 100_000_000,
             "created_at": created_old, "price_after_4h": None},
        ]

        mock_patch_resp = MagicMock()
        mock_patch_resp.status_code = 204

        mock_requests.get.return_value = mock_get_resp
        mock_requests.patch.return_value = mock_patch_resp

        evaluate_pending_switches()

        # Should have 2 PATCH calls (one for null, one for valid)
        assert mock_requests.patch.call_count == 2


# ===========================================================================
# PART 5: get_portfolio.py — Balance & Profit/Loss Calculation
# ===========================================================================

class TestGetPortfolio:
    """Test get_portfolio.py balance and profit/loss calculation."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        monkeypatch.setenv("UPBIT_ACCESS_KEY", "test_key")
        monkeypatch.setenv("UPBIT_SECRET_KEY", "test_secret")
        # Session 캐시 리셋 — requests mock이 동작하도록
        import get_portfolio
        get_portfolio._session = None
        orig = get_portfolio._get_session
        get_portfolio._get_session = lambda: get_portfolio.requests
        yield
        get_portfolio._get_session = orig
        get_portfolio._session = None

    @patch("get_portfolio.requests")
    def test_krw_only_portfolio(self, mock_requests, capsys):
        """Portfolio with only KRW balance."""
        from get_portfolio import main

        mock_accounts_resp = MagicMock()
        mock_accounts_resp.ok = True
        mock_accounts_resp.status_code = 200
        mock_accounts_resp.json.return_value = [
            {"currency": "KRW", "balance": "1000000", "avg_buy_price": "0"}
        ]
        mock_accounts_resp.raise_for_status = MagicMock()

        mock_requests.get.return_value = mock_accounts_resp

        main()
        output = json.loads(capsys.readouterr().out)
        assert output["krw_balance"] == 1_000_000.0
        assert output["holdings"] == []
        assert output["total_eval"] == 1_000_000.0

    @patch("get_portfolio.requests")
    def test_btc_holding_profit(self, mock_requests, capsys):
        """Portfolio with BTC showing profit."""
        from get_portfolio import main

        mock_accounts_resp = MagicMock()
        mock_accounts_resp.ok = True
        mock_accounts_resp.status_code = 200
        mock_accounts_resp.json.return_value = [
            {"currency": "KRW", "balance": "500000", "avg_buy_price": "0"},
            {"currency": "BTC", "balance": "0.01", "avg_buy_price": "100000000"},
        ]
        mock_accounts_resp.raise_for_status = MagicMock()

        mock_market_resp = MagicMock()
        mock_market_resp.ok = True
        mock_market_resp.json.return_value = [{"market": "KRW-BTC"}]

        mock_ticker_resp = MagicMock()
        mock_ticker_resp.ok = True
        mock_ticker_resp.json.return_value = [
            {"market": "KRW-BTC", "trade_price": 110_000_000}
        ]

        def side_effect(url, **kwargs):
            if "/accounts" in url:
                return mock_accounts_resp
            elif "/market/all" in url:
                return mock_market_resp
            elif "/ticker" in url:
                return mock_ticker_resp
            return MagicMock(ok=True, json=MagicMock(return_value=[]))

        mock_requests.get.side_effect = side_effect

        main()
        output = json.loads(capsys.readouterr().out)

        assert output["krw_balance"] == 500_000.0
        assert len(output["holdings"]) == 1
        btc = output["holdings"][0]
        assert btc["currency"] == "BTC"
        assert btc["balance"] == 0.01
        assert btc["current_price"] == 110_000_000
        assert btc["eval_amount"] == 1_100_000.0  # 0.01 * 110M
        assert btc["profit_loss_pct"] == 10.0  # (110M - 100M) / 100M * 100

    @patch("get_portfolio.requests")
    def test_btc_holding_loss(self, mock_requests, capsys):
        """Portfolio with BTC showing loss."""
        from get_portfolio import main

        mock_accounts_resp = MagicMock()
        mock_accounts_resp.ok = True
        mock_accounts_resp.status_code = 200
        mock_accounts_resp.json.return_value = [
            {"currency": "KRW", "balance": "500000", "avg_buy_price": "0"},
            {"currency": "BTC", "balance": "0.01", "avg_buy_price": "100000000"},
        ]
        mock_accounts_resp.raise_for_status = MagicMock()

        mock_market_resp = MagicMock()
        mock_market_resp.ok = True
        mock_market_resp.json.return_value = [{"market": "KRW-BTC"}]

        mock_ticker_resp = MagicMock()
        mock_ticker_resp.ok = True
        mock_ticker_resp.json.return_value = [
            {"market": "KRW-BTC", "trade_price": 95_000_000}
        ]

        def side_effect(url, **kwargs):
            if "/accounts" in url:
                return mock_accounts_resp
            elif "/market/all" in url:
                return mock_market_resp
            elif "/ticker" in url:
                return mock_ticker_resp
            return MagicMock(ok=True, json=MagicMock(return_value=[]))

        mock_requests.get.side_effect = side_effect

        main()
        output = json.loads(capsys.readouterr().out)

        btc = output["holdings"][0]
        assert btc["profit_loss_pct"] == -5.0  # (95M - 100M) / 100M * 100

    @patch("get_portfolio.requests")
    def test_total_eval_includes_krw_and_holdings(self, mock_requests, capsys):
        """total_eval = KRW balance + sum of all holding eval amounts."""
        from get_portfolio import main

        mock_accounts_resp = MagicMock()
        mock_accounts_resp.ok = True
        mock_accounts_resp.status_code = 200
        mock_accounts_resp.json.return_value = [
            {"currency": "KRW", "balance": "200000", "avg_buy_price": "0"},
            {"currency": "BTC", "balance": "0.005", "avg_buy_price": "100000000"},
            {"currency": "ETH", "balance": "0.1", "avg_buy_price": "5000000"},
        ]
        mock_accounts_resp.raise_for_status = MagicMock()

        mock_market_resp = MagicMock()
        mock_market_resp.ok = True
        mock_market_resp.json.return_value = [
            {"market": "KRW-BTC"},
            {"market": "KRW-ETH"},
        ]

        mock_ticker_resp = MagicMock()
        mock_ticker_resp.ok = True
        mock_ticker_resp.json.return_value = [
            {"market": "KRW-BTC", "trade_price": 100_000_000},
            {"market": "KRW-ETH", "trade_price": 5_000_000},
        ]

        def side_effect(url, **kwargs):
            if "/accounts" in url:
                return mock_accounts_resp
            elif "/market/all" in url:
                return mock_market_resp
            elif "/ticker" in url:
                return mock_ticker_resp
            return MagicMock(ok=True, json=MagicMock(return_value=[]))

        mock_requests.get.side_effect = side_effect

        main()
        output = json.loads(capsys.readouterr().out)

        # BTC: 0.005 * 100M = 500,000
        # ETH: 0.1 * 5M = 500,000
        # Total: 200,000 + 500,000 + 500,000 = 1,200,000
        assert output["total_eval"] == 1_200_000.0
        assert output["krw_balance"] == 200_000.0

    @patch("get_portfolio.requests")
    def test_zero_balance_coins_excluded(self, mock_requests, capsys):
        """Coins with zero balance are not included in holdings."""
        from get_portfolio import main

        mock_accounts_resp = MagicMock()
        mock_accounts_resp.ok = True
        mock_accounts_resp.status_code = 200
        mock_accounts_resp.json.return_value = [
            {"currency": "KRW", "balance": "1000000", "avg_buy_price": "0"},
            {"currency": "BTC", "balance": "0", "avg_buy_price": "100000000"},
            {"currency": "ETH", "balance": "0.5", "avg_buy_price": "5000000"},
        ]
        mock_accounts_resp.raise_for_status = MagicMock()

        mock_market_resp = MagicMock()
        mock_market_resp.ok = True
        mock_market_resp.json.return_value = [{"market": "KRW-ETH"}]

        mock_ticker_resp = MagicMock()
        mock_ticker_resp.ok = True
        mock_ticker_resp.json.return_value = [
            {"market": "KRW-ETH", "trade_price": 5_000_000}
        ]

        def side_effect(url, **kwargs):
            if "/accounts" in url:
                return mock_accounts_resp
            elif "/market/all" in url:
                return mock_market_resp
            elif "/ticker" in url:
                return mock_ticker_resp
            return MagicMock(ok=True, json=MagicMock(return_value=[]))

        mock_requests.get.side_effect = side_effect

        main()
        output = json.loads(capsys.readouterr().out)

        # BTC with 0 balance should be excluded
        assert len(output["holdings"]) == 1
        assert output["holdings"][0]["currency"] == "ETH"

    @patch("get_portfolio.requests")
    def test_total_profit_loss_pct(self, mock_requests, capsys):
        """Total profit/loss percentage is calculated correctly."""
        from get_portfolio import main

        mock_accounts_resp = MagicMock()
        mock_accounts_resp.ok = True
        mock_accounts_resp.status_code = 200
        mock_accounts_resp.json.return_value = [
            {"currency": "KRW", "balance": "0", "avg_buy_price": "0"},
            {"currency": "BTC", "balance": "0.01", "avg_buy_price": "100000000"},
        ]
        mock_accounts_resp.raise_for_status = MagicMock()

        mock_market_resp = MagicMock()
        mock_market_resp.ok = True
        mock_market_resp.json.return_value = [{"market": "KRW-BTC"}]

        mock_ticker_resp = MagicMock()
        mock_ticker_resp.ok = True
        mock_ticker_resp.json.return_value = [
            {"market": "KRW-BTC", "trade_price": 120_000_000}
        ]

        def side_effect(url, **kwargs):
            if "/accounts" in url:
                return mock_accounts_resp
            elif "/market/all" in url:
                return mock_market_resp
            elif "/ticker" in url:
                return mock_ticker_resp
            return MagicMock(ok=True, json=MagicMock(return_value=[]))

        mock_requests.get.side_effect = side_effect

        main()
        output = json.loads(capsys.readouterr().out)

        # Invested: 0.01 * 100M = 1M, Eval: 0.01 * 120M = 1.2M
        # Profit: (1.2M - 1M) / 1M * 100 = 20%
        assert output["total_profit_loss_pct"] == 20.0
