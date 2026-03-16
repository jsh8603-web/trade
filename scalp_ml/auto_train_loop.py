#!/usr/bin/env python3
"""승률 60%+ 달성까지 자동 반복 훈련"""
import json, time, sys, logging
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("auto_train")

MODEL_DIR = PROJECT / "data" / "scalp_models"
TARGET_WIN_RATE = 0.60
MAX_ROUNDS = 20

def train_and_eval(round_num, steps, lr, ent_coef, net_arch):
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import EvalCallback
    from scalp_ml.scalp_exit_env import ScalpExitEnv
    import numpy as np

    log.info(f"\n{'='*60}")
    log.info(f"Round {round_num}: steps={steps}, lr={lr}, ent={ent_coef}, arch={net_arch}")
    log.info(f"{'='*60}")

    env = ScalpExitEnv()
    eval_env = ScalpExitEnv()

    model = PPO(
        "MlpPolicy", env,
        learning_rate=lr,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=ent_coef,
        policy_kwargs={"net_arch": net_arch},
        verbose=0,
    )

    eval_cb = EvalCallback(
        eval_env, n_eval_episodes=200,
        eval_freq=10000,
        best_model_save_path=str(MODEL_DIR / f"ppo_exit_r{round_num}"),
        deterministic=True,
    )

    start = time.time()
    model.learn(total_timesteps=steps, callback=eval_cb, progress_bar=False)
    elapsed = time.time() - start

    # Evaluate best model
    best_path = MODEL_DIR / f"ppo_exit_r{round_num}" / "best_model"
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
        "net_arch": str(net_arch),
        "time_sec": round(elapsed),
    }

    log.info(f"  승률: {wr:.1%}, PnL: {avg_pnl:.4f}%, R:R: {rr:.2f}, 시간: {elapsed:.0f}s")

    # Save if best
    if wr >= TARGET_WIN_RATE:
        import shutil
        best_dir = MODEL_DIR / "ppo_exit_best"
        if best_dir.exists():
            shutil.rmtree(best_dir)
        shutil.copytree(MODEL_DIR / f"ppo_exit_r{round_num}", best_dir)
        model.save(str(MODEL_DIR / "ppo_exit_latest"))
        log.info(f"  🎯 TARGET {TARGET_WIN_RATE:.0%} 달성! Best 모델 업데이트")

    return result, wr


def main():
    # Hyperparameter search space
    configs = [
        # (steps, lr, ent_coef, net_arch)
        (400000, 3e-4, 0.02,  [128, 128]),
        (400000, 1e-4, 0.01,  [256, 128]),
        (500000, 3e-4, 0.005, [128, 64, 32]),
        (500000, 2e-4, 0.02,  [256, 256]),
        (600000, 1e-4, 0.01,  [128, 128]),
        (500000, 5e-4, 0.03,  [128, 128]),
        (600000, 3e-4, 0.015, [256, 128, 64]),
        (700000, 2e-4, 0.01,  [256, 256]),
        (500000, 3e-4, 0.02,  [512, 256]),
        (800000, 1e-4, 0.005, [256, 128]),
        # More aggressive exploration
        (500000, 5e-4, 0.05,  [128, 128]),
        (600000, 3e-4, 0.03,  [256, 128]),
        (700000, 2e-4, 0.02,  [128, 128, 64]),
        (500000, 1e-3, 0.01,  [128, 64]),
        (800000, 3e-4, 0.01,  [256, 256, 128]),
        (600000, 5e-4, 0.02,  [256, 128]),
        (500000, 2e-4, 0.03,  [128, 128]),
        (700000, 3e-4, 0.005, [256, 128]),
        (600000, 1e-4, 0.02,  [512, 256]),
        (800000, 2e-4, 0.01,  [256, 256]),
    ]

    all_results = []
    best_wr = 0

    for i, (steps, lr, ent, arch) in enumerate(configs[:MAX_ROUNDS]):
        result, wr = train_and_eval(i + 1, steps, lr, ent, arch)
        all_results.append(result)
        best_wr = max(best_wr, wr)

        # Save progress
        with open(MODEL_DIR / "auto_train_results.json", "w") as f:
            json.dump({"best_win_rate": best_wr, "target": TARGET_WIN_RATE, "results": all_results}, f, indent=2)

        if wr >= TARGET_WIN_RATE:
            log.info(f"\n🎯🎯🎯 TARGET 달성! Round {i+1}: {wr:.1%} >= {TARGET_WIN_RATE:.0%}")
            break

        log.info(f"  현재 최고: {best_wr:.1%} / 목표: {TARGET_WIN_RATE:.0%}")

    log.info(f"\n{'='*60}")
    log.info(f"자동 훈련 완료. 최고 승률: {best_wr:.1%}")
    log.info(f"결과: {MODEL_DIR / 'auto_train_results.json'}")
    log.info(f"{'='*60}")


if __name__ == "__main__":
    main()
