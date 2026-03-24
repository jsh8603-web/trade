#!/bin/bash
# Lifeline 자가치유 시스템 — cron/launchd 래퍼
# 매 2시간마다 :15에 실행 (com.claude.lifeline plist)
# 감시 → 진단 → 치유 → DB 기록 → 텔레그램 알림

export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"

cd ~/workspace/blockchain || exit 1
source .venv/bin/activate 2>/dev/null

# 외장하드 심볼릭 logs는 launchd에서 쓰기 불가 → /tmp 사용
LOG_DIR="/tmp/lifeline_logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date '+%Y-%m-%d_%H%M')
LOG_FILE="$LOG_DIR/lifeline_${TIMESTAMP}.log"

echo "=== Lifeline 실행 시작: $(date '+%Y-%m-%d %H:%M:%S KST') ===" | tee "$LOG_FILE"

# Lifeline main.py 실행 (--verbose로 상세 로그)
RESULT=$(python scripts/lifeline/main.py --once --verbose 2>>"$LOG_FILE")
EXIT_CODE=$?

echo "$RESULT" >> "$LOG_FILE"

# 결과 파싱
NON_OK=$(echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('non_ok_count',0))" 2>/dev/null || echo "?")
HEALED=$(echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('healed_count',0))" 2>/dev/null || echo "?")
DB_SYNCED=$(echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('db_synced_count',0))" 2>/dev/null || echo "?")
STATUS=$(echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('overall_status','UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")

echo "=== 완료: status=$STATUS, issues=$NON_OK, healed=$HEALED, db=$DB_SYNCED, exit=$EXIT_CODE ===" | tee -a "$LOG_FILE"

# 7일 이상 오래된 로그 정리
find "$LOG_DIR" -name "lifeline_*.log" -mtime +7 -delete 2>/dev/null

exit $EXIT_CODE
