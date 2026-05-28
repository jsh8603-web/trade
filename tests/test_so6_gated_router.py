"""SO-6 테스트: 우회불가 백스톱 + 프로세스 격리 + 5종 결함주입 통합.

검증기준:
- LLM 우회 시도(risk_gate 미경유 주문) → 실패(백스톱 차단) PASS
- risk_gate import 그래프에 LLM 의존 0 PASS
- 5종 결함주입 전부 near_miss_veto 기록 PASS
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
    GatedOrderRouter,
    KillSwitch,
    RiskGate,
    VerdictType,
)


# ── GatedOrderRouter 기본 ────────────────────────────────────────────

def test_gated_router_instantiation():
    router = GatedOrderRouter()
    assert router.bypassed_attempts == 0


def test_gated_router_bypass_rejected():
    """via_gate=False(우회) → REJECTED."""
    router = GatedOrderRouter()
    v = router.submit({"action": "buy"}, cycle_id="bypass_test", via_gate=False)
    assert v.verdict == VerdictType.REJECTED
    assert "bypass_attempt" in v.triggered_rules
    assert router.bypassed_attempts == 1


def test_gated_router_bypass_count_increments():
    """우회 횟수 카운터."""
    router = GatedOrderRouter()
    router.submit({}, via_gate=False)
    router.submit({}, via_gate=False)
    assert router.bypassed_attempts == 2


def test_gated_router_via_gate_approved():
    """via_gate=True + 정상 조건 → approved."""
    gate = RiskGate(min_holding_days=0)
    router = GatedOrderRouter(gate=gate)
    v = router.submit(
        {"action": "buy"},
        via_gate=True,
        cycle_id="ok",
        action="buy",
        proposed_size=100,
        nav=100000,
        daily_loss_pct=-0.01,
    )
    assert v.verdict == VerdictType.APPROVED


def test_gated_router_kill_switch_propagation():
    """KillSwitch HALTED → router 차단."""
    ks = KillSwitch(mdd_threshold=-0.15)
    ks.update_mdd(-0.20)
    router = GatedOrderRouter(kill_switch=ks)
    v = router.submit(
        {"action": "buy"},
        via_gate=True,
        cycle_id="ks_test",
        action="buy",
        proposed_size=1000,
        nav=100000,
    )
    assert v.verdict == VerdictType.REJECTED


# ── 5종 결함주입 통합 near_miss_veto ────────────────────────────────

def test_5_fault_injections_all_near_miss_veto(tmp_path, monkeypatch):
    """5종 결함주입 → 모두 near_miss_veto.jsonl 기록."""
    import core.risk_gate as rg
    monkeypatch.setattr(rg, "_LOG_DIR", tmp_path)

    gate = RiskGate(
        daily_loss_cap=-0.05,
        max_weight_single=0.10,
        corr_cap=0.7,
    )
    ks = KillSwitch(mdd_threshold=-0.15)
    router = GatedOrderRouter(gate=gate, kill_switch=ks)

    # ① 일일손실 → halt
    router.submit({}, via_gate=True, cycle_id="fault1", action="buy",
                  proposed_size=1000, daily_loss_pct=-0.10, nav=100000)

    # ② corr 0.7 초과 → 차단
    router.submit({}, via_gate=True, cycle_id="fault2", action="buy",
                  proposed_size=1000, avg_correlation=0.80, nav=100000,
                  daily_loss_pct=-0.01)

    # ③ max weight → 축소
    router.submit({}, via_gate=True, cycle_id="fault3", action="buy",
                  proposed_size=50000, current_weight=0.08, nav=100000,
                  daily_loss_pct=-0.01)

    # ④ MDD halt (KillSwitch 경유)
    ks.update_mdd(-0.20, cycle_id="fault4")

    # ⑤ LLM 우회 시도 → 차단
    router.submit({}, via_gate=False, cycle_id="fault5")

    veto_file = tmp_path / "near_miss_veto.jsonl"
    assert veto_file.exists(), "near_miss_veto.jsonl 미생성"

    lines = veto_file.read_text(encoding="utf-8").strip().split("\n")
    entries = [json.loads(l) for l in lines]
    rules = {e["rule"] for e in entries}

    assert "daily_loss_halt"  in rules, f"① 일일손실 미기록: {rules}"
    assert "corr_cap"         in rules, f"② corr 초과 미기록: {rules}"
    assert "max_weight_single" in rules or "corr_multiplier" in rules or any("weight" in r for r in rules), \
        f"③ max weight 미기록: {rules}"
    assert "kill_switch_mdd"  in rules, f"④ MDD halt 미기록: {rules}"
    assert "bypass_attempt"   in rules, f"⑤ LLM 우회 미기록: {rules}"


# ── 5종 결함주입 verdict 확인 ────────────────────────────────────────

def test_fault_1_daily_loss_rejected():
    """① 일일손실 → rejected."""
    router = GatedOrderRouter(gate=RiskGate(daily_loss_cap=-0.05))
    v = router.submit({}, via_gate=True, action="buy",
                      proposed_size=1000, daily_loss_pct=-0.10, nav=100000)
    assert v.verdict == VerdictType.REJECTED
    assert "daily_loss_halt" in v.triggered_rules


def test_fault_2_corr_rejected():
    """② corr > 0.7 → rejected."""
    router = GatedOrderRouter(gate=RiskGate(corr_cap=0.7))
    v = router.submit({}, via_gate=True, action="buy",
                      proposed_size=1000, avg_correlation=0.80,
                      nav=100000, daily_loss_pct=-0.01)
    assert v.verdict == VerdictType.REJECTED
    assert "corr_cap" in v.triggered_rules


def test_fault_3_max_weight_reduced():
    """③ max weight → reduced(adjusted_size)."""
    router = GatedOrderRouter(gate=RiskGate(max_weight_single=0.10))
    v = router.submit({}, via_gate=True, action="buy",
                      proposed_size=5000, current_weight=0.08,
                      nav=100000, daily_loss_pct=-0.01)
    assert v.verdict == VerdictType.REDUCED
    assert v.adjusted_size is not None and v.adjusted_size < 5000


def test_fault_4_mdd_halt():
    """④ MDD 초과 → KillSwitch HALTED → router 차단."""
    ks = KillSwitch(mdd_threshold=-0.15)
    ks.update_mdd(-0.20)
    router = GatedOrderRouter(kill_switch=ks)
    v = router.submit({}, via_gate=True, action="buy",
                      proposed_size=1000, nav=100000)
    assert v.verdict == VerdictType.REJECTED
    assert "halt_propagation" in v.triggered_rules


def test_fault_5_llm_bypass():
    """⑤ LLM 우회 → rejected(bypass_attempt)."""
    router = GatedOrderRouter()
    v = router.submit({"action": "buy"}, via_gate=False)
    assert v.verdict == VerdictType.REJECTED
    assert "bypass_attempt" in v.triggered_rules


# ── LLM import 0 (프로세스 격리 검증) ────────────────────────────────

def test_risk_gate_no_llm_imports():
    """core/risk_gate.py LLM/anthropic/gemini import 0."""
    src = (PROJECT_ROOT / "core" / "risk_gate.py").read_text(encoding="utf-8")
    assert "anthropic" not in src
    assert "gemini" not in src.lower()
    assert "openai" not in src
    assert "llm_provider" not in src
    assert "import google" not in src


def test_risk_sizing_no_llm_imports():
    """core/risk_sizing.py LLM import 0."""
    src = (PROJECT_ROOT / "core" / "risk_sizing.py").read_text(encoding="utf-8")
    assert "anthropic" not in src
    assert "llm_provider" not in src


# ── Phase -1/0/1 회귀 (핵심 테스트 파일들) ─────────────────────────

def test_phase_minus1_b1_regression():
    """Phase -1 B1 스키마 하드게이트 회귀 0."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_b1_schema_hardgate.py", "-q", "--tb=no"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"B1 회귀 발생: {result.stdout[-500:]}"


def test_phase2_so1_regression():
    """Phase 2 SO-1 기존 테스트 회귀 0."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_so1_risk_gate.py", "-q", "--tb=no"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"SO-1 회귀: {result.stdout[-500:]}"
