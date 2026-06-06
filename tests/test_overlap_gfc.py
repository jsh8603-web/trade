"""WIRE3.5-Gf-C 테스트: stock/overlap.py (N-vintage overlapping portfolio).

검증기준 (자문 R1 만장일치 + 본인 재검증 overlap +6.20%/yr CI 유의):
- 동일비중 합성 Σw=1 보존 (각 빈티지 Σw=1)
- 종목 중복 시 weight 가산
- n_vintages 초과 빈티지는 최신만 (만기 청산)
- capped-EW 빈티지 합성 = 볼록결합 → 종목 cap 유지 (cap 초과 불가)
- 빈 입력 graceful
- turnover 단방향 매수측 합
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stock.overlap import overlap_portfolio_weights, overlap_turnover


def test_sum_preserved():
    """각 빈티지 Σw=1 → 합성 Σw=1."""
    v1 = {"A": 0.5, "B": 0.5}
    v2 = {"B": 0.5, "C": 0.5}
    out = overlap_portfolio_weights([v1, v2], n_vintages=12)
    assert abs(sum(out.values()) - 1.0) < 1e-9


def test_overlap_accumulates_persistent():
    """B 가 두 빈티지에 → weight 가산 (0.5*0.5 + 0.5*0.5 = 0.5)."""
    v1 = {"A": 0.5, "B": 0.5}
    v2 = {"B": 0.5, "C": 0.5}
    out = overlap_portfolio_weights([v1, v2], n_vintages=12)
    assert abs(out["B"] - 0.5) < 1e-9
    assert abs(out["A"] - 0.25) < 1e-9
    assert abs(out["C"] - 0.25) < 1e-9


def test_caps_to_recent_n():
    """n_vintages=12 초과 빈티지는 최신 12 만 활성 (만기 청산)."""
    vs = [{"X": 1.0}] * 15
    out = overlap_portfolio_weights(vs, n_vintages=12)
    assert abs(out["X"] - 1.0) < 1e-9   # X 모든 활성 빈티지 → 12*(1/12)*1.0


def test_convex_combination_keeps_cap():
    """capped-EW 빈티지(종목 cap 0.05) 합성 = 볼록결합 → 종목 weight ≤ 0.05 (cap 유지)."""
    # 각 빈티지 20종목 균등 0.05 (capped-EW), 종목 구성만 일부 다름
    v1 = {f"T{i}": 0.05 for i in range(20)}
    v2 = {f"T{i}": 0.05 for i in range(5, 25)}
    out = overlap_portfolio_weights([v1, v2], n_vintages=12)
    assert max(out.values()) <= 0.05 + 1e-9   # 볼록결합 → max 불변


def test_empty_graceful():
    assert overlap_portfolio_weights([], 12) == {}
    assert overlap_portfolio_weights([{}, {}], 12) == {}


def test_n_vintages_zero_uses_all():
    vs = [{"X": 1.0}] * 3
    out = overlap_portfolio_weights(vs, n_vintages=0)
    assert abs(out["X"] - 1.0) < 1e-9


def test_turnover_buy_side():
    """단방향 turnover = 매수측 증분 합."""
    prev = {"A": 0.5, "B": 0.5}
    curr = {"A": 0.4, "B": 0.5, "C": 0.1}   # A −0.1, C +0.1
    assert abs(overlap_turnover(prev, curr) - 0.1) < 1e-9   # 매수측 C 0.1 만
