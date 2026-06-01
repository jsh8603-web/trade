"""tests/test_corp_action.py — 기업행위 전처리 검증 (Phase2 T1 WP-T1-D)."""

from __future__ import annotations

from datetime import datetime

from core.data.corp_action import (
    CorpAction, CorpActionType, split_factor, adjust_price, adjust_shares,
    market_cap_continuous, detect_unflagged_split,
)


def test_split_factor_future_only():
    actions = [
        CorpAction("A", datetime(2023, 6, 1), CorpActionType.SPLIT, 2.0),
        CorpAction("A", datetime(2024, 6, 1), CorpActionType.SPLIT, 5.0),
    ]
    # as_of 2023-01-01: 둘 다 미래 → 2*5=10
    assert split_factor(actions, datetime(2023, 1, 1)) == 10.0
    # as_of 2023-12-01: 2024 분할만 미래 → 5
    assert split_factor(actions, datetime(2023, 12, 1)) == 5.0
    # as_of 2025-01-01: 미래 분할 없음 → 1
    assert split_factor(actions, datetime(2025, 1, 1)) == 1.0


def test_reverse_split():
    actions = [CorpAction("A", datetime(2024, 1, 1), CorpActionType.REVERSE_SPLIT, 5.0)]
    assert split_factor(actions, datetime(2023, 1, 1)) == 0.2  # 1/5


def test_adjust_price_shares():
    assert adjust_price(1000.0, 2.0) == 500.0      # 분할 후 기준 환산
    assert adjust_shares(100.0, 2.0) == 200.0


def test_market_cap_continuity():
    # 2:1 분할: 가격 반토막, 주식수 2배 → 시총 동일
    assert market_cap_continuous(1000, 100, 500, 200) is True
    # 실질 가치 변화(시총 +20%) → 분할 artifact 아님
    assert market_cap_continuous(1000, 100, 600, 200) is False


def test_detect_unflagged_split():
    actions = [CorpAction("A", datetime(2023, 6, 1), CorpActionType.SPLIT, 2.0)]
    win = (datetime(2023, 1, 1), datetime(2023, 12, 31))
    # 주식수 2배 점프 + 로그 있음 → 미기록 아님
    assert detect_unflagged_split(100, 200, actions, "A", win) is False
    # 주식수 3배 점프 + 로그 없음(firm B) → 미기록 의심
    assert detect_unflagged_split(100, 300, actions, "B", win) is True
    # 점프 없음 → False
    assert detect_unflagged_split(100, 110, [], "A", win) is False
