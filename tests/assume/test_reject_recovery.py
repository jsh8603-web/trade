"""IC9 reject 가설 재진입 통합 테스트 (decisions §14 R11 수렴).

S1~S6 모듈 end-to-end + event_ledger 통합 + ★시계열 IC 주입 → 재진입 발생 관찰
(사용자 검증 방식: 지표 시계열을 시간순 주입하며 reject 가설이 국면 회복 시 자동 재진입하는지).
"""
import numpy as np

from core.assume.reject_recovery import (
    RejectClass, RevivalTrigger, RejectRecord, content_address,
    classify_reject, evaluate_recovery, should_trigger_revival,
    ChatterBackoff, revival_cohort_falsified,
)
from core.assume.weight_falsification import score_ic_recovery_eprocess
from core.data.event_ledger import reduce_events, make_event


def _mk(seq, et, tt, **p):
    return make_event(et, tt=tt, dt=tt, vt=tt, seq=seq,
                      assumption_id=p.pop("aid", "H1"), payload=p)


# ---------------------------------------------------------------------------
# end-to-end lifecycle (event_ledger 통합, §14.1 상태기계)
# ---------------------------------------------------------------------------

def test_end_to_end_revival_lifecycle():
    """REJECT_RECORDED → REVIVAL_TRIGGERED → SHADOW_REENTERED → REVIVED, as-of tt-cut 추적."""
    hid = content_address(statement="credit stress → defensive 초과수익",
                          falsification_metric="credit regime IC e-process",
                          domain="equity", scope="sector", kind="parametric")
    evs = [
        _mk(0, "REJECT_RECORDED", "2024-01-01", hypothesis_id=hid, reject_class="regime_conditional",
            reason_code="credit_n4_directional", e_against_at_reject=2.1, power_at_decision=0.3),
        _mk(1, "REVIVAL_TRIGGERED", "2024-06-01", hypothesis_id=hid, revival_trigger="regime_draw", e_for_state=8.0),
        _mk(2, "SHADOW_REENTERED", "2024-06-02", hypothesis_id=hid, e_for_state=15.0),
        _mk(3, "REVIVED", "2024-07-01", hypothesis_id=hid),
    ]
    assert reduce_events(evs, tt_cut="2024-03-01").reject_status(hid) == "rejected"
    s_trig = reduce_events(evs, tt_cut="2024-06-01")
    assert s_trig.reject_status(hid) == "rejected" and s_trig.rejects[hid]["revival_trigger"] == "regime_draw"
    assert reduce_events(evs, tt_cut="2024-06-15").reject_status(hid) == "shadow"
    assert reduce_events(evs, tt_cut="2024-08-01").reject_status(hid) == "revived"
    # random-order 복원(tt 순 결정적)
    import random
    for _ in range(8):
        sh = evs[:]; random.shuffle(sh)
        assert reduce_events(sh, tt_cut="2024-06-15").reject_status(hid) == "shadow"


# ---------------------------------------------------------------------------
# reject_class 별 재진입 (§14.3 burden 분기)
# ---------------------------------------------------------------------------

def test_regime_conditional_revives_on_recovery():
    """regime_conditional: 국면 회복(IC baseline 위) → E_for 누적 → trigger → 5-AND gate → revive."""
    rec = RejectRecord(hypothesis_id="rj_rc", reject_class=RejectClass.REGIME_CONDITIONAL,
                       reason_code="rc", n_at_decision=4, e_against_at_reject=2.1)
    fired, trig = should_trigger_revival(RejectClass.REGIME_CONDITIONAL, regime_episodes=2, distinct_regimes=4)
    assert fired and trig == RevivalTrigger.REGIME_DRAW
    rng = np.random.default_rng(1)
    ic_recover = list(-0.02 + rng.normal(0, 0.01, 10)) + list(0.10 + rng.normal(0, 0.01, 40))
    revive_ev, e_for, _ = score_ic_recovery_eprocess(ic_recover, baseline_ic=0.02, sd=0.02)
    assert revive_ev is True
    dec = evaluate_recovery(rec, e_for=e_for, fdr_significant=True, effect_size=0.6,
                            dwell_ok=True, k_window_persist=2, same_regime=True)
    assert dec.revive is True and dec.overcoming_required == 0.0


def test_structural_needs_overcoming():
    """structural: E_for < E_against_at_reject → 보류 / 초과 → revive(§14.3 overcoming term)."""
    rec = RejectRecord(hypothesis_id="rj_st", reject_class=RejectClass.STRUCTURAL,
                       reason_code="st", n_at_decision=200, e_against_at_reject=20.0, power_at_decision=0.9)
    common = dict(fdr_significant=True, effect_size=0.6, dwell_ok=True, k_window_persist=2, same_regime=True)
    assert evaluate_recovery(rec, e_for=10.0, **common).revive is False
    assert evaluate_recovery(rec, e_for=25.0, **common).revive is True


