"""core/brain/llm_provider.py — LLM Provider 추상화 + Router.

제공자:
  OllamaQwenProvider  — quick tier, qwen3-coder, localhost:11434
  ClaudeProvider      — deep tier, Max OAuth (~/.claude/.credentials.json)
  GeminiProvider      — 호환 폴백(기존 gemini_client 인터페이스 유지)

LLMRouter: 평상시=quick(Qwen), 트리거 조건=deep(Claude).
  트리거: 급락(price_change_24h <= -5%), 레짐전환(regime_switch=True), 고위험 신호.

SACRED: DRY_RUN 기본값·coin 라이브 경로 미변경. API key(sk-ant-api) 사용 금지.
reuse: TradingAgents llm 호출 패턴 참조.
"""

from __future__ import annotations

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger("brain.llm_provider")

# ── 환경설정 기본값 ──────────────────────────────────────────────────

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3-coder-fast")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-7")
GEMINI_MODEL = os.environ.get("GEMINI_ANALYSIS_MODEL", "gemini-2.5-flash")

_CREDENTIALS_PATH = Path(os.path.expanduser("~/.claude/.credentials.json"))


def _load_oauth_token() -> str:
    """~/.claude/.credentials.json 에서 claudeAiOauth.accessToken 로드.

    API key(sk-ant-api) 사용 금지 — OAuth만 허용.
    """
    try:
        with open(_CREDENTIALS_PATH, encoding="utf-8") as f:
            d = json.load(f)
        token = d.get("claudeAiOauth", {}).get("accessToken", "")
        if not token:
            raise ValueError("claudeAiOauth.accessToken not found in credentials")
        if token.startswith("sk-ant-api"):
            raise ValueError("API key (sk-ant-api) 는 사용 금지. OAuth token 만 허용.")
        return token
    except FileNotFoundError:
        raise FileNotFoundError(f"credentials 파일 없음: {_CREDENTIALS_PATH}")


# ── ABC ──────────────────────────────────────────────────────────────

class LLMProvider(ABC):
    """LLM 제공자 공통 추상 기반."""

    @property
    @abstractmethod
    def tier(self) -> str:
        """'quick' | 'deep' | 'fallback'"""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """프롬프트를 받아 텍스트 응답 반환."""


# ── OllamaQwenProvider ────────────────────────────────────────────────

class OllamaQwenProvider(LLMProvider):
    """quick tier — ollama qwen3-coder, HTTP localhost:11434.

    POST /api/generate (stream=false) 방식 사용.
    """

    def __init__(
        self,
        base_url: str = OLLAMA_URL,
        model: str = OLLAMA_MODEL,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    @property
    def tier(self) -> str:
        return "quick"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        import urllib.request  # noqa: PLC0415

        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.0),
                "num_predict": kwargs.get("max_tokens", 512),
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        timeout = kwargs.get("timeout", 60)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result.get("response", "")


# ── ClaudeProvider ───────────────────────────────────────────────────

class ClaudeProvider(LLMProvider):
    """deep tier — Claude Max OAuth (~/.claude/.credentials.json).

    anthropic SDK Anthropic(api_key=oauth_token) 사용.
    API key(sk-ant-api) 금지.
    """

    def __init__(self, model: str = CLAUDE_MODEL) -> None:
        self._model = model
        self._token: str | None = None

    def _get_token(self) -> str:
        if self._token is None:
            self._token = _load_oauth_token()
        return self._token

    @property
    def tier(self) -> str:
        return "deep"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        import urllib.request  # noqa: PLC0415

        token = self._get_token()
        # OAuth token → Authorization: Bearer (anthropic SDK 는 x-api-key 로 덮어써서 직접 HTTP 사용)
        payload = {
            "model": self._model,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": prompt}],
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        timeout = kwargs.get("timeout", 60)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        content = result.get("content", [])
        return content[0].get("text", "") if content else ""


# ── GeminiProvider ───────────────────────────────────────────────────

class GeminiProvider(LLMProvider):
    """fallback tier — 기존 GeminiClient 인터페이스 호환 폴백.

    GEMINI_API_KEY 환경변수 필요. .env 없으면 초기화 실패 → mock 대체.
    """

    def __init__(self, model: str = GEMINI_MODEL) -> None:
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from rl_hybrid.rag.gemini_client import GeminiClient  # noqa: PLC0415
            self._client = GeminiClient()
        return self._client

    @property
    def tier(self) -> str:
        return "fallback"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        client = self._get_client()
        return client.analyze(prompt)


# ── LLMRouter ────────────────────────────────────────────────────────

class LLMRouter:
    """평상시=quick(Qwen), 트리거=deep(Claude) 라우팅.

    트리거 조건 (any):
      - price_change_24h <= TRIGGER_CRASH_PCT (기본 -5%)
      - regime_switch=True
      - high_risk=True
    """

    TRIGGER_CRASH_PCT: float = float(os.environ.get("LLM_TRIGGER_CRASH_PCT", "-5.0"))

    def __init__(
        self,
        quick: LLMProvider | None = None,
        deep: LLMProvider | None = None,
    ) -> None:
        self._quick: LLMProvider = quick or OllamaQwenProvider()
        self._deep: LLMProvider = deep or ClaudeProvider()

    def _is_triggered(
        self,
        price_change_24h: float = 0.0,
        regime_switch: bool = False,
        high_risk: bool = False,
    ) -> bool:
        if price_change_24h <= self.TRIGGER_CRASH_PCT:
            return True
        if regime_switch:
            return True
        if high_risk:
            return True
        return False

    def route(
        self,
        prompt: str,
        *,
        price_change_24h: float = 0.0,
        regime_switch: bool = False,
        high_risk: bool = False,
        **kwargs: Any,
    ) -> tuple[str, str]:
        """(응답 텍스트, 사용된 tier) 반환."""
        triggered = self._is_triggered(price_change_24h, regime_switch, high_risk)
        provider = self._deep if triggered else self._quick
        tier = provider.tier
        logger.debug("LLMRouter: tier=%s triggered=%s", tier, triggered)
        response = provider.generate(prompt, **kwargs)
        return response, tier

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """tier 무관 단순 응답 반환 (기본=quick)."""
        response, _ = self.route(prompt, **kwargs)
        return response
