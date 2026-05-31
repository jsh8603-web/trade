"""core/db/filters.py — PostgREST 필터 문법 -> SQLite WHERE 절 변환.

L1 핵심 엔진. Supabase REST 호출 75파일이 쓰는 필터 문법을 SQL 로 1:1 변환.

지원 연산자(PostgREST):
    eq.  ne.  gt.  gte.  lt.  lte.       비교
    like.  ilike.   (* -> %)            패턴
    in.(a,b,c)                          IN
    is.null / is.true / is.false        IS
    cs. / cd.                           (배열 contains — TEXT 저장이라 LIKE 근사)
    not.<op>.<val>                      부정 prefix
값에 NOW()-INTERVAL 류는 caller 가 ISO 문자열로 넘기는 것을 전제(어댑터 docstring).
"""
from __future__ import annotations
from typing import Optional

_OPS = {
    "eq": "=", "ne": "!=", "neq": "!=", "gt": ">", "gte": ">=", "lt": "<", "lte": "<=",
}

# PG timestamptz 컬럼 — SQLite 는 TEXT 문자열 비교라 'YYYY-MM-DD HH:MM:SS'(공백) vs
# ISO 'T'/타임존 포맷이 어긋나면 비교가 깨진다. 시간 컬럼은 datetime() 으로 정규화 비교.
_TIME_COLS = {
    "created_at", "updated_at", "evaluated_at", "last_checked", "last_updated",
    "last_accessed", "entry_time", "exit_time", "trade_date", "applied_at",
    "ts", "time", "datetime",
}


def _is_time_col(col: str) -> bool:
    c = col.lower()
    return c.endswith("_at") or c.endswith("_time") or "timestamp" in c or c in _TIME_COLS


def _one(col: str, expr: str):
    """단일 (col, 'op.value') -> (sql_fragment, params list)."""
    if "." not in expr:
        # 연산자 없으면 eq 로 간주
        return "%s = ?" % col, [expr]
    op, _, val = expr.partition(".")
    op = op.lower()

    neg = False
    if op == "not":
        neg = True
        op2, _, val = val.partition(".")
        op = op2.lower()

    if op in _OPS:
        if op in ("eq", "ne", "neq") and val.lower() in ("true", "false"):
            # PG boolean 컬럼: eq.true/eq.false -> SQLite 1/0 (TEXT 'false' 비교 깨짐 방지)
            frag = "%s %s ?" % (col, _OPS[op])
            params = [1 if val.lower() == "true" else 0]
        elif op in ("gt", "gte", "lt", "lte") and _is_time_col(col):
            # PG timestamptz -> SQLite TEXT 비교 깨짐 방지: 양변 datetime() 정규화
            frag = "datetime(%s) %s datetime(?)" % (col, _OPS[op])
            params = [val]
        else:
            frag = "%s %s ?" % (col, _OPS[op])
            params = [val]
    elif op == "like":
        frag = "%s LIKE ?" % col
        params = [val.replace("*", "%")]
    elif op == "ilike":
        frag = "%s LIKE ? COLLATE NOCASE" % col
        params = [val.replace("*", "%")]
    elif op == "in":
        inner = val.strip()
        if inner.startswith("(") and inner.endswith(")"):
            inner = inner[1:-1]
        items = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
        if not items:
            return "0=1", []  # 빈 IN = 항상 거짓
        ph = ",".join("?" * len(items))
        frag = "%s IN (%s)" % (col, ph)
        params = items
    elif op == "is":
        v = val.lower()
        if v == "null":
            frag = "%s IS NULL" % col
        elif v in ("true", "false"):
            frag = "%s = ?" % col
            return ("NOT (%s)" % frag if neg else frag), [1 if v == "true" else 0]
        else:
            frag = "%s IS ?" % col
            params = [val]
            return ("NOT (%s)" % frag if neg else frag), params
        return ("NOT (%s)" % frag if neg else frag), []
    elif op in ("cs", "cd"):
        # 배열/JSON contains 근사 (TEXT 저장) — LIKE
        frag = "%s LIKE ?" % col
        params = ["%" + val.strip("{}()[]") + "%"]
    else:
        # 미지원 연산자 -> eq fallback
        frag = "%s = ?" % col
        params = [expr]

    if neg:
        frag = "NOT (%s)" % frag
    return frag, params


def build_where(filters: Optional[dict]):
    """filters dict -> (where_sql, params). filters 없으면 ('', [])."""
    if not filters:
        return "", []
    frags, params = [], []
    for col, expr in filters.items():
        if isinstance(expr, (list, tuple)):
            # 같은 컬럼 다중 조건 (AND)
            for e in expr:
                f, p = _one(col, str(e))
                frags.append(f)
                params.extend(p)
        else:
            f, p = _one(col, str(expr))
            frags.append(f)
            params.extend(p)
    return (" WHERE " + " AND ".join(frags)) if frags else "", params


def build_order(order: Optional[str]) -> str:
    """'col.desc' / 'col.asc' / 'col' / 'a.desc,b.asc' -> ' ORDER BY ...'."""
    if not order:
        return ""
    parts = []
    for tok in order.split(","):
        tok = tok.strip()
        if not tok:
            continue
        if tok.endswith(".desc"):
            parts.append("%s DESC" % tok[:-5])
        elif tok.endswith(".asc"):
            parts.append("%s ASC" % tok[:-4])
        else:
            parts.append(tok)
    return (" ORDER BY " + ", ".join(parts)) if parts else ""
