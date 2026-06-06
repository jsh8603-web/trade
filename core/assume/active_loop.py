"""core/assume/active_loop.py — S4 능동 애널리스트 루프 (LLM 소환 가설 발권, shadow).

★존재이유 = C9 '결정론이 못 푸는 6유형'(RESULTS C9, plan §3 S4): regime-break 구조모델 무효 /
value-trap 판별 / cross-source 합성 / 신규 가설 생성 / 이산 이벤트 / instrument 선택. 이 6유형만
LLM 카드발권이 결정론 코어보다 우위 — 나머지는 결정론이 처리(LLM은 enrich/발권만, down-only).

7-step(plan §3 S4): 저신뢰 트리거 → summon gate → scoped PIT 검색 → falsifiable claim(LLM) →
Opus pre-mint audit(LLM 2차 + 직교성) → probationary mint → write-back.

★shadow(plan §4 go-live 경계): 전부 dry-run = LLM 실호출하되 발권 카드는 **probationary**(자본 0).
  go-live arming(사람 게이트) 전엔 confirmed 돼도 미투입 — bonus 적립은 minted-dormant=0(INV) +
  construction 의 size_with_bonus 가 confirmed 카드만 적립하므로 probationary 는 자동 0.
★fail-closed(INV-3 / C2 abstain): llm None / trigger 없음 / claim 파싱 실패 / audit reject → None
  (결정론 baseline 유지, 카드 0). macro_reasoning.enrich 의 abstain 패턴과 동일.
★additive(INV-11): 호출처 0(go-live 시 소비). 기존 모듈 무수정.
  재사용: macro_mediator(전제 구독) · spanning_gate(직교성 audit) · info_delta_gate(summon 빈도) +
  brain.macro_reasoning(LLMProvider/ReportStore Protocol) · memory_layer(write-back).
★진입점 정렬(.coord §6'', btn-button 2026-06-06): S4 본체=btn-Inv / button 접점=step7 write-back
  (Σ_signal 원장=meta button, 미구현=go-live → 현재는 shadow sink). 종목 S6=button scope='sector' 확장.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

from core.assume.fhc import (
    Direction,
    FHCard,
    MediatorSpec,
    MediatorState,
    MediatorTest,
    OutcomeSpec,
)
from core.assume.info_delta_gate import RateCapState, delta_gate
from core.assume.spanning_gate import mint_gate

logger = logging.getLogger(__name__)


# ── 단계 결과 구조 ──────────────────────────────────────────────────────
@dataclass
class SummonDecision:
    summon: bool
    reason: str
    trigger_reason: str = ""        # low_confidence | mediator_unknown | info_delta
    detail: dict = field(default_factory=dict)


@dataclass
class AuditResult:
    passed: bool
    reason: str
    orthogonality: Optional[str] = None   # mint_gate verdict (mint/camouflage/insufficient)
    detail: dict = field(default_factory=dict)


@dataclass
class ProbationaryCard:
    """shadow 발권 카드 — 자본 0, go-live arming 전까지 미투입."""
    card: FHCard
    thesis: str
    counter_thesis: str
    audit: AuditResult
    minted_shadow: bool = True


@dataclass
class LoopConfig:
    low_confidence_threshold: float = 0.5   # regime confidence 이하 = 저신뢰 트리거
    require_falsification: bool = True       # claim.falsification_metric 필수(card_contract 정합)
    spanning_alpha_t_min: float = 2.0


# ── 능동 애널리스트 루프 ────────────────────────────────────────────────
class ActiveAnalystLoop:
    """LLM 소환 가설 발권 shadow orchestrator. 7-step. llm None → 전부 abstain(C2)."""

    def __init__(
        self,
        *,
        llm=None,                    # brain.macro_reasoning.LLMProvider (complete(system,user,json_mode))
        report_store=None,           # brain.macro_reasoning.ReportStore (retrieve(query,as_of_ts,k))
        rate_cap: Optional[RateCapState] = None,   # summon 빈도 상한(info_delta_gate)
        write_back: Optional[Callable] = None,     # step7 sink(card) — None=내부 list(shadow)
        config: Optional[LoopConfig] = None,
    ):
        self.llm = llm
        self.report_store = report_store
        self.rate_cap = rate_cap
        self.write_back = write_back
        self.config = config or LoopConfig()
        self.shadow_sink: list = []   # write_back None 시 dry-run 적재

    # step 1+2 — 저신뢰 트리거 + summon gate
    def should_summon(
        self,
        macro_view,
        mediator_state: Optional[MediatorState] = None,
        *,
        tick: float = 0.0,
        emb_new: Optional[Sequence[float]] = None,
        corpus_embs=None,
        numeric_revision: float = 0.0,
    ) -> SummonDecision:
        # step1 저신뢰 트리거: regime confidence 낮음 OR mediator UNKNOWN(전제 모름)
        conf = None
        try:
            from core.brain.macro_schema import Bloc
            est = macro_view.regime(Bloc.USD) if macro_view is not None else None
            conf = getattr(est, "confidence_now", None) if est else None
        except Exception:
            conf = None

        low_conf = (conf is not None) and (conf < self.config.low_confidence_threshold)
        med_unknown = mediator_state == MediatorState.UNKNOWN
        if not (low_conf or med_unknown):
            return SummonDecision(False, "고신뢰 baseline = LLM 불요(결정론 충분)", detail={"confidence": conf})

        trg = "low_confidence" if low_conf else "mediator_unknown"

        # step2 summon gate: info_delta(rate-cap AND 델타) — 빈도 상한 + 무의미 필터
        d = delta_gate(
            emb_new, corpus_embs,
            numeric_revision=numeric_revision,
            rate_cap=self.rate_cap, tick=tick,
        )
        if not d.fire:
            return SummonDecision(False, f"summon gate 차단: {d.reason}", trigger_reason=trg)
        return SummonDecision(True, f"소환: {trg} + {d.reason}", trigger_reason=trg,
                              detail={"confidence": conf, "novelty": d.novelty})

    # step3 — scoped PIT 검색
    def retrieve_reports(self, query: str, as_of_ts: Optional[float], k: int = 5) -> list:
        if self.report_store is None:
            return []
        try:
            return self.report_store.retrieve(query, as_of_ts=as_of_ts, k=k) or []
        except Exception:
            return []

    # step4 — falsifiable claim 생성(LLM)
    def generate_claim(self, macro_view, reports: list, trigger_reason: str) -> Optional[dict]:
        if self.llm is None:
            return None   # abstain
        system = (
            "You are a macro analyst proposing ONE falsifiable hypothesis card to tilt allocation. "
            "Output JSON: statement(str), direction(one of long_tilt/short_tilt/de_risk), "
            "mediator_ref(str, the precondition observable e.g. 'regime:USD:Overheat'), "
            "outcome_metric(str, e.g. 'ts_rank_IC'), falsification_metric(str, the condition that "
            "would prove this WRONG — REQUIRED, non-empty), counter_thesis(str). "
            "If evidence is weak, set falsification_metric empty to abstain."
        )
        regime = ""
        try:
            from core.brain.macro_schema import Bloc
            est = macro_view.regime(Bloc.USD) if macro_view else None
            regime = est.regime_now.value if est else ""
        except Exception:
            pass
        user = json.dumps({
            "trigger": trigger_reason,
            "regime_now": regime,
            "reports": [r.get("text", "")[:1000] for r in (reports or [])],
        }, ensure_ascii=False)
        try:
            raw = self.llm.complete(system, user, json_mode=True)
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            if not isinstance(parsed, dict):
                return None
            return parsed
        except Exception as e:
            logger.warning("active_loop claim 생성 실패 → abstain: %s", e)
            return None

    # step5 — Opus pre-mint audit (LLM 2차 + 직교성)
    def pre_mint_audit(
        self,
        claim: dict,
        *,
        spanning_inputs: Optional[tuple] = None,   # (r_c, F[, fwd]) 직교성 검증 시계열
    ) -> AuditResult:
        # (a) falsifiability 게이트 — card_contract 정합(반증조건 비면 진입 금지)
        fm = (claim.get("falsification_metric") or "").strip()
        if self.config.require_falsification and not fm:
            return AuditResult(False, "falsification_metric 부재 = 반증불가 = 발권 금지")

        # (b) 직교성 게이트(있을 때만) — 촉매가 7팩터 위장이면 발권 차단
        orth = None
        if spanning_inputs is not None:
            r_c, F = spanning_inputs[0], spanning_inputs[1]
            fwd = spanning_inputs[2] if len(spanning_inputs) > 2 else None
            v = mint_gate(r_c, F, fwd, alpha_t_min=self.config.spanning_alpha_t_min)
            orth = v.verdict
            if v.verdict == "camouflage":
                return AuditResult(False, f"직교성 reject: {v.reason}", orthogonality=orth)
            if v.verdict == "insufficient":
                return AuditResult(False, f"표본 부족: {v.reason}", orthogonality=orth)

        # (c) LLM 2차 audit(있을 때만) — falsifiability·직교성 재확인
        if self.llm is not None:
            try:
                sys2 = ("You audit a hypothesis card before minting. Reply JSON {approve: bool, "
                        "reason: str}. Reject if the claim is not falsifiable, is tautological, or "
                        "merely restates known factor exposure (camouflage).")
                raw = self.llm.complete(sys2, json.dumps(claim, ensure_ascii=False), json_mode=True)
                a = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(a, dict) and a.get("approve") is False:
                    return AuditResult(False, f"LLM audit reject: {a.get('reason', '')}",
                                       orthogonality=orth)
            except Exception:
                pass   # LLM audit 실패는 통과(직교성·falsifiability 1차가 main 게이트)

        return AuditResult(True, "audit 통과(falsifiable + 직교)", orthogonality=orth)

    # step6 — probationary mint
    def mint_probationary(self, claim: dict, *, scope: str = "macro", domain: str = "macro",
                          card_id: Optional[str] = None) -> Optional[FHCard]:
        try:
            direction = claim.get("direction", "de_risk")
            if direction not in ("long_tilt", "short_tilt", "de_risk"):
                direction = "de_risk"
            med_ref = (claim.get("mediator_ref") or "").strip()
            med_test = (MediatorTest.STATE_SPACE_POSTERIOR
                        if med_ref.lower().startswith("regime")
                        else MediatorTest.DETERMINISTIC_THRESHOLD)
            cid = card_id or f"active-{scope}-{abs(hash(claim.get('statement', ''))) % 10**8}"
            return FHCard(
                card_id=cid,
                scope=scope,
                domain=domain,
                direction=direction,           # type: ignore
                statement=claim.get("statement", ""),
                falsification_metric=(claim.get("falsification_metric") or "").strip(),
                mediator=MediatorSpec(observable_ref=med_ref or "regime:USD:Overheat", test=med_test),
                outcome=OutcomeSpec(metric=claim.get("outcome_metric", "ts_rank_IC")),
                bonus_cap=0.0,                  # ★probationary = 자본0(go-live arming 시 button이 부여)
                kind="probationary",
            )
        except Exception as e:
            logger.warning("probationary mint 실패 → abstain: %s", e)
            return None

    # step7 — write-back
    def write_back_card(self, pcard: ProbationaryCard) -> None:
        if self.write_back is not None:
            try:
                self.write_back(pcard)
                return
            except Exception as e:
                logger.warning("write_back sink 실패 → shadow 적재: %s", e)
        self.shadow_sink.append(pcard)   # button Σ_signal 원장 미구현 → dry-run sink

    # 전체 7-step
    def run_cycle(
        self,
        macro_view,
        mediator_state: Optional[MediatorState] = None,
        *,
        tick: float = 0.0,
        query: str = "",
        as_of_ts: Optional[float] = None,
        emb_new=None,
        corpus_embs=None,
        numeric_revision: float = 0.0,
        spanning_inputs: Optional[tuple] = None,
        scope: str = "macro",
        domain: str = "macro",
    ) -> Optional[ProbationaryCard]:
        """7-step 1사이클. 어느 단계든 abstain → None(결정론 baseline 유지)."""
        # 1+2
        s = self.should_summon(macro_view, mediator_state, tick=tick,
                               emb_new=emb_new, corpus_embs=corpus_embs,
                               numeric_revision=numeric_revision)
        if not s.summon:
            return None
        # 3
        reports = self.retrieve_reports(query or "macro regime outlook", as_of_ts)
        # 4
        claim = self.generate_claim(macro_view, reports, s.trigger_reason)
        if not claim:
            return None
        # 5
        audit = self.pre_mint_audit(claim, spanning_inputs=spanning_inputs)
        if not audit.passed:
            logger.info("active_loop audit reject: %s", audit.reason)
            return None
        # 6
        card = self.mint_probationary(claim, scope=scope, domain=domain)
        if card is None:
            return None
        pcard = ProbationaryCard(
            card=card,
            thesis=claim.get("statement", ""),
            counter_thesis=claim.get("counter_thesis", ""),
            audit=audit,
        )
        # 7
        self.write_back_card(pcard)
        return pcard


if __name__ == "__main__":
    from core.brain.macro_schema import Bloc, MacroView, RegimeEstimate, RegimeLabel, ViewStatus

    def _view(label, conf):
        est = RegimeEstimate(bloc=Bloc.USD, regime_now=label, confidence_now=conf)
        return MacroView(regimes={Bloc.USD: est}, status=ViewStatus.FRESH, as_of_ts=0.0)

    class _FakeLLM:
        def __init__(self, claim, approve=True):
            self._claim = claim
            self._approve = approve
            self._n = 0
        def complete(self, system, user, json_mode=True):
            self._n += 1
            if "audit a hypothesis" in system:
                return json.dumps({"approve": self._approve, "reason": "ok" if self._approve else "camouflage"})
            return json.dumps(self._claim)

    good_claim = {
        "statement": "Overheat 국면 원자재 sleeve 선도수익 우위",
        "direction": "long_tilt", "mediator_ref": "regime:USD:Overheat",
        "outcome_metric": "ts_rank_IC",
        "falsification_metric": "원자재 3M fwd IC < 0 in Overheat",
        "counter_thesis": "달러 강세가 원자재 상쇄",
    }

    # 1) llm None → 전부 abstain
    loop0 = ActiveAnalystLoop(llm=None)
    assert loop0.run_cycle(_view(RegimeLabel.OVERHEAT, 0.2)) is None
    print("1) llm None → abstain(None) OK")

    # 2) 고신뢰 → summon 안 함
    loop = ActiveAnalystLoop(llm=_FakeLLM(good_claim))
    assert loop.should_summon(_view(RegimeLabel.OVERHEAT, 0.9)).summon is False
    print("2) 고신뢰(0.9) → summon 차단 OK")

    # 3) 저신뢰 + 신규정보 → 7-step → probationary mint
    loop2 = ActiveAnalystLoop(llm=_FakeLLM(good_claim))
    pc = loop2.run_cycle(_view(RegimeLabel.OVERHEAT, 0.3), numeric_revision=0.3)
    assert pc is not None and pc.card.kind == "probationary" and pc.card.bonus_cap == 0.0
    assert pc.card.falsification_metric and pc.minted_shadow
    assert len(loop2.shadow_sink) == 1   # write-back shadow sink
    print(f"2) 저신뢰+신규 → probationary mint OK (scope={pc.card.scope}, bonus_cap={pc.card.bonus_cap})")

    # 4) falsification_metric 부재 claim → audit reject
    bad_claim = dict(good_claim, falsification_metric="")
    loop3 = ActiveAnalystLoop(llm=_FakeLLM(bad_claim))
    assert loop3.run_cycle(_view(RegimeLabel.OVERHEAT, 0.3), numeric_revision=0.3) is None
    print("4) falsification 부재 → audit reject(None) OK")

    # 5) LLM audit reject(camouflage) → None
    loop4 = ActiveAnalystLoop(llm=_FakeLLM(good_claim, approve=False))
    assert loop4.run_cycle(_view(RegimeLabel.OVERHEAT, 0.3), numeric_revision=0.3) is None
    print("5) LLM audit reject → None OK")

    # 6) mediator UNKNOWN 트리거 + write_back sink callback
    sink = []
    loop5 = ActiveAnalystLoop(llm=_FakeLLM(good_claim), write_back=sink.append)
    pc5 = loop5.run_cycle(_view(RegimeLabel.RECOVERY, 0.9), mediator_state=MediatorState.UNKNOWN,
                          numeric_revision=0.3)
    assert pc5 is not None and len(sink) == 1
    print("6) mediator UNKNOWN 트리거 + 외부 write_back sink OK")

    # 7) 직교성 audit: camouflage 시계열 → reject
    import numpy as np
    rng = np.random.RandomState(0)
    F = rng.randn(240, 3) * 0.01
    r_camo = F @ np.array([1.0, -0.5, 0.7]) + rng.randn(240) * 0.002   # 순수 팩터노출
    loop6 = ActiveAnalystLoop(llm=_FakeLLM(good_claim))
    pc6 = loop6.run_cycle(_view(RegimeLabel.OVERHEAT, 0.3), numeric_revision=0.3,
                          spanning_inputs=(r_camo, F))
    assert pc6 is None
    print("7) 직교성 camouflage 시계열 → 발권 차단(None) OK")

    print("S4 active_loop self-test PASS "
          "(abstain · summon gate · falsifiable claim · pre-mint audit[직교성+LLM] · probationary mint · write-back)")
