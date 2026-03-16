#!/usr/bin/env python3
"""
레짐별 RL 모델 가중치 학습기 — 과거 매매 정확도 기반 최적화

기능:
  1. Supabase decisions 테이블에서 레짐별 매매 결과를 수집 (최근 30일)
  2. 레짐별 모델 정확도를 계산하고 inverse-error 가중치를 산출
  3. 기본 가중치와 블렌딩 (70% 학습 + 30% 기본)하여 안정성 확보
  4. data/regime_weights_learned.json에 저장

사용법:
  python scripts/regime_learner.py              # 학습 실행 + 결과 출력

파이프라인 통합:
  run_agents.py Phase 12에서 자동 호출
  regime_detector.py에서 get_learned_weights()로 조회
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
import requests

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PROJECT_DIR = Path(__file__).resolve().parent.parent
WEIGHTS_FILE = PROJECT_DIR / "data" / "regime_weights_learned.json"
KST = timezone(timedelta(hours=9))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

MODELS = ["sb3", "dt", "multi_agent", "offline", "historical"]

REGIMES = ["bull_strong", "bull_weak", "sideways", "bear_weak", "bear_strong", "volatile"]

MIN_SAMPLES = 5  # 레짐당 최소 데이터 수

# 기본 가중치 (regime_detector.py와 동일)
DEFAULT_REGIME_WEIGHTS = {
    "bull_strong": {"sb3": 0.15, "dt": 0.25, "multi_agent": 0.20, "offline": 0.10, "historical": 0.30},
    "bull_weak":   {"sb3": 0.20, "dt": 0.25, "multi_agent": 0.20, "offline": 0.15, "historical": 0.20},
    "sideways":    {"sb3": 0.20, "dt": 0.20, "multi_agent": 0.15, "offline": 0.15, "historical": 0.30},
    "bear_weak":   {"sb3": 0.20, "dt": 0.15, "multi_agent": 0.20, "offline": 0.20, "historical": 0.25},
    "bear_strong": {"sb3": 0.15, "dt": 0.10, "multi_agent": 0.20, "offline": 0.25, "historical": 0.30},
    "volatile":    {"sb3": 0.25, "dt": 0.15, "multi_agent": 0.25, "offline": 0.15, "historical": 0.20},
}


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _fetch_decisions(days: int = 30) -> list[dict]:
    """Supabase에서 레짐 정보가 포함된 최근 결정들을 가져온다."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/decisions",
            headers=_headers(),
            params={
                "select": "market_data_snapshot,was_correct_4h,outcome_4h_pct,confidence,created_at",
                "created_at": f"gte.{cutoff}",
                "was_correct_4h": "not.is.null",
                "limit": "500",
            },
            timeout=15,
        )
        if r.status_code != 200:
            print(f"[regime_learner] Supabase 조회 실패: {r.status_code}", file=sys.stderr)
            return []
        return r.json() or []
    except Exception as e:
        print(f"[regime_learner] Supabase 조회 예외: {e}", file=sys.stderr)
        return []


def _extract_regime(snapshot) -> str | None:
    """market_data_snapshot에서 regime 키를 추출한다."""
    if not snapshot:
        return None
    if isinstance(snapshot, str):
        try:
            snapshot = json.loads(snapshot)
        except (json.JSONDecodeError, TypeError):
            return None
    if isinstance(snapshot, dict):
        return snapshot.get("regime")
    return None


def _extract_model_predictions(snapshot) -> dict[str, float] | None:
    """market_data_snapshot에서 모델별 예측 정보를 추출한다.

    Returns:
        {model_name: accuracy_proxy} 또는 None
    """
    if not snapshot:
        return None
    if isinstance(snapshot, str):
        try:
            snapshot = json.loads(snapshot)
        except (json.JSONDecodeError, TypeError):
            return None
    if not isinstance(snapshot, dict):
        return None

    # rl_advisory 안에 모델별 action이 있을 수 있음
    rl = snapshot.get("rl_advisory", {})
    if not rl or not isinstance(rl, dict):
        return None

    predictions = {}
    for model in MODELS:
        action_key = f"{model}_action"
        if action_key in rl:
            predictions[model] = rl[action_key]

    return predictions if predictions else None


