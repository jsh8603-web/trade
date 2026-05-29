"""tests/test_so8_p6_golden_rule.py — SO-8/P6 GOLDEN RULE 누락 감사 게이트.

검증 기준 (harness2.md SO-8):
1. Phase6 핵심 각각 IMPLEMENTATION_PROMPT 대조 근거
2. 6개 불변식/이연 정당성 명시
3. 잔여 누락 progress.md 박제
4. working tree clean + core/brain tracked화 확인
5. 정적 grep 아닌 실 점검 PASS
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIT_DOC = PROJECT_ROOT / ".harness2" / "audit-goldenrule-p6.md"


# ---------------------------------------------------------------------------
# 1. 감사 문서 존재 + 핵심 섹션
# ---------------------------------------------------------------------------

def test_audit_document_exists():
    assert AUDIT_DOC.exists(), f"감사 문서 없음: {AUDIT_DOC}"


def test_audit_covers_bl_pi():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "BL" in content and "pi" in content.lower()
    assert "portfolio_orchestrator" in content


def test_audit_covers_drift_monitor():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "Drift Monitor" in content or "drift" in content.lower()
    assert "NearMissVeto" in content or "near_miss_veto" in content


def test_audit_covers_consensus():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "consensus" in content.lower()
    assert "risk_gate" in content


def test_audit_covers_moosoon1():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "모순1" in content or "budget_ledger" in content
    assert "N3" in content or "rpm" in content.lower()


def test_audit_covers_h27_h26_h29():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    for h in ("H27", "H26", "H29"):
        assert h in content, f"H-항목 미언급: {h}"


def test_audit_covers_g8_dashboard():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "G8" in content or "대시보드" in content
    assert "multi_asset_view" in content


# ---------------------------------------------------------------------------
# 2. 6개 불변식/이연 정당성 명시
# ---------------------------------------------------------------------------

def test_audit_bl_invariant_mentioned():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "pi 주입 불변식" in content or "BL pi" in content


def test_audit_consensus_backstop_mentioned():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "백스톱" in content or "risk_gate 항상" in content


def test_audit_exp_drop_rejection_mentioned():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "e^|Drop|" in content or "기각" in content


def test_audit_pit_backfill0_mentioned():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "backfill" in content or "PIT" in content


def test_audit_90d_deferred():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "90일" in content and ("이연" in content or "go-live" in content)


def test_audit_credential_deferral_mentioned():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "credential" in content.lower() and "이연" in content


# ---------------------------------------------------------------------------
# 3. Phase 6 산출물 코드 실재
# ---------------------------------------------------------------------------

def test_portfolio_orchestrator_exists():
    f = PROJECT_ROOT / "core" / "portfolio_orchestrator.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "PortfolioOrchestrator" in content
    assert "monitor_band_drift" in content


def test_consensus_exists():
    f = PROJECT_ROOT / "core" / "consensus.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "ConsensusJudge" in content
    assert "DecisionRecord" in content


def test_budget_ledger_exists():
    f = PROJECT_ROOT / "core" / "budget_ledger.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "BudgetLedger" in content
    assert "N3RetryPolicy" in content
    assert "math.exp(abs" not in content  # e^|Drop| 기각


def test_fallback_policy_exists():
    f = PROJECT_ROOT / "core" / "fallback_policy.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "H27BoundedFallback" in content
    assert "H26FxGuard" in content
    assert "H29MacroAbstain" in content


def test_dashboard_multiasset_exists():
    f = PROJECT_ROOT / "dashboard" / "multi_asset_view.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "MultiAssetDashboard" in content
    assert "run_script" in content


# ---------------------------------------------------------------------------
# 4. git tracked 확인 + core/brain tracked화
# ---------------------------------------------------------------------------

def test_phase6_files_git_tracked():
    files = [
        "core/portfolio_orchestrator.py",
        "core/consensus.py",
        "core/budget_ledger.py",
        "core/fallback_policy.py",
        "dashboard/__init__.py",
        "dashboard/multi_asset_view.py",
        "core/brain/regime_classifier.py",
        "core/brain/macro_reasoning.py",
        "core/brain/regime_to_weights.py",
        "core/brain/macro_schema.py",
        "tests/test_so1_p6_orchestrator_bl.py",
        "tests/test_so7_p6_integration_gate.py",
    ]
    result = subprocess.run(
        ["git", "ls-files"] + files,
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    tracked = set(result.stdout.strip().split("\n"))
    for f in files:
        assert f in tracked, f"git untracked: {f}"


def test_sacred_coin_live_unchanged():
    """SACRED: coin 라이브 실거래 경로 미변경."""
    result = subprocess.run(
        ["git", "diff", "HEAD", "--name-only"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    modified = result.stdout.strip().split("\n")
    for f in modified:
        assert "execute_trade" not in f, f"SACRED 위반: {f}"
        assert "live_trader" not in f, f"SACRED 위반: {f}"


# ---------------------------------------------------------------------------
# 5. 실 테스트 실행 확인
# ---------------------------------------------------------------------------

def test_so1_p6_passes():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_so1_p6_orchestrator_bl.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert r.returncode == 0, f"SO-1 P6 실패:\n{r.stdout}"


def test_so4_p6_passes():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_so4_p6_budget_moosoon.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert r.returncode == 0, f"SO-4 P6 실패:\n{r.stdout}"


def test_so7_p6_passes():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_so7_p6_integration_gate.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert r.returncode == 0, f"SO-7 P6 실패:\n{r.stdout}"
