"""core/assume/loop_factory.py — S4 능동루프 LLM 실배선 (발권 실연결 팩토리).

active_loop.ActiveAnalystLoop 는 macro_reasoning.LLMProvider Protocol(complete(system,user,json_mode))
을 기대하나, brain.llm_provider.OllamaQwenProvider 는 generate(prompt) 인터페이스 → 어댑터로 연결.

★발권 실연결(plan §4 go-live 경계 정합 / autopilot-run-scope 2026-05-29):
  - LLM 이 실제 호출되어 카드를 발권하나 probationary=자본0(배분 무영향). DRY_RUN·EMERGENCY_STOP 유지.
  - ⛔ 실자금 flip(DRY_RUN=false)·push 는 사람 게이트 = 본 팩토리 범위 밖. 발권+채점까지만.
  - 기본 use_local_llm=False → llm None → 전부 abstain(byte-identical). on 일 때만 실 LLM.
★additive: 호출처 0(coin_track_macro opt-in wire 가 소비). 기존 llm_provider/active_loop 무수정.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from core.assume.active_loop import ActiveAnalystLoop, LoopConfig
from core.assume.info_delta_gate import RateCapState

logger = logging.getLogger(__name__)

_ENV_ACTIVE_LOOP_SHADOW = "ACTIVE_LOOP_SHADOW"


def is_active_loop_shadow_enabled() -> bool:
    """S4 발권 shadow wire opt-in 게이트(coin_track_macro 소비). off = 미호출(byte-identical).

    on 이어도 카드는 probationary(자본0) → 배분 무영향. go-live arming(사람 게이트)과 별개.
    study_register.is_r15_enabled 동일 패턴(1/true/on/yes).
    """
    return str(os.environ.get(_ENV_ACTIVE_LOOP_SHADOW, "")).strip().lower() in (
        "1", "true", "on", "yes")


class GenerateToComplete:
    """brain.llm_provider.LLMProvider(generate(prompt)) → macro_reasoning.LLMProvider(complete) 어댑터."""

    def __init__(self, provider):
        self._p = provider

    def complete(self, system: str, user: str, json_mode: bool = True) -> str:
        import time
        import urllib.error
        prompt = f"{system}\n\n{user}"
        if json_mode:
            prompt += "\n\nRespond ONLY with a single valid JSON object, no prose."
        last = None
        for attempt in range(4):
            try:
                raw = self._p.generate(prompt)
                if json_mode and isinstance(raw, str):
                    raw = _extract_json(raw)
                return raw
            except urllib.error.HTTPError as e:
                last = e
                # 429(rate limit, 동일 OAuth 동시호출)·529(overloaded) → 지수 backoff 재시도
                if e.code in (429, 529) and attempt < 3:
                    time.sleep((5, 15, 45)[attempt])   # exponential backoff(DA-rate-limit)
                    continue
                raise
        if last is not None:
            raise last
        return ""


def _extract_json(text: str) -> str:
    """LLM 응답에서 첫 JSON object 추출(코드펜스·prose 혼입 방어)."""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("```")[1] if "```" in s[3:] else s
        s = s.lstrip("json").strip()
    a, b = s.find("{"), s.rfind("}")
    if a != -1 and b != -1 and b > a:
        cand = s[a : b + 1]
        try:
            json.loads(cand)
            return cand
        except Exception:
            return cand
    return s


def ollama_health(base_url: str = "http://localhost:11434") -> bool:
    """OllamaQwen 로컬 서버 가용 여부(실호출 전 health). 미가동 → False(abstain)."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{base_url.rstrip('/')}/api/tags", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def build_active_loop(
    *,
    use_local_llm: bool = False,
    use_claude: bool = False,
    report_store=None,
    rate_cap: Optional[RateCapState] = None,
    write_back=None,
    config: Optional[LoopConfig] = None,
    require_health: bool = True,
) -> ActiveAnalystLoop:
    """발권 실연결 ActiveAnalystLoop 빌드.

    기본(둘 다 False) → llm None → 전부 abstain(byte-identical, 발권 0).
    use_claude=True → ClaudeProvider(deep tier, ~/.claude/.credentials.json OAuth) 어댑터 주입.
      credentials 부재/SDK 오류 → graceful abstain(예외 X). ★사용자 명시 시만(비용·OAuth 한도).
    use_local_llm=True → OllamaQwenProvider 어댑터(require_health 시 서버 가동 확인 후, 미가동 graceful).
    우선순위: use_claude > use_local_llm(둘 다 True 면 Claude).
    """
    llm = None
    if use_claude:
        try:
            from core.brain.llm_provider import ClaudeProvider
            llm = GenerateToComplete(ClaudeProvider())
            logger.info("active_loop LLM 실배선: Claude(OAuth deep)")
        except Exception as e:
            logger.warning("ClaudeProvider 배선 실패 → abstain: %s", e)
            llm = None
    elif use_local_llm:
        if (not require_health) or ollama_health():
            try:
                from core.brain.llm_provider import OllamaQwenProvider
                llm = GenerateToComplete(OllamaQwenProvider())
                logger.info("active_loop LLM 실배선: OllamaQwen(local)")
            except Exception as e:
                logger.warning("OllamaQwen 배선 실패 → abstain: %s", e)
                llm = None
        else:
            logger.info("OllamaQwen 서버 미가동 → abstain(발권 0)")
    return ActiveAnalystLoop(
        llm=llm, report_store=report_store, rate_cap=rate_cap,
        write_back=write_back, config=config,
    )


