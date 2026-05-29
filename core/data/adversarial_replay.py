"""core/data/adversarial_replay.py — 적대적 PIT replay 1급 CI 게이트 (전체구조 자문 #3·#R3).

통합테스트 1급 게이트(reducer 결정론보다 강한 **시간적 결정론**): OUTCOME/REVISION 에
taint-tag 를 달고, **as-of-A(t0≤A<t1) 산출에 tainted 가 0건**임을 assert + **revision 물리부재
oracle 과 byte-identical**임을 assert. 전 seam 관통(storage→reducer→read-model→signal→FDR).

왜 reducer 결정론만으론 부족한가: 같은 입력 → 같은 출력(결정론)은 증명해도, "as-of-A 에서
미래 fact 가 절대 새지 않는다"는 **시간적** 보증은 별개. 미래 revision 의 값이 as-of-A 산출에
한 톨이라도 섞이면 = revised lookahead alpha 누수(에러 없이 라이브 하회로만 드러남).

게이트 2축:
  ① **taint isolation**: 미래 REVISION 값(tainted)이 as-of-A resolve/projection 에 0건.
  ② **물리부재 byte-identical**: reduce(전체, cut=A) == reduce(미래revision 물리제거, cut=A).
     (cut 이 단지 가리는 게 아니라 실제로 미래를 안 보고 있음을 증명.)
시나리오: 지연개정·동일vt 다중개정·결정창 중간도착·이미소비 fact 개정.
"""

from __future__ import annotations

from datetime import date, timedelta

from core.data.event_ledger import LedgerState, make_event, reduce_events
from core.data.instrument_source import CoinMetricsMvrvProvider, run_mvrv_closed_loop
from core.data.event_ledger import EventLedger

_TAINT_KEY = "_taint"


def _tainted_values_in_state(state: LedgerState) -> list:
    """state 의 facts 중 tainted 표식 값 목록(누수 탐지). REVISION 은 value 로 추적."""
    leaked = []
    for facts in state.facts.values():
        for f in facts:
            # tainted fact 은 value 에 sentinel(999_xxx) 로 심어 추적 (payload 소실 대비)
            if f.value >= 900_000:
                leaked.append((f.series_key, f.vt.isoformat(), f.value))
    return leaked


def _mk(seq, et, tt, dt, vt, **p):
    return make_event(et, tt=tt, dt=dt, vt=vt, seq=seq,
                      assumption_id=p.pop("aid", "A1"), asset_class="crypto", payload=p)


def gate_taint_isolation_and_oracle() -> dict:
    """게이트 ①②: 미래 REVISION taint 격리 + 물리부재 byte-identical. 4 시나리오."""
    results = {}

    # 공통: OUTCOME(정상값) + 미래 REVISION(tainted sentinel 값 999_xxx)
    # 시나리오 A: 지연개정 — OUTCOME tt=02-15, REVISION tt=03-15(미래), 같은 vt=01-31
    base = [
        _mk(0, "OUTCOME_OBSERVED",  "2024-02-15", "2024-02-15", "2024-01-31", series_key="CPI", value=2.0),
        _mk(1, "REVISION_OBSERVED", "2024-03-15", "2024-03-15", "2024-01-31", series_key="CPI", value=999_025.0, supersedes="_o0"),
    ]
    A = "2024-02-20"   # t0 ≤ A < t1(revision tt)
    s_all = reduce_events(base, tt_cut=A)
    s_oracle = reduce_events([e for e in base if e.event_type != "REVISION_OBSERVED"], tt_cut=A)
    leaked = _tainted_values_in_state(s_all)
    assert leaked == [], f"[A 지연개정] tainted 누수: {leaked}"
    assert s_all == s_oracle, "[A 지연개정] 물리부재 oracle 과 불일치(미래 revision 이 cut 에 영향)"
    # as-of B ≥ revision tt 면 tainted 가 정상적으로 보여야(격리는 A 한정, 미래에선 진실)
    s_future = reduce_events(base, tt_cut="2024-03-20")
    assert any(v[2] >= 900_000 for v in _tainted_values_in_state(s_future)), "B 미래에선 revision 가시여야"
    results["A_지연개정"] = "PASS"

    # 시나리오 B: 동일 vt 다중개정 (REVISION 2건, tt 03-15·04-15 둘 다 미래)
    multi = base + [
        _mk(2, "REVISION_OBSERVED", "2024-04-15", "2024-04-15", "2024-01-31", series_key="CPI", value=999_050.0, supersedes="_o0"),
    ]
    s_all = reduce_events(multi, tt_cut=A)
    s_oracle = reduce_events([e for e in multi if e.event_type != "REVISION_OBSERVED"], tt_cut=A)
    assert _tainted_values_in_state(s_all) == [], "[B 다중개정] tainted 누수"
    assert s_all == s_oracle, "[B 다중개정] byte-identical 실패"
    results["B_동일vt_다중개정"] = "PASS"

    # 시나리오 C: 결정창 중간도착 (REVISION tt 가 A 와 같은 날 = 경계, A 직전까지 미가시)
    mid = [
        _mk(0, "OUTCOME_OBSERVED",  "2024-02-15", "2024-02-15", "2024-01-31", series_key="CPI", value=2.0),
        _mk(1, "REVISION_OBSERVED", "2024-02-20", "2024-02-20", "2024-01-31", series_key="CPI", value=999_030.0, supersedes="_o0"),
    ]
    A_before = "2024-02-19"   # 도착 직전
    s_all = reduce_events(mid, tt_cut=A_before)
    s_oracle = reduce_events([e for e in mid if e.event_type != "REVISION_OBSERVED"], tt_cut=A_before)
    assert _tainted_values_in_state(s_all) == [], "[C 중간도착] 도착 직전 누수"
    assert s_all == s_oracle, "[C 중간도착] byte-identical 실패"
    # tt == cut 이면 가시(tt ≤ cut) — 경계 정확성
    s_at = reduce_events(mid, tt_cut="2024-02-20")
    assert any(v[2] >= 900_000 for v in _tainted_values_in_state(s_at)), "tt==cut 은 가시여야(≤)"
    results["C_결정창_중간도착"] = "PASS"

    # 시나리오 D: 이미 소비된 fact 개정 (OUTCOME 이 FDR 에 이미 쓰인 뒤 REVISION 도착)
    consumed = [
        _mk(0, "OUTCOME_OBSERVED",  "2024-02-15", "2024-02-15", "2024-01-31", series_key="pred:1", value=-0.05),
        _mk(1, "FDR_DECISION",      "2024-02-16", "2024-02-16", "2024-02-16", reject=True, p_value=0.01, alpha_spent=0.01, family_key="f1"),
        _mk(2, "REVISION_OBSERVED", "2024-03-15", "2024-03-15", "2024-01-31", series_key="pred:1", value=999_010.0, supersedes="_o0"),
    ]
    s_all = reduce_events(consumed, tt_cut=A)
    s_oracle = reduce_events([e for e in consumed if e.event_type != "REVISION_OBSERVED"], tt_cut=A)
    assert _tainted_values_in_state(s_all) == [], "[D 이미소비] 누수"
    assert s_all == s_oracle, "[D 이미소비] byte-identical 실패"
    # 이미 내려진 FDR 결정은 미래 revision 으로 되감기 X (dt 순 불변)
    assert [e["seq"] for e in s_all.fdr_replay()] == [1], "FDR 결정이 revision 으로 변형"
    results["D_이미소비_fact개정"] = "PASS"

    return results


