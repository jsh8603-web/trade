"""SO-1 테스트: core/stock_track.py StockTrack(AssetTrack).

검증기준:
- StockTrack 인스턴스화 PASS
- collect_market_state → MarketState 무손실 PASS
- generate_candidate(mock state) → Decision 호환 출력 PASS
- AssetTrack 3 추상메서드 구현 어서션 PASS
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.asset_track import AssetTrack, MarketState
from core.stock_track import StockTrack
from stock.contracts import (
    FilingSource,
    Fundamentals,
    MarketQuote,
    RunMode,
    ValuationResult,
    ValueVerdict,
)

KST = timezone(timedelta(hours=9))


def _make_fundamentals(ticker="005930", pit_clean=True) -> Fundamentals:
    return Fundamentals(
        ticker=ticker,
        fiscal_period="2024FY",
        filing_timestamp=datetime(2024, 3, 15, tzinfo=KST),
        source=FilingSource.DART_XBRL if pit_clean else FilingSource.RESTATED,
        currency="KRW",
        revenue=300_000_000_000,
        free_cash_flow=30_000_000_000,
        outstanding_shares=5_000_000_000,
    )


def _make_valuation(ticker="005930", gap=0.30) -> ValuationResult:
    mcap = 400_000_000_000_000
    intrinsic = mcap * (1 + gap)
    return ValuationResult(
        ticker=ticker,
        as_of=datetime(2024, 4, 1, tzinfo=KST),
        currency="KRW",
        intrinsic_value=intrinsic,
        market_cap=mcap,
        valuation_gap=gap,
        bear_value=intrinsic * 0.8,
        base_value=intrinsic,
        bull_value=intrinsic * 1.2,
        wacc=0.09,
    )


def _make_quote(ticker="005930", price_change=-0.12) -> MarketQuote:
    return MarketQuote(
        ticker=ticker,
        as_of=datetime(2024, 4, 1, tzinfo=KST),
        price=71_000,
        market_cap=400_000_000_000_000,
        price_change_pct=price_change,
        price_change_window_days=30,
    )


# ── 기본 구조 ────────────────────────────────────────────────────────

def test_stock_track_is_asset_track():
    """StockTrack 은 AssetTrack 의 구현체."""
    assert issubclass(StockTrack, AssetTrack)


def test_stock_track_instantiation():
    """StockTrack 인스턴스화 성공."""
    track = StockTrack(ticker="005930")
    assert track.ticker == "005930"
    assert track.mode == RunMode.FORWARD


def test_stock_track_abstract_methods_implemented():
    """AssetTrack 3 추상메서드 모두 구현됨 — 인스턴스화 가능 = 추상 없음."""
    track = StockTrack()
    assert hasattr(track, "collect_market_state")
    assert hasattr(track, "generate_candidate")
    assert hasattr(track, "recommended_next_check")
    assert callable(track.collect_market_state)
    assert callable(track.generate_candidate)
    assert callable(track.recommended_next_check)


def test_abstract_base_cannot_instantiate():
    """AssetTrack 직접 인스턴스화 불가."""
    with pytest.raises(TypeError):
        AssetTrack()  # type: ignore[abstract]


# ── collect_market_state → MarketState 무손실 ────────────────────────

def test_collect_market_state_returns_market_state():
    track = StockTrack(ticker="005930")
    state = track.collect_market_state()
    assert isinstance(state, MarketState)


def test_collect_market_state_preserves_raw_data():
    """raw 4종 무손실 보존."""
    raw_market = {"ticker": "005930", "price": 71000}
    raw_external = {"sector": "반도체"}
    raw_portfolio = {"KRW": 1_000_000}
    raw_past = [{"decision": "hold"}]

    track = StockTrack(
        _market_data_override=raw_market,
        _external_data_override=raw_external,
        _portfolio_override=raw_portfolio,
        _past_decisions_override=raw_past,
    )
    state = track.collect_market_state()
    assert state.raw_market_data["ticker"] == "005930"
    assert state.raw_market_data["price"] == 71000
    assert state.raw_external_data["sector"] == "반도체"
    assert state.raw_portfolio["KRW"] == 1_000_000
    assert state.raw_past_decisions == [{"decision": "hold"}]


def test_collect_market_state_with_quote_override():
    """MarketQuote override → raw_market_data 에 통합."""
    quote = _make_quote()
    track = StockTrack(_quote_override=quote)
    state = track.collect_market_state()
    assert state.raw_market_data["ticker"] == "005930"
    assert state.raw_market_data["price"] == 71_000
    assert state.raw_market_data["price_change_pct"] == pytest.approx(-0.12)


def test_collect_market_state_with_fundamentals():
    """Fundamentals override → raw_external_data 에 통합."""
    f = _make_fundamentals()
    track = StockTrack(_fundamentals_override=[f])
    state = track.collect_market_state()
    assert "fundamentals" in state.raw_external_data
    assert len(state.raw_external_data["fundamentals"]) == 1
    assert state.raw_external_data["fundamentals"][0]["is_pit_clean"] is True


# ── generate_candidate → Decision 호환 dict ─────────────────────────

def test_generate_candidate_returns_dict():
    track = StockTrack()
    state = track.collect_market_state()
    result = track.generate_candidate(state)
    assert isinstance(result, dict)


def test_generate_candidate_decision_compatible_fields():
    """Decision 호환 필수 필드 포함."""
    track = StockTrack()
    state = track.collect_market_state()
    result = track.generate_candidate(state)
    assert "decision" in result
    assert "confidence" in result
    assert "reason" in result
    assert "trade_params" in result
    assert "agent_name" in result


def test_generate_candidate_no_valuation_returns_hold():
    """valuation 미연결(Phase 4 전) → hold/abstain 반환."""
    track = StockTrack(ticker="005930")
    state = track.collect_market_state()
    result = track.generate_candidate(state)
    assert result["decision"] in ("hold", "abstain")
    assert result["confidence"] == 0.0


def test_generate_candidate_opportunity():
    """가격↓ + 가치갭 충분 + heavy_agent=False(기회) → buy."""
    mock_ha = MagicMock()
    from stock.value_trigger import HeavyAgentVerdict
    mock_ha.judge_value_trap.return_value = HeavyAgentVerdict(
        is_trap=False, confidence=0.8, reasoning="기회: 내재가치 충분"
    )

    track = StockTrack(
        ticker="005930",
        mode=RunMode.FORWARD,
        _valuation_override=_make_valuation(gap=0.30),
        _fundamentals_override=[_make_fundamentals()],
        _quote_override=_make_quote(price_change=-0.12),
        _heavy_agent_override=mock_ha,
    )
    state = track.collect_market_state()
    result = track.generate_candidate(state)
    assert result["decision"] == "buy"
    assert result["confidence"] > 0


def test_generate_candidate_value_trap():
    """가격↓ + heavy_agent=True(함정) → hold."""
    mock_ha = MagicMock()
    from stock.value_trigger import HeavyAgentVerdict
    mock_ha.judge_value_trap.return_value = HeavyAgentVerdict(
        is_trap=True, confidence=0.85, reasoning="thesis 붕괴"
    )

    track = StockTrack(
        ticker="005930",
        mode=RunMode.FORWARD,
        _valuation_override=_make_valuation(gap=0.30),
        _fundamentals_override=[_make_fundamentals()],
        _quote_override=_make_quote(price_change=-0.12),
        _heavy_agent_override=mock_ha,
    )
    state = track.collect_market_state()
    result = track.generate_candidate(state)
    assert result["decision"] == "hold"
    assert result["_trigger_result"].verdict == ValueVerdict.VALUE_TRAP


def test_generate_candidate_backtest_abstain():
    """BACKTEST 모드 → ABSTAIN(H22)."""
    track = StockTrack(
        ticker="005930",
        mode=RunMode.BACKTEST,
        _valuation_override=_make_valuation(gap=0.30),
        _quote_override=_make_quote(price_change=-0.12),
    )
    state = track.collect_market_state()
    result = track.generate_candidate(state)
    assert result["decision"] == "hold"
    assert result["_trigger_result"].verdict == ValueVerdict.ABSTAIN


def test_generate_candidate_gate1_reject():
    """가격변동 미달(0%) → 1차 게이트 미통과 → hold."""
    track = StockTrack(
        ticker="005930",
        mode=RunMode.FORWARD,
        _valuation_override=_make_valuation(gap=0.30),
        _quote_override=_make_quote(price_change=0.0),  # 가격 변동 없음
    )
    state = track.collect_market_state()
    result = track.generate_candidate(state)
    assert result["decision"] == "hold"
    assert result["_trigger_result"].verdict == ValueVerdict.REJECT


# ── recommended_next_check ───────────────────────────────────────────

def test_recommended_next_check_returns_datetime():
    track = StockTrack()
    state = track.collect_market_state()
    result = track.recommended_next_check(state)
    assert isinstance(result, datetime)
    assert result > datetime.now(KST)
