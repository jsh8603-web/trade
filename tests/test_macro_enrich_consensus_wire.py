# -*- coding: utf-8 -*-
"""tests/test_macro_enrich_consensus_wire.py — 기존 brain LLM wire 회귀.

(enrich) macro_reasoning.enrich → coin_track_macro 거시 LLM stance 주입(결정론 baseline 수정).
(consensus) ConsensusNode → portfolio_orchestrator.allocate 고-스테이크스 down-only de-risk.
둘 다 env opt-in(MACRO_ENRICH/MACRO_CONSENSUS) off=byte-identical.
"""
import json

import pytest

from core.brain.consensus_node import ConsensusNode, apply_consensus_derisk
from core.brain.macro_reasoning import MacroReasoningNode
from core.brain.macro_schema import (
    Bloc, MacroView, RegimeEstimate, RegimeLabel, ViewStatus,
)
from core.coin_track_macro import CoinTrackWithMacro
from core.portfolio_orchestrator import PortfolioOrchestrator


def _view(conf):
    est = RegimeEstimate(bloc=Bloc.USD, regime_now=RegimeLabel.STAGFLATION, confidence_now=conf)
    return MacroView(regimes={Bloc.USD: est}, status=ViewStatus.FRESH, as_of_ts=0.0)


class _EnrichLLM:
    def complete(self, system, user, json_mode=True):
        return json.dumps({
            "thesis": "stagflation 방어", "counter_thesis": "인플레 둔화",
            "stance": {"us_stock": -0.5, "gold": 0.6, "bond": 0.3, "cash": 0.2,
                       "commodity": 0.4, "kr_stock": -0.3, "coin": -0.2},
            "confidence": 0.8})


# ── enrich ─────────────────────────────────────────────────────────────────
def _ct():
    ct = CoinTrackWithMacro.__new__(CoinTrackWithMacro)
    ct._macro_node = None
    ct._fhc_ingest = None
    return ct


def test_enrich_high_confidence_baseline():
    """고신뢰(0.9) → trigger 없음 → baseline(stance 미주입)."""
    ct = _ct()
    out = ct._run_macro_enrich(_view(0.9))
    assert getattr(out, "stance", None) in (None, {})


def test_enrich_low_confidence_injects_stance():
    """저신뢰(0.3) → LLM stance 주입(결정론 baseline 수정), confidence 축소."""
    ct = _ct()
    ct._macro_node = MacroReasoningNode(llm=_EnrichLLM())
    out = ct._run_macro_enrich(_view(0.3))
    assert out.stance and out.stance["gold"] > 0
    assert abs(out.stance["gold"] - 0.6 * 0.8) < 1e-6   # confidence 0.8 축소


def test_enrich_llm_none_abstain():
    ct = _ct()
    ct._macro_node = MacroReasoningNode(llm=None)
    out = ct._run_macro_enrich(_view(0.3))
    assert getattr(out, "stance", None) in (None, {})


# ── consensus ───────────────────────────────────────────────────────────────
def test_consensus_off_byte_identical(monkeypatch):
    monkeypatch.delenv("MACRO_CONSENSUS", raising=False)
    orch = PortfolioOrchestrator()
    base = orch.allocate(macro_view=None)["weights"]
    r = orch.allocate(macro_view=None)
    assert r["weights"] == base and "consensus" not in r


def test_consensus_high_stakes_derisk(monkeypatch):
    monkeypatch.setenv("MACRO_CONSENSUS", "on")
    orch = PortfolioOrchestrator()
    base = orch.allocate(macro_view=None)["weights"]

    class _LLM:
        def complete(self, system, user, json_mode=True):
            return json.dumps({"approve": False, "de_risk": 0.5, "reason": "over-concentrated"})

    orch._consensus_node = ConsensusNode(llm=_LLM())
    orch._prev_weights = {k: (0.9 if k == "cash" else 0.0) for k in base}   # 고-스테이크스 유도
    r = orch.allocate(macro_view=None)
    assert r["consensus"]["de_risk"] == 0.5
    assert "consensus_derisk" in r.get("caution", [])
    assert abs(sum(r["weights"].values()) - 1.0) < 1e-9


def test_consensus_low_stakes_no_trigger(monkeypatch):
    monkeypatch.setenv("MACRO_CONSENSUS", "on")
    orch = PortfolioOrchestrator()
    base = orch.allocate(macro_view=None)["weights"]
    orch._consensus_node = ConsensusNode(llm=lambda: None)   # 미호출 검증(저-스테이크스)
    orch._prev_weights = dict(base)                          # 변경 0 = 저-스테이크스
    r = orch.allocate(macro_view=None)
    assert "consensus" not in r                              # review 미발동


def test_consensus_down_only_clip():
    """LLM de_risk 1.5 → clip 1.0(증폭 불가). de_risk<0 → 0."""
    n = ConsensusNode(llm=type("L", (), {
        "complete": lambda self, s, u, json_mode=True: json.dumps({"approve": False, "de_risk": 1.5})
    })())
    r = n.review(weights={"a": 0.6, "b": 0.4}, prior={"a": 0.3, "b": 0.7})
    assert r["de_risk"] == 1.0


def test_apply_derisk_down_only():
    w = {"us_stock": 0.6, "bond": 0.4}
    prior = {"us_stock": 0.3, "bond": 0.7}
    assert apply_consensus_derisk(w, prior, 0.0) == w           # 0=무변경
    out = apply_consensus_derisk(w, prior, 0.5)
    assert out["us_stock"] < w["us_stock"]                      # prior 후퇴(증폭 없음)
    assert abs(sum(out.values()) - 1.0) < 1e-9


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
