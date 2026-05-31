"""core/db/sqlite_backend.py — 로컬 SQLite 백엔드.

INV_DB_BACKEND=sqlite (기본) 일 때 사용. data/inv.db 단일 파일.
- PostgREST 필터 -> SQL (core/db/filters.py)
- dict 값 중 list/dict -> JSON TEXT 자동 직렬화 (PG JSONB 흉내)
- 벡터 = float32 BLOB + numpy 코사인 top-k (pgvector match_* 대체)
- 최초 연결 시 core/db/schema.sql 자동 적용 (idempotent: CREATE IF NOT EXISTS)
"""
from __future__ import annotations
import os
import json
import sqlite3
import threading
from typing import Optional

from .base import DBBackend
from . import filters as F

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
_DEFAULT_DB = os.path.join(_ROOT, "data", "inv.db")


def _jsonify(v):
    """dict/list -> JSON 문자열, 그 외 그대로 (PG JSONB 컬럼 호환)."""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return v


def _row_to_dict(cur, row) -> dict:
    return {d[0]: row[i] for i, d in enumerate(cur.description)}


class SQLiteBackend(DBBackend):
    def __init__(self, db_path: Optional[str] = None, schema_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("INV_DB_PATH", _DEFAULT_DB)
        self.schema_path = schema_path or _SCHEMA
        self._lock = threading.RLock()
        self._pk_cache = {}
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=OFF;")
        self._apply_schema()

    def _apply_schema(self):
        if not os.path.exists(self.schema_path):
            return
        ddl = open(self.schema_path, encoding="utf-8").read()
        with self._lock:
            # CREATE IF NOT EXISTS 위주라 idempotent. ALTER ADD 중복은 개별 catch.
            for stmt in _iter_statements(ddl):
                try:
                    self._conn.execute(stmt)
                except sqlite3.OperationalError as e:
                    msg = str(e).lower()
                    if ("duplicate column" in msg or "already exists" in msg
                            or "already another table or index" in msg):
                        continue
                    raise
            self._conn.commit()

    # ---------- 쓰기 ----------
    def _text_pk(self, table):
        """default 없는 TEXT PRIMARY KEY 컬럼명. 없으면 None. (PG gen_random_uuid() 대체용). 캐싱."""
        if table in self._pk_cache:
            return self._pk_cache[table]
        found = None
        try:
            cur = self._conn.execute("PRAGMA table_info(%s)" % table)
            for _cid, name, ctype, _nn, dflt, pk in cur.fetchall():
                if pk and (ctype or "").upper().startswith("TEXT") and dflt is None:
                    found = name
                    break
        except sqlite3.Error:
            found = None
        self._pk_cache[table] = found
        return found

    def insert(self, table, row, *, returning=True):
        row = {k: _jsonify(v) for k, v in row.items()}
        pk = self._text_pk(table)
        if pk and pk not in row:
            import uuid
            row[pk] = str(uuid.uuid4())
        cols = list(row.keys())
        ph = ",".join("?" * len(cols))
        sql = "INSERT INTO %s (%s) VALUES (%s)" % (table, ",".join(cols), ph)
        with self._lock:
            cur = self._conn.execute(sql, tuple(row.values()))
            self._conn.commit()
            rid = cur.lastrowid
        if returning and rid is not None:
            got = self.select(table, filters={"rowid": "eq.%s" % rid}, limit=1)
            if got:
                return got[0]
            return {**row, "rowid": rid}
        return None

    def insert_many(self, table, rows):
        if not rows:
            return 0
        n = 0
        pk = self._text_pk(table)
        with self._lock:
            for r in rows:
                r = {k: _jsonify(v) for k, v in r.items()}
                if pk and pk not in r:
                    import uuid
                    r[pk] = str(uuid.uuid4())
                cols = list(r.keys())
                ph = ",".join("?" * len(cols))
                sql = "INSERT INTO %s (%s) VALUES (%s)" % (table, ",".join(cols), ph)
                self._conn.execute(sql, tuple(r.values()))
                n += 1
            self._conn.commit()
        return n

    # ---------- 읽기 ----------
    def select(self, table, *, filters=None, order=None, limit=None,
               select="*", offset=0):
        where, params = F.build_where(filters)
        order_sql = F.build_order(order)
        sql = "SELECT %s FROM %s%s%s" % (select, table, where, order_sql)
        if limit is not None:
            sql += " LIMIT %d" % int(limit)
            if offset:
                sql += " OFFSET %d" % int(offset)
        with self._lock:
            cur = self._conn.execute(sql, tuple(params))
            rows = [_row_to_dict(cur, r) for r in cur.fetchall()]
        return rows

    def update(self, table, filters, patch):
        patch = {k: _jsonify(v) for k, v in patch.items()}
        set_sql = ", ".join("%s = ?" % k for k in patch)
        where, wparams = F.build_where(filters)
        sql = "UPDATE %s SET %s%s" % (table, set_sql, where)
        with self._lock:
            cur = self._conn.execute(sql, tuple(patch.values()) + tuple(wparams))
            self._conn.commit()
            return cur.rowcount

    def delete(self, table, filters):
        where, params = F.build_where(filters)
        sql = "DELETE FROM %s%s" % (table, where)
        with self._lock:
            cur = self._conn.execute(sql, tuple(params))
            self._conn.commit()
            return cur.rowcount

    # ---------- 벡터 ----------
    def rpc_match(self, table, embedding, *, column="embedding", k=5, filters=None):
        import numpy as np
        q = np.asarray(embedding, dtype=np.float32)
        qn = float(np.linalg.norm(q)) or 1.0
        where, params = F.build_where(filters)
        sql = "SELECT * FROM %s%s" % (table, where)
        with self._lock:
            cur = self._conn.execute(sql, tuple(params))
            rows = [_row_to_dict(cur, r) for r in cur.fetchall()]
        scored = []
        for r in rows:
            blob = r.get(column)
            if blob is None:
                continue
            v = np.frombuffer(blob, dtype=np.float32) if isinstance(blob, (bytes, bytearray)) \
                else np.asarray(json.loads(blob), dtype=np.float32)
            if v.shape != q.shape:
                continue
            sim = float(np.dot(q, v) / (qn * (float(np.linalg.norm(v)) or 1.0)))
            r["_similarity"] = sim
            scored.append(r)
        scored.sort(key=lambda x: x["_similarity"], reverse=True)
        return scored[:k]

    def execute_raw(self, sql, params=()):
        with self._lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            if cur.description:
                return [_row_to_dict(cur, r) for r in cur.fetchall()]
            return cur.rowcount

    def close(self):
        with self._lock:
            self._conn.close()


def encode_vector(vec) -> bytes:
    """float 리스트 -> float32 BLOB (insert 시 사용)."""
    import numpy as np
    return np.asarray(vec, dtype=np.float32).tobytes()


def _iter_statements(ddl: str):
    """schema.sql 을 ; 단위로 분리 (단순; schema.sql 은 함수/달러쿼트 없음)."""
    buf = []
    for line in ddl.splitlines():
        s = line.strip()
        if s.startswith("--") or s.startswith("PRAGMA"):
            continue
        buf.append(line)
        if s.endswith(";"):
            stmt = "\n".join(buf).strip()
            if stmt:
                yield stmt
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        yield tail
