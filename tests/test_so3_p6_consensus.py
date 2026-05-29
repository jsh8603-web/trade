"""tests/test_so3_p6_consensus.py — SO-3/P6 §4.2 consensus 2단 Judge 검증.

검증 기준 (harness2.md SO-3/P6):
1. is_high_stakes — 레짐flip/배분변경/누적포지션 각각 발동
2. routine(미발동) → stub 즉시 반환, LLM 미호출, 비용 0
3. 발동 시 LLMRouter deep(Claude) 경유 — credential 없으면 stub
4. risk_gate 항상-on 백스톱 — approve라도 risk_gate 거부 시 hold 강제
5. path-attribution DecisionRecord 기록
6. ConsensusDecision 구조 (action/is_triggered/confidence/reasoning/routing)
7. SO-1/SO-2 P6 회귀 0
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.consensus import (
    ConsensusContext,
    ConsensusDecision,
    ConsensusJudge,
    DecisionRecord,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_ctx(
    regime_changed=False,
    allocation_change_pct=0.0,
    cumulative_position_pct=0.0,
    past_lessons="",
) -> ConsensusContext:
    return ConsensusContext(
        regime_changed=regime_changed,
        allocation_change_pct=allocation_change_pct,
        cumulative_position_pct=cumulative_position_pct,
        current_weights={"coin": 0.10, "us_stock": 0.30},
        proposed_weights={"coin": 0.15, "us_stock": 0.25},
        macro_view="neutral",
        past_lessons=past_lessons,
    )


def _make_judge(llm_router=None, risk_gate=None) -> ConsensusJudge:
    return ConsensusJudge(
        llm_router=llm_router,
        risk_gate=risk_gate,
        allocation_threshold=0.10,
        cumulative_threshold=0.25,
    )


# ---------------------------------------------------------------------------
# 1. is_high_stakes — 발동 조건
# ---------------------------------------------------------------------------

def test_high_stakes_regime_changed():
    """레짐flip → 고-스테이크스 발동."""
    judge = _make_judge()
    ctx = _make_ctx(regime_changed=True)
    assert judge.is_high_stakes(ctx) is True


def test_high_stakes_allocation_change():
    """배분변경 10% 이상 → 발동."""
    judge = _make_judge()
    ctx = _make_ctx(allocation_change_pct=0.12)
    assert judge.is_high_stakes(ctx) is True


def test_high_stakes_cumulative_position():
    """누적포지션 25% 이상 → 발동."""
    judge = _make_judge()
    ctx = _make_ctx(cumulative_position_pct=0.30)
    assert judge.is_high_stakes(ctx) is True


def test_not_high_stakes_routine():
    """routine(기준 미달) → 미발동."""
    judge = _make_judge()
    ctx = _make_ctx(
        regime_changed=False,
        allocation_change_pct=0.05,
        cumulative_position_pct=0.10,
    )
    assert judge.is_high_stakes(ctx) is False


def test_high_stakes_threshold_boundary():
    """배분변경 정확히 threshold — 발동."""
    judge = _make_judge()
    ctx = _make_ctx(allocation_change_pct=0.10)
    assert judge.is_high_stakes(ctx) is True

    ctx2 = _make_ctx(allocation_change_pct=0.099)
    assert judge.is_high_stakes(ctx2) is False


# ---------------------------------------------------------------------------
# 2. routine 미발동 → stub, LLM 미호출
# ---------------------------------------------------------------------------

def test_routine_returns_stub_immediately():
    """routine → is_triggered=False, routing=stub."""
    mock_router = MagicMock()
    judge = _make_judge(llm_router=mock_router)
    ctx = _make_ctx()  # 기준 미달 routine

    result = judge.run(ctx)
    assert result.is_triggered is False
    assert result.routing == "stub"
    assert result.action == "hold"
    # LLM 미호출
    mock_router.route_with_meta.assert_not_called()


def test_routine_records_decision():
    """routine 에도 path-attribution 기록."""
    judge = _make_judge()
    ctx = _make_ctx()
    judge.run(ctx)
    assert len(judge.decision_records) == 1
    rec = judge.decision_records[0]
    assert isinstance(rec, DecisionRecord)
    assert rec.final_action == "hold"


# ---------------------------------------------------------------------------
# 3. 고-스테이크스 발동 시 LLMRouter 경유
# ---------------------------------------------------------------------------

def test_high_stakes_calls_llm_router():
    """고-스테이크스 → LLMRouter.route_with_meta 호출."""
    mock_result = MagicMock()
    mock_result.text = "approve the allocation change"
    mock_router = MagicMock()
    mock_router.route_with_meta.return_value = mock_result

    judge = _make_judge(llm_router=mock_router)
    ctx = _make_ctx(regime_changed=True)

    result = judge.run(ctx)
    mock_router.route_with_meta.assert_called_once()
    assert result.routing == "llm"


def test_high_stakes_no_credential_returns_stub():
    """credential 없음(router=None) → stub 반환, 예외 없음."""
    judge = _make_judge(llm_router=None)
    ctx = _make_ctx(regime_changed=True)

    result = judge.run(ctx)
    assert result.routing == "stub"
    assert result.action == "hold"


def test_lessons_injected_into_prompt():
    """lessons → LLM 프롬프트에 past_lessons 포함."""
    captured = []

    mock_result = MagicMock()
    mock_result.text = "approve"
    mock_router = MagicMock()

    def capture_call(prompt, **kwargs):
        captured.append(prompt)
        return mock_result

    mock_router.route_with_meta.side_effect = capture_call

    judge = _make_judge(llm_router=mock_router)
    ctx = _make_ctx(regime_changed=True, past_lessons="Previous lesson: avoid momentum chasing")

    judge.run(ctx)
    assert len(captured) == 1
    assert "Previous lesson" in captured[0], "lessons_line 미주입"


def test_high_stakes_is_triggered_true():
    """고-스테이크스 발동 → is_triggered=True."""
    mock_result = MagicMock()
    mock_result.text = "approve"
    mock_router = MagicMock()
    mock_router.route_with_meta.return_value = mock_result

    judge = _make_judge(llm_router=mock_router)
    ctx = _make_ctx(allocation_change_pct=0.15)

    result = judge.run(ctx)
    assert result.is_triggered is True


# ---------------------------------------------------------------------------
# 4. risk_gate 항상-on 백스톱
# ---------------------------------------------------------------------------

def test_risk_gate_approved_passes_through():
    """risk_gate approve → consensus action 유지."""
    mock_result = MagicMock()
    mock_result.text = "approve"
    mock_router = MagicMock()
    mock_router.route_with_meta.return_value = mock_result

    mock_gate_result = MagicMock()
    mock_gate_result.approved = True
    mock_risk_gate = MagicMock()
    mock_risk_gate.check.return_value = mock_gate_result

    judge = _make_judge(llm_router=mock_router, risk_gate=mock_risk_gate)
    ctx = _make_ctx(regime_changed=True)

    result = judge.run(ctx)
    assert result.action == "approve"
    assert result.routing != "risk_gate_override"


def test_risk_gate_rejected_forces_hold():
    """risk_gate 거부 → approve라도 hold 강제."""
    mock_result = MagicMock()
    mock_result.text = "approve"
    mock_router = MagicMock()
    mock_router.route_with_meta.return_value = mock_result

    mock_gate_result = MagicMock()
    mock_gate_result.approved = False
    mock_risk_gate = MagicMock()
    mock_risk_gate.check.return_value = mock_gate_result

    judge = _make_judge(llm_router=mock_router, risk_gate=mock_risk_gate)
    ctx = _make_ctx(regime_changed=True)

    result = judge.run(ctx)
    assert result.action == "hold", f"risk_gate 거부 시 hold 강제 실패: {result.action}"
    assert result.routing == "risk_gate_override"


def test_risk_gate_none_passes_through():
    """risk_gate=None → 백스톱 미적용, action 유지."""
    mock_result = MagicMock()
    mock_result.text = "reduce exposure"
    mock_router = MagicMock()
    mock_router.route_with_meta.return_value = mock_result

    judge = _make_judge(llm_router=mock_router, risk_gate=None)
    ctx = _make_ctx(regime_changed=True)

    result = judge.run(ctx)
    assert result.action == "reduce"


# ---------------------------------------------------------------------------
# 5. path-attribution DecisionRecord
# ---------------------------------------------------------------------------

def test_decision_record_stored():
    """고-스테이크스 실행 후 DecisionRecord 기록."""
    mock_result = MagicMock()
    mock_result.text = "approve"
    mock_router = MagicMock()
    mock_router.route_with_meta.return_value = mock_result

    judge = _make_judge(llm_router=mock_router)
    ctx = _make_ctx(regime_changed=True)

    judge.run(ctx)
    records = judge.decision_records
    assert len(records) == 1
    rec = records[0]
    assert rec.context is ctx
    assert isinstance(rec.decision, ConsensusDecision)
    assert rec.final_action in ("approve", "hold", "reduce")


def test_multiple_runs_accumulate_records():
    """여러 번 run() 호출 → records 누적."""
    judge = _make_judge()

    judge.run(_make_ctx())  # routine
    judge.run(_make_ctx())  # routine

    assert len(judge.decision_records) == 2


def test_decision_record_risk_gate_passed_flag():
    """risk_gate_passed 플래그 정확히 기록."""
    mock_result = MagicMock()
    mock_result.text = "approve"
    mock_router = MagicMock()
    mock_router.route_with_meta.return_value = mock_result

    mock_gate_result = MagicMock()
    mock_gate_result.approved = False
    mock_risk_gate = MagicMock()
    mock_risk_gate.check.return_value = mock_gate_result

    judge = _make_judge(llm_router=mock_router, risk_gate=mock_risk_gate)
    judge.run(_make_ctx(regime_changed=True))

    rec = judge.decision_records[0]
    assert rec.risk_gate_passed is False


# ---------------------------------------------------------------------------
# 6. ConsensusDecision 구조
# ---------------------------------------------------------------------------

def test_decision_has_required_fields():
    """ConsensusDecision 필수 필드 확인."""
    judge = _make_judge()
    result = judge.run(_make_ctx())
    assert hasattr(result, "action")
    assert hasattr(result, "is_triggered")
    assert hasattr(result, "confidence")
    assert hasattr(result, "reasoning")
    assert hasattr(result, "routing")
    assert hasattr(result, "as_of")


def test_confidence_in_range():
    """confidence 0~1 범위."""
    judge = _make_judge()
    result = judge.run(_make_ctx())
    assert 0.0 <= result.confidence <= 1.0


# ---------------------------------------------------------------------------
# 7. SO-1/SO-2 P6 회귀 0
# ---------------------------------------------------------------------------

def test_so1_p6_orchestrator_import():
    """SO-1/P6: portfolio_orchestrator 미변경."""
    from core.portfolio_orchestrator import PortfolioOrchestrator, SLEEVE_BANDS
    assert len(SLEEVE_BANDS) == 7
    orc = PortfolioOrchestrator()
    assert orc is not None


def test_so2_p6_drift_monitor_import():
    """SO-2/P6: Drift Monitor NearMissVeto 미변경."""
    from core.portfolio_orchestrator import NearMissVeto, is_high_stakes
    veto = NearMissVeto(sleeve="coin", current_weight=0.25, band_min=0.02, band_max=0.20, reason="drift")
    assert veto.sleeve == "coin"


def test_so3_p6_consensus_import():
    """SO-3/P6: core/consensus.py import 정합."""
    from core.consensus import ConsensusJudge, ConsensusContext, ConsensusDecision, DecisionRecord
    assert all([ConsensusJudge, ConsensusContext, ConsensusDecision, DecisionRecord])
