#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────
# 초단타 봇 24시간 연속 운영 스크립트
#
# DRY_RUN=true 고정. 수수료 포함 수익률 추적.
# 봇이 크래시하면 자동 재시작 (무한 루프).
# 매 세션 종료 시 텔레그램 보고.
#
# 사용법:
#   bash scripts/run_short_term_24h.sh
# ──────────────────────────────────────────────────────────

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# .env 로드
if [ -f .env ]; then
  set -a; source .env; set +a
fi

# 초단타는 DRY_RUN=true 강제 (승률 검증 전까지)
export DRY_RUN=true

# Python 실행파일 결정 (venv 직접 사용)
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python3"
fi

LOG_DIR="logs/short_term"
mkdir -p "$LOG_DIR"

# v5: 중복 실행 방지 (PID lock)
PIDFILE="data/.short_term_bot.pid"
if [ -f "$PIDFILE" ]; then
  OLD_PID=$(cat "$PIDFILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 이미 실행 중 (PID $OLD_PID) — 종료" | tee -a "$LOG_DIR/launchd_stdout.log"
    exit 0
  fi
fi
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT

# 텔레그램 알림 함수
notify() {
  local msg="$1"
  if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_USER_ID:-}" ]; then
    curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d "chat_id=${TELEGRAM_USER_ID}" \
      -d "text=${msg}" > /dev/null 2>&1 || true
  fi
}

notify "🔄 초단타 봇 24시간 연속 운영 시작 (DRY_RUN=true, 훈련 모드)"

CRASH_COUNT=0
MAX_CRASH=10  # 10회 연속 크래시 시 중단

while true; do
  LOG_FILE="${LOG_DIR}/scalp_24h_$(date +%Y%m%d_%H%M%S).log"

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 초단타 봇 시작 (DRY_RUN=true, 24h 연속)" | tee -a "$LOG_FILE"

  # 봇 실행
  "$PYTHON" scripts/short_term_trader.py --dry-run >> "$LOG_FILE" 2>&1
  EXIT_CODE=$?

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 봇 종료 (exit code: ${EXIT_CODE})" | tee -a "$LOG_FILE"

  if [ $EXIT_CODE -eq 0 ] || [ $EXIT_CODE -eq 130 ] || [ $EXIT_CODE -eq 143 ]; then
    # 정상 종료: 0=정상, 130=SIGINT, 143=SIGTERM
    CRASH_COUNT=0

    # 세션 요약 추출 + 텔레그램 보고
    SUMMARY=$(tail -30 "$LOG_FILE" | grep -A 15 "세션 요약" || echo "세션 요약 없음")
    notify "📊 초단타 세션 종료 (정상)
${SUMMARY}"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 10초 후 재시작..." | tee -a "$LOG_FILE"
    sleep 10
  else
    # 비정상 종료
    CRASH_COUNT=$((CRASH_COUNT + 1))
    LAST_ERROR=$(tail -5 "$LOG_FILE" | head -3)

    notify "⚠️ 초단타 봇 크래시 #${CRASH_COUNT} (exit: ${EXIT_CODE})
${LAST_ERROR}"

    if [ $CRASH_COUNT -ge $MAX_CRASH ]; then
      notify "🛑 초단타 봇 ${MAX_CRASH}회 연속 크래시 — 자동 중단"
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${MAX_CRASH}회 연속 크래시 — 중단" | tee -a "$LOG_FILE"
      exit 1
    fi

    # 크래시 후 대기 (점점 길게)
    WAIT=$((30 * CRASH_COUNT))
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${WAIT}초 후 재시작 (크래시 #${CRASH_COUNT})" | tee -a "$LOG_FILE"
    sleep "$WAIT"
  fi
done
