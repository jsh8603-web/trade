"""core/brain/embedder.py — Embedder 추상화 + da 8787 재사용.

제공자:
  DaServiceEmbedder  — 검증된 da embed 서비스(127.0.0.1:8787/embed)
                       BGE-m3 dim 1024, ONNX-DML GPU
  GeminiEmbedder     — 3072 호환 폴백 (재임베딩 전까지)
  DaReranker         — 옵션 8787/rerank (bge-reranker-v2-m3)

SACRED:
  - 신규 ollama BGE 금지 (da/vaultvoice 임베딩 공간 보존)
  - EMBED_URL 기본값 = 127.0.0.1:8787
  - 차원 일관성: DaServiceEmbedder → 1024, GeminiEmbedder → 3072
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger("brain.embedder")

EMBED_URL = os.environ.get("EMBED_URL", "http://127.0.0.1:8787")
EMBED_DIM_BGE = 1024
EMBED_DIM_GEMINI = 3072


# ── ABC ──────────────────────────────────────────────────────────────

class Embedder(ABC):
    """임베딩 제공자 공통 추상 기반."""

    @property
    @abstractmethod
    def dim(self) -> int:
        """출력 벡터 차원."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """텍스트 리스트 → 벡터 리스트 (L2 정규화 완료)."""


# ── DaServiceEmbedder ────────────────────────────────────────────────

class DaServiceEmbedder(Embedder):
    """da embed 서비스 재사용 — POST http://127.0.0.1:8787/embed.

    BGE-m3 dim 1024, ONNX-DML GPU 가동 중.
    응답: {vectors: [[1024 floats], ...]}
    L2 정규화는 서비스 측에서 수행 (코사인 = 내적).
    """

    def __init__(self, base_url: str = EMBED_URL) -> None:
        self._base_url = base_url.rstrip("/")

    @property
    def dim(self) -> int:
        return EMBED_DIM_BGE

    def health(self) -> dict[str, Any]:
        """GET /health → 서비스 상태 dict."""
        req = urllib.request.Request(
            f"{self._base_url}/health",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = json.dumps({"texts": texts}).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/embed",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        vectors: list[list[float]] = result["vectors"]
        if len(vectors) != len(texts):
            raise ValueError(f"벡터 수 불일치: expected {len(texts)}, got {len(vectors)}")
        if not all(len(v) == EMBED_DIM_BGE for v in vectors):
            raise ValueError(f"벡터 차원 오류: expected {EMBED_DIM_BGE}")
        return vectors


# ── GeminiEmbedder ───────────────────────────────────────────────────

class GeminiEmbedder(Embedder):
    """3072 호환 폴백 — 재임베딩 완료 전까지 기존 Gemini 임베딩 공간 유지.

    GEMINI_API_KEY 환경변수 필요. .env 없으면 초기화 실패.
    ⚠️ 재임베딩(SO-3) 완료 후 DaServiceEmbedder 로 전환 권장.
    """

    def __init__(self) -> None:
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from rl_hybrid.rag.gemini_client import GeminiClient  # noqa: PLC0415
            self._client = GeminiClient()
        return self._client

    @property
    def dim(self) -> int:
        return EMBED_DIM_GEMINI

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._get_client()
        vectors = []
        for text in texts:
            vec = client.embed(text)
            if len(vec) != EMBED_DIM_GEMINI:
                raise ValueError(f"GeminiEmbedder 차원 오류: {len(vec)} != {EMBED_DIM_GEMINI}")
            vectors.append(vec)
        return vectors


# ── DaReranker ───────────────────────────────────────────────────────

class DaReranker:
    """옵션 reranker — POST 127.0.0.1:8787/rerank (bge-reranker-v2-m3).

    SO-5 recall 품질 향상에 활용.
    """

    def __init__(self, base_url: str = EMBED_URL) -> None:
        self._base_url = base_url.rstrip("/")

    def rerank(self, query: str, docs: list[str], top_k: int = 5) -> list[dict[str, Any]]:
        """→ [{id, score}, ...] top_k 개 (점수 내림차순).

        docs: 평문 텍스트 리스트 — 내부에서 {id, text} 형식으로 변환.
        """
        if not docs:
            return []
        doc_objs = [{"id": str(i), "text": t} for i, t in enumerate(docs)]
        payload = json.dumps({"query": query, "docs": doc_objs, "top_k": top_k}).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/rerank",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result.get("results", [])
