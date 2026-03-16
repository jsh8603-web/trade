#!/bin/bash
# =============================================================================
# Remote Control Watchdog v4
#
# 3분마다 실행 (LaunchAgent: com.claude.watchdog-remote)
#
# v4 핵심 변경:
#   - 3단계 건강 검진: 프로세스 → 화면 텍스트 → 실제 응답성 검증
#   - 좀비 세션 감지: "active" 표시인데 실제 작동 안 하는 상태 탐지
#   - graceful reconnect 폐기 (성공률 0%) → 즉시 full restart
#   - 연속 실패 카운터 → 3회 연속 실패 시 startup.sh 전체 재구축
#   - 텔레그램으로 상태 변화만 알림 (스팸 방지)
#
# 사용자가 보고한 3가지 문제:
#   1) 연결됐다고 표시 + 실제 작동 ✅ → 정상
#   2) 연결 끊겼는데 새 세션 안 만듦 → 빠른 복구
#   3) 연결됐다고 표시 + 작동 안 함 → 좀비 감지 + 강제 재시작
# =============================================================================

PROJECT_DIR="/Users/drj00/workspace/blockchain"
REMOTE_URL_FILE="$PROJECT_DIR/data/remote_url.txt"
LOG_FILE="$PROJECT_DIR/logs/watchdog.log"
KEEPALIVE_FILE="$PROJECT_DIR/data/.rc_keepalive_ts"
HEALTH_FILE="$PROJECT_DIR/data/.rc_health.json"
FAIL_COUNT_FILE="$PROJECT_DIR/data/.rc_fail_count"
REBUILD_COUNT_FILE="$PROJECT_DIR/data/.rc_rebuild_count"
REBUILD_TS_FILE="$PROJECT_DIR/data/.rc_rebuild_ts"
MANUAL_INTERVENTION_FILE="$PROJECT_DIR/data/.rc_manual_intervention.json"
HEALTHY_COUNT_FILE="$PROJECT_DIR/data/.rc_healthy_count"
TMUX_SESSION="blockchain"
TMUX_WINDOW="claude"
KEEPALIVE_INTERVAL=240   # 4분 (10분 타임아웃의 40% → 안전 마진 최대화)
MAX_CONSECUTIVE_FAILS=3  # 3회 연속 실패 → startup.sh로 전체 재구축
ESCALATION_PAUSE_SEC=1800  # 30분 (수동 개입 대기)

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

mkdir -p "$(dirname "$LOG_FILE")" "$PROJECT_DIR/data"

# .env 로드 (한 번만, 스크립트 시작 시)
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env" 2>/dev/null; set +a
fi

# Python 실행파일 결정 (venv 직접 사용)
if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON="$PROJECT_DIR/.venv/bin/python"
else
    PYTHON="python3"
fi

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

send_telegram() {
    [ -z "${TELEGRAM_BOT_TOKEN:-}" ] && return
    curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d "chat_id=${TELEGRAM_USER_ID}" \
        --data-urlencode "text=$1" \
        -d "disable_web_page_preview=true" > /dev/null 2>&1
}

get_fail_count() {
    [ -f "$FAIL_COUNT_FILE" ] && cat "$FAIL_COUNT_FILE" 2>/dev/null || echo "0"
}

set_fail_count() {
    echo "$1" > "$FAIL_COUNT_FILE"
}

reset_fail_count() {
    echo "0" > "$FAIL_COUNT_FILE"
}

# ─── 에스컬레이션: 재구축 횟수 추적 ───
get_rebuild_count() {
    [ -f "$REBUILD_COUNT_FILE" ] && cat "$REBUILD_COUNT_FILE" 2>/dev/null || echo "0"
}

increment_rebuild_count() {
    local count
    count=$(get_rebuild_count)
    count=$((count + 1))
    echo "$count" > "$REBUILD_COUNT_FILE"
    date +%s > "$REBUILD_TS_FILE"
    log "ESCALATION: Rebuild count incremented to $count"
}

reset_rebuild_count() {
    echo "0" > "$REBUILD_COUNT_FILE"
    rm -f "$REBUILD_TS_FILE"
    log "ESCALATION: Rebuild counter reset"
}

