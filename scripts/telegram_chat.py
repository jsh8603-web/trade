#!/usr/bin/env python3
"""
텔레그램 다중 채팅 터미널

시작 시 연락처 목록을 표시하고, 통합 채팅방에서 모든 사람과 동시 대화.
번호/이름으로 대화 상대를 전환하며, 모든 수신 메시지가 실시간 표시된다.

실행: python scripts/telegram_chat.py
중지: Ctrl+C
"""

from __future__ import annotations

import io
import os
import sys
import time
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows cp949 대응 + unbuffered
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import requests  # Telegram Bot API 호출용 (Supabase REST 아님)
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
load_dotenv(PROJECT_DIR / ".env")

from core.db import db

KST = timezone(timedelta(hours=9))
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OWNER_CHAT_ID = os.getenv("TELEGRAM_USER_ID", "")

POLL_INTERVAL = 2
_running = True
_current_target: dict | None = None
_contacts: list = []                   # 캐시된 연락처 목록
_contact_colors: dict[str, str] = {}   # chat_id → 색상

# ── 색상 (Windows 터미널 ANSI) ──────────────────
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
RED     = "\033[91m"
BLUE    = "\033[94m"
WHITE   = "\033[97m"
DIM     = "\033[90m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

# 사용자별 색상 팔레트
_COLOR_PALETTE = [GREEN, YELLOW, MAGENTA, CYAN, BLUE, RED, WHITE]


def ts_now() -> str:
    return datetime.now(KST).strftime("%H:%M:%S")


def get_color_for(chat_id: str) -> str:
    """사용자별 고정 색상 반환"""
    if chat_id not in _contact_colors:
        idx = len(_contact_colors) % len(_COLOR_PALETTE)
        _contact_colors[chat_id] = _COLOR_PALETTE[idx]
    return _contact_colors[chat_id]


# ── DB 연락처 ──────────────────────────────────
def get_all_contacts() -> list:
    try:
        return db.select(
            "telegram_contacts",
            filters={"is_active": "eq.true"},
            order="role.asc,name.asc",
            select="chat_id,name,role,aliases",
        )
    except Exception:
        return []


def save_message(chat_id, direction, message, **kwargs):
    data = {"chat_id": chat_id, "direction": direction, "message": message}
    data.update({k: v for k, v in kwargs.items() if v is not None})
    try:
        db.insert("telegram_messages", data)
    except Exception:
        pass


def send_telegram(chat_id: str, text: str) -> bool:
    try:
        from utils.machine import get_machine_name
        tag = f"[{get_machine_name()}]"
    except Exception:
        import platform
        tag = f"[{platform.node().split('.')[0]}]"
    r = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": f"{text}\n{tag}"},
        timeout=15,
    )
    return r.ok


def lookup_by_chat_id(chat_id: str) -> dict | None:
    for c in _contacts:
        if c["chat_id"] == chat_id:
            return c
    # 캐시 미스 → DB 조회
    try:
        rows = db.select(
            "telegram_contacts",
            filters={"chat_id": f"eq.{chat_id}", "is_active": "eq.true"},
            select="chat_id,name,role,aliases",
        )
    except Exception:
        rows = []
    if rows:
        return rows[0]
    return None


def find_contact(keyword: str) -> dict | None:
    """번호, 이름, 별명으로 연락처 검색"""
    # 번호로 검색
    try:
        idx = int(keyword) - 1
        if 0 <= idx < len(_contacts):
            return _contacts[idx]
    except ValueError:
        pass
    # 이름/별명으로 검색
    kw = keyword.strip().lower()
    for c in _contacts:
        if kw == c["name"].lower():
            return c
        for alias in (c.get("aliases") or []):
            if kw == alias.lower():
                return c
    # 부분 매치
    for c in _contacts:
        if kw in c["name"].lower():
            return c
    return None


