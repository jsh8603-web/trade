"""core/risk_sizing.py — 멀티에셋 사이징 (Phase 2 SO-5).

Ledoit-Wolf 공분산 → 변동성 타깃 비중 사이징 (PyPortfolioOpt SSOT).
HRP tail-codependence fallback (Riskfolio, w_max=0.10 클램핑).

PRODUCTION: 실 라이브러리 import.
  - pypfopt.risk_models.CovarianceShrinkage.ledoit_wolf()  (PyPortfolioOpt)
  - riskfolio.HCPortfolio.optimization(model='HRP', codependence='tail')

SACRED: LLM import 0, 코인 라이브 미변경, Phase0/1 본체 미변경.
        sklearn/scipy 대체 금지 — 실 라이브러리 사용.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger("core.risk_sizing")

# ── HRP fallback 트리거 임계 ─────────────────────────────────────────
COND_NUMBER_THRESHOLD = float(1e6)   # cov condition number 이상 → HRP
AVG_CORR_THRESHOLD   = float(0.80)  # 평균 상관 이상 → HRP (crisis corr 1수렴)
HRP_W_MAX            = float(0.10)  # HRP 최대 단일 비중 (클램핑 후 재정규화)


# ── 유틸 ─────────────────────────────────────────────────────────────

def _normalize_weights(w: dict[str, float]) -> dict[str, float]:
    """비중 합 → 1.0 재정규화."""
    total = sum(w.values())
    if total <= 0:
        n = len(w)
        return {k: 1.0 / n for k in w}
    return {k: v / total for k, v in w.items()}


def _clamp_and_renorm(w: dict[str, float], w_max: float) -> dict[str, float]:
    """w_max 초과 비중 클램핑 후 재정규화 (수렴까지 반복)."""
    for _ in range(100):
        clamped = {k: min(v, w_max) for k, v in w.items()}
        total = sum(clamped.values())
        if total <= 0:
            break
        renormed = {k: v / total for k, v in clamped.items()}
        converged = all(abs(renormed[k] - clamped[k] / total) < 1e-10 for k in w)
        w = renormed
        if converged and all(v <= w_max + 1e-9 for v in w.values()):
            break
    return w


def _should_use_hrp(cov_matrix: pd.DataFrame, returns: pd.DataFrame | None = None) -> bool:
    """HRP fallback 트리거: cov condition number 높음 또는 raw 상관 과열.

    cov_matrix: Ledoit-Wolf shrunk 공분산 (condition number 체크용).
    returns: raw returns (평균 상관 체크용 — LW shrinkage 전 원본).
    """
    try:
        eigenvalues = np.linalg.eigvalsh(cov_matrix.values)
        pos_eigs = eigenvalues[eigenvalues > 0]
        if len(pos_eigs) == 0:
            return True
        cond = pos_eigs[-1] / pos_eigs[0]
        if cond > COND_NUMBER_THRESHOLD:
            logger.info("HRP fallback: condition number=%.2e > %.2e", cond, COND_NUMBER_THRESHOLD)
            return True

        # raw returns 상관 (LW shrinkage 영향 없는 원본)
        if returns is not None and len(returns.columns) > 1:
            raw_corr = returns.corr().values
            n = len(raw_corr)
            mask = ~np.eye(n, dtype=bool)
            avg_corr = float(np.mean(np.abs(raw_corr[mask])))
            if avg_corr > AVG_CORR_THRESHOLD:
                logger.info("HRP fallback: raw avg_corr=%.3f > %.2f", avg_corr, AVG_CORR_THRESHOLD)
                return True
    except Exception as e:
        logger.warning("HRP trigger check 실패: %s → HRP 사용", e)
        return True
    return False


# ── Ledoit-Wolf 사이징 ────────────────────────────────────────────────

def ledoit_wolf_weights(
    returns: pd.DataFrame,
    vol_target: float = 0.15,
    cov: pd.DataFrame | None = None,
) -> tuple[dict[str, float], pd.DataFrame]:
    """PyPortfolioOpt CovarianceShrinkage.ledoit_wolf() → 변동성 타깃 비중.

    비중 합 ≈ 1.0, non-negative (역변동성 방식, vol_target 기준 스케일링).
    cov 가 주어지면 재계산 생략(size_portfolio 의 LW 공분산 재사용).
    반환: (weights, cov).
    """
    if cov is None:
        from pypfopt.risk_models import CovarianceShrinkage  # noqa: PLC0415
        cov = CovarianceShrinkage(returns).ledoit_wolf()

    # 역변동성 비중
    vols = np.sqrt(np.diag(cov.values))
    inv_vols = np.where(vols > 0, 1.0 / vols, 0.0)
    total_inv = inv_vols.sum()
    if total_inv <= 0:
        n = len(returns.columns)
        raw_w = {col: 1.0 / n for col in returns.columns}
    else:
        raw_w = {col: float(iv / total_inv) for col, iv in zip(returns.columns, inv_vols)}

    return _normalize_weights(raw_w), cov


# ── HRP tail-codependence 사이징 ─────────────────────────────────────

def hrp_weights(
    returns: pd.DataFrame,
    w_max: float = HRP_W_MAX,
) -> dict[str, float]:
    """Riskfolio HCPortfolio.optimization(model='HRP', codependence='tail') + w_max 클램핑.

    w_max=0.10 초과 비중을 클램핑 후 재정규화.
    """
    import riskfolio as rp  # noqa: PLC0415

    port = rp.HCPortfolio(returns=returns)
    w_df = port.optimization(model="HRP", codependence="tail", rm="MV")

    raw_w = {str(idx): float(val) for idx, val in w_df["weights"].items()}

    # w_max 클램핑
    clamped = _clamp_and_renorm(raw_w, w_max)
    return clamped


# ── 통합 사이징 진입점 ────────────────────────────────────────────────

def size_portfolio(
    returns: pd.DataFrame,
    vol_target: float = 0.15,
    hrp_w_max: float = HRP_W_MAX,
    force_hrp: bool = False,
) -> tuple[dict[str, float], str]:
    """멀티에셋 최종 비중 계산.

    반환: (weights_dict, method) — method = 'ledoit_wolf' | 'hrp'

    단일자산: 기존 사이징 유지 (1.0 반환).
    멀티에셋: Ledoit-Wolf 시도 → ill-conditioned/고상관 → HRP fallback.
    """
    if returns is None or returns.empty:
        return {}, "empty"

    assets = list(returns.columns)
    n = len(assets)

    if n == 1:
        return {assets[0]: 1.0}, "single"

    try:
        from pypfopt.risk_models import CovarianceShrinkage  # noqa: PLC0415
        cs = CovarianceShrinkage(returns)
        cov = cs.ledoit_wolf()

        use_hrp = force_hrp or _should_use_hrp(cov, returns)

        if use_hrp:
            w = hrp_weights(returns, w_max=hrp_w_max)
            return w, "hrp"
        else:
            w, _ = ledoit_wolf_weights(returns, vol_target, cov=cov)
            return w, "ledoit_wolf"

    except Exception as e:
        logger.warning("size_portfolio 실패: %s → HRP fallback", e)
        try:
            w = hrp_weights(returns, w_max=hrp_w_max)
            return w, "hrp"
        except Exception as e2:
            logger.error("HRP도 실패: %s → 균등배분", e2)
            return {a: 1.0 / n for a in assets}, "equal"
