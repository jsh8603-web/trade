"""빌드 무결성 — 의존성(requirements.txt) ↔ 코드 import, .env.example ↔ os.getenv 일관성 검증.

B2팀 진단:
- test_requirements_consistency: scripts/, agents/, rl_hybrid/ 의 top-level import를
  수집해서 requirements.txt 에 누락된 외부 패키지를 찾는다.
- test_env_example_completeness: 코드에서 사용되는 os.environ/os.getenv("XXX") 키가
  .env.example 에 모두 기재됐는지 검증한다.
- test_env_actual_keys_subset_of_example: .env 파일이 있으면 키가 모두 .env.example
  에 있는지 확인(값은 검사하지 않음, 스킵 OK).

화이트리스트는 의미 있는 경고를 남기기 위해 꼭 필요한 항목만 포함한다. 신규 의존성을
추가할 때 requirements.txt/.env.example 중 한쪽만 갱신하고 커밋하는 실수를 잡는 것이
목표다.
"""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# 스캔 대상 디렉토리
# ---------------------------------------------------------------------------
SCAN_DIRS = [
    PROJECT_ROOT / "scripts",
    PROJECT_ROOT / "agents",
    PROJECT_ROOT / "rl_hybrid",
    PROJECT_ROOT / "utils",
]

# 프로젝트 내부(1st-party) 패키지 루트명 — requirements 체크에서 제외
FIRST_PARTY_PKGS = {
    "agents",
    "scripts",
    "rl_hybrid",
    "utils",
    "scalp_ml",
    "tools",
    "kimchirang",
    "web",
    "prompts",
    "tests",
    # scripts/ 하위의 bare-import(sys.path 에 scripts/ 가 포함될 때) 모듈
    "hide_console",
    "lifeline",
    "supabase_query",
}

# 표준 라이브러리 — Python 3.10+ 에는 sys.stdlib_module_names 가 있다.
STDLIB = set(getattr(sys, "stdlib_module_names", set()))
# 안전망: 구버전 호환용 수동 목록
STDLIB |= {
    "__future__", "typing", "typing_extensions", "dataclasses", "pathlib",
    "collections", "datetime", "json", "os", "sys", "re", "io", "time",
    "logging", "subprocess", "threading", "multiprocessing", "queue",
    "concurrent", "asyncio", "http", "urllib", "socket", "ssl", "email",
    "hashlib", "hmac", "base64", "binascii", "struct", "math", "random",
    "itertools", "functools", "operator", "copy", "pickle", "shelve",
    "sqlite3", "csv", "xml", "html", "argparse", "getopt", "shlex", "shutil",
    "tempfile", "glob", "fnmatch", "configparser", "platform", "signal",
    "atexit", "traceback", "inspect", "ast", "dis", "importlib", "contextlib",
    "warnings", "weakref", "abc", "enum", "numbers", "decimal", "fractions",
    "statistics", "zipfile", "gzip", "bz2", "lzma", "tarfile", "zoneinfo",
    "calendar", "locale", "uuid", "secrets", "string", "textwrap", "pprint",
    "unicodedata", "stringprep", "codecs", "errno", "ctypes", "select",
    "selectors", "fcntl", "msvcrt", "winreg", "posixpath", "ntpath",
    "unittest", "doctest", "pdb", "bdb", "trace", "pyclbr", "py_compile",
    "compileall", "runpy", "site", "tokenize", "token", "keyword", "symtable",
    "readline", "rlcompleter", "resource", "getpass", "webbrowser", "tty",
    "pty", "termios", "mimetypes", "sched", "tracemalloc", "gc",
}

