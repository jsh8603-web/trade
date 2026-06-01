"""stock/data/us_etf.py — US ETF 구성/섹터 매핑 수집기 (graceful).

목표:
1) **섹터 ETF 매핑표** (XLK/XLF/XLV/... → GICS 11 섹터). 라이브러리 의존 없이 항상 가용
   (static reference table) — broad-market ETF 의 섹터 익스포저 분해 기준선.
2) **broad-market ETF holdings** (SPY/QQQ/IVV 등) — 무료 소스(issuer 공개 CSV) graceful fetch.
   외부망 차단/소스 없음 시 빈 holdings(매핑표는 그대로 가용) → off graceful.

정합: stock/data/sector_multiples (offline cache 우선 + 빈 결과 degrade) 패턴 동일.
기존 파일 변경 없이 추가만. holdings 는 시점 vintage 가 약하므로(issuer 일별 갱신, 과거
vintage 미보존) PIT 백테스트엔 부적합 — knowable_from=수집 시점 anchor + vintage_note 경고.

license/source:
- 섹터 ETF 매핑: 공개 사실(SPDR Select Sector / iShares). 라이선스 제약 없음(reference).
- holdings: 각 issuer 공개 CSV (State Street SPDR, Invesco, BlackRock iShares) — 개인/연구용
  무료 공개. 재배포는 issuer 약관 확인 권장.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("stock.data.us_etf")

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "us_etf"

# ---------------------------------------------------------------------------
# 섹터 ETF 매핑표 (SPDR Select Sector → GICS 11 섹터). static reference, 항상 가용.
# ---------------------------------------------------------------------------
SECTOR_ETF_MAP: Dict[str, str] = {
    "XLK": "Information Technology",
    "XLF": "Financials",
    "XLV": "Health Care",
    "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLB": "Materials",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLC": "Communication Services",
}

# broad-market ETF → 발행사/벤치마크 (holdings fetch 대상 메타).
BROAD_ETFS: Dict[str, Dict[str, str]] = {
    "SPY": {"issuer": "State Street SPDR", "benchmark": "S&P 500"},
    "IVV": {"issuer": "BlackRock iShares", "benchmark": "S&P 500"},
    "QQQ": {"issuer": "Invesco", "benchmark": "Nasdaq-100"},
    "VOO": {"issuer": "Vanguard", "benchmark": "S&P 500"},
}

LICENSE_NOTE = (
    "Sector map = public reference (SPDR Select Sector / GICS); "
    "holdings = issuer free public CSV (SPDR/iShares/Invesco), personal/research use"
)


@dataclass(frozen=True)
class EtfHolding:
    """ETF 구성종목 1행. as_of=수집 시점(holdings 는 과거 vintage 미보존 → anchor)."""
    etf: str
    ticker: str
    name: str
    weight: float                # 비중 (% or fraction, 원본 그대로)
    as_of: datetime
    vintage_note: str = "no-vintage:snapshot-anchor"


@dataclass
class EtfComposition:
    """ETF 1개의 구성 스냅샷."""
    etf: str
    holdings: List[EtfHolding] = field(default_factory=list)
    as_of: Optional[datetime] = None

    @property
    def n_holdings(self) -> int:
        return len(self.holdings)

    def top(self, k: int = 10) -> List[EtfHolding]:
        return sorted(self.holdings, key=lambda h: h.weight, reverse=True)[:k]


class SectorEtfMap:
    """섹터 ETF ↔ GICS 섹터 매핑 (static, 항상 가용). 네트워크 불요."""

    def sector_of(self, etf: str) -> Optional[str]:
        return SECTOR_ETF_MAP.get(etf.upper())

    def etf_of(self, sector: str) -> Optional[str]:
        s = sector.strip().lower()
        for etf, sec in SECTOR_ETF_MAP.items():
            if sec.lower() == s:
                return etf
        return None

    def all(self) -> Dict[str, str]:
        return dict(SECTOR_ETF_MAP)

    def sector_etfs(self) -> List[str]:
        return list(SECTOR_ETF_MAP.keys())


class UsEtfHoldingsProvider:
    """broad-market ETF holdings 수집 (offline cache 우선, off graceful).

    fetch(etf) → EtfComposition. cache(data/us_etf/holdings_{ETF}.csv) 없으면
    빈 composition(holdings=[]) — 예외 없음. 라이브 갱신 refresh_cache(etf).
    """

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self._cache = cache_dir or _CACHE_DIR

    def fetch(self, etf: str, as_of: Optional[datetime] = None) -> EtfComposition:
        etf = etf.upper()
        as_of = as_of or datetime.now(timezone.utc).replace(tzinfo=None)
        cache_file = self._cache / f"holdings_{etf}.csv"
        if not cache_file.exists():
            logger.info("ETF holdings cache 부재 (%s) — live fetch deferred (refresh_cache)", etf)
            return EtfComposition(etf=etf, holdings=[], as_of=as_of)
        return self._parse_cache(cache_file, etf, as_of)

    def _parse_cache(self, path: Path, etf: str, as_of: datetime) -> EtfComposition:
        holdings: List[EtfHolding] = []
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                reader = csv.DictReader(fh)
                # 컬럼명 정규화 (issuer 마다 다름)
                for row in reader:
                    norm = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
                    ticker = (norm.get("ticker") or norm.get("symbol")
                              or norm.get("holding ticker") or "")
                    name = (norm.get("name") or norm.get("company") or norm.get("description")
                            or norm.get("holding name") or "")
                    w_raw = (norm.get("weight") or norm.get("weight (%)")
                             or norm.get("% of net assets") or norm.get("weighting") or "")
                    w_raw = w_raw.replace("%", "").replace(",", "").strip()
                    if not ticker and not name:
                        continue
                    try:
                        weight = float(w_raw) if w_raw else 0.0
                    except ValueError:
                        weight = 0.0
                    holdings.append(EtfHolding(
                        etf=etf, ticker=ticker, name=name, weight=weight, as_of=as_of,
                    ))
        except Exception as exc:
            logger.warning("ETF holdings 파싱 실패 %s: %s", path, exc)
        return EtfComposition(etf=etf, holdings=holdings, as_of=as_of)

    def refresh_cache(self, etf: str) -> bool:
        """issuer 공개 CSV fetch → cache. 성공 True (graceful False).

        URL 은 issuer 마다 다르고 변동 → 사용자 PC 에서 실 URL 지정 갱신.
        샌드박스 외부망 차단 시 false 반환(이연).
        """
        etf = etf.upper()
        url = self._issuer_url(etf)
        if not url:
            logger.warning("ETF %s holdings URL 미정 — 수동 cache 필요", etf)
            return False
        try:
            import urllib.request

            with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310
                blob = resp.read().decode("utf-8", errors="replace")
            self._cache.mkdir(parents=True, exist_ok=True)
            (self._cache / f"holdings_{etf}.csv").write_text(blob, encoding="utf-8")
            return True
        except Exception as exc:
            logger.warning("ETF %s holdings refresh 실패: %s", etf, exc)
            return False

    @staticmethod
    def _issuer_url(etf: str) -> Optional[str]:
        # iShares(IVV) 는 공개 CSV 직링크 제공. SPY/QQQ 는 발행사 페이지 경유(변동) → None.
        urls = {
            "IVV": (
                "https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf/"
                "1467271812596.ajax?fileType=csv&fileName=IVV_holdings&dataType=fund"
            ),
        }
        return urls.get(etf)


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import tempfile

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=== US ETF collector self-test ===")

    # 1) 섹터 매핑표: static, 항상 가용
    sm = SectorEtfMap()
    assert sm.sector_of("XLK") == "Information Technology"
    assert sm.sector_of("xlf") == "Financials"  # case-insensitive
    assert sm.etf_of("Health Care") == "XLV"
    assert len(sm.sector_etfs()) == 11, len(sm.sector_etfs())
    print(f"1) 섹터 ETF 매핑표: 11개 GICS 섹터 (XLK→IT, XLF→Financials, ...) OK")

    # 2) off graceful: holdings cache 없음 → 빈 composition, 예외 없음
    prov = UsEtfHoldingsProvider(cache_dir=Path(tempfile.gettempdir()) / "no_such_etf_dir")
    comp = prov.fetch("SPY")
    assert comp.etf == "SPY"
    assert comp.n_holdings == 0
    assert comp.as_of is not None
    print("2) off graceful: holdings 소스 없음 → 빈 구성(0 holdings), 예외 없음 OK")

    # 3) cache CSV 파싱 (issuer 컬럼 변형 정규화)
    tmpdir = Path(tempfile.mkdtemp())
    (tmpdir / "holdings_SPY.csv").write_text(
        "Ticker,Name,Weight (%)\n"
        "AAPL,Apple Inc,7.10\n"
        "MSFT,Microsoft Corp,6.50\n"
        "NVDA,NVIDIA Corp,5.80\n",
        encoding="utf-8",
    )
    prov2 = UsEtfHoldingsProvider(cache_dir=tmpdir)
    comp2 = prov2.fetch("SPY")
    assert comp2.n_holdings == 3, comp2.n_holdings
    top1 = comp2.top(1)[0]
    assert top1.ticker == "AAPL" and abs(top1.weight - 7.10) < 1e-9, top1
    print(f"3) holdings cache 파싱: SPY 3종목, top1=AAPL(7.10%) OK")

    # 4) 컬럼명 변형(Symbol/% of Net Assets) 정규화
    (tmpdir / "holdings_QQQ.csv").write_text(
        "Symbol,Company,% of Net Assets\n"
        "MSFT,Microsoft,8.9\n"
        "AAPL,Apple,8.1\n",
        encoding="utf-8",
    )
    comp3 = prov2.fetch("QQQ")
    assert comp3.n_holdings == 2, comp3.n_holdings
    assert comp3.top(1)[0].ticker == "MSFT"
    print("4) issuer 컬럼 변형(Symbol/% of Net Assets) 정규화 OK")

    # 5) broad ETF 메타 + vintage 경고 노트
    assert "SPY" in BROAD_ETFS and BROAD_ETFS["SPY"]["benchmark"] == "S&P 500"
    assert comp2.holdings[0].vintage_note == "no-vintage:snapshot-anchor"
    print("5) broad ETF 메타(SPY/QQQ/IVV/VOO) + holdings vintage-anchor 경고 OK")

    print(f"\nlicense: {LICENSE_NOTE}")
    print("US ETF collector self-test PASS")
