"""stock/selector.py — sleeve selection 전략 디스패치 (Phase A, 자문 3R 2026-06-06).

약변별 sleeve → 테마 ETF fallback 설계의 **load-bearing 추상**.
construction(정책층)이 sleeve 별로 어느 Selector 를 쓸지 dispatch 하고,
본 모듈은 mechanism (Selector 프로토콜 + 구현체) 을 제공한다.

설계 근거 (자문 3R 수렴 — gemini-web Gemini Pro + claude-web Claude Opus):
- D3: z=+99.9 mock 주입(poison: dispersion/breadth 통계 오염) 기각 → selector-dispatch.
  ETF 는 SelectionCandidate.pre_resolved=True 로 ranker bypass (가짜 점수 주입 아니라 경로 건너뜀).
- 'value 트리거 우회'가 아니라 'value 트리거를 안 부름' = byte-identity 보존 핵심.
- CheapnessSelector = 기존 select_cross_sectional 위임 (로직 무변경, ABC 만 implements).
- dispatch seam = construction(정책 소유) 층 / pipeline·selector = mechanism.

라우팅 (Phase 3~4 에서 construction 이 적용):
  RepresentativeETFSelector ⟸ N≥5(비용 proxy) ∧ 적격 passive-ETF ∧ look-through 통과 ∧ PIT max-lag
  EwBasketSelector          ⟸ 그 외 (소N OR 적격ETF부재 OR look-through 실패 OR PIT-stale)
  CheapnessSelector         ⟸ strong sleeve (기존 robust-z, 무변경)

⛔ Phase A 범위 = 프로토콜 + SleeveInput + CheapnessSelector(기존 강등) 만.
   EwBasketSelector / RepresentativeETFSelector 구현 + build_universe_candidates wire 는 Phase 3~4.
   본 모듈은 아직 어디서도 import 되지 않음 → 기존 호출 경로 무변경 = production byte-identical.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional, Sequence

from stock.cross_sectional_selection import (
    SelectionCandidate,
    SelectionConfig,
    _capped_equal_weight,
    select_cross_sectional,
)


# ---------------------------------------------------------------------------
# sleeve 입력 묶음 — Selector 구현체가 소비하는 계약
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SleeveInput:
    """한 sleeve 의 selection 입력. Selector.select 가 받는 (constituents, features) 묶음.

    EQUITY selector(CheapnessSelector) 는 metric_panel/market_caps/metric_signs 를 쓰고,
    ETF selector(Phase 3) 는 etf_candidates 를 쓴다. 한 컨테이너로 양 경로를 dispatch.
    """
    sleeve_id: str
    constituents: Sequence[str]                       # 이 sleeve 후보 ticker
    metric_panel: dict = field(default_factory=dict)  # {ticker: {metric: value}}
    market_caps: dict = field(default_factory=dict)   # {ticker: market_cap}
    metric_signs: dict = field(default_factory=dict)  # {metric: +1/-1}
    sectors: Optional[dict] = None                    # {ticker: sector}
    weights: Optional[dict] = None                    # composite z 합성 가중
    config: SelectionConfig = SelectionConfig()
    # ETF fallback 입력 (Phase 3 ETF selector 가 소비, EQUITY 경로 미사용)
    etf_candidates: Optional[Sequence[dict]] = None   # 적격 테마 ETF 메타 [{ticker, ter, te, adv, aum, holdings...}]


# ---------------------------------------------------------------------------
# Selector 프로토콜 (자문 D3: (constituents, features, asof) → List[SelectionCandidate])
# ---------------------------------------------------------------------------

class Selector(ABC):
    """sleeve → List[SelectionCandidate] 변환 전략.

    구현체:
      - CheapnessSelector        : 횡단면 robust-z cheapness top-K (기존, strong sleeve)
      - EwBasketSelector         : 소N OR 적격ETF부재 → 구성종목 EW (Phase 3)
      - RepresentativeETFSelector: 대N ∧ 적격ETF ∧ look-through → 단일 ETF, pre_resolved (Phase 3)

    asof = PIT 시점. ETF selector 의 holdings/리밸 PIT 에 쓰이고, EQUITY 경로는 미사용.
    """

    @abstractmethod
    def select(self, sleeve: SleeveInput, asof: datetime) -> list[SelectionCandidate]:
        """sleeve 입력을 SelectionCandidate 리스트로 변환. risk_gate 가 소비."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# CheapnessSelector — 기존 select_cross_sectional 강등 래퍼 (로직 무변경)
# ---------------------------------------------------------------------------