def build_shadow_active_loop(
    *,
    use_claude: bool = True,
    use_local_llm: bool = False,
    cap_per_slot: int = 1,
    report_store=None,
    write_back=None,
    config: Optional[LoopConfig] = None,
) -> ActiveAnalystLoop:
    """coin_track_macro 발권 shadow wire 전용 빌더 — rate_cap(슬롯당 cap_per_slot, 기본 일1회) 내장.

    ★build_active_loop + RateCapState 결합. 매 collect_market_state 호출이 폭증하지 않도록
    슬롯당 발권 상한(info_delta_gate)을 강제. 인스턴스를 호출자가 캐시하면 rate 상태가 유지됨.
    use_claude 기본 True(사용자 "OAuth 한도 OK, 메인과 동일 키"). off=llm None→abstain(byte-identical).
    """
    return build_active_loop(
        use_claude=use_claude, use_local_llm=use_local_llm,
        report_store=report_store,
        rate_cap=RateCapState(cap_per_slot=cap_per_slot),
        write_back=write_back, config=config,
    )


# ── S5 stage-1 ingest 실배선 (하이쿠 요약 + BGE 임베딩) ───────────────────
HAIKU_MODEL = "claude-haiku-4-5-20251001"   # 소형 LLM = Claude Haiku 4.5(OAuth, 저비용 요약)


