#!/usr/bin/env python3
"""
Predictive API Throttler — 429 예방 + 레이턴시 트렌드 기반 선제 조절.

기능:
  - record_call(): 모든 API 호출 기록 (타임스탬프, 상태코드, 레이턴시)
  - should_throttle(): 호출 전 대기 여부 판단 (예측 기반)
  - get_throttle_stats(): 전체 API 호출 패턴 요약
  - get_api_health(): 개별 API 건강 상태

예측 로직:
  1. 429 비율 감지 — 최근 5분 내 429 > 10% → throttle
  2. 레이턴시 트렌드 — 평균 레이턴시 50%+ 증가 → pre-throttle
  3. 버스트 감지 — 30초 내 10회+ 호출 → throttle
  4. 시간대 패턴 — 429 빈발 시간대 → pre-throttle

상태 파일: data/api_throttle_state.json (atomic write)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = PROJECT_DIR / "data" / "api_throttle_state.json"

# ── Per-API 설정 ──────────────────────────────────────────
API_CONFIGS: dict[str, dict] = {
    "upbit": {
        "max_calls_per_sec": 10,
        "baseline_latency_ms": 200,
    },
    "tavily": {
        "max_calls_per_sec": 1,
        "baseline_latency_ms": 1000,
    },
    "binance": {
        "max_calls_per_sec": 20,
        "baseline_latency_ms": 100,
    },
    "alternative_me": {
        "max_calls_per_sec": 0.1,  # 1 call / 10 sec
        "baseline_latency_ms": 500,
    },
    "mempool": {
        "max_calls_per_sec": 5,
        "baseline_latency_ms": 300,
    },
}

# 롤링 윈도우 크기
ROLLING_WINDOW_SIZE = 100
# 429 감지 윈도우 (초)
RATE_DETECT_WINDOW_SEC = 300  # 5분
# 버스트 감지 윈도우 (초)
BURST_DETECT_WINDOW_SEC = 30
# 버스트 임계값
BURST_THRESHOLD = 10
# 429 비율 임계값
RATE_429_THRESHOLD = 0.10
# 레이턴시 증가 임계값
LATENCY_INCREASE_THRESHOLD = 0.50  # 50%
# 딜레이 범위
MIN_DELAY = 0.5
MAX_DELAY = 5.0
# 에러율 경고 임계값
ERROR_RATE_DEGRADED = 0.20  # 20%
# 에러 감지 윈도우 (초)
ERROR_DETECT_WINDOW_SEC = 3600  # 1시간


def _load_state() -> dict:
    """상태 파일에서 호출 이력 로드."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"calls": {}, "hourly_429": {}}


def _save_state(state: dict) -> None:
    """상태 파일 atomic 저장."""
    try:
        from scripts.atomic_write import atomic_json_save
        atomic_json_save(STATE_FILE, state)
    except ImportError:
        # fallback: 직접 저장
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)


def record_call(api_name: str, status_code: int, latency_ms: float) -> None:
    """API 호출 기록.

    Args:
        api_name: API 이름 (upbit, tavily, binance, alternative_me, mempool)
        status_code: HTTP 상태 코드
        latency_ms: 응답 시간 (ms)
    """
    state = _load_state()

    # 호출 이력 초기화
    if api_name not in state["calls"]:
        state["calls"][api_name] = []

    # 호출 기록 추가
    entry = {
        "ts": time.time(),
        "status": status_code,
        "latency_ms": round(latency_ms, 1),
    }
    state["calls"][api_name].append(entry)

    # 롤링 윈도우 유지 (최근 100건)
    if len(state["calls"][api_name]) > ROLLING_WINDOW_SIZE:
        state["calls"][api_name] = state["calls"][api_name][-ROLLING_WINDOW_SIZE:]

    # 429 시간대 패턴 기록
    if status_code == 429:
        hour_key = datetime.now(timezone.utc).strftime("%H")
        if api_name not in state["hourly_429"]:
            state["hourly_429"][api_name] = {}
        state["hourly_429"][api_name][hour_key] = (
            state["hourly_429"][api_name].get(hour_key, 0) + 1
        )

    _save_state(state)


