"""tests/assume/test_research_ingest.py — S5 stage-1 ingest(요약→임베딩→PIT)."""
import numpy as np

from core.assume.research_ingest import ResearchIngestPipeline


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


def test_embedder_none_abstains():
    assert ResearchIngestPipeline(embedder=None).ingest("리포트", release_ts=1.0) is None


def test_new_doc_indexed():
    p = ResearchIngestPipeline(embedder=_FakeEmbedder(), summarizer=_FakeSummarizer())
    d = p.ingest("HBM 공급부족 목표가 상향", release_ts=1000.0, scope="sector")
    assert d is not None and d.scope == "sector" and d.summary.startswith("SUMMARY:")
    assert len(p.shadow_index) == 1 and d.release_ts == 1000.0


def test_duplicate_skipped():
    p = ResearchIngestPipeline(embedder=_FakeEmbedder(), summarizer=_FakeSummarizer())
    p.ingest("동일 문서", release_ts=1.0)
    assert p.ingest("동일 문서", release_ts=2.0) is None
    assert len(p.shadow_index) == 1


def test_summarizer_none_truncates():
    p = ResearchIngestPipeline(embedder=_FakeEmbedder(seed=1), summarizer=None)
    d = p.ingest("X" * 2000, release_ts=1.0)
    assert d is not None and len(d.summary) <= 600


def test_bitemporal_stamp():
    p = ResearchIngestPipeline(embedder=_FakeEmbedder(seed=2))
    d = p.ingest("거시 리포트", release_ts=2100.0, ingestion_ts=2200.0)
    assert d.release_ts == 2100.0 and d.ingestion_ts == 2200.0


def test_external_store_upsert():
    class _Store:
        def __init__(self):
            self._v = []

        def vectors(self):
            return self._v

        def upsert(self, doc):
            self._v.append(doc.vector)

    st = _Store()
    p = ResearchIngestPipeline(embedder=_FakeEmbedder(seed=3), store=st)
    d = p.ingest("store 문서", release_ts=1.0)
    assert d is not None and len(st._v) == 1 and len(p.shadow_index) == 0


def test_ingest_batch():
    p = ResearchIngestPipeline(embedder=_FakeEmbedder(seed=4))
    res = p.ingest_batch([
        {"raw_text": "doc A", "release_ts": 1.0},
        {"raw_text": "doc B", "release_ts": 2.0, "scope": "sector"},
    ])
    assert len(res) == 2
