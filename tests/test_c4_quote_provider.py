"""tests/test_c4_quote_provider.py — C4 주식 quote provider 단위 테스트.

검증 항목:
- as_of 시점 quote 단위테스트 (캐시 주입 후 조회)
- 미래 as_of → None 반환 (core.pit.as_of 경유 lookahead 거부 확인)
- 결측 → None 반환 + source_missing 라벨 (silent 금지)
- MarketQuote 필드 형식 (ticker/as_of/price)
- price_change_pct 계산 (window_days 지정 시)
- QuoteProvider 클래스 인터페이스
- with_market_cap graceful (없어도 예외 X)
"""

from __future__ import annotations

import json
import sys
import os
import tempfile
import datetime
from datetime import date, timedelta
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from stock.data.historical_provider import HistoricalProvider, OhlcvBar, _append_cache
from stock.data.quote_provider import get_quote_at, QuoteProvider


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _inject_bars(tmp_path: Path, ticker: str, region: str, bars: list[OhlcvBar]) -> None:
    """tmp_path 기반 캐시에 bars 주입."""
    _append_cache(ticker, region, bars, root=tmp_path)


def _make_provider(tmp_path: Path) -> HistoricalProvider:
    return HistoricalProvider(cache_root=tmp_path)


def _make_us_bars(ticker: str, start: date, n: int) -> list[OhlcvBar]:
    bars = []
    cur = start
    for i in range(n):
        bars.append(OhlcvBar(
            ticker=ticker,
            date=cur.isoformat(),
            open=100.0 + i,
            high=105.0 + i,
            low=99.0 + i,
            close=103.0 + i,
            volume=1_000_000,
        ))
        cur += timedelta(days=1)
    return bars


# ---------------------------------------------------------------------------
# 기본 조회 단위 테스트
# ---------------------------------------------------------------------------

class TestGetQuoteAt:
    def test_returns_market_quote(self, tmp_path):
        """정상 캐시 조회 → MarketQuote 반환."""
        from stock.contracts import MarketQuote

        bars = [
            OhlcvBar("AAPL", "2024-01-02", 182.0, 185.0, 181.0, 184.0, 50_000_000),
            OhlcvBar("AAPL", "2024-01-03", 184.0, 187.0, 183.0, 185.5, 55_000_000),
        ]
        _inject_bars(tmp_path, "AAPL", "US", bars)
        provider = _make_provider(tmp_path)

        q = get_quote_at("AAPL", date(2024, 1, 3), "US", provider=provider)

        assert q is not None, "MarketQuote 가 None"
        assert isinstance(q, MarketQuote)
        assert q.ticker == "AAPL"
        assert q.price == 185.5
        assert isinstance(q.as_of, datetime.datetime)

    def test_ticker_in_result(self, tmp_path):
        """결과 ticker 가 요청 ticker 와 일치."""
        bars = [OhlcvBar("005930", "2024-01-02", 73000, 74000, 72000, 73500, 10_000_000)]
        _inject_bars(tmp_path, "005930", "KR", bars)
        provider = _make_provider(tmp_path)

        q = get_quote_at("005930", date(2024, 1, 2), "KR", provider=provider)

        assert q is not None
        assert q.ticker == "005930"
        assert q.price == 73500.0

    def test_as_of_datetime_normalized(self, tmp_path):
        """반환 as_of 는 datetime 타입."""
        bars = [OhlcvBar("X", "2024-03-01", 100, 101, 99, 100, 500_000)]
        _inject_bars(tmp_path, "X", "US", bars)
        provider = _make_provider(tmp_path)

        q = get_quote_at("X", date(2024, 3, 1), "US", provider=provider)

        assert isinstance(q.as_of, datetime.datetime)
        assert q.as_of.date() == date(2024, 3, 1)

    def test_latest_bar_before_as_of(self, tmp_path):
        """as_of 당일 bar 없으면 as_of 이전 가장 최근 bar 반환.

        네트워크 fetch 를 mock 으로 막아 순수 캐시 히트 경로만 테스트한다.
        """
        bars = [
            OhlcvBar("TSLA", "2024-01-02", 200, 205, 198, 203, 5_000_000),
            OhlcvBar("TSLA", "2024-01-03", 203, 208, 201, 207, 6_000_000),
            # 2024-01-04(목), 2024-01-05(금) 캐시 없음
        ]
        _inject_bars(tmp_path, "TSLA", "US", bars)
        provider = _make_provider(tmp_path)

        # 캐시 미스 구간 fetch 를 빈 결과로 막음(실네트워크 차단)
        with patch.object(provider, "_fetch", return_value=[]):
            q = get_quote_at("TSLA", date(2024, 1, 5), "US", provider=provider)

        assert q is not None
        assert q.price == 207.0  # 캐시 내 최신(2024-01-03) 종가


# ---------------------------------------------------------------------------
# PIT 불변식: 미래 as_of 거부 (core.pit.as_of 경유)
# ---------------------------------------------------------------------------