def bge_health(base_url: str = "http://127.0.0.1:8787") -> bool:
    """DaService BGE 임베드 서버(127.0.0.1:8787) 가용 여부."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{base_url.rstrip('/')}/health", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def build_research_ingest(
    *,
    use_haiku: bool = False,
    use_bge: bool = False,
    store=None,
    novelty_min: float = 0.15,
    require_health: bool = True,
):
    """S5 stage-1 ResearchIngestPipeline 실배선 (사용자 구상: 리포트→하이쿠 요약→BGE 인덱싱).

    use_haiku=True → ClaudeProvider(Haiku 4.5) 어댑터를 summarizer 로 주입(소형 LLM 요약).
      ⛔OAuth credentials 부재/오류 → graceful(summarizer None → raw truncate 로 fallback).
    use_haiku=False → summarizer None → raw 그대로 BGE 인덱싱(요약 생략, 사용자 '그대로 bge로 읽거나').
    use_bge=True → DaServiceEmbedder(127.0.0.1:8787 BGE-m3) 주입(require_health 시 서버 확인 후).
      미가동 → embedder None → ingest abstain(byte-identical).
    """
    from core.assume.research_ingest import ResearchIngestPipeline

    summarizer = None
    if use_haiku:
        try:
            from core.brain.llm_provider import ClaudeProvider
            summarizer = GenerateToComplete(ClaudeProvider(model=HAIKU_MODEL))
            logger.info("research_ingest summarizer 실배선: Claude Haiku 4.5")
        except Exception as e:
            logger.warning("Haiku summarizer 배선 실패 → raw truncate: %s", e)
            summarizer = None

    embedder = None
    if use_bge:
        if (not require_health) or bge_health():
            try:
                from core.brain.embedder import DaServiceEmbedder
                embedder = DaServiceEmbedder()
                logger.info("research_ingest embedder 실배선: DaService BGE-m3(8787)")
            except Exception as e:
                logger.warning("BGE embedder 배선 실패 → abstain: %s", e)
                embedder = None
        else:
            logger.info("BGE 서버(8787) 미가동 → embedder None(abstain)")

    return ResearchIngestPipeline(
        summarizer=summarizer, embedder=embedder, store=store, novelty_min=novelty_min,
    )


if __name__ == "__main__":
    from core.brain.macro_schema import Bloc, MacroView, RegimeEstimate, RegimeLabel, ViewStatus

    def _view(label, conf):
        est = RegimeEstimate(bloc=Bloc.USD, regime_now=label, confidence_now=conf)
        return MacroView(regimes={Bloc.USD: est}, status=ViewStatus.FRESH, as_of_ts=0.0)

    # 1) use_local_llm=False → llm None → abstain(byte-identical)
    loop0 = build_active_loop(use_local_llm=False)
    assert loop0.llm is None
    assert loop0.run_cycle(_view(RegimeLabel.OVERHEAT, 0.2)) is None
    print("1) use_local_llm=False → llm None abstain(byte-identical) OK")

    # 2) generate→complete 어댑터: JSON 추출
    class _Gen:
        def generate(self, prompt, **kw):
            return '```json\n{"statement":"x","direction":"de_risk","falsification_metric":"fwd<0"}\n```'
    ad = GenerateToComplete(_Gen())
    out = ad.complete("sys", "user", json_mode=True)
    parsed = json.loads(out)
    assert parsed["direction"] == "de_risk"
    print(f"2) generate→complete JSON 추출 OK ({out[:30]}...)")

    # 3) 어댑터 주입 loop → 발권 동작(fake provider)
    class _GenClaim:
        def __init__(self): self._n = 0
        def generate(self, prompt, **kw):
            if "audit" in prompt.lower():
                return '{"approve": true, "reason": "ok"}'
            return ('{"statement":"Overheat 원자재 우위","direction":"long_tilt",'
                    '"mediator_ref":"regime:USD:Overheat","outcome_metric":"ts_rank_IC",'
                    '"falsification_metric":"원자재 3M fwd IC < 0","counter_thesis":"달러 상쇄"}')
    loop = ActiveAnalystLoop(llm=GenerateToComplete(_GenClaim()))
    pc = loop.run_cycle(_view(RegimeLabel.OVERHEAT, 0.3), numeric_revision=0.3)
    assert pc is not None and pc.card.kind == "probationary" and pc.card.bonus_cap == 0.0
    print(f"3) 어댑터 주입 → 발권 동작 OK (probationary, 자본0)")

    # 4) ollama_health (미가동 시 False, 예외 X)
    h = ollama_health("http://localhost:59999")   # 없는 포트
    assert h is False
    print(f"4) ollama_health 미가동 포트 → False(graceful) OK")

    # 5) use_local_llm=True + 서버 미가동 → graceful abstain
    loop5 = build_active_loop(use_local_llm=True)   # health 실패 시 llm None
    if loop5.llm is None:
        print("5) use_local_llm=True + 서버 미가동 → graceful abstain OK")
    else:
        # 서버 가동 중이면 실 LLM 1회 발권 시도(자본0)
        pc5 = loop5.run_cycle(_view(RegimeLabel.STAGFLATION, 0.3), numeric_revision=0.3)
        print(f"5) ★OllamaQwen 실연결 발권 {'성공' if pc5 else 'abstain'}(자본0) — LIVE 검증 OK")

    print("S4 loop_factory self-test PASS "
          "(generate→complete 어댑터 · JSON 추출 · 발권 실배선 · health graceful · byte-identical 기본)")
