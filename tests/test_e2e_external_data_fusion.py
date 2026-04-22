"""
E2E 테스트: ExternalDataAgent(뉴스랑) 11소스 병렬 수집 + Data Fusion

E2팀 담당: 외부 데이터 11개 소스를 mock으로 대체하여 full happy,
강세/약세 방향성, 부분 실패(fail-open), 전체 실패(safe neutral) 시나리오를 검증한다.

11 소스:
  1. FGI            (collect_fear_greed.py)
  2. Tavily 뉴스    (collect_news.py)
  3. mempool 고래   (whale_tracker.py)
  4. Binance 심리   (binance_sentiment.py)
  5. ETH/BTC 비율   (collect_eth_btc.py)
  6. Yahoo 매크로   (collect_macro.py)
  7. CoinGecko 이상 (collect_crypto_signals.py)
  8. CoinMarketCap  (collect_coinmarketcap.py)
  9. RSS 뉴스       (collect_rss_news.py)
 10. X 트위터       (collect_x_signals.py)
 11. 소셜 감성      (collect_social_sentiment.py)
  + NVT Signal (blockchain.com)
  + Supabase: feedback / performance_review

Fusion 점수 이론 최대치:
  - calculate_external_signal.py(binance/whale/news/...)의 base + ±80 보너스
  - ±15(macro) +5(eth_btc) +10(news) +10(crypto) +5(cmc) +10(rss) +15+5(x) +10(social)
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.external_data import ExternalDataAgent  # noqa: E402


# ============================================================
# Mock payload builders
# ============================================================

def _bullish_payload(script: str) -> dict:
    """모든 소스가 강세 방향을 반환하는 페이로드를 생성한다."""
    if "fear_greed" in script:
        return {"current": {"value": 20, "classification": "Extreme Fear"}}
    if "collect_news.py" in script:
        return {
            "articles": [
                {"title": "ETF approved bullish rally adoption",
                 "content": "institutional inflow breaks all-time high",
                 "category": "crypto"},
                {"title": "승인 호재 상승 돌파 강세 매수세",
                 "content": "신고가 유입 반등", "category": "crypto"},
            ]
        }
    if "whale_tracker" in script:
        return {
            "whale_score": {"score": 15, "direction": "accumulation"},
            "block_analysis": {
                "whale_txs_count": 8,
                "direction_btc": {"exchange_deposit": 20, "exchange_withdrawal": 80},
            },
        }
    if "binance_sentiment" in script:
        return {
            "sentiment_score": {"score": 15},
            "top_trader_long_short": {"current_ratio": 0.9},
            "funding_rate": {"current_rate": -0.0005},
            "open_interest": {"oi_change_24h_pct": 1.5},
            "kimchi_premium": {"premium_pct": -1.2},
        }
    if "collect_eth_btc" in script:
        return {"eth_btc_ratio": 0.055, "eth_btc_z_score": -2.3, "signal": "btc_strong"}
    if "collect_macro" in script:
        return {
            "analysis": {"macro_score": 24, "sentiment": "risk_on"},
            "quotes": {
                "sp500": {"change_pct": 1.2},
                "dxy": {"change_pct": -0.4},
                "gold": {"change_pct": 0.2},
                "us10y": {"change_pct": -0.1},
            },
        }
    if "collect_crypto_signals" in script:
        return {
            "btc": {"anomaly_level": "HIGH", "change_24h": 4.5},
            "anomaly_alerts": {"count": 10},
        }
    if "collect_coinmarketcap" in script:
        return {"status": "success", "btc_dominance": 58.0}
    if "collect_rss_news" in script:
        return {
            "total_articles": 30,
            "sentiment": {
                "combined_score": 28,
                "crypto": {"sentiment_score": 30, "key_signals": ["bullish"]},
                "macro": {"sentiment_score": 20, "key_signals": ["risk_on"]},
            },
        }
    if "collect_x_signals" in script:
        return {
            "signal": {
                "score": 35, "signal": "strong_bullish",
                "tweet_count": 15, "bullish_count": 12, "bearish_count": 1,
                "whale_summary": {"total_alerts": 3, "net_direction": "buy"},
            },
            "tweets": [],
        }
    if "collect_social_sentiment" in script:
        return {
            "signal": {"total_score": 25, "signal": "bullish", "sources_available": 3,
                       "components": {"reddit": 8, "twitter": 10, "coingecko": 7}},
            "sources": {"cryptocompare": {}, "coingecko": {}},
        }
    return {}


def _bearish_payload(script: str) -> dict:
    """모든 소스가 약세 방향을 반환하는 페이로드를 생성한다."""
    if "fear_greed" in script:
        return {"current": {"value": 85, "classification": "Extreme Greed"}}
    if "collect_news.py" in script:
        return {
            "articles": [
                {"title": "Major hack exploit crash panic", "content": "bearish sell-off liquidation", "category": "crypto"},
                {"title": "해킹 폭락 사기 소송 제재 전쟁", "content": "공격 파산 청산 약세 하락", "category": "crypto"},
            ]
        }
    if "whale_tracker" in script:
        return {
            "whale_score": {"score": -18, "direction": "distribution"},
            "block_analysis": {
                "whale_txs_count": 12,
                "direction_btc": {"exchange_deposit": 90, "exchange_withdrawal": 15},
            },
        }
    if "binance_sentiment" in script:
        return {
            "sentiment_score": {"score": -20},
            "top_trader_long_short": {"current_ratio": 1.8},
            "funding_rate": {"current_rate": 0.0012},
            "open_interest": {"oi_change_24h_pct": -5.0},
            "kimchi_premium": {"premium_pct": 4.5},
        }
    if "collect_eth_btc" in script:
        return {"eth_btc_ratio": 0.075, "eth_btc_z_score": 2.4, "signal": "alt_overheated"}
    if "collect_macro" in script:
        return {
            "analysis": {"macro_score": -26, "sentiment": "risk_off"},
            "quotes": {
                "sp500": {"change_pct": -1.8},
                "dxy": {"change_pct": 0.9},
                "gold": {"change_pct": -0.3},
                "us10y": {"change_pct": 0.4},
            },
        }
    if "collect_crypto_signals" in script:
        return {
            "btc": {"anomaly_level": "HIGH", "change_24h": -5.2},
            "anomaly_alerts": {"count": 40},
        }
    if "collect_coinmarketcap" in script:
        return {"status": "success", "btc_dominance": 42.0}
    if "collect_rss_news" in script:
        return {
            "total_articles": 25,
            "sentiment": {
                "combined_score": -28,
                "crypto": {"sentiment_score": -30, "key_signals": ["panic"]},
                "macro": {"sentiment_score": -20, "key_signals": ["risk_off"]},
            },
        }
    if "collect_x_signals" in script:
        return {
            "signal": {
                "score": -35, "signal": "strong_bearish",
                "tweet_count": 18, "bullish_count": 2, "bearish_count": 14,
                "whale_summary": {"total_alerts": 4, "net_direction": "sell"},
            },
            "tweets": [],
        }
    if "collect_social_sentiment" in script:
        return {
            "signal": {"total_score": -22, "signal": "bearish", "sources_available": 3,
                       "components": {"reddit": -8, "twitter": -9, "coingecko": -5}},
            "sources": {"cryptocompare": {}, "coingecko": {}},
        }
    return {}


def _neutral_payload(script: str) -> dict:
    """모든 소스가 중립 — 0에 가까운 값을 반환."""
    if "fear_greed" in script:
        return {"current": {"value": 50, "classification": "Neutral"}}
    if "collect_news.py" in script:
        return {"articles": [{"title": "Market update", "content": "mixed signals", "category": "crypto"}]}
    if "whale_tracker" in script:
        return {"whale_score": {"score": 0, "direction": "neutral"},
                "block_analysis": {"whale_txs_count": 3,
                                    "direction_btc": {"exchange_deposit": 50, "exchange_withdrawal": 50}}}
    if "binance_sentiment" in script:
        return {"sentiment_score": {"score": 0},
                "top_trader_long_short": {"current_ratio": 1.0},
                "funding_rate": {"current_rate": 0.0001},
                "open_interest": {"oi_change_24h_pct": 0.1},
                "kimchi_premium": {"premium_pct": 0.5}}
    if "collect_eth_btc" in script:
        return {"eth_btc_ratio": 0.06, "eth_btc_z_score": 0.2, "signal": "neutral"}
    if "collect_macro" in script:
        return {"analysis": {"macro_score": 0, "sentiment": "neutral"},
                "quotes": {"sp500": {"change_pct": 0.1}, "dxy": {"change_pct": 0.0},
                           "gold": {"change_pct": 0.0}, "us10y": {"change_pct": 0.0}}}
    if "collect_crypto_signals" in script:
        return {"btc": {"anomaly_level": "LOW", "change_24h": 0.3}, "anomaly_alerts": {"count": 3}}
    if "collect_coinmarketcap" in script:
        return {"status": "success", "btc_dominance": 50.0}
    if "collect_rss_news" in script:
        return {"total_articles": 10,
                "sentiment": {"combined_score": 0,
                              "crypto": {"sentiment_score": 0, "key_signals": []},
                              "macro": {"sentiment_score": 0, "key_signals": []}}}
    if "collect_x_signals" in script:
        return {"signal": {"score": 0, "signal": "neutral", "tweet_count": 5,
                           "bullish_count": 2, "bearish_count": 2, "whale_summary": None},
                "tweets": []}
    if "collect_social_sentiment" in script:
        return {"signal": {"total_score": 0, "signal": "neutral", "sources_available": 3,
                           "components": {}}, "sources": {}}
    return {}


def _make_run_script(flavor: str, failing: set[str] | None = None):
    """지정된 방향(강세/약세/중립) 페이로드를 반환하는 _run_script mock factory.

    failing: 실패로 처리할 스크립트 이름 서브스트링 집합.
    """
    builders = {
        "bullish": _bullish_payload,
        "bearish": _bearish_payload,
        "neutral": _neutral_payload,
    }
    build = builders[flavor]
    fail = failing or set()

    def side_effect(script, *args, **kwargs):
        # calculate_external_signal.py는 base fusion 역할 — 방향별 base_score 반환
        if "calculate_external_signal" in script:
            if flavor == "bullish":
                return {"total_score": 30, "strategy_bonus": 15,
                        "fusion": {"signal": "bullish", "note": "base bullish"}}
            if flavor == "bearish":
                return {"total_score": -30, "strategy_bonus": -15,
                        "fusion": {"signal": "bearish", "note": "base bearish"}}
            return {"total_score": 0, "strategy_bonus": 0,
                    "fusion": {"signal": "neutral", "note": "base neutral"}}

        # failing 대상이면 에러 반환
        for token in fail:
            if token in script:
                return {"error": f"mocked timeout: {script}"}

        return build(script)

    return side_effect


# ============================================================
# E2E Fixtures
# ============================================================

@pytest.fixture
def agent_with_stubs(tmp_path):
    """Supabase/DB 저장, 외부 함수들을 stub 처리한 ExternalDataAgent.

    snapshot_dir을 설정하여 _enhance_fusion 경로(extra_components 포함)를 타도록 한다.
    """
    agent = ExternalDataAgent(snapshot_dir=tmp_path / "snapshots")
    # DB 저장 차단
    agent._save_signal_to_db = lambda *a, **k: None  # type: ignore[assignment]
    agent._save_newsrang_to_db = lambda *a, **k: None  # type: ignore[assignment]
    return agent


# ============================================================
# 1) Full Happy Path — 모든 소스 정상, Fusion 점수 ±145 이내
# ============================================================

class TestFusionFullHappy:
    """모든 소스가 정상 응답 — Fusion 점수 산출 및 구조 검증."""

    @patch("agents.external_data._fetch_nvt_signal")
    @patch("agents.external_data._run_script")
    @patch("agents.external_data.load_user_feedback", return_value=[])
    @patch("agents.external_data.load_performance_review", return_value={"available": False})
    def test_fusion_full_happy(self, mock_perf, mock_fb, mock_run, mock_nvt, agent_with_stubs):
        mock_run.side_effect = _make_run_script("neutral")
        mock_nvt.return_value = {"nvt_signal": 100.0}

        result = agent_with_stubs.collect_all()

        # 1. 필수 키 존재
        assert "timestamp" in result
        assert "collection_time_sec" in result
        assert "sources" in result
        assert "external_signal" in result
        assert "errors" in result
        assert "warnings" in result

        # 2. 11 소스 + nvt가 sources에 포함 (x_signals 제외 — 현재 주석처리)
        expected_sources = {
            "fear_greed", "news", "whale_tracker", "binance_sentiment",
            "eth_btc", "macro", "crypto_signals", "coinmarketcap",
            "rss_news", "social_sentiment", "nvt",
        }
        assert expected_sources.issubset(set(result["sources"].keys())), \
            f"missing sources: {expected_sources - set(result['sources'].keys())}"

        # 3. 에러 없음 (모두 정상 응답)
        assert result["errors"] == [], f"unexpected errors: {result['errors']}"

        # 4. Fusion 점수 범위 검증 (CLAUDE.md 기준: ±145)
        ext_sig = result["external_signal"]
        assert "total_score" in ext_sig
        assert "strategy_bonus" in ext_sig
        assert -145 <= ext_sig["total_score"] <= 145, \
            f"total_score out of range: {ext_sig['total_score']}"
        assert -20 <= ext_sig["strategy_bonus"] <= 20

        # 5. 뉴스 감성/압축 포스트 처리 확인
        assert "news_sentiment" in result["sources"]
        assert "user_feedback" in result["sources"]
        assert "performance_review" in result["sources"]


# ============================================================
# 2) Strong Buy Signal — 전 소스 강세
# ============================================================

class TestFusionStrongBuy:
    """모든 소스 강세 → Fusion 양수, strategy_bonus 양수 확인."""

    @patch("agents.external_data._fetch_nvt_signal")
    @patch("agents.external_data._run_script")
    @patch("agents.external_data.load_user_feedback", return_value=[])
    @patch("agents.external_data.load_performance_review", return_value={"available": False})
    def test_fusion_strong_buy_signal(self, mock_perf, mock_fb, mock_run, mock_nvt, agent_with_stubs):
        mock_run.side_effect = _make_run_script("bullish")
        mock_nvt.return_value = {"nvt_signal": 45.0, "interpretation": "undervalued"}

        result = agent_with_stubs.collect_all()
        ext_sig = result["external_signal"]

        # 강세 기대: total_score > 15, strategy_bonus > 0
        assert ext_sig["total_score"] > 15, \
            f"expected strong buy score, got {ext_sig['total_score']}"
        assert ext_sig["strategy_bonus"] > 0

        # 확장 컴포넌트 중 대부분 양수
        extra = ext_sig.get("extra_components", {})
        positive_components = sum(1 for c in extra.values() if c.get("score", 0) > 0)
        assert positive_components >= 5, \
            f"expected majority positive components, got {positive_components}"

        # 뉴스 감성 positive
        assert result["sources"]["news_sentiment"]["sentiment_score"] > 0
        # 에러 없음
        assert result["errors"] == []


# ============================================================
# 3) Strong Sell Signal — 전 소스 약세
# ============================================================

class TestFusionStrongSell:
    """모든 소스 약세 → Fusion 음수, strategy_bonus 음수 확인."""

    @patch("agents.external_data._fetch_nvt_signal")
    @patch("agents.external_data._run_script")
    @patch("agents.external_data.load_user_feedback", return_value=[])
    @patch("agents.external_data.load_performance_review", return_value={"available": False})
    def test_fusion_strong_sell_signal(self, mock_perf, mock_fb, mock_run, mock_nvt, agent_with_stubs):
        mock_run.side_effect = _make_run_script("bearish")
        mock_nvt.return_value = {"nvt_signal": 200.0, "interpretation": "overvalued"}

        result = agent_with_stubs.collect_all()
        ext_sig = result["external_signal"]

        # 약세 기대: total_score < -15, strategy_bonus < 0
        assert ext_sig["total_score"] < -15, \
            f"expected strong sell score, got {ext_sig['total_score']}"
        assert ext_sig["strategy_bonus"] < 0

        extra = ext_sig.get("extra_components", {})
        negative_components = sum(1 for c in extra.values() if c.get("score", 0) < 0)
        assert negative_components >= 5, \
            f"expected majority negative components, got {negative_components}"

        # 뉴스 감성 negative
        assert result["sources"]["news_sentiment"]["sentiment_score"] < 0


# ============================================================
# 4) Partial Failure — 3~5개 소스 실패, 나머지로 Fusion 산출 (fail-open)
# ============================================================

class TestFusionPartialFailure:
    """일부 소스 타임아웃/에러여도 나머지로 Fusion 정상 산출."""

    @patch("agents.external_data._fetch_nvt_signal")
    @patch("agents.external_data._run_script")
    @patch("agents.external_data.load_user_feedback", return_value=[])
    @patch("agents.external_data.load_performance_review", return_value={"available": False})
    def test_fusion_partial_failure(self, mock_perf, mock_fb, mock_run, mock_nvt, agent_with_stubs):
        # 5개 스크립트가 실패: fear_greed, whale_tracker, macro, rss_news, social_sentiment
        failing = {"fear_greed", "whale_tracker", "collect_macro",
                   "collect_rss_news", "collect_social_sentiment"}
        mock_run.side_effect = _make_run_script("bullish", failing=failing)
        mock_nvt.return_value = {"nvt_signal": 100.0}

        result = agent_with_stubs.collect_all()

        # errors 목록에 실패 소스가 적어도 3개 이상 반영
        error_names = set(result["errors"])
        assert len(error_names) >= 3, \
            f"expected >=3 errors, got {error_names}"
        assert "fear_greed" in error_names
        assert "whale_tracker" in error_names

        # 나머지 정상 소스는 여전히 존재
        assert result["sources"].get("binance_sentiment", {}).get("sentiment_score") is not None
        assert "eth_btc" in result["sources"]

        # Fusion은 여전히 산출되며 범위 내 (fail-open)
        ext_sig = result["external_signal"]
        assert "total_score" in ext_sig
        assert -145 <= ext_sig["total_score"] <= 145
        # 앱이 크래시하지 않고 구조 유지
        assert "strategy_bonus" in ext_sig


# ============================================================
# 5) All Fail — 모든 소스 실패 → 안전한 neutral (crash 없음)
# ============================================================

class TestFusionAllFail:
    """모든 소스 실패 → 안전한 neutral 반환, 앱이 크래시 안함."""

    @patch("agents.external_data._fetch_nvt_signal")
    @patch("agents.external_data._run_script")
    @patch("agents.external_data.load_user_feedback", return_value=[])
    @patch("agents.external_data.load_performance_review", return_value={"available": False})
    def test_fusion_all_fail(self, mock_perf, mock_fb, mock_run, mock_nvt, agent_with_stubs):
        # 모든 스크립트 실패 응답
        def all_fail(script, *args, **kwargs):
            return {"error": f"total failure: {script}"}
        mock_run.side_effect = all_fail
        # NVT도 실패
        mock_nvt.return_value = {"nvt_signal": 100.0, "error": "fetch_failed"}

        # crash 없이 완료
        result = agent_with_stubs.collect_all()

        # 모든 주요 소스가 errors에 포함
        error_names = set(result["errors"])
        assert "fear_greed" in error_names
        assert "binance_sentiment" in error_names
        assert "whale_tracker" in error_names

        # Fusion 결과가 neutral 쪽에 수렴 + 구조 유지
        ext_sig = result["external_signal"]
        assert isinstance(ext_sig, dict)
        assert "total_score" in ext_sig
        assert "strategy_bonus" in ext_sig
        # 모든 기여 요소가 0이므로 total_score도 0 근처
        assert abs(ext_sig["total_score"]) <= 20, \
            f"expected near-neutral on all-fail, got {ext_sig['total_score']}"
        assert ext_sig["strategy_bonus"] in (-5, 0, 5)

        # 기본 구조 유지 — 크래시/None 없음
        assert result["sources"] is not None
        assert result["timestamp"]
        assert result["collection_time_sec"] >= 0