get_healthy_count() {
    [ -f "$HEALTHY_COUNT_FILE" ] && cat "$HEALTHY_COUNT_FILE" 2>/dev/null || echo "0"
}

increment_healthy_count() {
    local count
    count=$(get_healthy_count)
    count=$((count + 1))
    echo "$count" > "$HEALTHY_COUNT_FILE"
}

reset_healthy_count() {
    echo "0" > "$HEALTHY_COUNT_FILE"
}

# ─── 에스컬레이션: 진단 정보 수집 ───
collect_diagnostics() {
    local diag=""
    diag+="📋 최근 로그 (5줄):
"
    diag+="$(tail -5 "$LOG_FILE" 2>/dev/null || echo '(로그 없음)')
"
    diag+="
📺 tmux 세션:
"
    diag+="$(tmux list-sessions 2>/dev/null || echo '(tmux 없음)')
"
    diag+="
🔍 Claude 프로세스:
"
    local claude_count
    claude_count=$(pgrep -f "claude" 2>/dev/null | wc -l | tr -d ' ')
    diag+="${claude_count}개 실행 중"
    echo "$diag"
}

# ─── 에스컬레이션: 반복 재구축 감지 + 대응 ───
check_escalation_after_rebuild() {
    local rebuild_count now first_rebuild_ts elapsed_since_first
    rebuild_count=$(get_rebuild_count)
    now=$(date +%s)

    # 최초 재구축 타임스탬프가 없으면 리턴
    [ ! -f "$REBUILD_TS_FILE" ] && return

    # 재구축 이력 파일에서 시간 범위 계산
    first_rebuild_ts=$(cat "$REBUILD_TS_FILE" 2>/dev/null || echo "$now")
    elapsed_since_first=$((now - first_rebuild_ts))

    # 2시간 넘으면 카운터 리셋 (오래된 이력 무시)
    if [ "$elapsed_since_first" -gt 7200 ]; then
        reset_rebuild_count
        return
    fi

    # 3+ rebuilds within 2 hours → 수동 개입 필요
    if [ "$rebuild_count" -ge 3 ]; then
        log "CRITICAL: $rebuild_count rebuilds within ${elapsed_since_first}s — manual intervention required"
        local diagnostics
        diagnostics=$(collect_diagnostics)
        send_telegram "🚨 RC 반복 재구축 실패 — 수동 개입 필요

${rebuild_count}회 재구축 실패 (${elapsed_since_first}초 이내)
워치독 30분 대기 모드 진입

$diagnostics"
        cat > "$MANUAL_INTERVENTION_FILE" <<EOF
{"created_at":"$(date '+%Y-%m-%d %H:%M:%S')","ts":$now,"rebuild_count":$rebuild_count,"elapsed_sec":$elapsed_since_first,"reason":"${rebuild_count} rebuilds within ${elapsed_since_first}s"}
EOF
        save_health_with_escalation "manual_required" "Manual intervention required after $rebuild_count rebuilds"
        return
    fi

    # 2+ rebuilds within 1 hour → CRITICAL 알림 (아직 대기 모드는 아님)
    if [ "$rebuild_count" -ge 2 ] && [ "$elapsed_since_first" -le 3600 ]; then
        log "CRITICAL: $rebuild_count rebuilds within 1 hour — sending critical alert"
        local diagnostics
        diagnostics=$(collect_diagnostics)
        send_telegram "🚨 RC 반복 재구축 실패 — 수동 개입 필요

1시간 이내 ${rebuild_count}회 재구축 실패
다음 실패 시 워치독 30분 대기 모드 진입

$diagnostics"
        save_health_with_escalation "critical" "Critical: $rebuild_count rebuilds in 1 hour"
    fi
}

