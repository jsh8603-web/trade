"""scripts/watchdog.py — Dead-man's switch / Watchdog (Phase Unattended SO-4).

독립 프로세스. 봇/DB/brain/LLM import 무의존.
ExchangeAdapter + DeriskExecutor 만 사용.

동작:
  - heartbeat.json 주기 폴링 → stale 감지 → derisk_to_floor 직접 트리거
  - resume/re-arm 금지 (de-risk 발동 후 사람만 복구)
  - 거래소 native stop 등록 stub (flash-crash 1차 방어, 실연결 go-live 이연)
  - revoke_bot_api_key stub (인프라 전소 시 master key 무효화, 실연결 이연)
  - 봇과 독립 credential 사용 (WATCHDOG_UPBIT_KEY / WATCHDOG_UPBIT_SECRET)

SACRED: market order 금지. 전량청산 금지. LLM 독립.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

# 봇 코어/brain/LLM import 0 — ExchangeAdapter / DeriskExecutor 만
# (import 정적 검사: grep 'brain\|judge\|llm\|consensus\|HRP' scripts/watchdog.py → 0)
sys.path.insert(0, str(Path(__file__).parent.parent))  # project root

from core.derisk_executor import DeriskExecutor, ExchangeAdapter, FakeExchange  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s watchdog %(message)s",
)
logger = logging.getLogger("watchdog")

# ── 환경 변수 파라미터 ────────────────────────────────────────────────

HEARTBEAT_PATH = Path(
    os.environ.get("UNATTENDED_HEARTBEAT_PATH", "data/heartbeat.json")
)
HEARTBEAT_TIMEOUT_SEC = float(
    os.environ.get("UNATTENDED_HEARTBEAT_TIMEOUT_SEC", "90")
)  # = 3 miss (heartbeat 30s 간격)
WATCHDOG_POLL_SEC = float(
    os.environ.get("UNATTENDED_WATCHDOG_POLL_SEC", "15")
)  # 15s 간격 폴링

# 봇과 독립 credential (SPOF 완화 A4)
WATCHDOG_UPBIT_KEY = os.environ.get("WATCHDOG_UPBIT_KEY", "")
WATCHDOG_UPBIT_SECRET = os.environ.get("WATCHDOG_UPBIT_SECRET", "")

# de-risk floor (floor 0 = IOC 상한 내 최대 축소, 전량청산 아님)
# 실운영 시 심볼별 floor 를 .env 또는 config로 설정
_FLOOR_JSON_STR = os.environ.get("WATCHDOG_FLOORS_JSON", "{}")
try:
    WATCHDOG_FLOORS: dict[str, float] = json.loads(_FLOOR_JSON_STR)
    if not isinstance(WATCHDOG_FLOORS, dict):
        raise ValueError("WATCHDOG_FLOORS_JSON must be a JSON object")
except Exception as _exc:  # noqa: BLE001 — 잘못된 JSON 으로 watchdog import crash 방지 (Phase Gate 보안 P1)
    logger.warning("WATCHDOG_FLOORS_JSON 파싱 실패 (%s) — 빈 floors 사용", _exc)
    WATCHDOG_FLOORS = {}


# ── Heartbeat writer (봇 메인 루프에서 호출) ─────────────────────────


def write_heartbeat(
    ts: float | None = None,
    position_hash: str = "",
    healthy: bool = True,
    last_decision_age: float = 0.0,
    path: str | Path = "data/heartbeat.json",
) -> None:
    """봇 메인 루프가 매 cycle 호출 — watchdog 용 heartbeat 기록.

    path: heartbeat.json 경로 (env UNATTENDED_HEARTBEAT_PATH 와 일치).
    interval: env UNATTENDED_HEARTBEAT_SEC (기본 30s).
    """
    if ts is None:
        ts = time.time()
    entry = {
        "ts": ts,
        "position_hash": position_hash,
        "healthy": healthy,
        "last_decision_age": last_decision_age,
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # atomic write (tmp → rename)
    tmp = p.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")
        tmp.replace(p)
    except Exception as exc:  # noqa: BLE001
        logger.error("write_heartbeat: failed: %s", exc)


def read_heartbeat(path: Path = HEARTBEAT_PATH) -> dict | None:
    """heartbeat.json 읽기. 파일 없거나 파싱 실패 시 None."""
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text)
    except Exception as exc:  # noqa: BLE001
        logger.error("read_heartbeat: parse failed: %s", exc)
        return None


# ── Native stop stub (1차 방어, 실연결 go-live 이연) ─────────────────


def register_native_stop(
    symbol: str,
    stop_price: float,
    exchange: ExchangeAdapter | None = None,
) -> bool:
    """거래소 native stop 등록 stub.

    설계: 포지션 개시 즉시 1차 방어선 등록 → derisk_executor = 2차 보강.
    Upbit 현물 조건부주문 제약 / KIS stop-loss 제약 → 실연결 go-live 이연.
    실연결 시 이 함수 body를 거래소 API 호출로 교체.

    Returns: True(성공) / False(미지원 or 실패).
    """
    logger.info(
        "register_native_stop: STUB — symbol=%s stop_price=%.4f (실연결 이연)",
        symbol,
        stop_price,
    )
    # TODO(go-live): Upbit 조건부 주문 / KIS 손절 API 실연결
    return False  # stub: 항상 미지원


def revoke_bot_api_key(
    reason: str = "watchdog_triggered",
) -> bool:
    """봇 API 키 무효화 stub — 인프라 전소(데몬+세션 동시사망) 시 master key 로 호출.

    거래소 master key 로 봇 API key 를 revoke → 궁극 fail-safe.
    실연결 go-live 이연 (credential 분리 필요).

    Returns: True(성공) / False(stub or 실패).
    """
    logger.critical(
        "revoke_bot_api_key: STUB — reason=%s (실연결 이연, master key 미설정)",
        reason,
    )
    # TODO(go-live): exchange.revoke_api_key(WATCHDOG_UPBIT_KEY) — master credential
    return False  # stub


# ── 알림 ────────────────────────────────────────────────────────────


def _notify(msg: str) -> None:
    """멀티채널 알림 (텔레그램 등). 환경변수 미설정 시 log only."""
    logger.critical("WATCHDOG ALERT: %s", msg)
    # 텔레그램 알림 시도 (TELEGRAM_BOT_TOKEN 있을 때만)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if token and chat_id:
        try:
            import urllib.request

            payload = json.dumps({"chat_id": chat_id, "text": f"[WATCHDOG] {msg}"}).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception as exc:  # noqa: BLE001
            logger.error("_notify: telegram failed: %s", exc)


# ── WatchdogProcess ──────────────────────────────────────────────────


class WatchdogProcess:
    """Dead-man's switch 프로세스.

    heartbeat stale → DeriskExecutor.derisk_to_floor 직접 트리거.
    resume/re-arm 금지 — de-risk 발동 후 사람만 복구.
    """

    def __init__(
        self,
        exchange: ExchangeAdapter,
        heartbeat_path: Path = HEARTBEAT_PATH,
        timeout_sec: float = HEARTBEAT_TIMEOUT_SEC,
        poll_sec: float = WATCHDOG_POLL_SEC,
        floors: dict[str, float] | None = None,
        _now_fn=None,  # 테스트 주입용 시간 함수
    ) -> None:
        self._exchange = exchange
        self._executor = DeriskExecutor(exchange)
        self._heartbeat_path = heartbeat_path
        self._timeout_sec = timeout_sec
        self._poll_sec = poll_sec
        self._floors = floors if floors is not None else WATCHDOG_FLOORS
        self._now_fn = _now_fn or time.time
        self._triggered = False  # 이미 트리거했는지 (de-risk 중복 방지)

    def tick(self) -> bool:
        """단일 폴링 틱.

        Returns: True = derisk 트리거됨 / False = 정상.
        """
        now = self._now_fn()
        hb = read_heartbeat(self._heartbeat_path)

        if hb is None:
            # heartbeat 파일 없음 → stale로 취급
            logger.warning("tick: heartbeat missing — treating as stale")
            return self._trigger_derisk(now, "heartbeat_missing")

        ts = hb.get("ts", 0.0)
        age = now - ts

        if age > self._timeout_sec:
            logger.warning("tick: heartbeat stale age=%.1fs > timeout=%.1fs", age, self._timeout_sec)
            return self._trigger_derisk(now, f"heartbeat_loss(age={age:.0f}s)")

        # 정상 — 트리거 상태 리셋 (봇이 복구되면 다음 stale 감지 가능)
        if self._triggered:
            logger.info("tick: heartbeat recovered — resetting trigger flag")
            self._triggered = False
        return False

    def _trigger_derisk(self, now: float, reason: str) -> bool:
        """de-risk 트리거. 이미 트리거됐으면 중복 호출 방지."""
        if self._triggered:
            logger.info("_trigger_derisk: already triggered — skip duplicate")
            return True  # 이미 처리됨

        self._triggered = True
        _notify(f"heartbeat_loss → derisk_to_floor | reason={reason}")
        logger.critical("WATCHDOG: triggering derisk_to_floor reason=%s floors=%s", reason, self._floors)

        try:
            result = self._executor.derisk_to_floor(
                floors=self._floors,
                reason=reason,
                now=now,
            )
            logger.warning(
                "WATCHDOG: derisk_to_floor done reduced=%s frozen=%s fully_done=%s",
                result.reduced,
                result.frozen,
                result.fully_done,
            )
            _notify(
                f"derisk_to_floor complete | reduced={result.reduced} frozen={result.frozen}"
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("WATCHDOG: derisk_to_floor exception: %s", exc)
            _notify(f"derisk_to_floor EXCEPTION: {exc}")
        return True

    def run_loop(self) -> None:
        """메인 폴링 루프 (독립 프로세스 진입점)."""
        logger.info(
            "watchdog start: timeout=%.0fs poll=%.0fs floors=%s",
            self._timeout_sec,
            self._poll_sec,
            self._floors,
        )
        while True:
            try:
                self.tick()
            except Exception as exc:  # noqa: BLE001
                logger.error("watchdog: tick exception: %s", exc)
            time.sleep(self._poll_sec)


# ── 진입점 ───────────────────────────────────────────────────────────


def _build_live_exchange() -> ExchangeAdapter:
    """실거래소 어댑터 생성 (go-live 시 실구현으로 교체).

    현재: FakeExchange stub (credential 부재 — 실연결 이연).
    go-live: UpbitExchangeAdapter(key=WATCHDOG_UPBIT_KEY, secret=WATCHDOG_UPBIT_SECRET)
    독립 credential: WATCHDOG_UPBIT_KEY / WATCHDOG_UPBIT_SECRET (봇과 다른 키).
    """
    if WATCHDOG_UPBIT_KEY and WATCHDOG_UPBIT_SECRET:
        # TODO(go-live): return UpbitExchangeAdapter(WATCHDOG_UPBIT_KEY, WATCHDOG_UPBIT_SECRET)
        logger.warning("_build_live_exchange: UpbitExchangeAdapter stub (go-live 미완료)")
    logger.warning("_build_live_exchange: FakeExchange 사용 (독립 credential 미설정 — DRY_RUN 동등)")
    return FakeExchange()


if __name__ == "__main__":
    exchange = _build_live_exchange()
    wd = WatchdogProcess(exchange=exchange)
    wd.run_loop()