class CheapnessSelector(Selector):
    """strong sleeve 기존 횡단면 cheapness selection.

    cross_sectional_selection.select_cross_sectional 에 1:1 위임한다 — robust-z·capped-EW·
    trap-veto eligibility 로직을 한 줄도 바꾸지 않는다 (자문 D3: 기존 함수를 이 구현체로 '강등').
    trap_veto/held_ranks/interactions 는 selection_pipeline 이 주입하던 그대로 생성자로 받는다.
    """

    def __init__(
        self,
        *,
        trap_veto: Optional[Callable] = None,
        held_ranks: Optional[dict[str, int]] = None,
        interactions: Optional[Sequence[tuple[str, str, int]]] = None,
    ) -> None:
        self._trap_veto = trap_veto
        self._held_ranks = held_ranks
        self._interactions = interactions

    def select(self, sleeve: SleeveInput, asof: datetime) -> list[SelectionCandidate]:
        # asof 는 EQUITY cheapness 경로 미사용 (PIT 마스킹은 호출자가 metric_panel 조립 시 적용).
        return select_cross_sectional(
            sleeve.metric_panel,
            sleeve.market_caps,
            sleeve.metric_signs,
            sectors=sleeve.sectors,
            config=sleeve.config,
            weights=sleeve.weights,
            trap_veto=self._trap_veto,
            held_ranks=self._held_ranks,
            interactions=self._interactions,
        )


# ---------------------------------------------------------------------------
# EwBasketSelector — 소N/과점/적격ETF부재 → 구성종목 capped-EW (자문 D4)
# ---------------------------------------------------------------------------

class EwBasketSelector(Selector):
    """약변별 sleeve 中 소N·과점·적격ETF부재 → 구성종목 capped-EW basket.

    value selection 없이 sleeve 전 종목을 capped equal-weight 로 보유 = 테마 노출 충실 재현
    (수수료0/TE0/basis0, 자문 'EW dominant'). ETF wrapper 운영비용 회피 (정유 2종/통신 3종 등).
    cheapness 미산출(pre_resolved=True) → downstream ranker bypass. capped-EW 는 기존
    _capped_equal_weight 재사용 (종목 cap + 섹터 cap water-filling, risk_gate cap 안쪽).
    """

    def select(self, sleeve: SleeveInput, asof: datetime) -> list[SelectionCandidate]:
        tickers = list(sleeve.constituents) or list(sleeve.market_caps)
        w = _capped_equal_weight(
            tickers, sleeve.sectors or {},
            sleeve.config.max_weight_single, sleeve.config.max_weight_sector,
        )
        ranked = sorted(tickers, key=lambda t: -sleeve.market_caps.get(t, 0.0))
        out: list[SelectionCandidate] = []
        for i, t in enumerate(ranked, 1):
            tw = w.get(t, 0.0)
            out.append(SelectionCandidate(
                ticker=t, cheapness_z=0.0, market_cap=sleeve.market_caps.get(t, 0.0),
                rank=i, target_weight=tw, eligible=tw > 0,
                reason="EW basket fallback (약변별 sleeve, 구성종목 capped-EW, selection 포기)",
                instrument_type="EQUITY", pre_resolved=True,
            ))
        return out


# ---------------------------------------------------------------------------
# RepresentativeETFSelector — 대N ∧ 적격ETF ∧ look-through → 단일 대표 ETF (자문 D2/D3)
# ---------------------------------------------------------------------------

class RepresentativeETFSelector(Selector):
    """약변별 sleeve 中 대N ∧ 적격 passive-ETF ∧ look-through 통과 → 단일 대표 ETF.

    선정 기준(자문 D2) = 대표성(추종충실) + 유동성(거래대금/AUM) + 저비용(TER/realized-TE) + tax/FX,
    레버리지/인버스 제외, ★과거 리턴 배제(momentum chasing 회피). ETF 는 score=None(pre_resolved)
    → ranker bypass(가짜점수 주입 아니라 경로 건너뜀). holdings 메타 운반 → risk_gate look-through
    (섹터 cap = underlying / 단일발행체 direct+via-ETF 합산).

    ⛔ etf_pick(선정된 ETF 메타) 주입 = 호출자(construction, Phase 2 fetch + 선정 후). 본 selector 는
       이미 선정·look-through 통과한 ETF 1개를 candidate 화만 (선정 로직은 호출자/Phase 1-2).
    """

    def __init__(self, etf_pick: dict) -> None:
        self._etf = etf_pick   # {ticker, aum, ter, realized_te, holdings_source, holdings_asof, ...}

    def select(self, sleeve: SleeveInput, asof: datetime) -> list[SelectionCandidate]:
        e = self._etf
        return [SelectionCandidate(
            ticker=e["ticker"], cheapness_z=0.0, market_cap=float(e.get("aum", 0.0)),
            rank=1, target_weight=1.0, eligible=True,
            reason=(f"ETF fallback (약변별 sleeve {sleeve.sleeve_id}, 대표성+유동성+저비용 선정, "
                    f"리턴 배제, TER={e.get('ter')})"),
            instrument_type="ETF",
            holdings_source=e.get("holdings_source"),
            holdings_asof=e.get("holdings_asof"),
            pre_resolved=True,
        )]
