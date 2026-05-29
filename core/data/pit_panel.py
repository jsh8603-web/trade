"""core/data/pit_panel.py — bitemporal PIT 패널 조립층 (Phase2 T1, WP-T1-B/C).

PANEL-SCHEMA-phase2.md 계약1 구현. 기존 provider 를 **조립**한다(바닥부터 X):
  - DART/EDGAR XBRL → Fundamentals (filing_timestamp, RESTATED 거부)
  - KrxStatusProvider → 상태 플래그 (관리종목/상폐위험, PIT)
  - UniverseManager → survivorship (상폐 포함)
  - filter_pit_fundamentals → filing-lag PIT (재사용, 재구현 X)

PIT 보호 3중 (PANEL-SCHEMA §3):
  ① filing-lag (build-time)   : 관측일 D 의 features 는 filing<=D 펀더멘털만 (filter_pit_fundamentals)
  ② 관측 horizon (query-time) : knowable_from <= as_of (pit_query)
  ③ silent revision (query-time): sys_time append-only, 최신 sys_time 선택 (pit_query)

불변식 ②(rollback=append만): rebuild 시 같은 (firm,date) 의 갱신값은 새 sys_time row 로
append, 옛 row 는 절대 mutate 하지 않는다. AS OF 가 최신 sys_time 을 선택한다.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Sequence

import pandas as pd

from stock.contracts import Fundamentals, FilingSource
from backtest.walk_forward import filter_pit_fundamentals, UniverseManager

logger = logging.getLogger("core.data.pit_panel")

# ---------------------------------------------------------------------------
# 패널 컬럼 스펙 (PANEL-SCHEMA-phase2.md §2)
# ---------------------------------------------------------------------------

# features (Fundamentals 매핑) — 모두 nullable float
FEATURE_COLS: List[str] = [
    "revenue", "operating_income", "net_income", "ebit", "ebitda",
    "free_cash_flow", "depreciation_amortization", "capital_expenditure",
    "interest_expense", "total_debt", "cash_and_equivalents",
    "shareholders_equity", "book_value", "working_capital",
    "outstanding_shares", "earnings_growth", "revenue_growth",
    "book_value_growth", "return_on_invested_capital", "beta",
]
MULTIPLE_COLS: List[str] = ["per", "pbr", "ev_ebitda", "ps"]
STATUS_COLS: List[str] = [
    "is_watchlist", "is_invest_warn", "is_invest_risk",
    "is_halt", "is_delisting_risk", "is_qualified_audit",
]

PANEL_COLUMNS: List[str] = (
    # bitemporal 3축
    ["effective_from", "knowable_from", "sys_time"]
    # 식별/분류
    + ["firm", "date", "sector", "sector_scheme", "sector_valid_from"]
    # features + 메타
    + FEATURE_COLS
    + ["fiscal_period", "filing_source", "currency", "is_pit_clean"]
    # multiple
    + MULTIPLE_COLS + ["multiple_def_version"]
    # survivorship
    + ["delist_flag", "delist_date", "delist_ret"]
    # regime (T1 = NULL, T2 producer)
    + ["regime_id", "regime_model_version"]
    # 상태(KR PIT)
    + STATUS_COLS
)

_TS_COLS = ["effective_from", "knowable_from", "sys_time", "date",
            "sector_valid_from", "delist_date"]
_BOOL_COLS = ["is_pit_clean", "delist_flag"] + STATUS_COLS


# ---------------------------------------------------------------------------
# fiscal period → effective_from (회계기간 말일)
# ---------------------------------------------------------------------------

_Q_END_MONTH = {"Q1": (3, 31), "Q2": (6, 30), "Q3": (9, 30), "Q4": (12, 31)}


def fiscal_period_end(fiscal_period: str) -> Optional[datetime]:
    """'2023Q4'/'2023FY' → 회계기간 말일 datetime. 파싱 실패 시 None."""
    if not fiscal_period or len(fiscal_period) < 6:
        return None
    try:
        year = int(fiscal_period[:4])
    except ValueError:
        return None
    tail = fiscal_period[4:].upper()
    if tail in ("FY", "A"):
        return datetime(year, 12, 31)
    if tail in _Q_END_MONTH:
        m, d = _Q_END_MONTH[tail]
        return datetime(year, m, d)
    return None


# ---------------------------------------------------------------------------
# raw 멀티플 계산 (T2 가 cheapness_z 로 변환 — 여기선 raw 만)
# ---------------------------------------------------------------------------

def _safe_div(num: Optional[float], den: Optional[float]) -> Optional[float]:
    if num is None or den is None:
        return None
    if den == 0 or den != den:  # 0 또는 NaN
        return None
    return num / den


def compute_multiples(f: Fundamentals, market_cap: Optional[float]) -> Dict[str, Optional[float]]:
    """raw 멀티플. 분모 0/None → None (싸다 판정 아님, T2 입력용)."""
    if market_cap is None:
        return {k: None for k in MULTIPLE_COLS}
    ev = market_cap
    if f.total_debt is not None:
        ev += f.total_debt
    if f.cash_and_equivalents is not None:
        ev -= f.cash_and_equivalents
    equity = f.shareholders_equity if f.shareholders_equity else f.book_value
    return {
        "per": _safe_div(market_cap, f.net_income),
        "pbr": _safe_div(market_cap, equity),
        "ev_ebitda": _safe_div(ev, f.ebitda),
        "ps": _safe_div(market_cap, f.revenue),
    }


# ---------------------------------------------------------------------------
# 단일 관측 row 빌드
# ---------------------------------------------------------------------------

def build_record(
    *,
    firm: str,
    date: datetime,
    sys_time: Optional[datetime] = None,
    fundamentals: Fundamentals,
    market_cap: Optional[float],
    sector: Optional[str] = None,
    sector_scheme: Optional[str] = None,
    sector_valid_from: Optional[datetime] = None,
    multiple_def_version: str = "raw_v1",
    delist_flag: bool = False,
    delist_date: Optional[datetime] = None,
    delist_ret: Optional[float] = None,
    status: Optional[Dict[str, bool]] = None,
) -> Dict:
    """(firm, date) 1 관측 → 패널 record dict (PANEL_COLUMNS).

    knowable_from = max(관측일, 사용 펀더멘털 filing_timestamp) — 가격@date 가
    마지막으로 알려진 시점. filing<=date 는 호출자(filter_pit_fundamentals)가 보장.

    sys_time 기본 = knowable_from (그 값이 알려진 즉시 기록 = silent revision 없는 경우).
    ⚠️ build 시각을 sys_time 으로 쓰면 안 된다 — 2026 빌드 패널로 2024 백테스트 조회 시
    sys_time(2026) > as_of(2024) 로 전부 막힌다. silent revision(과거 조용한 정정) 발생
    시에만 호출자가 정정 시점을 명시 sys_time 으로 줘서 새 row append(불변식②).
    """
    eff = fiscal_period_end(fundamentals.fiscal_period) or fundamentals.filing_timestamp
    knowable = max(date, fundamentals.filing_timestamp)
    if sys_time is None:
        sys_time = knowable
    mult = compute_multiples(fundamentals, market_cap)
    status = status or {}

    rec: Dict = {
        "effective_from": eff,
        "knowable_from": knowable,
        "sys_time": sys_time,
        "firm": firm,
        "date": date,
        "sector": sector,
        "sector_scheme": sector_scheme,
        "sector_valid_from": sector_valid_from,
        "fiscal_period": fundamentals.fiscal_period,
        "filing_source": fundamentals.source.value,
        "currency": fundamentals.currency,
        "is_pit_clean": fundamentals.is_pit_clean(),
        "multiple_def_version": multiple_def_version,
        "delist_flag": delist_flag,
        "delist_date": delist_date,
        "delist_ret": delist_ret,
        "regime_id": None,            # T2 producer
        "regime_model_version": None,  # T2 producer
    }
    for c in FEATURE_COLS:
        rec[c] = getattr(fundamentals, c, None)
    for c in MULTIPLE_COLS:
        rec[c] = mult[c]
    for c in STATUS_COLS:
        rec[c] = bool(status.get(c, False))
    return rec


def coerce_panel(records: Sequence[Dict]) -> pd.DataFrame:
    """record dict 목록 → 스키마 정합 typed DataFrame (PANEL_COLUMNS 순서/dtype)."""
    if not records:
        df = pd.DataFrame(columns=PANEL_COLUMNS)
    else:
        df = pd.DataFrame(list(records))
        for c in PANEL_COLUMNS:
            if c not in df.columns:
                df[c] = None
        df = df[PANEL_COLUMNS]
    # dtype 정합
    for c in _TS_COLS:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    for c in FEATURE_COLS + MULTIPLE_COLS + ["delist_ret"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if not df.empty:
        df["regime_id"] = df["regime_id"].astype("Int32")
    return df


# ---------------------------------------------------------------------------
# 조립기 — provider 주입 → 패널
# ---------------------------------------------------------------------------

class RoutingFundamentalsProvider:
    """ticker 형식으로 dart(KR 6자리)/edgar(US) 라우팅하는 FundamentalsProvider.

    .fetch_filings(ticker, limit) 단일 인터페이스로 PanelAssembler 에 주입.
    provider 부재(None, credential 없음)면 빈 목록 → 패널 비게 됨(graceful degrade).
    """

    def __init__(self, dart_provider=None, edgar_provider=None) -> None:
        self._dart = dart_provider
        self._edgar = edgar_provider

    @staticmethod
    def _is_kr(ticker: str) -> bool:
        t = ticker.strip()
        return len(t) == 6 and t.isdigit()

    def fetch_filings(self, ticker: str, limit: int = 8):
        prov = self._dart if self._is_kr(ticker) else self._edgar
        if prov is None:
            return []
        try:
            return prov.fetch_filings(ticker, limit=limit)
        except Exception as exc:  # 라이브 I/O 실패 → graceful
            logger.warning("fetch_filings 실패 ticker=%s: %s", ticker, exc)
            return []


class PanelAssembler:
    """기존 provider 를 주입받아 bitemporal 패널을 조립.

    credential 부재(샌드박스)면 provider 가 빈 결과를 반환하므로 패널도 비게 된다
    — 라이브 데이터 왕복은 go-live(N-P4) 의존. 본 클래스는 조립 로직 + PIT 보호의
    SSOT 이고, 테스트는 fixture provider 로 검증한다.
    """

    def __init__(
        self,
        *,
        fundamentals_adapter,            # FundamentalsProvider (.fetch_filings) — RoutingFundamentalsProvider 권장
        krx_status_provider=None,        # KrxStatusProvider (KR 상태 플래그)
        quote_fn=None,                   # Callable[[firm, date], Optional[market_cap]]
        delisted: Optional[Dict[str, datetime]] = None,  # {ticker: delist_date}
        sector_fn=None,                  # Callable[[firm, date], (sector, scheme, valid_from)]
        multiple_def_version: str = "raw_v1",
    ) -> None:
        self._funds = fundamentals_adapter
        self._krx = krx_status_provider
        self._quote = quote_fn
        self._delisted = delisted or {}
        self._universe = UniverseManager(set(self._delisted.keys()))
        self._sector_fn = sector_fn
        self._mdv = multiple_def_version

    def _latest_pit_fundamental(
        self, firm: str, observation_date: datetime
    ) -> Optional[Fundamentals]:
        """관측일 기준 filing-lag PIT 최신 펀더멘털 (filter_pit_fundamentals 재사용)."""
        raw = self._funds.fetch_filings(firm, limit=12)
        pit = filter_pit_fundamentals(raw, observation_date)  # filing<=date AND pit_clean
        if not pit:
            return None
        # 가장 최근 filing
        return max(pit, key=lambda f: f.filing_timestamp)

    def _status(self, firm: str, observation_date: datetime) -> Dict[str, bool]:
        if self._krx is None:
            return {}
        try:
            snap = self._krx.get_status_snapshot(firm, observation_date)
            return {c: bool(getattr(snap, c, False)) for c in STATUS_COLS}
        except Exception as exc:
            logger.warning("KRX status 조회 실패 firm=%s: %s", firm, exc)
            return {}

    def _sector(self, firm: str, observation_date: datetime):
        if self._sector_fn is None:
            return (None, None, None)
        try:
            return self._sector_fn(firm, observation_date)
        except Exception:
            return (None, None, None)

    def assemble(
        self,
        firms: Sequence[str],
        dates: Sequence[datetime],
        *,
        sys_time: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """(firms × dates) 관측 그리드 → 패널 DataFrame.

        sys_time 미지정 시 각 record 의 knowable_from(알게된 시점). 배치 override 가
        필요한 silent-revision 재적재 시에만 sys_time 명시. survivorship: 상폐 종목도
        그 관측일에 살아있었으면 포함(UniverseManager + 상폐일 date-aware 필터).
        """
        records: List[Dict] = []
        # 상폐 포함 backtest pool (H5, UniverseManager 재사용 — date-agnostic 원칙)
        backtest_pool = self._universe.get_backtest_universe(list(firms))
        for d in dates:
            for firm in backtest_pool:
                delist_date = self._delisted.get(firm)
                # survivorship-free + date-aware: 상폐일 이후 관측일은 거래불가 → 제외
                if delist_date is not None and delist_date <= d:
                    continue
                f = self._latest_pit_fundamental(firm, d)
                if f is None:
                    continue
                mcap = self._quote(firm, d) if self._quote else None
                sector, scheme, valid_from = self._sector(firm, d)
                rec = build_record(
                    firm=firm, date=d, sys_time=sys_time,
                    fundamentals=f, market_cap=mcap,
                    sector=sector, sector_scheme=scheme, sector_valid_from=valid_from,
                    multiple_def_version=self._mdv,
                    delist_flag=delist_date is not None,
                    delist_date=delist_date,
                    status=self._status(firm, d),
                )
                records.append(rec)
        return coerce_panel(records)
