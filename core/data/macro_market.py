"""core/data/macro_market.py — 매크로 시장 수집기 (DXY · USDKRW → FxStore PIT 적재).

달러 인덱스(DXY)와 원/달러 환율(USDKRW)을 Yahoo Finance 무료 API 에서 일별로 끌어와
:class:`core.data.fx.FxStore` 에 bitemporal(rate_date + knowable_from) 으로 적재한다.

PIT 규칙 (lookahead 차단):
- 각 일봉의 종가는 **그 거래일 종료 시점**에 확정된다. 따라서 그 종가를 우리가 알 수 있는
  최초 시점(knowable_from) = rate_date 와 동일 거래일로 둔다 (장 마감 후 가용). 즉
  rate_date == knowable_from. 이렇게 하면 as_of < rate_date 인 백테스트 의사결정에서는
  해당 종가가 미가시 → fill-forward 만 사용되어 lookahead 가 원천 차단된다.

표현:
- USDKRW → FxStore 직접쌍 ``USD/KRW`` (1 USD = N KRW). FxStore.get_rate("USD","KRW",..) 로 조회.
- DXY 는 통화쌍이 아니라 지수지만, bitemporal 시계열을 동일 substrate 에 담기 위해 합성쌍
  ``DXY/USD`` 로 적재한다 (1 "DXY" 단위 = 지수값 USD). get_rate("DXY","USD",..) 로 조회하면
  해당 시점 PIT 지수값을 얻는다 — 단순 시계열 저장 용도이며 실제 환산 의미는 없다.

off graceful: requests 미설치 / 네트워크 실패 / 응답 이상 시 **예외를 던지지 않고** 빈 결과
(빈 리스트 / 0건 적재)를 반환한다. 호출부는 결과 건수만 보고 분기하면 된다.

기존 함수 변경 없음 — 신규 모듈. scripts/collect_macro.py 의 Yahoo 패턴(심볼·헤더·chart API)을
재사용하되, 일봉 타임스탬프를 보존해 rate_date 를 정확히 매핑한다.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from core.data.fx import FxStore

# Yahoo Finance chart API (무료, 키 불필요) — collect_macro.py 와 동일 엔드포인트
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}
TIMEOUT = 15

# 수집 대상: Yahoo 심볼 → (FxStore base, quote). DXY 는 합성쌍 DXY/USD.
MACRO_PAIRS = {
    "DX-Y.NYB": ("DXY", "USD"),  # 달러 인덱스 (지수, 합성쌍으로 시계열 저장)
    "KRW=X": ("USD", "KRW"),     # 원/달러 환율 (1 USD = N KRW)
}


def _ts_to_date(ts: int) -> date:
    """Yahoo epoch(UTC 초) → 거래일(date). 일봉 기준 UTC 날짜로 매핑."""
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).date()


def fetch_daily(symbol: str, range_: str = "1mo", interval: str = "1d") -> list[tuple[date, float]]:
    """Yahoo Finance 에서 일봉 (거래일, 종가) 리스트를 끌어온다.

    off graceful: requests 미설치 / HTTP 오류 / 파싱 실패 시 빈 리스트. 예외 없음.
    None 종가(휴장 등)는 제외. 거래일 오름차순.
    """
    try:
        import requests  # 지연 import — 미설치여도 모듈 import 자체는 성공
    except Exception:  # C2: source_missing 라벨 — 동작 동일([] 반환), silent 제거
        import logging as _log
        _log.getLogger(__name__).warning(
            "fetch_daily source_missing: requests not installed [label=source_missing] symbol=%r",
            symbol,
        )
        return []

    try:
        resp = requests.get(
            YAHOO_CHART.format(symbol=symbol),
            params={"range": range_, "interval": interval, "includePrePost": "false"},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        result = (data.get("chart") or {}).get("result") or []
        if not result:
            return []
        node = result[0]
        timestamps = node.get("timestamp") or []
        quote = ((node.get("indicators") or {}).get("quote") or [{}])[0]
        closes = quote.get("close") or []
    except Exception as _exc:  # C2: data_empty 라벨 — 동작 동일([] 반환), silent 제거
        import logging as _log
        _log.getLogger(__name__).warning(
            "fetch_daily data_empty: Yahoo parse failed [label=data_empty] symbol=%r exc=%r",
            symbol, _exc,
        )
        return []

    out: list[tuple[date, float]] = []
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        try:
            c = float(close)
        except (TypeError, ValueError):
            continue
        if c <= 0 or c != c:  # 0 이하 또는 NaN 제외 (rate 양수 제약)
            continue
        out.append((_ts_to_date(ts), c))
    out.sort(key=lambda t: t[0])
    return out


def collect_into(
    store: FxStore,
    *,
    pairs: Optional[dict[str, tuple[str, str]]] = None,
    range_: str = "1mo",
    _fetcher=fetch_daily,
) -> dict[str, int]:
    """DXY · USDKRW 일봉을 FxStore 에 PIT(bitemporal) 적재. 적재 건수 dict 반환.

    각 일봉: rate_date = knowable_from = 거래일 (장 마감 후 종가 확정 → 그날부터 가시).
    이로써 as_of < rate_date 의사결정에서는 미가시 → lookahead 차단.

    off graceful: fetch 가 빈 리스트면 0건. 예외를 전파하지 않는다.
    ``_fetcher`` 는 테스트 주입용 (기본 = 실 Yahoo fetch).
    """
    pairs = pairs or MACRO_PAIRS
    counts: dict[str, int] = {}
    for symbol, (base, quote) in pairs.items():
        n = 0
        try:
            series = _fetcher(symbol, range_=range_)
        except Exception:
            series = []
        for rate_date, rate in series:
            try:
                store.register(base, quote, rate_date, rate, knowable_from=rate_date)
                n += 1
            except Exception:
                # 개별 row 실패(예: 비양수 rate)는 건너뛰되 전체는 계속
                continue
        counts[symbol] = n
    return counts


def collect_macro_fx(
    *, pairs: Optional[dict[str, tuple[str, str]]] = None, range_: str = "1mo"
) -> tuple[FxStore, dict[str, int]]:
    """새 FxStore 를 만들어 DXY · USDKRW 를 적재하고 (store, 건수) 반환. off graceful."""
    store = FxStore()
    counts = collect_into(store, pairs=pairs, range_=range_)
    return store, counts


if __name__ == "__main__":
    # --- self-test: mock fetcher 로 FxStore PIT 적재·조회 왕복 검증 (네트워크 불필요) ---

    def _mock_fetcher(symbol: str, range_: str = "1mo") -> list[tuple[date, float]]:
        if symbol == "KRW=X":
            return [
                (date(2024, 6, 3), 1380.0),   # 월
                (date(2024, 6, 4), 1385.0),   # 화
                (date(2024, 6, 7), 1390.0),   # 금
            ]
        if symbol == "DX-Y.NYB":
            return [
                (date(2024, 6, 3), 104.1),
                (date(2024, 6, 4), 104.3),
            ]
        return []

    store = FxStore()
    counts = collect_into(store, _fetcher=_mock_fetcher)

    # 1) 적재 건수 확인
    assert counts == {"DX-Y.NYB": 2, "KRW=X": 3}, counts
    print(f"1) 적재 건수: {counts} OK")

    # 2) USDKRW 직접쌍 왕복 — as_of 충분히 미래
    assert store.get_rate("USD", "KRW", "2024-06-04", "2024-06-30") == 1385.0
    print("2) USD/KRW 06-04 = 1385.0 (왕복 조회) OK")

    # 3) 주말 fill-forward — 06-08(토) 가치 = 직전 06-07(금) 환율
    assert store.get_rate("USD", "KRW", "2024-06-08", "2024-06-30") == 1390.0
    print("3) 주말 fill-forward 06-08(토) = 06-07(금) 1390.0 OK")

    # 4) PIT lookahead 차단 — rate_date == knowable_from 이므로
    #    as_of(06-03) 시점엔 06-04 종가 미가시 → 06-03 fill-forward(1380)
    assert store.get_rate("USD", "KRW", "2024-06-07", "2024-06-03") == 1380.0, "lookahead 차단"
    #    as_of(06-04) 에는 06-04 종가 가시(1385)
    assert store.get_rate("USD", "KRW", "2024-06-07", "2024-06-04") == 1385.0
    print("4) PIT lookahead 차단: as_of 06-03 엔 06-04 종가 미가시(1380)/06-04 엔 가시(1385) OK")

    # 5) DXY 합성쌍 시계열 조회
    assert store.get_rate("DXY", "USD", "2024-06-04", "2024-06-30") == 104.3
    print("5) DXY/USD 06-04 = 104.3 (합성쌍 시계열) OK")

    # 6) off graceful — fetcher 가 빈 리스트(네트워크/라이브러리 부재 모사)면 0건, 예외 없음
    empty_store = FxStore()
    empty_counts = collect_into(empty_store, _fetcher=lambda s, range_="1mo": [])
    assert empty_counts == {"DX-Y.NYB": 0, "KRW=X": 0}, empty_counts
    assert empty_store.get_rate("USD", "KRW", "2024-06-04", "2024-06-30") is None
    print("6) off graceful: 빈 fetch → 0건 적재, 조회 None, 예외 없음 OK")

    # 7) fetcher 가 예외를 던져도 collect_into 는 graceful (전파 X)
    def _boom(symbol: str, range_: str = "1mo"):
        raise RuntimeError("network down")

    boom_counts = collect_into(FxStore(), _fetcher=_boom)
    assert boom_counts == {"DX-Y.NYB": 0, "KRW=X": 0}, boom_counts
    print("7) off graceful: fetcher 예외 → 0건, 예외 미전파 OK")

    print("macro_market (DXY·USDKRW → FxStore PIT) self-test PASS")
