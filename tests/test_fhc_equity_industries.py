"""tests/test_fhc_equity_industries.py — eq_kr 산업 exposure card → core FHC wire 전수 검증.

battery 단독(test_fhc_equity_adapter.py) → 완료 4산업(battery/financial/consumer/
semiconductor) 전수 parametrize. 각 산업의 confidence_hook 연결 primary indicator 가
exposure_card_to_fhc → FHCard(scope='sector') → core lifecycle(eval_mediator/
update_outcome/transition) + bonus_channel.size_with_bonus 를 일관 통과하는지 박제.

★4산업 archetype 분기(cyclical-momentum / spread_driven-regime / asset_stable-valuation /
   cyclical-reversal)가 동일 wire 한 줄로 흡수됨을 검증 = frame v3 §M.7 division of labor.
INV-3 fail-closed(valuation 부재) + INV-1 cap + INV-9 breaker 는 산업 불변.
frame v3 §M.9 / .coord-fhc-contract-20260603.md §2.
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
IND_DIR = ROOT / "study-research/eq_kr/industries"

# (산업, primary indicator id, 기대 industry 식별자, 기대 archetype)
# ★5 archetype 전수: cyclical-momentum / cyclical-reversal / spread-regime /
#   asset_stable-valuation(×2 재현) / event_driven-변동성. 동일 wire 가 전부 흡수.
INDUSTRIES = [
    ("battery", "cs_mom_6m", "kr_battery", "cyclical"),
    ("financial", "cs_mom_6m_rate_up", "kr_financial", "spread_driven"),
    ("consumer", "cs_per_z_24m", "kr_consumer", "asset_stable"),
    ("semiconductor", "cs_mom_6m_reversal", "kr_semiconductor", "cyclical"),
    ("bio", "cs_lowvol", "kr_bio", "event_driven"),          # 멀티플 부적합 → 변동성 신호
    ("telecom", "cs_pbr_z_24m", "kr_telecom", "asset_stable"),  # value premium 재현(n=13 magnitude hedge)
    ("auto", "cs_pbr_z_24m", "kr_auto", "cyclical"),          # ★momentum 무효 → PBR value(PER=peak-EPS trap✗)
]


def _load(industry):
    return yaml.safe_load((IND_DIR / industry / "summary.yaml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("industry,ind_id,expect_id,expect_arch", INDUSTRIES)
def test_industry_card_builds_sector_fhc(industry, ind_id, expect_id, expect_arch):
    """4산업 각 primary indicator → scope='sector' FHCard, cs_rank_IC outcome, PIT valid_from."""
    summary = _load(industry)
    assert summary["industry"] == expect_id
    assert summary["archetype"] == expect_arch
    card = exposure_card_to_fhc(summary, ind_id, bonus_cap=0.02)
    assert card.scope == "sector"
    assert card.domain == "equity"
    assert card.outcome.metric == "cs_rank_IC"          # 섹터 = 횡단면 forward IC
    assert card.outcome.target_signal_ref == ind_id
    assert card.card_id == f"{expect_id}__{ind_id}"
    assert card.falsification_metric.strip()             # 반증조건 존재(card_contract 게이트)
    assert card.valid_from == "2019-01-01"               # archetype attestation PIT 사전선언


@pytest.mark.parametrize("industry,ind_id,expect_id,expect_arch", INDUSTRIES)
def test_industry_valuation_absent_fail_closed(industry, ind_id, expect_id, expect_arch):
    """valuation 횡단면 부재 → mediator UNKNOWN → 적립 0 (INV-3 fail-closed) — 산업 불변."""
    summary = _load(industry)
    card = exposure_card_to_fhc(summary, ind_id, bonus_cap=0.02)
    ms = eval_mediator(card.mediator, observable_value=None)
    assert ms == MediatorState.UNKNOWN
    st = FHCState(card.card_id)
    for _ in range(60):
        update_outcome(st, 1.2, mediator_holds=(ms == MediatorState.HOLDS))
    transition(card, st, mediator_state=ms)
    assert st.realized_bonus == 0.0
    assert st.state == FHCStateEnum.MINTED


@pytest.mark.parametrize("industry,ind_id,expect_id,expect_arch", INDUSTRIES)
def test_industry_mediator_holds_confirms_and_sizes(industry, ind_id, expect_id, expect_arch):
    """valuation HOLDS + 강 forward IC → CONFIRMED + bonus, size_with_bonus 가 천장 C 내 강화."""
    summary = _load(industry)
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
    assert a.l1 <= a.final <= 0.12                        # INV-1 천장 C 내
    assert a.n_cards == 1


@pytest.mark.parametrize("industry,ind_id,expect_id,expect_arch", INDUSTRIES)
def test_industry_breaker_de_risk(industry, ind_id, expect_id, expect_arch):
    """RegimeGlasso breaker(INV-9) → bonus 0, w=L1 (de-risk, attenuation-only) — 산업 불변."""
    summary = _load(industry)
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
