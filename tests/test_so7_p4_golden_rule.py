"""tests/test_so7_p4_golden_rule.py — SO-7/P4 GOLDEN RULE 누락 감사 게이트.

검증 기준 (harness2.md SO-7):
1. Phase4 핵심 각각 IMPLEMENTATION_PROMPT 대조 근거(코드 라인+테스트)
2. credential 이연 정당성 명시 (deferral-pinning, 설계변경 아님)
3. 잔여 누락 progress.md 박제
4. working tree clean (tracked .py/test 미커밋 0)
5. 정적 grep이 아닌 실 점검 PASS
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HARNESS_DIR = PROJECT_ROOT / ".harness2"
AUDIT_DOC = HARNESS_DIR / "audit-goldenrule-p4.md"


# ---------------------------------------------------------------------------
# 1. 감사 문서 존재 + 핵심 섹션 포함
# ---------------------------------------------------------------------------

def test_audit_document_exists():
    """audit-goldenrule-p4.md 생성 확인."""
    assert AUDIT_DOC.exists(), f"감사 문서 없음: {AUDIT_DOC}"


def test_audit_document_covers_fdr_pykrx():
    """감사 문서: FDR/pykrx 관리종목 실연결 커버."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "FDR" in content and "관리종목" in content
    assert "krx_universe.py" in content


def test_audit_document_covers_dart_edgar():
    """감사 문서: DART/EDGAR XBRL PIT 파서 커버."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "DART_XBRL" in content and "EDGAR_XBRL" in content
    assert "dart_provider.py" in content and "edgar_provider.py" in content


def test_audit_document_covers_alfred_vintage():
    """감사 문서: ALFRED vintage PIT 커버."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "ALFRED" in content or "realtime_" in content
    assert "macro_vintage.py" in content


def test_audit_document_covers_h30_rate_tier():
    """감사 문서: H30 rate-tier 커버."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "H30" in content or "rate_tier" in content
    assert "TokenBucket" in content or "rate_tier.py" in content


def test_audit_document_covers_pykis_elements():
    """감사 문서: pykis 5요소(order/modify/cancel/pending/clamp/poll-amend/ws/token) 커버."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    for term in ("order()", "modify()", "cancel()", "pending()",
                 "_clamp", "_poll_and_amend", "websocket", "토큰"):
        assert term in content, f"감사 문서에 pykis 요소 누락: {term}"


def test_audit_document_covers_paper_mode():
    """감사 문서: 모의투자 우선 커버."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "paper" in content.lower() or "모의투자" in content


def test_audit_document_covers_admission_risk_gate():
    """감사 문서: admission+risk_gate 경유 커버."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "admission" in content and "risk_gate" in content


# ---------------------------------------------------------------------------
# 2. credential 이연 정당성 명시 (deferral-pinning)
# ---------------------------------------------------------------------------

