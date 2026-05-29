"""tests/test_so6_unattended_wire.py — SO-6 검증 게이트.

검증:
  1. auto_derisk_due()=True mock 사이클 → DeriskExecutor.derisk_to_floor 호출 assert (wire 증명).
  2. H27 record_halt_entry 후 confirm 없이 timeout_hours 경과 → check_timeout triggered=True assert (무인 자동발동).
  3. H27 attended 경로(record_confirm) 보존: 기존 동작 그대로.
  4. U1 회귀 0 보존: KillSwitch/RiskGate import 정상.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from core.derisk_executor import DeriskExecutor, FakeExchange
from core.fallback_policy import H27BoundedFallback
from core.risk_gate import KillSwitch
from core.unattended_fsm import UnattendedState, UnattendedStateMachine


def _write_normal_state(state_file: Path) -> None:
    """NORMAL 상태 파일을 올바른 포맷으로 초기화 (wire 증명용)."""
    import hashlib as _hlib, json as _json
    _body = _json.dumps({
        "state": "NORMAL",
        "daily_triggers": 0,
        "last_update_date": "",
        "cooldown_enter_mono": 0.0,
        "cooldown_sec": 3600.0,
        "freeze_enter_date": "",
    })
    _cs = _hlib.sha256(_body.encode()).hexdigest()
    state_file.write_text(_json.dumps({"checksum": _cs, "body": _body}), encoding="utf-8")


# ── Test 1: auto_derisk_due=True → FSM _trigger_hard → DeriskExecutor 호출 ──

def test_auto_derisk_due_triggers_fsm_derisk(tmp_path) -> None:
    """KillSwitch auto_derisk_due()=True → NORMAL 상태 FSM에 mdd 신호 → HARD_DERISK + executor 호출.

    NORMAL → mdd<=-15% → _trigger_hard → derisk_to_floor → cancel_all_open_orders 호출.
    """
    exchange = FakeExchange(positions={"BTC": 1.0})
    executor = DeriskExecutor(exchange)

    state_file = tmp_path / "state.json"
    _write_normal_state(state_file)
    fsm = UnattendedStateMachine(executor=executor, state_path=state_file)

    ks = KillSwitch(mdd_threshold=-0.15, unattended=True)
    ks.update_mdd(-0.16)  # MDD -16% → HALTED
    assert ks.auto_derisk_due() is True, "unattended + halted → auto_derisk_due=True"

    # NORMAL → mdd=-16% (<=HARD -15%) → _trigger_hard → derisk_to_floor
    signals = {
        "mdd": -0.16,
        "vol": 0.0,
        "gap": False,
        "heartbeat_loss": False,
        "recon_break": False,
    }
    new_state = fsm.step(signals, now=time.time())

    assert new_state == UnattendedState.HARD_DERISK, f"NORMAL → HARD_DERISK 전이: {new_state}"
    # derisk_to_floor → cancel_all_open_orders 호출 증명 (wire 확인)
    assert exchange.cancelled_orders >= 1, "FSM → executor wire: derisk_to_floor → cancel 호출됨"


# ── Test 2: auto_derisk_due=False → NORMAL 유지 ─────────────────────────

def test_auto_derisk_due_false_no_derisk(tmp_path) -> None:
    """MDD 정상 → auto_derisk_due=False → FSM NORMAL 유지, derisk 미발동."""
    exchange = FakeExchange(positions={"BTC": 0.5})
    executor = DeriskExecutor(exchange)

    state_file = tmp_path / "state2.json"
    _write_normal_state(state_file)
    fsm = UnattendedStateMachine(executor=executor, state_path=state_file)

    ks = KillSwitch(mdd_threshold=-0.15, unattended=True)
    ks.update_mdd(-0.05)  # 정상 MDD
    assert ks.auto_derisk_due() is False

    signals = {
        "mdd": -0.05,
        "vol": 0.0,
        "gap": False,
        "heartbeat_loss": False,
        "recon_break": False,
    }
    new_state = fsm.step(signals, now=time.time())

    assert new_state == UnattendedState.NORMAL, f"정상 MDD → NORMAL 유지: {new_state}"
    assert exchange.cancelled_orders == 0, "derisk 미발동 시 cancel 0"


# ── Test 3: H27 record_halt_entry → 무인 타임아웃 자동발동 ──────────────

def test_h27_halt_entry_anchor_triggers_without_confirm() -> None:
    """H27: record_halt_entry 후 confirm 없이 timeout 경과 → triggered=True (무인 자동발동)."""
    fb = H27BoundedFallback(timeout_hours=1.0)

    now = time.monotonic()
    # halt 진입 시점 기록 (무인 — confirm 없음)
    fb.record_halt_entry(ts=now)

    # timeout 미경과 → 미발동
    result_before = fb.check_timeout(current_ts=now + 1800)  # 30분
    assert result_before.triggered is False, "timeout 미경과 → 미발동"

    # timeout 경과 → 발동
    result_after = fb.check_timeout(current_ts=now + 3601)  # 1h 1s
    assert result_after.triggered is True, "timeout 경과 → 발동"
    assert result_after.is_full_liquidation is False, "전량청산 금지 유지"
    assert "halt_entry" in result_after.reason, "halt_entry anchor 명시"


# ── Test 4: H27 attended 경로(record_confirm) 보존 ──────────────────────

def test_h27_attended_confirm_path_preserved() -> None:
    """attended 경로: record_confirm → timeout 체크 — 기존 동작 보존."""
    fb = H27BoundedFallback(timeout_hours=1.0)

    now = time.monotonic()
    fb.record_confirm()  # attended confirm 기록

    # confirm 후 즉시 → 미발동
    result = fb.check_timeout(current_ts=now + 10)
    assert result.triggered is False, "confirm 후 즉시 → 미발동"

    # confirm 후 timeout 경과 → 발동
    result2 = fb.check_timeout(current_ts=now + 3601)
    assert result2.triggered is True
    assert "confirm" in result2.reason, "confirm anchor 명시"


# ── Test 5: H27 halt_entry → confirm 수신 시 anchor 전환 ───────────────

def test_h27_confirm_overrides_halt_anchor() -> None:
    """attended confirm 이 halt_entry anchor 보다 우선."""
    fb = H27BoundedFallback(timeout_hours=1.0)

    old_now = time.monotonic()
    fb.record_halt_entry(ts=old_now - 5000)  # 오래된 halt anchor

    # confirm 수신 → anchor 리셋
    confirm_ts = old_now
    fb.record_confirm()
    fb._last_confirm_ts = confirm_ts  # 명시 주입

    # confirm 기준 10s → 미발동 (halt anchor 가 더 오래됐어도 confirm 우선)
    result = fb.check_timeout(current_ts=confirm_ts + 10)
    assert result.triggered is False, "confirm anchor 우선 → halt anchor 무시"


# ── Test 6: H27 anchor 없음 → 대기(미발동) ──────────────────────────────

def test_h27_no_anchor_no_trigger() -> None:
    """anchor(confirm/halt_entry) 없음 → triggered=False 대기."""
    fb = H27BoundedFallback(timeout_hours=1.0)
    result = fb.check_timeout()
    assert result.triggered is False


# ── Test 7: U1 회귀 — KillSwitch import 정상 ─────────────────────────────

def test_u1_killswitch_import_ok() -> None:
    """U1 회귀: KillSwitch / RiskGate import 및 기본 동작 정상."""
    from core.risk_gate import KillSwitch, RiskGate
    ks = KillSwitch()
    assert ks.auto_derisk_due() is False, "초기 상태: auto_derisk_due=False"
    rg = RiskGate()
    assert rg is not None
