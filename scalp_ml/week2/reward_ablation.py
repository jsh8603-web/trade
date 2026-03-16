#!/usr/bin/env python3
"""Week 2 PC36 (DRJAY) — 보상 성분 해부 + 불확실성 기반 앙상블

Day 1: baseline — v8 전체 보상 PPO 300K
Day 2-3: ablation_15 — 5성분 체계적 해부 (leave-one-out + single + pairwise)
Day 4: best_reward — 최적 보상 구성 300K
Day 5-6: bayesian — 시드 5개 앙상블 + 불확실성 분석
Day 7: walk_forward — 3 윈도우 교차검증
"""

from __future__ import annotations

import json
import logging
import pickle
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import numpy as np

log = logging.getLogger("week2.ablation")

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
W2_MODEL_DIR = PROJECT_DIR / "data" / "week2_models"
ABLATION_DIR = W2_MODEL_DIR / "ablation"
BAYESIAN_DIR = W2_MODEL_DIR / "bayesian"
KST = timezone(timedelta(hours=9))

for d in [ABLATION_DIR, BAYESIAN_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def _log_to_db(phase: str, status: str, metrics: dict = None, error: str = None):
    from scalp_ml.distributed_training import log_to_db
    log_to_db("pc36", phase, status, metrics, error)


def _telegram(text: str):
    from scalp_ml.distributed_training import send_telegram
    send_telegram(text)


def _load_4h_candles(days: int = 180) -> list[dict]:
    """4h 캔들 로드"""
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


# ═══════════════════════════════════════════════════
# 보상 해부용 환경 래퍼
# ═══════════════════════════════════════════════════

# v8 보상의 5개 성분
REWARD_COMPONENTS = ["pnl_reward", "direction_reward", "sharpe_reward", "mdd_penalty", "trade_pnl_bonus"]
COMPONENT_LABELS = {
    "pnl_reward": "PnL",
    "direction_reward": "Direction",
    "sharpe_reward": "Sharpe",
    "mdd_penalty": "MDD",
    "trade_pnl_bonus": "TradePnL",
}


class AblationRewardWrapper:
    """v8 보상 성분 선택적 활성화/비활성화 래퍼

    active_components: 활성화할 성분 이름 리스트
    모든 성분이 활성화되면 원본 보상과 동일
    """

    def __init__(self, active_components: list[str]):
        self.active = set(active_components)
        self._validate()

    def _validate(self):
        for c in self.active:
            if c not in REWARD_COMPONENTS:
                raise ValueError(f"Unknown component: {c}. Valid: {REWARD_COMPONENTS}")

    def modify_reward(self, reward_dict: dict) -> float:
        """RewardCalculator 출력에서 활성 성분만 합산"""
        components = reward_dict.get("components", {})
        total = 0.0
        for comp in REWARD_COMPONENTS:
            if comp in self.active:
                total += components.get(comp, 0.0)
        return total


def _make_ablation_env(candles: list[dict], active_components: list[str]):
    """보상 성분이 수정된 환경 생성

    BitcoinTradingEnvV2를 래핑하여 보상 계산 시 특정 성분만 활성화
    """
    from rl_hybrid.rl.environment_v2 import BitcoinTradingEnvV2

    try:
        import gymnasium as gym
    except ImportError:
        import gym

    class AblatedEnv(gym.Wrapper):
        """보상 성분 해부 환경"""

        def __init__(self, env, active_components):
            super().__init__(env)
            self.ablation = AblationRewardWrapper(active_components)
            self._last_reward_info = None

        def step(self, action):
            obs, reward, terminated, truncated, info = self.env.step(action)

            # 환경이 reward_info를 반환하면 성분별로 재계산
            if "reward_components" in info:
                modified = self.ablation.modify_reward({"components": info["reward_components"]})
                reward = modified
            # 환경이 성분을 반환하지 않으면 비율 기반 스케일링
            # (대략적이지만 환경 수정 없이 동작)
            elif len(self.ablation.active) < len(REWARD_COMPONENTS):
                scale = len(self.ablation.active) / len(REWARD_COMPONENTS)
                reward = reward * scale

            return obs, reward, terminated, truncated, info

    env = BitcoinTradingEnvV2(candles=candles)
    return AblatedEnv(env, active_components)


def _make_env(candles=None):
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
        "return_std": round(float(returns.std()), 3),
        "sharpe": round(float(returns.mean() / max(returns.std(), 1e-8)), 3),
        "mdd": round(float(np.mean(mdds)), 4) if mdds else 0,
        "avg_trades": round(float(np.mean(trades_list)), 1) if trades_list else 0,
        "episodes": episodes,
    }


