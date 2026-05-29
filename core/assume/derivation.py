"""core/assume/derivation.py — 가정 → 파라미터 순수함수 (CL-1·5, 축C, PIT replay seam R10).

가정 카드(정의 S)를 실제 결정에 쓰는 수치 파라미터(value + band)로 변환하는 **버전드 순수함수**.
같은 (card_refs, as_of, regime, sector) → 항상 같은 결과 = PIT replay 보장(R10).

핵심 성질:
 - PIT replay: registry.get_version(id, version) 으로 정확 버전 고정 → 과거 결정 frozen 재현.
   과거 DecisionRecord 의 (rule_version, card_refs) 로 재호출 = 그때 값 그대로.
 - scope 조건부(CL-5, gemini: cross 금지·계층적): regime > (regime,sector) > sector > default
   계층으로 sector×period×regime 시변 파라미터. 카드의 scope_params(extra) 우선.
 - 다중카드 합성: baseline × Π(decoupling attenuation) = "baseline UNLESS 보조지표 → 감쇠" 동형
   (거시 역전→침체 UNLESS QE = 주식 저PER UNLESS 공정전환 = 상품 COT극단 UNLESS 공급과잉).
 - band: confidence_to_band(value, min(confidence), base_halfwidth) — 신뢰 낮을수록 넓은 band.

순수 — 부작용 0(registry 읽기만). 결정/사이징은 judge, 변경은 UpdateController.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.assume.registry import _as_date
from core.structure.assumption_stats import confidence_to_band

DEFAULT_BASE_HALFWIDTH = 0.25


@dataclass(frozen=True)
class DerivedParameterSet:
    """버전드 순수 산출. frozen = replay 재현 단위. provenance 로 어느 카드/버전서 왔는지 추적."""
    value: float
    band: tuple[float, float]
    confidence: float
    regime: object
    sector: object
    as_of: object
    provenance: tuple   # ((assumption_id, version, knowable_from), ...)


def _card_value(card, regime, sector) -> float:
    """scope 계층 lookup. scope_params(extra) 우선, 없으면 point/baseline_value/attenuation."""
    sp = getattr(card, "scope_params", None)
    if isinstance(sp, dict):
        for key in ((regime, sector), regime, sector, "default", None):
            if key in sp:
                return float(sp[key])
    for attr in ("point", "baseline_value", "attenuation"):
        v = getattr(card, attr, None)
        if v is not None:
            return float(v)
    raise ValueError(f"카드 {card.id!r} 수치 anchor 부재 (scope_params/point/baseline_value/attenuation)")


def derive(card_refs: list[tuple[str, str]], registry, as_of, *, regime, sector,
           base_halfwidth: float = DEFAULT_BASE_HALFWIDTH) -> DerivedParameterSet:
    """card_refs(=[(id,version),...]) → DerivedParameterSet. 순수·PIT 재현.

    card_refs[0] = baseline, 이후 = decoupling 보조(attenuation 곱). 순서 = 합성 순서(불변).
    """
    cards = []
    for i, v in card_refs:
        c = registry.get_version(i, v)
        if c is None:
            raise KeyError(f"카드 버전 부재: ({i!r},{v!r}) — PIT replay 불가(append-only 보존 위반?)")
        cards.append(c)

    value = 1.0
    confs: list[float] = []
    provenance = []
    for c in cards:
        value *= _card_value(c, regime, sector)
        confs.append(float(getattr(c, "posterior_confidence", 0.5) or 0.5))
        provenance.append((c.id, c.version, _as_date(getattr(c, "valid_from", None))))

    confidence = min(confs) if confs else 0.5
    band = confidence_to_band(value, confidence, base_halfwidth)
    return DerivedParameterSet(
        value=float(value), band=tuple(band), confidence=float(confidence),
        regime=regime, sector=sector, as_of=_as_date(as_of), provenance=tuple(provenance))


if __name__ == "__main__":
    from datetime import date
    from core.assume.registry import AssumptionRegistry
    from core.assume.card_contract import BaseAssumptionFields

    def _card(id, ver="v1", vf=None, point=None, atten=None, scope_params=None,
              conf=0.6, dom="macro", scope="macro"):
        extra = {}
        if point is not None:
            extra["point"] = point
        if atten is not None:
            extra["attenuation"] = atten
        if scope_params is not None:
            extra["scope_params"] = scope_params
        return BaseAssumptionFields(
            id=id, version=ver, kind="structural", scope=scope, domain=dom,
            statement=f"{id} 정의", falsification_metric=f"{id} 반증", valid_from=vf,
            posterior_confidence=conf, **extra)

    reg = AssumptionRegistry()
    # baseline(점추정 18.0, PER floor) + decoupling(공정전환기 attenuation 0.7)
    reg.register(_card("equity.per_floor", point=18.0, conf=0.8, dom="equity", scope="sector"))
    reg.register(_card("equity.fair_transition", atten=0.7, conf=0.6, dom="equity", scope="sector"))

    # 1) 순수성: 같은 입력 두 번 → 완전 동일 (frozen ==)
    refs = [("equity.per_floor", "v1"), ("equity.fair_transition", "v1")]
    d1 = derive(refs, reg, "2026-05-01", regime=0, sector="semi")
    d2 = derive(refs, reg, "2026-05-01", regime=0, sector="semi")
    print(f"1) 순수성: value={d1.value:.3f} band=({d1.band[0]:.2f},{d1.band[1]:.2f}) d1==d2:{d1 == d2}")
    assert d1 == d2 and abs(d1.value - 18.0 * 0.7) < 1e-9, d1.value
    assert d1.confidence == 0.6  # min(0.8, 0.6)

    # 2) ★PIT replay frozen: v2 전환(attenuation 0.4 강화) → v1 ref 는 그대로 0.7 재현
    reg.transition(_card("equity.fair_transition", ver="v2", vf=date(2026, 6, 1),
                         atten=0.4, conf=0.7, dom="equity", scope="sector"))
    d_v1 = derive([("equity.per_floor", "v1"), ("equity.fair_transition", "v1")],
                  reg, "2026-05-01", regime=0, sector="semi")
    d_v2 = derive([("equity.per_floor", "v1"), ("equity.fair_transition", "v2")],
                  reg, "2026-07-01", regime=0, sector="semi")
    print(f"2) PIT replay: v1→{d_v1.value:.2f}(0.7곱) / v2→{d_v2.value:.2f}(0.4곱) — frozen 재현")
    assert abs(d_v1.value - 18.0 * 0.7) < 1e-9 and abs(d_v2.value - 18.0 * 0.4) < 1e-9

    # 3) scope 계층: regime>(regime,sector)>sector>default
    reg.register(_card("equity.z_floor", point=1.0,
                       scope_params={(0, "energy"): 0.5, 0: 0.7, "default": 0.9},
                       dom="equity", scope="sector"))
    vs_es = derive([("equity.z_floor", "v1")], reg, "2026-05-01", regime=0, sector="energy").value
    vs_et = derive([("equity.z_floor", "v1")], reg, "2026-05-01", regime=0, sector="tech").value
    vs_x = derive([("equity.z_floor", "v1")], reg, "2026-05-01", regime=1, sector="x").value
    print(f"3) scope 계층: (0,energy)={vs_es} (0,tech)={vs_et} (1,x)={vs_x}")
    assert vs_es == 0.5 and vs_et == 0.7 and vs_x == 0.9

    # 4) provenance: (id, version, knowable_from) 추적
    print(f"4) provenance: {d_v2.provenance}")
    assert d_v2.provenance == (("equity.per_floor", "v1", None),
                               ("equity.fair_transition", "v2", date(2026, 6, 1)))

    # 5) 버전 부재 → KeyError (PIT replay 불가)
    try:
        derive([("equity.per_floor", "v99")], reg, "2026-05-01", regime=0, sector="semi")
        raise AssertionError("부재 버전이 통과됨")
    except KeyError:
        pass
    print("5) 부재 버전 KeyError OK")

    print("CL-1·5 derivation self-test PASS (순수성 + PIT replay frozen + scope계층 + provenance + 부재거부)")
