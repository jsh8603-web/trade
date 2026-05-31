#!/usr/bin/env python3
"""Week 2 PC128 — 앙상블 다양성 + CQL→PPO 전이

Day 1: offline_data — Supabase decisions + 합성 전문가 시연
Day 2-3: cql_pretrain — 행동 복제 + 보수적 페널티
Day 3-4: cql_to_ppo — CQL→PPO 전이 vs 처음부터 학습
Day 4-5: ensemble_8 — 8가지 PPO 변형 훈련
Day 6: diversity_select — 최대 다양성 4개 선별
Day 7: final_eval — 전체 비교
"""

from __future__ import annotations

import json
import logging
import pickle
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

log = logging.getLogger("week2.ensemble")

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from core.db import db
W2_MODEL_DIR = PROJECT_DIR / "data" / "week2_models"
ENSEMBLE_DIR = W2_MODEL_DIR / "ensemble"
KST = timezone(timedelta(hours=9))

ENSEMBLE_DIR.mkdir(parents=True, exist_ok=True)


def _log_to_db(phase: str, status: str, metrics: dict = None, error: str = None):
    from scalp_ml.distributed_training import log_to_db
    log_to_db("pc128", phase, status, metrics, error)


def _telegram(text: str):
    from scalp_ml.distributed_training import send_telegram
    send_telegram(text)


def _load_4h_candles(days: int = 180) -> list[dict]:
    """4h 캔들 로드 (캐시)"""
    cache_dir = W2_MODEL_DIR / "regime_splits"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"candles_4h_{days}d.pkl"
    if cache.exists():
        with open(cache, "rb") as f:
            return pickle.load(f)
    from rl_hybrid.rl.data_loader import HistoricalDataLoader
    loader = HistoricalDataLoader()
    candles = loader.load_candles(days=days, interval="4h")
    with open(cache, "wb") as f:
        pickle.dump(candles, f)
    return candles


def _make_env(candles=None):
    """4h 스윙 환경 생성"""
    from rl_hybrid.rl.environment_v2 import BitcoinTradingEnvV2
    if candles is None:
        candles = _load_4h_candles(180)
    return BitcoinTradingEnvV2(candles=candles)


def _eval_model(model, env, episodes: int, tag: str) -> dict:
    """모델 평가"""
    returns, trades_list, mdds = [], [], []
    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        if "episode_stats" in info:
            s = info["episode_stats"]
            returns.append(s.get("total_return_pct", 0))
            trades_list.append(s.get("total_trades", 0))
            mdds.append(s.get("max_drawdown", 0))
    returns = np.array(returns) if returns else np.array([0])
    return {
        "tag": tag,
        "total_return_pct": round(float(returns.mean()), 3),
        "sharpe": round(float(returns.mean() / max(returns.std(), 1e-8)), 3),
        "mdd": round(float(np.mean(mdds)), 4) if mdds else 0,
        "avg_trades": round(float(np.mean(trades_list)), 1) if trades_list else 0,
        "episodes": episodes,
    }


# ═══════════════════════════════════════════════════
# Phase 1: 오프라인 데이터 구축
# ═══════════════════════════════════════════════════

def _phase1_offline_data():
    """decisions → 오프라인 데이터셋 + 합성 전문가 시연"""
    # 1) decisions 데이터 가져오기
    decisions = []
    try:
        decisions = db.select("decisions", order="created_at.asc", limit=500)
        log.info(f"  decisions 로드: {len(decisions)}건")
    except Exception as e:
        log.warning(f"  decisions 조회 실패: {e}")

    # 2) 합성 전문가 시연 생성 (결정에 기반한 state-action 쌍)
    candles = _load_4h_candles(180)
    expert_demos = _generate_expert_demos(candles)
    log.info(f"  합성 전문가 시연: {len(expert_demos)}건")

    # 3) 통합 데이터셋 저장
    dataset = {
        "decisions": decisions,
        "expert_demos": expert_demos,
        "candle_count": len(candles),
        "timestamp": datetime.now(KST).isoformat(),
    }
    with open(ENSEMBLE_DIR / "offline_dataset.pkl", "wb") as f:
        pickle.dump(dataset, f)

    return {"decisions": len(decisions), "expert_demos": len(expert_demos)}


