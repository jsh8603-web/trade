"""
Orchestrator._record_switch_to_db 유닛 테스트

v1.32.1에서 추가된 중복 방지 + machine_name 태그 로직 검증.

Coverage:
  - test_skip_when_duplicate_exists: dup_check GET이 non-empty → POST 호출 안됨
  - test_post_when_no_duplicate: dup_check = [] → POST 수행
  - test_dup_check_network_failure_continues: dup_check 예외 → POST는 수행
  - test_machine_name_included_in_row: get_machine_name="pc128" → row에 machine_name 포함
  - test_machine_name_missing_not_included: get_machine_name 예외 → row에 machine_name 없음
  - test_worker_skips_entirely: skip_trade_db=True → 어떤 HTTP 호출도 없음
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


def _make_dup_response(rows: list) -> MagicMock:
    """Supabase dup_check 응답을 흉내낸다."""
    resp = MagicMock()
    resp.ok = True
    resp.json.return_value = rows
    return resp


# ── 공통 env 패치 (SUPABASE_URL / KEY 필요) ───────

ENV_PATCH = {
    "SUPABASE_URL": "https://fake.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "fake_key",
}


# ── 1. 중복 존재 시 POST 스킵 ─────────────────────

def test_skip_when_duplicate_exists():
    orch = _make_orch()
    dup_resp = _make_dup_response([{"id": 123}])  # non-empty → 중복

    with patch.dict("os.environ", ENV_PATCH, clear=False), \
         patch("utils.machine.skip_trade_db", return_value=False), \
         patch("utils.machine.get_machine_name", return_value="pc128"), \
         patch("scripts.cycle_id.get_or_create_cycle_id", return_value="20260421-1200-agent"), \
         patch("requests.get", return_value=dup_resp) as mock_get, \
         patch("requests.post") as mock_post:
        orch._record_switch_to_db(_switch_info(), _market_state(), btc_price=150_000_000)

    # dup_check GET은 호출됨 (btc_price가 주어졌으므로 ticker GET은 없음)
    assert mock_get.call_count == 1
    # POST는 호출 안됨
    mock_post.assert_not_called()


# ── 2. 중복 없을 때 POST 수행 ─────────────────────

def test_post_when_no_duplicate():
    orch = _make_orch()
    dup_resp = _make_dup_response([])  # 빈 결과 → 중복 없음

    with patch.dict("os.environ", ENV_PATCH, clear=False), \
         patch("utils.machine.skip_trade_db", return_value=False), \
         patch("utils.machine.get_machine_name", return_value="pc128"), \
         patch("scripts.cycle_id.get_or_create_cycle_id", return_value="20260421-1200-agent"), \
         patch("requests.get", return_value=dup_resp), \
         patch("requests.post") as mock_post:
        orch._record_switch_to_db(_switch_info(), _market_state(), btc_price=150_000_000)

    mock_post.assert_called_once()
    # POST URL 및 row 내용 확인
    call = mock_post.call_args
    assert "/rest/v1/agent_switches" in call.args[0]
    sent_row = call.kwargs["json"]
    assert sent_row["from_agent"] == "conservative"
    assert sent_row["to_agent"] == "aggressive"
    assert sent_row["cycle_id"] == "20260421-1200-agent"


# ── 3. dup_check 네트워크 실패여도 POST는 수행 ───

def test_dup_check_network_failure_continues():
    orch = _make_orch()

    with patch.dict("os.environ", ENV_PATCH, clear=False), \
         patch("utils.machine.skip_trade_db", return_value=False), \
         patch("utils.machine.get_machine_name", return_value="pc128"), \
         patch("scripts.cycle_id.get_or_create_cycle_id", return_value="20260421-1200-agent"), \
         patch("requests.get", side_effect=Exception("network down")), \
         patch("requests.post") as mock_post:
        orch._record_switch_to_db(_switch_info(), _market_state(), btc_price=150_000_000)

    mock_post.assert_called_once()


# ── 4. machine_name 있으면 row에 포함 ────────────

def test_machine_name_included_in_row():
    orch = _make_orch()
    dup_resp = _make_dup_response([])

    with patch.dict("os.environ", ENV_PATCH, clear=False), \
         patch("utils.machine.skip_trade_db", return_value=False), \
         patch("utils.machine.get_machine_name", return_value="pc128"), \
         patch("scripts.cycle_id.get_or_create_cycle_id", return_value="20260421-1200-agent"), \
         patch("requests.get", return_value=dup_resp), \
         patch("requests.post") as mock_post:
        orch._record_switch_to_db(_switch_info(), _market_state(), btc_price=150_000_000)

    sent_row = mock_post.call_args.kwargs["json"]
    assert "machine_name" in sent_row
    assert sent_row["machine_name"] == "pc128"


# ── 5. machine_name 조회 실패 시 키 제외 ─────────

def test_machine_name_missing_not_included():
    orch = _make_orch()
    dup_resp = _make_dup_response([])

    with patch.dict("os.environ", ENV_PATCH, clear=False), \
         patch("utils.machine.skip_trade_db", return_value=False), \
         patch("utils.machine.get_machine_name", side_effect=Exception("no hostname")), \
         patch("scripts.cycle_id.get_or_create_cycle_id", return_value="20260421-1200-agent"), \
         patch("requests.get", return_value=dup_resp), \
         patch("requests.post") as mock_post:
        orch._record_switch_to_db(_switch_info(), _market_state(), btc_price=150_000_000)

    sent_row = mock_post.call_args.kwargs["json"]
    assert "machine_name" not in sent_row


# ── 6. worker(skip_trade_db=True)면 완전히 early return ─

def test_worker_skips_entirely():
    orch = _make_orch()

    with patch.dict("os.environ", ENV_PATCH, clear=False), \
         patch("utils.machine.skip_trade_db", return_value=True), \
         patch("utils.machine.get_machine_name", return_value="pc128"), \
         patch("scripts.cycle_id.get_or_create_cycle_id", return_value="20260421-1200-agent"), \
         patch("requests.get") as mock_get, \
         patch("requests.post") as mock_post:
        orch._record_switch_to_db(_switch_info(), _market_state(), btc_price=150_000_000)

    # skip_trade_db=True면 HTTP 호출 전혀 없어야 함
    mock_get.assert_not_called()
    mock_post.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
