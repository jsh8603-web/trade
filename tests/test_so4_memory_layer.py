"""SO-4 테스트: core/brain/memory_layer.py FinMem식 계층 메모리.

검증기준:
- FinMem 점수식(recency/relevance/importance + decay α^경과) 단위
- 시계 freeze 로 동일 입력 동일 점수
- 경과 클수록 recency 감쇠 어서션
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from core.brain.memory_layer import (
    ALPHA_DECAY,
    HALF_LIFE_HOURS,
    W_IMPORTANCE,
    W_RECENCY,
    W_RELEVANCE,
    MemoryEntry,
    MemoryLayer,
    _cosine,
)


# ── 기본 구조 테스트 ─────────────────────────────────────────────────

def test_import_ok():
    from core.brain.memory_layer import MemoryLayer, MemoryEntry  # noqa: F401


def test_default_weights_sum():
    """w_recency + w_relevance + w_importance == 1.0"""
    total = W_RECENCY + W_RELEVANCE + W_IMPORTANCE
    assert abs(total - 1.0) < 1e-9, f"가중치 합 {total} != 1.0"


def test_memory_layer_instantiation():
    ml = MemoryLayer()
    assert len(ml) == 0


# ── 시계 freeze — 동일 입력 동일 점수 ───────────────────────────────

def test_score_deterministic_with_frozen_clock():
    """시계 freeze(now 고정) 시 동일 입력 → 동일 점수."""
    ml = MemoryLayer()
    now = time.time()
    entry = MemoryEntry(importance=0.7, created_at=now - 3600)

    s1 = ml.score(entry, query_embedding=None, now=now)
    s2 = ml.score(entry, query_embedding=None, now=now)
    assert s1 == s2, f"점수 불일치: {s1} != {s2}"


def test_score_same_embedding_frozen_clock():
    """임베딩 동일 + 시계 freeze → 점수 동일."""
    ml = MemoryLayer()
    now = time.time()
    emb = [0.6, 0.8]
    entry = MemoryEntry(importance=0.5, embedding=emb, created_at=now - 7200)

    s1 = ml.score(entry, query_embedding=emb, now=now)
    s2 = ml.score(entry, query_embedding=emb, now=now)
    assert abs(s1 - s2) < 1e-12


# ── 경과 클수록 recency 감쇠 ─────────────────────────────────────────

def test_recency_decreases_with_elapsed():
    """elapsed 증가 → recency 감소."""
    ml = MemoryLayer()
    now = time.time()

    entry_fresh = MemoryEntry(created_at=now - 1800)       # 0.5h ago
    entry_old   = MemoryEntry(created_at=now - 48 * 3600)  # 48h ago

    r_fresh = ml.recency_score(entry_fresh, now)
    r_old   = ml.recency_score(entry_old, now)
    assert r_fresh > r_old, f"fresh({r_fresh}) <= old({r_old})"


def test_recency_half_life():
    """elapsed = half_life_hours → recency ≈ alpha (0.5 기본)."""
    ml = MemoryLayer(alpha=ALPHA_DECAY, half_life_hours=HALF_LIFE_HOURS)
    now = time.time()
    entry = MemoryEntry(created_at=now - HALF_LIFE_HOURS * 3600)
    r = ml.recency_score(entry, now)
    assert abs(r - ALPHA_DECAY) < 1e-6, f"반감기 recency {r} != {ALPHA_DECAY}"


def test_recency_at_creation():
    """elapsed = 0 → recency = 1.0 (α^0)."""
    ml = MemoryLayer()
    now = time.time()
    entry = MemoryEntry(created_at=now)
    r = ml.recency_score(entry, now)
    assert abs(r - 1.0) < 1e-9


# ── 점수식 수치 검증 ──────────────────────────────────────────────────

def test_score_formula():
    """score = w_r·recency + w_v·relevance + w_i·importance 수치 확인."""
    ml = MemoryLayer(w_recency=0.4, w_relevance=0.35, w_importance=0.25)
    now = time.time()
    # elapsed=0 → recency=1.0, relevance=0.5(no emb), importance=0.8
    entry = MemoryEntry(importance=0.8, created_at=now)
    s = ml.score(entry, query_embedding=None, now=now)
    expected = 0.4 * 1.0 + 0.35 * 0.5 + 0.25 * 0.8
    assert abs(s - expected) < 1e-9, f"{s} != {expected}"


def test_score_with_relevance():
    """임베딩 제공 시 relevance 반영."""
    ml = MemoryLayer()
    now = time.time()
    emb = [1.0, 0.0]
    entry = MemoryEntry(importance=0.5, embedding=[1.0, 0.0], created_at=now)
    s = ml.score(entry, query_embedding=emb, now=now)
    # relevance = cosine([1,0],[1,0]) = 1.0
    # recency=1.0 (elapsed=0), importance=0.5
    expected = W_RECENCY * 1.0 + W_RELEVANCE * 1.0 + W_IMPORTANCE * 0.5
    assert abs(s - expected) < 1e-9


# ── TradingAgents 패턴 ───────────────────────────────────────────────

def test_store_decision_returns_id():
    ml = MemoryLayer()
    eid = ml.store_decision("buy", reason="RSI oversold", confidence=0.8)
    assert isinstance(eid, str) and len(eid) > 0
    assert len(ml) == 1


def test_update_with_outcome_raises_importance():
    ml = MemoryLayer()
    eid = ml.store_decision("buy", importance=0.5)
    result = ml.update_with_outcome(eid, outcome_pct=10.0)
    assert result is True
    entry = ml._store[0]
    assert entry.outcome_pct == 10.0
    assert entry.importance > 0.5  # 양의 결과 → importance 상승


def test_update_with_outcome_lowers_importance():
    ml = MemoryLayer()
    eid = ml.store_decision("sell", importance=0.5)
    ml.update_with_outcome(eid, outcome_pct=-10.0)
    assert ml._store[0].importance < 0.5


def test_update_with_unknown_id():
    ml = MemoryLayer()
    result = ml.update_with_outcome("nonexistent-id", outcome_pct=5.0)
    assert result is False


def test_get_past_context_top_k():
    ml = MemoryLayer()
    now = time.time()
    for i in range(10):
        ml.store_decision("buy", importance=i / 10.0, created_at=now)
    top = ml.get_past_context(top_k=3, now=now)
    assert len(top) == 3


def test_get_past_context_score_order():
    """get_past_context 반환은 FinMem 점수 내림차순."""
    ml = MemoryLayer()
    now = time.time()
    ml.store_decision("hold", importance=0.1, created_at=now)
    ml.store_decision("buy", importance=0.9, created_at=now)
    top = ml.get_past_context(top_k=2, now=now)
    scores = [ml.score(e, None, now) for e in top]
    assert scores[0] >= scores[1]


# ── _cosine 단위 ──────────────────────────────────────────────────────

def test_cosine_identical_vectors():
    assert abs(_cosine([1.0, 0.0], [1.0, 0.0]) - 1.0) < 1e-9


def test_cosine_orthogonal():
    assert abs(_cosine([1.0, 0.0], [0.0, 1.0])) < 1e-9


def test_cosine_opposite():
    assert abs(_cosine([1.0, 0.0], [-1.0, 0.0]) - (-1.0)) < 1e-9


def test_cosine_empty():
    assert _cosine([], []) == 0.0


def test_cosine_dim_mismatch():
    assert _cosine([1.0], [1.0, 0.0]) == 0.0
