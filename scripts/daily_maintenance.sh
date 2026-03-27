#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────
# 일일 유지보수 스크립트
#
# 매일 04:30 KST (cron_run.sh 직후) 실행
# 1. 시그널 사후 추적 (scalp_retrospective.py)
# 2. DB 정리 (db_cleanup.py)
# ──────────────────────────────────────────────────────────

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# .env 로드
if [ -f .env ]; then
  set -a; source .env; set +a
fi

# Python
PYTHON="$PROJECT_DIR/.venv/bin/python3"
if [ ! -f "$PYTHON" ]; then
  PYTHON=$(which python3)
fi

LOG_DIR="$PROJECT_DIR/logs/maintenance"
mkdir -p "$LOG_DIR"
# 외장하드 심볼릭 logs 쓰기 불가 시 /tmp fallback
if ! touch "$LOG_DIR/.write_test" 2>/dev/null; then
    LOG_DIR="/tmp/blockchain_logs/maintenance"
    mkdir -p "$LOG_DIR"
fi
rm -f "$LOG_DIR/.write_test" 2>/dev/null
LOG_FILE="$LOG_DIR/maintenance_$(date +%Y%m%d).log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 일일 유지보수 시작" >> "$LOG_FILE"

# 1. 시그널 사후 추적
echo "[$(date '+%H:%M:%S')] 사후 추적 실행" >> "$LOG_FILE"
$PYTHON scripts/scalp_retrospective.py >> "$LOG_FILE" 2>&1 || true

# 2. DB 정리
echo "[$(date '+%H:%M:%S')] DB 정리 실행" >> "$LOG_FILE"
$PYTHON scripts/db_cleanup.py >> "$LOG_FILE" 2>&1 || true

# 3. 메모리 시스템 유지보수 (decay + consolidate)
echo "[$(date '+%H:%M:%S')] 메모리 decay 실행" >> "$LOG_FILE"
$PYTHON scripts/memory.py decay >> "$LOG_FILE" 2>&1 || true
$PYTHON scripts/memory.py consolidate >> "$LOG_FILE" 2>&1 || true

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 일일 유지보수 완료" >> "$LOG_FILE"

# 4. 브라우저/시스템 캐시 정리 (04:30 실행 시만)
CURRENT_HOUR=$(date +%H)
if [ "$CURRENT_HOUR" = "04" ]; then
  echo "[$(date '+%H:%M:%S')] 캐시 정리 실행" >> "$LOG_FILE"
  FREED=0

  # npm 캐시
  NPM_BEFORE=$(du -sm ~/.npm/_cacache 2>/dev/null | cut -f1 || echo 0)
  npm cache clean --force >> "$LOG_FILE" 2>&1 || true
  FREED=$((FREED + NPM_BEFORE))

  # 브라우저 캐시
  for DIR in \
    "$HOME/Library/Caches/Google" \
    "$HOME/Library/Caches/Microsoft Edge" \
    "$HOME/Library/Caches/Google Earth" \
    "$HOME/Library/Caches/com.google.antigravity.ShipIt"; do
    if [ -d "$DIR" ]; then
      SIZE=$(du -sm "$DIR" 2>/dev/null | cut -f1 || echo 0)
      rm -rf "$DIR" 2>/dev/null
      FREED=$((FREED + SIZE))
    fi
  done

  # 김치랑 로그 truncate (10MB 초과 시)
  KR_LOG="$PROJECT_DIR/logs/kimchirang.log"
  if [ -f "$KR_LOG" ]; then
    KR_SIZE=$(du -sm "$KR_LOG" 2>/dev/null | cut -f1 || echo 0)
    if [ "$KR_SIZE" -gt 10 ]; then
      tail -1000 "$KR_LOG" > "${KR_LOG}.tmp" && mv "${KR_LOG}.tmp" "$KR_LOG"
      FREED=$((FREED + KR_SIZE - 1))
    fi
  fi

  echo "[$(date '+%H:%M:%S')] 캐시 정리 완료: ~${FREED}MB 확보" >> "$LOG_FILE"
fi

# 오래된 로그 정리 (30일+)
find "$LOG_DIR" -name "maintenance_*.log" -mtime +30 -delete 2>/dev/null || true
