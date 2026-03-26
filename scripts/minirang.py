#!/usr/bin/env python3
"""
미니랑(MiniRang) — Computer Use 에이전트 (OAuth/구독 기반, API 비용 0원)

claude -p를 사용하여 Mac Mini 데스크톱을 조작한다.
Claude Pro/Max 구독의 OAuth 인증을 사용하므로 별도 API 비용이 없다.

원리:
  1. 스크린샷 캡처 (screencapture)
  2. claude -p에 스크린샷 + 작업 지시를 전달
  3. Claude가 분석 후 실행할 명령(cliclick 등)을 JSON으로 반환
  4. 명령 실행 → 다시 스크린샷 → 반복

Usage:
    python scripts/minirang.py "NordVPN 팝업 닫아줘"
    python scripts/minirang.py --screenshot-only
    python scripts/minirang.py --status
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from dotenv import load_dotenv
load_dotenv(PROJECT_DIR / ".env")

from scripts.minirang_executor import MiniRangExecutor

# === 설정 ===
MAX_ITERATIONS = int(os.getenv("MINIRANG_MAX_ITERATIONS", "10"))
TIMEOUT_SEC = int(os.getenv("MINIRANG_TIMEOUT", "180"))
NOTIFY = os.getenv("MINIRANG_NOTIFY", "true").lower() == "true"

STATE_FILE = PROJECT_DIR / "data" / "minirang_state.json"
LOG_DIR = PROJECT_DIR / "logs" / "minirang"
SCREENSHOT_DIR = PROJECT_DIR / "data" / "minirang_screenshots"

# claude -p 경로
CLAUDE_BIN = os.getenv("MINIRANG_CLAUDE_BIN", "claude")

SYSTEM_PROMPT = """당신은 Mac Mini 데스크톱을 조작하는 AI 에이전트 '미니랑'입니다.
사용자가 보내준 스크린샷을 분석하고, 다음 행동을 JSON으로 반환하세요.

## 반환 형식 (반드시 JSON만 출력)

작업이 필요한 경우:
```json
{
  "status": "action",
  "actions": [
    {"type": "click", "x": 500, "y": 300, "desc": "확인 버튼 클릭"},
    {"type": "type", "text": "hello", "desc": "텍스트 입력"},
    {"type": "key", "keys": "cmd+v", "desc": "붙여넣기"},
    {"type": "scroll", "x": 500, "y": 400, "direction": "down", "amount": 3},
    {"type": "wait", "seconds": 2}
  ],
  "reasoning": "팝업의 확인 버튼이 보여서 클릭합니다"
}
```

작업 완료 시:
```json
{
  "status": "done",
  "summary": "작업 완료 설명"
}
```

## 액션 타입
- click: 좌클릭 (x, y 좌표)
- right_click: 우클릭
- double_click: 더블클릭
- type: 텍스트 입력
- key: 키 조합 (예: cmd+c, return, tab)
- scroll: 스크롤 (direction: up/down/left/right)
- wait: 대기 (seconds)
- open_app: 앱 실행 (name: "앱이름")

## 좌표 체계
스크린샷은 2560x1080 → 1568x661로 리사이즈됨.
좌표는 **리사이즈된 이미지 기준**으로 지정하세요.
executor가 자동으로 실제 화면 좌표로 변환합니다.

## 안전 규칙
1. 금융 거래/매매/송금 절대 금지
2. 비밀번호 입력 금지
3. 시스템 파일 삭제 금지

반드시 JSON만 출력하세요. 설명이나 마크다운 코드블록 없이 순수 JSON만."""


def send_telegram(msg_type, title, body, image_path=None):
    """텔레그램 알림"""
    if not NOTIFY:
        return
    try:
        from scripts.notify_telegram import send_message, send_photo
        send_message(msg_type, title, body)
        if image_path and os.path.exists(image_path):
            send_photo(image_path, caption=title)
    except Exception as e:
        print(f"[MiniRang] 텔레그램 실패: {e}", file=sys.stderr)


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"total_tasks": 0, "last_task": None, "last_status": None, "last_run_at": None}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def save_log(log_data):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = LOG_DIR / f"{ts}.json"
    path.write_text(json.dumps(log_data, ensure_ascii=False, indent=2))
    return path


def call_claude(task: str, screenshot_path: str) -> dict:
    """
    claude -p로 스크린샷 + 작업 지시를 전달하고 JSON 응답을 받는다.
    OAuth 인증 사용 — API 비용 없음.
    """
    prompt = f"""다음 스크린샷을 분석하고 작업을 수행하세요.

