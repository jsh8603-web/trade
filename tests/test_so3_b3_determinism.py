"""SO-3 테스트: B3 결정성 — model_id property + prompt_hash + temperature RouteResult.

검증기준:
- 같은 prompt → 같은 prompt_hash 재현 PASS
- RouteResult.model_id = provider model 일치 PASS
- _parse_llm_response 결과 dict 에 B3 3필드 PASS
- degraded → 관망 강제 PASS
- route_with_meta 전환 후 ZMQ reply·B1 하드게이트 유지 PASS
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.brain.llm_provider import (
    ClaudeProvider,
    GeminiProvider,
    LLMProvider,
    LLMRouter,
    OllamaQwenProvider,
    RouteResult,
)

WORKER_SRC = (PROJECT_ROOT / "rl_hybrid" / "nodes" / "llm_worker.py").read_text(encoding="utf-8")


# ── model_id property ────────────────────────────────────────────────

def test_abc_has_model_id_abstract():
    """LLMProvider ABC 에 model_id 추상 property 존재."""
    import inspect
    props = {
        name for name, val in inspect.getmembers(LLMProvider)
        if isinstance(val, property)
    }
    assert "model_id" in props


def test_ollama_model_id():
    p = OllamaQwenProvider(model="qwen3-coder-fast")
    assert p.model_id == "qwen3-coder-fast"


def test_claude_model_id():
    p = ClaudeProvider(model="claude-opus-4-7")
    assert p.model_id == "claude-opus-4-7"


def test_gemini_model_id():
    p = GeminiProvider(model="gemini-2.5-flash")
    assert p.model_id == "gemini-2.5-flash"


# ── prompt_hash 결정성 ───────────────────────────────────────────────

def test_same_prompt_same_hash(tmp_path):
    """같은 prompt 2회 → 같은 prompt_hash."""
    q = MagicMock(spec=LLMProvider)
    q.tier = "quick"
    q.model_id = "mock-quick"
    q.generate.return_value = '{"decision":"관망","confidence":0.5}'
    router = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                       daily_cap=9999, counter_file=tmp_path / "c.json")

    r1 = router.route_with_meta("bitcoin analysis prompt")
    r2 = router.route_with_meta("bitcoin analysis prompt")
    assert r1.prompt_hash == r2.prompt_hash
    assert r1.prompt_hash != ""


def test_different_prompt_different_hash(tmp_path):
    """다른 prompt → 다른 prompt_hash."""
    q = MagicMock(spec=LLMProvider)
    q.tier = "quick"
    q.model_id = "mock-quick"
    q.generate.return_value = "ok"
    router = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                       daily_cap=9999, counter_file=tmp_path / "c.json")

    r1 = router.route_with_meta("prompt A")
    r2 = router.route_with_meta("prompt B")
    assert r1.prompt_hash != r2.prompt_hash


def test_prompt_hash_is_sha256(tmp_path):
    """prompt_hash = sha256(prompt) 검증."""
    q = MagicMock(spec=LLMProvider)
    q.tier = "quick"
    q.model_id = "mock"
    q.generate.return_value = "ok"
    router = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                       daily_cap=9999, counter_file=tmp_path / "c.json")

    prompt = "test sha256"
    result = router.route_with_meta(prompt)
    expected = hashlib.sha256(prompt.encode()).hexdigest()
    assert result.prompt_hash == expected


# ── RouteResult.model_id = provider model ────────────────────────────

def test_route_result_model_id_quick(tmp_path):
    """quick provider 호출 시 result.model_id = quick model."""
    q = MagicMock(spec=LLMProvider)
    q.tier = "quick"
    q.model_id = "qwen3-coder-fast"
    q.generate.return_value = "ok"
    router = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                       daily_cap=9999, counter_file=tmp_path / "c.json")

    result = router.route_with_meta("prompt", price_change_24h=0.0)
    assert result.model_id == "qwen3-coder-fast"


def test_route_result_model_id_deep(tmp_path):
    """deep trigger 시 result.model_id = deep model."""
    d = MagicMock(spec=LLMProvider)
    d.tier = "deep"
    d.model_id = "claude-opus-4-7"
    d.generate.return_value = "ok"
    router = LLMRouter(quick=MagicMock(spec=LLMProvider), deep=d,
                       daily_cap=9999, counter_file=tmp_path / "c.json")

    result = router.route_with_meta("prompt", price_change_24h=-6.0)  # 급락 트리거
    assert result.model_id == "claude-opus-4-7"


# ── _parse_llm_response B3 3필드 전파 ────────────────────────────────

def test_llm_worker_parse_b3_fields_in_source():
    """llm_worker.py _parse_llm_response 에 B3 3필드 setdefault 존재."""
    assert "model_id" in WORKER_SRC
    assert "prompt_hash" in WORKER_SRC
    assert "temperature" in WORKER_SRC


def test_parse_b3_fields_propagated():
    """_parse_llm_response 소스 exec → B3 3필드 결정레코드 전파."""
    import re
    import json as _json
    import logging as _log

    globs = {
        "json": _json,
        "re": re,
        "logging": _log,
        "logger": _log.getLogger("test_b3"),
    }

    m_parse = re.search(
        r"def _parse_llm_response\(.*?\n(?=    def |\nclass |\Z)",
        WORKER_SRC,
        re.DOTALL,
    )
    assert m_parse, "_parse_llm_response 추출 실패"

    def dedent(src):
        lines = src.split("\n")
        ind = len(lines[0]) - len(lines[0].lstrip())
        return "\n".join(l[ind:] if len(l) >= ind else l for l in lines)

    exec(dedent(m_parse.group()).replace("self.", "mock_self."), globs)
    mock_self = MagicMock()
    mock_self.logger = MagicMock()

    raw = '{"decision":"매수","confidence":0.8,"reason":"x","market_regime":"bull"}'
    result = globs["_parse_llm_response"](
        mock_self, raw, "c1", "quick",
        model_id="qwen3-coder-fast",
        prompt_hash="abc123",
        temperature=0.0,
    )
    assert result["model_id"] == "qwen3-coder-fast"
    assert result["prompt_hash"] == "abc123"
    assert result["temperature"] == 0.0


# ── degraded → 관망 강제 ─────────────────────────────────────────────

def test_llm_worker_degraded_hold_in_source():
    """llm_worker.py 에 C2 degrade→관망 강제 코드 존재."""
    assert "llm_result.degraded" in WORKER_SRC
    assert "C2 degrade" in WORKER_SRC


def test_route_with_meta_in_worker_source():
    """llm_worker.py 에 route_with_meta 전환 존재."""
    assert "route_with_meta" in WORKER_SRC


# ── ZMQ reply·B1 하드게이트 보존 ─────────────────────────────────────

def test_b1_hardgate_preserved():
    """B1 하드게이트(_validate_decision) 보존."""
    assert "_validate_decision" in WORKER_SRC
    assert "b1_veto" in WORKER_SRC


def test_zmq_reply_preserved():
    """ZMQ msg.reply() 계약 보존."""
    assert "msg.reply(" in WORKER_SRC


# ── temperature RouteResult 필드 ─────────────────────────────────────

def test_route_result_temperature(tmp_path):
    """RouteResult.temperature = kwargs.get('temperature', LLM_TEMPERATURE)."""
    q = MagicMock(spec=LLMProvider)
    q.tier = "quick"
    q.model_id = "mock"
    q.generate.return_value = "ok"
    router = LLMRouter(quick=q, deep=MagicMock(spec=LLMProvider),
                       daily_cap=9999, counter_file=tmp_path / "c.json")

    result = router.route_with_meta("prompt", temperature=0.0)
    assert isinstance(result.temperature, float)
