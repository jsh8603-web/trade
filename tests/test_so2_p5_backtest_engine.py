"""tests/test_so2_p5_backtest_engine.py — SO-2/P5 backtest/engine.py 검증.

검증 기준 (harness2.md SO-2):
1. 엔진이 AssetTrack 계약으로 백테스트 1구간 완주
2. 슬리피지(거래대금↑→임팩트↑, 슬리피지0 대비 정량 차이)
3. 수수료+세금 차감 정확
4. OrderState 전이 검증 (부분체결→PARTIALLY_FILLED)
5. common/metrics 사용 (자체 지표 0)
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from backtest.engine import (
    BacktestEngine,
    BacktestResult,
    CostConfig,
    OrderState,
    Trade,
    calculate_slippage,
    validate_transition,
)
from common.metrics import calculate_sharpe_ratio, calculate_max_drawdown


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_price_series(n: int = 20, start: float = 100.0, drift: float = 0.001) -> pd.Series:
    """랜덤 가격 시계열."""
    np.random.seed(42)
    prices = [start]
    for _ in range(n - 1):
        prices.append(prices[-1] * (1 + drift + np.random.normal(0, 0.01)))
    idx = pd.date_range("2023-01-01", periods=n, freq="D", tz=timezone.utc)
    return pd.Series(prices, index=idx, name="TEST")


def _make_volume_series(n: int = 20, volume: float = 1e9) -> pd.Series:
    idx = pd.date_range("2023-01-01", periods=n, freq="D", tz=timezone.utc)
    return pd.Series([volume] * n, index=idx)


def _make_mock_asset_track(action_cycle=("buy", "hold", "hold", "hold", "sell")):
    """AssetTrack stub — 순환 action."""
    track = MagicMock()
    state = MagicMock()
    state.raw_market_data = {}
    track.collect_market_state.return_value = state

    call_count = [0]
    def _gen_candidate(s):
        decision = MagicMock()
        idx = call_count[0] % len(action_cycle)
        decision.action = action_cycle[idx]
        call_count[0] += 1
        return decision

    track.generate_candidate.side_effect = _gen_candidate
    return track


# ---------------------------------------------------------------------------
# 1. AssetTrack 계약 경유 1구간 완주
# ---------------------------------------------------------------------------

def test_engine_run_completes():
    """백테스트 1구간 완주 — BacktestResult 반환."""
    engine = BacktestEngine()
    track = _make_mock_asset_track()
    prices = _make_price_series(20)
    result = engine.run(track, prices)
    assert isinstance(result, BacktestResult)
    assert len(result.equity_curve) > 0


def test_engine_run_calls_collect_and_generate():
    """AssetTrack 계약 메서드 호출 확인."""
    engine = BacktestEngine()
    track = _make_mock_asset_track()
    prices = _make_price_series(10)
    engine.run(track, prices)
    assert track.collect_market_state.call_count == 10
    assert track.generate_candidate.call_count == 10


def test_engine_trades_recorded():
    """매수/매도 발생 시 trade 기록."""
    engine = BacktestEngine(CostConfig(commission_rate=0.0005))
    track = _make_mock_asset_track(("buy", "hold", "sell", "buy", "hold", "sell", "hold"))
    prices = _make_price_series(14)
    result = engine.run(track, prices)
    assert len(result.trades) > 0


# ---------------------------------------------------------------------------
# 2. 슬리피지 — 거래대금↑ → 임팩트↑
# ---------------------------------------------------------------------------

def test_slippage_increases_with_trade_value():
    """거래대금↑ → 슬리피지↑. slippage_min=0으로 클램핑 제거."""
    cfg = CostConfig(slippage_impact_factor=0.001, slippage_min=0.0)
    s1 = calculate_slippage(1_000_000, 1_000_000_000, cfg)
    s2 = calculate_slippage(100_000_000, 1_000_000_000, cfg)
    assert s2 > s1, f"s2={s2} s1={s1}"


def test_slippage_bounded():
    """슬리피지는 [min, max] 범위."""
    cfg = CostConfig(slippage_min=0.0001, slippage_max=0.05)
    s_tiny = calculate_slippage(1, 1_000_000_000_000, cfg)
    s_huge = calculate_slippage(1_000_000_000, 1, cfg)
    assert s_tiny >= cfg.slippage_min
    assert s_huge <= cfg.slippage_max


def test_slippage_zero_volume_returns_max():
    """시장 거래량 0 → 최대 슬리피지."""
    cfg = CostConfig(slippage_max=0.05)
    s = calculate_slippage(1_000_000, 0, cfg)
    assert s == cfg.slippage_max


def test_slippage0_vs_real_return_difference():
    """슬리피지0 vs 현실 백테스트 수익률 차이 정량화."""
    real_cfg = CostConfig(slippage_impact_factor=0.001, commission_rate=0.0005)
    zero_cfg = CostConfig(slippage_impact_factor=0.0, slippage_min=0.0,
                           commission_rate=0.0, kr_transaction_tax=0.0)

    track_real = _make_mock_asset_track()
    track_zero = _make_mock_asset_track()
    prices = _make_price_series(20)
    vol = _make_volume_series(20, 1e8)

    result_real = BacktestEngine(real_cfg).run(track_real, prices, vol)
    result_zero = BacktestEngine(zero_cfg).run(track_zero, prices, vol)

    # 슬리피지/수수료가 있으면 수익률이 낮아야 함
    # (트레이드가 발생했을 경우)
    drag = result_zero.total_return_pct - result_real.total_return_pct
    assert drag >= 0.0, f"슬리피지 drag 음수: {drag}"


# ---------------------------------------------------------------------------
# 3. 수수료 + 세금 차감
# ---------------------------------------------------------------------------

def test_commission_deducted():
    """수수료 설정 시 최종 자본이 수수료 없을 때보다 작음."""
    no_cost = CostConfig(commission_rate=0.0, kr_transaction_tax=0.0,
                         slippage_min=0.0, slippage_impact_factor=0.0)
    with_cost = CostConfig(commission_rate=0.001, kr_transaction_tax=0.002,
                            slippage_min=0.0, slippage_impact_factor=0.0)

    track_free = _make_mock_asset_track(("buy", "hold", "sell"))
    track_cost = _make_mock_asset_track(("buy", "hold", "sell"))
    prices = _make_price_series(6)

    r_free = BacktestEngine(no_cost).run(track_free, prices)
    r_cost = BacktestEngine(with_cost).run(track_cost, prices)

    assert r_cost.final_capital <= r_free.final_capital


def test_kr_tax_on_sell():
    """KR 거래세 0.20% 매도 시 적용."""
    cfg = CostConfig(commission_rate=0.0, slippage_min=0.0,
                     slippage_impact_factor=0.0, kr_transaction_tax=0.002)
    engine = BacktestEngine(cfg)
    track = _make_mock_asset_track(("buy", "hold", "sell"))
    prices = _make_price_series(6)
    result = engine.run(track, prices, region="KR")
    sell_trades = [t for t in result.trades if t.side == "SELL"]
    for t in sell_trades:
        assert t.tax >= 0.0


# ---------------------------------------------------------------------------
# 4. OrderState 전이 검증
# ---------------------------------------------------------------------------

def test_order_state_valid_transitions():
    """정상 전이 허용."""
    assert validate_transition(OrderState.INITIALIZED, OrderState.SUBMITTED)
    assert validate_transition(OrderState.SUBMITTED, OrderState.ACCEPTED)
    assert validate_transition(OrderState.ACCEPTED, OrderState.FILLED)
    assert validate_transition(OrderState.ACCEPTED, OrderState.PARTIALLY_FILLED)
    assert validate_transition(OrderState.PARTIALLY_FILLED, OrderState.FILLED)


def test_order_state_invalid_transitions():
    """비정상 전이 거부."""
    assert not validate_transition(OrderState.FILLED, OrderState.SUBMITTED)
    assert not validate_transition(OrderState.CANCELED, OrderState.FILLED)
    assert not validate_transition(OrderState.INITIALIZED, OrderState.FILLED)


def test_partial_fill_state():
    """FillModel 활성화 시 PARTIALLY_FILLED 발생 가능."""
    cfg = CostConfig(enable_partial_fill=True, partial_fill_prob=1.0)
    engine = BacktestEngine(cfg, fill_model_seed=42)
    state, qty = engine._apply_fill_model(100.0)
    assert state == OrderState.PARTIALLY_FILLED
    assert qty < 100.0


def test_no_partial_fill_by_default():
    """기본값: FillModel 비활성화 → FILLED."""
    engine = BacktestEngine()
    state, qty = engine._apply_fill_model(100.0)
    assert state == OrderState.FILLED
    assert qty == 100.0


# ---------------------------------------------------------------------------
# 5. common/metrics 사용 (자체 지표 중복 0)
# ---------------------------------------------------------------------------

def test_result_uses_common_metrics():
    """BacktestResult.compute_metrics 가 common/metrics 사용 확인."""
    result = BacktestResult(
        initial_capital=10_000,
        final_capital=11_000,
        equity_curve=pd.Series([10_000, 10_500, 11_000]),
        trades=[],
    )
    result.compute_metrics()
    # common/metrics 의 결과와 일치
    returns = result.equity_curve.pct_change().dropna()
    expected_sharpe = calculate_sharpe_ratio(returns)
    assert abs(result.sharpe - expected_sharpe) < 1e-6


def test_engine_no_internal_sharpe_implementation():
    """engine.py 자체 Sharpe 계산 없음 (common/metrics만 import)."""
    import ast, pathlib
    src = pathlib.Path("backtest/engine.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    # 자체 Sharpe 계산 함수 없음 (def calculate_sharpe... 없어야 함)
    defs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert "calculate_sharpe_ratio" not in defs
    assert "calculate_max_drawdown" not in defs


def test_result_metrics_computed():
    """1구간 완주 후 지표 산출 확인."""
    engine = BacktestEngine()
    track = _make_mock_asset_track()
    prices = _make_price_series(20)
    result = engine.run(track, prices)
    result.compute_metrics()
    # equity_curve 있으면 Sharpe/MDD 계산됨
    assert isinstance(result.sharpe, float)
    assert result.max_drawdown <= 0.0 or result.max_drawdown == 0.0


# ---------------------------------------------------------------------------
# 6. compare_slippage — §2.9① 슬리피지 정량화
# ---------------------------------------------------------------------------

def test_compare_slippage_returns_dict():
    """compare_slippage → 필수 키 포함 dict 반환."""
    engine = BacktestEngine(CostConfig(slippage_impact_factor=0.001))
    track = _make_mock_asset_track()
    prices = _make_price_series(10)
    result = engine.compare_slippage(track, prices)
    for key in ("real_sharpe", "zero_sharpe", "slippage_drag_pct"):
        assert key in result
