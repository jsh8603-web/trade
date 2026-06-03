"""tests/test_fhc_equity_adapter.py — equity exposure card → core FHCard wire 검증.

battery(2차전지) summary.yaml v3 → exposure_card_to_fhc → core FHC lifecycle(eval_mediator/
update_outcome/transition/bonus) + bonus_channel.size_with_bonus 소비. INV 집행 +
valuation 부재 fail-closed 정합. frame v3 §M.9 / .coord-fhc-contract §2.
"""
from pathlib import Path

import pytest
import yaml

from core.assume.fhc import (
    FHCState,
    FHCStateEnum,
    MediatorState,
    eval_mediator,
    transition,
    update_outcome,
)
from core.assume.bonus_channel import size_with_bonus
from stock.fhc_adapter import exposure_card_to_fhc

BATTERY = (
    Path(__file__).resolve().parent.parent
    / "study-research/eq_kr/industries/battery/summary.yaml"
)


@pytest.fixture
def battery_summary():
    return yaml.safe_load(BATTERY.read_text(encoding="utf-8"))


def test_adapter_builds_sector_fhc(battery_summary):
    card = exposure_card_to_fhc(battery_summary, "cs_mom_6m", bonus_cap=0.02)
    assert card.scope == "sector"
    assert card.domain == "equity"
    assert card.outcome.metric == "cs_rank_IC"   # ★sector = cs_rank_IC (.coord §2)
    assert card.falsification_metric.strip()      # 반증조건 존재(card_contract 게이트)
    assert card.card_id == "kr_battery__cs_mom_6m"
    assert card.valid_from == "2019-01-01"        # archetype attestation PIT 사전선언


def test_valuation_absent_fail_closed(battery_summary):
    """valuation 횡단면 부재 → mediator observable None → UNKNOWN → bonus 0 (INV-3 fail-closed)."""
    card = exposure_card_to_fhc(battery_summary, "cs_mom_6m", bonus_cap=0.02)
    ms = eval_mediator(card.mediator, observable_value=None)
    assert ms == MediatorState.UNKNOWN
    st = FHCState(card.card_id)
    for _ in range(60):
        update_outcome(st, 1.2, mediator_holds=(ms == MediatorState.HOLDS))
    transition(card, st, mediator_state=ms)
    # mediator UNKNOWN(=not holds) → minted-dormant, 적립 0
    assert st.realized_bonus == 0.0
    assert st.state == FHCStateEnum.MINTED


def test_mediator_holds_confirms_and_sizes(battery_summary):
    """valuation 채워짐 가정(mediator HOLDS) + 강 forward IC → CONFIRMED + bonus → size_with_bonus 소비."""
    card = exposure_card_to_fhc(battery_summary, "cs_mom_6m", bonus_cap=0.02)
    st = FHCState(card.card_id)
    for _ in range(60):
        update_outcome(st, 1.2, mediator_holds=True)   # 강 적중 신호(IC>0)
    transition(card, st, mediator_state=MediatorState.HOLDS)
    assert st.state == FHCStateEnum.CONFIRMED
    assert 0.0 < st.realized_bonus <= card.bonus_cap

    # construction = size_with_bonus 소비. INV-1 hard cap = per-name 천장 C
    sizing = size_with_bonus(
        {"kr_battery": 0.10},
        [(card, st)],
        {"kr_battery": 0.12},   # 천장 C (L1 0.10 + bonus ≤ 0.12)
    )
    a = sizing["kr_battery"]
    assert a.bonus > 0.0
    assert a.l1 <= a.final <= 0.12          # 강화(L1 위) + 천장 내
    assert a.n_cards == 1


def test_breaker_de_risk(battery_summary):
    """RegimeGlasso breaker(INV-9) → bonus 0, w=L1 (de-risk, attenuation-only)."""
    card = exposure_card_to_fhc(battery_summary, "cs_mom_6m", bonus_cap=0.02)
    st = FHCState(card.card_id)
    for _ in range(60):
        update_outcome(st, 1.2, mediator_holds=True)
    transition(card, st, mediator_state=MediatorState.HOLDS)
    sizing = size_with_bonus(
        {"kr_battery": 0.10}, [(card, st)], {"kr_battery": 0.30},
        breaker_tripped=True,
    )
    assert sizing["kr_battery"].bonus == 0.0
    assert sizing["kr_battery"].final == 0.10
    assert sizing["kr_battery"].fail_closed


def test_missing_indicator_raises(battery_summary):
    with pytest.raises(KeyError):
        exposure_card_to_fhc(battery_summary, "nonexistent_id", bonus_cap=0.02)
