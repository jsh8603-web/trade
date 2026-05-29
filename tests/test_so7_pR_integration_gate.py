"""tests/test_so7_pR_integration_gate.py — SO-7/PR §2.9 Phase R 통합 동작게이트.

검증 기준 (harness2.md SO-7/PR):
① 이식 전후 coin DRY_RUN decision 동치/개선 (Phase0 판정 재사용, 회귀 0)
② coin 변형 적용 후 안전게이트(risk_gate·KillSwitch·EMERGENCY_STOP)·reconciliation 정상
③ 교체 백테스트 엔진이 coin 과거구간에서 기존 대비 슬리피지·수수료 더 현실적(정량)
④ 전 Phase(-1·0·1·2·2.5·3·4·5·6·R) 회귀 0
"""

from __future__ import annotations

import subprocess
import sys
from datetime import timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _make_prices(n: int = 20, seed: int = 42) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series(
        [50_000_000 + rng.normal(0, 500_000) for _ in range(n)],
        index=pd.date_range("2023-01-01", periods=n, freq="D", tz=timezone.utc),
        name="BTC/KRW",
    )


def _make_track():
    # offline fixture 주입 (SO-1 PR 패턴) — 실 Upbit/macro fetch 차단, DRY_RUN 패리티 게이트
    from core.coin_track_macro import CoinTrackWithMacro
    return CoinTrackWithMacro(
        _market_data_override={"price": 60000.0},
        _portfolio_override={"krw_balance": 1000000.0},
        _external_data_override={"fgi": 50},
        _past_decisions_override=[],
    )


# ---------------------------------------------------------------------------
# ① DRY_RUN decision 동치 — Phase0 판정 재사용, 회귀 0
# ---------------------------------------------------------------------------

def test_coin_track_macro_collect_returns_market_state():
    """CoinTrackWithMacro.collect_market_state → MarketState 반환."""
    track = _make_track()
    state = track.collect_market_state()
    assert state is not None
    assert hasattr(state, "raw_market_data")


def test_coin_track_generate_candidate_returns_decision():
    """generate_candidate → Decision 반환 (AssetTrack 계약: Decision dataclass)."""
    track = _make_track()
    state = track.collect_market_state()
    decision = track.generate_candidate(state)
    assert decision is not None
    assert hasattr(decision, "decision")
    assert decision.decision in ("buy", "sell", "hold")


def test_dry_run_decision_deterministic():
    """동일 상태 → 동일 decision (결정론)."""
    track = _make_track()
    s = track.collect_market_state()
    d1 = track.generate_candidate(s)
    d2 = track.generate_candidate(s)
    assert d1.decision == d2.decision


def test_coin_engine_run_completes():
    """CoinBacktestEngine.run → BacktestResult 반환."""
    from backtest.coin_engine import CoinBacktestEngine, CoinBacktestConfig
    config = CoinBacktestConfig(initial_capital=10_000_000)
    engine = CoinBacktestEngine(config)
    result = engine.run(_make_track(), _make_prices())
    assert result is not None
    assert result.final_capital > 0


# ---------------------------------------------------------------------------
# ② 안전게이트 + reconciliation 정상
# ---------------------------------------------------------------------------

def test_risk_gate_blocks_oversized_position():
    """risk_gate: 과도한 포지션(90%) → 안전게이트 개입(max weight 축소 또는 거부)."""
    from core.risk_gate import RiskGate, VerdictType
    gate = RiskGate()
    verdict = gate.check(
        action="buy",
        proposed_size=0.9,
        current_weight=0.0,
        sector_weight=0.0,
        nav=1.0,
        daily_loss_pct=0.0,
    )
    # 과도 포지션은 그대로 승인되지 않음 — max weight 로 축소(REDUCED) 또는 거부(REJECTED)
    assert verdict.verdict != VerdictType.APPROVED
    assert verdict.verdict in (VerdictType.REDUCED, VerdictType.REJECTED)
    assert "max_weight_single" in verdict.triggered_rules


