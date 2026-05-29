"""tests/test_wp6_as_of_threading.py — WP6① collect_market_state(as_of=) 진입점.

PIT 백테스트 리플레이가 과거 시점을 track 으로 전달하는 진입점 검증.
- as_of=None: 현행 동작 보존(하위호환).
- as_of=<datetime>: raw_market_data["as_of"] 기록 + 엔진→track 스레딩.
SACRED: 라이브 결정 로직 미변경(default None 경로=기존과 동일).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from core.asset_track import AssetTrack, MarketState
from core.coin_track import CoinTrack
from core.coin_track_macro import CoinTrackWithMacro
from core.stock_track import StockTrack
from backtest.engine import BacktestEngine


_AS_OF = datetime(2023, 6, 1, tzinfo=timezone.utc)


def _coin_overrides():
    return dict(
        _market_data_override={"price": 60000.0},
        _portfolio_override={"krw_balance": 1_000_000.0},
        _external_data_override={"fgi": 50},
        _past_decisions_override=[],
    )


# --- 하위호환: as_of=None → 기존 동작 ----------------------------------------

def test_cointrack_as_of_none_backward_compatible():
    ct = CoinTrack(**_coin_overrides())
    state = ct.collect_market_state()
    assert isinstance(state, MarketState)
    assert state.raw_market_data.get("price") == 60000.0
    assert "as_of" not in state.raw_market_data


# --- as_of 기록 --------------------------------------------------------------

def test_cointrack_as_of_recorded():
    ct = CoinTrack(**_coin_overrides())
    state = ct.collect_market_state(as_of=_AS_OF)
    assert state.raw_market_data.get("as_of") == _AS_OF.isoformat()


def test_cointrackmacro_threads_as_of_to_super():
    ct = CoinTrackWithMacro(macro_enabled=False, **_coin_overrides())
    state = ct.collect_market_state(as_of=_AS_OF)
    assert state.raw_market_data.get("as_of") == _AS_OF.isoformat()


def test_stocktrack_as_of_recorded():
    st = StockTrack(ticker="005930", _market_data_override={"price": 70000.0})
    state = st.collect_market_state(as_of=_AS_OF)
    assert state.raw_market_data.get("as_of") == _AS_OF.isoformat()


def test_stocktrack_as_of_none_backward_compatible():
    st = StockTrack(ticker="005930", _market_data_override={"price": 70000.0})
    state = st.collect_market_state()
    assert "as_of" not in state.raw_market_data


# --- 엔진 → track as_of 스레딩 -----------------------------------------------

class _RecordingTrack(AssetTrack):
    """collect_market_state 가 받은 as_of 를 기록하는 최소 AssetTrack."""

    def __init__(self):
        self.seen_as_of = []

    def collect_market_state(self, as_of=None) -> MarketState:
        self.seen_as_of.append(as_of)
        return MarketState(raw_market_data={})

    def generate_candidate(self, state):
        class _D:
            action = "hold"
        return _D()

    def recommended_next_check(self, state):
        return datetime.now(timezone.utc)


def test_engine_threads_bar_timestamp_as_of():
    idx = pd.to_datetime(["2023-06-01", "2023-06-02", "2023-06-03"], utc=True)
    prices = pd.Series([100.0, 101.0, 102.0], index=idx, name="BTC")
    track = _RecordingTrack()

    BacktestEngine(initial_capital=1_000_000.0).run(track, prices)

    # 각 bar 의 타임스탬프가 as_of 로 전달됐는지
    assert len(track.seen_as_of) == 3
    assert all(isinstance(t, datetime) for t in track.seen_as_of)
    assert track.seen_as_of[0] == idx[0].to_pydatetime()
