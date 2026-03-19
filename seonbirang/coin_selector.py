"""SeonbiRang Coin Selector -- 코인 순위 산정 + 진입/청산 대상 선별"""

import logging
from dataclasses import dataclass
from typing import Optional

from seonbirang.config import SeonbirangConfig, COIN_BLACKLIST
from seonbirang.data_feeder import CoinData

logger = logging.getLogger("seonbirang.selector")


@dataclass
class CoinScore:
    """코인 평가 점수"""
    symbol: str
    score: float
    funding_rate: float = 0.0
    momentum_score: float = 0.0
    volume_24h: float = 0.0
    reason: str = ""


class CoinSelector:
    """코인 스크리닝 및 순위 산정"""

    def __init__(self, config: SeonbirangConfig):
        self.config = config

    def rank_by_funding(self, data: dict[str, CoinData]) -> list[CoinScore]:
        """펀딩비 기준 순위 (높은 양수 펀딩 = 수확 대상)

        필터:
        - 펀딩비 > min_funding_rate
        - 24h 거래량 > min_volume
        - 블랙리스트 제외
        - 현물 가격 존재 (델타뉴트럴에 현물 필요)
        """
        min_rate = self.config.funding.min_funding_rate
        min_vol = self.config.rotation.min_volume_usdt_24h
        scores = []

        for sym, coin in data.items():
            if sym in COIN_BLACKLIST:
                continue
            if coin.funding_rate < min_rate:
                continue
            if coin.quote_volume_24h < min_vol:
                continue
            if coin.spot_price <= 0:
                continue

            # 점수: 펀딩비 × 유동성 가중치
            vol_weight = min(1.0, coin.quote_volume_24h / 100_000_000)
            score = coin.funding_rate * 10000 * (0.7 + 0.3 * vol_weight)

            scores.append(CoinScore(
                symbol=sym,
                score=score,
                funding_rate=coin.funding_rate,
                volume_24h=coin.quote_volume_24h,
                reason=f"FR={coin.funding_rate*100:.4f}% vol=${coin.quote_volume_24h/1e6:.0f}M",
            ))

        scores.sort(key=lambda x: x.score, reverse=True)
        return scores[:self.config.funding.max_coins * 2]  # 2배수 후보

    def rank_by_momentum(self, data: dict[str, CoinData]) -> list[CoinScore]:
        """모멘텀 기준 순위 (상대 강도)

        점수 = 0.5 * 24h변동 + 0.3 * 거래량서지 + 0.2 * 추세일관성
        """
        min_vol = self.config.rotation.min_volume_usdt_24h
        scores = []

        for sym, coin in data.items():
            if sym in COIN_BLACKLIST:
                continue
            if coin.quote_volume_24h < min_vol:
                continue
            if coin.spot_price <= 0:
                continue

            # 24h 가격 변동 (핵심 팩터)
            change_score = coin.price_change_pct_24h

            # 거래량 서지 (높은 거래량 = 관심 증가)
            vol_score = min(2.0, coin.quote_volume_24h / 500_000_000) * 10

            # 종합 모멘텀 점수
            momentum = change_score * 0.7 + vol_score * 0.3

            scores.append(CoinScore(
                symbol=sym,
                score=momentum,
                momentum_score=momentum,
                funding_rate=coin.funding_rate,
                volume_24h=coin.quote_volume_24h,
                reason=f"24h={coin.price_change_pct_24h:+.1f}% vol=${coin.quote_volume_24h/1e6:.0f}M",
            ))

        scores.sort(key=lambda x: x.score, reverse=True)
        return scores[:self.config.rotation.universe_size]

    def select_funding_targets(
        self,
        current_symbols: set[str],
        ranked: list[CoinScore],
        max_new: int = 3,
    ) -> tuple[list[CoinScore], list[str]]:
        """펀딩 전략 진입/청산 대상 결정

        Returns:
            (enter_list, exit_symbols)
        """
        # 진입: 아직 미보유 + 상위 순위
        enter = []
        for coin in ranked:
            if coin.symbol not in current_symbols and len(enter) < max_new:
                enter.append(coin)

        # 청산: 현재 보유 중인데 순위에서 밀린 코인
        ranked_symbols = {c.symbol for c in ranked}
        exit_syms = [s for s in current_symbols if s not in ranked_symbols]

        return enter, exit_syms

    def select_rotation_targets(
        self,
        current_symbols: set[str],
        ranked: list[CoinScore],
        max_replace: int = 2,
    ) -> tuple[list[CoinScore], list[str]]:
        """로테이션 전략 진입/청산 대상 결정

        Returns:
            (enter_list, exit_symbols)
        """
        top_n = self.config.rotation.top_n
        top_symbols = {c.symbol for c in ranked[:top_n]}

        # 청산: top_n에서 밀린 코인 (최대 max_replace개)
        exit_syms = [s for s in current_symbols if s not in top_symbols]
        exit_syms = exit_syms[:max_replace]

        # 진입: top_n에 새로 진입한 코인 (청산 수만큼)
        enter = []
        for coin in ranked[:top_n]:
            if coin.symbol not in current_symbols and len(enter) < len(exit_syms):
                enter.append(coin)

        # 빈 슬롯이 있으면 추가 진입
        remaining_slots = top_n - len(current_symbols) + len(exit_syms) - len(enter)
        if remaining_slots > 0:
            for coin in ranked[:top_n]:
                if coin.symbol not in current_symbols and coin not in enter:
                    enter.append(coin)
                    remaining_slots -= 1
                    if remaining_slots <= 0:
                        break

        return enter, exit_syms
