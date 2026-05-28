"""stock/valuation.py — 내재가치 산출 (간이 DCF + 멀티플 밴드).

임무: 종목의 내재가치(밴드)를 산출해 value_trigger 의 "가치 갭" 입력을 제공한다.
PER/PBR/EV-EBITDA 멀티플 밴드 + 간이 다단계 DCF 를 확률가중으로 종합.

코드화한 출처:
- ai-hedge-fund `src/agents/valuation.py`:
    - calculate_enhanced_dcf_value / calculate_dcf_scenarios (다단계 성장 DCF + bear/base/bull)
    - calculate_wacc (CAPM 자기자본비용 + interest-coverage 부채비용)
    - calculate_ev_ebitda_value (median EV/EBITDA 멀티플 → 내재 EV → equity)
    - calculate_residual_income_value (Edwards-Bell-Ohlson RIM)
  → 위 함수들의 *수식*을 어댑트. 단 입력을 라이브 API 객체 대신 우리 PIT Fundamentals
    3-튜플로 받도록 시그니처를 재설계 (announcement-date PIT 강제, §5.7-A).
- ai-hedge-fund `src/agents/aswath_damodaran.py`:
    - calculate_intrinsic_value_dcf (FCFF DCF, growth fade-to-terminal)
    - estimate_cost_of_equity (CAPM r_f + β·ERP)
  → Damodaran "story→numbers→value" 의 numbers 부분(DCF·cost of equity)을 코드화.
    LLM narrative(generate_damodaran_output)는 value_trigger 2차 게이트로 분리.
- quant.md 기본적 분석:
    - Gordon 성장모형 V0 = D1/(r-g) → 터미널 가치 perpetuity 로 반영.
    - PEG = (P/E)/성장률 → multiple_band_signal 의 보조 신호.
    - PER/PBR/EV-EBITDA 멀티플 밴드 → 역사적 멀티플 분위로 fair-value 밴드.

코드화 못 한 것(명시):
- quant.md 기술적 지표(EMA/MACD/RSI/MFI/ADX/볼린저)·차트패턴(H&S 등)·페어트레이딩
  공적분: 가치(valuation) 모듈 범위 밖. 기술 신호는 별도 모듈(technicals)·코인 트랙이
  이미 보유(calculate_buy_score). 여기서는 *내재가치*만.
- "이익의 질"(CFO vs 영업이익 2σ 괴리, quant.md): quality_flag 로 훅만 남김(데이터
  파이프라인 확장 시 채움).

미해결 가정:
- 섹터 median 멀티플은 외부 유니버스 통계가 필요 → 없으면 종목 자기 역사 분위로 대체
  (ai-hedge-fund 와 동일한 fallback). sector_multiples 주입 시 그것을 우선.
- 통화 혼합 없음(단일 종목 단일 통화). 환산은 상위(FX, H26).
"""

from __future__ import annotations

import statistics
from datetime import datetime
from typing import Optional, Sequence, List

from stock.contracts import Fundamentals, MarketQuote, ValuationResult


# ---------------------------------------------------------------------------
# WACC / cost of equity (ai-hedge-fund calculate_wacc + Damodaran estimate_cost_of_equity)
# ---------------------------------------------------------------------------

def estimate_cost_of_equity(
    beta: Optional[float],
    risk_free_rate: float = 0.04,
    equity_risk_premium: float = 0.05,
) -> float:
    """CAPM: r_e = r_f + β·ERP. (Damodaran 장기 평균 default)."""
    b = beta if beta is not None else 1.0
    return risk_free_rate + b * equity_risk_premium


def calculate_wacc(
    market_cap: float,
    total_debt: Optional[float],
    cash: Optional[float],
    interest_coverage: Optional[float],
    beta: Optional[float] = None,
    risk_free_rate: float = 0.045,
    market_risk_premium: float = 0.06,
    tax_rate: float = 0.25,
) -> float:
    """가용 재무로 WACC 산출. ai-hedge-fund calculate_wacc 어댑트.

    cost of equity = CAPM. cost of debt = interest coverage 역수 스프레드.
    가중치 = market_cap vs net_debt. tax shield 적용. floor 6% / cap 20%.
    """
    cost_of_equity = estimate_cost_of_equity(beta, risk_free_rate, market_risk_premium)

    if interest_coverage and interest_coverage > 0:
        cost_of_debt = max(risk_free_rate + 0.01, risk_free_rate + (10.0 / interest_coverage))
    else:
        cost_of_debt = risk_free_rate + 0.05

    net_debt = max((total_debt or 0.0) - (cash or 0.0), 0.0)
    total_value = market_cap + net_debt
    if total_value > 0:
        w_e = market_cap / total_value
        w_d = net_debt / total_value
        wacc = w_e * cost_of_equity + w_d * cost_of_debt * (1.0 - tax_rate)
    else:
        wacc = cost_of_equity
    return min(max(wacc, 0.06), 0.20)


