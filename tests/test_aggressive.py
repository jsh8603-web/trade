"""
AggressiveAgent 유닛 테스트

Coverage:
  - 임계값 검증 (v2: threshold 40, FGI 60, RSI 50)
  - 뉴스 무관 (항상 20점 자동 부여)
  - AI 필터 없음
  - 빠른 익절(7%), 빠른 손절(-3%)
  - 주말 축소 없음
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.aggressive import AggressiveAgent


@pytest.fixture
def agent():
    return AggressiveAgent()


def _md(rsi=50, sma_deviation=0, fgi=50, ai_score=0,
        news_sentiment="neutral", trade_price=50000000):
    return {
        "indicators": {
            "rsi_14": rsi, "sma_20": trade_price,
            "sma_20_deviation_pct": sma_deviation,
            "macd": {"histogram": 0, "signal_cross": False},
            "bollinger": {},
        },
        "ticker": {"trade_price": trade_price, "signed_change_rate": 0},
        "fear_greed": {"value": fgi},
        "news": {"overall_sentiment": news_sentiment},
        "ai_composite_signal": {"score": ai_score},
        "current_price": trade_price,
        "candles_4h": [],
    }


def _port(krw=1000000, btc_balance=0, profit_pct=0, total_eval=1000000):
    btc_eval = btc_balance * 50000000 if btc_balance > 0 else 0
    return {
        "krw_balance": krw,
        "btc": {"balance": btc_balance, "avg_buy_price": 50000000,
                "profit_pct": profit_pct, "eval_amount": btc_eval},
        "total_eval": total_eval,
        "btc_ratio": btc_eval / total_eval if total_eval > 0 else 0,
    }


def _ext(strategy_bonus=0):
    return {"total_score": 0, "strategy_bonus": strategy_bonus,
            "fusion": {"signal": "neutral"}}


# ============================================================
# Thresholds
# ============================================================

class TestAggressiveThresholds:

    def test_buy_threshold(self, agent):
        assert agent.buy_score_threshold == 40

    def test_fgi_threshold(self, agent):
        assert agent.fgi_threshold == 60

    def test_rsi_threshold(self, agent):
        assert agent.rsi_threshold == 50

    def test_sma_deviation(self, agent):
        assert agent.sma_deviation_pct == -1.0

    def test_target_profit(self, agent):
        assert agent.target_profit_pct == 7.0

    def test_stop_loss(self, agent):
        assert agent.stop_loss_pct == -3.0

    def test_forced_stop_loss(self, agent):
        assert agent.forced_stop_loss_pct == -7.0

    def test_sell_fgi_threshold(self, agent):
        assert agent.sell_fgi_threshold == 65

    def test_sell_rsi_threshold(self, agent):
        assert agent.sell_rsi_threshold == 60

    def test_max_trade_ratio(self, agent):
        assert agent.max_trade_ratio == 0.20

    def test_max_daily_trades(self, agent):
        assert agent.max_daily_trades == 7

    def test_weekend_reduction_zero(self, agent):
        assert agent.weekend_reduction == 0.0

    def test_no_macd_bonus(self, agent):
        assert agent.macd_bonus is False

    def test_name_and_emoji(self, agent):
        assert agent.name == "aggressive"
        assert agent.emoji == "🔥"


# ============================================================
# News Always Positive
# ============================================================

class TestAggressiveNewsAlwaysPositive:

    @patch.dict(os.environ, {"MAX_TRADE_AMOUNT": "100000"})
    def test_buy_despite_negative_news(self, agent):
        """뉴스가 negative여도 항상 20점 자동 부여."""
        md = _md(rsi=45, sma_deviation=-2.0, fgi=55,
                 ai_score=0, news_sentiment="negative")
        decision = agent.decide(md, _ext(strategy_bonus=5), _port())
        assert decision.decision == "buy"

    def test_news_always_positive_in_score(self, agent):
        """calculate_buy_score에서 news_negative=False가 전달됨."""
        score = agent.calculate_buy_score(
            fgi=55, rsi=45, sma_deviation=-2.0,
            news_negative=False, external_bonus=0,
        )
        assert score["news"]["score"] == 20


# ============================================================
# No AI Filter
# ============================================================

class TestAggressiveNoAiFilter:

    @patch.dict(os.environ, {"MAX_TRADE_AMOUNT": "100000"})
    def test_no_ai_veto_negative(self, agent):
        """AI 음수여도 매수 진행."""
        md = _md(rsi=45, sma_deviation=-2.0, fgi=55, ai_score=-10)
        decision = agent.decide(md, _ext(strategy_bonus=5), _port())
        assert decision.decision == "buy"

    @patch.dict(os.environ, {"MAX_TRADE_AMOUNT": "100000"})
    def test_no_ai_veto_very_negative(self, agent):
        """AI -50이어도 매수 진행."""
        md = _md(rsi=45, sma_deviation=-2.0, fgi=55, ai_score=-50)
        decision = agent.decide(md, _ext(strategy_bonus=5), _port())
        assert decision.decision == "buy"

    @patch.dict(os.environ, {"MAX_TRADE_AMOUNT": "100000"})
    def test_no_was_ai_vetoed_attr(self, agent):
        """Aggressive 매수 시 _was_ai_vetoed 속성이 없다."""
        md = _md(rsi=45, sma_deviation=-2.0, fgi=55, ai_score=-10)
        decision = agent.decide(md, _ext(strategy_bonus=5), _port())
        assert decision.decision == "buy"
        assert not decision._was_ai_vetoed


# ============================================================
# Fast Take-Profit and Stop-Loss
# ============================================================

class TestAggressiveSell:

    @patch.dict(os.environ, {"MAX_TRADE_AMOUNT": "100000"})
    def test_target_profit_7pct(self, agent):
        """v6: profit 8%(25pts) + RSI 75(20pts) + FGI 70(15pts) = 60 >= sideways(55)."""
        md = _md(fgi=70, rsi=75)
        port = _port(btc_balance=0.01, profit_pct=8.0, total_eval=1000000)
        dc = {"v6_regime": "sideways", "v6_sma_deviation": 0, "v6_change_24h": 0,
              "v6_danger_score": 0, "v6_macro_score": 0, "v6_kimchi_pct": 0,
              "v6_news_negative": False, "v6_current_price": 50000000, "v6_position_peak": 0}
        decision = agent.decide(md, _ext(), port, drop_context=dc)
        assert decision.decision == "sell"

    @patch.dict(os.environ, {"MAX_TRADE_AMOUNT": "100000"})
    def test_target_profit_boundary(self, agent):
        """v6: profit 7%(25pts) + RSI 75(20pts) + FGI 70(15pts) = 60 >= sideways(55)."""
        md = _md(fgi=70, rsi=75)
        port = _port(btc_balance=0.01, profit_pct=7.0, total_eval=1000000)
        dc = {"v6_regime": "sideways", "v6_sma_deviation": 0, "v6_change_24h": 0,
              "v6_danger_score": 0, "v6_macro_score": 0, "v6_kimchi_pct": 0,
              "v6_news_negative": False, "v6_current_price": 50000000, "v6_position_peak": 0}
        decision = agent.decide(md, _ext(), port, drop_context=dc)
        assert decision.decision == "sell"

    @patch.dict(os.environ, {"MAX_TRADE_AMOUNT": "100000"})
    def test_target_profit_below(self, agent):
        """v6: profit 6.9%(25pts) 단독으로는 sideways(55) 미달 → 매도 안 함."""
        md = _md(fgi=50, rsi=50)
        port = _port(btc_balance=0.01, profit_pct=6.9, total_eval=1000000)
        dc = {"v6_regime": "sideways", "v6_sma_deviation": 0, "v6_change_24h": 0,
              "v6_danger_score": 0, "v6_macro_score": 0, "v6_kimchi_pct": 0,
              "v6_news_negative": False, "v6_current_price": 50000000, "v6_position_peak": 0}
        decision = agent.decide(md, _ext(), port, drop_context=dc)
        # profit 5%+ → 20pts, FGI 50 → 0, RSI 50 → 0 = 20 < 55
        assert decision.decision != "sell" or "v6_sell_score" not in decision.reason

    @patch.dict(os.environ, {"MAX_TRADE_AMOUNT": "100000"})
    def test_forced_stop_7pct(self, agent):
        """강제 손절 -7% (aggressive forced_stop_loss_pct = -7)."""
        md = _md(fgi=50, rsi=50)
        port = _port(btc_balance=0.01, profit_pct=-8.0, total_eval=1000000)
        dc = {"v6_regime": "sideways", "v6_sma_deviation": 0, "v6_change_24h": 0,
              "v6_danger_score": 0, "v6_macro_score": 0, "v6_kimchi_pct": 0,
              "v6_news_negative": False, "v6_current_price": 50000000, "v6_position_peak": 0}
        decision = agent.decide(md, _ext(), port, drop_context=dc)
        assert decision.decision == "sell"

    @patch.dict(os.environ, {"MAX_TRADE_AMOUNT": "100000"})
    def test_stop_loss_3pct(self, agent):
        """일반 손절 -3.5%: FGI/RSI 높아 바닥 시그널 없음 → 손절."""
        md = _md(fgi=80, rsi=75)
        port = _port(btc_balance=0.01, profit_pct=-3.5, total_eval=1000000)
        dc = {"v6_regime": "sideways", "v6_sma_deviation": 0, "v6_change_24h": 0,
              "v6_danger_score": 0, "v6_macro_score": 0, "v6_kimchi_pct": 0,
              "v6_news_negative": False, "v6_current_price": 50000000, "v6_position_peak": 0}
        decision = agent.decide(md, _ext(), port, drop_context=dc)
        assert decision.decision == "sell"

    @patch.dict(os.environ, {"MAX_TRADE_AMOUNT": "100000"})
    def test_sell_lower_fgi_threshold(self, agent):
        """v6: FGI 66(8pts) + profit 3%(15pts) + RSI 65(8pts) + danger 60(10pts) = 41.
        With bear regime threshold(45): add sma_dev=-2(15pts) = 56 >= 45."""
        md = _md(fgi=66, rsi=65)
        port = _port(btc_balance=0.01, profit_pct=3.0, total_eval=1000000)
        dc = {"v6_regime": "bear", "v6_sma_deviation": -2.5, "v6_change_24h": 0,
              "v6_danger_score": 60, "v6_macro_score": 0, "v6_kimchi_pct": 0,
              "v6_news_negative": False, "v6_current_price": 50000000, "v6_position_peak": 0}
        decision = agent.decide(md, _ext(), port, drop_context=dc)
        assert decision.decision == "sell"

    @patch.dict(os.environ, {"MAX_TRADE_AMOUNT": "100000"})
    def test_sell_lower_rsi_threshold(self, agent):
        """v6: RSI 65(8pts) + profit 3%(15pts) + FGI 60(8pts) + danger 60(10pts) + sma_dev(15pts) = 56 >= bear(45)."""
        md = _md(fgi=60, rsi=65)
        port = _port(btc_balance=0.01, profit_pct=3.0, total_eval=1000000)
        dc = {"v6_regime": "bear", "v6_sma_deviation": -2.5, "v6_change_24h": 0,
              "v6_danger_score": 60, "v6_macro_score": 0, "v6_kimchi_pct": 0,
              "v6_news_negative": False, "v6_current_price": 50000000, "v6_position_peak": 0}
        decision = agent.decide(md, _ext(), port, drop_context=dc)
        assert decision.decision == "sell"


# ============================================================
# Weekend & Trade Ratio
# ============================================================

class TestAggressiveTrading:

    @patch.dict(os.environ, {"MAX_TRADE_AMOUNT": "500000"})
    def test_trade_ratio_20pct(self, agent):
        """regime_trade_ratios sideways=0.1 → min(0.20, 0.10) = 0.10"""
        with patch.object(agent, '_is_weekend', return_value=False):
            amount = agent._calculate_trade_amount(1000000)
            assert amount == 100000  # sideways 레짐 기본

    @patch.dict(os.environ, {"MAX_TRADE_AMOUNT": "500000"})
    def test_no_weekend_reduction(self, agent):
        """Aggressive는 주말 축소 없음."""
        with patch.object(agent, '_is_weekend', return_value=True):
            amount = agent._calculate_trade_amount(1000000, external_bonus=0)
            # weekend_reduction = 0.0, regime sideways=0.1
            assert amount == 100000


# ============================================================
# Cross-Agent Comparison
# ============================================================

class TestAggressiveVsOthers:

    def test_lowest_buy_threshold(self, agent):
        from agents.conservative import ConservativeAgent
        from agents.moderate import ModerateAgent
        assert agent.buy_score_threshold < ModerateAgent().buy_score_threshold
        assert agent.buy_score_threshold < ConservativeAgent().buy_score_threshold

    def test_highest_fgi_threshold(self, agent):
        from agents.conservative import ConservativeAgent
        from agents.moderate import ModerateAgent
        assert agent.fgi_threshold > ModerateAgent().fgi_threshold
        assert agent.fgi_threshold > ConservativeAgent().fgi_threshold

    def test_tightest_stop_loss(self, agent):
        from agents.conservative import ConservativeAgent
        assert agent.stop_loss_pct > ConservativeAgent().stop_loss_pct  # -3 > -5

    def test_lowest_target_profit(self, agent):
        from agents.conservative import ConservativeAgent
        from agents.moderate import ModerateAgent
        assert agent.target_profit_pct < ModerateAgent().target_profit_pct
        assert agent.target_profit_pct < ConservativeAgent().target_profit_pct

    def test_highest_trade_ratio(self, agent):
        from agents.conservative import ConservativeAgent
        from agents.moderate import ModerateAgent
        assert agent.max_trade_ratio > ModerateAgent().max_trade_ratio
        assert agent.max_trade_ratio > ConservativeAgent().max_trade_ratio
