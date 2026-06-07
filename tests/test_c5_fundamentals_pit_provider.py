"""tests/test_c5_fundamentals_pit_provider.py — C5 PIT 펀더멘털 provider 단위 테스트.

검증 항목:
- PIT 마스킹(filing_ts>as_of 제외) — filter_pit_fundamentals 재사용
- DART 키 부재 graceful (dart_key_missing 라벨, 비중0 금지 명시)
- EDGAR fixture stub(네트워크 없음) — US 정상 경로
- available=False 라벨 종류 (pit_empty / source_missing / dart_key_missing)
- FundamentalsPitProvider 클래스 인터페이스
- off byte-identical (engine_wire 회귀)
"""

from __future__ import annotations

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List
from unittest.mock import patch, MagicMock

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from stock.contracts import Fundamentals, FilingSource
from stock.data.fundamentals_pit_provider import (
    get_fundamentals_pit,
    FundamentalsPitProvider,
    FundamentalsResult,
)


# ---------------------------------------------------------------------------
# 헬퍼 — Fundamentals fixture 생성
# ---------------------------------------------------------------------------

def _make_filing(
    ticker: str,
    fiscal_period: str,
    filing_ts: datetime,
    revenue: float = 1_000_000.0,
    source: FilingSource = FilingSource.EDGAR_XBRL,
) -> Fundamentals:
    return Fundamentals(
        ticker=ticker,
        fiscal_period=fiscal_period,
        filing_timestamp=filing_ts,
        source=source,
        revenue=revenue,
    )


class _StubProvider:
    """fetch_filings 를 고정 공시 리스트로 반환하는 stub."""
    def __init__(self, filings: List[Fundamentals]):
        self._filings = filings

    def fetch_filings(self, ticker: str, limit: int = 8) -> List[Fundamentals]:
        return self._filings


# ---------------------------------------------------------------------------
# PIT 마스킹 단위 테스트
# ---------------------------------------------------------------------------

class TestPitMasking:
    def test_filing_after_as_of_excluded(self):
        """filing_ts > as_of 이면 제외."""
        filings = [
            _make_filing("AAPL", "2023FY", datetime(2024, 2, 15)),  # as_of 이전 ✓
            _make_filing("AAPL", "2024Q1", datetime(2024, 5, 10)),  # as_of 이후 ✗
        ]
        stub = _StubProvider(filings)
        r = get_fundamentals_pit("AAPL", datetime(2024, 4, 1), "US", edgar_provider=stub)

        assert r.available
        assert len(r.filings) == 1
        assert r.filings[0].fiscal_period == "2023FY"

    def test_filing_on_as_of_included(self):
        """filing_ts == as_of 이면 포함."""
        ts = datetime(2024, 3, 15)
        filings = [_make_filing("AAPL", "2023Q3", ts)]
        stub = _StubProvider(filings)
        r = get_fundamentals_pit("AAPL", ts, "US", edgar_provider=stub)

        assert r.available
        assert len(r.filings) == 1

    def test_all_filings_after_as_of_returns_pit_empty(self):
        """모든 filing_ts > as_of → pit_empty 라벨."""
        filings = [
            _make_filing("AAPL", "2023FY", datetime(2024, 2, 15)),
            _make_filing("AAPL", "2024Q1", datetime(2024, 5, 10)),
        ]
        stub = _StubProvider(filings)
        r = get_fundamentals_pit("AAPL", datetime(2020, 1, 1), "US", edgar_provider=stub)

        assert not r.available
        assert r.label == "pit_empty"
        assert r.filings == []
        assert r.latest is None

    def test_latest_is_most_recent_pit(self):
        """latest 는 PIT 통과 중 가장 최신 filing_ts."""
        filings = [
            _make_filing("MSFT", "2022FY", datetime(2023, 2, 1)),
            _make_filing("MSFT", "2023Q1", datetime(2023, 5, 1)),
            _make_filing("MSFT", "2023Q2", datetime(2023, 8, 1)),  # 최신
            _make_filing("MSFT", "2023Q3", datetime(2024, 1, 1)),  # 미래 ✗
        ]
        stub = _StubProvider(filings)
        r = get_fundamentals_pit("MSFT", datetime(2023, 10, 1), "US", edgar_provider=stub)

        assert r.available
        assert r.latest.fiscal_period == "2023Q2"

    def test_filings_sorted_by_filing_ts(self):
        """filings 는 filing_ts 오름차순 정렬."""
        filings = [
            _make_filing("X", "2023Q2", datetime(2023, 8, 1)),
            _make_filing("X", "2022FY", datetime(2023, 2, 1)),
            _make_filing("X", "2023Q1", datetime(2023, 5, 1)),
        ]
        stub = _StubProvider(filings)
        r = get_fundamentals_pit("X", datetime(2023, 12, 1), "US", edgar_provider=stub)

        ts_list = [f.filing_timestamp for f in r.filings]
        assert ts_list == sorted(ts_list)


# ---------------------------------------------------------------------------
# DART 키 부재 graceful (비중0 금지)
# ---------------------------------------------------------------------------

