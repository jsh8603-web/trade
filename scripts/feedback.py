#!/usr/bin/env python3
"""
사용자 피드백 시스템 — 자율 매매 시스템에 구체적 피드백 전달

피드백 유형:
  1. 성향 조절:  python scripts/feedback.py bias -0.5       (보수적↔공격적)
  2. 구체적 지시: python scripts/feedback.py say "관망 좀 더 해"
  3. 파라미터:   python scripts/feedback.py param MIN_TRADE_INTERVAL_HOURS 6
  4. 현재 상태:  python scripts/feedback.py status
  5. 이력 조회:  python scripts/feedback.py history

피드백은 두 곳에 저장된다:
  - data/orchestrator_state.json → 다음 매매 사이클에서 즉시 반영
  - Supabase feedback 테이블 → 장기 학습 데이터로 활용
"""

from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Windows cp949 인코딩 문제 방지
if sys.stdout and sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr and sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")

STATE_FILE = PROJECT_DIR / "data" / "orchestrator_state.json"
KST = timezone(timedelta(hours=9))


# ── 피드백 유형별 자동 태그 ──────────────────────────────

FEEDBACK_TAGS = {
    "거래 많": {"type": "behavior_change", "action": "reduce_trade_frequency",
                "param": "MIN_TRADE_INTERVAL_HOURS", "direction": "increase"},
    "트레이딩 많": {"type": "behavior_change", "action": "reduce_trade_frequency",
                    "param": "MIN_TRADE_INTERVAL_HOURS", "direction": "increase"},
    "수익 없": {"type": "behavior_change", "action": "improve_profitability",
                "param": "confidence_threshold", "direction": "increase"},
    "얻는게 없": {"type": "behavior_change", "action": "improve_profitability",
                  "param": "confidence_threshold", "direction": "increase"},
    "학습 부진": {"type": "behavior_change", "action": "force_retrain",
                  "param": "training_urgency", "direction": "increase"},
    "기록 안": {"type": "behavior_change", "action": "improve_db_logging",
                "param": "db_logging_level", "direction": "increase"},
    "개선 안": {"type": "behavior_change", "action": "force_strategy_review",
                "param": "strategy_review", "direction": "force"},
    "보수적": {"type": "parameter_change", "action": "go_conservative",
               "param": "feedback_bias", "direction": "decrease"},
    "공격적": {"type": "parameter_change", "action": "go_aggressive",
               "param": "feedback_bias", "direction": "increase"},
    "관망": {"type": "one_time", "action": "force_hold",
             "param": "force_hold_cycles", "direction": "increase"},
    "매수": {"type": "one_time", "action": "bias_buy",
             "param": "feedback_bias", "direction": "increase"},
    "매도": {"type": "one_time", "action": "bias_sell",
             "param": "feedback_bias", "direction": "decrease"},
}


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = STATE_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    temp_file.replace(STATE_FILE)


