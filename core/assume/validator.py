"""core/assume/validator.py — 검증엔진 dispatch + 결과 영속 (CL-1, 축A·D).

btn-button `AssumptionValidationEngine`(BB-4, R4/R5 보강 완료: e-process·e-LOND·hierarchical
cascade·power 게이트·per-domain decay) 위에 얇게 얹는 orchestration. 자체 통계 0 — 전부 위임.

책임 4개 (DESIGN-codlearn-v2.md §2.2, ckpt -E):
 (a) engine.validate dispatch  — card.kind(parametric/structural) → holds_now/fdr_significant.
 (b) ★측정깨짐 ≠ 정의틀림     — evidence.contract(data_contract IA-2) 위반이면 validate SKIP.
     incident verdict 반환(holds_now=None, fdr_significant=False) → UpdateController 가 keep 으로
     처리(변경 트리거 금지). 측정 incident 를 "가정 틀림"으로 오판하면 멀쩡한 정의가 은퇴됨.
 (c) RulePerformance.log       — (rule=card@version, regime, sector, regime_model_version, ic, n)
     축A 영속. dormant rule 부활 판정 substrate.
 (d) fdr_backbone='elond' 기본 — `AssumptionValidator.default()` = 임의의존 robust e값 online FDR.

per-domain alpha-wealth 격리(claude R1)는 engine 내부에서 이미 처리(stream key=(domain, id)).
validator 는 도메인 pooling 을 만들지 않고 그대로 통과시키기만 한다.

결정 X — 관측·산출만. holds/significant 판정은 engine, 변경 결정은 UpdateController.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from core.assume.card_contract import AssumptionCardLike
from core.rules.ledger import RulePerformance
from core.structure.assumption_validation_engine import (
    AssumptionValidationEngine,
    ValidationVerdict,
)


@dataclass
class Evidence:
    """validate 입력 묶음. parametric/structural 분기 + cascade + 측정계약 + 축A 메타.

    duck-typed: validate 는 getattr 로 읽으므로 같은 속성을 가진 임의 객체도 허용.
    contract = data_contract.ContractResult (또는 .passed/.incidents 를 가진 객체).
    """
    # parametric
    realized: Any = None
    assumed_value: Optional[float] = None
    sd: Optional[float] = None
    # structural
    predictions: Any = None
    outcomes: Any = None
    # cascade (hierarchical 부모게이트 + de-risking bypass)
    parent_id: Optional[str] = None
    action: str = "new_entry"
    # ★측정 계약 (위반 시 validate skip)
    contract: Any = None
    # 축A 영속 메타 (없으면 card/verdict 에서 파생)
    sector: Optional[str] = None
    regime_model_version: Optional[str] = None
    ic: Optional[float] = None
    n: Optional[int] = None


def _structural_ic(predictions, outcomes) -> Optional[tuple[float, int]]:
    """structural 카드 IC = corr(predictions, outcomes). 분산 0/길이부족 → (0.0, n)."""
    if predictions is None or outcomes is None:
        return None
    p = np.asarray(predictions, dtype=float)
    o = np.asarray(outcomes, dtype=float)
    if p.size < 2 or o.size != p.size:
        return (0.0, int(p.size))
    if p.std() == 0.0 or o.std() == 0.0:
        return (0.0, int(p.size))
    return (float(np.corrcoef(p, o)[0, 1]), int(p.size))


class AssumptionValidator:
    """engine.validate dispatch + 측정 incident skip + RulePerformance 영속."""

    def __init__(self, engine: AssumptionValidationEngine, perf: RulePerformance):
        self.engine = engine
        self.perf = perf

    @classmethod
    def default(cls, *, perf: Optional[RulePerformance] = None,
                fdr_backbone: str = "elond", **engine_kw) -> "AssumptionValidator":
        """권장 기본 구성: e-LOND backbone(임의의존 robust) + 새 RulePerformance."""
        return cls(AssumptionValidationEngine(fdr_backbone=fdr_backbone, **engine_kw),
                   perf or RulePerformance())

    def _incident_verdict(self, card: AssumptionCardLike, contract: Any) -> ValidationVerdict:
        """측정 incident = 변경 트리거 금지 no-op verdict (holds 미지, fdr 무유의)."""
        incidents = list(getattr(contract, "incidents", []) or [])
        fmeta = (getattr(card, "falsification_metric", "") or "").strip()
        return ValidationVerdict(
            assumption_id=card.id, domain=card.domain, kind=card.kind,
            holds_now=None,                # 측정 깨짐 → 성립 여부 판정 불가
            confidence_now=0.0,
            p_value=1.0, alpha_t=0.0,
            fdr_significant=False,         # ★incident 를 "가정 틀림"으로 승격 금지
            by_regime={},
            falsifiable=bool(fmeta),
            evidence={"incident": True,
                      "data_contract_incidents": incidents,
                      "skip_reason": "DATA_CONTRACT_VIOLATION (측정깨짐 ≠ 정의틀림)"},
            protectable=False,
        )

    def _log_perf(self, card: AssumptionCardLike, verdict: ValidationVerdict,
                  ev: Any, current_regime: int) -> tuple[float, int]:
        """축A 영속. ic/n = evidence 명시값 우선, 없으면 structural corr / signed confidence 파생."""
        ic = getattr(ev, "ic", None)
        n = getattr(ev, "n", None)
        if ic is None or n is None:
            sic = _structural_ic(getattr(ev, "predictions", None), getattr(ev, "outcomes", None))
            if sic is not None:
                ic = ic if ic is not None else sic[0]
                n = n if n is not None else sic[1]
            else:
                # parametric/fallback: holds=True → +conf, False → -conf
                conf = float(verdict.confidence_now)
                ic = ic if ic is not None else (conf if verdict.holds_now else -conf)
                n = n if n is not None else int(verdict.by_regime.get(current_regime, {}).get("n", 0))
        self.perf.log(
            rule_version=f"{card.id}@{card.version}",
            regime_id=current_regime,
            sector=(getattr(ev, "sector", None) or card.scope),
            regime_model_version=(getattr(ev, "regime_model_version", None)
                                  or getattr(card, "regime_model_version", None)),
            ic=float(ic), n=int(n))
        return float(ic), int(n)

    def validate(self, card: AssumptionCardLike, evidence: Any, *,
                 regime_ids, current_regime: int) -> ValidationVerdict:
        """card + evidence → ValidationVerdict. 측정 incident 면 skip(no-op verdict)."""
        # (b) ★측정깨짐 ≠ 정의틀림: data_contract 위반 → validate skip
        contract = getattr(evidence, "contract", None)
        if contract is not None and not getattr(contract, "passed", True):
            return self._incident_verdict(card, contract)

        # (a) engine dispatch (per-domain alpha-wealth 격리 = engine 내부 stream key)
        verdict = self.engine.validate(
            card, regime_ids=regime_ids, current_regime=current_regime,
            realized=getattr(evidence, "realized", None),
            assumed_value=getattr(evidence, "assumed_value", None),
            predictions=getattr(evidence, "predictions", None),
            outcomes=getattr(evidence, "outcomes", None),
            sd=getattr(evidence, "sd", None),
            parent_id=getattr(evidence, "parent_id", None),
            action=getattr(evidence, "action", "new_entry"))

        # (c) 축A 영속
        self._log_perf(card, verdict, evidence, current_regime)
        return verdict


if __name__ == "__main__":
    from core.assume.card_contract import BaseAssumptionFields
    rng = np.random.default_rng(11)

    val = AssumptionValidator.default()
    assert val.engine.fdr_backbone == "elond", "default = elond backbone"
    print(f"0) default 구성 OK: backbone={val.engine.fdr_backbone}")

    # 1) parametric: regime1 평균이동(깸) → fdr_significant + 축A 1행 영속
    pcard = BaseAssumptionFields(
        id="commodity.carry_normal_range", version="v1", kind="parametric", scope="asset",
        domain="commodity", statement="carry 정상범위=θ",
        falsification_metric="carry CUSUM 이탈 + variance-ratio")
    n = 80
    reg = np.array([0] * n + [1] * n)
    realized = np.concatenate([rng.normal(15, 1, n), rng.normal(20, 1, n)])
    ev1 = Evidence(realized=realized, assumed_value=15.0, sd=1.0, sector="energy")
    v1 = val.validate(pcard, ev1, regime_ids=reg, current_regime=1)
    print(f"1) parametric r1: holds={v1.holds_now} fdr={v1.fdr_significant} backbone={v1.fdr_backbone}")
    assert v1.holds_now is False and v1.fdr_significant is True
    rows = val.perf.query(rule_version="commodity.carry_normal_range@v1")
    assert len(rows) == 1 and rows[0].sector == "energy", rows
    print(f"   축A 영속 OK: {len(rows)}행 sector={rows[0].sector} ic={rows[0].ic:.3f} n={rows[0].n}")

    # 2) structural: IC = corr(pred,out). 잘 맞으면 holds + 양의 IC
    scard = BaseAssumptionFields(
        id="macro.yc_term_premium", version="v1", kind="structural", scope="macro",
        domain="macro", statement="장단기 역전 → term premium 메커니즘",
        falsification_metric="prequential ΔBrier + mechanism: ACM term premium 독립 검증")
    pred = rng.normal(0, 0.3, 60)
    out = pred + rng.normal(0, 0.15, 60)
    v2 = val.validate(scard, Evidence(predictions=pred, outcomes=out),
                      regime_ids=np.zeros(60, int), current_regime=0)
    rows2 = val.perf.query(rule_version="macro.yc_term_premium@v1")
    print(f"2) structural: holds={v2.holds_now} IC={rows2[0].ic:.3f} (corr 파생)")
    assert v2.holds_now is True and rows2[0].ic > 0.5, rows2[0].ic

    # 3) ★측정 incident skip — contract.passed=False → no-op verdict + 영속 X
    class _BrokenContract:
        passed = False
        incidents = [{"check": "in_range", "column": "per", "n_failed": 3, "sample": "999"}]
    before = len(val.perf.query())
    v3 = val.validate(pcard, Evidence(realized=realized, assumed_value=15.0, sd=1.0,
                                      contract=_BrokenContract()),
                      regime_ids=reg, current_regime=1)
    after = len(val.perf.query())
    print(f"3) incident skip: holds={v3.holds_now} fdr={v3.fdr_significant} "
          f"incident={v3.evidence.get('incident')} perf증가={after - before}")
    assert v3.holds_now is None and v3.fdr_significant is False
    assert v3.evidence["incident"] is True and after == before, "incident 은 영속/변경 금지"

    # 4) contract.passed=True → 정상 통과 (incident 아님)
    class _OkContract:
        passed = True
        incidents = []
    v4 = val.validate(pcard, Evidence(realized=realized, assumed_value=15.0, sd=1.0,
                                      contract=_OkContract()),
                      regime_ids=reg, current_regime=1)
    assert v4.holds_now is False, "정상계약 = engine 통과"
    print(f"4) ok-contract 통과 OK: holds={v4.holds_now}")

    # 5) per-domain 격리 통과 — commodity/macro 스트림 키 분리 (engine 책임, validator 통과 확인)
    s_cm = val.engine.stream_state("commodity", "commodity.carry_normal_range")
    s_mac = val.engine.stream_state("macro", "macro.yc_term_premium")
    assert s_cm["isolated_key"] != s_mac["isolated_key"]
    print(f"5) per-domain 격리 OK: {s_cm['isolated_key']} ≠ {s_mac['isolated_key']}")

    print("CL-1 validator self-test PASS "
          "(elond default + dispatch + 축A영속 + ★incident skip + 격리통과)")
