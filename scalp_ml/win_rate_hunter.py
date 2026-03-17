#!/usr/bin/env python3
"""
단타 승률 60%+ 자동 탐색 훈련 — Win Rate Hunter

연속 검증 60%+ 달성할 때까지 하이퍼파라미터를 랜덤 탐색한다.
PPO/SAC/DQN 3가지 알고리즘, 보상함수 변형 포함.

실행:
  python scalp_ml/win_rate_hunter.py                     # 기본 (60% 목표, 100라운드)
  python scalp_ml/win_rate_hunter.py --target-wr 0.65    # 65% 목표
  python scalp_ml/win_rate_hunter.py --max-rounds 50     # 최대 50라운드
  python scalp_ml/win_rate_hunter.py --algo ppo          # PPO만
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import random
import shutil
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from dotenv import load_dotenv
load_dotenv(PROJECT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT / "logs" / "win_rate_hunt.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("win_rate_hunter")

KST = timezone(timedelta(hours=9))
MODEL_DIR = PROJECT / "data" / "scalp_models"
CONFIRMED_DIR = MODEL_DIR / "confirmed_best"
HUNT_RESULTS = MODEL_DIR / "hunt_results.json"

# ── 탐색 공간 ──────────────────────────────────────────────

ALGO_CHOICES = ["ppo", "sac", "dqn"]

SEARCH_SPACE = {
    "steps":     [400_000, 500_000, 600_000, 700_000, 800_000, 1_000_000],
    "lr":        [5e-5, 1e-4, 2e-4, 3e-4, 5e-4, 7e-4, 1e-3],
    "ent_coef":  [0.001, 0.005, 0.01, 0.015, 0.02, 0.03, 0.05],
    "gamma":     [0.95, 0.97, 0.98, 0.99, 0.995, 0.999],
    "net_arch":  [
        [64, 64], [128, 64], [128, 128], [256, 128],
        [256, 256], [128, 64, 32], [256, 128, 64], [512, 256],
    ],
    "n_steps":   [1024, 2048, 4096],  # PPO only
    "batch_size": [32, 64, 128, 256],
}

EVAL_EPISODES = 3000      # 1차 평가
VERIFY_EPISODES = 3000    # 2차 검증
CONSECUTIVE_NEEDED = 2    # 연속 검증 횟수


def sample_hyperparams(algo: str) -> dict:
    """랜덤 하이퍼파라미터 샘플링"""
    hp = {
        "algo": algo,
        "steps": random.choice(SEARCH_SPACE["steps"]),
        "lr": random.choice(SEARCH_SPACE["lr"]),
        "gamma": random.choice(SEARCH_SPACE["gamma"]),
        "net_arch": random.choice(SEARCH_SPACE["net_arch"]),
        "batch_size": random.choice(SEARCH_SPACE["batch_size"]),
    }
    if algo == "ppo":
        hp["ent_coef"] = random.choice(SEARCH_SPACE["ent_coef"])
        hp["n_steps"] = random.choice(SEARCH_SPACE["n_steps"])
    elif algo == "dqn":
        hp["exploration_fraction"] = random.choice([0.2, 0.3, 0.4, 0.5])
        hp["target_update_interval"] = random.choice([250, 500, 1000])
    return hp


def evaluate(model, env_class, episodes: int, algo: str, hp: dict) -> dict:
    """모델 평가 — 승률, PnL, R:R 계산"""
    env = env_class()
    pnls = []
    holds = []
    exits = {}

    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, done, _, info = env.step(action)
        if "pnl_pct" in info:
            pnls.append(info["pnl_pct"])
            holds.append(info.get("hold_minutes", 0))
            er = info.get("exit_reason", "unknown")
            exits[er] = exits.get(er, 0) + 1

    pnls = np.array(pnls)
    if len(pnls) == 0:
        return {"win_rate": 0, "avg_pnl_pct": 0, "rr_ratio": 0, "total_pnl": 0}

    wins = pnls[pnls > 0]
    losses = pnls[pnls <= 0]
    rr = abs(wins.mean() / losses.mean()) if len(losses) > 0 and losses.mean() != 0 else 0

    return {
        "win_rate": round(float((pnls > 0).mean()), 4),
        "avg_pnl_pct": round(float(pnls.mean()), 4),
        "total_pnl": round(float(pnls.sum()), 2),
        "rr_ratio": round(float(rr), 3),
        "avg_hold_min": round(float(np.mean(holds)), 1) if holds else 0,
        "max_pnl": round(float(pnls.max()), 4),
        "min_pnl": round(float(pnls.min()), 4),
        "std_pnl": round(float(pnls.std()), 4),
        "exit_reasons": exits,
        "episodes": len(pnls),
    }


def train_round(round_num: int, hp: dict) -> tuple[dict, object]:
    """한 라운드 훈련 + 평가"""
    algo = hp["algo"]
    steps = hp["steps"]

    log.info(f"\n{'='*70}")
    log.info(f"Round {round_num}: algo={algo}, steps={steps:,}, lr={hp['lr']}, "
             f"arch={hp['net_arch']}, gamma={hp['gamma']}")
    log.info(f"{'='*70}")

    # 환경 선택
    if algo == "sac":
        from scalp_ml.scalp_exit_env import ScalpExitEnvV2 as EnvClass
    else:
        from scalp_ml.scalp_exit_env import ScalpExitEnv as EnvClass

    env = EnvClass()
    eval_env = EnvClass()

    start = time.time()

    if algo == "ppo":
        from stable_baselines3 import PPO
        from stable_baselines3.common.callbacks import EvalCallback

        model = PPO(
            "MlpPolicy", env,
            learning_rate=hp["lr"],
            n_steps=hp.get("n_steps", 2048),
            batch_size=hp["batch_size"],
            n_epochs=10,
            gamma=hp["gamma"],
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=hp.get("ent_coef", 0.01),
            policy_kwargs={"net_arch": hp["net_arch"]},
            verbose=0,
        )
        eval_cb = EvalCallback(
            eval_env, n_eval_episodes=200, eval_freq=max(10000, steps // 20),
            best_model_save_path=str(MODEL_DIR / f"hunt_r{round_num}"),
            deterministic=True, verbose=0,
        )
        model.learn(total_timesteps=steps, callback=eval_cb, progress_bar=False)

        # best model 로드
        best_path = MODEL_DIR / f"hunt_r{round_num}" / "best_model.zip"
        if best_path.exists():
            model = PPO.load(str(best_path.with_suffix("")))

    elif algo == "sac":
        from stable_baselines3 import SAC
        from stable_baselines3.common.callbacks import EvalCallback

        model = SAC(
            "MlpPolicy", env,
            learning_rate=hp["lr"],
            batch_size=hp["batch_size"],
            gamma=hp["gamma"],
            buffer_size=100000,
            learning_starts=1000,
            tau=0.005,
            policy_kwargs={"net_arch": hp["net_arch"]},
            verbose=0,
        )
        eval_cb = EvalCallback(
            eval_env, n_eval_episodes=200, eval_freq=max(10000, steps // 20),
            best_model_save_path=str(MODEL_DIR / f"hunt_r{round_num}"),
            deterministic=True, verbose=0,
        )
        model.learn(total_timesteps=steps, callback=eval_cb, progress_bar=False)

        best_path = MODEL_DIR / f"hunt_r{round_num}" / "best_model.zip"
        if best_path.exists():
            model = SAC.load(str(best_path.with_suffix("")))

    elif algo == "dqn":
        from stable_baselines3 import DQN
        from stable_baselines3.common.callbacks import EvalCallback

        model = DQN(
            "MlpPolicy", env,
            learning_rate=hp["lr"],
            batch_size=hp["batch_size"],
            gamma=hp["gamma"],
            buffer_size=50000,
            exploration_fraction=hp.get("exploration_fraction", 0.3),
            exploration_final_eps=0.05,
            target_update_interval=hp.get("target_update_interval", 500),
            train_freq=4,
            policy_kwargs={"net_arch": hp["net_arch"]},
            verbose=0,
        )
        eval_cb = EvalCallback(
            eval_env, n_eval_episodes=200, eval_freq=max(5000, steps // 20),
            best_model_save_path=str(MODEL_DIR / f"hunt_r{round_num}"),
            deterministic=True, verbose=0,
        )
        model.learn(total_timesteps=steps, callback=eval_cb, progress_bar=False)

        best_path = MODEL_DIR / f"hunt_r{round_num}" / "best_model.zip"
        if best_path.exists():
            model = DQN.load(str(best_path.with_suffix("")))

    elapsed = time.time() - start

    # 1차 평가
    log.info(f"  1차 평가 ({EVAL_EPISODES} 에피소드)...")
    metrics = evaluate(model, EnvClass, EVAL_EPISODES, algo, hp)
    metrics["round"] = round_num
    metrics["algo"] = algo
    metrics["hyperparams"] = {k: str(v) if isinstance(v, list) else v for k, v in hp.items()}
    metrics["train_time_sec"] = round(elapsed)
    metrics["timestamp"] = datetime.now(KST).isoformat()

    wr = metrics["win_rate"]
    avg_pnl = metrics["avg_pnl_pct"]
    rr = metrics["rr_ratio"]

    log.info(f"  결과: 승률={wr:.1%}, PnL={avg_pnl:+.4f}%, R:R={rr:.2f}, 시간={elapsed:.0f}s")
    log.info(f"  청산: {metrics.get('exit_reasons', {})}")

    return metrics, model


def save_confirmed_model(model, algo: str, hp: dict, metrics: dict, verify_metrics: list[dict]):
    """확정 모델 저장"""
    CONFIRMED_DIR.mkdir(parents=True, exist_ok=True)

    # 모델 파일 저장
    model.save(str(CONFIRMED_DIR / "best_model"))
    log.info(f"  확정 모델 저장: {CONFIRMED_DIR / 'best_model.zip'}")

    # 기존 ppo_exit_best 업데이트 (실전 연결)
    ppo_best = MODEL_DIR / "ppo_exit_best"
    if ppo_best.exists():
        shutil.rmtree(ppo_best)
    ppo_best.mkdir(parents=True, exist_ok=True)
    model.save(str(ppo_best / "best_model"))
    log.info(f"  실전 모델 업데이트: {ppo_best / 'best_model.zip'}")

    # 메타 정보
    info = {
        "algo": algo,
        "hyperparams": {k: str(v) if isinstance(v, list) else v for k, v in hp.items()},
        "final_metrics": metrics,
        "verify_metrics": verify_metrics,
        "confirmed_at": datetime.now(KST).isoformat(),
        "consecutive_passes": len(verify_metrics),
    }
    with open(CONFIRMED_DIR / "model_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    log.info(f"  메타 정보 저장: {CONFIRMED_DIR / 'model_info.json'}")


def record_to_db(metrics: dict, confirmed: bool = False):
    """DB에 훈련 결과 기록"""
    try:
        from rl_hybrid.rl.rl_db_logger import log_training_start, log_training_complete
        cid = log_training_start(
            cycle_type=f"hunt_{'confirmed' if confirmed else 'search'}",
            algorithm=metrics.get("algo", "ppo"),
            module="win_rate_hunter.py",
            training_steps=metrics.get("hyperparams", {}).get("steps"),
            interval="1m",
        )
        if cid:
            log_training_complete(
                cycle_id=cid,
                avg_return_pct=metrics.get("avg_pnl_pct"),
                avg_sharpe=metrics.get("rr_ratio"),
                model_path=str(CONFIRMED_DIR / "best_model") if confirmed else None,
                status="confirmed" if confirmed else "completed",
            )
    except Exception as e:
        log.warning(f"  DB 기록 실패 (비치명적): {e}")


def main():
    parser = argparse.ArgumentParser(description="단타 승률 60%+ 자동 탐색")
    parser.add_argument("--target-wr", type=float, default=0.60, help="목표 승률 (기본 0.60)")
    parser.add_argument("--max-rounds", type=int, default=100, help="최대 라운드 (기본 100)")
    parser.add_argument("--algo", choices=["ppo", "sac", "dqn", "all"], default="all",
                        help="알고리즘 (기본: all)")
    args = parser.parse_args()

    TARGET_WR = args.target_wr
    MAX_ROUNDS = args.max_rounds
    algos = ALGO_CHOICES if args.algo == "all" else [args.algo]

    log.info(f"{'='*70}")
    log.info(f"Win Rate Hunter 시작")
    log.info(f"  목표 승률: {TARGET_WR:.0%}")
    log.info(f"  최대 라운드: {MAX_ROUNDS}")
    log.info(f"  알고리즘: {algos}")
    log.info(f"  확정 조건: 승률≥{TARGET_WR:.0%} + PnL>0 + R:R≥1.0 (연속 {CONSECUTIVE_NEEDED}회)")
    log.info(f"{'='*70}")

    all_results = []
    best_wr = 0
    best_round = 0
    consecutive_passes = 0
    confirmed = False
    confirmed_model = None
    confirmed_hp = None
    verify_results = []

    global_start = time.time()

    for round_num in range(1, MAX_ROUNDS + 1):
        algo = random.choice(algos)
        hp = sample_hyperparams(algo)

        try:
            metrics, model = train_round(round_num, hp)
        except Exception as e:
            log.error(f"  Round {round_num} 실패: {e}")
            all_results.append({"round": round_num, "algo": algo, "error": str(e)})
            continue

        wr = metrics["win_rate"]
        avg_pnl = metrics["avg_pnl_pct"]
        rr = metrics["rr_ratio"]

        # DB 기록
        record_to_db(metrics, confirmed=False)

        # 최고 기록 갱신
        if wr > best_wr:
            best_wr = wr
            best_round = round_num
            log.info(f"  ★ 새 최고 승률: {wr:.1%} (Round {round_num})")

        # 확정 조건 체크: 승률 + PnL + R:R
        passed = (wr >= TARGET_WR and avg_pnl > 0 and rr >= 1.0)

        if passed:
            log.info(f"  ✓ 기본 조건 통과! 검증 평가 시작...")

            # 검증 평가 (별도 환경)
            if algo == "sac":
                from scalp_ml.scalp_exit_env import ScalpExitEnvV2 as VerifyEnv
            else:
                from scalp_ml.scalp_exit_env import ScalpExitEnv as VerifyEnv

            verify = evaluate(model, VerifyEnv, VERIFY_EPISODES, algo, hp)
            verify["round"] = round_num
            verify["type"] = "verify"
            log.info(f"  검증: 승률={verify['win_rate']:.1%}, PnL={verify['avg_pnl_pct']:+.4f}%, R:R={verify['rr_ratio']:.2f}")

            v_passed = (verify["win_rate"] >= TARGET_WR and verify["avg_pnl_pct"] > 0 and verify["rr_ratio"] >= 1.0)

            if v_passed:
                consecutive_passes += 1
                verify_results.append(verify)
                log.info(f"  ✓ 검증 통과! (연속 {consecutive_passes}/{CONSECUTIVE_NEEDED})")

                if consecutive_passes >= CONSECUTIVE_NEEDED:
                    # 확정!
                    confirmed = True
                    confirmed_model = model
                    confirmed_hp = hp
                    metrics["confirmed"] = True

                    log.info(f"\n{'🎯' * 20}")
                    log.info(f"  확정 모델 발견! Round {round_num}")
                    log.info(f"  알고리즘: {algo}")
                    log.info(f"  승률: {wr:.1%} (검증: {verify['win_rate']:.1%})")
                    log.info(f"  PnL: {avg_pnl:+.4f}%")
                    log.info(f"  R:R: {rr:.2f}")
                    log.info(f"{'🎯' * 20}\n")

                    save_confirmed_model(model, algo, hp, metrics, verify_results)
                    record_to_db(metrics, confirmed=True)
            else:
                consecutive_passes = 0
                verify_results = []
                log.info(f"  ✗ 검증 실패 — 연속 카운트 리셋")
        else:
            consecutive_passes = 0
            verify_results = []

        all_results.append(metrics)

        # 진행 상황 저장
        summary = {
            "target_win_rate": TARGET_WR,
            "best_win_rate": best_wr,
            "best_round": best_round,
            "total_rounds": round_num,
            "confirmed": confirmed,
            "elapsed_min": round((time.time() - global_start) / 60, 1),
            "results": all_results,
        }
        with open(HUNT_RESULTS, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        if confirmed:
            break

        # 진행 로그
        elapsed_min = (time.time() - global_start) / 60
        log.info(f"  진행: {round_num}/{MAX_ROUNDS} | 최고: {best_wr:.1%} (R{best_round}) | "
                 f"경과: {elapsed_min:.0f}분")

        # 임시 디렉토리 정리 (디스크 절약)
        hunt_dir = MODEL_DIR / f"hunt_r{round_num}"
        if hunt_dir.exists() and not confirmed:
            shutil.rmtree(hunt_dir, ignore_errors=True)

    # 최종 리포트
    total_min = (time.time() - global_start) / 60
    log.info(f"\n{'='*70}")
    log.info(f"Win Rate Hunter 완료")
    log.info(f"  총 라운드: {len(all_results)}")
    log.info(f"  총 시간: {total_min:.1f}분")
    log.info(f"  최고 승률: {best_wr:.1%} (Round {best_round})")
    log.info(f"  확정: {'YES' if confirmed else 'NO'}")
    if confirmed:
        log.info(f"  확정 모델: {CONFIRMED_DIR / 'best_model.zip'}")
    log.info(f"  결과 파일: {HUNT_RESULTS}")
    log.info(f"{'='*70}")

    # Top 5 출력
    valid = [r for r in all_results if "win_rate" in r]
    if valid:
        top5 = sorted(valid, key=lambda x: x["win_rate"], reverse=True)[:5]
        log.info(f"\nTop 5:")
        for i, r in enumerate(top5, 1):
            log.info(f"  {i}. R{r['round']} {r['algo']}: 승률={r['win_rate']:.1%}, "
                     f"PnL={r['avg_pnl_pct']:+.4f}%, R:R={r['rr_ratio']:.2f}")


if __name__ == "__main__":
    main()
