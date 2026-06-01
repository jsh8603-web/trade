"""core/assume/judge.py — 3층 판정 결합 (CL-2, 축C / R6·R7).

가정→derivation→**판정**의 최종 결합. 자문 수렴(gemini R1 + claude R1 Opus4.8) 반영:

  L1 = 결정론 floor, **상대축**(cheapness_z = 구조모델 대비 저평가) = **sizing 축**.
  DCF = 독립 veto, **절대축**(내재가치) = **pure kill 축**.
  → L1 ∥ DCF 병렬. 둘은 결합(평균/가중합) 안 함 — 저평가+무가치가 중간점수로
     생존하는 누수 차단. veto = disjunctive(하나만 죽여도 차단).
  L2(Qwen 맥락)·L3(BGE 사례) = **strictly attenuating-only** (claude R1 핵심 정정):
     confirm 이 아니라 감쇠기. a2,a3 ∈ [0,1]. final_size = L1_size * a2 * a3.
     → final ∈ [0, L1_size]. L2/L3 가 L1 sizing 을 **증폭하는 경로 구조적 부재**
       (monotone-down). LLM 요소가 safe-by-construction.

  싼지/비싼지 수치 = L1(cheapness_z)·DCF(내재가치) 결정론. LLM(L2/L3)은 맥락·사례로
  **감쇠만** — 수치판정 X, 증폭 X (plan §0 안티패턴 차단).

  ★fail-safe by manifest (자문 R1/R2 정정 — fail-open 은 역방향이라 금지):
   - L2/L3 미제공(absent, manifest 미선언) = L1 단독 의도 → a=1.0 (결정론 baseline).
   - L2/L3 제공됐는데 errored/timeout/stale(expected-but-failed) = epistemic uncertainty
     → **abstain(방향노출 0)**. a=1.0 fail-open 은 장애 시 사이징을 늘리는 역방향이라 금지.
  abstain(포지션 0): |cheapness_z|<deadzone(L1 neutral band) OR DCF veto OR 기대 confirm 장애.

judge 는 I/O 를 하지 않는다 (순수 판정). 호출자가 value_stock·RagPitPipeline 결과를 주입.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol, Sequence

import numpy as np

from core.pit.as_of import AsOfLike, resolve_as_of
from core.rules.l1_gate import L1Config, Verdict, l1_verdict
from core.rules.signal import Signal
from core.structure.assumption_stats import band_to_size_multiplier, confidence_to_band
from core.assume.weight_card import (
    WeightAssumptionCard, assert_ceiling_invariant, synthesize_l1,
)

# 내재가치가 가격보다 이만큼 아래면(가치 훼손) DCF 독립 veto.
# valuation_gap = (intrinsic - market_cap) / market_cap. 음수 = 고평가.
DCF_VETO_GAP: float = -0.30
DEFAULT_BASE_HALFWIDTH: float = 1.0
REF_HALFWIDTH: float = 1.0
QWEN_MISMATCH_ATTEN: float = 0.5     # 현 상황정의가 S→S' 전환 정황이면 사이징 절반


class ValuationLike(Protocol):
    """value_stock(stock/valuation.py) 의 ValuationResult 구조적 타입 (judge 입력)."""

    valuation_gap: float
    intrinsic_value: float


@dataclass
class JudgeVerdict:
    final: str                                   # allow | veto | abstain | neutral
    l1: Verdict
    dcf_gap: Optional[float] = None
    l2_context: dict = field(default_factory=dict)
    l3_analogs: list = field(default_factory=list)
    confidence: float = 0.0                       # L1/derived base (L2/L3 미반영 — 보고용)
    l1_size: float = 0.0                          # L1 결정론 사이징 (감쇠 전 상한)
    attenuation: tuple[float, float] = (1.0, 1.0) # (a2 Qwen, a3 BGE) ∈ [0,1]
    size_mult: float = 0.0                        # final = l1_size * a2 * a3 ∈ [0, l1_size]
    l1_synth: Optional[float] = None              # ★R15 학습비중 합성 S_L1 (weight 경로, 보고용)
    vetoed_by: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def _align_indicator_z(indicator_z, series_ids: Sequence[str]) -> np.ndarray:
    """지표 신호를 카드 series 순서로 정렬(R15 L1 합성 입력). dict=라벨 lookup(누락=0 기여),
    sequence=순서 일치 가정(길이 검증). 누락 series 0 = 그 지표 신호 부재(기여 없음)."""
    if isinstance(indicator_z, dict):
        return np.array([float(indicator_z.get(s, 0.0)) for s in series_ids], dtype=float)
    arr = np.asarray(indicator_z, dtype=float)
    if arr.shape[0] != len(series_ids):
        raise ValueError(f"indicator_z 길이 {arr.shape[0]} ≠ series {len(series_ids)}")
    return arr


def _base_confidence(l1: Verdict, derived_confidence: Optional[float]) -> float:
    """L1 결정론 사이징의 base 신뢰도. derived(가정 posterior) 우선, 없으면 |z| 근사.
    ★ L2/L3 는 여기 절대 개입 안 함 (monotone-down 보장)."""
    if derived_confidence is not None:
        return float(np.clip(derived_confidence, 0.05, 0.99))
    z = l1.cheapness_z
    if z is None or (isinstance(z, float) and np.isnan(z)):
        return 0.3
    return float(np.clip(0.4 + 0.2 * abs(z), 0.05, 0.95))


def _qwen_attenuator(l2: dict) -> tuple[float, Optional[str]]:
    """L2 Qwen 맥락 → 감쇠기 a2 ∈ [0,1]. 증폭 불가 (max 1.0). 결측/저신뢰 → 1.0(fail-open)."""
    dm = l2.get("definition_match") if l2 else None
    if dm is False:                              # 현 정의가 S→S' 로 바뀐 정황 → 감쇠
        return QWEN_MISMATCH_ATTEN, "L2: 정의전환 정황 S→S' → 사이징 감쇠"
    return 1.0, None                              # 일치/결측 = 감쇠 없음 (증폭 X)


def _bge_attenuator(analogs: Sequence[dict]) -> tuple[float, Optional[str]]:
    """L3 유사사례 → 감쇠기 a3 ∈ [0,1]. 부정사례 다수일수록 ↓. 긍정/결측 = 1.0 (증폭 X)."""
    if not analogs:
        return 1.0, None
    score = 0
    n = 0
    for a in analogs:
        oc = a.get("outcome") or a.get("label")
        if oc is None:
            continue
        n += 1
        if oc in ("win", "positive", "up", 1, True):
            score += 1
        elif oc in ("loss", "negative", "down", -1, False):
            score -= 1
    if not n:
        return 1.0, None
    agree = score / n                            # [-1,1]
    if agree >= 0:
        return 1.0, None                         # 긍정 일치 = 증폭 안 함 (monotone-down)
    a3 = float(np.clip(1.0 + agree, 0.0, 1.0))   # 부정일수록 ↓ (agree=-1 → 0)
    return a3, f"L3: 부정 유사사례 다수(일치도 {agree:+.2f}) → 사이징 감쇠"


def _qwen_accepts_lens(qwen_hook) -> bool:
    """qwen_hook 이 lens/lens_prompt 키워드를 받는지(시그니처 검사). 못 받으면 기존 호출 유지."""
    try:
        import inspect
        sig = inspect.signature(qwen_hook)
        params = sig.parameters
        if any(k in params for k in ("lens", "lens_prompt", "lens_context")):
            return True
        # **kwargs 받으면 임의 키 허용
        return any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    except (ValueError, TypeError):
        return False


def _call_qwen_with_lens(qwen_hook, firm, sector, a, lens_prompt):
    """lens 주입 가능하면 lens=lens_prompt 로 호출, 아니면 기존 시그니처(firm/sector/as_of)로."""
    if lens_prompt and _qwen_accepts_lens(qwen_hook):
        return qwen_hook(firm=firm, sector=sector, as_of=a, lens=lens_prompt)
    return qwen_hook(firm=firm, sector=sector, as_of=a)


def judge(
    firm: str,
    sector: str,
    date_: AsOfLike,
    as_of: AsOfLike,
    *,
    model: Any,
    features: dict,
    signals: list[Signal],
    cards: Optional[dict] = None,
    cfg: Optional[L1Config] = None,
    valuation: Optional[ValuationLike] = None,
    rag: Any = None,                              # RagPitPipeline (query_similar(text,top_k,as_of))
    qwen_hook: Optional[Callable[..., dict]] = None,
    derived_confidence: Optional[float] = None,
    derived_band_halfwidth: Optional[float] = None,
    weight_card: Optional[WeightAssumptionCard] = None,
    indicator_z=None,
    regime_pi: Optional[dict] = None,
    lens_prompt: Optional[str] = None,
) -> JudgeVerdict:
    """L1 floor(상대·sizing) ∥ DCF veto(절대·kill) → L2/L3 attenuator(monotone-down).

    valuation/rag/qwen_hook 부재·장애 = fail-open(a=1.0, L1∧DCF floor 가 안전 확보).

    ★R15(opt-in, 자문 §1.4): weight_card+indicator_z 제공 시 sizing point 를 단일 cheapness_z
    대신 학습비중 다중지표 합성 S_L1=clamp_floor(Σ w·z) 로 교체(soft archetype=regime_pi).
    l1_verdict 의 floor 판정(veto/neutral)은 학습과 분리 유지((c)안). 천장 불변식 항상 강제.
    """
    a = resolve_as_of(as_of)                                       # PIT 강제 (미래거부)

    # === 병렬 veto: L1(상대축) ∥ DCF(절대축) — 결합 없음, disjunctive ===
    l1 = l1_verdict(firm, sector, date_, a, model, features, signals, cards=cards, cfg=cfg)
    dcf_gap = valuation.valuation_gap if valuation is not None else None

    vetoed: list[str] = []
    reasons: list[str] = list(l1.reasons)
    if l1.final == "veto":
        vetoed.append("l1")
    if dcf_gap is not None and dcf_gap < DCF_VETO_GAP:
        vetoed.append("dcf")
        reasons.append(f"DCF veto(절대축): 내재가치 갭 {dcf_gap:+.2%} < {DCF_VETO_GAP:.0%}")
    if vetoed:
        return JudgeVerdict(final="veto", l1=l1, dcf_gap=dcf_gap, vetoed_by=vetoed, reasons=reasons)
    if l1.final == "abstain":                                      # deadzone(L1 neutral band)
        return JudgeVerdict(final="abstain", l1=l1, dcf_gap=dcf_gap,
                            reasons=reasons + ["abstain: L1 neutral band(엣지 없음)"])

    # === L1 결정론 사이징 (상대축만, L2/L3 미개입) ===
    base = _base_confidence(l1, derived_confidence)
    base_hw = derived_band_halfwidth or DEFAULT_BASE_HALFWIDTH
    # ★R15(opt-in): 학습비중 다중지표 합성 S_L1 = clamp_floor(Σ w·z). 미제공 시 단일 cheapness_z.
    s_l1_synth: Optional[float] = None
    if weight_card is not None and indicator_z is not None:
        zc = _align_indicator_z(indicator_z, weight_card.series_ids)
        w = weight_card.composed_weights(regime_pi)
        s_l1_synth = synthesize_l1(zc, w, floor=weight_card.floor)
        if s_l1_synth == 0.0:                                      # deadzone = L1 neutral(엣지 없음)
            return JudgeVerdict(final="abstain", l1=l1, dcf_gap=dcf_gap, confidence=base,
                                l1_synth=0.0, reasons=reasons +
                                ["abstain: L1 학습비중 합성 deadzone(|S_L1|≤floor)"])
        point = s_l1_synth
        reasons.append(f"L1 합성 S_L1={s_l1_synth:+.3f} (학습비중 {weight_card.id}@{weight_card.version})")
    else:
        point = l1.cheapness_z if l1.cheapness_z is not None and not np.isnan(l1.cheapness_z) else 0.0
    band = confidence_to_band(point, base, base_hw)
    l1_size = band_to_size_multiplier((band[1] - band[0]) / 2.0, REF_HALFWIDTH)

    # === L2/L3 = strictly attenuating-only + ★fail-safe by manifest (자문 R1/R2) ===
    # manifest = hook 제공 여부. 미제공(absent) = L1 단독 의도 → a=1.0.
    # 제공됐는데 errored/timeout(expected-but-failed) = epistemic uncertainty → abstain(방향노출 0).
    #   ※ a=1.0 fail-open 은 장애 시 사이징을 늘리는 역방향 = 금지(R1/R2 양모델 정정).
    l2: dict = {}
    expected_failed: list[str] = []
    if qwen_hook is not None:
        try:
            # ★G3 lens 주입(opt-in): lens_prompt 제공 + qwen_hook 이 lens 파라미터를 받으면 LLM
            # 컨텍스트로 전달(STUDY-KIT §2 — 정성 렌즈 주입). 못 받으면 기존 호출(무회귀).
            # lens 는 attenuator 의 입력 컨텍스트일 뿐 — 천장 불변식(down-only)과 무관.
            l2 = _call_qwen_with_lens(qwen_hook, firm, sector, a, lens_prompt) or {}
            if lens_prompt and _qwen_accepts_lens(qwen_hook):
                reasons.append("L2 lens 주입(정성 렌즈 컨텍스트)")
        except Exception as e:                                     # 기대됐는데 장애 → fail-safe
            expected_failed.append(f"L2(Qwen) errored: {e}")
    l3: list = []
    if rag is not None:
        try:
            l3 = rag.query_similar(f"{sector} {firm}", top_k=5, as_of=a) or []
        except Exception as e:
            expected_failed.append(f"L3(BGE) errored: {e}")

    if expected_failed:                                            # ★fail-safe = abstain (min-size 아님)
        return JudgeVerdict(final="abstain", l1=l1, dcf_gap=dcf_gap, l2_context=l2, l3_analogs=l3,
                            confidence=base, l1_size=l1_size, attenuation=(0.0, 0.0), size_mult=0.0,
                            vetoed_by=[], reasons=reasons + expected_failed +
                            ["fail-safe: 기대된 confirm 레이어 장애 → abstain(방향노출 0)"])

    a2, n2 = _qwen_attenuator(l2)
    a3, n3 = _bge_attenuator(l3)
    if n2:
        reasons.append(n2)
    if n3:
        reasons.append(n3)
    size_mult = l1_size * a2 * a3                                  # ∈ [0, l1_size] (monotone-↓)
    assert_ceiling_invariant(size_mult, l1_size)                  # ★순서 불변식: LLM/agent down-only

    final = "allow" if l1.final == "allow_cheap" else "neutral"
    return JudgeVerdict(final=final, l1=l1, dcf_gap=dcf_gap, l2_context=l2, l3_analogs=l3,
                        confidence=base, l1_size=l1_size, attenuation=(a2, a3),
                        size_mult=size_mult, l1_synth=s_l1_synth, vetoed_by=[], reasons=reasons)


if __name__ == "__main__":
    from core.structure import archetype as arch
    from core.rules.signal import make_cyclical_signal_set

    sigs = make_cyclical_signal_set()
    cards = {
        "cyclical": arch.CyclicalCard(primary_metric="ev_ebitda", percentile_overfit_risk=True),
        "compounder": arch.CompounderCard(primary_metric="roic_durability"),
        "event_driven": arch.EventDrivenCard(primary_metric="ps"),
    }

    class DummyModel:
        def __init__(self, z): self._z = z
        def cheapness_z(self, firm, sector, date, as_of): return self._z

    class DummyVal:
        def __init__(self, gap, iv=1.0): self.valuation_gap = gap; self.intrinsic_value = iv

    feats_cheap = {"cheapness_z": -1.8, "pb": 0.8, "ev_ebitda": 4.0,
                   "book_to_bill": 1.2, "inventory_qoq": -0.1, "capex_to_rev": 0.1}
    D, A = "2021-09-30", "2022-01-01"

    # 1) allow + DCF pass + 긍정 confirm → allow, 감쇠 없음 (a2=a3=1.0)
    rag_pos = type("R", (), {"query_similar": lambda self, t, top_k, as_of: [
        {"outcome": "win"}, {"outcome": "win"}, {"outcome": "loss"}]})()
    v1 = judge("S1", "semiconductor", D, A, model=DummyModel(-1.8), features=feats_cheap,
               signals=sigs, cards=cards, valuation=DummyVal(0.10), rag=rag_pos,
               qwen_hook=lambda **k: {"definition_match": True})
    assert v1.final == "allow" and v1.attenuation == (1.0, 1.0) and v1.size_mult == v1.l1_size, v1
    print(f"1) allow+긍정confirm: size={v1.size_mult:.3f}=l1_size (증폭X) atten={v1.attenuation}")

    # 4) degrade(confirm 전무) → a=1.0, size=l1_size (case1 과 동일 = 긍정confirm 이 증폭 안 함 증명)
    v4 = judge("S4", "semiconductor", D, A, model=DummyModel(-1.8), features=feats_cheap,
               signals=sigs, cards=cards)
    assert v4.final == "allow" and v4.size_mult == v1.size_mult, (v4.size_mult, v1.size_mult)
    print(f"4) degrade: size={v4.size_mult:.3f} == 긍정confirm size (monotone-down 불변식 확인)")

    # 5) 부정 confirm(정의전환+부정사례) → 감쇠 (size < l1_size), allow 유지
    rag_neg = type("R", (), {"query_similar": lambda self, t, top_k, as_of: [
        {"outcome": "loss"}, {"outcome": "loss"}, {"outcome": "loss"}]})()
    v5 = judge("S5", "semiconductor", D, A, model=DummyModel(-1.8), features=feats_cheap,
               signals=sigs, cards=cards, valuation=DummyVal(0.10), rag=rag_neg,
               qwen_hook=lambda **k: {"definition_match": False})
    assert v5.final == "allow" and v5.size_mult < v5.l1_size and v5.attenuation == (0.5, 0.0), v5
    print(f"5) 부정confirm: size={v5.size_mult:.3f}<l1_size={v5.l1_size:.3f} atten={v5.attenuation}")

    # 2) L1 allow 인데 DCF veto (절대축 가치훼손) → dual-gate veto
    v2 = judge("S2", "semiconductor", D, A, model=DummyModel(-1.8), features=feats_cheap,
               signals=sigs, cards=cards, valuation=DummyVal(-0.40))
    assert v2.final == "veto" and v2.vetoed_by == ["dcf"], v2
    print(f"2) DCF veto(절대축): vetoed={v2.vetoed_by} gap={v2.dcf_gap:+.0%}")

    # 3) 비쌈(z=+1.5) → L1 floor veto
    v3 = judge("S3", "semiconductor", D, A, model=DummyModel(1.5),
               features=dict(feats_cheap, cheapness_z=1.5), signals=sigs, cards=cards)
    assert v3.final == "veto" and "l1" in v3.vetoed_by, v3
    print(f"3) L1 floor veto: vetoed={v3.vetoed_by}")

    # 6) ★기대된 L2 장애 → fail-safe abstain(방향노출 0), NOT fail-open (자문 R1/R2 정정)
    def boom(**k): raise RuntimeError("qwen down")
    v6 = judge("S6", "semiconductor", D, A, model=DummyModel(-1.8), features=feats_cheap,
               signals=sigs, cards=cards, valuation=DummyVal(0.10), qwen_hook=boom)
    assert v6.final == "abstain" and v6.size_mult == 0.0, v6
    print(f"6) 기대 L2 장애 fail-safe: final={v6.final} size={v6.size_mult} (사이징 증가 역방향 차단)")

    # 6b) L2 미제공(absent) → L1 단독 baseline (a=1.0, allow 유지) — manifest 구분
    v6b = judge("S6b", "semiconductor", D, A, model=DummyModel(-1.8), features=feats_cheap,
                signals=sigs, cards=cards, valuation=DummyVal(0.10))
    assert v6b.final == "allow" and v6b.size_mult == v6b.l1_size, v6b
    print(f"6b) L2 absent: final={v6b.final} size={v6b.size_mult:.3f}=l1_size (결정론 baseline)")

    # 7) ★monotone-down 불변식: 어떤 L2/L3 입력도 size > l1_size 불가
    for dm in (True, False, None):
        for analogs in ([], [{"outcome": "win"}]*3, [{"outcome": "loss"}]*3):
            r = type("R", (), {"query_similar": (lambda an: lambda self, t, top_k, as_of: an)(analogs)})()
            vt = judge("ST", "semiconductor", D, A, model=DummyModel(-1.8), features=feats_cheap,
                       signals=sigs, cards=cards, valuation=DummyVal(0.10), rag=r,
                       qwen_hook=(lambda v: lambda **k: {"definition_match": v})(dm))
            assert vt.size_mult <= vt.l1_size + 1e-12, (dm, analogs, vt.size_mult, vt.l1_size)
    print("7) monotone-down 불변식: 모든 L2/L3 조합에서 size ≤ l1_size 확인")

    # === ★R15: 학습비중 다중지표 합성 S_L1 경로 (opt-in) ===
    from core.assume.weight_card import WeightAssumptionCard
    wc = WeightAssumptionCard(
        id="weight.semi.cyclical", kind="parametric", scope="sector", domain="equity",
        statement="반도체 cyclical 합성비중", falsification_metric="합성 score OOS Rank-IC e-process 붕괴",
        series_ids=("cheapness_z", "book_to_bill", "inventory_qoq"),
        w_global=(0.5, 0.3, 0.2), floor=0.25)

    # 8) weight 경로 — S_L1 = 0.5·(-1.8)+0.3·1.2+0.2·(-0.1) = -0.56, clamp_floor → -0.31
    iz = {"cheapness_z": -1.8, "book_to_bill": 1.2, "inventory_qoq": -0.1}
    v8 = judge("S8", "semiconductor", D, A, model=DummyModel(-1.8), features=feats_cheap,
               signals=sigs, cards=cards, valuation=DummyVal(0.10),
               weight_card=wc, indicator_z=iz)
    assert v8.l1_synth is not None and abs(v8.l1_synth - (-0.31)) < 1e-9, v8.l1_synth
    assert v8.final == "allow" and v8.size_mult <= v8.l1_size + 1e-12, v8
    print(f"8) R15 weight 경로: S_L1={v8.l1_synth:+.3f}(합성) final={v8.final} size={v8.size_mult:.3f}≤l1_size")

    # 9) ★deadzone — 약신호 합성 |S_L1|≤floor → abstain (L1 neutral, 비중 학습이 진입 차단)
    iz_weak = {"cheapness_z": 0.2, "book_to_bill": 0.1, "inventory_qoq": 0.0}  # Σw·z=0.13<0.25
    v9 = judge("S9", "semiconductor", D, A, model=DummyModel(-1.8), features=feats_cheap,
               signals=sigs, cards=cards, valuation=DummyVal(0.10),
               weight_card=wc, indicator_z=iz_weak)
    assert v9.final == "abstain" and v9.l1_synth == 0.0 and v9.size_mult == 0.0, v9
    print(f"9) R15 deadzone: 약신호 → final={v9.final} S_L1={v9.l1_synth} (학습비중 진입 차단)")

    # 10) ★천장 불변식 — weight 경로 + L2/L3 감쇠 조합 전수 size ≤ l1_size
    for dm in (True, False, None):
        for analogs in ([], [{"outcome": "loss"}]*3):
            r = type("R", (), {"query_similar": (lambda an: lambda self, t, top_k, as_of: an)(analogs)})()
            vt = judge("ST10", "semiconductor", D, A, model=DummyModel(-1.8), features=feats_cheap,
                       signals=sigs, cards=cards, valuation=DummyVal(0.10), rag=r,
                       qwen_hook=(lambda v: lambda **k: {"definition_match": v})(dm),
                       weight_card=wc, indicator_z=iz)
            assert vt.size_mult <= vt.l1_size + 1e-12, (dm, analogs, vt.size_mult, vt.l1_size)
    print("10) R15 천장 불변식: weight 경로 모든 L2/L3 조합 size ≤ l1_size (down-only 강제)")

    # 11) opt-out 동등성 — weight_card 미제공 = 기존 단일 cheapness_z 경로 그대로(무회귀)
    v11 = judge("S11", "semiconductor", D, A, model=DummyModel(-1.8), features=feats_cheap,
                signals=sigs, cards=cards, valuation=DummyVal(0.10))
    assert v11.l1_synth is None and abs(v11.size_mult - v1.size_mult) < 1e-12, v11
    print(f"11) opt-out 동등성: weight 미제공 → l1_synth=None size={v11.size_mult:.3f}=case1(무회귀)")

    print("CL-2 judge self-test PASS (+ R15 weight 합성/deadzone/천장불변식/opt-out)")
