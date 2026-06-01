"""stock/data/krx_flows.py — KRX 업종분류(WICS/섹터)·외국인 순매수 flow provider.

WHY: krx_universe.py 가 유니버스/상태(관리·상폐·정지)를 채웠지만, T2 구조모델이
     요구하는 (a) 종목→업종(섹터) 매핑 (b) 외국인 순매수 flow 가 비어 있었다.
     본 모듈이 그 gap 을 FDR/pykrx 실호출로 닫는다 (krx_universe 동일 스타일).

주요 설계 (krx_universe.py 패턴 정합):
- KrxSectorProvider.get_sector_map(as_of, market) → Dict[ticker, sector]
  · pykrx get_market_sector_classifications(date, market) 우선
  · 실패 시 FDR StockListing 의 Sector 컬럼 fallback
- KrxForeignFlowProvider.get_foreign_net_purchase(ticker, start, end) → List[FlowRecord]
  · pykrx get_market_trading_value_by_investor → '외국인' 순매수
  · get_foreign_net_by_market(date, market) → 시장 전체 종목별 순매수 (top flow)
- 일별 스냅샷 적재: jsonl (data/krx_flow_snapshots.jsonl) — knowable_from 기록 PIT
  · 비PIT 라이브(get_market_sector_classifications=현재 분류) → 스냅샷 적재로 PIT 재구성
  · 미래 as_of → lookahead 차단 (빈 결과)
- off graceful: pykrx/FDR 미설치·네트워크 차단 → 빈 결과 (예외 던지지 않음)
- credential 불요 (FDR/pykrx 무료 라이브; KRX_ID/PW 는 일부 통계 한정, 본 모듈 미사용)
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("stock.data.krx_flows")

# ---------------------------------------------------------------------------
# 스냅샷 경로 (krx_universe._SNAP_PATH 패턴 정합, 별 파일로 분리)
# ---------------------------------------------------------------------------
_SECTOR_SNAP_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "krx_sector_snapshots.jsonl"
_FLOW_SNAP_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "krx_flow_snapshots.jsonl"


# ---------------------------------------------------------------------------
# lazy import helpers (krx_universe 동일 — 미설치 시 graceful)
# ---------------------------------------------------------------------------

def _pykrx_stock():
    from pykrx import stock as pk  # noqa: F401
    return pk


def _fdr():
    import FinanceDataReader as fdr  # noqa: F401
    return fdr


# ---------------------------------------------------------------------------
# 캐시 (krx_universe._admin_cache TTL 패턴 정합)
# ---------------------------------------------------------------------------
_cache_lock = threading.Lock()
_sector_cache: Dict[str, object] = {}        # market+date → DataFrame
_sector_cache_ts: Dict[str, float] = {}
_SECTOR_TTL = 3600.0  # 1h


# ---------------------------------------------------------------------------
# 일별 스냅샷 적재 (krx_universe._persist_snapshot / _load_snapshot 패턴 정합)
# ---------------------------------------------------------------------------

def _persist_jsonl(path: Path, entry: dict) -> None:
    """jsonl append (knowable_from 포함). 실패해도 예외 전파 X."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("스냅샷 적재 실패 (%s): %s", path.name, exc)


def _load_latest_jsonl(
    path: Path,
    as_of_date: date,
    match: Dict[str, str],
) -> Optional[dict]:
    """jsonl 에서 match 조건 + as_of <= target 인 최신 레코드 (PIT 재구성)."""
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
                if any(str(rec.get(k)) != str(v) for k, v in match.items()):
                    continue
                rec_as_of = rec.get("as_of")
                # as_of 누락 / 미래 레코드 제외, 최신(<=target) 채택 (krx_universe 동일)
                if not rec_as_of or rec_as_of > target:
                    continue
                if rec_as_of >= best_as_of:
                    best = rec
                    best_as_of = rec_as_of
    except Exception as exc:
        logger.warning("스냅샷 로드 실패 (%s): %s", path.name, exc)
    return best


# ===========================================================================
# 1) KrxSectorProvider — WICS/업종 분류 (종목 → 섹터)
# ===========================================================================

