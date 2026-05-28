"""stock/factor_attribution.py — 사후 factor 귀속 + 메타라벨링 (G3 / §5.9-B / §5.8-H).

임무 1 (factor 귀속): 종료된(또는 G9 미청산) 거래의 수익을 market-β + 섹터 + idiosyncratic
회귀(2~3 팩터 상한)로 분해해 failure_reason enum 을 산출한다.
  β지배 → MACRO_REGIME_WRONG / 섹터지배 → SECTOR_THEME_WRONG /
  idio지배(value 가설) → VALUE_TRAP / 잔차 → EXECUTION_SLIPPAGE.
  저신뢰(노이즈 β·소표본) → UNATTRIBUTED (억지 라벨 금지).

임무 2 (메타라벨링): MlFinLab López de Prado 메타라벨링을 value 신호 레이어에 어댑트.
  1차 모델(=value_trigger 신호)이 side(방향)를 정하면, 2차 모델이 triple-barrier 결과
  bin∈{0,1}(베팅 채택/패스)을 학습 → 함정확률 → 억제/사이징.
  → §5.8-H (a) value-trap 루프에 연결 (value_trigger 가 MetaLabeler 로 주입받음).

코드화한 출처:
- MlFinLab `mlfinlab/labeling/labeling.py`:
    - get_events / apply_pt_sl_on_t1 / barrier_touched / get_bins 의 *계약*
      (side_prediction → bin∈{0,1} 메타라벨, pt_sl 2-원소 배리어, target=일변동성).
      공개판은 본문이 stub(pass) 라 docstring 계약만 신뢰 — triple-barrier 본 로직을
      여기서 자체 구현(numpy/pandas 의존 최소화, 표준 라이브러리로).
    - 메타라벨 핵심: "primary 가 side, secondary 가 size(0/1 확률)" → MetaLabeler.
- IMPLEMENTATION_PROMPT G3/§5.9-B: factor 귀속 enum·tiered minimal(주식 market-β+섹터+
  idio / 코인 market-β+idio)·상한 2~3 팩터·저신뢰 unattributed·G9 mark-to-market.
- quant.md Fama-French/AQR: market(MKT)·HML(value)·섹터 노출 회귀 → β 분해 토대.
- quant.md triple-barrier: 상단 익절/하단 손절/수직 만료 + σ 동적 배리어 → 메타라벨 라벨링.

코드화 못 한 것:
- numpy/sklearn 의존 회귀(OLS)는 여기서 최소제곱을 표준 라이브러리로 직접 구현
  (정규방정식). 대규모는 추후 numpy 로 교체 가능(인터페이스 동일).
- 2차 모델 학습기(실제 분류기 fit)는 SecondaryModel 프로토콜로 경계만. 본 모듈은
  라벨 생성(triple-barrier) + 회귀 분해 + 함정확률 *추론* 인터페이스 제공.

미해결 가정:
- 섹터 인덱스 수익률(SECTOR factor)은 데이터 레이어 주입. 없으면 market+idio 2팩터로
  degrade (코인과 동일 ⓑ-lite, "깨끗한 팩터 모델 없는 척 안 함").
- β지배/섹터지배/idio지배 판정 임계는 튜닝값 (설명분산 비중 기준).
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Optional, Sequence, Protocol, List

from stock.contracts import (
    FailureReason,
    AttributionResult,
    ValuationResult,
    Fundamentals,
)


# ===========================================================================
# PART 1. Factor 귀속 회귀 (G3 / §5.9-B)
# ===========================================================================

def _ols_multifactor(
    y: Sequence[float],
    factors: Sequence[Sequence[float]],
) -> Optional[dict]:
    """다요인 OLS (정규방정식). 표준 라이브러리만.

    y: 자산 초과수익 시계열 (길이 T).
    factors: 각 팩터 수익 시계열 리스트 [[f1_t...], [f2_t...], ...] (각 길이 T).
    반환 {betas: [...], r2: float, explained_var: [factor별 설명분산 비중], residual_var}.
    소표본/특이행렬 → None (저신뢰 → UNATTRIBUTED).
    """
    T = len(y)
    k = len(factors)
    if T < max(2 * k + 2, 8):       # 최소 표본: 팩터당 충분한 자유도
        return None
    for f in factors:
        if len(f) != T:
            return None

    # 설계행렬 X = [1, f1, f2, ...] (절편 포함)
    X = [[1.0] + [factors[j][t] for j in range(k)] for t in range(T)]
    p = k + 1

    # X^T X (p×p), X^T y (p)
    XtX = [[0.0] * p for _ in range(p)]
    Xty = [0.0] * p
    for t in range(T):
        for i in range(p):
            Xty[i] += X[t][i] * y[t]
            for j in range(p):
                XtX[i][j] += X[t][i] * X[t][j]

    beta = _solve_linear(XtX, Xty)
    if beta is None:
        return None

    # 예측·잔차
    y_mean = sum(y) / T
    ss_tot = sum((yt - y_mean) ** 2 for yt in y)
    ss_res = 0.0
    for t in range(T):
        pred = sum(beta[i] * X[t][i] for i in range(p))
        ss_res += (y[t] - pred) ** 2
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # 각 팩터의 설명분산 기여 (betas[1:] × cov(factor, y) 근사)
    explained = []
    for j in range(k):
        fj = factors[j]
        fj_mean = sum(fj) / T
        cov = sum((fj[t] - fj_mean) * (y[t] - y_mean) for t in range(T)) / T
        explained.append(abs(beta[j + 1] * cov))
    total_expl = sum(explained)
    explained_share = [e / total_expl if total_expl > 0 else 0.0 for e in explained]

    return {
        "betas": beta[1:],          # 절편 제외 (market, sector, ...)
        "alpha": beta[0],
        "r2": r2,
        "explained_share": explained_share,
        "residual_var": ss_res / T,
    }


def _solve_linear(A: List[List[float]], b: List[float]) -> Optional[List[float]]:
    """가우스 소거 (부분 피벗). 특이행렬 → None."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-12:
            return None
        M[col], M[piv] = M[piv], M[col]
        pivot = M[col][col]
        for j in range(col, n + 1):
            M[col][j] /= pivot
        for r in range(n):
            if r != col and abs(M[r][col]) > 1e-12:
                factor = M[r][col]
                for j in range(col, n + 1):
                    M[r][j] -= factor * M[col][j]
    return [M[i][n] for i in range(n)]


