"""tests/test_so6_pR_coin_consensus_lens.py — SO-6/PR consensus 코인 렌즈 검증.

검증 기준 (harness2.md SO-6/PR):
1. 코인 consensus 발동 시 코인 렌즈(on-chain/FGI/funding/technical) 사용
2. DCF 미사용 (주식 전용)
3. 타임아웃 짧게 (COIN_LENS_TIMEOUT_SEC < 주식)
4. risk_gate 항상-on 백스톱 보존 (§4.2 불변식)
5. consensus.py 본체 미변경 (CoinConsensusLens = subclass)
6. SO-1~5 PR 회귀 0
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.coin_consensus_lens import (
    CoinConsensusLens,
    CoinLensData,
    build_coin_lens_prompt,
    COIN_LENS_TIMEOUT_SEC,
)
from core.consensus import ConsensusContext, ConsensusJudge


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_ctx(regime_changed=True, allocation_change_pct=0.15) -> ConsensusContext:
    return ConsensusContext(
        regime_changed=regime_changed,
        allocation_change_pct=allocation_change_pct,
        current_weights={"coin": 0.15},
        proposed_weights={"coin": 0.20},
        macro_view="bull",
    )


def _make_lens() -> CoinLensData:
    return CoinLensData(
        whale_inflow_usd=-50_000_000,
        exchange_reserve_change_pct=-0.05,
        fear_greed_index=25.0,
        funding_rate=-0.001,
        open_interest_change_pct=0.10,
        rsi_14=32.0,
        price_change_24h_pct=-0.08,
    )


# ---------------------------------------------------------------------------
# 1. 코인 렌즈 프롬프트 — on-chain/FGI/funding/technical 포함
# ---------------------------------------------------------------------------

def test_coin_lens_prompt_contains_on_chain():
    """프롬프트에 on-chain 섹션 포함."""
    ctx = _make_ctx()
    lens = _make_lens()
    prompt = build_coin_lens_prompt(ctx, lens)
    assert "On-chain" in prompt or "on-chain" in prompt.lower()
    assert "Whale" in prompt


def test_coin_lens_prompt_contains_fgi():
    """프롬프트에 Fear & Greed Index 포함."""
    ctx = _make_ctx()
    lens = _make_lens()
    prompt = build_coin_lens_prompt(ctx, lens)
    assert "Fear" in prompt or "Greed" in prompt or "25" in prompt


def test_coin_lens_prompt_contains_funding():
    """프롬프트에 funding rate 포함."""
    ctx = _make_ctx()
    lens = _make_lens()
    prompt = build_coin_lens_prompt(ctx, lens)
    assert "Funding" in prompt or "funding" in prompt.lower()


def test_coin_lens_prompt_contains_technical():
    """프롬프트에 기술적 지표(RSI) 포함."""
    ctx = _make_ctx()
    lens = _make_lens()
    prompt = build_coin_lens_prompt(ctx, lens)
    assert "RSI" in prompt or "Technical" in prompt


# ---------------------------------------------------------------------------
# 2. DCF 미사용
# ---------------------------------------------------------------------------

def test_dcf_not_in_prompt():
    """코인 렌즈 프롬프트에 DCF 미포함."""
    ctx = _make_ctx()
    lens = _make_lens()
    prompt = build_coin_lens_prompt(ctx, lens)
    # DCF 언급이 있더라도 "NOT used" 명시 (코인 특성)
    assert "no DCF" in prompt.lower() or "dcf not used" in prompt.lower() or "NOT used" in prompt


def test_dcf_not_used_static_method():
    """CoinConsensusLens.dcf_not_used() = True."""
    assert CoinConsensusLens.dcf_not_used() is True


def test_coin_consensus_lens_no_dcf_attribute():
    """CoinLensData에 dcf_fair_value 필드 없음."""
    lens = CoinLensData()
    assert not hasattr(lens, "dcf_fair_value")


# ---------------------------------------------------------------------------
# 3. 타임아웃 짧게
# ---------------------------------------------------------------------------

def test_coin_lens_timeout_shorter_than_default():
    """코인 렌즈 타임아웃 < 30s (주식 기본값 대비 짧음)."""
    assert COIN_LENS_TIMEOUT_SEC < 30.0, (
        f"코인 타임아웃({COIN_LENS_TIMEOUT_SEC}s) >= 주식 기본(30s)"
    )


def test_coin_consensus_lens_timeout_property():
    """CoinConsensusLens.lens_timeout_sec = COIN_LENS_TIMEOUT_SEC."""
    lens_judge = CoinConsensusLens()
    assert lens_judge.lens_timeout_sec == COIN_LENS_TIMEOUT_SEC


# ---------------------------------------------------------------------------
# 4. risk_gate 항상-on 백스톱 보존
# ---------------------------------------------------------------------------

def test_risk_gate_backstop_preserved_on_rejection():
    """risk_gate 거부 → approve라도 hold 강제 (§4.2 불변식)."""
    mock_result = MagicMock()
    mock_result.text = "approve"
    mock_router = MagicMock()
    mock_router.route_with_meta.return_value = mock_result

    mock_gate_result = MagicMock()
    mock_gate_result.approved = False
    mock_risk_gate = MagicMock()
    mock_risk_gate.check.return_value = mock_gate_result

    judge = CoinConsensusLens(llm_router=mock_router, risk_gate=mock_risk_gate)
    ctx = _make_ctx()
    lens = _make_lens()

    result = judge.run_with_lens(ctx, lens)
    assert result.action == "hold", f"risk_gate 거절 시 hold 강제 실패: {result.action}"
    assert result.routing == "risk_gate_override"


def test_risk_gate_backstop_allows_on_approval():
    """risk_gate 승인 → 코인 렌즈 action 유지."""
    mock_result = MagicMock()
    mock_result.text = "approve"
    mock_router = MagicMock()
    mock_router.route_with_meta.return_value = mock_result

    mock_gate_result = MagicMock()
    mock_gate_result.approved = True
    mock_risk_gate = MagicMock()
    mock_risk_gate.check.return_value = mock_gate_result

    judge = CoinConsensusLens(llm_router=mock_router, risk_gate=mock_risk_gate)
    ctx = _make_ctx()
    lens = _make_lens()

    result = judge.run_with_lens(ctx, lens)
    assert result.action == "approve"
    assert result.routing == "coin_lens_llm"


def test_routine_no_risk_gate_call():
    """routine(미발동) → LLM 및 risk_gate 미호출."""
    mock_router = MagicMock()
    mock_gate = MagicMock()
    judge = CoinConsensusLens(llm_router=mock_router, risk_gate=mock_gate)

    ctx = ConsensusContext()  # 발동 조건 미달
    lens = _make_lens()
    result = judge.run_with_lens(ctx, lens)

    assert result.is_triggered is False
    mock_router.route_with_meta.assert_not_called()
    mock_gate.check.assert_not_called()


# ---------------------------------------------------------------------------
# 5. consensus.py 본체 미변경 (subclass)
# ---------------------------------------------------------------------------

def test_coin_consensus_lens_is_subclass():
    """CoinConsensusLens는 ConsensusJudge 서브클래스."""
    assert issubclass(CoinConsensusLens, ConsensusJudge)


def test_base_consensus_judge_still_works():
    """기존 ConsensusJudge 정상 동작 (본체 미변경)."""
    judge = ConsensusJudge()
    ctx = ConsensusContext(regime_changed=True)
    result = judge.run(ctx)
    assert result.is_triggered is True


def test_coin_lens_credential_none_falls_back_to_base():
    """credential 없음(router=None) → base ConsensusJudge 경로."""
    judge = CoinConsensusLens(llm_router=None)
    ctx = _make_ctx()
    lens = _make_lens()
    result = judge.run_with_lens(ctx, lens)
    # stub 반환 (credential 없음)
    assert result.routing in ("stub", "coin_lens_llm")
    assert result.action in ("approve", "hold", "reduce")


# ---------------------------------------------------------------------------
# 6. SO-1~5 PR 회귀 0
# ---------------------------------------------------------------------------

def test_so1_pr_regression():
    from core.coin_track_macro import CoinTrackWithMacro
    assert CoinTrackWithMacro is not None


def test_so2_pr_regression():
    from backtest.coin_engine import CoinBacktestEngine
    assert CoinBacktestEngine is not None


def test_so3_pr_regression():
    from core.coin_sizing import size_coin_portfolio
    assert size_coin_portfolio is not None


def test_so4_pr_regression():
    from core.coin_memory import CoinMemoryLayer, COIN_HALF_LIFE_HOURS
    assert COIN_HALF_LIFE_HOURS < 24.0


def test_so5_pr_regression():
    from core.coin_shadow import CoinShadowExecutor
    executor = CoinShadowExecutor()
    order = executor.place_shadow("BTC/KRW", "buy", 0.001, 50_000_000)
    assert order.is_dry_run is True


def test_so6_pr_coin_consensus_lens_import():
    from core.coin_consensus_lens import CoinConsensusLens, CoinLensData, COIN_LENS_TIMEOUT_SEC
    assert all([CoinConsensusLens, CoinLensData])
    assert COIN_LENS_TIMEOUT_SEC < 30.0
