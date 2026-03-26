#!/bin/bash
# 리포를 private으로 전환
cd ~/workspace/blockchain
gh repo edit --visibility private
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Repo set to PRIVATE" >> ~/workspace/blockchain/logs/repo_visibility.log 2>/dev/null \
  || echo "[$(date '+%Y-%m-%d %H:%M:%S')] Repo set to PRIVATE" >> /tmp/blockchain_logs/repo_visibility.log

# 텔레그램 알림
source ~/workspace/blockchain/.env
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d chat_id="${TELEGRAM_USER_ID}" \
  -d text="🔒 GitHub 리포 private으로 전환 완료" > /dev/null
