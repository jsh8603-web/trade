"""AltRang (알트랑) -- 알트코인 모멘텀 로테이션 전용 봇

실행:
  python -m altrang.main              # 기본 (DRY_RUN=true)
  SB_DRY_RUN=false python -m altrang.main  # 실매매

전략:
  - 5팩터 스코어링으로 상위 20개 알트코인 선별
  - 트레일링 스탑 / 부분 익절 / 시간 기반 청산
  - (펀딩비 수확: 코드 내장, SB_FUNDING_ENABLED=true 시 활성화)
"""

import asyncio
import logging
import os
import signal
import sys
import time
import traceback

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from altrang.config import AltrangConfig
from altrang.state import BotState, load_state, save_state
from altrang.data_feeder import MultiCoinFeeder
from altrang.coin_selector import CoinSelector
from altrang.execution import BinanceExecutor
from altrang.risk_manager import RiskManager
from altrang.funding_engine import FundingEngine
from altrang.rotation_engine import RotationEngine
from altrang.notifier import AltrangNotifier
from altrang.db import AltrangDB

logger = logging.getLogger("altrang.main")

# 틱 간격 (초)
TICK_INTERVAL = 60
# 상태 보고 간격 (초) -- 6시간 (테스트 중)
STATUS_INTERVAL = 21600
# 스냅샷 DB 기록 간격 (초) -- 6시간 (테스트 중, 이벤트 없으면 스킵)
SNAPSHOT_INTERVAL = 21600


