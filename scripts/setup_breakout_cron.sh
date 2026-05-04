#!/usr/bin/env bash
# 변동성 돌파 cron 등록 (macOS / Linux)
#
# 사용:
#   bash scripts/setup_breakout_cron.sh           # 등록
#   bash scripts/setup_breakout_cron.sh --remove  # 해제
#   bash scripts/setup_breakout_cron.sh --status  # 현재 등록 상태 확인
#
# 등록 작업:
#   1) 매일 10:00 KST — breakout_trader.py (매수/24h 청산)
#   2) 매 15분 (00, 15, 30, 45) — breakout_monitor.py (손절 감시)

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"
LOG_DIR="$PROJECT_DIR/logs/breakout"
mkdir -p "$LOG_DIR"

# 가상환경 자동 감지 (macOS/Linux)
if [ ! -x "$PYTHON" ]; then
    if [ -x "$PROJECT_DIR/.venv/Scripts/python.exe" ]; then
        PYTHON="$PROJECT_DIR/.venv/Scripts/python.exe"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON="python3"
        echo "[warning] .venv/bin/python 없음 — 시스템 python3 사용"
    else
        echo "[error] python 인터프리터 못 찾음. .venv 생성 필요" >&2
        exit 1
    fi
fi

CRON_TAG="# CoinTrading_Breakout"
TRADE_LINE="0 10 * * * cd $PROJECT_DIR && $PYTHON scripts/breakout_trader.py >> $LOG_DIR/cron_trade.log 2>&1 $CRON_TAG"
MONITOR_LINE="*/15 * * * * cd $PROJECT_DIR && $PYTHON scripts/breakout_monitor.py >> $LOG_DIR/cron_monitor.log 2>&1 $CRON_TAG"

case "${1:-install}" in
    --remove|remove)
        echo "변동성 돌파 cron 해제 중..."
        (crontab -l 2>/dev/null | grep -v "$CRON_TAG") | crontab - || true
        echo "완료"
        ;;
    --status|status)
        echo "현재 등록된 변동성 돌파 cron:"
        crontab -l 2>/dev/null | grep "$CRON_TAG" || echo "  (등록된 작업 없음)"
        ;;
    install|--install|"")
        echo "변동성 돌파 cron 등록 중..."
        echo "  PROJECT_DIR: $PROJECT_DIR"
        echo "  PYTHON: $PYTHON"

        # 기존 작업 제거 (재등록 안전)
        EXISTING=$(crontab -l 2>/dev/null | grep -v "$CRON_TAG" || true)

        # 새 작업 추가
        printf '%s\n%s\n%s\n' "$EXISTING" "$TRADE_LINE" "$MONITOR_LINE" | grep -v '^$' | crontab -

        echo "  등록: 매일 10:00 → breakout_trader.py"
        echo "  등록: 매 15분 → breakout_monitor.py"
        echo ""
        echo "현재 등록된 작업:"
        crontab -l | grep "$CRON_TAG" | sed 's/^/  /'
        echo ""
        echo "[안내]"
        echo "  로그: $LOG_DIR/YYYYMMDD.log (매매 이력)"
        echo "       $LOG_DIR/cron_*.log (cron 출력)"
        echo "  state: $PROJECT_DIR/data/breakout_state.json"
        echo "  현재 모드: BREAKOUT_DRY_RUN=true (.env) — 실거래 없음, 알림만"
        echo "  실거래 전환: .env에서 BREAKOUT_DRY_RUN=false 로 변경"
        echo "  완전 정지: .env에서 BREAKOUT_ENABLED=false 또는 EMERGENCY_STOP=true"
        ;;
    *)
        echo "사용법: $0 [install | --remove | --status]"
        exit 1
        ;;
esac
