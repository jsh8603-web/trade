#!/usr/bin/env python3
"""
7년 역사 데이터 특별 훈련 — 위기/반감기/블랙스완 전문 RL 모델

2019-01 ~ 2026-02 BTC 데이터로 다양한 시장 상황을 학습한다.
일반 훈련(최근 180일)과 달리, 7년 전체를 학습하되 이벤트별 가중치를 적용한다.

훈련 전략:
  1. 전체 7년 순차 학습 (기본 PPO)
  2. 위기 상황 강화 학습 (COVID, LUNA, FTX 등 bear_strong 2배 가중)
  3. 레짐별 전문가 모델 (bull/bear/sideways/volatile 각각)
  4. 반감기 전후 패턴 전문 학습

사용법:
  python scripts/train_historical.py                    # 전체 7년 훈련
  python scripts/train_historical.py --mode crisis      # 위기 상황 강화
  python scripts/train_historical.py --mode regime      # 레짐별 전문가
  python scripts/train_historical.py --mode halving     # 반감기 패턴
  python scripts/train_historical.py --steps 500000     # 스텝 수 변경
  python scripts/train_historical.py --algo sac         # 알고리즘 변경
"""

from __future__ import annotations

import io
import json
import logging
import sys
import time
from pathlib import Path

# Windows cp949 방지
if sys.stdout and sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("historical_training")

# ── 데이터 로드 ──────────────────────────────────────────

HISTORICAL_DIR = PROJECT_DIR / "data" / "historical"
MODEL_DIR = PROJECT_DIR / "data" / "rl_models" / "historical"


def load_historical_data(interval: str = "4h") -> list[dict]:
    """수집된 역사 데이터 로드 + 지표 계산"""
    data_file = HISTORICAL_DIR / f"btc_{interval}_2019_2026.json"

    if not data_file.exists():
        print(f"역사 데이터 없음: {data_file}")
        print("먼저 실행: python scripts/collect_historical_btc.py")
        sys.exit(1)

    with open(data_file, "r", encoding="utf-8") as f:
        candles = json.load(f)

    logger.info(f"역사 데이터 로드: {len(candles):,}개 캔들 ({interval})")

    # Binance USDT 데이터를 훈련 환경 형식으로 변환
    # close_krw가 있으면 KRW 사용, 없으면 USDT 그대로
    for c in candles:
        if "close_krw" in c:
            c["close"] = c["close_krw"]
            c["open"] = c["open_krw"]
            c["high"] = c["high_krw"]
            c["low"] = c["low_krw"]
        if "volume_krw" not in c:
            c["volume_krw"] = c.get("volume_usdt", c["volume"])

    # 기술 지표 계산
    from rl_hybrid.rl.data_loader import HistoricalDataLoader
    loader = HistoricalDataLoader()
    candles = loader.compute_indicators(candles)

    return candles


def filter_by_regime(candles: list[dict], regime: str) -> list[dict]:
    """특정 레짐의 캔들만 필터링"""
    return [c for c in candles if c.get("event_regime") == regime]


def filter_by_events(candles: list[dict], event_labels: list[str]) -> list[dict]:
    """특정 이벤트 레이블의 캔들만 필터링"""
    return [c for c in candles if c.get("event_label") in event_labels]


def split_train_eval(candles: list[dict], eval_ratio: float = 0.2):
    """시간순으로 train/eval 분할"""
    split_idx = int(len(candles) * (1 - eval_ratio))
    return candles[:split_idx], candles[split_idx:]


# ── 훈련 모드 ────────────────────────────────────────────

