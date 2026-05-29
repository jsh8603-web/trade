"""tests/test_phase_R_so5.py — SO-5/PR 집행 상태머신 coin 변형 검증.

검증 기준 (harness2.md SO-5/PR):
(a) ShadowOrder.is_dry_run 항상 True (실주문 0건)
(b) place_shadow → OrderState INITIALIZED→SUBMITTED 전이
(c) simulate_fill 부분체결→PARTIALLY_FILLED / 전체→FILLED
(d) cancel_shadow → CANCELED
(e) lookup_by_identifier H9 멱등 재조회
(f) reconcile/pending_orders 미체결 필터
(g) UpbitRateLimiter 10req/s 간격
(h) validate_transition 거부 전이 reject
(i) SACRED: execute_trade.py / live_trader.py diff=0 (coin 실거래 경로 미변경)
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.coin_shadow import (
    CoinShadowExecutor,
    ShadowOrder,
    UpbitRateLimiter,
)
from backtest.engine import OrderState, validate_transition


# ---------------------------------------------------------------------------
# (a) ShadowOrder.is_dry_run 항상 True
# ---------------------------------------------------------------------------

def test_shadow_order_is_dry_run_always_true():
    """ShadowOrder.is_dry_run = True (실주문 0건 보장)."""
    order = ShadowOrder(ticker="BTC/KRW", side="buy", qty=0.001, price=50_000_000)
    assert order.is_dry_run is True


def test_place_shadow_is_dry_run():
    """place_shadow 생성 주문 is_dry_run = True."""
    executor = CoinShadowExecutor()
    order = executor.place_shadow("BTC/KRW", "buy", 0.001, 50_000_000)
    assert order.is_dry_run is True


# ---------------------------------------------------------------------------
# (b) place_shadow → INITIALIZED → SUBMITTED
# ---------------------------------------------------------------------------

def test_shadow_order_initial_state_initialized():
    """ShadowOrder 초기 상태 = INITIALIZED."""
    order = ShadowOrder()
    assert order.state == OrderState.INITIALIZED


def test_place_shadow_transitions_to_submitted():
    """place_shadow → 최종 상태 SUBMITTED."""
    executor = CoinShadowExecutor()
    order = executor.place_shadow("BTC/KRW", "buy", 0.001, 50_000_000)
    assert order.state == OrderState.SUBMITTED


def test_place_shadow_registers_in_orders():
    """place_shadow → executor 내부 _orders 등록."""
    executor = CoinShadowExecutor()
    order = executor.place_shadow("ETH/KRW", "sell", 0.1, 3_000_000)
    assert executor.lookup_by_identifier(order.identifier) is order


# ---------------------------------------------------------------------------
# (c) simulate_fill — 부분체결/전체체결
# ---------------------------------------------------------------------------

def test_simulate_fill_partial_fill():
    """부분체결(fill_qty < qty) → PARTIALLY_FILLED."""
    executor = CoinShadowExecutor()
    order = executor.place_shadow("BTC/KRW", "buy", 1.0, 50_000_000)
    filled = executor.simulate_fill(order.identifier, fill_qty=0.5)
    assert filled is not None
    assert filled.state == OrderState.PARTIALLY_FILLED
    assert filled.filled_qty == 0.5


def test_simulate_fill_full_fill():
    """전체체결(fill_qty=None → qty 전량) → FILLED."""
    executor = CoinShadowExecutor()
    order = executor.place_shadow("BTC/KRW", "buy", 1.0, 50_000_000)
    filled = executor.simulate_fill(order.identifier, fill_qty=None)
    assert filled is not None
    assert filled.state == OrderState.FILLED
    assert filled.filled_qty == order.qty


def test_simulate_fill_unknown_identifier():
    """존재하지 않는 identifier → None."""
    executor = CoinShadowExecutor()
    result = executor.simulate_fill("nonexistent-id")
    assert result is None


# ---------------------------------------------------------------------------
# (d) cancel_shadow → CANCELED
# ---------------------------------------------------------------------------

def test_cancel_shadow_submitted_order():
    """SUBMITTED 주문 취소 → CANCELED."""
    executor = CoinShadowExecutor()
    order = executor.place_shadow("BTC/KRW", "buy", 0.001, 50_000_000)
    ok = executor.cancel_shadow(order.identifier)
    assert ok is True
    assert order.state == OrderState.CANCELED


def test_cancel_shadow_filled_order_fails():
    """FILLED 주문 취소 → 거부 (False)."""
    executor = CoinShadowExecutor()
    order = executor.place_shadow("BTC/KRW", "buy", 0.001, 50_000_000)
    executor.simulate_fill(order.identifier)
    ok = executor.cancel_shadow(order.identifier)
    assert ok is False
    assert order.state == OrderState.FILLED


def test_cancel_shadow_unknown_identifier():
    """존재하지 않는 identifier → False."""
    executor = CoinShadowExecutor()
    assert executor.cancel_shadow("bad-id") is False


# ---------------------------------------------------------------------------
# (e) lookup_by_identifier — H9 멱등 재조회
# ---------------------------------------------------------------------------

def test_lookup_by_identifier_found():
    """identifier로 주문 재조회 (H9 멱등성)."""
    executor = CoinShadowExecutor()
    order = executor.place_shadow("BTC/KRW", "buy", 0.001, 50_000_000)
    found = executor.lookup_by_identifier(order.identifier)
    assert found is order


def test_lookup_by_identifier_idempotent():
    """동일 identifier 반복 조회 → 동일 객체 반환 (멱등)."""
    executor = CoinShadowExecutor()
    order = executor.place_shadow("BTC/KRW", "buy", 0.001, 50_000_000)
    r1 = executor.lookup_by_identifier(order.identifier)
    r2 = executor.lookup_by_identifier(order.identifier)
    assert r1 is r2


def test_lookup_by_identifier_not_found():
    """없는 identifier → None."""
    executor = CoinShadowExecutor()
    assert executor.lookup_by_identifier("bad") is None


# ---------------------------------------------------------------------------
# (f) reconcile / pending_orders 미체결 필터
# ---------------------------------------------------------------------------

def test_reconcile_returns_pending_for_ticker():
    """reconcile → 해당 티커의 미체결 주문만 반환."""
    executor = CoinShadowExecutor()
    o1 = executor.place_shadow("BTC/KRW", "buy", 0.001, 50_000_000)
    o2 = executor.place_shadow("ETH/KRW", "buy", 0.01, 3_000_000)
    o3 = executor.place_shadow("BTC/KRW", "sell", 0.001, 51_000_000)

    # o3 체결 완료
    executor.simulate_fill(o3.identifier)

    pending_btc = executor.reconcile("BTC/KRW")
    assert o1 in pending_btc
    assert o2 not in pending_btc      # ETH 아님
    assert o3 not in pending_btc      # FILLED


def test_pending_orders_excludes_filled():
    """pending_orders → FILLED/CANCELED 제외."""
    executor = CoinShadowExecutor()
    o1 = executor.place_shadow("BTC/KRW", "buy", 0.001, 50_000_000)
    o2 = executor.place_shadow("BTC/KRW", "buy", 0.002, 50_000_000)
    executor.simulate_fill(o2.identifier)  # o2 체결

    pending = executor.pending_orders()
    assert o1 in pending
    assert o2 not in pending


def test_pending_orders_empty_after_all_filled():
    """전부 체결 → pending_orders 비어 있음."""
    executor = CoinShadowExecutor()
    o = executor.place_shadow("BTC/KRW", "buy", 0.001, 50_000_000)
    executor.simulate_fill(o.identifier)
    assert len(executor.pending_orders()) == 0


# ---------------------------------------------------------------------------
# (g) UpbitRateLimiter 10req/s 간격
# ---------------------------------------------------------------------------

def test_rate_limiter_interval_respected():
    """2회 연속 acquire — 간격 ≥ min_interval."""
    limiter = UpbitRateLimiter(rate_per_sec=5.0)  # 0.2s 간격
    t0 = time.monotonic()
    limiter.acquire()
    t1 = time.monotonic()
    limiter.acquire()
    t2 = time.monotonic()
    elapsed = t2 - t1
    assert elapsed >= 0.18, f"레이트리밋 미준수: {elapsed:.4f}s"


def test_rate_limiter_first_call_no_wait():
    """첫 번째 acquire → 즉시 반환."""
    limiter = UpbitRateLimiter(rate_per_sec=100.0)
    t0 = time.monotonic()
    limiter.acquire()
    assert time.monotonic() - t0 < 0.1


# ---------------------------------------------------------------------------
# (h) validate_transition 거부 전이
# ---------------------------------------------------------------------------

def test_validate_transition_invalid_rejected():
    """FILLED → SUBMITTED 불가 전이 → False."""
    assert validate_transition(OrderState.FILLED, OrderState.SUBMITTED) is False


def test_validate_transition_valid_accepted():
    """INITIALIZED → SUBMITTED 가능 전이 → True."""
    assert validate_transition(OrderState.INITIALIZED, OrderState.SUBMITTED) is True


def test_shadow_order_transition_invalid_returns_false():
    """ShadowOrder.transition 불가 전이 → False + 상태 미변경."""
    order = ShadowOrder()
    order.state = OrderState.FILLED
    ok = order.transition(OrderState.SUBMITTED)
    assert ok is False
    assert order.state == OrderState.FILLED


# ---------------------------------------------------------------------------
# (i) SACRED: execute_trade.py / live_trader.py diff=0
# ---------------------------------------------------------------------------

def test_sacred_execute_trade_no_diff():
    """execute_trade.py 실거래 경로 미변경 — git diff HEAD 빈 출력."""
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD", "--",
         "scripts/execute_trade.py"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.stdout.strip() == "", (
        f"execute_trade.py 변경 감지:\n{result.stdout}"
    )


def test_sacred_live_trader_no_diff():
    """live_trader.py 실거래 경로 미변경 — git diff HEAD 빈 출력."""
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD", "--",
         "rl_hybrid/rl/live_trader.py"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.stdout.strip() == "", (
        f"live_trader.py 변경 감지:\n{result.stdout}"
    )


def test_sacred_coin_shadow_no_execute_trade_import():
    """coin_shadow.py는 execute_trade를 import하지 않음."""
    import ast
    shadow_path = PROJECT_ROOT / "core" / "coin_shadow.py"
    tree = ast.parse(shadow_path.read_text(encoding="utf-8"))
    imports = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    for imp in imports:
        if isinstance(imp, ast.ImportFrom):
            module = imp.module or ""
            assert "execute_trade" not in module, (
                f"execute_trade import 금지: {module}"
            )
        elif isinstance(imp, ast.Import):
            for alias in imp.names:
                assert "execute_trade" not in alias.name
