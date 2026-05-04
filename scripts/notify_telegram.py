#!/usr/bin/env python3
"""
텔레그램 알림 전송 스크립트

메시지 타입: trade, analysis, error, status
포맷: MarkdownV2

사용법:
  python3 scripts/notify_telegram.py trade "BTC 매수 실행" "10만원 매수, RSI 28"
  python3 scripts/notify_telegram.py error "데이터 수집 실패" "Upbit API 타임아웃"

출력: JSON (stdout)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
import requests

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TELEGRAM_API = "https://api.telegram.org/bot{token}"

EMOJI = {
    "trade": "\U0001f4b0",     # 💰
    "analysis": "\U0001f4ca",  # 📊
    "error": "\U0001f6a8",     # 🚨
    "status": "\U0001f4cb",    # 📋
}

KST = timezone(timedelta(hours=9))


def escape_md(text: str) -> str:
    """MarkdownV2 특수문자 이스케이프 (backslash를 먼저 이스케이프하여 이중 이스케이프 방지)"""
    text = text.replace("\\", "\\\\")
    return re.sub(r"([_*\[\]()~`>#+\-=|{}.!])", r"\\\1", text)


def _get_machine_tag() -> str:
    """머신 이름 태그를 반환한다."""
    try:
        from utils.machine import get_machine_name
        name = get_machine_name()
    except Exception:
        import platform
        name = platform.node().split(".")[0] or "unknown"
    return f"[{name}]"


def send_message(msg_type: str, title: str, body: str, max_retries: int = 3):
    import time
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    user_id = os.environ.get("TELEGRAM_USER_ID")
    if not bot_token or not user_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 또는 TELEGRAM_USER_ID 미설정")

    machine_tag = _get_machine_tag()
    ts = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")
    emoji = EMOJI.get(msg_type, "\U0001f4ac")
    text = f"{emoji} *{escape_md(title)}*\n\n{escape_md(body)}\n\n{escape_md(machine_tag)} _{escape_md(ts)}_"

    for attempt in range(max_retries):
        try:
            r = requests.post(
                f"{TELEGRAM_API.format(token=bot_token)}/sendMessage",
                json={
                    "chat_id": user_id,
                    "text": text,
                    "parse_mode": "MarkdownV2",
                },
                timeout=10,
            )
            if r.ok:
                return {"success": True, "type": msg_type, "title": title}
            if r.status_code == 400:
                # MarkdownV2 파싱 실패 — plain text로 재시도
                import re
                plain = re.sub(r'[_*\[\]()~`>#+\-=|{}.!\\]', '', text)
                r2 = requests.post(
                    f"{TELEGRAM_API.format(token=bot_token)}/sendMessage",
                    json={"chat_id": user_id, "text": plain},
                    timeout=10,
                )
                if r2.ok:
                    return {"success": True, "type": msg_type, "title": title, "fallback": "plain"}
                raise RuntimeError(f"텔레그램 전송 실패 (plain fallback도 실패): {r2.text}")
            if attempt < max_retries - 1 and (r.status_code >= 500 or r.status_code == 429):
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"텔레그램 전송 실패: {r.text}")
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError("텔레그램 전송 타임아웃 (재시도 소진)")


def send_photo(image_path: str, caption: str, max_retries: int = 3):
    import time
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    user_id = os.environ.get("TELEGRAM_USER_ID")
    if not bot_token or not user_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 또는 TELEGRAM_USER_ID 미설정")

    # 파일 존재 및 크기 검증 (텔레그램 sendPhoto 상한 10MB)
    img_path = Path(image_path)
    if not img_path.exists():
        raise FileNotFoundError(f"이미지 파일 없음: {image_path}")
    if not img_path.is_file():
        raise RuntimeError(f"이미지 경로가 파일이 아님: {image_path}")
    size_bytes = img_path.stat().st_size
    if size_bytes == 0:
        raise RuntimeError(f"이미지 파일 비어 있음: {image_path}")
    if size_bytes > 10 * 1024 * 1024:
        raise RuntimeError(
            f"이미지 파일 10MB 초과 ({size_bytes / (1024*1024):.1f}MB): {image_path}"
        )

    machine_tag = _get_machine_tag()
    caption = f"{caption}\n{machine_tag}"

    for attempt in range(max_retries):
        with open(image_path, "rb") as f:
            r = requests.post(
                f"{TELEGRAM_API.format(token=bot_token)}/sendPhoto",
                data={"chat_id": user_id, "caption": caption},
                files={"photo": ("chart.png", f, "image/png")},
                timeout=30,
            )

        if r.ok:
            return {"success": True, "type": "photo", "path": image_path}
        try:
            status = int(r.status_code)
        except (TypeError, ValueError):
            status = 0
        if attempt < max_retries - 1 and (status >= 500 or status == 429):
            time.sleep(2 ** attempt)
            continue
        raise RuntimeError(f"텔레그램 이미지 전송 실패: {r.text}")

    return {"success": True, "type": "photo", "path": image_path}


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(
            '사용법: python3 notify_telegram.py [trade|analysis|error|status] "제목" "본문"',
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        result = send_message(sys.argv[1], sys.argv[2], sys.argv[3])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        json.dump({"error": str(e)}, sys.stderr, ensure_ascii=False)
        sys.exit(1)
