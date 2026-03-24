"""
Phase 2 자동화 스크립트 유닛 테스트

테스트 대상:
  1. scripts/model_retrainer.py — check_and_queue(), process_queue(), get_queue_status()
  2. scripts/regime_learner.py — learn_weights(), get_learned_weights(), get_learning_summary()
  3. agents/orchestrator.py — get_transition_weight(), _get_warmup_threshold(), _in_transition(), _clear_transition()
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

KST = timezone(timedelta(hours=9))


# ============================================================
# Helpers
# ============================================================

DEFAULT_STATE = {
    "active_agent": "moderate",
    "transition_from": None,
    "transition_started": None,
    "transition_duration_min": None,
    "last_switch_time": None,
    "last_trade_time": None,
    "consecutive_losses": 0,
    "switch_history": [],
}


def _make_orchestrator(active="moderate", state_overrides=None):
    """테스트용 Orchestrator 팩토리."""
    with patch("agents.orchestrator._load_state") as mock:
        state = {**DEFAULT_STATE, "active_agent": active}
        if state_overrides:
            state.update(state_overrides)
        mock.return_value = state
        from agents.orchestrator import Orchestrator
        orch = Orchestrator()
        orch._learning_data = None
        orch._performance = {}
        return orch


def _now_kst_iso() -> str:
    return datetime.now(KST).isoformat()


def _past_kst_iso(hours: int = 0, minutes: int = 0) -> str:
    return (datetime.now(KST) - timedelta(hours=hours, minutes=minutes)).isoformat()


# ============================================================
# model_retrainer 테스트
# ============================================================


class TestModelRetrainerCheckAndQueue:
    """check_and_queue() 적격성 검사 테스트"""

    @patch("scripts.model_retrainer._log_training_queue_to_db", return_value="test-cycle-id")
    @patch("scripts.model_retrainer._get_decisions_count_since", return_value=100)
    @patch("scripts.model_retrainer._save_queue")
    @patch("scripts.model_retrainer._load_queue")
    @patch("scripts.model_retrainer._load_feedback_state")
    def test_no_disabled_models(self, mock_fb, mock_lq, mock_sq, mock_count, mock_db):
        """비활성 모델이 없으면 queued=0"""
        from scripts.model_retrainer import check_and_queue

        mock_fb.return_value = {"disabled_rl_models": [], "rl_model_scores": {}, "last_updated": None}
        mock_lq.return_value = {"queue": [], "history": [], "last_checked": None}

        result = check_and_queue()
        assert result["queued"] == 0
        assert result["skipped"] == 0

    @patch("scripts.model_retrainer._log_training_queue_to_db", return_value="test-cycle-id")
    @patch("scripts.model_retrainer._get_decisions_count_since", return_value=100)
    @patch("scripts.model_retrainer._save_queue")
    @patch("scripts.model_retrainer._load_queue")
    @patch("scripts.model_retrainer._load_feedback_state")
    def test_skip_disabled_under_24h(self, mock_fb, mock_lq, mock_sq, mock_count, mock_db):
        """비활성화 후 24시간 미경과 시 스킵"""
        from scripts.model_retrainer import check_and_queue

        mock_fb.return_value = {
            "disabled_rl_models": ["sb3"],
            "rl_model_scores": {"sb3": {"accuracy": 0.3}},
            "last_updated": _past_kst_iso(hours=10),  # 10시간 전
        }
        mock_lq.return_value = {"queue": [], "history": [], "last_checked": None}

        result = check_and_queue()
        assert result["queued"] == 0
        assert result["skipped"] == 1

    @patch("scripts.model_retrainer._log_training_queue_to_db", return_value="test-cycle-id")
    @patch("scripts.model_retrainer._get_decisions_count_since", return_value=30)
    @patch("scripts.model_retrainer._save_queue")
    @patch("scripts.model_retrainer._load_queue")
    @patch("scripts.model_retrainer._load_feedback_state")
    def test_skip_insufficient_samples(self, mock_fb, mock_lq, mock_sq, mock_count, mock_db):
        """새 데이터 50건 미만 시 스킵"""
        from scripts.model_retrainer import check_and_queue

        mock_fb.return_value = {
            "disabled_rl_models": ["sb3"],
            "rl_model_scores": {"sb3": {"accuracy": 0.3}},
            "last_updated": _past_kst_iso(hours=30),  # 30시간 전 — 24h 충족
        }
        mock_lq.return_value = {"queue": [], "history": [], "last_checked": None}

        result = check_and_queue()
        assert result["queued"] == 0
        assert result["skipped"] == 1
        assert any("30건" in d for d in result["details"])

    @patch("scripts.model_retrainer._log_training_queue_to_db", return_value="test-cycle-id")
    @patch("scripts.model_retrainer._get_decisions_count_since", return_value=100)
    @patch("scripts.model_retrainer._save_queue")
    @patch("scripts.model_retrainer._load_queue")
    @patch("scripts.model_retrainer._load_feedback_state")
    def test_skip_48h_cooldown(self, mock_fb, mock_lq, mock_sq, mock_count, mock_db):
        """마지막 재훈련 시도 후 48시간 미경과 시 스킵"""
        from scripts.model_retrainer import check_and_queue

        mock_fb.return_value = {
            "disabled_rl_models": ["sb3"],
            "rl_model_scores": {"sb3": {"accuracy": 0.3}},
            "last_updated": _past_kst_iso(hours=30),
        }
        mock_lq.return_value = {
            "queue": [],
            "history": [{
                "model_name": "sb3",
                "queued_at": _past_kst_iso(hours=20),  # 20시간 전 — 48h 미충족
                "status": "failed",
            }],
            "last_checked": None,
        }

        result = check_and_queue()
        assert result["queued"] == 0
        assert result["skipped"] == 1

    @patch("scripts.model_retrainer._log_training_queue_to_db", return_value="test-cycle-id")
    @patch("scripts.model_retrainer._get_decisions_count_since", return_value=100)
    @patch("scripts.model_retrainer._save_queue")
    @patch("scripts.model_retrainer._load_queue")
    @patch("scripts.model_retrainer._load_feedback_state")
    def test_eligible_model_queued(self, mock_fb, mock_lq, mock_sq, mock_count, mock_db):
        """모든 조건 충족 시 큐에 등록"""
        from scripts.model_retrainer import check_and_queue

        mock_fb.return_value = {
            "disabled_rl_models": ["sb3"],
            "rl_model_scores": {"sb3": {"accuracy": 0.25}},
            "last_updated": _past_kst_iso(hours=30),
        }
        mock_lq.return_value = {
            "queue": [],
            "history": [{
                "model_name": "sb3",
                "queued_at": _past_kst_iso(hours=72),  # 72시간 전 — 48h 충족
                "status": "failed",
            }],
            "last_checked": None,
        }

        result = check_and_queue()
        assert result["queued"] == 1
        assert result["skipped"] == 0

    @patch("scripts.model_retrainer._log_training_queue_to_db", return_value="test-cycle-id")
    @patch("scripts.model_retrainer._get_decisions_count_since", return_value=100)
    @patch("scripts.model_retrainer._save_queue")
    @patch("scripts.model_retrainer._load_queue")
    @patch("scripts.model_retrainer._load_feedback_state")
    def test_skip_already_in_queue(self, mock_fb, mock_lq, mock_sq, mock_count, mock_db):
        """이미 큐에 있는 모델은 스킵"""
        from scripts.model_retrainer import check_and_queue

        mock_fb.return_value = {
            "disabled_rl_models": ["sb3"],
            "rl_model_scores": {"sb3": {"accuracy": 0.3}},
            "last_updated": _past_kst_iso(hours=30),
        }
        mock_lq.return_value = {
            "queue": [{"model_name": "sb3", "status": "pending"}],
            "history": [],
            "last_checked": None,
        }

        result = check_and_queue()
        assert result["queued"] == 0
        assert result["skipped"] == 1


class TestModelRetrainerProcessQueue:
    """process_queue() 큐 처리 테스트"""

    @patch("scripts.model_retrainer._save_queue")
    @patch("scripts.model_retrainer._load_queue")
    def test_empty_queue(self, mock_lq, mock_sq):
        """빈 큐에서 아무것도 처리하지 않음"""
        from scripts.model_retrainer import process_queue

        mock_lq.return_value = {"queue": [], "history": [], "last_checked": None}

        result = process_queue()
        assert result["processed"] == 0
        assert result["failed"] == 0
        assert result["deferred"] == 0

    @patch("scripts.model_retrainer._update_training_status_db")
    @patch("scripts.model_retrainer._save_queue")
    @patch("scripts.model_retrainer._load_queue")
    def test_deferred_gpu_models(self, mock_lq, mock_sq, mock_update):
        """GPU 필요 모델(dt, multi_agent, offline)은 deferred 처리"""
        from scripts.model_retrainer import process_queue

        mock_lq.return_value = {
            "queue": [
                {"model_name": "dt", "status": "pending", "db_cycle_id": "c1"},
                {"model_name": "multi_agent", "status": "pending", "db_cycle_id": "c2"},
            ],
            "history": [],
            "last_checked": None,
        }

        result = process_queue()
        assert result["deferred"] == 2
        assert result["processed"] == 0

    @patch("scripts.model_retrainer._update_training_status_db")
    @patch("scripts.model_retrainer._save_queue")
    @patch("scripts.model_retrainer._load_queue")
    def test_non_primary_sb3_deferred(self, mock_lq, mock_sq, mock_update):
        """primary 머신이 아닐 때 sb3는 deferred"""
        from scripts.model_retrainer import process_queue

        mock_lq.return_value = {
            "queue": [
                {"model_name": "sb3", "status": "pending", "db_cycle_id": "c1"},
            ],
            "history": [],
            "last_checked": None,
        }

        with patch("utils.machine.is_primary", return_value=False):
            result = process_queue()
        assert result["deferred"] == 1

    @patch("scripts.model_retrainer._update_training_status_db")
    @patch("scripts.model_retrainer._save_queue")
    @patch("scripts.model_retrainer._load_queue")
    def test_unknown_model_deferred(self, mock_lq, mock_sq, mock_update):
        """미지원 모델은 deferred 처리"""
        from scripts.model_retrainer import process_queue

        mock_lq.return_value = {
            "queue": [
                {"model_name": "custom_xyz", "status": "pending", "db_cycle_id": "c1"},
            ],
            "history": [],
            "last_checked": None,
        }

        result = process_queue()
        assert result["deferred"] == 1

    @patch("scripts.model_retrainer._save_queue")
    @patch("scripts.model_retrainer._load_queue")
    def test_skip_non_pending_entries(self, mock_lq, mock_sq):
        """pending이 아닌 항목(training, completed 등)은 스킵"""
        from scripts.model_retrainer import process_queue

        mock_lq.return_value = {
            "queue": [
                {"model_name": "sb3", "status": "training", "db_cycle_id": "c1"},
                {"model_name": "dt", "status": "completed", "db_cycle_id": "c2"},
            ],
            "history": [],
            "last_checked": None,
        }

        result = process_queue()
        # completed entry moves to history, training stays
        assert result["processed"] == 0
        assert result["failed"] == 0

    @patch("scripts.model_retrainer._update_training_status_db")
    @patch("scripts.model_retrainer._save_queue")
    @patch("scripts.model_retrainer._load_queue")
    def test_history_moves_completed(self, mock_lq, mock_sq, mock_update):
        """완료/실패/deferred 항목은 history로 이동"""
        from scripts.model_retrainer import process_queue

        queue_data = {
            "queue": [
                {"model_name": "dt", "status": "pending", "db_cycle_id": "c1"},
            ],
            "history": [],
            "last_checked": None,
        }
        mock_lq.return_value = queue_data

        process_queue()

        # _save_queue가 호출됨을 확인하고, 저장된 데이터에서 queue는 비고 history에 dt가 있는지 확인
        saved = mock_sq.call_args[0][0]
        assert len(saved["queue"]) == 0
        assert len(saved["history"]) == 1
        assert saved["history"][0]["model_name"] == "dt"


class TestModelRetrainerGetQueueStatus:
    """get_queue_status() 테스트"""

    @patch("scripts.model_retrainer._load_feedback_state")
    @patch("scripts.model_retrainer._load_queue")
    def test_status_output(self, mock_lq, mock_fb):
        """상태 조회가 올바른 구조를 반환"""
        from scripts.model_retrainer import get_queue_status

        mock_lq.return_value = {
            "queue": [
                {"model_name": "sb3", "status": "pending"},
                {"model_name": "dt", "status": "training"},
                {"model_name": "historical", "status": "completed"},
            ],
            "history": [{"model_name": "old", "status": "completed"}] * 3,
            "last_checked": "2026-03-16T10:00:00+09:00",
        }
        mock_fb.return_value = {
            "disabled_rl_models": ["sb3", "dt"],
            "rl_model_scores": {},
            "last_updated": None,
        }

        status = get_queue_status()
        assert len(status["disabled_models"]) == 2
        assert len(status["active_queue"]) == 2  # pending + training only
        assert status["total_history"] == 3
        assert status["last_checked"] == "2026-03-16T10:00:00+09:00"


# ============================================================
# regime_learner 테스트
# ============================================================


class TestRegimeLearnerLearnWeights:
    """learn_weights() 테스트"""

    @patch("scripts.regime_learner._fetch_decisions", return_value=[])
    def test_empty_data_returns_none(self, mock_fetch):
        """데이터 없으면 None 반환"""
        from scripts.regime_learner import learn_weights
        result = learn_weights()
        assert result is None

    @patch("scripts.regime_learner.WEIGHTS_FILE")
    @patch("scripts.regime_learner._fetch_decisions")
    def test_single_regime_insufficient_samples(self, mock_fetch, mock_wf, tmp_path):
        """한 레짐에 MIN_SAMPLES 미만이면 기본 가중치 사용"""
        from scripts.regime_learner import learn_weights, REGIMES, DEFAULT_REGIME_WEIGHTS, MIN_SAMPLES

        # sideways에 3건만 (MIN_SAMPLES=5 미만)
        rows = []
        for _ in range(3):
            rows.append({
                "market_data_snapshot": json.dumps({"regime": "sideways"}),
                "was_correct_4h": True,
                "outcome_4h_pct": 1.0,
                "confidence": 0.7,
                "created_at": "2026-03-15T10:00:00+00:00",
            })

        mock_fetch.return_value = rows

        wf = tmp_path / "regime_weights_learned.json"
        mock_wf.__class__ = type(wf)
        # Use tmp_path for file I/O
        with patch("scripts.regime_learner.WEIGHTS_FILE", wf):
            result = learn_weights()

        assert result is not None
        # sideways 샘플이 3건이므로 기본 가중치 사용
        assert result["sample_counts"]["sideways"] == 3
        assert result["regime_accuracy"]["sideways"] is None
        # 기본 가중치와 동일해야 함
        assert result["weights"]["sideways"] == DEFAULT_REGIME_WEIGHTS["sideways"]

    @patch("scripts.regime_learner.WEIGHTS_FILE")
    @patch("scripts.regime_learner._fetch_decisions")
    def test_sufficient_samples_calculates_weights(self, mock_fetch, mock_wf, tmp_path):
        """충분한 샘플이면 학습된 가중치 계산"""
        from scripts.regime_learner import learn_weights, MODELS

        rows = []
        for i in range(10):
            rows.append({
                "market_data_snapshot": json.dumps({
                    "regime": "bull_strong",
                    "rl_advisory": {
                        "sb3_action": 0.5,
                        "dt_action": 0.4,
                        "multi_agent_action": -0.1,
                        "offline_action": 0.2,
                        "historical_action": 0.6,
                    },
                }),
                "was_correct_4h": i < 7,  # 70% 정확도
                "outcome_4h_pct": 1.5 if i < 7 else -1.0,
                "confidence": 0.7,
                "created_at": "2026-03-15T10:00:00+00:00",
            })

        mock_fetch.return_value = rows
        wf = tmp_path / "regime_weights_learned.json"

        with patch("scripts.regime_learner.WEIGHTS_FILE", wf):
            result = learn_weights()

        assert result is not None
        assert result["sample_counts"]["bull_strong"] == 10
        assert result["regime_accuracy"]["bull_strong"] == 0.7
        # 가중치 합이 1.0에 가까워야 함
        w = result["weights"]["bull_strong"]
        total = sum(w.values())
        assert abs(total - 1.0) < 0.01

    @patch("scripts.regime_learner.WEIGHTS_FILE")
    @patch("scripts.regime_learner._fetch_decisions")
    def test_weights_sum_to_one(self, mock_fetch, mock_wf, tmp_path):
        """모든 학습된 레짐의 가중치 합이 1.0"""
        from scripts.regime_learner import learn_weights, REGIMES

        rows = []
        for regime in REGIMES:
            for i in range(8):
                rows.append({
                    "market_data_snapshot": json.dumps({
                        "regime": regime,
                        "rl_advisory": {
                            "sb3_action": 0.5,
                            "dt_action": 0.3,
                            "multi_agent_action": 0.1,
                            "offline_action": -0.2,
                            "historical_action": 0.4,
                        },
                    }),
                    "was_correct_4h": i < 5,
                    "outcome_4h_pct": 1.0 if i < 5 else -0.5,
                    "confidence": 0.6,
                    "created_at": "2026-03-15T10:00:00+00:00",
                })

        mock_fetch.return_value = rows
        wf = tmp_path / "regime_weights_learned.json"

        with patch("scripts.regime_learner.WEIGHTS_FILE", wf):
            result = learn_weights()

        for regime in REGIMES:
            w = result["weights"][regime]
            assert abs(sum(w.values()) - 1.0) < 0.01, f"{regime} weights don't sum to 1.0"

    @patch("scripts.regime_learner._fetch_decisions")
    def test_string_snapshot_parsing(self, mock_fetch, tmp_path):
        """market_data_snapshot이 문자열일 때도 정상 파싱"""
        from scripts.regime_learner import _extract_regime, _extract_model_predictions

        snapshot_str = json.dumps({
            "regime": "bear_weak",
            "rl_advisory": {"sb3_action": 0.5, "dt_action": -0.3},
        })

        assert _extract_regime(snapshot_str) == "bear_weak"
        preds = _extract_model_predictions(snapshot_str)
        assert preds is not None
        assert "sb3" in preds


class TestRegimeLearnerGetLearnedWeights:
    """get_learned_weights() 테스트"""

    def test_no_file_returns_none(self, tmp_path):
        """파일 없으면 None"""
        from scripts.regime_learner import get_learned_weights

        with patch("scripts.regime_learner.WEIGHTS_FILE", tmp_path / "nonexistent.json"):
            result = get_learned_weights("sideways")
        assert result is None

    def test_insufficient_samples_returns_none(self, tmp_path):
        """샘플 수 부족이면 None"""
        from scripts.regime_learner import get_learned_weights

        wf = tmp_path / "regime_weights_learned.json"
        wf.write_text(json.dumps({
            "weights": {"sideways": {"sb3": 0.2, "dt": 0.2, "multi_agent": 0.2, "offline": 0.2, "historical": 0.2}},
            "sample_counts": {"sideways": 3},  # < MIN_SAMPLES(5)
        }))

        with patch("scripts.regime_learner.WEIGHTS_FILE", wf):
            result = get_learned_weights("sideways")
        assert result is None

    def test_sufficient_samples_returns_weights(self, tmp_path):
        """충분한 샘플이면 가중치 반환"""
        from scripts.regime_learner import get_learned_weights

        expected = {"sb3": 0.25, "dt": 0.20, "multi_agent": 0.15, "offline": 0.15, "historical": 0.25}
        wf = tmp_path / "regime_weights_learned.json"
        wf.write_text(json.dumps({
            "weights": {"bull_strong": expected},
            "sample_counts": {"bull_strong": 10},
        }))

        with patch("scripts.regime_learner.WEIGHTS_FILE", wf):
            result = get_learned_weights("bull_strong")
        assert result == expected

    def test_corrupted_file_returns_none(self, tmp_path):
        """손상된 JSON 파일이면 None"""
        from scripts.regime_learner import get_learned_weights

        wf = tmp_path / "regime_weights_learned.json"
        wf.write_text("{corrupted json!!!")

        with patch("scripts.regime_learner.WEIGHTS_FILE", wf):
            result = get_learned_weights("sideways")
        assert result is None


class TestRegimeLearnerGetLearningSummary:
    """get_learning_summary() 테스트"""

    def test_no_file_returns_none(self, tmp_path):
        """파일 없으면 None"""
        from scripts.regime_learner import get_learning_summary

        with patch("scripts.regime_learner.WEIGHTS_FILE", tmp_path / "nonexistent.json"):
            result = get_learning_summary()
        assert result is None

    def test_returns_full_state(self, tmp_path):
        """정상 파일이면 전체 상태 반환"""
        from scripts.regime_learner import get_learning_summary

        data = {
            "weights": {"sideways": {"sb3": 0.2}},
            "sample_counts": {"sideways": 10},
            "regime_accuracy": {"sideways": 0.65},
            "last_updated": "2026-03-16T10:00:00+09:00",
        }
        wf = tmp_path / "regime_weights_learned.json"
        wf.write_text(json.dumps(data))

        with patch("scripts.regime_learner.WEIGHTS_FILE", wf):
            result = get_learning_summary()
        assert result == data


class TestRegimeLearnerNormalizeWeights:
    """_normalize_weights() 엣지 케이스"""

    def test_zero_total_gives_equal_weights(self):
        """전체 합이 0이면 균등 분배"""
        from scripts.regime_learner import _normalize_weights

        result = _normalize_weights({"a": 0, "b": 0, "c": 0})
        assert abs(sum(result.values()) - 1.0) < 0.01
        for v in result.values():
            assert abs(v - 1.0 / 3) < 0.01

    def test_normal_normalization(self):
        """정상 정규화"""
        from scripts.regime_learner import _normalize_weights

        result = _normalize_weights({"a": 2, "b": 3, "c": 5})
        assert abs(result["a"] - 0.2) < 0.01
        assert abs(result["b"] - 0.3) < 0.01
        assert abs(result["c"] - 0.5) < 0.01


# ============================================================
# Orchestrator 워밍업 전환 테스트
# ============================================================


class TestOrchestratorInTransition:
    """_in_transition() 테스트"""

    @patch("agents.orchestrator._save_state")
    def test_not_in_transition_when_fields_none(self, mock_save):
        """전환 필드가 None이면 전환 중이 아님"""
        orch = _make_orchestrator()
        assert orch._in_transition() is False

    @patch("agents.orchestrator._save_state")
    def test_in_transition_when_all_fields_set(self, mock_save):
        """전환 필드가 모두 설정되어 있으면 전환 중"""
        orch = _make_orchestrator(state_overrides={
            "transition_from": "conservative",
            "transition_started": _now_kst_iso(),
            "transition_duration_min": 30,
        })
        assert orch._in_transition() is True

    @patch("agents.orchestrator._save_state")
    def test_not_in_transition_partial_fields(self, mock_save):
        """전환 필드가 부분적으로만 설정되면 전환 중 아님"""
        orch = _make_orchestrator(state_overrides={
            "transition_from": "conservative",
            "transition_started": None,  # missing
            "transition_duration_min": 30,
        })
        assert orch._in_transition() is False


class TestOrchestratorGetTransitionWeight:
    """get_transition_weight() — 선형 블렌딩 0.3/0.7 → 1.0/0.0 (30분)"""

    @patch("agents.orchestrator._save_state")
    def test_no_transition_returns_full_new(self, mock_save):
        """전환 중이 아니면 (1.0, 0.0)"""
        orch = _make_orchestrator()
        w_new, w_old = orch.get_transition_weight()
        assert w_new == 1.0
        assert w_old == 0.0

    @patch("agents.orchestrator._save_state")
    def test_transition_start_returns_0_3(self, mock_save):
        """전환 시작 직후 신규 가중치 ~0.3"""
        orch = _make_orchestrator(state_overrides={
            "transition_from": "conservative",
            "transition_started": _now_kst_iso(),
            "transition_duration_min": 30,
        })
        w_new, w_old = orch.get_transition_weight()
        assert 0.28 <= w_new <= 0.35
        assert 0.65 <= w_old <= 0.72

    @patch("agents.orchestrator._save_state")
    def test_transition_midpoint(self, mock_save):
        """전환 중간(15분)에서 신규 가중치 ~0.65"""
        orch = _make_orchestrator(state_overrides={
            "transition_from": "conservative",
            "transition_started": _past_kst_iso(minutes=15),
            "transition_duration_min": 30,
        })
        w_new, w_old = orch.get_transition_weight()
        # At 15 min: 0.3 + 0.7 * (15/30) = 0.3 + 0.35 = 0.65
        assert 0.60 <= w_new <= 0.70
        assert 0.30 <= w_old <= 0.40

    @patch("agents.orchestrator._save_state")
    def test_transition_auto_clear_after_30min(self, mock_save):
        """30분 경과 후 자동 전환 완료 → (1.0, 0.0)"""
        orch = _make_orchestrator(state_overrides={
            "transition_from": "conservative",
            "transition_started": _past_kst_iso(minutes=35),
            "transition_duration_min": 30,
        })
        w_new, w_old = orch.get_transition_weight()
        assert w_new == 1.0
        assert w_old == 0.0
        # 전환 상태가 클리어되었는지 확인
        assert orch.state["transition_from"] is None

    @patch("agents.orchestrator._save_state")
    def test_corrupted_started_field_clears(self, mock_save):
        """transition_started가 파싱 불가능한 문자열이면 전환 클리어"""
        orch = _make_orchestrator(state_overrides={
            "transition_from": "conservative",
            "transition_started": "not-a-date",
            "transition_duration_min": 30,
        })
        w_new, w_old = orch.get_transition_weight()
        assert w_new == 1.0
        assert w_old == 0.0
        assert orch.state["transition_from"] is None


class TestOrchestratorClearTransition:
    """_clear_transition() 테스트"""

    @patch("agents.orchestrator._save_state")
    def test_clears_all_fields(self, mock_save):
        """전환 필드 모두 None으로 초기화, _state_dirty 플래그 설정"""
        orch = _make_orchestrator(state_overrides={
            "transition_from": "conservative",
            "transition_started": _now_kst_iso(),
            "transition_duration_min": 30,
        })
        orch._clear_transition()
        assert orch.state["transition_from"] is None
        assert orch.state["transition_started"] is None
        assert orch.state["transition_duration_min"] is None
        assert orch._state_dirty is True  # batch save: _save_state 대신 dirty 플래그


class TestOrchestratorGetWarmupThreshold:
    """_get_warmup_threshold() — 블렌딩된 임계값"""

    @patch("agents.orchestrator._save_state")
    def test_no_transition_returns_none(self, mock_save):
        """전환 중이 아니면 None (원래 임계값 사용)"""
        orch = _make_orchestrator(active="moderate")
        result = orch._get_warmup_threshold(orch.active_agent)
        assert result is None

    @patch("agents.orchestrator._save_state")
    def test_conservative_to_aggressive_start(self, mock_save):
        """보수적→공격적 전환 시작: 0.3*40 + 0.7*60 = 54"""
        orch = _make_orchestrator(active="aggressive", state_overrides={
            "transition_from": "conservative",
            "transition_started": _now_kst_iso(),
            "transition_duration_min": 30,
        })
        agent = orch.active_agent
        threshold = orch._get_warmup_threshold(agent)
        assert threshold is not None
        # w_new ~0.3, w_old ~0.7 → 0.3*40 + 0.7*60 = 12 + 42 = 54
        assert 52 <= threshold <= 56

    @patch("agents.orchestrator._save_state")
    def test_conservative_to_aggressive_end(self, mock_save):
        """보수적→공격적 전환 완료(30분 후): None (원래 임계값)"""
        orch = _make_orchestrator(active="aggressive", state_overrides={
            "transition_from": "conservative",
            "transition_started": _past_kst_iso(minutes=35),
            "transition_duration_min": 30,
        })
        agent = orch.active_agent
        threshold = orch._get_warmup_threshold(agent)
        # 30분 경과 → 전환 완료 → None
        assert threshold is None

    @patch("agents.orchestrator._save_state")
    def test_moderate_to_conservative_midpoint(self, mock_save):
        """보통→보수적 전환 중간(15분): 블렌딩"""
        orch = _make_orchestrator(active="conservative", state_overrides={
            "transition_from": "moderate",
            "transition_started": _past_kst_iso(minutes=15),
            "transition_duration_min": 30,
        })
        agent = orch.active_agent
        threshold = orch._get_warmup_threshold(agent)
        assert threshold is not None
        # w_new ~0.65, w_old ~0.35 → 0.65*60 + 0.35*50 = 39 + 17.5 = 56.5 ≈ 57
        assert 54 <= threshold <= 59
