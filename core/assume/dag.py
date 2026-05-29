"""core/assume/dag.py — ATMS 의존전파 (CL-3, 축E). gridlock 방어.

거시 가정 1건 변경이 3도메인 하위 재유도 폭주 → 매매 마비(gemini ★실패모드). 방어:
 - hard/soft 분기(§2.3 비대칭의 전파레벨): retract(falsifier)=hard fast-path(즉시 orphan 후보) /
   transition(adopt)=soft grace+lazy(stale 마킹만, 재검증은 derive 접근 시).
 - epoch topological single-pass + nogood: 같은 epoch 재무효화 차단(무한루프 0).
 - churn > CHURN_CAP → escalate human(rate-limit, 폭주 차단).
 - BaseLayerCutover(claude R1): base-layer(regime/지표의미) 변경 = retraction 아니라 re-derivation.
   '가정 바뀜'≠'결론 틀림'. old 운영 + new 그림자 병행 → 안정 후에만 commit(shadow/canary).

전파 위상은 registry.dependents(역색인) 단일. 통계예산(FDR)만 도메인 격리(validator).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from core.assume.registry import _as_date

GRACE_DAYS = 5      # soft 전이 = 의존 가정 grace 유지기간 (이 안엔 기존값 매매 지속)
CHURN_CAP = 20      # epoch당 무효화 상한 — 초과 시 사람 escalate (cascade 폭주 차단)


@dataclass
class InvalidationResult:
    id: str
    epoch: int
    mode: str
    stale_marked: list[str] = field(default_factory=list)      # soft: grace 마킹된 의존카드
    orphan_candidates: list[str] = field(default_factory=list)  # hard: 즉시 청산후보 (§4.2)
    escalated: bool = False                                     # churn cap 초과 → 사람
    churn: int = 0                                              # 이 epoch 누적 처리수


class AssumptionDAG:
    """가정 의존 DAG. invalidate(hard/soft) + grace/lazy resolve + epoch single-pass."""

    def __init__(self, registry, *, grace_days: int = GRACE_DAYS, churn_cap: int = CHURN_CAP):
        self.registry = registry
        self.grace_days = grace_days
        self.churn_cap = churn_cap
        self._stale: dict[str, Optional[date]] = {}    # card_id → grace_until (soft)
        self._orphan: set[str] = set()                 # hard-retract 청산후보
        self._epoch_done: dict[int, set[str]] = {}     # epoch → 처리한 id (nogood, 재진입 0)

    def _dependents_transitive(self, id: str, seen: set[str]) -> list[str]:
        """registry.dependents BFS. seen(=epoch nogood) 은 single-pass 로 건너뜀."""
        out: list[str] = []
        frontier = list(self.registry.dependents(id))
        while frontier:
            d = frontier.pop()
            if d in seen:
                continue
            seen.add(d)
            out.append(d)
            frontier.extend(self.registry.dependents(d))
        return out

    def invalidate(self, id: str, *, epoch: int, as_of, mode: str = "soft",
                   grace_days: Optional[int] = None) -> InvalidationResult:
        """id 변경 → 의존 전파. mode='hard'=fast orphan / 'soft'=grace stale. epoch single-pass."""
        grace = self.grace_days if grace_days is None else grace_days
        seen = self._epoch_done.setdefault(epoch, set())
        if id in seen:                                   # 같은 epoch 재무효화 = nogood (차단)
            return InvalidationResult(id, epoch, mode, churn=len(seen))
        seen.add(id)
        deps = self._dependents_transitive(id, seen)

        res = InvalidationResult(id, epoch, mode)
        if mode == "hard":
            for d in deps:
                self._orphan.add(d)
                res.orphan_candidates.append(d)
        elif mode == "soft":
            a = _as_date(as_of)
            grace_until = (a + timedelta(days=grace)) if a is not None else None
            for d in deps:
                self._stale[d] = grace_until
                res.stale_marked.append(d)
        else:
            raise ValueError(f"미지 mode: {mode!r} (hard|soft)")

        res.churn = len(seen)
        res.escalated = res.churn > self.churn_cap      # 폭주 → 사람 rate-limit
        return res

    def is_stale(self, id: str) -> bool:
        return id in self._stale

    def is_orphan_candidate(self, id: str) -> bool:
        return id in self._orphan

    def resolve_stale(self, id: str, as_of) -> bool:
        """derive 가 호출. grace 만료 → True(재검증 필요) / grace 내 → False(기존값 유지=매매지속).

        lazy 핵심: stale 이어도 grace 안엔 재검증 안 함(eager cascade 차단 = gridlock 방어).
        재검증 완료 후 호출자가 clear_stale.
        """
        if id not in self._stale:
            return False
        grace_until = self._stale[id]
        a = _as_date(as_of)
        if grace_until is None or a is None or a >= grace_until:
            return True
        return False

    def clear_stale(self, id: str) -> None:
        self._stale.pop(id, None)


class BaseLayerCutover:
    """base-layer(regime/지표의미) 변경 = old 운영 + new 그림자 병행 → 안정 후 commit (claude R1)."""

    def __init__(self):
        self._active: dict[str, dict] = {}   # base_id → {new_version, stable}

    def begin(self, base_id: str, new_version: str) -> None:
        """old derived param 으로 계속 운영 + new base 로 그림자 유도 병행 시작."""
        self._active[base_id] = {"new_version": new_version, "stable": False}

    def mark_shadow(self, base_id: str, *, stable: bool) -> None:
        if base_id in self._active:
            self._active[base_id]["stable"] = stable

    def is_active(self, base_id: str) -> bool:
        return base_id in self._active

    def is_stable(self, base_id: str) -> bool:
        return self._active.get(base_id, {}).get("stable", False)

    def commit(self, base_id: str) -> str:
        """그림자 안정 확인 후에만 전환. 미안정 commit = 차단(shadow/canary 강제)."""
        if not self.is_stable(base_id):
            raise ValueError(f"base {base_id!r} 그림자 미안정 — commit 금지 (shadow/canary 선행)")
        return self._active.pop(base_id)["new_version"]


if __name__ == "__main__":
    from core.assume.registry import AssumptionRegistry
    from core.assume.card_contract import BaseAssumptionFields

    def _card(id, deps=(), dom="macro", scope="macro"):
        return BaseAssumptionFields(
            id=id, version="v1", kind="parametric", scope=scope, domain=dom,
            statement=f"{id} 정의", falsification_metric=f"{id} cusum", depends_on=list(deps))

    # 체인: macro.A ← equity.B ← equity.C (C dep B, B dep A) → A 변경 = {B,C} 전파
    reg = AssumptionRegistry()
    reg.register(_card("macro.A"))
    reg.register(_card("equity.B", deps=["macro.A"], dom="equity", scope="sector"))
    reg.register(_card("equity.C", deps=["equity.B"], dom="equity", scope="sector"))
    assert reg.dependents("macro.A") == ["equity.B"] and reg.dependents("equity.B") == ["equity.C"]

    dag = AssumptionDAG(reg)

    # 1) soft transition: 의존 {B,C} stale 마킹 (즉시 orphan X)
    r1 = dag.invalidate("macro.A", epoch=1, as_of="2026-05-01", mode="soft")
    print(f"1) soft: stale={sorted(r1.stale_marked)} orphan={r1.orphan_candidates} churn={r1.churn}")
    assert sorted(r1.stale_marked) == ["equity.B", "equity.C"] and not r1.orphan_candidates
    assert dag.is_stale("equity.B") and dag.is_stale("equity.C")

    # 2) lazy: grace(2026-05-06) 내 → resolve_stale False(매매유지) / 만료 후 → True(재검증)
    assert dag.resolve_stale("equity.B", as_of="2026-05-03") is False, "grace 내 = 매매유지"
    assert dag.resolve_stale("equity.B", as_of="2026-05-10") is True, "grace 만료 = 재검증"
    dag.clear_stale("equity.B")
    assert dag.is_stale("equity.B") is False
    print("2) lazy grace OK: grace내 유지 / 만료 재검증 / clear")

    # 3) hard retract: 의존 즉시 orphan 후보 (fast-path)
    dag3 = AssumptionDAG(reg)
    r3 = dag3.invalidate("macro.A", epoch=1, as_of="2026-05-01", mode="hard")
    print(f"3) hard: orphan={sorted(r3.orphan_candidates)} stale={r3.stale_marked}")
    assert sorted(r3.orphan_candidates) == ["equity.B", "equity.C"] and not r3.stale_marked
    assert dag3.is_orphan_candidate("equity.B")

    # 4) epoch single-pass: 같은 epoch 재무효화 = nogood (no-op)
    dag4 = AssumptionDAG(reg)
    dag4.invalidate("macro.A", epoch=7, as_of="2026-05-01", mode="soft")
    r4 = dag4.invalidate("macro.A", epoch=7, as_of="2026-05-01", mode="soft")
    print(f"4) single-pass: 재무효화 stale={r4.stale_marked} (nogood = 빈 처리)")
    assert r4.stale_marked == [], "같은 epoch 재무효화는 nogood"

    # 5) churn cap → escalate human
    reg5 = AssumptionRegistry()
    reg5.register(_card("macro.root"))
    for i in range(4):
        reg5.register(_card(f"equity.x{i}", deps=["macro.root"], dom="equity", scope="sector"))
    dag5 = AssumptionDAG(reg5, churn_cap=2)
    r5 = dag5.invalidate("macro.root", epoch=1, as_of="2026-05-01", mode="soft")
    print(f"5) churn cap: churn={r5.churn} escalated={r5.escalated}")
    assert r5.escalated is True, "churn>cap → 사람 escalate"

    # 6) BaseLayerCutover: 미안정 commit 차단 → 안정 후 commit OK
    cut = BaseLayerCutover()
    cut.begin("macro.regime_model", "v2")
    assert cut.is_active("macro.regime_model")
    try:
        cut.commit("macro.regime_model")
        raise AssertionError("미안정인데 commit 됨")
    except ValueError:
        pass
    cut.mark_shadow("macro.regime_model", stable=True)
    assert cut.commit("macro.regime_model") == "v2" and not cut.is_active("macro.regime_model")
    print("6) BaseLayerCutover OK: 미안정 commit 차단 → 그림자 안정 후 commit")

    print("CL-3 dag self-test PASS (hard/soft + grace/lazy + single-pass + churn escalate + base cutover)")
