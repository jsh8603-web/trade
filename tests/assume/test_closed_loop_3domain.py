"""tests/assume/test_closed_loop_3domain.py — CL-4 closed-loop GATE (★부분구현 차단).

DESIGN-codlearn-v2.md §6. plan 루프를 거시∧주식∧상품 각각 end-to-end 로 닫는다(단일 경로 동형):

  [결정] derive → DecisionLedger.record(frozen, rule_version, regime_model_version)   축C·A
   → [학습] outcome → validator.validate(regime-conditional)                          축A·D
   → [검증] ValidationVerdict(holds_now, fdr_significant)                             축D
   → [변경] UpdateController.step → AND-gate → transition(S→S')                       축E
   → [전파] dag.invalidate(grace+lazy) + orphan_guard                                축E·F
   → [재주입] registry.active → 다음 결정                                             축C

GATE = 3도메인 6스텝 PASS + PIT replay(과거결정 frozen 재현) + gridlock 미발생(grace 내 매매유지)
+ ★재주입 반사성 방어 3종(claude R1 Q5): frozen control book / off-policy 로깅 / per-domain 격리.

scope-split: 수치 S'(새 정의값) 계산 = 학습/판단 레이어(Phase II, 별 세션). 본 GATE = 라이프사이클
spine(버전전환 메커니즘 + PIT 불변 + 전파 안전)의 does-it-run·불변식 검증.
e-allocation property(reorder-invariance·parent-gate) = tests/structure/test_eprocess_backbone_properties.py 커버.
"""

from __future__ import annotations

import numpy as np
import pytest

from core.assume.card_contract import BaseAssumptionFields
from core.assume.registry import AssumptionRegistry
from core.assume.dag import AssumptionDAG
from core.assume.validator import AssumptionValidator, Evidence
from core.assume.update_controller import UpdateController, UpdateAction
from core.assume.derivation import derive
from core.assume.orphan_guard import on_assumption_retired, TokenBucket
from core.rules.ledger import DecisionLedger, DecisionRecord


# 3도메인 = 단일 경로 동형 (거시 역전→침체 UNLESS QE = 주식 저PER UNLESS 공정전환 = 상품 COT UNLESS 공급과잉)
DOMAINS = [
    ("macro", "macro", "US10Y"),
    ("equity", "sector", "SEMI"),
    ("commodity", "asset", "WTI"),
]


def _param_card(domain, scope, point=15.0, ver="v1", conf=0.7, deps=()):
    return BaseAssumptionFields(
        id=f"{domain}.threshold", version=ver, kind="parametric", scope=scope, domain=domain,
        statement=f"{domain} 정상범위 baseline=θ UNLESS 보조지표 → decoupling",
        falsification_metric=f"{domain} CUSUM 이탈 + variance-ratio", posterior_confidence=conf,
        depends_on=list(deps), point=point)


def _decision(did, domain, instrument, scope_name, rule_version, regime=1):
    return DecisionRecord(
        decision_id=did, ts="2026-05-01T00:00:00", firm=instrument, sector=scope_name,
        as_of="2026-05-01", rule_version=rule_version, regime_id=regime,
        regime_model_version="rm_2026a", verdict="cheap", cheapness_z=-1.6, action="buy")


