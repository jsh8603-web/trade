"""core/data/pit_query.py — AS OF PIT 조회 인터페이스 + 계약0 as_of_resolver seam.

PANEL-SCHEMA-phase2.md §3 PIT 조회 규약 구현. T2·T3 는 이 인터페이스만 통해
패널을 조회한다(raw parquet 직접 필터 = PIT 우회 = 금지). DB 가 PIT 를 강제한다.

★ 계약0 (T3 producer 대기): canonical as_of 의미론은 T3(btn-Codlearn) 의
`as_of_resolver` 를 경유한다(claude R7: transaction-time as_of 해석이 트랙마다
갈리면 reconcile 발산). T3 도착 전까지는 항등 resolver(naive `<=` 비교)로 동작하되,
모든 호출이 `resolve_as_of` 단일 seam 을 경유하므로 wire 는 1곳 교체로 끝난다.

PIT 게이트 2중 (PANEL-SCHEMA §2.1):
  ① knowable_from <= as_of  — filing-lag / 관측 horizon (미래 관측 차단)
  ② sys_time      <= as_of  — silent revision 방어 (미래 정정값 누수 차단)
  → (firm, date) 별 최신 sys_time row = "as_of 시점에 우리가 실제로 알던 값"
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, Iterable, Optional

import pandas as pd

# ---------------------------------------------------------------------------
# 계약0 seam — as_of_resolver (T3 producer 가 wire)
# ---------------------------------------------------------------------------

#: 기본 resolver = 항등(naive transaction-time). T3 가 set_as_of_resolver 로 교체.
_AS_OF_RESOLVER: Callable[[datetime], datetime] = lambda x: x


def set_as_of_resolver(resolver: Callable[[datetime], datetime]) -> None:
    """계약0: T3(btn-Codlearn) canonical as_of_resolver 주입점.

    T3 이 transaction-time as_of 의 정규화(타임존·경계·시장 캘린더) 로직을 제공하면
    이 함수로 wire 한다. 이후 모든 AS OF 조회가 동일 의미론을 공유한다.
    """
    global _AS_OF_RESOLVER
    _AS_OF_RESOLVER = resolver


def resolve_as_of(as_of: datetime) -> datetime:
    """계약0 seam 경유 as_of 정규화. T3 wire 전 = 항등."""
    return _AS_OF_RESOLVER(as_of)


# ---------------------------------------------------------------------------
# AS OF 조회
# ---------------------------------------------------------------------------

BITEMPORAL_KEYS = ("effective_from", "knowable_from", "sys_time")
_GATE_COLS = ("knowable_from", "sys_time")


def _pit_visible(panel: pd.DataFrame, resolved: datetime) -> pd.DataFrame:
    """PIT 게이트 2중 통과 row (firm/date 무관 전체)."""
    ts = pd.Timestamp(resolved)
    return panel[(panel["knowable_from"] <= ts) & (panel["sys_time"] <= ts)]


def as_of_view(panel: pd.DataFrame, as_of: datetime) -> pd.DataFrame:
    """as_of 시점에 알 수 있었던 PIT-correct 패널 슬라이스 전체.

    (firm, date) 별로 sys_time 이 가장 최신인 row 1개만 남긴다 — silent revision
    이 있어도 "그때 알던 최신값"을 재현. T2 가 cross-sectional 잔차 적합에 쓴다.
    """
    resolved = resolve_as_of(as_of)
    visible = _pit_visible(panel, resolved)
    if visible.empty:
        return visible
    # (firm,date) 별 최신 sys_time 선택
    idx = visible.groupby(["firm", "date"])["sys_time"].idxmax()
    return visible.loc[idx].reset_index(drop=True)


def query_as_of(
    panel: pd.DataFrame,
    firm: str,
    date: datetime,
    as_of: datetime,
) -> Optional[pd.Series]:
    """단일 (firm, date) 의 as_of 시점 PIT row.

    PANEL-SCHEMA §3 query_as_of 규약. 없으면 None.
    """
    resolved = pd.Timestamp(resolve_as_of(as_of))
    date_ts = pd.Timestamp(date)
    rows = panel[
        (panel["firm"] == firm)
        & (panel["date"] == date_ts)
        & (panel["knowable_from"] <= resolved)
        & (panel["sys_time"] <= resolved)
    ]
    if rows.empty:
        return None
    return rows.sort_values("sys_time").iloc[-1]


# ---------------------------------------------------------------------------
# PitPanel 래퍼 — parquet 로드 + AS OF 조회 캡슐화
# ---------------------------------------------------------------------------

class PitPanel:
    """패널 parquet 래퍼. T2/T3 가 이 객체로 AS OF 조회한다."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    @classmethod
    def load(cls, path: str) -> "PitPanel":
        return cls(pd.read_parquet(path))

    def as_of(self, as_of: datetime) -> pd.DataFrame:
        """as_of 시점 PIT-correct 전체 슬라이스."""
        return as_of_view(self.df, as_of)

    def query(self, firm: str, date: datetime, as_of: datetime) -> Optional[pd.Series]:
        """단일 (firm, date) 의 as_of 시점 row."""
        return query_as_of(self.df, firm, date, as_of)


