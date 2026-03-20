"""AltRang State -- 멀티코인 포지션 상태 영속화"""

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger("altrang.state")

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(PROJECT_DIR, "data", "altrang_state.json")


@dataclass
class CoinPosition:
    """개별 코인 포지션"""
    symbol: str = ""
    strategy: str = ""            # "funding" or "rotation"
    side: str = ""                # "hedged" (funding) or "long" (rotation)
    spot_qty: float = 0.0
    futures_qty: float = 0.0      # 0 for rotation
    entry_price: float = 0.0
    entry_time: float = 0.0
    funding_collected: float = 0.0
    unrealized_pnl: float = 0.0
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    # 고급 실행 로직 필드
    highest_price: float = 0.0    # 트레일링 스탑용 최고가
    partial_sold: bool = False    # 부분 익절 실행 여부
    original_qty: float = 0.0    # 최초 수량 (부분 매도 추적)
    entry_score: float = 0.0      # 5팩터 진입 점수 (동적 사이징용)


@dataclass
class BotState:
    """전체 봇 상태"""
    positions: dict = field(default_factory=dict)  # symbol -> CoinPosition dict
    trade_count_today: int = 0
    trade_date: str = ""          # YYYY-MM-DD
    last_trade_time: float = 0.0
    total_funding_collected: float = 0.0
    last_funding_rebalance: float = 0.0
    last_rotation_check: float = 0.0
    session_start_time: float = field(default_factory=time.time)
    # 손절 쿨다운: {symbol: stop_time} — 2시간 내 재진입 방지
    stop_cooldowns: dict = field(default_factory=dict)

    def get_position(self, symbol: str) -> Optional[CoinPosition]:
        if symbol in self.positions:
            data = self.positions[symbol]
            if isinstance(data, dict):
                return CoinPosition(**data)
            return data
        return None

    def set_position(self, pos: CoinPosition):
        self.positions[pos.symbol] = asdict(pos)

    def remove_position(self, symbol: str):
        self.positions.pop(symbol, None)

    def get_strategy_positions(self, strategy: str) -> list[CoinPosition]:
        result = []
        for data in self.positions.values():
            d = data if isinstance(data, dict) else asdict(data)
            if d.get("strategy") == strategy:
                result.append(CoinPosition(**d))
        return result

    def funding_count(self) -> int:
        return len(self.get_strategy_positions("funding"))

    def rotation_count(self) -> int:
        return len(self.get_strategy_positions("rotation"))

    def total_invested(self, strategy: str) -> float:
        return sum(
            p.entry_price * p.spot_qty
            for p in self.get_strategy_positions(strategy)
        )

    def check_daily_reset(self):
        """날짜 변경 시 일일 카운터 리셋"""
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self.trade_date != today:
            self.trade_date = today
            self.trade_count_today = 0


def load_state() -> BotState:
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            state = BotState()
            for k, v in data.items():
                if hasattr(state, k):
                    setattr(state, k, v)
            state.check_daily_reset()
            logger.info(
                f"상태 로드: {len(state.positions)}개 포지션, "
                f"금일 거래 {state.trade_count_today}회"
            )
            return state
    except Exception as e:
        logger.warning(f"상태 로드 실패 (새로 생성): {e}")
    return BotState()


def save_state(state: BotState):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(asdict(state), f, ensure_ascii=False, indent=2, default=str)
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        logger.error(f"상태 저장 실패: {e}")
        try:
            os.unlink(tmp)
        except OSError:
            pass