# ---------------------------------------------------------------------------
# 간이 다단계 DCF (ai-hedge-fund calculate_enhanced_dcf_value 어댑트)
# ---------------------------------------------------------------------------

def _fcf_volatility(fcf_history: Sequence[float]) -> float:
    """FCF 변동성(변동계수). 품질 조정 인자. ai-hedge-fund calculate_fcf_volatility."""
    pos = [f for f in fcf_history if f and f > 0]
    if len(pos) < 2:
        return 0.8
    mean = statistics.mean(pos)
    if mean <= 0:
        return 0.8
    try:
        return min(statistics.stdev(pos) / mean, 1.0)
    except statistics.StatisticsError:
        return 0.5


def enhanced_dcf_value(
    fcf_history: Sequence[float],
    wacc: float,
    market_cap: float,
    revenue_growth: Optional[float],
) -> float:
    """3단계 성장 DCF (고성장 1-3y → 전환 4-7y → 터미널). ai-hedge-fund 어댑트.

    Gordon 성장모형(quant.md V0=D1/(r-g))을 터미널 perpetuity 로 반영.
    품질 조정: FCF 변동성 높으면 가치 할인.
    """
    if not fcf_history or fcf_history[0] is None or fcf_history[0] <= 0:
        return 0.0

    fcf_current = fcf_history[0]
    fcf_avg3 = sum(fcf_history[:3]) / min(3, len(fcf_history))
    vol = _fcf_volatility(fcf_history)

    high_growth = min(revenue_growth or 0.05, 0.25) if revenue_growth else 0.05
    if market_cap > 50_000_000_000:        # large cap → 성장 캡
        high_growth = min(high_growth, 0.10)
    transition_growth = (high_growth + 0.03) / 2.0
    terminal_growth = min(0.03, high_growth * 0.6)

    base_fcf = max(fcf_current, fcf_avg3 * 0.85)   # 보수적 base
    pv = 0.0
    # 고성장 1-3년
    for yr in range(1, 4):
        pv += base_fcf * (1 + high_growth) ** yr / (1 + wacc) ** yr
    # 전환 4-7년 (성장 체감)
    for yr in range(4, 8):
        rate = transition_growth * (8 - yr) / 4.0
        proj = base_fcf * (1 + high_growth) ** 3 * (1 + rate) ** (yr - 3)
        pv += proj / (1 + wacc) ** yr
    # 터미널 (perpetuity, Gordon)
    final_fcf = base_fcf * (1 + high_growth) ** 3 * (1 + transition_growth) ** 4
    if wacc <= terminal_growth:
        terminal_growth = wacc * 0.8
    tv = final_fcf * (1 + terminal_growth) / (wacc - terminal_growth)
    pv_terminal = tv / (1 + wacc) ** 7

    quality_factor = max(0.7, 1 - vol * 0.5)
    return (pv + pv_terminal) * quality_factor


def dcf_scenarios(
    fcf_history: Sequence[float],
    wacc: float,
    market_cap: float,
    revenue_growth: Optional[float],
) -> dict:
    """bear/base/bull 시나리오 DCF + 확률가중 기대값. ai-hedge-fund calculate_dcf_scenarios."""
    adj = {
        "bear": {"growth": 0.5, "wacc": 1.2},
        "base": {"growth": 1.0, "wacc": 1.0},
        "bull": {"growth": 1.5, "wacc": 0.9},
    }
    base_g = revenue_growth or 0.05
    results = {}
    for name, a in adj.items():
        results[name] = enhanced_dcf_value(
            fcf_history, wacc * a["wacc"], market_cap, base_g * a["growth"]
        )
    expected = results["bear"] * 0.2 + results["base"] * 0.6 + results["bull"] * 0.2
    return {
        "scenarios": results,
        "expected_value": expected,
        "downside": results["bear"],
        "upside": results["bull"],
        "range": results["bull"] - results["bear"],
    }


