#!/usr/bin/env python3
"""
RL 모델 자동 재훈련 큐 관리자

feedback_hub에서 비활성화된 RL 모델을 감지하고, 재훈련 큐에 등록하여
자동으로 재학습을 실행한다.

기능:
  1. disabled_rl_models 감지 + 재훈련 적격성 검사
  2. data/model_retrain_queue.json 큐 관리
  3. SB3 모델 직접 재훈련 (primary 머신) / DB 큐 등록 (그 외)
  4. 재훈련 후 정확도 비교 → 복원 또는 유지

사용법:
  python scripts/model_retrainer.py            # 전체 사이클 (check + process)
  python scripts/model_retrainer.py --status    # 큐 상태 조회

파이프라인 통합:
  run_agents.py Phase 11에서 자동 호출
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

KST = timezone(timedelta(hours=9))
STATE_FILE = PROJECT_DIR / "data" / "feedback_hub_state.json"
QUEUE_FILE = PROJECT_DIR / "data" / "model_retrain_queue.json"

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# 재훈련 파라미터
MIN_DISABLED_HOURS = 24       # 비활성화 후 최소 대기 시간
MIN_NEW_SAMPLES = 50          # 최소 새 데이터 수
MIN_RETRAIN_INTERVAL_HOURS = 48  # 재시도 최소 간격
ACCURACY_IMPROVEMENT_THRESHOLD = 0.05  # 복원 기준: 이전 대비 +5%

# GPU 필요 모델 (큐잉만 하고 직접 실행하지 않음)
DEFERRED_MODELS = {"dt", "multi_agent", "offline"}


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _now_kst() -> str:
    return datetime.now(KST).isoformat()


# ============================================================
# 큐 파일 I/O
# ============================================================

def _load_queue() -> dict:
    """model_retrain_queue.json 로드"""
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"queue": [], "history": [], "last_checked": None}


def _save_queue(data: dict):
    """model_retrain_queue.json 저장"""
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_feedback_state() -> dict:
    """feedback_hub_state.json 로드"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "disabled_rl_models": [],
        "rl_model_scores": {},
        "last_updated": None,
    }


def _save_feedback_state(state: dict):
    """feedback_hub_state.json 저장"""
    state["last_updated"] = _now_kst()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ============================================================
# Supabase 헬퍼
# ============================================================

def _get_decisions_count_since(since_iso: str) -> int:
    """지정 시각 이후 decisions 건수 조회"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return 0
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/decisions",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "count=exact",
            },
            params={
                "select": "id",
                "created_at": f"gte.{since_iso}",
                "limit": "0",
            },
            timeout=10,
        )
        # count=exact 헤더로 Content-Range에서 총 개수 파싱
        content_range = r.headers.get("Content-Range", "")
        if "/" in content_range:
            total = content_range.split("/")[-1]
            if total != "*":
                return int(total)
        # fallback
        return len(r.json()) if r.status_code == 200 else 0
    except Exception:
        return 0


def _log_training_queue_to_db(model_name: str, reason: str, previous_accuracy: float):
    """rl_training_cycles 테이블에 queued 상태로 기록"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from utils.machine import get_machine_name
        machine = get_machine_name()
    except Exception:
        machine = "unknown"

    import uuid
    cycle_id = str(uuid.uuid4())

    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/rl_training_cycles",
            headers=_headers(),
            json={
                "id": cycle_id,
                "algorithm": model_name,
                "status": "queued",
                "machine_name": machine,
                "module": "model_retrainer",
                "cycle_type": "auto_retrain",
                "training_meta": json.dumps({
                    "reason": "auto_retrain",
                    "previous_accuracy": previous_accuracy,
                    "trigger": "feedback_hub_disabled",
                }, ensure_ascii=False),
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
            timeout=15,
        )
        if r.status_code in (200, 201):
            return cycle_id
        else:
            print(f"[model_retrainer] DB queued 기록 실패: {r.status_code}", file=sys.stderr)
            return cycle_id
    except Exception as e:
        print(f"[model_retrainer] DB queued 예외: {e}", file=sys.stderr)
        return cycle_id


