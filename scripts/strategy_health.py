#!/usr/bin/env python3
"""
Strategy Health Monitor — 전략 건강검진 및 텔레그램 알림

매매 전략의 성과를 모니터링하고, 성과 저하 시 텔레그램 알림을 전송한다.

기능:
  1. 최근 7일 매매 결정의 승률, 연패, 샤프비 등 건강 지표 산출
  2. 상태 판정: GREEN / YELLOW / ORANGE / RED
  3. 상태별 개선 제안 생성
  4. data/strategy_health.json에 상태 저장
  5. YELLOW 이상 시 텔레그램 알림

사용법:
  python scripts/strategy_health.py            # 전체 분석 + 텔레그램 알림
  python scripts/strategy_health.py --quiet    # 분석만 (텔레그램 없음)

파이프라인 통합:
  run_agents.py Phase 8에서 자동 호출
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
load_dotenv(PROJECT_DIR / ".env")

STATE_FILE = PROJECT_DIR / "data" / "strategy_health.json"
KST = timezone(timedelta(hours=9))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _fetch_recent_decisions(days: int = 7) -> list[dict]:
    """Supabase에서 최근 N일간 매매 결정을 조회한다."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    since = (datetime.now(KST) - timedelta(days=days)).isoformat()
    url = (
        f"{SUPABASE_URL}/rest/v1/decisions"
        f"?select=decision,confidence,outcome_4h_pct,outcome_24h_pct,"
        f"was_correct_4h,created_at,agent_name"
        f"&created_at=gte.{since}"
        f"&decision=in.(buy,sell)"
        f"&order=created_at.desc"
    )

    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def _calc_win_rate(decisions: list[dict]) -> float:
    """was_correct_4h 기준 승률을 계산한다."""
    evaluated = [d for d in decisions if d.get("was_correct_4h") is not None]
    if not evaluated:
        return 0.0
    wins = sum(1 for d in evaluated if d.get("was_correct_4h") is True)
    return wins / len(evaluated)


def _calc_consecutive_losses(decisions: list[dict]) -> int:
    """최근부터 연속 손실 횟수를 계산한다 (was_correct_4h=false 연속)."""
    streak = 0
    for d in decisions:  # already sorted by created_at desc
        if d.get("was_correct_4h") is None:
            continue
        if d.get("was_correct_4h") is False:
            streak += 1
        else:
            break
    return streak


def _calc_sharpe(decisions: list[dict]) -> float:
    """outcome_4h_pct 기반 샤프비를 계산한다."""
    outcomes = []
    for d in decisions:
        pct = d.get("outcome_4h_pct")
        if pct is not None:
            try:
                outcomes.append(float(pct))
            except (ValueError, TypeError):
                pass
    if len(outcomes) < 2:
        return 0.0
    mean = sum(outcomes) / len(outcomes)
    variance = sum((x - mean) ** 2 for x in outcomes) / (len(outcomes) - 1)
    std = math.sqrt(variance) if variance > 0 else 0.0
    if std == 0:
        return 0.0
    return mean / std


def _agent_win_rates(decisions: list[dict]) -> dict[str, float]:
    """에이전트별 승률을 계산한다."""
    agents: dict[str, list[bool]] = {}
    for d in decisions:
        agent = d.get("agent_name") or "unknown"
        if d.get("was_correct_4h") is not None:
            agents.setdefault(agent, []).append(d["was_correct_4h"] is True)
    return {
        agent: sum(wins) / len(wins) if wins else 0.0
        for agent, wins in agents.items()
    }


def _determine_status(win_rate: float, consecutive_losses: int) -> str:
    """건강 상태를 판정한다."""
    if win_rate < 0.25 or consecutive_losses >= 7:
        return "RED"
    if win_rate < 0.35 or consecutive_losses >= 5:
        return "ORANGE"
    if win_rate < 0.50 or consecutive_losses >= 3:
        return "YELLOW"
    return "GREEN"


def _status_emoji(status: str) -> str:
    emojis = {
        "GREEN": "\u2705",   # checkmark
        "YELLOW": "\u26a0\ufe0f",  # warning
        "ORANGE": "\U0001f7e0",     # orange circle
        "RED": "\U0001f6a8",        # alarm
    }
    return emojis.get(status, "\u2753")


def _status_label(status: str) -> str:
    labels = {
        "GREEN": "건강",
        "YELLOW": "주의",
        "ORANGE": "경고",
        "RED": "위험",
    }
    return labels.get(status, "알 수 없음")


def _generate_suggestion(
    status: str,
    total_trades: int,
    days_since_last_trade: float | None,
    worst_agent: str | None,
) -> str:
    """상태에 따른 개선 제안을 생성한다."""
    suggestions = []

    if days_since_last_trade is not None and days_since_last_trade >= 3:
        suggestions.append("3일간 시그널 없음. 현재 레짐에서 진입 조건 완화 검토")

    if status == "YELLOW":
        suggestions.append("최근 승률 하락 추세. 보수적 전환 고려")
    elif status == "ORANGE":
        msg = "전략 점검 필요. 에이전트별 성과 비교 후 최약 에이전트 비활성화 검토"
        if worst_agent:
            msg += f" (최약: {worst_agent})"
        suggestions.append(msg)
    elif status == "RED":
        suggestions.append("즉시 전략 수정 필요. 매매 금액 축소 또는 관망 전환 권고")

    return " / ".join(suggestions) if suggestions else "정상 운영 중"