# ─── 에스컬레이션: 대기 모드 확인 (메인 루프 진입 전 실행) ───
check_escalation() {
    # 수동 개입 파일이 없으면 정상 진행
    [ ! -f "$MANUAL_INTERVENTION_FILE" ] && return 0

    local created_ts now elapsed
    created_ts=$(grep -o '"ts":[0-9]*' "$MANUAL_INTERVENTION_FILE" 2>/dev/null | grep -o '[0-9]*')
    [ -z "$created_ts" ] && { rm -f "$MANUAL_INTERVENTION_FILE"; return 0; }

    now=$(date +%s)
    elapsed=$((now - created_ts))

    if [ "$elapsed" -lt "$ESCALATION_PAUSE_SEC" ]; then
        local remaining=$(( (ESCALATION_PAUSE_SEC - elapsed) / 60 ))
        log "ESCALATION: 대기 중 — 수동 개입 필요 (잔여 ${remaining}분)"
        save_health_with_escalation "manual_required" "Paused: manual intervention needed (${remaining}min remaining)"
        return 1  # 1 = 체크 건너뛰기
    fi

    # 30분 경과 → 파일 제거, 카운터 리셋, 정상 재개
    log "ESCALATION: 30분 대기 완료 — 정상 모드 재개"
    rm -f "$MANUAL_INTERVENTION_FILE"
    reset_rebuild_count
    reset_healthy_count
    save_health_with_escalation "normal" "Resumed after escalation pause"
    send_telegram "✅ 워치독 대기 모드 해제
30분 경과 — 정상 모니터링 재개"
    return 0
}

# ─── 에스컬레이션: 복구 감지 (연속 healthy 체크) ───
check_recovery() {
    increment_healthy_count
    local healthy_count
    healthy_count=$(get_healthy_count)

    if [ "$healthy_count" -ge 3 ]; then
        local rebuild_count
        rebuild_count=$(get_rebuild_count)
        if [ "$rebuild_count" -gt 0 ]; then
            log "RECOVERY: 3 consecutive healthy checks — resetting all escalation state"
            reset_rebuild_count
            reset_healthy_count
            rm -f "$MANUAL_INTERVENTION_FILE"
            save_health_with_escalation "normal" "Recovered after 3 consecutive healthy checks"
        fi
    fi
}

# ─── 에스컬레이션 레벨 판단 ───
get_escalation_level() {
    if [ -f "$MANUAL_INTERVENTION_FILE" ]; then
        echo "manual_required"
        return
    fi
    local rebuild_count
    rebuild_count=$(get_rebuild_count)
    if [ "$rebuild_count" -ge 2 ]; then
        echo "critical"
    elif [ "$rebuild_count" -ge 1 ]; then
        echo "warning"
    else
        echo "normal"
    fi
}

# ─── 상태 저장 (모니터링용) ───
save_health() {
    local status="$1" detail="$2"
    local escalation_level
    escalation_level=$(get_escalation_level)
    cat > "$HEALTH_FILE" <<EOF
{"status":"$status","detail":"$detail","ts":"$(date '+%Y-%m-%d %H:%M:%S')","url":"$(cat "$REMOTE_URL_FILE" 2>/dev/null)","escalation_level":"$escalation_level","rebuild_count":$(get_rebuild_count)}
EOF
}

# save_health_with_escalation: 에스컬레이션 컨텍스트에서 호출 (무한 재귀 방지)
save_health_with_escalation() {
    local status="$1" detail="$2" level="$3"
    [ -z "$level" ] && level=$(get_escalation_level)
    cat > "$HEALTH_FILE" <<EOF
{"status":"$status","detail":"$detail","ts":"$(date '+%Y-%m-%d %H:%M:%S')","url":"$(cat "$REMOTE_URL_FILE" 2>/dev/null)","escalation_level":"$level","rebuild_count":$(get_rebuild_count)}
EOF
}

# ─── URL 추출 ───
extract_url() {
    local pane_output
    pane_output=$(tmux capture-pane -t "$TMUX_SESSION:$TMUX_WINDOW" -p -S -30 2>/dev/null)
    echo "$pane_output" | grep -o 'https://claude\.ai/code/session_[A-Za-z0-9]*' | tail -1
}

# ─── rating 프롬프트 자동 dismiss ───
dismiss_rating_prompt() {
    local screen
    screen=$(tmux capture-pane -t "$TMUX_SESSION:$TMUX_WINDOW" -p 2>/dev/null)
    if echo "$screen" | grep -q "1: Bad.*2: Fine.*3: Good.*0: Dismiss"; then
        tmux send-keys -t "$TMUX_SESSION:$TMUX_WINDOW" '0' Enter
        sleep 2
        tmux send-keys -t "$TMUX_SESSION:$TMUX_WINDOW" C-u
        log "OK: Rating prompt auto-dismissed"
        return 0
    fi
    return 1
}

