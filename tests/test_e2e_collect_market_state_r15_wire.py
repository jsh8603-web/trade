"""tests/test_e2e_collect_market_state_r15_wire.py — ★Y capstone: 진입점 e2e 통합 배선.

핸드오프 §6(1): collect_market_state(coin_track_macro) = study→runtime wire 의 *진입점*.
  INV_R15 on  → sleeve substrate(returns_panel + macro_view + sleeve_regime_ids)를 실제
                allocate 에 연결 + belief 동적 공분산(belief_conditional_cov) 발동.
  INV_R15 off → substrate 미공급(정적 경로, byte-identical 무회귀).

본 파일은 *진입점→allocate connectivity* 를 전담한다. orchestrator.allocate 내부(golden·belief
동적성·corr_prior PSD)는 test_sleeve_belief_cov.py 가 커버 — 중복하지 않는다.

실 FRED/네트워크 29s fetch 는 CI 부적합 → fetch_sleeve_returns·RegimeClassifier·RealFredAdapter 를
합성(2국면) patch + CoinTrack override 4종으로 격리(실 Upbit/DB 무호출).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.brain.macro_schema import Bloc, MacroView, RegimeEstimate, RegimeLabel, ViewStatus
from core.brain.regime_to_weights import SLEEVES

LABELS = ("Reflation", "Recovery", "Overheat", "Stagflation")
_SPLIT = pd.Timestamp("2025-05-01")   # 합성 returns 기간 중앙 → Recovery↔Overheat 2국면 분할

# -- CoinTrack override 최소 fixture (실 Upbit/외부 호출 차단, test_so2 패턴) --
_MARKET_DATA = {
    "timestamp": "2025-01-01T09:00:00+09:00", "market": "KRW-BTC",
    "current_price": 80_000_000, "ticker": {"signed_change_rate": 0.01},
    "indicators": {"rsi_14": 45.0, "sma_20": 79_000_000},
    "fear_greed": {"value": 40}, "news": {"overall_sentiment": "neutral", "sentiment_score": 0},
}
_EXTERNAL_DATA = {
    "sources": {"fear_greed": {"current": {"value": 40}}},
    "total_score": 0, "fusion": {"signal": "neutral"}, "collection_time_sec": 0, "errors": [],
}
_PORTFOLIO = {
    "krw_balance": 1_000_000, "total_eval": 1_000_000,
    "btc_balance": 0.0, "btc": {}, "btc_ratio": 0.0,
}


def _synth_returns(seed=0):
    """2-regime 슬리브 수익률 (Recovery=전반·Overheat=후반, _SPLIT 분할)."""
    rng = np.random.default_rng(seed)
    n_per = 70
    cols = list(SLEEVES)
    p = len(cols)
    cA = np.eye(p) * 0.02
    cA[0, 6] = cA[6, 0] = 0.012                       # us_stock-coin (regime A)
    cB = np.eye(p) * 0.02
    cB[3, 4] = cB[4, 3] = 0.012                       # gold-bond (regime B)
    XA = rng.normal(size=(n_per, p)) @ np.linalg.cholesky(cA).T
    XB = rng.normal(size=(n_per, p)) @ np.linalg.cholesky(cB).T
    X = np.vstack([XA, XB])
    idx = pd.date_range("2024-01-01", periods=2 * n_per, freq="W")
    return pd.DataFrame(X, columns=cols, index=idx)


class _StubClassifier:
    """FRED 차단 stub: as_of 시점별 2국면 합성 MacroView 반환(FRESH + stance).

    collect_market_state 가 `RegimeClassifier(usd_adapter=RealFredAdapter())` 로 생성 →
    usd_adapter kwarg accept. classify(as_of) 는 (1) collect 본문 macro_view (2) build_sleeve_
    regime_ids 내부 시점별 호출 두 용도 모두 진짜 MacroView 로 응답.
    """

    def __init__(self, *args, usd_adapter=None, **kwargs):
        self._raise = False

    def classify(self, as_of=None):
        if self._raise:
            raise RuntimeError("synthetic FRED unavailable")
        lab = RegimeLabel.OVERHEAT
        if as_of is not None and pd.Timestamp(as_of) < _SPLIT:
            lab = RegimeLabel.RECOVERY
        est = RegimeEstimate(bloc=Bloc.USD, regime_now=lab, confidence_now=0.85)
        # stance 동반(§4: cov 효과 가시) — belief_conditional_cov 발동엔 belief+ids+returns 3-AND 면 충분.
        return MacroView(regimes={Bloc.USD: est}, status=ViewStatus.FRESH,
                         as_of_ts=0.0, stance={"us_stock": 0.6, "gold": -0.4, "coin": 0.3})


def _make_track_and_spy(monkeypatch, *, classifier=None):
    """CoinTrackWithMacro + allocate spy + fetch 카운터 합성 배선.

    Returns: (ct, cap, calls) — cap=allocate kwargs/result capture, calls=fetch 호출수.
    """
    from core.coin_track_macro import CoinTrackWithMacro
    from core.portfolio_orchestrator import PortfolioOrchestrator

    synth = _synth_returns()
    calls = {"fetch": 0}

    def _fake_fetch(as_of=None, **kw):
        calls["fetch"] += 1
        return synth

    monkeypatch.setattr("core.data.sleeve_returns.fetch_sleeve_returns", _fake_fetch)
    monkeypatch.setattr("core.brain.regime_classifier.RegimeClassifier",
                        classifier or _StubClassifier)
    monkeypatch.setattr("core.brain.fred_adapter.RealFredAdapter",
                        lambda *a, **k: object())

    orch = PortfolioOrchestrator()
    cap: dict = {}
    _real = orch.allocate

    def _spy(**kw):
        cap["kw"] = kw
        out = _real(**kw)
        cap["out"] = out
        return out

    orch.allocate = _spy

    ct = CoinTrackWithMacro(
        macro_orchestrator=orch, macro_enabled=True,
        _market_data_override=_MARKET_DATA, _portfolio_override=_PORTFOLIO,
        _external_data_override=dict(_EXTERNAL_DATA), _past_decisions_override=[],
    )
    return ct, cap, calls


def test_r15_on_wires_substrate_into_allocate(monkeypatch):
    """INV_R15 on → 진입점이 substrate(returns+macro_view+ids)를 allocate 에 실제 연결 + 동적공분산 발동."""
    pytest.importorskip("pypfopt")
    pytest.importorskip("sklearn")
    monkeypatch.setenv("INV_R15_WEIGHTS", "true")
    ct, cap, calls = _make_track_and_spy(monkeypatch)

    state = ct.collect_market_state()

    # 1) substrate fetch 발동 + allocate 에 셋 다 None 아니게 전달 (배선 LIVE)
    assert calls["fetch"] == 1, "r15 on 인데 sleeve returns fetch 미발동"
    assert cap["kw"]["returns_history"] is not None
    assert cap["kw"]["macro_view"] is not None
    assert cap["kw"]["sleeve_regime_ids"] is not None
    # 2) regime substrate 가 실제 2국면 (build_sleeve_regime_ids 진짜 동작 — stub classify 경유)
    ids = np.asarray(cap["kw"]["sleeve_regime_ids"])
    assert set(np.unique(ids)) <= {-1, 1, 2}
    assert (ids == 1).sum() > 0 and (ids == 2).sum() > 0, "2국면 substrate 미생성"
    # 3) belief 동적 공분산 실발동 (Σ_eff → BL 공분산 주입)
    assert "r15_belief" in cap["out"]
    assert abs(sum(cap["out"]["r15_belief"].values()) - 1.0) < 1e-6
    assert any("belief_conditional_cov" in str(c) for c in cap["out"].get("caution", [])), \
        cap["out"].get("caution")
    # 4) 진입점 산출물 (raw_external_data 에 macro_weights 박힘, 합=1)
    mw = state.raw_external_data["macro_weights"]
    assert abs(sum(mw.values()) - 1.0) < 1e-4
    assert state.raw_external_data["macro_status"] is not None


def test_r15_off_no_substrate_static_path(monkeypatch):
    """INV_R15 off → substrate fetch 0회 + allocate 정적(None) 경로 + macro_weights 여전히 산출."""
    monkeypatch.delenv("INV_R15_WEIGHTS", raising=False)
    ct, cap, calls = _make_track_and_spy(monkeypatch)

    state = ct.collect_market_state()

    assert calls["fetch"] == 0, "r15 off 인데 sleeve fetch 발동(무회귀 위반)"
    assert cap["kw"]["returns_history"] is None
    assert cap["kw"]["macro_view"] is None
    assert cap["kw"]["sleeve_regime_ids"] is None
    assert "r15_belief" not in cap["out"], "r15 off 인데 belief 산출(무회귀 위반)"
    mw = state.raw_external_data["macro_weights"]
    assert abs(sum(mw.values()) - 1.0) < 1e-4        # 정적 배분은 그대로 산출


def test_r15_on_classify_failure_graceful(monkeypatch):
    """on + classify 예외(FRED 실패 모사) → 예외 전파 없이 정적 fallback + macro_weights 산출."""
    monkeypatch.setenv("INV_R15_WEIGHTS", "true")

    class _RaisingClassifier(_StubClassifier):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._raise = True

    ct, cap, _calls = _make_track_and_spy(monkeypatch, classifier=_RaisingClassifier)

    state = ct.collect_market_state()       # 예외 없이 완주해야 함

    # classify 실패 → 안쪽 try 가 substrate 전부 None 리셋 → allocate 정적 경로
    assert cap["kw"]["macro_view"] is None
    assert cap["kw"]["sleeve_regime_ids"] is None
    mw = state.raw_external_data["macro_weights"]
    assert abs(sum(mw.values()) - 1.0) < 1e-4