class KrxSectorProvider:
    """KOSPI/KOSDAQ 종목 → 업종(섹터) 매핑 provider.

    get_sector_map(as_of, market) → Dict[6자리 ticker, sector 명]

    1차: pykrx get_market_sector_classifications(date, market) — KRX 표준 업종.
    2차(fallback): FDR StockListing 의 Sector 컬럼.

    비PIT(현재 분류 라이브)이므로 일별 스냅샷(data/krx_sector_snapshots.jsonl)
    적재로 PIT 재구성. 과거 as_of 는 스냅샷 fallback, 미래 as_of 는 lookahead 차단.
    """

    def __init__(self, snap_path: Optional[Path] = None):
        self._snap_path = snap_path or _SECTOR_SNAP_PATH

    # ------------------------------------------------------------------
    def get_sector_map(
        self,
        as_of: Optional[datetime] = None,
        market: str = "KOSPI",
    ) -> Dict[str, str]:
        """as_of 시점 종목→섹터 매핑. off/네트워크 차단 시 빈 dict."""
        as_of_date = (as_of.date() if as_of else date.today())
        today = date.today()

        # 미래 as_of → lookahead 차단
        if as_of_date > today:
            logger.warning("미래 as_of 거부(lookahead) - market=%s as_of=%s", market, as_of_date)
            return {}

        use_live = (as_of_date >= today - timedelta(days=1))
        if use_live:
            live = self._live_sector_map(as_of_date, market)
            if live:
                return live
        # 과거 as_of 또는 라이브 실패 → 스냅샷 PIT 재구성
        return self._pit_sector_map(as_of_date, market)

    # ------------------------------------------------------------------
    def _live_sector_map(self, as_of_date: date, market: str) -> Dict[str, str]:
        out: Dict[str, str] = {}
        date_str = as_of_date.strftime("%Y%m%d")
        cache_key = f"{market}:{date_str}"

        # pykrx 1차
        try:
            with _cache_lock:
                now = time.monotonic()
                cached = _sector_cache.get(cache_key)
                if cached is not None and (now - _sector_cache_ts.get(cache_key, 0.0)) < _SECTOR_TTL:
                    df = cached
                else:
                    pk = _pykrx_stock()
                    df = pk.get_market_sector_classifications(date_str, market)
                    _sector_cache[cache_key] = df
                    _sector_cache_ts[cache_key] = time.monotonic()
            if df is not None and len(df) > 0:
                # index = 종목코드, '업종명' 컬럼
                sector_col = None
                for c in ("업종명", "업종", "Sector", "지수명"):
                    if c in df.columns:
                        sector_col = c
                        break
                for idx, row in df.iterrows():
                    code = str(idx).zfill(6)
                    sector = str(row[sector_col]) if sector_col else ""
                    if sector:
                        out[code] = sector
        except Exception as exc:
            logger.warning("pykrx 업종 분류 실패 - market=%s err=%s", market, exc)

        # FDR fallback
        if not out:
            try:
                fdr = _fdr()
                fdr_market = "KOSPI" if market.upper().startswith("KOSPI") else "KOSDAQ"
                df = fdr.StockListing(fdr_market)
                if df is not None and "Sector" in df.columns:
                    code_col = "Code" if "Code" in df.columns else ("Symbol" if "Symbol" in df.columns else None)
                    if code_col:
                        for _, row in df.iterrows():
                            code = str(row[code_col]).zfill(6)
                            sector = str(row.get("Sector", "") or "")
                            if sector and sector.lower() != "nan":
                                out[code] = sector
            except Exception as exc:
                logger.warning("FDR Sector fallback 실패 - market=%s err=%s", market, exc)

        # 스냅샷 적재 (PIT 재구성용, knowable_from = 수집 시점)
        if out:
            knowable = datetime.now().isoformat()
            for code, sector in out.items():
                _persist_jsonl(self._snap_path, {
                    "as_of": as_of_date.isoformat(),
                    "market": market,
                    "ticker": code,
                    "sector": sector,
                    "knowable_from": knowable,
                })
        return out

    # ------------------------------------------------------------------
    def _pit_sector_map(self, as_of_date: date, market: str) -> Dict[str, str]:
        """과거 as_of → jsonl 스냅샷에서 시장 전체 최신(<=as_of) 매핑 재구성."""
        path = self._snap_path
        if not path.exists():
            logger.debug("섹터 스냅샷 없음 - market=%s as_of=%s, 빈 결과", market, as_of_date)
            return {}
        # ticker 별 최신 레코드 채택
        latest: Dict[str, dict] = {}
        target = as_of_date.isoformat()
        try:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    if str(rec.get("market")) != str(market):
                        continue
                    rec_as_of = rec.get("as_of")
                    if not rec_as_of or rec_as_of > target:
                        continue
                    tk = rec.get("ticker")
                    if tk is None:
                        continue
                    prev = latest.get(tk)
                    if prev is None or rec_as_of >= prev.get("as_of", ""):
                        latest[tk] = rec
        except Exception as exc:
            logger.warning("섹터 스냅샷 로드 실패: %s", exc)
            return {}
        return {tk: rec.get("sector", "") for tk, rec in latest.items() if rec.get("sector")}

    def get_sector(
        self,
        ticker: str,
        as_of: Optional[datetime] = None,
        market: str = "KOSPI",
    ) -> Optional[str]:
        """단일 종목 섹터 조회 (없으면 None)."""
        return self.get_sector_map(as_of=as_of, market=market).get(ticker.zfill(6))


