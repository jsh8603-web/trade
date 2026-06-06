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
        self._fhc_loop = None        # (B) FHC shadow 발권 루프 lazy 캐시(rate_cap 상태 유지)
        self._fhc_ingest = None      # (RAG) research_ingest lazy(발권 report_store=RAG stage-2 연결)
        self._fhc_cards = []         # (C) 발권 카드 누적 [(FHCard, FHCState)] → allocate bonus wire
        self._macro_node = None      # (enrich) MacroReasoningNode lazy(거시 LLM stance 주입)

    def collect_market_state(self, as_of=None) -> MarketState:
        """기존 CoinTrack.collect_market_state + macro 레이어 주입.

        macro_view 는 raw_external_data["macro_view"] 에 주입.
        coin 결정엔진은 이 정보를 참조할 수 있으나 무시도 가능(기존 로직 우선).
        as_of 는 super() 로 전달(백테스트 PIT 진입점, 하위호환 default None).
        """
        state = super().collect_market_state(as_of=as_of)

        if self._macro_enabled and self._macro_orch is not None:
            try:
                # IC0: opt-in on 이면 sleeve 수익률 패널 공급(corr_prior/Λ dormant 해제).
                # off/실패 시 None → allocate fallback(무회귀). 네트워크 의존이라 try 격리.
                returns_panel = None
                macro_view = None
                sleeve_regime_ids = None
                try:
                    from core.study.study_register import is_r15_enabled
                    if is_r15_enabled():
                        from core.data.sleeve_returns import fetch_sleeve_returns
                        returns_panel = fetch_sleeve_returns(as_of=as_of)
                        # IC0-R: regime 동적 corr 진입 substrate. macro_view(국면)+sleeve_regime_ids
                        # 둘 다 공급돼야 _belief_conditional_cov → RegimeGlasso belief-mix 동적 Σ_eff 동작.
                        # ★무거움(classify=FRED fetch / build=과거 전체 classify, regime_history:94 경고)
                        #   → 배치 캐시 후속. 1차=connectivity. FRED 키 부재→classify UNAVAILABLE→graceful.
                        if returns_panel is not None:
                            from core.brain.regime_classifier import RegimeClassifier
                            from core.brain.fred_adapter import RealFredAdapter
                            from core.brain.regime_history import build_sleeve_regime_ids
                            _clf = RegimeClassifier(usd_adapter=RealFredAdapter())
                            macro_view = _clf.classify(as_of=as_of)
                            sleeve_regime_ids = build_sleeve_regime_ids(
                                _clf, returns_panel,
                                ("Reflation", "Recovery", "Overheat", "Stagflation"))
                except Exception:
                    returns_panel = None
                    macro_view = None
                    sleeve_regime_ids = None
                # ★거시 LLM enrich (env MACRO_ENRICH off=byte-identical) — trigger 시 LLM stance
                #   주입 → regime_to_weights BL View 로 배분 이동(결정론 baseline 자체 수정). 고신뢰=baseline.
                if macro_view is not None:
                    from core.assume.loop_factory import is_macro_enrich_enabled
                    if is_macro_enrich_enabled():
                        try:
                            macro_view = self._run_macro_enrich(macro_view)
                        except Exception as exc:
                            logger.warning("macro enrich 실패 → baseline 유지: %s", exc)

                macro_result = self._macro_orch.allocate(
                    macro_view=macro_view, returns_history=returns_panel,
                    sleeve_regime_ids=sleeve_regime_ids, as_of=as_of,
                    fhc_card_states=(self._fhc_cards or None))  # (C) env FHC_BONUS off=무시
                # macro_abstain 정보 주입 (H29: buy 차단 신호)
                state.raw_external_data["macro_weights"] = macro_result.get("weights", {})
                state.raw_external_data["macro_abstain"] = macro_result.get("macro_abstain", False)
                state.raw_external_data["macro_status"] = macro_result.get("status", "fresh")
                logger.debug("macro 레이어 주입 완료: abstain=%s", macro_result.get("macro_abstain"))

                # (B) FHC shadow 발권 wire — env ACTIVE_LOOP_SHADOW opt-in. off=미호출(byte-identical).
                #     LLM(Claude OAuth) 실호출하되 카드=probationary(자본0, 배분 무영향).
                #     결과는 raw_external_data["fhc_shadow_cards"](관찰용)로만 — 결정엔진 미참조.
                try:
                    from core.assume.loop_factory import is_active_loop_shadow_enabled
                    if is_active_loop_shadow_enabled():
                        self._run_fhc_shadow(macro_view, as_of, state)
                except Exception as exc:
                    logger.warning("FHC shadow 발권 wire 실패 → 무시(배분 무영향): %s", exc)
            except Exception as exc:
                logger.warning("macro 레이어 주입 실패 → 기존 경로 유지: %s", exc)

        return state

    def _run_macro_enrich(self, macro_view):
        """거시 LLM enrich — 저신뢰/caution trigger 시 LLM stance 주입, 고신뢰=baseline(결정론 충분).

        ★결정론 baseline 수정 경로: trigger 발동 시 LLM 이 stance(슬리브 tilt)를 macro_view 에 주입,
        regime_to_weights 가 이를 BL View 로 소비 → 배분 이동. confidence 낮으면 stance 자동 축소(C2).
        trigger 없으면(고신뢰 + caution 없음) baseline 그대로(LLM 미호출, 비용 0). 실패→baseline graceful.
        """
        from core.brain.macro_reasoning import MacroTrigger
        from core.brain.macro_schema import Bloc

        usd = macro_view.regime(Bloc.USD)
        conf = getattr(usd, "confidence_now", 1.0) if usd is not None else 1.0
        caution = bool(getattr(macro_view, "caution_flags", []))
        if conf >= 0.5 and not caution:
            return macro_view   # 고신뢰 + caution 없음 = trigger 없음(결정론 baseline)

        if self._macro_node is None:
            from core.assume.loop_factory import build_macro_reasoning_node
            self._macro_node = build_macro_reasoning_node(
                use_claude=True, report_store=self._fhc_ingest)
        trig = MacroTrigger(
            reason=("low_confidence" if conf < 0.5 else "report_divergence"),
            detail={"confidence": conf, "caution": caution})
        return self._macro_node.enrich(macro_view, trig)

    def _run_fhc_shadow(self, macro_view, as_of, state) -> None:
        """(B) FHC 능동 발권 루프 shadow 1사이클 — env ACTIVE_LOOP_SHADOW on 일 때만 호출.

        macro_view(국면) 저신뢰/mediator UNKNOWN 시 LLM(Claude OAuth) 소환→반증가능 카드 발권.
        카드 = probationary(자본0, go-live arming 전 배분 무영향). 결과는 관찰용 적재만.
        macro_view 부재(r15 off) 시 shadow 전용 가벼운 classify 1회(graceful). 실패=무시.
        rate_cap(일1회) 상태 유지를 위해 루프 인스턴스를 self._fhc_loop 에 캐시.
        """
        mv = macro_view
        if mv is None:
            try:
                from core.brain.regime_classifier import RegimeClassifier
                from core.brain.fred_adapter import RealFredAdapter
                mv = RegimeClassifier(usd_adapter=RealFredAdapter()).classify(as_of=as_of)
            except Exception:
                mv = None
        if mv is None:
            return

        if self._fhc_loop is None:
            from core.assume.loop_factory import build_shadow_active_loop, build_research_ingest
            # ★RAG 닫기: research_ingest(Haiku 요약 + BGE 임베딩)를 발권 report_store 로 연결.
            #   거시 증권 리포트 소스는 go-live(미구축) → 현재 빈 retrieve(graceful). 종목은 실동작.
            self._fhc_ingest = build_research_ingest(use_haiku=True, use_bge=True)
            # use_claude=True: 메인과 동일 OAuth 키(사용자 "한도 OK"). 실패→llm None graceful.
            self._fhc_loop = build_shadow_active_loop(
                use_claude=True, report_store=self._fhc_ingest)

        # tick = as_of 일슬롯(같은 날 1회 상한). 라이브(as_of None)=0 슬롯=프로세스 내 1회.
        tick = 0.0
        try:
            if as_of is not None and hasattr(as_of, "toordinal"):
                tick = float(as_of.toordinal())
        except Exception:
            tick = 0.0

        pcard = self._fhc_loop.run_cycle(
            mv, tick=tick, numeric_revision=1.0,
            query="macro regime asset allocation outlook",
            as_of_ts=(tick or None))
        if pcard is not None:
            state.raw_external_data["fhc_shadow_cards"] = [{
                "card_id": pcard.card.card_id,
                "direction": pcard.card.direction,
                "thesis": pcard.thesis,
                "mediator": pcard.card.mediator.observable_ref,
                "falsification": pcard.card.falsification_metric,
                "kind": pcard.card.kind,
                "bonus_cap": pcard.card.bonus_cap,
            }]
            # (C) 연결: 발권 카드 누적 → 다음 사이클 allocate fhc_card_states 소비(FHC_BONUS on 시).
            #   probationary(minted)=bonus 0→무영향. go-live arming(confirmed 전이) 시 weight tilt.
            from core.assume.fhc import FHCState
            self._fhc_cards.append((pcard.card, FHCState(pcard.card.card_id)))
            if len(self._fhc_cards) > 20:
                self._fhc_cards = self._fhc_cards[-20:]
            logger.info("FHC shadow 발권: %s (probationary, 자본0)", pcard.card.card_id)

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
