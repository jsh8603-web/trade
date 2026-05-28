"""stock/data/rate_tier.py — H30 데이터소스 rate-tier 공통 레이어 (SO-4/P4).

WHY: DART/FRED/ECOS/OpenBB 각각 API 한도(H30)가 있으나 공통 레이트리밋 없음.
     소스별 독립 토큰버킷 + jitter + 지수 백오프 + rotation(키/엔드포인트 풀) + tier 한도.
     KIS 레이트리밋(E1)과는 별개 — 데이터 조회 전용.

설계:
- RateTierConfig: 소스별 한도값 (DART 일, FRED ~120/min, ECOS, OpenBB)
- TokenBucket: 토큰버킷 (한도 초과 시 소진 상태 반환)
- DataSourceLimiter: 소스별 독립 토큰버킷 + jitter + 지수 백오프 + rotation
- RateTierRegistry: 전역 소스 레지스트리 (SO-1~3 provider 경유)
"""

from __future__ import annotations

import logging
import math
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("stock.data.rate_tier")


# ---------------------------------------------------------------------------
# Rate Tier Config — 소스별 한도 (OPEN ZONE — 키 발급 후 확정)
# ---------------------------------------------------------------------------

@dataclass
class RateTierConfig:
    """소스별 rate-tier 설정 (보수 기본값, 실 key 발급 후 조정 가능)."""
    requests_per_minute: float = 60.0    # 분당 요청 상한
    requests_per_day: Optional[float] = None   # 일 상한 (None=무제한)
    burst: int = 5                       # 버스트 허용 요청수
    min_interval_sec: float = 0.0        # 최소 요청 간격
    jitter_max_sec: float = 0.5          # 최대 jitter (랜덤 지연)
    max_backoff_sec: float = 60.0        # 최대 지수 백오프


# 소스별 기본 설정 (보수값 — OPEN ZONE)
SOURCE_CONFIGS: Dict[str, RateTierConfig] = {
    "DART": RateTierConfig(
        requests_per_minute=20.0,        # DART 공식 비공개, 보수 20/min
        requests_per_day=1000.0,         # 보수 일 1000
        burst=3,
        min_interval_sec=3.0,
        jitter_max_sec=1.0,
    ),
    "FRED": RateTierConfig(
        requests_per_minute=100.0,       # FRED ~120/min, 보수 100
        requests_per_day=None,
        burst=10,
        min_interval_sec=0.6,
        jitter_max_sec=0.2,
    ),
    "ECOS": RateTierConfig(
        requests_per_minute=10.0,        # ECOS 보수값 (키 발급 후 확인 필요)
        requests_per_day=500.0,
        burst=2,
        min_interval_sec=6.0,
        jitter_max_sec=1.0,
    ),
    "OPENBB": RateTierConfig(
        requests_per_minute=30.0,
        requests_per_day=None,
        burst=5,
        min_interval_sec=2.0,
        jitter_max_sec=0.5,
    ),
    "FDR": RateTierConfig(               # FinanceDataReader — 무료, 보수
        requests_per_minute=30.0,
        burst=5,
        min_interval_sec=2.0,
        jitter_max_sec=0.3,
    ),
    "PYKRX": RateTierConfig(             # pykrx KRX API
        requests_per_minute=20.0,
        burst=3,
        min_interval_sec=3.0,
        jitter_max_sec=0.5,
    ),
}


# ---------------------------------------------------------------------------
# TokenBucket — 소스별 분당 토큰버킷
# ---------------------------------------------------------------------------

class TokenBucket:
    """스레드 안전 토큰버킷 (분당·일별 이중 게이트)."""

    def __init__(self, config: RateTierConfig):
        self._cfg = config
        self._lock = threading.Lock()

        # 분 버킷
        self._tokens = float(config.burst)
        self._max_tokens = float(config.burst)
        self._refill_rate = config.requests_per_minute / 60.0  # tokens/sec
        self._last_refill = time.monotonic()

        # 일 버킷
        self._day_tokens: Optional[float] = config.requests_per_day
        self._day_start = time.time()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(
            self._max_tokens,
            self._tokens + elapsed * self._refill_rate,
        )
        self._last_refill = now

        # 일 버킷 리셋
        if self._cfg.requests_per_day is not None:
            wall = time.time()
            if wall - self._day_start >= 86400:
                self._day_tokens = self._cfg.requests_per_day
                self._day_start = wall

    def acquire(self) -> Tuple[bool, float]:
        """토큰 획득 시도.

        Returns:
            (success, wait_sec): success=True 즉시 진행, False → wait_sec 후 재시도.
        """
        with self._lock:
            self._refill()

            # 일 한도 체크
            if self._cfg.requests_per_day is not None:
                if self._day_tokens is not None and self._day_tokens < 1.0:
                    seconds_since_day = time.time() - self._day_start
                    wait = max(0.0, 86400.0 - seconds_since_day)
                    return False, wait

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                if self._cfg.requests_per_day is not None and self._day_tokens is not None:
                    self._day_tokens = max(0.0, self._day_tokens - 1.0)
                return True, 0.0
            else:
                # 얼마나 기다려야 토큰 1개 회복?
                wait = (1.0 - self._tokens) / self._refill_rate
                return False, wait

    def peek(self) -> bool:
        """토큰 소비 없이 가용 여부만 확인 (조회 전용 — is_any_exhausted 용)."""
        with self._lock:
            self._refill()
            if (self._cfg.requests_per_day is not None
                    and self._day_tokens is not None and self._day_tokens < 1.0):
                return False
            return self._tokens >= 1.0


