"""
regime_to_weights.py — 레짐 → 슬리브 % (Black-Litterman 메인, MMR 폴백).

설계 정합 (§5.8-B, §5.8-D):
- regime→% = Black-Litterman:
    Prior = §5.8-B Investment Clock 목표비중표 (시총 prior 아님 — 이종 슬리브에 CAPM 불가).
    View  = macro_view stance 편차 (정성 stance → view 벡터).
    τ·Ω   = confidence (낮을수록 Prior 근접 → 과도 tilt 자제).
    공분산 = Ledoit-Wolf (H25).
- 출력 = 슬리브 % (risk_gate 통과 *전*). portfolio_orchestrator 가 risk_gate 캡·밴드 적용.
- MMR fallback: BL 실패/특이행렬 시 IC Prior 그대로 (MMR calculate_weights 는 HMM states 입력이라
  baseline anchor 충돌 → 우리는 안전한 IC Prior 폴백을 MMR 자리에 둔다).
- per-bloc: 미국주식=USD레짐, 한국주식=KRW레짐 독립 키잉; 원자재/금/채권/현금/코인=글로벌(USD).

코드화한 §5.8-B 표 (Reflation/Recovery/Overheat/Stagflation × 7슬리브 ↑/↓/중립/최우위):
- IC_TARGET_WEIGHTS = 표를 실제 목표비중 %로 정량화 (방향 등급 → 기준비중 배수).

github 차용 (입출력 계약 확인 후 어댑트):
- PyPortfolioOpt pypfopt/black_litterman.py:BlackLittermanModel
    __init__(cov_matrix, pi=Prior, absolute_views=dict, omega="idzorek"/"default",
             view_confidences, tau) → .bl_weights() → OrderedDict.
    주의: BL 은 음수 weight(숏) 허용 → long-only 슬리브이므로 음수 클립 + 재정규화 후처리.
- PyPortfolioOpt risk_models.CovarianceShrinkage.ledoit_wolf() — 공분산 (H25).

미해결 결정:
- BL 은 본래 'expected returns' 공간에서 동작 → IC 목표비중(%)을 직접 Prior 로 쓰려면
  '암묵 수익률(implied returns)' 로 역산해야 정합. 여기선 *두 경로* 제공:
    (a) BL_RETURNS 경로: IC Prior weights → reverse-optimize → implied π, view 반영 → 재최적화.
    (b) WEIGHT_TILT 경로(기본·견고): IC Prior weights 에 stance 를 BL τ/Ω 로직으로 tilt
        (수익률 공간 우회, 직관적·수치 안정). 둘 다 동일 인터페이스.
- 슬리브 기준비중(BASE_WEIGHTS)은 정책 파라미터 → 사용자 리스크 한도로 주입 가능.
"""
from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Optional

import numpy as np
import pandas as pd

from .macro_schema import Bloc, MacroView, RegimeLabel, ViewStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 슬리브 정의 + bloc 키잉 (§5.8-B)
# ---------------------------------------------------------------------------
SLEEVES = ["us_stock", "kr_stock", "commodity", "gold", "bond", "cash", "coin"]

# 각 슬리브가 어느 bloc 레짐에 키잉되는가 (§5.8-B: US행=USD, KR행=KRW, 나머지=글로벌USD).
SLEEVE_BLOC = {
    "us_stock": Bloc.USD,
    "kr_stock": Bloc.KRW,
    "commodity": Bloc.USD,
    "gold": Bloc.USD,
    "bond": Bloc.USD,
    "cash": Bloc.USD,
    "coin": Bloc.USD,
}

# 중립(레짐 무관) 기준비중 — 정책 파라미터 (사용자 리스크 한도로 override 가능).
BASE_WEIGHTS = {
    "us_stock": 0.25, "kr_stock": 0.15, "commodity": 0.08,
    "gold": 0.08, "bond": 0.25, "cash": 0.09, "coin": 0.10,
}

# 방향 등급 → 기준비중 배수 (§5.8-B 표: ↑/↓/중립/최우위 정량화).
TILT_MULT = {"top": 1.8, "up": 1.35, "neutral": 1.0, "down": 0.6}

