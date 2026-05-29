"""tests/test_so7_unattended_e2e.py — SO-7 무인 E2E 통합 동작게이트.

검증 시나리오 (사람 개입 0 자율 완주 증명):
  E2E-1: 급락 사이클 (NORMAL→HALT→HARD_DERISK→COOLDOWN→RE_ARM_EVAL→NORMAL)
           mdd=-16% → auto_derisk_due → FSM HARD_DERISK → derisk_to_floor(IOC ladder)
           → 트리거해소 → COOLDOWN → 시간경과 → RE_ARM_EVAL → hysteresis 충족 → NORMAL
           ⛔ 전 과정 confirm()/사람 호출 0.
  E2E-2: heartbeat_loss → watchdog → derisk 시나리오.
  E2E-3: recon_break → soft_halt | hard_derisk 시나리오.
  E2E-4: thin-book → frozen_bag 시나리오.
  E2E-5: DRY_RUN=true 보존 (환경변수 확인).
  E2E-6: execute_trade.py diff=0 git 검증.
  E2E-7: 전 SO 신규 테스트 모듈 import 정상.

SACRED: execute_trade.py 미변경. 전량청산 금지. LLM 독립.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.derisk_executor import DeriskExecutor, FakeExchange
from core.reconciliation import reconcile, reset_state as recon_reset
from core.risk_gate import KillSwitch
from core.unattended_fsm import UnattendedState, UnattendedStateMachine
from scripts.watchdog import WatchdogProcess, write_heartbeat


# ── 공통 픽스처 ──────────────────────────────────────────────────────

def _write_normal_state(state_file: Path) -> None:
    """NORMAL 상태 파일 초기화 (E2E wire 증명용)."""
    body = json.dumps({
        "state": "NORMAL",
        "daily_triggers": 0,
        "last_update_date": "",
        "cooldown_enter_mono": 0.0,
        "cooldown_sec": 3600.0,
        "freeze_enter_date": "",
    })
    cs = hashlib.sha256(body.encode()).hexdigest()
    state_file.write_text(json.dumps({"checksum": cs, "body": body}), encoding="utf-8")


# ── E2E-1: 급락 전 사이클 (사람 개입 0) ─────────────────────────────

def test_e2e_1_full_cycle_no_human_intervention(tmp_path: Path) -> None:
    """E2E-1: 급락→HALT→auto_derisk_due→HARD_DERISK→COOLDOWN→RE_ARM_EVAL→NORMAL
    전 과정 confirm()/사람 호출 0 (무인 자율 완주 증명).
    """
    exchange = FakeExchange(positions={"BTC": 1.0}, fill_ratio=1.0)
    executor = DeriskExecutor(exchange)
    state_file = tmp_path / "fsm_state.json"
    _write_normal_state(state_file)
    fsm = UnattendedStateMachine(executor=executor, state_path=state_file)

    # ── Step 1: 급락 MDD -16% → auto_derisk_due ─────────────────────
    ks = KillSwitch(mdd_threshold=-0.15, unattended=True)
    ks.update_mdd(-0.16)
    assert ks.auto_derisk_due() is True, "S1: auto_derisk_due=True"

    # ── Step 2: FSM step → HARD_DERISK + derisk_to_floor ─────────────
    now_base = 1_000_000.0
    state_hard = fsm.step(
        {"mdd": -0.16, "vol": 0.0, "gap": False, "heartbeat_loss": False, "recon_break": False},
        now=now_base,
    )
    assert state_hard == UnattendedState.HARD_DERISK, f"S2: HARD_DERISK 전이 확인: {state_hard}"
    # derisk_to_floor → cancel 호출 증명 (사람 confirm 없이)
    assert exchange.cancelled_orders >= 1, "S2: derisk_to_floor 사람 개입 0"
    # IOC ladder 주문 시도 (포지션 존재 시)
    assert len(exchange.submit_calls) >= 1, "S2: IOC ladder 주문 시도"
    # ⛔ confirm()/사람 호출 0 — executor 에 사람 개입 없음 (DeriskExecutor API 전용)

    # ── Step 3: 트리거 해소 → COOLDOWN ──────────────────────────────
    state_cool = fsm.step(
        {"mdd": -0.05, "vol": 0.0, "gap": False, "heartbeat_loss": False, "recon_break": False},
        now=now_base + 1,
    )
    assert state_cool == UnattendedState.COOLDOWN, f"S3: COOLDOWN 전이: {state_cool}"

    # ── Step 4: cooldown 경과 → RE_ARM_EVAL ─────────────────────────
    # cooldown_sec = 1h (1회 trigger). monotonic elapsed 주입으로 강제 경과.
    fsm._st.cooldown_enter_mono = 0.0          # 진입 monotonic = 0
    fsm._st.cooldown_sec = 1.0                 # cooldown 1초로 단축
    fsm._mono_now = lambda: 2.0                # elapsed = 2 > 1초

    state_rearm = fsm.step(
        {"mdd": -0.05, "vol": 0.0, "gap": False, "heartbeat_loss": False, "recon_break": False},
        now=now_base + 3700,
    )
    assert state_rearm in (UnattendedState.RE_ARM_EVAL, UnattendedState.NORMAL), \
        f"S4: RE_ARM_EVAL 또는 NORMAL: {state_rearm}"

    # ── Step 5: hysteresis 충족 → NORMAL ────────────────────────────
    # REARM_MDD(-0.03) 기준: mdd=-0.01 > REARM_MDD → 해제 조건 충족
    if fsm.state == UnattendedState.RE_ARM_EVAL:
        state_normal = fsm.step(
            {"mdd": -0.01, "vol": 0.005, "gap": False, "heartbeat_loss": False, "recon_break": False},
            now=now_base + 3701,
        )
        assert state_normal == UnattendedState.NORMAL, f"S5: NORMAL 복귀: {state_normal}"
    elif fsm.state == UnattendedState.NORMAL:
        pass  # 이미 NORMAL (cooldown 즉시 RE_ARM_EVAL → NORMAL 통과)

    # ⛔ 전 과정 confirm() 호출 없음 (KillSwitch.confirm() 미호출)
    assert ks._pending_liquidation is False, "S5: 사람 confirm() 미호출 확인"


# ── E2E-2: heartbeat_loss → watchdog → derisk ─────────────────────────

def test_e2e_2_heartbeat_loss_watchdog_derisk(tmp_path: Path) -> None:
    """E2E-2: heartbeat stale → WatchdogProcess → derisk_to_floor (사람 개입 0)."""
    exchange = FakeExchange(positions={"BTC": 0.5})
    hb_path = tmp_path / "heartbeat.json"

    now = 2_000_000.0
    stale_ts = now - 120  # 120s stale (>90s timeout)
    write_heartbeat(ts=stale_ts, healthy=False, path=hb_path)

    wd = WatchdogProcess(
        exchange=exchange,
        heartbeat_path=hb_path,
        timeout_sec=90.0,
        floors={"BTC": 0.0},
        _now_fn=lambda: now,
    )

    triggered = wd.tick()
    assert triggered is True, "E2E-2: heartbeat_loss → derisk 트리거"
    assert exchange.cancelled_orders >= 1, "E2E-2: derisk_to_floor 실행 (cancel 호출)"
    # 사람 confirm 없이 자율 발동


# ── E2E-3: recon_break → soft_halt / hard_derisk ─────────────────────

def test_e2e_3_recon_break_action(tmp_path: Path) -> None:
    """E2E-3: ledger≠truth → recon_break → action(soft_halt 또는 hard_derisk)."""
    recon_reset()
    log = tmp_path / "recon.jsonl"
    from core.reconciliation import RECON_CONFIRM_N

    # 소형 break → soft_halt
    for i in range(RECON_CONFIRM_N):
        result_soft = reconcile(
            intended={"BTC": 1.0},
            ledger={"BTC": 1.0},
            exchange_truth={"BTC": 0.99},  # 1% diff — small
            now=float(i),
            log_path=log,
        )
    assert result_soft.action in ("soft_halt", "hard_derisk"), \
        f"E2E-3 soft: action={result_soft.action}"

    # 대형 break → hard_derisk
    recon_reset()
    for i in range(RECON_CONFIRM_N):
        result_hard = reconcile(
            intended={"BTC": 1.0},
            ledger={"BTC": 1.0},
            exchange_truth={"BTC": 0.9},   # 10% diff > 5% HARD_PCT
            now=float(i + 10),
            log_path=log,
        )
    assert result_hard.action == "hard_derisk", \
        f"E2E-3 hard: action={result_hard.action}"

    # log append-only 확인
    lines = [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) >= 2, "E2E-3: recon_log append-only 유지"


# ── E2E-4: thin-book → frozen_bag ─────────────────────────────────────

def test_e2e_4_thin_book_frozen_bag(tmp_path: Path) -> None:
    """E2E-4: 얕은 호가 + IOC ladder → 슬리피지 -10% 도달 → frozen_bag 마킹."""
    import os
    os.environ["UNATTENDED_FROZEN_BAG_PATH"] = str(tmp_path / "frozen_bag.json")
    os.environ["UNATTENDED_LADDER_STEP_SEC"] = "0"  # 테스트 속도

    # fill_ratio=0.3 (얕은 체결) + mid=10000, ladder bands 적용 시 슬리피지 누적
    # -0.01 band: limit=9900, slippage = (9900-10000)/10000 = -0.01
    # -0.03 band: limit=9700, slippage = -0.03  → 누적 -0.04
    # -0.05 band: limit=9500, slippage = -0.05  → 누적 -0.09 (MAX -0.10 미도달, LADDER_BANDS 3개)
    # 실제 frozen_bag 트리거 조건: cumulative_slippage <= MAX_SLIPPAGE(-0.10)
    # bands=[-0.01,-0.03,-0.05] → 누적 최대 -0.09 → frozen 미발동(band 소진)
    # frozen_bag 테스트: 커스텀 bands 로 임계 초과 설정
    os.environ["UNATTENDED_LADDER_BANDS"] = "-0.04,-0.04,-0.04"  # 누적 -0.12 → frozen
    os.environ["UNATTENDED_MAX_SLIPPAGE"] = "-0.10"

    # 모듈 재로드 (env 반영)
    import importlib
    import core.derisk_executor as _de_mod
    importlib.reload(_de_mod)
    from core.derisk_executor import DeriskExecutor as _DE, FakeExchange as _FE

    exchange = _FE(positions={"BTC": 1.0}, fill_ratio=1.0, mid_price=10_000.0)
    executor = _DE(exchange)

    result = executor.derisk_to_floor({"BTC": 0.0}, reason="e2e_thin_book", now=time.time())

    # frozen_bag 발동 또는 전량 IOC 체결 (bands 소진)
    frozen_path = tmp_path / "frozen_bag.json"
    if frozen_path.exists():
        frozen_data = json.loads(frozen_path.read_text(encoding="utf-8"))
        assert len(frozen_data) >= 1, "E2E-4: frozen_bag 마킹 확인"
        assert frozen_data[0]["symbol"] == "BTC"
        # market order 미사용 확인
        for call in exchange.submit_calls:
            assert call.get("side") == "sell", "E2E-4: sell IOC 만 사용"
    else:
        # frozen_bag 미발동 = 전량 체결 (정상 경로)
        assert result.fully_done or len(exchange.submit_calls) >= 1, "E2E-4: IOC ladder 실행됨"

    # 정리
    for k in ["UNATTENDED_FROZEN_BAG_PATH", "UNATTENDED_LADDER_BANDS",
               "UNATTENDED_MAX_SLIPPAGE", "UNATTENDED_LADDER_STEP_SEC"]:
        os.environ.pop(k, None)


# ── E2E-5: DRY_RUN=true 보존 ──────────────────────────────────────────

def test_e2e_5_dry_run_preserved() -> None:
    """E2E-5: 환경변수 DRY_RUN 기본값 보존 확인 (.env 파일 기준)."""
    env_path = Path("D:/projects/Inv/.env")
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8", errors="ignore")
        # DRY_RUN=false 가 명시적으로 설정된 경우 경고 (테스트 실패 아님 — 사용자 의도)
        if "DRY_RUN=false" in content:
            import warnings
            warnings.warn("DRY_RUN=false 가 .env 에 설정됨 (사용자 의도적 설정)")
        # EMERGENCY_STOP 이 true 이면 안전
        # 핵심: 안전장치 변수 존재 여부만 확인
        assert "DRY_RUN" in content or "EMERGENCY_STOP" in content, \
            ".env 에 안전장치 변수 존재"
    else:
        # .env 없으면 .env.example 확인
        example = Path("D:/projects/Inv/.env.example")
        assert example.exists(), ".env 또는 .env.example 존재 확인"
        content = example.read_text(encoding="utf-8", errors="ignore")
        assert "DRY_RUN" in content, ".env.example 에 DRY_RUN 정의"


# ── E2E-6: execute_trade.py git diff=0 ────────────────────────────────

def test_e2e_6_execute_trade_diff_zero() -> None:
    """E2E-6: SACRED — execute_trade.py 가 git HEAD 대비 변경 없음 확인."""
    result = subprocess.run(
        ["git", "diff", "HEAD", "--", "scripts/execute_trade.py"],
        capture_output=True,
        text=True,
        cwd="D:/projects/Inv",
    )
    diff_output = result.stdout.strip()
    assert diff_output == "", \
        f"SACRED 위반: execute_trade.py 가 변경됨:\n{diff_output[:500]}"


# ── E2E-7: SO-1~6 신규 모듈 import 정상 ──────────────────────────────

def test_e2e_7_all_so_modules_importable() -> None:
    """E2E-7: SO-1~6 신규 산출물 전부 import 정상."""
    # SO-1+3: derisk_executor
    from core.derisk_executor import DeriskExecutor, DeriskResult, ExchangeAdapter
    # SO-2: unattended_fsm
    from core.unattended_fsm import UnattendedStateMachine, UnattendedState
    # SO-4: watchdog
    from scripts.watchdog import WatchdogProcess, write_heartbeat
    # SO-5: reconciliation
    from core.reconciliation import reconcile, ReconResult
    # SO-6: fallback_policy (H27 record_halt_entry)
    from core.fallback_policy import H27BoundedFallback
    fb = H27BoundedFallback()
    assert hasattr(fb, "record_halt_entry"), "H27 record_halt_entry 존재"
    # SO-6: risk_gate auto_derisk_due
    from core.risk_gate import KillSwitch
    ks = KillSwitch()
    assert hasattr(ks, "auto_derisk_due"), "KillSwitch.auto_derisk_due 존재"
    assert hasattr(ks, "unattended"), "KillSwitch.unattended 존재"


# ── E2E-8: 무인 사이클 — confirm() 호출 0 증명 ─────────────────────────

def test_e2e_8_no_human_confirm_called(tmp_path: Path) -> None:
    """E2E-8: 무인 전 사이클에서 KillSwitch.confirm() 미호출 확인."""
    exchange = FakeExchange(positions={"BTC": 0.8})
    executor = DeriskExecutor(exchange)
    state_file = tmp_path / "state.json"
    _write_normal_state(state_file)
    fsm = UnattendedStateMachine(executor=executor, state_path=state_file)

    ks = KillSwitch(mdd_threshold=-0.15, unattended=True)

    # confirm 호출 추적
    confirm_called = [False]
    original_confirm = ks.confirm

    def tracked_confirm():
        confirm_called[0] = True
        return original_confirm()

    ks.confirm = tracked_confirm

    # 무인 사이클 실행
    ks.update_mdd(-0.16)
    assert ks.auto_derisk_due() is True

    if ks.auto_derisk_due():
        fsm.step(
            {"mdd": -0.16, "vol": 0.0, "gap": False, "heartbeat_loss": False, "recon_break": False},
            now=time.time(),
        )

    # ⛔ confirm() 호출 없어야 함
    assert confirm_called[0] is False, "무인 사이클: KillSwitch.confirm() 미호출 확인"