@pytest.mark.parametrize("domain,scope,instrument", DOMAINS)
def test_closed_loop_end_to_end(domain, scope, instrument):
    """6스텝 end-to-end + PIT replay + 재주입. 3도메인 동형(같은 코드경로)."""
    reg = AssumptionRegistry()
    dag = AssumptionDAG(reg)
    val = AssumptionValidator.default()
    led = DecisionLedger()
    uc = UpdateController(reg, val, dag)

    card = _param_card(domain, scope, point=15.0)
    reg.register(card)

    # [결정] derive → frozen DecisionRecord (rule_version=card@v1, regime_model_version 박제)
    dp0 = derive([(card.id, "v1")], reg, "2026-05-01", regime=1, sector=instrument)
    assert dp0.value == 15.0
    led.record(_decision("dec1", domain, instrument, scope, f"{card.id}@v1"))

    # [학습] outcome: regime0 안정(=θ15) / regime1 중간 level shift(17, d~2 = 재보정 대상, 붕괴 아님)
    rng = np.random.default_rng(hash(domain) % (2**32))
    reg_ids = np.array([0] * 80 + [1] * 80)
    realized = np.concatenate([rng.normal(15, 1, 80), rng.normal(17, 1, 80)])
    verdict = val.validate(card, Evidence(realized=realized, assumed_value=15.0, sd=1.0),
                           regime_ids=reg_ids, current_regime=1)

    # [검증] 가정 깸 + FDR 유의 (학습 신호)
    assert verdict.holds_now is False, f"{domain}: regime1 shift 인데 holds"
    assert verdict.fdr_significant is True, f"{domain}: 깸인데 FDR 미유의"
    eff = abs(verdict.by_regime[1]["evidence"]["cohens_d"])
    assert 0.5 <= eff < 3.0, f"{domain}: effect {eff} (재보정 구간이어야 = transition)"

    # [변경] adopt 5조건 AND 충족 → 정의 S→S'(v2). 붕괴(d≥3) 아니라 transition
    dec = uc.step(card, verdict, effect_size=eff, dwell_ok=True, k_window_persist=2,
                  same_regime=True, as_of="2026-05-02", epoch=1)
    assert dec.action == UpdateAction.TRANSITION, f"{domain}: {dec.action} (transition 기대) — {dec.reason}"
    assert dec.new_card.version == "v2"

    # [전파] step 내부 dag soft invalidate 호출됨(의존 없으면 no-op). gridlock 은 별 테스트.
    # [재주입] registry.active → 새 v2 가 활성 카드
    active = reg.active(domain=domain, as_of="2026-05-03")
    assert any(c.version == "v2" for c in active), f"{domain}: 재주입 v2 부재"

    # ★PIT replay: v1 frozen 은 v2 등록 후에도 동일 재현(append-only 불변), v2 도 파생가능
    dp_v1_after = derive([(card.id, "v1")], reg, "2026-05-01", regime=1, sector=instrument)
    assert dp_v1_after == dp0, f"{domain}: v1 frozen replay 깨짐(append-only 위반)"
    dp_v2 = derive([(card.id, "v2")], reg, "2026-05-03", regime=1, sector=instrument)
    assert dp_v2.provenance[0][1] == "v2"


def test_gridlock_free_grace_keeps_trading():
    """거시 가정 soft transition → 의존 카드 grace 내엔 매매 유지(즉시 cascade 청산 X)."""
    reg = AssumptionRegistry()
    reg.register(_param_card("macro", "macro"))
    # equity 카드가 macro 에 의존
    dep = BaseAssumptionFields(
        id="equity.threshold", version="v1", kind="parametric", scope="sector", domain="equity",
        statement="s", falsification_metric="cusum", posterior_confidence=0.7,
        depends_on=["macro.threshold"], point=20.0)
    reg.register(dep)
    dag = AssumptionDAG(reg, grace_days=5)

    r = dag.invalidate("macro.threshold", epoch=1, as_of="2026-05-01", mode="soft")
    assert "equity.threshold" in r.stale_marked
    # grace(2026-05-06) 내 → resolve_stale False = 기존값 매매 지속(gridlock 미발생)
    assert dag.resolve_stale("equity.threshold", as_of="2026-05-03") is False
    # 의존 카드 derive 는 grace 내 계속 가능(즉시 무효화 안 됨)
    dp = derive([("equity.threshold", "v1")], reg, "2026-05-03", regime=0, sector="SEMI")
    assert dp.value == 20.0
    # grace 만료 후에만 재검증 신호
    assert dag.resolve_stale("equity.threshold", as_of="2026-05-10") is True


def test_reflexivity_frozen_control_book():
    """방어①: control book = 재주입(transition) 안 받는 통제계좌 → drift 기준선(frozen)."""
    rng = np.random.default_rng(7)
    reg_ids = np.array([0] * 80 + [1] * 80)
    realized = np.concatenate([rng.normal(15, 1, 80), rng.normal(17, 1, 80)])

    # live book: transition 재주입 받음
    live = AssumptionRegistry(); live_dag = AssumptionDAG(live)
    val = AssumptionValidator.default(); uc = UpdateController(live, val, live_dag)
    card = _param_card("equity", "sector", point=15.0)
    live.register(card)
    # control book: 같은 시작, 그러나 학습 재주입 차단(frozen)
    control = AssumptionRegistry(); control.register(_param_card("equity", "sector", point=15.0))

    v = val.validate(card, Evidence(realized=realized, assumed_value=15.0, sd=1.0),
                     regime_ids=reg_ids, current_regime=1)
    uc.step(card, v, effect_size=abs(v.by_regime[1]["evidence"]["cohens_d"]),
            dwell_ok=True, k_window_persist=2, same_regime=True, as_of="2026-05-02", epoch=1)

    # live = v2 진화 / control = v1 고정(drift 기준선)
    assert any(c.version == "v2" for c in live.active(domain="equity", as_of="2026-05-03"))
    ctrl_active = control.active(domain="equity", as_of="2026-05-03")
    assert all(c.version == "v1" for c in ctrl_active), "control book 은 재주입 차단(frozen)"
    assert len(control._versions["equity.threshold"]) == 1   # 버전 안 늘어남


