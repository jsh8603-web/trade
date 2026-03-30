#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────
# 단타 봇 랜덤 2시간 실행 스크립트
#
# 하루 1회 실행되며, 랜덤 대기 후 2시간 동안 단타 봇을 돌린다.
# cron으로 매일 자정(또는 원하는 시각)에 등록하면 된다.
#
# 사용법:
#   bash scripts/run_short_term_random.sh          # 기본 2시간
#   bash scripts/run_short_term_random.sh 3        # 3시간 실행
#
# cron 예시 (매일 00:05에 실행 → 랜덤 시각에 2시간 단타):
#   5 0 * * * cd ~/workspace/blockchain && bash scripts/run_short_term_random.sh
# ──────────────────────────────────────────────────────────

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# .env 로드
if [ -f .env ]; then
  set -a; source .env; set +a
fi

# Python 가상환경
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

# 머신 이름
MACHINE_TAG="[${MACHINE_NAME:-$(hostname -s)}]"

# 실행 시간 (시간 단위, 기본 2시간)
RUN_HOURS=${1:-2}
RUN_SECONDS=$((RUN_HOURS * 3600))

# 랜덤 대기: 0~22시간 중 랜덤 (2시간 실행 고려하여 22시간 범위)
MAX_WAIT_HOURS=$((24 - RUN_HOURS))
RANDOM_WAIT=$((RANDOM % (MAX_WAIT_HOURS * 3600)))
RANDOM_WAIT_H=$((RANDOM_WAIT / 3600))
RANDOM_WAIT_M=$(((RANDOM_WAIT % 3600) / 60))

START_TIME=$(date -v+${RANDOM_WAIT}S '+%H:%M' 2>/dev/null || date -d "+${RANDOM_WAIT} seconds" '+%H:%M' 2>/dev/null || echo "??:??")

LOG_DIR="logs/short_term"
mkdir -p "$LOG_DIR" 2>/dev/null
# 외장하드 심볼릭 쓰기 불가 시 /tmp fallback
if ! touch "$LOG_DIR/.write_test" 2>/dev/null; then
    LOG_DIR="/tmp/blockchain_logs/short_term"
    mkdir -p "$LOG_DIR"
fi
rm -f "$LOG_DIR/.write_test" 2>/dev/null
LOG_FILE="${LOG_DIR}/random_$(date +%Y%m%d).log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 랜덤 단타 스케줄러 시작" | tee -a "$LOG_FILE"
echo "  대기: ${RANDOM_WAIT_H}시간 ${RANDOM_WAIT_M}분 → 예상 시작: ${START_TIME}" | tee -a "$LOG_FILE"
echo "  실행 시간: ${RUN_HOURS}시간" | tee -a "$LOG_FILE"

# 텔레그램 알림 (선택)
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_USER_ID:-}" ]; then
  MSG="단타 봇 예약: ${START_TIME} 시작 예정 (${RUN_HOURS}시간, DRY_RUN=${DRY_RUN:-true}) ${MACHINE_TAG}"
  curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_USER_ID}" \
    -d "text=${MSG}" > /dev/null 2>&1 || true
fi

# 랜덤 대기
sleep "$RANDOM_WAIT"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 단타 봇 시작 (${RUN_HOURS}시간)" | tee -a "$LOG_FILE"

# 텔레그램 알림
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_USER_ID:-}" ]; then
  MSG="단타 봇 시작 (DRY_RUN=${DRY_RUN:-true}, ${RUN_HOURS}시간) ${MACHINE_TAG}"
  curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_USER_ID}" \
    -d "text=${MSG}" > /dev/null 2>&1 || true
fi

# 단타 봇 실행 (.env DRY_RUN 설정 따름)
python3 scripts/short_term_trader.py >> "$LOG_FILE" 2>&1 &
BOT_PID=$!

echo "  PID: ${BOT_PID}" | tee -a "$LOG_FILE"

# 지정 시간 후 종료
sleep "$RUN_SECONDS"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${RUN_HOURS}시간 경과 — 봇 종료" | tee -a "$LOG_FILE"

# SIGINT로 정상 종료 (세션 요약 + DB 기록을 위해)
kill -INT "$BOT_PID" 2>/dev/null || true
sleep 15  # v4: 5→15초 대기 (DB 기록 시간 확보)

# 아직 살아있으면 SIGTERM 시도 후 강제 종료
if kill -0 "$BOT_PID" 2>/dev/null; then
  kill -TERM "$BOT_PID" 2>/dev/null || true
  sleep 5
  if kill -0 "$BOT_PID" 2>/dev/null; then
    kill -9 "$BOT_PID" 2>/dev/null || true
    echo "  강제 종료됨" | tee -a "$LOG_FILE"
  fi
fi

# 텔레그램 알림
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_USER_ID:-}" ]; then
  # 로그 마지막 20줄에서 세션 요약 추출
  SUMMARY=$(tail -20 "$LOG_FILE" | grep -A 10 "세션 요약" || echo "세션 요약 없음")
  MSG="단타 봇 종료 (${RUN_HOURS}시간 완료) ${MACHINE_TAG}
${SUMMARY}"
  curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_USER_ID}" \
    -d "text=${MSG}" > /dev/null 2>&1 || true
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 랜덤 단타 스케줄러 종료" | tee -a "$LOG_FILE"
