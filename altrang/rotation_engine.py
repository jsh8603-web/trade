"""AltRang Rotation Engine -- 알트코인 모멘텀 로테이션 (고도화)

개선 사항 (freqtrade/passivbot 참고):
  1. 트레일링 스탑 (단계별): 수익 구간별 스탑 자동 상향
  2. 부분 익절: +5%에서 50% 매도, 나머지 트레일
  3. 시간 기반 ROI 감쇠: 24h 미달 시 손익분기점 청산
  4. 동적 포지션 사이징: 5팩터 점수 비례 배분
  5. 손절 후 쿨다운: 같은 코인 2시간 재진입 금지
  6. high watermark 추적: 최고가 기록으로 트레일링 지원
"""

import logging
import time

from altrang.config import AltrangConfig
from altrang.coin_selector import CoinSelector
from altrang.data_feeder import MultiCoinFeeder
from altrang.exchange_base import ExchangeAdapter
from altrang.risk_manager import RiskManager
from altrang.state import BotState, CoinPosition, save_state

logger = logging.getLogger("altrang.rotation")

# 트레일링 스탑 단계 설정
# (최소 수익률, 트레일 비율) — 수익이 높을수록 스탑을 좁혀서 보호
TRAILING_STEPS = [
    (0.08, 0.03),   # +8% 이상 → 최고가에서 -3% (최소 +5% 확보)
    (0.05, 0.035),  # +5% 이상 → 최고가에서 -3.5% (최소 +1.5% 확보)
    (0.03, 0.02),   # +3% 이상 → 진입가 +1% 확보 (본전 이상)
]

# 부분 익절 설정
PARTIAL_TAKE_PROFIT_PCT = 0.05   # +5%에서 부분 매도
PARTIAL_SELL_RATIO = 0.50        # 50% 매도

# 시간 기반 ROI 감쇠
MAX_HOLD_HOURS = 48              # 48시간 후 무조건 청산
STALE_HOLD_HOURS = 24            # 24시간 후 +1% 미달이면 청산
ROI_DECAY_START_HOURS = 12       # 12시간부터 목표 수익률 감소

# 쿨다운
STOP_COOLDOWN_HOURS = 2          # 손절 후 2시간 재진입 금지


