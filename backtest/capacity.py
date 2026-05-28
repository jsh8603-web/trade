"""backtest/capacity.py — H28 capacity 상한 + H17 가격제한폭 + H1 E4 캘리브레이션 (SO-5/P5).

WHY:
- H28: capacity 상한 = 자기충격(price impact)이 Sharpe 부풀림 차단. KR 소형주·얇은 알트.
- H17: 한국 ±30% 가격제한폭·거래정지·하한가잠김 매도불가 → 슬리피지/게이트 반영.
- H1 E4: R2 reconciliation 데이터로 예상 vs 실제 체결가 주간 측정 → 슬리피지 파라미터 보정.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("backtest.capacity")


# ---------------------------------------------------------------------------
# H28 Capacity 상한
# ---------------------------------------------------------------------------

@dataclass
class CapacityConfig:
    """H28 capacity 상한 설정 (OPEN ZONE — 구체 계수 튜닝 가능)."""
    max_capacity_ratio: float = 0.01     # 전략 주문 ≤ 일 거래대금의 1%
    sharpe_boost_threshold: float = 2.0  # 이 Sharpe 이상이면 capacity 검사
    reject_on_exceed: bool = True


class CapacityChecker:
    """H28: 전략 주문이 시장 용량을 초과하는지 체크.

    규모 과대 → 자기충격(price impact) → Sharpe 부풀림.
    capacity 상한 초과 주문 거절로 비현실적 수익률 차단.
    """

    def __init__(self, config: Optional[CapacityConfig] = None):
        self._cfg = config or CapacityConfig()

    def check(
        self,
        order_value: float,
        daily_volume: float,
        strategy_sharpe: float = 0.0,
    ) -> Tuple[bool, str]:
        """주문이 capacity 한도 내인지 확인.

        Returns:
            (ok, reason): ok=True 허용, False 거절.
        """
        if daily_volume <= 0:
            return False, "H28: 거래량 0 — 유동성 없음"

        ratio = order_value / daily_volume
        if ratio > self._cfg.max_capacity_ratio:
            return False, (
                f"H28: capacity 초과 "
                f"(주문={order_value:.0f} / 거래대금={daily_volume:.0f} "
                f"= {ratio:.2%} > 한도 {self._cfg.max_capacity_ratio:.2%})"
            )

        return True, "OK"

    def adjust_sharpe_for_capacity(
        self,
        sharpe: float,
        order_value: float,
        daily_volume: float,
    ) -> float:
        """capacity 초과 시 Sharpe 패널티 적용 (규모 조정 후 재추정)."""
        if daily_volume <= 0:
            return 0.0
        ratio = order_value / daily_volume
        if ratio > self._cfg.max_capacity_ratio:
            # 현실적 규모로 축소 비율만큼 Sharpe 감소
            scale = self._cfg.max_capacity_ratio / ratio
            return sharpe * scale
        return sharpe


# ---------------------------------------------------------------------------
# H17 가격제한폭 / 거래정지 / 하한가잠김
# ---------------------------------------------------------------------------

class PriceLimitChecker:
    """H17: 한국 ±30% 가격제한폭·거래정지·하한가잠김 매도불가.

    kis_client.py 의 check_price_limit 과 동일 로직 (백테스트 엔진용 독립 구현).
    SACRED: kis_client.py 미변경.
    """

    LIMIT_PCT = 0.30  # ±30%

    def check_buy(self, price: float, ref_price: float) -> Tuple[bool, str]:
        """매수 가격 제한폭 체크."""
        if ref_price <= 0:
            return True, "ref_price 불명"
        upper = ref_price * (1 + self.LIMIT_PCT)
        if price > upper:
            return False, f"H17: 상한 초과 ({price:.0f} > {upper:.0f})"
        return True, "OK"

    def check_sell(self, price: float, ref_price: float) -> Tuple[bool, str]:
        """매도 가격 제한폭 체크. 하한가잠김 = 매도불가."""
        if ref_price <= 0:
            return True, "ref_price 불명"
        lower = ref_price * (1 - self.LIMIT_PCT)
        if price <= lower:
            return False, f"H17: 하한가잠김 매도불가 ({price:.0f} <= {lower:.0f})"
        return True, "OK"

    def calc_sell_slippage(
        self,
        price: float,
        ref_price: float,
        base_slippage: float = 0.001,
    ) -> float:
        """하한가 접근 시 추가 슬리피지 (하한가에 가까울수록 큰 임팩트)."""
        if ref_price <= 0:
            return base_slippage
        lower = ref_price * (1 - self.LIMIT_PCT)
        distance = (price - lower) / ref_price
        if distance < 0.05:  # 하한가 5% 이내
            extra = (0.05 - distance) * 0.1  # 최대 +0.5% 추가
            return base_slippage + extra
        return base_slippage


# ---------------------------------------------------------------------------
# H1 E4 라이브 캘리브레이션
# ---------------------------------------------------------------------------

@dataclass
class SlippageObservation:
    """실측 체결가 vs 예상 체결가 관측."""
    expected_price: float
    actual_price: float
    side: str  # "BUY" | "SELL"

    @property
    def slippage_pct(self) -> float:
        if self.expected_price <= 0:
            return 0.0
        return abs(self.actual_price - self.expected_price) / self.expected_price


class E4SlippageCalibrator:
    """H1 E4: R2 reconciliation 데이터로 슬리피지 파라미터 주간 보정.

    예상 체결가 vs 실제 체결가 측정 → impact_factor 자동 조정.
    백테스트=라이브 패리티 유지.
    """

    def __init__(self, window_size: int = 20):
        self._window_size = window_size
        self._observations: List[SlippageObservation] = []
        self._current_impact_factor: float = 0.001  # 초기값

    def record(self, obs: SlippageObservation) -> None:
        """실측 체결가 기록."""
        self._observations.append(obs)
        if len(self._observations) > self._window_size * 2:
            self._observations = self._observations[-self._window_size:]

    def calibrate(self) -> float:
        """최근 관측으로 impact_factor 재보정. 이동평균 기반."""
        if len(self._observations) < 3:
            return self._current_impact_factor

        recent = self._observations[-self._window_size:]
        avg_slippage = sum(o.slippage_pct for o in recent) / len(recent)

        # 실측 슬리피지가 모델 예측과 다르면 factor 조정
        # 간단한 비례 보정 (OPEN ZONE — 갱신식 구체값 튜닝 가능)
        adjustment = avg_slippage / max(self._current_impact_factor, 1e-6)
        adjustment = max(0.5, min(2.0, adjustment))  # ±2배 이내 조정
        self._current_impact_factor = self._current_impact_factor * adjustment
        return self._current_impact_factor

    @property
    def impact_factor(self) -> float:
        return self._current_impact_factor

    def n_observations(self) -> int:
        return len(self._observations)