# §5.8-B 표를 코드화: {RegimeLabel: {sleeve: 방향등급}}.
# US/KR 주식은 "stock" 키 하나로 두고 per-bloc 으로 적용 (US레짐→us_stock, KR레짐→kr_stock).
REGIME_DIRECTION = {
    RegimeLabel.REFLATION:   {"stock": "down",    "commodity": "down",    "gold": "up",      "bond": "top",     "cash": "neutral", "coin": "down"},
    RegimeLabel.RECOVERY:    {"stock": "top",     "commodity": "neutral", "gold": "down",    "bond": "down",    "cash": "down",    "coin": "up"},
    RegimeLabel.OVERHEAT:    {"stock": "neutral", "commodity": "top",     "gold": "up",      "bond": "down",    "cash": "down",    "coin": "neutral"},
    RegimeLabel.STAGFLATION: {"stock": "down",    "commodity": "neutral", "gold": "up",      "bond": "down",    "cash": "top",     "coin": "down"},
}


def ic_target_weights(macro_view: MacroView) -> "OrderedDict[str, float]":
    """
    §5.8-B Investment Clock 목표비중표 → per-bloc 정량 목표비중 (BL Prior 입력).

    us_stock 은 USD 레짐, kr_stock 은 KRW 레짐으로 독립 키잉 (US overheat + KR recovery 가능).
    나머지는 USD(글로벌) 레짐. 레짐 unavailable bloc 은 중립(배수 1.0).
    출력은 정규화된 비중 (합=1).
    """
    raw = {}
    for sleeve in SLEEVES:
        bloc = SLEEVE_BLOC[sleeve]
        est = macro_view.regime(bloc)
        base = BASE_WEIGHTS[sleeve]
        if est is None:
            raw[sleeve] = base
            continue
        # 주식은 "stock" 키, 나머지는 슬리브명 그대로.
        dir_key = "stock" if sleeve in ("us_stock", "kr_stock") else sleeve
        grade = REGIME_DIRECTION[est.regime_now].get(dir_key, "neutral")
        raw[sleeve] = base * TILT_MULT[grade]
    return _normalize(raw)


# ---------------------------------------------------------------------------
# 메인 진입점
# ---------------------------------------------------------------------------
def regime_to_weights(
    macro_view: MacroView,
    returns_history: Optional[pd.DataFrame] = None,   # 슬리브 일/월 수익률 (BL 공분산용).
    method: str = "weight_tilt",                      # "weight_tilt" | "bl_returns".
) -> dict:
    """
    macro_view → 슬리브 목표비중 % (risk_gate 통과 전).

    반환: {
      "weights": {sleeve: pct},        # 합=1, long-only.
      "method": "...",                 # 실제 사용된 경로.
      "prior": {sleeve: pct},          # IC Prior (감사용).
      "status": "fresh|stale|unavailable",
      "caution": [...],                # §5.8-H caution flags 전파.
    }
    """
    prior = ic_target_weights(macro_view)
    caution = list(macro_view.caution_flags)

    # unavailable view → IC 중립 Prior 그대로 (degrade, H29).
    if macro_view.status == ViewStatus.UNAVAILABLE or not macro_view.regimes:
        return _result(prior, prior, "ic_prior_unavailable", macro_view.status, caution)

    # stale 이어도 BL 진행 (last-good 으로 청산·리밸런싱 가능, H29) — caution 만 부착.
    if macro_view.status == ViewStatus.STALE:
        caution.append("macro_view_stale")

    try:
        if method == "bl_returns" and returns_history is not None:
            weights = _bl_returns_path(macro_view, prior, returns_history)
            used = "black_litterman_returns"
        else:
            weights = _weight_tilt_path(macro_view, prior, returns_history)
            used = "black_litterman_weight_tilt"
        weights = _project_long_only(weights, prior)
        return _result(weights, prior, used, macro_view.status, caution)
    except Exception as e:
        logger.warning("BL path failed (%s) → MMR/IC-prior fallback", e)
        caution.append(f"bl_fallback:{type(e).__name__}")
        return _result(prior, prior, "ic_prior_fallback", macro_view.status, caution)


