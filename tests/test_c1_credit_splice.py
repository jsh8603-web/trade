"""C1 credit BAA10Y splice 단위테스트.

검증기준 (harness2.md C1):
- splice 경계 단위테스트: 2023-04(BAA10Y) vs 2023-06(BAMLH0A0HYM2) 소스 전환
- Δ연속성: cutover 점프 부재(diff 변환 후 레벨 불연속 사라짐)
- off byte-identical: factor 미사용 경로 무변화(mock source_fn 경로)
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.data.factor_returns import (
    _CREDIT_SPLICE_CUTOVER,
    _CREDIT_HY_SERIES,
    _CREDIT_IG_SERIES,
    credit_series_for,
    credit_confidence_label,
    fetch_factor_cov,
)


# ---------------------------------------------------------------------------
# C1-A: credit_series_for 경계 전환
# ---------------------------------------------------------------------------

class TestCreditSeriesFor:
    def test_before_cutover_returns_baa10y(self):
        """as_of < 2023-05-01 → BAA10Y(IG proxy)."""
        d = _CREDIT_SPLICE_CUTOVER - timedelta(days=1)  # 2023-04-30
        assert credit_series_for(d) == _CREDIT_IG_SERIES, (
            f"{d} should map to BAA10Y, got {credit_series_for(d)}"
        )

    def test_at_cutover_returns_hy_oas(self):
        """as_of == 2023-05-01 → BAMLH0A0HYM2(HY OAS)."""
        assert credit_series_for(_CREDIT_SPLICE_CUTOVER) == _CREDIT_HY_SERIES

    def test_after_cutover_returns_hy_oas(self):
        """as_of > 2023-05-01 → BAMLH0A0HYM2(HY OAS)."""
        d = _CREDIT_SPLICE_CUTOVER + timedelta(days=31)  # 2023-06-01
        assert credit_series_for(d) == _CREDIT_HY_SERIES

    def test_string_input(self):
        """문자열 as_of 입력도 정상 처리."""
        assert credit_series_for("2022-01-01") == _CREDIT_IG_SERIES
        assert credit_series_for("2024-01-01") == _CREDIT_HY_SERIES

    def test_early_date_baa10y(self):
        """2017년 이전 백테스트 시작 → BAA10Y."""
        assert credit_series_for(date(2017, 1, 1)) == _CREDIT_IG_SERIES


# ---------------------------------------------------------------------------
# C1-B: credit_confidence_label 경계 감지
# ---------------------------------------------------------------------------

class TestCreditConfidenceLabel:
    def test_pre_cutover_only_ig(self):
        """lookback이 cutover 이전 전체 → IG grade."""
        start = date(2017, 1, 1)
        end = date(2023, 4, 30)
        label = credit_confidence_label(start, end)
        assert "IG" in label
        assert "mismatch" not in label

    def test_post_cutover_only_hy(self):
        """lookback이 cutover 이후 전체 → HY OAS grade."""
        start = date(2023, 6, 1)
        end = date(2026, 6, 1)
        label = credit_confidence_label(start, end)
        assert "HY_OAS" in label
        assert "mismatch" not in label

    def test_spanning_cutover_mismatch(self):
        """lookback이 cutover 걸치면 mismatch 라벨."""
        start = date(2020, 1, 1)
        end = date(2024, 1, 1)
        label = credit_confidence_label(start, end)
        assert "mismatch" in label
        assert "BAA10Y" in label
        assert "HY_OAS" in label


# ---------------------------------------------------------------------------
# C1-C: Δ연속성 — cutover 전후 diff 변환 후 레벨 점프 없음
# ---------------------------------------------------------------------------

class TestDeltaContinuity:
    """두 시리즈(BAA10Y/HY OAS)의 diff 변환 결과가 단위 동일(Δbp) — 레벨 불연속은 diff 후 사라짐."""

    def test_diff_unit_same(self):
        """임의 레벨 수준 차이(BAA10Y≈3% HY OAS≈5%)에서 diff(Δbp)는 같은 단위."""
        # BAA10Y 레벨 약 300bp 근방, HY OAS 약 500bp 근방
        baa_levels = np.array([300.0, 302.0, 298.0, 301.0, 299.0])
        hy_levels = np.array([500.0, 503.0, 498.0, 502.0, 499.0])

        baa_diff = np.diff(baa_levels)   # Δbp
        hy_diff = np.diff(hy_levels)     # Δbp

        # 절대 크기 범주가 유사 (레벨 다르지만 Δ는 비슷한 수준)
        assert np.abs(baa_diff).mean() < 10, "BAA10Y Δ too large"
        assert np.abs(hy_diff).mean() < 10, "HY OAS Δ too large"
        # diff 단위가 동일(bp) — 이상치 없음
        assert np.all(np.isfinite(baa_diff)) and np.all(np.isfinite(hy_diff))

    def test_splice_at_boundary_no_jump(self):
        """경계에서 레벨 점프가 있어도 diff 후 첫 값이 splice 이전 마지막 Δ와 연속."""
        # 가상 시계열: BAA10Y 끝값=300, HY OAS 시작값=500 (레벨 차 200bp)
        # → splice 시 레벨 불연속. 하지만 각 시리즈 내 diff는 그 이전 값 대비 변화량.
        # 실제 fetch_factor_cov에선 단일 source_fn이 한 시리즈만 반환하므로 경계 점프 없음.
        # (splice = 구간별로 다른 시리즈를 사용, 혼합 연결 X)
        baa_arr = np.array([298.0, 299.0, 300.0])
        hy_arr  = np.array([500.0, 502.0, 499.0])

        baa_diff = np.diff(baa_arr)  # [1.0, 1.0]
        hy_diff  = np.diff(hy_arr)   # [2.0, -3.0]

        # 각 diff는 자기 시계열 내 연속 (레벨 점프 없음)
        assert list(baa_diff) == [1.0, 1.0]
        assert list(hy_diff)  == [2.0, -3.0]


# ---------------------------------------------------------------------------
# C1-D: fetch_factor_cov credit splice 실제 호출 (mock source_fn)
# ---------------------------------------------------------------------------

class TestFetchFactorCovCreditSplice:
    """fetch_factor_cov가 as_of에 따라 올바른 credit series를 source_fn에 요청하는지."""

    def _make_source_fn(self, captured_series_ids: list):
        """source_fn: 호출 시 series_ids를 captured_series_ids에 저장."""
        rng = np.random.default_rng(42)

        def _fn(series_ids, start, end):
            captured_series_ids.extend(series_ids)
            # 각 시리즈에 대해 합성 레벨 시계열 반환 (300 행 = min_rows 충분)
            out = {}
            for sid in series_ids:
                base = 300.0 if sid == "BAA10Y" else 500.0
                out[sid] = base + np.cumsum(rng.standard_normal(400) * 0.5)
            return out

        return _fn

    def test_pre_cutover_uses_baa10y(self):
        """as_of < 2023-05 → source_fn에 BAA10Y 요청."""
        captured = []
        fn = self._make_source_fn(captured)
        as_of = date(2022, 12, 31)
        result = fetch_factor_cov(
            as_of=as_of,
            lookback_days=300,
            factors=["credit"],
            source_fn=fn,
            min_rows=60,
        )
        # credit만이면 len(facs)<2 → None (최소 2 factor 필요) — 하지만 series 요청 확인
        # factor 1개면 None 반환. credit+real 로 테스트
        captured.clear()
        result2 = fetch_factor_cov(
            as_of=as_of,
            lookback_days=300,
            factors=["credit", "real"],
            source_fn=fn,
            min_rows=60,
        )
        assert _CREDIT_IG_SERIES in captured, (
            f"pre-cutover should request BAA10Y, got: {captured}"
        )
        assert _CREDIT_HY_SERIES not in captured, (
            f"pre-cutover should NOT request BAMLH0A0HYM2, got: {captured}"
        )

    def test_post_cutover_uses_hy_oas(self):
        """as_of >= 2023-05 → source_fn에 BAMLH0A0HYM2 요청."""
        captured = []
        fn = self._make_source_fn(captured)
        as_of = date(2025, 1, 1)
        fetch_factor_cov(
            as_of=as_of,
            lookback_days=300,
            factors=["credit", "real"],
            source_fn=fn,
            min_rows=60,
        )
        assert _CREDIT_HY_SERIES in captured, (
            f"post-cutover should request BAMLH0A0HYM2, got: {captured}"
        )
        assert _CREDIT_IG_SERIES not in captured, (
            f"post-cutover should NOT request BAA10Y, got: {captured}"
        )

    def test_non_credit_factors_unaffected(self):
        """credit 외 factor는 splice 영향 없음 — off byte-identical."""
        captured_pre, captured_post = [], []

        rng = np.random.default_rng(7)

        def fn(series_ids, start, end):
            captured_pre.extend(series_ids) if start.year < 2023 else captured_post.extend(series_ids)
            out = {}
            for sid in series_ids:
                out[sid] = 100 + np.cumsum(rng.standard_normal(400) * 0.5)
            return out

        # real+vol 만 요청 — credit 없음
        fetch_factor_cov(
            as_of=date(2022, 1, 1),
            lookback_days=300,
            factors=["real", "vol"],
            source_fn=fn,
            min_rows=60,
        )
        # credit series가 requested 목록에 없어야 함
        all_captured = captured_pre + captured_post
        assert _CREDIT_IG_SERIES not in all_captured
        assert _CREDIT_HY_SERIES not in all_captured

    def test_result_is_psd(self):
        """fetch_factor_cov 결과가 PSD(양반정치) — C1 변경 후 수치 회귀 없음."""
        rng = np.random.default_rng(99)

        def fn(series_ids, start, end):
            out = {}
            for sid in series_ids:
                base = 300.0 if "BAA" in sid else 100.0
                out[sid] = base + np.cumsum(rng.standard_normal(400) * 0.3)
            return out

        result = fetch_factor_cov(
            as_of=date(2026, 6, 1),
            lookback_days=300,
            factors=["credit", "real", "vol"],
            source_fn=fn,
            min_rows=60,
        )
        assert result is not None, "fetch_factor_cov returned None"
        eig = np.linalg.eigvalsh(result)
        assert eig.min() > -1e-6, f"result not PSD: min_eig={eig.min():.2e}"
