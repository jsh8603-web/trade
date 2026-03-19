"""SeonbiRang Rotation Engine -- 알트코인 모멘텀 로테이션

전략:
  1. 24h 모멘텀 상위 N개 코인을 현물 보유
  2. 주기적으로 순위 변동 시 교체 (약한 코인 매도 → 강한 코인 매수)
  3. 개별 코인 손절/익절 자동 관리
"""

import logging
import time

from seonbirang.config import SeonbirangConfig
from seonbirang.coin_selector import CoinSelector
from seonbirang.data_feeder import MultiCoinFeeder
from seonbirang.execution import BinanceExecutor
from seonbirang.risk_manager import RiskManager
from seonbirang.state import BotState, CoinPosition, save_state

logger = logging.getLogger("seonbirang.rotation")


class RotationEngine:
    """알트코인 모멘텀 로테이션 엔진"""

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
        """주기적 체크

        빠른 체크 (매분): 손절/익절
        느린 체크 (rotation_interval): 로테이션
        """
        actions = []

        # 1. 손절/익절 체크 (항상)
        actions.extend(await self._check_stop_loss_take_profit())

        # 2. 로테이션 체크 (주기적)
        now = time.time()
        elapsed = now - self.state.last_rotation_check
        if elapsed >= self.config.rotation.rotation_interval_min * 60:
            self.state.last_rotation_check = now
            actions.extend(await self._do_rotation())

        return actions

    async def _check_stop_loss_take_profit(self) -> list[dict]:
        """개별 코인 손절/익절"""
        actions = []
        positions = self.state.get_strategy_positions("rotation")
        data = self.feeder.get_all()

        for pos in positions:
            coin = data.get(pos.symbol)
            if not coin or coin.spot_price <= 0 or pos.entry_price <= 0:
                continue

            pnl_pct = (coin.spot_price - pos.entry_price) / pos.entry_price * 100
            action = None
            reason = ""

            # 손절
            if pnl_pct <= -self.config.rotation.stop_loss_pct:
                action = "stop_loss"
                reason = f"손절: {pnl_pct:+.1f}% (한도 -{self.config.rotation.stop_loss_pct}%)"

            # 익절
            elif pnl_pct >= self.config.rotation.take_profit_pct:
                action = "take_profit"
                reason = f"익절: {pnl_pct:+.1f}% (목표 +{self.config.rotation.take_profit_pct}%)"

            if action:
                logger.info(f"로테이션 {action}: {pos.symbol} ({reason})")
                result = await self.executor.spot_sell(pos.symbol, pos.spot_qty)
                if result.success:
                    pnl_usdt = (coin.spot_price - pos.entry_price) * pos.spot_qty
                    self.state.remove_position(pos.symbol)
                    self.state.trade_count_today += 1
                    save_state(self.state)
                    actions.append({
                        "action": action,
                        "strategy": "rotation",
                        "symbol": pos.symbol,
                        "reason": reason,
                        "pnl_pct": round(pnl_pct, 2),
                        "pnl_usdt": round(pnl_usdt, 2),
                        "success": True,
                    })
                else:
                    actions.append({
                        "action": action,
                        "strategy": "rotation",
                        "symbol": pos.symbol,
                        "success": False,
                        "error": result.error,
                    })

        return actions

    async def _do_rotation(self) -> list[dict]:
        """모멘텀 기반 로테이션 실행"""
        actions = []
        data = self.feeder.get_all()
        ranked = self.selector.rank_by_momentum(data)

        if not ranked:
            logger.info("로테이션 대상 없음")
            return actions

        current_symbols = {
            p.symbol for p in self.state.get_strategy_positions("rotation")
        }

        # 최소 보유 시간 체크 (너무 빨리 교체 방지)
        protected = set()
        for pos in self.state.get_strategy_positions("rotation"):
            held_hours = (time.time() - pos.entry_time) / 3600
            if held_hours < self.config.rotation.min_hold_hours:
                protected.add(pos.symbol)

        # 교체 대상 선별
        enter_list, exit_symbols = self.selector.select_rotation_targets(
            current_symbols,
            ranked,
            max_replace=self.config.rotation.max_replace_per_cycle,
        )

        # 보호 기간 코인 제외
        exit_symbols = [s for s in exit_symbols if s not in protected]

        # 먼저 매도 (자금 확보)
        for sym in exit_symbols:
            pos = self.state.get_position(sym)
            if not pos:
                continue

            coin = data.get(sym)
            price = coin.spot_price if coin else pos.entry_price
            pnl_pct = (price - pos.entry_price) / pos.entry_price * 100 if pos.entry_price > 0 else 0

            logger.info(f"로테이션 매도: {sym} (순위 하락, PnL={pnl_pct:+.1f}%)")
            result = await self.executor.spot_sell(sym, pos.spot_qty)
            if result.success:
                pnl_usdt = (price - pos.entry_price) * pos.spot_qty
                self.state.remove_position(sym)
                self.state.trade_count_today += 1
                save_state(self.state)
                actions.append({
                    "action": "rotation_sell",
                    "strategy": "rotation",
                    "symbol": sym,
                    "pnl_pct": round(pnl_pct, 2),
                    "pnl_usdt": round(pnl_usdt, 2),
                    "success": True,
                })

        # 매수
        for coin_score in enter_list:
            size = self.config.rotation.position_size_usdt
            ok, reason = self.risk.check_entry("rotation", coin_score.symbol, size)
            if not ok:
                logger.info(f"로테이션 매수 거부: {coin_score.symbol} ({reason})")
                continue

            coin = data.get(coin_score.symbol)
            if not coin or coin.spot_price <= 0:
                continue

            logger.info(
                f"로테이션 매수: {coin_score.symbol} "
                f"score={coin_score.score:.1f} "
                f"24h={coin.price_change_pct_24h:+.1f}% "
                f"${size:.0f}"
            )

            result = await self.executor.spot_buy(
                coin_score.symbol, size, coin.spot_price
            )
            if result.success:
                entry_price = result.filled_price or coin.spot_price
                pos = CoinPosition(
                    symbol=coin_score.symbol,
                    strategy="rotation",
                    side="long",
                    spot_qty=result.filled_qty,
                    entry_price=entry_price,
                    entry_time=time.time(),
                    stop_loss_price=entry_price * (1 - self.config.rotation.stop_loss_pct / 100),
                    take_profit_price=entry_price * (1 + self.config.rotation.take_profit_pct / 100),
                )
                self.state.set_position(pos)
                self.state.trade_count_today += 1
                self.state.last_trade_time = time.time()
                save_state(self.state)
                actions.append({
                    "action": "rotation_buy",
                    "strategy": "rotation",
                    "symbol": coin_score.symbol,
                    "momentum_score": coin_score.score,
                    "size_usdt": size,
                    "success": True,
                })

        return actions

    def get_summary(self) -> dict:
        """로테이션 전략 현황 요약"""
        positions = self.state.get_strategy_positions("rotation")
        data = self.feeder.get_all()

        pos_details = []
        total_pnl = 0
        for pos in positions:
            coin = data.get(pos.symbol)
            current_price = coin.spot_price if coin else pos.entry_price
            pnl_pct = (current_price - pos.entry_price) / pos.entry_price * 100 if pos.entry_price > 0 else 0
            pnl_usdt = (current_price - pos.entry_price) * pos.spot_qty
            total_pnl += pnl_usdt
            held_hours = (time.time() - pos.entry_time) / 3600
            pos_details.append({
                "symbol": pos.symbol,
                "qty": pos.spot_qty,
                "entry_price": pos.entry_price,
                "current_price": current_price,
                "pnl_pct": round(pnl_pct, 2),
                "pnl_usdt": round(pnl_usdt, 2),
                "held_hours": round(held_hours, 1),
            })

        return {
            "strategy": "rotation",
            "position_count": len(positions),
            "total_invested": self.state.total_invested("rotation"),
            "total_unrealized_pnl": round(total_pnl, 2),
            "positions": pos_details,
        }