# ---------------------------------------------------------------------------
# 멀티플 밴드 (PER/PBR/EV-EBITDA) — quant.md AQR value 팩터 + ai-hedge-fund EV/EBITDA
# ---------------------------------------------------------------------------

def ev_ebitda_implied_equity(
    ebitda_now: float,
    ev_ebitda_multiples: Sequence[float],
    net_debt: float,
) -> float:
    """median EV/EBITDA 멀티플 → 내재 EV → equity. ai-hedge-fund calculate_ev_ebitda_value."""
    valid = [m for m in ev_ebitda_multiples if m and m > 0]
    if not valid or ebitda_now <= 0:
        return 0.0
    med = statistics.median(valid)
    ev_implied = med * ebitda_now
    return max(ev_implied - net_debt, 0.0)


def multiple_band(
    metric_now: float,
    historical_multiples: Sequence[float],
    low_pct: float = 0.25,
    high_pct: float = 0.75,
) -> Optional[dict]:
    """역사적 멀티플 분위로 fair-value 밴드 산출 (PER/PBR 공통).

    metric_now = 현재 펀더멘털 (예: EPS, BPS, EBITDA).
    historical_multiples = 과거 멀티플 시계열 (예: 과거 PER 들).
    반환 = {low, fair, high} fair value (멀티플 분위 × metric_now).
    quant.md AQR value 팩터의 "절대 저평가 순위" 아이디어를 자기-역사 밴드로 구현.
    """
    valid = sorted(m for m in historical_multiples if m and m > 0)
    if len(valid) < 3 or metric_now <= 0:
        return None

    def _quantile(data: List[float], q: float) -> float:
        idx = q * (len(data) - 1)
        lo = int(idx)
        hi = min(lo + 1, len(data) - 1)
        frac = idx - lo
        return data[lo] * (1 - frac) + data[hi] * frac

    return {
        "low": _quantile(valid, low_pct) * metric_now,
        "fair": statistics.median(valid) * metric_now,
        "high": _quantile(valid, high_pct) * metric_now,
    }


def peg_ratio(pe: Optional[float], earnings_growth_pct: Optional[float]) -> Optional[float]:
    """PEG = (P/E) / 이익성장률(%). quant.md: PEG<1.0 = 저평가 고성장 매수 신호."""
    if pe is None or not earnings_growth_pct or earnings_growth_pct <= 0:
        return None
    return pe / (earnings_growth_pct * 100.0)


# ---------------------------------------------------------------------------
# 종합: ValuationResult 산출
# ---------------------------------------------------------------------------

