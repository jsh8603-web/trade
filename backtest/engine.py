"""backtest/engine.py — asset-agnostic 통합 백테스트 엔진 (SO-2/P5).

WHY: coin 13 분산 backtest_*.py + 슬리피지0 sim_engine.py 의 교체 대상(교체=Phase R).
     본 Phase = 일반 빌드만. 코인 기존 파일 미변경(SACRED).

설계:
- BacktestEngine: AssetTrack 계약(collect_market_state·generate_candidate) 경유
- 슬리피지 모델: 거래대금/호가잔량 비례 임팩트 (H1, sim_engine 슬리피지0 대비)
- 수수료: Upbit 0.05% / KIS (설정 가능)
- 세금: KR 거래세 0.20% 매도 / 환전 ~0.2% US / 해외양도세 22%
- nautilus OrderState enum: INITIALIZED→SUBMITTED→ACCEPTED→PARTIALLY_FILLED→FILLED/CANCELED
- FillModel: 확률체결 옵션 (랜덤 부분체결)
- UTC 단일 타임존
- common/metrics import (자체 지표 중복 0)
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional

import pandas as pd

from common.metrics import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_win_rate,
    calculate_cagr,
    returns_from_equity,
)

logger = logging.getLogger("backtest.engine")

# ---------------------------------------------------------------------------
# OrderState — nautilus FSM 축약 (implementation-keys §1-(d))
# ---------------------------------------------------------------------------

class OrderState(Enum):
    """nautilus OrderState FSM 축약. 전이 검증 필수."""
    INITIALIZED = auto()
    SUBMITTED = auto()
    ACCEPTED = auto()
    PARTIALLY_FILLED = auto()
    FILLED = auto()
    CANCELED = auto()


_VALID_TRANSITIONS = {
    OrderState.INITIALIZED: {OrderState.SUBMITTED, OrderState.CANCELED},
    OrderState.SUBMITTED: {OrderState.ACCEPTED, OrderState.CANCELED},
    OrderState.ACCEPTED: {OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.CANCELED},
    OrderState.PARTIALLY_FILLED: {OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.CANCELED},
    OrderState.FILLED: set(),
    OrderState.CANCELED: set(),
}


def validate_transition(from_state: OrderState, to_state: OrderState) -> bool:
    return to_state in _VALID_TRANSITIONS.get(from_state, set())


# ---------------------------------------------------------------------------
# 비용 모델 설정
# ---------------------------------------------------------------------------

@dataclass
class CostConfig:
    """수수료/세금/슬리피지 설정 (OPEN ZONE — 구체 계수 튜닝 가능)."""
    # 수수료
    commission_rate: float = 0.0005      # Upbit 0.05%
    kis_commission_rate: float = 0.00015  # KIS ~0.015%

    # 세금 (§5)
    kr_transaction_tax: float = 0.002    # KR 거래세 0.20% 매도 시
    us_fx_cost: float = 0.002            # 환전 비용 ~0.2%
    us_capital_gains_tax: float = 0.22   # 해외 양도세 22% (연간 기준, 백테스트 근사)

    # 슬리피지 모델 파라미터 (H1)
    slippage_impact_factor: float = 0.001  # 거래대금/시총 비례 임팩트 기본 계수
    slippage_min: float = 0.0001           # 최소 슬리피지 (0.01%)
    slippage_max: float = 0.05             # 최대 슬리피지 (5%)

    # FillModel
    enable_partial_fill: bool = False      # 확률체결 옵션
    partial_fill_prob: float = 0.1         # 부분체결 확률


# ---------------------------------------------------------------------------
# 슬리피지 모델 (H1)
# ---------------------------------------------------------------------------

def calculate_slippage(
    trade_value: float,
    market_volume: float,
    config: CostConfig,
) -> float:
    """거래대금/시장거래량 비례 임팩트 슬리피지.

    market_volume = 해당 바의 거래대금(또는 시총). trade_value = 주문 금액.
    임팩트 = impact_factor * (trade_value / market_volume).
    """
    if market_volume <= 0:
        return config.slippage_max
    impact = config.slippage_impact_factor * (trade_value / market_volume)
    return float(max(config.slippage_min, min(config.slippage_max, impact)))


# ---------------------------------------------------------------------------
# 거래 레코드
# ---------------------------------------------------------------------------

@dataclass
class Trade:
    trade_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    asset: str = ""
    side: str = "BUY"               # "BUY" | "SELL"
    price: float = 0.0
    qty: float = 0.0
    commission: float = 0.0
    tax: float = 0.0
    slippage: float = 0.0
    pnl: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    order_state: OrderState = OrderState.FILLED
    region: str = "KR"              # "KR" | "US"


# ---------------------------------------------------------------------------
# BacktestResult
# ---------------------------------------------------------------------------

@dataclass
class BacktestResult:
    """백테스트 단일 구간 결과."""
    asset: str = ""
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    initial_capital: float = 10_000_000.0
    final_capital: float = 10_000_000.0
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)

    # 지표 (common/metrics 로 채움)
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0
    win_rate: float = 0.0
    cagr: float = 0.0
    total_return_pct: float = 0.0
    n_trades: int = 0

    def compute_metrics(self) -> None:
        """common/metrics 로 지표 산출 (자체 중복 0)."""
        if len(self.equity_curve) < 2:
            return
        returns = returns_from_equity(self.equity_curve)
        self.sharpe = calculate_sharpe_ratio(returns)
        self.max_drawdown = calculate_max_drawdown(self.equity_curve)
        self.cagr = calculate_cagr(self.equity_curve)
        if self.trades:
            df = pd.DataFrame([{"pnl": t.pnl} for t in self.trades])
            self.profit_factor = calculate_profit_factor(df)
            self.win_rate = calculate_win_rate(df)
        self.n_trades = len(self.trades)
        if self.initial_capital > 0:
            self.total_return_pct = (
                (self.final_capital - self.initial_capital) / self.initial_capital * 100
            )


# ---------------------------------------------------------------------------
# BacktestEngine — 메인 엔진
# ---------------------------------------------------------------------------

class BacktestEngine:
    """asset-agnostic 통합 백테스트 엔진.

    AssetTrack 계약(collect_market_state·generate_candidate) 경유.
    coin_track·stock_track 둘 다 구동.
    risk_gate(Phase2)·admission(Phase3) 재사용.
    common/metrics(SO-1) import.
    """

    def __init__(
        self,
        cost_config: Optional[CostConfig] = None,
        initial_capital: float = 10_000_000.0,
        fill_model_seed: Optional[int] = None,
    ):
        self._cost = cost_config or CostConfig()
        self._initial_capital = initial_capital
        self._rng = __import__("random").Random(fill_model_seed)

    def run(
        self,
        asset_track,
        price_series: pd.Series,
        volume_series: Optional[pd.Series] = None,
        region: str = "KR",
    ) -> BacktestResult:
        """단일 자산 백테스트 1구간 완주.

        Args:
            asset_track: AssetTrack 구현체 (coin_track·stock_track)
            price_series: 가격 시계열 (UTC index)
            volume_series: 거래대금 시계열 (슬리피지 계산용, None이면 최대 슬리피지)
            region: "KR" | "US"
        """
        if volume_series is None:
            volume_series = pd.Series(
                [0.0] * len(price_series), index=price_series.index
            )

        capital = self._initial_capital
        position = 0.0        # 보유 수량
        avg_price = 0.0
        equity_points: List[float] = [capital]
        trades: List[Trade] = []

        asset_name = price_series.name or "UNKNOWN"

        for ts, price in price_series.items():
            vol = float(volume_series.get(ts, 0.0))

            # AssetTrack 계약 경유
            state = asset_track.collect_market_state()
            state.raw_market_data["price"] = price
            state.raw_market_data["asset"] = asset_name
            state.raw_market_data["timestamp"] = str(ts)

            try:
                decision = asset_track.generate_candidate(state)
                action = getattr(decision, "action", "hold")
            except Exception:
                action = "hold"

            if action == "buy" and capital > 0:
                trade_value = capital * 0.95  # 자본의 95%
                slip = calculate_slippage(trade_value, vol, self._cost)
                exec_price = price * (1 + slip)
                commission = trade_value * self._cost.commission_rate
                qty = (trade_value - commission) / exec_price

                # FillModel 확률체결
                state_order, qty = self._apply_fill_model(qty)

                if qty > 0:
                    position += qty
                    avg_price = exec_price
                    capital -= (qty * exec_price + commission)

                    trades.append(Trade(
                        asset=asset_name,
                        side="BUY",
                        price=exec_price,
                        qty=qty,
                        commission=commission,
                        slippage=slip * trade_value,
                        timestamp=ts if isinstance(ts, datetime) else datetime.now(timezone.utc),
                        order_state=state_order,
                        region=region,
                    ))

            elif action == "sell" and position > 0:
                trade_value = position * price
                slip = calculate_slippage(trade_value, vol, self._cost)
                exec_price = price * (1 - slip)
                commission = trade_value * self._cost.commission_rate
                tax = self._calc_tax(exec_price * position, region)
                pnl = (exec_price - avg_price) * position - commission - tax

                # H17: 하한가잠김 체크 (Phase4 kis_client 연계)
                if self._is_lower_limit_locked(price, avg_price):
                    logger.debug("H17 하한가잠김 — 매도 불가: %s", asset_name)
                    equity_points.append(capital + position * price)
                    continue

                capital += position * exec_price - commission - tax
                position = 0.0

                trades.append(Trade(
                    asset=asset_name,
                    side="SELL",
                    price=exec_price,
                    qty=position,
                    commission=commission,
                    tax=tax,
                    slippage=slip * trade_value,
                    pnl=pnl,
                    timestamp=ts if isinstance(ts, datetime) else datetime.now(timezone.utc),
                    order_state=OrderState.FILLED,
                    region=region,
                ))

            equity_points.append(capital + position * price)

        final_capital = capital + position * (
            float(price_series.iloc[-1]) if len(price_series) > 0 else 0.0
        )

        result = BacktestResult(
            asset=asset_name,
            start=price_series.index[0] if len(price_series) > 0 else None,
            end=price_series.index[-1] if len(price_series) > 0 else None,
            initial_capital=self._initial_capital,
            final_capital=final_capital,
            trades=trades,
            equity_curve=pd.Series(equity_points),
        )
        result.compute_metrics()
        return result

    def _apply_fill_model(self, qty: float):
        """FillModel 확률체결. 확률적으로 부분체결 시뮬레이션."""
        if not self._cost.enable_partial_fill:
            return OrderState.FILLED, qty
        if self._rng.random() < self._cost.partial_fill_prob:
            partial = qty * self._rng.uniform(0.3, 0.9)
            return OrderState.PARTIALLY_FILLED, partial
        return OrderState.FILLED, qty

    def _calc_tax(self, sell_value: float, region: str) -> float:
        """§5 세금 계산. KR 거래세 / US 환전 비용."""
        if region == "KR":
            return sell_value * self._cost.kr_transaction_tax
        elif region == "US":
            return sell_value * self._cost.us_fx_cost
        return 0.0

    @staticmethod
    def _is_lower_limit_locked(price: float, avg_price: float) -> bool:
        """H17 하한가잠김 — 기준가 대비 ±30% 하한 체크."""
        if avg_price <= 0:
            return False
        lower_limit = avg_price * 0.70
        return price <= lower_limit

    def compare_slippage(
        self,
        asset_track,
        price_series: pd.Series,
        volume_series: Optional[pd.Series] = None,
        region: str = "KR",
    ) -> Dict[str, Any]:
        """§2.9①: 슬리피지0 vs 현실 정량화."""
        zero_cost = CostConfig(
            slippage_impact_factor=0.0, slippage_min=0.0,
            commission_rate=0.0, kr_transaction_tax=0.0,
        )
        real_engine = BacktestEngine(self._cost, self._initial_capital)
        zero_engine = BacktestEngine(zero_cost, self._initial_capital)

        real_result = real_engine.run(asset_track, price_series, volume_series, region)
        zero_result = zero_engine.run(asset_track, price_series, volume_series, region)

        return {
            "real_sharpe": real_result.sharpe,
            "zero_sharpe": zero_result.sharpe,
            "real_return_pct": real_result.total_return_pct,
            "zero_return_pct": zero_result.total_return_pct,
            "slippage_drag_pct": zero_result.total_return_pct - real_result.total_return_pct,
        }