def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """가중치의 합이 1.0이 되도록 정규화한다."""
    total = sum(weights.values())
    if total <= 0:
        # 균등 분배
        n = len(weights)
        if n == 0:
            return {}
        return {k: round(1.0 / n, 4) for k in weights}
    return {k: round(v / total, 4) for k, v in weights.items()}


def learn_weights(days: int = 30, cached_decisions: list[dict] | None = None) -> dict | None:
    """과거 매매 결과를 분석하여 레짐별 최적 모델 가중치를 학습한다.

    Args:
        days: 분석 기간 (일)
        cached_decisions: phase_cache에서 전달받은 캐시 데이터 (None이면 직접 조회)

    Returns:
        저장된 전체 상태 dict 또는 실패 시 None
    """
    if cached_decisions is not None:
        # 캐시에서 was_correct_4h not null 필터 (regime_learner 조건과 동일)
        rows = [d for d in cached_decisions if d.get("was_correct_4h") is not None]
    else:
        rows = _fetch_decisions(days)
    if not rows:
        print("[regime_learner] 데이터 없음 — 학습 스킵", file=sys.stderr)
        return None

    # 레짐별 그룹핑
    regime_decisions: dict[str, list[dict]] = {r: [] for r in REGIMES}

    for row in rows:
        snapshot_raw = row.get("market_data_snapshot")
        regime = _extract_regime(snapshot_raw)
        if regime and regime in regime_decisions:
            regime_decisions[regime].append({
                "was_correct": row.get("was_correct_4h", False),
                "outcome_pct": row.get("outcome_4h_pct", 0),
                "confidence": row.get("confidence", 0.5),
                "snapshot": snapshot_raw,
            })

    # 레짐별 모델 정확도 계산 + 가중치 학습
    learned_weights = {}
    sample_counts = {}
    regime_accuracy = {}

    for regime in REGIMES:
        decisions = regime_decisions[regime]
        sample_counts[regime] = len(decisions)

        if len(decisions) < MIN_SAMPLES:
            # 데이터 부족 — 기본 가중치 사용
            learned_weights[regime] = DEFAULT_REGIME_WEIGHTS.get(
                regime, DEFAULT_REGIME_WEIGHTS["sideways"]
            )
            regime_accuracy[regime] = None
            continue

        # 전체 레짐 정확도
        correct_count = sum(1 for d in decisions if d["was_correct"])
        total_count = len(decisions)
        overall_accuracy = correct_count / total_count
        regime_accuracy[regime] = round(overall_accuracy, 4)

        # 모델별 정확도 계산
        model_accuracy = {}
        for model in MODELS:
            model_correct = 0
            model_total = 0

            for d in decisions:
                snapshot = d["snapshot"]
                predictions = _extract_model_predictions(snapshot)

                if predictions and model in predictions:
                    action = predictions[model]
                    # action > 0.3 = buy 예측, < -0.3 = sell 예측
                    predicted_buy = action > 0.3
                    predicted_sell = action < -0.3
                    outcome = d.get("outcome_pct", 0) or 0

                    # 정확도: buy 예측 + 양수 결과, sell 예측 + 음수 결과, hold 예측 + 작은 변동
                    was_right = False
                    if predicted_buy and outcome > 0:
                        was_right = True
                    elif predicted_sell and outcome < 0:
                        was_right = True
                    elif not predicted_buy and not predicted_sell and abs(outcome) < 1:
                        was_right = True

                    model_total += 1
                    if was_right:
                        model_correct += 1

            if model_total >= 3:
                model_accuracy[model] = model_correct / model_total
            else:
                # 모델 예측 데이터 부족 — 전체 정확도를 proxy로 사용
                model_accuracy[model] = overall_accuracy

        # Inverse-error 가중치 계산
        raw_weights = {}
        for model in MODELS:
            acc = model_accuracy.get(model, overall_accuracy)
            # 정확도를 최소 0.1로 클램프 (0 division 방지)
            acc = max(0.1, acc)
            raw_weights[model] = acc  # weight = accuracy (= 1 - error 에서 error = 1 - acc)

        # 정규화
        total_w = sum(raw_weights.values())
        if total_w > 0:
            learned_only = {m: raw_weights[m] / total_w for m in MODELS}
        else:
            learned_only = {m: 1.0 / len(MODELS) for m in MODELS}

        # 기본 가중치와 블렌딩 (70% 학습 + 30% 기본)
        defaults = DEFAULT_REGIME_WEIGHTS.get(regime, DEFAULT_REGIME_WEIGHTS["sideways"])
        blended = {}
        for model in MODELS:
            blended[model] = 0.7 * learned_only.get(model, 0.2) + 0.3 * defaults.get(model, 0.2)

        # 최종 정규화
        learned_weights[regime] = _normalize_weights(blended)

    # 결과 저장
    result = {
        "weights": learned_weights,
        "sample_counts": sample_counts,
        "regime_accuracy": regime_accuracy,
        "last_updated": datetime.now(KST).isoformat(),
    }

    try:
        from scripts.atomic_write import atomic_json_save
        atomic_json_save(WEIGHTS_FILE, result)
    except ImportError:
        WEIGHTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        WEIGHTS_FILE.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"[regime_learner] 저장 실패: {e}", file=sys.stderr)

    return result


