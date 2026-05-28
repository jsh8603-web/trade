"""SO-1 테스트: LLMRouter C2 일일 호출 캡 + RouteResult + route_with_meta.

검증기준:
- 캡 미달 → provider 호출 + 카운터 +1 PASS
- 캡 도달(count>=cap) → provider 미호출 degrade PASS
- route() 여전히 (text, tier) 2-tuple 반환 PASS
- 카운터 파일 KST 영속·재로드 PASS
"""

from __future__ import annotations

import json
import sys
import tempfile
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
    _increment_c2_counter,
    _kst_today,
    _load_c2_counter,
    _save_c2_counter,
)


# ── RouteResult 구조 ──────────────────────────────────────────────────

def test_route_result_fields():
    r = RouteResult(text="hello", tier="quick")
    assert r.text == "hello"
    assert r.tier == "quick"
    assert r.degraded is False
    assert r.degrade_reason == ""
    assert r.model_id == ""
    assert r.prompt_hash == ""


def test_route_result_degraded():
    r = RouteResult(text="hold", tier="degraded", degraded=True, degrade_reason="cap")
    assert r.degraded is True
    assert r.degrade_reason == "cap"


# ── 카운터 유틸 ──────────────────────────────────────────────────────

def test_load_c2_counter_empty(tmp_path):
    """파일 없으면 (today, 0) 반환."""
    f = tmp_path / "counter.json"
    today, count = _load_c2_counter(f)
    assert count == 0
    assert today == _kst_today()


def test_save_and_reload_counter(tmp_path):
    """저장 후 재로드 — 값 일치."""
    f = tmp_path / "counter.json"
    today = _kst_today()
    _save_c2_counter(f, today, 5)
    loaded_today, loaded_count = _load_c2_counter(f)
    assert loaded_count == 5
    assert loaded_today == today


def test_increment_counter(tmp_path):
    """카운터 +1."""
    f = tmp_path / "counter.json"
    today = _kst_today()
    new_today, new_count = _increment_c2_counter(f, today, 3)
    assert new_count == 4
    # 파일 영속 확인
    loaded_today, loaded_count = _load_c2_counter(f)
    assert loaded_count == 4


def test_counter_date_reset(tmp_path):
    """날짜 다르면 카운터 0으로 리셋."""
    f = tmp_path / "counter.json"
    _save_c2_counter(f, "2020-01-01", 99)  # 과거 날짜
    today, count = _load_c2_counter(f)
    assert count == 0  # 오늘 날짜 불일치 → 0
    assert today == _kst_today()


# ── mock provider 헬퍼 ────────────────────────────────────────────────

def _make_mock_provider(response: str = "ok", tier: str = "quick"):
    m = MagicMock(spec=LLMProvider)
    m.tier = tier
    m.generate.return_value = response
    m.model_id = f"mock-{tier}"
    return m


# ── 캡 미달 → provider 호출 + 카운터 +1 ────────────────────────────

def test_cap_not_reached_calls_provider(tmp_path):
    """캡(5) 미달(count=3) → provider 호출."""
    q = _make_mock_provider("quick_ok", "quick")
    d = _make_mock_provider("deep_ok", "deep")
    router = LLMRouter(quick=q, deep=d, daily_cap=5, counter_file=tmp_path / "c.json")
    # count=3으로 미리 설정
    _save_c2_counter(tmp_path / "c.json", _kst_today(), 3)
    router._c2_today, router._c2_count = _load_c2_counter(tmp_path / "c.json")

    result = router.route_with_meta("test prompt")
    assert result.degraded is False
    q.generate.assert_called_once()
    # 카운터 +1 → 4
    _, count = _load_c2_counter(tmp_path / "c.json")
    assert count == 4


def test_cap_not_reached_returns_response(tmp_path):
    """캡 미달 → 실제 provider 응답 반환."""
    q = _make_mock_provider("response_text", "quick")
    router = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                       daily_cap=5, counter_file=tmp_path / "c.json")
    result = router.route_with_meta("prompt")
    assert result.text == "response_text"
    assert result.tier == "quick"


# ── 캡 도달 → provider 미호출 degrade ────────────────────────────────

def test_cap_reached_degrade(tmp_path):
    """count >= cap → degraded=True, provider.generate 미호출."""
    q = _make_mock_provider("should_not_call", "quick")
    router = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                       daily_cap=3, counter_file=tmp_path / "c.json")
    _save_c2_counter(tmp_path / "c.json", _kst_today(), 3)  # count=cap
    router._c2_today, router._c2_count = _load_c2_counter(tmp_path / "c.json")

    result = router.route_with_meta("prompt")
    assert result.degraded is True
    assert result.degrade_reason == "cap"
    assert result.tier == "degraded"
    q.generate.assert_not_called()


def test_cap_degrade_hold_content(tmp_path):
    """degrade 텍스트 = hold/관망 의미."""
    router = LLMRouter(quick=MagicMock(spec=LLMProvider),
                       deep=MagicMock(spec=LLMProvider),
                       daily_cap=0, counter_file=tmp_path / "c.json")
    result = router.route_with_meta("prompt")
    assert result.degraded is True
    data = json.loads(result.text)
    assert data.get("decision") == "관망" or data.get("recommended_action") == "hold"
    assert data.get("_c2_degraded") is True


# ── route() 2-tuple 계약 보존 ────────────────────────────────────────

def test_route_returns_2_tuple(tmp_path):
    """route() 여전히 (text, tier) tuple 반환."""
    q = _make_mock_provider("r", "quick")
    router = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                       daily_cap=100, counter_file=tmp_path / "c.json")
    result = router.route("prompt")
    assert isinstance(result, tuple)
    assert len(result) == 2
    text, tier = result
    assert isinstance(text, str)
    assert isinstance(tier, str)


def test_route_unpacking_works(tmp_path):
    """기존 resp, tier = router.route(...) 패턴 무파손."""
    q = _make_mock_provider("hello", "quick")
    router = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                       daily_cap=100, counter_file=tmp_path / "c.json")
    resp, tier = router.route("test")
    assert resp == "hello"
    assert tier == "quick"


def test_generate_returns_text(tmp_path):
    """generate() = route_with_meta().text."""
    q = _make_mock_provider("gen_response", "quick")
    router = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                       daily_cap=100, counter_file=tmp_path / "c.json")
    text = router.generate("prompt")
    assert text == "gen_response"


# ── 카운터 영속·재로드 통합 ──────────────────────────────────────────

def test_counter_persists_across_router_instances(tmp_path):
    """router 인스턴스 재생성 후 카운터 이어받기."""
    cf = tmp_path / "c.json"
    q = _make_mock_provider("ok", "quick")

    router1 = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                        daily_cap=100, counter_file=cf)
    router1.route_with_meta("p1")  # count=1
    router1.route_with_meta("p2")  # count=2

    # 새 인스턴스 — 파일에서 count=2 복구
    q2 = _make_mock_provider("ok2", "quick")
    router2 = LLMRouter(quick=q2, deep=MagicMock(spec=LLMProvider),
                        daily_cap=100, counter_file=cf)
    assert router2._c2_count == 2
