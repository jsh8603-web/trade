"""SO-2 테스트: 상관캡(corr>0.7 차단) + 상관 multiplier(corr>=0.8 → 0.7x).

검증기준:
- corr 0.7 초과 페어 → 차단(rejected) PASS
- corr 0.8 이상 → adjusted_size 0.7x(reduced) PASS
- corr < 0.7 → 영향 없음(approved) PASS
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.risk_gate import (
    RiskGate,
    VerdictType,
    calculate_correlation_multiplier,
)


# ── calculate_correlation_multiplier 단위 ────────────────────────────

def test_multiplier_very_high():
    """>= 0.80 → 0.70x."""
    assert calculate_correlation_multiplier(0.80) == 0.70
    assert calculate_correlation_multiplier(0.95) == 0.70


def test_multiplier_high():
    """0.60~0.80 → 0.85x."""
    assert calculate_correlation_multiplier(0.60) == 0.85
    assert calculate_correlation_multiplier(0.75) == 0.85


def test_multiplier_moderate():
    """0.40~0.60 → 1.00x."""
    assert calculate_correlation_multiplier(0.50) == 1.00
    assert calculate_correlation_multiplier(0.40) == 1.00


def test_multiplier_low():
    """0.20~0.40 → 1.05x."""
    assert calculate_correlation_multiplier(0.30) == 1.05


def test_multiplier_very_low():
    """< 0.20 → 1.10x."""
    assert calculate_correlation_multiplier(0.10) == 1.10
    assert calculate_correlation_multiplier(0.0) == 1.10


# ── 상관캡 corr > 0.7 → 차단(rejected) ──────────────────────────────

def test_corr_cap_rejects_above_threshold():
    """corr > 0.7 → rejected(corr_cap)."""
    gate = RiskGate(corr_cap=0.7)
    v = gate.check(
        cycle_id="c_corr",
        action="buy",
        proposed_size=5000,
        avg_correlation=0.75,  # 0.7 초과
        nav=100000,
        daily_loss_pct=-0.01,
    )
    assert v.verdict == VerdictType.REJECTED
    assert "corr_cap" in v.triggered_rules


def test_corr_cap_rejects_well_above():
    """corr = 0.9 → 확실히 차단."""
    gate = RiskGate(corr_cap=0.7)
    v = gate.check(
        cycle_id="c_high",
        action="buy",
        proposed_size=5000,
        avg_correlation=0.90,
        nav=100000,
        daily_loss_pct=-0.01,
    )
    assert v.verdict == VerdictType.REJECTED
    assert "corr_cap" in v.triggered_rules


def test_corr_cap_at_boundary_rejected():
    """corr 정확히 0.7 초과(0.701) → 차단."""
    gate = RiskGate(corr_cap=0.7)
    v = gate.check(
        cycle_id="c_boundary",
        action="buy",
        proposed_size=1000,
        avg_correlation=0.701,
        nav=100000,
        daily_loss_pct=-0.01,
    )
    assert v.verdict == VerdictType.REJECTED


def test_corr_cap_at_exact_threshold_passes():
    """corr = 0.7 정확히 → 통과(> 조건이므로 0.7 이하 허용)."""
    gate = RiskGate(corr_cap=0.7, min_holding_days=0)
    v = gate.check(
        cycle_id="c_exact",
        action="buy",
        proposed_size=1000,
        avg_correlation=0.70,
        nav=100000,
        daily_loss_pct=-0.01,
    )
    assert "corr_cap" not in v.triggered_rules


# ── corr >= 0.8 → size 0.7x(reduced) ────────────────────────────────

def test_corr_high_reduces_size():
    """corr = 0.85 (≤ 0.7 cap 이하, multiplier=0.7x) → reduced."""
    gate = RiskGate(corr_cap=0.7, min_holding_days=0)
    v = gate.check(
        cycle_id="c_reduce",
        action="buy",
        proposed_size=10000,
        avg_correlation=0.65,  # cap 이하지만 multiplier 0.85x 적용
        nav=100000,
        daily_loss_pct=-0.01,
    )
    assert v.verdict == VerdictType.REDUCED
    assert "corr_multiplier" in v.triggered_rules
    assert v.adjusted_size is not None
    assert abs(v.adjusted_size - 10000 * 0.85) < 1.0


def test_corr_0_8_size_0_7x():
    """corr = 0.8 → multiplier = 0.7x. (cap=0.7이므로 0.8은 차단. cap 올려서 확인)."""
    gate = RiskGate(corr_cap=0.85, min_holding_days=0)  # cap을 0.85로 올려 0.8 통과
    v = gate.check(
        cycle_id="c_0_8",
        action="buy",
        proposed_size=10000,
        avg_correlation=0.82,  # cap(0.85) 이하, multiplier=0.70x
        nav=100000,
        daily_loss_pct=-0.01,
    )
    assert v.verdict == VerdictType.REDUCED
    assert "corr_multiplier" in v.triggered_rules
    assert abs(v.adjusted_size - 10000 * 0.70) < 1.0


# ── corr < 0.7(낮은 상관) → 영향 없음 ──────────────────────────────

def test_low_corr_no_effect():
    """corr = 0.1 → multiplier=1.10x (>1 → 축소 없음, approved)."""
    gate = RiskGate(corr_cap=0.7, min_holding_days=0)
    v = gate.check(
        cycle_id="c_low",
        action="buy",
        proposed_size=1000,
        avg_correlation=0.10,
        nav=100000,
        daily_loss_pct=-0.01,
    )
    assert "corr_cap" not in v.triggered_rules
    assert "corr_multiplier" not in v.triggered_rules
    assert v.verdict == VerdictType.APPROVED


def test_zero_corr_approved():
    """avg_correlation = 0.0 (기본값) → 영향 없음."""
    gate = RiskGate(min_holding_days=0)
    v = gate.check(
        cycle_id="c_zero",
        action="buy",
        proposed_size=1000,
        nav=100000,
        daily_loss_pct=-0.01,
    )
    assert "corr_cap" not in v.triggered_rules
    assert "corr_multiplier" not in v.triggered_rules


def test_corr_cap_sell_not_applied():
    """상관캡은 매도에는 적용 안 함."""
    gate = RiskGate(corr_cap=0.7, min_holding_days=0)
    v = gate.check(
        cycle_id="c_sell_corr",
        action="sell",
        proposed_size=5000,
        avg_correlation=0.95,  # 매도이므로 cap 무시
        holding_days=5,
        nav=100000,
        daily_loss_pct=-0.01,
    )
    assert "corr_cap" not in v.triggered_rules


# ── near_miss_veto 기록 확인 ─────────────────────────────────────────

def test_corr_cap_veto_written(tmp_path, monkeypatch):
    """corr_cap 차단 시 near_miss_veto.jsonl 기록."""
    import core.risk_gate as rg
    import json
    monkeypatch.setattr(rg, "_LOG_DIR", tmp_path)

    gate = RiskGate(corr_cap=0.7)
    gate.check(
        cycle_id="veto_corr",
        action="buy",
        proposed_size=5000,
        avg_correlation=0.80,
        nav=100000,
        daily_loss_pct=-0.01,
    )
    veto_file = tmp_path / "near_miss_veto.jsonl"
    assert veto_file.exists()
    entry = json.loads(veto_file.read_text(encoding="utf-8").strip())
    assert entry["event"] == "near_miss_veto"
    assert entry["rule"] == "corr_cap"
