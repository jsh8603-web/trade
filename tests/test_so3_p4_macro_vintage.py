"""tests/test_so3_p4_macro_vintage.py — SO-3/P4 FRED ALFRED vintage PIT 검증.

검증 기준 (harness2.md SO-3):
1. realtime_* 로 as_of vintage 반환 PASS
2. 미래 realtime(as_of 이후) 거부 (lookahead 차단)
3. 같은 시리즈 vintage 차이 반영 (as_of 다르면 다른 값)
4. credential 부재 시 None + 이연 박제 (blocked 아님)
5. ECOS stub 경계 PASS
6. FredAdapterBridge → core/brain/fred_adapter 연계 경계 미변경
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

import pandas as pd


# ---------------------------------------------------------------------------
# 1. credential 부재 → None + 이연 (deferral-pinning)
# ---------------------------------------------------------------------------

def test_no_api_key_returns_none():
    """FRED_API_KEY 없으면 get_vintage → None (blocked 아님)."""
    from stock.data.macro_vintage import MacroVintageProvider
    provider = MacroVintageProvider(api_key="")
    result = provider.get_vintage("GDPC1", datetime(2023, 1, 1))
    assert result is None


def test_is_available_without_key_false():
    """API key 없으면 is_available() → False."""
    from stock.data.macro_vintage import MacroVintageProvider
    provider = MacroVintageProvider(api_key="")
    assert provider.is_available() is False


# ---------------------------------------------------------------------------
# 2. 미래 realtime 거부 (lookahead 차단)
# ---------------------------------------------------------------------------

def test_future_as_of_rejected():
    """미래 as_of → None (lookahead 차단)."""
    from stock.data.macro_vintage import MacroVintageProvider
    provider = MacroVintageProvider(api_key="DUMMY")
    future = datetime(2099, 1, 1)
    with patch.object(provider, "_ensure_client", return_value=MagicMock()):
        result = provider.get_vintage("GDPC1", future)
    assert result is None


# ---------------------------------------------------------------------------
# 3. stub transport — realtime_start/end 파라미터 전달 검증
# ---------------------------------------------------------------------------

def _make_fred_client(val: float = 3.5) -> MagicMock:
    mock_client = MagicMock()
    mock_series = pd.Series([val], index=[pd.Timestamp("2023-01-01")])
    mock_client.get_series.return_value = mock_series
    return mock_client


def test_vintage_uses_realtime_params():
    """get_vintage → fredapi get_series 에 realtime_start=realtime_end=as_of_date 전달."""
    from stock.data.macro_vintage import MacroVintageProvider
    provider = MacroVintageProvider(api_key="DUMMY")
    mock_client = _make_fred_client(3.5)

    with patch.object(provider, "_ensure_client", return_value=mock_client):
        result = provider.get_vintage("GDPC1", datetime(2022, 6, 30))

    mock_client.get_series.assert_called_once_with(
        "GDPC1",
        realtime_start="2022-06-30",
        realtime_end="2022-06-30",
    )
    assert result == pytest.approx(3.5)


def test_vintage_different_as_of_different_value():
    """같은 시리즈, 다른 as_of → 다른 vintage 값 (lookahead 차단 검증)."""
    from stock.data.macro_vintage import MacroVintageProvider
    provider = MacroVintageProvider(api_key="DUMMY")

    # as_of=2022-01-01 → val=1.0
    client1 = _make_fred_client(1.0)
    with patch.object(provider, "_ensure_client", return_value=client1):
        val1 = provider.get_vintage("GDPC1", datetime(2022, 1, 1))

    # as_of=2023-01-01 → val=2.0
    client2 = _make_fred_client(2.0)
    with patch.object(provider, "_ensure_client", return_value=client2):
        val2 = provider.get_vintage("GDPC1", datetime(2023, 1, 1))

    assert val1 == pytest.approx(1.0)
    assert val2 == pytest.approx(2.0)
    assert val1 != val2


def test_vintage_empty_series_returns_none():
    """빈 시리즈 → None 반환 (안전 처리)."""
    from stock.data.macro_vintage import MacroVintageProvider
    provider = MacroVintageProvider(api_key="DUMMY")
    mock_client = MagicMock()
    mock_client.get_series.return_value = pd.Series([], dtype=float)

    with patch.object(provider, "_ensure_client", return_value=mock_client):
        result = provider.get_vintage("GDPC1", datetime(2020, 1, 1))
    assert result is None


def test_vintage_network_error_returns_none():
    """네트워크 에러 → None 반환 (예외 전파 X)."""
    from stock.data.macro_vintage import MacroVintageProvider
    provider = MacroVintageProvider(api_key="DUMMY")
    mock_client = MagicMock()
    mock_client.get_series.side_effect = Exception("network timeout")

    with patch.object(provider, "_ensure_client", return_value=mock_client):
        result = provider.get_vintage("GDPC1", datetime(2022, 6, 1))
    assert result is None


# ---------------------------------------------------------------------------
# 4. get_vintage_series — end > today 자동 클램프
# ---------------------------------------------------------------------------

def test_vintage_series_clamps_future_end():
    """future end → 오늘로 클램프 후 호출."""
    from stock.data.macro_vintage import MacroVintageProvider
    from datetime import date, timedelta

    provider = MacroVintageProvider(api_key="DUMMY")
    mock_client = _make_fred_client()

    with patch.object(provider, "_ensure_client", return_value=mock_client):
        provider.get_vintage_series(
            "GDPC1",
            start=datetime(2020, 1, 1),
            end=datetime(2099, 1, 1),  # 미래
        )

    called_end = mock_client.get_series.call_args[1]["realtime_end"]
    called_date = datetime.strptime(called_end, "%Y-%m-%d").date()
    assert called_date <= date.today()


# ---------------------------------------------------------------------------
# 5. ECOS stub — credential 부재
# ---------------------------------------------------------------------------

def test_ecos_stub_no_key():
    """ECOS_API_KEY 없으면 is_available() → False."""
    from stock.data.macro_vintage import EcosVintageStub
    stub = EcosVintageStub(api_key="")
    assert stub.is_available() is False


def test_ecos_stub_get_vintage_none_without_key():
    """ECOS key 없으면 get_vintage → None."""
    from stock.data.macro_vintage import EcosVintageStub
    stub = EcosVintageStub(api_key="")
    result = stub.get_vintage("722Y001/A", datetime(2023, 1, 1))
    assert result is None


# ---------------------------------------------------------------------------
# 6. FredAdapterBridge — core/brain/fred_adapter 경계 미변경 확인
# ---------------------------------------------------------------------------

def test_fred_adapter_bridge_delegates_to_vintage():
    """FredAdapterBridge.get_pit_value → MacroVintageProvider.get_vintage 위임."""
    from stock.data.macro_vintage import FredAdapterBridge, MacroVintageProvider

    mock_provider = MagicMock(spec=MacroVintageProvider)
    mock_provider.get_vintage.return_value = 4.8

    bridge = FredAdapterBridge(vintage_provider=mock_provider)
    result = bridge.get_pit_value("GDPC1", datetime(2022, 9, 1))

    mock_provider.get_vintage.assert_called_once_with("GDPC1", datetime(2022, 9, 1))
    assert result == pytest.approx(4.8)


def test_core_fred_adapter_import_unchanged():
    """core/brain/fred_adapter.py 본체 import — 미변경 확인."""
    from core.brain.fred_adapter import RealFredAdapter, NullFredAdapter, FredAdapter
    # 계약 필드 확인
    null = NullFredAdapter()
    assert null.is_available() is False
    assert null.get_series("GDPC1") is None
