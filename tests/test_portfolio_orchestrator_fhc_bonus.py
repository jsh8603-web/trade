# -*- coding: utf-8 -*-
"""tests/test_portfolio_orchestrator_fhc_bonus.py — (C) FHC bonus → weight allocate wire 회귀.

PortfolioOrchestrator.allocate(fhc_card_states=...) 가 env FHC_BONUS opt-in 으로 확정 카드 bonus 를
L1 위로 tilt(합=1 재정규화) + INV 집행 검증:
  - off=byte-identical(card 있어도 무변경)
  - probationary(자본0) 카드 → INV-5 confirmed-only 로 기여 0(byte-identical)
  - confirmed + mediator HOLDS → 해당 슬리브 weight tilt ↑
  - 천장 C(SLEEVE_BANDS 상한) clip
  - breaker(macro_abstain) → bonus 0

★결정론 코어(allocate) 변경 = env-gated + 회귀 엄수. 실주문은 별도(GatedOrderRouter, go-live).
"""
import pytest

from core.assume.fhc import (
    FHCard, FHCState, FHCStateEnum, MediatorSpec, MediatorState, OutcomeSpec,
    transition, update_outcome,
)
from core.portfolio_orchestrator import PortfolioOrchestrator


def _confirmed(asset, cap=0.05):
    c = FHCard(card_id="fhc." + asset, scope=asset, domain="macro", direction="long_tilt",
               statement="t", falsification_metric="f",
               mediator=MediatorSpec("x", op=">", threshold=0.0),
               outcome=OutcomeSpec("ts_rank_IC", "s"), bonus_cap=cap,
               confirm_e_threshold=20.0, targets=(asset,))
    st = FHCState(c.card_id)
    for _ in range(60):
        update_outcome(st, 1.2, mediator_holds=True)
    transition(c, st, mediator_state=MediatorState.HOLDS)
    assert st.state == FHCStateEnum.CONFIRMED
    return c, st


def _probationary(asset):
    c = FHCard(card_id="p." + asset, scope=asset, domain="macro", direction="long_tilt",
               statement="t", falsification_metric="f", mediator=MediatorSpec("x"),
               outcome=OutcomeSpec(), bonus_cap=0.0, kind="probationary", targets=(asset,))
    return c, FHCState(c.card_id)   # minted


@pytest.fixture
def orch():
    return PortfolioOrchestrator()


@pytest.fixture
def base_weights(orch):
    return orch.allocate(macro_view=None)["weights"]


def test_off_byte_identical(orch, base_weights, monkeypatch):
    monkeypatch.delenv("FHC_BONUS", raising=False)
    r = orch.allocate(macro_view=None, fhc_card_states=[_confirmed("us_stock")])
    assert r["weights"] == base_weights
    assert "fhc_sizing" not in r


def test_probationary_only_no_change(orch, base_weights, monkeypatch):
    monkeypatch.setenv("FHC_BONUS", "true")
    r = orch.allocate(macro_view=None, fhc_card_states=[_probationary("us_stock")])
    assert r["weights"] == base_weights          # INV-5 confirmed-only → 자본0 기여 0
    assert "fhc_sizing" not in r


def test_confirmed_tilts_weight(orch, base_weights, monkeypatch):
    monkeypatch.setenv("FHC_BONUS", "true")
    us0 = base_weights["us_stock"]
    r = orch.allocate(macro_view=None, fhc_card_states=[_confirmed("us_stock", cap=0.05)])
    w = r["weights"]
    assert w["us_stock"] > us0                    # L1 위 tilt
    assert abs(sum(w.values()) - 1.0) < 1e-9      # 합=1 재정규화
    assert "fhc_bonus_applied" in r.get("caution", [])
    assert r["fhc_sizing"]["us_stock"]["bonus"] > 0


def test_ceiling_clip(orch, monkeypatch):
    monkeypatch.setenv("FHC_BONUS", "true")
    r = orch.allocate(macro_view=None, fhc_card_states=[_confirmed("us_stock", cap=0.9)])
    s = r["fhc_sizing"]["us_stock"]
    assert s["clipped"] is True                   # 밴드 상한(0.45)에서 clip
    assert s["final"] <= 0.45 + 1e-9


def test_apply_fhc_bonus_helper_normalizes(orch):
    weights = {"us_stock": 0.25, "bond": 0.25, "cash": 0.5}
    new_w, sized = orch._apply_fhc_bonus(weights, [_confirmed("us_stock", cap=0.05)])
    assert abs(sum(new_w.values()) - 1.0) < 1e-9
    assert new_w["us_stock"] > weights["us_stock"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
