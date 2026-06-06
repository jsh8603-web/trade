"""stock/value_trigger.py — 가치 2단 게이트 트리거 (§3 / Phase 3).

임무: "싸진 기회 vs thesis 붕괴 value-trap" 를 2단 게이트로 가른다.
  1차 게이트(저비용 Qwen 필터): 가격변동 X% AND 내재가치 갭(가격 < 내재가치의 Y%).
  2차 게이트(heavy agent, Claude/Damodaran 페르소나): value-trap 판정.
  통과분만 risk_gate 로 후보 전달.

⛔ 핵심 계약 — 단순 buy-the-dip 금지:
  가격↓ + 내재가치↓ 동반 = 매수 아님 (thesis 붕괴). 1차 게이트는 가격이 빠졌어도
  *내재가치 대비* 싸진 경우만 통과시키고, 가치가 같이 빠졌으면 2차에서 VALUE_TRAP.

코드화한 출처:
- IMPLEMENTATION_PROMPT §3/Phase3/§4: 2단(1차 Qwen 가격변동 AND 가치갭 → 2차
  Claude/Damodaran value-trap) → risk_gate. "가격만 빠진 vs 가치 갭 구분" 수용 기준.
- ai-hedge-fund `aswath_damodaran.py`: margin_of_safety(>=0.25 bullish) 판정 로직 +
  generate_damodaran_output 의 LLM "story→numbers→value" → 2차 게이트 heavy-agent
  프롬프트 계약으로 코드화 (HeavyAgent 프로토콜).
- ai-hedge-fund `stanley_druckenmiller.py`: asymmetric risk-reward 렌즈 → 2차 게이트의
  "기회 vs 함정" 판정에 보조 시그널(가치 갭 비대칭 보상).
- quant.md 기본적 분석: "이익의 질" 악화(CFO vs 영업이익 2σ 괴리) = thesis 붕괴 신호 →
  trap 판정 입력(quality_deterioration 훅).
- §5.8-H (a) value-trap 메타라벨링: 2차 모델이 함정확률 학습 → metalabel_size_factor
  로 억제/사이징. factor_attribution 의 메타라벨러를 주입받아 연결.

H22 경계 (코드에 반영):
- 2차 heavy-agent 는 백테스트에서 training-data lookahead 오염 → BACKTEST 모드에서
  abstain stub 으로 동작 (ValueVerdict.ABSTAIN). FORWARD 만 실제 판정.

미해결 가정:
- 1차 임계 X%(가격변동)·Y%(가치갭)는 튜닝값. 기본 X=10%, Y=내재가치의 80%(=gap>=0.25).
- HeavyAgent 구현체(실제 Claude 호출)는 외부. 여기서는 프로토콜 경계만.
- 내재가치 추세(value↓ 동반 판별)는 직전 ValuationResult 와 비교 — 히스토리 주입 시 정밀,
  없으면 단일 시점 + 펀더멘털 quality 플래그로 근사.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Protocol, Sequence

from stock.contracts import (
    ValuationResult,
    ValueTriggerResult,
    ValueVerdict,
    TriggerStage,
    RunMode,
    Fundamentals,
)


# ---------------------------------------------------------------------------
# 1차 게이트 임계 (튜닝값) — §3
# ---------------------------------------------------------------------------

class Gate1Thresholds:
    """1차 저비용 필터 임계. borderline 이면 강화(2.9 게이트 원칙)."""
    price_drop_pct: float = 0.10          # X%: 최근 윈도우 가격 하락 >= 10%
    valuation_gap_min: float = 0.25       # Y%: 가격 < 내재가치의 80% (gap >= 0.25)
    # 내재가치 동반 하락 판별 임계 (buy-the-dip 차단)
    value_decline_tolerance: float = -0.05  # 내재가치가 직전 대비 -5% 초과 하락 = 동반↓ 의심


# ---------------------------------------------------------------------------
# Heavy agent 경계 (2차 게이트) — Claude/Damodaran 페르소나
# ---------------------------------------------------------------------------

class HeavyAgentVerdict:
    """2차 heavy-agent 의 구조화 출력 (LLM → 우리 enum)."""

    def __init__(self, is_trap: bool, confidence: float, reasoning: str):
        self.is_trap = is_trap          # True = thesis 붕괴(value-trap), False = 싸진 기회
        self.confidence = confidence    # 0~1
        self.reasoning = reasoning


class HeavyAgent(Protocol):
    """2차 게이트 heavy-agent 경계 (Claude/Damodaran 페르소나 구현체).

    구현체는 §4.1 stateless 일회성 호출 + 컨텍스트 팩(현 시장·RAG recall·macro_view).
    Damodaran "story→numbers→value" + Druckenmiller asymmetric risk-reward 렌즈로
    "이 가격 하락이 싸진 기회인가, thesis 붕괴(value-trap)인가" 판정.
    """

    def judge_value_trap(
        self,
        valuation: ValuationResult,
        fundamentals: Sequence[Fundamentals],
        price_change_pct: Optional[float],
        context: dict,
    ) -> HeavyAgentVerdict:
        ...


class MetaLabeler(Protocol):
    """§5.8-H (a): value 신호 함정확률을 학습한 2차 모델 (메타라벨링).

    factor_attribution 의 메타라벨러가 이를 구현. value_trigger 는 그 함정확률로
    사이징(metalabel_size_factor)을 조절한다. 1차 모델(=value 신호)이 side 를 정하면
    2차 모델이 "이 신호+피처면 함정?" → 억제/사이징 (MlFinLab meta-labeling 계약).
    """

    def trap_probability(
        self,
        valuation: ValuationResult,
        fundamentals: Sequence[Fundamentals],
    ) -> float:
        """함정(value-trap)일 확률 0~1 반환. 높을수록 사이징 억제."""
        ...


# ---------------------------------------------------------------------------
# 1차 게이트 로직
# ---------------------------------------------------------------------------

def passes_gate1(
    valuation: ValuationResult,
    price_change_pct: Optional[float],
    prev_intrinsic_value: Optional[float] = None,
    thresholds: Gate1Thresholds = Gate1Thresholds(),
) -> tuple[bool, str]:
    """1차 저비용 필터: 가격변동 X% AND 내재가치 갭 Y%.

    ⛔ buy-the-dip 차단: 가격이 빠졌고(price_change<=-X) 가치 갭이 충분해도
       *내재가치가 같이 빠졌으면*(prev 대비 큰 하락) 통과시키되 trap 의심 플래그를
       2차로 넘긴다 (1차는 후보 수집, 2차가 trap 최종 판정).

    반환 (passed, reason).
    """
    # 조건 A: 가격이 충분히 빠졌나
    price_drop_ok = (
        price_change_pct is not None and price_change_pct <= -thresholds.price_drop_pct
    )
    # 조건 B: 내재가치 대비 싼가 (가격 < 내재가치의 (1-Y)... gap >= valuation_gap_min)
    gap_ok = valuation.valuation_gap >= thresholds.valuation_gap_min

    if not (price_drop_ok and gap_ok):
        reasons = []
        if not price_drop_ok:
            reasons.append(
                f"가격변동 미달(Δ={price_change_pct}, 임계 -{thresholds.price_drop_pct})"
            )
        if not gap_ok:
            reasons.append(
                f"가치갭 미달(gap={valuation.valuation_gap:.2f}, 임계 {thresholds.valuation_gap_min})"
            )
        return False, "; ".join(reasons)

    return True, f"가격 {price_change_pct:.1%} 하락 + 가치갭 {valuation.valuation_gap:.1%}"


def _value_declined_with_price(
    valuation: ValuationResult,
    prev_intrinsic_value: Optional[float],
    thresholds: Gate1Thresholds,
) -> bool:
    """내재가치가 가격과 동반 하락했는가 (buy-the-dip = 매수 아님 신호).

    prev_intrinsic_value 가 있으면 직접 비교, 없으면 False(2차가 펀더멘털로 판정).
    """
    if prev_intrinsic_value is None or prev_intrinsic_value <= 0:
        return False
    change = (valuation.intrinsic_value - prev_intrinsic_value) / prev_intrinsic_value
    return change < thresholds.value_decline_tolerance


# ---------------------------------------------------------------------------
# 2단 게이트 오케스트레이션 (핵심 진입점)
# ---------------------------------------------------------------------------

def run_value_trigger(
    valuation: ValuationResult,
    fundamentals: Sequence[Fundamentals],
    price_change_pct: Optional[float],
    heavy_agent: Optional[HeavyAgent] = None,
    metalabeler: Optional[MetaLabeler] = None,
    prev_intrinsic_value: Optional[float] = None,
    context: Optional[dict] = None,
    mode: RunMode = RunMode.FORWARD,
    thresholds: Gate1Thresholds = Gate1Thresholds(),
    heavy_agent_fail_reason: Optional[str] = None,
    bypass_gate1: bool = False,
) -> ValueTriggerResult:
    """2단 게이트 실행. risk_gate 가 소비하는 후보 신호를 반환.

    heavy_agent_fail_reason: 모순1 최소훅 — heavy_agent=None 시 실패 사유 구분.
      "quality"  = 품질붕괴(모델 이상·컨텍스트 부족) → 즉시 abstain 정답.
      "resource" = 자원 부족(429·예산 초과·타임아웃) → 재시도/예약 대상(Phase6 retry).
      None/미전달 = 사유 불명(silent abstain 금지, 경고 로그).

    bypass_gate1 (cross-sectional selection 경로, default False=byte-identical):
      cross_sectional_selection 이 universe 횡단면 cheapness 로 종목을 이미 선별한 경우,
      1차 게이트의 "가격 −10% 급락 AND" 조건(coin 단일종목 dip-buy 혈통)을 면제하고
      stage-2 value-trap veto 만 적용한다. 근거 = 외부 자문 2R 수렴(2026-06-04):
      −10% 게이트는 cross-sectional value-rank 픽을 전멸(횡보·상승 중 싼 종목 REJECT)시키며,
      −10% 의 유일한 정당한 잔여물(falling-knife/trap 우려)은 이미 stage-2 가 소유.
      ⛔ default False → 기존 단일종목 호출 경로 byte-identical (회귀 0).
    """
    """2단 게이트 실행. risk_gate 가 소비하는 후보 신호를 반환.

    흐름:
      1) 1차 게이트 (가격변동 AND 가치갭). 미통과 → REJECT.
      2) buy-the-dip 차단: 내재가치 동반 하락 의심 시 trap 우선 검토.
      3) H22: BACKTEST 모드면 2차 heavy-agent abstain (ABSTAIN, forward 만 실제).
      4) 2차 heavy-agent value-trap 판정. trap → VALUE_TRAP, 아니면 OPPORTUNITY.
      5) 메타라벨러 함정확률 → metalabel_size_factor 로 사이징 억제 (§5.8-H).

    direction (G2): trap/reject = "none", price_only = "hold", opportunity = "buy".
    종목 신호는 *하향만* 오버라이드 (상향은 S3/S4) → buy 는 후보 제안일 뿐.
    """
    context = context or {}

    # --- 1차 게이트 ---
    if bypass_gate1:
        # cross-sectional selection 경로: −10% 타이밍 게이트(coin dip-buy 혈통) 면제, stage-2 trap veto 만.
        g1_pass, g1_reason = True, "bypass_gate1: cross-sectional selection 경로 (stage-2 trap veto only)"
    else:
        g1_pass, g1_reason = passes_gate1(valuation, price_change_pct, prev_intrinsic_value, thresholds)
    if not g1_pass:
        return ValueTriggerResult(
            ticker=valuation.ticker,
            as_of=valuation.as_of,
            verdict=ValueVerdict.REJECT,
            passed_gate1=False,
            stage_reached=TriggerStage.GATE1_QWEN,
            direction="none",
            confidence=0.0,
            valuation_gap=valuation.valuation_gap,
            price_change_pct=price_change_pct,
            reasoning=f"1차 게이트 미통과: {g1_reason}",
        )

    # buy-the-dip 동반 하락 의심 플래그 (2차 입력으로 전달)
    value_declined = _value_declined_with_price(valuation, prev_intrinsic_value, thresholds)
    context = {**context, "value_declined_with_price": value_declined}

    # --- 메타라벨러 함정확률 → 사이징 계수 (§5.8-H (a)) ---
    size_factor = 1.0
    if metalabeler is not None:
        try:
            trap_p = metalabeler.trap_probability(valuation, fundamentals)
            # 함정확률 높을수록 사이징 억제 (선형). 0.5 이상이면 절반 이하로.
            size_factor = max(0.0, 1.0 - trap_p)
        except Exception:
            size_factor = 1.0  # 메타라벨러 실패 시 억제 안 함(보수적이지 않으니 로깅 필요)

    # --- H22: 백테스트는 2차 heavy-agent abstain ---
    if mode == RunMode.BACKTEST:
        return ValueTriggerResult(
            ticker=valuation.ticker,
            as_of=valuation.as_of,
            verdict=ValueVerdict.ABSTAIN,
            passed_gate1=True,
            stage_reached=TriggerStage.GATE1_QWEN,
            direction="hold",
            confidence=0.0,
            valuation_gap=valuation.valuation_gap,
            price_change_pct=price_change_pct,
            reasoning="H22: 백테스트에서 heavy-agent lookahead 오염 → abstain (forward 만 판정)",
            metalabel_size_factor=size_factor,
        )

    # --- 2차 게이트 (heavy-agent) ---
    if heavy_agent is None:
        # 모순1 최소훅: degrade 사유를 quality vs resource 로 구분해 reasoning 명시
        # (silent abstain 금지 — Phase6 retry 풀 연계를 위해 사유 태깅 필수)
        if heavy_agent_fail_reason == "resource":
            _abstain_reason = (
                "heavy-agent 미주입 [resource]: 자원부족(429·예산·타임아웃) → "
                "보수적 abstain. Phase6 retry 풀 대상(silent 아님)."
            )
        elif heavy_agent_fail_reason == "quality":
            _abstain_reason = (
                "heavy-agent 미주입 [quality]: 품질붕괴(모델이상·컨텍스트부족) → "
                "abstain 정답(즉시 hold, retry 아님)."
            )
        else:
            # 사유 불명 — 경고 기록 필수(silent abstain 금지)
            import logging as _logging  # noqa: PLC0415
            _logging.getLogger("stock.value_trigger").warning(
                "heavy-agent=None but fail_reason 미전달(ticker=%s). "
                "모순1: silent abstain 금지 — heavy_agent_fail_reason 명시 요망.",
                valuation.ticker,
            )
            _abstain_reason = (
                "heavy-agent 미주입 [reason=unknown] → 보수적 abstain. "
                "호출자는 heavy_agent_fail_reason 을 명시해야 합니다(모순1 최소훅)."
            )
        return ValueTriggerResult(
            ticker=valuation.ticker,
            as_of=valuation.as_of,
            verdict=ValueVerdict.ABSTAIN,
            passed_gate1=True,
            stage_reached=TriggerStage.GATE1_QWEN,
            direction="hold",
            confidence=0.0,
            valuation_gap=valuation.valuation_gap,
            price_change_pct=price_change_pct,
            reasoning=_abstain_reason,
            metalabel_size_factor=size_factor,
        )

    verdict = heavy_agent.judge_value_trap(valuation, fundamentals, price_change_pct, context)

    if verdict.is_trap:
        return ValueTriggerResult(
            ticker=valuation.ticker,
            as_of=valuation.as_of,
            verdict=ValueVerdict.VALUE_TRAP,
            passed_gate1=True,
            stage_reached=TriggerStage.GATE2_HEAVY,
            direction="none",
            confidence=verdict.confidence,
            valuation_gap=valuation.valuation_gap,
            price_change_pct=price_change_pct,
            reasoning=f"VALUE_TRAP: {verdict.reasoning}",
            metalabel_size_factor=size_factor,
        )

    # 싸진 기회 — 단 메타라벨러가 강하게 함정확률 높이면 PRICE_ONLY 로 강등
    if size_factor < 0.3:
        verdict_kind = ValueVerdict.PRICE_ONLY
        direction = "hold"
        reasoning = (
            f"heavy-agent=기회지만 메타라벨러 함정확률 높음(size={size_factor:.2f}) → 관망"
        )
    else:
        verdict_kind = ValueVerdict.OPPORTUNITY
        direction = "buy"
        reasoning = f"OPPORTUNITY: {verdict.reasoning} ({g1_reason})"

    return ValueTriggerResult(
        ticker=valuation.ticker,
        as_of=valuation.as_of,
        verdict=verdict_kind,
        passed_gate1=True,
        stage_reached=TriggerStage.GATE2_HEAVY,
        direction=direction,
        confidence=verdict.confidence * size_factor,
        valuation_gap=valuation.valuation_gap,
        price_change_pct=price_change_pct,
        reasoning=reasoning,
        metalabel_size_factor=size_factor,
    )


# ---------------------------------------------------------------------------
# wiring 헬퍼 — risk_gate / AssetTrack 이 소비하는 형태로 변환
# ---------------------------------------------------------------------------

def to_track_decision(result: ValueTriggerResult, agent_name: str = "stock_value_trigger") -> dict:
    """ValueTriggerResult → 공유 Decision dict (coin Decision 과 동형, risk_gate 입력).

    coin/agents/base_agent.py Decision 필드(decision/confidence/reason/trade_params/...)
    와 호환되는 dict 를 만든다. StockTrack.generate_candidate() 가 이걸 감싸 risk_gate 로
    넘긴다. amount/사이징은 risk_gate·G1 사이징 단계에서 metalabel_size_factor 와 함께 결정.

    G2: 종목 신호는 *하향만* 오버라이드 → buy 는 후보 제안, hold/none 은 억제 신호.
    """
    decision = {
        "OPPORTUNITY": "buy",
        "PRICE_ONLY": "hold",
        "VALUE_TRAP": "hold",     # 매수 금지 (none 이지만 거래 결정상 hold)
        "REJECT": "hold",
        "ABSTAIN": "hold",
    }.get(result.verdict.name, "hold")

    return {
        "decision": decision,
        "confidence": round(result.confidence, 4),
        "reason": result.reasoning,
        "buy_score": {
            "valuation_gap": result.valuation_gap,
            "price_change_pct": result.price_change_pct,
            "verdict": result.verdict.value,
            "stage_reached": result.stage_reached.value,
            "metalabel_size_factor": result.metalabel_size_factor,
        },
        "trade_params": {
            "side": "bid" if decision == "buy" else "hold",
            "ticker": result.ticker,
            # amount 는 risk_gate/G1 사이징이 결정. 사이징 힌트만 전달.
            "size_factor": result.metalabel_size_factor,
        },
        "external_signal": {},
        "agent_name": agent_name,
        # 메타 — risk_gate 가 value-trap suppress / downgrade-ratchet(G2) 에 사용
        "_value_verdict": result.verdict.value,
        "_suppressed": result.suppressed,
        "_is_buy_candidate": result.verdict == ValueVerdict.OPPORTUNITY,
    }
