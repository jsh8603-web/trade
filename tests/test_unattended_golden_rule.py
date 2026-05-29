"""tests/test_unattended_golden_rule.py — SO-8 GOLDEN RULE 감사 게이트.

자문 수렴 5축 구현 존재 + SACRED 준수 + 이연 항목 stub 경계 확인.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent


# ── §1. 자문 수렴 5축 산출물 존재 확인 ─────────────────────────────────

def test_axis1_derisk_executor_exists() -> None:
    """축 ①: core/derisk_executor.py 존재 + DeriskExecutor/cancel_only/derisk_to_floor."""
    p = PROJECT_ROOT / "core" / "derisk_executor.py"
    assert p.exists(), "core/derisk_executor.py 존재"
    src = p.read_text(encoding="utf-8")
    assert "class DeriskExecutor" in src
    assert "def cancel_only" in src
    assert "def derisk_to_floor" in src


def test_axis2_unattended_fsm_exists() -> None:
    """축 ②: core/unattended_fsm.py 존재 + 6상태 + hysteresis + PERMANENT_FREEZE."""
    p = PROJECT_ROOT / "core" / "unattended_fsm.py"
    assert p.exists(), "core/unattended_fsm.py 존재"
    src = p.read_text(encoding="utf-8")
    assert "PERMANENT_FREEZE" in src
    assert "HARD_DERISK" in src
    assert "RE_ARM_EVAL" in src
    assert "COOLDOWN" in src
    assert "SOFT_HALT" in src
    assert "NORMAL" in src


def test_axis3_watchdog_exists() -> None:
    """축 ③: scripts/watchdog.py 존재 + WatchdogProcess + 독립 credential."""
    p = PROJECT_ROOT / "scripts" / "watchdog.py"
    assert p.exists(), "scripts/watchdog.py 존재"
    src = p.read_text(encoding="utf-8")
    assert "class WatchdogProcess" in src
    assert "WATCHDOG_UPBIT_KEY" in src       # 독립 credential
    assert "WATCHDOG_UPBIT_SECRET" in src
    assert "def write_heartbeat" in src


def test_axis4_reconciliation_exists() -> None:
    """축 ④: core/reconciliation.py 존재 + reconcile + N-consistent-sample."""
    p = PROJECT_ROOT / "core" / "reconciliation.py"
    assert p.exists(), "core/reconciliation.py 존재"
    src = p.read_text(encoding="utf-8")
    assert "def reconcile" in src
    assert "RECON_CONFIRM_N" in src          # N-consistent-sample 안전장치
    assert "quarantine" in src.lower()


def test_axis5_frozen_bag_exists() -> None:
    """축 ⑤: thin-book frozen bag — _escalate_liquidation + frozen_bag.json."""
    p = PROJECT_ROOT / "core" / "derisk_executor.py"
    src = p.read_text(encoding="utf-8")
    assert "_escalate_liquidation" in src
    assert "MAX_SLIPPAGE" in src
    assert "_record_frozen_bag" in src
    assert "frozen_bag.json" in src


# ── §2. SACRED 준수 정적 검사 ─────────────────────────────────────────

def test_sacred_no_llm_import_in_derisk() -> None:
    """SACRED: derisk_executor + unattended_fsm + watchdog + reconciliation — LLM import 0 (AST)."""
    banned = {"brain", "judge", "llm", "consensus", "HRP"}
    targets = [
        PROJECT_ROOT / "core" / "derisk_executor.py",
        PROJECT_ROOT / "core" / "unattended_fsm.py",
        PROJECT_ROOT / "scripts" / "watchdog.py",
        PROJECT_ROOT / "core" / "reconciliation.py",
    ]
    for path in targets:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                for name in names:
                    for b in banned:
                        assert b.lower() not in name.lower(), \
                            f"LLM 금지 import 발견: {path.name}: {name}"


def test_sacred_no_market_order_in_derisk() -> None:
    """SACRED: derisk_executor — 'market' order 키워드 직접 사용 금지."""
    src = (PROJECT_ROOT / "core" / "derisk_executor.py").read_text(encoding="utf-8")
    # submit_ioc_limit 만 사용, market 주문 제출 금지
    # "market order" 주석 제외 후 실제 호출 확인
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # submit_ioc_limit 만 허용, submit_market 류 금지
            if isinstance(node.func, ast.Attribute):
                assert "market" not in node.func.attr.lower() or "orderbook" in node.func.attr.lower(), \
                    f"market order 호출 의심: {node.func.attr}"


def test_sacred_execute_trade_diff_zero() -> None:
    """SACRED: execute_trade.py git diff=0 (미변경)."""
    result = subprocess.run(
        ["git", "diff", "HEAD", "--", "scripts/execute_trade.py"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.stdout.strip() == "", "execute_trade.py 변경됨 (SACRED 위반)"


def test_sacred_auto_derisk_due_exists_in_risk_gate() -> None:
    """SACRED/U1: risk_gate.py 에 KillSwitch.auto_derisk_due + unattended 존재 (wire 전제)."""
    src = (PROJECT_ROOT / "core" / "risk_gate.py").read_text(encoding="utf-8")
    assert "def auto_derisk_due" in src, "KillSwitch.auto_derisk_due 존재"
    assert "self.unattended" in src, "KillSwitch.unattended 플래그 존재"


# ── §3. H27 무인 anchor 존재 확인 ────────────────────────────────────

def test_h27_halt_entry_anchor_exists() -> None:
    """SO-6: H27BoundedFallback.record_halt_entry 존재 (무인 타임아웃 anchor)."""
    src = (PROJECT_ROOT / "core" / "fallback_policy.py").read_text(encoding="utf-8")
    assert "def record_halt_entry" in src, "H27 record_halt_entry 존재"
    assert "_halt_anchor_ts" in src, "H27 _halt_anchor_ts anchor 존재"


# ── §4. 이연 항목 stub 경계 확인 ─────────────────────────────────────

def test_deferred_native_stop_is_stub() -> None:
    """이연 D2: register_native_stop — stub(실연결 이연) 경계 문서화 확인."""
    src = (PROJECT_ROOT / "scripts" / "watchdog.py").read_text(encoding="utf-8")
    assert "register_native_stop" in src
    # stub 임을 명시 (go-live 이연)
    assert "go-live" in src.lower() or "stub" in src.lower() or "이연" in src, \
        "register_native_stop stub 경계 문서화 확인"


def test_deferred_revoke_key_is_stub() -> None:
    """이연 D3: revoke_bot_api_key — stub(실연결 이연) 경계 문서화 확인."""
    src = (PROJECT_ROOT / "scripts" / "watchdog.py").read_text(encoding="utf-8")
    assert "revoke_bot_api_key" in src
    assert "stub" in src.lower(), "revoke_bot_api_key stub 경계 문서화 확인"


# ── §5. 감사 문서 존재 확인 ───────────────────────────────────────────

def test_audit_document_exists() -> None:
    """SO-8: audit-goldenrule-unattended.md 존재 + 5축 커버 확인."""
    # .harness2/ 는 gitignore → 루트에 배치
    audit = PROJECT_ROOT / "audit-goldenrule-unattended.md"
    if not audit.exists():
        audit = PROJECT_ROOT / ".harness2" / "audit-goldenrule-unattended.md"
    assert audit.exists(), "audit-goldenrule-unattended.md 존재"
    content = audit.read_text(encoding="utf-8")
    # 5축 명시 확인
    for axis in ["derisk_executor", "unattended_fsm", "watchdog", "reconciliation", "frozen_bag"]:
        assert axis in content.lower() or axis.replace("_", " ") in content.lower(), \
            f"감사 문서에 축 '{axis}' 미언급"
    # SACRED 섹션 확인
    assert "SACRED" in content
    # 이연 항목 섹션 확인
    assert "이연" in content


# ── §6. SO-1~7 신규 모듈 전부 git tracked 확인 ───────────────────────

def test_all_new_modules_git_tracked() -> None:
    """SO-1~7 신규 산출물 전부 git ls-files 에 등재됨."""
    new_files = [
        "core/derisk_executor.py",
        "core/unattended_fsm.py",
        "scripts/watchdog.py",
        "core/reconciliation.py",
        "core/fallback_policy.py",   # SO-6 수정
        "scripts/run_agents.py",     # SO-6 wire 수정
        "tests/test_derisk_executor.py",
        "tests/test_unattended_fsm.py",
        "tests/test_watchdog.py",
        "tests/test_reconciliation.py",
        "tests/test_so6_unattended_wire.py",
        "tests/test_so7_unattended_e2e.py",
    ]
    result = subprocess.run(
        ["git", "ls-files"] + new_files,
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    tracked = set(result.stdout.strip().splitlines())
    for f in new_files:
        assert f in tracked, f"git ls-files 미등재: {f}"