# Pip 패키지 분산 이름 → 실제 top-level import 이름 매핑 (requirements.txt 표기 기준)
# 왼쪽이 requirements.txt 에 쓰는 이름(소문자), 오른쪽이 import 문에 쓰는 모듈명.
PIP_TO_IMPORT = {
    "pyjwt": {"jwt"},
    "python-dotenv": {"dotenv"},
    "pyzmq": {"zmq"},
    "google-generativeai": {"google"},  # google.generativeai
    "stable-baselines3": {"stable_baselines3"},
    "psycopg2-binary": {"psycopg2"},
    "pillow": {"PIL"},
    "beautifulsoup4": {"bs4"},
    "pyyaml": {"yaml"},
    "scikit-learn": {"sklearn"},
    "opencv-python": {"cv2"},
}

# requirements.txt 에 없어도 허용되는 외부 import 화이트리스트.
# (선택적 의존성 / 개발 도구 / 런타임 가드로 try-import 처리된 것)
OPTIONAL_IMPORT_WHITELIST = {
    # 테스트/개발 도구
    "pytest", "mock", "freezegun", "hypothesis",
    # Supabase REST 는 requests 로 직접 호출하지만 일부 헬퍼 모듈이
    # supabase-py 를 선택적으로 참조할 수 있음
    "supabase",
    # 과학 계산 — numpy/torch 의 전이 의존성 (requirements 가 pin 하지 않음)
    "pandas", "scipy", "matplotlib", "seaborn", "sklearn", "lightgbm",
    "optuna", "joblib", "tqdm",
    # HuggingFace — decision_transformer 선택적
    "transformers", "tokenizers", "datasets", "accelerate", "safetensors",
    "huggingface_hub",
    # Gymnasium 내부적으로 쓰는 wrappers
    "gym", "shimmy",
    # RL 고급 — 선택적 설치
    "d3rlpy", "morl_baselines", "pymoo", "ray", "tianshou",
    # 시각화/모니터링
    "tensorboard", "wandb", "mlflow",
    # Playwright 가 playwright 본체를 설치하면 같이 온다
    "playwright",
    # CCXT 내부 사용 가능
    "aiohttp_socks",
    # utilities
    "dateutil", "pytz", "colorama", "rich", "click", "typer",
    # Windows/플랫폼별 — condition import
    "pywin32", "win32api", "win32con", "pywintypes",
    # 기타: schedule / croniter 는 OS cron 으로 대체 가능
    "schedule", "croniter", "apscheduler",
    # TA-Lib / pandas-ta — optional indicators (코드 내 대체 구현 존재)
    "talib", "pandas_ta",
    # psutil: scripts/lifeline/sentinel.py, healer.py 에서 try/except ImportError
    # 가드 처리된 선택적 의존성 (미설치 시 경고만 출력)
    "psutil",
}

# v1.32.5에서 pyyaml/yfinance 를 requirements.txt 에 추가하여 해소됨.
# 향후 추가 누락이 재발하면 다시 이 집합에 올려 xfail 추적 가능.
KNOWN_REQUIREMENTS_GAPS: set[str] = set()

# requirements.txt 에 있으나 코드에 import 가 없어도 OK 인 패키지
# (간접 의존 / 런타임에만 CLI 로 사용)
UNUSED_OK_WHITELIST = {
    "qrcode",        # CLI/서버 전용 QR 생성, 일부 스크립트에서 동적 import 가능
    "pillow",        # qrcode 의존
    "openai",        # 선택적 LLM 백엔드
    "websockets",    # 선택적 실시간 피드
    "aiohttp",       # twikit / ccxt 간접 의존
    "flask",         # 웹 대시보드만 사용 — tests/ 스캔 범위 밖일 수 있음
    "msgpack",       # pyzmq serializer
}


