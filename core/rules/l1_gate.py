"""core/rules/l1_gate.py — L1 결정론 veto floor + archetype dispatch (S5, C축 핵심).

3층 런타임의 L1 = **불가침 결정론 게이트**. rule(S1)은 L1 허용공간 안에서 soft 의견만.
  우선순위: 하드리스크 한도 > **L1 veto floor** > rule signal > default.
  rule 은 사이징·리스크 못 건드린다. L1 floor 를 못 넘는다.

archetype dispatch (계약 #3, claude R4): "싸다"의 의미가 archetype 마다 다르다.
- cyclical      : cheapness_z(잔차) 우선. percentile_overfit_risk → raw 분위는 경고만.
- event_driven  : 멀티플 percentile 무의미 → cheapness_z floor 를 적용하지 않음(neutral 기본,
                  rule 의 event catalyst 신호에 위임). 멀티플로 싸다 판정 금지.
- spread_driven : cheapness_z 적용하되 신용사이클 trap_guard 비중↑(rule).
- asset_stable  : cheapness_z 적용(금리 trap 은 rule).
- compounder    : cheapness_sign="expensive_trap" → 저멀티플(cheapness_z 음수)=함정.
                  floor 부호 반전 — 너무 싸 보이면 오히려 veto.

L1 결정론 floor:
- cheapness_z 가 z_floor 보다 충분히 음수(=구조모델 대비 싸다)여야 진입 허용 후보.
- z_ceiling 보다 높으면(=비쌈) hard veto (살 결정론적 근거 없음).
- NaN(미관측) → abstain (정보 없음, 판단 보류).
- value_trap_guard veto(rule) > 앙상블 > L1 floor 통과여부 (R8: trap 최우선).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from core.structure import archetype as arch
from core.rules.signal import Signal, rule_resolver, EffectiveRule
from core.pit.as_of import cheapness_z_safe, AsOfLike


@dataclass
class L1Config:
    z_floor: float = -0.5      # 이보다 음수여야 "싸다" 후보 (구조모델 대비)
    z_ceiling: float = 1.0     # 이보다 크면 비쌈 → hard veto
    quorum: int = 4


@dataclass
class Verdict:
    firm: str
    sector: str
    archetype: str
    cheapness_z: float
    floor: str                 # "pass" | "veto" | "abstain" | "na"
    rule_verdict: str          # cheap/veto/abstain/neutral (S1)
    final: str = "neutral"     # allow_cheap | veto | abstain | neutral
    deciding_rule_id: Optional[str] = None
    reasons: list[str] = field(default_factory=list)


def _l1_floor(z: float, expensive_trap: bool, cfg: L1Config) -> tuple[str, str]:
    """결정론 floor 판정 → (floor, reason). NaN=abstain."""
    if z is None or (isinstance(z, float) and np.isnan(z)):
        return "abstain", "cheapness_z 미관측 → 판단 보류"
    if expensive_trap:
        # compounder: 저멀티플(z 음수)이 함정. 너무 싸 보이면 veto.
        if z <= cfg.z_floor:
            return "veto", f"expensive_trap: z={z:.2f} 과도하게 저평가=함정"
        return "pass", f"expensive_trap: z={z:.2f} 정상 범위"
    # 일반: 충분히 음수여야 pass, 비싸면 veto
    if z >= cfg.z_ceiling:
        return "veto", f"비쌈: z={z:.2f} ≥ ceiling {cfg.z_ceiling}"
    if z <= cfg.z_floor:
        return "pass", f"저평가 후보: z={z:.2f} ≤ floor {cfg.z_floor}"
    return "abstain", f"중립대: floor<z={z:.2f}<ceiling"


def l1_verdict(
    firm: str,
    sector: str,
    date_: AsOfLike,
    as_of: AsOfLike,
    model,
    features: dict,
    signals: list[Signal],
    cards: Optional[dict] = None,
    cfg: Optional[L1Config] = None,
) -> Verdict:
    """L1 결정론 floor + archetype dispatch + rule soft → 최종 verdict.

    우선순위: rule trap veto > L1 floor veto > (event_driven 특례) > rule cheap > floor/neutral.
    """
    cfg = cfg or L1Config()
    archetype = arch.archetype_for_sector(sector)
    card = (cards or {}).get(archetype)
    expensive_trap = bool(card and getattr(card, "cheapness_sign", "low_multiple") == "expensive_trap")

    z = cheapness_z_safe(model, firm, sector, date_, as_of)   # S0 resolver 경유(미래거부)
    er: EffectiveRule = rule_resolver(sector, date_, as_of, features, signals, cards=cards, quorum=cfg.quorum)

    v = Verdict(firm=firm, sector=sector, archetype=archetype, cheapness_z=float(z),
                floor="na", rule_verdict=er.verdict, deciding_rule_id=er.deciding_rule_id)

    # 1) rule trap veto = 최우선 (R8: value_trap_guard > 앙상블 > L1)
    if er.verdict == "veto":
        v.floor, v.final = "veto", "veto"
        v.reasons.append(f"rule trap veto (deciding={er.deciding_rule_id})")
        return v

    # 2) event_driven 특례: 멀티플 percentile 무의미 → cheapness_z floor 미적용
    if archetype == "event_driven":
        v.floor = "na"
        v.final = "allow_cheap" if er.verdict == "cheap" else ("abstain" if er.verdict == "abstain" else "neutral")
        v.reasons.append("event_driven: cheapness_z floor 미적용, rule(이벤트 catalyst)에 위임")
        return v

    # 3) L1 결정론 floor
    floor, reason = _l1_floor(z, expensive_trap, cfg)
    v.floor = floor
    v.reasons.append(f"L1 floor: {reason}")
    if floor == "veto":
        v.final = "veto"
        return v
    if floor == "abstain":
        v.final = "abstain"
        return v

    # 4) floor pass → rule soft 가 허용공간 안에서 의견
    if er.verdict == "cheap":
        v.final = "allow_cheap"
        v.reasons.append(f"floor pass + rule cheap (score={er.score:.2f})")
    elif er.verdict == "abstain":
        v.final = "abstain"
    else:
        v.final = "neutral"
        v.reasons.append("floor pass 이나 rule quorum 미달 → 근거 부족")
    return v


if __name__ == "__main__":
    import pandas as pd
    from core.structure.panel_schema import make_semiconductor_fixture
    from core.structure.structure_model import StructureModel
    from core.rules.signal import make_cyclical_signal_set

    NOW = pd.Timestamp("2026-05-29")
    panel = make_semiconductor_fixture()
    model = StructureModel()
    model.fit(panel, pd.Timestamp("2022-01-01"))
    sigs = make_cyclical_signal_set()
    cards = {
        "cyclical": arch.CyclicalCard(primary_metric="ev_ebitda", percentile_overfit_risk=True),
        "compounder": arch.CompounderCard(primary_metric="roic_durability"),
        "event_driven": arch.EventDrivenCard(primary_metric="ps"),
    }
    cfg = L1Config()

    # 헬퍼: 강제 z 주입용 더미 모델
    class DummyModel:
        def __init__(self, z): self._z = z
        def cheapness_z(self, firm, sector, date, as_of): return self._z

    # 1) cyclical 저평가 + cheap rule → allow_cheap
    feats_cheap = {"cheapness_z": -1.8, "pb": 0.8, "ev_ebitda": 4.0, "book_to_bill": 1.2, "inventory_qoq": -0.1, "capex_to_rev": 0.1}
    v = l1_verdict("SEMI001", "semiconductor", "2021-09-30", "2022-01-01", DummyModel(-1.8), feats_cheap, sigs, cards, cfg)
    assert v.final == "allow_cheap", v
    print(f"1) cyclical 저평가+cheap: final={v.final} floor={v.floor} z={v.cheapness_z}")

    # 2) cyclical trap(capex 정점) → rule veto 최우선
    feats_trap = dict(feats_cheap, capex_to_rev=0.4)
    v = l1_verdict("SEMI002", "semiconductor", "2021-09-30", "2022-01-01", DummyModel(-1.8), feats_trap, sigs, cards, cfg)
    assert v.final == "veto", v
    print(f"2) cyclical trap: final={v.final} (rule trap veto 최우선)")

    # 3) 비싼 종목(z=+1.5) → L1 floor veto
    v = l1_verdict("SEMI003", "semiconductor", "2021-09-30", "2022-01-01", DummyModel(1.5), dict(feats_cheap, cheapness_z=1.5), sigs, cards, cfg)
    assert v.final == "veto" and v.floor == "veto", v
    print(f"3) 비쌈 z=1.5: final={v.final} floor={v.floor} ({v.reasons[-1]})")

    # 4) compounder 저멀티플(z=-1.8) → expensive_trap floor veto
    comp_sigs = [Signal(id="cmp_pe", version="v1", archetype="compounder", feature="pe", op="lt", threshold=15.0, kind="cheap")]
    v = l1_verdict("CMP001", "software_compounder", "2021-09-30", "2022-01-01", DummyModel(-1.8), {"pe": 10.0}, comp_sigs, cards, cfg)
    assert v.final == "veto", v
    print(f"4) compounder 과도저평가: final={v.final} floor={v.floor} ({v.reasons[0]})")

    # 5) event_driven → cheapness_z floor 미적용 (비싸도 veto 아님, rule 위임)
    ev_sigs = [Signal(id="ev_cat", version="v1", archetype="event_driven", feature="catalyst", op="ge", threshold=1.0, kind="cheap")]
    v = l1_verdict("BIO001", "biotech", "2021-09-30", "2022-01-01", DummyModel(2.0), {"catalyst": 1.0}, ev_sigs, cards, cfg)
    assert v.floor == "na" and v.final in ("allow_cheap", "neutral"), v
    print(f"5) event_driven z=2.0(비쌈): floor={v.floor} final={v.final} (멀티플 floor 미적용)")

    # 6) 중립대 z=-0.1 + quorum 미달 → abstain/neutral
    v = l1_verdict("SEMI004", "semiconductor", "2021-09-30", "2022-01-01", DummyModel(-0.1), dict(feats_cheap, cheapness_z=-0.1, pb=9, ev_ebitda=99, book_to_bill=0.1, inventory_qoq=9), sigs, cards, cfg)
    assert v.final in ("abstain", "neutral"), v
    print(f"6) 중립대 z=-0.1: floor={v.floor} final={v.final}")

    print("S5 l1_gate self-test PASS")
