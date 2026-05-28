"""SO-5 테스트: RAG recall + PIT causal-mask.

검증기준:
- PIT 마스크 결함주입(as_of 이후 생성 결정 mock → 검색 제외) 어서션 PASS
- recall 동작(mock RAG, status=closed 필터) PASS
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from core.brain.rag_pit import PITFilter, RagPitPipeline


# ── PITFilter 기본 ────────────────────────────────────────────────────

def test_pit_filter_no_as_of():
    """as_of=None → 필터 없이 전체 반환."""
    f = PITFilter()
    records = [{"id": "1", "created_at": "2025-01-01T00:00:00Z"}]
    assert f.apply(records, as_of=None) == records


def test_pit_filter_empty_records():
    f = PITFilter()
    assert f.apply([], as_of="2025-06-01T00:00:00Z") == []


# ── 결함주입: as_of 이후 레코드 제외 ────────────────────────────────

def test_pit_mask_future_record_excluded():
    """as_of 이후 생성된 레코드 → 검색에서 제외 (PIT 핵심)."""
    f = PITFilter()
    as_of = "2025-05-01T00:00:00Z"

    records = [
        {"id": "past", "created_at": "2025-04-01T00:00:00Z"},    # 통과
        {"id": "future", "created_at": "2025-06-01T00:00:00Z"},  # 제외
        {"id": "equal", "created_at": "2025-05-01T00:00:00Z"},   # 동일시각 제외(< 조건)
    ]
    result = f.apply(records, as_of=as_of)
    ids = [r["id"] for r in result]
    assert "past" in ids
    assert "future" not in ids, "미래 레코드가 필터되지 않음"
    assert "equal" not in ids, "동일 시각 레코드가 필터되지 않음(< 조건)"


def test_pit_mask_all_past():
    """모두 과거 레코드 → 전체 통과."""
    f = PITFilter()
    as_of = "2025-12-01T00:00:00Z"
    records = [
        {"id": "a", "created_at": "2025-01-01T00:00:00Z"},
        {"id": "b", "created_at": "2025-06-01T00:00:00Z"},
    ]
    result = f.apply(records, as_of=as_of)
    assert len(result) == 2


def test_pit_mask_all_future():
    """모두 미래 레코드 → 전체 제외."""
    f = PITFilter()
    as_of = "2024-01-01T00:00:00Z"
    records = [
        {"id": "a", "created_at": "2025-01-01T00:00:00Z"},
        {"id": "b", "created_at": "2025-06-01T00:00:00Z"},
    ]
    result = f.apply(records, as_of=as_of)
    assert len(result) == 0


# ── status='closed' 필터 ─────────────────────────────────────────────

def test_pit_status_closed_filter():
    """status='open' 레코드 제외."""
    f = PITFilter()
    as_of = "2025-12-01T00:00:00Z"
    records = [
        {"id": "closed_rec", "created_at": "2025-01-01T00:00:00Z", "status": "closed"},
        {"id": "open_rec",   "created_at": "2025-01-01T00:00:00Z", "status": "open"},
        {"id": "no_status",  "created_at": "2025-01-01T00:00:00Z"},  # status 없으면 통과
    ]
    result = f.apply(records, as_of=as_of)
    ids = [r["id"] for r in result]
    assert "closed_rec" in ids
    assert "open_rec" not in ids
    assert "no_status" in ids


def test_pit_exit_at_filter():
    """exit_at > as_of → 제외 (포지션 미종료)."""
    f = PITFilter()
    as_of = "2025-05-01T00:00:00Z"
    records = [
        {
            "id": "closed_before",
            "created_at": "2025-01-01T00:00:00Z",
            "status": "closed",
            "exit_at": "2025-04-01T00:00:00Z",  # 통과
        },
        {
            "id": "closed_after",
            "created_at": "2025-01-01T00:00:00Z",
            "status": "closed",
            "exit_at": "2025-06-01T00:00:00Z",  # 제외
        },
    ]
    result = f.apply(records, as_of=as_of)
    ids = [r["id"] for r in result]
    assert "closed_before" in ids
    assert "closed_after" not in ids


# ── datetime 파싱 ─────────────────────────────────────────────────────

def test_pit_datetime_object_as_of():
    """as_of 를 datetime 객체로 전달해도 동작."""
    f = PITFilter()
    as_of = datetime(2025, 5, 1, tzinfo=timezone.utc)
    records = [
        {"id": "past",   "created_at": "2025-04-01T00:00:00Z"},
        {"id": "future", "created_at": "2025-06-01T00:00:00Z"},
    ]
    result = f.apply(records, as_of=as_of)
    assert len(result) == 1
    assert result[0]["id"] == "past"


# ── RagPitPipeline — mock 검색 함수 주입 ────────────────────────────

def _make_mock_records() -> list[dict[str, Any]]:
    return [
        {"id": "old", "created_at": "2025-01-01T00:00:00Z", "similarity": 0.9},
        {"id": "new", "created_at": "2025-07-01T00:00:00Z", "similarity": 0.8},
    ]


def test_rag_pit_pipeline_no_as_of():
    """as_of=None → 전체 mock 결과 반환."""
    pipeline = RagPitPipeline(mock_search_fn=lambda q, k: _make_mock_records())
    result = pipeline.query_similar("bitcoin", top_k=5)
    assert len(result) == 2


def test_rag_pit_pipeline_with_as_of():
    """as_of 지정 → PIT 필터 적용."""
    pipeline = RagPitPipeline(mock_search_fn=lambda q, k: _make_mock_records())
    result = pipeline.query_similar(
        "bitcoin", top_k=5, as_of="2025-03-01T00:00:00Z"
    )
    assert len(result) == 1
    assert result[0]["id"] == "old"


def test_rag_pit_pipeline_future_excluded():
    """as_of 이후 레코드 → 완전 제외."""
    pipeline = RagPitPipeline(mock_search_fn=lambda q, k: _make_mock_records())
    result = pipeline.query_similar(
        "bitcoin", top_k=5, as_of="2020-01-01T00:00:00Z"
    )
    assert result == []


def test_rag_pit_pipeline_no_backend():
    """backend 없음 → []."""
    pipeline = RagPitPipeline()
    result = pipeline.query_similar("test", top_k=3, as_of=None)
    assert result == []


def test_rag_pit_pipeline_status_closed_only():
    """status=closed만 통과하는 mock."""
    records = [
        {"id": "ok",  "created_at": "2025-01-01T00:00:00Z", "status": "closed"},
        {"id": "bad", "created_at": "2025-01-01T00:00:00Z", "status": "open"},
    ]
    pipeline = RagPitPipeline(mock_search_fn=lambda q, k: records)
    result = pipeline.query_similar("test", as_of="2025-12-01T00:00:00Z")
    assert len(result) == 1
    assert result[0]["id"] == "ok"
