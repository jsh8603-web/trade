#!/usr/bin/env python3
"""build_sqlite_schema.py — supabase/migrations/*.sql -> core/db/schema.sql (SQLite DDL)

Supabase(PostgreSQL+pgvector) 마이그레이션을 로컬 SQLite DDL 로 결정론적 변환.
재현 가능(매번 동일 산출). L0 산출물.

변환 규칙:
  - 타입: BIGSERIAL/SERIAL->INTEGER(+PK 시 AUTOINCREMENT), JSONB/JSON->TEXT,
          vector(N)->BLOB, TIMESTAMPTZ/TIMESTAMP->TEXT, UUID->TEXT,
          DOUBLE PRECISION->REAL, NUMERIC/DECIMAL->REAL, T[](배열)->TEXT
  - 기본값: gen_random_uuid()/uuid_generate_v4()->제거, NOW()->CURRENT_TIMESTAMP
  - cast(::type)->제거
  - 제거 statement: CREATE EXTENSION / CREATE [OR REPLACE] FUNCTION / DO $$ /
          CREATE TRIGGER / COMMENT ON / GRANT/REVOKE / CREATE POLICY /
          ALTER ... ENABLE ROW LEVEL / 벡터인덱스(USING ivfflat|hnsw) /
          CREATE [MATERIALIZED] VIEW (PG 전용 함수 포함 多 -> 어댑터 select 로 대체)
  - pgvector 검색함수(match_*)는 어댑터 rpc_match(numpy 코사인)로 대체 -> DDL 제외

사용:
  python scripts/build_sqlite_schema.py            # schema.sql 생성 + 검증
  python scripts/build_sqlite_schema.py --check    # 검증만(임시 sqlite 로드)
"""
from __future__ import annotations
import re
import sys
import glob
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIG_DIR = os.path.join(ROOT, "supabase", "migrations")
OUT_SQL = os.path.join(ROOT, "core", "db", "schema.sql")
REPORT = os.path.join(ROOT, ".l0-schema-report.txt")


def strip_comments(sql: str) -> str:
    sql = re.sub(r"--[^\n]*", "", sql)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    return sql


def split_statements(sql: str) -> list:
    """$tag$ 달러쿼트 + '문자열' 내부 ; 보호하며 statement 분리."""
    stmts = []
    buf = []
    i, n = 0, len(sql)
    in_squote = False
    dollar_tag = None
    while i < n:
        ch = sql[i]
        if dollar_tag is not None:
            if sql.startswith(dollar_tag, i):
                buf.append(dollar_tag)
                i += len(dollar_tag)
                dollar_tag = None
                continue
            buf.append(ch)
            i += 1
            continue
        if in_squote:
            buf.append(ch)
            if ch == "'":
                if i + 1 < n and sql[i + 1] == "'":
                    buf.append("'")
                    i += 2
                    continue
                in_squote = False
            i += 1
            continue
        m = re.match(r"\$[a-zA-Z_0-9]*\$", sql[i:])
        if m:
            dollar_tag = m.group(0)
            buf.append(dollar_tag)
            i += len(dollar_tag)
            continue
        if ch == "'":
            in_squote = True
            buf.append(ch)
            i += 1
            continue
        if ch == ";":
            buf.append(";")
            stmts.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        stmts.append(tail)
    return stmts


_DROP_PREFIX = (
    "CREATE EXTENSION", "DROP EXTENSION",
    "CREATE OR REPLACE FUNCTION", "CREATE FUNCTION", "DROP FUNCTION",
    "CREATE TRIGGER", "DROP TRIGGER",
    "CREATE OR REPLACE VIEW", "CREATE VIEW", "CREATE MATERIALIZED VIEW", "DROP VIEW",
    "COMMENT ON",
    "GRANT", "REVOKE",
    "CREATE POLICY", "DROP POLICY",
    "ALTER PUBLICATION", "CREATE PUBLICATION",
    "ANALYZE", "VACUUM", "REFRESH MATERIALIZED",
)


def keep(stmt: str) -> bool:
    st = stmt.strip()
    if not st:
        return False
    head = re.sub(r"\s+", " ", st).upper()
    if head.startswith(_DROP_PREFIX):
        return False
    if head.startswith("DO ") or head.startswith("DO$") or head == "DO" or head.startswith("DO\n"):
        return False
    if "USING IVFFLAT" in head or "USING HNSW" in head:
        return False
    if head.startswith("ALTER") and "ENABLE ROW LEVEL" in head:
        return False
    if head.startswith("ALTER") and "REPLICA IDENTITY" in head:
        return False
    # SQLite 미지원 ALTER 변형 (RLS 정책/제약/인덱스 rename/drop column)
    if head.startswith("ALTER INDEX"):
        return False
    if head.startswith("ALTER TABLE") and "DROP CONSTRAINT" in head:
        return False
    if head.startswith("ALTER TABLE") and "ADD CONSTRAINT" in head:
        return False
    if head.startswith("ALTER TABLE") and "DROP COLUMN IF EXISTS" in head:
        return False
    if head.startswith("ALTER TABLE") and "ALTER COLUMN" in head:
        return False
    # GIN/GIST 인덱스 (배열/전문검색용, SQLite 무관)
    if "USING GIN" in head or "USING GIST" in head:
        return False
    return True


