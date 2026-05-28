"""
core.brain — 거시 brain (자산배분 두뇌).

설계 §5.8 거시/미시 추론 레이어 핵심 모듈. portfolio_orchestrator 가 소비하는 진입점:

    from core.brain import RegimeClassifier, regime_to_weights, MacroReasoningNode

표준 사이클 (§5.8-D):
    clf = RegimeClassifier(usd_adapter=RealFredAdapter(api_key=...))
    macro_view = clf.classify()                       # 매 사이클 결정론 baseline (C3).
    macro_view = reasoner.enrich(macro_view, trigger) # macro-trigger 시에만 LLM enrich.
    alloc = regime_to_weights(macro_view, returns_history)  # BL 메인 → 슬리브 % (risk_gate 전).

모듈:
- macro_schema             : MacroView/RegimeEstimate 공통 계약 (스키마).
- macro_indicators         : macro.md 정량 법칙(Michez/Sahm/GDP-GDI/금리커브/Truflation).
- fred_adapter             : FRED/ALFRED(PIT) 데이터 어댑터 경계.
- regime_classifier        : Investment Clock + JM/SJM + HMM 폴백 (per-bloc, classifier≠forecaster).
- regime_to_weights        : Black-Litterman(Prior=IC표) 메인 + IC-prior 폴백.
- macro_reasoning          : LLM 거시추론 노드(thesis+반대thesis, C2 abstain).
- indicator_event_correlation : §5.8-H 상관 모델 + 오판 피드백 루프(조건부 약화·보정 메모리).
"""
from .macro_schema import (
    Bloc,
    MacroView,
    RegimeEstimate,
    RegimeLabel,
    ViewStatus,
)
from .regime_classifier import RegimeClassifier
from .regime_to_weights import regime_to_weights, ic_target_weights, SLEEVES
from .macro_reasoning import MacroReasoningNode, MacroTrigger
from .indicator_event_correlation import (
    IndicatorEventCorrelation,
    CorrectionRecord,
    MacroEvent,
    conditional_attenuation,
    baseline_violation,
)

__all__ = [
    "Bloc", "MacroView", "RegimeEstimate", "RegimeLabel", "ViewStatus",
    "RegimeClassifier",
    "regime_to_weights", "ic_target_weights", "SLEEVES",
    "MacroReasoningNode", "MacroTrigger",
    "IndicatorEventCorrelation", "CorrectionRecord", "MacroEvent",
    "conditional_attenuation", "baseline_violation",
]
