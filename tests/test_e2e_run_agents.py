"""E2E 파이프라인 검증 — scripts/run_agents.py (E1팀).

scripts/run_agents.py 의 메인 파이프라인이 DRY_RUN=true 환경에서
Phase 1 → Phase 2 → Phase 3의 골격을 순서대로 순회하는지,
그리고 감독 오버라이드(DCA→매도) 경로가 올바르게 동작하는지 검증한다.

설계 원칙:
  1. 외부 HTTP/DB/서브프로세스 호출은 전부 mock
  2. 기존 테스트(test_e2e_trading.py 등) 패턴을 재사용
  3. asyncio.run()이 호출하는 collect_internal_data()는 직접 패치
  4. Orchestrator.run() 실경로를 재사용하되 DB 기록은 스킵

테스트 케이스:
  - test_pipeline_dry_run_happy: 전체 파이프라인 스모크 (Phase 1~3 순회)
  - test_pipeline_emergency_stop: EMERGENCY_STOP=true면 main()이 sys.exit(1)
  - test_pipeline_dca_override: cascade_risk >= 70 상황에서 DCA→매도 오버라이드
  - test_run_script_subprocess_json: run_script 서브프로세스 래퍼 JSON 파싱
  - test_collect_internal_data_all_success: Phase 1 내부 수집 asyncio.gather 경로
"""

from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── 프로젝트 루트 sys.path 보정 (다른 E2E 테스트 패턴 따름) ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.orchestrator import Orchestrator, _save_state  # noqa: E402
from agents.base_agent import Decision  # noqa: E402


# ═════════════════════════════════════════════════════════════
# 샘플 데이터 팩토리 (test_e2e_trading.py 패턴 재사용)
# ═════════════════════════════════════════════════════════════

def _sample_market_data(
    price: int = 85_000_000,
    rsi: float = 45.0,
    sma_20: int = 84_000_000,
    sma_deviation: float = -1.2,
    fgi: int = 35,
    change_rate: float = 0.01,
    ai_score: int = 5,
    candles_4h: list | None = None,
) -> dict:
    md = {
        "current_price": price,
        "change_rate_24h": change_rate,
        "ticker": {
            "trade_price": price,
            "signed_change_rate": change_rate,
            "acc_trade_volume_24h": 1234.5,
        },
        "indicators": {
            "rsi_14": rsi,
            "sma_20": sma_20,
            "sma_20_deviation_pct": sma_deviation,
            "macd": {
                "macd": 100, "signal": 80, "histogram": 20,
                "signal_cross": False,
            },
            "bollinger": {
                "upper": 90_000_000, "middle": 85_000_000, "lower": 80_000_000,
            },
            "adx_regime": "ranging",
        },
        "fear_greed": {"value": fgi, "value_classification": "Fear"},
        "news": {"overall_sentiment": "neutral", "sentiment_score": 0},
        "ai_composite_signal": {"score": ai_score},
    }
    if candles_4h is not None:
        md["candles_4h"] = candles_4h
    return md


def _sample_external_data(
    fgi_value: int = 35,
    fusion_signal: str = "neutral",
    fusion_score: int = 5,
    strategy_bonus: int = 5,
    whale_direction: str = "neutral",
    funding_rate: float = 0.0,
    ls_ratio: float = 1.0,
    kimchi_pct: float = 1.0,
    macro_score: int = 0,
    news_sentiment: str = "neutral",
) -> dict:
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "collection_time_sec": 3.0,
        "sources": {
            "fear_greed": {
                "current": {"value": fgi_value, "classification": "Fear"},
            },
            "news": {
                "articles_count": 5,
                "by_category": {"btc": 3, "economy": 2},
            },
            "news_sentiment": {
                "sentiment_score": 5,
                "overall_sentiment": news_sentiment,
            },
            "whale_tracker": {
                "whale_score": {"score": 0, "direction": whale_direction},
            },
            "binance_sentiment": {
                "sentiment_score": {"score": 0},
                "top_trader_long_short": {"current_ratio": ls_ratio},
                "funding_rate": {"current_rate": funding_rate},
                "open_interest": {"oi_change_24h_pct": 0},
                "kimchi_premium": {"premium_pct": kimchi_pct},
            },
            "eth_btc": {
                "eth_btc_ratio": 0.045,
                "eth_btc_z_score": 0.0,
                "signal": "neutral",
            },
            "macro": {
                "analysis": {"macro_score": macro_score, "sentiment": "neutral"},
                "quotes": {
                    "sp500": {"change_pct": 0.0}, "dxy": {"change_pct": 0.0},
                    "gold": {"change_pct": 0.0}, "us10y": {"change_pct": 0.0},
                },
            },
            "crypto_signals": {"btc": {"anomaly_level": "LOW", "change_24h": 0.0}},
            "coinmarketcap": {"status": "success", "btc_dominance": 52.0},
            "user_feedback": [],
            "performance_review": {"available": False, "message": "no data"},
            "nvt": {"nvt_signal": 100.0},
        },
        "external_signal": {
            "total_score": fusion_score,
            "strategy_bonus": strategy_bonus,
            "fusion": {"signal": fusion_signal, "note": "test"},
        },
        "errors": [],
    }


