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

from typing import Optional, Sequence

from stock.contracts import Fundamentals, MarketQuote, RunMode
from stock.cross_sectional_selection import SelectionConfig
from stock.selection_pipeline import build_universe_candidates
from stock.sleeve_signals import (
    interaction_weights_for,
    interactions_for,
    load_sleeve_weights,
    signs_for,
)


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
) -> list[dict]:
    """sleeve명으로 preset 부호 + yaml weights + interaction 자동 주입 → 종목선택 Decision 리스트.

    - metric_signs = sleeve_signals.signs_for(sleeve). preset 미정의 sleeve 면 metric_panel 키 +1 default.
    - weights = load_sleeve_weights(sleeve) (use_yaml_weights, 미존재=등가중 fallback).
    - interactions = interactions_for(sleeve) (use_interactions, DEF-2 등. panel 부재 metric 은 내부 skip).
    - sectors 주입 시 demean_by_sector=on (자문 d: 다섹터 sleeve sector-neutral). config 미주입 시 자동.

    반환 = build_universe_candidates 결과(eligible 매수후보 Decision 호환 dict, target_weight 권고).
    """
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
