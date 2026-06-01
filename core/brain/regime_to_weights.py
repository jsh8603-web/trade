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
    belief: Optional[dict] = None,                    # ④ R15 belief b(t) {regime_label: prob}.
    sleeve_regime_ids=None,                           # ④ 슬리브 시점별 regime int id (substrate).
    labels=("Reflation", "Recovery", "Overheat", "Stagflation"),
    as_of=None,                                       # IC7: decision-time(valid-time) — static Λ PIT 컷오프.
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

    ④ belief 동적 공분산 (opt-in, R15 자산 배분 레이어): belief + sleeve_regime_ids +
    returns_history 셋 다 제공되면 regime-conditional glasso(Σ_eff, belief-mix)를 BL 공분산으로
    주입해 정통 BL(bl_returns)을 강제한다. confidence 낮으면 between-dispersion 이 inflate 돼
    공분산이 부풀고 tilt 가 자동 보수화(transition de-risk). substrate 부족/실패 시 기존 경로로
    graceful(byte-identical 무회귀). 종목 *판정* R15(stock_track)와 다른 *배분* 레이어.
    """
    prior = ic_target_weights(macro_view)
    caution = list(macro_view.caution_flags)

    # unavailable view → IC 중립 Prior 그대로 (degrade, H29).
    if macro_view.status == ViewStatus.UNAVAILABLE or not macro_view.regimes:
        return _result(prior, prior, "ic_prior_unavailable", macro_view.status, caution)

    # stale 이어도 BL 진행 (last-good 으로 청산·리밸런싱 가능, H29) — caution 만 부착.
    if macro_view.status == ViewStatus.STALE:
        caution.append("macro_view_stale")

    # ④ belief 동적 공분산 산출 시도 (substrate 충족 시만, 아니면 None → 기존 경로).
    cov_override = None
    if belief is not None and sleeve_regime_ids is not None and returns_history is not None:
        cov_override = _belief_conditional_cov(returns_history, sleeve_regime_ids, belief, labels, as_of=as_of)
        if cov_override is not None:
            method = "bl_returns"                     # belief cov 는 정통 BL 경로에서만 의미.
            caution.append("belief_conditional_cov(Σ_eff regime-glasso 주입)")

    try:
        if method == "bl_returns" and returns_history is not None:
            weights = _bl_returns_path(macro_view, prior, returns_history, cov_override=cov_override)
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


# IC1 대안C(R10 수렴): study 세분 sleeve → 배분 sleeve cov-공간 roll-up 비중.
# cov 가산성(Cov(Σwᵢxᵢ, y)=Σwᵢ Cov(xᵢ,y))으로 factor cancel·sign-flip 방어(beta 가중평균 금지).
# 미매핑 배분 sleeve(kr_stock=eq_kr superseded / bond·cash·coin=betas 부재) = eye 독립.
# eq_intl·reit betas = 배분 자산군 부재 → drop(us_stock 에 안 섞음, R10).
SLEEVE_AGG = {
    "us_stock": {"eq_us_cyclical": 0.5, "eq_us_defensive": 0.5},  # 초기 eq-weight(시총 가중은 후속)
    "commodity": {"commodity": 1.0},
    "gold": {"gold": 1.0},
}

# IC2 — factor static 장기 Λ(HL250, FRED 레벨) 하루 단위 캐시. 매 allocate FRED fetch 회피.
# gate-Λ(EWMA 75d, risk_gate cross_cov)와 분리된 윈도우(§11 IC2 함정: static·reactive 격리).
_STATIC_LAMBDA_CACHE: dict = {}


def _static_factor_lambda(nf, factors, as_of=None):
    """factor 레벨(FRED) → static 장기 Λ(F,F). 실패/shape 불일치 → np.eye(nf)(무회귀 fallback).

    Λ=I 이면 IC1 기존 동작(factor 등분산·무상관, byte-identical)과 동일. 실 Λ 주입 시 cross-sleeve
    corr_prior magnitude 를 factor 실측 공분산으로 채움(cov2corr 후 corr 만 추출 → 절대분산 박제 X,
    eb_shrink lam 이 prior 비중 제어). FRED 키/네트워크 부재 → None → eye → IC1 폴백.
    """
    import datetime
    key = str(as_of) if as_of is not None else datetime.date.today().isoformat()
    if key not in _STATIC_LAMBDA_CACHE:
        Lam = None
        try:
            from core.data.factor_returns import fetch_factor_cov
            Lam = fetch_factor_cov(as_of=as_of, factors=list(factors))
        except Exception:
            Lam = None
        _STATIC_LAMBDA_CACHE[key] = Lam
    Lam = _STATIC_LAMBDA_CACHE[key]
    if Lam is None:
        return np.eye(nf)
    Lam = np.asarray(Lam, float)
    if Lam.shape != (nf, nf):
        return np.eye(nf)
    return Lam


def _ic_corr_prior(cols, as_of=None, *, fx_hedge="none"):
    """IC1 — 세분 SEED betas → factor_implied_cross_cov(static Λ) → ★W roll-up(cov 공간) →
    cov2corr 한 배분 sleeve corr_prior(magnitude FREEZE 보수 prior, §1.2-1/§11 IC1/§13 R10 대안C).

    factor 등분산·무상관(점추정 magnitude 박제 회피). 세분 unit 에서 cov 산출 후
    `Σ_alloc = W·Σ_fine·Wᵀ`(SLEEVE_AGG) 로 배분 차원 roll-up — beta 가중평균 금지(sign-flip 방어).
    미매핑 배분 sleeve = eye 독립. static SEED 기반이라 belief 무관 → firewall 불요(§1.2-1).
    opt-in(INV_R15_WEIGHTS) off → None → RegimeGlasso np.eye(byte-identical). 실패 시 None.
    eb_shrink lam(=n0/(n0+n_eff)) 이 prior 비중 제어. cols 순서 = 반환 corr 행/열 순서(정렬 일관성).

    ★IC8 fx_hedge: "none"(기본)=fx denomination factor 활성(KRW 투자자 USD자산 환노출 공통채널) /
        "full"=fx_β:=0(완전 환헤지). gold decoupling(IC10) 보호 — gold fx_β 부분(+0.3)+idio 흡수로 영향 미미.
    """
    try:
        from core.study.study_register import is_r15_enabled
        if not is_r15_enabled():
            return None
        from core.study.factor_betas_seed import build_seed_betas, FACTORS
        from core.study.system_priors import factor_implied_cross_cov
        sb = build_seed_betas(fx_hedge=fx_hedge)
        nf = len(FACTORS)
        fine = list(sb.betas.keys())
        if not fine:
            return None
        # IC2: static Λ 주입(실패 시 eye → IC1 동작). idio 도 βᵀΛβ 로 매칭(systematic 과 동일 스케일 →
        # off-diag corr 가 idio 에 묻혀 0 으로 죽는 것 방지, 발견 C 회귀 방어). Λ=I 면 βᵀβ 와 동일.
        Lam = _static_factor_lambda(nf, FACTORS, as_of=as_of)
        idio = {s: max(float(sb.betas[s] @ Lam @ sb.betas[s]), 1e-6) for s in fine}
        res = factor_implied_cross_cov(sb.betas, Lam, factors=list(FACTORS), idio_var=idio)
        fine_cov = np.asarray(res.cov, float)
        fidx = {s: i for i, s in enumerate(res.sleeves)}
        n = len(cols)
        W = np.zeros((n, len(res.sleeves)))
        for i, c in enumerate(cols):
            for fs, w in SLEEVE_AGG.get(c, {}).items():
                if fs in fidx:
                    W[i, fidx[fs]] = w
        alloc = W @ fine_cov @ W.T                          # 배분 cov (cov 공간 roll-up)
        for i in range(n):                                  # 미매핑 sleeve = eye 독립(대각 0 → 1)
            if alloc[i, i] <= 1e-12:
                alloc[i, i] = 1.0
        dd = np.sqrt(np.diag(alloc))
        corr = alloc / np.outer(dd, dd)
        corr = 0.5 * (corr + corr.T)
        np.fill_diagonal(corr, 1.0)
        return corr
    except Exception:
        return None


def _belief_conditional_cov(returns_history, sleeve_regime_ids, belief, labels, as_of=None):
    """슬리브 returns + 시점별 regime id + belief → regime-conditional belief-mixed Σ_eff (④ 핵심).

    RegimeGlasso.fit(슬리브 수익률 matrix, regime_ids) → effective_precision(models, belief_by_id)
    → Σ_eff(belief 가중 regime-conditional 공분산). BL cov_matrix 로 주입(_bl_returns_path).
    반환 = (cols, Σ_eff) 또는 substrate 부족/실패 시 None(호출자 Ledoit-Wolf 폴백).

    정합: belief(label→prob) → belief_by_id(int id→prob), id = labels.index = regime_id_series 규약.
    학습된 regime(models_)과 belief 교집합만 사용(미적합 regime 은 자동 제외).
    """
    try:
        from core.structure.conditional_correlation import RegimeGlasso, effective_precision
    except Exception:
        return None
    cols = [s for s in SLEEVES if s in getattr(returns_history, "columns", [])]
    if len(cols) < 2:
        return None
    sub = returns_history[cols]
    valid = ~sub.isna().any(axis=1)
    X = sub[valid].values
    ids = np.asarray(sleeve_regime_ids, int)
    if len(ids) != len(returns_history):
        return None
    ids_v = ids[valid.values]
    keep = ids_v >= 0                                 # 미지 regime(-1) 제외.
    X = X[keep]
    ids_v = ids_v[keep]
    if len(X) < 20:                                   # regime 당 min_obs=10 × 2 regime 하한.
        return None
    cp = _ic_corr_prior(cols, as_of=as_of)            # IC1/IC7: SEED corr_prior, static Λ as_of PIT(off=None)
    try:
        rg = RegimeGlasso(min_obs=10, corr_prior=cp).fit(X, ids_v)
    except Exception:
        return None                                   # 적합 regime 없음 등 → 폴백.
    label_to_id = {lab: i for i, lab in enumerate(labels)}
    belief_by_id = {}
    for lab, prob in belief.items():
        rid = label_to_id.get(lab)
        if rid is not None and rid in rg.models_:
            belief_by_id[rid] = float(prob)
    if not belief_by_id:
        return None
    try:
        res = effective_precision(rg.models_, belief_by_id)
    except Exception:
        return None
    return cols, res.Sigma_eff


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
def _bl_returns_path(macro_view: MacroView, prior: dict, returns_history: pd.DataFrame,
                     cov_override=None) -> dict:
    """
    정통 BL: IC Prior weights → implied returns(π) 역산 → stance 를 absolute view 로 →
    BlackLittermanModel → posterior returns → max-Sharpe weights.

    PyPortfolioOpt 계약(black_litterman.py):
      BlackLittermanModel(cov_matrix, pi=π, absolute_views={asset: ret},
                          omega="idzorek", view_confidences=[...], tau).bl_weights()

    cov_override = (cols, Σ_eff): ④ belief 동적 공분산. 제공 시 Ledoit-Wolf 대신 regime-conditional
    belief-mixed Σ_eff 를 BL 공분산으로 사용(누락 슬리브 있거나 비PD 시 Ledoit-Wolf 로 graceful).
    """
    from pypfopt import black_litterman, risk_models
    from pypfopt.efficient_frontier import EfficientFrontier

    cols = [s for s in SLEEVES if s in returns_history.columns]
    if len(cols) < 2:
        raise ValueError("returns_history insufficient for BL")
    rh = returns_history[cols].dropna()

    # 공분산: ④ belief 동적 Σ_eff override 우선, 아니면 Ledoit-Wolf (H25).
    S = None
    if cov_override is not None:
        ov_cols, sigma_eff = cov_override
        try:
            S_df = pd.DataFrame(sigma_eff, index=list(ov_cols), columns=list(ov_cols))
            S_df = S_df.reindex(index=cols, columns=cols)
            if not S_df.isna().any().any():
                S = S_df
        except Exception:
            S = None
    if S is None:
        S = risk_models.CovarianceShrinkage(rh, returns_data=True).ledoit_wolf()

    # 스케일 정합: cov(주기 수익률)·implied π 를 연율화. view(연 5%)·rf(연 2%)·δ 가 연율 가정이라
    # 주기 cov 를 그대로 쓰면 π≪rf → tangency 부재 → max_sharpe infeasible → fallback(belief cov
    # 효과 소실). returns_history 인덱스 간격으로 periods/year 추정 후 Σ·π 를 연율 공간으로 올린다.
    S = S * _periods_per_year(returns_history)

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
def _periods_per_year(returns_history) -> float:
    """returns_history 인덱스 간격으로 연간 관측수 추정 (cov 연율화 스케일). 일별≈252, 주간≈52,
    월간≈12. DatetimeIndex 아니거나 추정 불가 시 일별(252) 기본. BL rf/view 연율 정합용."""
    try:
        idx = getattr(returns_history, "index", None)
        if isinstance(idx, pd.DatetimeIndex) and len(idx) > 2:
            avg_days = (idx[-1] - idx[0]).days / (len(idx) - 1)
            if avg_days > 0:
                return float(np.clip(365.25 / avg_days, 1.0, 365.0))
    except Exception:
        pass
    return 252.0


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