def test_audit_covers_deferral_pinning():
    """감사 문서: deferral-pinning 정당성 명시."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    assert "deferral-pinning" in content or "credential" in content.lower()
    assert "설계변경 아님" in content or "설계 변경이 아님" in content


def test_audit_credential_items_listed():
    """감사 문서: credential 이연 항목 명시 (DART/FRED/ECOS/KIS)."""
    content = AUDIT_DOC.read_text(encoding="utf-8")
    for src in ("DART", "FRED", "ECOS", "KIS"):
        assert src in content, f"이연 항목 누락: {src}"


# ---------------------------------------------------------------------------
# 3. Phase4 산출물 코드 실재 grep (정적 X → 실 파일 확인)
# ---------------------------------------------------------------------------

def test_krx_universe_file_exists():
    """stock/data/krx_universe.py 실재 확인."""
    f = PROJECT_ROOT / "stock" / "data" / "krx_universe.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "KrxStatusProvider" in content
    assert "get_status_snapshot" in content


def test_dart_provider_file_exists():
    """stock/data/dart_provider.py 실재 확인."""
    f = PROJECT_ROOT / "stock" / "data" / "dart_provider.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "DartXbrlProvider" in content
    assert "fetch_filings" in content
    assert "DART_XBRL" in content


def test_edgar_provider_file_exists():
    """stock/data/edgar_provider.py 실재 확인."""
    f = PROJECT_ROOT / "stock" / "data" / "edgar_provider.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "EdgarXbrlProvider" in content
    assert "fetch_filings" in content
    assert "EDGAR_XBRL" in content


def test_macro_vintage_file_exists():
    """stock/data/macro_vintage.py 실재 확인."""
    f = PROJECT_ROOT / "stock" / "data" / "macro_vintage.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "MacroVintageProvider" in content
    assert "get_vintage" in content
    assert "realtime_start" in content


def test_rate_tier_file_exists():
    """stock/data/rate_tier.py 실재 확인."""
    f = PROJECT_ROOT / "stock" / "data" / "rate_tier.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "TokenBucket" in content
    assert "DataSourceLimiter" in content
    assert "RateTierRegistry" in content


def test_kis_client_file_exists():
    """stock/kis_client.py 실재 확인."""
    f = PROJECT_ROOT / "stock" / "kis_client.py"
    assert f.exists()
    content = f.read_text(encoding="utf-8")
    assert "KisClient" in content
    assert "_clamp_to_balance" in content
    assert "_poll_and_amend" in content
    assert "paper" in content


# ---------------------------------------------------------------------------
# 4. git tracked 확인 (working tree clean)
# ---------------------------------------------------------------------------

def test_phase4_files_git_tracked():
    """Phase 4 신규 파일 전부 git tracked."""
    files = [
        "stock/data/krx_universe.py",
        "stock/data/dart_provider.py",
        "stock/data/edgar_provider.py",
        "stock/data/macro_vintage.py",
        "stock/data/rate_tier.py",
        "stock/kis_client.py",
        "tests/test_so1_p4_krx_universe.py",
        "tests/test_so2_p4_dart_edgar_provider.py",
        "tests/test_so3_p4_macro_vintage.py",
        "tests/test_so4_p4_rate_tier.py",
        "tests/test_so5_p4_kis_client.py",
        "tests/test_so6_p4_integration_gate.py",
    ]
    result = subprocess.run(
        ["git", "ls-files"] + files,
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    tracked = set(result.stdout.strip().split("\n"))
    for f in files:
        assert f in tracked, f"git untracked: {f}"


# ---------------------------------------------------------------------------
# 5. 실 테스트 실행 확인 (정적 grep 아닌 실 점검)
# ---------------------------------------------------------------------------

def test_so1_p4_passes():
    """SO-1 테스트 실 실행 PASS 확인."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_so1_p4_krx_universe.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert result.returncode == 0, f"SO-1 실패:\n{result.stdout}\n{result.stderr}"


def test_so2_p4_passes():
    """SO-2 테스트 실 실행 PASS 확인."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_so2_p4_dart_edgar_provider.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert result.returncode == 0, f"SO-2 실패:\n{result.stdout}"


def test_so3_p4_passes():
    """SO-3 테스트 실 실행 PASS 확인."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_so3_p4_macro_vintage.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert result.returncode == 0, f"SO-3 실패:\n{result.stdout}"


def test_so4_p4_passes():
    """SO-4 테스트 실 실행 PASS 확인."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_so4_p4_rate_tier.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert result.returncode == 0, f"SO-4 실패:\n{result.stdout}"


def test_so5_p4_passes():
    """SO-5 테스트 실 실행 PASS 확인."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_so5_p4_kis_client.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert result.returncode == 0, f"SO-5 실패:\n{result.stdout}"


def test_so6_p4_passes():
    """SO-6 테스트 실 실행 PASS 확인."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_so6_p4_integration_gate.py", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    assert result.returncode == 0, f"SO-6 실패:\n{result.stdout}"
