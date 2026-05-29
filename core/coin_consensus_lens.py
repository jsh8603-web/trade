"""core/coin_consensus_lens.py — consensus 코인 렌즈 (SO-6/PR).

WHY: Phase6 §4.2 ConsensusJudge에 코인 전용 렌즈 어댑트.
     주식 consensus(DCF·펀더멘털)와 달리 코인은
     on-chain / sentiment(FGI) / funding / technical 신호 사용.
     DCF 없음 (코인 특성).

변형표 #5 (Phase R):
- CoinConsensusLens: ConsensusJudge 서브클래스
- 코인 고-스테이크스 발동 조건: 레짐flip·배분변경·누적포지션 (동일)
- 프롬프트 렌즈: on-chain/FGI/funding/technical (DCF 미포함)
- 타임아웃 짧게 (코인 변동성 빠름)
- risk_gate 항상-on 백스톱 보존 (§4.2 불변식)

SACRED:
- consensus.py 본체 미변경 (subclass만)
- risk_gate 우회 금지 (항상-on)
- execute_trade 실주문 미변경
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from core.consensus import ConsensusContext, ConsensusDecision, ConsensusJudge

logger = logging.getLogger("core.coin_consensus_lens")

# 코인 렌즈 타임아웃 (초) — 주식보다 짧게
COIN_LENS_TIMEOUT_SEC = 15.0  # vs 주식 30s


@dataclass
class CoinLensData:
    """코인 consensus 렌즈 입력 데이터 (DCF 없음)."""
    # on-chain
    whale_inflow_usd: float = 0.0       # 고래 거래소 유입 (음수=유출)
    exchange_reserve_change_pct: float = 0.0  # 거래소 잔고 변화율

    # sentiment
    fear_greed_index: Optional[float] = None   # 0~100 (극공포=0, 극탐욕=100)

    # funding / derivatives
    funding_rate: float = 0.0           # 펀딩비 (양수=롱 우세)
    open_interest_change_pct: float = 0.0  # OI 변화율

    # technical (기술적 지표)
    rsi_14: Optional[float] = None      # RSI 14
    price_change_24h_pct: float = 0.0  # 24h 가격 변화율

    # DCF 없음 (코인 특성)
    # dcf_fair_value: 사용 안 함


def build_coin_lens_prompt(ctx: ConsensusContext, lens: CoinLensData) -> str:
    """코인 렌즈 프롬프트 생성 (DCF 미포함).

    TradingAgents portfolio_manager.py:35-58 패턴 유지.
    """
    fgi_str = f"{lens.fear_greed_index:.0f}" if lens.fear_greed_index is not None else "N/A"
    rsi_str = f"{lens.rsi_14:.1f}" if lens.rsi_14 is not None else "N/A"

    return (
        f"[Coin Portfolio Consensus — rounds=1, COIN LENS (no DCF)]\n"
        f"Regime changed: {ctx.regime_changed}\n"
        f"Allocation delta: {ctx.allocation_change_pct:.1%}\n"
        f"Cumulative position: {ctx.cumulative_position_pct:.1%}\n"
        f"Macro view: {ctx.macro_view}\n\n"
        f"=== COIN LENS (on-chain / sentiment / funding / technical) ===\n"
        f"On-chain:\n"
        f"  Whale inflow: ${lens.whale_inflow_usd:,.0f} (neg=outflow)\n"
        f"  Exchange reserve change: {lens.exchange_reserve_change_pct:+.1%}\n"
        f"Sentiment:\n"
        f"  Fear & Greed Index: {fgi_str}/100\n"
        f"Funding/Derivatives:\n"
        f"  Funding rate: {lens.funding_rate:+.4f}\n"
        f"  OI change: {lens.open_interest_change_pct:+.1%}\n"
        f"Technical:\n"
        f"  RSI(14): {rsi_str}\n"
        f"  24h price change: {lens.price_change_24h_pct:+.1%}\n"
        f"Note: DCF NOT used (crypto — no stable cash flows).\n\n"
        f"Current weights: {ctx.current_weights}\n"
        f"Proposed weights: {ctx.proposed_weights}\n"
        f"{f'Past lessons: {ctx.past_lessons}' if ctx.past_lessons else ''}\n\n"
        f"Decide: approve|hold|reduce. Be decisive."
    )


class CoinConsensusLens(ConsensusJudge):
    """consensus 코인 렌즈 어댑터.

    ConsensusJudge 서브클래스 — 코인 전용 렌즈(on-chain/FGI/funding/technical) 주입.
    DCF 없음. 타임아웃 짧게. risk_gate 항상-on 보존.
    """

    def __init__(
        self,
        llm_router=None,
        risk_gate=None,
        allocation_threshold: float = 0.10,
        cumulative_threshold: float = 0.25,
        lens_timeout_sec: float = COIN_LENS_TIMEOUT_SEC,
    ) -> None:
        super().__init__(
            llm_router=llm_router,
            risk_gate=risk_gate,
            allocation_threshold=allocation_threshold,
            cumulative_threshold=cumulative_threshold,
        )
        self._lens_timeout = lens_timeout_sec

    def run_with_lens(
        self,
        ctx: ConsensusContext,
        lens: Optional[CoinLensData] = None,
    ) -> ConsensusDecision:
        """코인 렌즈를 포함한 consensus 실행.

        routine(is_high_stakes=False) → stub (LLM 미호출).
        고-스테이크스 → 코인 렌즈 프롬프트 → LLM Judge → risk_gate 백스톱.
        """
        if not self.is_high_stakes(ctx):
            return self._stub_decision(ctx, routing="stub")

        if lens is not None and self._router is not None:
            # 코인 렌즈 프롬프트로 LLM 호출
            prompt = build_coin_lens_prompt(ctx, lens)
            try:
                result = self._router.route_with_meta(
                    prompt,
                    high_risk=True,
                )
                text = result.text.strip().lower()
                action = "approve" if "approve" in text else (
                    "reduce" if "reduce" in text else "hold"
                )
                decision = ConsensusDecision(
                    action=action,
                    is_triggered=True,
                    confidence=0.7,
                    reasoning=result.text[:200],
                    routing="coin_lens_llm",
                )
                # risk_gate 백스톱 (§4.2 불변식 — 항상-on)
                gate_ok, final_action = self._apply_risk_gate(decision, ctx)
                if not gate_ok:
                    decision.routing = "risk_gate_override"
                decision.action = final_action
                decision.is_triggered = True
                return decision
            except Exception as exc:
                logger.warning("코인 렌즈 LLM 실패 → stub: %s", exc)

        # credential 없음 or lens=None → 기본 consensus 경로
        return self.run(ctx)

    @property
    def lens_timeout_sec(self) -> float:
        return self._lens_timeout

    @staticmethod
    def dcf_not_used() -> bool:
        """DCF 미사용 확인 — 코인 특성 명시."""
        return True