class AltrangBot:
    """알트랑 메인 봇 클래스"""

    MAX_CONSECUTIVE_ERRORS = 30

    def __init__(self):
        self.config = AltrangConfig()
        self.state = load_state()
        self.feeder = MultiCoinFeeder(self.config)
        self.selector = CoinSelector(self.config)
        self.executor = BinanceExecutor(self.config)
        self.risk = RiskManager(self.config, self.state)
        self.funding = FundingEngine(
            self.config, self.state, self.feeder,
            self.executor, self.selector, self.risk,
        )
        self.rotation = RotationEngine(
            self.config, self.state, self.feeder,
            self.executor, self.selector, self.risk,
        )
        self.notifier = AltrangNotifier()
        self.db = AltrangDB(self.config.db)
        self._running = False
        self._tick_count = 0
        self._consecutive_errors = 0
        self._last_status_time = 0.0
        self._last_snapshot_time = 0.0

    async def run(self):
        """메인 실행"""
        self._running = True

        # 설정 검증
        errors = self.config.validate()
        if errors and not self.config.safety.dry_run:
            for e in errors:
                logger.error(f"설정 오류: {e}")
            return

        summary = self.config.summary()
        logger.info(summary)

        # 컴포넌트 시작
        await self.feeder.start()
        await self.executor.start()

        # 초기 데이터 대기
        ready = await self.feeder.wait_ready(timeout=30)
        if not ready:
            logger.error("데이터 준비 실패 -- 중단")
            await self._shutdown()
            return

        # BNB 잔고 확인
        await self.executor.ensure_bnb_reserve()

        # 시작 알림
        await self.notifier.notify_startup(summary)

        mode = "로테이션"
        if self.config.funding.enabled:
            mode += " + 펀딩비 수확"
        logger.info(f"=== 알트랑 (AltRang) 시작 [{mode}] ===")

        try:
            await self._main_loop()
        except asyncio.CancelledError:
            logger.info("봇 중단 요청")
        finally:
            await self._shutdown()

    async def _main_loop(self):
        """메인 루프 (TICK_INTERVAL 간격)"""
        while self._running:
            try:
                await self._tick()
                self._consecutive_errors = 0
            except (SystemExit, KeyboardInterrupt, MemoryError):
                raise
            except Exception as e:
                self._consecutive_errors += 1
                if self._consecutive_errors <= 3 or self._consecutive_errors % 10 == 0:
                    logger.error(
                        f"Tick 오류 ({self._consecutive_errors}회): {e}",
                        exc_info=(self._consecutive_errors % 10 == 0),
                    )
                if self._consecutive_errors == self.MAX_CONSECUTIVE_ERRORS:
                    try:
                        await self.notifier.notify_error(
                            "tick_loop",
                            f"연속 {self.MAX_CONSECUTIVE_ERRORS}회 오류. 마지막: {str(e)[:200]}"
                        )
                    except Exception:
                        pass

            await asyncio.sleep(TICK_INTERVAL)

    async def _tick(self):
        """1분마다 실행되는 메인 로직"""
        self._tick_count += 1
        now = time.time()

        # 긴급 정지 체크
        if self.config.safety.emergency_stop:
            if self._tick_count % 10 == 1:
                logger.warning("EMERGENCY_STOP 활성화 -- 대기 중")
            return

        # 1. 유니버스 스캔 (필요 시)
        if self.feeder.needs_scan():
            await self.feeder.scan_universe()

        # 2. 펀딩비 수확 엔진 — 활성화된 경우만, 이벤트 발생 시에만 알림+DB
        funding_actions = []
        if self.config.funding.enabled:
            funding_actions = await self.funding.tick()
            for action in funding_actions:
                action["dry_run"] = self.config.safety.dry_run
                try:
                    await self.notifier.notify_action(action)
                except Exception as e:
                    logger.warning(f"알림 실패: {e}")
                try:
                    await self.db.record_trade(action)
                except Exception as e:
                    logger.warning(f"DB 기록 실패: {e}")

        # 3. 로테이션 엔진 — 이벤트 발생 시에만 알림+DB
        rotation_actions = await self.rotation.tick()
        for action in rotation_actions:
            action["dry_run"] = self.config.safety.dry_run
            try:
                await self.notifier.notify_action(action)
            except Exception as e:
                logger.warning(f"알림 실패: {e}")
            try:
                await self.db.record_trade(action)
            except Exception as e:
                logger.warning(f"DB 기록 실패: {e}")

        # 이벤트 유무 추적
        has_events = bool(funding_actions or rotation_actions)

        # 4. 포트폴리오 건강 체크
        health = self.risk.check_portfolio_health()
        if health.get("should_reduce"):
            logger.warning(f"포트폴리오 드로다운 경고: {health['drawdown_pct']:.1f}%")

        # 5. 주기적 로그
        if self._tick_count % 5 == 0:
            f_count = health["funding_count"]
            r_count = health["rotation_count"]
            logger.info(
                f"[Tick {self._tick_count}] "
                f"펀딩:{f_count} 로테이션:{r_count} "
                f"거래:{health['trades_today']}건 "
                f"미실현PnL:${health['total_unrealized_pnl']:+.2f}"
            )

        # 6. 주기적 상태 보고 — 6시간 간격, 이벤트 없으면 스킵
        if now - self._last_status_time >= STATUS_INTERVAL:
            if has_events:
                self._last_status_time = now
                try:
                    f_summary = self.funding.get_summary() if self.config.funding.enabled else {}
                    r_summary = self.rotation.get_summary()
                    data = self.feeder.get_all()
                    top_funding = self.selector.rank_by_funding(data) if self.config.funding.enabled else []
                    top_momentum = self.selector.rank_by_momentum(data)
                    await self.notifier.notify_status(
                        f_summary, r_summary,
                        health=health,
                        top_funding=top_funding,
                        top_momentum=top_momentum,
                    )
                    # 코인 순위 DB 기록
                    if top_momentum:
                        rankings = [
                            {"symbol": c.symbol, "score": c.score, "reason": c.reason}
                            for c in top_momentum[:20]
                        ]
                        await self.db.record_rankings("momentum", rankings)
                    if top_funding:
                        rankings = [
                            {"symbol": c.symbol, "score": c.score, "reason": c.reason}
                            for c in top_funding[:10]
                        ]
                        await self.db.record_rankings("funding", rankings)
                except Exception as e:
                    logger.warning(f"상태 보고 실패: {e}")
            else:
                # 이벤트 없어도 타이머는 리셋 (다음 6시간까지 대기)
                self._last_status_time = now

        # 7. 주기적 DB 스냅샷 — 6시간 간격, 이벤트 없으면 스킵
        if now - self._last_snapshot_time >= SNAPSHOT_INTERVAL:
            if has_events:
                self._last_snapshot_time = now
                try:
                    f_summary = self.funding.get_summary() if self.config.funding.enabled else {}
                    r_summary = self.rotation.get_summary()
                    balances = await self.executor.get_spot_balances()
                    total = balances.get("USDT", 0) + health["total_invested"]
                    await self.db.record_snapshot(total, f_summary, r_summary)
                except Exception as e:
                    logger.warning(f"스냅샷 기록 실패: {e}")
            else:
                # 이벤트 없어도 타이머는 리셋
                self._last_snapshot_time = now

        # 8. 상태 저장
        save_state(self.state)

    async def _shutdown(self):
        """정리 종료"""
        logger.info("알트랑 종료 중...")
        self._running = False
        save_state(self.state)
        try:
            await self.executor.close()
        except Exception as e:
            logger.error(f"executor 정리 실패: {e}")
        try:
            await self.feeder.stop()
        except Exception as e:
            logger.error(f"feeder 정리 실패: {e}")
        logger.info("알트랑 종료 완료")

    def stop(self):
        self._running = False


def setup_logging():
    log_dir = os.path.join(PROJECT_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                os.path.join(log_dir, "altrang.log"),
                encoding="utf-8",
            ),
        ],
    )


def main():
    setup_logging()
    logger.info("AltRang (알트랑) v0.2.0 시작")

    bot = AltrangBot()

    def handle_signal(*_):
        logger.info("종료 시그널 수신")
        bot.stop()

    try:
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
    except (OSError, ValueError):
        pass

    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
