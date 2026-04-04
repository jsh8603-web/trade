#!/bin/bash
# 안전한 git pull — RC(리모트랑) 보호 + 자동 복원
# RC 세션을 건드리지 않고 코드만 업데이트한다.
# 사용법: bash ~/workspace/blockchain/scripts/safe_pull.sh

set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"

cd ~/workspace/blockchain
source .venv/bin/activate 2>/dev/null
set -a; source .env 2>/dev/null; set +a

LOG_FILE="logs/safe_pull_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

log() { echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

# ============================================================
# 1단계: RC 상태 백업
# ============================================================
log "📸 1/5 RC 상태 백업"

RC_HEALTH_BACKUP=$(cat data/.rc_health.json 2>/dev/null || echo '{}')
RC_URL_BACKUP=$(cat data/remote_url.txt 2>/dev/null || echo '')
RC_REVIVE_TS_BACKUP=$(cat data/.rc_revive_ts 2>/dev/null || echo '')
RC_HEALTHY_COUNT_BACKUP=$(cat data/.rc_healthy_count 2>/dev/null || echo '0')
RC_FAIL_COUNT_BACKUP=$(cat data/.rc_fail_count 2>/dev/null || echo '0')
RC_REBUILD_COUNT_BACKUP=$(cat data/.rc_rebuild_count 2>/dev/null || echo '0')

# RC 윈도우 찾기
RC_SESSION=""
RC_WINDOW=""
for sess in main blockchain; do
    if tmux has-session -t "$sess" 2>/dev/null; then
        w=$(tmux list-windows -t "$sess" -F '#{window_name}' 2>/dev/null | grep -E '^rc(@|$)' | head -1)
        if [ -n "$w" ]; then
            RC_SESSION="$sess"
            RC_WINDOW="$w"
            break
        fi
    fi
done

if [ -n "$RC_WINDOW" ]; then
    RC_PID=$(tmux list-panes -t "$RC_SESSION:$RC_WINDOW" -F '#{pane_pid}' 2>/dev/null | head -1)
    log "  RC 세션: $RC_SESSION:$RC_WINDOW (PID: ${RC_PID:-unknown})"
    log "  RC URL: $RC_URL_BACKUP"
    log "  healthy_count: $RC_HEALTHY_COUNT_BACKUP, fail: $RC_FAIL_COUNT_BACKUP"
else
    log "  ⚠️ RC 윈도우 없음"
fi

# ============================================================
# 2단계: 워치독 일시 정지 (pull 중 간섭 방지)
# ============================================================
log "⏸️  2/5 워치독 일시 정지"

WATCHDOG_PAUSE_FILE="data/.watchdog_pause"
echo "$(date +%s)" > "$WATCHDOG_PAUSE_FILE"
log "  pause 파일 생성: $WATCHDOG_PAUSE_FILE"

# ============================================================
# 3단계: git pull (RC 관련 파일 보호)
# ============================================================
log "📥 3/5 git pull 실행"

# stash 할 로컬 변경이 있는지 확인
STASH_NEEDED=false
if ! git diff --quiet scripts/revive_rc.sh scripts/watchdog_remote.sh 2>/dev/null; then
    STASH_NEEDED=true
    log "  RC 스크립트 로컬 변경 감지 — stash"
    git stash push -m "safe_pull: RC scripts backup $(date +%Y%m%d_%H%M%S)" \
        -- scripts/revive_rc.sh scripts/watchdog_remote.sh
fi

# pull 실행
PULL_OUTPUT=$(git pull origin main 2>&1) || {
    log "❌ git pull 실패: $PULL_OUTPUT"
    # stash 복원
    if [ "$STASH_NEEDED" = true ]; then
        git stash pop 2>/dev/null || true
    fi
    rm -f "$WATCHDOG_PAUSE_FILE"
    exit 1
}
log "  $PULL_OUTPUT"

# stash 복원
if [ "$STASH_NEEDED" = true ]; then
    git stash pop 2>/dev/null || {
        log "  ⚠️ stash pop 충돌 — 수동 확인 필요"
    }
fi

# ============================================================
# 4단계: RC 상태 파일 복원 (pull이 덮어썼을 수 있음)
# ============================================================
log "🔄 4/5 RC 상태 복원"

echo "$RC_HEALTH_BACKUP" > data/.rc_health.json
[ -n "$RC_URL_BACKUP" ] && echo "$RC_URL_BACKUP" > data/remote_url.txt
[ -n "$RC_REVIVE_TS_BACKUP" ] && echo "$RC_REVIVE_TS_BACKUP" > data/.rc_revive_ts
echo "$RC_HEALTHY_COUNT_BACKUP" > data/.rc_healthy_count
echo "$RC_FAIL_COUNT_BACKUP" > data/.rc_fail_count
echo "$RC_REBUILD_COUNT_BACKUP" > data/.rc_rebuild_count

log "  상태 파일 복원 완료"

# RC 프로세스 생존 확인
if [ -n "$RC_WINDOW" ]; then
    RC_SCREEN=$(tmux capture-pane -t "$RC_SESSION:$RC_WINDOW" -p -S -5 2>/dev/null)
    if echo "$RC_SCREEN" | grep -qE 'Remote Control active|Remote Control ❯|Session ID|Cooking|Thinking|Running'; then
        log "  ✅ RC 세션 정상 생존"
    elif echo "$RC_SCREEN" | grep -q "Remote Control reconnecting"; then
        log "  ⚠️ RC reconnecting — 자동 복구 대기"
    else
        log "  ❌ RC 세션 비정상 — revive_rc.sh 호출"
        bash scripts/revive_rc.sh &
    fi
fi

# ============================================================
# 5단계: 워치독 재개
# ============================================================
log "▶️  5/5 워치독 재개"

rm -f "$WATCHDOG_PAUSE_FILE"
log "  pause 파일 제거"

# 최종 상태 확인
log ""
log "=== safe_pull 완료 ==="
log "  현재 커밋: $(git log --oneline -1)"
if [ -n "$RC_WINDOW" ]; then
    log "  RC 상태: $(cat data/.rc_health.json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"status\",\"unknown\"))' 2>/dev/null || echo 'unknown')"
fi
log "  로그: $LOG_FILE"
