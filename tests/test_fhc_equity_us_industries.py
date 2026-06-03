"""tests/test_fhc_equity_us_industries.py — eq_us 3 sleeve exposure card → core FHC wire 검증.

CP-EUS-1: study_session.yaml confidence_hook 3건(us_cyclical/us_defensive/us_mega_tech)
   primary indicator → exposure_card_to_fhc → FHCard(scope='sector') → core lifecycle +
   bonus_channel. 기존 eq_kr 패턴(test_fhc_equity_industries.py) 동일 적용.

archetype: cyclical(us_cyclical) / asset_stable(us_defensive) / compounder(us_mega_tech).
INV-3 fail-closed(valuation 부재) / INV-1 cap / INV-9 breaker 는 sleeve 불변.
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

ROOT = Path(__file__).resolve().parent.parent
US_IND_DIR = ROOT / "study-research/eq_us/industries"

# (디렉토리명, primary indicator id, 기대 industry 식별자, 기대 archetype, 기대 valid_from)
US_INDUSTRIES = [
    ("us_cyclical",  "cs_per_z_24m", "us_cyclical",  "cyclical",    "2015-01-01"),
    ("us_defensive", "cs_rev_1m",    "us_defensive", "asset_stable", "2010-01-01"),
    ("us_mega_tech", "cs_lowvol",    "us_mega_tech", "compounder",  "2015-01-01"),
]


def _load(industry_dir: str) -> dict:
    return yaml.safe_load(
        (US_IND_DIR / industry_dir / "summary.yaml").read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("ind_dir,ind_id,expect_id,expect_arch,expect_vf", US_INDUSTRIES)
def test_us_sleeve_card_builds_sector_fhc(ind_dir, ind_id, expect_id, expect_arch, expect_vf):
    """us 3 sleeve primary indicator → scope='sector' FHCard, cs_rank_IC outcome, PIT valid_from."""
    summary = _load(ind_dir)
    assert summary["industry"] == expect_id
    assert summary["archetype"] == expect_arch
    card = exposure_card_to_fhc(summary, ind_id, bonus_cap=0.02)
    assert card.scope == "sector"
    assert card.domain == "equity"
    assert card.outcome.metric == "cs_rank_IC"
    assert card.outcome.target_signal_ref == ind_id
    assert card.card_id == f"{expect_id}__{ind_id}"
    assert card.falsification_metric.strip()
    assert card.valid_from == expect_vf


@pytest.mark.parametrize("ind_dir,ind_id,expect_id,expect_arch,expect_vf", US_INDUSTRIES)
def test_us_sleeve_valuation_absent_fail_closed(ind_dir, ind_id, expect_id, expect_arch, expect_vf):
    """valuation 횡단면 부재 → mediator UNKNOWN → 적립 0 (INV-3 fail-closed) — sleeve 불변."""
    summary = _load(ind_dir)
    card = exposure_card_to_fhc(summary, ind_id, bonus_cap=0.02)
    ms = eval_mediator(card.mediator, observable_value=None)
    assert ms == MediatorState.UNKNOWN
    st = FHCState(card.card_id)
    for _ in range(60):
        update_outcome(st, 1.2, mediator_holds=(ms == MediatorState.HOLDS))
    transition(card, st, mediator_state=ms)
    assert st.realized_bonus == 0.0
    assert st.state == FHCStateEnum.MINTED


@pytest.mark.parametrize("ind_dir,ind_id,expect_id,expect_arch,expect_vf", US_INDUSTRIES)
def test_us_sleeve_mediator_holds_confirms_and_sizes(ind_dir, ind_id, expect_id, expect_arch, expect_vf):
    """valuation HOLDS + 강 forward IC → CONFIRMED + bonus, size_with_bonus 가 천장 C 내 강화."""
    summary = _load(ind_dir)
    card = exposure_card_to_fhc(summary, ind_id, bonus_cap=0.02)
    st = FHCState(card.card_id)
    for _ in range(60):
        update_outcome(st, 1.2, mediator_holds=True)
    transition(card, st, mediator_state=MediatorState.HOLDS)
    assert st.state == FHCStateEnum.CONFIRMED
    assert 0.0 < st.realized_bonus <= card.bonus_cap

    sizing = size_with_bonus({expect_id: 0.10}, [(card, st)], {expect_id: 0.12})
    a = sizing[expect_id]
    assert a.bonus > 0.0
    assert a.l1 <= a.final <= 0.12
    assert a.n_cards == 1


@pytest.mark.parametrize("ind_dir,ind_id,expect_id,expect_arch,expect_vf", US_INDUSTRIES)
def test_us_sleeve_breaker_de_risk(ind_dir, ind_id, expect_id, expect_arch, expect_vf):
    """RegimeGlasso breaker(INV-9) → bonus 0, w=L1 (de-risk, attenuation-only) — sleeve 불변."""
    summary = _load(ind_dir)
    card = exposure_card_to_fhc(summary, ind_id, bonus_cap=0.02)
    st = FHCState(card.card_id)
    for _ in range(60):
        update_outcome(st, 1.2, mediator_holds=True)
    transition(card, st, mediator_state=MediatorState.HOLDS)
    sizing = size_with_bonus(
        {expect_id: 0.10}, [(card, st)], {expect_id: 0.30}, breaker_tripped=True,
    )
    assert sizing[expect_id].bonus == 0.0
    assert sizing[expect_id].final == 0.10
    assert sizing[expect_id].fail_closed
