#!/usr/bin/env python3
"""
Dynamic Risk — 롤링 Sharpe 기반 동적 리스크 조절

최근 7일 매매 성과(Sharpe ratio)를 기반으로 MAX_TRADE_AMOUNT를 자동 조정한다.
연속 손실 페널티도 적용하여 하락장에서 자산을 보전한다.

리스크 레벨:
  CRITICAL (Sharpe < -0.5) : -40%
  LOW      (Sharpe < 0)    : -20%
  NORMAL   (0 <= Sharpe < 0.5) : 기본값
  HIGH     (0.5 <= Sharpe < 1.5) : +10%
  BOOST    (Sharpe >= 1.5) : +20% (최대 2x)

연속 손실 페널티:
  3회+ : 추가 -20%
  5회+ : 최소값 강제 (기본의 30%)

사용법:
  python scripts/dynamic_risk.py          # 현재 리스크 상태 출력 + 업데이트

파이프라인 통합:
  run_agents.py Phase 8에서 자동 호출
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PROJECT_DIR = Path(__file__).resolve().parent.parent
import sys as _sys
if str(PROJECT_DIR) not in _sys.path:
    _sys.path.insert(0, str(PROJECT_DIR))
from core.db import db  # 로컬 DB 어댑터 (Supabase REST 대체)
STATE_FILE = PROJECT_DIR / "data" / "dynamic_risk.json"
KST = timezone(timedelta(hours=9))

# 기본 MAX_TRADE_AMOUNT
DEFAULT_MAX_AMOUNT = int(os.environ.get("MAX_TRADE_AMOUNT", "100000"))

# 최소 샘플 수 (이하면 기본값 사용)
MIN_SAMPLES = 3


def _fetch_recent_decisions(days: int = 7) -> list[dict]:
    """최근 N일간 매수/매도 결정을 로컬 DB에서 조회한다."""
    cutoff = (datetime.now(KST) - timedelta(days=days)).isoformat()

    try:
        return db.select(
            "decisions",
            filters={"created_at": f"gte.{cutoff}", "decision": "in.(매수,매도)"},
            order="created_at.asc",
            select="outcome_4h_pct,outcome_24h_pct,created_at,decision",
        )
    except Exception as e:
        print(f"[dynamic_risk] DB 조회 실패: {e}", file=sys.stderr)

    return []


def _calculate_sharpe(decisions: list[dict]) -> float | None:
    """outcome_4h_pct 값들로 Sharpe ratio를 계산한다."""
    returns = []
    for d in decisions:
        pct = d.get("outcome_4h_pct")
        if pct is not None:
            try:
                returns.append(float(pct))
            except (ValueError, TypeError):
                pass

    if len(returns) < MIN_SAMPLES:
        return None

    mean_r = sum(returns) / len(returns)
    variance = sum((r - mean_r) ** 2 for r in returns) / len(returns)
    std_r = variance ** 0.5

    if std_r == 0:
        return 0.0

    return mean_r / std_r


def _calculate_win_rate(decisions: list[dict]) -> float:
    """승률을 계산한다 (outcome_4h_pct > 0 비율)."""
    valid = []
    for d in decisions:
        pct = d.get("outcome_4h_pct")
        if pct is not None:
            try:
                valid.append(float(pct))
            except (ValueError, TypeError):
                pass

    if not valid:
        return 0.0

    wins = sum(1 for r in valid if r > 0)
    return round(wins / len(valid), 4)


def _count_consecutive_losses(decisions: list[dict]) -> int:
    """최근 연속 손실 횟수를 계산한다 (최신부터 역순)."""
    count = 0
    for d in reversed(decisions):
        pct = d.get("outcome_4h_pct")
        if pct is None:
            continue
        try:
            if float(pct) < 0:
                count += 1
            else:
                break
        except (ValueError, TypeError):
            continue
    return count


def _determine_risk_level(sharpe: float | None) -> tuple[str, float]:
    """
    Sharpe ratio에 따른 리스크 레벨과 조정 배율을 반환한다.

    Returns:
        (risk_level, multiplier)
    """
    if sharpe is None:
        return "NORMAL", 1.0

    if sharpe < -0.5:
        return "CRITICAL", 0.6   # -40%
    elif sharpe < 0:
        return "LOW", 0.8        # -20%
    elif sharpe < 0.5:
        return "NORMAL", 1.0
    elif sharpe < 1.5:
        return "HIGH", 1.1       # +10%
    else:
        return "BOOST", 1.2      # +20%


def update_risk(cached_decisions: list[dict] | None = None) -> dict:
    """
    동적 리스크를 재계산하고 상태 파일에 저장한다.

    Args:
        cached_decisions: phase_cache에서 전달받은 캐시 데이터 (None이면 직접 조회)

    Returns:
        리스크 상태 딕셔너리
    """
    decisions = cached_decisions if cached_decisions is not None else _fetch_recent_decisions(days=7)
    sharpe = _calculate_sharpe(decisions)
    win_rate = _calculate_win_rate(decisions)
    consec_losses = _count_consecutive_losses(decisions)

    # Sharpe 기반 리스크 레벨 및 배율
    risk_level, multiplier = _determine_risk_level(sharpe)

    # 연속 손실 페널티
    if consec_losses >= 5:
        # 5회+ 연속 손실: 최소값 강제 (기본의 30%)
        adjusted = int(DEFAULT_MAX_AMOUNT * 0.3)
        risk_level = "CRITICAL"
    elif consec_losses >= 3:
        # 3회+ 연속 손실: 추가 -20% (기존 배율에 곱)
        adjusted = int(DEFAULT_MAX_AMOUNT * multiplier * 0.8)
    else:
        adjusted = int(DEFAULT_MAX_AMOUNT * multiplier)

    # 상한: 기본값의 2배 초과 불가
    max_cap = DEFAULT_MAX_AMOUNT * 2
    adjusted = min(adjusted, max_cap)

    # 하한: 기본값의 30% 미만 불가 (최소 보장)
    min_floor = int(DEFAULT_MAX_AMOUNT * 0.3)
    adjusted = max(adjusted, min_floor)

    sample_count = len([
        d for d in decisions
        if d.get("outcome_4h_pct") is not None
    ])

    state = {
        "base_amount": DEFAULT_MAX_AMOUNT,
        "adjusted_amount": adjusted,
        "sharpe_7d": round(sharpe, 4) if sharpe is not None else None,
        "risk_level": risk_level,
        "sample_count": sample_count,
        "win_rate_7d": win_rate,
        "consecutive_losses": consec_losses,
        "last_updated": datetime.now(KST).isoformat(),
    }

    # 저장 (atomic write)
    try:
        from scripts.atomic_write import atomic_json_save
        atomic_json_save(STATE_FILE, state)
    except OSError as e:
        print(f"[dynamic_risk] 상태 저장 실패: {e}", file=sys.stderr)

    return state


def get_adjusted_max_amount() -> int | None:
    """
    저장된 동적 리스크 상태에서 조정된 MAX_TRADE_AMOUNT를 반환한다.
    상태 파일이 없거나 24시간 이상 오래된 경우 None을 반환한다.
    """
    if not STATE_FILE.exists():
        return None

    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    # 24시간 이상 오래된 상태는 무시
    last_updated = state.get("last_updated")
    if last_updated:
        try:
            updated_dt = datetime.fromisoformat(last_updated)
            if datetime.now(KST) - updated_dt > timedelta(hours=24):
                return None
        except (ValueError, TypeError):
            pass

    return state.get("adjusted_amount")


def get_risk_summary() -> dict:
    """저장된 리스크 상태 전체를 반환한다."""
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def main():
    """CLI: 리스크 상태 업데이트 및 출력."""
    print("=" * 50)
    print("  동적 리스크 조절 (7일 롤링 Sharpe)")
    print("=" * 50)

    state = update_risk()

    sharpe_str = f"{state['sharpe_7d']:.4f}" if state["sharpe_7d"] is not None else "N/A"
    print(f"\n  기본 금액:     {state['base_amount']:>10,}원")
    print(f"  조정 금액:     {state['adjusted_amount']:>10,}원")
    print(f"  Sharpe (7d):   {sharpe_str:>10}")
    print(f"  리스크 레벨:   {state['risk_level']:>10}")
    print(f"  샘플 수:       {state['sample_count']:>10}")
    print(f"  승률 (7d):     {state['win_rate_7d'] * 100:>9.1f}%")
    print(f"  연속 손실:     {state['consecutive_losses']:>10}회")
    print(f"  업데이트:      {state['last_updated']}")
    print()

    if state["sample_count"] < MIN_SAMPLES:
        print(f"  ⚠ 샘플 부족 ({state['sample_count']}/{MIN_SAMPLES}) — 기본값 사용")

    if state["consecutive_losses"] >= 5:
        print("  ⚠ 연속 5회+ 손실 — 최소 금액 강제 적용")
    elif state["consecutive_losses"] >= 3:
        print("  ⚠ 연속 3회+ 손실 — 추가 20% 감액 적용")


if __name__ == "__main__":
    main()