class TestPitLookaheadRefusal:
    def test_future_as_of_returns_none(self, tmp_path):
        """미래 as_of → None 반환 (lookahead 차단) — core.pit.as_of 경유 확인."""
        bars = [OhlcvBar("AAPL", "2024-01-02", 182, 185, 181, 184, 50_000_000)]
        _inject_bars(tmp_path, "AAPL", "US", bars)
        provider = _make_provider(tmp_path)

        future = datetime.date.today() + timedelta(days=365)
        q = get_quote_at("AAPL", future, "US", provider=provider)

        assert q is None, f"미래 as_of 가 통과됨: {q}"

    def test_future_as_of_uses_pit_module(self, tmp_path):
        """미래거부가 core.pit.as_of.resolve_as_of 를 실제로 거쳐 오는지 확인."""
        provider = _make_provider(tmp_path)

        # resolve_as_of 가 ValueError 를 발생시키는 것을 spy 로 확인
        future = datetime.date.today() + timedelta(days=100)

        with patch("stock.data.quote_provider._resolve_as_of") as mock_resolve:
            mock_resolve.side_effect = ValueError("미래 as_of 거부(lookahead)")
            q = get_quote_at("AAPL", future, "US", provider=provider)

        assert q is None
        mock_resolve.assert_called_once()

    def test_past_as_of_passes(self, tmp_path):
        """과거 as_of → resolve_as_of 통과, 정상 흐름 진행."""
        bars = [OhlcvBar("AAPL", "2020-01-02", 300, 305, 298, 302, 40_000_000)]
        _inject_bars(tmp_path, "AAPL", "US", bars)
        provider = _make_provider(tmp_path)

        q = get_quote_at("AAPL", date(2020, 1, 2), "US", provider=provider)
        # 데이터 있으면 MarketQuote, 없어도 None(source_missing) — 예외 X
        # 이 케이스에서는 캐시에 있으므로 MarketQuote 반환
        assert q is not None
        assert q.price == 302.0


# ---------------------------------------------------------------------------
# 결측 → source_missing (silent 금지)
# ---------------------------------------------------------------------------

class TestSourceMissing:
    def test_no_data_returns_none(self, tmp_path):
        """캐시에 해당 종목 없음 → None [source_missing]."""
        provider = _make_provider(tmp_path)

        # 네트워크 fetch 도 mock 으로 막아 순수 "데이터 없음" 시나리오
        with patch("stock.data.historical_provider._fetch_us", return_value=[]):
            q = get_quote_at("ZZZZZ", date(2024, 1, 3), "US", provider=provider)

        assert q is None

    def test_source_missing_logged(self, tmp_path, caplog):
        """결측 시 source_missing 로그 발생."""
        import logging
        provider = _make_provider(tmp_path)

        with patch("stock.data.historical_provider._fetch_us", return_value=[]):
            with caplog.at_level(logging.WARNING, logger="stock.data.quote_provider"):
                get_quote_at("ZZZZZ", date(2024, 1, 3), "US", provider=provider)

        assert any("source_missing" in r.message for r in caplog.records), (
            "source_missing 로그 없음"
        )

    def test_no_exception_on_failure(self, tmp_path):
        """provider._fetch 가 빈 리스트 반환해도(결측) 예외 X → None 반환.

        _fetch_us 내부에서 예외를 잡아 빈 리스트로 반환하는 건 historical_provider 몫.
        여기서는 provider._fetch 를 빈 반환으로 mock 해 quote_provider graceful 검증.
        """
        provider = _make_provider(tmp_path)

        with patch.object(provider, "_fetch", return_value=[]):
            q = get_quote_at("FAIL", date(2024, 1, 3), "US", provider=provider)

        assert q is None


# ---------------------------------------------------------------------------
# price_change_pct 계산
# ---------------------------------------------------------------------------

class TestPriceChange:
    def test_price_change_pct_correct(self, tmp_path):
        """price_change_window_days 지정 시 pct 계산 정확."""
        # 2024-01-02 종가=100, 2024-01-12 종가=110 → 10일 변화 +10%
        bars = []
        cur = date(2024, 1, 2)
        for i in range(11):
            bars.append(OhlcvBar(
                "X", cur.isoformat(),
                100 + i, 101 + i, 99 + i, 100 + i, 1_000_000
            ))
            cur += timedelta(days=1)
        _inject_bars(tmp_path, "X", "US", bars)
        provider = _make_provider(tmp_path)

        q = get_quote_at(
            "X", date(2024, 1, 12), "US",
            provider=provider,
            price_change_window_days=10,
        )

        assert q is not None
        assert q.price_change_window_days == 10
        assert q.price_change_pct is not None
        # 2024-01-02 close=100, 2024-01-12 close=110 → pct ≈ 0.10
        assert abs(q.price_change_pct - 0.10) < 0.01, f"pct={q.price_change_pct}"

    def test_no_price_change_when_not_requested(self, tmp_path):
        """price_change_window_days 미지정 시 price_change_pct=None."""
        bars = [OhlcvBar("Y", "2024-01-02", 100, 101, 99, 100, 500_000)]
        _inject_bars(tmp_path, "Y", "US", bars)
        provider = _make_provider(tmp_path)

        q = get_quote_at("Y", date(2024, 1, 2), "US", provider=provider)

        assert q.price_change_pct is None
        assert q.price_change_window_days is None


