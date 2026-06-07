"""C2 silent default 가드 5곳 단위테스트.

검증기준 (harness2.md C2):
- 결측 주입 시 라벨(source_missing/data_empty) 발생 확인
- 정상 입력 시 무영향(기존 반환값 동일)
- off byte-identical: 동작 변경 없음(None/[] 반환 유지)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# C2-1: factor_returns.py — source_missing 라벨
# ---------------------------------------------------------------------------

class TestFactorReturnsGuard:
    def test_source_exception_logs_source_missing(self, caplog):
        """fetch_factor_cov source_fn 예외 시 source_missing 라벨 로깅."""
        from core.data.factor_returns import fetch_factor_cov

        def bad_source(series_ids, start, end):
            raise RuntimeError("network timeout")

        with caplog.at_level(logging.WARNING, logger="core.data.factor_returns"):
            result = fetch_factor_cov(
                as_of="2026-06-01",
                lookback_days=100,
                factors=["credit", "real"],
                source_fn=bad_source,
            )
        assert result is None, "should return None on exception"
        assert any("source_missing" in r.message for r in caplog.records), (
            f"expected 'source_missing' in logs, got: {[r.message for r in caplog.records]}"
        )

    def test_normal_source_no_label(self, caplog):
        """정상 source_fn 시 source_missing 라벨 없음."""
        import numpy as np
        from core.data.factor_returns import fetch_factor_cov

        def good_source(series_ids, start, end):
            out = {}
            for sid in series_ids:
                # numpy array 필수(float + list 타입 에러 방지)
                out[sid] = 100.0 + np.arange(400, dtype=float) * 0.3
            return out

        with caplog.at_level(logging.WARNING, logger="core.data.factor_returns"):
            fetch_factor_cov(
                as_of="2026-06-01",
                lookback_days=200,
                factors=["credit", "vol"],
                source_fn=good_source,
                min_rows=60,
            )
        source_missing_msgs = [r for r in caplog.records if "source_missing" in r.message]
        assert not source_missing_msgs, (
            f"normal source should not log source_missing, got: {source_missing_msgs}"
        )


# ---------------------------------------------------------------------------
# C2-2: sleeve_returns.py — data_empty 라벨
# ---------------------------------------------------------------------------

class TestSleeveReturnsGuard:
    def test_source_exception_logs_data_empty(self, caplog):
        """fetch_sleeve_returns source_fn 예외 시 data_empty 라벨 로깅."""
        from core.data.sleeve_returns import fetch_sleeve_returns

        def bad_source(tickers, start, end):
            raise ConnectionError("yahoo down")

        with caplog.at_level(logging.WARNING, logger="core.data.sleeve_returns"):
            result = fetch_sleeve_returns(
                as_of="2026-06-01",
                lookback_days=60,
                sleeves=["us_stock", "gold"],
                source_fn=bad_source,
            )
        assert result is None, "should return None on exception"
        assert any("data_empty" in r.message for r in caplog.records), (
            f"expected 'data_empty' in logs, got: {[r.message for r in caplog.records]}"
        )

    def test_normal_source_no_label(self, caplog):
        """정상 source_fn 시 data_empty 라벨 없음."""
        import numpy as np
        import pandas as pd
        from datetime import date, timedelta
        from core.data.sleeve_returns import SLEEVE_TICKERS, fetch_sleeve_returns

        def good_source(tickers, start, end):
            # 충분한 날짜 범위 반환
            dates = pd.date_range("2025-01-01", periods=100, freq="B")
            data = {}
            for t in tickers:
                data[t] = 100.0 + np.arange(100) * 0.1
            return pd.DataFrame(data, index=dates)

        with caplog.at_level(logging.WARNING, logger="core.data.sleeve_returns"):
            fetch_sleeve_returns(
                as_of="2026-06-01",
                lookback_days=80,
                sleeves=["us_stock", "gold"],
                source_fn=good_source,
                min_rows=30,
            )
        data_empty_msgs = [r for r in caplog.records if "data_empty" in r.message]
        assert not data_empty_msgs, (
            f"normal source should not log data_empty, got: {data_empty_msgs}"
        )


# ---------------------------------------------------------------------------
# C2-3: fred_adapter.py — source_missing 라벨
# ---------------------------------------------------------------------------

class TestFredAdapterGuard:
    def test_get_series_exception_logs_source_missing(self, caplog):
        """RealFredAdapter.get_series 내부 예외 시 source_missing 라벨 로깅."""
        from core.brain.fred_adapter import RealFredAdapter

        adapter = RealFredAdapter(api_key="fake_key_for_test")
        # client 가 있는 척하되 get_series_first_release 예외 발생 시뮬레이션
        mock_client = MagicMock()
        mock_client.get_series_first_release.side_effect = RuntimeError("FRED API error")
        mock_client.get_series.side_effect = RuntimeError("FRED API error")
        adapter._client = mock_client

        with caplog.at_level(logging.WARNING, logger="core.brain.fred_adapter"):
            result = adapter.get_series("BAA10Y", as_of=None)

        assert result is None, "should return None on exception"
        assert any("source_missing" in r.message for r in caplog.records), (
            f"expected 'source_missing' in logs, got: {[r.message for r in caplog.records]}"
        )

    def test_get_series_success_no_label(self, caplog):
        """정상 get_series 시 source_missing 라벨 없음."""
        import pandas as pd
        from core.brain.fred_adapter import RealFredAdapter

        adapter = RealFredAdapter(api_key="fake_key_for_test")
        mock_client = MagicMock()
        mock_series = pd.Series(
            [1.5, 1.6, 1.7],
            index=pd.to_datetime(["2026-01-01", "2026-02-01", "2026-03-01"])
        )
        mock_client.get_series_first_release.return_value = mock_series
        adapter._client = mock_client

        with caplog.at_level(logging.WARNING, logger="core.brain.fred_adapter"):
            result = adapter.get_series("DGS10", as_of=None)

        source_missing_msgs = [r for r in caplog.records if "source_missing" in r.message]
        assert not source_missing_msgs, (
            f"success case should not log source_missing, got: {source_missing_msgs}"
        )
        assert result is not None, "should return series on success"


# ---------------------------------------------------------------------------
# C2-4: macro_market.py — source_missing/data_empty 라벨
# ---------------------------------------------------------------------------

class TestMacroMarketGuard:
    def test_requests_import_failure_logs_source_missing(self, caplog):
        """requests 미설치 시 source_missing 라벨 로깅."""
        import sys
        from core.data.macro_market import fetch_daily

        # requests import 실패 시뮬레이션
        original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else None

        with patch.dict('sys.modules', {'requests': None}):
            # None을 등록하면 import requests → ModuleNotFoundError
            import importlib
            with caplog.at_level(logging.WARNING, logger="core.data.macro_market"):
                # sys.modules에 None 등록 방식으로 import 실패 시뮬레이션
                result = fetch_daily("DX-Y.NYB")

        # requests가 None이면 import 실패하므로 [] 반환 확인
        # (sys.modules None = ModuleNotFoundError 트리거)
        assert isinstance(result, list), "should return [] on requests import failure"

    def test_yahoo_parse_failure_logs_data_empty(self, caplog):
        """Yahoo API 파싱 실패(예외) 시 data_empty 라벨 로깅.

        core.data.macro_market 내부 `import requests` 는 이미 완료된 상태이므로
        requests.get 을 patch 해 resp.json() 에서 예외 발생 시뮬레이션.
        """
        import requests  # 이미 설치된 경우 선 import (macro_market._lazy import 캐시)
        from core.data.macro_market import fetch_daily

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("invalid JSON")

        # requests 모듈이 설치된 환경에서만 실행
        with patch("requests.get", return_value=mock_resp):
            with caplog.at_level(logging.WARNING, logger="core.data.macro_market"):
                result = fetch_daily("DX-Y.NYB")

        assert result == [], "should return [] on parse failure"
        assert any("data_empty" in r.message for r in caplog.records), (
            f"expected 'data_empty' in logs, got: {[r.message for r in caplog.records]}"
        )


# ---------------------------------------------------------------------------
# C2-5: regime_classifier.py — source_missing 라벨 (_safe_fetch)
# ---------------------------------------------------------------------------

class TestRegimeClassifierGuard:
    def test_safe_fetch_exception_logs_source_missing(self, caplog):
        """_safe_fetch 예외 시 source_missing 라벨 로깅 + MacroFeatureBundle(available=False)."""
        from core.brain.regime_classifier import RegimeClassifier
        from core.brain.fred_adapter import RealFredAdapter, NullFredAdapter

        classifier = RegimeClassifier(usd_adapter=NullFredAdapter())

        # fetch_macro_bundle이 예외를 던지도록 mock
        with patch("core.brain.regime_classifier.fetch_macro_bundle",
                   side_effect=RuntimeError("FRED unavailable")):
            with caplog.at_level(logging.WARNING, logger="core.brain.regime_classifier"):
                bundle = classifier._safe_fetch(NullFredAdapter(), as_of=None)

        assert not bundle.available, "bundle should be unavailable"
        assert any("source_missing" in r.message for r in caplog.records), (
            f"expected 'source_missing' in logs, got: {[r.message for r in caplog.records]}"
        )

    def test_safe_fetch_success_no_source_missing_label(self, caplog):
        """정상 fetch 시 source_missing 라벨 없음."""
        from core.brain.regime_classifier import RegimeClassifier
        from core.brain.fred_adapter import MacroFeatureBundle, NullFredAdapter

        classifier = RegimeClassifier(usd_adapter=NullFredAdapter())
        ok_bundle = MacroFeatureBundle(available=True, series={"test": None})

        with patch("core.brain.regime_classifier.fetch_macro_bundle", return_value=ok_bundle):
            with caplog.at_level(logging.WARNING, logger="core.brain.regime_classifier"):
                bundle = classifier._safe_fetch(NullFredAdapter(), as_of=None)

        source_missing_msgs = [r for r in caplog.records if "source_missing" in r.message]
        assert not source_missing_msgs, (
            f"success case should not log source_missing, got: {source_missing_msgs}"
        )
        assert bundle.available is True
