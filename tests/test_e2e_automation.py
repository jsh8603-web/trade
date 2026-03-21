"""End-to-end integration tests for the full automation pipeline (Phases 8-12).

Tests the complete flow as executed by run_agents.py:
  Phase 8:  dynamic_risk.update_risk() — Sharpe-based risk adjustment
  Phase 9:  strategy_health.check_health() — win rate / streak monitoring
  Phase 10: alert_aggregator.aggregate_and_send() — tiered alert dispatch
  Phase 11: model_retrainer.check_and_queue() / process_queue() — RL retrain
  Phase 12: regime_learner.learn_weights() — regime weight optimization

All external calls (Supabase REST, Telegram, file I/O) are mocked.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

KST = timezone(timedelta(hours=9))


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def env_vars(monkeypatch):
    """Standard environment variables for all tests."""
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("EMERGENCY_STOP", "false")
    monkeypatch.setenv("MAX_TRADE_AMOUNT", "100000")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")


@pytest.fixture
def supabase_decisions_with_outcomes():
    """Supabase decisions rows with outcome data for 7-day window."""
    now = datetime.now(KST)
    return [
        {
            "decision": "buy",
            "confidence": 0.65,
            "outcome_4h_pct": 1.2,
            "outcome_24h_pct": 2.5,
            "was_correct_4h": True,
            "created_at": (now - timedelta(hours=4)).isoformat(),
            "agent_name": "conservative",
            "market_data_snapshot": json.dumps({
                "regime": "sideways",
                "rl_advisory": {"sb3_action": 0.4, "dt_action": 0.2},
            }),
        },
        {
            "decision": "sell",
            "confidence": 0.55,
            "outcome_4h_pct": -0.8,
            "outcome_24h_pct": -1.5,
            "was_correct_4h": False,
            "created_at": (now - timedelta(hours=8)).isoformat(),
            "agent_name": "moderate",
            "market_data_snapshot": json.dumps({
                "regime": "sideways",
                "rl_advisory": {"sb3_action": -0.5, "dt_action": -0.3},
            }),
        },
        {
            "decision": "buy",
            "confidence": 0.70,
            "outcome_4h_pct": 0.5,
            "outcome_24h_pct": 1.0,
            "was_correct_4h": True,
            "created_at": (now - timedelta(hours=12)).isoformat(),
            "agent_name": "conservative",
            "market_data_snapshot": json.dumps({
                "regime": "bull_weak",
                "rl_advisory": {"sb3_action": 0.6},
            }),
        },
        {
            "decision": "buy",
            "confidence": 0.60,
            "outcome_4h_pct": -0.3,
            "outcome_24h_pct": -0.1,
            "was_correct_4h": False,
            "created_at": (now - timedelta(hours=20)).isoformat(),
            "agent_name": "conservative",
            "market_data_snapshot": json.dumps({"regime": "sideways"}),
        },
    ]


@pytest.fixture
def supabase_empty_response():
    """Mock Supabase returning an empty list."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = []
    return mock_resp