def _update_training_status_db(cycle_id: str, status: str, error_message: str = None,
                                elapsed_seconds: float = None):
    """rl_training_cycles 상태 업데이트"""
    if not SUPABASE_URL or not SUPABASE_KEY or not cycle_id:
        return
    data = {"status": status}
    if error_message:
        data["error_message"] = error_message
    if elapsed_seconds is not None:
        data["elapsed_seconds"] = elapsed_seconds
    if status in ("completed", "failed"):
        data["completed_at"] = datetime.now(timezone.utc).isoformat()

    try:
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/rl_training_cycles",
            headers=_headers(),
            json=data,
            params={"id": f"eq.{cycle_id}"},
            timeout=10,
        )
    except Exception:
        pass


# ============================================================
# 1. check_and_queue — 비활성 모델 감지 + 큐 등록
# ============================================================

def check_and_queue() -> dict:
    """disabled_rl_models를 확인하고, 적격한 모델을 재훈련 큐에 등록한다.

    Returns:
        {"queued": int, "skipped": int, "details": [...]}
    """
    fb_state = _load_feedback_state()
    disabled_models = fb_state.get("disabled_rl_models", [])
    rl_scores = fb_state.get("rl_model_scores", {})
    last_updated = fb_state.get("last_updated")

    queue_data = _load_queue()
    queue_data["last_checked"] = _now_kst()

    queued = 0
    skipped = 0
    details = []

    if not disabled_models:
        _save_queue(queue_data)
        return {"queued": 0, "skipped": 0, "details": ["비활성 모델 없음"]}

    # 현재 큐에 있는 모델 (pending/training)
    active_queue_models = {
        item["model_name"]
        for item in queue_data["queue"]
        if item.get("status") in ("pending", "training")
    }

    for model_name in disabled_models:
        skip_reason = None

        # 1) 이미 큐에 있는지
        if model_name in active_queue_models:
            skip_reason = "이미 큐에 존재"

        # 2) 비활성화 경과 시간 확인 (last_updated 기준)
        if not skip_reason and last_updated:
            try:
                updated_dt = datetime.fromisoformat(last_updated)
                hours_since = (datetime.now(KST) - updated_dt).total_seconds() / 3600
                if hours_since < MIN_DISABLED_HOURS:
                    skip_reason = f"비활성화 {hours_since:.1f}h 경과 (최소 {MIN_DISABLED_HOURS}h)"
            except (ValueError, TypeError):
                pass

        # 3) 마지막 재훈련 시도 간격
        if not skip_reason:
            for hist in reversed(queue_data.get("history", [])):
                if hist.get("model_name") == model_name:
                    try:
                        last_attempt = datetime.fromisoformat(hist["queued_at"])
                        hours_ago = (datetime.now(KST) - last_attempt).total_seconds() / 3600
                        if hours_ago < MIN_RETRAIN_INTERVAL_HOURS:
                            skip_reason = f"마지막 시도 {hours_ago:.1f}h 전 (최소 {MIN_RETRAIN_INTERVAL_HOURS}h)"
                    except (ValueError, TypeError, KeyError):
                        pass
                    break

        # 4) 새 데이터 수 확인
        if not skip_reason:
            # 최근 7일 데이터
            cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            new_count = _get_decisions_count_since(cutoff)
            if new_count < MIN_NEW_SAMPLES:
                skip_reason = f"새 데이터 {new_count}건 (최소 {MIN_NEW_SAMPLES}건)"

        if skip_reason:
            skipped += 1
            details.append(f"{model_name}: 스킵 - {skip_reason}")
            continue

        # 적격 → 큐에 추가
        score_info = rl_scores.get(model_name, {})
        prev_accuracy = score_info.get("accuracy", 0.0)
        reason = f"정확도 {prev_accuracy:.0%} (임계 35% 미만)"

        entry = {
            "model_name": model_name,
            "reason": reason,
            "queued_at": _now_kst(),
            "status": "pending",
            "previous_accuracy": prev_accuracy,
            "retrain_started": None,
            "retrain_completed": None,
            "new_accuracy": None,
            "db_cycle_id": None,
        }

        # DB에 queued 기록
        cycle_id = _log_training_queue_to_db(model_name, reason, prev_accuracy)
        entry["db_cycle_id"] = cycle_id

        queue_data["queue"].append(entry)
        queued += 1
        details.append(f"{model_name}: 큐 등록 (정확도 {prev_accuracy:.0%})")

    _save_queue(queue_data)
    return {"queued": queued, "skipped": skipped, "details": details}


