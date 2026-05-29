"""tests/test_stock_r15_weight.py — R15 평가지표 동적 가중이 주식 트랙 판정에 연결됐는지 GATE.

사용자 핵심 요청: "stock 트랙 판정에 지표별 가중치를 넣어달라". 이전엔 평가가 valuation_gap
단일 지표만 써서 R15 가중이 계산만 되고 평가에 미반영(끊김)이었다. StockTrack.generate_candidate
가 weight_card 주입 시 다중지표 합성 S_L1 을 buy sizing 에 반영하는지(끊김 해소) 검증.

자문 §1.4 정합: R15=L1 결정론(지표가중 cheapness, pre-agent) / value_trigger=down-only attenuator.
천장 불변식 final ≤ l1_size 강제.
"""

from __future__ import annotations

from core.asset_track import MarketState
from core.assume.weight_card import WeightAssumptionCard
from core.stock_track import StockTrack


def _wc(floor: float = 0.25) -> WeightAssumptionCard:
    return WeightAssumptionCard(
        id="weight.equity.semi", version="v1", kind="parametric", scope="sector", domain="equity",
        statement="반도체 cyclical 합성비중",
        falsification_metric="합성 score OOS Rank-IC e-process 붕괴 → kill",
        series_ids=("ev_ebitda_z", "book_to_bill", "inventory_qoq"),
        w_global=(0.5, 0.3, 0.2), floor=floor)


def _state(zvals: dict) -> MarketState:
    return MarketState(raw_market_data={}, raw_external_data=zvals,
                       raw_portfolio={}, raw_past_decisions=[])


def test_r15_buy_sizing_applied():
    """weight_card 주입 + 강한 지표 → buy sizing 에 S_L1 반영(끊김 해소 핵심)."""
    tr = StockTrack(_weight_card_override=_wc())
    state = _state({"ev_ebitda_z": -1.8, "book_to_bill": 1.2, "inventory_qoq": -0.1})
    # S_L1 = 0.5·(-1.8)+0.3·1.2+0.2·(-0.1) = -0.56 → clamp_floor(0.25) → -0.31, l1_size=0.31
    d = tr._apply_r15_sizing({"decision": "buy", "confidence": 0.8, "reason": "opp"},
                             state, None, "SEMI")
    assert "r15_s_l1" in d and abs(d["r15_s_l1"] - (-0.31)) < 1e-9
    assert abs(d["confidence"] - 0.31 * 0.8) < 1e-9          # l1_size × value_atten(down-only)
    assert d["confidence"] <= 0.31 + 1e-12                   # ★천장 불변식


def test_r15_deadzone_abstain():
    """약한 지표 합성 → deadzone(|S_L1|≤floor) → abstain(지표가중상 엣지 없음)."""
    tr = StockTrack(_weight_card_override=_wc())
    state = _state({"ev_ebitda_z": 0.2, "book_to_bill": 0.1, "inventory_qoq": 0.0})  # Σw·z=0.13<0.25
    d = tr._apply_r15_sizing({"decision": "buy", "confidence": 0.8, "reason": "opp"},
                             state, None, "SEMI")
    assert d["decision"] == "hold" and d["confidence"] == 0.0


def test_r15_no_card_unchanged():
    """weight_card 미주입 → 기존 결정 그대로(무회귀)."""
    tr = StockTrack()
    state = _state({"ev_ebitda_z": -1.8})
    d = tr._apply_r15_sizing({"decision": "buy", "confidence": 0.8, "reason": "opp"},
                             state, None, "SEMI")
    assert d["confidence"] == 0.8 and "r15_s_l1" not in d


def test_r15_indicator_z_override():
    """indicator_z override 우선 + series 누락=0 기여."""
    tr = StockTrack(_weight_card_override=_wc(),
                    _indicator_z_override={"ev_ebitda_z": -2.0, "book_to_bill": 1.0,
                                           "inventory_qoq": 0.0})
    d = tr._apply_r15_sizing({"decision": "buy", "confidence": 1.0, "reason": "x"},
                             _state({}), None, "SEMI")
    # S_L1 = 0.5·(-2.0)+0.3·1.0+0.2·0 = -0.7 → clamp_floor(0.25) → -0.45(r15_s_l1=clamp 후), ×1.0
    assert abs(d["r15_s_l1"] - (-0.45)) < 1e-9 and abs(d["confidence"] - 0.45) < 1e-9


def test_r15_hold_not_affected():
    """buy 가 아니면(hold/reject) R15 미적용(L1 base sizing 은 진입 결정에만)."""
    tr = StockTrack(_weight_card_override=_wc())
    d = tr._apply_r15_sizing({"decision": "hold", "confidence": 0.0, "reason": "reject"},
                             _state({"ev_ebitda_z": -1.8}), None, "SEMI")
    assert d["decision"] == "hold" and "r15_s_l1" not in d


def test_r15_ceiling_invariant_all_value_conf():
    """★천장 불변식 — 어떤 value_trigger confidence(attenuator)도 final ≤ l1_size."""
    tr = StockTrack(_weight_card_override=_wc())
    state = _state({"ev_ebitda_z": -1.8, "book_to_bill": 1.2, "inventory_qoq": -0.1})  # l1_size=0.31
    for vc in (0.0, 0.3, 0.7, 1.0):
        d = tr._apply_r15_sizing({"decision": "buy", "confidence": vc, "reason": "o"},
                                 state, None, "SEMI")
        assert d["confidence"] <= 0.31 + 1e-12, (vc, d["confidence"])
