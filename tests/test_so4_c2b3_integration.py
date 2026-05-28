"""SO-4 통합 동작게이트: C2/B3 end-to-end 6종 + Phase 전 회귀 0.

검증기준:
① 캡 초과 → degrade(hold)
② 지연 초과 → degrade
③ 예외 → degrade
④ 같은 입력 → 같은 prompt_hash(결정성 재현)
⑤ 정상 → tier 라우팅 보존(급락-5%→deep/평상시→quick)
⑥ degrade hold ↔ risk_gate 무모순(관망=차단 아님 정상)
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.brain.llm_provider import LLMProvider, LLMRouter, RouteResult


def _mock_provider(tier: str = "quick", resp: str = "ok"):
    m = MagicMock(spec=LLMProvider)
    m.tier = tier
    m.model_id = f"mock-{tier}"
    m.generate.return_value = resp
    return m


def _router(tmp_path, cap=9999, budget=30.0, quick_resp="ok"):
    q = _mock_provider("quick", quick_resp)
    d = _mock_provider("deep", "deep_ok")
    return LLMRouter(
        quick=q, deep=d,
        daily_cap=cap,
        latency_budget=budget,
        counter_file=tmp_path / "c.json",
    ), q, d


# ── ① 캡 초과 → degrade(hold) ────────────────────────────────────────

def test_scenario_1_cap_degrade(tmp_path):
    """cap=0 → degraded=True + reason=cap + hold JSON."""
    router, q, _ = _router(tmp_path, cap=0)
    result = router.route_with_meta("prompt")
    assert result.degraded is True
    assert result.degrade_reason == "cap"
    data = json.loads(result.text)
    assert data.get("_c2_degraded") is True
    q.generate.assert_not_called()


# ── ② 지연 초과 → degrade ────────────────────────────────────────────

def test_scenario_2_latency_degrade(tmp_path):
    """지연 초과 → degraded + reason=latency."""
    q = _mock_provider("quick")
    q.generate.side_effect = lambda p, **kw: (time.sleep(0.05) or "ok")
    d = _mock_provider("deep")
    router = LLMRouter(
        quick=q, deep=d, daily_cap=9999,
        latency_budget=0.001, counter_file=tmp_path / "c.json",
    )
    result = router.route_with_meta("prompt")
    assert result.degraded is True
    assert result.degrade_reason == "latency"


# ── ③ 예외 → degrade ─────────────────────────────────────────────────

def test_scenario_3_exception_degrade(tmp_path):
    """provider 예외 → degraded + reason=error/quality."""
    q = _mock_provider("quick")
    q.generate.side_effect = RuntimeError("connection refused")
    router = LLMRouter(
        quick=q, deep=_mock_provider("deep"), daily_cap=9999,
        latency_budget=30.0, counter_file=tmp_path / "c.json",
    )
    result = router.route_with_meta("prompt")
    assert result.degraded is True
    assert result.degrade_reason in ("error", "quality")
    data = json.loads(result.text)
    assert data.get("_c2_degraded") is True


# ── ④ 같은 입력 → 같은 prompt_hash(결정성 재현) ─────────────────────

def test_scenario_4_prompt_hash_determinism(tmp_path):
    """같은 prompt 2회 → prompt_hash 완전 일치."""
    q = _mock_provider("quick")
    q.generate.return_value = "ok"
    router = LLMRouter(quick=q, deep=_mock_provider("deep"),
                       daily_cap=9999, counter_file=tmp_path / "c.json")

    prompt = "BTC market analysis request"
    r1 = router.route_with_meta(prompt)
    r2 = router.route_with_meta(prompt)
    assert r1.prompt_hash == r2.prompt_hash
    assert r1.prompt_hash != ""
    assert r1.model_id == r2.model_id


# ── ⑤ 정상 → tier 라우팅 보존 ───────────────────────────────────────

def test_scenario_5a_normal_quick(tmp_path):
    """평상시(급락 없음) → quick."""
    router, q, d = _router(tmp_path)
    result = router.route_with_meta("prompt", price_change_24h=0.0)
    assert result.degraded is False
    assert result.intended_tier == "quick"
    q.generate.assert_called_once()
    d.generate.assert_not_called()


def test_scenario_5b_crash_deep(tmp_path):
    """급락(-5%) → deep."""
    router, q, d = _router(tmp_path)
    result = router.route_with_meta("prompt", price_change_24h=-6.0)
    assert result.degraded is False
    assert result.intended_tier == "deep"
    d.generate.assert_called_once()
    q.generate.assert_not_called()


def test_scenario_5c_route_tuple_preserved(tmp_path):
    """route() 2-tuple tier = intended_tier (degrade 없는 정상)."""
    router, q, d = _router(tmp_path)
    text, tier = router.route("prompt", price_change_24h=0.0)
    assert tier == "quick"
    assert isinstance(text, str)


# ── ⑥ degrade hold ↔ risk_gate 무모순 ───────────────────────────────

def test_scenario_6_degrade_hold_no_risk_gate_conflict(tmp_path):
    """degrade hold(관망) 은 risk_gate 차단 아님 — 무모순."""
    from core.risk_gate import RiskGate, VerdictType

    # degrade → 관망 결정
    router, _, _ = _router(tmp_path, cap=0)
    result = router.route_with_meta("prompt")
    assert result.degraded is True

    degrade_text = json.loads(result.text)
    assert degrade_text.get("decision") == "관망"

    # risk_gate 에 hold/관망 제안 → approved(차단 아님)
    gate = RiskGate(min_holding_days=0)
    verdict = gate.check(
        cycle_id="degrade_test",
        action="hold",  # 관망=hold → risk_gate 스킵
        proposed_size=0,
        nav=100000,
    )
    assert verdict.verdict == VerdictType.APPROVED


# ── B3 3필드 RouteResult 채워짐 ─────────────────────────────────────

def test_b3_fields_populated_on_success(tmp_path):
    """정상 호출 시 model_id·prompt_hash·temperature 모두 채워짐."""
    q = _mock_provider("quick")
    q.generate.return_value = "ok"
    router = LLMRouter(quick=q, deep=_mock_provider("deep"),
                       daily_cap=9999, counter_file=tmp_path / "c.json")

    result = router.route_with_meta("test prompt", temperature=0.0)
    assert result.model_id != ""
    assert result.prompt_hash != ""
    assert isinstance(result.temperature, float)
    assert result.degraded is False


# ── Phase 전 회귀 테스트 ─────────────────────────────────────────────

def test_phase1_regression_llm_provider():
    """Phase 1 SO-1 llm_provider 16 tests 회귀 0."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_so1_llm_provider.py", "-q", "--tb=no"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"Phase1 회귀: {result.stdout[-400:]}"


def test_phase1_regression_llm_worker():
    """Phase 1 SO-6 llm_worker 15 tests 회귀 0."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_so6_llm_worker_router.py", "-q", "--tb=no"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"Phase1 SO-6 회귀: {result.stdout[-400:]}"


def test_phase_minus1_b1_regression():
    """Phase -1 B1 16 tests 회귀 0."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_b1_schema_hardgate.py", "-q", "--tb=no"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"Phase -1 회귀: {result.stdout[-400:]}"
