"""SO-1 테스트: core/risk_gate.py RiskGate hard rule 결함주입.

검증기준:
- 일일손실 한도초과 → halt(rejected) PASS
- max weight 초과 → reduced(adjusted_size) PASS
- min_holding 위반 → rejected PASS
- per-position -5% soft stop PASS
- per-position -10% hard stop PASS
- 정상 거래 → approved PASS
- near_miss_veto jsonl 기록 어서션 PASS
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.risk_gate import RiskGate, RiskVerdict, VerdictType, _log_near_miss_veto


# ── 기본 구조 ────────────────────────────────────────────────────────

def test_import_ok():
    from core.risk_gate import RiskGate, RiskVerdict, VerdictType  # noqa: F401


def test_risk_gate_instantiation():
    gate = RiskGate()
    assert gate.soft_stop_pct == -5.0
    assert gate.hard_stop_pct == -10.0


def test_verdict_approved_property():
    v = RiskVerdict(VerdictType.APPROVED, "ok")
    assert v.approved is True

    v2 = RiskVerdict(VerdictType.REJECTED, "no")
    assert v2.approved is False


# ── hold 는 항상 approved ────────────────────────────────────────────

def test_hold_always_approved():
    gate = RiskGate()
    v = gate.check(cycle_id="c1", action="hold")
    assert v.verdict == VerdictType.APPROVED


# ── 일일 손실한도 초과 → halt(rejected) ────────────────────────────

def test_daily_loss_halt():
    gate = RiskGate(daily_loss_cap=-0.05)
    v = gate.check(
        cycle_id="c_daily",
        action="buy",
        proposed_size=1000,
        daily_loss_pct=-0.06,  # 초과
        nav=100000,
    )
    assert v.verdict == VerdictType.REJECTED
    assert "daily_loss_halt" in v.triggered_rules


def test_daily_loss_boundary_pass():
    gate = RiskGate(daily_loss_cap=-0.05)
    v = gate.check(
        cycle_id="c_pass",
        action="buy",
        proposed_size=1000,
        daily_loss_pct=-0.04,  # 한도 내
        nav=100000,
    )
    assert v.verdict != VerdictType.REJECTED or "daily_loss_halt" not in v.triggered_rules


# ── per-position -5% soft stop ───────────────────────────────────────

def test_soft_stop_rejects_buy():
    gate = RiskGate(soft_stop_pct=-5.0)
    v = gate.check(
        cycle_id="c_soft",
        action="buy",
        proposed_size=1000,
        position_pnl_pct=-0.06,  # -6% < -5%
        nav=100000,
    )
    assert v.verdict == VerdictType.REJECTED
    assert "per_pos_soft_stop" in v.triggered_rules


def test_soft_stop_allows_sell():
    """soft stop 은 매수만 차단, 매도는 허용."""
    gate = RiskGate(soft_stop_pct=-5.0, min_holding_days=0)
    v = gate.check(
        cycle_id="c_sell",
        action="sell",
        proposed_size=1000,
        position_pnl_pct=-0.06,
        holding_days=5,
        nav=100000,
    )
    assert "per_pos_soft_stop" not in v.triggered_rules


# ── per-position -10% hard stop ─────────────────────────────────────

def test_hard_stop_rejects():
    gate = RiskGate(hard_stop_pct=-10.0)
    v = gate.check(
        cycle_id="c_hard",
        action="sell",
        proposed_size=1000,
        position_pnl_pct=-0.11,  # -11% < -10%
        holding_days=10,
        nav=100000,
    )
    assert v.verdict == VerdictType.REJECTED
    assert "per_pos_hard_stop" in v.triggered_rules


def test_hard_stop_boundary():
    gate = RiskGate(hard_stop_pct=-10.0, min_holding_days=0)
    v = gate.check(
        cycle_id="c_hb",
        action="sell",
        proposed_size=1000,
        position_pnl_pct=-0.09,  # -9% > -10% → 통과
        holding_days=5,
        nav=100000,
    )
    assert "per_pos_hard_stop" not in v.triggered_rules


# ── min_holding 위반 → rejected ─────────────────────────────────────

def test_min_holding_rejects():
    gate = RiskGate(min_holding_days=3)
    v = gate.check(
        cycle_id="c_hold",
        action="sell",
        proposed_size=1000,
        holding_days=1,  # 1일 < 3일
        nav=100000,
    )
    assert v.verdict == VerdictType.REJECTED
    assert "min_holding" in v.triggered_rules


def test_min_holding_passes():
    gate = RiskGate(min_holding_days=3)
    v = gate.check(
        cycle_id="c_hold_ok",
        action="sell",
        proposed_size=1000,
        holding_days=3,  # 정확히 3일
        nav=100000,
    )
    assert "min_holding" not in v.triggered_rules


# ── max weight 초과 → reduced ────────────────────────────────────────

def test_max_weight_reduces():
    gate = RiskGate(max_weight_single=0.10)
    # 현 비중 0.08 + 제안 0.05 = 0.13 > 0.10 → 축소
    v = gate.check(
        cycle_id="c_weight",
        action="buy",
        proposed_size=5000,
        current_weight=0.08,
        nav=100000,
    )
    assert v.verdict == VerdictType.REDUCED
    assert "max_weight_single" in v.triggered_rules
    assert v.adjusted_size is not None
    assert v.adjusted_size < 5000


def test_max_weight_rejects_when_full():
    """현 비중이 이미 max → 완전 차단."""
    gate = RiskGate(max_weight_single=0.10)
    v = gate.check(
        cycle_id="c_full",
        action="buy",
        proposed_size=5000,
        current_weight=0.10,  # 이미 최대
        nav=100000,
    )
    assert v.verdict == VerdictType.REJECTED


# ── is_halted 전달 ───────────────────────────────────────────────────

def test_halted_rejects_all():
    gate = RiskGate()
    v = gate.check(cycle_id="c_halt", action="buy", proposed_size=1000, is_halted=True, nav=100000)
    assert v.verdict == VerdictType.REJECTED
    assert "halt_propagation" in v.triggered_rules


# ── 정상 거래 → approved ─────────────────────────────────────────────

def test_normal_trade_approved():
    gate = RiskGate(min_holding_days=0)
    v = gate.check(
        cycle_id="c_ok",
        action="buy",
        proposed_size=500,
        position_pnl_pct=0.02,  # +2%
        holding_days=5,
        current_weight=0.03,
        sector_weight=0.05,
        nav=100000,
        daily_loss_pct=-0.01,
    )
    assert v.verdict == VerdictType.APPROVED
    assert v.approved is True


# ── near_miss_veto jsonl 기록 어서션 ────────────────────────────────

def test_near_miss_veto_written_on_reject(tmp_path, monkeypatch):
    """거절 시 near_miss_veto.jsonl 에 기록."""
    import core.risk_gate as rg
    monkeypatch.setattr(rg, "_LOG_DIR", tmp_path)

    gate = RiskGate(daily_loss_cap=-0.05)
    gate.check(
        cycle_id="veto_test",
        action="buy",
        proposed_size=1000,
        daily_loss_pct=-0.10,
        nav=100000,
    )

    veto_file = tmp_path / "near_miss_veto.jsonl"
    assert veto_file.exists(), "near_miss_veto.jsonl 미생성"
    lines = veto_file.read_text(encoding="utf-8").strip().split("\n")
    entry = json.loads(lines[-1])
    assert entry["event"] == "near_miss_veto"
    assert entry["cycle_id"] == "veto_test"
    assert "reason" in entry
    assert "timestamp" in entry


def test_near_miss_veto_on_reduced(tmp_path, monkeypatch):
    """축소 시도도 near_miss_veto 기록."""
    import core.risk_gate as rg
    monkeypatch.setattr(rg, "_LOG_DIR", tmp_path)

    gate = RiskGate(max_weight_single=0.10)
    gate.check(
        cycle_id="reduce_test",
        action="buy",
        proposed_size=5000,
        current_weight=0.08,
        nav=100000,
    )
    veto_file = tmp_path / "near_miss_veto.jsonl"
    assert veto_file.exists()


def test_no_veto_on_approved(tmp_path, monkeypatch):
    """정상 승인 시 veto 미기록."""
    import core.risk_gate as rg
    monkeypatch.setattr(rg, "_LOG_DIR", tmp_path)

    gate = RiskGate(min_holding_days=0)
    gate.check(
        cycle_id="approved_test",
        action="buy",
        proposed_size=100,
        nav=100000,
        daily_loss_pct=-0.01,
    )
    veto_file = tmp_path / "near_miss_veto.jsonl"
    assert not veto_file.exists()


# ── LLM import 0 확인 ────────────────────────────────────────────────

def test_risk_gate_no_llm_imports():
    """risk_gate.py 가 LLM/anthropic/gemini 를 import 하지 않음."""
    src = (PROJECT_ROOT / "core" / "risk_gate.py").read_text(encoding="utf-8")
    assert "anthropic" not in src
    assert "gemini" not in src.lower()
    assert "openai" not in src
    assert "llm_provider" not in src