def value_stock(
    fundamentals: Sequence[Fundamentals],
    quote: MarketQuote,
    sector_ev_ebitda: Optional[Sequence[float]] = None,
) -> Optional[ValuationResult]:
    """PIT 펀더멘털 + 가격으로 내재가치 밴드 산출.

    fundamentals: PITFundamentalsAdapter.get_pit_fundamentals 의 출력 (최신순).
                  이미 announcement-date PIT 마스킹됨 (§5.7-A).
    quote: 현재 가격/시총.
    sector_ev_ebitda: 섹터 비교 멀티플(있으면 우선). 없으면 종목 자기 역사.

    반환 ValuationResult (intrinsic_value=확률가중, valuation_gap, bear/base/bull 밴드).
    데이터 부족 시 None.
    """
    if not fundamentals or len(fundamentals) < 1:
        return None
    cur = fundamentals[0]
    market_cap = quote.market_cap
    if not market_cap or market_cap <= 0:
        return None

    pit_clean = all(f.is_pit_clean() for f in fundamentals)
    notes: List[str] = []
    if not pit_clean:
        notes.append("일부 펀더멘털이 PIT-clean 아님 (restated 혼입 가능)")

    # --- WACC ---
    interest_coverage = None
    if cur.ebit and cur.interest_expense and cur.interest_expense != 0:
        interest_coverage = cur.ebit / abs(cur.interest_expense)
    wacc = calculate_wacc(
        market_cap=market_cap,
        total_debt=cur.total_debt,
        cash=cur.cash_and_equivalents,
        interest_coverage=interest_coverage,
        beta=cur.beta,
    )

    # --- DCF 시나리오 (밴드) ---
    fcf_history = [f.free_cash_flow for f in fundamentals if f.free_cash_flow is not None]
    dcf = dcf_scenarios(fcf_history, wacc, market_cap, cur.revenue_growth)

    method_values: dict = {}
    if dcf["expected_value"] > 0:
        method_values["dcf"] = {"value": dcf["expected_value"], "weight": 0.45}

    # --- EV/EBITDA 멀티플 ---
    if cur.ebitda and cur.ebitda > 0:
        net_debt = (cur.total_debt or 0.0) - (cur.cash_and_equivalents or 0.0)
        if sector_ev_ebitda:
            mults = list(sector_ev_ebitda)
        else:
            # 자기 역사: EV/EBITDA = (mcap+net_debt)/ebitda 를 과거 분기로 근사 불가하면
            # 현재 한 점만 → 밴드 의미 약함 → median 1점 사용
            mults = []
            for f in fundamentals:
                if f.ebitda and f.ebitda > 0:
                    fnd = (market_cap + ((f.total_debt or 0) - (f.cash_and_equivalents or 0))) / f.ebitda
                    if fnd > 0:
                        mults.append(fnd)
        ev_eq = ev_ebitda_implied_equity(cur.ebitda, mults, net_debt)
        if ev_eq > 0:
            method_values["ev_ebitda"] = {"value": ev_eq, "weight": 0.30}

    # --- Residual Income (PBR 기반) ---
    if cur.net_income and cur.book_value and cur.book_value > 0:
        rim = _residual_income_value(
            book_value=cur.book_value,
            net_income=cur.net_income,
            book_value_growth=cur.book_value_growth or 0.03,
            cost_of_equity=estimate_cost_of_equity(cur.beta),
        )
        if rim > 0:
            method_values["residual_income"] = {"value": rim, "weight": 0.25}

    if not method_values:
        notes.append("유효한 밸류에이션 메서드 없음 (FCF/EBITDA/순이익 부족)")
        return None

    # --- 가중 종합 ---
    total_w = sum(v["weight"] for v in method_values.values())
    for v in method_values.values():
        v["gap"] = (v["value"] - market_cap) / market_cap
    intrinsic = sum(v["weight"] * v["value"] for v in method_values.values()) / total_w
    valuation_gap = (intrinsic - market_cap) / market_cap

    # 밴드: DCF bear/base/bull 을 전체 메서드 비율로 스케일 (DCF 없으면 ±30% 폭)
    if "dcf" in method_values and dcf["expected_value"] > 0:
        scale = intrinsic / dcf["expected_value"]
        bear = dcf["downside"] * scale
        bull = dcf["upside"] * scale
    else:
        bear = intrinsic * 0.7
        bull = intrinsic * 1.3

    return ValuationResult(
        ticker=quote.ticker,
        as_of=quote.as_of,
        currency=cur.currency,
        intrinsic_value=intrinsic,
        market_cap=market_cap,
        valuation_gap=valuation_gap,
        bear_value=bear,
        base_value=intrinsic,
        bull_value=bull,
        wacc=wacc,
        method_values=method_values,
        pit_clean=pit_clean,
        fundamentals_period=cur.fiscal_period,
        notes=notes,
    )


def _residual_income_value(
    book_value: float,
    net_income: float,
    book_value_growth: float,
    cost_of_equity: float,
    terminal_growth_rate: float = 0.03,
    num_years: int = 5,
    margin_of_safety: float = 0.20,
) -> float:
    """Edwards-Bell-Ohlson RIM. ai-hedge-fund calculate_residual_income_value 어댑트.

    여기서는 book_value 를 직접 입력받는다 (PIT Fundamentals.book_value).
    """
    ri0 = net_income - cost_of_equity * book_value
    if ri0 <= 0:
        return 0.0
    pv_ri = 0.0
    for yr in range(1, num_years + 1):
        ri_t = ri0 * (1 + book_value_growth) ** yr
        pv_ri += ri_t / (1 + cost_of_equity) ** yr
    if cost_of_equity <= terminal_growth_rate:
        terminal_growth_rate = cost_of_equity * 0.8
    term_ri = ri0 * (1 + book_value_growth) ** (num_years + 1) / (cost_of_equity - terminal_growth_rate)
    pv_term = term_ri / (1 + cost_of_equity) ** num_years
    intrinsic = book_value + pv_ri + pv_term
    return intrinsic * (1 - margin_of_safety)
