"""stock/data/edgar_provider.py — EDGAR XBRL PIT 펀더멘털 provider (SO-2/P4).

WHY: FundamentalsProvider 프로토콜(fetch_filings)의 미국 구현체.
     EDGAR companyfacts JSON (SEC XBRL API, 무료·익명) → accession 단위 PIT.
     frames API(연간 최종값) 는 lookahead 위험 있으므로 우회 — companyfacts 직접.

CREDENTIAL 부재: SEC EDGAR API 는 무료·익명 (User-Agent 헤더만 필요).
  → 실 네트워크는 가능하나, 테스트는 fixture 경계 사용 (네트워크 의존 최소화).
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Sequence

from stock.contracts import FilingSource, Fundamentals

logger = logging.getLogger("stock.data.edgar_provider")

# SEC EDGAR companyfacts API — 무료·익명 (User-Agent 필수)
_SEC_BASE = "https://data.sec.gov"
_HEADERS = {
    "User-Agent": "InvestmentSystem contact@example.com",
    "Accept-Encoding": "gzip, deflate",
}

# US-GAAP 계정 → Fundamentals 필드 매핑
_GAAP_MAP: Dict[str, str] = {
    "Revenues": "revenue",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
    "SalesRevenueNet": "revenue",
    "OperatingIncomeLoss": "operating_income",
    "NetIncomeLoss": "net_income",
    "NetCashProvidedByUsedInOperatingActivities": "free_cash_flow",
    "CashAndCashEquivalentsAtCarryingValue": "cash_and_equivalents",
    "LongTermDebt": "total_debt",
    "LiabilitiesAndStockholdersEquity": "total_debt",  # fallback
    "StockholdersEquity": "shareholders_equity",
    # ★PD(2026-06-07): value_stock market_cap 합성 + ev_ebitda/residual_income 메서드 활성용.
    "WeightedAverageNumberOfDilutedSharesOutstanding": "outstanding_shares",
    "DepreciationDepletionAndAmortization": "depreciation_amortization",
    "DepreciationAndAmortization": "depreciation_amortization",  # fallback
    "RetainedEarningsAccumulatedDeficit": None,  # 무시
}

# rate limit: SEC EDGAR ~ 10 req/s
_RATE_LIMIT_DELAY = 0.11


# ★PD 캐시(2026-06-07): 백테스트 매 bar 동적 PIT 조회 시 네트워크 폭주 차단.
#   company_tickers.json 1회(전역) + companyfacts cik별 1회 → 매 bar 메모리 적중.
_TICKERS_CACHE: Optional[dict] = None
_FACTS_CACHE: Dict[str, dict] = {}


def _ticker_to_cik(ticker: str) -> Optional[str]:
    """SEC EDGAR company_tickers.json 에서 ticker → CIK 조회.

    ★URL fix(2026-06-07 smoke): company_tickers.json 은 www.sec.gov/files 에 있다.
      data.sec.gov 는 companyfacts API(_SEC_BASE) 전용 — /files 경로는 404.
    ★캐시: tickers.json 은 전역 1회만 fetch(매 bar 재조회 폭주 차단).
    """
    global _TICKERS_CACHE
    import requests
    ticker_upper = ticker.upper()
    if _TICKERS_CACHE is None:
        url = "https://www.sec.gov/files/company_tickers.json"
        try:
            time.sleep(_RATE_LIMIT_DELAY)
            r = requests.get(url, headers=_HEADERS, timeout=15)
            r.raise_for_status()
            _TICKERS_CACHE = r.json()
        except Exception as exc:
            logger.warning("SEC ticker→CIK 조회 실패 ticker=%s: %s", ticker, exc)
            return None
    for _, v in _TICKERS_CACHE.items():
        if str(v.get("ticker", "")).upper() == ticker_upper:
            return str(v["cik_str"]).zfill(10)
    return None


def _fetch_company_facts(cik: str) -> Optional[dict]:
    """SEC EDGAR companyfacts API — 전체 US-GAAP facts. ★cik별 전역 캐시(매 bar 재fetch 차단)."""
    if cik in _FACTS_CACHE:
        return _FACTS_CACHE[cik]
    import requests
    url = f"{_SEC_BASE}/api/xbrl/companyfacts/CIK{cik}.json"
    try:
        time.sleep(_RATE_LIMIT_DELAY)
        r = requests.get(url, headers=_HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        _FACTS_CACHE[cik] = data
        return data
    except Exception as exc:
        logger.warning("companyfacts 조회 실패 CIK=%s: %s", cik, exc)
    return None


# ---------------------------------------------------------------------------
# EdgarXbrlProvider
# ---------------------------------------------------------------------------

class EdgarXbrlProvider:
    """SEC EDGAR companyfacts → accession 단위 PIT Fundamentals.

    FundamentalsProvider 프로토콜 구현체.

    설계:
    - SEC EDGAR /api/xbrl/companyfacts/CIK{cik}.json 직접 호출 (frames 우회)
    - 각 accession 에 해당하는 filed 날짜를 filing_timestamp 로 사용 (PIT)
    - source = FilingSource.EDGAR_XBRL
    - frames API(연간 최종값, lookahead risk) 는 사용하지 않음
    """

    def __init__(self, ticker_to_cik: Optional[Dict[str, str]] = None):
        self._ticker_to_cik: Dict[str, str] = ticker_to_cik or {}

    # ------------------------------------------------------------------
    # FundamentalsProvider 프로토콜 구현
    # ------------------------------------------------------------------

    def fetch_filings(self, ticker: str, limit: int = 8) -> Sequence[Fundamentals]:
        """accession 단위 EDGAR facts → Fundamentals 목록 (최신순).

        네트워크 없으면 빈 목록 + 경고 — 라이브 이연 박제.
        """
        cik = self._resolve_cik(ticker)
        if not cik:
            logger.warning("EDGAR CIK 미확인 — ticker=%s", ticker)
            return []

        facts = _fetch_company_facts(cik)
        if not facts:
            return []

        return self._facts_to_fundamentals(ticker, facts, limit)

    # ------------------------------------------------------------------
    def _resolve_cik(self, ticker: str) -> Optional[str]:
        if ticker.upper() in self._ticker_to_cik:
            return self._ticker_to_cik[ticker.upper()]
        cik = _ticker_to_cik(ticker)
        if cik:
            self._ticker_to_cik[ticker.upper()] = cik
        return cik

    def _facts_to_fundamentals(
        self, ticker: str, facts: dict, limit: int
    ) -> List[Fundamentals]:
        """companyfacts JSON → accession 단위 Fundamentals 목록."""
        us_gaap = facts.get("facts", {}).get("us-gaap", {})
        if not us_gaap:
            logger.debug("us-gaap facts 없음 ticker=%s", ticker)
            return []

        # accession → {field: value, filed_date} 집계
        accession_data: Dict[str, dict] = {}

        for concept, field in _GAAP_MAP.items():
            if field is None:
                continue
            concept_data = us_gaap.get(concept, {})
            for unit_key, unit_vals in concept_data.get("units", {}).items():
                # shares = 발행주식수 unit(outstanding_shares). USD/KRW = 금액. 그 외 무시.
                if unit_key not in ("USD", "KRW", "shares"):
                    continue
                for entry in unit_vals:
                    form = entry.get("form", "")
                    if form not in ("10-K", "10-Q", "20-F"):
                        continue
                    accn = entry.get("accn", "")
                    filed = entry.get("filed", "")
                    if not accn or not filed:
                        continue
                    if accn not in accession_data:
                        accession_data[accn] = {
                            "filed": filed,
                            "form": form,
                            "fy": entry.get("fy"),
                            "fp": entry.get("fp", ""),
                            # shares unit 이 currency 를 덮어쓰지 않게 금액 unit 만 통화로.
                            "currency": unit_key if unit_key in ("USD", "KRW") else "USD",
                        }
                    # 최신 값 우선 (val이 있는 경우만)
                    if field not in accession_data[accn]:
                        accession_data[accn][field] = entry.get("val")

        # 날짜순 정렬 후 limit
        sorted_accns = sorted(
            accession_data.items(),
            key=lambda x: x[1].get("filed", ""),
            reverse=True,
        )

        results: List[Fundamentals] = []
        for accn, data in sorted_accns[:limit]:
            f = self._accession_to_fundamentals(ticker, accn, data)
            if f:
                results.append(f)

        return results

    def _accession_to_fundamentals(
        self, ticker: str, accn: str, data: dict
    ) -> Optional[Fundamentals]:
        """accession entry → Fundamentals (PIT filing_timestamp = filed 날짜)."""
        try:
            filed_str = data.get("filed", "")
            filing_ts = self._parse_filed(filed_str)
            if not filing_ts:
                return None

            fy = data.get("fy")
            fp = data.get("fp", "")
            fiscal_period = self._make_fiscal_period(fy, fp)

            # ★PD(2026-06-07): ebitda = operating_income + D&A 합성(둘 다 있을 때).
            #   book_value = shareholders_equity(장부가). value_stock ev_ebitda/residual_income 활성용.
            _oi = data.get("operating_income")
            _da = data.get("depreciation_amortization")
            _ebitda = (_oi + _da) if (_oi is not None and _da is not None) else None
            _equity = data.get("shareholders_equity")

            return Fundamentals(
                ticker=ticker,
                fiscal_period=fiscal_period,
                filing_timestamp=filing_ts,
                source=FilingSource.EDGAR_XBRL,
                currency=data.get("currency", "USD"),
                as_reported=True,
                revenue=data.get("revenue"),
                operating_income=data.get("operating_income"),
                net_income=data.get("net_income"),
                free_cash_flow=data.get("free_cash_flow"),
                cash_and_equivalents=data.get("cash_and_equivalents"),
                shareholders_equity=_equity,
                total_debt=data.get("total_debt"),
                outstanding_shares=data.get("outstanding_shares"),
                depreciation_amortization=_da,
                ebitda=_ebitda,
                book_value=_equity,
            )
        except Exception as exc:
            logger.debug("accession 변환 실패 accn=%s: %s", accn, exc)
            return None

    @staticmethod
    def _parse_filed(filed_str: str) -> Optional[datetime]:
        """YYYY-MM-DD → datetime."""
        try:
            return datetime.strptime(filed_str[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _make_fiscal_period(fy, fp: str) -> str:
        if not fy:
            return "UNKNOWN"
        fp_map = {"FY": "FY", "Q1": "Q1", "Q2": "Q2", "Q3": "Q3", "Q4": "Q4", "H1": "H1"}
        suffix = fp_map.get(fp.upper(), fp.upper() or "FY")
        return f"{fy}{suffix}"
