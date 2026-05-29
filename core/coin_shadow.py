"""core/coin_shadow.py — 집행 상태머신 coin 변형 (SO-5/Phase R).

변형표 #4:
- Upbit identifier 매핑 (H9 멱등성)
- shadow-live (H19): 실주문 시뮬 — DRY_RUN=True 경로에서 OrderState FSM 추적
- Upbit nonce/레이트리밋 wire
- OrderState FSM(Phase5/-1) coin Upbit 경로 어댑터

⛔ SACRED 최우선:
  execute_trade.py 실주문(:457)·nonce uuid(:153)·live_trader.run_cycle 절대 미변경.
  shadow-live/DRY_RUN 경로만. diff=0 on execute_trade.py.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backtest.engine import OrderState, validate_transition

logger = logging.getLogger("core.coin_shadow")

# Upbit 레이트리밋 (초당 10req)
_UPBIT_RATE_LIMIT_PER_SEC = 10.0
_MIN_INTERVAL_SEC = 1.0 / _UPBIT_RATE_LIMIT_PER_SEC


# ---------------------------------------------------------------------------
# shadow-live 주문 추적 (H19 — 실주문 없이 FSM만 추적)
# ---------------------------------------------------------------------------

@dataclass
class ShadowOrder:
    """shadow-live 주문 레코드. 실주문 없이 OrderState FSM만 추적."""
    identifier: str = field(default_factory=lambda: str(uuid.uuid4()))
    ticker: str = ""
    side: str = "buy"
    qty: float = 0.0
    price: float = 0.0
    state: OrderState = OrderState.INITIALIZED
    is_dry_run: bool = True          # 항상 True (실주문 0건)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    filled_qty: float = 0.0

    def transition(self, to_state: OrderState) -> bool:
        """FSM 전이 검증 후 상태 변경."""
        if validate_transition(self.state, to_state):
            self.state = to_state
            return True
        logger.warning("OrderState 전이 거부: %s → %s", self.state, to_state)
        return False


# ---------------------------------------------------------------------------
# UpbitRateLimiter — E1 레이트리밋
# ---------------------------------------------------------------------------

class UpbitRateLimiter:
    """Upbit 레이트리밋 — 초당 10req."""

    def __init__(self, rate_per_sec: float = _UPBIT_RATE_LIMIT_PER_SEC):
        self._min_interval = 1.0 / rate_per_sec
        self._last_call = 0.0

    def acquire(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.monotonic()


# ---------------------------------------------------------------------------
# CoinShadowExecutor — shadow-live + identifier + nonce + FSM
# ---------------------------------------------------------------------------

class CoinShadowExecutor:
    """집행 상태머신 coin 변형 어댑터.

    shadow-live(H19): DRY_RUN=True 경로에서 OrderState FSM 추적.
    Upbit identifier 매핑 (H9 멱등성 — 응답유실 후 재조회).
    nonce: 실행마다 uuid.uuid4() — execute_trade.py:153 패턴 유지.

    SACRED: execute_trade.py 실주문/nonce 미변경.
             이 클래스=shadow 경로만, 실 order 발송 없음.
    """

    def __init__(self, rate_limiter: Optional[UpbitRateLimiter] = None):
        self._rate_limiter = rate_limiter or UpbitRateLimiter()
        self._orders: Dict[str, ShadowOrder] = {}   # identifier → ShadowOrder

    def place_shadow(
        self,
        ticker: str,
        side: str,
        qty: float,
        price: float,
    ) -> ShadowOrder:
        """shadow-live 주문 생성 (실주문 0건).

        identifier = uuid4 (H9 멱등성).
        OrderState: INITIALIZED → SUBMITTED.
        """
        self._rate_limiter.acquire()

        order = ShadowOrder(
            identifier=str(uuid.uuid4()),  # execute_trade.py:153 패턴
            ticker=ticker,
            side=side,
            qty=qty,
            price=price,
            is_dry_run=True,
        )
        order.transition(OrderState.SUBMITTED)
        self._orders[order.identifier] = order
        logger.info("[shadow] 주문 생성: %s %s %s@%s (id=%s)",
                    side, ticker, qty, price, order.identifier[:8])
        return order

    def simulate_fill(
        self,
        identifier: str,
        fill_qty: Optional[float] = None,
    ) -> Optional[ShadowOrder]:
        """shadow-live 체결 시뮬. 부분체결 → PARTIALLY_FILLED, 전체 → FILLED."""
        order = self._orders.get(identifier)
        if order is None:
            return None

        if order.state == OrderState.SUBMITTED:
            order.transition(OrderState.ACCEPTED)

        if fill_qty is not None and fill_qty < order.qty:
            order.filled_qty += fill_qty
            order.transition(OrderState.PARTIALLY_FILLED)
        else:
            order.filled_qty = order.qty
            order.transition(OrderState.FILLED)

        return order

    def cancel_shadow(self, identifier: str) -> bool:
        """shadow 주문 취소."""
        order = self._orders.get(identifier)
        if order is None:
            return False
        return order.transition(OrderState.CANCELED)

    def lookup_by_identifier(self, identifier: str) -> Optional[ShadowOrder]:
        """H9: identifier로 주문 재조회 (응답유실 대응)."""
        return self._orders.get(identifier)

    def reconcile(self, ticker: str) -> List[ShadowOrder]:
        """R2 reconciliation: 티커의 미체결 shadow 주문 목록."""
        pending = [
            o for o in self._orders.values()
            if o.ticker == ticker
            and o.state in (OrderState.SUBMITTED, OrderState.ACCEPTED, OrderState.PARTIALLY_FILLED)
        ]
        return pending

    def pending_orders(self) -> List[ShadowOrder]:
        """전체 미체결 shadow 주문."""
        return [
            o for o in self._orders.values()
            if o.state in (OrderState.SUBMITTED, OrderState.ACCEPTED, OrderState.PARTIALLY_FILLED)
        ]

    @property
    def order_count(self) -> int:
        return len(self._orders)
