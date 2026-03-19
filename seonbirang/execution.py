"""SeonbiRang Execution -- Binance Spot + Futures 주문 실행

핵심 원칙:
  1. 헤지 진입: Spot Buy + Futures Short을 asyncio.gather()로 동시 실행
  2. 한쪽 실패 시 다른 쪽 긴급 청산 (레그 리스크 방지)
  3. DRY_RUN 모드에서는 실제 주문 없이 시뮬레이션
  4. BNB 수수료 결제 잔고 확인
"""

import asyncio
import hashlib
import hmac
import logging
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional

import aiohttp

from seonbirang.config import SeonbirangConfig

logger = logging.getLogger("seonbirang.execution")

_NON_RETRYABLE_STATUS = {400, 401, 403, 404, 422}


@dataclass
class OrderResult:
    """단일 주문 결과"""
    exchange: str = ""           # "spot" or "futures"
    success: bool = False
    order_id: str = ""
    filled_price: float = 0.0
    filled_qty: float = 0.0
    side: str = ""
    symbol: str = ""
    error: str = ""
    latency_ms: float = 0.0


@dataclass
class HedgedResult:
    """헤지 (Spot + Futures) 동시 주문 결과"""
    action: str = ""              # "enter" or "exit"
    symbol: str = ""
    spot_leg: OrderResult = field(default_factory=lambda: OrderResult(exchange="spot"))
    futures_leg: OrderResult = field(default_factory=lambda: OrderResult(exchange="futures"))
    dry_run: bool = True
    timestamp: float = field(default_factory=time.time)

    @property
    def both_success(self) -> bool:
        return self.spot_leg.success and self.futures_leg.success

    @property
    def partial_fill(self) -> bool:
        return self.spot_leg.success != self.futures_leg.success