# ---------------------------------------------------------------------------
# 유틸리티
# ---------------------------------------------------------------------------
def _iter_py_files(dirs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for d in dirs:
        if not d.exists():
            continue
        for p in d.rglob("*.py"):
            rel = p.relative_to(PROJECT_ROOT).as_posix()
            if "__pycache__" in rel or "/venv/" in rel or "/.venv/" in rel:
                continue
            files.append(p)
    return files


def _extract_top_level_imports(py_file: Path) -> set[str]:
    """AST 로 top-level 모듈명(앞부분)을 추출한다."""
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()

    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            # 상대 import 는 제외 (node.level > 0)
            if node.level and node.level > 0:
                continue
            if node.module:
                mods.add(node.module.split(".")[0])
    return mods


def _parse_requirements(req_path: Path) -> set[str]:
    """requirements.txt 에서 패키지명(소문자)만 파싱한다."""
    pkgs: set[str] = set()
    if not req_path.exists():
        return pkgs
    for line in req_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # name>=x.y 형태 — extras/버전 제거
        name = re.split(r"[<>=!~;\[]", line, maxsplit=1)[0].strip().lower()
        if name:
            pkgs.add(name)
    return pkgs


def _expand_provides(pkg_name: str) -> set[str]:
    """requirements 패키지명이 제공하는 import 이름 집합."""
    if pkg_name in PIP_TO_IMPORT:
        return PIP_TO_IMPORT[pkg_name]
    # 기본적으로 하이픈→언더스코어 변환한 이름이 import 명이라 가정
    return {pkg_name.replace("-", "_")}


def _extract_env_keys_from_code(py_files: list[Path]) -> set[str]:
    """os.environ[], os.environ.get(), os.getenv() 에서 키를 추출한다."""
    patterns = [
        re.compile(r"""os\.environ\.get\(\s*["']([A-Z_][A-Z0-9_]*)["']"""),
        re.compile(r"""os\.getenv\(\s*["']([A-Z_][A-Z0-9_]*)["']"""),
        re.compile(r"""os\.environ\[\s*["']([A-Z_][A-Z0-9_]*)["']\s*\]"""),
    ]
    keys: set[str] = set()
    for f in py_files:
        try:
            src = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pat in patterns:
            keys.update(pat.findall(src))
    return keys


def _parse_env_file(path: Path) -> set[str]:
    """.env / .env.example 에서 KEY=... 패턴의 키만 추출."""
    keys: set[str] = set()
    if not path.exists():
        return keys
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Z_][A-Z0-9_]*)\s*=", line)
        if m:
            keys.add(m.group(1))
    return keys


# ---------------------------------------------------------------------------
# 화이트리스트: 코드엔 있지만 .env.example 에 없어도 되는 키
# ---------------------------------------------------------------------------
# 런타임 전용 / 플랫폼 기본 제공 / 테스트 전용 / 동적 구성 키
ENV_KEY_WHITELIST = {
    # 파이썬/OS 기본
    "PATH", "HOME", "USER", "USERNAME", "USERPROFILE", "APPDATA",
    "LOCALAPPDATA", "PROGRAMFILES", "SYSTEMROOT", "TEMP", "TMP", "TMPDIR",
    "PWD", "SHELL", "LANG", "LC_ALL", "PYTHONPATH", "PYTHONIOENCODING",
    "PYTHONUNBUFFERED", "PYTHONDONTWRITEBYTECODE", "PYTHONUTF8",
    "VIRTUAL_ENV", "CONDA_DEFAULT_ENV",
    # 테스트/CI
    "CI", "GITHUB_ACTIONS", "PYTEST_CURRENT_TEST",
    # Claude Code / 터미널
    "CLAUDE_CODE", "CLAUDECODE", "TERM", "TERM_PROGRAM",
    # Playwright
    "PLAYWRIGHT_BROWSERS_PATH",
    # 선택적 RL/ML 튜닝 키 (동적으로 활성화/비활성화)
    "SB3_NUM_ENVS", "SB3_TOTAL_TIMESTEPS", "SB3_DEVICE",
    "TORCH_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
    "CUDA_VISIBLE_DEVICES",
    # Supabase Management API (문서화는 README/MEMORY)
    "SUPABASE_ACCESS_TOKEN", "SUPABASE_PROJECT_REF",
    # Git / hook / push 토큰
    "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL",
}