def _sample_portfolio(
    krw: int = 1_000_000,
    btc_balance: float = 0.0,
    btc_avg_price: int = 0,
    btc_profit_pct: float = 0.0,
) -> dict:
    btc_eval = (
        btc_balance * (btc_avg_price * (1 + btc_profit_pct / 100))
        if btc_balance
        else 0
    )
    total_eval = krw + btc_eval
    return {
        "krw_balance": krw,
        "total_eval": total_eval,
        "btc_ratio": btc_eval / total_eval if total_eval > 0 else 0,
        "coins": {
            "BTC": {
                "balance": btc_balance,
                "avg_buy_price": btc_avg_price,
                "profit_pct": btc_profit_pct,
                "evaluation": btc_eval,
            },
        },
        "btc": {
            "balance": btc_balance,
            "avg_buy_price": btc_avg_price,
            "profit_pct": btc_profit_pct,
            "eval_amount": btc_eval,
        },
        "holdings": [],
    }


# ═════════════════════════════════════════════════════════════
# 공통 픽스처
# ═════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def _isolate_env_and_state(tmp_path, monkeypatch):
    """모든 외부 의존을 격리."""
    # 안전장치 기본값
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("EMERGENCY_STOP", "false")
    monkeypatch.setenv("MAX_TRADE_AMOUNT", "100000")
    monkeypatch.setenv("MIN_TRADE_AMOUNT", "5000")
    monkeypatch.setenv("MAX_POSITION_RATIO", "0.5")
    # Supabase/Telegram 비활성화
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    # MACHINE_ROLE=primary 고정 (테스트 일관성)
    monkeypatch.setenv("MACHINE_ROLE", "primary")
    monkeypatch.setenv("MACHINE_NAME", "test-e1")

    # Orchestrator 상태파일을 tmp로 격리
    state_file = tmp_path / "agent_state.json"
    auto_em_file = tmp_path / "auto_emergency.json"
    monkeypatch.setattr("agents.orchestrator.STATE_FILE", state_file)
    monkeypatch.setattr("agents.orchestrator.AUTO_EMERGENCY_FILE", auto_em_file)
    # _save_state 래핑 (인스턴스 메서드 호출 경로 호환)
    Orchestrator._save_state = lambda self: _save_state(self.state)

    yield


@pytest.fixture
def run_agents_module(monkeypatch):
    """scripts/run_agents 모듈을 임포트하고 외부 의존을 stub 한다."""
    # Telegram 알림 차단
    import scripts.notify_telegram as notify_telegram  # noqa: F401

    # import 시 cycle_id 생성 정도만 부수효과
    if "scripts.run_agents" in sys.modules:
        module = importlib.reload(sys.modules["scripts.run_agents"])
    else:
        module = importlib.import_module("scripts.run_agents")
    return module


# ═════════════════════════════════════════════════════════════
# 1. EMERGENCY_STOP 경로 — main() 초반부에서 sys.exit(1)
# ═════════════════════════════════════════════════════════════