# ── 화면 그리기 ──────────────────────────────────
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def draw_header():
    print(f"{BOLD}{CYAN}")
    print("╔═══════════════════════════════════════════════════╗")
    print("║          💬 텔레그램 다중 채팅 터미널              ║")
    print("╚═══════════════════════════════════════════════════╝")
    print(f"{RESET}")


def draw_contact_bar():
    """상단 연락처 바 — 현재 대화 상대 표시"""
    parts = []
    for i, c in enumerate(_contacts, 1):
        color = get_color_for(c["chat_id"])
        is_selected = _current_target and c["chat_id"] == _current_target["chat_id"]
        if is_selected:
            parts.append(f" {BOLD}{color}[{i}]◆{c['name']}{RESET}")
        else:
            parts.append(f" {DIM}[{i}]{c['name']}{RESET}")
    target_str = f"  →  {BOLD}{_current_target['name']}{RESET}" if _current_target else f"  →  {DIM}(선택 안됨){RESET}"
    print(f" {'  '.join(parts)}")
    print(f" {DIM}{'─' * 55}{RESET}")
    print(f" 대화 상대{target_str}")
    print(f" {DIM}{'─' * 55}{RESET}")


def draw_help():
    print(f" {DIM}명령어: /1~/9 상대선택 | /all 전체공지 | /list 목록 | /recent 내역 | /q 종료{RESET}")
    print(f" {DIM}        이름>메시지 — 특정인에게 | 그냥 입력 — 현재 상대에게{RESET}")
    print()


def print_incoming(sender_name: str, text: str, chat_id: str = ""):
    ts = ts_now()
    color = get_color_for(chat_id) if chat_id else GREEN
    print(f"\r {DIM}[{ts}]{RESET} {color}{BOLD}{sender_name}{RESET}: {text}", flush=True)


def print_outgoing(target_name: str, text: str, ok: bool):
    ts = ts_now()
    status = f"{GREEN}✓{RESET}" if ok else f"{RED}✗ 전송실패{RESET}"
    print(f" {DIM}[{ts}]{RESET} {CYAN}나 → {target_name}{RESET}: {text}  {status}", flush=True)


def print_system(msg: str):
    ts = ts_now()
    print(f" {DIM}[{ts}]{RESET} {YELLOW}ℹ {msg}{RESET}", flush=True)


# ── 수신 폴링 스레드 ──────────────────────────────
def poll_incoming(offset_holder: list):
    """백그라운드에서 텔레그램 메시지를 수신하여 콘솔에 표시"""
    global _current_target
    while _running:
        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates",
                params={"offset": offset_holder[0], "timeout": POLL_INTERVAL,
                        "allowed_updates": '["message"]'},
                timeout=POLL_INTERVAL + 10,
            )
            if not resp.ok:
                time.sleep(POLL_INTERVAL)
                continue

            for upd in resp.json().get("result", []):
                offset_holder[0] = upd["update_id"] + 1
                msg = upd.get("message")
                if not msg or not msg.get("text"):
                    continue

                chat_id = str(msg["chat"]["id"])
                text = msg["text"]
                tg_username = msg["chat"].get("username", "")
                tg_msg_id = msg.get("message_id")

                contact = lookup_by_chat_id(chat_id)
                sender_name = contact["name"] if contact else f"미등록({chat_id})"

                # DB 기록
                save_message(
                    chat_id=chat_id, direction="incoming", message=text,
                    worker_name=sender_name,
                    telegram_message_id=tg_msg_id,
                    telegram_username=tg_username,
                )

                # 봇 명령어 처리
                if text.startswith("/"):
                    handle_bot_command(chat_id, text, contact)
                    continue

                # 콘솔 출력 — 모든 사람의 메시지가 보임
                print_incoming(sender_name, text, chat_id)

                # 마지막 메시지 보낸 사람을 자동으로 대화 상대로 전환
                if contact and (not _current_target or _current_target["chat_id"] != chat_id):
                    _current_target = contact
                    print_system(f"대화 상대 자동 전환: {contact['name']}")

        except requests.exceptions.Timeout:
            continue
        except requests.exceptions.ConnectionError:
            time.sleep(5)
        except Exception:
            time.sleep(3)


