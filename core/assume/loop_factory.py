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
from typing import Optional

from core.assume.active_loop import ActiveAnalystLoop, LoopConfig
from core.assume.info_delta_gate import RateCapState

logger = logging.getLogger(__name__)


class GenerateToComplete:
    """brain.llm_provider.LLMProvider(generate(prompt)) → macro_reasoning.LLMProvider(complete) 어댑터."""

    def __init__(self, provider):
        self._p = provider

    def complete(self, system: str, user: str, json_mode: bool = True) -> str:
        prompt = f"{system}\n\n{user}"
        if json_mode:
            prompt += "\n\nRespond ONLY with a single valid JSON object, no prose."
        raw = self._p.generate(prompt)
        if json_mode and isinstance(raw, str):
            raw = _extract_json(raw)
        return raw


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
    report_store=None,
    rate_cap: Optional[RateCapState] = None,
    write_back=None,
    config: Optional[LoopConfig] = None,
    require_health: bool = True,
) -> ActiveAnalystLoop:
    """발권 실연결 ActiveAnalystLoop 빌드.

    use_local_llm=False(기본) → llm None → 전부 abstain(byte-identical, 발권 0).
    use_local_llm=True → OllamaQwenProvider 어댑터 주입(require_health 시 서버 가동 확인 후).
      서버 미가동이면 llm None 유지(graceful abstain, 예외 X).
    """
    llm = None
    if use_local_llm:
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
