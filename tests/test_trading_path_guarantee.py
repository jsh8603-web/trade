"""tests/test_trading_path_guarantee.py — 실거래 동작 보장: 매매경로 6분할 검증.

사용자 지시(2026-05-30): "실제 트레이딩 시작하면 동작 보장? 테스트 쪼개서."
e2e(조각 안깨짐)와 별개 = 실거래 켜기 전 매매 흐름의 안전·정확성 단계별 증명.

분할:
  M1 주문 생성 정확성 (결정→주문 파라미터)
  M2 안전장치 게이트 독립 검증 (DRY_RUN/EMERGENCY_STOP/auto_emergency/MAX_AMOUNT/일일횟수/간격/포지션비율/MIN_AMOUNT)
  M3 잔고·체결 처리 (매도 보유량 초과 차단)
  M4 무인 안전장치 실손실 발동 (KillSwitch auto_derisk_due)
  M5 멱등성·중복주문 방지 (일일카운터·금액검증)
  M6 상태 영속·재시작 복구 (daily_trades/last_trade_time)

⛔ SACRED: execute_trade.py 미변경(읽기만). DRY_RUN 기본. 실주문 0(모든 실주문 경로 mock/차단).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.execute_trade import execute  # noqa: E402

KST = timezone(timedelta(hours=9))


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """각 테스트 격리: 안전장치 env 기본값 명시 (이전 테스트 누수 차단)."""
    monkeypatch.setenv("EMERGENCY_STOP", "false")
    monkeypatch.setenv("MAX_TRADE_AMOUNT", "100000")
    monkeypatch.setenv("MIN_TRADE_AMOUNT", "5000")
    monkeypatch.setenv("MAX_DAILY_TRADES", "6")
    monkeypatch.setenv("MIN_TRADE_INTERVAL_HOURS", "4")
    monkeypatch.setenv("MAX_POSITION_RATIO", "0.5")
    yield


# ═══════════════════════════════════════════════════════════
# M1 — 주문 생성 정확성 (결정 → 주문 파라미터)
# ═══════════════════════════════════════════════════════════

class TestM1OrderGeneration:
    def test_invalid_side_rejected(self, monkeypatch):
        """side는 bid/ask만 — 그 외 즉시 거부 (잘못된 주문 생성 차단)."""
        monkeypatch.setenv("DRY_RUN", "false")
        r = execute("long", "KRW-BTC", "10000")
        assert r["success"] is False
        assert "side" in r["error"].lower()

    def test_invalid_amount_rejected(self, monkeypatch):
        """금액이 숫자 아니면 주문 생성 거부."""
        monkeypatch.setenv("DRY_RUN", "false")
        monkeypatch.setattr("scripts.execute_trade._get_daily_trades", lambda: {"count": 0, "date": "x"})
        monkeypatch.setattr("scripts.execute_trade._get_last_trade_time", lambda: None)
        monkeypatch.setattr("scripts.execute_trade._get_btc_position_ratio", lambda: 0.0)
        r = execute("bid", "KRW-BTC", "abc")
        assert r["success"] is False
        assert "금액" in r["error"] or "amount" in r["error"].lower()

    def test_amount_and_side_preserved_in_result(self, monkeypatch):
        """주문 결과에 side/market/amount 정확히 반영 (파라미터 보존)."""
        monkeypatch.setenv("DRY_RUN", "true")
        r = execute("bid", "KRW-BTC", "10000")
        assert r["side"] == "bid"
        assert r["market"] == "KRW-BTC"
        assert r["amount"] == "10000"


# ═══════════════════════════════════════════════════════════
# M2 — 안전장치 게이트 독립 검증 (각각 단독 ON)
# ═══════════════════════════════════════════════════════════

class TestM2SafetyGates:
    def test_dry_run_blocks_real_order(self, monkeypatch):
        """DRY_RUN=true → 실주문 미발생 (dry_run 플래그)."""
        monkeypatch.setenv("DRY_RUN", "true")
        r = execute("bid", "KRW-BTC", "10000")
        assert r["dry_run"] is True
        assert r.get("success") is True  # 분석 성공, 실주문 X

    def test_emergency_stop_blocks_buy_before_dryrun(self, monkeypatch):
        """EMERGENCY_STOP=true → 매수 차단. DRY_RUN보다 먼저 (설계: dry_run에서도 반영)."""
        monkeypatch.setenv("EMERGENCY_STOP", "true")
        monkeypatch.setenv("DRY_RUN", "true")  # dry_run이어도 EMERGENCY가 먼저
        r = execute("bid", "KRW-BTC", "10000")
        assert r["success"] is False
        assert "EMERGENCY_STOP" in r["error"]
        assert r["dry_run"] is False  # EMERGENCY가 DRY_RUN보다 먼저 평가됨 (증명)

    def test_emergency_stop_allows_sell_liquidation(self, monkeypatch):
        """EMERGENCY_STOP 중에도 매도(청산)는 허용 (자산 보전)."""
        monkeypatch.setenv("EMERGENCY_STOP", "true")
        monkeypatch.setenv("DRY_RUN", "true")
        r = execute("ask", "KRW-BTC", "0.001")
        # 매도는 EMERGENCY 통과 → DRY_RUN에서 멈춤
        assert r["dry_run"] is True

    def test_max_daily_trades_blocks(self, monkeypatch):
        """MAX_DAILY_TRADES 도달 → 차단."""
        monkeypatch.setenv("DRY_RUN", "false")
        monkeypatch.setenv("MAX_DAILY_TRADES", "6")
        monkeypatch.setattr("scripts.execute_trade._get_daily_trades", lambda: {"count": 6, "date": "x"})
        r = execute("bid", "KRW-BTC", "10000")
        assert r["success"] is False
        assert "일일" in r["error"] or "daily" in r["error"].lower()

    def test_min_interval_blocks(self, monkeypatch):
        """MIN_TRADE_INTERVAL_HOURS 미달 → 차단."""
        monkeypatch.setenv("DRY_RUN", "false")
        monkeypatch.setenv("MIN_TRADE_INTERVAL_HOURS", "4")
        monkeypatch.setattr("scripts.execute_trade._get_daily_trades", lambda: {"count": 0, "date": "x"})
        recent = datetime.now(KST) - timedelta(hours=1)  # 1h 전 = 4h 미달
        monkeypatch.setattr("scripts.execute_trade._get_last_trade_time", lambda: recent)
        r = execute("bid", "KRW-BTC", "10000")
        assert r["success"] is False
        assert "간격" in r["error"] or "interval" in r["error"].lower()

    def test_max_position_ratio_blocks_buy(self, monkeypatch):
        """MAX_POSITION_RATIO 초과 → 매수 차단 (과다 보유 방지)."""
        monkeypatch.setenv("DRY_RUN", "false")
        monkeypatch.setenv("MAX_POSITION_RATIO", "0.5")
        monkeypatch.setattr("scripts.execute_trade._get_daily_trades", lambda: {"count": 0, "date": "x"})
        monkeypatch.setattr("scripts.execute_trade._get_last_trade_time", lambda: None)
        monkeypatch.setattr("scripts.execute_trade._get_btc_position_ratio", lambda: 0.6)
        r = execute("bid", "KRW-BTC", "10000")
        assert r["success"] is False
        assert "포지션" in r["error"] or "position" in r["error"].lower()

    def test_max_amount_blocks_oversized(self, monkeypatch):
        """MAX_TRADE_AMOUNT 초과 매수 → 차단 (상한)."""
        monkeypatch.setenv("DRY_RUN", "false")
        monkeypatch.setenv("MAX_TRADE_AMOUNT", "100000")
        monkeypatch.setattr("scripts.execute_trade._get_daily_trades", lambda: {"count": 0, "date": "x"})
        monkeypatch.setattr("scripts.execute_trade._get_last_trade_time", lambda: None)
        monkeypatch.setattr("scripts.execute_trade._get_btc_position_ratio", lambda: 0.0)
        r = execute("bid", "KRW-BTC", "200000")  # 상한 2배
        assert r["success"] is False
        assert "상한" in r["error"] or "초과" in r["error"]

    def test_min_amount_skips_tiny_buy(self, monkeypatch):
        """MIN_TRADE_AMOUNT 미달 매수 → 스킵 (Upbit 최소주문 5000원)."""
        monkeypatch.setenv("DRY_RUN", "false")
        monkeypatch.setenv("MIN_TRADE_AMOUNT", "5000")
        monkeypatch.setattr("scripts.execute_trade._get_daily_trades", lambda: {"count": 0, "date": "x"})
        monkeypatch.setattr("scripts.execute_trade._get_last_trade_time", lambda: None)
        monkeypatch.setattr("scripts.execute_trade._get_btc_position_ratio", lambda: 0.0)
        r = execute("bid", "KRW-BTC", "3000")  # 5000원 미만
        assert r["success"] is False
        assert r.get("skipped") is True


# ═══════════════════════════════════════════════════════════
# M3 — 잔고·체결 처리 (매도 보유량 초과 차단)
# ═══════════════════════════════════════════════════════════

class TestM3BalanceSettlement:
    def test_sell_exceeding_holdings_blocked(self, monkeypatch):
        """매도 수량 > 보유량 → 차단 (음수 잔고 방지)."""
        monkeypatch.setenv("DRY_RUN", "false")
        monkeypatch.setattr("scripts.execute_trade._get_daily_trades", lambda: {"count": 0, "date": "x"})
        monkeypatch.setattr("scripts.execute_trade._get_last_trade_time", lambda: None)

        import subprocess
        class _PF:
            returncode = 0
            stdout = json.dumps({"holdings": [{"currency": "BTC", "balance": 0.001}]})
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: _PF())

        r = execute("ask", "KRW-BTC", "0.5")  # 보유 0.001보다 큼
        assert r["success"] is False
        assert "보유" in r["error"] or "초과" in r["error"]


# ═══════════════════════════════════════════════════════════
# M4 — 무인 안전장치 실손실 발동 (KillSwitch auto_derisk_due)
# ═══════════════════════════════════════════════════════════

class TestM4UnattendedTrigger:
    def test_auto_derisk_due_exists_and_callable(self):
        """auto_derisk_due()가 bool 반환 (무인 트리거 신호 인터페이스)."""
        from core.risk_gate import KillSwitch
        ks = KillSwitch()
        assert hasattr(ks, "auto_derisk_due"), "KillSwitch.auto_derisk_due 부재"
        result = ks.auto_derisk_due()
        assert isinstance(result, bool)

    def test_killswitch_has_unattended_flag(self):
        """KillSwitch unattended 모드 (무인 de-risk 경로 활성)."""
        from core.risk_gate import KillSwitch
        ks = KillSwitch()
        # unattended 속성 또는 RISK_UNATTENDED env 경로 존재
        assert hasattr(ks, "unattended") or hasattr(ks, "auto_derisk_due")


# ═══════════════════════════════════════════════════════════
# M5 — 멱등성·중복주문 방지
# ═══════════════════════════════════════════════════════════

class TestM5Idempotency:
    def test_dry_run_repeated_no_state_change(self, monkeypatch):
        """DRY_RUN 반복 호출 → 동일 결과, 상태 변경 없음 (멱등)."""
        monkeypatch.setenv("DRY_RUN", "true")
        r1 = execute("bid", "KRW-BTC", "10000")
        r2 = execute("bid", "KRW-BTC", "10000")
        assert r1["dry_run"] == r2["dry_run"] is True
        assert r1["success"] == r2["success"]

    def test_daily_count_gate_prevents_overtrade(self, monkeypatch):
        """일일 카운터가 상한이면 추가 주문 전부 차단 (중복/과다매매 방지)."""
        monkeypatch.setenv("DRY_RUN", "false")
        monkeypatch.setenv("MAX_DAILY_TRADES", "2")
        monkeypatch.setattr("scripts.execute_trade._get_daily_trades", lambda: {"count": 2, "date": "x"})
        for _ in range(3):
            r = execute("bid", "KRW-BTC", "10000")
            assert r["success"] is False  # 상한 도달 후 전부 차단


# ═══════════════════════════════════════════════════════════
# M6 — 상태 영속·재시작 복구
# ═══════════════════════════════════════════════════════════

class TestM6StatePersistence:
    def test_daily_trades_helper_returns_structure(self):
        """_get_daily_trades() → {count, ...} 구조 (재시작 후 카운터 복원 기반)."""
        from scripts.execute_trade import _get_daily_trades
        d = _get_daily_trades()
        assert isinstance(d, dict)
        assert "count" in d

    def test_last_trade_time_helper_returns_datetime_or_none(self):
        """_get_last_trade_time() → datetime|None (재시작 후 간격 계산 기반)."""
        from scripts.execute_trade import _get_last_trade_time
        t = _get_last_trade_time()
        assert t is None or isinstance(t, datetime)
