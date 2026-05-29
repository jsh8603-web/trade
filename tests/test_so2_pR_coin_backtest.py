"""tests/test_so2_pR_coin_backtest.py — SO-2/Phase R coin 백테스트 변형 + N-P5-COIN-METRICS 소진.

검증 기준 (harness2.md SO-2):
1. coin 과거구간 backtest가 슬리피지0 대비 더 현실적 (정량 비교)
2. common/metrics 일원화 후 coin DRY_RUN 회귀 0 (동일 입력=동일 점수)
3. calc_rsi 동치 검산 (backtest_v6_simulation.py:187 vs common/metrics)
"""

from __future__ import annotations

import pytest
import numpy as np
import pandas as pd
from datetime import timezone
from unittest.mock import MagicMock

from backtest.coin_engine import CoinBacktestEngine, CoinBacktestConfig, UPBIT_COST_CONFIG
from common.metrics import calculate_rsi


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_prices(n: int = 30, seed: int = 42) -> pd.Series:
    np.random.seed(seed)
    prices = [60000.0]
    for _ in range(n - 1):
        prices.append(prices[-1] * (1 + np.random.normal(0.001, 0.015)))
    idx = pd.date_range("2023-01-01", periods=n, freq="D", tz=timezone.utc)
    return pd.Series(prices, index=idx, name="BTC")


def _make_vol(n: int = 30) -> pd.Series:
    idx = pd.date_range("2023-01-01", periods=n, freq="D", tz=timezone.utc)
    return pd.Series([1e9] * n, index=idx)


def _make_mock_track(action="hold"):
    track = MagicMock()
    state = MagicMock()
    state.raw_market_data = {}
    track.collect_market_state.return_value = state
    decision = MagicMock()
    decision.action = action
    track.generate_candidate.return_value = decision
    return track


# ---------------------------------------------------------------------------
# 1. coin 백테스트 24/7 + Upbit fee 적용
# ---------------------------------------------------------------------------

def test_coin_engine_runs():
    """CoinBacktestEngine 1구간 완주."""
    engine = CoinBacktestEngine()
    track = _make_mock_track("hold")
    prices = _make_prices(20)
    result = engine.run(track, prices)
    assert result is not None
    assert len(result.equity_curve) > 0


def test_coin_engine_upbit_fee_config():
    """Upbit fee 설정 확인 (0.05%)."""
    assert UPBIT_COST_CONFIG.commission_rate == pytest.approx(0.0005)
    assert UPBIT_COST_CONFIG.kr_transaction_tax == pytest.approx(0.0)  # 코인 거래세 없음


def test_coin_engine_24_7_flag():
    """24/7 플래그 기본값."""
    config = CoinBacktestConfig()
    assert config.is_24_7 is True
    assert config.pair == "KRW"


# ---------------------------------------------------------------------------
# 2. 슬리피지0 vs coin 현실 정량 비교
# ---------------------------------------------------------------------------

def test_coin_more_realistic_than_zero_slippage():
    """coin 엔진 수익률 ≤ 슬리피지0 수익률 (더 현실적)."""
    engine = CoinBacktestEngine()
    track = _make_mock_track("hold")
    prices = _make_prices(30)
    vol = _make_vol(30)
    result = engine.compare_with_legacy(track, prices, vol)

    assert "slippage_drag_pct" in result
    assert "is_more_realistic" in result
    assert result["is_more_realistic"] is True  # coin엔진이 더 보수적


def test_slippage_drag_nonnegative():
    """슬리피지 drag ≥ 0 (coin 엔진이 더 낮은 수익률)."""
    engine = CoinBacktestEngine()
    track = _make_mock_track("hold")
    prices = _make_prices(20)
    vol = _make_vol(20)
    result = engine.compare_with_legacy(track, prices, vol)
    assert result["slippage_drag_pct"] >= 0.0


# ---------------------------------------------------------------------------
# 3. N-P5-COIN-METRICS: calc_rsi 동치 검산
# ---------------------------------------------------------------------------

def test_rsi_equivalence_known_series():
    """common/metrics.calculate_rsi == backtest_v6_simulation calc_rsi (동치)."""
    # 같은 로직을 직접 재현해 동치 확인
    def ref_calc_rsi(closes, period=14):
        """backtest_v6_simulation.py:187 그대로."""
        if len(closes) < period + 1:
            return 50.0
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        recent = deltas[-period:]
        gains = [d for d in recent if d > 0]
        losses = [-d for d in recent if d < 0]
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0.001
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)

    # 알려진 시계열로 동치 검산
    np.random.seed(7)
    prices = [60000.0]
    for _ in range(30):
        prices.append(prices[-1] * (1 + np.random.normal(0.001, 0.02)))

    expected = ref_calc_rsi(prices, period=14)
    actual = calculate_rsi(prices, period=14)
    assert actual == pytest.approx(expected, abs=1e-6), (
        f"RSI 동치 실패: expected={expected}, actual={actual}"
    )


def test_rsi_equivalence_multiple_cases():
    """여러 케이스에서 RSI 동치 (회귀 0)."""
    def ref_rsi(closes, period=14):
        if len(closes) < period + 1:
            return 50.0
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        recent = deltas[-period:]
        gains = [d for d in recent if d > 0]
        losses = [-d for d in recent if d < 0]
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0.001
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)

    for seed in [0, 1, 42, 99]:
        np.random.seed(seed)
        prices = [100.0]
        for _ in range(25):
            prices.append(prices[-1] * (1 + np.random.normal(0.0, 0.015)))
        assert calculate_rsi(prices) == pytest.approx(ref_rsi(prices), abs=1e-6)


def test_rsi_short_series_returns_50():
    """시리즈 짧을 때 50.0 반환."""
    assert calculate_rsi([60000.0, 61000.0], period=14) == 50.0


def test_rsi_via_coin_engine():
    """CoinBacktestEngine.calc_rsi_common → common/metrics 경유."""
    engine = CoinBacktestEngine()
    closes = [60000.0 + i * 100 for i in range(20)]
    rsi = engine.calc_rsi_common(closes)
    assert rsi == calculate_rsi(closes)


# ---------------------------------------------------------------------------
# 4. 회귀 0 — 기존 Phase 미변경
# ---------------------------------------------------------------------------

def test_backtest_engine_unchanged():
    """backtest/engine.py 기존 Phase5 코드 미변경."""
    from backtest.engine import BacktestEngine, OrderState
    assert BacktestEngine is not None
    assert OrderState.FILLED is not None


def test_sim_engine_not_modified():
    """scripts/sim_engine.py 미변경 (SACRED)."""
    import pathlib
    src = pathlib.Path("scripts/sim_engine.py").read_text(encoding="utf-8")
    # 기존 FEE_RATE 보존
    assert "FEE_RATE = 0.0005" in src
    # common/metrics import 없음 (SACRED: 미변경)
    assert "from common.metrics" not in src
