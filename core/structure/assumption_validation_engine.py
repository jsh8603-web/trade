"""core/structure/assumption_validation_engine.py — BB-4: 검증 cohesion (holds + FDR).

DESIGN-button-v2.md §6 / §10.5·10.6. 기존 부품(assumption_stats holds + online_fdr LORD++)을
**가정 카드 단위로 묶는** cohesion 레이어. T3 Validator/UpdateController 가 호출.

자문 수렴 반영:
- card.kind dispatch → validate_parametric/structural (regime-conditional holds_now).
- **자산클래스별 독립 FDR 스트림**(R3/gemini R4): 풀링 금지 — crypto 가 macro alpha 예산 독식
  + exchangeability 붕괴 차단. stream key = (domain, assumption_id). calibration α 자산별 차등.
- **event-time 인덱싱**: validate 1회 = 1 resolved-outcome tick(=stream.test 1회). FDR_DECISION 은
  decision_time 순(immutable) — 호출자가 그 순서로 validate 하면 보장 유지.
- **부활 차단**: 기각된 가정을 regime 복귀 때 반복 검정 → LORD++ alpha-wealth 소진.
- falsification_metric → validator 파라미터 휴리스틱 컴파일(BB-1 카드 검증 연계).

결정 X — 관측·산출만(rule_observer "관측≠제어" 동형). 데이터는 호출자(ledger)가 주입.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from core.assume.card_contract import AssumptionCardLike
from core.structure.assumption_stats import (
    RegimeConditionalReport,
    RegimeHolds,
    validate_parametric,
    validate_structural,
)
from core.structure.online_fdr import LordPlusPlus
from core.structure.hierarchical_fdr import (
    EProcessSpender,
    HierarchicalFDRCascade,
    falsification_power,
    pvalue_to_evalue,
)
from core.structure.eprocess_backbone import ELOND

# 자산클래스별 LORD++ alpha (R4 calibration: crypto 노이즈↑ → α 관대, macro 희소 → α 엄격)
ALPHA_BY_DOMAIN = {"crypto": 0.10, "equity": 0.07, "commodity": 0.07, "macro": 0.05}
_DEFAULT_ALPHA = 0.05

# V7-④ per-domain 추정 다형성 (update 주기·decay): crypto 빠른 망각/잦은 갱신, macro 느린/희소.
# e-process decay 와 검정력 reference n 에 소비. 자문 §btn-button "per-domain 추정 다형성".
DOMAIN_ESTIMATION_POLICY = {
    "crypto":    {"eprocess_decay": 0.90, "update_period_days": 1,  "min_baseline_n": 60},
    "equity":    {"eprocess_decay": 0.97, "update_period_days": 5,  "min_baseline_n": 40},
    "commodity": {"eprocess_decay": 0.97, "update_period_days": 5,  "min_baseline_n": 40},
    "macro":     {"eprocess_decay": 0.99, "update_period_days": 21, "min_baseline_n": 24},
}
_DEFAULT_POLICY = {"eprocess_decay": 0.97, "update_period_days": 5, "min_baseline_n": 40}


def estimation_policy(domain: str) -> dict:
    return DOMAIN_ESTIMATION_POLICY.get(domain, _DEFAULT_POLICY)


def _phi(z: float) -> float:
    """표준정규 CDF (erf 기반, numpy/math only)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _evidence_effect(rh: RegimeHolds) -> float:
    """RegimeHolds.evidence → 효과크기(가정 위반 정도). parametric=cohens_d / structural=slope/loss."""
    ev = rh.evidence or {}
    if "cohens_d" in ev and ev["cohens_d"] is not None:
        return abs(float(ev["cohens_d"]))
    rs, ml = ev.get("recent_slope"), ev.get("mean_loss")
    if rs is not None and ml is not None:
        return abs(float(rs)) / (float(ml) + 1e-9)
    # fallback: 신뢰도 낮을수록 효과 큼
    return max(0.0, 1.0 - float(rh.confidence))


