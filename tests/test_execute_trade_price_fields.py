"""
Unit tests for _record_trade_to_db's v1.32.1 current_price/trade_amount logic.

Target: scripts/execute_trade.py lines 545-605
  - current_price: response.price 우선, 없으면 Upbit /ticker fallback
  - trade_amount: bid→amount, ask→funds/executed_funds / volume*price / amount*price

All network calls (requests.get/post) and utils.machine.* are mocked.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

with patch("dotenv.load_dotenv"):
    from scripts.execute_trade import _record_trade_to_db


# ── Fixtures ────────────────────────────────────────────────

@pytest.fixture
def supabase_env(monkeypatch):
    """Set Supabase credentials so _record_trade_to_db actually runs."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")


@pytest.fixture
def ok_post():
    """POST mock that returns a successful response."""
    resp = MagicMock()
    resp.ok = True
    resp.status_code = 201
    return resp


@pytest.fixture
def _patches():
    """Common patch set: skip_trade_db=False + get_machine_name=pc-test."""
    with patch("utils.machine.skip_trade_db", return_value=False) as skip, \
         patch("utils.machine.get_machine_name", return_value="pc-test") as mname:
        yield skip, mname


# ── Tests ───────────────────────────────────────────────────

class TestCurrentPrice:
    def test_current_price_from_response(self, supabase_env, ok_post, _patches):
        """response.price가 있으면 ticker API 호출 없이 그걸 사용."""
        with patch("scripts.execute_trade.requests.post", return_value=ok_post) as mp, \
             patch("scripts.execute_trade.requests.get") as mg:
            result = {
                "side": "bid",
                "success": True,
                "market": "KRW-BTC",
                "amount": "50000",
                "dry_run": False,
                "response": {"uuid": "u1", "price": "100000000", "volume": "0.0005"},
            }
            _record_trade_to_db(result, source="agent")

        mg.assert_not_called()  # ticker fallback 호출 안 됨
        row = mp.call_args[1]["json"]
        assert row["current_price"] == 100000000

    def test_current_price_fallback_to_ticker(self, supabase_env, ok_post, _patches):
        """response.price 없으면 Upbit /ticker로 fallback."""
        ticker_resp = MagicMock()
        ticker_resp.ok = True
        ticker_resp.json.return_value = [{"trade_price": 95000000.0}]

        with patch("scripts.execute_trade.requests.post", return_value=ok_post) as mp, \
             patch("scripts.execute_trade.requests.get", return_value=ticker_resp) as mg:
            result = {
                "side": "bid",
                "success": True,
                "market": "KRW-BTC",
                "amount": "50000",
                "dry_run": False,
                "response": {"uuid": "u2"},  # price 없음
            }
            _record_trade_to_db(result, source="agent")

        mg.assert_called_once()
        # ticker URL/params 확인
        args, kwargs = mg.call_args
        assert "/ticker" in args[0]
        assert kwargs["params"]["markets"] == "KRW-BTC"
        row = mp.call_args[1]["json"]
        assert row["current_price"] == 95000000

    def test_current_price_ticker_failure_safe(self, supabase_env, ok_post, _patches):
        """ticker 호출이 예외여도 함수는 죽지 않고 current_price 없이 기록."""
        with patch("scripts.execute_trade.requests.post", return_value=ok_post) as mp, \
             patch("scripts.execute_trade.requests.get",
                   side_effect=Exception("network down")):
            result = {
                "side": "bid",
                "success": True,
                "market": "KRW-BTC",
                "amount": "50000",
                "dry_run": False,
                "response": {},  # price 없음 → fallback 시도 → 실패
            }
            # Should NOT raise
            _record_trade_to_db(result, source="agent")

        mp.assert_called_once()
        row = mp.call_args[1]["json"]
        # current_price는 None이므로 row에 키가 없어야 함
        assert "current_price" not in row


class TestTradeAmount:
    def test_trade_amount_for_bid(self, supabase_env, ok_post, _patches):
        """side=bid이면 result.amount가 그대로 trade_amount (KRW)."""
        with patch("scripts.execute_trade.requests.post", return_value=ok_post) as mp, \
             patch("scripts.execute_trade.requests.get"):
            result = {
                "side": "bid",
                "success": True,
                "market": "KRW-BTC",
                "amount": "75000",
                "dry_run": False,
                "response": {"uuid": "u3", "price": "100000000"},
            }
            _record_trade_to_db(result, source="agent")

        row = mp.call_args[1]["json"]
        assert row["trade_amount"] == 75000.0

    def test_trade_amount_for_ask_with_funds(self, supabase_env, ok_post, _patches):
        """side=ask이고 response.funds가 있으면 그걸 사용."""
        with patch("scripts.execute_trade.requests.post", return_value=ok_post) as mp, \
             patch("scripts.execute_trade.requests.get"):
            result = {
                "side": "ask",
                "success": True,
                "market": "KRW-BTC",
                "amount": "0.001",
                "dry_run": False,
                "response": {
                    "uuid": "u4",
                    "price": "100000000",
                    "volume": "0.001",
                    "funds": "99500",  # 수수료 차감된 실제 KRW
                },
            }
            _record_trade_to_db(result, source="agent")

        row = mp.call_args[1]["json"]
        assert row["trade_amount"] == 99500.0

    def test_trade_amount_for_ask_with_volume_price(
            self, supabase_env, ok_post, _patches):
        """funds 없을 땐 volume * price 로 계산."""
        with patch("scripts.execute_trade.requests.post", return_value=ok_post) as mp, \
             patch("scripts.execute_trade.requests.get"):
            result = {
                "side": "ask",
                "success": True,
                "market": "KRW-BTC",
                "amount": "0.002",
                "dry_run": False,
                "response": {
                    "uuid": "u5",
                    "price": "50000000",
                    "volume": "0.002",
                    # funds, executed_funds 모두 없음
                },
            }
            _record_trade_to_db(result, source="agent")

        row = mp.call_args[1]["json"]
        assert row["trade_amount"] == pytest.approx(0.002 * 50000000)


class TestDryRunRecording:
    def test_dry_run_still_records_current_price(
            self, supabase_env, ok_post, _patches):
        """dry_run=True여도 ticker fallback으로 current_price가 채워져야 함."""
        ticker_resp = MagicMock()
        ticker_resp.ok = True
        ticker_resp.json.return_value = [{"trade_price": 88000000.0}]

        with patch("scripts.execute_trade.requests.post", return_value=ok_post) as mp, \
             patch("scripts.execute_trade.requests.get",
                   return_value=ticker_resp) as mg:
            result = {
                "side": "bid",
                "success": True,
                "market": "KRW-BTC",
                "amount": "30000",
                "dry_run": True,
                "response": {},  # DRY_RUN이면 price 없음 → ticker fallback
            }
            _record_trade_to_db(result, source="manual")

        mg.assert_called_once()
        row = mp.call_args[1]["json"]
        assert row["dry_run"] is True
        assert row["current_price"] == 88000000
        # bid라 amount 그대로 KRW
        assert row["trade_amount"] == 30000.0
