#!/usr/bin/env python3
"""
텔레그램 채팅 터미널 (Interactive UI)

시작 시 연락처 목록을 표시하고 번호로 대화 상대를 선택한다.
선택 후 바로 채팅 모드로 진입하여 메시지를 주고받는다.

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

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
load_dotenv(PROJECT_DIR / ".env")

KST = timezone(timedelta(hours=9))
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OWNER_CHAT_ID = os.getenv("TELEGRAM_USER_ID", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

POLL_INTERVAL = 2
_running = True
_current_target: dict | None = None

# ── 색상 (Windows 터미널 ANSI) ──────────────────
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
RED     = "\033[91m"
DIM     = "\033[90m"
BOLD    = "\033[1m"
RESET   = "\033[0m"


def ts_now() -> str:
    return datetime.now(KST).strftime("%H:%M:%S")


# ── DB 연락처 ──────────────────────────────────
def get_all_contacts() -> list:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/telegram_contacts",
        params={"select": "chat_id,name,role,aliases",
                "is_active": "eq.true",
                "order": "role.asc,name.asc"},
        headers=HEADERS, timeout=10,
    )
    return resp.json() if resp.ok else []


def save_message(chat_id, direction, message, **kwargs):
    data = {"chat_id": chat_id, "direction": direction, "message": message}
    data.update({k: v for k, v in kwargs.items() if v is not None})
    try:
        requests.post(
            f"{SUPABASE_URL}/rest/v1/telegram_messages",
            json=data,
            headers={**HEADERS, "Prefer": "return=minimal"},
            timeout=10,
        )
    except Exception:
        pass


def send_telegram(chat_id: str, text: str) -> bool:
    r = requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=15,
    )
    return r.ok


def lookup_by_chat_id(chat_id: str) -> dict | None:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/telegram_contacts",
        params={"select": "chat_id,name,role,aliases",
                "chat_id": f"eq.{chat_id}", "is_active": "eq.true"},
        headers=HEADERS, timeout=10,
    )
    if resp.ok and resp.json():
        return resp.json()[0]
    return None


# ── 화면 그리기 ──────────────────────────────────
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def draw_header():
    print(f"{BOLD}{CYAN}")
    print("╔═══════════════════════════════════════════════╗")
    print("║         💬 텔레그램 채팅 터미널               ║")
    print("╚═══════════════════════════════════════════════╝")
    print(f"{RESET}")


def draw_contact_list(contacts: list):
    print(f"{BOLD} 대화 상대를 선택하세요:{RESET}")
    print(f"{DIM} {'─' * 45}{RESET}")
    for i, c in enumerate(contacts, 1):
        role_color = GREEN if c["role"] == "owner" else YELLOW
        role_icon = "👑" if c["role"] == "owner" else "👤"
        aliases = c.get("aliases") or []
        alias_str = f" {DIM}({', '.join(aliases)}){RESET}" if aliases else ""
        print(f"  {BOLD}{CYAN}[{i}]{RESET} {role_icon} {c['name']}{alias_str}  {role_color}[{c['role']}]{RESET}")
    print(f"{DIM} {'─' * 45}{RESET}")
    print(f"  {BOLD}{MAGENTA}[0]{RESET} 전체 공지 (브로드캐스트)")
    print(f"  {BOLD}{RED}[q]{RESET} 종료")
    print()


def draw_chat_header(target: dict):
    name = target["name"]
    role = target["role"]
    print(f"\n{DIM}{'─' * 50}{RESET}")
    print(f" {BOLD}💬 {name}{RESET} {DIM}[{role}]{RESET} 과(와) 대화 중")
    print(f" {DIM}메시지 입력 후 Enter | /back 목록 | /q 종료{RESET}")
    print(f"{DIM}{'─' * 50}{RESET}\n")


def print_incoming(sender_name: str, text: str):
    ts = ts_now()
    print(f" {DIM}[{ts}]{RESET} {GREEN}{BOLD}{sender_name}{RESET}: {text}", flush=True)


def print_outgoing(target_name: str, text: str, ok: bool):
    ts = ts_now()
    status = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
    print(f" {DIM}[{ts}]{RESET} {CYAN}나 → {target_name}{RESET}: {text}  {status}", flush=True)


def print_system(msg: str):
    ts = ts_now()
    print(f" {DIM}[{ts}] {YELLOW}ℹ {msg}{RESET}", flush=True)


# ── 수신 폴링 스레드 ──────────────────────────────
def poll_incoming(offset_holder: list):
    """백그라운드에서 텔레그램 메시지를 수신하여 콘솔에 표시"""
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
                else:
                    # 콘솔 출력
                    print_incoming(sender_name, text)

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
            target = None
            for c in get_all_contacts():
                if c["name"] == target_name or target_name in (c.get("aliases") or []):
                    target = c
                    break
            if target:
                forward = f"[{sender['name']}] {msg_text}"
                ok = send_telegram(target["chat_id"], forward)
                if ok:
                    send_telegram(chat_id, f"✓ {target['name']}에게 전송")
                    save_message(chat_id=target["chat_id"], direction="incoming",
                                 message=forward, worker_name=sender["name"])
                    print_incoming(sender["name"], f"→ {target['name']}: {msg_text}")
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


# ── 메인 ──────────────────────────────────
def main():
    global _running, _current_target

    if not TG_TOKEN:
        print("TELEGRAM_BOT_TOKEN 미설정")
        sys.exit(1)

    # ANSI 색상 활성화 (Windows 10+)
    if os.name == 'nt':
        os.system('')

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

    try:
        while _running:
            # ── 연락처 목록 화면 ──
            clear_screen()
            draw_header()

            contacts = get_all_contacts()
            if not contacts:
                print(f"  {RED}등록된 연락처가 없습니다.{RESET}")
                print(f"  텔레그램에서 봇에게 /start 를 보내면 등록됩니다.")
                input(f"\n  Enter로 새로고침...")
                continue

            draw_contact_list(contacts)

            try:
                choice = input(f"  {BOLD}선택 ▸ {RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if choice.lower() in ('q', 'quit', 'exit'):
                break

            # 전체 공지
            if choice == '0':
                try:
                    msg = input(f"  {MAGENTA}공지 메시지 ▸ {RESET}").strip()
                except (EOFError, KeyboardInterrupt):
                    continue
                if msg:
                    sent = 0
                    for c in contacts:
                        send_telegram(c["chat_id"], f"[공지] {msg}")
                        save_message(chat_id=c["chat_id"], direction="outgoing",
                                     message=f"[공지] {msg}", worker_name="owner")
                        sent += 1
                    print(f"\n  {GREEN}✓ {sent}명에게 공지 발송 완료{RESET}")
                    time.sleep(1.5)
                continue

            # 번호로 선택
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(contacts):
                    _current_target = contacts[idx]
                else:
                    print(f"  {RED}잘못된 번호입니다.{RESET}")
                    time.sleep(1)
                    continue
            except ValueError:
                # 이름으로 검색
                found = None
                for c in contacts:
                    if choice in c["name"] or choice in (c.get("aliases") or []):
                        found = c
                        break
                if found:
                    _current_target = found
                else:
                    print(f"  {RED}'{choice}' 을(를) 찾을 수 없습니다.{RESET}")
                    time.sleep(1)
                    continue

            # ── 채팅 모드 ──
            clear_screen()
            draw_header()
            draw_chat_header(_current_target)

            # 최근 메시지 불러오기
            _load_recent_messages(_current_target["chat_id"])

            while _running:
                try:
                    msg = input(f" {CYAN}▸ {RESET}")
                except (EOFError, KeyboardInterrupt):
                    _running = False
                    break

                msg = msg.strip()
                if not msg:
                    continue

                if msg.lower() in ('/back', '/b', '/목록'):
                    break

                if msg.lower() in ('/q', '/quit', '/exit'):
                    _running = False
                    break

                if msg.lower() == '/clear':
                    clear_screen()
                    draw_header()
                    draw_chat_header(_current_target)
                    continue

                if msg.lower() == '/recent':
                    _load_recent_messages(_current_target["chat_id"])
                    continue

                # 메시지 전송
                ok = send_telegram(_current_target["chat_id"], msg)
                print_outgoing(_current_target["name"], msg, ok)
                if ok:
                    save_message(chat_id=_current_target["chat_id"],
                                 direction="outgoing", message=msg,
                                 worker_name="owner")

    except KeyboardInterrupt:
        pass
    finally:
        _running = False
        print(f"\n{DIM}[{ts_now()}] 채팅 터미널 종료{RESET}")


def _load_recent_messages(chat_id: str, limit: int = 10):
    """최근 대화 내역 불러오기"""
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/telegram_messages",
            params={
                "select": "direction,message,created_at,worker_name",
                "chat_id": f"eq.{chat_id}",
                "order": "created_at.desc",
                "limit": str(limit),
            },
            headers=HEADERS, timeout=10,
        )
        if not resp.ok or not resp.json():
            print(f" {DIM}(이전 대화 없음){RESET}\n", flush=True)
            return

        messages = list(reversed(resp.json()))
        print(f" {DIM}── 최근 {len(messages)}건 ──{RESET}")
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
                print(f" {DIM}[{ts}]{RESET} {GREEN}{name}{RESET}: {text}")
            else:
                print(f" {DIM}[{ts}]{RESET} {CYAN}나{RESET}: {text}")
        print(f" {DIM}{'─' * 40}{RESET}\n")

    except Exception as e:
        print(f" {DIM}(대화 내역 로드 실패: {e}){RESET}\n", flush=True)


if __name__ == "__main__":
    main()
