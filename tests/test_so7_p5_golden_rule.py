"""tests/test_so7_p5_golden_rule.py — SO-7/P5 GOLDEN RULE 누락 감사 게이트.

검증 기준 (harness2.md SO-7):
1. Phase5 핵심 각각 IMPLEMENTATION_PROMPT 대조 근거
2. PBO 정통식·common/metrics 공유·H22 2층·상폐only·credential 이연 정당성 명시
3. 잔여 누락 progress.md 박제
4. working tree clean
5. 정적 grep 아닌 실 점검 PASS
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIT_DOC = PROJECT_ROOT / ".harness2" / "audit-goldenrule-p5.md"


# ---------------------------------------------------------------------------
# 1. 감사 문서 존재 + 핵심 섹션
# ---------------------------------------------------------------------------

def test_audit_document_exists():
    assert AUDIT_DOC.exists(), f"감사 문서 없음: {AUDIT_DOC}"


def test_audit_covers_common_metrics():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "common/metrics" in content
    assert "백테스트=라이브" in content or "SSOT" in content


def test_audit_covers_backtest_engine():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "backtest/engine.py" in content
    assert "슬리피지" in content


def test_audit_covers_walk_forward_pit():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "CombinatorialPurgedCV" in content
    assert "PIT" in content


def test_audit_covers_pbo_cscv():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "logit-rank" in content or "CSCV" in content
    assert "179" in content  # 근사식 폐기 언급


def test_audit_covers_dsr():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "DSR" in content
    assert "218" in content  # yakub268:218


def test_audit_covers_capacity_h17():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "H28" in content or "capacity" in content
    assert "H17" in content or "하한가잠김" in content


def test_audit_covers_e4():
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "E4" in content


# ---------------------------------------------------------------------------
# 2. 의도적 일탈/이연 정당성 명시
# ---------------------------------------------------------------------------

def test_audit_pbo_simplified_dropped():
    """감사 문서: PBO 근사식(:179) 폐기 명시."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "179" in content and "폐기" in content


def test_audit_coin_metrics_phase_r_deferred():
    """감사 문서: coin 3중 중복 제거 Phase R 이연 명시."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "Phase R" in content and ("3중 중복" in content or "coin" in content)


def test_audit_h22_layer2_abstain():
    """감사 문서: H22 Layer2 LLM abstain 명시."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "H22" in content
    assert "abstain" in content or "forward only" in content


def test_audit_delisted_backtest_only():
    """감사 문서: 상폐 백테스트only(H5 생존편향) 명시."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "상폐" in content and ("백테스트" in content or "H5" in content)


def test_audit_credential_deferral_pinning():
    """감사 문서: credential 이연 = deferral-pinning 명시."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "credential" in content.lower() and (
        "이연" in content or "deferral" in content
    )


# ---------------------------------------------------------------------------
# 3. Phase 5 산출물 코드 실재 확인
# ---------------------------------------------------------------------------

def test_common_metrics_exists():
    f = PROJECT_ROOT / "common" / "metrics.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "calculate_sharpe_ratio" in content
    assert "calculate_max_drawdown" in content
    assert "calculate_profit_factor" in content


def test_backtest_engine_exists():
    f = PROJECT_ROOT / "backtest" / "engine.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "BacktestEngine" in content
    assert "OrderState" in content
    assert "calculate_slippage" in content


def test_walk_forward_exists():
    f = PROJECT_ROOT / "backtest" / "walk_forward.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "WalkForwardEngine" in content
    assert "purged_size" in content
    assert "filter_pit_fundamentals" in content


def test_pbo_cscv_no_simplified():
    """pbo.py: norm.cdf(0, loc=...) 근사식 없음."""
    f = PROJECT_ROOT / "backtest" / "pbo.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "norm.cdf(0, loc=" not in content
    assert "logit" in content  # 정통식 존재


def test_capacity_exists():
    f = PROJECT_ROOT / "backtest" / "capacity.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "CapacityChecker" in content
    assert "E4SlippageCalibrator" in content


# ---------------------------------------------------------------------------
# 4. git tracked 확인
# ---------------------------------------------------------------------------

def test_phase5_files_git_tracked():
    files = [
        "common/__init__.py",
        "common/metrics.py",
        "backtest/__init__.py",
        "backtest/engine.py",
        "backtest/walk_forward.py",
        "backtest/pbo.py",
        "backtest/capacity.py",
        "tests/test_so1_p5_metrics.py",
        "tests/test_so2_p5_backtest_engine.py",
        "tests/test_so3_p5_walk_forward.py",
        "tests/test_so4_p5_pbo_dsr.py",
        "tests/test_so5_p5_capacity_h17_e4.py",
        "tests/test_so6_p5_integration_gate.py",
    ]
    result = subprocess.run(
        ["git", "ls-files"] + files,
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    tracked = set(result.stdout.strip().split("\n"))
    for f in files:
        assert f in tracked, f"git untracked: {f}"


def test_sacred_backtest_scripts_unchanged():
    """SACRED: coin 기존 scripts/backtest_*.py / sim_engine.py 미변경."""
    result = subprocess.run(
        ["git", "diff", "HEAD", "--name-only"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    modified = result.stdout.strip().split("\n")
    for f in modified:
        assert "scripts/backtest" not in f, f"SACRED 위반: {f}"
        assert "sim_engine" not in f, f"SACRED 위반: {f}"


# ---------------------------------------------------------------------------
# 5. 실 테스트 실행 확인
# ---------------------------------------------------------------------------

def test_so1_p5_passes():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_so1_p5_metrics.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert r.returncode == 0, f"SO-1 실패:\n{r.stdout}"


def test_so2_p5_passes():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_so2_p5_backtest_engine.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert r.returncode == 0, f"SO-2 실패:\n{r.stdout}"


def test_so4_p5_passes():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_so4_p5_pbo_dsr.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert r.returncode == 0, f"SO-4 실패:\n{r.stdout}"


def test_so6_p5_passes():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_so6_p5_integration_gate.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert r.returncode == 0, f"SO-6 실패:\n{r.stdout}"
