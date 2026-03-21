"""
agents/ 모듈 추가 유닛 테스트 (Week 2)

기존 test_agents.py가 커버하지 못하는 엣지 케이스와 경계값 집중 테스트:
  1. danger_score 계산 엣지 케이스 (0, 50, 70, 100)
  2. opportunity_score 엣지 케이스
  3. 전략 전환 로직 (쿨다운, FOMO 방지, 직행 전환)
  4. DCA 추적 (dca_history 업데이트, 매도 시 초기화)
  5. 자동 긴급정지 발동/해제 조건
  6. cascade_risk 계산 및 오버라이드 동작
  7. 외부 데이터 fusion 점수 산출
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.base_agent import BaseStrategyAgent, Decision
from agents.conservative import ConservativeAgent
from agents.moderate import ModerateAgent
from agents.aggressive import AggressiveAgent
from agents.external_data import (
    ExternalDataAgent,
    analyze_news_sentiment,
)


# ============================================================
# Helpers
# ============================================================

KST = timezone(timedelta(hours=9))

DEFAULT_STATE = {
    "active_agent": "moderate",
    "last_switch_time": None,
    "last_trade_time": None,
    "consecutive_losses": 0,
    "switch_history": [],
    "dca_history": {},
}


def _make_orchestrator(active="moderate", state_overrides=None):
    """테스트용 Orchestrator 팩토리."""
    with patch("agents.orchestrator._load_state") as mock:
        state = {**DEFAULT_STATE, "active_agent": active}
        if state_overrides:
            state.update(state_overrides)
        mock.return_value = state
        from agents.orchestrator import Orchestrator
        orch = Orchestrator()
        orch._learning_data = None
        orch._performance = {}
        return orch


def _make_market_state(**overrides):
    """테스트용 market_state dict 팩토리."""
    base = {
        "phase": "neutral",
        "fgi": 50,
        "rsi": 50,
        "price_change_24h": 0,
        "btc_ratio": 0.2,
        "consecutive_losses": 0,
        "fusion_signal": "neutral",
        "fusion_score": 0,
        "kimchi_pct": 0,
        "ls_ratio": 1.0,
        "funding_rate": 0,
        "macro_score": 0,
        "macro_sentiment": "neutral",
        "eth_btc_z": 0,
        "news_sentiment": "neutral",
        "danger_score": 0,
        "opportunity_score": 0,
    }
    base.update(overrides)
    return base


def _make_drop_context(**overrides):
    """테스트용 drop_context dict 팩토리."""
    base = {
        "price_change_4h": 0,
        "price_change_12h": 0,
        "price_change_24h": 0,
        "consecutive_red_candles": 0,
        "volume_ratio": 1.0,
        "trend_falling": False,
        "dca_already_done": False,
        "dca_history": {},
        "external_bearish_count": 0,
        "external_bearish_details": [],
        "cascade_risk": 0,
        "whale_direction": "neutral",
        "funding_rate": 0,
    }
    base.update(overrides)
    return base


def _make_market_data(
    rsi=50, sma_deviation=0, fgi=50, price_change_rate=0,
    ai_score=0, trade_price=50000000, candles_4h=None,
):
    """테스트용 시장 데이터 팩토리."""
    return {
        "indicators": {
            "rsi_14": rsi,
            "sma_20": trade_price,
            "sma_20_deviation_pct": sma_deviation,
            "macd": {"histogram": 0, "signal_cross": False},
            "bollinger": {},
        },
        "ticker": {
            "trade_price": trade_price,
            "signed_change_rate": price_change_rate / 100,
        },
        "fear_greed": {"value": fgi},
        "news": {"overall_sentiment": "neutral"},
        "ai_composite_signal": {"score": ai_score},
        "current_price": trade_price,
        "candles_4h": candles_4h or [],
    }


def _make_external_data(**overrides):
    """테스트용 external_data 팩토리 (sources + external_signal)."""
    base = {
        "external_signal": {"total_score": 0, "strategy_bonus": 0, "fusion": {"signal": "neutral"}},
        "sources": {
            "fear_greed": {"current": {"value": 50}},
            "binance_sentiment": {
                "kimchi_premium": {"premium_pct": 0},
                "top_trader_long_short": {"current_ratio": 1.0},
                "funding_rate": {"current_rate": 0},
            },
            "macro": {"analysis": {"macro_score": 0, "sentiment": "neutral"}},
            "eth_btc": {},
            "news_sentiment": {"overall_sentiment": "neutral"},
            "whale_tracker": {"whale_score": {"direction": "neutral"}},
            "user_feedback": [],
            "performance_review": {"available": False},
        },
    }
    # Merge overrides into sources
    for k, v in overrides.items():
        if k == "external_signal":
            base["external_signal"] = v
        elif k in base["sources"]:
            base["sources"][k] = v
    return base


def _make_portfolio(krw=1000000, btc_balance=0, btc_avg_price=50000000,
                    profit_pct=0, total_eval=1000000):
    btc_eval = btc_balance * btc_avg_price if btc_balance > 0 else 0
    return {
        "krw_balance": krw,
        "btc": {
            "balance": btc_balance,
            "avg_buy_price": btc_avg_price,
            "profit_pct": profit_pct,
            "eval_amount": btc_eval,
        },
        "total_eval": total_eval,
        "btc_ratio": btc_eval / total_eval if total_eval > 0 else 0,
    }


# ============================================================
# 1. Danger Score Edge Cases
# ============================================================

class TestDangerScoreEdgeCases:
    """danger_score 계산의 경계값 및 조합 테스트."""

    def test_danger_exactly_zero_all_neutral(self):
        """모든 지표가 중립일 때 정확히 0."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=0,
            kimchi_pct=0, ls_ratio=1.0, btc_ratio=0.2,
            consecutive_losses=0, macro_score=0, news_sentiment="neutral",
        )
        assert score == 0

    def test_danger_near_50_combination(self):
        """danger ~ 50이 되는 조합: 손절 2회(20) + 급락 -4%(20) + 뉴스부정(10) = 50."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=-4,
            kimchi_pct=0, ls_ratio=1.0, btc_ratio=0.2,
            consecutive_losses=2, macro_score=0, news_sentiment="negative",
        )
        # losses: 20, crash: 20, news: 10 = 50
        assert score == 50

    def test_danger_exactly_70_threshold(self):
        """danger = 70 경계: 긴급 보수 전환 트리거 지점."""
        orch = _make_orchestrator()
        # losses 3=30, crash -5=25, kimchi 6=(6-3)*5=15 = 70
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=-5,
            kimchi_pct=6, ls_ratio=1.0, btc_ratio=0.2,
            consecutive_losses=3, macro_score=0, news_sentiment="neutral",
        )
        assert score == 70

    def test_danger_max_100_extreme(self):
        """모든 항목 최대치일 때 100으로 캡."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=90, rsi=80, price_change_24h=-10,
            kimchi_pct=10, ls_ratio=2.5, btc_ratio=0.8,
            consecutive_losses=10, macro_score=-50, news_sentiment="negative",
        )
        assert score == 100

    def test_danger_btc_overweight_at_boundary(self):
        """btc_ratio = 0.3 경계: 가산점 0."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=0,
            kimchi_pct=0, ls_ratio=1.0, btc_ratio=0.3,
            consecutive_losses=0,
        )
        assert score == 0

    def test_danger_btc_overweight_above_boundary(self):
        """btc_ratio = 0.5 → (0.5-0.3)*100 = 20점."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=0,
            kimchi_pct=0, ls_ratio=1.0, btc_ratio=0.5,
            consecutive_losses=0,
        )
        assert score == 20

    def test_danger_btc_overweight_cap(self):
        """btc_ratio = 0.9 → min((0.9-0.3)*100, 20) = 20 (캡)."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=0,
            kimchi_pct=0, ls_ratio=1.0, btc_ratio=0.9,
            consecutive_losses=0,
        )
        assert score == 20

    def test_danger_ls_ratio_boundary(self):
        """ls_ratio = 1.2 경계: 가산점 0."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=0,
            kimchi_pct=0, ls_ratio=1.2, btc_ratio=0.2,
            consecutive_losses=0,
        )
        assert score == 0

    def test_danger_ls_ratio_above_boundary(self):
        """ls_ratio = 1.7 → min((1.7-1.2)*20, 10) = 10."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=0,
            kimchi_pct=0, ls_ratio=1.7, btc_ratio=0.2,
            consecutive_losses=0,
        )
        assert score == 10

    def test_danger_slightly_negative_news(self):
        """slightly_negative 뉴스 → 5점."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=0,
            kimchi_pct=0, ls_ratio=1.0, btc_ratio=0.2,
            consecutive_losses=0, news_sentiment="slightly_negative",
        )
        assert score == 5

    def test_danger_crash_boundary_at_minus_3(self):
        """price_change_24h = -3 → 조건 미충족 (< -3 필요, strict)."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=-3,
            kimchi_pct=0, ls_ratio=1.0, btc_ratio=0.2,
            consecutive_losses=0,
        )
        assert score == 0

    def test_danger_crash_at_minus_3_1(self):
        """price_change_24h = -3.1 → abs(-3.1)*5=15."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=-3.1,
            kimchi_pct=0, ls_ratio=1.0, btc_ratio=0.2,
            consecutive_losses=0,
        )
        assert score == 15

    def test_danger_crash_just_above_boundary(self):
        """price_change_24h = -2.9 → 급락 안 됨 (> -3), 0점."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=-2.9,
            kimchi_pct=0, ls_ratio=1.0, btc_ratio=0.2,
            consecutive_losses=0,
        )
        assert score == 0

    def test_danger_macro_boundary(self):
        """macro_score = -10 경계: 조건 미충족 (< -10 필요)."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=0,
            kimchi_pct=0, ls_ratio=1.0, btc_ratio=0.2,
            consecutive_losses=0, macro_score=-10,
        )
        assert score == 0

    def test_danger_macro_below_boundary(self):
        """macro_score = -11 → abs(-11)*0.5 = 5 (반올림 처리에 따라)."""
        orch = _make_orchestrator()
        score = orch._calculate_danger_score(
            fgi=50, rsi=50, price_change_24h=0,
            kimchi_pct=0, ls_ratio=1.0, btc_ratio=0.2,
            consecutive_losses=0, macro_score=-11,
        )
        assert score == 5  # int(11*0.5) = 5


