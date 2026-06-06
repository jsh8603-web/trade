"""tests/assume/test_spanning_gate.py — S4 직교성 발권 게이트(스패닝 회귀 C9/Q3)."""
import numpy as np
import pytest

from core.assume.spanning_gate import (
    conditional_alpha,
    mint_gate,
    residual_forward_ic,
    spanning_regression,
)


@pytest.fixture
def rng():
    return np.random.RandomState(0)


def test_pure_factor_exposure_is_camouflage(rng):
    F = rng.randn(240, 3) * 0.01
    r = F @ np.array([1.2, -0.5, 0.8]) + rng.randn(240) * 0.002
    v = mint_gate(r, F)
    assert v.verdict == "camouflage" and not v.can_mint


def test_orthogonal_alpha_is_mint(rng):
    F = rng.randn(240, 3) * 0.01
    r = 0.004 + F @ np.array([0.3, 0.2, -0.1]) + rng.randn(240) * 0.002
    v = mint_gate(r, F)
    assert v.verdict == "mint" and v.can_mint and v.alpha > 0


def test_small_sample_is_insufficient(rng):
    F = rng.randn(15, 3) * 0.01
    r = 0.004 + rng.randn(15) * 0.002
    assert mint_gate(r, F).verdict == "insufficient"


def test_residual_forward_ic_gate_blocks_noise(rng):
    F = rng.randn(240, 3) * 0.01
    r = 0.004 + F @ np.array([0.3, 0.2, -0.1]) + rng.randn(240) * 0.002
    # 잔차와 구조적으로 직교한 결정론 패턴(sin) → forward IC 비유의 → 발권 보류
    fwd = np.sin(np.arange(240) * 0.7)
    v = mint_gate(r, F, fwd_returns=fwd)
    assert v.verdict == "camouflage" and "forward IC" in v.reason


def test_residual_predicts_forward_is_mint(rng):
    F = rng.randn(240, 3) * 0.01
    r = 0.004 + F @ np.array([0.3, 0.2, -0.1]) + rng.randn(240) * 0.002
    res = spanning_regression(r, F)
    fwd = np.array(res.resid) * 2.0 + rng.randn(240) * 0.001
    assert mint_gate(r, F, fwd_returns=fwd).verdict == "mint"


def test_hac_lags_applied(rng):
    F = rng.randn(240, 3) * 0.01
    res = spanning_regression(0.003 + rng.randn(240) * 0.002, F)
    assert res.hac_lags >= 1 and res.n == 240


def test_conditional_alpha_splits_regime(rng):
    F = rng.randn(240, 3) * 0.01
    regime = np.array([i % 2 == 0 for i in range(240)])
    r = np.where(regime, 0.005, 0.0) + F @ np.array([0.2, 0.1, 0.0]) + rng.randn(240) * 0.002
    c = conditional_alpha(r, F, regime)
    assert c["in_regime"]["n"] > 0 and c["out_regime"]["n"] > 0


def test_residual_forward_ic_degenerate():
    assert residual_forward_ic([1.0, 1.0, 1.0], [0.1, 0.2, 0.3])["ok"] is False
