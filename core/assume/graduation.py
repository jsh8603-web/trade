"""core/assume/graduation.py — IC4: candidate 가설 졸업(candidate→adopted) 루프.

study/지표가 누적 증거(IC e-process)로 5-AND adopt gate(assumption_stats.hysteresis_and_gate)를
통과하면 adopted 로 승격(graduation). reject 재진입(reject_recovery.evaluate_recovery)과 대칭:
- reject_recovery: rejected  → (trigger)     → shadow → 5-AND → revived
- graduation:      candidate → (사이클 경계) →        → 5-AND → ratified(adopted)

★설계 원칙(decisions §11 IC4 + progress wire-impl):
- owner = 외부 평가자(update_controller 5-AND). StudyRegister **자가 승격 0**(confirmation bias 방지):
  proposer == self_owner 면 차단(자기 study 를 자기가 졸업시키지 못함).
- 사이클 경계 flip: 매 allocate 가 아니라 cycle_id 경계에서 1회 sweep(idempotent — 같은 cycle 재호출 no-op).
- e-process(누적 증거)는 호출자/test 가 산출해 (fdr/effect/dwell/k_window/same_regime) 로 주입
  (reject_recovery.evaluate_recovery 와 동일 — gate 입력은 외부 상태).
- base-layer 가정·falsifiable=False(검정력 미달)는 자동 승격 차단(hysteresis_and_gate 게이트 위임).
- opt-in off byte-identical: graduation_sweep 호출처 0 = 자동 격리(go-live 시 런타임 사이클 경계서 소비).
  RATIFIED event 도 on 경로만 emit(off=미발생=event_ledger byte-identical, forward-compat fold).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass(frozen=True)
class CandidateCard:
    """졸업 후보 1건. 5-AND 입력(누적 증거)은 호출자가 IC e-process 에서 산출해 주입."""
    hypothesis_id: str
    fdr_significant: bool = False
    effect_size: float = 0.0
    dwell_ok: bool = False
    k_window_persist: int = 0
    same_regime: bool = True
    falsifiable: bool = True           # §1.8 검정력 게이트(False=보호관찰, 승격 차단)
    is_base_layer: bool = False        # base-layer 가정=자동승격 금지(사람 비준, C-meta)
    proposer: str = ""                 # 제안 주체(자가승격 가드용)


@dataclass(frozen=True)
class GraduationDecision:
    hypothesis_id: str
    graduate: bool
    reason: str
    gate_promote: bool = False
    self_promote_blocked: bool = False


def evaluate_graduation(card: CandidateCard, *, adopt_gate=None,
                        self_owner: Optional[str] = None) -> GraduationDecision:
    """candidate → 5-AND adopt gate 판정. StudyRegister 자가 승격 차단(confirmation bias 방지).

    adopt_gate=None → assumption_stats.hysteresis_and_gate 재사용(reject_recovery 와 동일 게이트,
    새 human surface 신설 X = §14.1 정합). self_owner 가 card.proposer 와 같으면 승격 차단.
    """
    # 자가 승격 가드 — 외부 평가자만 졸업시킬 수 있음(StudyRegister 자기 study 차단).
    if self_owner is not None and card.proposer and card.proposer == self_owner:
        return GraduationDecision(card.hypothesis_id, graduate=False,
                                  reason=f"self_promote_blocked(proposer={card.proposer})",
                                  gate_promote=False, self_promote_blocked=True)
    if adopt_gate is None:
        from core.structure.assumption_stats import hysteresis_and_gate
        adopt_gate = hysteresis_and_gate
    gate = adopt_gate(
        fdr_significant=card.fdr_significant, effect_size=card.effect_size,
        dwell_ok=card.dwell_ok, k_window_persist=card.k_window_persist,
        same_regime=card.same_regime, is_base_layer=card.is_base_layer,
        falsifiable=card.falsifiable,
    )
    promote = bool(gate.promote)
    return GraduationDecision(
        card.hypothesis_id, graduate=promote,
        reason="5-AND graduation gate " + ("통과" if promote else "미충족"),
        gate_promote=promote)


def graduation_sweep(candidates: Sequence[CandidateCard], *, cycle_id,
                     last_cycle_id=None, adopt_gate=None,
                     self_owner: Optional[str] = None) -> list:
    """사이클 경계 졸업 sweep. cycle_id == last_cycle_id(같은 사이클) → no-op([], idempotent).

    경계일 때만 candidate 전수 5-AND 평가. graduate=True/False 전 결정 리스트 반환
    (event 발행 = make_ratify_events helper 또는 호출자). 같은 사이클 중복 호출이 재승격을 일으키지
    않도록(flip 1회) cycle 경계 가드 — reject_recovery 의 ChatterBackoff 와 같은 oscillation 방어 취지.
    """
    if last_cycle_id is not None and cycle_id == last_cycle_id:
        return []                              # 사이클 경계 아님 — flip 금지(idempotent)
    return [evaluate_graduation(c, adopt_gate=adopt_gate, self_owner=self_owner)
            for c in candidates]


def make_ratify_events(decisions: Sequence[GraduationDecision], *, tt, seq_start: int = 0):
    """graduate=True 결정 → RATIFIED event 리스트(event_ledger.make_event). on 경로만 호출
    (off=미발생=byte-identical). event_ledger projection 이 status=ratified(adopted) 로 fold."""
    from core.data.event_ledger import make_event
    evs = []
    seq = seq_start
    for d in decisions:
        if not d.graduate:
            continue
        evs.append(make_event("RATIFIED", tt=tt, dt=tt, vt=tt, seq=seq,
                              assumption_id=d.hypothesis_id,
                              payload={"reason": d.reason}))
        seq += 1
    return evs


# ===========================================================================
# self-test
# ===========================================================================
if __name__ == "__main__":
    _common = dict(fdr_significant=True, effect_size=0.6, dwell_ok=True,
                   k_window_persist=2, same_regime=True)

    # 1) 5-AND 전 조건 충족 → graduate
    d = evaluate_graduation(CandidateCard("h1", **_common))
    assert d.graduate is True and d.gate_promote is True, d
    print(f"1) 5-AND 통과 graduation OK: {d.reason}")

    # 2) effect 약(0.3<0.5 threshold) → 미충족 → graduate False
    d2 = evaluate_graduation(CandidateCard("h2", fdr_significant=True, effect_size=0.3,
                                           dwell_ok=True, k_window_persist=2, same_regime=True))
    assert d2.graduate is False, d2
    print(f"2) effect 약 미충족 OK: graduate={d2.graduate}")

    # 3) ★자가 승격 차단: proposer == self_owner → 게이트 통과 조건이어도 blocked(confirmation bias)
    d3 = evaluate_graduation(CandidateCard("h3", proposer="study_register", **_common),
                             self_owner="study_register")
    assert d3.graduate is False and d3.self_promote_blocked is True, d3
    # 외부 owner(다른 proposer)면 정상 승격
    d3b = evaluate_graduation(CandidateCard("h3", proposer="study_register", **_common),
                              self_owner="external_evaluator")
    assert d3b.graduate is True, d3b
    print(f"3) 자가승격 차단 OK: self={d3.self_promote_blocked} / 외부 owner graduate={d3b.graduate}")

    # 4) ★사이클 경계 idempotent: 같은 cycle_id 재호출 → no-op([])
    cards = [CandidateCard("h1", **_common), CandidateCard("h2", effect_size=0.3,
             fdr_significant=True, dwell_ok=True, k_window_persist=2)]
    sweep_boundary = graduation_sweep(cards, cycle_id="2026Q2", last_cycle_id="2026Q1")
    sweep_same = graduation_sweep(cards, cycle_id="2026Q2", last_cycle_id="2026Q2")
    assert len(sweep_boundary) == 2 and sweep_same == [], (len(sweep_boundary), sweep_same)
    n_grad = sum(1 for x in sweep_boundary if x.graduate)
    print(f"4) 사이클 경계 sweep OK: 경계 {len(sweep_boundary)}건 평가({n_grad} 졸업) / 같은 cycle no-op {sweep_same}")

    # 5) falsifiable=False(검정력 미달) → 형식상 유의해도 승격 차단(§1.8)
    d5 = evaluate_graduation(CandidateCard("h5", falsifiable=False, **_common))
    assert d5.graduate is False, d5
    print(f"5) falsifiable 게이트 OK: 검정력 미달 graduate={d5.graduate}")

    # 6) ★event_ledger 연동: CANDIDATE_PROPOSED→candidate, RATIFIED→ratified(adopted) as-of projection
    from core.data.event_ledger import make_event, reduce_events
    evs = [
        make_event("ASSUMPTION_CREATED", tt="2026-01-01", dt="2026-01-01", vt="2026-01-01", seq=0,
                   assumption_id="h1", payload={"version": 1}),
        make_event("CANDIDATE_PROPOSED", tt="2026-02-01", dt="2026-02-01", vt="2026-02-01", seq=1,
                   assumption_id="h1", payload={}),
    ]
    ratify = make_ratify_events([evaluate_graduation(CandidateCard("h1", **_common))],
                                tt="2026-04-01", seq_start=2)
    assert len(ratify) == 1, ratify
    st_cand = reduce_events(evs, tt_cut="2026-03-01")
    st_grad = reduce_events(evs + ratify, tt_cut="2026-05-01")
    assert st_cand.assumption_status("h1") == "candidate", st_cand.assumption_status("h1")
    assert st_grad.assumption_status("h1") == "ratified", st_grad.assumption_status("h1")
    print(f"6) event_ledger 연동 OK: candidate(03-01)→ratified(05-01) as-of projection")

    # 7) ★opt-in off byte-identical: RATIFIED/CANDIDATE 미emit → status 변화 0(기존 active 유지)
    base = [make_event("ASSUMPTION_CREATED", tt="2026-01-01", dt="2026-01-01", vt="2026-01-01",
                       seq=0, assumption_id="h9", payload={"version": 1})]
    st_off = reduce_events(base)
    assert st_off.assumption_status("h9") == "active", st_off.assumption_status("h9")
    print(f"7) off byte-identical OK: graduation event 미발생 → active 유지(무회귀)")

    print("\ngraduation self-test PASS (5-AND 재사용 + 자가승격 차단 + 사이클경계 idempotent "
          "+ falsifiable 게이트 + event_ledger candidate→ratified projection + off byte-identical)")
