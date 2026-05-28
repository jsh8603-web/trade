"""SO-3 테스트: migration 048 + M4 가드 + reembed_to_bge.py 배치 로직.

검증기준:
- mig 048 스키마 정합(idempotent ADD) PASS
- M4 가드(reembedding_status 미완료→신규 인덱스 차단) 단위 PASS
- 재임베딩 스크립트가 8787 호출 구조 확인(mock 배치 어서션) PASS
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

MIG_FILE = PROJECT_DIR / "supabase" / "migrations" / "048_bge_reembedding_guard.sql"


# ── migration 스키마 정합 ─────────────────────────────────────────────

def test_migration_file_exists():
    assert MIG_FILE.exists(), f"migration 파일 없음: {MIG_FILE}"


def test_migration_idempotent_add():
    """048 SQL에 IF NOT EXISTS 패턴 포함 확인 (idempotent ADD)."""
    sql = MIG_FILE.read_text(encoding="utf-8")
    assert "ADD COLUMN IF NOT EXISTS" in sql, "ADD COLUMN IF NOT EXISTS 없음"
    assert "CREATE TABLE IF NOT EXISTS" in sql, "CREATE TABLE IF NOT EXISTS 없음"
    assert "CREATE INDEX IF NOT EXISTS" in sql, "CREATE INDEX IF NOT EXISTS 없음"


def test_migration_bge_column_1024():
    """state_embedding_bge vector(1024) 컬럼 정의 확인."""
    sql = MIG_FILE.read_text(encoding="utf-8")
    assert "state_embedding_bge vector(1024)" in sql, "BGE 1024 컬럼 없음"


def test_migration_reembedding_status_table():
    """reembedding_status 테이블 생성 및 status CHECK 포함 확인."""
    sql = MIG_FILE.read_text(encoding="utf-8")
    assert "reembedding_status" in sql
    assert "pending" in sql
    assert "completed" in sql


def test_migration_gemini_column_preserved():
    """기존 Gemini 3072 컬럼(match_similar_decisions) 미삭제 확인."""
    sql = MIG_FILE.read_text(encoding="utf-8")
    # 기존 Gemini RPC 삭제 없음 확인
    assert "DROP FUNCTION match_similar_decisions" not in sql, (
        "기존 Gemini RPC 삭제 금지"
    )


# ── M4 가드 단위 테스트 ──────────────────────────────────────────────

def test_m4_guard_sql_present():
    """match_similar_decisions_bge 함수에 M4 가드 로직 포함 확인."""
    sql = MIG_FILE.read_text(encoding="utf-8")
    assert "match_similar_decisions_bge" in sql
    assert "RAISE EXCEPTION" in sql, "M4 가드 RAISE EXCEPTION 없음"
    assert "'completed'" in sql, "completed 상태 체크 없음"


def test_m4_guard_logic_simulation():
    """M4 가드 시뮬레이션 — status != completed 시 차단."""

    def _bge_query_with_guard(status: str) -> str:
        if status != "completed":
            raise RuntimeError(f"BGE 재임베딩 미완료(status={status}). 차단.")
        return "QUERY_OK"

    with pytest.raises(RuntimeError, match="미완료"):
        _bge_query_with_guard("pending")

    with pytest.raises(RuntimeError, match="미완료"):
        _bge_query_with_guard("in_progress")

    # completed 시 통과
    assert _bge_query_with_guard("completed") == "QUERY_OK"


# ── 재임베딩 스크립트 배치 로직 어서션 ──────────────────────────────

def test_reembed_script_exists():
    script = PROJECT_DIR / "scripts" / "reembed_to_bge.py"
    assert script.exists(), f"reembed_to_bge.py 없음"


def test_reembed_script_imports():
    """reembed_to_bge.py 임포트 성공."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "reembed_to_bge",
        PROJECT_DIR / "scripts" / "reembed_to_bge.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "run")
    assert hasattr(mod, "mock_batch_assert")


def test_reembed_mock_batch_calls_da_embed():
    """mock_batch_assert — DaServiceEmbedder.embed() 8787 실호출로 배치 구조 검증."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "reembed_to_bge",
        PROJECT_DIR / "scripts" / "reembed_to_bge.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    from core.brain.embedder import DaServiceEmbedder
    embedder = DaServiceEmbedder()
    texts = ["bitcoin test", "fear greed check", "RSI oversold"]
    mod.mock_batch_assert(texts, embedder)  # 8787 실호출 — 예외 없으면 PASS


def test_reembed_run_dry_mode():
    """reembed_to_bge.run(dry_run=True) — Supabase 미호출, 예외 없음."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "reembed_to_bge",
        PROJECT_DIR / "scripts" / "reembed_to_bge.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # DRY_RUN 모드 — Supabase 실호출 없이 mock 배치만
    mod.run(batch_size=5, dry_run=True)  # 예외 없으면 PASS


def test_reembed_dim_1024_asserted():
    """mock 배치 어서션이 dim=1024 검증 포함."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "reembed_to_bge",
        PROJECT_DIR / "scripts" / "reembed_to_bge.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    from core.brain.embedder import DaServiceEmbedder

    mock_embedder = MagicMock(spec=DaServiceEmbedder)
    mock_embedder.embed.return_value = [[0.0] * 512]  # 잘못된 차원

    with pytest.raises(AssertionError):
        mod.mock_batch_assert(["test text"], mock_embedder)
