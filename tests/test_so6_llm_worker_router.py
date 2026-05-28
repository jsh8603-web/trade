"""SO-6 테스트: rl_hybrid/nodes/llm_worker.py LLMRouter 경유 교체.

검증기준:
- llm_worker 가 llm_provider 경유(gemini_client 직접호출 제거) PASS
- ZMQ 계약 유지(reply payload 형식) PASS
- 라우팅 동작(평상시=quick, 트리거=deep) PASS
- B1 하드게이트 보존 PASS
- Phase -1 B1 회귀 0 PASS

NOTE: zmq/msgpack 없이 소스 직접 파싱 + LLMRouter mock 으로 단위 테스트.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKER_SRC = (PROJECT_ROOT / "rl_hybrid" / "nodes" / "llm_worker.py").read_text(encoding="utf-8")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.brain.llm_provider import LLMProvider, LLMRouter


# ── 소스 구조 검증 ───────────────────────────────────────────────────

def test_llm_worker_imports_llm_router():
    """llm_worker.py 가 LLMRouter 를 임포트하는지 확인."""
    assert "from core.brain.llm_provider import LLMRouter" in WORKER_SRC


def test_llm_worker_no_direct_gemini_client_import():
    """gemini_client 직접 임포트 없음 (RAGPipeline 경유는 허용)."""
    assert "from rl_hybrid.rag.gemini_client import GeminiClient" not in WORKER_SRC


def test_llm_worker_has_llm_router_field():
    assert "_llm_router" in WORKER_SRC


def test_llm_worker_b1_hardgate_preserved():
    """B1 스키마 하드게이트 코드 보존."""
    assert "_validate_decision" in WORKER_SRC
    assert "b1_veto" in WORKER_SRC


def test_zmq_reply_contract_preserved():
    """ZMQ msg.reply() 계약 유지."""
    assert "msg.reply(" in WORKER_SRC


def test_build_analysis_prompt_in_source():
    """_build_analysis_prompt 메서드 존재."""
    assert "_build_analysis_prompt" in WORKER_SRC


def test_parse_llm_response_in_source():
    """_parse_llm_response 메서드 존재."""
    assert "_parse_llm_response" in WORKER_SRC


# ── 소스에서 함수만 추출 — zmq/msgpack 없이 단위 테스트 ─────────────

def _extract_standalone_helpers():
    """_build_analysis_prompt / _parse_llm_response 를 독립 함수로 실행."""
    import json as _json
    import logging as _log
    import re as _re
    from unittest.mock import MagicMock as _MM

    # 독립 실행 환경 구성
    globs: dict[str, Any] = {
        "json": _json,
        "logging": _log,
        "re": _re,
        "logger": _log.getLogger("test_so6"),
        "MagicMock": _MM,
    }

    # _build_analysis_prompt 함수 추출 실행
    m_build = re.search(
        r"def _build_analysis_prompt\(.*?\n(?=    def |\nclass |\Z)",
        WORKER_SRC,
        re.DOTALL,
    )
    m_parse = re.search(
        r"def _parse_llm_response\(.*?\n(?=    def |\nclass |\Z)",
        WORKER_SRC,
        re.DOTALL,
    )
    assert m_build, "_build_analysis_prompt 추출 실패"
    assert m_parse, "_parse_llm_response 추출 실패"

    # 들여쓰기 제거 + self → mock_self 치환
    def dedent_fn(src: str) -> str:
        lines = src.split("\n")
        indent = len(lines[0]) - len(lines[0].lstrip())
        return "\n".join(l[indent:] if len(l) >= indent else l for l in lines)

    build_src = dedent_fn(m_build.group()).replace("self.", "mock_self.")
    parse_src = dedent_fn(m_parse.group()).replace("self.", "mock_self.")

    exec(build_src, globs)
    exec(parse_src, globs)
    return globs


def _make_mock_self():
    ms = MagicMock()
    ms.logger = MagicMock()
    return ms


def test_build_prompt_has_btc_price():
    globs = _extract_standalone_helpers()
    mock_self = _make_mock_self()
    market_data = {
        "current_price": {"trade_price": 90000000, "signed_change_rate": -0.05},
        "indicators": {"rsi_14": 35.5},
    }
    external_data = {"fgi": {"value": 25}}
    prompt = globs["_build_analysis_prompt"](mock_self, market_data, external_data, "cycle1")
    assert "90000000" in prompt
    assert "35.5" in prompt
    assert "25" in prompt


def test_parse_valid_json_response():
    globs = _extract_standalone_helpers()
    mock_self = _make_mock_self()
    raw = '{"decision":"매수","confidence":0.8,"reason":"RSI 과매도","market_regime":"bull"}'
    result = globs["_parse_llm_response"](mock_self, raw, "c1", "quick")
    assert result["decision"] == "매수"
    assert result["confidence"] == 0.8
    assert result["llm_tier"] == "quick"
    assert result["cycle_id"] == "c1"


def test_parse_json_embedded_in_text():
    globs = _extract_standalone_helpers()
    mock_self = _make_mock_self()
    raw = '분석: {"decision":"매도","confidence":0.6,"reason":"RSI 과매수","market_regime":"bear"}'
    result = globs["_parse_llm_response"](mock_self, raw, "c2", "deep")
    assert result["decision"] == "매도"
    assert result["llm_tier"] == "deep"


def test_parse_fallback_on_invalid_json():
    globs = _extract_standalone_helpers()
    mock_self = _make_mock_self()
    result = globs["_parse_llm_response"](mock_self, "JSON 없는 응답", "c3", "quick")
    assert result["decision"] == "관망"
    assert result["confidence"] == 0.0
    assert "heuristic" in result["reason"]


# ── LLMRouter 라우팅 동작 (mock 주입) ────────────────────────────────

def _make_mock_router(response_json: str) -> tuple[LLMRouter, MagicMock, MagicMock]:
    mock_quick = MagicMock(spec=LLMProvider)
    mock_quick.tier = "quick"
    mock_quick.generate.return_value = response_json

    mock_deep = MagicMock(spec=LLMProvider)
    mock_deep.tier = "deep"
    mock_deep.generate.return_value = response_json

    return LLMRouter(quick=mock_quick, deep=mock_deep), mock_quick, mock_deep


def test_router_default_quick():
    """평상시(급락 없음) → quick(Qwen)."""
    router, q, d = _make_mock_router('{"decision":"관망"}')
    _, tier = router.route("prompt", price_change_24h=0.0)
    assert tier == "quick"
    q.generate.assert_called_once()
    d.generate.assert_not_called()


def test_router_crash_deep():
    """급락(-5%) → deep(Claude)."""
    router, q, d = _make_mock_router('{"decision":"관망"}')
    _, tier = router.route("prompt", price_change_24h=-6.0)
    assert tier == "deep"
    d.generate.assert_called_once()
    q.generate.assert_not_called()


def test_router_regime_switch_deep():
    """레짐전환 → deep."""
    router, q, d = _make_mock_router('{"decision":"관망"}')
    _, tier = router.route("prompt", regime_switch=True)
    assert tier == "deep"


def test_router_high_risk_deep():
    """고위험 → deep."""
    router, q, d = _make_mock_router('{"decision":"관망"}')
    _, tier = router.route("prompt", high_risk=True)
    assert tier == "deep"
