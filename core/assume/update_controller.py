"""core/assume/update_controller.py — adopt/retract 비대칭 gate (CL-1·3, 축E).

★claude R1 핵심 정정: 채택(adopt)과 기각(retract)에 같은 AND-gate 쓰면 치명적 —
falsification breach 된(증명상 틀린) 가정이 dwell/K 채울 때까지 live 노출된다. 분리:
 - RETRACT = hard-falsifier disjunctive(fast): 강한 반증 1개로 즉시 retire → dag.invalidate(hard).
   dwell/K 안 기다림. live 노출 차단이 목적.
 - base-layer(regime/지표의미) = 자동변경 금지 → human_review(BaseLayerCutover shadow/canary).
 - ADOPT = conjunctive 5조건 AND(slow): 정의 S→S' 전환은 dwell+K-window+same-regime+effect+fdr
   전부 충족해야 transition(노이즈 추격 차단). hysteresis_and_gate 위임.

순서가 안전의 핵심: retract 먼저(틀린 가정 즉시 제거) → base 사람비준 → adopt(느린 정의전환).
측정 incident(validator skip)는 변경 보류(keep) — 측정깨짐≠정의틀림.

결정 X — UpdateAction 산출만. 집행(청산)은 orphan_guard, 사람비준은 HumanApprovalGate(외부).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from core.assume.card_contract import AssumptionCardLike
from core.assume.registry import _as_date
from core.structure.assumption_stats import AndGateResult, hysteresis_and_gate

# RETRACT 판별 임계. ★e_value 는 안 씀 — 엔진 e_value 는 p-floor(1e-9)에서 saturate(~1.6e4)라
# 어떤 유의 break 든 동일값 → 판별력 0. kill(retract) vs 재보정(transition) 구분은 (1) 카드 자체
# falsification_metric breach(hard_falsifier, 호출자 평가) (2) 붕괴 수준 effect(재보정 불가)로.
RETRACT_EFFECT_HARD = 3.0   # Cohen's d ≥ 3.0 = 관계 붕괴(재보정 불가). adopt 0.5 의 6배.
                            # mild~med shift(d 1~2)=정의전환(transition) / 붕괴(d≥3)=kill(retract).


class UpdateAction(str, Enum):
    KEEP = "keep"
    RETIRE = "retire"               # hard-retract (falsifier)
    TRANSITION = "transition"       # 정의 S→S' (adopt)
    HUMAN_REVIEW = "human_review"   # base-layer 사람비준


@dataclass
class UpdateDecision:
    action: UpdateAction
    reason: str                          # 감사 가능 "변경 사유서"
    gate: Optional[AndGateResult] = None  # adopt gate 결과 (왜 미승격 = cost_to_flip 노출)
    new_card: Optional[AssumptionCardLike] = None   # transition 시 새 버전


def retract_now(verdict, *, hard_falsifier: bool = False, effect_size: float = 0.0,
                effect_hard: float = RETRACT_EFFECT_HARD) -> bool:
    """hard-falsifier disjunctive: 깨짐(holds=False) + (카드 kill조건 breach OR 붕괴 effect).

    hard_falsifier = 호출자가 카드 falsification_metric(자체 kill 조건) breach 를 평가해 주입.
    그 외엔 adopt 보다 엄격한 effect_hard(붕괴=재보정 불가)만 retract. 미만 깸은 adopt gate
    (정의전환 후보)로. incident(holds_now=None)·성립(True)은 retract 대상 아님.
    """
    if verdict.holds_now is not False:
        return False
    if hard_falsifier:                                   # 카드 자체 kill 조건 breach = 즉시
        return True
    sig = verdict.fdr_significant or bool(verdict.eprocess_significant)
    return sig and float(effect_size) >= effect_hard     # 붕괴 수준 = 재보정 불가 → kill


def _bump_version(v: str) -> str:
    s = str(v)
    if s.startswith("v") and s[1:].isdigit():
        return f"v{int(s[1:]) + 1}"
    return f"{s}.1"


def _copy_card(card: AssumptionCardLike, update: dict) -> AssumptionCardLike:
    if hasattr(card, "model_copy"):                 # pydantic v2 (BaseAssumptionFields frozen)
        return card.model_copy(update=update)
    if dataclasses.is_dataclass(card):
        return dataclasses.replace(card, **update)
    raise TypeError(f"카드 복제 불가: {type(card)!r}")


def transition_card(card: AssumptionCardLike, *, as_of=None, **overrides) -> AssumptionCardLike:
    """정의 S→S' = version bump + valid_from 갱신. 새 statement 는 overrides 로 학습층이 주입."""
    update: dict = {"version": _bump_version(card.version)}
    if as_of is not None:
        update["valid_from"] = _as_date(as_of)
    update.update(overrides)
    return _copy_card(card, update)


