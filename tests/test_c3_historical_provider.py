"""tests/test_c3_historical_provider.py — C3 주식 OHLCV batch provider 단위 테스트.

검증 항목:
- KR fixture mock(pykrx) OHLCV 형태 + 필드 존재
- US fixture mock(yfinance) OHLCV 형태 + 필드 존재
- 캐시 라운드트립(write→load 일치)
- 캐시 중복 append skip(idempotent)
- PIT 불변식: as_of 초과 행 제거(look-ahead 차단)
- source_missing 라벨: 결측 시 빈 리스트 반환(예외 X)
- 실네트워크=1건 skipped LIVE 마킹
"""

from __future__ import annotations

import json
import sys
import os
import tempfile
import types
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 프로젝트 루트를 sys.path 에 추가
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from stock.data.historical_provider import (
    OhlcvBar,
    HistoricalProvider,
    _append_cache,
    _load_cache,
    _cache_path,
    _business_dates,
)


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _make_bars(ticker: str, start: date, n: int) -> list[OhlcvBar]:
    """연속 n일 dummy bar 생성."""
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
            volume=1_000_000 + i * 1000,
        ))
        cur += timedelta(days=1)
    return bars


def _tmp_provider() -> tuple[HistoricalProvider, Path]:
    tmp = Path(tempfile.mkdtemp()) / "ohlcv_cache"
    return HistoricalProvider(cache_root=tmp), tmp


# ---------------------------------------------------------------------------
# OHLCV 형태 검증 헬퍼
# ---------------------------------------------------------------------------

def _assert_ohlcv_shape(bars: list[OhlcvBar], ticker: str, min_bars: int = 1) -> None:
    assert len(bars) >= min_bars, f"bar 수 부족: {len(bars)}"
    for b in bars:
        assert b.ticker == ticker
        assert len(b.date) == 10, f"날짜 형식 오류: {b.date}"
        assert b.open > 0, "open 0 이하"
        assert b.high >= b.low, "high < low"
        assert b.close > 0, "close 0 이하"
        assert b.volume >= 0, "volume 음수"


# ---------------------------------------------------------------------------
# 캐시 단위 테스트
# ---------------------------------------------------------------------------

class TestCacheRoundtrip:
    def test_write_and_load(self, tmp_path):
        """캐시 write→load 라운드트립."""
        from stock.data import historical_provider as hp
        bars = _make_bars("005930", date(2024, 1, 2), 3)
        hp._append_cache("005930", "KR", bars, root=tmp_path)
        cached = hp._load_cache("005930", "KR", root=tmp_path)

        assert len(cached) == 3
        assert "2024-01-02" in cached
        assert cached["2024-01-02"].close == 103.0

    def test_duplicate_append_idempotent(self, tmp_path):
        """중복 append 시 bar 수 불변(idempotent)."""
        from stock.data import historical_provider as hp
        bars = _make_bars("AAPL", date(2024, 1, 2), 3)
        hp._append_cache("AAPL", "US", bars, root=tmp_path)
        hp._append_cache("AAPL", "US", bars, root=tmp_path)  # 중복
        cached = hp._load_cache("AAPL", "US", root=tmp_path)

        assert len(cached) == 3, f"중복 append 후 bar 수: {len(cached)}"

    def test_partial_append(self, tmp_path):
        """기존 3행 + 신규 2행 → 합 5행."""
        from stock.data import historical_provider as hp
        bars_old = _make_bars("TEST", date(2024, 1, 2), 3)
        bars_new = _make_bars("TEST", date(2024, 1, 5), 2)
        hp._append_cache("TEST", "KR", bars_old, root=tmp_path)
        hp._append_cache("TEST", "KR", bars_new, root=tmp_path)
        cached = hp._load_cache("TEST", "KR", root=tmp_path)

        assert len(cached) == 5


# ---------------------------------------------------------------------------
# PIT 불변식
# ---------------------------------------------------------------------------

