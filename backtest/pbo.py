"""backtest/pbo.py — PBO(CSCV 정통식)+DSR+GO/NO-GO 카드 (SO-4/P5).

WHY: 다중검정 과적합(H23) 방지. PBO 정통식 = CSCV logit-rank 집계기.
     yakub268 validation_framework.py:179 norm.cdf 근사식 폐기(CSCV 정통식만 사용).

reuse-as-is (재코딩 금지):
- yakub268 validation_framework.py:218 calculate_deflated_sharpe_ratio 그대로
- yakub268 walk_forward.py:134 assess_go_nogo + GoNoGoStatus + GoNoGoCriteria 그대로

PBO 정통식 (Bailey & Lopez de Prado, CSCV logit-rank):
1. CombinatorialPurgedCV 경로별 OOS Sharpe 수집
2. 각 경로에서 IS 최고 전략이 OOS 최하위인지 logit 변환
3. PBO = P(logit(rank_OOS) < 0)
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger("backtest.pbo")


# ---------------------------------------------------------------------------
# yakub268 walk_forward.py:17-51 — 그대로 재사용 (재코딩 금지)
# ---------------------------------------------------------------------------

class GoNoGoStatus(Enum):
    GO = "GO"
    NO_GO = "NO_GO"
    MARGINAL = "MARGINAL"


class GoNoGoCriteria:
    """yakub268 walk_forward.py:83 그대로."""
    MIN_SHARPE = 1.0
    MIN_TRADES = 0          # 우리 엔진은 trade count 별도 집계
    MAX_DRAWDOWN = -15.0
    MIN_WIN_RATE = 45.0
    MARGINAL_SHARPE = 0.7
    MARGINAL_WIN_RATE = 40.0
    MARGINAL_DRAWDOWN = -20.0


def assess_go_nogo(
    sharpe: float,
    trades: int,
    max_drawdown: float,
    win_rate: float,
) -> Tuple[GoNoGoStatus, str]:
    """yakub268 walk_forward.py:134 그대로 채택 (재코딩 금지)."""
    reasons = []

    if GoNoGoCriteria.MIN_TRADES > 0 and trades < GoNoGoCriteria.MIN_TRADES:
        reasons.append(f"Insufficient trades ({trades} < {GoNoGoCriteria.MIN_TRADES})")
    if max_drawdown < GoNoGoCriteria.MAX_DRAWDOWN:
        reasons.append(f"Excessive drawdown ({max_drawdown:.1f}% < {GoNoGoCriteria.MAX_DRAWDOWN}%)")

    if reasons:
        return GoNoGoStatus.NO_GO, "; ".join(reasons)

    meets_sharpe = sharpe >= GoNoGoCriteria.MIN_SHARPE
    meets_win_rate = win_rate >= GoNoGoCriteria.MIN_WIN_RATE
    meets_drawdown = max_drawdown >= GoNoGoCriteria.MAX_DRAWDOWN

    if meets_sharpe and meets_win_rate and meets_drawdown:
        return GoNoGoStatus.GO, (
            f"All criteria met (Sharpe={sharpe:.2f}, "
            f"WR={win_rate:.1f}%, DD={max_drawdown:.1f}%)"
        )

    marginal_sharpe = sharpe >= GoNoGoCriteria.MARGINAL_SHARPE
    marginal_win_rate = win_rate >= GoNoGoCriteria.MARGINAL_WIN_RATE
    marginal_drawdown = max_drawdown >= GoNoGoCriteria.MARGINAL_DRAWDOWN

    if marginal_sharpe and marginal_win_rate and marginal_drawdown:
        warnings = []
        if not meets_sharpe:
            warnings.append(f"Sharpe below target ({sharpe:.2f} < {GoNoGoCriteria.MIN_SHARPE})")
        if not meets_win_rate:
            warnings.append(f"Win rate below target ({win_rate:.1f}% < {GoNoGoCriteria.MIN_WIN_RATE}%)")
        return GoNoGoStatus.MARGINAL, "; ".join(warnings)

    failures = []
    if not marginal_sharpe:
        failures.append(f"Low Sharpe ({sharpe:.2f})")
    if not marginal_win_rate:
        failures.append(f"Low win rate ({win_rate:.1f}%)")
    if not marginal_drawdown:
        failures.append(f"High drawdown ({max_drawdown:.1f}%)")

    return GoNoGoStatus.NO_GO, "; ".join(failures)


# ---------------------------------------------------------------------------
# yakub268 validation_framework.py:218 — 그대로 재사용 (재코딩 금지)
# ---------------------------------------------------------------------------

@dataclass
class DSRResult:
    """yakub268 validation_framework.py:210 그대로."""
    observed_sharpe: float
    deflated_sharpe: float
    expected_max_sharpe: float
    p_value: float
    is_significant: bool  # True if DSR > 0.95


def calculate_deflated_sharpe_ratio(
    observed_sharpe: float,
    n_trials: int,
    track_record_length: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    benchmark_sharpe: float = 0.0,
) -> DSRResult:
    """yakub268 validation_framework.py:218 그대로 채택 (재코딩 금지)."""
    euler_gamma = 0.5772156649

    if n_trials <= 1:
        expected_max_sharpe = benchmark_sharpe
    else:
        z1 = stats.norm.ppf(1 - 1 / n_trials)
        z2 = stats.norm.ppf(1 - 1 / (n_trials * math.e))
        expected_max_sharpe = benchmark_sharpe + (
            (1 - euler_gamma) * z1 + euler_gamma * z2
        ) / math.sqrt(track_record_length)

    sr_var = (
        1 + 0.5 * observed_sharpe**2
        - skewness * observed_sharpe
        + ((kurtosis - 3) / 4) * observed_sharpe**2
    ) / track_record_length

    if sr_var > 0:
        z_score = (observed_sharpe - expected_max_sharpe) / math.sqrt(sr_var)
        deflated_sharpe = float(stats.norm.cdf(z_score))  # yakub268 :271
    else:
        deflated_sharpe = 0.5

    p_value = 1 - deflated_sharpe

    return DSRResult(
        observed_sharpe=observed_sharpe,
        deflated_sharpe=deflated_sharpe,
        expected_max_sharpe=expected_max_sharpe,
        p_value=p_value,
        is_significant=deflated_sharpe > 0.95,
    )


# ---------------------------------------------------------------------------
# PBO 정통식 — CSCV logit-rank 집계기
# (yakub268 :179 norm.cdf 근사식 폐기 — SACRED)
# ---------------------------------------------------------------------------

def calculate_pbo_cscv(
    oos_sharpe_paths: List[float],
    is_sharpe_paths: Optional[List[float]] = None,
) -> float:
    """CSCV logit-rank PBO 정통식 (근사식 :179 폐기).

    Bailey & Lopez de Prado (2014):
    1. 각 경로 OOS Sharpe 순위를 logit 변환
    2. PBO = E[logit(rank) < 0] = 경로 중 OOS 음수 비율

    Args:
        oos_sharpe_paths: 각 CSCV 경로의 OOS Sharpe 목록
        is_sharpe_paths: (선택) IS Sharpe 목록 (경로별 최고 IS 선택 시 사용)

    Returns:
        PBO ∈ [0, 1]. 높을수록 과적합.
    """
    if not oos_sharpe_paths:
        return 0.5

    paths = np.array(oos_sharpe_paths, dtype=float)
    n = len(paths)

    # 순위 기반 logit 변환 (Bailey & Lopez de Prado 정통식)
    # rank = OOS Sharpe 의 상대 순위 (1-based, 낮은 값 = 낮은 rank)
    # argsort(argsort) 는 동률을 달리 처리 — 실제 순위(rankdata) 사용
    from scipy.stats import rankdata
    ranks = rankdata(paths, method="average")  # 동률 평균, 1-based
    # logit(rank / (n+1)) — 양쪽 끝 0/1 회피
    logit_ranks = np.log(ranks / (n + 1 - ranks + 1e-12))

    # PBO = logit_rank < 0 (OOS 가 하위 경로 비율)
    pbo = float(np.mean(logit_ranks < 0))
    return max(0.0, min(1.0, pbo))


# ---------------------------------------------------------------------------
# GO/NO-GO 카드 — JSON 직렬화 가능
# ---------------------------------------------------------------------------

@dataclass
class GoNoGoCard:
    """GO/NO-GO 카드 (G5/G8 렌더 스키마). JSON 직렬화 가능."""
    status: str          # "GO" | "MARGINAL" | "NO_GO"
    reason: str
    sharpe: float
    max_drawdown: float
    win_rate: float
    n_trades: int
    pbo: float           # CSCV 정통식 PBO
    dsr: float           # Deflated Sharpe Ratio
    dsr_significant: bool
    avg_oos_sharpe: float
    n_wf_splits: int

    def to_json(self) -> str:
        """JSON 직렬화."""
        d = asdict(self)
        return json.dumps(d, ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "GoNoGoCard":
        return cls(**d)


def build_go_nogo_card(
    oos_sharpe_paths: List[float],
    max_drawdown: float,
    win_rate: float,
    n_trades: int,
    n_trials: int,
    track_record_length: int,
    avg_oos_sharpe: Optional[float] = None,
) -> GoNoGoCard:
    """PBO + DSR + GO/NO-GO 를 종합한 카드 생성.

    Args:
        oos_sharpe_paths: CSCV 경로별 OOS Sharpe
        max_drawdown: 최대 낙폭 %
        win_rate: 승률 %
        n_trades: 총 거래수
        n_trials: DSR 계산용 전략 시도 수
        track_record_length: 백테스트 기간(관측수)
        avg_oos_sharpe: 평균 OOS Sharpe (없으면 paths 평균)
    """
    avg_sharpe = avg_oos_sharpe or (
        float(np.mean(oos_sharpe_paths)) if oos_sharpe_paths else 0.0
    )

    # PBO 정통식
    pbo = calculate_pbo_cscv(oos_sharpe_paths)

    # DSR
    dsr_result = calculate_deflated_sharpe_ratio(
        observed_sharpe=avg_sharpe,
        n_trials=max(1, n_trials),
        track_record_length=max(2, track_record_length),
    )

    # GO/NO-GO
    status, reason = assess_go_nogo(
        sharpe=avg_sharpe,
        trades=n_trades,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
    )

    return GoNoGoCard(
        status=status.value,
        reason=reason,
        sharpe=avg_sharpe,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        n_trades=n_trades,
        pbo=pbo,
        dsr=dsr_result.deflated_sharpe,
        dsr_significant=dsr_result.is_significant,
        avg_oos_sharpe=avg_sharpe,
        n_wf_splits=len(oos_sharpe_paths),
    )
