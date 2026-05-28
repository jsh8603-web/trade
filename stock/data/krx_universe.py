"""stock/data/krx_universe.py — FDR/pykrx 실연결 KRX 유니버스·상태 provider (SO-1/P4).

WHY: admission.check_admission 이 KrxStatusSnapshot 을 요구하지만 Phase3까지는
     수동 stub 주입이었다(N-P3-1 이연). 본 모듈이 실 FDR/pykrx 호출로 그 gap 을 닫는다.

주요 설계:
- KrxStatusProvider.get_status_snapshot(ticker, as_of) → KrxStatusSnapshot (실데이터)
  · FDR KrxAdministrative = 관리종목 현재 목록 (비PIT, KRAX kind.krx.co.kr)
  · FDR KrxDelisting      = 상폐 종목 (DelistingDate 기준 PIT)
  · pykrx get_market_ohlcv → 거래정지 여부 (당일 거래량 0 + 가격 동결)
- KrxUniverseProvider.get_universe(as_of, market) → List[str] (ticker)
  · FDR StockListing("KRX-MARCAP") 경유
- 일별 스냅샷 적재: jsonl (data/krx_snapshots.jsonl) — in-memory PIT 재구성용
- credential 불요 (FDR/pykrx 무료 라이브)
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("stock.data.krx_universe")

# ---------------------------------------------------------------------------
# 캐시/스냅샷 경로 (OPEN ZONE — in-memory/jsonl 우선)
# ---------------------------------------------------------------------------
_SNAP_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "krx_snapshots.jsonl"


# ---------------------------------------------------------------------------
# lazy import helpers (FDR/pykrx 없으면 ImportError 조기 감지)
# ---------------------------------------------------------------------------

def _fdr():
    import FinanceDataReader as fdr  # noqa: F401
    return fdr


def _pykrx_stock():
    from pykrx import stock as pk  # noqa: F401
    return pk


# ---------------------------------------------------------------------------
# 내부: FDR 관리종목·상폐 raw 조회 (캐시 1시간)
# ---------------------------------------------------------------------------

_admin_cache: Optional[object] = None      # pd.DataFrame
_admin_cache_ts: float = 0.0
_ADMIN_TTL = 3600.0  # 1h
_cache_lock = threading.Lock()  # _admin_cache/_delist_cache 동시 read-check-write race 방지


def _fetch_administrative() -> "pd.DataFrame":
    """FDR KrxAdministrative.read() — 관리종목 현재 목록.

    비PIT(현 시점 스냅샷)이므로 일별 스냅샷 적재로 PIT 재구성한다.
    """
    global _admin_cache, _admin_cache_ts
    with _cache_lock:
        now = time.monotonic()
        if _admin_cache is not None and (now - _admin_cache_ts) < _ADMIN_TTL:
            return _admin_cache  # type: ignore[return-value]
        from FinanceDataReader.krx.listing import KrxAdministrative
        df = KrxAdministrative("").read()
        _admin_cache = df
        _admin_cache_ts = time.monotonic()
        return df


_delist_cache: Optional[object] = None
_delist_cache_ts: float = 0.0
_DELIST_TTL = 3600.0


def _fetch_delistings(start: datetime, end: datetime) -> "pd.DataFrame":
    """FDR KrxDelisting — 상폐 종목 목록 (DelistingDate 컬럼 PIT)."""
    global _delist_cache, _delist_cache_ts
    with _cache_lock:
        now = time.monotonic()
        if _delist_cache is not None and (now - _delist_cache_ts) < _DELIST_TTL:
            return _delist_cache  # type: ignore[return-value]
        import FinanceDataReader as fdr
        df = fdr.StockListing("KRX-DELISTING")
        _delist_cache = df
        _delist_cache_ts = time.monotonic()
        return df


# ---------------------------------------------------------------------------
# 일별 스냅샷 적재 (KrxAdministrative 비PIT → jsonl PIT 재구성)
# ---------------------------------------------------------------------------

def _persist_snapshot(as_of_date: date, ticker: str, snapshot: dict) -> None:
    """관리종목 스냅샷을 jsonl 에 append (as_of + ticker + flags)."""
    try:
        _SNAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {"as_of": as_of_date.isoformat(), "ticker": ticker, **snapshot}
        with open(_SNAP_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("스냅샷 적재 실패: %s", exc)


def _load_snapshot(
    as_of_date: date,
    ticker: str,
    snap_path: Optional[Path] = None,
) -> Optional[dict]:
    """jsonl 에서 가장 최신(<=as_of) 스냅샷 로드 — PIT 재구성."""
    path = snap_path or _SNAP_PATH
    if not path.exists():
        return None
    best: Optional[dict] = None
    best_as_of = ""
    target = as_of_date.isoformat()
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("ticker") != ticker:
                    continue
                rec_as_of = rec.get("as_of")
                # as_of 누락(빈 문자열=사전순 최소→오선택) / 미래 레코드 제외, 최신(<=target) 채택
                if not rec_as_of or rec_as_of > target:
                    continue
                if rec_as_of >= best_as_of:
                    best = rec
                    best_as_of = rec_as_of
    except Exception as exc:
        logger.warning("스냅샷 로드 실패: %s", exc)
    return best


# ---------------------------------------------------------------------------
# 핵심: KrxStatusProvider
# ---------------------------------------------------------------------------

class KrxStatusProvider:
    """FDR/pykrx 실연결 KRX 상태 provider.

    get_status_snapshot(ticker, as_of) → KrxStatusSnapshot
    - 관리종목: FDR KrxAdministrative (비PIT → 일별 스냅샷으로 PIT 재구성)
    - 상폐: FDR KrxDelisting DelistingDate 기준 PIT
    - 거래정지: pykrx 당일 OHLCV 거래량 0 + 가격 동결 휴리스틱

    네트워크 불가 시: jsonl 캐시 fixture 경계로 fallback, 이연 박제.
    """

    def __init__(self, snap_path: Optional[Path] = None):
        self._snap_path = snap_path or _SNAP_PATH

    def get_status_snapshot(
        self,
        ticker: str,
        as_of: Optional[datetime] = None,
    ) -> "KrxStatusSnapshot":
        """실데이터 → KrxStatusSnapshot.

        as_of: 기준 시각 (None=오늘). 과거 as_of 는 jsonl 스냅샷 fallback.
        """
        from stock.admission import KrxStatusSnapshot  # 기존 계약 미변경

        as_of_date = (as_of.date() if as_of else date.today())
        today = date.today()
        use_live = (as_of_date >= today - timedelta(days=1))

        if use_live:
            return self._live_snapshot(ticker, as_of_date)
        else:
            return self._pit_snapshot(ticker, as_of_date)

    # ------------------------------------------------------------------
    def _live_snapshot(self, ticker: str, as_of_date: date) -> "KrxStatusSnapshot":
        from stock.admission import KrxStatusSnapshot

        is_watchlist = False
        is_invest_warn = False
        is_invest_risk = False
        is_halt = False
        is_delisting_risk = False
        is_qualified_audit = False

        try:
            admin_df = _fetch_administrative()
            # Symbol 컬럼 = 6자리 종목코드
            symbols = set(admin_df["Symbol"].astype(str).str.zfill(6).tolist())
            norm = ticker.zfill(6)
            if norm in symbols:
                is_watchlist = True
                # Reason 필드로 세분화
                rows = admin_df[admin_df["Symbol"].astype(str).str.zfill(6) == norm]
                for _, row in rows.iterrows():
                    reason = str(row.get("Reason", "")).lower()
                    if "투자경고" in reason or "investment warning" in reason.lower():
                        is_invest_warn = True
                        is_watchlist = False
                    elif "투자위험" in reason or "investment risk" in reason.lower():
                        is_invest_risk = True
                        is_watchlist = False
                    elif "거래정지" in reason or "trading halt" in reason.lower():
                        is_halt = True
                        is_watchlist = False
                    elif "상장폐지" in reason or "delisting" in reason.lower():
                        is_delisting_risk = True
                        is_watchlist = False
                    elif "감사" in reason or "audit" in reason.lower():
                        is_qualified_audit = True
                        is_watchlist = False
        except Exception as exc:
            logger.warning("관리종목 조회 실패 — ticker=%s err=%s", ticker, exc)

        # 상폐 PIT 체크
        if not is_halt:
            try:
                delist_df = _fetch_delistings(
                    datetime(2000, 1, 1), datetime.combine(as_of_date, datetime.min.time())
                )
                norm6 = ticker.zfill(6)
                if len(delist_df):
                    delist_col = None
                    for c in ("Symbol", "Code", "ISU_SRT_CD"):
                        if c in delist_df.columns:
                            delist_col = c
                            break
                    if delist_col:
                        delist_syms = set(delist_df[delist_col].astype(str).str.zfill(6).tolist())
                        if norm6 in delist_syms:
                            is_delisting_risk = True
            except Exception as exc:
                logger.warning("상폐 조회 실패 — ticker=%s err=%s", ticker, exc)

        # 거래정지 pykrx 휴리스틱 (당일 거래량 0)
        if not is_halt:
            try:
                pk = _pykrx_stock()
                date_str = as_of_date.strftime("%Y%m%d")
                ohlcv = pk.get_market_ohlcv_by_date(date_str, date_str, ticker)
                if ohlcv is not None and len(ohlcv) > 0:
                    vol = ohlcv["거래량"].iloc[-1] if "거래량" in ohlcv.columns else None
                    if vol is not None and vol == 0:
                        is_halt = True
            except Exception as exc:
                logger.debug("거래량 조회 실패 — ticker=%s err=%s", ticker, exc)

        snap = KrxStatusSnapshot(
            is_watchlist=is_watchlist,
            is_invest_warn=is_invest_warn,
            is_invest_risk=is_invest_risk,
            is_halt=is_halt,
            is_delisting_risk=is_delisting_risk,
            is_qualified_audit=is_qualified_audit,
        )

        # 일별 스냅샷 적재
        _persist_snapshot(as_of_date, ticker, {
            "is_watchlist": snap.is_watchlist,
            "is_invest_warn": snap.is_invest_warn,
            "is_invest_risk": snap.is_invest_risk,
            "is_halt": snap.is_halt,
            "is_delisting_risk": snap.is_delisting_risk,
            "is_qualified_audit": snap.is_qualified_audit,
        })
        return snap

    def _pit_snapshot(self, ticker: str, as_of_date: date) -> "KrxStatusSnapshot":
        """과거 as_of → jsonl 스냅샷 PIT 재구성 (라이브 불필요)."""
        from stock.admission import KrxStatusSnapshot

        rec = _load_snapshot(as_of_date, ticker, snap_path=self._snap_path)
        if rec:
            return KrxStatusSnapshot(
                is_watchlist=rec.get("is_watchlist", False),
                is_invest_warn=rec.get("is_invest_warn", False),
                is_invest_risk=rec.get("is_invest_risk", False),
                is_halt=rec.get("is_halt", False),
                is_delisting_risk=rec.get("is_delisting_risk", False),
                is_qualified_audit=rec.get("is_qualified_audit", False),
            )

        logger.debug("PIT 스냅샷 없음 — ticker=%s as_of=%s, 기본값 반환", ticker, as_of_date)
        return KrxStatusSnapshot()


# ---------------------------------------------------------------------------
# KrxUniverseProvider — 종목 유니버스 조회
# ---------------------------------------------------------------------------

class KrxUniverseProvider:
    """FDR StockListing("KRX-MARCAP") 경유 KRX 전체 유니버스.

    get_universe(as_of, market) → List[str] (6자리 종목코드)
    """

    def get_universe(
        self,
        as_of: Optional[datetime] = None,
        market: str = "KRX-MARCAP",
    ) -> List[str]:
        import FinanceDataReader as fdr
        df = fdr.StockListing(market)
        codes = df["Code"].astype(str).str.zfill(6).tolist()
        return codes

    def get_market_caps(
        self,
        as_of: Optional[datetime] = None,
        market: str = "KRX-MARCAP",
    ) -> Dict[str, float]:
        """종목코드 → 시총 매핑."""
        import FinanceDataReader as fdr
        df = fdr.StockListing(market)
        result: Dict[str, float] = {}
        if "Marcap" in df.columns:
            for _, row in df.iterrows():
                code = str(row["Code"]).zfill(6)
                result[code] = float(row["Marcap"]) if row["Marcap"] else 0.0
        return result
