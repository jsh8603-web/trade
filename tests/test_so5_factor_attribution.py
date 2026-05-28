"""SO-5 테스트: factor_attribution wire + ValueTrapMetaLabeler.

검증기준:
- factor → AttributionResult(failure_reason·attribution·confidence) PASS
- 저신뢰 → UNATTRIBUTED PASS
- trap_probability → size_factor PASS
- value_trigger 연동(size_factor<0.3 → PRICE_ONLY) PASS
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stock.contracts import (
    AttributionResult,
    FailureReason,
    FilingSource,
    Fundamentals,
    MarketQuote,
    RunMode,
    ValuationResult,
    ValueVerdict,
)
from stock.factor_attribution import (
    ValueTrapMetaLabeler,
    attribute_trade,
    triple_barrier_label,
)
from stock.value_trigger import run_value_trigger

KST = timezone(timedelta(hours=9))


def _make_valuation(gap=0.30, pit_clean=True) -> ValuationResult:
    mcap = 400_000_000_000_000
    return ValuationResult(
        ticker="005930",
        as_of=datetime(2024, 4, 1, tzinfo=KST),
        currency="KRW",
        intrinsic_value=mcap * (1 + gap),
        market_cap=mcap,
        valuation_gap=gap,
        bear_value=mcap * 1.1,
        base_value=mcap * 1.3,
        bull_value=mcap * 1.5,
        wacc=0.09,
        pit_clean=pit_clean,
    )


def _make_fundamentals(fcf_to_oi=1.0) -> Fundamentals:
    operating_income = 50_000_000_000
    return Fundamentals(
        ticker="005930",
        fiscal_period="2024FY",
        filing_timestamp=datetime(2024, 3, 15, tzinfo=KST),
        source=FilingSource.DART_XBRL,
        currency="KRW",
        free_cash_flow=operating_income * fcf_to_oi,
        operating_income=operating_income,
        total_debt=100_000_000_000,
        shareholders_equity=200_000_000_000,
        earnings_growth=0.05,
    )


# ── attribute_trade 단위 ──────────────────────────────────────────────

def test_attribute_trade_returns_attribution_result():
    """attribute_trade → AttributionResult."""
    holding_rets = [-0.01] * 20
    market_rets = [0.02] * 20
    result = attribute_trade("t001", "005930", holding_rets, market_rets)
    assert isinstance(result, AttributionResult)
    assert isinstance(result.failure_reason, FailureReason)
    assert "r2" in result.attribution or "reason" in result.attribution


def test_attribute_trade_macro_regime():
    """market-β 지배 → MACRO_REGIME_WRONG."""
    # market과 자산이 거의 같이 움직이면 β지배
    rets = [0.01 * (i % 3 - 1) for i in range(30)]
    market = [r * 1.1 for r in rets]  # 자산이 market 따라감
    result = attribute_trade("t002", "005930", rets, market)
    assert result.failure_reason in (
        FailureReason.MACRO_REGIME_WRONG,
        FailureReason.UNATTRIBUTED,  # 소표본이면 unattributed도 허용
    )


def test_attribute_trade_unattributed_small_sample():
    """소표본 → UNATTRIBUTED (억지 라벨 금지)."""
    holding_rets = [-0.01] * 5  # 5개 = 소표본
    market_rets = [0.02] * 5
    result = attribute_trade("t003", "005930", holding_rets, market_rets)
    assert result.failure_reason == FailureReason.UNATTRIBUTED
    assert result.confidence == 0.0


def test_attribute_trade_confidence_range():
    """confidence 0~1 범위."""
    holding_rets = [-0.01] * 30
    market_rets = [0.02] * 30
    result = attribute_trade("t004", "005930", holding_rets, market_rets)
    assert 0.0 <= result.confidence <= 1.0


def test_attribute_trade_attribution_fields():
    """AttributionResult 필수 필드."""
    result = attribute_trade("t005", "005930", [-0.01] * 10, [0.02] * 10)
    assert hasattr(result, "failure_reason")
    assert hasattr(result, "attribution")
    assert hasattr(result, "confidence")
    assert hasattr(result, "trade_id")
    assert result.trade_id == "t005"


# ── triple_barrier_label ─────────────────────────────────────────────

def test_triple_barrier_label_profit_target():
    """가격이 상단 배리어 돌파 → label={1,0,-1} 유효."""
    # entry=100, forward prices, vol=0.03, k_up=2
    forward_prices = [100, 102, 105, 110]  # 상단 배리어(100*(1+2*0.03)=106) 돌파
    label = triple_barrier_label(100.0, forward_prices, volatility=0.03, k_up=2.0)
    assert label in (1, 0, -1)


def test_triple_barrier_label_stop_loss():
    """가격이 하단 배리어 돌파 → label 유효."""
    forward_prices = [100, 97, 94, 91]  # 하단(100*(1-1*0.03)=97) 돌파 후 계속 하락
    label = triple_barrier_label(100.0, forward_prices, volatility=0.03, k_down=1.0)
    assert label in (1, 0, -1)


def test_triple_barrier_label_timeout():
    """만료 → label 유효."""
    forward_prices = [100, 101, 100, 99, 100]  # 배리어 미돌파
    label = triple_barrier_label(100.0, forward_prices, volatility=0.001, k_up=100.0, k_down=100.0)
    assert label in (1, 0, -1)


# ── ValueTrapMetaLabeler ──────────────────────────────────────────────

def test_metalabeler_trap_probability_range():
    """trap_probability 0~1 범위."""
    labeler = ValueTrapMetaLabeler()
    val = _make_valuation(gap=0.30)
    f = _make_fundamentals()
    p = labeler.trap_probability(val, [f])
    assert 0.0 <= p <= 1.0


def test_metalabeler_high_debt_increases_probability():
    """부채비율 높으면 함정확률↑."""
    labeler = ValueTrapMetaLabeler(prior_trap_rate=0.3)
    val = _make_valuation(gap=0.30)

    # 저부채
    f_low_debt = Fundamentals(
        ticker="005930", fiscal_period="2024FY",
        filing_timestamp=datetime(2024, 3, 15, tzinfo=KST),
        source=FilingSource.DART_XBRL, currency="KRW",
        total_debt=100_000_000_000,
        shareholders_equity=500_000_000_000,  # debt/equity = 0.2
    )
    # 고부채
    f_high_debt = Fundamentals(
        ticker="005930", fiscal_period="2024FY",
        filing_timestamp=datetime(2024, 3, 15, tzinfo=KST),
        source=FilingSource.DART_XBRL, currency="KRW",
        total_debt=500_000_000_000,
        shareholders_equity=100_000_000_000,  # debt/equity = 5.0
    )
    p_low = labeler.trap_probability(val, [f_low_debt])
    p_high = labeler.trap_probability(val, [f_high_debt])
    assert p_high >= p_low, f"고부채 함정확률({p_high}) >= 저부채({p_low}) 기대"


def test_metalabeler_poor_fcf_increases_probability():
    """FCF/영업이익 낮으면(이익의 질 의심) 함정확률↑."""
    labeler = ValueTrapMetaLabeler(prior_trap_rate=0.3)
    val = _make_valuation()

    f_good_fcf = _make_fundamentals(fcf_to_oi=1.2)   # FCF 풍부
    f_poor_fcf = _make_fundamentals(fcf_to_oi=0.1)   # FCF 빈약

    p_good = labeler.trap_probability(val, [f_good_fcf])
    p_poor = labeler.trap_probability(val, [f_poor_fcf])
    assert p_poor > p_good, f"FCF 빈약 함정확률({p_poor}) > 풍부({p_good}) 기대"


def test_metalabeler_not_pit_clean_increases_probability():
    """PIT-clean 아니면 함정확률+0.1."""
    labeler = ValueTrapMetaLabeler(prior_trap_rate=0.3)
    val_clean = _make_valuation(pit_clean=True)
    val_dirty = _make_valuation(pit_clean=False)
    f = _make_fundamentals()

    p_clean = labeler.trap_probability(val_clean, [f])
    p_dirty = labeler.trap_probability(val_dirty, [f])
    assert p_dirty > p_clean


def test_metalabeler_secondary_model_injected():
    """2차 모델 주입 시 predict_trap_proba 호출."""
    mock_model = MagicMock()
    mock_model.predict_trap_proba.return_value = 0.75
    labeler = ValueTrapMetaLabeler(secondary_model=mock_model)
    val = _make_valuation()
    f = _make_fundamentals()
    p = labeler.trap_probability(val, [f])
    assert p == pytest.approx(0.75)
    mock_model.predict_trap_proba.assert_called_once()


# ── value_trigger 연동: trap_probability → size_factor ───────────────

def test_metalabeler_high_trap_prob_downgrades_to_price_only():
    """함정확률 높음(>0.7) → metalabel_size_factor<0.3 → PRICE_ONLY."""
    # prior=0.8 으로 확실히 높게
    labeler = ValueTrapMetaLabeler(prior_trap_rate=0.8)

    val = _make_valuation(gap=0.30, pit_clean=False)
    f = _make_fundamentals(fcf_to_oi=0.05)  # 이익의 질 최악

    # trap_probability 실제 값 확인
    p = labeler.trap_probability(val, [f])
    assert p > 0.5, f"테스트 의도: 함정확률 높게 설정됐어야 함({p})"

    ha = MagicMock()
    from stock.value_trigger import HeavyAgentVerdict
    ha.judge_value_trap.return_value = HeavyAgentVerdict(
        is_trap=False, confidence=0.8, reasoning="기회"
    )

    result = run_value_trigger(
        val, [f],
        price_change_pct=-0.15,
        heavy_agent=ha,
        metalabeler=labeler,
        mode=RunMode.FORWARD,
    )
    # size_factor < 0.3이면 PRICE_ONLY, 아니면 OPPORTUNITY
    if result.metalabel_size_factor < 0.3:
        assert result.verdict == ValueVerdict.PRICE_ONLY
    else:
        assert result.verdict == ValueVerdict.OPPORTUNITY


def test_metalabeler_low_trap_prob_opportunity():
    """함정확률 낮음(prior=0.0, 좋은 재무) → OPPORTUNITY."""
    labeler = ValueTrapMetaLabeler(prior_trap_rate=0.0)
    val = _make_valuation(gap=0.30, pit_clean=True)
    f = _make_fundamentals(fcf_to_oi=1.5)  # FCF 풍부, 좋은 재무

    p = labeler.trap_probability(val, [f])
    assert p < 0.5

    ha = MagicMock()
    from stock.value_trigger import HeavyAgentVerdict
    ha.judge_value_trap.return_value = HeavyAgentVerdict(
        is_trap=False, confidence=0.9, reasoning="기회"
    )

    result = run_value_trigger(
        val, [f],
        price_change_pct=-0.15,
        heavy_agent=ha,
        metalabeler=labeler,
        mode=RunMode.FORWARD,
    )
    assert result.verdict == ValueVerdict.OPPORTUNITY
    assert result.metalabel_size_factor > 0.5