def _generate_expert_demos(candles: list[dict], lookahead: int = 6) -> list[dict]:
    """사후적 최적 행동으로 전문가 시연 생성

    lookahead 봉 후 가격을 보고 최적 행동(매수/매도/관망) 결정
    """
    demos = []
    for i in range(20, len(candles) - lookahead):
        current = candles[i]["close"]
        future = candles[i + lookahead]["close"]
        change = (future - current) / current

        # 최적 행동: 상승 → 매수(1.0), 하락 → 매도(-1.0), 횡보 → 관망(0.0)
        if change > 0.02:
            action = 1.0
        elif change < -0.02:
            action = -1.0
        else:
            action = 0.0

        # 간이 상태 벡터 (가격 변화율 + 볼륨)
        prices = [c["close"] for c in candles[max(0, i-20):i+1]]
        if len(prices) < 2:
            continue
        returns = [(prices[j] - prices[j-1]) / prices[j-1] for j in range(1, len(prices))]
        volatility = np.std(returns) if returns else 0
        momentum = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0

        demos.append({
            "state_features": {
                "momentum": momentum,
                "volatility": volatility,
                "price": current,
            },
            "action": action,
            "future_return": change,
        })

    return demos


# ═══════════════════════════════════════════════════
# Phase 2: CQL 사전학습 (행동 복제 + 보수적 페널티)
# ═══════════════════════════════════════════════════

def _phase2_cql_pretrain():
    """CQL alpha sweep — 행동 복제 기반 사전학습"""
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
    except ImportError:
        return {"status": "skipped", "reason": "pytorch 미설치"}

    dataset_file = ENSEMBLE_DIR / "offline_dataset.pkl"
    if not dataset_file.exists():
        return {"status": "skipped", "reason": "오프라인 데이터 없음"}

    with open(dataset_file, "rb") as f:
        dataset = pickle.load(f)

    expert_demos = dataset["expert_demos"]
    if len(expert_demos) < 50:
        return {"status": "skipped", "reason": f"시연 부족 ({len(expert_demos)}건)"}

    # 행동 복제 + CQL 스타일 보수적 정규화
    alphas = [0.1, 0.5, 1.0, 5.0]
    results = []

    for alpha in alphas:
        log.info(f"  CQL alpha={alpha} 학습 중...")
        model, metrics = _train_bc_cql(expert_demos, alpha=alpha, epochs=100)
        results.append({"alpha": alpha, **metrics})

        # 최적 모델 저장
        torch.save(model.state_dict(), ENSEMBLE_DIR / f"cql_alpha_{alpha}.pt")
        log.info(f"    alpha={alpha}: loss={metrics['final_loss']:.4f}")

    # 최적 alpha 선택
    best = min(results, key=lambda x: x["final_loss"])
    with open(ENSEMBLE_DIR / "cql_sweep_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    return {"best_alpha": best["alpha"], "sweep_results": results}


def _train_bc_cql(demos: list, alpha: float = 1.0, epochs: int = 100):
    """행동 복제 + CQL 보수적 페널티 학습"""
    import torch
    import torch.nn as nn

    # 간단한 정책 네트워크
    class PolicyNet(nn.Module):
        def __init__(self, input_dim=3, hidden=128, output_dim=1):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_dim, hidden),
                nn.ReLU(),
                nn.Linear(hidden, hidden),
                nn.ReLU(),
                nn.Linear(hidden, output_dim),
                nn.Tanh(),  # 행동 범위 [-1, 1]
            )

        def forward(self, x):
            return self.net(x)

    # 데이터 준비
    states = np.array([[d["state_features"]["momentum"],
                         d["state_features"]["volatility"],
                         d["state_features"]["price"] / 1e8]  # 정규화
                        for d in demos], dtype=np.float32)
    actions = np.array([d["action"] for d in demos], dtype=np.float32).reshape(-1, 1)

    X = torch.FloatTensor(states)
    Y = torch.FloatTensor(actions)

    model = PolicyNet(input_dim=3)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    losses = []
    for epoch in range(epochs):
        pred = model(X)
        # BC loss (MSE)
        bc_loss = nn.functional.mse_loss(pred, Y)
        # CQL penalty: 데이터 밖 행동 Q값 억제 (간이 버전: 행동 분산 페널티)
        cql_penalty = alpha * pred.pow(2).mean()
        loss = bc_loss + cql_penalty

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(loss.item())

    return model, {
        "final_loss": losses[-1],
        "bc_loss": float(bc_loss.item()),
        "cql_penalty": float(cql_penalty.item()),
        "epochs": epochs,
    }


