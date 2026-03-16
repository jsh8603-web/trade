#!/usr/bin/env python3
"""Week 2 PC128 앙상블 다양성 훈련 — cql_bridge.py에 통합

이 모듈의 핵심 로직은 cql_bridge.py의 _phase4_ensemble_8()과
_phase5_diversity_select()에 구현되어 있다.
별도 함수가 필요한 경우 여기에 추가할 수 있다.
"""

from scalp_ml.week2.cql_bridge import (
    _phase4_ensemble_8 as train_ensemble_members,
    _phase5_diversity_select as select_diverse_ensemble,
    _eval_ensemble as evaluate_ensemble,
)

__all__ = ["train_ensemble_members", "select_diverse_ensemble", "evaluate_ensemble"]
