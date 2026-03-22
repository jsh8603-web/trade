"""
ExternalDataAgent의 crypto_signals 통합 테스트.

collect_all(), _enhance_fusion(), _inline_fusion()에서
CoinGecko crypto_signals 데이터를 올바르게 처리하는지 검증한다.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from agents.external_data import ExternalDataAgent, _run_script


# ── Fixtures ──────────────────────────────────────────


@pytest.fixture
def agent():
    return ExternalDataAgent(snapshot_dir=None)


@pytest.fixture
def agent_with_snapshot(tmp_path):
    return ExternalDataAgent(snapshot_dir=tmp_path / "snapshots")


def _make_results(**overrides):
    """기본 results dict를 생성한다. overrides로 특정 소스를 덮어쓸 수 있다."""
    base = {
        "fear_greed": {"current": {"value": 50}},
        "news": {"articles": []},
        "whale_tracker": {"whale_score": {"score": 0}},
        "binance_sentiment": {"sentiment_score": {"score": 0}},
        "eth_btc": {"eth_btc_z_score": 0},
        "macro": {"analysis": {"macro_score": 0, "sentiment": "neutral"}},
        "crypto_signals": {},
        "news_sentiment": {"sentiment_score": 0, "overall_sentiment": "neutral"},
    }
    base.update(overrides)
    return base


# ── 1. collect_all: crypto_signals가 tasks에 포함되는지 ─────


class TestCollectAllCryptoSignals:

    @patch("agents.external_data._run_script")
    @patch("agents.external_data.load_user_feedback", return_value=[])
    @patch("agents.external_data.load_performance_review", return_value={"available": False})
    def test_crypto_signals_in_tasks(self, mock_perf, mock_fb, mock_run):
        """collect_all()에서 crypto_signals 스크립트가 호출된다."""
        mock_run.return_value = {}
        agent = ExternalDataAgent(snapshot_dir=None)
        result = agent.collect_all()

        # crypto_signals가 sources에 존재
        assert "crypto_signals" in result["sources"]

        # collect_crypto_signals.py가 호출됨을 확인
        script_calls = [
            call.args[0] for call in mock_run.call_args_list
        ]
        assert "collect_crypto_signals.py" in script_calls

    @patch("agents.external_data._run_script")
    @patch("agents.external_data.load_user_feedback", return_value=[])
    @patch("agents.external_data.load_performance_review", return_value={"available": False})
    def test_crypto_signals_error_isolated(self, mock_perf, mock_fb, mock_run):
        """crypto_signals 실패해도 다른 소스는 정상 수집된다."""
        def side_effect(script, args=None, timeout=60):
            if script == "collect_crypto_signals.py":
                return {"error": "API timeout"}
            return {"status": "ok"}

        mock_run.side_effect = side_effect
        agent = ExternalDataAgent(snapshot_dir=None)
        result = agent.collect_all()

        assert "crypto_signals" in result["errors"]
        # 다른 소스들은 정상
        assert "fear_greed" not in result["errors"]


# ── 2. _enhance_fusion: crypto_signals 점수 로직 ────────


class TestEnhanceFusionCryptoSignals:

    def test_btc_anomaly_high_positive_change(self, agent):
        """BTC anomaly HIGH + 양의 변화 -> +10점."""
        fusion = {"total_score": 0}
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "HIGH", "change_24h": 5.2},
            "anomaly_alerts": {"count": 0},
        })
        out = agent._enhance_fusion(fusion, results)
        assert out["extra_components"]["crypto_signals"]["score"] == 10

    def test_btc_anomaly_high_negative_change(self, agent):
        """BTC anomaly HIGH + 음의 변화 -> -10점."""
        fusion = {"total_score": 0}
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "HIGH", "change_24h": -3.1},
            "anomaly_alerts": {"count": 0},
        })
        out = agent._enhance_fusion(fusion, results)
        assert out["extra_components"]["crypto_signals"]["score"] == -10

    def test_btc_anomaly_critical_positive(self, agent):
        """CRITICAL도 HIGH와 동일하게 처리된다."""
        fusion = {"total_score": 0}
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "CRITICAL", "change_24h": 1.0},
            "anomaly_alerts": {"count": 0},
        })
        out = agent._enhance_fusion(fusion, results)
        assert out["extra_components"]["crypto_signals"]["score"] == 10

    def test_btc_anomaly_moderate_above_3pct(self, agent):
        """MODERATE + >3% 변화 -> +5점."""
        fusion = {"total_score": 0}
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "MODERATE", "change_24h": 4.5},
            "anomaly_alerts": {"count": 0},
        })
        out = agent._enhance_fusion(fusion, results)
        assert out["extra_components"]["crypto_signals"]["score"] == 5

    def test_btc_anomaly_moderate_negative_above_3pct(self, agent):
        """MODERATE + <-3% 변화 -> -5점."""
        fusion = {"total_score": 0}
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "MODERATE", "change_24h": -3.5},
            "anomaly_alerts": {"count": 0},
        })
        out = agent._enhance_fusion(fusion, results)
        assert out["extra_components"]["crypto_signals"]["score"] == -5

    def test_btc_anomaly_moderate_below_3pct(self, agent):
        """MODERATE + <=3% 변화 -> 0점 (미달)."""
        fusion = {"total_score": 0}
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "MODERATE", "change_24h": 2.0},
            "anomaly_alerts": {"count": 0},
        })
        out = agent._enhance_fusion(fusion, results)
        assert out["extra_components"]["crypto_signals"]["score"] == 0

    def test_btc_anomaly_low(self, agent):
        """BTC anomaly LOW -> 0점."""
        fusion = {"total_score": 0}
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "LOW", "change_24h": 1.5},
            "anomaly_alerts": {"count": 0},
        })
        out = agent._enhance_fusion(fusion, results)
        assert out["extra_components"]["crypto_signals"]["score"] == 0

    def test_missing_btc_data_no_crash(self, agent):
        """btc 데이터가 없어도 크래시하지 않는다."""
        fusion = {"total_score": 0}
        results = _make_results(crypto_signals={
            "anomaly_alerts": {"count": 0},
        })
        out = agent._enhance_fusion(fusion, results)
        assert out["extra_components"]["crypto_signals"]["score"] == 0

    def test_empty_crypto_signals_no_crash(self, agent):
        """crypto_signals가 빈 dict여도 크래시하지 않는다."""
        fusion = {"total_score": 0}
        results = _make_results(crypto_signals={})
        out = agent._enhance_fusion(fusion, results)
        assert out["extra_components"]["crypto_signals"]["score"] == 0

    def test_change_24h_none_treated_as_zero(self, agent):
        """change_24h가 None이면 0으로 처리된다."""
        fusion = {"total_score": 0}
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "HIGH", "change_24h": None},
            "anomaly_alerts": {"count": 0},
        })
        out = agent._enhance_fusion(fusion, results)
        # None -> 0 -> negative path (0 is not > 0)
        assert out["extra_components"]["crypto_signals"]["score"] == -10


# ── 3. _enhance_fusion: alert_count >= 30 메시지 ────────


class TestEnhanceFusionAlertCount:

    def test_alert_count_30_adds_detail(self, agent):
        """alert_count >= 30이면 변동성 경고 메시지가 추가된다."""
        fusion = {"total_score": 0}
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "LOW", "change_24h": 0},
            "anomaly_alerts": {"count": 30},
        })
        out = agent._enhance_fusion(fusion, results)
        details = out["extra_details"]
        assert any("CoinGecko" in d and "30" in d for d in details)

    def test_alert_count_50_adds_detail(self, agent):
        """alert_count 50에서도 경고 메시지가 포함된다."""
        fusion = {"total_score": 0}
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "LOW", "change_24h": 0},
            "anomaly_alerts": {"count": 50},
        })
        out = agent._enhance_fusion(fusion, results)
        details = out["extra_details"]
        assert any("시장 변동성 높음" in d for d in details)

    def test_alert_count_below_30_no_detail(self, agent):
        """alert_count < 30이면 변동성 경고 없음."""
        fusion = {"total_score": 0}
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "LOW", "change_24h": 0},
            "anomaly_alerts": {"count": 29},
        })
        out = agent._enhance_fusion(fusion, results)
        details = out["extra_details"]
        assert not any("CoinGecko" in d for d in details)


# ── 4. _inline_fusion: crypto_signals 점수 ──────────────


class TestInlineFusionCryptoSignals:

    def test_high_positive_adds_10(self, agent):
        """인라인 폴백에서도 HIGH + 양의 변화 -> +10."""
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "HIGH", "change_24h": 2.0},
        })
        out = agent._inline_fusion(results)
        # 다른 소스가 0이므로 total_score == 10
        assert out["total_score"] == 10

    def test_high_negative_subtracts_10(self, agent):
        """인라인 폴백에서 HIGH + 음의 변화 -> -10."""
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "HIGH", "change_24h": -1.0},
        })
        out = agent._inline_fusion(results)
        assert out["total_score"] == -10

    def test_moderate_above_3pct(self, agent):
        """인라인 폴백에서 MODERATE + >3% -> +5."""
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "MODERATE", "change_24h": 4.0},
        })
        out = agent._inline_fusion(results)
        assert out["total_score"] == 5

    def test_low_no_effect(self, agent):
        """인라인 폴백에서 LOW -> 점수 변화 없음."""
        results = _make_results(crypto_signals={
            "btc": {"anomaly_level": "LOW", "change_24h": 5.0},
        })
        out = agent._inline_fusion(results)
        assert out["total_score"] == 0

    def test_empty_crypto_signals(self, agent):
        """인라인 폴백에서 crypto_signals 빈 dict -> 점수 0."""
        results = _make_results(crypto_signals={})
        out = agent._inline_fusion(results)
        assert out["total_score"] == 0

    def test_missing_crypto_signals_key(self, agent):
        """results에 crypto_signals 키 자체가 없어도 동작."""
        results = _make_results()
        del results["crypto_signals"]
        out = agent._inline_fusion(results)
        assert out["total_score"] == 0


# ── 5. extra_components에 crypto_signals 필드 포함 ────────


class TestExtraComponentsCryptoSignals:

    def test_crypto_signals_field_present(self, agent):
        """extra_components에 crypto_signals 키가 존재한다."""
        fusion = {"total_score": 0}
        results = _make_results()
        out = agent._enhance_fusion(fusion, results)
        assert "crypto_signals" in out["extra_components"]

    def test_crypto_signals_has_score_and_max(self, agent):
        """crypto_signals 필드에 score와 max 키가 있다."""
        fusion = {"total_score": 0}
        results = _make_results()
        out = agent._enhance_fusion(fusion, results)
        cs = out["extra_components"]["crypto_signals"]
        assert "score" in cs
        assert cs["max"] == 10


# ── 6. ThreadPoolExecutor max_workers == 12 ──────────────


class TestThreadPoolWorkers:

    @patch("agents.external_data._run_script", return_value={})
    @patch("agents.external_data.load_user_feedback", return_value=[])
    @patch("agents.external_data.load_performance_review", return_value={"available": False})
    @patch("agents.external_data.ThreadPoolExecutor")
    def test_max_workers_is_12(self, mock_pool_cls, mock_perf, mock_fb, mock_run):
        """ThreadPoolExecutor가 max_workers=12로 생성된다 (I/O 병렬화 최적화)."""
        # Mock context manager
        mock_pool = MagicMock()
        mock_pool.__enter__ = MagicMock(return_value=mock_pool)
        mock_pool.__exit__ = MagicMock(return_value=False)
        mock_pool.submit.return_value = MagicMock()
        mock_pool_cls.return_value = mock_pool

        agent = ExternalDataAgent(snapshot_dir=None)
        # as_completed를 빈 리스트로 패치하여 루프 스킵
        with patch("agents.external_data.as_completed", return_value=[]):
            agent.collect_all()

        mock_pool_cls.assert_called_once_with(max_workers=12)
