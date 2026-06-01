"""stock/data/french_factors.py — Kenneth French 5-factor vintage 수집 (US 팩터).

Ken French Data Library 무료 CSV (mkt-rf/smb/hml/rmw/cma + rf) 를 받아
**관측월 vintage 로 VintageStore 에 적재** → VintageProvider.realtime(series, period, as_of)
인터페이스로 자동 PIT 보호. core/data/vintage.VintageStore 와 동일 계약
(core/data/weight_panel.VintageProvider Protocol 충족 → build_indicator_matrix 소비 가능).

정합 근거: stock/data/sector_multiples.French49Provider 가 이미 Ken French 49산업을 쓴다.
본 모듈은 같은 데이터 라이브러리의 **5-factor 시계열** 을 담당 — 기존 변경 없이 추가.

vintage 보존 원칙:
- French 의 month-end 관측치 row 가 곧 측정 대상 기간(period="YYYY-MM" 또는 "YYYY-MM-DD").
- 그 관측치가 **알 수 있게 되는 시점**(vintage_knowable_from) = 다음 달/다음 영업일 공표 시차
  반영(보수적으로 period 종료 + publish_lag). 즉 month=2024-01 팩터는 2024-02 이후에야 가시.
- VintageStore.realtime(as_of) 가 이 knowable_from ≤ as_of 만 노출 → lookahead 차단.

off graceful: 네트워크/소스 없음 → 빈 결과(빈 VintageStore). 샌드박스 외부망 차단 대응
(sector_multiples 와 동일 N-T1-SECTORMULT 패턴). offline cache(data/french_factors/) 우선.
"""

from __future__ import annotations

import csv
import io
import logging
import zipfile
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from core.data.vintage import VintageStore

logger = logging.getLogger("stock.data.french_factors")

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "french_factors"

_BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp"

# 5-factor 데이터셋 (무료, Ken French Data Library). 월간/일간 두 frequency.
FRENCH_5F_URLS = {
    "monthly": f"{_BASE}/F-F_Research_Data_5_Factors_2x3_CSV.zip",
    "daily": f"{_BASE}/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip",
}

# CSV 헤더 컬럼 → 정규화 series_id (대소문자/공백 무시 매핑).
# Ken French 헤더: "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"
_COL_TO_SERIES = {
    "mkt-rf": "FF5_MKT_RF",
    "smb": "FF5_SMB",
    "hml": "FF5_HML",
    "rmw": "FF5_RMW",
    "cma": "FF5_CMA",
    "rf": "FF5_RF",
}

# 공표 시차(보수적). 월간=관측월 종료 후 대략 한 달 뒤 라이브러리 갱신, 일간=익영업일.
_PUBLISH_LAG = {"monthly": timedelta(days=35), "daily": timedelta(days=2)}

# License: Ken French Data Library — 학술/비상업 무료 공개. 출처 표기 권장
# (Eugene F. Fama & Kenneth R. French). 본 데이터는 재배포 시 출처 명기.
LICENSE_NOTE = "Kenneth French Data Library (free, academic; cite Fama-French)"


def _parse_period_token(tok: str, freq: str) -> Optional[str]:
    """French row 인덱스 토큰 → period 라벨.

    monthly: "202401" → "2024-01" / daily: "20240131" → "2024-01-31".
    숫자 외(섹션 헤더/주석/공란)는 None.
    """
    tok = tok.strip()
    if not tok.isdigit():
        return None
    if freq == "monthly" and len(tok) == 6:
        return f"{tok[:4]}-{tok[4:6]}"
    if freq == "daily" and len(tok) == 8:
        return f"{tok[:4]}-{tok[4:6]}-{tok[6:8]}"
    return None


def _period_end_date(period: str, freq: str) -> Optional[date]:
    """period 라벨 → 측정 기간 종료일(공표 시차 기준점)."""
    try:
        if freq == "monthly":
            y, m = period.split("-")
            yy, mm = int(y), int(m)
            # 월말일
            if mm == 12:
                nxt = date(yy + 1, 1, 1)
            else:
                nxt = date(yy, mm + 1, 1)
            return nxt - timedelta(days=1)
        # daily
        y, m, d = period.split("-")
        return date(int(y), int(m), int(d))
    except (ValueError, IndexError):
        return None


def _knowable_from(period: str, freq: str) -> Optional[date]:
    end = _period_end_date(period, freq)
    if end is None:
        return None
    return end + _PUBLISH_LAG.get(freq, timedelta(days=35))