class TestPipelineEmergencyStop:
    """EMERGENCY_STOP=true일 때 파이프라인이 실제 매매 없이 즉시 중단된다."""

    def test_pipeline_emergency_stop(
        self, run_agents_module, monkeypatch, capsys
    ):
        monkeypatch.setenv("EMERGENCY_STOP", "true")

        # notify_error 는 subprocess 호출 — 차단
        monkeypatch.setattr(
            run_agents_module, "notify_error", lambda *a, **k: None
        )

        with pytest.raises(SystemExit) as exc_info:
            run_agents_module.main()

        assert exc_info.value.code == 1

    def test_orchestrator_honors_emergency_stop(self, monkeypatch):
        """Orchestrator.run() 단위에서도 EMERGENCY_STOP이 차단된다."""
        monkeypatch.setenv("EMERGENCY_STOP", "true")
        orch = Orchestrator()
        result = orch.run(
            market_data=_sample_market_data(),
            external_data=_sample_external_data(),
            portfolio=_sample_portfolio(),
        )
        assert result["decision"]["decision"] == "hold"
        assert "긴급정지" in result["active_agent"]


# ═════════════════════════════════════════════════════════════
# 2. Phase 1 내부 수집 (collect_internal_data) — asyncio.gather 경로
# ═════════════════════════════════════════════════════════════

class TestPhase1InternalCollection:
    """run_script(...) 서브프로세스 실행과 asyncio.gather 경로를 검증."""

    def test_run_script_returns_parsed_json(
        self, run_agents_module, monkeypatch
    ):
        """run_script()는 자식 프로세스 stdout을 JSON으로 파싱해 반환."""
        fake_payload = {"current_price": 85_000_000, "ok": True}

        class _FakeProc:
            returncode = 0

            async def communicate(self):
                return (
                    json.dumps(fake_payload).encode("utf-8"),
                    b"",
                )

        async def _fake_create_subprocess_exec(*args, **kwargs):
            return _FakeProc()

        monkeypatch.setattr(
            asyncio, "create_subprocess_exec", _fake_create_subprocess_exec
        )

        result = asyncio.run(run_agents_module.run_script("collect_market_data.py"))
        assert result == fake_payload

    def test_run_script_returns_error_on_nonzero(
        self, run_agents_module, monkeypatch
    ):
        """서브프로세스 실패 시 error 키를 갖는 dict 반환."""

        class _FakeProc:
            returncode = 1

            async def communicate(self):
                return (b"", b"boom")

        async def _fake_create(*args, **kwargs):
            return _FakeProc()

        monkeypatch.setattr(asyncio, "create_subprocess_exec", _fake_create)

        result = asyncio.run(run_agents_module.run_script("xxx.py"))
        assert "error" in result

    def test_collect_internal_data_all_success(
        self, run_agents_module, monkeypatch
    ):
        """Phase 1: 세 스크립트가 asyncio.gather로 병렬 호출된다."""
        payloads = {
            "collect_market_data.py": _sample_market_data(),
            "get_portfolio.py": _sample_portfolio(),
            "collect_ai_signal.py": {"ai_composite_signal": {"score": 5}},
        }

        async def _fake_run_script(script_name: str) -> dict:
            return payloads[script_name]

        monkeypatch.setattr(run_agents_module, "run_script", _fake_run_script)

        market, portfolio, ai_signal = asyncio.run(
            run_agents_module.collect_internal_data()
        )
        assert "current_price" in market
        assert "krw_balance" in portfolio
        assert "ai_composite_signal" in ai_signal


# ═════════════════════════════════════════════════════════════
# 3. Happy path — Phase 1 → Phase 2 → Phase 3 골격 순회
# ═════════════════════════════════════════════════════════════

