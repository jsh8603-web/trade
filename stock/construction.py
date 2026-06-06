"""stock/construction.py — sleeve 단위 종목선택 조립 (WIRE3.5-Gd, production 진입점).

sleeve명 + 실 universe 데이터(metric_panel/market_caps/fundamentals/quote)를 받아
sleeve_signals preset(부호·yaml weights·interaction)을 자동 주입하고 build_universe_candidates 호출.
= "supervisor/construction 이 sleeve 와 universe 만 주면 연구 입증 부호·가중·교호항이 자동 연결".

⛔ 경계:
  - universe 데이터 조립(EDGAR 펀더 / 가격 fetch)은 호출자(provider) 책임. 본 모듈은 선택만.
  - risk_gate cap 강제·주문(GatedOrderRouter)·go-live 사람게이트 = 별 레이어(WIRE6). 무접촉.
  - 반환 = Decision 호환 dict 리스트(target_weight 권고 포함). 최종 비중 강제는 risk_gate.
"""

from __future__ import annotations

import os
from typing import Optional, Sequence

from stock.contracts import Fundamentals, MarketQuote, RunMode, utcnow
from stock.cross_sectional_selection import SelectionConfig
from stock.selection_pipeline import build_universe_candidates
from stock.selector import EwBasketSelector, RepresentativeETFSelector, SleeveInput
from stock.sleeve_signals import (
    interaction_weights_for,
    interactions_for,
    load_sleeve_weights,
    signs_for,
)

# ★ETF fallback 라우팅 (Phase 1 ledger, etf-fallback-routing-ledger-20260606.md).
#   약변별(低/불가) sleeve → "EW"(소N·과점·ETF부재) / "ETF"(대N ∧ 적격ETF ∧ look-through).
#   strong sleeve(미수록) = None = 기존 CheapnessSelector 경로. env ETF_FALLBACK off 시 전부 무시(byte-identical).
_ETF_FALLBACK_ROUTING: dict[str, str] = {
    # 한국 — ★공정 맞대결(자문 R1 비용보정 net, etf-fallback-routing-ledger-20260606.md) 반영.
    "financial": "ETF", "battery": "ETF", "shipbuilding": "ETF", "auto": "ETF",  # net ETF 우위 or 무승부
    "bio": "EW",        # ★ETF→EW 변경: KODEX바이오 ETF +2% 트래커 실패작, EW net +138%(t=2.6 유의)
    "consumer": "EW", "chemical": "EW",       # net ETF 우위지만 ETF AUM<500억=청산리스크 → 보수적 EW
    "telecom": "EW", "refining": "EW",        # ETF 부재/부적합 + 과점 → 구성종목 EW
    # 미국 (within-residual-us-v1)
    "us_defensive": "ETF",                    # us_cyclical(작동)/us_mega_tech(basket) = 미수록(현행 유지)
}


def _resolve_etf_routing(sleeve: str, override: Optional[dict[str, str]]) -> Optional[str]:
    """sleeve → "EW"|"ETF"|None. env ETF_FALLBACK off(default)면 항상 None = byte-identical."""
    if override is not None:
        return override.get(sleeve)
    if os.environ.get("ETF_FALLBACK", "off") == "off":
        return None
    return _ETF_FALLBACK_ROUTING.get(sleeve)


def _candidate_to_decision(c) -> dict:
    """fallback SelectionCandidate → Decision 호환 dict (value 2단 게이트 우회).

    ETF/EW basket = 내재가치 부적합 → value_trigger skip. ★우회가 아니라 '안 부름'(자문 D3).
    verdict=opportunity 강제(약변별 통째 매수). instrument_type/holdings 메타 = risk_gate look-through(Phase 4-2).
    """
    return {
        "ticker": c.ticker,
        "target_weight": c.target_weight,
        "cheapness_z": c.cheapness_z,
        "rank": c.rank,
        "selection_reason": c.reason,
        "instrument_type": c.instrument_type,
        "holdings_source": c.holdings_source,
        "holdings_asof": c.holdings_asof,
        "pre_resolved": c.pre_resolved,
        "direction": "buy",
        "verdict": "opportunity",
        "confidence": 1.0,
        "value_trigger_bypassed": True,
    }