class FrenchFactorProvider:
    """Ken French 5-factor → VintageStore PIT 적재 (US 팩터, 관측월 vintage 보존).

    realtime(series_id, period, as_of) = VintageStore 위임 → 자동 PIT 보호.
    series_id ∈ {FF5_MKT_RF, FF5_SMB, FF5_HML, FF5_RMW, FF5_CMA, FF5_RF}.

    off graceful: 소스(cache/network) 없음 → 빈 store. is_loaded()=False.
    """

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self._cache = cache_dir or _CACHE_DIR
        self._store = VintageStore()
        self._loaded = False
        self._row_count = 0

    # ------------------------------------------------------------------
    # 적재
    # ------------------------------------------------------------------
    def load(self, freq: str = "monthly") -> int:
        """offline cache 우선 적재. row 수 반환(0=소스 없음, graceful)."""
        cache_file = self._cache / f"french_5f_{freq}.csv"
        if cache_file.exists():
            try:
                text = cache_file.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                logger.warning("French cache 읽기 실패 %s: %s", cache_file, exc)
                return 0
            return self._ingest_csv_text(text, freq)
        logger.info(
            "French 5F cache 부재 (%s) — live fetch deferred (refresh_cache 로 갱신)", freq
        )
        return 0

    def _ingest_csv_text(self, text: str, freq: str) -> int:
        """Ken French CSV 본문(또는 cache 정규화 CSV) → VintageStore 적재.

        Ken French 원본 CSV 는 상단 주석 + 빈 줄 + 헤더 + 데이터 + 하단 부속 테이블 구조.
        헤더는 첫 컬럼이 공란이고 나머지가 팩터명인 행. 데이터는 첫 토큰이 날짜 숫자인 행.
        """
        reader = csv.reader(io.StringIO(text))
        col_series: List[Optional[str]] = []  # 컬럼 인덱스 → series_id (없으면 None)
        header_seen = False
        count = 0
        for row in reader:
            if not row:
                if header_seen:
                    # 데이터 블록 종료(annual/부속 테이블 시작) — 첫 블록만 사용
                    break
                continue
            first = row[0].strip()
            # 헤더 후보: 첫 칸 공란 + 뒤에 알려진 팩터명
            if not header_seen:
                mapped = [
                    _COL_TO_SERIES.get(c.strip().lower())
                    for c in row[1:]
                ]
                if first == "" and any(m is not None for m in mapped):
                    col_series = [None] + mapped
                    header_seen = True
                continue
            # 데이터 행
            period = _parse_period_token(first, freq)
            if period is None:
                # 숫자 아님 → 데이터 블록 끝
                break
            kf = _knowable_from(period, freq)
            if kf is None:
                continue
            for idx, raw in enumerate(row):
                if idx >= len(col_series):
                    break
                sid = col_series[idx]
                if sid is None:
                    continue
                raw = raw.strip()
                if raw in ("", "-99.99", "-999"):
                    continue
                try:
                    val = float(raw)
                except ValueError:
                    continue
                self._store.add(sid, period, val, kf)
                count += 1
        self._row_count += count
        self._loaded = self._loaded or count > 0
        return count

    # ------------------------------------------------------------------
    # VintageProvider 인터페이스 (core/data/weight_panel.VintageProvider Protocol)
    # ------------------------------------------------------------------
    def realtime(self, series_id: str, period: str, as_of) -> Optional[float]:
        """as_of 에 알 수 있던 팩터값(PIT). VintageStore 위임 → lookahead 차단."""
        return self._store.realtime(series_id, period, as_of)

    def final(self, series_id: str, period: str) -> Optional[float]:
        return self._store.final(series_id, period)

    @property
    def store(self) -> VintageStore:
        return self._store

    def is_loaded(self) -> bool:
        return self._loaded

    def factor_series_ids(self) -> List[str]:
        return list(_COL_TO_SERIES.values())

    # ------------------------------------------------------------------
    # 라이브 갱신 (네트워크) — 샌드박스 외부망 차단 시 사용자 PC 에서 실행
    # ------------------------------------------------------------------
    def refresh_cache(self, freq: str = "monthly") -> bool:
        """Ken French zip CSV fetch → cache 저장. 성공 True (graceful False)."""
        url = FRENCH_5F_URLS.get(freq)
        if url is None:
            logger.warning("French 알 수 없는 freq: %s", freq)
            return False
        try:
            import urllib.request

            with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310
                blob = resp.read()
            with zipfile.ZipFile(io.BytesIO(blob)) as zf:
                csv_name = next(
                    (n for n in zf.namelist() if n.lower().endswith(".csv")), None
                )
                if csv_name is None:
                    logger.warning("French zip 안에 CSV 없음: %s", url)
                    return False
                text = zf.read(csv_name).decode("utf-8", errors="replace")
            self._cache.mkdir(parents=True, exist_ok=True)
            (self._cache / f"french_5f_{freq}.csv").write_text(text, encoding="utf-8")
            return True
        except Exception as exc:
            logger.warning("French refresh 실패 freq=%s: %s", freq, exc)
            return False


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    try:  # Windows cp949 콘솔에서 em-dash/한글 출력 보호
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=== FrenchFactorProvider self-test ===")

    # 1) off graceful: cache 없는 경로 → 빈 store, 예외 없음
    import tempfile

    empty = FrenchFactorProvider(cache_dir=Path(tempfile.gettempdir()) / "no_such_french_dir")
    n0 = empty.load("monthly")
    assert n0 == 0, n0
    assert empty.is_loaded() is False
    assert empty.realtime("FF5_MKT_RF", "2024-01", "2024-12-31") is None
    print("1) off graceful: 소스 없음 → 빈 결과(None), 예외 없음 OK")

    # 2) Ken French 원본 포맷(주석+공란+헤더+데이터+부속테이블) 파싱
    sample = (
        "This file was created using the 100% etc (annotation)\n"
        "\n"
        ",Mkt-RF,SMB,HML,RMW,CMA,RF\n"
        "202401,1.20,-0.50,0.30,0.10,0.20,0.42\n"
        "202402,2.00,0.40,-0.10,0.05,-0.05,0.41\n"
        "202403,-0.80,0.10,0.60,-0.20,0.15,0.43\n"
        "\n"
        "Annual Factors: January-December\n"
        ",Mkt-RF,SMB,HML,RMW,CMA,RF\n"
        "2024,12.50,1.20,3.40,0.90,1.10,5.10\n"
    )
    prov = FrenchFactorProvider()
    n = prov._ingest_csv_text(sample, "monthly")
    # 3 데이터행 × 6 컬럼 = 18 (annual 블록은 빈 줄에서 차단)
    assert n == 18, f"적재 row 기대 18, 실제 {n}"
    assert prov.is_loaded() is True
    print(f"2) Ken French 포맷 파싱: 데이터 18셀 적재(annual 블록 차단) OK")

    # 3) ★PIT vintage: 2024-01 팩터는 공표시차(35일) 後에만 가시
    #    knowable_from = 2024-01-31 + 35d = 2024-03-06
    assert prov.realtime("FF5_MKT_RF", "2024-01", "2024-02-15") is None, "공표 前 미가시"
    v = prov.realtime("FF5_MKT_RF", "2024-01", "2024-03-31")
    assert v is not None and abs(v - 1.20) < 1e-9, v
    print("3) PIT vintage: 2024-01 팩터 02-15 미가시 / 03-31 가시(1.20) — lookahead 차단 OK")

    # 4) 5팩터 + RF 모두 적재되었는지
    for sid, exp in [("FF5_SMB", -0.50), ("FF5_HML", 0.30), ("FF5_RMW", 0.10),
                     ("FF5_CMA", 0.20), ("FF5_RF", 0.42)]:
        got = prov.realtime(sid, "2024-01", "2024-12-31")
        assert got is not None and abs(got - exp) < 1e-9, f"{sid}={got} 기대 {exp}"
    print("4) 5팩터(mkt-rf/smb/hml/rmw/cma)+rf 전부 적재 확인 OK")

    # 5) VintageProvider Protocol 호환 (weight_panel.build_indicator_matrix 소비 가능)
    from core.data.weight_panel import build_indicator_matrix

    panel = build_indicator_matrix(
        prov,
        series_ids=["FF5_MKT_RF", "FF5_SMB", "FF5_HML"],
        periods=["2024-01", "2024-02", "2024-03"],
        as_of="2024-12-31",
    )
    assert panel.shape == (3, 3), panel.shape
    assert panel.n_complete == 3, panel.n_complete
    print("5) VintageProvider Protocol 호환: build_indicator_matrix (3x3, 완전관측 3행) OK")

    # 6) daily freq period 파싱
    daily_sample = (
        "header annotation\n\n"
        ",Mkt-RF,SMB,HML,RMW,CMA,RF\n"
        "20240102,0.10,0.02,-0.01,0.00,0.01,0.02\n"
        "20240103,-0.20,0.01,0.03,0.01,-0.01,0.02\n"
    )
    dprov = FrenchFactorProvider()
    dn = dprov._ingest_csv_text(daily_sample, "daily")
    assert dn == 12, dn
    # 2024-01-02 + 2일 = 2024-01-04 가시
    assert dprov.realtime("FF5_MKT_RF", "2024-01-02", "2024-01-03") is None
    assert abs(dprov.realtime("FF5_MKT_RF", "2024-01-02", "2024-01-05") - 0.10) < 1e-9
    print("6) daily freq: 20240102→2024-01-02 파싱 + 익영업일 PIT OK")

    print(f"\nlicense: {LICENSE_NOTE}")
    print("FrenchFactorProvider self-test PASS")
