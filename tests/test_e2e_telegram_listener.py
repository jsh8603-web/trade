#!/usr/bin/env python3
"""E2E 검증 — scripts/telegram_listener.py (E5팀)

통합 멀티챗 터미널의 메시지 디스패처를 단위 단위로 검증한다.
네트워크(requests), Supabase, 텔레그램 API 는 전부 mock.

검증 범위:
  1) DB 등록 사용자 메시지 수락 (handle_plain_message/handle_command)
  2) 미등록 사용자 거부 (sender=None 경로)
  3) /to 이름 — 기본 대상 설정
  4) 이름>메시지 — prefix 라우팅
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


@pytest.fixture
def tl(monkeypatch):
    """telegram_listener 모듈을 mock 환경에서 로드."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "srv-key")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")

    # nl_feedback 의존성 mock
    nl_stub = MagicMock()
    nl_stub.extract_feedback = MagicMock(return_value=None)
    nl_stub.save_feedback_to_db = MagicMock(return_value=True)
    monkeypatch.setitem(sys.modules, "scripts.nl_feedback", nl_stub)

    # stdout/stderr 를 buffer 속성 없는 객체로 위장 → 모듈 최상단 TextIOWrapper
    # 재할당 블록을 건너뛰게 한다 (pytest capture 충돌 방지).
    monkeypatch.setattr(sys, "stdout", io.StringIO())
    monkeypatch.setattr(sys, "stderr", io.StringIO())

    if "scripts.telegram_listener" in sys.modules:
        del sys.modules["scripts.telegram_listener"]
    import scripts.telegram_listener as _tl  # noqa: E402
    _tl._default_target = None
    return _tl


def _resp(ok=True, json_data=None):
    """requests.get/post mock 응답 팩토리."""
    m = MagicMock()
    m.ok = ok
    m.json = MagicMock(return_value=json_data if json_data is not None else [])
    return m


# ════════════════════════════════════════════════════════════
# 1. 등록된 사용자 메시지 수락
# ════════════════════════════════════════════════════════════

class TestRegisteredUserAccepted:
    def test_plain_message_routes_to_target(self, tl):
        """등록 발신자가 '이름>메시지' 형식으로 보낼 때 수신자로 전달."""
        sender = {"chat_id": "100", "name": "Jay", "role": "owner"}
        target_hit = [{"chat_id": "200", "name": "Son", "role": "collaborator"}]

        get_responses = [_resp(True, target_hit)]
        with patch("scripts.telegram_listener.requests.get",
                   side_effect=get_responses), \
             patch("scripts.telegram_listener.requests.post",
                   return_value=_resp(True, {"ok": True})), \
             patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send:
            tl.handle_plain_message("100", "Son>안녕", sender)

        # send_telegram 이 target 과 sender 둘 다에 호출되어야 함
        calls = mock_send.call_args_list
        assert any(c.args[0] == "200" and "[Jay] 안녕" in c.args[1] for c in calls), \
            "target 에게 forward 메시지가 전송되어야 한다"
        assert any(c.args[0] == "100" and "✓" in c.args[1] for c in calls), \
            "sender 에게 전송 성공 확인 메시지가 가야 한다"

    def test_command_list_accepted_for_registered(self, tl):
        """등록된 사용자는 /list 명령을 실행할 수 있다."""
        sender = {"chat_id": "100", "name": "Jay", "role": "owner"}
        contacts = [
            {"chat_id": "100", "name": "Jay", "role": "owner", "aliases": []},
            {"chat_id": "200", "name": "Son", "role": "collaborator", "aliases": ["아들"]},
        ]
        with patch("scripts.telegram_listener.requests.get",
                   return_value=_resp(True, contacts)), \
             patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send:
            handled = tl.handle_command("100", "/list", sender)

        assert handled is True
        mock_send.assert_called_once()
        _, text = mock_send.call_args.args
        assert "연락처 목록" in text
        assert "Jay" in text and "Son" in text

    def test_start_command_greets_registered_user_by_role(self, tl):
        sender = {"chat_id": "100", "name": "Jay", "role": "owner"}
        with patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send:
            handled = tl.handle_command("100", "/start", sender)

        assert handled is True
        _, text = mock_send.call_args.args
        assert "Jay" in text
        assert "owner" in text


