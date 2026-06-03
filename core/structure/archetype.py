"""core/structure/archetype.py — archetype 5종 discriminated union (T2-4, 계약 #3).

cheapness_z 는 "얼마나 싼가"를 주지만, **무엇을 보고 싼지 판단하고 어떤 함정을 경계할지**
는 archetype 마다 다르다. 현 percentile 설계는 cyclical 1개에 과적합 — event_driven 은
멀티플 분위가 무의미하고, compounder 는 함정이 *비싼* 쪽이다 (claude R4).

discriminated union (pydantic v2, 판별자 = `archetype`):
- cyclical      : 반도체·화학·철강. primary=EV/EBITDA·P/B. trap=peak-EPS(정점에 멀티플 낮음).
- event_driven  : 바이오·인터넷. primary=P/S·pipeline·MAU. 멀티플 percentile 무의미, trap=이벤트 binary.
- spread_driven : 은행·증권(financials). primary=P/B·ROE. trap=신용사이클(대손).
- asset_stable  : 유틸·통신. primary=DDM·배당수익률. trap=금리쇼크·규제.
- compounder    : 고ROIC 복리기업. primary=ROIC 지속성·reinvestment. **trap=비싼 쪽**(멀티플 unwind).

★ 시변 (claude/gemini R7): archetype 도 시간에 따라 변한다 (엔비디아: 과거 게임카드 cyclical →
  AI 가속기 compounder). 그래서 `valid_from` 을 두고 bitemporal 로 카드를 교체한다.
  percentile 은 cyclical 과적합 위험이라 카드가 명시적으로 경고 플래그를 든다.

계약 표면 (T3 소비, SPEC):
    ArchetypeCard(archetype, primary_metric, companion_signals[], value_trap_guards[])
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 공통 core
# ---------------------------------------------------------------------------

class _ArchetypeBase(BaseModel):
    """모든 archetype 카드의 공통 core. 판별자(archetype)는 subclass 의 Literal."""
    model_config = {"frozen": True, "extra": "forbid"}

    primary_metric: str                       # 이 archetype 에서 "싸다" 의 1차 척도
    companion_signals: list[str] = Field(default_factory=list)  # 보조 확증 신호
    value_trap_guards: list[str] = Field(default_factory=list)  # 밸류트랩 경고 신호
    valid_from: Optional[date] = None         # 시변: 이 카드가 유효해진 시점 (bitemporal)
    percentile_overfit_risk: bool = False     # raw 분위가 이 archetype 에 과적합/오작동하는가
    cheapness_sign: Literal["low_multiple", "expensive_trap"] = "low_multiple"
    # cheapness_sign="expensive_trap" → compounder 처럼 함정이 비싼 쪽 (저멀티플≠기회)


class CyclicalCard(_ArchetypeBase):
    archetype: Literal["cyclical"] = "cyclical"
    # 사이클 위상 판정에 쓰는 드라이버 (peak-EPS trap 핵심)
    cycle_drivers: list[str] = Field(
        default_factory=lambda: ["book_to_bill", "capex_to_rev", "inventory_qoq"]
    )


class EventDrivenCard(_ArchetypeBase):
    archetype: Literal["event_driven"] = "event_driven"
    event_catalysts: list[str] = Field(default_factory=list)  # 임상·승인·출시 등 binary 이벤트


class SpreadDrivenCard(_ArchetypeBase):
    archetype: Literal["spread_driven"] = "spread_driven"
    spread_inputs: list[str] = Field(
        default_factory=lambda: ["net_interest_margin", "credit_spread", "rate_curve"]
    )


class AssetStableCard(_ArchetypeBase):
    archetype: Literal["asset_stable"] = "asset_stable"
    rate_sensitivity: float = 1.0             # 금리 민감도 (DDM 분모)


class CompounderCard(_ArchetypeBase):
    archetype: Literal["compounder"] = "compounder"
    # compounder 는 함정이 비싼 쪽 → 기본값으로 명시
    cheapness_sign: Literal["low_multiple", "expensive_trap"] = "expensive_trap"
    quality_inputs: list[str] = Field(
        default_factory=lambda: ["roic_durability", "reinvestment_rate", "moat_proxy"]
    )


# ---------------------------------------------------------------------------
# commodity archetype (BB-5, 자문 R1/R4) — carry/seasonal/inventory
# ---------------------------------------------------------------------------

class CommodityCarryCard(_ArchetypeBase):
    """원자재 carry(롤수익률·convenience yield). 백워데이션(carry+)=매력 = low_multiple 동형.
    falsification(R1): carry→fwd-return 회귀 slope 부호전환(prequential) + 2sigma 이탈."""
    archetype: Literal["commodity_carry"] = "commodity_carry"
    carry_inputs: list[str] = Field(
        default_factory=lambda: ["roll_yield", "term_structure_slope", "convenience_yield", "storage_cost"]
    )
    # trap: contango_flip(carry 음전환), 재고급증


class SeasonalCard(_ArchetypeBase):
    """계절성(난방유·곡물). falsification(R1): 월dummy F-test + STL seasonal-strength + 차기 OOS hit."""
    archetype: Literal["seasonal"] = "seasonal"
    season_inputs: list[str] = Field(
        default_factory=lambda: ["seasonal_zscore", "heating_degree_days", "harvest_calendar"]
    )
    # trap: regime_break(이상기온·공급충격으로 계절성 무력화)


class InventoryCard(_ArchetypeBase):
    """재고/COT. COT 예측력 약함(Sanders-Irwin) → COT=companion. falsification(R1):
    정규화재고 variance-ratio(Lo-MacKinlay) + threshold-regression(Hansen, threshold=days-of-supply)."""
    archetype: Literal["inventory"] = "inventory"
    inventory_inputs: list[str] = Field(
        default_factory=lambda: ["days_of_supply", "inventory_zscore", "production_qoq"]
    )
    # trap: oversupply_regime(재고 극단인데 평균회귀 안 함 = 구조적 공급과잉)


# ---------------------------------------------------------------------------
# crypto archetype (BB-5, 자문 R2) — monetary_store/network_utility/speculative_flow
# ---------------------------------------------------------------------------

class MonetaryStoreCard(_ArchetypeBase):
    """BTC 가치저장. primary=MVRV(낮을수록 cheap, mechanical robust). realized-price cost-basis.
    trap: network impairment(죽는 체인이 realized price 아래) + forced-deleverage(LUNA/FTX)."""
    archetype: Literal["monetary_store"] = "monetary_store"
    onchain_inputs: list[str] = Field(
        default_factory=lambda: ["realized_price", "nvt", "hash_rate", "lth_supply"]
    )


class NetworkUtilityCard(_ArchetypeBase):
    """ETH 류 준-현금흐름(fee burn·staking). equity archetype 최근접.
    trap: high APY death spiral(토큰 인플레>스테이킹 이율), dev 활동 급감."""
    archetype: Literal["network_utility"] = "network_utility"
    utility_inputs: list[str] = Field(
        default_factory=lambda: ["fee_burn", "staking_yield", "active_addresses", "active_dev_count"]
    )


class SpeculativeFlowCard(_ArchetypeBase):
    """alts. 수급/과열(funding·SOPR). value_trap_guard 최강(영구손상 위험).
    trap: liquidation cascade + 영구 impairment. funding=regime-dependent companion(primary 부적합)."""
    archetype: Literal["speculative_flow"] = "speculative_flow"
    flow_inputs: list[str] = Field(
        default_factory=lambda: ["funding_rate", "sopr", "stablecoin_supply", "open_interest"]
    )


# discriminated union (판별자 = archetype)
ArchetypeCard = Annotated[
    Union[CyclicalCard, EventDrivenCard, SpreadDrivenCard, AssetStableCard, CompounderCard,
          CommodityCarryCard, SeasonalCard, InventoryCard,
          MonetaryStoreCard, NetworkUtilityCard, SpeculativeFlowCard],
    Field(discriminator="archetype"),
]

ARCHETYPE_NAMES = ("cyclical", "event_driven", "spread_driven", "asset_stable", "compounder",
                   "commodity_carry", "seasonal", "inventory",
                   "monetary_store", "network_utility", "speculative_flow")
_CARD_CLASSES = {
    "cyclical": CyclicalCard,
    "event_driven": EventDrivenCard,
    "spread_driven": SpreadDrivenCard,
    "asset_stable": AssetStableCard,
    "compounder": CompounderCard,
    "commodity_carry": CommodityCarryCard,
    "seasonal": SeasonalCard,
    "inventory": InventoryCard,
    "monetary_store": MonetaryStoreCard,
    "network_utility": NetworkUtilityCard,
    "speculative_flow": SpeculativeFlowCard,
}


def parse_card(data: dict) -> "ArchetypeCard":
    """dict(YAML/JSON) → 검증된 ArchetypeCard (판별자로 자동 dispatch)."""
    from pydantic import TypeAdapter
    return TypeAdapter(ArchetypeCard).validate_python(data)


def card_class(archetype: str) -> type[_ArchetypeBase]:
    if archetype not in _CARD_CLASSES:
        raise ValueError(f"미지 archetype: {archetype!r} (가능: {ARCHETYPE_NAMES})")
    return _CARD_CLASSES[archetype]


# ---------------------------------------------------------------------------
# 섹터 → archetype 매핑 (PIT, 시변 가능) — v1 정적 기본값
# ---------------------------------------------------------------------------

DEFAULT_SECTOR_ARCHETYPE = {
    # equity (generic v1)
    "semiconductor": "cyclical",
    "chemicals": "cyclical",
    "steel": "cyclical",
    "biotech": "event_driven",
    "internet": "event_driven",
    "banks": "spread_driven",
    "brokers": "spread_driven",
    "utilities": "asset_stable",
    "telecom": "asset_stable",
    "software_compounder": "compounder",
    # equity KR (stock.md eq_kr 12산업 — 1차 가설 배정, 산업 study 가 검증·정정.
    #  ★frame v3 §M.5: valid_from PIT 사전선언 + soft/probabilistic 배정은 카드 레지스트리로 확장.
    #  현 dict 는 ex-ante 정적 fallback 일 뿐 — archetype transition 은 valid_from 카드로만 시변 박제)
    "kr_semiconductor": "cyclical",   # 반도체 (T1, DRAM 사이클)
    "kr_auto": "cyclical",            # 자동차 (경기민감)
    "kr_battery": "cyclical",         # 2차전지 (capex/리튬 사이클)
    "kr_bio": "event_driven",         # 바이오 (임상·승인 binary)
    "kr_consumer": "asset_stable",    # 소비재 (방어·안정, 일부 compounder = study 분기)
    "kr_financial": "spread_driven",  # 금융 (NIM·credit spread)
    "kr_telecom": "asset_stable",     # 통신 (배당·금리민감)
    # equity US (stock.md eq_us — ★배정단위 = Mag7 basket/macro-sleeve, GICS 11 아님)
    "us_mega_tech": "compounder",     # T0 = Mag7 + AVGO/ORCL/AMD (대형 테크 복리, expensive_trap)
    "us_cyclical": "cyclical",        # SOXX/XLB/XLI/XLE (경기민감 sleeve)
    "us_defensive": "asset_stable",   # XLP/XLU/XLV/XLC (방어 sleeve)
    # commodity (BB-5)
    "energy_crude": "commodity_carry",
    "energy_gas": "seasonal",
    "agriculture": "seasonal",
    "industrial_metals": "inventory",
    "precious_metals": "commodity_carry",
    # crypto (BB-5)
    "crypto_btc": "monetary_store",
    "crypto_eth": "network_utility",
    "crypto_alt": "speculative_flow",
}


def archetype_for_sector(sector: str) -> str:
    """섹터 → archetype (v1 정적). 시변 매핑은 valid_from 카드 레지스트리로 확장 예정."""
    return DEFAULT_SECTOR_ARCHETYPE.get(sector, "cyclical")


# ---------------------------------------------------------------------------
# config/archetypes/*.yaml 로더
# ---------------------------------------------------------------------------

def load_cards_from_config(config_dir: str | None = None) -> dict[str, "ArchetypeCard"]:
    """config/archetypes/*.yaml → {archetype: 검증된 ArchetypeCard}.

    각 YAML 은 판별자(archetype) 필드를 가지며 discriminated union 으로 검증된다.
    """
    import os
    import glob
    import yaml

    if config_dir is None:
        here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_dir = os.path.join(here, "config", "archetypes")
    cards: dict[str, ArchetypeCard] = {}
    for path in sorted(glob.glob(os.path.join(config_dir, "*.yaml"))):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        card = parse_card(data)
        cards[card.archetype] = card
    return cards


if __name__ == "__main__":
    # 5종 모두 생성 + 판별 round-trip 검증
    cards = {
        "cyclical": CyclicalCard(primary_metric="ev_ebitda",
                                 companion_signals=["book_to_bill", "gross_margin"],
                                 value_trap_guards=["peak_eps", "capex_rollover"],
                                 percentile_overfit_risk=True),
        "compounder": CompounderCard(primary_metric="roic_durability",
                                     value_trap_guards=["multiple_unwind", "growth_decel"]),
        # commodity (BB-5)
        "commodity_carry": CommodityCarryCard(primary_metric="roll_yield",
                                              value_trap_guards=["contango_flip", "inventory_glut"]),
        "seasonal": SeasonalCard(primary_metric="seasonal_zscore",
                                 value_trap_guards=["regime_break"],
                                 percentile_overfit_risk=True),
        "inventory": InventoryCard(primary_metric="days_of_supply",
                                   value_trap_guards=["oversupply_regime"]),
        # crypto (BB-5)
        "monetary_store": MonetaryStoreCard(primary_metric="mvrv",
                                            value_trap_guards=["network_impairment", "forced_deleverage"]),
        "network_utility": NetworkUtilityCard(primary_metric="fee_burn_yield",
                                              value_trap_guards=["high_apy_death_spiral"]),
        "speculative_flow": SpeculativeFlowCard(primary_metric="sopr",
                                                value_trap_guards=["liquidation_cascade", "permanent_impairment"],
                                                percentile_overfit_risk=True),
    }
    for name, c in cards.items():
        d = c.model_dump()
        rt = parse_card(d)
        assert rt.archetype == name, (name, rt.archetype)
        print(f"{name}: sign={rt.cheapness_sign} primary={rt.primary_metric} guards={rt.value_trap_guards}")
    print("discriminated union round-trip PASS")
    # config 로드
    loaded = load_cards_from_config()
    print(f"config 로드: {sorted(loaded)} ({len(loaded)}종)")
    for n in ARCHETYPE_NAMES:
        assert n in loaded, f"config 누락: {n}"
    print(f"config/archetypes/*.yaml {len(ARCHETYPE_NAMES)}종 검증 PASS")