class AttributionConfig:
    """factor 귀속 임계 (튜닝값). 상한 2~3 팩터 (§5.9-B over-engineering 회피선)."""
    dominance_threshold: float = 0.5      # 단일 팩터 설명분산 비중 >= 50% = 지배
    min_r2_for_attribution: float = 0.3   # r2 미달 = 저신뢰 → UNATTRIBUTED
    residual_dominance: float = 0.6       # 잔차가 설명분산보다 크면 EXECUTION_SLIPPAGE


def attribute_trade(
    trade_id: str,
    ticker: str,
    holding_returns: Sequence[float],     # 보유기간 자산 (초과)수익 시계열
    market_returns: Sequence[float],      # market-β 팩터 (KOSPI/KOSDAQ/S&P)
    sector_returns: Optional[Sequence[float]] = None,  # 섹터 팩터 (없으면 2팩터 degrade)
    holding_return_total: Optional[float] = None,
    status: str = "closed",
    is_provisional: bool = False,
    config: AttributionConfig = AttributionConfig(),
) -> AttributionResult:
    """단일 거래의 factor 귀속. failure_reason enum + attribution JSONB 산출.

    분해→enum 매핑 (§5.9-B):
      market-β 지배 → MACRO_REGIME_WRONG
      섹터 지배     → SECTOR_THEME_WRONG
      idio(잔차 內 종목특이) 지배 → VALUE_TRAP (value 가설 실패)
      순수 잔차(설명 안 됨) 지배 → EXECUTION_SLIPPAGE
      저신뢰(r2 낮음·소표본·특이행렬) → UNATTRIBUTED

    저신뢰=unattributed: 억지 라벨 금지 (노이즈 β 가 매매를 직접 망치진 않음).
    """
    total_ret = holding_return_total
    if total_ret is None:
        total_ret = sum(holding_returns)

    # 팩터 구성 (코인은 sector 없음 → ⓑ-lite 2팩터)
    factors: List[Sequence[float]] = [market_returns]
    factor_names = ["market_beta"]
    if sector_returns is not None and len(sector_returns) == len(market_returns):
        factors.append(sector_returns)
        factor_names.append("sector")

    fit = _ols_multifactor(holding_returns, factors)

    # 소표본/특이행렬(fit=None) → 진짜 UNATTRIBUTED (β 노이즈, 억지 라벨 금지)
    if fit is None:
        return AttributionResult(
            trade_id=trade_id,
            ticker=ticker,
            failure_reason=FailureReason.UNATTRIBUTED,
            attribution={
                "reason": "저신뢰(소표본/특이행렬 — 회귀 불가)",
                "r2": None,
                "factors_used": factor_names,
            },
            confidence=0.0,
            holding_return=total_ret,
            status=status,
            is_provisional=is_provisional,
        )

    # low r2 의 의미 분기 (중요):
    #   r2 가 낮다 = market/섹터로 설명 안 됨 = idiosyncratic 지배 가능성.
    #   표본은 충분(fit 성공)하므로, 손실이 유의미하면 이는 UNATTRIBUTED 가 아니라
    #   VALUE_TRAP(종목특이 thesis 붕괴) 또는 EXECUTION_SLIPPAGE(순수 잔차) 후보다.
    #   단 손실이 미미하면(노이즈 수준) 억지 라벨 금지 → UNATTRIBUTED.
    if fit["r2"] < config.min_r2_for_attribution:
        if abs(total_ret) < 0.02:   # 손실/이익 미미 → 라벨 무의미
            return AttributionResult(
                trade_id=trade_id, ticker=ticker,
                failure_reason=FailureReason.UNATTRIBUTED,
                attribution={"reason": "저r2 + 손익 미미", "r2": round(fit["r2"], 4),
                             "factors_used": factor_names},
                confidence=fit["r2"], holding_return=total_ret,
                status=status, is_provisional=is_provisional,
            )
        # 유의미한 손실인데 factor 로 설명 안 됨 → idio 지배. value 가설 손실이면
        # VALUE_TRAP, market/섹터 베타가 거의 0 이고 잔차만 크면 EXECUTION_SLIPPAGE.
        # 아래 공통 지배 판정으로 흘려보낸다 (idio_share 가 자연히 지배).

    shares = dict(zip(factor_names, fit["explained_share"]))
    # idiosyncratic = 잔차 분산 비중 (전체 분산 대비 설명 안 된 부분)
    idio_share = max(0.0, 1.0 - fit["r2"])
    market_share = shares.get("market_beta", 0.0) * fit["r2"]
    sector_share = shares.get("sector", 0.0) * fit["r2"]

    attribution = {
        "market_beta": round(market_share, 4),
        "sector": round(sector_share, 4),
        "idiosyncratic": round(idio_share, 4),
        "alpha": round(fit["alpha"], 6),
        "betas": dict(zip(factor_names, [round(b, 4) for b in fit["betas"]])),
        "r2": round(fit["r2"], 4),
        "factors_used": factor_names,
    }

    # 지배 팩터 판정 (systematic factor: market vs sector)
    systematic = {
        FailureReason.MACRO_REGIME_WRONG: market_share,
        FailureReason.SECTOR_THEME_WRONG: sector_share,
    }
    dominant_sys = max(systematic, key=systematic.get)
    dominant_sys_share = systematic[dominant_sys]

    if dominant_sys_share >= config.dominance_threshold:
        # market 또는 섹터가 지배 → 거시/스타일 오판
        failure = dominant_sys
    elif idio_share >= config.residual_dominance:
        # idiosyncratic(종목특이) 지배 — VALUE_TRAP vs EXECUTION_SLIPPAGE 구분:
        #   체계적 음의 alpha(보유기간 전반 꾸준한 누수) = EXECUTION_SLIPPAGE,
        #   종목특이 thesis 붕괴(idio 손실 자체) = VALUE_TRAP.
        # alpha(절편, 일평균)가 idio 변동성 대비 크고 손실 방향이면 슬리피지/타이밍.
        idio_vol = math.sqrt(fit["residual_var"])
        alpha = fit["alpha"]
        if idio_vol > 0 and alpha < 0 and abs(alpha) > 0.5 * idio_vol and total_ret < 0:
            failure = FailureReason.EXECUTION_SLIPPAGE
        else:
            failure = FailureReason.VALUE_TRAP
    else:
        # 어떤 팩터도 명확히 지배하지 못함 → 신뢰 부족
        failure = FailureReason.UNATTRIBUTED

    return AttributionResult(
        trade_id=trade_id,
        ticker=ticker,
        failure_reason=failure,
        attribution=attribution,
        confidence=fit["r2"],
        holding_return=total_ret,
        status=status,
        is_provisional=is_provisional,
    )


