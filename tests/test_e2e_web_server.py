#!/usr/bin/env python3
"""E2E 검증 — scripts/web_server.py (E5팀)

`scripts.web_server`는 stdlib `http.server.BaseHTTPRequestHandler` 기반이므로
FastAPI/Flask TestClient 대신, 요청을 위조(fake request/response stream)하여
핸들러를 직접 호출한다. 실제 포트 바인딩은 하지 않는다.

검증 범위:
  1) /health 등 기본 라우트(루트) 응답이 200
  2) 인증 활성 상태에서 토큰 없으면 401
  3) 올바른 토큰이면 200
"""

from __future__ import annotations

import http.client
import importlib
import io
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# hide_console 는 web_server 가 최상단에서 import 한다 — Windows 외 환경 대비 stub.
sys.modules.setdefault("hide_console", MagicMock(subprocess_kwargs=lambda: {}))


def _load_web_server(auth_token: str = ""):
    """scripts.web_server 를 주어진 WEB_AUTH_TOKEN 환경에서 리로드한다."""
    if auth_token:
        os.environ["WEB_AUTH_TOKEN"] = auth_token
    else:
        os.environ.pop("WEB_AUTH_TOKEN", None)
    with patch("dotenv.load_dotenv"):
        with patch.object(sys.stdout, "reconfigure", create=True), \
             patch.object(sys.stderr, "reconfigure", create=True):
            if "scripts.web_server" in sys.modules:
                importlib.reload(sys.modules["scripts.web_server"])
            else:
                import scripts.web_server  # noqa: F401
    return sys.modules["scripts.web_server"]


class _FakeRequest(io.BytesIO):
    def makefile(self, *args, **kwargs):
        return self


def _build_handler(mod, method: str, path: str, body: bytes = b"", extra_headers=None):
    """실제 소켓 없이 DashboardHandler 인스턴스를 만들어 준비한다."""
    Handler = mod.DashboardHandler
    with patch.object(Handler, "__init__", lambda self, *a, **kw: None):
        h = Handler()
    h.client_address = ("127.0.0.1", 11111)
    h.server = MagicMock()
    h.request = _FakeRequest(b"")
    h.rfile = io.BytesIO(body)
    h.wfile = io.BytesIO()
    h.requestline = f"{method} {path} HTTP/1.1"
    h.command = method
    h.path = path
    h.headers = http.client.HTTPMessage()
    if method == "POST":
        h.headers["Content-Length"] = str(len(body))
        h.headers["Content-Type"] = "application/json"
    if extra_headers:
        for k, v in extra_headers.items():
            h.headers[k] = v
    h.close_connection = True
    h._headers_buffer = []
    # BaseHTTPRequestHandler.send_response_only 가 참조하는 속성들
    h.request_version = "HTTP/1.1"
    h.protocol_version = "HTTP/1.1"
    return h


def _parse_wfile(wfile: io.BytesIO):
    """BaseHTTPRequestHandler 가 wfile 에 쓴 HTTP 응답을 파싱해 (status, body) 반환."""
    raw = wfile.getvalue()
    if not raw:
        return None, b""
    # 첫 줄: HTTP/1.0 CODE REASON
    try:
        status_line, rest = raw.split(b"\r\n", 1)
        parts = status_line.split(b" ", 2)
        status = int(parts[1])
    except Exception:
        return None, raw
    # 헤더/바디 분리
    if b"\r\n\r\n" in rest:
        _, body = rest.split(b"\r\n\r\n", 1)
    else:
        body = b""
    return status, body


# ════════════════════════════════════════════════════════════
# 1. health/root 엔드포인트 (AUTH 비활성)
# ════════════════════════════════════════════════════════════

class TestHealthEndpoint:
    """루트(/) 는 index.html 로 리라이트 된다 — 정적 파일 서빙으로 200 응답."""

    def test_root_serves_index_when_file_exists(self, tmp_path):
        mod = _load_web_server(auth_token="")
        # WEB_DIR 를 tmp_path 로 치환하고 index.html 생성
        index_html = tmp_path / "index.html"
        index_html.write_text("<html>OK</html>", encoding="utf-8")

        h = _build_handler(mod, "GET", "/")
        # 핸들러가 WEB_DIR 대신 tmp_path 에서 파일을 찾도록 directory 재바인딩
        h.directory = str(tmp_path)

        # SimpleHTTPRequestHandler 의 translate_path 가 self.directory 를 쓰므로 ok
        with patch.object(mod, "WEB_DIR", tmp_path):
            h.do_GET()

        status, body = _parse_wfile(h.wfile)
        assert status == 200
        assert b"OK" in body

    def test_api_status_returns_200_when_no_auth(self):
        """/api/status 는 인증 비활성 시 바로 JSON 응답."""
        mod = _load_web_server(auth_token="")
        h = _build_handler(mod, "GET", "/api/status")
        # read_env/_get_active_strategy 의존성은 실제 호출 허용 (프로젝트 루트 .env 있음)
        captured = {}

        def capture(data, code=200):
            captured["code"] = code
            captured["data"] = data

        h._json_response = capture
        h.do_GET()
        assert captured.get("code") == 200
        assert "dry_run" in captured["data"]

    def test_unknown_api_returns_404(self):
        mod = _load_web_server(auth_token="")
        h = _build_handler(mod, "GET", "/api/does-not-exist")
        captured = {}
        h._json_response = lambda data, code=200: captured.update(code=code, data=data)
        h.do_GET()
        assert captured["code"] == 404
        assert captured["data"]["error"] == "not found"


