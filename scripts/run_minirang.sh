#!/bin/bash
# =============================================================================
# 미니랑(MiniRang) — Computer Use 에이전트 실행 래퍼
#
# Usage:
#   bash scripts/run_minirang.sh "NordVPN에서 Meshnet 활성화해줘"
#   bash scripts/run_minirang.sh --screenshot-only
#   bash scripts/run_minirang.sh --status
# =============================================================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# .env 로드
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# Python venv 감지
if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON="$PROJECT_DIR/.venv/bin/python"
elif [ -f "$PROJECT_DIR/venv/bin/python" ]; then
    PYTHON="$PROJECT_DIR/venv/bin/python"
else
    PYTHON="python3"
fi

# PATH 설정 (launchd 호환)
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

# 로그 디렉토리 확인
LOG_DIR="$PROJECT_DIR/logs/minirang"
if ! mkdir -p "$LOG_DIR" 2>/dev/null || ! touch "$LOG_DIR/.write_test" 2>/dev/null; then
    LOG_DIR="/tmp/blockchain_logs/minirang"
    mkdir -p "$LOG_DIR"
fi
rm -f "$LOG_DIR/.write_test" 2>/dev/null

# 스크린샷 디렉토리
mkdir -p "$PROJECT_DIR/data/minirang_screenshots" 2>/dev/null || true

# 실행
exec "$PYTHON" "$PROJECT_DIR/scripts/minirang.py" "$@"
