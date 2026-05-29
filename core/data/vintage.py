"""core/data/vintage.py — 거시/지표 vintage open-sequence (IA-3·IA-6, 자문 R1 #1 직격).

전체구조 자문 R1 #1(가장 silent 한 결함): 거시지표 **사후 revision** 을 별 bitemporal fact
로 안 쪼개면 backtest 가 **revised lookahead alpha** 를 먹는다 — 에러 없이, 라이브 하회로만
드러난다. GDP 2024-Q1 이 처음 +2.0% 로 발표됐다가 한 달 뒤 +2.5% 로 개정되면, 그 시점
의사결정은 2.0% 만 알 수 있었는데 backtest 가 final(2.5%)을 쓰면 미래 정보 누수.

설계: 같은 (series, period) 의 여러 vintage 를 **open-sequence 로 append**.
- realtime(series, period, as_of) = as_of 에 알 수 있던 값(vintage_knowable_from ≤ as_of 최신)
- final(series, period) = 최신 vintage(= 개정된 '진실', backtest 에 쓰면 lookahead)
- revision_drift = realtime − final (의사결정이 본 값 vs 나중 진실의 간극)

event_ledger 연계: realtime 값으로 PREDICTION_MADE, 개정 도착 시 REVISION_OBSERVED emit
(OUTCOME mutate 금지). data_vintage 공통필드 = vintage_knowable_from.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Union

AsOfLike = Union[str, date, datetime]


def _d(x: AsOfLike) -> date:
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return datetime.fromisoformat(str(x)).date()


@dataclass(frozen=True)
class VintageObservation:
    """단일 vintage. period=측정 대상 기간, vintage_knowable_from=그 vintage 공표 시점."""
    series_id: str
    period: str                  # 측정 대상 기간 라벨 (예: "2024-Q1", "2024-01")
    value: float
    vintage_knowable_from: date  # 이 vintage 를 알게 된 시점
    sys_time: date               # 기록/정정 시점


class VintageStore:
    """거시/지표 vintage open-sequence 저장소. append-only(개정마다 새 row)."""

    def __init__(self) -> None:
        self._obs: list[VintageObservation] = []

    def add(self, series_id: str, period: str, value: float, vintage_knowable_from: AsOfLike,
            *, sys_time: Optional[AsOfLike] = None) -> VintageObservation:
        kf = _d(vintage_knowable_from)
        ob = VintageObservation(series_id, period, float(value), kf,
                                _d(sys_time) if sys_time is not None else kf)
        self._obs.append(ob)
        return ob

    def _candidates(self, series_id: str, period: str, as_of: Optional[date]) -> list[VintageObservation]:
        out = [o for o in self._obs if o.series_id == series_id and o.period == period]
        if as_of is not None:
            out = [o for o in out if o.vintage_knowable_from <= as_of and o.sys_time <= as_of]
        return out

    def realtime(self, series_id: str, period: str, as_of: AsOfLike) -> Optional[float]:
        """as_of 에 알 수 있던 값 = vintage_knowable_from ≤ as_of 중 최신 vintage(개정 반영)."""
        cands = self._candidates(series_id, period, _d(as_of))
        if not cands:
            return None
        # 최신 vintage_knowable_from, 동률이면 최신 sys_time
        return max(cands, key=lambda o: (o.vintage_knowable_from, o.sys_time)).value

    def final(self, series_id: str, period: str, as_of: Optional[AsOfLike] = None) -> Optional[float]:
        """현재(또는 as_of) 시점의 최신 개정값 = '진실'. backtest 에 쓰면 lookahead 경고 대상."""
        cands = self._candidates(series_id, period, _d(as_of) if as_of is not None else None)
        if not cands:
            return None
        return max(cands, key=lambda o: (o.vintage_knowable_from, o.sys_time)).value

    def revision_drift(self, series_id: str, period: str, decision_as_of: AsOfLike) -> Optional[float]:
        """의사결정이 본 realtime 값 − final 진실. !=0 이면 그 결정은 개정 전 정보로 내려짐.

        backtest-on-final 이 먹었을 lookahead 크기 = -drift(final 이 realtime 보다 유리한 만큼).
        """
        rt = self.realtime(series_id, period, decision_as_of)
        fn = self.final(series_id, period)
        if rt is None or fn is None:
            return None
        return rt - fn

    def vintage_count(self, series_id: str, period: str) -> int:
        return len(self._candidates(series_id, period, None))


if __name__ == "__main__":
    vs = VintageStore()
    # GDP 2024-Q1: 속보 +2.0(04-30) → 잠정 +2.3(05-30) → 확정 +2.5(06-27)
    vs.add("GDP", "2024-Q1", 2.0, "2024-04-30")
    vs.add("GDP", "2024-Q1", 2.3, "2024-05-30")
    vs.add("GDP", "2024-Q1", 2.5, "2024-06-27")

    # 1) ★realtime PIT: 의사결정 시점별 다른 값(개정 누수 차단)
    assert vs.realtime("GDP", "2024-Q1", "2024-05-15") == 2.0, "05-15=속보만"
    assert vs.realtime("GDP", "2024-Q1", "2024-06-10") == 2.3, "06-10=잠정"
    assert vs.realtime("GDP", "2024-Q1", "2024-07-01") == 2.5, "07-01=확정"
    print("1) realtime PIT: 05-15→2.0 / 06-10→2.3 / 07-01→2.5 (개정 누수 차단) OK")

    # 2) final = 최신 개정 진실
    assert vs.final("GDP", "2024-Q1") == 2.5
    print("2) final = 2.5 (최신 개정 '진실') OK")

    # 3) ★revision_drift: 05-15 결정은 2.0 봤지만 진실 2.5 → drift=-0.5
    #    backtest-on-final(2.5)이 먹었을 lookahead = +0.5 (실제론 몰랐던 상향)
    d = vs.revision_drift("GDP", "2024-Q1", "2024-05-15")
    assert abs(d - (2.0 - 2.5)) < 1e-9, d
    print(f"3) revision_drift(05-15 결정): {d:+.1f} (realtime 2.0 − final 2.5, backtest-on-final lookahead 노출) OK")

    # 4) 공표 前 미가시
    assert vs.realtime("GDP", "2024-Q1", "2024-04-01") is None, "속보 前 미가시"
    print("4) 속보 공표(04-30) 前 realtime=None OK")

    # 5) sys_time 정정: 05-30 잠정값을 2.3→2.35 로 기록 정정(최신 sys_time)
    vs.add("GDP", "2024-Q1", 2.35, vintage_knowable_from="2024-05-30", sys_time="2024-06-05")
    assert vs.realtime("GDP", "2024-Q1", "2024-06-03") == 2.3, "정정 前(06-03)=2.3"
    assert vs.realtime("GDP", "2024-Q1", "2024-06-10") == 2.35, "정정 後(06-10)=2.35"
    print("5) sys_time 정정: 잠정값 06-05 정정 → 06-03 미가시(2.3)/06-10 가시(2.35) OK")

    print(f"6) vintage_count(GDP 2024-Q1) = {vs.vintage_count('GDP', '2024-Q1')} (open-sequence)")
    print("vintage (open-sequence realtime/final + revision-drift) self-test PASS")
