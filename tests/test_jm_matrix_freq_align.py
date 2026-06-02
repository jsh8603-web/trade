"""tests/test_jm_matrix_freq_align.py — JM 입력행렬 빈도정렬 회귀(2026-06-02 insufficient_data fix).

_build_jm_matrix 가 일/주/월 혼합 빈도 시리즈를 공통 월말(ME) 그리드로 정렬하지 못해
`DataFrame(cols).dropna()` inner-join 교집합 ≈ 0 → X 0행 → JM 이 *항상* insufficient_data
였던 버그 박제. 실측 진단: 월별 yoy(매월 1일)·resample ME diff(월말)·breakeven 일별 yoy
세 빈도가 섞여 교집합 소멸. fix = 모든 시리즈 ME.last() 월말 통일 후 변환.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from core.brain.fred_adapter import MacroFeatureBundle
from core.brain.regime_classifier import RegimeClassifier


def _monthly(start, n, base=100.0):
    idx = pd.date_range(start, periods=n, freq="MS")       # 매월 1일(월초 라벨)
    return pd.Series(np.linspace(base, base * 1.5, n), index=idx)


def _daily(start, n, base=2.0):
    idx = pd.date_range(start, periods=n, freq="B")        # 영업일(일별)
    rng = np.random.default_rng(0)
    return pd.Series(base + np.cumsum(rng.normal(0, 0.01, n)), index=idx)


def _bare_classifier():
    """__init__(FRED fetch) 우회 — _build_jm_matrix 는 self 미사용(b 인자만)."""
    return RegimeClassifier.__new__(RegimeClassifier)


def test_build_jm_matrix_aligns_mixed_freq():
    """월별(1일) + 일별 혼합 → 월말 그리드 정렬 → X len>=60 (이전 버그: 0행 → None)."""
    b = MacroFeatureBundle(series={
        "industrial_production": _monthly("2005-01-01", 240),   # 월별 1일 라벨
        "core_cpi": _monthly("2005-01-01", 240),
        "unemployment_rate": _monthly("2005-01-01", 240),
        "yield_10y_2y": _daily("2005-01-01", 5000),             # 일별 → resample ME diff
        "real_rate_10y": _daily("2005-01-01", 5000),
        "breakeven_5y": _daily("2005-01-01", 5000),             # 이전 diff_list 누락 케이스
    })
    X, ret = _bare_classifier()._build_jm_matrix(b)
    assert X is not None, "혼합 빈도 정렬 실패 → X None(회귀 재발)"
    assert len(X) >= 60
    assert ret is not None and len(ret) == len(X)
    assert X.index.is_monotonic_increasing
    assert (X.index.day >= 28).all(), "월말 그리드 통일 안 됨"   # 전부 월말 라벨


def test_build_jm_matrix_excludes_short_series():
    """짧은 시리즈(≈35mo, hy_oas 류) 섞여도 전체 X 절단 안 함(변환후 60mo 미만 제외)."""
    b = MacroFeatureBundle(series={
        "industrial_production": _monthly("2005-01-01", 240),
        "core_cpi": _monthly("2005-01-01", 240),
        "unemployment_rate": _monthly("2005-01-01", 240),
        "credit_spread_hy_oas": _daily("2023-06-01", 760),      # ≈35mo → 제외돼야
    })
    X, _ = _bare_classifier()._build_jm_matrix(b)
    assert X is not None and len(X) >= 60                       # 긴 3종으로 X 확보
    assert "credit_spread_hy_oas" not in X.columns             # 짧은 시리즈 미포함


def test_build_jm_matrix_insufficient_when_too_few():
    """유효 컬럼 < 3 → None(graceful, jm_status=insufficient_data 경로)."""
    b = MacroFeatureBundle(series={
        "industrial_production": _monthly("2005-01-01", 240),
        "core_cpi": _monthly("2005-01-01", 240),
    })
    X, ret = _bare_classifier()._build_jm_matrix(b)
    assert X is None and ret is None
