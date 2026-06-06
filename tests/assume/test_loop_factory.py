"""tests/assume/test_loop_factory.py — S4 발권 실연결 팩토리(LLM 어댑터)."""
import json

import numpy as np

from core.assume.active_loop import ActiveAnalystLoop
from core.assume.loop_factory import (
    GenerateToComplete,
    build_active_loop,
    build_security_news_loop,
    build_shadow_active_loop,
    is_active_loop_shadow_enabled,
    ollama_health,
)
from core.assume.research_ingest import ResearchIngestPipeline
from core.assume.security_news_loop import SecurityNewsCardLoop
from core.brain.macro_schema import Bloc, MacroView, RegimeEstimate, RegimeLabel, ViewStatus


def _view(label, conf):
    est = RegimeEstimate(bloc=Bloc.USD, regime_now=label, confidence_now=conf)
    return MacroView(regimes={Bloc.USD: est}, status=ViewStatus.FRESH, as_of_ts=0.0)


class _Gen:
    """brain.llm_provider 스타일 generate(prompt) provider."""
    def __init__(self, payload):
        self._payload = payload

    def generate(self, prompt, **kw):
        if "audit" in prompt.lower():
            return '{"approve": true, "reason": "ok"}'
        return self._payload


def test_use_local_llm_false_is_byte_identical():
    loop = build_active_loop(use_local_llm=False)
    assert loop.llm is None
    assert loop.run_cycle(_view(RegimeLabel.OVERHEAT, 0.2)) is None


def test_generate_to_complete_json_extraction():
    g = _Gen('```json\n{"a":1,"b":"x"}\n```')
    out = GenerateToComplete(g).complete("sys", "user", json_mode=True)
    assert json.loads(out)["a"] == 1


def test_generate_to_complete_prose_wrapped_json():
    g = _Gen('Here is the card: {"direction":"de_risk"} hope it helps')
    out = GenerateToComplete(g).complete("sys", "user", json_mode=True)
    assert json.loads(out)["direction"] == "de_risk"


def test_adapter_injected_loop_mints():
    claim = ('{"statement":"Overheat 원자재 우위","direction":"long_tilt",'
             '"mediator_ref":"regime:USD:Overheat","outcome_metric":"ts_rank_IC",'
             '"falsification_metric":"원자재 3M fwd IC < 0","counter_thesis":"달러 상쇄"}')
    loop = ActiveAnalystLoop(llm=GenerateToComplete(_Gen(claim)))
    pc = loop.run_cycle(_view(RegimeLabel.OVERHEAT, 0.3), numeric_revision=0.3)
    assert pc is not None and pc.card.kind == "probationary" and pc.card.bonus_cap == 0.0


def test_ollama_health_dead_port_graceful():
    assert ollama_health("http://localhost:59999") is False


def test_build_with_local_llm_graceful_when_server_down():
    # 서버 미가동/미설치 → llm None graceful(예외 없음), abstain
    loop = build_active_loop(use_local_llm=True)
    # 서버 떠 있으면 llm 주입될 수 있으나, 없으면 None — 둘 다 예외 없이 통과해야
    assert loop is not None
    if loop.llm is None:
        assert loop.run_cycle(_view(RegimeLabel.OVERHEAT, 0.2)) is None


# ── (B) shadow builder + env gate ──────────────────────────────────────────
def test_active_loop_shadow_env_gate(monkeypatch):
    monkeypatch.delenv("ACTIVE_LOOP_SHADOW", raising=False)
    assert is_active_loop_shadow_enabled() is False
    monkeypatch.setenv("ACTIVE_LOOP_SHADOW", "on")
    assert is_active_loop_shadow_enabled() is True


def test_build_shadow_active_loop_rate_cap():
    loop = build_shadow_active_loop(use_claude=False)
    assert loop.llm is None and loop.rate_cap is not None
    assert loop.rate_cap.cap_per_slot == 1   # 기본 일1회


