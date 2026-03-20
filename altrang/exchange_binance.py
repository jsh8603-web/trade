"""AltRang Binance Adapter -- 바이낸스 현물+선물 거래소 어댑터

기존 BinanceExecutor + UniverseScanner를 ExchangeAdapter 인터페이스로 래핑한다.
"""

import logging

from altrang.config import AltrangConfig
from altrang.data_feeder import CoinData, UniverseScanner
from altrang.execution import BinanceExecutor, OrderResult, HedgedResult
from altrang.exchange_base import ExchangeAdapter

logger = logging.getLogger("altrang.binance_adapter")


class BinanceAdapter(ExchangeAdapter):
    """바이낸스 거래소 어댑터 (기존 코드 위임)"""

    def __init__(self, config: AltrangConfig):
        self.config = config
        self._executor = BinanceExecutor(config)
        self._scanner = UniverseScanner(config)

    async def start(self):
        await self._executor.start()
        await self._scanner.start()
        logger.info("Binance 어댑터 시작")

    async def close(self):
        await self._executor.close()
        await self._scanner.close()

    # ─── 유니버스 스캔 ───

    async def scan_universe(self) -> dict[str, CoinData]:
        return await self._scanner.scan()

    async def enrich_candidates(
        self, data: dict[str, CoinData], top_n: int = 50,
    ) -> dict[str, CoinData]:
        return await self._scanner.enrich_candidates(data, top_n)

    async def enrich_funding_candidates(
        self, data: dict[str, CoinData], top_n: int = 15, history_lookback: int = 21,
    ) -> dict[str, CoinData]:
        return await self._scanner.enrich_funding_candidates(data, top_n, history_lookback)

    # ─── 현물 매매 ───

    async def spot_buy(self, symbol: str, quote_amount: float, price: float) -> OrderResult:
        return await self._executor.spot_buy(symbol, quote_amount, price)

    async def spot_sell(self, symbol: str, qty: float) -> OrderResult:
        return await self._executor.spot_sell(symbol, qty)

    # ─── 잔고 ───

    async def get_spot_balances(self) -> dict[str, float]:
        return await self._executor.get_spot_balances()

    # ─── 선물/펀딩비 (Binance 전용) ───

    async def enter_hedged(self, symbol, usdt_amount, spot_price, futures_price) -> HedgedResult:
        return await self._executor.enter_hedged(symbol, usdt_amount, spot_price, futures_price)

    async def exit_hedged(self, symbol, spot_qty, futures_qty) -> HedgedResult:
        return await self._executor.exit_hedged(symbol, spot_qty, futures_qty)

    async def ensure_bnb_reserve(self) -> bool:
        return await self._executor.ensure_bnb_reserve()

    async def get_futures_positions(self) -> dict:
        return await self._executor.get_futures_positions()

    async def set_leverage(self, symbol: str, leverage: int = 1) -> bool:
        return await self._executor.set_leverage(symbol, leverage)

    @property
    def last_scan_time(self) -> float:
        return self._scanner.last_scan_time
