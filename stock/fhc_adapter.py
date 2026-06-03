"""stock/fhc_adapter.py — equity exposure card(summary.yaml) → core FHCard 어댑터.

frame v3 §M.9 / .coord-fhc-contract-20260603.md §2. equity = FHC scope='sector' 한 인스턴스.
⛔ core schema/lifecycle/bonus 로직은 안 짐(거시 btn-Inv 단일 소유) — card→FHCard 어댑트 +
   construction 이 size_with_bonus 소비만. ★별 schema 만들지 않음(.coord §2 계약).

INV-11(off byte-identical): 본 모듈 import 만으로 회귀 0 — 호출처 0 = 자동 격리, go-live 시
   construction(supervisor 조립부)이 소비. 결정론/risk_gate 무수정.

2-leg 매핑(.coord §2):
  - outcome leg = cs_rank_IC(섹터 횡단면 forward IC) ← summary.indicators_passed[].
  - mediator leg = 섹터 펀더멘털(valuation_cs_z 등, restatement PIT=compute_delay). observable 데이터
    부재 시 eval_mediator(None)=UNKNOWN → fail-closed(INV-3) bonus 0. valuation(DART) 채우면 활성.
"""
from __future__ import annotations

from typing import Optional

from core.assume.fhc import FHCard, MediatorSpec, OutcomeSpec, MediatorTest


def exposure_card_to_fhc(
    summary: dict,
    indicator_id: str,
    *,
    bonus_cap: float,
    mediator_observable: Optional[str] = None,
    mediator_op: str = ">",
    mediator_threshold: float = 0.0,
    mediator_compute_delay: int = 0,
) -> FHCard:
    """summary.yaml(exposure card) 의 indicator 1개 → FHCard(scope='sector').

    bonus_cap = per-asset 천장 C − L1 baseline(§M.6 cap 1-3% / .coord §4). 호출자(construction) 주입.
    mediator_observable=None → 'valuation_cs_z'(섹터 펀더멘털). 데이터 부재 시 eval_mediator 가
       UNKNOWN 반환 → fail-closed(bonus 0). mediator_compute_delay = DART publication lag(restatement PIT).
    """
    inds = {i["id"]: i for i in summary.get("indicators_passed", [])}
    if indicator_id not in inds:
        raise KeyError(f"indicator {indicator_id!r} not in summary.indicators_passed")
    ind = inds[indicator_id]
    hook = next(
        (h for h in summary.get("confidence_hooks", [])
         if h.get("affects_indicator") == indicator_id),
        {},
    )
    att = summary.get("archetype_attestation", {}) or {}
    industry = summary.get("industry", "equity")

    mediator = MediatorSpec(
        observable_ref=mediator_observable or "valuation_cs_z",
        test=MediatorTest.DETERMINISTIC_THRESHOLD,
        op=mediator_op,
        threshold=mediator_threshold,
        compute_delay=mediator_compute_delay,   # DART publication lag (restatement PIT, load-bearing)
    )
    outcome = OutcomeSpec(metric="cs_rank_IC", target_signal_ref=indicator_id)

    falsification = (
        hook.get("reject_signal")
        or "cs_rank_IC e-CUSUM 단측 붕괴 (cross-sectional forward 예측력 소멸)"
    )
    statement = (
        hook.get("confirm_signal")
        or ind.get("notes")
        or f"{indicator_id} cross-sectional forward IC > 0 (peer-relative, long-only)"
    )
    # targets = universe 종목(있으면) / 없으면 industry 단위(supervisor 가 universe 로 확장)
    targets = tuple(summary.get("targets") or (industry,))

    return FHCard(
        card_id=f"{industry}__{indicator_id}",
        scope="sector",
        domain="equity",
        direction="long_tilt",           # cross-sectional 상위 overweight, long-only-implementable
        statement=str(statement)[:500],
        falsification_metric=str(falsification),
        mediator=mediator,
        outcome=outcome,
        bonus_cap=float(bonus_cap),
        targets=targets,
        valid_from=att.get("valid_from"),
        version="v3",
        kind="cross_sectional",
    )