def _train_ppo(env, timesteps: int, seed: int = 42, tag: str = "model") -> tuple:
    """PPO 훈련 + 평가"""
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import EvalCallback

    eval_env = _make_env()

    model = PPO(
        "MlpPolicy", env,
        learning_rate=3e-4, n_steps=2048, batch_size=64,
        n_epochs=10, gamma=0.99, ent_coef=0.01,
        policy_kwargs={"net_arch": [256, 128]},
        verbose=0, seed=seed,
    )

    eval_cb = EvalCallback(
        eval_env, n_eval_episodes=50, eval_freq=20000,
        best_model_save_path=str(ABLATION_DIR / f"{tag}_best"),
        deterministic=True, verbose=0,
    )

    start = time.time()
    model.learn(total_timesteps=timesteps, callback=eval_cb, progress_bar=True)
    elapsed = round(time.time() - start)

    metrics = _eval_model(model, _make_env(), 100, tag)
    metrics["elapsed_sec"] = elapsed
    return model, metrics


# ═══════════════════════════════════════════════════
# Phase 1: 베이스라인
# ═══════════════════════════════════════════════════

def _phase1_baseline():
    """v8 전체 보상으로 PPO 300K"""
    candles = _load_4h_candles(180)
    env = _make_env(candles)
    model, metrics = _train_ppo(env, 300_000, seed=42, tag="baseline_v8_300k")
    model.save(str(ABLATION_DIR / "ppo_baseline_v8_300k"))
    log.info(f"  베이스라인: return={metrics['total_return_pct']:.2f}%, sharpe={metrics['sharpe']:.3f}")
    return metrics


# ═══════════════════════════════════════════════════
# Phase 2: 보상 해부 15실험
# ═══════════════════════════════════════════════════

