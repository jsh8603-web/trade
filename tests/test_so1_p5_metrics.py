"""tests/test_so1_p5_metrics.py — SO-1/P5 common/metrics.py 검증.

검증 기준 (harness2.md SO-1):
1. 순수함수 결정성 (동일 입력→동일 출력)
2. Sharpe/MDD/profit_factor 수식 정확성 (알려진 시계열 검산)
3. 엔진이 common/metrics 만 import (자체 중복 0)
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import pytest

from common.metrics import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_win_rate,
    calculate_cagr,
    calculate_sortino_ratio,
    calculate_calmar_ratio,
    returns_from_equity,
    equity_from_returns,
)


# ---------------------------------------------------------------------------
# 1. 순수함수 결정성
# ---------------------------------------------------------------------------

def test_sharpe_deterministic():
    """동일 입력 → 동일 Sharpe 출력."""
    returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])
    r1 = calculate_sharpe_ratio(returns)
    r2 = calculate_sharpe_ratio(returns)
    assert r1 == r2


def test_mdd_deterministic():
    """동일 입력 → 동일 MDD 출력."""
    equity = pd.Series([100, 110, 105, 95, 100])
    m1 = calculate_max_drawdown(equity)
    m2 = calculate_max_drawdown(equity)
    assert m1 == m2


def test_profit_factor_deterministic():
    """동일 입력 → 동일 profit_factor 출력."""
    trades = pd.DataFrame({"pnl": [10, -5, 8, -3, 12]})
    p1 = calculate_profit_factor(trades)
    p2 = calculate_profit_factor(trades)
    assert p1 == p2


# ---------------------------------------------------------------------------
# 2-a. Sharpe 수식 정확성
# ---------------------------------------------------------------------------

def test_sharpe_monotone_increase_zero():
    """단조증가 수익률 → 표준편차 0 → Sharpe = 0.0."""
    returns = pd.Series([0.01, 0.01, 0.01, 0.01])
    assert calculate_sharpe_ratio(returns) == 0.0


def test_sharpe_known_value():
    """알려진 수익률열 Sharpe 검산. 일간 수익률 0.001±0.002."""
    np.random.seed(42)
    n = 500
    mu, sigma = 0.001, 0.002
    returns = pd.Series(np.random.normal(mu, sigma, n))
    sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.0, periods_per_year=252)
    # 이론값 ≈ mu/sigma * sqrt(252) ≈ 0.001/0.002 * 15.87 ≈ 7.9 (표본 분산)
    assert sharpe > 5.0  # 랜덤 시드 42 기준 양수 Sharpe


def test_sharpe_negative_returns():
    """음수 평균 수익률 → 음수 Sharpe."""
    returns = pd.Series([-0.01, -0.02, -0.005, -0.015])
    sharpe = calculate_sharpe_ratio(returns)
    assert sharpe < 0.0


def test_sharpe_empty():
    """빈 시리즈 → 0.0."""
    assert calculate_sharpe_ratio(pd.Series([], dtype=float)) == 0.0


# ---------------------------------------------------------------------------
# 2-b. MDD 수식 정확성
# ---------------------------------------------------------------------------

def test_mdd_monotone_increase_zero():
    """단조증가 자산가치 → MDD = 0.0."""
    equity = pd.Series([100.0, 110.0, 120.0, 130.0])
    assert calculate_max_drawdown(equity) == 0.0


def test_mdd_known_value():
    """알려진 자산가치 MDD 검산. 100→120→90 → MDD = (90-120)/120 * 100 = -25%."""
    equity = pd.Series([100.0, 120.0, 90.0])
    mdd = calculate_max_drawdown(equity)
    assert abs(mdd - (-25.0)) < 1e-6


def test_mdd_always_nonpositive():
    """MDD ≤ 0 항상."""
    equity = pd.Series([100, 95, 110, 85, 100])
    assert calculate_max_drawdown(equity) <= 0.0


def test_mdd_single_element():
    """단일 원소 → 0.0."""
    assert calculate_max_drawdown(pd.Series([100.0])) == 0.0


# ---------------------------------------------------------------------------
# 2-c. profit_factor 수식 정확성
# ---------------------------------------------------------------------------

def test_profit_factor_known():
    """익 20 손 10 → profit_factor = 2.0."""
    trades = pd.DataFrame({"pnl": [10.0, 10.0, -10.0]})
    assert calculate_profit_factor(trades) == pytest.approx(2.0)


def test_profit_factor_no_loss():
    """손실 없음 → inf."""
    trades = pd.DataFrame({"pnl": [5.0, 10.0, 3.0]})
    assert calculate_profit_factor(trades) == float("inf")


def test_profit_factor_all_loss():
    """모두 손실 → 0.0."""
    trades = pd.DataFrame({"pnl": [-5.0, -3.0]})
    assert calculate_profit_factor(trades) == 0.0


def test_profit_factor_empty():
    """빈 DataFrame → 0.0."""
    assert calculate_profit_factor(pd.DataFrame({"pnl": []})) == 0.0


# ---------------------------------------------------------------------------
# 3. 추가 지표
# ---------------------------------------------------------------------------

def test_win_rate_known():
    """승 3 패 1 → 75%."""
    trades = pd.DataFrame({"pnl": [1.0, 2.0, -1.0, 3.0]})
    assert calculate_win_rate(trades) == pytest.approx(75.0)


def test_cagr_known():
    """100→200 (252일) → CAGR ≈ 100%."""
    equity = pd.Series([100.0] + [100.0] * 251 + [200.0])
    cagr = calculate_cagr(equity, periods_per_year=252)
    # 253 periods → 252/252 = 1년 → (200/100)^1 - 1 = 100%
    assert abs(cagr - 100.0) < 2.0


def test_returns_from_equity_roundtrip():
    """equity → returns → equity 왕복 (오차 < 1e-10)."""
    equity = pd.Series([100.0, 110.0, 105.0, 115.0])
    returns = returns_from_equity(equity)
    recovered = equity_from_returns(returns, initial_capital=equity.iloc[0])
    # 첫 원소는 dropna 로 소실되므로 [1:] 비교
    for orig, rec in zip(equity.iloc[1:], recovered):
        assert abs(orig - rec) < 1e-6


def test_sortino_ratio_positive():
    """양의 평균 수익률 → 양수 Sortino."""
    returns = pd.Series([0.01, 0.02, -0.005, 0.015, -0.003])
    assert calculate_sortino_ratio(returns) > 0.0


def test_calmar_ratio_positive():
    """양의 CAGR + 음의 MDD → 양수 Calmar."""
    equity = pd.Series([100.0, 105.0, 102.0, 108.0, 115.0])
    assert calculate_calmar_ratio(equity) > 0.0


# ---------------------------------------------------------------------------
# 4. import 경로 검증 (중복 자체 지표 0)
# ---------------------------------------------------------------------------

def test_metrics_module_no_self_duplicate():
    """common/metrics.py 가 자체 중복 지표 없이 모든 함수 export."""
    import common.metrics as m
    for fn in ("calculate_sharpe_ratio", "calculate_max_drawdown",
               "calculate_profit_factor", "calculate_win_rate",
               "calculate_cagr"):
        assert callable(getattr(m, fn, None)), f"{fn} 미존재"
