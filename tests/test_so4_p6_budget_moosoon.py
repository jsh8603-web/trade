"""tests/test_so4_p6_budget_moosoon.py — SO-4/P6 모순1 풀메커니즘 + N3/rpm_limit 검증.

검증 기준 (harness2.md SO-4):
1. 예산 소진→재시도/예약 vs degrade→abstain 사유분류
2. 점수 sat(gap)×pos×regime_mult 적용 (급락폭 지배 안함)
3. crash reserve 레짐조건부 트랜치
4. N3 retry (예외→max_retries 재시도)·rpm_limit (RPM 초과→rate-limit)
5. e^|Drop| 지수증폭·soft limit 기각
"""

from __future__ import annotations

import pytest

from core.budget_ledger import (
    BudgetLedger,
    BucketType,
    N3RetryPolicy,
    get_crash_reserve_tranche,
    score_sat,
)


# ---------------------------------------------------------------------------
# 1. 예산 소진 → 버킷 분류
# ---------------------------------------------------------------------------

def test_budget_normal_reservation():
    """정상 예약 → NORMAL 버킷."""
    ledger = BudgetLedger(total_budget=1000.0)
    ok, bucket = ledger.reserve("stock_kr", 100.0, "매수")
    assert ok is True
    assert bucket == BucketType.NORMAL


def test_budget_partial_exhaustion_retry():
    """부분 가용 예산 → RETRY_RESERVE."""
    ledger = BudgetLedger(total_budget=100.0)
    ledger.reserve("stock_kr", 90.0)   # 90 예약
    ok, bucket = ledger.reserve("stock_us", 50.0)  # 50 요청 (잔여 10)
    assert ok is False
    assert bucket == BucketType.RETRY_RESERVE


def test_budget_full_exhaustion_degrade():
    """예산 완전 소진 → DEGRADE abstain."""
    ledger = BudgetLedger(total_budget=100.0)
    ledger.reserve("stock_kr", 100.0)
    ok, bucket = ledger.reserve("stock_us", 10.0)
    assert ok is False
    assert bucket == BucketType.DEGRADE


def test_budget_consume_reduces_reserved():
    """consume → 예약→소비 전환 (총 사용량 동일, 잔여는 reserve와 동일)."""
    ledger = BudgetLedger(total_budget=1000.0)
    ledger.reserve("bond", 200.0)
    # 예약 후 잔여: 800
    assert ledger.remaining() == pytest.approx(800.0, abs=1.0)
    ledger.consume("bond", 150.0)
    # consume은 reserve→consumed 전환 (총 사용량 200 유지)
    assert ledger.remaining() == pytest.approx(800.0, abs=1.0)


def test_budget_release_restores():
    """release → 예약 해제 → 잔여 증가."""
    ledger = BudgetLedger(total_budget=500.0)
    ledger.reserve("gold", 200.0)
    ledger.release("gold", 200.0)
    assert ledger.remaining() == pytest.approx(500.0, abs=1.0)


def test_budget_classify_bucket():
    """classify_bucket: 잔여에 따른 사전 분류."""
    ledger = BudgetLedger(total_budget=100.0)
    assert ledger.classify_bucket(50.0) == BucketType.NORMAL
    ledger.reserve("x", 90.0)
    assert ledger.classify_bucket(50.0) == BucketType.RETRY_RESERVE
    ledger.reserve("y", 10.0)
    assert ledger.classify_bucket(1.0) == BucketType.DEGRADE


# ---------------------------------------------------------------------------
# 2. 점수 sat(gap)×pos×regime_mult — 급락폭 지배 금지
# ---------------------------------------------------------------------------

def test_score_sat_basic():
    """score_sat 기본 동작."""
    s = score_sat(gap=0.3, pos_weight=0.5, regime_mult=1.0)
    assert 0.0 <= s <= 1.0


def test_score_sat_crash_not_dominant():
    """급락폭이 점수를 지배하지 않음 — 기여 상한 이하."""
    # crash_drop=100% 이어도 기여 ≤ max_crash_contribution=0.2
    s_no_crash = score_sat(gap=0.3, pos_weight=0.5, regime_mult=1.0, crash_drop_pct=0.0)
    s_crash = score_sat(gap=0.3, pos_weight=0.5, regime_mult=1.0, crash_drop_pct=100.0)
    diff = s_crash - s_no_crash
    assert diff <= 0.2, f"급락폭 기여 {diff:.3f} > 0.2 (지배)"


