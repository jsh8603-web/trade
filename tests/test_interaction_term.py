"""WIRE3.5-Gb 테스트: composite_cheapness_z interaction term (factor×factor 곱항).

검증기준:
- interactions=None → 기존 선형합과 byte-identical
- interactions 주입 → 곱항 반영(랭킹 변화), 측정코드(interaction_z=z(z1·z2)) 구조 일치
- m1/m2 metric_panel 부재 → 해당 항 skip(0 기여)
- DEF-2 시나리오: 두 factor 모두 상위 종목이 interaction 양 기여
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stock.cross_sectional_selection import composite_cheapness_z


# div_yield, op_prof 각각 (높을수록 쌈 sign +1). A 둘 다 고 / B div고 op저 / C div저 op고 / D 둘 다 저
PANEL = {
    "div": {"A": 5.0, "B": 4.5, "C": 1.0, "D": 0.5, "E": 2.5},
    "op":  {"A": 5.0, "B": 1.0, "C": 4.5, "D": 0.5, "E": 2.5},
}
SIGNS = {"div": 1, "op": 1}


def test_interaction_none_byte_identical():
    """interactions=None → 기존 선형합 결과와 완전 동일."""
    a = composite_cheapness_z(PANEL, SIGNS)
    b = composite_cheapness_z(PANEL, SIGNS, interactions=None)
    assert a == b


def test_interaction_on_changes_result():
    """interaction 주입 → 곱항 반영으로 composite z 변화."""
    off = composite_cheapness_z(PANEL, SIGNS)
    on = composite_cheapness_z(PANEL, SIGNS, interactions=[("div", "op", 1)])
    assert on != off


def test_interaction_missing_metric_skipped():
    """m1/m2 가 metric_panel 에 없으면 그 항 skip → 기존과 동일."""
    off = composite_cheapness_z(PANEL, SIGNS)
    on = composite_cheapness_z(PANEL, SIGNS, interactions=[("div", "nonexistent", 1)])
    assert on == off


def test_interaction_both_high_gets_boost():
    """DEF-2 시나리오(생짜 곱항): 두 factor 모두 상위인 A 가 곱 양 기여로 상대 상승.

    A(div고·op고)는 z_div·z_op 둘 다 큰 양수 → 곱 큰 양수. interaction_residualize=False
    (생짜 곱항)에서 A 가 B/C 대비 추가 우위. (default True 잔차화는 main 직교화라 별 거동.)
    """
    off = composite_cheapness_z(PANEL, SIGNS)
    on = composite_cheapness_z(PANEL, SIGNS, interactions=[("div", "op", 1)],
                               interactions_residualize=False)
    da = on["A"] - off["A"]
    db = on["B"] - off["B"]
    dc = on["C"] - off["C"]
    assert da > db
    assert da > dc


def test_interaction_residualize_differs_from_raw():
    """★FWL 잔차화(default) vs 생짜 곱항 → 결과 다름 (main 직교화가 합성 바꿈)."""
    resid = composite_cheapness_z(PANEL, SIGNS, interactions=[("div", "op", 1)])
    raw = composite_cheapness_z(PANEL, SIGNS, interactions=[("div", "op", 1)],
                                interactions_residualize=False)
    assert resid != raw


def test_interaction_sign_flips():
    """sign=−1 interaction 은 곱항을 반대 방향 기여."""
    pos = composite_cheapness_z(PANEL, SIGNS, interactions=[("div", "op", 1)])
    neg = composite_cheapness_z(PANEL, SIGNS, interactions=[("div", "op", -1)])
    assert pos != neg
    # A 는 곱 양 → +1 이면 상승, −1 이면 하락
    off = composite_cheapness_z(PANEL, SIGNS)
    assert (pos["A"] - off["A"]) * (neg["A"] - off["A"]) < 0
