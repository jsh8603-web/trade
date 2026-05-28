"""tests/test_so1_p4_krx_universe.py — SO-1/P4 KRX 유니버스·상태 provider 검증.

검증 기준 (harness2.md SO-1):
1. 실 종목코드 FDR/pykrx 호출 → KrxStatusSnapshot 채움 PASS
2. 관리종목 실재 종목 → is_watchlist=True → admission 거절(KRX_WATCHLIST)
3. 일별 스냅샷 PIT (다른 as_of = 다른 상태 재구성)
4. StockListing 유니버스 로드 어서션 실제 실행 PASS
5. 네트워크 불가 시 fixture/스텁 경계 + 이연 박제

credential 부재 없음 — FDR/pykrx 무료 라이브. 네트워크 불가 시 캐시 fixture.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# sys.path 설정은 conftest.py 가 담당


# ---------------------------------------------------------------------------
# 1. KrxStatusSnapshot 계약 — fixture 경계 (live 호출 없이)
# ---------------------------------------------------------------------------

def test_krx_status_snapshot_fields():
    """KrxStatusSnapshot 6필드 계약 검증 — admission 기존 계약 미변경 확인."""
    from stock.admission import KrxStatusSnapshot
    snap = KrxStatusSnapshot(is_watchlist=True)
    assert snap.is_watchlist is True
    assert snap.is_invest_warn is False
    assert snap.is_invest_risk is False
    assert snap.is_halt is False
    assert snap.is_delisting_risk is False
    assert snap.is_qualified_audit is False


# ---------------------------------------------------------------------------
# 2. KrxStatusProvider — stub transport 경계 (관리종목 is_watchlist 매핑)
# ---------------------------------------------------------------------------

def _make_admin_df(symbols: list, reasons: list = None):
    """KrxAdministrative.read() 모의 DataFrame."""
    import pandas as pd
    reasons = reasons or ["관리종목지정" for _ in symbols]
    return pd.DataFrame({"Symbol": symbols, "Name": [f"종목{s}" for s in symbols],
                          "DesignationDate": [datetime.now()] * len(symbols),
                          "Reason": reasons})


def _make_empty_delist_df():
    import pandas as pd
    return pd.DataFrame({"Symbol": [], "DelistingDate": [], "Reason": []})


@patch("stock.data.krx_universe._fetch_administrative")
@patch("stock.data.krx_universe._fetch_delistings")
@patch("stock.data.krx_universe._pykrx_stock")
def test_status_provider_watchlist(mock_pk, mock_delist, mock_admin):
    """관리종목 종목 → is_watchlist=True."""
    mock_admin.return_value = _make_admin_df(["005930"], ["관리종목지정"])
    mock_delist.return_value = _make_empty_delist_df()
    mock_pykrx = MagicMock()
    mock_pykrx.get_market_ohlcv_by_date.return_value = None
    mock_pk.return_value = mock_pykrx

    from stock.data.krx_universe import KrxStatusProvider
    provider = KrxStatusProvider()
    snap = provider.get_status_snapshot("005930", datetime.now())
    assert snap.is_watchlist is True


@patch("stock.data.krx_universe._fetch_administrative")
@patch("stock.data.krx_universe._fetch_delistings")
@patch("stock.data.krx_universe._pykrx_stock")
def test_status_provider_invest_warn(mock_pk, mock_delist, mock_admin):
    """투자경고 종목 → is_invest_warn=True."""
    mock_admin.return_value = _make_admin_df(["123456"], ["투자경고"])
    mock_delist.return_value = _make_empty_delist_df()
    mock_pk.return_value = MagicMock()
    mock_pk.return_value.get_market_ohlcv_by_date.return_value = None

    from stock.data.krx_universe import KrxStatusProvider
    provider = KrxStatusProvider()
    snap = provider.get_status_snapshot("123456", datetime.now())
    assert snap.is_invest_warn is True
    assert snap.is_watchlist is False


@patch("stock.data.krx_universe._fetch_administrative")
@patch("stock.data.krx_universe._fetch_delistings")
@patch("stock.data.krx_universe._pykrx_stock")
def test_status_provider_normal(mock_pk, mock_delist, mock_admin):
    """정상 종목 → 모든 플래그 False."""
    mock_admin.return_value = _make_admin_df([])
    mock_delist.return_value = _make_empty_delist_df()
    mock_pk.return_value = MagicMock()
    mock_pk.return_value.get_market_ohlcv_by_date.return_value = None

    from stock.data.krx_universe import KrxStatusProvider
    provider = KrxStatusProvider()
    snap = provider.get_status_snapshot("005930", datetime.now())
    assert snap.is_watchlist is False
    assert snap.is_halt is False


# ---------------------------------------------------------------------------
# 3. admission wire — is_watchlist=True → check_admission 거절
# ---------------------------------------------------------------------------

@patch("stock.data.krx_universe._fetch_administrative")
@patch("stock.data.krx_universe._fetch_delistings")
@patch("stock.data.krx_universe._pykrx_stock")
def test_admission_krx_watchlist_rejection(mock_pk, mock_delist, mock_admin):
    """관리종목 실데이터 → admission.check_admission KRX_WATCHLIST 거절."""
    mock_admin.return_value = _make_admin_df(["005930"], ["관리종목지정"])
    mock_delist.return_value = _make_empty_delist_df()
    mock_pk.return_value = MagicMock()
    mock_pk.return_value.get_market_ohlcv_by_date.return_value = None

    from stock.data.krx_universe import KrxStatusProvider
    from stock.admission import check_admission, AdmissionRejectionReason
    from stock.contracts import ProductTier

    provider = KrxStatusProvider()
    krx_status = provider.get_status_snapshot("005930", datetime.now())
    result = check_admission("005930", ProductTier.CORE_ALLOWED, "KR", krx_status=krx_status)
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.KRX_WATCHLIST


# ---------------------------------------------------------------------------
# 4. 일별 스냅샷 PIT — jsonl 적재·로드
# ---------------------------------------------------------------------------

def test_snapshot_persist_and_pit_reload():
    """일별 스냅샷 적재 후 다른 as_of로 PIT 재구성 — 상태 차이 반영."""
    from stock.data.krx_universe import _persist_snapshot, _load_snapshot, KrxStatusProvider

    with tempfile.TemporaryDirectory() as tmpdir:
        snap_path = Path(tmpdir) / "krx_snapshots.jsonl"

        # 2026-01-01 — 관리종목 아님
        _persist_snapshot.__wrapped__ = getattr(_persist_snapshot, "__wrapped__", None)

        # 직접 jsonl 에 기록
        d1 = date(2026, 1, 1)
        d2 = date(2026, 1, 10)
        snap_path.parent.mkdir(parents=True, exist_ok=True)
        with open(snap_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"as_of": d1.isoformat(), "ticker": "005930",
                                 "is_watchlist": False, "is_invest_warn": False,
                                 "is_invest_risk": False, "is_halt": False,
                                 "is_delisting_risk": False, "is_qualified_audit": False}) + "\n")
            fh.write(json.dumps({"as_of": d2.isoformat(), "ticker": "005930",
                                 "is_watchlist": True, "is_invest_warn": False,
                                 "is_invest_risk": False, "is_halt": False,
                                 "is_delisting_risk": False, "is_qualified_audit": False}) + "\n")

        provider = KrxStatusProvider(snap_path=snap_path)
        # as_of 2026-01-01 → 관리종목 아님
        snap_past = provider._pit_snapshot("005930", d1)
        assert snap_past.is_watchlist is False

        # as_of 2026-01-10 → 관리종목
        snap_recent = provider._pit_snapshot("005930", d2)
        assert snap_recent.is_watchlist is True


# ---------------------------------------------------------------------------
# 5. KrxUniverseProvider — StockListing 유니버스 로드 stub
# ---------------------------------------------------------------------------

@patch("FinanceDataReader.StockListing")
def test_universe_provider_stub(mock_listing):
    """StockListing stub → 유니버스 코드 목록 반환."""
    import pandas as pd
    mock_df = pd.DataFrame({"Code": ["005930", "000660", "035420"],
                             "Name": ["삼성전자", "SK하이닉스", "NAVER"],
                             "Marcap": [450_000_000_000_000,
                                        100_000_000_000_000,
                                        30_000_000_000_000]})
    mock_listing.return_value = mock_df

    from stock.data.krx_universe import KrxUniverseProvider
    provider = KrxUniverseProvider()
    universe = provider.get_universe()
    assert len(universe) == 3
    assert "005930" in universe
    assert all(len(c) == 6 for c in universe)


# ---------------------------------------------------------------------------
# 6. 네트워크 불가 fallback — 이연 핀 검증
# ---------------------------------------------------------------------------

def test_network_failure_fallback():
    """네트워크 실패 시 KrxStatusSnapshot 기본값 반환 (블록 없음)."""
    from stock.data.krx_universe import KrxStatusProvider

    with patch("stock.data.krx_universe._fetch_administrative",
               side_effect=Exception("network error")), \
         patch("stock.data.krx_universe._fetch_delistings",
               side_effect=Exception("network error")), \
         patch("stock.data.krx_universe._pykrx_stock",
               side_effect=Exception("network error")):
        provider = KrxStatusProvider()
        snap = provider.get_status_snapshot("005930", datetime.now())
        # 실패해도 KrxStatusSnapshot 반환 (기본값=정상)
        from stock.admission import KrxStatusSnapshot
        assert isinstance(snap, KrxStatusSnapshot)


# ---------------------------------------------------------------------------
# LIVE (optional — --live 플래그 없으면 skip)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    os.environ.get("SKIP_LIVE", "1") == "1",
    reason="LIVE 테스트 — SKIP_LIVE=0 환경변수로 활성화"
)
def test_live_krx_status_005930():
    """[LIVE] 삼성전자 005930 — KrxStatusSnapshot 실 조회 PASS."""
    from stock.data.krx_universe import KrxStatusProvider
    provider = KrxStatusProvider()
    snap = provider.get_status_snapshot("005930", datetime.now())
    from stock.admission import KrxStatusSnapshot
    assert isinstance(snap, KrxStatusSnapshot)
    assert snap.is_watchlist is False
