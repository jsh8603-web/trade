"""tests/test_unattended_phase_gate_patch.py — Phase Gate 리뷰 패치 효과 검증.

E2E 검사 중 Phase Gate 3 reviewer(보안/품질/성능) 발견사항을 패치한 뒤,
그 동작이 실제로 의도대로 작동하는지 증명(E95 효과 검증).

검증 패치:
  1. FSM infra_hard (heartbeat_loss/recon_break) → COOLDOWN/RE_ARM_EVAL 중에도 즉시 재집행 (품질 P0)
  2. FSM mdd_hard 재급락 → COOLDOWN 중 재집행 안 함 (whipsawing 방지, 보안 절충)
  3. FSM cooldown backoff → MAX_COOLDOWN_SEC 상한 (성능·품질)
  4. DeriskExecutor frozen_bag 재시작 복구 (_load_frozen_bag, 보안 P0)
"""
from __future__ import annotations

import json

import pytest

from core.unattended_fsm import (
    UnattendedStateMachine,
    UnattendedState,
    MAX_COOLDOWN_SEC,
)

WALL = 1_700_000_000.0


class _SpyExecutor:
    def __init__(self):
        self.derisk_calls = []
        self.cancel_calls = []
        self.entry_cleared = 0

    def derisk_to_floor(self, floors, reason="", now=0.0):
        self.derisk_calls.append({"reason": reason, "now": now})

    def cancel_only(self, reason=""):
        self.cancel_calls.append(reason)

    def clear_entry_block(self):
        self.entry_cleared += 1


def _make_fsm(tmp_path, mono_start=1000.0):
    ex = _SpyExecutor()
    mono = [mono_start]
    fsm = UnattendedStateMachine(
        ex,
        state_path=tmp_path / "st.json",
        floors={"BTC": 0.0},
        _mono_fn=lambda: mono[0],
    )
    return fsm, ex, mono


class TestInfraHardRetrigger:
    def test_heartbeat_loss_retriggers_during_cooldown(self, tmp_path):
        """COOLDOWN 중 봇 정지(heartbeat_loss) → 즉시 de-risk 재집행 (인프라 위험)."""
        fsm, ex, _ = _make_fsm(tmp_path)
        fsm.step({"mdd": -0.20}, now=WALL)                 # NORMAL → HARD_DERISK
        assert fsm.state == UnattendedState.HARD_DERISK
        fsm.step({"mdd": -0.01}, now=WALL)                 # 해소 → COOLDOWN
        assert fsm.state == UnattendedState.COOLDOWN
        n_before = len(ex.derisk_calls)
        s = fsm.step({"mdd": -0.01, "heartbeat_loss": True}, now=WALL)
        assert s == UnattendedState.HARD_DERISK
        assert len(ex.derisk_calls) == n_before + 1

    def test_recon_break_retriggers_during_cooldown(self, tmp_path):
        """COOLDOWN 중 장부 불일치(recon_break) → 즉시 de-risk 재집행."""
        fsm, ex, _ = _make_fsm(tmp_path)
        fsm.step({"mdd": -0.20}, now=WALL)
        fsm.step({"mdd": -0.01}, now=WALL)
        assert fsm.state == UnattendedState.COOLDOWN
        n_before = len(ex.derisk_calls)
        s = fsm.step({"mdd": -0.01, "recon_break": True}, now=WALL)
        assert s == UnattendedState.HARD_DERISK
        assert len(ex.derisk_calls) == n_before + 1

    def test_mdd_hard_does_not_retrigger_during_cooldown(self, tmp_path):
        """시장 재급락(mdd)만으로는 COOLDOWN 중 재집행 안 함 (whipsawing 방지)."""
        fsm, ex, _ = _make_fsm(tmp_path)
        fsm.step({"mdd": -0.20}, now=WALL)
        fsm.step({"mdd": -0.01}, now=WALL)
        assert fsm.state == UnattendedState.COOLDOWN
        n_before = len(ex.derisk_calls)
        fsm.step({"mdd": -0.20}, now=WALL)                 # 시장 재급락만
        assert len(ex.derisk_calls) == n_before           # 재집행 없음
        assert fsm.state == UnattendedState.COOLDOWN


class TestCooldownCap:
    def test_cooldown_never_exceeds_max(self, tmp_path):
        """daily_triggers 가 커도 backoff 가 MAX_COOLDOWN_SEC 를 넘지 않음."""
        fsm, _, _ = _make_fsm(tmp_path)
        fsm._st.daily_triggers = 20                        # 2^19 시도
        assert fsm._calc_cooldown_sec() <= MAX_COOLDOWN_SEC


class TestFrozenBagRecovery:
    def test_load_frozen_bag_on_restart(self, tmp_path):
        """재시작 시 frozen_bag JSONL 을 읽어 _frozen_symbols 복구 + entry block."""
        from core.derisk_executor import DeriskExecutor, FakeExchange

        fp = tmp_path / "frozen_bag.json"
        fp.write_text(
            json.dumps([{"symbol": "BTC", "qty": 0.5, "ts": 1.0, "reason": "test"}])
        )
        ex = DeriskExecutor(FakeExchange(), frozen_path=fp)
        assert "BTC" in ex._frozen_symbols
        assert ex._entry_blocked

    def test_no_frozen_file_keeps_empty(self, tmp_path):
        """frozen 파일 없으면 빈 set 유지 (fail-safe)."""
        from core.derisk_executor import DeriskExecutor, FakeExchange

        ex = DeriskExecutor(FakeExchange(), frozen_path=tmp_path / "none.json")
        assert ex._frozen_symbols == set()
        assert not ex._entry_blocked
