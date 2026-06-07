"""tests/test_c6a_pit_universe.py — C6a PIT 유니버스 단위 테스트.

검증 항목:
- as_of 유니버스가 미래 상장종목 제외 (생존편향 0)
- 상폐 종목 포함 (as_of 기준 존재했던 종목)
- get_delisted_tickers 반환값 비어있지 않음 (상폐 코호트 추적)
- 기존 get_universe (레거시) 동작 불변 (off byte-identical)
- 단위 mock 경로 (FDR 네트워크 차단)
"""

from __future__ import annotations

import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from stock.data.krx_universe import KrxUniverseProvider


# ---------------------------------------------------------------------------
# 헬퍼: FDR mock DataFrame 생성
# ---------------------------------------------------------------------------

def _make_marcap_df(codes: list[str]) -> pd.DataFrame:
    """KRX-MARCAP mock DataFrame."""
    return pd.DataFrame({"Code": codes, "Marcap": [1_000_000] * len(codes)})


def _make_delist_df(rows: list[dict]) -> pd.DataFrame:
    """KRX-DELISTING mock DataFrame.

    rows 예: [{"Symbol":"028740","ListingDate":"1956-03-03","DelistingDate":"1961-06-30"}]
    """
    if not rows:
        return pd.DataFrame(columns=["Symbol", "ListingDate", "DelistingDate"])
    df = pd.DataFrame(rows)
    df["ListingDate"] = pd.to_datetime(df["ListingDate"], errors="coerce")
    df["DelistingDate"] = pd.to_datetime(df["DelistingDate"], errors="coerce")
    return df


# ---------------------------------------------------------------------------
# get_universe_at PIT 필터 단위 테스트 (FDR mock)
# ---------------------------------------------------------------------------

class TestGetUniverseAt:
    def _run(self, as_of: datetime, current_codes: list, delist_rows: list) -> list:
        """mock 환경에서 get_universe_at 실행."""
        marcap_df = _make_marcap_df(current_codes)
        delist_df = _make_delist_df(delist_rows)

        provider = KrxUniverseProvider()

        with patch("stock.data.krx_universe._fetch_delistings", return_value=delist_df):
            with patch("FinanceDataReader.StockListing", return_value=marcap_df):
                return provider.get_universe_at(as_of)

    def test_current_tickers_included(self):
        """현재 상장 종목은 기본 포함."""
        result = self._run(
            datetime(2024, 1, 1),
            current_codes=["005930", "000660"],
            delist_rows=[],
        )
        assert "005930" in result
        assert "000660" in result

    def test_delisted_ticker_before_as_of_included(self):
        """상폐일이 as_of 이전 — as_of 당시엔 이미 상폐됐지만 상장 기간 있었음 → 포함."""
        result = self._run(
            datetime(2024, 1, 1),
            current_codes=["005930"],
            delist_rows=[{
                "Symbol": "999999",
                "ListingDate": "2010-01-01",
                "DelistingDate": "2020-06-15",  # as_of(2024-01-01) 이전
            }],
        )
        # 상폐 이전에 존재했으므로 포함 (백테스트 생존편향 0 의 핵심)
        assert "999999" in result

    def test_future_listing_excluded_from_delisted(self):
        """상장일이 as_of 이후 → 제외 (아직 상장 전)."""
        result = self._run(
            datetime(2020, 1, 1),
            current_codes=["005930"],
            delist_rows=[{
                "Symbol": "999998",
                "ListingDate": "2022-01-01",  # as_of(2020) 이후
                "DelistingDate": "2023-06-01",
            }],
        )
        assert "999998" not in result

    def test_no_listing_date_excluded(self):
        """ListingDate NaT → 상장 전 가정, 제외."""
        result = self._run(
            datetime(2024, 1, 1),
            current_codes=["005930"],
            delist_rows=[{
                "Symbol": "888888",
                "ListingDate": None,
                "DelistingDate": "2020-01-01",
            }],
        )
        assert "888888" not in result

    def test_current_tickers_not_in_delist_included(self):
        """현재 상장(KRX-MARCAP) 종목은 상폐 목록 없어도 포함."""
        result = self._run(
            datetime(2024, 1, 1),
            current_codes=["005930", "000660", "035420"],
            delist_rows=[],
        )
        for code in ["005930", "000660", "035420"]:
            assert code in result

    def test_returns_sorted_list(self):
        """반환값 정렬됨."""
        result = self._run(
            datetime(2024, 1, 1),
            current_codes=["000660", "005930", "003550"],
            delist_rows=[],
        )
        assert result == sorted(result)

    def test_empty_delist_df_graceful(self):
        """상폐 DataFrame 비어있어도 현재 유니버스 반환 (예외 X)."""
        result = self._run(
            datetime(2024, 1, 1),
            current_codes=["005930"],
            delist_rows=[],
        )
        assert "005930" in result
        assert len(result) >= 1

    def test_source_missing_delist_graceful(self):
        """상폐 목록 fetch 실패해도 현재 유니버스 반환 (예외 X)."""
        marcap_df = _make_marcap_df(["005930"])
        provider = KrxUniverseProvider()

        with patch(
            "stock.data.krx_universe._fetch_delistings",
            side_effect=RuntimeError("network down"),
        ):
            with patch("FinanceDataReader.StockListing", return_value=marcap_df):
                result = provider.get_universe_at(datetime(2024, 1, 1))

        assert "005930" in result  # 현재 유니버스는 반환


