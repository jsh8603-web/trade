"""reembed_to_bge.py — 기존 Gemini 3072 임베딩 → BGE-m3 1024 재임베딩 배치.

역할:
  1. decisions 테이블에서 embedding_text 가 있는 레코드를 배치 로드
  2. da 8787 /embed 로 BGE-m3 1024 벡터 생성
  3. decisions.state_embedding_bge 에 업데이트
  4. reembedding_status 테이블 진행률 기록 (M4 가드 연동)

SACRED:
  - Supabase 실쓰기 금지(.env 없음) — mock 모드로 배치 로직 어서션
  - da 8787 실호출 허용 (EMBED_URL 기본값)
  - DRY_RUN=true 시 DB write skip

사용법:
  python scripts/reembed_to_bge.py [--batch-size N] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from core.brain.embedder import DaServiceEmbedder

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("reembed")

EMBED_URL = os.environ.get("EMBED_URL", "http://127.0.0.1:8787")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"

DEFAULT_BATCH = 50


def _supabase_request(
    method: str,
    path: str,
    payload: Any = None,
    params: str = "",
) -> Any:
    """Supabase REST 호출 래퍼 (mock-only 시 RuntimeError)."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "Supabase 미설정(.env 없음). DRY_RUN 모드 또는 .env 설정 후 실행."
        )
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    if params:
        url += f"?{params}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        method=method,
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_pending_rows(batch_size: int, offset: int) -> list[dict[str, Any]]:
    """embedding_text 있고 state_embedding_bge 없는 레코드 조회."""
    params = (
        f"select=id,embedding_text"
        f"&embedding_text=not.is.null"
        f"&state_embedding_bge=is.null"
        f"&limit={batch_size}&offset={offset}"
    )
    return _supabase_request("GET", "decisions", params=params)


def update_bge_vector(row_id: str, vector: list[float]) -> None:
    """decisions.state_embedding_bge 업데이트."""
    _supabase_request(
        "PATCH",
        f"decisions?id=eq.{row_id}",
        payload={"state_embedding_bge": vector},
    )


def update_reembedding_status(status: str, done: int, total: int | None = None) -> None:
    """reembedding_status 테이블 진행률 기록."""
    payload: dict[str, Any] = {"status": status, "done_rows": done}
    if total is not None:
        payload["total_rows"] = total
    if status == "in_progress" and done == 0:
        payload["started_at"] = "now()"
    if status == "completed":
        payload["completed_at"] = "now()"
    payload["updated_at"] = "now()"
    _supabase_request(
        "PATCH",
        "reembedding_status?target=eq.decisions.state_embedding_bge",
        payload=payload,
    )


def mock_batch_assert(texts: list[str], embedder: DaServiceEmbedder) -> None:
    """mock 배치 로직 어서션 — da 8787 실호출로 벡터 구조 검증."""
    vecs = embedder.embed(texts)
    assert len(vecs) == len(texts), f"벡터 수 불일치: {len(vecs)} != {len(texts)}"
    assert all(len(v) == 1024 for v in vecs), "1024차원 아님"
    logger.info(
        "[MOCK] %d 텍스트 → %d 벡터 (dim=%d) — DB write skip (DRY_RUN/mock-only)",
        len(texts), len(vecs), len(vecs[0]) if vecs else 0,
    )


def run(batch_size: int = DEFAULT_BATCH, dry_run: bool = True) -> None:
    embedder = DaServiceEmbedder(base_url=EMBED_URL)
    health = embedder.health()
    logger.info("da embed 서비스 상태: %s", health)
    assert health.get("embed_dim") == 1024, f"embed_dim 불일치: {health}"

    if dry_run or not SUPABASE_URL:
        logger.info(
            "DRY_RUN / mock-only 모드 — 샘플 텍스트로 배치 로직 어서션"
        )
        sample_texts = (
            ["bitcoin rally 10% today", "fear greed index at 25 extreme fear", "RSI oversold below 30"]
            + [f"sample_{i}" for i in range(batch_size - 3)]
        )
        sample_texts = sample_texts[:batch_size]
        mock_batch_assert(sample_texts, embedder)
        logger.info("mock 배치 어서션 PASS")
        return

    logger.info("Supabase 연결 확인 중...")
    update_reembedding_status("in_progress", 0)

    offset = 0
    done = 0
    total: int | None = None

    while True:
        rows = fetch_pending_rows(batch_size, offset)
        if not rows:
            break

        texts = [r["embedding_text"] for r in rows]
        vecs = embedder.embed(texts)

        for row, vec in zip(rows, vecs):
            update_bge_vector(row["id"], vec)
            done += 1

        logger.info("진행: %d 행 완료", done)
        update_reembedding_status("in_progress", done, total)
        offset += batch_size

    update_reembedding_status("completed", done, done)
    logger.info("재임베딩 완료: %d 행", done)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini 3072 → BGE-m3 1024 재임베딩")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH)
    parser.add_argument("--dry-run", action="store_true", default=DRY_RUN)
    args = parser.parse_args()
    run(batch_size=args.batch_size, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
