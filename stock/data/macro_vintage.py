"""stock/data/macro_vintage.py — FRED realtime_*(ALFRED) vintage 거시 PIT (SO-3/P4).

WHY: OpenBB vintage-drop 우회. FRED get_series 는 최신값 반환(lookahead 위험) →
     ALFRED realtime_start/realtime_end 파라미터로 as_of 시점 vintage 강제.
     동일 시리즈도 as_of 가 다르면 다른 값 → lookahead 완전 차단.

설계:
- MacroVintageProvider.get_vintage(series_id, as_of) → float | None
  · fredapi.Fred.get_series_vintage_dates() → 발표일 목록 → as_of 이하 최신 vintage 선택
  · fredapi.Fred.get_series(realtime_start, realtime_end) → 해당 시점 값
- ECOS(한국은행) 경계: EcosVintageStub — credential 부재, 이연 박제
- core/brain/fred_adapter 연계 경계(본체 미변경)
- credential 부재(FRED_API_KEY 없음): 무료 시리즈는 인증 불요이나 ALFRED vintage는 key 필요
  → 어댑터 본체 빌드 + fixture 경계 테스트, 라이브 이연 박제
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger("stock.data.macro_vintage")


# ---------------------------------------------------------------------------
# MacroVintageProvider — FRED ALFRED vintage PIT
# ---------------------------------------------------------------------------

class MacroVintageProvider:
    """FRED realtime_*(ALFRED) vintage 직접 호출 → 거시 PIT.

    get_vintage(series_id, as_of) → float | None

    ALFRED 방식:
      fredapi Fred.get_series(series_id,
          realtime_start=<as_of>, realtime_end=<as_of>)
      → 해당 시점에 FRED 가 공표했던 최신값 (lookahead 차단).

    credential(FRED_API_KEY) 부재 시: None 반환 + 경고, 라이브 이연.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.environ.get("FRED_API_KEY", "")
        self._client = None

    # ------------------------------------------------------------------
    def _ensure_client(self):
        if self._client is not None:
            return self._client
        if not self._api_key:
            return None
        try:
            from fredapi import Fred
            self._client = Fred(api_key=self._api_key)
            return self._client
        except Exception as exc:
            logger.warning("fredapi 클라이언트 초기화 실패: %s", exc)
            return None

    def is_available(self) -> bool:
        return self._ensure_client() is not None

    def get_vintage(
        self,
        series_id: str,
        as_of: datetime,
    ) -> Optional[float]:
        """as_of 시점 ALFRED vintage 값 반환 (lookahead 차단).

        realtime_start=realtime_end=as_of_date → FRED 가 그 날 공표한 최신 관측값.
        미래 realtime(as_of > today) → None (lookahead 거부).
        """
        client = self._ensure_client()
        if client is None:
            logger.warning(
                "FRED_API_KEY 없음 — get_vintage 이연 (deferral-pinning). series=%s", series_id
            )
            return None

        # 미래 as_of 거부
        if as_of.date() > date.today():
            logger.warning("미래 realtime as_of 거부(lookahead) — series=%s as_of=%s", series_id, as_of)
            return None

        as_of_str = as_of.strftime("%Y-%m-%d")
        try:
            series = client.get_series(
                series_id,
                realtime_start=as_of_str,
                realtime_end=as_of_str,
            )
            if series is None or len(series) == 0:
                return None
            val = series.dropna()
            if len(val) == 0:
                return None
            return float(val.iloc[-1])
        except Exception as exc:
            logger.warning("ALFRED vintage 조회 실패 series=%s as_of=%s: %s", series_id, as_of, exc)
            return None

    def get_vintage_series(
        self,
        series_id: str,
        start: datetime,
        end: datetime,
    ):
        """start~end 기간 vintage 시계열 반환 (pd.Series). lookahead 차단 — end<=today."""
        client = self._ensure_client()
        if client is None:
            logger.warning("FRED_API_KEY 없음 — vintage series 이연. series=%s", series_id)
            return None

        if end.date() > date.today():
            end = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            return client.get_series(
                series_id,
                realtime_start=start.strftime("%Y-%m-%d"),
                realtime_end=end.strftime("%Y-%m-%d"),
            )
        except Exception as exc:
            logger.warning("ALFRED vintage series 실패 series=%s: %s", series_id, exc)
            return None


# ---------------------------------------------------------------------------
# ECOS 경계 stub (한국은행 경제통계시스템, credential 부재 → 이연)
# ---------------------------------------------------------------------------

class EcosVintageStub:
    """ECOS(한국은행 경제통계시스템) PIT vintage 경계.

    credential(ECOS_API_KEY) 부재 → None 반환.
    라이브 구현: ECOS open API + statSearch/100Y 시리즈 realtime 파라미터.
    이연 박제: progress.md N-P4-ECOS (credential 프로비저닝 후 해소).
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.environ.get("ECOS_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def get_vintage(self, series_code: str, as_of: datetime) -> Optional[float]:
        if not self._api_key:
            logger.debug("ECOS_API_KEY 없음 — 이연 박제. series=%s", series_code)
            return None
        # 실 구현: ECOS API /StatisticSearch/{key}/json/kr/100/... + 발표일 정렬
        raise NotImplementedError("ECOS 라이브 구현: credential 프로비저닝 후 활성화")


# ---------------------------------------------------------------------------
# fred_adapter 연계 경계 (본체 미변경, 래퍼만)
# ---------------------------------------------------------------------------

class FredAdapterBridge:
    """core/brain/fred_adapter 의 RealFredAdapter 와 MacroVintageProvider 연계 경계.

    core/brain/fred_adapter.py 본체 미변경 — 이 클래스가 브리지 역할.
    """

    def __init__(self, vintage_provider: Optional[MacroVintageProvider] = None):
        self._vintage = vintage_provider or MacroVintageProvider()

    def get_pit_value(self, series_id: str, as_of: datetime) -> Optional[float]:
        """as_of PIT vintage 값. fred_adapter SERIES 큐레이션 목록 소비 가능."""
        return self._vintage.get_vintage(series_id, as_of)

    def is_available(self) -> bool:
        return self._vintage.is_available()
