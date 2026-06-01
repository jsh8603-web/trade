"""IC4 graduation(candidate→adopted) 루프 테스트.

5-AND adopt gate 재사용 + StudyRegister 자가승격 0 + 사이클 경계 idempotent + event_ledger
candidate→ratified projection. reject_recovery(IC9)와 대칭(candidate 졸업 vs reject 복귀).
"""
from core.assume.graduation import (
    CandidateCard, GraduationDecision, evaluate_graduation,
    graduation_sweep, make_ratify_events,
)
from core.data.event_ledger import make_event, reduce_events

_PASS = dict(fdr_significant=True, effect_size=0.6, dwell_ok=True,
             k_window_persist=2, same_regime=True)


def test_5and_graduation_pass():
    d = evaluate_graduation(CandidateCard("h1", **_PASS))
    assert d.graduate is True and d.gate_promote is True


def test_effect_weak_no_graduation():
    """effect 0.3 < threshold 0.5 → 5-AND 미충족 → graduate False."""
    d = evaluate_graduation(CandidateCard("h2", fdr_significant=True, effect_size=0.3,
                                          dwell_ok=True, k_window_persist=2, same_regime=True))
    assert d.graduate is False


def test_self_promote_blocked():
    """★자가 승격 0: proposer == self_owner → 게이트 충족이어도 차단(confirmation bias 방지)."""
    blocked = evaluate_graduation(CandidateCard("h3", proposer="study_register", **_PASS),
                                  self_owner="study_register")
    assert blocked.graduate is False and blocked.self_promote_blocked is True
    # 외부 owner면 정상 승격
    ext = evaluate_graduation(CandidateCard("h3", proposer="study_register", **_PASS),
                              self_owner="external_evaluator")
    assert ext.graduate is True and ext.self_promote_blocked is False


def test_cycle_boundary_idempotent():
    """사이클 경계에서만 sweep. 같은 cycle_id 재호출 → no-op([], flip 1회 보장)."""
    cards = [CandidateCard("h1", **_PASS),
             CandidateCard("h2", fdr_significant=True, effect_size=0.3, dwell_ok=True, k_window_persist=2)]
    boundary = graduation_sweep(cards, cycle_id="2026Q2", last_cycle_id="2026Q1")
    same = graduation_sweep(cards, cycle_id="2026Q2", last_cycle_id="2026Q2")
    assert len(boundary) == 2 and same == []
    assert sum(1 for x in boundary if x.graduate) == 1   # h1만 졸업


def test_falsifiable_gate():
    """falsifiable=False(검정력 미달) → 형식상 유의해도 승격 차단(§1.8)."""
    d = evaluate_graduation(CandidateCard("h5", falsifiable=False, **_PASS))
    assert d.graduate is False


def test_base_layer_no_auto_graduation():
    """base-layer 가정(regime 모델 등) = 자동 승격 금지(사람 비준 C-meta)."""
    d = evaluate_graduation(CandidateCard("h6", is_base_layer=True, **_PASS))
    assert d.graduate is False


def test_event_ledger_candidate_to_ratified():
    """★candidate→ratified as-of projection: CANDIDATE_PROPOSED→candidate, RATIFIED→ratified."""
    evs = [
        make_event("ASSUMPTION_CREATED", tt="2026-01-01", dt="2026-01-01", vt="2026-01-01",
                   seq=0, assumption_id="h1", payload={"version": 1}),
        make_event("CANDIDATE_PROPOSED", tt="2026-02-01", dt="2026-02-01", vt="2026-02-01",
                   seq=1, assumption_id="h1", payload={}),
    ]
    ratify = make_ratify_events([evaluate_graduation(CandidateCard("h1", **_PASS))],
                                tt="2026-04-01", seq_start=2)
    assert len(ratify) == 1
    assert reduce_events(evs, tt_cut="2026-01-15").assumption_status("h1") == "active"
    assert reduce_events(evs, tt_cut="2026-03-01").assumption_status("h1") == "candidate"
    assert reduce_events(evs + ratify, tt_cut="2026-05-01").assumption_status("h1") == "ratified"
    # random-order 복원(tt 순 결정적)
    import random
    allev = evs + ratify
    for _ in range(6):
        sh = allev[:]; random.shuffle(sh)
        assert reduce_events(sh, tt_cut="2026-05-01").assumption_status("h1") == "ratified"


def test_no_graduation_no_ratify_event():
    """graduate=False 결정은 RATIFIED event 미발행(졸업 안 한 가설은 ledger 무변)."""
    weak = evaluate_graduation(CandidateCard("h2", fdr_significant=True, effect_size=0.3,
                                             dwell_ok=True, k_window_persist=2))
    assert make_ratify_events([weak], tt="2026-04-01") == []


def test_opt_in_off_byte_identical():
    """graduation event 미발생 → assumption status 변화 0(기존 active 유지, 무회귀)."""
    base = [make_event("ASSUMPTION_CREATED", tt="2026-01-01", dt="2026-01-01", vt="2026-01-01",
                       seq=0, assumption_id="h9", payload={"version": 1})]
    st = reduce_events(base)
    assert st.assumption_status("h9") == "active"
    assert st.assumption_status("missing") is None
