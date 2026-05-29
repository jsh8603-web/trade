"""core/assume/orphan_guard.py — orphaned 포지션 managed-exit (CL-3, 축F). 청산폭주 방어.

가정 retire → 그 가정이 trigger 한 결정으로 잡은 포지션이 "고아"가 된다. 일괄 즉시청산은
동시다발 retire 시 gridlock(매매마비). 방어(claude R1 Q4):
 - mode 분기: hard-retract(falsifier 발화)만 fast 청산. soft(adopt transition)는 즉시청산 X →
   re-derivation→shadow 경로(dag grace/lazy 가 처리). 고아 즉시청산은 hard 한정.
 - 도메인 netting: 같은 instrument 가 여러 결정/도메인서 상쇄되면 net 만 집행(중복청산 0).
 - token-bucket rate-limit(book 레벨): 동시다발 retire 시 청산 토큰 한도 → 초과분 deferred(폭주 차단).
 - decay: card.half_life 로 신뢰도 시간감쇠 → 재검증 전 점진 사이징 축소(절벽 회피).

역추적은 DecisionLedger(frozen) rule_version 매칭. 집행(실주문)은 호출자 — 여기선 ExitOrder 산출만.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExitOrder:
    instrument: str
    domain: str
    delta: float                 # 청산 수량(부호) = -보유. long→음수(매도), short→양수(매수)
    reason: str
    decision_ids: list[str] = field(default_factory=list)


@dataclass
class OrphanResult:
    """managed-exit 산출. issued=토큰 허용 집행분 / deferred=한도초과 보류분(다음 refill)."""
    card_id: str
    mode: str
    issued: list[ExitOrder] = field(default_factory=list)
    deferred: list[ExitOrder] = field(default_factory=list)


class TokenBucket:
    """book 레벨 청산 rate-limiter. capacity 만큼만 즉시 집행, 초과는 deferred."""

    def __init__(self, capacity: int, *, refill_per_call: int = 0):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_per_call = refill_per_call

    def refill(self) -> None:
        self.tokens = min(self.capacity, self.tokens + self.refill_per_call)

    def take(self, n: int = 1) -> int:
        grant = max(0, min(n, int(self.tokens)))
        self.tokens -= grant
        return grant


def decayed_confidence(card, age_days: float) -> float:
    """card.half_life 로 신뢰도 시간감쇠. posterior * 0.5**(age/half_life). half_life 부재→무감쇠."""
    base = float(getattr(card, "posterior_confidence", 0.5) or 0.5)
    hl = getattr(card, "half_life", None)
    if not hl or hl <= 0:
        return base
    return base * (0.5 ** (max(0.0, float(age_days)) / float(hl)))


def _matches(rule_version: str, card_id: str) -> bool:
    """결정의 rule_version 이 이 카드에서 나왔는지. 'card_id' 또는 'card_id@ver' 매칭."""
    return rule_version == card_id or rule_version.startswith(card_id + "@")


def on_assumption_retired(card_id: str, registry, ledger, positions: dict, *,
                          mode: str = "hard", bucket: Optional[TokenBucket] = None) -> OrphanResult:
    """retire → 역추적 → managed-exit. hard 만 fast 청산, soft 는 shadow(빈 집행).

    positions = {instrument: {"qty": float, "domain": str}}. ledger = DecisionLedger.
    """
    res = OrphanResult(card_id=card_id, mode=mode)
    # soft(adopt transition) = 즉시청산 안 함 → re-derivation/shadow(dag grace) 경로
    if mode != "hard":
        return res

    # 1) 역추적: 이 가정이 trigger 한 결정 → 영향 instrument
    triggered = [d for d in ledger.all() if _matches(d.rule_version, card_id)]

    # 2~3) 도메인 netting: instrument 별 1회 flatten (여러 결정/도메인 상쇄 → net 만)
    net: dict[str, ExitOrder] = {}
    for d in triggered:
        pos = positions.get(d.firm)
        if not pos:
            continue
        qty = float(pos.get("qty", 0.0))
        if qty == 0.0:
            continue
        if d.firm not in net:
            net[d.firm] = ExitOrder(
                instrument=d.firm, domain=pos.get("domain", "unknown"),
                delta=-qty, reason=f"orphan(retire {card_id}) flatten", decision_ids=[])
        net[d.firm].decision_ids.append(d.decision_id)
    orders = [o for o in net.values() if abs(o.delta) > 1e-12]

    # 4) token-bucket rate-limit: 한도 내만 즉시, 초과 deferred
    if bucket is None:
        res.issued = orders
        return res
    grant = bucket.take(len(orders))
    res.issued = orders[:grant]
    res.deferred = orders[grant:]
    return res


if __name__ == "__main__":
    from core.rules.ledger import DecisionLedger, DecisionRecord
    from core.assume.card_contract import BaseAssumptionFields

    def _dec(did, firm, rule_version, action="buy"):
        return DecisionRecord(decision_id=did, ts="2026-05-01", firm=firm, sector="semi",
                              as_of="2026-05-01", rule_version=rule_version, regime_id=0,
                              regime_model_version="rm_2026", verdict="cheap",
                              cheapness_z=-1.5, action=action)

    led = DecisionLedger()
    led.record(_dec("d1", "AAPL", "equity.per_floor@v1"))
    led.record(_dec("d2", "AAPL", "equity.per_floor@v1"))   # 같은 firm 두 결정 → netting 대상
    led.record(_dec("d3", "MSFT", "equity.per_floor@v1"))
    led.record(_dec("d4", "XOM", "commodity.carry@v1"))      # 다른 가정 → 무관
    positions = {"AAPL": {"qty": 100.0, "domain": "equity"},
                 "MSFT": {"qty": -50.0, "domain": "equity"},  # short
                 "XOM": {"qty": 200.0, "domain": "commodity"}}

    # 1) hard retract: AAPL(net 1회 flatten) + MSFT(short→매수청산). XOM 무관(다른 가정)
    r1 = on_assumption_retired("equity.per_floor", None, led, positions, mode="hard")
    by = {o.instrument: o for o in r1.issued}
    print(f"1) hard: {[(o.instrument, o.delta) for o in r1.issued]}")
    assert set(by) == {"AAPL", "MSFT"}, set(by)
    assert by["AAPL"].delta == -100.0 and by["MSFT"].delta == 50.0
    # netting: AAPL 두 결정(d1,d2) → 1 ExitOrder
    assert sorted(by["AAPL"].decision_ids) == ["d1", "d2"]
    print("   netting OK: AAPL 2결정 → 1청산, XOM(타가정) 제외")

    # 2) soft transition: 즉시청산 X (shadow/re-derivation 경로)
    r2 = on_assumption_retired("equity.per_floor", None, led, positions, mode="soft")
    print(f"2) soft: issued={len(r2.issued)} (즉시청산 안 함)")
    assert r2.issued == []

    # 3) token-bucket: capacity 1 → 1 집행 / 1 deferred (폭주 차단)
    bucket = TokenBucket(capacity=1)
    r3 = on_assumption_retired("equity.per_floor", None, led, positions, mode="hard", bucket=bucket)
    print(f"3) token-bucket(cap1): issued={len(r3.issued)} deferred={len(r3.deferred)}")
    assert len(r3.issued) == 1 and len(r3.deferred) == 1

    # 4) decay: half_life=30, posterior=0.8 → age30 절반(0.4), age0 원값(0.8), half_life 부재 무감쇠
    c_hl = BaseAssumptionFields(id="x", kind="parametric", scope="global", domain="equity",
                                statement="s", falsification_metric="f",
                                posterior_confidence=0.8, half_life=30.0)
    c_no = BaseAssumptionFields(id="y", kind="parametric", scope="global", domain="equity",
                                statement="s", falsification_metric="f", posterior_confidence=0.8)
    print(f"4) decay: age0={decayed_confidence(c_hl,0):.3f} age30={decayed_confidence(c_hl,30):.3f} "
          f"no_hl={decayed_confidence(c_no,99):.3f}")
    assert abs(decayed_confidence(c_hl, 0) - 0.8) < 1e-9
    assert abs(decayed_confidence(c_hl, 30) - 0.4) < 1e-9
    assert abs(decayed_confidence(c_no, 99) - 0.8) < 1e-9

    print("CL-3 orphan_guard self-test PASS "
          "(hard fast / soft shadow / 도메인netting / token-bucket / half_life decay)")
