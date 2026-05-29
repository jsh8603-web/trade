"""core/consensus.py — §4.2 고-스테이크스 consensus 2단 Judge (SO-3/P6).

WHY: 레짐flip·배분변경·누적포지션 임계 초과 시에만 LLM Judge 호출(비용 게이팅).
     routine(평상시)에서는 미발동. risk_gate 항상-on 백스톱.
     TradingAgents portfolio_manager.py:35-58 bind_structured+lesson+Judge 패턴 어댑트.

설계:
- ConsensusJudge.run(context) → ConsensusDecision
  · trigger 미발동 시 is_triggered=False, action="hold", routing=stub
  · trigger 발동 시 LLMRouter(deep=Claude) 경유 2단 Judge
      Layer1: 구조화 판단 (lessons 주입)
      Layer2: risk_gate 백스톱 (override 가능)
- path-attribution 결정레코드 (DecisionRecord) 기록
- credential 없음 → stub (실 LLM 미호출, deterministic)

SACRED:
- coin 라이브·Phase0~5 본체 미변경
- LLMRouter C2 daily_cap 경유 (우회 금지)
- risk_gate 항상-on (consensus 결과가 risk_gate 기각 시 hold 강제)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("core.consensus")


# ---------------------------------------------------------------------------
# ConsensusContext — Judge 입력 컨텍스트
# ---------------------------------------------------------------------------

@dataclass
class ConsensusContext:
    """§4.2 Judge 호출 컨텍스트."""
    # 발동 조건 플래그
    regime_changed: bool = False
    allocation_change_pct: float = 0.0
    cumulative_position_pct: float = 0.0

    # 시장/포트폴리오 상태 (Judge 프롬프트 입력)
    current_weights: Dict[str, float] = field(default_factory=dict)
    proposed_weights: Dict[str, float] = field(default_factory=dict)
    macro_view: str = ""

    # lessons (TradingAgents portfolio_manager.py:35-58 패턴)
    past_lessons: str = ""  # 과거 의사결정 교훈

    # 타임스탬프
    as_of: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# ConsensusDecision — Judge 출력
# ---------------------------------------------------------------------------

@dataclass
class ConsensusDecision:
    """§4.2 Judge 최종 결정."""
    action: str             # "approve" | "hold" | "reduce"
    is_triggered: bool      # 고-스테이크스 발동 여부
    confidence: float       # 0~1
    reasoning: str          # 결정 근거
    routing: str            # "llm" | "stub" | "risk_gate_override"
    as_of: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# DecisionRecord — path-attribution 기록
# ---------------------------------------------------------------------------

@dataclass
class DecisionRecord:
    """path-attribution 결정레코드."""
    context: ConsensusContext
    decision: ConsensusDecision
    risk_gate_passed: bool
    final_action: str       # risk_gate override 적용 후 최종


# ---------------------------------------------------------------------------
# ConsensusJudge
# ---------------------------------------------------------------------------

class ConsensusJudge:
    """§4.2 고-스테이크스 consensus 2단 Judge.

    Layer1: LLM Judge (TradingAgents bind_structured+lesson 어댑트)
    Layer2: risk_gate 항상-on 백스톱

    routine(평상시) = is_high_stakes=False → stub 즉시 반환(LLM 미호출, 비용 0).
    """

    def __init__(
        self,
        llm_router=None,      # LLMRouter(deep=Claude) — None이면 stub
        risk_gate=None,       # Phase2 RiskGate 인스턴스
        allocation_threshold: float = 0.10,
        cumulative_threshold: float = 0.25,
    ):
        self._router = llm_router
        self._risk_gate = risk_gate
        self._alloc_thresh = allocation_threshold
        self._cumul_thresh = cumulative_threshold
        self._records: List[DecisionRecord] = []

    # ------------------------------------------------------------------
    # 발동 판정 (§4.2 고-스테이크스 기준)
    # ------------------------------------------------------------------

    def is_high_stakes(self, ctx: ConsensusContext) -> bool:
        """고-스테이크스 발동 여부 — 레짐flip·배분변경·누적포지션."""
        if ctx.regime_changed:
            return True
        if ctx.allocation_change_pct >= self._alloc_thresh:
            return True
        if ctx.cumulative_position_pct >= self._cumul_thresh:
            return True
        return False

    # ------------------------------------------------------------------
    # Layer1: LLM Judge (TradingAgents 패턴 어댑트)
    # ------------------------------------------------------------------

    def _judge_via_llm(self, ctx: ConsensusContext) -> ConsensusDecision:
        """LLMRouter deep=Claude 경유 2단 Judge.

        credential 없음 / router=None → stub 반환 (deterministic).
        TradingAgents portfolio_manager.py:35-58: bind_structured+lessons_line+Judge 패턴.
        """
        if self._router is None:
            return self._stub_decision(ctx, routing="stub")

        # lessons 주입 (TradingAgents :36-40 패턴)
        lessons_line = (
            f"- Past lessons:\n{ctx.past_lessons}\n"
            if ctx.past_lessons
            else ""
        )

        prompt = (
            f"[Portfolio Consensus Judge — rounds=1]\n"
            f"Regime changed: {ctx.regime_changed}\n"
            f"Allocation delta: {ctx.allocation_change_pct:.1%}\n"
            f"Cumulative position: {ctx.cumulative_position_pct:.1%}\n"
            f"Macro view: {ctx.macro_view}\n"
            f"Current weights: {ctx.current_weights}\n"
            f"Proposed weights: {ctx.proposed_weights}\n"
            f"{lessons_line}"
            f"Decide: approve|hold|reduce. Be decisive."
        )

        try:
            result = self._router.route_with_meta(
                prompt,
                high_risk=True,  # 고-스테이크스 → deep(Claude) 강제 트리거
            )
            text = result.text.strip().lower()
            action = "approve" if "approve" in text else (
                "reduce" if "reduce" in text else "hold"
            )
            return ConsensusDecision(
                action=action,
                is_triggered=True,
                confidence=0.7,
                reasoning=result.text[:200],
                routing="llm",
            )
        except Exception as exc:
            logger.warning("LLM Judge 실패 → stub 대체: %s", exc)
            return self._stub_decision(ctx, routing="stub")

    # ------------------------------------------------------------------
    # Layer2: risk_gate 백스톱
    # ------------------------------------------------------------------

    def _apply_risk_gate(self, decision: ConsensusDecision, ctx: ConsensusContext) -> tuple[bool, str]:
        """risk_gate 항상-on 백스톱. approve라도 risk_gate 거부 시 hold 강제."""
        if self._risk_gate is None:
            return True, decision.action

        try:
            # risk_gate.check() 에 consensus action 을 Decision dict 로 변환
            gate_input = {
                "decision": "buy" if decision.action == "approve" else "hold",
                "confidence": decision.confidence,
                "_is_buy_candidate": decision.action == "approve",
            }
            result = self._risk_gate.check(gate_input)
            if result and getattr(result, "approved", True):
                return True, decision.action
            # risk_gate 거부 → hold 강제
            logger.info("risk_gate 백스톱 — consensus %s → hold 강제", decision.action)
            return False, "hold"
        except Exception as exc:
            logger.warning("risk_gate 호출 실패 — hold 강제: %s", exc)
            return False, "hold"

    # ------------------------------------------------------------------
    # stub 결정 (routine 미발동 or LLM 없음)
    # ------------------------------------------------------------------

    @staticmethod
    def _stub_decision(ctx: ConsensusContext, routing: str = "stub") -> ConsensusDecision:
        """LLM 없음 or routine — deterministic stub."""
        return ConsensusDecision(
            action="hold",
            is_triggered=False,
            confidence=1.0,
            reasoning="stub — consensus 미발동 or credential 부재",
            routing=routing,
        )

    # ------------------------------------------------------------------
    # 메인 진입점
    # ------------------------------------------------------------------

    def run(self, ctx: ConsensusContext) -> ConsensusDecision:
        """§4.2 consensus 실행.

        routine(is_high_stakes=False) → stub 즉시 반환 (LLM 미호출).
        고-스테이크스 → LLM Judge → risk_gate 백스톱 → DecisionRecord 기록.
        """
        if not self.is_high_stakes(ctx):
            decision = self._stub_decision(ctx, routing="stub")
            # routine 에도 path-attribution 기록
            self._records.append(DecisionRecord(
                context=ctx,
                decision=decision,
                risk_gate_passed=True,
                final_action=decision.action,
            ))
            return decision

        # Layer1: LLM Judge
        decision = self._judge_via_llm(ctx)
        decision.is_triggered = True

        # Layer2: risk_gate 백스톱
        gate_ok, final_action = self._apply_risk_gate(decision, ctx)

        if not gate_ok:
            decision.routing = "risk_gate_override"

        # path-attribution 기록
        record = DecisionRecord(
            context=ctx,
            decision=decision,
            risk_gate_passed=gate_ok,
            final_action=final_action,
        )
        self._records.append(record)

        # 최종 action 반영
        decision.action = final_action
        return decision

    @property
    def decision_records(self) -> List[DecisionRecord]:
        """path-attribution 결정레코드 목록."""
        return list(self._records)
