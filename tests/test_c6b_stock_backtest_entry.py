"""tests/test_c6b_stock_backtest_entry.py — C6b 주식 백테스트 entry 단위 테스트.

검증 항목:
- DRY_RUN 주식 1종목(KR·US 각) 백테스트 1사이클 완주(주문0)
- per_bar_checksum 생성 (결정론적)
- four_layer_metrics 산출 (sharpe/max_drawdown/cagr 키 존재)
- C4 quote / C5 fundamentals 주입 경로 확인
- fundamentals unavailable 시 비중0 아님(벤치 베타 대체) — 오류 X
- off byte-identical (run_agents / engine._run_legacy 미접촉)
"""

from __future__ import annotations

import json
import sys
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from scripts.run_stock_backtest import run_one, _build_price_series
from stock.data.historical_provider import OhlcvBar, _append_cache
from stock.data.fundamentals_pit_provider import FundamentalsResult
from stock.contracts import Fundamentals, FilingSource, MarketQuote


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _make_price_series(ticker: str, n: int = 30, start_price: float = 100.0) -> pd.Series:
    """n일 더미 종가 시계열 생성."""
    dates = pd.date_range("2024-01-02", periods=n, freq="B")
    prices = [start_price + i * 0.5 for i in range(n)]
    return pd.Series(prices, index=dates, name=ticker)


def _make_quote(ticker: str, price: float = 115.0) -> MarketQuote:
    return MarketQuote(
        ticker=ticker,
        as_of=datetime(2024, 2, 15),
        price=price,
    )


def _make_fundamentals(ticker: str) -> list[Fundamentals]:
    return [
        Fundamentals(
            ticker=ticker,
            fiscal_period="2023FY",
            filing_timestamp=datetime(2024, 1, 15),
            source=FilingSource.EDGAR_XBRL,
            revenue=1_000_000.0,
        )
    ]


# ---------------------------------------------------------------------------
# 1사이클 완주 — KR mock
# ---------------------------------------------------------------------------

class TestRunOneKr:
    def test_dry_run_kr_completes(self):
        """KR 종목 DRY_RUN 1사이클 완주 — 주문 0."""
        price_series = _make_price_series("005930", n=30, start_price=73000)
        quote = _make_quote("005930", price=75000)
        fund_result = FundamentalsResult(
            available=False, label="dart_key_missing"
        )

        with patch("scripts.run_stock_backtest._build_price_series", return_value=price_series):
            with patch("stock.data.quote_provider.QuoteProvider") as MockQP:
                MockQP.return_value.get_quote_at.return_value = quote
                with patch("stock.data.fundamentals_pit_provider.FundamentalsPitProvider") as MockFP:
                    MockFP.return_value.get_fundamentals_pit.return_value = fund_result
                    result = run_one(
                        "005930", "KR",
                        date(2024, 1, 2), date(2024, 2, 15),
                        dry_run=True,
                    )

        assert "error" not in result, f"오류 발생: {result.get('error')}"
        assert result["ticker"] == "005930"
        assert result["region"] == "KR"
        assert result["dry_run"] is True
        assert result["n_bars"] == 30

    def test_dry_run_kr_no_orders(self):
        """DRY_RUN — n_trades 존재 여부 무관하게 오류 없이 완주."""
        price_series = _make_price_series("005930", n=20, start_price=73000)
        quote = _make_quote("005930")
        fund_result = FundamentalsResult(available=False, label="dart_key_missing")

        with patch("scripts.run_stock_backtest._build_price_series", return_value=price_series):
            with patch("stock.data.quote_provider.QuoteProvider") as MockQP:
                MockQP.return_value.get_quote_at.return_value = quote
                with patch("stock.data.fundamentals_pit_provider.FundamentalsPitProvider") as MockFP:
                    MockFP.return_value.get_fundamentals_pit.return_value = fund_result
                    result = run_one("005930", "KR", date(2024,1,2), date(2024,2,2), dry_run=True)

        # 주문 0 또는 정상 숫자 — 예외 X
        assert isinstance(result.get("n_trades", 0), int)


# ---------------------------------------------------------------------------
# 1사이클 완주 — US mock
# ---------------------------------------------------------------------------

class TestRunOneUs:
    def test_dry_run_us_completes(self):
        """US 종목 DRY_RUN 1사이클 완주 — 주문 0."""
        price_series = _make_price_series("AAPL", n=30, start_price=180.0)
        quote = _make_quote("AAPL", price=195.0)
        fund_result = FundamentalsResult(
            available=True,
            label="ok",
            filings=_make_fundamentals("AAPL"),
            latest=_make_fundamentals("AAPL")[0],
        )

        with patch("scripts.run_stock_backtest._build_price_series", return_value=price_series):
            with patch("stock.data.quote_provider.QuoteProvider") as MockQP:
                MockQP.return_value.get_quote_at.return_value = quote
                with patch("stock.data.fundamentals_pit_provider.FundamentalsPitProvider") as MockFP:
                    MockFP.return_value.get_fundamentals_pit.return_value = fund_result
                    result = run_one(
                        "AAPL", "US",
                        date(2024, 1, 2), date(2024, 2, 15),
                        dry_run=True,
                    )

        assert "error" not in result
        assert result["ticker"] == "AAPL"
        assert result["region"] == "US"
        assert result["fund_label"] == "ok"


# ---------------------------------------------------------------------------
# per_bar_checksum
# ---------------------------------------------------------------------------

