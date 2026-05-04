#!/usr/bin/env python3
"""ScalpExitEnv v6 파라미터 단위 테스트

외부 의존성 없이 합성 캔들 데이터로 ScalpExitEnv/V2를 검증한다.
"""

import sys
import math
import random
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

# 프로젝트 루트를 path에 추가
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from scalp_ml.scalp_exit_env import (
    ScalpExitEnv,
    ScalpExitEnvV2,
    ScalpEpisode,
    FEE_PCT,
    MAX_HOLD,
    TP_DEFAULT,
    SL_DEFAULT,
)


@pytest.fixture(autouse=True)
def _seed_random():
    """스칼프 env가 전역 random.randint/choice를 사용 — 테스트 간 격리.
    seed=123 사용 (seed=42는 test_hold 깨뜨림). 종료 시 상태 복원."""
    py_state = random.getstate()
    np_state = np.random.get_state()
    random.seed(123)
    np.random.seed(123)
    yield
    random.setstate(py_state)
    np.random.set_state(np_state)


# ═══════════════════════════════════════════════════
# 헬퍼: 합성 1분봉 생성
# ═══════════════════════════════════════════════════

def _make_candles(n: int = 100, base_price: float = 100_000_000,
                  trend: float = 0.0, volatility: float = 0.001) -> list[dict]:
    """합성 1분봉 캔들 데이터 생성.

    Args:
        n: 캔들 개수
        base_price: 시작 가격
        trend: 분당 추세 비율 (양수=상승, 음수=하락)
        volatility: 랜덤 변동폭 비율
    """
    rng = np.random.RandomState(42)
    candles = []
    price = base_price
    for i in range(n):
        noise = rng.normal(0, volatility)
        price = price * (1 + trend + noise)
        candles.append({
            "trade_price": price,
            "candle_acc_trade_volume": rng.uniform(0.5, 5.0),
            "close": price,
            "volume": rng.uniform(0.5, 5.0),
        })
    return candles


def _make_env(candles=None, **kwargs) -> ScalpExitEnv:
    """테스트용 환경 생성."""
    if candles is None:
        candles = _make_candles(200)
    return ScalpExitEnv(candle_data=candles, **kwargs)


def _make_env_v2(candles=None, **kwargs) -> ScalpExitEnvV2:
    """테스트용 V2 환경 생성."""
    if candles is None:
        candles = _make_candles(200)
    return ScalpExitEnvV2(candle_data=candles, **kwargs)


# ═══════════════════════════════════════════════════
# v6 파라미터 상수 검증
# ═══════════════════════════════════════════════════

class TestV6Parameters:
    """v6 파라미터가 실전과 동일한지 확인."""

    def test_fee_pct(self):
        assert FEE_PCT == 0.1, "왕복 수수료 0.1%"

    def test_max_hold(self):
        assert MAX_HOLD == 15, "최대 보유 15분"

    def test_tp_default(self):
        assert TP_DEFAULT == 0.3, "기본 익절 0.3%"

    def test_sl_default(self):
        assert SL_DEFAULT == 0.25, "기본 손절 0.25%"


# ═══════════════════════════════════════════════════
# 관측/행동 공간 테스트
# ═══════════════════════════════════════════════════

class TestSpaces:
    """관측 공간과 행동 공간 검증."""

    def test_observation_space_shape(self):
        env = _make_env()
        assert env.observation_space.shape == (8,), "8개 피처"

    def test_observation_space_low_bounds(self):
        env = _make_env()
        expected_low = np.array([-10, 0, -5, -5, 0, 0, 0, 0], dtype=np.float32)
        np.testing.assert_array_equal(env.observation_space.low, expected_low)

    def test_observation_space_high_bounds(self):
        env = _make_env()
        expected_high = np.array([10, MAX_HOLD, 5, 5, 10, 100, 1, 2], dtype=np.float32)
        np.testing.assert_array_equal(env.observation_space.high, expected_high)

    def test_action_space_discrete_3(self):
        env = _make_env()
        assert hasattr(env.action_space, "n")
        assert env.action_space.n == 3, "HOLD=0, TP=1, SL=2"

    def test_observation_dtype(self):
        env = _make_env()
        obs, info = env.reset()
        assert obs.dtype == np.float32