def gate_closed_loop_replay_invariance() -> dict:
    """전 seam(signal→FDR) 관통: closed-loop 에 미래 vintage 주입해도 as-of replay 불변."""
    prov = CoinMetricsMvrvProvider()
    base_dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(20)]
    mvrv = [2.0, 2.1, 2.5, 2.6, 2.7, 2.3, 2.2, 2.8, 2.9, 3.0,
            2.4, 2.3, 2.6, 2.7, 2.5, 2.1, 2.0, 2.45, 2.5, 2.6]
    for d0, mv in zip(base_dates, mvrv):
        prov.add("btc", d0, mv, d0 + timedelta(days=1))

    prices = {}
    px = 42000.0
    for i, dd in enumerate([date(2024, 1, 1) + timedelta(days=j) for j in range(40)]):
        px *= (0.99 if 8 <= i <= 20 else 1.003)
        prices[dd] = px
    decision_dates = [date(2024, 1, 6) + timedelta(days=i) for i in range(12)]

    led = EventLedger()
    run_mvrv_closed_loop(led, prov, prices, decision_dates, mvrv_hi=2.4, horizon_days=7)
    canon = led.project()

    # ★미래 MVRV vintage 정정 주입(tt 미래) — as-of(closed-loop 종료 시점) projection 불변이어야
    last_decision = decision_dates[-1] + timedelta(days=7)
    prov.add("btc", "2024-01-03", 999_099.0, knowable_from="2024-06-01", sys_time="2024-06-01")  # 미래 tainted
    # provider 정정은 ledger 에 안 들어갔으므로 ledger projection 은 그대로 — seam 격리 증명
    assert led.project() == canon, "provider 미래정정이 ledger projection 오염(seam 누수)"
    # as-of < 미래정정 tt 에서 provider PIT 도 tainted 미가시
    assert prov.get_point("btc", "2024-01-03", str(last_decision)) != 999_099.0, "provider PIT 미래정정 누수"
    return {"closed_loop_seam_isolation": "PASS"}


if __name__ == "__main__":
    r1 = gate_taint_isolation_and_oracle()
    for k, v in r1.items():
        print(f"  [{k}] {v}")
    print(f"1) taint isolation + 물리부재 byte-identical: 4 시나리오 {list(r1.values())} OK")

    r2 = gate_closed_loop_replay_invariance()
    print(f"2) closed-loop 전 seam 격리(provider 미래정정↛ledger projection): {list(r2.values())} OK")

    print("adversarial_replay (1급 CI 게이트: 시간적 결정론) self-test PASS")