class BinanceExecutor:
    """Binance 주문 실행기 (현물 + 선물)"""

    def __init__(self, config: SeonbirangConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._server_time_offset: int = 0

    async def start(self):
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        await self._sync_server_time()

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ─── 서버 시간 동기화 ───

    async def _sync_server_time(self):
        """Binance 서버 시간과 로컬 시간 차이 계산"""
        try:
            url = f"{self.config.binance.futures_rest_url}/fapi/v1/time"
            async with self._session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    server_time = data["serverTime"]
                    local_time = int(time.time() * 1000)
                    self._server_time_offset = server_time - local_time
                    logger.info(f"서버 시간 오프셋: {self._server_time_offset}ms")
        except Exception as e:
            logger.warning(f"서버 시간 동기화 실패: {e}")

    def _timestamp(self) -> int:
        return int(time.time() * 1000) + self._server_time_offset

    # ─── 서명 ───

    def _sign(self, params: dict) -> str:
        query = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.config.binance.api_secret.encode(),
            query.encode(),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _auth_headers(self) -> dict:
        return {"X-MBX-APIKEY": self.config.binance.api_key}

    # ─── 현물 주문 ───

    async def spot_market_order(
        self, symbol: str, side: str, qty: Optional[float] = None,
        quote_qty: Optional[float] = None,
    ) -> OrderResult:
        """현물 시장가 주문"""
        result = OrderResult(exchange="spot", symbol=symbol, side=side)
        start = time.time()

        if self.config.safety.dry_run:
            result.success = True
            result.order_id = f"DRY_{int(time.time()*1000)}"
            # 시뮬레이션 가격은 외부에서 설정
            result.latency_ms = 0
            return result

        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "timestamp": self._timestamp(),
        }
        if qty:
            params["quantity"] = f"{qty:.8f}".rstrip("0").rstrip(".")
        elif quote_qty:
            params["quoteOrderQty"] = f"{quote_qty:.2f}"
        else:
            result.error = "qty 또는 quote_qty 필요"
            return result

        params["signature"] = self._sign(params)

        try:
            url = f"{self.config.binance.spot_rest_url}/api/v3/order"
            async with self._session.post(
                url, params=params, headers=self._auth_headers()
            ) as resp:
                data = await resp.json()
                result.latency_ms = (time.time() - start) * 1000

                if resp.status == 200:
                    result.success = True
                    result.order_id = str(data.get("orderId", ""))
                    # 체결 가격 계산
                    fills = data.get("fills", [])
                    if fills:
                        total_qty = sum(float(f["qty"]) for f in fills)
                        total_cost = sum(float(f["qty"]) * float(f["price"]) for f in fills)
                        result.filled_qty = total_qty
                        result.filled_price = total_cost / total_qty if total_qty > 0 else 0
                    else:
                        result.filled_qty = float(data.get("executedQty", 0))
                        result.filled_price = float(data.get("price", 0))
                else:
                    result.error = f"HTTP {resp.status}: {data.get('msg', str(data)[:200])}"
                    logger.error(f"현물 주문 실패: {result.error}")
        except Exception as e:
            result.error = str(e)
            result.latency_ms = (time.time() - start) * 1000
            logger.error(f"현물 주문 오류: {e}")

        return result

    # ─── 선물 주문 ───

    async def futures_market_order(
        self, symbol: str, side: str, qty: float
    ) -> OrderResult:
        """선물 시장가 주문"""
        result = OrderResult(exchange="futures", symbol=symbol, side=side)
        start = time.time()

        if self.config.safety.dry_run:
            result.success = True
            result.order_id = f"DRY_F_{int(time.time()*1000)}"
            result.latency_ms = 0
            return result

        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "quantity": f"{qty:.8f}".rstrip("0").rstrip("."),
            "timestamp": self._timestamp(),
        }
        params["signature"] = self._sign(params)

        try:
            url = f"{self.config.binance.futures_rest_url}/fapi/v1/order"
            async with self._session.post(
                url, params=params, headers=self._auth_headers()
            ) as resp:
                data = await resp.json()
                result.latency_ms = (time.time() - start) * 1000

                if resp.status == 200:
                    result.success = True
                    result.order_id = str(data.get("orderId", ""))
                    result.filled_qty = float(data.get("executedQty", 0))
                    result.filled_price = float(data.get("avgPrice", 0))
                else:
                    result.error = f"HTTP {resp.status}: {data.get('msg', str(data)[:200])}"
                    logger.error(f"선물 주문 실패: {result.error}")
        except Exception as e:
            result.error = str(e)
            result.latency_ms = (time.time() - start) * 1000
            logger.error(f"선물 주문 오류: {e}")

        return result

    # ─── 레버리지 설정 ───

    async def set_leverage(self, symbol: str, leverage: int = 1) -> bool:
        """선물 레버리지 설정"""
        if self.config.safety.dry_run:
            return True

        params = {
            "symbol": symbol,
            "leverage": leverage,
            "timestamp": self._timestamp(),
        }
        params["signature"] = self._sign(params)

        try:
            url = f"{self.config.binance.futures_rest_url}/fapi/v1/leverage"
            async with self._session.post(
                url, params=params, headers=self._auth_headers()
            ) as resp:
                if resp.status == 200:
                    logger.info(f"{symbol} 레버리지 {leverage}x 설정 완료")
                    return True
                data = await resp.json()
                logger.warning(f"{symbol} 레버리지 설정 실패: {data.get('msg', '')}")
                return False
        except Exception as e:
            logger.error(f"레버리지 설정 오류: {e}")
            return False

    # ─── 델타뉴트럴 헤지 진입/청산 ───

    async def enter_hedged(
        self, symbol: str, usdt_amount: float, spot_price: float, futures_price: float
    ) -> HedgedResult:
        """델타뉴트럴 진입: Spot Buy + Futures Short 동시"""
        result = HedgedResult(action="enter", symbol=symbol, dry_run=self.config.safety.dry_run)

        qty = usdt_amount / spot_price
        # 소수점 자릿수 조정 (심볼별로 다르나 일반적으로 3~5자리)
        qty = round(qty, 5)

        if self.config.safety.dry_run:
            result.spot_leg.success = True
            result.spot_leg.filled_price = spot_price
            result.spot_leg.filled_qty = qty
            result.spot_leg.side = "BUY"
            result.spot_leg.order_id = f"DRY_{int(time.time()*1000)}"
            result.futures_leg.success = True
            result.futures_leg.filled_price = futures_price
            result.futures_leg.filled_qty = qty
            result.futures_leg.side = "SELL"
            result.futures_leg.order_id = f"DRY_F_{int(time.time()*1000)}"
            logger.info(f"[DRY] 헤지 진입: {symbol} qty={qty:.5f} ${usdt_amount:.0f}")
            return result

        # 레버리지 설정
        await self.set_leverage(symbol, self.config.funding.leverage)

        # 동시 주문
        spot_task = self.spot_market_order(symbol, "BUY", qty=qty)
        futures_task = self.futures_market_order(symbol, "SELL", qty)

        spot_result, futures_result = await asyncio.gather(
            spot_task, futures_task, return_exceptions=True
        )

        if isinstance(spot_result, Exception):
            result.spot_leg.error = str(spot_result)
        else:
            result.spot_leg = spot_result

        if isinstance(futures_result, Exception):
            result.futures_leg.error = str(futures_result)
        else:
            result.futures_leg = futures_result

        # 한쪽만 성공 → 긴급 청산
        if result.partial_fill:
            logger.error(f"헤지 진입 편측 체결! {symbol} -- 긴급 청산")
            await self._emergency_unwind(result)

        return result

    async def exit_hedged(
        self, symbol: str, spot_qty: float, futures_qty: float
    ) -> HedgedResult:
        """델타뉴트럴 청산: Spot Sell + Futures Cover 동시"""
        result = HedgedResult(action="exit", symbol=symbol, dry_run=self.config.safety.dry_run)

        if self.config.safety.dry_run:
            result.spot_leg.success = True
            result.spot_leg.side = "SELL"
            result.spot_leg.filled_qty = spot_qty
            result.futures_leg.success = True
            result.futures_leg.side = "BUY"
            result.futures_leg.filled_qty = futures_qty
            logger.info(f"[DRY] 헤지 청산: {symbol}")
            return result

        spot_task = self.spot_market_order(symbol, "SELL", qty=spot_qty)
        futures_task = self.futures_market_order(symbol, "BUY", futures_qty)

        spot_result, futures_result = await asyncio.gather(
            spot_task, futures_task, return_exceptions=True
        )

        if isinstance(spot_result, Exception):
            result.spot_leg.error = str(spot_result)
        else:
            result.spot_leg = spot_result

        if isinstance(futures_result, Exception):
            result.futures_leg.error = str(futures_result)
        else:
            result.futures_leg = futures_result

        if result.partial_fill:
            logger.error(f"헤지 청산 편측 체결! {symbol} -- 긴급 청산")
            await self._emergency_unwind(result)

        return result

    # ─── 현물 단순 매매 (로테이션용) ───

    async def spot_buy(self, symbol: str, usdt_amount: float, price: float) -> OrderResult:
        """현물 매수 (USDT 금액 지정)"""
        if self.config.safety.dry_run:
            qty = usdt_amount / price if price > 0 else 0
            return OrderResult(
                exchange="spot", success=True, symbol=symbol, side="BUY",
                filled_price=price, filled_qty=qty,
                order_id=f"DRY_{int(time.time()*1000)}",
            )
        return await self.spot_market_order(symbol, "BUY", quote_qty=usdt_amount)

    async def spot_sell(self, symbol: str, qty: float) -> OrderResult:
        """현물 매도 (수량 지정)"""
        if self.config.safety.dry_run:
            return OrderResult(
                exchange="spot", success=True, symbol=symbol, side="SELL",
                filled_qty=qty, order_id=f"DRY_{int(time.time()*1000)}",
            )
        return await self.spot_market_order(symbol, "SELL", qty=qty)

    # ─── 잔고 조회 ───

    async def get_spot_balances(self) -> dict[str, float]:
        """현물 잔고 조회"""
        if self.config.safety.dry_run:
            return {"USDT": 5000.0, "BNB": 0.1}

        params = {"timestamp": self._timestamp()}
        params["signature"] = self._sign(params)

        try:
            url = f"{self.config.binance.spot_rest_url}/api/v3/account"
            async with self._session.get(
                url, params=params, headers=self._auth_headers()
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    balances = {}
                    for b in data.get("balances", []):
                        free = float(b.get("free", 0))
                        if free > 0:
                            balances[b["asset"]] = free
                    return balances
        except Exception as e:
            logger.error(f"잔고 조회 오류: {e}")
        return {}

    async def get_futures_positions(self) -> dict[str, dict]:
        """선물 포지션 조회"""
        if self.config.safety.dry_run:
            return {}

        params = {"timestamp": self._timestamp()}
        params["signature"] = self._sign(params)

        try:
            url = f"{self.config.binance.futures_rest_url}/fapi/v2/positionRisk"
            async with self._session.get(
                url, params=params, headers=self._auth_headers()
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    positions = {}
                    for p in data:
                        amt = float(p.get("positionAmt", 0))
                        if amt != 0:
                            positions[p["symbol"]] = {
                                "qty": amt,
                                "entry_price": float(p.get("entryPrice", 0)),
                                "unrealized_pnl": float(p.get("unRealizedProfit", 0)),
                                "leverage": int(p.get("leverage", 1)),
                            }
                    return positions
        except Exception as e:
            logger.error(f"선물 포지션 조회 오류: {e}")
        return {}

    # ─── BNB 잔고 확인 ───

    async def ensure_bnb_reserve(self) -> bool:
        """BNB 수수료 결제용 최소 잔고 확인"""
        if not self.config.safety.use_bnb_fee:
            return True
        balances = await self.get_spot_balances()
        bnb = balances.get("BNB", 0)
        if bnb < self.config.safety.min_bnb_reserve:
            logger.warning(
                f"BNB 잔고 부족: {bnb:.4f} < {self.config.safety.min_bnb_reserve}"
            )
            return False
        return True

    # ─── 긴급 청산 ───

    async def _emergency_unwind(self, result: HedgedResult):
        """편측 체결 시 긴급 청산"""
        logger.critical(f"긴급 청산 시작: {result.symbol}")

        if result.spot_leg.success and not result.futures_leg.success:
            # 현물만 체결 → 현물 되팔기
            side = "SELL" if result.spot_leg.side == "BUY" else "BUY"
            await self.spot_market_order(
                result.symbol, side, qty=result.spot_leg.filled_qty
            )
        elif result.futures_leg.success and not result.spot_leg.success:
            # 선물만 체결 → 선물 청산
            side = "BUY" if result.futures_leg.side == "SELL" else "SELL"
            await self.futures_market_order(
                result.symbol, side, result.futures_leg.filled_qty
            )