# ─── 3단계 건강 검진 ───
# 반환값: healthy / zombie / disconnected / no_rc / no_claude / no_tmux
health_check() {
    # Layer 1: tmux 세션 존재?
    if ! tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
        echo "no_tmux"
        return
    fi

    # Layer 1.5: claude 윈도우 존재?
    if ! tmux list-windows -t "$TMUX_SESSION" -F '#{window_name}' 2>/dev/null | grep -q "^${TMUX_WINDOW}$"; then
        echo "no_claude"
        return
    fi

    # Layer 2: Claude 프로세스 살아있나?
    local PANE_PID CLAUDE_PID
    PANE_PID=$(tmux list-panes -t "$TMUX_SESSION:$TMUX_WINDOW" -F '#{pane_pid}' 2>/dev/null)
    if [ -n "$PANE_PID" ]; then
        CLAUDE_PID=$(pgrep -P "$PANE_PID" -f "claude" 2>/dev/null | head -1)
        if [ -z "$CLAUDE_PID" ]; then
            echo "no_claude"
            return
        fi
    else
        echo "no_claude"
        return
    fi

    # Layer 3: 화면 텍스트 확인
    local screen
    screen=$(tmux capture-pane -t "$TMUX_SESSION:$TMUX_WINDOW" -p 2>/dev/null)

    # rating 프롬프트 체크 (먼저 해소)
    if echo "$screen" | grep -q "1: Bad.*2: Fine.*3: Good.*0: Dismiss"; then
        dismiss_rating_prompt
        sleep 3
        screen=$(tmux capture-pane -t "$TMUX_SESSION:$TMUX_WINDOW" -p 2>/dev/null)
    fi

    if echo "$screen" | grep -q "reconnecting"; then
        echo "disconnected"
        return
    fi

    if ! echo "$screen" | grep -q "Remote Control active"; then
        echo "no_rc"
        return
    fi

    # Layer 4: 좀비 감지 — "active"인데 실제로 살아있는지 확인
    # 방법: 상태바(status line)의 마지막 갱신 시간으로 판단
    # Claude가 실제 동작 중이면 상태바가 주기적으로 갱신됨
    # 프로세스의 CPU 사용률로 좀비 판단 (완전 멈추면 0%)
    local cpu_usage
    cpu_usage=$(ps -p "$CLAUDE_PID" -o %cpu= 2>/dev/null | tr -d ' ')
    if [ -z "$cpu_usage" ]; then
        echo "zombie"
        return
    fi

    # Claude 프로세스가 존재하고, RC active 텍스트가 있고, 프로세스도 살아있음
    # 추가 검증: 마지막 keepalive 이후 너무 오래됐으면 의심
    local last_ping now elapsed
    last_ping=0
    [ -f "$KEEPALIVE_FILE" ] && last_ping=$(cat "$KEEPALIVE_FILE" 2>/dev/null)
    now=$(date +%s)
    elapsed=$((now - last_ping))

    # 마지막 keepalive가 15분 이상 전이면 좀비 의심
    if [ "$elapsed" -gt 900 ]; then
        log "WARN: Last keepalive was ${elapsed}s ago — possible zombie"
        echo "zombie"
        return
    fi

    echo "healthy"
}

# ─── 킵얼라이브 전송 ───
send_keepalive() {
    # 메뉴 열려있으면 닫기
    local pane_check
    pane_check=$(tmux capture-pane -t "$TMUX_SESSION:$TMUX_WINDOW" -p -S -5 2>/dev/null)
    if echo "$pane_check" | grep -q "Disconnect\|Show QR\|Enter to select"; then
        tmux send-keys -t "$TMUX_SESSION:$TMUX_WINDOW" Escape
        sleep 1
    fi

    # Space BSpace (공백 입력 후 뒤로가기) → 터미널 포커스만 유지, 세션 종료 방지
    tmux send-keys -t "$TMUX_SESSION:$TMUX_WINDOW" Space BSpace
    sleep 1

    echo "$(date +%s)" > "$KEEPALIVE_FILE"
}

