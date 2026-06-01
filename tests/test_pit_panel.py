"""tests/test_pit_panel.py — T1 bitemporal PIT 패널 검증 (Phase2 T1 Phase 3 게이트).

검증 4축 (SPEC-T1 충족 + PANEL-SCHEMA §3):
  1. RESTATED 거부 (filing_source=restated row 미적재)
  2. filing-lag PIT (관측일 features = filing<=date 만)
  3. look-ahead 0 (knowable_from > as_of row 가 query 에서 안 나옴)
  4. silent revision 재현 (과거 조용한 수정 후에도 as_of 시점 값 동일, sys_time 분리)
  5. survivorship (상폐 종목이 그 시점 살아있으면 백테스트 universe 포함)
  6. 계약0 as_of_resolver seam (set/reset)
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import pytest

from stock.contracts import Fundamentals, FilingSource
from core.data import pit_panel
from core.data.pit_panel import (
    PanelAssembler, RoutingFundamentalsProvider, compute_multiples, fiscal_period_end,
)
from core.data import pit_query
from core.data.pit_query import PitPanel, query_as_of, as_of_view, set_as_of_resolver


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

def _fund(ticker, fp, filing, src=FilingSource.DART_XBRL, **kw):
    return Fundamentals(
        ticker=ticker, fiscal_period=fp,
        filing_timestamp=filing, source=src,
        currency="KRW", as_reported=(src != FilingSource.RESTATED),
        **kw,
    )


class FakeAdapter:
    """ticker → Fundamentals 목록 주입 (FundamentalsProvider 인터페이스)."""
    def __init__(self, by_ticker):
        self._by = by_ticker

    def fetch_filings(self, ticker, limit=8):
        return self._by.get(ticker, [])


class FakeKrxStatus:
    def __init__(self, flags=None):
        self._flags = flags or {}

    def get_status_snapshot(self, ticker, as_of=None):
        class _S:
            pass
        s = _S()
        for c in pit_panel.STATUS_COLS:
            setattr(s, c, self._flags.get(ticker, {}).get(c, False))
        return s


# ---------------------------------------------------------------------------
# 1. RESTATED 거부
# ---------------------------------------------------------------------------

def test_restated_rejected():
    funds = {
        "005930": [
            _fund("005930", "2023Q4", datetime(2024, 2, 1), net_income=100,
                  shareholders_equity=1000, revenue=500, ebitda=200),
            _fund("005930", "2023Q4", datetime(2024, 2, 1),
                  src=FilingSource.RESTATED, net_income=999),  # 재작성 — 거부돼야
        ]
    }
    asm = PanelAssembler(fundamentals_adapter=FakeAdapter(funds),
                         quote_fn=lambda t, d: 5000.0)
    panel = asm.assemble(["005930"], [datetime(2024, 3, 31)])
    assert len(panel) == 1
    assert panel.iloc[0]["filing_source"] == "dart_xbrl"
    assert panel.iloc[0]["net_income"] == 100  # restated 999 아님


# ---------------------------------------------------------------------------
# 2. filing-lag PIT (관측일 features = filing<=date 만)
# ---------------------------------------------------------------------------

def test_filing_lag():
    funds = {
        "000660": [
            _fund("000660", "2023Q2", datetime(2023, 8, 1), net_income=50,
                  shareholders_equity=800, revenue=300, ebitda=120),
            _fund("000660", "2023Q4", datetime(2024, 2, 15), net_income=80,
                  shareholders_equity=900, revenue=400, ebitda=160),
        ]
    }
    asm = PanelAssembler(fundamentals_adapter=FakeAdapter(funds),
                         quote_fn=lambda t, d: 10000.0)
    # 관측일 2023-12-31 → 2024-02-15 공시는 아직 모름 → 2023Q2 만 사용
    panel = asm.assemble(["000660"], [datetime(2023, 12, 31)])
    assert len(panel) == 1
    assert panel.iloc[0]["fiscal_period"] == "2023Q2"
    assert panel.iloc[0]["net_income"] == 50


# ---------------------------------------------------------------------------
# 3. look-ahead 0 (knowable_from > as_of → query 미반환)
# ---------------------------------------------------------------------------

def test_lookahead_blocked():
    funds = {
        "A": [_fund("A", "2023Q4", datetime(2024, 2, 1), net_income=100,
                    shareholders_equity=1000, revenue=500, ebitda=200)]
    }
    asm = PanelAssembler(fundamentals_adapter=FakeAdapter(funds),
                         quote_fn=lambda t, d: 5000.0)
    panel = asm.assemble(["A"], [datetime(2024, 3, 31)])  # knowable_from=2024-03-31
    # as_of 가 관측일 이전 → 안 보여야
    assert query_as_of(panel, "A", datetime(2024, 3, 31), datetime(2024, 1, 1)) is None
    # as_of 가 관측일 이후 → 보여야
    row = query_as_of(panel, "A", datetime(2024, 3, 31), datetime(2024, 6, 1))
    assert row is not None and row["net_income"] == 100


# ---------------------------------------------------------------------------
# 4. silent revision — sys_time 분리, as_of 시점 값 재현
# ---------------------------------------------------------------------------

def test_silent_revision():
    f = _fund("B", "2023Q4", datetime(2024, 2, 1), net_income=100,
              shareholders_equity=1000, revenue=500, ebitda=200)
    asm = PanelAssembler(fundamentals_adapter=FakeAdapter({"B": [f]}),
                         quote_fn=lambda t, d: 5000.0)
    d = datetime(2024, 3, 31)
    # v1: sys_time = 2024-03-31 빌드
    p1 = asm.assemble(["B"], [d], sys_time=datetime(2024, 3, 31))
    # 과거가 조용히 수정됨: 같은 firm/date, net_income 120, 새 sys_time(2024-09-01)
    f2 = _fund("B", "2023Q4", datetime(2024, 2, 1), net_income=120,
               shareholders_equity=1000, revenue=500, ebitda=200)
    asm2 = PanelAssembler(fundamentals_adapter=FakeAdapter({"B": [f2]}),
                          quote_fn=lambda t, d: 5000.0)
    p2 = asm2.assemble(["B"], [d], sys_time=datetime(2024, 9, 1))
    panel = pd.concat([p1, p2], ignore_index=True)  # append-only (불변식②)

    # as_of=2024-06-01 → 정정 전(sys_time<=06-01 최신=03-31 row) = 100
    r_before = query_as_of(panel, "B", d, datetime(2024, 6, 1))
    assert r_before["net_income"] == 100
    # as_of=2024-10-01 → 정정 후(sys_time 09-01) = 120
    r_after = query_as_of(panel, "B", d, datetime(2024, 10, 1))
    assert r_after["net_income"] == 120


# ---------------------------------------------------------------------------
# 5. survivorship — 상폐 종목이 그 시점 살아있으면 포함
# ---------------------------------------------------------------------------

def test_survivorship_includes_delisted():
    funds = {
        "DEAD": [_fund("DEAD", "2022Q4", datetime(2023, 2, 1), net_income=10,
                       shareholders_equity=100, revenue=50, ebitda=20)]
    }
    asm = PanelAssembler(
        fundamentals_adapter=FakeAdapter(funds),
        quote_fn=lambda t, d: 1000.0,
        delisted={"DEAD": datetime(2023, 12, 1)},  # 2023-12-01 상폐
    )
    # 관측일 2023-06-30 = 상폐 전 → 포함 + delist 메타
    panel = asm.assemble(["DEAD"], [datetime(2023, 6, 30)])
    assert len(panel) == 1
    assert panel.iloc[0]["delist_flag"] == True  # noqa: E712
    assert pd.Timestamp(panel.iloc[0]["delist_date"]) == pd.Timestamp("2023-12-01")
    # 관측일 2024-01-31 = 상폐 후 → universe 제외
    panel2 = asm.assemble(["DEAD"], [datetime(2024, 1, 31)])
    assert len(panel2) == 0


# ---------------------------------------------------------------------------
# 6. 계약0 as_of_resolver seam
# ---------------------------------------------------------------------------

def test_as_of_resolver_seam():
    # 기본 = 항등
    assert pit_query.resolve_as_of(datetime(2024, 1, 1)) == datetime(2024, 1, 1)
    # T3 resolver 주입 시뮬: 항상 월말로 정규화
    set_as_of_resolver(lambda x: datetime(x.year, x.month, 28))
    try:
        assert pit_query.resolve_as_of(datetime(2024, 1, 5)) == datetime(2024, 1, 28)
    finally:
        set_as_of_resolver(lambda x: x)  # 복원


# ---------------------------------------------------------------------------
# 7. 보조 — multiples / fiscal_period_end
# ---------------------------------------------------------------------------

def test_compute_multiples():
    f = _fund("X", "2023Q4", datetime(2024, 2, 1), net_income=100,
              shareholders_equity=1000, revenue=500, ebitda=200,
              total_debt=300, cash_and_equivalents=100)
    m = compute_multiples(f, market_cap=5000.0)
    assert m["per"] == 50.0           # 5000/100
    assert m["pbr"] == 5.0            # 5000/1000
    assert m["ps"] == 10.0            # 5000/500
    assert m["ev_ebitda"] == (5000 + 300 - 100) / 200  # 26.0
    # 분모 0 → None
    f0 = _fund("X", "2023Q4", datetime(2024, 2, 1), net_income=0,
               shareholders_equity=1000, revenue=500, ebitda=200)
    assert compute_multiples(f0, 5000.0)["per"] is None


def test_fiscal_period_end():
    assert fiscal_period_end("2023Q4") == datetime(2023, 12, 31)
    assert fiscal_period_end("2023Q1") == datetime(2023, 3, 31)
    assert fiscal_period_end("2023FY") == datetime(2023, 12, 31)
    assert fiscal_period_end("garbage") is None


def test_routing_provider():
    """KR(6자리) → dart, US(심볼) → edgar 라우팅 + None graceful."""
    f_kr = _fund("005930", "2023Q4", datetime(2024, 2, 1), net_income=1)
    f_us = _fund("AAPL", "2023FY", datetime(2024, 2, 1),
                 src=FilingSource.EDGAR_XBRL, net_income=2)
    router = RoutingFundamentalsProvider(
        dart_provider=FakeAdapter({"005930": [f_kr]}),
        edgar_provider=FakeAdapter({"AAPL": [f_us]}),
    )
    assert router.fetch_filings("005930")[0].net_income == 1
    assert router.fetch_filings("AAPL")[0].net_income == 2
    # provider 부재 → 빈 목록
    assert RoutingFundamentalsProvider().fetch_filings("005930") == []


def test_panel_schema_columns():
    """패널 컬럼이 PANEL-SCHEMA 와 정합."""
    funds = {"X": [_fund("X", "2023Q4", datetime(2024, 2, 1), net_income=100,
                         shareholders_equity=1000, revenue=500, ebitda=200)]}
    asm = PanelAssembler(fundamentals_adapter=FakeAdapter(funds),
                         quote_fn=lambda t, d: 5000.0)
    panel = asm.assemble(["X"], [datetime(2024, 3, 31)])
    assert list(panel.columns) == pit_panel.PANEL_COLUMNS
    # regime 은 T1 = NULL
    assert panel.iloc[0]["regime_id"] is pd.NA or pd.isna(panel.iloc[0]["regime_id"])
