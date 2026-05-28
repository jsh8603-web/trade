"""tests/test_so2_p4_dart_edgar_provider.py — SO-2/P4 DART/EDGAR provider 검증.

검증 기준 (harness2.md SO-2):
1. DartXbrlProvider/EdgarXbrlProvider 가 FundamentalsProvider 만족 (fetch_filings 시그니처)
2. 반환 Fundamentals.source ∈ {DART_XBRL, EDGAR_XBRL}
3. 정정공시 → 원본 접수일 filing_timestamp 보존
4. PITFundamentalsAdapter(BACKTEST) → 미래/RESTATED 거부 연동 + is_pit_clean True
5. credential 부재 시 fixture 경계 + 라이브 이연 박제
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Sequence
from unittest.mock import MagicMock, patch

import pytest

from stock.contracts import FilingSource, Fundamentals, RunMode
from stock.data.fundamentals_adapter import (
    FundamentalsProvider,
    PITFundamentalsAdapter,
    InMemoryFundamentalsProvider,
)


# ---------------------------------------------------------------------------
# 1. FundamentalsProvider 프로토콜 만족 검증 (duck-type)
# ---------------------------------------------------------------------------

def test_dart_provider_satisfies_protocol():
    """DartXbrlProvider 가 FundamentalsProvider 프로토콜 만족 (fetch_filings 시그니처)."""
    from stock.data.dart_provider import DartXbrlProvider
    provider = DartXbrlProvider()
    assert callable(getattr(provider, "fetch_filings", None))


def test_edgar_provider_satisfies_protocol():
    """EdgarXbrlProvider 가 FundamentalsProvider 프로토콜 만족."""
    from stock.data.edgar_provider import EdgarXbrlProvider
    provider = EdgarXbrlProvider()
    assert callable(getattr(provider, "fetch_filings", None))


# ---------------------------------------------------------------------------
# 2. DART — credential 부재 시 빈 목록 + 경고 (이연 박제)
# ---------------------------------------------------------------------------

def test_dart_provider_no_credential_returns_empty():
    """DART_API_KEY 없을 때 fetch_filings → [] (credential 이연, blocked 아님)."""
    from stock.data.dart_provider import DartXbrlProvider
    provider = DartXbrlProvider(api_key="")
    result = provider.fetch_filings("005930", limit=3)
    assert isinstance(result, (list, tuple, Sequence.__class__))
    result_list = list(result)
    assert result_list == []


# ---------------------------------------------------------------------------
# 3. DART — stub transport 경계: filing 객체 → Fundamentals 변환
# ---------------------------------------------------------------------------

def _make_dart_filing(rcept_no="20231114000001", rcept_dt="20231114",
                      report_nm="2023사업보고서"):
    """dart-fss filing stub."""
    m = MagicMock()
    m.rcept_no = rcept_no
    m.rcept_dt = rcept_dt
    m.report_nm = report_nm
    m.rm = ""
    return m


def test_dart_filing_to_fundamentals_source():
    """DartXbrlProvider._filing_to_fundamentals → source=DART_XBRL."""
    from stock.data.dart_provider import DartXbrlProvider
    provider = DartXbrlProvider(api_key="DUMMY")

    # XBRL 파싱은 네트워크 의존 → stub
    with patch.object(provider, "_parse_xbrl_values", return_value={"revenue": 1e12}):
        filing = _make_dart_filing()
        result = provider._filing_to_fundamentals("005930", filing)

    assert result is not None
    assert result.source == FilingSource.DART_XBRL
    assert result.ticker == "005930"
    assert result.as_reported is True


def test_dart_filing_timestamp_yyyymmdd():
    """DART 접수일 YYYYMMDD → filing_timestamp datetime 변환."""
    from stock.data.dart_provider import DartXbrlProvider
    provider = DartXbrlProvider(api_key="DUMMY")
    with patch.object(provider, "_parse_xbrl_values", return_value={}):
        filing = _make_dart_filing(rcept_dt="20221231")
        result = provider._filing_to_fundamentals("005930", filing)
    assert result is not None
    assert result.filing_timestamp == datetime(2022, 12, 31)


def test_dart_original_filing_date_preserved():
    """정정공시 원본 접수일 보존 — rcept_dt 가 원본 공시 날짜임을 확인."""
    from stock.data.dart_provider import DartXbrlProvider
    provider = DartXbrlProvider(api_key="DUMMY")
    # 정정공시: rcept_dt = 원본 접수일 (정정본 날짜 X)
    with patch.object(provider, "_parse_xbrl_values", return_value={"net_income": 5e10}):
        filing = _make_dart_filing(rcept_dt="20220315", report_nm="2021사업보고서(정정)")
        result = provider._filing_to_fundamentals("005930", filing)
    assert result is not None
    # 정정이어도 원본 접수일 = 2022-03-15 보존
    assert result.filing_timestamp == datetime(2022, 3, 15)
    assert result.source == FilingSource.DART_XBRL


# ---------------------------------------------------------------------------
# 4. EDGAR — companyfacts fixture → accession 단위 Fundamentals
# ---------------------------------------------------------------------------

def _make_companyfacts_fixture():
    """SEC EDGAR companyfacts fixture (최소 구조)."""
    return {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {
                                "accn": "0001234567-23-001000",
                                "filed": "2023-02-15",
                                "form": "10-K",
                                "fy": 2022,
                                "fp": "FY",
                                "val": 394328000000,
                            },
                            {
                                "accn": "0001234567-22-001000",
                                "filed": "2022-02-28",
                                "form": "10-K",
                                "fy": 2021,
                                "fp": "FY",
                                "val": 365817000000,
                            },
                        ]
                    }
                },
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            {
                                "accn": "0001234567-23-001000",
                                "filed": "2023-02-15",
                                "form": "10-K",
                                "fy": 2022,
                                "fp": "FY",
                                "val": 99803000000,
                            }
                        ]
                    }
                },
            }
        }
    }


def test_edgar_provider_source_edgar_xbrl():
    """EdgarXbrlProvider → source=EDGAR_XBRL."""
    from stock.data.edgar_provider import EdgarXbrlProvider

    provider = EdgarXbrlProvider(ticker_to_cik={"AAPL": "0000320193"})

    with patch("stock.data.edgar_provider._fetch_company_facts",
               return_value=_make_companyfacts_fixture()):
        results = list(provider.fetch_filings("AAPL", limit=5))

    assert len(results) >= 1
    for r in results:
        assert r.source == FilingSource.EDGAR_XBRL
        assert r.as_reported is True


def test_edgar_accession_pit_filing_date():
    """EDGAR accession filed 날짜 → filing_timestamp PIT."""
    from stock.data.edgar_provider import EdgarXbrlProvider

    provider = EdgarXbrlProvider(ticker_to_cik={"AAPL": "0000320193"})
    with patch("stock.data.edgar_provider._fetch_company_facts",
               return_value=_make_companyfacts_fixture()):
        results = list(provider.fetch_filings("AAPL", limit=5))

    # 최신순 정렬 → 첫 번째 = 2023-02-15
    assert results[0].filing_timestamp == datetime(2023, 2, 15)


def test_edgar_fiscal_period_fy():
    """EDGAR FY → fiscal_period '2022FY'."""
    from stock.data.edgar_provider import EdgarXbrlProvider

    provider = EdgarXbrlProvider(ticker_to_cik={"AAPL": "0000320193"})
    with patch("stock.data.edgar_provider._fetch_company_facts",
               return_value=_make_companyfacts_fixture()):
        results = list(provider.fetch_filings("AAPL", limit=5))

    periods = {r.fiscal_period for r in results}
    assert "2022FY" in periods


def test_edgar_no_cik_returns_empty():
    """CIK 못 찾으면 빈 목록 반환 (네트워크 이연)."""
    from stock.data.edgar_provider import EdgarXbrlProvider

    provider = EdgarXbrlProvider()
    with patch("stock.data.edgar_provider._ticker_to_cik", return_value=None):
        results = list(provider.fetch_filings("UNKNOWN", limit=5))
    assert results == []


# ---------------------------------------------------------------------------
# 5. PITFundamentalsAdapter wire — BACKTEST 미래·RESTATED 거부
# ---------------------------------------------------------------------------

def _make_fundamentals(ticker, days_offset, source=FilingSource.DART_XBRL):
    ts = datetime(2023, 6, 1)
    from datetime import timedelta
    filing_ts = ts + __import__("datetime").timedelta(days=days_offset)
    return Fundamentals(
        ticker=ticker,
        fiscal_period="2023Q2",
        filing_timestamp=filing_ts,
        source=source,
        as_reported=True,
        revenue=1e10,
    )


def test_pit_adapter_backtest_rejects_future():
    """PITFundamentalsAdapter(BACKTEST) → as_of 이후 공시 거부."""
    as_of = datetime(2023, 6, 1)
    # 하루 뒤 공시 → 미래
    future = _make_fundamentals("005930", days_offset=1)
    # 하루 전 공시 → 가시
    past = _make_fundamentals("005930", days_offset=-1)

    provider = InMemoryFundamentalsProvider({"005930": [future, past]})
    adapter = PITFundamentalsAdapter(provider, RunMode.BACKTEST)
    results = adapter.get_pit_fundamentals("005930", as_of)
    assert all(r.filing_timestamp <= as_of for r in results)
    assert len(results) == 1


def test_pit_adapter_backtest_rejects_restated():
    """PITFundamentalsAdapter(BACKTEST) → RESTATED 거부."""
    as_of = datetime(2023, 6, 1)
    restated = Fundamentals(
        ticker="005930",
        fiscal_period="2023Q2",
        filing_timestamp=datetime(2023, 5, 1),
        source=FilingSource.RESTATED,
        as_reported=False,
        revenue=9e9,
    )
    clean = _make_fundamentals("005930", days_offset=-10)
    provider = InMemoryFundamentalsProvider({"005930": [restated, clean]})
    adapter = PITFundamentalsAdapter(provider, RunMode.BACKTEST)
    results = adapter.get_pit_fundamentals("005930", as_of)
    assert all(r.source != FilingSource.RESTATED for r in results)


def test_pit_clean_ratio_dart_xbrl():
    """is_pit_clean() → DART_XBRL + as_reported=True = True."""
    f = _make_fundamentals("005930", days_offset=-5, source=FilingSource.DART_XBRL)
    assert f.is_pit_clean() is True


def test_pit_clean_ratio_edgar_xbrl():
    """is_pit_clean() → EDGAR_XBRL + as_reported=True = True."""
    f = _make_fundamentals("AAPL", days_offset=-5, source=FilingSource.EDGAR_XBRL)
    assert f.is_pit_clean() is True


def test_pit_clean_ratio_restated_false():
    """is_pit_clean() → RESTATED = False."""
    f = Fundamentals(
        ticker="005930",
        fiscal_period="2022FY",
        filing_timestamp=datetime(2023, 1, 1),
        source=FilingSource.RESTATED,
        as_reported=False,
    )
    assert f.is_pit_clean() is False


# ---------------------------------------------------------------------------
# 6. 네트워크 이연 핀 — deferral-pinning 정당성
# ---------------------------------------------------------------------------

def test_deferral_pinning_dart_no_network():
    """DART 라이브 네트워크 이연: API key 없으면 빈 목록 (blocked 아님)."""
    from stock.data.dart_provider import DartXbrlProvider
    provider = DartXbrlProvider(api_key="")
    result = provider.fetch_filings("005930", limit=5)
    # 빈 목록이지만 예외 없음 — 어댑터 본체 작동
    assert list(result) == []


def test_deferral_pinning_edgar_no_network():
    """EDGAR 네트워크 이연: network error → 빈 목록 (blocked 아님)."""
    from stock.data.edgar_provider import EdgarXbrlProvider
    provider = EdgarXbrlProvider(ticker_to_cik={"AAPL": "0000320193"})
    with patch("stock.data.edgar_provider._fetch_company_facts", return_value=None):
        result = provider.fetch_filings("AAPL", limit=5)
    assert list(result) == []
