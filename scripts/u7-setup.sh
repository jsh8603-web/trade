#!/bin/bash
# U7 — E2E 실작동 검사 환경 설정 및 검사 자동화

set -e  # 에러 시 즉시 중단

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== U7 E2E 검사 자동화 설정 ==="
echo "Project: $PROJECT_DIR"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# 1. Python 환경 확인
echo "[1/5] Python 환경 확인..."
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found in PATH"
    echo "💡 시스템 Python 또는 pyenv 설정 필요"
    exit 1
fi

python_version=$(python3 --version 2>&1 || echo "unknown")
echo "✅ $python_version"

# 2. venv 활성화 또는 생성
echo "[2/5] Python venv 설정..."
if [ ! -d ".venv" ]; then
    echo "  📦 venv 생성 중..."
    python3 -m venv .venv
fi

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ venv 활성화"
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
    echo "✅ venv 활성화 (Windows)"
else
    echo "⚠️  venv 활성화 경로 불명"
fi

# 3. 의존성 설치
echo "[3/5] 의존성 설치..."
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    echo "✅ requirements.txt 설치 완료"
else
    echo "⚠️  requirements.txt 미발견"
fi

# 4. 테스트 패키지 확인
echo "[4/5] 테스트 도구 확인..."
if python3 -m pytest --version &> /dev/null; then
    echo "✅ pytest 설치됨"
else
    echo "⚠️  pytest 미설치 (U7 단위테스트 스킵)"
fi

# 5. 데이터 디렉토리 준비
echo "[5/5] 데이터 디렉토리 준비..."
mkdir -p data logs/executions
echo "✅ 디렉토리 준비 완료"

# 환경변수 확인
echo ""
echo "=== 환경변수 상태 ==="
if [ -f ".env" ]; then
    echo "✅ .env 파일 존재"
    # API key 존재 여부 확인 (내용은 숨김)
    grep -q "UPBIT_ACCESS_KEY\|UPBIT_SECRET_KEY" .env && echo "  ✓ Upbit credentials" || echo "  ✗ Upbit credentials 미설정"
    grep -q "TAVILY_API_KEY" .env && echo "  ✓ Tavily API key" || echo "  ✗ Tavily API key 미설정"
else
    echo "⚠️  .env 파일 미발견 (API 호출 기능 스킵됨)"
    echo "   💡 사용 시: cp .env.example .env && 각 항목 채우기"
fi

# DRY_RUN 기본값 확인
DRY_RUN=${DRY_RUN:-true}
EMERGENCY_STOP=${EMERGENCY_STOP:-false}
echo ""
echo "=== 안전장치 상태 ==="
echo "DRY_RUN=$DRY_RUN (기본값: true, 실주문 차단)"
echo "EMERGENCY_STOP=$EMERGENCY_STOP (기본값: false, 긴급정지 미발동)"

echo ""
echo "=== U7 환경 설정 완료 ==="
echo "✅ 다음 스텝:"
echo "   1. pytest tests/ -q --tb=short          # 회귀 검증"
echo "   2. python scripts/collect_market_data.py  # 데이터 수집"
echo "   3. python agents/base_agent.py ...      # 에이전트 결정"
echo ""