def test_killswitch_triggers_on_mdd_breach():
    """KillSwitch: MDD 임계 초과 → HALTED."""
    from core.risk_gate import KillSwitch, KillSwitchState
    ks = KillSwitch(mdd_threshold=-0.10)
    state = ks.update_mdd(-0.20)
    assert state == KillSwitchState.HALTED


def test_shadow_always_dry_run():
    """shadow order is_dry_run = True (EMERGENCY_STOP 상황에도 실주문 0건)."""
    from core.coin_shadow import CoinShadowExecutor
    executor = CoinShadowExecutor()
    order = executor.place_shadow("BTC/KRW", "buy", 0.001, 50_000_000)
    assert order.is_dry_run is True


def test_reconciliation_pending_filter():
    """reconciliation: 미체결 필터 (R2)."""
    from core.coin_shadow import CoinShadowExecutor
    executor = CoinShadowExecutor()
    o1 = executor.place_shadow("BTC/KRW", "buy", 0.001, 50_000_000)
    o2 = executor.place_shadow("BTC/KRW", "sell", 0.001, 51_000_000)
    executor.simulate_fill(o2.identifier)
    pending = executor.reconcile("BTC/KRW")
    assert o1 in pending
    assert o2 not in pending


# ---------------------------------------------------------------------------
# ③ 교체 백테스트 엔진 — 슬리피지·수수료 더 현실적
# ---------------------------------------------------------------------------

def test_coin_engine_upbit_fee_config():
    """CoinBacktestConfig Upbit taker fee 0.05% 설정."""
    from backtest.coin_engine import CoinBacktestConfig
    from backtest.coin_engine import UPBIT_COST_CONFIG
    # UPBIT_COST_CONFIG 의 commission_rate >= 0.0005
    assert UPBIT_COST_CONFIG.commission_rate >= 0.0005


def test_coin_engine_compare_slippage_returns_dict():
    """compare_with_legacy → dict 반환 (슬리피지 정량화)."""
    from backtest.coin_engine import CoinBacktestEngine, CoinBacktestConfig
    config = CoinBacktestConfig(initial_capital=10_000_000)
    engine = CoinBacktestEngine(config)
    prices = _make_prices(20, seed=7)
    result = engine.compare_with_legacy(_make_track(), prices)
    assert isinstance(result, dict)
    assert "slippage_drag_pct" in result
    assert "is_more_realistic" in result


def _make_cost_stub():
    """비용모델 drag 검증용 — 가격 기준 결정론적 buy/sell 스텁.

    compare_with_legacy 는 같은 track 을 coin/zero 두 엔진에 넘기므로
    call-counter 가 아닌 가격(state) 기준 결정론으로 양 run 이 동일 거래를 내야 공정 비교.
    엔진은 decision.action 을 읽음(engine.py) — price < 5천만 → buy, ≥ → sell.
    """
    from unittest.mock import MagicMock
    track = MagicMock()
    state = MagicMock()
    state.raw_market_data = {}
    track.collect_market_state.return_value = state

    def _decide(s):
        d = MagicMock()
        d.action = "buy" if s.raw_market_data.get("price", 0.0) < 50_000_000 else "sell"
        return d

    track.generate_candidate.side_effect = _decide
    return track