def get_learned_weights(regime: str) -> dict | None:
    """특정 레짐의 학습된 가중치를 반환한다.

    Args:
        regime: 레짐 이름 (예: "bull_strong", "sideways")

    Returns:
        {model: weight} dict 또는 데이터 부족/파일 없음 시 None
    """
    if not WEIGHTS_FILE.exists():
        return None

    try:
        data = json.loads(WEIGHTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    weights = data.get("weights", {})
    sample_counts = data.get("sample_counts", {})

    # 해당 레짐의 샘플 수가 MIN_SAMPLES 미만이면 None (기본값 사용)
    if sample_counts.get(regime, 0) < MIN_SAMPLES:
        return None

    regime_weights = weights.get(regime)
    if not regime_weights:
        return None

    return regime_weights


def get_learning_summary() -> dict | None:
    """저장된 학습 상태 전체를 반환한다.

    Returns:
        전체 저장 상태 dict 또는 파일 없음 시 None
    """
    if not WEIGHTS_FILE.exists():
        return None

    try:
        return json.loads(WEIGHTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


# ── CLI ──────────────────────────────────────────────────

if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("=== 레짐별 RL 모델 가중치 학습 ===\n")

    result = learn_weights()

    if not result:
        print("학습 데이터 없음 — 기본 가중치를 사용합니다.")
        sys.exit(0)

    print(f"분석 완료: {datetime.now(KST).strftime('%Y-%m-%d %H:%M')}\n")

    for regime in REGIMES:
        count = result["sample_counts"].get(regime, 0)
        acc = result["regime_accuracy"].get(regime)
        weights = result["weights"].get(regime, {})

        status = f"({count}건)" if count >= MIN_SAMPLES else f"({count}건 - 기본값 사용)"
        acc_str = f"{acc:.1%}" if acc is not None else "N/A"

        print(f"  {regime:15s}  정확도={acc_str:>6s}  샘플={status}")
        if count >= MIN_SAMPLES:
            w_str = ", ".join(f"{m}={w:.2f}" for m, w in weights.items())
            print(f"    가중치: {w_str}")

    updated = sum(1 for v in result["sample_counts"].values() if v >= MIN_SAMPLES)
    total = len(REGIMES)
    print(f"\n학습 완료: {updated}/{total} 레짐 가중치 업데이트")
    print(f"저장: {WEIGHTS_FILE}")