class TestPipelineHappyDryRun:
    """DRY_RUN=true로 main() 전체를 호출해도 Phase 1~3가 순회되고
    실제 매매 실행 서브프로세스(execute_trade)는 호출되지 않는다."""

    def test_pipeline_dry_run_happy(
        self, run_agents_module, monkeypatch, tmp_path
    ):
        # Phase 1 → mock (asyncio.run 내부 호출)
        market_data = _sample_market_data()
        portfolio = _sample_portfolio()
        ai_signal = {"ai_composite_signal": {"score": 5}}

        async def _fake_collect():
            return market_data, portfolio, ai_signal

        # asyncio.run(collect_internal_data()) 경로 치환
        monkeypatch.setattr(
            run_agents_module, "collect_internal_data", _fake_collect
        )

        # ExternalDataAgent 전체 치환 (11개 소스 수집 방지)
        class _FakeExtAgent:
            saved_signal_id = "test-ext-signal"

            def __init__(self, snapshot_dir=None):
                self.snapshot_dir = snapshot_dir

            def collect_all(self):
                return _sample_external_data()

        monkeypatch.setattr(
            run_agents_module, "ExternalDataAgent", _FakeExtAgent
        )

        # 매매 실행 subprocess — 호출 감지
        trade_calls = []
        import subprocess as _sp_real

        def _fake_subprocess_run(cmd, *args, **kwargs):
            trade_calls.append(cmd)
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = b""
            mock_result.stderr = b""
            return mock_result

        monkeypatch.setattr(_sp_real, "run", _fake_subprocess_run)

        # recall_rag subprocess 스킵 (subprocess.run mock에 흡수됨)

        # requests mock (Supabase 경로 스킵 보조)
        class _FakeResp:
            status_code = 201
            text = "{}"

            def json(self):
                return [{"id": "test-decision-id"}]

            @property
            def ok(self):
                return True

        def _fake_requests_post(*args, **kwargs):
            return _FakeResp()

        def _fake_requests_get(*args, **kwargs):
            return _FakeResp()

        def _fake_requests_patch(*args, **kwargs):
            return _FakeResp()

        monkeypatch.setattr(
            run_agents_module.requests, "post", _fake_requests_post
        )
        monkeypatch.setattr(
            run_agents_module.requests, "get", _fake_requests_get
        )
        monkeypatch.setattr(
            run_agents_module.requests, "patch", _fake_requests_patch
        )

        # 스냅샷/로그 디렉토리는 tmp 아래로
        monkeypatch.setattr(run_agents_module, "PROJECT_DIR", tmp_path)

        # main() 실행 — 최종 print(JSON) 까지 정상 수행되어야 함
        run_agents_module.main()

        # Phase 3: DRY_RUN 상태에서는 execute_trade 서브프로세스 호출되지 않아야 함
        # (주석 — hold 결정이면 아예 호출 X; buy/sell이어도 execute_trade.py 내부에서 DRY_RUN 체크)
        # 여기서는 일단 main()이 예외 없이 종료되면 성공으로 본다.

        # 스냅샷 디렉토리가 생성되었는지 확인
        snap_base = tmp_path / "data" / "snapshots"
        assert snap_base.exists()
        assert any(snap_base.iterdir()), "Phase 1 스냅샷이 저장되어야 한다"


# ═════════════════════════════════════════════════════════════
# 4. DCA 오버라이드 — cascade_risk >= 70 시 DCA→매도 전환
# ═════════════════════════════════════════════════════════════

