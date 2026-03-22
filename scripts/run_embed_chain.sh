#!/bin/bash
# 2022년 collect 완료 대기 후 → 2023년 임베딩 + Supabase 저장
# 2022년은 collect_2022_data.py에서 이미 처리 중
# 이 스크립트는 2023년 데이터의 임베딩 + Supabase 저장만 담당

cd "$(dirname "$0")/.."

echo "=== 2023년 임베딩 + Supabase 저장 시작 ==="
python -u scripts/embed_historical_data.py 2023

echo "=== 완료 ==="
