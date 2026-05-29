"""tests/structure/test_assumption_stats.py — 가정 검증통계 엔진 잠금 (T2 산출).

detectors / online_fdr / assumption_stats 의 핵심 보장을 회귀로부터 보호.
"""

from __future__ import annotations

import numpy as np
import pytest

from core.structure import detectors as dt
from core.structure import online_fdr as ofdr
from core.structure import assumption_stats as ast


# --- detectors --------------------------------------------------------------

def test_cusum_detects_mean_shift_not_noise():
    rng = np.random.default_rng(7)
    c = dt.Cusum(target=0.0, sd=1.0, k_sigma=1.0, h_sigma=5.0)
    fired = [c.update(float(x)) for x in np.concatenate([rng.normal(0, 1, 60), rng.normal(3, 1, 40)])]
    first = next((i for i, f in enumerate(fired) if f), None)
    assert first is not None and first >= 60

def test_sprt_accepts_h1_under_alternative():
    rng = np.random.default_rng(7)
    s = dt.Sprt(mu0=0.0, mu1=2.0, sd=1.0)
    dec = None
    for x in rng.normal(2, 1, 100):
        r = s.update(float(x))
        if r.decision != "continue":
            dec = r.decision; break
    assert dec == "accept_H1"

def test_bocpd_run_length_collapses_at_changepoint():
    rng = np.random.default_rng(7)
    b = dt.Bocpd(hazard_lambda=50.0)
    rls = []
    for x in np.concatenate([rng.normal(0, 1, 60), rng.normal(4, 1, 60)]):
        b.update(float(x)); rls.append(b.map_run_length)
    assert max(rls[55:60]) >= 40 and min(rls[60:70]) <= 5

def test_prequential_kink_on_degradation():
    rng = np.random.default_rng(7)
    pred = np.zeros(60)
    out = np.concatenate([rng.normal(0, 0.3, 30), rng.normal(3, 0.3, 30)])
    assert dt.prequential_loss(pred, out, recent_window=10).kink_alert


# --- online FDR -------------------------------------------------------------

def test_lord_controls_fdr_under_null():
    rng = np.random.default_rng(3)
    lord = ofdr.LordPlusPlus(alpha=0.05)
    n = sum(lord.test(float(p)).reject for p in rng.uniform(0, 1, 500))
    assert n <= 5  # FDR 제어

def test_lord_rejects_strong_signal():
    lord = ofdr.LordPlusPlus(alpha=0.05)
    n = sum(lord.test(1e-6).reject for _ in range(20))
    assert n >= 10

def test_alpha_investing_blocks_revival_abuse():
    """죽은 가정 50번 재검정 + 막판 운좋은 p → wealth 고갈로 차단 (claude C-부활)."""
    rng = np.random.default_rng(3)
    ai = ofdr.AlphaInvesting(alpha=0.05)
    pvals = list(rng.uniform(0.2, 1.0, 49)) + [0.04]
    for p in pvals:
        ai.test(float(p))
    assert ai.n_rejections == 0


# --- assumption_stats: kind dispatch + regime-conditional -------------------

def test_parametric_regime_conditional_separation():
    """★ claude A-1: pooled 금지. regime0 성립·regime1 깸이 레짐별로 갈려야."""
    rng = np.random.default_rng(11)
    n = 80
    reg = np.array([0] * n + [1] * n)
    realized = np.concatenate([rng.normal(15.0, 1.0, n), rng.normal(19.0, 1.0, n)])
    rep = ast.validate_parametric("a", 15.0, realized, reg, current_regime=0, sd=1.0)
    assert rep.kind == "parametric"
    assert rep.by_regime[0].holds and not rep.by_regime[1].holds
    assert rep.holds_now is True  # 현재 regime(0) 만 거래 판정

def test_structural_holds_when_mechanism_works():
    rng = np.random.default_rng(11)
    pred = rng.normal(0, 0.3, 60)
    out = pred + rng.normal(0, 0.2, 60)
    rep = ast.validate_structural("b", pred, out, np.zeros(60, int), 0)
    assert rep.kind == "structural" and rep.by_regime[0].holds


# --- hysteresis AND-gate ----------------------------------------------------

def test_and_gate_requires_all_conditions():
    g = ast.hysteresis_and_gate(fdr_significant=True, effect_size=0.7, dwell_ok=True,
                                k_window_persist=2, same_regime=True)
    assert g.promote
    g2 = ast.hysteresis_and_gate(fdr_significant=True, effect_size=0.3, dwell_ok=True,
                                 k_window_persist=2, same_regime=True)
    assert not g2.promote and not g2.conditions["effect_material"]

def test_and_gate_base_layer_never_auto_promotes():
    """★ claude C-meta: base-layer 가정(regime 모델)은 자동변경 금지."""
    g = ast.hysteresis_and_gate(fdr_significant=True, effect_size=2.0, dwell_ok=True,
                                k_window_persist=5, same_regime=True, is_base_layer=True)
    assert not g.promote and "base-layer" in g.reason


# --- 신뢰도 → band → 사이징 -------------------------------------------------

def test_confidence_band_widens_and_sizing_abstains():
    lo, hi = ast.confidence_to_band(15.0, confidence=0.5, base_halfwidth=1.0)
    assert (hi - lo) > 2.0                       # 신뢰도 낮음 → 넓은 band
    assert ast.band_to_size_multiplier(1.0, 1.0) == 1.0
    assert ast.band_to_size_multiplier(3.5, 1.0) == 0.0   # 너무 넓음 → abstain
