"""Unit tests for rl_hybrid/rl/reward.py — RewardCalculator v8"""

import math
import numpy as np
import pytest

from rl_hybrid.rl.reward import (
    RewardCalculator,
    TRANSACTION_COST,
    UPBIT_FEE_RATE,
    SLIPPAGE_RATE,
)


# ── Constants ────────────────────────────────────────────────────────────

class TestConstants:
    def test_upbit_fee_rate(self):
        assert UPBIT_FEE_RATE == 0.0005

    def test_slippage_rate(self):
        assert SLIPPAGE_RATE == 0.0003

    def test_transaction_cost_is_sum(self):
        assert TRANSACTION_COST == UPBIT_FEE_RATE + SLIPPAGE_RATE
        assert math.isclose(TRANSACTION_COST, 0.0008)


# ── Initialization & Reset ───────────────────────────────────────────────

class TestInitAndReset:
    def test_default_init(self):
        rc = RewardCalculator()
        assert rc.window_size == 20
        assert rc.max_drawdown_penalty == 3.0
        assert rc.pnl_scale == 100.0
        assert rc.total_trades == 0
        assert rc.steps_since_last_trade == 0
        assert len(rc.returns_history) == 0

    def test_custom_init(self):
        rc = RewardCalculator(
            window_size=10,
            risk_free_rate=0.0,
            max_drawdown_penalty=5.0,
            pnl_scale=50.0,
        )
        assert rc.window_size == 10
        assert rc.risk_free_rate == 0.0
        assert rc.max_drawdown_penalty == 5.0
        assert rc.pnl_scale == 50.0

    def test_reset_clears_state(self):
        rc = RewardCalculator()
        # Accumulate some state
        rc.returns_history.append(0.01)
        rc.total_trades = 5
        rc.steps_since_last_trade = 10
        rc.peak_value = 200_000

        rc.reset(initial_value=100_000)

        assert len(rc.returns_history) == 0
        assert rc.peak_value == 100_000
        assert rc.total_trades == 0
        assert rc.steps_since_last_trade == 0

    def test_returns_history_maxlen(self):
        rc = RewardCalculator(window_size=5)
        for i in range(10):
            rc.returns_history.append(float(i))
        assert len(rc.returns_history) == 5
        assert list(rc.returns_history) == [5.0, 6.0, 7.0, 8.0, 9.0]


# ── Positive / Negative Returns ──────────────────────────────────────────