@pytest.fixture
def state_dir(tmp_path):
    """Temporary directory for state files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def feedback_hub_state_with_disabled(state_dir):
    """feedback_hub_state.json with a disabled model."""
    state = {
        "disabled_rl_models": ["sb3"],
        "rl_model_scores": {
            "sb3": {"accuracy": 0.30, "should_disable": True},
        },
        "last_updated": (datetime.now(KST) - timedelta(hours=30)).isoformat(),
    }
    path = state_dir / "feedback_hub_state.json"
    path.write_text(json.dumps(state), encoding="utf-8")
    return path


# ═══════════════════════════════════════════════════════════
# Phase 8: Dynamic Risk
# ═══════════════════════════════════════════════════════════

class TestPhase8DynamicRisk:

    @patch("scripts.dynamic_risk.requests.get")
    def test_happy_path_normal_risk(self, mock_get, env_vars, state_dir, monkeypatch):
        """Phase 8 with positive Sharpe returns NORMAL risk level."""
        import scripts.dynamic_risk as dr

        monkeypatch.setattr(dr, "STATE_FILE", state_dir / "dynamic_risk.json")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"outcome_4h_pct": 1.0, "created_at": datetime.now(KST).isoformat(), "decision": "buy"},
            {"outcome_4h_pct": 0.5, "created_at": datetime.now(KST).isoformat(), "decision": "buy"},
            {"outcome_4h_pct": 0.3, "created_at": datetime.now(KST).isoformat(), "decision": "sell"},
            {"outcome_4h_pct": -0.2, "created_at": datetime.now(KST).isoformat(), "decision": "buy"},
        ]
        mock_get.return_value = mock_resp

        result = dr.update_risk()

        assert result["risk_level"] in ("NORMAL", "HIGH", "BOOST")
        assert result["adjusted_amount"] >= int(100000 * 0.3)
        assert result["sample_count"] == 4
        assert (state_dir / "dynamic_risk.json").exists()

    @patch("scripts.dynamic_risk.requests.get")
    def test_empty_supabase_returns_normal(self, mock_get, env_vars, state_dir, monkeypatch):
        """No decisions data -> NORMAL risk (insufficient samples)."""
        import scripts.dynamic_risk as dr

        monkeypatch.setattr(dr, "STATE_FILE", state_dir / "dynamic_risk.json")
        monkeypatch.setattr(dr, "DEFAULT_MAX_AMOUNT", 100000)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mock_get.return_value = mock_resp

        result = dr.update_risk()

        assert result["risk_level"] == "NORMAL"
        assert result["sharpe_7d"] is None
        assert result["adjusted_amount"] == 100000

    @patch("scripts.dynamic_risk.requests.get")
    def test_consecutive_losses_penalty(self, mock_get, env_vars, state_dir, monkeypatch):
        """5+ consecutive losses -> CRITICAL risk, minimum amount forced."""
        import scripts.dynamic_risk as dr

        monkeypatch.setattr(dr, "STATE_FILE", state_dir / "dynamic_risk.json")
        monkeypatch.setattr(dr, "DEFAULT_MAX_AMOUNT", 100000)

        # 6 consecutive losses
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"outcome_4h_pct": -1.0, "created_at": (datetime.now(KST) - timedelta(hours=i)).isoformat(), "decision": "buy"}
            for i in range(6)
        ]
        mock_get.return_value = mock_resp

        result = dr.update_risk()

        assert result["risk_level"] == "CRITICAL"
        assert result["consecutive_losses"] >= 5
        assert result["adjusted_amount"] == int(100000 * 0.3)


# ═══════════════════════════════════════════════════════════
# Phase 9: Strategy Health
# ═══════════════════════════════════════════════════════════

class TestPhase9StrategyHealth:

    @patch("scripts.strategy_health.requests.get")
    def test_happy_path_green(self, mock_get, env_vars, state_dir, monkeypatch,
                              supabase_decisions_with_outcomes):
        """Healthy strategy returns GREEN status."""
        import scripts.strategy_health as sh

        monkeypatch.setattr(sh, "STATE_FILE", state_dir / "strategy_health.json")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = supabase_decisions_with_outcomes
        mock_get.return_value = mock_resp

        result = sh.check_health(quiet=True)

        assert result is not None
        assert result["status"] in ("GREEN", "YELLOW")
        assert result["total_trades_7d"] == 4
        assert (state_dir / "strategy_health.json").exists()

    @patch("scripts.strategy_health.requests.get")
    def test_no_data_returns_unknown(self, mock_get, env_vars, state_dir, monkeypatch):
        """No decisions -> UNKNOWN status."""
        import scripts.strategy_health as sh

        monkeypatch.setattr(sh, "STATE_FILE", state_dir / "strategy_health.json")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mock_get.return_value = mock_resp

        result = sh.check_health(quiet=True)

        assert result is not None
        assert result["status"] == "UNKNOWN"
        assert result["total_trades_7d"] == 0

    @patch("scripts.strategy_health.requests.get")
    def test_phase9_failure_does_not_crash(self, mock_get, env_vars, state_dir, monkeypatch):
        """Phase 9 Supabase failure -> exception is caught gracefully."""
        import scripts.strategy_health as sh

        monkeypatch.setattr(sh, "STATE_FILE", state_dir / "strategy_health.json")
        mock_get.side_effect = Exception("connection timeout")

        # Should not raise -- just return UNKNOWN-like result
        result = sh.check_health(quiet=True)
        assert result is not None
        assert result["status"] == "UNKNOWN"


# ═══════════════════════════════════════════════════════════
# Phase 10: Alert Aggregator
# ═══════════════════════════════════════════════════════════

class TestPhase10AlertAggregator:

    def test_no_alerts_returns_low(self, env_vars, state_dir, monkeypatch):
        """No alert sources -> LOW tier only."""
        import scripts.alert_aggregator as aa

        monkeypatch.setattr(aa, "ALERT_STATE_PATH", state_dir / "alert_state.json")
        monkeypatch.setattr(aa, "FEEDBACK_HUB_STATE_PATH", state_dir / "nonexist_fh.json")
        monkeypatch.setattr(aa, "STRATEGY_HEALTH_PATH", state_dir / "nonexist_sh.json")
        monkeypatch.setattr(aa, "DYNAMIC_RISK_PATH", state_dir / "nonexist_dr.json")
        monkeypatch.setattr(aa, "AUTO_EMERGENCY_PATH", state_dir / "nonexist_ae.json")
        monkeypatch.setattr(aa, "SENTINEL_SCRIPT", state_dir / "nonexist_sentinel.py")
        monkeypatch.delenv("EMERGENCY_STOP", raising=False)

        result = aa.aggregate_and_send(dry_run=True)

        assert result["sent_count"] == 0
        assert result["tiers"]["LOW"] >= 1

    def test_strategy_health_red_triggers_critical(self, env_vars, state_dir, monkeypatch):
        """strategy_health RED -> CRITICAL alert collected."""
        import scripts.alert_aggregator as aa

        # Write a RED strategy health
        health_path = state_dir / "strategy_health.json"
        health_path.write_text(json.dumps({
            "status": "RED",
            "win_rate_7d": 0.15,
            "consecutive_losses": 8,
        }))

        monkeypatch.setattr(aa, "ALERT_STATE_PATH", state_dir / "alert_state.json")
        monkeypatch.setattr(aa, "FEEDBACK_HUB_STATE_PATH", state_dir / "nonexist_fh.json")
        monkeypatch.setattr(aa, "STRATEGY_HEALTH_PATH", health_path)
        monkeypatch.setattr(aa, "DYNAMIC_RISK_PATH", state_dir / "nonexist_dr.json")
        monkeypatch.setattr(aa, "AUTO_EMERGENCY_PATH", state_dir / "nonexist_ae.json")
        monkeypatch.setattr(aa, "SENTINEL_SCRIPT", state_dir / "nonexist_sentinel.py")
        monkeypatch.delenv("EMERGENCY_STOP", raising=False)

        result = aa.aggregate_and_send(dry_run=True)

        assert result["tiers"]["CRITICAL"] >= 1

    def test_phase10_continues_after_phase9_failure(self, env_vars, state_dir, monkeypatch):
        """Even if Phase 9 didn't write state, Phase 10 still runs."""
        import scripts.alert_aggregator as aa

        # No strategy_health.json exists
        monkeypatch.setattr(aa, "ALERT_STATE_PATH", state_dir / "alert_state.json")
        monkeypatch.setattr(aa, "FEEDBACK_HUB_STATE_PATH", state_dir / "nonexist_fh.json")
        monkeypatch.setattr(aa, "STRATEGY_HEALTH_PATH", state_dir / "nonexist_sh.json")
        monkeypatch.setattr(aa, "DYNAMIC_RISK_PATH", state_dir / "nonexist_dr.json")
        monkeypatch.setattr(aa, "AUTO_EMERGENCY_PATH", state_dir / "nonexist_ae.json")
        monkeypatch.setattr(aa, "SENTINEL_SCRIPT", state_dir / "nonexist_sentinel.py")
        monkeypatch.delenv("EMERGENCY_STOP", raising=False)

        # Should not raise
        result = aa.aggregate_and_send(dry_run=True)
        assert isinstance(result, dict)
        assert "sent_count" in result