def test_class_c_isolated_until_data_fixed():
    """class C(PIT-corrupt): 데이터 정정(DATA_EVENT) 전 재진입 차단(§14.5 lookahead false revival 방지)."""
    common = dict(fdr_significant=True, effect_size=0.6, dwell_ok=True, k_window_persist=2, same_regime=True)
    rec = RejectRecord(hypothesis_id="rj_c", reject_class=RejectClass.DATA_CORRUPT,
                       reason_code="pit_corrupt", n_at_decision=100, revival_trigger=RevivalTrigger.REGIME_DRAW)
    assert evaluate_recovery(rec, e_for=99.0, **common).revive is False
    rec2 = RejectRecord(hypothesis_id="rj_c2", reject_class=RejectClass.DATA_CORRUPT,
                        reason_code="pit_fixed", n_at_decision=100, revival_trigger=RevivalTrigger.DATA_EVENT)
    assert evaluate_recovery(rec2, e_for=99.0, **common).revive is True


# ---------------------------------------------------------------------------
# ★시계열 IC 주입 → 재진입 발생 관찰 (사용자 검증 방식)
# ---------------------------------------------------------------------------

def test_timeseries_injection_revival_observed():
    """★지표 IC 시계열을 시간순 주입 → reject 가설이 국면 회복 시에만 재진입(파탄 구간선 미발생).

    전반 국면 파탄(IC<baseline=reject 유지) → 후반 회복(IC>baseline=재진입 신호) 시뮬.
    convex-leak E_for 가 파탄 구간선 1로 누수(false revival 방지) → 회복 누적 시 돌파."""
    rng = np.random.default_rng(7)
    ic_broken = list(-0.03 + rng.normal(0, 0.01, 30))      # 파탄: baseline 아래
    ic_recovered = list(0.12 + rng.normal(0, 0.01, 40))    # 회복: baseline 위
    # 파탄 구간만 → 재진입 안 함(false revival 차단)
    rev_broken, _, _ = score_ic_recovery_eprocess(ic_broken, baseline_ic=0.03, sd=0.02)
    assert rev_broken is False, "파탄 구간서 false revival 발생"
    # 회복 구간 포함 → 재진입 신호 발생
    rev_full, ef_full, _ = score_ic_recovery_eprocess(ic_broken + ic_recovered, baseline_ic=0.03, sd=0.02)
    assert rev_full is True, "국면 회복 후에도 재진입 신호 미발생"


def test_alpha_pricing_blocks_repeated_reproposal():
    """동일 reject pool 약신호 반복 재제안 → alpha-wealth 고갈 → 자동 차단(§14.4 재탐구 회계)."""
    from core.structure.online_fdr import AlphaInvesting
    rec = RejectRecord(hypothesis_id="rj_rep", reject_class=RejectClass.REGIME_CONDITIONAL,
                       reason_code="rc", n_at_decision=4, e_against_at_reject=2.1)
    acct = AlphaInvesting(alpha=0.05)
    revived = sum(
        evaluate_recovery(rec, e_for=2.0, fdr_significant=True, effect_size=0.6, dwell_ok=True,
                          k_window_persist=2, same_regime=True, alpha_account=acct, p_value=0.5).revive
        for _ in range(60))
    assert revived == 0


def test_chatter_backoff_exponential():
    """revive→kill 반복 → cooldown 지수 증가(§14.8a oscillation 차단)."""
    cb = ChatterBackoff(base_cooldown=4)
    assert cb.record_kill("h", 0) == 4
    assert cb.record_kill("h", 10) - 10 == 8
    assert cb.record_kill("h", 20) - 20 == 16
    assert cb.can_retry("h", 200) is True
    cb.reset("h")
    assert cb.can_retry("h", 0) is True


def test_revival_cohort_falsification():
    """복귀 cohort OOS IC 붕괴 → 복귀=noise kill / 유지 → 통과(§14.8b)."""
    rng = np.random.default_rng(11)
    cohort_break = list(0.05 + rng.normal(0, 0.01, 10)) + list(-0.05 + rng.normal(0, 0.01, 30))
    cohort_hold = list(0.05 + rng.normal(0, 0.01, 40))
    assert revival_cohort_falsified(cohort_break, baseline_ic=0.04, sd=0.02) is True
    assert revival_cohort_falsified(cohort_hold, baseline_ic=0.04, sd=0.02) is False


# ---------------------------------------------------------------------------
# opt-in off byte-identical (IC9 코드가 기존 경로 무영향)
# ---------------------------------------------------------------------------

def test_opt_in_off_byte_identical():
    """reject event 없는 ledger → rejects 빈 dict(IC9 추가가 기존 reduce 결과 무영향, §14.6 fold)."""
    evs = [_mk(0, "ASSUMPTION_CREATED", "2024-01-01", version=1),
           _mk(1, "OUTCOME_OBSERVED", "2024-01-02", series_key="S1", value=1.0),
           _mk(2, "FDR_DECISION", "2024-01-03", reject=True, p_value=0.01, alpha_spent=0.01, family_key="f1")]
    st = reduce_events(evs)
    assert st.rejects == {}
    assert len(st.fdr_log) == 1 and st.watermark_seq == 2


def test_classify_reject_power_branch():
    """검정력 분기(§14.3): high power=structural(봤는데 없음) / low·None=regime_conditional(못 봤음)."""
    assert classify_reject(0.8) == RejectClass.STRUCTURAL
    assert classify_reject(0.3) == RejectClass.REGIME_CONDITIONAL
    assert classify_reject(None) == RejectClass.REGIME_CONDITIONAL
    assert classify_reject(0.9, data_corrupt=True) == RejectClass.DATA_CORRUPT
