#!/usr/bin/env python3
"""
AI 단타 트레이딩 봇

3가지 전략을 실시간으로 동시 운영한다:
  1. 뉴스 반응 단타 (News Reaction) -- 뉴스 감성 급변 시 선제 매매
  2. 급등/급락 리바운드 단타 (Spike Rebound) -- 급변동 후 되돌림 포착
  3. 고래 추종 단타 (Whale Following) -- 대량 체결 방향 추종

실행:
  python3 scripts/short_term_trader.py              # 실매매 (.env DRY_RUN 따름)
  python3 scripts/short_term_trader.py --dry-run     # 시뮬레이션만
  python3 scripts/short_term_trader.py --status       # 현재 상태 출력 후 종료

안전장치:
  - DRY_RUN / EMERGENCY_STOP 준수
  - 단타 전용 자금 한도 (SHORT_TERM_BUDGET)
  - 1회 매매 상한, 일일 매매 횟수 상한
  - 포지션별 자동 손절/익절/시간제한
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import signal
import sys
import time
import uuid
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from dotenv import load_dotenv
import jwt
import requests

try:
    import websockets
except ImportError:
    print("websockets 패키지 필요: pip install websockets", file=sys.stderr)
    sys.exit(1)

# ── 환경 설정 ──────────────────────────────────────────

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
from core.db import db

LOG_DIR = PROJECT_DIR / "logs" / "short_term"
LOG_DIR.mkdir(parents=True, exist_ok=True)

KST = timezone(timedelta(hours=9))
MARKET = "KRW-BTC"
UPBIT_API = "https://api.upbit.com/v1"
UPBIT_WS = "wss://api.upbit.com/websocket/v1"

# ── 단타 전용 파라미터 (공격적 모드) ──────────────────────
# AutoLearner 연동: data/auto_learner_params.json이 있으면 우선 사용

def _auto_param(key: str, default, cast=float):
    """AutoLearner 파라미터 우선, 환경변수 폴백"""
    _auto_params_cache = getattr(_auto_param, "_cache", None)
    if _auto_params_cache is None:
        _ap = Path(__file__).resolve().parent.parent / "data" / "auto_learner_params.json"
        try:
            if _ap.exists():
                import json as _json
                with open(_ap) as _f:
                    _auto_params_cache = _json.load(_f)
                logging.getLogger("short_term").info(f"[AutoLearner] 파라미터 로드: {_ap.name}")
            else:
                _auto_params_cache = {}
        except Exception:
            _auto_params_cache = {}
        _auto_param._cache = _auto_params_cache

    if key in _auto_params_cache:
        return cast(_auto_params_cache[key])
    return cast(os.getenv(key, str(default)))


SHORT_TERM_BUDGET = int(os.getenv("SHORT_TERM_BUDGET", "1000000"))
SHORT_TERM_MAX_TRADE = int(os.getenv("SHORT_TERM_MAX_TRADE", "300000"))
SHORT_TERM_MAX_DAILY = int(os.getenv("SHORT_TERM_MAX_DAILY", "20"))
SHORT_TERM_MAX_DAILY_DRYRUN = int(os.getenv("SHORT_TERM_MAX_DAILY_DRYRUN", "40"))
# v8: 실제 스캘핑에 맞는 현실적 손절/익절 (기존 25%/30%는 무손절과 동일)
SHORT_TERM_STOP_LOSS = _auto_param("SHORT_TERM_STOP_LOSS", 0.4)    # 0.4% 손절
SHORT_TERM_TAKE_PROFIT = _auto_param("SHORT_TERM_TAKE_PROFIT", 0.6)  # 0.6% 익절 (R:R 1:1.5)
SHORT_TERM_MAX_HOLD_MIN = _auto_param("SHORT_TERM_MAX_HOLD_MIN", 15, int)
COMMISSION_PCT = 0.05
MIN_PROFIT_AFTER_FEE = COMMISSION_PCT * 2 + 0.05

# 뉴스 스캔 간격
NEWS_SCAN_INTERVAL = 120

# 급등/급락 감지 기준 — v8: 적응형 spike threshold (ATR 기반)
SPIKE_THRESHOLD_PCT = _auto_param("SPIKE_THRESHOLD_PCT", 0.8)  # 폴백 기본값
SPIKE_THRESHOLD_MIN = 0.5   # ATR 적응 최소값
SPIKE_THRESHOLD_MAX = 1.0   # ATR 적응 최대값
SPIKE_ATR_MULTIPLIER = 0.6  # ATR × 0.6 = spike threshold
SPIKE_WINDOW_SEC = 300

# 고래 감지 기준 — v8: BTC 수량 기반 (가격 변동에 무관하게 일관된 감지)
WHALE_THRESHOLD_KRW = _auto_param("WHALE_THRESHOLD_KRW", 200_000_000)  # 폴백
WHALE_THRESHOLD_BTC = _auto_param("WHALE_THRESHOLD_BTC", 5.0)  # 5 BTC 기준
WHALE_RATIO_THRESHOLD = _auto_param("WHALE_RATIO_THRESHOLD", 0.85)
WHALE_RATIO_WINDOW_SEC = 180

# 매도 압력 방패
SELL_PRESSURE_BLOCK_RATIO = _auto_param("SELL_PRESSURE_BLOCK_RATIO", 4.0)

# v5: 진입 보호 기간
GRACE_PERIOD_SEC = 180

# v5: 트레일링 스탑 설정
TRAILING_STOP_ACTIVATE_PCT = _auto_param("TRAILING_STOP_ACTIVATE_PCT", 0.25)
TRAILING_STOP_DISTANCE_PCT = _auto_param("TRAILING_STOP_DISTANCE_PCT", 0.15)

# v5: 모멘텀 확인
MOMENTUM_WINDOW_SEC = 60
MOMENTUM_MIN_PCT = _auto_param("MOMENTUM_MIN_PCT", 0.06)

# ── v4 안전 필터 ─────────────────────────
TREND_SMA_CANDLE_COUNT = 20
NEWS_BLOCK_THRESHOLD = _auto_param("NEWS_BLOCK_THRESHOLD", -0.5)
# v8: FGI 극공포 기준 상향 (5→15) + 하락장 매수 편향 제거
FGI_BLOCK_THRESHOLD = 15
# v8: 연속 음봉 매수 차단 (3일 연속 하락 시 신규 매수 차단)
CONSECUTIVE_RED_CANDLE_BLOCK = 3
# v8: 하락장 매수 제한 (SMA 하향 + FGI < 25 → 매수 2회/일)
BEAR_MARKET_MAX_DAILY_BUYS = 2

# ── v9: 레짐 기반 필터 강도 조절 ─────────────────────
# 상승장에서 필터를 완화하여 기회를 놓치지 않도록 한다.
# 하락장에서 필터를 강화하여 구조적 손실을 방지한다.
# 레짐: bull(상승), bear(하락), sideways(횡보), crisis(급락)
REGIME_FILTER_INTENSITY = {
    "bull": {
        "fgi_block": 5,            # 극공포만 차단 (15→5)
        "red_candle_block": 5,     # 5연속 이상만 차단 (3→5)
        "bear_max_daily": 10,      # 사실상 무제한 (2→10)
        "sma_filter": False,       # SMA 필터 비활성
        "macro_penalty": 0,        # 매크로 감산 없음
        "momentum_min": 0.03,      # 모멘텀 완화 (0.06→0.03)
        "buy_score_bonus": 0,      # v5.1: 매수 점수 가산 없음
        "tp_multiplier": 1.5,      # v5.1: 익절 확대 (let winners run)
        "sl_multiplier": 1.0,      # v5.1: 손절 기본
    },
    "early_bull": {
        "fgi_block": 8,            # v5.1: bull 진입 전 완화
        "red_candle_block": 4,     # bull보다 약간 엄격
        "bear_max_daily": 8,       # 넉넉하게
        "sma_filter": False,       # SMA 필터 비활성
        "macro_penalty": 0,        # 매크로 감산 없음
        "momentum_min": 0.04,      # 약간 완화
        "buy_score_bonus": 0,      # v5.1: 가산 없음
        "tp_multiplier": 1.3,      # v5.1: 익절 약간 확대
        "sl_multiplier": 1.0,      # v5.1: 손절 기본
    },
    "sideways": {
        "fgi_block": 10,           # 중간 (15→10)
        "red_candle_block": 3,     # 기본값 유지
        "bear_max_daily": 5,       # 약간 완화 (2→5)
        "sma_filter": True,        # SMA 필터 활성
        "macro_penalty": -5,       # 약한 감산
        "momentum_min": 0.06,      # 기본값
        "buy_score_bonus": 5,      # v5.1: 과매매 억제 +5
        "tp_multiplier": 1.0,      # v5.1: 익절 기본
        "sl_multiplier": 1.0,      # v5.1: 손절 기본
    },
    "bear": {
        "fgi_block": 15,           # 강한 차단
        "red_candle_block": 3,     # 기본값
        "bear_max_daily": 2,       # 강한 제한
        "sma_filter": True,        # SMA 필터 활성
        "macro_penalty": -15,      # 강한 감산
        "momentum_min": 0.08,      # 모멘텀 강화 (0.06→0.08)
        "buy_score_bonus": 10,     # v5.1: 과매매 강한 억제 +10
        "tp_multiplier": 1.0,      # v5.1: 익절 기본
        "sl_multiplier": 0.7,      # v5.1: 손절 강화 (빠른 탈출)
    },
    "crisis": {
        "fgi_block": 20,           # 가장 강한 차단
        "red_candle_block": 2,     # 2연속도 차단
        "bear_max_daily": 1,       # 거의 차단
        "sma_filter": True,        # SMA 필터 활성
        "macro_penalty": -20,      # 최대 감산
        "momentum_min": 0.10,      # 매우 강한 모멘텀 요구
        "buy_score_bonus": 15,     # v5.1: 과매매 최강 억제 +15
        "tp_multiplier": 1.0,      # v5.1: 익절 기본
        "sl_multiplier": 0.7,      # v5.1: 손절 강화 (빠른 탈출)
    },
}
EARLY_STOP_LOSS_PCT = _auto_param("EARLY_STOP_LOSS_PCT", 0.15)
EARLY_STOP_TIME_MIN = _auto_param("EARLY_STOP_TIME_MIN", 5, int)
# 5. 중복 진입 방지: 같은 전략으로 동시 1포지션만 (v5: 2→1, 집중)
MAX_SAME_STRATEGY_POSITIONS = 1

# ── 오케스트레이터 연동: 감독의 시장 판단 읽기 ──────────────
_AGENT_STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "agent_state.json"
_orch_cache: dict = {"data": None, "ts": 0.0}
_ORCH_CACHE_TTL = 60  # 60초 캐시 — 파일 I/O로 타이밍 놓치지 않도록


def _read_orchestrator_state() -> dict:
    """agent_state.json에서 감독의 danger_score/opportunity_score/regime을 읽는다.
    60초 캐시로 반복 I/O 방지."""
    import time as _t
    now = _t.time()
    if _orch_cache["data"] is not None and (now - _orch_cache["ts"]) < _ORCH_CACHE_TTL:
        return _orch_cache["data"]
    try:
        with open(_AGENT_STATE_PATH, "r", encoding="utf-8") as f:
            state = json.loads(f.read())
        result = {
            "active_agent": state.get("active_agent", "moderate"),
            "danger_score": state.get("danger_score", 0) or 0,
            "opportunity_score": state.get("opportunity_score", 0) or 0,
            "regime": state.get("regime", "sideways"),
        }
    except (FileNotFoundError, json.JSONDecodeError):
        result = {"active_agent": "moderate", "danger_score": 0, "opportunity_score": 0, "regime": "sideways"}
    _orch_cache["data"] = result
    _orch_cache["ts"] = now
    return result


def _orchestrator_trade_multiplier() -> float:
    """감독의 판단에 따른 단타 매수 금액 스케일링 배수.

    - danger ≥ 70 (보수적 구간): 매수 차단 (0.0)
    - danger 50~69: 50% 축소 (0.5)
    - danger 30~49: 70% (0.7)
    - danger < 30 + opportunity ≥ 60: 확대 (1.5)
    - 기본: 1.0
    - conservative 에이전트 활성: 매수 차단 (0.0)
    """
    orch = _read_orchestrator_state()
    danger = orch["danger_score"]
    opportunity = orch["opportunity_score"]
    agent = orch["active_agent"]

    # 보수적 에이전트가 활성이면 단타도 차단
    if agent == "conservative":
        return 0.0

    if danger >= 70:
        return 0.0
    elif danger >= 50:
        return 0.5
    elif danger >= 30:
        return 0.7
    elif danger < 30 and opportunity >= 60:
        return 1.5
    return 1.0


# ── Kelly Criterion 단타용 포지션 사이징 ──────────────────

def _kelly_short_term(confidence: float) -> int:
    """단타 시그널의 confidence로 SHORT_TERM_MAX_TRADE를 스케일링한다.

    strategy.md 테이블 준수 (Half-Kelly):
      ≥0.85 → 100%, 0.70~0.84 → 70%, 0.55~0.69 → 50%, <0.55 → 30%

    감독 연동: 오케스트레이터의 danger/opportunity에 따라 추가 스케일링.

    Returns:
        스케일링된 최대 매매 금액
    """
    if confidence >= 0.85:
        frac = 1.0
    elif confidence >= 0.70:
        frac = 0.7
    elif confidence >= 0.55:
        frac = 0.5
    else:
        frac = 0.3

    # 감독 연동 배수 적용
    orch_mult = _orchestrator_trade_multiplier()
    amount = int(SHORT_TERM_MAX_TRADE * frac * orch_mult)
    return max(5000, amount) if orch_mult > 0 else 0  # 차단 시 0 반환


# ── 로깅 설정 ──────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            LOG_DIR / f"trader_{datetime.now(KST).strftime('%Y%m%d')}.log",
            encoding="utf-8",
        ),
    ],
)
log = logging.getLogger("short_term")


# ── 데이터 구조 ────────────────────────────────────────

@dataclass
class Position:
    strategy: str  # news / spike / whale
    side: str  # bid (롱)
    entry_price: float
    amount_krw: float
    btc_qty: float
    entry_time: datetime
    stop_loss_pct: float = SHORT_TERM_STOP_LOSS
    take_profit_pct: float = SHORT_TERM_TAKE_PROFIT
    max_hold_min: int = SHORT_TERM_MAX_HOLD_MIN
    exit_price: float | None = None
    exit_time: datetime | None = None
    exit_reason: str | None = None
    pnl_pct: float | None = None
    # v5: 트레일링 스탑
    trailing_stop_active: bool = False
    highest_pnl_pct: float = 0.0  # 보유 중 최고 수익률 (수수료 후)


@dataclass
class TradeSignal:
    strategy: str
    action: str  # buy / sell
    confidence: float  # 0.0 ~ 1.0
    reason: str
    suggested_amount: int = SHORT_TERM_MAX_TRADE
    timestamp: datetime = field(default_factory=lambda: datetime.now(KST))


# ── Upbit API ──────────────────────────────────────────

def upbit_auth_header(query_string: str) -> dict:
    payload = {
        "access_key": os.environ["UPBIT_ACCESS_KEY"],
        "nonce": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
        "query_hash": hashlib.sha512(query_string.encode()).hexdigest(),
        "query_hash_alg": "SHA512",
    }
    token = jwt.encode(payload, os.environ["UPBIT_SECRET_KEY"], algorithm="HS256")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def upbit_order(side: str, market: str, amount: str) -> dict:
    """시장가 주문 실행"""
    body = {"market": market, "side": side}
    if side == "bid":
        body["ord_type"] = "price"
        body["price"] = amount
    else:
        body["ord_type"] = "market"
        body["volume"] = amount

    qs = urlencode(body)
    headers = upbit_auth_header(qs)
    r = _get_http_session().post(f"{UPBIT_API}/orders", json=body, headers=headers, timeout=10)
    try:
        data = r.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        data = {"error": {"name": "parse_error", "message": r.text[:200]}}
    return {"ok": r.ok, "data": data}


# ── 커넥션 재사용을 위한 HTTP 세션 ──────────────────────
_http_session: requests.Session | None = None


def _get_http_session() -> requests.Session:
    """모듈 레벨 requests.Session을 반환한다 (커넥션 풀 재사용)."""
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
        _http_session.headers.update({"Accept": "application/json"})
    return _http_session


def get_current_price(market: str = MARKET) -> float:
    r = _get_http_session().get(f"{UPBIT_API}/ticker", params={"markets": market}, timeout=5)
    return r.json()[0]["trade_price"]


def sound_alert(message: str, urgent: bool = False):
    """음성 알림 비활성화됨 (2026-03-08)"""
    return


# ── DB 기록 (core.db 어댑터) ────────────────────────────

def db_insert(table: str, data: dict):
    """core.db 어댑터로 데이터 삽입 + decisions이면 임베딩 자동 생성"""
    _log = logging.getLogger("short_term")
    from utils.machine import skip_trade_db, get_machine_name
    if skip_trade_db(table):
        _backup_to_local(table, data)
        return
    # 머신 태그 자동 추가 (중복 방지 + 머신별 성과 비교)
    data.setdefault("machine_name", get_machine_name())
    try:
        try:
            row = db.insert(table, data, returning=(table == "decisions"))
        except Exception as ie:
            # machine_name 컬럼 미존재 등 스키마 불일치 — 제거 후 재시도
            if "machine_name" in str(ie):
                data.pop("machine_name", None)
                row = db.insert(table, data, returning=(table == "decisions"))
            else:
                raise
        if table == "decisions":
            # 임베딩 자동 생성
            try:
                decision_id = row["id"] if row else None
                if decision_id:
                    _generate_and_save_embedding(decision_id, data, _log)
            except Exception as emb_err:
                _log.warning(f"[DB] 임베딩 생성 실패 (봇 영향 없음): {emb_err}")
        # 로컬 백업 — 모든 중요 테이블 (DB 실패해도 기록 유지)
        _backup_to_local(table, data)
    except Exception as e:
        _log.warning(f"[DB] {table} 예외: {e}")
        _backup_to_local(table, data)


def _generate_and_save_embedding(decision_id: str, data: dict, _log):
    """decisions 저장 후 Gemini 임베딩을 생성하여 Management API로 업데이트."""
    try:
        from scripts.save_decision import generate_state_embedding
        from scripts.save_decision import _update_embedding_via_sql

        emb_data = {
            "current_price": data.get("current_price"),
            "rsi_14": data.get("rsi_value"),
            "fear_greed_value": data.get("fear_greed_value"),
            "sma_20": data.get("sma20_price"),
        }
        emb_text, emb_vector = generate_state_embedding(emb_data)
        if emb_text and emb_vector:
            _update_embedding_via_sql(decision_id, emb_vector, emb_text)
    except Exception as e:
        _log.warning(f"[DB] 임베딩 저장 실패: {e}")


def _backup_to_local(table: str, data: dict):
    """DB 기록의 로컬 JSON 백업 (v4)"""
    try:
        backup_dir = PROJECT_DIR / "data" / "db_backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / f"{table}_{datetime.now(KST).strftime('%Y%m%d')}.jsonl"
        with open(backup_file, "a", encoding="utf-8") as f:
            import json as _json
            f.write(_json.dumps(data, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def send_telegram(message: str):
    """텔레그램 알림 (간단 버전)"""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_USER_ID", "")
    if not token or not chat_id:
        return
    try:
        from utils.machine import get_machine_name
        tag = f"[{get_machine_name()}]"
    except Exception:
        import platform
        tag = f"[{platform.node().split('.')[0]}]"
    try:
        _get_http_session().post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": f"{message}\n{tag}", "parse_mode": "HTML"},
            timeout=5,
        )
    except Exception:
        pass


# ── 락파일 (정규 매매와 동시 실행 방지) ──────────────────

LOCK_FILE = PROJECT_DIR / "data" / "trading.lock"

def check_lock() -> bool:
    """정규 매매가 실행 중인지 확인. True면 안전, False면 충돌 위험."""
    if not LOCK_FILE.exists():
        return True
    try:
        lock_data = json.loads(LOCK_FILE.read_text())
        lock_time = datetime.fromisoformat(lock_data.get("timestamp", ""))
        age = (datetime.now(KST) - lock_time).total_seconds()
        lock_pid = lock_data.get("pid", 0)
        # PID 생존 확인
        pid_alive = False
        if lock_pid > 0:
            try:
                if os.name == "nt":
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    handle = kernel32.OpenProcess(0x100000, False, lock_pid)
                    if handle:
                        kernel32.CloseHandle(handle)
                        pid_alive = True
                else:
                    os.kill(lock_pid, 0)
                    pid_alive = True
            except (OSError, ProcessLookupError):
                pid_alive = False
        # 10분 이상이거나 프로세스 사망 시 stale
        if age > 600 or (lock_pid > 0 and not pid_alive):
            log.warning(f"stale 락파일 제거 (age={age:.0f}s, pid={lock_pid}, alive={pid_alive})")
            LOCK_FILE.unlink(missing_ok=True)
            return True
        log.warning(f"정규 매매 실행 중: {lock_data.get('process', 'unknown')} (pid={lock_pid})")
        return False
    except Exception:
        return True

def acquire_lock(owner="short_term"):
    """락파일 생성 (atomic exclusive create)"""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, 'w') as f:
            json.dump({"process": owner, "pid": os.getpid(), "timestamp": datetime.now(KST).isoformat()}, f)
        return True
    except FileExistsError:
        return False

def release_lock():
    """락파일 해제"""
    try:
        if LOCK_FILE.exists():
            lock_data = json.loads(LOCK_FILE.read_text())
            if lock_data.get("pid") == os.getpid():
                LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass


# ── 메인 트레이더 클래스 ───────────────────────────────

class ShortTermTrader:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.running = True
        # cycle_id: 이 세션의 모든 DB 기록을 연결하는 키
        try:
            sys.path.insert(0, str(PROJECT_DIR))
            from scripts.cycle_id import make_cycle_id
            self.cycle_id = make_cycle_id("scalp")
        except Exception:
            self.cycle_id = datetime.now(KST).strftime("%Y%m%d-%H%M") + "-scalp"
        self.current_price: float = 0
        self.positions: list[Position] = []
        self.closed_positions: list[Position] = []
        self.total_closed_count: int = 0  # 전체 청산 수 (closed_positions 트리밍 후에도 정확)
        self.daily_trade_count = 0
        self.daily_pnl = 0.0
        self._current_date = datetime.now(KST).date()
        self.used_budget = 0

        # 에러 카운터 -- 연속 에러 시 자동 정지
        self.consecutive_errors = 0
        self.MAX_CONSECUTIVE_ERRORS = 5
        self.emergency_stopped = False

        # 실시간 데이터 버퍼
        self.price_history: deque = deque(maxlen=600)  # 10분 (1초 간격)
        self.trade_history: deque = deque(maxlen=500)  # 최근 500건 체결
        self.last_news_scan: float = 0
        self.last_news_sentiment: str = "neutral"
        self.news_sentiment_score: float = 0  # -1.0 ~ +1.0

        # 고래 감지 버퍼
        self.whale_recent: deque = deque(maxlen=20)

        # v4: 시장 컨텍스트 캐시
        self._market_trend: str = "unknown"  # uptrend / downtrend / sideways
        self._sma20: float = 0
        self._rsi: float = 50
        self._fgi: int = 50
        self._last_context_update: float = 0
        self._trade_counter: int = 0  # 세션 내 거래 번호
        self._last_snapshot_time: float = 0

        # 뉴스랑(NewsRang) 시그널 캐시
        self._newsrang: dict = {}
        self._newsrang_update: float = 0

        # v8: 적응형 파라미터
        self._adaptive_spike_threshold: float = SPIKE_THRESHOLD_PCT
        self._adaptive_max_hold: int = SHORT_TERM_MAX_HOLD_MIN
        self._atr_1h: float = 0.0  # 1시간 ATR (%)
        self._atr_24h: float = 0.0  # 24시간 ATR (%)
        self._consecutive_red_candles: int = 0  # 연속 음봉 수
        self._daily_buy_count: int = 0  # 당일 매수 횟수 (하락장 제한용)
        self._whale_threshold_dynamic: float = WHALE_THRESHOLD_KRW  # 동적 고래 기준

        # v9: 레짐 기반 필터 강도
        self._market_regime: str = "sideways"  # bull / early_bull / bear / sideways / crisis
        self._regime_filters: dict = REGIME_FILTER_INTENSITY["sideways"]
        self._change_24h: float = 0.0  # v5.1: 24시간 변동률 (%)

        # 로그 노이즈 방지
        self._last_block_reason: set = set()

    def update_market_context(self):
        """5분마다 SMA20, RSI, FGI를 갱신하여 추세 판단 (v4)"""
        now = time.time()
        if now - self._last_context_update < 300:  # 5분 캐시
            return
        self._last_context_update = now

        try:
            # SMA20 from 일봉
            _sess = _get_http_session()
            r = _sess.get(
                f"{UPBIT_API}/candles/days",
                params={"market": MARKET, "count": TREND_SMA_CANDLE_COUNT},
                timeout=5,
            )
            if r.ok:
                candles = r.json()
                closes = [c["trade_price"] for c in candles]
                self._sma20 = sum(closes) / len(closes) if closes else 0
                if self.current_price > self._sma20 * 1.005:
                    self._market_trend = "uptrend"
                elif self.current_price < self._sma20 * 0.995:
                    self._market_trend = "downtrend"
                else:
                    self._market_trend = "sideways"

            # v5.1: 24h 변동률 (ticker API)
            try:
                rt = requests.get(
                    f"{UPBIT_API}/ticker", params={"markets": MARKET}, timeout=5
                )
                if rt.ok:
                    ticker = rt.json()[0]
                    self._change_24h = ticker.get("signed_change_rate", 0) * 100
            except Exception:
                pass

            # RSI from 시장 데이터 수집 스크립트 (간이 계산)
            r2 = _sess.get(
                f"{UPBIT_API}/candles/minutes/60",
                params={"market": MARKET, "count": 15},
                timeout=5,
            )
            if r2.ok:
                candles_1h = r2.json()
                closes_1h = [c["trade_price"] for c in reversed(candles_1h)]
                gains, losses = [], []
                for i in range(1, len(closes_1h)):
                    diff = closes_1h[i] - closes_1h[i - 1]
                    if diff > 0:
                        gains.append(diff)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(diff))
                if gains:
                    avg_gain = sum(gains) / len(gains)
                    avg_loss = sum(losses) / len(losses)
                    if avg_loss > 0:
                        rs = avg_gain / avg_loss
                        self._rsi = 100 - (100 / (1 + rs))
                    else:
                        self._rsi = 100

            # FGI
            try:
                r3 = _sess.get(
                    "https://api.alternative.me/fng/?limit=1", timeout=5
                )
                if r3.ok:
                    self._fgi = int(r3.json()["data"][0]["value"])
            except Exception:
                pass

            # v8: ATR 계산 + 적응형 파라미터 업데이트
            try:
                r_4h = requests.get(
                    f"{UPBIT_API}/candles/minutes/60",
                    params={"market": MARKET, "count": 25},
                    timeout=5,
                )
                if r_4h.ok:
                    candles_1h = r_4h.json()
                    if len(candles_1h) >= 2:
                        # ATR 계산 (1h 캔들 기준)
                        atr_vals = []
                        for c in candles_1h:
                            tr = (c["high_price"] - c["low_price"]) / c["low_price"] * 100
                            atr_vals.append(tr)
                        self._atr_1h = sum(atr_vals) / len(atr_vals) if atr_vals else 1.0
                        # 24h ATR = 최근 24개 1h 캔들의 평균
                        recent_24 = atr_vals[:24]
                        self._atr_24h = sum(recent_24) / len(recent_24) if recent_24 else 1.0

                        # 적응형 spike threshold: ATR × 0.6, 범위 [0.5, 1.0]
                        self._adaptive_spike_threshold = max(
                            SPIKE_THRESHOLD_MIN,
                            min(SPIKE_THRESHOLD_MAX, self._atr_24h * SPIKE_ATR_MULTIPLIER)
                        )

                        # 적응형 max_hold: 고변동→10분, 저변동→20분
                        if self._atr_1h > 1.5:
                            self._adaptive_max_hold = 10
                        elif self._atr_1h > 0.8:
                            self._adaptive_max_hold = 15
                        else:
                            self._adaptive_max_hold = 20

                        # 연속 음봉 계산 (1h 캔들 기준)
                        red_count = 0
                        for c in candles_1h:
                            if c["trade_price"] < c["opening_price"]:
                                red_count += 1
                            else:
                                break
                        self._consecutive_red_candles = red_count

                        # 동적 고래 기준: BTC 수량 기반
                        if self.current_price > 0:
                            self._whale_threshold_dynamic = WHALE_THRESHOLD_BTC * self.current_price

                        # v5.1: 레짐 판별 (Bull 조기 감지 + early_bull + 모멘텀)
                        old_regime = self._market_regime
                        sma_dev = ((self.current_price - self._sma20) / self._sma20 * 100) if self._sma20 > 0 else 0

                        # 1) bull: SMA 상향 + FGI 30 이상 (v5의 40→30 완화)
                        if self._market_trend == "uptrend" and self._fgi >= 30:
                            self._market_regime = "bull"
                        # 2) bull 모멘텀 대안: SMA 근접 상향 + 24h +2%
                        elif sma_dev > 0.3 and self._change_24h >= 2.0:
                            self._market_regime = "bull"
                        # 3) early_bull: SMA 전환 초기 + FGI 25+ + 하락 아님
                        elif sma_dev > 0 and self._fgi >= 25 and self._change_24h >= 0:
                            self._market_regime = "early_bull"
                        elif (self._market_trend == "downtrend" and self._fgi <= 20
                              and self._atr_1h > 2.0):
                            self._market_regime = "crisis"
                        elif self._market_trend == "downtrend" and self._fgi <= 35:
                            self._market_regime = "bear"
                        else:
                            self._market_regime = "sideways"

                        self._regime_filters = REGIME_FILTER_INTENSITY.get(
                            self._market_regime, REGIME_FILTER_INTENSITY["sideways"]
                        )

                        if old_regime != self._market_regime:
                            log.info(
                                f"[v9 레짐 전환] {old_regime} → {self._market_regime} "
                                f"(FGI={self._fgi}, trend={self._market_trend}, ATR={self._atr_1h:.2f}%)"
                            )

                        log.debug(
                            f"[v8 적응형] ATR_1h={self._atr_1h:.3f}% ATR_24h={self._atr_24h:.3f}% "
                            f"spike={self._adaptive_spike_threshold:.3f}% hold={self._adaptive_max_hold}min "
                            f"red_candles={self._consecutive_red_candles} "
                            f"whale={self._whale_threshold_dynamic/1e8:.1f}억 "
                            f"regime={self._market_regime}"
                        )
            except Exception as e:
                log.debug(f"ATR/적응형 업데이트 실패: {e}")

        except Exception as e:
            log.debug(f"시장 컨텍스트 업데이트 실패: {e}")

        # 뉴스랑(NewsRang) 시그널 업데이트
        try:
            from utils.newsrang_reader import get_newsrang_signal
            self._newsrang = get_newsrang_signal()
            self._newsrang_update = now
            nr = self._newsrang
            if nr.get("fresh") and nr.get("source") != "empty":
                log.info(
                    f"뉴스랑 시그널: score={nr['score']}, RSS={nr['rss']}, "
                    f"X={nr['x']}, 소셜={nr['social']}, "
                    f"signal={nr['signal']}, age={nr['age_min']:.0f}min"
                )
        except Exception as e:
            log.debug(f"뉴스랑 업데이트 실패: {e}")

    def record_market_snapshot(self):
        """5분마다 시장 스냅샷을 DB에 기록 (ML 학습용)"""
        try:
            # 체결 강도 계산 (최근 60초)
            now_t = time.time()
            cutoff_60s = now_t - 60
            recent_trades = [t for t in self.trade_history if t["time"] > cutoff_60s]
            buy_vol = sum(t["volume"] for t in recent_trades if t["side"] == "BID")
            sell_vol = sum(t["volume"] for t in recent_trades if t["side"] == "ASK")
            total_vol = buy_vol + sell_vol
            pressure_ratio = round(buy_vol / total_vol, 3) if total_vol > 0 else 0.5

            # 고래 통계 (최근 3분)
            cutoff_whale = now_t - 180
            recent_whales = [w for w in self.whale_recent if w["time"] > cutoff_whale]
            whale_buys = [w for w in recent_whales if w["side"] == "BID"]
            whale_sells = [w for w in recent_whales if w["side"] == "ASK"]
            whale_buy_krw = sum(int(w["krw"]) for w in whale_buys)
            whale_sell_krw = sum(int(w["krw"]) for w in whale_sells)
            whale_total = whale_buy_krw + whale_sell_krw
            whale_buy_ratio = round(whale_buy_krw / whale_total, 3) if whale_total > 0 else 0.5

            # 모멘텀 계산
            def calc_momentum(seconds):
                cutoff = now_t - seconds
                window = [p["price"] for p in self.price_history if p["time"] > cutoff]
                if len(window) >= 2:
                    return round((window[-1] - window[0]) / window[0] * 100, 3)
                return None

            # 변동성 (5분 가격 표준편차/평균 * 100)
            cutoff_5m = now_t - 300
            prices_5m = [p["price"] for p in self.price_history if p["time"] > cutoff_5m]
            volatility_5m = None
            if len(prices_5m) >= 10:
                import statistics
                mean_p = statistics.mean(prices_5m)
                std_p = statistics.stdev(prices_5m)
                volatility_5m = round(std_p / mean_p * 100, 3)

            snapshot = {
                "cycle_id": self.cycle_id,
                "btc_price": int(self.current_price),
                "rsi_1h": round(self._rsi, 2),
                "sma20": int(self._sma20) if self._sma20 else None,
                "market_trend": self._market_trend,
                "fgi": self._fgi,
                "news_sentiment": self.last_news_sentiment,
                "news_score": round(self.news_sentiment_score, 2),
                "whale_buy_count": len(whale_buys),
                "whale_sell_count": len(whale_sells),
                "whale_buy_krw": whale_buy_krw,
                "whale_sell_krw": whale_sell_krw,
                "whale_buy_ratio": whale_buy_ratio,
                "trade_buy_volume": round(buy_vol, 8),
                "trade_sell_volume": round(sell_vol, 8),
                "trade_pressure_ratio": pressure_ratio,
                "momentum_1m_pct": calc_momentum(60),
                "momentum_5m_pct": calc_momentum(300),
                "momentum_15m_pct": calc_momentum(900),
                "volatility_5m": volatility_5m,
                "open_positions": len(self.positions),
                "daily_trade_count": self.daily_trade_count,
                "daily_pnl_krw": int(self.daily_pnl),
            }
            db_insert("scalp_market_snapshot", snapshot)
        except Exception as e:
            log.debug(f"시장 스냅샷 기록 실패: {e}")

    def check_safety_filters(self, signal: "TradeSignal") -> tuple[bool, str]:
        """v4 안전 필터: 5가지 바보짓 방지. 통과 못하면 (False, 사유) 반환"""
        if signal.action != "buy":
            return True, "OK"

        # v5.1: 레짐별 과매매 억제 (confidence 최소 기준 가산)
        rf = self._regime_filters
        bonus = rf.get("buy_score_bonus", 0)
        if bonus > 0:
            # bonus를 confidence로 환산: +5 → +0.05, +10 → +0.10, +15 → +0.15
            min_confidence = 0.55 + bonus * 0.01
            if signal.confidence < min_confidence:
                return False, (
                    f"v5.1 과매매 억제: confidence {signal.confidence:.2f} < "
                    f"{min_confidence:.2f} (regime={self._market_regime}, +{bonus})"
                )

        # 필터 1: 하락 추세에서 whale 매수 차단
        if signal.strategy == "whale" and self._market_trend == "downtrend":
            return False, f"하락추세(SMA20 {self._sma20:,.0f} > 현재가) whale 매수 차단"

        # 필터 2: 뉴스 negative일 때 매수 차단
        if self.news_sentiment_score <= NEWS_BLOCK_THRESHOLD:
            return False, f"뉴스 부정적(score {self.news_sentiment_score:+.2f}) 매수 차단"

        # v9: 레짐별 필터 강도 적용
        rf = self._regime_filters

        # 필터 3: 극공포 FGI 차단 (레짐별 기준)
        fgi_block = rf.get("fgi_block", FGI_BLOCK_THRESHOLD)
        if self._fgi <= fgi_block:
            return False, f"극공포(FGI {self._fgi} ≤ {fgi_block}, regime={self._market_regime}) 매수 차단"

        # v8 필터 8: 연속 음봉 매수 차단 (레짐별 기준)
        red_block = rf.get("red_candle_block", CONSECUTIVE_RED_CANDLE_BLOCK)
        if self._consecutive_red_candles >= red_block:
            return False, f"연속 음봉 {self._consecutive_red_candles}개 ≥ {red_block} (regime={self._market_regime}) — 매수 차단"

        # v8 필터 9: 하락장 매수 제한 (레짐별 기준)
        bear_max = rf.get("bear_max_daily", BEAR_MARKET_MAX_DAILY_BUYS)
        if (self._market_trend == "downtrend" and self._fgi < 25
                and self._daily_buy_count >= bear_max):
            return False, f"하락장 매수 제한 (FGI {self._fgi}, 매수 {self._daily_buy_count}/{bear_max}, regime={self._market_regime})"

        # v8 필터 10: SMA 하향 돌파 (레짐에 따라 비활성화 가능)
        if rf.get("sma_filter", True):
            if self.current_price < self._sma20 * 0.99 and self._market_trend == "downtrend":
                if signal.confidence < 0.7:
                    return False, f"SMA 하향 돌파({self.current_price:,.0f} < SMA×0.99) + 낮은 신뢰도 — 매수 차단 (regime={self._market_regime})"

        # 필터 4: 같은 전략 중복 진입 방지
        same_strategy_count = sum(
            1 for p in self.positions if p.strategy == signal.strategy
        )
        if same_strategy_count >= MAX_SAME_STRATEGY_POSITIONS:
            return False, f"{signal.strategy} 중복 진입 차단 (이미 {same_strategy_count}건)"

        # 필터 5: 하락 추세 + RSI 과매도 접근 시 전체 매수 차단
        if self._market_trend == "downtrend" and self._rsi < 35:
            return False, f"하락추세 + RSI {self._rsi:.0f} 과매도 접근 -- 매수 차단"

        # 필터 6: 뉴스랑 강한 약세 시 매수 차단 (전쟁/대형 악재)
        nr = self._newsrang
        if nr and nr.get("fresh"):
            nr_score = nr.get("score", 0)
            if nr_score <= -20:
                return False, f"뉴스랑 강한 약세(score {nr_score}) 매수 차단"
            # 고래 알림 매도 압력 시 whale 전략 차단
            whale_a = nr.get("whale_alert")
            if (whale_a and whale_a.get("net_direction") == "sell"
                    and whale_a.get("total_alerts", 0) >= 2
                    and signal.strategy == "whale"):
                return False, "뉴스랑 X고래알림 매도압력 — whale 매수 차단"

        # v5 필터 7: 모멘텀 확인 — 최근 60초 가격이 상승 중이어야 진입
        if len(self.price_history) >= 10:
            now_t = time.time()
            cutoff = now_t - MOMENTUM_WINDOW_SEC
            window = [p["price"] for p in self.price_history if p["time"] > cutoff]
            if len(window) >= 5:
                momentum_pct = (window[-1] - window[0]) / window[0] * 100
                if momentum_pct < MOMENTUM_MIN_PCT:
                    return False, f"모멘텀 부족 ({momentum_pct:+.3f}%, 최소 {MOMENTUM_MIN_PCT}%)"

        return True, "OK"

    def log_signal_attempt(self, strategy: str, signal_type: str, signal=None,
                           block_filter=None, block_reason=None):
        """시그널 시도 기록 (generated/blocked/no_signal)"""
        try:
            row = {
                "strategy": strategy,
                "signal_type": signal_type,
                "btc_price": int(self.current_price) if self.current_price else None,
                "market_trend": self._market_trend,
                "rsi_value": round(self._rsi, 2),
                "fgi_value": self._fgi,
                "news_score": round(self.news_sentiment_score, 2),
                "cycle_id": getattr(self, 'cycle_id', None),
            }
            if signal:
                row["action"] = signal.action
                row["confidence"] = round(signal.confidence, 2)
                row["suggested_amount"] = signal.suggested_amount
                row["signal_reason"] = signal.reason[:200] if signal.reason else None
            if block_filter:
                row["block_filter"] = block_filter
                row["block_reason"] = block_reason[:200] if block_reason else None

            # v6: ML 컨텍스트 추가
            now_t = time.time()
            cutoff_60s = now_t - 60
            window = [p["price"] for p in self.price_history if p["time"] > cutoff_60s]
            if len(window) >= 2:
                row["momentum_1m_pct"] = round((window[-1] - window[0]) / window[0] * 100, 3)

            recent_trades = [t for t in self.trade_history if t["time"] > cutoff_60s]
            buy_vol = sum(t["volume"] for t in recent_trades if t["side"] == "BID")
            sell_vol = sum(t["volume"] for t in recent_trades if t["side"] == "ASK")
            total_vol = buy_vol + sell_vol
            if total_vol > 0:
                row["trade_pressure_ratio"] = round(buy_vol / total_vol, 3)

            cutoff_whale = now_t - 180
            recent_whales = [w for w in self.whale_recent if w["time"] > cutoff_whale]
            whale_buys_krw = sum(w["krw"] for w in recent_whales if w["side"] == "BID")
            whale_total_krw = sum(w["krw"] for w in recent_whales)
            if whale_total_krw > 0:
                row["whale_buy_ratio"] = round(whale_buys_krw / whale_total_krw, 3)

            cutoff_5m = now_t - 300
            prices_5m = [p["price"] for p in self.price_history if p["time"] > cutoff_5m]
            if len(prices_5m) >= 10:
                import statistics
                mean_p = statistics.mean(prices_5m)
                std_p = statistics.stdev(prices_5m)
                row["volatility_5m"] = round(std_p / mean_p * 100, 3)

            db_insert("signal_attempt_log", row)
        except Exception as e:
            log.debug(f"signal_attempt_log 기록 실패: {e}")

    def log_completed_trade(self, pos: "Position"):
        """완결된 거래를 scalp_trade_log에 기록 (v4: 모든 거래 반드시 기록)"""
        self._trade_counter += 1
        today = datetime.now(KST).strftime("%Y-%m-%d")

        lesson = ""
        was_good = None
        if pos.pnl_pct is not None:
            if pos.pnl_pct > 0:
                was_good = True
                lesson = "수익 실현"
            else:
                was_good = False
                # 자동 교훈 생성
                reasons = []
                if self._market_trend == "downtrend":
                    reasons.append("하락추세 역행 매수")
                if self.news_sentiment_score < -0.3:
                    reasons.append(f"뉴스 부정적({self.news_sentiment_score:+.2f})")
                if self._fgi <= 20:
                    reasons.append(f"극공포(FGI {self._fgi})")
                if pos.exit_reason and "시간 제한" in pos.exit_reason:
                    reasons.append("타임아웃 강제 청산")
                lesson = " + ".join(reasons) if reasons else "시장 역행"

        db_insert("scalp_trade_log", {
            "session_date": today,
            "trade_no": self._trade_counter,
            "strategy": pos.strategy,
            "entry_time": pos.entry_time.isoformat(),
            "exit_time": pos.exit_time.isoformat() if pos.exit_time else None,
            "entry_price": int(pos.entry_price),
            "exit_price": int(pos.exit_price) if pos.exit_price else None,
            "amount_krw": int(pos.amount_krw),
            "pnl_pct": pos.pnl_pct,  # 이미 수수료 왕복 차감된 값
            "pnl_krw": int(pos.amount_krw * (pos.pnl_pct or 0) / 100),  # 수수료 반영 PnL
            "exit_reason": pos.exit_reason,
            "signal_reason": getattr(pos, '_signal_reason', None),
            "confidence": getattr(pos, '_confidence', None),
            "market_trend": self._market_trend,
            "news_sentiment": self.last_news_sentiment,
            "news_score": round(self.news_sentiment_score, 2),
            "fgi_value": self._fgi,
            "rsi_value": round(self._rsi, 2),
            "sma20_vs_price": "above" if self.current_price > self._sma20 else "below",
            "was_good_trade": was_good,
            "lesson": lesson,
            "dry_run": self.dry_run,
            "cycle_id": self.cycle_id,
            "trailing_stop_hit": pos.trailing_stop_active and "트레일링" in (pos.exit_reason or ""),
            "highest_pnl_pct": round(pos.highest_pnl_pct, 3),
            "grace_period_saved": False,
        })

    def emergency_stop(self, reason: str):
        """긴급 정지: 모든 매매 중단, 포지션 정리, 텔레그램 보고"""
        if self.emergency_stopped:
            return
        self.emergency_stopped = True
        log.critical(f"긴급 정지 발동: {reason}")
        sound_alert("문제 생겨서 매매 멈췄어요. 확인해 주세요.", urgent=True)
        send_telegram(
            f"<b>[단타봇 긴급 정지]</b>\n"
            f"사유: {reason}\n"
            f"보유 포지션: {len(self.positions)}개\n"
            f"오늘 손익: {self.daily_pnl:+,.0f}원\n"
            f"{'포지션 보유 중 -- 수동 확인 필요!' if self.positions else '포지션 없음'}"
        )
        # DRY_RUN이 아니고 포지션이 있으면 긴급 청산 시도
        if not self.dry_run and self.positions:
            for pos in list(self.positions):
                try:
                    self.execute_exit(pos, f"긴급 정지: {reason}")
                except Exception as e:
                    log.error(f"긴급 청산 실패: {e}")
                    send_telegram(f"<b>[긴급 청산 실패]</b> {e}\n수동 확인 필요!")
        self.running = False

    # ── WebSocket 수신 ────────────────────────────────

    async def ws_combined(self):
        """실시간 가격+체결 통합 수신 (단일 WebSocket 연결)"""
        backoff = 1
        while self.running:
            try:
                async with websockets.connect(UPBIT_WS, ping_interval=30) as ws:
                    subscribe = [
                        {"ticket": f"combined-{uuid.uuid4().hex[:8]}"},
                        {"type": "ticker", "codes": [MARKET]},
                        {"type": "trade", "codes": [MARKET]},
                    ]
                    await ws.send(json.dumps(subscribe))
                    log.info("WebSocket 통합 연결됨 (ticker+trade)")
                    backoff = 1  # 연결 성공 시 backoff 리셋

                    async for msg in ws:
                        if not self.running:
                            break
                        data = json.loads(msg)
                        msg_type = data.get("type", "")

                        if msg_type == "ticker":
                            self.current_price = data.get("trade_price", self.current_price)
                            self.price_history.append({
                                "price": self.current_price,
                                "time": time.time(),
                            })

                        elif msg_type == "trade":
                            trade = {
                                "price": data.get("trade_price", 0),
                                "volume": data.get("trade_volume", 0),
                                "side": data.get("ask_bid", ""),
                                "krw": data.get("trade_price", 0) * data.get("trade_volume", 0),
                                "time": time.time(),
                            }
                            self.trade_history.append(trade)

                            # 고래 감지 — v8: 동적 BTC 수량 기반
                            whale_threshold = self._whale_threshold_dynamic if self._whale_threshold_dynamic > 0 else WHALE_THRESHOLD_KRW
                            if trade["krw"] >= whale_threshold:
                                self.whale_recent.append(trade)
                                side_kr = '매수' if trade['side'] == 'BID' else '매도'
                                log.info(
                                    f"고래 감지: {side_kr} "
                                    f"{trade['krw']/10000:.0f}만원 @ {trade['price']:,.0f}"
                                )
                                # DB 기록
                                buy_c = sum(1 for w in self.whale_recent if w.get("side") == "BID")
                                sell_c = sum(1 for w in self.whale_recent if w.get("side") == "ASK")
                                db_insert("whale_detections", {
                                    "side": trade["side"],
                                    "volume": trade["volume"],
                                    "price": int(trade["price"]),
                                    "krw_amount": int(trade["krw"]),
                                    "detected_at": datetime.now(KST).isoformat(),
                                    "whale_buy_count": buy_c,
                                    "whale_sell_count": sell_c,
                                })
            except Exception as e:
                log.warning(f"WebSocket 재연결 ({backoff}s): {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)  # 지수 백오프, 최대 30초

    # ── 전략 1: 뉴스 반응 ─────────────────────────────

    # RSS 피드 소스 (무료, API 키 불필요)
    RSS_FEEDS = [
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cointelegraph.com/rss",
        "https://bitcoinmagazine.com/.rss/full/",
        "https://rss.app/feeds/v1.1/tSmEpMocyHlHkMnR.xml",  # 코인니스 한국어
    ]

    # 뉴스 감성 키워드 (클래스 레벨 상수 -- 매 스캔마다 재생성 방지)
    POSITIVE_WORDS = frozenset({
        "surge", "rally", "soar", "breakout", "bull", "pump",
        "approval", "etf approved", "institutional buy", "record high",
        "all-time high", "ath", "moon", "adoption",
        "급등", "상승", "돌파", "호재", "승인", "최고가", "반등", "강세",
    })
    NEGATIVE_WORDS = frozenset({
        "crash", "plunge", "dump", "ban", "hack", "fraud",
        "regulation", "crackdown", "war", "sanctions", "collapse",
        "liquidation", "sell-off", "bearish", "fear",
        "급락", "폭락", "해킹", "규제", "금지", "전쟁", "제재", "하락", "약세",
    })

    async def scan_news(self):
        """RSS 피드로 뉴스 헤드라인 스캔 (무료, API 키 불필요)"""
        import xml.etree.ElementTree as ET

        # 이미 본 헤드라인 추적 (중복 방지, FIFO 순서 보장)
        seen_titles: dict[str, None] = {}  # insertion-ordered dict as ordered set

        while self.running:
            try:
                now = time.time()
                if now - self.last_news_scan < NEWS_SCAN_INTERVAL:
                    await asyncio.sleep(10)
                    continue

                self.last_news_scan = now

                positive_words = self.POSITIVE_WORDS
                negative_words = self.NEGATIVE_WORDS

                pos_count = neg_count = 0
                urgent_signals = []
                new_headlines = 0

                for feed_url in self.RSS_FEEDS:
                    try:
                        r = await asyncio.to_thread(
                            requests.get, feed_url, timeout=10,
                            headers={"User-Agent": "Mozilla/5.0 (crypto-bot)"}
                        )
                        if not r.ok:
                            continue

                        root = ET.fromstring(r.content)

                        # RSS 2.0 또는 Atom 파싱
                        items = root.findall(".//item")  # RSS 2.0
                        if not items:
                            ns = {"atom": "http://www.w3.org/2005/Atom"}
                            items = root.findall(".//atom:entry", ns)

                        for item in items[:10]:  # 피드당 최근 10건만
                            title_el = item.find("title")
                            if title_el is None or not title_el.text:
                                # Atom format
                                ns = {"atom": "http://www.w3.org/2005/Atom"}
                                title_el = item.find("atom:title", ns)
                            if title_el is None or not title_el.text:
                                continue

                            title = title_el.text.strip()
                            title_key = title.lower()[:80]

                            if title_key in seen_titles:
                                continue
                            seen_titles[title_key] = None
                            new_headlines += 1

                            # 헤드라인만으로 키워드 감성 분석
                            text = title.lower()
                            p = sum(1 for w in positive_words if w in text)
                            n = sum(1 for w in negative_words if w in text)
                            pos_count += p
                            neg_count += n

                            if p >= 2 or n >= 2:
                                urgent_signals.append({
                                    "title": title,
                                    "sentiment": "positive" if p > n else "negative",
                                    "score": p - n,
                                })

                    except ET.ParseError as e:
                        log.warning(f"RSS 파싱 실패 ({feed_url[:40]}): {e}")
                        continue
                    except Exception as e:
                        log.warning(f"RSS 피드 에러 ({feed_url[:40]}): {e}")
                        continue

                # seen dict가 너무 커지지 않도록 관리 (최근 300건만 유지)
                if len(seen_titles) > 500:
                    # dict preserves insertion order; keep newest 300
                    keys = list(seen_titles)
                    for k in keys[:-300]:
                        del seen_titles[k]

                total = pos_count + neg_count
                if total > 0:
                    self.news_sentiment_score = (pos_count - neg_count) / total
                elif new_headlines == 0:
                    # 새 헤드라인 없을 때 이전 감성 유지 (리셋 방지)
                    # 단, 시간 경과에 따라 서서히 감쇠 (5분마다 20% 감쇠)
                    self.news_sentiment_score *= 0.8
                else:
                    # 새 헤드라인은 있지만 키워드 없음 → 중립
                    self.news_sentiment_score = 0

                prev = self.last_news_sentiment
                if self.news_sentiment_score > 0.3:
                    self.last_news_sentiment = "positive"
                elif self.news_sentiment_score < -0.3:
                    self.last_news_sentiment = "negative"
                else:
                    self.last_news_sentiment = "neutral"

                if new_headlines > 0:
                    log.debug(f"RSS 스캔: 새 헤드라인 {new_headlines}건, 감성 {self.news_sentiment_score:+.2f}")

                # DB 기록 (매 스캔마다)
                if total > 0 or new_headlines > 0:
                    db_insert("news_sentiment_log", {
                        "sentiment": self.last_news_sentiment,
                        "score": round(self.news_sentiment_score, 2),
                        "prev_sentiment": prev,
                        "source": "rss",
                        "headline_count": new_headlines,
                        "positive_count": pos_count,
                        "negative_count": neg_count,
                        "urgent_headlines": urgent_signals if urgent_signals else None,
                    })

                # 감성 급변 시 시그널
                if prev != self.last_news_sentiment and self.last_news_sentiment != "neutral":
                    log.info(
                        f"뉴스 감성 급변: {prev} -> {self.last_news_sentiment} "
                        f"(score: {self.news_sentiment_score:+.2f})"
                    )
                    if urgent_signals:
                        for s in urgent_signals:
                            log.info(f"  긴급: {s['title']}")

            except Exception as e:
                log.error(f"뉴스 스캔 에러: {e}")
                await asyncio.sleep(30)

    def check_news_signal(self) -> TradeSignal | None:
        """v5: 뉴스는 모니터링 전용 — 직접 매매 시그널 생성하지 않음.
        매도 시그널만 반환 (보유 포지션 보호용), 매수는 안전 필터로만 작동."""
        if abs(self.news_sentiment_score) < 0.3:
            return None

        # v5: 매수 시그널 제거 — 0% 승률이었던 뉴스 매수 중단
        # 뉴스 긍정은 다른 전략의 confidence 보너스로만 활용
        if self.news_sentiment_score >= 0.3:
            return None  # 매수 시그널 비활성화

        # 강한 부정 뉴스일 때만 매도 시그널 (보유 포지션 보호)
        if self.news_sentiment_score <= -0.5:
            reason = f"뉴스 강한 부정 (score: {self.news_sentiment_score:+.2f})"
            conf = min(abs(self.news_sentiment_score), 1.0)
            # 뉴스랑 약세가 겹치면 confidence 보강
            nr = self._newsrang
            if nr and nr.get("fresh") and nr.get("score", 0) <= -10:
                conf = min(conf + 0.15, 1.0)
                reason += f" + 뉴스랑 약세({nr['score']})"
            return TradeSignal(
                strategy="news",
                action="sell",
                confidence=conf,
                reason=reason,
            )

        # 뉴스랑 단독 매도 시그널: RSS 자체 감성은 약하지만 뉴스랑 종합이 매우 약세
        nr = self._newsrang
        if nr and nr.get("fresh") and nr.get("score", 0) <= -30:
            return TradeSignal(
                strategy="news",
                action="sell",
                confidence=0.6,
                reason=f"뉴스랑 강한 약세(score {nr['score']}) — 보유 포지션 보호",
            )

        return None

    # ── 전략 2: 급등/급락 리바운드 ────────────────────

    def _get_recent_trade_volumes(self, now: float, window_sec: int = 60) -> tuple[float, float]:
        """최근 N초 체결의 매수/매도 거래량 합계 (중복 계산 방지)"""
        buy_vol = 0.0
        sell_vol = 0.0
        cutoff = now - window_sec
        # deque는 시간순이므로 뒤에서부터 탐색하면 빠르게 중단 가능
        for t in reversed(self.trade_history):
            if t["time"] < cutoff:
                break
            if t["side"] == "BID":
                buy_vol += t["volume"]
            elif t["side"] == "ASK":
                sell_vol += t["volume"]
        return buy_vol, sell_vol

    def check_spike_signal(self) -> TradeSignal | None:
        """급등/급락 후 리바운드 시그널"""
        if len(self.price_history) < 30:
            return None

        now = time.time()
        cutoff = now - SPIKE_WINDOW_SEC
        window_prices = [
            p["price"] for p in self.price_history
            if p["time"] > cutoff
        ]

        if len(window_prices) < 10:
            return None

        high = max(window_prices)
        low = min(window_prices)
        current = self.current_price

        # 급락 후 리바운드 감지 — v8: 적응형 threshold
        spike_th = self._adaptive_spike_threshold
        drop_pct = (high - low) / high * 100
        if drop_pct >= spike_th:
            # 바닥에서 반등 시작 확인 (최저점 대비 0.2% 이상 회복)
            recovery = (current - low) / low * 100
            if recovery >= 0.2 and current < high * 0.998:
                # 체결 강도로 반등 확인 (52% 이상이면 매수 우위)
                buy_vol, sell_vol = self._get_recent_trade_volumes(now)
                total = buy_vol + sell_vol
                if total > 0 and buy_vol / total > 0.52:
                    return TradeSignal(
                        strategy="spike",
                        action="buy",
                        confidence=min(drop_pct / 3, 1.0),
                        reason=(
                            f"급락 {drop_pct:.1f}% 후 반등 {recovery:.1f}% "
                            f"(매수 체결 {buy_vol/total*100:.0f}%)"
                        ),
                    )

        # 급등 후 되돌림 감지 (보유 중일 때 매도 시그널)
        surge_pct = (high - low) / low * 100
        if surge_pct >= spike_th:
            pullback = (high - current) / high * 100
            if pullback >= 0.2 and current > low * 1.002:
                buy_vol, sell_vol = self._get_recent_trade_volumes(now)
                total = buy_vol + sell_vol
                if total > 0 and sell_vol / total > 0.52:
                    return TradeSignal(
                        strategy="spike",
                        action="sell",
                        confidence=min(surge_pct / 3, 1.0),
                        reason=(
                            f"급등 {surge_pct:.1f}% 후 되돌림 {pullback:.1f}% "
                            f"(매도 체결 {sell_vol/total*100:.0f}%)"
                        ),
                    )
        return None

    # ── 전략 3: 고래 추종 ─────────────────────────────

    def _get_recent_whale_krw(self, now: float) -> tuple[float, float, int]:
        """최근 고래 매수/매도 KRW 합계와 건수 (중복 필터링 방지)"""
        buy_krw = 0.0
        sell_krw = 0.0
        count = 0
        cutoff = now - WHALE_RATIO_WINDOW_SEC
        for w in reversed(self.whale_recent):
            if w["time"] < cutoff:
                break
            count += 1
            if w["side"] == "BID":
                buy_krw += w["krw"]
            elif w["side"] == "ASK":
                sell_krw += w["krw"]
        return buy_krw, sell_krw, count

    def check_whale_signal(self) -> TradeSignal | None:
        """고래 금액 비율 기반 추종 시그널 (v2)"""
        if len(self.whale_recent) < 2:
            return None

        now = time.time()
        buy_krw, sell_krw, count = self._get_recent_whale_krw(now)

        if count < 3:  # v6: 2→3, 최소 3건의 고래 거래로 통계적 유의성 확보
            return None

        total_krw = buy_krw + sell_krw

        if total_krw < WHALE_THRESHOLD_KRW:
            return None

        buy_ratio = buy_krw / total_krw
        sell_ratio = sell_krw / total_krw

        if buy_ratio >= WHALE_RATIO_THRESHOLD:
            return TradeSignal(
                strategy="whale",
                action="buy",
                confidence=min(buy_ratio, 1.0),
                reason=(
                    f"고래 매수 금액 {buy_ratio:.0%} "
                    f"({buy_krw/10000:.0f}만 vs 매도 {sell_krw/10000:.0f}만)"
                ),
            )
        elif sell_ratio >= WHALE_RATIO_THRESHOLD:
            return TradeSignal(
                strategy="whale",
                action="sell",
                confidence=min(sell_ratio, 1.0),
                reason=(
                    f"고래 매도 금액 {sell_ratio:.0%} "
                    f"({sell_krw/10000:.0f}만 vs 매수 {buy_krw/10000:.0f}만)"
                ),
            )
        return None

    def is_sell_pressure_blocking(self) -> bool:
        """매도 압력 방패: 고래 매도가 매수의 N배 이상이면 매수 차단 (v2)"""
        if not self.whale_recent:
            return False

        now = time.time()
        buy_krw, sell_krw, count = self._get_recent_whale_krw(now)

        if count == 0:
            return False

        if buy_krw == 0 and sell_krw > 0:
            return True
        if buy_krw > 0 and sell_krw / buy_krw >= SELL_PRESSURE_BLOCK_RATIO:
            log.info(
                f"매도 압력 방패 발동: 매도 {sell_krw/10000:.0f}만 / 매수 {buy_krw/10000:.0f}만 "
                f"= {sell_krw/buy_krw:.1f}배 (기준 {SELL_PRESSURE_BLOCK_RATIO}배)"
            )
            return True
        return False

    # ── 포지션 관리 ───────────────────────────────────

    def _load_rl_exit_model(self):
        """RL 청산 모델 로드 (PPO). 한 번만 로드하고 캐싱."""
        if hasattr(self, '_rl_exit_model'):
            return self._rl_exit_model
        try:
            from stable_baselines3 import PPO
            model_path = Path(__file__).resolve().parent.parent / "data" / "scalp_models" / "ppo_exit_best" / "best_model"
            if model_path.with_suffix(".zip").exists():
                self._rl_exit_model = PPO.load(str(model_path))
                log.info("RL 청산 모델 로드 완료 (PPO best)")
                return self._rl_exit_model
        except Exception as e:
            log.warning(f"RL 청산 모델 로드 실패: {e}")
        self._rl_exit_model = None
        return None

    def _rl_exit_decision(self, pos, pnl_pct: float, hold_min: float) -> int | None:
        """RL 모델로 청산 결정. 0=HOLD, 1=TP, 2=SL. 실패 시 None."""
        model = self._load_rl_exit_model()
        if model is None:
            return None

        try:
            import numpy as np
            # 모멘텀 계산
            prices = list(self.price_history) if self.price_history else [{"price": self.current_price}]
            mom_1m = (prices[-1]["price"] / prices[-2]["price"] - 1) * 100 if len(prices) >= 2 else 0
            mom_5m = (prices[-1]["price"] / prices[-6]["price"] - 1) * 100 if len(prices) >= 6 else 0

            # 전략 인코딩
            strat_map = {"news": 0, "spike": 1, "whale": 2}
            strategy_type = strat_map.get(pos.strategy, 1)

            obs = np.array([
                np.clip(pnl_pct, -10, 10),
                min(hold_min, 15),
                np.clip(mom_1m, -5, 5),
                np.clip(mom_5m, -5, 5),
                1.0,    # vol_ratio (실시간 미수집 시 기본값)
                float(np.clip(self._rsi, 0, 100)),   # RSI
                0.5,    # BB 위치 (기본값)
                float(strategy_type),
            ], dtype=np.float32)

            action, _ = model.predict(obs, deterministic=True)
            return int(action)
        except Exception as e:
            log.warning(f"RL 청산 예측 실패: {e}")
            return None

    def check_position_exit(self) -> list[tuple[Position, str]]:
        """보유 포지션의 익절/손절/트레일링/시간제한 확인 (v7: RL 청산 통합)"""
        exits = []
        now = datetime.now(KST)
        fee_roundtrip = COMMISSION_PCT * 2  # 왕복 수수료 0.10%
        use_rl = os.environ.get("USE_RL_EXIT", "true").lower() == "true"

        for pos in self.positions:
            if self.current_price <= 0:
                continue

            raw_pnl = (self.current_price - pos.entry_price) / pos.entry_price * 100
            pnl_pct = raw_pnl - fee_roundtrip  # 수수료 차감 실질 수익률
            hold_sec = (now - pos.entry_time).total_seconds()
            hold_min = hold_sec / 60

            # v5: 트레일링 스탑 업데이트
            if pnl_pct > pos.highest_pnl_pct:
                pos.highest_pnl_pct = pnl_pct
            if not pos.trailing_stop_active and pnl_pct >= TRAILING_STOP_ACTIVATE_PCT:
                pos.trailing_stop_active = True
                log.info(
                    f"[{pos.strategy}] 트레일링 스탑 활성화: "
                    f"현재 {pnl_pct:+.2f}%, 최고 {pos.highest_pnl_pct:+.2f}%"
                )

            # === 안전장치 (RL보다 우선) ===
            # 강제 손절 — 절대 한계
            if pnl_pct <= -pos.stop_loss_pct:
                exits.append((pos, f"손절 {pnl_pct:.2f}%"))
                continue
            # 시간 제한 — 절대 한계
            if hold_sec > pos.max_hold_min * 60:
                exits.append((pos, f"시간 제한 {pos.max_hold_min}분 (현재 {pnl_pct:+.2f}%)"))
                continue

            # === v7: RL 청산 판단 ===
            if use_rl:
                rl_action = self._rl_exit_decision(pos, pnl_pct, hold_min)
                if rl_action == 1:  # RL says TAKE_PROFIT
                    exits.append((pos, f"RL 익절 {pnl_pct:+.2f}% (보유 {hold_min:.0f}분)"))
                    continue
                elif rl_action == 2:  # RL says STOP_LOSS
                    exits.append((pos, f"RL 손절 {pnl_pct:+.2f}% (보유 {hold_min:.0f}분)"))
                    continue
                # rl_action == 0 (HOLD) or None → 기존 규칙으로 폴백

            # === 기존 규칙 기반 (RL HOLD 또는 모델 없을 때) ===
            # 익절 (수수료 차감 후 기준)
            if pnl_pct >= pos.take_profit_pct:
                exits.append((pos, f"익절 +{pnl_pct:.2f}% (수수료 후)"))
            # v5: 트레일링 스탑 — 최고점 대비 하락 시 청산
            elif pos.trailing_stop_active:
                drawdown = pos.highest_pnl_pct - pnl_pct
                if drawdown >= TRAILING_STOP_DISTANCE_PCT:
                    exits.append((pos, f"트레일링 스탑: 최고 {pos.highest_pnl_pct:+.2f}% → 현재 {pnl_pct:+.2f}% (하락 {drawdown:.2f}%)"))
            # 조기 손절 -- 5분 경과 + -0.15% 이하
            elif hold_sec > EARLY_STOP_TIME_MIN * 60 and pnl_pct <= -EARLY_STOP_LOSS_PCT:
                exits.append((pos, f"조기 손절: {hold_sec/60:.0f}분 경과 + {pnl_pct:+.2f}%"))

        return exits

    # ── 매매 실행 ─────────────────────────────────────

    def can_trade(self) -> tuple[bool, str]:
        """매매 가능 여부 확인"""
        if os.environ.get("EMERGENCY_STOP", "false").lower() == "true":
            return False, "EMERGENCY_STOP 활성화"
        # Check auto emergency stop
        auto_em_file = Path(__file__).resolve().parent.parent / "data" / "auto_emergency.json"
        if auto_em_file.exists():
            try:
                with open(auto_em_file) as f:
                    em_data = json.load(f)
                if em_data.get("active", False):
                    log.warning("자동 긴급정지 활성화 - 매매 차단")
                    return False, "자동 긴급정지 활성화"
            except Exception:
                pass
        max_daily = SHORT_TERM_MAX_DAILY_DRYRUN if self.dry_run else SHORT_TERM_MAX_DAILY
        if self.daily_trade_count >= max_daily:
            return False, "daily_limit"
        if self.used_budget >= SHORT_TERM_BUDGET:
            return False, "budget_limit"
        if len(self.positions) >= 2:
            return False, "position_limit"
        return True, "OK"

    def execute_entry(self, signal: TradeSignal):
        """매수 진입"""
        if self.emergency_stopped:
            return

        can, reason = self.can_trade()
        if not can:
            if reason not in self._last_block_reason:
                log.info(f"매수 불가: {reason}")
                self._last_block_reason.add(reason)
            self.log_signal_attempt(signal.strategy, "blocked", signal=signal,
                                    block_filter="can_trade", block_reason=reason)
            return

        # v4: 안전 필터 적용
        self.update_market_context()
        safe, block_reason = self.check_safety_filters(signal)
        if not safe:
            if block_reason not in self._last_block_reason:
                log.info(f"[v4 필터] {block_reason}")
                self._last_block_reason.add(block_reason)
            # 필터명 파싱: 첫 줄에서 키워드 추출
            filter_name = "unknown"
            if "하락추세" in block_reason and "whale" in block_reason:
                filter_name = "downtrend_whale"
            elif "뉴스 부정적" in block_reason:
                filter_name = "news_negative"
            elif "극공포" in block_reason:
                filter_name = "extreme_fear"
            elif "중복 진입" in block_reason:
                filter_name = "duplicate_strategy"
            elif "과매도" in block_reason:
                filter_name = "downtrend_oversold"
            elif "모멘텀" in block_reason:
                filter_name = "momentum_lacking"
            self.log_signal_attempt(signal.strategy, "blocked", signal=signal,
                                    block_filter=filter_name, block_reason=block_reason)
            return

        # 시그널 통과 -- generated 기록
        self.log_signal_attempt(signal.strategy, "generated", signal=signal)

        # Kelly 사이징: confidence에 비례하여 최대 금액 조절 (감독 연동)
        kelly_max = _kelly_short_term(signal.confidence)
        if kelly_max == 0:
            orch = _read_orchestrator_state()
            log.info(
                f"[감독 차단] 매수 차단 — danger={orch['danger_score']}, "
                f"agent={orch['active_agent']}, regime={orch['regime']}"
            )
            self.log_signal_attempt(signal.strategy, "blocked", signal=signal,
                                    block_filter="orchestrator_danger",
                                    block_reason=f"감독 danger={orch['danger_score']}")
            return
        amount = min(signal.suggested_amount, kelly_max)
        amount = min(amount, SHORT_TERM_BUDGET - self.used_budget)

        if amount < 5000:  # Upbit 최소 주문
            log.info("매수 금액 부족 (5,000원 미만)")
            return

        log.info(
            f"[{signal.strategy}] 매수 시그널: {signal.reason} "
            f"(신뢰도 {signal.confidence:.0%}, 금액 {amount:,}원)"
        )

        if self.dry_run:
            log.info(f"[DRY_RUN] 매수 시뮬레이션: {amount:,}원 @ {self.current_price:,.0f}")
            entry_price = self.current_price
            btc_qty = (amount / entry_price) * (1 - COMMISSION_PCT / 100)
            self.consecutive_errors = 0
        else:
            # 정규 매매와 동시 실행 방지
            if not check_lock():
                log.warning("정규 매매 실행 중 -- 매수 보류")
                return
            if not acquire_lock("short_term"):
                log.warning("락 획득 실패 -- 매수 보류")
                return
            try:
                result = upbit_order("bid", MARKET, str(amount))
                if not result["ok"]:
                    self.consecutive_errors += 1
                    err_data = result.get("data", {})
                    err_name = err_data.get("error", {}).get("name", "") if isinstance(err_data, dict) else str(err_data)
                    log.error(f"매수 실패 ({self.consecutive_errors}회 연속): {err_data}")
                    # 인증/권한 에러 → 즉시 정지
                    if err_name in ("jwt_verification", "no_authorization", "invalid_access_key"):
                        self.emergency_stop(f"Upbit 인증 에러: {err_name}")
                    elif self.consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                        self.emergency_stop(f"연속 {self.consecutive_errors}회 에러")
                    return
                self.consecutive_errors = 0
                entry_price = self.current_price
                btc_qty = (amount / entry_price) * (1 - COMMISSION_PCT / 100)
                log.info(f"매수 체결: {amount:,}원 @ ~{entry_price:,.0f}")
            except requests.exceptions.Timeout:
                self.consecutive_errors += 1
                log.error(f"매수 타임아웃 ({self.consecutive_errors}회 연속)")
                if self.consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                    self.emergency_stop("Upbit API 연속 타임아웃")
                return
            except Exception as e:
                self.consecutive_errors += 1
                log.error(f"매수 예외 ({self.consecutive_errors}회 연속): {e}")
                if self.consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                    self.emergency_stop(f"연속 예외: {e}")
                return
            finally:
                release_lock()

        # v5.1: 레짐별 tp/sl 배율 적용
        rf = self._regime_filters
        tp_mult = rf.get("tp_multiplier", 1.0)
        sl_mult = rf.get("sl_multiplier", 1.0)

        pos = Position(
            strategy=signal.strategy,
            side="bid",
            entry_price=entry_price,
            amount_krw=amount,
            btc_qty=btc_qty,
            entry_time=datetime.now(KST),
            max_hold_min=self._adaptive_max_hold,  # v8: 동적 보유 시간
            take_profit_pct=SHORT_TERM_TAKE_PROFIT * tp_mult,  # v5.1: bull 1.5x
            stop_loss_pct=SHORT_TERM_STOP_LOSS * sl_mult,      # v5.1: bear 0.7x
        )
        # v4: 기록용 메타데이터
        pos._signal_reason = signal.reason
        pos._confidence = round(signal.confidence, 2)
        self.positions.append(pos)
        self.daily_trade_count += 1
        self._daily_buy_count += 1  # v8: 하락장 매수 제한 카운터
        self.used_budget += amount

        # DB 기록: entry 시에는 기록하지 않음 (exit 시 완전한 1건으로 기록)
        # 이전 코드는 entry/exit 각각 INSERT하여 중복 + exit_price=0 문제 발생

        send_telegram(
            f"<b>[초단타 매수]</b> {signal.strategy}\n"
            f"금액: {amount:,}원\n"
            f"가격: {entry_price:,.0f}원\n"
            f"사유: {signal.reason}\n"
            f"{'[DRY_RUN]' if self.dry_run else ''}"
        )

    def execute_exit(self, pos: Position, reason: str):
        """매도 청산"""
        exit_price = self.current_price
        # 수수료 왕복(매수+매도) 차감한 실질 수익률
        raw_pnl_pct = (exit_price - pos.entry_price) / pos.entry_price * 100
        pnl_pct = raw_pnl_pct - (COMMISSION_PCT * 2)  # 왕복 수수료 0.10% 차감
        pnl_krw = pos.amount_krw * pnl_pct / 100

        log.info(
            f"[{pos.strategy}] 매도: {reason} | "
            f"진입 {pos.entry_price:,.0f} → 청산 {exit_price:,.0f} | "
            f"손익 {pnl_pct:+.2f}% ({pnl_krw:+,.0f}원)"
        )

        if not self.dry_run:
            if not acquire_lock("short_term_exit"):
                log.warning("매도 락 획득 실패 — 매도 보류")
                return
            try:
                result = upbit_order("ask", MARKET, f"{pos.btc_qty:.8f}")
                if not result["ok"]:
                    self.consecutive_errors += 1
                    err_data = result.get("data", {})
                    log.error(f"매도 실패 ({self.consecutive_errors}회 연속): {err_data}")
                    send_telegram(
                        f"<b>[단타 매도 실패]</b>\n"
                        f"사유: {err_data}\n"
                        f"포지션: {pos.strategy} {pos.amount_krw:,}원\n"
                        f"수동 확인 필요!"
                    )
                    if self.consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                        self.emergency_stop(f"매도 연속 {self.consecutive_errors}회 실패")
                    return
                self.consecutive_errors = 0
            except Exception as e:
                self.consecutive_errors += 1
                log.error(f"매도 예외: {e}")
                send_telegram(f"<b>[단타 매도 예외]</b> {e}\n수동 확인 필요!")
                if self.consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                    self.emergency_stop(f"매도 예외: {e}")
                return
            finally:
                release_lock()

        pos.exit_price = exit_price
        pos.exit_time = datetime.now(KST)
        pos.exit_reason = reason
        pos.pnl_pct = round(pnl_pct, 2)

        self.positions.remove(pos)
        self.closed_positions.append(pos)
        self.total_closed_count += 1
        # daily_trade_count는 entry에서만 증가 (round-trip = 1회)
        self.daily_pnl += pnl_krw
        self.used_budget = max(0, self.used_budget - pos.amount_krw)
        self._last_block_reason.clear()

        # v4: 완결된 거래를 scalp_trade_log에 기록
        self.log_completed_trade(pos)

        # DB 기록 (완결된 거래 1건 — entry+exit 통합)
        db_insert("scalp_trades", {
            "strategy": pos.strategy,
            "side": "ask",
            "entry_price": int(pos.entry_price),
            "exit_price": int(exit_price),
            "amount_krw": int(pos.amount_krw),
            "btc_qty": float(pos.btc_qty),
            "entry_time": pos.entry_time.isoformat(),
            "exit_time": pos.exit_time.isoformat(),
            "exit_reason": reason,
            "pnl_pct": round(pnl_pct, 3),
            "pnl_krw": int(pnl_krw),
            "confidence": getattr(pos, '_confidence', None),
            "signal_reason": getattr(pos, '_signal_reason', None),
            "cycle_id": self.cycle_id,
            "dry_run": self.dry_run,
        })

        # decisions 테이블 기록 (RL 훈련 데이터용 — 매수/매도 각각 독립 insert)
        try:
            entry_reason = (
                f"[초단타-{pos.strategy}] {getattr(pos, '_signal_reason', '')} | "
                f"추세={self._market_trend} RSI={self._rsi:.1f} FGI={self._fgi}"
            )
            db_insert("decisions", {
                "market": MARKET,
                "decision": "매수",
                "confidence": getattr(pos, '_confidence', 0.5),
                "reason": entry_reason,
                "current_price": int(pos.entry_price),
                "trade_amount": int(pos.amount_krw),
                "rsi_value": round(self._rsi, 2),
                "fear_greed_value": self._fgi,
                "sma20_price": int(self._sma20) if self._sma20 else None,
                "executed": not self.dry_run,
                "source": "short_term",
                "cycle_id": self.cycle_id,
                "dry_run": self.dry_run,
                "created_at": pos.entry_time.isoformat(),
            })
        except Exception as e:
            log.error(f"[DB] decisions 매수 기록 실패: {e}")

        try:
            exit_reason_full = (
                f"[초단타-{pos.strategy}] {reason} | "
                f"진입 {pos.entry_price:,.0f} → 청산 {exit_price:,.0f} | "
                f"손익 {pnl_pct:+.2f}% ({pnl_krw:+,.0f}원)"
            )
            db_insert("decisions", {
                "market": MARKET,
                "decision": "매도",
                "confidence": getattr(pos, '_confidence', 0.5),
                "reason": exit_reason_full,
                "current_price": int(exit_price),
                "trade_amount": int(pos.amount_krw),
                "trade_volume": float(pos.btc_qty),
                "rsi_value": round(self._rsi, 2),
                "fear_greed_value": self._fgi,
                "sma20_price": int(self._sma20) if self._sma20 else None,
                "executed": not self.dry_run,
                "profit_loss": round(pnl_pct, 3),
                "source": "short_term",
                "cycle_id": self.cycle_id,
                "dry_run": self.dry_run,
            })
        except Exception as e:
            log.error(f"[DB] decisions 매도 기록 실패: {e}")

        send_telegram(
            f"<b>[초단타 매도]</b> {pos.strategy}\n"
            f"사유: {reason}\n"
            f"진입: {pos.entry_price:,.0f}원\n"
            f"청산: {exit_price:,.0f}원\n"
            f"손익: {pnl_pct:+.2f}% ({pnl_krw:+,.0f}원)\n"
            f"일일 누적: {self.daily_pnl:+,.0f}원\n"
            f"{'[DRY_RUN]' if self.dry_run else ''}"
        )

    # ── 메인 루프 ─────────────────────────────────────

    async def strategy_loop(self):
        """매 1초 마다 전략 판단"""
        # WebSocket 연결 대기
        await asyncio.sleep(5)
        log.info("전략 루프 시작")

        # v4: 초기 시장 컨텍스트 로드
        self.update_market_context()
        log.info(
            f"[v4] 시장 컨텍스트: 추세={self._market_trend}, "
            f"SMA20={self._sma20:,.0f}, RSI={self._rsi:.1f}, FGI={self._fgi}"
        )

        while self.running:
            try:
                # 자정 리셋: 날짜가 바뀌면 daily 카운터 초기화
                today = datetime.now(KST).date()
                if today != self._current_date:
                    log.info(f"[자정 리셋] {self._current_date} → {today}: "
                             f"daily_trade_count {self.daily_trade_count}→0, "
                             f"daily_pnl {self.daily_pnl:+.0f}→0")
                    self.daily_trade_count = 0
                    self.daily_pnl = 0.0
                    self._current_date = today

                if self.current_price <= 0:
                    await asyncio.sleep(1)
                    continue

                # v4: 시장 컨텍스트 주기적 업데이트
                self.update_market_context()

                # v6: 시장 스냅샷 기록 (5분 간격)
                if time.time() - self._last_snapshot_time >= 300:
                    self.record_market_snapshot()
                    self._last_snapshot_time = time.time()

                # 1) 보유 포지션 청산 확인
                exits = self.check_position_exit()
                for pos, reason in exits:
                    self.execute_exit(pos, reason)

                # 2) 매수 시그널 수집
                signals: list[TradeSignal] = []

                news_sig = self.check_news_signal()
                if news_sig:
                    signals.append(news_sig)

                spike_sig = self.check_spike_signal()
                if spike_sig:
                    signals.append(spike_sig)

                whale_sig = self.check_whale_signal()
                if whale_sig:
                    signals.append(whale_sig)

                # 2-1) 무신호 로깅 (5분 간격 제한)
                if not any([news_sig, spike_sig, whale_sig]):
                    if not hasattr(self, '_last_no_signal_log') or \
                       (datetime.now(KST) - self._last_no_signal_log).total_seconds() > 300:
                        self.log_signal_attempt("all", "no_signal")
                        self._last_no_signal_log = datetime.now(KST)

                # 3) 시그널 우선순위 처리
                buy_signals = [s for s in signals if s.action == "buy"]
                sell_signals = [s for s in signals if s.action == "sell"]
                now_dt = datetime.now(KST)

                # v5: 매도 시그널 — 전략별 독립 청산 + 진입 보호 기간
                if sell_signals and self.positions:
                    for sell_sig in sell_signals:
                        for pos in list(self.positions):
                            # v5: 진입 보호 기간 — 진입 후 3분 이내면 시그널 청산 무시
                            hold_sec = (now_dt - pos.entry_time).total_seconds()
                            if hold_sec < GRACE_PERIOD_SEC:
                                continue
                            # v5: 전략별 독립 청산 — 같은 전략 또는 뉴스 강부정만 청산
                            if sell_sig.strategy == pos.strategy or sell_sig.strategy == "news":
                                self.execute_exit(pos, f"{sell_sig.strategy}: {sell_sig.reason}")

                # 매수 시그널: 매도 압력 방패 확인 후 실행
                if buy_signals:
                    if self.is_sell_pressure_blocking():
                        # 매도 압력 방패에 의해 차단된 시그널 기록
                        best_blocked = max(buy_signals, key=lambda s: s.confidence)
                        self.log_signal_attempt(
                            best_blocked.strategy, "blocked", signal=best_blocked,
                            block_filter="sell_pressure", block_reason="매도 압력 방패 발동")
                    else:
                        best_buy = max(buy_signals, key=lambda s: s.confidence)
                        # v5: 뉴스 긍정일 때 confidence 보너스 (다른 전략 강화)
                        if self.news_sentiment_score >= 0.3 and best_buy.strategy != "news":
                            best_buy.confidence = min(best_buy.confidence + 0.1, 1.0)
                        # 뉴스랑 강세일 때 추가 보너스
                        nr = self._newsrang
                        if nr and nr.get("fresh") and nr.get("score", 0) >= 15:
                            best_buy.confidence = min(best_buy.confidence + 0.1, 1.0)
                        if best_buy.confidence >= 0.5:  # 최소 신뢰도 50%
                            self.execute_entry(best_buy)

                await asyncio.sleep(1)

            except Exception as e:
                log.error(f"전략 루프 에러: {e}")
                await asyncio.sleep(5)

    async def status_reporter(self):
        """5분마다 상태 리포트"""
        while self.running:
            await asyncio.sleep(300)
            pos_info = ""
            for pos in self.positions:
                pnl = (self.current_price - pos.entry_price) / pos.entry_price * 100
                hold_min = (datetime.now(KST) - pos.entry_time).total_seconds() / 60
                pos_info += (
                    f"\n  [{pos.strategy}] {pnl:+.2f}% "
                    f"({hold_min:.0f}분 보유, {pos.amount_krw:,}원)"
                )

            log.info(
                f"=== 상태 리포트 ===\n"
                f"  현재가: {self.current_price:,.0f}원\n"
                f"  보유 포지션: {len(self.positions)}개{pos_info}\n"
                f"  오늘 매매: {self.daily_trade_count}회\n"
                f"  오늘 손익: {self.daily_pnl:+,.0f}원\n"
                f"  사용 자금: {self.used_budget:,}/{SHORT_TERM_BUDGET:,}원\n"
                f"  뉴스 감성: {self.last_news_sentiment} ({self.news_sentiment_score:+.2f})\n"
                f"  고래 버퍼: {len(self.whale_recent)}건"
            )

    async def settlement_reporter(self):
        """6시간 간격 정산 리포트 — DB 기록 + 텔레그램 알림 + 훈련 일지"""
        SETTLEMENT_INTERVAL = 6 * 3600  # 6시간
        self._settlement_start = time.time()
        self._settlement_epoch = 0  # 정산 회차
        self._prev_settled_count = 0  # 이전 정산까지 처리된 거래 수
        self._prev_settled_pnl = 0.0  # 이전 정산까지 누적 PnL

        while self.running:
            await asyncio.sleep(SETTLEMENT_INTERVAL)
            self._settlement_epoch += 1
            try:
                await self._do_settlement()
            except Exception as e:
                log.error(f"정산 리포트 에러: {e}")

    async def _do_settlement(self):
        """6시간 정산 실행"""
        # now = datetime.now(KST)  # available but epoch/elapsed_h used instead
        epoch = self._settlement_epoch
        elapsed_h = (time.time() - self._settlement_start) / 3600

        # 이번 정산 구간의 거래만 추출
        current_count = len(self.closed_positions)
        period_trades = self.closed_positions[self._prev_settled_count:]
        period_count = len(period_trades)
        period_wins = sum(1 for p in period_trades if (p.pnl_pct or 0) > 0)
        period_losses = sum(1 for p in period_trades if (p.pnl_pct or 0) < 0)
        period_even = period_count - period_wins - period_losses
        period_pnl = sum(p.amount_krw * (p.pnl_pct or 0) / 100 for p in period_trades)
        period_win_rate = period_wins / max(period_count, 1) * 100

        # 전략별 성과 분석
        strategy_stats: dict[str, dict] = {}
        for p in period_trades:
            s = p.strategy
            if s not in strategy_stats:
                strategy_stats[s] = {"count": 0, "wins": 0, "pnl": 0.0, "reasons": []}
            strategy_stats[s]["count"] += 1
            if (p.pnl_pct or 0) > 0:
                strategy_stats[s]["wins"] += 1
            strategy_stats[s]["pnl"] += p.amount_krw * (p.pnl_pct or 0) / 100
            if p.exit_reason:
                strategy_stats[s]["reasons"].append(p.exit_reason[:60])

        # 수수료 분석
        total_volume = sum(p.amount_krw for p in period_trades) * 2  # 매수+매도
        total_fee_est = total_volume * COMMISSION_PCT / 100
        gross_pnl = sum(
            p.amount_krw * ((p.exit_price - p.entry_price) / p.entry_price * 100) / 100
            for p in period_trades if p.exit_price
        )

        # 누적 통계 (total_closed_count는 트리밍과 무관하게 정확)
        cumul_count = self.total_closed_count
        cumul_pnl = self.daily_pnl

        # 훈련 일지 메시지 생성
        strat_detail = ""
        for s, st in strategy_stats.items():
            wr = st["wins"] / max(st["count"], 1) * 100
            strat_detail += f"\n  [{s}] {st['count']}건, 승률 {wr:.0f}%, 손익 {st['pnl']:+,.0f}원"
            # 가장 빈번한 청산 사유
            if st["reasons"]:
                from collections import Counter
                top_reason = Counter(st["reasons"]).most_common(1)[0]
                strat_detail += f" (주요청산: {top_reason[0]}, {top_reason[1]}회)"

        # 수수료 대비 수익 평가
        if total_fee_est > 0:
            fee_ratio = abs(period_pnl) / total_fee_est * 100
            fee_verdict = "✅ 수수료 커버" if period_pnl > 0 else f"❌ 수수료 미달 ({fee_ratio:.0f}%)"
        else:
            fee_verdict = "거래 없음"

        settlement_log = (
            f"\n{'='*60}\n"
            f"📊 정산 리포트 #{epoch} (경과 {elapsed_h:.1f}시간)\n"
            f"{'='*60}\n"
            f"  ■ 이번 구간: {period_count}건 (승 {period_wins} / 패 {period_losses} / 무 {period_even})\n"
            f"  ■ 구간 승률: {period_win_rate:.0f}%\n"
            f"  ■ 구간 손익: {period_pnl:+,.0f}원\n"
            f"  ■ 추정 수수료: {total_fee_est:,.0f}원\n"
            f"  ■ 수수료 평가: {fee_verdict}\n"
            f"  ■ 전략별:{strat_detail}\n"
            f"  ────────────────────────────\n"
            f"  ■ 누적: {cumul_count}건, 손익 {cumul_pnl:+,.0f}원\n"
            f"  ■ 현재가: {self.current_price:,.0f}원\n"
            f"  ■ 추세: {self._market_trend}, RSI={self._rsi:.1f}, FGI={self._fgi}\n"
            f"{'='*60}"
        )
        log.info(settlement_log)

        # DB 기록 — scalp_settlements 테이블
        db_insert("scalp_settlements", {
            "epoch": epoch,
            "elapsed_hours": round(elapsed_h, 2),
            "period_trades": period_count,
            "period_wins": period_wins,
            "period_losses": period_losses,
            "period_win_rate": round(period_win_rate, 2),
            "period_pnl_krw": int(period_pnl),
            "estimated_fee_krw": int(total_fee_est),
            "fee_covered": period_pnl > 0,
            "cumulative_trades": cumul_count,
            "cumulative_pnl_krw": int(cumul_pnl),
            "strategy_stats": json.dumps(
                {s: {"count": st["count"], "wins": st["wins"], "pnl": int(st["pnl"])}
                 for s, st in strategy_stats.items()},
                ensure_ascii=False
            ),
            "market_trend": self._market_trend,
            "rsi_value": round(self._rsi, 2),
            "fgi_value": self._fgi,
            "current_price": int(self.current_price),
            "dry_run": self.dry_run,
            "cycle_id": self.cycle_id,
        })

        # 훈련 일지 — scalp_training_journal 테이블
        # 개선 포인트 자동 도출
        improvements = []
        if period_pnl < 0 and period_count > 0:
            avg_loss = abs(period_pnl) / period_count
            improvements.append(f"건당 평균 손실 {avg_loss:,.0f}원 — 진입 기준 강화 필요")
        if period_win_rate < 40 and period_count >= 3:
            improvements.append(f"승률 {period_win_rate:.0f}% 저조 — 시그널 신뢰도 임계값 상향 검토")
        if total_fee_est > abs(gross_pnl) and period_count > 0:
            improvements.append("총 수수료가 총 변동폭 초과 — 진입 빈도 축소 or 익절폭 확대 필요")
        for s, st in strategy_stats.items():
            s_wr = st["wins"] / max(st["count"], 1) * 100
            if s_wr < 30 and st["count"] >= 3:
                improvements.append(f"[{s}] 승률 {s_wr:.0f}% — 해당 전략 일시 비활성화 검토")

        journal_entry = {
            "epoch": epoch,
            "elapsed_hours": round(elapsed_h, 2),
            "period_summary": f"{period_count}건 {period_pnl:+,.0f}원 (승률 {period_win_rate:.0f}%)",
            "cumulative_summary": f"{cumul_count}건 {cumul_pnl:+,.0f}원",
            "fee_analysis": f"추정수수료 {total_fee_est:,.0f}원, {fee_verdict}",
            "strategy_breakdown": json.dumps(strategy_stats, ensure_ascii=False, default=str),
            "market_context": f"추세={self._market_trend}, RSI={self._rsi:.1f}, FGI={self._fgi}, 가격={self.current_price:,.0f}",
            "improvement_notes": json.dumps(improvements, ensure_ascii=False),
            "dry_run": self.dry_run,
            "cycle_id": self.cycle_id,
        }
        db_insert("scalp_training_journal", journal_entry)

        # 텔레그램 정산 알림
        tg_msg = (
            f"<b>[초단타 6h 정산 #{epoch}]</b>\n"
            f"구간: {period_count}건 | 승률 {period_win_rate:.0f}%\n"
            f"손익: {period_pnl:+,.0f}원 (수수료 {total_fee_est:,.0f}원)\n"
            f"{fee_verdict}\n"
            f"누적: {cumul_count}건 {cumul_pnl:+,.0f}원\n"
        )
        if improvements:
            tg_msg += "\n<b>개선점:</b>\n" + "\n".join(f"• {imp}" for imp in improvements)
        tg_msg += f"\n{'[DRY_RUN]' if self.dry_run else ''}"
        send_telegram(tg_msg)

        # 이전 정산 기준 업데이트 — 정산 완료된 포지션은 메모리에서 해제
        # print_summary()에서 필요한 전체 통계는 cumul_count/cumul_pnl로 이미 추적 중
        # 최근 50건만 유지하여 메모리 누수 방지 (장기 운영 시)
        MAX_CLOSED_KEEP = 50
        if current_count > MAX_CLOSED_KEEP:
            self.closed_positions = self.closed_positions[-MAX_CLOSED_KEEP:]
        self._prev_settled_count = min(self._prev_settled_count, len(self.closed_positions))
        self._prev_settled_pnl = cumul_pnl

    async def strategy_alert_monitor(self):
        """10분마다 주요 지표를 확인하고 전략 변곡점에서 음성 알림"""
        # 알림 쿨다운 (같은 알림 반복 방지, 30분)
        last_alerts: dict[str, float] = {}
        ALERT_COOLDOWN = 1800  # 30분

        while self.running:
            await asyncio.sleep(600)  # 10분 간격
            try:
                now = time.time()

                # 1) RSI 체크 (Upbit API로 1시간봉 조회)
                try:
                    r = _get_http_session().get(
                        f"{UPBIT_API}/candles/minutes/60",
                        params={"market": MARKET, "count": 15},
                        timeout=10,
                    )
                    if r.ok:
                        candles = r.json()
                        closes = [c["trade_price"] for c in reversed(candles)]
                        if len(closes) >= 14:
                            gains = [max(closes[i] - closes[i-1], 0) for i in range(1, len(closes))]
                            losses = [max(closes[i-1] - closes[i], 0) for i in range(1, len(closes))]
                            avg_gain = sum(gains[-14:]) / 14
                            avg_loss = sum(losses[-14:]) / 14
                            rsi = 100 - 100 / (1 + avg_gain / avg_loss) if avg_loss > 0 else 100

                            def _log_alert(atype, msg, val=None):
                                db_insert("strategy_alerts", {
                                    "alert_type": atype,
                                    "message": msg,
                                    "price": int(self.current_price) if self.current_price else None,
                                    "indicator_value": round(val, 2) if val is not None else None,
                                    "sound_played": True,
                                    "telegram_sent": True,
                                })

                            if rsi <= 25 and now - last_alerts.get("rsi_극과매도", 0) > ALERT_COOLDOWN:
                                msg = f"RSI {rsi:.0f}. 극과매도. 매수 타이밍 근접."
                                log.warning(f"[전략 알림] {msg}")
                                sound_alert("비트코인 바닥 근처예요. 살까요?", urgent=True)
                                send_telegram(f"<b>[전략 변곡점]</b> 1시간 RSI {rsi:.1f} 극과매도")
                                _log_alert("rsi_extreme_oversold", msg, rsi)
                                last_alerts["rsi_극과매도"] = now
                            elif rsi <= 30 and now - last_alerts.get("rsi_과매도", 0) > ALERT_COOLDOWN:
                                msg = f"RSI {rsi:.0f}. 과매도 진입."
                                log.info(f"[전략 알림] {msg}")
                                sound_alert("비트코인 많이 빠졌어요. 지켜보세요.")
                                _log_alert("rsi_oversold", msg, rsi)
                                last_alerts["rsi_과매도"] = now
                            elif rsi >= 75 and now - last_alerts.get("rsi_과매수", 0) > ALERT_COOLDOWN:
                                msg = f"RSI {rsi:.0f}. 과매수. 매도 고려."
                                log.warning(f"[전략 알림] {msg}")
                                sound_alert("비트코인 너무 올랐어요. 팔까요?", urgent=True)
                                send_telegram(f"<b>[전략 변곡점]</b> 1시간 RSI {rsi:.1f} 과매수")
                                _log_alert("rsi_overbought", msg, rsi)
                                last_alerts["rsi_과매수"] = now
                except Exception:
                    pass

                # 2) 고래 방향 전환 감지
                if len(self.whale_recent) >= 5:
                    recent_5 = list(self.whale_recent)[-5:]
                    buy_whales = sum(1 for w in recent_5 if w.get("side") == "BID")
                    sell_whales = sum(1 for w in recent_5 if w.get("side") == "ASK")

                    if buy_whales >= 4 and now - last_alerts.get("고래매수전환", 0) > ALERT_COOLDOWN:
                        msg = f"고래 매수 전환. 5건 중 {buy_whales}건 매수."
                        log.warning(f"[전략 알림] {msg}")
                        sound_alert("큰손들이 사기 시작했어요. 따라 살까요?", urgent=True)
                        send_telegram(f"<b>[전략 변곡점]</b> 고래 매수 전환 ({buy_whales}/5)")
                        db_insert("strategy_alerts", {"alert_type": "whale_buy_reversal", "message": msg, "price": int(self.current_price), "indicator_value": buy_whales, "sound_played": True, "telegram_sent": True})
                        last_alerts["고래매수전환"] = now
                    elif sell_whales >= 4 and now - last_alerts.get("고래매도전환", 0) > ALERT_COOLDOWN:
                        msg = f"고래 매도 집중. 5건 중 {sell_whales}건 매도."
                        log.info(f"[전략 알림] {msg}")
                        sound_alert("큰손들이 팔고 있어요. 조심하세요.")
                        db_insert("strategy_alerts", {"alert_type": "whale_sell_pressure", "message": msg, "price": int(self.current_price), "indicator_value": sell_whales, "sound_played": True, "telegram_sent": False})
                        last_alerts["고래매도전환"] = now

                # 3) 가격 급변동 (10분 내 1.5% 이상)
                if len(self.price_history) >= 60:
                    # 직접 deque 인덱싱 -- 전체 리스트 생성 방지
                    idx = max(0, len(self.price_history) - 600)
                    price_10m_ago = self.price_history[idx]["price"]
                    change_pct = (self.current_price - price_10m_ago) / price_10m_ago * 100

                    if abs(change_pct) >= 1.5 and now - last_alerts.get("급변동", 0) > ALERT_COOLDOWN:
                        direction = "급등" if change_pct > 0 else "급락"
                        atype = "price_spike" if change_pct > 0 else "price_crash"
                        price_m = self.current_price / 1_000_000
                        msg = f"비트코인 10분 내 {abs(change_pct):.1f}퍼센트 {direction}. 현재 {price_m:.0f}백만."
                        log.warning(f"[전략 알림] {msg}")
                        if change_pct > 0:
                            sound_alert(f"비트코인 갑자기 {abs(change_pct):.1f}퍼센트 올랐어요. 확인해 보세요.", urgent=True)
                        else:
                            sound_alert(f"비트코인 갑자기 {abs(change_pct):.1f}퍼센트 빠졌어요. 확인해 보세요.", urgent=True)
                        send_telegram(f"<b>[급변동]</b> {change_pct:+.1f}% → {self.current_price:,.0f}원")
                        db_insert("strategy_alerts", {"alert_type": atype, "message": msg, "price": int(self.current_price), "indicator_value": round(change_pct, 2), "sound_played": True, "telegram_sent": True})
                        last_alerts["급변동"] = now

                # 4) 심리적 지지선 이탈 (1억원)
                if self.current_price < 100_000_000 and now - last_alerts.get("1억이탈", 0) > ALERT_COOLDOWN:
                    msg = f"비트코인 1억 이탈. 현재 {self.current_price/1_000_000:.1f}백만."
                    log.warning(f"[전략 알림] {msg}")
                    sound_alert("비트코인 1억 깨졌어요. 더 살까요, 기다릴까요?", urgent=True)
                    send_telegram(f"<b>[지지선 이탈]</b> BTC 1억원 하회: {self.current_price:,.0f}원")
                    db_insert("strategy_alerts", {"alert_type": "support_break", "message": msg, "price": int(self.current_price), "sound_played": True, "telegram_sent": True})
                    last_alerts["1억이탈"] = now

                # 5) 뉴스 감성 급변
                if abs(self.news_sentiment_score) >= 0.6 and now - last_alerts.get("뉴스극단", 0) > ALERT_COOLDOWN:
                    direction = "긍정" if self.news_sentiment_score > 0 else "부정"
                    msg = f"뉴스 {direction} 급변. 점수 {self.news_sentiment_score:+.1f}."
                    log.warning(f"[전략 알림] {msg}")
                    if self.news_sentiment_score > 0:
                        sound_alert("좋은 뉴스가 나왔어요. 오를 수 있어요.", urgent=True)
                    else:
                        sound_alert("나쁜 뉴스가 나왔어요. 빠질 수 있어요.", urgent=True)
                    db_insert("strategy_alerts", {"alert_type": "news_extreme", "message": msg, "price": int(self.current_price), "indicator_value": round(self.news_sentiment_score, 2), "sound_played": True, "telegram_sent": False})
                    last_alerts["뉴스극단"] = now

                # 6) 전략 전환 제안 (현재 strategy.md의 활성 전략 기반)
                try:
                    strategy_path = PROJECT_DIR / "strategy.md"
                    if strategy_path.exists():
                        first_lines = strategy_path.read_text()[:200]
                        current_strategy = "conservative"
                        if "보통" in first_lines or "moderate" in first_lines:
                            current_strategy = "moderate"
                        elif "공격적" in first_lines or "aggressive" in first_lines:
                            current_strategy = "aggressive"

                        # FGI 조회 (간단)
                        try:
                            fgi_r = _get_http_session().get("https://api.alternative.me/fng/?limit=1", timeout=5)
                            fgi = int(fgi_r.json()["data"][0]["value"]) if fgi_r.ok else None
                        except Exception:
                            fgi = None

                        if fgi is not None:
                            # 보수적인데 시장이 좋아지면 → 공격적 전환 제안
                            if current_strategy == "conservative" and fgi >= 50 and now - last_alerts.get("전략업", 0) > ALERT_COOLDOWN * 4:
                                voice = f"시장 분위기가 좋아졌어요. 공포지수 {fgi}. 공격적 전략으로 바꿀까요?"
                                log.warning(f"[전략 제안] 보수적 → 공격적 (FGI {fgi})")
                                sound_alert(voice, urgent=True)
                                send_telegram(f"<b>[전략 전환 제안]</b> 보수적 → 공격적?\nFGI: {fgi}")
                                db_insert("strategy_alerts", {"alert_type": "resistance_break", "message": f"전략 전환 제안: 보수적→공격적 (FGI {fgi})", "price": int(self.current_price), "indicator_value": fgi, "sound_played": True, "telegram_sent": True})
                                last_alerts["전략업"] = now

                            elif current_strategy == "conservative" and fgi >= 35 and now - last_alerts.get("전략중립", 0) > ALERT_COOLDOWN * 4:
                                voice = f"공포가 좀 줄었어요. 공포지수 {fgi}. 보통 전략으로 바꿀까요?"
                                log.info(f"[전략 제안] 보수적 → 보통 (FGI {fgi})")
                                sound_alert(voice)
                                send_telegram(f"<b>[전략 전환 제안]</b> 보수적 → 보통?\nFGI: {fgi}")
                                db_insert("strategy_alerts", {"alert_type": "resistance_break", "message": f"전략 전환 제안: 보수적→보통 (FGI {fgi})", "price": int(self.current_price), "indicator_value": fgi, "sound_played": True, "telegram_sent": True})
                                last_alerts["전략중립"] = now

                            # 공격적인데 공포 급증 → 보수적 전환 제안
                            elif current_strategy == "aggressive" and fgi <= 25 and now - last_alerts.get("전략다운", 0) > ALERT_COOLDOWN * 4:
                                voice = f"시장이 무서워지고 있어요. 공포지수 {fgi}. 보수적으로 바꿀까요?"
                                log.warning(f"[전략 제안] 공격적 → 보수적 (FGI {fgi})")
                                sound_alert(voice, urgent=True)
                                send_telegram(f"<b>[전략 전환 제안]</b> 공격적 → 보수적?\nFGI: {fgi}")
                                db_insert("strategy_alerts", {"alert_type": "support_break", "message": f"전략 전환 제안: 공격적→보수적 (FGI {fgi})", "price": int(self.current_price), "indicator_value": fgi, "sound_played": True, "telegram_sent": True})
                                last_alerts["전략다운"] = now

                            elif current_strategy == "moderate" and fgi <= 20 and now - last_alerts.get("전략다운2", 0) > ALERT_COOLDOWN * 4:
                                voice = f"공포가 심해지고 있어요. 공포지수 {fgi}. 보수적으로 바꿀까요?"
                                log.warning(f"[전략 제안] 보통 → 보수적 (FGI {fgi})")
                                sound_alert(voice, urgent=True)
                                send_telegram(f"<b>[전략 전환 제안]</b> 보통 → 보수적?\nFGI: {fgi}")
                                last_alerts["전략다운2"] = now
                except Exception:
                    pass

                # 7) 물타기 vs 손절 판단 (보유 중인 포지션)
                try:
                    # Upbit에서 현재 보유 확인
                    ak = os.getenv("UPBIT_ACCESS_KEY", "")
                    sk = os.getenv("UPBIT_SECRET_KEY", "")
                    if ak and sk and not self.dry_run:
                        payload = {
                            "access_key": ak,
                            "nonce": str(uuid.uuid4()),
                            "timestamp": int(time.time() * 1000),
                        }
                        token = jwt.encode(payload, sk, algorithm="HS256")
                        acct_r = _get_http_session().get(
                            f"{UPBIT_API}/accounts",
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=5,
                        )
                        if acct_r.ok:
                            for coin in acct_r.json():
                                if coin.get("currency") == "BTC" and float(coin.get("balance", 0)) > 0:
                                    avg_price = float(coin.get("avg_buy_price", 0))
                                    if avg_price > 0 and self.current_price > 0:
                                        loss_pct = (self.current_price - avg_price) / avg_price * 100

                                        # -3% ~ -5% 구간: 물타기 vs 손절 제안
                                        if -5 <= loss_pct <= -3 and now - last_alerts.get("물타기판단", 0) > ALERT_COOLDOWN * 2:
                                            # 매수 시그널이 있는지 확인
                                            has_buy_signal = False
                                            if fgi is not None and fgi <= 30:
                                                has_buy_signal = True

                                            if has_buy_signal:
                                                voice = f"비트코인 {abs(loss_pct):.1f}퍼센트 손실이에요. 바닥 신호가 있어요. 물타기 할까요?"
                                                log.warning(f"[물타기 제안] 손실 {loss_pct:.1f}%, 매수 시그널 있음")
                                            else:
                                                voice = f"비트코인 {abs(loss_pct):.1f}퍼센트 손실이에요. 반등 신호가 없어요. 손절할까요?"
                                                log.warning(f"[손절 제안] 손실 {loss_pct:.1f}%, 매수 시그널 없음")

                                            sound_alert(voice, urgent=True)
                                            send_telegram(
                                                f"<b>[물타기/손절 판단]</b>\n"
                                                f"손실: {loss_pct:+.1f}%\n"
                                                f"평균매수가: {avg_price:,.0f}\n"
                                                f"현재가: {self.current_price:,.0f}\n"
                                                f"매수신호: {'있음' if has_buy_signal else '없음'}\n"
                                                f"제안: {'물타기' if has_buy_signal else '손절'}"
                                            )
                                            db_insert("strategy_alerts", {
                                                "alert_type": "support_break",
                                                "message": f"물타기/손절 판단: {loss_pct:+.1f}%, 제안: {'물타기' if has_buy_signal else '손절'}",
                                                "price": int(self.current_price),
                                                "indicator_value": round(loss_pct, 2),
                                                "sound_played": True,
                                                "telegram_sent": True,
                                            })
                                            last_alerts["물타기판단"] = now

                                        # -5% 이하: 긴급 손절 제안
                                        elif loss_pct < -5 and now - last_alerts.get("긴급손절", 0) > ALERT_COOLDOWN * 2:
                                            voice = f"비트코인 {abs(loss_pct):.1f}퍼센트 손실이에요. 더 빠질 수 있어요. 지금 팔까요?"
                                            log.warning(f"[긴급 손절 제안] 손실 {loss_pct:.1f}%")
                                            sound_alert(voice, urgent=True)
                                            send_telegram(
                                                f"<b>[긴급 손절 제안]</b>\n"
                                                f"손실: {loss_pct:+.1f}%\n"
                                                f"평균매수가: {avg_price:,.0f}\n"
                                                f"현재가: {self.current_price:,.0f}"
                                            )
                                            last_alerts["긴급손절"] = now
                except Exception:
                    pass

            except Exception as e:
                log.error(f"전략 알림 모니터 에러: {e}")

    async def run(self):
        """모든 코루틴 실행"""
        mode = "DRY_RUN" if self.dry_run else "LIVE"
        log.info(f"{'='*50}")
        log.info(f"AI 단타 트레이딩 봇 시작 [{mode}]")
        log.info(f"  단타 자금: {SHORT_TERM_BUDGET:,}원")
        log.info(f"  1회 최대: {SHORT_TERM_MAX_TRADE:,}원")
        effective_daily = SHORT_TERM_MAX_DAILY_DRYRUN if self.dry_run else SHORT_TERM_MAX_DAILY
        log.info(f"  일일 한도: {effective_daily}회{' (DRY_RUN 확장)' if self.dry_run else ''}")
        log.info(f"  익절: +{SHORT_TERM_TAKE_PROFIT}% / 손절: -{SHORT_TERM_STOP_LOSS}%")
        log.info(f"  최대 보유: {SHORT_TERM_MAX_HOLD_MIN}분")
        log.info(f"  수수료 왕복: {COMMISSION_PCT*2}%")
        log.info(f"  최소 수익 마진: {MIN_PROFIT_AFTER_FEE}%")
        log.info(f"  [v5] 트레일링: +{TRAILING_STOP_ACTIVATE_PCT}% 활성 / -{TRAILING_STOP_DISTANCE_PCT}% 거리")
        log.info(f"  [v5] 진입 보호: {GRACE_PERIOD_SEC}초 / 모멘텀: {MOMENTUM_MIN_PCT}%")
        log.info(f"  [v5] 고래 기준: {WHALE_THRESHOLD_KRW/10000:.0f}만원 / 비율: {WHALE_RATIO_THRESHOLD:.0%}")
        log.info("  [v5] 뉴스 매수: 비활성 (모니터링 전용)")
        log.info(f"{'='*50}")

        sound_alert("초단타 봇 시작했어요.")

        send_telegram(
            f"<b>[단타봇 시작]</b> {mode}\n"
            f"자금: {SHORT_TERM_BUDGET:,}원\n"
            f"익절: +{SHORT_TERM_TAKE_PROFIT}% / 손절: -{SHORT_TERM_STOP_LOSS}%\n"
            f"최대 보유: {SHORT_TERM_MAX_HOLD_MIN}분"
        )

        tasks = [
            asyncio.create_task(self.ws_combined()),
            asyncio.create_task(self.scan_news()),
            asyncio.create_task(self.strategy_loop()),
            asyncio.create_task(self.status_reporter()),
            asyncio.create_task(self.strategy_alert_monitor()),
            asyncio.create_task(self.settlement_reporter()),
        ]

        # graceful shutdown (Windows에서는 add_signal_handler 미지원)
        loop = asyncio.get_running_loop()
        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda: self.shutdown())
        except NotImplementedError:
            pass  # Windows: Ctrl+C는 KeyboardInterrupt로 처리

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            self.print_summary()

    def shutdown(self):
        log.info("종료 신호 수신 -- 포지션 정리 중...")
        # 보유 포지션 전부 청산
        for pos in list(self.positions):
            self.execute_exit(pos, "봇 종료 -- 강제 청산")
        self.running = False
        # v4: 종료 직전에 세션 요약 DB 기록 (kill -9 방지용 선행 기록)
        try:
            self.print_summary()
        except Exception as e:
            log.error(f"종료 요약 실패: {e}")
        release_lock()

    def print_summary(self):
        """세션 종료 요약 (중복 호출 방지)"""
        if getattr(self, '_summary_done', False):
            return
        self._summary_done = True
        total_trades = self.total_closed_count
        wins = sum(1 for p in self.closed_positions if (p.pnl_pct or 0) > 0)
        losses = sum(1 for p in self.closed_positions if (p.pnl_pct or 0) < 0)
        win_rate = wins / max(total_trades, 1) * 100

        summary = (
            f"\n{'='*50}\n"
            f"세션 요약\n"
            f"{'='*50}\n"
            f"  총 매매: {total_trades}회 (승 {wins} / 패 {losses})\n"
            f"  승률: {win_rate:.0f}%\n"
            f"  누적 손익: {self.daily_pnl:+,.0f}원\n"
            f"  사용 자금: {self.used_budget:,}원\n"
        )

        for p in self.closed_positions:
            summary += (
                f"  [{p.strategy}] {p.entry_price:,.0f} → {p.exit_price:,.0f} "
                f"{p.pnl_pct:+.2f}% | {p.exit_reason}\n"
            )

        log.info(summary)

        # 세션 요약 DB 기록
        whale_count = len(self.whale_recent)
        session_data = {
            "start_time": (self.closed_positions[0].entry_time.isoformat()
                          if self.closed_positions else datetime.now(KST).isoformat()),
            "end_time": datetime.now(KST).isoformat(),
            "mode": "dry_run" if self.dry_run else "live",
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "total_pnl_krw": int(self.daily_pnl),
            "budget": SHORT_TERM_BUDGET,
            "start_price": int(self.price_history[0]["price"]) if self.price_history else None,
            "end_price": int(self.current_price) if self.current_price else None,
            "price_change_pct": round(
                (self.current_price - self.price_history[0]["price"])
                / self.price_history[0]["price"] * 100, 3
            ) if self.price_history and self.current_price else None,
            "whale_count": whale_count,
            "news_sentiment_avg": round(self.news_sentiment_score, 2),
            "cycle_id": self.cycle_id,
        }
        db_insert("scalp_sessions", session_data)

        send_telegram(
            f"<b>[초단타봇 종료]</b>\n"
            f"매매: {total_trades}회 (승률 {win_rate:.0f}%)\n"
            f"손익: {self.daily_pnl:+,.0f}원"
        )

    def print_status(self):
        """현재 상태만 출력 (--status 옵션)"""
        self.current_price = get_current_price()
        print(json.dumps({
            "timestamp": datetime.now(KST).isoformat(),
            "mode": "DRY_RUN" if self.dry_run else "LIVE",
            "current_price": self.current_price,
            "positions": [asdict(p) for p in self.positions],
            "daily_trade_count": self.daily_trade_count,
            "daily_pnl": self.daily_pnl,
            "used_budget": self.used_budget,
            "budget_limit": SHORT_TERM_BUDGET,
            "config": {
                "max_trade": SHORT_TERM_MAX_TRADE,
                "max_daily": SHORT_TERM_MAX_DAILY_DRYRUN if self.dry_run else SHORT_TERM_MAX_DAILY,
                "stop_loss_pct": SHORT_TERM_STOP_LOSS,
                "take_profit_pct": SHORT_TERM_TAKE_PROFIT,
                "max_hold_min": SHORT_TERM_MAX_HOLD_MIN,
                "commission_round_trip": COMMISSION_PCT * 2,
                "min_profit_margin": MIN_PROFIT_AFTER_FEE,
                "spike_threshold": SPIKE_THRESHOLD_PCT,
                "whale_threshold_krw": WHALE_THRESHOLD_KRW,
            },
        }, indent=2, ensure_ascii=False, default=str))


# ── 엔트리 ────────────────────────────────────────────

if __name__ == "__main__":
    # 최우선: EMERGENCY_STOP 확인 — 매매 관련 초기화 전에 차단
    if os.environ.get("EMERGENCY_STOP", "false").lower() == "true":
        print("[EMERGENCY_STOP] 긴급 정지 활성화 — 초단타 봇 시작 중단", file=sys.stderr)
        sys.exit(1)

    dry_run = os.environ.get("DRY_RUN", "true").lower() == "true"

    if "--dry-run" in sys.argv:
        dry_run = True
    elif "--live" in sys.argv:
        dry_run = False

    trader = ShortTermTrader(dry_run=dry_run)

    if "--status" in sys.argv:
        trader.print_status()
        sys.exit(0)

    asyncio.run(trader.run())
