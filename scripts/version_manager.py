"""
앱 버전 관리 + 변경 이력 DB 기록

사용법:
  # 변경사항 기록 (DB + VERSION 파일 자동 업데이트)
  python scripts/version_manager.py log \
    --severity major \
    --category bugfix \
    --summary "FGI 기본값 캐싱 + DB학습 활성화" \
    --files "agents/orchestrator.py,agents/base_agent.py" \
    --details '{"fixes": ["FGI fallback", "price_at_switch"]}' \
    --verified

  # 버전 조회
  python scripts/version_manager.py version

  # 최근 변경이력 조회
  python scripts/version_manager.py history [--limit 10]

  # 버전 범프 (patch/minor/major)
  python scripts/version_manager.py bump patch

severity 등급:
  critical  → 긴급 버그 수정, 데이터 손실 방지
  major     → 주요 기능 추가/변경, 중요 버그 수정
  minor     → 소규모 개선, 부분 수정
  patch     → 문서, 설정, 코드 정리
"""

import io
import sys
import json
import argparse
from pathlib import Path
from datetime import timezone, timedelta

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from core.db import db
VERSION_FILE = PROJECT_DIR / "VERSION"
KST = timezone(timedelta(hours=9))


def get_version() -> str:
    """현재 버전을 읽는다."""
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.0.0"


def set_version(version: str) -> None:
    """VERSION 파일에 버전을 기록한다."""
    VERSION_FILE.write_text(version + "\n", encoding="utf-8")


def bump_version(part: str) -> str:
    """시맨틱 버전을 올린다. part: major/minor/patch"""
    current = get_version()
    parts = current.split(".")
    if len(parts) != 3:
        parts = ["0", "0", "0"]

    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        raise ValueError(f"VERSION 파일의 버전이 숫자가 아닙니다: '{current}' — x.y.z 형식이어야 합니다")

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError(f"Unknown bump part: {part}")

    new_version = f"{major}.{minor}.{patch}"
    set_version(new_version)
    return new_version


def _severity_to_bump(severity: str) -> str:
    """severity에 따라 자동 버전 범프 결정."""
    return {
        "critical": "minor",
        "major": "minor",
        "minor": "patch",
        "patch": "patch",
    }.get(severity, "patch")


def log_change(
    severity: str,
    category: str,
    summary: str,
    files: list[str] | None = None,
    details: dict | None = None,
    verified: bool = False,
    verification_result: str | None = None,
    auto_bump: bool = True,
    changed_by: str = "claude_session",
) -> dict:
    """변경사항을 DB에 기록하고, VERSION을 자동 범프한다."""
    # 버전은 DB 기록 성공 후 범프
    old_version = get_version()
    if auto_bump:
        bump_part = _severity_to_bump(severity)
        version = bump_version(bump_part)
    else:
        version = get_version()

    row = {
        "version": version,
        "severity": severity,
        "category": category,
        "summary": summary,
        "files_modified": files or [],
        "details": details or {},
        "verified": verified,
        "verification_result": verification_result,
        "changed_by": changed_by,
    }

    try:
        result = db.insert("app_changelog", row, returning=True)
        print(f"[OK] v{version} ({severity}/{category}): {summary}")
        return result or {}
    except Exception as e:
        # DB 기록 실패 — VERSION 롤백
        if auto_bump:
            set_version(old_version)
        print(f"[ERROR] {e}", file=sys.stderr)
        return {"error": str(e)}


def get_history(limit: int = 10) -> list[dict]:
    """최근 변경이력을 조회한다."""
    try:
        return db.select(
            "app_changelog",
            select="version,severity,category,summary,files_modified,verified,created_at",
            order="created_at.desc",
            limit=limit,
        )
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(description="앱 버전 관리")
    sub = parser.add_subparsers(dest="command")

    # version
    sub.add_parser("version", help="현재 버전 조회")

    # bump
    p_bump = sub.add_parser("bump", help="버전 범프")
    p_bump.add_argument("part", choices=["major", "minor", "patch"])

    # log
    p_log = sub.add_parser("log", help="변경사항 기록")
    p_log.add_argument("--severity", required=True, choices=["critical", "major", "minor", "patch"])
    p_log.add_argument("--category", required=True, choices=["bugfix", "feature", "improvement", "refactor", "config", "strategy"])
    p_log.add_argument("--summary", required=True, help="변경 요약 (1줄)")
    p_log.add_argument("--files", default="", help="수정 파일 (콤마 구분)")
    p_log.add_argument("--details", default="{}", help="상세 JSON")
    p_log.add_argument("--verified", action="store_true", help="검증 완료")
    p_log.add_argument("--verification-result", default=None, help="검증 결과")
    p_log.add_argument("--no-bump", action="store_true", help="자동 버전 범프 안 함")
    p_log.add_argument("--changed-by", default="claude_session")

    # history
    p_hist = sub.add_parser("history", help="변경이력 조회")
    p_hist.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()

    if args.command == "version":
        print(f"v{get_version()}")

    elif args.command == "bump":
        new = bump_version(args.part)
        print(f"v{new}")

    elif args.command == "log":
        files = [f.strip() for f in args.files.split(",") if f.strip()]
        try:
            details = json.loads(args.details)
        except json.JSONDecodeError as e:
            print(f"ERROR: --details 값이 올바른 JSON이 아닙니다: {e}", file=sys.stderr)
            sys.exit(1)
        log_change(
            severity=args.severity,
            category=args.category,
            summary=args.summary,
            files=files,
            details=details,
            verified=args.verified,
            verification_result=args.verification_result,
            auto_bump=not args.no_bump,
            changed_by=args.changed_by,
        )

    elif args.command == "history":
        history = get_history(args.limit)
        for h in history:
            sev_icon = {"critical": "🔴", "major": "🟡", "minor": "🟢", "patch": "⚪"}.get(h["severity"], "?")
            verified = "✅" if h.get("verified") else "  "
            ts = h.get("created_at", "")[:16]
            print(f"  {sev_icon} v{h['version']} [{h['category']}] {h['summary']} {verified} ({ts})")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
