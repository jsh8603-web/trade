"""core/data/cv_split.py — purged + embargo CV split provider (R15 §4-3·§1.8).

CONSULT-DECISIONS-weight-20260529.md §1.8 (btn-Inv 분담).

regime-conditional glasso / IC falsification 의 OOS 평가에서 **학습-평가 누수**를 차단하는
데이터 분할 인덱스 제공자. 시계열 라벨이 horizon 을 가지면(feature@t → 라벨이 [t, t+h]
에서 실현) 인접 train/test 가 시간적으로 겹쳐 정보가 샌다.

  - **purge**: train 샘플의 라벨 구간 [t_start, t_end] 이 test 구간과 겹치면 train 에서 제거.
  - **embargo**: test 종료 직후 embargo_days 내 시작하는 train 도 제거(자기상관 누수 — test
    의 정보가 직후 train feature 로 샘, 전이구간 누수 차단 §1.8).

PurgedKFold + Combinatorial Purged CV(CPCV, §3 skfolio 차용 개념) 둘 다 제공. CPCV =
N 그룹 중 k 개를 test 로 하는 모든 조합 → 여러 OOS path(검정력↑).

⛔ mlfinlab 차용 금지(독점 라이선스 페이월, §3) → 알고리즘을 순수 numpy 로 자체구현. 추정
/스코어링은 범위 밖(btn-button) — 본 모듈은 (train_idx, test_idx) 인덱스만 산출.
"""

from __future__ import annotations

from datetime import date, datetime
from itertools import combinations
from typing import Sequence, Union

import numpy as np

TimeLike = Union[str, date, datetime]


def _to_ordinal(x: TimeLike) -> int:
    if isinstance(x, datetime):
        return x.date().toordinal()
    if isinstance(x, date):
        return x.toordinal()
    return datetime.fromisoformat(str(x)).date().toordinal()


def _ordinals(times: Sequence[TimeLike]) -> np.ndarray:
    return np.array([_to_ordinal(t) for t in times], dtype=np.int64)


def _contiguous_runs(sorted_positions: list) -> list:
    """정렬된 위치 리스트를 연속 run [(p0,p1), ...] 로 분해. [3,4,5,9,10]→[(3,5),(9,10)]."""
    runs = []
    if not sorted_positions:
        return runs
    start = prev = sorted_positions[0]
    for p in sorted_positions[1:]:
        if p == prev + 1:
            prev = p
        else:
            runs.append((start, prev))
            start = prev = p
    runs.append((start, prev))
    return runs


def _purge_embargo_train(
    ts: np.ndarray, te: np.ndarray, order: np.ndarray,
    test_orig: np.ndarray, embargo_days: int,
) -> np.ndarray:
    """test_orig(원본 인덱스) 에 대해 purge+embargo 적용한 train 원본 인덱스 산출.

    test 가 비연속(CPCV)일 수 있으므로 정렬 위치에서 연속 run 으로 분해 후 run 별 구간
    [T0,T1] 로 purge(overlap)+embargo(직후) 처리.
    """
    n = len(ts)
    pos_of = np.empty(n, dtype=np.int64)
    pos_of[order] = np.arange(n)
    test_set = set(int(o) for o in test_orig)
    test_positions = sorted(int(pos_of[o]) for o in test_orig)
    remove = np.zeros(n, dtype=bool)
    for p0, p1 in _contiguous_runs(test_positions):
        run_orig = order[p0:p1 + 1]
        T0 = int(ts[run_orig].min())
        T1 = int(te[run_orig].max())
        remove |= (ts <= T1) & (te >= T0)                    # purge: 라벨구간 overlap
        if embargo_days > 0:
            remove |= (ts > T1) & (ts <= T1 + embargo_days)  # embargo: test 직후
    return np.array([o for o in range(n) if o not in test_set and not remove[o]],
                    dtype=np.int64)


def _validate(t_start: Sequence[TimeLike], t_end: Sequence[TimeLike]) -> tuple:
    ts, te = _ordinals(t_start), _ordinals(t_end)
    if len(ts) != len(te):
        raise ValueError("t_start/t_end 길이 불일치")
    if len(ts) == 0:
        raise ValueError("빈 입력")
    if not (te >= ts).all():
        raise ValueError("라벨 구간 위반: t_end < t_start (라벨 실현이 관측보다 과거)")
    return ts, te


def purged_kfold_splits(
    t_start: Sequence[TimeLike], t_end: Sequence[TimeLike], *,
    n_splits: int, embargo_days: int = 0,
) -> list:
    """purged k-fold (+embargo). 반환 = [(train_idx, test_idx), ...] (원본 인덱스 np.ndarray).

    fold = t_start 정렬 후 연속 시간 블록. test 합집합 = 전체, train∩test=∅.
    """
    ts, te = _validate(t_start, t_end)
    n = len(ts)
    if not (1 < n_splits <= n):
        raise ValueError(f"n_splits 는 (1, n={n}] 범위 (받음 {n_splits})")
    order = np.argsort(ts, kind="stable")
    splits = []
    for fp in np.array_split(np.arange(n), n_splits):
        test_orig = order[fp]
        train_orig = _purge_embargo_train(ts, te, order, test_orig, embargo_days)
        splits.append((train_orig, np.sort(test_orig)))
    return splits


