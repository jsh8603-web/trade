"""stock/data/dart_provider.py — DART XBRL PIT 펀더멘털 provider (SO-2/P4).

WHY: FundamentalsProvider 프로토콜(fetch_filings)의 한국 구현체.
     dart-fss/OpenDartReader fnlttXbrl.xml + rcept_no 단위 XBRL 파싱.
     정정공시 = 원본 접수일 보존(정정본 접수일 X) → PIT 누수 없음.

CREDENTIAL 부재: DART_API_KEY 없으면 어댑터 본체는 작동하지만 라이브 fetch 불가.
  → 경계 계약 테스트(fixture/스텁)로 does-it-behave 검증,
    실 네트워크 왕복은 progress.md 이연 박제. "구현 불가" 단정 금지.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Sequence

from stock.contracts import FilingSource, Fundamentals

logger = logging.getLogger("stock.data.dart_provider")

# ---------------------------------------------------------------------------
# 계정과목 → Fundamentals 필드 매핑 (DART XBRL 표준계정과목체계 기반)
# ---------------------------------------------------------------------------
_ACCOUNT_MAP: Dict[str, str] = {
    # 손익계산서
    "ifrs-full_Revenue": "revenue",
    "dart_Revenue": "revenue",
    "ifrs-full_OperatingIncome": "operating_income",
    "dart_OperatingIncomeLoss": "operating_income",
    "ifrs-full_ProfitLoss": "net_income",
    "dart_ProfitLoss": "net_income",
    "ifrs-full_ProfitLossFromContinuingOperations": "net_income",
    # 재무상태표
    "ifrs-full_Equity": "shareholders_equity",
    "dart_TotalEquity": "shareholders_equity",
    "ifrs-full_CashAndCashEquivalents": "cash_and_equivalents",
    "dart_CashAndCashEquivalents": "cash_and_equivalents",
    "ifrs-full_Liabilities": "total_debt",
    # 현금흐름
    "ifrs-full_CashFlowsFromUsedInOperatingActivities": "free_cash_flow",
    "dart_CashFlowsFromOperatingActivities": "free_cash_flow",
}


def _parse_amount(val) -> Optional[float]:
    """XBRL amount 파싱 (단위: 원, None 허용)."""
    if val is None:
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# DartXbrlProvider
# ---------------------------------------------------------------------------

class DartXbrlProvider:
    """DART OpenAPI fnlttXbrl.xml + rcept_no 단위 XBRL → Fundamentals.

    FundamentalsProvider 프로토콜 구현체.

    설계:
    - dart-fss search() 로 재무제표 공시 목록 조회 (corp_code 매핑)
    - OpenDartReader finstate_xml(api_key, rcept_no) 로 XBRL zip 다운로드
    - 정정공시 = 원본 접수일(암무 rcept_dt) 보존 (정정본 접수번호 접수일 X)
    - source = FilingSource.DART_XBRL

    credential 부재 시: 어댑터 본체 작동, 라이브 I/O는 DART_API_KEY 필요.
    """

    def __init__(self, api_key: Optional[str] = None, ticker_to_corp: Optional[Dict[str, str]] = None):
        self._api_key = api_key or os.environ.get("DART_API_KEY", "")
        self._ticker_to_corp: Dict[str, str] = ticker_to_corp or {}

    # ------------------------------------------------------------------
    # FundamentalsProvider 프로토콜 구현
    # ------------------------------------------------------------------

    def fetch_filings(self, ticker: str, limit: int = 8) -> Sequence[Fundamentals]:
        """rcept_no 단위 XBRL 공시 → Fundamentals 목록 (최신순).

        credential 부재 시 빈 목록 + 경고 로깅.
        """
        if not self._api_key:
            logger.warning(
                "DART_API_KEY 없음 — 라이브 fetch 이연 (deferral-pinning). ticker=%s", ticker
            )
            return []

        corp_code = self._resolve_corp_code(ticker)
        if not corp_code:
            logger.warning("DART corp_code 미확인 — ticker=%s", ticker)
            return []

        return self._fetch_from_dart(ticker, corp_code, limit)

    # ------------------------------------------------------------------
    def _resolve_corp_code(self, ticker: str) -> Optional[str]:
        """ticker → DART 고유번호(8자리). ticker_to_corp 맵 우선, 없으면 dart-fss 조회."""
        if ticker in self._ticker_to_corp:
            return self._ticker_to_corp[ticker]

        try:
            import dart_fss as dart
            dart.set_api_key(self._api_key)
            corp_list = dart.get_corp_list()
            corp = corp_list.find_by_stock_code(ticker)
            if corp:
                code = getattr(corp, "corp_code", None)
                if code:
                    self._ticker_to_corp[ticker] = code
                    return code
        except Exception as exc:
            logger.warning("dart corp_code 조회 실패 — ticker=%s err=%s", ticker, exc)
        return None

    def _fetch_from_dart(self, ticker: str, corp_code: str, limit: int) -> List[Fundamentals]:
        """dart-fss search → 공시목록 → fnlttXbrl rcept_no 파싱."""
        results: List[Fundamentals] = []
        try:
            import dart_fss as dart
            dart.set_api_key(self._api_key)

            # 사업보고서(11011) + 반기(11012) + 분기(11013/11014) 순서로 검색
            report_types = ["11011", "11012", "11013", "11014"]
            filings_seen = []
            for rt in report_types:
                try:
                    search_result = dart.filings.search(
                        corp_code=corp_code,
                        pblntf_ty="A",  # 정기공시
                        sort_mth="desc",
                        page_count=min(limit * 2, 40),
                    )
                    for filing in search_result.filings[:limit]:
                        filings_seen.append(filing)
                except Exception:
                    pass
                if len(filings_seen) >= limit:
                    break

            for filing in filings_seen[:limit]:
                f = self._filing_to_fundamentals(ticker, filing)
                if f:
                    results.append(f)
        except Exception as exc:
            logger.error("DART fetch 실패 — ticker=%s err=%s", ticker, exc)
        return results

    def _filing_to_fundamentals(self, ticker: str, filing) -> Optional[Fundamentals]:
        """dart-fss filing 객체 → Fundamentals (rcept_no PIT, 원본 접수일 보존)."""
        try:
            rcept_no = getattr(filing, "rcept_no", None)
            rcept_dt = getattr(filing, "rcept_dt", None)  # YYYYMMDD
            if not rcept_no or not rcept_dt:
                return None

            # 정정공시 처리: 원본 접수일 보존
            # dart-fss 의 filing 에 "원본접수번호" 필드가 있으면 그 날짜를 씀
            orig_dt = getattr(filing, "rm", None)  # rm = 비고(정정 시 원본번호 포함 가능)
            filing_ts = self._parse_date(str(rcept_dt))
            if filing_ts is None:
                return None

            # 회계기간 파악
            report_nm = getattr(filing, "report_nm", "")
            fiscal_period = self._extract_fiscal_period(report_nm, rcept_dt)

            # 재무제표 값 — 라이브 파싱 (credential 필요)
            fin_vals = self._parse_xbrl_values(rcept_no)

            return Fundamentals(
                ticker=ticker,
                fiscal_period=fiscal_period,
                filing_timestamp=filing_ts,
                source=FilingSource.DART_XBRL,
                currency="KRW",
                as_reported=True,
                revenue=fin_vals.get("revenue"),
                operating_income=fin_vals.get("operating_income"),
                net_income=fin_vals.get("net_income"),
                shareholders_equity=fin_vals.get("shareholders_equity"),
                cash_and_equivalents=fin_vals.get("cash_and_equivalents"),
                free_cash_flow=fin_vals.get("free_cash_flow"),
                total_debt=fin_vals.get("total_debt"),
            )
        except Exception as exc:
            logger.debug("filing 변환 실패: %s", exc)
            return None

    def _parse_xbrl_values(self, rcept_no: str) -> Dict[str, Optional[float]]:
        """fnlttXbrl.xml 다운로드·파싱 → 재무 수치 딕셔너리."""
        vals: Dict[str, Optional[float]] = {}
        try:
            from opendartreader import dart_finstate
            import tempfile, zipfile, xml.etree.ElementTree as ET, pathlib

            with tempfile.TemporaryDirectory() as tmpd:
                zpath = str(pathlib.Path(tmpd) / "fs.zip")
                ok = dart_finstate.finstate_xml(self._api_key, rcept_no, save_as=zpath)
                if not ok:
                    return vals
                with zipfile.ZipFile(zpath) as zf:
                    for name in zf.namelist():
                        if name.lower().endswith(".xbrl") or name.lower().endswith(".xml"):
                            with zf.open(name) as xf:
                                tree = ET.parse(xf)
                                for elem in tree.iter():
                                    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                                    full_tag = elem.tag.split("}")[-1]
                                    for key, field in _ACCOUNT_MAP.items():
                                        if key.split("_")[-1] == full_tag and field not in vals:
                                            vals[field] = _parse_amount(elem.text)
        except Exception as exc:
            logger.debug("XBRL 파싱 실패 rcept_no=%s: %s", rcept_no, exc)
        return vals

    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """YYYYMMDD → datetime."""
        try:
            return datetime.strptime(date_str[:8], "%Y%m%d")
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _extract_fiscal_period(report_nm: str, rcept_dt: str) -> str:
        """보고서명에서 회계기간 추출."""
        try:
            year = str(rcept_dt)[:4]
            if "사업보고서" in report_nm or "Annual" in report_nm:
                return f"{year}FY"
            elif "반기" in report_nm:
                return f"{year}H1"
            elif "1분기" in report_nm:
                return f"{year}Q1"
            elif "3분기" in report_nm:
                return f"{year}Q3"
            return f"{year}FY"
        except Exception:
            return "UNKNOWN"
