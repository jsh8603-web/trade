"""SeonbiRang Funding Engine -- 펀딩비 수확 (델타뉴트럴)

전략:
  1. 펀딩비 양수 코인 → Spot Buy + Futures Short (수수료 수령)
  2. 매 8시간 펀딩비 자동 지급 (00:00, 08:00, 16:00 UTC)
  3. 펀딩비 하락 시 청산, 더 좋은 코인으로 교체
"""

import logging
import time

from seonbirang.config import SeonbirangConfig
from seonbirang.coin_selector import CoinSelector, CoinScore
from seonbirang.data_feeder import MultiCoinFeeder
from seonbirang.execution import BinanceExecutor
from seonbirang.risk_manager import RiskManager
from seonbirang.state import BotState, CoinPosition, save_state

logger = logging.getLogger("seonbirang.funding")


class FundingEngine:
    """펀딩비 수확 엔진"""

    def __init__(
        self,
        config: SeonbirangConfig,
        state: BotState,
        feeder: MultiCoinFeeder,
        executor: BinanceExecutor,
        selector: CoinSelector,
        risk: RiskManager,
    ):
        self.config = config
        self.state = state
        self.feeder = feeder
        self.executor = executor
        self.selector = selector
        self.risk = risk

    async def tick(self) -> list[dict]:
        """주기적 체크 (1분마다 호출)

        Returns:
            실행된 액션 리스트 [{action, symbol, result, ...}]
        """
        actions = []
        now = time.time()

        # 리밸런스 간격 체크
        elapsed = now - self.state.last_funding_rebalance
        if elapsed < self.config.funding.rebalance_interval_min * 60:
            # 리밸런스 시간 아님 → 기존 포지션 모니터링만
            actions.extend(await self._check_exits())
            return actions

        self.state.last_funding_rebalance = now

        # 1. 청산 대상 체크
        actions.extend(await self._check_exits())

        # 2. 신규 진입 체크
        actions.extend(await self._check_entries())

        return actions

    async def _check_exits(self) -> list[dict]:
        """기존 포지션 청산 조건 체크"""
        actions = []
        positions = self.state.get_strategy_positions("funding")
        data = self.feeder.get_all()

        for pos in positions:
            coin = data.get(pos.symbol)
            if not coin:
                continue

            should_exit = False
            reason = ""

            # 펀딩비 하락
            if coin.funding_rate < self.config.funding.exit_funding_threshold:
                should_exit = True
                reason = f"펀딩비 하락: {coin.funding_rate*100:.4f}%"

            # 최소 보유 시간 체크
            held_hours = (time.time() - pos.entry_time) / 3600
            if should_exit and held_hours < self.config.funding.min_hold_hours:
                logger.info(
                    f"{pos.symbol} 청산 조건이나 최소 보유 {self.config.funding.min_hold_hours}h 미달 "
                    f"({held_hours:.1f}h) -- 유지"
                )
                continue

            if should_exit:
                logger.info(f"펀딩 청산: {pos.symbol} ({reason})")
                result = await self.executor.exit_hedged(
                    pos.symbol, pos.spot_qty, pos.futures_qty
                )
                if result.both_success:
                    self.state.remove_position(pos.symbol)
                    self.state.trade_count_today += 1
                    save_state(self.state)
                    actions.append({
                        "action": "exit",
                        "strategy": "funding",
                        "symbol": pos.symbol,
                        "reason": reason,
                        "success": True,
                    })
                else:
                    actions.append({
                        "action": "exit",
                        "strategy": "funding",
                        "symbol": pos.symbol,
                        "reason": reason,
                        "success": False,
                        "error": "편측 체결",
                    })

        return actions

    async def _check_entries(self) -> list[dict]:
        """신규 진입 대상 탐색"""
        actions = []
        data = self.feeder.get_all()
        ranked = self.selector.rank_by_funding(data)

        if not ranked:
            logger.info("펀딩 진입 대상 없음")
            return actions

        current_symbols = {
            p.symbol for p in self.state.get_strategy_positions("funding")
        }

        # 빈 슬롯 수
        available_slots = self.config.funding.max_coins - len(current_symbols)
        if available_slots <= 0:
            return actions

        entered = 0
        for coin_score in ranked:
            if entered >= available_slots:
                break
            if coin_score.symbol in current_symbols:
                continue

            # 리스크 체크
            size = self.config.funding.position_size_usdt
            ok, reason = self.risk.check_entry("funding", coin_score.symbol, size)
            if not ok:
                logger.info(f"펀딩 진입 거부: {coin_score.symbol} ({reason})")
                continue

            coin = data[coin_score.symbol]
            logger.info(
                f"펀딩 진입 시도: {coin_score.symbol} "
                f"FR={coin.funding_rate*100:.4f}% "
                f"${size:.0f}"
            )

            result = await self.executor.enter_hedged(
                coin_score.symbol, size, coin.spot_price, coin.futures_price
            )

            if result.both_success:
                pos = CoinPosition(
                    symbol=coin_score.symbol,
                    strategy="funding",
                    side="hedged",
                    spot_qty=result.spot_leg.filled_qty,
                    futures_qty=result.futures_leg.filled_qty,
                    entry_price=result.spot_leg.filled_price or coin.spot_price,
                    entry_time=time.time(),
                )
                self.state.set_position(pos)
                self.state.trade_count_today += 1
                self.state.last_trade_time = time.time()
                save_state(self.state)
                entered += 1
                actions.append({
                    "action": "enter",
                    "strategy": "funding",
                    "symbol": coin_score.symbol,
                    "funding_rate": coin.funding_rate,
                    "size_usdt": size,
                    "success": True,
                })
            else:
                actions.append({
                    "action": "enter",
                    "strategy": "funding",
                    "symbol": coin_score.symbol,
                    "success": False,
                    "error": "주문 실패",
                })

        if entered > 0:
            logger.info(f"펀딩 신규 진입 {entered}개 코인")

        return actions

    def get_summary(self) -> dict:
        """펀딩 전략 현황 요약"""
        positions = self.state.get_strategy_positions("funding")
        data = self.feeder.get_all()

        pos_details = []
        for pos in positions:
            coin = data.get(pos.symbol)
            current_rate = coin.funding_rate if coin else 0
            held_hours = (time.time() - pos.entry_time) / 3600
            pos_details.append({
                "symbol": pos.symbol,
                "qty": pos.spot_qty,
                "entry_price": pos.entry_price,
                "current_funding_rate": current_rate,
                "funding_collected": pos.funding_collected,
                "held_hours": round(held_hours, 1),
            })

        return {
            "strategy": "funding",
            "position_count": len(positions),
            "total_invested": self.state.total_invested("funding"),
            "total_funding_collected": self.state.total_funding_collected,
            "positions": pos_details,
        }
