"""core/db/supabase_backend.py — 레거시 Supabase REST 백엔드 (롤백/검증용).

INV_DB_BACKEND=supabase 일 때만 사용. 기본 운영은 sqlite_backend.
기존 75파일이 쓰던 PostgREST REST 호출을 동일 인터페이스로 래핑한다.
실 운영은 SQLite 로 이전했으므로 이 백엔드는 전환 전후 비교/긴급 롤백 목적.
"""
from __future__ import annotations
import os
from typing import Optional

import requests

from .base import DBBackend

_REST_TIMEOUT = float(os.environ.get("SUPABASE_REST_TIMEOUT", "15"))


class SupabaseBackend(DBBackend):
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = (url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.key = key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") \
            or os.environ.get("SUPABASE_KEY", "")
        if not self.url or not self.key:
            raise ValueError("SupabaseBackend: SUPABASE_URL / KEY 미설정")
        self._s = requests.Session()
        self._s.headers.update({
            "apikey": self.key,
            "Authorization": "Bearer %s" % self.key,
            "Content-Type": "application/json",
        })

    def _u(self, table: str) -> str:
        return "%s/rest/v1/%s" % (self.url, table)

    @staticmethod
    def _params(filters, order, limit, select, offset):
        p = {"select": select}
        for col, expr in (filters or {}).items():
            p[col] = expr if isinstance(expr, str) else str(expr)
        if order:
            p["order"] = order
        if limit is not None:
            p["limit"] = str(limit)
        if offset:
            p["offset"] = str(offset)
        return p

    def insert(self, table, row, *, returning=True):
        h = {"Prefer": "return=representation"} if returning else {}
        r = self._s.post(self._u(table), json=row, headers=h, timeout=_REST_TIMEOUT)
        r.raise_for_status()
        if returning and r.text:
            data = r.json()
            return data[0] if isinstance(data, list) and data else data
        return None

    def insert_many(self, table, rows):
        if not rows:
            return 0
        r = self._s.post(self._u(table), json=rows, timeout=_REST_TIMEOUT)
        r.raise_for_status()
        return len(rows)

    def select(self, table, *, filters=None, order=None, limit=None,
               select="*", offset=0):
        r = self._s.get(self._u(table),
                        params=self._params(filters, order, limit, select, offset),
                        timeout=_REST_TIMEOUT)
        r.raise_for_status()
        return r.json()

    def update(self, table, filters, patch):
        r = self._s.patch(self._u(table),
                          params=self._params(filters, None, None, "*", 0),
                          json=patch,
                          headers={"Prefer": "return=representation"},
                          timeout=_REST_TIMEOUT)
        r.raise_for_status()
        return len(r.json()) if r.text else 0

    def delete(self, table, filters):
        r = self._s.delete(self._u(table),
                           params=self._params(filters, None, None, "*", 0),
                           headers={"Prefer": "return=representation"},
                           timeout=_REST_TIMEOUT)
        r.raise_for_status()
        return len(r.json()) if r.text else 0

    def rpc_match(self, table, embedding, *, column="embedding", k=5, filters=None):
        # 레거시: pgvector match_* RPC 호출 (테이블별 RPC 이름 규약 필요).
        raise NotImplementedError(
            "SupabaseBackend.rpc_match 은 테이블별 RPC 이름이 필요 — sqlite_backend 사용 권장")

    def close(self):
        self._s.close()
