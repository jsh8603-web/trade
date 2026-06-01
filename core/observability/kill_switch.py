"""core/observability/kill_switch.py — Token Bucket kill-switch (S8, G축, 불변식③).

gemini R6 G6 / claude R6 G6:
- **Token Bucket**: rule 엔진과 주문 실행기 사이 물리 방화벽. 섹터당 일일 최대주문 +
  일 최대턴오버(3%) 하드리밋. 초과 시 주문기가 신호 100% Veto.
- **rule engine ⊂ emergency_stop** (불변식③): rule 은 stop 의 **producer 지 override 아님**.
  rule 이 아무리 "사라" 해도 emergency/한도를 못 넘는다 (우회 불가).
- rule 오작동(주문율 spike · agreement 붕괴) → **auto_emergency 자동발화**.

이 모듈은 실제 wiring 시 execute_trade.py:346-480 MAX_* 블록 + core/risk_gate 위에 얹는다
(WIRE-READY). 여기서는 결정론 한도 로직 + emergency latch 를 self-contained 하게 둔다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class BucketLimits:
    max_orders_per_day: int = 20          # 섹터당 일일 최대 주문 수
    max_turnover_per_day: float = 0.03    # 일 최대 턴오버 (자본 대비 3%)
    order_rate_spike: int = 50            # 비정상 주문율(자동 emergency 트리거)


@dataclass
class GateDecision:
    allow: bool
    reason: str
    verdict: Literal["allow", "veto_limit", "veto_emergency"] = "allow"


class KillSwitch:
    """결정론 하드리밋 + emergency latch. rule 이 우회 불가(불변식③)."""

    def __init__(self, limits: BucketLimits | None = None):
        self.lim = limits or BucketLimits()
        self._orders_today: dict[str, int] = {}
        self._turnover_today: dict[str, float] = {}
        self._emergency = False
        self._emergency_reason = ""
        self.events: list[str] = []

    # --- emergency latch (전역 상위 차단) -------------------------------

    def trip_emergency(self, reason: str) -> None:
        """auto_emergency 발화. 이후 모든 주문 veto. rule 로 해제 불가(사람만)."""
        self._emergency = True
        self._emergency_reason = reason
        self.events.append(f"EMERGENCY: {reason}")

    def reset_emergency(self, by_human: bool = False) -> None:
        if not by_human:
            raise PermissionError("emergency 해제는 사람만(불변식③ rule override 금지)")
        self._emergency = False
        self._emergency_reason = ""
        self.events.append("emergency reset by human")

    # --- 일일 카운터 ----------------------------------------------------

    def new_day(self) -> None:
        self._orders_today.clear()
        self._turnover_today.clear()

    # --- 주문 게이트 (rule 신호가 여기를 통과해야 실행) ------------------

    def check_order(self, sector: str, turnover_frac: float, *, rule_says_buy: bool = True) -> GateDecision:
        """rule 신호(rule_says_buy)는 입력일 뿐 — 한도/emergency 가 최종 결정(불변식③)."""
        # 1) emergency = 무조건 veto (rule 우회 불가)
        if self._emergency:
            return GateDecision(False, f"emergency active: {self._emergency_reason}", "veto_emergency")

        o = self._orders_today.get(sector, 0)
        tv = self._turnover_today.get(sector, 0.0)

        # 2) 주문율 spike → 자동 emergency 발화 후 veto
        if o + 1 > self.lim.order_rate_spike:
            self.trip_emergency(f"주문율 spike sector={sector} ({o+1}>{self.lim.order_rate_spike})")
            return GateDecision(False, "주문율 spike auto-emergency", "veto_emergency")

        # 3) 일일 주문 수 한도
        if o + 1 > self.lim.max_orders_per_day:
            return GateDecision(False, f"일일 주문한도 초과 ({o+1}>{self.lim.max_orders_per_day})", "veto_limit")

        # 4) 턴오버 한도
        if tv + turnover_frac > self.lim.max_turnover_per_day:
            return GateDecision(False, f"턴오버 한도 초과 ({tv+turnover_frac:.3f}>{self.lim.max_turnover_per_day})", "veto_limit")

        # 통과 → 카운터 증가
        self._orders_today[sector] = o + 1
        self._turnover_today[sector] = tv + turnover_frac
        return GateDecision(True, "allow", "allow")


if __name__ == "__main__":
    ks = KillSwitch(BucketLimits(max_orders_per_day=3, max_turnover_per_day=0.03))

    # 1) 한도 내 통과
    d = ks.check_order("semiconductor", 0.005)
    assert d.allow, d
    print(f"1) 한도내: allow={d.allow}")

    # 2) 턴오버 한도 초과 veto (0.005+0.03 > 0.03)
    d = ks.check_order("semiconductor", 0.03)
    assert not d.allow and d.verdict == "veto_limit", d
    print(f"2) 턴오버 초과: allow={d.allow} verdict={d.verdict}")

    # 3) 주문 수 한도: 3개까지 → 4번째 veto
    ks2 = KillSwitch(BucketLimits(max_orders_per_day=3, max_turnover_per_day=1.0))
    res = [ks2.check_order("steel", 0.001).allow for _ in range(4)]
    assert res == [True, True, True, False], res
    print(f"3) 주문수 한도: {res} (4번째 veto)")

    # 4) emergency: rule 이 사라 해도 우회 불가
    ks2.trip_emergency("테스트 비상")
    d = ks2.check_order("steel", 0.001, rule_says_buy=True)
    assert not d.allow and d.verdict == "veto_emergency", d
    print(f"4) emergency 중 rule_says_buy=True: allow={d.allow} (rule 우회 불가, 불변식③)")

    # 5) emergency 해제는 사람만
    try:
        ks2.reset_emergency(by_human=False)
        raise AssertionError("rule 이 emergency 해제함")
    except PermissionError:
        print("5) emergency 해제 사람만 OK")
    ks2.reset_emergency(by_human=True)
    ks2.new_day()   # 일일 카운터 리셋(직전 case3 에서 한도 소진됨)
    assert ks2.check_order("steel", 0.001).allow
    print("   사람 해제 후 정상 복귀 OK")

    print("S8 kill_switch self-test PASS")
