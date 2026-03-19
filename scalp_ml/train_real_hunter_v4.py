#!/usr/bin/env python3
"""
실제 데이터 모델 헌터 V4 — 2.5개월 데이터 + PPO/SAC 집중 + 과적합 방지

V3 대비 변경:
1. 데이터 2배 (1/1~3/10, ~18,000봉 vs V3의 ~11,000봉)
2. PPO + SAC만 (A2C/DQN 폐기 — V3에서 전멸)
3. 400K~800K steps (1M은 과적합 심각)
4. SL 0.4% 고정 (tightSL 0.2% 폐기)
5. hunt_results.json Top 라운드 하이퍼파라미터 기반
6. 라운드별 결과 즉시 DB 기록
"""
from __future__ import annotations

import json
import os
import pickle
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
DATA_DIR = PROJECT_DIR / "data" / "scalp_models" / "real_data"
SAVE_DIR = PROJECT_DIR / "data" / "scalp_models" / "real_models_v4"


def merge_data():
    """1월 + 2~3월 V3 데이터를 합쳐서 하나의 pkl로 저장"""
    merged_path = DATA_DIR / "btc_5min_v3_20260101_20260317.pkl"

    if merged_path.exists():
        with open(merged_path, "rb") as f:
            bars = pickle.load(f)
        print(f"  기존 병합 데이터 로드: {len(bars)}봉")
        return str(merged_path)

    jan_path = DATA_DIR / "btc_5min_v3_20260101_20260131.pkl"
    feb_path = DATA_DIR / "btc_5min_v3_20260201_20260317.pkl"

    with open(jan_path, "rb") as f:
        jan = pickle.load(f)
    with open(feb_path, "rb") as f:
        feb = pickle.load(f)

    # 시간순 병합 + 중복 제거
    all_bars = jan + feb
    seen = set()
    merged = []
    for b in sorted(all_bars, key=lambda x: x["time"]):
        if b["time"] not in seen:
            seen.add(b["time"])
            merged.append(b)

    with open(merged_path, "wb") as f:
        pickle.dump(merged, f)
    print(f"  데이터 병합: {len(jan)} + {len(feb)} → {len(merged)}봉")
    print(f"  범위: {merged[0]['time'][:10]} ~ {merged[-1]['time'][:10]}")
    return str(merged_path)


def evaluate(model, env, episodes=500):
    """모델 평가"""
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


def save_round_to_db(entry, version="v4"):
    """라운드별 결과를 즉시 DB에 저장"""
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY", ""))
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    te = entry["test"]
    tr = entry["train"]
    row = {
        "market": "KRW-BTC",
        "decision": "관망",
        "confidence": 0.0,
        "reason": (
            f"[{version.upper()}-HUNT] R{entry['round']} {entry['name']} ({entry['algo']}) "
            f"test: WR={te['win_rate']}% PnL={te['avg_pnl']:+.4f}% "
            f"RR={te['rr_ratio']} PF={te['profit_factor']} "
            f"train: WR={tr['win_rate']}% PnL={tr['avg_pnl']:+.4f}%"
        ),
        "current_price": 0,
        "executed": False,
        "source": f"{version}_hunter_{MACHINE}",
        "trade_amount": 0,
        "rsi_value": 50,
        "machine_name": MACHINE,
        "market_data_snapshot": json.dumps({
            "type": f"{version}_hunt_result",
            "round": entry["round"],
            "model_name": entry["name"],
            "algorithm": entry["algo"],
            "train_seconds": entry["train_sec"],
            "steps": entry["steps"],
            "hyperparams": entry.get("hyperparams", {}),
            "obs_dims": 20,
            "train_period": "2026-01-01~2026-03-10",
            "test_period": "2026-03-10~2026-03-17",
            "train": tr,
            "test": te,
            "machine": MACHINE,
            "hunt_time": datetime.now(KST).isoformat(),
        }, ensure_ascii=False),
    }

    try:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/decisions",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
            },
            json=row, timeout=10,
        )
        status = "OK" if resp.ok else f"FAIL({resp.status_code})"
    except Exception as e:
        status = f"ERR({e})"
    print(f"    DB: {status}")


