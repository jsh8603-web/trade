#!/usr/bin/env python3
"""
결정 사후 추적 스크립트 -- 매 시간 cron으로 실행

1h/4h/24h 전 결정들의 가격 변동을 기록하여 결정 정확도를 측정한다.

사용법:
  python3 scripts/retrospective.py           # 모든 미평가 결정 업데이트
  python3 scripts/retrospective.py report    # 정확도 리포트 출력

cron 예시 (매시 15분):
  15 * * * * cd ~/workspace/blockchain && .venv/bin/python3 scripts/retrospective.py
"""

import os, sys, time
from typing import Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Ensure project root is in sys.path for utils imports
PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from dotenv import load_dotenv
import requests

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
UPBIT_API = "https://api.upbit.com/v1"
KST = timezone(timedelta(hours=9))

# ── 커넥션 재사용을 위한 세션 ──────────────────────────
_session: requests.Session | None = None


def _get_session() -> requests.Session:
    """모듈 레벨 requests.Session을 반환한다 (커넥션 풀 재사용)."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({"Accept": "application/json"})
    return _session


# 헤더를 매번 dict 생성하지 않고 캐시
_supabase_headers: dict | None = None
_supabase_patch_headers: dict | None = None


def supabase_headers():
    global _supabase_headers
    if _supabase_headers is None:
        _supabase_headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
        }
    return _supabase_headers


def _supabase_patch_hdrs():
    """PATCH 전용 헤더 (Prefer: return=minimal 포함)."""
    global _supabase_patch_headers
    if _supabase_patch_headers is None:
        _supabase_patch_headers = {**supabase_headers(), "Prefer": "return=minimal"}
    return _supabase_patch_headers


def get_btc_price() -> Optional[int]:
    """현재 BTC/KRW 가격. 실패 시 None 반환."""
    try:
        r = _get_session().get(f"{UPBIT_API}/ticker", params={"markets": "KRW-BTC"}, timeout=10)
        if r.ok:
            return int(r.json()[0]["trade_price"])
    except Exception:
        pass
    return None


def get_historical_price(target_time: datetime) -> int:
    """특정 시점의 BTC 가격 (분봉으로 근사)"""
    to_str = target_time.strftime("%Y-%m-%dT%H:%M:%S") + "+09:00"
    params = {
        "market": "KRW-BTC",
        "to": to_str,
        "count": 1,
    }
    r = _get_session().get(f"{UPBIT_API}/candles/minutes/60", params=params, timeout=10)
    if r.ok and r.json():
        return int(r.json()[0]["trade_price"])
    return 0


def _evaluate_correctness(decision_type: str, outcome_pct: float, window: str) -> bool:
    """결정이 올바랐는지 판단"""
    if decision_type == "매수":
        return outcome_pct > 0
    elif decision_type == "매도":
        return outcome_pct < 0
    else:  # 관망
        threshold = 1.0 if window == "24h" else 0.5
        return outcome_pct < threshold


def _batch_patch(table: str, patches: list, session=None) -> int:
    """Supabase 일괄 PATCH 헬퍼 — sleep 없이 연속 실행 (세션 재사용).

    Args:
        table: Supabase 테이블명
        patches: [(row_id, patch_data), ...]

    Returns:
        성공 건수
    """
    if not patches:
        return 0
    sess = session or _get_session()
    hdrs = _supabase_patch_hdrs()
    updated = 0
    for row_id, patch in patches:
        resp = sess.patch(
            f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{row_id}",
            headers=hdrs,
            json=patch,
            timeout=10,
        )
        if resp.ok:
            updated += 1
        else:
            print(f"[retrospective] {table} PATCH 실패 id={row_id}: {resp.status_code}", file=sys.stderr)
    return updated


def _update_window(window: str, hours: int):
    """특정 시간 윈도우의 aftermath 업데이트 (collect-then-patch 패턴).

    Returns:
        (updated_count, outcomes_list)
    """
    now = datetime.now(KST)
    cutoff = (now - timedelta(hours=hours)).isoformat()

    price_col = f"price_{window}_after"
    outcome_col = f"outcome_{window}_pct"
    correct_col = f"was_correct_{window}"

    params = {
        price_col: "is.null",
        "created_at": f"lt.{cutoff}",
        "select": "id,decision,current_price,created_at",
        "limit": "100",
    }
    r = _get_session().get(
        f"{SUPABASE_URL}/rest/v1/decisions",
        headers=supabase_headers(),
        params=params,
        timeout=15,
    )
    if not r.ok:
        print(f"[retrospective] {window} 조회 실패: {r.status_code}", file=sys.stderr)
        return 0, []

    skipped_null_price = 0
    outcomes = []
    # Phase 1: Upbit 가격 조회 수집 (rate limit 준수)
    patches = []
    for row in r.json():
        decision_price = row.get("current_price", 0)
        if not decision_price:
            skipped_null_price += 1
            print(f"[retrospective] [skip] decision {str(row.get('id', '?'))[:8]} — current_price=NULL", file=sys.stderr)
            continue

        try:
            decision_time = datetime.fromisoformat(row["created_at"])
        except ValueError:
            decision_time = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        target_time = decision_time + timedelta(hours=hours)

        if target_time > now:
            continue

        price_after = get_historical_price(target_time)
        if not price_after:
            continue
        time.sleep(0.15)  # Upbit API rate limit

        outcome_pct = round((price_after - decision_price) / decision_price * 100, 3)
        decision_type = row.get("decision", "")
        was_correct = _evaluate_correctness(decision_type, outcome_pct, window)

        patch_data = {
            price_col: price_after,
            outcome_col: outcome_pct,
            correct_col: was_correct,
            "aftermath_updated_at": now.isoformat(),
        }
        if window == "24h":
            if decision_type == "매수":
                patch_data["profit_loss"] = outcome_pct
            elif decision_type == "매도":
                patch_data["profit_loss"] = -outcome_pct
            else:
                patch_data["profit_loss"] = -outcome_pct
        patches.append((row["id"], patch_data))
        outcomes.append({
            "created_at": row["created_at"],
            "outcome_pct": outcome_pct,
        })

    # Phase 2: Supabase 일괄 PATCH (sleep 불필요)
    updated = _batch_patch("decisions", patches)

    if skipped_null_price:
        print(f"[retrospective] {window}: {skipped_null_price}건 current_price=NULL로 스킵됨", file=sys.stderr)

    return updated, outcomes


def update_decisions():
    """미평가 결정들의 aftermath 업데이트.

    Returns:
        {"1h": int, "4h": int, "24h": int, "updated": int,
         "outcomes": [{"timestamp": str, "outcome_4h_pct": float}, ...]}
    """
    updated_1h, outcomes_1h = _update_window("1h", 1)
    updated_4h, outcomes_4h = _update_window("4h", 4)
    updated_24h, outcomes_24h = _update_window("24h", 24)

    buffer_outcomes = [
        {"timestamp": o["created_at"], "outcome_4h_pct": o["outcome_pct"]}
        for o in outcomes_4h
        if o.get("outcome_pct") is not None
    ]

    total = updated_1h + updated_4h + updated_24h
    print(f"[retrospective] 업데이트 완료: 1h={updated_1h}, 4h={updated_4h}, 24h={updated_24h}")
    return {"1h": updated_1h, "4h": updated_4h, "24h": updated_24h,
            "updated": total, "outcomes": buffer_outcomes}


def update_scalp_aftermath():
    """초단타 거래 aftermath 업데이트 (collect-then-patch 패턴)"""
    now = datetime.now(KST)
    cutoff = (now - timedelta(hours=1)).isoformat()

    session = _get_session()
    r = session.get(
        f"{SUPABASE_URL}/rest/v1/scalp_trade_log",
        headers=supabase_headers(),
        params={
            "price_1h_after": "is.null",
            "entry_time": f"lt.{cutoff}",
            "select": "id,entry_price,exit_price,pnl_pct,entry_time",
            "limit": "100",
        },
        timeout=15,
    )
    if not r.ok:
        return

    # Phase 1: Upbit 가격 조회 수집 (rate limit 준수)
    patches = []
    for row in r.json():
        entry_price = row.get("entry_price", 0)
        if not entry_price:
            continue

        entry_time = datetime.fromisoformat(row["entry_time"].replace("Z", "+00:00"))
        target_time = entry_time + timedelta(hours=1)

        if target_time > now:
            continue

        price_after = get_historical_price(target_time)
        if not price_after:
            continue
        time.sleep(0.15)  # Upbit API rate limit

        outcome_pct = round((price_after - entry_price) / entry_price * 100, 3)
        was_good_entry = outcome_pct > 0

        patches.append((row["id"], {
            "price_1h_after": price_after,
            "outcome_1h_pct": outcome_pct,
            "was_good_entry": was_good_entry,
            "aftermath_updated_at": now.isoformat(),
        }))

    # Phase 2: Supabase 일괄 PATCH (sleep 불필요)
    updated = _batch_patch("scalp_trade_log", patches, session)

    if updated:
        print(f"[retrospective] 초단타 {updated}건 업데이트")


def update_signal_attempts():
    """차단된/생성된 시그널의 1시간 후 가격 업데이트 (collect-then-patch 패턴)"""
    now = datetime.now(KST)
    cutoff = (now - timedelta(hours=1)).isoformat()

    session = _get_session()
    r = session.get(
        f"{SUPABASE_URL}/rest/v1/signal_attempt_log",
        headers=supabase_headers(),
        params={
            "price_1h_after": "is.null",
            "signal_type": "neq.no_signal",
            "recorded_at": f"lt.{cutoff}",
            "select": "id,btc_price,recorded_at,signal_type,action",
            "limit": "100",
        },
        timeout=15,
    )
    if not r.ok:
        print(f"[retrospective] signal_attempt 조회 실패: {r.status_code}", file=sys.stderr)
        return

    # Phase 1: Upbit 가격 조회 수집 (rate limit 준수)
    patches = []
    for row in r.json():
        btc_price = row.get("btc_price", 0)
        if not btc_price:
            continue

        recorded_at = datetime.fromisoformat(row["recorded_at"].replace("Z", "+00:00"))
        target_time = recorded_at + timedelta(hours=1)

        if target_time > now:
            continue

        price_after = get_historical_price(target_time)
        if not price_after:
            continue
        time.sleep(0.15)  # Upbit API rate limit

        outcome_pct = round((price_after - btc_price) / btc_price * 100, 3)

        action = row.get("action", "buy")
        if action == "buy":
            would_have_won = outcome_pct > 0
        elif action == "sell":
            would_have_won = outcome_pct < 0
        else:
            would_have_won = None

        patches.append((row["id"], {
            "price_1h_after": price_after,
            "outcome_1h_pct": outcome_pct,
            "would_have_won": would_have_won,
            "aftermath_updated_at": now.isoformat(),
        }))

    # Phase 2: Supabase 일괄 PATCH (sleep 불필요)
    updated = _batch_patch("signal_attempt_log", patches, session)

    if updated:
        print(f"[retrospective] signal_attempt {updated}건 업데이트")


def update_buy_score_aftermath():
    """니어미스/AI거부 사후 추적 (collect-then-patch 패턴)."""
    now = datetime.now(KST)
    current_price = get_btc_price()
    if not current_price:
        print("[retrospective] BTC 가격 조회 실패, buy_score aftermath 스킵", file=sys.stderr)
        return

    session = _get_session()

    # ── 1시간 후 가격 업데이트 ──
    cutoff_1h = (now - timedelta(hours=1)).isoformat()
    r = session.get(
        f"{SUPABASE_URL}/rest/v1/buy_score_detail",
        headers=supabase_headers(),
        params={
            "price_1h_after": "is.null",
            "recorded_at": f"lt.{cutoff_1h}",
            "select": "id,price_at_decision,recorded_at,action",
            "limit": "100",
        },
        timeout=15,
    )
    # Phase 1: Upbit 가격 조회 수집
    patches_1h = []
    if r.ok:
        for row in r.json():
            decision_price = row.get("price_at_decision", 0)
            if not decision_price:
                continue

            recorded_at = datetime.fromisoformat(row["recorded_at"].replace("Z", "+00:00"))
            target_time = recorded_at + timedelta(hours=1)
            if target_time > now:
                continue

            price_after = get_historical_price(target_time)
            if not price_after:
                continue
            time.sleep(0.15)  # Upbit API rate limit

            outcome_pct = round((price_after - decision_price) / decision_price * 100, 3)

            patches_1h.append((row["id"], {
                "price_1h_after": price_after,
                "outcome_1h_pct": outcome_pct,
                "aftermath_updated_at": now.isoformat(),
            }))

    # Phase 2: Supabase 일괄 PATCH
    updated_1h = _batch_patch("buy_score_detail", patches_1h, session)

    # ── 4시간 후 가격 업데이트 ──
    cutoff_4h = (now - timedelta(hours=4)).isoformat()
    r = session.get(
        f"{SUPABASE_URL}/rest/v1/buy_score_detail",
        headers=supabase_headers(),
        params={
            "price_4h_after": "is.null",
            "price_1h_after": "not.is.null",
            "recorded_at": f"lt.{cutoff_4h}",
            "select": "id,price_at_decision,recorded_at,action",
            "limit": "100",
        },
        timeout=15,
    )
    patches_4h = []
    if r.ok:
        for row in r.json():
            decision_price = row.get("price_at_decision", 0)
            if not decision_price:
                continue

            recorded_at = datetime.fromisoformat(row["recorded_at"].replace("Z", "+00:00"))
            target_time = recorded_at + timedelta(hours=4)
            if target_time > now:
                continue

            price_after = get_historical_price(target_time)
            if not price_after:
                continue
            time.sleep(0.15)  # Upbit API rate limit

            outcome_pct = round((price_after - decision_price) / decision_price * 100, 3)
            action = row.get("action", "hold")
            if action in ("hold",):
                would_have_profited = outcome_pct > 0.5
            elif action in ("buy", "매수"):
                would_have_profited = outcome_pct > 0
            else:
                would_have_profited = None

            patches_4h.append((row["id"], {
                "price_4h_after": price_after,
                "outcome_4h_pct": outcome_pct,
                "would_have_profited": would_have_profited,
                "aftermath_updated_at": now.isoformat(),
            }))

    updated_4h = _batch_patch("buy_score_detail", patches_4h, session)

    if updated_1h or updated_4h:
        print(f"[retrospective] buy_score aftermath: 1h={updated_1h}, 4h={updated_4h}")


def report():
    """정확도 리포트"""
    session = _get_session()
    hdrs = supabase_headers()

    r = session.get(
        f"{SUPABASE_URL}/rest/v1/v_decision_accuracy",
        headers=hdrs,
        timeout=15,
    )
    if r.ok and r.json():
        print("=== 결정 정확도 ===")
        print(
            f"  {'결정':<6} {'소스':<8} {'총':<5} {'1h정확':>7} {'1h평균':>7} "
            f"{'4h정확':>7} {'4h평균':>7} {'24h정확':>8} {'24h평균':>7}"
        )
        for row in r.json():
            d = row.get('decision') or '?'
            s = row.get('source') or '?'
            t = row.get('total') or 0
            a1 = row.get('accuracy_1h')
            m1 = row.get('avg_1h_pct')
            a4 = row.get('accuracy_4h')
            m4 = row.get('avg_4h_pct')
            a24 = row.get('accuracy_24h')
            m24 = row.get('avg_24h_pct')
            print(
                f"  {d:<6} {s:<8} {t:<5} "
                f"{f'{a1}%' if a1 is not None else '-':>7} "
                f"{f'{m1}%' if m1 is not None else '-':>7} "
                f"{f'{a4}%' if a4 is not None else '-':>7} "
                f"{f'{m4}%' if m4 is not None else '-':>7} "
                f"{f'{a24}%' if a24 is not None else '-':>8} "
                f"{f'{m24}%' if m24 is not None else '-':>7}"
            )
    else:
        print("=== 결정 정확도 === (데이터 없음)")

    r = session.get(
        f"{SUPABASE_URL}/rest/v1/v_missed_opportunities",
        headers=hdrs,
        params={"limit": "10"},
        timeout=15,
    )
    if r.ok and r.json():
        print(f"\n=== 놓친 기회 TOP {len(r.json())} ===")
        for row in r.json():
            print(
                f"  {row.get('created_at', '')[:16]} | "
                f"가격: {row.get('current_price', 0):,} | "
                f"24h후: +{row.get('outcome_24h_pct', 0):.1f}% | "
                f"FGI:{row.get('fear_greed_value', '?')} RSI:{row.get('rsi_value', '?')}"
            )
            print(f"    사유: {(row.get('reason') or '')[:80]}")

    r = session.get(
        f"{SUPABASE_URL}/rest/v1/v_bad_trades",
        headers=hdrs,
        params={"limit": "10"},
        timeout=15,
    )
    if r.ok and r.json():
        print(f"\n=== 잘못된 매수 TOP {len(r.json())} ===")
        for row in r.json():
            print(
                f"  {row.get('created_at', '')[:16]} | "
                f"가격: {row.get('current_price', 0):,} | "
                f"4h후: {row.get('outcome_4h_pct', 0):+.1f}% | "
                f"금액: {row.get('trade_amount', 0):,}"
            )
            print(f"    사유: {(row.get('reason') or '')[:80]}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        report()
    else:
        from utils.machine import skip_trade_db
        if skip_trade_db("decisions"):
            print("[retrospective] worker 머신 — 사후추적 스킵")
            return
        update_decisions()
        update_scalp_aftermath()
        update_signal_attempts()
        update_buy_score_aftermath()
        if "--report" in sys.argv:
            report()


if __name__ == "__main__":
    main()
