#!/bin/bash
# =============================================================================
# Claude Auto-Restart Wrapper
#
# Claude가 exit하면 자동으로 재시작합니다.
# 사용자 대화형 세션에서 사용:
#   bash scripts/claude_loop.sh
#
# Ctrl+C 2회로 완전 종료
# =============================================================================

PROJECT_DIR="/Users/drj00/workspace/blockchain"
cd "$PROJECT_DIR"

RESTART_COUNT=0
LAST_EXIT_TIME=0
CTRL_C_COUNT=0

trap_handler() {
    CTRL_C_COUNT=$((CTRL_C_COUNT + 1))
    if [ $CTRL_C_COUNT -ge 2 ]; then
        echo ""
        echo "[claude_loop] Ctrl+C 2회 → 완전 종료"
        exit 0
    fi
    echo ""
    echo "[claude_loop] 종료하려면 Ctrl+C 한번 더 누르세요 (3초 이내)"
    sleep 3
    CTRL_C_COUNT=0
}

trap trap_handler INT

echo "[claude_loop] Claude 자동 재시작 모드 시작"
echo "[claude_loop] Ctrl+C 2회로 완전 종료"
echo ""

while true; do
    CTRL_C_COUNT=0

    # Claude 실행
    unset CLAUDECODE
    claude --continue --dangerously-skip-permissions
    EXIT_CODE=$?

    NOW=$(date +%s)

    # 정상 종료 (/exit 등) 감지 — 5초 이내 재exit하면 사용자가 의도적으로 나간 것
    if [ $((NOW - LAST_EXIT_TIME)) -lt 5 ]; then
        echo "[claude_loop] 빠른 연속 종료 감지 → 완전 종료"
        exit 0
    fi

    LAST_EXIT_TIME=$NOW
    RESTART_COUNT=$((RESTART_COUNT + 1))

    echo ""
    echo "[claude_loop] Claude 종료됨 (exit code: $EXIT_CODE, 재시작 #$RESTART_COUNT)"
    echo "[claude_loop] 3초 후 재시작... (Ctrl+C로 취소)"
    sleep 3

    echo "[claude_loop] Claude 재시작 중..."
    echo ""
done
