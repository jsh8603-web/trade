"""SO-1 E2 멱등성 fault-injection 테스트

검증 기준:
1. 응답 유실(Timeout/ConnectionError) 후 재시도 시 거래소에 주문 1건만 존재.
2. 멱등 차단 이벤트가 execution_logs에 기록된다.
3. 깨끗한 경로(주문 성공)는 회귀 없이 정상 동작한다.
4. identifier가 POST body에 포함된다.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest
import requests as req_lib

with patch("dotenv.load_dotenv"):
    import scripts.execute_trade as mod
    from scripts.execute_trade import execute, _reconcile_recent_order, _log_idempotent_block


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Redirect file I/O and mock safety guards for all tests."""
    monkeypatch.setattr(mod, "LOCK_FILE", tmp_path / "trading.lock")
    monkeypatch.setattr(mod, "PROJECT_DIR", tmp_path)

    # Safety guard mocks
    monkeypatch.setattr(mod, "_get_daily_trades", lambda: {"date": "2099-01-01", "count": 0})
    monkeypatch.setattr(mod, "_get_last_trade_time", lambda: None)
    monkeypatch.setattr(mod, "_get_btc_position_ratio", lambda: 0.0)
    monkeypatch.setattr(mod, "_increment_daily_trades", lambda: None)
    monkeypatch.setattr(mod, "_update_last_trade_time", lambda: None)
    monkeypatch.setattr(mod, "check_open_orders_and_cancel", lambda market, side: None)
    monkeypatch.setattr(mod, "_record_trade_to_db", lambda result, source="manual": None)

    # Env
    monkeypatch.setenv("EMERGENCY_STOP", "false")
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("MAX_TRADE_AMOUNT", "100000")
    monkeypatch.setenv("MAX_DAILY_TRADES", "100")
    monkeypatch.setenv("MIN_TRADE_INTERVAL_HOURS", "0")
    monkeypatch.setenv("MAX_POSITION_RATIO", "1.0")
    monkeypatch.setenv("UPBIT_ACCESS_KEY", "test_key")
    monkeypatch.setenv("UPBIT_SECRET_KEY", "test_secret")


# ---------------------------------------------------------------------------
# Test 1: 응답 유실 후 거래소에 주문 이미 존재 → 멱등 차단
# ---------------------------------------------------------------------------

class TestE2IdempotentBlock:
    def test_timeout_with_existing_order_returns_reuse(self, tmp_path):
        """Timeout 후 _reconcile_recent_order 가 주문 반환 → idempotent_reuse=True."""
        existing_order = {"uuid": "mock-uuid-1234", "state": "wait", "side": "bid"}

        with patch("scripts.execute_trade.requests.post") as mock_post, \
             patch("scripts.execute_trade._reconcile_recent_order") as mock_reconcile:

            mock_post.side_effect = req_lib.exceptions.Timeout("forced timeout")
            mock_reconcile.return_value = existing_order

            result = execute("bid", "KRW-BTC", "50000")

        assert result["success"] is True
        assert result.get("idempotent_reuse") is True
        assert result["response"]["uuid"] == "mock-uuid-1234"
        # POST는 1회만 호출됨 (재시도 없음)
        mock_post.assert_called_once()
        mock_reconcile.assert_called_once()

    def test_connection_error_with_existing_order_blocks_duplicate(self, tmp_path):
        """ConnectionError 후 기존 주문 재사용 → 중복 발주 차단."""
        existing_order = {"uuid": "conn-uuid-5678", "state": "done", "side": "ask"}

        with patch("scripts.execute_trade.requests.post") as mock_post, \
             patch("scripts.execute_trade._reconcile_recent_order") as mock_reconcile:

            mock_post.side_effect = req_lib.exceptions.ConnectionError("forced drop")
            mock_reconcile.return_value = existing_order

            result = execute("ask", "KRW-BTC", "0.001")

        assert result["success"] is True
        assert result.get("idempotent_reuse") is True
        mock_post.assert_called_once()

    def test_idempotent_block_logged(self, tmp_path):
        """멱등 차단 시 execution_logs/idempotent_blocks.jsonl 에 기록된다."""
        existing_order = {"uuid": "log-uuid-9999", "state": "wait"}

        with patch("scripts.execute_trade.requests.post") as mock_post, \
             patch("scripts.execute_trade._reconcile_recent_order") as mock_reconcile:

            mock_post.side_effect = req_lib.exceptions.Timeout("timeout")
            mock_reconcile.return_value = existing_order

            execute("bid", "KRW-BTC", "50000")

        log_file = tmp_path / "logs" / "executions" / "idempotent_blocks.jsonl"
        assert log_file.exists(), "idempotent_blocks.jsonl 이 생성돼야 한다"
        lines = [json.loads(l) for l in log_file.read_text().splitlines()]
        assert len(lines) == 1
        assert lines[0]["event"] == "idempotent_block"
        assert lines[0]["existing_uuid"] == "log-uuid-9999"


# ---------------------------------------------------------------------------
# Test 2: 응답 유실 후 거래소에도 없음 → 실패 반환 (중복 발주 없음)
# ---------------------------------------------------------------------------

