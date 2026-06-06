"""tests/test_a2_stock_adapter.py — A2 stock track 어댑터 단위 테스트.

검증: stock_track.generate_candidate dict 반환 → _stock_track_adapter → action 속성 도달.
★A2 SR 발견: action!=hold 단언(stock 주문 경로 도달 가능 확인).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util
import types

# run_multiasset 를 올바른 모듈 이름으로 등록 후 임포트
def _load_run_multiasset():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "scripts", "run_multiasset.py")
    spec = importlib.util.spec_from_file_location("scripts.run_multiasset", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["scripts.run_multiasset"] = mod
    spec.loader.exec_module(mod)
    return mod

_mod = _load_run_multiasset()
_stock_track_adapter = _mod._stock_track_adapter
_StockDecision = _mod._StockDecision

from core.asset_track import MarketState


class _BuyStub:
    """valuation 주입 시뮬 — buy dict 반환."""
    def generate_candidate(self, state):
        return {"decision": "buy", "confidence": 0.8, "reason": "stub_buy", "trade_params": {}}

class _AbstainStub:
    def generate_candidate(self, state):
        return {"decision": "abstain", "confidence": 0.0, "reason": "abstain_test"}

class _ObjWithAction:
    def generate_candidate(self, state):
        return type("D", (), {"action": "sell", "confidence": 0.5})()


def test_buy_dict_reaches_action():
    """★A2 핵심: stock buy dict → .action=="buy" (주문시도 도달)."""
    state = MarketState(raw_market_data={"ticker": "005930"})
    d = _stock_track_adapter(_BuyStub(), state)
    assert d.action == "buy", f"expected buy, got {d.action}"


def test_abstain_normalizes_to_hold():
    state = MarketState(raw_market_data={"ticker": "005930"})
    d = _stock_track_adapter(_AbstainStub(), state)
    assert d.action == "hold", f"expected hold, got {d.action}"


def test_obj_with_action_passthrough():
    state = MarketState(raw_market_data={"ticker": "005930"})
    d = _stock_track_adapter(_ObjWithAction(), state)
    assert d.action == "sell", f"expected sell, got {d.action}"


def test_none_track_returns_hold():
    state = MarketState(raw_market_data={})
    d = _stock_track_adapter(None, state)
    assert d.action == "hold", f"expected hold, got {d.action}"


def test_run_one_cycle_dry_run():
    """1사이클 DRY_RUN weights 합=1."""
    result = _mod.run_one_cycle(dry_run=True)
    assert result["dry_run"] is True
    assert abs(result["weights_sum"] - 1.0) < 1e-6, f"weights_sum={result['weights_sum']}"
    assert result["coin_action"] in ("buy", "sell", "hold")
    assert result["stock_action"] in ("buy", "sell", "hold")


def test_stock_buy_reaches_orders_attempted():
    """stock buy → orders_attempted=1 (주문 경로 계상)."""
    class _BuyTrack:
        def generate_candidate(self, s): return {"decision": "buy", "confidence": 0.8, "reason": "buy"}

    result = _mod.run_one_cycle(
        dry_run=True,
        stock_track=_BuyTrack(),
    )
    assert result["stock_action"] == "buy", f"got {result['stock_action']}"
    assert result["orders_attempted"] >= 1, f"orders_attempted={result['orders_attempted']}"