def train_full_history(candles: list[dict], steps: int = 500_000, algo: str = "ppo"):
    """모드 1: 전체 7년 순차 학습"""
    logger.info(f"=== 전체 7년 훈련 시작 (algo={algo}, steps={steps:,}) ===")

    from rl_hybrid.rl.environment import BitcoinTradingEnv
    from rl_hybrid.rl.train import get_trader_class, evaluate

    train_candles, eval_candles = split_train_eval(candles)
    logger.info(f"데이터: train={len(train_candles):,}, eval={len(eval_candles):,}")

    # FGI를 external signal로 변환
    # signals computed from candles but not passed to env (env extracts internally)

    train_env = BitcoinTradingEnv(
        candles=train_candles,
        initial_balance=10_000_000,
    )
    eval_env = BitcoinTradingEnv(
        candles=eval_candles,
        initial_balance=10_000_000,
    )

    TraderClass = get_trader_class(algo)
    model_path = str(MODEL_DIR / f"full_7y_{algo}")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # 기존 모델 이어 학습
    if (Path(model_path + ".zip")).exists():
        logger.info(f"기존 모델 이어 학습: {model_path}")
        trader = TraderClass(env=train_env, model_path=model_path)
    else:
        trader = TraderClass(env=train_env)

    trader.train(
        total_timesteps=steps,
        eval_env=eval_env,
        save_freq=steps // 5,
    )
    trader.save(model_path)

    # 평가
    stats = evaluate(trader, eval_env, episodes=5)
    avg_return = np.mean([s["total_return_pct"] for s in stats])
    avg_sharpe = np.mean([s["sharpe_ratio"] for s in stats])
    avg_mdd = np.mean([s.get("max_drawdown", s.get("max_drawdown_pct", 0)) for s in stats])
    trades = np.mean([s["trade_count"] for s in stats])

    logger.info("=== 전체 7년 훈련 결과 ===")
    logger.info(f"  수익률: {avg_return:+.2f}%")
    logger.info(f"  Sharpe: {avg_sharpe:.3f}")
    logger.info(f"  MDD: {avg_mdd:.2f}%")
    logger.info(f"  거래수: {trades:.0f}")
    logger.info(f"  모델: {model_path}")

    return {
        "mode": "full_history",
        "algo": algo,
        "steps": steps,
        "return_pct": round(avg_return, 2),
        "sharpe": round(avg_sharpe, 3),
        "mdd": round(avg_mdd, 2),
        "trades": int(trades),
        "model_path": model_path,
    }


