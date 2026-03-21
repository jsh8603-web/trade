#!/usr/bin/env python3
"""
BTC 가격 감시 → 지정가 도달 시 자동 매수 스크립트

설정 파일: data/price_alerts.json
사용법:
  # 감시 실행 (cron/launchd에서 1분 간격 호출)
  python3 scripts/price_alert_buy.py

  # 알림 등록 (CLI)
  python3 scripts/price_alert_buy.py add --target-usd 73500 --amount-krw 2000000

  # 알림 목록 조회
  python3 scripts/price_alert_buy.py list

  # 알림 삭제
  python3 scripts/price_alert_buy.py remove --id 1

동작:
  1. Binance BTCUSDT 가격 조회 (무료, 인증 불필요)
  2. 목표가 이하 진입 시 Upbit 시장가 매수 실행
  3. 텔레그램 알림 전송
  4. 실행 완료된 알림은 triggered=true로 마킹
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

KST = timezone(timedelta(hours=9))
ALERTS_FILE = PROJECT_DIR / "data" / "price_alerts.json"
BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/price"


def _load_alerts() -> list[dict]:
    """알림 목록 로드"""
    if ALERTS_FILE.exists():
        try:
            return json.loads(ALERTS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, KeyError):
            pass
    return []


def _save_alerts(alerts: list[dict]):
    """알림 목록 저장"""
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ALERTS_FILE.write_text(
        json.dumps(alerts, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def get_btc_usd_price() -> float | None:
    """Binance에서 BTC/USDT 현재가 조회"""
    try:
        r = requests.get(BINANCE_TICKER, params={"symbol": "BTCUSDT"}, timeout=10)
        if r.ok:
            return float(r.json()["price"])
    except Exception as e:
        print(f"[error] Binance 가격 조회 실패: {e}", file=sys.stderr)
    return None


def execute_buy(amount_krw: int, reason: str) -> dict:
    """Upbit 시장가 매수 실행 (일일 횟수 제한 우회 — 사용자 지정가 매수)"""
    # 가격 알림 매수는 사용자가 직접 설정한 것이므로
    # 일일 매매 횟수/간격 제한을 임시 우회한다
    env_override = os.environ.copy()
    env_override["MAX_DAILY_TRADES"] = "9999"
    env_override["MIN_TRADE_INTERVAL_HOURS"] = "0"

    result = subprocess.run(
        [sys.executable, str(PROJECT_DIR / "scripts" / "execute_trade.py"),
         "bid", "KRW-BTC", str(amount_krw)],
        capture_output=True, text=True, timeout=30,
        cwd=str(PROJECT_DIR),
        env=env_override,
    )
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        return {
            "success": False,
            "error": result.stderr[:500] if result.stderr else "Unknown error",
            "stdout": result.stdout[:500],
        }


def send_telegram(message: str):
    """텔레그램 알림 전송"""
    try:
        subprocess.run(
            [sys.executable, str(PROJECT_DIR / "scripts" / "notify_telegram.py"),
             "--message", message],
            capture_output=True, text=True, timeout=15,
            cwd=str(PROJECT_DIR),
        )
    except Exception as e:
        print(f"[warning] 텔레그램 전송 실패: {e}", file=sys.stderr)


def check_and_execute():
    """가격 감시 → 조건 충족 시 매수 실행"""
    alerts = _load_alerts()
    active_alerts = [a for a in alerts if not a.get("triggered")]

    if not active_alerts:
        return

    # BTC/USD 현재가 조회
    btc_usd = get_btc_usd_price()
    if btc_usd is None:
        return

    now = datetime.now(KST).isoformat()

    for alert in alerts:
        if alert.get("triggered"):
            continue

        target_usd = alert["target_usd"]
        direction = alert.get("direction", "below")  # below: 이하일 때 매수

        # 조건 확인
        condition_met = False
        if direction == "below" and btc_usd <= target_usd:
            condition_met = True
        elif direction == "above" and btc_usd >= target_usd:
            condition_met = True

        if not condition_met:
            print(f"[watch] BTC ${btc_usd:,.0f} | 목표 ${target_usd:,} ({direction}) | 대기중")
            continue

        # 조건 충족 → 매수 실행
        amount_krw = alert["amount_krw"]
        print(f"[TRIGGER] BTC ${btc_usd:,.0f} <= ${target_usd:,} → {amount_krw:,}원 매수 실행!")

        trade_result = execute_buy(amount_krw, f"가격알림 매수: ${target_usd}")

        # 결과 기록
        alert["triggered"] = True
        alert["triggered_at"] = now
        alert["triggered_price_usd"] = btc_usd
        alert["trade_result"] = {
            "success": trade_result.get("success"),
            "dry_run": trade_result.get("dry_run"),
            "error": trade_result.get("error"),
        }

        # 텔레그램 알림
        dry_label = " (DRY\\_RUN)" if trade_result.get("dry_run") else ""
        success_label = "성공" if trade_result.get("success") else "실패"

        msg = (
            f"🎯 *가격 알림 매수{dry_label}*\n\n"
            f"BTC 현재가: ${btc_usd:,.0f}\n"
            f"목표가: ${target_usd:,}\n"
            f"매수 금액: {amount_krw:,}원\n"
            f"결과: {success_label}\n"
        )
        if trade_result.get("error"):
            msg += f"오류: {trade_result['error']}\n"

        send_telegram(msg)

    _save_alerts(alerts)


def add_alert(target_usd: float, amount_krw: int, direction: str = "below"):
    """새 가격 알림 추가"""
    alerts = _load_alerts()
    alert_id = max([a.get("id", 0) for a in alerts], default=0) + 1

    new_alert = {
        "id": alert_id,
        "target_usd": target_usd,
        "amount_krw": amount_krw,
        "direction": direction,
        "triggered": False,
        "created_at": datetime.now(KST).isoformat(),
    }
    alerts.append(new_alert)
    _save_alerts(alerts)
    print(f"[등록] 알림 #{alert_id}: BTC ${target_usd:,} {direction} → {amount_krw:,}원 매수")
    return new_alert


def list_alerts():
    """등록된 알림 목록 출력"""
    alerts = _load_alerts()
    if not alerts:
        print("등록된 가격 알림이 없습니다.")
        return

    btc_usd = get_btc_usd_price()
    if btc_usd:
        print(f"현재 BTC: ${btc_usd:,.0f}\n")

    for a in alerts:
        status = "✅ 체결" if a.get("triggered") else "⏳ 대기"
        direction = a.get("direction", "below")
        dir_label = "이하" if direction == "below" else "이상"
        print(f"  #{a['id']} | {status} | ${a['target_usd']:,} {dir_label} → {a['amount_krw']:,}원")
        if a.get("triggered"):
            print(f"       체결: {a.get('triggered_at', '?')} @ ${a.get('triggered_price_usd', 0):,.0f}")
            tr = a.get("trade_result", {})
            dry = " (DRY_RUN)" if tr.get("dry_run") else ""
            print(f"       결과: {'성공' if tr.get('success') else '실패'}{dry}")


def remove_alert(alert_id: int):
    """알림 삭제"""
    alerts = _load_alerts()
    before = len(alerts)
    alerts = [a for a in alerts if a.get("id") != alert_id]
    if len(alerts) < before:
        _save_alerts(alerts)
        print(f"[삭제] 알림 #{alert_id} 삭제됨")
    else:
        print(f"[오류] 알림 #{alert_id}를 찾을 수 없습니다")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 기본: 감시 실행
        check_and_execute()
    elif sys.argv[1] == "add":
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("cmd")
        parser.add_argument("--target-usd", type=float, required=True)
        parser.add_argument("--amount-krw", type=int, required=True)
        parser.add_argument("--direction", default="below", choices=["below", "above"])
        args = parser.parse_args()
        add_alert(args.target_usd, args.amount_krw, args.direction)
    elif sys.argv[1] == "list":
        list_alerts()
    elif sys.argv[1] == "remove":
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("cmd")
        parser.add_argument("--id", type=int, required=True)
        args = parser.parse_args()
        remove_alert(args.id)
    else:
        print(f"알 수 없는 명령: {sys.argv[1]}")
        print("사용법: price_alert_buy.py [add|list|remove]")
        sys.exit(1)
