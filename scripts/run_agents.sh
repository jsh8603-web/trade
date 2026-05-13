#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────
# 에이전트 모드 파이프라인
#
# 기존 run_analysis.sh(LLM 프롬프트 조립 방식)와 달리,
# Python 에이전트가 직접 데이터 수집 → 전략 전환 → 매매 판단을 수행한다.
#
# 사용법:
#   bash scripts/run_agents.sh              # 일반 실행
#   DRY_RUN=true bash scripts/run_agents.sh # 시뮬레이션
# ──────────────────────────────────────────────────────────

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# cron/launchd 환경에서 $SECONDS가 불안정할 수 있으므로 명시적 epoch 사용
START_EPOCH=$(date +%s)

# .env 로드
if [ -f .env ]; then
  set -a; source .env; set +a
fi

# Python 실행파일 결정 (venv 직접 사용, activate 불필요)
if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python3"
fi

# Windows cp949 → UTF-8 강제 (Python subprocess 출력 인코딩)
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

# 긴급 정지 확인 — 사용자 수동
if [ "${EMERGENCY_STOP:-false}" = "true" ]; then
  echo "[STOP] 사용자 EMERGENCY_STOP 활성화됨. 실행 중단." >&2
  "$PYTHON" scripts/notify_telegram.py error "EMERGENCY_STOP" "사용자 긴급 정지 활성화로 에이전트 실행 중단" 2>/dev/null || true
  exit 1
fi

# 긴급 정지 확인 — 감독 자동 (data/auto_emergency.json)
AUTO_EMERGENCY_FILE="${PROJECT_DIR}/data/auto_emergency.json"
if [ -f "$AUTO_EMERGENCY_FILE" ]; then
  IS_ACTIVE=$("$PYTHON" -c "import json; d=json.load(open('$AUTO_EMERGENCY_FILE','r',encoding='utf-8')); print(d.get('active',False))" 2>/dev/null || echo "False")
  if [ "$IS_ACTIVE" = "True" ]; then
    REASON=$("$PYTHON" -c "import json; d=json.load(open('$AUTO_EMERGENCY_FILE','r',encoding='utf-8')); print(d.get('reason','알 수 없음'))" 2>/dev/null || echo "알 수 없음")
    echo "[STOP] 감독 자동 긴급정지 활성 중: $REASON" >&2
    echo "[STOP] Orchestrator가 해제 조건을 평가합니다..." >&2
    # Orchestrator 내부에서 해제 여부를 판단하므로 여기서는 차단하지 않고
    # Phase 2까지는 진행시킨다 (Orchestrator가 해제 가능 여부를 확인해야 하므로)
  fi
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CYCLE_ID="$(date +%Y%m%d-%H%M)-agent"
SNAPSHOT_DIR="data/snapshots/${TIMESTAMP}"
LOG_DIR="logs/executions"
mkdir -p "$SNAPSHOT_DIR" "$LOG_DIR" 2>/dev/null

# 외장하드 심볼릭 쓰기 불가 시 /tmp fallback
if ! touch "$SNAPSHOT_DIR/.write_test" 2>/dev/null; then
    SNAPSHOT_DIR="/tmp/blockchain_logs/snapshots/${TIMESTAMP}"
    mkdir -p "$SNAPSHOT_DIR"
    echo "[WARN] data/snapshots 쓰기 불가 → /tmp fallback: $SNAPSHOT_DIR" >&2
fi
rm -f "$SNAPSHOT_DIR/.write_test" 2>/dev/null

if ! touch "$LOG_DIR/.write_test" 2>/dev/null; then
    LOG_DIR="/tmp/blockchain_logs/executions"
    mkdir -p "$LOG_DIR"
    echo "[WARN] logs/executions 쓰기 불가 → /tmp fallback: $LOG_DIR" >&2
fi
rm -f "$LOG_DIR/.write_test" 2>/dev/null

echo "[$(date)] ═══ 에이전트 모드 시작 ═══" >&2

# ── Phase 1: 내부 시장 데이터 수집 (기존 스크립트 활용) ──
echo "[$(date)] Phase 1: 내부 데이터 수집..." >&2

