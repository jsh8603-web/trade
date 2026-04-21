"""
collect_macro.analyze_macro 추세 필드 유닛 테스트.

v1.32.2에서 market_context_log 매핑을 위해 추가된 네 필드를 검증한다:
  - sp500_trend
  - dxy_trend (달러 인덱스는 크립토와 역 상관 → inverse=True)
  - gold_trend
  - macro_sentiment

네트워크 호출 없이 analyze_macro(quotes) 를 직접 호출한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# scripts/ 경로를 sys.path에 추가 (다른 테스트와 동일한 패턴)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.collect_macro import analyze_macro


# ── Helpers ──────────────────────────────────────────────


def make_quote(change_pct: float = 0.0, five_day_change_pct: float = 0.0) -> dict:
    """최소한의 parse_quote 호환 딕셔너리를 만든다."""
    return {
        "price": 100.0,
        "prev_close": 100.0,
        "change_pct": change_pct,
        "five_day_change_pct": five_day_change_pct,
        "currency": "USD",
    }


def analyze_with(**quotes) -> dict:
    """지정한 심볼만 포함된 quotes로 analyze_macro를 실행한다."""
    return analyze_macro(quotes)


# ── S&P 500 trend ──────────────────────────────────────────


def test_sp500_bullish_when_change_pct_above_1():
    """일간 변동률이 1% 초과면 bullish."""
    result = analyze_with(sp500=make_quote(change_pct=1.5))
    assert result["sp500_trend"] == "bullish"


def test_sp500_bearish_when_change_pct_below_minus1():
    """일간 변동률이 -1% 미만이면 bearish."""
    result = analyze_with(sp500=make_quote(change_pct=-1.5))
    assert result["sp500_trend"] == "bearish"


def test_sp500_neutral_for_small_moves():
    """일간 0.5% + 5일 2% 모두 트리거 미달이면 neutral."""
    result = analyze_with(sp500=make_quote(change_pct=0.5, five_day_change_pct=2))
    assert result["sp500_trend"] == "neutral"


def test_sp500_bullish_on_five_day_trigger():
    """일간 변동이 작아도 5일 추세가 3% 초과면 bullish."""
    result = analyze_with(sp500=make_quote(change_pct=0.2, five_day_change_pct=4))
    assert result["sp500_trend"] == "bullish"


# ── DXY trend (inverse) ───────────────────────────────────


def test_dxy_inverse_bullish_when_dollar_weakens():
    """달러 약세(-1.5%)는 크립토 관점에서 bullish."""
    result = analyze_with(dxy=make_quote(change_pct=-1.5))
    assert result["dxy_trend"] == "bullish"


def test_dxy_inverse_bearish_when_dollar_strengthens():
    """달러 강세(+1.5%)는 크립토 관점에서 bearish."""
    result = analyze_with(dxy=make_quote(change_pct=1.5))
    assert result["dxy_trend"] == "bearish"


def test_dxy_five_day_inverse():
    """달러 5일 강세(+4%)도 inverse 로직에 의해 bearish."""
    result = analyze_with(dxy=make_quote(change_pct=0.0, five_day_change_pct=4))
    assert result["dxy_trend"] == "bearish"


# ── Gold trend ────────────────────────────────────────────


def test_gold_trend_same_as_sp500_logic():
    """금은 동행 로직이므로 +2%는 bullish."""
    result = analyze_with(gold=make_quote(change_pct=2))
    assert result["gold_trend"] == "bullish"


def test_gold_trend_bearish_on_drop():
    """금 일간 -2%는 bearish."""
    result = analyze_with(gold=make_quote(change_pct=-2))
    assert result["gold_trend"] == "bearish"


# ── macro_sentiment == sentiment ──────────────────────────


def test_macro_sentiment_matches_sentiment():
    """macro_sentiment 는 항상 sentiment 와 동일한 값이어야 한다."""
    quotes = {
        "sp500": make_quote(change_pct=1.5),
        "dxy": make_quote(change_pct=-1.5),
        "gold": make_quote(change_pct=2),
    }
    result = analyze_macro(quotes)
    assert result["macro_sentiment"] == result["sentiment"]


def test_macro_sentiment_matches_sentiment_neutral_case():
    """심볼이 비어 있어도 둘 다 'neutral' 로 일치."""
    result = analyze_macro({})
    assert result["macro_sentiment"] == result["sentiment"]
    assert result["macro_sentiment"] == "neutral"


# ── Missing / error cases ────────────────────────────────


def test_missing_quote_key_returns_neutral():
    """quotes에 sp500 키 자체가 없으면 neutral."""
    result = analyze_with(dxy=make_quote(change_pct=-1.5))
    assert result["sp500_trend"] == "neutral"


def test_error_quote_returns_neutral():
    """quotes.sp500 에 error 필드만 있으면 neutral."""
    result = analyze_macro({"sp500": {"error": "데이터 없음"}})
    assert result["sp500_trend"] == "neutral"


def test_all_error_quotes_return_neutral():
    """모든 심볼이 error 상태여도 네 필드 모두 neutral."""
    quotes = {
        "sp500": {"error": "fail"},
        "dxy": {"error": "fail"},
        "gold": {"error": "fail"},
    }
    result = analyze_macro(quotes)
    assert result["sp500_trend"] == "neutral"
    assert result["dxy_trend"] == "neutral"
    assert result["gold_trend"] == "neutral"
    assert result["macro_sentiment"] == "neutral"


# ── Boundary tests ────────────────────────────────────────


def test_sp500_boundary_exactly_1_is_neutral():
    """경계값: change_pct == 1.0 은 strict `> 1` 조건에 걸리지 않으므로 neutral."""
    result = analyze_with(sp500=make_quote(change_pct=1.0, five_day_change_pct=0))
    assert result["sp500_trend"] == "neutral"


def test_sp500_boundary_just_above_1_is_bullish():
    """경계값: change_pct == 1.01 은 bullish."""
    result = analyze_with(sp500=make_quote(change_pct=1.01, five_day_change_pct=0))
    assert result["sp500_trend"] == "bullish"


def test_sp500_boundary_exactly_minus1_is_neutral():
    """경계값: change_pct == -1.0 은 strict `< -1` 조건에 걸리지 않으므로 neutral."""
    result = analyze_with(sp500=make_quote(change_pct=-1.0, five_day_change_pct=0))
    assert result["sp500_trend"] == "neutral"


def test_sp500_boundary_just_below_minus1_is_bearish():
    """경계값: change_pct == -1.01 은 bearish."""
    result = analyze_with(sp500=make_quote(change_pct=-1.01, five_day_change_pct=0))
    assert result["sp500_trend"] == "bearish"


def test_sp500_five_day_boundary_exactly_3_is_neutral():
    """경계값: 5일 변동률 == 3.0 은 strict `> 3` 이 아니므로 neutral."""
    result = analyze_with(sp500=make_quote(change_pct=0.0, five_day_change_pct=3.0))
    assert result["sp500_trend"] == "neutral"


def test_dxy_boundary_exactly_minus1_is_neutral():
    """dxy 경계값: change_pct == -1.0 도 neutral (strict)."""
    result = analyze_with(dxy=make_quote(change_pct=-1.0))
    assert result["dxy_trend"] == "neutral"


# ── Result shape ─────────────────────────────────────────


def test_result_contains_all_four_new_fields():
    """analyze_macro 반환 dict에 네 필드가 모두 존재해야 한다."""
    result = analyze_macro({})
    for key in ("sp500_trend", "dxy_trend", "gold_trend", "macro_sentiment"):
        assert key in result, f"missing key: {key}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
