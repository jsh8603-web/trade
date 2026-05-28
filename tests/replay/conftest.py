"""tests/replay/conftest.py — 결정적 replay 하니스 공용 픽스처.

5격리:
  (a) RAG 격리/리셋 — query_similar mock + 빈 RAG
  (b) 시계 freeze — timestamp 고정 주입 (fixture 내 timestamp 사용)
  (c) 외부데이터/포트폴리오 mock fixture — ExternalDataAgent.collect_all + _run_script 스텁
  (d) LLM record-replay fixture — .env 없음 = mock-only → snapshot으로 실데이터 대체
  (e) PPO/temperature=0 결정성 재사용 (Phase -1 B3 산물, GEMINI_TEMPERATURE=0)

기존 tests/conftest.py 패턴 확장 (PROJECT_DIR/Path(__file__).resolve().parents[N] 재사용).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[2]
FIXTURES_DIR = PROJECT_DIR / "tests" / "fixtures" / "replay"

for _p in (PROJECT_DIR, PROJECT_DIR / "scripts"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)


# ── 픽스처 로더 ─────────────────────────────────────────────────────

def load_snapshot(name: str) -> dict[str, Any]:
    """tests/fixtures/replay/<name>.json 로드."""
    path = FIXTURES_DIR / f"{name}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


ALL_FIXTURE_NAMES = [
    "bull_market",
    "bear_market",
    "sideways_market",
    "extreme_fear",
    "flash_crash",
]


# ── Orchestrator 내부 DB/네트워크 패치 컨텍스트 ──────────────────────

class OrchestratorIsolation:
    """Orchestrator의 외부 의존성을 모두 격리하는 컨텍스트 매니저."""

    def __init__(self) -> None:
        self._patches: list = []

    def __enter__(self) -> "OrchestratorIsolation":
        self._patches = [
            patch("agents.orchestrator._load_state",
                  return_value={"active_agent": "conservative"}),
            patch("agents.orchestrator._save_state"),
            patch("agents.orchestrator.Orchestrator._load_learning_data",
                  return_value=None),
            patch("agents.orchestrator.Orchestrator._check_auto_emergency_active",
                  return_value=None),
            patch.dict(os.environ, {
                "SUPABASE_URL": "",
                "SUPABASE_SERVICE_ROLE_KEY": "",
                "GEMINI_TEMPERATURE": "0",
                "EMERGENCY_STOP": "false",
            }),
        ]
        for p in self._patches:
            p.start()
        return self

    def __exit__(self, *args: object) -> None:
        for p in reversed(self._patches):
            p.stop()


# ── pytest 픽스처 ──────────────────────────────────────────────────

@pytest.fixture(params=ALL_FIXTURE_NAMES)
def snapshot(request: pytest.FixtureRequest) -> dict[str, Any]:
    """5개 snapshot fixture를 파라미터화하여 반환."""
    return load_snapshot(request.param)


@pytest.fixture
def orch_isolated() -> "OrchestratorIsolation":
    """격리된 Orchestrator 컨텍스트 — 테스트에서 with orch_isolated 로 사용."""
    return OrchestratorIsolation()


@pytest.fixture
def coin_track_factory():
    """snapshot dict를 받아 CoinTrack 인스턴스를 반환하는 팩토리."""
    from core.coin_track import CoinTrack

    def factory(snap: dict[str, Any]) -> CoinTrack:
        return CoinTrack(
            _market_data_override=snap["market_data"],
            _portfolio_override=snap["portfolio"],
            _external_data_override=snap["external_data"],
            _past_decisions_override=snap.get("past_decisions", []),
        )

    return factory