def test_score_no_exp_amplification():
    """e^|gap| 지수증폭 사용 안 함 — gap=10이어도 점수≤1."""
    s = score_sat(gap=10.0, pos_weight=1.0, regime_mult=1.0)
    assert s <= 1.0  # 지수증폭이면 1 초과 가능


def test_score_zero_pos_weight():
    """pos_weight=0 → 점수=0."""
    s = score_sat(gap=0.5, pos_weight=0.0, regime_mult=1.0)
    assert s == pytest.approx(0.0, abs=0.01)


def test_score_regime_mult_scales():
    """regime_mult↑ → 점수 증가."""
    s1 = score_sat(gap=0.3, pos_weight=0.5, regime_mult=0.5)
    s2 = score_sat(gap=0.3, pos_weight=0.5, regime_mult=1.5)
    assert s2 > s1


# ---------------------------------------------------------------------------
# 3. crash reserve 레짐 조건부 트랜치
# ---------------------------------------------------------------------------

def test_crash_reserve_stagflation_highest():
    """Stagflation → 가장 높은 crash reserve."""
    r_stag = get_crash_reserve_tranche("STAGFLATION")
    r_rec = get_crash_reserve_tranche("RECOVERY")
    assert r_stag > r_rec


def test_crash_reserve_values_valid():
    """모든 레짐 crash reserve ∈ [0, 1]."""
    for regime in ["STAGFLATION", "REFLATION", "OVERHEAT", "RECOVERY"]:
        r = get_crash_reserve_tranche(regime)
        assert 0.0 <= r <= 1.0, f"{regime}: {r}"


def test_crash_reserve_unknown_fallback():
    """알 수 없는 레짐 → 기본값 반환."""
    r = get_crash_reserve_tranche("UNKNOWN_REGIME")
    assert 0.0 <= r <= 1.0


# ---------------------------------------------------------------------------
# 4. N3 retry + rpm_limit
# ---------------------------------------------------------------------------

def test_n3_retry_succeeds_eventually():
    """N3: 처음 2회 실패, 3번째 성공."""
    policy = N3RetryPolicy(max_retries=3, rpm_limit=100)
    call_count = [0]

    def flaky_fn():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError("일시적 오류")
        return "success"

    # time.sleep을 mock해서 빠르게 실행
    import unittest.mock as mock
    with mock.patch("time.sleep"):
        result = policy.execute_with_retry(flaky_fn)

    assert result == "success"
    assert call_count[0] == 3


def test_n3_retry_all_fail_raises():
    """N3: max_retries 초과 → 예외 전파."""
    policy = N3RetryPolicy(max_retries=2, rpm_limit=100)
    import unittest.mock as mock

    with mock.patch("time.sleep"):
        with pytest.raises(Exception):
            policy.execute_with_retry(lambda: (_ for _ in ()).throw(RuntimeError("항상 실패")))


def test_rpm_limit_blocks():
    """RPM rate-limit: 분당 2회 설정 시 3번째 차단."""
    policy = N3RetryPolicy(max_retries=0, rpm_limit=2)
    assert policy.check_rate_limit() is True   # 1회
    assert policy.check_rate_limit() is True   # 2회
    assert policy.check_rate_limit() is False  # 3회 차단


def test_n3_retry_success_no_retry():
    """N3: 즉시 성공 → 재시도 없음."""
    policy = N3RetryPolicy(max_retries=3, rpm_limit=100)
    call_count = [0]

    def success_fn():
        call_count[0] += 1
        return 42

    result = policy.execute_with_retry(success_fn)
    assert result == 42
    assert call_count[0] == 1


# ---------------------------------------------------------------------------
# 5. e^|Drop|/soft-limit 기각 검증 (code grep)
# ---------------------------------------------------------------------------

def test_no_exp_drop_in_code():
    """budget_ledger.py에 e^|Drop| 패턴 없음."""
    import pathlib
    src = pathlib.Path("core/budget_ledger.py").read_text(encoding="utf-8")
    assert "math.exp(abs" not in src  # e^|Drop| 기각
    assert "exp(drop" not in src.lower()
    assert "exp(crash" not in src.lower()
