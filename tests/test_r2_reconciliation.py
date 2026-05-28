"""SO-2 R2 reconciliation fault-injection 테스트

검증 기준:
1. mock drift 주입 → 다음 사이클이 drift 감지하고 halt + 기록 (자동보정 안 함).
2. 미체결 주문 보유 중 주입 → locked 합산으로 가짜 halt 안 일으킴.
3. DB 스냅샷 없으면 검사 생략(첫 실행).
4. 매도 시 _clamp_to_balance가 실잔량 초과 방지.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# live_trader imports
with patch("dotenv.load_dotenv"), \
     patch("rl_hybrid.config.config"), \
     patch("rl_hybrid.rl.state_encoder.StateEncoder"), \
     patch("rl_hybrid.rl.decision_blender.DecisionBlender"):
    try:
        from rl_hybrid.rl.live_trader import LiveTrader
        LIVE_TRADER_IMPORTABLE = True
    except Exception:
        LIVE_TRADER_IMPORTABLE = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trader(tmp_path):
    """Minimal LiveTrader with all heavy deps mocked."""
    with patch("rl_hybrid.rl.live_trader.StateEncoder"), \
         patch("rl_hybrid.rl.live_trader.DecisionBlender"), \
         patch.object(LiveTrader, "__init__", lambda self, *a, **kw: None):
        trader = LiveTrader.__new__(LiveTrader)
        trader.project_root = str(tmp_path)
        trader.enable_rl = False
        trader.enable_llm = False
        trader._cycle_count = 0
        trader.blender = MagicMock()
        trader.encoder = MagicMock()
        trader.trainer = None
        trader.learner = None
        trader.registry = None
    return trader


LIVE_PORTFOLIO_BTC = {
    "krw_balance": 1_000_000.0,
    "holdings": [{"currency": "BTC", "balance": 0.01, "eval_amount": 1_000_000.0}],
    "total_eval": 2_000_000.0,
}

DB_SNAP_MATCH = {
    "btc_balance": 0.01,
    "krw_balance": 1_000_000.0,
    "created_at": "2026-05-28T00:00:00+09:00",
}

DB_SNAP_DRIFT = {
    "btc_balance": 0.02,   # DB shows 0.02 but exchange has 0.01 → 50% drift
    "krw_balance": 1_000_000.0,
    "created_at": "2026-05-28T00:00:00+09:00",
}


# ---------------------------------------------------------------------------
# Conditional skip if import failed
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.skipif(
    not LIVE_TRADER_IMPORTABLE,
    reason="LiveTrader import requires optional torch/rl_hybrid deps",
)


# ---------------------------------------------------------------------------
# Test 1: drift 주입 → halt + 기록
# ---------------------------------------------------------------------------

class TestR2DriftDetection:
    def test_drift_triggers_halt(self, tmp_path):
        trader = _make_trader(tmp_path)
        with patch.object(trader, "_get_db_portfolio_snapshot", return_value=DB_SNAP_DRIFT), \
             patch.object(trader, "_get_open_orders_locked", return_value=0.0):
            result = trader._check_portfolio_drift(LIVE_PORTFOLIO_BTC, drift_threshold=0.05)
        assert result["halt"] is True
        assert "drift" in result["reason"].lower()

    def test_drift_halt_logs_to_file(self, tmp_path):
        trader = _make_trader(tmp_path)
        with patch.object(trader, "_get_db_portfolio_snapshot", return_value=DB_SNAP_DRIFT), \
             patch.object(trader, "_get_open_orders_locked", return_value=0.0):
            drift_result = trader._check_portfolio_drift(LIVE_PORTFOLIO_BTC, drift_threshold=0.05)

        trader._log_execution({"event": "r2_drift_halt", **drift_result})

        log_file = tmp_path / "logs" / "executions" / "live_trader_events.jsonl"
        assert log_file.exists()
        lines = [json.loads(l) for l in log_file.read_text().splitlines()]
        assert any(l.get("event") == "r2_drift_halt" for l in lines)

    def test_no_auto_correction(self, tmp_path):
        """halt 시 잔고 자동보정 없음 — DB/exchange 값 변경 없음."""
        trader = _make_trader(tmp_path)
        original_db = dict(DB_SNAP_DRIFT)
        with patch.object(trader, "_get_db_portfolio_snapshot", return_value=DB_SNAP_DRIFT), \
             patch.object(trader, "_get_open_orders_locked", return_value=0.0):
            trader._check_portfolio_drift(LIVE_PORTFOLIO_BTC, drift_threshold=0.05)
        # DB 스냅샷 값 변경 없음
        assert DB_SNAP_DRIFT["btc_balance"] == original_db["btc_balance"]


# ---------------------------------------------------------------------------
# Test 2: 미체결 locked 합산 → 가짜 halt 방지
# ---------------------------------------------------------------------------

class TestR2LockedOrdersFalseHaltPrevention:
    def test_locked_included_prevents_false_halt(self, tmp_path):
        """DB=0.02 BTC, exchange=0.01 live + 0.01 locked ask → 합산 0.02 = 일치 → halt X."""
        trader = _make_trader(tmp_path)
        with patch.object(trader, "_get_db_portfolio_snapshot", return_value=DB_SNAP_DRIFT), \
             patch.object(trader, "_get_open_orders_locked", return_value=0.01):
            result = trader._check_portfolio_drift(LIVE_PORTFOLIO_BTC, drift_threshold=0.05)
        assert result["halt"] is False
        assert result["locked_btc"] == 0.01

    def test_partial_locked_still_detects_real_drift(self, tmp_path):
        """locked 이 있어도 real drift 는 감지."""
        db_snap = {"btc_balance": 0.05, "krw_balance": 1_000_000.0}
        trader = _make_trader(tmp_path)
        # exchange=0.01 live + 0.01 locked = 0.02, DB=0.05 → 60% drift → halt
        with patch.object(trader, "_get_db_portfolio_snapshot", return_value=db_snap), \
             patch.object(trader, "_get_open_orders_locked", return_value=0.01):
            result = trader._check_portfolio_drift(LIVE_PORTFOLIO_BTC, drift_threshold=0.05)
        assert result["halt"] is True


# ---------------------------------------------------------------------------
# Test 3: DB 스냅샷 없으면 검사 생략
# ---------------------------------------------------------------------------

class TestR2NoDbSnapshot:
    def test_no_snapshot_skips_check(self, tmp_path):
        trader = _make_trader(tmp_path)
        with patch.object(trader, "_get_db_portfolio_snapshot", return_value=None):
            result = trader._check_portfolio_drift(LIVE_PORTFOLIO_BTC)
        assert result["halt"] is False
        assert result.get("skipped") is True


# ---------------------------------------------------------------------------
# Test 4: 잔고 일치 → halt 없음
# ---------------------------------------------------------------------------

class TestR2NoDrift:
    def test_matching_balances_no_halt(self, tmp_path):
        trader = _make_trader(tmp_path)
        with patch.object(trader, "_get_db_portfolio_snapshot", return_value=DB_SNAP_MATCH), \
             patch.object(trader, "_get_open_orders_locked", return_value=0.0):
            result = trader._check_portfolio_drift(LIVE_PORTFOLIO_BTC, drift_threshold=0.05)
        assert result["halt"] is False


# ---------------------------------------------------------------------------
# Test 5: _clamp_to_balance 실잔량 초과 방지
# ---------------------------------------------------------------------------

class TestR2ClampToBalance:
    def test_clamp_excess_volume(self, tmp_path):
        trader = _make_trader(tmp_path)
        portfolio = {
            "krw_balance": 0,
            "holdings": [{"currency": "BTC", "balance": 0.005}],
        }
        with patch.object(trader, "_run_script", return_value=portfolio), \
             patch.object(trader, "_get_open_orders_locked", return_value=0.0):
            clamped = trader._clamp_to_balance(0.01, "KRW-BTC")
        assert clamped == pytest.approx(0.005)

    def test_clamp_with_locked_reduces_usable(self, tmp_path):
        """locked 0.003 → usable=0.002, ask 0.008 → clamp to 0.002."""
        trader = _make_trader(tmp_path)
        portfolio = {
            "krw_balance": 0,
            "holdings": [{"currency": "BTC", "balance": 0.005}],
        }
        with patch.object(trader, "_run_script", return_value=portfolio), \
             patch.object(trader, "_get_open_orders_locked", return_value=0.003):
            clamped = trader._clamp_to_balance(0.008, "KRW-BTC")
        assert clamped == pytest.approx(0.002)

    def test_no_clamp_when_within_balance(self, tmp_path):
        trader = _make_trader(tmp_path)
        portfolio = {
            "krw_balance": 0,
            "holdings": [{"currency": "BTC", "balance": 0.05}],
        }
        with patch.object(trader, "_run_script", return_value=portfolio), \
             patch.object(trader, "_get_open_orders_locked", return_value=0.0):
            clamped = trader._clamp_to_balance(0.01, "KRW-BTC")
        assert clamped == pytest.approx(0.01)


# ---------------------------------------------------------------------------
# Test SO-6c: DB 조회 에러 → halt (skip 아님)
# ---------------------------------------------------------------------------

class TestR2DbQueryError:
    def test_db_error_triggers_halt(self, tmp_path):
        """DB 조회 에러 시 halt=True (빈 테이블 skip과 구분)."""
        trader = _make_trader(tmp_path)

        def _notify_noop(msg):
            pass
        trader._notify_telegram_sync = _notify_noop

        with patch.object(trader, "_get_db_portfolio_snapshot",
                          return_value=LiveTrader._DB_QUERY_ERROR):
            result = trader._check_portfolio_drift(LIVE_PORTFOLIO_BTC)

        assert result["halt"] is True
        assert result.get("reason") == "db_query_error"
        assert result.get("skipped") is False

    def test_empty_table_skips(self, tmp_path):
        """빈 테이블(None 반환) → halt=False + skipped=True."""
        trader = _make_trader(tmp_path)
        with patch.object(trader, "_get_db_portfolio_snapshot", return_value=None):
            result = trader._check_portfolio_drift(LIVE_PORTFOLIO_BTC)

        assert result["halt"] is False
        assert result.get("skipped") is True

    def test_get_db_snapshot_error_returns_sentinel(self, tmp_path, monkeypatch):
        """_get_db_portfolio_snapshot: 요청 예외 시 _DB_QUERY_ERROR sentinel 반환."""
        trader = _make_trader(tmp_path)
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "fake_key")

        import requests as _req
        with patch("rl_hybrid.rl.live_trader._req.get" if False else "requests.get",
                   side_effect=ConnectionError("DB 연결 실패")):
            result = trader._get_db_portfolio_snapshot()

        assert result is LiveTrader._DB_QUERY_ERROR