# 병렬 수집
"$PYTHON" scripts/collect_market_data.py > "${SNAPSHOT_DIR}/market_data.json" 2>/dev/null &
PID_MARKET=$!

"$PYTHON" scripts/get_portfolio.py > "${SNAPSHOT_DIR}/portfolio.json" 2>/dev/null &
PID_PORTFOLIO=$!

"$PYTHON" scripts/collect_ai_signal.py > "${SNAPSHOT_DIR}/ai_signal.json" 2>/dev/null &
PID_AI=$!

# 병렬 완료 대기 + 에러 핸들링
wait $PID_MARKET 2>/dev/null || echo '{"error":"market_data 수집 실패"}' > "${SNAPSHOT_DIR}/market_data.json"
wait $PID_PORTFOLIO 2>/dev/null || echo '{"error":"portfolio 조회 실패"}' > "${SNAPSHOT_DIR}/portfolio.json"
wait $PID_AI 2>/dev/null || echo '{"error":"ai_signal 수집 실패"}' > "${SNAPSHOT_DIR}/ai_signal.json"

echo "[$(date)] Phase 1 완료." >&2

# ── Phase 2: 에이전트 실행 (Python) ──
echo "[$(date)] Phase 2: 에이전트 파이프라인 실행..." >&2

if ! AGENT_RESULT=$("$PYTHON" -c "
import json, sys, os
sys.path.insert(0, '.')

# cycle_id 설정 — 이 파이프라인의 모든 DB 기록에 사용
try:
    from scripts.cycle_id import set_cycle_id
    set_cycle_id('${CYCLE_ID}')
except Exception:
    pass

from agents.external_data import ExternalDataAgent
from agents.orchestrator import Orchestrator
from pathlib import Path

snapshot_dir = Path('${SNAPSHOT_DIR}')

# 1) 외부 데이터 수집 (ExternalDataAgent)
print('[Agent] 외부 데이터 수집 중...', file=sys.stderr)
ext_agent = ExternalDataAgent(snapshot_dir=snapshot_dir)
external_data = ext_agent.collect_all()
print(f'[Agent] 외부 데이터 수집 완료 ({external_data[\"collection_time_sec\"]}초, 에러: {external_data[\"errors\"]})', file=sys.stderr)

# 2) 내부 데이터 로드
market_data = json.loads(open(snapshot_dir / 'market_data.json', encoding='utf-8').read())
portfolio = json.loads(open(snapshot_dir / 'portfolio.json', encoding='utf-8').read())
ai_signal = json.loads(open(snapshot_dir / 'ai_signal.json', encoding='utf-8').read())

# market_data에 ai_composite_signal 주입
market_data['ai_composite_signal'] = ai_signal.get('composite_signal', {})

# FGI 정보를 market_data에 주입 (에이전트가 참조)
fgi_data = external_data.get('sources', {}).get('fear_greed', {})
market_data['fear_greed'] = fgi_data.get('current', {})

# 뉴스 정보를 market_data에 주입
news_data = external_data.get('sources', {}).get('news', {})
news_sentiment = external_data.get('sources', {}).get('news_sentiment', {})
market_data['news'] = news_data
market_data['news']['overall_sentiment'] = news_sentiment.get('overall_sentiment', 'neutral')
market_data['news']['sentiment_score'] = news_sentiment.get('sentiment_score', 0)

# 3) 과거 결정 조회 (Supabase)
past_decisions = []
supabase_url = os.getenv('SUPABASE_URL', '')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
if supabase_url and supabase_key:
    try:
        import requests
        resp = requests.get(
            f'{supabase_url}/rest/v1/decisions',
            params={'select': '*', 'order': 'created_at.desc', 'limit': '10'},
            headers={
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
            },
            timeout=10,
        )
        if resp.status_code == 200:
            past_decisions = resp.json()
    except Exception as e:
        print(f'[Agent] Supabase 조회 실패: {e}', file=sys.stderr)

# 4) BTC 비중 계산
btc_info = portfolio.get('coins', {}).get('BTC', portfolio.get('btc', {}))
total_eval = portfolio.get('total_evaluation', 1)
btc_eval = btc_info.get('evaluation', 0) if isinstance(btc_info, dict) else 0
portfolio['btc_ratio'] = btc_eval / total_eval if total_eval > 0 else 0
portfolio['btc'] = btc_info if isinstance(btc_info, dict) else {}

# 5) Orchestrator 실행
print('[Agent] Orchestrator 실행 중...', file=sys.stderr)
orchestrator = Orchestrator()
result = orchestrator.run(
    market_data=market_data,
    external_data=external_data,
    portfolio=portfolio,
    past_decisions=past_decisions,
)
print(f'[Agent] 결정: {result[\"decision\"][\"decision\"]} by {result[\"active_agent\"]}', file=sys.stderr)

# 6) 전체 결과 조립
output = {
    'timestamp': external_data['timestamp'],
    'active_agent': result['active_agent'],
    'switch': result.get('switch'),
    'decision': result['decision'],
    'external_data_summary': {
        'collection_time_sec': external_data['collection_time_sec'],
        'errors': external_data['errors'],
        'signal': external_data.get('external_signal', {}),
    },
    'snapshot_dir': str(snapshot_dir),
}

print(json.dumps(output, ensure_ascii=False, indent=2))
" 2>&2); then
  AGENT_EXIT=$?
  echo "[$(date)] Phase 2 실패 (exit $AGENT_EXIT)" >&2
  "$PYTHON" scripts/notify_telegram.py error "Agent Pipeline" "에이전트 파이프라인 실패 (exit $AGENT_EXIT)" 2>/dev/null || true
  exit 1
fi

echo "[$(date)] Phase 2 완료." >&2

# 결과 저장
echo "$AGENT_RESULT" > "${SNAPSHOT_DIR}/agent_result.json"

# ── Phase 3: 매매 실행 ──
# JSON 파싱을 단일 Python 호출로 통합 (기존 7회 → 1회)
eval "$(echo "$AGENT_RESULT" | "$PYTHON" -c "
import sys, json
try:
    r = json.load(sys.stdin)
    d = r.get('decision', {})
    sw = r.get('switch')
    sw_str = f\"전략 전환: {sw['from']} → {sw['to']} ({sw['reason']})\" if sw else '전환 없음'
    # shell 변수로 export (값에 single quote가 포함될 수 있으므로 이스케이프)
    def sh_escape(s):
        return str(s).replace(\"'\", \"'\\\\''\")
    print(f\"DECISION='{sh_escape(d.get('decision','hold'))}'\")
    print(f\"REASON='{sh_escape(d.get('reason',''))}'\")
    print(f\"AGENT_NAME='{sh_escape(r.get('active_agent','unknown'))}'\")
    print(f\"SWITCH_INFO='{sh_escape(sw_str)}'\")
except Exception:
    print(\"DECISION='hold'\")
    print(\"REASON=''\")
    print(\"AGENT_NAME='unknown'\")
    print(\"SWITCH_INFO='전환 없음'\")
")"

echo "[$(date)] Phase 3: 매매 실행 — $DECISION ($AGENT_NAME)" >&2

# trade_params + Phase 4 데이터를 단일 Python 호출로 추출 (기존 6회 → 1회)
eval "$(echo "$AGENT_RESULT" | "$PYTHON" -c "
import sys, json
try:
    r = json.load(sys.stdin)
    d = r.get('decision', {})
    tp = d.get('trade_params', {})
    def sh_escape(s):
        return str(s).replace(\"'\", \"'\\\\''\")
    print(f\"TRADE_MARKET='{sh_escape(tp.get('market','KRW-BTC'))}'\")
    print(f\"TRADE_AMOUNT='{sh_escape(tp.get('amount',0))}'\")
    vol = tp.get('volume', 0)
    vol = 0 if vol is None else vol
    print(f\"TRADE_VOLUME='{sh_escape(vol)}'\")
    print(f\"TRADE_IS_DCA='{sh_escape(tp.get('is_dca',False))}'\")
    print(f\"SELL_ALL='{sh_escape(tp.get('sell_all',False))}'\")
    print(f\"BUY_SCORE='{sh_escape(d.get('buy_score',{}).get('total','N/A'))}'\")
    print(f\"CONFIDENCE='{sh_escape(round(d.get('confidence',0)*100))}'\")
except Exception:
    print(\"TRADE_MARKET='KRW-BTC'\")
    print(\"TRADE_AMOUNT='0'\")
    print(\"TRADE_VOLUME='0'\")
    print(\"TRADE_IS_DCA='False'\")
    print(\"SELL_ALL='False'\")
    print(\"BUY_SCORE='N/A'\")
    print(\"CONFIDENCE='0'\")
")"

if [ "$DECISION" = "buy" ]; then
  if "$PYTHON" -c "assert float('$TRADE_AMOUNT') > 0" 2>/dev/null; then
    DCA_TAG=""
    [ "$TRADE_IS_DCA" = "True" ] && DCA_TAG=" [DCA]"
    echo "[$(date)] 매수 실행: $TRADE_MARKET $TRADE_AMOUNT KRW${DCA_TAG}" >&2
    "$PYTHON" scripts/execute_trade.py bid "$TRADE_MARKET" "$TRADE_AMOUNT" "swing_${AGENT_NAME}" 2>&1 | tee -a "$LOG_DIR/trade_${TIMESTAMP}.log"
  fi

elif [ "$DECISION" = "sell" ]; then
  SELL_VOLUME="$TRADE_VOLUME"
  # sell_all: 포트폴리오에서 BTC 잔고를 조회하여 전량 매도
  if [ "$SELL_ALL" = "True" ]; then
    SELL_VOLUME=$("$PYTHON" -c "
import json, sys
p = json.load(open('${SNAPSHOT_DIR}/portfolio.json', encoding='utf-8'))
btc = p.get('coins', {}).get('BTC', p.get('btc', {}))
bal = btc.get('balance', btc.get('volume', 0)) if isinstance(btc, dict) else 0
print(bal if bal else 0)
" 2>/dev/null || echo "0")
    echo "[$(date)] sell_all 감지: BTC 잔고 $SELL_VOLUME 전량 매도" >&2
  fi
  if "$PYTHON" -c "assert float('$SELL_VOLUME') > 0" 2>/dev/null; then
    echo "[$(date)] 매도 실행: $TRADE_MARKET $SELL_VOLUME BTC" >&2
    "$PYTHON" scripts/execute_trade.py ask "$TRADE_MARKET" "$SELL_VOLUME" "swing_${AGENT_NAME}" 2>&1 | tee -a "$LOG_DIR/trade_${TIMESTAMP}.log"
  fi

else
  echo "[$(date)] 관망 결정. 매매 없음." >&2
fi

# ── Phase 4: 텔레그램 알림 ──
echo "[$(date)] Phase 4: 텔레그램 알림..." >&2

SUMMARY="${AGENT_NAME} | ${DECISION} (${CONFIDENCE}%)"
DETAIL="근거: ${REASON}
매수점수: ${BUY_SCORE}
${SWITCH_INFO}"

"$PYTHON" scripts/notify_telegram.py trade "$SUMMARY" "$DETAIL" 2>/dev/null || true

# ── Phase 5: Supabase 기록 ──
if [ -n "${SUPABASE_URL:-}" ] && [ -n "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then
  echo "[$(date)] Phase 5: Supabase 기록..." >&2
  "$PYTHON" -c "
import json, os, requests, sys

DECISION_MAP = {'buy': '매수', 'sell': '매도', 'hold': '관망'}

result = json.loads(open('${SNAPSHOT_DIR}/agent_result.json', encoding='utf-8').read())
dec = result['decision']
market = json.loads(open('${SNAPSHOT_DIR}/market_data.json', encoding='utf-8').read())

raw_decision = dec['decision']
kr_decision = DECISION_MAP.get(raw_decision, raw_decision)

agent_name = result.get('active_agent', '')
buy_score = dec.get('buy_score', {})
ext_summary = dec.get('external_signal_summary', {})

reason_parts = [dec.get('reason', '')]
if agent_name:
    reason_parts.append(f'에이전트: {agent_name}')
if buy_score:
    reason_parts.append(f'매수점수: {buy_score.get(\"total\", \"?\")}/{buy_score.get(\"threshold\", \"?\")}')
if ext_summary:
    reason_parts.append(f'외부시그널: {ext_summary.get(\"fusion_signal\", \"?\")}({ext_summary.get(\"total_score\", \"?\")})')

row = {
    'decision': kr_decision,
    'confidence': dec.get('confidence', 0),
    'reason': ' | '.join(reason_parts),
    'current_price': int(market.get('current_price') or market.get('ticker', {}).get('trade_price', 0)),
    'rsi_value': market.get('indicators', {}).get('rsi_14'),
    'fear_greed_value': buy_score.get('fgi', {}).get('value'),
    'market_data_snapshot': json.dumps({
        'buy_score': buy_score,
        'external': ext_summary,
        'snapshot_dir': '${SNAPSHOT_DIR}',
    }, ensure_ascii=False),
    'cycle_id': '${CYCLE_ID}',
    'source': 'agent',
}

resp = requests.post(
    os.environ['SUPABASE_URL'] + '/rest/v1/decisions',
    json=row,
    headers={
        'apikey': os.environ['SUPABASE_SERVICE_ROLE_KEY'],
        'Authorization': 'Bearer ' + os.environ['SUPABASE_SERVICE_ROLE_KEY'],
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
    },
    timeout=10,
)
if resp.status_code in (200, 201):
    print(f'[Agent] Supabase 기록 완료 (HTTP {resp.status_code})', file=sys.stderr)
else:
    print(f'[Agent] Supabase 기록 실패! HTTP {resp.status_code}: {resp.text}', file=sys.stderr)
" 2>&1 || true
fi

# ── Phase 5b: market_data 기록 ──
if [ -n "${SUPABASE_URL:-}" ] && [ -n "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then
  echo "[$(date)] Phase 5b: market_data + execution_logs 기록..." >&2
  "$PYTHON" -c "
import json, os, time, requests, sys

supabase_url = os.environ['SUPABASE_URL']
supabase_key = os.environ['SUPABASE_SERVICE_ROLE_KEY']
headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal',
}

# market_data 저장
try:
    market = json.loads(open('${SNAPSHOT_DIR}/market_data.json', encoding='utf-8').read())
    ticker = market.get('ticker', {})
    indicators = market.get('indicators', {})
    result = json.loads(open('${SNAPSHOT_DIR}/agent_result.json', encoding='utf-8').read())
    fgi = market.get('fear_greed', result.get('decision', {}).get('buy_score', {}).get('fgi', {}))
    news = market.get('news', {})

    price = ticker.get('trade_price') or market.get('current_price', 0)
    row = {
        'market': 'KRW-BTC',
        'price': int(price) if price else 0,
        'volume_24h': float(ticker.get('acc_trade_volume_24h', 0)) if ticker.get('acc_trade_volume_24h') else None,
        'change_rate_24h': float(ticker.get('signed_change_rate', 0)) if ticker.get('signed_change_rate') else None,
        'fear_greed_value': fgi.get('value') if isinstance(fgi, dict) else None,
        'fear_greed_class': fgi.get('value_classification') if isinstance(fgi, dict) else None,
        'rsi_14': indicators.get('rsi_14'),
        'sma_20': int(indicators.get('sma_20')) if indicators.get('sma_20') else None,
        'news_sentiment': news.get('overall_sentiment', 'neutral'),
        'cycle_id': '${CYCLE_ID}',
    }
    resp = requests.post(f'{supabase_url}/rest/v1/market_data', json=row, headers=headers, timeout=10)
    if resp.status_code in (200, 201):
        print('[Agent] market_data 기록 완료', file=sys.stderr)
    else:
        print(f'[Agent] market_data 기록 실패: HTTP {resp.status_code}: {resp.text[:200]}', file=sys.stderr)
except Exception as e:
    print(f'[Agent] market_data 기록 예외: {e}', file=sys.stderr)

# execution_logs 저장
try:
    dry_run = os.environ.get('DRY_RUN', 'true').lower() == 'true'
    decision = result.get('decision', {}).get('decision', 'hold')
    if decision in ('buy', 'sell') and not dry_run:
        exec_mode = 'execute'
    elif decision in ('buy', 'sell') and dry_run:
        exec_mode = 'dry_run'
    else:
        exec_mode = 'analyze'

    log_row = {
        'execution_mode': exec_mode,
        'duration_ms': int(float('$(( $(date +%s) - START_EPOCH ))') * 1000),
        'data_sources': json.dumps({
            'sources': ['market_data', 'portfolio', 'ai_signal', 'external_data'],
            'agent': result.get('active_agent', ''),
            'decision': decision,
            'snapshot_dir': '${SNAPSHOT_DIR}',
        }, ensure_ascii=False),
        'raw_output': json.dumps(result, ensure_ascii=False)[:10000],
        'cycle_id': '${CYCLE_ID}',
    }
    resp = requests.post(f'{supabase_url}/rest/v1/execution_logs', json=log_row, headers=headers, timeout=10)
    if resp.status_code in (200, 201):
        print('[Agent] execution_logs 기록 완료', file=sys.stderr)
    else:
        print(f'[Agent] execution_logs 기록 실패: HTTP {resp.status_code}: {resp.text[:200]}', file=sys.stderr)
except Exception as e:
    print(f'[Agent] execution_logs 기록 예외: {e}', file=sys.stderr)
" 2>&1 || true
fi

# ── Phase 5c: portfolio_snapshots 기록 ──
if [ -n "${SUPABASE_URL:-}" ] && [ -n "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then
  echo "[$(date)] Phase 5c: portfolio_snapshots 기록..." >&2
  "$PYTHON" -c "
import json, os, requests, sys

supabase_url = os.environ['SUPABASE_URL']
supabase_key = os.environ['SUPABASE_SERVICE_ROLE_KEY']
headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal',
}

try:
    from utils.machine import skip_trade_db, get_machine_name
    if skip_trade_db('portfolio_snapshots'):
        print('[Agent] portfolio_snapshots 스킵 (worker 머신)', file=sys.stderr)
        sys.exit(0)
    machine_name = get_machine_name()
except Exception:
    machine_name = None

try:
    portfolio = json.loads(open('${SNAPSHOT_DIR}/portfolio.json', encoding='utf-8').read())
    if 'error' in portfolio:
        print(f'[Agent] portfolio_snapshots 스킵: 포트폴리오 수집 실패', file=sys.stderr)
        sys.exit(0)

    krw_balance = int(portfolio.get('krw_balance', 0))
    holdings = portfolio.get('holdings', [])
    crypto_value = int(sum(h.get('eval_amount', 0) for h in holdings))
    total_value = int(portfolio.get('total_eval', 0))

    row = {
        'total_krw': krw_balance,
        'total_crypto_value': crypto_value,
        'total_value': total_value,
        'holdings': json.dumps(holdings, ensure_ascii=False),
        'cycle_id': '${CYCLE_ID}',
    }
    if machine_name:
        row['machine_name'] = machine_name

    resp = requests.post(
        f'{supabase_url}/rest/v1/portfolio_snapshots',
        json=row, headers=headers, timeout=10,
    )
    if resp.status_code in (200, 201):
        print('[Agent] portfolio_snapshots 기록 완료', file=sys.stderr)
    else:
        print(f'[Agent] portfolio_snapshots 기록 실패: HTTP {resp.status_code}: {resp.text[:200]}', file=sys.stderr)
except Exception as e:
    print(f'[Agent] portfolio_snapshots 기록 예외: {e}', file=sys.stderr)
" 2>&1 || true
fi

# ── Phase 6: 과거 전환 성과 평가 (학습 데이터 축적) ──
echo "[$(date)] Phase 6: 전환 성과 평가..." >&2
"$PYTHON" scripts/evaluate_switches.py 2>&1 || true

echo "[$(date)] ═══ 에이전트 모드 완료 ═══" >&2
echo "$AGENT_RESULT"
