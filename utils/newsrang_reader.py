"""뉴스랑(NewsRang) 시그널 리더 — 공유 모듈

초단타(short_term_trader), 김치랑(kimchirang) 등 독립 시스템에서
뉴스랑 최신 시그널을 조회하여 매매 판단에 반영한다.

데이터 소스:
  1순위: Supabase newsrang_signals 테이블 (최신 1행)
  2순위: 로컬 캐시 파일 (data/newsrang_cache.json)

사용법:
  from utils.newsrang_reader import get_newsrang_signal
  sig = get_newsrang_signal()
  # sig = {"score": 17, "rss": -3, "social": 5, "x": 0, "signal": "neutral",
  #        "whale_alert": None, "age_min": 12, "fresh": True}
"""

import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.db import db

logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_FILE = PROJECT_DIR / "data" / "newsrang_cache.json"
_CACHE_MAX_AGE_SEC = 300  # 5분 캐시
_STALE_THRESHOLD_MIN = 60  # 60분 넘으면 stale 판정

_cached: dict | None = None
_cached_at: float = 0


def get_newsrang_signal(max_age_min: int = 120) -> dict:
    """뉴스랑 최신 시그널을 반환한다.

    Args:
        max_age_min: 이 시간(분) 이상 된 데이터는 stale로 표시

    Returns:
        dict with keys:
          score (int): Data Fusion 종합 점수
          rss (int): RSS 뉴스 감성 점수 (-100~+100)
          social (int): 소셜 감성 점수 (-100~+100)
          x (int): X 트위터 점수 (-100~+100)
          signal (str): 종합 판정 (strong_bullish/bullish/neutral/bearish/strong_bearish)
          whale_alert (dict|None): X 고래 알림 요약
          rss_top (list): 주요 뉴스 헤드라인 (최대 10개)
          age_min (float): 데이터 나이 (분)
          fresh (bool): max_age_min 이내면 True
    """
    global _cached, _cached_at

    # 메모리 캐시 확인
    if _cached and (time.time() - _cached_at) < _CACHE_MAX_AGE_SEC:
        return _cached

    result = _fetch_from_db()
    if not result:
        result = _fetch_from_cache_file()
    if not result:
        result = _empty_signal()

    _cached = result
    _cached_at = time.time()

    # 로컬 캐시 파일 갱신
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
    except Exception:
        pass

    return result


def _fetch_from_db() -> dict | None:
    """core.db 어댑터로 최신 newsrang_signals 1행을 조회한다."""
    try:
        rows = db.select(
            "newsrang_signals",
            select="created_at,rss_combined_score,rss_crypto_score,rss_macro_score,"
                   "x_score,x_signal,x_whale_summary,"
                   "social_score,social_signal,"
                   "fusion_total_score,fusion_rss_adj,fusion_x_adj,fusion_social_adj,"
                   "rss_top_signals",
            order="created_at.desc",
            limit=1,
        )
        if not rows:
            return None

        row = rows[0]
        created = row.get("created_at", "")

        # 나이 계산
        age_min = _calc_age_min(created)

        # 종합 시그널 판정
        score = row.get("fusion_total_score", 0) or 0
        signal = _score_to_signal(score)

        # 고래 알림
        whale = row.get("x_whale_summary")
        if isinstance(whale, str):
            try:
                whale = json.loads(whale)
            except Exception:
                whale = None

        # 주요 뉴스
        rss_top = row.get("rss_top_signals")
        if isinstance(rss_top, str):
            try:
                rss_top = json.loads(rss_top)
            except Exception:
                rss_top = []
        if not isinstance(rss_top, list):
            rss_top = []

        return {
            "score": score,
            "rss": row.get("rss_combined_score", 0) or 0,
            "rss_crypto": row.get("rss_crypto_score", 0) or 0,
            "rss_macro": row.get("rss_macro_score", 0) or 0,
            "social": row.get("social_score", 0) or 0,
            "x": row.get("x_score", 0) or 0,
            "signal": signal,
            "x_signal": row.get("x_signal", "no_data"),
            "social_signal": row.get("social_signal", "neutral"),
            "whale_alert": whale,
            "rss_top": rss_top[:10],
            "fusion_rss_adj": row.get("fusion_rss_adj", 0) or 0,
            "fusion_x_adj": row.get("fusion_x_adj", 0) or 0,
            "fusion_social_adj": row.get("fusion_social_adj", 0) or 0,
            "age_min": round(age_min, 1),
            "fresh": age_min <= _STALE_THRESHOLD_MIN,
            "source": "db",
        }
    except Exception as e:
        logger.debug(f"newsrang DB 조회 실패: {e}")
        return None


def _fetch_from_cache_file() -> dict | None:
    """로컬 캐시 파일에서 읽는다."""
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "score" in data:
            data["source"] = "cache"
            # age_min/fresh 재계산: created_at 필드 우선, 없으면 파일 수정 시간 사용
            created_at = data.get("created_at") or data.get("ts")
            if created_at:
                age_min = _calc_age_min(str(created_at))
            else:
                file_mtime = CACHE_FILE.stat().st_mtime
                age_min = (time.time() - file_mtime) / 60
            data["age_min"] = round(age_min, 1)
            data["fresh"] = age_min <= _STALE_THRESHOLD_MIN
            return data
    except Exception:
        pass
    return None


def _empty_signal() -> dict:
    """데이터 없을 때 기본값."""
    return {
        "score": 0, "rss": 0, "rss_crypto": 0, "rss_macro": 0,
        "social": 0, "x": 0,
        "signal": "no_data", "x_signal": "no_data", "social_signal": "neutral",
        "whale_alert": None, "rss_top": [],
        "fusion_rss_adj": 0, "fusion_x_adj": 0, "fusion_social_adj": 0,
        "age_min": 999, "fresh": False, "source": "empty",
    }


def _score_to_signal(score: int) -> str:
    if score >= 30:
        return "strong_bullish"
    elif score >= 10:
        return "bullish"
    elif score <= -30:
        return "strong_bearish"
    elif score <= -10:
        return "bearish"
    return "neutral"


def _calc_age_min(iso_str: str) -> float:
    """ISO 타임스탬프와 현재 시간의 차이를 분으로 반환."""
    from datetime import datetime, timezone
    try:
        # ISO 형식 파싱
        created = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - created).total_seconds() / 60
    except Exception:
        return 999
