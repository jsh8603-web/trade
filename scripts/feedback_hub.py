#!/usr/bin/env python3
"""
Feedback Hub — 자율 개선 파이프라인의 핵심

예측 vs 실제 비교 → confidence 보정 → RL 모델 정확도 평가 → 자동 조정

기능:
  1. Confidence Calibration: 예측 confidence와 실제 결과를 비교하여 보정 계수 계산
  2. RL Model Scoring: 각 RL 모델의 예측 정확도를 측정, 부정확한 모델 비활성화
  3. Decision Quality Report: 최근 매매 품질 리포트 생성
  4. Auto-adjust: 다음 매매에 반영할 보정 파라미터를 data/feedback_hub_state.json에 저장

사용법:
  python scripts/feedback_hub.py              # 전체 분석 + 보정 계수 업데이트
  python scripts/feedback_hub.py report       # 리포트만 출력
  python scripts/feedback_hub.py calibrate    # confidence 보정만

파이프라인 통합:
  run_agents.py Phase 7에서 자동 호출
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

load_dotenv(PROJECT_DIR / ".env")

from core.db import db

STATE_FILE = PROJECT_DIR / "data" / "feedback_hub_state.json"
KST = timezone(timedelta(hours=9))


def _load_state() -> dict:
    """현재 feedback hub 상태를 로드한다."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "confidence_bias": 0.0,         # confidence 보정값 (-0.2 ~ +0.2)
        "rl_model_scores": {},           # 모델별 정확도 {model: {accuracy, samples, active}}
        "disabled_rl_models": [],        # 비활성화된 RL 모델 목록
        "calibration_history": [],       # 최근 10회 보정 이력
        "regime_weights": {},            # 레짐별 모델 가중치
        "last_updated": None,
    }


def _save_state(state: dict):
    """feedback hub 상태를 저장한다 (atomic write)."""
    state["last_updated"] = datetime.now(KST).isoformat()
    try:
        from scripts.atomic_write import atomic_json_save
        atomic_json_save(STATE_FILE, state)
    except ImportError:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ============================================================
# 1. Confidence Calibration
# ============================================================

