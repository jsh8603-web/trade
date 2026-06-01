"""core/observability/rule_attributor.py — 반사실 PnL attribution (S7, F축, 불변식④).

claude R6 F1:
- PnL_rule = PnL_actual − PnL_baseline(floor/ceiling 만 적용한 기준선). Shapley-lite.
- ⚠️ **veto 가 entry 를 막으면 기여 = 음수(0 아님)**. 막은 거래가 나중에 올랐으면 그만큼
  손해를 끼친 것 → **opportunity cost 별도 계상** (불변식④).

Trade Tagging: 모든 주문에 trigger_rule_version 태깅 → rule 별 가상 PnL 귀속.
Shapley-lite: 한 거래에 여러 rule 이 겹치면 균등 분배(완전 Shapley 는 v2).

⛔ 관측 계열(모듈 4분리). 실제 주문/포지션을 안 만든다. 기록된 trade tag 로 사후 귀속만.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TradeTag:
    """체결 거래 1건. trigger_rules = 이 거래를 유발한 rule_version 목록(중첩 가능)."""
    trade_id: str
    trigger_rules: list[str]
    pnl_actual: float          # 실제 실현 PnL
    pnl_baseline: float        # floor/ceiling 만 적용한 기준선 PnL


@dataclass
class VetoEvent:
    """rule veto 가 막은 가상 entry. counterfactual_pnl = 안 막았으면 났을 PnL."""
    veto_id: str
    veto_rule: str
    counterfactual_pnl: float  # 막은 거래가 났을 경우의 PnL (양수면 기회손실)


@dataclass
class AttributionReport:
    rule_pnl: dict = field(default_factory=dict)          # rule → 실거래 기여 합
    rule_opportunity_cost: dict = field(default_factory=dict)  # rule → veto 기회비용(음수)
    rule_net: dict = field(default_factory=dict)          # 기여 + 기회비용
    notes: list[str] = field(default_factory=list)


class RuleAttributor:
    def attribute(self, trades: list[TradeTag], vetoes: Optional[list[VetoEvent]] = None) -> AttributionReport:
        rep = AttributionReport()
        pnl = defaultdict(float)
        # 실거래 기여: (actual − baseline) 을 trigger rule 들에 Shapley-lite 균등 분배
        for t in trades:
            excess = t.pnl_actual - t.pnl_baseline
            if not t.trigger_rules:
                continue
            share = excess / len(t.trigger_rules)
            for r in t.trigger_rules:
                pnl[r] += share

        # opportunity cost: veto 가 막은 거래가 양(+) 이었으면 음(−) 기여 (불변식④)
        oppc = defaultdict(float)
        for v in (vetoes or []):
            # 막은 게 이득이었으면(+) rule 에 음수 기여, 손실 회피였으면(−) 양수(veto 가 옳았음)
            oppc[v.veto_rule] += -v.counterfactual_pnl

        rep.rule_pnl = dict(pnl)
        rep.rule_opportunity_cost = dict(oppc)
        allr = set(pnl) | set(oppc)
        rep.rule_net = {r: pnl.get(r, 0.0) + oppc.get(r, 0.0) for r in allr}
        for r in sorted(allr):
            rep.notes.append(f"{r}: 거래기여={pnl.get(r,0):.3f} 기회비용={oppc.get(r,0):.3f} 순={rep.rule_net[r]:.3f}")
        return rep


if __name__ == "__main__":
    att = RuleAttributor()

    trades = [
        TradeTag("t1", ["cyc_cheapz_v2"], pnl_actual=0.08, pnl_baseline=0.03),   # +0.05 기여
        TradeTag("t2", ["cyc_cheapz_v2", "cyc_pb_v1"], pnl_actual=0.06, pnl_baseline=0.04),  # +0.02 분배
        TradeTag("t3", ["cyc_pb_v1"], pnl_actual=-0.02, pnl_baseline=0.01),      # -0.03 기여
    ]
    vetoes = [
        VetoEvent("v1", "cyc_trap_peak_v1", counterfactual_pnl=-0.10),  # 막은 게 손실회피 → 양수 기여
        VetoEvent("v2", "cyc_trap_peak_v1", counterfactual_pnl=0.07),   # 막은 게 이득이었음 → 음수 기여(기회손실)
    ]
    rep = att.attribute(trades, vetoes)

    # 1) 거래 기여
    assert abs(rep.rule_pnl["cyc_cheapz_v2"] - (0.05 + 0.01)) < 1e-9, rep.rule_pnl
    print(f"1) 거래기여 cyc_cheapz_v2={rep.rule_pnl['cyc_cheapz_v2']:.3f} cyc_pb_v1={rep.rule_pnl['cyc_pb_v1']:.3f}")

    # 2) opportunity cost (veto): 손실회피(+0.10) + 기회손실(-0.07) = +0.03 순
    assert abs(rep.rule_opportunity_cost["cyc_trap_peak_v1"] - 0.03) < 1e-9, rep.rule_opportunity_cost
    print(f"2) 기회비용 cyc_trap_peak_v1={rep.rule_opportunity_cost['cyc_trap_peak_v1']:.3f} (손실회피+기회손실)")

    # 3) veto 가 entry 막은 게 이득이었으면 음수 기여가 반영됨 (불변식④)
    only_miss = att.attribute([], [VetoEvent("v9", "r", counterfactual_pnl=0.05)])
    assert only_miss.rule_opportunity_cost["r"] == -0.05, only_miss.rule_opportunity_cost
    print(f"3) 기회손실만: r={only_miss.rule_opportunity_cost['r']:.3f} (veto 가 오른 거래 막음=음수, 불변식④)")

    print("S7 rule_attributor self-test PASS")