def handle_bot_command(chat_id: str, text: str, sender: dict | None):
    """텔레그램에서 보낸 봇 명령어 처리"""
    cmd = text.strip().lower()

    if cmd == "/start":
        if sender:
            send_telegram(chat_id,
                f"안녕하세요 {sender['name']}님! [{sender['role']}]\n\n"
                f"명령어: /list /msg 이름 메시지 /all 메시지 /chat_id")
        else:
            send_telegram(chat_id,
                f"CoinTrading 봇입니다.\nchat_id: {chat_id}\n관리자에게 알려주세요.")
        return

    if cmd == "/chat_id":
        send_telegram(chat_id, f"chat_id: {chat_id}")
        return

    if not sender:
        send_telegram(chat_id, f"미등록 사용자. chat_id: {chat_id}")
        return

    if cmd == "/list":
        contacts = get_all_contacts()
        lines = ["[연락처 목록]"]
        for c in contacts:
            aliases = c.get("aliases") or []
            alias_str = f" ({', '.join(aliases)})" if aliases else ""
            lines.append(f"  {c['name']}{alias_str} [{c['role']}]")
        send_telegram(chat_id, "\n".join(lines))
        return

    if text.strip().lower().startswith("/msg "):
        parts = text[5:].strip().split(None, 1)
        if len(parts) >= 2:
            target_name, msg_text = parts
            target = find_contact(target_name)
            if target:
                forward = f"[{sender['name']}] {msg_text}"
                ok = send_telegram(target["chat_id"], forward)
                if ok:
                    send_telegram(chat_id, f"✓ {target['name']}에게 전송")
                    save_message(chat_id=target["chat_id"], direction="incoming",
                                 message=forward, worker_name=sender["name"])
                    print_incoming(sender["name"], f"→ {target['name']}: {msg_text}", chat_id)
            else:
                send_telegram(chat_id, f"'{target_name}' 찾을 수 없음. /list 확인")
        return

    if text.strip().lower().startswith("/all "):
        msg_text = text[5:].strip()
        contacts = get_all_contacts()
        sent = 0
        for c in contacts:
            if c["chat_id"] != chat_id:
                send_telegram(c["chat_id"], f"[공지 from {sender['name']}] {msg_text}")
                sent += 1
        send_telegram(chat_id, f"✓ {sent}명에게 공지 완료")
        print_system(f"공지 from {sender['name']}: {msg_text}")
        return


# ── 최근 대화 불러오기 ──────────────────────────────
def load_recent_all(limit: int = 20):
    """모든 연락처의 최근 대화를 통합 표시"""
    try:
        rows = db.select(
            "telegram_messages",
            order="created_at.desc",
            limit=limit,
            select="chat_id,direction,message,created_at,worker_name",
        )
        if not rows:
            print(f" {DIM}(이전 대화 없음){RESET}\n", flush=True)
            return

        messages = list(reversed(rows))
        print(f" {DIM}── 최근 대화 {len(messages)}건 ──{RESET}")
        for m in messages:
            try:
                created = datetime.fromisoformat(m["created_at"].replace("Z", "+00:00"))
                ts = created.astimezone(KST).strftime("%m/%d %H:%M")
            except Exception:
                ts = "?"
            direction = m.get("direction", "")
            text = m.get("message", "")
            name = m.get("worker_name", "")
            chat_id = m.get("chat_id", "")
            color = get_color_for(chat_id)

            if direction == "incoming":
                print(f" {DIM}[{ts}]{RESET} {color}{name}{RESET}: {text}")
            else:
                # 누구에게 보냈는지 찾기
                target_contact = lookup_by_chat_id(chat_id)
                target_name = target_contact["name"] if target_contact else chat_id
                print(f" {DIM}[{ts}]{RESET} {CYAN}나→{target_name}{RESET}: {text}")
        print(f" {DIM}{'─' * 50}{RESET}\n")

    except Exception as e:
        print(f" {DIM}(대화 내역 로드 실패: {e}){RESET}\n", flush=True)