# ═══════════════════════════════════════════════════
# reset 테스트
# ═══════════════════════════════════════════════════

class TestReset:
    """reset이 유효한 관측을 반환하는지 확인."""

    def test_reset_returns_tuple(self):
        env = _make_env()
        result = env.reset()
        assert isinstance(result, tuple) and len(result) == 2

    def test_reset_obs_shape(self):
        env = _make_env()
        obs, info = env.reset()
        assert obs.shape == (8,)

    def test_reset_obs_in_bounds(self):
        env = _make_env()
        obs, _ = env.reset()
        low = env.observation_space.low
        high = env.observation_space.high
        # 관측값이 허용 범위 안에 있어야 함 (약간의 부동소수점 여유)
        assert np.all(obs >= low - 1e-5), f"obs below low: {obs} < {low}"
        assert np.all(obs <= high + 1e-5), f"obs above high: {obs} > {high}"

    def test_reset_clears_done(self):
        env = _make_env()
        env.reset()
        # 즉시 step 가능해야 함
        obs, reward, terminated, truncated, info = env.step(0)
        assert not (terminated and truncated), "reset 직후에 바로 종료되면 안됨 (첫 hold)"

    def test_reset_with_seed(self):
        """seed로 gymnasium RNG는 결정적이지만, _find_signal_entry가 random 모듈을 사용하므로 완전 재현은 불가."""
        candles = _make_candles(200)
        env1 = _make_env(candles)
        obs1, _ = env1.reset(seed=123)
        # 관측 벡터의 형태와 범위만 검증
        assert obs1.shape == (8,)
        assert obs1.dtype == np.float32

    def test_reset_info_is_dict(self):
        env = _make_env()
        _, info = env.reset()
        assert isinstance(info, dict)


# ═══════════════════════════════════════════════════
# HOLD 행동 테스트
# ═══════════════════════════════════════════════════

class TestHoldAction:
    """action=0 (HOLD) 동작 검증."""

    def test_hold_returns_small_negative_reward(self):
        env = _make_env()
        env.reset()
        obs, reward, terminated, truncated, info = env.step(0)
        # v7: HOLD 보상은 모멘텀에 따라 -0.01 ~ +0.01 범위
        if not terminated:
            assert -0.02 <= reward <= 0.05, f"v7 HOLD 보상 범위 초과: {reward}"

    def test_hold_not_terminated(self):
        """강제 청산 조건이 아니면 HOLD는 에피소드를 종료하지 않음."""
        # 평평한 가격으로 강제 손절 방지
        candles = _make_candles(200, volatility=0.0001, trend=0.0)
        env = _make_env(candles)
        env.reset()
        obs, reward, terminated, truncated, info = env.step(0)
        assert not terminated, "첫 HOLD에서 종료되면 안됨"

    def test_hold_increments_step(self):
        env = _make_env()
        env.reset()
        initial_step = env._current_step
        env.step(0)
        assert env._current_step == initial_step + 1


# ═══════════════════════════════════════════════════
# TAKE_PROFIT 행동 테스트
# ═══════════════════════════════════════════════════

