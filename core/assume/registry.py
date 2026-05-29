"""core/assume/registry.py — 가정 카드 통합 보관 + 버전 + lifecycle (CL-1, 축B).

3도메인(macro/equity/commodity/crypto) 카드를 `card_contract.AssumptionCardLike` 표면으로 통합 보관.
- 진입 게이트: `assert_falsifiable` (반증불가 카드 거부).
- 버전: append-only. id 불변, version bump = 정의 S→S' 전환(이전 version 보존, get 은 PIT 로 분기).
- PIT: `get(id, as_of)` = valid_from≤as_of 최신 등록 version(retired 제외). `get_version(id, ver)` = 정확 버전(replay).
- ATMS: `dependents(id)` = depends_on 역색인 (의존전파 O(1)).
- lifecycle: register=ASSUMPTION_CREATED / transition=TRANSITIONED / retire=RETIRED 를 optional
  event_sink 로 emit. sink = btn-Inv `event_ledger`(12-event bitemporal) producer 배선점.
  미주입 = standalone(테스트). join 키 = (assumption_id, version).

자문 R1~R5: 카드 = 통합 method(decoupling 머신) 일반화. 이벤트소싱 substrate(btn-Inv) 위에서
Registry 는 lifecycle 이벤트 producer, derivation/judge 는 state(=카드 projection) consumer.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Callable, Optional

from core.assume.card_contract import AssumptionCardLike, assert_falsifiable

# event_sink(event_type, card) — production 은 btn-Inv event_ledger 로 배선.
EventSink = Callable[[str, AssumptionCardLike], None]


def _as_date(x) -> Optional[date]:
    """date/datetime/str/Timestamp → date (None=genesis/now). 비교 일관성."""
    if x is None:
        return None
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return date.fromisoformat(str(x)[:10])


class AssumptionRegistry:
    """카드 통합 보관소. (id, version) 키. PIT 조회 + lifecycle 이벤트 emit."""

    def __init__(self, event_sink: Optional[EventSink] = None):
        self._cards: dict[tuple[str, str], AssumptionCardLike] = {}
        self._versions: dict[str, list[str]] = {}            # id → [version,...] 등록순
        self._retired: dict[tuple[str, str], Optional[date]] = {}  # (id,ver) → retire as_of
        self._dep_index: dict[str, set[str]] = {}            # dep_id → {card_id,...} (역색인)
        self._sink = event_sink

    def _emit(self, ev: str, card: AssumptionCardLike) -> None:
        if self._sink is not None:
            self._sink(ev, card)

    def register(self, card: AssumptionCardLike, *, _event: str = "ASSUMPTION_CREATED") -> AssumptionCardLike:
        """카드 등록. 반증불가 거부 + 중복 (id,version) 거부 + 역색인 + lifecycle emit."""
        assert_falsifiable(card)                              # 진입 게이트 (btn-button)
        key = (card.id, card.version)
        if key in self._cards:
            raise ValueError(f"중복 등록 (id,version)={key} — 정의 전환 시 version bump 필요")
        self._cards[key] = card
        self._versions.setdefault(card.id, []).append(card.version)
        for dep in (getattr(card, "depends_on", None) or []):
            self._dep_index.setdefault(dep, set()).add(card.id)
        self._emit(_event, card)
        return card

    def transition(self, new_card: AssumptionCardLike) -> AssumptionCardLike:
        """정의 S→S' = 새 version 등록(TRANSITIONED). 이전 version append-only 보존(get 이 PIT 분기).

        new_card.valid_from = 전환 시점 (이 시점부터 새 정의 활성). PIT replay 는 get_version 으로.
        """
        if new_card.id not in self._versions:
            raise ValueError(f"transition 대상 {new_card.id!r} 미등록 — register 선행 필요")
        if new_card.version in self._versions[new_card.id]:
            raise ValueError(f"{new_card.id!r} version {new_card.version!r} 이미 존재 — 새 version 필요")
        return self.register(new_card, _event="TRANSITIONED")

    def retire(self, id: str, version: str, *, reason: str = "", as_of=None) -> None:
        """카드 은퇴(RETIRED). as_of=None → 즉시(now). PIT: as_of 이후 조회에서만 제외."""
        key = (id, version)
        if key not in self._cards:
            raise KeyError(f"retire 대상 {key} 미등록")
        self._retired[key] = _as_date(as_of)
        self._emit("RETIRED", self._cards[key])

    def get_version(self, id: str, version: str) -> Optional[AssumptionCardLike]:
        """정확 버전 (PIT replay — frozen 재현)."""
        return self._cards.get((id, version))

    def get(self, id: str, as_of=None) -> Optional[AssumptionCardLike]:
        """as_of 활성 카드 = valid_from≤as_of 중 최신 등록 version (retired 제외). as_of=None=now."""
        a = _as_date(as_of)
        result = None
        for v in self._versions.get(id, []):
            key = (id, v)
            if key in self._retired:                          # retired 분기 (PIT)
                rt = self._retired[key]
                if a is None or rt is None or rt <= a:        # now / 즉시은퇴 / as_of≥은퇴 → 제외
                    continue
            card = self._cards[key]
            vf = _as_date(getattr(card, "valid_from", None))
            if a is None or vf is None or vf <= a:            # valid_from≤as_of (None=genesis)
                result = card                                 # 등록순 최신 valid 유지
        return result

    def active(self, *, domain: Optional[str] = None, scope: Optional[str] = None,
               as_of=None) -> list[AssumptionCardLike]:
        """활성 카드 surface (judge/derivation 입력). domain/scope 필터."""
        out = []
        for id in self._versions:
            c = self.get(id, as_of=as_of)
            if c is None:
                continue
            if domain is not None and c.domain != domain:
                continue
            if scope is not None and c.scope != scope:
                continue
            out.append(c)
        return out

    def dependents(self, id: str) -> list[str]:
        """이 가정에 의존하는 카드 id (ATMS 전파 역색인)."""
        return sorted(self._dep_index.get(id, set()))


if __name__ == "__main__":
    from core.assume.card_contract import BaseAssumptionFields

    def _card(id, ver="v1", vf=None, deps=(), dom="macro", scope="macro"):
        return BaseAssumptionFields(
            id=id, version=ver, kind="structural", scope=scope, domain=dom,
            statement=f"{id} 정의", falsification_metric=f"{id} 반증조건 정량",
            valid_from=vf, depends_on=list(deps), posterior_confidence=0.6,
        )

    events: list[tuple[str, str]] = []
    reg = AssumptionRegistry(event_sink=lambda ev, c: events.append((ev, f"{c.id}@{c.version}")))

    # 1) register + get + get_version + active
    a = _card("macro.yc_inv", vf=date(2020, 1, 1))
    reg.register(a)
    assert reg.get("macro.yc_inv") is a and reg.get_version("macro.yc_inv", "v1") is a
    assert a in reg.active(domain="macro")
    print(f"1) register/get/active OK ({len(reg.active())} active)")

    # 2) ATMS 역색인: B depends_on A
    b = _card("equity.semi_per", deps=["macro.yc_inv"], dom="equity", scope="sector")
    reg.register(b)
    assert reg.dependents("macro.yc_inv") == ["equity.semi_per"], reg.dependents("macro.yc_inv")
    print(f"2) dependents 역색인 OK: {reg.dependents('macro.yc_inv')}")

    # 3) ★PIT 버전전환 S→S': v2(valid_from 2023) transition
    a2 = _card("macro.yc_inv", ver="v2", vf=date(2023, 1, 1))
    reg.transition(a2)
    assert reg.get("macro.yc_inv", as_of="2021-06-01") is a, "PIT: 2021 엔 v1 이어야"
    assert reg.get("macro.yc_inv", as_of="2024-06-01") is a2, "PIT: 2024 엔 v2 여야"
    assert reg.get_version("macro.yc_inv", "v1") is a, "replay: v1 정확 보존"
    print("3) PIT 버전전환 S→S' OK (2021→v1, 2024→v2, v1 replay 보존)")

    # 4) retire PIT: v2 as_of 2025 → 2026 조회 시 v1 로 폴백(v2 제외)
    reg.retire("macro.yc_inv", "v2", as_of="2025-01-01")
    assert reg.get("macro.yc_inv", as_of="2024-06-01") is a2, "2024 < 은퇴(2025) → v2 유지"
    assert reg.get("macro.yc_inv", as_of="2026-01-01") is a, "2026 ≥ 은퇴 → v2 제외 → v1 폴백"
    print("4) retire PIT OK (2024<은퇴 v2유지 / 2026≥은퇴 v1폴백)")

    # 5) 반증불가 게이트 + 중복 거부
    class _NoFalsify:
        id = "bad"; version = "v1"; kind = "parametric"; scope = "global"; domain = "equity"
        statement = "x"; rationale = ""; falsification_metric = ""; is_base_layer = False
        valid_from = None; regime_model_version = None; posterior_confidence = 0.5
        band_halfwidth = 1.0; depends_on = []; half_life = None
    try:
        reg.register(_NoFalsify())
        raise AssertionError("반증불가 카드가 등록됨")
    except Exception as e:
        assert "falsification" in str(e) or "반증" in str(e), e
    try:
        reg.register(a)  # (id,v1) 중복
        raise AssertionError("중복 (id,version) 등록됨")
    except ValueError:
        pass
    print("5) 반증불가 게이트 + 중복 거부 OK")

    # 6) lifecycle 이벤트 emit
    evtypes = [e[0] for e in events]
    assert "ASSUMPTION_CREATED" in evtypes and "TRANSITIONED" in evtypes and "RETIRED" in evtypes, events
    print(f"6) lifecycle emit OK: {events}")

    print("CL-1 registry self-test PASS")
