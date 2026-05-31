"""
Orchestrator._record_switch_to_db 유닛 테스트

v1.32.1에서 추가된 중복 방지 + machine_name 태그 로직 검증.
(SQLite 어댑터 이관 후: requests mock → core.db.db mock)

Coverage:
  - test_skip_when_duplicate_exists: dup select가 non-empty → insert 호출 안됨
  - test_post_when_no_duplicate: dup select = [] → insert 수행
  - test_dup_check_network_failure_continues: dup select 예외 → insert는 수행
  - test_machine_name_included_in_row: get_machine_name="pc128" → row에 machine_name 포함
  - test_machine_name_missing_not_included: get_machine_name 예외 → row에 machine_name 없음
  - test_worker_skips_entirely: skip_trade_db=True → 어떤 DB 호출도 없음
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.orchestrator import Orchestrator


# ── 헬퍼 ───────────────────────────────────────────

def _make_orch() -> Orchestrator:
    """무거운 __init__을 우회하여 최소한의 Orchestrator 인스턴스를 만든다."""
    orch = Orchestrator.__new__(Orchestrator)
    orch.state = {"active_agent": "moderate"}
    orch._active_agent_name = "moderate"
    orch._switch_reason = ""
    orch._learning_data = None
    orch._state_dirty = False
    orch._cached_agent = None
    return orch


def _switch_info() -> dict:
    return {"from": "conservative", "to": "aggressive", "reason": "test_reason"}


def _market_state() -> dict:
    return {
        "fgi": 30,
        "rsi": 45.0,
        "price_change_24h": -1.5,
        "kimchi_pct": 2.0,
        "fusion_signal": "neutral",
        "consecutive_losses": 1,
    }


def _make_db_mock(dup_rows: list | None = None, select_raises: bool = False) -> MagicMock:
    """core.db.db 어댑터 mock. select → dup 조회, insert → 기록.

    db.select 는 _record_switch_to_db 안에서 dup 체크에만 쓰인다.
    """
    db = MagicMock()
    if select_raises:
        db.select.side_effect = Exception("network down")
    else:
        db.select.return_value = dup_rows if dup_rows is not None else []
    db.insert.return_value = None
    return db


# ── 1. 중복 존재 시 insert 스킵 ─────────────────────

def test_skip_when_duplicate_exists():
    orch = _make_orch()
    db = _make_db_mock(dup_rows=[{"id": 123}])  # non-empty → 중복

    with patch("utils.machine.skip_trade_db", return_value=False), \
         patch("utils.machine.get_machine_name", return_value="pc128"), \
         patch("scripts.cycle_id.get_or_create_cycle_id", return_value="20260421-1200-agent"), \
         patch("agents.orchestrator.db", db):
        orch._record_switch_to_db(_switch_info(), _market_state(), btc_price=150_000_000)

    # dup select는 호출됨
    assert db.select.call_count == 1
    # insert는 호출 안됨
    db.insert.assert_not_called()


# ── 2. 중복 없을 때 insert 수행 ─────────────────────

def test_post_when_no_duplicate():
    orch = _make_orch()
    db = _make_db_mock(dup_rows=[])  # 빈 결과 → 중복 없음

    with patch("utils.machine.skip_trade_db", return_value=False), \
         patch("utils.machine.get_machine_name", return_value="pc128"), \
         patch("scripts.cycle_id.get_or_create_cycle_id", return_value="20260421-1200-agent"), \
         patch("agents.orchestrator.db", db):
        orch._record_switch_to_db(_switch_info(), _market_state(), btc_price=150_000_000)

    db.insert.assert_called_once()
    # insert 대상 테이블 및 row 내용 확인
    call = db.insert.call_args
    assert call.args[0] == "agent_switches"
    sent_row = call.args[1]
    assert sent_row["from_agent"] == "conservative"
    assert sent_row["to_agent"] == "aggressive"
    assert sent_row["cycle_id"] == "20260421-1200-agent"


# ── 3. dup select 실패여도 insert는 수행 ───

def test_dup_check_network_failure_continues():
    orch = _make_orch()
    db = _make_db_mock(select_raises=True)

    with patch("utils.machine.skip_trade_db", return_value=False), \
         patch("utils.machine.get_machine_name", return_value="pc128"), \
         patch("scripts.cycle_id.get_or_create_cycle_id", return_value="20260421-1200-agent"), \
         patch("agents.orchestrator.db", db):
        orch._record_switch_to_db(_switch_info(), _market_state(), btc_price=150_000_000)

    db.insert.assert_called_once()


# ── 4. machine_name 있으면 row에 포함 ────────────

def test_machine_name_included_in_row():
    orch = _make_orch()
    db = _make_db_mock(dup_rows=[])

    with patch("utils.machine.skip_trade_db", return_value=False), \
         patch("utils.machine.get_machine_name", return_value="pc128"), \
         patch("scripts.cycle_id.get_or_create_cycle_id", return_value="20260421-1200-agent"), \
         patch("agents.orchestrator.db", db):
        orch._record_switch_to_db(_switch_info(), _market_state(), btc_price=150_000_000)

    sent_row = db.insert.call_args.args[1]
    assert "machine_name" in sent_row
    assert sent_row["machine_name"] == "pc128"


# ── 5. machine_name 조회 실패 시 키 제외 ─────────

def test_machine_name_missing_not_included():
    orch = _make_orch()
    db = _make_db_mock(dup_rows=[])

    with patch("utils.machine.skip_trade_db", return_value=False), \
         patch("utils.machine.get_machine_name", side_effect=Exception("no hostname")), \
         patch("scripts.cycle_id.get_or_create_cycle_id", return_value="20260421-1200-agent"), \
         patch("agents.orchestrator.db", db):
        orch._record_switch_to_db(_switch_info(), _market_state(), btc_price=150_000_000)

    sent_row = db.insert.call_args.args[1]
    assert "machine_name" not in sent_row


# ── 6. worker(skip_trade_db=True)면 완전히 early return ─

def test_worker_skips_entirely():
    orch = _make_orch()
    db = _make_db_mock(dup_rows=[])

    with patch("utils.machine.skip_trade_db", return_value=True), \
         patch("utils.machine.get_machine_name", return_value="pc128"), \
         patch("scripts.cycle_id.get_or_create_cycle_id", return_value="20260421-1200-agent"), \
         patch("agents.orchestrator.db", db):
        orch._record_switch_to_db(_switch_info(), _market_state(), btc_price=150_000_000)

    # skip_trade_db=True면 DB 호출 전혀 없어야 함
    db.select.assert_not_called()
    db.insert.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