def _p_from_holds(rh: Optional[RegimeHolds]) -> float:
    """현재 regime holds → 가정-변경 신호 p-value (작을수록 '변경 필요' 신호).

    holds=True(가정 성립) → 효과 작음 → z 작음 → p≈1(변경 신호 없음).
    holds=False(가정 깸) → 효과 큼 → z 큼 → p≈0(변경 신호) → FDR 검정 통과 후보.
    z = effect * sqrt(min(n,200)) (pseudo t-stat). p = 2(1-Phi(|z|)).
    """
    if rh is None:
        return 1.0
    eff = _evidence_effect(rh)
    n_eff = min(int(rh.n_obs), 200)
    z = eff * math.sqrt(max(n_eff, 1))
    p = 2.0 * (1.0 - _phi(abs(z)))
    # holds=True 인데 우연히 p 작아지는 것 방지: 성립이면 floor 상향
    if rh.holds:
        p = max(p, 0.5)
    return float(min(max(p, 1e-9), 1.0))


@dataclass
class ValidationVerdict:
    assumption_id: str
    domain: str
    kind: str
    holds_now: Optional[bool]
    confidence_now: float
    p_value: float
    alpha_t: float
    fdr_significant: bool                 # AND-gate 첫 조건 (T3 hysteresis_and_gate 주입)
    by_regime: dict = field(default_factory=dict)
    falsifiable: bool = True              # 형식 존재 (falsification_metric 비어있지 않음)
    evidence: dict = field(default_factory=dict)
    # V7 보강
    eprocess_significant: Optional[bool] = None   # ② anytime-valid 게이트 (None=미사용)
    power: float = 1.0                            # ③ 추정 검정력
    protectable: bool = True                      # ③ 형식+power 게이트 통과 (power=0 → False)
    cascade_reason: Optional[str] = None          # ① 부모게이트 결과 (None=cascade 미사용)
    fdr_backbone: str = "lord"                    # R4 backbone ('lord'/'elond')
    elond_significant: Optional[bool] = None      # R4 e값 online FDR readout (None=lord backbone)


def compile_falsification(falsification_metric: str) -> dict:
    """falsification_metric 문자열 → validator 파라미터 휴리스틱 (BB-1 카드 검증 연계).

    정설 키워드 매칭으로 어떤 검정을 써야 하는지 힌트. 정밀 파싱 아닌 라우팅 보조.
    """
    s = (falsification_metric or "").lower()
    hints = []
    if any(k in s for k in ["brier", "prequential", "δbrier", "예측"]):
        hints.append("structural:prequential")
    if any(k in s for k in ["cusum", "이탈", "평균이동", "급등"]):
        hints.append("parametric:cusum")
    if any(k in s for k in ["variance-ratio", "variance ratio", "평균회귀", "mean-revert", "mean revert"]):
        hints.append("parametric:variance_ratio")
    if any(k in s for k in ["f-test", "계절", "seasonal", "strength"]):
        hints.append("structural:seasonal_f")
    if any(k in s for k in ["mechanism", "독립 검증", "결과독립", "term premium"]):
        hints.append("mechanism_validation")
    kind = "structural" if any(h.startswith("structural") for h in hints) else (
        "parametric" if any(h.startswith("parametric") for h in hints) else "unknown")
    return {"kind": kind, "hints": hints, "has_mechanism_check": "mechanism_validation" in hints,
            "falsifiable": bool(s.strip())}


