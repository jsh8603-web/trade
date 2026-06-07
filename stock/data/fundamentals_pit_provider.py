"""stock/data/fundamentals_pit_provider.py — 종목 PIT 펀더멘털 provider (C5).

WHY: P3 주식 백테스트에서 매 bar 마다 filing_ts≤as_of 를 만족하는 펀더멘털이 필요하다.
     edgar_provider / dart_provider 가 Fundamentals 리스트를 내리면,
     filter_pit_fundamentals (backtest.walk_forward 재사용) 로 PIT 마스킹 후 반환한다.

설계 원칙:
- US: EdgarXbrlProvider (edgar_provider.py 재사용, 무료·무키).
- KR: DartXbrlProvider (dart_provider.py 재사용). DART_API_KEY 없으면
      dart_key_missing 라벨 + FundamentalsUnavailable → ★비중0 금지.
      DART 키 부재 시 호출자는 벤치마크 베타(passive) 로 대체해야 한다.
- filter_pit_fundamentals(filing_ts≤as_of) 재사용 의무 (backtest.walk_forward).
- graceful: 네트워크·키 부재 시 FundamentalsResult(available=False, label=...) 반환.
  예외 전파 X. silent default 금지(라벨 로깅 필수).
- off byte-identical: 기존 production import 경로 미접촉.

FundamentalsResult (본 모듈):
  available: bool          — True=펀더멘털 있음 / False=unavailable
  label: str               — "ok" | "dart_key_missing" | "source_missing" | "pit_empty"
  filings: list[Fundamentals]  — PIT 통과 공시 목록 (available=False 이면 빈 리스트)
  latest: Fundamentals|None    — PIT 통과 중 가장 최신 공시 (없으면 None)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from stock.contracts import Fundamentals

logger = logging.getLogger("stock.data.fundamentals_pit_provider")


# ---------------------------------------------------------------------------
# 결과 계약
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FundamentalsResult:
    """get_fundamentals_pit 반환 계약.

    available=False 시 filings=[] / latest=None.
    label 은 호출자가 routing 에 사용한다:
      - "ok"               : PIT 통과 공시 있음
      - "pit_empty"        : 공시 있었으나 filing_ts>as_of (전부 미래 — 너무 이름)
      - "dart_key_missing" : DART_API_KEY 없음 → 밸류 unavailable, 비중0 금지
      - "source_missing"   : 네트워크·파싱 오류 등 데이터 없음
    """
    available: bool
    label: str
    filings: List[Fundamentals] = field(default_factory=list)
    latest: Optional[Fundamentals] = None


# ---------------------------------------------------------------------------
# PIT 마스킹 재사용
# ---------------------------------------------------------------------------

def _pit_filter(filings: list, as_of: datetime) -> list:
    """backtest.walk_forward.filter_pit_fundamentals 재사용."""
    from backtest.walk_forward import filter_pit_fundamentals
    return filter_pit_fundamentals(filings, as_of)


# ---------------------------------------------------------------------------
# 핵심 함수
# ---------------------------------------------------------------------------

def get_fundamentals_pit(
    ticker: str,
    as_of: datetime,
    region: str,
    *,
    edgar_provider=None,
    dart_provider=None,
    limit: int = 60,  # ★PD: 과거 백테스트 as_of 커버(최근 12=3년만→pit_empty). 60=15년 분기.
) -> FundamentalsResult:
    """as_of 기준 PIT 펀더멘털 반환.

    Parameters
    ----------
    ticker   : 종목 코드 (KR=6자리 / US=심볼)
    as_of    : 의사결정 시점 (filing_ts≤as_of 로 마스킹)
    region   : "KR" | "US"
    edgar_provider : EdgarXbrlProvider 인스턴스 주입 (None 이면 기본)
    dart_provider  : DartXbrlProvider 인스턴스 주입 (None 이면 기본)
    limit    : fetch 공시 최대 건수

    Returns
    -------
    FundamentalsResult
      - available=True  : PIT 통과 공시 있음
      - available=False : label 로 사유 명시 (dart_key_missing/source_missing/pit_empty)
    """
    region = region.upper()

    if region == "US":
        return _get_us(ticker, as_of, limit=limit, provider=edgar_provider)
    elif region == "KR":
        return _get_kr(ticker, as_of, limit=limit, provider=dart_provider)
    else:
        logger.warning(
            "알 수 없는 region %s ticker=%s [source_missing]", region, ticker
        )
        return FundamentalsResult(available=False, label="source_missing")


# ---------------------------------------------------------------------------
# US — EdgarXbrlProvider
# ---------------------------------------------------------------------------

def _get_us(
    ticker: str,
    as_of: datetime,
    *,
    limit: int,
    provider=None,
) -> FundamentalsResult:
    try:
        if provider is None:
            from stock.data.edgar_provider import EdgarXbrlProvider
            provider = EdgarXbrlProvider()

        raw: list = list(provider.fetch_filings(ticker, limit=limit))
    except Exception as exc:
        logger.warning(
            "EDGAR fetch 실패 %s: %s [source_missing]", ticker, exc
        )
        return FundamentalsResult(available=False, label="source_missing")

    if not raw:
        logger.warning("EDGAR 공시 없음 %s [source_missing]", ticker)
        return FundamentalsResult(available=False, label="source_missing")

    # PIT 마스킹
    pit = _pit_filter(raw, as_of)
    if not pit:
        logger.warning(
            "EDGAR PIT 통과 공시 없음 %s as_of=%s (전부 미래) [pit_empty]",
            ticker, as_of.date(),
        )
        return FundamentalsResult(available=False, label="pit_empty")

    pit_sorted = sorted(pit, key=lambda f: f.filing_timestamp)
    return FundamentalsResult(
        available=True,
        label="ok",
        filings=pit_sorted,
        latest=pit_sorted[-1],
    )


# ---------------------------------------------------------------------------
# KR — DartXbrlProvider (DART_API_KEY graceful)
# ---------------------------------------------------------------------------

def _get_kr(
    ticker: str,
    as_of: datetime,
    *,
    limit: int,
    provider=None,
) -> FundamentalsResult:
    # DART_API_KEY 확인
    api_key = os.environ.get("DART_API_KEY", "")
    if not api_key:
        logger.warning(
            "DART_API_KEY 없음 ticker=%s — 밸류 unavailable [dart_key_missing]. "
            "호출자는 벤치마크 베타(passive)로 대체해야 함 (비중0 금지).",
            ticker,
        )
        return FundamentalsResult(available=False, label="dart_key_missing")

    try:
        if provider is None:
            from stock.data.dart_provider import DartXbrlProvider
            provider = DartXbrlProvider(api_key=api_key)

        raw: list = list(provider.fetch_filings(ticker, limit=limit))
    except Exception as exc:
        logger.warning(
            "DART fetch 실패 %s: %s [source_missing]", ticker, exc
        )
        return FundamentalsResult(available=False, label="source_missing")

    if not raw:
        logger.warning("DART 공시 없음 %s [source_missing]", ticker)
        return FundamentalsResult(available=False, label="source_missing")

    # PIT 마스킹 (filter_pit_fundamentals 재사용)
    pit = _pit_filter(raw, as_of)
    if not pit:
        logger.warning(
            "DART PIT 통과 공시 없음 %s as_of=%s (전부 미래) [pit_empty]",
            ticker, as_of.date(),
        )
        return FundamentalsResult(available=False, label="pit_empty")

    pit_sorted = sorted(pit, key=lambda f: f.filing_timestamp)
    return FundamentalsResult(
        available=True,
        label="ok",
        filings=pit_sorted,
        latest=pit_sorted[-1],
    )


# ---------------------------------------------------------------------------
# FundamentalsPitProvider 클래스 (공유 provider 주입 편의)
# ---------------------------------------------------------------------------

class FundamentalsPitProvider:
    """get_fundamentals_pit 의 stateful wrapper.

    edgar_provider / dart_provider 를 한 번 생성·공유해 백테스트 루프 호출 최적화.
    """

    def __init__(
        self,
        edgar_provider=None,
        dart_provider=None,
    ):
        self._edgar = edgar_provider
        self._dart = dart_provider

    def get_fundamentals_pit(
        self,
        ticker: str,
        as_of: datetime,
        region: str,
        limit: int = 60,  # ★PD: 과거 백테스트 커버(모듈 함수와 동일). 12=최근 3년만→pit_empty.
    ) -> FundamentalsResult:
        return get_fundamentals_pit(
            ticker,
            as_of,
            region,
            edgar_provider=self._edgar,
            dart_provider=self._dart,
            limit=limit,
        )


# ---------------------------------------------------------------------------
# self-test (graceful — 네트워크 불요, DART 키 부재 경로 + fixture)
# ---------------------------------------------------------------------------

def _self_test() -> None:
    import os
    from datetime import datetime
    from stock.contracts import Fundamentals, FilingSource

    # 1. unknown region → source_missing
    r = get_fundamentals_pit("TEST", datetime(2024, 1, 1), "JP")
    assert not r.available
    assert r.label == "source_missing"

    # 2. DART 키 없음 → dart_key_missing (비중0 금지 라벨)
    orig = os.environ.pop("DART_API_KEY", None)
    try:
        r_kr = get_fundamentals_pit("005930", datetime(2024, 1, 1), "KR")
        assert not r_kr.available
        assert r_kr.label == "dart_key_missing", f"label={r_kr.label}"
    finally:
        if orig is not None:
            os.environ["DART_API_KEY"] = orig

    # 3. US EDGAR — stub provider (네트워크 없음)
    def _stub_filings(ticker, limit=8):
        f1 = Fundamentals(
            ticker=ticker,
            fiscal_period="2023FY",
            filing_timestamp=datetime(2024, 2, 15),  # as_of 이전
            source=FilingSource.EDGAR_XBRL,
            revenue=100_000_000,
        )
        f2 = Fundamentals(
            ticker=ticker,
            fiscal_period="2024Q1",
            filing_timestamp=datetime(2024, 5, 10),  # as_of 이후 → 마스킹
            source=FilingSource.EDGAR_XBRL,
            revenue=110_000_000,
        )
        return [f1, f2]

    class _StubEdgar:
        def fetch_filings(self, ticker, limit=8):
            return _stub_filings(ticker, limit)

    r_us = get_fundamentals_pit(
        "AAPL",
        datetime(2024, 4, 1),  # f2 filing_ts(2024-05-10) 이후만 마스킹
        "US",
        edgar_provider=_StubEdgar(),
    )
    assert r_us.available, f"US available=False label={r_us.label}"
    assert len(r_us.filings) == 1, f"filings={len(r_us.filings)}"  # f1만 통과
    assert r_us.latest.fiscal_period == "2023FY"

    # 4. PIT 전부 마스킹 → pit_empty
    r_empty = get_fundamentals_pit(
        "AAPL",
        datetime(2023, 1, 1),  # f1 filing_ts(2024-02-15)도 미래
        "US",
        edgar_provider=_StubEdgar(),
    )
    assert not r_empty.available
    assert r_empty.label == "pit_empty"

    print("fundamentals_pit_provider self-test PASSED")


if __name__ == "__main__":
    _self_test()
