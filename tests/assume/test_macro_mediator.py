"""tests/assume/test_macro_mediator.py — S2 macro mediator 구독 어댑터.

filtered-only belief 구독 · fail-closed UNKNOWN · entropy 게이트 · eval_mediator 연결.
INV-11: 어댑터는 additive(fhc/regime_belief_adapter 무수정) → 기존 회귀는 별 테스트가 보장.
"""
import time

import pytest

from core.assume.fhc import MediatorSpec, MediatorState, MediatorTest
from core.assume.macro_mediator import (
    belief_entropy,
    eval_macro_mediator,
    macro_posterior_holds,
)
from core.brain.macro_schema import (
    Bloc,
    MacroView,
    RegimeEstimate,
    RegimeLabel,
    ViewStatus,
)


def _view(label, conf, *, status=ViewStatus.FRESH, as_of=0.0, forecast=None, bloc=Bloc.USD):
    est = RegimeEstimate(
        bloc=bloc,
        regime_now=label,
        confidence_now=conf,
        regime_forecast=forecast,
    )
    return MacroView(regimes={bloc: est}, status=status, as_of_ts=as_of)


_SP = MediatorSpec(
    "regime:USD:Overheat",
    test=MediatorTest.STATE_SPACE_POSTERIOR,
    op=">=",
    threshold=0.5,
)


def test_target_regime_high_conf_holds():
    assert macro_posterior_holds(_view(RegimeLabel.OVERHEAT, 0.9), _SP) is True


def test_target_regime_low_conf_fails():
    # 평탄 → mass < 0.5
    assert macro_posterior_holds(_view(RegimeLabel.OVERHEAT, 0.1), _SP) is False


def test_other_regime_fails():
    assert macro_posterior_holds(_view(RegimeLabel.RECOVERY, 0.9), _SP) is False


def test_unavailable_is_unknown():
    assert macro_posterior_holds(MacroView.unavailable(), _SP) is None


def test_none_view_is_unknown():
    assert macro_posterior_holds(None, _SP) is None


def test_bad_target_label_is_unknown():
    bad = MediatorSpec("regime:USD:Nonexistent", test=MediatorTest.STATE_SPACE_POSTERIOR)
    assert macro_posterior_holds(_view(RegimeLabel.OVERHEAT, 0.9), bad) is None


def test_stale_too_old_is_unknown():
    old = _view(RegimeLabel.OVERHEAT, 0.9, status=ViewStatus.STALE, as_of=time.time() - 10_000)
    assert macro_posterior_holds(old, _SP, max_stale_seconds=3600) is None


def test_fresh_within_window_holds():
    fresh = _view(RegimeLabel.OVERHEAT, 0.9, as_of=time.time())
    assert macro_posterior_holds(fresh, _SP, max_stale_seconds=3600) is True


def test_entropy_gate_blocks_flat_distribution():
    sp_lo = MediatorSpec(
        "regime:USD:Overheat",
        test=MediatorTest.STATE_SPACE_POSTERIOR,
        op=">=",
        threshold=0.3,
    )
    v_mod = _view(RegimeLabel.OVERHEAT, 0.35)
    assert macro_posterior_holds(v_mod, sp_lo) is True            # gate off → 통과
    assert macro_posterior_holds(v_mod, sp_lo, max_entropy=0.85) is False  # 평탄 → 보류


def test_filtered_only_ignores_forecast():
    # regime_now=Recovery(target 아님)인데 forecast=Overheat(target) → forecast 무시 = filtered-only
    v = _view(RegimeLabel.RECOVERY, 0.9, forecast=RegimeLabel.OVERHEAT)
    assert macro_posterior_holds(v, _SP) is False


def test_krw_bloc_routing():
    sp_krw = MediatorSpec(
        "regime:KRW:Stagflation",
        test=MediatorTest.STATE_SPACE_POSTERIOR,
        op=">=",
        threshold=0.5,
    )
    v = _view(RegimeLabel.STAGFLATION, 0.9, bloc=Bloc.KRW)
    assert macro_posterior_holds(v, sp_krw) is True


def test_eval_macro_mediator_states():
    assert eval_macro_mediator(_view(RegimeLabel.OVERHEAT, 0.9), _SP) == MediatorState.HOLDS
    assert eval_macro_mediator(_view(RegimeLabel.RECOVERY, 0.9), _SP) == MediatorState.FAILS
    assert eval_macro_mediator(MacroView.unavailable(), _SP) == MediatorState.UNKNOWN


def test_eval_macro_mediator_deterministic_delegates():
    det = MediatorSpec("x", test=MediatorTest.DETERMINISTIC_THRESHOLD)
    # state-space 아님 → observable 경로 위임(value 없음 → UNKNOWN)
    assert eval_macro_mediator(None, det) == MediatorState.UNKNOWN


def test_belief_entropy_bounds():
    flat = {lab: 0.25 for lab in ("Reflation", "Recovery", "Overheat", "Stagflation")}
    assert belief_entropy(flat) == pytest.approx(1.0, abs=1e-9)
    peaked = {"Reflation": 0.0001, "Recovery": 0.0001, "Overheat": 0.9997, "Stagflation": 0.0001}
    assert belief_entropy(peaked) < 0.1
