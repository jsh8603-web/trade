"""core/stock_track.py — StockTrack(AssetTrack) KR/US 주식 가치투자 Directional 래퍼.

stock/ 코드(contracts·valuation·value_trigger·factor_attribution)를
AssetTrack 인터페이스로 wire한다 — 본체 재작성 금지, 위임 중심.

흐름:
  collect_market_state → MarketState(raw 4종 보존)
  generate_candidate  → value_stock → run_value_trigger(2단) → to_track_decision → Decision 호환
  recommended_next_check → 레짐/상태 기반 권장 간격

SACRED:
  - AssetTrack ABC 미변경(상속만)
  - Phase 0/1/2 본체 미변경
  - risk_gate(Phase 2) 경유는 호출자 책임(stock_track 은 Decision 후보 반환만)
  - DRY_RUN / EMERGENCY_STOP 보존
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from core.asset_track import AssetTrack, MarketState
from stock.contracts import (
    Fundamentals,
    MarketQuote,
    RunMode,
    ValuationResult,
    ValueVerdict,
)

if TYPE_CHECKING:
    from agents.base_agent import Decision

logger = logging.getLogger("core.stock_track")

KST = timezone(timedelta(hours=9))

# 다음 점검 권장 간격 (verdict → 분)
_NEXT_CHECK_MINUTES: dict[str, int] = {
    "OPPORTUNITY": 480,    # 매수 기회 → 8시간 후 재점검
    "VALUE_TRAP": 1440,    # 함정 판정 → 24시간 후
    "ABSTAIN": 720,        # 백테스트 abstain → 12시간
    "REJECT": 1440,        # 1차 미통과 → 24시간
    "default": 720,
}


class StockTrack(AssetTrack):
    """KR/US 주식 가치투자 Directional 래퍼.

    CoinTrack 패턴 동일: 외부 데이터 수집/생성 로직을 stock/ 모듈에 위임.
    구현체는 mock 주입으로 격리 가능(테스트용).
    """

    def __init__(
        self,
        ticker: str = "",
        *,
        mode: RunMode = RunMode.FORWARD,
        _market_data_override: dict | None = None,
        _portfolio_override: dict | None = None,
        _external_data_override: dict | None = None,
        _past_decisions_override: list | None = None,
        _heavy_agent_override: Any = None,
        _metalabeler_override: Any = None,
        _valuation_override: ValuationResult | None = None,
        _fundamentals_override: list[Fundamentals] | None = None,
        _quote_override: MarketQuote | None = None,
    ) -> None:
        self.ticker = ticker
        self.mode = mode
        self._market_data_override = _market_data_override
        self._portfolio_override = _portfolio_override
        self._external_data_override = _external_data_override
        self._past_decisions_override = _past_decisions_override
        self._heavy_agent = _heavy_agent_override
        self._metalabeler = _metalabeler_override
        self._valuation_override = _valuation_override
        self._fundamentals_override = _fundamentals_override or []
        self._quote_override = _quote_override

    # ── AssetTrack 추상메서드 구현 ─────────────────────────────────────

    def collect_market_state(self) -> MarketState:
        """주가 MarketQuote + PIT Fundamentals 수집 → MarketState raw 보존.

        실 데이터는 Phase 4 KIS/DART wire 후. 현재는 override 주입 또는 빈 dict.
        MarketState.raw_market_data 에 quote·fundamentals·ticker 를 보존한다.
        """
        raw_market = self._market_data_override or {}
        raw_external = self._external_data_override or {}
        raw_portfolio = self._portfolio_override or {}
        raw_past = self._past_decisions_override or []

        # 주가/펀더멘털 override 가 있으면 raw_market_data 에 통합
        if self._quote_override is not None:
            q = self._quote_override
            raw_market = {
                **raw_market,
                "ticker": q.ticker,
                "asset": q.ticker,
                "price": q.price,
                "market_cap": q.market_cap,
                "price_change_pct": q.price_change_pct,
                "price_change_window_days": q.price_change_window_days,
                "as_of": q.as_of.isoformat(),
                "timestamp": q.as_of.isoformat(),
            }
        if self.ticker and "ticker" not in raw_market:
            raw_market["ticker"] = self.ticker

        if self._fundamentals_override:
            raw_external = {
                **raw_external,
                "fundamentals": [
                    {
                        "fiscal_period": f.fiscal_period,
                        "filing_timestamp": f.filing_timestamp.isoformat(),
                        "source": f.source.value,
                        "is_pit_clean": f.is_pit_clean(),
                    }
                    for f in self._fundamentals_override
                ],
            }

        return MarketState(
            raw_market_data=raw_market,
            raw_external_data=raw_external,
            raw_portfolio=raw_portfolio,
            raw_past_decisions=raw_past,
        )

    def generate_candidate(self, state: MarketState) -> dict:
        """MarketState → value_stock → run_value_trigger(2단) → Decision 호환 dict.

        Decision dataclass(base_agent.py:111)와 호환되는 dict 를 반환한다.
        실제 Decision 생성은 risk_gate 상위 레이어(호출자) 책임.

        반환 형식 (Decision 호환):
          decision: "buy" | "sell" | "hold" | "abstain"
          confidence: float 0~1
          reason: str
          trade_params: dict
          agent_name: str
          trigger_result: ValueTriggerResult (부가 정보)
        """
        from stock.value_trigger import run_value_trigger  # noqa: PLC0415

        ticker = state.raw_market_data.get("ticker", self.ticker) or "UNKNOWN"
        price_change_pct: Optional[float] = state.raw_market_data.get("price_change_pct")

        # valuation 결과 (override 또는 stub)
        valuation = self._valuation_override
        if valuation is None:
            # Phase 4 이전: 가치평가 미연결 → abstain
            logger.warning("StockTrack: valuation 미연결 → abstain (Phase 4 KIS wire 후 실연결)")
            return _make_decision_dict(
                decision="hold",
                confidence=0.0,
                reason="valuation 미연결(stub) — Phase 4 wire 후 실판정",
                ticker=ticker,
                trigger_result=None,
            )

        # 2단 게이트 실행
        trigger = run_value_trigger(
            valuation=valuation,
            fundamentals=self._fundamentals_override,
            price_change_pct=price_change_pct,
            heavy_agent=self._heavy_agent,
            metalabeler=self._metalabeler,
            prev_intrinsic_value=None,
            context={"ticker": ticker},
            mode=self.mode,
        )

        # verdict → Decision 호환 변환
        return _trigger_to_decision(trigger, ticker)

    def recommended_next_check(self, state: MarketState) -> datetime:
        """다음 점검 권장 시각 반환 (verdict 기반 동적 간격)."""
        ticker = state.raw_market_data.get("ticker", self.ticker)
        minutes = _NEXT_CHECK_MINUTES.get("default")

        # 마지막 generate_candidate 결과에서 verdict 추출 (가능한 경우)
        verdict_str = state.raw_market_data.get("_last_verdict", "default")
        minutes = _NEXT_CHECK_MINUTES.get(verdict_str, _NEXT_CHECK_MINUTES["default"])

        return datetime.now(KST) + timedelta(minutes=minutes)


# ── 내부 유틸 ─────────────────────────────────────────────────────────

def _make_decision_dict(
    decision: str,
    confidence: float,
    reason: str,
    ticker: str,
    trigger_result: Any = None,
) -> dict:
    """Decision 호환 dict 생성."""
    return {
        "decision": decision,
        "confidence": confidence,
        "reason": reason,
        "buy_score": {},
        "trade_params": {
            "side": "bid" if decision == "buy" else "ask" if decision == "sell" else "none",
            "market": ticker,
            "amount": 0,
        },
        "external_signal": {},
        "agent_name": "StockTrack",
        "_trigger_result": trigger_result,
    }


def _trigger_to_decision(trigger: Any, ticker: str) -> dict:
    """ValueTriggerResult → Decision 호환 dict 변환."""
    verdict = trigger.verdict

    if verdict == ValueVerdict.OPPORTUNITY:
        decision = "buy"
        confidence = float(trigger.confidence)
    elif verdict == ValueVerdict.VALUE_TRAP:
        decision = "hold"
        confidence = 0.0
    elif verdict == ValueVerdict.ABSTAIN:
        decision = "hold"
        confidence = 0.0
    elif verdict == ValueVerdict.REJECT:
        decision = "hold"
        confidence = 0.0
    else:
        decision = "hold"
        confidence = 0.0

    return _make_decision_dict(
        decision=decision,
        confidence=confidence,
        reason=trigger.reasoning,
        ticker=ticker,
        trigger_result=trigger,
    )