def convert(stmt: str) -> str:
    s = stmt
    s = re.sub(r"\bBIGSERIAL\b", "INTEGER", s, flags=re.I)
    s = re.sub(r"\bSMALLSERIAL\b", "INTEGER", s, flags=re.I)
    s = re.sub(r"\bSERIAL\b", "INTEGER", s, flags=re.I)
    s = re.sub(r"\bJSONB\b", "TEXT", s, flags=re.I)
    s = re.sub(r"\bJSON\b", "TEXT", s, flags=re.I)
    s = re.sub(r"\bvector\(\s*\d+\s*\)", "BLOB", s, flags=re.I)
    s = re.sub(r"\bTIMESTAMP\s+WITH\s+TIME\s+ZONE\b", "TEXT", s, flags=re.I)
    s = re.sub(r"\bTIMESTAMP\s+WITHOUT\s+TIME\s+ZONE\b", "TEXT", s, flags=re.I)
    s = re.sub(r"\bTIMESTAMPTZ\b", "TEXT", s, flags=re.I)
    s = re.sub(r"\bTIMESTAMP\b", "TEXT", s, flags=re.I)
    s = re.sub(r"\bUUID\b", "TEXT", s, flags=re.I)
    s = re.sub(r"\bDOUBLE\s+PRECISION\b", "REAL", s, flags=re.I)
    s = re.sub(r"\bNUMERIC\s*\([^)]*\)", "REAL", s, flags=re.I)
    s = re.sub(r"\bNUMERIC\b", "REAL", s, flags=re.I)
    s = re.sub(r"\bDECIMAL\s*\([^)]*\)", "REAL", s, flags=re.I)
    s = re.sub(r"\bDECIMAL\b", "REAL", s, flags=re.I)
    # 배열 타입 T[] / T[][] -> TEXT (cast :: 처리 전에)
    s = re.sub(r"(\b[A-Za-z]+)(\s*\[\s*\])+", "TEXT", s)
    # 기본값
    s = re.sub(r"DEFAULT\s+gen_random_uuid\(\)", "", s, flags=re.I)
    s = re.sub(r"DEFAULT\s+uuid_generate_v4\(\)", "", s, flags=re.I)
    s = re.sub(r"\bNOW\(\)", "CURRENT_TIMESTAMP", s, flags=re.I)
    s = re.sub(r"\btimezone\s*\([^)]*\)", "CURRENT_TIMESTAMP", s, flags=re.I)
    # cast ::type
    s = re.sub(r"::\s*[A-Za-z_][A-Za-z0-9_]*(\s*\[\s*\])*", "", s)
    # INTEGER PRIMARY KEY -> AUTOINCREMENT 명시
    s = re.sub(r"\bINTEGER\s+PRIMARY\s+KEY\b(?!\s+AUTOINCREMENT)",
               "INTEGER PRIMARY KEY AUTOINCREMENT", s, flags=re.I)
    # ALTER TABLE ADD COLUMN IF NOT EXISTS -> SQLite 미지원
    # DEFAULT ARRAY[...] / DEFAULT '{}' (배열 기본값) -> 제거 (컬럼은 TEXT 로 이미 변환됨)
    s = re.sub(r"DEFAULT\s+ARRAY\s*\[[^\]]*\]", "", s, flags=re.I)
    s = re.sub(r"DEFAULT\s+'\{\}'", "DEFAULT '[]'", s, flags=re.I)
    # NULLS FIRST/LAST (SQLite 미지원) 제거
    s = re.sub(r"\bNULLS\s+(FIRST|LAST)\b", "", s, flags=re.I)
    # 인덱스 표현식 내 'AT TIME ZONE ...' 제거 (created_at AT TIME ZONE 'x' -> created_at)
    s = re.sub(r"\bAT\s+TIME\s+ZONE\s+'[^']*'", "", s, flags=re.I)
    s = re.sub(r"\bAT\s+TIME\s+ZONE\s+\"[^\"]*\"", "", s, flags=re.I)
    if re.match(r"\s*ALTER\s+TABLE", s, flags=re.I):
        s = re.sub(r"(ADD\s+COLUMN)\s+IF\s+NOT\s+EXISTS", r"\1", s, flags=re.I)
    return s


def expand_multicol_alter(stmt: str) -> list:
    """ALTER TABLE t ADD COLUMN a.., ADD COLUMN b.. -> SQLite 는 1개씩만. 분해."""
    m = re.match(r"\s*(ALTER\s+TABLE\s+[A-Za-z0-9_.\"]+)\s+(.*);?\s*$", stmt, flags=re.I | re.S)
    if not m:
        return [stmt]
    prefix, body = m.group(1), m.group(2).rstrip(";").strip()
    # ADD COLUMN 다중만 대상 (top-level 콤마 분리)
    parts, depth, buf = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf)); buf = []; continue
        buf.append(ch)
    if buf:
        parts.append("".join(buf))
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) <= 1:
        return [stmt]
    # 모든 파트가 ADD COLUMN 형태여야 안전 분해
    if not all(re.match(r"ADD\s+COLUMN", p, flags=re.I) for p in parts):
        return [stmt]
    return ["%s %s;" % (prefix, p) for p in parts]