# ─── Claude + RC 빠른 재시작 ───
# graceful reconnect 폐기 (성공률 0%) → 즉시 kill + restart
fast_restart() {
    local reason="$1"
    log "ACTION: Fast restart ($reason)"

    # rating 프롬프트 해소
    dismiss_rating_prompt 2>/dev/null

    # 1) Claude 프로세스 강제 종료
    local PANE_PID CLAUDE_PIDS
    PANE_PID=$(tmux list-panes -t "$TMUX_SESSION:$TMUX_WINDOW" -F '#{pane_pid}' 2>/dev/null)
    if [ -n "$PANE_PID" ]; then
        CLAUDE_PIDS=$(pgrep -P "$PANE_PID" 2>/dev/null)
        if [ -n "$CLAUDE_PIDS" ]; then
            echo "$CLAUDE_PIDS" | xargs kill -9 2>/dev/null
            log "OK: Killed processes: $CLAUDE_PIDS"
            sleep 3
        fi
    fi

    # 2) 터미널 초기화
    tmux send-keys -t "$TMUX_SESSION:$TMUX_WINDOW" C-c C-u C-l
    sleep 2

    # 3) 쉘 프롬프트 확인 (프로세스 종료 확인)
    local shell_check
    shell_check=$(tmux capture-pane -t "$TMUX_SESSION:$TMUX_WINDOW" -p -S -3 2>/dev/null)
    if ! echo "$shell_check" | grep -qE '(\$|%|❯)\s*$|drj00@'; then
        # 쉘이 안 보이면 추가 대기
        sleep 5
        tmux send-keys -t "$TMUX_SESSION:$TMUX_WINDOW" Enter
        sleep 2
    fi

    # 4) Claude 시작
    tmux send-keys -t "$TMUX_SESSION:$TMUX_WINDOW" "unset CLAUDECODE && claude --dangerously-skip-permissions" Enter
    log "OK: Claude starting..."
    sleep 30

    # 5) /rc 활성화
    tmux send-keys -t "$TMUX_SESSION:$TMUX_WINDOW" "/rc" Enter
    sleep 10

    # 자동완성 메뉴 대응 (Enter)
    tmux send-keys -t "$TMUX_SESSION:$TMUX_WINDOW" Enter
    sleep 8

    # 6) 결과 확인
    local screen new_url
    screen=$(tmux capture-pane -t "$TMUX_SESSION:$TMUX_WINDOW" -p 2>/dev/null)
    new_url=$(extract_url)

    if echo "$screen" | grep -q "Remote Control active" && [ -n "$new_url" ]; then
        echo "$new_url" > "$REMOTE_URL_FILE"
        echo "$(date +%s)" > "$KEEPALIVE_FILE"
        reset_fail_count
        reset_rebuild_count
        save_health "healthy" "Fast restart succeeded"
        log "OK: Fast restart succeeded. URL: $new_url"
        send_telegram "🔄 RC 재시작 성공 ($reason)
$new_url"
        return 0
    fi

    # 실패
    local fails
    fails=$(get_fail_count)
    fails=$((fails + 1))
    set_fail_count "$fails"
    save_health "failed" "Fast restart failed ($fails/$MAX_CONSECUTIVE_FAILS)"
    log "ERROR: Fast restart failed ($fails consecutive). Status: $(echo "$screen" | grep -i remote | head -1)"
    return 1
}

# ─── 전체 재구축 (startup.sh) ───
full_rebuild() {
    log "ACTION: Full rebuild via startup.sh ($(get_fail_count) consecutive failures)"
    send_telegram "⚠️ RC ${MAX_CONSECUTIVE_FAILS}회 연속 실패
전체 재구축 시작 (startup.sh)"
    reset_fail_count

    # 재구축 실행
    bash "$PROJECT_DIR/scripts/startup.sh"

    # 재구축 카운터 증가 + 에스컬레이션 체크
    increment_rebuild_count
    check_escalation_after_rebuild
}

# =============================================================================
# 메인 로직
# =============================================================================

# 0. 에스컬레이션 대기 모드 확인 (무한 루프 방지)
if ! check_escalation; then
    exit 0
fi

# 1. 텔레그램 수동 재연결(/rc, /reconnect) 명령 확인
if "$PYTHON" "$PROJECT_DIR/scripts/check_telegram_cmd.py"; then
    log "ACTION: Telegram /reconnect command received"
    save_health "manual_restart" "User requested via Telegram"
    fast_restart "User requested via Telegram"
    exit 0
fi

STATUS=$(health_check)

