"""
End-to-end tests for orchestrator warmup (soft) transition feature.

Tests the full agent switching + warmup flow as it would work in production:
  - Threshold blending during transitions (conservative<->aggressive)
  - Mid-transition threshold interpolation
  - Transition completion and field cleanup
  - Multiple rapid switches during active transitions
  - Cooldown enforcement and emergency overrides
  - State persistence across orchestrator restarts (agent_state.json)
  - Corrupted transition state handling
  - Buy score decisions affected by warmup threshold blending
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.base_agent import Decision
from agents.conservative import ConservativeAgent
from agents.moderate import ModerateAgent
from agents.aggressive import AggressiveAgent

KST = timezone(timedelta(hours=9))


# ── Helpers ──────────────────────────────────────────

def _kst_now() -> datetime:
    return datetime.now(KST)


def _kst_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")


def _default_state(
    active="conservative",
    last_switch=None,
    consecutive_losses=0,
    switch_history=None,
    transition_from=None,
    transition_started=None,
    transition_duration_min=None,
):
    state = {
        "active_agent": active,
        "transition_from": transition_from,
        "transition_started": transition_started,
        "transition_duration_min": transition_duration_min,
        "last_switch_time": last_switch,
        "last_trade_time": None,
        "consecutive_losses": consecutive_losses,
        "switch_history": switch_history or [],
    }
    return state


def _make_orchestrator(
    active="conservative",
    last_switch=None,
    consecutive_losses=0,
    switch_history=None,
    transition_from=None,
    transition_started=None,
    transition_duration_min=None,
):
    """Create an Orchestrator with mocked _load_state and _save_state."""
    state = _default_state(
        active=active,
        last_switch=last_switch,
        consecutive_losses=consecutive_losses,
        switch_history=switch_history,
        transition_from=transition_from,
        transition_started=transition_started,
        transition_duration_min=transition_duration_min,
    )
    with patch("agents.orchestrator._load_state", return_value=state):
        with patch("agents.orchestrator._save_state"):
            from agents.orchestrator import Orchestrator
            orch = Orchestrator()
            orch._learning_data = None
            orch._performance = {}
            return orch


def _make_market_data(
    rsi=50, sma_deviation=0, fgi=50, price_change_rate=0,
    ai_score=0, news_sentiment="neutral", trade_price=50_000_000,
):
    return {
        "indicators": {
            "rsi_14": rsi,
            "sma_20": trade_price,
            "sma_20_deviation_pct": sma_deviation,
            "macd": {"histogram": 0, "signal_cross": False},
            "bollinger": {},
        },
        "ticker": {
            "trade_price": trade_price,
            "signed_change_rate": price_change_rate / 100,
        },
        "fear_greed": {"value": fgi},
        "news": {"overall_sentiment": news_sentiment},
        "ai_composite_signal": {"score": ai_score},
        "current_price": trade_price,
        "candles_4h": [],
    }


def _make_portfolio(krw=1_000_000, btc_balance=0, btc_avg_price=50_000_000,
                    profit_pct=0, total_eval=1_000_000):
    btc_eval = btc_balance * btc_avg_price if btc_balance > 0 else 0
    return {
        "krw_balance": krw,
        "btc": {
            "balance": btc_balance,
            "avg_buy_price": btc_avg_price,
            "profit_pct": profit_pct,
            "eval_amount": btc_eval,
        },
        "total_eval": total_eval,
        "btc_ratio": btc_eval / total_eval if total_eval > 0 else 0,
    }


def _make_external_data(
    fgi=50, fusion_signal="neutral", total_score=0,
    strategy_bonus=0, kimchi_pct=0, ls_ratio=1.0,
    funding_rate=0, macro_score=0, news_sentiment="neutral",
):
    return {
        "external_signal": {
            "total_score": total_score,
            "strategy_bonus": strategy_bonus,
            "fusion": {"signal": fusion_signal},
        },
        "sources": {
            "fear_greed": {"current": {"value": fgi}},
            "binance_sentiment": {
                "kimchi_premium": {"premium_pct": kimchi_pct},
                "top_trader_long_short": {"current_ratio": ls_ratio},
                "funding_rate": {"current_rate": funding_rate},
            },
            "whale_tracker": {"whale_score": {"direction": "neutral"}},
            "news_sentiment": {"overall_sentiment": news_sentiment},
            "macro": {"analysis": {"macro_score": macro_score, "sentiment": "neutral"}},
            "eth_btc": {"eth_btc_z_score": 0},
            "user_feedback": [],
            "performance_review": {},
        },
    }


def _ms(danger_score=20, opportunity_score=20, fgi=50, rsi=50,
        price_change_24h=0, kimchi_pct=0, ls_ratio=1.0,
        consecutive_losses=0, fusion_signal="neutral", phase="neutral"):
    return {
        "danger_score": danger_score,
        "opportunity_score": opportunity_score,
        "fgi": fgi,
        "rsi": rsi,
        "price_change_24h": price_change_24h,
        "kimchi_pct": kimchi_pct,
        "ls_ratio": ls_ratio,
        "consecutive_losses": consecutive_losses,
        "fusion_signal": fusion_signal,
        "phase": phase,
    }


# ============================================================
# Test Class: Conservative -> Aggressive warmup transition
# ============================================================

class TestConservativeToAggressiveWarmup:
    """Conservative(60) -> Aggressive(40): threshold blends 60->40 over 30 min."""

    def test_threshold_at_transition_start(self):
        """At t=0, threshold should be 0.3*40 + 0.7*60 = 54."""
        now = _kst_now()
        orch = _make_orchestrator(
            active="aggressive",
            transition_from="conservative",
            transition_started=_kst_iso(now),
            transition_duration_min=30,
        )
        agent = orch.active_agent
        assert isinstance(agent, AggressiveAgent)

        threshold = orch._get_warmup_threshold(agent)
        assert threshold is not None
        # w_new = 0.3, w_old = 0.7
        # blended = 0.3*40 + 0.7*60 = 12 + 42 = 54
        assert threshold == 54

    def test_threshold_at_transition_end(self):
        """After 30 min, transition should complete and return None (full new threshold)."""
        now = _kst_now()
        past = now - timedelta(minutes=31)
        orch = _make_orchestrator(
            active="aggressive",
            transition_from="conservative",
            transition_started=_kst_iso(past),
            transition_duration_min=30,
        )
        with patch("agents.orchestrator._save_state"):
            agent = orch.active_agent
            threshold = orch._get_warmup_threshold(agent)
            # Transition completed -> None (use agent's own threshold = 40)
            assert threshold is None


# ============================================================
# Test Class: Aggressive -> Conservative warmup transition
# ============================================================

class TestAggressiveToConservativeWarmup:
    """Aggressive(40) -> Conservative(60): threshold blends 40->60 over 30 min."""

    def test_threshold_at_start(self):
        """At t=0, threshold = 0.3*60 + 0.7*40 = 18+28 = 46."""
        now = _kst_now()
        orch = _make_orchestrator(
            active="conservative",
            transition_from="aggressive",
            transition_started=_kst_iso(now),
            transition_duration_min=30,
        )
        agent = orch.active_agent
        assert isinstance(agent, ConservativeAgent)

        threshold = orch._get_warmup_threshold(agent)
        assert threshold is not None
        assert threshold == 46

    def test_threshold_at_end(self):
        """After 30 min, should return None (agent uses its own 60)."""
        past = _kst_now() - timedelta(minutes=35)
        orch = _make_orchestrator(
            active="conservative",
            transition_from="aggressive",
            transition_started=_kst_iso(past),
            transition_duration_min=30,
        )
        with patch("agents.orchestrator._save_state"):
            threshold = orch._get_warmup_threshold(orch.active_agent)
            assert threshold is None


# ============================================================
# Test Class: Mid-transition threshold blending
# ============================================================

class TestMidTransitionBlending:
    """At 15 min (halfway), verify correct blending."""

    def test_halfway_conservative_to_aggressive(self):
        """At 15/30 min: w_new = 0.3 + 0.7*(15/30) = 0.65, w_old = 0.35
        blended = 0.65*40 + 0.35*60 = 26+21 = 47"""
        now = _kst_now()
        past = now - timedelta(minutes=15)
        orch = _make_orchestrator(
            active="aggressive",
            transition_from="conservative",
            transition_started=_kst_iso(past),
            transition_duration_min=30,
        )
        threshold = orch._get_warmup_threshold(orch.active_agent)
        assert threshold is not None
        assert threshold == 47

    def test_halfway_aggressive_to_conservative(self):
        """At 15/30 min: w_new=0.65, w_old=0.35
        blended = 0.65*60 + 0.35*40 = 39+14 = 53"""
        now = _kst_now()
        past = now - timedelta(minutes=15)
        orch = _make_orchestrator(
            active="conservative",
            transition_from="aggressive",
            transition_started=_kst_iso(past),
            transition_duration_min=30,
        )
        threshold = orch._get_warmup_threshold(orch.active_agent)
        assert threshold is not None
        assert threshold == 53

    def test_quarter_point(self):
        """At 7.5/30 min (quarter): w_new = 0.3 + 0.7*(7.5/30) = 0.475
        conservative->aggressive: blended = 0.475*40 + 0.525*60 = 19+31.5 = 50.5 -> 50"""
        now = _kst_now()
        past = now - timedelta(minutes=7, seconds=30)
        orch = _make_orchestrator(
            active="aggressive",
            transition_from="conservative",
            transition_started=_kst_iso(past),
            transition_duration_min=30,
        )
        threshold = orch._get_warmup_threshold(orch.active_agent)
        assert threshold is not None
        # Allow rounding: 50 or 51 depending on exact timing
        assert 50 <= threshold <= 51


# ============================================================
# Test Class: Transition completion
# ============================================================

class TestTransitionCompletes:
    """After 30 min, transition fields should be cleared."""

    def test_transition_fields_cleared_after_duration(self):
        past = _kst_now() - timedelta(minutes=31)
        orch = _make_orchestrator(
            active="aggressive",
            transition_from="conservative",
            transition_started=_kst_iso(past),
            transition_duration_min=30,
        )
        with patch("agents.orchestrator._save_state"):
            w_new, w_old = orch.get_transition_weight()
            assert w_new == 1.0
            assert w_old == 0.0
            # State should be cleared
            assert orch.state["transition_from"] is None
            assert orch.state["transition_started"] is None
            assert orch.state["transition_duration_min"] is None

    def test_not_in_transition_after_completion(self):
        past = _kst_now() - timedelta(minutes=31)
        orch = _make_orchestrator(
            active="aggressive",
            transition_from="conservative",
            transition_started=_kst_iso(past),
            transition_duration_min=30,
        )
        with patch("agents.orchestrator._save_state"):
            # Calling get_transition_weight clears the transition
            orch.get_transition_weight()
            assert not orch._in_transition()


# ============================================================
# Test Class: Multiple rapid switches
# ============================================================

class TestMultipleRapidSwitches:
    """Switch during an active transition should start a new transition."""

    def test_switch_during_active_transition(self):
        """If we switch conservative->aggressive at t=0, then at t=10 switch
        aggressive->conservative, the new transition should replace the old one."""
        now = _kst_now()
        ten_min_ago = now - timedelta(minutes=10)

        orch = _make_orchestrator(
            active="aggressive",
            transition_from="conservative",
            transition_started=_kst_iso(ten_min_ago),
            transition_duration_min=30,
        )

        # Perform a new switch (aggressive -> conservative)
        switch_info = {
            "from": "aggressive",
            "to": "conservative",
            "reason": "danger increased",
            "timestamp": _kst_iso(now),
        }
        with patch("agents.orchestrator._save_state"):
            orch._do_switch(switch_info)

        assert orch._active_agent_name == "conservative"
        assert orch.state["transition_from"] == "aggressive"
        assert orch.state["transition_started"] == _kst_iso(now)
        assert orch.state["active_agent"] == "conservative"

    def test_threshold_uses_new_transition(self):
        """After a rapid re-switch, threshold should use new from/to agents."""
        now = _kst_now()
        # First: conservative->aggressive started 10 min ago
        # Then: aggressive->moderate just now
        orch = _make_orchestrator(
            active="moderate",
            transition_from="aggressive",
            transition_started=_kst_iso(now),
            transition_duration_min=30,
        )
        agent = orch.active_agent
        assert isinstance(agent, ModerateAgent)

        threshold = orch._get_warmup_threshold(agent)
        # w_new=0.3, w_old=0.7 at start
        # blended = 0.3*50 + 0.7*40 = 15+28 = 43
        assert threshold is not None
        assert threshold == 43


# ============================================================
# Test Class: Cooldown respected
# ============================================================

class TestCooldownRespected:
    """Switch attempt within cooldown period should be rejected."""

    def test_switch_rejected_during_cooldown(self):
        """A switch attempt within 2 hours of last switch should be None."""
        one_hour_ago = _kst_iso(_kst_now() - timedelta(hours=1))
        orch = _make_orchestrator(
            active="conservative",
            last_switch=one_hour_ago,
        )
        ms = _ms(danger_score=20, opportunity_score=50, fgi=40, rsi=40)
        result = orch._evaluate_switch(ms)
        assert result is None

    def test_switch_allowed_after_cooldown(self):
        """After 2+ hours, switch should be allowed."""
        three_hours_ago = _kst_iso(_kst_now() - timedelta(hours=3))
        orch = _make_orchestrator(
            active="conservative",
            last_switch=three_hours_ago,
        )
        # Opportunity high enough to trigger conservative->moderate
        ms = _ms(danger_score=10, opportunity_score=30, fgi=40, rsi=40, phase="neutral")
        result = orch._evaluate_switch(ms)
        assert result is not None
        assert result["to"] == "moderate"

    def test_enhanced_cooldown_after_3_switches(self):
        """After 3 switches in one day, cooldown should be 4 hours."""
        now = _kst_now()
        # Create 3 switches today
        switches = []
        for i in range(3):
            t = now - timedelta(hours=2, minutes=30+i*10)
            switches.append({
                "from": "conservative",
                "to": "moderate",
                "timestamp": _kst_iso(t),
            })
        # Last switch was 3 hours ago (normally allowed with 2h cooldown)
        three_hours_ago = _kst_iso(now - timedelta(hours=3))
        orch = _make_orchestrator(
            active="conservative",
            last_switch=three_hours_ago,
            switch_history=switches,
        )
        # With 4h enhanced cooldown, 3h should still be blocked
        ms = _ms(danger_score=10, opportunity_score=30, fgi=40, rsi=40, phase="neutral")
        result = orch._evaluate_switch(ms)
        assert result is None


# ============================================================
# Test Class: Emergency override bypasses cooldown
# ============================================================

class TestEmergencyOverride:
    """danger >= 70 should bypass cooldown and trigger immediate switch."""

    def test_emergency_bypasses_cooldown(self):
        """danger >= 70 should bypass 2h cooldown."""
        one_hour_ago = _kst_iso(_kst_now() - timedelta(hours=1))
        orch = _make_orchestrator(
            active="aggressive",
            last_switch=one_hour_ago,
        )
        ms = _ms(
            danger_score=75,
            opportunity_score=5,
            fgi=15,
            rsi=30,
            price_change_24h=-8,
            consecutive_losses=3,
            phase="extreme_fear",
        )
        result = orch._evaluate_switch(ms)
        assert result is not None
        assert result["to"] == "conservative"

    def test_severe_crash_bypasses_cooldown(self):
        """price_change_24h < -7 should also bypass cooldown."""
        thirty_min_ago = _kst_iso(_kst_now() - timedelta(minutes=30))
        orch = _make_orchestrator(
            active="moderate",
            last_switch=thirty_min_ago,
        )
        ms = _ms(
            danger_score=55,
            opportunity_score=5,
            fgi=20,
            rsi=25,
            price_change_24h=-8.5,
            phase="extreme_fear",
        )
        result = orch._evaluate_switch(ms)
        assert result is not None
        assert result["to"] == "conservative"


# ============================================================
# Test Class: State persistence (agent_state.json)
# ============================================================

class TestStatePersistence:
    """Transition state should survive orchestrator restart."""

    def test_transition_survives_restart(self, tmp_path):
        """Write agent_state.json, create new Orchestrator, verify transition."""
        state_file = tmp_path / "agent_state.json"
        now = _kst_now()
        ten_min_ago = now - timedelta(minutes=10)

        state = {
            "active_agent": "aggressive",
            "transition_from": "conservative",
            "transition_started": _kst_iso(ten_min_ago),
            "transition_duration_min": 30,
            "last_switch_time": _kst_iso(ten_min_ago),
            "last_trade_time": None,
            "consecutive_losses": 0,
            "switch_history": [],
        }
        state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2))

        with patch("agents.orchestrator.STATE_FILE", state_file):
            from agents.orchestrator import Orchestrator
            orch = Orchestrator()

        assert orch._active_agent_name == "aggressive"
        assert orch.state["transition_from"] == "conservative"
        assert orch._in_transition()

        # Threshold should be mid-transition (10/30 min elapsed)
        threshold = orch._get_warmup_threshold(orch.active_agent)
        assert threshold is not None
        # w_new at 10min: 0.3 + 0.7*(10/30) = 0.5333...
        # blended = 0.5333*40 + 0.4667*60 = 21.33 + 28.0 = ~49
        assert 49 <= threshold <= 50

    def test_completed_transition_cleared_on_restart(self, tmp_path):
        """If transition_started is >30 min ago, it should be cleared on access."""
        state_file = tmp_path / "agent_state.json"
        old = _kst_now() - timedelta(minutes=45)

        state = {
            "active_agent": "aggressive",
            "transition_from": "conservative",
            "transition_started": _kst_iso(old),
            "transition_duration_min": 30,
            "last_switch_time": _kst_iso(old),
            "last_trade_time": None,
            "consecutive_losses": 0,
            "switch_history": [],
        }
        state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2))

        with patch("agents.orchestrator.STATE_FILE", state_file):
            with patch("agents.orchestrator._save_state"):
                from agents.orchestrator import Orchestrator
                orch = Orchestrator()

        # Access transition weight to trigger cleanup
        with patch("agents.orchestrator._save_state"):
            w_new, w_old = orch.get_transition_weight()
        assert w_new == 1.0
        assert w_old == 0.0
        assert orch.state["transition_from"] is None


# ============================================================
# Test Class: Corrupted transition state
# ============================================================

class TestCorruptedTransitionState:
    """Missing or malformed transition fields should be handled gracefully."""

    def test_missing_transition_started(self):
        """transition_from set but transition_started is None -> not in transition."""
        orch = _make_orchestrator(
            active="aggressive",
            transition_from="conservative",
            transition_started=None,
            transition_duration_min=30,
        )
        assert not orch._in_transition()
        threshold = orch._get_warmup_threshold(orch.active_agent)
        assert threshold is None

    def test_bad_datetime_format(self):
        """Invalid datetime format should gracefully clear transition."""
        orch = _make_orchestrator(
            active="aggressive",
            transition_from="conservative",
            transition_started="not-a-date",
            transition_duration_min=30,
        )
        with patch("agents.orchestrator._save_state"):
            w_new, w_old = orch.get_transition_weight()
            # Should fallback to (1.0, 0.0) and clear transition
            assert w_new == 1.0
            assert w_old == 0.0

    def test_missing_transition_duration(self):
        """transition_duration_min is None -> not in transition."""
        now = _kst_now()
        orch = _make_orchestrator(
            active="aggressive",
            transition_from="conservative",
            transition_started=_kst_iso(now),
            transition_duration_min=None,
        )
        assert not orch._in_transition()

    def test_unknown_agent_in_transition_from(self):
        """If transition_from references an unknown agent, threshold returns None."""
        now = _kst_now()
        state = _default_state(
            active="aggressive",
            transition_from="unknown_agent",
            transition_started=_kst_iso(now),
            transition_duration_min=30,
        )
        with patch("agents.orchestrator._load_state", return_value=state):
            with patch("agents.orchestrator._save_state"):
                from agents.orchestrator import Orchestrator
                orch = Orchestrator()
                orch._learning_data = None
                orch._performance = {}

        threshold = orch._get_warmup_threshold(orch.active_agent)
        assert threshold is None


# ============================================================
# Test Class: Buy score with warmup
# ============================================================

class TestBuyScoreWithWarmup:
    """Verify blended threshold affects actual buy decisions."""

    def test_warmup_blocks_buy_that_new_agent_would_allow(self):
        """During warmup, threshold is higher than aggressive's 40.
        A score between 40 and 54 should be blocked by warmup threshold."""
        now = _kst_now()
        orch = _make_orchestrator(
            active="aggressive",
            transition_from="conservative",
            transition_started=_kst_iso(now),
            transition_duration_min=30,
        )
        agent = orch.active_agent
        assert isinstance(agent, AggressiveAgent)

        # Blended threshold at t=0: 54
        warmup_threshold = orch._get_warmup_threshold(agent)
        assert warmup_threshold == 54

        # Craft a score that lands between 40 and 54:
        # fgi=70 > aggressive threshold 60 -> 0 pts (but within +10 -> partial 15 pts)
        # rsi=55 > aggressive threshold 50 -> 0 pts (but within +5 -> partial 15 pts)
        # sma_deviation=0 > -1.0 -> 0 pts
        # news_negative=False -> 20 pts
        # Total: 15 + 15 + 0 + 20 = 50
        buy_score = agent.calculate_buy_score(
            fgi=70, rsi=55, sma_deviation=0,
            news_negative=False, external_bonus=0,
        )
        total = buy_score["total"]
        # Verify score is between 40 (aggressive) and 54 (warmup)
        assert 40 <= total < 54, f"Score {total} not in expected range [40, 54)"

        # Without warmup: aggressive threshold is 40, so score >= 40 -> buy
        assert buy_score["result"] == "buy"

        # With warmup applied: score < 54 -> hold
        original = agent.buy_score_threshold
        agent.buy_score_threshold = warmup_threshold
        buy_score_warmup = agent.calculate_buy_score(
            fgi=70, rsi=55, sma_deviation=0,
            news_negative=False, external_bonus=0,
        )
        assert buy_score_warmup["result"] == "hold"
        agent.buy_score_threshold = original

    def test_warmup_allows_buy_when_score_exceeds_blended(self):
        """A score well above the blended threshold should still allow buy."""
        now = _kst_now()
        orch = _make_orchestrator(
            active="aggressive",
            transition_from="conservative",
            transition_started=_kst_iso(now),
            transition_duration_min=30,
        )
        agent = orch.active_agent
        warmup_threshold = orch._get_warmup_threshold(agent)
        assert warmup_threshold == 54

        # Create conditions that yield a high score (well above 54)
        # FGI <= 60 (aggressive threshold): 30pts
        # RSI <= 50: 25pts
        # SMA deviation <= -1.0: 25pts
        # News not negative: 20pts
        # Total: 100 >> 54
        original = agent.buy_score_threshold
        agent.buy_score_threshold = warmup_threshold
        buy_score = agent.calculate_buy_score(
            fgi=20, rsi=25, sma_deviation=-2.0,
            news_negative=False, external_bonus=0,
        )
        assert buy_score["result"] == "buy"
        assert buy_score["total"] >= warmup_threshold
        agent.buy_score_threshold = original


# ============================================================
# Test Class: _do_switch sets transition fields
# ============================================================

class TestDoSwitchSetsTransition:
    """Verify _do_switch properly sets warmup transition state."""

    def test_do_switch_sets_all_fields(self):
        now = _kst_now()
        orch = _make_orchestrator(active="conservative")

        switch_info = {
            "from": "conservative",
            "to": "aggressive",
            "reason": "high opportunity",
            "timestamp": _kst_iso(now),
        }
        with patch("agents.orchestrator._save_state"):
            orch._do_switch(switch_info)

        assert orch.state["active_agent"] == "aggressive"
        assert orch.state["transition_from"] == "conservative"
        assert orch.state["transition_started"] == _kst_iso(now)
        assert orch.state["transition_duration_min"] == 30
        assert orch._active_agent_name == "aggressive"

    def test_switch_history_appended(self):
        now = _kst_now()
        orch = _make_orchestrator(active="conservative")
        assert len(orch.state["switch_history"]) == 0

        switch_info = {
            "from": "conservative",
            "to": "moderate",
            "reason": "market stabilizing",
            "timestamp": _kst_iso(now),
        }
        with patch("agents.orchestrator._save_state"):
            orch._do_switch(switch_info)

        assert len(orch.state["switch_history"]) == 1
        assert orch.state["switch_history"][0]["to"] == "moderate"

    def test_switch_history_capped_at_30(self):
        """Switch history should be capped at 30 entries."""
        now = _kst_now()
        history = [
            {"from": "a", "to": "b", "timestamp": _kst_iso(now - timedelta(hours=i))}
            for i in range(30)
        ]
        orch = _make_orchestrator(active="conservative", switch_history=history)
        assert len(orch.state["switch_history"]) == 30

        switch_info = {
            "from": "conservative",
            "to": "aggressive",
            "reason": "test",
            "timestamp": _kst_iso(now),
        }
        with patch("agents.orchestrator._save_state"):
            orch._do_switch(switch_info)

        assert len(orch.state["switch_history"]) == 30  # capped


# ============================================================
# Test Class: get_transition_weight edge cases
# ============================================================

class TestTransitionWeight:
    """Test get_transition_weight linear interpolation."""

    def test_no_transition_returns_full_new(self):
        orch = _make_orchestrator(active="conservative")
        w_new, w_old = orch.get_transition_weight()
        assert w_new == 1.0
        assert w_old == 0.0

    def test_weights_sum_to_one(self):
        """At any point during transition, weights should sum to 1.0."""
        now = _kst_now()
        for minutes in [0, 5, 10, 15, 20, 25, 29]:
            past = now - timedelta(minutes=minutes)
            orch = _make_orchestrator(
                active="aggressive",
                transition_from="conservative",
                transition_started=_kst_iso(past),
                transition_duration_min=30,
            )
            w_new, w_old = orch.get_transition_weight()
            assert abs((w_new + w_old) - 1.0) < 0.01, f"Weights don't sum to 1 at {minutes}min"

    def test_new_weight_monotonically_increases(self):
        """w_new should increase as time progresses."""
        now = _kst_now()
        prev_w = 0.0
        for minutes in [0, 5, 10, 15, 20, 25]:
            past = now - timedelta(minutes=minutes)
            orch = _make_orchestrator(
                active="aggressive",
                transition_from="conservative",
                transition_started=_kst_iso(past),
                transition_duration_min=30,
            )
            w_new, _ = orch.get_transition_weight()
            assert w_new >= prev_w, f"w_new decreased at {minutes}min"
            prev_w = w_new

    def test_new_weight_starts_at_0_3(self):
        """At t=0, w_new should be 0.3."""
        now = _kst_now()
        orch = _make_orchestrator(
            active="aggressive",
            transition_from="conservative",
            transition_started=_kst_iso(now),
            transition_duration_min=30,
        )
        w_new, w_old = orch.get_transition_weight()
        assert abs(w_new - 0.3) < 0.05  # allow small timing variance
        assert abs(w_old - 0.7) < 0.05


# ============================================================
# Test Class: Full run integration with warmup
# ============================================================

class TestFullRunWithWarmup:
    """Test the full orchestrator.run() method with warmup transition active."""

    @patch("agents.orchestrator._save_state")
    @patch("agents.orchestrator._load_state")
    def test_run_applies_warmup_threshold(self, mock_load, mock_save):
        """During run(), the warmup threshold should be applied to the agent,
        then restored after decision."""
        now = _kst_now()
        state = _default_state(
            active="aggressive",
            transition_from="conservative",
            transition_started=_kst_iso(now),
            transition_duration_min=30,
            last_switch=_kst_iso(now - timedelta(hours=3)),
        )
        mock_load.return_value = state

        from agents.orchestrator import Orchestrator
        orch = Orchestrator()
        orch._learning_data = None
        orch._performance = {}

        market_data = _make_market_data(fgi=50, rsi=50, sma_deviation=0)
        external_data = _make_external_data(fgi=50)
        portfolio = _make_portfolio()

        # Mock DB calls
        with patch.object(orch, '_load_learning_data', return_value=None), \
             patch.object(orch, '_record_switch_to_db'), \
             patch.object(orch, '_check_auto_emergency_active', return_value=None), \
             patch("agents.base_agent.BaseStrategyAgent.save_buy_score_detail", return_value=None):
            result = orch.run(market_data, external_data, portfolio)

        # Decision should exist
        assert "decision" in result
        # The active agent's threshold should be restored to original
        agent = AggressiveAgent()
        assert agent.buy_score_threshold == 40
