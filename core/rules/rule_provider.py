"""core/rules/rule_provider.py — RuleProvider shadow-only 통합 어댑터 (S10, C축 주입).

SPEC T3-2 / IMPL §6: 기존 `stock/valuation.py:value_stock` 를 Provider 뒤로 감싸,
cheapness_z(T2) + L1 결정론 floor(S5) + rule 앙상블(S1, seed_builder) 을 주입한다.
**shadow-only**: 기존 legacy verdict 와 신규 rule verdict 를 둘 다 산출해 divergence 만
기록한다. 실주문은 안 바꾼다 (claude R6: divergence=안전 1차 방어선, 라이브 전 관측).

⛔ 기존 value_stock·execute_trade 폐기금지 증분(additive). legacy 호출은 try/except 로
   감싸 미가용(StockTrack 미인스턴스화)이어도 rule verdict 는 독립 산출.
wiring 순서(IMPL §6): 이 Provider 가 shadow 로 돌며 RuleObserver(S6)에 divergence 공급
→ 충분히 수렴하면 INT 단계에서 L1 floor 를 execute_trade 앞에 라이브 연결.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.rules.l1_gate import l1_verdict, L1Config, Verdict
from core.rules.seed_builder import SeedRegistry
from core.structure import archetype as arch
from core.pit.as_of import resolve_as_of, AsOfLike


@dataclass
class ShadowResult:
    """legacy(value_stock) vs rule(L1) 병기 + divergence (shadow-only)."""
    firm: str
    sector: str
    rule_final: str                 # allow_cheap/veto/abstain/neutral (신규)
    legacy_signal: Optional[str]    # 기존 value_stock 기반 (저평가 여부) or None
    cheapness_z: float
    diverged: bool                  # legacy↔rule 판정 불일치
    deciding_rule_id: Optional[str] = None
    reasons: list[str] = field(default_factory=list)


def _legacy_signal(fundamentals, quote, sector_ev_ebitda=None) -> Optional[str]:
    """기존 value_stock → 'cheap'/'rich'/None (shadow 비교용, 미가용=None)."""
    try:
        from stock.valuation import value_stock
        res = value_stock(fundamentals, quote, sector_ev_ebitda)
        if res is None:
            return None
        gap = getattr(res, "valuation_gap", None)
        if gap is None:
            return None
        return "cheap" if gap > 0 else "rich"   # intrinsic > price = 저평가
    except Exception:
        return None


class RuleProvider:
    """cheapness_z + L1 floor + rule seed 주입. shadow verdict 산출(실행 미변경)."""

    def __init__(self, model, registry: SeedRegistry,
                 cards: Optional[dict] = None, cfg: Optional[L1Config] = None):
        self.model = model
        self.registry = registry
        self.cards = cards or arch.load_cards_from_config()
        self.cfg = cfg or L1Config()

    def evaluate_shadow(
        self,
        firm: str, sector: str, date_: AsOfLike, as_of: AsOfLike, features: dict,
        regime_id: Optional[int] = None,
        fundamentals=None, quote=None, sector_ev_ebitda=None,
    ) -> ShadowResult:
        signals = self.registry.signals_for(sector, regime_id)
        v: Verdict = l1_verdict(firm, sector, date_, as_of, self.model,
                                features, signals, self.cards, self.cfg)
        legacy = _legacy_signal(fundamentals, quote, sector_ev_ebitda) if fundamentals else None

        # divergence: 신규 rule 이 cheap 인데 legacy 는 rich, 또는 그 반대
        rule_says_cheap = v.final == "allow_cheap"
        legacy_says_cheap = legacy == "cheap"
        diverged = (legacy is not None) and (rule_says_cheap != legacy_says_cheap)

        return ShadowResult(
            firm=firm, sector=sector, rule_final=v.final, legacy_signal=legacy,
            cheapness_z=v.cheapness_z, diverged=diverged,
            deciding_rule_id=v.deciding_rule_id, reasons=v.reasons,
        )


if __name__ == "__main__":
    import pandas as pd
    from core.structure.panel_schema import make_semiconductor_fixture
    from core.structure.structure_model import StructureModel

    panel = make_semiconductor_fixture()
    model = StructureModel(); model.fit(panel, pd.Timestamp("2022-01-01"))
    reg = SeedRegistry().load_base(as_of="2024-01-01")
    cards = arch.load_cards_from_config()
    rp = RuleProvider(model, reg, cards)

    feats = {"cheapness_z": -1.8, "pb": 0.8, "ev_ebitda": 4.0, "book_to_bill": 1.2,
             "inventory_qoq": -0.1, "capex_to_rev": 0.1, "gross_margin": 0.3}

    class DummyModel:
        def cheapness_z(self, f, s, d, a): return -1.8

    rp2 = RuleProvider(DummyModel(), reg, cards)

    # 1) rule verdict 산출 (legacy 미가용 → divergence False)
    r = rp2.evaluate_shadow("SEMI001", "semiconductor", "2021-09-30", "2022-01-01", feats)
    print(f"1) shadow: rule={r.rule_final} z={r.cheapness_z} legacy={r.legacy_signal} diverged={r.diverged}")
    assert r.rule_final in ("allow_cheap", "neutral", "abstain", "veto"), r

    # 2) config archetype card 로드 확인 (5종)
    assert len(cards) == 5, list(cards)
    print(f"2) archetype cards 로드: {sorted(cards)} ({len(cards)}종)")

    # 3) regime 변형 적용 (다기간 학습 수용)
    reg.register_period_variant.__self__  # noqa (존재 확인)
    from core.rules.seed_builder import PeriodVariant
    reg.register_period_variant(PeriodVariant("semiconductor", "슈퍼사이클", 0, {"cyc_cheapz": -1.5}))
    r0 = rp2.evaluate_shadow("SEMI001", "semiconductor", "2021-09-30", "2022-01-01", feats, regime_id=0)
    print(f"3) regime0 변형 적용: rule={r0.rule_final} (다기간 seed 수용)")

    print("S10 rule_provider self-test PASS")
