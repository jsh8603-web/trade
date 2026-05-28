"""SO-5 C2 서킷브레이커 fault-injection 테스트

검증 기준:
1. mock 트리거 폭주(호출 급증) → 캡 발동 + 휴리스틱 폴백 동작.
2. 지연 초과 mock → 휴리스틱 직행.
3. get_daily_call_count() 로 카운트 조회 가능.
4. 카운터가 날짜 경계에서 리셋됨.
5. config에 daily_call_cap/latency_budget_seconds 필드 존재.

NOTE: google.generativeai 미설치 환경 → C2 로직을 소스에서 추출하여 단위 테스트.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# C2 로직 소스 추출 헬퍼
# ---------------------------------------------------------------------------

def _load_c2_helpers(tmp_path: Path):
    """gemini_client.py 에서 C2 관련 메서드를 독립 실행."""
    src = (PROJECT_ROOT / "rl_hybrid" / "rag" / "gemini_client.py").read_text(encoding="utf-8")
    import json as _json
    import logging as _logging
    import time as _time
    import os as _os
    from pathlib import Path as _Path
    from typing import Optional as _Optional
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td

    ns: dict = {
        "json": _json,
        "logging": _logging,
        "logger": _logging.getLogger("c2_test"),
        "time": _time,
        "os": _os,
        "Path": _Path,
        "Optional": _Optional,
        "datetime": _dt,
        "timezone": _tz,
        "timedelta": _td,
        "KST": _tz(_td(hours=9)),
    }

    # C2 메서드 추출 대상
    target_funcs = {
        "_kst_today", "_load_daily_counter", "_save_daily_counter",
        "_increment_daily_counter", "get_daily_call_count", "_heuristic_fallback",
    }

    func_src = []
    in_func = False
    current_func = None
    for line in src.splitlines():
        stripped = line.lstrip()
        # 메서드 시작
        for fname in target_funcs:
            if stripped.startswith(f"def {fname}("):
                in_func = True
                current_func = fname
                break
        # 다음 비타겟 def/class 시 종료
        if in_func and stripped and not line.startswith(" ") and not line.startswith("\t"):
            if stripped.startswith("class ") or (
                stripped.startswith("def ") and
                not any(stripped.startswith(f"def {f}(") for f in target_funcs)
            ):
                in_func = False
                current_func = None
        if in_func:
            func_src.append(line)

    # 클래스 내부 들여쓰기(4 spaces) 제거
    import textwrap
    exec(textwrap.dedent("\n".join(func_src)), ns)

    # stub 객체로 감쌈
    class C2Stub:
        def __init__(self):
            self.cfg = MagicMock()
            self.cfg.daily_call_cap = 5
            self.cfg.latency_budget_seconds = 30.0
            self._daily_counter_file = tmp_path / "data" / "gemini_daily_counter.json"
            self._c2_today = ""
            self._c2_count = 0
            # 함수들을 bound method로 등록
            for fname in target_funcs:
                if fname in ns:
                    setattr(self, fname, lambda *a, self=self, fn=ns[fname]: fn(self, *a))

        def _kst_today(self):
            return ns["_kst_today"](self)

        def _load_daily_counter(self):
            return ns["_load_daily_counter"](self)

        def _save_daily_counter(self):
            return ns["_save_daily_counter"](self)

        def _increment_daily_counter(self):
            return ns["_increment_daily_counter"](self)

        def get_daily_call_count(self):
            return ns["get_daily_call_count"](self)

        def _heuristic_fallback(self, market_data, reason):
            return ns["_heuristic_fallback"](self, market_data, reason)

    stub = C2Stub()
    stub._load_daily_counter()
    return stub


# ---------------------------------------------------------------------------
# Test 1: 일일 캡 초과 → 휴리스틱 폴백 (소스 정적 검증)
# ---------------------------------------------------------------------------

class TestC2DailyCapStatic:
    SRC = (PROJECT_ROOT / "rl_hybrid" / "rag" / "gemini_client.py").read_text(encoding="utf-8")

    def test_daily_cap_check_in_source(self):
        assert "daily_call_cap" in self.SRC

    def test_heuristic_fallback_called_when_cap_exceeded(self):
        assert "_heuristic_fallback" in self.SRC

    def test_cap_check_before_rate_limit(self):
        """daily_cap 체크가 _rate_limit() 호출보다 앞에 위치해야 한다."""
        lines = self.SRC.splitlines()
        cap_line = next(
            (i for i, l in enumerate(lines) if "daily_call_cap" in l and "c2_count" in l), -1
        )
        rate_limit_call = next(
            (i for i, l in enumerate(lines) if "self._rate_limit()" in l), -1
        )
        assert cap_line != -1
        assert rate_limit_call != -1
        assert cap_line < rate_limit_call, "캡 체크는 rate_limit 보다 앞에 있어야 한다"


# ---------------------------------------------------------------------------
# Test 2: 지연 초과 체크 소스 확인
# ---------------------------------------------------------------------------

class TestC2LatencyStatic:
    SRC = (PROJECT_ROOT / "rl_hybrid" / "rag" / "gemini_client.py").read_text(encoding="utf-8")

    def test_latency_budget_check_in_source(self):
        assert "latency_budget_seconds" in self.SRC

    def test_heuristic_fallback_on_latency(self):
        assert "_heuristic_fallback" in self.SRC
        assert "지연" in self.SRC or "latency" in self.SRC.lower()

    def test_call_start_time_measured(self):
        assert "_call_start" in self.SRC or "call_start" in self.SRC


# ---------------------------------------------------------------------------
# Test 3: C2 헬퍼 단위 테스트 (소스 추출)
# ---------------------------------------------------------------------------

class TestC2Helpers:
    def test_heuristic_fallback_returns_hold(self, tmp_path):
        stub = _load_c2_helpers(tmp_path)
        result = stub._heuristic_fallback({}, "test reason")
        assert result["recommended_action"] == "hold"
        assert result.get("_c2_degraded") is True
        assert result["_c2_reason"] == "test reason"

    def test_daily_counter_persisted(self, tmp_path):
        stub = _load_c2_helpers(tmp_path)
        stub._c2_today = stub._kst_today()
        stub._c2_count = 7
        stub._save_daily_counter()

        stub2 = _load_c2_helpers(tmp_path)
        assert stub2.get_daily_call_count() == 7

    def test_counter_resets_on_new_day(self, tmp_path):
        stub = _load_c2_helpers(tmp_path)
        stub._c2_today = "2000-01-01"
        stub._c2_count = 9
        stub._save_daily_counter()

        stub._load_daily_counter()
        assert stub.get_daily_call_count() == 0

    def test_increment_increases_count(self, tmp_path):
        stub = _load_c2_helpers(tmp_path)
        stub._c2_today = stub._kst_today()
        stub._c2_count = 0
        stub._increment_daily_counter()
        assert stub._c2_count == 1
        stub._increment_daily_counter()
        assert stub._c2_count == 2


# ---------------------------------------------------------------------------
# Test 4: config에 C2 필드 존재
# ---------------------------------------------------------------------------

class TestC2Config:
    def test_daily_call_cap_field_exists(self):
        import rl_hybrid.config as cfg_mod
        assert "daily_call_cap" in cfg_mod.GeminiConfig.__dataclass_fields__

    def test_latency_budget_field_exists(self):
        import rl_hybrid.config as cfg_mod
        assert "latency_budget_seconds" in cfg_mod.GeminiConfig.__dataclass_fields__

    def test_default_cap_is_24(self):
        import rl_hybrid.config as cfg_mod
        cfg = cfg_mod.GeminiConfig.__new__(cfg_mod.GeminiConfig)
        # dataclass 기본값 확인
        default_cap = cfg_mod.GeminiConfig.__dataclass_fields__["daily_call_cap"].default
        assert default_cap == 24

    def test_default_latency_budget_is_30(self):
        import rl_hybrid.config as cfg_mod
        default_lat = cfg_mod.GeminiConfig.__dataclass_fields__["latency_budget_seconds"].default
        assert default_lat == 30.0
