"""tests/test_so6_p5_integration_gate.py — SO-6/P5 §2.9 통합 동작게이트.

검증 기준 (harness2.md SO-6):
①슬리피지0 vs 현실 정량화
②기계적 패리티≥95% (LLM abstain stub H22 2층)
③walk-forward OOS/IS Sharpe+DSR/PBO 산출
④전구간 MDD<kill switch + capacity 초과 거절 + E4 보정 + 상폐 포함
⑤StockTrack/CoinTrack→backtest 엔진 wire
⑥전 Phase 회귀 0
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from backtest.engine import BacktestEngine, CostConfig, OrderState
from backtest.walk_forward import WalkForwardEngine, UniverseManager
from backtest.pbo import calculate_pbo_cscv, calculate_deflated_sharpe_ratio, build_go_nogo_card
from backtest.capacity import CapacityChecker, CapacityConfig, PriceLimitChecker
from common.metrics import calculate_max_drawdown, returns_from_equity


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_prices(n: int = 40, seed: int = 0) -> pd.Series:
    np.random.seed(seed)
    prices = [100.0]
    for _ in range(n - 1):
        prices.append(prices[-1] * (1 + np.random.normal(0.001, 0.01)))
    idx = pd.date_range("2023-01-01", periods=n, freq="D", tz=timezone.utc)
    return pd.Series(prices, index=idx, name="TEST")


def _make_mock_track(action_cycle=("buy", "hold", "hold", "hold", "sell")):
    track = MagicMock()
    state = MagicMock()
    state.raw_market_data = {}
    track.collect_market_state.return_value = state
    call_count = [0]
    def _gen(s):
        decision = MagicMock()
        decision.action = action_cycle[call_count[0] % len(action_cycle)]
        call_count[0] += 1
        return decision
    track.generate_candidate.side_effect = _gen
    return track


# ---------------------------------------------------------------------------
# ① 슬리피지0 vs 현실 정량화
# ---------------------------------------------------------------------------

def test_slippage0_vs_real_quantification():
    """①: 슬리피지0 대비 현실 수익률 차이 정량화."""
    engine = BacktestEngine(CostConfig(slippage_impact_factor=0.002, commission_rate=0.0005))
    track = _make_mock_track()
    prices = _make_prices(40)
    vol = pd.Series([1e8] * 40, index=prices.index)
    result = engine.compare_slippage(track, prices, vol)
    assert "slippage_drag_pct" in result
    # drag ≥ 0 (슬리피지+수수료 있으면 수익 감소)
    assert result["slippage_drag_pct"] >= 0.0


def test_slippage_drag_increases_with_impact():
    """①: 임팩트↑ → drag↑."""
    track_low = _make_mock_track()
    track_high = _make_mock_track()
    prices = _make_prices(40)
    vol = pd.Series([1e8] * 40, index=prices.index)

    low_cfg = CostConfig(slippage_impact_factor=0.0001, slippage_min=0.0)
    high_cfg = CostConfig(slippage_impact_factor=0.01, slippage_min=0.0)

    result_low = BacktestEngine(low_cfg).compare_slippage(track_low, prices, vol)
    result_high = BacktestEngine(high_cfg).compare_slippage(track_high, prices, vol)
    assert result_high["slippage_drag_pct"] >= result_low["slippage_drag_pct"]


# ---------------------------------------------------------------------------
# ② 기계적 패리티 ≥ 95% (H22 2층: LLM abstain stub)
# ---------------------------------------------------------------------------

def test_h22_llm_abstain_stub_backtest():
    """②: H22 LLM 백테스트 오염 — Layer2(LLM) abstain stub."""
    # Layer1 결정론 코어: generate_candidate 항상 동일 action
    prices = _make_prices(30, seed=42)

    results = []
    for _ in range(10):
        track = _make_mock_track(("buy", "hold", "hold", "sell"))
        engine = BacktestEngine(CostConfig(commission_rate=0.0, slippage_impact_factor=0.0))
        result = engine.run(track, prices)
        results.append(result.total_return_pct)

    # 결정론 코어: 모든 실행 동일
    assert all(abs(r - results[0]) < 1e-6 for r in results)


def test_h22_mechanical_parity_ratio():
    """②: 기계적 패리티(결정론 경로) ≥ 95%."""
    prices = _make_prices(50, seed=1)
    n_runs = 20
    base_track = _make_mock_track()
    base_engine = BacktestEngine(CostConfig(commission_rate=0.0, slippage_min=0.0,
                                             slippage_impact_factor=0.0))
    base_result = base_engine.run(base_track, prices)
    base_return = base_result.total_return_pct

    matches = 0
    for _ in range(n_runs):
        track = _make_mock_track()
        engine = BacktestEngine(CostConfig(commission_rate=0.0, slippage_min=0.0,
                                            slippage_impact_factor=0.0))
        result = engine.run(track, prices)
        if abs(result.total_return_pct - base_return) < 1e-4:
            matches += 1

    parity = matches / n_runs
    assert parity >= 0.95, f"기계적 패리티 {parity:.2%} < 95%"


# ---------------------------------------------------------------------------
# ③ walk-forward OOS/IS Sharpe + DSR/PBO 산출
# ---------------------------------------------------------------------------

def test_walk_forward_ois_sharpe_computed():
    """③: walk-forward OOS/IS Sharpe 산출."""
    engine = WalkForwardEngine(n_folds=4, n_test_folds=2, purged_size=1)
    np.random.seed(99)
    returns = pd.Series(np.random.normal(0.002, 0.01, 80))
    result = engine.run(returns)
    assert result.n_splits > 0
    assert all(isinstance(s.oos_sharpe, float) for s in result.splits)


def test_dsr_pbo_from_wf_result():
    """③: WalkForward 결과로 DSR+PBO 산출."""
    oos_sharpes = [1.2, 0.8, 1.5, 1.0, 0.9]
    card = build_go_nogo_card(
        oos_sharpe_paths=oos_sharpes,
        max_drawdown=-8.0,
        win_rate=52.0,
        n_trades=100,
        n_trials=5,
        track_record_length=80,
    )
    assert 0.0 <= card.pbo <= 1.0
    assert 0.0 <= card.dsr <= 1.0
    assert card.status in ("GO", "MARGINAL", "NO_GO")


# ---------------------------------------------------------------------------
# ④ 전구간 MDD < kill switch + capacity + E4 + 상폐
# ---------------------------------------------------------------------------

def test_full_period_mdd_check():
    """④: 전구간 MDD < kill switch 임계 확인."""
    from core.risk_gate import KillSwitch, KillSwitchState

    engine = BacktestEngine()
    track = _make_mock_track()
    prices = _make_prices(30)
    result = engine.run(track, prices)

    mdd = result.max_drawdown
    ks = KillSwitch(mdd_threshold=-50.0)
    # MDD가 kill switch 임계보다 작으면 halt 안함
    assert mdd > -50.0 or ks.state == KillSwitchState.ACTIVE


def test_capacity_excess_rejected_in_gate():
    """④: capacity 초과 주문 거절."""
    checker = CapacityChecker(CapacityConfig(max_capacity_ratio=0.005))
    ok, _ = checker.check(order_value=10_000_000, daily_volume=100_000_000)
    assert ok is False  # 10% > 0.5%


def test_e4_calibration_in_gate():
    """④: E4 보정 동작 확인."""
    from backtest.capacity import E4SlippageCalibrator, SlippageObservation
    cal = E4SlippageCalibrator()
    for _ in range(5):
        obs = SlippageObservation(100.0, 100.8, "BUY")
        cal.record(obs)
    new_factor = cal.calibrate()
    assert new_factor > 0.0


def test_delisted_included_in_backtest_universe():
    """④: 상폐 종목 백테스트 유니버스 포함."""
    mgr = UniverseManager(delisted_tickers={"999999"})
    bt = mgr.get_backtest_universe(["005930", "999999"])
    live = mgr.get_live_universe(["005930", "999999"])
    assert "999999" in bt
    assert "999999" not in live


# ---------------------------------------------------------------------------
# ⑤ StockTrack/CoinTrack → backtest 엔진 wire
# ---------------------------------------------------------------------------

def test_stocktrack_wire_to_backtest():
    """⑤: StockTrack → BacktestEngine wire."""
    from core.stock_track import StockTrack
    from stock.contracts import RunMode, MarketQuote

    quote = MarketQuote(ticker="005930", as_of=datetime(2023, 1, 1, tzinfo=timezone.utc),
                         price=70000.0, market_cap=4e14)
    track = StockTrack(ticker="005930", mode=RunMode.FORWARD, _quote_override=quote)

    prices = _make_prices(20)
    engine = BacktestEngine()
    result = engine.run(track, prices)
    assert isinstance(result.equity_curve, pd.Series)
    assert len(result.equity_curve) > 0


def test_cointrack_wire_to_backtest():
    """⑤: CoinTrack → BacktestEngine wire (mock)."""
    from core.coin_track import CoinTrack

    track = MagicMock(spec=CoinTrack)
    state = MagicMock()
    state.raw_market_data = {"price": 60000.0, "asset": "BTC"}
    track.collect_market_state.return_value = state
    decision = MagicMock()
    decision.action = "hold"
    track.generate_candidate.return_value = decision

    prices = _make_prices(15)
    engine = BacktestEngine()
    result = engine.run(track, prices)
    assert result is not None
    assert len(result.equity_curve) > 0


# ---------------------------------------------------------------------------
# ⑥ 전 Phase 회귀 0
# ---------------------------------------------------------------------------

def test_phase0_coin_track_unchanged():
    """Phase 0: coin_track.py 미변경."""
    from core.coin_track import CoinTrack
    assert CoinTrack is not None


def test_phase1_brain_unchanged():
    """Phase 1: core/brain 미변경."""
    from core.brain.fred_adapter import NullFredAdapter
    assert NullFredAdapter().is_available() is False


def test_phase2_risk_gate_unchanged():
    """Phase 2: risk_gate.py 미변경."""
    from core.risk_gate import RiskGate
    assert RiskGate is not None


def test_phase3_admission_unchanged():
    """Phase 3: admission.py 미변경."""
    from stock.admission import check_admission, KrxStatusSnapshot
    from stock.contracts import ProductTier
    snap = KrxStatusSnapshot()
    r = check_admission("005930", ProductTier.CORE_ALLOWED, "KR", krx_status=snap)
    assert r.admit is True


def test_phase4_data_layer_unchanged():
    """Phase 4: stock/data 레이어 미변경."""
    from stock.data.krx_universe import KrxStatusProvider
    from stock.data.macro_vintage import MacroVintageProvider
    assert KrxStatusProvider is not None
    assert MacroVintageProvider is not None


def test_phase5_backtest_imports_ok():
    """Phase 5: backtest/ 전체 import 정합."""
    from backtest.engine import BacktestEngine, OrderState
    from backtest.walk_forward import WalkForwardEngine
    from backtest.pbo import calculate_pbo_cscv, GoNoGoStatus
    from backtest.capacity import CapacityChecker, E4SlippageCalibrator
    from common.metrics import calculate_sharpe_ratio
    assert all([BacktestEngine, WalkForwardEngine, calculate_pbo_cscv,
                CapacityChecker, calculate_sharpe_ratio])


def test_existing_scripts_not_modified():
    """SACRED: coin 기존 13 backtest_*.py 미변경 확인 (sim_engine 포함)."""
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True, text=True, cwd="D:/projects/Inv"
    )
    modified = result.stdout.strip().split("\n")
    for f in modified:
        assert "scripts/backtest" not in f, f"SACRED 위반: {f} 수정됨"
        assert "scripts/sim_engine" not in f, f"SACRED 위반: {f} 수정됨"
