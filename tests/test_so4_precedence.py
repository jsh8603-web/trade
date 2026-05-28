"""SO-4 테스트: §6 precedence 격자 충돌 해소.

검증기준:
- 다중 규칙 동시발동 → 격자 순서로 halt 최우선 해소 PASS
- near_miss_veto 기록 PASS
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.risk_gate import (
    PrecedenceLevel,
    RiskVerdict,
    VerdictType,
    _RULE_PRECEDENCE,
    resolve_precedence,
)


# ── 격자 레벨 매핑 검증 ──────────────────────────────────────────────

def test_precedence_levels_ordered():
    """kill_switch < safety_stop < portfolio_cap < tax_holding < rebalance."""
    assert PrecedenceLevel.KILL_SWITCH < PrecedenceLevel.SAFETY_STOP
    assert PrecedenceLevel.SAFETY_STOP < PrecedenceLevel.PORTFOLIO_CAP
    assert PrecedenceLevel.PORTFOLIO_CAP < PrecedenceLevel.TAX_HOLDING
    assert PrecedenceLevel.TAX_HOLDING < PrecedenceLevel.REBALANCE


def test_rule_precedence_mapping():
    """핵심 규칙이 올바른 레벨에 매핑됨."""
    assert _RULE_PRECEDENCE["halt_propagation"] == PrecedenceLevel.KILL_SWITCH
    assert _RULE_PRECEDENCE["kill_switch_mdd"] == PrecedenceLevel.KILL_SWITCH
    assert _RULE_PRECEDENCE["daily_loss_halt"] == PrecedenceLevel.SAFETY_STOP
    assert _RULE_PRECEDENCE["per_pos_hard_stop"] == PrecedenceLevel.SAFETY_STOP
    assert _RULE_PRECEDENCE["corr_cap"] == PrecedenceLevel.PORTFOLIO_CAP
    assert _RULE_PRECEDENCE["max_weight_single"] == PrecedenceLevel.PORTFOLIO_CAP
    assert _RULE_PRECEDENCE["min_holding"] == PrecedenceLevel.TAX_HOLDING
    assert _RULE_PRECEDENCE["regime_flip"] == PrecedenceLevel.REBALANCE


# ── 단일 verdict 통과 ────────────────────────────────────────────────

def test_single_approved():
    v = RiskVerdict(VerdictType.APPROVED, "ok")
    result = resolve_precedence([v])
    assert result.verdict == VerdictType.APPROVED


def test_single_rejected():
    v = RiskVerdict(VerdictType.REJECTED, "halt", triggered_rules=["halt_propagation"])
    result = resolve_precedence([v])
    assert result.verdict == VerdictType.REJECTED


def test_empty_verdicts():
    result = resolve_precedence([])
    assert result.verdict == VerdictType.APPROVED


# ── 충돌 해소: halt 최우선 ───────────────────────────────────────────

def test_kill_switch_beats_min_holding():
    """kill switch halt + min_holding → kill switch 최우선."""
    halt = RiskVerdict(VerdictType.REJECTED, "halt", triggered_rules=["halt_propagation"])
    min_hold = RiskVerdict(VerdictType.REJECTED, "min_hold", triggered_rules=["min_holding"])
    result = resolve_precedence([min_hold, halt])
    assert result.verdict == VerdictType.REJECTED
    assert "halt_propagation" in result.triggered_rules


def test_kill_switch_beats_regime_flip():
    """kill switch + regime_flip → kill switch 우선."""
    halt = RiskVerdict(VerdictType.REJECTED, "mdd halt", triggered_rules=["kill_switch_mdd"])
    regime = RiskVerdict(VerdictType.REJECTED, "regime", triggered_rules=["regime_flip"])
    result = resolve_precedence([regime, halt])
    assert "kill_switch_mdd" in result.triggered_rules


def test_safety_stop_beats_portfolio_cap():
    """daily_loss_halt + max_weight_single → daily_loss 우선."""
    daily = RiskVerdict(VerdictType.REJECTED, "daily", triggered_rules=["daily_loss_halt"])
    weight = RiskVerdict(VerdictType.REJECTED, "weight", triggered_rules=["max_weight_single"])
    result = resolve_precedence([weight, daily])
    assert "daily_loss_halt" in result.triggered_rules


def test_precedence_conflict_main_case():
    """레짐flip + min_holding + kill switch halt 동시 → halt 최우선(rejected)."""
    halt = RiskVerdict(VerdictType.REJECTED, "halt", triggered_rules=["halt_propagation"])
    min_h = RiskVerdict(VerdictType.REJECTED, "min_hold", triggered_rules=["min_holding"])
    regime = RiskVerdict(VerdictType.REJECTED, "regime", triggered_rules=["regime_flip"])

    result = resolve_precedence([regime, min_h, halt])
    assert result.verdict == VerdictType.REJECTED
    assert "halt_propagation" in result.triggered_rules


# ── 충돌 해소: reduced 다중 → 최소 사이즈 ──────────────────────────

def test_multiple_reduced_takes_minimum():
    """다중 reduced → adjusted_size 최솟값."""
    r1 = RiskVerdict(VerdictType.REDUCED, "corr", adjusted_size=8000, triggered_rules=["corr_multiplier"])
    r2 = RiskVerdict(VerdictType.REDUCED, "weight", adjusted_size=5000, triggered_rules=["max_weight_single"])
    result = resolve_precedence([r1, r2])
    assert result.verdict == VerdictType.REDUCED
    assert result.adjusted_size == 5000


def test_rejected_beats_reduced():
    """rejected + reduced 혼합 → rejected 우선."""
    rej = RiskVerdict(VerdictType.REJECTED, "halt", triggered_rules=["halt_propagation"])
    red = RiskVerdict(VerdictType.REDUCED, "weight", adjusted_size=5000, triggered_rules=["max_weight_single"])
    result = resolve_precedence([red, rej])
    assert result.verdict == VerdictType.REJECTED


def test_all_approved():
    """전부 approved → approved."""
    a1 = RiskVerdict(VerdictType.APPROVED, "ok1")
    a2 = RiskVerdict(VerdictType.APPROVED, "ok2")
    result = resolve_precedence([a1, a2])
    assert result.verdict == VerdictType.APPROVED


# ── near_miss_veto 충돌 기록 ─────────────────────────────────────────

def test_precedence_conflict_veto_written(tmp_path, monkeypatch):
    """충돌 해소 시 near_miss_veto.jsonl 기록."""
    import core.risk_gate as rg
    monkeypatch.setattr(rg, "_LOG_DIR", tmp_path)

    halt = RiskVerdict(VerdictType.REJECTED, "halt", triggered_rules=["halt_propagation"])
    regime = RiskVerdict(VerdictType.REJECTED, "regime", triggered_rules=["regime_flip"])
    resolve_precedence([regime, halt], cycle_id="conflict_test")

    veto_file = tmp_path / "near_miss_veto.jsonl"
    assert veto_file.exists()
    entry = json.loads(veto_file.read_text(encoding="utf-8").strip())
    assert entry["rule"] == "precedence_conflict"
    assert "conflict_test" == entry["cycle_id"]


def test_no_conflict_veto_single_rule(tmp_path, monkeypatch):
    """단일 규칙 → 충돌 기록 없음."""
    import core.risk_gate as rg
    monkeypatch.setattr(rg, "_LOG_DIR", tmp_path)

    halt = RiskVerdict(VerdictType.REJECTED, "halt", triggered_rules=["halt_propagation"])
    resolve_precedence([halt], cycle_id="no_conflict")

    veto_file = tmp_path / "near_miss_veto.jsonl"
    assert not veto_file.exists()
