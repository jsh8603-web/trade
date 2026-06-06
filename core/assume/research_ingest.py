"""core/assume/research_ingest.py — S5 리서치 통합 stage-1 (소형 LLM 요약 → 임베딩 인덱싱, shadow).

plan §3 S5 = 2-stage: ①소형 LLM 요약 → 임베딩 인덱싱(RAG, PIT 스탬프) ②대형 LLM 카드발권.
본 모듈 = **stage-1 ingest**(요약+인덱싱). stage-2 발권 = active_loop.ActiveAnalystLoop(retrieve→claim).
즉 ingest → store → active_loop.retrieve → 발권 으로 거시 RAG 파이프라인이 닫힌다.

★bitemporal PIT(plan §3 S5 Q1④): valid_time(release_ts=발표일) vs ingestion_time(적재일) 분리 →
  RAG stale-context 누수 차단(백테스트 시 as_of 이전 발표분만 retrieve, rag_pit.PITFilter 정합).
★중복 인덱싱 방지: info_delta_gate.cosine_novelty(신규 doc vs 기존 index) < 임계면 skip(phantom 적재 방지).
★발권 단위 scope: macro / sector / <ticker>(종목=S6 button, 본 파이프라인은 scope 태그만 운반).
★shadow / fail-closed: embedder None → abstain(None). summarizer None → raw truncate(요약 생략).
  store None → shadow_index(dry-run 적재). 실 BGE/LanceDB 연결은 호출자 주입(go-live/VaultVoice).
★additive(INV-11): 호출처 0. 기존 brain.embedder/rag_pit 무수정(import만). 재사용=info_delta cosine_novelty.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional, Sequence

from core.assume.info_delta_gate import cosine_novelty

logger = logging.getLogger(__name__)


@dataclass
class IndexedDoc:
    doc_id: str
    summary: str
    vector: tuple
    release_ts: float                 # valid-time (발표일, PIT retrieve 기준)
    scope: str = "macro"              # macro / sector / <ticker>
    ingestion_ts: Optional[float] = None   # ingestion-time (적재일, bitemporal)
    novelty: Optional[float] = None
    source: str = ""


class ResearchIngestPipeline:
    """stage-1 ingest: 소형 LLM 요약 → 임베딩 → 중복판정 → PIT 스탬프 upsert. shadow."""

    def __init__(
        self,
        *,
        summarizer=None,     # LLMProvider (complete(system,user,json_mode=False)) — None=요약 생략
        embedder=None,       # brain.embedder.Embedder (embed(texts)->vectors) — None=abstain
        store=None,          # upsert(IndexedDoc) + vectors()->list[vector] — None=shadow_index
        novelty_min: float = 0.15,
        summary_max_chars: int = 600,
    ):
        self.summarizer = summarizer
        self.embedder = embedder
        self.store = store
        self.novelty_min = novelty_min
        self.summary_max_chars = summary_max_chars
        self.shadow_index: list = []   # store None 시 dry-run 적재

    # stage-1a — 소형 LLM 요약
    def summarize(self, raw_text: str) -> str:
        text = (raw_text or "").strip()
        if self.summarizer is None:
            return text[: self.summary_max_chars]   # 요약 생략 → truncate
        try:
            system = ("Summarize this research/news for a macro allocation index in <=3 sentences. "
                      "Keep tickers, numbers (TP, ratings, surprises), and dates. No opinion.")
            out = self.summarizer.complete(system, text[:4000], json_mode=False)
            return (out or text)[: self.summary_max_chars]
        except Exception as e:
            logger.warning("research_ingest 요약 실패 → raw truncate: %s", e)
            return text[: self.summary_max_chars]

    # stage-1b — 임베딩
    def _embed(self, summary: str) -> Optional[tuple]:
        if self.embedder is None:
            return None
        try:
            vecs = self.embedder.embed([summary])
            if not vecs:
                return None
            return tuple(float(x) for x in vecs[0])
        except Exception as e:
            logger.warning("research_ingest 임베딩 실패 → abstain: %s", e)
            return None

    def _corpus(self) -> list:
        if self.store is not None and hasattr(self.store, "vectors"):
            try:
                return list(self.store.vectors() or [])
            except Exception:
                return []
        return [d.vector for d in self.shadow_index]

    # stage-1 전체
    def ingest(
        self,
        raw_text: str,
        *,
        release_ts: float,
        scope: str = "macro",
        doc_id: Optional[str] = None,
        ingestion_ts: Optional[float] = None,
        source: str = "",
    ) -> Optional[IndexedDoc]:
        """소형 요약 → 임베딩 → 중복판정 → PIT 스탬프 upsert. abstain/중복 → None."""
        summary = self.summarize(raw_text)
        if not summary:
            return None

        vector = self._embed(summary)
        if vector is None:
            return None   # embedder 부재 = abstain(shadow)

        # 중복 인덱싱 방지(novelty)
        novelty = cosine_novelty(vector, self._corpus() or None)
        if novelty < self.novelty_min:
            logger.info("research_ingest 중복 skip: novelty=%.3f < %.3f", novelty, self.novelty_min)
            return None

        cid = doc_id or f"doc-{scope}-{abs(hash(summary)) % 10**10}"
        doc = IndexedDoc(
            doc_id=cid, summary=summary, vector=vector,
            release_ts=float(release_ts), scope=scope,
            ingestion_ts=ingestion_ts, novelty=novelty, source=source,
        )

        if self.store is not None and hasattr(self.store, "upsert"):
            try:
                self.store.upsert(doc)
                return doc
            except Exception as e:
                logger.warning("research_ingest store.upsert 실패 → shadow 적재: %s", e)
        self.shadow_index.append(doc)
        return doc

    def ingest_batch(self, docs: Sequence[dict]) -> list:
        """docs=[{raw_text, release_ts, scope?, doc_id?, source?}] 순차 ingest, indexed 만 반환."""
        out = []
        for d in docs:
            r = self.ingest(
                d.get("raw_text", ""),
                release_ts=d.get("release_ts", 0.0),
                scope=d.get("scope", "macro"),
                doc_id=d.get("doc_id"),
                ingestion_ts=d.get("ingestion_ts"),
                source=d.get("source", ""),
            )
            if r is not None:
                out.append(r)
        return out


if __name__ == "__main__":
    import numpy as np

    class _FakeEmbedder:
        def __init__(self, seed=0):
            self._rng = np.random.RandomState(seed)
            self._map = {}
        def dim(self):
            return 16
        def embed(self, texts):
            out = []
            for t in texts:
                if t not in self._map:
                    self._map[t] = self._rng.randn(16).tolist()
                out.append(self._map[t])
            return out

    class _FakeSummarizer:
        def complete(self, system, user, json_mode=False):
            return "SUMMARY: " + user[:40]

    emb = _FakeEmbedder()

    # 1) embedder None → abstain
    p0 = ResearchIngestPipeline(embedder=None)
    assert p0.ingest("리포트 본문", release_ts=100.0) is None
    print("1) embedder None → abstain(None) OK")

    # 2) 신규 문서 → indexed (shadow_index)
    p = ResearchIngestPipeline(embedder=emb, summarizer=_FakeSummarizer())
    d1 = p.ingest("삼성전자 HBM 공급부족 목표가 상향", release_ts=1000.0, scope="sector", source="broker")
    assert d1 is not None and d1.scope == "sector" and d1.summary.startswith("SUMMARY:")
    assert len(p.shadow_index) == 1 and d1.release_ts == 1000.0
    print(f"2) 신규 문서 → indexed OK (novelty={d1.novelty:.3f}, scope={d1.scope})")

    # 3) 동일 문서 재적재 → 중복 skip(novelty 낮음)
    d2 = p.ingest("삼성전자 HBM 공급부족 목표가 상향", release_ts=1001.0, scope="sector")
    assert d2 is None and len(p.shadow_index) == 1
    print("3) 동일 문서 재적재 → 중복 skip OK")

    # 4) 다른 문서 → 추가 indexed
    d3 = p.ingest("연준 금리 동결 시사 FOMC", release_ts=1002.0, scope="macro")
    assert d3 is not None and len(p.shadow_index) == 2
    print(f"4) 다른 문서 → indexed OK (총 {len(p.shadow_index)})")

    # 5) summarizer None → raw truncate
    p2 = ResearchIngestPipeline(embedder=_FakeEmbedder(seed=1), summarizer=None)
    d4 = p2.ingest("X" * 2000, release_ts=2000.0)
    assert d4 is not None and len(d4.summary) <= 600
    print(f"5) summarizer None → raw truncate OK (len={len(d4.summary)})")

    # 6) bitemporal: release_ts(valid) vs ingestion_ts 분리
    d5 = p2.ingest("새 거시 리포트", release_ts=2100.0, ingestion_ts=2200.0)
    assert d5.release_ts == 2100.0 and d5.ingestion_ts == 2200.0
    print("6) bitemporal valid/ingestion 분리 OK")

    # 7) 외부 store upsert + vectors corpus
    class _Store:
        def __init__(self): self._v = []
        def vectors(self): return self._v
        def upsert(self, doc): self._v.append(doc.vector)
    st = _Store()
    p3 = ResearchIngestPipeline(embedder=_FakeEmbedder(seed=2), store=st)
    r = p3.ingest("store 연결 문서", release_ts=3000.0)
    assert r is not None and len(st._v) == 1 and len(p3.shadow_index) == 0
    print("7) 외부 store.upsert + vectors corpus OK")

    # 8) batch
    p4 = ResearchIngestPipeline(embedder=_FakeEmbedder(seed=3))
    res = p4.ingest_batch([
        {"raw_text": "doc A", "release_ts": 1.0},
        {"raw_text": "doc B", "release_ts": 2.0, "scope": "sector"},
    ])
    assert len(res) == 2
    print(f"8) ingest_batch → {len(res)} indexed OK")

    print("S5 research_ingest self-test PASS "
          "(요약 → 임베딩 → 중복 skip → bitemporal PIT 스탬프 → store/shadow upsert · abstain)")
