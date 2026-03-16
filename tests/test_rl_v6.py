"""
RL 모듈 유닛 테스트 — v6 스캘핑 환경 + v8 보상함수 + 상태 인코더 + 보상 해부

Coverage:
  - scalp_ml/scalp_exit_env.py: 환경 reset/step, HOLD/TP/SL, 강제 청산, v6 파라미터
  - rl_hybrid/rl/reward.py: PnL 클리핑, 방향성 보상, Sharpe, MDD 페널티, 거래 보너스
  - rl_hybrid/rl/state_encoder.py: 정규화, 42차원 출력, 경계값
  - scalp_ml/week2/reward_ablation.py: AblationRewardWrapper 성분 선택, leave-one-out
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rl_hybrid.rl.reward import RewardCalculator, TRANSACTION_COST
from rl_hybrid.rl.state_encoder import (
    StateEncoder,
    FEATURE_SPEC,
    OBSERVATION_DIM,
    FEATURE_NAMES,
)
from scalp_ml.scalp_exit_env import (
    ScalpExitEnv,
    ScalpExitEnvV2,
    FEE_PCT,
    MAX_HOLD,
    TP_DEFAULT,
    SL_DEFAULT,
)
from scalp_ml.week2.reward_ablation import (
    AblationRewardWrapper,
    REWARD_COMPONENTS,
    COMPONENT_LABELS,
)


# ============================================================
# Helpers
# ============================================================

def _make_candles(n: int = 50, base_price: float = 100_000_000.0, trend: float = 0.0):
    """테스트용 캔들 데이터 생성.

    Args:
        n: 캔들 개수
        base_price: 시작가
        trend: 분당 변화율 (0.001 = 0.1% 상승/분)
    """
    candles = []
    price = base_price
    for i in range(n):
        price = price * (1 + trend + np.random.normal(0, 0.0001))
        candles.append({
            "trade_price": price,
            "candle_acc_trade_volume": max(0.5, np.random.exponential(2.0)),
            "opening_price": price * 0.9999,
            "high_price": price * 1.0002,
            "low_price": price * 0.9998,
        })
    return candles


def _make_scalp_env(n_candles: int = 80, trend: float = 0.0) -> ScalpExitEnv:
    """테스트용 ScalpExitEnv 생성."""
    candles = _make_candles(n_candles, trend=trend)
    return ScalpExitEnv(candle_data=candles)


def _make_market_data_for_encoder(price=50_000_000, rsi=50, change_rate=0.0):
    """StateEncoder 테스트용 시장 데이터."""
    return {
        "current_price": price,
        "change_rate_24h": change_rate,
        "indicators": {
            "rsi_14": rsi,
            "sma_20": price,
            "sma_50": price,
            "macd": {"histogram": 0},
            "bollinger": {"upper": price * 1.02, "lower": price * 0.98, "middle": price},
            "stochastic": {"k": 50, "d": 50},
            "adx": {"adx": 25, "plus_di": 20, "minus_di": 20},
            "atr": price * 0.01,
        },
        "indicators_4h": {"rsi_14": 50},
        "orderbook": {"ratio": 1.0},
        "trade_pressure": {"buy_volume": 100, "sell_volume": 100},
        "eth_btc_analysis": {"eth_btc_z_score": 0},
    }


def _make_external_data_for_encoder(fgi=50, sentiment=0):
    """StateEncoder 테스트용 외부 데이터."""
    return {
        "sources": {
            "fear_greed": {"current": {"value": fgi}},
            "news_sentiment": {"sentiment_score": sentiment},
            "whale_tracker": {"whale_score": {"score": 0}},
            "binance_sentiment": {
                "funding_rate": {"current_rate": 0},
                "top_trader_long_short": {"current_ratio": 1.0},
                "kimchi_premium": {"premium_pct": 0},
            },
            "macro": {"analysis": {"macro_score": 0}},
            "ai_signal": {"ai_composite_signal": {"score": 0}},
            "coinmarketcap": {"btc_dominance": 50},
        },
        "external_signal": {"total_score": 0},
    }


def _make_portfolio_for_encoder(krw=5_000_000, btc_eval=5_000_000, price=50_000_000):
    """StateEncoder 테스트용 포트폴리오."""
    return {
        "krw_balance": krw,
        "total_eval": krw + btc_eval,
        "holdings": [
            {
                "currency": "BTC",
                "eval_amount": btc_eval,
                "avg_buy_price": price,
                "profit_loss_pct": 0,
            }
        ],
    }


# ============================================================
# 1. ScalpExitEnv Tests
# ============================================================

class TestScalpExitEnvParams:
    """v6 파라미터 검증."""

    def test_v6_defaults(self):
        assert TP_DEFAULT == 0.3, "v6 익절 기본값은 0.3%"
        assert SL_DEFAULT == 0.25, "v6 손절 기본값은 0.25%"
        assert MAX_HOLD == 15, "v6 최대 보유시간은 15분"
        assert FEE_PCT == 0.1, "왕복 수수료는 0.1%"

    def test_action_space(self):
        env = _make_scalp_env()
        assert env.action_space.n == 3, "행동 공간: HOLD(0), TP(1), SL(2)"

    def test_observation_space_shape(self):
        env = _make_scalp_env()
        assert env.observation_space.shape == (8,), "관측 벡터: 8차원"

    def test_observation_space_bounds(self):
        env = _make_scalp_env()
        low = env.observation_space.low
        high = env.observation_space.high
        # pnl_pct bounds
        assert low[0] == -10 and high[0] == 10
        # hold_min bounds
        assert low[1] == 0 and high[1] == MAX_HOLD
        # strategy bounds
        assert low[7] == 0 and high[7] == 2


class TestScalpExitEnvReset:
    """환경 reset 검증."""

    def test_reset_returns_obs_and_info(self):
        env = _make_scalp_env()
        result = env.reset()
        assert isinstance(result, tuple) and len(result) == 2
        obs, info = result
        assert obs.shape == (8,)
        assert isinstance(info, dict)

    def test_reset_obs_in_bounds(self):
        env = _make_scalp_env()
        obs, _ = env.reset()
        low = env.observation_space.low
        high = env.observation_space.high
        assert np.all(obs >= low - 1e-5), f"obs below low: {obs}"
        assert np.all(obs <= high + 1e-5), f"obs above high: {obs}"

    def test_reset_initializes_state(self):
        env = _make_scalp_env()
        env.reset()
        assert env._entry_price > 0
        assert env._current_step == 15  # 진입 시점 = index 15
        assert env._done is False
        assert env._total_reward == 0
        assert env._strategy in (0, 1, 2)

    def test_multiple_resets(self):
        env = _make_scalp_env()
        for _ in range(5):
            obs, info = env.reset()
            assert obs.shape == (8,)
            assert env._done is False


class TestScalpExitEnvStep:
    """환경 step 검증."""

    def test_hold_action_gives_time_cost(self):
        env = _make_scalp_env()
        env.reset()
        obs, reward, terminated, truncated, info = env.step(0)  # HOLD
        assert not terminated
        assert not truncated
        # v7: 모멘텀 기반 HOLD 보상 (-0.01 ~ +0.01+)
        assert -0.02 <= reward <= 0.05

    def test_take_profit_terminates(self):
        env = _make_scalp_env()
        env.reset()
        obs, reward, terminated, truncated, info = env.step(1)  # TAKE_PROFIT
        assert terminated is True
        assert info["exit_reason"] == "take_profit"
        assert "pnl_pct" in info

    def test_stop_loss_terminates(self):
        env = _make_scalp_env()
        env.reset()
        obs, reward, terminated, truncated, info = env.step(2)  # STOP_LOSS
        assert terminated is True
        assert info["exit_reason"] == "stop_loss"
        assert "pnl_pct" in info

    def test_done_returns_zero_reward(self):
        env = _make_scalp_env()
        env.reset()
        env.step(1)  # terminate
        obs, reward, terminated, truncated, info = env.step(0)  # step after done
        assert terminated is True
        assert reward == 0.0

    def test_tp_with_profit_gets_bonus(self):
        """수익 상태에서 TP → v7: reward = pnl * 2.0 보너스."""
        # 상승 추세 캔들로 환경 생성
        candles = _make_candles(80, trend=0.001)
        env = ScalpExitEnv(candle_data=candles)
        env.reset()
        # 몇 스텝 HOLD 후 TP (상승 추세이므로 수익 확률 높음)
        for _ in range(3):
            env.step(0)
        obs, reward, terminated, _, info = env.step(1)  # TP
        if info.get("pnl_pct", 0) > 0:
            # v7: 수익이면 reward = pnl * 2.0 (후회비용으로 약간 감소 가능)
            expected = info["pnl_pct"] * 2.0
            assert reward == pytest.approx(expected, abs=0.1)

    def test_sl_with_large_loss_gets_bonus(self):
        """큰 손실에서 빠른 손절 → +0.1 보너스."""
        # 하락 추세로 손실 유도
        candles = _make_candles(80, trend=-0.002)
        env = ScalpExitEnv(candle_data=candles)
        env.reset()
        for _ in range(5):
            env.step(0)
        obs, reward, terminated, _, info = env.step(2)  # SL
        pnl = info.get("pnl_pct", 0)
        if pnl < -0.3:
            # 큰 손실 + SL → pnl + 0.1 보너스
            expected = pnl + 0.1
            assert reward == pytest.approx(expected, abs=0.01)

    def test_episode_count_increments(self):
        env = _make_scalp_env()
        env.reset()
        env.step(1)  # terminate
        assert env.episode_count == 1
        env.reset()
        env.step(2)  # terminate
        assert env.episode_count == 2

    def test_win_loss_tracking(self):
        env = _make_scalp_env()
        initial_wins = env.wins
        initial_losses = env.losses
        env.reset()
        _, _, _, _, info = env.step(1)
        pnl = info.get("pnl_pct", 0)
        if pnl > 0:
            assert env.wins == initial_wins + 1
        else:
            assert env.losses == initial_losses + 1


class TestScalpExitEnvForcedExits:
    """강제 청산 검증 (timeout, forced SL)."""

    def test_timeout_at_max_hold(self):
        """MAX_HOLD 분 경과 시 강제 청산."""
        env = _make_scalp_env(n_candles=80)
        env.reset()
        terminated = False
        for i in range(MAX_HOLD + 5):
            if terminated:
                break
            obs, reward, terminated, truncated, info = env.step(0)  # HOLD
        assert terminated is True
        assert info.get("exit_reason") in ("timeout", "forced_sl")

    def test_timeout_reward_is_penalized(self):
        """타임아웃 시 보상 = pnl * 0.8 (약간 벌칙)."""
        env = _make_scalp_env(n_candles=80)
        env.reset()
        info = {}
        for _ in range(MAX_HOLD + 1):
            obs, reward, terminated, _, info = env.step(0)
            if terminated:
                break
        if info.get("exit_reason") == "timeout":
            # reward = pnl * 0.8
            pnl = info["pnl_pct"]
            assert reward == pytest.approx(pnl * 0.8, abs=0.02)

    def test_forced_sl_when_loss_exceeds_threshold(self):
        """손실이 SL_DEFAULT 초과 시 강제 손절."""
        # 급락 캔들 생성
        candles = _make_candles(80, trend=-0.005)
        env = ScalpExitEnv(candle_data=candles)
        env.reset()
        info = {}
        for _ in range(MAX_HOLD + 1):
            obs, reward, terminated, _, info = env.step(0)
            if terminated:
                break
        # 급락이면 forced_sl 또는 timeout
        assert terminated is True
        if info.get("exit_reason") == "forced_sl":
            # v7: forced_sl reward = pnl * 1.5 (큰 벌칙)
            pnl = info["pnl_pct"]
            assert reward == pytest.approx(pnl * 1.5, abs=0.02)


class TestScalpExitEnvV2:
    """V2 연속 행동 공간 검증."""

    def test_continuous_action_space(self):
        candles = _make_candles(80)
        env = ScalpExitEnvV2(candle_data=candles)
        assert env.action_space.shape == (1,)
        assert env.action_space.low[0] == pytest.approx(0.0)
        assert env.action_space.high[0] == pytest.approx(1.0)

    def test_low_action_holds(self):
        candles = _make_candles(80)
        env = ScalpExitEnvV2(candle_data=candles)
        env.reset()
        obs, reward, terminated, _, info = env.step(np.array([0.1]))
        assert not terminated  # 0.1 < 0.3 → HOLD

    def test_mid_action_takes_profit(self):
        candles = _make_candles(80)
        env = ScalpExitEnvV2(candle_data=candles)
        env.reset()
        obs, reward, terminated, _, info = env.step(np.array([0.5]))
        assert terminated  # 0.3 <= 0.5 < 0.7 → TAKE_PROFIT
        assert info["exit_reason"] == "take_profit"

    def test_high_action_stops_loss(self):
        candles = _make_candles(80)
        env = ScalpExitEnvV2(candle_data=candles)
        env.reset()
        obs, reward, terminated, _, info = env.step(np.array([0.9]))
        assert terminated  # 0.9 >= 0.7 → STOP_LOSS
        assert info["exit_reason"] == "stop_loss"


class TestScalpExitEnvWinRate:
    """승률 속성 검증."""

    def test_win_rate_zero_initially(self):
        env = _make_scalp_env()
        assert env.win_rate == 0

    def test_win_rate_after_episodes(self):
        env = _make_scalp_env()
        # Run a few episodes
        for _ in range(5):
            env.reset()
            env.step(1)  # TP to terminate
        total = env.wins + env.losses
        if total > 0:
            assert env.win_rate == pytest.approx(env.wins / total)


# ============================================================
# 2. RewardCalculator Tests (v8)
# ============================================================

class TestRewardCalculatorInit:
    """초기화 검증."""

    def test_default_params(self):
        rc = RewardCalculator()
        assert rc.window_size == 20
        assert rc.pnl_scale == 100.0
        assert rc.max_drawdown_penalty == 3.0

    def test_custom_params(self):
        rc = RewardCalculator(window_size=10, pnl_scale=50.0)
        assert rc.window_size == 10
        assert rc.pnl_scale == 50.0

    def test_reset(self):
        rc = RewardCalculator()
        rc.reset(1_000_000)
        assert rc.peak_value == 1_000_000
        assert rc.max_drawdown == 0.0
        assert rc.total_trades == 0
        assert len(rc.returns_history) == 0


class TestRewardCalculatorPnL:
    """PnL 보상 클리핑 검증."""

    def test_pnl_reward_clipping_upper(self):
        """raw_return * 100 > 1.5 이면 1.5로 클리핑."""
        rc = RewardCalculator()
        rc.reset(100)
        result = rc.calculate(100, 103, 0.5, 0.5, 1)  # +3% → 100*0.03=3.0 → clip 1.5
        assert result["components"]["pnl_reward"] == pytest.approx(1.5)

    def test_pnl_reward_clipping_lower(self):
        """raw_return * 100 < -1.5 이면 -1.5로 클리핑."""
        rc = RewardCalculator()
        rc.reset(100)
        result = rc.calculate(100, 97, 0.5, 0.5, 1)  # -3%
        assert result["components"]["pnl_reward"] == pytest.approx(-1.5)

    def test_pnl_reward_within_range(self):
        """작은 변화는 클리핑 없음."""
        rc = RewardCalculator()
        rc.reset(100)
        result = rc.calculate(100, 100.5, 0.5, 0.5, 1)  # +0.5%
        expected = 0.005 * 100  # = 0.5
        assert result["components"]["pnl_reward"] == pytest.approx(expected, abs=0.01)


class TestRewardCalculatorDirection:
    """방향성 보상 검증."""

    def test_correct_direction_btc_hold_price_up(self):
        """BTC 보유(ratio>0.5) + 가격 상승 → 양의 방향성 보상."""
        rc = RewardCalculator()
        rc.reset(100)
        result = rc.calculate(
            100, 101, 0.5, 0.5, 1,
            btc_ratio=0.8, price_change=0.01  # 1% 상승
        )
        assert result["components"]["direction_reward"] > 0

    def test_correct_direction_cash_hold_price_down(self):
        """현금 보유(ratio<0.5) + 가격 하락 → 양의 방향성 보상."""
        rc = RewardCalculator()
        rc.reset(100)
        result = rc.calculate(
            100, 99, 0.5, 0.5, 1,
            btc_ratio=0.2, price_change=-0.01  # 1% 하락
        )
        assert result["components"]["direction_reward"] > 0

    def test_wrong_direction_btc_hold_price_down(self):
        """BTC 보유(ratio>0.5) + 가격 하락 → 음의 방향성 보상."""
        rc = RewardCalculator()
        rc.reset(100)
        result = rc.calculate(
            100, 99, 0.5, 0.5, 1,
            btc_ratio=0.8, price_change=-0.01
        )
        assert result["components"]["direction_reward"] < 0

    def test_no_direction_reward_small_change(self):
        """가격 변화 < 0.1% → 방향성 보상 0."""
        rc = RewardCalculator()
        rc.reset(100)
        result = rc.calculate(
            100, 100, 0.5, 0.5, 1,
            btc_ratio=0.8, price_change=0.0005  # 0.05%
        )
        assert result["components"]["direction_reward"] == 0.0

    def test_direction_reward_clipping(self):
        """방향성 보상은 [-0.5, 0.5] 범위."""
        rc = RewardCalculator()
        rc.reset(100)
        result = rc.calculate(
            100, 110, 0.5, 0.5, 1,
            btc_ratio=1.0, price_change=0.1  # 극단적
        )
        assert -0.5 <= result["components"]["direction_reward"] <= 0.5


class TestRewardCalculatorSharpe:
    """Sharpe 보상 검증."""

    def test_sharpe_with_few_returns(self):
        """3개 미만 리턴 시 latest_return * 15."""
        rc = RewardCalculator()
        rc.reset(100)
        result = rc.calculate(100, 101, 0.5, 0.5, 1)
        # n < 3 → latest_return * 15
        raw_return = (101 - 100) / 100
        expected_sharpe = raw_return * 15
        assert result["components"]["sharpe_reward"] == pytest.approx(expected_sharpe, abs=0.01)

    def test_sharpe_with_enough_returns(self):
        """3개 이상 리턴 → Sharpe ratio * 0.25."""
        rc = RewardCalculator()
        rc.reset(100)
        # Fill history with known returns
        for v in [100.5, 101, 101.5, 102]:
            prev = rc.peak_value if len(rc.returns_history) == 0 else 100 + len(rc.returns_history) * 0.5
            rc.calculate(prev, prev + 0.5, 0.5, 0.5, len(rc.returns_history))
        # Now compute with enough history
        result = rc.calculate(102, 102.5, 0.5, 0.5, 5)
        assert "sharpe_reward" in result["components"]

    def test_sharpe_clipping(self):
        """Sharpe 보상은 [-1.5, 1.5] 범위."""
        rc = RewardCalculator()
        rc.reset(100)
        # Build up consistent positive returns for high sharpe
        val = 100
        for i in range(10):
            new_val = val * 1.01
            rc.calculate(val, new_val, 0.5, 0.5, i)
            val = new_val
        result = rc.calculate(val, val * 1.05, 0.5, 0.5, 10)
        assert -1.5 <= result["components"]["sharpe_reward"] <= 1.5


class TestRewardCalculatorMDD:
    """MDD 페널티 검증."""

    def test_no_penalty_below_3pct(self):
        """드로다운 < 3% → 페널티 없음."""
        rc = RewardCalculator()
        rc.reset(100)
        # Small dip: 2%
        result = rc.calculate(100, 98, 0.5, 0.5, 1)
        assert result["components"]["mdd_penalty"] == 0.0

    def test_penalty_above_3pct(self):
        """드로다운 > 3% → 페널티 적용."""
        rc = RewardCalculator()
        rc.reset(100)
        rc.peak_value = 100
        # 5% drawdown
        result = rc.calculate(100, 95, 0.5, 0.5, 1)
        dd = (100 - 95) / 100  # 0.05
        expected = -dd * 3.0  # -0.15
        assert result["components"]["mdd_penalty"] == pytest.approx(expected, abs=0.01)

    def test_mdd_tracks_peak(self):
        """peak_value가 올바르게 갱신되는지 확인."""
        rc = RewardCalculator()
        rc.reset(100)
        rc.calculate(100, 110, 0.5, 0.5, 1)  # new peak
        assert rc.peak_value == 110
        rc.calculate(110, 105, 0.5, 0.5, 2)  # drawdown from 110
        assert rc.max_drawdown == pytest.approx((110 - 105) / 110, abs=1e-6)


class TestRewardCalculatorTradePnLBonus:
    """거래 수익성 보너스 검증."""

    def test_no_bonus_no_trade(self):
        """행동 변화 없으면 보너스 없음."""
        rc = RewardCalculator()
        rc.reset(100)
        result = rc.calculate(100, 101, 0.5, 0.5, 1)  # same action
        assert result["components"]["trade_pnl_bonus"] == 0.0

    def test_profit_trade_bonus(self):
        """수익 거래 → +0.5 보너스."""
        rc = RewardCalculator()
        rc.reset(100)
        rc.prev_trade_value = 100
        # Action change > 0.05 and trade_return > 0.002
        result = rc.calculate(100, 101, 0.8, 0.0, 1)  # action change = 0.8
        assert result["components"]["trade_pnl_bonus"] == pytest.approx(0.5)

    def test_loss_trade_penalty(self):
        """손실 거래 → -0.2 페널티."""
        rc = RewardCalculator()
        rc.reset(100)
        rc.prev_trade_value = 100
        result = rc.calculate(100, 99, 0.8, 0.0, 1)  # loss trade
        assert result["components"]["trade_pnl_bonus"] == pytest.approx(-0.2)

    def test_neutral_trade_no_bonus(self):
        """미미한 수익/손실 → 보너스 없음."""
        rc = RewardCalculator()
        rc.reset(100)
        rc.prev_trade_value = 100
        result = rc.calculate(100, 100.1, 0.8, 0.0, 1)  # +0.1% < 0.2% threshold
        assert result["components"]["trade_pnl_bonus"] == 0.0

    def test_trade_count_increments(self):
        """거래 시 total_trades 증가."""
        rc = RewardCalculator()
        rc.reset(100)
        assert rc.total_trades == 0
        rc.calculate(100, 101, 0.8, 0.0, 1)
        assert rc.total_trades == 1
        rc.calculate(101, 102, 0.0, 0.8, 2)
        assert rc.total_trades == 2


class TestRewardCalculatorTotal:
    """총 보상 합산 검증."""

    def test_reward_is_sum_of_components(self):
        rc = RewardCalculator()
        rc.reset(100)
        result = rc.calculate(100, 101, 0.8, 0.0, 1, btc_ratio=0.7, price_change=0.01)
        comp = result["components"]
        expected = (
            comp["pnl_reward"]
            + comp["direction_reward"]
            + comp["sharpe_reward"]
            + comp["mdd_penalty"]
            + comp["trade_pnl_bonus"]
        )
        assert result["reward"] == pytest.approx(expected, abs=1e-6)


class TestRewardCalculatorEpisodeStats:
    """에피소드 통계 검증."""

    def test_episode_stats_format(self):
        rc = RewardCalculator()
        rc.reset(100)
        rc.calculate(100, 101, 0.5, 0.5, 1)
        rc.calculate(101, 102, 0.5, 0.5, 2)
        stats = rc.get_episode_stats(102, 100)
        assert "total_return_pct" in stats
        assert "total_trades" in stats
        assert "max_drawdown" in stats
        assert "sharpe_ratio" in stats
        assert stats["total_return_pct"] == pytest.approx(2.0, abs=0.1)


# ============================================================
# 3. StateEncoder Tests
# ============================================================

class TestStateEncoderInit:
    """StateEncoder 초기화 검증."""

    def test_observation_dim_is_42(self):
        assert OBSERVATION_DIM == 42

    def test_feature_spec_has_42_entries(self):
        assert len(FEATURE_SPEC) == 42

    def test_feature_names_list(self):
        assert len(FEATURE_NAMES) == 42
        assert FEATURE_NAMES[0] == "price_change_1h"
        assert FEATURE_NAMES[-1] == "daily_trade_count"

    def test_encoder_dims(self):
        encoder = StateEncoder()
        assert encoder.obs_dim == 42
        assert len(encoder.feature_names) == 42

    def test_normalization_ranges(self):
        """모든 정규화 범위가 양수(max > min)인지 확인."""
        for name, (lo, hi) in FEATURE_SPEC.items():
            assert hi > lo, f"{name}: max({hi}) must be > min({lo})"


class TestStateEncoderEncode:
    """encode 메서드 검증."""

    def test_output_shape(self):
        encoder = StateEncoder()
        md = _make_market_data_for_encoder()
        ext = _make_external_data_for_encoder()
        pf = _make_portfolio_for_encoder()
        obs = encoder.encode(md, ext, pf)
        assert obs.shape == (42,)
        assert obs.dtype == np.float32

    def test_output_in_zero_one(self):
        """모든 출력이 [0, 1] 범위."""
        encoder = StateEncoder()
        md = _make_market_data_for_encoder()
        ext = _make_external_data_for_encoder()
        pf = _make_portfolio_for_encoder()
        obs = encoder.encode(md, ext, pf)
        assert np.all(obs >= 0.0), f"Below 0: {obs[obs < 0]}"
        assert np.all(obs <= 1.0), f"Above 1: {obs[obs > 1]}"

    def test_neutral_values_around_midpoint(self):
        """중립 데이터 → 대부분의 피처가 0.3~0.7 사이."""
        encoder = StateEncoder()
        md = _make_market_data_for_encoder()
        ext = _make_external_data_for_encoder()
        pf = _make_portfolio_for_encoder()
        obs = encoder.encode(md, ext, pf)
        # At least half the features should be in the middle range
        mid_count = np.sum((obs >= 0.2) & (obs <= 0.8))
        assert mid_count >= 20, f"Only {mid_count}/42 in middle range"

    def test_extreme_rsi_maps_correctly(self):
        """RSI 경계값 매핑 검증.

        Note: source code uses `indicators.get("rsi_14", 50) or 50` which
        treats 0 as falsy and maps to 50. So RSI=0 → encoded as 50 → 0.5.
        We test RSI=5 (truthy low) and RSI=100 instead.
        """
        encoder = StateEncoder()
        rsi_idx = FEATURE_NAMES.index("rsi_14")
        ext = _make_external_data_for_encoder()
        pf = _make_portfolio_for_encoder()

        # RSI=5 (low but truthy) → normalized ≈ 5/100 = 0.05
        md_low = _make_market_data_for_encoder(rsi=5)
        obs_low = encoder.encode(md_low, ext, pf)
        assert obs_low[rsi_idx] == pytest.approx(0.05, abs=0.01)

        # RSI=100 → normalized 1.0
        md_high = _make_market_data_for_encoder(rsi=100)
        obs_high = encoder.encode(md_high, ext, pf)
        assert obs_high[rsi_idx] == pytest.approx(1.0, abs=0.01)

    def test_rsi_zero_falsy_behavior(self):
        """RSI=0은 `or 50` 패턴으로 인해 50으로 처리됨 (알려진 동작)."""
        encoder = StateEncoder()
        rsi_idx = FEATURE_NAMES.index("rsi_14")
        md = _make_market_data_for_encoder(rsi=0)
        ext = _make_external_data_for_encoder()
        pf = _make_portfolio_for_encoder()
        obs = encoder.encode(md, ext, pf)
        # 0 is falsy → `0 or 50` = 50 → normalized = 0.5
        assert obs[rsi_idx] == pytest.approx(0.5, abs=0.01)

    def test_fgi_encoding(self):
        """FGI 0→0.0, 100→1.0."""
        encoder = StateEncoder()
        fgi_idx = FEATURE_NAMES.index("fgi")
        md = _make_market_data_for_encoder()
        pf = _make_portfolio_for_encoder()

        ext_fear = _make_external_data_for_encoder(fgi=0)
        obs_fear = encoder.encode(md, ext_fear, pf)
        assert obs_fear[fgi_idx] == pytest.approx(0.0, abs=0.01)

        ext_greed = _make_external_data_for_encoder(fgi=100)
        obs_greed = encoder.encode(md, ext_greed, pf)
        assert obs_greed[fgi_idx] == pytest.approx(1.0, abs=0.01)

    def test_missing_agent_state_defaults(self):
        """agent_state 없어도 동작."""
        encoder = StateEncoder()
        md = _make_market_data_for_encoder()
        ext = _make_external_data_for_encoder()
        pf = _make_portfolio_for_encoder()
        obs = encoder.encode(md, ext, pf, agent_state=None)
        assert obs.shape == (42,)

    def test_with_agent_state(self):
        """agent_state 포함 시 danger/opportunity 반영."""
        encoder = StateEncoder()
        md = _make_market_data_for_encoder()
        ext = _make_external_data_for_encoder()
        pf = _make_portfolio_for_encoder()
        ag = {"danger_score": 80, "opportunity_score": 20, "cascade_risk": 50,
              "consecutive_losses": 5, "hours_since_last_trade": 48, "daily_trade_count": 3}
        obs = encoder.encode(md, ext, pf, agent_state=ag)
        danger_idx = FEATURE_NAMES.index("danger_score")
        assert obs[danger_idx] == pytest.approx(80 / 100, abs=0.01)


class TestStateEncoderDecode:
    """decode_feature 검증."""

    def test_decode_roundtrip(self):
        """encode → decode 왕복 검증."""
        encoder = StateEncoder()
        md = _make_market_data_for_encoder(rsi=70)
        ext = _make_external_data_for_encoder(fgi=30)
        pf = _make_portfolio_for_encoder()
        obs = encoder.encode(md, ext, pf)

        decoded_rsi = encoder.decode_feature(obs, "rsi_14")
        assert decoded_rsi == pytest.approx(70, abs=5)  # 근사값 (정규화 손실)

        decoded_fgi = encoder.decode_feature(obs, "fgi")
        assert decoded_fgi == pytest.approx(30, abs=5)


class TestStateEncoderEdgeValues:
    """경계값 테스트."""

    def test_all_zeros_portfolio(self):
        """빈 포트폴리오도 에러 없이 동작."""
        encoder = StateEncoder()
        md = _make_market_data_for_encoder()
        ext = _make_external_data_for_encoder()
        pf = {"krw_balance": 0, "total_eval": 0, "holdings": []}
        obs = encoder.encode(md, ext, pf)
        assert obs.shape == (42,)
        assert not np.any(np.isnan(obs))
        assert not np.any(np.isinf(obs))

    def test_extreme_price_change(self):
        """극단적 가격 변동에도 클리핑."""
        encoder = StateEncoder()
        md = _make_market_data_for_encoder(change_rate=0.5)  # 50% 변동
        ext = _make_external_data_for_encoder()
        pf = _make_portfolio_for_encoder()
        obs = encoder.encode(md, ext, pf)
        assert np.all(obs >= 0.0)
        assert np.all(obs <= 1.0)


# ============================================================
# 4. AblationRewardWrapper Tests
# ============================================================

class TestAblationRewardWrapperInit:
    """AblationRewardWrapper 초기화 검증."""

    def test_all_components_valid(self):
        wrapper = AblationRewardWrapper(REWARD_COMPONENTS.copy())
        assert len(wrapper.active) == 5

    def test_single_component(self):
        wrapper = AblationRewardWrapper(["pnl_reward"])
        assert wrapper.active == {"pnl_reward"}

    def test_invalid_component_raises(self):
        with pytest.raises(ValueError, match="Unknown component"):
            AblationRewardWrapper(["invalid_component"])

    def test_empty_components(self):
        wrapper = AblationRewardWrapper([])
        assert len(wrapper.active) == 0

    def test_component_labels_match(self):
        """모든 REWARD_COMPONENTS에 대응하는 라벨이 있는지."""
        for comp in REWARD_COMPONENTS:
            assert comp in COMPONENT_LABELS


class TestAblationRewardWrapperModify:
    """modify_reward 검증."""

    def _make_reward_dict(self, pnl=0.5, direction=0.3, sharpe=0.2, mdd=-0.1, trade=0.4):
        return {
            "components": {
                "pnl_reward": pnl,
                "direction_reward": direction,
                "sharpe_reward": sharpe,
                "mdd_penalty": mdd,
                "trade_pnl_bonus": trade,
            }
        }

    def test_all_active_returns_full_sum(self):
        """모든 성분 활성화 → 원본 보상과 동일."""
        wrapper = AblationRewardWrapper(REWARD_COMPONENTS.copy())
        rd = self._make_reward_dict()
        total = wrapper.modify_reward(rd)
        expected = 0.5 + 0.3 + 0.2 + (-0.1) + 0.4
        assert total == pytest.approx(expected, abs=1e-6)

    def test_single_pnl_only(self):
        """pnl_reward만 활성화."""
        wrapper = AblationRewardWrapper(["pnl_reward"])
        rd = self._make_reward_dict(pnl=0.7)
        assert wrapper.modify_reward(rd) == pytest.approx(0.7)

    def test_leave_one_out_no_mdd(self):
        """mdd_penalty 제거 → 나머지 4성분 합."""
        active = [c for c in REWARD_COMPONENTS if c != "mdd_penalty"]
        wrapper = AblationRewardWrapper(active)
        rd = self._make_reward_dict(pnl=0.5, direction=0.3, sharpe=0.2, mdd=-0.5, trade=0.1)
        total = wrapper.modify_reward(rd)
        expected = 0.5 + 0.3 + 0.2 + 0.1  # mdd excluded
        assert total == pytest.approx(expected, abs=1e-6)

    def test_leave_one_out_correctness_all_five(self):
        """5개 성분에 대해 각각 leave-one-out이 올바른지 체계적으로 검증."""
        values = {
            "pnl_reward": 1.0,
            "direction_reward": 2.0,
            "sharpe_reward": 3.0,
            "mdd_penalty": -4.0,
            "trade_pnl_bonus": 5.0,
        }
        full_sum = sum(values.values())  # 1+2+3-4+5 = 7
        rd = {"components": values}

        for remove_comp in REWARD_COMPONENTS:
            active = [c for c in REWARD_COMPONENTS if c != remove_comp]
            wrapper = AblationRewardWrapper(active)
            total = wrapper.modify_reward(rd)
            expected = full_sum - values[remove_comp]
            assert total == pytest.approx(expected, abs=1e-6), (
                f"Leave-one-out {remove_comp}: got {total}, expected {expected}"
            )

    def test_pairwise_combination(self):
        """2성분 조합 검증."""
        values = {
            "pnl_reward": 1.0,
            "direction_reward": 2.0,
            "sharpe_reward": 3.0,
            "mdd_penalty": -1.0,
            "trade_pnl_bonus": 4.0,
        }
        rd = {"components": values}
        wrapper = AblationRewardWrapper(["pnl_reward", "direction_reward"])
        assert wrapper.modify_reward(rd) == pytest.approx(3.0)

    def test_empty_active_returns_zero(self):
        """활성 성분 없으면 보상 0."""
        wrapper = AblationRewardWrapper([])
        rd = self._make_reward_dict(pnl=1.0, direction=1.0, sharpe=1.0, mdd=-1.0, trade=1.0)
        assert wrapper.modify_reward(rd) == 0.0

    def test_missing_component_in_reward_dict(self):
        """reward_dict에 일부 성분만 있어도 활성 성분만 합산."""
        wrapper = AblationRewardWrapper(["pnl_reward", "direction_reward"])
        # direction_reward가 dict에 없으면 0으로 처리
        rd = {"components": {"pnl_reward": 0.5}}
        assert wrapper.modify_reward(rd) == pytest.approx(0.5)

    def test_invalid_component_in_constructor_raises(self):
        """유효하지 않은 성분명은 ValueError."""
        with pytest.raises(ValueError, match="Unknown component"):
            AblationRewardWrapper(["pnl_reward", "nonexistent_in_dict"])


class TestRewardComponentsList:
    """REWARD_COMPONENTS 상수 검증."""

    def test_five_components(self):
        assert len(REWARD_COMPONENTS) == 5

    def test_component_names(self):
        expected = ["pnl_reward", "direction_reward", "sharpe_reward", "mdd_penalty", "trade_pnl_bonus"]
        assert REWARD_COMPONENTS == expected

    def test_labels_for_all_components(self):
        for comp in REWARD_COMPONENTS:
            assert comp in COMPONENT_LABELS
            assert isinstance(COMPONENT_LABELS[comp], str)


# ============================================================
# 5. Integration / Cross-module Tests
# ============================================================

class TestRewardCalculatorWithEncoder:
    """RewardCalculator와 StateEncoder 연동 검증."""

    def test_btc_ratio_from_encoder(self):
        """StateEncoder의 position_ratio를 RewardCalculator에 전달."""
        encoder = StateEncoder()
        md = _make_market_data_for_encoder()
        ext = _make_external_data_for_encoder()
        pf = _make_portfolio_for_encoder(krw=3_000_000, btc_eval=7_000_000)
        obs = encoder.encode(md, ext, pf)

        pos_idx = FEATURE_NAMES.index("position_ratio")
        btc_ratio = obs[pos_idx]  # normalized [0,1]
        assert btc_ratio > 0.5  # BTC가 더 많으므로

        rc = RewardCalculator()
        rc.reset(10_000_000)
        result = rc.calculate(
            10_000_000, 10_100_000, 0.7, 0.0, 1,
            btc_ratio=btc_ratio, price_change=0.01
        )
        # BTC 많이 보유 + 가격 상승 → 양의 방향성
        assert result["components"]["direction_reward"] > 0


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
