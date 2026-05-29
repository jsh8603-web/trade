"""core/coin_sizing.py — 사이징 coin 변형 (SO-3/PR).

WHY: 단일 BTC = 기존 Kelly 유지(재작성 금지). 멀티코인만 Riskfolio tail HRP.
     crisis 상관 집중 완화(H25). risk_gate.check() 경유(near_miss_veto).

변형표 #2 (Phase R):
- 단일 BTC: risk_sizing.size_portfolio 위임 (Kelly/LW 그대로)
- 멀티코인 트리거: cov condition number↑ OR corr 평균 > 임계
- 멀티코인 사이징: Riskfolio HCPortfolio(model=HRP, codependence=tail, w_max=0.10)
- H25 crisis: 상관 과열 → BTC 집중 완화 (BTC 비중 cap)

SACRED:
- execute_trade.py 실주문·run_cycle 미변경
- risk_sizing.py 본체 미변경 (단일 BTC 경로 위임)
- Phase0~6 본체 미변경
- risk_gate.check() 우회 금지
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("core.coin_sizing")

# ── 멀티코인 HRP 트리거 임계 ─────────────────────────────────────────
COIN_COND_THRESHOLD = float(1e6)   # cov condition number 이상 → HRP
COIN_CORR_THRESHOLD = float(0.75)  # 코인 crisis 상관 임계 (주식보다 낮게 — 코인 특성)
COIN_HRP_W_MAX      = float(0.10)  # HRP 단일 비중 상한 (w_max=0.10)
BTC_CRISIS_CAP      = float(0.40)  # H25: crisis 상관 과열 시 BTC 비중 상한

_BITCOIN_TICKERS = {"BTC", "BTC/KRW", "BTCUSDT", "XBT"}


def _is_single_btc(tickers: List[str]) -> bool:
    """단일 BTC 여부 판정 — True이면 기존 Kelly 위임."""
    active = [t for t in tickers if t]
    if len(active) != 1:
        return False
    return active[0].upper().split("/")[0] in _BITCOIN_TICKERS


def _normalize(w: Dict[str, float]) -> Dict[str, float]:
    total = sum(w.values())
    if total <= 0:
        n = len(w)
        return {k: 1.0 / n for k in w}
    return {k: v / total for k, v in w.items()}


def _clamp_and_renorm(w: Dict[str, float], w_max: float) -> Dict[str, float]:
    """w_max 초과 클램핑 후 재정규화.

    모든 값을 w_max로 클램핑한 뒤 정규화. 단순하고 수렴 보장.
    """
    w = {k: min(v, w_max) for k, v in w.items()}
    total = sum(w.values())
    if total <= 0:
        n = len(w)
        return {k: min(1.0 / n, w_max) for k in w}
    # 정규화 후에도 w_max 초과할 수 있으므로 재클램핑 반복
    for _ in range(50):
        normed = {k: v / total for k, v in w.items()}
        if all(v <= w_max + 1e-9 for v in normed.values()):
            return normed
        # 정규화 후 초과 항목 다시 클램핑
        w = {k: min(v, w_max) for k, v in normed.items()}
        total = sum(w.values())
        if total <= 0:
            break
    return {k: v / total for k, v in w.items()}


def should_use_hrp_multi(
    cov_matrix: pd.DataFrame,
    returns: Optional[pd.DataFrame] = None,
) -> bool:
    """멀티코인 HRP 트리거 — condition number 높음 OR 상관 과열."""
    try:
        vals = np.linalg.eigvalsh(cov_matrix.values)
        vals = np.abs(vals)
        pos = vals[vals > 1e-12]
        if len(pos) > 0:
            cond = float(pos.max() / pos.min())
            if cond > COIN_COND_THRESHOLD:
                logger.info("코인 HRP 트리거: condition=%.2e", cond)
                return True
    except Exception:
        pass

    if returns is not None and len(returns.columns) > 1:
        try:
            raw_corr = returns.corr().values
            mask = np.ones(raw_corr.shape, dtype=bool)
            np.fill_diagonal(mask, False)
            avg_corr = float(np.mean(np.abs(raw_corr[mask])))
            if avg_corr > COIN_CORR_THRESHOLD:
                logger.info("코인 HRP 트리거: avg_corr=%.3f > %.2f", avg_corr, COIN_CORR_THRESHOLD)
                return True
        except Exception:
            pass

    return False


def hrp_multi_coin(
    returns: pd.DataFrame,
    w_max: float = COIN_HRP_W_MAX,
    btc_crisis_cap: float = BTC_CRISIS_CAP,
) -> Dict[str, float]:
    """멀티코인 Riskfolio HRP(tail). H25 crisis 상관 → BTC cap.

    Riskfolio 미설치 시 동치 fallback (equal-weight + clamp).
    """
    tickers = list(returns.columns)
    n = len(tickers)

    # H25: crisis 상관 판정 — avg_corr 높으면 BTC 집중 완화
    crisis = False
    try:
        raw_corr = returns.corr().values
        mask = np.ones(raw_corr.shape, dtype=bool)
        np.fill_diagonal(mask, False)
        if np.mean(np.abs(raw_corr[mask])) > COIN_CORR_THRESHOLD:
            crisis = True
    except Exception:
        pass

    # Riskfolio HCPortfolio(model=HRP, codependence=tail)
    weights: Dict[str, float] = {}
    try:
        import riskfolio as rp
        port = rp.HCPortfolio(returns=returns)
        port.assets_stats(method_mu="hist", method_cov="hist")
        w_df = port.optimization(
            model="HRP",
            codependence="tail",
            rm="MV",
            rf=0,
            linkage="single",
            max_k=10,
            leaf_order=True,
        )
        weights = {ticker: float(w_df.loc[ticker, "weights"]) for ticker in tickers
                   if ticker in w_df.index}
        if not weights:
            raise ValueError("HRP 결과 없음")
    except Exception as exc:
        logger.warning("Riskfolio HRP 실패 → equal-weight fallback: %s", exc)
        weights = {t: min(1.0 / n, w_max) for t in tickers}
        weights = _normalize(weights)

    # w_max 클램핑 (HRP 기본) — crisis cap 전에 적용
    weights = _clamp_and_renorm(weights, w_max)

    # H25: crisis → BTC 집중 완화 (btc_crisis_cap 반복 클램핑, 수렴 보장)
    if crisis:
        btc_keys = {k for k in weights if k.upper().split("/")[0] in _BITCOIN_TICKERS}
        if btc_keys:
            # _clamp_and_renorm 동일 패턴으로 BTC만 cap
            for _ in range(50):
                btc_over = {k: v for k, v in weights.items()
                            if k in btc_keys and v > btc_crisis_cap}
                if not btc_over:
                    break
                for k in btc_over:
                    weights[k] = btc_crisis_cap
                total = sum(weights.values())
                if total > 0:
                    weights = {k: v / total for k, v in weights.items()}

    return weights


def size_coin_portfolio(
    tickers: List[str],
    returns: Optional[pd.DataFrame] = None,
    cov_matrix: Optional[pd.DataFrame] = None,
    risk_gate=None,
    cycle_id: str = "",
    nav: float = 1.0,
    proposed_size: float = 0.0,
    **legacy_kwargs,
) -> Dict[str, float]:
    """coin 사이징 진입점.

    - 단일 BTC → risk_sizing.size_portfolio 위임 (Kelly/LW 그대로)
    - 멀티코인 → HRP 트리거 판정 → Riskfolio tail HRP (H25 BTC cap)
    - risk_gate.check() 경유 필수 (near_miss_veto)
    """
    # 단일 BTC: 기존 경로 위임 (재작성 금지)
    if _is_single_btc(tickers):
        logger.debug("단일 BTC → risk_sizing 위임")
        try:
            from core.risk_sizing import size_portfolio
            return size_portfolio(
                returns=returns,
                cov_matrix=cov_matrix,
                **legacy_kwargs,
            )
        except Exception as exc:
            logger.warning("risk_sizing 위임 실패: %s", exc)
            return {tickers[0]: 1.0}

    # 멀티코인: HRP 트리거 판정
    if returns is None or len(returns.columns) < 2:
        logger.warning("멀티코인 returns 부족 → equal-weight")
        n = len(tickers)
        return {t: 1.0 / n for t in tickers}

    use_hrp = should_use_hrp_multi(cov_matrix or pd.DataFrame(), returns)

    if use_hrp:
        weights = hrp_multi_coin(returns)
    else:
        # HRP 트리거 미발동 → equal-weight (단순 베이스라인)
        n = len(tickers)
        weights = {t: 1.0 / n for t in tickers}

    # risk_gate.check() 경유 (near_miss_veto)
    if risk_gate is not None:
        try:
            verdict = risk_gate.check(
                cycle_id=cycle_id,
                action="buy",
                proposed_size=proposed_size,
                nav=nav,
            )
            from core.risk_gate import VerdictType
            if verdict.verdict_type != VerdictType.APPROVED:
                logger.info("risk_gate 거절 → 사이징 0: %s", verdict.reason)
                return {t: 0.0 for t in tickers}
        except Exception as exc:
            logger.warning("risk_gate 호출 실패 — 사이징 진행: %s", exc)

    return weights