def _split_column_defs(body: str):
    """ADD COLUMN 묶음의 최상위 콤마만 분리(괄호 내부 콤마 보호)."""
    parts, depth, buf = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    if "".join(buf).strip():
        parts.append("".join(buf).strip())
    return parts


def expand_alter_add(stmt: str, seen_cols: set):
    """SQLite 비호환 ALTER 보정. 반환=statement 리스트.
       - 멀티컬럼 ADD COLUMN -> 개별 ALTER 로 분리
       - ADD COLUMN ... UNIQUE -> UNIQUE 제거 + CREATE UNIQUE INDEX
       - 중복 (table,col) ADD -> 스킵 (PG IF NOT EXISTS 흉내)
       해당 패턴 아니면 [stmt] 그대로."""
    m = re.match(r"\s*ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?([A-Za-z_][\w.]*)\s+(.+);?\s*$",
                 stmt, flags=re.I | re.S)
    if not m:
        return [stmt]
    table, rest = m.group(1), m.group(2).rstrip(";").strip()
    # ADD COLUMN 액션만 처리 (그 외 ALTER 액션은 원본 유지)
    actions = _split_column_defs(rest)
    if not all(re.match(r"ADD\s+COLUMN\b", a, flags=re.I) for a in actions):
        return [stmt]
    out = []
    for a in actions:
        cm = re.match(r"ADD\s+COLUMN\s+([A-Za-z_]\w*)\s+(.+)$", a, flags=re.I | re.S)
        if not cm:
            out.append("ALTER TABLE %s %s;" % (table, a))
            continue
        col, coldef = cm.group(1), cm.group(2).strip()
        key = (table.lower(), col.lower())
        if key in seen_cols:
            continue  # 중복 ADD 스킵
        seen_cols.add(key)
        uniq = bool(re.search(r"\bUNIQUE\b", coldef, flags=re.I))
        coldef_noq = re.sub(r"\bUNIQUE\b", "", coldef, flags=re.I).strip()
        out.append("ALTER TABLE %s ADD COLUMN %s %s;" % (table, col, coldef_noq))
        if uniq:
            out.append("CREATE UNIQUE INDEX IF NOT EXISTS uq_%s_%s ON %s(%s);"
                       % (table, col, table, col))
    return out


def build():
    files = sorted(glob.glob(os.path.join(MIG_DIR, "*.sql")))
    out_stmts = []
    seen_cols = set()
    for f in files:
        raw = open(f, encoding="utf-8").read()
        clean = strip_comments(raw)
        for st in split_statements(clean):
            if not keep(st):
                continue
            conv = convert(st).strip()
            if not conv:
                continue
            # gen_random_uuid 등 PG 함수 남은 DML(시드) 은 스킵
            if re.search(r"gen_random_uuid|uuid_generate", conv, flags=re.I):
                continue
            for piece in expand_alter_add(conv, seen_cols):
                piece = piece.strip()
                if piece:
                    out_stmts.append(piece if piece.endswith(";") else piece + ";")
    return files, out_stmts


def header(files):
    return (
        "-- AUTO-GENERATED by scripts/build_sqlite_schema.py -- DO NOT EDIT BY HAND.\n"
        "-- Source: supabase/migrations/*.sql (%d files) -> SQLite DDL.\n"
        "-- pgvector match_* / VIEW / FUNCTION 은 core/db 어댑터로 대체됨.\n"
        "-- 재생성: python scripts/build_sqlite_schema.py\n"
        "PRAGMA foreign_keys=OFF;\n" % len(files)
    )


def validate(stmts):
    con = sqlite3.connect(":memory:")
    failures = []
    for st in stmts:
        try:
            con.execute(st)
        except Exception as e:
            head_s = re.sub(r"\s+", " ", st)[:100]
            failures.append("%s: %s :: %s" % (type(e).__name__, e, head_s))
    n_tables = con.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    con.close()
    return n_tables, failures


def main():
    check_only = "--check" in sys.argv
    files, stmts = build()
    n_tables, failures = validate(stmts)
    lines = [
        "files=%d" % len(files),
        "statements_kept=%d" % len(stmts),
        "tables_created=%d" % n_tables,
        "failures=%d" % len(failures),
        "",
        "--- FAILED STATEMENTS ---",
    ]
    lines.extend(failures if failures else ["(none)"])
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines))
    if not check_only:
        os.makedirs(os.path.dirname(OUT_SQL), exist_ok=True)
        open(OUT_SQL, "w", encoding="utf-8").write(
            header(files) + "\n" + "\n\n".join(stmts) + "\n")
    print("L0_SCHEMA tables=%d stmts=%d failures=%d" % (n_tables, len(stmts), len(failures)))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
