"""core/data/identity.py — PSID(영구 식별자) + bitemporal 식별자 이력 + CA 그래프 (IA-4 substrate).

자문 claude R2-C/R3 #1 (retrofit-grade): ticker 는 안정 키가 아니다.
- ticker recycling: 청산된 ticker 가 수년 후 다른 발행사·종목에 재배정 → ticker 로 join 하면
  무관한 두 종목이 splice(이어붙음) = 전형적 lookahead/생존편향 버그.
- 합병/티커변경/CUSIP변경/액면분할/재상장이 모두 ticker 를 깬다. KR 단축코드(6자리)도 재사용.

해결: 내부 **PSID**(permanent security id, 절대 재사용 금지) 를 단일 join 키로 두고,
(ticker/isin/krx_short/cusip) → PSID 매핑을 **bitemporal** 이력으로 관리.
`resolve_psid(id_value, id_type, as_of)` 는 **PIT 함수** — 그 as_of 시점에 그 식별자가
가리키던 PSID 를 반환(단순 query-time 매핑이면 과거 universe 재현 불가).

합병은 splice 금지: 선행 PSID 종료 + 후행 PSID 계속, `corporate_action_graph` 에
predecessor/successor 링크만 저장(가격/return 을 이어붙이지 않는다).

PIT 2중 게이트(다른 PIT 모듈과 동일): knowable_from ≤ as_of(그때 알 수 있었나) AND
sys_time ≤ as_of(미래 정정 누수 차단). 같은 (id_type,id_value,valid_window) 의 최신 sys_time row.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Optional, Union

AsOfLike = Union[str, date, datetime]
IdType = Literal["ticker", "isin", "krx_short", "cusip", "coinmetrics"]
CaAction = Literal["merge", "rename", "split", "spinoff", "ticker_change", "relist"]

# 영구 끝값 (valid_to 미정 = 현재까지 유효)
_FAR_FUTURE = date(9999, 12, 31)


def _d(x: AsOfLike) -> date:
    """as_of-like → date (naive). datetime 은 date 로 절단."""
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return datetime.fromisoformat(str(x)).date()


@dataclass(frozen=True)
class IdentifierRecord:
    """(id_type, id_value) → PSID 의 bitemporal 매핑 1건.

    valid_from/valid_to = 그 식별자가 이 PSID 를 가리킨 실제 기간(effective).
    knowable_from = 이 매핑을 우리가 알게 된 시점. sys_time = 이 row 를 기록/정정한 시점.
    """
    psid: str
    id_type: IdType
    id_value: str
    valid_from: date
    valid_to: date            # 미정이면 _FAR_FUTURE
    knowable_from: date
    sys_time: date

    def covers(self, when: date) -> bool:
        return self.valid_from <= when < self.valid_to


@dataclass(frozen=True)
class CorporateActionEdge:
    """기업행위 그래프 엣지 — 합병/분할 등에서 PSID 간 인과 링크(splice 금지용)."""
    predecessor_psid: str
    successor_psid: str
    action: CaAction
    effective_date: date
    knowable_from: date


class IdentityStore:
    """PSID 발급 + bitemporal 식별자 이력 + CA 그래프. append-only.

    PSID 는 monotonic 발급(P000001...) — 한 번 발급되면 절대 재사용/재배정 안 함.
    """

    def __init__(self) -> None:
        self._records: list[IdentifierRecord] = []
        self._edges: list[CorporateActionEdge] = []
        self._seq = 0

    # --- PSID 발급 -------------------------------------------------------
    def new_psid(self) -> str:
        self._seq += 1
        return f"P{self._seq:06d}"

    # --- 식별자 매핑 등록 (append-only) ---------------------------------
    def register(
        self,
        psid: str,
        id_type: IdType,
        id_value: str,
        valid_from: AsOfLike,
        knowable_from: AsOfLike,
        *,
        valid_to: Optional[AsOfLike] = None,
        sys_time: Optional[AsOfLike] = None,
    ) -> IdentifierRecord:
        """식별자→PSID 매핑 추가. valid_to 미지정=현재까지. sys_time 기본=knowable_from."""
        kf = _d(knowable_from)
        rec = IdentifierRecord(
            psid=psid,
            id_type=id_type,
            id_value=id_value,
            valid_from=_d(valid_from),
            valid_to=_d(valid_to) if valid_to is not None else _FAR_FUTURE,
            knowable_from=kf,
            sys_time=_d(sys_time) if sys_time is not None else kf,
        )
        self._records.append(rec)
        return rec

    def link_corporate_action(
        self,
        predecessor_psid: str,
        successor_psid: str,
        action: CaAction,
        effective_date: AsOfLike,
        knowable_from: AsOfLike,
    ) -> CorporateActionEdge:
        """합병/분할 등 PSID 간 인과 링크. 가격을 splice 하지 않고 그래프로만 보존."""
        edge = CorporateActionEdge(
            predecessor_psid=predecessor_psid,
            successor_psid=successor_psid,
            action=action,
            effective_date=_d(effective_date),
            knowable_from=_d(knowable_from),
        )
        self._edges.append(edge)
        return edge

    # --- PIT 조회 -------------------------------------------------------
    def resolve_psid(self, id_value: str, id_type: IdType, as_of: AsOfLike) -> Optional[str]:
        """as_of 시점에 (id_type,id_value) 가 가리키던 PSID. 없으면 None.

        PIT 2중 게이트 + valid_window 포함 + 최신 sys_time 선택(정정 반영).
        ticker reuse: 같은 ticker 라도 as_of 가 다르면 다른 PSID 가 나온다.
        """
        a = _d(as_of)
        cands = [
            r for r in self._records
            if r.id_type == id_type and r.id_value == id_value
            and r.knowable_from <= a and r.sys_time <= a and r.covers(a)
        ]
        if not cands:
            return None
        # 같은 valid_window 정정이 여러 건이면 최신 sys_time
        best = max(cands, key=lambda r: r.sys_time)
        return best.psid

    def identifiers_for(self, psid: str, as_of: AsOfLike) -> list[IdentifierRecord]:
        """as_of 시점에 그 PSID 가 가졌던 식별자들(PIT)."""
        a = _d(as_of)
        return [
            r for r in self._records
            if r.psid == psid and r.knowable_from <= a and r.sys_time <= a and r.covers(a)
        ]

    def successors(self, psid: str, as_of: AsOfLike) -> list[CorporateActionEdge]:
        """as_of 시점까지 알려진, 이 PSID 를 선행으로 하는 CA 엣지(합병/분할 후속)."""
        a = _d(as_of)
        return [e for e in self._edges if e.predecessor_psid == psid and e.knowable_from <= a]


if __name__ == "__main__":
    store = IdentityStore()

    # 1) ticker recycling: "ABC" 가 2010-2015 P1, 청산 후 2020+ 다른 발행사 P2 에 재배정
    p1 = store.new_psid()
    p2 = store.new_psid()
    store.register(p1, "ticker", "ABC", valid_from="2010-01-01", knowable_from="2010-01-01", valid_to="2015-07-01")
    store.register(p2, "ticker", "ABC", valid_from="2020-03-01", knowable_from="2020-03-01")
    assert store.resolve_psid("ABC", "ticker", "2012-06-01") == p1, "2012 = P1"
    assert store.resolve_psid("ABC", "ticker", "2021-01-01") == p2, "2021 = P2 (재배정)"
    assert store.resolve_psid("ABC", "ticker", "2017-01-01") is None, "공백기 = None (splice 금지)"
    print(f"1) ticker recycling PIT: 2012->{store.resolve_psid('ABC','ticker','2012-06-01')} / 2021->{store.resolve_psid('ABC','ticker','2021-01-01')} / 2017->공백 OK")

    # 2) ticker change: 같은 PSID 가 ticker 를 바꿈 (P3: OLD->NEW @2022)
    p3 = store.new_psid()
    store.register(p3, "ticker", "OLD", valid_from="2018-01-01", knowable_from="2018-01-01", valid_to="2022-01-01")
    store.register(p3, "ticker", "NEW", valid_from="2022-01-01", knowable_from="2022-01-01")
    store.register(p3, "isin", "KR7000001009", valid_from="2018-01-01", knowable_from="2018-01-01")
    assert store.resolve_psid("OLD", "ticker", "2019-01-01") == p3
    assert store.resolve_psid("NEW", "ticker", "2023-01-01") == p3
    assert store.resolve_psid("KR7000001009", "isin", "2023-01-01") == p3, "ISIN 은 불변 → 같은 PSID"
    ids_2023 = {r.id_value for r in store.identifiers_for(p3, "2023-01-01")}
    assert ids_2023 == {"NEW", "KR7000001009"}, ids_2023
    print(f"2) ticker change: OLD/NEW 모두 P3, ISIN 불변. 2023 식별자={sorted(ids_2023)} OK")

    # 3) knowable_from PIT: 미래에 알게 된 매핑은 과거 as_of 에서 안 보임
    p4 = store.new_psid()
    store.register(p4, "ticker", "LATE", valid_from="2015-01-01", knowable_from="2024-01-01")  # 소급 등록
    assert store.resolve_psid("LATE", "ticker", "2016-01-01") is None, "knowable 2024 → 2016 미가시"
    assert store.resolve_psid("LATE", "ticker", "2024-06-01") == p4
    print("3) knowable_from PIT: 소급 등록 매핑이 과거 as_of 에 미가시 OK")

    # 4) 합병 splice 금지: A(P1) merge into B(P5) → 그래프 링크만, 가격 splice 안 함
    p5 = store.new_psid()
    store.link_corporate_action(p1, p5, "merge", effective_date="2015-07-01", knowable_from="2015-07-01")
    succ = store.successors(p1, "2016-01-01")
    assert len(succ) == 1 and succ[0].successor_psid == p5 and succ[0].action == "merge"
    print(f"4) 합병 그래프: P1 -merge-> {succ[0].successor_psid} (splice 아닌 링크) OK")

    # 5) sys_time 정정: 잘못 등록된 valid_to 를 새 row 로 정정(최신 sys_time 채택)
    p6 = store.new_psid()
    store.register(p6, "ticker", "FIX", valid_from="2020-01-01", knowable_from="2020-01-01", valid_to="2021-01-01", sys_time="2020-01-01")
    store.register(p6, "ticker", "FIX", valid_from="2020-01-01", knowable_from="2020-01-01", valid_to="2099-01-01", sys_time="2021-06-01")  # 정정: 사실 계속 유효
    assert store.resolve_psid("FIX", "ticker", "2022-01-01") == p6, "정정 후 2022 도 유효"
    print("5) sys_time 정정: 최신 sys_time row 채택 OK")

    print("identity (PSID bitemporal) self-test PASS")
