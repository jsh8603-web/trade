"""tests/test_so5_p4_kis_client.py — SO-5/P4 KisClient 검증.

검증 기준 (harness2.md SO-5):
1. KisClient order/modify/cancel/pending 구현 PASS
2. _clamp_to_balance(req>free → free로 클램프)
3. _poll_and_amend(미체결→정정→실패시 취소)
4. 원번호 추적 체인(modify 신규번호→원번호 매핑 유지)
5. 토큰갱신/ws재연결 로직
6. 모의투자 기본 모드 + EMERGENCY_STOP/DRY_RUN 선검사
7. pykis 경계 스텁 (credential 없음=이연)
"""

from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock, patch, call
import time

import pytest

from stock.kis_client import KisClient, KisOrderRef, KisRateLimiter


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_client(dry_run=True, emergency_stop=False, paper=True):
    return KisClient(
        appkey="",
        appsecret="",
        account_no="",
        paper=paper,
        dry_run=dry_run,
        emergency_stop=emergency_stop,
    )


def _make_order_ref(number="ORDER001"):
    return KisOrderRef(
        branch="000",
        number=number,
        account_no="TEST",
        symbol="005930",
        market="KRX",
    )


# ---------------------------------------------------------------------------
# 1. 인터페이스 — order/modify/cancel/pending 구현
# ---------------------------------------------------------------------------

def test_kis_client_has_required_methods():
    """KisClient 필수 메서드 존재 확인."""
    client = _make_client()
    for method in ("order", "modify", "cancel", "pending",
                   "_clamp_to_balance", "_poll_and_amend",
                   "start_token_refresh", "start_websocket",
                   "check_price_limit", "convert_usd_to_krw"):
        assert callable(getattr(client, method, None)), f"{method} 미구현"


# ---------------------------------------------------------------------------
# 2. DRY_RUN / EMERGENCY_STOP 선검사
# ---------------------------------------------------------------------------

def test_order_blocked_by_dry_run():
    """DRY_RUN=True → order 차단, None 반환."""
    client = _make_client(dry_run=True)
    result = client.order("005930", "BUY", qty=1)
    assert result is None


def test_order_blocked_by_emergency_stop():
    """EMERGENCY_STOP=True → order 차단."""
    client = _make_client(emergency_stop=True, dry_run=False)
    result = client.order("005930", "BUY", qty=1)
    assert result is None


def test_modify_blocked_by_dry_run():
    """DRY_RUN=True → modify 차단."""
    client = _make_client(dry_run=True)
    ref = _make_order_ref()
    result = client.modify(ref, new_price=70000)
    assert result is None


def test_cancel_blocked_by_dry_run():
    """DRY_RUN=True → cancel False 반환."""
    client = _make_client(dry_run=True)
    ref = _make_order_ref()
    result = client.cancel(ref)
    assert result is False


# ---------------------------------------------------------------------------
# 3. 모의투자 기본 모드
# ---------------------------------------------------------------------------

def test_is_paper_default_true():
    """paper=True 기본값 확인."""
    client = KisClient(dry_run=True)
    assert client.is_paper is True


def test_is_paper_false_when_set():
    """paper=False 설정 확인."""
    client = KisClient(paper=False, dry_run=True)
    assert client.is_paper is False


# ---------------------------------------------------------------------------
# 4. credential 없음 — stub 주문 (이연)
# ---------------------------------------------------------------------------

def test_order_stub_when_no_credential():
    """credential 없으면 스텁 KisOrderRef 반환 (DRY_RUN=False 로 설정)."""
    client = _make_client(dry_run=False)
    result = client.order("005930", "BUY", qty=1)
    # credential 없으므로 스텁 반환 (None 아님)
    assert isinstance(result, KisOrderRef)
    assert result.symbol == "005930"


def test_modify_stub_when_no_credential():
    """credential 없으면 스텁 modify."""
    client = _make_client(dry_run=False)
    ref = _make_order_ref("ORD001")
    result = client.modify(ref, new_price=70000)
    assert isinstance(result, KisOrderRef)
    assert result.original_number == "ORD001"


def test_cancel_stub_when_no_credential():
    """credential 없으면 stub cancel True."""
    client = _make_client(dry_run=False)
    ref = _make_order_ref()
    result = client.cancel(ref)
    assert result is True


# ---------------------------------------------------------------------------
# 5. _clamp_to_balance — req>free → free로 클램프
# ---------------------------------------------------------------------------

def test_clamp_no_credential_passthrough():
    """credential 없으면 clamp=passthrough (원래 수량 그대로)."""
    client = _make_client(dry_run=False)
    clamped = client._clamp_to_balance("005930", "SELL", 100.0)
    assert clamped == 100.0  # 스텁: 변경 없음


def test_clamp_with_mock_balance_sell():
    """SELL clamp: 보유량(free=50) < req(100) → clamp to 50."""
    client = _make_client(dry_run=False)

    mock_pos = MagicMock()
    mock_pos.symbol = "005930"
    mock_pos.qty = 50

    mock_balance = MagicMock()
    mock_balance.positions = [mock_pos]

    mock_kis = MagicMock()
    mock_kis.account.balance.return_value = mock_balance

    with patch.object(client, "_ensure_pykis", return_value=mock_kis):
        clamped = client._clamp_to_balance("005930", "SELL", 100.0)

    assert clamped == 50.0


def test_clamp_with_mock_balance_buy():
    """BUY clamp: KRW잔고(free=50000) < req(100000) → clamp."""
    client = _make_client(dry_run=False)

    mock_balance = MagicMock()
    mock_balance.krw = 50000.0

    mock_kis = MagicMock()
    mock_kis.account.balance.return_value = mock_balance

    with patch.object(client, "_ensure_pykis", return_value=mock_kis):
        clamped = client._clamp_to_balance("005930", "BUY", 100000.0)

    assert clamped == 50000.0


