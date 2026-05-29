"""backtest/coin_engine.py — 통합 백테스트 엔진 coin 변형 어댑터 (SO-2/Phase R).

WHY: backtest/engine.py(Phase5) + coin 특성 변형표 #1 이식.
     coin 특성: 24/7(캘린더 없음)·Upbit maker/taker fee·호가깊이 슬리피지·얇은 알트 임팩트·KRW.

N-P5-COIN-METRICS 소진:
- common/metrics.calculate_rsi → 동치 보장
- backtest/engine.py CostConfig에 Upbit fee 적용

SACRED: 기존 13 backtest_*.py / sim_engine.py 미변경.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from backtest.engine import BacktestEngine, BacktestResult, CostConfig
from common.metrics import calculate_rsi

logger = logging.getLogger("backtest.coin_engine")


# ---------------------------------------------------------------------------
# Upbit 특성 비용 설정 (coin 변형 #1)
# ---------------------------------------------------------------------------

UPBIT_COST_CONFIG = CostConfig(
    commission_rate=0.0005,       # Upbit maker/taker 0.05%
    slippage_impact_factor=0.002, # 얇은 알트 호가깊이 임팩트 (2배)
    slippage_min=0.0001,
    slippage_max=0.05,
    kr_transaction_tax=0.0,       # 코인=거래세 없음
    enable_partial_fill=False,
)


@dataclass
class CoinBacktestConfig:
    """coin 백테스트 특성 설정."""
    is_24_7: bool = True           # 24/7 — 캘린더/휴장 없음
    pair: str = "KRW"              # KRW 페어
    funding_rate: float = 0.0001   # 펀딩비(선물, 현물=0)
    initial_capital: float = 1_000_000.0  # KRW


# ---------------------------------------------------------------------------
# CoinBacktestEngine
# ---------------------------------------------------------------------------

class CoinBacktestEngine:
    """통합 백테스트 엔진 coin 변형 어댑터.

    backtest/engine.py 재사용 + coin 특성 어댑트.
    SACRED: 기존 13 backtest_*.py/sim_engine.py 미변경.
    """

    def __init__(self, config: Optional[CoinBacktestConfig] = None):
        self._config = config or CoinBacktestConfig()
        self._engine = BacktestEngine(
            cost_config=UPBIT_COST_CONFIG,
            initial_capital=self._config.initial_capital,
        )

    def run(
        self,
        asset_track,
        price_series: pd.Series,
        volume_series: Optional[pd.Series] = None,
    ) -> BacktestResult:
        """coin 특성 백테스트 1구간 완주.

        24/7: 캘린더 필터 없이 전 기간 실행.
        Upbit fee: UPBIT_COST_CONFIG 경유.
        KRW 페어: region="KR"(거래세 0).
        """
        return self._engine.run(
            asset_track=asset_track,
            price_series=price_series,
            volume_series=volume_series,
            region="KR",  # KRW 페어 — 거래세 없음
        )

    def compare_with_legacy(
        self,
        asset_track,
        price_series: pd.Series,
        volume_series: Optional[pd.Series] = None,
    ) -> dict:
        """슬리피지0 vs coin 현실 백테스트 정량 비교.

        §2.9③: 교체 백테스트 엔진이 기존 backtest_*.py(슬리피지0) 대비 더 현실적.
        """
        from backtest.engine import CostConfig as CC
        zero_cfg = CC(
            commission_rate=0.0, slippage_impact_factor=0.0,
            slippage_min=0.0, kr_transaction_tax=0.0,
        )
        zero_engine = BacktestEngine(zero_cfg, self._config.initial_capital)

        coin_result = self.run(asset_track, price_series, volume_series)
        zero_result = zero_engine.run(asset_track, price_series, volume_series, region="KR")

        slippage_drag = zero_result.total_return_pct - coin_result.total_return_pct
        return {
            "coin_return_pct": coin_result.total_return_pct,
            "zero_return_pct": zero_result.total_return_pct,
            "slippage_drag_pct": slippage_drag,
            "is_more_realistic": slippage_drag >= 0.0,  # coin엔진이 더 보수적
            "coin_sharpe": coin_result.sharpe,
            "zero_sharpe": zero_result.sharpe,
        }

    @staticmethod
    def calc_rsi_common(closes: list, period: int = 14) -> float:
        """N-P5-COIN-METRICS: common/metrics.calculate_rsi 경유 (동치 보장)."""
        return calculate_rsi(closes, period)
