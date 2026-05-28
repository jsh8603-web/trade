"""SO-2 테스트: LLMRouter C2 지연예산 + degrade heuristic(H14) + provider 예외 catch.

검증기준:
- 지연 초과(mock provider sleep) → degraded hold + reason=latency PASS
- 캡 초과 → degraded + reason=cap(resource 구분) PASS
- provider raise → degraded + reason=error PASS
- degrade 시 매수 아닌 hold/관망 의미 반환 PASS
- 정상 → degraded=False PASS
- 모순1 최소훅: degrade_reason quality vs resource 구분 PASS
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.brain.llm_provider import (
    LLMProvider,
    LLMRouter,
    RouteResult,
)


def _make_mock(response: str = "ok", tier: str = "quick"):
    m = MagicMock(spec=LLMProvider)
    m.tier = tier
    m.generate.return_value = response
    m.model_id = f"mock-{tier}"
    return m


def _router(tmp_path, cap=9999, budget=30.0, quick_resp="ok"):
    q = _make_mock(quick_resp, "quick")
    d = _make_mock("deep_ok", "deep")
    return LLMRouter(
        quick=q, deep=d,
        daily_cap=cap,
        latency_budget=budget,
        counter_file=tmp_path / "c.json",
    ), q, d


# ── 정상 → degraded=False ────────────────────────────────────────────

def test_normal_not_degraded(tmp_path):
    router, q, _ = _router(tmp_path)
    result = router.route_with_meta("hello")
    assert result.degraded is False
    assert result.degrade_reason == ""
    assert result.text == "ok"
    q.generate.assert_called_once()


# ── 캡 초과 → reason=cap (resource) ─────────────────────────────────

def test_cap_degrade_reason_cap(tmp_path):
    """캡 초과 → degrade_reason=cap."""
    router, q, _ = _router(tmp_path, cap=0)
    result = router.route_with_meta("test")
    assert result.degraded is True
    assert result.degrade_reason == "cap"
    q.generate.assert_not_called()


def test_cap_degrade_hold_content(tmp_path):
    """캡 degrade 텍스트 = hold/관망 의미."""
    router, _, _ = _router(tmp_path, cap=0)
    result = router.route_with_meta("test")
    data = json.loads(result.text)
    # H14: 매수 degrade = abstain(hold)
    assert data.get("decision") == "관망" or data.get("recommended_action") == "hold"
    assert data.get("_c2_degraded") is True
    assert data.get("_c2_reason") == "cap"


# ── 지연 초과 → reason=latency ───────────────────────────────────────

def test_latency_degrade(tmp_path):
    """지연 초과(budget=0.001s) → degraded + reason=latency."""
    q = _make_mock("slow_response", "quick")

    def slow_generate(prompt, **kwargs):
        time.sleep(0.05)  # 50ms
        return "should_not_reach"

    q.generate.side_effect = slow_generate
    d = _make_mock("deep_ok", "deep")
    router = LLMRouter(
        quick=q, deep=d,
        daily_cap=9999,
        latency_budget=0.001,  # 1ms — 확실히 초과
        counter_file=tmp_path / "c.json",
    )
    result = router.route_with_meta("test prompt")
    assert result.degraded is True
    assert result.degrade_reason == "latency"
    assert result.tier == "degraded"


def test_latency_degrade_hold_content(tmp_path):
    """지연 degrade 텍스트 = hold 의미."""
    q = _make_mock("ok", "quick")

    def slow(prompt, **kwargs):
        time.sleep(0.05)
        return "ok"

    q.generate.side_effect = slow
    router = LLMRouter(
        quick=q, deep=_make_mock(), daily_cap=9999,
        latency_budget=0.001, counter_file=tmp_path / "c.json",
    )
    result = router.route_with_meta("test")
    data = json.loads(result.text)
    assert data.get("_c2_degraded") is True
    assert data.get("_c2_reason") == "latency"


# ── provider 예외 → reason=error ─────────────────────────────────────

def test_provider_exception_degrade(tmp_path):
    """provider raise RuntimeError → degraded + reason=error."""
    q = _make_mock("ok", "quick")
    q.generate.side_effect = RuntimeError("connection refused")
    router = LLMRouter(
        quick=q, deep=_make_mock(), daily_cap=9999,
        latency_budget=30.0, counter_file=tmp_path / "c.json",
    )
    result = router.route_with_meta("test")
    assert result.degraded is True
    assert result.degrade_reason in ("error", "quality")


def test_provider_exception_hold_content(tmp_path):
    """예외 degrade = hold 의미 JSON."""
    q = _make_mock("ok", "quick")
    q.generate.side_effect = RuntimeError("timeout")
    router = LLMRouter(
        quick=q, deep=_make_mock(), daily_cap=9999,
        latency_budget=30.0, counter_file=tmp_path / "c.json",
    )
    result = router.route_with_meta("test")
    data = json.loads(result.text)
    assert data.get("_c2_degraded") is True


# ── 모순1 최소훅: quality vs resource 구분 ────────────────────────────

def test_degrade_reason_not_silent(tmp_path):
    """degrade 시 reason 항상 비어있지 않음(silent degrade 금지)."""
    # cap degrade
    router1, _, _ = _router(tmp_path / "a", cap=0)
    r1 = router1.route_with_meta("p")
    assert r1.degrade_reason != "", "silent degrade: reason 비어있음(cap)"

    # latency degrade
    q = _make_mock("ok", "quick")
    q.generate.side_effect = lambda p, **kw: (time.sleep(0.05) or "ok")
    router2 = LLMRouter(
        quick=q, deep=_make_mock(), daily_cap=9999,
        latency_budget=0.001, counter_file=tmp_path / "b" / "c.json",
    )
    r2 = router2.route_with_meta("p")
    assert r2.degrade_reason != "", "silent degrade: reason 비어있음(latency)"


def test_resource_vs_quality_reason_distinct(tmp_path):
    """cap/latency = resource계열, 그 외 = quality/error — 분류 가능."""
    resource_reasons = {"cap", "latency", "error"}
    # cap
    router, _, _ = _router(tmp_path / "a", cap=0)
    r = router.route_with_meta("p")
    assert r.degrade_reason in resource_reasons, f"cap은 resource: {r.degrade_reason}"

    # latency
    q2 = _make_mock("ok", "quick")
    q2.generate.side_effect = lambda p, **kw: (time.sleep(0.05) or "ok")
    router2 = LLMRouter(
        quick=q2, deep=_make_mock(), daily_cap=9999,
        latency_budget=0.001, counter_file=tmp_path / "b" / "c.json",
    )
    r2 = router2.route_with_meta("p")
    assert r2.degrade_reason in resource_reasons, f"latency는 resource: {r2.degrade_reason}"


# ── 지연 초과 후 카운터 +1 확인 ─────────────────────────────────────

def test_latency_degrade_increments_counter(tmp_path):
    """지연 초과 degrade 시에도 카운터 +1."""
    from core.brain.llm_provider import _load_c2_counter, _kst_today

    q = _make_mock("ok", "quick")
    q.generate.side_effect = lambda p, **kw: (time.sleep(0.05) or "ok")
    cf = tmp_path / "c.json"
    router = LLMRouter(
        quick=q, deep=_make_mock(), daily_cap=9999,
        latency_budget=0.001, counter_file=cf,
    )
    router.route_with_meta("p")
    _, count = _load_c2_counter(cf)
    assert count == 1, f"지연 degrade 후 카운터 {count} != 1"
