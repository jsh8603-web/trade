"""core/brain/memory_layer.py — FinMem식 계층 메모리.

점수식: score = w_recency·recency + w_relevance·relevance + w_importance·importance
decay:  recency = α^(elapsed_hours / half_life_hours)  (지수 감쇠)

reuse: TradingAgents memory.py 패턴 (store_decision / update_with_outcome / get_past_context).

SACRED: Supabase 실쓰기 금지(.env 없음) — mock 내부 저장소로 동작.
        DRY_RUN, EMERGENCY_STOP 미변경.
"""

from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


# ── 기본 가중치·감쇠 파라미터 ────────────────────────────────────────

W_RECENCY = 0.4
W_RELEVANCE = 0.35
W_IMPORTANCE = 0.25
ALPHA_DECAY = 0.5          # 반감기 기반 지수 감쇠 밑수
HALF_LIFE_HOURS = 24.0     # 24시간 후 recency = 0.5


# ── MemoryEntry ──────────────────────────────────────────────────────

@dataclass
class MemoryEntry:
    """단일 메모리 레코드."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision: str = ""          # buy / sell / hold
    reason: str = ""
    confidence: float = 0.0
    importance: float = 0.5     # 0~1 (외부 주입 또는 결과 업데이트)
    outcome_pct: float | None = None  # 사후 결과 (%)
    created_at: float = field(default_factory=time.time)   # epoch seconds
    embedding: list[float] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def elapsed_hours(self, now: float | None = None) -> float:
        t = now if now is not None else time.time()
        return max(0.0, (t - self.created_at) / 3600.0)


# ── MemoryLayer ──────────────────────────────────────────────────────

class MemoryLayer:
    """FinMem식 계층 메모리.

    store_decision  → 새 MemoryEntry 저장
    update_with_outcome → 결과(outcome_pct) 반영 + importance 갱신
    get_past_context    → 유사 결정 FinMem 점수 순 조회
    score               → 단일 엔트리 FinMem 점수 계산
    """

    def __init__(
        self,
        w_recency: float = W_RECENCY,
        w_relevance: float = W_RELEVANCE,
        w_importance: float = W_IMPORTANCE,
        alpha: float = ALPHA_DECAY,
        half_life_hours: float = HALF_LIFE_HOURS,
        max_entries: int = 500,
    ) -> None:
        self.w_recency = w_recency
        self.w_relevance = w_relevance
        self.w_importance = w_importance
        self.alpha = alpha
        self.half_life_hours = half_life_hours
        self.max_entries = max_entries
        self._store: list[MemoryEntry] = []

    # ── 점수 계산 ────────────────────────────────────────────────────

    def recency_score(self, entry: MemoryEntry, now: float | None = None) -> float:
        """α^(elapsed / half_life) — 시간이 지날수록 감쇠."""
        elapsed = entry.elapsed_hours(now)
        exponent = elapsed / self.half_life_hours
        return self.alpha ** exponent

    def relevance_score(
        self,
        entry: MemoryEntry,
        query_embedding: list[float] | None = None,
    ) -> float:
        """코사인 유사도. query_embedding 없으면 0.5 기본."""
        if not query_embedding or not entry.embedding:
            return 0.5
        return _cosine(query_embedding, entry.embedding)

    def score(
        self,
        entry: MemoryEntry,
        query_embedding: list[float] | None = None,
        now: float | None = None,
    ) -> float:
        """FinMem 종합 점수 = w_r·recency + w_v·relevance + w_i·importance."""
        r = self.recency_score(entry, now)
        v = self.relevance_score(entry, query_embedding)
        i = entry.importance
        return self.w_recency * r + self.w_relevance * v + self.w_importance * i

    # ── TradingAgents 패턴 ───────────────────────────────────────────

    def store_decision(
        self,
        decision: str,
        reason: str = "",
        confidence: float = 0.0,
        importance: float = 0.5,
        embedding: list[float] | None = None,
        created_at: float | None = None,
        **extra: Any,
    ) -> str:
        """새 결정 저장 → entry id 반환."""
        entry = MemoryEntry(
            decision=decision,
            reason=reason,
            confidence=confidence,
            importance=max(0.0, min(1.0, importance)),
            embedding=embedding or [],
            extra=extra,
        )
        if created_at is not None:
            entry.created_at = created_at

        self._store.append(entry)
        if len(self._store) > self.max_entries:
            self._evict()
        return entry.id

    def update_with_outcome(self, entry_id: str, outcome_pct: float) -> bool:
        """결과 반영 + importance 갱신.

        양의 결과 → importance 상승, 음의 결과 → 하락 (0~1 clamp).
        """
        for entry in self._store:
            if entry.id == entry_id:
                entry.outcome_pct = outcome_pct
                delta = outcome_pct / 100.0 * 0.2  # ±20% max shift
                entry.importance = max(0.0, min(1.0, entry.importance + delta))
                return True
        return False

    def get_past_context(
        self,
        top_k: int = 5,
        query_embedding: list[float] | None = None,
        now: float | None = None,
    ) -> list[MemoryEntry]:
        """FinMem 점수 상위 top_k 엔트리 반환."""
        scored = [
            (self.score(e, query_embedding, now), e)
            for e in self._store
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    # ── 내부 유틸 ────────────────────────────────────────────────────

    def _evict(self) -> None:
        """점수 최하위 항목 제거 (now 기준, query 없음)."""
        now = time.time()
        self._store.sort(
            key=lambda e: self.score(e, None, now),
        )
        self._store = self._store[len(self._store) // 5:]  # 하위 20% 제거

    def __len__(self) -> int:
        return len(self._store)


# ── 유틸 ─────────────────────────────────────────────────────────────

def _cosine(a: list[float], b: list[float]) -> float:
    """L2 정규화된 벡터의 코사인 유사도 (dot product)."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)
