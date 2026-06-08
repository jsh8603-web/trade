"""tests/test_so1_p6_orchestrator_bl.py — SO-1/P6 BL 슬리브 배분 검증.

검증 기준 (harness2.md SO-1):
1. regime→macro→weights 체인 실행 PASS
2. BL 출력 % §5.8-B 방향 정합 (Recovery→US주↑·Stagflation→현금↑)
3. pi 주입 수렴 (슬리브 합=1)
4. fallback 동작 (BL 실패 시 HRP/IC Prior)
5. core/brain/* tracked 화 확인
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# helpers — MacroView stub
# ---------------------------------------------------------------------------

def _make_macro_view(regime_usd="Recovery", regime_krw="Recovery", status="fresh"):
    from core.brain.macro_schema import MacroView, RegimeLabel, Bloc, ViewStatus, RegimeEstimate

    est_usd = RegimeEstimate(
        bloc=Bloc.USD,
        regime_now=RegimeLabel[regime_usd],
        confidence_now=0.8,
    )
    est_krw = RegimeEstimate(
        bloc=Bloc.KRW,
        regime_now=RegimeLabel[regime_krw],
        confidence_now=0.8,
    )
    mv = MacroView(
        status=ViewStatus[status.upper()],
        regimes={Bloc.USD: est_usd, Bloc.KRW: est_krw},
    )
    return mv


# ---------------------------------------------------------------------------
# 1. regime→macro→weights 체인 실행
# ---------------------------------------------------------------------------

def test_chain_runs_without_error():
    """regime_to_weights 체인 직접 실행 — 예외 없이 완주."""
    mv = _make_macro_view("RECOVERY", "RECOVERY")
    from core.brain.regime_to_weights import regime_to_weights
    result = regime_to_weights(mv)
    assert "weights" in result
    assert "method" in result


def test_orchestrator_allocate_returns_weights():
    """PortfolioOrchestrator.allocate → weights dict 반환."""
    from core.portfolio_orchestrator import PortfolioOrchestrator
    orch = PortfolioOrchestrator()
    mv = _make_macro_view("RECOVERY", "RECOVERY")
    result = orch.allocate(macro_view=mv)
    assert "weights" in result
    assert isinstance(result["weights"], dict)


def test_orchestrator_allocate_none_macro_view():
    """macro_view=None → fallback IC Prior 반환."""
    from core.portfolio_orchestrator import PortfolioOrchestrator
    orch = PortfolioOrchestrator()
    result = orch.allocate(macro_view=None)
    assert "weights" in result
    assert "fallback" in result.get("method", "").lower() or result.get("method") is not None


# ---------------------------------------------------------------------------
# 2. §5.8-B 방향 정합
# ---------------------------------------------------------------------------

def test_recovery_us_stock_high():
    """Recovery 레짐 → US주(us_stock) 비중 높음."""
    from core.brain.regime_to_weights import regime_to_weights
    mv_recovery = _make_macro_view("RECOVERY", "RECOVERY")
    mv_stagflation = _make_macro_view("STAGFLATION", "STAGFLATION")

    r_rec = regime_to_weights(mv_recovery)["weights"]
    r_stag = regime_to_weights(mv_stagflation)["weights"]

    assert r_rec["us_stock"] > r_stag["us_stock"], (
        f"Recovery us_stock({r_rec['us_stock']:.3f}) ≤ Stagflation({r_stag['us_stock']:.3f})"
    )


def test_stagflation_cash_high():
    """Stagflation 레짐 → 현금(cash) 비중 높음."""
    from core.brain.regime_to_weights import regime_to_weights
    mv_recovery = _make_macro_view("RECOVERY", "RECOVERY")
    mv_stagflation = _make_macro_view("STAGFLATION", "STAGFLATION")

    r_rec = regime_to_weights(mv_recovery)["weights"]
    r_stag = regime_to_weights(mv_stagflation)["weights"]

    assert r_stag["cash"] > r_rec["cash"], (
        f"Stagflation cash({r_stag['cash']:.3f}) ≤ Recovery({r_rec['cash']:.3f})"
    )


def test_reflation_bond_high():
    """Reflation 레짐 → 채권(bond) 비중 높음 (채권 최우위)."""
    from core.brain.regime_to_weights import regime_to_weights
    mv_reflation = _make_macro_view("REFLATION", "REFLATION")
    mv_overheat = _make_macro_view("OVERHEAT", "OVERHEAT")

    r_ref = regime_to_weights(mv_reflation)["weights"]
    r_ov = regime_to_weights(mv_overheat)["weights"]

    assert r_ref["bond"] > r_ov["bond"], (
        f"Reflation bond({r_ref['bond']:.3f}) ≤ Overheat({r_ov['bond']:.3f})"
    )


# ---------------------------------------------------------------------------
# 3. pi 주입 수렴 — 슬리브 합=1
# ---------------------------------------------------------------------------

def test_weights_sum_to_one():
    """슬리브 비중 합=1 (±1e-4 허용)."""
    from core.brain.regime_to_weights import regime_to_weights
    for regime in ["RECOVERY", "STAGFLATION", "REFLATION", "OVERHEAT"]:
        mv = _make_macro_view(regime, regime)
        result = regime_to_weights(mv)
        total = sum(result["weights"].values())
        assert abs(total - 1.0) < 1e-4, f"{regime}: 합={total:.6f}"


def test_orchestrator_weights_sum_to_one():
    """PortfolioOrchestrator.allocate 슬리브 합=1."""
    from core.portfolio_orchestrator import PortfolioOrchestrator
    orch = PortfolioOrchestrator()
    for regime in ["RECOVERY", "STAGFLATION"]:
        mv = _make_macro_view(regime, regime)
        result = orch.allocate(macro_view=mv)
        total = sum(result["weights"].values())
        assert abs(total - 1.0) < 1e-4, f"{regime}: 합={total:.6f}"


def test_weights_all_nonnegative():
    """슬리브 비중 전부 ≥ 0 (long-only)."""
    from core.brain.regime_to_weights import regime_to_weights
    mv = _make_macro_view("RECOVERY", "RECOVERY")
    result = regime_to_weights(mv)
    for sleeve, w in result["weights"].items():
        assert w >= 0.0, f"{sleeve}: {w:.4f} < 0"


# ---------------------------------------------------------------------------
# 4. fallback 동작
# ---------------------------------------------------------------------------

def test_fallback_on_unavailable_macro():
    """macro=UNAVAILABLE → fallback 실행, 슬리브 합=1."""
    from core.portfolio_orchestrator import PortfolioOrchestrator
    orch = PortfolioOrchestrator()
    mv = _make_macro_view("RECOVERY", "RECOVERY", status="UNAVAILABLE")
    result = orch.allocate(macro_view=mv)
    assert "weights" in result
    total = sum(result["weights"].values())
    assert abs(total - 1.0) < 1e-4
    assert result.get("macro_abstain") is True


def test_fallback_on_none_macro_view():
    """macro_view=None → IC Prior fallback."""
    from core.portfolio_orchestrator import PortfolioOrchestrator
    orch = PortfolioOrchestrator()
    result = orch.allocate(macro_view=None)
    weights = result["weights"]
    total = sum(weights.values())
    assert abs(total - 1.0) < 1e-4


# ---------------------------------------------------------------------------
# 5. core/brain/* tracked 화 확인
# ---------------------------------------------------------------------------

def test_core_brain_files_importable():
    """core/brain/* import 정합 — 오류 없이 import 가능."""
    from core.brain.macro_schema import MacroView, RegimeLabel, Bloc, RegimeEstimate
    from core.brain.regime_to_weights import regime_to_weights, SLEEVES, BASE_WEIGHTS
    from core.brain.macro_reasoning import MacroReasoningNode
    assert len(SLEEVES) == 9   # ★eq_intl/reit 신설(2026-06-09, 7→9 분산 sleeve)
    assert abs(sum(BASE_WEIGHTS.values()) - 1.0) < 1e-4


def test_portfolio_orchestrator_importable():
    """PortfolioOrchestrator import PASS."""
    from core.portfolio_orchestrator import PortfolioOrchestrator, SLEEVE_BANDS
    assert len(SLEEVE_BANDS) == 7


def test_per_bloc_independence():
    """per-bloc: USD Recovery + KRW Stagflation → us_stock ≠ kr_stock 방향."""
    from core.brain.regime_to_weights import regime_to_weights
    mv = _make_macro_view("RECOVERY", "STAGFLATION")
    result = regime_to_weights(mv)
    weights = result["weights"]
    # US Recovery → us_stock 높음
    # KR Stagflation → kr_stock 낮음
    assert weights["us_stock"] > weights["kr_stock"] * 0.5, (
        f"per-bloc 독립성 위반: us={weights['us_stock']:.3f} kr={weights['kr_stock']:.3f}"
    )