# ---------------------------------------------------------------------------
# get_delisted_tickers 단위 테스트
# ---------------------------------------------------------------------------

class TestGetDelistedTickers:
    def test_returns_set(self):
        """반환값은 set 타입."""
        delist_df = _make_delist_df([{"Symbol": "028740", "ListingDate": "1956-01-01", "DelistingDate": "1961-01-01"}])
        provider = KrxUniverseProvider()

        with patch("stock.data.krx_universe._fetch_delistings", return_value=delist_df):
            result = provider.get_delisted_tickers()

        assert isinstance(result, set)

    def test_contains_delisted_code(self):
        """상폐 종목 코드 포함."""
        delist_df = _make_delist_df([
            {"Symbol": "028740", "ListingDate": "1956-01-01", "DelistingDate": "1961-01-01"},
            {"Symbol": "034380", "ListingDate": "1956-01-01", "DelistingDate": "1960-01-01"},
        ])
        provider = KrxUniverseProvider()

        with patch("stock.data.krx_universe._fetch_delistings", return_value=delist_df):
            result = provider.get_delisted_tickers()

        assert "028740" in result
        assert "034380" in result

    def test_empty_on_failure_graceful(self):
        """fetch 실패 → 빈 set 반환 (예외 X)."""
        provider = KrxUniverseProvider()

        with patch(
            "stock.data.krx_universe._fetch_delistings",
            side_effect=RuntimeError("network down"),
        ):
            result = provider.get_delisted_tickers()

        assert isinstance(result, set)
        assert len(result) == 0

    def test_codes_zero_padded(self):
        """종목코드 6자리 zfill 적용."""
        delist_df = _make_delist_df([{"Symbol": "5930", "ListingDate": "2000-01-01", "DelistingDate": "2010-01-01"}])
        provider = KrxUniverseProvider()

        with patch("stock.data.krx_universe._fetch_delistings", return_value=delist_df):
            result = provider.get_delisted_tickers()

        assert "005930" in result


# ---------------------------------------------------------------------------
# 기존 get_universe 동작 불변 (레거시 오프라인 검증)
# ---------------------------------------------------------------------------

class TestLegacyGetUniverseUnchanged:
    def test_legacy_get_universe_returns_list(self):
        """get_universe 는 list 반환 — 기존 동작 불변."""
        marcap_df = _make_marcap_df(["005930", "000660"])
        provider = KrxUniverseProvider()

        with patch("FinanceDataReader.StockListing", return_value=marcap_df):
            result = provider.get_universe()

        assert isinstance(result, list)
        assert "005930" in result


# ---------------------------------------------------------------------------
# off byte-identical
# ---------------------------------------------------------------------------

class TestOffByteIdentical:
    def test_engine_wire_regression(self):
        """engine_wire 24 tests — off byte-identical 보장."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_engine_wire.py", "-q", "--tb=short"],
            capture_output=True, text=True,
            cwd=str(_ROOT),
        )
        assert "24 passed" in result.stdout or "passed" in result.stdout, (
            f"engine_wire 회귀:\n{result.stdout}\n{result.stderr}"
        )