def load_recent_for(chat_id: str, limit: int = 10):
    """특정 상대와의 최근 대화"""
    try:
        rows = db.select(
            "telegram_messages",
            filters={"chat_id": f"eq.{chat_id}"},
            order="created_at.desc",
            limit=limit,
            select="direction,message,created_at,worker_name",
        )
        if not rows:
            print(f" {DIM}(이전 대화 없음){RESET}\n", flush=True)
            return

        messages = list(reversed(rows))
        contact = lookup_by_chat_id(chat_id)
        cname = contact["name"] if contact else chat_id
        color = get_color_for(chat_id)
        print(f" {DIM}── {cname}과(와) 최근 {len(messages)}건 ──{RESET}")
        for m in messages:
            try:
                created = datetime.fromisoformat(m["created_at"].replace("Z", "+00:00"))
                ts = created.astimezone(KST).strftime("%m/%d %H:%M")
            except Exception:
                ts = "?"
            direction = m.get("direction", "")
            text = m.get("message", "")
            name = m.get("worker_name", "")

            if direction == "incoming":
                print(f" {DIM}[{ts}]{RESET} {color}{name}{RESET}: {text}")
            else:
                print(f" {DIM}[{ts}]{RESET} {CYAN}나{RESET}: {text}")
        print(f" {DIM}{'─' * 50}{RESET}\n")
    except Exception as e:
        print(f" {DIM}(로드 실패: {e}){RESET}\n", flush=True)


# ── 로컬 입력 처리 ──────────────────────────────
def handle_input(text: str):
    """터미널 입력 처리"""
    global _current_target
    text = text.strip()
    if not text:
        return

    # ── 명령어 ──
    # /번호 — 대화 상대 전환
    if len(text) >= 2 and text[0] == '/' and text[1:].isdigit():
        num = int(text[1:])
        if 1 <= num <= len(_contacts):
            _current_target = _contacts[num - 1]
            color = get_color_for(_current_target["chat_id"])
            print_system(f"대화 상대: {color}{BOLD}{_current_target['name']}{RESET}")
            load_recent_for(_current_target["chat_id"], 5)
        else:
            print_system(f"잘못된 번호. 1~{len(_contacts)} 범위")
        return

    # /to 이름
    if text.lower().startswith("/to "):
        name = text[4:].strip()
        found = find_contact(name)
        if found:
            _current_target = found
            color = get_color_for(_current_target["chat_id"])
            print_system(f"대화 상대: {color}{BOLD}{_current_target['name']}{RESET}")
            load_recent_for(_current_target["chat_id"], 5)
        else:
            print_system(f"'{name}' 찾을 수 없음")
        return

    if text.lower() == "/list":
        print(f"\n {BOLD}[연락처 목록]{RESET}")
        for i, c in enumerate(_contacts, 1):
            color = get_color_for(c["chat_id"])
            role_icon = "👑" if c["role"] == "owner" else "👤"
            aliases = c.get("aliases") or []
            alias_str = f" {DIM}({', '.join(aliases)}){RESET}" if aliases else ""
            is_sel = "  ◆" if _current_target and c["chat_id"] == _current_target["chat_id"] else ""
            print(f"  {BOLD}{color}[{i}]{RESET} {role_icon} {color}{c['name']}{RESET}{alias_str} {DIM}[{c['role']}]{RESET}{GREEN}{is_sel}{RESET}")
        print()
        return

    if text.lower() == "/recent":
        if _current_target:
            load_recent_for(_current_target["chat_id"])
        else:
            load_recent_all()
        return

    if text.lower() == "/all-recent":
        load_recent_all()
        return

    if text.lower().startswith("/all "):
        msg_text = text[5:].strip()
        if not msg_text:
            return
        sent = 0
        for c in _contacts:
            send_telegram(c["chat_id"], f"[공지] {msg_text}")
            save_message(chat_id=c["chat_id"], direction="outgoing",
                         message=f"[공지] {msg_text}", worker_name="owner")
            sent += 1
        print_system(f"전체 공지 발송: {sent}명")
        return

    if text.lower() == "/refresh":
        _contacts[:] = get_all_contacts()
        print_system(f"연락처 새로고침: {len(_contacts)}명")
        return

    if text.lower() in ('/help', '/h', '/?'):
        draw_help()
        return

    if text.lower() == "/clear":
        clear_screen()
        draw_header()
        draw_contact_bar()
        draw_help()
        return

    if text.lower() in ('/q', '/quit', '/exit'):
        global _running
        _running = False
        return

    # ── 이름>메시지 — 특정인에게 전송 ──
    for sep in [">", ":"]:
        if sep in text:
            name_part, body = text.split(sep, 1)
            name_part = name_part.strip()
            body = body.strip()
            if name_part and body:
                found = find_contact(name_part)
                if found:
                    _current_target = found
                    ok = send_telegram(found["chat_id"], body)
                    print_outgoing(found["name"], body, ok)
                    if ok:
                        save_message(chat_id=found["chat_id"],
                                     direction="outgoing", message=body,
                                     worker_name="owner")
                    return

    # ── 일반 메시지 — 현재 대화 상대에게 ──
    if not _current_target:
        print_system("대화 상대를 먼저 선택하세요: /번호 또는 /to 이름")
        return

    ok = send_telegram(_current_target["chat_id"], text)
    print_outgoing(_current_target["name"], text, ok)
    if ok:
        save_message(chat_id=_current_target["chat_id"],
                     direction="outgoing", message=text,
                     worker_name="owner")


