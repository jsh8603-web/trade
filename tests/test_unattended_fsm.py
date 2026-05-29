"""tests/test_unattended_fsm.py — SO-2 검증 게이트 (시간 주입 기반).

검증 항목:
  1. HALT→COOLDOWN→RE_ARM_EVAL→NORMAL 1사이클
  2. hysteresis: HARD_DERISK 후 mdd=-0.05 → NORMAL 복귀 안 함
  3. 4회 트리거(같은 날) → PERMANENT_FREEZE
  4. 지수 backoff: 2회째 트리거 cooldown_sec==2*3600
  5. whipsawing: MAX_REARM 에서 정지
  6. state_path 영속: 재로드 후 daily_triggers 보존
  7. fail-safe(A1): 파손/빈/checksum 불일치 state.json → HARD_DERISK 기본값
  8. monotonic(A5): wall-clock 조작해도 cooldown 오판 안 함
  9. PERMANENT_FREEZE 무인탈출(A2): 자정 KST → COOLDOWN 자동 복귀
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.derisk_executor import DeriskExecutor, FakeExchange  # noqa: E402
from core.unattended_fsm import (  # noqa: E402
    COOLDOWN_BASE_H,
    MAX_REARM_PER_DAY,
    MDD_HARD,
    MDD_SOFT,
    REARM_MDD,
    SOFT_RELEASE_VOL,
    SOFT_TRIGGER_VOL,
    UnattendedState,
    UnattendedStateMachine,
    _checksum,
    _load_state,
    _save_state,
    _FsmState,
)


# ── 픽스처 ────────────────────────────────────────────────────────────

@pytest.fixture
def fake_exchange():
    return FakeExchange(positions={"BTC": 1.0}, mid_price=50_000.0)


@pytest.fixture
def executor(fake_exchange):
    return DeriskExecutor(fake_exchange)


def make_fsm(
    executor,
    tmp_path,
    mono_start: float = 1000.0,
    wall_now: float | None = None,
) -> tuple[UnattendedStateMachine, list[float]]:
    """FSM + 주입 가능한 monotonic 소스 반환."""
    from datetime import datetime, timezone, timedelta
    KST = timezone(timedelta(hours=9))
    _wall = wall_now if wall_now is not None else 1748527200.0  # 2025-05-30 00:00 KST 기본
    kst_today = datetime.fromtimestamp(_wall, tz=KST).strftime("%Y-%m-%d")

    mono_clock = [mono_start]  # 가변 컨테이너

    def mono_fn():
        return mono_clock[0]

    state_path = tmp_path / "unattended_state.json"
    fsm = UnattendedStateMachine(
        executor=executor,
        state_path=state_path,
        floors={},
        _mono_fn=mono_fn,
    )
    # 초기 상태 강제 NORMAL (fail-safe 기본값=HARD_DERISK, 테스트에서 명시 설정)
    fsm._st.state = UnattendedState.NORMAL
    fsm._st.daily_triggers = 0
    fsm._st.last_update_date = kst_today
    fsm._save()
    return fsm, mono_clock


# 2026-05-30 00:00:00 KST = 2026-05-29 15:00:00 UTC = 1748527200
# 이 값으로 kst_today = "2026-05-30"
WALL_NOW = 1748527200.0  # 2026-05-30 00:00 KST
WALL_TOMORROW = WALL_NOW + 86400.0  # 2026-05-31 00:00 KST


# ── 1. 1사이클 HALT→COOLDOWN→RE_ARM_EVAL→NORMAL ────────────────────

class TestOneCycle:
    def test_full_cycle(self, executor, tmp_path):
        fsm, mono = make_fsm(executor, tmp_path, mono_start=1000.0)

        # NORMAL → HARD_DERISK (mdd=-0.20 <= MDD_HARD=-0.15)
        s = fsm.step({"mdd": -0.20, "vol": 0.0}, now=WALL_NOW)
        assert s == UnattendedState.HARD_DERISK

        # HARD_DERISK → COOLDOWN (트리거 해소)
        s = fsm.step({"mdd": -0.01, "vol": 0.0}, now=WALL_NOW)
        assert s == UnattendedState.COOLDOWN

        # cooldown_sec = 1h (1회 트리거 → 2^0=1 × 3600)
        cooldown_sec = fsm._st.cooldown_sec
        # monotonic 진행: cooldown_sec 초 경과
        mono[0] = fsm._st.cooldown_enter_mono + cooldown_sec + 1.0

        # COOLDOWN → RE_ARM_EVAL
        s = fsm.step({"mdd": -0.01, "vol": 0.0}, now=WALL_NOW)
        assert s == UnattendedState.RE_ARM_EVAL

        # RE_ARM_EVAL → NORMAL (mdd > REARM_MDD, vol < SOFT_RELEASE_VOL)
        s = fsm.step(
            {"mdd": REARM_MDD + 0.01, "vol": SOFT_RELEASE_VOL - 0.001},
            now=WALL_NOW,
        )
        assert s == UnattendedState.NORMAL


# ── 2. hysteresis ────────────────────────────────────────────────────

class TestHysteresis:
    def test_no_normal_below_rearm(self, executor, tmp_path):
        """HARD_DERISK 후 mdd=-0.05 (> HARD 이나 < REARM) → NORMAL 복귀 안 함."""
        fsm, mono = make_fsm(executor, tmp_path, mono_start=1000.0)

        # 트리거
        fsm.step({"mdd": -0.20}, now=WALL_NOW)
        assert fsm.state == UnattendedState.HARD_DERISK

        # 트리거 해소 → COOLDOWN
        fsm.step({"mdd": -0.01}, now=WALL_NOW)
        assert fsm.state == UnattendedState.COOLDOWN

        # cooldown 경과
        mono[0] = fsm._st.cooldown_enter_mono + fsm._st.cooldown_sec + 1.0
        fsm.step({"mdd": -0.01}, now=WALL_NOW)
        assert fsm.state == UnattendedState.RE_ARM_EVAL

        # RE_ARM_EVAL: mdd=-0.05 < REARM_MDD(-0.03) → COOLDOWN 재진입 (NORMAL 금지)
        s = fsm.step({"mdd": -0.05, "vol": 0.001}, now=WALL_NOW)
        assert s != UnattendedState.NORMAL, "hysteresis 위반: NORMAL 복귀"
        assert s == UnattendedState.COOLDOWN


# ── 3. PERMANENT_FREEZE (4회 트리거 같은 날) ─────────────────────────

class TestPermanentFreeze:
    def test_four_triggers_same_day(self, executor, tmp_path):
        """4회 트리거(같은 날) → 4회째 PERMANENT_FREEZE.

        daily_triggers > MAX_REARM_PER_DAY(3) 조건이므로 4회째에 발동.
        """
        fsm, mono = make_fsm(executor, tmp_path, mono_start=1000.0)

        def do_cycle(now_base: float):
            """트리거 → COOLDOWN → RE_ARM_EVAL → NORMAL 1사이클."""
            fsm.step({"mdd": -0.20}, now=now_base)
            fsm.step({"mdd": -0.01}, now=now_base)
            mono[0] = fsm._st.cooldown_enter_mono + fsm._st.cooldown_sec + 1.0
            fsm.step({"mdd": -0.01}, now=now_base)
            fsm.step(
                {"mdd": REARM_MDD + 0.01, "vol": SOFT_RELEASE_VOL - 0.001},
                now=now_base,
            )

        # MAX_REARM_PER_DAY(3)회 정상 사이클 (같은 날)
        for i in range(MAX_REARM_PER_DAY):
            do_cycle(WALL_NOW)
            assert fsm.state == UnattendedState.NORMAL, f"{i+1}회 후 NORMAL 아님: {fsm.state}"

        # MAX_REARM_PER_DAY+1 = 4회째 트리거 → daily_triggers=4 > 3 → PERMANENT_FREEZE
        s = fsm.step({"mdd": -0.20}, now=WALL_NOW)
        assert s == UnattendedState.PERMANENT_FREEZE, f"4회째 후 상태={s}"


# ── 4. 지수 backoff ──────────────────────────────────────────────────

class TestExponentialBackoff:
    def test_second_trigger_cooldown_2h(self, executor, tmp_path):
        """2회째 트리거 후 cooldown_sec == 2 * 3600."""
        fsm, mono = make_fsm(executor, tmp_path, mono_start=1000.0)

        # 1회 트리거 → COOLDOWN → RE_ARM_EVAL → NORMAL
        fsm.step({"mdd": -0.20}, now=WALL_NOW)
        fsm.step({"mdd": -0.01}, now=WALL_NOW)
        mono[0] = fsm._st.cooldown_enter_mono + fsm._st.cooldown_sec + 1.0
        fsm.step({"mdd": -0.01}, now=WALL_NOW)
        fsm.step(
            {"mdd": REARM_MDD + 0.01, "vol": SOFT_RELEASE_VOL - 0.001},
            now=WALL_NOW,
        )
        assert fsm.state == UnattendedState.NORMAL

        # 2회 트리거 → COOLDOWN
        fsm.step({"mdd": -0.20}, now=WALL_NOW)
        fsm.step({"mdd": -0.01}, now=WALL_NOW)
        assert fsm.state == UnattendedState.COOLDOWN

        expected_sec = COOLDOWN_BASE_H * 3600.0 * (2 ** (fsm._st.daily_triggers - 1))
        assert abs(fsm._st.cooldown_sec - expected_sec) < 1.0, (
            f"cooldown_sec={fsm._st.cooldown_sec} expected={expected_sec}"
        )
        # 구체적 2h 검증 (daily_triggers=2 → 2^1=2h)
        assert abs(fsm._st.cooldown_sec - 2 * 3600.0) < 1.0


# ── 5. whipsawing 가드 ───────────────────────────────────────────────

class TestWhipsawing:
    def test_stops_at_max_rearm(self, executor, tmp_path):
        """경계 진동 신호 반복 → MAX_REARM+1 번째에 PERMANENT_FREEZE 정지."""
        fsm, mono = make_fsm(executor, tmp_path, mono_start=1000.0)

        final_state = None
        # MAX_REARM+2 회까지 시도 — MAX_REARM+1 번째 트리거에서 FREEZE 기대
        for i in range(MAX_REARM_PER_DAY + 2):
            s = fsm.step({"mdd": -0.20}, now=WALL_NOW)
            final_state = s
            if s == UnattendedState.PERMANENT_FREEZE:
                break
            # COOLDOWN → RE_ARM_EVAL → NORMAL 복귀
            fsm.step({"mdd": -0.01}, now=WALL_NOW)
            mono[0] = fsm._st.cooldown_enter_mono + fsm._st.cooldown_sec + 1.0
            fsm.step({"mdd": -0.01}, now=WALL_NOW)
            fsm.step(
                {"mdd": REARM_MDD + 0.01, "vol": SOFT_RELEASE_VOL - 0.001},
                now=WALL_NOW,
            )

        assert final_state == UnattendedState.PERMANENT_FREEZE, (
            "MAX_REARM 초과 후 PERMANENT_FREEZE 미발동"
        )
        # 이후 추가 step → 여전히 PERMANENT_FREEZE (같은 날)
        s2 = fsm.step({"mdd": -0.20}, now=WALL_NOW)
        assert s2 == UnattendedState.PERMANENT_FREEZE


# ── 6. 영속성: 재로드 후 daily_triggers 보존 ─────────────────────────

class TestPersistence:
    def test_reload_preserves_daily_triggers(self, executor, tmp_path):
        """state.json 재로드 후 daily_triggers 보존."""
        fsm, mono = make_fsm(executor, tmp_path, mono_start=1000.0)
        state_path = fsm._state_path

        fsm.step({"mdd": -0.20}, now=WALL_NOW)
        triggers_before = fsm._st.daily_triggers

        # 재로드
        from core.unattended_fsm import _load_state
        loaded = _load_state(state_path)
        assert loaded.daily_triggers == triggers_before, (
            f"재로드 후 daily_triggers 불일치: {loaded.daily_triggers} != {triggers_before}"
        )


# ── 7. fail-safe (A1): 파손/checksum 불일치 → HARD_DERISK ──────────

class TestFailSafe:
    def test_corrupted_json_defaults_hard_derisk(self, tmp_path):
        """빈/깨진 state.json → HARD_DERISK 기본값 반환."""
        state_path = tmp_path / "unattended_state.json"
        state_path.write_text("not json at all", encoding="utf-8")
        loaded = _load_state(state_path)
        assert loaded.state == UnattendedState.HARD_DERISK, (
            f"파손 파일에서 기본값 HARD_DERISK 아님: {loaded.state}"
        )

    def test_checksum_mismatch_defaults_hard_derisk(self, tmp_path):
        """checksum 불일치 → HARD_DERISK."""
        state_path = tmp_path / "unattended_state.json"
        # 정상 body + 잘못된 checksum
        body = json.dumps({"state": "NORMAL", "daily_triggers": 0,
                           "last_update_date": "", "cooldown_enter_mono": 0.0,
                           "cooldown_sec": 3600.0, "freeze_enter_date": ""})
        payload = {"checksum": "badhash", "body": body}
        state_path.write_text(json.dumps(payload), encoding="utf-8")
        loaded = _load_state(state_path)
        assert loaded.state == UnattendedState.HARD_DERISK

    def test_empty_file_defaults_hard_derisk(self, tmp_path):
        """빈 파일 → HARD_DERISK."""
        state_path = tmp_path / "unattended_state.json"
        state_path.write_text("", encoding="utf-8")
        loaded = _load_state(state_path)
        assert loaded.state == UnattendedState.HARD_DERISK

    def test_missing_file_defaults_hard_derisk(self, tmp_path):
        """파일 없음 → HARD_DERISK."""
        state_path = tmp_path / "nonexistent_state.json"
        loaded = _load_state(state_path)
        assert loaded.state == UnattendedState.HARD_DERISK


# ── 8. monotonic (A5): wall-clock 조작 내성 ──────────────────────────

class TestMonotonicCooldown:
    def test_wallclock_jump_no_early_release(self, executor, tmp_path):
        """wall-clock 을 미래로 조작해도 monotonic 미경과면 COOLDOWN 유지."""
        fsm, mono = make_fsm(executor, tmp_path, mono_start=1000.0)

        # HARD_DERISK → COOLDOWN
        fsm.step({"mdd": -0.20}, now=WALL_NOW)
        fsm.step({"mdd": -0.01}, now=WALL_NOW)
        assert fsm.state == UnattendedState.COOLDOWN

        cooldown_sec = fsm._st.cooldown_sec
        # wall-clock만 수십 시간 앞으로 (NTP jump 시뮬레이션)
        far_future_wall = WALL_NOW + 86400.0  # 하루 뒤

        # monotonic은 아직 1초만 경과 (cooldown 미완)
        mono[0] = fsm._st.cooldown_enter_mono + 1.0

        s = fsm.step({"mdd": -0.01}, now=far_future_wall)
        # wall-clock 이 크게 앞서도, monotonic 미경과 → COOLDOWN 유지
        assert s == UnattendedState.COOLDOWN, (
            f"wall-clock jump 후 monotonic 미경과인데 {s} 로 전이"
        )

    def test_monotonic_elapsed_triggers_rearm(self, executor, tmp_path):
        """monotonic 경과 시 정상 RE_ARM_EVAL 전이."""
        fsm, mono = make_fsm(executor, tmp_path, mono_start=1000.0)

        fsm.step({"mdd": -0.20}, now=WALL_NOW)
        fsm.step({"mdd": -0.01}, now=WALL_NOW)
        assert fsm.state == UnattendedState.COOLDOWN

        # monotonic 경과
        mono[0] = fsm._st.cooldown_enter_mono + fsm._st.cooldown_sec + 10.0
        s = fsm.step({"mdd": -0.01}, now=WALL_NOW)
        assert s == UnattendedState.RE_ARM_EVAL


# ── 9. PERMANENT_FREEZE 무인탈출 (A2): 자정 KST → COOLDOWN ──────────

class TestFreezeAutoRelease:
    def test_freeze_releases_at_midnight_kst(self, executor, tmp_path):
        """FREEZE 상태 + 자정 KST 경과 → COOLDOWN 자동 복귀 (사람 confirm 0)."""
        from datetime import datetime, timezone, timedelta
        KST = timezone(timedelta(hours=9))
        today_kst = datetime.fromtimestamp(WALL_NOW, tz=KST).strftime("%Y-%m-%d")

        fsm, mono = make_fsm(executor, tmp_path, mono_start=1000.0)

        # PERMANENT_FREEZE 강제 진입 (오늘 KST 날짜)
        fsm._st.state = UnattendedState.PERMANENT_FREEZE
        fsm._st.freeze_enter_date = today_kst
        fsm._st.last_update_date = today_kst
        fsm._save()

        # 자정 이후 (내일 KST = WALL_TOMORROW)
        s = fsm.step({"mdd": -0.01}, now=WALL_TOMORROW)
        assert s == UnattendedState.COOLDOWN, (
            f"자정 경과 후 PERMANENT_FREEZE 미해제: {s}"
        )

    def test_freeze_same_day_stays(self, executor, tmp_path):
        """FREEZE 상태, 같은 날 → 유지 (탈출 안 함)."""
        from datetime import datetime, timezone, timedelta
        KST = timezone(timedelta(hours=9))
        # WALL_NOW + 3600 의 KST 날짜를 직접 계산하여 freeze_enter_date로 사용
        now_plus_1h = WALL_NOW + 3600
        today_kst_at_step = datetime.fromtimestamp(now_plus_1h, tz=KST).strftime("%Y-%m-%d")

        fsm, mono = make_fsm(executor, tmp_path, mono_start=1000.0)
        fsm._st.state = UnattendedState.PERMANENT_FREEZE
        # freeze_enter_date = step 시점과 동일한 날 → 탈출 안 함
        fsm._st.freeze_enter_date = today_kst_at_step
        fsm._st.last_update_date = today_kst_at_step
        fsm._save()

        s = fsm.step({"mdd": -0.01}, now=now_plus_1h)
        assert s == UnattendedState.PERMANENT_FREEZE