class TestReturnSign:
    @pytest.fixture
    def calc(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        return rc

    def test_positive_return_gives_positive_reward(self, calc):
        result = calc.calculate(100_000, 101_000, action=0.5, prev_action=0.5, step=0)
        assert result["components"]["raw_return"] > 0
        assert result["reward"] > 0

    def test_negative_return_gives_negative_reward(self, calc):
        result = calc.calculate(100_000, 99_000, action=0.5, prev_action=0.5, step=0)
        assert result["components"]["raw_return"] < 0
        assert result["reward"] < 0

    def test_raw_return_value(self, calc):
        result = calc.calculate(100_000, 105_000, action=0.5, prev_action=0.5, step=0)
        assert math.isclose(result["components"]["raw_return"], 0.05)


# ── PnL Reward ──────────────────────────────────────────────────────────

class TestPnlReward:
    def test_pnl_scales_with_return(self):
        rc = RewardCalculator(risk_free_rate=0.0, pnl_scale=100.0)
        rc.reset(100_000)
        result = rc.calculate(100_000, 101_000, action=0.5, prev_action=0.5, step=0)
        # 1% return * 100 = 1.0, clipped to [-1.5, 1.5]
        assert result["components"]["pnl_reward"] == pytest.approx(1.0)

    def test_pnl_clipped_upper(self):
        rc = RewardCalculator(risk_free_rate=0.0, pnl_scale=100.0)
        rc.reset(100_000)
        # 5% return * 100 = 5.0, clipped to 1.5
        result = rc.calculate(100_000, 105_000, action=0.5, prev_action=0.5, step=0)
        assert result["components"]["pnl_reward"] == 1.5

    def test_pnl_clipped_lower(self):
        rc = RewardCalculator(risk_free_rate=0.0, pnl_scale=100.0)
        rc.reset(100_000)
        result = rc.calculate(100_000, 95_000, action=0.5, prev_action=0.5, step=0)
        assert result["components"]["pnl_reward"] == -1.5


# ── Direction Reward ────────────────────────────────────────────────────

class TestDirectionReward:
    def test_correct_direction_positive(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        # btc_ratio=0.8 (BTC heavy) + price_change=0.01 (up) → alignment positive
        result = rc.calculate(100_000, 101_000, action=0.5, prev_action=0.5, step=0,
                              btc_ratio=0.8, price_change=0.01)
        assert result["components"]["direction_reward"] > 0

    def test_wrong_direction_negative(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        # btc_ratio=0.8 (BTC heavy) + price_change=-0.01 (down) → alignment negative
        result = rc.calculate(100_000, 99_000, action=0.5, prev_action=0.5, step=0,
                              btc_ratio=0.8, price_change=-0.01)
        assert result["components"]["direction_reward"] < 0

    def test_no_direction_when_small_change(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        # price_change < 0.001 → no direction reward
        result = rc.calculate(100_000, 100_050, action=0.5, prev_action=0.5, step=0,
                              btc_ratio=0.8, price_change=0.0005)
        assert result["components"]["direction_reward"] == 0.0

    def test_direction_clipped(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        result = rc.calculate(100_000, 110_000, action=0.5, prev_action=0.5, step=0,
                              btc_ratio=1.0, price_change=0.10)
        assert result["components"]["direction_reward"] <= 0.5
        assert result["components"]["direction_reward"] >= -0.5


# ── MDD Penalty ──────────────────────────────────────────────────────────

class TestMDDPenalty:
    @pytest.fixture
    def calc(self):
        rc = RewardCalculator(max_drawdown_penalty=2.0, risk_free_rate=0.0)
        rc.reset(100_000)
        return rc

    def test_no_penalty_below_3pct_drawdown(self, calc):
        calc.peak_value = 100_000
        # 2% drawdown → below 3% threshold
        result = calc.calculate(100_000, 98_000, action=0.5, prev_action=0.5, step=0)
        assert result["components"]["mdd_penalty"] == 0
        assert result["components"]["drawdown"] == pytest.approx(0.02)

    def test_penalty_above_3pct_drawdown(self, calc):
        calc.peak_value = 100_000
        # 10% drawdown
        result = calc.calculate(100_000, 90_000, action=0.5, prev_action=0.5, step=0)
        dd = 0.10
        expected_penalty = -dd * 2.0
        assert result["components"]["mdd_penalty"] == pytest.approx(expected_penalty)

    def test_exact_3pct_boundary_no_penalty(self, calc):
        calc.peak_value = 100_000
        result = calc.calculate(100_000, 97_000, action=0.5, prev_action=0.5, step=0)
        # drawdown == 0.03 exactly → condition is > 0.03, so no penalty
        assert result["components"]["mdd_penalty"] == 0

    def test_peak_updates_upward(self, calc):
        calc.calculate(100_000, 110_000, action=0.5, prev_action=0.5, step=0)
        assert calc.peak_value == 110_000
        calc.calculate(110_000, 105_000, action=0.5, prev_action=0.5, step=1)
        assert calc.peak_value == 110_000


# ── Trade PnL Bonus ─────────────────────────────────────────────────────

class TestTradePnlBonus:
    @pytest.fixture
    def calc(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        return rc

    def test_profit_trade_bonus(self, calc):
        # prev_trade_value=100_000, curr=100_300 → 0.3% > 0.2% → bonus +0.5
        result = calc.calculate(100_000, 100_300, action=0.8, prev_action=0.0, step=0)
        assert result["components"]["trade_pnl_bonus"] == 0.5

    def test_loss_trade_penalty(self, calc):
        # curr < prev_trade_value by >0.2% → penalty -0.2
        result = calc.calculate(100_000, 99_700, action=0.8, prev_action=0.0, step=0)
        assert result["components"]["trade_pnl_bonus"] == -0.2

    def test_small_trade_no_bonus(self, calc):
        # Within ±0.2% → no bonus/penalty
        result = calc.calculate(100_000, 100_100, action=0.8, prev_action=0.0, step=0)
        assert result["components"]["trade_pnl_bonus"] == 0.0

    def test_no_bonus_when_no_trade(self, calc):
        # action_change <= 0.05
        result = calc.calculate(100_000, 100_300, action=0.5, prev_action=0.5, step=0)
        assert result["components"]["trade_pnl_bonus"] == 0.0

    def test_trade_increments_total_trades(self, calc):
        assert calc.total_trades == 0
        calc.calculate(100_000, 100_100, action=0.8, prev_action=0.0, step=0)
        assert calc.total_trades == 1
        calc.calculate(100_100, 100_200, action=0.0, prev_action=0.8, step=1)
        assert calc.total_trades == 2

    def test_no_trade_does_not_increment(self, calc):
        calc.calculate(100_000, 101_000, action=0.5, prev_action=0.5, step=0)
        assert calc.total_trades == 0

    def test_steps_since_last_trade_resets_on_trade(self, calc):
        calc.steps_since_last_trade = 10
        calc.calculate(100_000, 100_100, action=0.8, prev_action=0.0, step=0)
        assert calc.steps_since_last_trade == 0

    def test_steps_since_last_trade_increments_without_trade(self, calc):
        calc.steps_since_last_trade = 5
        calc.calculate(100_000, 100_100, action=0.5, prev_action=0.5, step=0)
        assert calc.steps_since_last_trade == 6


# ── Differential Sharpe Ratio ────────────────────────────────────────────

class TestDifferentialSharpe:
    def test_early_steps_use_simple_scaling(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        # len(returns_history) < 3 → raw * 15
        r1 = rc.calculate(100_000, 101_000, action=0.5, prev_action=0.5, step=0)
        raw = 0.01
        assert r1["components"]["sharpe_reward"] == pytest.approx(raw * 15)

    def test_sharpe_with_enough_history(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        rc.returns_history.append(0.01)
        rc.returns_history.append(0.02)
        result = rc.calculate(100_000, 101_500, action=0.5, prev_action=0.5, step=2)
        sharpe_rw = result["components"]["sharpe_reward"]
        assert sharpe_rw > 0

    def test_sharpe_clipped_upper(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        rc.returns_history.extend([0.4, 0.5, 0.6, 0.45, 0.55])
        result = rc._compute_sharpe_reward(0.5)
        assert result <= 1.5

    def test_sharpe_clipped_lower(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        rc.returns_history.extend([-0.4, -0.5, -0.6, -0.45, -0.55])
        result = rc._compute_sharpe_reward(-0.5)
        assert result >= -1.5

    def test_zero_std_returns_scaled_mean(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        for _ in range(5):
            rc.returns_history.append(0.01)
        result = rc._compute_sharpe_reward(0.01)
        # std < 1e-8 branch: mean_return * 15
        assert result == pytest.approx(0.01 * 15)


# ── Episode Stats ────────────────────────────────────────────────────────

class TestEpisodeStats:
    def test_basic_stats(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        rc.returns_history.extend([0.01, 0.02, -0.005, 0.015])
        rc.total_trades = 3
        rc.peak_value = 105_000

        stats = rc.get_episode_stats(final_value=103_000, initial_value=100_000)

        assert stats["total_return_pct"] == pytest.approx(3.0)
        assert stats["total_trades"] == 3
        assert stats["avg_return"] == pytest.approx(np.mean([0.01, 0.02, -0.005, 0.015]))
        assert stats["std_return"] == pytest.approx(np.std([0.01, 0.02, -0.005, 0.015]))
        assert stats["max_drawdown"] == pytest.approx((105_000 - 103_000) / 105_000)

    def test_stats_keys(self):
        rc = RewardCalculator()
        rc.reset(100_000)
        stats = rc.get_episode_stats(100_000, 100_000)
        expected_keys = {
            "total_return_pct",
            "total_trades",
            "avg_return",
            "std_return",
            "max_drawdown",
            "sharpe_ratio",
        }
        assert set(stats.keys()) == expected_keys

    def test_stats_empty_history(self):
        rc = RewardCalculator()
        rc.reset(100_000)
        stats = rc.get_episode_stats(100_000, 100_000)
        assert stats["total_return_pct"] == 0.0
        assert stats["avg_return"] == 0.0
        assert stats["std_return"] == 0
        assert stats["sharpe_ratio"] == 0

    def test_stats_single_return(self):
        rc = RewardCalculator()
        rc.reset(100_000)
        rc.returns_history.append(0.05)
        stats = rc.get_episode_stats(105_000, 100_000)
        assert stats["total_return_pct"] == pytest.approx(5.0)
        assert stats["std_return"] == 0
        assert stats["sharpe_ratio"] == 0

    def test_sharpe_ratio_in_stats(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        rc.returns_history.extend([0.01, 0.02, 0.03])
        stats = rc.get_episode_stats(106_000, 100_000)
        returns = np.array([0.01, 0.02, 0.03])
        expected_sharpe = returns.mean() / returns.std()
        assert stats["sharpe_ratio"] == pytest.approx(expected_sharpe)


# ── Calculate Return Structure ───────────────────────────────────────────

class TestCalculateReturnStructure:
    def test_return_dict_keys(self):
        rc = RewardCalculator()
        rc.reset(100_000)
        result = rc.calculate(100_000, 100_100, action=0.5, prev_action=0.5, step=0)
        assert "reward" in result
        assert "components" in result
        expected_comp_keys = {
            "raw_return",
            "pnl_reward",
            "direction_reward",
            "sharpe_reward",
            "mdd_penalty",
            "trade_pnl_bonus",
            "drawdown",
            "total_trades",
        }
        assert set(result["components"].keys()) == expected_comp_keys

    def test_reward_is_sum_of_components(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        result = rc.calculate(100_000, 90_000, action=0.8, prev_action=0.0, step=0)
        c = result["components"]
        expected = c["pnl_reward"] + c["direction_reward"] + c["sharpe_reward"] + c["mdd_penalty"] + c["trade_pnl_bonus"]
        assert result["reward"] == pytest.approx(expected)


# ── Edge Cases ───────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_zero_return(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        result = rc.calculate(100_000, 100_000, action=0.5, prev_action=0.5, step=0)
        assert result["components"]["raw_return"] == 0.0
        assert result["components"]["sharpe_reward"] == 0.0
        assert result["components"]["drawdown"] == 0.0

    def test_identical_portfolio_values_sequence(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        for i in range(10):
            result = rc.calculate(100_000, 100_000, action=0.5, prev_action=0.5, step=i)
        assert result["components"]["raw_return"] == 0.0
        assert result["reward"] == 0.0
        assert result["components"]["drawdown"] == 0.0

    def test_very_large_drawdown(self):
        rc = RewardCalculator(max_drawdown_penalty=2.0, risk_free_rate=0.0)
        rc.reset(1_000_000)
        rc.peak_value = 1_000_000
        # 90% drawdown
        result = rc.calculate(1_000_000, 100_000, action=0.5, prev_action=0.5, step=0)
        assert result["components"]["drawdown"] == pytest.approx(0.9)
        assert result["components"]["mdd_penalty"] == pytest.approx(-0.9 * 2.0)

    def test_very_small_return(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        result = rc.calculate(100_000, 100_001, action=0.5, prev_action=0.5, step=0)
        assert result["components"]["raw_return"] == pytest.approx(1e-5)

    def test_action_change_boundary_below_005(self):
        """action_change < 0.05 → NOT a trade"""
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        result = rc.calculate(100_000, 100_200, action=0.54, prev_action=0.5, step=0)
        assert rc.total_trades == 0
        assert result["components"]["trade_pnl_bonus"] == 0.0

    def test_action_change_just_above_005(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        result = rc.calculate(100_000, 100_200, action=0.5501, prev_action=0.5, step=0)
        assert rc.total_trades == 1

    def test_large_positive_return_no_overflow(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        result = rc.calculate(100_000, 200_000, action=0.5, prev_action=0.5, step=0)
        assert result["components"]["raw_return"] == pytest.approx(1.0)
        assert np.isfinite(result["reward"])

    def test_multiple_trades_accumulate(self):
        rc = RewardCalculator(risk_free_rate=0.0)
        rc.reset(100_000)
        for i in range(5):
            action = 0.8 if i % 2 == 0 else 0.0
            prev_action = 0.0 if i % 2 == 0 else 0.8
            rc.calculate(100_000, 100_100, action=action, prev_action=prev_action, step=i)
        assert rc.total_trades == 5

    def test_all_components_are_float(self):
        rc = RewardCalculator()
        rc.reset(100_000)
        result = rc.calculate(100_000, 101_000, action=0.8, prev_action=0.0, step=0)
        assert isinstance(result["reward"], float)
        for key, val in result["components"].items():
            if key != "total_trades":
                assert isinstance(val, float), f"{key} should be float"
            else:
                assert isinstance(val, int)
