"""ERB collector 테스트: stock/data/erb_snapshot (yfinance revision breadth self-snapshot).

검증기준 (forward-only bitemporal append-only):
- build_snapshot_rows → knowable_from=sys_time=as_of(normalize), PANEL_COLS 정합
- append_snapshot 멱등 → 같은 (ticker,period,sys_time) 재실행 무중복
- append_snapshot 누적 → 다른 sys_time = 새 layer 적립(과거 불변)
- erb_breadth → (up30-down30)/n_analysts, n 없으면 (up-down)/(up+down)
- load_us_universe → 3 sleeve 합집합 + 중복 제거(AVGO/AMD/NVDA 양쪽)
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stock.data import erb_snapshot as E


def _raw(tickers_periods):
    """(ticker, period, up30, down30, n) 리스트 → fetch_erb_live 출력 형태 raw."""
    rows = []
    for tk, pd_, up, dn, n in tickers_periods:
        d = {c: None for c in E.VALUE_COLS}
        d.update(ticker=tk, period=pd_, up30=float(up), down30=float(dn), n_analysts=float(n))
        rows.append(d)
    df = pd.DataFrame(rows)
    return df


def test_build_snapshot_rows_bitemporal():
    raw = _raw([("AAPL", "0y", 35, 2, 42), ("PG", "0y", 0, 19, 25)])
    as_of = datetime(2026, 6, 5, 14, 30)
    rows = E.build_snapshot_rows(raw, as_of)
    assert list(rows.columns) == E.PANEL_COLS
    # knowable_from == sys_time == as_of(normalize, 시각 제거)
    assert (rows["knowable_from"] == pd.Timestamp("2026-06-05")).all()
    assert (rows["sys_time"] == pd.Timestamp("2026-06-05")).all()
    assert set(rows["ticker"]) == {"AAPL", "PG"}


def test_append_idempotent(tmp_path):
    pq = str(tmp_path / "erb.parquet")
    rows = E.build_snapshot_rows(_raw([("AAPL", "0y", 35, 2, 42)]), datetime(2026, 6, 5))
    m1 = E.append_snapshot(rows, pq)
    m2 = E.append_snapshot(rows, pq)  # 같은 vintage 재실행
    assert len(m1) == len(m2) == 1  # 멱등 무중복


def test_append_accumulates_layers(tmp_path):
    pq = str(tmp_path / "erb.parquet")
    E.append_snapshot(E.build_snapshot_rows(_raw([("AAPL", "0y", 35, 2, 42)]), datetime(2026, 6, 5)), pq)
    merged = E.append_snapshot(
        E.build_snapshot_rows(_raw([("AAPL", "0y", 38, 1, 42)]), datetime(2026, 6, 6)), pq)
    # 다른 sys_time = 2 layer 누적, 과거(6/5) 불변
    assert len(merged) == 2
    d5 = merged[merged["sys_time"] == pd.Timestamp("2026-06-05")].iloc[0]
    assert d5["up30"] == 35 and d5["down30"] == 2  # 과거 layer repaint 안 됨


def test_erb_breadth():
    assert E.erb_breadth(35, 2, 42) == pytest.approx((35 - 2) / 42)
    # n_analysts 없으면 (up-down)/(up+down)
    assert E.erb_breadth(8, 2, None) == pytest.approx((8 - 2) / 10)
    # up=down=0 → None(0 division guard)
    assert E.erb_breadth(0, 0, None) is None


def test_load_us_universe_dedup():
    uni = E.load_us_universe()
    assert len(uni) == len(set(uni))  # 중복 제거됨
    # 3 sleeve 핵심 종목 포함
    for t in ("PG", "XOM", "AAPL", "NVDA"):
        assert t in uni
    # NVDA/AVGO/AMD = cyclical·mega 양쪽 → 1회만
    assert uni.count("NVDA") == 1


@pytest.mark.skip(reason="LIVE yfinance 네트워크 — 수동/CI 시에만")
def test_capture_live(tmp_path):
    res = E.capture(tickers=["AAPL", "MSFT"], parquet_path=str(tmp_path / "erb.parquet"))
    assert res["captured_tickers"] >= 1
    assert res["snapshot_rows"] > 0
