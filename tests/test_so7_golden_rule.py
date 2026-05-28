"""SO-7 GOLDEN RULE 누락 감사 게이트 — Phase 3.

검증기준:
- Phase3 핵심 6항목 IMPLEMENTATION_PROMPT 대조 실재 확인(grep + 실행)
- 의도적 일탈 명시
- working tree clean(tracked .py 미커밋 0)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

STOCK_DIR = PROJECT_ROOT / "stock"
CORE_DIR = PROJECT_ROOT / "core"


# ── 커버 항목 1: 2단 트리거 실재 ────────────────────────────────────

def test_golden_rule_two_stage_trigger():
    """§Phase3 L282-283: passes_gate1 + run_value_trigger heavy_agent 경유."""
    vt_src = (STOCK_DIR / "value_trigger.py").read_text(encoding="utf-8")
    assert "passes_gate1" in vt_src
    assert "heavy_agent" in vt_src
    assert "run_value_trigger" in vt_src
    assert "ValueVerdict.OPPORTUNITY" in vt_src
    assert "ValueVerdict.VALUE_TRAP" in vt_src


# ── 커버 항목 2: PIT 강제 실재 ──────────────────────────────────────

def test_golden_rule_pit_enforcement():
    """§5.7-A: is_pit_clean·visible_at·RESTATED 거부."""
    contracts_src = (STOCK_DIR / "contracts.py").read_text(encoding="utf-8")
    adapter_src = (STOCK_DIR / "data" / "fundamentals_adapter.py").read_text(encoding="utf-8")
    assert "is_pit_clean" in contracts_src
    assert "visible_at" in contracts_src
    assert "RESTATED" in contracts_src
    assert "PITFundamentalsAdapter" in adapter_src
    assert "RunMode.BACKTEST" in adapter_src


# ── 커버 항목 3: admission Tier coarse/fine 실재 ────────────────────

def test_golden_rule_admission_tier():
    """§5.10: TIER1_FORBIDDEN·TIER2_DEFAULT_OFF·KRX fine."""
    admission_src = (STOCK_DIR / "admission.py").read_text(encoding="utf-8")
    assert "TIER1_FORBIDDEN" in admission_src
    assert "TIER2_DEFAULT_OFF" in admission_src
    assert "KrxStatusSnapshot" in admission_src
    assert "LLM_EXPANSION" in admission_src  # LLM 확장 차단


# ── 커버 항목 4: 모순1 degrade/resource 사유구분 실재 ────────────────

def test_golden_rule_contradiction1_reason():
    """모순1: heavy_agent_fail_reason quality/resource 구분."""
    vt_src = (STOCK_DIR / "value_trigger.py").read_text(encoding="utf-8")
    assert "heavy_agent_fail_reason" in vt_src
    assert '"quality"' in vt_src or "'quality'" in vt_src
    assert '"resource"' in vt_src or "'resource'" in vt_src


# ── 커버 항목 5: 모순2 H22 BACKTEST abstain 실재 ────────────────────

def test_golden_rule_contradiction2_h22():
    """H22: RunMode.BACKTEST → ABSTAIN, heavy-agent 미호출."""
    vt_src = (STOCK_DIR / "value_trigger.py").read_text(encoding="utf-8")
    assert "RunMode.BACKTEST" in vt_src
    assert "ABSTAIN" in vt_src
    # H22 주석 존재
    assert "H22" in vt_src or "lookahead" in vt_src or "백테스트" in vt_src


# ── 커버 항목 6: value-trap 메타라벨 실재 ───────────────────────────

def test_golden_rule_metalabel():
    """§5.8-H: ValueTrapMetaLabeler.trap_probability → value_trigger의 size_factor 억제."""
    fa_src = (STOCK_DIR / "factor_attribution.py").read_text(encoding="utf-8")
    vt_src = (STOCK_DIR / "value_trigger.py").read_text(encoding="utf-8")
    # MetaLabeler = factor_attribution.py 에 있음
    assert "ValueTrapMetaLabeler" in fa_src
    assert "trap_probability" in fa_src
    # metalabel_size_factor 억제 = value_trigger.py 에 있음
    assert "metalabel_size_factor" in vt_src
    assert "size_factor" in vt_src


# ── working tree clean ─────────────────────────────────────────────

def test_working_tree_clean():
    """tracked .py 파일 미커밋 0."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
    # tracked 변경된 .py 파일만 체크 (M = modified, D = deleted)
    tracked_py_changes = [
        l for l in lines
        if l and l[0] in ("M", "D", "A") and l.strip().endswith(".py")
    ]
    assert len(tracked_py_changes) == 0, (
        f"tracked .py 미커밋 잔존: {tracked_py_changes}"
    )


# ── 핵심 import 정합 ──────────────────────────────────────────────────

def test_import_consistency():
    """stock/ + core/stock_track import 정합."""
    result = subprocess.run(
        [sys.executable, "-c",
         "import stock.value_trigger; import core.stock_track; "
         "import stock.admission; import stock.contracts; print('OK')"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"import 실패: {result.stderr}"
    assert "OK" in result.stdout


# ── 전 Phase 통합 회귀 0 ─────────────────────────────────────────────

def test_all_phase3_tests_pass():
    """Phase 3 SO-1~6 통합 회귀 0."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_so1_stock_track.py",
         "tests/test_so2_admission.py",
         "tests/test_so3_valuation_pit.py",
         "tests/test_so4_value_trigger.py",
         "tests/test_so5_factor_attribution.py",
         "tests/test_so6_integration.py",
         "-q", "--tb=no"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"Phase 3 회귀: {result.stdout[-500:]}"