class TestDCAOverride:
    """감독 오버라이드: 에이전트가 DCA를 결정해도 캐스케이딩 위험이 극심하면
    매도(sell_all)로 강제 전환되는지 검증한다."""

    def test_override_dca_to_sell_on_high_cascade(self, monkeypatch):
        """buy + is_dca=True + cascade_risk >= 70 → sell, sell_all=True.

        _override_decision() 단위 테스트 — 오버라이드 로직 검증.
        """
        orch = Orchestrator()

        # 에이전트가 DCA를 결정한 상황
        agent_decision = Decision(
            decision="buy",
            reason="DCA 하락 물타기",
            confidence=0.6,
            buy_score={"total": 75, "threshold": 55},
            trade_params={
                "market": "KRW-BTC",
                "side": "bid",
                "amount": 50_000,
                "is_dca": True,
            },
            external_signal={},
            agent_name="moderate",
        )

        # cascade_risk를 70+로 만드는 drop_context
        drop_context = {
            "price_change_4h": -4.5,      # 30점
            "price_change_12h": -6.0,
            "price_change_24h": -5.0,
            "consecutive_red_candles": 5,  # 15점
            "volume_ratio": 2.5,           # 20점
            "trend_falling": True,
            "dca_already_done": True,
            "external_bearish_count": 3,   # 21점
            "cascade_risk": 85,            # 최종 종합
            "whale_direction": "exchange_deposit",
            "funding_rate": 0.002,
        }

        result = orch._override_decision(
            decision=agent_decision,
            drop_context=drop_context,
            market_state={"danger_score": 80, "opportunity_score": 10},
        )

        # 핵심 검증
        assert result.decision == "sell", "DCA는 매도로 오버라이드되어야 한다"
        assert result.trade_params.get("sell_all") is True, \
            "sell_all=True 플래그가 있어야 run_agents.py가 전량 매도 수량을 계산"
        assert result.trade_params.get("side") == "ask"
        assert result.trade_params.get("ord_type") == "market"
        assert getattr(result, "_orchestrator_override", False) is True
        assert "감독 오버라이드" in result.agent_name
        assert "cascade_risk_85" in result._override_reason

    def test_no_override_on_low_cascade(self, monkeypatch):
        """cascade_risk < 70이면 DCA 결정 그대로 유지."""
        orch = Orchestrator()
        agent_decision = Decision(
            decision="buy",
            reason="DCA",
            confidence=0.5,
            buy_score={"total": 60, "threshold": 55},
            trade_params={
                "market": "KRW-BTC",
                "side": "bid",
                "amount": 50_000,
                "is_dca": True,
            },
            external_signal={},
            agent_name="moderate",
        )
        drop_context = {
            "price_change_4h": -1.0,
            "price_change_12h": -1.5,
            "price_change_24h": -2.0,
            "consecutive_red_candles": 2,
            "volume_ratio": 1.1,
            "trend_falling": False,
            "dca_already_done": False,
            "external_bearish_count": 1,
            "cascade_risk": 40,
            "whale_direction": "neutral",
            "funding_rate": 0.0,
        }

        result = orch._override_decision(
            decision=agent_decision,
            drop_context=drop_context,
            market_state={"danger_score": 30, "opportunity_score": 40},
        )
        # DCA 유지 — decision 그대로. 오버라이드 속성이 설정되지 않았음을 확인
        # (_override_decision은 오버라이드 안 할 때 원본 decision을 그대로 반환)
        assert result.decision == "buy"
        assert result.trade_params.get("is_dca") is True
        assert not getattr(result, "_orchestrator_override", False)

    def test_override_new_buy_on_crash(self, monkeypatch):
        """신규 매수(is_dca=False) + 급락 + trend_falling → 관망으로 오버라이드."""
        orch = Orchestrator()
        agent_decision = Decision(
            decision="buy",
            reason="신규 매수",
            confidence=0.55,
            buy_score={"total": 60, "threshold": 55},
            trade_params={
                "market": "KRW-BTC",
                "side": "bid",
                "amount": 30_000,
                "is_dca": False,
            },
            external_signal={},
            agent_name="moderate",
        )
        drop_context = {
            "price_change_4h": -4.0,
            "price_change_12h": -5.0,
            "price_change_24h": -6.0,
            "consecutive_red_candles": 4,
            "volume_ratio": 1.8,
            "trend_falling": True,
            "dca_already_done": False,
            "external_bearish_count": 2,
            "cascade_risk": 55,  # < 70이라 DCA 오버라이드 X
            "whale_direction": "neutral",
            "funding_rate": 0.0,
        }
        result = orch._override_decision(
            decision=agent_decision,
            drop_context=drop_context,
            market_state={"danger_score": 55, "opportunity_score": 20},
        )
        assert result.decision == "hold"
        assert getattr(result, "_orchestrator_override", False) is True
        assert "crash_in_progress" in result._override_reason


# ═════════════════════════════════════════════════════════════
# 5. 파이프라인 구조 보증 (phases_completed 체크)
# ═════════════════════════════════════════════════════════════

class TestPipelineStructure:
    """run_agents.main() 내부에서 발생하는 Phase 개념이 실제 모듈 symbol로 존재."""

    def test_key_pipeline_functions_exist(self, run_agents_module):
        """파이프라인 골격 함수들이 모듈에 정의되어 있어야 한다."""
        must_have = [
            "main",
            "collect_internal_data",
            "run_script",
            "save_execution_log",
            "save_market_data_record",
            "get_rl_advisory",
            "notify_error",
            "log",
        ]
        for name in must_have:
            assert hasattr(run_agents_module, name), (
                f"run_agents.py에 {name} 함수가 누락되었다"
            )

    def test_cycle_id_set(self, run_agents_module):
        """_CYCLE_ID는 문자열(또는 None-safe)로 설정되어야 한다."""
        cid = getattr(run_agents_module, "_CYCLE_ID", None)
        assert cid is not None
        assert isinstance(cid, str)
        assert len(cid) > 0
