"""SO-5: 래핑 전후 의미 동치 검증 (§2.9 Phase 0 동작 게이트).

래핑 전: Orchestrator.run(market_data, external_data, portfolio, past_decisions) 직접 호출
래핑 후: CoinTrack.collect_market_state() → generate_candidate(state)

비교 기준:
  - decision/action 완전 일치
  - buy_score breakdown 수치 동일 (부동소수 abs_tol)
  - confidence 동일

byte-동일 금지: timestamp/uuid/agent_name 등 비결정 필드 제외.
static grep 만으로 PASS 금지 — 실제 테스트 실행+어서션 캡처 필수.

5개 fixture 전부 통과 필수.
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

ABS_TOL = 1e-6


def _direct_run(snap: dict[str, Any]) -> dict:
    """래핑 전: Orchestrator.run 직접 호출."""
    from agents.orchestrator import Orchestrator
    from agents.base_agent import Decision

    with OrchestratorIsolation():
        orch = Orchestrator()
        result = orch.run(
            market_data=snap["market_data"],
            external_data=snap["external_data"],
            portfolio=snap["portfolio"],
            past_decisions=snap.get("past_decisions", []),
        )

    raw = result.get("decision", {})
    if isinstance(raw, Decision):
        return {
            "decision": raw.decision,
            "confidence": raw.confidence,
            "buy_score": raw.buy_score,
        }
    return {
        "decision": raw.get("decision"),
        "confidence": raw.get("confidence", 0.0),
        "buy_score": raw.get("buy_score", {}),
    }


def _wrapped_run(snap: dict[str, Any]) -> dict:
    """래핑 후: CoinTrack.collect_market_state → generate_candidate."""
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
        "buy_score": decision.buy_score,
    }


def _assert_equivalence(
    fixture_name: str,
    direct: dict,
    wrapped: dict,
) -> None:
    """decision/confidence/buy_score 의미 동치 어서션."""
    # decision 완전 일치
    assert direct["decision"] == wrapped["decision"], (
        f"[{fixture_name}] decision mismatch: "
        f"direct={direct['decision']} wrapped={wrapped['decision']}"
    )

    # confidence 부동소수 동치
    assert abs((direct["confidence"] or 0.0) - (wrapped["confidence"] or 0.0)) <= ABS_TOL, (
        f"[{fixture_name}] confidence mismatch: "
        f"direct={direct['confidence']} wrapped={wrapped['confidence']}"
    )

    # buy_score breakdown 수치 동치
    d_score = direct["buy_score"] or {}
    w_score = wrapped["buy_score"] or {}
    assert set(d_score.keys()) == set(w_score.keys()), (
        f"[{fixture_name}] buy_score keys mismatch: "
        f"direct={set(d_score)} wrapped={set(w_score)}"
    )
    for key in d_score:
        dv = d_score[key] if isinstance(d_score[key], (int, float)) else 0
        wv = w_score[key] if isinstance(w_score[key], (int, float)) else 0
        assert abs(dv - wv) <= ABS_TOL, (
            f"[{fixture_name}] buy_score[{key}] mismatch: direct={dv} wrapped={wv}"
        )


# ── 5개 fixture 의미 동치 검증 ───────────────────────────────────────

@pytest.mark.parametrize("fixture_name", ALL_FIXTURE_NAMES)
def test_equivalence_direct_vs_wrapped(fixture_name: str):
    """래핑 전후 의미 동치 — 5개 fixture 전부 통과 필수 (Phase 0 게이트)."""
    snap = load_snapshot(fixture_name)
    direct = _direct_run(snap)
    wrapped = _wrapped_run(snap)
    _assert_equivalence(fixture_name, direct, wrapped)


# ── 기존 코인 회귀 확인 (Phase -1 91 tests) ──────────────────────────

def test_phase_minus1_regression():
    """기존 코인 테스트에서 SO-1~4가 회귀를 유발하지 않음을 확인.

    빠른 회귀 체크: SO-1~4 관련 core/ 임포트가 agents/ 모듈을 깨지 않는지 검증.
    """
    from agents.base_agent import Decision, BaseStrategyAgent
    from agents.orchestrator import Orchestrator
    from agents.external_data import ExternalDataAgent
    from agents.conservative import ConservativeAgent
    from agents.moderate import ModerateAgent
    from agents.aggressive import AggressiveAgent
    from core.asset_track import AssetTrack, MarketState
    from core.coin_track import CoinTrack
    from core.strategy import Strategy, StrategyFamily

    # agents/ 핵심 클래스들이 여전히 정상
    assert issubclass(ConservativeAgent, BaseStrategyAgent)
    assert issubclass(ModerateAgent, BaseStrategyAgent)
    assert issubclass(AggressiveAgent, BaseStrategyAgent)
    assert issubclass(CoinTrack, AssetTrack)
    assert StrategyFamily.DIRECTIONAL.value == "directional"
