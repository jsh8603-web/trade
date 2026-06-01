"""core/pit/as_of.py — canonical as_of resolver (계약 #0, 공통 primitive).

WHY (claude R7): transaction-time as_of 를 모듈마다 다르게 해석하면 reconcile 이
발산한다. T1 bitemporal store, T2 cheapness_z(...,as_of), T3 rule_resolver 가
**전부 동일한 as_of 의미론**을 써야 한다. 그래서 T3 가 단일 resolver 를 소유하고
두 세션(btn-Inv/btn-button)에 "자체 as_of 해석 금지, 이 시그니처에 맞추라" 통지했다.

기존 컨벤션 정합 (`stock/data/macro_vintage.py`):
- as_of 는 시점이며, **미래 as_of 는 lookahead 라 거부**(`as_of.date() > today` → reject).
- ALFRED realtime_start=realtime_end=as_of 로 "그 시점에 알 수 있던 값"만 조회.

이 모듈이 메우는 갭 (T2 structure_model 은 as_of 를 `pd.Timestamp()` 로만 정규화):
1. 미래 as_of 거부 (lookahead 차단)
2. tz-aware → tz-naive 정규화 (transaction-time 일관성, 비교 시 tz 혼재 에러 방지)
3. str/date/datetime/Timestamp 입력을 단일 형태로 수렴 (해석 발산 차단)
4. None as_of 정책 = reject (명시 as_of 강제 — 암묵 today 는 백테스트 lookahead 원천)
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Union

import numpy as np
import pandas as pd

from core.structure import panel_schema as ps

AsOfLike = Union[str, date, datetime, pd.Timestamp]


def _now_naive(now: Optional[AsOfLike]) -> pd.Timestamp:
    """현재 시각 경계 (미래 거부용). now 미지정 시 today 자정 기준."""
    if now is None:
        return pd.Timestamp(date.today())
    return resolve_as_of(now, now=pd.Timestamp.max)  # now 자신은 미래검사 면제


def resolve_as_of(x: AsOfLike, *, now: Optional[AsOfLike] = None) -> pd.Timestamp:
    """임의 as_of 입력 → canonical tz-naive Timestamp.

    - None → ValueError (암묵 today 금지: 백테스트 lookahead 원천 차단)
    - tz-aware → tz-naive 로 변환 (UTC 기준 후 tz drop)
    - 미래(as_of > now/today) → ValueError (lookahead 거부)
    """
    if x is None:
        raise ValueError("as_of=None 금지 — 명시 as_of 필요(암묵 today=lookahead 위험)")
    ts = pd.Timestamp(x)
    if ts.tz is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    if pd.isna(ts):
        raise ValueError(f"as_of 파싱 실패: {x!r}")
    # now=Timestamp.max 는 미래검사 면제 신호 (_now_naive 재귀 차단)
    if now is not None and pd.Timestamp(now) == pd.Timestamp.max:
        return ts
    boundary = _now_naive(now)
    if ts.normalize() > boundary.normalize():
        raise ValueError(f"미래 as_of 거부(lookahead): as_of={ts.date()} > {boundary.date()}")
    return ts


def knowable_filter(panel: pd.DataFrame, as_of: AsOfLike, *, now: Optional[AsOfLike] = None) -> pd.DataFrame:
    """as_of 시점에 알 수 있던 row 만 (knowable_from ≤ as_of). PIT 강제."""
    a = resolve_as_of(as_of, now=now)
    kf = pd.to_datetime(panel[ps.COL_KNOWABLE_FROM])
    return panel[kf <= a]


def cheapness_z_safe(model, firm: str, sector: str, date_: AsOfLike, as_of: AsOfLike,
                     *, now: Optional[AsOfLike] = None) -> float:
    """T2 `model.cheapness_z` 어댑터 — as_of·date 를 canonical resolve 후 호출.

    계약 #2 갭(T2 는 pd.Timestamp 정규화만) 보강: 미래거부·tz정규화를 여기서 단일 책임.
    date_ 는 valuation 관측 시점 (≤ as_of 가 일반적이나 강제는 안 함 — model 이 ≤date 필터).
    """
    a = resolve_as_of(as_of, now=now)
    d = resolve_as_of(date_, now=now) if date_ is not None else a
    return float(model.cheapness_z(firm, sector, d, a))


if __name__ == "__main__":
    NOW = pd.Timestamp("2026-05-29")
    # 1) str/date/datetime/Timestamp 동일 결과
    targets = ["2022-01-01", date(2022, 1, 1), datetime(2022, 1, 1), pd.Timestamp("2022-01-01")]
    vals = [resolve_as_of(t, now=NOW) for t in targets]
    assert all(v == vals[0] for v in vals), vals
    print(f"입력형 4종 동일 수렴: {vals[0].date()} OK")

    # 2) tz-aware → tz-naive
    tzed = resolve_as_of("2022-01-01T00:00:00+09:00", now=NOW)
    assert tzed.tz is None, tzed
    print(f"tz-aware→naive: {tzed} OK")

    # 3) 미래 as_of 거부
    try:
        resolve_as_of("2099-01-01", now=NOW)
        raise AssertionError("미래 as_of 가 통과됨")
    except ValueError as e:
        print(f"미래 거부 OK: {str(e)[:50]}")

    # 4) None 거부
    try:
        resolve_as_of(None)
        raise AssertionError("None 이 통과됨")
    except ValueError:
        print("None 거부 OK")

    # 5) knowable_filter row 수
    panel = ps.make_semiconductor_fixture()
    full = len(panel)
    early = len(knowable_filter(panel, "2018-01-01", now=NOW))
    late = len(knowable_filter(panel, "2024-01-01", now=NOW))
    assert early <= late <= full, (early, late, full)
    print(f"knowable_filter PIT 단조: 2018={early} ≤ 2024={late} ≤ full={full} OK")

    # 6) cheapness_z_safe 어댑터 (미래거부가 model 호출 전 동작)
    from core.structure.structure_model import StructureModel
    m = StructureModel()
    m.fit(panel, resolve_as_of("2022-01-01", now=NOW))
    try:
        cheapness_z_safe(m, "SEMI001", "semiconductor", "2099-01-01", "2099-01-01", now=NOW)
        raise AssertionError("미래 date/as_of 가 어댑터를 통과함")
    except ValueError:
        print("cheapness_z_safe 미래거부 선차단 OK")
    print("S0 as_of resolver self-test PASS")
