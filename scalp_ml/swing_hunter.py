#!/usr/bin/env python3
"""
Swing Hunter — 수수료 2배+ 수익 모델 탐색기

5분봉 기반 SwingExitEnv에서 PPO/SAC/DQN을 랜덤 하이퍼파라미터로 훈련,
연속 2회 목표 달성 시 모델 확정.

목표 조건 (모두 충족):
  - 승률 55%+
  - 평균 순이익(수수료 후) 0.2%+ (= 100만원당 2,000원+)
  - R:R 비율 1.5+

사용법:
  python scalp_ml/swing_hunter.py --max-rounds 100
  python scalp_ml/swing_hunter.py --target-wr 0.55 --target-pnl 0.20 --algo ppo
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# Windows cp949 → UTF-8
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv(PROJECT_DIR / ".env")

KST = timezone(timedelta(hours=9))

# 로깅 — UTF-8 강제
log = logging.getLogger("swing_hunter")
log.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s"))
# UTF-8 강제 (cp949 에러 방지)
if hasattr(_handler.stream, "reconfigure"):
    try:
        _handler.stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
log.addHandler(_handler)

# ── 하이퍼파라미터 탐색 공간 ──────────────────────────────

SEARCH_SPACE = {
    "ppo": {
        "steps": [400_000, 600_000, 800_000, 1_000_000],
        "lr": [1e-4, 2e-4, 3e-4, 5e-4, 8e-4],
        "ent_coef": [0.001, 0.005, 0.01, 0.02, 0.05],
        "gamma": [0.95, 0.97, 0.98, 0.99],
        "net_arch": [[64, 64], [128, 64], [128, 64, 32], [256, 128], [256, 128, 64]],
        "batch_size": [64, 128, 256],
        "n_steps": [512, 1024, 2048],
        "clip_range": [0.1, 0.2, 0.3],
    },
    "sac": {
        "steps": [400_000, 600_000, 800_000],
        "lr": [1e-4, 3e-4, 5e-4],
        "gamma": [0.95, 0.98, 0.99, 0.999],
        "net_arch": [[64, 64], [128, 64, 32], [256, 128]],
        "batch_size": [128, 256, 512],
        "tau": [0.005, 0.01, 0.02],
    },
    "dqn": {
        "steps": [400_000, 600_000, 800_000, 1_000_000],
        "lr": [1e-4, 3e-4, 5e-4, 1e-3],
        "gamma": [0.95, 0.97, 0.99],
        "net_arch": [[64, 64], [128, 64], [256, 128]],
        "batch_size": [64, 128, 256],
        "exploration_fraction": [0.1, 0.2, 0.3],
    },
}


def _sample_params(algo: str) -> dict:
    """알고리즘별 랜덤 하이퍼파라미터 샘플링"""
    space = SEARCH_SPACE[algo]
    return {k: random.choice(v) for k, v in space.items()}


def _build_model(algo: str, env, params: dict):
    """알고리즘별 모델 생성"""
    from stable_baselines3 import PPO, DQN
    from stable_baselines3.common.vec_env import DummyVecEnv

    net_arch = params.get("net_arch", [128, 64])
    lr = params.get("lr", 3e-4)
    gamma = params.get("gamma", 0.99)
    batch_size = params.get("batch_size", 128)

    if algo == "ppo":
        return PPO(
            "MlpPolicy", env,
            learning_rate=lr, gamma=gamma,
            n_steps=params.get("n_steps", 1024),
            batch_size=batch_size,
            ent_coef=params.get("ent_coef", 0.01),
            clip_range=params.get("clip_range", 0.2),
            policy_kwargs={"net_arch": net_arch},
            verbose=0,
        )
    elif algo == "sac":
        from stable_baselines3 import SAC
        from scalp_ml.swing_exit_env import SwingExitEnvV2
        # SAC는 연속 행동 공간 필요
        sac_env = SwingExitEnvV2()
        return SAC(
            "MlpPolicy", sac_env,
            learning_rate=lr, gamma=gamma,
            batch_size=batch_size,
            tau=params.get("tau", 0.01),
            policy_kwargs={"net_arch": net_arch},
            verbose=0,
        ), sac_env
    elif algo == "dqn":
        return DQN(
            "MlpPolicy", env,
            learning_rate=lr, gamma=gamma,
            batch_size=batch_size,
            exploration_fraction=params.get("exploration_fraction", 0.2),
            policy_kwargs={"net_arch": net_arch},
            verbose=0,
        )


def _evaluate(model, env, n_episodes: int = 3000, algo: str = "ppo") -> dict:
    """모델 평가 — 승률, 평균 순이익, R:R 계산"""
    wins, losses = 0, 0
    pnl_list = []
    exit_reasons = {}

    for _ in range(n_episodes):
        obs, _ = env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            if algo == "sac":
                obs, reward, done, truncated, info = env.step(action)
            else:
                obs, reward, done, truncated, info = env.step(int(action))
            done = done or truncated

        net_pnl = info.get("net_pnl_pct", 0)
        pnl_list.append(net_pnl)
        if net_pnl > 0:
            wins += 1
        else:
            losses += 1

        reason = info.get("exit_reason", "unknown")
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1

    total = wins + losses
    win_rate = wins / total if total > 0 else 0

    win_pnls = [p for p in pnl_list if p > 0]
    loss_pnls = [abs(p) for p in pnl_list if p < 0]
    avg_win = np.mean(win_pnls) if win_pnls else 0
    avg_loss = np.mean(loss_pnls) if loss_pnls else 0.001
    rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0
    avg_pnl = np.mean(pnl_list) if pnl_list else 0
    profit_factor = sum(win_pnls) / max(sum(loss_pnls), 0.001)

    return {
        "win_rate": round(win_rate * 100, 1),
        "avg_net_pnl": round(avg_pnl, 4),
        "avg_win_pnl": round(avg_win, 4),
        "avg_loss_pnl": round(avg_loss, 4),
        "rr_ratio": round(rr_ratio, 2),
        "profit_factor": round(profit_factor, 2),
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "exit_reasons": exit_reasons,
        "total_net_pnl": round(sum(pnl_list), 2),
        # 100만원 10회 기준 예상 수익
        "est_profit_10trades_krw": round(avg_pnl * 10000 * 10, 0),  # 0.01% = 100원
    }


def _log_to_db(algo: str, params: dict, result: dict, round_num: int):
    """훈련 결과 DB 기록"""
    try:
        from rl_hybrid.rl.rl_db_logger import log_training_start, log_training_complete
        cycle_id = log_training_start(
            algorithm=algo,
            script_name="swing_hunter.py",
            training_config={
                "round": round_num,
                "params": {k: str(v) for k, v in params.items()},
                "env": "SwingExitEnv",
                "bar_minutes": 5,
                "target": "net_pnl_0.2%+",
            },
        )
        if cycle_id:
            log_training_complete(
                cycle_id=cycle_id,
                status="completed",
                metrics={
                    "win_rate": result["win_rate"],
                    "avg_net_pnl": result["avg_net_pnl"],
                    "rr_ratio": result["rr_ratio"],
                    "profit_factor": result["profit_factor"],
                    "est_profit_10trades": result["est_profit_10trades_krw"],
                },
            )
    except Exception as e:
        log.warning(f"DB 기록 실패: {e}")


def main():
    parser = argparse.ArgumentParser(description="Swing Hunter — 수수료 2배+ 수익 모델 탐색")
    parser.add_argument("--target-wr", type=float, default=0.55, help="목표 승률 (기본: 55%%)")
    parser.add_argument("--target-pnl", type=float, default=0.20, help="목표 평균 순이익 %% (기본: 0.20)")
    parser.add_argument("--target-rr", type=float, default=1.5, help="목표 R:R (기본: 1.5)")
    parser.add_argument("--max-rounds", type=int, default=100, help="최대 라운드 수")
    parser.add_argument("--algo", type=str, default="all", choices=["ppo", "sac", "dqn", "all"])
    parser.add_argument("--eval-episodes", type=int, default=3000, help="평가 에피소드 수")
    args = parser.parse_args()

    TARGET_WR = args.target_wr * 100
    TARGET_PNL = args.target_pnl
    TARGET_RR = args.target_rr
    MAX_ROUNDS = args.max_rounds
    EVAL_EPS = args.eval_episodes
    CONSECUTIVE_NEEDED = 2

    algos = ["ppo", "sac", "dqn"] if args.algo == "all" else [args.algo]

    log.info("=" * 70)
    log.info("Swing Hunter - 수수료 2배+ 수익 모델 탐색기")
    log.info(f"  목표 승률: {TARGET_WR}%")
    log.info(f"  목표 순이익: {TARGET_PNL}% (수수료 후)")
    log.info(f"  목표 R:R: {TARGET_RR}")
    log.info(f"  최대 라운드: {MAX_ROUNDS}")
    log.info(f"  알고리즘: {algos}")
    log.info(f"  확정 조건: 승률>{TARGET_WR}% + PnL>{TARGET_PNL}% + R:R>{TARGET_RR} (연속 {CONSECUTIVE_NEEDED}회)")
    log.info(f"  100만원 10회 목표: {TARGET_PNL * 10000 * 10:,.0f}원+ 순이익")
    log.info("=" * 70)

    # 환경 생성
    from scalp_ml.swing_exit_env import SwingExitEnv
    eval_env = SwingExitEnv()
    log.info(f"5분봉 {len(eval_env.bars_5m)}개 로드 완료")

    best_result = None
    best_round = 0
    consecutive_passes = 0
    confirmed = False
    start_time = time.time()

    for round_num in range(1, MAX_ROUNDS + 1):
        algo = random.choice(algos)
        params = _sample_params(algo)
        steps = params.pop("steps")

        log.info("")
        log.info("=" * 70)
        log.info(f"Round {round_num}: algo={algo}, steps={steps:,}, "
                 f"lr={params.get('lr')}, arch={params.get('net_arch')}, "
                 f"gamma={params.get('gamma')}")
        log.info("=" * 70)

        t0 = time.time()

        try:
            # 모델 생성 & 훈련
            if algo == "sac":
                model, train_env = _build_model(algo, None, params)
                model.learn(total_timesteps=steps, progress_bar=False)
                # SAC 평가는 V2 env로
                from scalp_ml.swing_exit_env import SwingExitEnvV2
                sac_eval = SwingExitEnvV2()
                result = _evaluate(model, sac_eval, EVAL_EPS, algo)
            else:
                train_env = SwingExitEnv()
                model = _build_model(algo, train_env, params)
                model.learn(total_timesteps=steps, progress_bar=False)
                result = _evaluate(model, eval_env, EVAL_EPS, algo)

            elapsed = int(time.time() - t0)
            result["elapsed_sec"] = elapsed

            log.info(f"  평가 ({EVAL_EPS} 에피소드)...")
            log.info(f"  결과: 승률={result['win_rate']}%, "
                     f"순이익={result['avg_net_pnl']:+.4f}%, "
                     f"R:R={result['rr_ratio']}, "
                     f"PF={result['profit_factor']}, "
                     f"시간={elapsed}s")
            log.info(f"  청산: {result['exit_reasons']}")
            log.info(f"  100만원x10회 예상: {result['est_profit_10trades_krw']:+,.0f}원")

            # DB 기록
            params["steps"] = steps
            _log_to_db(algo, params, result, round_num)

            # 최고 기록 갱신
            if best_result is None or result["avg_net_pnl"] > best_result["avg_net_pnl"]:
                best_result = result
                best_round = round_num
                log.info(f"  >> 최고 기록 갱신! 순이익={result['avg_net_pnl']:+.4f}% (Round {round_num})")

            # 목표 달성 확인
            passed = (
                result["win_rate"] >= TARGET_WR and
                result["avg_net_pnl"] >= TARGET_PNL and
                result["rr_ratio"] >= TARGET_RR
            )

            if passed:
                consecutive_passes += 1
                log.info(f"  >> 기본 조건 통과! 검증 중... (연속 {consecutive_passes}/{CONSECUTIVE_NEEDED})")

                if consecutive_passes >= CONSECUTIVE_NEEDED:
                    # 확정!
                    confirmed = True
                    save_dir = MODEL_DIR / "confirmed_swing"
                    save_dir.mkdir(parents=True, exist_ok=True)
                    model_path = save_dir / f"swing_{algo}_best"
                    model.save(str(model_path))

                    # 메타데이터 저장
                    meta = {
                        "algo": algo,
                        "params": {k: str(v) for k, v in params.items()},
                        "result": result,
                        "round": round_num,
                        "confirmed_at": datetime.now(KST).isoformat(),
                        "target": {
                            "win_rate": TARGET_WR,
                            "net_pnl": TARGET_PNL,
                            "rr_ratio": TARGET_RR,
                        },
                    }
                    with open(save_dir / "swing_best_meta.json", "w", encoding="utf-8") as f:
                        json.dump(meta, f, indent=2, ensure_ascii=False)

                    log.info("")
                    log.info("=" * 70)
                    log.info(f"  모델 확정! {model_path}")
                    log.info(f"  승률: {result['win_rate']}%")
                    log.info(f"  순이익: {result['avg_net_pnl']:+.4f}%")
                    log.info(f"  R:R: {result['rr_ratio']}")
                    log.info(f"  100만원x10회: {result['est_profit_10trades_krw']:+,.0f}원")
                    log.info("=" * 70)
                    break
            else:
                consecutive_passes = 0

        except Exception as e:
            log.error(f"  Round {round_num} 실패: {e}")
            consecutive_passes = 0
            continue

        # 진행 상황
        elapsed_total = int((time.time() - start_time) / 60)
        log.info(f"  진행: {round_num}/{MAX_ROUNDS} | "
                 f"최고: {best_result['avg_net_pnl']:+.4f}% (R{best_round}) | "
                 f"경과: {elapsed_total}분")

    # 최종 리포트
    total_min = int((time.time() - start_time) / 60)
    log.info("")
    log.info("=" * 70)
    if confirmed:
        log.info(f"훈련 완료: 모델 확정됨 (Round {round_num}, {total_min}분)")
    else:
        log.info(f"훈련 완료: {MAX_ROUNDS}라운드 소진 (미확정, {total_min}분)")
    if best_result:
        log.info(f"최고 기록 (Round {best_round}):")
        log.info(f"  승률: {best_result['win_rate']}%")
        log.info(f"  순이익: {best_result['avg_net_pnl']:+.4f}%")
        log.info(f"  R:R: {best_result['rr_ratio']}")
        log.info(f"  100만원x10회: {best_result['est_profit_10trades_krw']:+,.0f}원")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
