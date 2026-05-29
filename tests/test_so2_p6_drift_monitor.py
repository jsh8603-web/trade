"""tests/test_so2_p6_drift_monitor.py — SO-2/P6 Drift Monitor 검증.

검증 기준 (harness2.md SO-2):
1. 슬리브 밴드 이탈 주입 → 감지 + near_miss_veto 기록 + 리밸런싱 트리거
2. 밴드 내 = 무동작
"""

from __future__ import annotations

import pytest

from core.portfolio_orchestrator import (
    PortfolioOrchestrator,
    NearMissVeto,
    SLEEVE_BANDS,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _normal_weights() -> dict:
    """SLEEVE_BANDS 내 정상 비중."""
    return {
        "us_stock": 0.25, "kr_stock": 0.15, "commodity": 0.08,
        "gold": 0.08, "bond": 0.25, "cash": 0.09, "coin": 0.10,
    }


# ---------------------------------------------------------------------------
# 1. 밴드 이탈 → 감지 + near_miss_veto + 리밸런싱 트리거
# ---------------------------------------------------------------------------

def test_drift_detects_upper_breach():
    """us_stock 상한 초과 → Drift Monitor 감지."""
    orch = PortfolioOrchestrator()
    weights = _normal_weights()
    weights["us_stock"] = 0.60  # 상한 0.45 초과
    vetoes = orch.monitor_band_drift(weights)
    assert any(v.sleeve == "us_stock" for v in vetoes)


def test_drift_detects_lower_breach():
    """bond 하한 미달 → Drift Monitor 감지."""
    orch = PortfolioOrchestrator()
    weights = _normal_weights()
    weights["bond"] = 0.02  # 하한 0.10 미달
    vetoes = orch.monitor_band_drift(weights)
    assert any(v.sleeve == "bond" for v in vetoes)


def test_drift_creates_near_miss_veto():
    """이탈 시 NearMissVeto 인스턴스 생성."""
    orch = PortfolioOrchestrator()
    weights = _normal_weights()
    weights["cash"] = 0.50  # 상한 0.25 초과
    vetoes = orch.monitor_band_drift(weights)
    cash_vetoes = [v for v in vetoes if v.sleeve == "cash"]
    assert len(cash_vetoes) == 1
    veto = cash_vetoes[0]
    assert isinstance(veto, NearMissVeto)
    assert veto.action_taken == "rebalance_trigger"
    assert veto.current_weight == pytest.approx(0.50)


def test_drift_veto_log_accumulated():
    """여러 사이클 veto 누적."""
    orch = PortfolioOrchestrator()
    w1 = _normal_weights()
    w1["us_stock"] = 0.60
    orch.monitor_band_drift(w1)

    w2 = _normal_weights()
    w2["bond"] = 0.02
    orch.monitor_band_drift(w2)

    assert len(orch.veto_log) == 2


def test_drift_multiple_breaches():
    """여러 슬리브 동시 이탈 → 모두 감지."""
    orch = PortfolioOrchestrator()
    weights = {
        "us_stock": 0.60,   # 상한 초과
        "kr_stock": 0.15,
        "commodity": 0.08,
        "gold": 0.08,
        "bond": 0.02,       # 하한 미달
        "cash": 0.05,
        "coin": 0.02,
    }
    vetoes = orch.monitor_band_drift(weights)
    sleeves_flagged = {v.sleeve for v in vetoes}
    assert "us_stock" in sleeves_flagged
    assert "bond" in sleeves_flagged


# ---------------------------------------------------------------------------
# 2. 밴드 내 = 무동작
# ---------------------------------------------------------------------------

def test_drift_no_action_within_band():
    """정상 비중 → 빈 veto 목록 반환."""
    orch = PortfolioOrchestrator()
    weights = _normal_weights()
    vetoes = orch.monitor_band_drift(weights)
    assert vetoes == []


def test_drift_boundary_exact():
    """밴드 경계값 = 이탈 없음."""
    orch = PortfolioOrchestrator()
    # us_stock 하한 = 0.10, 상한 = 0.45
    weights = _normal_weights()
    weights["us_stock"] = 0.10   # 정확히 하한
    vetoes = orch.monitor_band_drift(weights)
    us_vetoes = [v for v in vetoes if v.sleeve == "us_stock"]
    assert len(us_vetoes) == 0


# ---------------------------------------------------------------------------
# 3. SLEEVE_BANDS 정합
# ---------------------------------------------------------------------------

def test_sleeve_bands_all_sleeves():
    """SLEEVE_BANDS 에 7개 슬리브 모두 존재."""
    expected = {"us_stock", "kr_stock", "commodity", "gold", "bond", "cash", "coin"}
    assert set(SLEEVE_BANDS.keys()) == expected


def test_sleeve_bands_valid_ranges():
    """모든 밴드 min < max."""
    for sleeve, (lo, hi) in SLEEVE_BANDS.items():
        assert lo < hi, f"{sleeve}: min({lo}) >= max({hi})"
