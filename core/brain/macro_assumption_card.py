"""core/brain/macro_assumption_card.py — BB-1: 거시 decoupling → 버전드 가정 카드.

DESIGN-button-v2.md §2 / §10.1. indicator_event_correlation.ANOMALY_CASES (static dataclass,
version·falsification 無) → falsification_metric 있는 **버전드 MacroAssumptionCard** 승격.

자문 수렴(R1/R5): decoupling 의 falsification = "attenuation 이 실제로 regime 오판을 줄였나"를
prequential ΔBrier + 잔차 CUSUM + mechanism-validation(결과독립) 로 채점 (소표본 precision/recall 폐기).

경계: 카드 = btn-brain(T2) 도메인. AssumptionCardLike(card_contract) 만족 → T3 Registry 통합 보관.
원장 emit/검증은 BB-2/BB-4. 본 모듈은 카드 정의 + AnomalyCase↔Card 어댑터 + 신규 case API.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from core.assume.card_contract import BaseAssumptionFields, assert_falsifiable
from core.brain.indicator_event_correlation import (
    ANOMALY_CASES,
    AnomalyCase,
    Dir,
    MacroEvent,
    SupplementarySignal,
)


# ---------------------------------------------------------------------------
# 케이스별 falsification_metric (반증 조건 — 자문 R1/R5 채점법)
# ---------------------------------------------------------------------------
# key = AnomalyCase.case_id. 값 = 정량 반증 조건 (prequential ΔBrier / 잔차 CUSUM / mechanism).
FALSIFICATION_BY_CASE: dict[str, str] = {
    "yc_inversion_term_premium": (
        "역전(yc<0) ∧ WALCL>7.5e6 기간의 12M-fwd 침체확률이 baseline 침체율 대비 prequential "
        "ΔBrier>0 (attenuation 이 오판 축소) ∧ |d|>=0.5. 반증=ΔBrier<=0. mechanism: ACM term "
        "premium 추정으로 QE 왜곡 독립 검증(결과독립)."
    ),
    "sahm_supply_shock": (
        "Sahm 트리거 ∧ V/U>1.0 기간의 12M 침체율 < Sahm 단독 트리거 침체율(잔차 CUSUM 미발화). "
        "반증=V/U 높아도 침체율 동일."
    ),
    "m2_inflation_decoupling": (
        "M2 급증 ∧ M2V<1.3 ∧ 초과준비금 급등 시 24M 코어CPI YoY < M2 단독 급증의 인플레"
        "(prequential ΔBrier>0). 반증=velocity 낮아도 인플레 동일."
    ),
    "m2_inflation_fiscal_recoupling": (
        "재정 직접이전(PSAVERT 급등후 급락) 동반 시 코어CPI YoY 상승 baseline 유지(recoupling). "
        "반증=재정이전에도 인플레 미점화. (attenuation=1.0 sensing 카드)"
    ),
    "rate_hike_soft_landing": (
        "500bp+ 인상 ∧ TDSP<11 ∧ R*>1.5 기간 실업률 급등 부재(CUSUM 미발화). "
        "반증=락인/R* 상향에도 실업 폭등."
    ),
    "cpi_truflation_lag": (
        "Truflation-CPI gap<-1%p 시 40~75일 후 공식 CPI 하락(선행 적중 prequential ΔBrier>0). "
        "반증=gap 음이어도 공식 CPI 미하락."
    ),
    "gdp_gdi_divergence": (
        "GDP<0<GDI 기간 NBER 침체 미선언(mechanism: 실질 GDI 정상확장 독립 확인). "
        "반증=GDI 양인데도 침체 선언."
    ),
}

# attenuation==1.0 (sensing 전용, 상관 약화 안 함) 케이스 = recoupling 류.
_SENSING_ONLY = {"m2_inflation_fiscal_recoupling"}


def _sig_to_dict(sig: SupplementarySignal) -> dict:
    return {
        "name": sig.name, "fred_id": sig.fred_id, "threshold": sig.threshold,
        "direction": sig.direction.value, "description": sig.description,
    }


def _dict_to_sig(d: dict) -> SupplementarySignal:
    return SupplementarySignal(
        name=d["name"], fred_id=d.get("fred_id"), threshold=float(d["threshold"]),
        direction=Dir(d["direction"]), description=d.get("description", ""),
    )


# ---------------------------------------------------------------------------
# MacroAssumptionCard — 버전드 거시 가정 카드 (AssumptionCardLike 충족)
# ---------------------------------------------------------------------------
class MacroAssumptionCard(BaseAssumptionFields):
    """거시 decoupling 1 케이스 = 버전드·반증가능 가정 카드.

    BaseAssumptionFields(공유 계약) + 거시 도메인 필드. domain=macro, kind=structural 고정.
    정의 전환(S→S') = version bump + 새 카드 발행(이전 valid_to 마킹은 T3 ledger).
    """
    # 도메인 필드 (extra=allow 라 자유, 명시로 검증)
    event: str                       # MacroEvent.value
    distorted_indicator: str
    expected: str                    # Dir.value
    actual: str                      # Dir.value
    supplementary: list[dict]        # [_sig_to_dict, ...]
    attenuation: float
    historical_episodes: list[str] = []
    sensing_only: bool = False       # attenuation==1.0 (상관 약화 X, sensing)

    def triggered_supplementary_names(self) -> list[str]:
        return [s["name"] for s in self.supplementary]


def anomaly_to_card(
    case: AnomalyCase,
    version: str = "v1",
    valid_from: Optional[date] = None,
    posterior_confidence: float = 0.6,
) -> MacroAssumptionCard:
    """AnomalyCase(static) → 버전드 MacroAssumptionCard. falsification_metric 자동 주입."""
    fm = FALSIFICATION_BY_CASE.get(case.case_id)
    if not fm:
        raise ValueError(
            f"case {case.case_id!r} 의 falsification_metric 미정의 → 카드 승격 불가 "
            "(FALSIFICATION_BY_CASE 에 반증 조건 추가 필요)."
        )
    card = MacroAssumptionCard(
        id=f"macro.{case.case_id}",
        version=version,
        kind="structural", scope="macro", domain="macro",
        statement=f"{case.event.value}: {case.distorted_indicator} baseline={case.expected.value} "
                  f"UNLESS {', '.join(s.name for s in case.supplementary)} trigger → decoupling",
        rationale=case.reason,
        falsification_metric=fm,
        is_base_layer=False,
        valid_from=valid_from,
        posterior_confidence=posterior_confidence,
        depends_on=[],
        event=case.event.value,
        distorted_indicator=case.distorted_indicator,
        expected=case.expected.value,
        actual=case.actual.value,
        supplementary=[_sig_to_dict(s) for s in case.supplementary],
        attenuation=case.attenuation,
        historical_episodes=list(case.historical_episodes),
        sensing_only=(case.case_id in _SENSING_ONLY) or (abs(case.attenuation - 1.0) < 1e-9),
    )
    assert_falsifiable(card)
    return card


def card_to_anomaly(card: MacroAssumptionCard) -> AnomalyCase:
    """MacroAssumptionCard → AnomalyCase (live 주입 — conditional_attenuation 재사용)."""
    return AnomalyCase(
        case_id=card.id.split(".", 1)[-1],
        event=MacroEvent(card.event),
        distorted_indicator=card.distorted_indicator,
        expected=Dir(card.expected),
        actual=Dir(card.actual),
        reason=card.rationale,
        supplementary=[_dict_to_sig(d) for d in card.supplementary],
        attenuation=card.attenuation,
        historical_episodes=list(card.historical_episodes),
    )


def promote_all(version: str = "v1") -> list[MacroAssumptionCard]:
    """6(+1) ANOMALY_CASES 전부 버전드 카드 승격."""
    return [anomaly_to_card(c, version=version) for c in ANOMALY_CASES]


def add_candidate_card(
    *,
    case_id: str,
    event: str,
    distorted_indicator: str,
    expected: str,
    actual: str,
    reason: str,
    supplementary: list[dict],
    attenuation: float,
    falsification_metric: str,
    version: str = "v1.cand",
    episodes: tuple = (),
) -> MacroAssumptionCard:
    """신규 decoupling case → 후보 카드 (BB-1 신규 case 추가 경로).

    falsification_metric 필수(빈 값이면 BaseAssumptionFields 가 거부). candidate version 표기.
    승격(production version)은 검증(BB-4) + 사람 비준(T3) 후.
    """
    card = MacroAssumptionCard(
        id=f"macro.{case_id}",
        version=version,
        kind="structural", scope="macro", domain="macro",
        statement=f"{event}: {distorted_indicator} baseline={expected} UNLESS "
                  f"{', '.join(s['name'] for s in supplementary)} → decoupling (candidate)",
        rationale=reason,
        falsification_metric=falsification_metric,
        is_base_layer=False,
        posterior_confidence=0.3,           # 후보 = 낮은 신뢰
        event=event, distorted_indicator=distorted_indicator,
        expected=expected, actual=actual,
        supplementary=supplementary, attenuation=attenuation,
        historical_episodes=list(episodes),
        sensing_only=abs(attenuation - 1.0) < 1e-9,
    )
    assert_falsifiable(card)
    return card


# 모듈 상수 — 승격된 거시 카드 (lazy 아닌 즉시; ANOMALY_CASES 정적이라 안전)
MACRO_DECOUPLING_CARDS: list[MacroAssumptionCard] = promote_all()


if __name__ == "__main__":
    # 1) 6(+1) 케이스 전부 카드 승격 + falsification 보유
    cards = MACRO_DECOUPLING_CARDS
    print(f"1) 승격 카드 {len(cards)}장")
    assert len(cards) == len(ANOMALY_CASES)
    for c in cards:
        assert c.falsification_metric.strip(), f"{c.id} falsification 부재"
        assert c.domain == "macro" and c.kind == "structural"
    assert any(c.id == "macro.yc_inversion_term_premium" for c in cards)
    print(f"   전부 falsifiable=True, 예: {cards[0].id} v{cards[0].version}")

    # 2) round-trip: card → anomaly → conditional_attenuation 재사용 가능
    from core.brain.indicator_event_correlation import conditional_attenuation, MacroEvent
    card0 = next(c for c in cards if c.id == "macro.yc_inversion_term_premium")
    anom = card_to_anomaly(card0)
    assert anom.case_id == "yc_inversion_term_premium"
    assert anom.event == MacroEvent.RECESSION_ONSET
    assert len(anom.supplementary) == len(card0.supplementary)
    print(f"2) round-trip OK: card→anomaly {anom.case_id}, sup={len(anom.supplementary)}")

    # 3) 신규 candidate case 추가 (falsification 필수)
    cand = add_candidate_card(
        case_id="ai_capex_overheat_decoupling",
        event="inflation_shock", distorted_indicator="core_cpi",
        expected="up", actual="flat",
        reason="AI capex 붐이 생산성 충격으로 단위비용 하락 → 수요견인 인플레 무력화 가설",
        supplementary=[{"name": "productivity_yoy", "fred_id": "OPHNFB", "threshold": 2.5,
                        "direction": "up", "description": "비농업 노동생산성 YoY. 급등 시 비용 인플레 상쇄."}],
        attenuation=0.6,
        falsification_metric="생산성 YoY>2.5 기간 코어CPI 가속 부재(prequential ΔBrier>0). 반증=생산성 높아도 인플레 가속.",
    )
    assert cand.version == "v1.cand" and cand.posterior_confidence == 0.3
    print(f"3) 신규 candidate OK: {cand.id} v{cand.version}")

    # 4) 반증불가 신규 case 거부
    try:
        add_candidate_card(case_id="x", event="inflation_shock", distorted_indicator="core_cpi",
                           expected="up", actual="flat", reason="r", supplementary=[],
                           attenuation=0.5, falsification_metric="  ")
        raise AssertionError("반증불가 candidate 가 통과됨")
    except ValueError:
        print("4) 반증불가 candidate 차단 OK")

    print("macro_assumption_card self-test PASS (6+1 승격 + round-trip + 신규 case + 반증 게이트)")
