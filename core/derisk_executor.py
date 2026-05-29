"""core/derisk_executor.py — 무인 자동 de-risk 집행기 (Phase Unattended SO-1 + SO-3).

설계 원칙:
  - LLM/brain/judge/consensus/HRP import 0 (완전 독립 fail-safe).
  - fail-safe: 예외 시 더 줄이는 방향, never fail-open.
  - idempotent: 이미 floor면 no-op.
  - 거래소 truth 직접 query (내부 ledger 불신).

SO-1: DeriskResult / ExchangeAdapter / DeriskExecutor (cancel_only / derisk_to_floor).
SO-3: _escalate_liquidation (IOC ladder, thin-book, frozen bag -10% 상한).

SACRED: market order 사용 금지. 전량 시장가 청산 금지.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

logger = logging.getLogger("core.derisk_executor")

# ── 환경 변수 파라미터 ─────────────────────────────────────────────────

_LADDER_BANDS_STR = os.environ.get("UNATTENDED_LADDER_BANDS", "-0.01,-0.03,-0.05")
LADDER_BANDS: list[float] = [float(b) for b in _LADDER_BANDS_STR.split(",")]

MAX_SLIPPAGE = float(os.environ.get("UNATTENDED_MAX_SLIPPAGE", "-0.10"))  # -10% frozen 상한
LADDER_STEP_SEC = float(os.environ.get("UNATTENDED_LADDER_STEP_SEC", "2.0"))

_FROZEN_BAG_PATH = Path(os.environ.get("UNATTENDED_FROZEN_BAG_PATH", "data/frozen_bag.json"))


# ── 데이터 클래스 ─────────────────────────────────────────────────────

@dataclass
class FillResult:
    """단일 IOC 주문 체결 결과."""
    filled_qty: float   # 체결 수량
    avg_price: float    # 체결 평균가 (미체결 시 0.0)
    slippage: float     # (체결가 - mid) / mid (매도: 음수)


@dataclass
class Orderbook:
    """호가 스냅샷."""
    bids: list[tuple[float, float]]  # (price, qty) 내림차순
    asks: list[tuple[float, float]]  # (price, qty) 오름차순

    def mid(self) -> float:
        """중간가."""
        if not self.bids or not self.asks:
            return 0.0
        return (self.bids[0][0] + self.asks[0][0]) / 2.0


@dataclass
class DeriskResult:
    """de-risk 집행 결과."""
    reduced: dict[str, float]   # symbol → 집행 후 잔여 수량
    frozen: list[str]           # frozen bag 처리된 symbol 목록
    fully_done: bool            # 모든 symbol이 floor 이하로 축소됐는지
    reason: str                 # 집행 사유


# ── 거래소 어댑터 Protocol ────────────────────────────────────────────

@runtime_checkable
class ExchangeAdapter(Protocol):
    """거래소 인터페이스 — 실거래소 구현은 SO-6 wire 시 추가."""

    def query_live_positions(self) -> dict[str, float]:
        """현재 보유 포지션 {symbol: qty}. 거래소 truth 직접 조회."""
        ...

    def cancel_all_open_orders(self) -> int:
        """모든 미체결 주문 취소. 반환: 취소된 주문 수."""
        ...

    def submit_ioc_limit(
        self,
        symbol: str,
        side: str,
        qty: float,
        limit_price: float,
    ) -> FillResult:
        """IOC 지정가 주문 제출 (시장가 금지). side="sell"|"buy"."""
        ...

    def get_orderbook(self, symbol: str) -> Orderbook:
        """호가 조회."""
        ...


# ── FakeExchange (테스트 더블) ────────────────────────────────────────

class FakeExchange:
    """테스트 전용 가짜 거래소.

    positions: 초기 포지션.
    fill_ratio: 각 IOC 주문에서 체결될 비율 (기본 1.0 = 전량).
    mid_price: 기본 중간가.
    raise_on_query: True 시 query_live_positions 에서 예외 발생.
    """

    def __init__(
        self,
        positions: dict[str, float] | None = None,
        fill_ratio: float = 1.0,
        mid_price: float = 10_000.0,
        raise_on_query: bool = False,
    ) -> None:
        self._positions: dict[str, float] = dict(positions or {})
        self._fill_ratio = fill_ratio
        self._mid_price = mid_price
        self._raise_on_query = raise_on_query
        self.cancelled_orders: int = 0
        self.submit_calls: list[dict] = []

    def query_live_positions(self) -> dict[str, float]:
        if self._raise_on_query:
            raise RuntimeError("exchange query failed (test)")
        return dict(self._positions)

    def cancel_all_open_orders(self) -> int:
        self.cancelled_orders += 1
        return 0  # 테스트: 취소 건수 0 (없어도 호출 증명)

    def submit_ioc_limit(
        self,
        symbol: str,
        side: str,
        qty: float,
        limit_price: float,
    ) -> FillResult:
        call = {"symbol": symbol, "side": side, "qty": qty, "limit_price": limit_price}
        self.submit_calls.append(call)

        if side != "sell":
            return FillResult(filled_qty=0.0, avg_price=0.0, slippage=0.0)

        filled = qty * self._fill_ratio
        if symbol in self._positions:
            self._positions[symbol] = max(0.0, self._positions[symbol] - filled)

        slippage = (limit_price - self._mid_price) / self._mid_price if self._mid_price else 0.0
        return FillResult(
            filled_qty=filled,
            avg_price=limit_price if filled > 0 else 0.0,
            slippage=slippage,
        )

    def get_orderbook(self, symbol: str) -> Orderbook:
        p = self._mid_price
        return Orderbook(
            bids=[(p * 0.999, 100.0)],
            asks=[(p * 1.001, 100.0)],
        )


# ── DeriskExecutor ────────────────────────────────────────────────────

class DeriskExecutor:
    """무인 de-risk 집행기.

    soft tier: cancel_only — 미체결 주문 취소 + 신규 진입 차단.
    hard tier: derisk_to_floor — IOC ladder 단계 청산으로 floor까지 축소.

    ⛔ LLM/brain/HRP import 0. fail-safe: 예외 → 더 줄이는 방향.
    """

    def __init__(self, exchange: ExchangeAdapter) -> None:
        self._exchange = exchange
        self._entry_blocked: bool = False  # 신규 진입 차단 플래그
        self._frozen_symbols: set[str] = set()  # frozen bag 처리된 symbol

    # ── Public API ────────────────────────────────────────────────────

    def cancel_only(self, reason: str) -> DeriskResult:
        """Soft tier — 미체결 주문 취소 + 신규 진입 차단 (청산 안 함, reversible)."""
        logger.warning("derisk cancel_only: %s", reason)
        try:
            n = self._exchange.cancel_all_open_orders()
            logger.info("cancel_only: cancelled %d orders", n)
        except Exception as exc:  # noqa: BLE001
            logger.error("cancel_only: cancel_all_open_orders failed: %s", exc)
            # fail-safe: 취소 실패해도 차단 플래그는 set
        self._entry_blocked = True
        return DeriskResult(
            reduced={},
            frozen=list(self._frozen_symbols),
            fully_done=False,
            reason=reason,
        )

    def derisk_to_floor(
        self,
        floors: dict[str, float],
        reason: str,
        now: float | None = None,
    ) -> DeriskResult:
        """Hard tier — 거래소 truth 기준으로 floor까지 IOC 단계 청산.

        floors: {symbol: 목표_잔여_수량}. floor 0.0 = 전량 청산 시도(IOC 상한 내).
        now: 타임스탬프(테스트 주입용).
        """
        if now is None:
            now = time.time()
        logger.warning("derisk_to_floor: %s | floors=%s", reason, floors)

        # (a) 미체결 주문 취소 (예외 시도 계속)
        try:
            self._exchange.cancel_all_open_orders()
        except Exception as exc:  # noqa: BLE001
            logger.error("derisk_to_floor: cancel failed (continuing): %s", exc)

        self._entry_blocked = True

        # (b) 거래소 truth 조회
        try:
            positions = self._exchange.query_live_positions()
        except Exception as exc:  # noqa: BLE001
            logger.error("derisk_to_floor: query_live_positions failed: %s — applying cancel only", exc)
            # fail-safe: 포지션 조회 실패 → cancel 보장 + fail-open 금지
            # (no-op 반환 금지 — cancel은 이미 완료됨)
            return DeriskResult(
                reduced={},
                frozen=list(self._frozen_symbols),
                fully_done=False,
                reason=f"{reason} [query_failed]",
            )

        reduced: dict[str, float] = {}
        all_done = True

        # (c) symbol별 IOC ladder 단계 청산
        for symbol, position_qty in positions.items():
            target_floor = floors.get(symbol, 0.0)
            excess = position_qty - target_floor

            if excess <= 1e-12:
                # 이미 floor 이하 (idempotent)
                reduced[symbol] = position_qty
                continue

            if symbol in self._frozen_symbols:
                # frozen bag: 매매 중단
                reduced[symbol] = position_qty
                all_done = False
                logger.info("derisk_to_floor: %s frozen — skipping", symbol)
                continue

            # SO-3: IOC ladder 단계 청산
            final_qty, is_frozen = self._escalate_liquidation(symbol, excess, now)
            remaining = max(0.0, position_qty - (excess - final_qty))

            # (d) re-query 체결 검증
            try:
                live = self._exchange.query_live_positions()
                remaining = live.get(symbol, remaining)
            except Exception:  # noqa: BLE001
                pass  # re-query 실패 시 추정값 유지

            reduced[symbol] = remaining
            if remaining > target_floor + 1e-12 and not is_frozen:
                all_done = False

        # floors에 있지만 positions에 없는 symbol도 기록
        for symbol, target_floor in floors.items():
            if symbol not in reduced:
                reduced[symbol] = 0.0  # 이미 0

        return DeriskResult(
            reduced=reduced,
            frozen=list(self._frozen_symbols),
            fully_done=all_done,
            reason=reason,
        )

    @property
    def entry_blocked(self) -> bool:
        """신규 진입 차단 상태."""
        return self._entry_blocked

    def clear_entry_block(self) -> None:
        """신규 진입 차단 해제 (re-arm 시 FSM 이 호출)."""
        self._entry_blocked = False

    # ── SO-3: IOC Ladder ──────────────────────────────────────────────

    def _escalate_liquidation(
        self,
        symbol: str,
        target_reduce_qty: float,
        now: float,
    ) -> tuple[float, bool]:
        """IOC ladder 단계 청산.

        Returns: (총_체결량, frozen_여부).
        ⛔ naked market order 금지 — IOC 지정가만 사용.
        frozen bag 누적 슬리피지 -10% 도달 시 중단 + data/frozen_bag.json 기록.
        """
        try:
            orderbook = self._exchange.get_orderbook(symbol)
            mid = orderbook.mid()
        except Exception as exc:  # noqa: BLE001
            logger.error("_escalate_liquidation: get_orderbook failed for %s: %s", symbol, exc)
            return 0.0, False

        if mid <= 0.0:
            logger.error("_escalate_liquidation: mid price 0 for %s — skipping", symbol)
            return 0.0, False

        remaining_qty = target_reduce_qty
        cumulative_slippage = 0.0
        total_filled = 0.0

        for band in LADDER_BANDS:
            if remaining_qty <= 1e-12:
                break

            limit_price = mid * (1.0 + band)  # 매도 기준: mid보다 낮은 limit

            try:
                fill = self._exchange.submit_ioc_limit(
                    symbol=symbol,
                    side="sell",
                    qty=remaining_qty,
                    limit_price=limit_price,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "_escalate_liquidation: submit_ioc_limit failed [band=%.3f]: %s", band, exc
                )
                # fail-safe: 이 band 실패 → 다음 band 시도
                time.sleep(LADDER_STEP_SEC)
                continue

            total_filled += fill.filled_qty
            remaining_qty = max(0.0, remaining_qty - fill.filled_qty)

            if fill.filled_qty > 0:
                # 슬리피지 누적 (실제 체결가 기준 vs mid)
                band_slippage = (fill.avg_price - mid) / mid  # 음수(매도 할인)
                cumulative_slippage += band_slippage

            logger.debug(
                "_escalate_liquidation %s band=%.3f filled=%.6f remaining=%.6f cumslip=%.4f",
                symbol, band, fill.filled_qty, remaining_qty, cumulative_slippage,
            )

            # frozen bag 상한 체크: 누적 슬리피지 MAX_SLIPPAGE(-10%) 초과
            # remaining 잔여 여부와 무관 — 슬리피지가 임계 초과하면 bag 마킹
            if cumulative_slippage <= MAX_SLIPPAGE:
                logger.warning(
                    "_escalate_liquidation: %s frozen bag (cumslip=%.4f, remaining=%.6f)",
                    symbol, cumulative_slippage, remaining_qty,
                )
                self._frozen_symbols.add(symbol)
                self._record_frozen_bag(symbol, remaining_qty, now, "max_slippage")
                return total_filled, True

            if remaining_qty > 1e-12:
                time.sleep(LADDER_STEP_SEC)

        return total_filled, False

    def _record_frozen_bag(
        self,
        symbol: str,
        qty: float,
        ts: float,
        reason: str,
    ) -> None:
        """frozen_bag.json 에 {symbol, qty, ts, reason} append."""
        entry = {"symbol": symbol, "qty": qty, "ts": ts, "reason": reason}
        path = _FROZEN_BAG_PATH
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            existing: list[dict] = []
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    try:
                        existing = json.load(f)
                    except json.JSONDecodeError:
                        existing = []
            existing.append(entry)
            with path.open("w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            logger.warning("frozen_bag recorded: %s", entry)
        except Exception as exc:  # noqa: BLE001
            logger.error("_record_frozen_bag: write failed: %s", exc)