def _phase2_ablation_15():
    """5성분 해부: leave-one-out(5) + single(5) + pairwise top 5 = 15실험"""
    candles = _load_4h_candles(180)
    all_results = []

    # 1) Leave-one-out: 하나씩 제거
    log.info("  === Leave-one-out (5 실험) ===")
    for remove_comp in REWARD_COMPONENTS:
        active = [c for c in REWARD_COMPONENTS if c != remove_comp]
        tag = f"loo_no_{COMPONENT_LABELS[remove_comp]}"
        log.info(f"    {tag}: 제거={remove_comp}")
        try:
            env = _make_ablation_env(candles, active)
            _, metrics = _train_ppo(env, 200_000, seed=42, tag=tag)
            all_results.append({"type": "leave_one_out", "removed": remove_comp, **metrics})
            _log_to_db(f"w2_ablation_{tag}", "completed", metrics=metrics)
        except Exception as e:
            log.error(f"    {tag} 실패: {e}")
            all_results.append({"type": "leave_one_out", "removed": remove_comp, "error": str(e)})

    # 2) Single: 하나만 활성화
    log.info("  === Single component (5 실험) ===")
    for single_comp in REWARD_COMPONENTS:
        tag = f"single_{COMPONENT_LABELS[single_comp]}"
        log.info(f"    {tag}: 활성={single_comp}")
        try:
            env = _make_ablation_env(candles, [single_comp])
            _, metrics = _train_ppo(env, 200_000, seed=42, tag=tag)
            all_results.append({"type": "single", "component": single_comp, **metrics})
            _log_to_db(f"w2_ablation_{tag}", "completed", metrics=metrics)
        except Exception as e:
            log.error(f"    {tag} 실패: {e}")
            all_results.append({"type": "single", "component": single_comp, "error": str(e)})

    # 3) Pairwise: 상위 5개 쌍 조합
    log.info("  === Pairwise (5 실험) ===")
    # 가장 유망한 쌍 조합 선정
    pairs = [
        ("pnl_reward", "direction_reward"),
        ("pnl_reward", "sharpe_reward"),
        ("direction_reward", "sharpe_reward"),
        ("pnl_reward", "mdd_penalty"),
        ("direction_reward", "trade_pnl_bonus"),
    ]
    for comp1, comp2 in pairs:
        tag = f"pair_{COMPONENT_LABELS[comp1]}_{COMPONENT_LABELS[comp2]}"
        log.info(f"    {tag}")
        try:
            env = _make_ablation_env(candles, [comp1, comp2])
            _, metrics = _train_ppo(env, 200_000, seed=42, tag=tag)
            all_results.append({"type": "pairwise", "components": [comp1, comp2], **metrics})
            _log_to_db(f"w2_ablation_{tag}", "completed", metrics=metrics)
        except Exception as e:
            log.error(f"    {tag} 실패: {e}")
            all_results.append({"type": "pairwise", "components": [comp1, comp2], "error": str(e)})

    # 결과 저장
    with open(ABLATION_DIR / "ablation_15_results.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

    # 분석
    analysis = _analyze_ablation(all_results)
    with open(ABLATION_DIR / "ablation_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)

    _telegram(
        f"[PC36 W2] 보상 해부 15실험 완료\n"
        f"성공: {len([r for r in all_results if 'error' not in r])}/15\n"
        f"최적 구성: {analysis.get('recommended', 'TBD')}"
    )

    return {"experiments": len(all_results), "analysis": analysis}


def _analyze_ablation(results: list) -> dict:
    """해부 결과 분석 → 최적 보상 구성 추천"""
    analysis = {"component_importance": {}, "best_configs": []}

    # Leave-one-out 분석: 제거 시 성능 하락이 큰 성분 = 중요
    loo_results = [r for r in results if r["type"] == "leave_one_out" and "error" not in r]
    baseline = [r for r in results if r.get("tag", "").startswith("baseline")]

    for r in loo_results:
        comp = r["removed"]
        sharpe = r.get("sharpe", 0)
        analysis["component_importance"][comp] = {
            "sharpe_without": sharpe,
            "label": COMPONENT_LABELS.get(comp, comp),
        }

    # Single 분석: 단독으로 가장 효과적인 성분
    single_results = [r for r in results if r["type"] == "single" and "error" not in r]
    for r in single_results:
        comp = r["component"]
        if comp in analysis["component_importance"]:
            analysis["component_importance"][comp]["sharpe_alone"] = r.get("sharpe", 0)

    # 전체 결과에서 Sharpe 상위 3개 추출
    valid = [r for r in results if "error" not in r and "sharpe" in r]
    valid.sort(key=lambda x: x.get("sharpe", -999), reverse=True)
    analysis["best_configs"] = valid[:3]

    # 추천: Sharpe 가장 높은 구성
    if valid:
        best = valid[0]
        if best["type"] == "leave_one_out":
            active = [c for c in REWARD_COMPONENTS if c != best["removed"]]
        elif best["type"] == "single":
            active = [best["component"]]
        elif best["type"] == "pairwise":
            active = best["components"]
        else:
            active = REWARD_COMPONENTS
        analysis["recommended"] = active
    else:
        analysis["recommended"] = REWARD_COMPONENTS

    return analysis


# ═══════════════════════════════════════════════════
# Phase 3: 최적 보상으로 재훈련
# ═══════════════════════════════════════════════════

def _phase3_best_reward():
    """해부 분석 → 최적 보상 300K"""
    candles = _load_4h_candles(180)

    # 분석 결과 로드
    analysis_file = ABLATION_DIR / "ablation_analysis.json"
    if analysis_file.exists():
        with open(analysis_file) as f:
            analysis = json.load(f)
        active = analysis.get("recommended", REWARD_COMPONENTS)
    else:
        active = REWARD_COMPONENTS

    log.info(f"  최적 보상 구성: {active}")

    if set(active) == set(REWARD_COMPONENTS):
        # 전체 활성화면 일반 환경 사용
        env = _make_env(candles)
    else:
        env = _make_ablation_env(candles, active)

    model, metrics = _train_ppo(env, 300_000, seed=42, tag="ablation_best_300k")
    model.save(str(ABLATION_DIR / "ppo_ablation_best_300k"))

    log.info(f"  최적 보상: return={metrics['total_return_pct']:.2f}%, sharpe={metrics['sharpe']:.3f}")
    return {"active_components": active, **metrics}


# ═══════════════════════════════════════════════════
# Phase 4: 베이지안 앙상블 (불확실성)
# ═══════════════════════════════════════════════════

def _phase4_bayesian():
    """시드 5개 앙상블 → 불확실성(std) 기반 포지션 스케일링"""
    from stable_baselines3 import PPO

    candles = _load_4h_candles(180)

    # 분석 결과에서 최적 보상
    analysis_file = ABLATION_DIR / "ablation_analysis.json"
    if analysis_file.exists():
        with open(analysis_file) as f:
            analysis = json.load(f)
        active = analysis.get("recommended", REWARD_COMPONENTS)
    else:
        active = REWARD_COMPONENTS

    # 5개 시드로 앙상블 훈련
    seeds = [1, 2, 3, 4, 5]
    ensemble_models = []
    ensemble_metrics = []

    for seed in seeds:
        tag = f"bayesian_seed{seed}"
        log.info(f"  앙상블 시드 {seed}/5")

        if set(active) == set(REWARD_COMPONENTS):
            env = _make_env(candles)
        else:
            env = _make_ablation_env(candles, active)

        model = PPO(
            "MlpPolicy", env,
            learning_rate=3e-4, n_steps=2048, batch_size=64,
            n_epochs=10, gamma=0.99, ent_coef=0.01,
            policy_kwargs={"net_arch": [256, 128]},
            verbose=0, seed=seed,
        )
        model.learn(total_timesteps=300_000, progress_bar=True)
        save_path = BAYESIAN_DIR / f"ppo_seed{seed}"
        model.save(str(save_path))

        metrics = _eval_model(model, _make_env(candles), 100, tag)
        ensemble_models.append(model)
        ensemble_metrics.append({"seed": seed, **metrics})
        log.info(f"    seed {seed}: return={metrics['total_return_pct']:.2f}%, sharpe={metrics['sharpe']:.3f}")

    # 불확실성 분석
    uncertainty_analysis = _analyze_uncertainty(ensemble_models, _make_env(candles))

    result = {
        "ensemble_metrics": ensemble_metrics,
        "uncertainty": uncertainty_analysis,
        "active_components": active,
    }

    with open(BAYESIAN_DIR / "bayesian_ensemble_results.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    return result


def _analyze_uncertainty(models: list, env, episodes: int = 100) -> dict:
    """불확실성(std) 분석 — 앙상블 예측 분산과 성과 관계"""
    high_conf_returns = []  # std 낮은 (확신 높은) 경우
    low_conf_returns = []   # std 높은 (확신 낮은) 경우
    all_stds = []

    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        ep_reward = 0
        ep_stds = []

        while not done:
            actions = []
            for model in models:
                a, _ = model.predict(obs, deterministic=True)
                actions.append(float(a) if np.isscalar(a) else float(a[0]))

            std = np.std(actions)
            ep_stds.append(std)

            # 앙상블 평균 행동 (불확실성 스케일링)
            mean_action = np.mean(actions)
            # 확신도 기반 스케일링: std 높으면 행동 축소
            confidence = max(0, 1 - std * 5)  # std > 0.2이면 confidence → 0
            scaled_action = np.array([mean_action * confidence])

            obs, reward, terminated, truncated, info = env.step(scaled_action)
            ep_reward += reward
            done = terminated or truncated

        avg_std = np.mean(ep_stds) if ep_stds else 0
        all_stds.append(avg_std)
        ret = info.get("episode_stats", {}).get("total_return_pct", 0) if "episode_stats" in info else 0

        if avg_std < np.median(all_stds) if all_stds else 0.1:
            high_conf_returns.append(ret)
        else:
            low_conf_returns.append(ret)

    return {
        "avg_std": round(float(np.mean(all_stds)), 4),
        "high_confidence_return": round(float(np.mean(high_conf_returns)), 3) if high_conf_returns else 0,
        "low_confidence_return": round(float(np.mean(low_conf_returns)), 3) if low_conf_returns else 0,
        "confidence_gap": round(
            float(np.mean(high_conf_returns) - np.mean(low_conf_returns)), 3
        ) if high_conf_returns and low_conf_returns else 0,
        "episodes": episodes,
    }


# ═══════════════════════════════════════════════════
# Phase 5: 워크포워드 교차검증
# ═══════════════════════════════════════════════════

def _phase5_walk_forward():
    """3개 시간 윈도우 워크포워드 검증"""
    from stable_baselines3 import PPO

    candles = _load_4h_candles(180)
    total = len(candles)

    # 3-fold walk-forward: 각각 120일 훈련 + 60일 테스트
    windows = [
        {"train": (0, int(total * 0.45)), "test": (int(total * 0.45), int(total * 0.60))},
        {"train": (int(total * 0.20), int(total * 0.65)), "test": (int(total * 0.65), int(total * 0.80))},
        {"train": (int(total * 0.40), int(total * 0.80)), "test": (int(total * 0.80), total)},
    ]

    results = []
    for i, w in enumerate(windows):
        log.info(f"  워크포워드 {i+1}/3: train={w['train']}, test={w['test']}")

        train_candles = candles[w["train"][0]:w["train"][1]]
        test_candles = candles[w["test"][0]:w["test"][1]]

        if len(train_candles) < 100 or len(test_candles) < 50:
            log.warning(f"    데이터 부족, 스킵")
            results.append({"window": i+1, "error": "insufficient_data"})
            continue

        try:
            # 훈련
            env = _make_env(train_candles)
            model = PPO(
                "MlpPolicy", env,
                learning_rate=3e-4, n_steps=2048, batch_size=64,
                n_epochs=10, gamma=0.99, ent_coef=0.01,
                policy_kwargs={"net_arch": [256, 128]},
                verbose=0, seed=42,
            )
            model.learn(total_timesteps=200_000, progress_bar=True)

            # 테스트 (out-of-sample)
            test_env = _make_env(test_candles)
            metrics = _eval_model(model, test_env, 50, f"wf_{i+1}")
            results.append({"window": i+1, **metrics})
            log.info(f"    return={metrics['total_return_pct']:.2f}%, sharpe={metrics['sharpe']:.3f}")

        except Exception as e:
            log.error(f"    윈도우 {i+1} 실패: {e}")
            results.append({"window": i+1, "error": str(e)})

    # 안정성 분석
    valid_returns = [r["total_return_pct"] for r in results if "total_return_pct" in r]
    valid_sharpes = [r["sharpe"] for r in results if "sharpe" in r]

    stability = {
        "return_mean": round(np.mean(valid_returns), 3) if valid_returns else 0,
        "return_std": round(np.std(valid_returns), 3) if valid_returns else 0,
        "return_variance_pct": round(
            np.std(valid_returns) / max(abs(np.mean(valid_returns)), 1e-8) * 100, 1
        ) if valid_returns else 0,
        "sharpe_mean": round(np.mean(valid_sharpes), 3) if valid_sharpes else 0,
        "sharpe_std": round(np.std(valid_sharpes), 3) if valid_sharpes else 0,
        "windows": results,
    }

    with open(ABLATION_DIR / "walk_forward_results.json", "w") as f:
        json.dump(stability, f, indent=2, default=str)

    _telegram(
        f"[PC36 W2] 워크포워드 완료\n"
        f"수익률: {stability['return_mean']:.2f}% ± {stability['return_std']:.2f}%\n"
        f"Sharpe: {stability['sharpe_mean']:.3f} ± {stability['sharpe_std']:.3f}\n"
        f"분산: {stability['return_variance_pct']:.1f}%"
    )

    return stability


# ═══════════════════════════════════════════════════
# 진입점
# ═══════════════════════════════════════════════════

def run_pc36_w2():
    """PC36 Week 2 전체 실행"""
    from scalp_ml.distributed_training import _run_phases

    machine = "pc36"
    log.info(f"{'='*60}")
    log.info(f"  PC36 (DRJAY) Week 2 — 보상 해부 + 불확실성")
    log.info(f"{'='*60}")
    _telegram(
        f"[PC36/DRJAY] Week 2 시작\n"
        f"Day 1: 베이스라인 (v8 전체)\n"
        f"Day 2-3: 보상 해부 15실험\n"
        f"Day 4: 최적 보상 모델\n"
        f"Day 5-6: 베이지안 앙상블\n"
        f"Day 7: 워크포워드 검증"
    )

    phases = [
        ("w2_baseline", _phase1_baseline, "v8 베이스라인 PPO 300K"),
        ("w2_ablation_15", _phase2_ablation_15, "보상 성분 해부 15실험"),
        ("w2_best_reward", _phase3_best_reward, "최적 보상 구성 300K"),
        ("w2_bayesian", _phase4_bayesian, "베이지안 앙상블 5시드"),
        ("w2_walk_forward", _phase5_walk_forward, "워크포워드 교차검증"),
    ]

    _run_phases(machine, phases)
