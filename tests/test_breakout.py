"""변동성 돌파 trader/monitor 단위 테스트.

DRY_RUN 모드에서 모든 로직 시뮬 검증 + monitor 빈도 조절 + 빠른 종료 경로.
실제 Upbit API는 mock으로 차단.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

KST = timezone(timedelta(hours=9))


@pytest.fixture(autouse=True)
def _isolate_state(tmp_path, monkeypatch):
    """state 파일을 tmp로 격리 + DRY_RUN 강제 + 텔레그램 mock."""
    state_path = tmp_path / "breakout_state.json"
    monkeypatch.setenv("BREAKOUT_ENABLED", "true")
    monkeypatch.setenv("BREAKOUT_DRY_RUN", "true")
    monkeypatch.setenv("BREAKOUT_K", "0.7")
    monkeypatch.setenv("BREAKOUT_BUY_AMOUNT", "300000")
    monkeypatch.setenv("BREAKOUT_STOP_LOSS_PCT", "-2.0")
    monkeypatch.setenv("BREAKOUT_TIME_EXIT_HOURS", "24")
    monkeypatch.setenv("BREAKOUT_NOTIFY_NO_SIGNAL", "true")
    monkeypatch.setenv("EMERGENCY_STOP", "false")

    import scripts.breakout_trader as bt
    monkeypatch.setattr(bt, "STATE_PATH", state_path)
    monkeypatch.setattr(bt, "notify", lambda text: None)
    yield state_path


# ═══ trader.cfg() ═══

class TestCfg:
    def test_reads_env_correctly(self):
        from scripts.breakout_trader import cfg
        c = cfg()
        assert c["enabled"] is True
        assert c["dry_run"] is True
        assert c["k"] == 0.7
        assert c["buy_amount"] == 300_000
        assert c["stop_loss_pct"] == -2.0
        assert c["time_exit_h"] == 24


# ═══ 매수 평가 — 시그널 케이스 ═══

class TestBuySignal:
    @patch("scripts.breakout_trader.get_current_btc_price")
    @patch("scripts.breakout_trader.get_today_open")
    @patch("scripts.breakout_trader.get_yesterday_ohlc")
    def test_breakout_triggers_buy(self, mock_y, mock_o, mock_c):
        from scripts.breakout_trader import main, load_state
        # 어제 H=119M L=117M Range=2M, 오늘 시초 118M, K=0.7
        # Target = 118M + 2M*0.7 = 119.4M
        mock_y.return_value = {"open": 118_000_000, "high": 119_000_000,
                               "low": 117_000_000, "close": 118_500_000, "date": "2026-05-03"}
        mock_o.return_value = 118_000_000
        mock_c.return_value = 119_500_000  # >= 119.4M 돌파!

        rc = main()
        assert rc == 0
        state = load_state()
        assert state["active_position"] is not None
        pos = state["active_position"]
        assert pos["dry_run"] is True
        assert pos["btc_volume"] > 0
        assert pos["stop_loss_price"] == pytest.approx(pos["buy_price"] * 0.98, rel=1e-3)

    @patch("scripts.breakout_trader.get_current_btc_price")
    @patch("scripts.breakout_trader.get_today_open")
    @patch("scripts.breakout_trader.get_yesterday_ohlc")
    def test_no_breakout_no_buy(self, mock_y, mock_o, mock_c):
        from scripts.breakout_trader import main, load_state
        mock_y.return_value = {"open": 118_000_000, "high": 119_000_000,
                               "low": 117_000_000, "close": 118_500_000, "date": "2026-05-03"}
        mock_o.return_value = 118_000_000
        mock_c.return_value = 119_300_000  # 119.4M 미달

        rc = main()
        assert rc == 0
        state = load_state()
        assert state["active_position"] is None
        assert state["last_signal"]["type"] == "NONE"


# ═══ EMERGENCY_STOP / DISABLED ═══

class TestSafetyGuards:
    def test_disabled_returns_immediately(self, monkeypatch):
        from scripts.breakout_trader import main, load_state
        monkeypatch.setenv("BREAKOUT_ENABLED", "false")
        rc = main()
        assert rc == 0
        # state 파일은 안 만들어졌어야 함 (load_state는 기본값 반환)
        s = load_state()
        assert s["active_position"] is None

    @patch("scripts.breakout_trader.get_current_btc_price")
    @patch("scripts.breakout_trader.get_today_open")
    @patch("scripts.breakout_trader.get_yesterday_ohlc")
    def test_emergency_stop_blocks_buy(self, mock_y, mock_o, mock_c, monkeypatch):
        from scripts.breakout_trader import main, load_state
        monkeypatch.setenv("EMERGENCY_STOP", "true")
        mock_y.return_value = {"open": 118_000_000, "high": 119_000_000,
                               "low": 117_000_000, "close": 118_500_000, "date": "2026-05-03"}
        mock_o.return_value = 118_000_000
        mock_c.return_value = 999_999_999  # 무조건 돌파지만 차단되어야

        rc = main()
        assert rc == 0
        s = load_state()
        assert s["active_position"] is None  # 매수 안 됨


# ═══ 보유 중 — 같은 날 신규 매수 X ═══

class TestPositionHolding:
    def test_holding_no_new_buy(self, _isolate_state):
        from scripts.breakout_trader import main, load_state, save_state
        # 미리 active_position 주입 (1시간 전 매수)
        entered = (datetime.now(KST) - timedelta(hours=1)).isoformat()
        state = {
            "active_position": {
                "buy_price": 117_000_000,
                "btc_volume": 0.00256,
                "krw_amount": 300000,
                "entered_at": entered,
                "stop_loss_price": 114_660_000,
                "target_exit_at": (datetime.now(KST) + timedelta(hours=23)).isoformat(),
                "K": 0.7,
                "dry_run": True,
            },
            "history": [], "last_check": None, "last_signal": None,
        }
        save_state(state)

        rc = main()
        assert rc == 0
        # active_position 그대로 있어야 (24h 미경과)
        s = load_state()
        assert s["active_position"] is not None
        assert s["active_position"]["buy_price"] == 117_000_000

    @patch("scripts.breakout_trader.get_current_btc_price")
    def test_24h_elapsed_triggers_sell(self, mock_p_tra, _isolate_state):
        from scripts.breakout_trader import main, load_state, save_state
        # 25시간 전 매수
        entered = (datetime.now(KST) - timedelta(hours=25)).isoformat()
        state = {
            "active_position": {
                "buy_price": 117_000_000,
                "btc_volume": 0.00256,
                "krw_amount": 300000,
                "entered_at": entered,
                "stop_loss_price": 114_660_000,
                "target_exit_at": (datetime.now(KST) - timedelta(hours=1)).isoformat(),
                "K": 0.7,
                "dry_run": True,
            },
            "history": [], "last_check": None, "last_signal": None,
        }
        save_state(state)
        mock_p_tra.return_value = 118_500_000  # +1.28%

        rc = main()
        assert rc == 0
        s = load_state()
        assert s["active_position"] is None  # 청산됨
        assert len(s["history"]) == 1
        h = s["history"][0]
        assert "정상 청산" in h["exit_reason"] or "24h" in h["exit_reason"]
        assert h["pnl_pct"] > 0


# ═══ Monitor 빈도 조절 ═══

class TestMonitorFrequency:
    def test_should_process_within_3h(self):
        from scripts.breakout_monitor import should_process
        # 0~3h: 모든 분에 처리
        assert should_process(0.5, 7) is True
        assert should_process(1.5, 22) is True
        assert should_process(2.99, 45) is True

    def test_should_skip_after_3h_non_hour(self):
        from scripts.breakout_monitor import should_process
        # 3h+: 정시만 처리 (0~4분)
        assert should_process(5.0, 0) is True   # 정시
        assert should_process(5.0, 4) is True   # 정시 5분 이내
        assert should_process(5.0, 15) is False
        assert should_process(5.0, 30) is False
        assert should_process(5.0, 45) is False
        assert should_process(20.0, 30) is False  # 20h 후도 정시 외엔 X


# ═══ Monitor 손절 발동 ═══

class TestMonitorStopLoss:
    @patch("scripts.breakout_trader.get_current_btc_price")
    @patch("scripts.breakout_monitor.get_current_btc_price")
    def test_stop_loss_triggers_sell(self, mock_p_mon, mock_p_tra, _isolate_state):
        # monitor가 가격 조회 후 trader.execute_sell 호출 — 두 곳 모두 mock 필요
        from scripts.breakout_monitor import main as monitor_main
        from scripts.breakout_trader import load_state, save_state
        entered = (datetime.now(KST) - timedelta(hours=1)).isoformat()
        state = {
            "active_position": {
                "buy_price": 117_000_000,
                "btc_volume": 0.00256,
                "krw_amount": 300000,
                "entered_at": entered,
                "stop_loss_price": 114_660_000,
                "target_exit_at": (datetime.now(KST) + timedelta(hours=23)).isoformat(),
                "K": 0.7,
                "dry_run": True,
            },
            "history": [], "last_check": None, "last_signal": None,
        }
        save_state(state)
        mock_p_mon.return_value = 114_500_000
        mock_p_tra.return_value = 114_500_000  # -2.14% 도달

        rc = monitor_main()
        assert rc == 0
        s = load_state()
        assert s["active_position"] is None  # 손절 발동, 청산
        assert len(s["history"]) == 1
        assert "손절" in s["history"][0]["exit_reason"]
        assert s["history"][0]["pnl_pct"] < -1.5  # 약 -2%대

    @patch("scripts.breakout_monitor.get_current_btc_price")
    def test_no_stop_loss_when_above(self, mock_p, _isolate_state):
        from scripts.breakout_monitor import main as monitor_main
        from scripts.breakout_trader import load_state, save_state
        entered = (datetime.now(KST) - timedelta(hours=1)).isoformat()
        state = {
            "active_position": {
                "buy_price": 117_000_000,
                "btc_volume": 0.00256,
                "krw_amount": 300000,
                "entered_at": entered,
                "stop_loss_price": 114_660_000,
                "target_exit_at": (datetime.now(KST) + timedelta(hours=23)).isoformat(),
                "K": 0.7,
                "dry_run": True,
            },
            "history": [], "last_check": None, "last_signal": None,
        }
        save_state(state)
        mock_p.return_value = 116_000_000  # -0.85% (손절 미달)

        rc = monitor_main()
        assert rc == 0
        s = load_state()
        assert s["active_position"] is not None  # 보유 유지

    def test_no_position_quick_exit(self, _isolate_state):
        from scripts.breakout_monitor import main as monitor_main
        rc = monitor_main()
        assert rc == 0  # state 파일 없거나 active_position None — 즉시 종료
