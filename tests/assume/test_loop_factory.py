"""tests/assume/test_loop_factory.py — S4 발권 실연결 팩토리(LLM 어댑터)."""
import json

from core.assume.active_loop import ActiveAnalystLoop
from core.assume.loop_factory import (
    GenerateToComplete,
    build_active_loop,
    ollama_health,
)
from core.brain.macro_schema import Bloc, MacroView, RegimeEstimate, RegimeLabel, ViewStatus


def _view(label, conf):
    est = RegimeEstimate(bloc=Bloc.USD, regime_now=label, confidence_now=conf)
    return MacroView(regimes={Bloc.USD: est}, status=ViewStatus.FRESH, as_of_ts=0.0)


class _Gen:
    """brain.llm_provider 스타일 generate(prompt) provider."""
    def __init__(self, payload):
        self._payload = payload

    def generate(self, prompt, **kw):
        if "audit" in prompt.lower():
            return '{"approve": true, "reason": "ok"}'
        return self._payload


def test_use_local_llm_false_is_byte_identical():
    loop = build_active_loop(use_local_llm=False)
    assert loop.llm is None
    assert loop.run_cycle(_view(RegimeLabel.OVERHEAT, 0.2)) is None


def test_generate_to_complete_json_extraction():
    g = _Gen('```json\n{"a":1,"b":"x"}\n```')
    out = GenerateToComplete(g).complete("sys", "user", json_mode=True)
    assert json.loads(out)["a"] == 1


def test_generate_to_complete_prose_wrapped_json():
    g = _Gen('Here is the card: {"direction":"de_risk"} hope it helps')
    out = GenerateToComplete(g).complete("sys", "user", json_mode=True)
    assert json.loads(out)["direction"] == "de_risk"


def test_adapter_injected_loop_mints():
    claim = ('{"statement":"Overheat 원자재 우위","direction":"long_tilt",'
             '"mediator_ref":"regime:USD:Overheat","outcome_metric":"ts_rank_IC",'
             '"falsification_metric":"원자재 3M fwd IC < 0","counter_thesis":"달러 상쇄"}')
    loop = ActiveAnalystLoop(llm=GenerateToComplete(_Gen(claim)))
    pc = loop.run_cycle(_view(RegimeLabel.OVERHEAT, 0.3), numeric_revision=0.3)
    assert pc is not None and pc.card.kind == "probationary" and pc.card.bonus_cap == 0.0


def test_ollama_health_dead_port_graceful():
    assert ollama_health("http://localhost:59999") is False


def test_build_with_local_llm_graceful_when_server_down():
    # 서버 미가동/미설치 → llm None graceful(예외 없음), abstain
    loop = build_active_loop(use_local_llm=True)
    # 서버 떠 있으면 llm 주입될 수 있으나, 없으면 None — 둘 다 예외 없이 통과해야
    assert loop is not None
    if loop.llm is None:
        assert loop.run_cycle(_view(RegimeLabel.OVERHEAT, 0.2)) is None
