#!/usr/bin/env python3
"""
자연어 피드백 추출기 — 텔레그램 메시지에서 매매 피드백을 자동 감지

텔레그램 리스너에서 수신된 일반 메시지를 분석하여:
  1. 키워드/정규식 기반 의도 분류 (behavior_change, parameter_change, general, one_time)
  2. 복합 패턴 감지 (예: "너무 공격적이야 보수적으로 해")
  3. confidence 점수 산출 (0.3~1.0)
  4. anti-spam (3자 미만, 명령어, 5분 내 동일 유형 중복 차단)
  5. Supabase feedback 테이블 저장

사용:
    from scripts.nl_feedback import extract_feedback, save_feedback_to_db, get_feedback_stats
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import timedelta, timezone
from pathlib import Path

# sys.path setup for sibling imports
PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from dotenv import load_dotenv

load_dotenv(PROJECT_DIR / ".env")

from scripts.atomic_write import atomic_json_save

KST = timezone(timedelta(hours=9))
STATE_FILE = PROJECT_DIR / "data" / "nl_feedback_state.json"
ANTI_SPAM_WINDOW = 300  # 5 minutes in seconds


# ── 키워드 규칙 정의 ──────────────────────────────

# (pattern, type, action, weight)
# weight: 키워드 강도. 높을수록 confidence에 기여
KEYWORD_RULES: list[tuple[str, str, str, float]] = [
    # Strategy bias — behavior_change
    ("보수적으로", "behavior_change", "go_conservative", 0.35),
    ("보수적으로 해", "behavior_change", "go_conservative", 0.40),
    ("공격적으로", "behavior_change", "go_aggressive", 0.35),
    ("공격적으로 해", "behavior_change", "go_aggressive", 0.40),
    ("관망해", "behavior_change", "force_hold", 0.35),
    ("관망 해", "behavior_change", "force_hold", 0.30),
    ("조심해", "behavior_change", "go_conservative", 0.25),
    ("더 사", "behavior_change", "bias_buy", 0.25),
    ("더 팔아", "behavior_change", "bias_sell", 0.25),
    ("매수해", "behavior_change", "bias_buy", 0.30),
    ("매도해", "behavior_change", "bias_sell", 0.30),

    # Parameter change
    ("거래 줄여", "parameter_change", "reduce_trade_frequency", 0.35),
    ("금액 줄여", "parameter_change", "reduce_trade_amount", 0.35),
    ("간격 늘려", "parameter_change", "increase_interval", 0.30),
    ("손절 높여", "parameter_change", "raise_stop_loss", 0.30),
    ("익절 낮춰", "parameter_change", "lower_take_profit", 0.30),
    ("거래 늘려", "parameter_change", "increase_trade_frequency", 0.30),
    ("금액 늘려", "parameter_change", "increase_trade_amount", 0.30),

    # Complaints — general
    ("왜 샀어", "general", "question_buy", 0.30),
    ("왜 팔았어", "general", "question_sell", 0.30),
    ("손해", "general", "complaint_loss", 0.25),
    ("수익 없", "general", "complaint_no_profit", 0.25),
    ("기록 안", "general", "complaint_no_record", 0.25),
    ("거래 많", "general", "complaint_too_many_trades", 0.25),
    ("왜 관망", "general", "question_hold", 0.25),

    # Market opinion — one_time
    ("바닥", "one_time", "opinion_bottom", 0.20),
    ("천장", "one_time", "opinion_top", 0.20),
    ("위험", "one_time", "opinion_danger", 0.20),
    ("기회", "one_time", "opinion_opportunity", 0.20),
    ("급등", "one_time", "opinion_surge", 0.20),
    ("급락", "one_time", "opinion_crash", 0.20),
    ("폭락", "one_time", "opinion_crash", 0.25),
    ("반등", "one_time", "opinion_bounce", 0.20),
    ("상승장", "one_time", "opinion_bull", 0.25),
    ("하락장", "one_time", "opinion_bear", 0.25),

    # Positive — general
    ("잘했어", "general", "positive", 0.25),
    ("좋아", "general", "positive", 0.20),
    ("굿", "general", "positive", 0.20),
    ("완벽", "general", "positive", 0.30),
    ("잘한다", "general", "positive", 0.25),
    ("대박", "general", "positive", 0.20),
]

# Regex patterns for compound detection
COMPOUND_PATTERNS: list[tuple[re.Pattern, str, str, float]] = [
    (re.compile(r"너무\s*공격적.*보수적"), "behavior_change", "go_conservative", 0.45),
    (re.compile(r"너무\s*보수적.*공격적"), "behavior_change", "go_aggressive", 0.45),
    (re.compile(r"좀\s*더\s*보수적"), "behavior_change", "go_conservative", 0.40),
    (re.compile(r"좀\s*더\s*공격적"), "behavior_change", "go_aggressive", 0.40),
    (re.compile(r"(매매|거래)\s*(를\s*)?(좀\s*)?줄"), "parameter_change", "reduce_trade_frequency", 0.35),
    (re.compile(r"(매매|거래)\s*(를\s*)?(좀\s*)?늘"), "parameter_change", "increase_trade_frequency", 0.35),
    (re.compile(r"(금액|돈)\s*(을\s*)?(좀\s*)?줄"), "parameter_change", "reduce_trade_amount", 0.35),
    (re.compile(r"(간격|주기)\s*(을\s*)?(좀\s*)?늘"), "parameter_change", "increase_interval", 0.35),
    (re.compile(r"(한동안|당분간)\s*관망"), "behavior_change", "force_hold", 0.40),
    (re.compile(r"지금\s*(은\s*)?위험"), "one_time", "opinion_danger", 0.30),
    (re.compile(r"지금\s*(이\s*)?기회"), "one_time", "opinion_opportunity", 0.30),
    (re.compile(r"손절\s*(을\s*)?(좀\s*)?높"), "parameter_change", "raise_stop_loss", 0.35),
    (re.compile(r"익절\s*(을\s*)?(좀\s*)?낮"), "parameter_change", "lower_take_profit", 0.35),
]


# ── 상태 관리 ──────────────────────────────────────

def _load_state() -> dict:
    """anti-spam 상태 파일을 로드한다."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"recent_extractions": [], "stats": {"total": 0, "by_type": {}}}