def train_crisis_focused(candles: list[dict], steps: int = 300_000, algo: str = "ppo"):
    """모드 2: 위기 상황 강화 학습

    bear_strong + volatile 구간을 2배 가중하여 위기 대응력을 키운다.
    """
    logger.info("=== 위기 강화 훈련 시작 ===")

    # 위기 캔들 2배 포함 (데이터 오버샘플링)
    crisis_labels = [
        "covid_crash", "china_crackdown", "luna_crash", "3ac_celsius_crash",
        "ftx_crash", "japan_carry_unwind", "tariff_crash_2025",
    ]
    normal_candles = [c for c in candles if c.get("event_label") not in crisis_labels]
    crisis_candles = [c for c in candles if c.get("event_label") in crisis_labels]

    # 위기 데이터 2배 오버샘플링
    augmented = normal_candles.copy()
    augmented.extend(crisis_candles)
    augmented.extend(crisis_candles)  # 2배
    augmented.sort(key=lambda c: c["timestamp"])

    logger.info(f"위기 캔들: {len(crisis_candles):,}개 (2x 오버샘플링)")
    logger.info(f"전체 훈련 데이터: {len(augmented):,}개")

    from rl_hybrid.rl.environment import BitcoinTradingEnv
    from rl_hybrid.rl.train import get_trader_class, evaluate

    train_candles, eval_candles = split_train_eval(augmented)
    # signals computed from candles but not passed to env (env extracts internally)

    train_env = BitcoinTradingEnv(
        candles=train_candles,
        initial_balance=10_000_000,
    )

    # 평가는 순수 위기 데이터로
    crisis_eval = crisis_candles[-len(crisis_candles)//5:] if len(crisis_candles) > 100 else crisis_candles
    eval_env = BitcoinTradingEnv(
        candles=crisis_eval if len(crisis_eval) > 50 else eval_candles,
        initial_balance=10_000_000,
    )

    TraderClass = get_trader_class(algo)
    model_path = str(MODEL_DIR / f"crisis_{algo}")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    trader = TraderClass(env=train_env)
    trader.train(total_timesteps=steps, eval_env=eval_env, save_freq=steps // 5)
    trader.save(model_path)

    stats = evaluate(trader, eval_env, episodes=5)
    avg_return = np.mean([s["total_return_pct"] for s in stats])
    avg_sharpe = np.mean([s["sharpe_ratio"] for s in stats])

    logger.info("=== 위기 강화 훈련 결과 ===")
    logger.info(f"  수익률: {avg_return:+.2f}%, Sharpe: {avg_sharpe:.3f}")
    logger.info(f"  모델: {model_path}")

    return {
        "mode": "crisis_focused",
        "algo": algo,
        "return_pct": round(avg_return, 2),
        "sharpe": round(avg_sharpe, 3),
        "model_path": model_path,
    }


def train_regime_experts(candles: list[dict], steps: int = 200_000, algo: str = "ppo"):
    """모드 3: 레짐별 전문가 모델 훈련"""
    logger.info("=== 레짐별 전문가 훈련 시작 ===")

    from rl_hybrid.rl.environment import BitcoinTradingEnv
    from rl_hybrid.rl.train import get_trader_class, evaluate

    regimes = ["bull_strong", "bear_strong", "sideways", "volatile"]
    results = {}

    for regime in regimes:
        regime_candles = filter_by_regime(candles, regime)
        if len(regime_candles) < 100:
            logger.warning(f"  {regime}: 데이터 부족 ({len(regime_candles)}개) → 스킵")
            continue

        logger.info(f"\n  === {regime} 전문가 ({len(regime_candles):,}개 캔들) ===")

        train_c, eval_c = split_train_eval(regime_candles)
        if len(train_c) < 50 or len(eval_c) < 20:
            logger.warning(f"  {regime}: 분할 후 데이터 부족 → 스킵")
            continue

        # signals computed from candles but not passed to env

        train_env = BitcoinTradingEnv(
            candles=train_c,
            initial_balance=10_000_000,
        )
        eval_env = BitcoinTradingEnv(
            candles=eval_c,
            initial_balance=10_000_000,
        )

        TraderClass = get_trader_class(algo)
        model_path = str(MODEL_DIR / f"regime_{regime}_{algo}")

        trader = TraderClass(env=train_env)
        regime_steps = min(steps, len(train_c) * 10)  # 데이터 대비 적절한 스텝
        trader.train(total_timesteps=regime_steps, eval_env=eval_env, save_freq=regime_steps // 3)
        trader.save(model_path)

        stats = evaluate(trader, eval_env, episodes=3)
        avg_return = np.mean([s["total_return_pct"] for s in stats])
        avg_sharpe = np.mean([s["sharpe_ratio"] for s in stats])

        results[regime] = {
            "return_pct": round(avg_return, 2),
            "sharpe": round(avg_sharpe, 3),
            "candles": len(regime_candles),
            "model_path": model_path,
        }
        logger.info(f"  {regime}: return={avg_return:+.2f}%, sharpe={avg_sharpe:.3f}")

    logger.info("\n=== 레짐별 전문가 훈련 완료 ===")
    for regime, r in results.items():
        logger.info(f"  {regime}: {r['return_pct']:+.2f}% (sharpe={r['sharpe']:.3f})")

    return {"mode": "regime_experts", "results": results}


def train_halving_pattern(candles: list[dict], steps: int = 200_000, algo: str = "ppo"):
    """모드 4: 반감기 전후 패턴 학습

    반감기 ±6개월 데이터로 반감기 사이클 패턴을 학습한다.
    """
    logger.info("=== 반감기 패턴 훈련 시작 ===")

    halving_events = [
        "halving_2020", "post_halving_consolidation",
        "halving_2024", "post_halving_sideways",
        "pre_halving_correction", "etf_inflow_rally",
    ]

    halving_candles = filter_by_events(candles, halving_events)
    if len(halving_candles) < 100:
        logger.warning(f"반감기 데이터 부족: {len(halving_candles)}개")
        return {"mode": "halving", "status": "skipped"}

    logger.info(f"반감기 관련 데이터: {len(halving_candles):,}개")

    from rl_hybrid.rl.environment import BitcoinTradingEnv
    from rl_hybrid.rl.train import get_trader_class, evaluate

    train_c, eval_c = split_train_eval(halving_candles)
    # signals computed from candles but not passed to env

    train_env = BitcoinTradingEnv(
        candles=train_c,
        initial_balance=10_000_000,
    )
    eval_env = BitcoinTradingEnv(
        candles=eval_c,
        initial_balance=10_000_000,
    )

    TraderClass = get_trader_class(algo)
    model_path = str(MODEL_DIR / f"halving_{algo}")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    trader = TraderClass(env=train_env)
    trader.train(total_timesteps=steps, eval_env=eval_env, save_freq=steps // 5)
    trader.save(model_path)

    stats = evaluate(trader, eval_env, episodes=3)
    avg_return = np.mean([s["total_return_pct"] for s in stats])
    avg_sharpe = np.mean([s["sharpe_ratio"] for s in stats])

    logger.info("=== 반감기 패턴 훈련 결과 ===")
    logger.info(f"  수익률: {avg_return:+.2f}%, Sharpe: {avg_sharpe:.3f}")

    return {
        "mode": "halving_pattern",
        "return_pct": round(avg_return, 2),
        "sharpe": round(avg_sharpe, 3),
        "model_path": model_path,
    }


# ── 헬퍼 ─────────────────────────────────────────────────

def _candles_to_signals(candles: list[dict]) -> list[dict]:
    """캔들의 FGI + 이벤트 정보를 external signal 형식으로 변환"""
    signals = []
    for c in candles:
        signals.append({
            "recorded_at": c["timestamp"],
            "fgi_value": c.get("fgi", 50),
            "news_sentiment": 0,
            "whale_score": 0,
            "funding_rate": 0,
            "long_short_ratio": 1.0,
            "kimchi_premium_pct": 0,
            "macro_score": 0,
            "eth_btc_score": 0,
            "fusion_score": 0,
            "fusion_signal": "neutral",
            "nvt_signal": 0,
            # 이벤트 메타데이터 (환경에서는 무시되지만 로그에 유용)
            "event_label": c.get("event_label", "normal"),
            "event_regime": c.get("event_regime", "sideways"),
        })
    return signals


# ── CLI ──────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="7년 역사 데이터 특별 훈련")
    parser.add_argument("--mode", default="full",
                        choices=["full", "crisis", "regime", "halving", "all"])
    parser.add_argument("--steps", type=int, default=500_000)
    parser.add_argument("--algo", default="ppo", choices=["ppo", "sac", "td3"])
    parser.add_argument("--interval", default="4h", choices=["4h", "1d"])
    args = parser.parse_args()

    candles = load_historical_data(args.interval)

    # 이벤트 통계
    from collections import Counter
    regime_counts = Counter(c.get("event_regime", "unknown") for c in candles)
    event_counts = Counter(c.get("event_label", "unknown") for c in candles)
    print("\n=== 데이터 구성 ===")
    print(f"  전체: {len(candles):,}개 캔들")
    for regime, count in regime_counts.most_common():
        print(f"  {regime}: {count:,}개 ({count/len(candles)*100:.1f}%)")

    results = {}
    start_time = time.time()

    if args.mode in ("full", "all"):
        results["full"] = train_full_history(candles, args.steps, args.algo)

    if args.mode in ("crisis", "all"):
        results["crisis"] = train_crisis_focused(candles, args.steps, args.algo)

    if args.mode in ("regime", "all"):
        results["regime"] = train_regime_experts(candles, args.steps, args.algo)

    if args.mode in ("halving", "all"):
        results["halving"] = train_halving_pattern(candles, args.steps, args.algo)

    elapsed = time.time() - start_time
    print(f"\n=== 전체 훈련 완료 ({elapsed/60:.1f}분) ===")
    print(json.dumps(results, ensure_ascii=False, indent=2))

    # 결과 저장
    result_path = MODEL_DIR / "training_results.json"
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  결과 저장: {result_path}")