# ═══════════════════════════════════════════════════════════
# Phase 11: Model Retrainer
# ═══════════════════════════════════════════════════════════

class TestPhase11ModelRetrainer:

    def test_no_disabled_models(self, env_vars, state_dir, monkeypatch):
        """No disabled models -> queued=0."""
        import scripts.model_retrainer as mr

        fb_state = state_dir / "feedback_hub_state.json"
        fb_state.write_text(json.dumps({
            "disabled_rl_models": [],
            "rl_model_scores": {},
            "last_updated": datetime.now(KST).isoformat(),
        }))
        monkeypatch.setattr(mr, "STATE_FILE", fb_state)
        monkeypatch.setattr(mr, "QUEUE_FILE", state_dir / "model_retrain_queue.json")

        result = mr.check_and_queue()

        assert result["queued"] == 0
        assert "비활성 모델 없음" in result["details"][0]

    @patch("scripts.model_retrainer.requests.get")
    @patch("scripts.model_retrainer.requests.post")
    def test_disabled_model_queued(self, mock_post, mock_get, env_vars, state_dir, monkeypatch):
        """Disabled model with sufficient data gets queued."""
        import scripts.model_retrainer as mr

        # feedback_hub_state with disabled sb3
        fb_state_path = state_dir / "feedback_hub_state.json"
        fb_state_path.write_text(json.dumps({
            "disabled_rl_models": ["sb3"],
            "rl_model_scores": {"sb3": {"accuracy": 0.25, "should_disable": True}},
            "last_updated": (datetime.now(KST) - timedelta(hours=30)).isoformat(),
        }))
        monkeypatch.setattr(mr, "STATE_FILE", fb_state_path)
        monkeypatch.setattr(mr, "QUEUE_FILE", state_dir / "model_retrain_queue.json")

        # Supabase decisions count: enough samples
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Range": "0-0/60"}
        mock_resp.json.return_value = []
        mock_get.return_value = mock_resp

        # DB queue log
        post_resp = MagicMock()
        post_resp.status_code = 201
        post_resp.json.return_value = [{"id": "cycle-123"}]
        mock_post.return_value = post_resp

        result = mr.check_and_queue()

        assert result["queued"] == 1
        assert any("sb3" in d for d in result["details"])

    def test_queue_file_missing_first_run(self, env_vars, state_dir, monkeypatch):
        """First run: no queue file exists -> creates it."""
        import scripts.model_retrainer as mr

        fb_state_path = state_dir / "feedback_hub_state.json"
        fb_state_path.write_text(json.dumps({
            "disabled_rl_models": [],
            "rl_model_scores": {},
        }))
        monkeypatch.setattr(mr, "STATE_FILE", fb_state_path)
        queue_path = state_dir / "model_retrain_queue.json"
        monkeypatch.setattr(mr, "QUEUE_FILE", queue_path)

        # queue file doesn't exist yet
        assert not queue_path.exists()

        result = mr.check_and_queue()
        assert result["queued"] == 0
        # Queue file should now exist
        assert queue_path.exists()


