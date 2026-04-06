#!/bin/bash
# ──────────────────────────────────────────────────────────
# 모니터 강제 슬립 스크립트
#
# Chrome Remote Desktop이 NoDisplaySleepAssertion을 걸어서
# macOS의 displaysleep 설정이 무시되는 문제를 우회한다.
# 1분마다 idle time을 체크하여 5분 이상이면 모니터를 끈다.
# ──────────────────────────────────────────────────────────

IDLE_THRESHOLD=300  # 5분

while true; do
    IDLE=$(ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print int($NF/1000000000); exit}')
    if [ "$IDLE" -ge "$IDLE_THRESHOLD" ]; then
        pmset displaysleepnow 2>/dev/null
    fi
    sleep 60
done
