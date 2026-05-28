"""core/brain/rag_pit.py — RAG recall + PIT(Point-In-Time) causal-mask.

역할:
  - rag_pipeline.query_similar 에 as_of 파라미터 추가 배선
  - WHERE created_at < as_of (status='closed' AND exit_at <= as_of) PIT 필터
  - 백테스트 시 미래 데이터 누수 차단

설계:
  - PITFilter: mock RAG 결과 리스트에 as_of 마스크 적용 (단위 테스트 가능)
  - RagPitPipeline: rag_pipeline.RAGPipeline 래핑 + query_similar_pit() 추가
    (기존 RAGPipeline 본체 미변경 — SACRED)

SACRED:
  - RAGPipeline(rag_pipeline.py) 본체 코드 미변경
  - Supabase 실쓰기/실쿼리 금지(.env 없음) — mock으로 필터 로직 검증
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("brain.rag_pit")


# ── PITFilter ────────────────────────────────────────────────────────

class PITFilter:
    """Point-In-Time 필터 — as_of 이후 생성된 레코드를 검색에서 제외.

    검증 기준:
      - created_at < as_of  (백테스트 누수 차단)
      - status == 'closed'  AND exit_at <= as_of  (열린 포지션 제외)

    as_of 는 ISO 8601 문자열 또는 datetime.
    """

    def apply(
        self,
        records: list[dict[str, Any]],
        as_of: str | datetime | None = None,
    ) -> list[dict[str, Any]]:
        """레코드 리스트에 PIT 마스크 적용 → 통과 레코드만 반환."""
        if as_of is None:
            return records

        as_of_dt = self._parse_dt(as_of)
        result = []
        for rec in records:
            # created_at < as_of
            created_at = rec.get("created_at")
            if created_at and self._parse_dt(created_at) >= as_of_dt:
                continue  # 미래 레코드 제외

            # status='closed' AND exit_at <= as_of (선택 필드, 없으면 통과)
            status = rec.get("status")
            if status is not None and status != "closed":
                continue
            exit_at = rec.get("exit_at")
            if exit_at and self._parse_dt(exit_at) > as_of_dt:
                continue

            result.append(rec)
        return result

    @staticmethod
    def _parse_dt(value: str | datetime) -> datetime:
        if isinstance(value, datetime):
            return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# ── RagPitPipeline ───────────────────────────────────────────────────

class RagPitPipeline:
    """RAGPipeline 래퍼 — query_similar 에 as_of PIT 마스크 추가.

    기존 RAGPipeline 본체(rag_pipeline.py) 미변경 (SACRED).
    mock_search_fn 주입으로 Supabase 없이 단위 테스트 가능.
    """

    def __init__(
        self,
        inner: Any = None,
        mock_search_fn: Any = None,
    ) -> None:
        self._inner = inner        # RAGPipeline 인스턴스 (선택)
        self._mock_fn = mock_search_fn
        self._pit = PITFilter()

    def query_similar(
        self,
        query_text: str,
        top_k: int = 5,
        as_of: str | datetime | None = None,
    ) -> list[dict[str, Any]]:
        """as_of PIT 필터 포함 유사 검색.

        - mock_search_fn 주입 시: mock 결과에 PITFilter 적용
        - inner(RAGPipeline) 주입 시: inner.query_similar() 호출 후 PITFilter 적용
        - 둘 다 없으면: []
        """
        if self._mock_fn is not None:
            raw = self._mock_fn(query_text, top_k)
        elif self._inner is not None:
            raw = self._inner.query_similar(query_text, top_k)
        else:
            logger.warning("RagPitPipeline: search backend 없음 → []")
            raw = []

        filtered = self._pit.apply(raw, as_of=as_of)
        logger.debug(
            "RagPitPipeline.query_similar: raw=%d filtered=%d (as_of=%s)",
            len(raw), len(filtered), as_of,
        )
        return filtered
