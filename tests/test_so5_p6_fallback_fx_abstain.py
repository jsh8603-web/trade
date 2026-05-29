"""tests/test_so5_p6_fallback_fx_abstain.py — SO-5/P6 H27+H26+H29 검증.

검증 기준 (harness2.md SO-5):
1. H27: 야간 컨펌 N시간 미수신→bounded 축소(전량청산 회피)
2. H26: 야간 FX stale→고정환율로 가짜 kill-switch 미발동
3. H29: macro 종료→abstain+청산/리밸런싱 정상
"""

from __future__ import annotations

import time
import pytest

from core.fallback_policy import (
    H27BoundedFallback,
    H26FxGuard,
    H29MacroAbstain,
    BoundedFallbackResult,
)


# ---------------------------------------------------------------------------
# H27 bounded auto-fallback
# ---------------------------------------------------------------------------

def test_h27_no_trigger_within_timeout():
    """컨펌 정상 → fallback 미발동."""
    fb = H27BoundedFallback(timeout_hours=1.0)
    fb.record_confirm()
    result = fb.check_timeout()
    assert result.triggered is False
    assert result.reduction_ratio == 0.0


def test_h27_triggers_after_timeout():
    """1차 타임아웃 초과 → bounded 축소 발동 (current_ts 직접 주입)."""
    fb = H27BoundedFallback(timeout_hours=1.0, reduction_step=0.25)
    fb.record_confirm()
    # 1시간 후 시뮬
    future_ts = fb._last_confirm_ts + 3601.0
    result = fb.check_timeout(current_ts=future_ts)
    assert result.triggered is True
    assert result.reduction_ratio == pytest.approx(0.25)
    assert result.is_full_liquidation is False


def test_h27_secondary_threshold_higher_reduction():
    """2차 임계 초과 → 더 높은 축소율 (current_ts 직접 주입)."""
    fb = H27BoundedFallback(
        timeout_hours=1.0,
        secondary_hours=2.0,
        reduction_step=0.25,
        secondary_reduction=0.50
    )
    fb.record_confirm()
    # 2시간 후 시뮬
    future_ts = fb._last_confirm_ts + 7201.0
    result = fb.check_timeout(current_ts=future_ts)
    assert result.triggered is True
    assert result.reduction_ratio == pytest.approx(0.50)


def test_h27_never_full_liquidation():
    """H27: is_full_liquidation 항상 False."""
    fb = H27BoundedFallback(timeout_hours=0.0001)
    fb.record_confirm()
    time.sleep(0.01)
    result = fb.check_timeout()
    assert result.is_full_liquidation is False


def test_h27_no_confirm_recorded():
    """컨펌 기록 없음 → 미발동 (첫 사이클 보호)."""
    fb = H27BoundedFallback()
    result = fb.check_timeout()
    assert result.triggered is False


# ---------------------------------------------------------------------------
# H26 FX 고정환율
# ---------------------------------------------------------------------------

def test_h26_market_hours_use_live():
    """정규장 → live_rate 사용."""
    guard = H26FxGuard(last_close_rate=1350.0)
    rate = guard.get_safe_rate(live_rate=1380.0, is_market_hours=True)
    assert rate == pytest.approx(1380.0)


def test_h26_night_hours_use_close():
    """야간 → 직전 마감율 사용."""
    guard = H26FxGuard(last_close_rate=1350.0)
    rate = guard.get_safe_rate(live_rate=1450.0, is_market_hours=False)
    assert rate == pytest.approx(1350.0)  # 야간 급변 무시


def test_h26_stale_none_use_close():
    """live_rate=None(stale) → 직전 마감율."""
    guard = H26FxGuard(last_close_rate=1320.0)
    rate = guard.get_safe_rate(live_rate=None, is_market_hours=True)
    assert rate == pytest.approx(1320.0)


def test_h26_update_close_rate():
    """마감 환율 갱신."""
    guard = H26FxGuard(last_close_rate=1300.0)
    guard.update_close_rate(1370.0)
    assert guard.last_close_rate == pytest.approx(1370.0)


def test_h26_night_no_fake_kill_switch():
    """야간 FX 급변 → 마감율 고정으로 MDD 오계산 방지."""
    guard = H26FxGuard(last_close_rate=1350.0)
    # 야간에 FX 급등(USD강세) 시뮬
    night_rate = guard.get_safe_rate(live_rate=1600.0, is_market_hours=False)
    # 마감율 그대로 → MDD 계산에 영향 없음
    assert night_rate == pytest.approx(1350.0)
    assert night_rate != pytest.approx(1600.0)


# ---------------------------------------------------------------------------
# H29 macro abstain
# ---------------------------------------------------------------------------

def test_h29_buy_blocked_when_unavailable():
    """macro unavailable → buy→abstain."""
    abstain = H29MacroAbstain()
    abstain.set_status("unavailable", "macro 종료")
    action = abstain.filter_action("buy")
    assert action == "abstain"
    assert abstain.should_abstain is True


def test_h29_sell_allowed_when_unavailable():
    """macro unavailable이어도 sell 정상."""
    abstain = H29MacroAbstain()
    abstain.set_status("unavailable")
    action = abstain.filter_action("sell")
    assert action == "sell"


def test_h29_hold_allowed_when_unavailable():
    """macro unavailable이어도 hold 정상."""
    abstain = H29MacroAbstain()
    abstain.set_status("error")
    action = abstain.filter_action("hold")
    assert action == "hold"


def test_h29_buy_allowed_when_fresh():
    """macro fresh → buy 정상."""
    abstain = H29MacroAbstain()
    abstain.set_status("fresh")
    action = abstain.filter_action("buy")
    assert action == "buy"
    assert abstain.should_abstain is False


def test_h29_status_recovery():
    """unavailable → fresh 복구."""
    abstain = H29MacroAbstain()
    abstain.set_status("unavailable")
    assert abstain.should_abstain is True
    abstain.set_status("fresh")
    assert abstain.should_abstain is False
