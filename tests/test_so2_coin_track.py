"""SO-2 테스트: core/coin_track.py CoinTrack(AssetTrack) 래핑 검증.

동일 입력 → CoinTrack.generate_candidate vs Orchestrator.run 의미 동치 확인.
실제 외부 호출 금지(mock-only): ExternalDataAgent.collect_all + 스크립트 subprocess 스텁.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
for _p in (PROJECT_DIR, PROJECT_DIR / "scripts"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

# -- 최소 fixture --
_MARKET_DATA = {
    "timestamp": "2025-01-01T09:00:00+09:00",
    "market": "KRW-BTC",
    "current_price": 80_000_000,
    "ticker": {"signed_change_rate": 0.01},
    "indicators": {"rsi_14": 45.0, "sma_20": 79_000_000},
    "fear_greed": {"value": 40},
    "news": {"overall_sentiment": "neutral", "sentiment_score": 0},
}
_EXTERNAL_DATA: dict = {
    "sources": {
        "fear_greed": {"current": {"value": 40}},
        "news": {"title": "test"},
        "news_sentiment": {"overall_sentiment": "neutral", "sentiment_score": 0},
        "nvt": {"nvt_signal": 100.0},
    },
    "total_score": 0,
    "fusion": {"signal": "neutral"},
    "collection_time_sec": 0,
    "errors": [],
}
_PORTFOLIO = {
    "krw_balance": 1_000_000,
    "total_eval": 1_000_000,
    "btc_balance": 0.0,
    "btc": {},
    "btc_ratio": 0.0,
}
_PAST_DECISIONS: list = []


# ── 공통 mock 패치 (DB/외부 호출 차단) ──────────────────────────────

def _make_orch_patches():
    """Orchestrator 내부 DB/네트워크 의존성을 모두 mock.

    실제 있는 메서드만 패치 + SUPABASE 환경변수 제거로 DB 호출 차단.
    """
    return [
        patch("agents.orchestrator._load_state", return_value={"active_agent": "conservative"}),
        patch("agents.orchestrator._save_state"),
        patch("agents.orchestrator.Orchestrator._load_learning_data", return_value=None),
        patch("agents.orchestrator.Orchestrator._check_auto_emergency_active", return_value=None),
        patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_SERVICE_ROLE_KEY": ""}),
    ]


# ────────────────────────────────────────────────────────────────────

def test_import_ok():
    from core.coin_track import CoinTrack  # noqa: F401


def test_coin_track_is_asset_track():
    from core.asset_track import AssetTrack
    from core.coin_track import CoinTrack
    assert issubclass(CoinTrack, AssetTrack)


def test_collect_market_state_uses_overrides():
    from core.coin_track import CoinTrack
    ct = CoinTrack(
        _market_data_override=_MARKET_DATA,
        _portfolio_override=_PORTFOLIO,
        _external_data_override=_EXTERNAL_DATA,
        _past_decisions_override=_PAST_DECISIONS,
    )
    state = ct.collect_market_state()
    assert state.raw_market_data is _MARKET_DATA
    assert state.raw_portfolio is _PORTFOLIO
    assert state.raw_external_data is _EXTERNAL_DATA
    assert state.raw_past_decisions is _PAST_DECISIONS


def test_generate_candidate_delegates_to_orchestrator():
    """generate_candidate → Orchestrator.run 통째 위임 확인."""
    from core.coin_track import CoinTrack
    from core.asset_track import MarketState
    from agents.base_agent import Decision

    state = MarketState(
        raw_market_data=_MARKET_DATA,
        raw_external_data=_EXTERNAL_DATA,
        raw_portfolio=_PORTFOLIO,
        raw_past_decisions=_PAST_DECISIONS,
    )
    ct = CoinTrack()

    patches = _make_orch_patches()
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        result = ct.generate_candidate(state)

    assert isinstance(result, Decision)
    assert result.decision in ("buy", "sell", "hold")


def test_generate_candidate_emergency_stop_returns_hold(monkeypatch):
    """EMERGENCY_STOP=true → generate_candidate 반드시 hold."""
    monkeypatch.setenv("EMERGENCY_STOP", "true")
    from core.coin_track import CoinTrack
    from core.asset_track import MarketState
    from agents.base_agent import Decision

    state = MarketState(
        raw_market_data=_MARKET_DATA,
        raw_external_data=_EXTERNAL_DATA,
        raw_portfolio=_PORTFOLIO,
        raw_past_decisions=_PAST_DECISIONS,
    )
    ct = CoinTrack()

    patches = _make_orch_patches()
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        result = ct.generate_candidate(state)

    assert isinstance(result, Decision)
    assert result.decision == "hold"
    monkeypatch.delenv("EMERGENCY_STOP")


def test_semantic_equivalence_coin_track_vs_orchestrator_direct():
    """CoinTrack.generate_candidate 와 Orchestrator.run 직접 호출의 의미 동치.

    동일 입력 → decision/confidence 일치. timestamp/uuid 비교 제외.
    """
    from core.coin_track import CoinTrack
    from core.asset_track import MarketState
    from agents.orchestrator import Orchestrator
    from agents.base_agent import Decision

    state = MarketState(
        raw_market_data=_MARKET_DATA,
        raw_external_data=_EXTERNAL_DATA,
        raw_portfolio=_PORTFOLIO,
        raw_past_decisions=_PAST_DECISIONS,
    )

    patches = _make_orch_patches()

    # 래핑 후: CoinTrack.generate_candidate
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        wrapped_result = CoinTrack().generate_candidate(state)

    # 래핑 전: Orchestrator.run 직접 호출
    patches2 = _make_orch_patches()
    with patches2[0], patches2[1], patches2[2], patches2[3], patches2[4]:
        orch = Orchestrator()
        direct_result_raw = orch.run(
            market_data=_MARKET_DATA,
            external_data=_EXTERNAL_DATA,
            portfolio=_PORTFOLIO,
            past_decisions=_PAST_DECISIONS,
        )

    direct_decision = direct_result_raw.get("decision", {})
    if isinstance(direct_decision, Decision):
        direct_action = direct_decision.decision
        direct_confidence = direct_decision.confidence
    else:
        direct_action = direct_decision.get("decision")
        direct_confidence = direct_decision.get("confidence")

    assert wrapped_result.decision == direct_action, (
        f"decision mismatch: wrapped={wrapped_result.decision} direct={direct_action}"
    )
    assert abs(wrapped_result.confidence - (direct_confidence or 0.0)) < 1e-6, (
        f"confidence mismatch: wrapped={wrapped_result.confidence} direct={direct_confidence}"
    )


def test_recommended_next_check_returns_future_datetime():
    from core.coin_track import CoinTrack
    from core.asset_track import MarketState

    state = MarketState(raw_external_data=_EXTERNAL_DATA)
    ct = CoinTrack(
        _market_data_override=_MARKET_DATA,
        _portfolio_override=_PORTFOLIO,
        _external_data_override=_EXTERNAL_DATA,
        _past_decisions_override=_PAST_DECISIONS,
    )
    next_check = ct.recommended_next_check(state)
    assert isinstance(next_check, datetime)
    assert next_check > datetime.now(tz=next_check.tzinfo)