class AssumptionValidationEngine:
    """가정 카드 → regime-conditional holds → 가정별 FDR stream → AND-gate fdr_significant.

    T2 통계 cohesion. 가정별 LORD++ 스트림을 자산클래스 격리 보유. 부활 = wealth 소진 차단.
    """

    def __init__(self, alpha_by_domain: Optional[dict] = None, *, use_eprocess: bool = True,
                 power_floor: float = 0.5, power_ref_effect: float = 0.5,
                 cascade: Optional[HierarchicalFDRCascade] = None,
                 fdr_backbone: str = "lord"):
        self.alpha_by_domain = dict(ALPHA_BY_DOMAIN)
        if alpha_by_domain:
            self.alpha_by_domain.update(alpha_by_domain)
        self.use_eprocess = use_eprocess
        self.power_floor = power_floor              # ③ 검정력 하한
        self.power_ref_effect = power_ref_effect     # ③ 탐지 목표 효과크기 (의미있는 위반 margin)
        self.cascade = cascade                       # ① 선택적 hierarchical 부모게이트
        # R4: FDR backbone — 'lord'(p값 LORD++, 기본·하위호환) / 'elond'(e값 online FDR, 임의의존 robust)
        self.fdr_backbone = fdr_backbone
        # stream key = (domain, assumption_id) → LORD++ (자산클래스 격리)
        self._streams: dict[tuple, LordPlusPlus] = {}
        self._eproc: dict[tuple, EProcessSpender] = {}
        self._elond: dict[tuple, ELOND] = {}

    def _elond_stream(self, domain: str, assumption_id: str) -> ELOND:
        key = (domain, assumption_id)
        if key not in self._elond:
            self._elond[key] = ELOND(alpha=self.alpha_by_domain.get(domain, _DEFAULT_ALPHA))
        return self._elond[key]

    def _stream(self, domain: str, assumption_id: str) -> LordPlusPlus:
        key = (domain, assumption_id)
        if key not in self._streams:
            alpha = self.alpha_by_domain.get(domain, _DEFAULT_ALPHA)
            self._streams[key] = LordPlusPlus(alpha=alpha)
        return self._streams[key]

    def _eprocess(self, domain: str, assumption_id: str) -> EProcessSpender:
        key = (domain, assumption_id)
        if key not in self._eproc:
            alpha = self.alpha_by_domain.get(domain, _DEFAULT_ALPHA)
            decay = estimation_policy(domain)["eprocess_decay"]   # ④ per-domain 망각
            self._eproc[key] = EProcessSpender(alpha=alpha, decay=decay)
        return self._eproc[key]

    def validate(
        self,
        card: AssumptionCardLike,
        *,
        regime_ids,
        current_regime: int,
        realized=None,
        assumed_value: Optional[float] = None,
        predictions=None,
        outcomes=None,
        sd: Optional[float] = None,
        parent_id: Optional[str] = None,
        action: str = "new_entry",
    ) -> ValidationVerdict:
        """card.kind dispatch → holds_now → 가정별 FDR test → ValidationVerdict.

        parametric: realized + assumed_value 필요. structural: predictions + outcomes 필요.
        validate 1회 = 1 event-time tick (FDR stream 소모). 호출 순서 = decision_time 순 권장.
        parent_id/action: cascade 주입 시 부모(거시 regime) 게이트 + de-risking bypass 라우팅.
        """
        fmeta = compile_falsification(getattr(card, "falsification_metric", ""))
        if card.kind == "parametric":
            if realized is None or assumed_value is None:
                raise ValueError("parametric 검증 = realized + assumed_value 필요")
            report: RegimeConditionalReport = validate_parametric(
                card.id, assumed_value, realized, regime_ids, current_regime, sd=sd)
        elif card.kind == "structural":
            if predictions is None or outcomes is None:
                raise ValueError("structural 검증 = predictions + outcomes 필요")
            report = validate_structural(card.id, predictions, outcomes, regime_ids, current_regime)
        else:
            raise ValueError(f"미지 kind: {card.kind!r}")

        rh = report.by_regime.get(current_regime)
        p = _p_from_holds(rh)

        # ③ falsification POWER 게이트: 형식 존재 + 검정력 하한. n 빈약/baseline 부재 → 보호 0.
        n_eff = int(rh.n_obs) if rh is not None else 0
        min_n = estimation_policy(card.domain)["min_baseline_n"]
        power = falsification_power(self.power_ref_effect, n_eff,
                                    alpha=self.alpha_by_domain.get(card.domain, _DEFAULT_ALPHA))
        protectable = bool(fmeta["falsifiable"] and power >= self.power_floor and n_eff >= min_n)

        stream = self._stream(card.domain, card.id)
        dec = stream.test(p)
        # R4: backbone 선택 — elond 면 e값 online FDR(임의의존 robust)이 fdr_sig 주체, lord 는 reporting 유지
        elond_reject = None
        if self.fdr_backbone == "elond":
            ed_fdr = self._elond_stream(card.domain, card.id).test(pvalue_to_evalue(p))
            elond_reject = ed_fdr.reject
            fdr_sig = ed_fdr.reject
        else:
            fdr_sig = dec.reject

        # ② e-process anytime-valid 게이트 (optional-stopping robust). 최종 = FDR ∧ e-process.
        eproc_sig = None
        e_val = 0.0
        if self.use_eprocess:
            ep = self._eprocess(card.domain, card.id)
            ed = ep.test(p)
            eproc_sig = ed.reject
            e_val = ed.e_value
            fdr_sig = fdr_sig and ed.reject

        # ① 선택적 hierarchical cascade: 부모(거시 regime) 게이트. 미통과 신규진입 차단.
        cascade_reason = None
        if self.cascade is not None and parent_id is not None:
            cd = self.cascade.test_child(parent_id, card.id, p, action=action)
            cascade_reason = cd.reason
            fdr_sig = fdr_sig and cd.reject

        # ③ 보호 불가(power=0/baseline 부재) → FDR 유의 무효화 (형식만으론 보호 0)
        if not protectable:
            fdr_sig = False

        return ValidationVerdict(
            assumption_id=card.id, domain=card.domain, kind=card.kind,
            holds_now=report.holds_now, confidence_now=report.confidence_now,
            p_value=dec.p_value, alpha_t=dec.alpha_t, fdr_significant=bool(fdr_sig),
            by_regime={r: {"holds": h.holds, "n": h.n_obs, "conf": round(h.confidence, 3),
                           "evidence": h.evidence} for r, h in report.by_regime.items()},
            falsifiable=fmeta["falsifiable"],
            evidence={"falsification_hints": fmeta["hints"], "fdr_t": dec.t,
                      "n_rejections": stream.n_rejections, "e_value": round(e_val, 3),
                      "power_ref_effect": self.power_ref_effect, "min_baseline_n": min_n},
            eprocess_significant=eproc_sig, power=round(power, 4), protectable=protectable,
            cascade_reason=cascade_reason, fdr_backbone=self.fdr_backbone,
            elond_significant=elond_reject,
        )

    def stream_state(self, domain: str, assumption_id: str) -> dict:
        s = self._streams.get((domain, assumption_id))
        if s is None:
            return {"exists": False}
        return {"exists": True, "t": s.t, "n_rejections": s.n_rejections,
                "alpha": s.alpha, "isolated_key": (domain, assumption_id)}


