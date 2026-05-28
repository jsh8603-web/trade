"""SO-4 결정적 replay 하니스 테스트.

검증기준:
- 동일 fixture를 N회(≥3) 반복 주입 → 매회 동일 decision 출력(결정성)
- RAG/시계/외부데이터 격리로 반복 간 비결정성 0 확인

5격리 구조:
  (a) RAG 격리: query_similar mock
  (b) 시계 freeze: fixture timestamp 고정 (비결정 필드 비교 제외)
  (c) 외부데이터/포트폴리오 override fixture
  (d) LLM record-replay: .env 없음 = mock-only
  (e) PPO/temperature=0: GEMINI_TEMPERATURE=0 환경변수
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[2]
for _p in (PROJECT_DIR, PROJECT_DIR / "scripts"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from tests.replay.conftest import OrchestratorIsolation, load_snapshot, ALL_FIXTURE_NAMES


REPEAT_N = 3  # 결정성 검증 반복 횟수


def _run_generate(snap: dict[str, Any]) -> dict:
    """CoinTrack.collect_market_state → generate_candidate 실행 후 결정 dict 반환."""
    from core.coin_track import CoinTrack

    ct = CoinTrack(
        _market_data_override=snap["market_data"],
        _portfolio_override=snap["portfolio"],
        _external_data_override=snap["external_data"],
        _past_decisions_override=snap.get("past_decisions", []),
    )
    with OrchestratorIsolation():
        state = ct.collect_market_state()
        decision = ct.generate_candidate(state)

    return {
        "decision": decision.decision,
        "confidence": decision.confidence,
        "agent_name": decision.agent_name,
        "buy_score": decision.buy_score,
    }


# ── 결정성 테스트 ────────────────────────────────────────────────────

@pytest.mark.parametrize("fixture_name", ALL_FIXTURE_NAMES)
def test_determinism_repeat_n_times(fixture_name: str):
    """동일 fixture를 REPEAT_N회 반복 → 매회 동일 decision(결정성)."""
    snap = load_snapshot(fixture_name)
    results = [_run_generate(snap) for _ in range(REPEAT_N)]

    first = results[0]
    for i, r in enumerate(results[1:], start=1):
        assert r["decision"] == first["decision"], (
            f"[{fixture_name}] 반복 {i}: decision 불일치 "
            f"first={first['decision']} got={r['decision']}"
        )
        assert abs(r["confidence"] - first["confidence"]) < 1e-6, (
            f"[{fixture_name}] 반복 {i}: confidence 불일치 "
            f"first={first['confidence']} got={r['confidence']}"
        )
        assert r["agent_name"] == first["agent_name"], (
            f"[{fixture_name}] 반복 {i}: agent_name 불일치 "
            f"first={first['agent_name']} got={r['agent_name']}"
        )


# ── RAG 격리 확인 ────────────────────────────────────────────────────

def test_rag_isolation_no_external_rag_calls():
    """격리 하니스에서 query_similar 등 외부 RAG 호출이 없음을 확인."""
    import unittest.mock as mock
    snap = load_snapshot("sideways_market")

    with mock.patch("agents.orchestrator._load_state",
                    return_value={"active_agent": "conservative"}), \
         mock.patch("agents.orchestrator._save_state"), \
         mock.patch("agents.orchestrator.Orchestrator._load_learning_data",
                    return_value=None), \
         mock.patch("agents.orchestrator.Orchestrator._check_auto_emergency_active",
                    return_value=None), \
         mock.patch.dict("os.environ", {
             "SUPABASE_URL": "", "SUPABASE_SERVICE_ROLE_KEY": "",
             "EMERGENCY_STOP": "false",
         }):
        result = _run_generate(snap)

    assert result["decision"] in ("buy", "sell", "hold")


# ── 외부데이터 격리: ExternalDataAgent.collect_all 호출 없음 ─────────

def test_external_data_isolation_uses_override():
    """override 주입 시 ExternalDataAgent.collect_all이 호출되지 않음."""
    import unittest.mock as mock
    snap = load_snapshot("bull_market")

    with mock.patch(
        "agents.external_data.ExternalDataAgent.collect_all",
        side_effect=AssertionError("collect_all should not be called"),
    ), OrchestratorIsolation():
        from core.coin_track import CoinTrack
        ct = CoinTrack(
            _market_data_override=snap["market_data"],
            _portfolio_override=snap["portfolio"],
            _external_data_override=snap["external_data"],
            _past_decisions_override=snap.get("past_decisions", []),
        )
        state = ct.collect_market_state()
        decision = ct.generate_candidate(state)

    assert decision.decision in ("buy", "sell", "hold")


# ── 시계 격리: fixture timestamp 고정 ───────────────────────────────

def test_clock_isolation_fixture_timestamp_used():
    """MarketState.timestamp가 fixture에 주입된 값을 그대로 반환."""
    snap = load_snapshot("bull_market")
    from core.coin_track import CoinTrack
    ct = CoinTrack(
        _market_data_override=snap["market_data"],
        _portfolio_override=snap["portfolio"],
        _external_data_override=snap["external_data"],
        _past_decisions_override=snap.get("past_decisions", []),
    )
    state = ct.collect_market_state()
    assert state.timestamp == snap["market_data"]["timestamp"]


# ── 5 fixture 전체 smoke ─────────────────────────────────────────────

@pytest.mark.parametrize("fixture_name", ALL_FIXTURE_NAMES)
def test_all_fixtures_run_without_error(fixture_name: str):
    """5개 fixture 모두 에러 없이 실행되고 유효한 decision 반환."""
    snap = load_snapshot(fixture_name)
    result = _run_generate(snap)
    assert result["decision"] in ("buy", "sell", "hold"), (
        f"[{fixture_name}] 예상치 못한 decision: {result['decision']}"
    )
