#!/usr/bin/env python3
"""
Swing Live Trader — SwingExitEnv DQN 모델 기반 실전 매매 봇

5분봉 실시간 모니터링 → 진입 신호 감지 → 매수 → DQN 청산 결정
최대 2개 동시 포지션, 일 최대 20회, 기회 좋으면 2배 배팅

사용법:
  python scalp_ml/swing_live_trader.py --dry-run              # 시뮬레이션
  python scalp_ml/swing_live_trader.py --hours 24              # 24시간 실전
  python scalp_ml/swing_live_trader.py --amount 1000000        # 100만원
  python scalp_ml/swing_live_trader.py --forever --dry-run     # 무한 실행
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# Windows cp949 → UTF-8
for stream in [sys.stdout, sys.stderr]:
    if stream and hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from dotenv import load_dotenv
load_dotenv(PROJECT_DIR / ".env")

KST = timezone(timedelta(hours=9))

# 로깅
log = logging.getLogger("swing_trader")
log.setLevel(logging.INFO)
_h = logging.StreamHandler(sys.stdout)
_h.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s"))
if hasattr(_h.stream, "reconfigure"):
    try:
        _h.stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
log.addHandler(_h)

# 파일 로그
log_dir = PROJECT_DIR / "logs"
log_dir.mkdir(exist_ok=True)
_fh = logging.FileHandler(log_dir / "swing_live.log", encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s"))
log.addHandler(_fh)

import requests

# ── 설정 ──────────────────────────────────────────────
TRADE_AMOUNT = 1_000_000       # 기본 1회 매매 금액 (원)
BAR_MINUTES = 5                # 5분봉
CHECK_INTERVAL = 60            # 1분마다 체크
MAX_HOLD_BARS = 12             # 최대 보유 12봉 = 60분
FEE_PCT = 0.1                  # 왕복 수수료

MODEL_PATH = PROJECT_DIR / "data" / "scalp_models" / "confirmed_swing" / "swing_dqn_r6"

# 진입 조건 — 적극적 설정 (낮은 임계값)
ENTRY_MOM_THRESHOLD = 0.10     # 15분 모멘텀 최소 (적극적: 0.10)
ENTRY_VOL_SPIKE = 1.5          # 거래량 스파이크 최소 (적극적: 1.5)
ENTRY_RSI_LOW = 38             # RSI 과매도 (적극적: 38)
ENTRY_RSI_HIGH = 62            # RSI 과매수 (적극적: 62)

# 멀티 포지션 + 일일 제한
MAX_CONCURRENT_POSITIONS = 2   # 최대 동시 보유 포지션
MAX_DAILY_TRADES = 20          # 일일 최대 매매 횟수
DOUBLE_BET_MULTIPLIER = 2      # 좋은 기회 시 배팅 배수

# 머신 식별
try:
    from utils.machine import get_machine_name
    MACHINE_NAME = get_machine_name()
except Exception:
    MACHINE_NAME = os.environ.get("MACHINE_NAME", "unknown")


# ── 포지션 클래스 ──────────────────────────────────────
class Position:
    """개별 포지션 상태"""
    def __init__(self, entry_price: float, amount: int, signal: dict, pos_id: str = None):
        self.id = pos_id or str(uuid.uuid4())[:8]
        self.entry_price = entry_price
        self.amount = amount
        self.signal = signal
        self.entry_time = datetime.now(KST)
        self.hold_bars = 0


# ── 유틸리티 함수 ──────────────────────────────────────

def _get_upbit_candles(market="KRW-BTC", unit=1, count=30) -> list[dict]:
    """업비트 분봉 조회"""
    url = f"https://api.upbit.com/v1/candles/minutes/{unit}"
    r = requests.get(url, params={"market": market, "count": count}, timeout=10)
    if r.ok:
        return list(reversed(r.json()))  # 시간순 정렬
    return []


def _aggregate_5min_candles(candles_1m: list[dict]) -> list[dict]:
    """1분봉 → 5분봉 집계"""
    bars = []
    for i in range(0, len(candles_1m) - 4, 5):
        chunk = candles_1m[i:i + 5]
        if len(chunk) < 5:
            break
        bars.append({
            "open": chunk[0]["opening_price"],
            "high": max(c["high_price"] for c in chunk),
            "low": min(c["low_price"] for c in chunk),
            "close": chunk[-1]["trade_price"],
            "volume": sum(c["candle_acc_trade_volume"] for c in chunk),
        })
    return bars


def _compute_rsi(prices: list[float], period=14) -> float:
    """RSI 계산"""
    if len(prices) < period + 1:
        return 50.0
    diffs = [prices[i] - prices[i-1] for i in range(-period, 0)]
    gains = [d for d in diffs if d > 0]
    losses = [-d for d in diffs if d < 0]
    avg_g = sum(gains) / period if gains else 0
    avg_l = sum(losses) / period if losses else 0.001
    return 100 - (100 / (1 + avg_g / avg_l))


def _check_entry_signal(bars_5m: list[dict]) -> dict | None:
    """진입 신호 확인 — 3중 필터 (적극적 설정)"""
    if len(bars_5m) < 10:
        return None

    prices = [b["close"] for b in bars_5m]
    current = prices[-1]

    # 1. 15분 모멘텀 (3봉)
    if len(prices) >= 4:
        mom_15m = (prices[-1] / prices[-4] - 1) * 100
    else:
        return None

    if abs(mom_15m) < ENTRY_MOM_THRESHOLD:
        return None

    # 2. 거래량 스파이크
    vols = [b["volume"] for b in bars_5m]
    if len(vols) >= 8:
        vol_avg = np.mean(vols[-8:-3])
        vol_recent = np.mean(vols[-3:])
        vol_spike = vol_recent / max(vol_avg, 0.001)
    else:
        return None

    if vol_spike < ENTRY_VOL_SPIKE:
        return None

    # 3. RSI
    rsi = _compute_rsi(prices)

    # 방향 결정
    direction = "long" if mom_15m > 0 else "short"

    # RSI 극단 가산점
    rsi_extreme = rsi < ENTRY_RSI_LOW or rsi > ENTRY_RSI_HIGH

    # 기회 품질 점수 (0~1) — 2배 배팅 판단용
    quality = 0.5
    if abs(mom_15m) >= 0.3:
        quality += 0.15
    if vol_spike >= 2.5:
        quality += 0.15
    if rsi_extreme:
        quality += 0.2

    return {
        "direction": direction,
        "mom_15m": round(mom_15m, 3),
        "vol_spike": round(vol_spike, 2),
        "rsi": round(rsi, 1),
        "rsi_extreme": rsi_extreme,
        "price": current,
        "quality": round(min(quality, 1.0), 2),
    }


def _compute_obs_live(entry_price: float, bars_5m: list[dict],
                       hold_bars: int, strategy: int = 0,
                       entry_quality: float = 0.7) -> np.ndarray:
    """실시간 데이터로 관측 벡터 생성 (SwingExitEnv 형식)"""
    prices = [b["close"] for b in bars_5m]
    current = prices[-1]

    pnl_pct = (current / entry_price - 1) * 100

    mom_1 = (prices[-1] / prices[-2] - 1) * 100 if len(prices) >= 2 else 0
    mom_3 = (prices[-1] / prices[-4] - 1) * 100 if len(prices) >= 4 else 0

    vols = [b["volume"] for b in bars_5m]
    if len(vols) >= 5:
        vol_recent = np.mean(vols[-2:])
        vol_prev = np.mean(vols[-5:-2])
        vol_ratio = min(vol_recent / max(vol_prev, 0.001), 10)
    else:
        vol_ratio = 1.0

    rsi = _compute_rsi(prices)

    if len(prices) >= 20:
        sma = np.mean(prices[-20:])
        std = np.std(prices[-20:])
        bb_pos = (current - (sma - 2*std)) / (4*std) if std > 0 else 0.5
        bb_pos = np.clip(bb_pos, 0, 1)
    else:
        bb_pos = 0.5

    if len(prices) >= 6:
        sma5_now = np.mean(prices[-5:])
        sma5_prev = np.mean(prices[-6:-1])
        trend = np.clip((sma5_now / sma5_prev - 1) * 100, -1, 1)
    else:
        trend = 0.0

    return np.array([
        np.clip(pnl_pct, -10, 10),
        float(hold_bars),
        np.clip(mom_1, -5, 5),
        np.clip(mom_3, -5, 5),
        vol_ratio,
        rsi,
        float(bb_pos),
        float(strategy),
        float(trend),
        float(entry_quality),
    ], dtype=np.float32)


def _execute_buy(amount: int, dry_run: bool) -> dict | None:
    """매수 실행"""
    if dry_run:
        r = requests.get("https://api.upbit.com/v1/ticker",
                        params={"markets": "KRW-BTC"}, timeout=10)
        price = r.json()[0]["trade_price"] if r.ok else 0
        return {"success": True, "dry_run": True, "price": price, "amount": amount}

    try:
        os.environ['DRY_RUN'] = 'false'
        from scripts.execute_trade import execute
        result = execute('bid', 'KRW-BTC', str(amount))
        os.environ['DRY_RUN'] = 'true'
        return result
    except Exception as e:
        log.error(f"매수 실패: {e}")
        os.environ['DRY_RUN'] = 'true'
        return None


def _execute_sell(dry_run: bool, amount_krw: int = 0) -> dict | None:
    """매도 실행"""
    if dry_run:
        r = requests.get("https://api.upbit.com/v1/ticker",
                        params={"markets": "KRW-BTC"}, timeout=10)
        price = r.json()[0]["trade_price"] if r.ok else 0
        return {"success": True, "dry_run": True, "price": price}

    try:
        from scripts.get_portfolio import get_portfolio
        portfolio = get_portfolio()
        btc_holding = None
        for h in portfolio.get("holdings", []):
            if h["currency"] == "BTC":
                btc_holding = h
                break

        if not btc_holding or btc_holding["balance"] < 0.00001:
            log.warning("매도할 BTC 없음")
            return None

        os.environ['DRY_RUN'] = 'false'
        from scripts.execute_trade import execute
        result = execute('ask', 'KRW-BTC', str(btc_holding["balance"]))
        os.environ['DRY_RUN'] = 'true'
        return result
    except Exception as e:
        log.error(f"매도 실패: {e}")
        os.environ['DRY_RUN'] = 'true'
        return None


def _send_telegram(msg: str):
    """텔레그램 알림"""
    try:
        from scripts.notify_telegram import send_message
        send_message(msg)
    except Exception:
        pass


def _save_trade_to_db(trade_data: dict):
    """매매 기록을 Supabase decisions 테이블에 저장"""
    try:
        from scripts.save_decision import save_decision
        save_decision(trade_data)
        log.info(f"DB 기록 완료 (machine={MACHINE_NAME})")
    except Exception as e:
        log.warning(f"DB 기록 실패: {e}")


def main():
    parser = argparse.ArgumentParser(description="Swing Live Trader")
    parser.add_argument("--hours", type=float, default=0, help="실행 시간 (0=무한)")
    parser.add_argument("--amount", type=int, default=TRADE_AMOUNT, help="기본 1회 매매 금액")
    parser.add_argument("--dry-run", action="store_true", help="시뮬레이션 모드")
    parser.add_argument("--model", type=str, default=str(MODEL_PATH), help="모델 경로")
    parser.add_argument("--forever", action="store_true", help="무한 실행 (hours=0과 동일)")
    parser.add_argument("--max-positions", type=int, default=MAX_CONCURRENT_POSITIONS,
                        help=f"최대 동시 포지션 (기본: {MAX_CONCURRENT_POSITIONS})")
    parser.add_argument("--max-daily", type=int, default=MAX_DAILY_TRADES,
                        help=f"일일 최대 매매 (기본: {MAX_DAILY_TRADES})")
    parser.add_argument("--aggressive", action="store_true", default=True,
                        help="적극적 진입 (기본: True)")
    args = parser.parse_args()

    dry_run = args.dry_run
    base_amount = args.amount
    run_hours = args.hours
    model_path = args.model
    forever = args.forever or (run_hours == 0)
    max_positions = args.max_positions
    max_daily = args.max_daily

    # 모델 로드
    from stable_baselines3 import DQN
    model_zip = model_path if model_path.endswith(".zip") else model_path + ".zip"
    if not Path(model_zip).exists():
        log.error(f"모델 파일 없음: {model_zip}")
        return

    model = DQN.load(model_path.replace(".zip", "") if model_path.endswith(".zip") else model_path)
    log.info(f"모델 로드: {model_path}")

    mode_str = "DRY_RUN" if dry_run else "LIVE"
    run_str = "무한" if forever else f"{run_hours}시간"

    log.info("=" * 70)
    log.info(f"Swing Live Trader 시작 [{mode_str}] [{MACHINE_NAME}]")
    log.info(f"  기본 금액: {base_amount:,}원 (기회 좋으면 x{DOUBLE_BET_MULTIPLIER})")
    log.info(f"  실행: {run_str}")
    log.info(f"  동시 포지션: 최대 {max_positions}개")
    log.info(f"  일일 최대: {max_daily}회")
    log.info(f"  진입: 적극적 (mom>{ENTRY_MOM_THRESHOLD}%, vol>{ENTRY_VOL_SPIKE}x, RSI {ENTRY_RSI_LOW}~{ENTRY_RSI_HIGH})")
    log.info(f"  청산: DQN R6 모델 (최대 {MAX_HOLD_BARS * BAR_MINUTES}분)")
    log.info("=" * 70)

    _send_telegram(
        f"Swing Trader 시작 [{mode_str}] [{MACHINE_NAME}]\n"
        f"금액: {base_amount:,}원 (x{DOUBLE_BET_MULTIPLIER})\n"
        f"실행: {run_str}\n"
        f"동시포지션: {max_positions}개 / 일일 {max_daily}회"
    )

    # ── 상태 ──
    positions: list[Position] = []  # 현재 보유 포지션들
    today_trades = 0                # 오늘 거래 횟수
    today_date = date.today()       # 일일 리셋용
    total_trades = 0
    total_pnl = 0.0
    wins = 0
    losses = 0

    start_time = time.time()
    if forever:
        end_time = float('inf')
    else:
        end_time = start_time + run_hours * 3600

    while time.time() < end_time:
        try:
            now = datetime.now(KST)

            # 일일 카운터 리셋
            if date.today() != today_date:
                log.info(f"일일 리셋: {today_date} -> {date.today()} (어제 {today_trades}회)")
                today_trades = 0
                today_date = date.today()

            # 1분봉 30개 수집 → 5분봉 변환
            candles = _get_upbit_candles(count=30)
            if not candles:
                log.warning("캔들 데이터 수집 실패")
                time.sleep(CHECK_INTERVAL)
                continue

            bars_5m = _aggregate_5min_candles(candles)
            if len(bars_5m) < 5:
                time.sleep(CHECK_INTERVAL)
                continue

            current_price = candles[-1]["trade_price"]

            # ── 1. 기존 포지션 관리 (청산 판단) ──
            closed_positions = []
            for pos in positions:
                elapsed_min = (now - pos.entry_time).total_seconds() / 60
                pos.hold_bars = int(elapsed_min / BAR_MINUTES)

                pnl_pct = (current_price / pos.entry_price - 1) * 100
                net_pnl = pnl_pct - FEE_PCT

                obs = _compute_obs_live(pos.entry_price, bars_5m, pos.hold_bars,
                                         entry_quality=pos.signal.get("quality", 0.7))
                action, _ = model.predict(obs, deterministic=True)
                action = int(action)
                action_name = ["HOLD", "TAKE_PROFIT", "STOP_LOSS"][action]

                force_exit = False
                if pos.hold_bars >= MAX_HOLD_BARS:
                    force_exit = True
                    action_name = "TIMEOUT"
                elif net_pnl <= -0.4:
                    force_exit = True
                    action_name = "FORCED_SL"

                if action in [1, 2] or force_exit:
                    # 청산
                    result = _execute_sell(dry_run, pos.amount)
                    if result and result.get("success"):
                        total_trades += 1
                        total_pnl += net_pnl
                        if net_pnl > 0:
                            wins += 1
                        else:
                            losses += 1

                        pnl_krw = net_pnl / 100 * pos.amount
                        wr = wins / max(wins + losses, 1) * 100

                        log.info(f"{'='*50}")
                        log.info(f"[{pos.id}] 청산 [{action_name}]: "
                                 f"PnL={net_pnl:+.3f}% ({pnl_krw:+,.0f}원), "
                                 f"투입={pos.amount:,}원, 보유={pos.hold_bars * BAR_MINUTES}분")
                        log.info(f"누적: {total_trades}회, 승률={wr:.1f}%, "
                                 f"총PnL={total_pnl:+.3f}%")
                        log.info(f"{'='*50}")

                        _send_telegram(
                            f"청산 [{action_name}] [{mode_str}] [{MACHINE_NAME}]\n"
                            f"PnL: {net_pnl:+.3f}% ({pnl_krw:+,.0f}원)\n"
                            f"투입: {pos.amount:,}원 / 보유: {pos.hold_bars * BAR_MINUTES}분\n"
                            f"누적: {total_trades}회 승률{wr:.1f}%"
                        )

                        # DB 기록
                        _save_trade_to_db({
                            "market": "KRW-BTC",
                            "decision": "sell",
                            "confidence": round(pos.signal.get("quality", 0.7), 2),
                            "reason": (f"Swing DQN R6 [{action_name}] "
                                       f"PnL={net_pnl:+.3f}% hold={pos.hold_bars * BAR_MINUTES}min "
                                       f"machine={MACHINE_NAME}"),
                            "current_price": current_price,
                            "executed": not dry_run,
                            "source": f"swing_dqn_r6_{MACHINE_NAME}",
                            "trade_amount": pos.amount,
                            "market_data_snapshot": json.dumps({
                                "position_id": pos.id,
                                "entry_price": pos.entry_price,
                                "exit_price": current_price,
                                "net_pnl_pct": round(net_pnl, 4),
                                "pnl_krw": round(pnl_krw, 0),
                                "hold_minutes": pos.hold_bars * BAR_MINUTES,
                                "exit_reason": action_name,
                                "signal": pos.signal,
                                "machine": MACHINE_NAME,
                                "dry_run": dry_run,
                            }, ensure_ascii=False),
                        })

                        closed_positions.append(pos)
                    else:
                        log.warning(f"[{pos.id}] 매도 실패")
                else:
                    # HOLD — 10분마다 로그
                    if pos.hold_bars % 2 == 0 and pos.hold_bars > 0:
                        log.info(f"[{pos.id}] HOLD: PnL={net_pnl:+.3f}%, "
                                 f"보유={pos.hold_bars * BAR_MINUTES}분, "
                                 f"투입={pos.amount:,}원")

            # 청산된 포지션 제거
            for cp in closed_positions:
                positions.remove(cp)

            # ── 2. 신규 진입 판단 ──
            can_enter = (
                len(positions) < max_positions and
                today_trades < max_daily
            )

            if can_enter:
                signal = _check_entry_signal(bars_5m)
                if signal and signal["direction"] == "long":
                    # 금액 결정: 기회 좋으면 2배
                    quality = signal.get("quality", 0.5)
                    if quality >= 0.8:
                        trade_amount = base_amount * DOUBLE_BET_MULTIPLIER
                        bet_label = f"x{DOUBLE_BET_MULTIPLIER} 배팅"
                    else:
                        trade_amount = base_amount
                        bet_label = "기본"

                    log.info(f"진입 신호! mom={signal['mom_15m']}%, "
                             f"vol={signal['vol_spike']}x, rsi={signal['rsi']}, "
                             f"quality={quality} [{bet_label}]")

                    result = _execute_buy(trade_amount, dry_run)
                    if result and result.get("success"):
                        pos = Position(current_price, trade_amount, signal)
                        positions.append(pos)
                        today_trades += 1

                        log.info(f"[{pos.id}] 매수: {current_price:,.0f}원 x "
                                 f"{trade_amount:,}원 [{bet_label}] "
                                 f"(포지션 {len(positions)}/{max_positions}, "
                                 f"오늘 {today_trades}/{max_daily})")

                        _send_telegram(
                            f"매수 [{mode_str}] [{MACHINE_NAME}]\n"
                            f"가격: {current_price:,.0f}원\n"
                            f"금액: {trade_amount:,}원 [{bet_label}]\n"
                            f"신호: mom={signal['mom_15m']}%, vol={signal['vol_spike']}x, "
                            f"rsi={signal['rsi']}\n"
                            f"포지션: {len(positions)}/{max_positions} | "
                            f"오늘: {today_trades}/{max_daily}"
                        )

                        # DB 기록
                        _save_trade_to_db({
                            "market": "KRW-BTC",
                            "decision": "buy",
                            "confidence": round(quality, 2),
                            "reason": (f"Swing DQN R6 진입 "
                                       f"mom={signal['mom_15m']}% vol={signal['vol_spike']}x "
                                       f"rsi={signal['rsi']} [{bet_label}] "
                                       f"machine={MACHINE_NAME}"),
                            "current_price": current_price,
                            "executed": not dry_run,
                            "source": f"swing_dqn_r6_{MACHINE_NAME}",
                            "trade_amount": trade_amount,
                            "market_data_snapshot": json.dumps({
                                "position_id": pos.id,
                                "entry_price": current_price,
                                "signal": signal,
                                "bet_label": bet_label,
                                "trade_amount": trade_amount,
                                "positions_count": len(positions),
                                "today_trades": today_trades,
                                "machine": MACHINE_NAME,
                                "dry_run": dry_run,
                            }, ensure_ascii=False),
                        })
                    else:
                        log.warning(f"매수 실패: {result}")

            # 5분마다 상태 요약
            elapsed_min = int((time.time() - start_time) / 60)
            if elapsed_min > 0 and elapsed_min % 5 == 0:
                pos_info = ", ".join(
                    f"[{p.id}] {p.hold_bars * BAR_MINUTES}분 "
                    f"PnL={(current_price / p.entry_price - 1) * 100 - FEE_PCT:+.3f}%"
                    for p in positions
                ) if positions else "없음"
                # 로그는 매 5분 한번만 (중복 방지)
                if elapsed_min % 5 == 0 and (time.time() % 300) < CHECK_INTERVAL + 5:
                    log.info(f"[상태] 포지션: {len(positions)}/{max_positions} | "
                             f"오늘: {today_trades}/{max_daily} | "
                             f"누적: {total_trades}회 | {pos_info}")

        except Exception as e:
            log.error(f"루프 에러: {e}")
            import traceback
            log.error(traceback.format_exc())

        time.sleep(CHECK_INTERVAL)

    # ── 종료 ──
    # 남은 포지션 강제 청산
    for pos in positions:
        pnl_pct = (current_price / pos.entry_price - 1) * 100 if pos.entry_price > 0 else 0
        net_pnl = pnl_pct - FEE_PCT
        log.info(f"[{pos.id}] 종료 강제청산: PnL={net_pnl:+.3f}%")
        result = _execute_sell(dry_run, pos.amount)
        if result and result.get("success"):
            total_trades += 1
            total_pnl += net_pnl
            if net_pnl > 0:
                wins += 1
            else:
                losses += 1

    elapsed_h = (time.time() - start_time) / 3600
    wr = wins / max(wins + losses, 1) * 100
    total_krw = total_pnl / 100 * base_amount

    log.info("=" * 70)
    log.info(f"Swing Trader 종료 ({elapsed_h:.1f}시간) [{MACHINE_NAME}]")
    log.info(f"  총 거래: {total_trades}회")
    log.info(f"  승률: {wr:.1f}% ({wins}승 {losses}패)")
    log.info(f"  총 순이익: {total_pnl:+.3f}% ({total_krw:+,.0f}원)")
    log.info("=" * 70)

    _send_telegram(
        f"Swing Trader 종료 [{mode_str}] [{MACHINE_NAME}]\n"
        f"거래: {total_trades}회\n"
        f"승률: {wr:.1f}%\n"
        f"순이익: {total_pnl:+.3f}% ({total_krw:+,.0f}원)"
    )


if __name__ == "__main__":
    main()