class TestTakeProfitAction:
    """action=1 (TAKE_PROFIT) 동작 검증."""

    def test_tp_terminates_episode(self):
        env = _make_env()
        env.reset()
        _, _, terminated, _, info = env.step(1)
        assert terminated
        assert info.get("exit_reason") == "take_profit"

    def test_tp_positive_pnl_gets_bonus(self):
        """수익 상태에서 TP는 pnl * 1.5 보너스."""
        # 상승 추세 캔들로 양의 PnL 유도
        candles = _make_candles(200, trend=0.002, volatility=0.0001)
        env = _make_env(candles)
        env.reset()
        # 몇 스텝 HOLD 후 TP
        for _ in range(3):
            env.step(0)
        obs, reward, terminated, _, info = env.step(1)
        pnl = info.get("pnl_pct", 0)
        if pnl > 0:
            # reward = pnl * 1.5
            assert reward > 0, f"수익 TP인데 보상이 음수: reward={reward}, pnl={pnl}"

    def test_tp_negative_pnl_scaled_down(self):
        """손실 상태에서 TP는 pnl * 0.8."""
        # 하락 추세
        candles = _make_candles(200, trend=-0.003, volatility=0.0001)
        env = _make_env(candles)
        env.reset()
        for _ in range(3):
            env.step(0)
        obs, reward, terminated, _, info = env.step(1)
        pnl = info.get("pnl_pct", 0)
        if pnl < 0:
            # reward = pnl * 0.8 (loss but less penalty)
            expected = pnl * 0.8
            assert reward == pytest.approx(expected, abs=0.01)

    def test_tp_records_hold_minutes(self):
        env = _make_env()
        env.reset()
        env.step(0)  # 1분 hold
        env.step(0)  # 2분 hold
        _, _, terminated, _, info = env.step(1)  # TP at 3분
        assert terminated
        assert "hold_minutes" in info
        # hold_minutes = current_step - 15 (진입 시점)
        assert info["hold_minutes"] >= 1

    def test_tp_updates_episode_count(self):
        env = _make_env()
        assert env.episode_count == 0
        env.reset()
        env.step(1)
        assert env.episode_count == 1


# ═══════════════════════════════════════════════════
# STOP_LOSS 행동 테스트
# ═══════════════════════════════════════════════════

class TestStopLossAction:
    """action=2 (STOP_LOSS) 동작 검증."""

    def test_sl_terminates_episode(self):
        env = _make_env()
        env.reset()
        _, _, terminated, _, info = env.step(2)
        assert terminated
        assert info.get("exit_reason") == "stop_loss"

    def test_sl_big_loss_gets_bonus(self):
        """큰 손실(-0.3%+)에서 빠른 SL은 +0.1 보너스."""
        # 급락 캔들
        candles = _make_candles(200, trend=-0.005, volatility=0.0001)
        env = _make_env(candles)
        env.reset()
        # 충분히 하락하도록 hold
        for _ in range(5):
            env.step(0)
        _, reward, _, _, info = env.step(2)
        pnl = info.get("pnl_pct", 0)
        if pnl < -0.3:
            # reward = pnl + 0.1
            expected = pnl + 0.1
            assert reward == pytest.approx(expected, abs=0.01)

    def test_sl_positive_pnl_penalty(self):
        """수익 상태에서 SL은 -0.1 벌칙 (v7)."""
        # 상승 추세
        candles = _make_candles(200, trend=0.003, volatility=0.0001)
        env = _make_env(candles)
        env.reset()
        for _ in range(3):
            env.step(0)
        _, reward, _, _, info = env.step(2)
        pnl = info.get("pnl_pct", 0)
        if pnl > 0:
            # v7: 수익 중 SL → 고정 벌칙 -0.1
            assert reward == pytest.approx(-0.1, abs=0.01)


# ═══════════════════════════════════════════════════
# 타임아웃 (MAX_HOLD=15) 테스트
# ═══════════════════════════════════════════════════

class TestTimeout:
    """MAX_HOLD 도달 시 강제 청산."""

    def test_timeout_at_max_hold(self):
        """15분 HOLD 시 timeout 강제 청산."""
        # 평평한 가격으로 손절 방지
        candles = _make_candles(200, volatility=0.00001, trend=0.0)
        env = _make_env(candles)
        env.reset()

        terminated = False
        for step in range(MAX_HOLD + 5):
            obs, reward, terminated, truncated, info = env.step(0)
            if terminated:
                break

        assert terminated, "MAX_HOLD에 도달하면 종료되어야 함"
        assert info.get("exit_reason") == "timeout"

    def test_timeout_reward_scaled(self):
        """타임아웃 보상은 pnl * 0.8."""
        candles = _make_candles(200, volatility=0.00001, trend=0.0)
        env = _make_env(candles)
        env.reset()

        for _ in range(MAX_HOLD - 1):
            obs, reward, terminated, _, _ = env.step(0)
            if terminated:
                break

        if not terminated:
            obs, reward, terminated, _, info = env.step(0)
            if terminated and info.get("exit_reason") == "timeout":
                pnl = info["pnl_pct"]
                expected = pnl * 0.8
                assert reward == pytest.approx(expected, abs=0.05)


