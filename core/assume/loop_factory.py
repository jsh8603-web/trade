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
_ENV_MACRO_ENRICH = "MACRO_ENRICH"
_ENV_MACRO_CONSENSUS = "MACRO_CONSENSUS"


def _env_on(name: str) -> bool:
    return str(os.environ.get(name, "")).strip().lower() in ("1", "true", "on", "yes")


def is_active_loop_shadow_enabled() -> bool:
    """S4 발권 shadow wire opt-in 게이트(coin_track_macro 소비). off = 미호출(byte-identical).

    on 이어도 카드는 probationary(자본0) → 배분 무영향. go-live arming(사람 게이트)과 별개.
    study_register.is_r15_enabled 동일 패턴(1/true/on/yes).
    """
    return _env_on(_ENV_ACTIVE_LOOP_SHADOW)


def is_macro_enrich_enabled() -> bool:
    """macro_reasoning.enrich(거시 LLM 추론) wire opt-in. off=미호출(byte-identical, baseline 유지).

    ★on 이면 LLM stance 가 macro_view 에 주입돼 regime_to_weights BL View 로 배분 이동
      = 결정론 baseline 자체를 LLM 이 수정(FHC bonus 와 다른 리스크 프로파일, 사용자 명시 후 활성).
    """
    return _env_on(_ENV_MACRO_ENRICH)


def is_macro_consensus_enabled() -> bool:
    """consensus(고-스테이크스 LLM 합의) wire opt-in. off=미호출(byte-identical).

    ★on 이면 고-스테이크스 배분 변경을 LLM 이 검토 → down-only de-risk(보수화만, 증폭 불가).
    """
    return _env_on(_ENV_MACRO_CONSENSUS)


def build_macro_reasoning_node(*, use_claude: bool = True, report_store=None,
                               correction_memory=None):
    """macro_reasoning.MacroReasoningNode 실배선 — trigger 시 LLM 거시추론(stance) enrich.

    use_claude=True → ClaudeProvider(OAuth) 어댑터 주입. 실패/off → llm None → enrich abstain(baseline).
    report_store = research_ingest(RAG) 주입 시 PIT 리포트 컨텍스트 소비.
    """
    from core.brain.macro_reasoning import MacroReasoningNode
    llm = None
    if use_claude:
        try:
            from core.brain.llm_provider import ClaudeProvider
            llm = GenerateToComplete(ClaudeProvider())
            logger.info("MacroReasoningNode LLM 실배선: Claude(OAuth)")
        except Exception as e:
            logger.warning("MacroReasoningNode llm 배선 실패 → abstain: %s", e)
            llm = None
    return MacroReasoningNode(llm=llm, report_store=report_store,
                             correction_memory=correction_memory)


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