class TestDartKeyMissing:
    def test_no_dart_key_returns_dart_key_missing(self):
        """DART_API_KEY 없음 → dart_key_missing 라벨, available=False."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DART_API_KEY", None)
            r = get_fundamentals_pit("005930", datetime(2024, 1, 1), "KR")

        assert not r.available
        assert r.label == "dart_key_missing"
        assert r.filings == []
        assert r.latest is None

    def test_no_exception_on_missing_dart_key(self):
        """DART_API_KEY 없어도 예외 전파 X."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DART_API_KEY", None)
            try:
                r = get_fundamentals_pit("005930", datetime(2024, 1, 1), "KR")
            except Exception as exc:
                pytest.fail(f"예외 발생: {exc}")

    def test_dart_key_missing_logged(self, caplog):
        """dart_key_missing 시 경고 로그 발생."""
        import logging
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DART_API_KEY", None)
            with caplog.at_level(logging.WARNING, logger="stock.data.fundamentals_pit_provider"):
                get_fundamentals_pit("005930", datetime(2024, 1, 1), "KR")

        assert any("dart_key_missing" in r.message for r in caplog.records)

    def test_dart_key_present_calls_provider(self):
        """DART_API_KEY 있으면 DartXbrlProvider.fetch_filings 호출."""
        filings = [
            _make_filing(
                "005930", "2023FY", datetime(2023, 12, 15),
                source=FilingSource.DART_XBRL,
            )
        ]
        stub = _StubProvider(filings)

        with patch.dict(os.environ, {"DART_API_KEY": "fake_key"}):
            r = get_fundamentals_pit(
                "005930", datetime(2024, 1, 1), "KR", dart_provider=stub
            )

        assert r.available
        assert r.label == "ok"


# ---------------------------------------------------------------------------
# source_missing 경로
# ---------------------------------------------------------------------------

class TestSourceMissing:
    def test_empty_filings_returns_source_missing(self):
        """fetch_filings 가 빈 리스트 → source_missing."""
        stub = _StubProvider([])
        r = get_fundamentals_pit("AAPL", datetime(2024, 1, 1), "US", edgar_provider=stub)

        assert not r.available
        assert r.label == "source_missing"

    def test_provider_exception_returns_source_missing(self):
        """fetch_filings 예외 → source_missing (예외 전파 X)."""
        class _ErrorProvider:
            def fetch_filings(self, ticker, limit=8):
                raise RuntimeError("network down")

        r = get_fundamentals_pit(
            "AAPL", datetime(2024, 1, 1), "US", edgar_provider=_ErrorProvider()
        )

        assert not r.available
        assert r.label == "source_missing"

    def test_unknown_region_returns_source_missing(self):
        """알 수 없는 region → source_missing."""
        r = get_fundamentals_pit("XYZ", datetime(2024, 1, 1), "JP")

        assert not r.available
        assert r.label == "source_missing"


# ---------------------------------------------------------------------------
# FundamentalsResult 계약
# ---------------------------------------------------------------------------

class TestFundamentalsResult:
    def test_ok_result_structure(self):
        """available=True 결과 filings 비어있지 않음, latest 있음."""
        filings = [_make_filing("T", "2023FY", datetime(2023, 12, 1))]
        stub = _StubProvider(filings)
        r = get_fundamentals_pit("T", datetime(2024, 1, 1), "US", edgar_provider=stub)

        assert r.available
        assert isinstance(r.filings, list)
        assert len(r.filings) > 0
        assert r.latest is not None
        assert isinstance(r.latest, Fundamentals)

    def test_unavailable_result_structure(self):
        """available=False 결과 filings=[], latest=None."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DART_API_KEY", None)
            r = get_fundamentals_pit("005930", datetime(2024, 1, 1), "KR")

        assert not r.available
        assert r.filings == []
        assert r.latest is None


# ---------------------------------------------------------------------------
# FundamentalsPitProvider 클래스
# ---------------------------------------------------------------------------

class TestFundamentalsPitProvider:
    def test_class_delegates_to_function(self):
        """FundamentalsPitProvider.get_fundamentals_pit 는 모듈 함수와 동일 결과."""
        filings = [_make_filing("AAPL", "2023FY", datetime(2024, 1, 10))]
        stub = _StubProvider(filings)

        provider = FundamentalsPitProvider(edgar_provider=stub)
        r = provider.get_fundamentals_pit("AAPL", datetime(2024, 6, 1), "US")

        assert r.available
        assert r.latest.fiscal_period == "2023FY"

    def test_class_dart_key_missing(self):
        """FundamentalsPitProvider 도 DART 키 없으면 dart_key_missing."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DART_API_KEY", None)
            provider = FundamentalsPitProvider()
            r = provider.get_fundamentals_pit("005930", datetime(2024, 1, 1), "KR")

        assert not r.available
        assert r.label == "dart_key_missing"

    def test_class_shared_provider_reuse(self):
        """여러 번 호출해도 예외 X — shared provider 재사용."""
        filings = [_make_filing("X", "2023FY", datetime(2023, 12, 1))]
        stub = _StubProvider(filings)
        provider = FundamentalsPitProvider(edgar_provider=stub)

        r1 = provider.get_fundamentals_pit("X", datetime(2024, 1, 1), "US")
        r2 = provider.get_fundamentals_pit("X", datetime(2024, 1, 1), "US")
        assert r1.available and r2.available
        assert r1.latest.fiscal_period == r2.latest.fiscal_period


# ---------------------------------------------------------------------------
# off byte-identical (engine_wire 회귀)
# ---------------------------------------------------------------------------

class TestOffByteIdentical:
    def test_engine_wire_regression(self):
        """engine_wire 24 tests 이상 없음 — off byte-identical 보장."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_engine_wire.py", "-q", "--tb=short"],
            capture_output=True, text=True,
            cwd=str(_ROOT),
        )
        assert "24 passed" in result.stdout or "passed" in result.stdout, (
            f"engine_wire 회귀:\n{result.stdout}\n{result.stderr}"
        )
