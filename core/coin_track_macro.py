"""core/coin_track_macro.py — CoinTrack + macro 레이어 wire (SO-1/Phase R).

WHY: coin 결정엔진(calculate_buy_score)·레짐(detect_regime) = crypto-튜닝됨 → 유지(재작성 금지).
     Phase0 CoinTrack(AssetTrack ABC) 계약 위에 macro 레이어(Phase6 Orchestrator)만 추가.
     coin_track.py 본체 미변경 SACRED.

설계:
- CoinTrackWithMacro(CoinTrack): collect_market_state 에 macro_view 주입만
- macro 레이어: portfolio_orchestrator.allocate() → macro_abstain/weights 정보 주입
- generate_candidate: 기존 CoinTrack.generate_candidate 그대로 (재작성 금지)
- macro abstain(H29): macro unavailable → buy 차단(기존 EMERGENCY_STOP 보존)
"""

from __future__ import annotations

import logging
from typing import Optional

from core.asset_track import MarketState
from core.coin_track import CoinTrack

logger = logging.getLogger("core.coin_track_macro")


class CoinTrackWithMacro(CoinTrack):
    """CoinTrack + macro 레이어(Phase6 Orchestrator) wire.

    SACRED:
    - coin 결정엔진·레짐 본체 미변경 (super() 위임)
    - DRY_RUN/EMERGENCY_STOP 보존
    - nonce uuid 미변경
    """

    def __init__(
        self,
        *,
        macro_orchestrator=None,
        macro_enabled: bool = True,
        _market_data_override=None,
        _portfolio_override=None,
        _external_data_override=None,
        _past_decisions_override=None,
    ):
        super().__init__(
            _market_data_override=_market_data_override,
            _portfolio_override=_portfolio_override,
            _external_data_override=_external_data_override,
            _past_decisions_override=_past_decisions_override,
        )
        self._macro_orch = macro_orchestrator
        self._macro_enabled = macro_enabled

    def collect_market_state(self) -> MarketState:
        """기존 CoinTrack.collect_market_state + macro 레이어 주입.

        macro_view 는 raw_external_data["macro_view"] 에 주입.
        coin 결정엔진은 이 정보를 참조할 수 있으나 무시도 가능(기존 로직 우선).
        """
        state = super().collect_market_state()

        if self._macro_enabled and self._macro_orch is not None:
            try:
                macro_result = self._macro_orch.allocate()
                # macro_abstain 정보 주입 (H29: buy 차단 신호)
                state.raw_external_data["macro_weights"] = macro_result.get("weights", {})
                state.raw_external_data["macro_abstain"] = macro_result.get("macro_abstain", False)
                state.raw_external_data["macro_status"] = macro_result.get("status", "fresh")
                logger.debug("macro 레이어 주입 완료: abstain=%s", macro_result.get("macro_abstain"))
            except Exception as exc:
                logger.warning("macro 레이어 주입 실패 → 기존 경로 유지: %s", exc)

        return state

    def generate_candidate(self, state: MarketState):
        """기존 CoinTrack.generate_candidate 그대로 (재작성 금지).

        macro_abstain=True 인 경우 buy→hold 보수 처리 (H29).
        """
        decision = super().generate_candidate(state)

        # H29 macro abstain: macro unavailable → buy 차단
        if state.raw_external_data.get("macro_abstain") is True:
            if getattr(decision, "decision", "") == "buy":
                logger.info("H29 macro abstain: buy→hold 차단")
                # Decision 객체 복사 (원본 미변경)
                try:
                    from agents.base_agent import Decision as Dec
                    decision = Dec(
                        decision="hold",
                        confidence=decision.confidence,
                        reason=f"[H29 macro abstain] {decision.reason}",
                        buy_score=getattr(decision, "buy_score", {}),
                        trade_params=getattr(decision, "trade_params", {}),
                        external_signal=getattr(decision, "external_signal", {}),
                        agent_name=getattr(decision, "agent_name", ""),
                        timestamp=getattr(decision, "timestamp", ""),
                    )
                except Exception:
                    pass  # 변환 실패 시 원본 유지

        return decision