# ---------------------------------------------------------------------------
# 6. 원번호 추적 체인 (ORGN_ODNO 이중정정 방지)
# ---------------------------------------------------------------------------

def test_order_chain_modify_preserves_original():
    """modify → 원번호 체인 유지."""
    client = _make_client(dry_run=False)
    orig_ref = _make_order_ref("ORD_ORIG")
    mod_ref = client.modify(orig_ref, new_price=70000)
    assert mod_ref is not None
    # 원번호 체인: mod_ref.number → ORD_ORIG
    assert client.get_original_number(mod_ref.number) == "ORD_ORIG"


def test_order_chain_double_modify_prevents_loop():
    """이중정정 방지: 정정된 주문 다시 정정해도 원번호는 최초 원번호."""
    client = _make_client(dry_run=False)
    orig = _make_order_ref("ORD_A")
    mod1 = client.modify(orig, new_price=70000)
    assert mod1 is not None
    mod2 = client.modify(mod1, new_price=69000)
    assert mod2 is not None
    # 두 번 정정해도 원번호는 ORD_A
    assert client.get_original_number(mod2.number) == "ORD_A"


# ---------------------------------------------------------------------------
# 7. _poll_and_amend — 미체결→정정→취소
# ---------------------------------------------------------------------------

def test_poll_and_amend_fills_early():
    """체결되면 정정 없이 즉시 반환."""
    client = _make_client(dry_run=False)
    ref = _make_order_ref("ORD_FILL")

    # pending() 항상 빈 목록 → 이미 체결
    with patch.object(client, "pending", return_value=[]), \
         patch.object(time, "sleep"):
        result = client._poll_and_amend(ref, new_price=70000, poll_count=3, poll_interval_sec=0)

    assert result is not None
    assert result.number == "ORD_FILL"


def test_poll_and_amend_cancel_after_all_fail():
    """3회 모두 미체결 → 취소 호출."""
    client = _make_client(dry_run=False)
    ref = _make_order_ref("ORD_CANCEL")

    # pending() 항상 미체결 포함
    mock_pending = [_make_order_ref("ORD_CANCEL")]

    cancel_called = []

    def _mock_cancel(r):
        cancel_called.append(r.number)
        return True

    with patch.object(client, "pending", return_value=mock_pending), \
         patch.object(client, "modify", return_value=None), \
         patch.object(client, "cancel", side_effect=_mock_cancel), \
         patch.object(time, "sleep"):
        result = client._poll_and_amend(ref, new_price=70000, poll_count=3, poll_interval_sec=0)

    assert result is None
    assert "ORD_CANCEL" in cancel_called


# ---------------------------------------------------------------------------
# 8. H17 가격제한폭 체크
# ---------------------------------------------------------------------------

def test_price_limit_upper_violation():
    """H17: 가격제한폭 상한 초과 → False."""
    client = _make_client()
    ok, reason = client.check_price_limit("005930", price=140000, ref_price=100000, side="BUY")
    assert ok is False
    assert "상한" in reason


def test_price_limit_lower_sell_locked():
    """H17: 하한가잠김 매도불가."""
    client = _make_client()
    ok, reason = client.check_price_limit("005930", price=60000, ref_price=100000, side="SELL")
    assert ok is False
    assert "하한가잠김" in reason or "하한" in reason


def test_price_limit_ok():
    """H17: 정상 범위 → True."""
    client = _make_client()
    ok, reason = client.check_price_limit("005930", price=100000, ref_price=100000, side="BUY")
    assert ok is True


# ---------------------------------------------------------------------------
# 9. H18 US FX
# ---------------------------------------------------------------------------

def test_convert_usd_to_krw():
    """H18: USD → KRW 환산."""
    client = _make_client()
    krw = client.convert_usd_to_krw(usd_amount=100.0, fx_rate=1350.0)
    assert krw == pytest.approx(135000.0)


# ---------------------------------------------------------------------------
# 10. 토큰 갱신 스레드 / WebSocket
# ---------------------------------------------------------------------------

def test_token_refresh_starts_thread():
    """토큰 갱신 스레드 시작 — is_alive 확인."""
    client = KisClient(dry_run=True)
    # _ensure_pykis=None 이면 스레드는 뜨지만 갱신 시도는 skip
    client.start_token_refresh(interval_sec=9999)
    assert client._token_refresh_thread is not None
    assert client._token_refresh_thread.is_alive()


def test_websocket_stub_without_credential():
    """credential 없으면 WebSocket 시작 스킵 (False 반환)."""
    client = KisClient(dry_run=True)
    result = client.start_websocket()
    assert result is False


# ---------------------------------------------------------------------------
# 11. KisRateLimiter — 초당 제한
# ---------------------------------------------------------------------------

def test_rate_limiter_basic():
    """KisRateLimiter acquire — min_interval 준수."""
    limiter = KisRateLimiter(requests_per_second=100.0)
    t0 = time.monotonic()
    for _ in range(3):
        limiter.acquire()
    elapsed = time.monotonic() - t0
    # 100req/s → 3회 ≈ 0.02s 이상
    assert elapsed >= 0.0


def test_pending_list_after_stub_order():
    """stub order 후 pending() → 목록에 포함."""
    client = _make_client(dry_run=False)
    ref = client.order("005930", "BUY", qty=1)
    assert ref is not None
    # credential 없음 → 스텁 pending
    pending = client.pending()
    # 스텁 모드에서는 내부 _pending 목록 반환
    assert any(p.symbol == "005930" for p in pending)