# ── (D) security_news_loop 팩토리 ──────────────────────────────────────────
class _Emb:
    def __init__(self):
        self.r = np.random.RandomState(0)
        self.m = {}

    def dim(self):
        return 16

    def embed(self, texts):
        out = []
        for t in texts:
            if t not in self.m:
                self.m[t] = self.r.randn(16).tolist()
            out.append(self.m[t])
        return out


class _NewsLLM:
    def complete(self, system, user, json_mode=True):
        if "audit" in system.lower():
            return '{"approve": true, "reason": "ok"}'
        return json.dumps({
            "statement": "HBM 공급부족 수혜", "direction": "long_tilt",
            "mediator_ref": "regime:USD:Overheat", "outcome_metric": "cs_rank_IC",
            "falsification_metric": "3M 상대수익 < 0", "counter_thesis": "공급 정상화"})


def test_build_security_news_loop_off_byte_identical():
    """전부 off → ingest embedder None + active_loop llm None → abstain(byte-identical)."""
    loop = build_security_news_loop(
        use_claude=False, use_haiku=False, use_bge=False, universe={"005930"})
    assert loop.active_loop.llm is None and loop.ingest.embedder is None
    r = loop.on_news("005930", "삼성 HBM 소식", 1000.0)
    assert r.status == "duplicate"          # embedder None → ingest abstain


def test_build_security_news_loop_universe_wrap():
    loop = build_security_news_loop(
        use_claude=False, use_haiku=False, use_bge=False, universe={"005930"})
    assert loop.in_universe_fn("005930") is True
    assert loop.in_universe_fn("999999") is False


def test_security_news_batch_e2e():
    """더미 universe + fake 부품 → 종목 뉴스 batch 발권/풀."""
    ingest = ResearchIngestPipeline(embedder=_Emb())
    al = ActiveAnalystLoop(llm=_NewsLLM())
    loop = SecurityNewsCardLoop(ingest=ingest, active_loop=al,
                                in_universe_fn=lambda t: t == "005930")
    items = [
        {"ticker": "005930", "raw_text": "삼성전자 HBM3E 공급부족 목표가 상향",
         "release_ts": 1000.0, "source": "broker"},
        {"ticker": "999999", "raw_text": "잡주 급등 루머", "release_ts": 1001.0},
    ]
    res = loop.on_news_batch(items)
    assert res[0].status == "minted"
    assert res[0].card.card.domain == "equity" and res[0].card.card.bonus_cap == 0.0
    assert res[1].status == "pooled"        # 유니버스 밖 → 후보 풀


# ── (D) stock.admission 실연결 universe ────────────────────────────────────
def test_stock_admission_universe_real_wire():
    """stock.admission 안정 API 실연결: whitelist SSOT + 적격성 게이트."""
    from core.assume.loop_factory import stock_admission_universe_fn

    fn = stock_admission_universe_fn(whitelist={"005930", "000660"})
    assert fn("005930") is True           # universe 내 + 현물 적격
    assert fn("999999") is False          # universe 밖 = LLM 임의 확장 차단

    fn0 = stock_admission_universe_fn()   # whitelist 부재 → fail-closed
    assert fn0("005930") is False


def test_stock_admission_krx_sanction_rejected():
    """KRX 제재(거래정지) 종목 → admission 실게이트 거부."""
    from core.assume.loop_factory import stock_admission_universe_fn
    from stock.admission import KrxStatusSnapshot

    class _Status:
        def get_status_snapshot(self, t, as_of=None):
            return KrxStatusSnapshot(is_halt=True)

    fn = stock_admission_universe_fn(
        whitelist={"005930"}, use_krx_status=True, krx_status_provider=_Status())
    assert fn("005930") is False          # universe 내지만 거래정지 → 거부


def test_build_security_news_loop_stock_admission():
    loop = build_security_news_loop(
        use_claude=False, use_haiku=False, use_bge=False,
        use_stock_admission=True, whitelist={"005930"})
    assert loop.in_universe_fn("005930") is True
    assert loop.in_universe_fn("999999") is False
