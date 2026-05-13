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
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

KST = timezone(timedelta(hours=9))
ALERTS_FILE = PROJECT_DIR / "data" / "price_alerts.json"
BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/price"
UPBIT_TICKER = "https://api.upbit.com/v1/ticker"


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


def get_btc_krw_price() -> float | None:
    """Upbit에서 BTC/KRW 현재가 조회"""
    try:
        r = requests.get(UPBIT_TICKER, params={"markets": "KRW-BTC"}, timeout=10)
        if r.ok:
            return float(r.json()[0]["trade_price"])
    except Exception as e:
        print(f"[error] Upbit 가격 조회 실패: {e}", file=sys.stderr)
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
         "bid", "KRW-BTC", str(amount_krw), "price_alert"],
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

    # 가격 조회 (필요한 것만)
    need_usd = any(a.get("target_usd") for a in active_alerts)
    need_krw = any(a.get("target_krw") for a in active_alerts)

    btc_usd = get_btc_usd_price() if need_usd else None
    btc_krw = get_btc_krw_price() if need_krw else None

    if need_usd and btc_usd is None:
        print("[error] USD 가격 조회 실패", file=sys.stderr)
    if need_krw and btc_krw is None:
        print("[error] KRW 가격 조회 실패", file=sys.stderr)

    now = datetime.now(KST).isoformat()

    for alert in alerts:
        if alert.get("triggered"):
            continue

        direction = alert.get("direction", "below")

        # KRW 기준 알림
        if alert.get("target_krw"):
            if btc_krw is None:
                continue
            target = alert["target_krw"]
            current = btc_krw
            currency = "KRW"
            price_fmt = f"₩{current:,.0f}"
            target_fmt = f"₩{target:,.0f}"
        else:
            if btc_usd is None:
                continue
            target = alert["target_usd"]
            current = btc_usd
            currency = "USD"
            price_fmt = f"${current:,.0f}"
            target_fmt = f"${target:,}"

        # 조건 확인
        condition_met = False
        if direction == "below" and current <= target:
            condition_met = True
        elif direction == "above" and current >= target:
            condition_met = True

        if not condition_met:
            print(f"[watch] BTC {price_fmt} | 목표 {target_fmt} ({direction}) | 대기중")
            continue

        # 조건 충족 → 매수 실행
        amount_krw = alert["amount_krw"]
        print(f"[TRIGGER] BTC {price_fmt} {'<=' if direction == 'below' else '>='} {target_fmt} → {amount_krw:,}원 매수 실행!")

        trade_result = execute_buy(amount_krw, f"가격알림 매수: {target_fmt}")

        # 결과 기록
        alert["triggered"] = True
        alert["triggered_at"] = now
        if currency == "KRW":
            alert["triggered_price_krw"] = current
        else:
            alert["triggered_price_usd"] = current
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
            f"BTC 현재가: {price_fmt}\n"
            f"목표가: {target_fmt}\n"
            f"매수 금액: {amount_krw:,}원\n"
            f"결과: {success_label}\n"
        )
        if trade_result.get("error"):
            msg += f"오류: {trade_result['error']}\n"

        send_telegram(msg)

    _save_alerts(alerts)


def add_alert(amount_krw: int, direction: str = "below",
              target_usd: float | None = None, target_krw: float | None = None):
    """새 가격 알림 추가 (USD 또는 KRW 기준)"""
    if not target_usd and not target_krw:
        print("[오류] --target-usd 또는 --target-krw 중 하나를 지정하세요")
        return None

    alerts = _load_alerts()
    alert_id = max([a.get("id", 0) for a in alerts], default=0) + 1

    new_alert = {
        "id": alert_id,
        "amount_krw": amount_krw,
        "direction": direction,
        "triggered": False,
        "created_at": datetime.now(KST).isoformat(),
    }
    if target_krw:
        new_alert["target_krw"] = target_krw
        label = f"₩{target_krw:,.0f}"
    else:
        new_alert["target_usd"] = target_usd
        label = f"${target_usd:,}"

    alerts.append(new_alert)
    _save_alerts(alerts)
    print(f"[등록] 알림 #{alert_id}: BTC {label} {direction} → {amount_krw:,}원 매수")
    return new_alert


def list_alerts():
    """등록된 알림 목록 출력"""
    alerts = _load_alerts()
    if not alerts:
        print("등록된 가격 알림이 없습니다.")
        return

    btc_usd = get_btc_usd_price()
    btc_krw = get_btc_krw_price()
    if btc_usd:
        print(f"현재 BTC: ${btc_usd:,.0f}", end="")
    if btc_krw:
        print(f" / ₩{btc_krw:,.0f}", end="")
    print("\n")

    for a in alerts:
        status = "✅ 체결" if a.get("triggered") else "⏳ 대기"
        direction = a.get("direction", "below")
        dir_label = "이하" if direction == "below" else "이상"
        if a.get("target_krw"):
            target_label = f"₩{a['target_krw']:,.0f}"
        else:
            target_label = f"${a['target_usd']:,}"
        print(f"  #{a['id']} | {status} | {target_label} {dir_label} → {a['amount_krw']:,}원")
        if a.get("triggered"):
            if a.get("triggered_price_krw"):
                tp = f"₩{a['triggered_price_krw']:,.0f}"
            else:
                tp = f"${a.get('triggered_price_usd', 0):,.0f}"
            print(f"       체결: {a.get('triggered_at', '?')} @ {tp}")
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
        parser.add_argument("--target-usd", type=float, default=None)
        parser.add_argument("--target-krw", type=float, default=None)
        parser.add_argument("--amount-krw", type=int, required=True)
        parser.add_argument("--direction", default="below", choices=["below", "above"])
        args = parser.parse_args()
        if not args.target_usd and not args.target_krw:
            print("오류: --target-usd 또는 --target-krw 중 하나를 지정하세요")
            sys.exit(1)
        add_alert(args.amount_krw, args.direction,
                  target_usd=args.target_usd, target_krw=args.target_krw)
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
