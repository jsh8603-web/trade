#!/usr/bin/env python3
"""
실제 데이터 모델 헌터 V3 — 20차원 + 순수 PnL + 5중 필터 + 1M steps

V2 대비 변경:
1. 20차원 관측 (오더북 프록시 4개 추가)
2. 5중 진입 필터 (추세 + FGI/고래)
3. 순수 PnL 보상 (보너스/패널티 없음)
4. 1M steps (V2는 500K)
5. SL 변형 (tight 0.2%, default 0.4%)
6. 모든 결과 DB 기록
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import requests

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
MACHINE = os.getenv("MACHINE_NAME", "pc128")


def evaluate(model, env, episodes=500):
    wins, losses = 0, 0
    pnl_list, hold_list = [], []
    reasons = {}

    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, truncated, info = env.step(action)
            done = done or truncated

        net_pnl = info.get("net_pnl_pct", 0)
        pnl_list.append(net_pnl)
        hold_list.append(info.get("hold_bars", 0))
        if net_pnl > 0:
            wins += 1
        else:
            losses += 1
        r = info.get("exit_reason", "unknown")
        reasons[r] = reasons.get(r, 0) + 1

    total = wins + losses
    if total == 0:
        return None

    win_pnls = [p for p in pnl_list if p > 0]
    loss_pnls = [abs(p) for p in pnl_list if p < 0]
    avg_pnl = float(np.mean(pnl_list))
    std_pnl = float(np.std(pnl_list)) if len(pnl_list) > 1 else 0.001
    avg_win = float(np.mean(win_pnls)) if win_pnls else 0
    avg_loss = float(np.mean(loss_pnls)) if loss_pnls else 0.001

    return {
        "win_rate": round(wins / total * 100, 1),
        "wins": wins, "losses": losses,
        "avg_pnl": round(avg_pnl, 4),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
        "rr_ratio": round(avg_win / avg_loss, 2) if avg_loss > 0 else 0,
        "profit_factor": round(sum(win_pnls) / max(sum(loss_pnls), 0.001), 2),
        "sharpe": round(avg_pnl / std_pnl, 3) if std_pnl > 0 else 0,
        "total_pnl": round(float(sum(pnl_list)), 2),
        "avg_hold": round(float(np.mean(hold_list)), 1),
        "exit_reasons": reasons,
    }


def save_to_db(results, version="v3"):
    """DB에 헌팅 결과 요약 저장"""
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY", ""))

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("  DB 미설정, 스킵")
        return

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    for r in results:
        te = r["test"]
        tr = r["train"]
        row = {
            "market": "KRW-BTC",
            "decision": "관망",
            "confidence": 0.0,
            "reason": (
                f"[{version.upper()}-HUNT] {r['name']} ({r['algo']}) "
                f"test: WR={te['win_rate']}% PnL={te['avg_pnl']:+.4f}% "
                f"RR={te['rr_ratio']} PF={te['profit_factor']} "
                f"train: WR={tr['win_rate']}% PnL={tr['avg_pnl']:+.4f}%"
            ),
            "current_price": 0,
            "executed": False,
            "source": f"{version}_hunter_{MACHINE}",
            "trade_amount": 0,
            "rsi_value": 50,
            "market_data_snapshot": json.dumps({
                "type": f"{version}_hunt_result",
                "model_name": r["name"],
                "algorithm": r["algo"],
                "train_seconds": r["train_sec"],
                "sl_limit": r.get("sl_limit", 0.4),
                "steps": r.get("steps", 1_000_000),
                "obs_dims": 20,
                "train": tr,
                "test": te,
                "machine": MACHINE,
                "hunt_time": datetime.now(KST).isoformat(),
            }, ensure_ascii=False),
        }

        try:
            resp = requests.post(
                f"{SUPABASE_URL}/rest/v1/decisions",
                headers=headers, json=row, timeout=10,
            )
            status = "OK" if resp.ok else f"FAIL({resp.status_code})"
        except Exception as e:
            status = f"ERR({e})"
        print(f"  DB [{r['name']}]: {status}")


def main():
    from stable_baselines3 import DQN, PPO, A2C, SAC
    from scalp_ml.swing_env_v3 import SwingEnvV3, SwingEnvV3Continuous

    SAVE_DIR = PROJECT_DIR / "data" / "scalp_models" / "real_models_v3"
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    STEPS = 1_000_000  # 1M steps (V2는 500K)

    # ── 환경 변형 2개: default SL(0.4%) + tight SL(0.2%) ──
    sl_variants = [
        {"name_suffix": "", "sl_limit": 0.4},
        {"name_suffix": "_tightSL", "sl_limit": 0.2},
    ]

    configs = []
    for sl_var in sl_variants:
        suffix = sl_var["name_suffix"]
        sl = sl_var["sl_limit"]

        # ── DQN ──
        configs.append({
            "name": f"DQN_1024_512{suffix}", "algo": "DQN", "continuous": False,
            "sl_limit": sl,
            "kwargs": {"learning_rate": 0.0005, "gamma": 0.95,
                       "policy_kwargs": {"net_arch": [1024, 512]},
                       "batch_size": 256, "exploration_fraction": 0.15,
                       "buffer_size": 200_000}})

        configs.append({
            "name": f"DQN_512_256{suffix}", "algo": "DQN", "continuous": False,
            "sl_limit": sl,
            "kwargs": {"learning_rate": 0.0005, "gamma": 0.97,
                       "policy_kwargs": {"net_arch": [512, 256]},
                       "batch_size": 256, "exploration_fraction": 0.15,
                       "buffer_size": 100_000}})

        # ── PPO ──
        configs.append({
            "name": f"PPO_1024_512{suffix}", "algo": "PPO", "continuous": False,
            "sl_limit": sl,
            "kwargs": {"learning_rate": 0.0001, "gamma": 0.95,
                       "policy_kwargs": {"net_arch": [1024, 512]},
                       "n_steps": 2048, "batch_size": 256, "ent_coef": 0.01}})

        configs.append({
            "name": f"PPO_512_256{suffix}", "algo": "PPO", "continuous": False,
            "sl_limit": sl,
            "kwargs": {"learning_rate": 0.0003, "gamma": 0.97,
                       "policy_kwargs": {"net_arch": [512, 256]},
                       "n_steps": 2048, "batch_size": 128, "ent_coef": 0.02}})

        # ── A2C ──
        configs.append({
            "name": f"A2C_512_256{suffix}", "algo": "A2C", "continuous": False,
            "sl_limit": sl,
            "kwargs": {"learning_rate": 0.0005, "gamma": 0.97,
                       "policy_kwargs": {"net_arch": [512, 256]},
                       "n_steps": 10, "ent_coef": 0.02}})

        # ── SAC (연속 행동) ──
        configs.append({
            "name": f"SAC_512_256{suffix}", "algo": "SAC", "continuous": True,
            "sl_limit": sl,
            "kwargs": {"learning_rate": 0.0003, "gamma": 0.97,
                       "policy_kwargs": {"net_arch": [512, 256]},
                       "batch_size": 256, "buffer_size": 200_000}})

    algo_map = {"DQN": DQN, "PPO": PPO, "A2C": A2C, "SAC": SAC}
    results = []

    print(f"\n{'='*80}")
    print(f"  V3 헌터: 20차원 + 순수PnL + 5중필터 + 1M steps")
    print(f"  {len(configs)}개 조합 (SL 0.4% + SL 0.2%)")
    print(f"  훈련: 2/1~3/10 | 테스트: 3/10~3/17 | {STEPS//1000}K steps")
    print(f"  머신: {MACHINE}")
    print(f"{'='*80}\n")

    # 이미 훈련된 모델 스킵 (resume 지원)
    existing_models = {p.stem.replace("v3_", "") for p in SAVE_DIR.glob("v3_*.zip")}
    if existing_models:
        print(f"  이미 훈련된 모델 ({len(existing_models)}개): {', '.join(sorted(existing_models))}")
        print(f"  → 스킵하고 나머지만 훈련합니다.\n")

    for i, cfg in enumerate(configs):
        name = cfg["name"]
        algo_cls = algo_map[cfg["algo"]]
        is_cont = cfg["continuous"]
        sl = cfg["sl_limit"]

        # 이미 훈련된 모델 스킵
        if name in existing_models:
            print(f"[{i+1}/{len(configs)}] {name} — 이미 훈련됨, 스킵")
            continue

        print(f"[{i+1}/{len(configs)}] {name} ({cfg['algo']}, SL={sl}%, {STEPS//1000}K)")

        # 환경 생성 (각 모델마다 새로 — SL이 다를 수 있으므로)
        EnvCls = SwingEnvV3Continuous if is_cont else SwingEnvV3
        try:
            train_env = EnvCls(
                date_from="2026-02-01", date_to="2026-03-10",
                sl_limit=sl, filter_5x=True,
            )
            test_env = EnvCls(
                date_from="2026-03-10", date_to="2026-03-17",
                sl_limit=sl, filter_5x=True,
            )
        except ValueError as e:
            print(f"  환경 생성 실패: {e}")
            continue

        print(f"  훈련: {len(train_env.bars)}봉, {len(train_env.entry_points)}진입점")
        print(f"  테스트: {len(test_env.bars)}봉, {len(test_env.entry_points)}진입점")

        t0 = time.time()
        try:
            model = algo_cls("MlpPolicy", train_env, verbose=0, **cfg["kwargs"])
            model.learn(total_timesteps=STEPS, progress_bar=True)
            train_sec = int(time.time() - t0)
        except Exception as e:
            print(f"  훈련 실패: {e}")
            continue

        print(f"  훈련 {train_sec}초 → 평가...")
        tr = evaluate(model, train_env, 500)
        te = evaluate(model, test_env, 300)

        if not tr or not te:
            print(f"  평가 실패")
            continue

        entry = {
            "name": name, "algo": cfg["algo"],
            "train_sec": train_sec, "sl_limit": sl,
            "steps": STEPS,
            "train": tr, "test": te,
        }
        results.append(entry)

        model.save(str(SAVE_DIR / f"v3_{name}"))

        print(f"  훈련: 승률={tr['win_rate']}% PnL={tr['avg_pnl']:+.4f}% "
              f"RR={tr['rr_ratio']} PF={tr['profit_factor']}")
        print(f"  테스트: 승률={te['win_rate']}% PnL={te['avg_pnl']:+.4f}% "
              f"RR={te['rr_ratio']} PF={te['profit_factor']}")
        print(f"  청산: {te['exit_reasons']}")

        if te["avg_pnl"] > 0:
            print(f"  ★★★ 양수 PnL! ★★★")
        elif te["avg_pnl"] > -0.03:
            print(f"  ★ 손익분기 근접!")
        print()

    # ── 최종 순위 ──
    if results:
        ranked = sorted(results, key=lambda r: r["test"]["avg_pnl"], reverse=True)

        print(f"\n{'='*80}")
        print(f"  V3 최종 순위 ({len(ranked)}개 모델)")
        print(f"{'='*80}\n")
        print(f"  {'#':>2} {'모델':<30} {'알고':>4} {'SL':>4} {'테스트PnL':>10} {'승률':>6} "
              f"{'RR':>5} {'PF':>5} {'보유':>5} {'훈련PnL':>10}")
        print(f"  {'─'*2} {'─'*30} {'─'*4} {'─'*4} {'─'*10} {'─'*6} {'─'*5} {'─'*5} {'─'*5} {'─'*10}")

        for rank, r in enumerate(ranked, 1):
            te = r["test"]
            tr = r["train"]
            star = " ★" if te["avg_pnl"] > 0 else ""
            print(f"  {rank:2d} {r['name']:<30} {r['algo']:>4} {r['sl_limit']:3.1f}% "
                  f"{te['avg_pnl']:+10.4f}% {te['win_rate']:5.1f}% "
                  f"{te['rr_ratio']:5.2f} {te['profit_factor']:5.2f} "
                  f"{te['avg_hold']:4.1f}봉 {tr['avg_pnl']:+10.4f}%{star}")

        # 1위 상세
        best = ranked[0]
        te = best["test"]
        print(f"\n  [1위: {best['name']} ({best['algo']}, SL={best['sl_limit']}%)]")
        print(f"  테스트: {te['win_rate']}% ({te['wins']}승/{te['losses']}패)")
        print(f"  PnL: {te['avg_pnl']:+.4f}%, R:R: {te['rr_ratio']}, PF: {te['profit_factor']}")
        print(f"  이길때: +{te['avg_win']:.4f}%, 질때: -{te['avg_loss']:.4f}%")
        print(f"  Sharpe: {te['sharpe']}, 평균보유: {te['avg_hold']}봉 ({te['avg_hold']*5:.0f}분)")
        print(f"  청산: {te['exit_reasons']}")

        # JSON 저장
        json_path = SAVE_DIR / "hunt_results_v3.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "version": "v3",
                "obs_dims": 20,
                "reward": "pure_pnl",
                "entry_filter": "5x (mom+vol+rsi+trend+fgi_whale)",
                "steps": STEPS,
                "hunt_time": datetime.now(KST).isoformat(),
                "train_period": "2026-02-01~2026-03-10",
                "test_period": "2026-03-10~2026-03-17",
                "machine": MACHINE,
                "results": ranked,
            }, f, indent=2, ensure_ascii=False)
        print(f"\n  결과 JSON: {json_path}")

        # DB 저장
        print(f"\n  DB 기록 중...")
        save_to_db(ranked, "v3")

    print(f"\n{'='*80}")
    print(f"  V3 헌터 완료! {len(results)}/{len(configs)} 모델 훈련 성공")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