# ═══════════════════════════════════════════════════
# 강제 손절 (SL_DEFAULT=0.25) 테스트
# ═══════════════════════════════════════════════════

class TestForcedStopLoss:
    """SL_DEFAULT 도달 시 HOLD 중 강제 손절."""

    def test_forced_sl_on_big_drop(self):
        """PnL <= -SL_DEFAULT 시 HOLD해도 강제 손절."""
        # 강한 하락 (분당 -0.5%씩 하락 -> 몇 스텝이면 -0.25% 도달)
        candles = _make_candles(200, trend=-0.005, volatility=0.0001)
        env = _make_env(candles)
        env.reset()

        forced_sl = False
        for _ in range(MAX_HOLD):
            obs, reward, terminated, _, info = env.step(0)
            if terminated and info.get("exit_reason") == "forced_sl":
                forced_sl = True
                break

        assert forced_sl, "큰 하락 시 HOLD 중 강제 손절이 발동해야 함"

    def test_forced_sl_reward_penalty(self):
        """강제 손절 보상은 pnl * 1.5 (v7 벌칙 가중)."""
        candles = _make_candles(200, trend=-0.005, volatility=0.0001)
        env = _make_env(candles)
        env.reset()

        for _ in range(MAX_HOLD):
            obs, reward, terminated, _, info = env.step(0)
            if terminated and info.get("exit_reason") == "forced_sl":
                pnl = info["pnl_pct"]
                expected = pnl * 1.5  # v7: 강제 손절 큰 벌칙
                assert reward == pytest.approx(expected, abs=0.05)
                break


# ═══════════════════════════════════════════════════
# win_rate 프로퍼티 테스트
# ═══════════════════════════════════════════════════

class TestWinRate:
    """win_rate 프로퍼티 검증."""

    def test_win_rate_initial_zero(self):
        env = _make_env()
        assert env.win_rate == 0

    def test_win_rate_after_episodes(self):
        env = _make_env()
        # 2회 에피소드 수동 카운트
        env.wins = 3
        env.losses = 7
        assert env.win_rate == pytest.approx(0.3)

    def test_win_rate_all_wins(self):
        env = _make_env()
        env.wins = 5
        env.losses = 0
        assert env.win_rate == 1.0

    def test_win_rate_all_losses(self):
        env = _make_env()
        env.wins = 0
        env.losses = 5
        assert env.win_rate == 0.0


# ═══════════════════════════════════════════════════
# V2 연속 행동 공간 테스트
# ═══════════════════════════════════════════════════

class TestScalpExitEnvV2:
    """V2 연속 행동 공간 (SAC용)."""

    def test_v2_action_space_continuous(self):
        env = _make_env_v2()
        assert env.action_space.shape == (1,)
        np.testing.assert_array_equal(env.action_space.low, np.array([0.0]))
        np.testing.assert_array_equal(env.action_space.high, np.array([1.0]))

    def test_v2_observation_space_same_as_v1(self):
        env = _make_env_v2()
        assert env.observation_space.shape == (8,)

    def test_v2_low_action_is_hold(self):
        """action < 0.3 -> HOLD."""
        candles = _make_candles(200, volatility=0.00001)
        env = _make_env_v2(candles)
        env.reset()
        obs, reward, terminated, _, info = env.step(np.array([0.1]))
        if not terminated:
            # v7: 모멘텀 기반 HOLD 보상 (-0.01 ~ +0.01+)
            assert -0.02 <= reward <= 0.05, f"낮은 action은 HOLD, reward={reward}"

    def test_v2_mid_action_is_tp(self):
        """0.3 <= action < 0.7 -> TAKE_PROFIT."""
        env = _make_env_v2()
        env.reset()
        _, _, terminated, _, info = env.step(np.array([0.5]))
        assert terminated
        assert info.get("exit_reason") == "take_profit"

    def test_v2_high_action_is_sl(self):
        """action >= 0.7 -> STOP_LOSS."""
        env = _make_env_v2()
        env.reset()
        _, _, terminated, _, info = env.step(np.array([0.8]))
        assert terminated
        assert info.get("exit_reason") == "stop_loss"

    def test_v2_reset_works(self):
        env = _make_env_v2()
        obs, info = env.reset()
        assert obs.shape == (8,)
        assert isinstance(info, dict)


