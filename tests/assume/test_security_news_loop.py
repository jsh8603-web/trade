"""tests/assume/test_security_news_loop.py — S6 종목 소식 트리거 발권 오케스트레이터 골격."""
import json

import numpy as np

from core.assume.active_loop import ActiveAnalystLoop
from core.assume.research_ingest import ResearchIngestPipeline
from core.assume.security_news_loop import CandidatePool, SecurityNewsCardLoop


class _Emb:
    def __init__(self, seed=0):
        self.r = np.random.RandomState(seed)
        self.m = {}

    def dim(self):
        return 16

    def embed(self, texts):
        o = []
        for t in texts:
            if t not in self.m:
                self.m[t] = self.r.randn(16).tolist()
            o.append(self.m[t])
        return o


class _LLM:
    def complete(self, system, user, json_mode=True):
        if "audit" in system.lower():
            return '{"approve": true, "reason": "ok"}'
        return json.dumps({"statement": "HBM 수혜", "direction": "long_tilt",
                           "mediator_ref": "regime:USD:Overheat", "outcome_metric": "cs_rank_IC",
                           "falsification_metric": "3M 상대수익 < 0", "counter_thesis": "공급 정상화"})


def _mk():
    return ResearchIngestPipeline(embedder=_Emb()), ActiveAnalystLoop(llm=_LLM())


def test_in_universe_news_mints():
    ingest, al = _mk()
    loop = SecurityNewsCardLoop(ingest=ingest, active_loop=al, in_universe_fn=lambda t: t == "005930")
    r = loop.on_news("005930", "삼성전자 HBM3E 공급부족 목표가 상향", 1000.0)
    assert r.status == "minted"
    assert r.card.card.scope == "005930" and r.card.card.domain == "equity"
    assert r.card.card.bonus_cap == 0.0


def test_out_of_universe_pooled():
    ingest, al = _mk()
    loop = SecurityNewsCardLoop(ingest=ingest, active_loop=al, in_universe_fn=lambda t: t == "005930")
    r = loop.on_news("999999", "잡주 루머", 1001.0)
    assert r.status == "pooled" and len(loop.pool.items) == 1


def test_duplicate_news_skipped():
    ingest, al = _mk()
    loop = SecurityNewsCardLoop(ingest=ingest, active_loop=al, in_universe_fn=lambda t: True)
    loop.on_news("005930", "동일 소식", 1000.0)
    assert loop.on_news("005930", "동일 소식", 1001.0).status == "duplicate"


def test_candidate_promotion_on_universe_expand():
    ingest, al = _mk()
    loop = SecurityNewsCardLoop(ingest=ingest, active_loop=al, in_universe_fn=lambda t: t == "005930")
    loop.on_news("999999", "잡주 신규 소식", 1001.0)   # 풀 적재
    loop.in_universe_fn = lambda t: t in ("005930", "999999")  # 유니버스 확장
    promoted = loop.promote_candidates(max_slots=3)
    assert len(promoted) == 1 and promoted[0].ticker == "999999" and promoted[0].status == "minted"
    assert len(loop.pool.items) == 0


def test_none_universe_is_conservative_pool():
    ingest, al = _mk()
    loop = SecurityNewsCardLoop(ingest=ingest, active_loop=al, in_universe_fn=None)
    assert loop.on_news("000660", "신규 소식", 2000.0).status == "pooled"


def test_pool_drain_respects_max_slots():
    pool = CandidatePool()
    for i in range(5):
        pool.add(f"T{i}", "x", float(i))
    promoted = pool.drain_eligible(lambda t: True, max_slots=2)
    assert len(promoted) == 2 and len(pool.items) == 3
