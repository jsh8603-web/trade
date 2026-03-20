"""AltRang Notifier -- 텔레그램 알림"""

import asyncio
import logging
import os
import sys
import time

logger = logging.getLogger("altrang.notifier")

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)


class AltrangNotifier:
    """알트랑 전용 텔레그램 알림"""

    MIN_SEND_INTERVAL = 1.0
    MAX_RETRIES = 3

    def __init__(self):
        self._enabled = bool(
            os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_USER_ID")
        )
        if not self._enabled:
            logger.warning("텔레그램 미설정 -- 알림 비활성화")
        self._last_send_time = 0.0
        self._send_lock = asyncio.Lock()

    async def _send(self, msg_type: str, title: str, body: str):
        if not self._enabled:
            return
        async with self._send_lock:
            elapsed = time.time() - self._last_send_time
            if elapsed < self.MIN_SEND_INTERVAL:
                await asyncio.sleep(self.MIN_SEND_INTERVAL - elapsed)
            for attempt in range(self.MAX_RETRIES):
                try:
                    from scripts.notify_telegram import send_message
                    await asyncio.to_thread(send_message, msg_type, title, body)
                    self._last_send_time = time.time()
                    return
                except Exception as e:
                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(2.0 ** attempt)
                    else:
                        logger.error(f"텔레그램 전송 실패: {e}")

    async def notify_action(self, action: dict):
        """거래 액션 알림"""
        strategy = action.get("strategy", "?")
        act = action.get("action", "?")
        symbol = action.get("symbol", "?")
        success = action.get("success", False)

        emoji = {"funding": "💰", "rotation": "🔄"}.get(strategy, "📊")
        status = "✅" if success else "❌"

        title = f"{emoji} 알트랑 {strategy} | {act}"

        lines = [f"{status} {symbol}"]
        if "funding_rate" in action:
            lines.append(f"펀딩비: {action['funding_rate']*100:.4f}%")
        if "momentum_score" in action:
            lines.append(f"모멘텀: {action['momentum_score']:.1f}")
        if "size_usdt" in action:
            lines.append(f"금액: ${action['size_usdt']:.0f}")
        if "pnl_pct" in action:
            lines.append(f"PnL: {action['pnl_pct']:+.2f}%")
        if "pnl_usdt" in action:
            lines.append(f"PnL: ${action['pnl_usdt']:+.2f}")
        if "reason" in action:
            lines.append(f"사유: {action['reason']}")
        if "error" in action:
            lines.append(f"오류: {action['error']}")

        await self._send("trade", title, "\n".join(lines))

    async def notify_status(
        self,
        funding_summary: dict,
        rotation_summary: dict,
        health: dict = None,
        top_funding: list = None,
        top_momentum: list = None,
    ):
        """2시간 간격 종합 상태 보고"""
        f_count = funding_summary.get("position_count", 0)
        r_count = rotation_summary.get("position_count", 0)
        f_invested = funding_summary.get("total_invested", 0)
        r_invested = rotation_summary.get("total_invested", 0)
        r_pnl = rotation_summary.get("total_unrealized_pnl", 0)
        f_collected = funding_summary.get("total_funding_collected", 0)

        from datetime import datetime, timezone
        now_str = datetime.now(timezone.utc).strftime("%m/%d %H:%M UTC")

        lines = [
            f"[{now_str}]",
            "",
            f"=== 포지션 현황 ===",
            f"펀딩: {f_count}개 (${f_invested:,.0f}) 수확: ${f_collected:,.2f}",
            f"로테이션: {r_count}개 (${r_invested:,.0f}) PnL: ${r_pnl:+,.2f}",
        ]

        if health:
            lines.append(f"거래: {health.get('trades_today', 0)}건 | DD: {health.get('drawdown_pct', 0):.1f}%")

        # 펀딩 포지션 상세
        if funding_summary.get("positions"):
            lines.append("")
            lines.append("=== 펀딩 포지션 ===")
            for pos in funding_summary["positions"][:5]:
                lines.append(
                    f"  {pos['symbol']}: FR={pos['current_funding_rate']*100:.3f}% "
                    f"| {pos['held_hours']:.0f}h | ${pos.get('funding_collected', 0):.3f}"
                )

        # 로테이션 포지션 상세
        if rotation_summary.get("positions"):
            lines.append("")
            lines.append("=== 로테이션 포지션 ===")
            for pos in rotation_summary["positions"][:5]:
                lines.append(
                    f"  {pos['symbol']}: {pos['pnl_pct']:+.1f}% (${pos['pnl_usdt']:+.1f}) "
                    f"| {pos['held_hours']:.0f}h"
                )

        # 시장 현황 (펀딩비 TOP, 모멘텀 TOP)
        if top_funding:
            lines.append("")
            lines.append("=== 펀딩비 TOP 3 ===")
            for c in top_funding[:3]:
                lines.append(f"  {c.symbol}: {c.funding_rate*100:+.4f}%")

        if top_momentum:
            lines.append("")
            lines.append("=== 모멘텀 TOP 3 ===")
            for c in top_momentum[:3]:
                lines.append(f"  {c.symbol}: {c.reason}")

        await self._send("status", "📊 알트랑 2시간 리포트", "\n".join(lines))

    async def notify_error(self, phase: str, error: str):
        """에러 알림"""
        await self._send("error", "⚠️ 알트랑 오류", f"Phase: {phase}\n{error[:300]}")

    async def notify_startup(self, config_summary: str):
        """시작 알림"""
        await self._send("status", "🚀 알트랑 시작", config_summary[:500])
