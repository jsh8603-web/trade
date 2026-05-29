"""core/data/calendar.py — 거래소 세션·휴장 bitemporal 캘린더 (IA-6 substrate).

자문 수렴(IA-6 = 시간/정정 무결성): 모든 의사결정·관측의 시각은 **단일 UTC** 로 환원하고,
거래소 휴장은 **bitemporal** 로 둔다. 핵심은 두 가지 lookahead 차단:

1. **단일 UTC 환원**: 거래소 로컬 세션(예: KRX 09:00 Asia/Seoul, NYSE 09:30 America/New_York)을
   IANA tz + DST 규칙으로 UTC 경계로 변환. 모듈마다 로컬 tz 를 다르게 해석하면 outcome join
   시점이 어긋난다(예: NYSE 종가가 EDT/EST 에 따라 UTC 13:30/14:30 으로 갈림).

2. **휴장 bitemporal**: 긴급 휴장(임시공휴일·재난 휴장)은 **공표 시점(knowable_from)** 이 있다.
   2024-12-30 에 공표돼 2024-12-31 효력인 휴장은, as_of=2024-12-01 백테스트에서는
   **알 수 없어야** 한다(미래 휴장 foreknowledge = lookahead). `is_holiday(..., as_of)` 는
   knowable_from ≤ as_of AND sys_time ≤ as_of 인 휴장만 본다(다른 PIT 모듈과 동일 2중 게이트).

crypto = 24x7(휴장·주말 없음, 세션 = UTC 자정~자정). append-only, 신규 의존 없음(stdlib zoneinfo).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Optional, Union
from zoneinfo import ZoneInfo

AsOfLike = Union[str, date, datetime]

# 영구 끝값 (sys_time 기본 = knowable_from 과 동일 의미론, identity.py 정합)


def _d(x: AsOfLike) -> date:
    """as_of-like → date (naive). datetime 은 date 로 절단."""
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return datetime.fromisoformat(str(x)).date()


@dataclass(frozen=True)
class ExchangeSpec:
    """거래소 정규 세션 명세. 로컬 시각 + tz 로 정의, UTC 변환은 calendar 가 수행."""
    code: str
    tz: str                          # IANA tz (DST 자동 처리)
    open_local: time                 # 정규장 개장 (로컬)
    close_local: time                # 정규장 마감 (로컬)
    weekmask: frozenset[int]         # 개장 요일 {0=월..6=일}
    is_24x7: bool = False            # crypto 등 무휴장


@dataclass(frozen=True)
class HolidayRecord:
    """bitemporal 휴장 1건.

    holiday_date = 휴장 효력일(effective). knowable_from = 이 휴장을 알게 된(공표) 시점.
    sys_time = 이 row 를 기록/정정한 시점(정정 시 새 row + 최신 sys_time 채택).
    """
    exchange: str
    holiday_date: date
    knowable_from: date
    sys_time: date
    reason: str = ""


# 표준 거래소 명세 (확장 가능)
_KR = ExchangeSpec("KRX", "Asia/Seoul", time(9, 0), time(15, 30),
                   frozenset({0, 1, 2, 3, 4}))
_NYSE = ExchangeSpec("XNYS", "America/New_York", time(9, 30), time(16, 0),
                     frozenset({0, 1, 2, 3, 4}))
_NASDAQ = ExchangeSpec("XNAS", "America/New_York", time(9, 30), time(16, 0),
                       frozenset({0, 1, 2, 3, 4}))
_CRYPTO = ExchangeSpec("CRYPTO", "UTC", time(0, 0), time(0, 0),
                       frozenset({0, 1, 2, 3, 4, 5, 6}), is_24x7=True)

_DEFAULT_EXCHANGES = {e.code: e for e in (_KR, _NYSE, _NASDAQ, _CRYPTO)}


class ExchangeCalendar:
    """거래소 세션·휴장 bitemporal 캘린더. append-only 휴장 이력 + UTC 세션 변환.

    표준 거래소(KRX/XNYS/XNAS/CRYPTO)는 기본 등록. 휴장은 register 없이 비어 있고,
    `add_holiday` 로 공표 시점과 함께 적재한다(PIT).
    """

    def __init__(self) -> None:
        self._exchanges: dict[str, ExchangeSpec] = dict(_DEFAULT_EXCHANGES)
        self._holidays: list[HolidayRecord] = []

    # --- 거래소 등록 ----------------------------------------------------
    def register_exchange(self, spec: ExchangeSpec) -> None:
        self._exchanges[spec.code] = spec

    def _spec(self, exchange: str) -> ExchangeSpec:
        if exchange not in self._exchanges:
            raise KeyError(f"미등록 거래소: {exchange} (등록={sorted(self._exchanges)})")
        return self._exchanges[exchange]

    # --- 휴장 적재 (append-only, bitemporal) ----------------------------
    def add_holiday(
        self,
        exchange: str,
        holiday_date: AsOfLike,
        knowable_from: AsOfLike,
        *,
        sys_time: Optional[AsOfLike] = None,
        reason: str = "",
    ) -> HolidayRecord:
        """휴장 1건 적재. knowable_from = 공표 시점(이전 as_of 에는 미가시). sys_time 기본=knowable_from."""
        self._spec(exchange)
        kf = _d(knowable_from)
        rec = HolidayRecord(
            exchange=exchange,
            holiday_date=_d(holiday_date),
            knowable_from=kf,
            sys_time=_d(sys_time) if sys_time is not None else kf,
            reason=reason,
        )
        self._holidays.append(rec)
        return rec

    # --- PIT 조회 -------------------------------------------------------
    def is_holiday(self, exchange: str, day: AsOfLike, as_of: AsOfLike) -> bool:
        """as_of 시점에 알 수 있던 휴장인가. knowable_from ≤ as_of AND sys_time ≤ as_of.

        같은 (exchange, holiday_date) 에 정정 row 가 여러 건이면 최신 sys_time 의 효력을 따른다
        — reason 이 비면 '정정으로 휴장 취소'를 표현(취소도 row 로). 여기선 존재=휴장으로 단순화.
        """
        spec = self._spec(exchange)
        if spec.is_24x7:
            return False
        d = _d(day)
        a = _d(as_of)
        cands = [
            h for h in self._holidays
            if h.exchange == exchange and h.holiday_date == d
            and h.knowable_from <= a and h.sys_time <= a
        ]
        if not cands:
            return False
        latest = max(cands, key=lambda h: h.sys_time)
        # reason == "__CANCELLED__" 정정 = 휴장 아님 (취소도 bitemporal 로 표현)
        return latest.reason != "__CANCELLED__"

    def is_trading_day(self, exchange: str, day: AsOfLike, as_of: AsOfLike) -> bool:
        """as_of 기준 거래일 여부 = 개장 요일 AND (PIT) 휴장 아님."""
        spec = self._spec(exchange)
        d = _d(day)
        if spec.is_24x7:
            return True
        if d.weekday() not in spec.weekmask:
            return False
        return not self.is_holiday(exchange, d, as_of)

    def session_utc(
        self, exchange: str, day: AsOfLike, as_of: AsOfLike
    ) -> Optional[tuple[datetime, datetime]]:
        """day 의 정규장 (open, close) 를 **UTC tz-aware** 로 반환. 비거래일이면 None.

        로컬 세션 시각을 IANA tz 로 localize → UTC 변환(DST 자동). 단일 UTC 환원(IA-6).
        crypto 는 [그날 00:00 UTC, 다음날 00:00 UTC).
        """
        spec = self._spec(exchange)
        d = _d(day)
        if spec.is_24x7:
            start = datetime.combine(d, time(0, 0), tzinfo=ZoneInfo("UTC"))
            return start, start + timedelta(days=1)
        if not self.is_trading_day(exchange, d, as_of):
            return None
        tz = ZoneInfo(spec.tz)
        open_local = datetime.combine(d, spec.open_local, tzinfo=tz)
        close_local = datetime.combine(d, spec.close_local, tzinfo=tz)
        return (open_local.astimezone(ZoneInfo("UTC")),
                close_local.astimezone(ZoneInfo("UTC")))

    def next_trading_day(self, exchange: str, day: AsOfLike, as_of: AsOfLike) -> date:
        """day **다음**의 첫 거래일(PIT 휴장 반영). day 자신은 포함 안 함."""
        d = _d(day) + timedelta(days=1)
        for _ in range(370):  # 최대 1년 안전 상한
            if self.is_trading_day(exchange, d, as_of):
                return d
            d += timedelta(days=1)
        raise RuntimeError(f"{exchange}: {day} 이후 370일 내 거래일 없음")


if __name__ == "__main__":
    cal = ExchangeCalendar()

    # 1) KRX 정규 거래일/주말
    assert cal.is_trading_day("KRX", "2024-06-03", "2024-06-30")   # 월
    assert not cal.is_trading_day("KRX", "2024-06-01", "2024-06-30")  # 토
    assert not cal.is_trading_day("KRX", "2024-06-02", "2024-06-30")  # 일
    print("1) KRX 평일=거래/주말=비거래 OK")

    # 2) 휴장 bitemporal PIT: 임시휴장 2024-12-31, 공표 2024-12-30
    cal.add_holiday("KRX", "2024-12-31", knowable_from="2024-12-30", reason="임시공휴일")
    # as_of 2024-12-01 = 공표 전 → 알 수 없음(거래일로 보임)
    assert not cal.is_holiday("KRX", "2024-12-31", "2024-12-01"), "공표 전 휴장 미가시여야"
    assert cal.is_trading_day("KRX", "2024-12-31", "2024-12-01"), "공표 전엔 거래일로"
    # as_of 2024-12-31 = 공표 후 → 휴장
    assert cal.is_holiday("KRX", "2024-12-31", "2024-12-31"), "공표 후 휴장"
    assert not cal.is_trading_day("KRX", "2024-12-31", "2024-12-31")
    print("2) 휴장 bitemporal PIT: 공표(12-30) 전 미가시 / 후 휴장 OK")

    # 3) UTC 환원 + DST: NYSE 09:30 ET — 여름(EDT, UTC-4)=13:30Z / 겨울(EST, UTC-5)=14:30Z
    su = cal.session_utc("XNYS", "2024-07-01", "2024-12-31")  # 여름
    assert su is not None and su[0].hour == 13 and su[0].minute == 30, su[0]
    wi = cal.session_utc("XNYS", "2024-01-02", "2024-12-31")  # 겨울
    assert wi is not None and wi[0].hour == 14 and wi[0].minute == 30, wi[0]
    print(f"3) NYSE UTC+DST: 여름개장={su[0].time()}Z / 겨울개장={wi[0].time()}Z OK")

    # 3b) KRX 09:00 KST(UTC+9, DST 없음) → 00:00Z
    ks = cal.session_utc("KRX", "2024-06-03", "2024-06-30")
    assert ks is not None and ks[0].hour == 0 and ks[0].minute == 0, ks[0]
    print(f"3b) KRX UTC: 개장 {ks[0].time()}Z (KST 09:00→00:00Z) OK")

    # 4) crypto 24x7: 주말도 거래, 세션 = UTC 자정~자정
    assert cal.is_trading_day("CRYPTO", "2024-06-01", "2024-06-30")  # 토요일도
    cs = cal.session_utc("CRYPTO", "2024-06-01", "2024-06-30")
    assert cs is not None and cs[0].hour == 0 and (cs[1] - cs[0]) == timedelta(days=1), cs
    assert not cal.is_holiday("CRYPTO", "2024-12-31", "2025-01-01")  # 휴장 개념 없음
    print("4) crypto 24x7: 주말 거래 + UTC 자정~자정 세션 OK")

    # 5) next_trading_day: 휴장 PIT 반영 (공표 후엔 12-31 건너뜀)
    # 2024-12-30(월) 다음 = 공표 후엔 12-31 휴장→2025-01-01(수, 신정 미등록이라 거래로 단순화)
    nxt_after = cal.next_trading_day("KRX", "2024-12-30", "2024-12-31")
    assert nxt_after == date(2025, 1, 1), nxt_after  # 12-31 휴장 skip
    # 공표 전 as_of 면 12-31 거래일로 보여 다음 = 12-31
    nxt_before = cal.next_trading_day("KRX", "2024-12-30", "2024-12-01")
    assert nxt_before == date(2024, 12, 31), nxt_before
    print(f"5) next_trading_day PIT: 공표후={nxt_after} (12-31 skip) / 공표전={nxt_before} OK")

    # 6) sys_time 정정: 휴장 취소(__CANCELLED__) 최신 sys_time 채택
    cal.add_holiday("KRX", "2024-09-16", knowable_from="2024-09-01", sys_time="2024-09-01", reason="추석")
    assert cal.is_holiday("KRX", "2024-09-16", "2024-09-10")
    cal.add_holiday("KRX", "2024-09-16", knowable_from="2024-09-01", sys_time="2024-09-12", reason="__CANCELLED__")
    assert not cal.is_holiday("KRX", "2024-09-16", "2024-09-15"), "취소 정정 후 휴장 아님"
    print("6) sys_time 정정: 휴장 취소 최신 row 채택 OK")

    print("calendar (거래소 세션·휴장 bitemporal) self-test PASS")