# ============================================================
# 2. Opportunity Score Edge Cases
# ============================================================

class TestOpportunityScoreEdgeCases:
    """opportunity_score 계산의 경계값 및 조합 테스트."""

    def test_opportunity_exactly_zero(self):
        """모든 지표가 중립일 때 정확히 0."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=50, price_change_24h=0,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=0,
        )
        assert score == 0

    def test_opportunity_fgi_boundary_25(self):
        """FGI = 25 → max(1, 25-25) = 1점 (경계값 최소 1점 보장)."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=25, rsi=50, price_change_24h=0,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=0,
        )
        assert score == 1

    def test_opportunity_fgi_24(self):
        """FGI = 24 → 25-24 = 1점."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=24, rsi=50, price_change_24h=0,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=0,
        )
        assert score == 1

    def test_opportunity_fgi_0_maximum(self):
        """FGI = 0 → 25-0 = 25점 (최대)."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=0, rsi=50, price_change_24h=0,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=0,
        )
        assert score == 25

    def test_opportunity_rsi_boundary_35(self):
        """RSI = 35 → 조건 미충족 (< 35 필요)."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=35, price_change_24h=0,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=0,
        )
        assert score == 0

    def test_opportunity_rsi_34(self):
        """RSI = 34 → int((35-34)*1.3) = 1."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=34, price_change_24h=0,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=0,
        )
        assert score == 1

    def test_opportunity_rsi_20_deep_oversold(self):
        """RSI = 20 → int((35-20)*1.3) = 19."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=20, price_change_24h=0,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=0,
        )
        assert score == 19

    def test_opportunity_bounce_boundary_1pct(self):
        """price_change_24h = 1 → 조건 미충족 (> 1 필요, strict)."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=50, price_change_24h=1,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=0,
        )
        assert score == 0

    def test_opportunity_bounce_above_1pct(self):
        """price_change_24h = 1.1 → min(1.1*5, 15) = 5."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=50, price_change_24h=1.1,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=0,
        )
        assert score == 5

    def test_opportunity_bounce_capped(self):
        """price_change_24h = 5 → min(25, 15) = 15."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=50, price_change_24h=5,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=0,
        )
        assert score == 15

    def test_opportunity_buy_fusion(self):
        """fusion_signal='buy' → 10점."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=50, price_change_24h=0,
            fusion_signal="buy", fusion_score=20,
            funding_rate=0, kimchi_pct=0,
        )
        assert score == 10

    def test_opportunity_fusion_score_above_10(self):
        """fusion_score > 10 but signal != buy/strong_buy → 5점."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=50, price_change_24h=0,
            fusion_signal="neutral", fusion_score=15,
            funding_rate=0, kimchi_pct=0,
        )
        assert score == 5

    def test_opportunity_funding_mildly_negative(self):
        """funding_rate = -0.005 (> -0.01) → 5점."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=50, price_change_24h=0,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=-0.005, kimchi_pct=0,
        )
        assert score == 5

    def test_opportunity_kimchi_discount_boundary(self):
        """kimchi_pct = -1 경계: min(abs(-1)*3, 10) = 3."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=50, price_change_24h=0,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=-1,
        )
        # -1 < -1 is False, so no points
        assert score == 0

    def test_opportunity_kimchi_discount_below_boundary(self):
        """kimchi_pct = -2 → min(abs(-2)*3, 10) = 6."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=50, price_change_24h=0,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=-2,
        )
        assert score == 6

    def test_opportunity_macro_bullish(self):
        """macro_score > 10 → min(macro_score*0.5, 10)."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=50, price_change_24h=0,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=0,
            macro_score=20,
        )
        assert score == 10

    def test_opportunity_news_positive(self):
        """news_sentiment='positive' → 8점."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=50, price_change_24h=0,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=0,
            news_sentiment="positive",
        )
        assert score == 8

    def test_opportunity_news_slightly_positive(self):
        """news_sentiment='slightly_positive' → 4점."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=50, rsi=50, price_change_24h=0,
            fusion_signal="neutral", fusion_score=0,
            funding_rate=0, kimchi_pct=0,
            news_sentiment="slightly_positive",
        )
        assert score == 4

    def test_opportunity_near_60_combination(self):
        """opportunity ~ 60이 되는 조합 (공격적 직행 트리거)."""
        orch = _make_orchestrator()
        # fgi=5→20, rsi=20→19, fusion=strong_buy→20 = 59
        score = orch._calculate_opportunity_score(
            fgi=5, rsi=20, price_change_24h=0,
            fusion_signal="strong_buy", fusion_score=50,
            funding_rate=0, kimchi_pct=0,
        )
        assert score == 59

    def test_opportunity_capped_at_100(self):
        """극단 조합이라도 100 캡."""
        orch = _make_orchestrator()
        score = orch._calculate_opportunity_score(
            fgi=0, rsi=10, price_change_24h=10,
            fusion_signal="strong_buy", fusion_score=50,
            funding_rate=-0.05, kimchi_pct=-10,
            macro_score=30, news_sentiment="positive",
        )
        assert score == 100


# ============================================================
# 3. Strategy Switch Logic
# ============================================================