class UpdateController:
    """ValidationVerdict → UpdateAction. retract(fast) → base review → adopt(slow) 순."""

    def __init__(self, registry, validator, dag, *, adopt_gate=hysteresis_and_gate):
        self.registry = registry
        self.validator = validator          # 재유도/재검증용(step 은 verdict 직접 소비)
        self.dag = dag
        self.adopt_gate = adopt_gate

    def step(self, card: AssumptionCardLike, verdict, *,
             effect_size: float = 0.0, dwell_ok: bool = False, k_window_persist: int = 0,
             same_regime: bool = True, hard_falsifier: bool = False,
             as_of=None, epoch: int = 0) -> UpdateDecision:
        """card + verdict → UpdateDecision. effect/dwell/k_window/same_regime/hard_falsifier = 호출자 상태."""
        # 0) 측정 incident → 변경 보류 (측정깨짐 ≠ 정의틀림)
        if (verdict.evidence or {}).get("incident"):
            return UpdateDecision(UpdateAction.KEEP, "측정 incident → 변경 보류(가정틀림 아님)")

        # 1) ★RETRACT (fast, disjunctive) — 먼저. hard falsifier = 즉시 retire(live 노출 차단)
        if retract_now(verdict, hard_falsifier=hard_falsifier, effect_size=effect_size):
            self.dag.invalidate(card.id, epoch=epoch, as_of=as_of, mode="hard")
            return UpdateDecision(UpdateAction.RETIRE,
                                  "hard falsifier breach → 즉시 retract(dwell/K 미대기, live 차단)")

        # 2) base-layer = 사람비준 (자동변경 금지)
        if getattr(card, "is_base_layer", False):
            return UpdateDecision(UpdateAction.HUMAN_REVIEW,
                                  "base-layer(regime/지표의미) = 사람비준(BaseLayerCutover shadow/canary)")

        # 3) ADOPT (slow, conjunctive 5조건 AND) — 정의 S→S' 전환
        gate = self.adopt_gate(
            fdr_significant=verdict.fdr_significant, effect_size=effect_size,
            dwell_ok=dwell_ok, k_window_persist=k_window_persist, same_regime=same_regime)
        if gate.promote:
            new = transition_card(card, as_of=as_of)
            self.registry.transition(new)
            self.dag.invalidate(card.id, epoch=epoch, as_of=as_of, mode="soft")
            return UpdateDecision(UpdateAction.TRANSITION, gate.reason, gate=gate, new_card=new)
        return UpdateDecision(UpdateAction.KEEP, gate.reason, gate=gate)