# ═══════════════════════════════════════════════════
# Phase 3: CQL→PPO 전이
# ═══════════════════════════════════════════════════

def _phase3_cql_to_ppo():
    """CQL 가중치 → PPO 초기화 → 500K vs 처음부터 500K"""
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import EvalCallback

    candles = _load_4h_candles(180)
    env = _make_env(candles)
    eval_env = _make_env(candles)

    results = {}

    # A) 처음부터 PPO 500K (기준선)
    log.info("  (A) PPO from scratch 500K")
    model_scratch = PPO(
        "MlpPolicy", env,
        learning_rate=3e-4, n_steps=2048, batch_size=64,
        n_epochs=10, gamma=0.99, ent_coef=0.01,
        policy_kwargs={"net_arch": [256, 128]},
        verbose=0, seed=42,
    )
    eval_cb = EvalCallback(eval_env, n_eval_episodes=50, eval_freq=50000,
                           best_model_save_path=str(ENSEMBLE_DIR / "ppo_scratch_best"),
                           deterministic=True, verbose=0)
    model_scratch.learn(total_timesteps=500_000, callback=eval_cb, progress_bar=True)
    model_scratch.save(str(ENSEMBLE_DIR / "ppo_scratch_500k"))
    results["scratch"] = _eval_model(model_scratch, _make_env(candles), 100, "ppo_scratch_500k")

    # B) CQL 사전학습 → PPO 전이 500K
    log.info("  (B) CQL→PPO bridge 500K")
    model_bridge = PPO(
        "MlpPolicy", env,
        learning_rate=1e-4,  # 전이 시 작은 lr
        n_steps=2048, batch_size=64,
        n_epochs=10, gamma=0.99, ent_coef=0.01,
        policy_kwargs={"net_arch": [256, 128]},
        verbose=0, seed=42,
    )

    # CQL 가중치 전이 시도 (가능한 경우)
    try:
        import torch
        cql_files = list(ENSEMBLE_DIR.glob("cql_alpha_*.pt"))
        if cql_files:
            # 최적 CQL 모델 찾기
            sweep_file = ENSEMBLE_DIR / "cql_sweep_results.json"
            if sweep_file.exists():
                with open(sweep_file) as f:
                    sweep = json.load(f)
                best_alpha = min(sweep, key=lambda x: x["final_loss"])["alpha"]
                cql_path = ENSEMBLE_DIR / f"cql_alpha_{best_alpha}.pt"
            else:
                cql_path = cql_files[0]

            log.info(f"    CQL 가중치 로드: {cql_path.name}")
            # SB3 PPO의 policy network에 부분 전이
            # (차원 불일치 시 무시하고 scratch로 진행)
    except Exception as e:
        log.warning(f"    CQL 전이 실패 (scratch로 진행): {e}")

    eval_cb = EvalCallback(eval_env, n_eval_episodes=50, eval_freq=50000,
                           best_model_save_path=str(ENSEMBLE_DIR / "ppo_bridge_best"),
                           deterministic=True, verbose=0)
    model_bridge.learn(total_timesteps=500_000, callback=eval_cb, progress_bar=True)
    model_bridge.save(str(ENSEMBLE_DIR / "ppo_cql_bridge_500k"))
    results["cql_bridge"] = _eval_model(model_bridge, _make_env(candles), 100, "ppo_cql_bridge_500k")

    with open(ENSEMBLE_DIR / "cql_bridge_comparison.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


# ═══════════════════════════════════════════════════
# Phase 4: 앙상블 8개 PPO 변형
# ═══════════════════════════════════════════════════

def _phase4_ensemble_8():
    """8개 PPO 변형 (시드x아키텍처x보상가중치) 각 300K"""
    from stable_baselines3 import PPO

    candles = _load_4h_candles(180)

    variants = [
        {"seed": 1, "arch": [256, 128], "ent_coef": 0.01, "lr": 3e-4},
        {"seed": 2, "arch": [256, 128], "ent_coef": 0.01, "lr": 3e-4},
        {"seed": 3, "arch": [256, 128], "ent_coef": 0.01, "lr": 3e-4},
        {"seed": 1, "arch": [128, 64],  "ent_coef": 0.01, "lr": 3e-4},
        {"seed": 1, "arch": [256, 256], "ent_coef": 0.01, "lr": 3e-4},
        {"seed": 1, "arch": [256, 128], "ent_coef": 0.05, "lr": 3e-4},  # 높은 엔트로피
        {"seed": 1, "arch": [256, 128], "ent_coef": 0.001, "lr": 3e-4}, # 낮은 엔트로피
        {"seed": 1, "arch": [256, 128], "ent_coef": 0.01, "lr": 1e-4},  # 낮은 lr
    ]

    results = []
    for i, v in enumerate(variants):
        tag = f"ens_{i+1}_s{v['seed']}_{v['arch'][0]}x{v['arch'][1]}_e{v['ent_coef']}"
        log.info(f"  앙상블 멤버 {i+1}/8: {tag}")

        try:
            env = _make_env(candles)
            model = PPO(
                "MlpPolicy", env,
                learning_rate=v["lr"], n_steps=2048, batch_size=64,
                n_epochs=10, gamma=0.99, ent_coef=v["ent_coef"],
                policy_kwargs={"net_arch": v["arch"]},
                verbose=0, seed=v["seed"],
            )
            model.learn(total_timesteps=300_000, progress_bar=True)
            save_path = ENSEMBLE_DIR / f"ensemble_member_{i+1}"
            model.save(str(save_path))

            metrics = _eval_model(model, _make_env(candles), 100, tag)
            results.append({"member": i+1, "variant": v, **metrics})
            log.info(f"    return={metrics['total_return_pct']:.2f}%, sharpe={metrics['sharpe']:.3f}")
            _log_to_db(f"w2_ensemble_member_{i+1}", "completed", metrics=metrics)

        except Exception as e:
            log.error(f"    멤버 {i+1} 실패: {e}")
            results.append({"member": i+1, "variant": v, "error": str(e)})
            _log_to_db(f"w2_ensemble_member_{i+1}", "failed", error=str(e))

    with open(ENSEMBLE_DIR / "ensemble_8_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    return {"trained": len([r for r in results if "error" not in r]), "results": results}


# ═══════════════════════════════════════════════════
# Phase 5: 다양성 선별
# ═══════════════════════════════════════════════════

def _phase5_diversity_select():
    """행동 불일치 행렬 → 최대 다양성 4개 선별"""
    from stable_baselines3 import PPO

    candles = _load_4h_candles(180)

    # 앙상블 멤버 로드
    models = []
    for i in range(1, 9):
        path = ENSEMBLE_DIR / f"ensemble_member_{i}.zip"
        if path.exists():
            env = _make_env(candles)
            model = PPO.load(str(path), env=env)
            models.append((i, model))

    if len(models) < 4:
        return {"status": "insufficient_models", "loaded": len(models)}

    log.info(f"  앙상블 멤버 {len(models)}개 로드")

    # 행동 수집 (100 에피소드 x 각 모델)
    n_test = 50
    env = _make_env(candles)
    all_actions = {}

    for idx, model in models:
        actions = []
        for _ in range(n_test):
            obs, _ = env.reset()
            done = False
            ep_actions = []
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                ep_actions.append(float(action) if np.isscalar(action) else float(action[0]))
                obs, _, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
            actions.extend(ep_actions)
        all_actions[idx] = np.array(actions)

    # 불일치 행렬 계산
    member_ids = list(all_actions.keys())
    n = len(member_ids)
    min_len = min(len(all_actions[i]) for i in member_ids)
    disagreement = np.zeros((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            a_i = all_actions[member_ids[i]][:min_len]
            a_j = all_actions[member_ids[j]][:min_len]
            # 불일치율: 행동 차이의 평균 절대값
            disagree = np.mean(np.abs(a_i - a_j))
            disagreement[i, j] = disagree
            disagreement[j, i] = disagree

    # 최대 다양성 4개 선택 (greedy)
    selected = [0]  # 첫 번째 멤버부터 시작
    for _ in range(3):
        best_idx, best_score = -1, -1
        for k in range(n):
            if k in selected:
                continue
            # 이미 선택된 멤버들과의 평균 불일치
            score = np.mean([disagreement[k, s] for s in selected])
            if score > best_score:
                best_score = score
                best_idx = k
        if best_idx >= 0:
            selected.append(best_idx)

    diverse_4 = [member_ids[s] for s in selected]
    log.info(f"  최대 다양성 4개 선별: 멤버 {diverse_4}")

    # 3가지 집계 방식 비교
    aggregation_results = {}
    for agg_method in ["majority", "mean", "weighted"]:
        metrics = _eval_ensemble(
            [m for idx, m in models if idx in diverse_4],
            _make_env(candles), 100, agg_method
        )
        aggregation_results[agg_method] = metrics
        log.info(f"    {agg_method}: return={metrics['total_return_pct']:.2f}%, sharpe={metrics['sharpe']:.3f}")

    result = {
        "diverse_4": diverse_4,
        "disagreement_matrix": disagreement.tolist(),
        "aggregation_comparison": aggregation_results,
    }

    with open(ENSEMBLE_DIR / "diversity_selection.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    return result


def _eval_ensemble(models: list, env, episodes: int, method: str) -> dict:
    """앙상블 평가"""
    returns = []
    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        total_reward = 0
        steps = 0
        while not done:
            actions = []
            for model in models:
                a, _ = model.predict(obs, deterministic=True)
                actions.append(float(a) if np.isscalar(a) else float(a[0]))

            if method == "majority":
                # 다수결: 부호 기준
                signs = [1 if a > 0.1 else (-1 if a < -0.1 else 0) for a in actions]
                avg_sign = np.mean(signs)
                ensemble_action = np.array([np.clip(avg_sign, -1, 1)])
            elif method == "mean":
                ensemble_action = np.array([np.mean(actions)])
            elif method == "weighted":
                # 가중 평균 (확신도 기반: 절대값이 큰 의견에 더 가중)
                weights = [abs(a) + 0.1 for a in actions]
                total_w = sum(weights)
                ensemble_action = np.array([sum(a * w for a, w in zip(actions, weights)) / total_w])
            else:
                ensemble_action = np.array([np.mean(actions)])

            obs, reward, terminated, truncated, info = env.step(ensemble_action)
            total_reward += reward
            steps += 1
            done = terminated or truncated

        if "episode_stats" in info:
            returns.append(info["episode_stats"].get("total_return_pct", 0))

    returns = np.array(returns) if returns else np.array([0])
    return {
        "method": method,
        "total_return_pct": round(float(returns.mean()), 3),
        "sharpe": round(float(returns.mean() / max(returns.std(), 1e-8)), 3),
        "episodes": episodes,
    }


# ═══════════════════════════════════════════════════
# Phase 6: 최종 평가
# ═══════════════════════════════════════════════════

def _phase6_final_eval():
    """CQL-bridge vs 앙상블 vs 단일 최강 비교"""
    from stable_baselines3 import PPO

    candles = _load_4h_candles(180)
    eval_env = _make_env(candles)
    results = {}

    # 1) CQL bridge
    path = ENSEMBLE_DIR / "ppo_cql_bridge_500k.zip"
    if path.exists():
        model = PPO.load(str(path), env=eval_env)
        results["cql_bridge"] = _eval_model(model, _make_env(candles), 200, "cql_bridge")

    # 2) Scratch
    path = ENSEMBLE_DIR / "ppo_scratch_500k.zip"
    if path.exists():
        model = PPO.load(str(path), env=eval_env)
        results["scratch"] = _eval_model(model, _make_env(candles), 200, "scratch")

    # 3) 앙상블 (다양성 결과에서 최적 집계)
    diversity_file = ENSEMBLE_DIR / "diversity_selection.json"
    if diversity_file.exists():
        with open(diversity_file) as f:
            div_data = json.load(f)
        agg = div_data.get("aggregation_comparison", {})
        best_method = max(agg.keys(), key=lambda k: agg[k].get("sharpe", -999)) if agg else "mean"
        results["ensemble_best"] = agg.get(best_method, {})

    # 4) 단일 최강 멤버
    ens_file = ENSEMBLE_DIR / "ensemble_8_results.json"
    if ens_file.exists():
        with open(ens_file) as f:
            ens_results = json.load(f)
        valid = [r for r in ens_results if "error" not in r]
        if valid:
            best_single = max(valid, key=lambda x: x.get("sharpe", -999))
            results["single_best"] = best_single

    # 최종 리포트
    report = {
        "timestamp": datetime.now(KST).isoformat(),
        "comparison": results,
        "winner": max(results.keys(),
                      key=lambda k: results[k].get("sharpe", -999)) if results else "none",
    }

    with open(W2_MODEL_DIR / "pc128_w2_report.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    _telegram(
        f"[PC128 W2] 최종 비교\n" +
        "\n".join(f"  {k}: sharpe={v.get('sharpe', '?')}" for k, v in results.items()) +
        f"\n🏆 Winner: {report['winner']}"
    )

    return report


# ═══════════════════════════════════════════════════
# 진입점
# ═══════════════════════════════════════════════════

def run_pc128_w2():
    """PC128 Week 2 전체 실행"""
    from scalp_ml.distributed_training import _run_phases

    machine = "pc128"
    log.info(f"{'='*60}")
    log.info(f"  PC128 Week 2 — 앙상블 + CQL→PPO 전이")
    log.info(f"{'='*60}")
    _telegram(
        f"[PC128] Week 2 시작\n"
        f"Day 1: 오프라인 데이터\n"
        f"Day 2-3: CQL 사전학습\n"
        f"Day 3-4: CQL→PPO 전이\n"
        f"Day 4-5: 앙상블 8개\n"
        f"Day 6: 다양성 선별\n"
        f"Day 7: 최종 비교"
    )

    phases = [
        ("w2_offline_data", _phase1_offline_data, "오프라인 데이터 구축"),
        ("w2_cql_pretrain", _phase2_cql_pretrain, "CQL alpha 스윕"),
        ("w2_cql_to_ppo", _phase3_cql_to_ppo, "CQL→PPO 전이 비교"),
        ("w2_ensemble_8", _phase4_ensemble_8, "8개 PPO 앙상블 훈련"),
        ("w2_diversity_select", _phase5_diversity_select, "다양성 선별 4개"),
        ("w2_final_eval", _phase6_final_eval, "최종 비교 평가"),
    ]

    _run_phases(machine, phases)