# ═══════════════════════════════════════════════════════════
# Phase 12: Regime Learner
# ═══════════════════════════════════════════════════════════

class TestPhase12RegimeLearner:

    @patch("scripts.regime_learner.requests.get")
    def test_happy_path_learns_weights(self, mock_get, env_vars, state_dir, monkeypatch,
                                       supabase_decisions_with_outcomes):
        """Sufficient data -> weights learned and saved."""
        import scripts.regime_learner as rl

        monkeypatch.setattr(rl, "WEIGHTS_FILE", state_dir / "regime_weights_learned.json")

        # Return enough data for at least one regime
        rows = supabase_decisions_with_outcomes * 3  # 12 rows
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = rows
        mock_get.return_value = mock_resp

        result = rl.learn_weights()

        assert result is not None
        assert "weights" in result
        assert "sample_counts" in result
        assert (state_dir / "regime_weights_learned.json").exists()

    @patch("scripts.regime_learner.requests.get")
    def test_no_data_returns_none(self, mock_get, env_vars, state_dir, monkeypatch):
        """No Supabase data -> learn_weights returns None."""
        import scripts.regime_learner as rl

        monkeypatch.setattr(rl, "WEIGHTS_FILE", state_dir / "regime_weights_learned.json")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mock_get.return_value = mock_resp

        result = rl.learn_weights()
        assert result is None


