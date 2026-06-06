"""SO-5 보강: ClaudeProvider temperature payload 실주입 + route_with_meta kwargs 전달.

B3 결정성 완결 — RouteResult.temperature == 실제 API 전달 temperature.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.brain.llm_provider import (
    ClaudeProvider,
    LLM_TEMPERATURE,
    LLMProvider,
    LLMRouter,
    OllamaQwenProvider,
)

PROVIDER_SRC = (PROJECT_ROOT / "core" / "brain" / "llm_provider.py").read_text(encoding="utf-8")


# ── ClaudeProvider payload temperature 실주입 ────────────────────────

def _capture_payload(model, temperature):
    """ClaudeProvider.generate 의 payload 를 mock 으로 캡처."""
    import json as _json

    captured = {}

    def fake_urlopen(req, timeout=60):
        captured["payload"] = _json.loads(req.data.decode())
        captured["headers"] = dict(req.headers)
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = _json.dumps({"content": [{"type": "text", "text": "ok"}]}).encode()
        return mock_resp

    provider = ClaudeProvider(model=model)
    provider._token = "sk-ant-oat01-fake"  # mock token
    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        provider.generate("test", temperature=temperature)
    return captured


def test_claude_provider_omits_temperature_for_4x():
    """★신형 4.x(opus-4/sonnet-4/haiku-4) → temperature deprecated → payload 생략(400 invalid 회피)."""
    cap = _capture_payload("claude-haiku-4-5-20251001", 0.0)
    assert "temperature" not in cap["payload"], "신형 4.x 는 temperature 생략돼야(deprecated)"


def test_claude_provider_injects_temperature_for_legacy():
    """구형 모델(비 4.x) → temperature payload 주입(B3 결정성 하위호환)."""
    cap = _capture_payload("claude-3-5-haiku-20241022", 0.5)
    assert cap["payload"].get("temperature") == 0.5


def test_claude_provider_oauth_policy_headers_and_system():
    """★OAuth 정책(2026-06-06 실측): anthropic-beta oauth 헤더 + Claude Code system 필수."""
    cap = _capture_payload("claude-opus-4-7", 0.0)
    # system 은 Claude Code 문구 고정(opus 는 추가 텍스트 시 429)
    assert cap["payload"].get("system", "").startswith("You are Claude Code")
    # anthropic-beta oauth 헤더(대소문자 무관)
    hdrs = {k.lower(): v for k, v in cap["headers"].items()}
    assert "oauth-2025" in hdrs.get("anthropic-beta", "")


# ── route_with_meta → generate 로 temperature 전달 보장 ─────────────

def test_route_with_meta_passes_temperature_to_provider(tmp_path):
    """route_with_meta 가 provider.generate 에 temperature kwargs 전달."""
    q = MagicMock(spec=LLMProvider)
    q.tier = "quick"
    q.model_id = "mock-quick"
    q.generate.return_value = "ok"

    router = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                       daily_cap=9999, counter_file=tmp_path / "c.json")

    router.route_with_meta("prompt", temperature=0.0)

    call_kwargs = q.generate.call_args
    # generate(prompt, **kwargs) 로 호출 — kwargs 에 temperature 있어야 함
    assert "temperature" in call_kwargs.kwargs or (
        len(call_kwargs.args) > 1  # positional 로 전달된 경우
    ), "generate kwargs에 temperature 없음"


def test_route_result_temperature_matches_kwargs(tmp_path):
    """RouteResult.temperature == kwargs temperature (기록-실제 일치)."""
    q = MagicMock(spec=LLMProvider)
    q.tier = "quick"
    q.model_id = "mock"
    q.generate.return_value = "ok"

    router = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                       daily_cap=9999, counter_file=tmp_path / "c.json")

    result = router.route_with_meta("prompt", temperature=0.0)
    assert result.temperature == 0.0


def test_route_result_temperature_default(tmp_path):
    """temperature 미전달 → LLM_TEMPERATURE(0.0) 기본 사용."""
    q = MagicMock(spec=LLMProvider)
    q.tier = "quick"
    q.model_id = "mock"
    q.generate.return_value = "ok"

    router = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                       daily_cap=9999, counter_file=tmp_path / "c.json")

    result = router.route_with_meta("prompt")
    assert result.temperature == LLM_TEMPERATURE


# ── 소스 검증 ────────────────────────────────────────────────────────

def test_claude_provider_source_has_temperature():
    """ClaudeProvider.generate 에 temperature 조건부 로직 + OAuth 정책 존재."""
    assert '"temperature"' in PROVIDER_SRC or "'temperature'" in PROVIDER_SRC
    claude_section = PROVIDER_SRC[PROVIDER_SRC.find("class ClaudeProvider"):]
    assert "temperature" in claude_section[:1500]   # system/oauth 추가로 범위 확장
    # OAuth 정책(beta 헤더 + Claude Code system) 소스 존재
    assert "oauth-2025" in PROVIDER_SRC and "Claude Code" in PROVIDER_SRC
