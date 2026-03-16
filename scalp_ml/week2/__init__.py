"""Week 2 분산 RL 훈련 — 레짐 특화 + 앙상블 다양성 + 보상 해부

Mac Mini: 레짐 전문가 팩토리 (regime_specialist + curriculum_trainer)
PC128:    앙상블 + 오프라인→온라인 전이 (cql_bridge + ensemble_diversity)
PC36:     보상 해부 + 불확실성 측정 (reward_ablation + bayesian_ensemble)
"""

from scalp_ml.week2.regime_specialist import run_mac_mini_w2
from scalp_ml.week2.cql_bridge import run_pc128_w2
from scalp_ml.week2.reward_ablation import run_pc36_w2

__all__ = ["run_mac_mini_w2", "run_pc128_w2", "run_pc36_w2"]
