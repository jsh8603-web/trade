"""core/budget_ledger.py — 모순1 풀메커니즘 + N3/rpm_limit retry (SO-4/P6).

WHY: 모순1(review-findings §4) 기각 항목:
  - e^|Drop| 지수증폭 금지 (급락폭 지배 금지)
  - soft limit 초과호출 기각

3버킷:
  - 정상(normal): 큐 처리
  - 429/예산소진(retry_reserve): 재시도/예약
  - degrade(abstain): abstain 사유분류

예산 ledger C-lite:
  - 정책=트랙 도메인 risk_gate
  - 회계=LLMRouter reserve/consume/remaining

N3 retry + rpm_limit 이식:
  - gemini_client max_retries=3 패턴
  - RPM rate-limit 10/min 패턴
"""

from __future__ import annotations

import logging
import math
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("core.budget_ledger")


# ---------------------------------------------------------------------------
# 3버킷 enum
# ---------------------------------------------------------------------------

class BucketType(Enum):
    NORMAL = auto()           # 정상 — 큐 처리
    RETRY_RESERVE = auto()    # 429/예산소진 — 재시도/예약
    DEGRADE = auto()          # degrade → abstain


# ---------------------------------------------------------------------------
# 점수 함수 sat(gap)×pos×regime_mult (모순1: 급락폭 지배 금지)
# ---------------------------------------------------------------------------

def score_sat(
    gap: float,             # 가치 갭 (valuation_gap): ≥0
    pos_weight: float,      # 포지션 비중: [0,1]
    regime_mult: float,     # 레짐 배수: ≥0
    crash_drop_pct: float = 0.0,   # 급락폭(% 절대값) — quick proxy만, 지배 금지
    max_crash_contribution: float = 0.2,  # 급락폭 기여 상한 (지배 차단)
) -> float:
    """모순1 점수 함수.

    sat(gap): 포화 함수 (0~1, 급락폭 기반 지수증폭 e^|Drop| 기각).
    급락폭은 quick proxy로만 사용 — 기여 상한 max_crash_contribution 이하.

    ⛔ 기각: e^|gap| 지수증폭. soft limit 초과호출.
    """
    # sat(gap) = 1 - exp(-gap * k) — 포화 함수, 급락폭 미사용
    k = 3.0  # 포화 속도 (OPEN ZONE)
    sat = 1.0 - math.exp(-gap * k)
    sat = max(0.0, min(1.0, sat))

    # 급락폭 quick proxy (지배 차단: 기여 ≤ max_crash_contribution)
    crash_contribution = min(
        max_crash_contribution,
        crash_drop_pct / 100.0 * 0.1  # 급락폭 100% = 기여 0.1
    )

    base_score = sat * pos_weight * regime_mult
    # crash_contribution 은 작은 보정만 (지배 금지)
    return max(0.0, min(1.0, base_score + crash_contribution))


# ---------------------------------------------------------------------------
# Crash Reserve — 레짐 조건부 예약 트랜치
# ---------------------------------------------------------------------------

CRASH_RESERVE_TABLE: Dict[str, float] = {
    "STAGFLATION": 0.15,   # 15% 현금 예약
    "REFLATION":   0.10,
    "OVERHEAT":    0.08,
    "RECOVERY":    0.05,
    "UNKNOWN":     0.08,   # 기본
}


def get_crash_reserve_tranche(regime_label: str) -> float:
    """레짐 → crash reserve 트랜치 % 반환."""
    return CRASH_RESERVE_TABLE.get(regime_label.upper(), CRASH_RESERVE_TABLE["UNKNOWN"])


# ---------------------------------------------------------------------------
# N3 retry 패턴 (gemini_client max_retries=3)
# ---------------------------------------------------------------------------

class N3RetryPolicy:
    """gemini_client max_retries=3 패턴 이식.

    예외 발생 시 max_retries 까지 지수 백오프로 재시도.
    rpm_limit: 분당 10회 초과 시 rate-limit 대기.
    """

    def __init__(self, max_retries: int = 3, rpm_limit: int = 10):
        self._max_retries = max_retries
        self._rpm_limit = rpm_limit
        self._call_times: List[float] = []
        self._lock = threading.Lock()

    def check_rate_limit(self) -> bool:
        """RPM rate-limit 체크. True=통과, False=차단."""
        with self._lock:
            now = time.monotonic()
            # 1분 내 호출 수 집계
            self._call_times = [t for t in self._call_times if now - t < 60.0]
            if len(self._call_times) >= self._rpm_limit:
                return False
            self._call_times.append(now)
            return True

    def execute_with_retry(self, fn, *args, **kwargs):
        """max_retries=3 지수 백오프 재시도."""
        last_exc = None
        for attempt in range(self._max_retries + 1):
            if not self.check_rate_limit():
                logger.warning("N3: RPM rate-limit 초과 — 대기 후 재시도 attempt=%d", attempt)
                time.sleep(6.0)  # 10/min → 6s 간격
                if not self.check_rate_limit():
                    raise RuntimeError("RPM rate-limit: 재시도 실패")

            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    wait = (2 ** attempt) * 1.0
                    logger.warning("N3: 예외 attempt=%d → %.1fs 후 재시도: %s", attempt, wait, exc)
                    time.sleep(wait)
                else:
                    logger.error("N3: %d회 재시도 모두 실패: %s", self._max_retries, exc)
        raise last_exc


