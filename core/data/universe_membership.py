"""core/data/universe_membership.py — bitemporal 유니버스 멤버십 (IA-4 생존편향 차단).

claude R3 #1(crypto/ETF first-class): 유니버스(지수구성·ETF holdings·crypto 바스켓)는
시간에 따라 변하는데, 벤더는 보통 **현재 구성만** 준다. 현재 구성으로 과거를 조회하면
**생존편향**(그때 있었으나 지금 빠진 종목 누락 + 지금 있으나 그때 없던 종목 오포함) =
backtest 가 "살아남은 것만" 보는 전형적 lookahead.

해결: 관측 시점마다 구성을 **append-only 로 축적**하고 bitemporal 로 조회.
- member_psid(identity.PSID 연계) · universe_id · weight · valid_from/to(실제 편입기간)
- knowable_from(이 멤버십을 알게 된 시점) · sys_time(기록/정정)
- `members_as_of(universe_id, when, as_of)` = when 시점에 실제 멤버였고 as_of 에 알 수 있던 것
  (지금 상장폐지된 종목도 그때 멤버였으면 포함 = 생존편향 차단).

PIT 2중 게이트(다른 모듈 동일): knowable_from ≤ as_of AND sys_time ≤ as_of.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Union

AsOfLike = Union[str, date, datetime]
_FAR_FUTURE = date(9999, 12, 31)


def _d(x: AsOfLike) -> date:
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return datetime.fromisoformat(str(x)).date()


@dataclass(frozen=True)
class MembershipRecord:
    """bitemporal 유니버스 멤버십 1건."""
    member_psid: str
    universe_id: str
    weight: float
    valid_from: date
    valid_to: date            # 미정 = _FAR_FUTURE
    knowable_from: date
    sys_time: date

    def covers(self, when: date) -> bool:
        return self.valid_from <= when < self.valid_to


class UniverseStore:
    """bitemporal 유니버스 멤버십 저장소. append-only(관측시점 구성 축적)."""

    def __init__(self) -> None:
        self._records: list[MembershipRecord] = []

    # --- 적재 (append-only) ---------------------------------------------
    def add_member(
        self,
        member_psid: str,
        universe_id: str,
        valid_from: AsOfLike,
        knowable_from: AsOfLike,
        *,
        weight: float = 0.0,
        valid_to: Optional[AsOfLike] = None,
        sys_time: Optional[AsOfLike] = None,
    ) -> MembershipRecord:
        """멤버십 추가. valid_to 미정=현재까지. sys_time 기본=knowable_from."""
        kf = _d(knowable_from)
        rec = MembershipRecord(
            member_psid=member_psid, universe_id=universe_id, weight=float(weight),
            valid_from=_d(valid_from), valid_to=_d(valid_to) if valid_to is not None else _FAR_FUTURE,
            knowable_from=kf, sys_time=_d(sys_time) if sys_time is not None else kf,
        )
        self._records.append(rec)
        return rec

    # --- PIT 조회 -------------------------------------------------------
    def _visible(self, universe_id: str, when: date, as_of: date) -> list[MembershipRecord]:
        return [r for r in self._records
                if r.universe_id == universe_id and r.covers(when)
                and r.knowable_from <= as_of and r.sys_time <= as_of]

    def members_as_of(self, universe_id: str, when: AsOfLike, as_of: AsOfLike) -> list[str]:
        """when 시점에 실제 멤버였고 as_of 에 알 수 있던 member_psid 집합(생존편향 차단).

        같은 member 가 정정 다건이면 최신 sys_time 의 멤버십을 채택. weight 0 정정=제외 처리.
        """
        w, a = _d(when), _d(as_of)
        latest: dict[str, MembershipRecord] = {}
        for r in self._visible(universe_id, w, a):
            cur = latest.get(r.member_psid)
            if cur is None or r.sys_time > cur.sys_time:
                latest[r.member_psid] = r
        return sorted(pid for pid, r in latest.items())

    def is_member(self, member_psid: str, universe_id: str, when: AsOfLike, as_of: AsOfLike) -> bool:
        return member_psid in self.members_as_of(universe_id, when, as_of)

    def weight_of(self, member_psid: str, universe_id: str, when: AsOfLike, as_of: AsOfLike) -> Optional[float]:
        w, a = _d(when), _d(as_of)
        cands = [r for r in self._visible(universe_id, w, a) if r.member_psid == member_psid]
        if not cands:
            return None
        return max(cands, key=lambda r: r.sys_time).weight


if __name__ == "__main__":
    store = UniverseStore()

    # 시나리오: KOSPI200 에 A(2010~), B(2010~2018 편출), C(2019~ 편입, 이후 상장폐지)
    store.add_member("P0001", "KOSPI200", valid_from="2010-01-01", knowable_from="2010-01-01", weight=0.05)
    store.add_member("P0002", "KOSPI200", valid_from="2010-01-01", knowable_from="2010-01-01", weight=0.03, valid_to="2018-06-01")
    store.add_member("P0003", "KOSPI200", valid_from="2019-01-01", knowable_from="2019-01-01", weight=0.02, valid_to="2022-03-01")

    # 1) ★생존편향 차단: 2015 시점 멤버 = {A, B} (B 는 지금 편출됐지만 그때 멤버)
    m2015 = store.members_as_of("KOSPI200", "2015-06-01", "2024-01-01")
    assert m2015 == ["P0001", "P0002"], m2015
    print(f"1) 생존편향 차단: 2015 멤버={m2015} (편출된 B 포함) OK")

    # 2) 2020 시점 = {A, C} (B 편출, C 편입)
    m2020 = store.members_as_of("KOSPI200", "2020-06-01", "2024-01-01")
    assert m2020 == ["P0001", "P0003"], m2020
    print(f"2) 2020 멤버={m2020} (B 편출/C 편입) OK")

    # 3) ★knowable_from PIT: C 편입을 2019-01 에 알았으니 as_of 2018 에는 미가시
    m2020_seen2018 = store.members_as_of("KOSPI200", "2020-06-01", "2018-01-01")
    assert "P0003" not in m2020_seen2018, m2020_seen2018  # 2018 엔 C 편입 미인지
    print(f"3) knowable PIT: as_of 2018 엔 C(2019 편입) 미가시 → {m2020_seen2018} OK")

    # 4) is_member / weight_of
    assert store.is_member("P0002", "KOSPI200", "2015-06-01", "2024-01-01")
    assert not store.is_member("P0002", "KOSPI200", "2020-06-01", "2024-01-01")  # 편출 후
    assert store.weight_of("P0001", "KOSPI200", "2015-06-01", "2024-01-01") == 0.05
    print("4) is_member/weight_of PIT OK")

    # 5) sys_time 정정: A weight 0.05→0.07 정정(최신 sys_time 채택)
    store.add_member("P0001", "KOSPI200", valid_from="2010-01-01", knowable_from="2010-01-01", weight=0.07, sys_time="2021-01-01")
    assert store.weight_of("P0001", "KOSPI200", "2015-06-01", "2020-01-01") == 0.05  # 정정 전
    assert store.weight_of("P0001", "KOSPI200", "2015-06-01", "2022-01-01") == 0.07  # 정정 후
    print("5) sys_time 정정: weight 0.05→0.07 최신 채택 OK")

    # 6) crypto 바스켓 first-class: 동일 메커니즘
    store.add_member("BTC", "crypto_top2", valid_from="2020-01-01", knowable_from="2020-01-01", weight=0.7)
    store.add_member("ETH", "crypto_top2", valid_from="2020-01-01", knowable_from="2020-01-01", weight=0.3)
    assert store.members_as_of("crypto_top2", "2021-01-01", "2024-01-01") == ["BTC", "ETH"]
    print("6) crypto 바스켓 first-class OK")

    print("universe_membership (bitemporal 생존편향 차단) self-test PASS")