# ===========================================================================
# 2) KrxForeignFlowProvider — 외국인 순매수 flow
# ===========================================================================

@dataclass(frozen=True)
class ForeignFlowRecord:
    """종목·일자별 외국인 순매수 1행. knowable_from = 거래일 종가 확정 시점."""
    ticker: str
    trade_date: date
    net_value: float            # 외국인 순매수 대금 (원, 매수-매도)
    net_volume: Optional[float] # 외국인 순매수 수량 (주), 없으면 None
    knowable_from: datetime     # 수집 시점


class KrxForeignFlowProvider:
    """pykrx 경유 외국인 순매수 flow provider.

    get_foreign_net_purchase(ticker, start, end) → List[ForeignFlowRecord]
      · pykrx get_market_trading_value_by_investor(from, to, ticker) → '외국인' 행
    get_foreign_net_by_market(as_of, market, top) → Dict[ticker, net_value]
      · pykrx get_market_net_purchases_of_equities(from, to, market, '외국인')

    PIT: 외국인 순매수는 거래일 확정 데이터(현재→과거 안정) → 거래일 기준 적재.
         미래 일자 → lookahead 차단(빈 결과). 일별 스냅샷 jsonl 적재.
    off graceful: pykrx 미설치·네트워크 차단 → 빈 결과.
    credential 불요.
    """

    _FOREIGN_KEYS = ("외국인", "외국인합계", "기타외국인")

    def __init__(self, snap_path: Optional[Path] = None):
        self._snap_path = snap_path or _FLOW_SNAP_PATH

    # ------------------------------------------------------------------
    def get_foreign_net_purchase(
        self,
        ticker: str,
        start: datetime,
        end: datetime,
    ) -> List[ForeignFlowRecord]:
        """ticker 의 start~end 기간 외국인 순매수 (일자별). off 시 빈 list."""
        today = date.today()
        end_date = end.date()
        # lookahead 차단: 미래 구간은 오늘까지로 클램프
        if end_date > today:
            end_date = today
        if start.date() > end_date:
            return []

        out: List[ForeignFlowRecord] = []
        norm = ticker.zfill(6)
        from_str = start.strftime("%Y%m%d")
        to_str = end_date.strftime("%Y%m%d")
        knowable = datetime.now()

        try:
            pk = _pykrx_stock()
            # investor 축: index=투자자, 컬럼=거래/순매수 → 일자별은 detail freq
            df = pk.get_market_trading_value_by_investor(from_str, to_str, norm)
            if df is not None and len(df) > 0:
                # index = 투자자 구분, '순매수' 컬럼 (기간 합계)
                net_col = "순매수" if "순매수" in df.columns else None
                if net_col:
                    for inv_label in self._FOREIGN_KEYS:
                        if inv_label in df.index:
                            net_val = float(df.loc[inv_label, net_col])
                            out.append(ForeignFlowRecord(
                                ticker=norm,
                                trade_date=end_date,
                                net_value=net_val,
                                net_volume=None,
                                knowable_from=knowable,
                            ))
                            break
        except Exception as exc:
            logger.warning("외국인 순매수 조회 실패 - ticker=%s err=%s", norm, exc)

        # 스냅샷 적재
        for rec in out:
            _persist_jsonl(self._snap_path, {
                "as_of": rec.trade_date.isoformat(),
                "ticker": rec.ticker,
                "net_value": rec.net_value,
                "net_volume": rec.net_volume,
                "knowable_from": rec.knowable_from.isoformat(),
                "kind": "foreign_net_by_ticker",
            })
        return out

    # ------------------------------------------------------------------
    def get_foreign_net_by_market(
        self,
        as_of: datetime,
        market: str = "KOSPI",
        top: Optional[int] = None,
    ) -> Dict[str, float]:
        """as_of 기간(단일일) 시장 전체 종목별 외국인 순매수 대금 매핑.

        get_market_net_purchases_of_equities(date, date, market, '외국인').
        미래 as_of → lookahead 차단(빈 dict). off 시 빈 dict.
        """
        as_of_date = as_of.date()
        if as_of_date > date.today():
            logger.warning("미래 as_of 거부(lookahead) - market=%s as_of=%s", market, as_of_date)
            return {}

        out: Dict[str, float] = {}
        date_str = as_of_date.strftime("%Y%m%d")
        try:
            pk = _pykrx_stock()
            df = pk.get_market_net_purchases_of_equities(date_str, date_str, market, "외국인")
            if df is not None and len(df) > 0:
                net_col = None
                for c in ("순매수거래대금", "순매수", "거래대금"):
                    if c in df.columns:
                        net_col = c
                        break
                if net_col:
                    for idx, row in df.iterrows():
                        code = str(idx).zfill(6)
                        try:
                            out[code] = float(row[net_col])
                        except (TypeError, ValueError):
                            continue
        except Exception as exc:
            logger.warning("시장 외국인 순매수 조회 실패 - market=%s err=%s", market, exc)

        # 스냅샷 적재 (knowable_from = 수집 시점)
        if out:
            knowable = datetime.now().isoformat()
            for code, val in out.items():
                _persist_jsonl(self._snap_path, {
                    "as_of": as_of_date.isoformat(),
                    "ticker": code,
                    "net_value": val,
                    "net_volume": None,
                    "knowable_from": knowable,
                    "kind": "foreign_net_by_market",
                    "market": market,
                })

        if top is not None and out:
            ranked = sorted(out.items(), key=lambda kv: abs(kv[1]), reverse=True)[:top]
            return dict(ranked)
        return out

    # ------------------------------------------------------------------
    def load_pit_flow(self, ticker: str, as_of: datetime) -> Optional[float]:
        """과거 as_of 외국인 순매수 대금 PIT 재구성 (jsonl, 라이브 불필요)."""
        rec = _load_latest_jsonl(
            self._snap_path, as_of.date(), match={"ticker": ticker.zfill(6)}
        )
        if rec is not None:
            try:
                return float(rec.get("net_value"))
            except (TypeError, ValueError):
                return None
        return None


