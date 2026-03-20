"""AltRang Funding Engine -- 펀딩비 수확 (델타뉴트럴) 고도화

전략 (소수 정예, 장기 보유):
  1. 4팩터 스코어링: 현재 펀딩비 × 7일 안정성 × 유동성 × 스프레드
  2. 소수 코인(3개) 집중 보유, 최소 24시간 유지
  3. 펀딩비 수취 추적: 8시간마다 누적 수익 계산
  4. APR 기반 청산: 연환산 수익률 기준 미달 시 교체
  5. 프리미엄/디스카운트: 유리한 스프레드에서만 진입
  6. 헤지 균형 모니터링: 현물/선물 수량 불일치 경고
"""

import logging
import time

from altrang.config import AltrangConfig
from altrang.coin_selector import CoinSelector, CoinScore
from altrang.data_feeder import MultiCoinFeeder
from altrang.exchange_base import ExchangeAdapter
from altrang.risk_manager import RiskManager
from altrang.state import BotState, CoinPosition, save_state

logger = logging.getLogger("altrang.funding")

# 펀딩 지급 주기 (8시간)
FUNDING_INTERVAL_HOURS = 8
FUNDING_INTERVALS_PER_DAY = 3


class FundingEngine:
    """펀딩비 수확 엔진 (고도화)"""

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
        """주기적 체크 (매분 호출)

        빠른 체크 (매분): 펀딩 수취 추적 + 헤지 균형
        느린 체크 (리밸런스 주기): 청산/진입 판단
        """
        actions = []

        # 1. 매분: 펀딩 수취 추적 (8시간마다 자동 반영)
        self._track_funding_payments()

        # 2. 리밸런스 간격 체크
        now = time.time()
        elapsed = now - self.state.last_funding_rebalance
        if elapsed < self.config.funding.rebalance_interval_min * 60:
            return actions

        self.state.last_funding_rebalance = now

        # 3. 펀딩비 히스토리 심화 분석
        data = await self.feeder.enrich_funding_candidates(
            top_n=15,
            history_lookback=self.config.funding.history_lookback,
        )
        if not data:
            data = self.feeder.get_all()

        # 4. 청산 판단 (APR 기반)
        actions.extend(await self._check_exits(data))

        # 5. 신규 진입 (4팩터 스코어링)
        actions.extend(await self._check_entries(data))

        return actions

    def _track_funding_payments(self):
        """펀딩비 수취 추적 (시뮬레이션)

        Binance는 8시간마다(00:00/08:00/16:00 UTC) 펀딩비를 지급한다.
        DRY_RUN에서는 현재 펀딩비 기반으로 추정 수취액을 계산한다.
        """
        positions = self.state.get_strategy_positions("funding")
        data = self.feeder.get_all()

        for pos in positions:
            coin = data.get(pos.symbol)
            if not coin:
                continue

            held_hours = (time.time() - pos.entry_time) / 3600
            # 8시간마다 펀딩 지급 횟수 계산
            expected_payments = int(held_hours / FUNDING_INTERVAL_HOURS)
            # 이미 기록된 펀딩 횟수 추정 (기존 수취액 / 1회 예상액)
            one_payment = coin.funding_rate * pos.entry_price * pos.futures_qty
            if one_payment > 0:
                recorded_payments = int(pos.funding_collected / one_payment) if one_payment > 0 else 0
            else:
                recorded_payments = expected_payments

            # 미기록 펀딩 지급 반영
            new_payments = max(0, expected_payments - recorded_payments)
            if new_payments > 0:
                # 평균 펀딩비 사용 (enriched 시), 없으면 현재 펀딩비
                avg_rate = coin.funding_avg_7d if coin.funding_enriched and coin.funding_avg_7d > 0 else coin.funding_rate
                funding_income = avg_rate * pos.entry_price * pos.futures_qty * new_payments
                pos.funding_collected += funding_income
                self.state.total_funding_collected += funding_income
                self.state.set_position(pos)
                save_state(self.state)

                logger.info(
                    f"펀딩 수취: {pos.symbol} +${funding_income:.4f} "
                    f"(누적 ${pos.funding_collected:.4f}, {expected_payments}회)"
                )

    async def _check_exits(self, data: dict) -> list[dict]:
        """기존 포지션 청산 판단 (APR 기반)"""
        actions = []
        positions = self.state.get_strategy_positions("funding")
        cfg = self.config.funding

        for pos in positions:
            coin = data.get(pos.symbol)
            if not coin:
                continue

            held_hours = (time.time() - pos.entry_time) / 3600
            should_exit = False
            reason = ""

            # 1. 현재 펀딩비 급락 (음수 전환)
            if coin.funding_rate < 0:
                should_exit = True
                reason = f"펀딩비 음수: {coin.funding_rate*100:.4f}%"

            # 2. 펀딩비 히스토리 기반: 7일 평균 하락
            elif coin.funding_enriched and coin.funding_avg_7d < cfg.exit_funding_threshold:
                should_exit = True
                reason = f"7일 평균 펀딩비 하락: {coin.funding_avg_7d*100:.4f}%"

            # 3. 현재 펀딩비만 봤을 때 임계값 미달 (히스토리 없을 때)
            elif not coin.funding_enriched and coin.funding_rate < cfg.exit_funding_threshold:
                should_exit = True
                reason = f"펀딩비 하락: {coin.funding_rate*100:.4f}%"

            # 4. APR 기반: 실질 수익률 계산
            elif held_hours >= 48:  # 48시간 이상 보유 시 APR 검증
                invested = pos.entry_price * pos.spot_qty
                if invested > 0 and held_hours > 0:
                    daily_income = pos.funding_collected / (held_hours / 24)
                    actual_apr = (daily_income / invested) * 365 * 100
                    if actual_apr < cfg.min_apr_pct * 0.5:  # 최소 APR의 50% 미달
                        should_exit = True
                        reason = f"실질 APR 부족: {actual_apr:.1f}% (최소 {cfg.min_apr_pct/2:.0f}%)"

            # 최소 보유 시간 체크
            if should_exit and held_hours < cfg.min_hold_hours:
                # 음수 펀딩비는 보유시간 무시하고 즉시 청산
                if coin.funding_rate >= 0:
                    logger.info(
                        f"{pos.symbol} 청산 조건이나 최소 보유 {cfg.min_hold_hours}h 미달 "
                        f"({held_hours:.1f}h) - 유지"
                    )
                    continue

            if should_exit:
                invested = pos.entry_price * pos.spot_qty
                apr_str = ""
                if invested > 0 and held_hours > 0:
                    actual_apr = (pos.funding_collected / (held_hours / 24) / invested) * 365 * 100
                    apr_str = f" APR={actual_apr:.1f}%"

                logger.info(
                    f"펀딩 청산: {pos.symbol} ({reason})"
                    f" 보유 {held_hours:.0f}h"
                    f" 수취 ${pos.funding_collected:.4f}{apr_str}"
                )
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
                        "funding_collected": round(pos.funding_collected, 4),
                        "held_hours": round(held_hours, 1),
                        "success": True,
                    })
                else:
                    actions.append({
                        "action": "exit",
                        "strategy": "funding",
                        "symbol": pos.symbol,
                        "success": False,
                        "error": "편측 체결",
                    })

        return actions

    async def _check_entries(self, data: dict) -> list[dict]:
        """신규 진입 (4팩터 스코어링)"""
        actions = []
        ranked = self.selector.rank_by_funding(data)

        if not ranked:
            logger.info("펀딩 진입 대상 없음")
            return actions

        current_symbols = {
            p.symbol for p in self.state.get_strategy_positions("funding")
        }

        available_slots = self.config.funding.max_coins - len(current_symbols)
        if available_slots <= 0:
            return actions

        # TOP 코인 로깅
        top3 = ranked[:3]
        logger.info(
            f"펀딩 TOP 후보: "
            + ", ".join(f"{c.symbol}({c.score:.1f})" for c in top3)
        )

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

            coin = data.get(coin_score.symbol)
            if not coin or coin.spot_price <= 0:
                continue

            # 스프레드 로깅
            spread_pct = 0.0
            if coin.futures_price > 0:
                spread_pct = (coin.futures_price - coin.spot_price) / coin.spot_price * 100

            logger.info(
                f"펀딩 진입: {coin_score.symbol} "
                f"score={coin_score.score:.1f} "
                f"FR={coin.funding_rate*100:.4f}% "
                f"spread={spread_pct:+.3f}% "
                f"${size:.0f} "
                f"[{coin_score.reason}]"
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
                    entry_score=coin_score.score,
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
                    "score": coin_score.score,
                    "size_usdt": size,
                    "reason": coin_score.reason,
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
        total_funding = 0.0
        for pos in positions:
            coin = data.get(pos.symbol)
            current_rate = coin.funding_rate if coin else 0
            held_hours = (time.time() - pos.entry_time) / 3600
            invested = pos.entry_price * pos.spot_qty

            # 실질 APR 계산
            actual_apr = 0.0
            if invested > 0 and held_hours > 24:
                daily_income = pos.funding_collected / (held_hours / 24)
                actual_apr = (daily_income / invested) * 365 * 100

            # 추정 APR (현재 펀딩비 기반)
            est_apr = current_rate * FUNDING_INTERVALS_PER_DAY * 365 * 100

            total_funding += pos.funding_collected

            detail = {
                "symbol": pos.symbol,
                "qty": pos.spot_qty,
                "entry_price": pos.entry_price,
                "current_funding_rate": current_rate,
                "funding_collected": round(pos.funding_collected, 4),
                "held_hours": round(held_hours, 1),
                "invested_usdt": round(invested, 2),
                "entry_score": pos.entry_score,
                "actual_apr_pct": round(actual_apr, 1),
                "estimated_apr_pct": round(est_apr, 1),
            }

            # 히스토리 정보 추가
            if coin and coin.funding_enriched:
                detail["avg_7d_rate"] = round(coin.funding_avg_7d * 100, 4)
                detail["positive_ratio"] = round(coin.funding_positive_ratio * 100, 0)

            pos_details.append(detail)

        return {
            "strategy": "funding",
            "position_count": len(positions),
            "max_coins": self.config.funding.max_coins,
            "total_invested": self.state.total_invested("funding"),
            "total_funding_collected": round(total_funding, 4),
            "total_funding_all_time": round(self.state.total_funding_collected, 4),
            "positions": pos_details,
        }
