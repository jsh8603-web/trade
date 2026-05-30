"""core/db — DB 백엔드 추상화 + 백엔드 스위치.

사용:
    from core.db import db
    db.insert("decisions", {...})
    rows = db.select("decisions", filters={"created_at": "gte.2026-05-01"},
                     order="created_at.desc", limit=50)

백엔드 선택: 환경변수 INV_DB_BACKEND = sqlite(기본) | supabase
    sqlite   -> 로컬 data/inv.db (실 운영 기본)
    supabase -> 레거시 REST (전환 검증/롤백용)
"""
from __future__ import annotations
import os
import threading

from .base import DBBackend  # noqa: F401

_backend = None
_lock = threading.Lock()


def get_backend() -> DBBackend:
    """싱글톤 백엔드 반환 (lazy)."""
    global _backend
    if _backend is not None:
        return _backend
    with _lock:
        if _backend is not None:
            return _backend
        name = os.environ.get("INV_DB_BACKEND", "sqlite").lower()
        if name == "supabase":
            from .supabase_backend import SupabaseBackend
            _backend = SupabaseBackend()
        else:
            from .sqlite_backend import SQLiteBackend
            _backend = SQLiteBackend()
        return _backend


def reset_backend():
    """테스트용: 백엔드 싱글톤 초기화."""
    global _backend
    with _lock:
        if _backend is not None:
            try:
                _backend.close()
            except Exception:
                pass
        _backend = None


class _Proxy:
    """모듈 레벨 db.xxx() 위임 프록시 (lazy init)."""
    def __getattr__(self, name):
        return getattr(get_backend(), name)


db = _Proxy()

__all__ = ["db", "get_backend", "reset_backend", "DBBackend"]