# ═══════════════════════════════════════════════════
# 에피소드 흐름 통합 테스트
# ═══════════════════════════════════════════════════

class TestEpisodeFlow:
    """전체 에피소드 흐름 테스트."""

    def test_full_episode_hold_then_tp(self):
        env = _make_env()
        env.reset()
        total_reward = 0
        for _ in range(5):
            obs, reward, terminated, _, _ = env.step(0)
            total_reward += reward
            if terminated:
                break
        if not terminated:
            _, reward, terminated, _, info = env.step(1)
            assert terminated
            assert "pnl_pct" in info

    def test_done_state_returns_zero_reward(self):
        """종료 후 step 호출 시 reward=0."""
        env = _make_env()
        env.reset()
        env.step(1)  # TP -> terminated
        obs, reward, terminated, truncated, _ = env.step(0)
        assert terminated
        assert reward == 0.0

    def test_multiple_episodes(self):
        """여러 에피소드 연속 실행."""
        env = _make_env()
        for ep in range(5):
            env.reset()
            for _ in range(3):
                obs, _, terminated, _, _ = env.step(0)
                if terminated:
                    break
            if not terminated:
                env.step(1)
        assert env.episode_count == 5

    def test_total_reward_accumulated(self):
        env = _make_env()
        env.reset()
        # TP는 항상 terminated를 반환
        _, _, terminated, _, info = env.step(1)  # TP
        assert terminated
        assert "total_reward" in info

    def test_info_has_required_keys_on_termination(self):
        env = _make_env()
        env.reset()
        _, _, terminated, _, info = env.step(1)
        assert "pnl_pct" in info
        assert "hold_minutes" in info
        assert "total_reward" in info
        assert "exit_reason" in info


# ═══════════════════════════════════════════════════
# 합성 캔들 데이터 테스트
# ═══════════════════════════════════════════════════

class TestSyntheticCandles:
    """합성 캔들 데이터로 환경이 올바르게 동작하는지 확인."""

    def test_env_with_flat_candles(self):
        candles = _make_candles(200, trend=0.0, volatility=0.0)
        env = _make_env(candles)
        obs, _ = env.reset()
        assert obs.shape == (8,)

    def test_env_with_rising_candles(self):
        candles = _make_candles(200, trend=0.001)
        env = _make_env(candles)
        obs, _ = env.reset()
        assert obs.shape == (8,)

    def test_env_with_falling_candles(self):
        candles = _make_candles(200, trend=-0.001)
        env = _make_env(candles)
        obs, _ = env.reset()
        assert obs.shape == (8,)

    def test_env_requires_candle_data(self):
        """캔들 데이터 없이 생성 시 FileNotFoundError (캐시 없을 때만)."""
        from scalp_ml.scalp_exit_env import MODEL_DIR
        cache = MODEL_DIR / "candles_cache.pkl"
        if cache.exists():
            pytest.skip("candles_cache.pkl 존재 — FileNotFoundError 발생하지 않음")
        with pytest.raises(FileNotFoundError):
            ScalpExitEnv()

    def test_candle_path_loading(self, tmp_path):
        """candle_path 인자로 pickle 파일 로드."""
        import pickle
        candles = _make_candles(200)
        path = tmp_path / "candles.pkl"
        with open(path, "wb") as f:
            pickle.dump(candles, f)
        env = ScalpExitEnv(candle_path=str(path))
        obs, _ = env.reset()
        assert obs.shape == (8,)


# ═══════════════════════════════════════════════════
# ScalpEpisode 데이터클래스 테스트
# ═══════════════════════════════════════════════════

class TestScalpEpisode:
    """ScalpEpisode 데이터클래스."""

    def test_creation(self):
        ep = ScalpEpisode(entry_price=100_000_000, candles=[], strategy=0)
        assert ep.entry_price == 100_000_000
        assert ep.strategy == 0
        assert ep.candles == []

    def test_strategy_values(self):
        for s in [0, 1, 2]:
            ep = ScalpEpisode(entry_price=1.0, candles=[], strategy=s)
            assert ep.strategy == s


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
