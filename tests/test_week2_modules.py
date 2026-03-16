#!/usr/bin/env python3
"""Week 2 모듈 구조 및 핵심 유틸리티 단위 테스트

외부 의존성(SB3, Supabase, Upbit API) 없이 테스트 가능한 범위를 검증한다.
- 모듈 import 가능 여부
- AblationRewardWrapper 로직
- CurriculumSchedule, ForgettingTracker 동작
- REGIME_DIFFICULTY 상수
- make_cyclic_schedule, measure_regime_correlation
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# 프로젝트 루트를 path에 추가
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))


# ═══════════════════════════════════════════════════
# Import 테스트
# ═══════════════════════════════════════════════════

class TestImports:
    """Week 2 모듈 import 검증."""

    def test_import_curriculum_trainer(self):
        from scalp_ml.week2.curriculum_trainer import (
            CurriculumSchedule,
            ForgettingTracker,
            REGIME_DIFFICULTY,
            CURRICULUM_ORDERS,
            make_cyclic_schedule,
            measure_regime_correlation,
        )

    def test_import_reward_ablation_wrapper(self):
        from scalp_ml.week2.reward_ablation import (
            AblationRewardWrapper,
            REWARD_COMPONENTS,
            COMPONENT_LABELS,
        )

    def test_import_week2_init(self):
        """__init__.py의 __all__ 확인 (DB 의존성은 mock)."""
        # run_mac_mini_w2 등은 내부에서 distributed_training을 import하므로
        # 실제 호출은 하지 않고 이름만 확인
        from scalp_ml.week2 import __all__
        assert "run_mac_mini_w2" in __all__
        assert "run_pc128_w2" in __all__
        assert "run_pc36_w2" in __all__


# ═══════════════════════════════════════════════════
# REGIME_DIFFICULTY 상수 테스트
# ═══════════════════════════════════════════════════

class TestRegimeDifficulty:
    """레짐 난이도 상수 검증."""

    def test_all_regimes_present(self):
        from scalp_ml.week2.curriculum_trainer import REGIME_DIFFICULTY
        expected = {"sideways", "bull", "volatile", "bear"}
        assert set(REGIME_DIFFICULTY.keys()) == expected

    def test_difficulty_ordering(self):
        """sideways < bull < volatile < bear."""
        from scalp_ml.week2.curriculum_trainer import REGIME_DIFFICULTY
        assert REGIME_DIFFICULTY["sideways"] < REGIME_DIFFICULTY["bull"]
        assert REGIME_DIFFICULTY["bull"] < REGIME_DIFFICULTY["volatile"]
        assert REGIME_DIFFICULTY["volatile"] < REGIME_DIFFICULTY["bear"]

    def test_difficulty_values(self):
        from scalp_ml.week2.curriculum_trainer import REGIME_DIFFICULTY
        assert REGIME_DIFFICULTY["sideways"] == 1
        assert REGIME_DIFFICULTY["bull"] == 2
        assert REGIME_DIFFICULTY["volatile"] == 3
        assert REGIME_DIFFICULTY["bear"] == 4


# ═══════════════════════════════════════════════════
# CURRICULUM_ORDERS 테스트
# ═══════════════════════════════════════════════════

class TestCurriculumOrders:
    """커리큘럼 순서 사전 정의."""

    def test_easy_to_hard(self):
        from scalp_ml.week2.curriculum_trainer import CURRICULUM_ORDERS
        assert CURRICULUM_ORDERS["easy_to_hard"] == ["sideways", "bull", "volatile", "bear"]

    def test_hard_to_easy(self):
        from scalp_ml.week2.curriculum_trainer import CURRICULUM_ORDERS
        assert CURRICULUM_ORDERS["hard_to_easy"] == ["bear", "volatile", "bull", "sideways"]

    def test_all_orders_have_4_regimes(self):
        from scalp_ml.week2.curriculum_trainer import CURRICULUM_ORDERS
        for name, order in CURRICULUM_ORDERS.items():
            assert len(order) == 4, f"{name}에 4개 레짐이 있어야 함"
            assert set(order) == {"sideways", "bull", "volatile", "bear"}


# ═══════════════════════════════════════════════════
# CurriculumSchedule 테스트
# ═══════════════════════════════════════════════════

class TestCurriculumSchedule:
    """커리큘럼 스케줄 데이터클래스."""

    def test_total_steps_single_cycle(self):
        from scalp_ml.week2.curriculum_trainer import CurriculumSchedule
        sched = CurriculumSchedule(
            regime_order=["sideways", "bull", "volatile", "bear"],
            steps_per_stage=100_000,
            num_cycles=1,
        )
        # 4 regimes * 100K * 1 cycle = 400K
        assert sched.total_steps == 400_000

    def test_total_steps_multiple_cycles(self):
        from scalp_ml.week2.curriculum_trainer import CurriculumSchedule
        sched = CurriculumSchedule(
            regime_order=["sideways", "bull", "volatile", "bear"],
            steps_per_stage=50_000,
            num_cycles=3,
        )
        # 4 * 50K * 3 = 600K
        assert sched.total_steps == 600_000

    def test_get_lr_no_decay(self):
        from scalp_ml.week2.curriculum_trainer import CurriculumSchedule
        sched = CurriculumSchedule(
            regime_order=["sideways"],
            decay_lr=False,
            initial_lr=3e-4,
        )
        assert sched.get_lr(0) == 3e-4
        assert sched.get_lr(5) == 3e-4

    def test_get_lr_with_decay(self):
        from scalp_ml.week2.curriculum_trainer import CurriculumSchedule
        sched = CurriculumSchedule(
            regime_order=["sideways"],
            decay_lr=True,
            initial_lr=3e-4,
            final_lr=1e-4,
            num_cycles=3,
        )
        # cycle 0: initial_lr
        assert sched.get_lr(0) == pytest.approx(3e-4)
        # cycle 2 (last): final_lr
        assert sched.get_lr(2) == pytest.approx(1e-4)
        # cycle 1 (middle): midpoint
        assert sched.get_lr(1) == pytest.approx(2e-4)

    def test_get_lr_single_cycle_no_decay(self):
        """num_cycles=1이면 decay_lr=True여도 감쇠 안함."""
        from scalp_ml.week2.curriculum_trainer import CurriculumSchedule
        sched = CurriculumSchedule(
            regime_order=["sideways"],
            decay_lr=True,
            initial_lr=3e-4,
            final_lr=1e-4,
            num_cycles=1,
        )
        assert sched.get_lr(0) == 3e-4

    def test_default_values(self):
        from scalp_ml.week2.curriculum_trainer import CurriculumSchedule
        sched = CurriculumSchedule(regime_order=["sideways", "bull"])
        assert sched.steps_per_stage == 100_000
        assert sched.num_cycles == 1
        assert sched.decay_lr is False
        assert sched.initial_lr == 3e-4
        assert sched.final_lr == 1e-4


# ═══════════════════════════════════════════════════
# ForgettingTracker 테스트
# ═══════════════════════════════════════════════════

class TestForgettingTracker:
    """Catastrophic forgetting 추적기."""

    def test_initial_state(self):
        from scalp_ml.week2.curriculum_trainer import ForgettingTracker
        tracker = ForgettingTracker()
        assert tracker.baseline_scores == {}
        assert tracker.history == []
        assert tracker.get_max_forgetting() == 0

    def test_set_baseline(self):
        from scalp_ml.week2.curriculum_trainer import ForgettingTracker
        tracker = ForgettingTracker()
        tracker.set_baseline("bull", 5.0)
        tracker.set_baseline("bear", -2.0)
        assert tracker.baseline_scores["bull"] == 5.0
        assert tracker.baseline_scores["bear"] == -2.0

    def test_record_and_forgetting(self):
        from scalp_ml.week2.curriculum_trainer import ForgettingTracker
        tracker = ForgettingTracker()
        tracker.set_baseline("bull", 5.0)
        tracker.set_baseline("bear", -2.0)

        # bull에서 학습 후 bull 성능 유지, bear 성능 하락
        tracker.record(stage=1, current_regime="bull", eval_scores={"bull": 5.0, "bear": -3.0})
        assert len(tracker.history) == 1
        # bear 하락: baseline(-2.0) - current(-3.0) = 1.0
        assert tracker.history[0]["forgetting"]["bear"] == 1.0
        # bull 유지: 5.0 - 5.0 = 0
        assert tracker.history[0]["forgetting"]["bull"] == 0.0

    def test_get_max_forgetting(self):
        from scalp_ml.week2.curriculum_trainer import ForgettingTracker
        tracker = ForgettingTracker()
        tracker.set_baseline("bull", 5.0)
        tracker.set_baseline("bear", -1.0)

        tracker.record(1, "bull", {"bull": 4.0, "bear": -3.0})  # drop: bull=1.0, bear=2.0
        tracker.record(2, "bear", {"bull": 2.0, "bear": -1.0})  # drop: bull=3.0, bear=0.0
        assert tracker.get_max_forgetting() == 3.0

    def test_summary_no_data(self):
        from scalp_ml.week2.curriculum_trainer import ForgettingTracker
        tracker = ForgettingTracker()
        summary = tracker.summary()
        assert summary["status"] == "no_data"

    def test_summary_with_data(self):
        from scalp_ml.week2.curriculum_trainer import ForgettingTracker
        tracker = ForgettingTracker()
        tracker.set_baseline("bull", 5.0)
        tracker.set_baseline("bear", -1.0)

        tracker.record(1, "bull", {"bull": 4.0, "bear": -2.0})
        summary = tracker.summary()
        assert "max_forgetting" in summary
        assert summary["stages_tracked"] == 1
        assert "bull" in summary["regimes_tracked"]
        assert "bear" in summary["regimes_tracked"]
        assert summary["max_forgetting"] == 1.0  # bull drop=1.0, bear drop=1.0
        assert summary["avg_forgetting"] == pytest.approx(1.0)

    def test_record_without_baseline(self):
        """baseline 없는 레짐은 forgetting 계산 안됨."""
        from scalp_ml.week2.curriculum_trainer import ForgettingTracker
        tracker = ForgettingTracker()
        tracker.set_baseline("bull", 5.0)
        # bear baseline 미설정
        tracker.record(1, "bull", {"bull": 4.0, "bear": -2.0})
        assert "bear" not in tracker.history[0]["forgetting"]


# ═══════════════════════════════════════════════════
# make_cyclic_schedule 테스트
# ═══════════════════════════════════════════════════

class TestMakeCyclicSchedule:
    """사이클릭 리플레이 스케줄 생성."""

    def test_basic_schedule(self):
        from scalp_ml.week2.curriculum_trainer import make_cyclic_schedule
        schedule = make_cyclic_schedule(
            regime_order=["bull", "bear"],
            steps_per_regime=25_000,
            total_cycles=2,
        )
        # 2 regimes * 2 cycles = 4 entries
        assert len(schedule) == 4
        assert schedule[0] == ("bull", 25_000)
        assert schedule[1] == ("bear", 25_000)
        assert schedule[2] == ("bull", 25_000)
        assert schedule[3] == ("bear", 25_000)

    def test_single_cycle(self):
        from scalp_ml.week2.curriculum_trainer import make_cyclic_schedule
        schedule = make_cyclic_schedule(
            regime_order=["sideways", "bull", "volatile", "bear"],
            steps_per_regime=100_000,
            total_cycles=1,
        )
        assert len(schedule) == 4
        assert [s[0] for s in schedule] == ["sideways", "bull", "volatile", "bear"]

    def test_ten_cycles(self):
        from scalp_ml.week2.curriculum_trainer import make_cyclic_schedule
        schedule = make_cyclic_schedule(
            regime_order=["sideways", "bull", "volatile", "bear"],
            steps_per_regime=25_000,
            total_cycles=10,
        )
        # 4 * 10 = 40 entries
        assert len(schedule) == 40
        total_steps = sum(s[1] for s in schedule)
        assert total_steps == 1_000_000

    def test_empty_order(self):
        from scalp_ml.week2.curriculum_trainer import make_cyclic_schedule
        schedule = make_cyclic_schedule([], total_cycles=5)
        assert schedule == []


# ═══════════════════════════════════════════════════
# measure_regime_correlation 테스트
# ═══════════════════════════════════════════════════

class TestMeasureRegimeCorrelation:
    """레짐간 행동 상관관계 분석."""

    def test_identical_actions_high_correlation(self):
        from scalp_ml.week2.curriculum_trainer import measure_regime_correlation
        actions = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0], dtype=float)
        result = measure_regime_correlation({
            "bull": actions,
            "bear": actions,
        })
        assert result["avg_correlation"] == pytest.approx(1.0, abs=0.01)
        assert result["regime_specialized"] == False

    def test_opposite_actions_negative_correlation(self):
        from scalp_ml.week2.curriculum_trainer import measure_regime_correlation
        a = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0], dtype=float)
        b = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1], dtype=float)
        result = measure_regime_correlation({"bull": a, "bear": b})
        assert result["avg_correlation"] < 0
        assert result["regime_specialized"] == True

    def test_random_actions_low_correlation(self):
        from scalp_ml.week2.curriculum_trainer import measure_regime_correlation
        rng = np.random.RandomState(42)
        result = measure_regime_correlation({
            "bull": rng.rand(100),
            "bear": rng.rand(100),
            "sideways": rng.rand(100),
        })
        # 랜덤이면 상관 낮음
        assert abs(result["avg_correlation"]) < 0.3

    def test_too_few_actions_skipped(self):
        from scalp_ml.week2.curriculum_trainer import measure_regime_correlation
        result = measure_regime_correlation({
            "bull": np.array([1, 0]),
            "bear": np.array([0, 1]),
        })
        # min_len < 10 -> skip
        assert result["pairwise_correlation"] == {}
        assert result["avg_correlation"] == 0

    def test_single_regime(self):
        from scalp_ml.week2.curriculum_trainer import measure_regime_correlation
        result = measure_regime_correlation({
            "bull": np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0], dtype=float),
        })
        # 쌍이 없으므로 비어있음
        assert result["pairwise_correlation"] == {}


# ═══════════════════════════════════════════════════
# AblationRewardWrapper 테스트
# ═══════════════════════════════════════════════════

class TestAblationRewardWrapper:
    """보상 성분 선택적 활성화/비활성화."""

    def test_all_components_active(self):
        from scalp_ml.week2.reward_ablation import AblationRewardWrapper, REWARD_COMPONENTS
        wrapper = AblationRewardWrapper(REWARD_COMPONENTS.copy())
        reward_dict = {
            "components": {
                "pnl_reward": 1.0,
                "direction_reward": 0.5,
                "sharpe_reward": 0.3,
                "mdd_penalty": -0.2,
                "trade_pnl_bonus": 0.1,
            }
        }
        total = wrapper.modify_reward(reward_dict)
        assert total == pytest.approx(1.7)

    def test_single_component(self):
        from scalp_ml.week2.reward_ablation import AblationRewardWrapper
        wrapper = AblationRewardWrapper(["pnl_reward"])
        reward_dict = {
            "components": {
                "pnl_reward": 2.0,
                "direction_reward": 1.0,
                "sharpe_reward": 0.5,
                "mdd_penalty": -0.3,
                "trade_pnl_bonus": 0.1,
            }
        }
        total = wrapper.modify_reward(reward_dict)
        assert total == pytest.approx(2.0)

    def test_leave_one_out(self):
        from scalp_ml.week2.reward_ablation import AblationRewardWrapper, REWARD_COMPONENTS
        # mdd_penalty 제거
        active = [c for c in REWARD_COMPONENTS if c != "mdd_penalty"]
        wrapper = AblationRewardWrapper(active)
        reward_dict = {
            "components": {
                "pnl_reward": 1.0,
                "direction_reward": 0.5,
                "sharpe_reward": 0.3,
                "mdd_penalty": -0.2,
                "trade_pnl_bonus": 0.1,
            }
        }
        total = wrapper.modify_reward(reward_dict)
        # 1.0 + 0.5 + 0.3 + 0.1 = 1.9 (mdd_penalty 제외)
        assert total == pytest.approx(1.9)

    def test_empty_components_dict(self):
        from scalp_ml.week2.reward_ablation import AblationRewardWrapper, REWARD_COMPONENTS
        wrapper = AblationRewardWrapper(REWARD_COMPONENTS.copy())
        total = wrapper.modify_reward({"components": {}})
        assert total == 0.0

    def test_missing_components_key(self):
        from scalp_ml.week2.reward_ablation import AblationRewardWrapper
        wrapper = AblationRewardWrapper(["pnl_reward"])
        total = wrapper.modify_reward({})
        assert total == 0.0

    def test_invalid_component_raises(self):
        from scalp_ml.week2.reward_ablation import AblationRewardWrapper
        with pytest.raises(ValueError, match="Unknown component"):
            AblationRewardWrapper(["nonexistent_reward"])

    def test_pairwise_components(self):
        from scalp_ml.week2.reward_ablation import AblationRewardWrapper
        wrapper = AblationRewardWrapper(["pnl_reward", "direction_reward"])
        reward_dict = {
            "components": {
                "pnl_reward": 1.0,
                "direction_reward": 0.5,
                "sharpe_reward": 0.3,
                "mdd_penalty": -0.2,
                "trade_pnl_bonus": 0.1,
            }
        }
        total = wrapper.modify_reward(reward_dict)
        assert total == pytest.approx(1.5)


# ═══════════════════════════════════════════════════
# REWARD_COMPONENTS / COMPONENT_LABELS 상수 테스트
# ═══════════════════════════════════════════════════

class TestRewardConstants:
    """보상 성분 상수 검증."""

    def test_five_components(self):
        from scalp_ml.week2.reward_ablation import REWARD_COMPONENTS
        assert len(REWARD_COMPONENTS) == 5

    def test_component_names(self):
        from scalp_ml.week2.reward_ablation import REWARD_COMPONENTS
        expected = ["pnl_reward", "direction_reward", "sharpe_reward", "mdd_penalty", "trade_pnl_bonus"]
        assert REWARD_COMPONENTS == expected

    def test_labels_match_components(self):
        from scalp_ml.week2.reward_ablation import REWARD_COMPONENTS, COMPONENT_LABELS
        for comp in REWARD_COMPONENTS:
            assert comp in COMPONENT_LABELS, f"{comp}에 대한 라벨이 없음"

    def test_labels_are_strings(self):
        from scalp_ml.week2.reward_ablation import COMPONENT_LABELS
        for key, label in COMPONENT_LABELS.items():
            assert isinstance(label, str)


# ═══════════════════════════════════════════════════
# _analyze_ablation 함수 테스트
# ═══════════════════════════════════════════════════

class TestAnalyzeAblation:
    """보상 해부 결과 분석 함수."""

    def test_analyze_empty_results(self):
        from scalp_ml.week2.reward_ablation import _analyze_ablation, REWARD_COMPONENTS
        analysis = _analyze_ablation([])
        assert analysis["recommended"] == REWARD_COMPONENTS

    def test_analyze_with_loo_results(self):
        from scalp_ml.week2.reward_ablation import _analyze_ablation
        results = [
            {"type": "leave_one_out", "removed": "pnl_reward", "tag": "loo_no_PnL", "sharpe": 0.5, "total_return_pct": 3.0},
            {"type": "leave_one_out", "removed": "mdd_penalty", "tag": "loo_no_MDD", "sharpe": 0.8, "total_return_pct": 5.0},
        ]
        analysis = _analyze_ablation(results)
        assert "component_importance" in analysis
        assert "pnl_reward" in analysis["component_importance"]
        assert "mdd_penalty" in analysis["component_importance"]

    def test_analyze_best_is_loo(self):
        from scalp_ml.week2.reward_ablation import _analyze_ablation
        results = [
            {"type": "leave_one_out", "removed": "mdd_penalty", "tag": "loo", "sharpe": 1.5, "total_return_pct": 8.0},
            {"type": "single", "component": "pnl_reward", "tag": "single", "sharpe": 0.3, "total_return_pct": 2.0},
        ]
        analysis = _analyze_ablation(results)
        # Best is LOO (sharpe 1.5) -> mdd_penalty 제거한 구성
        recommended = analysis["recommended"]
        assert "mdd_penalty" not in recommended
        assert len(recommended) == 4

    def test_analyze_best_is_single(self):
        from scalp_ml.week2.reward_ablation import _analyze_ablation
        results = [
            {"type": "single", "component": "direction_reward", "tag": "single", "sharpe": 2.0, "total_return_pct": 10.0},
            {"type": "leave_one_out", "removed": "pnl_reward", "tag": "loo", "sharpe": 0.1, "total_return_pct": 1.0},
        ]
        analysis = _analyze_ablation(results)
        assert analysis["recommended"] == ["direction_reward"]

    def test_analyze_best_is_pairwise(self):
        from scalp_ml.week2.reward_ablation import _analyze_ablation
        results = [
            {"type": "pairwise", "components": ["pnl_reward", "sharpe_reward"], "tag": "pair", "sharpe": 3.0, "total_return_pct": 15.0},
        ]
        analysis = _analyze_ablation(results)
        assert analysis["recommended"] == ["pnl_reward", "sharpe_reward"]

    def test_analyze_handles_errors(self):
        from scalp_ml.week2.reward_ablation import _analyze_ablation, REWARD_COMPONENTS
        results = [
            {"type": "leave_one_out", "removed": "pnl_reward", "error": "training failed"},
        ]
        analysis = _analyze_ablation(results)
        # 에러 결과는 무시 -> 기본 추천
        assert analysis["recommended"] == REWARD_COMPONENTS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
