"""common/metrics.py — 백테스트=라이브 공유 지표 SSOT (SO-1/P5).

WHY: coin sim_engine·base_agent·backtest_v6 가 Sharpe/MDD/profit_factor 를 3중 중복으로 정의.
     이 파일이 단일 SSOT 가 되어 백테스트 엔진(SO-2~)이 import 한다.
     coin 3중 중복 제거(common/metrics 일원화)는 Phase R(DRY_RUN 패리티 후) — 본 Phase5 는
     신규 엔진만 이 모듈을 import, coin 라이브 본체 미변경.

reuse-as-is: yakub268 _refs/algo-trading-platform/backtest/walk_forward.py
  :96  calculate_sharpe_ratio
  :110 calculate_max_drawdown
  :120 calculate_profit_factor
  → 순수함수 그대로 차용 (재코딩 금지).
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 기본 지표 — yakub268 walk_forward.py:96/110/120 그대로 채택 (재코딩 금지)
# ---------------------------------------------------------------------------

def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """연율화 Sharpe ratio. yakub268 walk_forward.py:96 그대로."""
    if len(returns) < 2 or returns.std() == 0:
        return 0.0
    excess_returns = returns - risk_free_rate / periods_per_year
    sharpe = np.sqrt(periods_per_year) * excess_returns.mean() / excess_returns.std()
    return float(sharpe)


def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    """최대 낙폭 %. yakub268 walk_forward.py:110 그대로. 반환값 ≤ 0."""
    if len(equity_curve) < 2:
        return 0.0
    rolling_max = equity_curve.expanding().max()
    drawdown = (equity_curve - rolling_max) / rolling_max * 100
    return float(drawdown.min())


def calculate_profit_factor(trades: pd.DataFrame) -> float:
    """총익/총손 비율. yakub268 walk_forward.py:120 그대로. 손실 없으면 inf."""
    if "pnl" not in trades.columns or len(trades) == 0:
        return 0.0
    gross_profit = trades[trades["pnl"] > 0]["pnl"].sum()
    gross_loss = abs(trades[trades["pnl"] < 0]["pnl"].sum())
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


# ---------------------------------------------------------------------------
# 추가 공통 지표
# ---------------------------------------------------------------------------

def calculate_win_rate(trades: pd.DataFrame) -> float:
    """승률 (%). trades DataFrame 에 'pnl' 컬럼 필요."""
    if "pnl" not in trades.columns or len(trades) == 0:
        return 0.0
    wins = (trades["pnl"] > 0).sum()
    return float(wins / len(trades) * 100)


def calculate_cagr(
    equity_curve: pd.Series,
    periods_per_year: int = 252,
) -> float:
    """연율화 복리수익률 (CAGR). equity_curve 는 절대 자산가치."""
    if len(equity_curve) < 2:
        return 0.0
    start = equity_curve.iloc[0]
    end = equity_curve.iloc[-1]
    if start <= 0:
        return 0.0
    n_periods = len(equity_curve) - 1
    n_years = n_periods / periods_per_year
    if n_years <= 0:
        return 0.0
    return float((end / start) ** (1.0 / n_years) - 1.0) * 100


def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """Sortino ratio — 하방 표준편차 기준."""
    if len(returns) < 2:
        return 0.0
    excess = returns - risk_free_rate / periods_per_year
    downside = excess[excess < 0]
    # 하방편차 = 목표(0) 기준 하방 수익률의 RMS (표본 std 아님 — 음수들의 평균을 빼면 안 됨)
    downside_dev = float(np.sqrt((downside ** 2).mean())) if len(downside) > 0 else 0.0
    if downside_dev == 0:
        return float("inf") if excess.mean() > 0 else 0.0
    return float(np.sqrt(periods_per_year) * excess.mean() / downside_dev)


def calculate_calmar_ratio(
    equity_curve: pd.Series,
    periods_per_year: int = 252,
) -> float:
    """Calmar ratio = CAGR / |MDD|."""
    cagr = calculate_cagr(equity_curve, periods_per_year)
    mdd = calculate_max_drawdown(equity_curve)
    if mdd == 0:
        return float("inf") if cagr > 0 else 0.0
    return float(cagr / abs(mdd))


def returns_from_equity(equity_curve: pd.Series) -> pd.Series:
    """자산가치 시계열 → 수익률 시계열 (pct_change)."""
    return equity_curve.pct_change().dropna()


def equity_from_returns(
    returns: pd.Series,
    initial_capital: float = 1.0,
) -> pd.Series:
    """수익률 시계열 → 자산가치 시계열 (복리 누적)."""
    return initial_capital * (1 + returns).cumprod()