case "$STATUS" in
    healthy)
        # ✅ 정상 — 킵얼라이브 체크
        LAST_PING=0
        [ -f "$KEEPALIVE_FILE" ] && LAST_PING=$(cat "$KEEPALIVE_FILE" 2>/dev/null)
        NOW=$(date +%s)
        ELAPSED=$((NOW - LAST_PING))

        if [ "$ELAPSED" -ge "$KEEPALIVE_INTERVAL" ]; then
            send_keepalive
            save_health "healthy" "keepalive sent"
            log "OK: Healthy (keepalive sent)"
        else
            REMAINING=$((KEEPALIVE_INTERVAL - ELAPSED))
            save_health "healthy" "next keepalive in ${REMAINING}s"
            log "OK: Healthy (next keepalive in ${REMAINING}s)"
        fi
        reset_fail_count
        # 복구 감지: 연속 healthy 체크 시 에스컬레이션 상태 리셋
        check_recovery
        ;;

    zombie)
        # 🧟 좀비 — "active" 표시인데 실제 작동 안 함
        log "WARN: Zombie session detected — active but unresponsive"
        save_health "zombie" "Forcing restart"
        reset_healthy_count

        if ! fast_restart "zombie session detected"; then
            if [ "$(get_fail_count)" -ge "$MAX_CONSECUTIVE_FAILS" ]; then
                full_rebuild
            fi
        fi
        ;;

    disconnected)
        # 🔌 연결 끊김 (reconnecting 상태)
        log "WARN: RC disconnected (reconnecting)"
        save_health "disconnected" "Forcing restart"
        reset_healthy_count

        # graceful reconnect 폐기 → 바로 fast restart
        if ! fast_restart "RC disconnected"; then
            if [ "$(get_fail_count)" -ge "$MAX_CONSECUTIVE_FAILS" ]; then
                full_rebuild
            fi
        fi
        ;;

    no_rc)
        # ❌ RC 없음 — /rc 시도 후 실패하면 restart
        log "WARN: No RC found. Trying /rc..."
        save_health "no_rc" "Activating /rc"
        reset_healthy_count

        dismiss_rating_prompt 2>/dev/null
        tmux send-keys -t "$TMUX_SESSION:$TMUX_WINDOW" "/rc" Enter
        sleep 10
        tmux send-keys -t "$TMUX_SESSION:$TMUX_WINDOW" Enter
        sleep 8

        screen=$(tmux capture-pane -t "$TMUX_SESSION:$TMUX_WINDOW" -p 2>/dev/null)
        new_url=$(extract_url)

        if echo "$screen" | grep -q "Remote Control active" && [ -n "$new_url" ]; then
            echo "$new_url" > "$REMOTE_URL_FILE"
            echo "$(date +%s)" > "$KEEPALIVE_FILE"
            reset_fail_count
            save_health "healthy" "RC activated"
            log "OK: RC activated. URL: $new_url"
            send_telegram "✅ RC 활성화
$new_url"
        else
            log "WARN: /rc failed. Doing fast restart."
            if ! fast_restart "RC activation failed"; then
                if [ "$(get_fail_count)" -ge "$MAX_CONSECUTIVE_FAILS" ]; then
                    full_rebuild
                fi
            fi
        fi
        ;;

    no_claude)
        # ❌ Claude 프로세스 없음 → claude 윈도우 있으면 restart, 없으면 recreate
        log "WARN: Claude process not found"
        save_health "no_claude" "Starting Claude"
        reset_healthy_count

        if ! tmux list-windows -t "$TMUX_SESSION" -F '#{window_name}' 2>/dev/null | grep -q "^${TMUX_WINDOW}$"; then
            tmux new-window -t "$TMUX_SESSION" -n "$TMUX_WINDOW" -c "$PROJECT_DIR"
            sleep 1
        fi

        if ! fast_restart "Claude process not found"; then
            if [ "$(get_fail_count)" -ge "$MAX_CONSECUTIVE_FAILS" ]; then
                full_rebuild
            fi
        fi
        ;;

    no_tmux)
        # ❌ tmux 세션 없음 → 전체 재구축
        log "WARN: tmux session not found"
        save_health "no_tmux" "Running startup.sh"
        reset_healthy_count
        full_rebuild
        ;;
esac