if __name__ == "__main__":
    from core.assume.registry import AssumptionRegistry
    from core.assume.dag import AssumptionDAG
    from core.assume.card_contract import BaseAssumptionFields
    from core.structure.assumption_validation_engine import ValidationVerdict

    def _card(id, base=False):
        return BaseAssumptionFields(
            id=id, version="v1", kind="parametric", scope="sector", domain="equity",
            statement=f"{id} 정의", falsification_metric=f"{id} cusum", is_base_layer=base)

    def _verdict(holds, fdr, e_value=0.0, eproc=None, incident=False):
        ev = {"incident": True} if incident else {"e_value": e_value}
        return ValidationVerdict(
            assumption_id="x", domain="equity", kind="parametric",
            holds_now=holds, confidence_now=0.7, p_value=0.01, alpha_t=0.05,
            fdr_significant=fdr, evidence=ev, eprocess_significant=eproc)

    def _fresh():
        reg = AssumptionRegistry()
        dag = AssumptionDAG(reg)
        return reg, dag, UpdateController(reg, validator=None, dag=dag)

    # 1) ★RETRACT: 붕괴 효과(d=3.5≥3.0) → 즉시 retire + dag hard invalidate (dwell 미대기)
    reg, dag, uc = _fresh(); reg.register(_card("equity.per_floor"))
    d1 = uc.step(_card("equity.per_floor"), _verdict(False, True),
                 effect_size=3.5, dwell_ok=False, k_window_persist=0, as_of="2026-05-01", epoch=1)
    print(f"1) RETRACT: action={d1.action.value} reason={d1.reason[:30]}")
    assert d1.action == UpdateAction.RETIRE

    # 2) ★TRANSITION: 중간 효과(0.6<3.0) → retract X → adopt 5조건 AND → 정의 S→S'(v2)
    reg, dag, uc = _fresh(); reg.register(_card("equity.per_floor"))
    d2 = uc.step(_card("equity.per_floor"), _verdict(False, True),
                 effect_size=0.6, dwell_ok=True, k_window_persist=2, same_regime=True,
                 as_of="2026-05-01", epoch=1)
    print(f"2) TRANSITION: action={d2.action.value} new_ver={d2.new_card.version if d2.new_card else None}")
    assert d2.action == UpdateAction.TRANSITION and d2.new_card.version == "v2"
    assert reg.get_version("equity.per_floor", "v2") is not None, "전환 카드 registry 등록"
    assert dag.is_stale("equity.per_floor") is False  # 자기 자신은 stale 아님(의존만)

    # 3) base-layer: 중간 깸 → retract X → human_review (자동변경 금지)
    reg, dag, uc = _fresh(); reg.register(_card("macro.regime_def", base=True))
    d3 = uc.step(_card("macro.regime_def", base=True), _verdict(False, True),
                 effect_size=0.6, dwell_ok=True, k_window_persist=2, as_of="2026-05-01")
    print(f"3) base-layer: action={d3.action.value}")
    assert d3.action == UpdateAction.HUMAN_REVIEW

    # 4) KEEP: 효과 약함(0.3<0.5) → retract X, adopt effect_material 실패 → keep + 사유서
    reg, dag, uc = _fresh(); reg.register(_card("equity.per_floor"))
    d4 = uc.step(_card("equity.per_floor"), _verdict(False, True),
                 effect_size=0.3, dwell_ok=True, k_window_persist=2, as_of="2026-05-01")
    print(f"4) KEEP: action={d4.action.value} failed={[k for k,v in d4.gate.conditions.items() if not v]}")
    assert d4.action == UpdateAction.KEEP and d4.gate.conditions["effect_material"] is False

    # 5) 측정 incident → KEEP (가정틀림 아님)
    reg, dag, uc = _fresh(); reg.register(_card("equity.per_floor"))
    d5 = uc.step(_card("equity.per_floor"), _verdict(None, False, incident=True),
                 effect_size=5.0, dwell_ok=True, k_window_persist=5)
    print(f"5) incident: action={d5.action.value} (붕괴효과여도 변경보류)")
    assert d5.action == UpdateAction.KEEP

    # 6) hard_falsifier(카드 kill조건 breach) → 효과 작아도 RETRACT
    reg, dag, uc = _fresh(); reg.register(_card("equity.per_floor"))
    d6 = uc.step(_card("equity.per_floor"), _verdict(False, True),
                 effect_size=0.2, hard_falsifier=True, as_of="2026-05-01", epoch=1)
    print(f"6) hard_falsifier RETRACT: action={d6.action.value}")
    assert d6.action == UpdateAction.RETIRE

    print("CL-1·3 update_controller self-test PASS "
          "(RETRACT 붕괴 / TRANSITION adopt / base human_review / KEEP 사유서 / incident 보류 / hard_falsifier retract)")
