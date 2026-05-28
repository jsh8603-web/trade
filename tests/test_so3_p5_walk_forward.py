"""tests/test_so3_p5_walk_forward.py — SO-3/P5 walk-forward + PIT/생존편향 검증.

검증 기준 (harness2.md SO-3):
1. CombinatorialPurgedCV 폴드 생성 (purge+embargo 적용)
2. OOS/IS Sharpe 분리 산출
3. PIT 분리 (미래 펀더멸 누수 0, filing_timestamp<=as_of)
4. 상폐 백테스트 포함·라이브 매수 admission 제외
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timezone, timedelta

from backtest.walk_forward import (
    WalkForwardEngine,
    WalkForwardResult,
    WalkForwardSplit,
    UniverseManager,
    filter_pit_fundamentals,
    is_delisted_universe_only,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_returns(n: int = 100, seed: int = 42) -> pd.Series:
    np.random.seed(seed)
    return pd.Series(np.random.normal(0.001, 0.01, n))


def _make_fundamentals(tickers_dates: list):
    """합성 Fundamentals 목록."""
    from stock.contracts import Fundamentals, FilingSource
    result = []
    for ticker, filing_dt, source in tickers_dates:
        result.append(Fundamentals(
            ticker=ticker,
            fiscal_period="2023FY",
            filing_timestamp=filing_dt,
            source=source,
            as_reported=True,
            revenue=1e10,
        ))
    return result


# ---------------------------------------------------------------------------
# 1. CombinatorialPurgedCV 폴드 생성
# ---------------------------------------------------------------------------

def test_cv_generates_folds():
    """CombinatorialPurgedCV 폴드 생성 확인 (skfolio 설치 시). 미설치=skip."""
    skfolio_ms = pytest.importorskip("skfolio.model_selection", reason="skfolio 미설치")

    CombinatorialPurgedCV = skfolio_ms.CombinatorialPurgedCV
    X = np.random.randn(60, 1)
    cv = CombinatorialPurgedCV(n_folds=6, n_test_folds=2, purged_size=1)
    splits = list(cv.split(X))
    assert len(splits) > 0
    for train_idx, test_groups in splits:
        assert len(train_idx) > 0
        for test_idx in test_groups:
            assert len(test_idx) > 0


def test_cv_purged_size_reduces_train():
    """purged_size=1 시 train 집합이 test 인접 구간 제거됨. 미설치=skip."""
    skfolio_ms = pytest.importorskip("skfolio.model_selection", reason="skfolio 미설치")

    CombinatorialPurgedCV = skfolio_ms.CombinatorialPurgedCV
    X = np.random.randn(30, 1)
    cv_no_purge = CombinatorialPurgedCV(n_folds=3, n_test_folds=2, purged_size=0)
    cv_purge = CombinatorialPurgedCV(n_folds=3, n_test_folds=2, purged_size=1)

    splits_no = list(cv_no_purge.split(X))
    splits_pu = list(cv_purge.split(X))

    # purge 있으면 train 집합이 작거나 같음
    for (train_no, _), (train_pu, _) in zip(splits_no, splits_pu):
        assert len(train_pu) <= len(train_no)


def test_purged_size_min_1():
    """WalkForwardEngine purged_size 는 항상 ≥1."""
    engine = WalkForwardEngine(purged_size=0)
    assert engine._purged_size >= 1


# ---------------------------------------------------------------------------
# 2. OOS/IS Sharpe 분리
# ---------------------------------------------------------------------------

def test_walk_forward_oos_is_separate():
    """OOS/IS Sharpe 분리 산출 확인."""
    engine = WalkForwardEngine(n_folds=4, n_test_folds=2, purged_size=1)
    returns = _make_returns(80)
    result = engine.run(returns)
    assert isinstance(result, WalkForwardResult)
    assert result.n_splits > 0
    for split in result.splits:
        assert isinstance(split.is_sharpe, float)
        assert isinstance(split.oos_sharpe, float)


def test_walk_forward_avg_sharpe_computed():
    """평균 OOS/IS Sharpe 산출."""
    engine = WalkForwardEngine(n_folds=4, n_test_folds=2, purged_size=1)
    returns = _make_returns(80)
    result = engine.run(returns)
    assert isinstance(result.avg_oos_sharpe, float)
    assert isinstance(result.avg_is_sharpe, float)


def test_walk_forward_split_indices_disjoint():
    """각 fold의 train/test 인덱스 비겹침."""
    engine = WalkForwardEngine(n_folds=4, n_test_folds=2, purged_size=1)
    returns = _make_returns(80)
    result = engine.run(returns)
    for split in result.splits:
        train_set = set(split.train_indices.tolist())
        test_set = set(split.test_indices.tolist())
        assert len(train_set & test_set) == 0, "train/test 겹침 발견"


# ---------------------------------------------------------------------------
# 3. PIT 분리 — 미래 펀더멘털 누수 0
# ---------------------------------------------------------------------------

def test_pit_filter_blocks_future():
    """as_of 이후 filing_timestamp → 필터 제거 (미래 누수 차단)."""
    from stock.contracts import FilingSource
    as_of = datetime(2023, 6, 1, tzinfo=timezone.utc)
    future_dt = datetime(2023, 9, 1, tzinfo=timezone.utc)
    past_dt = datetime(2023, 3, 1, tzinfo=timezone.utc)

    funds = _make_fundamentals([
        ("005930", past_dt, FilingSource.DART_XBRL),
        ("005930", future_dt, FilingSource.DART_XBRL),
    ])
    visible = filter_pit_fundamentals(funds, as_of)
    assert len(visible) == 1
    assert visible[0].filing_timestamp == past_dt


def test_pit_filter_blocks_restated():
    """RESTATED source → PIT-clean 아님 → 필터 제거."""
    from stock.contracts import FilingSource
    as_of = datetime(2023, 6, 1, tzinfo=timezone.utc)
    past_dt = datetime(2023, 3, 1, tzinfo=timezone.utc)

    funds = _make_fundamentals([
        ("005930", past_dt, FilingSource.RESTATED),
        ("005930", past_dt, FilingSource.DART_XBRL),
    ])
    visible = filter_pit_fundamentals(funds, as_of)
    assert len(visible) == 1
    assert visible[0].source.value == "dart_xbrl"


def test_pit_filter_allows_xbrl_only():
    """DART_XBRL, EDGAR_XBRL 만 통과."""
    from stock.contracts import FilingSource
    as_of = datetime(2023, 12, 31, tzinfo=timezone.utc)
    dt = datetime(2023, 6, 1, tzinfo=timezone.utc)

    funds = _make_fundamentals([
        ("005930", dt, FilingSource.DART_XBRL),
        ("AAPL", dt, FilingSource.EDGAR_XBRL),
        ("005930", dt, FilingSource.RESTATED),
    ])
    visible = filter_pit_fundamentals(funds, as_of)
    assert len(visible) == 2
    sources = {f.source.value for f in visible}
    assert sources == {"dart_xbrl", "edgar_xbrl"}


# ---------------------------------------------------------------------------
# 4. 생존편향 — 상폐 백테스트 포함·라이브 제외
# ---------------------------------------------------------------------------

def test_delisted_in_backtest_not_live():
    """상폐 종목: 백테스트 유니버스 포함, 라이브 유니버스 제외."""
    in_bt, in_live = is_delisted_universe_only("999999", datetime.now(), {"999999"})
    assert in_bt is True
    assert in_live is False


def test_normal_in_both_universes():
    """정상 종목: 백테스트·라이브 모두 포함."""
    in_bt, in_live = is_delisted_universe_only("005930", datetime.now(), {"999999"})
    assert in_bt is True
    assert in_live is True


def test_universe_manager_backtest_includes_delisted():
    """UniverseManager: 백테스트 유니버스 = 상폐 포함."""
    mgr = UniverseManager(delisted_tickers={"999999"})
    all_tickers = ["005930", "000660", "999999"]
    bt_universe = mgr.get_backtest_universe(all_tickers)
    live_universe = mgr.get_live_universe(all_tickers)
    assert "999999" in bt_universe
    assert "999999" not in live_universe


def test_universe_manager_survival_bias_free():
    """UniverseManager.is_survival_bias_free: 상폐 포함 시 True."""
    mgr = UniverseManager(delisted_tickers={"999999"})
    assert mgr.is_survival_bias_free(["005930", "999999"]) is True
    assert mgr.is_survival_bias_free(["005930"]) is False


def test_walk_forward_tracks_delisted():
    """WalkForwardResult.includes_delisted 상폐 포함 여부 기록."""
    engine = WalkForwardEngine(n_folds=4, n_test_folds=2, purged_size=1)
    returns = _make_returns(80)
    result = engine.run(returns, delisted_tickers={"999999"})
    assert result.includes_delisted is True


# ---------------------------------------------------------------------------
# 5. admission 연동 — 상폐 종목 라이브 거절
# ---------------------------------------------------------------------------

def test_admission_rejects_delisted_from_live():
    """admission.check_admission: 상폐 종목 → KRX_DELISTING_RISK 거절."""
    from stock.admission import check_admission, KrxStatusSnapshot, AdmissionRejectionReason
    from stock.contracts import ProductTier

    snap = KrxStatusSnapshot(is_delisting_risk=True)
    result = check_admission("999999", ProductTier.CORE_ALLOWED, "KR", krx_status=snap)
    assert result.admit is False
    assert result.reason == AdmissionRejectionReason.KRX_DELISTING_RISK
