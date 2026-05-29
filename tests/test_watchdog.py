"""tests/test_watchdog.py — SO-4 검증 게이트.

검증:
  1. heartbeat stale (now-120s) → derisk_to_floor 호출 assert.
  2. heartbeat 정상 (now-10s) → 트리거 0 assert.
  3. import 정적검사: 봇 코어/brain/LLM import 0, ExchangeAdapter 만 assert.
"""

from __future__ import annotations

import ast
import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.derisk_executor import FakeExchange
from scripts.watchdog import WatchdogProcess, write_heartbeat


# ── 픽스처 ────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_hb(tmp_path: Path) -> Path:
    """임시 heartbeat.json 경로."""
    return tmp_path / "heartbeat.json"


def _make_watchdog(exchange, tmp_hb, now_val: float, timeout_sec: float = 90.0) -> WatchdogProcess:
    return WatchdogProcess(
        exchange=exchange,
        heartbeat_path=tmp_hb,
        timeout_sec=timeout_sec,
        poll_sec=1.0,
        floors={"BTC": 0.0},
        _now_fn=lambda: now_val,
    )


# ── Test 1: heartbeat stale → derisk_to_floor 호출 ────────────────────

def test_stale_heartbeat_triggers_derisk(tmp_hb: Path) -> None:
    """heartbeat.json ts = now-120s → watchdog 1틱이 derisk_to_floor 호출."""
    now = time.time()
    stale_ts = now - 120  # 90s timeout 초과
    tmp_hb.write_text(json.dumps({"ts": stale_ts, "healthy": True}), encoding="utf-8")

    exchange = FakeExchange(positions={"BTC": 1.0})
    wd = _make_watchdog(exchange, tmp_hb, now_val=now)

    triggered = wd.tick()

    assert triggered is True, "stale heartbeat 는 True 반환"
    # cancel_all_open_orders 호출됨 (derisk_to_floor → cancel 먼저)
    assert exchange.cancelled_orders >= 1, "derisk_to_floor 가 cancel_all_open_orders 호출"
    # positions 가 floor(0) 방향으로 축소 시도됨
    assert len(exchange.submit_calls) >= 1, "IOC 주문 최소 1회 호출"


# ── Test 2: heartbeat 정상 → 트리거 0 ───────────────────────────────

def test_fresh_heartbeat_no_trigger(tmp_hb: Path) -> None:
    """heartbeat.json ts = now-10s → 트리거 0."""
    now = time.time()
    fresh_ts = now - 10  # 90s 이내
    tmp_hb.write_text(json.dumps({"ts": fresh_ts, "healthy": True}), encoding="utf-8")

    exchange = FakeExchange(positions={"BTC": 0.5})
    wd = _make_watchdog(exchange, tmp_hb, now_val=now)

    triggered = wd.tick()

    assert triggered is False, "정상 heartbeat 는 False 반환"
    assert exchange.cancelled_orders == 0, "정상 시 cancel 호출 0"
    assert len(exchange.submit_calls) == 0, "정상 시 IOC 주문 0"


# ── Test 3: heartbeat 파일 없음 → stale로 취급 ────────────────────────

def test_missing_heartbeat_triggers_derisk(tmp_hb: Path) -> None:
    """heartbeat.json 없음 → stale 취급, derisk 트리거."""
    now = time.time()
    # tmp_hb 파일 미생성

    exchange = FakeExchange(positions={"BTC": 0.3})
    wd = _make_watchdog(exchange, tmp_hb, now_val=now)

    triggered = wd.tick()

    assert triggered is True, "heartbeat 파일 없으면 derisk 트리거"


# ── Test 4: 중복 트리거 방지 ───────────────────────────────────────────

def test_duplicate_trigger_skipped(tmp_hb: Path) -> None:
    """이미 트리거된 상태에서 추가 stale 감지 → 중복 derisk 호출 0."""
    now = time.time()
    stale_ts = now - 120
    tmp_hb.write_text(json.dumps({"ts": stale_ts}), encoding="utf-8")

    exchange = FakeExchange(positions={"BTC": 1.0})
    wd = _make_watchdog(exchange, tmp_hb, now_val=now)

    wd.tick()  # 1회 트리거
    first_cancel_count = exchange.cancelled_orders

    wd.tick()  # 2회째: 이미 triggered=True → 중복 호출 안 함
    assert exchange.cancelled_orders == first_cancel_count, "중복 derisk 호출 0"


# ── Test 5: write_heartbeat → read 정상 확인 ─────────────────────────

def test_write_heartbeat_readable(tmp_path: Path) -> None:
    """write_heartbeat 기록 → json 파싱 가능."""
    hb_path = tmp_path / "heartbeat.json"
    ts_val = 1234567890.0
    write_heartbeat(ts=ts_val, healthy=True, path=hb_path)

    data = json.loads(hb_path.read_text(encoding="utf-8"))
    assert data["ts"] == ts_val
    assert data["healthy"] is True


# ── Test 6: import 정적검사 — 봇 코어/brain/LLM import 0 ──────────────

def test_watchdog_no_banned_imports() -> None:
    """watchdog.py 에 brain/judge/llm/consensus/HRP import 0 (AST 정적 검사)."""
    watchdog_path = Path(__file__).parent.parent / "scripts" / "watchdog.py"
    source = watchdog_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned = {"brain", "judge", "llm", "consensus", "HRP"}
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for b in banned:
                        if b.lower() in alias.name.lower():
                            violations.append(f"Import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for b in banned:
                    if b.lower() in module.lower():
                        violations.append(f"ImportFrom: {module}")

    assert not violations, f"금지된 import 발견: {violations}"


# ── Test 7: ExchangeAdapter 만 — 내부 core 금지 모듈 미사용 ─────────────

def test_watchdog_only_uses_exchange_adapter() -> None:
    """watchdog.py 이 ExchangeAdapter / DeriskExecutor 만 사용, 라이브 봇 직접 import 없음."""
    watchdog_path = Path(__file__).parent.parent / "scripts" / "watchdog.py"
    source = watchdog_path.read_text(encoding="utf-8")

    # 봇 메인 루프 import 금지
    bot_modules = [
        "live_trader",
        "rl_hybrid",
        "orchestrator",
        "portfolio_orchestrator",
        "risk_gate",   # KillSwitch 직접 의존 금지 (watchdog 은 독립)
        "unattended_fsm",  # FSM 도 봇 코어 — watchdog 은 executor 만
    ]
    for mod in bot_modules:
        assert mod not in source, f"watchdog.py 에 금지된 봇 모듈 발견: {mod}"
