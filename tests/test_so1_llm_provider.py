"""SO-1 테스트: core/brain/llm_provider.py LLMProvider + LLMRouter.

검증기준:
- ollama Qwen 실호출로 텍스트 반환 PASS
- Claude OAuth(.credentials.json accessToken) 실호출 반환 PASS
- LLMRouter 평상시→Qwen, 트리거(급락 mock)→Claude 라우팅 단위 PASS
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
for _p in (PROJECT_DIR,):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from core.brain.llm_provider import (
    ClaudeProvider,
    GeminiProvider,
    LLMProvider,
    LLMRouter,
    OllamaQwenProvider,
    _load_oauth_token,
)


# ── 기본 구조 테스트 ─────────────────────────────────────────────────

def test_import_ok():
    from core.brain.llm_provider import LLMProvider, LLMRouter  # noqa: F401


def test_abstract_instantiation_raises():
    with pytest.raises(TypeError):
        LLMProvider()  # type: ignore[abstract]


def test_ollama_provider_tier():
    p = OllamaQwenProvider()
    assert p.tier == "quick"


def test_claude_provider_tier():
    p = ClaudeProvider()
    assert p.tier == "deep"


def test_gemini_provider_tier():
    p = GeminiProvider()
    assert p.tier == "fallback"


# ── OAuth 토큰 로드 ──────────────────────────────────────────────────

def test_oauth_token_loads():
    token = _load_oauth_token()
    assert token.startswith("sk-ant-oat01-"), f"OAuth token 형식 오류: {token[:20]}"


def test_oauth_token_not_api_key():
    token = _load_oauth_token()
    assert not token.startswith("sk-ant-api"), "API key 사용 금지 (과금 분리)"


# ── ollama Qwen 실호출 ────────────────────────────────────────────────

def test_ollama_qwen_live_call():
    """ollama qwen3-coder-fast 실호출로 텍스트 반환 확인."""
    provider = OllamaQwenProvider(model="qwen3-coder-fast")
    response = provider.generate("Reply with exactly: HELLO", max_tokens=32, timeout=90)
    assert isinstance(response, str), f"응답이 str이 아님: {type(response)}"
    assert len(response) > 0, "빈 응답"


# ── Claude OAuth 실호출 ──────────────────────────────────────────────

def test_claude_oauth_live_call():
    """Claude Max OAuth 실호출로 텍스트 반환 확인."""
    provider = ClaudeProvider(model="claude-haiku-4-5-20251001")
    response = provider.generate("Reply with exactly: HELLO", max_tokens=32)
    assert isinstance(response, str), f"응답이 str이 아님: {type(response)}"
    assert len(response) > 0, "빈 응답"


# ── LLMRouter 라우팅 단위 테스트 ─────────────────────────────────────

def _make_mock_quick():
    m = MagicMock(spec=LLMProvider)
    m.tier = "quick"
    m.generate.return_value = "quick_response"
    return m


def _make_mock_deep():
    m = MagicMock(spec=LLMProvider)
    m.tier = "deep"
    m.generate.return_value = "deep_response"
    return m


def test_router_default_uses_quick():
    """평상시(트리거 없음) → quick(Qwen) 경유."""
    q, d = _make_mock_quick(), _make_mock_deep()
    router = LLMRouter(quick=q, deep=d)
    resp, tier = router.route("test prompt", price_change_24h=0.0)
    assert tier == "quick"
    assert resp == "quick_response"
    q.generate.assert_called_once()
    d.generate.assert_not_called()


def test_router_crash_triggers_deep():
    """급락(price_change_24h <= -5%) → deep(Claude) 경유."""
    q, d = _make_mock_quick(), _make_mock_deep()
    router = LLMRouter(quick=q, deep=d)
    resp, tier = router.route("test prompt", price_change_24h=-6.0)
    assert tier == "deep"
    assert resp == "deep_response"
    d.generate.assert_called_once()
    q.generate.assert_not_called()


def test_router_regime_switch_triggers_deep():
    """레짐전환(regime_switch=True) → deep(Claude) 경유."""
    q, d = _make_mock_quick(), _make_mock_deep()
    router = LLMRouter(quick=q, deep=d)
    _, tier = router.route("test prompt", regime_switch=True)
    assert tier == "deep"


def test_router_high_risk_triggers_deep():
    """고위험(high_risk=True) → deep(Claude) 경유."""
    q, d = _make_mock_quick(), _make_mock_deep()
    router = LLMRouter(quick=q, deep=d)
    _, tier = router.route("test prompt", high_risk=True)
    assert tier == "deep"


def test_router_borderline_no_trigger():
    """-4.9% 는 트리거(-5%) 미달 → quick 유지."""
    q, d = _make_mock_quick(), _make_mock_deep()
    router = LLMRouter(quick=q, deep=d)
    _, tier = router.route("test prompt", price_change_24h=-4.9)
    assert tier == "quick"


def test_router_exact_threshold_triggers():
    """-5.0% 정확히 임계값 → deep 트리거."""
    q, d = _make_mock_quick(), _make_mock_deep()
    router = LLMRouter(quick=q, deep=d)
    _, tier = router.route("test prompt", price_change_24h=-5.0)
    assert tier == "deep"


def test_router_generate_convenience():
    """router.generate() = route() 응답 반환."""
    q, d = _make_mock_quick(), _make_mock_deep()
    router = LLMRouter(quick=q, deep=d)
    resp = router.generate("test", price_change_24h=0.0)
    assert resp == "quick_response"