if __name__ == "__main__":
    from core.brain.macro_assumption_card import MACRO_DECOUPLING_CARDS
    from core.assume.card_contract import BaseAssumptionFields
    rng = np.random.default_rng(7)
    eng = AssumptionValidationEngine()

    # 1) parametric 카드: regime0 안정(성립) / regime1 평균이동(깸) → holds_now 분리
    pcard = BaseAssumptionFields(
        id="commodity.carry_normal_range", kind="parametric", scope="asset", domain="commodity",
        statement="백워데이션 carry 정상범위=θ", falsification_metric="carry CUSUM 이탈 + variance-ratio")
    n = 80
    reg = np.array([0] * n + [1] * n)
    realized = np.concatenate([rng.normal(15, 1, n), rng.normal(19, 1, n)])
    v0 = eng.validate(pcard, regime_ids=reg, current_regime=0, realized=realized, assumed_value=15.0, sd=1.0)
    v1 = eng.validate(pcard, regime_ids=reg, current_regime=1, realized=realized, assumed_value=15.0, sd=1.0)
    print(f"1) parametric: r0 holds={v0.holds_now} p={v0.p_value:.3f} fdr={v0.fdr_significant} / "
          f"r1 holds={v1.holds_now} p={v1.p_value:.3f} fdr={v1.fdr_significant}")
    assert v0.holds_now is True and v1.holds_now is False
    assert v1.fdr_significant, "가정 깸(r1) 인데 FDR 미유의"

    # 2) structural 카드 (거시 decoupling): 메커니즘 작동 → holds
    scard = MACRO_DECOUPLING_CARDS[0]   # macro.yc_inversion_term_premium (structural)
    pred = rng.normal(0, 0.3, 60); out = pred + rng.normal(0, 0.2, 60)
    vs = eng.validate(scard, regime_ids=np.zeros(60, int), current_regime=0,
                      predictions=pred, outcomes=out)
    print(f"2) structural(거시카드 {scard.id}): holds={vs.holds_now} hints={vs.evidence['falsification_hints']}")
    assert vs.holds_now is True

    # 3) 자산클래스 격리 — crypto α=0.10, macro α=0.05 별 스트림
    s_cm = eng.stream_state("commodity", "commodity.carry_normal_range")
    s_mac = eng.stream_state("macro", scard.id)
    print(f"3) 격리 스트림: commodity α={eng.alpha_by_domain['commodity']} macro α={eng.alpha_by_domain['macro']} "
          f"keys={s_cm['isolated_key']},{s_mac['isolated_key']}")
    assert s_cm["isolated_key"] != s_mac["isolated_key"]

    # 4) 부활 차단 — 기각된(holds=True null) 가정을 50회 반복 검정 → 폭주 없음 (LORD++ FDR 제어)
    dead = BaseAssumptionFields(id="dead.assumption", kind="parametric", scope="global",
                                domain="equity", statement="x", falsification_metric="cusum")
    stable = rng.normal(10, 1, 60)   # 가정값 10 근처 안정 = null
    for _ in range(50):
        eng.validate(dead, regime_ids=np.zeros(60, int), current_regime=0,
                     realized=stable, assumed_value=10.0, sd=1.0)
    st = eng.stream_state("equity", "dead.assumption")
    print(f"4) 부활 차단: 50 검정 → 기각 {st['n_rejections']} (소수여야 = FDR 제어)")
    assert st["n_rejections"] <= 3, st["n_rejections"]

    # 5) falsification compile
    fc = compile_falsification("prequential ΔBrier>0 + mechanism: ACM term premium 독립 검증")
    print(f"5) falsification compile: kind={fc['kind']} mechanism={fc['has_mechanism_check']}")
    assert fc["has_mechanism_check"] and "structural:prequential" in fc["hints"]

    # 6) ③ POWER 게이트: n 빈약 → 위반(작은 p) 이어도 protectable=False → fdr_significant 무효
    eng6 = AssumptionValidationEngine()
    tiny = rng.normal(20, 1, 8)            # n=8 << min_baseline(commodity 40), 평균이동(위반)
    vt = eng6.validate(pcard, regime_ids=np.zeros(8, int), current_regime=0,
                       realized=tiny, assumed_value=15.0, sd=1.0)
    print(f"6) power 게이트: power={vt.power:.3f} protectable={vt.protectable} "
          f"holds={vt.holds_now} fdr_sig={vt.fdr_significant} (형식만으론 보호 0)")
    assert vt.protectable is False and vt.fdr_significant is False

    # 7) ① cascade 통합: 부모(거시 regime) 미통과 → 신규진입 차단 / de-risking 우회
    casc = HierarchicalFDRCascade(alpha=0.05)
    casc.evaluate_parent("macro.regime_shift", p_independent=0.40)   # 미통과
    eng7 = AssumptionValidationEngine(cascade=casc)
    broke = np.concatenate([rng.normal(15, 1, 60), rng.normal(20, 1, 60)])
    rr = np.array([0] * 60 + [1] * 60)
    v_new = eng7.validate(pcard, regime_ids=rr, current_regime=1, realized=broke,
                          assumed_value=15.0, sd=1.0, parent_id="macro.regime_shift", action="new_entry")
    v_risk = eng7.validate(pcard, regime_ids=rr, current_regime=1, realized=broke,
                           assumed_value=15.0, sd=1.0, parent_id="macro.regime_shift", action="de_risking")
    print(f"7) cascade: new_entry reason={v_new.cascade_reason} fdr={v_new.fdr_significant} / "
          f"de_risking reason={v_risk.cascade_reason}")
    assert v_new.cascade_reason == "parent_gate_locked" and v_new.fdr_significant is False
    assert v_risk.cascade_reason == "de_risking_bypass"

    # 8) R4 backbone='elond': e값 online FDR 가 fdr_sig 주체 (임의의존 robust). 위반→유의 / 안정→미유의
    eng8 = AssumptionValidationEngine(fdr_backbone="elond")
    reg8 = np.array([0] * 80 + [1] * 80)
    real8 = np.concatenate([rng.normal(15, 1, 80), rng.normal(20, 1, 80)])
    ve = eng8.validate(pcard, regime_ids=reg8, current_regime=1, realized=real8,
                       assumed_value=15.0, sd=1.0)
    print(f"8) elond backbone: backbone={ve.fdr_backbone} elond_sig={ve.elond_significant} "
          f"fdr_sig={ve.fdr_significant} holds={ve.holds_now}")
    assert ve.fdr_backbone == "elond" and ve.elond_significant is True and ve.fdr_significant is True

    print("assumption_validation_engine self-test PASS "
          "(kind dispatch + 격리 FDR + 부활차단 + falsification compile + ②e-process + ③power게이트 + ①cascade + R4 elond backbone)")