# ===========================================================================
# self-test (__main__) — mock PIT 검증 + 1 skipped LIVE
#   실행: PYTHONPATH=/d/projects/Inv python stock/data/krx_flows.py
# ===========================================================================

if __name__ == "__main__":
    import os
    import tempfile

    logging.basicConfig(level=logging.INFO)
    fails: List[str] = []

    def check(name: str, cond: bool) -> None:
        status = "PASS" if cond else "FAIL"
        print(f"  [{status}] {name}")
        if not cond:
            fails.append(name)

    print("=== krx_flows self-test ===")

    tmp = Path(tempfile.mkdtemp())
    sector_snap = tmp / "sector.jsonl"
    flow_snap = tmp / "flow.jsonl"

    # --- T1: mock 섹터 스냅샷 PIT 재구성 (라이브 불필요) ---------------------
    # 과거 두 시점 적재 → as_of 가 중간이면 그 이전 최신만 채택 (lookahead 차단)
    _persist_jsonl(sector_snap, {
        "as_of": "2026-01-02", "market": "KOSPI", "ticker": "005930",
        "sector": "반도체", "knowable_from": "2026-01-02T18:00:00",
    })
    _persist_jsonl(sector_snap, {
        "as_of": "2026-03-02", "market": "KOSPI", "ticker": "005930",
        "sector": "반도체-개정", "knowable_from": "2026-03-02T18:00:00",
    })
    _persist_jsonl(sector_snap, {
        "as_of": "2026-01-02", "market": "KOSDAQ", "ticker": "035720",
        "sector": "IT서비스", "knowable_from": "2026-01-02T18:00:00",
    })
    sp = KrxSectorProvider(snap_path=sector_snap)
    m_feb = sp._pit_sector_map(date(2026, 2, 1), "KOSPI")
    check("PIT 섹터 2/1 → 1/2 스냅샷(반도체) 채택", m_feb.get("005930") == "반도체")
    m_apr = sp._pit_sector_map(date(2026, 4, 1), "KOSPI")
    check("PIT 섹터 4/1 → 3/2 최신(반도체-개정) 채택", m_apr.get("005930") == "반도체-개정")
    m_dec = sp._pit_sector_map(date(2025, 12, 1), "KOSPI")
    check("PIT 섹터 2025/12 → 미래 레코드 제외(빈 결과)", m_dec.get("005930") is None)
    check("PIT 섹터 market 격리(KOSDAQ 미혼입)", "035720" not in m_apr)

    # --- T2: 미래 as_of lookahead 차단 (라이브 경로) ------------------------
    future = datetime.now() + timedelta(days=30)
    check("섹터 미래 as_of → 빈 dict", sp.get_sector_map(as_of=future, market="KOSPI") == {})

    ffp = KrxForeignFlowProvider(snap_path=flow_snap)
    check("flow 미래 as_of → 빈 dict", ffp.get_foreign_net_by_market(as_of=future, market="KOSPI") == {})
    # 미래 end 구간 → start>today clamp 시 빈 list
    check("flow start 미래 → 빈 list",
          ffp.get_foreign_net_purchase("005930", future, future + timedelta(days=1)) == [])

    # --- T3: mock flow 스냅샷 PIT 재구성 ------------------------------------
    _persist_jsonl(flow_snap, {
        "as_of": "2026-02-10", "ticker": "005930", "net_value": 1.5e10,
        "net_volume": None, "knowable_from": "2026-02-10T18:00:00",
        "kind": "foreign_net_by_ticker",
    })
    _persist_jsonl(flow_snap, {
        "as_of": "2026-02-20", "ticker": "005930", "net_value": -3.2e10,
        "net_volume": None, "knowable_from": "2026-02-20T18:00:00",
        "kind": "foreign_net_by_ticker",
    })
    v_15 = ffp.load_pit_flow("005930", datetime(2026, 2, 15))
    check("PIT flow 2/15 → 2/10 스냅샷(1.5e10) 채택", v_15 == 1.5e10)
    v_25 = ffp.load_pit_flow("005930", datetime(2026, 2, 25))
    check("PIT flow 2/25 → 2/20 최신(-3.2e10) 채택", v_25 == -3.2e10)
    v_early = ffp.load_pit_flow("005930", datetime(2026, 2, 1))
    check("PIT flow 2/1 → 미래 레코드 제외(None)", v_early is None)

    # --- T4: off graceful (lazy import 실패 시 예외 X) ----------------------
    # 존재하지 않는 종목 라이브 호출도 예외 던지지 않고 빈 결과여야 함
    try:
        r = KrxForeignFlowProvider(snap_path=flow_snap).get_foreign_net_purchase(
            "000000", datetime(2026, 1, 2), datetime(2026, 1, 3)
        )
        check("off/오류 graceful — 예외 없이 list 반환", isinstance(r, list))
    except Exception as exc:  # noqa: BLE001
        check(f"off/오류 graceful (예외 발생: {exc})", False)

    # --- T5: 1 skipped LIVE (네트워크/credential 의존, 기본 SKIP) -----------
    if os.environ.get("KRX_FLOWS_LIVE") == "1":
        print("  [LIVE] 실 pykrx 호출 ...")
        live_map = KrxSectorProvider().get_sector_map(market="KOSPI")
        print(f"    KOSPI 섹터 매핑 종목 수: {len(live_map)}")
        live_flow = KrxForeignFlowProvider().get_foreign_net_by_market(
            datetime.now() - timedelta(days=3), "KOSPI", top=5
        )
        print(f"    최근 외국인 순매수 top5: {live_flow}")
        check("LIVE 섹터 매핑 비어있지 않음", len(live_map) > 0)
    else:
        print("  [SKIP] LIVE 테스트 (KRX_FLOWS_LIVE=1 로 활성화)")

    print("=== 결과:", "ALL PASS" if not fails else f"FAIL {fails}", "===")
    raise SystemExit(1 if fails else 0)
