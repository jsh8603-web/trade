#!/bin/bash
# =============================================================================
# 부팅 시 자동 실행 스크립트
# tmux → Claude Code (remote-control) → Dashboard → QR 페이지
# =============================================================================

set -e

PROJECT_DIR="/Users/drj00/workspace/blockchain"
REMOTE_URL_FILE="$PROJECT_DIR/data/remote_url.txt"
LOG_DIR="$PROJECT_DIR/logs"
TMUX_SESSION="blockchain"
DASHBOARD_PORT=5555

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/startup.log"
}

# --- 0. 준비 ---
mkdir -p "$LOG_DIR" "$PROJECT_DIR/data/charts" "$PROJECT_DIR/data/snapshots"
log "=== Startup begin ==="

# --- 0.1 오래된 데이터 자동 정리 ---
find "$PROJECT_DIR/data/snapshots" -maxdepth 1 -type d -mtime +7 -exec rm -rf {} + 2>/dev/null
find "$PROJECT_DIR/data/charts" -name "*.png" -mtime +7 -delete 2>/dev/null
# 로그 로테이션: 10MB 초과 시 1MB로 truncate, 30일 이상 개별 로그 삭제
find "$LOG_DIR" -name "*.log" -size +10M -exec truncate -s 1M {} \; 2>/dev/null
find "$LOG_DIR/executions" -name "*.log" -mtime +30 -delete 2>/dev/null
find "$LOG_DIR/claude_responses" -name "*.txt" -mtime +30 -delete 2>/dev/null
find "$LOG_DIR/short_term" -name "scalp_24h_*.log" -mtime +14 -delete 2>/dev/null
find "$LOG_DIR/short_term" -name "random_*.log" -mtime +14 -delete 2>/dev/null
find "$LOG_DIR/short_term" -name "trader_*.log" -mtime +14 -delete 2>/dev/null
log "Cleanup: old snapshots/charts/logs trimmed"

# --- 1. 기존 세션 정리 (살아있는 세션 보호) ---
# ★ 살아있는 RC 세션이 있으면 보존, 죽은 것만 정리
LIVE_RC_EXISTS=false
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    # 모든 윈도우 순회하여 살아있는 RC 확인
    while IFS=: read -r idx name; do
        screen=$(tmux capture-pane -t "${TMUX_SESSION}:${idx}" -p 2>/dev/null)
        if echo "$screen" | grep -q "Remote Control active"; then
            pane_pid=$(tmux list-panes -t "${TMUX_SESSION}:${idx}" -F '#{pane_pid}' 2>/dev/null | head -1)
            child_claude=$(pgrep -P "$pane_pid" -f "claude" 2>/dev/null | head -1)
            if [ -n "$child_claude" ] && ps -p "$child_claude" >/dev/null 2>&1; then
                LIVE_RC_EXISTS=true
                log "PROTECT: Live RC session at window ${idx}:${name} (PID=$child_claude) — NOT killing"
            fi
        fi
    done <<< "$(tmux list-windows -t "$TMUX_SESSION" -F '#{window_index}:#{window_name}' 2>/dev/null)"

    if [ "$LIVE_RC_EXISTS" = true ]; then
        # 살아있는 RC가 있으면 죽은 윈도우만 정리
        log "Live RC session found — cleaning dead windows only"
        while IFS=: read -r idx name; do
            [ "$name" = "dashboard" ] && continue
            pane_pid=$(tmux list-panes -t "${TMUX_SESSION}:${idx}" -F '#{pane_pid}' 2>/dev/null | head -1)
            [ -z "$pane_pid" ] && continue
            child_claude=$(pgrep -P "$pane_pid" -f "claude" 2>/dev/null | head -1)
            screen=$(tmux capture-pane -t "${TMUX_SESSION}:${idx}" -p 2>/dev/null)
            # claude 자식 없고 RC active도 아닌 빈 윈도우만 제거
            if [ -z "$child_claude" ] && ! echo "$screen" | grep -q "Remote Control active"; then
                log "CLEANUP: Removing dead window ${idx}:${name}"
                tmux kill-window -t "${TMUX_SESSION}:${idx}" 2>/dev/null
            fi
        done <<< "$(tmux list-windows -t "$TMUX_SESSION" -F '#{window_index}:#{window_name}' 2>/dev/null)"
    else
        # 살아있는 RC 없음 → 기존처럼 전체 정리
        log "No live RC session — killing entire tmux session"
        tmux kill-session -t "$TMUX_SESSION" 2>/dev/null || true
    fi
fi

# 기존 대시보드 프로세스 정리 (포트 충돌 방지)
if [ "$LIVE_RC_EXISTS" = false ]; then
    lsof -i :$DASHBOARD_PORT -t 2>/dev/null | xargs kill -9 2>/dev/null || true
    sleep 3

    # 포트 해제 확인 (TIME_WAIT 대기)
    for i in $(seq 1 10); do
        if ! lsof -i :$DASHBOARD_PORT -t >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
fi

