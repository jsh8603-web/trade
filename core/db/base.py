"""core/db/base.py — DB 백엔드 추상 인터페이스.

Supabase REST 직접호출(75파일 산재)을 이 인터페이스 뒤로 통합한다.
호출자는 `from core.db import db` 후 db.insert/select/update/delete/rpc_match 만 사용.

PostgREST 필터 문법을 그대로 받는다 (L1 에서 sqlite_backend 가 SQL 로 변환):
    filters = {"created_at": "gte.2026-05-01", "status": "eq.done",
               "id": "in.(1,2,3)", "name": "like.*foo*"}
    order = "created_at.desc"  /  select = "id,created_at"  /  limit = 50
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional


class DBBackend(ABC):
    """모든 백엔드(sqlite/supabase)가 구현하는 공통 계약."""

    @abstractmethod
    def insert(self, table: str, row: dict, *, returning: bool = True) -> Optional[dict]:
        """단일 row 삽입. returning=True 면 삽입된 row(dict) 반환."""

    @abstractmethod
    def insert_many(self, table: str, rows: list) -> int:
        """다중 row 삽입. 삽입 개수 반환."""

    @abstractmethod
    def select(self, table: str, *, filters: Optional[dict] = None,
               order: Optional[str] = None, limit: Optional[int] = None,
               select: str = "*", offset: int = 0) -> list:
        """PostgREST 필터 문법으로 조회. row dict 리스트 반환."""

    @abstractmethod
    def update(self, table: str, filters: dict, patch: dict) -> int:
        """filters 매칭 row 를 patch 로 갱신. 갱신 개수 반환."""

    @abstractmethod
    def delete(self, table: str, filters: dict) -> int:
        """filters 매칭 row 삭제. 삭제 개수 반환."""

    @abstractmethod
    def rpc_match(self, table: str, embedding: list, *, column: str = "embedding",
                  k: int = 5, filters: Optional[dict] = None) -> list:
        """벡터 유사도 top-k 검색 (pgvector match_* 대체).
        sqlite_backend = BLOB(float32) + numpy 코사인. row + _similarity 필드 포함."""

    def execute_raw(self, sql: str, params: tuple = ()) -> Any:
        """비상용 raw SQL (어댑터로 못 덮는 케이스). 기본 미지원."""
        raise NotImplementedError("execute_raw not supported by this backend")

    def close(self) -> None:
        """리소스 정리(옵션)."""
        pass