# ============================================================
# 2. process_queue — 대기 중인 재훈련 처리
# ============================================================

def process_queue() -> dict:
    """pending 상태의 재훈련 작업을 처리한다.

    - SB3: primary 머신에서 ContinuousLearner.force_retrain()
    - historical: train_historical.py 호출
    - dt/multi_agent/offline: deferred로 마킹

    Returns:
        {"processed": int, "failed": int, "deferred": int, "details": [...]}
    """
    queue_data = _load_queue()
    processed = 0
    failed = 0
    deferred = 0
    details = []

    try:
        from utils.machine import is_primary
        on_primary = is_primary()
    except Exception:
        on_primary = False

    for entry in queue_data["queue"]:
        if entry.get("status") != "pending":
            continue

        model_name = entry["model_name"]
        cycle_id = entry.get("db_cycle_id")

        # GPU 필요 모델 → deferred
        if model_name in DEFERRED_MODELS:
            entry["status"] = "deferred"
            entry["retrain_completed"] = _now_kst()
            _update_training_status_db(cycle_id, "deferred",
                                       error_message=f"{model_name}: GPU 필요, 수동 훈련 대기")
            deferred += 1
            details.append(f"{model_name}: deferred (GPU 필요)")
            continue

        # SB3 모델 재훈련
        if model_name in ("sb3", "ensemble"):
            if not on_primary:
                entry["status"] = "deferred"
                entry["retrain_completed"] = _now_kst()
                _update_training_status_db(cycle_id, "deferred",
                                           error_message="primary 머신이 아님")
                deferred += 1
                details.append(f"{model_name}: deferred (non-primary)")
                continue

            entry["status"] = "training"
            entry["retrain_started"] = _now_kst()
            _update_training_status_db(cycle_id, "running")

            start_time = time.time()
            try:
                from rl_hybrid.rl.continuous_learner import ContinuousLearner
                learner = ContinuousLearner(
                    incremental_steps=50_000,
                    min_new_decisions=2,
                )
                learner.force_retrain()
                elapsed = time.time() - start_time

                # 재훈련 후 정확도 평가
                new_accuracy = _evaluate_model_accuracy(model_name)
                entry["new_accuracy"] = new_accuracy
                entry["retrain_completed"] = _now_kst()

                prev_acc = entry.get("previous_accuracy", 0)
                if new_accuracy is not None and new_accuracy > prev_acc + ACCURACY_IMPROVEMENT_THRESHOLD:
                    entry["status"] = "completed"
                    _update_training_status_db(cycle_id, "completed", elapsed_seconds=elapsed)
                    _restore_model(model_name)
                    details.append(
                        f"{model_name}: 성공 ({prev_acc:.0%} -> {new_accuracy:.0%}), 복원됨"
                    )
                else:
                    entry["status"] = "failed"
                    reason = f"개선 부족 ({prev_acc:.0%} -> {new_accuracy:.0%})" if new_accuracy is not None else "정확도 평가 불가"
                    _update_training_status_db(cycle_id, "failed",
                                               error_message=reason, elapsed_seconds=elapsed)
                    details.append(f"{model_name}: 실패 - {reason}")
                    failed += 1
                    continue

                processed += 1

            except Exception as e:
                elapsed = time.time() - start_time
                entry["status"] = "failed"
                entry["retrain_completed"] = _now_kst()
                error_msg = str(e)[:200]
                _update_training_status_db(cycle_id, "failed",
                                           error_message=error_msg, elapsed_seconds=elapsed)
                failed += 1
                details.append(f"{model_name}: 예외 - {error_msg}")
                continue

        # historical 모델
        elif model_name == "historical":
            if not on_primary:
                entry["status"] = "deferred"
                entry["retrain_completed"] = _now_kst()
                deferred += 1
                details.append(f"{model_name}: deferred (non-primary)")
                continue

            entry["status"] = "training"
            entry["retrain_started"] = _now_kst()
            _update_training_status_db(cycle_id, "running")

            start_time = time.time()
            try:
                import subprocess
                result = subprocess.run(
                    [
                        sys.executable,
                        str(PROJECT_DIR / "scripts" / "train_historical.py"),
                        "--mode", "regime",
                        "--steps", "100000",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=1800,  # 30분 타임아웃
                    cwd=str(PROJECT_DIR),
                )
                elapsed = time.time() - start_time

                if result.returncode == 0:
                    new_accuracy = _evaluate_model_accuracy(model_name)
                    entry["new_accuracy"] = new_accuracy
                    entry["retrain_completed"] = _now_kst()

                    prev_acc = entry.get("previous_accuracy", 0)
                    if new_accuracy is not None and new_accuracy > prev_acc + ACCURACY_IMPROVEMENT_THRESHOLD:
                        entry["status"] = "completed"
                        _update_training_status_db(cycle_id, "completed", elapsed_seconds=elapsed)
                        _restore_model(model_name)
                        processed += 1
                        details.append(f"{model_name}: 성공 ({prev_acc:.0%} -> {new_accuracy:.0%})")
                    else:
                        entry["status"] = "failed"
                        _update_training_status_db(cycle_id, "failed",
                                                   error_message="개선 부족", elapsed_seconds=elapsed)
                        failed += 1
                        details.append(f"{model_name}: 개선 부족")
                else:
                    entry["status"] = "failed"
                    entry["retrain_completed"] = _now_kst()
                    err = result.stderr[:200] if result.stderr else "exit code non-zero"
                    _update_training_status_db(cycle_id, "failed",
                                               error_message=err, elapsed_seconds=elapsed)
                    failed += 1
                    details.append(f"{model_name}: 실패 - {err}")

            except Exception as e:
                elapsed = time.time() - start_time
                entry["status"] = "failed"
                entry["retrain_completed"] = _now_kst()
                _update_training_status_db(cycle_id, "failed",
                                           error_message=str(e)[:200], elapsed_seconds=elapsed)
                failed += 1
                details.append(f"{model_name}: 예외 - {e}")

        else:
            # 알 수 없는 모델 → deferred
            entry["status"] = "deferred"
            entry["retrain_completed"] = _now_kst()
            deferred += 1
            details.append(f"{model_name}: deferred (미지원 모델)")

    # 완료/실패 항목을 history로 이동
    still_active = []
    for entry in queue_data["queue"]:
        if entry["status"] in ("completed", "failed", "deferred"):
            queue_data["history"].append(entry)
        else:
            still_active.append(entry)
    queue_data["queue"] = still_active

    # history는 최근 20건만 유지
    queue_data["history"] = queue_data["history"][-20:]

    _save_queue(queue_data)
    return {"processed": processed, "failed": failed, "deferred": deferred, "details": details}


# ============================================================
# 헬퍼: 정확도 평가 + 모델 복원
# ============================================================

def _evaluate_model_accuracy(model_name: str) -> float | None:
    """재훈련 후 모델의 최근 예측 정확도를 평가한다.

    rl_model_predictions에서 최근 데이터를 조회하여 계산.
    재훈련 직후이므로 과거 데이터 기반으로 추정한다.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    action_key_map = {
        "sb3": "sb3_action",
        "dt": "dt_action",
        "multi_agent": "multi_agent_action",
        "offline": "offline_action",
        "ensemble": "ensemble_direction",
        "historical": "sb3_action",  # historical은 sb3 기반
    }

    action_key = action_key_map.get(model_name)
    if not action_key:
        return None

    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/rl_model_predictions",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
            },
            params={
                "select": f"{action_key},ensemble_direction,return_after_4h",
                "created_at": f"gte.{cutoff}",
                "return_after_4h": "not.is.null",
                "limit": "100",
            },
            timeout=10,
        )
        if r.status_code != 200:
            return None

        rows = r.json()
        if not rows or len(rows) < 3:
            return None

        correct = 0
        total = 0
        for row in rows:
            actual_return = row.get("return_after_4h", 0)
            actual_dir = "buy" if actual_return > 0.5 else ("sell" if actual_return < -0.5 else "hold")

            if model_name == "ensemble":
                pred_dir = row.get("ensemble_direction")
                if not pred_dir:
                    continue
            else:
                action = row.get(action_key)
                if action is None:
                    continue
                pred_dir = "buy" if action > 0.3 else ("sell" if action < -0.3 else "hold")

            total += 1
            if pred_dir == actual_dir or (pred_dir == "hold" and abs(actual_return) < 0.5):
                correct += 1

        return round(correct / total, 4) if total > 0 else None

    except Exception:
        return None


def _restore_model(model_name: str):
    """재훈련 성공 시 disabled_rl_models에서 모델을 제거한다."""
    fb_state = _load_feedback_state()
    disabled = fb_state.get("disabled_rl_models", [])
    if model_name in disabled:
        disabled.remove(model_name)
        fb_state["disabled_rl_models"] = disabled

        # rl_model_scores에서 should_disable도 해제
        scores = fb_state.get("rl_model_scores", {})
        if model_name in scores:
            scores[model_name]["should_disable"] = False
        fb_state["rl_model_scores"] = scores

        _save_feedback_state(fb_state)
        print(f"[model_retrainer] {model_name} 복원: disabled 목록에서 제거")


# ============================================================
# 3. get_queue_status — 큐 상태 조회
# ============================================================

def get_queue_status() -> dict:
    """현재 재훈련 큐 상태를 반환한다."""
    queue_data = _load_queue()
    fb_state = _load_feedback_state()

    active = [e for e in queue_data["queue"] if e["status"] in ("pending", "training")]
    recent_history = queue_data.get("history", [])[-5:]

    return {
        "disabled_models": fb_state.get("disabled_rl_models", []),
        "active_queue": active,
        "recent_history": recent_history,
        "last_checked": queue_data.get("last_checked"),
        "total_history": len(queue_data.get("history", [])),
    }


# ============================================================
# CLI
# ============================================================

def _print_status(status: dict):
    """큐 상태를 사람이 읽을 수 있는 형식으로 출력."""
    print("\n=== RL 모델 재훈련 큐 ===\n")

    disabled = status.get("disabled_models", [])
    print(f"비활성 모델: {', '.join(disabled) if disabled else '없음'}")
    print(f"마지막 점검: {status.get('last_checked', 'N/A')}")

    active = status.get("active_queue", [])
    if active:
        print(f"\n대기 중 ({len(active)}건):")
        for e in active:
            print(f"  - {e['model_name']}: {e['status']} (정확도 {e.get('previous_accuracy', 0):.0%})")
            print(f"    사유: {e.get('reason', 'N/A')}")
    else:
        print("\n대기 중: 없음")

    history = status.get("recent_history", [])
    if history:
        print(f"\n최근 이력 ({len(history)}건):")
        for e in history:
            new_acc = e.get("new_accuracy")
            acc_str = f" -> {new_acc:.0%}" if new_acc is not None else ""
            print(f"  - {e['model_name']}: {e['status']} ({e.get('previous_accuracy', 0):.0%}{acc_str})")


if __name__ == "__main__":
    # Windows cp949 방지
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    import argparse
    parser = argparse.ArgumentParser(description="RL 모델 자동 재훈련 큐 관리자")
    parser.add_argument("--status", action="store_true", help="큐 상태 조회")
    args = parser.parse_args()

    if args.status:
        status = get_queue_status()
        _print_status(status)
    else:
        print("[model_retrainer] 비활성 모델 점검...")
        q_result = check_and_queue()
        print(f"  큐 등록: {q_result['queued']}건, 스킵: {q_result['skipped']}건")
        for d in q_result.get("details", []):
            print(f"  - {d}")

        if q_result["queued"] > 0:
            print("\n[model_retrainer] 재훈련 처리...")
            p_result = process_queue()
            print(f"  처리: {p_result['processed']}건, 실패: {p_result['failed']}건, 보류: {p_result['deferred']}건")
            for d in p_result.get("details", []):
                print(f"  - {d}")
        else:
            print("  재훈련 대상 없음")

        print("\n[model_retrainer] 완료")
