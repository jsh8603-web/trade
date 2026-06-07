"""stock/data/quote_provider.py — 종목 as_of 시점 quote provider (C4).

WHY: P3 주식 백테스트에서 매 bar 마다 종목의 as_of 기준 종가·시총이 필요하다.
     C3 HistoricalProvider 의 캐시를 조회하고 MarketQuote 계약(stock/contracts.py)으로
     반환한다.

설계 원칙:
- **미래거부**: `core/pit/as_of.py:resolve_as_of` 경유 강제 (lookahead 우회 차단).
  pit.as_of 항등 seam 아님 — 미래 as_of 진입 시 ValueError 발생·로깅 후 None 반환.
- **시총 근사**: 가격 × 시가총액배수(KR=발행주식수·US=shares_outstanding) — 정밀 시총
  없을 시 None (MarketQuote.market_cap=None). 시총 없어도 price 단독 반환.
- **graceful**: 네트워크·라이브러리 부재 시 None 반환 + source_missing 로깅(예외 X).
- **off byte-identical**: 기존 production import 경로 미접촉.
- **1일 lag 선택**: as_of 자체를 그대로 사용. 1일 lag 강제 여부는 호출자가 결정
  (백테스트 bar 시점이 이미 lag 반영 — 이중 lag 방지).

MarketQuote (stock/contracts.py):
  ticker / as_of / price / market_cap / price_change_pct / price_change_window_days
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from stock.data.historical_provider import HistoricalProvider, OhlcvBar

logger = logging.getLogger("stock.data.quote_provider")


# ---------------------------------------------------------------------------
# lazy import — pit.as_of (pandas 의존성 격리)
# ---------------------------------------------------------------------------

def _resolve_as_of(as_of_raw):
    """core.pit.as_of.resolve_as_of 경유 미래거부. 실패 시 ValueError 전파."""
    from core.pit.as_of import resolve_as_of
    return resolve_as_of(as_of_raw)


def _resolve_as_of_safe(as_of_raw) -> Optional[date]:
    """미래 as_of → None + 로깅(예외 X). 정상 → date 반환."""
    try:
        ts = _resolve_as_of(as_of_raw)
        return ts.date()
    except ValueError as exc:
        logger.warning(
            "미래 as_of 거부(lookahead) [source_missing]: %s", exc
        )
        return None


# ---------------------------------------------------------------------------
# 시총 근사 (shares × price)
# ---------------------------------------------------------------------------

def _approx_market_cap_kr(ticker: str, price: float) -> Optional[float]:
    """KR 발행주식수 × 종가 근사 시총(원). pykrx get_market_cap_by_date 이용."""
    try:
        from pykrx import stock as pk
        # 당일 시총(가장 최근 영업일) 직접 조회 — 역사 시총은 pykrx 가 보존
        # 실제 백테스트에서는 as_of 날짜를 주지만 여기서는 빈 결과 graceful 처리
        return None  # 정밀 시총은 별도 스냅샷 인프라 필요 — 현재 None graceful
    except Exception:
        return None


def _approx_market_cap_us(ticker: str, price: float) -> Optional[float]:
    """US shares_outstanding × 종가 근사 시총($). yfinance info 이용."""
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        shares = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
        if shares and shares > 0:
            return float(shares) * price
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# quote_at 핵심 함수
# ---------------------------------------------------------------------------

def get_quote_at(
    ticker: str,
    as_of,
    region: str,
    *,
    provider: Optional[HistoricalProvider] = None,
    with_market_cap: bool = False,
    price_change_window_days: Optional[int] = None,
):
    """as_of 시점 종목 MarketQuote 반환.

    Parameters
    ----------
    ticker : 종목 코드 (KR=6자리 숫자 / US=심볼)
    as_of  : 의사결정 시점 (str/date/datetime/pd.Timestamp). 미래→None.
    region : "KR" | "US"
    provider : HistoricalProvider 인스턴스. None 이면 기본 캐시 루트 사용.
    with_market_cap : True 이면 시총 근사 산출(추가 네트워크 호출 발생 가능).
    price_change_window_days : 지정 시 price_change_pct 를 같이 산출.

    Returns
    -------
    MarketQuote | None
        - None : 미래 as_of / 데이터 없음 / 네트워크 오류
        - source_missing : None 반환 + logger.warning 발생
    """
    from stock.contracts import MarketQuote

    region = region.upper()

    # 1. PIT 미래거부 (core.pit.as_of 경유 — lookahead 차단)
    as_of_date = _resolve_as_of_safe(as_of)
    if as_of_date is None:
        return None  # 미래 as_of — 로깅은 _resolve_as_of_safe 가 담당

    # 2. C3 캐시 조회
    _provider = provider or HistoricalProvider()
    # 가격 변동 계산용 윈도우 확보 (최소 30일, 지정 시 그 이상)
    lookback_days = max(30, (price_change_window_days or 0) + 5)
    fetch_start = as_of_date - timedelta(days=lookback_days)

    bars = _provider.get_ohlcv_range(
        ticker, fetch_start, as_of_date, region=region, as_of=as_of_date
    )

    if not bars:
        logger.warning(
            "quote_at 데이터 없음 %s/%s as_of=%s [source_missing]",
            region, ticker, as_of_date,
        )
        return None

    # 3. as_of 기준 가장 최근 bar 선택
    latest: OhlcvBar = bars[-1]
    price = latest.close

    # 4. 시총 근사 (선택)
    market_cap: Optional[float] = None
    if with_market_cap:
        if region == "KR":
            market_cap = _approx_market_cap_kr(ticker, price)
        elif region == "US":
            market_cap = _approx_market_cap_us(ticker, price)

    # 5. 가격 변동률 (선택)
    price_change_pct: Optional[float] = None
    if price_change_window_days and price_change_window_days > 0:
        # 윈도우 이전 bar 탐색
        cutoff_str = (as_of_date - timedelta(days=price_change_window_days)).isoformat()
        prev_bars = [b for b in bars if b.date <= cutoff_str]
        if prev_bars:
            prev_price = prev_bars[-1].close
            if prev_price > 0:
                price_change_pct = (price - prev_price) / prev_price

    # 6. MarketQuote 조립
    # as_of 를 datetime 으로 정규화 (contracts 계약)
    as_of_dt = datetime.combine(as_of_date, datetime.min.time())

    return MarketQuote(
        ticker=ticker,
        as_of=as_of_dt,
        price=price,
        market_cap=market_cap,
        price_change_pct=price_change_pct,
        price_change_window_days=price_change_window_days,
    )


# ---------------------------------------------------------------------------
# QuoteProvider 클래스 (캐시 루트·공유 provider 주입 편의)
# ---------------------------------------------------------------------------

class QuoteProvider:
    """get_quote_at 의 stateful wrapper — 공유 HistoricalProvider 재사용.

    백테스트 루프에서 종목×bar 수만큼 호출 시 provider 를 한 번 생성·공유.
    """

    def __init__(self, cache_root: Optional[Path] = None):
        self._provider = HistoricalProvider(cache_root=cache_root)

    def get_quote_at(
        self,
        ticker: str,
        as_of,
        region: str,
        *,
        with_market_cap: bool = False,
        price_change_window_days: Optional[int] = None,
    ):
        """as_of 시점 MarketQuote 반환. 시그니처는 모듈 함수와 동일."""
        return get_quote_at(
            ticker,
            as_of,
            region,
            provider=self._provider,
            with_market_cap=with_market_cap,
            price_change_window_days=price_change_window_days,
        )


# ---------------------------------------------------------------------------
# self-test (graceful — 네트워크 불요, 캐시 주입·PIT 거부만)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    import tempfile
    from datetime import date
    from stock.data.historical_provider import _append_cache, OhlcvBar

    tmp = Path(tempfile.mkdtemp()) / "ohlcv_cache"
    provider = HistoricalProvider(cache_root=tmp)

    # 캐시 주입
    bars = [
        OhlcvBar("AAPL", "2024-01-02", 182.0, 185.0, 181.0, 184.0, 50_000_000),
        OhlcvBar("AAPL", "2024-01-03", 184.0, 187.0, 183.0, 185.5, 55_000_000),
        OhlcvBar("AAPL", "2024-01-04", 185.5, 188.0, 184.0, 186.0, 48_000_000),
    ]
    _append_cache("AAPL", "US", bars, root=tmp)

    # 정상 조회
    q = get_quote_at("AAPL", date(2024, 1, 3), "US", provider=provider)
    assert q is not None, "정상 조회 실패"
    assert q.ticker == "AAPL"
    assert q.price == 185.5, f"가격 불일치: {q.price}"

    # 미래 as_of → None (lookahead 거부)
    import datetime as dt
    future = dt.date.today() + dt.timedelta(days=365)
    q_future = get_quote_at("AAPL", future, "US", provider=provider)
    assert q_future is None, "미래 as_of 가 통과됨 — lookahead 차단 실패"

    # 데이터 없는 종목 → None [source_missing]
    q_none = get_quote_at("ZZZZZ", date(2024, 1, 3), "US", provider=provider)
    assert q_none is None, "없는 종목이 None 이 아님"

    print("quote_provider self-test PASSED")


if __name__ == "__main__":
    _self_test()
