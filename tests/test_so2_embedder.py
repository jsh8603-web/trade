"""SO-2 테스트: core/brain/embedder.py DaServiceEmbedder + GeminiEmbedder.

검증기준:
- 8787 /health 확인 PASS
- /embed 실호출로 1024차원 벡터 반환 PASS
- L2 정규화 확인 (norm ≈ 1.0)
- GeminiEmbedder 폴백 인터페이스 정의 PASS
- 차원 일관성 단위테스트 PASS
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from core.brain.embedder import (
    EMBED_DIM_BGE,
    EMBED_DIM_GEMINI,
    DaReranker,
    DaServiceEmbedder,
    Embedder,
    GeminiEmbedder,
)


# ── 기본 구조 테스트 ─────────────────────────────────────────────────

def test_import_ok():
    from core.brain.embedder import Embedder, DaServiceEmbedder  # noqa: F401


def test_abstract_instantiation_raises():
    with pytest.raises(TypeError):
        Embedder()  # type: ignore[abstract]


def test_da_embedder_dim():
    e = DaServiceEmbedder()
    assert e.dim == 1024


def test_gemini_embedder_dim():
    e = GeminiEmbedder()
    assert e.dim == 3072


def test_dim_constants():
    assert EMBED_DIM_BGE == 1024
    assert EMBED_DIM_GEMINI == 3072


# ── 8787 /health 확인 ────────────────────────────────────────────────

def test_da_service_health():
    """da 서비스 /health → embed_dim=1024, BGE-m3 확인."""
    e = DaServiceEmbedder()
    h = e.health()
    assert h.get("embed_dim") == 1024, f"embed_dim 불일치: {h}"
    assert "bge-m3" in h.get("embed_model", "").lower(), f"모델 불일치: {h}"


# ── /embed 실호출 + 차원 + L2 정규화 ────────────────────────────────

def test_da_embed_live_single():
    """단일 텍스트 임베딩 — 1024차원 벡터 반환."""
    e = DaServiceEmbedder()
    vecs = e.embed(["bitcoin price analysis"])
    assert len(vecs) == 1
    assert len(vecs[0]) == 1024


def test_da_embed_live_batch():
    """배치 임베딩 — 텍스트 수 = 벡터 수."""
    e = DaServiceEmbedder()
    texts = ["BTC up", "ETH down", "fear greed index"]
    vecs = e.embed(texts)
    assert len(vecs) == 3
    assert all(len(v) == 1024 for v in vecs)


def test_da_embed_l2_normalized():
    """L2 정규화 확인 — norm ≈ 1.0 (코사인 = 내적)."""
    e = DaServiceEmbedder()
    vecs = e.embed(["normalize check"])
    norm = math.sqrt(sum(x * x for x in vecs[0]))
    assert abs(norm - 1.0) < 1e-3, f"L2 norm {norm:.6f} != 1.0"


def test_da_embed_empty():
    """빈 리스트 → 빈 결과."""
    e = DaServiceEmbedder()
    vecs = e.embed([])
    assert vecs == []


# ── GeminiEmbedder 폴백 인터페이스 ──────────────────────────────────

def test_gemini_embedder_interface():
    """GeminiEmbedder 는 Embedder 를 상속하며 dim=3072."""
    assert issubclass(GeminiEmbedder, Embedder)
    e = GeminiEmbedder()
    assert e.dim == EMBED_DIM_GEMINI


def test_gemini_embedder_mock_embed():
    """GeminiEmbedder.embed() — GeminiClient mock 으로 3072 벡터 반환."""
    mock_client = MagicMock()
    mock_client.embed.return_value = [0.0] * 3072

    with patch.object(GeminiEmbedder, "_get_client", return_value=mock_client):
        e = GeminiEmbedder()
        vecs = e.embed(["test text"])
    assert len(vecs) == 1
    assert len(vecs[0]) == 3072


def test_gemini_embedder_dimension_guard():
    """GeminiEmbedder — 차원 불일치 시 ValueError 발생."""
    mock_client = MagicMock()
    mock_client.embed.return_value = [0.0] * 1024  # 잘못된 차원

    with patch.object(GeminiEmbedder, "_get_client", return_value=mock_client):
        e = GeminiEmbedder()
        with pytest.raises(ValueError, match="차원 오류"):
            e.embed(["test"])


# ── DaReranker 인터페이스 ─────────────────────────────────────────────

def test_da_reranker_live():
    """DaReranker — /rerank 실호출로 결과 반환."""
    r = DaReranker()
    results = r.rerank(
        query="bitcoin rally",
        docs=["BTC surged 10%", "ETH stable", "fear greed 80"],
        top_k=2,
    )
    assert isinstance(results, list)
    assert len(results) <= 2
    if results:
        assert "score" in results[0]


def test_da_reranker_empty_docs():
    """DaReranker — 빈 docs → 빈 결과."""
    r = DaReranker()
    results = r.rerank("query", [], top_k=5)
    assert results == []