# ---------------------------------------------------------------------------
# 경로 (a) weight_tilt — 기본·견고 (BL τ/Ω 로직, 수익률 공간 우회)
# ---------------------------------------------------------------------------
def _weight_tilt_path(macro_view: MacroView, prior: dict, returns_history) -> dict:
    """
    BL 의 핵심 직관(View 를 confidence 로 Prior 와 베이지안 블렌딩)을 weight 공간에서 구현.

      posterior = Prior + α * (View_target - Prior),  α = f(confidence, τ, Ω)

    View_target = stance(슬리브별 tilt -1..+1)를 Prior 에 적용한 목표.
    confidence 낮으면 α↓ → Prior 근접 (§5.8-D τ·Ω=confidence). stance 없으면 Prior 그대로.
    공분산(Ledoit-Wolf)은 변동성 큰 슬리브의 tilt 를 줄이는 데 사용(있을 때).
    """
    stance = macro_view.stance or {}
    if not stance:
        return dict(prior)

    # 슬리브별 view 목표비중: stance>0 → 증대, <0 → 축소 (Prior 기준 ±50% 한도).
    view_target = {}
    for s in SLEEVES:
        tilt = float(np.clip(stance.get(s, 0.0), -1.0, 1.0))
        view_target[s] = prior[s] * (1.0 + 0.5 * tilt)
    view_target = _normalize(view_target)

    # 신뢰도 가중 α — 가장 강한 bloc confidence 기반 (τ-유사 스칼라).
    conf = _aggregate_confidence(macro_view)
    tau = 0.5      # weight-on-views (PyPortfolioOpt 기본 0.05 보다 크게 — weight 공간이라).
    alpha = float(np.clip(tau * conf, 0.0, 0.6))

    # Ledoit-Wolf 변동성으로 슬리브별 Ω 보정 (변동성 큰 슬리브는 view 신뢰 ↓).
    vol = _sleeve_vol(returns_history)
    posterior = {}
    for s in SLEEVES:
        a_s = alpha
        if vol is not None and s in vol:
            a_s *= float(np.clip(1.0 - vol[s], 0.3, 1.0))   # Ω↑(고변동) → tilt↓.
        posterior[s] = prior[s] + a_s * (view_target[s] - prior[s])
    return _normalize(posterior)


# ---------------------------------------------------------------------------
# 경로 (b) bl_returns — PyPortfolioOpt BlackLittermanModel 직접 사용
# ---------------------------------------------------------------------------
def _bl_returns_path(macro_view: MacroView, prior: dict, returns_history: pd.DataFrame) -> dict:
    """
    정통 BL: IC Prior weights → implied returns(π) 역산 → stance 를 absolute view 로 →
    BlackLittermanModel → posterior returns → max-Sharpe weights.

    PyPortfolioOpt 계약(black_litterman.py):
      BlackLittermanModel(cov_matrix, pi=π, absolute_views={asset: ret},
                          omega="idzorek", view_confidences=[...], tau).bl_weights()
    """
    from pypfopt import black_litterman, risk_models
    from pypfopt.efficient_frontier import EfficientFrontier

    cols = [s for s in SLEEVES if s in returns_history.columns]
    if len(cols) < 2:
        raise ValueError("returns_history insufficient for BL")
    rh = returns_history[cols].dropna()

    # 공분산 = Ledoit-Wolf (H25).
    S = risk_models.CovarianceShrinkage(rh, returns_data=True).ledoit_wolf()

    # IC Prior weights → implied(reverse-optimized) returns π = δ Σ w.
    w_prior = pd.Series({c: prior[c] for c in cols})
    w_prior = w_prior / w_prior.sum()
    delta = 2.5   # 시장 위험회피 (기본).
    pi = delta * S.dot(w_prior.values)
    pi = pd.Series(pi, index=cols)

    # stance → absolute views (해당 슬리브 implied return 을 tilt 만큼 상/하향).
    stance = macro_view.stance or {}
    views, confidences = {}, []
    for c in cols:
        tilt = float(np.clip(stance.get(c, 0.0), -1.0, 1.0))
        if abs(tilt) < 1e-6:
            continue
        # implied return 에 ±(연 5% * tilt) view (정성 stance → 정량 view 편차).
        views[c] = float(pi[c] + 0.05 * tilt)
        confidences.append(min(0.5 + 0.5 * abs(tilt), 0.95))
    if not views:
        return dict(prior)

    bl = black_litterman.BlackLittermanModel(
        S, pi=pi, absolute_views=views,
        omega="idzorek", view_confidences=confidences, tau=0.05,
    )
    post_ret = bl.bl_returns()
    post_cov = bl.bl_cov()

    # posterior 로 max-Sharpe (long-only, 가중치 캡).
    ef = EfficientFrontier(post_ret, post_cov, weight_bounds=(0.0, 0.5))
    ef.max_sharpe(risk_free_rate=0.02)
    w = ef.clean_weights()

    # BL 에서 빠진 슬리브(stance 없음·returns 없음)는 Prior 비중 유지 후 재정규화.
    out = {s: w.get(s, prior[s]) for s in SLEEVES}
    return _normalize(out)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _aggregate_confidence(mv: MacroView) -> float:
    confs = [e.confidence_now for e in mv.regimes.values()]
    return float(np.mean(confs)) if confs else 0.0