# ── 메인 ──────────────────────────────────
def main():
    global _running

    if not TG_TOKEN:
        print("TELEGRAM_BOT_TOKEN 미설정")
        sys.exit(1)

    # ANSI 색상 활성화 (Windows 10+)
    if os.name == 'nt':
        os.system('')

    # 연락처 로드
    _contacts[:] = get_all_contacts()

    # 기존 메시지 건너뛰기
    offset_holder = [0]
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates",
            params={"offset": -1, "timeout": 0}, timeout=10,
        )
        if r.ok and r.json().get("result"):
            offset_holder[0] = r.json()["result"][-1]["update_id"] + 1
    except Exception:
        pass

    # 수신 폴링 스레드 시작
    poll_thread = threading.Thread(target=poll_incoming, args=(offset_holder,), daemon=True)
    poll_thread.start()

    # ── 초기 화면 ──
    clear_screen()
    draw_header()

    if not _contacts:
        print(f"  {RED}등록된 연락처가 없습니다.{RESET}")
        print("  텔레그램에서 봇에게 /start 를 보내면 등록됩니다.\n")
    else:
        draw_contact_bar()
        print()
        draw_help()

        # 최근 대화 통합 표시
        load_recent_all(15)

        # 연결 알림
        try:
            ts = datetime.now(KST).strftime("%H:%M")
            for c in _contacts:
                send_telegram(c["chat_id"],
                    f"💬 채팅 터미널 온라인 ({ts} KST)")
        except Exception:
            pass

    # ── 입력 루프 ──
    try:
        while _running:
            try:
                # 프롬프트에 현재 대화 상대 표시
                if _current_target:
                    color = get_color_for(_current_target["chat_id"])
                    prompt = f" {color}{_current_target['name']}{RESET} {CYAN}▸{RESET} "
                else:
                    prompt = f" {DIM}(상대 선택: /번호){RESET} {CYAN}▸{RESET} "
                line = input(prompt)
                handle_input(line)
            except EOFError:
                break
            except KeyboardInterrupt:
                break
    except KeyboardInterrupt:
        pass
    finally:
        _running = False
        # 오프라인 알림
        try:
            for c in _contacts:
                send_telegram(c["chat_id"], "💬 채팅 터미널 오프라인")
        except Exception:
            pass
        print(f"\n{DIM}[{ts_now()}] 다중 채팅 터미널 종료{RESET}")


if __name__ == "__main__":
    main()
