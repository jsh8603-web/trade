"""tests/assume/test_fhc_core.py — FHC core(S1) + bonus_channel(S3) 회귀.

설계 SSOT=.consult-judge-report-RESULTS.md / .coord-fhc-contract-20260603.md. INV 집행 + 2-leg + 5-state.
self-test(__main__)의 pytest 정식화. 두 모듈 모두 additive·호출처 0(INV-11 off byte-identical).
"""
import math

import pytest

from core.assume.fhc import (
    FHCard, FHCState, FHCStateEnum, MediatorState, MediatorSpec, MediatorTest, OutcomeSpec,
    eval_mediator, update_outcome, transition, bonus_from_evalue,
)
from core.assume.bonus_channel import size_with_bonus, AssetSizing
from core.assume.fhc_fdr import FDRFirewall


def _card(card_id="fhc.t", scope="macro", cap=0.05, confirm_thr=20.0, reject_thr=20.0,
          revival_cap=3, targets=None):
    return FHCard(
        card_id=card_id, scope=scope, domain="macro", direction="long_tilt",
        statement="capex→tilt", falsification_metric="capex 꺾이면 무효",
        mediator=MediatorSpec("capex", op=">", threshold=0.0),
        outcome=OutcomeSpec("ts_rank_IC", "tilt"),
        bonus_cap=cap, confirm_e_threshold=confirm_thr, reject_e_threshold=reject_thr,
        revival_cap=revival_cap, targets=tuple(targets) if targets else (),
    )


def _confirm(card, signal=1.2, n=60):
    st = FHCState(card.card_id)
    for _ in range(n):
        update_outcome(st, signal, mediator_holds=True)
    transition(card, st, mediator_state=MediatorState.HOLDS)
    return st


# --- card_contract 정합 ---
def test_falsification_gate():
    with pytest.raises(ValueError):
        _card().__class__(  # falsification 빈 값
            card_id="bad", scope="macro", domain="macro", direction="long_tilt",
            statement="x", falsification_metric="  ",
            mediator=MediatorSpec("x"), outcome=OutcomeSpec())


def test_bonus_cap_nonneg():
    with pytest.raises(ValueError):
        FHCard(card_id="b", scope="macro", domain="macro", direction="long_tilt",
               statement="x", falsification_metric="f",
               mediator=MediatorSpec("x"), outcome=OutcomeSpec(), bonus_cap=-0.1)


# --- mediator gating ---
def test_eval_mediator_deterministic_and_failclosed():
    sp = MediatorSpec("x", op=">", threshold=0.0)
    assert eval_mediator(sp, 0.5) == MediatorState.HOLDS
    assert eval_mediator(sp, -0.5) == MediatorState.FAILS
    assert eval_mediator(sp, None) == MediatorState.UNKNOWN          # fail-closed


def test_eval_mediator_state_space():
    sp = MediatorSpec("r", test=MediatorTest.STATE_SPACE_POSTERIOR)
    assert eval_mediator(sp, posterior_holds=True) == MediatorState.HOLDS
    assert eval_mediator(sp, posterior_holds=False) == MediatorState.FAILS
    assert eval_mediator(sp, posterior_holds=None) == MediatorState.UNKNOWN


# --- 5-state machine ---
def test_minted_to_confirmed_accrues_bonus():
    c = _card()
    st = _confirm(c)
    assert st.state == FHCStateEnum.CONFIRMED
    assert 0.0 < st.realized_bonus <= c.bonus_cap


def test_confirmed_to_vacated_suspends_bonus():
    c = _card()
    st = _confirm(c)
    transition(c, st, mediator_state=MediatorState.FAILS)
    assert st.state == FHCStateEnum.VACATED
    assert st.realized_bonus == 0.0


def test_vacated_to_revived():
    c = _card()
    st = _confirm(c)
    transition(c, st, mediator_state=MediatorState.FAILS)
    transition(c, st, mediator_state=MediatorState.HOLDS)
    assert st.state == FHCStateEnum.REVIVED
    assert st.revival_count == 1
    assert st.realized_bonus > 0.0


# --- INV ---
def test_inv_minted_vacate_forbidden():
    c = _card()
    st = FHCState(c.card_id)
    transition(c, st, mediator_state=MediatorState.FAILS)
    assert st.state == FHCStateEnum.MINTED                 # minted-dormant, vacate 아님
    assert st.realized_bonus == 0.0


def test_inv_rejected_absorbing():
    c = _card(reject_thr=5.0)
    st = FHCState(c.card_id)
    for _ in range(80):
        update_outcome(st, -1.5, mediator_holds=True)      # adverse
    transition(c, st, mediator_state=MediatorState.HOLDS)
    assert st.state == FHCStateEnum.REJECTED
    transition(c, st, mediator_state=MediatorState.HOLDS)
    assert st.state == FHCStateEnum.REJECTED               # absorbing


def test_inv_revival_cap_retires():
    c = _card(revival_cap=1)
    st = _confirm(c)
    transition(c, st, mediator_state=MediatorState.FAILS)   # vacated
    transition(c, st, mediator_state=MediatorState.HOLDS)   # revived #1
    transition(c, st, mediator_state=MediatorState.FAILS)   # vacated
    transition(c, st, mediator_state=MediatorState.HOLDS)   # cap → retire
    assert st.state == FHCStateEnum.REJECTED