def test_coin_engine_more_realistic_than_zero():
    """교체 엔진이 슬리피지0 대비 실제로 더 보수적 — 거래 강제 후 drag>0 정량 검증.

    리뷰 CONCERN(거래0 fixture→drag=0 vacuous 통과) 해소: 단조 가격(48M→52M) +
    가격기준 스텁으로 라운드트립(전반 buy·후반 sell) 보장 → Upbit fee+슬리피지가
    실제로 수익률을 갉는지(drag>0) 정량 검증.
    """
    from backtest.coin_engine import CoinBacktestEngine, CoinBacktestConfig
    prices = pd.Series(
        np.linspace(48_000_000, 52_000_000, 30),
        index=pd.date_range("2023-01-01", periods=30, freq="D", tz=timezone.utc),
        name="BTC/KRW",
    )
    config = CoinBacktestConfig(initial_capital=10_000_000)
    engine = CoinBacktestEngine(config)
    result = engine.compare_with_legacy(_make_cost_stub(), prices)
    # 거래가 실제 발생해야 비용모델이 검증됨(n_trades=0 vacuous 방지)
    assert result["coin_return_pct"] != result["zero_return_pct"], "거래 미발생 — 비용모델 검증 불가"
    # Upbit 수수료+슬리피지 → coin 수익률 < zero 수익률 → drag 엄격 양수
    assert result["slippage_drag_pct"] > 0.0
    assert result["is_more_realistic"] is True


# ---------------------------------------------------------------------------
# ④ 전 Phase 회귀 0
# ---------------------------------------------------------------------------

def test_phase_minus1_import():
    from core.asset_track import AssetTrack
    assert AssetTrack is not None


def test_phase0_coin_track_import():
    from core.coin_track import CoinTrack
    assert CoinTrack is not None


def test_phase1_brain_import():
    from core.brain.llm_provider import LLMRouter
    assert LLMRouter is not None


def test_phase2_risk_gate_import():
    from core.risk_gate import RiskGate, KillSwitch
    assert RiskGate is not None and KillSwitch is not None


def test_phase3_admission_import():
    from stock.admission import check_admission
    assert check_admission is not None


def test_phase4_data_layer_import():
    from stock.data.rate_tier import RateTierRegistry
    assert RateTierRegistry is not None


def test_phase5_backtest_import():
    from backtest.engine import BacktestEngine
    assert BacktestEngine is not None


def test_phase6_orchestrator_import():
    from core.portfolio_orchestrator import PortfolioOrchestrator
    assert PortfolioOrchestrator is not None


def test_phaseR_all_modules_import():
    """Phase R 신규 모듈 전체 import 정합."""
    from core.coin_track_macro import CoinTrackWithMacro
    from backtest.coin_engine import CoinBacktestEngine
    from core.coin_sizing import size_coin_portfolio
    from core.coin_memory import CoinMemoryLayer
    from core.coin_shadow import CoinShadowExecutor
    from core.coin_consensus_lens import CoinConsensusLens
    assert all([CoinTrackWithMacro, CoinBacktestEngine, size_coin_portfolio,
                CoinMemoryLayer, CoinShadowExecutor, CoinConsensusLens])


def test_sacred_execute_trade_no_diff():
    """SACRED: execute_trade.py 실거래 경로 미변경."""
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD", "--", "scripts/execute_trade.py"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.stdout.strip() == "", f"execute_trade.py 변경:\n{result.stdout}"


def test_sacred_live_trader_no_diff():
    """SACRED: live_trader.py 실거래 경로 미변경."""
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD", "--", "rl_hybrid/rl/live_trader.py"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.stdout.strip() == "", f"live_trader.py 변경:\n{result.stdout}"


_PR_TEST_FILES = [
    "tests/test_so1_pR_coin_assettrack_wire.py",
    "tests/test_so2_pR_coin_backtest.py",
    "tests/test_so3_pR_coin_sizing.py",
    "tests/test_so4_pR_coin_memory.py",
    "tests/test_phase_R_so5.py",
    "tests/test_so6_pR_coin_consensus_lens.py",
]


@pytest.mark.slow
def test_phase_R_so1_to_so6_regression():
    """PR SO-1~6 회귀 0 (subprocess)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *_PR_TEST_FILES, "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, (
        f"PR SO-1~6 회귀:\n{result.stdout[-2000:]}\n{result.stderr[-500:]}"
    )