class TestPitInvariant:
    def test_as_of_cutoff_filters_future(self, tmp_path):
        """as_of 초과 행 제거 — look-ahead 차단."""
        from stock.data import historical_provider as hp
        provider = HistoricalProvider(cache_root=tmp_path)
        bars = _make_bars("005380", date(2024, 1, 2), 5)  # 1/2~1/6
        hp._append_cache("005380", "KR", bars, root=tmp_path)

        result = provider.get_ohlcv_range(
            "005380",
            date(2024, 1, 1),
            date(2024, 1, 6),
            region="KR",
            as_of=date(2024, 1, 3),
        )
        # 1/2, 1/3 만 포함 (1/4~1/6 제거)
        assert all(b.date <= "2024-01-03" for b in result), "미래 행 포함됨"
        assert len(result) >= 1

    def test_as_of_exact_boundary(self, tmp_path):
        """as_of 당일은 포함 — 캐시 직접 주입 후 provider 로 확인."""
        from stock.data import historical_provider as hp
        # tmp_path 경로로 직접 jsonl 파일 생성
        bar = OhlcvBar("X", "2024-03-01", 100, 101, 99, 100, 500)
        cache_path = tmp_path / "US" / "X.jsonl"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(bar.to_dict()) + "\n")

        provider = HistoricalProvider(cache_root=tmp_path)
        result = provider.get_ohlcv_range(
            "X", date(2024, 3, 1), date(2024, 3, 1), region="US", as_of=date(2024, 3, 1)
        )
        assert len(result) == 1, "as_of 당일 행 누락"


# ---------------------------------------------------------------------------
# KR fixture mock (pykrx)
# ---------------------------------------------------------------------------

class TestKrMock:
    def _make_kr_df(self):
        """pykrx get_market_ohlcv_by_date 반환 DataFrame fixture."""
        import pandas as pd
        data = {
            "시가":  [73100, 73500, 73200],
            "고가":  [73400, 73800, 73600],
            "저가":  [72800, 73100, 72900],
            "종가":  [73200, 73700, 73000],
            "거래량": [10_000_000, 12_000_000, 9_000_000],
        }
        idx = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
        return pd.DataFrame(data, index=idx)

    def test_kr_ohlcv_shape_via_mock(self, tmp_path):
        """pykrx mock 경유 KR OHLCV 형태 검증."""
        df = self._make_kr_df()
        mock_pk = MagicMock()
        mock_pk.get_market_ohlcv_by_date.return_value = df

        with patch("stock.data.historical_provider._pykrx_stock", return_value=mock_pk):
            from stock.data import historical_provider as hp
            bars = hp._fetch_kr("005930", date(2024, 1, 2), date(2024, 1, 4))

        assert len(bars) == 3
        _assert_ohlcv_shape(bars, "005930", min_bars=3)
        assert bars[0].close == 73200.0
        assert bars[1].volume == 12_000_000

    def test_kr_pykrx_fail_fdr_fallback(self, tmp_path):
        """pykrx 실패 → FDR fallback 경로."""
        import pandas as pd
        fdr_df = pd.DataFrame({
            "Open":   [73100, 73500],
            "High":   [73400, 73800],
            "Low":    [72800, 73100],
            "Close":  [73200, 73700],
            "Volume": [10_000_000, 12_000_000],
        }, index=pd.to_datetime(["2024-01-02", "2024-01-03"]))

        def _raise():
            raise RuntimeError("pykrx down")

        mock_fdr = MagicMock()
        mock_fdr.DataReader.return_value = fdr_df

        with patch("stock.data.historical_provider._pykrx_stock", side_effect=_raise):
            with patch("stock.data.historical_provider._fdr", return_value=mock_fdr):
                from stock.data import historical_provider as hp
                bars = hp._fetch_kr("005930", date(2024, 1, 2), date(2024, 1, 3))

        assert len(bars) == 2
        _assert_ohlcv_shape(bars, "005930", min_bars=2)

    def test_kr_all_fail_returns_empty(self):
        """pykrx + FDR 모두 실패 → 빈 리스트(예외 X)."""
        def _raise():
            raise RuntimeError("both down")

        with patch("stock.data.historical_provider._pykrx_stock", side_effect=_raise):
            with patch("stock.data.historical_provider._fdr", side_effect=_raise):
                from stock.data import historical_provider as hp
                bars = hp._fetch_kr("005930", date(2024, 1, 2), date(2024, 1, 4))

        assert bars == [], "실패 시 빈 리스트 반환 필수"


# ---------------------------------------------------------------------------
# US fixture mock (yfinance)
# ---------------------------------------------------------------------------