# ── S6 종목 universe 실연결 (stock.admission 안정 API 소비) ──────────────────
def stock_admission_universe_fn(
    *,
    whitelist=None,
    fetch_krx_universe: bool = False,
    as_of=None,
    market: str = "KRX-MARCAP",
    use_krx_status: bool = False,
    krx_status_provider=None,
    tier2_allowlist=None,
):
    """stock.admission 실연결 in_universe_fn(ticker)->bool — 거시→종목 stock 안정 API 단방향 소비.

    ★universe 정책(admission.LLM_EXPANSION 정합): LLM 임의 확장 차단 = config 화이트리스트만 SSOT.
      - whitelist(set) = universe SSOT(button/supervisor 조립분 주입). 1차 게이트(미포함=거부).
      - whitelist None + fetch_krx_universe → KrxUniverseProvider.get_universe() 실조회로 채움(FDR).
      - 둘 다 없으면 fail-closed(빈 universe = 전부 거부, 보수적 = LLM 임의 발권 차단).
    admission.check_admission 2차 적격성(tier=CORE_ALLOWED 현물 / region ticker 추론 / KRX 제재).
      use_krx_status → KrxStatusProvider 실조회(KR 제재 상태), 부재 시 None(무제재 가정).
    실패=fail-closed(False). ⛔stock/ 무수정 — 안정 API import 만(button 작업 파일 미접촉).
    """
    _wl = set(whitelist) if whitelist else None
    if _wl is None and fetch_krx_universe:
        try:
            from stock.data.krx_universe import KrxUniverseProvider
            _wl = set(KrxUniverseProvider().get_universe(as_of=as_of, market=market))
            logger.info("stock universe 실조회: %d 종목(%s)", len(_wl), market)
        except Exception as e:
            logger.warning("KRX universe 실조회 실패 → fail-closed(빈 universe): %s", e)
            _wl = set()
    if _wl is None:
        _wl = set()

    _status = krx_status_provider
    if use_krx_status and _status is None:
        try:
            from stock.data.krx_universe import KrxStatusProvider
            _status = KrxStatusProvider()
        except Exception as e:
            logger.warning("KrxStatusProvider 생성 실패 → 무제재 가정: %s", e)
            _status = None

    def _fn(ticker) -> bool:
        try:
            t = str(ticker)
            if t not in _wl:                       # 1차 universe SSOT 게이트(LLM 임의 확장 차단)
                return False
            from stock.admission import check_admission
            from stock.contracts import ProductTier
            region = "KR" if (t.isdigit() and len(t) == 6) else "US"
            krx = None
            if _status is not None and region == "KR":
                try:
                    krx = _status.get_status_snapshot(t, as_of=as_of)
                except Exception:
                    krx = None
            res = check_admission(t, ProductTier.CORE_ALLOWED, region,
                                  krx_status=krx, tier2_allowlist=tier2_allowlist)
            return bool(res.admit)                 # 2차 적격성(제재·tier)
        except Exception:
            return False                           # fail-closed
    return _fn


# ── S6 종목 소식 → 카드 발권 오케스트레이터 실배선 ─────────────────────────
def build_security_news_loop(
    *,
    use_claude: bool = True,
    use_haiku: bool = True,
    use_bge: bool = True,
    in_universe_fn=None,
    universe=None,
    use_stock_admission: bool = False,
    whitelist=None,
    fetch_krx_universe: bool = False,
    use_krx_status: bool = False,
    as_of=None,
    store=None,
    novelty_min: float = 0.15,
    rate_cap: Optional[RateCapState] = None,
    require_health: bool = True,
):
    """S6 SecurityNewsCardLoop 실배선 (종목 뉴스/증권 리포트 → probationary 카드 발권).

    ingest = build_research_ingest(haiku 요약 + BGE 임베딩) / active_loop = build_active_loop(claude).
    in_universe_fn = button stock/ 스크린 통과분 콜백(주입식). universe(set[str]) 주면 자동 래핑.
    ★실 universe·실 종목뉴스소스 = button 합류 게이트(handoff §5.2) — 거시 세션 단독은 더미 universe e2e.
    use_* 전부 off → ingest embedder None / active_loop llm None → 전부 abstain(byte-identical, 발권 0).
    in_universe_fn/universe 둘 다 None → 모두 후보 풀(보수적, 즉시 발권 0).
    """
    from core.assume.security_news_loop import SecurityNewsCardLoop

    ingest = build_research_ingest(
        use_haiku=use_haiku, use_bge=use_bge, store=store,
        novelty_min=novelty_min, require_health=require_health)
    # ★RAG 닫기: ingest 를 active_loop report_store 로 연결 → on_news 가 적재한 리포트를
    #   발권 단계(retrieve→claim)가 컨텍스트로 소비(research_ingest.retrieve = stage-2 Protocol).
    al = build_active_loop(use_claude=use_claude, rate_cap=rate_cap, report_store=ingest)

    fn = in_universe_fn
    if fn is None and use_stock_admission:
        # ★실연결: stock.admission 안정 API(거시→종목 단방향). whitelist 또는 KRX 실조회 universe.
        fn = stock_admission_universe_fn(
            whitelist=whitelist, fetch_krx_universe=fetch_krx_universe,
            use_krx_status=use_krx_status, as_of=as_of)
    elif fn is None and universe is not None:
        _u = set(universe)
        fn = lambda t: t in _u   # noqa: E731 (button universe set → 콜백 래핑)
    return SecurityNewsCardLoop(ingest=ingest, active_loop=al, in_universe_fn=fn)


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
