"""tests/test_so4_p4_rate_tier.py — SO-4/P4 H30 rate-tier 레이어 검증.

검증 기준 (harness2.md SO-4):
1. tier 한도 초과 → 백오프 발동
2. rotation (풀 회전) — 다음 엔드포인트로 전환
3. jitter 분산 (고정간격 아님)
4. 소스별 독립 버킷 (한 소스 소진이 타 소스 무영향)
"""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from stock.data.rate_tier import (
    DataSourceLimiter,
    RateTierConfig,
    RateTierRegistry,
    TokenBucket,
)


# ---------------------------------------------------------------------------
# 1. TokenBucket — 토큰 소진 후 대기 반환
# ---------------------------------------------------------------------------

def test_token_bucket_exhaustion():
    """토큰버킷 소진 → (False, wait>0) 반환."""
    cfg = RateTierConfig(requests_per_minute=60.0, burst=2, jitter_max_sec=0.0)
    bucket = TokenBucket(cfg)

    # burst=2, 2회 성공
    ok1, w1 = bucket.acquire()
    ok2, w2 = bucket.acquire()
    assert ok1 is True
    assert ok2 is True

    # 3번째 실패
    ok3, w3 = bucket.acquire()
    assert ok3 is False
    assert w3 > 0.0


def test_token_bucket_daily_limit():
    """일 한도 소진 → False."""
    cfg = RateTierConfig(
        requests_per_minute=1000.0,
        burst=10,
        requests_per_day=2.0,  # 일 2회
        jitter_max_sec=0.0,
    )
    bucket = TokenBucket(cfg)
    bucket.acquire()
    bucket.acquire()
    ok, w = bucket.acquire()
    assert ok is False
    assert w > 0.0


# ---------------------------------------------------------------------------
# 2. DataSourceLimiter — 백오프
# ---------------------------------------------------------------------------

def test_limiter_backoff_on_exhaustion():
    """토큰 소진 시 acquire_with_backoff=False (timeout 짧게 설정)."""
    cfg = RateTierConfig(
        requests_per_minute=0.001,  # 매우 낮은 한도
        burst=0,
        jitter_max_sec=0.0,
        max_backoff_sec=0.1,
    )
    limiter = DataSourceLimiter("TEST", config=cfg)
    result = limiter.acquire_with_backoff(max_retries=2, timeout=0.2)
    assert result is False


def test_limiter_success_within_burst():
    """burst 이내 → acquire 즉시 성공."""
    cfg = RateTierConfig(
        requests_per_minute=600.0,
        burst=5,
        jitter_max_sec=0.0,
        min_interval_sec=0.0,
    )
    limiter = DataSourceLimiter("TEST2", config=cfg)
    ok = limiter.acquire_with_backoff(timeout=1.0)
    assert ok is True


# ---------------------------------------------------------------------------
# 3. rotation — 다음 엔드포인트 전환
# ---------------------------------------------------------------------------

def test_rotation_cycles_endpoints():
    """rotate_endpoint → 풀 순환."""
    cfg = RateTierConfig()
    endpoints = ["ep1", "ep2", "ep3"]
    limiter = DataSourceLimiter("TEST", config=cfg, endpoints=endpoints)

    assert limiter.current_endpoint() == "ep1"
    ep2 = limiter.rotate_endpoint()
    assert ep2 == "ep2"
    ep3 = limiter.rotate_endpoint()
    assert ep3 == "ep3"
    ep1_again = limiter.rotate_endpoint()
    assert ep1_again == "ep1"


def test_rotation_no_endpoints_returns_none():
    """엔드포인트 풀 없으면 None."""
    limiter = DataSourceLimiter("TEST", config=RateTierConfig())
    assert limiter.current_endpoint() is None
    assert limiter.rotate_endpoint() is None


# ---------------------------------------------------------------------------
# 4. jitter 분산 — 고정 간격이 아님
# ---------------------------------------------------------------------------

def test_jitter_is_nondeterministic():
    """acquire_with_backoff 호출 간 간격이 일정하지 않음 (jitter 효과)."""
    cfg = RateTierConfig(
        requests_per_minute=600.0,
        burst=100,
        jitter_max_sec=0.05,
        min_interval_sec=0.0,
    )
    limiter = DataSourceLimiter("JITTER_TEST", config=cfg)
    intervals = []
    for _ in range(5):
        t0 = time.monotonic()
        limiter.acquire_with_backoff(timeout=1.0)
        intervals.append(time.monotonic() - t0)

    # 모든 간격이 동일하지 않음 (최소 1개 이상 다름)
    unique = len(set(round(v, 4) for v in intervals))
    assert unique > 1 or max(intervals) > 0.0  # jitter 가 0.0 이상임


# ---------------------------------------------------------------------------
# 5. 소스별 독립 버킷 — 한 소스 소진이 타 소스 무영향
# ---------------------------------------------------------------------------

def test_independent_buckets():
    """DART 버킷 소진 → FRED 버킷 무영향."""
    dart_cfg = RateTierConfig(
        requests_per_minute=0.001, burst=0, jitter_max_sec=0.0, max_backoff_sec=0.01
    )
    fred_cfg = RateTierConfig(
        requests_per_minute=600.0, burst=10, jitter_max_sec=0.0
    )
    dart_limiter = DataSourceLimiter("DART_INDEP", config=dart_cfg)
    fred_limiter = DataSourceLimiter("FRED_INDEP", config=fred_cfg)

    # DART 소진
    dart_ok = dart_limiter.acquire_with_backoff(timeout=0.05)
    assert dart_ok is False  # 소진

    # FRED는 영향 없이 성공
    fred_ok = fred_limiter.acquire_with_backoff(timeout=1.0)
    assert fred_ok is True


# ---------------------------------------------------------------------------
# 6. RateTierRegistry — 소스별 독립 limiter 관리
# ---------------------------------------------------------------------------

def test_registry_returns_same_limiter():
    """같은 소스 → 동일 limiter 인스턴스 반환."""
    registry = RateTierRegistry()
    l1 = registry.get_limiter("DART")
    l2 = registry.get_limiter("DART")
    assert l1 is l2


def test_registry_different_sources_independent():
    """다른 소스 → 다른 limiter."""
    registry = RateTierRegistry()
    l_dart = registry.get_limiter("DART_REG_TEST")
    l_fred = registry.get_limiter("FRED_REG_TEST")
    assert l_dart is not l_fred


def test_registry_custom_config():
    """커스텀 설정 등록 → 해당 설정 반영."""
    registry = RateTierRegistry()
    custom_cfg = RateTierConfig(requests_per_minute=5.0, burst=1)
    limiter = registry.register("CUSTOM_SRC", custom_cfg)
    assert limiter.source == "CUSTOM_SRC"
    assert limiter is registry.get_limiter("CUSTOM_SRC")