def _save_to_db(fb_type: str, content: str, action: str = None) -> bool:
    """Supabase feedback 테이블에 저장한다."""
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not supabase_url or not supabase_key:
        return False

    import requests
    try:
        row = {
            "type": fb_type,
            "content": content,
            "applied": False,
        }
        resp = requests.post(
            f"{supabase_url}/rest/v1/feedback",
            json=row,
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            timeout=10,
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


# ── 명령어 구현 ──────────────────────────────────────────


def cmd_bias(score_str: str):
    """성향 바이어스 조절 (-1.0 ~ 1.0)"""
    try:
        score = float(score_str)
    except ValueError:
        print("점수는 숫자여야 합니다. (예: 0.5, -0.2)")
        sys.exit(1)

    if not (-1.0 <= score <= 1.0):
        print("점수는 -1.0과 1.0 사이여야 합니다.")
        sys.exit(1)

    state = _load_state()
    old_bias = state.get("feedback_bias", 0.0)
    # 숫자형 bias가 아닌 경우(레거시 문자열) 리셋
    if not isinstance(old_bias, (int, float)):
        old_bias = 0.0
    new_bias = max(-1.0, min(1.0, old_bias + score))

    state["feedback_bias"] = new_bias
    state["feedback_bias_set_at"] = datetime.now(KST).isoformat()
    state["last_feedback_time"] = datetime.now(KST).isoformat()
    state["last_feedback_score"] = score
    _save_state(state)

    direction = "공격적" if score > 0 else "보수적"
    _save_to_db("parameter_change", f"성향 조절: {old_bias:.2f} → {new_bias:.2f} ({direction})")

    print(f"  성향 바이어스: {old_bias:.2f} → {new_bias:.2f}")
    print(f"  방향: {'공격적' if new_bias > 0 else '보수적' if new_bias < 0 else '중립'}")
    print(f"  7일 후 자동 감쇠됩니다.")


def cmd_say(message: str):
    """구체적 피드백을 자연어로 전달"""
    state = _load_state()
    now = datetime.now(KST).isoformat()

    # 자동 태그 매칭
    matched_tags = []
    actions = []
    for keyword, tag_info in FEEDBACK_TAGS.items():
        if keyword in message:
            matched_tags.append(keyword)
            actions.append(tag_info)

    # 피드백 큐에 추가
    fb_queue = state.get("feedback_queue", [])
    fb_entry = {
        "message": message,
        "tags": matched_tags,
        "actions": [a["action"] for a in actions],
        "created_at": now,
        "applied": False,
    }
    fb_queue.append(fb_entry)

    # 최근 20개만 유지
    if len(fb_queue) > 20:
        fb_queue = fb_queue[-20:]
    state["feedback_queue"] = fb_queue
    state["last_feedback_time"] = now

    # 즉시 반영 가능한 액션 처리
    for action_info in actions:
        action = action_info["action"]
        if action == "reduce_trade_frequency":
            current = state.get("min_trade_interval_override", None)
            state["min_trade_interval_override"] = (current or 4) + 2
            print(f"  → 매매 간격 확대: {current or 4}h → {state['min_trade_interval_override']}h")
        elif action == "improve_profitability":
            state["confidence_threshold_override"] = 0.65
            print(f"  → confidence 임계값 상향: 0.5 → 0.65 (확신 높은 거래만)")
        elif action == "force_retrain":
            state["force_retrain_next_cycle"] = True
            print(f"  → 다음 사이클에 강제 재학습 트리거")
        elif action == "improve_db_logging":
            state["db_logging_verbose"] = True
            print(f"  → DB 기록 강화 모드 활성화")
        elif action == "force_strategy_review":
            state["force_strategy_review"] = True
            print(f"  → 전략 리뷰 강제 트리거")
        elif action == "force_hold":
            cycles = state.get("force_hold_cycles", 0)
            state["force_hold_cycles"] = cycles + 2
            print(f"  → 강제 관망: {state['force_hold_cycles']}사이클")
        elif action == "go_conservative":
            old = state.get("feedback_bias", 0.0)
            if not isinstance(old, (int, float)):
                old = 0.0
            state["feedback_bias"] = max(-1.0, old - 0.3)
            state["feedback_bias_set_at"] = now
            print(f"  → 보수적 전환: bias {old:.2f} → {state['feedback_bias']:.2f}")
        elif action == "go_aggressive":
            old = state.get("feedback_bias", 0.0)
            if not isinstance(old, (int, float)):
                old = 0.0
            state["feedback_bias"] = min(1.0, old + 0.3)
            state["feedback_bias_set_at"] = now
            print(f"  → 공격적 전환: bias {old:.2f} → {state['feedback_bias']:.2f}")

    _save_state(state)

    # DB에도 저장
    fb_type = actions[0]["type"] if actions else "general"
    _save_to_db(fb_type, message, actions[0]["action"] if actions else None)

    if not matched_tags:
        print(f"  피드백 저장 완료 (다음 사이클에 반영)")
    else:
        print(f"  자동 태그: {', '.join(matched_tags)}")
    print(f"  DB 기록: {'성공' if _save_to_db else '실패'}")


def cmd_param(param_name: str, value: str):
    """특정 파라미터를 직접 오버라이드"""
    state = _load_state()
    overrides = state.get("param_overrides", {})
    overrides[param_name] = value
    state["param_overrides"] = overrides
    state["last_feedback_time"] = datetime.now(KST).isoformat()
    _save_state(state)

    _save_to_db("parameter_change", f"파라미터 오버라이드: {param_name}={value}")
    print(f"  {param_name} = {value} (다음 사이클부터 적용)")


def cmd_status():
    """현재 피드백 상태 조회"""
    state = _load_state()

    print("=== 피드백 상태 ===\n")

    # 성향 바이어스
    bias = state.get("feedback_bias", 0.0)
    if isinstance(bias, str):
        print(f"  성향 바이어스: {bias} (레거시 문자열)")
    else:
        bar_len = int(abs(bias) * 10)
        if bias < 0:
            bar = "◀" + "█" * bar_len + "·" * (10 - bar_len) + "│" + "·" * 10 + "▶"
        elif bias > 0:
            bar = "◀" + "·" * 10 + "│" + "█" * bar_len + "·" * (10 - bar_len) + "▶"
        else:
            bar = "◀" + "·" * 10 + "│" + "·" * 10 + "▶"
        direction = "보수적" if bias < 0 else "공격적" if bias > 0 else "중립"
        print(f"  성향: {bias:+.2f} ({direction})")
        print(f"  {bar}")

    set_at = state.get("feedback_bias_set_at")
    if set_at:
        print(f"  설정 시간: {set_at}")

    # 오버라이드
    overrides = state.get("param_overrides", {})
    interval_override = state.get("min_trade_interval_override")
    conf_override = state.get("confidence_threshold_override")
    force_hold = state.get("force_hold_cycles", 0)
    force_retrain = state.get("force_retrain_next_cycle", False)
    db_verbose = state.get("db_logging_verbose", False)

    print(f"\n  활성 오버라이드:")
    if interval_override:
        print(f"    매매 간격: {interval_override}h (기본: 4h)")
    if conf_override:
        print(f"    confidence 임계값: {conf_override} (기본: 0.5)")
    if force_hold > 0:
        print(f"    강제 관망: {force_hold}사이클 남음")
    if force_retrain:
        print(f"    강제 재학습: 다음 사이클에 트리거")
    if db_verbose:
        print(f"    DB 기록 강화: 활성")
    if overrides:
        for k, v in overrides.items():
            print(f"    {k}: {v}")
    if not any([interval_override, conf_override, force_hold, force_retrain, db_verbose, overrides]):
        print(f"    (없음)")

    # 피드백 큐
    queue = state.get("feedback_queue", [])
    unapplied = [q for q in queue if not q.get("applied")]
    if unapplied:
        print(f"\n  미반영 피드백: {len(unapplied)}건")
        for q in unapplied[-5:]:
            tags = ", ".join(q.get("tags", [])) or "일반"
            print(f"    [{tags}] {q['message'][:60]}")
    else:
        print(f"\n  미반영 피드백: 없음")


def cmd_history():
    """Supabase에 저장된 피드백 이력 조회"""
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not supabase_url or not supabase_key:
        print("SUPABASE 환경변수 미설정")
        return

    import requests
    try:
        resp = requests.get(
            f"{supabase_url}/rest/v1/feedback",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
            },
            params={
                "select": "type,content,applied,created_at",
                "order": "created_at.desc",
                "limit": "10",
            },
            timeout=10,
        )
        if resp.ok:
            rows = resp.json()
            if not rows:
                print("피드백 이력 없음")
                return
            print("=== 최근 피드백 이력 ===\n")
            for r in rows:
                applied = "적용됨" if r.get("applied") else "미적용"
                created = r.get("created_at", "?")[:16]
                print(f"  [{r['type']}] {r['content'][:50]} ({applied}, {created})")
        else:
            print(f"조회 실패: {resp.status_code}")
    except Exception as e:
        print(f"조회 예외: {e}")