# ===========================================================================
# PART 2. 메타라벨링 (MlFinLab 어댑트) — §5.8-H (a) value-trap
# ===========================================================================

def triple_barrier_label(
    entry_price: float,
    forward_prices: Sequence[float],
    volatility: float,
    k_up: float = 2.0,
    k_down: float = 1.0,
    side: int = 1,
) -> int:
    """triple-barrier 라벨. MlFinLab get_bins/barrier_touched 계약 + quant.md 수식.

    상단 익절 = entry·(1 + k_up·σ), 하단 손절 = entry·(1 - k_down·σ),
    수직 만료 = forward_prices 끝. 먼저 닿는 배리어로 라벨.

    side(1차 모델 방향)가 주어지면 메타라벨(bin∈{0,1}): pnl>0 → 1(베팅 성공), else 0.
    side 없으면(side=0) 가격행동 라벨 {-1,0,1}.

    quant.md: 추세추종 k_up=3σ/k_down=1σ, 평균회귀 k_up=1σ/k_down=2σ.
    value 트리거(역발상·평균회귀 성격)는 평균회귀 배리어가 기본.
    """
    if volatility <= 0:
        volatility = 0.02
    upper = entry_price * (1 + k_up * volatility)
    lower = entry_price * (1 - k_down * volatility)

    touched = 0   # 0 = 수직 만료
    for p in forward_prices:
        if p >= upper:
            touched = 1
            break
        if p <= lower:
            touched = -1
            break

    if side == 0:
        return touched   # 가격행동 라벨

    # 메타라벨: side 방향 기준 pnl
    final_price = forward_prices[-1] if forward_prices else entry_price
    if touched == 1:
        pnl = (upper - entry_price) * side
    elif touched == -1:
        pnl = (lower - entry_price) * side
    else:
        pnl = (final_price - entry_price) * side
    return 1 if pnl > 0 else 0


