"""core/brain/llm_provider.py — LLM Provider 추상화 + Router.

제공자:
  OllamaQwenProvider  — quick tier, qwen3-coder, localhost:11434
  ClaudeProvider      — deep tier, Max OAuth (~/.claude/.credentials.json)
  GeminiProvider      — 호환 폴백(기존 gemini_client 인터페이스 유지)

LLMRouter: 평상시=quick(Qwen), 트리거 조건=deep(Claude).
  트리거: 급락(price_change_24h <= -5%), 레짐전환(regime_switch=True), 고위험 신호.

C2 서킷브레이커 (Phase 2.5):
  - 일일 호출 캡(LLM_DAILY_CAP, 기본 9999=비활성) — 실운용 시 .env 에 LLM_DAILY_CAP=24 설정 필수.
    KST 날짜 기준, data/llm_daily_counter.json 영속
  - 지연 예산(LLM_LATENCY_BUDGET, 기본 30s) — 초과 시 degrade
  - provider 예외 catch → degrade(reason 태깅)
  - degrade 사유: cap/latency/error(resource) vs quality(품질붕괴)
  - 풀 reserve/retry/3버킷 = Phase 6

B3 결정성 (Phase 2.5):
  - model_id·prompt_hash·temperature RouteResult 채움
  - route_with_meta() 신설, route() = 위임 (2-tuple 계약 보존)

SACRED: DRY_RUN 기본값·coin 라이브 경로 미변경. API key(sk-ant-api) 사용 금지.
reuse: TradingAgents llm 호출 패턴 · gemini_client.py:40-176 C2 원본 패턴.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("brain.llm_provider")

# ── 환경설정 기본값 ──────────────────────────────────────────────────

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3-coder-fast")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-7")
GEMINI_MODEL = os.environ.get("GEMINI_ANALYSIS_MODEL", "gemini-2.5-flash")

# C2 서킷브레이커 설정 (gemini_client.py config 패턴 동일)
# LLM_DAILY_CAP: 기본 9999(비활성) — 실 운용 시 .env 에서 24 등으로 낮춰 설정
LLM_DAILY_CAP      = int(os.environ.get("LLM_DAILY_CAP", "9999"))
LLM_LATENCY_BUDGET = float(os.environ.get("LLM_LATENCY_BUDGET", "30.0"))
LLM_TEMPERATURE    = float(os.environ.get("LLM_TEMPERATURE", "0.0"))

_CREDENTIALS_PATH = Path(os.path.expanduser("~/.claude/.credentials.json"))

# C2 카운터 파일 (gemini_client.py:41-43 패턴, 별도 파일로 분리)
_LLM_COUNTER_FILE = Path(
    os.environ.get("PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
) / "data" / "llm_daily_counter.json"


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


# ── RouteResult (B3 결정성 + C2 메타) ───────────────────────────────

@dataclass
class RouteResult:
    """route_with_meta() 반환값 — B3 결정성 + C2 degrade 정보."""
    text: str
    tier: str              # 실제 응답 tier (degrade 시 "degraded")
    model_id: str = ""
    prompt_hash: str = ""
    temperature: float = LLM_TEMPERATURE
    degraded: bool = False
    degrade_reason: str = ""   # cap | latency | error | quality
    intended_tier: str = ""    # 라우팅 결정 tier(quick/deep) — route() 2-tuple 계약용


# ── C2 카운터 유틸 (gemini_client.py:48-91 패턴 이식) ───────────────

def _kst_today() -> str:
    from datetime import datetime, timezone, timedelta  # noqa: PLC0415
    KST = timezone(timedelta(hours=9))
    return datetime.now(KST).strftime("%Y-%m-%d")


def _load_c2_counter(counter_file: Path) -> tuple[str, int]:
    """(today_str, count) 반환."""
    today = _kst_today()
    try:
        if counter_file.exists():
            data = json.loads(counter_file.read_text(encoding="utf-8"))
            if data.get("date") == today:
                return today, int(data.get("count", 0))
    except Exception:
        pass
    return today, 0


def _save_c2_counter(counter_file: Path, today: str, count: int) -> None:
    try:
        counter_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = counter_file.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"date": today, "count": count}, ensure_ascii=False),
            encoding="utf-8",
        )
        import os as _os  # noqa: PLC0415
        _os.replace(str(tmp), str(counter_file))
    except Exception as e:
        logger.debug("C2 카운터 저장 실패: %s", e)


def _increment_c2_counter(counter_file: Path, today: str, count: int) -> tuple[str, int]:
    """날짜 체크 후 카운터 +1 저장, (new_today, new_count) 반환."""
    now_today = _kst_today()
    if now_today != today:
        today, count = now_today, 0
    count += 1
    _save_c2_counter(counter_file, today, count)
    return today, count


# ── ABC ──────────────────────────────────────────────────────────────

class LLMProvider(ABC):
    """LLM 제공자 공통 추상 기반."""

    @property
    @abstractmethod
    def tier(self) -> str:
        """'quick' | 'deep' | 'fallback'"""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """B3 결정성: 모델 식별자 (예: 'qwen3-coder-fast', 'claude-opus-4-7')."""

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

    @property
    def model_id(self) -> str:
        return self._model

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

    @property
    def model_id(self) -> str:
        return self._model

    def generate(self, prompt: str, **kwargs: Any) -> str:
        import urllib.request  # noqa: PLC0415

        token = self._get_token()
        # OAuth token → Authorization: Bearer (anthropic SDK 는 x-api-key 로 덮어써서 직접 HTTP 사용)
        # B3 결정성: temperature payload 실주입 — 미주입 시 Anthropic 기본 1.0(비결정) → RouteResult 기록과 불일치
        payload = {
            "model": self._model,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "temperature": float(kwargs.get("temperature", LLM_TEMPERATURE)),
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

    @property
    def model_id(self) -> str:
        return self._model

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
        daily_cap: int = LLM_DAILY_CAP,
        latency_budget: float = LLM_LATENCY_BUDGET,
        counter_file: Path | None = None,
    ) -> None:
        self._quick: LLMProvider = quick or OllamaQwenProvider()
        self._deep: LLMProvider = deep or ClaudeProvider()
        self._daily_cap = daily_cap
        self._latency_budget = latency_budget
        self._counter_file: Path = counter_file or _LLM_COUNTER_FILE
        # C2 카운터 초기화 (gemini_client.py:44-46 패턴)
        self._c2_today, self._c2_count = _load_c2_counter(self._counter_file)

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
        """(응답 텍스트, 사용된 tier) 반환 — 2-tuple 계약 보존(기존 호출자 무수정).

        tier = 라우팅 결정 tier(quick/deep). degrade 여부와 무관하게
        _is_triggered 결과에 따른 원래 tier 를 반환(기존 테스트 무수정 조건).
        내부적으로 route_with_meta() 에 위임한다.
        """
        result = self.route_with_meta(
            prompt,
            price_change_24h=price_change_24h,
            regime_switch=regime_switch,
            high_risk=high_risk,
            **kwargs,
        )
        # degrade 시에도 의도한 provider tier(quick/deep) 반환 — 기존 계약 보존
        intended_tier = result.intended_tier if result.intended_tier else result.tier
        return result.text, intended_tier

    def route_with_meta(
        self,
        prompt: str,
        *,
        price_change_24h: float = 0.0,
        regime_switch: bool = False,
        high_risk: bool = False,
        **kwargs: Any,
    ) -> RouteResult:
        """C2 + B3 풀 RouteResult 반환.

        C2: 캡 초과 → degrade(reason=cap) / 지연 초과 → degrade(reason=latency) /
            예외 → degrade(reason=error|quality).
        B3: prompt_hash·model_id·temperature 채움.
        """
        # C2: 날짜 갱신 체크
        now_today = _kst_today()
        if now_today != self._c2_today:
            self._c2_today, self._c2_count = _load_c2_counter(self._counter_file)

        # 라우팅 결정 (캡 체크 전에 먼저 — intended_tier 확보용)
        triggered = self._is_triggered(price_change_24h, regime_switch, high_risk)
        provider = self._deep if triggered else self._quick
        tier = provider.tier  # intended_tier (quick/deep)

        # C2 ①: 캡 초과 → degrade (resource)
        if self._c2_count >= self._daily_cap:
            reason = f"일일 호출 캡 초과({self._c2_count}/{self._daily_cap})"
            logger.warning("C2 cap degrade: %s", reason)
            return self._degrade_result(prompt, "cap", kwargs, intended_tier=tier)
        temperature = float(kwargs.get("temperature", LLM_TEMPERATURE))
        # B3 결정성: temperature 를 kwargs 에 명시 보장 → provider.generate 에 실제 전달
        # (Claude payload 실주입 + Ollama options temperature 일관 적용)
        kwargs = {**kwargs, "temperature": temperature}

        # B3: prompt_hash
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()

        logger.debug("LLMRouter: tier=%s triggered=%s", tier, triggered)

        # C2 ②: 지연 예산 측정 + 예외 catch
        _call_start = time.time()
        try:
            response = provider.generate(prompt, **kwargs)
        except Exception as exc:
            reason = str(exc)[:120]
            # 모순1 최소훅: 429/timeout → resource, 나머지 → quality
            degrade_type = "error"
            if "429" in reason or "timeout" in reason.lower() or "connection" in reason.lower():
                degrade_type = "error"  # resource계열, 추후 Phase6 retry
            else:
                degrade_type = "quality"
            logger.warning("C2 provider exception → degrade(%s): %s", degrade_type, reason)
            return self._degrade_result(prompt, degrade_type, kwargs, prompt_hash=prompt_hash, model_id=getattr(provider, "model_id", tier), temperature=temperature, intended_tier=tier)

        _latency = time.time() - _call_start

        # C2 ③: 지연 초과 → degrade (resource)
        if _latency > self._latency_budget:
            logger.warning("C2 latency degrade: %.1fs > %.1fs", _latency, self._latency_budget)
            self._c2_today, self._c2_count = _increment_c2_counter(self._counter_file, self._c2_today, self._c2_count)
            return self._degrade_result(prompt, "latency", kwargs, prompt_hash=prompt_hash, model_id=getattr(provider, "model_id", tier), temperature=temperature, intended_tier=tier)

        # 정상 → 카운터 +1
        self._c2_today, self._c2_count = _increment_c2_counter(self._counter_file, self._c2_today, self._c2_count)

        return RouteResult(
            text=response,
            tier=tier,
            model_id=getattr(provider, "model_id", tier),
            prompt_hash=prompt_hash,
            temperature=temperature,
            degraded=False,
            degrade_reason="",
            intended_tier=tier,
        )

    def _degrade_result(
        self,
        prompt: str,
        reason: str,
        kwargs: dict[str, Any],
        prompt_hash: str = "",
        model_id: str = "degraded",
        temperature: float = LLM_TEMPERATURE,
        intended_tier: str = "",
    ) -> RouteResult:
        """H14: 매수 degrade = abstain(hold) 보수 — hold 의미 JSON 반환."""
        if not prompt_hash:
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        hold_text = json.dumps({
            "decision": "관망",
            "confidence": 0.0,
            "reason": f"C2 서킷브레이커 발동: {reason}",
            "market_regime": "unknown",
            "_c2_degraded": True,
            "_c2_reason": reason,
        }, ensure_ascii=False)
        return RouteResult(
            text=hold_text,
            tier="degraded",
            model_id=model_id,
            prompt_hash=prompt_hash,
            temperature=temperature,
            degraded=True,
            degrade_reason=reason,
            intended_tier=intended_tier,
        )

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """tier 무관 단순 응답 반환 (기본=quick)."""
        return self.route_with_meta(prompt, **kwargs).text

    def get_daily_call_count(self) -> int:
        """C2 일일 호출 카운트 반환 (모니터링용)."""
        now_today = _kst_today()
        if now_today != self._c2_today:
            self._c2_today, self._c2_count = _load_c2_counter(self._counter_file)
        return self._c2_count
