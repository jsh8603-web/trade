"""AltRang Exchange Base -- 거래소 어댑터 추상 인터페이스"""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from altrang.data_feeder import CoinData
from altrang.execution import OrderResult, HedgedResult


class ExchangeAdapter(ABC):
    """거래소 어댑터 추상 클래스

    Binance / Upbit 공통 인터페이스 정의.
    rotation_engine, funding_engine은 이 인터페이스만 사용한다.
    """

    @abstractmethod
    async def start(self): ...

    @abstractmethod
    async def close(self): ...

    # ─── 유니버스 스캔 ───
    @abstractmethod
    async def scan_universe(self) -> dict[str, CoinData]: ...

    @abstractmethod
    async def enrich_candidates(
        self, data: dict[str, CoinData], top_n: int,
    ) -> dict[str, CoinData]: ...

    # ─── 현물 매매 ───
    @abstractmethod
    async def spot_buy(self, symbol: str, quote_amount: float, price: float) -> OrderResult: ...

    @abstractmethod
    async def spot_sell(self, symbol: str, qty: float) -> OrderResult: ...

    # ─── 잔고 조회 ───
    @abstractmethod
    async def get_spot_balances(self) -> dict[str, float]: ...

    # ─── 펀딩비 (Binance 전용, 기본 no-op) ───
    async def enrich_funding_candidates(
        self, data: dict[str, CoinData], top_n: int = 15, history_lookback: int = 21,
    ) -> dict[str, CoinData]:
        return data

    async def enter_hedged(self, symbol, usdt_amount, spot_price, futures_price) -> HedgedResult:
        return HedgedResult()

    async def exit_hedged(self, symbol, spot_qty, futures_qty) -> HedgedResult:
        return HedgedResult()

    async def ensure_bnb_reserve(self) -> bool:
        return True

    async def get_futures_positions(self) -> dict:
        return {}

    async def set_leverage(self, symbol: str, leverage: int = 1) -> bool:
        return True

    # ─── 공용 기술적 지표 유틸리티 ───

    @staticmethod
    def compute_rsi(closes: list[float], period: int = 14) -> float:
        """Wilder's RSI"""
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
    def compute_bb_position(
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
    def compute_correlation(a: list[float], b: list[float]) -> float:
        """Pearson 상관계수"""
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