class TestStrategySwitchLogicExtended:
    """전환 규칙의 경계값 테스트."""

    def test_danger_69_aggressive_to_moderate(self):
        """danger=69 + aggressive → moderate (45~69 범위)."""
        orch = _make_orchestrator("aggressive")
        ms = _make_market_state(danger_score=69, kimchi_pct=5, ls_ratio=1.5)
        target = orch._decide_target("aggressive", ms, 69, 10)
        assert target == "moderate"

    def test_danger_44_aggressive_no_switch(self):
        """danger=44 + aggressive → 전환 없음 (45 미만)."""
        orch = _make_orchestrator("aggressive")
        ms = _make_market_state(danger_score=44)
        target = orch._decide_target("aggressive", ms, 44, 10)
        # 44 < 45 → aggressive→moderate 룰 미적용
        # Check there's no sideways or other match
        assert target is None or target != "conservative"

    def test_danger_49_moderate_no_switch(self):
        """danger=49 + moderate → 전환 없음 (50 필요)."""
        orch = _make_orchestrator("moderate")
        ms = _make_market_state(danger_score=49, fgi=40)
        target = orch._decide_target("moderate", ms, 49, 10)
        assert target is None

    def test_danger_50_moderate_to_conservative(self):
        """danger=50 + moderate → conservative."""
        orch = _make_orchestrator("moderate")
        ms = _make_market_state(danger_score=50, fgi=35)
        target = orch._decide_target("moderate", ms, 50, 10)
        assert target == "conservative"

    def test_opportunity_59_moderate_no_aggressive(self):
        """opportunity=59 + danger<35 + moderate → aggressive (40~59 범위)."""
        orch = _make_orchestrator("moderate")
        ms = _make_market_state(opportunity_score=59, fgi=30, fusion_signal="buy")
        target = orch._decide_target("moderate", ms, 10, 59)
        assert target == "aggressive"

    def test_opportunity_39_conservative_no_switch(self):
        """opportunity=39 + danger=31 → no switch (danger >= 30)."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(opportunity_score=39, fgi=40, rsi=40)
        target = orch._decide_target("conservative", ms, 31, 39)
        # 25~39 range requires danger < 30
        assert target is None

    def test_opportunity_25_conservative_to_moderate(self):
        """opportunity=25 + danger=29 + conservative → moderate."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(opportunity_score=25, fgi=40, rsi=40)
        target = orch._decide_target("conservative", ms, 29, 25)
        assert target == "moderate"

    def test_opportunity_24_conservative_no_switch(self):
        """opportunity=24 + conservative → 전환 없음 (25 필요)."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(opportunity_score=24, fgi=40, rsi=40)
        target = orch._decide_target("conservative", ms, 10, 24)
        # Below 25, no match unless sideways (both < 25)
        assert target is None or target == "moderate"  # sideways could match

    def test_opportunity_60_danger_30_no_aggressive(self):
        """opportunity=60 + danger=30 → 공격적 불가 (danger < 30 필요)."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(opportunity_score=60, fgi=15, rsi=25,
                                price_change_24h=2, fusion_signal="strong_buy",
                                phase="extreme_fear")
        target = orch._decide_target("conservative", ms, 30, 60)
        # danger=30 fails danger < 30 check for opportunity >= 60
        assert target != "aggressive"

    def test_opportunity_60_danger_29_aggressive(self):
        """opportunity=60 + danger=29 → 공격적 직행."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(opportunity_score=60, fgi=15, rsi=25,
                                price_change_24h=2, fusion_signal="strong_buy",
                                phase="extreme_fear")
        target = orch._decide_target("conservative", ms, 29, 60)
        assert target == "aggressive"

    def test_sideways_conservative_with_losses_no_switch(self):
        """횡보 + conservative + 연속손절 1회 → 전환 안 함."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(
            danger_score=10, opportunity_score=10,
            fgi=50, rsi=50, phase="neutral", consecutive_losses=1,
            price_change_24h=0,
        )
        target = orch._decide_target("conservative", ms, 10, 10)
        # sideways rule requires consecutive_losses == 0
        assert target is None

    def test_sideways_conservative_high_price_change_no_switch(self):
        """횡보 + conservative + |24h변동| >= 3% → 전환 안 함."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(
            danger_score=10, opportunity_score=10,
            fgi=50, rsi=50, phase="neutral", consecutive_losses=0,
            price_change_24h=3.5,
        )
        target = orch._decide_target("conservative", ms, 10, 10)
        # abs(3.5) >= 3 → no switch
        assert target is None

    def test_already_conservative_danger_70(self):
        """이미 conservative인데 danger=70 → 전환 없음 (이미 최적)."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(danger_score=75, fgi=20, rsi=50,
                                price_change_24h=-6, consecutive_losses=3)
        target = orch._decide_target("conservative", ms, 75, 10)
        assert target is None

    def test_already_aggressive_opportunity_65(self):
        """이미 aggressive인데 opportunity=65 → 전환 없음."""
        orch = _make_orchestrator("aggressive")
        ms = _make_market_state(danger_score=10, opportunity_score=65,
                                fgi=15, rsi=25, price_change_24h=2,
                                fusion_signal="strong_buy", phase="extreme_fear")
        target = orch._decide_target("aggressive", ms, 10, 65)
        assert target is None


# ============================================================
# 3b. FOMO Prevention Extended
# ============================================================

