"""변동성 돌파(Larry Williams) 자동 매매 — 매수/24h 청산 전용.

매일 BREAKOUT_TRADE_TIME_KST(기본 10:00) 정각에 1회 실행.
손절(-2%) 감시는 별도 `breakout_monitor.py`가 담당.

룰:
  Range  = 어제 일봉 (high - low)
  Target = 오늘 시초가 + Range × K (기본 0.7)
  현재가 >= Target  →  매수 (BUY)
  보유 중 + 24h 경과  →  청산 (SELL)
  보유 중 + 24h 미경과  →  대기 (monitor가 손절 감시)

운영 정책:
  - 포지션 보유 시: 청산만, 같은 날 신규 매수 X
  - KRW 잔고 부족 시: 매수 스킵
  - EMERGENCY_STOP=true: 매수 차단 (청산은 허용)
  - BREAKOUT_DRY_RUN=true: API 호출 X, 시뮬만
  - 시그널 없는 날도 텔레그램 알림 (BREAKOUT_NOTIFY_NO_SIGNAL=true)
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import jwt
import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(PROJECT_DIR / ".env", override=True)

KST = timezone(timedelta(hours=9))
UPBIT_API = "https://api.upbit.com/v1"
STATE_PATH = PROJECT_DIR / "data" / "breakout_state.json"
LOG_DIR = PROJECT_DIR / "logs" / "breakout"
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ─── 환경변수 ──────────────────────────────────────────

def cfg() -> dict:
    return {
        "enabled": os.getenv("BREAKOUT_ENABLED", "true").lower() == "true",
        "dry_run": os.getenv("BREAKOUT_DRY_RUN", "true").lower() == "true",
        "k": float(os.getenv("BREAKOUT_K", "0.7")),
        "buy_amount": int(os.getenv("BREAKOUT_BUY_AMOUNT", "300000")),
        "stop_loss_pct": float(os.getenv("BREAKOUT_STOP_LOSS_PCT", "-2.0")),
        "time_exit_h": float(os.getenv("BREAKOUT_TIME_EXIT_HOURS", "24")),
        "notify_no_signal": os.getenv("BREAKOUT_NOTIFY_NO_SIGNAL", "true").lower() == "true",
        "emergency_stop": os.getenv("EMERGENCY_STOP", "false").lower() == "true",
    }


# ─── 로깅 ────────────────────────────────────────────

def _log(msg: str) -> None:
    ts = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    log_file = LOG_DIR / f"{datetime.now(KST).strftime('%Y%m%d')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ─── State 관리 ──────────────────────────────────────

def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"active_position": None, "history": [], "last_check": None, "last_signal": None}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ─── Upbit API ───────────────────────────────────────

def _auth_headers(query_string: str = "") -> dict:
    access = os.environ["UPBIT_ACCESS_KEY"]
    secret = os.environ["UPBIT_SECRET_KEY"]
    payload = {"access_key": access, "nonce": str(uuid.uuid4())}
    if query_string:
        import hashlib
        payload["query_hash"] = hashlib.sha512(query_string.encode()).hexdigest()
        payload["query_hash_alg"] = "SHA512"
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def get_current_btc_price() -> float:
    """공개 API — 인증 불필요."""
    r = requests.get(f"{UPBIT_API}/ticker", params={"markets": "KRW-BTC"}, timeout=10)
    r.raise_for_status()
    return float(r.json()[0]["trade_price"])


def get_yesterday_ohlc() -> dict:
    """어제 일봉 OHLC — `to=오늘 KST 자정` count=2 후 어제 1개."""
    today_midnight_kst = datetime.now(KST).replace(hour=0, minute=0, second=0, microsecond=0)
    to_str = today_midnight_kst.strftime("%Y-%m-%d %H:%M:%S")
    r = requests.get(
        f"{UPBIT_API}/candles/days",
        params={"market": "KRW-BTC", "count": 1, "to": to_str},
        timeout=10,
    )
    r.raise_for_status()
    c = r.json()[0]
    return {
        "open": float(c["opening_price"]),
        "high": float(c["high_price"]),
        "low": float(c["low_price"]),
        "close": float(c["trade_price"]),
        "date": c["candle_date_time_kst"][:10],
    }


def get_today_open() -> float:
    """오늘 일봉 시초가 (오늘 자정 ~ 현재까지의 일봉)."""
    r = requests.get(
        f"{UPBIT_API}/candles/days",
        params={"market": "KRW-BTC", "count": 1},
        timeout=10,
    )
    r.raise_for_status()
    return float(r.json()[0]["opening_price"])


def get_krw_balance() -> float:
    r = requests.get(f"{UPBIT_API}/accounts", headers=_auth_headers(), timeout=10)
    r.raise_for_status()
    for acc in r.json():
        if acc["currency"] == "KRW":
            return float(acc["balance"])
    return 0.0


def upbit_buy_market(krw_amount: int) -> dict:
    """시장가 매수 (KRW 기준). Upbit는 ord_type=price + price=KRW로 시장가 매수."""
    body = {"market": "KRW-BTC", "side": "bid", "ord_type": "price", "price": str(krw_amount)}
    qs = urlencode(body)
    headers = _auth_headers(qs)
    r = requests.post(f"{UPBIT_API}/orders", json=body, headers=headers, timeout=10)
    r.raise_for_status()
    order = r.json()
    # 체결 확인 (시장가는 즉시 체결되지만 잠시 대기)
    time.sleep(2)
    return _fetch_order_detail(order["uuid"])


def upbit_sell_market(btc_volume: float) -> dict:
    body = {"market": "KRW-BTC", "side": "ask", "ord_type": "market", "volume": f"{btc_volume:.8f}"}
    qs = urlencode(body)
    headers = _auth_headers(qs)
    r = requests.post(f"{UPBIT_API}/orders", json=body, headers=headers, timeout=10)
    r.raise_for_status()
    order = r.json()
    time.sleep(2)
    return _fetch_order_detail(order["uuid"])


def _fetch_order_detail(order_uuid: str) -> dict:
    """체결된 주문 상세 — executed_volume, avg_price 추출."""
    qs = urlencode({"uuid": order_uuid})
    headers = _auth_headers(qs)
    r = requests.get(f"{UPBIT_API}/order", params={"uuid": order_uuid}, headers=headers, timeout=10)
    r.raise_for_status()
    detail = r.json()
    trades = detail.get("trades", [])
    if trades:
        total_funds = sum(float(t["funds"]) for t in trades)
        total_volume = sum(float(t["volume"]) for t in trades)
        avg_price = total_funds / total_volume if total_volume > 0 else 0
    else:
        avg_price = float(detail.get("price", 0)) if detail.get("price") else 0
        total_volume = float(detail.get("executed_volume", 0))
        total_funds = avg_price * total_volume
    return {
        "uuid": order_uuid,
        "executed_volume": total_volume,
        "avg_price": avg_price,
        "executed_funds": total_funds,
        "paid_fee": float(detail.get("paid_fee", 0)),
        "raw": detail,
    }


# ─── Supabase 결정 기록 ──────────────────────────────────

def _supabase_headers() -> dict:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def save_breakout_decision(
    decision: str,
    reason: str,
    confidence: float,
    current_price: float,
    market_snapshot: dict,
    trade_result: dict | None = None,
    dry_run: bool = False,
) -> None:
    """Breakout 매매 결정을 Supabase decisions 테이블에 저장한다."""
    url = os.environ.get("SUPABASE_URL")
    if not url:
        _log("[DB] SUPABASE_URL 미설정 — 저장 스킵")
        return

    DECISION_MAP = {"buy": "매수", "sell": "매도", "hold": "관망"}
    try:
        from utils.machine import get_machine_name
        machine = get_machine_name()
    except Exception:
        machine = os.getenv("MACHINE_NAME", "unknown")

    row = {
        "market": "KRW-BTC",
        "decision": DECISION_MAP.get(decision, decision),
        "confidence": round(min(1.0, max(0.0, confidence)), 2),
        "reason": reason,
        "current_price": int(current_price),
        "rsi_value": market_snapshot.get("rsi"),
        "fear_greed_value": market_snapshot.get("fgi"),
        "market_data_snapshot": json.dumps(market_snapshot, ensure_ascii=False),
        "source": "breakout",
        "machine_name": machine,
    }

    # 체결 결과 포함
    if trade_result:
        row["execution_result"] = json.dumps(trade_result, ensure_ascii=False)

    try:
        resp = requests.post(
            f"{url}/rest/v1/decisions",
            json=row,
            headers=_supabase_headers(),
            timeout=10,
        )
        if resp.status_code in (200, 201):
            _log("[DB] breakout 결정 기록 완료")
        else:
            _log(f"[DB] 기록 실패 (HTTP {resp.status_code}): {resp.text[:200]}")
    except Exception as e:
        _log(f"[DB] 기록 예외: {e}")


# ─── 텔레그램 알림 ──────────────────────────────────────

def notify(text: str) -> None:
    """notify_telegram.send_message 직접 호출."""
    try:
        from scripts.notify_telegram import send_message
        send_message("trade", "[변동성 돌파]", text)
    except Exception as e:
        _log(f"텔레그램 알림 실패 (무시): {e}")


# ─── 매매 로직 ──────────────────────────────────────

def execute_buy(target_price: float, current_price: float, c: dict) -> dict | None:
    """매수 실행. 반환: 새 active_position dict 또는 None(실패)."""
    krw = get_krw_balance() if not c["dry_run"] else 1_000_000
    if krw < c["buy_amount"]:
        msg = f"BUY 시그널이지만 KRW 부족 ({krw:,.0f} < {c['buy_amount']:,}) — 스킵"
        _log(msg)
        notify(msg)
        return None

    if c["dry_run"]:
        # 시뮬: 슬리피지 0.03% + 수수료 0.05% 가정
        actual_price = current_price * 1.0003
        btc_volume = c["buy_amount"] * (1 - 0.0005) / actual_price
        order = {
            "uuid": f"dry-{uuid.uuid4()}",
            "executed_volume": btc_volume,
            "avg_price": actual_price,
            "executed_funds": c["buy_amount"],
            "paid_fee": c["buy_amount"] * 0.0005,
        }
        _log(f"[DRY_RUN] 매수 시뮬: {actual_price:,.0f}원 × {btc_volume:.8f} BTC")
    else:
        try:
            order = upbit_buy_market(c["buy_amount"])
            _log(f"매수 완료: {order['avg_price']:,.0f}원 × {order['executed_volume']:.8f} BTC (uuid={order['uuid']})")
        except Exception as e:
            _log(f"매수 실패: {e}")
            notify(f"🚨 매수 실패\n에러: {e}\n다음 시도: 내일 {os.getenv('BREAKOUT_TRADE_TIME_KST', '10:00')}")
            return None

    now_kst = datetime.now(KST)
    pos = {
        "buy_price": order["avg_price"],
        "btc_volume": order["executed_volume"],
        "krw_amount": int(order["executed_funds"]),
        "entered_at": now_kst.isoformat(),
        "stop_loss_price": order["avg_price"] * (1 + c["stop_loss_pct"] / 100),
        "target_exit_at": (now_kst + timedelta(hours=c["time_exit_h"])).isoformat(),
        "buy_order_uuid": order["uuid"],
        "K": c["k"],
        "fee_paid_krw": order["paid_fee"],
        "target_price": target_price,
        "dry_run": c["dry_run"],
    }

    icon = "🐂"
    mode = "[DRY_RUN] " if c["dry_run"] else ""
    notify(
        f"{icon} {mode}매수 완료\n"
        f"   가격: {order['avg_price']:,.0f}원\n"
        f"   양: {order['executed_volume']:.8f} BTC\n"
        f"   투입: {int(order['executed_funds']):,}원 (수수료 {int(order['paid_fee']):,}원)\n"
        f"   손절선: {pos['stop_loss_price']:,.0f}원 ({c['stop_loss_pct']}%)\n"
        f"   24h 청산: {(now_kst + timedelta(hours=c['time_exit_h'])).strftime('%m/%d %H:%M')} KST\n"
        f"   주문: {order['uuid'][:8]}..."
    )
    return pos


def execute_sell(pos: dict, c: dict, reason: str) -> dict | None:
    """청산 실행. 반환: history 항목 dict 또는 None."""
    if c["dry_run"]:
        current_price = get_current_btc_price()
        actual_price = current_price * 0.9997  # 매도 슬리피지
        order = {
            "uuid": f"dry-sell-{uuid.uuid4()}",
            "executed_volume": pos["btc_volume"],
            "avg_price": actual_price,
            "executed_funds": pos["btc_volume"] * actual_price,
            "paid_fee": pos["btc_volume"] * actual_price * 0.0005,
        }
        _log(f"[DRY_RUN] 매도 시뮬: {actual_price:,.0f}원 × {pos['btc_volume']:.8f} BTC")
    else:
        try:
            order = upbit_sell_market(pos["btc_volume"])
            _log(f"매도 완료: {order['avg_price']:,.0f}원 × {order['executed_volume']:.8f} BTC (uuid={order['uuid']})")
        except Exception as e:
            _log(f"매도 실패: {e}")
            notify(f"🚨 매도 실패\n사유: {reason}\n에러: {e}")
            return None

    pnl_pct = (order["avg_price"] - pos["buy_price"]) / pos["buy_price"] * 100
    pnl_krw = int(order["executed_funds"] - pos["krw_amount"] - order["paid_fee"])

    icon = "⚠️" if "손절" in reason else "🚀"
    mode = "[DRY_RUN] " if c["dry_run"] else ""
    notify(
        f"{icon} {mode}매도 완료 ({reason})\n"
        f"   매수 {pos['buy_price']:,.0f} → 매도 {order['avg_price']:,.0f}\n"
        f"   양: {pos['btc_volume']:.8f} BTC\n"
        f"   손익: {pnl_pct:+.2f}% ({pnl_krw:+,}원, 수수료 후)"
    )

    return {
        "entered_at": pos["entered_at"],
        "exited_at": datetime.now(KST).isoformat(),
        "exit_reason": reason,
        "buy_price": pos["buy_price"],
        "exit_price": order["avg_price"],
        "btc_volume": pos["btc_volume"],
        "krw_amount": pos["krw_amount"],
        "pnl_krw": pnl_krw,
        "pnl_pct": round(pnl_pct, 4),
        "buy_order_uuid": pos.get("buy_order_uuid"),
        "sell_order_uuid": order["uuid"],
        "dry_run": c["dry_run"],
    }


# ─── 메인 흐름 ──────────────────────────────────────

def main() -> int:
    c = cfg()
    _log(f"breakout_trader 시작 (dry_run={c['dry_run']}, K={c['k']}, buy={c['buy_amount']:,})")

    if not c["enabled"]:
        _log("BREAKOUT_ENABLED=false — 종료")
        return 0

    state = load_state()
    state["last_check"] = datetime.now(KST).isoformat()

    # 1) 보유 중이면 청산 평가만
    pos = state.get("active_position")
    if pos:
        entered = datetime.fromisoformat(pos["entered_at"])
        elapsed_h = (datetime.now(KST) - entered).total_seconds() / 3600
        if elapsed_h >= c["time_exit_h"]:
            _log(f"24h 청산 시점 도래 ({elapsed_h:.1f}h 경과)")
            current_price = get_current_btc_price()
            history_item = execute_sell(pos, c, reason=f"{c['time_exit_h']:.0f}h 정상 청산")
            if history_item:
                state["history"] = state.get("history", []) + [history_item]
                state["active_position"] = None
                state["last_signal"] = {"date": datetime.now(KST).date().isoformat(), "type": "SELL_TIME"}
                # DB 기록: 시간 청산
                save_breakout_decision(
                    decision="sell",
                    reason=f"24h 정상 청산 | 매수 {pos['buy_price']:,.0f} → 매도 {history_item['exit_price']:,.0f} | 손익 {history_item['pnl_pct']:+.2f}%",
                    confidence=0.9,
                    current_price=current_price,
                    market_snapshot={
                        "strategy": "breakout_larry_williams",
                        "exit_reason": "time_exit",
                        "elapsed_h": round(elapsed_h, 1),
                        "buy_price": pos["buy_price"],
                        "exit_price": history_item["exit_price"],
                        "pnl_pct": history_item["pnl_pct"],
                        "pnl_krw": history_item["pnl_krw"],
                        "dry_run": c["dry_run"],
                    },
                    trade_result=history_item,
                    dry_run=c["dry_run"],
                )
        else:
            _log(f"보유 중 {elapsed_h:.1f}h 경과 (24h 미도달) — monitor가 손절 감시 중")
            if c["notify_no_signal"]:
                notify(
                    f"보유 중 {elapsed_h:.1f}h 경과\n"
                    f"   매수가 {pos['buy_price']:,.0f} / 손절선 {pos['stop_loss_price']:,.0f}\n"
                    f"   24h 청산까지 {c['time_exit_h'] - elapsed_h:.1f}h 남음"
                )
        save_state(state)
        return 0

    # 2) 매수 평가 (보유 없을 때만)
    if c["emergency_stop"]:
        msg = "EMERGENCY_STOP active — 매수 차단 (보유 없음, 청산할 것 없음)"
        _log(msg)
        notify(f"⚠️ {msg}")
        save_state(state)
        return 0

    try:
        yesterday = get_yesterday_ohlc()
        today_open = get_today_open()
        current = get_current_btc_price()
    except Exception as e:
        _log(f"가격 조회 실패: {e}")
        notify(f"🚨 가격 조회 실패\n{e}")
        save_state(state)
        return 1

    range_val = yesterday["high"] - yesterday["low"]
    target = today_open + range_val * c["k"]

    _log(
        f"어제({yesterday['date']}) H={yesterday['high']:,.0f} L={yesterday['low']:,.0f} "
        f"R={range_val:,.0f} | 오늘 시초={today_open:,.0f} | "
        f"Target={target:,.0f} (K={c['k']}) | 현재={current:,.0f}"
    )

    # 시장 스냅샷 (DB 기록용)
    market_snapshot = {
        "strategy": "breakout_larry_williams",
        "K": c["k"],
        "yesterday_high": yesterday["high"],
        "yesterday_low": yesterday["low"],
        "yesterday_range": range_val,
        "today_open": today_open,
        "target_price": target,
        "current_price": current,
        "gap_pct": round((current - target) / target * 100, 3),
        "buy_amount": c["buy_amount"],
        "stop_loss_pct": c["stop_loss_pct"],
        "time_exit_h": c["time_exit_h"],
        "dry_run": c["dry_run"],
    }

    if current >= target:
        _log(f"BUY 시그널 — 현재 {current:,.0f} >= Target {target:,.0f}")
        new_pos = execute_buy(target, current, c)
        if new_pos:
            state["active_position"] = new_pos
            state["last_signal"] = {
                "date": datetime.now(KST).date().isoformat(),
                "type": "BUY",
                "executed": True,
            }
            # DB 기록: 매수 결정
            save_breakout_decision(
                decision="buy",
                reason=f"변동성 돌파 매수 | Target {target:,.0f} ≤ 현재 {current:,.0f} | K={c['k']} Range={range_val:,.0f}",
                confidence=min(1.0, (current - target) / range_val + 0.5),
                current_price=current,
                market_snapshot=market_snapshot,
                trade_result={"buy_price": new_pos["buy_price"], "btc_volume": new_pos["btc_volume"], "krw_amount": new_pos["krw_amount"]},
                dry_run=c["dry_run"],
            )
    else:
        gap_pct = (target - current) / current * 100
        msg = (
            f"오늘 {os.getenv('BREAKOUT_TRADE_TIME_KST', '10:00')} — 시그널 없음\n"
            f"   Target: {target:,.0f}원\n"
            f"   현재: {current:,.0f}원 ({gap_pct:+.2f}% 부족)\n"
            f"   K={c['k']}, 어제 변동폭 {range_val:,.0f}원"
        )
        _log(msg.replace("\n   ", " | "))
        if c["notify_no_signal"]:
            notify(msg)
        state["last_signal"] = {
            "date": datetime.now(KST).date().isoformat(),
            "type": "NONE",
            "target": target,
            "current": current,
        }
        # DB 기록: 관망 결정
        save_breakout_decision(
            decision="hold",
            reason=f"변동성 돌파 미달 | Target {target:,.0f} > 현재 {current:,.0f} ({gap_pct:+.2f}% 부족) | K={c['k']}",
            confidence=0.5,
            current_price=current,
            market_snapshot=market_snapshot,
            dry_run=c["dry_run"],
        )

    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