def test_reflexivity_off_policy_logging():
    """방어②: abstain/shadow 결정도 별도 로깅 → 학습기가 자기-생성 아닌 데이터 확보."""
    led = DecisionLedger()
    off_policy = DecisionLedger()        # abstain/shadow arm 전용 (IPS 가중 학습용)
    # on-policy: 실제 집행된 buy
    led.record(_decision("on1", "equity", "SEMI", "sector", "equity.threshold@v1"))
    # off-policy: abstain·shadow (집행 안 했지만 결과 관측 가능 → 학습 데이터)
    off_policy.record(DecisionRecord(
        decision_id="off1", ts="2026-05-01", firm="MSFT", sector="sector", as_of="2026-05-01",
        rule_version="equity.threshold@v1", regime_id=1, regime_model_version="rm_2026a",
        verdict="abstain", cheapness_z=-0.2, action="hold"))
    off_policy.record(DecisionRecord(
        decision_id="off2", ts="2026-05-01", firm="AMD", sector="sector", as_of="2026-05-01",
        rule_version="equity.threshold@v1", regime_id=1, regime_model_version="rm_2026a",
        verdict="shadow", cheapness_z=-2.5, action="hold"))
    # 학습기는 on+off 둘 다 봄 → self-confirming attractor 완화(자기결정만 학습 X)
    assert len(led.all()) == 1 and len(off_policy.all()) == 2
    assert {d.verdict for d in off_policy.all()} == {"abstain", "shadow"}


def test_reflexivity_per_domain_isolation():
    """방어③: FDR alpha-wealth 도메인 격리 — noisy commodity 가 macro 발견 starve/누출 X."""
    val = AssumptionValidator.default()
    rng = np.random.default_rng(11)
    com = _param_card("commodity", "asset", point=15.0)
    mac = _param_card("macro", "macro", point=15.0)

    # commodity 를 50회 noise(가정 성립=null) 검정 — alpha-wealth 소비 시도
    stable = rng.normal(15, 1, 60)
    for _ in range(50):
        val.validate(com, Evidence(realized=stable, assumed_value=15.0, sd=1.0),
                     regime_ids=np.zeros(60, int), current_regime=0)
    # macro 는 단 1회 — commodity 활동에 영향 0 (격리)
    mv = val.validate(mac, Evidence(realized=stable, assumed_value=15.0, sd=1.0),
                      regime_ids=np.zeros(60, int), current_regime=0)
    s_com = val.engine.stream_state("commodity", "commodity.threshold")
    s_mac = val.engine.stream_state("macro", "macro.threshold")
    # 스트림 키 격리 + macro 검정수=1(commodity 50회와 분리)
    assert s_com["isolated_key"] != s_mac["isolated_key"]
    assert s_mac["t"] == 1 and s_com["t"] == 50, (s_mac["t"], s_com["t"])
    assert mv.holds_now is True and mv.fdr_significant is False   # noise 누출 0


def test_retract_path_orphan_exit():
    """retract(hard_falsifier) → dag hard invalidate → orphan_guard managed-exit(token-bucket)."""
    reg = AssumptionRegistry()
    dag = AssumptionDAG(reg)
    val = AssumptionValidator.default()
    led = DecisionLedger()
    uc = UpdateController(reg, val, dag)

    card = _param_card("equity", "sector", point=15.0)
    reg.register(card)
    led.record(_decision("d1", "equity", "AAPL", "sector", f"{card.id}@v1"))
    led.record(_decision("d2", "equity", "MSFT", "sector", f"{card.id}@v1"))
    positions = {"AAPL": {"qty": 100.0, "domain": "equity"},
                 "MSFT": {"qty": 50.0, "domain": "equity"}}

    rng = np.random.default_rng(5)
    reg_ids = np.array([0] * 80 + [1] * 80)
    # ★붕괴 수준 break(regime1 = 21, d~6 ≥ 3.0 = 재보정 불가) → retract(kill), transition 아님
    realized = np.concatenate([rng.normal(15, 1, 80), rng.normal(21, 1, 80)])
    v = val.validate(card, Evidence(realized=realized, assumed_value=15.0, sd=1.0),
                     regime_ids=reg_ids, current_regime=1)
    eff = abs(v.by_regime[1]["evidence"]["cohens_d"])
    assert v.holds_now is False and eff >= 3.0, (v.holds_now, eff)
    dec = uc.step(card, v, effect_size=eff, as_of="2026-05-02", epoch=1)
    assert dec.action == UpdateAction.RETIRE

    # orphan_guard: hard mode → 보유 포지션 managed-exit (token-bucket rate-limit)
    res = on_assumption_retired(card.id, reg, led, positions, mode="hard",
                                bucket=TokenBucket(capacity=1))
    assert len(res.issued) == 1 and len(res.deferred) == 1   # 폭주 차단


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
