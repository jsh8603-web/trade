"""AltRang Data Feeder -- 멀티코인 시장 데이터 수집

REST 폴링으로 전체 코인 유니버스를 스캔하고,
kline 심화 분석으로 기술적 지표(RSI/BB/상관도)를 산출한다.
"""

import asyncio
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Optional

import aiohttp

from altrang.config import AltrangConfig, COIN_BLACKLIST

logger = logging.getLogger("altrang.feeder")


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
    spot_quote_volume_24h: float = 0.0
    price_change_pct_1h: float = 0.0
    price_change_pct_4h: float = 0.0
    price_change_pct_24h: float = 0.0
    open_interest: float = 0.0
    timestamp: float = 0.0
    # kline 심화 분석 필드
    rsi_14: float = 50.0              # RSI(14) — 기본 중립
    bb_position: float = 0.5          # 볼린저밴드 위치 (0=하단, 1=상단)
    volume_surge_ratio: float = 1.0   # 현재 24h 거래량 / 7일 평균
    trend_1h: float = 0.0             # 1시간 추세 (%)
    trend_4h: float = 0.0             # 4시간 추세 (%)
    btc_correlation: float = 0.5      # BTC 24h 수익률 상관도
    kline_enriched: bool = False       # kline 심화 분석 완료 여부
    # 펀딩비 히스토리 분석 필드
    funding_history: list = field(default_factory=list)  # 과거 펀딩비 리스트
    funding_avg_7d: float = 0.0        # 7일 평균 펀딩비
    funding_positive_ratio: float = 0.0  # 양수 비율 (0~1)
    funding_std: float = 0.0           # 펀딩비 표준편차
    funding_enriched: bool = False     # 펀딩비 심화 분석 완료


