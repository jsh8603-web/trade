"""B1팀 빌드 무결성 — 바이트컴파일 스윕

프로젝트의 모든 Python 소스 파일이 `py_compile`로 **문법 컴파일**되는지
개별 파일마다 pytest parametrize로 회귀 검증한다. 실패 시 어떤 파일인지
즉시 드러나도록 각 파일을 별개 테스트 케이스로 분리한다.

대상:
    scripts/, agents/, rl_hybrid/, utils/, llm/, scalp_ml/ 디렉토리의 .py 파일

제외:
    - tests/ (pytest가 별도 수집)
    - __pycache__, .venv, .git (빌드 산출물)
    - capture_chart.py (Playwright 브라우저 의존, 이 레포 컨벤션상 제외)
"""

from __future__ import annotations

import py_compile
from pathlib import Path

import pytest

# 프로젝트 루트 (tests/ 의 부모)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 스캔 대상 디렉토리 (CLAUDE.md 기준 핵심 소스 트리)
TARGET_DIRS = ("scripts", "agents", "rl_hybrid", "utils", "llm", "scalp_ml")

# 파일 단위 제외 (Playwright 등 외부 바이너리 의존)
EXCLUDED_FILENAMES = frozenset({"capture_chart.py"})

# 경로 토큰 단위 제외 (산출물/테스트 디렉토리)
EXCLUDED_PATH_PARTS = frozenset({"__pycache__", ".venv", ".git", "tests"})


def _collect_source_files() -> list[Path]:
    """스캔 대상 .py 파일 목록을 수집한다."""
    collected: list[Path] = []
    for target in TARGET_DIRS:
        base = PROJECT_ROOT / target
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            parts = set(path.parts)
            if parts & EXCLUDED_PATH_PARTS:
                continue
            if path.name in EXCLUDED_FILENAMES:
                continue
            collected.append(path)
    return sorted(collected)


# 수집은 모듈 로드 시점에 1회 수행 (pytest parametrize 요구사항)
SOURCE_FILES = _collect_source_files()

# parametrize ID는 프로젝트 루트 기준 상대 경로 (POSIX 스타일)
SOURCE_FILE_IDS = [p.relative_to(PROJECT_ROOT).as_posix() for p in SOURCE_FILES]


def test_source_tree_discovered():
    """스캔이 어떤 파일도 찾지 못하면 설정 문제이므로 실패시킨다."""
    assert SOURCE_FILES, (
        "대상 소스 파일이 0건입니다. TARGET_DIRS 또는 프로젝트 구조를 확인하세요."
    )


@pytest.mark.parametrize("source_path", SOURCE_FILES, ids=SOURCE_FILE_IDS)
def test_py_compile(source_path: Path):
    """각 .py 파일이 문법 오류 없이 바이트컴파일되어야 한다.

    py_compile.compile(doraise=True)는 SyntaxError 등을 PyCompileError로
    래핑해 던진다. 성공 시 조용히 통과한다.
    """
    py_compile.compile(str(source_path), doraise=True, quiet=1)
