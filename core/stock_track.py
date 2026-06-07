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
        _sector_ev_ebitda_override: "list[float] | None" = None,
        _bypass_gate1_override: bool = False,
        _deterministic_no_llm_override: bool = False,
        _heavy_agent_fail_reason_override: str | None = None,
        _weight_card_override: Any = None,
        _indicator_z_override: dict | None = None,
        _regime_pi_override: dict | None = None,
        _registry_override: Any = None,
        _regime_label_override: str | None = None,
        _fund_provider: Any = None,
        _quote_provider: Any = None,
        _region: str = "KR",
    ) -> None:
        self.ticker = ticker
        self.mode = mode
        # ★PD lookahead 보수: 백테스트 시계열 PIT — collect_market_state(as_of) 가 override 없을 때
        #   provider 로 그 시점 quote/PIT 펀더를 동적 조회(매 bar engine 이 as_of 전달). override 우선.
        self._fund_provider = _fund_provider
        self._quote_provider = _quote_provider
        self._region = _region
        # 동적 조회분(매 bar 갱신) — 외부 override 와 분리. _eff_*() 가 override 우선 결합.
        self._dynamic_quote: MarketQuote | None = None
        self._dynamic_funds: list[Fundamentals] = []
        self._market_data_override = _market_data_override
        self._portfolio_override = _portfolio_override
        self._external_data_override = _external_data_override
        self._past_decisions_override = _past_decisions_override
        self._heavy_agent = _heavy_agent_override
        self._metalabeler = _metalabeler_override
        self._valuation_override = _valuation_override
        self._fundamentals_override = _fundamentals_override or []
        self._quote_override = _quote_override
        # ★WIRE 배선(갭A): override 미주입 시 fundamentals+quote 로 value_stock 실연결.
        #   sector_ev_ebitda = 섹터 비교 멀티플(measure.py 패널). 미주입=종목 자기역사 fallback.
        self._sector_ev_ebitda = _sector_ev_ebitda_override
        # ★WIRE 배선(갭B): cross-sectional selection 경로는 가격 −10% 게이트(coin dip-buy 혈통)를
        #   면제하고 stage-2 trap veto 만 적용. default False=byte-identical(단일종목 dip-buy 경로 유지).
        self._bypass_gate1 = _bypass_gate1_override
        # ★결정론(LLM off) 경로: gate2 trap veto overlay skip → cheapness 통과분 진입(자문 nested B).
        self._deterministic_no_llm = _deterministic_no_llm_override
        self._heavy_agent_fail_reason = _heavy_agent_fail_reason_override
        # ★R15 가중학습: 평가지표 동적 가중 카드 + 지표 신호. 주입 시 generate_candidate 의
        # buy sizing 에 다중지표 합성 S_L1 을 반영(자문 §1.4 L1 결정론, pre-agent). 미주입=무회귀.
        # weight_card = WeightAssumptionCard(registry 학습 카드 또는 prior). indicator_z =
        # series_ids 순서 지표 z. regime_pi = soft archetype membership(거시상황/산업 조건부).
        self._weight_card = _weight_card_override
        self._indicator_z = _indicator_z_override
        self._regime_pi = _regime_pi_override
        # ③ registry 조회: override 없으면 train_weights 가 영속한 학습 카드를 거시국면별로 조회.
        self._registry = _registry_override
        self._regime_label = _regime_label_override

    def _eff_quote(self) -> "MarketQuote | None":
        """효과 quote = 외부 override 우선, 없으면 동적 조회분(백테스트 PIT)."""
        return self._quote_override if self._quote_override is not None else self._dynamic_quote

    def _eff_funds(self) -> "list[Fundamentals]":
        """효과 fundamentals = 외부 override 우선, 없으면 동적 조회분(백테스트 PIT)."""
        return self._fundamentals_override or self._dynamic_funds

    # ── AssetTrack 추상메서드 구현 ─────────────────────────────────────

    def collect_market_state(self, as_of=None) -> MarketState:
        """주가 MarketQuote + PIT Fundamentals 수집 → MarketState raw 보존.

        실 데이터는 Phase 4 KIS/DART wire 후. 현재는 override 주입 또는 빈 dict.
        MarketState.raw_market_data 에 quote·fundamentals·ticker 를 보존한다.
        as_of=<datetime>: 백테스트 PIT 진입점 — quote override 가 없을 때 raw_market_data["as_of"]
          기록(provider 소비는 후속 WP6). 하위호환 default None.
        """
        # ★PD lookahead 보수: as_of + provider 주입 시 매 bar 그 시점 PIT 동적 조회(외부 override 없을 때만).
        #   engine 백테스트 루프가 매 bar as_of=ts 전달 → 시점별 PIT 펀더/quote → lookahead 차단.
        if as_of is not None:
            _aod = as_of.date() if hasattr(as_of, "date") else as_of
            if self._quote_override is None and self._quote_provider is not None:
                try:
                    self._dynamic_quote = self._quote_provider.get_quote_at(self.ticker, _aod, self._region)
                except Exception:
                    self._dynamic_quote = None
            if not self._fundamentals_override and self._fund_provider is not None:
                try:
                    _fr = self._fund_provider.get_fundamentals_pit(self.ticker, as_of, self._region)
                    self._dynamic_funds = list(_fr.filings) if getattr(_fr, "available", False) else []
                except Exception:
                    self._dynamic_funds = []

        raw_market = self._market_data_override or {}
        raw_external = self._external_data_override or {}
        raw_portfolio = self._portfolio_override or {}
        raw_past = self._past_decisions_override or []

        # 주가/펀더멘털: 효과값(외부 override 우선 → 없으면 동적 PIT) 으로 raw 통합
        q = self._eff_quote()
        if q is not None:
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
        if as_of is not None and "as_of" not in raw_market:
            raw_market["as_of"] = as_of.isoformat()

        _funds = self._eff_funds()
        if _funds:
            raw_external = {
                **raw_external,
                "fundamentals": [
                    {
                        "fiscal_period": f.fiscal_period,
                        "filing_timestamp": f.filing_timestamp.isoformat(),
                        "source": f.source.value,
                        "is_pit_clean": f.is_pit_clean(),
                    }
                    for f in _funds
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

        # valuation 결과 (override 우선 → fundamentals+quote 있으면 value_stock 실연결 → 없으면 abstain)
        # ★WIRE 배선(갭A): _valuation_override 미주입이라도 PIT fundamentals + quote 가 있으면
        #   stock.valuation.value_stock 로 내재가치 밴드 실산출(과거 stub abstain 경로 대체).
        #   override 주입 경로·데이터 전무 경로는 byte-identical(둘 다 없을 때만 fallback 발동).
        valuation = self._valuation_override
        _eff_f = self._eff_funds()   # 외부 override 우선 → 없으면 동적 PIT(백테스트 시계열)
        _eff_q = self._eff_quote()
        if valuation is None and _eff_f and _eff_q:
            from stock.valuation import value_stock  # noqa: PLC0415
            valuation = value_stock(
                _eff_f,
                _eff_q,
                sector_ev_ebitda=self._sector_ev_ebitda,
            )
        if valuation is None:
            # 데이터 전무(fundamentals/quote 미주입) → abstain
            logger.warning("StockTrack: valuation 미연결 → abstain (fundamentals+quote 주입 시 실연결)")
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
            fundamentals=_eff_f,
            price_change_pct=price_change_pct,
            heavy_agent=self._heavy_agent,
            metalabeler=self._metalabeler,
            prev_intrinsic_value=None,
            context={"ticker": ticker},
            mode=self.mode,
            bypass_gate1=self._bypass_gate1,
            deterministic_no_llm=self._deterministic_no_llm,
            heavy_agent_fail_reason=self._heavy_agent_fail_reason,
        )

        # verdict → Decision 호환 변환
        decision_dict = _trigger_to_decision(trigger, ticker)

        # ★R15: 다중지표 동적 가중 → L1 합성 S_L1 을 buy sizing 에 반영(평가지표 가중 연결).
        # 이전엔 평가가 valuation_gap 단일 지표만 → R15 가중이 계산만 되고 평가 미반영(끊김).
        # 여기서 weight_card 주입 시 EV/EBITDA·book_to_bill·inventory 등이 거시국면·산업 archetype
        # 조건부 가중으로 합성돼 sizing 에 도달. 미주입 시 기존 경로 그대로(무회귀).
        return self._apply_r15_sizing(decision_dict, state, trigger, ticker)

    def _resolve_weight_card(self, state: MarketState):
        """③ override 없으면 registry 에서 거시국면별 학습 카드 조회(train_weights 영속분).

        regime_label = override 또는 state.raw_market_data["regime_label"]. id=weight.equity.{regime}.
        registry/regime 부재·미존재 → None(R15 미적용, 기존 경로). 학습=배치 / 적용=라이브 조회 분리.
        """
        if self._registry is None:
            return None
        regime = self._regime_label or state.raw_market_data.get("regime_label")
        if not regime:
            return None
        try:
            return self._registry.get(f"weight.equity.{regime}")
        except Exception:
            return None

    def _extract_indicator_z(self, state: MarketState, series_ids):
        """state 에서 series_ids 순서로 지표 z 벡터 추출. override 우선, 누락 series=0 기여.

        indicator_z override 가 있으면 그것(dict 라벨 lookup). 없으면 raw_external/raw_market 의
        수치 feature 를 키 매칭. 추출 불가(소스 전무) → None(R15 미적용, 기존 경로 유지).
        """
        import numpy as np
        if self._indicator_z is not None:
            src = self._indicator_z
        else:
            src = {}
            for d in (state.raw_external_data, state.raw_market_data):
                if isinstance(d, dict):
                    src.update({k: v for k, v in d.items() if isinstance(v, (int, float))})
        if not src:
            return None
        return np.array([float(src.get(s, 0.0)) for s in series_ids], dtype=float)

    def _apply_r15_sizing(self, decision_dict: dict, state: MarketState,
                          trigger: Any, ticker: str) -> dict:
        """R15 다중지표 동적 가중 → L1 합성 S_L1 으로 buy sizing 조절(자문 §1.4).

        weight_card 미주입 → 그대로 반환(무회귀). buy 결정에만 적용:
          S_L1 = clamp_floor(Σ wᵢ(거시국면·archetype)·zᵢ) = 지표 가중 합성 cheapness(상대 sizing 축).
          - deadzone(|S_L1|≤floor): 지표 가중 합성상 엣지 없음 → abstain(hold, sizing 0).
          - else: l1_size = R15 base sizing(지표가중 합성 강도). value_trigger(DCF+heavy value-trap)
            결과 confidence 를 **down-only attenuator** 로 곱함 → final = l1_size·a (a∈[0,1]).
            천장 불변식 final ≤ l1_size 강제(value_trigger 가 R15 sizing 을 증폭 못 함, pre-agent 우위).
        ★이유(판단근거 보존): R15=L1 결정론(평가지표 가중, 거시·산업 조건부) / value_trigger=
          agent veto/감쇠. 순서 불변식으로 LLM/agent 가 학습가중 sizing 을 흔들지 못함.
        """
        wc = self._weight_card or self._resolve_weight_card(state)
        if wc is None or decision_dict.get("decision") != "buy":
            return decision_dict
        z = self._extract_indicator_z(state, wc.series_ids)
        if z is None:
            return decision_dict
        from core.assume.weight_card import synthesize_l1, assert_ceiling_invariant

        s_l1 = synthesize_l1(z, wc.composed_weights(self._regime_pi), floor=wc.floor)
        if s_l1 == 0.0:                                       # deadzone = 지표가중 합성 엣지 없음
            return _make_decision_dict(
                decision="hold", confidence=0.0,
                reason=(f"R15 L1 지표가중 합성 deadzone(|S_L1|≤{wc.floor}) → abstain "
                        f"({decision_dict.get('reason', '')})"),
                ticker=ticker, trigger_result=trigger)

        l1_size = min(abs(float(s_l1)), 1.0)                  # R15 base sizing(지표가중 합성 강도)
        atten = min(max(float(decision_dict.get("confidence", 0.0)), 0.0), 1.0)  # value_trigger=down-only
        final = l1_size * atten
        assert_ceiling_invariant(final, l1_size)              # 천장: value_trigger 증폭 불가
        decision_dict["confidence"] = final
        decision_dict["r15_s_l1"] = float(s_l1)
        decision_dict["reason"] = (
            f"{decision_dict.get('reason', '')} | R15 L1 S_L1={s_l1:+.3f}(지표가중 합성) "
            f"l1_size={l1_size:.3f}×value_atten{atten:.2f}={final:.3f}")
        return decision_dict

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
