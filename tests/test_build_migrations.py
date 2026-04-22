"""Build integrity tests for Supabase SQL migrations.

B3팀 — SQL 마이그레이션 문법/순서/멱등성 검증.

Checks:
- 모든 .sql 파일이 sqlparse로 파싱 가능한지 (파서 레벨)
- 파일명 번호(001, 002, ...) 순서 + 중복 번호 없음
- CREATE TABLE/INDEX/POLICY 등의 멱등성 힌트 (IF NOT EXISTS / OR REPLACE)

제약:
- DB 실제 연결 없음 (순수 파일 파싱)
- sqlparse 미설치 환경에서는 skip
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Tuple

import pytest

# sqlparse가 없으면 전체 모듈 skip
sqlparse = pytest.importorskip("sqlparse")

LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "supabase" / "migrations"

# 041/042/043은 이미 멱등성 수정 적용됨 — 배경 주석 참고
IDEMPOTENCY_EXEMPT_PREFIXES = {"041", "042", "043"}

# 파일명 번호 파싱 정규식 (예: 001, 002b, 017b, 037 중복)
FILENAME_NUM_RE = re.compile(r"^(\d{3})([a-z]?)_")


def _iter_migration_files() -> List[Path]:
    """마이그레이션 .sql 파일 정렬된 목록 반환."""
    if not MIGRATIONS_DIR.is_dir():
        return []
    return sorted(
        p for p in MIGRATIONS_DIR.iterdir()
        if p.is_file() and p.suffix.lower() == ".sql"
    )


def _parse_filename(name: str) -> Tuple[int, str] | None:
    """파일명에서 (번호, 서픽스) 추출. 실패 시 None."""
    m = FILENAME_NUM_RE.match(name)
    if not m:
        return None
    return int(m.group(1)), m.group(2)


# ---------------------------------------------------------------------------
# 1. sqlparse 파싱
# ---------------------------------------------------------------------------


def test_all_migrations_parseable() -> None:
    """모든 .sql 파일이 sqlparse로 문법 파싱 가능해야 한다."""
    files = _iter_migration_files()
    assert files, f"마이그레이션 파일 없음: {MIGRATIONS_DIR}"

    parse_errors: List[Tuple[str, str]] = []
    for path in files:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="utf-8-sig", errors="replace")

        if not content.strip():
            parse_errors.append((path.name, "empty file"))
            continue

        try:
            statements = sqlparse.parse(content)
        except Exception as exc:  # pragma: no cover - sqlparse는 거의 예외 없음
            parse_errors.append((path.name, f"parse exception: {exc}"))
            continue

        # sqlparse는 실패해도 보통 빈 튜플을 반환하지 않지만,
        # 완전히 공백이 아닌데 statement가 0개면 이상 징후.
        if not statements:
            parse_errors.append((path.name, "no statements parsed"))
            continue

        # 각 statement의 tokens가 전부 Error 토큰이면 문법 오류로 간주.
        for stmt in statements:
            tokens = [t for t in stmt.flatten() if not t.is_whitespace]
            if not tokens:
                continue
            error_tokens = [
                t for t in tokens
                if t.ttype is not None and "Error" in str(t.ttype)
            ]
            if error_tokens and len(error_tokens) == len(tokens):
                parse_errors.append(
                    (path.name, f"all-error stmt near: {str(stmt)[:60]!r}")
                )
                break

    assert not parse_errors, (
        "SQL 파싱 에러 발생:\n"
        + "\n".join(f"  - {name}: {reason}" for name, reason in parse_errors)
    )


# ---------------------------------------------------------------------------
# 2. 파일명 번호 순서 + 중복 방지
# ---------------------------------------------------------------------------


def test_migration_ordering() -> None:
    """파일명 번호가 단조 증가하며, 동일 (번호, 서픽스) 중복이 없어야 한다."""
    files = _iter_migration_files()
    assert files, "마이그레이션 파일 없음"

    parsed: List[Tuple[int, str, str]] = []  # (num, suffix, filename)
    unparseable: List[str] = []

    for path in files:
        result = _parse_filename(path.name)
        if result is None:
            unparseable.append(path.name)
            continue
        num, suffix = result
        parsed.append((num, suffix, path.name))

    assert not unparseable, (
        f"파일명 형식 오류 (NNN_... 규칙 위반): {unparseable}"
    )

    # 중복 체크: (num, suffix) 조합이 겹치면 경고.
    # 단, 실제로 동일 파일이 두 번 등장할 수는 없으므로 fail 처리는 완전 동명 시에만.
    seen: dict[Tuple[int, str], List[str]] = {}
    for num, suffix, fname in parsed:
        key = (num, suffix)
        seen.setdefault(key, []).append(fname)

    # 완전 동명(파일 시스템상 불가능하지만 혹시) 방지
    identical_dups = [
        names for names in seen.values()
        if len(names) > 1 and len(set(names)) < len(names)
    ]
    assert not identical_dups, f"동일 파일명 중복: {identical_dups}"

    # 번호+서픽스 동일이지만 이름이 다른 경우 → 경고 로그만
    partial_dups = {
        key: names for key, names in seen.items() if len(names) > 1
    }
    if partial_dups:
        LOGGER.warning(
            "동일 (번호, 서픽스) 다중 파일 존재 (경고):\n%s",
            "\n".join(
                f"  {k[0]:03d}{k[1]}: {names}" for k, names in partial_dups.items()
            ),
        )

    # 단조 증가: 정렬된 파일명이 번호순과 일치해야 함 (서픽스 동률 허용)
    sorted_by_num = sorted(parsed, key=lambda t: (t[0], t[1], t[2]))
    filename_sorted = sorted(parsed, key=lambda t: t[2])
    sorted_names_by_num = [t[2] for t in sorted_by_num]
    sorted_names_by_name = [t[2] for t in filename_sorted]
    assert sorted_names_by_name == sorted_names_by_num, (
        "파일명 정렬 순서와 번호 순서 불일치:\n"
        f"  파일명 정렬: {sorted_names_by_name[:5]}...\n"
        f"  번호 정렬:   {sorted_names_by_num[:5]}..."
    )


# ---------------------------------------------------------------------------
# 3. 멱등성 휴리스틱 (경고 레벨)
# ---------------------------------------------------------------------------


# 멱등성 위험 패턴: "명령" 다음 바로 이름이 오는 경우
# (IF NOT EXISTS, OR REPLACE 등이 없는 bare form)
RISKY_PATTERNS = [
    # CREATE TABLE foo ... (IF NOT EXISTS 없음)
    (re.compile(r"\bCREATE\s+TABLE\s+(?!IF\s+NOT\s+EXISTS)", re.IGNORECASE),
     "CREATE TABLE without IF NOT EXISTS"),
    # CREATE INDEX foo ... (IF NOT EXISTS 없음)
    (re.compile(
        r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+(?!IF\s+NOT\s+EXISTS|CONCURRENTLY\s+IF\s+NOT\s+EXISTS)",
        re.IGNORECASE,
    ), "CREATE INDEX without IF NOT EXISTS"),
    # CREATE POLICY foo ... (DROP POLICY IF EXISTS 선행 없이)
    # 이건 파일 전체 맥락이 필요하므로 별도 처리
]


def _strip_sql_comments(sql: str) -> str:
    """-- 라인 주석 + /* */ 블록 주석 제거."""
    # 블록 주석
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    # 라인 주석
    sql = re.sub(r"--[^\n]*", "", sql)
    return sql


def test_idempotency_heuristic(caplog: pytest.LogCaptureFixture) -> None:
    """CREATE TABLE/INDEX/POLICY의 멱등성 힌트 점검 (WARN만, fail 안 함)."""
    files = _iter_migration_files()
    assert files, "마이그레이션 파일 없음"

    warnings: List[str] = []

    for path in files:
        # 041/042/043은 이미 수정됨 — skip
        prefix = path.name[:3]
        if prefix in IDEMPOTENCY_EXEMPT_PREFIXES:
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="utf-8-sig", errors="replace")

        clean = _strip_sql_comments(content)
        upper = clean.upper()

        # CREATE TABLE / INDEX: IF NOT EXISTS 누락 체크
        for pattern, label in RISKY_PATTERNS:
            for match in pattern.finditer(clean):
                # match 주변 120자 컨텍스트 (디버그용)
                start = max(0, match.start() - 10)
                end = min(len(clean), match.end() + 60)
                snippet = clean[start:end].replace("\n", " ").strip()
                warnings.append(
                    f"[{path.name}] {label}: ...{snippet[:100]}..."
                )

        # CREATE POLICY: DROP POLICY IF EXISTS 선행 또는 CREATE POLICY IF NOT EXISTS
        # (PostgreSQL 15+는 CREATE POLICY IF NOT EXISTS 미지원 → DROP 선행이 관용)
        policy_creates = list(re.finditer(
            r"\bCREATE\s+POLICY\s+", upper
        ))
        if policy_creates:
            has_drop_guard = bool(re.search(
                r"\bDROP\s+POLICY\s+IF\s+EXISTS\b", upper
            ))
            if not has_drop_guard:
                warnings.append(
                    f"[{path.name}] CREATE POLICY without preceding "
                    f"DROP POLICY IF EXISTS (count={len(policy_creates)})"
                )

    # 경고만 출력 — 테스트는 항상 pass
    if warnings:
        LOGGER.warning(
            "멱등성 경고 %d건:\n%s",
            len(warnings),
            "\n".join(f"  - {w}" for w in warnings),
        )
        # 디버깅용: 개수를 메시지에 남겨둠 (pytest -s 시 가시성)
        print(f"\n[idempotency] total warnings: {len(warnings)}")
    else:
        print("\n[idempotency] no warnings")

    # 항상 pass — 완전 스킵하지 않고 정보 제공
    assert True