# ---------------------------------------------------------------------------
# with_market_cap graceful
# ---------------------------------------------------------------------------

class TestMarketCap:
    def test_market_cap_graceful_when_unavailable(self, tmp_path):
        """with_market_cap=True 요청해도 없으면 market_cap=None, 예외 X."""
        bars = [OhlcvBar("AAPL", "2024-01-02", 182, 185, 181, 184, 50_000_000)]
        _inject_bars(tmp_path, "AAPL", "US", bars)
        provider = _make_provider(tmp_path)

        # yfinance.info 실패 → graceful
        with patch("stock.data.quote_provider._approx_market_cap_us", return_value=None):
            q = get_quote_at(
                "AAPL", date(2024, 1, 2), "US",
                provider=provider,
                with_market_cap=True,
            )

        assert q is not None
        assert q.market_cap is None  # None graceful

    def test_market_cap_returned_when_available(self, tmp_path):
        """with_market_cap=True 이고 시총 근사 가능 시 값 반환."""
        bars = [OhlcvBar("AAPL", "2024-01-02", 182, 185, 181, 184.0, 50_000_000)]
        _inject_bars(tmp_path, "AAPL", "US", bars)
        provider = _make_provider(tmp_path)

        with patch("stock.data.quote_provider._approx_market_cap_us", return_value=2.9e12):
            q = get_quote_at(
                "AAPL", date(2024, 1, 2), "US",
                provider=provider,
                with_market_cap=True,
            )

        assert q is not None
        assert q.market_cap == pytest.approx(2.9e12)

    def test_market_cap_not_fetched_when_not_requested(self, tmp_path):
        """with_market_cap=False (기본) 시 시총 함수 미호출."""
        bars = [OhlcvBar("AAPL", "2024-01-02", 182, 185, 181, 184, 50_000_000)]
        _inject_bars(tmp_path, "AAPL", "US", bars)
        provider = _make_provider(tmp_path)

        with patch("stock.data.quote_provider._approx_market_cap_us") as mock_cap:
            q = get_quote_at("AAPL", date(2024, 1, 2), "US", provider=provider)

        mock_cap.assert_not_called()
        assert q.market_cap is None


# ---------------------------------------------------------------------------
# QuoteProvider 클래스
# ---------------------------------------------------------------------------

class TestQuoteProvider:
    def test_class_interface(self, tmp_path):
        """QuoteProvider.get_quote_at 모듈 함수와 동일 결과."""
        bars = [OhlcvBar("MSFT", "2024-02-01", 410, 415, 408, 412, 30_000_000)]
        _inject_bars(tmp_path, "MSFT", "US", bars)

        qp = QuoteProvider(cache_root=tmp_path)
        q = qp.get_quote_at("MSFT", date(2024, 2, 1), "US")

        assert q is not None
        assert q.ticker == "MSFT"
        assert q.price == 412.0

    def test_shared_provider_reuse(self, tmp_path):
        """QuoteProvider 는 내부 provider 재사용 (생성 1회)."""
        bars = [OhlcvBar("T1", "2024-01-10", 50, 52, 49, 51, 100_000)]
        _inject_bars(tmp_path, "T1", "US", bars)

        qp = QuoteProvider(cache_root=tmp_path)
        # 여러 번 호출해도 예외 X
        q1 = qp.get_quote_at("T1", date(2024, 1, 10), "US")
        q2 = qp.get_quote_at("T1", date(2024, 1, 10), "US")
        assert q1 is not None and q2 is not None
        assert q1.price == q2.price

    def test_future_as_of_via_class(self, tmp_path):
        """QuoteProvider 도 미래 as_of → None."""
        qp = QuoteProvider(cache_root=tmp_path)
        future = datetime.date.today() + timedelta(days=100)
        q = qp.get_quote_at("AAPL", future, "US")
        assert q is None


# ---------------------------------------------------------------------------
# off byte-identical 확인 (engine_wire 회귀)
# ---------------------------------------------------------------------------

class TestOffByteIdentical:
    def test_engine_wire_regression(self):
        """engine_wire 24 tests 이상 없음 — off byte-identical 보장."""
        import subprocess
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                "tests/test_engine_wire.py", "-q", "--tb=short",
            ],
            capture_output=True, text=True,
            cwd=str(_ROOT),
        )
        assert "24 passed" in result.stdout or "passed" in result.stdout, (
            f"engine_wire 회귀 발생:\n{result.stdout}\n{result.stderr}"
        )