# ---------------------------------------------------------------------------
# IA-3 확장 — 파생값 PIT 무결성 (synth_knowable_from + 참조 무결성)
# ---------------------------------------------------------------------------

def synth_knowable_from(
    input_knowable_froms: Iterable[datetime],
    *,
    compute_delay: timedelta = timedelta(0),
) -> datetime:
    """파생값의 knowable_from = max(입력 knowable_from) + compute_delay.

    claude R3 invariant: 파생값(신호·DerivedParameter·FDR 입력)은 **모든 입력이 알려진 뒤 +
    계산 지연** 후에야 알 수 있다. 입력보다 이른 knowable_from 을 주장하면 = 입력 前 가시 =
    lookahead. write-time 에 이 값을 동결 materialize 하고 replay 에서 재계산하지 않는다.
    """
    ks = [pd.Timestamp(k) for k in input_knowable_froms]
    if not ks:
        raise ValueError("입력 knowable_from 0개 — 파생값 PIT 산정 불가")
    return (max(ks) + compute_delay).to_pydatetime()


def assert_referential_pit(
    seed_refs: Iterable[tuple],          # [(assumption_id, version), ...]
    as_of: datetime,
    is_active: Callable[[str, str, datetime], bool],
) -> None:
    """파생 seed 가 참조하는 가정들이 as_of 에 **active** 였는지 검증(T3 is_active 계약).

    참조 무결성: replay 시 그 시점 비활성/미존재 가정을 참조하면 PIT 재현이 깨진다(은퇴된
    가정으로 과거 결정을 정당화 = dangling reference). 하나라도 비활성이면 ValueError.
    is_active(assumption_id, version, as_of) = T3(btn-Codlearn) assumption_store 계약.
    """
    resolved = pd.Timestamp(resolve_as_of(as_of)).to_pydatetime()
    dangling = [(aid, ver) for aid, ver in seed_refs
                if not is_active(aid, ver, resolved)]
    if dangling:
        raise ValueError(f"참조 무결성 위반(as_of={resolved.date()}): "
                         f"비활성/미존재 가정 참조 {dangling}")


if __name__ == "__main__":
    from datetime import date

    # 1) synth_knowable_from: max(입력) + compute_delay
    inputs = [datetime(2024, 1, 10), datetime(2024, 1, 15), datetime(2024, 1, 12)]
    kf = synth_knowable_from(inputs, compute_delay=timedelta(days=1))
    assert kf == datetime(2024, 1, 16), kf
    print(f"1) synth_knowable_from: max(01-15)+1d = {kf.date()} OK")

    # 2) 입력 前 가시 차단: 파생 knowable_from 은 항상 모든 입력 ≥
    assert synth_knowable_from(inputs) == datetime(2024, 1, 15), "delay 0 = max"
    assert kf >= max(inputs), "파생값은 입력보다 이르게 알 수 없음"
    print("2) 입력 前 가시 차단: 파생 knowable ≥ max(입력) OK")

    # 3) 참조 무결성: as_of 에 active 가정만 통과 (T3 is_active 계약 모킹)
    active_set = {("A1", "1"), ("A2", "2")}  # as_of 시점 활성 가정
    def is_active(aid, ver, as_of):
        return (aid, ver) in active_set
    assert_referential_pit([("A1", "1"), ("A2", "2")], datetime(2024, 6, 1), is_active)
    print("3) 참조 무결성: 활성 가정만 참조 → 통과 OK")

    # 4) dangling reference 거부: 비활성/미존재 가정 참조 = ValueError
    try:
        assert_referential_pit([("A1", "1"), ("A9", "1")], datetime(2024, 6, 1), is_active)
        raise AssertionError("dangling 참조가 통과함")
    except ValueError as e:
        assert "A9" in str(e), e
    print("4) dangling reference(A9 미존재) 거부 OK")

    print("pit_query (AS OF + IA-3 파생 PIT 무결성) self-test PASS")