def daily_volatility(prices: Sequence[float], span: int = 20) -> float:
    """직근 일변동성(EWM 표준편차 근사). triple-barrier target. quant.md σ_t."""
    if len(prices) < 2:
        return 0.02
    rets = [(prices[i] / prices[i - 1] - 1.0) for i in range(1, len(prices)) if prices[i - 1] > 0]
    if not rets:
        return 0.02
    window = rets[-span:]
    mean = sum(window) / len(window)
    var = sum((r - mean) ** 2 for r in window) / len(window)
    return math.sqrt(var)


class SecondaryModel(Protocol):
    """메타라벨링 2차 모델 (실제 분류기 fit/predict). 외부 구현.

    fit(X, y): X=value 신호+피처, y=triple_barrier 메타라벨(0/1).
    predict_proba(x): 함정 아닐 확률(=베팅 성공 확률) → 1 - p = 함정확률.
    """

    def predict_trap_proba(self, features: dict) -> float:
        """함정(value-trap)일 확률 0~1 반환."""
        ...


class ValueTrapMetaLabeler:
    """value_trigger 가 주입받는 MetaLabeler 구현 (§5.8-H (a)).

    2차 모델(SecondaryModel)이 학습돼 있으면 그 함정확률을 쓰고, 없으면
    factor 귀속 통계(과거 VALUE_TRAP 빈도)로 휴리스틱 함정확률을 낸다.
    이것이 value_trigger.run_value_trigger(metalabeler=...) 로 연결된다.
    """

    def __init__(
        self,
        secondary_model: Optional[SecondaryModel] = None,
        prior_trap_rate: float = 0.3,
    ):
        self._model = secondary_model
        self._prior = prior_trap_rate    # 모델 없을 때 휴리스틱 prior

    def _features(
        self, valuation: ValuationResult, fundamentals: Sequence[Fundamentals]
    ) -> dict:
        """value 신호 + 펀더멘털 피처 (2차 모델 입력). quant.md 이익의 질 포함."""
        cur = fundamentals[0] if fundamentals else None
        feat = {
            "valuation_gap": valuation.valuation_gap,
            "wacc": valuation.wacc,
            "band_width": (valuation.bull_value - valuation.bear_value)
            / valuation.intrinsic_value if valuation.intrinsic_value else 0.0,
            "pit_clean": 1.0 if valuation.pit_clean else 0.0,
        }
        if cur:
            # 이익의 질: 영업이익 대비 FCF 괴리 (quant.md CFO vs 영업이익 2σ)
            if cur.operating_income and cur.operating_income != 0 and cur.free_cash_flow is not None:
                feat["fcf_to_oi"] = cur.free_cash_flow / cur.operating_income
            feat["debt_to_equity"] = (
                (cur.total_debt or 0.0) / cur.shareholders_equity
                if cur.shareholders_equity else None
            )
            feat["earnings_growth"] = cur.earnings_growth
        return feat

    def trap_probability(
        self,
        valuation: ValuationResult,
        fundamentals: Sequence[Fundamentals],
    ) -> float:
        """함정확률 0~1. value_trigger 가 1-p 로 사이징 (MetaLabeler 계약)."""
        feat = self._features(valuation, fundamentals)
        if self._model is not None:
            try:
                return min(max(self._model.predict_trap_proba(feat), 0.0), 1.0)
            except Exception:
                pass
        # 휴리스틱 fallback: 이익의 질 나쁘거나 부채 높으면 함정확률↑
        p = self._prior
        fcf_to_oi = feat.get("fcf_to_oi")
        if fcf_to_oi is not None and fcf_to_oi < 0.3:
            p += 0.25   # FCF 가 영업이익 대비 빈약 = 이익의 질 의심
        dte = feat.get("debt_to_equity")
        if dte is not None and dte > 2.0:
            p += 0.15
        eg = feat.get("earnings_growth")
        if eg is not None and eg < -0.1:
            p += 0.2    # 이익 역성장 = thesis 붕괴 가능성
        if not valuation.pit_clean:
            p += 0.1
        return min(max(p, 0.0), 1.0)


