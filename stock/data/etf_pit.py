"""stock/data/etf_pit.py — 테마 ETF 가격·AUM·유동성 PIT provider (Phase 2, 약변별 fallback).

WHY: RepresentativeETFSelector(stock/selector.py) 가 소비할 ETF 메타(aum/adv/nav/holdings_asof)를
     look-ahead 없이 조립한다. 약변별 sleeve → 단일 테마 ETF fallback 의 데이터 레이어.

설계 (자문 3R 수렴 D5 정합 — gemini-web + claude-web 2026-06-06):
- **AUM 우선순위**: 운용사 공시 절대값 PIT > NAV×상장좌수 근사 > 현재 스냅샷(look-ahead 위험).
  공시/좌수는 미보존(비PIT) → krx_universe.py 와 동일하게 **일별 jsonl 스냅샷 적재**로 PIT 재구성.
- **1일 lag 강제**: as_of 시점 의사결정은 as_of-1(전영업일)까지만 knowable → T 종가로 T 체결
  가정(look-ahead) 차단. get_* 전부 `_pit_cutoff = as_of - 1day` 마스킹.
- **trailing 1M ADV**: as_of-1 기준 과거 21영업일 거래대금 평균 = 청산·체결가능성 proxy.
- **graceful**: FDR/yfinance/네트워크 부재 시 None/빈 반환(예외 X) — us_etf.py off-graceful 정합.

PIT 가용성:
- 가격/NAV: FDR(KR) · yfinance(US) **역사 시계열 PIT 가용** → as_of-1 마스킹만으로 충분.
- AUM/좌수: **비PIT 현재 스냅샷** → 일별 적재 후 <=cutoff 최신 레코드 채택(미래 레코드 제외).

⛔ 본 모듈은 production core/stock 호출 경로에서 import 되지 않음(provider 레이어). env 무관하게
   기존 17 test byte-identical. construction._fallback_decisions 가 etf_picks 를 받을 뿐, 그 picks
   조립(본 모듈 호출)은 호출자(백테스트/라이브 provider) 책임.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("stock.data.etf_pit")

# AUM/거래대금 스냅샷 jsonl (비PIT → 일별 적재 PIT 재구성). krx_snapshots.jsonl 정합.
_SNAP_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "etf_snapshots.jsonl"

# 1일 lag (look-ahead 차단). as_of 의사결정은 전영업일까지만 knowable.
_PIT_LAG_DAYS = 1
# trailing ADV 윈도 (영업일 ≈ 1개월).
_ADV_WINDOW = 21


# ---------------------------------------------------------------------------
# lazy import (라이브러리 부재 시 graceful)
# ---------------------------------------------------------------------------

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
class EtfPitSnapshot:
    """ETF 1개의 as_of 기준 PIT 스냅샷 (1일 lag 적용).

    selector 의 etf_pick 메타로 직접 매핑된다(ticker/aum/holdings_asof).
    None 필드 = 해당 시점 데이터 부재(graceful) — 호출자가 라우팅에서 배제.
    """
    ticker: str
    as_of: datetime              # 의사결정 시점 (요청값)
    pit_cutoff: date             # 실제 knowable 경계 (as_of - 1영업일)
    close: Optional[float]        # 전영업일 종가
    nav: Optional[float]          # 전영업일 NAV (KR=FDR, US=close 근사)
    aum: Optional[float]          # AUM PIT (공시>NAV×좌수>스냅샷 우선순위)
    aum_source: str               # "disclosed" | "nav_x_shares" | "snapshot" | "none"
    adv_1m: Optional[float]       # trailing 21영업일 평균 거래대금
    market: str                   # "KR" | "US"
    vintage_note: str = ""

    @property
    def eligible_liquidity(self) -> bool:
        """가격·AUM·ADV 모두 존재 = 라우팅 적격 1차(청산리스크 필터 전)."""
        return self.close is not None and self.aum is not None and self.adv_1m is not None


# ---------------------------------------------------------------------------
# 일별 AUM/거래대금 스냅샷 적재 (krx_universe._persist/_load 패턴)
# ---------------------------------------------------------------------------

def persist_aum_snapshot(
    as_of_date: date, ticker: str, payload: dict,
    snap_path: Optional[Path] = None,
) -> None:
    """AUM/좌수/거래대금 비PIT 스냅샷을 jsonl append (as_of + ticker + payload)."""
    path = snap_path or _SNAP_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"as_of": as_of_date.isoformat(), "ticker": ticker, **payload}
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("ETF 스냅샷 적재 실패: %s", exc)


def load_aum_snapshot(
    cutoff: date, ticker: str,
    snap_path: Optional[Path] = None,
) -> Optional[dict]:
    """jsonl 에서 <=cutoff 최신 스냅샷 로드 — PIT 재구성(미래 레코드 제외)."""
    path = snap_path or _SNAP_PATH
    if not path.exists():
        return None
    best: Optional[dict] = None
    best_as_of = ""
    target = cutoff.isoformat()
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
                # as_of 누락(빈→사전순 최소 오선택) / 미래 레코드 제외, 최신(<=target) 채택
                if not rec_as_of or rec_as_of > target:
                    continue
                if rec_as_of >= best_as_of:
                    best = rec
                    best_as_of = rec_as_of
    except Exception as exc:
        logger.warning("ETF 스냅샷 로드 실패: %s", exc)
    return best


# ---------------------------------------------------------------------------
# 핵심: EtfPitProvider
# ---------------------------------------------------------------------------

class EtfPitProvider:
    """테마 ETF 가격·AUM·유동성 PIT 조립.

    snapshot(ticker, market, as_of) → EtfPitSnapshot (1일 lag 적용).
    - KR: FDR.DataReader(ticker, ...) 일별 OHLCV(종가/거래대금). AUM=jsonl 공시 > NAV×좌수 > MarCap 스냅샷.
    - US: yfinance.Ticker(ticker).history(...) 일별 종가/거래량. AUM=yfinance totalAssets 스냅샷(비PIT, 적재).
    네트워크/라이브러리 부재 → None 필드 graceful(예외 X).
    """

    def __init__(self, snap_path: Optional[Path] = None):
        self._snap_path = snap_path or _SNAP_PATH

    # ------------------------------------------------------------------
    @staticmethod
    def _cutoff(as_of: datetime) -> date:
        """as_of - 1영업일 근사(주말 보정). 정밀 휴장일은 fetch 결과 인덱스가 자연 처리."""
        d = as_of.date() - timedelta(days=_PIT_LAG_DAYS)
        # 토(5)/일(6) → 직전 금요일로 당김 (휴장일은 시세 인덱스에서 추가 보정됨)
        while d.weekday() >= 5:
            d -= timedelta(days=1)
        return d

    # ------------------------------------------------------------------
    def snapshot(
        self, ticker: str, market: str, as_of: Optional[datetime] = None,
    ) -> EtfPitSnapshot:
        as_of = as_of or datetime.utcnow()
        cutoff = self._cutoff(as_of)
        market = market.upper()

        if market == "KR":
            close, nav, adv = self._kr_price(ticker, cutoff)
        else:
            close, nav, adv = self._us_price(ticker, cutoff)

        aum, aum_src = self._resolve_aum(ticker, cutoff, nav)

        notes = []
        if close is None:
            notes.append("price:none(graceful)")
        if aum_src == "snapshot":
            notes.append("aum:snapshot-vintage(공시/좌수 부재 fallback)")
        elif aum_src == "none":
            notes.append("aum:none(라우팅 EW로 강등 권고)")
        return EtfPitSnapshot(
            ticker=ticker, as_of=as_of, pit_cutoff=cutoff,
            close=close, nav=nav, aum=aum, aum_source=aum_src,
            adv_1m=adv, market=market,
            vintage_note="; ".join(notes) or "ok",
        )

    # ------------------------------------------------------------------
    # KR: FDR DataReader (역사 PIT 가용)
    # ------------------------------------------------------------------
    def _kr_price(self, ticker: str, cutoff: date):
        try:
            fdr = _fdr()
            # cutoff 까지만 fetch (look-ahead 차단). 시작 = 충분한 ADV 윈도 확보.
            start = (cutoff - timedelta(days=_ADV_WINDOW * 3)).isoformat()
            df = fdr.DataReader(ticker, start, cutoff.isoformat())
            if df is None or len(df) == 0:
                return None, None, None
            close = float(df["Close"].iloc[-1])
            # 거래대금: FDR KR OHLCV 는 'Volume'(주). 거래대금 ≈ Close×Volume(원). 근사.
            adv = self._trailing_adv(df, value_col=None)
            return close, close, adv   # KR NAV ≈ 종가(괴리 작음, 정밀 NAV 는 공시 jsonl)
        except Exception as exc:
            logger.info("KR ETF 시세 fetch graceful 실패 %s: %s", ticker, exc)
            return None, None, None

    # ------------------------------------------------------------------
    # US: yfinance (역사 PIT 가용)
    # ------------------------------------------------------------------
    def _us_price(self, ticker: str, cutoff: date):
        try:
            yf = _yf()
            start = (cutoff - timedelta(days=_ADV_WINDOW * 3)).isoformat()
            end = (cutoff + timedelta(days=1)).isoformat()   # yfinance end 는 exclusive
            hist = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
            if hist is None or len(hist) == 0:
                return None, None, None
            close = float(hist["Close"].iloc[-1])
            adv = self._trailing_adv(hist, value_col=None)
            return close, close, adv
        except Exception as exc:
            logger.info("US ETF 시세 fetch graceful 실패 %s: %s", ticker, exc)
            return None, None, None

    # ------------------------------------------------------------------
    @staticmethod
    def _trailing_adv(df, value_col: Optional[str]):
        """trailing 21행 평균 거래대금. value_col 없으면 Close×Volume 근사."""
        try:
            tail = df.tail(_ADV_WINDOW)
            if value_col and value_col in tail.columns:
                series = tail[value_col]
            elif "Volume" in tail.columns and "Close" in tail.columns:
                series = tail["Close"] * tail["Volume"]
            else:
                return None
            vals = [float(x) for x in series.tolist() if x == x]   # NaN 제거
            if not vals:
                return None
            return sum(vals) / len(vals)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # AUM 우선순위: 공시 절대값 > NAV×좌수 > 현재 스냅샷 (자문 D5)
    # ------------------------------------------------------------------
    def _resolve_aum(self, ticker: str, cutoff: date, nav: Optional[float]):
        rec = load_aum_snapshot(cutoff, ticker, snap_path=self._snap_path)
        if rec:
            # 1순위: 운용사 공시 절대값 PIT
            disclosed = rec.get("aum_disclosed")
            if disclosed not in (None, "", 0):
                return float(disclosed), "disclosed"
            # 2순위: NAV × 상장좌수 (둘 다 PIT 일 때)
            shares = rec.get("shares_outstanding")
            rec_nav = rec.get("nav", nav)
            if shares and rec_nav:
                return float(rec_nav) * float(shares), "nav_x_shares"
            # 3순위: 스냅샷 시 MarCap 근사 (vintage 경고)
            marcap = rec.get("aum_marcap")
            if marcap not in (None, "", 0):
                return float(marcap), "snapshot"
        return None, "none"


# ---------------------------------------------------------------------------
# Phase 2↔4 wire: etf-picks(정적 선정) + EtfPitProvider(동적 PIT) → construction etf_picks dict
# ---------------------------------------------------------------------------

# sleeve → (market, etf-picks JSON 내 위치). build_etf_picks.py 산출 스키마 정합.
_KR_SLEEVES = ("financial", "battery", "bio", "shipbuilding", "consumer", "chemical", "auto")
_US_DEFENSIVE_SUB = ("staples", "utilities", "healthcare", "comm_mature")


def seed_aum_from_picks(
    picks: dict, asof_date: date, snap_path: Optional[Path] = None,
) -> int:
    """etf-picks JSON 의 정적 AUM → jsonl 스냅샷 시드 (forward 운영용, aum_marcap=snapshot 등급).

    ⚠️ 이 AUM 은 '선정 시점 현재 스냅샷'(자문 D5 3순위, vintage 약). 백테스트 과거 시점엔 look-ahead
       위험 → 운용사 공시 history / NAV×좌수 history 로 정밀화 전까지 forward 운영에만 사용.
    반환 = 적재 건수.
    """
    n = 0
    for sleeve in _KR_SLEEVES:
        rec = (picks.get("kr_picks") or {}).get(sleeve)
        if rec and rec.get("aum_marcap"):
            persist_aum_snapshot(asof_date, rec["ticker"],
                                 {"aum_marcap": float(rec["aum_marcap"])}, snap_path=snap_path)
            n += 1
    for sub in _US_DEFENSIVE_SUB:
        rec = (picks.get("us_defensive_subsector") or {}).get(sub)
        if rec and rec.get("aum"):
            # US aum = 절대값($) → disclosed 등급(yfinance totalAssets, 단 비PIT 스냅샷)
            persist_aum_snapshot(asof_date, rec["ticker"],
                                 {"aum_disclosed": float(rec["aum"])}, snap_path=snap_path)
            n += 1
    return n


def assemble_etf_picks(
    picks: dict, asof: datetime, snap_path: Optional[Path] = None,
) -> dict[str, dict]:
    """etf-picks JSON + EtfPitProvider → construction.build_sleeve_decisions(etf_picks=...) dict.

    반환 {sleeve_id: {ticker, aum, adv, holdings_source, holdings_asof, ...}}.
    가격/AUM/ADV 부재(graceful) sleeve 는 dict 에 미포함 → construction 이 EwBasket 으로 안전 강등.
    US defensive = sub-sector 4개 중 대표 1개(staples) 로 sleeve 통째 매핑(현 ledger; sub-sector 분리는 미결).
    """
    prov = EtfPitProvider(snap_path=snap_path)
    out: dict[str, dict] = {}

    def _entry(sleeve_id: str, ticker: str, market: str, holdings_source: str):
        snap = prov.snapshot(ticker, market, asof)
        if snap.close is None or snap.aum is None:
            return   # 적격 데이터 부재 → 미포함(EW 강등)
        out[sleeve_id] = {
            "ticker": ticker, "aum": snap.aum, "aum_source": snap.aum_source,
            "adv": snap.adv_1m, "close": snap.close,
            "holdings_source": holdings_source,
            "holdings_asof": datetime.combine(snap.pit_cutoff, datetime.min.time()),
            "pit_cutoff": snap.pit_cutoff.isoformat(),
        }

    for sleeve in _KR_SLEEVES:
        rec = (picks.get("kr_picks") or {}).get(sleeve)
        if rec:
            _entry(sleeve, rec["ticker"], "KR", rec.get("holdings_source", "FDR"))
    # US defensive: 현 ledger = sub-sector staples 대표(sleeve 통째). sub-sector 분리는 Phase 미결(§5-5).
    staples = (picks.get("us_defensive_subsector") or {}).get("staples")
    if staples:
        _entry("us_defensive", staples["ticker"], "US", staples.get("holdings_source", "yfinance"))
    return out


# ---------------------------------------------------------------------------
# self-test (graceful — 네트워크/라이브러리 불요, jsonl 경계만 검증)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import tempfile

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=== ETF PIT provider self-test ===")

    tmp = Path(tempfile.mkdtemp()) / "etf_snapshots.jsonl"

    # 1) 1일 lag cutoff: 주말 보정 (월요일 as_of → 직전 금요일)
    prov = EtfPitProvider(snap_path=tmp)
    mon = datetime(2026, 6, 8, 10, 0)   # 2026-06-08 = 월요일
    cutoff = prov._cutoff(mon)
    assert cutoff == date(2026, 6, 5), cutoff   # 일(6/7)→토(6/6) 건너뛰고 금(6/5)
    print(f"1) 1일 lag + 주말 보정: 월 6/8 → cutoff 금 6/5 OK")

    # 2) AUM PIT: 미래 레코드 제외, <=cutoff 최신 채택
    persist_aum_snapshot(date(2026, 6, 1), "091170", {"aum_disclosed": 6100.0}, snap_path=tmp)
    persist_aum_snapshot(date(2026, 6, 5), "091170", {"aum_disclosed": 6143.0}, snap_path=tmp)
    persist_aum_snapshot(date(2026, 6, 9), "091170", {"aum_disclosed": 9999.0}, snap_path=tmp)  # 미래
    aum, src = prov._resolve_aum("091170", date(2026, 6, 5), None)
    assert aum == 6143.0 and src == "disclosed", (aum, src)
    print(f"2) AUM PIT: <=cutoff 최신=6143(disclosed), 미래 6/9 9999 제외 OK")

    # 3) AUM 우선순위: 공시 부재 → NAV×좌수 → snapshot
    persist_aum_snapshot(date(2026, 6, 5), "TESTNAVSH", {"nav": 10000.0, "shares_outstanding": 2.0}, snap_path=tmp)
    aum2, src2 = prov._resolve_aum("TESTNAVSH", date(2026, 6, 5), None)
    assert aum2 == 20000.0 and src2 == "nav_x_shares", (aum2, src2)
    persist_aum_snapshot(date(2026, 6, 5), "TESTSNAP", {"aum_marcap": 360.0}, snap_path=tmp)
    aum3, src3 = prov._resolve_aum("TESTSNAP", date(2026, 6, 5), None)
    assert aum3 == 360.0 and src3 == "snapshot", (aum3, src3)
    print("3) AUM 우선순위: 공시>NAV×좌수(20000)>snapshot(360) OK")

    # 4) graceful: 스냅샷·시세 부재 → None 필드, 예외 없음
    aum4, src4 = prov._resolve_aum("UNKNOWN", date(2026, 6, 5), None)
    assert aum4 is None and src4 == "none", (aum4, src4)
    snap = prov.snapshot("UNKNOWN", "KR", mon)   # 네트워크 graceful → close None
    assert snap.ticker == "UNKNOWN" and snap.aum is None
    assert snap.pit_cutoff == date(2026, 6, 5)
    assert not snap.eligible_liquidity
    print("4) graceful: 미존재 ticker → None 필드 + eligible_liquidity False, 예외 없음 OK")

    # 5) trailing ADV: Close×Volume 근사
    try:
        import pandas as pd
        df = pd.DataFrame({
            "Close": [100.0] * 21,
            "Volume": [10.0] * 21,
        })
        adv = EtfPitProvider._trailing_adv(df, None)
        assert adv == 1000.0, adv   # 100×10
        print("5) trailing ADV: Close×Volume 평균=1000 OK")
    except ImportError:
        print("5) trailing ADV: pandas 부재 → skip (graceful)")

    # 6) seed + assemble (graceful — 시세 없는 더미 ticker는 미포함, AUM 시드는 적재됨)
    dummy_picks = {
        "kr_picks": {"financial": {"ticker": "091170", "aum_marcap": 6143.0, "holdings_source": "FDR"}},
        "us_defensive_subsector": {"staples": {"ticker": "XLP", "aum": 1.48e10, "holdings_source": "yfinance"}},
    }
    seeded = seed_aum_from_picks(dummy_picks, date(2026, 6, 4), snap_path=tmp)
    assert seeded == 2, seeded
    aum_kr, src_kr = prov._resolve_aum("091170", date(2026, 6, 4), None)
    assert aum_kr == 6143.0 and src_kr == "snapshot", (aum_kr, src_kr)
    aum_us, src_us = prov._resolve_aum("XLP", date(2026, 6, 4), None)
    assert aum_us == 1.48e10 and src_us == "disclosed", (aum_us, src_us)
    print("6) seed_aum_from_picks: KR aum_marcap→snapshot / US aum→disclosed 적재 2건 OK")

    print("\nETF PIT provider self-test PASS")