def calibrate_confidence(days: int = 14, cached_decisions: list[dict] | None = None) -> dict:
    """예측 confidence와 실제 결과를 비교하여 보정 계수를 계산한다.

    Args:
        days: 분석 기간 (일)
        cached_decisions: phase_cache에서 전달받은 캐시 데이터 (None이면 직접 조회)

    Returns:
        {
            "confidence_bias": float,    # 보정값 (음수: 과신, 양수: 과소평가)
            "calibration_error": float,  # 보정 오차 (0에 가까울수록 좋음)
            "samples": int,
            "buckets": {conf_range: {predicted: X, actual: Y, count: N}}
        }
    """
    rows = None
    if cached_decisions is not None:
        # 캐시에서 was_correct_4h이 null이 아닌 것만 필터 + days 창 적용
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        rows = [
            d for d in cached_decisions
            if d.get("was_correct_4h") is not None and d.get("created_at", "") >= cutoff
        ]

    if rows is None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        try:
            rows = db.select(
                "decisions",
                select="confidence,decision,was_correct_4h,outcome_4h_pct",
                filters={
                    "created_at": f"gte.{cutoff}",
                    "was_correct_4h": "not.is.null",
                },
                limit=200,
            )
            if not rows:
                return {"confidence_bias": 0.0, "calibration_error": 0.0, "samples": 0}
        except Exception as e:
            print(f"[feedback_hub] calibration 예외: {e}", file=sys.stderr)
            return {"confidence_bias": 0.0, "calibration_error": 0.0, "samples": 0}

    if not rows:
        return {"confidence_bias": 0.0, "calibration_error": 0.0, "samples": 0}

    try:

        # confidence 구간별 실제 정확도 계산
        buckets = {
            "0.0-0.4": {"predicted": 0.3, "correct": 0, "total": 0},
            "0.4-0.6": {"predicted": 0.5, "correct": 0, "total": 0},
            "0.6-0.8": {"predicted": 0.7, "correct": 0, "total": 0},
            "0.8-1.0": {"predicted": 0.9, "correct": 0, "total": 0},
        }

        for row in rows:
            conf = float(row.get("confidence") or 0.5)
            correct = row.get("was_correct_4h", False)

            if conf < 0.4:
                bucket = "0.0-0.4"
            elif conf < 0.6:
                bucket = "0.4-0.6"
            elif conf < 0.8:
                bucket = "0.6-0.8"
            else:
                bucket = "0.8-1.0"

            buckets[bucket]["total"] += 1
            if correct:
                buckets[bucket]["correct"] += 1

        # 보정 오차 = 예측 confidence와 실제 정확도의 차이 평균
        total_error = 0.0
        total_samples = 0
        for bk, data in buckets.items():
            if data["total"] < 2:
                continue
            actual_rate = data["correct"] / data["total"]
            data["actual"] = round(actual_rate, 4)
            error = data["predicted"] - actual_rate  # 양수 = 과신
            total_error += error * data["total"]
            total_samples += data["total"]

        calibration_error = total_error / total_samples if total_samples > 0 else 0.0

        # 보정값: 과신이면 음수 보정 (confidence 낮춤), 과소평가면 양수
        confidence_bias = round(-calibration_error * 0.5, 4)  # 보수적으로 절반만 보정
        confidence_bias = max(-0.2, min(0.2, confidence_bias))  # 클램프

        return {
            "confidence_bias": confidence_bias,
            "calibration_error": round(calibration_error, 4),
            "samples": total_samples,
            "buckets": {k: v for k, v in buckets.items() if v["total"] > 0},
        }

    except Exception as e:
        print(f"[feedback_hub] calibration 예외: {e}", file=sys.stderr)
        return {"confidence_bias": 0.0, "calibration_error": 0.0, "samples": 0}


# ============================================================
# 2. RL Model Accuracy Scoring
# ============================================================

