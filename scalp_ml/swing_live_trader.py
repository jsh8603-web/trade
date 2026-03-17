#!/usr/bin/env python3
"""
Swing Live Trader — SwingExitEnv DQN 모델 기반 실전 매매 봇

5분봉 실시간 모니터링 → 진입 신호 감지 → 100만원 매수 → DQN 청산 결정

사용법:
  python scalp_ml/swing_live_trader.py                    # 24시간 실전
  python scalp_ml/swing_live_trader.py --hours 4           # 4시간만
  python scalp_ml/swing_live_trader.py --dry-run            # 시뮬레이션
  python scalp_ml/swing_live_trader.py --amount 500000      # 50만원씩
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone, timedelta
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

# 파일 로그도 추가
_fh = logging.FileHandler(PROJECT_DIR / "logs" / "swing_live.log", encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s"))
log.addHandler(_fh)

import requests

# ── 설정 ──────────────────────────────────────────────
TRADE_AMOUNT = 1_000_000       # 1회 매매 금액 (원)
BAR_MINUTES = 5                # 5분봉
CHECK_INTERVAL = 60            # 1분마다 체크
MAX_HOLD_BARS = 12             # 최대 보유 12봉 = 60분
FEE_PCT = 0.1                  # 왕복 수수료

MODEL_PATH = PROJECT_DIR / "data" / "scalp_models" / "confirmed_swing" / "swing_dqn_r1"

# 진입 조건
ENTRY_MOM_THRESHOLD = 0.15     # 15분 모멘텀 최소
ENTRY_VOL_SPIKE = 1.8          # 거래량 스파이크 최소
ENTRY_RSI_LOW = 35             # RSI 과매도
ENTRY_RSI_HIGH = 65            # RSI 과매수


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
    """진입 신호 확인 — 3중 필터"""
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

    return {
        "direction": direction,
        "mom_15m": round(mom_15m, 3),
        "vol_spike": round(vol_spike, 2),
        "rsi": round(rsi, 1),
        "rsi_extreme": rsi_extreme,
        "price": current,
    }


def _compute_obs_live(entry_price: float, bars_5m: list[dict],
                       hold_bars: int, strategy: int = 0,
                       entry_quality: float = 0.7) -> np.ndarray:
    """실시간 데이터로 관측 벡터 생성 (SwingExitEnv 형식)"""
    prices = [b["close"] for b in bars_5m]
    current = prices[-1]

    pnl_pct = (current / entry_price - 1) * 100

    # 모멘텀
    mom_1 = (prices[-1] / prices[-2] - 1) * 100 if len(prices) >= 2 else 0
    mom_3 = (prices[-1] / prices[-4] - 1) * 100 if len(prices) >= 4 else 0

    # 거래량 비율
    vols = [b["volume"] for b in bars_5m]
    if len(vols) >= 5:
        vol_recent = np.mean(vols[-2:])
        vol_prev = np.mean(vols[-5:-2])
        vol_ratio = min(vol_recent / max(vol_prev, 0.001), 10)
    else:
        vol_ratio = 1.0

    # RSI
    rsi = _compute_rsi(prices)

    # 볼린저밴드 위치
    if len(prices) >= 20:
        sma = np.mean(prices[-20:])
        std = np.std(prices[-20:])
        bb_pos = (current - (sma - 2*std)) / (4*std) if std > 0 else 0.5
        bb_pos = np.clip(bb_pos, 0, 1)
    else:
        bb_pos = 0.5

    # 추세 강도
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
        # 현재가 조회
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


def _execute_sell(dry_run: bool) -> dict | None:
    """매도 실행 (보유 BTC 전량)"""
    if dry_run:
        r = requests.get("https://api.upbit.com/v1/ticker",
                        params={"markets": "KRW-BTC"}, timeout=10)
        price = r.json()[0]["trade_price"] if r.ok else 0
        return {"success": True, "dry_run": True, "price": price}

    try:
        # 보유량 조회
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
        # 전량 매도
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


def main():
    parser = argparse.ArgumentParser(description="Swing Live Trader")
    parser.add_argument("--hours", type=float, default=24, help="실행 시간 (기본: 24시간)")
    parser.add_argument("--amount", type=int, default=TRADE_AMOUNT, help="1회 매매 금액")
    parser.add_argument("--dry-run", action="store_true", help="시뮬레이션 모드")
    parser.add_argument("--model", type=str, default=str(MODEL_PATH), help="모델 경로")
    args = parser.parse_args()

    dry_run = args.dry_run
    amount = args.amount
    run_hours = args.hours
    model_path = args.model

    # 모델 로드
    from stable_baselines3 import DQN
    if not Path(model_path + ".zip").exists():
        log.error(f"모델 파일 없음: {model_path}.zip")
        log.error("먼저 swing_hunter.py로 모델을 훈련하세요.")
        return

    model = DQN.load(model_path)
    log.info(f"모델 로드: {model_path}")

    mode_str = "DRY_RUN" if dry_run else "LIVE"
    log.info("=" * 70)
    log.info(f"Swing Live Trader 시작 [{mode_str}]")
    log.info(f"  매매 금액: {amount:,}원")
    log.info(f"  실행 시간: {run_hours}시간")
    log.info(f"  진입 조건: 모멘텀 {ENTRY_MOM_THRESHOLD}%+ / 거래량 {ENTRY_VOL_SPIKE}x+ / RSI 극단")
    log.info(f"  청산: DQN 모델 결정 (최대 {MAX_HOLD_BARS * BAR_MINUTES}분)")
    log.info("=" * 70)

    _send_telegram(f"Swing Trader 시작 [{mode_str}]\n금액: {amount:,}원\n시간: {run_hours}h")

    # 상태
    in_position = False
    entry_price = 0.0
    entry_time = None
    hold_bars = 0
    total_trades = 0
    total_pnl = 0.0
    wins = 0
    losses = 0

    start_time = time.time()
    end_time = start_time + run_hours * 3600

    while time.time() < end_time:
        try:
            now = datetime.now(KST)

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

            if not in_position:
                # ── 진입 확인 ──
                signal = _check_entry_signal(bars_5m)
                if signal and signal["direction"] == "long":
                    log.info(f"진입 신호 감지! mom={signal['mom_15m']}%, "
                             f"vol={signal['vol_spike']}x, rsi={signal['rsi']}")

                    result = _execute_buy(amount, dry_run)
                    if result and result.get("success"):
                        in_position = True
                        entry_price = current_price
                        entry_time = now
                        hold_bars = 0
                        log.info(f"매수 완료: {current_price:,.0f}원 x {amount:,}원")
                        _send_telegram(
                            f"매수 [{mode_str}]\n"
                            f"가격: {current_price:,.0f}원\n"
                            f"금액: {amount:,}원\n"
                            f"신호: mom={signal['mom_15m']}%, vol={signal['vol_spike']}x"
                        )
                    else:
                        log.warning(f"매수 실패: {result}")

            else:
                # ── 포지션 보유 중 — DQN 결정 ──
                # 5분 경과 확인
                elapsed_min = (now - entry_time).total_seconds() / 60
                hold_bars = int(elapsed_min / BAR_MINUTES)

                pnl_pct = (current_price / entry_price - 1) * 100
                net_pnl = pnl_pct - FEE_PCT

                # 관측 벡터 생성
                obs = _compute_obs_live(entry_price, bars_5m, hold_bars)

                # DQN 예측
                action, _ = model.predict(obs, deterministic=True)
                action = int(action)
                action_name = ["HOLD", "TAKE_PROFIT", "STOP_LOSS"][action]

                # 강제 청산 조건
                force_exit = False
                if hold_bars >= MAX_HOLD_BARS:
                    force_exit = True
                    action_name = "TIMEOUT"
                elif net_pnl <= -0.4:
                    force_exit = True
                    action_name = "FORCED_SL"

                if action in [1, 2] or force_exit:
                    # 청산!
                    result = _execute_sell(dry_run)
                    if result and result.get("success"):
                        total_trades += 1
                        total_pnl += net_pnl
                        if net_pnl > 0:
                            wins += 1
                        else:
                            losses += 1

                        pnl_krw = net_pnl / 100 * amount
                        log.info(f"{'='*50}")
                        log.info(f"청산 [{action_name}]: "
                                 f"PnL={net_pnl:+.3f}% ({pnl_krw:+,.0f}원), "
                                 f"보유={hold_bars*BAR_MINUTES}분")
                        log.info(f"누적: {total_trades}회, "
                                 f"승률={wins/(wins+losses)*100:.1f}%, "
                                 f"총PnL={total_pnl:+.3f}%")
                        log.info(f"{'='*50}")

                        _send_telegram(
                            f"청산 [{action_name}] [{mode_str}]\n"
                            f"PnL: {net_pnl:+.3f}% ({pnl_krw:+,.0f}원)\n"
                            f"보유: {hold_bars*BAR_MINUTES}분\n"
                            f"누적: {total_trades}회 승률{wins/(wins+losses)*100:.1f}%"
                        )

                        in_position = False
                        entry_price = 0
                        entry_time = None
                    else:
                        log.warning(f"매도 실패: {result}")
                else:
                    # HOLD
                    if hold_bars % 2 == 0:  # 10분마다 로그
                        log.info(f"HOLD: PnL={net_pnl:+.3f}%, "
                                 f"보유={hold_bars*BAR_MINUTES}분, "
                                 f"가격={current_price:,.0f}")

        except Exception as e:
            log.error(f"루프 에러: {e}")

        time.sleep(CHECK_INTERVAL)

    # 종료
    elapsed_h = (time.time() - start_time) / 3600
    wr = wins / max(wins + losses, 1) * 100
    total_krw = total_pnl / 100 * amount

    log.info("=" * 70)
    log.info(f"Swing Trader 종료 ({elapsed_h:.1f}시간)")
    log.info(f"  총 거래: {total_trades}회")
    log.info(f"  승률: {wr:.1f}% ({wins}승 {losses}패)")
    log.info(f"  총 순이익: {total_pnl:+.3f}% ({total_krw:+,.0f}원)")
    log.info("=" * 70)

    _send_telegram(
        f"Swing Trader 종료 [{mode_str}]\n"
        f"거래: {total_trades}회\n"
        f"승률: {wr:.1f}%\n"
        f"순이익: {total_pnl:+.3f}% ({total_krw:+,.0f}원)"
    )


if __name__ == "__main__":
    main()