# ════════════════════════════════════════════════════════════
# 2. 미등록 사용자 거부
# ════════════════════════════════════════════════════════════

class TestUnregisteredUserRejected:
    def test_plain_message_from_unregistered_is_rejected(self, tl):
        """sender=None → send_telegram 으로 등록 안내만 가고 포워딩 없음."""
        with patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send:
            tl.handle_plain_message("9999", "뭐든지", None)

        mock_send.assert_called_once()
        chat_id, text = mock_send.call_args.args
        assert chat_id == "9999"
        assert "등록되지 않은" in text
        assert "9999" in text  # chat_id 를 안내해야 한다

    def test_command_list_blocked_for_unregistered(self, tl):
        """/list 는 미등록자는 차단(return False)."""
        with patch("scripts.telegram_listener.send_telegram", return_value=True):
            handled = tl.handle_command("9999", "/list", None)
        assert handled is False

    def test_command_msg_blocked_for_unregistered(self, tl):
        with patch("scripts.telegram_listener.send_telegram", return_value=True):
            handled = tl.handle_command("9999", "/msg Jay 안녕", None)
        assert handled is False

    def test_unregistered_start_shows_chat_id_hint(self, tl):
        """미등록자의 /start 는 처리되지만 chat_id 안내만 전송."""
        with patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send:
            handled = tl.handle_command("9999", "/start", None)

        assert handled is True
        _, text = mock_send.call_args.args
        assert "9999" in text
        assert "관리자" in text

    def test_chat_id_command_works_without_registration(self, tl):
        """/chat_id 는 등록 여부와 무관하게 chat_id 를 반환."""
        with patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send:
            handled = tl.handle_command("9999", "/chat_id", None)

        assert handled is True
        _, text = mock_send.call_args.args
        assert "9999" in text


# ════════════════════════════════════════════════════════════
# 3. /to 이름 — 기본 대상 설정
# ════════════════════════════════════════════════════════════

class TestMultichatToCommand:
    def test_to_sets_default_target(self, tl, capsys):
        """/to 이름 → 이후 이름 없이 입력해도 해당 대상으로 전송."""
        son = {"chat_id": "200", "name": "Son", "role": "collaborator"}

        # lookup_by_name 이 Son 을 반환하도록 mock
        with patch("scripts.telegram_listener.lookup_by_name",
                   return_value=son):
            tl.handle_local_input("/to Son")

        assert tl._default_target == son

    def test_to_without_name_clears_target(self, tl):
        tl._default_target = {"chat_id": "200", "name": "Son", "role": "collaborator"}
        tl.handle_local_input("/to")
        assert tl._default_target is None

    def test_to_unknown_name_does_not_set_target(self, tl):
        tl._default_target = None
        with patch("scripts.telegram_listener.lookup_by_name", return_value=None):
            tl.handle_local_input("/to NOBODY")
        assert tl._default_target is None

    def test_plain_input_uses_default_target(self, tl):
        """/to 설정 후 일반 텍스트 입력 시 기본 대상으로 전송."""
        son = {"chat_id": "200", "name": "Son", "role": "collaborator"}
        tl._default_target = son

        with patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send, \
             patch("scripts.telegram_listener.save_message"):
            tl.handle_local_input("안녕하세요")

        mock_send.assert_called_once_with("200", "안녕하세요")

    def test_plain_input_without_default_target_shows_hint(self, tl, capsys):
        tl._default_target = None
        # lookup_by_name 호출되지 않아야 함 (separator 없으므로)
        with patch("scripts.telegram_listener.send_telegram") as mock_send:
            tl.handle_local_input("그냥 텍스트")
        mock_send.assert_not_called()


# ════════════════════════════════════════════════════════════
# 4. 이름>메시지 — prefix 라우팅
# ════════════════════════════════════════════════════════════