def check_health(quiet: bool = False, cached_decisions: list[dict] | None = None) -> dict | None:
    """전략 건강검진을 수행한다.

    Args:
        quiet: True이면 텔레그램 알림을 보내지 않는다.
        cached_decisions: phase_cache에서 전달받은 캐시 데이터 (None이면 직접 조회)

    Returns:
        건강 상태 딕셔너리 또는 데이터 부족 시 None.
    """
    decisions_7d = cached_decisions if cached_decisions is not None else _fetch_recent_decisions(days=7)

    if not decisions_7d:
        result = {
            "status": "UNKNOWN",
            "win_rate_7d": 0.0,
            "win_rate_3d": 0.0,
            "avg_roi_7d": 0.0,
            "consecutive_losses": 0,
            "sharpe_7d": 0.0,
            "total_trades_7d": 0,
            "best_agent": None,
            "worst_agent": None,
            "suggestion": "데이터 없음. 최근 7일간 매매 기록이 없습니다.",
            "last_checked": datetime.now(KST).isoformat(),
        }
        _save_state(result)
        return result

    # 3일 필터
    three_days_ago = datetime.now(KST) - timedelta(days=3)
    decisions_3d = []
    for d in decisions_7d:
        try:
            created = datetime.fromisoformat(d["created_at"].replace("Z", "+00:00"))
            if created >= three_days_ago:
                decisions_3d.append(d)
        except (KeyError, ValueError):
            pass

    # 메트릭 계산
    win_rate_7d = _calc_win_rate(decisions_7d)
    win_rate_3d = _calc_win_rate(decisions_3d) if decisions_3d else 0.0
    consecutive_losses = _calc_consecutive_losses(decisions_7d)
    sharpe_7d = _calc_sharpe(decisions_7d)
    total_trades_7d = len(decisions_7d)

    outcomes = []
    for d in decisions_7d:
        pct = d.get("outcome_4h_pct")
        if pct is not None:
            try:
                outcomes.append(float(pct))
            except (ValueError, TypeError):
                pass
    avg_roi_7d = sum(outcomes) / len(outcomes) if outcomes else 0.0

    # 에이전트별 승률
    agent_wr = _agent_win_rates(decisions_7d)
    best_agent = max(agent_wr, key=agent_wr.get) if agent_wr else None
    worst_agent = min(agent_wr, key=agent_wr.get) if agent_wr else None

    # 마지막 거래 이후 경과일
    days_since_last = None
    if decisions_7d:
        try:
            last_dt = datetime.fromisoformat(
                decisions_7d[0]["created_at"].replace("Z", "+00:00")
            )
            days_since_last = (datetime.now(KST) - last_dt).total_seconds() / 86400
        except (KeyError, ValueError):
            pass

    status = _determine_status(win_rate_7d, consecutive_losses)
    suggestion = _generate_suggestion(status, total_trades_7d, days_since_last, worst_agent)

    result = {
        "status": status,
        "win_rate_7d": round(win_rate_7d, 4),
        "win_rate_3d": round(win_rate_3d, 4),
        "avg_roi_7d": round(avg_roi_7d, 4),
        "consecutive_losses": consecutive_losses,
        "sharpe_7d": round(sharpe_7d, 4),
        "total_trades_7d": total_trades_7d,
        "best_agent": best_agent,
        "worst_agent": worst_agent,
        "suggestion": suggestion,
        "last_checked": datetime.now(KST).isoformat(),
    }

    _save_state(result)

    # 텔레그램 알림 (YELLOW 이상만)
    if not quiet and status in ("YELLOW", "ORANGE", "RED"):
        _send_telegram_alert(result)

    return result


def _save_state(state: dict):
    """건강 상태를 JSON 파일에 저장한다 (atomic write)."""
    try:
        from scripts.atomic_write import atomic_json_save
        atomic_json_save(STATE_FILE, state)
    except ImportError:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as e:
        print(f"[strategy_health] 상태 저장 실패: {e}", file=sys.stderr)


def _send_telegram_alert(health: dict):
    """텔레그램으로 건강검진 결과를 전송한다."""
    try:
        from scripts.notify_telegram import send_message
    except ImportError:
        return

    status = health["status"]
    emoji = _status_emoji(status)
    label = _status_label(status)

    body_lines = [
        f"상태: {emoji} {status} ({label})",
        f"",
        f"승률 7일: {health['win_rate_7d']:.1%}",
        f"승률 3일: {health['win_rate_3d']:.1%}",
        f"평균 ROI 7일: {health['avg_roi_7d']:+.2f}%",
        f"연패: {health['consecutive_losses']}회",
        f"샤프비: {health['sharpe_7d']:.3f}",
        f"총 거래: {health['total_trades_7d']}건",
        f"",
        f"최고 에이전트: {health.get('best_agent', 'N/A')}",
        f"최약 에이전트: {health.get('worst_agent', 'N/A')}",
        f"",
        f"제안: {health['suggestion']}",
    ]

    send_message(
        msg_type="status",
        title=f"전략 건강검진: {emoji} {status}",
        body="\n".join(body_lines),
    )


def get_health_status() -> str:
    """저장된 상태 파일에서 현재 건강 상태를 반환한다."""
    summary = get_health_summary()
    return summary.get("status", "UNKNOWN")


def get_health_summary() -> dict:
    """저장된 건강 상태 전체를 반환한다."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"status": "UNKNOWN"}


if __name__ == "__main__":
    quiet = "--quiet" in sys.argv

    result = check_health(quiet=quiet)
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("건강검진 실패: 데이터를 가져올 수 없습니다.")
