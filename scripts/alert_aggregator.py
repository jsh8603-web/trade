#!/usr/bin/env python3
"""
알림 집계기 (Alert Aggregator)

여러 소스에서 건강/매매 알림을 수집하고, 심각도 티어별로 그룹화하여
텔레그램으로 전송한다. 동일 알림 반복 전송을 방지하는 안티스팸 메커니즘 내장.

티어:
  CRITICAL — 즉시 전송 (최소 10분 간격)
  HIGH     — 1시간 요약 전송
  MEDIUM   — 일일 요약 (08:00 KST)
  LOW      — 로그만 기록, 텔레그램 미전송

사용법:
  python scripts/alert_aggregator.py           # 전체 사이클 실행
  python scripts/alert_aggregator.py --dry-run # 수집만, 전송 안 함
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from dotenv import load_dotenv
load_dotenv(PROJECT_DIR / ".env")

KST = timezone(timedelta(hours=9))

# ── 경로 ────────────────────────────────────────────────
DATA_DIR = PROJECT_DIR / "data"
ALERT_STATE_PATH = DATA_DIR / "alert_state.json"
FEEDBACK_HUB_STATE_PATH = DATA_DIR / "feedback_hub_state.json"
STRATEGY_HEALTH_PATH = DATA_DIR / "strategy_health.json"
DYNAMIC_RISK_PATH = DATA_DIR / "dynamic_risk.json"
AUTO_EMERGENCY_PATH = DATA_DIR / "auto_emergency.json"
SENTINEL_SCRIPT = PROJECT_DIR / "scripts" / "lifeline" / "sentinel.py"

# ── 안티스팸 간격 ────────────────────────────────────────
CRITICAL_INTERVAL = timedelta(minutes=10)
HIGH_INTERVAL = timedelta(hours=1)
MEDIUM_HOUR = 8  # 08:00 KST
SUPPRESS_THRESHOLD = 3  # 동일 알림 3회 이상 반복 시 억제


def _now_kst() -> datetime:
    return datetime.now(KST)


def _load_json(path: Path) -> dict | None:
    """JSON 파일을 안전하게 로드한다."""
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _save_json(path: Path, data: dict) -> None:
    """JSON 파일을 안전하게 저장한다 (atomic write)."""
    try:
        from scripts.atomic_write import atomic_json_save
        atomic_json_save(path, data)
    except ImportError:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _load_alert_state() -> dict:
    """알림 상태 파일을 로드한다."""
    state = _load_json(ALERT_STATE_PATH)
    if state is None:
        state = {
            "last_critical_sent": None,
            "last_high_sent": None,
            "last_medium_sent": None,
            "active_alerts": [],
            "suppressed_count": 0,
            "alert_history": {},
        }
    return state


def _save_alert_state(state: dict) -> None:
    """알림 상태 파일을 저장한다."""
    _save_json(ALERT_STATE_PATH, state)


def _make_alert(tier: str, source: str, message: str) -> dict:
    """표준 알림 딕셔너리를 생성한다."""
    return {
        "tier": tier,
        "source": source,
        "message": message,
        "timestamp": _now_kst().isoformat(),
    }


# ── 소스별 알림 수집 ─────────────────────────────────────

def _collect_feedback_hub_alerts() -> list[dict]:
    """feedback_hub_state.json에서 비활성 모델, 낮은 정확도 알림을 수집한다."""
    alerts = []
    data = _load_json(FEEDBACK_HUB_STATE_PATH)
    if data is None:
        return alerts

    # 비활성 RL 모델
    disabled = data.get("disabled_rl_models", [])
    if disabled:
        models_str = ", ".join(disabled)
        alerts.append(_make_alert("HIGH", "feedback_hub", f"RL 모델 비활성: {models_str}"))

    # RAG 품질 저하
    rag = data.get("rag_quality", {})
    rag_acc = rag.get("rag_accuracy", 1.0)
    if rag_acc < 0.45 and rag.get("rag_samples", 0) >= 5:
        alerts.append(_make_alert("MEDIUM", "feedback_hub", f"RAG 정확도 저하: {rag_acc:.1%}"))

    return alerts


def _collect_strategy_health_alerts() -> list[dict]:
    """strategy_health.json에서 건강 상태 알림을 수집한다."""
    alerts = []
    data = _load_json(STRATEGY_HEALTH_PATH)
    if data is None:
        return alerts

    status = data.get("status", "GREEN")
    win_rate = data.get("win_rate_7d", data.get("win_rate", 0))
    consecutive_losses = data.get("consecutive_losses", 0)
    detail_parts = []
    if win_rate:
        # win_rate is 0~1 ratio, display as percentage
        if isinstance(win_rate, (int, float)) and win_rate <= 1:
            detail_parts.append(f"승률 {win_rate:.0%}")
        else:
            detail_parts.append(f"승률 {win_rate}%")
    if consecutive_losses:
        detail_parts.append(f"연패 {consecutive_losses}회")
    detail = ", ".join(detail_parts) if detail_parts else "상세 정보 없음"

    if status == "RED":
        alerts.append(_make_alert("CRITICAL", "strategy_health", f"전략 건강 RED — {detail}"))
    elif status == "ORANGE":
        alerts.append(_make_alert("HIGH", "strategy_health", f"전략 건강 ORANGE — {detail}"))
    elif status == "YELLOW":
        alerts.append(_make_alert("MEDIUM", "strategy_health", f"전략 건강 YELLOW — {detail}"))

    # 연속 손실 5회 이상
    if consecutive_losses >= 5:
        alerts.append(_make_alert("HIGH", "strategy_health",
                                  f"연속 손실 {consecutive_losses}회"))

    return alerts


def _collect_dynamic_risk_alerts() -> list[dict]:
    """dynamic_risk.json에서 리스크 레벨 알림을 수집한다."""
    alerts = []
    data = _load_json(DYNAMIC_RISK_PATH)
    if data is None:
        return alerts

    risk_level = data.get("risk_level", "NORMAL")
    sharpe = data.get("sharpe_7d")  # can be None
    trade_amount = data.get("adjusted_amount", 0)
    win_rate = data.get("win_rate_7d", 0)  # 0~1 ratio

    sharpe_str = f"{sharpe:.2f}" if sharpe is not None else "N/A"

    if risk_level == "CRITICAL":
        alerts.append(_make_alert("CRITICAL", "dynamic_risk",
                                  f"동적 리스크 CRITICAL — Sharpe {sharpe_str}"))
    elif risk_level == "LOW":
        detail = f"Sharpe {sharpe_str}"
        if trade_amount:
            detail += f", 매매액 {trade_amount:,.0f}원"
        alerts.append(_make_alert("HIGH", "dynamic_risk", f"동적 리스크 LOW — {detail}"))
    elif risk_level == "NORMAL" and win_rate and win_rate < 0.45:
        alerts.append(_make_alert("MEDIUM", "dynamic_risk",
                                  f"리스크 NORMAL이나 승률 {win_rate:.0%} 저조"))

    return alerts


def _collect_emergency_alerts() -> list[dict]:
    """auto_emergency.json 및 .env EMERGENCY_STOP 확인."""
    alerts = []

    # .env EMERGENCY_STOP
    if os.environ.get("EMERGENCY_STOP", "").lower() == "true":
        alerts.append(_make_alert("CRITICAL", "emergency",
                                  "EMERGENCY_STOP 활성 (수동 설정)"))

    # auto_emergency.json
    data = _load_json(AUTO_EMERGENCY_PATH)
    if data and data.get("active", False):
        reason = data.get("reason", "알 수 없음")
        alerts.append(_make_alert("CRITICAL", "auto_emergency",
                                  f"자동 긴급정지 활성 — {reason}"))

    return alerts


# Sentinel 결과 캐시 (5분 TTL)
_sentinel_cache: dict = {"data": None, "ts": 0.0}
_SENTINEL_CACHE_TTL = 300  # 5분


def _collect_sentinel_alerts() -> list[dict]:
    """sentinel.py를 실행하여 점검 결과에서 알림을 수집한다.

    결과를 5분간 캐시하여 반복 호출 시 API 재호출을 방지한다.
    """
    import time as _time
    alerts = []

    if not SENTINEL_SCRIPT.exists():
        return alerts

    # 캐시 확인
    now = _time.monotonic()
    if _sentinel_cache["data"] is not None and (now - _sentinel_cache["ts"]) < _SENTINEL_CACHE_TTL:
        sentinel_data = _sentinel_cache["data"]
    else:
        try:
            result = subprocess.run(
                [sys.executable, str(SENTINEL_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(PROJECT_DIR),
            )
            output = result.stdout.strip()
            if not output:
                return alerts

            sentinel_data = json.loads(output)
            _sentinel_cache["data"] = sentinel_data
            _sentinel_cache["ts"] = now
        except subprocess.TimeoutExpired:
            alerts.append(_make_alert("HIGH", "sentinel", "Sentinel 점검 타임아웃 (60s)"))
            return alerts
        except (json.JSONDecodeError, OSError) as e:
            alerts.append(_make_alert("MEDIUM", "sentinel", f"Sentinel 파싱 실패: {e}"))
            return alerts

    checks = sentinel_data.get("checks", [])

    for check in checks:
        component = check.get("component", "unknown")
        status = check.get("status", "OK")
        message = check.get("message", "")

        if status == "CRITICAL":
            alerts.append(_make_alert("CRITICAL", f"sentinel_{component}", message))
        elif status == "ERROR":
            alerts.append(_make_alert("HIGH", f"sentinel_{component}", message))
        elif status == "WARNING":
            # 디스크/메모리/stale lock 경고
            alerts.append(_make_alert("HIGH", f"sentinel_{component}", message))

    return alerts


# ── 메인 수집 함수 ────────────────────────────────────────

def collect_alerts() -> list[dict]:
    """모든 소스에서 알림을 수집하여 리스트로 반환한다."""
    alerts: list[dict] = []
    alerts.extend(_collect_emergency_alerts())
    alerts.extend(_collect_strategy_health_alerts())
    alerts.extend(_collect_dynamic_risk_alerts())
    alerts.extend(_collect_feedback_hub_alerts())
    alerts.extend(_collect_sentinel_alerts())
    return alerts


def get_active_alerts() -> list[dict]:
    """현재 활성 알림을 반환한다 (수집만, 전송 안 함)."""
    return collect_alerts()


# ── 안티스팸 판단 ─────────────────────────────────────────

def _should_send(tier: str, alert_key: str, state: dict) -> bool:
    """안티스팸 규칙에 따라 전송 여부를 판단한다."""
    now = _now_kst()

    # 반복 횟수 확인
    history = state.get("alert_history", {})
    entry = history.get(alert_key, {"count": 0, "last_sent": None})
    if entry["count"] >= SUPPRESS_THRESHOLD:
        return False

    if tier == "CRITICAL":
        last_sent_str = state.get("last_critical_sent")
        if last_sent_str:
            try:
                last_sent = datetime.fromisoformat(last_sent_str)
                if now - last_sent < CRITICAL_INTERVAL:
                    return False
            except (ValueError, TypeError):
                pass  # corrupted timestamp → allow sending
        return True

    elif tier == "HIGH":
        last_sent_str = state.get("last_high_sent")
        if last_sent_str:
            try:
                last_sent = datetime.fromisoformat(last_sent_str)
                if now - last_sent < HIGH_INTERVAL:
                    return False
            except (ValueError, TypeError):
                pass
        return True

    elif tier == "MEDIUM":
        last_sent_str = state.get("last_medium_sent")
        if last_sent_str:
            try:
                last_sent = datetime.fromisoformat(last_sent_str)
                # 같은 날 이미 전송했으면 스킵
                if last_sent.date() == now.date():
                    return False
            except (ValueError, TypeError):
                pass
        # 08:00 KST 이후에만 전송
        return now.hour >= MEDIUM_HOUR

    return False


def _update_history(state: dict, alert_key: str) -> None:
    """알림 히스토리를 업데이트한다."""
    history = state.setdefault("alert_history", {})
    if alert_key not in history:
        history[alert_key] = {"count": 0, "last_sent": None}
    history[alert_key]["count"] += 1
    history[alert_key]["last_sent"] = _now_kst().isoformat()


def _reset_stale_history(state: dict) -> None:
    """24시간 이상 지난 히스토리 항목을 초기화한다."""
    now = _now_kst()
    history = state.get("alert_history", {})
    stale_keys = []
    for key, entry in history.items():
        last_sent_str = entry.get("last_sent")
        if last_sent_str:
            try:
                last_sent = datetime.fromisoformat(last_sent_str)
                if now - last_sent > timedelta(hours=24):
                    stale_keys.append(key)
            except (ValueError, TypeError):
                stale_keys.append(key)  # corrupted timestamp → treat as stale
    for key in stale_keys:
        del history[key]


# ── 텔레그램 전송 ────────────────────────────────────────

def _format_critical(alert: dict) -> tuple[str, str]:
    """CRITICAL 알림 포맷."""
    title = "시스템 긴급 알림 (CRITICAL)"
    body = f"• {alert['source']}: {alert['message']}"
    return title, body


def _format_high_group(alerts: list[dict]) -> tuple[str, str]:
    """HIGH 알림 그룹 포맷."""
    title = "시스템 알림 (HIGH)"
    lines = []
    for a in alerts:
        lines.append(f"• {a['message']}")
    now_str = _now_kst().strftime("%H:%M KST")
    body = "\n".join(lines) + f"\n\n마지막 점검: {now_str}"
    return title, body


def _format_medium_group(alerts: list[dict]) -> tuple[str, str]:
    """MEDIUM 일일 요약 포맷."""
    title = "일일 시스템 요약 (MEDIUM)"
    lines = []
    for a in alerts:
        lines.append(f"• {a['message']}")
    now_str = _now_kst().strftime("%Y-%m-%d %H:%M KST")
    body = "\n".join(lines) + f"\n\n점검 시각: {now_str}"
    return title, body


def _send_telegram(title: str, body: str) -> bool:
    """텔레그램 메시지를 전송한다."""
    try:
        from scripts.notify_telegram import send_message
        send_message("status", title, body)
        return True
    except Exception as e:
        print(f"[alert_aggregator] 텔레그램 전송 실패: {e}", file=sys.stderr)
        return False


# ── 집계 + 전송 ──────────────────────────────────────────

def aggregate_and_send(dry_run: bool = False) -> dict:
    """알림을 수집하고, 티어별로 그룹화하여 전송한다.

    Returns:
        dict: {"sent_count": int, "suppressed_count": int,
               "alerts": list, "tiers": dict}
    """
    alerts = collect_alerts()
    state = _load_alert_state()
    _reset_stale_history(state)

    # 티어별 분류
    tiers: dict[str, list[dict]] = {
        "CRITICAL": [],
        "HIGH": [],
        "MEDIUM": [],
        "LOW": [],
    }
    for alert in alerts:
        tier = alert.get("tier", "LOW")
        tiers.setdefault(tier, []).append(alert)

    # 알림이 없으면 LOW로 분류
    if not alerts:
        tiers["LOW"].append(_make_alert("LOW", "system", "모든 시스템 정상"))

    sent_count = 0
    suppressed_count = 0
    now = _now_kst()

    # CRITICAL: 개별 즉시 전송
    for alert in tiers["CRITICAL"]:
        alert_key = f"{alert['source']}:{alert['message']}"
        if _should_send("CRITICAL", alert_key, state):
            if not dry_run:
                title, body = _format_critical(alert)
                if _send_telegram(title, body):
                    sent_count += 1
                    state["last_critical_sent"] = now.isoformat()
                    _update_history(state, alert_key)
            else:
                sent_count += 1
                print(f"[DRY-RUN] CRITICAL: {alert['message']}")
        else:
            suppressed_count += 1

    # HIGH: 그룹 전송
    if tiers["HIGH"]:
        # HIGH 전체를 하나의 키로 판단
        high_key = "HIGH:" + "|".join(sorted(a["source"] for a in tiers["HIGH"]))
        if _should_send("HIGH", high_key, state):
            if not dry_run:
                title, body = _format_high_group(tiers["HIGH"])
                if _send_telegram(title, body):
                    sent_count += 1
                    state["last_high_sent"] = now.isoformat()
                    _update_history(state, high_key)
            else:
                sent_count += 1
                print(f"[DRY-RUN] HIGH ({len(tiers['HIGH'])}건):")
                for a in tiers["HIGH"]:
                    print(f"  • {a['message']}")
        else:
            suppressed_count += len(tiers["HIGH"])

    # MEDIUM: 일일 요약
    if tiers["MEDIUM"]:
        medium_key = "MEDIUM:daily"
        if _should_send("MEDIUM", medium_key, state):
            if not dry_run:
                title, body = _format_medium_group(tiers["MEDIUM"])
                if _send_telegram(title, body):
                    sent_count += 1
                    state["last_medium_sent"] = now.isoformat()
                    _update_history(state, medium_key)
            else:
                sent_count += 1
                print(f"[DRY-RUN] MEDIUM ({len(tiers['MEDIUM'])}건):")
                for a in tiers["MEDIUM"]:
                    print(f"  • {a['message']}")
        else:
            suppressed_count += len(tiers["MEDIUM"])

    # 상태 저장
    state["active_alerts"] = alerts
    state["suppressed_count"] = suppressed_count
    _save_alert_state(state)

    summary = {
        "sent_count": sent_count,
        "suppressed_count": suppressed_count,
        "alerts": alerts,
        "tiers": {tier: len(items) for tier, items in tiers.items()},
    }

    return summary


# ── CLI ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="알림 집계기")
    parser.add_argument("--dry-run", action="store_true",
                        help="수집만 하고 텔레그램 전송 안 함")
    args = parser.parse_args()

    result = aggregate_and_send(dry_run=args.dry_run)

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

    # 종료 코드: CRITICAL이 있으면 1
    if result["tiers"].get("CRITICAL", 0) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
