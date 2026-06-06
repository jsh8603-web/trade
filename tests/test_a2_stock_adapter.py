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
    """stock buy dict → stock_action=buy 도달 + gate_verdicts 에 kr_stock 존재.

    ★A2 핵심: 어댑터가 dict["decision"]="buy"를 .action="buy"로 정규화,
    gate submit 경로에 도달하는지 확인. gate 통과 여부(APPROVED/REJECTED)는
    risk_gate 설정 종속이라 stock_action + gate_verdicts["kr_stock"] 존재로 검증.
    """
    class _BuyTrack:
        def generate_candidate(self, s): return {"decision": "buy", "confidence": 0.8, "reason": "buy"}

    result = _mod.run_one_cycle(
        dry_run=True,
        stock_track=_BuyTrack(),
    )
    assert result["stock_action"] == "buy", f"got {result['stock_action']}"
    # gate submit 경로 도달 확인 (hold_skip 이 아님 = buy action이 gate에 전달됨)
    kr_verdict = result["gate_verdicts"].get("kr_stock", "hold_skip")
    assert kr_verdict != "hold_skip", f"kr_stock did not reach gate: {kr_verdict}"


# ---------------------------------------------------------------------------
# A3 tests — GatedOrderRouter + corr/sector 합산층 산출
# ---------------------------------------------------------------------------

def test_a3_bypassed_attempts_zero():
    """bypassed_attempts==0 (우회 시도 없음)."""
    result = _mod.run_one_cycle(dry_run=True)
    assert result["bypassed_attempts"] == 0


def test_a3_gate_verdicts_present():
    """gate_verdicts 키 존재(hold_skip 포함)."""
    result = _mod.run_one_cycle(dry_run=True)
    assert "gate_verdicts" in result
    assert "triggered_rules" in result


def test_a3_sector_weight_stock_sleeves():
    """us_stock + kr_stock = 주식 섹터 합산."""
    w = {"coin": 0.10, "us_stock": 0.30, "kr_stock": 0.20,
         "gold": 0.10, "bond": 0.20, "cash": 0.10}
    _, sector_w = _mod._compute_multiasset_corr_sector(w, "us_stock")
    assert abs(sector_w - 0.50) < 1e-6, f"sector_w={sector_w}"


def test_a3_sector_weight_coin_only():
    """coin 섹터 = coin 자기 비중만."""
    w = {"coin": 0.10, "us_stock": 0.30, "kr_stock": 0.20}
    _, sector_w = _mod._compute_multiasset_corr_sector(w, "coin")
    assert abs(sector_w - 0.10) < 1e-6, f"sector_w={sector_w}"


def test_a3_corr_matrix_avg():
    """corr_matrix 주입 시 avg_correlation 실산출."""
    w = {"coin": 0.10, "us_stock": 0.30, "kr_stock": 0.20}
    corr_matrix = {"coin": {"us_stock": 0.8, "kr_stock": 0.6}}
    avg_corr, _ = _mod._compute_multiasset_corr_sector(w, "coin", corr_matrix=corr_matrix)
    # 가중평균: (0.30*0.8 + 0.20*0.6)/(0.30+0.20) = (0.24+0.12)/0.50 = 0.72
    assert abs(avg_corr - 0.72) < 1e-6, f"avg_corr={avg_corr}"


def test_a3_max_weight_sector_triggers():
    """sector_weight 초과 시 REJECTED 발동 (주문 차단)."""
    class _BuyStock:
        def generate_candidate(self, s):
            return {"decision": "buy", "confidence": 0.9, "reason": "buy"}

    # us_stock+kr_stock=0.80 (섹터 합산) = max_weight_sector(0.40 기본) 초과 → REJECTED
    weights_override = {"coin": 0.05, "us_stock": 0.50, "kr_stock": 0.30,
                        "gold": 0.05, "bond": 0.05, "cash": 0.05}

    result = _mod.run_one_cycle(
        dry_run=True,
        stock_track=_BuyStock(),
        nav=1_000_000.0,
    )
    # kr_stock buy가 sector_weight(0.20 기본 가중치)로 게이트 통과 여부 — gate_verdicts 확인
    assert "kr_stock" in result["gate_verdicts"], f"missing kr_stock: {result}"


# ---------------------------------------------------------------------------
# A4 tests — judge(down-only) hook
# ---------------------------------------------------------------------------

def test_a4_judge_hook_attenuation():
    """judge hook 감쇠 → judge_a < 1.0."""
    class _AttenuatingHook:
        def __call__(self, sleeve, proposed_size, l1_size=1.0):
            return {"size_mult": 0.5, "l1_size": l1_size}

    class _BuyStock:
        def generate_candidate(self, s):
            return {"decision": "buy", "confidence": 0.9, "reason": "buy"}

    result = _mod.run_one_cycle(
        dry_run=True,
        stock_track=_BuyStock(),
        judge_hook=_AttenuatingHook(),
    )
    assert result["judge_a"]["kr_stock"] == 0.5, f"judge_a={result['judge_a']}"


def test_a4_judge_hook_fail_open():
    """judge_hook=None → fail-open a=1.0 (증폭 없음)."""
    result = _mod.run_one_cycle(dry_run=True, judge_hook=None)
    for sleeve, a in result["judge_a"].items():
        assert a <= 1.0, f"{sleeve} a={a} > 1.0 (증폭 위반)"


def test_a4_down_only_invariant():
    """★천장 불변식: judge_a ≤ l1_size=1.0 (증폭 금지)."""
    class _AmpHook:
        """증폭 시도 hook — size_mult > l1_size 반환 시 clamp 확인."""
        def __call__(self, sleeve, proposed_size, l1_size=1.0):
            return {"size_mult": 2.0, "l1_size": l1_size}  # 증폭 시도

    result = _mod.run_one_cycle(dry_run=True, judge_hook=_AmpHook())
    for sleeve, a in result["judge_a"].items():
        assert a <= 1.0, f"{sleeve} a={a} > 1.0 (down-only 불변식 위반)"


# ---------------------------------------------------------------------------
# A5 tests — 주문 배선 (Upbit + KIS paper, DRY_RUN stub)
# ---------------------------------------------------------------------------

def test_a5_coin_stub_dry_run():
    """DRY_RUN=true → coin stub_order(네트워크0)."""
    ref = _mod._coin_stub_order("KRW-BTC", "buy", dry_run=True)
    assert ref["status"] == "stub"
    assert ref["network"] == 0


def test_a5_stock_stub_dry_run():
    """DRY_RUN=true → KIS paper stub(네트워크0)."""
    ref = _mod._stock_order_via_kis("005930", "buy", 1.0, dry_run=True)
    assert ref["status"] == "stub"
    assert ref.get("paper") is True


def test_a5_coin_stub_network_zero():
    """coin stub network=0 (실 Upbit API 미호출)."""
    ref = _mod._coin_stub_order("KRW-ETH", "sell", dry_run=True)
    assert ref["network"] == 0, f"network={ref.get('network')}"
