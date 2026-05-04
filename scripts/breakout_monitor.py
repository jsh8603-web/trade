"""변동성 돌파 손절 감시 — 매 15분 cron, 빈도 자동 조절.

빈도 룰:
  매수 후 0~3h: 매번 처리 (15분마다)
  매수 후 3h~24h: 정시(00분)에만 처리 (1h 마다)
  보유 없음: 즉시 종료 (오버헤드 최소화)

손절 룰:
  현재가 ≤ 매수가 × (1 + STOP_LOSS_PCT/100)  →  즉시 시장가 매도
  EMERGENCY_STOP=true 시에도 손절은 허용 (포지션 정리)
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.breakout_trader import (
    cfg,
    load_state,
    save_state,
    get_current_btc_price,
    execute_sell,
    save_breakout_decision,
    notify,
    _log,
    KST,
)


def should_process(elapsed_h: float, now_minute: int) -> bool:
    """빈도 조절: 0~3h 매번, 3h~24h는 정시만."""
    if elapsed_h <= 3.0:
        return True  # 매 15분 처리
    return now_minute < 5  # 3h~24h: 정시 ±5분


def main() -> int:
    c = cfg()
    if not c["enabled"]:
        return 0

    state = load_state()
    pos = state.get("active_position")
    if not pos:
        # 보유 없음 — 즉시 종료 (cron 오버헤드 최소화)
        return 0

    now_kst = datetime.now(KST)
    entered = datetime.fromisoformat(pos["entered_at"])
    elapsed_h = (now_kst - entered).total_seconds() / 3600

    # 24h 경과 시 monitor가 처리 X — trader가 10:00에 처리
    if elapsed_h >= c["time_exit_h"]:
        _log(f"24h 초과 ({elapsed_h:.1f}h) — trader가 청산 처리")
        return 0

    if not should_process(elapsed_h, now_kst.minute):
        return 0  # 이번 호출은 스킵 (3h+ 이후 정시 외)

    state["last_check"] = now_kst.isoformat()

    try:
        current = get_current_btc_price()
    except Exception as e:
        _log(f"가격 조회 실패: {e}")
        save_state(state)
        return 1

    pnl_pct = (current - pos["buy_price"]) / pos["buy_price"] * 100
    _log(
        f"보유 감시 ({elapsed_h:.1f}h 경과): 매수 {pos['buy_price']:,.0f} → 현재 {current:,.0f} "
        f"({pnl_pct:+.2f}%) 손절선 {pos['stop_loss_price']:,.0f}"
    )

    if pnl_pct <= c["stop_loss_pct"]:
        _log(f"손절 발동 — {pnl_pct:.2f}% ≤ {c['stop_loss_pct']}%")
        history_item = execute_sell(pos, c, reason=f"손절 {pnl_pct:.2f}%")
        if history_item:
            state["history"] = state.get("history", []) + [history_item]
            state["active_position"] = None
            state["last_signal"] = {"date": now_kst.date().isoformat(), "type": "SELL_STOP_LOSS"}
            # DB 기록: 손절 매도
            save_breakout_decision(
                decision="sell",
                reason=f"손절 발동 | 매수 {pos['buy_price']:,.0f} → 현재 {current:,.0f} ({pnl_pct:+.2f}%) | 기준 {c['stop_loss_pct']}%",
                confidence=0.95,
                current_price=current,
                market_snapshot={
                    "strategy": "breakout_larry_williams",
                    "exit_reason": "stop_loss",
                    "elapsed_h": round(elapsed_h, 1),
                    "buy_price": pos["buy_price"],
                    "exit_price": history_item["exit_price"],
                    "pnl_pct": history_item["pnl_pct"],
                    "pnl_krw": history_item["pnl_krw"],
                    "stop_loss_pct": c["stop_loss_pct"],
                    "dry_run": c["dry_run"],
                },
                trade_result=history_item,
                dry_run=c["dry_run"],
            )

    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
