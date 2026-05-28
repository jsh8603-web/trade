"""SO-3 테스트: valuation wire + PIT 펀더멘털 검증.

검증기준:
- value_stock → ValuationResult(intrinsic·gap·bear/base/bull) PASS
- RESTATED source 백테스트 거부 PASS
- filing_timestamp > as_of 데이터 마스킹(visible_at=False) PASS
- PIT-clean 판별 PASS
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stock.contracts import (
    FilingSource,
    Fundamentals,
    MarketQuote,
    RunMode,
    ValuationResult,
)
from stock.valuation import value_stock
from stock.data.fundamentals_adapter import (
    InMemoryFundamentalsProvider,
    PITFundamentalsAdapter,
)

KST = timezone(timedelta(hours=9))


def _make_fundamentals(
    ticker="005930",
    filing_dt: datetime | None = None,
    source: FilingSource = FilingSource.DART_XBRL,
    fcf: float = 30_000_000_000,
) -> Fundamentals:
    filing_dt = filing_dt or datetime(2024, 3, 15, tzinfo=KST)
    return Fundamentals(
        ticker=ticker,
        fiscal_period="2024FY",
        filing_timestamp=filing_dt,
        source=source,
        currency="KRW",
        revenue=300_000_000_000,
        operating_income=50_000_000_000,
        free_cash_flow=fcf,
        ebitda=60_000_000_000,
        ebit=50_000_000_000,
        interest_expense=5_000_000_000,
        total_debt=100_000_000_000,
        cash_and_equivalents=50_000_000_000,
        beta=0.9,
        revenue_growth=0.05,
        outstanding_shares=5_000_000_000,
    )


def _make_quote(price=71_000, market_cap=400_000_000_000_000) -> MarketQuote:
    return MarketQuote(
        ticker="005930",
        as_of=datetime(2024, 4, 1, tzinfo=KST),
        price=price,
        market_cap=market_cap,
        price_change_pct=-0.12,
        price_change_window_days=30,
    )


# ── value_stock → ValuationResult ────────────────────────────────────

def test_value_stock_returns_valuation_result():
    f = _make_fundamentals()
    q = _make_quote()
    result = value_stock([f], q)
    assert result is not None
    assert isinstance(result, ValuationResult)


def test_value_stock_required_fields():
    """bear/base/bull 밴드 + intrinsic_value + valuation_gap."""
    f = _make_fundamentals()
    q = _make_quote()
    result = value_stock([f], q)
    assert result is not None
    assert isinstance(result.intrinsic_value, float)
    assert isinstance(result.valuation_gap, float)
    assert isinstance(result.bear_value, float)
    assert isinstance(result.base_value, float)
    assert isinstance(result.bull_value, float)
    assert isinstance(result.wacc, float)


def test_value_stock_gap_formula():
    """valuation_gap = (intrinsic - market_cap) / market_cap."""
    f = _make_fundamentals()
    q = _make_quote()
    result = value_stock([f], q)
    assert result is not None
    expected_gap = (result.intrinsic_value - result.market_cap) / result.market_cap
    assert abs(result.valuation_gap - expected_gap) < 1e-6


def test_value_stock_positive_intrinsic():
    """FCF 양수 → intrinsic_value > 0."""
    f = _make_fundamentals(fcf=30_000_000_000)
    q = _make_quote()
    result = value_stock([f], q)
    assert result is not None
    assert result.intrinsic_value > 0


def test_value_stock_no_fundamentals_returns_none():
    """펀더멘털 없으면 None."""
    q = _make_quote()
    result = value_stock([], q)
    assert result is None


def test_value_stock_pit_clean_flag():
    """DART XBRL → pit_clean=True."""
    f = _make_fundamentals(source=FilingSource.DART_XBRL)
    q = _make_quote()
    result = value_stock([f], q)
    assert result is not None
    assert result.pit_clean is True


def test_value_stock_restated_not_pit_clean():
    """RESTATED → pit_clean=False."""
    f = _make_fundamentals(source=FilingSource.RESTATED)
    q = _make_quote()
    result = value_stock([f], q)
    assert result is not None
    assert result.pit_clean is False


# ── Fundamentals.is_pit_clean() ──────────────────────────────────────

def test_dart_xbrl_is_pit_clean():
    f = _make_fundamentals(source=FilingSource.DART_XBRL)
    assert f.is_pit_clean() is True


def test_edgar_xbrl_is_pit_clean():
    f = _make_fundamentals(source=FilingSource.EDGAR_XBRL)
    assert f.is_pit_clean() is True


def test_restated_not_pit_clean():
    f = _make_fundamentals(source=FilingSource.RESTATED)
    assert f.is_pit_clean() is False


def test_estimate_not_pit_clean():
    f = _make_fundamentals(source=FilingSource.ESTIMATE)
    assert f.is_pit_clean() is False


# ── Fundamentals.visible_at() ────────────────────────────────────────

def test_visible_at_past_filing():
    """filing_timestamp < as_of → visible_at=True."""
    filing_dt = datetime(2024, 3, 15, tzinfo=KST)
    as_of = datetime(2024, 4, 1, tzinfo=KST)
    f = _make_fundamentals(filing_dt=filing_dt)
    assert f.visible_at(as_of) is True


def test_visible_at_same_moment():
    """filing_timestamp == as_of → visible_at=True (<=)."""
    dt = datetime(2024, 4, 1, tzinfo=KST)
    f = _make_fundamentals(filing_dt=dt)
    assert f.visible_at(dt) is True


def test_visible_at_future_filing():
    """filing_timestamp > as_of → visible_at=False (마스킹)."""
    filing_dt = datetime(2024, 5, 1, tzinfo=KST)
    as_of = datetime(2024, 4, 1, tzinfo=KST)
    f = _make_fundamentals(filing_dt=filing_dt)
    assert f.visible_at(as_of) is False


# ── PITFundamentalsAdapter — RESTATED 백테스트 거부 ─────────────────

def test_pit_adapter_backtest_rejects_restated():
    """백테스트: RESTATED 소스 완전 거부."""
    f_restated = _make_fundamentals(
        filing_dt=datetime(2024, 1, 1, tzinfo=KST),
        source=FilingSource.RESTATED,
    )
    f_dart = _make_fundamentals(
        filing_dt=datetime(2024, 1, 1, tzinfo=KST),
        source=FilingSource.DART_XBRL,
    )
    provider = InMemoryFundamentalsProvider({"005930": [f_restated, f_dart]})
    adapter = PITFundamentalsAdapter(provider, mode=RunMode.BACKTEST)

    as_of = datetime(2024, 4, 1, tzinfo=KST)
    result = adapter.get_pit_fundamentals("005930", as_of)
    assert all(f.source != FilingSource.RESTATED for f in result), "RESTATED 누수 발생"
    assert any(f.source == FilingSource.DART_XBRL for f in result)


def test_pit_adapter_backtest_masks_future_filings():
    """백테스트: filing_timestamp > as_of 마스킹."""
    f_past = _make_fundamentals(
        filing_dt=datetime(2024, 1, 1, tzinfo=KST),
        source=FilingSource.DART_XBRL,
    )
    f_future = _make_fundamentals(
        filing_dt=datetime(2024, 5, 1, tzinfo=KST),  # 미래
        source=FilingSource.DART_XBRL,
    )
    provider = InMemoryFundamentalsProvider({"005930": [f_past, f_future]})
    adapter = PITFundamentalsAdapter(provider, mode=RunMode.BACKTEST)

    as_of = datetime(2024, 4, 1, tzinfo=KST)
    result = adapter.get_pit_fundamentals("005930", as_of)
    assert all(f.filing_timestamp <= as_of for f in result), "미래 데이터 누수 발생"
    assert len(result) == 1


def test_pit_adapter_forward_allows_restated_warning():
    """forward 모드: RESTATED 허용(경고만)."""
    f_restated = _make_fundamentals(
        filing_dt=datetime(2024, 1, 1, tzinfo=KST),
        source=FilingSource.RESTATED,
    )
    provider = InMemoryFundamentalsProvider({"005930": [f_restated]})
    adapter = PITFundamentalsAdapter(provider, mode=RunMode.FORWARD)

    as_of = datetime(2024, 4, 1, tzinfo=KST)
    result = adapter.get_pit_fundamentals("005930", as_of)
    assert len(result) == 1  # forward에서는 통과


def test_pit_clean_ratio():
    """PIT-clean 비율 계산."""
    f1 = _make_fundamentals(source=FilingSource.DART_XBRL)
    f2 = _make_fundamentals(source=FilingSource.EDGAR_XBRL)
    f3 = _make_fundamentals(source=FilingSource.RESTATED)
    provider = InMemoryFundamentalsProvider({"005930": [f1, f2, f3]})
    adapter = PITFundamentalsAdapter(provider, mode=RunMode.FORWARD)
    ratio = adapter.pit_clean_ratio([f1, f2, f3])
    assert abs(ratio - 2/3) < 1e-6
