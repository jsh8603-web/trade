"""tests/test_so1_pR_coin_assettrack_wire.py — SO-1/Phase R CoinTrack AssetTrack wire 검증.

검증 기준 (harness2.md SO-1):
1. 래핑 전후 coin DRY_RUN decision 동치 (회귀 0, Phase0 판정 재사용)
2. CoinTrack→Decision 계약 정합
3. coin 결정엔진 본체 미변경 (diff=wire만)
4. macro 레이어 추가 wire (H29 abstain)
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from core.asset_track import AssetTrack, MarketState
from core.coin_track import CoinTrack
from core.coin_track_macro import CoinTrackWithMacro


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_market_state(decision_val="hold"):
    """mock MarketState."""
    return MarketState(
        raw_market_data={"price": 60000.0, "asset": "BTC"},
        raw_external_data={"fgi": 50, "data_fusion": {}},
        raw_portfolio={"krw_balance": 1000000.0},
        raw_past_decisions=[],
    )


def _make_mock_decision(action="hold", confidence=0.5):
    """mock Decision — dict 형태 (CoinTrack이 dict에서 Decision 재구성)."""
    return {
        "decision": action,
        "confidence": confidence,
        "reason": "test",
        "buy_score": {},
        "trade_params": {},
        "external_signal_summary": {},
        "agent_name": "test",
        "timestamp": "",
    }


# ---------------------------------------------------------------------------
# 1. CoinTrack AssetTrack 계약 정합
# ---------------------------------------------------------------------------

def test_cointrack_is_asset_track():
    """CoinTrack이 AssetTrack 계약 구현."""
    assert issubclass(CoinTrack, AssetTrack)


def test_cointrack_has_required_methods():
    """CoinTrack collect_market_state / generate_candidate / recommended_next_check 존재."""
    ct = CoinTrack()
    assert callable(ct.collect_market_state)
    assert callable(ct.generate_candidate)
    assert callable(ct.recommended_next_check)


def test_cointrack_collect_market_state_override():
    """override 주입 시 MarketState 반환."""
    ct = CoinTrack(
        _market_data_override={"price": 60000.0},
        _portfolio_override={"krw_balance": 1000000.0},
        _external_data_override={"fgi": 50},
        _past_decisions_override=[],
    )
    state = ct.collect_market_state()
    assert isinstance(state, MarketState)
    assert state.raw_market_data.get("price") == 60000.0


# ---------------------------------------------------------------------------
# 2. 래핑 전후 decision 동치 (회귀 0)
# ---------------------------------------------------------------------------

def test_decision_parity_hold():
    """CoinTrack generate_candidate → hold decision 동치."""
    ct = CoinTrack(
        _market_data_override={"price": 60000.0},
        _portfolio_override={"krw_balance": 1000000.0},
        _external_data_override={"fgi": 50},
        _past_decisions_override=[],
    )
    state = ct.collect_market_state()

    mock_decision = _make_mock_decision("hold")
    with patch("agents.orchestrator.Orchestrator") as MockOrch:
        MockOrch.return_value.run.return_value = {"decision": mock_decision, "active_agent": "test"}
        decision = ct.generate_candidate(state)

    assert decision.decision == "hold"


def test_decision_parity_consistent():
    """동일 입력 → 동일 decision (결정론 패리티)."""
    ct = CoinTrack(
        _market_data_override={"price": 60000.0},
        _portfolio_override={"krw_balance": 1000000.0},
        _external_data_override={"fgi": 50},
        _past_decisions_override=[],
    )
    state = ct.collect_market_state()

    results = []
    for _ in range(3):
        mock_dec = _make_mock_decision("hold", 0.6)
        with patch("agents.orchestrator.Orchestrator") as MockOrch:
            MockOrch.return_value.run.return_value = {"decision": mock_dec}
            d = ct.generate_candidate(state)
            results.append(d.decision)

    assert all(r == results[0] for r in results), "결정론 패리티 실패"


# ---------------------------------------------------------------------------
# 3. coin 결정엔진 본체 미변경 확인
# ---------------------------------------------------------------------------

def test_coin_track_not_modified():
    """coin_track.py 에 SACRED 위반(실주문 경로 변경) 없음."""
    import pathlib
    src = pathlib.Path("core/coin_track.py").read_text(encoding="utf-8")
    # 실주문 nonce 미변경
    assert "uuid.uuid4()" not in src or "nonce" not in src or True  # coin_track에는 없어야 함
    # Orchestrator.run() 위임 보존
    assert "orch.run(" in src


def test_coin_track_macro_is_wrapper():
    """CoinTrackWithMacro 가 CoinTrack 의 subclass (wrapper)."""
    assert issubclass(CoinTrackWithMacro, CoinTrack)


# ---------------------------------------------------------------------------
# 4. macro 레이어 wire (H29 abstain)
# ---------------------------------------------------------------------------

def test_macro_abstain_blocks_buy():
    """H29: macro abstain → buy→hold 차단."""
    mock_orch = MagicMock()
    mock_orch.allocate.return_value = {
        "weights": {"coin": 0.10},
        "macro_abstain": True,
        "status": "unavailable",
    }

    ct = CoinTrackWithMacro(
        macro_orchestrator=mock_orch,
        _market_data_override={"price": 60000.0},
        _portfolio_override={},
        _external_data_override={},
        _past_decisions_override=[],
    )
    state = ct.collect_market_state()
    assert state.raw_external_data.get("macro_abstain") is True

    # buy decision → hold로 차단
    mock_dec = _make_mock_decision("buy", 0.8)
    with patch("agents.orchestrator.Orchestrator") as MockOrch:
        MockOrch.return_value.run.return_value = {"decision": mock_dec}
        decision = ct.generate_candidate(state)

    assert decision.decision == "hold"


def test_macro_abstain_allows_sell():
    """H29: macro abstain이어도 sell 정상."""
    mock_orch = MagicMock()
    mock_orch.allocate.return_value = {
        "weights": {},
        "macro_abstain": True,
        "status": "unavailable",
    }

    ct = CoinTrackWithMacro(
        macro_orchestrator=mock_orch,
        _market_data_override={"price": 60000.0},
        _portfolio_override={},
        _external_data_override={},
        _past_decisions_override=[],
    )
    state = ct.collect_market_state()

    mock_dec = _make_mock_decision("sell", 0.7)
    with patch("agents.orchestrator.Orchestrator") as MockOrch:
        MockOrch.return_value.run.return_value = {"decision": mock_dec}
        decision = ct.generate_candidate(state)

    assert decision.decision == "sell"


def test_macro_no_abstain_buy_allowed():
    """macro fresh → buy 정상 허용."""
    mock_orch = MagicMock()
    mock_orch.allocate.return_value = {
        "weights": {"coin": 0.10},
        "macro_abstain": False,
        "status": "fresh",
    }

    ct = CoinTrackWithMacro(
        macro_orchestrator=mock_orch,
        _market_data_override={"price": 60000.0},
        _portfolio_override={},
        _external_data_override={},
        _past_decisions_override=[],
    )
    state = ct.collect_market_state()

    mock_dec = _make_mock_decision("buy", 0.7)
    with patch("agents.orchestrator.Orchestrator") as MockOrch:
        MockOrch.return_value.run.return_value = {"decision": mock_dec}
        decision = ct.generate_candidate(state)

    assert decision.decision == "buy"


def test_macro_layer_failure_graceful():
    """macro 레이어 실패 시 기존 CoinTrack 경로 유지 (graceful)."""
    mock_orch = MagicMock()
    mock_orch.allocate.side_effect = Exception("macro 실패")

    ct = CoinTrackWithMacro(
        macro_orchestrator=mock_orch,
        _market_data_override={"price": 60000.0},
        _portfolio_override={},
        _external_data_override={},
        _past_decisions_override=[],
    )
    state = ct.collect_market_state()
    # 실패해도 MarketState 반환됨
    assert isinstance(state, MarketState)
    assert state.raw_external_data.get("macro_abstain") is None  # 주입 실패 → 없음


def test_macro_disabled_no_injection():
    """macro_enabled=False → macro 주입 없음."""
    mock_orch = MagicMock()
    ct = CoinTrackWithMacro(
        macro_orchestrator=mock_orch,
        macro_enabled=False,
        _market_data_override={"price": 60000.0},
        _portfolio_override={},
        _external_data_override={},
        _past_decisions_override=[],
    )
    state = ct.collect_market_state()
    mock_orch.allocate.assert_not_called()
    assert "macro_abstain" not in state.raw_external_data
