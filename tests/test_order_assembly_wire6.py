"""WIRE6 테스트: stock/order_assembly (selection Decision → GatedOrderRouter → broker, flag-gated).

검증기준 (사용자 2026-06-05 "연결은 다 해두고 flag on/off"):
- DRY_RUN=True(default) → broker.order 호출 0 (실주문 0, status=shadow)
- EMERGENCY_STOP=True → 전면 차단 (status=shadow, reason=emergency_stop)
- 모든 주문 = router.submit(via_gate=True) 경유 강제 (risk_gate 우회 불가)
- risk_gate REJECTED → status=rejected, broker 미호출
- dry_run=False + broker 주입 → broker.order 호출 (status=sent)
- target_weight<=0 skip
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.risk_gate import RiskVerdict, VerdictType
from stock.order_assembly import assemble_stock_orders


class _MockRouter:
    """GatedOrderRouter 대역 — via_gate 호출 기록 + verdict 고정."""

    def __init__(self, approved: bool = True):
        self.calls: list = []
        self._approved = approved

    def submit(self, order, *, cycle_id="", via_gate=False, **kw):
        self.calls.append({"order": order, "via_gate": via_gate})
        vt = VerdictType.APPROVED if self._approved else VerdictType.REJECTED
        return RiskVerdict(vt, "mock")


class _MockBroker:
    def __init__(self):
        self.orders: list = []

    def order(self, ticker, side, qty, **kw):
        self.orders.append({"ticker": ticker, "side": side, "qty": qty})
        return {"ok": True}


_DECISIONS = [
    {"ticker": "A", "target_weight": 0.1, "cheapness_z": 1.2, "rank": 1},
    {"ticker": "B", "target_weight": 0.1, "cheapness_z": 0.8, "rank": 2},
    {"ticker": "C", "target_weight": 0.0, "rank": 99},   # skip (tw=0)
]


def test_dry_run_default_no_live_order():
    """DRY_RUN default(True) → broker 미호출, status=shadow (실주문 0)."""
    router, broker = _MockRouter(approved=True), _MockBroker()
    out = assemble_stock_orders(_DECISIONS, router=router, broker=broker, dry_run=True)
    assert len(broker.orders) == 0                       # ★실주문 0건
    assert all(r["status"] == "shadow" for r in out)
    assert all(r["reason"] == "dry_run" for r in out)


def test_via_gate_always_true():
    """모든 주문이 router.submit(via_gate=True) 경유 (risk_gate 우회 불가)."""
    router = _MockRouter(approved=True)
    assemble_stock_orders(_DECISIONS, router=router, dry_run=True)
    assert len(router.calls) == 2                         # tw>0 2건
    assert all(c["via_gate"] is True for c in router.calls)


def test_emergency_stop_blocks():
    """EMERGENCY_STOP=True → status=shadow reason=emergency_stop, broker 미호출."""
    router, broker = _MockRouter(approved=True), _MockBroker()
    out = assemble_stock_orders(_DECISIONS, router=router, broker=broker,
                                dry_run=False, emergency_stop=True)
    assert len(broker.orders) == 0
    assert all(r["reason"] == "emergency_stop" for r in out)


def test_risk_gate_rejected():
    """risk_gate REJECTED → status=rejected, broker 미호출."""
    router, broker = _MockRouter(approved=False), _MockBroker()
    out = assemble_stock_orders(_DECISIONS, router=router, broker=broker, dry_run=False)
    assert len(broker.orders) == 0
    assert all(r["status"] == "rejected" for r in out)


def test_flag_on_sends_to_broker():
    """dry_run=False + emergency_stop=False + broker 주입 → broker.order 호출 (status=sent)."""
    router, broker = _MockRouter(approved=True), _MockBroker()
    out = assemble_stock_orders(_DECISIONS, router=router, broker=broker,
                                dry_run=False, emergency_stop=False)
    assert len(broker.orders) == 2                       # ★flag on = 실 발송 (A, B)
    assert {o["ticker"] for o in broker.orders} == {"A", "B"}
    assert all(r["status"] == "sent" for r in out)


def test_no_broker_falls_to_shadow():
    """broker 미주입 → dry_run=False 여도 shadow(reason=no_broker)."""
    router = _MockRouter(approved=True)
    out = assemble_stock_orders(_DECISIONS, router=router, broker=None, dry_run=False)
    assert all(r["status"] == "shadow" and r["reason"] == "no_broker" for r in out)


def test_zero_weight_skipped():
    """target_weight<=0 = 주문 조립 제외."""
    router = _MockRouter(approved=True)
    out = assemble_stock_orders(_DECISIONS, router=router, dry_run=True)
    assert {r["ticker"] for r in out} == {"A", "B"}      # C(tw=0) 제외