# ---------------------------------------------------------------------------
# BudgetLedger C-lite
# ---------------------------------------------------------------------------

@dataclass
class LedgerEntry:
    """예산 소비 레코드."""
    track: str
    action: str          # "reserve" | "consume" | "release"
    amount: float
    reason: str
    bucket: BucketType
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BudgetLedger:
    """예산 ledger C-lite — 정책=트랙 도메인, 회계=LLMRouter reserve/consume/remaining.

    3버킷 분류:
    - NORMAL: 정상 처리
    - RETRY_RESERVE: 429/예산소진 → 재시도/예약
    - DEGRADE: degrade → abstain 사유분류
    """

    def __init__(self, total_budget: float = 1000.0):
        self._total = total_budget
        self._reserved: Dict[str, float] = {}    # track → 예약량
        self._consumed: Dict[str, float] = {}    # track → 소비량
        self._log: List[LedgerEntry] = []
        self._lock = threading.Lock()

    def reserve(self, track: str, amount: float, reason: str = "") -> Tuple[bool, BucketType]:
        """예산 예약. 부족 시 RETRY_RESERVE 또는 DEGRADE."""
        with self._lock:
            current_reserved = sum(self._reserved.values())
            current_consumed = sum(self._consumed.values())
            available = self._total - current_reserved - current_consumed

            if available >= amount:
                self._reserved[track] = self._reserved.get(track, 0.0) + amount
                entry = LedgerEntry(track, "reserve", amount, reason, BucketType.NORMAL)
                self._log.append(entry)
                return True, BucketType.NORMAL
            elif available > 0:
                # 부분 예약 → RETRY_RESERVE
                partial = available
                self._reserved[track] = self._reserved.get(track, 0.0) + partial
                entry = LedgerEntry(track, "reserve", partial,
                                    f"{reason} [partial={partial:.1f}]", BucketType.RETRY_RESERVE)
                self._log.append(entry)
                logger.warning("BudgetLedger: 부분 예약 track=%s amount=%.1f→%.1f (RETRY_RESERVE)",
                               track, amount, partial)
                return False, BucketType.RETRY_RESERVE
            else:
                # 예산 완전 소진 → DEGRADE
                entry = LedgerEntry(track, "reserve", 0.0,
                                    f"{reason} [exhausted]", BucketType.DEGRADE)
                self._log.append(entry)
                logger.warning("BudgetLedger: 예산 소진 track=%s → DEGRADE abstain", track)
                return False, BucketType.DEGRADE

    def consume(self, track: str, amount: float, reason: str = "") -> None:
        """예약을 실 소비로 전환."""
        with self._lock:
            reserved = self._reserved.get(track, 0.0)
            actual = min(amount, reserved)
            self._reserved[track] = max(0.0, reserved - actual)
            self._consumed[track] = self._consumed.get(track, 0.0) + actual
            self._log.append(LedgerEntry(track, "consume", actual, reason, BucketType.NORMAL))

    def release(self, track: str, amount: float, reason: str = "") -> None:
        """예약 해제 (주문 취소/미체결)."""
        with self._lock:
            self._reserved[track] = max(0.0, self._reserved.get(track, 0.0) - amount)
            self._log.append(LedgerEntry(track, "release", amount, reason, BucketType.NORMAL))

    def remaining(self, track: Optional[str] = None) -> float:
        """잔여 예산."""
        with self._lock:
            used = sum(self._reserved.values()) + sum(self._consumed.values())
            return max(0.0, self._total - used)

    def classify_bucket(self, amount: float) -> BucketType:
        """요청 금액에 따른 버킷 사전 분류."""
        if self.remaining() >= amount:
            return BucketType.NORMAL
        elif self.remaining() > 0:
            return BucketType.RETRY_RESERVE
        return BucketType.DEGRADE

    @property
    def log(self) -> List[LedgerEntry]:
        return list(self._log)
