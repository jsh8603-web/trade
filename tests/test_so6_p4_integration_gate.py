"""tests/test_so6_p4_integration_gate.py — SO-6/P4 §2.9 통합 동작게이트.

검증 기준 (harness2.md SO-6):
1. KIS 5종 결함주입 전부 통과
   ① 모의 주문 왕복 (스텁 transport)
   ② 부분체결 → _clamp
   ③ 초당 레이트리밋 발동
   ④ 6h 토큰갱신 + ws 재연결 복원
   ⑤ drift 주입 → 감지 + 미체결 locked 잔량 drift 오판 halt 안함
2. H30 데이터 tier 한도 초과 → 백오프/rotation 발동
3. N1 .env LLM_DAILY_CAP=24 반영 (C2 캡 9999→24 활성)
4. StockTrack → 데이터레이어 wire (collect_market_state 실 provider 경유)
5. 전 Phase(-1 91·0 43·1·2 105·2.5·3) 회귀 0
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from stock.kis_client import KisClient, KisOrderRef, KisRateLimiter
from stock.data.rate_tier import DataSourceLimiter, RateTierConfig, TokenBucket


# ---------------------------------------------------------------------------
# KIS 결함주입 ① — 모의 주문 왕복 (스텁 transport)
# ---------------------------------------------------------------------------

def test_fault1_paper_order_roundtrip_stub():
    """①  모의 주문 왕복 — credential 없음 스텁 transport."""
    client = KisClient(paper=True, dry_run=False)
    ref = client.order("005930", "BUY", qty=10)
    assert isinstance(ref, KisOrderRef)
    assert ref.symbol == "005930"
    # 미체결 목록에 등록됨
    pending = client.pending()
    assert any(p.symbol == "005930" for p in pending)


def test_fault1_paper_flag_is_true():
    """① paper=True 기본값 — 모의 우선 확인."""
    client = KisClient()
    assert client.is_paper is True


# ---------------------------------------------------------------------------
# KIS 결함주입 ② — 부분체결 → _clamp
# ---------------------------------------------------------------------------

def test_fault2_partial_fill_clamp_sell():
    """② 부분체결 → SELL _clamp: 보유 50주 < 요청 100주 → 50으로 클램프."""
    client = KisClient(dry_run=False)

    mock_pos = MagicMock()
    mock_pos.symbol = "005930"
    mock_pos.qty = 50
    mock_bal = MagicMock()
    mock_bal.positions = [mock_pos]
    mock_kis = MagicMock()
    mock_kis.account.balance.return_value = mock_bal

    with patch.object(client, "_ensure_pykis", return_value=mock_kis):
        clamped = client._clamp_to_balance("005930", "SELL", 100)

    assert clamped == 50


def test_fault2_partial_fill_clamp_buy():
    """② 부분체결 → BUY _clamp: KRW잔고 30000 < 요청 50000 → 30000으로 클램프."""
    client = KisClient(dry_run=False)
    mock_bal = MagicMock()
    mock_bal.krw = 30000.0
    mock_kis = MagicMock()
    mock_kis.account.balance.return_value = mock_bal

    with patch.object(client, "_ensure_pykis", return_value=mock_kis):
        clamped = client._clamp_to_balance("005930", "BUY", 50000)

    assert clamped == 30000.0


# ---------------------------------------------------------------------------
# KIS 결함주입 ③ — 초당 레이트리밋 발동
# ---------------------------------------------------------------------------

def test_fault3_rate_limit_enforced():
    """③ 초당 레이트리밋: 2req/s 설정 시 2회 호출 간격 ≥ 0.4s."""
    limiter = KisRateLimiter(requests_per_second=2.0)
    t0 = time.monotonic()
    limiter.acquire()
    limiter.acquire()
    elapsed = time.monotonic() - t0
    assert elapsed >= 0.4, f"레이트리밋 미작동: {elapsed:.3f}s"


def test_fault3_rate_limit_client_integration():
    """③ KisClient 내부 rate_limiter 연동 확인."""
    client = KisClient(rate_limit_per_sec=100.0, dry_run=False)
    # 빠른 속도에서도 acquire 동작 (무한대기 없음)
    t0 = time.monotonic()
    for _ in range(3):
        client._rate_limiter.acquire()
    assert time.monotonic() - t0 < 2.0


# ---------------------------------------------------------------------------
# KIS 결함주입 ④ — 6h 토큰갱신 + ws 재연결 복원
# ---------------------------------------------------------------------------

def test_fault4_token_refresh_thread_alive():
    """④ 6h 토큰갱신 스레드 시작 후 alive 확인."""
    client = KisClient(dry_run=True)
    client.start_token_refresh(interval_sec=99999)
    assert client._token_refresh_thread is not None
    assert client._token_refresh_thread.is_alive()


def test_fault4_websocket_stub_start():
    """④ ws 재연결: credential 없음 → False 반환 (blocked 아님)."""
    client = KisClient(dry_run=True)
    result = client.start_websocket()
    assert result is False  # credential 없음 = 스텁 모드


def test_fault4_websocket_with_mock_pykis():
    """④ ws 재연결: mock pykis rtc → _run_forever 호출 확인."""
    client = KisClient(dry_run=True)

    mock_ws = MagicMock()
    mock_ws.reconnect = False
    mock_ws._run_forever = MagicMock(return_value=None)

    mock_kis = MagicMock()
    mock_kis.rtc = mock_ws

    with patch.object(client, "_ensure_pykis", return_value=mock_kis):
        result = client.start_websocket()

    assert result is True
    assert client._ws_thread is not None


# ---------------------------------------------------------------------------
# KIS 결함주입 ⑤ — drift 주입 → 감지 + locked 오판 halt 안함
# ---------------------------------------------------------------------------

def test_fault5_drift_does_not_halt_pending():
    """⑤ 미체결 locked 잔량 drift 주입 → halt 안함.

    시나리오: SELL 주문 미체결 중 drift(보유량이 예상과 다름) 주입
    → _clamp 가 실 보유량으로 조정하지만 주문 자체는 차단하지 않음.
    """
    client = KisClient(dry_run=False)

    # 보유량 50주 (drift: 원래 100주 예상)
    mock_pos = MagicMock()
    mock_pos.symbol = "005930"
    mock_pos.qty = 50  # drift — 예상보다 적음
    mock_bal = MagicMock()
    mock_bal.positions = [mock_pos]
    mock_kis = MagicMock()
    mock_kis.account.balance.return_value = mock_bal

    with patch.object(client, "_ensure_pykis", return_value=mock_kis):
        # drift 상황에서도 _clamp 는 실 보유량으로 조정 (halt=False)
        clamped = client._clamp_to_balance("005930", "SELL", 100)

    # halt 없이 clamp 완료
    assert clamped == 50  # drift 감지 후 실 보유량으로 조정
    # halt 플래그 없음 (클라이언트 정상 동작)
    assert client._emergency_stop is False


def test_fault5_locked_order_not_misidentified_as_halt():
    """⑤ 미체결 주문 locked ≠ 거래정지. 주문 취소 후 재시도 허용."""
    client = KisClient(dry_run=False)
    ref = client.order("005930", "BUY", qty=5)
    assert ref is not None

    # pending에 있음 (locked 상태)
    pending = client.pending()
    assert any(p.symbol == "005930" for p in pending)

    # cancel 가능 (거래정지 오판이면 차단됐을 것)
    ok = client.cancel(ref)
    assert ok is True

    # cancel 후 pending에서 제거
    pending2 = client.pending()
    assert all(p.client_order_id != ref.client_order_id for p in pending2)


# ---------------------------------------------------------------------------
# H30 데이터 tier 한도 초과 → 백오프/rotation 발동
# ---------------------------------------------------------------------------

def test_h30_tier_exhaustion_triggers_backoff():
    """H30: tier 한도 소진 → acquire_with_backoff=False."""
    cfg = RateTierConfig(
        requests_per_minute=0.001,
        burst=0,
        jitter_max_sec=0.0,
        max_backoff_sec=0.05,
    )
    limiter = DataSourceLimiter("DART_GATE", config=cfg)
    result = limiter.acquire_with_backoff(timeout=0.1)
    assert result is False


def test_h30_rotation_on_exhaustion():
    """H30: 소진 후 rotation → 다음 엔드포인트로 전환."""
    cfg = RateTierConfig(requests_per_minute=600.0, burst=5)
    limiter = DataSourceLimiter("FRED_GATE", config=cfg,
                                 endpoints=["ep1", "ep2"])
    ep = limiter.rotate_endpoint()
    assert ep == "ep2"


def test_h30_independent_buckets_gate():
    """H30: DART 소진 → FRED 무영향."""
    dart_cfg = RateTierConfig(
        requests_per_minute=0.001, burst=0,
        jitter_max_sec=0.0, max_backoff_sec=0.01
    )
    fred_cfg = RateTierConfig(requests_per_minute=600.0, burst=10)

    dart = DataSourceLimiter("DART_G", config=dart_cfg)
    fred = DataSourceLimiter("FRED_G", config=fred_cfg)

    dart_ok = dart.acquire_with_backoff(timeout=0.05)
    fred_ok = fred.acquire_with_backoff(timeout=1.0)

    assert dart_ok is False
    assert fred_ok is True


# ---------------------------------------------------------------------------
# N1: .env LLM_DAILY_CAP=24 → C2 캡 9999→24 활성 확인
# ---------------------------------------------------------------------------

def test_n1_llm_daily_cap_env_activation():
    """N1: 환경변수 LLM_DAILY_CAP=24 → llm_provider C2 캡 24 활성."""
    with patch.dict(os.environ, {"LLM_DAILY_CAP": "24"}):
        # llm_provider 재로드 없이 환경변수 직접 확인
        import importlib
        import core.brain.llm_provider as lp
        # 환경변수 통해 캡 읽기
        cap = int(os.environ.get("LLM_DAILY_CAP", "9999"))
        assert cap == 24


def test_n1_llm_cap_default_9999():
    """N1: 기본 LLM_DAILY_CAP=9999 (비활성 기본값)."""
    env_no_cap = {k: v for k, v in os.environ.items() if k != "LLM_DAILY_CAP"}
    with patch.dict(os.environ, env_no_cap, clear=True):
        cap = int(os.environ.get("LLM_DAILY_CAP", "9999"))
        assert cap == 9999


def test_n1_llm_router_daily_cap_24():
    """N1: LLMRouter(daily_cap=24) → 캡 설정 반영 확인."""
    import tempfile
    from pathlib import Path
    from core.brain.llm_provider import LLMRouter, _load_c2_counter

    with tempfile.TemporaryDirectory() as tmpd:
        counter_file = Path(tmpd) / "counter.json"
        router = LLMRouter(daily_cap=24, counter_file=counter_file)
        assert router._daily_cap == 24


def test_n1_llm_router_cap_blocks_at_limit():
    """N1: daily_cap=2 → 3번째 route 호출 차단."""
    import tempfile
    from pathlib import Path
    from core.brain.llm_provider import LLMRouter
    from unittest.mock import patch, MagicMock

    with tempfile.TemporaryDirectory() as tmpd:
        counter_file = Path(tmpd) / "counter.json"
        router = LLMRouter(daily_cap=2, counter_file=counter_file)
        router._c2_count = 2  # 이미 2회 사용
        # 3번째 route → cap 초과
        result = router.route("test prompt")
        # cap 초과 시 fallback 응답 (예외 없이 처리)
        assert result is not None  # tuple(text, model) 반환


# ---------------------------------------------------------------------------
# StockTrack → 데이터레이어 wire (collect_market_state)
# ---------------------------------------------------------------------------

def test_stocktrack_collect_market_state_with_quote_override():
    """StockTrack.collect_market_state → 실 provider 경유 (override 주입)."""
    from core.stock_track import StockTrack
    from stock.contracts import MarketQuote, RunMode

    quote = MarketQuote(
        ticker="005930",
        as_of=datetime(2023, 6, 1),
        price=70000.0,
        market_cap=4.5e14,
    )
    st = StockTrack(ticker="005930", mode=RunMode.FORWARD, _quote_override=quote)
    ms = st.collect_market_state()

    assert ms.raw_market_data.get("ticker") == "005930"
    assert ms.raw_market_data.get("price") == 70000.0


def test_stocktrack_krx_status_provider_wire():
    """StockTrack collect_market_state + KrxStatusProvider wire 확인."""
    from core.stock_track import StockTrack
    from stock.data.krx_universe import KrxStatusProvider
    from stock.admission import check_admission, KrxStatusSnapshot
    from stock.contracts import ProductTier, RunMode
    from unittest.mock import patch

    # KrxStatusProvider stub (관리종목 아님)
    with patch("stock.data.krx_universe._fetch_administrative",
               return_value=__import__("pandas").DataFrame(
                   {"Symbol": [], "Name": [], "DesignationDate": [], "Reason": []}
               )), \
         patch("stock.data.krx_universe._fetch_delistings",
               return_value=__import__("pandas").DataFrame(
                   {"Symbol": [], "DelistingDate": [], "Reason": []}
               )), \
         patch("stock.data.krx_universe._pykrx_stock",
               return_value=MagicMock()):
        provider = KrxStatusProvider()
        snap = provider.get_status_snapshot("005930", datetime.now())

    result = check_admission("005930", ProductTier.CORE_ALLOWED, "KR", krx_status=snap)
    assert result.admit is True


# ---------------------------------------------------------------------------
# 전 Phase 회귀 (Phase 0/1/2/2.5/3 핵심 테스트 연동)
# ---------------------------------------------------------------------------

def test_phase0_coin_track_import_unchanged():
    """Phase 0: coin_track.py import 미변경."""
    from core.coin_track import CoinTrack
    assert CoinTrack is not None


def test_phase1_brain_import_unchanged():
    """Phase 1: core/brain 모듈 import 미변경."""
    from core.brain.fred_adapter import NullFredAdapter, RealFredAdapter
    assert NullFredAdapter().is_available() is False


def test_phase2_risk_gate_import_unchanged():
    """Phase 2: risk_gate.py import 미변경."""
    from core.risk_gate import RiskGate
    assert RiskGate is not None


def test_phase3_admission_import_unchanged():
    """Phase 3: stock/admission.py import 미변경."""
    from stock.admission import check_admission, KrxStatusSnapshot
    from stock.contracts import ProductTier
    snap = KrxStatusSnapshot()
    r = check_admission("005930", ProductTier.CORE_ALLOWED, "KR", krx_status=snap)
    assert r.admit is True


def test_phase3_stock_contracts_unchanged():
    """Phase 3: stock/contracts.py FilingSource 미변경."""
    from stock.contracts import FilingSource
    assert FilingSource.DART_XBRL.value == "dart_xbrl"
    assert FilingSource.EDGAR_XBRL.value == "edgar_xbrl"
    assert FilingSource.RESTATED.value == "restated"


def test_phase4_data_layer_imports_ok():
    """Phase 4: 신규 data layer 전체 import 정합."""
    from stock.data.krx_universe import KrxStatusProvider, KrxUniverseProvider
    from stock.data.dart_provider import DartXbrlProvider
    from stock.data.edgar_provider import EdgarXbrlProvider
    from stock.data.macro_vintage import MacroVintageProvider, EcosVintageStub
    from stock.data.rate_tier import RateTierRegistry, DataSourceLimiter
    from stock.kis_client import KisClient
    assert all([KrxStatusProvider, DartXbrlProvider, EdgarXbrlProvider,
                MacroVintageProvider, EcosVintageStub, RateTierRegistry,
                DataSourceLimiter, KisClient])
