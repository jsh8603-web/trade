"""tests/assume/test_active_loop.py — S4 능동 애널리스트 루프(LLM 소환 발권 shadow)."""
import json

import numpy as np
import pytest

from core.assume.active_loop import ActiveAnalystLoop
from core.assume.fhc import MediatorState
from core.brain.macro_schema import Bloc, MacroView, RegimeEstimate, RegimeLabel, ViewStatus


def _view(label, conf):
    est = RegimeEstimate(bloc=Bloc.USD, regime_now=label, confidence_now=conf)
    return MacroView(regimes={Bloc.USD: est}, status=ViewStatus.FRESH, as_of_ts=0.0)


class _FakeLLM:
    def __init__(self, claim, approve=True):
        self._claim, self._approve = claim, approve

    def complete(self, system, user, json_mode=True):
        if "audit a hypothesis" in system:
            return json.dumps({"approve": self._approve, "reason": "ok" if self._approve else "camouflage"})
        return json.dumps(self._claim)


GOOD = {
    "statement": "Overheat 원자재 우위", "direction": "long_tilt",
    "mediator_ref": "regime:USD:Overheat", "outcome_metric": "ts_rank_IC",
    "falsification_metric": "원자재 3M fwd IC < 0", "counter_thesis": "달러 강세 상쇄",
}


def test_llm_none_abstains():
    assert ActiveAnalystLoop(llm=None).run_cycle(_view(RegimeLabel.OVERHEAT, 0.2)) is None


def test_high_confidence_no_summon():
    loop = ActiveAnalystLoop(llm=_FakeLLM(GOOD))
    assert loop.should_summon(_view(RegimeLabel.OVERHEAT, 0.9)).summon is False


def test_low_conf_novel_mints_probationary():
    loop = ActiveAnalystLoop(llm=_FakeLLM(GOOD))
    pc = loop.run_cycle(_view(RegimeLabel.OVERHEAT, 0.3), numeric_revision=0.3)
    assert pc is not None
    assert pc.card.kind == "probationary" and pc.card.bonus_cap == 0.0
    assert pc.card.falsification_metric and pc.minted_shadow
    assert len(loop.shadow_sink) == 1


def test_missing_falsification_rejected():
    bad = dict(GOOD, falsification_metric="")
    loop = ActiveAnalystLoop(llm=_FakeLLM(bad))
    assert loop.run_cycle(_view(RegimeLabel.OVERHEAT, 0.3), numeric_revision=0.3) is None


def test_llm_audit_reject():
    loop = ActiveAnalystLoop(llm=_FakeLLM(GOOD, approve=False))
    assert loop.run_cycle(_view(RegimeLabel.OVERHEAT, 0.3), numeric_revision=0.3) is None


def test_mediator_unknown_triggers_with_external_sink():
    sink = []
    loop = ActiveAnalystLoop(llm=_FakeLLM(GOOD), write_back=sink.append)
    pc = loop.run_cycle(_view(RegimeLabel.RECOVERY, 0.9),
                        mediator_state=MediatorState.UNKNOWN, numeric_revision=0.3)
    assert pc is not None and len(sink) == 1


def test_orthogonality_camouflage_blocks_mint():
    rng = np.random.RandomState(0)
    F = rng.randn(240, 3) * 0.01
    r_camo = F @ np.array([1.0, -0.5, 0.7]) + rng.randn(240) * 0.002
    loop = ActiveAnalystLoop(llm=_FakeLLM(GOOD))
    pc = loop.run_cycle(_view(RegimeLabel.OVERHEAT, 0.3), numeric_revision=0.3,
                        spanning_inputs=(r_camo, F))
    assert pc is None


def test_summon_gate_rate_cap_blocks():
    from core.assume.info_delta_gate import RateCapState
    rc = RateCapState(cap_per_slot=1, slot_fn=lambda t: 0)
    loop = ActiveAnalystLoop(llm=_FakeLLM(GOOD), rate_cap=rc)
    v = _view(RegimeLabel.OVERHEAT, 0.3)
    first = loop.run_cycle(v, numeric_revision=0.3)
    second = loop.run_cycle(v, numeric_revision=0.3)   # rate-cap 소진
    assert first is not None and second is None