def combinatorial_purged_splits(
    t_start: Sequence[TimeLike], t_end: Sequence[TimeLike], *,
    n_groups: int, n_test_groups: int = 2, embargo_days: int = 0,
) -> list:
    """Combinatorial Purged CV (CPCV). N 그룹 중 k 개 test 의 모든 조합 → C(N,k) split.

    여러 OOS path 로 단일 분할의 우연 의존을 줄임(§1.8 IC 검정력). 반환 = [(train, test), ...].
    """
    ts, te = _validate(t_start, t_end)
    n = len(ts)
    if not (1 < n_groups <= n):
        raise ValueError(f"n_groups 는 (1, n={n}] 범위")
    if not (0 < n_test_groups < n_groups):
        raise ValueError("n_test_groups 는 (0, n_groups) 범위")
    order = np.argsort(ts, kind="stable")
    groups = np.array_split(np.arange(n), n_groups)
    splits = []
    for combo in combinations(range(n_groups), n_test_groups):
        test_pos = np.concatenate([groups[g] for g in combo])
        test_orig = order[test_pos]
        train_orig = _purge_embargo_train(ts, te, order, test_orig, embargo_days)
        splits.append((train_orig, np.sort(test_orig)))
    return splits


if __name__ == "__main__":
    # 20 샘플, 일 간격 관측. 라벨 horizon = 5일 (feature@t → 라벨 실현 t+5)
    base = date(2024, 1, 1)
    t_start = [base.toordinal() + i for i in range(20)]
    t_start = [date.fromordinal(o) for o in t_start]
    t_end = [date.fromordinal(o.toordinal() + 5) for o in t_start]   # horizon 5일

    # 1) 기본 분할 불변식: test 합집합=전체, train∩test=∅
    splits = purged_kfold_splits(t_start, t_end, n_splits=4, embargo_days=0)
    assert len(splits) == 4
    all_test = np.sort(np.concatenate([te for _, te in splits]))
    assert (all_test == np.arange(20)).all(), "test 합집합 = 전체"
    for tr, te_ in splits:
        assert len(set(tr.tolist()) & set(te_.tolist())) == 0, "train∩test=∅"
    print(f"1) purged k-fold: 4 fold, test 합집합=전체 20, train∩test=∅ OK")

    # 2) ★purge: train 라벨구간이 test 와 겹치면 제거 (horizon 5일 누수 차단)
    tr0, te0 = splits[1]   # 중간 fold (양쪽 이웃 존재)
    ts_o, te_o = _ordinals(t_start), _ordinals(t_end)
    T0, T1 = ts_o[te0].min(), te_o[te0].max()
    for i in tr0:
        overlaps = (ts_o[i] <= T1) and (te_o[i] >= T0)
        assert not overlaps, f"purge 실패: train {i} 라벨구간이 test [{T0},{T1}] 와 겹침"
    print("2) purge: train 라벨구간(horizon 5일) ∩ test 구간 = 0건 OK")

    # 3) ★embargo: test 종료 직후 embargo_days 내 시작 train 제거
    sp_e = purged_kfold_splits(t_start, t_end, n_splits=4, embargo_days=3)
    tr_e, te_e = sp_e[1]
    T1_e = te_o[te_e].max()
    for i in tr_e:
        in_embargo = (ts_o[i] > T1_e) and (ts_o[i] <= T1_e + 3)
        assert not in_embargo, f"embargo 실패: train {i} 가 test 직후 3일 내"
    assert len(tr_e) <= len(tr0), "embargo 적용 시 train 더 적거나 같음"
    print(f"3) embargo: test 직후 3일 내 train 0건, |train| {len(tr0)}→{len(tr_e)}(embargo) OK")

    # 4) point label(horizon 0): purge 거의 없음 → 표준 kfold 근사
    t_end0 = list(t_start)   # horizon 0
    sp0 = purged_kfold_splits(t_start, t_end0, n_splits=4, embargo_days=0)
    union0 = sum(len(tr) for tr, _ in sp0)
    union5 = sum(len(tr) for tr, _ in splits)
    assert union0 > union5, "point label 은 horizon label 보다 purge 적음(train 많음)"
    print(f"4) point label(h=0) train합={union0} > horizon(h=5) train합={union5} (purge 차이) OK")

    # 5) CPCV: C(6,2)=15 split, 각 split train∩test=∅
    cpcv = combinatorial_purged_splits(t_start, t_end, n_groups=6, n_test_groups=2, embargo_days=2)
    from math import comb
    assert len(cpcv) == comb(6, 2) == 15, len(cpcv)
    for tr, te_ in cpcv:
        assert len(set(tr.tolist()) & set(te_.tolist())) == 0
    print(f"5) CPCV: C(6,2)={len(cpcv)} split, 전부 train∩test=∅ (다중 OOS path) OK")

    # 6) ★라벨 구간 위반 거부: t_end < t_start
    try:
        purged_kfold_splits(t_start, [date.fromordinal(o.toordinal() - 1) for o in t_start],
                            n_splits=3)
        raise AssertionError("t_end<t_start 통과")
    except ValueError as e:
        assert "라벨 구간" in str(e), e
    print("6) 라벨 구간 위반(t_end<t_start) 거부 OK")

    print("cv_split (purged k-fold + CPCV + embargo) self-test PASS")
