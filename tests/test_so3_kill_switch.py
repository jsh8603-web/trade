"""SO-3 테스트: KillSwitch MDD 상태머신.

검증기준:
- MDD 임계 초과 → 신규 halt + 청산 보류(자동청산 안 함) PASS
- confirm 시에만 청산 진행 PASS
- MDD 회복 → 해제(ACTIVE 복귀) PASS
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.risk_gate import KillSwitch, KillSwitchState, RiskGate, VerdictType


# ── 기본 구조 ────────────────────────────────────────────────────────

def test_kill_switch_initial_state():
    ks = KillSwitch()
    assert ks.state == KillSwitchState.ACTIVE
    assert ks.is_halted is False
    assert ks.alert_flag is False


def test_kill_switch_mdd_threshold_default():
    ks = KillSwitch()
    assert ks.mdd_threshold == -0.15


# ── MDD 초과 → HALTED ────────────────────────────────────────────────

def test_mdd_breach_transitions_to_halted():
    """MDD -16% → HALTED."""
    ks = KillSwitch(mdd_threshold=-0.15)
    state = ks.update_mdd(-0.16)
    assert state == KillSwitchState.HALTED
    assert ks.is_halted is True
    assert ks.alert_flag is True


def test_mdd_at_exact_threshold_halted():
    """MDD 정확히 임계 = HALTED (<=)."""
    ks = KillSwitch(mdd_threshold=-0.15)
    state = ks.update_mdd(-0.15)
    assert state == KillSwitchState.HALTED


def test_mdd_just_above_threshold_stays_active():
    """MDD -14.9% → ACTIVE 유지."""
    ks = KillSwitch(mdd_threshold=-0.15)
    state = ks.update_mdd(-0.149)
    assert state == KillSwitchState.ACTIVE
    assert ks.is_halted is False


# ── 자동청산 금지 — request_liquidation 후 confirm 필요 ──────────────

def test_no_auto_liquidation_on_halt():
    """HALTED 전이 시 자동 청산 안 함 (_pending_liquidation=False)."""
    ks = KillSwitch(mdd_threshold=-0.15)
    ks.update_mdd(-0.20)
    assert ks.state == KillSwitchState.HALTED
    # confirm 없이는 청산 불가
    result = ks.confirm()
    assert result is False  # CONFIRM_PENDING 아니므로 False


def test_request_liquidation_transitions_confirm_pending():
    """HALTED → request_liquidation() → CONFIRM_PENDING."""
    ks = KillSwitch(mdd_threshold=-0.15)
    ks.update_mdd(-0.20)
    assert ks.state == KillSwitchState.HALTED
    ok = ks.request_liquidation()
    assert ok is True
    assert ks.state == KillSwitchState.CONFIRM_PENDING


def test_confirm_only_from_confirm_pending():
    """HALTED 상태에서 직접 confirm() → False (CONFIRM_PENDING 아님)."""
    ks = KillSwitch(mdd_threshold=-0.15)
    ks.update_mdd(-0.20)
    # request_liquidation 없이 confirm
    result = ks.confirm()
    assert result is False


def test_confirm_after_request_succeeds():
    """request_liquidation → confirm → True (청산 허가)."""
    ks = KillSwitch(mdd_threshold=-0.15)
    ks.update_mdd(-0.20)
    ks.request_liquidation()
    result = ks.confirm()
    assert result is True


def test_request_liquidation_from_active_fails():
    """ACTIVE 상태에서 request_liquidation → False."""
    ks = KillSwitch()
    ok = ks.request_liquidation()
    assert ok is False


# ── MDD 회복 → ACTIVE 복귀 ─────────────────────────────────────────

def test_mdd_recovery_clears_halt():
    """MDD -16% → HALTED → MDD -10% 회복 → ACTIVE."""
    ks = KillSwitch(mdd_threshold=-0.15)
    ks.update_mdd(-0.16)
    assert ks.state == KillSwitchState.HALTED
    ks.update_mdd(-0.10)
    assert ks.state == KillSwitchState.ACTIVE
    assert ks.alert_flag is False
    assert ks.is_halted is False


def test_mdd_recovery_from_confirm_pending():
    """CONFIRM_PENDING 중에도 MDD 회복 → ACTIVE."""
    ks = KillSwitch(mdd_threshold=-0.15)
    ks.update_mdd(-0.20)
    ks.request_liquidation()
    assert ks.state == KillSwitchState.CONFIRM_PENDING
    ks.update_mdd(-0.05)  # 회복
    assert ks.state == KillSwitchState.ACTIVE


# ── near_miss_veto 기록 ──────────────────────────────────────────────

def test_kill_switch_veto_written_on_halt(tmp_path, monkeypatch):
    """MDD 초과 halt 시 near_miss_veto.jsonl 기록."""
    import core.risk_gate as rg
    import json
    monkeypatch.setattr(rg, "_LOG_DIR", tmp_path)

    ks = KillSwitch(mdd_threshold=-0.15)
    ks.update_mdd(-0.20, cycle_id="ks_veto_test")

    veto_file = tmp_path / "near_miss_veto.jsonl"
    assert veto_file.exists()
    entry = json.loads(veto_file.read_text(encoding="utf-8").strip())
    assert entry["event"] == "near_miss_veto"
    assert entry["rule"] == "kill_switch_mdd"
    assert "ks_veto_test" == entry["cycle_id"]


# ── RiskGate.check 에 is_halted 연동 ─────────────────────────────────

def test_risk_gate_halted_when_kill_switch_active():
    """KillSwitch 발동 후 is_halted=True → RiskGate.check 차단."""
    ks = KillSwitch(mdd_threshold=-0.15)
    ks.update_mdd(-0.20)

    gate = RiskGate()
    v = gate.check(
        cycle_id="ks_gate",
        action="buy",
        proposed_size=1000,
        is_halted=ks.is_halted,
        nav=100000,
    )
    assert v.verdict == VerdictType.REJECTED
    assert "halt_propagation" in v.triggered_rules


def test_risk_gate_not_halted_when_recovered():
    """KillSwitch 회복 후 is_halted=False → RiskGate 차단 없음."""
    ks = KillSwitch(mdd_threshold=-0.15)
    ks.update_mdd(-0.20)
    ks.update_mdd(-0.05)  # 회복

    gate = RiskGate(min_holding_days=0)
    v = gate.check(
        cycle_id="ks_recover",
        action="buy",
        proposed_size=100,
        is_halted=ks.is_halted,
        nav=100000,
        daily_loss_pct=-0.01,
    )
    assert "halt_propagation" not in v.triggered_rules