# ════════════════════════════════════════════════════════════
# 2. 인증 필요한 라우트 — 토큰 없으면 401
# ════════════════════════════════════════════════════════════

class TestAuthRequiredRoutes:
    def test_missing_token_returns_401_on_api(self):
        mod = _load_web_server(auth_token="SECRET-123")
        assert mod.AUTH_ENABLED is True

        h = _build_handler(mod, "GET", "/api/status")
        h.do_GET()
        status, body = _parse_wfile(h.wfile)
        assert status == 401
        payload = json.loads(body.decode("utf-8"))
        assert payload["error"] == "unauthorized"

    def test_wrong_token_returns_401(self):
        mod = _load_web_server(auth_token="SECRET-123")
        h = _build_handler(mod, "GET", "/api/status?token=WRONG")
        h.do_GET()
        status, body = _parse_wfile(h.wfile)
        assert status == 401

    def test_wrong_bearer_header_returns_401(self):
        mod = _load_web_server(auth_token="SECRET-123")
        h = _build_handler(mod, "GET", "/api/portfolio",
                           extra_headers={"Authorization": "Bearer WRONG"})
        h.do_GET()
        status, _ = _parse_wfile(h.wfile)
        assert status == 401

    def test_post_without_token_returns_401(self):
        mod = _load_web_server(auth_token="SECRET-123")
        h = _build_handler(mod, "POST", "/api/emergency-stop", body=b"{}")
        h.do_POST()
        status, _ = _parse_wfile(h.wfile)
        assert status == 401

    def test_qr_html_exempt_from_auth(self):
        """/qr.html 은 AUTH_EXEMPT_PATHS 에 포함 — 토큰 없어도 통과해야 한다."""
        mod = _load_web_server(auth_token="SECRET-123")
        assert "/qr.html" in mod.AUTH_EXEMPT_PATHS
        h = _build_handler(mod, "GET", "/qr.html")
        # static 파일 없어도 auth 체크는 통과 — _check_auth() 가 False 여야 함
        assert h._check_auth() is False


# ════════════════════════════════════════════════════════════
# 3. 올바른 토큰 → 200
# ════════════════════════════════════════════════════════════

class TestAuthValidToken:
    def test_valid_query_token_allows_access(self):
        mod = _load_web_server(auth_token="SECRET-123")
        h = _build_handler(mod, "GET", "/api/status?token=SECRET-123")
        captured = {}
        h._json_response = lambda data, code=200: captured.update(code=code, data=data)
        h.do_GET()
        assert captured["code"] == 200
        assert "dry_run" in captured["data"]

    def test_valid_bearer_header_allows_access(self):
        mod = _load_web_server(auth_token="SECRET-123")
        h = _build_handler(mod, "GET", "/api/status",
                           extra_headers={"Authorization": "Bearer SECRET-123"})
        captured = {}
        h._json_response = lambda data, code=200: captured.update(code=code, data=data)
        h.do_GET()
        assert captured["code"] == 200

    def test_valid_token_post_emergency_stop(self, tmp_path, monkeypatch):
        """POST /api/emergency-stop — 토큰 OK 시 .env 토글 후 200."""
        mod = _load_web_server(auth_token="SECRET-123")
        # .env 쓰기를 tmp_path 로 격리
        env_file = tmp_path / ".env"
        env_file.write_text("EMERGENCY_STOP=false\n", encoding="utf-8")
        monkeypatch.setattr(mod, "PROJECT_DIR", tmp_path)
        monkeypatch.setenv("EMERGENCY_STOP", "false")

        h = _build_handler(mod, "POST", "/api/emergency-stop?token=SECRET-123", body=b"{}")
        captured = {}
        h._json_response = lambda data, code=200: captured.update(code=code, data=data)
        h.do_POST()
        assert captured["code"] == 200
        assert captured["data"]["emergency_stop"] == "true"


# ════════════════════════════════════════════════════════════
# 4. E2E 통합 — 종단 요청 플로우
# ════════════════════════════════════════════════════════════

class TestE2EFlow:
    def test_auth_flow_round_trip(self):
        """401 → 토큰 포함 → 200 까지 전체 플로우."""
        mod = _load_web_server(auth_token="TOP-SECRET")

        # 1. 토큰 없이 요청 → 401
        h1 = _build_handler(mod, "GET", "/api/status")
        h1.do_GET()
        s1, _ = _parse_wfile(h1.wfile)
        assert s1 == 401

        # 2. 올바른 토큰 → 200
        h2 = _build_handler(mod, "GET", "/api/status?token=TOP-SECRET")
        captured = {}
        h2._json_response = lambda data, code=200: captured.update(code=code, data=data)
        h2.do_GET()
        assert captured["code"] == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