# ---------------------------------------------------------------------------
# 사전 계산
# ---------------------------------------------------------------------------
_PY_FILES = _iter_py_files(SCAN_DIRS)
_REQ_PKGS = _parse_requirements(PROJECT_ROOT / "requirements.txt")

_PROVIDED_IMPORT_NAMES: set[str] = set()
for pkg in _REQ_PKGS:
    _PROVIDED_IMPORT_NAMES |= _expand_provides(pkg)

_ALL_IMPORTS: set[str] = set()
for f in _PY_FILES:
    _ALL_IMPORTS |= _extract_top_level_imports(f)

_EXTERNAL_IMPORTS: set[str] = {
    m for m in _ALL_IMPORTS
    if m
    and m not in STDLIB
    and m not in FIRST_PARTY_PKGS
    and not m.startswith("_")
}

_ENV_KEYS_IN_CODE = _extract_env_keys_from_code(_PY_FILES)
_ENV_EXAMPLE_KEYS = _parse_env_file(PROJECT_ROOT / ".env.example")


# ===========================================================================
# 1. requirements.txt ↔ 코드 import 일관성
# ===========================================================================
class TestRequirementsConsistency:
    """코드가 실제로 import 하는 외부 패키지가 requirements.txt 에 있는지 검증"""

    def test_scan_found_files(self):
        """스캔 대상 .py 파일이 실제로 수집됐다"""
        assert len(_PY_FILES) > 20, (
            f"scripts/agents/rl_hybrid/utils 에서 충분한 파일을 찾지 못함: {len(_PY_FILES)}"
        )

    def test_requirements_present(self):
        """requirements.txt 가 존재하고 파싱됐다"""
        assert len(_REQ_PKGS) > 5, f"requirements.txt 파싱 실패: {_REQ_PKGS}"

    def test_imports_covered_by_requirements(self):
        """외부 import 가 requirements.txt 로 커버되거나 화이트리스트에 있다.

        알려진 누락(KNOWN_REQUIREMENTS_GAPS) 은 별도 테스트에서 추적하므로
        여기서는 예외로 넘긴다.
        """
        missing: set[str] = set()
        for imp in _EXTERNAL_IMPORTS:
            if imp in _PROVIDED_IMPORT_NAMES:
                continue
            if imp in OPTIONAL_IMPORT_WHITELIST:
                continue
            if imp in KNOWN_REQUIREMENTS_GAPS:
                continue
            missing.add(imp)

        assert not missing, (
            "requirements.txt 에 누락된 외부 import 발견:\n  "
            + "\n  ".join(sorted(missing))
            + "\n\n해결: requirements.txt 에 패키지 추가 또는 "
            + "OPTIONAL_IMPORT_WHITELIST 에 의도적 예외 등록"
        )

    def test_known_requirements_gaps_resolved(self):
        """KNOWN_REQUIREMENTS_GAPS 에 등록된 항목이 전부 해소돼 있어야 한다.

        v1.32.5 에서 yaml/yfinance 해소 → 집합 비어 있음. 새로 누락이 발견되면
        집합에 추가하여 일시 추적하다가 해소 후 다시 비운다.
        """
        still_missing = {
            imp for imp in KNOWN_REQUIREMENTS_GAPS
            if imp not in _PROVIDED_IMPORT_NAMES
        }
        assert not still_missing, (
            f"아직 requirements.txt 에 누락: {sorted(still_missing)}"
        )

    def test_requirements_all_used(self):
        """requirements.txt 에 선언됐으나 코드에 사용 흔적이 없는 패키지 탐지.

        scripts/agents/rl_hybrid/utils 범위에서만 스캔하므로 kimchirang 등
        다른 디렉토리에서만 쓰는 패키지는 unused 로 보일 수 있다. 그런 경우
        UNUSED_OK_WHITELIST 에 등록하거나 SCAN_DIRS 를 확장한다.
        """
        unused: set[str] = set()
        for pkg in _REQ_PKGS:
            provides = _expand_provides(pkg)
            used = any(name in _ALL_IMPORTS for name in provides)
            if not used and pkg not in UNUSED_OK_WHITELIST:
                # ccxt 는 kimchirang/ 디렉토리 전용 → 스캔 범위 밖이라 unused 로 보임
                # (requirements.txt 에 "# === Kimchirang ===" 섹션으로 명시됨)
                if pkg == "ccxt":
                    continue
                unused.add(pkg)

        assert not unused, (
            "requirements.txt 에 있으나 코드에서 사용되지 않는 패키지:\n  "
            + "\n  ".join(sorted(unused))
            + "\n\n해결: 제거하거나 UNUSED_OK_WHITELIST 에 등록"
        )


