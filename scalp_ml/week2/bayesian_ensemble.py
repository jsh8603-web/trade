#!/usr/bin/env python3
"""Week 2 PC36 베이지안 앙상블 — reward_ablation.py에 통합

핵심 로직은 reward_ablation.py의 _phase4_bayesian()과
_analyze_uncertainty()에 구현되어 있다.
"""

from scalp_ml.week2.reward_ablation import (
    _phase4_bayesian as train_bayesian_ensemble,
    _analyze_uncertainty as analyze_ensemble_uncertainty,
    AblationRewardWrapper,
    REWARD_COMPONENTS,
    COMPONENT_LABELS,
)

__all__ = [
    "train_bayesian_ensemble",
    "analyze_ensemble_uncertainty",
    "AblationRewardWrapper",
    "REWARD_COMPONENTS",
    "COMPONENT_LABELS",
]