def should_throttle(api_name: str) -> tuple[bool, float]:
    """호출 전 대기 여부 판단.

    Returns:
        (should_wait, suggested_delay_seconds)
        should_wait=False이면 즉시 호출 가능, True이면 suggested_delay만큼 대기 권장.
    """
    state = _load_state()
    calls = state.get("calls", {}).get(api_name, [])

    if not calls:
        return False, 0.0

    now = time.time()
    severity = 0.0  # 0~1 범위, 높을수록 심각

    # ── 1. 429 비율 감지 (최근 5분) ──
    recent_calls = [c for c in calls if now - c["ts"] < RATE_DETECT_WINDOW_SEC]
    if recent_calls:
        count_429 = sum(1 for c in recent_calls if c["status"] == 429)
        rate_429 = count_429 / len(recent_calls)
        if rate_429 > RATE_429_THRESHOLD:
            severity = max(severity, min(rate_429 * 5, 1.0))  # 10%→0.5, 20%→1.0

    # ── 2. 레이턴시 트렌드 감지 ──
    config = API_CONFIGS.get(api_name, {"baseline_latency_ms": 300})
    baseline_ms = config["baseline_latency_ms"]
    if len(recent_calls) >= 5:
        avg_latency = sum(c["latency_ms"] for c in recent_calls) / len(recent_calls)
        increase_ratio = (avg_latency - baseline_ms) / baseline_ms if baseline_ms > 0 else 0
        if increase_ratio > LATENCY_INCREASE_THRESHOLD:
            # 50% 증가 → severity 0.3, 100% → 0.6, 200% → 1.0
            latency_severity = min(increase_ratio * 0.5, 1.0)
            severity = max(severity, latency_severity)

    # ── 3. 버스트 감지 (30초 내 10회+) ──
    burst_calls = [c for c in calls if now - c["ts"] < BURST_DETECT_WINDOW_SEC]
    if len(burst_calls) >= BURST_THRESHOLD:
        burst_severity = min((len(burst_calls) - BURST_THRESHOLD + 1) / 10, 1.0)
        severity = max(severity, burst_severity)

    # ── 4. 시간대 패턴 (해당 시간 429 빈발) ──
    hourly_429 = state.get("hourly_429", {}).get(api_name, {})
    current_hour = datetime.now(timezone.utc).strftime("%H")
    hour_count = hourly_429.get(current_hour, 0)
    if hour_count >= 3:
        # 3회 → 0.15, 10회 → 0.5
        hour_severity = min(hour_count * 0.05, 0.5)
        severity = max(severity, hour_severity)

    if severity <= 0:
        return False, 0.0

    # 딜레이 계산: 0.5s ~ 5s 범위
    delay = MIN_DELAY + (MAX_DELAY - MIN_DELAY) * severity
    return True, round(delay, 2)


def get_throttle_stats() -> dict:
    """전체 API 호출 패턴 요약.

    Returns:
        {
            "api_name": {
                "total_calls": int,
                "calls_last_5min": int,
                "rate_429_5min": float,
                "avg_latency_ms": float,
                "burst_30s": int,
                "should_throttle": bool,
                "suggested_delay": float,
            },
            ...
        }
    """
    state = _load_state()
    now = time.time()
    stats = {}

    for api_name, calls in state.get("calls", {}).items():
        recent = [c for c in calls if now - c["ts"] < RATE_DETECT_WINDOW_SEC]
        burst = [c for c in calls if now - c["ts"] < BURST_DETECT_WINDOW_SEC]
        count_429 = sum(1 for c in recent if c["status"] == 429)

        throttle, delay = should_throttle(api_name)

        stats[api_name] = {
            "total_calls": len(calls),
            "calls_last_5min": len(recent),
            "rate_429_5min": round(count_429 / len(recent), 3) if recent else 0.0,
            "avg_latency_ms": round(
                sum(c["latency_ms"] for c in recent) / len(recent), 1
            ) if recent else 0.0,
            "burst_30s": len(burst),
            "should_throttle": throttle,
            "suggested_delay": delay,
        }

    return stats


def get_api_health() -> dict:
    """개별 API 건강 상태.

    Returns:
        {
            "api_name": {
                "status": "healthy" | "degraded" | "critical",
                "error_rate_1h": float,
                "avg_latency_ms": float,
                "last_429_ago_sec": float | None,
                "hourly_429_pattern": dict,
            },
            ...
            "overall": "healthy" | "degraded" | "critical",
        }
    """
    state = _load_state()
    now = time.time()
    health: dict = {}
    overall_status = "healthy"

    for api_name in set(list(state.get("calls", {}).keys()) + list(API_CONFIGS.keys())):
        calls = state.get("calls", {}).get(api_name, [])
        hourly_429 = state.get("hourly_429", {}).get(api_name, {})

        # 최근 1시간 에러율
        recent_1h = [c for c in calls if now - c["ts"] < ERROR_DETECT_WINDOW_SEC]
        error_count = sum(1 for c in recent_1h if c["status"] >= 400)
        error_rate = error_count / len(recent_1h) if recent_1h else 0.0

        # 평균 레이턴시
        avg_latency = (
            sum(c["latency_ms"] for c in recent_1h) / len(recent_1h)
            if recent_1h else 0.0
        )

        # 마지막 429
        last_429 = None
        for c in reversed(calls):
            if c["status"] == 429:
                last_429 = round(now - c["ts"], 1)
                break

        # 상태 판정
        if error_rate >= ERROR_RATE_DEGRADED:
            status = "critical" if error_rate >= 0.5 else "degraded"
        elif avg_latency > 0 and api_name in API_CONFIGS:
            baseline = API_CONFIGS[api_name]["baseline_latency_ms"]
            if avg_latency > baseline * 3:
                status = "degraded"
            else:
                status = "healthy"
        else:
            status = "healthy"

        health[api_name] = {
            "status": status,
            "error_rate_1h": round(error_rate, 3),
            "avg_latency_ms": round(avg_latency, 1),
            "last_429_ago_sec": last_429,
            "hourly_429_pattern": hourly_429,
        }

        # overall 집계
        if status == "critical":
            overall_status = "critical"
        elif status == "degraded" and overall_status != "critical":
            overall_status = "degraded"

    health["overall"] = overall_status
    return health


# ── CLI ───────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        stats = get_throttle_stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "health":
        health = get_api_health()
        print(json.dumps(health, ensure_ascii=False, indent=2))
    else:
        print("Usage: python scripts/api_throttler.py [stats|health]")
        print()
        health = get_api_health()
        print(f"Overall: {health.get('overall', 'unknown')}")
        for name, info in health.items():
            if name == "overall":
                continue
            print(f"  {name}: {info['status']} (err={info['error_rate_1h']:.1%}, lat={info['avg_latency_ms']:.0f}ms)")