# ===========================================================================
# 2. .env.example ↔ 코드 os.getenv/os.environ 일관성
# ===========================================================================
class TestEnvExampleCompleteness:
    """코드가 실제로 읽는 환경변수가 .env.example 에 기재됐는지 검증"""

    def test_env_example_present(self):
        """.env.example 파일 존재 및 파싱됨"""
        assert len(_ENV_EXAMPLE_KEYS) > 5, (
            f".env.example 파싱 실패: {_ENV_EXAMPLE_KEYS}"
        )

    def test_env_keys_collected(self):
        """코드에서 환경변수 키가 실제로 수집됐다"""
        assert len(_ENV_KEYS_IN_CODE) > 5, (
            f"코드에서 os.getenv/environ 키를 찾지 못함: {_ENV_KEYS_IN_CODE}"
        )

    # ⚠️ B2팀 발견 — .env.example 에 누락됐지만 코드가 사용 중인 피처 플래그/
    # 설정 키. 실제 문서화가 누락된 상태라 별도 xfail 테스트로 추적한다.
    # 해소 시 아래 집합에서 해당 키를 제거하면 XPASS 로 알려준다.
    KNOWN_ENV_EXAMPLE_GAPS = {
        # 고급 RL 피처 플래그 (MEMORY.md 에는 기재, .env.example 은 누락)
        "MORL_ENVELOPE", "MORL_ADAPTIVE", "MORL_MAX_MDD", "MORL_MAX_TRADES_PER_DAY",
        "MULTI_AGENT_ENABLED", "MA_SCALPING_STEPS", "MA_SWING_STEPS",
        "MA_SCALP_WEIGHT", "MA_SWING_WEIGHT", "MA_VETO_THRESHOLD",
        "MA_WEIGHT_LEARNER_STEPS",
        "LLM_STATE_ENCODER_ENABLED", "LLM_STATE_CACHE_TTL",
        "LLM_STATE_PROJECTED_DIM",
        "SELF_TUNING_ENABLED", "SELF_TUNING_AUTO_APPLY",
        "SELF_TUNING_APPROVAL_THRESHOLD", "SELF_TUNING_FREQUENCY_HOURS",
        "SELF_TUNING_ROLLBACK_SHARPE_DROP",
        "USE_RL_EXIT",
        # 추가 API 키 / 런타임 설정
        "CMC_API_KEY", "GEMINI_ANALYSIS_MODEL", "SUPABASE_KEY",
        "SHORT_TERM_MAX_DAILY_DRYRUN", "WEB_AUTH_TOKEN",
        # 미니랑 도구 설정
        "MINIRANG_CLAUDE_BIN", "MINIRANG_MAX_ITERATIONS",
        "MINIRANG_NOTIFY", "MINIRANG_TIMEOUT",
        # SMTP 알림 (선택적)
        "SMTP_FROM", "SMTP_HOST", "SMTP_PASS", "SMTP_PORT", "SMTP_USER",
    }

    def test_code_env_keys_documented(self):
        """코드에서 쓰는 키가 .env.example 또는 화이트리스트에 있다.

        알려진 누락(KNOWN_ENV_EXAMPLE_GAPS) 은 별도 xfail 테스트에서 추적.
        """
        missing = {
            k for k in _ENV_KEYS_IN_CODE
            if k not in _ENV_EXAMPLE_KEYS
            and k not in ENV_KEY_WHITELIST
            and k not in self.KNOWN_ENV_EXAMPLE_GAPS
        }
        assert not missing, (
            ".env.example 에 문서화되지 않은 환경변수 키:\n  "
            + "\n  ".join(sorted(missing))
            + "\n\n해결: .env.example 에 기본값과 함께 추가 또는 "
            + "ENV_KEY_WHITELIST / KNOWN_ENV_EXAMPLE_GAPS 에 등록"
        )

    @pytest.mark.xfail(
        reason="B2팀 알려진 누락 — .env.example 에 추가되어야 함",
        strict=False,
    )
    def test_known_env_gaps_resolved(self):
        """알려진 .env.example 누락이 해소되면 XPASS 로 알려준다."""
        still_missing = {
            k for k in self.KNOWN_ENV_EXAMPLE_GAPS
            if k not in _ENV_EXAMPLE_KEYS
        }
        assert not still_missing, (
            f".env.example 에 아직 누락된 키 {len(still_missing)}건: "
            + f"{sorted(still_missing)[:5]}..."
        )