class TestNamePrefixRouting:
    def test_gt_separator_routes_to_named_target(self, tl):
        """로컬 입력 '이름>메시지' → 해당 대상에게 전송 + _default_target 갱신."""
        son = {"chat_id": "200", "name": "Son", "role": "collaborator"}

        with patch("scripts.telegram_listener.lookup_by_name",
                   return_value=son), \
             patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send, \
             patch("scripts.telegram_listener.save_message"):
            tl.handle_local_input("Son>안녕")

        mock_send.assert_called_once_with("200", "안녕")
        assert tl._default_target == son  # auto-update

    def test_colon_separator_also_routes(self, tl):
        son = {"chat_id": "200", "name": "Son", "role": "collaborator"}
        with patch("scripts.telegram_listener.lookup_by_name",
                   return_value=son), \
             patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send, \
             patch("scripts.telegram_listener.save_message"):
            tl.handle_local_input("Son: 안녕")

        mock_send.assert_called_once_with("200", "안녕")

    def test_prefix_with_unknown_name_falls_back_to_default(self, tl):
        """이름>메시지 에서 이름을 못 찾으면 기본 대상(없으면 힌트)."""
        tl._default_target = None
        with patch("scripts.telegram_listener.lookup_by_name", return_value=None), \
             patch("scripts.telegram_listener.send_telegram") as mock_send, \
             patch("scripts.telegram_listener.save_message"):
            tl.handle_local_input("UnknownName>메시지")
        mock_send.assert_not_called()

    def test_telegram_inbound_prefix_routing(self, tl):
        """텔레그램 쪽에서 들어온 '이름>메시지' 도 동일하게 포워딩."""
        sender = {"chat_id": "100", "name": "Jay", "role": "owner"}
        son = {"chat_id": "200", "name": "Son", "role": "collaborator"}

        with patch("scripts.telegram_listener.lookup_by_name",
                   return_value=son), \
             patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send, \
             patch("scripts.telegram_listener.save_message"):
            tl.handle_plain_message("100", "Son>반가워", sender)

        # target 으로 전달 + sender 에게 확인 메시지
        sent_to = [c.args[0] for c in mock_send.call_args_list]
        assert "200" in sent_to
        assert "100" in sent_to


# ════════════════════════════════════════════════════════════
# 5. E2E 통합 — 멀티챗 전체 플로우
# ════════════════════════════════════════════════════════════

class TestE2EMultichatFlow:
    def test_full_session_flow(self, tl):
        """로그인(start) → /list → /to Son → 기본 대상 전송 → 이름>메시지 전환"""
        jay = {"chat_id": "100", "name": "Jay", "role": "owner"}
        son = {"chat_id": "200", "name": "Son", "role": "collaborator"}
        jane = {"chat_id": "300", "name": "Jane", "role": "viewer"}
        contacts = [jay, son, jane]

        # 1. /start 수신자에게 인사
        with patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send:
            tl.handle_command("100", "/start", jay)
        assert "Jay" in mock_send.call_args.args[1]

        # 2. /list 는 등록된 연락처 반환
        with patch("scripts.telegram_listener.requests.get",
                   return_value=_resp(True, [
                       {**c, "aliases": []} for c in contacts])), \
             patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send:
            tl.handle_command("100", "/list", jay)
        assert "Son" in mock_send.call_args.args[1]

        # 3. /to Son — 기본 대상 설정
        with patch("scripts.telegram_listener.lookup_by_name",
                   return_value=son):
            tl.handle_local_input("/to Son")
        assert tl._default_target == son

        # 4. 기본 대상에게 일반 텍스트 전송
        with patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send, \
             patch("scripts.telegram_listener.save_message"):
            tl.handle_local_input("안녕 Son")
        mock_send.assert_called_once_with("200", "안녕 Son")

        # 5. Jane>…으로 대상 전환 → default 도 Jane 으로 변경
        with patch("scripts.telegram_listener.lookup_by_name",
                   return_value=jane), \
             patch("scripts.telegram_listener.send_telegram",
                   return_value=True) as mock_send, \
             patch("scripts.telegram_listener.save_message"):
            tl.handle_local_input("Jane>안녕")
        assert tl._default_target == jane
        mock_send.assert_called_once_with("300", "안녕")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
