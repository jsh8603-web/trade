#!/bin/bash
# RC 부활 + 텔레그램 링크 전송
# 리모트랑(RemoteRang) 매시 정각 강제 부활 — com.claude.rc-revival plist에서 호출
# 워치독(watchdog_remote.sh)의 1시간 부활과 이중화
# 사용법: bash ~/workspace/blockchain/scripts/revive_rc.sh

export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"

cd ~/workspace/blockchain
source .venv/bin/activate 2>/dev/null
set -a; source .env 2>/dev/null; set +a

# tmux 세션 결정 (main 우선, 없으면 blockchain)
if tmux has-session -t main 2>/dev/null; then
    TMUX_SESSION="main"
elif tmux has-session -t blockchain 2>/dev/null; then
    TMUX_SESSION="blockchain"
else
    echo "❌ tmux 세션 없음"
    exit 1
fi

# RC가 실제로 살아있는지 tmux 화면으로 확인 (파일 상태만 믿지 않음)
RC_ALIVE=false
if tmux has-session -t main 2>/dev/null; then
    CHECK_SESSION="main"
elif tmux has-session -t blockchain 2>/dev/null; then
    CHECK_SESSION="blockchain"
else
    CHECK_SESSION=""
fi

if [ -n "$CHECK_SESSION" ]; then
    # Find actual RC window name (could be "rc" or "rc@HHMM" from watchdog)
    RC_WINDOW=$(tmux list-windows -t "$CHECK_SESSION" -F '#{window_name}' 2>/dev/null | grep -E '^rc(@|$)' | head -1)
    [ -z "$RC_WINDOW" ] && RC_WINDOW="rc"
    RC_SCREEN=$(tmux capture-pane -t "$CHECK_SESSION:$RC_WINDOW" -p -S -10 2>/dev/null)
    if echo "$RC_SCREEN" | grep -q "Remote Control reconnecting"; then
        echo "⚠️ RC 연결 끊김 감지 (reconnecting) — 부활 필요"
        # health 파일도 갱신
        echo '{"status":"disconnected","ts":"'"$(date '+%Y-%m-%d %H:%M:%S')"'","source":"rc-revival"}' > ~/workspace/blockchain/data/.rc_health.json
    elif echo "$RC_SCREEN" | grep -qE '❯.*Remote Control|Remote Control active|Session ID'; then
        echo "✅ RC 실제 활성 확인 — 스킵"
        # health 파일 갱신 (타임스탬프 최신화)
        URL=$(tmux capture-pane -t "$CHECK_SESSION:$RC_WINDOW" -p 2>/dev/null | grep -oE 'https://claude\.ai/code/session_[A-Za-z0-9_-]+' | tail -1)
        if [ -n "$URL" ]; then
            echo '{"status":"healthy","url":"'"$URL"'","ts":"'"$(date '+%Y-%m-%d %H:%M:%S')"'","source":"rc-revival"}' > ~/workspace/blockchain/data/.rc_health.json
        fi
        exit 0
    elif echo "$RC_SCREEN" | tail -3 | grep -qE '^.*❯\s*$'; then
        # Claude는 살아있지만 RC 모드가 아닌 경우
        echo "⚠️ Claude 활성이지만 RC 모드 아님 — 부활 필요"
    else
        echo "⚠️ RC 윈도우 상태 불명 — 부활 진행"
    fi
else
    echo "⚠️ tmux 세션 없음"
fi

echo "🔄 RC 부활 시작 (세션: $TMUX_SESSION)"

# 기존 rc / rc@HHMM 윈도우 정리
for w in $(tmux list-windows -t "$TMUX_SESSION" -F '#{window_name}' 2>/dev/null | grep -E '^rc(@|$)'); do
    tmux kill-window -t "$TMUX_SESSION:$w" 2>/dev/null
done
sleep 1

# 새 Claude 시작
tmux new-window -t "$TMUX_SESSION" -n rc -c ~/workspace/blockchain
sleep 1
tmux send-keys -t "$TMUX_SESSION:rc" "unset CLAUDECODE && claude --continue --dangerously-skip-permissions" Enter

# Claude 준비 대기 (최대 60초)
for i in $(seq 1 12); do
    sleep 5
    screen=$(tmux capture-pane -t "$TMUX_SESSION:rc" -p -S -5 2>/dev/null)
    if echo "$screen" | grep -qE '❯|>|tips|Claude Code'; then
        echo "✅ Claude ready ($((i*5))s)"
        break
    fi
    echo "⏳ Waiting... $((i*5))s"
done

# /remote-control 실행
tmux send-keys -t "$TMUX_SESSION:rc" "/remote-control" Enter
sleep 5
tmux send-keys -t "$TMUX_SESSION:rc" Enter

# RC 활성화 대기 (최대 30초)
URL=""
for attempt in $(seq 1 6); do
    sleep 5
    screen=$(tmux capture-pane -t "$TMUX_SESSION:rc" -p -J 2>/dev/null)
    if echo "$screen" | grep -q "Remote Control active"; then
        URL=$(echo "$screen" | grep -oE 'https://claude\.ai/code/session_[A-Za-z0-9_-]+' | tail -1)
        # URL이 화면에 없으면 remote_url.txt에서 시도
        [ -z "$URL" ] && URL=$(cat ~/workspace/blockchain/data/remote_url.txt 2>/dev/null)
        echo "✅ RC active 감지 ($((attempt*5))s)"
        break
    fi
    echo "⏳ RC 대기... $((attempt*5))s"
done

if [ -n "$URL" ]; then
    echo "✅ RC 활성: $URL"
    echo "$URL" > ~/workspace/blockchain/data/remote_url.txt
    echo '{"status":"healthy","url":"'"$URL"'","ts":"'"$(date '+%Y-%m-%d %H:%M:%S')"'","source":"rc-revival"}' > ~/workspace/blockchain/data/.rc_health.json
    date +%s > ~/workspace/blockchain/data/.rc_revive_ts
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_USER_ID}" \
        --data-urlencode "text=🔄 RC 매시 부활 완료

🔗 링크: $URL" \
        -d "disable_web_page_preview=true" > /dev/null
    echo "✅ 텔레그램 전송 완료"
elif tmux capture-pane -t "$TMUX_SESSION:rc" -p 2>/dev/null | grep -qE "Remote Control active|Remote Control ❯"; then
    # RC는 살아있는데 URL만 못 찾은 경우
    echo "⚠️ RC 활성이나 URL 추출 실패 — health만 갱신"
    echo '{"status":"healthy","url":"unknown","ts":"'"$(date '+%Y-%m-%d %H:%M:%S')"'","source":"rc-revival"}' > ~/workspace/blockchain/data/.rc_health.json
    date +%s > ~/workspace/blockchain/data/.rc_revive_ts
else
    echo "❌ RC 활성화 실패 — 워치독에 위임"
    echo '{"status":"failed","ts":"'"$(date '+%Y-%m-%d %H:%M:%S')"'","source":"rc-revival"}' > ~/workspace/blockchain/data/.rc_health.json
fi