def cmd_reset():
    """모든 피드백 오버라이드를 초기화"""
    state = _load_state()
    keys_to_remove = [
        "feedback_bias", "feedback_bias_set_at",
        "min_trade_interval_override", "confidence_threshold_override",
        "force_hold_cycles", "force_retrain_next_cycle",
        "db_logging_verbose", "force_strategy_review",
        "param_overrides", "feedback_queue",
    ]
    for k in keys_to_remove:
        state.pop(k, None)
    _save_state(state)
    print("  모든 피드백 오버라이드가 초기화되었습니다.")


# ── CLI ──────────────────────────────────────────────

USAGE = """
사용법:
  python scripts/feedback.py bias -0.5          보수적으로 조절
  python scripts/feedback.py bias +0.5          공격적으로 조절
  python scripts/feedback.py say "관망 좀 더 해"  자연어 피드백
  python scripts/feedback.py say "거래 많고 수익 없다"
  python scripts/feedback.py say "학습 부진하다"
  python scripts/feedback.py say "DB 기록 안 한다"
  python scripts/feedback.py param MAX_TRADE_AMOUNT 50000   파라미터 직접 변경
  python scripts/feedback.py status             현재 상태 조회
  python scripts/feedback.py history            DB 이력 조회
  python scripts/feedback.py reset              오버라이드 초기화

자연어 피드백 키워드 (자동 감지):
  "거래 많" / "트레이딩 많"  → 매매 간격 자동 확대
  "수익 없" / "얻는게 없"   → confidence 임계값 상향
  "학습 부진"              → 강제 재학습 트리거
  "기록 안"                → DB 기록 강화 모드
  "개선 안"                → 전략 리뷰 강제
  "보수적" / "공격적"       → 성향 자동 조절
  "관망"                   → 강제 관망 2사이클
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "bias" and len(sys.argv) >= 3:
        cmd_bias(sys.argv[2])
    elif command == "say" and len(sys.argv) >= 3:
        cmd_say(" ".join(sys.argv[2:]))
    elif command == "param" and len(sys.argv) >= 4:
        cmd_param(sys.argv[2], sys.argv[3])
    elif command == "status":
        cmd_status()
    elif command == "history":
        cmd_history()
    elif command == "reset":
        cmd_reset()
    else:
        # 레거시 호환: 숫자만 입력하면 bias로 처리
        try:
            float(command)
            cmd_bias(command)
        except ValueError:
            print(USAGE)
            sys.exit(1)
