"""SeonbiRang Data Feeder -- 멀티코인 시장 데이터 수집

REST 폴링으로 전체 코인 유니버스를 스캔하고,
WebSocket으로 보유 코인의 실시간 가격을 추적한다.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import aiohttp

from seonbirang.config import SeonbirangConfig, COIN_BLACKLIST

logger = logging.getLogger("seonbirang.feeder")


@dataclass
class CoinData:
    """개별 코인 시장 데이터"""
    symbol: str = ""
    spot_price: float = 0.0
    futures_price: float = 0.0
    funding_rate: float = 0.0
    next_funding_time: int = 0
    volume_24h: float = 0.0
    quote_volume_24h: float = 0.0
    price_change_pct_1h: float = 0.0
    price_change_pct_4h: float = 0.0
    price_change_pct_24h: float = 0.0
    open_interest: float = 0.0
    timestamp: float = 0.0


class UniverseScanner:
    """Binance REST 폴링: 전체 선물 시장 스캔

    API 2~3회 호출로 모든 코인 데이터를 수집한다.
    """

    def __init__(self, config: SeonbirangConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_scan: dict[str, CoinData] = {}
        self._last_scan_time: float = 0.0

    async def start(self):
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15)
        )

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def scan(self) -> dict[str, CoinData]:
        """전체 USDT 퍼프 코인 스캔

        3개 API를 병렬 호출:
        1. /fapi/v1/premiumIndex -- 펀딩비, 마크가격
        2. /fapi/v1/ticker/24hr -- 24시간 통계
        3. /api/v3/ticker/price  -- 현물 가격
        """
        if not self._session or self._session.closed:
            return self._last_scan

        try:
            futures_url = self.config.binance.futures_rest_url
            spot_url = self.config.binance.spot_rest_url

            premium_task = self._fetch_json(f"{futures_url}/fapi/v1/premiumIndex")
            ticker_task = self._fetch_json(f"{futures_url}/fapi/v1/ticker/24hr")
            spot_task = self._fetch_json(f"{spot_url}/api/v3/ticker/price")

            premium_data, ticker_data, spot_data = await asyncio.gather(
                premium_task, ticker_task, spot_task,
                return_exceptions=True,
            )

            if isinstance(premium_data, Exception):
                logger.error(f"premiumIndex 실패: {premium_data}")
                return self._last_scan
            if isinstance(ticker_data, Exception):
                logger.error(f"ticker/24hr 실패: {ticker_data}")
                return self._last_scan

            # 현물 가격 맵
            spot_prices = {}
            if not isinstance(spot_data, Exception) and spot_data:
                for item in spot_data:
                    sym = item.get("symbol", "")
                    if sym.endswith("USDT"):
                        try:
                            spot_prices[sym] = float(item["price"])
                        except (KeyError, ValueError):
                            pass

            # 24h 통계 맵
            ticker_map = {}
            if ticker_data:
                for item in ticker_data:
                    sym = item.get("symbol", "")
                    if sym.endswith("USDT"):
                        ticker_map[sym] = item

            # 조합
            now = time.time()
            result: dict[str, CoinData] = {}

            for item in premium_data or []:
                sym = item.get("symbol", "")
                if not sym.endswith("USDT") or sym in COIN_BLACKLIST:
                    continue

                try:
                    funding_rate = float(item.get("lastFundingRate", 0))
                    futures_price = float(item.get("markPrice", 0))
                    next_funding = int(item.get("nextFundingTime", 0))
                except (ValueError, TypeError):
                    continue

                if futures_price <= 0:
                    continue

                tk = ticker_map.get(sym, {})
                try:
                    volume_24h = float(tk.get("volume", 0))
                    quote_vol = float(tk.get("quoteVolume", 0))
                    change_24h = float(tk.get("priceChangePercent", 0))
                except (ValueError, TypeError):
                    volume_24h = 0
                    quote_vol = 0
                    change_24h = 0

                coin = CoinData(
                    symbol=sym,
                    spot_price=spot_prices.get(sym, 0.0),
                    futures_price=futures_price,
                    funding_rate=funding_rate,
                    next_funding_time=next_funding,
                    volume_24h=volume_24h,
                    quote_volume_24h=quote_vol,
                    price_change_pct_24h=change_24h,
                    timestamp=now,
                )
                result[sym] = coin

            self._last_scan = result
            self._last_scan_time = now
            logger.info(f"유니버스 스캔 완료: {len(result)}개 USDT 페어")
            return result

        except Exception as e:
            logger.error(f"유니버스 스캔 오류: {e}")
            return self._last_scan

    async def _fetch_json(self, url: str):
        async with self._session.get(url) as resp:
            if resp.status == 200:
                return await resp.json()
            logger.warning(f"API 응답 {resp.status}: {url}")
            return None

    @property
    def last_scan_time(self) -> float:
        return self._last_scan_time


class MultiCoinFeeder:
    """통합 데이터 피더: REST 스캔 + 실시간 가격"""

    def __init__(self, config: SeonbirangConfig):
        self.config = config
        self.scanner = UniverseScanner(config)
        self._data: dict[str, CoinData] = {}
        self._running = False
        self._scan_interval = 120  # 2분마다 스캔

    async def start(self):
        await self.scanner.start()
        self._running = True
        logger.info("MultiCoinFeeder 시작")

    async def stop(self):
        self._running = False
        await self.scanner.close()
        logger.info("MultiCoinFeeder 정지")

    async def scan_universe(self) -> dict[str, CoinData]:
        """유니버스 스캔 실행 (외부에서 호출)"""
        self._data = await self.scanner.scan()
        return self._data

    async def wait_ready(self, timeout: float = 30) -> bool:
        """초기 데이터 준비 대기"""
        start = time.time()
        while time.time() - start < timeout:
            data = await self.scan_universe()
            if len(data) > 10:
                logger.info(f"데이터 준비 완료: {len(data)}개 코인 ({time.time()-start:.1f}초)")
                return True
            await asyncio.sleep(2)
        logger.error(f"데이터 준비 타임아웃 ({timeout}초)")
        return False

    def get_coin(self, symbol: str) -> Optional[CoinData]:
        return self._data.get(symbol)

    def get_all(self) -> dict[str, CoinData]:
        return self._data

    def needs_scan(self) -> bool:
        return time.time() - self.scanner.last_scan_time > self._scan_interval
