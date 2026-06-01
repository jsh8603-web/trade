"""core/study/lens_store.py — 정성 렌즈(블록1 LENS) 보관·렌더·주입 어댑터 (골격 G3).

study_session.yaml 블록1 lens 는 LLM 이 종목을 평가할 때 주입되는 **판단 scope**다(STUDY-KIT §2).
이 어댑터는 (scope, regime) → Lens 를 보관하고, judge 의 L2(LLM/qwen) 컨텍스트에 넣을 프롬프트
문자열로 렌더한다. **weight_card 본체는 안 고친다** — lens 는 카드와 분리해 여기서 독립 보관·주입.

opt-in: 환경변수 `INV_STUDY_LENS` 가 truthy 일 때만 주입 활성(off = byte-identical 무회귀).
렌즈는 가변(STUDY-KIT §2 3단계): flag_router(G4)가 신뢰도 누적으로 estimation_note·regime_reading
을 갱신하면 LensStore.put 으로 새 버전을 덮어 주입 텍스트가 바뀐다. down-only 불변식과 무관(lens 는
LLM attenuator 의 입력 컨텍스트일 뿐, 사이징 천장을 올리지 않는다).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from core.study.study_loader import Lens, StudySession


_ENV_FLAG = "INV_STUDY_LENS"


def is_enabled() -> bool:
    """렌즈 주입 opt-in 게이트. off 면 judge 가 lens_prompt 를 받아도 무시(무회귀)."""
    return str(os.environ.get(_ENV_FLAG, "")).strip().lower() in ("1", "true", "on", "yes")


def render_lens_prompt(lens: Lens, *, scope: str = "", regime_id: Optional[str] = None,
                       confidence_note: Optional[str] = None) -> str:
    """Lens(블록1) → LLM 컨텍스트 문자열. 빈 필드는 생략. 빈 lens 면 빈 문자열.

    confidence_note: flag_router(G4)가 라이브 누적한 가설 신뢰도 한 줄 요약(U1 flag→lens). 주면
    estimation_note 다음에 동적 라벨로 붙어 qwen(agent 판단)이 저신뢰 가설을 보수적으로 읽게 한다.
    None(기본)이면 기존과 byte-identical(무회귀).
    """
    if lens is None:
        return ""
    parts: list = []
    head = f"[판단 렌즈{(' · ' + scope) if scope else ''}{(' · regime=' + str(regime_id)) if regime_id else ''}]"
    if lens.pricing_principle:
        parts.append(f"가격결정 원리: {lens.pricing_principle.strip()}")
    if lens.report_relations:
        rels = "; ".join(str(r).strip() for r in lens.report_relations if str(r).strip())
        if rels:
            parts.append(f"리포트 관계도: {rels}")
    if lens.regime_reading:
        parts.append(f"국면 독법: {lens.regime_reading.strip()}")
    if lens.estimation_note:
        parts.append(f"현 추정(가변): {lens.estimation_note.strip()}")
    if confidence_note and str(confidence_note).strip():
        parts.append(f"flag 신뢰도(라이브 누적, 저신뢰=보수 해석): {str(confidence_note).strip()}")
    if not parts:
        return ""
    return head + "\n" + "\n".join(f"- {p}" for p in parts)


# ---------------------------------------------------------------------------
# LensStore — (scope, regime_id) → Lens. judge 주입의 단일 출처.
# ---------------------------------------------------------------------------

@dataclass
class LensStore:
    """정성 렌즈 보관소. scope 기본 + (scope, regime) 특수화. 가변(put 으로 갱신)."""
    _lenses: dict = field(default_factory=dict)   # (scope, regime_id|None) → Lens

    def put(self, lens: Lens, *, scope: str, regime_id: Optional[str] = None) -> None:
        self._lenses[(scope, regime_id)] = lens

    def get(self, scope: str, regime_id: Optional[str] = None) -> Optional[Lens]:
        """regime 특수화 우선 → scope 기본(regime_id=None) fallback."""
        if regime_id is not None and (scope, regime_id) in self._lenses:
            return self._lenses[(scope, regime_id)]
        return self._lenses.get((scope, None))

    def render(self, scope: str, regime_id: Optional[str] = None,
               confidence_note: Optional[str] = None) -> Optional[str]:
        """주입용 프롬프트. opt-in off 면 None(무회귀). 해당 lens 없으면 None.

        confidence_note: U1 flag→lens. flag_router.confidence_note() 결과를 받아 동적 신뢰도 라벨 주입.
        """
        if not is_enabled():
            return None
        lens = self.get(scope, regime_id)
        if lens is None:
            return None
        txt = render_lens_prompt(lens, scope=scope, regime_id=regime_id, confidence_note=confidence_note)
        return txt or None

    def scopes(self) -> list:
        return sorted({s for (s, _) in self._lenses})


def from_study_session(s: StudySession, store: Optional[LensStore] = None) -> LensStore:
    """study yaml 의 lens(블록1)를 asset_scope 별로 등록. regime_reading 은 scope 기본 렌즈로.

    여러 방의 lens 를 한 store 에 누적(store 재사용). asset_scope 각각에 같은 lens 를 매핑.
    """
    store = store or LensStore()
    for scope in (s.asset_scope or [s.study_id]):
        store.put(s.lens, scope=str(scope))
    return store


# ===========================================================================
# self-test
# ===========================================================================

if __name__ == "__main__":
    from core.study.study_loader import load_study_session

    macro = {
        "study_id": "macro", "asset_scope": ["macro"], "as_of": "2026-05-30",
        "lens": {
            "pricing_principle": "거시 자산가격 = 성장·인플레·유동성·리스크프리미엄 조합",
            "report_relations": ["M2↔미·일 국채금리↔환율", "HY OAS 확대→리스크오프"],
            "regime_reading": "Reflation→주식·원자재 우위",
            "estimation_note": "Recovery 초입 추정(확신 중)",
        },
        "indicators": [{"id": "x", "family": "macro_driver", "in_our_system": True}],
    }
    s = load_study_session(macro)

    # 1) render_lens_prompt — 필드 직렬화
    txt = render_lens_prompt(s.lens, scope="macro")
    assert "가격결정 원리" in txt and "M2↔미·일 국채금리↔환율" in txt and "Recovery 초입" in txt
    print(f"1) render_lens_prompt OK ({len(txt)} chars)")

    # 2) LensStore put/get + regime 특수화 우선
    store = from_study_session(s)
    assert store.get("macro").pricing_principle.startswith("거시")
    store.put(Lens(pricing_principle="침체 국면 특수 렌즈"), scope="macro", regime_id="Stagflation")
    assert store.get("macro", "Stagflation").pricing_principle == "침체 국면 특수 렌즈"
    assert store.get("macro", "Reflation").pricing_principle.startswith("거시")  # fallback
    print(f"2) LensStore get + regime 특수화/fallback OK: scopes={store.scopes()}")

    # 3) opt-in 게이트: off → render None (무회귀)
    os.environ.pop(_ENV_FLAG, None)
    assert store.render("macro") is None, "opt-in off 인데 주입됨(회귀)"
    print(f"3) opt-in off → render None (무회귀) OK")

    # 4) opt-in on → 실제 주입 텍스트
    os.environ[_ENV_FLAG] = "1"
    r = store.render("macro")
    assert r and "판단 렌즈" in r and "macro" in r
    rr = store.render("macro", "Stagflation")
    assert "침체 국면 특수 렌즈" in rr
    print(f"4) opt-in on → render 텍스트 OK (regime별 분기)")

    # 5) 가변성: put 으로 estimation_note 갱신 시 주입 텍스트 변화(flag→lens 갱신 시뮬)
    s.lens.estimation_note = "Overheat 전환 추정으로 갱신됨(flag 누적)"
    store.put(s.lens, scope="macro")
    r2 = store.render("macro")
    assert "Overheat 전환" in r2
    print(f"5) lens 가변(put 갱신→주입 텍스트 변화) OK")

    # 6) 없는 scope → None graceful
    os.environ[_ENV_FLAG] = "1"
    assert store.render("nonexistent") is None
    os.environ.pop(_ENV_FLAG, None)
    print(f"6) 없는 scope graceful OK")

    print("\nlens_store self-test PASS (render + store regime 분기/fallback + opt-in 게이트 + 가변 갱신)")
