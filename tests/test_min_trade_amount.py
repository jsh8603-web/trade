"""MIN_TRADE_AMOUNT 하한 안전장치(ET-06) 테스트."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


@pytest.fixture
def live_env(monkeypatch, tmp_path):
    """DRY_RUN=false, daily/last_trade 제약 우회, portfolio 정상 응답 모킹."""
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("EMERGENCY_STOP", "false")
    monkeypatch.setenv("UPBIT_ACCESS_KEY", "test_access")
    monkeypatch.setenv("UPBIT_SECRET_KEY", "test_secret")
    monkeypatch.setenv("MAX_TRADE_AMOUNT", "1000000")
    monkeypatch.setenv("MAX_DAILY_TRADES", "100")
    monkeypatch.setenv("MAX_POSITION_RATIO", "0.95")
    monkeypatch.setenv("MIN_TRADE_INTERVAL_HOURS", "0")

    # daily_trades/last_trade 파일 격리
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr("scripts.execute_trade.DAILY_TRADES_FILE", data_dir / "daily_trades.json")
    monkeypatch.setattr("scripts.execute_trade.LAST_TRADE_TIME_FILE", data_dir / "last_trade_time.txt")
    monkeypatch.setattr("scripts.execute_trade.LOCK_FILE", data_dir / "trading.lock")

    # auto_emergency 경로 우회 — 존재하지 않는 곳으로
    monkeypatch.setattr("scripts.execute_trade.PROJECT_DIR", tmp_path)

    # 포지션 비율 계산 스킵
    with patch("scripts.execute_trade._get_btc_position_ratio", return_value=0.1):
        yield


def test_min_amount_blocks_below_threshold(live_env, monkeypatch):
    """MIN_TRADE_AMOUNT=5000 기본값에서 4000원 매수는 스킵됨."""
    from scripts import execute_trade
    # ET-06 체크는 ET-05(포지션) 이후에 있음 → 포지션 OK 상태에서만 닿음
    result = execute_trade.execute("bid", "KRW-BTC", "4000")
    assert result["success"] is False
    assert result.get("skipped") is True
    assert "하한 미달" in result["error"]


def test_min_amount_allows_at_threshold(live_env, monkeypatch):
    """정확히 5000원은 통과(실제 주문 호출은 모킹)."""
    from scripts import execute_trade

    fake_resp = MagicMock()
    fake_resp.ok = True
    fake_resp.json.return_value = {"uuid": "test-uuid", "price": "112000000"}
    fake_resp.text = ""

    with patch("scripts.execute_trade.requests.post", return_value=fake_resp):
        result = execute_trade.execute("bid", "KRW-BTC", "5000")
    assert result["success"] is True
    assert result.get("skipped") is not True


def test_min_amount_custom_env(live_env, monkeypatch):
    """MIN_TRADE_AMOUNT=10000 설정 시 9999원은 스킵, 10000원은 통과."""
    monkeypatch.setenv("MIN_TRADE_AMOUNT", "10000")
    from scripts import execute_trade

    result_blocked = execute_trade.execute("bid", "KRW-BTC", "9999")
    assert result_blocked["success"] is False
    assert result_blocked.get("skipped") is True
    assert "9999" in result_blocked["error"]
    assert "10000" in result_blocked["error"]


def test_min_amount_ignored_on_ask(live_env, monkeypatch):
    """매도(ask)는 volume 기반이므로 MIN_TRADE_AMOUNT 적용되지 않음."""
    monkeypatch.setenv("MIN_TRADE_AMOUNT", "100000")
    from scripts import execute_trade
    import subprocess as _sp

    fake_pf = MagicMock()
    fake_pf.returncode = 0
    fake_pf.stdout = '{"holdings":[{"currency":"BTC","balance":10.0}]}'

    fake_resp = MagicMock()
    fake_resp.ok = True
    fake_resp.json.return_value = {"uuid": "sell-uuid"}
    fake_resp.text = ""

    # 매도 경로는 ET-06 체크를 거치지만 side=="ask"이므로 통과해야 함
    with patch.object(_sp, "run", return_value=fake_pf), \
         patch("scripts.execute_trade.requests.post", return_value=fake_resp):
        result = execute_trade.execute("ask", "KRW-BTC", "0.001")

    # 매도는 MIN_TRADE_AMOUNT에 걸리지 않아야 함
    assert "하한 미달" not in (result.get("error") or "")


def test_min_amount_float_string(live_env, monkeypatch):
    """'4999.5' 같은 float 문자열도 정상 처리."""
    from scripts import execute_trade

    result = execute_trade.execute("bid", "KRW-BTC", "4999.5")
    assert result["success"] is False
    assert result.get("skipped") is True
