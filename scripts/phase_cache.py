#!/usr/bin/env python3
"""
Phase Cache — Supabase 결정 데이터 공유 캐시

Phase 7-12 (feedback_hub, dynamic_risk, strategy_health, regime_learner)가
모두 decisions 테이블을 개별 조회하던 것을 1회 조회로 통합한다.

사용법:
  # run_agents.py에서 사이클 시작 시 프리로드
  from scripts.phase_cache import prefetch_decisions, get_cached_decisions, invalidate

  prefetch_decisions()  # 1회 Supabase 조회

  # 각 Phase에서 캐시 사용
  decisions = get_cached_decisions(days=7)   # 메모리 캐시에서 필터링
  decisions = get_cached_decisions(days=14)  # 동일 캐시, 다른 필터
  decisions = get_cached_decisions(days=30)  # 30일까지 커버

  invalidate()  # 사이클 종료 시 캐시 해제
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.db import db

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

KST = timezone(timedelta(hours=9))

# 캐시 TTL (초) — 같은 프로세스 내에서 10분간 유효
_CACHE_TTL = 600

# 모듈-레벨 캐시
_cache: dict = {
    "decisions": None,      # list[dict] — 최근 30일 buy/sell 결정
    "decisions_all": None,  # list[dict] — 30일 hold 포함 전체
    "fetched_at": 0.0,      # time.monotonic()
}


def prefetch_decisions(max_days: int = 30) -> bool:
    """decisions 테이블을 1회 조회하여 캐시에 저장한다.

    Phase 7-12에서 사용하는 모든 컬럼을 포함한다:
      - feedback_hub: confidence, was_correct_4h, outcome_4h_pct, source, market_data_snapshot
      - dynamic_risk: outcome_4h_pct, outcome_24h_pct, created_at, decision
      - strategy_health: decision, confidence, outcome_4h_pct, outcome_24h_pct,
                         was_correct_4h, created_at, agent_name
      - regime_learner: market_data_snapshot, was_correct_4h, outcome_4h_pct, confidence, created_at

    Returns:
        True if fetch succeeded
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=max_days)).isoformat()

    try:
        # 통합 SELECT: 모든 Phase에서 필요한 컬럼 합집합
        all_rows = db.select(
            "decisions",
            filters={"created_at": f"gte.{cutoff}"},
            order="created_at.desc",
            limit=500,
            select=(
                "id,decision,confidence,outcome_4h_pct,outcome_24h_pct,"
                "was_correct_4h,created_at,agent_name,source,"
                "market_data_snapshot"
            ),
        ) or []
        # buy/sell만 필터 (dynamic_risk, strategy_health에서 사용)
        buy_sell = [d for d in all_rows if d.get("decision") in ("buy", "sell")]
        _cache["decisions"] = buy_sell
        _cache["decisions_all"] = all_rows
        _cache["fetched_at"] = time.monotonic()
        return True
    except Exception:
        return False


def _is_valid() -> bool:
    """캐시가 유효한지 확인한다."""
    if _cache["decisions"] is None:
        return False
    elapsed = time.monotonic() - _cache["fetched_at"]
    return elapsed < _CACHE_TTL


def get_cached_decisions(
    days: int = 7,
    buy_sell_only: bool = True,
    include_hold: bool = False,
) -> list[dict] | None:
    """캐시에서 최근 N일 결정을 필터링하여 반환한다.

    Args:
        days: 최근 N일
        buy_sell_only: True이면 buy/sell만, False이면 전체
        include_hold: was_correct_4h이 null인 것도 포함

    Returns:
        필터링된 결정 리스트, 캐시 미스 시 None
    """
    if not _is_valid():
        return None

    source = _cache["decisions"] if buy_sell_only else _cache["decisions_all"]
    if source is None:
        return None

    cutoff = (datetime.now(KST) - timedelta(days=days)).isoformat()
    filtered = []
    for d in source:
        created = d.get("created_at", "")
        if created >= cutoff:
            filtered.append(d)

    return filtered


def invalidate():
    """캐시를 무효화한다. 사이클 종료 시 호출."""
    _cache["decisions"] = None
    _cache["decisions_all"] = None
    _cache["fetched_at"] = 0.0