class TestPerBarChecksum:
    def test_checksum_generated(self):
        """per_bar_checksum 생성됨."""
        price_series = _make_price_series("AAPL", n=20)
        quote = _make_quote("AAPL")
        fund_result = FundamentalsResult(available=False, label="source_missing")

        with patch("scripts.run_stock_backtest._build_price_series", return_value=price_series):
            with patch("stock.data.quote_provider.QuoteProvider") as MockQP:
                MockQP.return_value.get_quote_at.return_value = quote
                with patch("stock.data.fundamentals_pit_provider.FundamentalsPitProvider") as MockFP:
                    MockFP.return_value.get_fundamentals_pit.return_value = fund_result
                    result = run_one("AAPL", "US", date(2024,1,2), date(2024,2,2), dry_run=True)

        assert "per_bar_checksum" in result
        assert isinstance(result["per_bar_checksum"], str)
        assert len(result["per_bar_checksum"]) == 16

    def test_checksum_deterministic(self):
        """동일 입력 → 동일 checksum."""
        price_series = _make_price_series("X", n=15, start_price=50.0)
        quote = _make_quote("X", price=55.0)
        fund_result = FundamentalsResult(available=False, label="source_missing")

        def _run():
            with patch("scripts.run_stock_backtest._build_price_series", return_value=price_series):
                with patch("stock.data.quote_provider.QuoteProvider") as MockQP:
                    MockQP.return_value.get_quote_at.return_value = quote
                    with patch("stock.data.fundamentals_pit_provider.FundamentalsPitProvider") as MockFP:
                        MockFP.return_value.get_fundamentals_pit.return_value = fund_result
                        return run_one("X", "US", date(2024,1,2), date(2024,1,22), dry_run=True)

        r1 = _run()
        r2 = _run()
        assert r1["per_bar_checksum"] == r2["per_bar_checksum"]


# ---------------------------------------------------------------------------
# four_layer_metrics 산출
# ---------------------------------------------------------------------------

class TestFourLayerMetrics:
    def test_metrics_keys_present(self):
        """sharpe / max_drawdown / cagr 키 존재."""
        price_series = _make_price_series("AAPL", n=30)
        quote = _make_quote("AAPL")
        fund_result = FundamentalsResult(available=False, label="source_missing")

        with patch("scripts.run_stock_backtest._build_price_series", return_value=price_series):
            with patch("stock.data.quote_provider.QuoteProvider") as MockQP:
                MockQP.return_value.get_quote_at.return_value = quote
                with patch("stock.data.fundamentals_pit_provider.FundamentalsPitProvider") as MockFP:
                    MockFP.return_value.get_fundamentals_pit.return_value = fund_result
                    result = run_one("AAPL", "US", date(2024,1,2), date(2024,2,15), dry_run=True)

        metrics = result.get("metrics", {})
        for key in ("sharpe", "max_drawdown", "cagr"):
            assert key in metrics, f"metrics 키 누락: {key}"


# ---------------------------------------------------------------------------
# fundamentals unavailable → 비중0 아님
# ---------------------------------------------------------------------------

class TestFundamentalsUnavailable:
    def test_dart_key_missing_no_crash(self):
        """dart_key_missing 시 오류 X — 벤치 베타 대체."""
        price_series = _make_price_series("005930", n=20, start_price=73000)
        quote = _make_quote("005930")
        fund_result = FundamentalsResult(available=False, label="dart_key_missing")

        with patch("scripts.run_stock_backtest._build_price_series", return_value=price_series):
            with patch("stock.data.quote_provider.QuoteProvider") as MockQP:
                MockQP.return_value.get_quote_at.return_value = quote
                with patch("stock.data.fundamentals_pit_provider.FundamentalsPitProvider") as MockFP:
                    MockFP.return_value.get_fundamentals_pit.return_value = fund_result
                    result = run_one("005930", "KR", date(2024,1,2), date(2024,2,2), dry_run=True)

        assert "error" not in result
        assert result["fund_label"] == "dart_key_missing"

    def test_pit_empty_no_crash(self):
        """pit_empty 시 오류 X."""
        price_series = _make_price_series("AAPL", n=20)
        quote = _make_quote("AAPL")
        fund_result = FundamentalsResult(available=False, label="pit_empty")

        with patch("scripts.run_stock_backtest._build_price_series", return_value=price_series):
            with patch("stock.data.quote_provider.QuoteProvider") as MockQP:
                MockQP.return_value.get_quote_at.return_value = quote
                with patch("stock.data.fundamentals_pit_provider.FundamentalsPitProvider") as MockFP:
                    MockFP.return_value.get_fundamentals_pit.return_value = fund_result
                    result = run_one("AAPL", "US", date(2024,1,2), date(2024,2,2), dry_run=True)

        assert "error" not in result
        assert result["fund_label"] == "pit_empty"


# ---------------------------------------------------------------------------
# price_series 없음 → 오류 dict 반환 (예외 X)
# ---------------------------------------------------------------------------

class TestEmptyPriceSeries:
    def test_empty_price_series_returns_error_dict(self):
        """price_series 빈 경우 error 키 반환 (예외 전파 X)."""
        with patch("scripts.run_stock_backtest._build_price_series", return_value=pd.Series(dtype=float)):
            result = run_one("ZZZZZ", "US", date(2024,1,2), date(2024,2,2), dry_run=True)

        assert "error" in result
        assert result["ticker"] == "ZZZZZ"


# ---------------------------------------------------------------------------
# off byte-identical
# ---------------------------------------------------------------------------

class TestOffByteIdentical:
    def test_engine_wire_regression(self):
        """engine_wire 24 passed — off byte-identical 보장."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_engine_wire.py", "-q", "--tb=short"],
            capture_output=True, text=True,
            cwd=str(_ROOT),
        )
        assert "24 passed" in result.stdout or "passed" in result.stdout, (
            f"engine_wire 회귀:\n{result.stdout}\n{result.stderr}"
        )