class RotationEngine:
    """알트코인 모멘텀 로테이션 엔진 (고도화)"""

    def __init__(
        self,
        config: AltrangConfig,
        state: BotState,
        feeder: MultiCoinFeeder,
        executor: ExchangeAdapter,
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

        빠른 체크 (매분): 트레일링 스탑 + 부분 익절 + 시간 청산
        느린 체크 (rotation_interval): 5팩터 로테이션
        """
        actions = []

        # 1. high watermark 업데이트 + 트레일링/부분익절/시간청산
        actions.extend(await self._check_positions())

        # 2. 로테이션 체크 (주기적)
        now = time.time()
        elapsed = now - self.state.last_rotation_check
        if elapsed >= self.config.rotation.rotation_interval_min * 60:
            self.state.last_rotation_check = now
            actions.extend(await self._do_rotation())

        return actions

    async def _check_positions(self) -> list[dict]:
        """매분 실행: 트레일링 스탑 + 부분 익절 + 시간 기반 청산"""
        actions = []
        positions = self.state.get_strategy_positions("rotation")
        data = self.feeder.get_all()

        for pos in positions:
            coin = data.get(pos.symbol)
            if not coin or coin.spot_price <= 0 or pos.entry_price <= 0:
                continue

            current_price = coin.spot_price
            pnl_pct = (current_price - pos.entry_price) / pos.entry_price * 100
            held_hours = (time.time() - pos.entry_time) / 3600

            # high watermark 업데이트
            if current_price > pos.highest_price:
                pos.highest_price = current_price
                self.state.set_position(pos)

            action = None
            reason = ""

            # ── 1. 트레일링 스탑 체크 ──
            trailing_stop = self._calculate_trailing_stop(pos)
            if trailing_stop > 0 and current_price <= trailing_stop:
                trail_pnl = (trailing_stop - pos.entry_price) / pos.entry_price * 100
                action = "trailing_stop"
                reason = (
                    f"트레일링 스탑: 현재 {pnl_pct:+.1f}% "
                    f"(최고 {(pos.highest_price/pos.entry_price-1)*100:+.1f}% → "
                    f"스탑 {trail_pnl:+.1f}%)"
                )

            # ── 2. 고정 손절 (트레일링 이전 단계) ──
            elif current_price <= pos.stop_loss_price:
                action = "stop_loss"
                reason = f"손절: {pnl_pct:+.1f}% (한도 -{self.config.rotation.stop_loss_pct}%)"

            # ── 3. 부분 익절 (50% @ +5%) ──
            elif (not pos.partial_sold
                  and pnl_pct >= PARTIAL_TAKE_PROFIT_PCT * 100
                  and pos.spot_qty > 0):
                action = "partial_take_profit"
                reason = f"부분 익절: {pnl_pct:+.1f}% (50% 매도, 나머지 트레일)"

            # ── 4. 시간 기반 강제 청산 ──
            elif held_hours >= MAX_HOLD_HOURS:
                action = "time_exit_max"
                reason = f"최대 보유시간 초과: {held_hours:.0f}h (한도 {MAX_HOLD_HOURS}h)"

            # ── 5. 정체 포지션 퇴출 (24h + 수익 <1%) ──
            elif held_hours >= STALE_HOLD_HOURS and pnl_pct < 1.0:
                action = "time_exit_stale"
                reason = f"정체 청산: {held_hours:.0f}h 보유, PnL={pnl_pct:+.1f}% (<1%)"

            # ── 6. ROI 감쇠 청산 (12h~ 목표 수익 점진 하향) ──
            elif held_hours >= ROI_DECAY_START_HOURS:
                min_roi = max(0, 3.0 - (held_hours - ROI_DECAY_START_HOURS) * 0.15)
                if pnl_pct >= min_roi and pnl_pct > 0:
                    action = "roi_decay"
                    reason = f"ROI 감쇠 익절: {pnl_pct:+.1f}% (목표 {min_roi:.1f}% @ {held_hours:.0f}h)"

            # 실행
            if action == "partial_take_profit":
                result = await self._execute_partial_sell(pos, current_price, pnl_pct, reason)
                if result:
                    actions.append(result)
            elif action:
                result = await self._execute_full_sell(pos, current_price, pnl_pct, action, reason)
                if result:
                    actions.append(result)

        return actions

    def _calculate_trailing_stop(self, pos: CoinPosition) -> float:
        """단계별 트레일링 스탑 계산

        수익 구간별로 스탑을 자동 상향:
          +8% → 최고가 -3% (최소 +5% 확보)
          +5% → 최고가 -3.5%
          +3% → 진입가 +1% (본전 이상)
        """
        if pos.highest_price <= 0 or pos.entry_price <= 0:
            return 0.0

        profit_from_peak = (pos.highest_price - pos.entry_price) / pos.entry_price

        for min_profit, trail_pct in TRAILING_STEPS:
            if profit_from_peak >= min_profit:
                return pos.highest_price * (1 - trail_pct)

        return 0.0  # 아직 트레일링 활성화 구간 아님

    async def _execute_partial_sell(
        self, pos: CoinPosition, current_price: float, pnl_pct: float, reason: str
    ) -> dict | None:
        """부분 익절 실행 (50% 매도)"""
        sell_qty = pos.spot_qty * PARTIAL_SELL_RATIO

        logger.info(f"부분 익절: {pos.symbol} {sell_qty:.5f} ({reason})")
        result = await self.executor.spot_sell(pos.symbol, sell_qty)

        if result.success:
            pnl_usdt = (current_price - pos.entry_price) * sell_qty

            # 포지션 업데이트 (남은 수량)
            if not pos.original_qty:
                pos.original_qty = pos.spot_qty
            pos.spot_qty -= sell_qty
            pos.partial_sold = True
            self.state.set_position(pos)
            self.state.trade_count_today += 1
            save_state(self.state)

            return {
                "action": "partial_take_profit",
                "strategy": "rotation",
                "symbol": pos.symbol,
                "reason": reason,
                "pnl_pct": round(pnl_pct, 2),
                "pnl_usdt": round(pnl_usdt, 2),
                "size_usdt": round(sell_qty * current_price, 2),
                "success": True,
            }
        return None

    async def _execute_full_sell(
        self, pos: CoinPosition, current_price: float,
        pnl_pct: float, action: str, reason: str,
    ) -> dict | None:
        """전량 매도 실행"""
        logger.info(f"로테이션 {action}: {pos.symbol} ({reason})")
        result = await self.executor.spot_sell(pos.symbol, pos.spot_qty)

        if result.success:
            pnl_usdt = (current_price - pos.entry_price) * pos.spot_qty
            self.state.remove_position(pos.symbol)
            self.state.trade_count_today += 1

            # 손절 쿨다운 등록
            if action in ("stop_loss", "trailing_stop") and pnl_pct < 0:
                self.state.stop_cooldowns[pos.symbol] = time.time()

            save_state(self.state)
            return {
                "action": action,
                "strategy": "rotation",
                "symbol": pos.symbol,
                "reason": reason,
                "pnl_pct": round(pnl_pct, 2),
                "pnl_usdt": round(pnl_usdt, 2),
                "success": True,
            }
        else:
            return {
                "action": action,
                "strategy": "rotation",
                "symbol": pos.symbol,
                "success": False,
                "error": result.error,
            }

    async def _do_rotation(self) -> list[dict]:
        """5팩터 모멘텀 기반 로테이션 실행"""
        actions = []

        # kline 심화 분석 (RSI/BB/상관도) — 상위 50개 후보만
        data = await self.feeder.enrich_rotation_candidates(
            top_n=self.config.rotation.enrichment_top_n
        )
        if not data:
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

        # 쿨다운 만료 정리
        self._cleanup_cooldowns()

        # 매수 (균등 배분 + 점수 보정 + 쿨다운 체크)
        # 예산을 목표 코인 수로 균등 분배 후, 점수에 따라 ±20% 보정
        current_invested = self.state.total_invested("rotation")
        remaining_budget = self.config.rotation.max_total_usdt - current_invested
        buyable = [c for c in enter_list if not self._is_on_cooldown(c.symbol)]
        if buyable:
            per_coin_budget = remaining_budget / len(buyable)
        else:
            per_coin_budget = 0

        for coin_score in enter_list:
            # 쿨다운 체크
            if self._is_on_cooldown(coin_score.symbol):
                logger.info(f"쿨다운 중: {coin_score.symbol} (손절 후 {STOP_COOLDOWN_HOURS}h 미경과)")
                continue

            # 동적 사이징: 균등 배분 × 점수 보정 (±20%)
            # 점수 50=0.8x, 70=1.0x, 90=1.2x (선형 보간)
            score_multiplier = max(0.8, min(1.2, 0.6 + coin_score.score / 150))
            size = round(per_coin_budget * score_multiplier, 2)
            size = max(self.config.min_order_amount, size)

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
                f"size=${size:.0f} (x{score_multiplier:.2f}) "
                f"24h={coin.price_change_pct_24h:+.1f}%"
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
                    highest_price=entry_price,
                    original_qty=result.filled_qty,
                    entry_score=coin_score.score,
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
                    "reason": coin_score.reason,
                })

        return actions

    def _is_on_cooldown(self, symbol: str) -> bool:
        """손절 후 쿨다운 중인지 확인"""
        stop_time = self.state.stop_cooldowns.get(symbol)
        if not stop_time:
            return False
        elapsed_hours = (time.time() - stop_time) / 3600
        return elapsed_hours < STOP_COOLDOWN_HOURS

    def _cleanup_cooldowns(self):
        """만료된 쿨다운 정리"""
        now = time.time()
        expired = [
            sym for sym, t in self.state.stop_cooldowns.items()
            if (now - t) / 3600 >= STOP_COOLDOWN_HOURS
        ]
        for sym in expired:
            del self.state.stop_cooldowns[sym]

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
            highest_pct = (pos.highest_price / pos.entry_price - 1) * 100 if pos.entry_price > 0 and pos.highest_price > 0 else 0
            pos_details.append({
                "symbol": pos.symbol,
                "qty": pos.spot_qty,
                "entry_price": pos.entry_price,
                "current_price": current_price,
                "pnl_pct": round(pnl_pct, 2),
                "pnl_usdt": round(pnl_usdt, 2),
                "held_hours": round(held_hours, 1),
                "highest_pct": round(highest_pct, 2),
                "partial_sold": pos.partial_sold,
                "entry_score": pos.entry_score,
            })

        return {
            "strategy": "rotation",
            "position_count": len(positions),
            "total_invested": self.state.total_invested("rotation"),
            "total_unrealized_pnl": round(total_pnl, 2),
            "positions": pos_details,
        }
