#!/usr/bin/env python3
"""
RL 파인튜닝 — 연속 20라운드 60% 승률 달성까지 실행

라운드마다:
1. PPO 모델 50K 스텝 학습
2. 500 에피소드 평가
3. 승률 60%+ 연속 카운트
4. 20연속 달성 시 종료
5. 정체 시 하이퍼파라미터/보상함수 자동 변형

사용법:
  python scripts/rl_finetune_60.py
  python scripts/rl_finetune_60.py --target 0.55   # 목표 55%
  python scripts/rl_finetune_60.py --steps 100000   # 라운드당 100K
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_DIR / "data" / "scalp_models"
LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "rl_finetune_60.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("rl_finetune")

TARGET_WIN_RATE = 0.60
TARGET_CONSECUTIVE = 20
EVAL_EPISODES = 500
MAX_ROUNDS = 300

# ── 보상함수 변형들 ──────────────────────────────────

class RewardV1:
    """기본 보상 — 현재 ScalpExitEnv 기본값"""
    name = "v1_base"
    hold_cost = -0.002
    tp_win_mult = 1.5
    tp_loss_mult = 0.8
    sl_bonus = 0.1
    sl_threshold = -0.3
    sl_profit_mult = 0.5
    timeout_mult = 0.8
    forced_sl_mult = 1.2


class RewardV2:
    """승률 중심 — 작은 수익이라도 탈출 보상"""
    name = "v2_winrate"
    hold_cost = -0.005       # 더 강한 시간 벌칙
    tp_win_mult = 2.0        # 수익 청산 보너스 강화
    tp_loss_mult = 0.5       # 손실 청산 벌칙 약화 (빠른 탈출 유도)
    sl_bonus = 0.2           # 손절 보너스 강화
    sl_threshold = -0.15     # 더 작은 손실에서도 보너스
    sl_profit_mult = 0.3     # 수익에서 SL 벌칙 약화
    timeout_mult = 0.5       # 타임아웃 벌칙 강화
    forced_sl_mult = 1.5     # 강제손절 벌칙 강화


class RewardV3:
    """빠른 청산 — HOLD 비용 극대화"""
    name = "v3_fast_exit"
    hold_cost = -0.01        # 매우 강한 시간 벌칙
    tp_win_mult = 2.5        # 수익 보너스 극대화
    tp_loss_mult = 0.3       # 손실 탈출 덜 벌칙
    sl_bonus = 0.3           # 빠른 손절 보상
    sl_threshold = -0.10     # 아주 작은 손실에서도 보상
    sl_profit_mult = 0.2
    timeout_mult = 0.3       # 타임아웃 강한 벌칙
    forced_sl_mult = 2.0


class RewardV4:
    """적응형 — 수익/손실 비대칭 보상"""
    name = "v4_asymmetric"
    hold_cost = -0.003
    tp_win_mult = 3.0        # 수익 매우 강한 보너스
    tp_loss_mult = 0.6
    sl_bonus = 0.15
    sl_threshold = -0.20
    sl_profit_mult = 0.4
    timeout_mult = 0.6
    forced_sl_mult = 1.8


REWARD_VARIANTS = [RewardV1, RewardV2, RewardV3, RewardV4]


# ── 환경 래퍼 (보상함수 교체) ──────────────────────

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:
    import gym
    from gym import spaces

from scalp_ml.scalp_exit_env import ScalpExitEnv, FEE_PCT, MAX_HOLD, SL_DEFAULT


class TunedScalpExitEnv(ScalpExitEnv):
    """보상함수를 동적으로 교체할 수 있는 환경"""

    def __init__(self, reward_config=None, **kwargs):
        super().__init__(**kwargs)
        self.rc = reward_config or RewardV1()

    def step(self, action: int):
        if self._done:
            return self._compute_obs(), 0.0, True, False, {}

        self._current_step += 1
        hold_min = self._current_step - 15

        current_idx = min(self._current_step, len(self._episode_candles) - 1)
        current_price = self._episode_candles[current_idx]["trade_price"]
        pnl_pct = (current_price / self._entry_price - 1) * 100 - FEE_PCT

        reward = 0.0
        terminated = False
        info = {}
        rc = self.rc

        if action == 0:  # HOLD
            reward = rc.hold_cost

            if hold_min >= MAX_HOLD:
                reward = pnl_pct * rc.timeout_mult
                terminated = True
                info["exit_reason"] = "timeout"
            elif pnl_pct <= -SL_DEFAULT:
                reward = pnl_pct * rc.forced_sl_mult
                terminated = True
                info["exit_reason"] = "forced_sl"

        elif action == 1:  # TAKE_PROFIT
            reward = pnl_pct
            if pnl_pct > 0:
                reward *= rc.tp_win_mult
            else:
                reward *= rc.tp_loss_mult
            terminated = True
            info["exit_reason"] = "take_profit"

        elif action == 2:  # STOP_LOSS
            reward = pnl_pct
            if pnl_pct < rc.sl_threshold:
                reward += rc.sl_bonus
            elif pnl_pct > 0:
                reward *= rc.sl_profit_mult
            terminated = True
            info["exit_reason"] = "stop_loss"

        self._total_reward += reward

        if terminated:
            self._done = True
            self.episode_count += 1
            if pnl_pct > 0:
                self.wins += 1
            else:
                self.losses += 1
            info["pnl_pct"] = round(pnl_pct, 4)
            info["hold_minutes"] = hold_min
            info["total_reward"] = round(self._total_reward, 4)

        return self._compute_obs(), reward, terminated, False, info


# ── 평가 ──────────────────────────────────────────

def evaluate(model, env, episodes: int) -> dict:
    """모델 평가 — 승률, PnL, exit_reason 분포"""
    wins, total_pnl = 0, 0.0
    exit_reasons = {}
    hold_times = []

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
        hold_times.append(info.get("hold_minutes", 0))

        er = info.get("exit_reason", "unknown")
        exit_reasons[er] = exit_reasons.get(er, 0) + 1

    win_rate = wins / episodes if episodes > 0 else 0
    return {
        "win_rate": round(win_rate, 4),
        "avg_pnl": round(total_pnl / episodes, 4) if episodes else 0,
        "total_pnl": round(total_pnl, 2),
        "exit_reasons": exit_reasons,
        "avg_hold": round(np.mean(hold_times), 1) if hold_times else 0,
        "episodes": episodes,
    }


# ── 하이퍼파라미터 탐색 ──────────────────────────────

HP_CONFIGS = [
    {"lr": 3e-4, "n_steps": 1024, "batch": 64,  "ent": 0.02, "arch": [128, 64]},
    {"lr": 1e-4, "n_steps": 2048, "batch": 128, "ent": 0.01, "arch": [256, 128]},
    {"lr": 5e-4, "n_steps": 512,  "batch": 32,  "ent": 0.05, "arch": [64, 64]},
    {"lr": 2e-4, "n_steps": 1024, "batch": 64,  "ent": 0.03, "arch": [128, 128]},
    {"lr": 3e-4, "n_steps": 2048, "batch": 64,  "ent": 0.02, "arch": [256, 128, 64]},
    {"lr": 1e-3, "n_steps": 512,  "batch": 64,  "ent": 0.01, "arch": [128, 64]},
]


def create_model(hp: dict, env, reward_config):
    """하이퍼파라미터로 PPO 모델 생성"""
    from stable_baselines3 import PPO
    return PPO(
        "MlpPolicy", env,
        learning_rate=hp["lr"],
        n_steps=hp["n_steps"],
        batch_size=hp["batch"],
        n_epochs=10,
        gamma=0.99,
        ent_coef=hp["ent"],
        policy_kwargs={"net_arch": hp["arch"]},
        verbose=0,
    )


# ── 텔레그램 ──────────────────────────────────────

def send_telegram(text: str):
    try:
        import requests
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_USER_ID", "")
        if token and chat_id:
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


# ── 메인 훈련 루프 ──────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RL 파인튜닝 — 60% 승률 목표")
    parser.add_argument("--target", type=float, default=TARGET_WIN_RATE)
    parser.add_argument("--consecutive", type=int, default=TARGET_CONSECUTIVE)
    parser.add_argument("--steps", type=int, default=50000, help="라운드당 학습 스텝")
    parser.add_argument("--max-rounds", type=int, default=MAX_ROUNDS)
    args = parser.parse_args()

    from stable_baselines3.common.callbacks import EvalCallback

    log.info(f"{'='*60}")
    log.info("  RL 파인튜닝 시작")
    log.info(f"  목표: 승률 {args.target:.0%} x {args.consecutive}연속")
    log.info(f"  라운드당: {args.steps:,} 스텝")
    log.info(f"{'='*60}")

    send_telegram(
        f"🏋️ RL 파인튜닝 시작\n"
        f"목표: {args.target:.0%} x {args.consecutive}연속\n"
        f"라운드당: {args.steps:,} 스텝"
    )

    # 최고 기록 추적
    best_win_rate = 0
    # best_model_path tracking removed (unused after loop)
    consecutive_count = 0
    round_history = []

    # 현재 최적 설정
    current_hp_idx = 0
    current_reward_idx = 0
    stagnation_count = 0  # 정체 카운터

    # 초기 모델 탐색: 모든 보상+HP 조합 중 최적 찾기
    log.info("\n[Phase 0] 초기 탐색 — 보상함수 x HP 조합 평가")
    best_combo = {"win_rate": 0, "hp_idx": 0, "reward_idx": 0}

    for ri, rc_cls in enumerate(REWARD_VARIANTS):
        for hi, hp in enumerate(HP_CONFIGS[:3]):  # 상위 3개 HP만
            rc = rc_cls()
            env = TunedScalpExitEnv(reward_config=rc)
            model = create_model(hp, env, rc)
            model.learn(total_timesteps=20000, progress_bar=False)

            eval_env = TunedScalpExitEnv(reward_config=rc)
            result = evaluate(model, eval_env, 200)
            log.info(
                f"  {rc.name} + HP{hi}: 승률={result['win_rate']:.1%}, "
                f"PnL={result['avg_pnl']:.3f}%, exits={result['exit_reasons']}"
            )

            if result["win_rate"] > best_combo["win_rate"]:
                best_combo = {
                    "win_rate": result["win_rate"],
                    "hp_idx": hi,
                    "reward_idx": ri,
                }

    current_hp_idx = best_combo["hp_idx"]
    current_reward_idx = best_combo["reward_idx"]
    log.info(
        f"\n[Phase 0 결과] 최적: {REWARD_VARIANTS[current_reward_idx].name} + "
        f"HP{current_hp_idx} (승률 {best_combo['win_rate']:.1%})"
    )

    # 메인 모델 생성
    rc = REWARD_VARIANTS[current_reward_idx]()
    hp = HP_CONFIGS[current_hp_idx]
    env = TunedScalpExitEnv(reward_config=rc)
    eval_env = TunedScalpExitEnv(reward_config=rc)
    model = create_model(hp, env, rc)

    start_time = time.time()

    for round_num in range(1, args.max_rounds + 1):
        round_start = time.time()

        # 학습
        eval_cb = EvalCallback(
            eval_env, n_eval_episodes=100, eval_freq=10000,
            best_model_save_path=str(MODEL_DIR / "ppo_finetune_best"),
            deterministic=True, verbose=0,
        )
        model.learn(total_timesteps=args.steps, callback=eval_cb,
                     progress_bar=False, reset_num_timesteps=False)

        # 평가
        result = evaluate(model, eval_env, EVAL_EPISODES)
        win_rate = result["win_rate"]
        elapsed = time.time() - round_start
        total_elapsed = (time.time() - start_time) / 3600

        # 연속 카운트
        if win_rate >= args.target:
            consecutive_count += 1
            stagnation_count = 0
        else:
            consecutive_count = 0
            stagnation_count += 1

        # 최고 기록
        if win_rate > best_win_rate:
            best_win_rate = win_rate
            model.save(str(MODEL_DIR / "ppo_finetune_best_ever"))
            # best_model_path updated but not used after loop

        # 히스토리
        round_history.append({
            "round": round_num,
            "win_rate": win_rate,
            "avg_pnl": result["avg_pnl"],
            "avg_hold": result["avg_hold"],
            "consecutive": consecutive_count,
            "reward": rc.name,
            "hp_idx": current_hp_idx,
        })

        # 로그
        bar = "█" * int(win_rate * 20) + "░" * (20 - int(win_rate * 20))
        target_mark = "🎯" if win_rate >= args.target else "  "
        log.info(
            f"R{round_num:03d} [{bar}] {win_rate:5.1%} "
            f"pnl={result['avg_pnl']:+.3f}% hold={result['avg_hold']:.0f}m "
            f"연속={consecutive_count}/{args.consecutive} "
            f"최고={best_win_rate:.1%} {target_mark} "
            f"({elapsed:.0f}s, 총{total_elapsed:.1f}h)"
        )

        # 목표 달성!
        if consecutive_count >= args.consecutive:
            log.info(f"\n{'🎯' * 10}")
            log.info(f"  목표 달성! {args.target:.0%} x {args.consecutive}연속!")
            log.info(f"  총 {round_num}라운드, {total_elapsed:.1f}시간")
            log.info(f"{'🎯' * 10}")

            # 최종 모델 저장
            model.save(str(MODEL_DIR / "ppo_finetune_60pct"))
            model.save(str(MODEL_DIR / "ppo_auto_latest"))

            # best_model도 복사
            best_path = MODEL_DIR / "ppo_finetune_best" / "best_model.zip"
            if best_path.exists():
                import shutil
                shutil.copy2(best_path, MODEL_DIR / "ppo_auto_best" / "best_model.zip")

            send_telegram(
                f"🎯🎯🎯 RL 파인튜닝 목표 달성!\n"
                f"승률: {win_rate:.1%} x {args.consecutive}연속\n"
                f"총 {round_num}라운드, {total_elapsed:.1f}시간\n"
                f"보상: {rc.name}, HP{current_hp_idx}\n"
                f"최고 승률: {best_win_rate:.1%}"
            )

            _save_report(round_history, best_win_rate, round_num, total_elapsed)
            return

        # 정체 감지 → 전략 변경
        if stagnation_count > 0 and stagnation_count % 10 == 0:
            log.info(f"\n[정체 {stagnation_count}라운드] 전략 변경...")

            if stagnation_count % 30 == 0:
                # 30라운드 정체: 보상함수 + HP 모두 변경
                current_reward_idx = (current_reward_idx + 1) % len(REWARD_VARIANTS)
                current_hp_idx = (current_hp_idx + 1) % len(HP_CONFIGS)
                rc = REWARD_VARIANTS[current_reward_idx]()
                hp = HP_CONFIGS[current_hp_idx]
                env = TunedScalpExitEnv(reward_config=rc)
                eval_env = TunedScalpExitEnv(reward_config=rc)
                model = create_model(hp, env, rc)
                log.info(f"  새 조합: {rc.name} + HP{current_hp_idx} (모델 초기화)")

            elif stagnation_count % 20 == 0:
                # 20라운드 정체: 보상함수 변경
                current_reward_idx = (current_reward_idx + 1) % len(REWARD_VARIANTS)
                rc = REWARD_VARIANTS[current_reward_idx]()
                env = TunedScalpExitEnv(reward_config=rc)
                eval_env = TunedScalpExitEnv(reward_config=rc)
                model = create_model(hp, env, rc)
                log.info(f"  새 보상: {rc.name} (모델 초기화)")

            else:
                # 10라운드 정체: HP만 변경, 모델 유지 시도
                current_hp_idx = (current_hp_idx + 1) % len(HP_CONFIGS)
                hp = HP_CONFIGS[current_hp_idx]
                # learning rate만 업데이트
                model.learning_rate = hp["lr"]
                model.ent_coef = hp["ent"]
                log.info(f"  HP 변경: lr={hp['lr']}, ent={hp['ent']}")

            send_telegram(
                f"🔄 RL 정체 {stagnation_count}R → 전략 변경\n"
                f"보상: {rc.name}, HP{current_hp_idx}\n"
                f"현재 최고: {best_win_rate:.1%}"
            )

        # 10라운드마다 보고
        if round_num % 10 == 0:
            recent = round_history[-10:]
            avg_wr = np.mean([r["win_rate"] for r in recent])
            send_telegram(
                f"📊 RL R{round_num} 보고\n"
                f"최근10R 평균: {avg_wr:.1%}\n"
                f"현재: {win_rate:.1%}, 최고: {best_win_rate:.1%}\n"
                f"연속: {consecutive_count}/{args.consecutive}\n"
                f"보상: {rc.name}, 경과: {total_elapsed:.1f}h"
            )

        # 중간 저장 (20라운드마다)
        if round_num % 20 == 0:
            model.save(str(MODEL_DIR / f"ppo_finetune_r{round_num}"))
            _save_report(round_history, best_win_rate, round_num,
                        (time.time() - start_time) / 3600)

    # 최대 라운드 도달
    log.info(f"\n최대 {args.max_rounds}라운드 도달. 최고 승률: {best_win_rate:.1%}")
    model.save(str(MODEL_DIR / "ppo_finetune_final"))
    _save_report(round_history, best_win_rate, args.max_rounds,
                (time.time() - start_time) / 3600)

    send_telegram(
        f"⏰ RL 파인튜닝 {args.max_rounds}R 완료\n"
        f"최고: {best_win_rate:.1%}, 연속최대: {max(r['consecutive'] for r in round_history)}\n"
        f"경과: {(time.time()-start_time)/3600:.1f}h"
    )


def _save_report(history: list, best_wr: float, rounds: int, hours: float):
    """훈련 보고서 저장"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_rounds": rounds,
        "total_hours": round(hours, 2),
        "best_win_rate": best_wr,
        "target": TARGET_WIN_RATE,
        "target_consecutive": TARGET_CONSECUTIVE,
        "history": history[-50:],  # 최근 50라운드
    }
    with open(MODEL_DIR / "rl_finetune_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)


if __name__ == "__main__":
    main()
