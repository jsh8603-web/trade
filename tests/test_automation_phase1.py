#!/usr/bin/env python3
"""
Unit tests for automation Phase 1 scripts:
  - scripts/dynamic_risk.py
  - scripts/strategy_health.py
  - scripts/alert_aggregator.py

All external API calls, file I/O, and telegram sends are mocked.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# ---------------------------------------------------------------------------
# Imports: Add project directory to path
# ---------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

KST = timezone(timedelta(hours=9))


# ===========================================================================
# PART 1: dynamic_risk.py
# ===========================================================================

from dynamic_risk import (
    _calculate_sharpe,
    _calculate_win_rate,
    _count_consecutive_losses,
    _determine_risk_level,
    update_risk,
    get_adjusted_max_amount,
    get_risk_summary,
    MIN_SAMPLES,
)


class TestCalculateSharpe:
    """Tests for _calculate_sharpe."""

    def test_normal_returns(self):
        decisions = [
            {"outcome_4h_pct": 1.0},
            {"outcome_4h_pct": 2.0},
            {"outcome_4h_pct": 3.0},
        ]
        result = _calculate_sharpe(decisions)
        assert result is not None
        assert isinstance(result, float)

    def test_insufficient_samples(self):
        decisions = [{"outcome_4h_pct": 1.0}, {"outcome_4h_pct": 2.0}]
        assert _calculate_sharpe(decisions) is None

    def test_empty_list(self):
        assert _calculate_sharpe([]) is None

    def test_none_values_skipped(self):
        decisions = [
            {"outcome_4h_pct": None},
            {"outcome_4h_pct": 1.0},
            {"outcome_4h_pct": 2.0},
            {"outcome_4h_pct": 3.0},
        ]
        result = _calculate_sharpe(decisions)
        assert result is not None

    def test_all_none_values(self):
        decisions = [{"outcome_4h_pct": None}] * 5
        assert _calculate_sharpe(decisions) is None

    def test_zero_std_returns_zero(self):
        """All identical returns => std=0 => sharpe=0."""
        decisions = [{"outcome_4h_pct": 5.0}] * 5
        assert _calculate_sharpe(decisions) == 0.0

    def test_negative_returns(self):
        decisions = [
            {"outcome_4h_pct": -3.0},
            {"outcome_4h_pct": -1.0},
            {"outcome_4h_pct": -2.0},
        ]
        result = _calculate_sharpe(decisions)
        assert result is not None
        assert result < 0

    def test_invalid_type_skipped(self):
        decisions = [
            {"outcome_4h_pct": "bad"},
            {"outcome_4h_pct": 1.0},
            {"outcome_4h_pct": 2.0},
            {"outcome_4h_pct": 3.0},
        ]
        result = _calculate_sharpe(decisions)
        assert result is not None

    def test_missing_key(self):
        decisions = [{"no_key": 1}] * 5
        assert _calculate_sharpe(decisions) is None


class TestCalculateWinRate:
    """Tests for _calculate_win_rate."""

    def test_all_wins(self):
        decisions = [{"outcome_4h_pct": 1.0}, {"outcome_4h_pct": 2.0}]
        assert _calculate_win_rate(decisions) == 1.0

    def test_all_losses(self):
        decisions = [{"outcome_4h_pct": -1.0}, {"outcome_4h_pct": -2.0}]
        assert _calculate_win_rate(decisions) == 0.0

    def test_mixed(self):
        decisions = [
            {"outcome_4h_pct": 1.0},
            {"outcome_4h_pct": -1.0},
            {"outcome_4h_pct": 2.0},
            {"outcome_4h_pct": -2.0},
        ]
        assert _calculate_win_rate(decisions) == 0.5

    def test_empty(self):
        assert _calculate_win_rate([]) == 0.0

    def test_none_values_excluded(self):
        decisions = [
            {"outcome_4h_pct": None},
            {"outcome_4h_pct": 1.0},
            {"outcome_4h_pct": -1.0},
        ]
        assert _calculate_win_rate(decisions) == 0.5

    def test_zero_not_counted_as_win(self):
        decisions = [{"outcome_4h_pct": 0.0}, {"outcome_4h_pct": 0.0}]
        assert _calculate_win_rate(decisions) == 0.0


class TestCountConsecutiveLosses:
    """Tests for _count_consecutive_losses."""

    def test_no_losses(self):
        decisions = [{"outcome_4h_pct": 1.0}, {"outcome_4h_pct": 2.0}]
        assert _count_consecutive_losses(decisions) == 0

    def test_all_losses(self):
        decisions = [{"outcome_4h_pct": -1.0}] * 5
        assert _count_consecutive_losses(decisions) == 5

    def test_loss_streak_broken(self):
        # Ordered chronologically (asc), most recent is last
        decisions = [
            {"outcome_4h_pct": -1.0},
            {"outcome_4h_pct": 1.0},   # breaks streak
            {"outcome_4h_pct": -1.0},
            {"outcome_4h_pct": -2.0},
        ]
        assert _count_consecutive_losses(decisions) == 2

    def test_empty(self):
        assert _count_consecutive_losses([]) == 0

    def test_none_values_skipped(self):
        decisions = [
            {"outcome_4h_pct": -1.0},
            {"outcome_4h_pct": None},
            {"outcome_4h_pct": -2.0},
        ]
        # reversed: -2.0 (loss), None (skip), -1.0 (loss) => 2
        assert _count_consecutive_losses(decisions) == 2


class TestDetermineRiskLevel:
    """Tests for _determine_risk_level."""

    def test_none_sharpe(self):
        level, mult = _determine_risk_level(None)
        assert level == "NORMAL"
        assert mult == 1.0

    def test_critical(self):
        level, mult = _determine_risk_level(-1.0)
        assert level == "CRITICAL"
        assert mult == 0.6

    def test_low(self):
        level, mult = _determine_risk_level(-0.3)
        assert level == "LOW"
        assert mult == 0.8

    def test_normal(self):
        level, mult = _determine_risk_level(0.3)
        assert level == "NORMAL"
        assert mult == 1.0

    def test_high(self):
        level, mult = _determine_risk_level(1.0)
        assert level == "HIGH"
        assert mult == 1.1

    def test_boost(self):
        level, mult = _determine_risk_level(2.0)
        assert level == "BOOST"
        assert mult == 1.2

    def test_boundary_critical_low(self):
        level, _ = _determine_risk_level(-0.5)
        assert level == "LOW"  # -0.5 is not < -0.5

    def test_boundary_normal_high(self):
        level, _ = _determine_risk_level(0.5)
        assert level == "HIGH"

    def test_boundary_high_boost(self):
        level, _ = _determine_risk_level(1.5)
        assert level == "BOOST"


class TestUpdateRisk:
    """Tests for update_risk."""

    @patch("dynamic_risk._fetch_recent_decisions")
    @patch("dynamic_risk.STATE_FILE")
    def test_no_data_returns_normal(self, mock_state_file, mock_fetch):
        mock_fetch.return_value = []
        mock_parent = MagicMock()
        mock_state_file.parent = mock_parent
        mock_state_file.write_text = MagicMock()

        result = update_risk()
        assert result["risk_level"] == "NORMAL"
        assert result["sharpe_7d"] is None
        assert result["consecutive_losses"] == 0

    @patch("dynamic_risk._fetch_recent_decisions")
    @patch("dynamic_risk.STATE_FILE")
    def test_5_consecutive_losses_forces_critical(self, mock_state_file, mock_fetch):
        mock_fetch.return_value = [
            {"outcome_4h_pct": -1.0, "decision": "buy"} for _ in range(5)
        ]
        mock_parent = MagicMock()
        mock_state_file.parent = mock_parent
        mock_state_file.write_text = MagicMock()

        result = update_risk()
        assert result["risk_level"] == "CRITICAL"
        assert result["consecutive_losses"] >= 5

    @patch("dynamic_risk._fetch_recent_decisions")
    @patch("dynamic_risk.STATE_FILE")
    def test_3_consecutive_losses_penalty(self, mock_state_file, mock_fetch):
        # 3 losses but not 5 => extra -20%
        decisions = [
            {"outcome_4h_pct": 2.0, "decision": "buy"},
            {"outcome_4h_pct": 2.0, "decision": "buy"},
            {"outcome_4h_pct": -1.0, "decision": "buy"},
            {"outcome_4h_pct": -1.0, "decision": "buy"},
            {"outcome_4h_pct": -1.0, "decision": "buy"},
        ]
        mock_fetch.return_value = decisions
        mock_parent = MagicMock()
        mock_state_file.parent = mock_parent
        mock_state_file.write_text = MagicMock()

        result = update_risk()
        assert result["consecutive_losses"] == 3
        # Should have additional 20% penalty
        assert result["adjusted_amount"] < result["base_amount"]

    @patch("dynamic_risk._fetch_recent_decisions")
    @patch("dynamic_risk.STATE_FILE")
    def test_adjusted_amount_capped_at_2x(self, mock_state_file, mock_fetch):
        # Very high sharpe => BOOST 1.2x, but capped at 2x
        decisions = [{"outcome_4h_pct": 10.0}] * 10
        mock_fetch.return_value = decisions
        mock_parent = MagicMock()
        mock_state_file.parent = mock_parent
        mock_state_file.write_text = MagicMock()

        result = update_risk()
        assert result["adjusted_amount"] <= result["base_amount"] * 2

    @patch("dynamic_risk._fetch_recent_decisions")
    @patch("dynamic_risk.STATE_FILE")
    def test_adjusted_amount_min_floor(self, mock_state_file, mock_fetch):
        # Sharpe very negative => CRITICAL 0.6 + 5+ losses => 30% floor
        decisions = [{"outcome_4h_pct": -10.0}] * 10
        mock_fetch.return_value = decisions
        mock_parent = MagicMock()
        mock_state_file.parent = mock_parent
        mock_state_file.write_text = MagicMock()

        result = update_risk()
        min_floor = int(result["base_amount"] * 0.3)
        assert result["adjusted_amount"] >= min_floor


class TestGetAdjustedMaxAmount:
    """Tests for get_adjusted_max_amount."""

    @patch("dynamic_risk.STATE_FILE")
    def test_no_file_returns_none(self, mock_state_file):
        mock_state_file.exists.return_value = False
        assert get_adjusted_max_amount() is None

    @patch("dynamic_risk.STATE_FILE")
    def test_valid_state(self, mock_state_file):
        now = datetime.now(KST).isoformat()
        state = {"adjusted_amount": 80000, "last_updated": now}
        mock_state_file.exists.return_value = True
        mock_state_file.read_text.return_value = json.dumps(state)
        assert get_adjusted_max_amount() == 80000

    @patch("dynamic_risk.STATE_FILE")
    def test_stale_state_returns_none(self, mock_state_file):
        old = (datetime.now(KST) - timedelta(hours=25)).isoformat()
        state = {"adjusted_amount": 80000, "last_updated": old}
        mock_state_file.exists.return_value = True
        mock_state_file.read_text.return_value = json.dumps(state)
        assert get_adjusted_max_amount() is None

    @patch("dynamic_risk.STATE_FILE")
    def test_invalid_json_returns_none(self, mock_state_file):
        mock_state_file.exists.return_value = True
        mock_state_file.read_text.return_value = "not json"
        assert get_adjusted_max_amount() is None


class TestGetRiskSummary:
    """Tests for get_risk_summary."""

    @patch("dynamic_risk.STATE_FILE")
    def test_no_file_returns_empty(self, mock_state_file):
        mock_state_file.exists.return_value = False
        assert get_risk_summary() == {}

    @patch("dynamic_risk.STATE_FILE")
    def test_valid_state(self, mock_state_file):
        state = {"risk_level": "HIGH", "adjusted_amount": 110000}
        mock_state_file.exists.return_value = True
        mock_state_file.read_text.return_value = json.dumps(state)
        result = get_risk_summary()
        assert result["risk_level"] == "HIGH"

    @patch("dynamic_risk.STATE_FILE")
    def test_corrupt_json(self, mock_state_file):
        mock_state_file.exists.return_value = True
        mock_state_file.read_text.return_value = "{bad"
        assert get_risk_summary() == {}


# ===========================================================================
# PART 2: strategy_health.py
# ===========================================================================

from strategy_health import (
    _calc_win_rate as sh_calc_win_rate,
    _calc_consecutive_losses as sh_calc_consecutive_losses,
    _calc_sharpe as sh_calc_sharpe,
    _determine_status,
    _agent_win_rates,
    _generate_suggestion,
    check_health,
    get_health_status,
    get_health_summary,
)


class TestDetermineStatus:
    """Tests for _determine_status."""

    def test_green(self):
        assert _determine_status(0.6, 0) == "GREEN"

    def test_yellow_by_win_rate(self):
        assert _determine_status(0.45, 0) == "YELLOW"

    def test_yellow_by_consecutive(self):
        assert _determine_status(0.7, 3) == "YELLOW"

    def test_orange_by_win_rate(self):
        assert _determine_status(0.30, 0) == "ORANGE"

    def test_orange_by_consecutive(self):
        assert _determine_status(0.7, 5) == "ORANGE"

    def test_red_by_win_rate(self):
        assert _determine_status(0.20, 0) == "RED"

    def test_red_by_consecutive(self):
        assert _determine_status(0.7, 7) == "RED"

    def test_boundary_green_yellow(self):
        # win_rate=0.50 => not < 0.50 => GREEN
        assert _determine_status(0.50, 2) == "GREEN"

    def test_boundary_yellow_orange(self):
        assert _determine_status(0.35, 0) == "YELLOW"  # 0.35 is not < 0.35

    def test_boundary_orange_red(self):
        assert _determine_status(0.25, 0) == "ORANGE"  # 0.25 is not < 0.25


class TestStrategyHealthCalcWinRate:
    """Tests for strategy_health._calc_win_rate."""

    def test_all_correct(self):
        decisions = [{"was_correct_4h": True}] * 4
        assert sh_calc_win_rate(decisions) == 1.0

    def test_all_incorrect(self):
        decisions = [{"was_correct_4h": False}] * 3
        assert sh_calc_win_rate(decisions) == 0.0

    def test_none_excluded(self):
        decisions = [
            {"was_correct_4h": True},
            {"was_correct_4h": None},
            {"was_correct_4h": False},
        ]
        assert sh_calc_win_rate(decisions) == 0.5

    def test_empty(self):
        assert sh_calc_win_rate([]) == 0.0


class TestStrategyHealthCalcSharpe:
    """Tests for strategy_health._calc_sharpe."""

    def test_insufficient_samples(self):
        decisions = [{"outcome_4h_pct": 1.0}]
        assert sh_calc_sharpe(decisions) == 0.0

    def test_zero_std(self):
        decisions = [{"outcome_4h_pct": 5.0}] * 5
        assert sh_calc_sharpe(decisions) == 0.0

    def test_normal_calculation(self):
        decisions = [
            {"outcome_4h_pct": 1.0},
            {"outcome_4h_pct": 3.0},
            {"outcome_4h_pct": 2.0},
        ]
        result = sh_calc_sharpe(decisions)
        assert isinstance(result, float)
        assert result > 0


class TestAgentWinRates:
    """Tests for _agent_win_rates."""

    def test_multiple_agents(self):
        decisions = [
            {"agent_name": "conservative", "was_correct_4h": True},
            {"agent_name": "conservative", "was_correct_4h": False},
            {"agent_name": "aggressive", "was_correct_4h": True},
            {"agent_name": "aggressive", "was_correct_4h": True},
        ]
        rates = _agent_win_rates(decisions)
        assert rates["conservative"] == 0.5
        assert rates["aggressive"] == 1.0

    def test_none_agent_becomes_unknown(self):
        decisions = [{"agent_name": None, "was_correct_4h": True}]
        rates = _agent_win_rates(decisions)
        assert "unknown" in rates

    def test_empty(self):
        assert _agent_win_rates([]) == {}


class TestGenerateSuggestion:
    """Tests for _generate_suggestion."""

    def test_green_returns_normal(self):
        result = _generate_suggestion("GREEN", 10, 1.0, None)
        assert result == "정상 운영 중"

    def test_yellow_suggestion(self):
        result = _generate_suggestion("YELLOW", 10, 1.0, None)
        assert "보수적" in result

    def test_orange_with_worst_agent(self):
        result = _generate_suggestion("ORANGE", 10, 1.0, "aggressive")
        assert "aggressive" in result

    def test_red_suggestion(self):
        result = _generate_suggestion("RED", 10, 1.0, None)
        assert "즉시" in result

    def test_no_signal_for_3_days(self):
        result = _generate_suggestion("GREEN", 5, 4.0, None)
        assert "3일간" in result


class TestCheckHealth:
    """Tests for check_health."""

    @patch("strategy_health._send_telegram_alert")
    @patch("strategy_health._save_state")
    @patch("strategy_health._fetch_recent_decisions")
    def test_no_data_returns_unknown(self, mock_fetch, mock_save, mock_tg):
        mock_fetch.return_value = []
        result = check_health(quiet=True)
        assert result is not None
        assert result["status"] == "UNKNOWN"
        assert result["total_trades_7d"] == 0

    @patch("strategy_health._send_telegram_alert")
    @patch("strategy_health._save_state")
    @patch("strategy_health._fetch_recent_decisions")
    def test_healthy_data_green(self, mock_fetch, mock_save, mock_tg):
        now = datetime.now(KST)
        mock_fetch.return_value = [
            {
                "decision": "buy",
                "confidence": 0.8,
                "outcome_4h_pct": 1.5,
                "outcome_24h_pct": 2.0,
                "was_correct_4h": True,
                "created_at": now.isoformat(),
                "agent_name": "conservative",
            }
            for _ in range(5)
        ]
        result = check_health(quiet=True)
        assert result["status"] == "GREEN"
        assert result["win_rate_7d"] == 1.0
        mock_tg.assert_not_called()

    @patch("strategy_health._send_telegram_alert")
    @patch("strategy_health._save_state")
    @patch("strategy_health._fetch_recent_decisions")
    def test_red_status_sends_telegram(self, mock_fetch, mock_save, mock_tg):
        now = datetime.now(KST)
        # All incorrect => win_rate < 0.25 => RED
        mock_fetch.return_value = [
            {
                "decision": "buy",
                "confidence": 0.5,
                "outcome_4h_pct": -3.0,
                "outcome_24h_pct": -5.0,
                "was_correct_4h": False,
                "created_at": now.isoformat(),
                "agent_name": "aggressive",
            }
            for _ in range(8)
        ]
        result = check_health(quiet=False)
        assert result["status"] == "RED"
        mock_tg.assert_called_once()

    @patch("strategy_health._send_telegram_alert")
    @patch("strategy_health._save_state")
    @patch("strategy_health._fetch_recent_decisions")
    def test_quiet_mode_no_telegram(self, mock_fetch, mock_save, mock_tg):
        now = datetime.now(KST)
        mock_fetch.return_value = [
            {
                "decision": "buy",
                "outcome_4h_pct": -3.0,
                "was_correct_4h": False,
                "created_at": now.isoformat(),
                "agent_name": "moderate",
            }
            for _ in range(8)
        ]
        check_health(quiet=True)
        mock_tg.assert_not_called()


class TestGetHealthStatus:
    """Tests for get_health_status and get_health_summary."""

    @patch("strategy_health.STATE_FILE")
    def test_no_file_returns_unknown(self, mock_state_file):
        mock_state_file.exists.return_value = False
        assert get_health_status() == "UNKNOWN"

    @patch("strategy_health.STATE_FILE")
    def test_valid_state(self, mock_state_file):
        state = {"status": "YELLOW", "win_rate_7d": 0.4}
        mock_state_file.exists.return_value = True
        mock_state_file.read_text.return_value = json.dumps(state)
        assert get_health_status() == "YELLOW"

    @patch("strategy_health.STATE_FILE")
    def test_corrupt_json(self, mock_state_file):
        mock_state_file.exists.return_value = True
        mock_state_file.read_text.return_value = "corrupt"
        assert get_health_status() == "UNKNOWN"

    @patch("strategy_health.STATE_FILE")
    def test_get_health_summary_full(self, mock_state_file):
        state = {"status": "GREEN", "win_rate_7d": 0.65, "sharpe_7d": 0.8}
        mock_state_file.exists.return_value = True
        mock_state_file.read_text.return_value = json.dumps(state)
        result = get_health_summary()
        assert result["status"] == "GREEN"
        assert result["sharpe_7d"] == 0.8


# ===========================================================================
# PART 3: alert_aggregator.py
# ===========================================================================

from alert_aggregator import (
    collect_alerts,
    get_active_alerts,
    aggregate_and_send,
    _make_alert,
    _should_send,
    _collect_strategy_health_alerts,
    _collect_dynamic_risk_alerts,
    _collect_emergency_alerts,
    _collect_feedback_hub_alerts,
    _reset_stale_history,
    _load_json,
)


class TestMakeAlert:
    """Tests for _make_alert."""

    def test_creates_valid_alert(self):
        alert = _make_alert("CRITICAL", "test_source", "test message")
        assert alert["tier"] == "CRITICAL"
        assert alert["source"] == "test_source"
        assert alert["message"] == "test message"
        assert "timestamp" in alert


class TestCollectStrategyHealthAlerts:
    """Tests for _collect_strategy_health_alerts."""

    @patch("alert_aggregator._load_json")
    def test_red_status_critical(self, mock_load):
        mock_load.return_value = {"status": "RED", "win_rate": 20, "consecutive_losses": 8}
        alerts = _collect_strategy_health_alerts()
        tiers = [a["tier"] for a in alerts]
        assert "CRITICAL" in tiers

    @patch("alert_aggregator._load_json")
    def test_orange_status_high(self, mock_load):
        mock_load.return_value = {"status": "ORANGE", "win_rate": 30, "consecutive_losses": 2}
        alerts = _collect_strategy_health_alerts()
        assert any(a["tier"] == "HIGH" for a in alerts)

    @patch("alert_aggregator._load_json")
    def test_yellow_status_medium(self, mock_load):
        mock_load.return_value = {"status": "YELLOW", "win_rate": 45, "consecutive_losses": 1}
        alerts = _collect_strategy_health_alerts()
        assert any(a["tier"] == "MEDIUM" for a in alerts)

    @patch("alert_aggregator._load_json")
    def test_green_status_no_alerts(self, mock_load):
        mock_load.return_value = {"status": "GREEN", "win_rate": 60, "consecutive_losses": 0}
        alerts = _collect_strategy_health_alerts()
        assert len(alerts) == 0

    @patch("alert_aggregator._load_json")
    def test_consecutive_losses_5_adds_high(self, mock_load):
        mock_load.return_value = {"status": "GREEN", "win_rate": 60, "consecutive_losses": 5}
        alerts = _collect_strategy_health_alerts()
        assert any(a["tier"] == "HIGH" and "연속 손실" in a["message"] for a in alerts)

    @patch("alert_aggregator._load_json")
    def test_no_file_returns_empty(self, mock_load):
        mock_load.return_value = None
        assert _collect_strategy_health_alerts() == []


class TestCollectDynamicRiskAlerts:
    """Tests for _collect_dynamic_risk_alerts."""

    @patch("alert_aggregator._load_json")
    def test_critical_risk(self, mock_load):
        mock_load.return_value = {"risk_level": "CRITICAL", "sharpe_7d": -1.5, "adjusted_amount": 30000, "win_rate_7d": 0.20}
        alerts = _collect_dynamic_risk_alerts()
        assert any(a["tier"] == "CRITICAL" for a in alerts)

    @patch("alert_aggregator._load_json")
    def test_low_risk(self, mock_load):
        mock_load.return_value = {"risk_level": "LOW", "sharpe_7d": -0.3, "adjusted_amount": 80000, "win_rate_7d": 0.40}
        alerts = _collect_dynamic_risk_alerts()
        assert any(a["tier"] == "HIGH" for a in alerts)

    @patch("alert_aggregator._load_json")
    def test_normal_low_winrate(self, mock_load):
        mock_load.return_value = {"risk_level": "NORMAL", "sharpe_7d": 0.1, "adjusted_amount": 100000, "win_rate_7d": 0.40}
        alerts = _collect_dynamic_risk_alerts()
        assert any(a["tier"] == "MEDIUM" for a in alerts)

    @patch("alert_aggregator._load_json")
    def test_normal_good_winrate_no_alert(self, mock_load):
        mock_load.return_value = {"risk_level": "NORMAL", "sharpe_7d": 0.3, "adjusted_amount": 100000, "win_rate_7d": 0.55}
        alerts = _collect_dynamic_risk_alerts()
        assert len(alerts) == 0

    @patch("alert_aggregator._load_json")
    def test_no_file(self, mock_load):
        mock_load.return_value = None
        assert _collect_dynamic_risk_alerts() == []


class TestCollectEmergencyAlerts:
    """Tests for _collect_emergency_alerts."""

    @patch("alert_aggregator._load_json")
    @patch.dict(os.environ, {"EMERGENCY_STOP": "true"}, clear=False)
    def test_emergency_stop_env(self, mock_load):
        mock_load.return_value = None
        alerts = _collect_emergency_alerts()
        assert any(a["source"] == "emergency" for a in alerts)

    @patch("alert_aggregator._load_json")
    @patch.dict(os.environ, {"EMERGENCY_STOP": "false"}, clear=False)
    def test_auto_emergency_active(self, mock_load):
        mock_load.return_value = {"active": True, "reason": "급락"}
        alerts = _collect_emergency_alerts()
        assert any(a["source"] == "auto_emergency" for a in alerts)

    @patch("alert_aggregator._load_json")
    @patch.dict(os.environ, {"EMERGENCY_STOP": "false"}, clear=False)
    def test_no_emergency(self, mock_load):
        mock_load.return_value = {"active": False}
        alerts = _collect_emergency_alerts()
        assert len(alerts) == 0


class TestCollectFeedbackHubAlerts:
    """Tests for _collect_feedback_hub_alerts."""

    @patch("alert_aggregator._load_json")
    def test_disabled_models(self, mock_load):
        mock_load.return_value = {"disabled_rl_models": ["model_a", "model_b"]}
        alerts = _collect_feedback_hub_alerts()
        assert any(a["tier"] == "HIGH" and "RL 모델 비활성" in a["message"] for a in alerts)

    @patch("alert_aggregator._load_json")
    def test_low_rag_accuracy(self, mock_load):
        mock_load.return_value = {"rag_quality": {"rag_accuracy": 0.3, "rag_samples": 10}}
        alerts = _collect_feedback_hub_alerts()
        assert any(a["tier"] == "MEDIUM" and "RAG" in a["message"] for a in alerts)

    @patch("alert_aggregator._load_json")
    def test_rag_insufficient_samples(self, mock_load):
        mock_load.return_value = {"rag_quality": {"rag_accuracy": 0.3, "rag_samples": 2}}
        alerts = _collect_feedback_hub_alerts()
        # Not enough samples => no RAG alert
        assert not any("RAG" in a.get("message", "") for a in alerts)

    @patch("alert_aggregator._load_json")
    def test_no_file(self, mock_load):
        mock_load.return_value = None
        assert _collect_feedback_hub_alerts() == []


class TestShouldSend:
    """Tests for _should_send (anti-spam)."""

    def test_critical_first_time(self):
        state = {"last_critical_sent": None, "alert_history": {}}
        assert _should_send("CRITICAL", "test:key", state) is True

    def test_critical_within_interval(self):
        recent = (datetime.now(KST) - timedelta(minutes=5)).isoformat()
        state = {"last_critical_sent": recent, "alert_history": {}}
        assert _should_send("CRITICAL", "test:key", state) is False

    def test_critical_after_interval(self):
        old = (datetime.now(KST) - timedelta(minutes=15)).isoformat()
        state = {"last_critical_sent": old, "alert_history": {}}
        assert _should_send("CRITICAL", "test:key", state) is True

    def test_high_first_time(self):
        state = {"last_high_sent": None, "alert_history": {}}
        assert _should_send("HIGH", "test:key", state) is True

    def test_high_within_interval(self):
        recent = (datetime.now(KST) - timedelta(minutes=30)).isoformat()
        state = {"last_high_sent": recent, "alert_history": {}}
        assert _should_send("HIGH", "test:key", state) is False

    def test_suppress_threshold_blocks(self):
        state = {
            "last_critical_sent": None,
            "alert_history": {"test:key": {"count": 3, "last_sent": None}},
        }
        assert _should_send("CRITICAL", "test:key", state) is False

    @patch("alert_aggregator._now_kst")
    def test_medium_before_8am(self, mock_now):
        mock_now.return_value = datetime(2026, 3, 16, 7, 0, tzinfo=KST)
        state = {"last_medium_sent": None, "alert_history": {}}
        assert _should_send("MEDIUM", "test:key", state) is False

    @patch("alert_aggregator._now_kst")
    def test_medium_after_8am_first_time(self, mock_now):
        mock_now.return_value = datetime(2026, 3, 16, 9, 0, tzinfo=KST)
        state = {"last_medium_sent": None, "alert_history": {}}
        assert _should_send("MEDIUM", "test:key", state) is True

    @patch("alert_aggregator._now_kst")
    def test_medium_already_sent_today(self, mock_now):
        today_9am = datetime(2026, 3, 16, 9, 0, tzinfo=KST)
        mock_now.return_value = datetime(2026, 3, 16, 10, 0, tzinfo=KST)
        state = {"last_medium_sent": today_9am.isoformat(), "alert_history": {}}
        assert _should_send("MEDIUM", "test:key", state) is False

    def test_low_tier_always_false(self):
        state = {"alert_history": {}}
        assert _should_send("LOW", "test:key", state) is False


class TestResetStaleHistory:
    """Tests for _reset_stale_history."""

    @patch("alert_aggregator._now_kst")
    def test_removes_old_entries(self, mock_now):
        mock_now.return_value = datetime(2026, 3, 16, 12, 0, tzinfo=KST)
        old_time = (datetime(2026, 3, 14, 12, 0, tzinfo=KST)).isoformat()
        state = {
            "alert_history": {
                "old_key": {"count": 2, "last_sent": old_time},
            }
        }
        _reset_stale_history(state)
        assert "old_key" not in state["alert_history"]

    @patch("alert_aggregator._now_kst")
    def test_keeps_recent_entries(self, mock_now):
        mock_now.return_value = datetime(2026, 3, 16, 12, 0, tzinfo=KST)
        recent_time = (datetime(2026, 3, 16, 10, 0, tzinfo=KST)).isoformat()
        state = {
            "alert_history": {
                "recent_key": {"count": 1, "last_sent": recent_time},
            }
        }
        _reset_stale_history(state)
        assert "recent_key" in state["alert_history"]


class TestAggregateAndSend:
    """Tests for aggregate_and_send."""

    @patch("alert_aggregator._save_alert_state")
    @patch("alert_aggregator._load_alert_state")
    @patch("alert_aggregator.collect_alerts")
    def test_dry_run_no_telegram(self, mock_collect, mock_load_state, mock_save_state):
        mock_collect.return_value = [
            _make_alert("CRITICAL", "test", "critical alert"),
        ]
        mock_load_state.return_value = {
            "last_critical_sent": None,
            "last_high_sent": None,
            "last_medium_sent": None,
            "active_alerts": [],
            "suppressed_count": 0,
            "alert_history": {},
        }

        result = aggregate_and_send(dry_run=True)
        assert result["sent_count"] >= 1
        assert "tiers" in result
        assert result["tiers"]["CRITICAL"] == 1

    @patch("alert_aggregator._save_alert_state")
    @patch("alert_aggregator._load_alert_state")
    @patch("alert_aggregator.collect_alerts")
    def test_no_alerts_adds_low(self, mock_collect, mock_load_state, mock_save_state):
        mock_collect.return_value = []
        mock_load_state.return_value = {
            "last_critical_sent": None,
            "last_high_sent": None,
            "last_medium_sent": None,
            "active_alerts": [],
            "suppressed_count": 0,
            "alert_history": {},
        }

        result = aggregate_and_send(dry_run=True)
        assert result["tiers"]["LOW"] >= 1

    @patch("alert_aggregator._send_telegram")
    @patch("alert_aggregator._save_alert_state")
    @patch("alert_aggregator._load_alert_state")
    @patch("alert_aggregator.collect_alerts")
    def test_suppressed_alerts_counted(self, mock_collect, mock_load_state, mock_save_state, mock_tg):
        recent = (datetime.now(KST) - timedelta(minutes=2)).isoformat()
        mock_collect.return_value = [
            _make_alert("CRITICAL", "test", "msg"),
        ]
        mock_load_state.return_value = {
            "last_critical_sent": recent,
            "last_high_sent": None,
            "last_medium_sent": None,
            "active_alerts": [],
            "suppressed_count": 0,
            "alert_history": {},
        }

        result = aggregate_and_send(dry_run=False)
        assert result["suppressed_count"] >= 1
        mock_tg.assert_not_called()


class TestCollectAlerts:
    """Tests for collect_alerts integration."""

    @patch("alert_aggregator._collect_sentinel_alerts")
    @patch("alert_aggregator._collect_feedback_hub_alerts")
    @patch("alert_aggregator._collect_dynamic_risk_alerts")
    @patch("alert_aggregator._collect_strategy_health_alerts")
    @patch("alert_aggregator._collect_emergency_alerts")
    def test_aggregates_all_sources(self, mock_em, mock_sh, mock_dr, mock_fh, mock_se):
        mock_em.return_value = [_make_alert("CRITICAL", "emergency", "stop")]
        mock_sh.return_value = [_make_alert("HIGH", "health", "orange")]
        mock_dr.return_value = [_make_alert("MEDIUM", "risk", "low wr")]
        mock_fh.return_value = []
        mock_se.return_value = []

        alerts = collect_alerts()
        assert len(alerts) == 3

    @patch("alert_aggregator._collect_sentinel_alerts")
    @patch("alert_aggregator._collect_feedback_hub_alerts")
    @patch("alert_aggregator._collect_dynamic_risk_alerts")
    @patch("alert_aggregator._collect_strategy_health_alerts")
    @patch("alert_aggregator._collect_emergency_alerts")
    def test_all_empty(self, mock_em, mock_sh, mock_dr, mock_fh, mock_se):
        mock_em.return_value = []
        mock_sh.return_value = []
        mock_dr.return_value = []
        mock_fh.return_value = []
        mock_se.return_value = []

        alerts = collect_alerts()
        assert len(alerts) == 0

    @patch("alert_aggregator._collect_sentinel_alerts")
    @patch("alert_aggregator._collect_feedback_hub_alerts")
    @patch("alert_aggregator._collect_dynamic_risk_alerts")
    @patch("alert_aggregator._collect_strategy_health_alerts")
    @patch("alert_aggregator._collect_emergency_alerts")
    def test_get_active_alerts_same_as_collect(self, mock_em, mock_sh, mock_dr, mock_fh, mock_se):
        mock_em.return_value = [_make_alert("CRITICAL", "em", "x")]
        mock_sh.return_value = []
        mock_dr.return_value = []
        mock_fh.return_value = []
        mock_se.return_value = []

        alerts = get_active_alerts()
        assert len(alerts) == 1
        assert alerts[0]["tier"] == "CRITICAL"


class TestLoadJson:
    """Tests for _load_json edge cases."""

    def test_nonexistent_file(self, tmp_path):
        result = _load_json(tmp_path / "nonexistent.json")
        assert result is None

    def test_valid_json(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text('{"key": "value"}', encoding="utf-8")
        result = _load_json(f)
        assert result == {"key": "value"}

    def test_invalid_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not json", encoding="utf-8")
        result = _load_json(f)
        assert result is None
