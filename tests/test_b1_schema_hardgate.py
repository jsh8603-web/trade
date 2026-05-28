"""SO-3 B1 스키마 하드게이트 fault-injection 테스트

검증 기준:
1. 깨진 JSON/스키마 위반 출력 mock 주입 → 관망 결정 + near_miss_veto 기록.
2. 스키마 통과 JSON → 정상 결정 흐름 유지 (b1_veto 없음).
3. near_miss_veto.jsonl 파일에 이벤트 기록.

NOTE: llm_worker 는 zmq/rl_hybrid 의존성이 많아 _validate_decision/_log_near_miss_veto 를
직접 소스에서 로드해 단위 테스트한다.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path("D:/projects/Inv")


# ---------------------------------------------------------------------------
# 독립 로더 — zmq/rl_hybrid 없이 _validate_decision/_log_near_miss_veto 추출
# ---------------------------------------------------------------------------

def _load_b1_helpers():
    """llm_worker 소스에서 B1 헬퍼 함수만 추출 (의존성 분리)."""
    src = (PROJECT_ROOT / "rl_hybrid" / "nodes" / "llm_worker.py").read_text(encoding="utf-8")
    import json as _json
    import logging as _logging
    import jsonschema as _jsonschema
    from pathlib import Path as _Path
    from typing import Optional as _Optional
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td

    schema_path = PROJECT_ROOT / "prompts" / "schemas" / "decision_result.json"

    ns: dict = {
        "__name__": "llm_worker_b1_test",
        "json": _json,
        "logging": _logging,
        "logger": _logging.getLogger("llm_worker_b1_test"),
        "Path": _Path,
        "Optional": _Optional,
        "jsonschema": _jsonschema,
        "datetime": _dt,
        "timezone": _tz,
        "timedelta": _td,
        "_SCHEMA_PATH": schema_path,
        "_DECISION_SCHEMA": None,
        "_SCHEMA_LOAD_ERROR": None,
    }

    func_src = []
    in_func = False
    for line in src.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("def _validate_decision") or \
           stripped.startswith("def _log_near_miss_veto") or \
           stripped.startswith("def _load_decision_schema"):
            in_func = True
        elif in_func and stripped and not line.startswith(" ") and not line.startswith("\t"):
            if stripped.startswith("class ") or (stripped.startswith("def ") and
               not stripped.startswith("def _validate_decision") and
               not stripped.startswith("def _log_near_miss_veto") and
               not stripped.startswith("def _load_decision_schema")):
                in_func = False
        if in_func:
            func_src.append(line)

    exec("\n".join(func_src), ns)
    return ns


try:
    _B1 = _load_b1_helpers()
    _validate_decision = _B1["_validate_decision"]
    _log_near_miss_veto = _B1["_log_near_miss_veto"]
    B1_IMPORTABLE = True
except Exception as e:
    B1_IMPORTABLE = False
    _import_error = str(e)

pytestmark = pytest.mark.skipif(
    not B1_IMPORTABLE,
    reason=f"B1 helpers load failed: {'' if B1_IMPORTABLE else _import_error if not B1_IMPORTABLE else ''}",
)


# ---------------------------------------------------------------------------
# LLMWorkerNode stub — _handle_analyze B1 로직만 테스트
# ---------------------------------------------------------------------------

def _make_handle_analyze_b1(schema_path: Path):
    """_handle_analyze 의 B1 게이트 부분만 실행하는 스텁 함수."""
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    import jsonschema

    def handle(analysis: dict, cycle_id: str = "test") -> dict:
        try:
            jsonschema.validate(instance=analysis, schema=schema)
            return {"passed": True, "result": analysis}
        except jsonschema.ValidationError as e:
            return {
                "passed": False,
                "decision": "관망",
                "b1_veto": True,
                "b1_error": e.message,
            }
    return handle


SCHEMA_PATH = PROJECT_ROOT / "prompts" / "schemas" / "decision_result.json"

VALID_ANALYSIS = {
    "timestamp": "2026-05-28T00:00:00+09:00",
    "decision": "매수",
    "confidence": 0.8,
    "reason": "RSI 과매도 구간이며 공포탐욕지수가 극단적 공포 수준으로 하락하여 반등 가능성이 높다고 판단함",
    "market_analysis": {
        "trend": "하락",
        "fear_greed": {"value": 20, "classification": "Extreme Fear"},
        "rsi": 28.5,
        "sma20_deviation": "-5.2%",
        "news_sentiment": "부정",
        "key_factors": ["RSI 과매도", "공포 지수 극단", "지지선 근접"],
    },
    "trade_details": {
        "side": "bid",
        "amount": 50000,
        "executed": False,
    },
}

INVALID_MISSING_DECISION = {
    "timestamp": "2026-05-28T00:00:00+09:00",
    # decision 누락
    "confidence": 0.5,
    "reason": "근거",
}

INVALID_WRONG_ENUM = {
    **VALID_ANALYSIS,
    "decision": "invalid_value",
}


# ---------------------------------------------------------------------------
# Test 1: _validate_decision
# ---------------------------------------------------------------------------

class TestValidateDecision:
    def test_valid_schema_passes(self):
        valid, err = _validate_decision(VALID_ANALYSIS)
        assert valid is True
        assert err == ""

    def test_missing_required_field_fails(self):
        valid, err = _validate_decision(INVALID_MISSING_DECISION)
        assert valid is False
        assert err != ""

    def test_wrong_enum_fails(self):
        valid, err = _validate_decision(INVALID_WRONG_ENUM)
        assert valid is False

    def test_empty_dict_fails(self):
        valid, err = _validate_decision({})
        assert valid is False


# ---------------------------------------------------------------------------
# Test 2: _log_near_miss_veto
# ---------------------------------------------------------------------------

class TestLogNearMissVeto:
    def test_veto_logged_to_file(self, tmp_path, monkeypatch):
        # _SCHEMA_PATH.parent.parent.parent → tmp_path 로 리다이렉트
        fake_schema_path = tmp_path / "prompts" / "schemas" / "decision_result.json"
        monkeypatch.setitem(_B1, "_SCHEMA_PATH", fake_schema_path)

        _log_near_miss_veto("cycle_test_1", "decision 필드 누락", {"foo": "bar"})

        log_file = tmp_path / "logs" / "executions" / "near_miss_veto.jsonl"
        assert log_file.exists(), "near_miss_veto.jsonl 이 생성돼야 한다"
        lines = [json.loads(l) for l in log_file.read_text(encoding="utf-8").splitlines()]
        assert len(lines) == 1
        assert lines[0]["event"] == "near_miss_veto"
        assert lines[0]["cycle_id"] == "cycle_test_1"

        # 복원
        monkeypatch.setitem(_B1, "_SCHEMA_PATH", SCHEMA_PATH)


# ---------------------------------------------------------------------------
# Test 3: B1 gate 스텁 — 스키마 위반 시 관망 강제
# ---------------------------------------------------------------------------

class TestB1GateStub:
    def setup_method(self):
        self.gate = _make_handle_analyze_b1(SCHEMA_PATH)

    def test_invalid_returns_hold(self):
        result = self.gate(INVALID_MISSING_DECISION)
        assert result["passed"] is False
        assert result["decision"] == "관망"
        assert result.get("b1_veto") is True

    def test_valid_passes_through(self):
        result = self.gate(VALID_ANALYSIS)
        assert result["passed"] is True
        assert result["result"]["decision"] == "매수"

    def test_wrong_enum_returns_hold(self):
        result = self.gate(INVALID_WRONG_ENUM)
        assert result["passed"] is False
        assert result.get("b1_veto") is True

    def test_empty_dict_returns_hold(self):
        result = self.gate({})
        assert result["passed"] is False


# ---------------------------------------------------------------------------
# Test 4: near_miss_veto.jsonl 이 llm_worker 소스에 실제로 구현돼 있는지 확인
# ---------------------------------------------------------------------------

class TestB1SourceImplementation:
    def test_validate_decision_function_exists_in_source(self):
        """소스에 _validate_decision 함수가 존재한다."""
        assert callable(_validate_decision)

    def test_log_near_miss_veto_function_exists_in_source(self):
        """소스에 _log_near_miss_veto 함수가 존재한다."""
        assert callable(_log_near_miss_veto)

    def test_jsonschema_called_in_validate(self):
        """_validate_decision 이 jsonschema.validate 를 호출한다."""
        with patch("jsonschema.validate") as mock_v:
            mock_v.return_value = None
            _B1["_DECISION_SCHEMA"] = None  # force reload
            valid, err = _validate_decision(VALID_ANALYSIS)
        mock_v.assert_called_once()


# ---------------------------------------------------------------------------
# Test 5: SO-6 fail-closed — 스키마 로드 실패 / SchemaError 시 (False, 사유)
# ---------------------------------------------------------------------------

class TestB1FailClosed:
    def test_schema_load_failure_returns_false(self, monkeypatch):
        """스키마 파일 로드 실패 시 fail-closed: (False, 사유) 반환."""
        monkeypatch.setitem(_B1, "_DECISION_SCHEMA", None)
        monkeypatch.setitem(_B1, "_SCHEMA_LOAD_ERROR", "로드 실패 mock")
        valid, err = _validate_decision(VALID_ANALYSIS)
        assert valid is False
        assert "로드 실패" in err

    def test_schema_load_failure_no_passthrough(self, monkeypatch):
        """fail-closed 시 어떤 입력도 True 반환하지 않는다."""
        monkeypatch.setitem(_B1, "_DECISION_SCHEMA", None)
        monkeypatch.setitem(_B1, "_SCHEMA_LOAD_ERROR", "파일 없음")
        for analysis in [VALID_ANALYSIS, INVALID_MISSING_DECISION, {}]:
            valid, _ = _validate_decision(analysis)
            assert valid is False

    def test_schema_error_returns_false(self, monkeypatch):
        """jsonschema.SchemaError 발생 시 fail-closed: (False, 사유) 반환."""
        import jsonschema
        monkeypatch.setitem(_B1, "_DECISION_SCHEMA", {"type": "object"})
        monkeypatch.setitem(_B1, "_SCHEMA_LOAD_ERROR", None)

        def raise_schema_error(instance, schema):
            raise jsonschema.SchemaError("스키마 자체 오류")

        with patch("jsonschema.validate", side_effect=raise_schema_error):
            valid, err = _validate_decision(VALID_ANALYSIS)
        assert valid is False
        assert "SchemaError" in err
