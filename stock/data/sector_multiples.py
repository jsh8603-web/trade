"""stock/data/sector_multiples.py — US 섹터 멀티플 vintage 수집 (Phase2 T1, WP-T1-D).

SPEC-T1 T1-1: Damodaran(US 섹터 멀티플/WACC/마진) + Kenneth French 49산업.
findings §2: Damodaran=vintage 없음(현재 앵커로만, PIT 백테스트 부적합),
            French49=49산업 멀티플 시계열(PIT 가능).

본 모듈은 **섹터 레벨** 멀티플 vintage 를 산출한다(firm 레벨 raw 멀티플은 pit_panel).
T2 가 "동종 대비 싸다" 기준선(structure model)으로 소비한다.

⚠️ 라이브 fetch = 네트워크 의존(read_excel URL / French CSV). 샌드박스 외부망 차단
   → offline cache(data/sector_multiples/) 우선, 부재 시 빈 결과로 graceful degrade.
   실 fetch round-trip = N-T1-SECTORMULT (go-live deferral, N-P4 패턴 동일).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("stock.data.sector_multiples")

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "sector_multiples"

# Damodaran 무료 데이터 URL (findings §2). 연1회 갱신, vintage 없음.
DAMODARAN_URLS = {
    "ev_ebitda": "https://pages.stern.nyu.edu/~adamodar/pc/datasets/vebitda.xls",
    "pbv": "https://pages.stern.nyu.edu/~adamodar/pc/datasets/pbvdata.xls",
    "margin": "https://pages.stern.nyu.edu/~adamodar/pc/datasets/margin.xls",
    "wacc": "https://pages.stern.nyu.edu/~adamodar/pc/datasets/wacc.xls",
}


@dataclass(frozen=True)
class SectorMultipleSnapshot:
    """섹터 레벨 멀티플 vintage 1행. knowable_from = 스냅샷 수집 시점."""
    sector: str
    scheme: str               # "DAMODARAN" | "FRENCH49"
    metric: str               # "ev_ebitda" | "pbv" | "ps" | ...
    value: float
    knowable_from: datetime   # 수집 시점 (Damodaran=현재 앵커, French=관측월)
    vintage_note: str = ""    # "no-vintage:current-anchor" 등 PIT 경고


class DamodaranProvider:
    """Damodaran 섹터 멀티플 (US, 현재 앵커 only — PIT 백테스트 부적합)."""

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self._cache = cache_dir or _CACHE_DIR

    def fetch(self, metric: str, as_of: Optional[datetime] = None) -> List[SectorMultipleSnapshot]:
        """metric 의 섹터별 멀티플. offline cache 우선, 부재 시 빈 결과.

        ⚠️ Damodaran 은 vintage 없음 → as_of 무시(현재 스냅샷). vintage_note 로 경고.
        """
        as_of = as_of or datetime.utcnow()
        cache_file = self._cache / f"damodaran_{metric}.csv"
        if not cache_file.exists():
            logger.info("Damodaran cache 부재 (%s) — live fetch deferred(N-T1-SECTORMULT)", metric)
            return []
        return self._parse_cache(cache_file, metric, as_of)

    def _parse_cache(self, path: Path, metric: str, as_of: datetime) -> List[SectorMultipleSnapshot]:
        import csv
        out: List[SectorMultipleSnapshot] = []
        try:
            with open(path, encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    try:
                        val = float(row.get("value", ""))
                    except (TypeError, ValueError):
                        continue
                    out.append(SectorMultipleSnapshot(
                        sector=row.get("sector", ""), scheme="DAMODARAN",
                        metric=metric, value=val, knowable_from=as_of,
                        vintage_note="no-vintage:current-anchor",
                    ))
        except Exception as exc:
            logger.warning("Damodaran cache 파싱 실패 %s: %s", path, exc)
        return out

    def refresh_cache(self, metric: str) -> bool:
        """라이브 fetch → cache 갱신 (네트워크 필요). 성공 True.

        N-T1-SECTORMULT: 샌드박스 외부망 차단 → 사용자 PC 에서 실행.
        """
        url = DAMODARAN_URLS.get(metric)
        if url is None:
            return False
        try:
            import pandas as pd
            df = pd.read_excel(url)  # 네트워크
            self._cache.mkdir(parents=True, exist_ok=True)
            df.to_csv(self._cache / f"damodaran_{metric}.csv", index=False)
            return True
        except Exception as exc:
            logger.warning("Damodaran refresh 실패 %s: %s", metric, exc)
            return False


class French49Provider:
    """Kenneth French 49산업 멀티플 시계열 (PIT 가능 — 관측월 vintage 보유)."""

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self._cache = cache_dir or _CACHE_DIR

    def fetch(self, metric: str, as_of: datetime) -> List[SectorMultipleSnapshot]:
        """as_of 시점에 알 수 있었던 49산업 멀티플 (관측월 <= as_of)."""
        cache_file = self._cache / f"french49_{metric}.csv"
        if not cache_file.exists():
            logger.info("French49 cache 부재 (%s) — live fetch deferred(N-T1-SECTORMULT)", metric)
            return []
        return self._parse_cache(cache_file, metric, as_of)

    def _parse_cache(self, path: Path, metric: str, as_of: datetime) -> List[SectorMultipleSnapshot]:
        import csv
        out: List[SectorMultipleSnapshot] = []
        try:
            with open(path, encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    try:
                        obs = datetime.fromisoformat(row["knowable_from"])
                        val = float(row["value"])
                    except (KeyError, TypeError, ValueError):
                        continue
                    if obs > as_of:    # PIT: 관측월 <= as_of
                        continue
                    out.append(SectorMultipleSnapshot(
                        sector=row.get("sector", ""), scheme="FRENCH49",
                        metric=metric, value=val, knowable_from=obs,
                        vintage_note="pit-ok",
                    ))
        except Exception as exc:
            logger.warning("French49 cache 파싱 실패 %s: %s", path, exc)
        return out