# ---------------------------------------------------------------------------
# DataSourceLimiter — 소스별 단일 진입점
# ---------------------------------------------------------------------------

class DataSourceLimiter:
    """H30 데이터소스 rate-tier — 소스별 독립 토큰버킷 + jitter + 지수 백오프 + rotation.

    SO-1~3 provider가 경유하는 단일 레이트리밋 진입점.
    """

    def __init__(self, source: str, config: Optional[RateTierConfig] = None,
                 endpoints: Optional[List[str]] = None):
        self._source = source
        self._cfg = config or SOURCE_CONFIGS.get(source, RateTierConfig())
        self._bucket = TokenBucket(self._cfg)
        self._endpoints = endpoints or []
        self._endpoint_idx = 0
        self._fail_count = 0  # 연속 실패 수 (지수 백오프 기준)
        self._lock = threading.Lock()

    def acquire_with_backoff(
        self, max_retries: int = 5, timeout: float = 120.0
    ) -> bool:
        """토큰 획득 + jitter + 지수 백오프.

        Returns:
            True = 획득 성공, False = timeout 초과
        """
        deadline = time.monotonic() + timeout
        attempt = 0

        while time.monotonic() < deadline:
            ok, wait = self._bucket.acquire()
            if ok:
                # jitter 분산
                jitter = random.uniform(0.0, self._cfg.jitter_max_sec)
                if jitter > 0:
                    time.sleep(jitter)
                with self._lock:
                    self._fail_count = 0
                return True

            # 지수 백오프 + jitter
            backoff = min(
                self._cfg.max_backoff_sec,
                (2 ** attempt) * max(wait, 0.1),
            )
            jitter = random.uniform(0.0, backoff * 0.2)
            sleep_time = min(backoff + jitter, deadline - time.monotonic())
            if sleep_time <= 0:
                break

            logger.debug(
                "rate_tier %s 대기: %.2fs (attempt=%d, tokens_wait=%.2fs)",
                self._source, sleep_time, attempt, wait
            )
            time.sleep(sleep_time)
            attempt += 1

        logger.warning("rate_tier %s timeout 초과 (%.1fs)", self._source, timeout)
        self.on_error()
        return False

    def on_error(self) -> None:
        """API 오류 발생 시 실패 카운터 증가 (rotation trigger)."""
        with self._lock:
            self._fail_count += 1

    def rotate_endpoint(self) -> Optional[str]:
        """다음 엔드포인트/키로 rotation. 없으면 None."""
        if not self._endpoints:
            return None
        with self._lock:
            self._endpoint_idx = (self._endpoint_idx + 1) % len(self._endpoints)
            return self._endpoints[self._endpoint_idx]

    def current_endpoint(self) -> Optional[str]:
        if not self._endpoints:
            return None
        return self._endpoints[self._endpoint_idx % len(self._endpoints)]

    @property
    def source(self) -> str:
        return self._source


# ---------------------------------------------------------------------------
# RateTierRegistry — 전역 소스 레지스트리
# ---------------------------------------------------------------------------

class RateTierRegistry:
    """소스별 DataSourceLimiter 전역 관리. SO-1~3 provider에서 경유."""

    _instance: Optional["RateTierRegistry"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._limiters: Dict[str, DataSourceLimiter] = {}
        self._reg_lock = threading.Lock()

    @classmethod
    def get(cls) -> "RateTierRegistry":
        """싱글톤 접근."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_limiter(self, source: str) -> DataSourceLimiter:
        with self._reg_lock:
            if source not in self._limiters:
                self._limiters[source] = DataSourceLimiter(source)
            return self._limiters[source]

    def register(self, source: str, config: RateTierConfig,
                 endpoints: Optional[List[str]] = None) -> DataSourceLimiter:
        """커스텀 설정으로 limiter 등록."""
        with self._reg_lock:
            limiter = DataSourceLimiter(source, config, endpoints)
            self._limiters[source] = limiter
            return limiter

    def is_any_exhausted(self) -> bool:
        """어떤 소스든 일 한도 소진 여부."""
        with self._reg_lock:
            for limiter in self._limiters.values():
                if not limiter._bucket.peek():
                    return True
        return False
