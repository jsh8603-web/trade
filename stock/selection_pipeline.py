"""stock/selection_pipeline.py — universe selection ⊕ per-ticker value_trigger 배선부.

임무 (실행 wire 갭B): cross_sectional_selection(횡단면 cheapness top-K capped-EW)과
StockTrack.generate_candidate(2단 value_trigger: trap veto + R15 sizing)를 한 파이프로 잇는다.
= "시총 universe 안에서 싼 종목을 골라(selection) → 각각 함정 판별·sizing(per-ticker) → risk_gate 후보".

⛔ 책임 경계:
  - selection(무엇을 고를지) = cross_sectional_selection (계약: generate 무접촉). 본 모듈이 호출.
  - per-ticker 판정(함정·sizing) = StockTrack.generate_candidate (value_trigger 위임). 본 모듈이 호출.
  - 최종 비중 강제·주문·go-live = risk_gate / order 레이어 (호출자 책임). 본 모듈 무접촉.

설계 정합 (.consult-us-selection-layer-brief.md 2R 수렴):
  - selection 경로 = run_value_trigger(bypass_gate1=True): 가격 −10% 타이밍 게이트(coin dip-buy
    혈통)를 면제하고 stage-2 trap veto 만 적용 (횡보·상승 중 싼 종목 전멸 방지).
  - valuation 1회 계산 후 trap_veto 와 generate_candidate 가 공유(중복 value_stock 호출 회피).
  - target_weight = selection capped-EW 권고(risk_gate 10%/30% 안쪽). 최종 강제는 risk_gate.
  - heavy_agent 미주입 = trap veto ABSTAIN(보수적 비-trap, 매수 후보 유지하되 abstain 로그).

미해결 가정:
  - universe {ticker → metric_panel + market_caps + fundamentals + quote} 조립은 호출자
    (supervisor/construction) 책임. 본 모듈은 조립된 universe 를 받아 변환만.
  - net-alpha t-cost reject(한국 hard)는 SelectionConfig(net_alpha_hard_reject) 로 selection 단계 처리.
"""

from __future__ import annotations

from typing import Optional, Sequence

from stock.contracts import Fundamentals, MarketQuote, RunMode, ValuationResult
from stock.cross_sectional_selection import (
    SelectionCandidate,
    SelectionConfig,
    make_trap_veto,
    select_cross_sectional,
)
from stock.valuation import value_stock


def build_universe_candidates(
    metric_panel: dict[str, dict[str, Optional[float]]],
    market_caps: dict[str, float],
    metric_signs: dict[str, int],
    fundamentals_by_ticker: dict[str, Sequence[Fundamentals]],
    quote_by_ticker: dict[str, MarketQuote],
    *,
    sectors: Optional[dict[str, str]] = None,
    sector_ev_ebitda_by_ticker: Optional[dict[str, Sequence[float]]] = None,
    config: SelectionConfig = SelectionConfig(),
    weights: Optional[dict[str, float]] = None,
    heavy_agent=None,
    mode: RunMode = RunMode.FORWARD,
    held_ranks: Optional[dict[str, int]] = None,
    interactions: Optional[Sequence[tuple[str, str, int]]] = None,
    deterministic_no_llm: bool = False,
) -> list[dict]:
    """universe → selection → per-ticker value_trigger → Decision 호환 dict 리스트.

    파이프라인:
      1. valuation_of(ticker) = value_stock(fundamentals, quote, sector_ev_ebitda) (1회 캐시)
      2. trap_veto = make_trap_veto(valuation_of, heavy_agent, fundamentals_of)
      3. select_cross_sectional(... trap_veto, held_ranks) → SelectionCandidate (top-K capped-EW)
      4. eligible candidate 각각 StockTrack(bypass_gate1=True, valuation override) → generate_candidate
      5. decision dict + selection 메타(target_weight/cheapness_z/rank/selection_reason) 병합

    반환 = eligible(매수 권고) 종목의 Decision 호환 dict 리스트 (target_weight>0, rank 순).
      risk_gate 가 소비. 비-eligible(trap veto·net-alpha·rank 이탈)은 제외.
    """
    from core.stock_track import StockTrack  # noqa: PLC0415 (순환 import 회피)

    # 1. valuation 1회 계산 캐시 (trap_veto·generate_candidate 공유)
    _val_cache: dict[str, Optional[ValuationResult]] = {}

    def valuation_of(ticker: str) -> Optional[ValuationResult]:
        if ticker not in _val_cache:
            funds = fundamentals_by_ticker.get(ticker) or []
            quote = quote_by_ticker.get(ticker)
            sec_mults = (sector_ev_ebitda_by_ticker or {}).get(ticker)
            if funds and quote is not None:
                _val_cache[ticker] = value_stock(funds, quote, sector_ev_ebitda=sec_mults)
            else:
                _val_cache[ticker] = None
        return _val_cache[ticker]

    def fundamentals_of(ticker: str) -> Sequence[Fundamentals]:
        return fundamentals_by_ticker.get(ticker) or []

    # 2. trap veto (value_trigger stage-2 재사용, bypass_gate1 내부 적용)
    trap_veto = make_trap_veto(
        valuation_of, heavy_agent=heavy_agent, fundamentals_of=fundamentals_of
    )

    # 3. selection (횡단면 z + microcap floor + trap veto eligibility + capped-EW)
    candidates: list[SelectionCandidate] = select_cross_sectional(
        metric_panel,
        market_caps,
        metric_signs,
        sectors=sectors,
        config=config,
        weights=weights,
        trap_veto=trap_veto,
        held_ranks=held_ranks,
        interactions=interactions,
    )

    # 4~5. eligible 각각 per-ticker value_trigger → decision + selection 메타 병합
    fail_reason = "quality" if heavy_agent is None else None
    decisions: list[dict] = []
    for cand in candidates:
        if not (cand.eligible and cand.target_weight > 0):
            continue
        track = StockTrack(
            ticker=cand.ticker,
            mode=mode,
            _valuation_override=valuation_of(cand.ticker),
            _fundamentals_override=list(fundamentals_of(cand.ticker)),
            _quote_override=quote_by_ticker.get(cand.ticker),
            _heavy_agent_override=heavy_agent,
            _bypass_gate1_override=True,
            _deterministic_no_llm_override=deterministic_no_llm,
            _heavy_agent_fail_reason_override=fail_reason,
        )
        state = track.collect_market_state()
        decision = track.generate_candidate(state)
        # selection 메타 병합 (risk_gate sizing 권고)
        # ★ticker 명시 노출(2026-06-07): cheapness decision 은 종목을 trade_params.market/
        #   _trigger_result.ticker 에만 담아, 소비자(construction 호출자·risk_gate)가 종목을
        #   추측해야 했다(끊긴 계약). EW/ETF fallback(_candidate_to_decision)은 이미 "ticker"
        #   를 넣으므로 동일 키로 통일 — 미통일 시 cheapness sleeve 종목이 소비단에서 누락.
        decision["ticker"] = cand.ticker
        decision["target_weight"] = cand.target_weight
        decision["cheapness_z"] = cand.cheapness_z
        decision["rank"] = cand.rank
        decision["selection_reason"] = cand.reason
        decision["per_metric_z"] = cand.per_metric_z
        decisions.append(decision)

    return decisions