def main():
    from stable_baselines3 import PPO, SAC
    from scalp_ml.swing_env_v3 import SwingEnvV3, SwingEnvV3Continuous

    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    # ── 데이터 병합 ──
    print("\n[0] 데이터 병합...")
    merged_path = merge_data()

    # ── V4 설정: PPO 6개 + SAC 6개 = 12개 ──
    # hunt_results.json Top 라운드 하이퍼파라미터 기반
    configs = [
        # ── PPO: Top 라운드 기반 ──
        # R12 클론 (역대 최고 PnL +0.1433%)
        {"name": "PPO_R12_clone", "algo": "PPO", "continuous": False,
         "steps": 800_000,
         "kwargs": {"learning_rate": 0.0007, "gamma": 0.999,
                    "policy_kwargs": {"net_arch": [256, 128]},
                    "batch_size": 64, "ent_coef": 0.001, "n_steps": 2048}},

        # R15 클론 (역대 최고 WR 63.8%)
        {"name": "PPO_R15_clone", "algo": "PPO", "continuous": False,
         "steps": 400_000,
         "kwargs": {"learning_rate": 0.0005, "gamma": 0.95,
                    "policy_kwargs": {"net_arch": [128, 128]},
                    "batch_size": 256, "ent_coef": 0.05, "n_steps": 2048}},

        # R16 클론 (PnL +0.1256%, 작은 네트워크)
        {"name": "PPO_R16_clone", "algo": "PPO", "continuous": False,
         "steps": 400_000,
         "kwargs": {"learning_rate": 0.001, "gamma": 0.97,
                    "policy_kwargs": {"net_arch": [64, 64]},
                    "batch_size": 32, "ent_coef": 0.01, "n_steps": 4096}},

        # R12 변형: 더 작은 네트워크로 일반화 강화
        {"name": "PPO_R12_small", "algo": "PPO", "continuous": False,
         "steps": 600_000,
         "kwargs": {"learning_rate": 0.0005, "gamma": 0.999,
                    "policy_kwargs": {"net_arch": [128, 64]},
                    "batch_size": 64, "ent_coef": 0.005, "n_steps": 2048}},

        # PPO 신규: 높은 엔트로피 + 큰 배치 (탐험 강화)
        {"name": "PPO_explore", "algo": "PPO", "continuous": False,
         "steps": 600_000,
         "kwargs": {"learning_rate": 0.0003, "gamma": 0.98,
                    "policy_kwargs": {"net_arch": [128, 128]},
                    "batch_size": 128, "ent_coef": 0.08, "n_steps": 2048}},

        # PPO 신규: 매우 작은 네트워크 (과적합 최소화)
        {"name": "PPO_tiny", "algo": "PPO", "continuous": False,
         "steps": 400_000,
         "kwargs": {"learning_rate": 0.0005, "gamma": 0.97,
                    "policy_kwargs": {"net_arch": [64, 32]},
                    "batch_size": 64, "ent_coef": 0.03, "n_steps": 2048}},

        # ── SAC: Top 라운드 기반 ──
        # R7 클론 (PnL +0.1252%, WR 60.6%)
        {"name": "SAC_R7_clone", "algo": "SAC", "continuous": True,
         "steps": 700_000,
         "kwargs": {"learning_rate": 0.0005, "gamma": 0.999,
                    "policy_kwargs": {"net_arch": [256, 128]},
                    "batch_size": 128, "buffer_size": 200_000}},

        # R8 클론 (PnL +0.12%, RR 1.72)
        {"name": "SAC_R8_clone", "algo": "SAC", "continuous": True,
         "steps": 800_000,
         "kwargs": {"learning_rate": 0.0007, "gamma": 0.97,
                    "policy_kwargs": {"net_arch": [128, 64]},
                    "batch_size": 256, "buffer_size": 200_000}},

        # R10 클론 (WR 60.5%, 안정적)
        {"name": "SAC_R10_clone", "algo": "SAC", "continuous": True,
         "steps": 700_000,
         "kwargs": {"learning_rate": 0.0002, "gamma": 0.98,
                    "policy_kwargs": {"net_arch": [128, 128]},
                    "batch_size": 128, "buffer_size": 200_000}},

        # SAC 변형: 작은 네트워크
        {"name": "SAC_small", "algo": "SAC", "continuous": True,
         "steps": 500_000,
         "kwargs": {"learning_rate": 0.0003, "gamma": 0.99,
                    "policy_kwargs": {"net_arch": [64, 64]},
                    "batch_size": 128, "buffer_size": 100_000}},

        # SAC 변형: 느린 학습률 + 큰 버퍼 (안정)
        {"name": "SAC_stable", "algo": "SAC", "continuous": True,
         "steps": 600_000,
         "kwargs": {"learning_rate": 0.0001, "gamma": 0.995,
                    "policy_kwargs": {"net_arch": [128, 128]},
                    "batch_size": 256, "buffer_size": 300_000}},

        # SAC 변형: 빠른 학습 + 작은 네트워크
        {"name": "SAC_fast", "algo": "SAC", "continuous": True,
         "steps": 400_000,
         "kwargs": {"learning_rate": 0.001, "gamma": 0.97,
                    "policy_kwargs": {"net_arch": [64, 32]},
                    "batch_size": 64, "buffer_size": 100_000}},
    ]

    algo_map = {"PPO": PPO, "SAC": SAC}
    results = []

    # 이미 훈련된 모델 스킵 (resume 지원)
    existing_models = {p.stem.replace("v4_", "") for p in SAVE_DIR.glob("v4_*.zip")}

    print(f"\n{'='*80}")
    print(f"  V4 헌터: 2.5개월 데이터 + PPO/SAC 집중 + 과적합 방지")
    print(f"  {len(configs)}개 조합 (PPO 6 + SAC 6)")
    print(f"  훈련: 1/1~3/10 | 테스트: 3/10~3/17")
    print(f"  머신: {MACHINE}")
    if existing_models:
        print(f"  이미 훈련된 모델 ({len(existing_models)}개): {', '.join(sorted(existing_models))}")
    print(f"{'='*80}\n")

    total_start = time.time()

    for i, cfg in enumerate(configs):
        name = cfg["name"]

        # resume 지원
        if name in existing_models:
            print(f"[{i+1}/{len(configs)}] {name} — 이미 훈련됨, 스킵")
            continue

        steps = cfg["steps"]
        algo_cls = algo_map[cfg["algo"]]
        is_cont = cfg["continuous"]

        print(f"[{i+1}/{len(configs)}] {name} ({cfg['algo']}, {steps//1000}K)")

        # 환경 생성
        EnvCls = SwingEnvV3Continuous if is_cont else SwingEnvV3
        try:
            train_env = EnvCls(
                data_path=merged_path,
                date_from="2026-01-01", date_to="2026-03-10",
                sl_limit=0.4, filter_5x=True,
            )
            test_env = EnvCls(
                data_path=merged_path,
                date_from="2026-03-10", date_to="2026-03-17",
                sl_limit=0.4, filter_5x=True,
            )
        except ValueError as e:
            print(f"  환경 생성 실패: {e}")
            continue

        print(f"  훈련: {len(train_env.bars)}봉, {len(train_env.entry_points)}진입점")
        print(f"  테스트: {len(test_env.bars)}봉, {len(test_env.entry_points)}진입점")

        t0 = time.time()
        try:
            model = algo_cls("MlpPolicy", train_env, verbose=0, **cfg["kwargs"])
            model.learn(total_timesteps=steps, progress_bar=True)
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
            "round": i + 1,
            "name": name, "algo": cfg["algo"],
            "train_sec": train_sec, "steps": steps,
            "hyperparams": {k: str(v) for k, v in cfg["kwargs"].items()},
            "train": tr, "test": te,
        }
        results.append(entry)

        model.save(str(SAVE_DIR / f"v4_{name}"))

        # 결과 출력
        star = ""
        if te["avg_pnl"] > 0:
            star = " ★★★"
        elif te["avg_pnl"] > -0.03:
            star = " ★"

        print(f"  훈련: WR={tr['win_rate']}% PnL={tr['avg_pnl']:+.4f}% "
              f"RR={tr['rr_ratio']} PF={tr['profit_factor']}")
        print(f"  테스트: WR={te['win_rate']}% PnL={te['avg_pnl']:+.4f}% "
              f"RR={te['rr_ratio']} PF={te['profit_factor']}{star}")
        print(f"  청산: {te['exit_reasons']}")

        # 즉시 DB 기록
        save_round_to_db(entry, "v4")

        # 과적합 갭 경고
        gap = tr["avg_pnl"] - te["avg_pnl"]
        if gap > 0.1:
            print(f"  ⚠️ 과적합 경고: train-test 갭 {gap:+.4f}%")
        print()

    # ── 최종 순위 ──
    if results:
        ranked = sorted(results, key=lambda r: r["test"]["avg_pnl"], reverse=True)

        print(f"\n{'='*80}")
        print(f"  V4 최종 순위 ({len(ranked)}개 모델)")
        print(f"{'='*80}\n")
        print(f"  {'#':>2} {'모델':<20} {'알고':>4} {'스텝':>5} {'테스트PnL':>10} {'승률':>6} "
              f"{'RR':>5} {'PF':>5} {'보유':>5} {'훈련PnL':>10} {'갭':>8}")
        print(f"  {'─'*2} {'─'*20} {'─'*4} {'─'*5} {'─'*10} {'─'*6} {'─'*5} {'─'*5} {'─'*5} {'─'*10} {'─'*8}")

        for rank, r in enumerate(ranked, 1):
            te = r["test"]
            tr = r["train"]
            gap = tr["avg_pnl"] - te["avg_pnl"]
            star = " ★" if te["avg_pnl"] > 0 else ""
            print(f"  {rank:2d} {r['name']:<20} {r['algo']:>4} {r['steps']//1000:4d}K "
                  f"{te['avg_pnl']:+10.4f}% {te['win_rate']:5.1f}% "
                  f"{te['rr_ratio']:5.2f} {te['profit_factor']:5.2f} "
                  f"{te['avg_hold']:4.1f}봉 {tr['avg_pnl']:+10.4f}% {gap:+7.4f}%{star}")

        # 1위 상세
        best = ranked[0]
        te = best["test"]
        print(f"\n  🏆 1위: {best['name']} ({best['algo']}, {best['steps']//1000}K)")
        print(f"  테스트: {te['win_rate']}% ({te['wins']}승/{te['losses']}패)")
        print(f"  PnL: {te['avg_pnl']:+.4f}%, R:R: {te['rr_ratio']}, PF: {te['profit_factor']}")
        print(f"  이길때: +{te['avg_win']:.4f}%, 질때: -{te['avg_loss']:.4f}%")
        print(f"  Sharpe: {te['sharpe']}, 평균보유: {te['avg_hold']}봉 ({te['avg_hold']*5:.0f}분)")
        print(f"  청산: {te['exit_reasons']}")

        # JSON 저장
        json_path = SAVE_DIR / "hunt_results_v4.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "version": "v4",
                "strategy": "PPO/SAC focused, 2.5month data, overfitting prevention",
                "obs_dims": 20,
                "train_period": "2026-01-01~2026-03-10",
                "test_period": "2026-03-10~2026-03-17",
                "data_bars": "~18000 (Jan + Feb-Mar merged)",
                "hunt_time": datetime.now(KST).isoformat(),
                "machine": MACHINE,
                "total_minutes": round((time.time() - total_start) / 60, 1),
                "results": ranked,
            }, f, indent=2, ensure_ascii=False)
        print(f"\n  결과 JSON: {json_path}")

    elapsed = (time.time() - total_start) / 60
    print(f"\n{'='*80}")
    print(f"  V4 헌터 완료! {len(results)}/{len(configs)} 모델 | {elapsed:.0f}분 소요")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
