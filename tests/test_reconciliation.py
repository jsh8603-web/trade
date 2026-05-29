"""tests/test_reconciliation.py — SO-5 검증 게이트.

검증:
  1. ledger=1.0 / truth=0.5 (N회 일치) → recon_break + ledger overwrite to 0.5 + action 분류.
  2. ⛔ A3 transient stale: truth가 1회만 0 후 정상복귀 → overwrite 0 + quarantine/soft_halt.
  3. ⛔ A3 N회 연속 일치 후 overwrite: N=2 기본값 기준.
  4. tolerance 이내(0.05% diff) → breaks 0, log만.
  5. 대형 delta(>5%) → action=="hard_derisk".
  6. recon_log.jsonl append-only (이전 엔트리 보존).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.reconciliation import (
    RECON_CONFIRM_N,
    reconcile,
    reset_state,
)


@pytest.fixture(autouse=True)
def reset(tmp_path):
    """각 테스트 전 모듈 상태 리셋."""
    reset_state()
    yield


# ── Test 1: N회 일치 후 ledger overwrite ─────────────────────────────

def test_recon_break_and_overwrite(tmp_path: Path) -> None:
    """ledger=1.0, truth=0.5 — N회 일치 후 overwrite to 0.5 + action."""
    log = tmp_path / "recon.jsonl"
    now = 1000.0

    # RECON_CONFIRM_N 회 연속 truth=0.5 입력
    for i in range(RECON_CONFIRM_N):
        result = reconcile(
            intended={"BTC": 1.0},
            ledger={"BTC": 1.0},
            exchange_truth={"BTC": 0.5},
            now=now + i,
            log_path=log,
        )

    # N회째 → overwrite 확정
    assert "BTC" in result.overwritten, "N회 일치 후 ledger overwrite"
    assert abs(result.overwritten["BTC"] - 0.5) < 1e-9, "overwrite 값 = truth(0.5)"
    assert len(result.breaks) >= 1, "recon_break 존재"
    assert result.action in ("soft_halt", "hard_derisk"), "break 시 action 분류"


# ── Test 2: transient zero → quarantine (A3) ─────────────────────────

def test_transient_zero_no_overwrite(tmp_path: Path) -> None:
    """truth 가 1회만 0 → overwrite 0 + quarantine + soft_halt."""
    log = tmp_path / "recon.jsonl"

    # 직전 정상 truth 1.0 기록 (prev 설정)
    reconcile(
        intended={"BTC": 1.0},
        ledger={"BTC": 1.0},
        exchange_truth={"BTC": 1.0},
        now=1000.0,
        log_path=log,
    )
    reset_state()  # samples 리셋하되 prev 기록은 없음 → 첫 번째 0.0 = sanity_zero 감지

    # truth 갑자기 0 (transient zero)
    result = reconcile(
        intended={"BTC": 1.0},
        ledger={"BTC": 1.0},
        exchange_truth={"BTC": 0.0},
        now=1001.0,
        log_path=log,
    )

    assert "BTC" not in result.overwritten, "단일 0 truth → overwrite 금지"
    assert "BTC" in result.quarantined, "의심 truth → quarantine"
    assert result.action in ("soft_halt", "hard_derisk"), "quarantine 시 재매매 차단"


# ── Test 3: N회 연속 일치해야만 overwrite ────────────────────────────

def test_n_consistent_required(tmp_path: Path) -> None:
    """N-1 회에서는 overwrite 안 되고, N회째에서 overwrite."""
    if RECON_CONFIRM_N <= 1:
        pytest.skip("RECON_CONFIRM_N=1: N-1 검증 불필요")

    log = tmp_path / "recon.jsonl"

    # N-1 회: 아직 미확정
    for i in range(RECON_CONFIRM_N - 1):
        r = reconcile(
            intended={"ETH": 2.0},
            ledger={"ETH": 2.0},
            exchange_truth={"ETH": 1.0},
            now=float(i),
            log_path=log,
        )
        assert "ETH" not in r.overwritten, f"{i+1}회째: 아직 overwrite 금지"
        assert "ETH" in r.quarantined, f"{i+1}회째: pending → quarantine"

    # N회째: 확정 → overwrite
    r_n = reconcile(
        intended={"ETH": 2.0},
        ledger={"ETH": 2.0},
        exchange_truth={"ETH": 1.0},
        now=float(RECON_CONFIRM_N),
        log_path=log,
    )
    assert "ETH" in r_n.overwritten, f"{RECON_CONFIRM_N}회째: overwrite 확정"


# ── Test 4: tolerance 이내 → breaks 0, log만 ─────────────────────────

def test_within_tolerance_no_break(tmp_path: Path) -> None:
    """0.05% diff → breaks 0, log 기록만."""
    log = tmp_path / "recon.jsonl"

    # 0.05% = RECON_TOL_PCT(0.1%) 이내
    result = reconcile(
        intended={"BTC": 1.0},
        ledger={"BTC": 1.00045},  # 0.045% diff
        exchange_truth={"BTC": 1.0},
        now=1000.0,
        log_path=log,
    )

    assert len(result.breaks) == 0, "허용 오차 이내 → breaks 0"
    assert result.action == "none", "action=none"
    # log 파일은 ok 이벤트 기록됨
    assert log.exists(), "log 파일 생성됨"
    lines = [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) >= 1


# ── Test 5: 대형 delta → hard_derisk ─────────────────────────────────

def test_large_delta_hard_derisk(tmp_path: Path) -> None:
    """대형 delta(>5%) → action==hard_derisk."""
    log = tmp_path / "recon.jsonl"
    # ledger=1.0, truth=0.9 → 10% diff > RECON_HARD_PCT(5%)
    # N회 연속 일치 필요 → CONFIRM_N 회 입력
    for i in range(RECON_CONFIRM_N):
        result = reconcile(
            intended={"BTC": 1.0},
            ledger={"BTC": 1.0},
            exchange_truth={"BTC": 0.9},
            now=float(i),
            log_path=log,
        )

    assert result.action == "hard_derisk", f"대형 delta → hard_derisk (got: {result.action})"


# ── Test 6: recon_log.jsonl append-only ──────────────────────────────

def test_recon_log_append_only(tmp_path: Path) -> None:
    """recon_log.jsonl — 이전 엔트리 보존(append-only)."""
    log = tmp_path / "recon.jsonl"

    # 1회차
    reconcile(
        intended={"BTC": 1.0},
        ledger={"BTC": 1.0},
        exchange_truth={"BTC": 1.0},
        now=1000.0,
        log_path=log,
    )
    lines_after_1 = [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
    count_1 = len(lines_after_1)

    # 2회차
    reconcile(
        intended={"ETH": 0.5},
        ledger={"ETH": 0.5},
        exchange_truth={"ETH": 0.5},
        now=1001.0,
        log_path=log,
    )
    lines_after_2 = [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
    count_2 = len(lines_after_2)

    assert count_2 > count_1, "2회차 후 라인 수 증가 (append)"
    # 1회차 엔트리가 보존됐는지 (첫 줄 내용 동일)
    assert lines_after_2[:count_1] == lines_after_1, "이전 엔트리 보존"
    # 모든 줄이 유효한 JSON
    for line in lines_after_2:
        obj = json.loads(line)
        assert "ts" in obj and "symbol" in obj, f"유효한 로그 줄: {line}"


# ── Test 7: sanity jump → quarantine ────────────────────────────────

def test_sanity_jump_quarantine(tmp_path: Path) -> None:
    """직전 대비 50%+ 급변 truth → quarantine (transient/stale 의심)."""
    log = tmp_path / "recon.jsonl"

    # 첫 번째 호출: truth=1.0 기록
    reconcile(
        intended={"BTC": 1.0},
        ledger={"BTC": 1.0},
        exchange_truth={"BTC": 1.0},
        now=1000.0,
        log_path=log,
    )

    # 두 번째 호출: truth=0.1 (90% 급감 → sanity_jump)
    r = reconcile(
        intended={"BTC": 1.0},
        ledger={"BTC": 1.0},
        exchange_truth={"BTC": 0.1},
        now=1001.0,
        log_path=log,
    )

    assert "BTC" not in r.overwritten, "sanity jump → overwrite 금지"
    assert "BTC" in r.quarantined, "sanity jump → quarantine"


# ── Test 8: 다중 symbol, action 최대치 ───────────────────────────────

def test_multiple_symbols_action_max(tmp_path: Path) -> None:
    """soft_halt + hard_derisk 동시 존재 → action=hard_derisk (최대치)."""
    log = tmp_path / "recon.jsonl"

    # BTC: 대형 delta(>5%), ETH: 소형 break
    for i in range(RECON_CONFIRM_N):
        result = reconcile(
            intended={"BTC": 1.0, "ETH": 10.0},
            ledger={"BTC": 1.0, "ETH": 10.0},
            exchange_truth={"BTC": 0.9, "ETH": 9.98},  # BTC=10%, ETH=0.2%
            now=float(i),
            log_path=log,
        )

    # BTC 10% → hard_derisk, ETH 0.2% → tolerance or soft
    assert result.action == "hard_derisk", "hard_derisk 우선"
