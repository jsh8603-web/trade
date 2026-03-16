#!/usr/bin/env python3
"""Best 모델(54.6%)에서 파인튜닝 — 60%+ 목표, 20라운드"""
import json, time, sys, logging, shutil
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("finetune")

MODEL_DIR = PROJECT / "data" / "scalp_models"
BEST_MODEL = MODEL_DIR / "ppo_exit_best" / "best_model.zip"
TARGET_WIN_RATE = 0.60
MAX_ROUNDS = 20


def finetune_and_eval(round_num, steps, lr, ent_coef, clip_range, n_epochs, batch_size):
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import EvalCallback
    from scalp_ml.scalp_exit_env import ScalpExitEnv
    import numpy as np

    log.info(f"\n{'='*60}")
    log.info(f"FT Round {round_num}: steps={steps}, lr={lr}, ent={ent_coef}, "
             f"clip={clip_range}, epochs={n_epochs}, batch={batch_size}")
    log.info(f"{'='*60}")

    env = ScalpExitEnv()
    eval_env = ScalpExitEnv()

    # 기존 best 모델에서 파인튜닝 (핵심!)
    model = PPO.load(
        str(BEST_MODEL),
        env=env,
        learning_rate=lr,
        ent_coef=ent_coef,
        clip_range=clip_range,
        n_epochs=n_epochs,
        batch_size=batch_size,
    )

    eval_cb = EvalCallback(
        eval_env, n_eval_episodes=200,
        eval_freq=10000,
        best_model_save_path=str(MODEL_DIR / f"ppo_ft_r{round_num}"),
        deterministic=True,
    )

    start = time.time()
    model.learn(total_timesteps=steps, callback=eval_cb, progress_bar=False)
    elapsed = time.time() - start

    # Evaluate best from this round
    best_path = MODEL_DIR / f"ppo_ft_r{round_num}" / "best_model"
    if best_path.with_suffix(".zip").exists():
        model = PPO.load(str(best_path))

    eval2 = ScalpExitEnv()
    pnls = []
    for _ in range(3000):
        obs, _ = eval2.reset()
        done = False
        while not done:
            a, _ = model.predict(obs, deterministic=True)
            obs, _, done, _, info = eval2.step(a)
        if "pnl_pct" in info:
            pnls.append(info["pnl_pct"])

    pnls_arr = np.array(pnls)
    wr = float((pnls_arr > 0).mean())
    avg_pnl = float(pnls_arr.mean())
    profitable = pnls_arr[pnls_arr > 0]
    losing = pnls_arr[pnls_arr <= 0]
    rr = abs(profitable.mean() / losing.mean()) if len(losing) > 0 and losing.mean() != 0 else 0

    result = {
        "round": round_num,
        "win_rate": round(wr, 4),
        "avg_pnl_pct": round(avg_pnl, 4),
        "rr_ratio": round(rr, 2),
        "total_pnl": round(float(pnls_arr.sum()), 2),
        "steps": steps,
        "lr": lr,
        "ent_coef": ent_coef,
        "clip_range": clip_range,
        "n_epochs": n_epochs,
        "batch_size": batch_size,
        "time_sec": round(elapsed),
    }

    log.info(f"  승률: {wr:.1%}, PnL: {avg_pnl:.4f}%, R:R: {rr:.2f}, 시간: {elapsed:.0f}s")

    return result, wr, model


def main():
    if not BEST_MODEL.exists():
        log.error(f"Best 모델 없음: {BEST_MODEL}")
        sys.exit(1)

    log.info(f"파인튜닝 시작: {BEST_MODEL}")
    log.info(f"목표: {TARGET_WIN_RATE:.0%}, 최대 {MAX_ROUNDS}라운드")

    # 파인튜닝 전략:
    # - 작은 lr (1e-5 ~ 5e-4): 기존 학습 파괴 방지
    # - 다양한 entropy: 탐험/활용 균형
    # - 다양한 clip_range: 정책 변화 속도 조절
    # - 긴 steps: 충분한 수렴 시간
    configs = [
        # (steps, lr, ent_coef, clip_range, n_epochs, batch_size)
        # Phase 1: 보수적 파인튜닝 (lr 매우 작음)
        (300000, 5e-5,  0.005, 0.1,  10, 64),
        (300000, 1e-4,  0.01,  0.1,  10, 64),
        (400000, 5e-5,  0.005, 0.15, 10, 64),
        (400000, 1e-4,  0.01,  0.15, 15, 128),
        (500000, 5e-5,  0.005, 0.1,  10, 64),
        # Phase 2: 중간 파인튜닝
        (400000, 2e-4,  0.01,  0.15, 10, 64),
        (500000, 1e-4,  0.005, 0.1,  15, 128),
        (500000, 2e-4,  0.005, 0.15, 10, 64),
        (600000, 1e-4,  0.01,  0.1,  10, 64),
        (400000, 3e-4,  0.005, 0.1,  10, 64),
        # Phase 3: 적극적 파인튜닝
        (500000, 3e-4,  0.01,  0.15, 10, 64),
        (600000, 2e-4,  0.005, 0.1,  15, 128),
        (500000, 5e-4,  0.01,  0.2,  10, 64),
        (700000, 1e-4,  0.005, 0.1,  10, 64),
        (500000, 2e-4,  0.01,  0.1,  20, 256),
        # Phase 4: 마지막 시도
        (800000, 5e-5,  0.003, 0.1,  10, 64),
        (600000, 1e-4,  0.005, 0.15, 15, 128),
        (700000, 2e-4,  0.01,  0.1,  10, 64),
        (500000, 3e-4,  0.005, 0.15, 10, 64),
        (800000, 1e-4,  0.005, 0.1,  10, 64),
    ]

    all_results = []
    best_wr = 0.546  # 이전 최고
    best_model_path = BEST_MODEL

    for i, (steps, lr, ent, clip, epochs, batch) in enumerate(configs[:MAX_ROUNDS]):
        result, wr, model = finetune_and_eval(i + 1, steps, lr, ent, clip, epochs, batch)
        all_results.append(result)

        # Best 갱신 시 모델 업데이트
        if wr > best_wr:
            best_wr = wr
            # 새로운 best 저장
            best_dir = MODEL_DIR / "ppo_exit_best"
            round_dir = MODEL_DIR / f"ppo_ft_r{i+1}"
            best_round_model = round_dir / "best_model.zip"
            if best_round_model.exists():
                shutil.copy2(best_round_model, best_dir / "best_model.zip")
                log.info(f"  ⬆ Best 모델 갱신: {wr:.1%}")
                # 다음 라운드도 이 모델에서 파인튜닝
                best_model_path = best_dir / "best_model.zip"

        # Save progress
        with open(MODEL_DIR / "finetune_results.json", "w") as f:
            json.dump({
                "base_model": "ppo_exit_best (54.6%)",
                "best_win_rate": best_wr,
                "target": TARGET_WIN_RATE,
                "results": all_results,
            }, f, indent=2)

        if wr >= TARGET_WIN_RATE:
            log.info(f"\n🎯🎯🎯 TARGET 달성! FT Round {i+1}: {wr:.1%} >= {TARGET_WIN_RATE:.0%}")
            break

        log.info(f"  현재 최고: {best_wr:.1%} / 목표: {TARGET_WIN_RATE:.0%}")

    log.info(f"\n{'='*60}")
    log.info(f"파인튜닝 완료. 최고 승률: {best_wr:.1%}")
    log.info(f"결과: {MODEL_DIR / 'finetune_results.json'}")
    log.info(f"{'='*60}")


if __name__ == "__main__":
    main()
