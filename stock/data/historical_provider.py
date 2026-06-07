"""stock/data/historical_provider.py — 종목 OHLCV 배치 provider (C3).

WHY: P3 주식 백테스트용 과거 OHLCV(시가·고가·저가·종가·거래량)를 종목×기간 단위로
     배치 pull 하고 jsonl 캐시로 저장한다.

설계 원칙:
- KR: pykrx(무료·무키·KRX 역사 OHLCV). 없으면 FinanceDataReader 로 fallback.
- US: yfinance(무료·무키·Yahoo Finance 역사 OHLCV).
- 캐시: data/ohlcv_cache/{region}/{ticker}.jsonl (날짜·행 단위 append, 중복 skip).
- PIT 불변식: get_ohlcv_range(as_of=) 는 as_of 초과 행 제거(look-ahead 차단).
- graceful: 네트워크·라이브러리 부재 시 빈 리스트 반환 + source_missing 로깅(예외 X).
- off byte-identical: 기존 production import 경로(run_agents.py/engine.py) 미접촉.

캐시 포맷 (1줄 = 1영업일):
  {"ticker":"005930","date":"2024-01-02","open":73100,"high":73400,"low":72800,"close":73200,"volume":10000000}
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Sequence

logger = logging.getLogger("stock.data.historical_provider")

# 캐시 루트: data/ohlcv_cache/KR/<ticker>.jsonl  /  data/ohlcv_cache/US/<ticker>.jsonl
_CACHE_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "ohlcv_cache"

# 한 번에 fetch 할 최대 일수(yfinance/pykrx 과부하 방지)
_MAX_FETCH_DAYS = 365 * 15  # 15년


# ---------------------------------------------------------------------------
# lazy imports (라이브러리 없으면 ImportError → graceful 핸들)
# ---------------------------------------------------------------------------

def _pykrx_stock():
    from pykrx import stock as pk  # noqa: F401
    return pk


def _fdr():
    import FinanceDataReader as fdr  # noqa: F401
    return fdr


def _yf():
    import yfinance as yf  # noqa: F401
    return yf


# ---------------------------------------------------------------------------
# 계약
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OhlcvBar:
    """단일 영업일 OHLCV 바."""

    ticker: str
    date: str        # "YYYY-MM-DD"
    open: float
    high: float
    low: float
    close: float
    volume: float    # 주(KR) 또는 주(US) — 거래대금 아님

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 캐시 I/O
# ---------------------------------------------------------------------------

def _cache_path(ticker: str, region: str, root: Optional[Path] = None) -> Path:
    return (root or _CACHE_ROOT) / region.upper() / f"{ticker}.jsonl"


def _load_cache(ticker: str, region: str, root: Optional[Path] = None) -> Dict[str, OhlcvBar]:
    """jsonl 캐시 전체 로드 → {date_str: OhlcvBar}."""
    path = _cache_path(ticker, region, root)
    result: Dict[str, OhlcvBar] = {}
    if not path.exists():
        return result
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                d = rec.get("date", "")
                if d:
                    result[d] = OhlcvBar(
                        ticker=rec.get("ticker", ticker),
                        date=d,
                        open=float(rec.get("open", 0)),
                        high=float(rec.get("high", 0)),
                        low=float(rec.get("low", 0)),
                        close=float(rec.get("close", 0)),
                        volume=float(rec.get("volume", 0)),
                    )
    except Exception as exc:
        logger.warning("OHLCV 캐시 로드 실패 %s/%s: %s [data_empty]", region, ticker, exc)
    return result


def _append_cache(ticker: str, region: str, bars: List[OhlcvBar], root: Optional[Path] = None) -> None:
    """신규 바만 jsonl append (기존 날짜 중복 skip)."""
    if not bars:
        return
    path = _cache_path(ticker, region, root)
    existing = _load_cache(ticker, region, root)
    new_bars = [b for b in bars if b.date not in existing]
    if not new_bars:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            for bar in sorted(new_bars, key=lambda b: b.date):
                fh.write(json.dumps(bar.to_dict(), ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("OHLCV 캐시 적재 실패 %s/%s: %s", region, ticker, exc)


# ---------------------------------------------------------------------------
# KR fetch (pykrx → FDR fallback)
# ---------------------------------------------------------------------------

def _fetch_kr(ticker: str, start: date, end: date) -> List[OhlcvBar]:
    """pykrx로 KR 종목 OHLCV fetch. 실패 시 FDR fallback → 빈 리스트."""
    start_str = start.strftime("%Y%m%d")
    end_str = end.strftime("%Y%m%d")

    # 1차: pykrx
    try:
        pk = _pykrx_stock()
        df = pk.get_market_ohlcv_by_date(start_str, end_str, ticker)
        if df is not None and len(df) > 0:
            bars: List[OhlcvBar] = []
            for idx, row in df.iterrows():
                d = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
                bars.append(OhlcvBar(
                    ticker=ticker,
                    date=d,
                    open=float(row.get("시가", row.get("Open", 0))),
                    high=float(row.get("고가", row.get("High", 0))),
                    low=float(row.get("저가", row.get("Low", 0))),
                    close=float(row.get("종가", row.get("Close", 0))),
                    volume=float(row.get("거래량", row.get("Volume", 0))),
                ))
            return bars
    except Exception as exc:
        logger.info("pykrx fetch 실패 %s, FDR fallback 시도: %s", ticker, exc)

    # 2차: FDR fallback
    try:
        fdr = _fdr()
        df = fdr.DataReader(ticker, start.isoformat(), end.isoformat())
        if df is not None and len(df) > 0:
            bars = []
            for idx, row in df.iterrows():
                d = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
                bars.append(OhlcvBar(
                    ticker=ticker,
                    date=d,
                    open=float(row.get("Open", 0)),
                    high=float(row.get("High", 0)),
                    low=float(row.get("Low", 0)),
                    close=float(row.get("Close", 0)),
                    volume=float(row.get("Volume", 0)),
                ))
            return bars
    except Exception as exc:
        logger.warning("KR OHLCV fetch 전부 실패 %s: %s [source_missing]", ticker, exc)

    return []


# ---------------------------------------------------------------------------
# US fetch (yfinance)
# ---------------------------------------------------------------------------

def _fetch_us(ticker: str, start: date, end: date) -> List[OhlcvBar]:
    """yfinance로 US 종목 OHLCV fetch. 실패 시 빈 리스트."""
    try:
        yf = _yf()
        end_excl = (end + timedelta(days=1)).isoformat()  # yfinance end 는 exclusive
        hist = yf.Ticker(ticker).history(
            start=start.isoformat(), end=end_excl, auto_adjust=False
        )
        if hist is None or len(hist) == 0:
            logger.warning("US OHLCV 결과 없음 %s [data_empty]", ticker)
            return []
        bars: List[OhlcvBar] = []
        for idx, row in hist.iterrows():
            d = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
            bars.append(OhlcvBar(
                ticker=ticker,
                date=d,
                open=float(row.get("Open", 0)),
                high=float(row.get("High", 0)),
                low=float(row.get("Low", 0)),
                close=float(row.get("Close", 0)),
                volume=float(row.get("Volume", 0)),
            ))
        return bars
    except Exception as exc:
        logger.warning("US OHLCV fetch 실패 %s: %s [source_missing]", ticker, exc)
        return []


# ---------------------------------------------------------------------------
# 핵심 provider
# ---------------------------------------------------------------------------

class HistoricalProvider:
    """종목 OHLCV 배치 pull + jsonl 캐시.

    사용법:
        provider = HistoricalProvider()
        bars = provider.get_ohlcv_range("005930", date(2020,1,1), date(2024,12,31), region="KR")
        bars_pit = provider.get_ohlcv_range("AAPL", date(2020,1,1), date(2024,12,31),
                                             region="US", as_of=date(2023,6,30))
    """

    def __init__(self, cache_root: Optional[Path] = None):
        self._cache_root = cache_root or _CACHE_ROOT

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def get_ohlcv_range(
        self,
        ticker: str,
        start: date,
        end: date,
        region: str,
        as_of: Optional[date] = None,
        force_fetch: bool = False,
    ) -> List[OhlcvBar]:
        """ticker 의 [start, end] OHLCV 배치 반환.

        - 캐시 미스 구간 자동 fetch + 적재.
        - as_of 지정 시 as_of 초과 행 제거(PIT 불변식 — look-ahead 차단).
        - force_fetch=True 시 캐시 무시하고 재fetch.
        """
        region = region.upper()
        pit_cutoff = as_of if as_of else end

        # 캐시 로드 (self._cache_root 경유 — 테스트 격리 보장)
        cached = {} if force_fetch else _load_cache(ticker, region, self._cache_root)

        # 캐시 미스 구간 계산
        needed_dates = _business_dates(start, min(end, pit_cutoff))
        missing = [d for d in needed_dates if d not in cached]

        # fetch 필요 시
        if missing:
            fetch_start = date.fromisoformat(missing[0])
            fetch_end = date.fromisoformat(missing[-1])
            fetched = self._fetch(ticker, fetch_start, fetch_end, region)
            if fetched:
                _append_cache(ticker, region, fetched, self._cache_root)
                # 캐시 갱신 반영
                for bar in fetched:
                    cached[bar.date] = bar
            else:
                logger.warning(
                    "OHLCV fetch 결과 없음 %s/%s %s~%s [source_missing]",
                    region, ticker, fetch_start, fetch_end,
                )

        # PIT 필터: as_of 초과 제거
        pit_str = pit_cutoff.isoformat()
        bars = [b for b in cached.values() if b.date >= start.isoformat() and b.date <= pit_str]
        bars.sort(key=lambda b: b.date)
        return bars

    def get_latest_close(
        self,
        ticker: str,
        region: str,
        as_of: date,
    ) -> Optional[float]:
        """as_of 기준 가장 최근 종가(PIT). 데이터 없으면 None."""
        start = as_of - timedelta(days=30)
        bars = self.get_ohlcv_range(ticker, start, as_of, region=region, as_of=as_of)
        if not bars:
            logger.warning("종가 없음 %s/%s as_of=%s [data_empty]", region, ticker, as_of)
            return None
        return bars[-1].close

    def prefetch_batch(
        self,
        tickers: Sequence[str],
        start: date,
        end: date,
        region: str,
    ) -> Dict[str, int]:
        """종목 리스트 배치 prefetch. {ticker: bar_count} 반환."""
        result: Dict[str, int] = {}
        for ticker in tickers:
            bars = self.get_ohlcv_range(ticker, start, end, region=region)
            result[ticker] = len(bars)
        return result

    # ------------------------------------------------------------------
    # 내부
    # ------------------------------------------------------------------

    def _fetch(self, ticker: str, start: date, end: date, region: str) -> List[OhlcvBar]:
        """region 에 따라 KR/US fetch 분기."""
        span = (end - start).days
        if span > _MAX_FETCH_DAYS:
            logger.warning("fetch 구간 %d일 > %d일 상한 — 상한 적용", span, _MAX_FETCH_DAYS)
            start = end - timedelta(days=_MAX_FETCH_DAYS)

        if region == "KR":
            return _fetch_kr(ticker, start, end)
        elif region == "US":
            return _fetch_us(ticker, start, end)
        else:
            logger.warning("알 수 없는 region %s [source_missing]", region)
            return []


# ---------------------------------------------------------------------------
# 편의 함수
# ---------------------------------------------------------------------------

def _business_dates(start: date, end: date) -> List[str]:
    """start~end 사이 평일(월~금) 날짜 문자열 리스트 (간이 — 공휴일 제외 안 함)."""
    result = []
    cur = start
    while cur <= end:
        if cur.weekday() < 5:  # 월(0)~금(4)
            result.append(cur.isoformat())
        cur += timedelta(days=1)
    return result


# ---------------------------------------------------------------------------
# self-test (graceful — 네트워크 불요, 캐시 라운드트립만)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    import tempfile

    tmp_root = Path(tempfile.mkdtemp()) / "ohlcv_cache"
    provider = HistoricalProvider(cache_root=tmp_root)

    # ── 캐시 write/read 라운드트립 ──
    fake_bars = [
        OhlcvBar("TEST", "2024-01-02", 100.0, 105.0, 99.0, 103.0, 1_000_000),
        OhlcvBar("TEST", "2024-01-03", 103.0, 107.0, 102.0, 106.0, 1_100_000),
        OhlcvBar("TEST", "2024-01-04", 106.0, 108.0, 104.0, 105.0, 900_000),
    ]
    _append_cache("TEST", "KR", fake_bars)

    # 로드 검증
    cached = _load_cache("TEST", "KR")
    assert "2024-01-02" in cached, "캐시 날짜 누락"
    assert cached["2024-01-02"].close == 103.0, "종가 불일치"
    assert len(cached) == 3, f"bar 수 불일치: {len(cached)}"

    # 중복 append 시 길이 불변 확인
    _append_cache("TEST", "KR", fake_bars)
    cached2 = _load_cache("TEST", "KR")
    assert len(cached2) == 3, "중복 append 시 길이 증가 — 중복 skip 실패"

    # PIT 필터 확인 (as_of=2024-01-02 → 마지막 2행 제거)
    result = provider.get_ohlcv_range(
        "TEST",
        date(2024, 1, 1),
        date(2024, 1, 5),
        region="KR",
        as_of=date(2024, 1, 2),
    )
    assert len(result) == 1, f"PIT 필터 실패: {len(result)}"
    assert result[0].date == "2024-01-02", "PIT 필터 날짜 오류"

    print("historical_provider self-test PASSED")


if __name__ == "__main__":
    _self_test()
