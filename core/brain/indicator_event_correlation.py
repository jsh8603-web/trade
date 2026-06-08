"""
indicator_event_correlation.py — 거시지표↔거시이벤트 상관관계 모델 + §5.8-H 오판 피드백 루프.

이 모듈은 단순 분류기를 넘어, "정상 상관 패턴 / 그 패턴이 깨진 이상 케이스 / 보조지표가 임계를
넘으면 상관을 동적으로 약화" 를 *실제 동작 코드* 로 구현하고, 보정 레코드로 학습되는 caution 메모리다.

근거 문서 (1:1 연결): `core/brain/MACRO_CORRELATION_BACKGROUND.md`
  §1 → EVENT_BASELINE,  §2 → ANOMALY_CASES,  §3 → conditional_attenuation(),
  §4 → CorrectionRecord / IndicatorEventCorrelation.ingest_correction / recall_similar.

설계 정합 (§5.8-H, §5.8-A, §5.8-F):
- §5.8-H ① 탐지(3채널): ⓐ 실현수익 괴리 ⓑ 지표 이상(baseline 상관 위반) ⓒ 리포트 발산.
- §5.8-H ② 보정 레코드 (PIT-safe): (as_of, regime_realtime, confidence, regime_hindsight, signature, lag).
- §5.8-H ③ 학습: correction 태깅 RAG 적재 + 보수적 재보정(빈도/lag 통계, hard 재학습 금지).
- §5.8-H ④ 이후 개선: 유사 재현 시 recall → macro_reasoning confidence 하향 + BL τ·Ω 확대.
- PIT 철칙: 보정 라벨은 학습 신호로만, 원결정 backfill 금지 (causal mask by as_of_ts).

코드화한 macro.md (라인):
- 6 이상 케이스 전부 = macro.md 라인 6~8, 47~50, 105~136, 151~186 (배경문서 §2 참조).
- Michez/유통속도/term premium/모기지락인/GDI/Truflation 보조지표 + FRED ID + 임계 = 배경문서 §2.

github/메서드 차용:
- López de Prado 메타라벨링 (MlFinLab) — 2차 모델이 1차 신호 적중 판단 → 억제·사이징.
  여기선 ML 모델 대신 *규칙기반 attenuation* 로 경량 구현(거시 sparse → 과적합 회피, §5.8-H 정직).
- Hamilton(1989) regime-switching, conditional correlation — 보조지표 조건부 상관 약화 근거.

미해결 결정:
- attenuation 곱(0.4~0.7)은 휴리스틱. 보정 레코드 누적되면 실측 적중률로 재튜닝 가능(보수적으로).
- anomaly_signature 매칭 = 현재는 (이벤트+보조지표 trigger set) 키. 향후 embedder 코사인 유사도로 확장.
- term premium 직접관측 불가 → WALCL(대차대조표) + near-term forward spread 프록시로 대체.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from .macro_schema import RegimeLabel


# ===========================================================================
# 거시 이벤트 유형
# ===========================================================================
class MacroEvent(str, Enum):
    RATE_HIKE_CYCLE = "rate_hike_cycle"
    INFLATION_SHOCK = "inflation_shock"
    CREDIT_CRUNCH = "credit_crunch"
    RECESSION_ONSET = "recession_onset"
    MONETARY_EXPANSION = "monetary_expansion"   # QE/재정 (M2 급증).


# 지표 방향 부호.
class Dir(str, Enum):
    UP = "up"
    DOWN = "down"
    FLAT = "flat"


# ===========================================================================
# 1. 정상 패턴 (baseline 상관) — 배경문서 §1
# ===========================================================================
# {이벤트: {지표_logical_name: 기대방향}}  (지표명 = fred_adapter.FRED_SERIES 값과 정합)
EVENT_BASELINE: dict = {
    MacroEvent.RATE_HIKE_CYCLE: {
        "yield_10y_2y": Dir.DOWN,      # flatten.
        "credit_spread_baa": Dir.FLAT,
        "industrial_production": Dir.FLAT,
        "unemployment_rate": Dir.FLAT,
        "core_cpi": Dir.DOWN,          # 긴축 목적 = 인플레 하강 유도.
    },
    MacroEvent.INFLATION_SHOCK: {
        "yield_10y_2y": Dir.DOWN,
        "credit_spread_baa": Dir.UP,
        "core_cpi": Dir.UP,
        "breakeven_5y": Dir.UP,
    },
    MacroEvent.CREDIT_CRUNCH: {
        "credit_spread_baa": Dir.UP,   # 급확대.
        "nfci": Dir.UP,                # 금융상황 악화.
        "stl_financial_stress": Dir.UP,
        "unemployment_rate": Dir.UP,
        "industrial_production": Dir.DOWN,
    },
    MacroEvent.RECESSION_ONSET: {
        "yield_10y_2y": Dir.UP,        # 역전후 정상화(스티프닝).
        "credit_spread_baa": Dir.UP,
        "unemployment_rate": Dir.UP,
        "nonfarm_payrolls": Dir.DOWN,
        "industrial_production": Dir.DOWN,
    },
    MacroEvent.MONETARY_EXPANSION: {
        # baseline: M2 급증 → 인플레 (피셔 방정식, macro.md 라인 3~4).
        "core_cpi": Dir.UP,
        "breakeven_5y": Dir.UP,
    },
}


# ===========================================================================
# 2. 이상 케이스 (decoupling) — 배경문서 §2
# ===========================================================================
@dataclass
class SupplementarySignal:
    """
    보조지표 trigger — 이게 충족되면 해당 이벤트의 baseline 상관이 깨진다.

    name        : 보조지표 logical name (FRED 또는 파생).
    fred_id     : FRED 시리즈 ID (없으면 파생/외부).
    threshold   : 임계값.
    direction   : 임계를 *어느 방향* 으로 넘으면 trigger (UP=초과, DOWN=미만).
    description : 이 보조지표가 무엇을 sensing 하는가.
    """
    name: str
    fred_id: Optional[str]
    threshold: float
    direction: Dir
    description: str

    def is_triggered(self, value: Optional[float]) -> bool:
        if value is None:
            return False
        if self.direction == Dir.UP:
            return value > self.threshold
        if self.direction == Dir.DOWN:
            return value < self.threshold
        return False


@dataclass
class AnomalyCase:
    """
    같은 이벤트인데 동반지표가 평소와 다르게 움직인 역사적 케이스 (배경문서 §2).

    case_id      : 식별자.
    event        : 어느 거시 이벤트에서.
    distorted_indicator : baseline 상관이 깨진 주 지표.
    expected     : baseline 기대 거동.
    actual       : 실제 거동.
    reason       : 왜 다르게 움직였나 (구조적 원인).
    supplementary: 이 분기를 sensing 하는 보조지표(들).
    attenuation  : trigger 시 baseline 상관 신뢰도에 곱할 값 [0,1] (작을수록 강한 무력화).
    historical_episodes : 실제 발생 시기(감사·학습).
    macro_md_lines : 근거 macro.md 라인.
    """
    case_id: str
    event: MacroEvent
    distorted_indicator: str
    expected: Dir
    actual: Dir
    reason: str
    supplementary: list  # list[SupplementarySignal]
    attenuation: float
    historical_episodes: list = field(default_factory=list)
    macro_md_lines: str = ""


# --- 6 이상 케이스 인코딩 (배경문서 §2-1 ~ §2-6) ---
ANOMALY_CASES: list = [
    # 2-1. 금리커브 역전 무력화 (QE term premium 왜곡).
    AnomalyCase(
        case_id="yc_inversion_term_premium",
        event=MacroEvent.RECESSION_ONSET,
        distorted_indicator="yield_10y_2y",
        expected=Dir.DOWN, actual=Dir.DOWN,   # 역전은 일어났으나 침체 미발생.
        reason="QE가 장기채 term premium을 인위적 음(-)으로 억눌러 약한 신호에도 쉽게 역전. "
               "역전이 침체로 직행하지 않음.",
        supplementary=[
            SupplementarySignal(
                "near_term_forward_spread", None, 0.0, Dir.DOWN,
                "18M후 3M금리 - 현재 3M금리. QE왜곡 장기금리 대신 정책경로 기대 직접반영. "
                "이게 음(-)이어야 진짜 침체신호."),
            SupplementarySignal(
                "fed_balance_sheet", "WALCL", 7.5e6, Dir.UP,
                "연준 대차대조표(백만$). 큰 채로 유지 = term premium 왜곡 지속 → 역전신호 신뢰 저하. "
                "QT로 축소되면 신호 정상화."),
        ],
        attenuation=0.45,
        historical_episodes=["2022-07~2024"],
        macro_md_lines="131-136, 191-194",
    ),
    # 2-2. Sahm Rule 오작동 (이민 노동공급 충격).
    AnomalyCase(
        case_id="sahm_supply_shock",
        event=MacroEvent.RECESSION_ONSET,
        distorted_indicator="unemployment_rate",
        expected=Dir.UP, actual=Dir.UP,   # 실업률 상승은 맞으나 침체 아님.
        reason="실업률 상승이 해고가 아니라 이민 노동공급 충격(분모 팽창). 기업 구인은 정상 → 침체 아님.",
        supplementary=[
            SupplementarySignal(
                "vacancy_to_unemployed", None, 1.0, Dir.UP,
                "V/U비율 = 구인(JTSJOL)/실업(UNEMPLOY). 1.0 초과 유지 = 노동 타이트 → 실업률 상승은 공급발."),
            SupplementarySignal(
                "michez_m", None, 0.29, Dir.DOWN,
                "Michez m(t)=min(û,v̂). 0.29%p 미만 = 건전 균형. 구인 하락속도 v̂를 û와 대칭결합해 공급충격 차단."),
        ],
        attenuation=0.5,
        historical_episodes=["2024"],
        macro_md_lines="158-186, 205-208",
    ),
    # 2-3. M2-인플레 디커플링 (통화승수/유통속도).
    AnomalyCase(
        case_id="m2_inflation_decoupling",
        event=MacroEvent.MONETARY_EXPANSION,
        distorted_indicator="core_cpi",
        expected=Dir.UP, actual=Dir.FLAT,   # M2 급증했으나 인플레 미발생(2008형).
        reason="QE 유동성이 초과준비금에 갇혀 통화승수 붕괴+유통속도 급락(IOER). 돈이 실물로 안 감.",
        supplementary=[
            SupplementarySignal(
                "excess_reserves", "WRESBAL", 1.0e6, Dir.UP,
                "초과준비금(백만$). M2증가 대비 급등 = 돈이 은행에 갇힘 → M2-인플레 상관 약화."),
            SupplementarySignal(
                "money_velocity", "M2V", 1.3, Dir.DOWN,
                "M2 유통속도. 급락 = 통화량 인플레 전이 차단(2008형)."),
        ],
        attenuation=0.4,
        historical_episodes=["2008-2014"],
        macro_md_lines="3-8, 18-29",
    ),
    # 2-3b. 역(逆): 재정 직접이전이면 디커플링 *해제* → 인플레 점화 (2020형). attenuation>1 의미 = 상관 강화.
    AnomalyCase(
        case_id="m2_inflation_fiscal_recoupling",
        event=MacroEvent.MONETARY_EXPANSION,
        distorted_indicator="core_cpi",
        expected=Dir.UP, actual=Dir.UP,   # 재정이전 동반 시 인플레 강하게 점화.
        reason="재정 직접이전(은행 우회)+지준율 상한 폐지 → 유통속도 방어+보복소비 → 인플레 점화(2020형).",
        supplementary=[
            SupplementarySignal(
                "savings_rate_drop", "PSAVERT", 5.0, Dir.DOWN,
                "개인저축률. 급등 후 급락(초과저축 소진) = 돈이 실물 소비로 유입 → 인플레 점화."),
        ],
        attenuation=1.0,   # 상관 약화 안 함(오히려 baseline 유효) — sensing 용도.
        historical_episodes=["2020-2022"],
        macro_md_lines="7-8, 20-29",
    ),
    # 2-4. 500bp 인상에도 연착륙 (모기지 락인 + R*).
    AnomalyCase(
        case_id="rate_hike_soft_landing",
        event=MacroEvent.RATE_HIKE_CYCLE,
        distorted_indicator="unemployment_rate",
        expected=Dir.UP, actual=Dir.FLAT,   # 가파른 인상에도 실업 폭등 없음.
        reason="모기지 락인(30년 고정 저금리)+자산효과+R* 구조적 상향(2.0%+) → 5.33%가 약한 긴축.",
        supplementary=[
            SupplementarySignal(
                "household_debt_service", "TDSP", 11.0, Dir.DOWN,
                "가계 부채상환부담(% 가처분소득). 인상기에도 낮게 유지 = 통화정책 파급 약화."),
            SupplementarySignal(
                "r_star_estimate", None, 1.5, Dir.UP,
                "중립실질금리 R*. 상향(2.0%+)이면 동일 명목금리의 긴축강도 약화."),
        ],
        attenuation=0.5,
        historical_episodes=["2022-2023"],
        macro_md_lines="137-150, 195-200",
    ),
    # 2-5. CPI vs Truflation 괴리 (OER 시차).
    AnomalyCase(
        case_id="cpi_truflation_lag",
        event=MacroEvent.INFLATION_SHOCK,
        distorted_indicator="core_cpi",
        expected=Dir.UP, actual=Dir.DOWN,   # 공식 CPI 경직(상방)인데 실물은 디스인플레.
        reason="공식 OER 6~12개월 시차+셧다운 BLS 수집붕괴 → 공식 CPI가 디스인플레를 과장 은폐.",
        supplementary=[
            SupplementarySignal(
                "truflation_cpi_gap", None, -1.0, Dir.DOWN,
                "Truflation YoY - 공식 CPI YoY. -1%p 미만 = 디스인플레 조기신호(40~75일 선행)."),
        ],
        attenuation=0.55,
        historical_episodes=["2026-02"],
        macro_md_lines="44-51, 72-79, 213",
    ),
    # 2-6. GDP-GDI 단절 (무역/재고 왜곡).
    AnomalyCase(
        case_id="gdp_gdi_divergence",
        event=MacroEvent.RECESSION_ONSET,
        distorted_indicator="real_gdp",
        expected=Dir.DOWN, actual=Dir.DOWN,   # GDP 2분기 연속 음수.
        reason="지출측 GDP가 무역수지 역조+재고보정으로 과소집계. GDI는 정상 확장 → 침체 아님.",
        supplementary=[
            SupplementarySignal(
                "real_gdi", "A261RX1Q020SBEA", 0.0, Dir.UP,
                "실질 GDI. GDP<0<GDI 면 통계노이즈 → 침체 단정 보류(GDPplus 평균 사용)."),
        ],
        attenuation=0.5,
        historical_episodes=["2022-H1"],
        macro_md_lines="151-156, 201-204, 216",
    ),
]

_CASE_INDEX = {c.case_id: c for c in ANOMALY_CASES}


# ===========================================================================
# 3. 조건부 상관 약화 로직 — 배경문서 §3
# ===========================================================================
@dataclass
class AttenuationResult:
    """conditional_attenuation 출력 — confidence 곱 + 발동 케이스 + caution flag."""
    confidence_multiplier: float          # baseline 상관 신뢰도에 곱 [0,1].
    fired_cases: list = field(default_factory=list)   # [case_id, ...]
    caution_flags: list = field(default_factory=list)
    details: dict = field(default_factory=dict)


def conditional_attenuation(
    event: MacroEvent,
    indicator_values: dict,   # {logical_name: value} — 보조지표 현재값 (지표명/임계는 위 정의).
) -> AttenuationResult:
    """
    "보조지표 X가 임계를 넘으면 → 거시지표-이벤트 상관관계가 약해진다" 를 실제 계산한다 (배경문서 §3).

    동작:
      1) event 에 해당하는 ANOMALY_CASES 순회.
      2) 각 케이스의 보조지표 중 *하나라도* trigger 면 그 케이스의 attenuation 발동.
      3) 발동 attenuation 들을 곱(독립 가정) → confidence_multiplier.
      4) 발동 케이스 → caution flag (§5.8-H 메모리 + macro_reasoning confidence 하향 입력).

    이 multiplier 는:
      - regime_classifier 의 confidence 에 곱해짐 → 레짐 판정 보수화.
      - macro_reasoning 을 거쳐 BL τ·Ω 확대 → 배분이 Prior 근접(과도 tilt 자제, §5.8-D/H④).
    """
    mult = 1.0
    fired, flags, details = [], [], {}

    for case in ANOMALY_CASES:
        if case.event != event:
            continue
        triggered_sigs = [
            sig for sig in case.supplementary
            if sig.is_triggered(indicator_values.get(sig.name))
        ]
        if triggered_sigs:
            mult *= case.attenuation
            fired.append(case.case_id)
            flags.append(f"corr_break:{case.case_id}")
            details[case.case_id] = {
                "attenuation": case.attenuation,
                "triggered_by": [s.name for s in triggered_sigs],
                "reason": case.reason,
                "macro_md_lines": case.macro_md_lines,
            }

    return AttenuationResult(
        confidence_multiplier=float(max(mult, 0.1)),   # 바닥 0.1 (완전 0 방지).
        fired_cases=fired,
        caution_flags=flags,
        details=details,
    )


def baseline_violation(event: MacroEvent, observed: dict) -> list:
    """
    §5.8-H ① ⓑ 지표 이상 탐지: 선언된 이벤트가 예측하는 baseline 거동과 실제 관측이 *불일치* 하는 지표.

    observed = {logical_name: Dir} — 실제 관측 방향.
    반환 = 불일치 지표 리스트 (예: Reflation 선언인데 신용스프레드가 Stagflation처럼 거동).
    """
    base = EVENT_BASELINE.get(event, {})
    violations = []
    for ind_name, expected_dir in base.items():
        actual = observed.get(ind_name)
        if actual is not None and actual != expected_dir and expected_dir != Dir.FLAT:
            violations.append({"indicator": ind_name, "expected": expected_dir.value, "actual": actual.value})
    return violations


# ===========================================================================
# 4. 학습 — 보정 레코드 + caution 메모리 (배경문서 §4, §5.8-H ②③④)
# ===========================================================================
@dataclass
class CorrectionRecord:
    """
    §5.8-H ② 사후 보정 레코드 (PIT-safe).

    PIT 철칙: hindsight 라벨은 *학습 신호로만*. 원래 실시간 결정에 backfill 금지.
    as_of_ts = 실시간 판정 시각(causal mask 키). recorded_ts = 보정 기록 시각.
    """
    as_of_ts: float                       # 실시간 레짐 판정 시각.
    regime_realtime: RegimeLabel          # 그때 판정한 레짐.
    confidence_realtime: float
    regime_hindsight: RegimeLabel         # 사후(smoothed/NBER/실현) 정답 레짐.
    anomaly_signature: dict               # {event, triggered_sups, distorted_indicators}.
    lag_days: int                         # 실시간 판정 ~ 사후확정 시차.
    hint: str = ""                        # "이 패턴 때 교과서 A였지만 실제 B" recall 텍스트.
    event: Optional[str] = None
    recorded_ts: float = field(default_factory=time.time)

    def is_misjudgment(self) -> bool:
        return self.regime_realtime != self.regime_hindsight


class IndicatorEventCorrelation:
    """
    상관 모델 + caution 메모리. macro_reasoning / regime_classifier 가 주입받아 사용.

    역할:
      - score_confidence(): 분류기 confidence 에 조건부 약화 적용.
      - ingest_correction(): 보정 레코드 적재(학습) — 보수적 빈도/lag 통계만 (hard 재학습 금지).
      - recall_similar(): 유사 거시 재현 시 과거 보정 surface (PIT causal mask).

    저장소는 인터페이스 — 기본은 in-memory list, 프로덕션은 §5.8-E RAG 스토어 어댑터 주입.
    """

    def __init__(self, rag_store=None):
        self.rag_store = rag_store               # §5.8-E correction 태깅 적재용(옵션).
        self._records: list = []                 # in-memory fallback.
        # case_id → 누적 통계(빈도/평균 lag) — 보수적 재보정용.
        self._case_stats: dict = {}

    # ---------------------------------------------------------- 조회/스코어
    def score_confidence(
        self,
        event: MacroEvent,
        base_confidence: float,
        indicator_values: dict,
    ) -> AttenuationResult:
        """분류기/추론 confidence 에 조건부 상관 약화를 곱해 반환 (배경문서 §3)."""
        res = conditional_attenuation(event, indicator_values)
        res.details["scored_confidence"] = round(base_confidence * res.confidence_multiplier, 4)
        # 과거 보정 빈도가 높은 케이스면 추가 보수화.
        for cid in res.fired_cases:
            stat = self._case_stats.get(cid)
            if stat and stat["count"] >= 2:
                res.confidence_multiplier *= 0.9
                res.caution_flags.append(f"recurrent_misjudgment:{cid}")
        return res

    def recall_similar(
        self,
        regime: RegimeLabel,
        signature: dict,
        as_of_ts: Optional[float],
        k: int = 3,
    ) -> list:
        """
        §5.8-H ④: 유사 거시 재현 시 과거 보정 recall. PIT — as_of 이전 보정만 (causal mask).
        macro_reasoning 이 이걸 받아 confidence 하향 + caution 해석.
        """
        # RAG 스토어 우선 (있으면 임베딩 검색), 없으면 in-memory 규칙 매칭.
        if self.rag_store is not None:
            try:
                return self.rag_store.retrieve_corrections(regime, signature, as_of_ts, k)
            except Exception:
                pass

        candidates = []
        sig_event = signature.get("event") if isinstance(signature, dict) else None
        sig_sups = set(signature.get("triggered_sups", [])) if isinstance(signature, dict) else set()
        for rec in self._records:
            # PIT causal mask: 과거 보정만.
            if as_of_ts is not None and rec.as_of_ts >= as_of_ts:
                continue
            if not rec.is_misjudgment():
                continue
            score = 0
            if rec.regime_realtime == regime:
                score += 2
            if sig_event and rec.event == sig_event:
                score += 2
            rec_sups = set(rec.anomaly_signature.get("triggered_sups", []))
            score += len(sig_sups & rec_sups)
            if score > 0:
                candidates.append((score, rec))
        candidates.sort(key=lambda x: (-x[0], -x[1].as_of_ts))
        return [
            {"event": r.event, "hint": r.hint, "lag": r.lag_days,
             "regime_realtime": r.regime_realtime.value, "regime_hindsight": r.regime_hindsight.value}
            for _, r in candidates[:k]
        ]

    # ---------------------------------------------------------- 학습(적재)
    def ingest_correction(self, rec: CorrectionRecord) -> None:
        """
        §5.8-H ③: 보정 레코드 적재. 보수적 — hard 재학습 아닌 빈도/lag 통계 누적 + RAG 태깅.
        PIT 철칙: 이 레코드는 학습 신호로만, 원결정 backfill 금지 (호출측이 보장).
        """
        if not rec.is_misjudgment():
            return  # 오판 아니면 학습 불필요.
        self._records.append(rec)

        # 보수적 재보정: 매칭 케이스 빈도/lag 통계만 갱신 (임계·가중 hard 변경 안 함).
        cid = self._match_case(rec.anomaly_signature)
        if cid:
            st = self._case_stats.setdefault(cid, {"count": 0, "lag_sum": 0})
            st["count"] += 1
            st["lag_sum"] += rec.lag_days

        # §5.8-E RAG correction 태깅 적재.
        if self.rag_store is not None:
            try:
                self.rag_store.add_correction(rec)
            except Exception:
                pass

    def _match_case(self, signature: dict) -> Optional[str]:
        """anomaly_signature 를 기존 ANOMALY_CASES 와 매칭 (이벤트+보조지표 set)."""
        sig_event = signature.get("event")
        sig_sups = set(signature.get("triggered_sups", []))
        best, best_overlap = None, 0
        for case in ANOMALY_CASES:
            if sig_event and case.event.value != sig_event:
                continue
            case_sups = {s.name for s in case.supplementary}
            overlap = len(sig_sups & case_sups)
            if overlap > best_overlap:
                best, best_overlap = case.case_id, overlap
        return best

    def case_recurrence(self, case_id: str) -> dict:
        """감사용 — 특정 케이스의 누적 오판 빈도/평균 lag."""
        st = self._case_stats.get(case_id, {"count": 0, "lag_sum": 0})
        avg_lag = (st["lag_sum"] / st["count"]) if st["count"] else 0
        return {"case_id": case_id, "count": st["count"], "avg_lag_days": avg_lag}


# ===========================================================================
# 헬퍼 — regime_classifier evidence → conditional_attenuation 입력 변환
# ===========================================================================
def build_indicator_values(evidence: dict, extra: Optional[dict] = None) -> dict:
    """
    regime_classifier 의 evidence(+외부 보조지표)를 conditional_attenuation 입력으로 정규화.
    evidence 에 없는 보조지표(near_term_forward_spread, WALCL 등)는 extra 로 주입.
    """
    vals = {}
    # 분류기 evidence 에서 직접 매핑 가능한 것.
    if "michez_m" in evidence:
        vals["michez_m"] = evidence["michez_m"]
    if extra:
        vals.update(extra)
    return vals


def infer_event_from_regime(regime: RegimeLabel) -> MacroEvent:
    """
    레짐 → 가장 관련 깊은 거시 이벤트 매핑 (baseline_violation/attenuation 조회용).
    REFLATION/STAGFLATION 의 침체축 → RECESSION_ONSET, OVERHEAT → INFLATION_SHOCK 등.
    """
    return {
        RegimeLabel.REFLATION: MacroEvent.RECESSION_ONSET,
        RegimeLabel.STAGFLATION: MacroEvent.INFLATION_SHOCK,
        RegimeLabel.OVERHEAT: MacroEvent.INFLATION_SHOCK,
        RegimeLabel.RECOVERY: MacroEvent.RATE_HIKE_CYCLE,
        RegimeLabel.SLOWDOWN: MacroEvent.RECESSION_ONSET,  # 둔화(저성장+modest물가)=침체축
    }[regime]
