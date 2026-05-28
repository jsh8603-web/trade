"""
macro_indicators.py — macro.md 리서치의 정량 지표·임계·법칙을 *실제 동작 코드*로 구현.

이 모듈이 macro.md 의 핵심 임무다 — 리서치의 수치/임계/방법론을 코드화한다.
각 함수는 PIT-safe(발표일 정렬된 시계열만 받음) + 순수함수(외부 IO 없음) 로 설계 →
FRED 어댑터(아래 fred_adapter.py)가 데이터를 공급하면 그대로 동작한다.

코드화한 macro.md 라인(근거):
- Michez Rule (미셰즈 법칙)        : macro.md 라인 157~186, 215 (Michaillat-Saez FERU u*=√uv).
    이중 임계 0.29%p / 0.81%p, m(t)=min(û, v̂). Sahm 의 공급충격 취약성 보완 = 최종 침체 앵커.
- Sahm Rule (삼의 법칙)            : macro.md 라인 158, 205~208 (실업률 3MA - 12M최저 ≥ 0.50%p).
    단독 신뢰 금지(공급충격 왜곡), Michez 와 함께 본다.
- GDP-GDI 단절 크로스체크           : macro.md 라인 151~156, 216 (기술적 침체 오경보 차단).
- 장단기 금리차 (10Y-2Y) + 스티프닝 : macro.md 라인 129~136, 191~194 (역전 무력화, bear vs bull steepening).
- Truflation 선행 (고빈도 인플레)   : macro.md 라인 44~51, 213 (공식 CPI 10~75일 선행, 변동성 국면 확장).
- 금융스트레스/신용스프레드          : macro.md 라인 25~26(CP경색), §5.8-A 추가 피처(NFCI/STLFSI/GZ).

미해결 가정:
- Truflation 은 유료/API-키 필요 → 인터페이스만; 없으면 None 반환하고 분류기는 코어CPI 폴백.
- 임계치(0.29/0.81/0.50)는 논문 고정값. 우리 백테스트(2018+) 로 재튜닝하면 caution 메모리(§5.8-H)에 기록.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 1. Michez Rule (미셰즈 법칙) — 최종 침체 앵커 (macro.md 215, 라인 157~186)
# ---------------------------------------------------------------------------
@dataclass
class MichezResult:
    m_value: float            # m(t) = min(û, v̂), 단위 %p
    u_hat: float              # 실업률 3MA 의 12M 최저 대비 상승폭 (%p)
    v_hat: float              # 구인율 3MA 의 12M 최고 대비 하락폭 (%p)
    state: str                # "expansion" | "probable_recession" | "certain_recession"
    recession_prob: float     # 이중 임계 보간 확률 [0,1]


# 논문 고정 임계 (Michaillat-Saez 2024, macro.md 라인 184).
MICHEZ_LOWER = 0.29   # %p — 이 아래면 "노동 유휴화 제로 건전 균형".
MICHEZ_UPPER = 0.81   # %p — 이 위면 "100% 확정 침체".


def michez_rule(
    unemployment_rate: pd.Series,   # 월별 실업률 (%), 발표일 인덱스 (PIT).
    vacancy_rate: pd.Series,        # 월별 구인율 (%) = JOLTS job openings / labor force.
) -> Optional[MichezResult]:
    """
    미셰즈 법칙 m(t) = min( û(t), v̂(t) ) 을 계산한다 (macro.md 라인 169~186).

      û(t) = 실업률 3개월 평균 - 직전 12개월 실업률 3MA 의 최저치   (상승폭, 클수록 악화)
      v̂(t) = 직전 12개월 구인율 3MA 의 최고치 - 구인율 3개월 평균   (하락폭, 클수록 악화)

    이민 공급충격으로 û 가 치솟아도 v̂(구인 유지)가 작으면 min 이 작아 → 오경보 차단.
    이중 장벽(0.29 / 0.81)으로 expansion / probable / certain 3단 판정.
    """
    if len(unemployment_rate) < 15 or len(vacancy_rate) < 15:
        return None  # 12M 최저/최고 + 3MA 산출에 최소 15개월 필요.

    u_3ma = unemployment_rate.rolling(3).mean()
    v_3ma = vacancy_rate.rolling(3).mean()

    # 직전 12개월(현재 제외) 의 min/max 기준선.
    u_min_12m = u_3ma.shift(1).rolling(12).min().iloc[-1]
    v_max_12m = v_3ma.shift(1).rolling(12).max().iloc[-1]
    if pd.isna(u_min_12m) or pd.isna(v_max_12m):
        return None

    u_hat = float(u_3ma.iloc[-1] - u_min_12m)      # 실업률 상승폭.
    v_hat = float(v_max_12m - v_3ma.iloc[-1])      # 구인율 하락폭.
    m_value = float(min(u_hat, v_hat))

    if m_value < MICHEZ_LOWER:
        state, prob = "expansion", _interp_prob(m_value, 0.0, MICHEZ_LOWER, 0.0, 0.10)
    elif m_value < MICHEZ_UPPER:
        state, prob = "probable_recession", _interp_prob(m_value, MICHEZ_LOWER, MICHEZ_UPPER, 0.10, 1.0)
    else:
        state, prob = "certain_recession", 1.0

    return MichezResult(m_value, u_hat, v_hat, state, float(np.clip(prob, 0.0, 1.0)))


def _interp_prob(x, x0, x1, p0, p1):
    if x1 == x0:
        return p1
    return p0 + (p1 - p0) * (x - x0) / (x1 - x0)


# ---------------------------------------------------------------------------
# 2. Sahm Rule (삼의 법칙) — 보조 (macro.md 라인 158, 205~208)
# ---------------------------------------------------------------------------
SAHM_THRESHOLD = 0.50  # %p


def sahm_rule(unemployment_rate: pd.Series) -> Optional[dict]:
    """
    실업률 3MA - 직전 12개월 3MA 최저 ≥ 0.50%p → 트리거 (macro.md 라인 158).
    공급충격(이민)에 취약하므로 단독 신뢰 금지 — michez 와 교차검증용.
    """
    if len(unemployment_rate) < 15:
        return None
    u_3ma = unemployment_rate.rolling(3).mean()
    u_min_12m = u_3ma.shift(1).rolling(12).min().iloc[-1]
    if pd.isna(u_min_12m):
        return None
    spread = float(u_3ma.iloc[-1] - u_min_12m)
    return {"sahm_spread": spread, "triggered": spread >= SAHM_THRESHOLD}


# ---------------------------------------------------------------------------
# 3. GDP vs GDI 크로스체크 — 기술적 침체 오경보 차단 (macro.md 라인 151~156, 216)
# ---------------------------------------------------------------------------
def gdp_gdi_divergence(
    real_gdp_qoq: pd.Series,   # 분기 실질 GDP 전기대비 연율 (%).
    real_gdi_qoq: pd.Series,   # 분기 실질 GDI 전기대비 연율 (%).
) -> Optional[dict]:
    """
    2022 상반기처럼 GDP 2분기 연속 마이너스(기술적 침체)인데 GDI 는 정상 확장이면
    "지출측 무역/재고 왜곡" 으로 보고 침체 오경보를 차단한다 (macro.md 라인 153~156).
    반환 technical_recession=True 이지만 divergence_warning=True 면 침체 단정 보류.
    """
    if len(real_gdp_qoq) < 2 or len(real_gdi_qoq) < 2:
        return None
    g2 = real_gdp_qoq.iloc[-2:]
    technical_recession = bool((g2 < 0).all())   # 2분기 연속 역성장.
    gdi_latest = float(real_gdi_qoq.iloc[-1])
    gdp_latest = float(real_gdp_qoq.iloc[-1])
    # GDP 음수인데 GDI 양수 = 통계적 노이즈 의심.
    divergence_warning = bool(gdp_latest < 0 < gdi_latest)
    return {
        "technical_recession": technical_recession,
        "divergence_warning": divergence_warning,
        "gdp_qoq": gdp_latest,
        "gdi_qoq": gdi_latest,
        # 순수 내수 체력 = 두 지표 평균 (BEA 도 평균치 GDPplus 발표).
        "gdpplus_proxy": float((gdp_latest + gdi_latest) / 2.0),
    }


# ---------------------------------------------------------------------------
# 4. 금리커브 — 역전 + 스티프닝 구분 (macro.md 라인 129~136, 214)
# ---------------------------------------------------------------------------
def yield_curve_signal(
    spread_10y_2y: pd.Series,   # 10Y-2Y 스프레드 (%p) 시계열.
    lookback: int = 60,         # 스티프닝 방향 판정 윈도우(영업일/관측치).
) -> Optional[dict]:
    """
    macro.md 핵심 통찰(라인 131~136): 역전 자체가 무조건 침체 직행이 아니다 (QE 가 term premium 왜곡).
    중요한 건 *역전 해소 단계의 방향성* — bear steepening(재정우려·장기금리↑) 은 약세 신호,
    bull steepening(완화기대·단기금리↓) 은 회복 신호.
    """
    if len(spread_10y_2y) < lookback:
        return None
    cur = float(spread_10y_2y.iloc[-1])
    prev = float(spread_10y_2y.iloc[-lookback])
    inverted = cur < 0.0
    steepening = cur > prev   # 스프레드 확대 = 스티프닝.
    flattening = cur < prev
    # bear/bull 구분은 단기금리 동반 필요 → 여기선 스프레드 방향만, 라벨은 reasoning 노드가 결합.
    if steepening and cur > 0:
        regime_hint = "steepening_recovery"   # 역전 해소 + 양(+) → bull steepening 후보.
    elif flattening and cur > 0:
        regime_hint = "flattening_late_cycle"
    elif inverted:
        regime_hint = "inverted_caution"
    else:
        regime_hint = "neutral"
    return {
        "spread_now": cur,
        "spread_change": cur - prev,
        "inverted": inverted,
        "steepening": steepening,
        "regime_hint": regime_hint,
    }


# ---------------------------------------------------------------------------
# 5. Truflation 선행 인플레 — 고빈도 대안지표 (macro.md 라인 44~51, 213)
# ---------------------------------------------------------------------------
def truflation_lead_signal(
    truflation_yoy: Optional[pd.Series],   # 일별 Truflation 전년대비 (%). None 가능(유료/미연동).
    official_cpi_yoy: Optional[float],     # 최신 공식 코어 CPI YoY (%).
    high_volatility: bool = False,         # 변동성 국면이면 선행폭 40~75일로 확장.
) -> Optional[dict]:
    """
    Truflation 이 공식 CPI 에 안정기 10~15일, 변동성 국면 40~75일 선행 (macro.md 라인 48).
    공식 CPI 와 큰 괴리 시(2026.02 예시: CPI 2.4% vs Truflation 0.7%) = 조기 전환 신호.
    데이터 미연동(None)이면 분류기는 공식 코어CPI 로 폴백.
    """
    if truflation_yoy is None or len(truflation_yoy) == 0:
        return None
    truf_now = float(truflation_yoy.iloc[-1])
    out = {
        "truflation_yoy": truf_now,
        "lead_days_est": 75 if high_volatility else 12,
        "divergence_signal": None,
    }
    if official_cpi_yoy is not None:
        gap = truf_now - official_cpi_yoy
        out["cpi_gap"] = gap
        # 1%p 이상 하방 괴리 = 공식지표가 인플레를 과장(disinflation 조기신호).
        if gap < -1.0:
            out["divergence_signal"] = "disinflation_early"
        elif gap > 1.0:
            out["divergence_signal"] = "inflation_early"
    return out


# ---------------------------------------------------------------------------
# 6. 성장×인플레 → Investment Clock 4분면 매핑 (분류기 코어)
# ---------------------------------------------------------------------------
def investment_clock_quadrant(growth_signal: float, inflation_signal: float):
    """
    성장신호(>0=상승) × 인플레신호(>0=상승) → 4분면 라벨 + 일치 신뢰도.

      growth>0, infl<=0 → RECOVERY
      growth>0, infl>0  → OVERHEAT
      growth<=0, infl<=0→ REFLATION
      growth<=0, infl>0 → STAGFLATION

    confidence = 두 신호 크기의 기하평균을 [0,1] 로 squash (경계 근처면 낮게 → reasoning 에스컬레이션).
    """
    from .macro_schema import RegimeLabel  # 지연 import (순환 회피).

    if growth_signal > 0 and inflation_signal <= 0:
        label = RegimeLabel.RECOVERY
    elif growth_signal > 0 and inflation_signal > 0:
        label = RegimeLabel.OVERHEAT
    elif growth_signal <= 0 and inflation_signal <= 0:
        label = RegimeLabel.REFLATION
    else:
        label = RegimeLabel.STAGFLATION

    mag = np.sqrt(abs(growth_signal) * abs(inflation_signal))
    confidence = float(np.clip(np.tanh(mag), 0.0, 1.0))
    return label, confidence