class TestE2NoOrderAfterLoss:
    def test_timeout_no_existing_order_returns_failure(self):
        """Timeout 후 거래소에도 없으면 success=False, 발주 없음."""
        with patch("scripts.execute_trade.requests.post") as mock_post, \
             patch("scripts.execute_trade._reconcile_recent_order") as mock_reconcile:

            mock_post.side_effect = req_lib.exceptions.Timeout("timeout")
            mock_reconcile.return_value = None

            result = execute("bid", "KRW-BTC", "50000")

        assert result["success"] is False
        assert "응답 유실" in result["error"]
        mock_post.assert_called_once()


# ---------------------------------------------------------------------------
# Test 3: 깨끗한 경로 — 정상 주문 성공 (회귀 없음)
# ---------------------------------------------------------------------------

class TestE2CleanPath:
    def test_successful_order_contains_identifier(self):
        """정상 주문 시 response에 identifier 포함, success=True."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"uuid": "clean-uuid", "state": "wait"}

        with patch("scripts.execute_trade.requests.post", return_value=mock_resp):
            result = execute("bid", "KRW-BTC", "50000")

        assert result["success"] is True
        assert result.get("dry_run") is False
        # identifier 가 결과에 포함돼야 함
        assert "identifier" in result
        assert result["identifier"].startswith("inv_")

    def test_successful_order_identifier_in_post_body(self):
        """POST body에 identifier 필드가 포함돼야 한다."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"uuid": "body-uuid"}

        with patch("scripts.execute_trade.requests.post", return_value=mock_resp) as mock_post:
            execute("bid", "KRW-BTC", "50000")

        call_kwargs = mock_post.call_args
        body = call_kwargs[1].get("json") or (call_kwargs[0][1] if len(call_kwargs[0]) > 1 else {})
        assert "identifier" in body
        assert body["identifier"].startswith("inv_")

    def test_ask_order_success(self):
        """매도 정상 경로 회귀 없음."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"uuid": "ask-uuid", "state": "done"}

        with patch("scripts.execute_trade.requests.post", return_value=mock_resp):
            result = execute("ask", "KRW-BTC", "0.001")

        assert result["success"] is True
        assert result["side"] == "ask"


# ---------------------------------------------------------------------------
# Test 4: _reconcile_recent_order 단위 테스트
# ---------------------------------------------------------------------------

class TestReconcileRecentOrder:
    def test_direct_identifier_lookup_found(self):
        """identifier 직접 조회 성공 시 주문 dict 반환."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"uuid": "direct-uuid", "identifier": "inv_abc123"}

        with patch("scripts.execute_trade.requests.get", return_value=mock_resp), \
             patch("scripts.execute_trade.make_auth_header", return_value={}):
            result = _reconcile_recent_order("inv_abc123", "KRW-BTC")

        assert result is not None
        assert result["uuid"] == "direct-uuid"

    def test_direct_lookup_fail_fallback_to_list(self):
        """1차 조회 실패 시 미체결 목록에서 identifier 매칭."""
        fail_resp = MagicMock()
        fail_resp.ok = False

        list_resp = MagicMock()
        list_resp.ok = True
        list_resp.json.return_value = [
            {"uuid": "list-uuid", "identifier": "inv_target", "state": "wait"},
            {"uuid": "other", "identifier": "inv_other"},
        ]

        with patch("scripts.execute_trade.requests.get", side_effect=[fail_resp, list_resp]), \
             patch("scripts.execute_trade.make_auth_header", return_value={}):
            result = _reconcile_recent_order("inv_target", "KRW-BTC")

        assert result is not None
        assert result["uuid"] == "list-uuid"

    def test_not_found_returns_none(self):
        """어디서도 못 찾으면 None 반환."""
        not_found = MagicMock()
        not_found.ok = True
        not_found.json.return_value = {}  # no uuid key

        empty_list = MagicMock()
        empty_list.ok = True
        empty_list.json.return_value = []

        with patch("scripts.execute_trade.requests.get", side_effect=[not_found, empty_list]), \
             patch("scripts.execute_trade.make_auth_header", return_value={}):
            result = _reconcile_recent_order("inv_missing", "KRW-BTC")

        assert result is None


# ---------------------------------------------------------------------------
# Test SO-6b: reconcile 2차 실패 시 reconcile_status='unknown'+success=False
# ---------------------------------------------------------------------------

class TestE2ReconcileUnknown:
    def test_reconcile_none_returns_unknown_status(self):
        """거래소에도 없으면 reconcile_status='unknown' + success=False."""
        with patch("scripts.execute_trade.requests.post") as mock_post, \
             patch("scripts.execute_trade._reconcile_recent_order") as mock_reconcile:

            mock_post.side_effect = req_lib.exceptions.Timeout("timeout")
            mock_reconcile.return_value = None

            result = execute("bid", "KRW-BTC", "50000")

        assert result["success"] is False
        assert result.get("reconcile_status") == "unknown"

    def test_reconcile_unknown_no_retry_possible(self):
        """reconcile_status='unknown' 결과는 identifier 포함 (상위 재시도 식별 가능)."""
        with patch("scripts.execute_trade.requests.post") as mock_post, \
             patch("scripts.execute_trade._reconcile_recent_order") as mock_reconcile:

            mock_post.side_effect = req_lib.exceptions.ConnectionError("drop")
            mock_reconcile.return_value = None

            result = execute("ask", "KRW-BTC", "0.001")

        assert result["success"] is False
        assert result.get("reconcile_status") == "unknown"
        assert "identifier" in result
