#!/bin/bash
# RC 부활 + 텔레그램 링크 전송
# 사용법: bash ~/workspace/blockchain/scripts/revive_rc.sh

cd ~/workspace/blockchain
source .venv/bin/activate
source .env

# tmux 세션 결정 (main 우선, 없으면 blockchain)
if tmux has-session -t main 2>/dev/null; then
    TMUX_SESSION="main"
elif tmux has-session -t blockchain 2>/dev/null; then
    TMUX_SESSION="blockchain"
else
    echo "❌ tmux 세션 없음"
    exit 1
fi

# RC가 이미 healthy하면 스킵
RC_HEALTH=$(cat ~/workspace/blockchain/data/.rc_health.json 2>/dev/null)
if echo "$RC_HEALTH" | grep -q '"status":"healthy"'; then
    echo "✅ RC 이미 healthy — 스킵"
    exit 0
fi

echo "🔄 RC 부활 시작 (세션: $TMUX_SESSION)"

# 기존 rc 윈도우 정리
tmux kill-window -t $TMUX_SESSION:rc 2>/dev/null
sleep 1

# 새 Claude 시작
tmux new-window -t $TMUX_SESSION -n rc -c ~/workspace/blockchain
sleep 1
tmux send-keys -t $TMUX_SESSION:rc "unset CLAUDECODE && claude --continue --dangerously-skip-permissions" Enter

# Claude 준비 대기 (최대 60초)
for i in $(seq 1 12); do
    sleep 5
    screen=$(tmux capture-pane -t $TMUX_SESSION:rc -p -S -5 2>/dev/null)
    if echo "$screen" | grep -qE '❯|>|tips|Claude Code'; then
        echo "✅ Claude ready (${i}0s)"
        break
    fi
    echo "⏳ Waiting... ${i}0s"
done

# /remote-control 실행
tmux send-keys -t $TMUX_SESSION:rc "/remote-control" Enter
sleep 5
tmux send-keys -t $TMUX_SESSION:rc Enter
sleep 20

# URL 추출
URL=$(tmux capture-pane -t $TMUX_SESSION:rc -p 2>/dev/null | grep -oE 'https://claude\.ai/code/[A-Za-z0-9_-]+' | tail -1)

if [ -n "$URL" ]; then
    echo "✅ RC 활성: $URL"
    # 텔레그램 전송
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_USER_ID}" \
        --data-urlencode "text=🔄 RC 부활 완료

🔗 링크: $URL" \
        -d "disable_web_page_preview=true" > /dev/null
    echo "✅ 텔레그램 전송 완료"
else
    echo "❌ RC 활성화 실패"
fi
