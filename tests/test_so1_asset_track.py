"""SO-1 단위 테스트: core/asset_track.py AssetTrack ABC + MarketState."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
for _p in (PROJECT_DIR, PROJECT_DIR / "scripts"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from core.asset_track import AssetTrack, MarketState


class _ConcreteTrack(AssetTrack):
    """테스트용 최소 구현체."""

    def collect_market_state(self) -> MarketState:
        return MarketState()

    def generate_candidate(self, state: MarketState):
        return None  # type: ignore[return-value]

    def recommended_next_check(self, state: MarketState) -> datetime:
        return datetime.utcnow()


def test_import_ok():
    from core.asset_track import AssetTrack, MarketState  # noqa: F401


def test_abstract_instantiation_raises():
    with pytest.raises(TypeError):
        AssetTrack()  # type: ignore[abstract]


def test_concrete_instantiation_ok():
    t = _ConcreteTrack()
    assert isinstance(t, AssetTrack)


def test_market_state_round_trip_market_data():
    raw = {"timestamp": "2025-01-01T00:00:00+09:00", "market": "KRW-BTC", "current_price": 80000000}
    state = MarketState(raw_market_data=raw)
    assert state.raw_market_data is raw
    assert state.timestamp == "2025-01-01T00:00:00+09:00"
    assert state.asset == "KRW-BTC"
    assert state.price == 80000000.0


def test_market_state_round_trip_external_data():
    ext = {"fgi": 25, "fusion_signal": "buy"}
    state = MarketState(raw_external_data=ext)
    assert state.raw_external_data is ext


def test_market_state_round_trip_portfolio():
    port = {"krw_balance": 1000000, "btc_balance": 0.01}
    state = MarketState(raw_portfolio=port)
    assert state.raw_portfolio is port


def test_market_state_round_trip_past_decisions():
    past = [{"decision": "hold"}, {"decision": "buy"}]
    state = MarketState(raw_past_decisions=past)
    assert state.raw_past_decisions is past


def test_market_state_all_four_round_trip():
    md = {"current_price": 90000000, "market": "KRW-BTC", "timestamp": "T"}
    ext = {"fgi": 10}
    port = {"krw_balance": 500000}
    past = [{"decision": "sell"}]
    state = MarketState(
        raw_market_data=md,
        raw_external_data=ext,
        raw_portfolio=port,
        raw_past_decisions=past,
    )
    assert state.raw_market_data is md
    assert state.raw_external_data is ext
    assert state.raw_portfolio is port
    assert state.raw_past_decisions is past


def test_market_state_price_none_when_missing():
    state = MarketState()
    assert state.price is None
    assert state.asset is None
    assert state.timestamp is None
