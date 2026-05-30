"""core/unattended_fsm.py — 무인 자동 re-arm 상태기계 (Phase Unattended SO-2).

6상태 FSM + hysteresis + 지수 backoff + 일일 상한 + SR Pre-Review C 하드닝.

설계 원칙:
  - state.json 쓰기 = tmp+fsync+rename 원자적 + body checksum.
  - load 실패 / 파일 없음 / checksum 불일치 → 기본값 HARD_DERISK (절대 NORMAL 금지).
  - cooldown 경과 = monotonic 기준 경과시간 (wall-clock 직접 비교 금지).
  - PERMANENT_FREEZE → 자정 KST 자동 COOLDOWN 복귀 (무인 탈출 보장, A2).
  - LLM/brain/judge import 0.

SACRED: LLM/brain/HRP import 0. execute_trade.py 미변경. DRY_RUN 보존.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.derisk_executor import DeriskExecutor

logger = logging.getLogger("core.unattended_fsm")

KST = timezone(timedelta(hours=9))

# ── 환경 변수 파라미터 ─────────────────────────────────────────────────

MDD_SOFT        = float(os.environ.get("UNATTENDED_MDD_SOFT",  "-0.08"))   # -8%
MDD_HARD        = float(os.environ.get("UNATTENDED_MDD_HARD",  "-0.15"))   # -15%
REARM_MDD       = float(os.environ.get("UNATTENDED_REARM_MDD", "-0.03"))   # -3% (hysteresis)

SOFT_TRIGGER_VOL  = float(os.environ.get("UNATTENDED_SOFT_TRIGGER_VOL",  "0.05"))  # vol 트리거
SOFT_RELEASE_VOL  = float(os.environ.get("UNATTENDED_SOFT_RELEASE_VOL",  "0.02"))  # vol 해제

COOLDOWN_BASE_H   = float(os.environ.get("UNATTENDED_COOLDOWN_BASE_H",   "1.0"))   # 기본 1h
MAX_COOLDOWN_SEC  = float(os.environ.get("UNATTENDED_MAX_COOLDOWN_SEC",  str(24 * 3600.0)))  # backoff 상한 (Phase Gate)
MAX_REARM_PER_DAY = int(os.environ.get("UNATTENDED_MAX_REARM_PER_DAY",   "3"))     # 일일 상한

_DEFAULT_STATE_PATH = Path(os.environ.get(
    "UNATTENDED_STATE_PATH", "data/unattended_state.json"
))

# floors: de-risk 목표 (symbol→목표수량). 여기서는 전 symbol 20% 잔존 기본값.
# 실 운용에서 SO-6 wire 시 포트폴리오 컨텍스트로 주입.
DEFAULT_FLOORS: dict[str, float] = {}  # 빈 dict = derisk_to_floor가 0으로 처리


# ── 상태 Enum ─────────────────────────────────────────────────────────

class UnattendedState(str, Enum):
    NORMAL          = "NORMAL"
    SOFT_HALT       = "SOFT_HALT"
    HARD_DERISK     = "HARD_DERISK"
    COOLDOWN        = "COOLDOWN"
    RE_ARM_EVAL     = "RE_ARM_EVAL"
    PERMANENT_FREEZE = "PERMANENT_FREEZE"


# ── 영속 상태 데이터 ──────────────────────────────────────────────────

@dataclass
class _FsmState:
    """state.json 직렬화 단위."""
    state: str = UnattendedState.HARD_DERISK  # fail-safe 기본값
    daily_triggers: int = 0
    last_update_date: str = ""          # KST 날짜 문자열 (YYYY-MM-DD)
    cooldown_enter_mono: float = 0.0    # monotonic 기준 cooldown 진입 시각
    cooldown_sec: float = COOLDOWN_BASE_H * 3600.0
    freeze_enter_date: str = ""         # PERMANENT_FREEZE 진입 KST 날짜


def _checksum(body: str) -> str:
    return hashlib.sha256(body.encode()).hexdigest()


def _save_state(path: Path, st: _FsmState) -> None:
    """원자적 쓰기 (tmp+fsync+rename) + body checksum."""
    body = json.dumps(asdict(st), ensure_ascii=False)
    payload = {"checksum": _checksum(body), "body": body}
    text = json.dumps(payload, ensure_ascii=False)

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    except Exception as exc:  # noqa: BLE001
        logger.error("_save_state: write failed: %s", exc)
        try:
            tmp.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass


def _load_state(path: Path) -> _FsmState:
    """로드 실패 / checksum 불일치 → HARD_DERISK 기본값 반환 (절대 NORMAL 금지)."""
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
        body: str = payload["body"]
        if _checksum(body) != payload["checksum"]:
            logger.error("_load_state: checksum mismatch — defaulting HARD_DERISK")
            return _FsmState()
        data = json.loads(body)
        return _FsmState(**data)
    except FileNotFoundError:
        logger.info("_load_state: state file missing — defaulting HARD_DERISK")
        return _FsmState()
    except Exception as exc:  # noqa: BLE001
        logger.error("_load_state: load failed (%s) — defaulting HARD_DERISK", exc)
        return _FsmState()


# ── UnattendedStateMachine ────────────────────────────────────────────

class UnattendedStateMachine:
    """무인 자동 re-arm 상태기계.

    step(signals, now) → UnattendedState.
    signals: {mdd, vol, gap, heartbeat_loss, recon_break}.
    now: wall-clock epoch (float). monotonic 타이머는 내부 관리.
    """

    def __init__(
        self,
        executor: "DeriskExecutor",
        state_path: Path | str = _DEFAULT_STATE_PATH,
        floors: dict[str, float] | None = None,
        _mono_fn=None,  # 테스트 주입: monotonic 대체 함수
    ) -> None:
        self._executor = executor
        self._state_path = Path(state_path)
        self._floors = floors if floors is not None else DEFAULT_FLOORS
        self._mono_fn = _mono_fn or time.monotonic

        # 영속 상태 로드 (실패 → HARD_DERISK)
        self._st = _load_state(self._state_path)
        # monotonic 기준 오프셋: 현재 monotonic - cooldown_enter_mono 는 저장 당시 값
        # 재시작 후 monotonic 이 리셋될 수 있어, 재시작 후 첫 step에서 cooldown_enter_mono 재보정
        self._start_mono = self._mono_fn()
        self._start_wall = time.time()

    # ── Public ────────────────────────────────────────────────────────

    @property
    def state(self) -> UnattendedState:
        return UnattendedState(self._st.state)

    @property
    def daily_triggers(self) -> int:
        return self._st.daily_triggers

    def step(self, signals: dict, now: float) -> UnattendedState:
        """FSM 1 tick 진행.

        signals keys: mdd(float), vol(float), gap(bool),
                      heartbeat_loss(bool), recon_break(bool).
        now: wall-clock epoch (float).
        """
        mdd            = float(signals.get("mdd", 0.0))
        vol            = float(signals.get("vol", 0.0))
        gap            = bool(signals.get("gap", False))
        heartbeat_loss = bool(signals.get("heartbeat_loss", False))
        recon_break    = bool(signals.get("recon_break", False))

        kst_today = datetime.fromtimestamp(now, tz=KST).strftime("%Y-%m-%d")

        # 자정 KST 리셋 (daily_triggers + PERMANENT_FREEZE 무인탈출)
        self._maybe_daily_reset(kst_today)

        # PERMANENT_FREEZE 무인 탈출 (A2): 자정 지나면 COOLDOWN 복귀
        if self.state == UnattendedState.PERMANENT_FREEZE:
            if self._st.freeze_enter_date and self._st.freeze_enter_date < kst_today:
                logger.warning(
                    "PERMANENT_FREEZE → COOLDOWN (자정 KST 무인탈출, date %s → %s)",
                    self._st.freeze_enter_date, kst_today,
                )
                self._enter_cooldown(now, triggered_by="freeze_auto_release")
                self._save()
                return self.state
            # 아직 같은 날 → 유지
            self._save()
            return UnattendedState.PERMANENT_FREEZE

        # 하드 트리거 분리 (Phase Gate 품질 P0 / 보안 절충):
        #  - mdd_hard: 시장 급락. NORMAL/SOFT_HALT 에서만 신규 발동. COOLDOWN/RE_ARM_EVAL 중
        #    재급락은 RE_ARM_EVAL 의 재무장 차단(mdd>REARM_MDD 아니면 NORMAL 복귀 거부)이 커버 →
        #    과도한 daily_triggers 소진(whipsawing→조기 FREEZE) 방지.
        #  - infra_hard: 봇 정지(heartbeat_loss)·장부 불일치(recon_break). 시장 cooldown 과 무관한
        #    인프라 위험 → COOLDOWN/RE_ARM_EVAL 중에도 즉시 재집행 (HARD_DERISK 진행 중만 제외).
        mdd_hard   = (mdd <= MDD_HARD)
        infra_hard = heartbeat_loss or recon_break
        hard_trigger = mdd_hard or infra_hard
        if infra_hard and self.state != UnattendedState.HARD_DERISK:
            return self._trigger_hard(mdd, heartbeat_loss, recon_break, now, kst_today)
        if mdd_hard and self.state not in (
            UnattendedState.HARD_DERISK,
            UnattendedState.COOLDOWN,
            UnattendedState.RE_ARM_EVAL,
        ):
            return self._trigger_hard(mdd, heartbeat_loss, recon_break, now, kst_today)

        cur = self.state

        if cur == UnattendedState.NORMAL:
            soft_trigger = (mdd <= MDD_SOFT) or (vol >= SOFT_TRIGGER_VOL) or gap
            if soft_trigger:
                return self._trigger_soft(mdd, vol, gap, now, kst_today)
            # 정상 — 저장 후 반환
            self._save()
            return UnattendedState.NORMAL

        elif cur == UnattendedState.SOFT_HALT:
            # SOFT_HALT: hard 트리거 → HARD_DERISK (위에서 처리)
            # 트리거 해소(soft release) → COOLDOWN
            soft_resolved = (mdd > MDD_SOFT) and (vol < SOFT_RELEASE_VOL) and not gap
            if soft_resolved:
                self._enter_cooldown(now, triggered_by="soft_resolved")
                self._save()
                return self.state
            self._save()
            return UnattendedState.SOFT_HALT

        elif cur == UnattendedState.HARD_DERISK:
            # hard 트리거 중이면 유지
            if hard_trigger:
                self._save()
                return UnattendedState.HARD_DERISK
            # 트리거 해소 → COOLDOWN
            self._enter_cooldown(now, triggered_by="hard_resolved")
            self._save()
            return self.state

        elif cur == UnattendedState.COOLDOWN:
            # monotonic 기준 경과시간 판단 (wall-clock 직접 비교 금지, A5)
            elapsed = self._mono_elapsed_since_enter()
            if elapsed >= self._st.cooldown_sec:
                self._st.state = UnattendedState.RE_ARM_EVAL
                logger.info("COOLDOWN → RE_ARM_EVAL (elapsed=%.0fs)", elapsed)
                self._save()
                return UnattendedState.RE_ARM_EVAL
            self._save()
            return UnattendedState.COOLDOWN

        elif cur == UnattendedState.RE_ARM_EVAL:
            # 해제 조건: mdd > REARM_MDD AND vol < SOFT_RELEASE_VOL
            release_ok = (mdd > REARM_MDD) and (vol < SOFT_RELEASE_VOL)
            if release_ok:
                logger.info("RE_ARM_EVAL → NORMAL (mdd=%.4f, vol=%.4f)", mdd, vol)
                self._st.state = UnattendedState.NORMAL
                self._executor.clear_entry_block()
                self._save()
                return UnattendedState.NORMAL
            else:
                # 미충족 → 다시 COOLDOWN
                logger.info(
                    "RE_ARM_EVAL → COOLDOWN (미충족: mdd=%.4f REARM=%.4f, vol=%.4f RELEASE=%.4f)",
                    mdd, REARM_MDD, vol, SOFT_RELEASE_VOL,
                )
                self._enter_cooldown(now, triggered_by="rearm_eval_fail")
                self._save()
                return self.state

        self._save()
        return self.state

    # ── Private helpers ───────────────────────────────────────────────

    def _trigger_soft(
        self,
        mdd: float,
        vol: float,
        gap: bool,
        now: float,
        kst_today: str,
    ) -> UnattendedState:
        logger.warning(
            "SOFT_HALT 트리거 (mdd=%.4f, vol=%.4f, gap=%s)", mdd, vol, gap
        )
        self._st.state = UnattendedState.SOFT_HALT
        self._increment_daily(kst_today)  # → PERMANENT_FREEZE 로 바뀔 수 있음
        self._executor.cancel_only(reason=f"soft_halt mdd={mdd:.4f} vol={vol:.4f}")
        self._save()
        return self.state  # PERMANENT_FREEZE 반영

    def _trigger_hard(
        self,
        mdd: float,
        heartbeat_loss: bool,
        recon_break: bool,
        now: float,
        kst_today: str,
    ) -> UnattendedState:
        logger.warning(
            "HARD_DERISK 트리거 (mdd=%.4f, hl=%s, rb=%s)", mdd, heartbeat_loss, recon_break
        )
        self._st.state = UnattendedState.HARD_DERISK
        self._increment_daily(kst_today)  # → PERMANENT_FREEZE 로 바뀔 수 있음
        reason = f"hard_derisk mdd={mdd:.4f} hl={heartbeat_loss} rb={recon_break}"
        self._executor.derisk_to_floor(self._floors, reason=reason, now=now)
        self._save()
        return self.state  # PERMANENT_FREEZE 반영 위해 self.state 반환

    def _enter_cooldown(self, now: float, triggered_by: str) -> None:
        """COOLDOWN 진입 — monotonic 기준 enter 타이밍 기록."""
        self._st.cooldown_enter_mono = self._mono_fn()
        self._st.cooldown_sec = self._calc_cooldown_sec()
        self._st.state = UnattendedState.COOLDOWN
        logger.info(
            "→ COOLDOWN (by=%s, cooldown_sec=%.0f)", triggered_by, self._st.cooldown_sec
        )

    def _increment_daily(self, kst_today: str) -> None:
        """daily_triggers 증가 + 일일 상한 초과 시 PERMANENT_FREEZE."""
        self._st.daily_triggers += 1
        self._st.last_update_date = kst_today
        logger.debug("daily_triggers=%d / max=%d", self._st.daily_triggers, MAX_REARM_PER_DAY)
        if self._st.daily_triggers > MAX_REARM_PER_DAY:
            logger.warning(
                "PERMANENT_FREEZE: daily_triggers=%d > MAX=%d",
                self._st.daily_triggers, MAX_REARM_PER_DAY,
            )
            self._st.state = UnattendedState.PERMANENT_FREEZE
            self._st.freeze_enter_date = kst_today

    def _maybe_daily_reset(self, kst_today: str) -> None:
        """자정 KST 경과 시 daily_triggers 리셋 (last_update_date 상태값 비교)."""
        if self._st.last_update_date and self._st.last_update_date < kst_today:
            logger.info(
                "자정 KST 리셋: last=%s today=%s, daily_triggers %d→0",
                self._st.last_update_date, kst_today, self._st.daily_triggers,
            )
            self._st.daily_triggers = 0
            self._st.last_update_date = kst_today

    def _calc_cooldown_sec(self) -> float:
        """지수 backoff: base_h * 3600 * 2^(daily_triggers-1), 상한 MAX_COOLDOWN_SEC (폭발 방지)."""
        exp = max(0, self._st.daily_triggers - 1)
        sec = COOLDOWN_BASE_H * 3600.0 * (2 ** exp)
        return min(sec, MAX_COOLDOWN_SEC)

    def _mono_elapsed_since_enter(self) -> float:
        """monotonic 기준 cooldown_enter 이후 경과 시간(초).

        재시작 후 monotonic 이 리셋돼 cooldown_enter_mono 보다 현재 값이
        작을 수 있다 → 그런 경우 0 반환(보수적: 아직 미경과 판정).
        """
        now_mono = self._mono_fn()
        enter = self._st.cooldown_enter_mono
        if now_mono < enter:
            # 재시작 등으로 monotonic 리셋됨 — 보수적으로 0 반환
            return 0.0
        return now_mono - enter

    def _save(self) -> None:
        _save_state(self._state_path, self._st)