class TestUsMock:
    def _make_us_df(self):
        """yfinance history 반환 DataFrame fixture."""
        import pandas as pd
        data = {
            "Open":   [182.0, 183.5, 181.0],
            "High":   [185.0, 186.0, 184.0],
            "Low":    [181.5, 182.0, 180.0],
            "Close":  [184.0, 185.5, 182.0],
            "Volume": [50_000_000, 55_000_000, 48_000_000],
            "Adj Close": [184.0, 185.5, 182.0],
        }
        idx = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
        return pd.DataFrame(data, index=idx)

    def test_us_ohlcv_shape_via_mock(self):
        """yfinance mock 경유 US OHLCV 형태 검증."""
        df = self._make_us_df()
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = df
        mock_yf = MagicMock()
        mock_yf.Ticker.return_value = mock_ticker

        with patch("stock.data.historical_provider._yf", return_value=mock_yf):
            from stock.data import historical_provider as hp
            bars = hp._fetch_us("AAPL", date(2024, 1, 2), date(2024, 1, 4))

        assert len(bars) == 3
        _assert_ohlcv_shape(bars, "AAPL", min_bars=3)
        assert bars[0].close == 184.0
        assert bars[2].volume == 48_000_000

    def test_us_empty_returns_empty(self):
        """빈 DataFrame → 빈 리스트(예외 X) [data_empty]."""
        import pandas as pd
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_yf = MagicMock()
        mock_yf.Ticker.return_value = mock_ticker

        with patch("stock.data.historical_provider._yf", return_value=mock_yf):
            from stock.data import historical_provider as hp
            bars = hp._fetch_us("AAPL", date(2024, 1, 2), date(2024, 1, 4))

        assert bars == []

    def test_us_exception_returns_empty(self):
        """yfinance 예외 → 빈 리스트(예외 X) [source_missing]."""
        def _raise():
            raise RuntimeError("yf down")

        with patch("stock.data.historical_provider._yf", side_effect=_raise):
            from stock.data import historical_provider as hp
            bars = hp._fetch_us("AAPL", date(2024, 1, 2), date(2024, 1, 4))

        assert bars == []


# ---------------------------------------------------------------------------
# provider 통합 (mock 캐시 히트 경로)
# ---------------------------------------------------------------------------

class TestProviderIntegration:
    def test_cache_hit_no_fetch(self, tmp_path):
        """캐시에 행 있으면 누락 구간에만 fetch 호출 — 캐시 히트 행은 fetch 미발생."""
        # 2024-01-02(화)~2024-01-04(목) 3영업일 캐시 직접 주입
        for d in ["2024-01-02", "2024-01-03", "2024-01-04"]:
            cache_path = tmp_path / "US" / "TSLA.jsonl"
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "a", encoding="utf-8") as fh:
                bar = OhlcvBar("TSLA", d, 200.0, 205.0, 198.0, 203.0, 5_000_000)
                fh.write(json.dumps(bar.to_dict()) + "\n")

        provider = HistoricalProvider(cache_root=tmp_path)
        # 캐시 구간만 요청(1/2~1/4) → fetch 미호출
        with patch.object(provider, "_fetch", side_effect=AssertionError("fetch 불필요")):
            result = provider.get_ohlcv_range(
                "TSLA", date(2024, 1, 2), date(2024, 1, 4), region="US"
            )
        assert len(result) == 3, f"캐시 히트 bar 수 오류: {len(result)}"

    def test_missing_region_returns_empty(self, tmp_path):
        """unknown region → 빈 리스트(예외 X) [source_missing]."""
        provider = HistoricalProvider(cache_root=tmp_path)
        result = provider.get_ohlcv_range(
            "XYZ", date(2024, 1, 1), date(2024, 1, 5), region="JP"
        )
        assert result == []

    def test_business_dates_excludes_weekend(self):
        """_business_dates: 주말 제외."""
        # 2024-01-06(토), 2024-01-07(일) 제외 확인
        dates = _business_dates(date(2024, 1, 4), date(2024, 1, 8))
        assert "2024-01-06" not in dates
        assert "2024-01-07" not in dates
        assert "2024-01-04" in dates
        assert "2024-01-05" in dates
        assert "2024-01-08" in dates


# ---------------------------------------------------------------------------
# LIVE (실네트워크 — CI skip)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="LIVE: 실네트워크 필요 — CI skip")
class TestLive:
    def test_kr_samsung_live(self, tmp_path):
        """KR 삼성전자 30일 OHLCV fetch (실네트워크)."""
        provider = HistoricalProvider(cache_root=tmp_path)
        end = date.today() - timedelta(days=1)
        start = end - timedelta(days=30)
        bars = provider.get_ohlcv_range("005930", start, end, region="KR")
        _assert_ohlcv_shape(bars, "005930", min_bars=10)

    def test_us_apple_live(self, tmp_path):
        """US AAPL 30일 OHLCV fetch (실네트워크)."""
        provider = HistoricalProvider(cache_root=tmp_path)
        end = date.today() - timedelta(days=1)
        start = end - timedelta(days=30)
        bars = provider.get_ohlcv_range("AAPL", start, end, region="US")
        _assert_ohlcv_shape(bars, "AAPL", min_bars=10)
