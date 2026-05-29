"""core/assume/card_contract.py — 가정 카드 공유 계약 (btn-button T2 제공, T3/도메인 소비).

DESIGN-button-v2.md §2 / §10. 자문 R1~R5 수렴 반영:
- falsification_metric 필수 = 반증불가 카드 진입 금지 (gemini R1 C-1). assert_falsifiable 게이트.
- AssumptionCardLike = **구조적 Protocol** → MacroAssumptionCard(brain)·commodity/crypto archetype·
  equity 카드가 상속 없이 satisfy. T3 Registry/Validator 가 이 표면으로 카드를 통합 보관·dispatch.
- bitemporal: version(정의 변경 시 bump) + valid_from(시변) + regime_model_version(재현성).
- is_base_layer = regime 정의 등 = 자동변경 금지 (claude C-meta), HumanApprovalGate 경유.

경계: 본 모듈만 btn-button 소유 (core/assume 내). registry/validator/judge/update_controller = T3.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field, field_validator

AssumptionKind = Literal["structural", "parametric"]
AssumptionScope = Literal["global", "sector", "asset", "macro"]
AssumptionDomain = Literal["macro", "equity", "commodity", "crypto"]


@runtime_checkable
class AssumptionCardLike(Protocol):
    """모든 가정 카드가 만족해야 하는 구조적 계약 (T3 Registry/Validator dispatch 표면).

    이 Protocol 을 만족하면 도메인(macro/equity/commodity/crypto) 무관하게 동일 검증·원장 경로를
    탄다. validator dispatch 키 = kind, 충돌해소 우선순위 = scope(asset>sector>global, macro 별도).
    """
    id: str
    version: str
    kind: AssumptionKind
    scope: AssumptionScope
    domain: AssumptionDomain
    statement: str
    rationale: str
    falsification_metric: str            # 반증 조건 (비면 진입 금지)
    is_base_layer: bool
    valid_from: Optional[date]
    regime_model_version: Optional[str]
    posterior_confidence: float
    band_halfwidth: float
    depends_on: list[str]
    half_life: Optional[float]


class BaseAssumptionFields(BaseModel):
    """AssumptionCardLike 를 구현하는 frozen 기본 카드 (도메인 카드가 상속 또는 합성).

    도메인 카드(MacroAssumptionCard 등)는 이를 상속해 도메인 필드를 더한다. T3 의 별 base 와
    충돌하지 않도록 구조적 typing(Protocol) 으로 계약을 고정 — 상속은 선택.
    """
    model_config = {"frozen": True, "extra": "allow"}

    id: str
    version: str = "v1"
    kind: AssumptionKind
    scope: AssumptionScope
    domain: AssumptionDomain
    statement: str
    rationale: str = ""
    falsification_metric: str
    is_base_layer: bool = False
    valid_from: Optional[date] = None
    regime_model_version: Optional[str] = None
    posterior_confidence: float = 0.5
    band_halfwidth: float = 1.0
    depends_on: list[str] = Field(default_factory=list)
    half_life: Optional[float] = None

    @field_validator("falsification_metric")
    @classmethod
    def _falsification_nonempty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(
                "falsification_metric 비어있음 = 반증불가 카드 = 진입 금지 (gemini R1 C-1). "
                "정량 반증 조건을 명시하라."
            )
        return v


class NotFalsifiableError(ValueError):
    """반증불가 카드 진입 시도 (Registry 등록 게이트에서 raise)."""


def assert_falsifiable(card: AssumptionCardLike) -> None:
    """Registry 등록 전 진입 게이트 — falsification_metric 없는 카드 차단.

    AssumptionCardLike 면 어느 도메인 카드든 검사. T3 Registry.register() 첫 줄에서 호출.
    """
    fm = getattr(card, "falsification_metric", None)
    if not fm or not str(fm).strip():
        raise NotFalsifiableError(
            f"카드 {getattr(card, 'id', '?')!r} falsification_metric 부재 → 등록 거부 "
            "(반증불가 = 가정 아님)."
        )


def is_card_like(obj) -> bool:
    """런타임 구조 점검 (Protocol isinstance — 필드 존재 여부)."""
    return isinstance(obj, AssumptionCardLike)


if __name__ == "__main__":
    # 1) 정상 카드 — 모든 필드 + falsification 충족
    c = BaseAssumptionFields(
        id="macro.yc_inversion_term_premium",
        kind="structural", scope="macro", domain="macro",
        statement="수익률곡선 역전 → 침체, UNLESS QE term premium 왜곡(WALCL 高)",
        falsification_metric="역전+WALCL>7.5e6 기간 12M 침체율이 baseline 과 d<0.5 (attenuation 무효)",
        is_base_layer=False, posterior_confidence=0.6,
    )
    assert c.kind == "structural" and c.domain == "macro"
    assert is_card_like(c), "BaseAssumptionFields 가 AssumptionCardLike 미충족"
    assert_falsifiable(c)  # 통과해야
    print(f"1) 정상 카드 OK: {c.id} v{c.version} falsifiable={bool(c.falsification_metric)}")

    # 2) 반증불가 카드 — falsification 빈 값 → 생성 자체 거부
    try:
        BaseAssumptionFields(id="bad", kind="parametric", scope="global", domain="equity",
                             statement="x", falsification_metric="   ")
        raise AssertionError("빈 falsification_metric 이 통과됨 (차단 실패)")
    except ValueError as e:
        print(f"2) 반증불가 카드 차단 OK: {type(e).__name__}")

    # 3) 구조적 Protocol — 상속 없는 임의 객체도 필드 갖추면 satisfy
    class _Duck:
        id = "x"; version = "v1"; kind = "parametric"; scope = "asset"; domain = "crypto"
        statement = "s"; rationale = ""; falsification_metric = "f"; is_base_layer = False
        valid_from = None; regime_model_version = None; posterior_confidence = 0.5
        band_halfwidth = 1.0; depends_on = []; half_life = None
    assert is_card_like(_Duck()), "구조적 Protocol 매칭 실패"
    assert_falsifiable(_Duck())
    print("3) 구조적 Protocol(상속 없음) OK: crypto duck 카드 satisfy")

    # 4) frozen 불변
    try:
        c.version = "v2"  # type: ignore
        raise AssertionError("frozen 카드가 수정됨")
    except (ValueError, TypeError, AttributeError):
        print("4) frozen 불변 OK")

    print("card_contract self-test PASS (계약 + falsification 게이트 + 구조적 Protocol + frozen)")
