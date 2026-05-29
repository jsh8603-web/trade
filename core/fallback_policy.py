"""core/fallback_policy.py — H27 bounded fallback + H26 FX + H29 macro abstain (SO-5/P6).

WHY:
- H27: KillSwitch(confirm_pending) 타임아웃 → bounded auto-fallback (전량청산 아님)
- H26: 야간 FX stale → 직전 정규장 마감율 사용 (가짜 kill-switch MDD 방지)
- H29: macro 종료 → generate_candidate abstain (신규매수 차단) + 청산/리밸런싱 정상
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("core.fallback_policy")


# ---------------------------------------------------------------------------
# H27 bounded auto-fallback (KillSwitch confirm_pending 타임아웃)
# ---------------------------------------------------------------------------

@dataclass
class BoundedFallbackResult:
    """H27 bounded fallback 결과."""
    triggered: bool
    reduction_ratio: float   # 0~1, 0=무동작, 0.5=50% 축소
    reason: str
    is_full_liquidation: bool = False  # 항상 False (전량청산 금지)


class H27BoundedFallback:
    """H27: KillSwitch confirm_pending N시간 미수신 → 시간분산 축소.

    전량청산(full liquidation) 금지. 2차 임계 초과 시 추가 축소만.
    Phase2 KillSwitch 본체 미변경 — 타임아웃 wire만.

    무인(unattended) 자동발동:
      - attended: record_confirm() 후 confirm 미수신 시 타임아웃 시작.
      - unattended: confirm 없음 → record_halt_entry(ts) 로 halt 진입 시점부터 타임아웃 카운트.
        anchor = _last_confirm_ts if not None else _halt_anchor_ts
    """

    def __init__(
        self,
        timeout_hours: float = 4.0,       # 1차: N시간 미수신 → 축소 시작
        secondary_hours: float = 8.0,     # 2차: 추가 축소
        reduction_step: float = 0.25,     # 1차 축소율 25%
        secondary_reduction: float = 0.50,  # 2차 축소율 50%
    ):
        self._timeout_sec = timeout_hours * 3600
        self._secondary_sec = secondary_hours * 3600
        self._reduction_step = reduction_step
        self._secondary_reduction = secondary_reduction
        self._last_confirm_ts: Optional[float] = None
        self._halt_anchor_ts: Optional[float] = None  # SO-6: 무인 halt 진입 시점

    def record_confirm(self) -> None:
        """KillSwitch confirm 수신 시 타임스탬프 기록 (attended 경로)."""
        self._last_confirm_ts = time.monotonic()
        self._halt_anchor_ts = None  # confirm 이후 halt anchor 리셋

    def record_halt_entry(self, ts: Optional[float] = None) -> None:
        """SO-6: KillSwitch HALT 진입 시점 기록 (무인 타임아웃 anchor).

        무인 모드에서는 confirm() 이 없으므로, halt 진입 시점부터 타임아웃 카운트.
        attended 경로 (record_confirm 기록 있음) 는 이 anchor 를 사용하지 않음.
        """
        if self._halt_anchor_ts is None:  # 첫 halt 진입만 기록 (재진입 초기화 방지)
            self._halt_anchor_ts = ts if ts is not None else time.monotonic()
            logger.info("H27: halt anchor 기록 ts=%.1f (무인 타임아웃 기산점)", self._halt_anchor_ts)

    def check_timeout(self, current_ts: Optional[float] = None) -> BoundedFallbackResult:
        """타임아웃 체크 → bounded 축소 결정.

        anchor 우선순위:
          1) _last_confirm_ts (attended: confirm 이후 경과)
          2) _halt_anchor_ts (unattended: halt 진입 이후 경과)
          3) None → 대기 (아무 anchor 없음)

        Returns:
            BoundedFallbackResult(triggered, reduction_ratio, reason)
        """
        # anchor 결정: confirm 우선, 없으면 halt anchor (무인 자동발동)
        anchor = self._last_confirm_ts if self._last_confirm_ts is not None else self._halt_anchor_ts
        if anchor is None:
            return BoundedFallbackResult(False, 0.0, "컨펌/halt anchor 없음 — 대기")

        now = current_ts or time.monotonic()
        elapsed = now - anchor
        anchor_kind = "confirm" if self._last_confirm_ts is not None else "halt_entry"

        if elapsed >= self._secondary_sec:
            return BoundedFallbackResult(
                triggered=True,
                reduction_ratio=self._secondary_reduction,
                reason=f"H27: 2차 임계 {self._secondary_sec/3600:.0f}h 초과 → {self._secondary_reduction*100:.0f}% 축소 (anchor={anchor_kind})",
                is_full_liquidation=False,
            )
        elif elapsed >= self._timeout_sec:
            return BoundedFallbackResult(
                triggered=True,
                reduction_ratio=self._reduction_step,
                reason=f"H27: {self._timeout_sec/3600:.0f}h 미수신 → {self._reduction_step*100:.0f}% 축소 (anchor={anchor_kind})",
                is_full_liquidation=False,
            )
        return BoundedFallbackResult(False, 0.0, f"컨펌 정상 (anchor={anchor_kind})", is_full_liquidation=False)


# ---------------------------------------------------------------------------
# H26 FX 고정환율 (야간 stale → 직전 정규장 마감율)
# ---------------------------------------------------------------------------

class H26FxGuard:
    """H26: 야간 FX stale 시 직전 정규장 마감율 사용.

    가짜 MDD 방지 — FX 급변으로 인한 kill-switch 오발동 차단.
    US 장 정규시간(한국 22:30~05:00 = UTC 13:30~20:00)이 아니면 stale 처리.
    """

    def __init__(self, last_close_rate: float = 1350.0):
        self._last_close_rate = last_close_rate
        self._last_close_ts: Optional[datetime] = None

    def update_close_rate(self, rate: float, ts: Optional[datetime] = None) -> None:
        """정규장 마감 시 환율 갱신."""
        self._last_close_rate = rate
        self._last_close_ts = ts or datetime.now(timezone.utc)
        logger.debug("H26: 마감 환율 갱신 %.2f", rate)

    def get_safe_rate(
        self,
        live_rate: Optional[float],
        is_market_hours: bool,
    ) -> float:
        """야간/stale 시 직전 마감율 반환. 정규장이면 live_rate 반환.

        Args:
            live_rate: 현재 FX 환율 (None 이면 stale)
            is_market_hours: 정규장 여부
        """
        if is_market_hours and live_rate is not None:
            self._last_close_rate = live_rate  # 정규장 최신 환율 갱신
            return live_rate

        logger.debug(
            "H26: 야간/stale FX → 직전 마감율 %.2f 사용 (가짜 kill-switch 방지)",
            self._last_close_rate
        )
        return self._last_close_rate

    @property
    def last_close_rate(self) -> float:
        return self._last_close_rate


# ---------------------------------------------------------------------------
# H29 macro abstain
# ---------------------------------------------------------------------------

class H29MacroAbstain:
    """H29: macro 노드 status:unavailable → generate_candidate abstain.

    신규매수 차단. 청산·리밸런싱은 정상 허용 (liveness 디커플링).
    """

    def __init__(self):
        self._abstain: bool = False
        self._reason: str = ""

    def set_status(self, status: str, reason: str = "") -> None:
        """macro status 업데이트."""
        if status.lower() in ("unavailable", "error", "timeout"):
            self._abstain = True
            self._reason = reason or f"macro status={status}"
            logger.warning("H29: macro abstain 활성화 — %s", self._reason)
        else:
            self._abstain = False
            self._reason = ""

    @property
    def should_abstain(self) -> bool:
        """신규매수 차단 여부."""
        return self._abstain

    def filter_action(self, action: str) -> str:
        """H29: 신규매수(buy)→abstain 차단. 청산/리밸런싱 정상."""
        if self._abstain and action.lower() == "buy":
            logger.info("H29: buy → abstain (macro unavailable)")
            return "abstain"
        return action  # sell/hold/rebalance 정상

    @property
    def reason(self) -> str:
        return self._reason
