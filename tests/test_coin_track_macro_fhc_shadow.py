# -*- coding: utf-8 -*-
"""tests/test_coin_track_macro_fhc_shadow.py — (B) FHC shadow 발권 production wire 회귀.

coin_track_macro.CoinTrackWithMacro._run_fhc_shadow 가 production 진입점(collect_market_state)에서
LLM 소환 카드를 raw_external_data["fhc_shadow_cards"](관찰용, 자본0)로 적재하는지 +
env off=byte-identical(미진입) + rate_cap 일1회(폭증 방지) + 고신뢰 차단(결정론 충분) + graceful 검증.

★LIVE(Claude OAuth) 발권은 .p2-fhc-live-mint.py(메인 세션 idle 시) 담당 — 본 테스트는 fake LLM 로
production wire 메서드의 적재·게이트 로직만 격리 검증(네트워크 무의존, CI 안정).
"""
import json

import pytest

from core.assume.active_loop import ActiveAnalystLoop
from core.assume.info_delta_gate import RateCapState
from core.assume.loop_factory import is_active_loop_shadow_enabled
from core.brain.macro_schema import (
    Bloc, MacroView, RegimeEstimate, RegimeLabel, ViewStatus,
)
from core.coin_track_macro import CoinTrackWithMacro


class _FakeLLM:
    """저신뢰 국면 방어 tilt 카드 발권 + audit approve(network 무의존)."""

    def complete(self, system, user, json_mode=True):
        if "audit a hypothesis" in system:
            return json.dumps({"approve": True, "reason": "ok"})
        return json.dumps({
            "statement": "저신뢰 Stagflation 방어 tilt",
            "direction": "de_risk",
            "mediator_ref": "regime:USD:Stagflation",
            "outcome_metric": "ts_rank_IC",
            "falsification_metric": "방어 sleeve 3M fwd IC < 0",
            "counter_thesis": "인플레 둔화 시 상쇄",
        })


class _DummyState:
    def __init__(self):
        self.raw_external_data = {}


def _view(label, conf):
    est = RegimeEstimate(bloc=Bloc.USD, regime_now=label, confidence_now=conf)
    return MacroView(regimes={Bloc.USD: est}, status=ViewStatus.FRESH, as_of_ts=0.0)


def _ct_with_fake_loop():
    """__init__ 우회 + fake LLM 루프 주입(LLM 실호출 대신 wire 메서드 로직 검증)."""
    ct = CoinTrackWithMacro.__new__(CoinTrackWithMacro)
    ct._fhc_loop = ActiveAnalystLoop(llm=_FakeLLM(), rate_cap=RateCapState(cap_per_slot=1))
    ct._fhc_cards = []   # (C) 누적 슬롯(__init__ 우회라 수동 초기화)
    return ct


def test_env_gate_off_by_default(monkeypatch):
    monkeypatch.delenv("ACTIVE_LOOP_SHADOW", raising=False)
    assert is_active_loop_shadow_enabled() is False
    for v in ("1", "true", "on", "yes"):
        monkeypatch.setenv("ACTIVE_LOOP_SHADOW", v)
        assert is_active_loop_shadow_enabled() is True
    monkeypatch.setenv("ACTIVE_LOOP_SHADOW", "0")
    assert is_active_loop_shadow_enabled() is False


def test_low_confidence_mints_probationary_card():
    """저신뢰(0.3) → production wire 가 probationary 카드(자본0) 적재."""
    ct = _ct_with_fake_loop()
    state = _DummyState()
    ct._run_fhc_shadow(_view(RegimeLabel.STAGFLATION, 0.3), None, state)
    cards = state.raw_external_data.get("fhc_shadow_cards")
    assert cards and len(cards) == 1
    c = cards[0]
    assert c["kind"] == "probationary" and c["bonus_cap"] == 0.0   # 자본0 = 배분 무영향
    assert c["direction"] == "de_risk" and c["falsification"]
    assert c["mediator"] == "regime:USD:Stagflation"


def test_rate_cap_one_per_slot():
    """같은 슬롯 2회째 → rate_cap 일1회 상한(폭증 방지) → 미발권."""
    ct = _ct_with_fake_loop()
    s1, s2 = _DummyState(), _DummyState()
    ct._run_fhc_shadow(_view(RegimeLabel.STAGFLATION, 0.3), None, s1)
    ct._run_fhc_shadow(_view(RegimeLabel.STAGFLATION, 0.3), None, s2)
    assert "fhc_shadow_cards" in s1.raw_external_data
    assert "fhc_shadow_cards" not in s2.raw_external_data   # 일1회 상한


def test_high_confidence_no_summon():
    """고신뢰(0.9) → 결정론 충분 → summon 차단 → 미발권."""
    ct = _ct_with_fake_loop()
    state = _DummyState()
    ct._run_fhc_shadow(_view(RegimeLabel.RECOVERY, 0.9), None, state)
    assert "fhc_shadow_cards" not in state.raw_external_data


def test_macro_view_none_graceful(monkeypatch):
    """macro_view None + classify UNAVAILABLE → graceful 미발권(예외 X).

    ★pollution-proof: 배치 실행 시 다른 테스트가 FRED env/캐시를 남겨 classify 가 우연 성공하면
    발권될 수 있으므로 RegimeClassifier 를 UNAVAILABLE 고정(이 테스트는 graceful 경로만 검증)."""
    import core.brain.regime_classifier as rc

    class _Unavail:
        def __init__(self, *a, **k):
            pass

        def classify(self, *a, **k):
            return MacroView(regimes={}, status=ViewStatus.UNAVAILABLE, as_of_ts=0.0)

    monkeypatch.setattr(rc, "RegimeClassifier", _Unavail)
    ct = _ct_with_fake_loop()
    state = _DummyState()
    ct._run_fhc_shadow(None, None, state)   # 예외 없이 반환(UNAVAILABLE → summon 차단)
    assert "fhc_shadow_cards" not in state.raw_external_data


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
