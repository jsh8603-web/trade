#!/usr/bin/env python3
"""
자동 학습 루프 — 단타/초단타 승률 60% 목표

매 사이클(기본 2시간)마다:
1. 최근 DRY_RUN 매매 성과 평가
2. 전략별/시간대별/레짐별 패턴 분석
3. 파라미터 자동 조정 (Bayesian-like hill climbing)
4. RL 청산 모델 재훈련 (성과 악화 시)
5. 새 파라미터 배포 → 트레이더 재시작
6. 진행 상황 DB + 텔레그램 보고

사용법:
  python scripts/auto_learner.py                  # 2시간 주기
  python scripts/auto_learner.py --interval 3600  # 1시간 주기
  python scripts/auto_learner.py --once           # 1회만 실행
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

import requests

# ── 설정 ──────────────────────────────────────────────

PROJECT_DIR = Path(__file__).resolve().parent.parent
PARAM_FILE = PROJECT_DIR / "data" / "auto_learner_params.json"
HISTORY_FILE = PROJECT_DIR / "data" / "auto_learner_history.json"
LOG_FILE = PROJECT_DIR / "logs" / "auto_learner.log"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

TARGET_WIN_RATE = 0.60
MIN_TRADES_FOR_EVAL = 10      # 최소 매매 수
CYCLE_INTERVAL = 7200          # 기본 2시간
MAX_CYCLES = 500               # 최대 반복

# 파라미터 범위 정의
PARAM_RANGES = {
    # 진입 파라미터
    "SPIKE_THRESHOLD_PCT":       {"min": 0.3,  "max": 1.5,  "step": 0.05, "default": 0.8},
    "WHALE_THRESHOLD_KRW":       {"min": 50e6, "max": 500e6,"step": 50e6, "default": 200e6},
    "WHALE_RATIO_THRESHOLD":     {"min": 0.65, "max": 0.95, "step": 0.05, "default": 0.85},
    "MOMENTUM_MIN_PCT":          {"min": 0.02, "max": 0.15, "step": 0.01, "default": 0.06},
    # 청산 파라미터
    "SHORT_TERM_STOP_LOSS":      {"min": 0.10, "max": 0.50, "step": 0.05, "default": 0.25},
    "SHORT_TERM_TAKE_PROFIT":    {"min": 0.15, "max": 0.60, "step": 0.05, "default": 0.30},
    "SHORT_TERM_MAX_HOLD_MIN":   {"min": 5,    "max": 30,   "step": 1,    "default": 15},
    # 트레일링 스탑
    "TRAILING_STOP_ACTIVATE_PCT":{"min": 0.10, "max": 0.50, "step": 0.05, "default": 0.25},
    "TRAILING_STOP_DISTANCE_PCT":{"min": 0.05, "max": 0.30, "step": 0.05, "default": 0.15},
    # 조기 손절
    "EARLY_STOP_LOSS_PCT":       {"min": 0.05, "max": 0.30, "step": 0.05, "default": 0.15},
    "EARLY_STOP_TIME_MIN":       {"min": 2,    "max": 10,   "step": 1,    "default": 5},
    # 안전 필터
    "SELL_PRESSURE_BLOCK_RATIO": {"min": 2.0,  "max": 8.0,  "step": 0.5,  "default": 4.0},
    "NEWS_BLOCK_THRESHOLD":      {"min": -0.8, "max": 0.0,  "step": 0.1,  "default": -0.5},
}

# ── 로깅 ──────────────────────────────────────────────

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("auto_learner")


# ── 유틸리티 ──────────────────────────────────────────

def send_telegram(text: str):
    try:
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
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": f"{text[:3990]}\n{tag}"},
            timeout=10,
        )
    except Exception:
        pass


def db_query(table: str, params: dict = None) -> list:
    """Supabase REST API 쿼리"""
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=HEADERS,
            params=params or {},
            timeout=15,
        )
        if r.ok:
            return r.json()
    except Exception as e:
        log.warning(f"DB 쿼리 실패 ({table}): {e}")
    return []


def db_insert(table: str, row: dict):
    """Supabase REST API 삽입"""
    try:
        from utils.machine import get_machine_name
        row.setdefault("machine_name", get_machine_name())
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers={**HEADERS, "Prefer": "return=minimal"},
            json=row,
            timeout=10,
        )
        if r.status_code == 400 and "machine_name" in r.text:
            row.pop("machine_name", None)
            requests.post(
                f"{SUPABASE_URL}/rest/v1/{table}",
                headers={**HEADERS, "Prefer": "return=minimal"},
                json=row,
                timeout=10,
            )
    except Exception as e:
        log.warning(f"DB 삽입 실패 ({table}): {e}")


def load_params() -> dict:
    """현재 파라미터 로드 (파일 → 기본값)"""
    if PARAM_FILE.exists():
        with open(PARAM_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {k: v["default"] for k, v in PARAM_RANGES.items()}


def save_params(params: dict):
    """파라미터 저장"""
    PARAM_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PARAM_FILE, "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2)


def load_history() -> list:
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history: list):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    # 최근 200개만 유지
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-200:], f, indent=2, default=str)


# ── Phase 1: 성과 평가 ──────────────────────────────

def evaluate_performance(hours: int = 6) -> dict:
    """최근 N시간 DRY_RUN 매매 성과 분석"""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # scalp_trades에서 최근 거래 조회
    trades = db_query("scalp_trades", {
        "select": "strategy,pnl_pct,pnl_krw,confidence,exit_reason,entry_time,exit_time,dry_run",
        "entry_time": f"gte.{since}",
        "order": "entry_time.desc",
        "limit": "200",
    })

    if not trades:
        log.info(f"최근 {hours}시간 매매 기록 없음")
        return {"total": 0, "win_rate": 0, "trades": []}

    # 전체 통계
    total = len(trades)
    wins = sum(1 for t in trades if (t.get("pnl_pct") or 0) > 0)
    losses = total - wins
    win_rate = wins / total if total > 0 else 0

    pnls = [t.get("pnl_pct", 0) or 0 for t in trades]
    avg_pnl = sum(pnls) / len(pnls) if pnls else 0
    total_pnl_krw = sum(t.get("pnl_krw", 0) or 0 for t in trades)

    # 전략별 분석
    strategy_stats = {}
    for t in trades:
        s = t.get("strategy", "unknown")
        if s not in strategy_stats:
            strategy_stats[s] = {"total": 0, "wins": 0, "pnls": []}
        strategy_stats[s]["total"] += 1
        if (t.get("pnl_pct") or 0) > 0:
            strategy_stats[s]["wins"] += 1
        strategy_stats[s]["pnls"].append(t.get("pnl_pct", 0) or 0)

    for s, st in strategy_stats.items():
        st["win_rate"] = st["wins"] / st["total"] if st["total"] > 0 else 0
        st["avg_pnl"] = sum(st["pnls"]) / len(st["pnls"]) if st["pnls"] else 0
        del st["pnls"]

    # exit_reason 분석
    exit_reasons = {}
    for t in trades:
        r = t.get("exit_reason", "unknown")
        if r not in exit_reasons:
            exit_reasons[r] = {"count": 0, "win": 0}
        exit_reasons[r]["count"] += 1
        if (t.get("pnl_pct") or 0) > 0:
            exit_reasons[r]["win"] += 1

    result = {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 4),
        "avg_pnl_pct": round(avg_pnl, 4),
        "total_pnl_krw": total_pnl_krw,
        "strategy_stats": strategy_stats,
        "exit_reasons": exit_reasons,
        "hours": hours,
    }

    log.info(
        f"[평가] {hours}h: {total}건, 승률={win_rate:.1%}, "
        f"평균PnL={avg_pnl:.3f}%, 총PnL={total_pnl_krw:,}원"
    )
    for s, st in strategy_stats.items():
        log.info(f"  {s}: {st['total']}건, 승률={st['win_rate']:.1%}, 평균={st['avg_pnl']:.3f}%")

    return result


# ── Phase 2: 패턴 분석 ──────────────────────────────

def analyze_patterns(eval_result: dict, params: dict) -> dict:
    """승패 패턴 분석 → 조정 방향 결정"""
    recommendations = {}
    win_rate = eval_result.get("win_rate", 0)
    strategy_stats = eval_result.get("strategy_stats", {})
    exit_reasons = eval_result.get("exit_reasons", {})

    # 1. 전체 승률 기반 기본 방향
    if win_rate < 0.30:
        direction = "very_conservative"  # 대폭 보수적
        log.info("[분석] 승률 < 30% → 대폭 보수적 전환")
    elif win_rate < 0.40:
        direction = "conservative"       # 보수적
        log.info("[분석] 승률 < 40% → 보수적 전환")
    elif win_rate < 0.50:
        direction = "slightly_conservative"
        log.info("[분석] 승률 < 50% → 약간 보수적")
    elif win_rate < 0.55:
        direction = "fine_tune"
        log.info("[분석] 승률 50-55% → 미세 조정")
    elif win_rate < TARGET_WIN_RATE:
        direction = "optimize_exit"
        log.info("[분석] 승률 55-60% → 청산 최적화")
    else:
        direction = "maintain"
        log.info(f"[분석] 승률 {win_rate:.1%} ≥ 목표 {TARGET_WIN_RATE:.0%} 달성!")

    recommendations["direction"] = direction

    # 2. 전략별 분석
    weak_strategies = []
    strong_strategies = []
    for s, st in strategy_stats.items():
        if st["total"] >= 3:
            if st["win_rate"] < 0.35:
                weak_strategies.append(s)
            elif st["win_rate"] >= 0.55:
                strong_strategies.append(s)

    recommendations["weak_strategies"] = weak_strategies
    recommendations["strong_strategies"] = strong_strategies

    # 3. exit_reason 분석
    timeout_count = exit_reasons.get("timeout", {}).get("count", 0)
    forced_sl_count = exit_reasons.get("forced_sl", {}).get("count", 0)
    total = eval_result.get("total", 1)

    if timeout_count / max(total, 1) > 0.3:
        recommendations["timeout_too_high"] = True
        log.info(f"  타임아웃 비율 높음: {timeout_count}/{total}")

    if forced_sl_count / max(total, 1) > 0.4:
        recommendations["forced_sl_too_high"] = True
        log.info(f"  강제손절 비율 높음: {forced_sl_count}/{total}")

    # 4. PnL 분포 분석
    avg_pnl = eval_result.get("avg_pnl_pct", 0)
    if avg_pnl < -0.1:
        recommendations["cut_losses_faster"] = True
    elif avg_pnl > 0 and win_rate < 0.50:
        recommendations["few_big_wins"] = True  # 큰 수익이 적은 승률 보전

    return recommendations


# ── Phase 3: 파라미터 조정 ──────────────────────────

def adjust_parameters(params: dict, recommendations: dict, eval_result: dict) -> dict:
    """분석 결과에 따라 파라미터 자동 조정"""
    new_params = copy.deepcopy(params)
    direction = recommendations.get("direction", "maintain")
    changes = []

    def _adjust(key: str, delta: float, reason: str):
        r = PARAM_RANGES[key]
        old = new_params.get(key, r["default"])
        new_val = max(r["min"], min(r["max"], old + delta))
        # step 단위로 반올림
        step = r["step"]
        new_val = round(round(new_val / step) * step, 6)
        if new_val != old:
            new_params[key] = new_val
            changes.append(f"  {key}: {old} → {new_val} ({reason})")

    if direction == "very_conservative":
        # 진입 기준 대폭 강화
        _adjust("SPIKE_THRESHOLD_PCT", +0.15, "진입 기준 강화")
        _adjust("WHALE_THRESHOLD_KRW", +100e6, "고래 기준 강화")
        _adjust("WHALE_RATIO_THRESHOLD", +0.05, "고래 비율 강화")
        _adjust("MOMENTUM_MIN_PCT", +0.02, "모멘텀 기준 강화")
        # 손절 빠르게
        _adjust("SHORT_TERM_STOP_LOSS", -0.05, "빠른 손절")
        _adjust("EARLY_STOP_LOSS_PCT", -0.05, "조기 손절 강화")
        _adjust("SHORT_TERM_MAX_HOLD_MIN", -2, "보유 시간 단축")

    elif direction == "conservative":
        _adjust("SPIKE_THRESHOLD_PCT", +0.10, "진입 기준 강화")
        _adjust("WHALE_RATIO_THRESHOLD", +0.05, "고래 비율 강화")
        _adjust("SHORT_TERM_STOP_LOSS", -0.05, "빠른 손절")
        _adjust("EARLY_STOP_TIME_MIN", -1, "조기 판단")

    elif direction == "slightly_conservative":
        # 약한 전략만 조정
        weak = recommendations.get("weak_strategies", [])
        if "spike" in weak:
            _adjust("SPIKE_THRESHOLD_PCT", +0.05, "spike 승률 낮음")
        if "whale" in weak:
            _adjust("WHALE_RATIO_THRESHOLD", +0.05, "whale 승률 낮음")
        # 일반 조정
        _adjust("SHORT_TERM_STOP_LOSS", -0.05, "약간 빠른 손절")
        _adjust("TRAILING_STOP_ACTIVATE_PCT", -0.05, "트레일링 빨리 활성화")

    elif direction == "fine_tune":
        # 타임아웃 비율이 높으면 TP 낮추기
        if recommendations.get("timeout_too_high"):
            _adjust("SHORT_TERM_TAKE_PROFIT", -0.05, "타임아웃 줄이기")
            _adjust("SHORT_TERM_MAX_HOLD_MIN", +2, "보유 시간 여유")
        # 강제손절 많으면 SL 약간 넓히기
        if recommendations.get("forced_sl_too_high"):
            _adjust("SHORT_TERM_STOP_LOSS", +0.05, "강제손절 완화")
        # 트레일링 최적화
        _adjust("TRAILING_STOP_DISTANCE_PCT", -0.05, "트레일링 타이트")

    elif direction == "optimize_exit":
        # 55% 이상이면 청산 타이밍만 최적화
        _adjust("TRAILING_STOP_ACTIVATE_PCT", -0.05, "빠른 트레일링")
        _adjust("TRAILING_STOP_DISTANCE_PCT", -0.05, "타이트 트레일링")
        if recommendations.get("cut_losses_faster"):
            _adjust("EARLY_STOP_LOSS_PCT", -0.05, "빠른 손절")
            _adjust("EARLY_STOP_TIME_MIN", -1, "조기 판단")

    elif direction == "maintain":
        log.info("[조정] 목표 달성 — 파라미터 유지")

    if changes:
        log.info("[조정] 파라미터 변경:")
        for c in changes:
            log.info(c)
    else:
        log.info("[조정] 변경 없음")

    return new_params


# ── Phase 4: RL 모델 재훈련 ──────────────────────────

def retrain_rl_if_needed(eval_result: dict, params: dict) -> dict:
    """승률이 낮으면 RL 청산 모델 재훈련"""
    win_rate = eval_result.get("win_rate", 0)
    total = eval_result.get("total", 0)

    # 최소 20건 이상이고 승률 45% 미만이면 재훈련
    if total < 20 or win_rate >= 0.45:
        return {"retrained": False, "reason": "조건 미충족"}

    log.info("[재훈련] RL 청산 모델 재훈련 시작...")
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.callbacks import EvalCallback
        from scalp_ml.scalp_exit_env import ScalpExitEnv

        # 새 파라미터로 환경 생성
        env = ScalpExitEnv()
        eval_env = ScalpExitEnv()

        # 기존 모델 로드 시도 (obs space 호환 시)
        model = None
        for mp in [
            PROJECT_DIR / "data" / "scalp_models" / "ppo_auto_best" / "best_model.zip",
            PROJECT_DIR / "data" / "scalp_models" / "ppo_pc36_best" / "best_model.zip",
        ]:
            if mp.exists():
                try:
                    model = PPO.load(str(mp), env=env)
                    log.info(f"  기존 모델 로드 → 증분 학습: {mp.name}")
                    break
                except Exception as e:
                    log.info(f"  모델 {mp.name} 비호환 ({e}), 새로 생성")
                    model = None

        if model is None:
            model = PPO(
                "MlpPolicy", env,
                learning_rate=3e-4, n_steps=1024, batch_size=64,
                n_epochs=10, gamma=0.99, ent_coef=0.02,
                policy_kwargs={"net_arch": [128, 64]},
                verbose=0,
            )
            log.info("  새 모델 생성")

        # 사전 평가
        pre_stats = _quick_eval(model, eval_env, 300)
        log.info(f"  사전: 승률={pre_stats['win_rate']:.1%}, 평균PnL={pre_stats['avg_pnl']:.3f}%")

        # 50K 스텝 증분 학습
        eval_cb = EvalCallback(
            eval_env, n_eval_episodes=200, eval_freq=10000,
            best_model_save_path=str(PROJECT_DIR / "data" / "scalp_models" / "ppo_auto_best"),
            deterministic=True, verbose=0,
        )
        model.learn(total_timesteps=50000, callback=eval_cb, progress_bar=False)

        # 사후 평가
        post_stats = _quick_eval(model, eval_env, 300)
        log.info(f"  사후: 승률={post_stats['win_rate']:.1%}, 평균PnL={post_stats['avg_pnl']:.3f}%")

        # 개선됐으면 저장
        improved = post_stats["win_rate"] > pre_stats["win_rate"] - 0.02
        if improved:
            save_dir = PROJECT_DIR / "data" / "scalp_models"
            model.save(str(save_dir / "ppo_auto_latest"))
            log.info("  모델 저장: ppo_auto_latest")
        else:
            log.info("  성능 하락 → 롤백 (저장 안 함)")

        return {
            "retrained": True,
            "pre_win_rate": round(pre_stats["win_rate"], 4),
            "post_win_rate": round(post_stats["win_rate"], 4),
            "improved": improved,
        }

    except Exception as e:
        log.error(f"[재훈련] 실패: {e}")
        return {"retrained": False, "error": str(e)[:200]}


def _quick_eval(model, env, episodes: int) -> dict:
    """RL 모델 빠른 평가"""
    wins, total_pnl = 0, 0.0
    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        pnl = info.get("pnl_pct", 0)
        if pnl > 0:
            wins += 1
        total_pnl += pnl

    return {
        "win_rate": wins / episodes if episodes > 0 else 0,
        "avg_pnl": total_pnl / episodes if episodes > 0 else 0,
    }


# ── Phase 5: 배포 (트레이더 재시작) ──────────────────

def deploy_params(params: dict):
    """새 파라미터를 환경변수 파일에 쓰고 트레이더 재시작"""
    save_params(params)
    log.info("[배포] 파라미터 저장 완료")

    # 실행 중인 short_term_trader 찾아서 재시작
    try:
        result = subprocess.run(
            ["wmic", "process", "where",
             "name='python.exe' and commandline like '%short_term_trader%'",
             "get", "ProcessId"],
            capture_output=True, text=True, timeout=10,
        )
        pids = [p.strip() for p in result.stdout.split() if p.strip().isdigit()]
        for pid in pids:
            log.info(f"  단타 프로세스 종료: PID {pid}")
            subprocess.run(["taskkill", "/PID", pid, "/F"],
                           capture_output=True, timeout=5)
    except Exception as e:
        log.warning(f"  프로세스 종료 실패: {e}")

    # 1초 대기 후 재시작
    time.sleep(2)
    try:
        python = str(PROJECT_DIR / ".venv" / "Scripts" / "python.exe")
        trader_script = str(PROJECT_DIR / "scripts" / "short_term_trader.py")
        log_path = str(PROJECT_DIR / "logs" / f"short_term_pc36_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

        with open(log_path, "w", encoding="utf-8") as log_f:
            proc = subprocess.Popen(
                [python, "-u", trader_script, "--dry-run"],
                stdout=log_f, stderr=subprocess.STDOUT,
                cwd=str(PROJECT_DIR),
                creationflags=0x08000000,  # CREATE_NO_WINDOW
            )
        log.info(f"  단타 재시작: PID {proc.pid}")
    except Exception as e:
        log.error(f"  재시작 실패: {e}")


# ── Phase 6: 보고 ──────────────────────────────────

def report_cycle(cycle: int, eval_result: dict, recommendations: dict,
                 old_params: dict, new_params: dict, retrain_result: dict):
    """사이클 결과 보고"""
    win_rate = eval_result.get("win_rate", 0)
    total = eval_result.get("total", 0)
    direction = recommendations.get("direction", "unknown")

    # 파라미터 변경 목록
    changes = []
    for k in PARAM_RANGES:
        old_v = old_params.get(k, PARAM_RANGES[k]["default"])
        new_v = new_params.get(k, old_v)
        if old_v != new_v:
            changes.append(f"  {k}: {old_v}→{new_v}")

    # DB 기록
    db_insert("scalp_training_tasks", {
        "task_type": "auto_learner",
        "params": json.dumps({
            "cycle": cycle,
            "direction": direction,
            "changes": changes,
            "new_params": new_params,
        }),
        "status": "completed",
        "result": json.dumps({
            "win_rate": win_rate,
            "total_trades": total,
            "avg_pnl_pct": eval_result.get("avg_pnl_pct", 0),
            "retrain": retrain_result,
        }),
        "priority": 2,
    })

    # 텔레그램
    target_emoji = "🎯" if win_rate >= TARGET_WIN_RATE else "📊"
    msg = (
        f"{target_emoji} [AutoLearner] 사이클 #{cycle}\n"
        f"승률: {win_rate:.1%} / 목표: {TARGET_WIN_RATE:.0%}\n"
        f"매매: {total}건, 평균PnL: {eval_result.get('avg_pnl_pct', 0):.3f}%\n"
        f"방향: {direction}\n"
    )

    if changes:
        msg += "변경:\n" + "\n".join(changes[:5]) + "\n"
    if retrain_result.get("retrained"):
        msg += f"RL: {retrain_result.get('pre_win_rate', 0):.1%}→{retrain_result.get('post_win_rate', 0):.1%}\n"
    if win_rate >= TARGET_WIN_RATE:
        msg += "✅ 목표 달성!"

    send_telegram(msg)

    # 히스토리 저장
    history = load_history()
    history.append({
        "cycle": cycle,
        "timestamp": datetime.now().isoformat(),
        "win_rate": win_rate,
        "total_trades": total,
        "direction": direction,
        "changes_count": len(changes),
        "params": new_params,
    })
    save_history(history)


# ── 메인 루프 ──────────────────────────────────────

def run_cycle(cycle: int) -> bool:
    """1회 학습 사이클. 목표 달성 시 True 반환"""
    log.info(f"\n{'='*60}")
    log.info(f"  AutoLearner 사이클 #{cycle}")
    log.info(f"{'='*60}")

    # Phase 1: 평가
    eval_result = evaluate_performance(hours=6)

    if eval_result["total"] < MIN_TRADES_FOR_EVAL:
        log.info(f"매매 {eval_result['total']}건 < {MIN_TRADES_FOR_EVAL}건 — 평가 불가, 대기")
        # 매매가 적으면 더 넓은 기간 확인
        eval_result = evaluate_performance(hours=24)
        if eval_result["total"] < MIN_TRADES_FOR_EVAL:
            log.info("24시간에도 매매 부족 — 스킵")
            return False

    # 목표 달성 확인
    if eval_result["win_rate"] >= TARGET_WIN_RATE and eval_result["total"] >= 20:
        log.info(f"🎯 목표 달성! 승률 {eval_result['win_rate']:.1%} ≥ {TARGET_WIN_RATE:.0%}")
        send_telegram(
            f"🎯🎯🎯 AutoLearner 목표 달성!\n"
            f"승률: {eval_result['win_rate']:.1%} ({eval_result['total']}건)\n"
            f"평균PnL: {eval_result.get('avg_pnl_pct', 0):.3f}%\n"
            f"사이클: #{cycle}"
        )
        return True

    # Phase 2: 분석
    old_params = load_params()
    recommendations = analyze_patterns(eval_result, old_params)

    # Phase 3: 파라미터 조정
    new_params = adjust_parameters(old_params, recommendations, eval_result)

    # Phase 4: RL 재훈련 (필요 시)
    retrain_result = retrain_rl_if_needed(eval_result, new_params)

    # Phase 5: 배포
    if new_params != old_params:
        deploy_params(new_params)
    else:
        save_params(new_params)  # 기록만

    # Phase 6: 보고
    report_cycle(cycle, eval_result, recommendations, old_params, new_params, retrain_result)

    return False


def main():
    parser = argparse.ArgumentParser(description="자동 학습 루프 — 승률 60% 목표")
    parser.add_argument("--interval", type=int, default=CYCLE_INTERVAL, help="사이클 간격 (초)")
    parser.add_argument("--once", action="store_true", help="1회만 실행")
    parser.add_argument("--max-cycles", type=int, default=MAX_CYCLES, help="최대 사이클")
    args = parser.parse_args()

    log.info(f"AutoLearner 시작 — 목표 승률: {TARGET_WIN_RATE:.0%}, 간격: {args.interval}초")
    send_telegram(f"🤖 AutoLearner 시작\n목표: 승률 {TARGET_WIN_RATE:.0%}\n간격: {args.interval//60}분")

    # short_term_trader가 auto_learner 파라미터를 읽도록 연동 필요
    _patch_trader_params()

    for cycle in range(1, args.max_cycles + 1):
        try:
            achieved = run_cycle(cycle)
            if achieved:
                log.info("목표 달성 — 유지 모드 (6시간 주기 모니터링)")
                if args.once:
                    break
                time.sleep(6 * 3600)  # 목표 달성 후 6시간 대기
                continue

            if args.once:
                break

            log.info(f"다음 사이클까지 {args.interval // 60}분 대기...")
            time.sleep(args.interval)

        except KeyboardInterrupt:
            log.info("사용자 중단")
            break
        except Exception as e:
            log.error(f"사이클 #{cycle} 에러: {e}", exc_info=True)
            time.sleep(300)

    log.info("AutoLearner 종료")


def _patch_trader_params():
    """short_term_trader가 auto_learner 파라미터를 런타임에 읽도록 패치"""
    # auto_learner_params.json 파일이 있으면 트레이더가 우선 사용
    # 이를 위해 트레이더 시작 시 파라미터 로드 로직이 필요
    # → short_term_trader.py에 연동 코드 추가 필요
    params = load_params()
    save_params(params)
    log.info(f"파라미터 파일 준비: {PARAM_FILE}")


if __name__ == "__main__":
    main()
