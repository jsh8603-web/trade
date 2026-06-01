"""core/rules/bitemporal_store.py — rule bitemporal store (S2, E/G축).

설계 (claude R6 G5 + 불변식②):
- **append-only** (불변식②): 옛 row 를 절대 mutate 하지 않는다. 모든 변경 = event append.
- **soft-delete** (G5): rule DELETE 금지, invalidate event 만 append. 과거시점 조회는
  당시 사실 그대로 (PIT 오염 방지).
- **rollback** = 잘못된 version 을 invalidate → 이전 version 이 자동 active 복귀
  (옛 row 불변, 새 event 만 추가, claude R6 G5).
- **bitemporal 2축**: effective_from(signal 적용 시작, Signal 내부) ≠ knowable_from
  (이 event 를 알게 된 시점, event 메타). 조회 = AS-OF (knowable_from ≤ as_of).

이벤트 소싱 = 진실의 단일 원천이 append-only event log. as_of_query 는 그 시점까지
knowable 한 event 만 재생해 상태를 복원한다 → 어느 과거시점이든 그때 본 그대로 재현.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Optional

from core.rules.signal import Signal
from core.pit.as_of import resolve_as_of, AsOfLike

EventKind = Literal["publish", "invalidate"]


@dataclass(frozen=True)
class RuleEvent:
    """append-only event. frozen = 사후 mutate 불가(불변식② 코드 강제)."""
    kind: EventKind
    signal_id: str
    version: str
    knowable_from: date          # 이 event 를 알게 된 시점 (AS-OF 조회 축)
    signal: Optional[Signal] = None   # publish 시 본문


class BitemporalRuleStore:
    """rule 의 append-only event log + AS-OF 복원."""

    def __init__(self):
        self._events: list[RuleEvent] = []

    # --- 쓰기 (전부 append, 불변식②) ------------------------------------

    def publish(self, signal: Signal, knowable_from: Optional[AsOfLike] = None) -> None:
        kf = resolve_as_of(knowable_from).date() if knowable_from is not None else signal.knowable_from
        self._events.append(RuleEvent("publish", signal.id, signal.version, kf, signal))

    def invalidate(self, signal_id: str, version: str, knowable_from: AsOfLike) -> None:
        """soft-delete (G5). 옛 publish event 를 건드리지 않고 invalidate event append."""
        kf = resolve_as_of(knowable_from).date()
        self._events.append(RuleEvent("invalidate", signal_id, version, kf))

    def rollback(self, signal_id: str, bad_version: str, knowable_from: AsOfLike) -> None:
        """잘못된 version invalidate → 이전 유효 version 자동 복귀 (옛 row 불변)."""
        self.invalidate(signal_id, bad_version, knowable_from)

    # --- 읽기 (AS-OF 복원) ----------------------------------------------

    def _replay(self, as_of_d: date) -> dict[tuple[str, str], tuple[Signal, bool]]:
        """as_of 시점까지 knowable 한 event 재생 → {(id,ver): (signal, active)}."""
        state: dict[tuple[str, str], tuple[Signal, bool]] = {}
        for ev in self._events:
            if ev.knowable_from > as_of_d:
                continue
            key = (ev.signal_id, ev.version)
            if ev.kind == "publish" and ev.signal is not None:
                state[key] = (ev.signal, True)
            elif ev.kind == "invalidate" and key in state:
                sig, _ = state[key]
                state[key] = (sig, False)
        return state

    def as_of_query(self, signal_id: str, as_of: AsOfLike) -> Optional[Signal]:
        """signal_id 의 as_of 시점 active 최신 version. invalidated/미관측 → None."""
        as_of_d = resolve_as_of(as_of).date()
        state = self._replay(as_of_d)
        active = [
            sig for (sid, _ver), (sig, ok) in state.items()
            if sid == signal_id and ok
        ]
        if not active:
            return None
        # 최신 = effective_from 가장 늦은 active version
        return max(active, key=lambda s: s.effective_from)

    def active_signals(self, as_of: AsOfLike) -> list[Signal]:
        """as_of 시점 active 전체 signal (rule_resolver 입력용)."""
        as_of_d = resolve_as_of(as_of).date()
        return [sig for (sig, ok) in self._replay(as_of_d).values() if ok]

    @property
    def event_count(self) -> int:
        return len(self._events)


if __name__ == "__main__":
    st = BitemporalRuleStore()
    s_v1 = Signal(id="cyc_cheapz", version="v1", archetype="cyclical", feature="cheapness_z",
                  op="lt", threshold=-1.0, effective_from=date(2020, 1, 1))
    s_v2 = Signal(id="cyc_cheapz", version="v2", archetype="cyclical", feature="cheapness_z",
                  op="lt", threshold=-1.5, effective_from=date(2023, 1, 1))

    st.publish(s_v1, knowable_from="2020-01-01")
    st.publish(s_v2, knowable_from="2023-01-01")

    # 1) v2 이전 as_of → v1
    q = st.as_of_query("cyc_cheapz", "2022-06-01")
    assert q is not None and q.version == "v1", q
    print(f"1) as_of 2022-06 → {q.version} (thr={q.threshold}) OK")

    # 2) v2 이후 as_of → v2
    q = st.as_of_query("cyc_cheapz", "2024-01-01")
    assert q is not None and q.version == "v2", q
    print(f"2) as_of 2024-01 → {q.version} (thr={q.threshold}) OK")

    # 3) rollback: v2 가 나쁜 변경 → invalidate(2024-06 알게됨) → 그 이후 v1 복귀
    cnt_before = st.event_count
    st.rollback("cyc_cheapz", "v2", knowable_from="2024-06-01")
    q = st.as_of_query("cyc_cheapz", "2024-12-01")
    assert q is not None and q.version == "v1", q
    print(f"3) rollback 후 as_of 2024-12 → {q.version} 복귀 OK")

    # 4) append-only: rollback 이 event 만 늘림 (옛 row mutate 0)
    assert st.event_count == cnt_before + 1, st.event_count
    print(f"4) append-only: event {cnt_before}→{st.event_count} (옛 row 불변) OK")

    # 5) PIT 오염 방지: rollback 을 알기 전(2024-03) 조회는 여전히 v2
    q = st.as_of_query("cyc_cheapz", "2024-03-01")
    assert q is not None and q.version == "v2", q
    print(f"5) rollback 알기 전 as_of 2024-03 → {q.version} (당시 사실 보존) OK")

    print("S2 bitemporal_store self-test PASS")
