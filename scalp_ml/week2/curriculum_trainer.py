#!/usr/bin/env python3
"""Week 2 Mac Mini 커리큘럼 학습 유틸 — regime_specialist.py에서 사용

커리큘럼 학습의 핵심 유틸리티:
- 난이도 기반 레짐 순서 정의
- 사이클릭 리플레이 스케줄러
- 망각(catastrophic forgetting) 측정

메인 로직은 regime_specialist.py의 _phase3_curriculum(), _phase4_best_curriculum()에 있다.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

log = logging.getLogger("week2.curriculum")

# 레짐 난이도 정의 (변동성/예측 어려움 기준)
REGIME_DIFFICULTY = {
    "sideways": 1,   # 쉬움 — 낮은 변동성, 관망 학습
    "bull": 2,       # 보통 — 일정 방향, 추세 추종
    "volatile": 3,   # 어려움 — 높은 변동성, 타이밍 중요
    "bear": 4,       # 매우 어려움 — 하락장 대응, 손절 학습
}

# 미리 정의된 커리큘럼 순서
CURRICULUM_ORDERS = {
    "easy_to_hard": ["sideways", "bull", "volatile", "bear"],
    "hard_to_easy": ["bear", "volatile", "bull", "sideways"],
    "trend_first": ["bull", "bear", "sideways", "volatile"],
    "volatile_first": ["volatile", "bear", "bull", "sideways"],
}


@dataclass
class CurriculumSchedule:
    """커리큘럼 학습 스케줄"""
    regime_order: list[str]
    steps_per_stage: int = 100_000
    num_cycles: int = 1
    decay_lr: bool = False
    initial_lr: float = 3e-4
    final_lr: float = 1e-4

    @property
    def total_steps(self) -> int:
        return self.steps_per_stage * len(self.regime_order) * self.num_cycles

    def get_lr(self, cycle: int) -> float:
        """사이클에 따른 학습률 감쇠"""
        if not self.decay_lr or self.num_cycles <= 1:
            return self.initial_lr
        progress = cycle / (self.num_cycles - 1)
        return self.initial_lr + (self.final_lr - self.initial_lr) * progress


@dataclass
class ForgettingTracker:
    """Catastrophic Forgetting 추적기

    각 스테이지 학습 후, 이전 레짐에서의 성능 변화를 추적한다.
    """
    baseline_scores: dict[str, float] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)

    def set_baseline(self, regime: str, score: float):
        """레짐의 초기 성능 기록"""
        self.baseline_scores[regime] = score

    def record(self, stage: int, current_regime: str, eval_scores: dict[str, float]):
        """스테이지 완료 후 전체 레짐 성능 기록"""
        entry = {
            "stage": stage,
            "trained_on": current_regime,
            "scores": eval_scores.copy(),
            "forgetting": {},
        }
        for regime, score in eval_scores.items():
            if regime in self.baseline_scores:
                drop = self.baseline_scores[regime] - score
                entry["forgetting"][regime] = round(drop, 4)

        self.history.append(entry)

    def get_max_forgetting(self) -> float:
        """최대 망각 폭"""
        max_drop = 0
        for entry in self.history:
            for regime, drop in entry.get("forgetting", {}).items():
                if drop > max_drop:
                    max_drop = drop
        return max_drop

    def summary(self) -> dict:
        """망각 분석 요약"""
        if not self.history:
            return {"status": "no_data"}

        all_drops = []
        for entry in self.history:
            all_drops.extend(entry.get("forgetting", {}).values())

        return {
            "max_forgetting": self.get_max_forgetting(),
            "avg_forgetting": round(np.mean(all_drops), 4) if all_drops else 0,
            "stages_tracked": len(self.history),
            "regimes_tracked": list(self.baseline_scores.keys()),
        }


def make_cyclic_schedule(
    regime_order: list[str],
    steps_per_regime: int = 25_000,
    total_cycles: int = 10,
) -> list[tuple[str, int]]:
    """사이클릭 리플레이 스케줄 생성

    Returns:
        [(regime_name, steps), ...] 총 len(regime_order) × total_cycles 개
    """
    schedule = []
    for cycle in range(total_cycles):
        for regime in regime_order:
            schedule.append((regime, steps_per_regime))
    return schedule


def measure_regime_correlation(actions_by_regime: dict[str, np.ndarray]) -> dict:
    """레짐간 행동 상관관계 분석

    actions_by_regime: {"bull": [actions], "bear": [actions], ...}
    높은 상관 = 모델이 레짐 구분 못함 (안 좋음)
    낮은 상관 = 레짐별 특화 행동 (좋음)
    """
    regimes = list(actions_by_regime.keys())
    n = len(regimes)
    correlation = {}

    for i in range(n):
        for j in range(i + 1, n):
            a = actions_by_regime[regimes[i]]
            b = actions_by_regime[regimes[j]]
            min_len = min(len(a), len(b))
            if min_len < 10:
                continue
            corr = np.corrcoef(a[:min_len], b[:min_len])[0, 1]
            pair = f"{regimes[i]}_vs_{regimes[j]}"
            correlation[pair] = round(float(corr), 4)

    avg_corr = np.mean(list(correlation.values())) if correlation else 0
    return {
        "pairwise_correlation": correlation,
        "avg_correlation": round(float(avg_corr), 4),
        "regime_specialized": avg_corr < 0.5,  # 0.5 미만이면 특화 성공
    }