def _sleeve_vol(returns_history: Optional[pd.DataFrame]):
    """
    Ledoit-Wolf 공분산 대각(연율 변동성)을 [0,1] 로 squash → Ω 보정 입력 (H25).

    sklearn.covariance.LedoitWolf 를 직접 사용 — pypfopt(전체 import 시 cvxpy 필요) 우회.
    sklearn 은 jumpmodels 의존성이라 이미 가용. 둘 다 없으면 표본 std 폴백.
    """
    if returns_history is None:
        return None
    cols = [s for s in SLEEVES if s in returns_history.columns]
    if len(cols) < 2:
        return None
    rh = returns_history[cols].dropna()
    if len(rh) < 2:
        return None
    try:
        from sklearn.covariance import LedoitWolf  # H25 — cvxpy 불필요.
        S = LedoitWolf().fit(rh.values).covariance_
        ann = np.sqrt(np.diag(S) * 252.0)
    except Exception:
        ann = (rh.std().values * np.sqrt(252.0))   # 표본 std 폴백.
    if ann.max() <= 0:
        return None
    ann = ann / (ann.max() + 1e-9)
    return {c: float(v) for c, v in zip(cols, ann)}


def _project_long_only(weights: dict, prior: dict) -> dict:
    """BL 음수(숏) 클립 + 재정규화. 전부 0 이면 Prior 로 폴백."""
    clipped = {s: max(0.0, weights.get(s, 0.0)) for s in SLEEVES}
    if sum(clipped.values()) <= 1e-9:
        return dict(prior)
    return _normalize(clipped)


def _normalize(w: dict) -> dict:
    total = sum(w.values())
    if total <= 1e-12:
        n = len(w)
        return {k: 1.0 / n for k in w}
    return {k: v / total for k, v in w.items()}


def _result(weights, prior, method, status, caution) -> dict:
    return {
        "weights": _round_to_sum_one(weights),
        "prior": _round_to_sum_one(prior),
        "method": method,
        "status": status.value if isinstance(status, ViewStatus) else str(status),
        "caution": caution,
    }


def _round_to_sum_one(w: dict, ndigits: int = 6) -> dict:
    """round 누적 오차를 가장 큰 슬리브에 잔차로 흡수해 합=1 보장 (risk_gate 입력 정합)."""
    rounded = {s: round(w[s], ndigits) for s in SLEEVES}
    residual = round(1.0 - sum(rounded.values()), ndigits)
    if abs(residual) > 0:
        top = max(rounded, key=rounded.get)
        rounded[top] = round(rounded[top] + residual, ndigits)
    return rounded