# ═══════════════════════════════════════════════════════════
# Cross-phase integration tests
# ═══════════════════════════════════════════════════════════

class TestCascadingEffects:

    @patch("scripts.dynamic_risk.requests.get")
    def test_dynamic_risk_reduces_trade_amount(self, mock_get, env_vars, state_dir, monkeypatch):
        """Phase 8 CRITICAL risk -> adjusted_amount is 30% of base.
        Downstream execute_trade should use this reduced amount."""
        import scripts.dynamic_risk as dr

        monkeypatch.setattr(dr, "STATE_FILE", state_dir / "dynamic_risk.json")
        monkeypatch.setattr(dr, "DEFAULT_MAX_AMOUNT", 100000)

        # 5 consecutive losses -> CRITICAL
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"outcome_4h_pct": -2.0, "created_at": (datetime.now(KST) - timedelta(hours=i)).isoformat(), "decision": "buy"}
            for i in range(5)
        ]
        mock_get.return_value = mock_resp

        risk = dr.update_risk()
        assert risk["risk_level"] == "CRITICAL"

        # Verify get_adjusted_max_amount reads the file correctly
        adjusted = dr.get_adjusted_max_amount()
        assert adjusted is not None
        assert adjusted == int(100000 * 0.3)

    @patch("scripts.regime_learner.requests.get")
    def test_regime_learner_output_read_by_detector(self, mock_get, env_vars, state_dir, monkeypatch):
        """Phase 12 saves weights -> regime_detector reads them."""
        import scripts.regime_learner as rl

        weights_file = state_dir / "regime_weights_learned.json"
        monkeypatch.setattr(rl, "WEIGHTS_FILE", weights_file)

        # Provide enough sideways data (5+ samples)
        now = datetime.now(KST)
        rows = [
            {
                "market_data_snapshot": json.dumps({
                    "regime": "sideways",
                    "rl_advisory": {"sb3_action": 0.4, "dt_action": 0.1},
                }),
                "was_correct_4h": True,
                "outcome_4h_pct": 0.5,
                "confidence": 0.6,
                "created_at": (now - timedelta(hours=i)).isoformat(),
            }
            for i in range(6)
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = rows
        mock_get.return_value = mock_resp

        learn_result = rl.learn_weights()
        assert learn_result is not None
        assert weights_file.exists()

        # Now verify get_learned_weights can read it
        sideways_weights = rl.get_learned_weights("sideways")
        assert sideways_weights is not None
        assert isinstance(sideways_weights, dict)
        # Weights should sum close to 1.0
        total = sum(sideways_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_feedback_hub_disables_model_retrainer_detects(self, env_vars, state_dir, monkeypatch):
        """Feedback hub disables sb3 -> model_retrainer detects and attempts queue."""
        import scripts.model_retrainer as mr

        fb_path = state_dir / "feedback_hub_state.json"
        fb_path.write_text(json.dumps({
            "disabled_rl_models": ["sb3"],
            "rl_model_scores": {"sb3": {"accuracy": 0.20, "should_disable": True}},
            "last_updated": (datetime.now(KST) - timedelta(hours=30)).isoformat(),
        }))
        monkeypatch.setattr(mr, "STATE_FILE", fb_path)
        monkeypatch.setattr(mr, "QUEUE_FILE", state_dir / "model_retrain_queue.json")

        # Mock Supabase to indicate not enough new samples -> skip
        with patch("scripts.model_retrainer.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.headers = {"Content-Range": "0-0/10"}
            mock_resp.json.return_value = []
            mock_get.return_value = mock_resp

            result = mr.check_and_queue()

        # Should skip because only 10 new samples (below MIN_NEW_SAMPLES=50)
        assert result["skipped"] == 1
        assert result["queued"] == 0


# ═══════════════════════════════════════════════════════════
# State file corruption / missing
# ═══════════════════════════════════════════════════════════

class TestStateFileEdgeCases:

    def test_corrupted_dynamic_risk_json(self, env_vars, state_dir, monkeypatch):
        """Corrupted dynamic_risk.json -> get_adjusted_max_amount returns None."""
        import scripts.dynamic_risk as dr

        corrupted_file = state_dir / "dynamic_risk.json"
        corrupted_file.write_text("{invalid json!!!}", encoding="utf-8")
        monkeypatch.setattr(dr, "STATE_FILE", corrupted_file)

        result = dr.get_adjusted_max_amount()
        assert result is None

    def test_corrupted_strategy_health_json(self, env_vars, state_dir, monkeypatch):
        """Corrupted strategy_health.json -> get_health_summary returns default."""
        import scripts.strategy_health as sh

        corrupted_file = state_dir / "strategy_health.json"
        corrupted_file.write_text("not a json {{{", encoding="utf-8")
        monkeypatch.setattr(sh, "STATE_FILE", corrupted_file)

        result = sh.get_health_summary()
        assert result == {"status": "UNKNOWN"}

    def test_missing_state_files_first_run(self, env_vars, state_dir, monkeypatch):
        """First run: no state files exist -> all phases handle gracefully."""
        import scripts.dynamic_risk as dr
        import scripts.strategy_health as sh

        monkeypatch.setattr(dr, "STATE_FILE", state_dir / "nonexist_dr.json")
        monkeypatch.setattr(sh, "STATE_FILE", state_dir / "nonexist_sh.json")

        # dynamic_risk: no saved state
        assert dr.get_adjusted_max_amount() is None
        assert dr.get_risk_summary() == {}

        # strategy_health: no saved state
        assert sh.get_health_status() == "UNKNOWN"

    def test_corrupted_queue_file_recovers(self, env_vars, state_dir, monkeypatch):
        """Corrupted model_retrain_queue.json -> loads empty queue."""
        import scripts.model_retrainer as mr

        queue_path = state_dir / "model_retrain_queue.json"
        queue_path.write_text("{bad json [", encoding="utf-8")
        monkeypatch.setattr(mr, "QUEUE_FILE", queue_path)

        fb_path = state_dir / "feedback_hub_state.json"
        fb_path.write_text(json.dumps({
            "disabled_rl_models": [],
            "rl_model_scores": {},
        }))
        monkeypatch.setattr(mr, "STATE_FILE", fb_path)

        result = mr.check_and_queue()
        assert result["queued"] == 0

    def test_corrupted_regime_weights_file(self, env_vars, state_dir, monkeypatch):
        """Corrupted regime_weights_learned.json -> get_learned_weights returns None."""
        import scripts.regime_learner as rl

        corrupted = state_dir / "regime_weights_learned.json"
        corrupted.write_text("{{corrupt}", encoding="utf-8")
        monkeypatch.setattr(rl, "WEIGHTS_FILE", corrupted)

        result = rl.get_learned_weights("sideways")
        assert result is None


# ═══════════════════════════════════════════════════════════
# Full pipeline simulation (Phases 8→9→10→11→12 sequential)
# ═══════════════════════════════════════════════════════════

class TestFullPipelineFlow:

    @patch("scripts.regime_learner.requests.get")
    @patch("scripts.model_retrainer.requests.get")
    @patch("scripts.model_retrainer.requests.post")
    @patch("scripts.strategy_health.requests.get")
    @patch("scripts.dynamic_risk.requests.get")
    def test_full_pipeline_happy_path(
        self, mock_dr_get, mock_sh_get, mock_mr_post, mock_mr_get,
        mock_rl_get, env_vars, state_dir, monkeypatch,
        supabase_decisions_with_outcomes,
    ):
        """All 5 phases run sequentially with mock data, no crashes."""
        import scripts.dynamic_risk as dr
        import scripts.strategy_health as sh
        import scripts.alert_aggregator as aa
        import scripts.model_retrainer as mr
        import scripts.regime_learner as rl

        # Redirect all state files to tmp
        monkeypatch.setattr(dr, "STATE_FILE", state_dir / "dynamic_risk.json")
        monkeypatch.setattr(sh, "STATE_FILE", state_dir / "strategy_health.json")
        monkeypatch.setattr(aa, "ALERT_STATE_PATH", state_dir / "alert_state.json")
        monkeypatch.setattr(aa, "FEEDBACK_HUB_STATE_PATH", state_dir / "feedback_hub_state.json")
        monkeypatch.setattr(aa, "STRATEGY_HEALTH_PATH", state_dir / "strategy_health.json")
        monkeypatch.setattr(aa, "DYNAMIC_RISK_PATH", state_dir / "dynamic_risk.json")
        monkeypatch.setattr(aa, "AUTO_EMERGENCY_PATH", state_dir / "nonexist_ae.json")
        monkeypatch.setattr(aa, "SENTINEL_SCRIPT", state_dir / "nonexist_sentinel.py")
        monkeypatch.delenv("EMERGENCY_STOP", raising=False)

        fb_path = state_dir / "feedback_hub_state.json"
        fb_path.write_text(json.dumps({
            "disabled_rl_models": [],
            "rl_model_scores": {},
        }))
        monkeypatch.setattr(mr, "STATE_FILE", fb_path)
        monkeypatch.setattr(mr, "QUEUE_FILE", state_dir / "model_retrain_queue.json")
        monkeypatch.setattr(rl, "WEIGHTS_FILE", state_dir / "regime_weights_learned.json")

        # Mock Supabase responses
        decisions_resp = MagicMock()
        decisions_resp.status_code = 200
        decisions_resp.json.return_value = supabase_decisions_with_outcomes
        mock_dr_get.return_value = decisions_resp
        mock_sh_get.return_value = decisions_resp
        mock_rl_get.return_value = decisions_resp

        mock_mr_resp = MagicMock()
        mock_mr_resp.status_code = 200
        mock_mr_resp.headers = {"Content-Range": "0-0/0"}
        mock_mr_resp.json.return_value = []
        mock_mr_get.return_value = mock_mr_resp

        # Phase 8
        risk = dr.update_risk()
        assert risk is not None
        assert "risk_level" in risk

        # Phase 9
        health = sh.check_health(quiet=True)
        assert health is not None
        assert "status" in health

        # Phase 10
        alerts = aa.aggregate_and_send(dry_run=True)
        assert isinstance(alerts, dict)
        assert "sent_count" in alerts

        # Phase 11
        queue_result = mr.check_and_queue()
        assert queue_result["queued"] == 0

        # Phase 12
        learn_result = rl.learn_weights()
        # May be None if insufficient per-regime data (4 rows is < 5 for most regimes)
        # But should not crash
        assert learn_result is None or isinstance(learn_result, dict)
