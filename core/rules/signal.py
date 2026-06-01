"""core/rules/signal.py — versioned signal + weak-rule 앙상블 + rule_resolver (S1, C/B축).

설계 (findings B6 + claude R4/R8):
- **weak-rule 앙상블**: 5~7개 독립 단일룰, ∑발동 ≥ quorum(기본 4) → trigger.
  monolithic(단일 복합룰)은 데이터 결측 하나로 영원히 미발동(경직). 앙상블=강건+추적 용이.
- **bitemporal**: signal 마다 effective_from(적용 시작)≠knowable_from(알게된 시점).
  백테스트는 knowable_from ≤ as_of (PIT), 의사결정은 effective_from ≤ decision_date.
- **archetype dispatch** (계약 #3): archetype 마다 "싸다"의 의미가 다르다.
  cyclical=저멀티플=싸다 / compounder=저멀티플=함정(cheapness_sign="expensive_trap").
  resolver 가 card.cheapness_sign 으로 cheap signal 의 부호를 정렬한다.
- **veto 우선** (R8): value_trap_guard(=trap signal) 가 발동하면 앙상블 score 와 무관하게 veto.
- **부호충돌 → abstain** (claude R8): cheap 발동과 trap 발동이 둘 다 강하면(둘 다 quorum
  절반 이상) 판단 보류. resolver 가 단정하지 않는다.

⚠️ 이 모듈은 "rule 의 형태와 결합 정책"만 정의한다. predicate 의 실제 임계 τ 적합과
   승격은 S3(promotion_gate), L1 결정론 veto floor 주입은 S5(l1_gate) 에서.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Optional

import pandas as pd
from pydantic import BaseModel, Field

from core.structure import archetype as arch
from core.pit.as_of import resolve_as_of, AsOfLike

Op = Literal["lt", "le", "gt", "ge", "abs_gt"]
SignalKind = Literal["cheap", "trap_guard"]


class Signal(BaseModel):
    """단일 약한 규칙 (versioned, bitemporal). predicate = feature `op` threshold."""
    model_config = {"frozen": True, "extra": "forbid"}

    id: str
    version: str
    archetype: str                       # 이 signal 이 속한 archetype (dispatch 키)
    feature: str                         # 평가할 feature 이름 (예: cheapness_z, book_to_bill)
    op: Op
    threshold: float
    kind: SignalKind = "cheap"           # cheap=싸다 신호 / trap_guard=밸류트랩 veto
    weight: float = 1.0
    effective_from: date = date(1900, 1, 1)
    knowable_from: date = date(1900, 1, 1)

    def fires(self, features: dict) -> bool:
        """feature 값에 predicate 적용. feature 결측(None/NaN)=미발동(강건)."""
        v = features.get(self.feature)
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return False
        t = self.threshold
        if self.op == "lt":
            return v < t
        if self.op == "le":
            return v <= t
        if self.op == "gt":
            return v > t
        if self.op == "ge":
            return v >= t
        if self.op == "abs_gt":
            return abs(v) > t
        return False


@dataclass
class EffectiveRule:
    """resolve 결과 — 발동 signal 집합 + 결합 판정."""
    sector: str
    archetype: str
    fired_cheap: list[str] = field(default_factory=list)
    fired_trap: list[str] = field(default_factory=list)
    score: float = 0.0                   # cheap weight 합 (cheapness_sign 부호 정렬 후)
    verdict: Literal["cheap", "veto", "abstain", "neutral"] = "neutral"
    deciding_rule_id: Optional[str] = None
    quorum: int = 4
    notes: list[str] = field(default_factory=list)


def _bitemporal_filter(signals: list[Signal], decision_date: date, as_of_d: date) -> list[Signal]:
    """PIT: knowable_from ≤ as_of (알 수 있던 것) & effective_from ≤ decision_date (적용 시작)."""
    return [
        s for s in signals
        if s.knowable_from <= as_of_d and s.effective_from <= decision_date
    ]


def rule_resolver(
    sector: str,
    decision_date: AsOfLike,
    as_of: AsOfLike,
    features: dict,
    signals: list[Signal],
    cards: Optional[dict] = None,
    quorum: int = 4,
) -> EffectiveRule:
    """섹터 → archetype dispatch → bitemporal 필터 → 앙상블 평가 → EffectiveRule.

    우선순위: trap veto > 부호충돌 abstain > cheap quorum > neutral.
    """
    a_d = resolve_as_of(as_of).date()
    dec_d = resolve_as_of(decision_date).date()
    archetype = arch.archetype_for_sector(sector)
    card = (cards or {}).get(archetype)

    er = EffectiveRule(sector=sector, archetype=archetype, quorum=quorum)

    # archetype dispatch + bitemporal
    cand = [s for s in signals if s.archetype == archetype]
    cand = _bitemporal_filter(cand, dec_d, a_d)
    if not cand:
        er.notes.append("해당 archetype·시점에 유효 signal 없음")
        return er

    fired = [s for s in cand if s.fires(features)]
    cheap = [s for s in fired if s.kind == "cheap"]
    trap = [s for s in fired if s.kind == "trap_guard"]
    er.fired_cheap = [s.id for s in cheap]
    er.fired_trap = [s.id for s in trap]

    # compounder 등: 저멀티플=함정 → cheap 발동을 trap 쪽으로 재해석
    expensive_trap = bool(card and getattr(card, "cheapness_sign", "low_multiple") == "expensive_trap")
    if expensive_trap and cheap:
        er.notes.append("cheapness_sign=expensive_trap → cheap 발동을 함정 신호로 재해석")
        trap = trap + cheap
        er.fired_trap = [s.id for s in trap]
        cheap = []
        er.fired_cheap = []

    n_cheap = len(cheap)
    n_trap = len(trap)

    # 1) trap veto 우선 (R8: value_trap_guard 하나라도 발동 → 앙상블 무관 veto).
    #    실자산 안전 = 밸류트랩 경고에 보수적. cheap quorum 충족이어도 trap 이면 막는다.
    if n_trap >= 1:
        er.verdict = "veto"
        er.deciding_rule_id = trap[0].id
        er.notes.append(f"trap veto (trap={n_trap}, cheap={n_cheap} 무시)")
        return er

    # 2) (v2 자리) expensive signal(저멀티플=비쌈 방향) 과 cheap 충돌 → abstain.
    #    v1 엔 expensive kind 미도입 → 도달 안 함. 추가 시 여기서 부호충돌 보류.

    # 3) cheap quorum 충족
    er.score = sum(s.weight for s in cheap)
    if n_cheap >= quorum:
        er.verdict = "cheap"
        er.deciding_rule_id = max(cheap, key=lambda s: s.weight).id
        er.notes.append(f"cheap quorum 충족 ({n_cheap}≥{quorum}, score={er.score:.2f})")
    else:
        er.verdict = "neutral"
        er.notes.append(f"quorum 미달 ({n_cheap}<{quorum})")
    return er


# ---------------------------------------------------------------------------
# fixture signal set (self-test / S5·S10 mock 용)
# ---------------------------------------------------------------------------

def make_cyclical_signal_set() -> list[Signal]:
    """반도체(cyclical) 약한 규칙 6종: cheap 5 + trap_guard 1."""
    return [
        Signal(id="cyc_cheapz", version="v1", archetype="cyclical", feature="cheapness_z", op="lt", threshold=-1.0, kind="cheap", weight=2.0),
        Signal(id="cyc_pb", version="v1", archetype="cyclical", feature="pb", op="lt", threshold=1.0, kind="cheap"),
        Signal(id="cyc_evebitda", version="v1", archetype="cyclical", feature="ev_ebitda", op="lt", threshold=5.0, kind="cheap"),
        Signal(id="cyc_b2b", version="v1", archetype="cyclical", feature="book_to_bill", op="gt", threshold=1.0, kind="cheap"),
        Signal(id="cyc_inv", version="v1", archetype="cyclical", feature="inventory_qoq", op="lt", threshold=0.0, kind="cheap"),
        # peak-EPS trap: 멀티플 낮은데 capex 정점 → 함정
        Signal(id="cyc_trap_peak", version="v1", archetype="cyclical", feature="capex_to_rev", op="gt", threshold=0.25, kind="trap_guard"),
    ]


if __name__ == "__main__":
    sigs = make_cyclical_signal_set()
    cards = arch.load_cards_from_config() if False else {
        "cyclical": arch.CyclicalCard(primary_metric="ev_ebitda", percentile_overfit_risk=True),
        "compounder": arch.CompounderCard(primary_metric="roic_durability"),
    }

    # 1) cheap quorum 충족 (5 cheap 발동, trap 미발동)
    feats_cheap = {"cheapness_z": -1.5, "pb": 0.8, "ev_ebitda": 4.0, "book_to_bill": 1.2, "inventory_qoq": -0.1, "capex_to_rev": 0.1}
    er = rule_resolver("semiconductor", "2022-01-01", "2022-06-01", feats_cheap, sigs)
    assert er.verdict == "cheap", er
    assert len(er.fired_cheap) == 5, er.fired_cheap
    print(f"1) cheap quorum: verdict={er.verdict} score={er.score} fired={er.fired_cheap}")

    # 2) trap veto 우선 (cheap 5 발동 + capex 정점 trap 1 → trap 이 이김, R8)
    feats_trap = dict(feats_cheap, capex_to_rev=0.4)
    er = rule_resolver("semiconductor", "2022-01-01", "2022-06-01", feats_trap, sigs)
    assert er.verdict == "veto" and er.fired_trap == ["cyc_trap_peak"], er
    print(f"2) trap veto 우선: verdict={er.verdict} fired_trap={er.fired_trap} (cheap 5개 무시)")

    # 3) quorum 미달 → neutral
    feats_few = {"cheapness_z": -1.5, "pb": 5.0, "ev_ebitda": 99.0, "book_to_bill": 0.5, "inventory_qoq": 1.0, "capex_to_rev": 0.1}
    er = rule_resolver("semiconductor", "2022-01-01", "2022-06-01", feats_few, sigs)
    assert er.verdict == "neutral", er
    print(f"3) quorum 미달: verdict={er.verdict} fired={er.fired_cheap}")

    # 4) bitemporal: knowable_from 미래 signal 제외
    future_sig = [Signal(id="f", version="v1", archetype="cyclical", feature="cheapness_z", op="lt", threshold=0.0, kind="cheap", knowable_from=date(2025, 1, 1))]
    er = rule_resolver("semiconductor", "2022-01-01", "2022-06-01", feats_cheap, future_sig)
    assert er.verdict == "neutral" and not er.fired_cheap, er
    print(f"4) bitemporal 제외: verdict={er.verdict} (미래 knowable_from signal 무시)")

    # 5) compounder: 저멀티플 cheap 발동 → expensive_trap 재해석 → veto
    comp_sigs = [
        Signal(id="cmp_low_pe", version="v1", archetype="compounder", feature="pe", op="lt", threshold=15.0, kind="cheap"),
        Signal(id="cmp_low_pb", version="v1", archetype="compounder", feature="pb", op="lt", threshold=3.0, kind="cheap"),
    ]
    er = rule_resolver("software_compounder", "2022-01-01", "2022-06-01", {"pe": 10.0, "pb": 2.0}, comp_sigs, cards=cards)
    assert er.verdict == "veto", er
    print(f"5) compounder expensive_trap: verdict={er.verdict} notes={er.notes[0]}")

    print("S1 signal/resolver self-test PASS")