# ===========================================================================
# 3. 실제 .env 가 있다면 키 집합이 .env.example 의 부분집합인지 확인
# ===========================================================================
class TestEnvActualFile:
    """.env 가 존재하면 모든 키가 .env.example 에 있는지 확인.
    없으면 스킵 (CI/신규 머신 환경)."""

    _DOT_ENV = PROJECT_ROOT / ".env"

    # KR_* 키는 kimchirang 전용 설정 — B2팀 확인: .env.example 에 미기재
    _KR_PREFIX = "KR_"

    def test_env_keys_subset_of_example(self):
        if not self._DOT_ENV.exists():
            pytest.skip(".env 파일이 없어 스킵")

        actual_keys = _parse_env_file(self._DOT_ENV)
        example_keys = _ENV_EXAMPLE_KEYS

        # TestEnvExampleCompleteness.KNOWN_ENV_EXAMPLE_GAPS 도 허용
        # (순환 참조 방지 위해 클래스명으로 접근)
        known_gaps = TestEnvExampleCompleteness.KNOWN_ENV_EXAMPLE_GAPS

        unknown = set()
        for k in actual_keys:
            if k in example_keys:
                continue
            if k in ENV_KEY_WHITELIST:
                continue
            if k in known_gaps:
                continue
            if k.startswith(self._KR_PREFIX):
                # 김치랑 전용 접두사 — 별도 kimchirang/.env.example 권장
                continue
            unknown.add(k)

        # 주의: 값은 검사하지 않음 (시크릿). 키 집합만 검증.
        assert not unknown, (
            ".env 에만 존재하고 .env.example 에는 없는 키:\n  "
            + "\n  ".join(sorted(unknown))
            + "\n\n해결: .env.example 에 샘플 값과 함께 추가 "
            + "(레거시/폐기 키라면 .env 에서 제거)"
        )


# ===========================================================================
# 4. 진단용 메타 테스트 — 실패 시 현황을 빠르게 확인
# ===========================================================================
class TestDiagnostics:
    """수집 결과를 환경에 출력(디버깅 용이성)"""

    def test_summary_printable(self, capsys):
        print(f"py_files={len(_PY_FILES)}")
        print(f"req_pkgs={len(_REQ_PKGS)}")
        print(f"external_imports={len(_EXTERNAL_IMPORTS)}")
        print(f"env_keys_in_code={len(_ENV_KEYS_IN_CODE)}")
        print(f"env_example_keys={len(_ENV_EXAMPLE_KEYS)}")
        # 빈값이면 의미 있는 검증이 안 됨
        assert _PY_FILES
        assert _REQ_PKGS
        assert _ENV_EXAMPLE_KEYS