def _save_state(state: dict) -> None:
    """anti-spam 상태 파일을 원자적으로 저장한다."""
    atomic_json_save(STATE_FILE, state)


def _is_spam(sender_name: str, fb_type: str, state: dict) -> bool:
    """동일 발신자의 동일 유형 피드백이 5분 내 중복인지 확인한다."""
    now = time.time()
    recent = state.get("recent_extractions", [])

    for entry in recent:
        if (entry.get("sender") == sender_name
                and entry.get("type") == fb_type
                and now - entry.get("timestamp", 0) < ANTI_SPAM_WINDOW):
            return True
    return False


def _record_extraction(sender_name: str, fb_type: str, state: dict) -> None:
    """추출 기록을 상태에 추가하고 오래된 항목을 정리한다."""
    now = time.time()
    recent = state.get("recent_extractions", [])

    # Add new entry
    recent.append({
        "sender": sender_name,
        "type": fb_type,
        "timestamp": now,
    })

    # Purge entries older than anti-spam window
    cutoff = now - ANTI_SPAM_WINDOW
    recent = [e for e in recent if e.get("timestamp", 0) > cutoff]
    state["recent_extractions"] = recent

    # Update stats
    stats = state.get("stats", {"total": 0, "by_type": {}})
    stats["total"] = stats.get("total", 0) + 1
    stats["by_type"][fb_type] = stats.get("by_type", {}).get(fb_type, 0) + 1
    state["stats"] = stats


# ── 핵심 추출 함수 ────────────────────────────────