작업: {task}

스크린샷 파일: {screenshot_path}
(이 파일을 Read 도구로 읽어서 분석하세요)

반드시 JSON만 출력하세요."""

    full_prompt = SYSTEM_PROMPT + "\n\n" + prompt

    try:
        result = subprocess.run(
            [CLAUDE_BIN, "-p", "--dangerously-skip-permissions", full_prompt],
            capture_output=True, text=True, timeout=120,
            cwd=str(PROJECT_DIR),
        )
        output = result.stdout.strip()

        # JSON 추출 (코드블록이 포함된 경우 처리)
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0].strip()
        elif "```" in output:
            output = output.split("```")[1].split("```")[0].strip()

        # JSON 파싱
        return json.loads(output)

    except json.JSONDecodeError:
        # JSON 파싱 실패 시 텍스트에서 JSON 추출 시도
        try:
            import re
            match = re.search(r'\{[\s\S]*\}', output)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return {"status": "error", "summary": f"JSON 파싱 실패: {output[:200]}"}

    except subprocess.TimeoutExpired:
        return {"status": "error", "summary": "claude -p 타임아웃 (120초)"}

    except FileNotFoundError:
        return {"status": "error", "summary": f"claude 명령을 찾을 수 없음: {CLAUDE_BIN}"}

    except Exception as e:
        return {"status": "error", "summary": str(e)}


def execute_actions(executor: MiniRangExecutor, actions: list) -> list:
    """액션 목록을 실행하고 결과 반환"""
    results = []
    for action in actions:
        a_type = action.get("type", "")
        desc = action.get("desc", "")

        if a_type == "click":
            r = executor.execute({"action": "left_click", "coordinate": [action["x"], action["y"]]})
        elif a_type == "right_click":
            r = executor.execute({"action": "right_click", "coordinate": [action["x"], action["y"]]})
        elif a_type == "double_click":
            r = executor.execute({"action": "double_click", "coordinate": [action["x"], action["y"]]})
        elif a_type == "type":
            r = executor.execute({"action": "type", "text": action.get("text", "")})
        elif a_type == "key":
            r = executor.execute({"action": "key", "text": action.get("keys", "")})
        elif a_type == "scroll":
            r = executor.execute({
                "action": "scroll",
                "coordinate": [action.get("x", 800), action.get("y", 400)],
                "scroll_direction": action.get("direction", "down"),
                "scroll_amount": action.get("amount", 3),
            })
        elif a_type == "wait":
            time.sleep(min(action.get("seconds", 1), 5))
            r = f"Waited {action.get('seconds', 1)}s"
        elif a_type == "open_app":
            app = action.get("name", "")
            subprocess.run(["open", "-a", app], check=False)
            time.sleep(2)
            r = f"Opened {app}"
        else:
            r = f"Unknown action: {a_type}"

        print(f"  [{a_type}] {desc} → {r if isinstance(r, str) else 'OK'}")
        results.append({"action": a_type, "desc": desc, "result": str(r)[:100]})
        time.sleep(0.3)  # 액션 사이 간격

    return results


def run_task(task: str, max_iter: int = None, timeout: int = None):
    """미니랑 메인 루프 (OAuth 기반, API 비용 0원)"""
    max_iter = max_iter or MAX_ITERATIONS
    timeout = timeout or TIMEOUT_SEC

    executor = MiniRangExecutor(display_width=2560, display_height=1080)
    start = time.monotonic()
    iteration = 0
    summary = ""
    errors = []

    print(f"[MiniRang] 🖥️ 작업 시작: {task}")
    print(f"[MiniRang] OAuth 모드 (API 비용 없음), 최대 {max_iter}회")

    for iteration in range(1, max_iter + 1):
        elapsed = time.monotonic() - start
        if elapsed > timeout:
            summary = f"타임아웃 ({timeout}초)"
            errors.append(summary)
            break

        print(f"\n[MiniRang] --- 반복 {iteration}/{max_iter} ({elapsed:.0f}s) ---")

        # 1. 스크린샷 촬영
        print("[MiniRang] 📸 스크린샷 캡처...")
        screenshot_result = executor._screenshot()
        if isinstance(screenshot_result, str) and "Error" in screenshot_result:
            errors.append(screenshot_result)
            break

        # 스크린샷 경로 (리사이즈된 버전)
        screenshot_path = "/tmp/minirang_scaled.png"

        # 2. Claude에 분석 요청
        print("[MiniRang] 🤖 Claude 분석 중...")
        response = call_claude(task, screenshot_path)

        status = response.get("status", "error")

        if status == "done":
            summary = response.get("summary", "작업 완료")
            print(f"[MiniRang] ✅ 완료: {summary}")
            break

        elif status == "action":
            reasoning = response.get("reasoning", "")
            actions = response.get("actions", [])
            print(f"[MiniRang] 💭 {reasoning}")
            print(f"[MiniRang] ⚡ {len(actions)}개 액션 실행:")

            execute_actions(executor, actions)

            # 액션 실행 후 잠시 대기 (UI 반영)
            time.sleep(1)

        elif status == "error":
            err = response.get("summary", "알 수 없는 에러")
            errors.append(err)
            print(f"[MiniRang] ❌ 에러: {err}")
            break

        else:
            errors.append(f"알 수 없는 상태: {status}")
            break

    # 결과 정리
    duration = time.monotonic() - start
    final_status = "error" if errors else "success"

    result = {
        "status": final_status,
        "task": task,
        "summary": summary,
        "iterations": iteration,
        "duration_seconds": round(duration, 1),
        "mode": "oauth (free)",
        "errors": errors,
        "timestamp": datetime.now().isoformat(),
    }

    # 로그 저장
    log_path = save_log(result)
    print(f"\n[MiniRang] 📋 로그: {log_path}")

    # 상태 업데이트
    state = load_state()
    state["total_tasks"] = state.get("total_tasks", 0) + 1
    state["last_task"] = task
    state["last_status"] = final_status
    state["last_run_at"] = datetime.now().isoformat()
    save_state(state)

    # 텔레그램 알림
    emoji = "✅" if final_status == "success" else "❌"
    tg_title = f"🖥️ 미니랑 {emoji}"
    tg_body = f"작업: {task}\n반복: {iteration}회, {duration:.0f}초\n결과: {summary[:200]}"
    last_ss = sorted(executor.screenshot_dir.glob("iter_*.png"))
    send_telegram("status", tg_title, tg_body, image_path=str(last_ss[-1]) if last_ss else None)

    executor.cleanup(keep_last=True)
    return result


def screenshot_only():
    """스크린샷만 찍어서 텔레그램 전송"""
    executor = MiniRangExecutor(display_width=2560, display_height=1080)
    executor._screenshot()
    screenshots = sorted(executor.screenshot_dir.glob("iter_*.png"))
    if screenshots:
        send_telegram("status", "🖥️ 미니랑 스크린샷", "현재 화면", image_path=str(screenshots[-1]))
        print(f"[MiniRang] 스크린샷 전송: {screenshots[-1]}")


def show_status():
    state = load_state()
    print(json.dumps(state, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="미니랑(MiniRang) — Computer Use (OAuth, 무료)")
    parser.add_argument("task", nargs="?", default=None, help="실행할 작업")
    parser.add_argument("--screenshot-only", action="store_true", help="스크린샷만 전송")
    parser.add_argument("--status", action="store_true", help="상태 출력")
    parser.add_argument("--max-iter", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=None)
    args = parser.parse_args()

    if args.screenshot_only:
        screenshot_only()
    elif args.status:
        show_status()
    elif args.task:
        result = run_task(args.task, max_iter=args.max_iter, timeout=args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
