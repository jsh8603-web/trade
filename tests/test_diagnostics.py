"""tests/test_diagnostics.py — P2-3 측정 스크립트 회귀.

backtest/diagnostics 의 4층 지표 / per-asset attribution(self-ref base 금지) /
3차 게이트(NW HAC · block-bootstrap · walk-forward) 검증.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.diagnostics import (
    hit_rate,
    nw_hac_tstat,
    block_bootstrap_ci,
    confirm_gate,
    per_asset_attribution,
    four_layer_metrics,
)


def test_hit_rate():
    assert hit_rate([1, -1, 1], [1, -1, 1]) == 1.0
    assert hit_rate([1, 1], [1, -1]) == 0.5
    assert hit_rate([], []) == 0.0


def test_nw_hac_tstat_autocorr_finite():
    rng = np.random.default_rng(42)
    drift = 0.001 + 0.01 * rng.standard_normal(300)
    t, n, lags = nw_hac_tstat(drift)
    assert n == 300
    assert lags >= 1
    assert t > 0
    # 짧은 시계열 → 0
    assert nw_hac_tstat([0.1, 0.2]) == (0.0, 2, 0)


def test_block_bootstrap_ci_contains_mean():
    rng = np.random.default_rng(1)
    x = 0.002 + 0.01 * rng.standard_normal(200)
    lo, mu, hi = block_bootstrap_ci(x, n_boot=500, seed=1)
    assert lo <= mu <= hi


def test_confirm_gate_strong_drift_confirmed():
    rng = np.random.default_rng(7)
    g = confirm_gate(
        0.005 + 0.005 * rng.standard_normal(300),
        oos_excess=0.005 + 0.005 * rng.standard_normal(60),
    )
    assert g.confirmed is True
    assert g.walk_forward_consistent is True
    assert abs(g.nw_t) > 1.96
    assert (g.boot_lo > 0) or (g.boot_hi < 0)


def test_confirm_gate_noise_not_confirmed():
    """단정 금지 — 평균0 노이즈는 미확정."""
    rng = np.random.default_rng(8)
    g = confirm_gate(0.0 + 0.01 * rng.standard_normal(300))
    assert g.confirmed is False
    assert g.walk_forward_consistent is None
    assert g.note.startswith("walk-forward 미평가")


def test_per_asset_attribution_external_base_suspect():
    """★self-ref base 금지: base=외부 passive. 전략<passive → suspect."""
    strat = {"BTC": [0.01, -0.02, 0.01], "ETH": [0.02, 0.01, 0.0]}
    passive = {"BTC": [0.03, 0.01, 0.02], "ETH": [0.0, 0.0, 0.0]}
    rows = per_asset_attribution(strat, passive)
    btc = next(r for r in rows if r.asset == "BTC")
    eth = next(r for r in rows if r.asset == "ETH")
    assert btc.excess < 0 and btc.suspect is True
    assert eth.excess > 0 and eth.suspect is False


def test_per_asset_sum_excess_not_zero_with_external_base():
    """외부 base 면 ∑excess ≠ 0 (self-ref 거울 아님 = 독립 발견 가능)."""
    strat = {"A": [0.01, 0.01], "B": [0.02, -0.01]}
    passive = {"A": [0.005, 0.005], "B": [0.0, 0.0]}  # 외부 buy&hold
    rows = per_asset_attribution(strat, passive)
    total = sum(r.excess for r in rows)
    assert abs(total) > 1e-9  # ∑excess≡0 거울 아님


def test_four_layer_metrics_all_four():
    rng = np.random.default_rng(3)
    drift = 0.001 + 0.01 * rng.standard_normal(300)
    eq = pd.Series(np.cumprod(1 + drift) * 1_000_000)
    bench = pd.Series(np.cumprod(1 + 0.0005 + 0.01 * rng.standard_normal(300)) * 1_000_000)
    fm = four_layer_metrics(eq, bench, scores=list(drift), fwd_returns=list(drift))
    # (a) 연결성 (b) 신호품질 (c) 리스크조정 (d) 초과수익 4층 다 존재
    assert "error_count" in fm
    assert fm["rank_ic"] is not None and fm["hit_rate"] is not None
    assert "sharpe" in fm and "sortino" in fm and "max_drawdown" in fm
    assert "excess_cagr" in fm


def test_four_layer_metrics_no_signal_none():
    """scores 미제공 시 신호품질 None (scale-invariant 항만 생략)."""
    eq = pd.Series([1_000_000.0, 1_010_000.0, 1_005_000.0, 1_020_000.0])
    fm = four_layer_metrics(eq)
    assert fm["rank_ic"] is None and fm["hit_rate"] is None
    assert "sharpe" in fm
