#!/bin/bash
# =============================================================================
# Remote Control Watchdog v5
#
# 4분마다 실행 (LaunchAgent: com.claude.watchdog-remote)
#
# 스킬 참조: .claude/skills/rc-troubleshoot/skill.md
#
# v5 변경 (2026-03-19):
#   - rc-troubleshoot 스킬 기반 자동 진단 (run_rc_diagnostics)
#   - OAuth 토큰 검증 (Layer 5) — Transport 미연결 감지
#   - 버전 검증 — v2.1.78 미만 시 자동 심볼릭 링크 수정
#   - /rc → /remote-control 변경 (자동완성 메뉴 충돌 방지)
#   - 문제 발생 시 스킬 체크리스트 순서대로 자동 복구 시도
#
# v4 핵심 (유지):
#   - 3단계 건강 검진: 프로세스 → 화면 텍스트 → 실제 응답성 검증
#   - 좀비 세션 감지: "active" 표시인데 실제 작동 안 하는 상태 탐지
#   - graceful reconnect 폐기 (성공률 0%) → 즉시 full restart
#   - 연속 실패 카운터 → 3회 연속 실패 시 startup.sh 전체 재구축
#   - 텔레그램으로 상태 변화만 알림 (스팸 방지)
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
TMUX_WINDOW=""  # 동적으로 결정 (find_rc_window)
KEEPALIVE_INTERVAL=120   # 2분 간격 킵얼라이브
MAX_CONSECUTIVE_FAILS=3  # 3회 연속 실패 → startup.sh로 전체 재구축
TARGET_RC_COUNT=1        # RC 세션 1개 안정 유지
ESCALATION_PAUSE_SEC=1800  # 30분 (수동 개입 대기)
REVIVE_INTERVAL=3600       # 1시간마다 강제 RC 부활
REVIVE_TS_FILE="$PROJECT_DIR/data/.rc_revive_ts"

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

# =============================================================================
# rc-troubleshoot 스킬 기반 자동 진단
# 문제 발생 시 이 함수가 스킬 체크리스트를 순서대로 실행
# =============================================================================

# ─── 스킬: 버전 검증 + 자동 수정 ───
check_claude_version() {
    local current_version
    current_version=$(claude --version 2>/dev/null | grep -o '[0-9]*\.[0-9]*\.[0-9]*')

    if [ -z "$current_version" ]; then
        log "DIAG: Cannot determine Claude Code version"
        return 1
    fi

    # 버전 비교: 2.1.78 이상 필요
    local major minor patch
    IFS='.' read -r major minor patch <<< "$current_version"

    if [ "$major" -lt 2 ] || ([ "$major" -eq 2 ] && [ "$minor" -lt 1 ]) || \
       ([ "$major" -eq 2 ] && [ "$minor" -eq 1 ] && [ "$patch" -lt 78 ]); then
        log "DIAG: Claude Code v${current_version} < v2.1.78 — RC 세션 ID 불일치 위험"

        # 자동 수정: ~/.local/bin/claude 심볼릭 링크 업데이트
        local homebrew_version
        homebrew_version=$(/opt/homebrew/bin/claude --version 2>/dev/null | grep -o '[0-9]*\.[0-9]*\.[0-9]*')

        if [ -n "$homebrew_version" ]; then
            ln -sf /opt/homebrew/bin/claude "$HOME/.local/bin/claude" 2>/dev/null
            log "DIAG: Symlink updated: ~/.local/bin/claude → /opt/homebrew/bin/claude (v${homebrew_version})"
            send_telegram "🔧 RC 자동 수정: Claude Code v${current_version} → v${homebrew_version}
심볼릭 링크 업데이트 완료"
            return 0
        else
            send_telegram "⚠️ RC 버전 문제: v${current_version} < v2.1.78
homebrew 버전 없음 — 수동 업데이트 필요:
npm install -g @anthropic-ai/claude-code@latest"
            return 1
        fi
    fi

    log "DIAG: Claude Code v${current_version} — OK"
    return 0
}