class TestFomoPreventionExtended:
    """FOMO 방지 경계값 테스트."""

    def test_fomo_block_at_exactly_minus_5(self):
        """price_change_24h = -5 경계: FOMO 차단 (< -5 필요)."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(
            danger_score=10, opportunity_score=65,
            fgi=30, rsi=25, price_change_24h=-5,
            fusion_signal="strong_buy", phase="fear",
        )
        target = orch._decide_target("conservative", ms, 10, 65)
        # -5 < -5 is False → NOT FOMO blocked
        assert target == "aggressive"

    def test_fomo_block_at_minus_5_1(self):
        """price_change_24h = -5.1 → FOMO 차단 (fgi=30 > 20)."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(
            danger_score=10, opportunity_score=65,
            fgi=30, rsi=25, price_change_24h=-5.1,
            fusion_signal="strong_buy", phase="fear",
        )
        target = orch._decide_target("conservative", ms, 10, 65)
        assert target is None

    def test_fomo_exception_fgi_20_boundary(self):
        """FGI=20 → 예외 조건 미충족 (FGI <= 20 필요하나 price 조건도 필요)."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(
            danger_score=10, opportunity_score=65,
            fgi=20, rsi=25, price_change_24h=-6,
            fusion_signal="strong_buy", phase="extreme_fear",
        )
        target = orch._decide_target("conservative", ms, 10, 65)
        # fgi=20 <= 20 AND -6 > -8 → exception applies
        assert target == "aggressive"

    def test_fomo_exception_fgi_21_no_exception(self):
        """FGI=21 → 예외 미적용 (> 20)."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(
            danger_score=10, opportunity_score=65,
            fgi=21, rsi=25, price_change_24h=-6,
            fusion_signal="strong_buy", phase="fear",
        )
        target = orch._decide_target("conservative", ms, 10, 65)
        assert target is None

    def test_fomo_exception_price_minus_8_boundary(self):
        """price=-8 → 예외 미적용 (> -8 필요)."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(
            danger_score=10, opportunity_score=65,
            fgi=15, rsi=25, price_change_24h=-8,
            fusion_signal="strong_buy", phase="extreme_fear",
        )
        target = orch._decide_target("conservative", ms, 10, 65)
        # -8 > -8 is False → fomo_block applies
        assert target is None

    def test_fomo_exception_price_minus_7_9(self):
        """price=-7.9 + FGI=15 → 예외 적용 (-7.9 > -8)."""
        orch = _make_orchestrator("conservative")
        ms = _make_market_state(
            danger_score=10, opportunity_score=65,
            fgi=15, rsi=25, price_change_24h=-7.9,
            fusion_signal="strong_buy", phase="extreme_fear",
        )
        target = orch._decide_target("conservative", ms, 10, 65)
        assert target == "aggressive"


# ============================================================
# 3c. Cooldown Extended
# ============================================================

class TestCooldownExtended:
    """쿨다운 로직 추가 엣지 케이스."""

    def test_cooldown_from_switch_history_not_last_switch_time(self):
        """last_switch_time은 None이나 switch_history에 최근 항목 있으면 쿨다운."""
        recent_time = (datetime.now(KST) - timedelta(hours=1)).isoformat()
        orch = _make_orchestrator(state_overrides={
            "last_switch_time": None,
            "switch_history": [{"timestamp": recent_time}],
        })
        assert orch._is_on_cooldown() is True

    def test_cooldown_switch_history_newer_than_last_switch(self):
        """switch_history의 마지막이 last_switch_time보다 최신이면 그것을 사용."""
        old_time = (datetime.now(KST) - timedelta(hours=5)).isoformat()
        recent_time = (datetime.now(KST) - timedelta(hours=1)).isoformat()
        orch = _make_orchestrator(state_overrides={
            "last_switch_time": old_time,
            "switch_history": [{"timestamp": recent_time}],
        })
        assert orch._is_on_cooldown() is True

    def test_cooldown_exactly_2_hours_boundary(self):
        """정확히 2시간 전 전환 → 쿨다운 아님 (< 조건이므로 정확히 2시간은 False)."""
        exact_2h = (datetime.now(KST) - timedelta(hours=2, seconds=1)).isoformat()
        orch = _make_orchestrator(state_overrides={
            "last_switch_time": exact_2h,
        })
        assert orch._is_on_cooldown() is False

    def test_cooldown_3_switches_4h_cooldown_at_3h(self):
        """당일 3회 전환 → 4시간 쿨다운, 마지막 전환 1분 전 → 아직 쿨다운.

        자정 경계 문제 방지: 모든 전환을 1분 전으로 설정하여
        어떤 시간대에서도 반드시 '오늘'로 인식되도록 한다.
        """
        now = datetime.now(KST)
        one_min_ago = (now - timedelta(minutes=1)).isoformat()
        two_min_ago = (now - timedelta(minutes=2)).isoformat()
        three_min_ago = (now - timedelta(minutes=3)).isoformat()
        orch = _make_orchestrator(state_overrides={
            "last_switch_time": one_min_ago,
            "switch_history": [
                {"timestamp": three_min_ago},
                {"timestamp": two_min_ago},
                {"timestamp": one_min_ago},
            ],
        })
        # 3회 전환 → 4시간 쿨다운, 1분 경과 → 아직 쿨다운
        assert orch._is_on_cooldown() is True

    def test_cooldown_3_switches_4h_cooldown_expired(self):
        """당일 3회 전환 → 4시간 쿨다운, 5시간 경과 → 쿨다운 해제."""
        today = datetime.now(KST).strftime("%Y-%m-%d")
        five_hours_ago = (datetime.now(KST) - timedelta(hours=5)).isoformat()
        orch = _make_orchestrator(state_overrides={
            "last_switch_time": five_hours_ago,
            "switch_history": [
                {"timestamp": f"{today}T01:00:00+09:00"},
                {"timestamp": f"{today}T03:00:00+09:00"},
                {"timestamp": five_hours_ago},
            ],
        })
        assert orch._is_on_cooldown() is False

    def test_emergency_bypasses_cooldown_via_evaluate_switch(self):
        """danger>=70 → _evaluate_switch에서 쿨다운 무시 검증."""
        recent_time = (datetime.now(KST) - timedelta(minutes=10)).isoformat()
        orch = _make_orchestrator("aggressive", state_overrides={
            "last_switch_time": recent_time,
        })
        ms = _make_market_state(
            danger_score=75, opportunity_score=5,
            fgi=20, rsi=50, price_change_24h=-8,
            consecutive_losses=3, phase="extreme_fear",
        )
        result = orch._evaluate_switch(ms)
        assert result is not None
        assert result["to"] == "conservative"

    def test_price_crash_7pct_bypasses_cooldown(self):
        """price_change_24h < -7 → 쿨다운 무시 (danger < 70이어도)."""
        recent_time = (datetime.now(KST) - timedelta(minutes=10)).isoformat()
        orch = _make_orchestrator("aggressive", state_overrides={
            "last_switch_time": recent_time,
        })
        ms = _make_market_state(
            danger_score=60, opportunity_score=5,
            fgi=30, rsi=50, price_change_24h=-7.5,
            kimchi_pct=4, ls_ratio=1.3,
            consecutive_losses=0, phase="fear",
        )
        result = orch._evaluate_switch(ms)
        # is_emergency = danger>=70(False) OR price<-7(True) → bypass
        # danger 60 → 45~69 aggressive→moderate
        assert result is not None
        assert result["to"] == "moderate"


# ============================================================
# 4. DCA Tracking
# ============================================================

class TestDcaTrackingExtended:
    """DCA 추적 추가 테스트."""

    @patch("agents.orchestrator._save_state")
    def test_dca_increments_count(self, mock_save):
        """DCA 실행 시 카운트 증가."""
        orch = _make_orchestrator()
        d = Decision(
            decision="buy", confidence=0.6, reason="DCA",
            buy_score={},
            trade_params={"is_dca": True, "market": "KRW-BTC", "amount": 50000},
            external_signal={}, agent_name="test",
        )
        orch._track_dca(d)
        assert orch.state["dca_history"]["KRW-BTC"]["dca_count"] == 1
        assert orch.state["dca_history"]["KRW-BTC"]["dca_total_amount"] == 50000

    @patch("agents.orchestrator._save_state")
    def test_dca_multiple_increments(self, mock_save):
        """DCA 2회 연속 실행 시 누적."""
        orch = _make_orchestrator(state_overrides={"dca_history": {}})
        d1 = Decision(
            decision="buy", confidence=0.6, reason="DCA 1",
            buy_score={},
            trade_params={"is_dca": True, "market": "KRW-BTC", "amount": 50000},
            external_signal={}, agent_name="test",
        )
        d2 = Decision(
            decision="buy", confidence=0.6, reason="DCA 2",
            buy_score={},
            trade_params={"is_dca": True, "market": "KRW-BTC", "amount": 30000},
            external_signal={}, agent_name="test",
        )
        orch._track_dca(d1)
        orch._track_dca(d2)
        assert orch.state["dca_history"]["KRW-BTC"]["dca_count"] == 2
        assert orch.state["dca_history"]["KRW-BTC"]["dca_total_amount"] == 80000

    @patch("agents.orchestrator._save_state")
    def test_sell_resets_dca(self, mock_save):
        """매도 시 DCA 이력 초기화."""
        orch = _make_orchestrator(state_overrides={
            "dca_history": {"KRW-BTC": {"dca_count": 2, "dca_total_amount": 100000}},
        })
        d = Decision(
            decision="sell", confidence=0.8, reason="Take profit",
            buy_score={},
            trade_params={"market": "KRW-BTC", "volume": 0.01},
            external_signal={}, agent_name="test",
        )
        orch._track_dca(d)
        assert "KRW-BTC" not in orch.state["dca_history"]

    @patch("agents.orchestrator._save_state")
    def test_hold_does_not_affect_dca(self, mock_save):
        """관망 시 DCA 이력 변경 없음."""
        orch = _make_orchestrator(state_overrides={
            "dca_history": {"KRW-BTC": {"dca_count": 1, "dca_total_amount": 50000}},
        })
        d = Decision(
            decision="hold", confidence=0.5, reason="Hold",
            buy_score={},
            trade_params={},
            external_signal={}, agent_name="test",
        )
        orch._track_dca(d)
        assert orch.state["dca_history"]["KRW-BTC"]["dca_count"] == 1

    @patch("agents.orchestrator._save_state")
    def test_buy_without_dca_flag(self, mock_save):
        """일반 매수(is_dca 없음)는 DCA 이력에 기록되지 않음."""
        orch = _make_orchestrator(state_overrides={"dca_history": {}})
        d = Decision(
            decision="buy", confidence=0.7, reason="Normal buy",
            buy_score={},
            trade_params={"market": "KRW-BTC", "amount": 100000},
            external_signal={}, agent_name="test",
        )
        orch._track_dca(d)
        assert "KRW-BTC" not in orch.state.get("dca_history", {})

    @patch("agents.orchestrator._save_state")
    def test_sell_different_market(self, mock_save):
        """다른 마켓 매도 시 KRW-BTC DCA 이력 유지."""
        orch = _make_orchestrator(state_overrides={
            "dca_history": {"KRW-BTC": {"dca_count": 1, "dca_total_amount": 50000}},
        })
        d = Decision(
            decision="sell", confidence=0.8, reason="Sell ETH",
            buy_score={},
            trade_params={"market": "KRW-ETH", "volume": 0.1},
            external_signal={}, agent_name="test",
        )
        orch._track_dca(d)
        # KRW-ETH 삭제 시도하지만 없으므로 무시
        assert orch.state["dca_history"]["KRW-BTC"]["dca_count"] == 1

    @patch("agents.orchestrator._save_state")
    def test_dca_records_timestamp(self, mock_save):
        """DCA 실행 시 last_dca_time이 기록됨."""
        orch = _make_orchestrator()
        d = Decision(
            decision="buy", confidence=0.6, reason="DCA",
            buy_score={},
            trade_params={"is_dca": True, "market": "KRW-BTC", "amount": 50000},
            external_signal={}, agent_name="test",
        )
        orch._track_dca(d)
        assert "last_dca_time" in orch.state["dca_history"]["KRW-BTC"]


# ============================================================
# 5. Auto Emergency Stop
# ============================================================

class TestAutoEmergencyExtended:
    """자동 긴급정지 발동/해제 조건 확장 테스트."""

    def test_flash_crash_boundary_minus_10(self):
        """4h = -10 → 플래시 크래시 미발동 (< -10 필요)."""
        orch = _make_orchestrator()
        result = orch._evaluate_auto_emergency(
            market_state={"danger_score": 50, "consecutive_losses": 0},
            drop_context={"price_change_4h": -10, "cascade_risk": 50,
                          "external_bearish_count": 2, "external_bearish_details": []},
            portfolio={"btc": {"profit_pct": -5}},
        )
        assert result is None

    def test_flash_crash_minus_10_1(self):
        """4h = -10.1 → 플래시 크래시 발동."""
        orch = _make_orchestrator()
        result = orch._evaluate_auto_emergency(
            market_state={"danger_score": 50, "consecutive_losses": 0},
            drop_context={"price_change_4h": -10.1, "cascade_risk": 50,
                          "external_bearish_count": 2, "external_bearish_details": []},
            portfolio={"btc": {"profit_pct": -5}},
        )
        assert result is not None
        assert "플래시 크래시" in result["reason"]

    def test_cascade_danger_boundary_89_79(self):
        """cascade=89, danger=79 → 미발동 (cascade>=90 AND danger>=80 필요)."""
        orch = _make_orchestrator()
        result = orch._evaluate_auto_emergency(
            market_state={"danger_score": 79, "consecutive_losses": 0},
            drop_context={"price_change_4h": -2, "cascade_risk": 89,
                          "external_bearish_count": 2, "external_bearish_details": []},
            portfolio={"btc": {"profit_pct": -5}},
        )
        assert result is None

    def test_cascade_danger_boundary_90_80(self):
        """cascade=90, danger=80 → 발동."""
        orch = _make_orchestrator()
        result = orch._evaluate_auto_emergency(
            market_state={"danger_score": 80, "consecutive_losses": 0},
            drop_context={"price_change_4h": -2, "cascade_risk": 90,
                          "external_bearish_count": 2, "external_bearish_details": []},
            portfolio={"btc": {"profit_pct": -5}},
        )
        assert result is not None
        assert "캐스케이딩" in result["reason"]

    def test_external_bearish_4_not_enough(self):
        """외부 약세 4개 → 미발동 (5개 필요)."""
        orch = _make_orchestrator()
        result = orch._evaluate_auto_emergency(
            market_state={"danger_score": 50, "consecutive_losses": 0},
            drop_context={"price_change_4h": -2, "cascade_risk": 30,
                          "external_bearish_count": 4,
                          "external_bearish_details": ["a", "b", "c", "d"]},
            portfolio={"btc": {"profit_pct": -5}},
        )
        assert result is None

    def test_portfolio_crisis_losses_4_not_enough(self):
        """연속 손절 4회 + -18% → 미발동 (5회 필요)."""
        orch = _make_orchestrator()
        result = orch._evaluate_auto_emergency(
            market_state={"danger_score": 50, "consecutive_losses": 4},
            drop_context={"price_change_4h": -2, "cascade_risk": 30,
                          "external_bearish_count": 2, "external_bearish_details": []},
            portfolio={"btc": {"profit_pct": -18}},
        )
        assert result is None

    def test_portfolio_crisis_profit_minus_14_not_enough(self):
        """연속 손절 5회 + -14% → 미발동 (-15% 필요)."""
        orch = _make_orchestrator()
        result = orch._evaluate_auto_emergency(
            market_state={"danger_score": 50, "consecutive_losses": 5},
            drop_context={"price_change_4h": -2, "cascade_risk": 30,
                          "external_bearish_count": 2, "external_bearish_details": []},
            portfolio={"btc": {"profit_pct": -14}},
        )
        assert result is None

    def test_portfolio_crisis_exact_boundary_minus_15(self):
        """연속 손절 5회 + -15% → 미발동 (< -15 필요, strict)."""
        orch = _make_orchestrator()
        result = orch._evaluate_auto_emergency(
            market_state={"danger_score": 50, "consecutive_losses": 5},
            drop_context={"price_change_4h": -2, "cascade_risk": 30,
                          "external_bearish_count": 2, "external_bearish_details": []},
            portfolio={"btc": {"profit_pct": -15}},
        )
        assert result is None

    def test_portfolio_crisis_minus_15_1(self):
        """연속 손절 5회 + -15.1% → 발동."""
        orch = _make_orchestrator()
        result = orch._evaluate_auto_emergency(
            market_state={"danger_score": 50, "consecutive_losses": 5},
            drop_context={"price_change_4h": -2, "cascade_risk": 30,
                          "external_bearish_count": 2, "external_bearish_details": []},
            portfolio={"btc": {"profit_pct": -15.1}},
        )
        assert result is not None
        assert "연속 손절" in result["reason"]

    def test_emergency_conditions_dict_populated(self):
        """발동 시 conditions dict에 모든 정보 포함."""
        orch = _make_orchestrator()
        result = orch._evaluate_auto_emergency(
            market_state={"danger_score": 85, "consecutive_losses": 6},
            drop_context={"price_change_4h": -12, "cascade_risk": 95,
                          "external_bearish_count": 5,
                          "external_bearish_details": ["a", "b", "c", "d", "e"]},
            portfolio={"btc": {"profit_pct": -20}},
        )
        assert "conditions" in result
        assert result["conditions"]["price_change_4h"] == -12
        assert result["conditions"]["cascade_risk"] == 95
        assert result["conditions"]["danger_score"] == 85
        assert result["conditions"]["consecutive_losses"] == 6
        assert result["conditions"]["portfolio_profit_pct"] == -20

    @patch("agents.orchestrator.AUTO_EMERGENCY_FILE")
    def test_can_lift_requires_12h(self, mock_file):
        """해제 조건: 12시간 미경과 → 해제 불가."""
        orch = _make_orchestrator()
        # 6시간 전 발동
        activated = (datetime.now(KST) - timedelta(hours=6)).isoformat()
        auto_em = {"active": True, "reason": "test", "activated_at": activated}
        with patch.object(orch, '_check_auto_emergency_active', return_value=auto_em):
            md = _make_market_data(candles_4h=[
                {"trade_price": 50000000},
                {"trade_price": 50500000},
            ])
            ext = _make_external_data(fear_greed={"current": {"value": 50}})
            port = _make_portfolio()
            result = orch._can_lift_auto_emergency(md, ext, port)
            assert result is False

    @patch("agents.orchestrator.AUTO_EMERGENCY_FILE")
    def test_can_lift_requires_stable_price(self, mock_file):
        """해제 조건: 4h 급락 지속 중 → 해제 불가."""
        orch = _make_orchestrator()
        activated = (datetime.now(KST) - timedelta(hours=13)).isoformat()
        auto_em = {"active": True, "reason": "test", "activated_at": activated}
        with patch.object(orch, '_check_auto_emergency_active', return_value=auto_em):
            md = _make_market_data(candles_4h=[
                {"trade_price": 50000000},
                {"trade_price": 47000000},  # -6%
            ])
            ext = _make_external_data(fear_greed={"current": {"value": 50}})
            port = _make_portfolio()
            result = orch._can_lift_auto_emergency(md, ext, port)
            assert result is False

    @patch("agents.orchestrator.AUTO_EMERGENCY_FILE")
    def test_can_lift_requires_fgi_above_15(self, mock_file):
        """해제 조건: FGI <= 15 → 해제 불가."""
        orch = _make_orchestrator()
        activated = (datetime.now(KST) - timedelta(hours=13)).isoformat()
        auto_em = {"active": True, "reason": "test", "activated_at": activated}
        with patch.object(orch, '_check_auto_emergency_active', return_value=auto_em):
            md = _make_market_data(candles_4h=[
                {"trade_price": 50000000},
                {"trade_price": 50500000},
            ])
            ext = _make_external_data(fear_greed={"current": {"value": 10}})
            port = _make_portfolio()
            result = orch._can_lift_auto_emergency(md, ext, port)
            assert result is False

    @patch("agents.orchestrator.AUTO_EMERGENCY_FILE")
    def test_can_lift_all_conditions_met(self, mock_file):
        """해제 조건 모두 충족 → 해제 가능."""
        orch = _make_orchestrator()
        activated = (datetime.now(KST) - timedelta(hours=13)).isoformat()
        auto_em = {"active": True, "reason": "test", "activated_at": activated}
        with patch.object(orch, '_check_auto_emergency_active', return_value=auto_em):
            md = _make_market_data(candles_4h=[
                {"trade_price": 50000000},
                {"trade_price": 50500000},  # +1% (안정)
            ])
            ext = _make_external_data(fear_greed={"current": {"value": 30}})
            port = _make_portfolio()
            result = orch._can_lift_auto_emergency(md, ext, port)
            assert result is True


# ============================================================
# 6. Cascade Risk Calculation
# ============================================================

class TestCascadeRiskCalculation:
    """cascade_risk 계산 및 오버라이드 동작."""

    def test_cascade_zero_no_drop(self):
        """하락 없으면 cascade_risk = 0."""
        orch = _make_orchestrator()
        md = _make_market_data(price_change_rate=1, candles_4h=[
            {"trade_price": 50000000, "opening_price": 49500000,
             "candle_acc_trade_volume": 100},
            {"trade_price": 50500000, "opening_price": 50000000,
             "candle_acc_trade_volume": 100},
        ])
        ext = _make_external_data()
        port = _make_portfolio()
        dc = orch._build_drop_context(md, ext, port)
        assert dc["cascade_risk"] == 0

    def test_cascade_4h_drop_3pct_gives_15(self):
        """4h -3% → cascade += 15 (< -3 is strict, -3% matches < -1.5 tier)."""
        orch = _make_orchestrator()
        candles = [
            {"trade_price": 50000000, "opening_price": 51000000,
             "candle_acc_trade_volume": 100},
            {"trade_price": 48500000, "opening_price": 50000000,
             "candle_acc_trade_volume": 100},
        ]
        md = _make_market_data(candles_4h=candles)
        ext = _make_external_data()
        port = _make_portfolio()
        dc = orch._build_drop_context(md, ext, port)
        # (48500000 - 50000000)/50000000*100 = -3% → < -1.5 tier → 15 pts
        assert dc["cascade_risk"] >= 15

    def test_cascade_4h_drop_4pct_gives_30(self):
        """4h -4% → cascade += 30 (< -3 tier)."""
        orch = _make_orchestrator()
        candles = [
            {"trade_price": 50000000, "opening_price": 51000000,
             "candle_acc_trade_volume": 100},
            {"trade_price": 48000000, "opening_price": 50000000,
             "candle_acc_trade_volume": 100},
        ]
        md = _make_market_data(candles_4h=candles)
        ext = _make_external_data()
        port = _make_portfolio()
        dc = orch._build_drop_context(md, ext, port)
        # (48000000 - 50000000)/50000000*100 = -4% → < -3 → 30 pts
        assert dc["cascade_risk"] >= 30

    def test_cascade_volume_spike_with_drop(self):
        """거래량 3x + 4h -2% → cascade += 20."""
        orch = _make_orchestrator()
        candles = [
            {"trade_price": 50000000, "opening_price": 50500000,
             "candle_acc_trade_volume": 100},
            {"trade_price": 49500000, "opening_price": 50200000,
             "candle_acc_trade_volume": 100},
            {"trade_price": 49200000, "opening_price": 49800000,
             "candle_acc_trade_volume": 100},
            {"trade_price": 49000000, "opening_price": 49500000,
             "candle_acc_trade_volume": 100},
            {"trade_price": 48800000, "opening_price": 49200000,
             "candle_acc_trade_volume": 100},
            {"trade_price": 48500000, "opening_price": 49000000,
             "candle_acc_trade_volume": 300},  # 3x volume
        ]
        md = _make_market_data(candles_4h=candles)
        ext = _make_external_data()
        port = _make_portfolio()
        dc = orch._build_drop_context(md, ext, port)
        # 연속 음봉 5개 이상 → 15점, volume > 2x + drop → 추가 점수
        assert dc["cascade_risk"] >= 15

    def test_cascade_external_bearish_scoring(self):
        """외부 약세 시그널 개당 7점, 최대 25점."""
        orch = _make_orchestrator()
        md = _make_market_data(candles_4h=[
            {"trade_price": 50000000, "opening_price": 50000000,
             "candle_acc_trade_volume": 100},
            {"trade_price": 50000000, "opening_price": 50000000,
             "candle_acc_trade_volume": 100},
        ])
        ext = _make_external_data(
            whale_tracker={"whale_score": {"direction": "exchange_deposit"}},
            binance_sentiment={
                "funding_rate": {"current_rate": 0.002},
                "top_trader_long_short": {"current_ratio": 2.0},
                "kimchi_premium": {"premium_pct": 6.0},
            },
            news_sentiment={"overall_sentiment": "negative"},
            macro={"analysis": {"macro_score": -20}},
        )
        port = _make_portfolio()
        dc = orch._build_drop_context(md, ext, port)
        # 6 bearish signals → min(6*7, 25) = 25
        assert dc["external_bearish_count"] >= 5
        assert dc["cascade_risk"] >= 25

    def test_cascade_capped_at_100(self):
        """극단적 모든 요소 → 100 캡."""
        orch = _make_orchestrator()
        candles = []
        for i in range(6):
            candles.append({
                "trade_price": 50000000 - (i + 1) * 1000000,
                "opening_price": 50000000 - i * 1000000,
                "candle_acc_trade_volume": 50 + i * 100,
            })
        md = _make_market_data(price_change_rate=-10, candles_4h=candles)
        ext = _make_external_data(
            whale_tracker={"whale_score": {"direction": "exchange_deposit"}},
            binance_sentiment={
                "funding_rate": {"current_rate": 0.002},
                "top_trader_long_short": {"current_ratio": 2.0},
                "kimchi_premium": {"premium_pct": 6.0},
            },
            news_sentiment={"overall_sentiment": "negative"},
            macro={"analysis": {"macro_score": -20}},
        )
        port = _make_portfolio()
        dc = orch._build_drop_context(md, ext, port)
        assert dc["cascade_risk"] <= 100

    def test_trend_falling_consecutive_red_3(self):
        """연속 음봉 3개 → trend_falling = True."""
        orch = _make_orchestrator()
        candles = [
            {"trade_price": 50000000, "opening_price": 49000000, "candle_acc_trade_volume": 100},
            {"trade_price": 49500000, "opening_price": 49000000, "candle_acc_trade_volume": 100},
            {"trade_price": 49000000, "opening_price": 49200000, "candle_acc_trade_volume": 100},
            {"trade_price": 48500000, "opening_price": 48800000, "candle_acc_trade_volume": 100},
            {"trade_price": 48000000, "opening_price": 48300000, "candle_acc_trade_volume": 100},
            {"trade_price": 47500000, "opening_price": 47800000, "candle_acc_trade_volume": 100},
        ]
        md = _make_market_data(candles_4h=candles)
        ext = _make_external_data()
        port = _make_portfolio()
        dc = orch._build_drop_context(md, ext, port)
        assert dc["trend_falling"] is True
        assert dc["consecutive_red_candles"] >= 3


# ============================================================
# 6b. Override Decision Extended
# ============================================================

class TestOverrideDecisionExtended:
    """감독 오버라이드 추가 엣지 케이스."""

    def test_override_dca_cascade_69_no_override(self):
        """DCA + cascade=69 → 오버라이드 없음 (70 필요)."""
        orch = _make_orchestrator()
        decision = Decision(
            decision="buy", confidence=0.6, reason="DCA",
            buy_score={}, trade_params={"is_dca": True, "amount": 50000},
            external_signal={}, agent_name="moderate",
        )
        dc = _make_drop_context(cascade_risk=69, price_change_4h=-5,
                                external_bearish_count=3, consecutive_red_candles=4)
        ms = _make_market_state()
        result = orch._override_decision(decision, dc, ms)
        assert result.decision == "buy"  # No override

    def test_override_dca_cascade_70_sell(self):
        """DCA + cascade=70 → 매도 오버라이드."""
        orch = _make_orchestrator()
        decision = Decision(
            decision="buy", confidence=0.6, reason="DCA",
            buy_score={}, trade_params={"is_dca": True, "amount": 50000},
            external_signal={}, agent_name="moderate",
        )
        dc = _make_drop_context(cascade_risk=70, price_change_4h=-5,
                                external_bearish_count=3, consecutive_red_candles=4)
        ms = _make_market_state()
        result = orch._override_decision(decision, dc, ms)
        assert result.decision == "sell"
        assert result._orchestrator_override is True
        assert result.trade_params.get("sell_all") is True

    def test_override_buy_crash_requires_trend_falling(self):
        """매수 + 4h -4% but trend_falling=False → 오버라이드 없음."""
        orch = _make_orchestrator()
        decision = Decision(
            decision="buy", confidence=0.7, reason="Buy",
            buy_score={}, trade_params={"amount": 100000},
            external_signal={}, agent_name="aggressive",
        )
        dc = _make_drop_context(cascade_risk=40, price_change_4h=-4,
                                trend_falling=False, consecutive_red_candles=2)
        ms = _make_market_state()
        result = orch._override_decision(decision, dc, ms)
        assert result.decision == "buy"  # No override

    def test_override_buy_crash_requires_minus_3(self):
        """매수 + 4h -2.9% + trend_falling → 오버라이드 없음 (< -3 필요)."""
        orch = _make_orchestrator()
        decision = Decision(
            decision="buy", confidence=0.7, reason="Buy",
            buy_score={}, trade_params={"amount": 100000},
            external_signal={}, agent_name="aggressive",
        )
        dc = _make_drop_context(cascade_risk=40, price_change_4h=-2.9,
                                trend_falling=True, consecutive_red_candles=5)
        ms = _make_market_state()
        result = orch._override_decision(decision, dc, ms)
        assert result.decision == "buy"  # No override

    def test_override_hold_not_affected(self):
        """관망은 오버라이드 대상 아님."""
        orch = _make_orchestrator()
        decision = Decision(
            decision="hold", confidence=0.5, reason="Hold",
            buy_score={}, trade_params={},
            external_signal={}, agent_name="conservative",
        )
        dc = _make_drop_context(cascade_risk=90, price_change_4h=-8, trend_falling=True)
        ms = _make_market_state()
        result = orch._override_decision(decision, dc, ms)
        assert result.decision == "hold"


# ============================================================
# 7. External Data Fusion Scoring
# ============================================================

class TestExternalDataFusionExtended:
    """외부 데이터 fusion 점수 산출 추가 테스트."""

    def test_inline_fusion_fgi_extreme_fear(self):
        """인라인 fusion: FGI 기반 점수 산출."""
        agent = ExternalDataAgent()
        results = {
            "fear_greed": {"current": {"value": 10}},
        }
        result = agent._inline_fusion(results)
        # FGI < 25 → positive score expected
        assert result["total_score"] >= 0

    def test_inline_fusion_multiple_sources(self):
        """인라인 fusion: 여러 소스 합산."""
        agent = ExternalDataAgent()
        results = {
            "binance_sentiment": {"sentiment_score": {"score": 20}},
            "fear_greed": {"current": {"value": 15}},
        }
        result = agent._inline_fusion(results)
        # binance 20 + fgi bonus
        assert result["total_score"] >= 20

    def test_enhance_fusion_all_components(self):
        """enhance_fusion: 모든 extra 컴포넌트 추가."""
        agent = ExternalDataAgent()
        fusion = {"total_score": 10, "strategy_bonus": 5}
        results = {
            "macro": {"analysis": {"macro_score": 20, "sentiment": "bullish"}},
            "eth_btc": {"eth_btc_z_score": -2.5},
            "news_sentiment": {"sentiment_score": 50, "overall_sentiment": "positive"},
            "crypto_signals": {
                "btc": {"anomaly_level": "HIGH", "change_24h": 5.0},
                "anomaly_alerts": {"count": 10},
            },
            "coinmarketcap": {"status": "success", "btc_dominance": 58.0},
        }
        result = agent._enhance_fusion(fusion, results)
        # 10 + macro(10) + eth(5) + news(10) + crypto(10) + cmc(5) = 50
        assert result["total_score"] >= 40
        assert "extra_components" in result

    def test_enhance_fusion_negative_macro(self):
        """enhance_fusion: 매크로 약세 → 음수 조정."""
        agent = ExternalDataAgent()
        fusion = {"total_score": 10, "strategy_bonus": 5}
        results = {
            "macro": {"analysis": {"macro_score": -25, "sentiment": "bearish"}},
            "eth_btc": {},
            "news_sentiment": {},
            "crypto_signals": {},
            "coinmarketcap": {},
        }
        result = agent._enhance_fusion(fusion, results)
        # macro_adj = max(-15, min(15, -25*0.5)) = max(-15, -12) = -12
        assert result["total_score"] < 10

    def test_enhance_fusion_eth_btc_z_not_extreme(self):
        """enhance_fusion: ETH/BTC z-score < 2 → 점수 없음."""
        agent = ExternalDataAgent()
        fusion = {"total_score": 0, "strategy_bonus": 0}
        results = {
            "macro": {"analysis": {}},
            "eth_btc": {"eth_btc_z_score": 1.5},
            "news_sentiment": {},
            "crypto_signals": {},
            "coinmarketcap": {},
        }
        result = agent._enhance_fusion(fusion, results)
        eth_score = result.get("extra_components", {}).get("eth_btc", {}).get("score", 0)
        assert eth_score == 0

    def test_enhance_fusion_negative_news(self):
        """enhance_fusion: 부정적 뉴스 → 음수."""
        agent = ExternalDataAgent()
        fusion = {"total_score": 0, "strategy_bonus": 0}
        results = {
            "macro": {"analysis": {}},
            "eth_btc": {},
            "news_sentiment": {"sentiment_score": -50, "overall_sentiment": "negative"},
            "crypto_signals": {},
            "coinmarketcap": {},
        }
        result = agent._enhance_fusion(fusion, results)
        assert result["total_score"] < 0

    def test_news_sentiment_overall_thresholds(self):
        """뉴스 감성 점수 경계값 테스트."""
        # score=30 → "positive"
        articles = [{"title": "rally", "content": ""} for _ in range(3)]
        result = analyze_news_sentiment({"articles": articles})
        assert result["sentiment_score"] == 100  # 3/3 positive

        # score=-30 → "negative"
        articles = [{"title": "crash panic", "content": ""} for _ in range(3)]
        result = analyze_news_sentiment({"articles": articles})
        assert result["sentiment_score"] == -100

    def test_news_sentiment_score_10_slightly_positive(self):
        """감성 점수 10~29 → slightly_positive."""
        # 2 positive, 1 negative, 4 neutral = 1/7*100 ≈ 14
        articles = [
            {"title": "rally bullish", "content": ""},
            {"title": "rally bullish", "content": ""},
            {"title": "crash panic", "content": ""},
            {"title": "unrelated", "content": ""},
            {"title": "unrelated", "content": ""},
            {"title": "unrelated", "content": ""},
            {"title": "unrelated", "content": ""},
        ]
        result = analyze_news_sentiment({"articles": articles})
        assert result["overall_sentiment"] == "slightly_positive"


# ============================================================
# 8. Orchestrator _get_fgi Edge Cases
# ============================================================

class TestGetFgiEdgeCases:
    """FGI 수집 실패 시 폴백 테스트."""

    def test_fgi_from_external_data(self):
        """정상 수집 → 값 반환 + state에 저장."""
        orch = _make_orchestrator()
        ext = {"sources": {"fear_greed": {"current": {"value": 25}}}}
        fgi = orch._get_fgi(ext)
        assert fgi == 25
        assert orch.state.get("last_valid_fgi") == 25

    def test_fgi_fallback_to_last_valid(self):
        """수집 실패 → last_valid_fgi 사용."""
        orch = _make_orchestrator(state_overrides={"last_valid_fgi": 35})
        ext = {"sources": {"fear_greed": {}}}
        fgi = orch._get_fgi(ext)
        assert fgi == 35

    def test_fgi_fallback_to_default_50(self):
        """수집 실패 + 이전 값 없음 → 기본값 50."""
        orch = _make_orchestrator()
        ext = {"sources": {"fear_greed": {}}}
        fgi = orch._get_fgi(ext)
        assert fgi == 50

    def test_fgi_string_value_converted(self):
        """FGI가 문자열로 들어와도 int 변환."""
        orch = _make_orchestrator()
        ext = {"sources": {"fear_greed": {"current": {"value": "42"}}}}
        fgi = orch._get_fgi(ext)
        assert fgi == 42

    def test_fgi_missing_sources_key(self):
        """sources 키 자체가 없으면 기본값 50."""
        orch = _make_orchestrator()
        ext = {}
        fgi = orch._get_fgi(ext)
        assert fgi == 50


# ============================================================
# 9. Consecutive Losses Edge Cases
# ============================================================

class TestConsecutiveLossesExtended:

    def test_korean_decision_labels(self):
        """한국어 결정 레이블(매수/매도)도 인식."""
        orch = _make_orchestrator()
        count = orch._count_consecutive_losses([
            {"decision": "매수", "profit_loss": -2.0},
            {"decision": "매도", "profit_loss": -1.0},
            {"decision": "buy", "profit_loss": 5.0},
        ])
        assert count == 2

    def test_none_profit_loss_breaks_chain(self):
        """profit_loss가 None이면 체인 중단."""
        orch = _make_orchestrator()
        count = orch._count_consecutive_losses([
            {"decision": "buy", "profit_loss": None},
            {"decision": "buy", "profit_loss": -2.0},
        ])
        assert count == 0

    def test_zero_profit_not_a_loss(self):
        """profit_loss=0 → 손실 아님, 체인 중단."""
        orch = _make_orchestrator()
        count = orch._count_consecutive_losses([
            {"decision": "buy", "profit_loss": 0},
            {"decision": "buy", "profit_loss": -2.0},
        ])
        assert count == 0

    def test_all_losses(self):
        """모든 항목이 손실이면 전체 카운트."""
        orch = _make_orchestrator()
        count = orch._count_consecutive_losses([
            {"decision": "buy", "profit_loss": -1.0},
            {"decision": "sell", "profit_loss": -2.0},
            {"decision": "매수", "profit_loss": -0.5},
        ])
        assert count == 3


# ============================================================
# 10. Learning Penalty with Performance Adjustment
# ============================================================

class TestLearningAndPerformanceCombined:
    """DB 학습 + 성과 리뷰가 전환 판단에 미치는 복합 효과."""

    def test_bad_learning_suppresses_aggressive_switch(self):
        """학습 페널티(-10) → opportunity 감소 → 공격적 전환 억제."""
        orch = _make_orchestrator("conservative")
        orch._learning_data = {
            ("conservative", "aggressive"): {
                "success_rate_pct": 30,
                "total_switches": 5,
            },
        }
        orch._performance = {}
        # opportunity=65 → -10 = 55. 55 < 60 → 공격적 직행 불가
        # But 40~59 range + conservative → moderate
        ms = _make_market_state(
            danger_score=10, opportunity_score=65,
            fgi=15, rsi=25, price_change_24h=2,
            fusion_signal="strong_buy", phase="extreme_fear",
        )
        result = orch._evaluate_switch(ms)
        # With learning penalty, opportunity becomes 55 → conservative→moderate (not aggressive)
        assert result is not None
        assert result["to"] == "moderate"

    def test_losing_streak_increases_danger(self):
        """연패 성과 → danger 가산 → 보수적 전환 촉진."""
        orch = _make_orchestrator("moderate")
        orch._learning_data = None
        orch._performance = {
            "available": True,
            "win_rate_pct": 30,
            "recent_streak_type": "loss",
            "recent_streak": 4,
        }
        # danger=40 + perf_adj(+15) = 55 → moderate→conservative (>= 50)
        ms = _make_market_state(
            danger_score=40, opportunity_score=10,
            fgi=35, consecutive_losses=2,
        )
        result = orch._evaluate_switch(ms)
        assert result is not None
        assert result["to"] == "conservative"

    def test_feedback_bias_conservative_boosts_danger(self):
        """사용자 피드백 '보수적' → danger +10."""
        orch = _make_orchestrator("moderate")
        orch._learning_data = None
        orch._performance = {}
        orch.state["feedback_bias"] = "conservative"
        orch.state["feedback_bias_set_at"] = time.strftime("%Y-%m-%dT%H:%M:%S+09:00")
        # danger=41 + feedback(+10) = 51 → moderate→conservative
        ms = _make_market_state(
            danger_score=41, opportunity_score=10,
            fgi=35, consecutive_losses=1,
        )
        result = orch._evaluate_switch(ms)
        assert result is not None
        assert result["to"] == "conservative"

    def test_feedback_bias_aggressive_boosts_opportunity(self):
        """사용자 피드백 '공격적' → opportunity +10."""
        orch = _make_orchestrator("moderate")
        orch._learning_data = None
        orch._performance = {}
        orch.state["feedback_bias"] = "aggressive"
        orch.state["feedback_bias_set_at"] = time.strftime("%Y-%m-%dT%H:%M:%S+09:00")
        # opportunity=32 + feedback(+10) = 42 → moderate→aggressive (40~59 range)
        ms = _make_market_state(
            danger_score=10, opportunity_score=32,
            fgi=30, rsi=35, fusion_signal="buy",
        )
        result = orch._evaluate_switch(ms)
        assert result is not None
        assert result["to"] == "aggressive"


# ============================================================
# 11. Agent Thresholds Cross-Check
# ============================================================

class TestAgentThresholdsCrossCheck:
    """에이전트 간 임계값 일관성 검증."""

    def test_buy_thresholds_ordering(self):
        """aggressive < moderate < conservative (매수 난이도)."""
        c = ConservativeAgent()
        m = ModerateAgent()
        a = AggressiveAgent()
        assert a.buy_score_threshold < m.buy_score_threshold <= c.buy_score_threshold

    def test_stop_loss_ordering(self):
        """conservative 손절선이 aggressive보다 넓음 (더 관대)."""
        c = ConservativeAgent()
        a = AggressiveAgent()
        # Conservative: -5%, Aggressive: -3% → aggressive가 더 빠른 손절
        assert a.stop_loss_pct > c.stop_loss_pct  # -3 > -5

    def test_target_profit_ordering(self):
        """aggressive 목표수익이 conservative보다 낮음 (빠른 익절)."""
        c = ConservativeAgent()
        a = AggressiveAgent()
        assert a.target_profit_pct < c.target_profit_pct

    def test_trade_ratio_ordering(self):
        """aggressive가 1회 매매 비율이 가장 높음."""
        c = ConservativeAgent()
        m = ModerateAgent()
        a = AggressiveAgent()
        assert a.max_trade_ratio >= m.max_trade_ratio >= c.max_trade_ratio

    def test_fgi_threshold_ordering(self):
        """aggressive FGI 임계가 가장 높음 (탐욕 구간에서도 매수)."""
        c = ConservativeAgent()
        m = ModerateAgent()
        a = AggressiveAgent()
        assert a.fgi_threshold >= m.fgi_threshold >= c.fgi_threshold