def extract_feedback(text: str, sender_name: str) -> dict | None:
    """메시지에서 피드백 의도를 추출한다.

    Args:
        text: 수신된 메시지 텍스트
        sender_name: 발신자 이름

    Returns:
        추출된 피드백 dict 또는 None (피드백 아닌 경우)
        {
            "type": "behavior_change" | "parameter_change" | "general" | "one_time",
            "action": str,
            "content": str,
            "confidence": float (0.3~1.0),
            "matched_keywords": list[str],
            "sender": str,
        }
    """
    # Anti-spam: too short
    if not text or len(text.strip()) < 3:
        return None

    text = text.strip()

    # Anti-spam: commands
    if text.startswith("/"):
        return None

    # Collect all matches
    matches: list[tuple[str, str, str, float]] = []

    # Check compound patterns first (higher priority)
    for pattern, fb_type, action, weight in COMPOUND_PATTERNS:
        if pattern.search(text):
            matches.append((pattern.pattern, fb_type, action, weight))

    # Check simple keyword matches
    for keyword, fb_type, action, weight in KEYWORD_RULES:
        if keyword in text:
            matches.append((keyword, fb_type, action, weight))

    if not matches:
        return None

    # Anti-spam: check for duplicate within window
    state = _load_state()

    # Determine primary type — pick highest weight match
    matches.sort(key=lambda m: m[3], reverse=True)
    primary = matches[0]
    primary_type = primary[1]
    primary_action = primary[2]

    if _is_spam(sender_name, primary_type, state):
        return None

    # Calculate confidence: base from strongest match + bonus for additional matches
    total_weight = sum(m[3] for m in matches)
    # Normalize: single weak match ~0.3, multiple strong matches ~1.0
    confidence = min(1.0, max(0.3, total_weight))

    matched_keywords = list(dict.fromkeys(m[0] for m in matches))  # deduplicated, order preserved

    # Record extraction for anti-spam
    _record_extraction(sender_name, primary_type, state)
    _save_state(state)

    return {
        "type": primary_type,
        "action": primary_action,
        "content": text,
        "confidence": round(confidence, 2),
        "matched_keywords": matched_keywords,
        "sender": sender_name,
    }


# ── DB 저장 ──────────────────────────────────────

def save_feedback_to_db(entry: dict) -> bool:
    """추출된 피드백을 Supabase feedback 테이블에 저장한다.

    Args:
        entry: extract_feedback()의 반환값

    Returns:
        저장 성공 여부
    """
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not supabase_url or not supabase_key:
        return False

    import requests

    try:
        row = {
            "type": entry["type"],
            "content": (
                f"[자동추출:{entry['sender']}] {entry['content']} "
                f"(action={entry['action']}, confidence={entry['confidence']}, "
                f"keywords={','.join(entry['matched_keywords'])})"
            ),
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


# ── 통계 조회 ──────────────────────────────────────

def get_feedback_stats() -> dict:
    """자동 추출 피드백 통계를 반환한다.

    Returns:
        {"total": int, "by_type": {"behavior_change": int, ...}, "recent_count": int}
    """
    state = _load_state()
    stats = state.get("stats", {"total": 0, "by_type": {}})

    # Count recent (within anti-spam window)
    now = time.time()
    cutoff = now - ANTI_SPAM_WINDOW
    recent = state.get("recent_extractions", [])
    recent_count = sum(1 for e in recent if e.get("timestamp", 0) > cutoff)

    return {
        "total": stats.get("total", 0),
        "by_type": stats.get("by_type", {}),
        "recent_count": recent_count,
    }


# ── CLI (디버그/테스트용) ────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python scripts/nl_feedback.py <메시지>")
        print("       python scripts/nl_feedback.py stats")
        print()
        print("예시:")
        print('  python scripts/nl_feedback.py "지금 너무 공격적이야 좀 보수적으로 해"')
        print('  python scripts/nl_feedback.py "바닥인 것 같아"')
        print('  python scripts/nl_feedback.py "잘했어"')
        sys.exit(0)

    if sys.argv[1] == "stats":
        stats = get_feedback_stats()
        print(f"총 추출: {stats['total']}건")
        for t, c in stats.get("by_type", {}).items():
            print(f"  {t}: {c}건")
        print(f"최근 5분: {stats['recent_count']}건")
        sys.exit(0)

    text = " ".join(sys.argv[1:])
    result = extract_feedback(text, "test_user")
    if result:
        print(f"type: {result['type']}")
        print(f"action: {result['action']}")
        print(f"confidence: {result['confidence']}")
        print(f"keywords: {result['matched_keywords']}")
    else:
        print("피드백 감지 안 됨")