def score_rl_models(days: int = 14) -> dict:
    """각 RL 모델의 예측 정확도를 측정한다.

    Returns:
        {model_name: {"accuracy": float, "samples": int, "should_disable": bool}}
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    try:
        rows = db.select(
            "rl_model_predictions",
            select="sb3_action,dt_action,multi_agent_action,offline_action,"
                   "ensemble_direction,return_after_4h",
            filters={
                "created_at": f"gte.{cutoff}",
                "return_after_4h": "not.is.null",
            },
            limit=200,
        )
        if not rows:
            return {}

        # 모델별 정확도 계산
        models = {
            "sb3": {"correct": 0, "total": 0},
            "dt": {"correct": 0, "total": 0},
            "multi_agent": {"correct": 0, "total": 0},
            "offline": {"correct": 0, "total": 0},
            "ensemble": {"correct": 0, "total": 0},
        }

        for row in rows:
            actual_return = row.get("return_after_4h", 0)
            actual_dir = "buy" if actual_return > 0.5 else ("sell" if actual_return < -0.5 else "hold")

            # 앙상블 정확도
            ens_dir = row.get("ensemble_direction")
            if ens_dir:
                models["ensemble"]["total"] += 1
                if ens_dir == actual_dir or (ens_dir == "hold" and abs(actual_return) < 0.5):
                    models["ensemble"]["correct"] += 1

            # 개별 모델 정확도
            for model_key, action_key in [
                ("sb3", "sb3_action"), ("dt", "dt_action"),
                ("multi_agent", "multi_agent_action"), ("offline", "offline_action"),
            ]:
                action = row.get(action_key)
                if action is None:
                    continue
                predicted_dir = "buy" if action > 0.3 else ("sell" if action < -0.3 else "hold")
                models[model_key]["total"] += 1
                if predicted_dir == actual_dir or (predicted_dir == "hold" and abs(actual_return) < 0.5):
                    models[model_key]["correct"] += 1

        # 결과 정리
        result = {}
        for name, data in models.items():
            if data["total"] < 3:
                continue
            accuracy = data["correct"] / data["total"]
            result[name] = {
                "accuracy": round(accuracy, 4),
                "samples": data["total"],
                "should_disable": accuracy < 0.35 and data["total"] >= 10,
            }

        return result

    except Exception as e:
        print(f"[feedback_hub] RL scoring 예외: {e}", file=sys.stderr)
        return {}


# ============================================================
# 3. RAG Quality Feedback
# ============================================================

def evaluate_rag_quality(days: int = 14, cached_decisions: list[dict] | None = None) -> dict:
    """RAG recall이 매매 품질에 기여했는지 평가한다.

    RAG를 사용한 결정 vs 미사용 결정의 정확도 차이를 비교.

    Args:
        days: 분석 기간 (일)
        cached_decisions: phase_cache에서 전달받은 캐시 데이터 (None이면 직접 조회)
    """
    rows = None
    if cached_decisions is not None:
        rows = [
            d for d in cached_decisions
            if d.get("was_correct_4h") is not None and d.get("source") == "agent"
        ]

    if rows is None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        try:
            rows = db.select(
                "decisions",
                select="was_correct_4h,market_data_snapshot,source",
                filters={
                    "created_at": f"gte.{cutoff}",
                    "was_correct_4h": "not.is.null",
                    "source": "eq.agent",
                },
                limit=200,
            )
        except Exception as e:
            print(f"[feedback_hub] RAG quality 예외: {e}", file=sys.stderr)
            return {"rag_benefit": 0.0, "samples": 0}

    if not rows:
        return {"rag_benefit": 0.0, "samples": 0}

    try:
        rag_correct, rag_total = 0, 0
        no_rag_correct, no_rag_total = 0, 0

        for row in rows:
            correct = row.get("was_correct_4h", False)
            snapshot = row.get("market_data_snapshot", "{}")
            if isinstance(snapshot, str):
                try:
                    snapshot = json.loads(snapshot)
                except (json.JSONDecodeError, TypeError):
                    snapshot = {}
            if not isinstance(snapshot, dict):
                snapshot = {}

            # RAG 사용 여부: rag_context 또는 embedding 필드로 판단
            # snapshot_dir은 RAG와 무관하므로 사용하지 않음
            has_rag = bool(snapshot.get("rag_context") or snapshot.get("embedding"))
            if has_rag:
                rag_total += 1
                if correct:
                    rag_correct += 1
            else:
                no_rag_total += 1
                if correct:
                    no_rag_correct += 1

        # RAG 사용 샘플이 없으면 비교 불가 → benefit=0
        if rag_total == 0:
            return {"rag_benefit": 0.0, "samples": no_rag_total}

        rag_rate = rag_correct / rag_total if rag_total > 0 else 0
        no_rag_rate = no_rag_correct / no_rag_total if no_rag_total > 0 else 0
        benefit = rag_rate - no_rag_rate

        return {
            "rag_benefit": round(benefit, 4),
            "rag_accuracy": round(rag_rate, 4),
            "rag_samples": rag_total,
            "no_rag_accuracy": round(no_rag_rate, 4),
            "no_rag_samples": no_rag_total,
        }

    except Exception as e:
        print(f"[feedback_hub] RAG quality 예외: {e}", file=sys.stderr)
        return {"rag_benefit": 0.0, "samples": 0}


# ============================================================
# 4. Full Analysis & State Update
# ============================================================

def run_full_analysis(cached_decisions: list[dict] | None = None) -> dict:
    """전체 분석을 실행하고 보정 파라미터를 업데이트한다.

    Args:
        cached_decisions: phase_cache에서 전달받은 캐시 데이터 (None이면 직접 조회)
    """
    state = _load_state()

    # 1) Confidence 보정
    cal = calibrate_confidence(14, cached_decisions=cached_decisions)
    state["confidence_bias"] = cal["confidence_bias"]

    # 보정 이력 유지 (최근 10회)
    history = state.get("calibration_history", [])
    history.append({
        "timestamp": datetime.now(KST).isoformat(),
        "bias": cal["confidence_bias"],
        "error": cal["calibration_error"],
        "samples": cal["samples"],
    })
    state["calibration_history"] = history[-10:]

    # 2) RL 모델 정확도
    rl_scores = score_rl_models(14)
    state["rl_model_scores"] = rl_scores

    # 부정확한 모델 비활성화 목록
    disabled_models = [name for name, s in rl_scores.items() if s.get("should_disable")]
    state["disabled_rl_models"] = disabled_models

    # 3) RAG 품질
    rag = evaluate_rag_quality(14, cached_decisions=cached_decisions)
    state["rag_quality"] = rag

    _save_state(state)

    result = {
        "confidence_calibration": cal,
        "rl_model_scores": rl_scores,
        "disabled_rl_models": disabled_models,
        "rag_quality": rag,
        "state_file": str(STATE_FILE),
    }

    return result


def get_confidence_adjustment() -> float:
    """현재 confidence 보정값을 반환한다 (run_agents.py에서 호출)."""
    state = _load_state()
    return state.get("confidence_bias", 0.0)


def get_disabled_rl_models() -> list[str]:
    """비활성화된 RL 모델 목록을 반환한다 (run_agents.py에서 호출)."""
    state = _load_state()
    return state.get("disabled_rl_models", [])


def get_regime_model_weights() -> dict:
    """현재 레짐에 맞는 모델 가중치를 반환한다."""
    state = _load_state()
    return state.get("regime_weights", {})


# ============================================================
# CLI
# ============================================================

def _print_report(result: dict):
    """분석 결과를 사람이 읽을 수 있는 형식으로 출력."""
    cal = result.get("confidence_calibration", {})
    print("\n=== Feedback Hub 분석 리포트 ===\n")

    print("📊 Confidence 보정:")
    print(f"  보정값: {cal.get('confidence_bias', 0):+.4f}")
    print(f"  보정 오차: {cal.get('calibration_error', 0):.4f}")
    print(f"  샘플 수: {cal.get('samples', 0)}")
    for bk, data in cal.get("buckets", {}).items():
        actual = data.get("actual", "N/A")
        print(f"  [{bk}] 예측={data['predicted']:.1f}, 실제={actual}, n={data['total']}")

    print("\n🤖 RL 모델 정확도:")
    for name, score in result.get("rl_model_scores", {}).items():
        status = "❌ 비활성" if score.get("should_disable") else "✅ 활성"
        print(f"  {name}: {score['accuracy']:.1%} ({score['samples']}건) {status}")

    disabled = result.get("disabled_rl_models", [])
    if disabled:
        print(f"  ⚠️ 비활성화 대상: {', '.join(disabled)}")

    rag = result.get("rag_quality", {})
    print("\n🔍 RAG 품질:")
    print(f"  RAG 사용: {rag.get('rag_accuracy', 0):.1%} ({rag.get('rag_samples', 0)}건)")
    print(f"  RAG 미사용: {rag.get('no_rag_accuracy', 0):.1%} ({rag.get('no_rag_samples', 0)}건)")
    print(f"  RAG 기여도: {rag.get('rag_benefit', 0):+.1%}")


if __name__ == "__main__":
    # Windows cp949 방지
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    cmd = sys.argv[1] if len(sys.argv) > 1 else "full"

    if cmd == "report":
        result = run_full_analysis()
        _print_report(result)
    elif cmd == "calibrate":
        cal = calibrate_confidence(14)
        print(json.dumps(cal, ensure_ascii=False, indent=2))
    else:
        result = run_full_analysis()
        _print_report(result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
