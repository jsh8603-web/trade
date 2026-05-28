"""backtest/walk_forward.py — walk-forward + PIT/생존편향 (SO-3/P5).

WHY: OOS/IS Sharpe 분리 없으면 백테스트 과적합. skfolio CombinatorialPurgedCV 로
     purge+embargo 적용. PIT 분리(filing_timestamp<=as_of) + 상폐 포함(백테스트only).

reuse-as-is:
- skfolio CombinatorialPurgedCV(_refs/skfolio ... _combinatorial.py:50) 그대로 사용
- purged_size≥1 (집행지연 자산, _walk_forward.py:118)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from common.metrics import calculate_sharpe_ratio, returns_from_equity

logger = logging.getLogger("backtest.walk_forward")


# ---------------------------------------------------------------------------
# PIT 분리 — 펀더멘털 누수 차단
# ---------------------------------------------------------------------------

def filter_pit_fundamentals(
    fundamentals: list,
    as_of: datetime,
) -> list:
    """PIT 마스킹: filing_timestamp <= as_of 만 통과. 미래 누수 차단.

    SACRED: DART/EDGAR XBRL 만 허용(source∈{DART_XBRL,EDGAR_XBRL}), RESTATED 거부.
    stock/contracts.py Fundamentals.visible_at + is_pit_clean 재사용.
    """
    from stock.contracts import FilingSource
    visible = []
    for f in fundamentals:
        if not f.is_pit_clean():
            continue
        if f.filing_timestamp > as_of:
            continue
        visible.append(f)
    return visible


def is_delisted_universe_only(ticker: str, as_of: datetime, delisted_tickers: set) -> Tuple[bool, bool]:
    """H5 생존편향 체크.

    Returns:
        (in_backtest_universe, in_live_universe):
        상폐 종목 = 백테스트 유니버스 포함(True, False)
        정상 종목 = 둘 다 포함(True, True)
    """
    is_delisted = ticker in delisted_tickers
    if is_delisted:
        return True, False   # 백테스트 포함, 라이브 매수 제외
    return True, True


# ---------------------------------------------------------------------------
# WalkForwardSplit — 단일 fold 결과
# ---------------------------------------------------------------------------

@dataclass
class WalkForwardSplit:
    """단일 fold 결과 — IS(in-sample) / OOS(out-of-sample) Sharpe 분리."""
    split_id: int
    train_indices: np.ndarray
    test_indices: np.ndarray
    is_sharpe: float = 0.0
    oos_sharpe: float = 0.0
    is_return_pct: float = 0.0
    oos_return_pct: float = 0.0
    n_train: int = 0
    n_test: int = 0


# ---------------------------------------------------------------------------
# WalkForwardResult — 전체 walk-forward 결과
# ---------------------------------------------------------------------------

@dataclass
class WalkForwardResult:
    """walk-forward 전체 결과. GO/NO-GO 카드 입력."""
    n_splits: int = 0
    splits: List[WalkForwardSplit] = field(default_factory=list)
    avg_oos_sharpe: float = 0.0
    avg_is_sharpe: float = 0.0
    oos_sharpe_series: pd.Series = field(default_factory=pd.Series)
    is_sharpe_series: pd.Series = field(default_factory=pd.Series)
    # 상폐 포함 여부
    includes_delisted: bool = False


# ---------------------------------------------------------------------------
# WalkForwardEngine — CombinatorialPurgedCV 경유
# ---------------------------------------------------------------------------

class WalkForwardEngine:
    """skfolio CombinatorialPurgedCV 기반 walk-forward 엔진.

    PIT 분리 + 생존편향(H5 상폐 포함) + OOS/IS Sharpe 분리.
    """

    def __init__(
        self,
        n_folds: int = 6,
        n_test_folds: int = 2,
        purged_size: int = 1,    # ≥1 필수 (집행지연 자산)
        embargo_size: int = 0,
    ):
        self._n_folds = n_folds
        self._n_test_folds = n_test_folds
        self._purged_size = max(1, purged_size)  # ≥1 강제
        self._embargo_size = embargo_size

    def _make_cv(self):
        """skfolio CombinatorialPurgedCV 인스턴스 생성."""
        try:
            from skfolio.model_selection import CombinatorialPurgedCV
            return CombinatorialPurgedCV(
                n_folds=self._n_folds,
                n_test_folds=self._n_test_folds,
                purged_size=self._purged_size,
                embargo_size=self._embargo_size,
            )
        except ImportError:
            logger.warning("skfolio 미설치 — 자체 간소 CV 사용")
            return None

    def run(
        self,
        returns: pd.Series,
        asset_track=None,
        engine=None,
        delisted_tickers: Optional[set] = None,
    ) -> WalkForwardResult:
        """walk-forward OOS/IS Sharpe 분리 산출.

        Args:
            returns: 가격 수익률 시계열
            asset_track: BacktestEngine에 주입할 AssetTrack (선택)
            engine: BacktestEngine 인스턴스 (선택)
            delisted_tickers: 상폐 종목 집합 (생존편향 H5)
        """
        result = WalkForwardResult()
        result.includes_delisted = bool(delisted_tickers)

        X = returns.values.reshape(-1, 1)
        cv = self._make_cv()

        splits_data: List[WalkForwardSplit] = []

        if cv is not None:
            split_iter = list(cv.split(X))
        else:
            # fallback: 간소 분할 (skfolio 없을 때)
            split_iter = self._simple_split(len(X))

        for i, (train_idx, test_groups) in enumerate(split_iter):
            # test_groups: skfolio = list of arrays, fallback = single array
            if isinstance(test_groups, list):
                test_idx = np.concatenate(test_groups)
            else:
                test_idx = test_groups

            train_returns = pd.Series(returns.iloc[train_idx].values)
            test_returns = pd.Series(returns.iloc[test_idx].values)

            is_sharpe = calculate_sharpe_ratio(train_returns)
            oos_sharpe = calculate_sharpe_ratio(test_returns)

            split = WalkForwardSplit(
                split_id=i,
                train_indices=train_idx,
                test_indices=test_idx,
                is_sharpe=is_sharpe,
                oos_sharpe=oos_sharpe,
                n_train=len(train_idx),
                n_test=len(test_idx),
            )
            splits_data.append(split)

        result.splits = splits_data
        result.n_splits = len(splits_data)

        if splits_data:
            result.avg_oos_sharpe = float(
                np.mean([s.oos_sharpe for s in splits_data])
            )
            result.avg_is_sharpe = float(
                np.mean([s.is_sharpe for s in splits_data])
            )
            result.oos_sharpe_series = pd.Series(
                [s.oos_sharpe for s in splits_data]
            )
            result.is_sharpe_series = pd.Series(
                [s.is_sharpe for s in splits_data]
            )

        return result

    def _simple_split(self, n: int) -> list:
        """skfolio 없을 때 fallback 분할. CombinatorialPurgedCV 근사 — train 은 test
        양측을 쓰되(조합 경로) test fold 경계에 purge+embargo gap 을 적용해 누수 차단.
        (정통 CombinatorialPurgedCV 통합 = N-P5-SKFOLIO 이연; 그 전까지 누수 방지 gap 보장.)"""
        k = self._n_folds
        gap = self._purged_size + self._embargo_size  # 경계 누수 차단 gap
        fold_size = n // k
        splits = []
        for i in range(k):
            test_start = i * fold_size
            test_end = min(test_start + fold_size, n)
            test_idx = np.arange(test_start, test_end)
            # purge: test 시작 전 gap·test 종료 후 embargo gap 을 train 에서 제외
            train_idx = np.concatenate([
                np.arange(0, max(0, test_start - gap)),
                np.arange(min(test_end + gap, n), n)
            ])
            if len(train_idx) == 0 or len(test_idx) == 0:
                continue
            splits.append((train_idx, test_idx))
        return splits


# ---------------------------------------------------------------------------
# UniverseManager — 상폐 포함 백테스트 유니버스 관리 (H5)
# ---------------------------------------------------------------------------

class UniverseManager:
    """H5 생존편향 제거 — 상폐 종목 포함 백테스트 유니버스.

    라이브 매수는 admission.check_admission 로 상폐 거절 (기존 계약 재사용).
    백테스트 유니버스는 상폐 포함 = 생존편향 없음.
    """

    def __init__(self, delisted_tickers: Optional[set] = None):
        self._delisted = delisted_tickers or set()

    def get_backtest_universe(self, all_tickers: list) -> list:
        """백테스트 유니버스: 상폐 포함 전체."""
        return list(all_tickers)

    def get_live_universe(self, all_tickers: list) -> list:
        """라이브 유니버스: 상폐 제외."""
        return [t for t in all_tickers if t not in self._delisted]

    def is_survival_bias_free(self, backtest_tickers: list) -> bool:
        """백테스트 유니버스에 상폐 종목 포함 여부 확인."""
        return bool(self._delisted & set(backtest_tickers))