# ─── 스킬: 전체 진단 (문제 발생 시 호출) ───
# rc-troubleshoot 스킬의 체크리스트를 순서대로 실행
run_rc_diagnostics() {
    local reason="$1"
    local issues_found=0
    local diagnosis=""

    log "DIAG: === rc-troubleshoot 스킬 진단 시작 (사유: $reason) ==="

    # 체크 1: Claude Code 버전
    if ! check_claude_version; then
        diagnosis+="❌ 버전: v2.1.78 미만\n"
        issues_found=$((issues_found + 1))
    else
        diagnosis+="✅ 버전: OK\n"
    fi

    # 체크 2: OAuth 토큰 (Transport 연결)
    if ! check_oauth; then
        diagnosis+="❌ OAuth: Transport not configured\n"
        issues_found=$((issues_found + 1))
    else
        diagnosis+="✅ OAuth: Transport 연결됨\n"
    fi

    # 체크 3: 디버그 로그에서 Rejecting foreign session 확인
    local latest_debug reject_count
    latest_debug=$(ls -t ~/.claude/debug/*.txt 2>/dev/null | head -1)
    if [ -n "$latest_debug" ]; then
        reject_count=$(tail -100 "$latest_debug" 2>/dev/null | grep -c "Rejecting foreign session")
        if [ "$reject_count" -gt 0 ]; then
            diagnosis+="❌ 세션 ID 불일치: ${reject_count}회 거부\n"
            issues_found=$((issues_found + 1))
        else
            diagnosis+="✅ 세션 ID: OK\n"
        fi
    fi

    # 체크 4: RC URL 유효성
    local current_url
    current_url=$(cat "$REMOTE_URL_FILE" 2>/dev/null)
    if [ -z "$current_url" ] || echo "$current_url" | grep -q "pending"; then
        diagnosis+="❌ URL: pending 또는 없음\n"
        issues_found=$((issues_found + 1))
    else
        diagnosis+="✅ URL: $current_url\n"
    fi

    log "DIAG: === 진단 완료: ${issues_found}건 문제 발견 ==="

    # 문제가 있으면 텔레그램으로 진단 결과 전송
    if [ "$issues_found" -gt 0 ]; then
        send_telegram "🔍 RC 진단 결과 (${reason})

$(echo -e "$diagnosis")
문제 ${issues_found}건 발견"
        save_health "diagnosing" "rc-troubleshoot: ${issues_found} issues found"
    fi

    return "$issues_found"
}

# ─── OAuth 토큰 확인 ───
# RC에 OAuth 필수. 없으면 Transport 미연결 → iPhone 앱에 세션 안 뜸
check_oauth() {
    # 1차: 키체인에 Claude Code-credentials 존재 확인
    if ! security find-generic-password -s "Claude Code-credentials" >/dev/null 2>&1; then
        log "DIAG: OAuth credentials not found in keychain"
        return 1
    fi

    # 2차: 감시 대상 세션의 디버그 로그에서 Transport 상태 확인
    # 감시 윈도우의 Claude PID 기반으로 해당 세션의 디버그 로그 찾기
    local PANE_PID CLAUDE_PID session_id latest_debug
    PANE_PID=$(tmux list-panes -t "$TMUX_SESSION:$TMUX_WINDOW" -F '#{pane_pid}' 2>/dev/null)
    [ -z "$PANE_PID" ] && return 1

    # 해당 세션의 디버그 로그에서 Transport 확인
    # 최신 로그 파일 2개를 확인 (세션 로그 매핑이 어려우므로)
    local transport_errors=0
    for f in $(ls -t ~/.claude/debug/*.txt 2>/dev/null | head -3); do
        local count
        count=$(tail -30 "$f" 2>/dev/null | grep -c "Transport not configured")
        transport_errors=$((transport_errors + count))
    done

    if [ "$transport_errors" -gt 5 ]; then
        log "DIAG: Transport not configured detected ($transport_errors recent errors)"
        return 1  # OAuth/Transport 문제
    fi
    return 0  # OK
}

# ─── OAuth 재로그인 시도 ───
attempt_oauth_login() {
    log "ACTION: OAuth token missing/expired — attempting re-login"
    # 현재 실행 중인 claude 세션 종료 후 재로그인
    # 주의: 자동 로그인은 브라우저 없이는 불가 → 알림만 전송
    send_telegram "⚠️ RC Transport 미연결
OAuth 토큰이 없거나 만료됨
Mac에서 수동 실행 필요:
unset CLAUDECODE && claude auth login"
    save_health "oauth_required" "OAuth login required — Transport not configured"
    log "WARN: OAuth login required — sent Telegram notification"
}

# ─── 3단계 건강 검진 ───
# 반환값: healthy / zombie / disconnected / no_rc / no_claude / no_tmux / no_oauth
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

    # "Remote Control active" 또는 "Remote Control reconnecting" 확인
    if echo "$screen" | grep -q "Remote Control reconnecting"; then
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

    # Layer 5: Transport 연결 확인 (OAuth 없으면 RC active여도 iPhone에서 안 보임)
    if ! check_oauth; then
        echo "no_oauth"
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

    # 문자 입력 → 1초 대기 → 삭제: WebSocket input change 이벤트 확실히 발생
    # Space+BSpace는 너무 빨라서 coalesce될 수 있음 → 실제 문자+딜레이로 2개 프레임 보장
    tmux send-keys -t "$TMUX_SESSION:$TMUX_WINDOW" "x"
    sleep 1
    tmux send-keys -t "$TMUX_SESSION:$TMUX_WINDOW" BSpace
    sleep 1

    echo "$(date +%s)" > "$KEEPALIVE_FILE"
}

# ─── Claude + RC 빠른 재시작 ───
# 핵심 패턴: 기존 윈도우 정리 → 새 tmux 윈도우 → Claude --continue → /remote-control → URL 텔레그램 전송
fast_restart() {
    local reason="$1"
    log "ACTION: Fast restart ($reason)"

    # 1) 기존 rc 윈도우 정리 — Claude 프로세스 kill + 윈도우 삭제
    if [ -n "$TMUX_WINDOW" ] && tmux list-windows -t "$TMUX_SESSION" -F '#{window_index}' 2>/dev/null | grep -q "^${TMUX_WINDOW}$"; then
        local PANE_PID CLAUDE_PIDS
        PANE_PID=$(tmux list-panes -t "$TMUX_SESSION:$TMUX_WINDOW" -F '#{pane_pid}' 2>/dev/null)
        if [ -n "$PANE_PID" ]; then
            CLAUDE_PIDS=$(pgrep -P "$PANE_PID" 2>/dev/null)
            if [ -n "$CLAUDE_PIDS" ]; then
                echo "$CLAUDE_PIDS" | xargs kill -9 2>/dev/null
                log "OK: Killed processes: $CLAUDE_PIDS"
            fi
        fi
        tmux kill-window -t "$TMUX_SESSION:$TMUX_WINDOW" 2>/dev/null
        log "OK: Old RC window $TMUX_WINDOW killed"
        sleep 2
    fi

    # 2) 새 tmux 윈도우 생성
    local rc_time_label="rc@$(date '+%H%M')"
    tmux new-window -t "$TMUX_SESSION" -n "$rc_time_label" -c "$PROJECT_DIR"
    TMUX_WINDOW=$(tmux list-windows -t "$TMUX_SESSION" -F '#{window_index}:#{window_name}' 2>/dev/null | grep ":${rc_time_label}$" | cut -d: -f1)
    log "OK: New RC window created: $rc_time_label (idx=$TMUX_WINDOW)"
    sleep 1

    # 3) Claude --continue 실행
    tmux send-keys -t "$TMUX_SESSION:$rc_time_label" "unset CLAUDECODE && claude --continue --dangerously-skip-permissions" Enter
    log "OK: Claude starting (--continue, reuse session)..."

    local claude_ready=false
    local wait_count=0
    local max_wait=18  # 18 × 5초 = 90초
    while [ $wait_count -lt $max_wait ]; do
        sleep 5
        wait_count=$((wait_count + 1))
        local boot_screen
        boot_screen=$(tmux capture-pane -t "$TMUX_SESSION:$rc_time_label" -p -S -5 2>/dev/null)
        if echo "$boot_screen" | grep -qE '❯\s*$|>\s*$|tips|Claude Code'; then
            claude_ready=true
            log "OK: Claude ready after $((wait_count * 5))s"
            break
        fi
    done

    if [ "$claude_ready" = false ]; then
        log "WARN: Claude not ready after 90s, attempting /remote-control anyway"
    fi

    # 4) /remote-control 전송 — 최대 3회 재시도
    local rc_attempt=0
    local max_rc_attempts=3
    while [ $rc_attempt -lt $max_rc_attempts ]; do
        rc_attempt=$((rc_attempt + 1))
        log "OK: Sending /remote-control (attempt $rc_attempt/$max_rc_attempts)"

        tmux send-keys -t "$TMUX_SESSION:$rc_time_label" "/remote-control" Enter
        sleep 5
        tmux send-keys -t "$TMUX_SESSION:$rc_time_label" Enter
        sleep 20

        # 결과 확인
        local screen new_url
        screen=$(tmux capture-pane -t "$TMUX_SESSION:$rc_time_label" -p 2>/dev/null)
        new_url=$(echo "$screen" | grep -o 'https://claude\.ai/code/session_[A-Za-z0-9]*' | tail -1)

        if echo "$screen" | grep -q "Remote Control active" && [ -n "$new_url" ]; then
            # 5) URL 추출 → 텔레그램으로 전송
            echo "$new_url" > "$REMOTE_URL_FILE"
            echo "$(date +%s)" > "$KEEPALIVE_FILE"
            reset_fail_count
            reset_rebuild_count
            save_health "healthy" "Fast restart succeeded (RC attempt $rc_attempt)"
            log "OK: Fast restart succeeded (RC attempt $rc_attempt). Window: $rc_time_label URL: $new_url"
            send_telegram "🔄 RC 재시작 성공 ($reason)

🔗 링크: $new_url"
            return 0
        fi

        # Claude가 살아있으면 RC만 재시도
        local pane_pid has_claude=false
        pane_pid=$(tmux list-panes -t "$TMUX_SESSION:$rc_time_label" -F '#{pane_pid}' 2>/dev/null)
        if [ -n "$pane_pid" ] && pgrep -P "$pane_pid" > /dev/null 2>&1; then
            has_claude=true
        fi

        if [ "$has_claude" = true ] && [ $rc_attempt -lt $max_rc_attempts ]; then
            log "WARN: RC attempt $rc_attempt failed, but Claude is alive. Retrying RC only..."
            tmux send-keys -t "$TMUX_SESSION:$rc_time_label" Escape
            sleep 2
        elif [ "$has_claude" = false ]; then
            log "ERROR: Claude process died during RC activation"
            break
        fi
    done

    # 전체 실패 — 새 윈도우 정리
    local fails
    fails=$(get_fail_count)
    fails=$((fails + 1))
    set_fail_count "$fails"
    save_health "failed" "Fast restart failed ($fails/$MAX_CONSECUTIVE_FAILS)"
    log "ERROR: Fast restart failed ($fails consecutive)"

    # 실패한 윈도우 정리
    local pane_pid
    pane_pid=$(tmux list-panes -t "$TMUX_SESSION:$rc_time_label" -F '#{pane_pid}' 2>/dev/null)
    if [ -n "$pane_pid" ]; then
        pgrep -P "$pane_pid" 2>/dev/null | xargs kill -9 2>/dev/null
    fi
    tmux kill-window -t "$TMUX_SESSION:$rc_time_label" 2>/dev/null

    # 스킬 기반 진단
    run_rc_diagnostics "fast_restart failed ($fails/$MAX_CONSECUTIVE_FAILS)"
    return 1
}

# ─── 전체 재구축 (startup.sh) ───
full_rebuild() {
    log "ACTION: Full rebuild via startup.sh ($(get_fail_count) consecutive failures)"

    # ★ 살아있는 RC 세션이 있으면 재구축 하지 않음
    if has_live_rc_session; then
        log "SKIP: Live RC session exists — skipping full rebuild"
        reset_fail_count
        save_health "healthy" "Live RC session found, rebuild skipped"
        send_telegram "✅ 살아있는 RC 세션 발견 — 재구축 건너뜀"
        return 0
    fi

    # 재구축 전 죽은 세션부터 정리
    cleanup_dead_sessions

    # 재구축 전 스킬 기반 진단 — 버전/OAuth 문제면 재구축 전에 먼저 수정
    run_rc_diagnostics "before full_rebuild"
    check_claude_version  # 버전 자동 수정 시도

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
# 죽은 세션 정리 (살아있는 세션은 절대 건드리지 않음)
# =============================================================================

# Claude CLI 프로세스가 살아있는지 판별
# 기준: 프로세스 존재 + tty 연결 + 쉘 자식 프로세스
is_claude_alive() {
    local pid="$1"
    # 프로세스 존재?
    if ! ps -p "$pid" >/dev/null 2>&1; then
        return 1  # 죽음
    fi
    # zombie 상태?
    local state
    state=$(ps -p "$pid" -o state= 2>/dev/null | tr -d ' ')
    if [ "$state" = "Z" ]; then
        return 1  # 좀비
    fi
    return 0  # 살아있음
}

# 죽은 Claude CLI 세션(터미널/tmux) 정리
# 원칙: 살아있는 세션은 절대 건드리지 않음
cleanup_dead_sessions() {
    local cleaned=0

    # 1) 터미널 기반 claude 프로세스 (tmux 밖, MCP/Desktop 제외)
    local pids
    pids=$(ps -eo pid,tty,comm,args 2>/dev/null | \
        grep -E "claude\s*$|claude --" | \
        grep -v "grep\|Claude 3.app\|claude-code-mcp\|npm exec" | \
        awk '{print $1}')

    for pid in $pids; do
        # 현재 세션(이 워치독을 실행하는 세션)의 claude는 건너뜀
        # RC tmux 세션의 claude도 건너뜀 (별도 관리)
        local tty_name
        tty_name=$(ps -p "$pid" -o tty= 2>/dev/null | tr -d ' ')

        # tmux 내 프로세스는 이 함수에서 처리하지 않음 (워치독 메인 로직이 담당)
        if echo "$tty_name" | grep -q "^s0"; then
            # 터미널 세션의 claude
            if ! is_claude_alive "$pid"; then
                log "CLEANUP: Dead terminal claude PID=$pid (tty=$tty_name) — killing"
                kill "$pid" 2>/dev/null
                cleaned=$((cleaned + 1))
            fi
        fi
    done

    # 2) tmux 내 죽은 claude 윈도우 정리
    # ⚠️ 사용자 윈도우 보호: 워치독이 자동 생성한 "claude" 이름 윈도우만 정리 대상
    # 그 외 윈도우(dashboard, work, 사용자 세션 등)는 절대 건드리지 않음
    if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
        local windows
        windows=$(tmux list-windows -t "$TMUX_SESSION" -F '#{window_index}:#{window_name}' 2>/dev/null)

        while IFS=: read -r idx name; do
            # "claude" 또는 "rc@*" 이름 윈도우만 정리 대상 (워치독이 생성한 RC용 윈도우)
            # 그 외 모든 윈도우는 사용자 소유로 간주하고 건드리지 않음
            if [ "$name" != "claude" ] && ! echo "$name" | grep -q "^rc@"; then
                continue
            fi

            local pane_pid child_claude
            pane_pid=$(tmux list-panes -t "${TMUX_SESSION}:${idx}" -F '#{pane_pid}' 2>/dev/null | head -1)
            [ -z "$pane_pid" ] && continue

            # 쉘 자체가 죽었으면 윈도우 제거
            if ! ps -p "$pane_pid" >/dev/null 2>&1; then
                log "CLEANUP: Dead tmux window ${idx}:${name} (shell PID=$pane_pid gone)"
                tmux kill-window -t "${TMUX_SESSION}:${idx}" 2>/dev/null
                cleaned=$((cleaned + 1))
                continue
            fi

            # 쉘은 살아있는데 claude 자식 프로세스가 없으면 = 빈 윈도우
            child_claude=$(pgrep -P "$pane_pid" -f "claude" 2>/dev/null | head -1)
            if [ -z "$child_claude" ]; then
                # RC 윈도우(현재 감시 대상)가 아닌 빈 claude 윈도우만 정리
                if [ "$idx" != "$TMUX_WINDOW" ]; then
                    log "CLEANUP: Empty tmux window ${idx}:${name} (shell alive, no claude child)"
                    tmux kill-window -t "${TMUX_SESSION}:${idx}" 2>/dev/null
                    cleaned=$((cleaned + 1))
                fi
            fi
        done <<< "$windows"
    fi

    if [ "$cleaned" -gt 0 ]; then
        log "CLEANUP: Removed $cleaned dead session(s)"
        send_telegram "🧹 죽은 세션 ${cleaned}개 정리 완료"
    fi

    return "$cleaned"
}

# 살아있는 RC 세션이 있는지 확인 (startup/rebuild 전 호출)
# 있으면 0 (true), 없으면 1 (false)
has_live_rc_session() {
    if ! tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
        return 1
    fi

    local windows
    windows=$(tmux list-windows -t "$TMUX_SESSION" -F '#{window_index}:#{window_name}' 2>/dev/null)

    while IFS=: read -r idx name; do
        local screen
        screen=$(tmux capture-pane -t "${TMUX_SESSION}:${idx}" -p 2>/dev/null)

        if echo "$screen" | grep -q "Remote Control active"; then
            # RC active 텍스트가 있고, claude 프로세스도 살아있는지 확인
            local pane_pid child_claude
            pane_pid=$(tmux list-panes -t "${TMUX_SESSION}:${idx}" -F '#{pane_pid}' 2>/dev/null | head -1)
            child_claude=$(pgrep -P "$pane_pid" -f "claude" 2>/dev/null | head -1)

            if [ -n "$child_claude" ] && is_claude_alive "$child_claude"; then
                log "CHECK: Live RC session found at window ${idx}:${name} (PID=$child_claude)"
                return 0  # 살아있는 RC 세션 있음
            fi
        fi
    done <<< "$windows"

    return 1  # 없음
}

# =============================================================================
# RC 윈도우 자동 감지
# =============================================================================

# 모든 tmux 윈도우를 순회하여 RC가 있는 윈도우를 찾음
# "Remote Control active" 또는 "Remote Control reconnecting"이 있는 윈도우 우선
# 여러 개면 "active" 우선, 그 다음 "reconnecting"
find_rc_window() {
    local session="$1"
    local active_window="" reconnecting_window="" claude_window=""

    if ! tmux has-session -t "$session" 2>/dev/null; then
        echo ""
        return
    fi

    local windows
    windows=$(tmux list-windows -t "$session" -F '#{window_index}:#{window_name}' 2>/dev/null)

    while IFS=: read -r idx name; do
        local screen
        screen=$(tmux capture-pane -t "${session}:${idx}" -p 2>/dev/null)

        if echo "$screen" | grep -q "Remote Control active"; then
            active_window="$idx"
        elif echo "$screen" | grep -q "Remote Control reconnecting"; then
            reconnecting_window="$idx"
        fi

        # 이름이 "claude" 또는 "rc@*"인 윈도우도 기록 (fallback)
        if [ "$name" = "claude" ] || echo "$name" | grep -q "^rc@"; then
            claude_window="$idx"
        fi
    done <<< "$windows"

    # 우선순위: active > reconnecting > "claude" 이름
    if [ -n "$active_window" ]; then
        echo "$active_window"
    elif [ -n "$reconnecting_window" ]; then
        echo "$reconnecting_window"
    elif [ -n "$claude_window" ]; then
        echo "$claude_window"
    else
        echo ""
    fi
}

# =============================================================================
# 개별 RC 윈도우 건강검진 (윈도우 인덱스를 인자로 받음)
# 반환값: healthy / zombie / disconnected / no_rc / no_claude / no_oauth
# =============================================================================
check_rc_window_health() {
    local win_idx="$1"

    # Claude 프로세스 살아있나?
    local pane_pid claude_pid
    pane_pid=$(tmux list-panes -t "$TMUX_SESSION:$win_idx" -F '#{pane_pid}' 2>/dev/null)
    if [ -n "$pane_pid" ]; then
        claude_pid=$(pgrep -P "$pane_pid" -f "claude" 2>/dev/null | head -1)
        if [ -z "$claude_pid" ]; then
            echo "no_claude"
            return
        fi
    else
        echo "no_claude"
        return
    fi

    # 화면 텍스트 확인
    local screen
    screen=$(tmux capture-pane -t "$TMUX_SESSION:$win_idx" -p 2>/dev/null)

    # rating 프롬프트 해소
    if echo "$screen" | grep -q "1: Bad.*2: Fine.*3: Good.*0: Dismiss"; then
        tmux send-keys -t "$TMUX_SESSION:$win_idx" "0" Enter 2>/dev/null
        sleep 2
        screen=$(tmux capture-pane -t "$TMUX_SESSION:$win_idx" -p 2>/dev/null)
    fi

    if echo "$screen" | grep -q "Remote Control reconnecting\|reconnecting"; then
        echo "disconnected"
        return
    fi

    if ! echo "$screen" | grep -q "Remote Control active"; then
        echo "no_rc"
        return
    fi

    # 좀비 감지
    local cpu_usage
    cpu_usage=$(ps -p "$claude_pid" -o %cpu= 2>/dev/null | tr -d ' ')
    if [ -z "$cpu_usage" ]; then
        echo "zombie"
        return
    fi

    echo "healthy"
}

# =============================================================================
# 개별 RC 윈도우에 킵얼라이브 전송
# =============================================================================
send_keepalive_to() {
    local win_idx="$1"
    # 메뉴 열려있으면 닫기
    local pane_check
    pane_check=$(tmux capture-pane -t "$TMUX_SESSION:$win_idx" -p -S -5 2>/dev/null)
    if echo "$pane_check" | grep -q "Disconnect\|Show QR\|Enter to select"; then
        tmux send-keys -t "$TMUX_SESSION:$win_idx" Escape
        sleep 1
    fi
    # 문자 입력 → 1초 대기 → 삭제: WebSocket input change 이벤트 확실히 발생
    tmux send-keys -t "$TMUX_SESSION:$win_idx" "x"
    sleep 1
    tmux send-keys -t "$TMUX_SESSION:$win_idx" BSpace
}

# =============================================================================
# 새 RC 세션 생성 (부족분 보충용)
# 핵심 패턴: 새 tmux 윈도우 → Claude --continue → /remote-control → URL 텔레그램 전송
# =============================================================================
create_new_rc_session() {
    local win_name="rc@$(date '+%H%M')"
    log "ACTION: Creating new RC session ($win_name) to maintain ${TARGET_RC_COUNT} sessions"

    # 1) 새 tmux 윈도우 생성
    tmux new-window -t "$TMUX_SESSION" -n "$win_name" -c "$PROJECT_DIR"
    sleep 1

    # 2) Claude --continue 실행
    tmux send-keys -t "$TMUX_SESSION:$win_name" "unset CLAUDECODE && claude --continue --dangerously-skip-permissions" Enter
    log "OK: Claude starting in $win_name (--continue, reuse session)..."

    local ready=false wait_count=0
    while [ $wait_count -lt 18 ]; do
        sleep 5
        wait_count=$((wait_count + 1))
        local boot_screen
        boot_screen=$(tmux capture-pane -t "$TMUX_SESSION:$win_name" -p -S -5 2>/dev/null)
        if echo "$boot_screen" | grep -qE '❯\s*$|>\s*$|tips|Claude Code'; then
            ready=true
            log "OK: Claude ready in $win_name after $((wait_count * 5))s"
            break
        fi
    done

    if [ "$ready" = false ]; then
        log "WARN: Claude not ready in $win_name after 90s"
        # 실패한 윈도우 정리
        local pane_pid
        pane_pid=$(tmux list-panes -t "$TMUX_SESSION:$win_name" -F '#{pane_pid}' 2>/dev/null)
        if [ -n "$pane_pid" ]; then
            pgrep -P "$pane_pid" 2>/dev/null | xargs kill -9 2>/dev/null
        fi
        tmux kill-window -t "$TMUX_SESSION:$win_name" 2>/dev/null
        return 1
    fi

    # 3) /remote-control 전송
    tmux send-keys -t "$TMUX_SESSION:$win_name" "/remote-control" Enter
    sleep 5
    tmux send-keys -t "$TMUX_SESSION:$win_name" Enter
    sleep 20

    # 4) URL 추출 → 텔레그램 전송
    local screen new_url
    screen=$(tmux capture-pane -t "$TMUX_SESSION:$win_name" -p 2>/dev/null)
    new_url=$(echo "$screen" | grep -o 'https://claude\.ai/code/session_[A-Za-z0-9]*' | tail -1)

    if echo "$screen" | grep -q "Remote Control active" && [ -n "$new_url" ]; then
        echo "$new_url" > "$REMOTE_URL_FILE"
        echo "$(date +%s)" > "$KEEPALIVE_FILE"
        log "OK: New RC session $win_name active. URL: $new_url"
        send_telegram "✅ RC 세션 생성 완료: $win_name

🔗 링크: $new_url"
        return 0
    else
        log "ERROR: New RC session $win_name failed to activate"
        # 실패한 윈도우 정리
        local pane_pid
        pane_pid=$(tmux list-panes -t "$TMUX_SESSION:$win_name" -F '#{pane_pid}' 2>/dev/null)
        if [ -n "$pane_pid" ]; then
            pgrep -P "$pane_pid" 2>/dev/null | xargs kill -9 2>/dev/null
        fi
        tmux kill-window -t "$TMUX_SESSION:$win_name" 2>/dev/null
        return 1
    fi
}

# =============================================================================
# 메인 로직 — 다중 RC 세션 감시 (TARGET_RC_COUNT개 유지)
# =============================================================================

# 0. 에스컬레이션 대기 모드 확인 (무한 루프 방지)
if ! check_escalation; then
    exit 0
fi

# 0.1. 1시간마다 강제 RC 부활 (핵심 패턴: 윈도우 정리→새 윈도우→Claude→RC→텔레그램)
LAST_REVIVE=0
[ -f "$REVIVE_TS_FILE" ] && LAST_REVIVE=$(cat "$REVIVE_TS_FILE" 2>/dev/null)
NOW_REVIVE=$(date +%s)
REVIVE_ELAPSED=$((NOW_REVIVE - LAST_REVIVE))

if [ "$REVIVE_ELAPSED" -ge "$REVIVE_INTERVAL" ]; then
    log "REVIVE: 1시간 경과 (${REVIVE_ELAPSED}s) — 강제 RC 부활 시작"
    echo "$NOW_REVIVE" > "$REVIVE_TS_FILE"

    # 기존 RC 윈도우 찾기
    TMUX_WINDOW=$(find_rc_window "$TMUX_SESSION")
    fast_restart "hourly forced revive"

    # 부활 완료 → 나머지 체크 건너뜀
    exit 0
fi

# 0.3. 죽은 세션 정리 (살아있는 세션은 절대 건드리지 않음)
cleanup_dead_sessions

# 0.5. tmux 세션 존재 확인
if ! tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    log "WARN: tmux session not found"
    save_health "no_tmux" "Running startup.sh"
    full_rebuild
    exit 0
fi

# 1. 텔레그램 수동 재연결(/rc, /reconnect) 명령 확인
TMUX_WINDOW=$(find_rc_window "$TMUX_SESSION")
[ -z "$TMUX_WINDOW" ] && TMUX_WINDOW="rc@$(date '+%H%M')"
if "$PYTHON" "$PROJECT_DIR/scripts/check_telegram_cmd.py"; then
    log "ACTION: Telegram /reconnect command received"
    save_health "manual_restart" "User requested via Telegram"
    fast_restart "User requested via Telegram"
    exit 0
fi

# 2. 모든 RC 윈도우 수집 (rc@ 또는 claude 이름 + RC active 화면 보유)
LIVE_RC_WINDOWS=()
SICK_RC_WINDOWS=()

while IFS=: read -r idx name; do
    # RC 관련 윈도우만 대상 (rc@* 또는 claude)
    is_rc_win=false
    if [ "$name" = "claude" ] || echo "$name" | grep -q "^rc@"; then
        is_rc_win=true
    fi

    # 화면에 RC 텍스트가 있는 윈도우도 포함
    local screen
    screen=$(tmux capture-pane -t "$TMUX_SESSION:$idx" -p 2>/dev/null)
    if echo "$screen" | grep -q "Remote Control"; then
        is_rc_win=true
    fi

    [ "$is_rc_win" = false ] && continue

    # 개별 건강검진
    local status
    status=$(check_rc_window_health "$idx")

    case "$status" in
        healthy)
            LIVE_RC_WINDOWS+=("$idx")
            ;;
        *)
            SICK_RC_WINDOWS+=("$idx:$status")
            ;;
    esac
done <<< "$(tmux list-windows -t "$TMUX_SESSION" -F '#{window_index}:#{window_name}' 2>/dev/null)"

live_count=${#LIVE_RC_WINDOWS[@]}
sick_count=${#SICK_RC_WINDOWS[@]}

log "RC STATUS: live=$live_count sick=$sick_count target=$TARGET_RC_COUNT"

# 3. 살아있는 RC에 킵얼라이브 전송
LAST_PING=0
[ -f "$KEEPALIVE_FILE" ] && LAST_PING=$(cat "$KEEPALIVE_FILE" 2>/dev/null)
NOW=$(date +%s)
ELAPSED=$((NOW - LAST_PING))

if [ "$ELAPSED" -ge "$KEEPALIVE_INTERVAL" ] && [ "$live_count" -gt 0 ]; then
    for win_idx in "${LIVE_RC_WINDOWS[@]}"; do
        send_keepalive_to "$win_idx"
    done
    echo "$NOW" > "$KEEPALIVE_FILE"
    log "OK: Keepalive sent to $live_count RC session(s)"
fi

# 4. 병든 RC 윈도우 복구 시도
for sick_entry in "${SICK_RC_WINDOWS[@]}"; do
    local sick_idx="${sick_entry%%:*}"
    local sick_status="${sick_entry#*:}"
    local sick_name
    sick_name=$(tmux list-windows -t "$TMUX_SESSION" -F '#{window_index}:#{window_name}' 2>/dev/null | grep "^${sick_idx}:" | cut -d: -f2)

    case "$sick_status" in
        no_rc)
            # Claude는 살아있는데 RC가 없음 → /remote-control 시도 (윈도우 재사용)
            log "WARN: Window $sick_idx ($sick_name): no RC — trying /remote-control"
            dismiss_rating_prompt 2>/dev/null
            tmux send-keys -t "$TMUX_SESSION:$sick_idx" "/remote-control" Enter
            sleep 5
            tmux send-keys -t "$TMUX_SESSION:$sick_idx" Enter
            sleep 15
            local screen new_url
            screen=$(tmux capture-pane -t "$TMUX_SESSION:$sick_idx" -p 2>/dev/null)
            if echo "$screen" | grep -q "Remote Control active"; then
                new_url=$(echo "$screen" | grep -o 'https://claude\.ai/code/session_[A-Za-z0-9]*' | tail -1)
                tmux rename-window -t "$TMUX_SESSION:$sick_idx" "rc@$(date '+%H%M')" 2>/dev/null
                [ -n "$new_url" ] && echo "$new_url" > "$REMOTE_URL_FILE"
                echo "$(date +%s)" > "$KEEPALIVE_FILE"
                log "OK: Window $sick_idx RC restored"
                [ -n "$new_url" ] && send_telegram "✅ RC 복구 완료

🔗 링크: $new_url"
                live_count=$((live_count + 1))
            else
                # /remote-control 실패 → 핵심 패턴: 윈도우 정리 → 새 윈도우 → Claude → RC → 텔레그램
                log "WARN: Window $sick_idx RC activation failed — full restart"
                TMUX_WINDOW="$sick_idx"
                fast_restart "RC activation failed on window $sick_idx"
            fi
            ;;
        zombie|disconnected|no_claude)
            # 모두 동일 패턴: 기존 윈도우 정리 → 새 윈도우 → Claude --continue → /rc → 텔레그램
            log "WARN: Window $sick_idx ($sick_name): $sick_status — full restart"
            TMUX_WINDOW="$sick_idx"
            fast_restart "$sick_status on window $sick_idx"
            ;;
    esac
done

# 5. RC 세션 수 부족 → 새로 생성하여 TARGET_RC_COUNT 유지
# (복구 후 다시 카운트)
live_count=0
while IFS=: read -r idx name; do
    is_rc=false
    if [ "$name" = "claude" ] || echo "$name" | grep -q "^rc@"; then
        is_rc=true
    fi
    screen=$(tmux capture-pane -t "$TMUX_SESSION:$idx" -p 2>/dev/null)
    if echo "$screen" | grep -q "Remote Control active"; then
        is_rc=true
    fi
    if [ "$is_rc" = true ]; then
        local s
        s=$(check_rc_window_health "$idx")
        [ "$s" = "healthy" ] && live_count=$((live_count + 1))
    fi
done <<< "$(tmux list-windows -t "$TMUX_SESSION" -F '#{window_index}:#{window_name}' 2>/dev/null)"

if [ "$live_count" -lt "$TARGET_RC_COUNT" ]; then
    deficit=$((TARGET_RC_COUNT - live_count))
    log "WARN: Only $live_count/$TARGET_RC_COUNT RC sessions alive — creating $deficit more"
    for i in $(seq 1 $deficit); do
        create_new_rc_session
    done
fi

# 6. 최종 상태 저장
live_final=0
while IFS=: read -r idx name; do
    screen=$(tmux capture-pane -t "$TMUX_SESSION:$idx" -p 2>/dev/null)
    if echo "$screen" | grep -q "Remote Control active"; then
        live_final=$((live_final + 1))
    fi
done <<< "$(tmux list-windows -t "$TMUX_SESSION" -F '#{window_index}:#{window_name}' 2>/dev/null)"

if [ "$live_final" -ge "$TARGET_RC_COUNT" ]; then
    save_health "healthy" "${live_final} RC sessions active"
    reset_fail_count
    check_recovery
else
    save_health "degraded" "${live_final}/${TARGET_RC_COUNT} RC sessions"
fi

# =============================================================================
# 대시보드 헬스체크 (1시간 간격)
# =============================================================================
DASHBOARD_CHECK_FILE="$PROJECT_DIR/data/.dashboard_last_check"
DASHBOARD_CHECK_INTERVAL=3600  # 1시간
DASHBOARD_PORT=5555

dashboard_last_check=0
[ -f "$DASHBOARD_CHECK_FILE" ] && dashboard_last_check=$(cat "$DASHBOARD_CHECK_FILE" 2>/dev/null)
dashboard_now=$(date +%s)
dashboard_elapsed=$((dashboard_now - dashboard_last_check))

if [ "$dashboard_elapsed" -ge "$DASHBOARD_CHECK_INTERVAL" ]; then
    echo "$dashboard_now" > "$DASHBOARD_CHECK_FILE"

    # 1) HTTP 응답 확인
    dashboard_http=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "http://localhost:$DASHBOARD_PORT/" 2>/dev/null)

    if [ "$dashboard_http" = "200" ]; then
        log "DASHBOARD: OK (HTTP $dashboard_http)"
    else
        log "DASHBOARD: FAIL (HTTP $dashboard_http) — restarting"

        # 기존 프로세스 정리
        lsof -i :$DASHBOARD_PORT -t 2>/dev/null | xargs kill -9 2>/dev/null || true
        sleep 2

        # tmux dashboard 윈도우에서 재시작
        if tmux list-windows -t "$TMUX_SESSION" -F '#{window_name}' 2>/dev/null | grep -q "^dashboard$"; then
            tmux send-keys -t "$TMUX_SESSION:dashboard" C-c
            sleep 1
            tmux send-keys -t "$TMUX_SESSION:dashboard" "source .venv/bin/activate && PYTHONPATH=$PROJECT_DIR python scripts/dashboard.py $DASHBOARD_PORT" Enter
        else
            tmux new-window -t "$TMUX_SESSION" -n dashboard -c "$PROJECT_DIR"
            sleep 1
            tmux send-keys -t "$TMUX_SESSION:dashboard" "source .venv/bin/activate && PYTHONPATH=$PROJECT_DIR python scripts/dashboard.py $DASHBOARD_PORT" Enter
        fi

        sleep 5
        # 재시작 확인
        dashboard_http2=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "http://localhost:$DASHBOARD_PORT/" 2>/dev/null)
        if [ "$dashboard_http2" = "200" ]; then
            log "DASHBOARD: Restart succeeded (HTTP $dashboard_http2)"
            send_telegram "🖥️ 대시보드 자동 복구 완료 (port $DASHBOARD_PORT)"
        else
            log "DASHBOARD: Restart FAILED (HTTP $dashboard_http2)"
            send_telegram "❌ 대시보드 복구 실패 — 수동 확인 필요 (port $DASHBOARD_PORT)"
        fi
    fi
fi