def test_inv5_failclosed_bonus():
    c = _card()
    st = _confirm(c)
    assert bonus_from_evalue(c, st) > 0
    st.mediator_state = MediatorState.UNKNOWN
    assert bonus_from_evalue(c, st) == 0.0


def test_previsible_no_bet_on_fails():
    c = _card()
    st = FHCState(c.card_id)
    e0 = st.e_value
    for _ in range(30):
        update_outcome(st, 1.5, mediator_holds=False)      # fails → no-bet
    assert st.e_value == e0
    assert st.holds_ticks == 0


# --- bonus_channel (S3) ---
def test_bonus_b_amplification_below_ceiling():
    c = _card(targets=["BTC"])
    st = _confirm(c)
    r = size_with_bonus({"BTC": 0.10}, [(c, st)], {"BTC": 0.30})
    a = r["BTC"]
    assert a.final > a.l1 and not a.clipped
    assert abs(a.final - (a.l1 + a.bonus)) < 1e-9


def test_bonus_inv1_hard_cap():
    c = _card(targets=["BTC"])
    st = _confirm(c)
    r = size_with_bonus({"BTC": 0.10}, [(c, st)], {"BTC": 0.105})
    assert abs(r["BTC"].final - 0.105) < 1e-9 and r["BTC"].clipped


def test_bonus_inv9_breaker():
    c = _card(targets=["BTC"])
    st = _confirm(c)
    r = size_with_bonus({"BTC": 0.10}, [(c, st)], {"BTC": 0.30}, breaker_tripped=True)
    assert r["BTC"].bonus == 0.0 and r["BTC"].final == 0.10 and r["BTC"].fail_closed


def test_bonus_inv3_failclosed_missing_ceiling():
    c = _card(targets=["BTC"])
    st = _confirm(c)
    r = size_with_bonus({"BTC": 0.10}, [(c, st)], {})
    assert r["BTC"].bonus == 0.0 and r["BTC"].final == 0.10 and r["BTC"].fail_closed


def test_bonus_inv5_minted_no_contribution():
    c = _card(card_id="fhc.m", scope="ETH", targets=["ETH"])
    st = FHCState(c.card_id)                                # minted
    r = size_with_bonus({"ETH": 0.10}, [(c, st)], {"ETH": 0.30})
    assert r["ETH"].bonus == 0.0 and r["ETH"].n_cards == 0


# --- INV-12 FDR firewall (fhc_fdr) ---
def _state_e(card, signal, n):
    st = FHCState(card.card_id)
    for _ in range(n):
        update_outcome(st, signal, mediator_holds=True)
    return st


def test_fdr_none_fallback():
    c = _card(targets=["BTC"])
    st = _state_e(c, 1.2, 60)
    transition(c, st, mediator_state=MediatorState.HOLDS, fdr_firewall=None)
    assert st.state == FHCStateEnum.CONFIRMED              # 고정 임계 fallback


def test_fdr_prefilter_no_budget():
    fw = FDRFirewall(alpha=0.05)
    c = _card(card_id="pf", confirm_thr=1e9)               # 도달 불가
    st = _state_e(c, 1.2, 60)
    transition(c, st, mediator_state=MediatorState.HOLDS, fdr_firewall=fw)
    assert st.state == FHCStateEnum.MINTED and fw.stats() == {}   # budget 미소비


def test_fdr_layer_isolation():
    fw = FDRFirewall(alpha=0.05)
    cm = _card(card_id="m", scope="macro"); sm = _state_e(cm, 1.5, 80)
    cs = _card(card_id="s", scope="sector"); ss = _state_e(cs, 1.5, 80)
    transition(cm, sm, mediator_state=MediatorState.HOLDS, fdr_firewall=fw)
    transition(cs, ss, mediator_state=MediatorState.HOLDS, fdr_firewall=fw)
    s = fw.stats()
    assert s["macro"]["t"] == 1 and s["basket"]["t"] == 1  # INV-12 별 ledger


def test_fdr_double_spend_cache():
    fw = FDRFirewall(alpha=0.05)
    c = _card(card_id="d"); st = _state_e(c, 1.5, 80)
    r1 = fw.test_confirm(c, st.e_value)
    r2 = fw.test_confirm(c, st.e_value)
    assert r1 == r2 and fw.stats()["macro"]["t"] == 1      # 카드당 1회


def test_fdr_multiplicity_control():
    fw2 = FDRFirewall(alpha=0.05)
    n_fdr = 0
    for i in range(20):
        ci = _card(card_id=f"x{i}"); sti = _state_e(ci, 0.62, 50)
        transition(ci, sti, mediator_state=MediatorState.HOLDS, fdr_firewall=fw2)
        n_fdr += (sti.state == FHCStateEnum.CONFIRMED)
    n_fixed = 0
    for i in range(20):
        ci = _card(card_id=f"y{i}"); sti = _state_e(ci, 0.62, 50)
        transition(ci, sti, mediator_state=MediatorState.HOLDS, fdr_firewall=None)
        n_fixed += (sti.state == FHCStateEnum.CONFIRMED)
    assert n_fdr <= n_fixed                                # FDR multiplicity 억제