def _fallback_decisions(
    sleeve: str, routing: str,
    metric_panel: dict, market_caps: dict[str, float],
    sectors: Optional[dict[str, str]], config: Optional[SelectionConfig],
    etf_picks: Optional[dict[str, dict]],
) -> list[dict]:
    """약변별 sleeve dispatch → EwBasket/ETF selector → Decision dict (value_trigger 우회)."""
    cfg = config or SelectionConfig(demean_by_sector=bool(sectors))
    si = SleeveInput(
        sleeve_id=sleeve, constituents=list(market_caps),
        metric_panel=metric_panel, market_caps=market_caps,
        metric_signs={}, sectors=sectors, config=cfg,
    )
    asof = utcnow()
    if routing == "ETF" and etf_picks and sleeve in etf_picks:
        selector = RepresentativeETFSelector(etf_picks[sleeve])
    else:
        # ETF 라우팅이나 etf_pick 미주입(Phase 2 fetch 전) → EW basket 으로 안전 fallback
        selector = EwBasketSelector()
    cands = selector.select(si, asof)
    return [_candidate_to_decision(c) for c in cands if c.eligible]


def build_sleeve_decisions(
    sleeve: str,
    metric_panel: dict[str, dict[str, Optional[float]]],
    market_caps: dict[str, float],
    fundamentals_by_ticker: dict[str, Sequence[Fundamentals]],
    quote_by_ticker: dict[str, MarketQuote],
    *,
    sectors: Optional[dict[str, str]] = None,
    sector_ev_ebitda_by_ticker: Optional[dict[str, Sequence[float]]] = None,
    config: Optional[SelectionConfig] = None,
    heavy_agent=None,
    mode: RunMode = RunMode.FORWARD,
    held_ranks: Optional[dict[str, int]] = None,
    use_yaml_weights: bool = True,
    use_interactions: bool = True,
    etf_fallback_routing: Optional[dict[str, str]] = None,
    etf_picks: Optional[dict[str, dict]] = None,
) -> list[dict]:
    """sleeve명으로 preset 부호 + yaml weights + interaction 자동 주입 → 종목선택 Decision 리스트.

    - metric_signs = sleeve_signals.signs_for(sleeve). preset 미정의 sleeve 면 metric_panel 키 +1 default.
    - weights = load_sleeve_weights(sleeve) (use_yaml_weights, 미존재=등가중 fallback).
    - interactions = interactions_for(sleeve) (use_interactions, DEF-2 등. panel 부재 metric 은 내부 skip).
    - sectors 주입 시 demean_by_sector=on (자문 d: 다섹터 sleeve sector-neutral). config 미주입 시 자동.

    반환 = build_universe_candidates 결과(eligible 매수후보 Decision 호환 dict, target_weight 권고).

    ★ETF fallback (env ETF_FALLBACK on, 자문 D3 dispatch seam): 약변별 sleeve → EwBasket/ETF selector.
      off(default)=기존 CheapnessSelector 경로(byte-identical). etf_fallback_routing override 가능(테스트).
    """
    # ★ETF fallback dispatch (자문 D3 = construction 정책층 seam). env off → None → 기존 경로 무변경.
    _routing = _resolve_etf_routing(sleeve, etf_fallback_routing)
    if _routing:
        return _fallback_decisions(
            sleeve, _routing, metric_panel, market_caps, sectors, config, etf_picks
        )

    signs = signs_for(sleeve)
    if not signs:
        signs = {m: 1 for m in metric_panel}   # preset 미정의 = 호출자 책임(+1 default)
    weights = load_sleeve_weights(sleeve) if use_yaml_weights else None
    interactions = interactions_for(sleeve) if use_interactions else None
    # ★Gj: interaction marginal hedge — main 평균 × 0.5 로 등가중 과대 방지(DEF-2 등). main weight(yaml)
    #   있을 때만 적용, 없으면 등가중 유지(byte-identical). composite weights 에 병합 주입.
    if interactions and weights:
        iw = interaction_weights_for(sleeve, weights)
        if iw:
            weights = {**weights, **iw}
    cfg = config or SelectionConfig(demean_by_sector=bool(sectors))
    return build_universe_candidates(
        metric_panel,
        market_caps,
        signs,
        fundamentals_by_ticker,
        quote_by_ticker,
        sectors=sectors,
        sector_ev_ebitda_by_ticker=sector_ev_ebitda_by_ticker,
        config=cfg,
        weights=weights or None,
        heavy_agent=heavy_agent,
        mode=mode,
        held_ranks=held_ranks,
        interactions=interactions or None,
    )
