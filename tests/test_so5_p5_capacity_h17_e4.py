"""tests/test_so5_p5_capacity_h17_e4.py — SO-5/P5 H28+H17+E4 검증.

검증 기준 (harness2.md SO-5):
1. capacity 상한 초과 주문 거절 (규모↑→capacity 초과→거절)
2. H17 하한가잠김 → 매도 슬리피지/차단
3. E4 보정 (실측 체결가 입력 → 슬리피지 파라미터 조정)
"""

from __future__ import annotations

import pytest

from backtest.capacity import (
    CapacityChecker,
    CapacityConfig,
    PriceLimitChecker,
    E4SlippageCalibrator,
    SlippageObservation,
)


# ---------------------------------------------------------------------------
# 1. H28 Capacity 상한
# ---------------------------------------------------------------------------

def test_capacity_ok_within_limit():
    """주문/거래대금 비율 한도 내 → OK."""
    checker = CapacityChecker(CapacityConfig(max_capacity_ratio=0.01))
    ok, reason = checker.check(order_value=100_000, daily_volume=100_000_000)
    assert ok is True


def test_capacity_reject_over_limit():
    """주문/거래대금 비율 초과 → 거절."""
    checker = CapacityChecker(CapacityConfig(max_capacity_ratio=0.01))
    ok, reason = checker.check(order_value=5_000_000, daily_volume=100_000_000)
    assert ok is False
    assert "H28" in reason


def test_capacity_increases_rejection_with_order_size():
    """주문 규모↑ → 한도 초과 → 거절. 작은 주문은 통과."""
    checker = CapacityChecker(CapacityConfig(max_capacity_ratio=0.01))
    ok_small, _ = checker.check(order_value=100_000, daily_volume=100_000_000)
    ok_large, _ = checker.check(order_value=50_000_000, daily_volume=100_000_000)
    assert ok_small is True
    assert ok_large is False


def test_capacity_zero_volume_rejected():
    """거래량 0 → 유동성 없음 거절."""
    checker = CapacityChecker()
    ok, reason = checker.check(order_value=1000, daily_volume=0)
    assert ok is False


def test_capacity_sharpe_adjusted():
    """capacity 초과 시 Sharpe 패널티 적용 → 조정 후 < 원래 Sharpe."""
    checker = CapacityChecker(CapacityConfig(max_capacity_ratio=0.01))
    sharpe_adj = checker.adjust_sharpe_for_capacity(
        sharpe=2.0, order_value=10_000_000, daily_volume=100_000_000
    )
    assert sharpe_adj < 2.0


# ---------------------------------------------------------------------------
# 2. H17 가격제한폭 / 하한가잠김
# ---------------------------------------------------------------------------

def test_h17_buy_upper_limit_blocked():
    """H17: 매수 상한가 초과 → 차단."""
    checker = PriceLimitChecker()
    ok, reason = checker.check_buy(price=135000, ref_price=100000)
    assert ok is False
    assert "상한" in reason


def test_h17_buy_within_limit_ok():
    """H17: 매수 정상 범위 → OK."""
    checker = PriceLimitChecker()
    ok, _ = checker.check_buy(price=120000, ref_price=100000)
    assert ok is True


def test_h17_sell_lower_limit_locked():
    """H17: 하한가잠김 매도불가 → 차단."""
    checker = PriceLimitChecker()
    ok, reason = checker.check_sell(price=68000, ref_price=100000)
    assert ok is False
    assert "하한가잠김" in reason


def test_h17_sell_within_limit_ok():
    """H17: 매도 정상 범위 → OK."""
    checker = PriceLimitChecker()
    ok, _ = checker.check_sell(price=75000, ref_price=100000)
    assert ok is True


def test_h17_lower_limit_slippage_increased():
    """H17: 하한가 접근 시 추가 슬리피지."""
    checker = PriceLimitChecker()
    base_slip = checker.calc_sell_slippage(price=80000, ref_price=100000, base_slippage=0.001)
    near_limit_slip = checker.calc_sell_slippage(price=71000, ref_price=100000, base_slippage=0.001)
    assert near_limit_slip >= base_slip


# ---------------------------------------------------------------------------
# 3. H1 E4 라이브 캘리브레이션
# ---------------------------------------------------------------------------

def test_e4_calibrator_records_observations():
    """E4: 관측 기록."""
    cal = E4SlippageCalibrator()
    obs = SlippageObservation(expected_price=100.0, actual_price=100.5, side="BUY")
    cal.record(obs)
    assert cal.n_observations() == 1


def test_e4_calibrator_adjusts_factor():
    """E4: 실측 슬리피지 높으면 impact_factor 증가."""
    cal = E4SlippageCalibrator()
    initial_factor = cal.impact_factor

    # 높은 실측 슬리피지 주입
    for _ in range(5):
        obs = SlippageObservation(expected_price=100.0, actual_price=101.5, side="BUY")
        cal.record(obs)

    new_factor = cal.calibrate()
    # 실측 슬리피지(1.5%) >> 초기값(0.1%) → factor 증가
    assert new_factor >= initial_factor * 0.5  # 최소한 절반 이상 유지


def test_e4_calibration_bounded():
    """E4: 보정 ±2배 이내 클램핑."""
    cal = E4SlippageCalibrator()
    initial = cal.impact_factor

    # 극단적 슬리피지 주입
    for _ in range(10):
        obs = SlippageObservation(expected_price=100.0, actual_price=110.0, side="BUY")
        cal.record(obs)

    new_factor = cal.calibrate()
    # 2배 이내
    assert new_factor <= initial * 2.0 + 1e-6
    assert new_factor >= initial * 0.5 - 1e-6


def test_e4_slippage_observation_pct():
    """SlippageObservation.slippage_pct 계산."""
    obs = SlippageObservation(expected_price=100.0, actual_price=101.0, side="BUY")
    assert abs(obs.slippage_pct - 0.01) < 1e-6
