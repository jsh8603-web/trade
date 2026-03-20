"""AltRang Upbit Adapter -- 업비트 현물 거래소 어댑터

업비트 REST API로 알트코인 유니버스 스캔 + 현물 매매를 수행한다.
선물/펀딩비 기능은 없음 (현물 전용).
"""

import asyncio
import hashlib
import logging
import time
import uuid
from typing import Optional
from urllib.parse import urlencode

import aiohttp

from altrang.config import AltrangConfig
from altrang.data_feeder import CoinData
from altrang.execution import OrderResult, HedgedResult
from altrang.exchange_base import ExchangeAdapter

logger = logging.getLogger("altrang.upbit")

UPBIT_API = "https://api.upbit.com/v1"

# 업비트 블랙리스트: 스테이블/래핑 등 제외
UPBIT_BLACKLIST = {
    "KRW-USDT", "KRW-USDC", "KRW-DAI",
}


class UpbitAdapter(ExchangeAdapter):
    """업비트 현물 거래소 어댑터"""

    def __init__(self, config: AltrangConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._access_key = config.upbit.access_key
        self._secret_key = config.upbit.secret_key

    async def start(self):
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        logger.info("Upbit 어댑터 시작")

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ─── 인증 ───

    def _auth_header(self, query: dict = None) -> dict:
        """JWT 인증 헤더 생성"""
        try:
            import jwt as pyjwt
        except ImportError:
            import jwt as pyjwt

        payload = {
            "access_key": self._access_key,
            "nonce": str(uuid.uuid4()),
        }
        if query:
            query_string = urlencode(query)
            query_hash = hashlib.sha512(query_string.encode()).hexdigest()
            payload["query_hash"] = query_hash
            payload["query_hash_alg"] = "SHA512"

        token = pyjwt.encode(payload, self._secret_key, algorithm="HS256")
        return {"Authorization": f"Bearer {token}"}

    # ─── 유니버스 스캔 ───

    async def scan_universe(self) -> dict[str, CoinData]:
        """업비트 KRW 마켓 전체 스캔

        1. /v1/market/all — KRW 마켓 목록
        2. /v1/ticker — 가격, 24h 거래량/변동률 (최대 100개씩 배치)
        """
        if not self._session or self._session.closed:
            return {}

        try:
            # 1. 마켓 목록
            markets_data = await self._fetch_json(f"{UPBIT_API}/market/all?isDetails=false")
            if not markets_data:
                return {}

            krw_markets = [
                m["market"] for m in markets_data
                if m["market"].startswith("KRW-") and m["market"] not in UPBIT_BLACKLIST
            ]

            if not krw_markets:
                return {}

            # 2. 티커 (100개씩 배치)
            result: dict[str, CoinData] = {}
            now = time.time()

            for i in range(0, len(krw_markets), 100):
                batch = krw_markets[i:i+100]
                markets_str = ",".join(batch)
                ticker_data = await self._fetch_json(
                    f"{UPBIT_API}/ticker?markets={markets_str}"
                )
                if not ticker_data:
                    continue

                for item in ticker_data:
                    market = item.get("market", "")
                    try:
                        trade_price = float(item.get("trade_price", 0))
                        acc_trade_price_24h = float(item.get("acc_trade_price_24h", 0))
                        signed_change_rate = float(item.get("signed_change_rate", 0))
                    except (ValueError, TypeError):
                        continue

                    if trade_price <= 0:
                        continue

                    # 최소 거래대금 필터 (1억원 ≈ ~$70K)
                    if acc_trade_price_24h < 100_000_000:
                        continue

                    coin = CoinData(
                        symbol=market,
                        spot_price=trade_price,
                        quote_volume_24h=acc_trade_price_24h,
                        spot_quote_volume_24h=acc_trade_price_24h,
                        price_change_pct_24h=signed_change_rate * 100,
                        timestamp=now,
                    )
                    result[market] = coin

            logger.info(f"업비트 유니버스 스캔: {len(result)}개 KRW 마켓")
            return result

        except Exception as e:
            logger.error(f"업비트 유니버스 스캔 오류: {e}")
            return {}

    async def enrich_candidates(
        self, data: dict[str, CoinData], top_n: int = 50,
    ) -> dict[str, CoinData]:
        """상위 후보에 kline 기술적 지표 추가

        업비트 캔들 API: /v1/candles/minutes/{unit}?market=X&count=N
        """
        if not self._session or self._session.closed:
            return data

        candidates = sorted(
            data.values(),
            key=lambda c: c.quote_volume_24h * abs(c.price_change_pct_24h + 0.01),
            reverse=True,
        )[:top_n]

        if not candidates:
            return data

        # BTC 1h 수익률 (상관도 기준선)
        btc_returns = await self._fetch_hourly_returns("KRW-BTC")

        sem = asyncio.Semaphore(5)  # 업비트 rate limit: 10 req/sec
        enriched_count = 0

        async def _enrich_one(coin: CoinData):
            nonlocal enriched_count
            async with sem:
                try:
                    await self._enrich_coin(coin, btc_returns)
                    enriched_count += 1
                except Exception as e:
                    logger.debug(f"kline 분석 실패 {coin.symbol}: {e}")
                await asyncio.sleep(0.15)  # rate limit 보호

        await asyncio.gather(*[_enrich_one(c) for c in candidates])
        logger.info(f"업비트 kline 심화 분석: {enriched_count}/{len(candidates)}개 완료")
        return data

    async def _enrich_coin(self, coin: CoinData, btc_returns: list[float]):
        """단일 코인 kline 심화 분석"""
        # 1h 168개 (7일) + 4h 42개 동시 호출
        url_1h = f"{UPBIT_API}/candles/minutes/60?market={coin.symbol}&count=168"
        url_4h = f"{UPBIT_API}/candles/minutes/240?market={coin.symbol}&count=42"

        k1h, k4h = await asyncio.gather(
            self._fetch_json(url_1h),
            self._fetch_json(url_4h),
            return_exceptions=True,
        )

        if isinstance(k1h, Exception) or not k1h or len(k1h) < 20:
            return
        if isinstance(k4h, Exception) or not k4h or len(k4h) < 6:
            return

        # 업비트 캔들은 최신이 먼저 → 역순
        k1h.reverse()
        k4h.reverse()

        closes_1h = [float(k["trade_price"]) for k in k1h]
        volumes_1h = [float(k["candle_acc_trade_price"]) for k in k1h]
        closes_4h = [float(k["trade_price"]) for k in k4h]

        # RSI(14)
        coin.rsi_14 = self.compute_rsi(closes_1h, 14)

        # 볼린저밴드 위치
        coin.bb_position = self.compute_bb_position(closes_1h, 20, 2.0)

        # 거래량 서지
        recent_vol = sum(volumes_1h[-24:])
        avg_daily_vol = sum(volumes_1h) / 7 if len(volumes_1h) >= 168 else sum(volumes_1h) / max(1, len(volumes_1h) / 24)
        coin.volume_surge_ratio = recent_vol / avg_daily_vol if avg_daily_vol > 0 else 1.0

        # 1h/4h 추세
        if len(closes_1h) >= 2 and closes_1h[-2] > 0:
            coin.trend_1h = (closes_1h[-1] / closes_1h[-2] - 1) * 100
        if len(closes_4h) >= 2 and closes_4h[-2] > 0:
            coin.trend_4h = (closes_4h[-1] / closes_4h[-2] - 1) * 100

        # BTC 상관도
        if btc_returns and len(closes_1h) >= 25:
            coin_returns = [
                (closes_1h[i] / closes_1h[i-1] - 1) if closes_1h[i-1] > 0 else 0
                for i in range(len(closes_1h) - 24, len(closes_1h))
            ]
            coin.btc_correlation = self.compute_correlation(
                coin_returns, btc_returns[-len(coin_returns):]
            )

        coin.kline_enriched = True

    async def _fetch_hourly_returns(self, symbol: str = "KRW-BTC") -> list[float]:
        """1h 수익률 배열 (상관도 계산용)"""
        url = f"{UPBIT_API}/candles/minutes/60?market={symbol}&count=168"
        data = await self._fetch_json(url)
        if not data or isinstance(data, Exception) or len(data) < 25:
            return []
        data.reverse()  # 시간순
        closes = [float(k["trade_price"]) for k in data]
        return [
            (closes[i] / closes[i-1] - 1) if closes[i-1] > 0 else 0
            for i in range(1, len(closes))
        ]

    # ─── 현물 매매 ───

    async def spot_buy(self, symbol: str, quote_amount: float, price: float) -> OrderResult:
        """현물 매수 (KRW 금액 지정)"""
        result = OrderResult(exchange="spot", symbol=symbol, side="BUY")

        if self.config.safety.dry_run:
            qty = quote_amount / price if price > 0 else 0
            result.success = True
            result.order_id = f"DRY_{int(time.time()*1000)}"
            result.filled_price = price
            result.filled_qty = qty
            return result

        params = {
            "market": symbol,
            "side": "bid",
            "ord_type": "price",  # 시장가 매수 (총액 지정)
            "price": str(int(quote_amount)),
        }

        try:
            async with self._session.post(
                f"{UPBIT_API}/orders",
                json=params,
                headers=self._auth_header(params),
            ) as resp:
                data = await resp.json()
                if resp.status in (200, 201):
                    result.success = True
                    result.order_id = data.get("uuid", "")
                    # 체결 조회 (비동기 체결이므로 잠시 대기)
                    await asyncio.sleep(1.0)
                    filled = await self._get_order(result.order_id)
                    if filled:
                        result.filled_price = filled.get("avg_price", price)
                        result.filled_qty = filled.get("executed_volume", 0)
                else:
                    result.error = f"HTTP {resp.status}: {data.get('error', {}).get('message', str(data)[:200])}"
                    logger.error(f"업비트 매수 실패: {result.error}")
        except Exception as e:
            result.error = str(e)
            logger.error(f"업비트 매수 오류: {e}")

        return result

    async def spot_sell(self, symbol: str, qty: float) -> OrderResult:
        """현물 매도 (수량 지정)"""
        result = OrderResult(exchange="spot", symbol=symbol, side="SELL")

        if self.config.safety.dry_run:
            result.success = True
            result.order_id = f"DRY_{int(time.time()*1000)}"
            result.filled_qty = qty
            return result

        params = {
            "market": symbol,
            "side": "ask",
            "ord_type": "market",  # 시장가 매도
            "volume": f"{qty:.8f}",
        }

        try:
            async with self._session.post(
                f"{UPBIT_API}/orders",
                json=params,
                headers=self._auth_header(params),
            ) as resp:
                data = await resp.json()
                if resp.status in (200, 201):
                    result.success = True
                    result.order_id = data.get("uuid", "")
                    await asyncio.sleep(1.0)
                    filled = await self._get_order(result.order_id)
                    if filled:
                        result.filled_price = filled.get("avg_price", 0)
                        result.filled_qty = filled.get("executed_volume", qty)
                else:
                    result.error = f"HTTP {resp.status}: {data.get('error', {}).get('message', str(data)[:200])}"
                    logger.error(f"업비트 매도 실패: {result.error}")
        except Exception as e:
            result.error = str(e)
            logger.error(f"업비트 매도 오류: {e}")

        return result

    # ─── 잔고 조회 ───

    async def get_spot_balances(self) -> dict[str, float]:
        """업비트 잔고 조회"""
        if self.config.safety.dry_run:
            return {"KRW": 5_000_000.0}

        try:
            async with self._session.get(
                f"{UPBIT_API}/accounts",
                headers=self._auth_header(),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    balances = {}
                    for item in data:
                        currency = item.get("currency", "")
                        balance = float(item.get("balance", 0))
                        if balance > 0:
                            balances[currency] = balance
                    return balances
        except Exception as e:
            logger.error(f"업비트 잔고 조회 오류: {e}")
        return {}

    # ─── 내부 헬퍼 ───

    async def _get_order(self, order_id: str) -> dict:
        """주문 상세 조회 (체결 확인)"""
        params = {"uuid": order_id}
        try:
            async with self._session.get(
                f"{UPBIT_API}/order",
                params=params,
                headers=self._auth_header(params),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # 평균 체결가 계산
                    trades = data.get("trades", [])
                    if trades:
                        total_funds = sum(float(t.get("funds", 0)) for t in trades)
                        total_vol = sum(float(t.get("volume", 0)) for t in trades)
                        avg_price = total_funds / total_vol if total_vol > 0 else 0
                    else:
                        avg_price = float(data.get("price", 0))
                        total_vol = float(data.get("executed_volume", 0))
                    return {
                        "avg_price": avg_price,
                        "executed_volume": total_vol,
                        "state": data.get("state", ""),
                    }
        except Exception as e:
            logger.warning(f"주문 조회 실패: {e}")
        return {}

    async def _fetch_json(self, url: str):
        """GET 요청 + JSON 파싱"""
        try:
            async with self._session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                if resp.status == 429:
                    logger.warning(f"업비트 rate limit: {url}")
                    await asyncio.sleep(1.0)
                else:
                    logger.warning(f"업비트 API {resp.status}: {url}")
                return None
        except Exception as e:
            logger.warning(f"업비트 API 오류: {e}")
            return None