class UniverseScanner:
    """Binance REST 폴링: 전체 선물 시장 스캔

    API 2~3회 호출로 모든 코인 데이터를 수집한다.
    """

    def __init__(self, config: AltrangConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_scan: dict[str, CoinData] = {}
        self._last_scan_time: float = 0.0
        # exchangeInfo 캐시 (상장폐지 필터용)
        self._active_spot_symbols: set[str] = set()
        self._exchange_info_time: float = 0.0

    async def start(self):
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15)
        )

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _refresh_exchange_info(self):
        """Binance exchangeInfo 캐시 갱신 (상장폐지/비활성 코인 필터용)

        6시간마다 갱신. 응답이 ~2MB로 크므로 캐싱 필수.
        """
        now = time.time()
        refresh_secs = self.config.binance.exchange_info_refresh_hours * 3600
        if self._active_spot_symbols and (now - self._exchange_info_time) < refresh_secs:
            return  # 캐시 유효

        spot_url = self.config.binance.spot_rest_url
        try:
            data = await self._fetch_json(f"{spot_url}/api/v3/exchangeInfo")
            if not data or isinstance(data, Exception):
                logger.warning("exchangeInfo 조회 실패 — 기존 캐시 유지")
                return

            active = set()
            for sym_info in data.get("symbols", []):
                if (sym_info.get("status") == "TRADING"
                        and sym_info.get("quoteAsset") == "USDT"):
                    active.add(sym_info.get("symbol", ""))

            self._active_spot_symbols = active
            self._exchange_info_time = now
            logger.info(f"exchangeInfo 갱신: {len(active)}개 활성 USDT 현물 페어")
        except Exception as e:
            logger.warning(f"exchangeInfo 갱신 실패: {e} — 기존 캐시 유지")

    async def scan(self) -> dict[str, CoinData]:
        """전체 USDT 퍼프 코인 스캔

        4개 API를 병렬 호출:
        1. /fapi/v1/premiumIndex -- 펀딩비, 마크가격
        2. /fapi/v1/ticker/24hr -- 24시간 통계 (선물)
        3. /api/v3/ticker/24hr  -- 현물 24시간 통계 (가격 + 거래량)
        4. /api/v3/exchangeInfo -- 활성 페어 확인 (6시간 캐시)
        """
        if not self._session or self._session.closed:
            return self._last_scan

        try:
            # exchangeInfo 캐시 갱신 (필요 시)
            await self._refresh_exchange_info()

            futures_url = self.config.binance.futures_rest_url
            spot_url = self.config.binance.spot_rest_url

            premium_task = self._fetch_json(f"{futures_url}/fapi/v1/premiumIndex")
            ticker_task = self._fetch_json(f"{futures_url}/fapi/v1/ticker/24hr")
            spot_task = self._fetch_json(f"{spot_url}/api/v3/ticker/24hr")

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

            # 현물 가격 + 거래량 맵 (ticker/24hr에서 추출)
            spot_prices: dict[str, float] = {}
            spot_volumes: dict[str, float] = {}
            if not isinstance(spot_data, Exception) and spot_data:
                for item in spot_data:
                    sym = item.get("symbol", "")
                    if sym.endswith("USDT"):
                        try:
                            spot_prices[sym] = float(item.get("lastPrice", 0))
                            spot_volumes[sym] = float(item.get("quoteVolume", 0))
                        except (KeyError, ValueError):
                            pass

            # 선물 24h 통계 맵
            ticker_map = {}
            if ticker_data:
                for item in ticker_data:
                    sym = item.get("symbol", "")
                    if sym.endswith("USDT"):
                        ticker_map[sym] = item

            # 조합 + 필터링
            now = time.time()
            result: dict[str, CoinData] = {}
            filtered_delisted = 0
            filtered_spot_volume = 0
            filtered_futures_volume = 0

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

                # 상장폐지/비활성 필터: 현물에서 TRADING 상태가 아니면 제외
                if self._active_spot_symbols and sym not in self._active_spot_symbols:
                    filtered_delisted += 1
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

                spot_quote_vol = spot_volumes.get(sym, 0.0)

                # 유동성 필터: 현물/선물 모두 저유동성이면 제외
                # (펀딩비 전략은 현물 유동성 낮아도 소액 진입 가능하므로
                #  현물 없는 파생 전용은 제외하되, 있으면 유동성 무관하게 포함)
                has_spot = spot_quote_vol > 0
                if not has_spot:
                    filtered_spot_volume += 1
                    continue

                if quote_vol < 1_000_000:
                    filtered_futures_volume += 1
                    continue

                coin = CoinData(
                    symbol=sym,
                    spot_price=spot_prices.get(sym, 0.0),
                    futures_price=futures_price,
                    funding_rate=funding_rate,
                    next_funding_time=next_funding,
                    volume_24h=volume_24h,
                    quote_volume_24h=quote_vol,
                    spot_quote_volume_24h=spot_quote_vol,
                    price_change_pct_24h=change_24h,
                    timestamp=now,
                )
                result[sym] = coin

            self._last_scan = result
            self._last_scan_time = now
            logger.info(
                f"유니버스 스캔 완료: {len(result)}개 활성 페어 "
                f"(제외: 상폐{filtered_delisted}, 현물저유동성{filtered_spot_volume}, "
                f"선물저유동성{filtered_futures_volume})"
            )
            return result

        except Exception as e:
            logger.error(f"유니버스 스캔 오류: {e}")
            return self._last_scan

    async def enrich_candidates(
        self,
        data: dict[str, CoinData],
        top_n: int = 50,
    ) -> dict[str, CoinData]:
        """상위 후보 코인에 kline 기반 기술적 지표를 추가한다.

        로테이션 시점에만 호출 (4시간마다). 50개 코인 × 2 API = 100 호출.
        Binance weight ~200으로 1200/min 한도 내에서 안전.
        """
        if not self._session or self._session.closed:
            return data

        # 기본 스코어로 사전 필터: 거래량 × |변동률|로 상위 top_n 선정
        candidates = sorted(
            data.values(),
            key=lambda c: c.quote_volume_24h * abs(c.price_change_pct_24h + 0.01),
            reverse=True,
        )[:top_n]

        if not candidates:
            return data

        # BTC 1h kline (상관도 기준선)
        btc_returns = await self._fetch_hourly_returns("BTCUSDT")

        sem = asyncio.Semaphore(10)  # 동시 10개 요청
        enriched_count = 0

        async def _enrich_one(coin: CoinData):
            nonlocal enriched_count
            async with sem:
                try:
                    await self._enrich_coin(coin, btc_returns)
                    enriched_count += 1
                except Exception as e:
                    logger.debug(f"kline 분석 실패 {coin.symbol}: {e}")

        await asyncio.gather(*[_enrich_one(c) for c in candidates])

        logger.info(f"kline 심화 분석: {enriched_count}/{len(candidates)}개 코인 완료")
        return data

    async def _enrich_coin(
        self, coin: CoinData, btc_returns: list[float]
    ):
        """단일 코인 kline 심화 분석"""
        futures_url = self.config.binance.futures_rest_url

        # 1h kline 168개 (7일) + 4h kline 42개 (7일) 동시 호출
        url_1h = f"{futures_url}/fapi/v1/klines?symbol={coin.symbol}&interval=1h&limit=168"
        url_4h = f"{futures_url}/fapi/v1/klines?symbol={coin.symbol}&interval=4h&limit=42"

        k1h, k4h = await asyncio.gather(
            self._fetch_json(url_1h),
            self._fetch_json(url_4h),
            return_exceptions=True,
        )

        if isinstance(k1h, Exception) or not k1h or len(k1h) < 20:
            return
        if isinstance(k4h, Exception) or not k4h or len(k4h) < 6:
            return

        # 1h close 가격 추출
        closes_1h = [float(k[4]) for k in k1h]
        volumes_1h = [float(k[7]) for k in k1h]  # quoteVolume

        # 4h close 가격 추출
        closes_4h = [float(k[4]) for k in k4h]

        # RSI(14)
        coin.rsi_14 = self._compute_rsi(closes_1h, 14)

        # 볼린저밴드 위치
        coin.bb_position = self._compute_bb_position(closes_1h, 20, 2.0)

        # 거래량 서지: 최근 24h / 7일 일평균
        recent_vol = sum(volumes_1h[-24:])
        avg_daily_vol = sum(volumes_1h) / 7 if len(volumes_1h) >= 168 else sum(volumes_1h) / max(1, len(volumes_1h) / 24)
        coin.volume_surge_ratio = recent_vol / avg_daily_vol if avg_daily_vol > 0 else 1.0

        # 1h 추세: 최근 종가 vs 1시간 전
        if len(closes_1h) >= 2 and closes_1h[-2] > 0:
            coin.trend_1h = (closes_1h[-1] / closes_1h[-2] - 1) * 100

        # 4h 추세: 최근 종가 vs 4시간 전
        if len(closes_4h) >= 2 and closes_4h[-2] > 0:
            coin.trend_4h = (closes_4h[-1] / closes_4h[-2] - 1) * 100

        # BTC 상관도: 최근 24h 1h 수익률
        if btc_returns and len(closes_1h) >= 25:
            coin_returns = [
                (closes_1h[i] / closes_1h[i - 1] - 1) if closes_1h[i - 1] > 0 else 0
                for i in range(len(closes_1h) - 24, len(closes_1h))
            ]
            coin.btc_correlation = self._compute_correlation(
                coin_returns, btc_returns[-len(coin_returns):]
            )

        coin.kline_enriched = True

    async def _fetch_hourly_returns(self, symbol: str = "BTCUSDT") -> list[float]:
        """BTC 1h 수익률 배열 (상관도 계산용)"""
        futures_url = self.config.binance.futures_rest_url
        url = f"{futures_url}/fapi/v1/klines?symbol={symbol}&interval=1h&limit=168"
        data = await self._fetch_json(url)
        if not data or isinstance(data, Exception) or len(data) < 25:
            return []
        closes = [float(k[4]) for k in data]
        return [
            (closes[i] / closes[i - 1] - 1) if closes[i - 1] > 0 else 0
            for i in range(1, len(closes))
        ]

    @staticmethod
    def _compute_rsi(closes: list[float], period: int = 14) -> float:
        """Wilder's RSI — 업계 표준 계산법"""
        if len(closes) < period + 1:
            return 50.0
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [max(0, d) for d in deltas]
        losses = [max(0, -d) for d in deltas]

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _compute_bb_position(
        closes: list[float], period: int = 20, std_mult: float = 2.0
    ) -> float:
        """볼린저밴드 내 현재 위치 (0.0=하단, 1.0=상단)"""
        if len(closes) < period:
            return 0.5
        window = closes[-period:]
        sma = sum(window) / period
        variance = sum((x - sma) ** 2 for x in window) / period
        std = math.sqrt(variance) if variance > 0 else 0

        if std == 0:
            return 0.5

        upper = sma + std_mult * std
        lower = sma - std_mult * std
        band_width = upper - lower
        if band_width <= 0:
            return 0.5
        return max(0.0, min(1.0, (closes[-1] - lower) / band_width))

    @staticmethod
    def _compute_correlation(a: list[float], b: list[float]) -> float:
        """Pearson 상관계수 (-1 ~ +1)"""
        n = min(len(a), len(b))
        if n < 5:
            return 0.5

        a, b = a[:n], b[:n]
        mean_a = sum(a) / n
        mean_b = sum(b) / n

        cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n))
        var_a = sum((x - mean_a) ** 2 for x in a)
        var_b = sum((x - mean_b) ** 2 for x in b)

        denom = math.sqrt(var_a * var_b)
        if denom == 0:
            return 0.0
        return max(-1.0, min(1.0, cov / denom))

    async def enrich_funding_candidates(
        self,
        data: dict[str, CoinData],
        top_n: int = 15,
        history_lookback: int = 21,
    ) -> dict[str, CoinData]:
        """펀딩비 후보 코인에 과거 펀딩비 히스토리를 추가한다.

        현재 펀딩비 상위 top_n개에 대해 /fapi/v1/fundingRate로
        과거 7일(21회) 펀딩비를 조회하여 안정성을 평가한다.
        """
        if not self._session or self._session.closed:
            return data

        # 현재 펀딩비 상위 후보 선정
        candidates = sorted(
            [c for c in data.values() if c.funding_rate > 0],
            key=lambda c: c.funding_rate,
            reverse=True,
        )[:top_n]

        if not candidates:
            return data

        sem = asyncio.Semaphore(5)  # 동시 5개 (가벼운 API)
        enriched_count = 0

        async def _enrich_one(coin: CoinData):
            nonlocal enriched_count
            async with sem:
                try:
                    await self._enrich_funding_history(coin, history_lookback)
                    enriched_count += 1
                except Exception as e:
                    logger.debug(f"펀딩 히스토리 실패 {coin.symbol}: {e}")

        await asyncio.gather(*[_enrich_one(c) for c in candidates])
        logger.info(f"펀딩 히스토리 분석: {enriched_count}/{len(candidates)}개 코인 완료")
        return data

    async def _enrich_funding_history(
        self, coin: CoinData, lookback: int = 21
    ):
        """단일 코인 과거 펀딩비 조회 + 통계 산출"""
        futures_url = self.config.binance.futures_rest_url
        url = (
            f"{futures_url}/fapi/v1/fundingRate"
            f"?symbol={coin.symbol}&limit={lookback}"
        )
        data = await self._fetch_json(url)
        if not data or isinstance(data, Exception) or len(data) < 3:
            return

        rates = [float(item.get("fundingRate", 0)) for item in data]
        coin.funding_history = rates

        # 7일 중앙값 (이상치에 강건)
        sorted_rates = sorted(rates)
        n = len(sorted_rates)
        if n % 2 == 0:
            coin.funding_avg_7d = (sorted_rates[n//2 - 1] + sorted_rates[n//2]) / 2
        else:
            coin.funding_avg_7d = sorted_rates[n//2]

        # 양수 비율
        positive_count = sum(1 for r in rates if r > 0)
        coin.funding_positive_ratio = positive_count / len(rates)

        # IQR 기반 표준편차 (이상치 제거)
        q1 = sorted_rates[n//4]
        q3 = sorted_rates[3*n//4]
        trimmed = [r for r in rates if q1 - 1.5*(q3-q1) <= r <= q3 + 1.5*(q3-q1)]
        if trimmed:
            mean_t = sum(trimmed) / len(trimmed)
            variance = sum((r - mean_t) ** 2 for r in trimmed) / len(trimmed)
            coin.funding_std = math.sqrt(variance)
        else:
            coin.funding_std = 0.0

        coin.funding_enriched = True

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
    """통합 데이터 피더: 거래소 어댑터 위임 + kline 심화 분석"""

    def __init__(self, config: AltrangConfig, adapter=None):
        self.config = config
        # adapter가 주어지면 어댑터 모드, 없으면 레거시 UniverseScanner
        self._adapter = adapter
        self.scanner = None if adapter else UniverseScanner(config)
        self._data: dict[str, CoinData] = {}
        self._running = False
        self._scan_interval = 120  # 2분마다 스캔
        self._last_scan_time: float = 0.0

    async def start(self):
        if self._adapter:
            await self._adapter.start()
        elif self.scanner:
            await self.scanner.start()
        self._running = True
        logger.info("MultiCoinFeeder 시작")

    async def stop(self):
        self._running = False
        if self._adapter:
            pass  # adapter의 close는 main에서 관리
        elif self.scanner:
            await self.scanner.close()
        logger.info("MultiCoinFeeder 정지")

    async def scan_universe(self) -> dict[str, CoinData]:
        """유니버스 스캔 실행"""
        if self._adapter:
            self._data = await self._adapter.scan_universe()
            self._last_scan_time = time.time()
        elif self.scanner:
            self._data = await self.scanner.scan()
        return self._data

    async def enrich_rotation_candidates(self, top_n: int = 50) -> dict[str, CoinData]:
        """로테이션 후보 코인에 kline 심화 분석 적용."""
        if self._adapter:
            return await self._adapter.enrich_candidates(self._data, top_n)
        elif self.scanner:
            return await self.scanner.enrich_candidates(self._data, top_n)
        return self._data

    async def enrich_funding_candidates(
        self, top_n: int = 15, history_lookback: int = 21
    ) -> dict[str, CoinData]:
        """펀딩비 후보 코인에 과거 펀딩비 히스토리 추가."""
        if self._adapter:
            return await self._adapter.enrich_funding_candidates(
                self._data, top_n, history_lookback
            )
        elif self.scanner:
            return await self.scanner.enrich_funding_candidates(
                self._data, top_n, history_lookback
            )
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
        if self._adapter:
            return time.time() - self._last_scan_time > self._scan_interval
        elif self.scanner:
            return time.time() - self.scanner.last_scan_time > self._scan_interval
        return False
