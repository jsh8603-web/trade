#!/usr/bin/env python3
"""
Round 6 동일 조건 재훈련 — DQN 1M steps, lr=0.001, [256,128], gamma=0.97
모델 저장 + 완전한 평가 데이터 JSON
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv(PROJECT_DIR / ".env")

KST = timezone(timedelta(hours=9))


def main():
    from stable_baselines3 import DQN
    from scalp_ml.swing_exit_env import SwingExitEnv

    # ── R6 동일 하이퍼파라미터 ──
    ALGO = "dqn"
    STEPS = 1_000_000
    LR = 0.001
    NET_ARCH = [256, 128]
    GAMMA = 0.97
    BATCH_SIZE = 128
    EXPLORATION_FRACTION = 0.2
    EVAL_EPS = 3000

    print("=" * 70)
    print("Round 6 재훈련 — DQN 동일 조건")
    print(f"  algo=DQN, steps={STEPS:,}, lr={LR}, arch={NET_ARCH}, gamma={GAMMA}")
    print(f"  batch={BATCH_SIZE}, exploration={EXPLORATION_FRACTION}")
    print(f"  평가: {EVAL_EPS} 에피소드")
    print("=" * 70)

    train_env = SwingExitEnv()
    eval_env = SwingExitEnv()

    print(f"\n훈련 시작... ({STEPS:,} 스텝)")
    t0 = time.time()

    model = DQN(
        "MlpPolicy", train_env,
        learning_rate=LR,
        gamma=GAMMA,
        batch_size=BATCH_SIZE,
        exploration_fraction=EXPLORATION_FRACTION,
        policy_kwargs={"net_arch": NET_ARCH},
        verbose=0,
    )
    model.learn(total_timesteps=STEPS, progress_bar=True)

    train_sec = int(time.time() - t0)
    print(f"훈련 완료: {train_sec}초 ({train_sec // 60}분)")

    # ── 평가 ──
    print(f"\n평가 시작... ({EVAL_EPS} 에피소드)")
    t1 = time.time()

    wins, losses = 0, 0
    pnl_list = []
    exit_reasons = {}
    hold_bars_list = []

    for ep in range(EVAL_EPS):
        obs, _ = eval_env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, truncated, info = eval_env.step(int(action))
            done = done or truncated

        net_pnl = info.get("net_pnl_pct", 0)
        pnl_list.append(net_pnl)
        hold_bars_list.append(info.get("hold_bars", 0))

        if net_pnl > 0:
            wins += 1
        else:
            losses += 1

        reason = info.get("exit_reason", "unknown")
        exit_reasons[reason] = exit_reasons.get(reason, 0) + 1

        if (ep + 1) % 500 == 0:
            print(f"  ... {ep + 1}/{EVAL_EPS} 완료")

    eval_sec = int(time.time() - t1)

    # ── 결과 계산 ──
    total = wins + losses
    win_rate = wins / total if total > 0 else 0
    win_pnls = [p for p in pnl_list if p > 0]
    loss_pnls = [abs(p) for p in pnl_list if p < 0]
    avg_win = np.mean(win_pnls) if win_pnls else 0
    avg_loss = np.mean(loss_pnls) if loss_pnls else 0.001
    rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0
    avg_pnl = np.mean(pnl_list) if pnl_list else 0
    profit_factor = sum(win_pnls) / max(sum(loss_pnls), 0.001)
    max_pnl = max(pnl_list) if pnl_list else 0
    min_pnl = min(pnl_list) if pnl_list else 0
    std_pnl = np.std(pnl_list) if pnl_list else 0
    avg_hold = np.mean(hold_bars_list) if hold_bars_list else 0
    sharpe = avg_pnl / std_pnl if std_pnl > 0 else 0

    max_consecutive_loss = 0
    current_streak = 0
    for p in pnl_list:
        if p < 0:
            current_streak += 1
            max_consecutive_loss = max(max_consecutive_loss, current_streak)
        else:
            current_streak = 0

    # ── 출력 ──
    print("\n" + "=" * 70)
    print("  Round 6 재훈련 결과 (DQN 1M steps)")
    print("=" * 70)
    print(f"\n  [기본 지표]")
    print(f"  승률:           {win_rate * 100:.1f}% ({wins}승 / {losses}패)")
    print(f"  평균 순이익:    {avg_pnl:+.4f}% (수수료 후)")
    print(f"  R:R 비율:       {rr_ratio:.2f}")
    print(f"  Profit Factor:  {profit_factor:.2f}")
    print(f"  Sharpe Ratio:   {sharpe:.3f}")

    print(f"\n  [승패 상세]")
    print(f"  평균 수익 (이길 때): +{avg_win:.4f}%")
    print(f"  평균 손실 (질 때):   -{avg_loss:.4f}%")
    print(f"  최대 수익:           +{max_pnl:.4f}%")
    print(f"  최대 손실:           -{abs(min_pnl):.4f}%")
    print(f"  PnL 표준편차:        {std_pnl:.4f}%")
    print(f"  최대 연속 손실:      {max_consecutive_loss}회")

    print(f"\n  [청산 분포]")
    for reason, count in sorted(exit_reasons.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"  {reason:15s}: {count:5d}건 ({pct:.1f}%)")

    print(f"\n  [시간]")
    print(f"  평균 보유 시간:  {avg_hold:.1f}봉 ({avg_hold * 5:.0f}분)")
    print(f"  훈련 시간:       {train_sec // 60}분 {train_sec % 60}초")
    print(f"  평가 시간:       {eval_sec}초")

    print(f"\n  [수익 시뮬레이션 — 100만원 기준]")
    for trades in [5, 8, 10, 15, 20]:
        profit = avg_pnl * 10000 * trades
        print(f"  {trades}회 매매: {profit:+,.0f}원")

    print("\n" + "=" * 70)

    # ── 모델 저장 ──
    save_dir = PROJECT_DIR / "data" / "scalp_models" / "confirmed_swing"
    save_dir.mkdir(parents=True, exist_ok=True)
    model_path = save_dir / "swing_dqn_r6"
    model.save(str(model_path))
    print(f"모델 저장: {model_path}.zip")

    # ── JSON 저장 ──
    result_data = {
        "algo": ALGO,
        "hyperparams": {
            "steps": STEPS, "lr": LR, "net_arch": str(NET_ARCH),
            "gamma": GAMMA, "batch_size": BATCH_SIZE,
            "exploration_fraction": EXPLORATION_FRACTION,
        },
        "evaluation": {
            "episodes": EVAL_EPS, "win_rate": round(win_rate * 100, 1),
            "wins": wins, "losses": losses,
            "avg_net_pnl_pct": round(avg_pnl, 4),
            "avg_win_pnl_pct": round(avg_win, 4),
            "avg_loss_pnl_pct": round(avg_loss, 4),
            "rr_ratio": round(rr_ratio, 2),
            "profit_factor": round(profit_factor, 2),
            "sharpe_ratio": round(sharpe, 3),
            "max_pnl_pct": round(max_pnl, 4),
            "min_pnl_pct": round(min_pnl, 4),
            "std_pnl_pct": round(std_pnl, 4),
            "max_consecutive_loss": max_consecutive_loss,
            "avg_hold_bars": round(avg_hold, 1),
            "avg_hold_minutes": round(avg_hold * 5, 0),
            "exit_reasons": exit_reasons,
        },
        "profit_simulation_1m_krw": {
            f"{t}trades": round(avg_pnl * 10000 * t, 0) for t in [5, 8, 10, 15, 20]
        },
        "train_time_sec": train_sec,
        "timestamp": datetime.now(KST).isoformat(),
    }

    json_path = save_dir / "swing_dqn_r6_result.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    print(f"결과 저장: {json_path}")


if __name__ == "__main__":
    main()