# --- 2. tmux 세션 + 대시보드 + Claude RC ---
if [ "$LIVE_RC_EXISTS" = true ]; then
    # 살아있는 RC가 있으면 세션/Claude/RC 생성 건너뜀
    log "SKIP: Live RC session exists — reusing existing session"
    REMOTE_URL=$(cat "$REMOTE_URL_FILE" 2>/dev/null)

    # 대시보드만 확인/재시작
    if ! lsof -i :$DASHBOARD_PORT -t >/dev/null 2>&1; then
        if tmux list-windows -t "$TMUX_SESSION" -F '#{window_name}' 2>/dev/null | grep -q "^dashboard$"; then
            tmux send-keys -t "$TMUX_SESSION:dashboard" C-c
            sleep 1
            tmux send-keys -t "$TMUX_SESSION:dashboard" "source .venv/bin/activate && PYTHONPATH=/Users/drj00/workspace/blockchain python scripts/dashboard.py $DASHBOARD_PORT" Enter
        else
            tmux new-window -t "$TMUX_SESSION" -n dashboard -c "$PROJECT_DIR"
            tmux send-keys -t "$TMUX_SESSION:dashboard" "source .venv/bin/activate && PYTHONPATH=/Users/drj00/workspace/blockchain python scripts/dashboard.py $DASHBOARD_PORT" Enter
        fi
        log "Dashboard restarted on port $DASHBOARD_PORT"
    fi
else
    # --- 새로 생성 ---
    # 2. tmux 세션 생성
    tmux new-session -d -s "$TMUX_SESSION" -n dashboard -c "$PROJECT_DIR"
    log "tmux session created: $TMUX_SESSION"

    # 3. 대시보드 실행 (윈도우 0: dashboard)
    tmux send-keys -t "$TMUX_SESSION:dashboard" "source .venv/bin/activate && PYTHONPATH=/Users/drj00/workspace/blockchain python scripts/dashboard.py $DASHBOARD_PORT" Enter
    log "Dashboard starting on port $DASHBOARD_PORT"

    # 4. Claude Code 원격 세션 (윈도우 이름에 시작 시간 포함)
    RC_WIN_NAME="rc@$(date '+%H%M')"
    tmux new-window -t "$TMUX_SESSION" -n "$RC_WIN_NAME" -c "$PROJECT_DIR"
    tmux send-keys -t "$TMUX_SESSION:$RC_WIN_NAME" "unset CLAUDECODE && claude --dangerously-skip-permissions" Enter
    log "Claude Code starting..."

    # Claude 초기화 대기 (v2.1.78+ 기준 30초 필요)
    sleep 30

    # /remote-control 실행 (/rc는 자동완성 메뉴 충돌)
    tmux send-keys -t "$TMUX_SESSION:$RC_WIN_NAME" "/remote-control" Enter
    sleep 5
    # 자동완성 메뉴 선택
    tmux send-keys -t "$TMUX_SESSION:$RC_WIN_NAME" Enter
    log "Remote Control connecting..."

    # remote-control 연결 대기 및 URL 추출
    MAX_WAIT=120
    WAITED=0
    REMOTE_URL=""

    while [ $WAITED -lt $MAX_WAIT ]; do
        sleep 5
        WAITED=$((WAITED + 5))

        # tmux pane에서 URL 추출
        PANE_OUTPUT=$(tmux capture-pane -t "$TMUX_SESSION:$RC_WIN_NAME" -p -S -30 2>/dev/null)
        REMOTE_URL=$(echo "$PANE_OUTPUT" | grep -o 'https://claude.ai/code/session_[A-Za-z0-9]*' | tail -1)

        if [ -n "$REMOTE_URL" ]; then
            log "Remote Control URL: $REMOTE_URL"
            echo "$REMOTE_URL" > "$REMOTE_URL_FILE"
            break
        fi

        log "Waiting for remote URL... (${WAITED}s)"
    done

    if [ -z "$REMOTE_URL" ]; then
        log "WARNING: Could not capture remote URL after ${MAX_WAIT}s"
        echo "https://claude.ai/code/pending" > "$REMOTE_URL_FILE"
    fi
fi

log "Remote Control setup complete"

# --- 5. 텔레그램으로 새 URL 전송 ---
source "$PROJECT_DIR/.env"
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || echo '127.0.0.1')
DASHBOARD_URL="http://${LOCAL_IP}:${DASHBOARD_PORT}"
QR_URL="${DASHBOARD_URL}/qr"
REMOTE_URL_FINAL=$(cat "$REMOTE_URL_FILE")

MSG="Crypto Bot Started

Claude Code Remote:
${REMOTE_URL_FINAL}

Dashboard:
${DASHBOARD_URL}

QR Page:
${QR_URL}

$(date '+%Y-%m-%d %H:%M:%S')"

curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_USER_ID}" \
    --data-urlencode "text=${MSG}" \
    -d "disable_web_page_preview=true" > /dev/null 2>&1

log "Telegram notification sent"

# --- 6. 완료 ---
log "=== Startup complete ==="
log "  Dashboard: ${DASHBOARD_URL}"
log "  QR page:   ${QR_URL}"
log "  Remote:    ${REMOTE_URL_FINAL}"
log "  tmux:      tmux attach -t $TMUX_SESSION"