# ===========================================================================
# PART 3. 군집 분석 — 스타일 레짐 탐지 (§5.8-H (b))
# ===========================================================================

def detect_value_factor_regime(
    recent_attributions: Sequence[AttributionResult],
    cluster_threshold: float = 0.4,
) -> dict:
    """다수 종목 VALUE_TRAP *군집* = value 팩터 실패(스타일 레짐) 탐지 (§5.8-H (b)).

    idiosyncratic 아니라 systematic(value 스타일 out-of-favor) → value 트리거
    confidence 하향 권고. G3 factor 귀속 출력에 의존.

    반환 {value_trap_ratio, regime_unfavorable, recommended_confidence_haircut}.
    """
    closed = [a for a in recent_attributions if a.status == "closed" or a.is_provisional]
    if not closed:
        return {"value_trap_ratio": 0.0, "regime_unfavorable": False,
                "recommended_confidence_haircut": 0.0}

    trap_count = sum(1 for a in closed if a.failure_reason == FailureReason.VALUE_TRAP)
    ratio = trap_count / len(closed)
    unfavorable = ratio >= cluster_threshold
    # 군집 강도에 비례해 confidence haircut (스타일 레짐 caution, 예측기 아님)
    haircut = min((ratio - cluster_threshold) * 1.5, 0.5) if unfavorable else 0.0
    return {
        "value_trap_ratio": round(ratio, 3),
        "regime_unfavorable": unfavorable,
        "recommended_confidence_haircut": round(haircut, 3),
        "sample_size": len(closed),
    }
