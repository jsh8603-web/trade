"""AltRang Risk Manager -- 중앙 리스크 관리"""

import logging
import time

from altrang.config import AltrangConfig
from altrang.state import BotState

logger = logging.getLogger("altrang.risk")


class RiskManager:
    """양 전략 통합 리스크 관리"""

    def __init__(self, config: AltrangConfig, state: BotState):
        self.config = config
        self.state = state

    def check_entry(
        self, strategy: str, symbol: str, size_usdt: float,
        total_balance_usdt: float = 0,
    ) -> tuple[bool, str]:
        """진입 전 리스크 체크

        Returns:
            (허용 여부, 사유)
        """
        # 1. 긴급 정지
        if self.config.safety.emergency_stop:
            return False, "EMERGENCY_STOP 활성화"

        # 2. 일일 거래 횟수
        self.state.check_daily_reset()
        if self.state.trade_count_today >= self.config.safety.max_daily_trades:
            return False, f"일일 거래 한도 초과 ({self.config.safety.max_daily_trades})"

        # 3. 전략별 포지션 수 제한
        if strategy == "funding":
            current = self.state.funding_count()
            max_coins = self.config.funding.max_coins
            if current >= max_coins:
                return False, f"펀딩 포지션 한도 ({current}/{max_coins})"
            invested = self.state.total_invested("funding")
            if invested + size_usdt > self.config.funding.max_total_usdt:
                return False, f"펀딩 예산 초과 (${invested:.0f}+${size_usdt:.0f} > ${self.config.funding.max_total_usdt:.0f})"

        elif strategy == "rotation":
            current = self.state.rotation_count()
            max_coins = self.config.rotation.top_n
            if current >= max_coins:
                return False, f"로테이션 포지션 한도 ({current}/{max_coins})"
            invested = self.state.total_invested("rotation")
            if invested + size_usdt > self.config.rotation.max_total_usdt:
                return False, f"로테이션 예산 초과"

        # 4. 총 포지션 비율
        if total_balance_usdt > 0:
            total_invested = (
                self.state.total_invested("funding")
                + self.state.total_invested("rotation")
                + size_usdt
            )
            ratio = total_invested / total_balance_usdt
            if ratio > self.config.safety.max_position_ratio:
                return False, f"총 포지션 비율 초과 ({ratio:.0%} > {self.config.safety.max_position_ratio:.0%})"

        # 5. 중복 진입 방지
        if self.state.get_position(symbol):
            return False, f"{symbol} 이미 보유 중"

        return True, "OK"

    def check_portfolio_health(self) -> dict:
        """포트폴리오 전체 건강 상태"""
        funding_pos = self.state.get_strategy_positions("funding")
        rotation_pos = self.state.get_strategy_positions("rotation")

        total_unrealized = sum(p.unrealized_pnl for p in funding_pos + rotation_pos)
        total_invested = (
            self.state.total_invested("funding")
            + self.state.total_invested("rotation")
        )
        drawdown_pct = (total_unrealized / total_invested * 100) if total_invested > 0 else 0

        return {
            "funding_count": len(funding_pos),
            "rotation_count": len(rotation_pos),
            "total_invested": total_invested,
            "total_unrealized_pnl": total_unrealized,
            "drawdown_pct": drawdown_pct,
            "total_funding_collected": self.state.total_funding_collected,
            "trades_today": self.state.trade_count_today,
            "emergency_stop": self.config.safety.emergency_stop,
            "should_reduce": drawdown_pct < -self.config.safety.portfolio_drawdown_pct,
        }
