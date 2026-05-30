"""test_db_adapter_smoke.py — core/db SQLite 어댑터 L0 동작 검증.

schema 적용 / CRUD / PostgREST 필터 변환 / 벡터 코사인 top-k 전부 실파일로 확인.
"""
import os
import tempfile
import struct
import pytest

from core.db import filters as F
from core.db.sqlite_backend import SQLiteBackend, encode_vector


@pytest.fixture
def be(tmp_path):
    b = SQLiteBackend(db_path=str(tmp_path / "t.db"))
    yield b
    b.close()


# ---------- 필터 변환 ----------
def test_filter_operators():
    w, p = F.build_where({"created_at": "gte.2026-05-01", "status": "eq.done"})
    assert "created_at >= ?" in w and "status = ?" in w
    assert p == ["2026-05-01", "done"]

    w, p = F.build_where({"id": "in.(1,2,3)"})
    assert "id IN (?,?,?)" in w and p == ["1", "2", "3"]

    w, p = F.build_where({"name": "like.*btc*"})
    assert "LIKE ?" in w and p == ["%btc%"]

    w, p = F.build_where({"x": "is.null"})
    assert "x IS NULL" in w

    w, p = F.build_where({"flag": "is.true"})
    assert p == [1]


def test_order():
    assert F.build_order("created_at.desc") == " ORDER BY created_at DESC"
    assert F.build_order("a.asc,b.desc") == " ORDER BY a ASC, b DESC"


# ---------- schema ----------
def test_schema_applied(be):
    rows = be.execute_raw(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='decisions'")
    assert rows and rows[0]["name"] == "decisions"


# ---------- CRUD ----------
def test_insert_select_update_delete(be):
    be.insert("decisions", {"market": "KRW-BTC", "decision": "buy",
                            "reason": "test", "confidence": 0.7})
    got = be.select("decisions", filters={"decision": "eq.buy"}, limit=10)
    assert len(got) == 1 and got[0]["reason"] == "test"

    n = be.update("decisions", {"decision": "eq.buy"}, {"confidence": 0.9})
    assert n == 1
    got = be.select("decisions", filters={"decision": "eq.buy"})
    assert abs(got[0]["confidence"] - 0.9) < 1e-9

    n = be.delete("decisions", {"decision": "eq.buy"})
    assert n == 1
    assert be.select("decisions", filters={"decision": "eq.buy"}) == []


def test_json_column_roundtrip(be):
    be.insert("decisions", {"market": "KRW-BTC", "decision": "hold", "reason": "j",
                            "market_data_snapshot": {"rsi": 55, "sma": [1, 2]}})
    got = be.select("decisions", filters={"decision": "eq.hold"})
    # JSONB->TEXT 저장이라 문자열로 반환 (호출자가 json.loads)
    assert '"rsi": 55' in got[0]["market_data_snapshot"]


# ---------- 벡터 ----------
def test_rpc_match_cosine(be):
    # rag_analysis_vectors 테이블에 embedding BLOB 3개 삽입 (실제 컬럼 analysis_text)
    be.insert("rag_analysis_vectors",
              {"analysis_text": "a", "embedding": encode_vector([1.0, 0.0, 0.0])}, returning=False)
    be.insert("rag_analysis_vectors",
              {"analysis_text": "b", "embedding": encode_vector([0.0, 1.0, 0.0])}, returning=False)
    be.insert("rag_analysis_vectors",
              {"analysis_text": "c", "embedding": encode_vector([0.9, 0.1, 0.0])}, returning=False)
    res = be.rpc_match("rag_analysis_vectors", [1.0, 0.0, 0.0], k=2)
    assert len(res) == 2
    # 가장 유사한 것은 'a' (정확 일치)
    assert res[0]["analysis_text"] == "a"
    assert res[0]["_similarity"] > res[1]["_similarity"]
    # 두번째는 'c' (cos≈0.994) > 'b' (cos=0)
    assert res[1]["analysis_text"] == "c"
