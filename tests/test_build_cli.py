"""B4 팀 — scripts/*.py CLI 실행 가능성 검증.

검증 전략:
- 대상 스크립트가 argparse/ArgumentParser를 사용하면 ``--help`` 를 호출해
  크래시 없이 종료(exit 0 또는 2)하는지 확인한다.
- argparse를 사용하지 않는 스크립트는 ``pytest.skip("no argparse")``.
- 절대로 실제 매매/외부 API 호출을 트리거하지 않는다. ``--help`` 파싱만 수행.
- 환경 변수에 ``DRY_RUN=true`` + ``EMERGENCY_STOP=true`` 를 강제 주입해
  만에 하나 외부 I/O가 발생해도 안전 상태로 작동하도록 방어한다.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# 우선 .venv Python을 쓰되, 없으면 현재 인터프리터로 fallback.
_VENV_PY = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
PYTHON_EXE = str(_VENV_PY) if _VENV_PY.exists() else sys.executable

TIMEOUT_SEC = 20

TARGET_SCRIPTS = [
    "version_manager.py",
    "collect_market_data.py",
    "collect_fear_greed.py",
    "collect_news.py",
    "notify_telegram.py",
    "get_portfolio.py",
    "execute_trade.py",
    "evaluate_switches.py",
]


def _has_argparse(script_path: Path) -> bool:
    """스크립트 소스에 argparse/ArgumentParser 사용이 있는지 정적 체크."""
    if not script_path.exists():
        return False
    try:
        src = script_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return ("argparse" in src) or ("ArgumentParser" in src)


def _safe_env() -> dict[str, str]:
    """--help 파싱 도중 혹시 외부 I/O가 발생하더라도 안전하도록 환경 강제."""
    env = os.environ.copy()
    env["DRY_RUN"] = "true"
    env["EMERGENCY_STOP"] = "true"
    # 자식 프로세스에서 import 경로를 프로젝트 루트로 맞춘다.
    existing = env.get("PYTHONPATH", "")
    parts = [str(PROJECT_ROOT), str(SCRIPTS_DIR)]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    # 출력 인코딩 이슈(cp949) 회피
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


@pytest.mark.parametrize("script_name", TARGET_SCRIPTS)
def test_script_help_does_not_crash(script_name: str) -> None:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        pytest.skip(f"{script_name} not found")

    if not _has_argparse(script_path):
        pytest.skip("no argparse")

    try:
        proc = subprocess.run(
            [PYTHON_EXE, str(script_path), "--help"],
            cwd=str(PROJECT_ROOT),
            env=_safe_env(),
            capture_output=True,
            timeout=TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(f"{script_name} --help timed out after {TIMEOUT_SEC}s: {exc}")

    # argparse --help: exit 0 (정상) 혹은 2 (파서가 help 후 종료할 때 드물게 발생)
    assert proc.returncode in (0, 2), (
        f"{script_name} --help exited with {proc.returncode}\n"
        f"stdout: {proc.stdout[:500]!r}\n"
        f"stderr: {proc.stderr[:500]!r}"
    )
