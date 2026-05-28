"""SO-4 테스트: value_trigger 2단 wire + 모순2(BACKTEST abstain) + 모순1 최소훅.

검증기준:
- 1차 미통과 → REJECT PASS
- BACKTEST → ABSTAIN(H22) PASS
- heavy_agent=None forward → abstain + 사유구분 reasoning PASS
- value-trap → VALUE_TRAP(direction none) PASS
- 기회 → OPPORTUNITY(buy) PASS
- 모순1: quality vs resource 사유구분 reasoning 명시 PASS
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

from stock.contracts import (
    FilingSource,
    Fundamentals,
    MarketQuote,
    RunMode,
    ValuationResult,
    ValueVerdict,
    TriggerStage,
)
from stock.value_trigger import (
    Gate1Thresholds,
    HeavyAgentVerdict,
    passes_gate1,
    run_value_trigger,
    to_track_decision,
)

KST = timezone(timedelta(hours=9))


def _make_valuation(gap=0.30, intrinsic_mult=1.3) -> ValuationResult:
    mcap = 400_000_000_000_000
    return ValuationResult(
        ticker="005930",
        as_of=datetime(2024, 4, 1, tzinfo=KST),
        currency="KRW",
        intrinsic_value=mcap * intrinsic_mult,
        market_cap=mcap,
        valuation_gap=gap,
        bear_value=mcap * 1.1,
        base_value=mcap * 1.3,
        bull_value=mcap * 1.5,
        wacc=0.09,
    )


def _make_fundamentals() -> Fundamentals:
    return Fundamentals(
        ticker="005930",
        fiscal_period="2024FY",
        filing_timestamp=datetime(2024, 3, 15, tzinfo=KST),
        source=FilingSource.DART_XBRL,
        currency="KRW",
        free_cash_flow=30_000_000_000,
    )


def _make_mock_ha(is_trap: bool, confidence=0.8) -> MagicMock:
    m = MagicMock()
    m.judge_value_trap.return_value = HeavyAgentVerdict(
        is_trap=is_trap,
        confidence=confidence,
        reasoning="기회: 내재가치 충분" if not is_trap else "thesis 붕괴",
    )
    return m


# ── passes_gate1 단위 ────────────────────────────────────────────────

def test_passes_gate1_both_conditions():
    """가격↓ + 가치갭 충분 → PASS."""
    val = _make_valuation(gap=0.30)
    passed, reason = passes_gate1(val, price_change_pct=-0.15)
    assert passed is True


def test_passes_gate1_no_price_drop():
    """가격 안 빠짐 → FAIL."""
    val = _make_valuation(gap=0.30)
    passed, reason = passes_gate1(val, price_change_pct=0.0)
    assert passed is False
    assert "가격" in reason or "price" in reason.lower()


def test_passes_gate1_insufficient_gap():
    """가치갭 미달 → FAIL."""
    val = _make_valuation(gap=0.10)  # gap < 0.25 (기본 임계)
    passed, reason = passes_gate1(val, price_change_pct=-0.15)
    assert passed is False


def test_passes_gate1_no_price_data():
    """가격변동 데이터 없음 → FAIL."""
    val = _make_valuation(gap=0.30)
    passed, reason = passes_gate1(val, price_change_pct=None)
    assert passed is False


# ── 1차 게이트 미통과 → REJECT ────────────────────────────────────────

def test_gate1_reject():
    """1차 미통과 → REJECT."""
    val = _make_valuation(gap=0.30)
    result = run_value_trigger(val, [], price_change_pct=0.0)
    assert result.verdict == ValueVerdict.REJECT
    assert result.passed_gate1 is False
    assert result.stage_reached == TriggerStage.GATE1_QWEN
    assert result.direction == "none"


# ── BACKTEST abstain (H22) ────────────────────────────────────────────

def test_backtest_abstain_h22():
    """BACKTEST 모드 → ABSTAIN, heavy-agent 미호출(H22)."""
    val = _make_valuation(gap=0.30)
    ha = _make_mock_ha(is_trap=False)
    result = run_value_trigger(
        val, [_make_fundamentals()],
        price_change_pct=-0.15,
        heavy_agent=ha,
        mode=RunMode.BACKTEST,
    )
    assert result.verdict == ValueVerdict.ABSTAIN
    assert result.passed_gate1 is True
    ha.judge_value_trap.assert_not_called()  # 2차 heavy-agent 호출 없음


def test_backtest_abstain_preserves_line226():
    """H22: value_trigger.py:226 BACKTEST abstain stub 보존 확인."""
    src = (PROJECT_ROOT / "stock" / "value_trigger.py").read_text(encoding="utf-8")
    assert "RunMode.BACKTEST" in src
    assert "ABSTAIN" in src
    assert "H22" in src or "lookahead" in src or "백테스트" in src


# ── heavy_agent=None forward → abstain + 모순1 사유구분 ─────────────

def test_no_heavy_agent_forward_abstain_quality():
    """heavy_agent=None, reason=quality → abstain + quality 사유 reasoning."""
    val = _make_valuation(gap=0.30)
    result = run_value_trigger(
        val, [_make_fundamentals()],
        price_change_pct=-0.15,
        heavy_agent=None,
        mode=RunMode.FORWARD,
        heavy_agent_fail_reason="quality",
    )
    assert result.verdict == ValueVerdict.ABSTAIN
    assert "quality" in result.reasoning


def test_no_heavy_agent_forward_abstain_resource():
    """heavy_agent=None, reason=resource → abstain + resource 사유 reasoning."""
    val = _make_valuation(gap=0.30)
    result = run_value_trigger(
        val, [_make_fundamentals()],
        price_change_pct=-0.15,
        heavy_agent=None,
        mode=RunMode.FORWARD,
        heavy_agent_fail_reason="resource",
    )
    assert result.verdict == ValueVerdict.ABSTAIN
    assert "resource" in result.reasoning


def test_no_heavy_agent_no_reason_not_silent():
    """heavy_agent=None, reason=None → abstain + 사유불명 명시(silent 금지)."""
    val = _make_valuation(gap=0.30)
    result = run_value_trigger(
        val, [_make_fundamentals()],
        price_change_pct=-0.15,
        heavy_agent=None,
        mode=RunMode.FORWARD,
        heavy_agent_fail_reason=None,
    )
    assert result.verdict == ValueVerdict.ABSTAIN
    assert result.reasoning != ""  # silent 아님
    assert "unknown" in result.reasoning or "불명" in result.reasoning or "미전달" in result.reasoning


# ── value-trap → VALUE_TRAP ──────────────────────────────────────────

def test_value_trap_verdict():
    """heavy_agent=trap → VALUE_TRAP + direction=none."""
    val = _make_valuation(gap=0.30)
    ha = _make_mock_ha(is_trap=True)
    result = run_value_trigger(
        val, [_make_fundamentals()],
        price_change_pct=-0.15,
        heavy_agent=ha,
        mode=RunMode.FORWARD,
    )
    assert result.verdict == ValueVerdict.VALUE_TRAP
    assert result.direction == "none"
    assert result.stage_reached == TriggerStage.GATE2_HEAVY


# ── 기회 → OPPORTUNITY ───────────────────────────────────────────────

def test_opportunity_verdict():
    """heavy_agent=not trap → OPPORTUNITY + direction=buy."""
    val = _make_valuation(gap=0.30)
    ha = _make_mock_ha(is_trap=False)
    result = run_value_trigger(
        val, [_make_fundamentals()],
        price_change_pct=-0.15,
        heavy_agent=ha,
        mode=RunMode.FORWARD,
    )
    assert result.verdict == ValueVerdict.OPPORTUNITY
    assert result.direction == "buy"
    assert result.confidence > 0


# ── buy-the-dip 차단: 가격↓ + 내재가치↓ 동반 ─────────────────────────

def test_buy_the_dip_blocked_by_gate():
    """내재가치 5% 이상 동반 하락 → 2차 가서 trap 우선 검토 (플래그 전달)."""
    val = _make_valuation(gap=0.30)
    ha = _make_mock_ha(is_trap=True)  # 2차에서 trap 판정
    result = run_value_trigger(
        val, [_make_fundamentals()],
        price_change_pct=-0.15,
        heavy_agent=ha,
        mode=RunMode.FORWARD,
        prev_intrinsic_value=val.intrinsic_value * 1.2,  # 직전 내재가치 > 현재 → 동반 하락
    )
    assert result.verdict == ValueVerdict.VALUE_TRAP


# ── to_track_decision 변환 ────────────────────────────────────────────

def test_to_track_decision_opportunity():
    """OPPORTUNITY → decision=buy."""
    val = _make_valuation(gap=0.30)
    ha = _make_mock_ha(is_trap=False)
    result = run_value_trigger(
        val, [_make_fundamentals()],
        price_change_pct=-0.15,
        heavy_agent=ha,
        mode=RunMode.FORWARD,
    )
    decision = to_track_decision(result)
    assert decision["decision"] == "buy"
    assert "confidence" in decision


def test_to_track_decision_value_trap():
    """VALUE_TRAP → decision=hold."""
    val = _make_valuation(gap=0.30)
    ha = _make_mock_ha(is_trap=True)
    result = run_value_trigger(
        val, [_make_fundamentals()],
        price_change_pct=-0.15,
        heavy_agent=ha,
        mode=RunMode.FORWARD,
    )
    decision = to_track_decision(result)
    assert decision["decision"] == "hold"


def test_to_track_decision_reject():
    """REJECT → decision=hold."""
    val = _make_valuation(gap=0.30)
    result = run_value_trigger(val, [], price_change_pct=0.0)
    decision = to_track_decision(result)
    assert decision["decision"] == "hold"
