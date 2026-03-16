#!/usr/bin/env python3
"""Week 2 Mac Mini — 레짐 전문가 팩토리 + 커리큘럼 학습

Day 1: regime_split — 180일 4h 캔들 → bull/bear/sideways/volatile 분할
Day 2-3: specialists — 레짐별 PPO+SAC 200K 전문가 모델
Day 4-5: curriculum — Easy→Hard/Hard→Easy/Random 커리큘럼 학습
Day 6: best_curriculum — 최적 순서 1M 장기 훈련
Day 7: integration — 메타 선택기 + 비교 리포트
"""

from __future__ import annotations

import json
import logging
import pickle
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

log = logging.getLogger("week2.regime")

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
W2_MODEL_DIR = PROJECT_DIR / "data" / "week2_models"
KST = timezone(timedelta(hours=9))

# Subdirectories
REGIME_DIR = W2_MODEL_DIR / "regime_splits"
SPECIALIST_DIR = W2_MODEL_DIR / "specialists"
CURRICULUM_DIR = W2_MODEL_DIR / "curriculum"

for d in [REGIME_DIR, SPECIALIST_DIR, CURRICULUM_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def _log_to_db(phase: str, status: str, metrics: dict = None, error: str = None):
    from scalp_ml.distributed_training import log_to_db
    log_to_db("mac-mini", phase, status, metrics, error)


def _telegram(text: str):
    from scalp_ml.distributed_training import send_telegram
    send_telegram(text)


# ═══════════════════════════════════════════════════
# Phase 1: 레짐 분할
# ═══════════════════════════════════════════════════

def _load_4h_candles(days: int = 180) -> list[dict]:
    """Upbit 4h 캔들 로드 (캐시 포함)"""
    cache = REGIME_DIR / f"candles_4h_{days}d.pkl"
    if cache.exists():
        with open(cache, "rb") as f:
            candles = pickle.load(f)
        log.info(f"4h 캔들 캐시 로드: {len(candles)}건")
        return candles

    from rl_hybrid.rl.data_loader import HistoricalDataLoader
    loader = HistoricalDataLoader()
    candles = loader.load_candles(days=days, interval="4h")
    with open(cache, "wb") as f:
        pickle.dump(candles, f)
    log.info(f"4h 캔들 수집 완료: {len(candles)}건")
    return candles


def _classify_regimes(candles: list[dict], lookback: int = 20) -> tuple[np.ndarray, dict]:
    """HMM 기반 4-state 레짐 분류 + 전이 행렬

    Returns:
        labels: 레짐 라벨 배열 (0=bull, 1=bear, 2=sideways, 3=volatile)
        info: 통계 + 전이 행렬
    """
    # 피처 추출: 수익률, 변동성, 거래량 변화율
    features = []
    for i in range(lookback, len(candles)):
        window = candles[i - lookback:i + 1]
        prices = [c["close"] for c in window]
        returns = [(prices[j] - prices[j-1]) / prices[j-1] for j in range(1, len(prices))]

        total_ret = (prices[-1] - prices[0]) / prices[0]
        volatility = np.std(returns) if returns else 0.01
        avg_vol = np.mean([c.get("volume", 0) for c in window[-5:]])
        prev_vol = np.mean([c.get("volume", 0) for c in window[:5]]) or 1
        vol_ratio = avg_vol / max(prev_vol, 1e-10)

        features.append([total_ret, volatility, vol_ratio])

    X = np.array(features)

    # HMM 시도 → GMM 대체
    try:
        from hmmlearn.hmm import GaussianHMM
        best_model, best_bic = None, float("inf")
        for n in [4]:
            model = GaussianHMM(n_components=n, covariance_type="diag",
                                n_iter=300, random_state=42)
            model.fit(X)
            bic = -2 * model.score(X) + n * X.shape[1] * np.log(len(X))
            if bic < best_bic:
                best_bic = bic
                best_model = model
        raw_labels = best_model.predict(X)
    except ImportError:
        from sklearn.mixture import GaussianMixture
        model = GaussianMixture(n_components=4, random_state=42, max_iter=300)
        model.fit(X)
        raw_labels = model.predict(X)

    # 레짐 라벨 매핑: 수익률 기준 정렬
    regime_means = {}
    for r in range(4):
        mask = raw_labels == r
        if mask.sum() > 0:
            regime_means[r] = np.mean(X[mask, 0])  # 평균 수익률
        else:
            regime_means[r] = 0

    sorted_regimes = sorted(regime_means.keys(), key=lambda k: regime_means[k], reverse=True)
    # 매핑: 가장 높은 수익률 → bull(0), 가장 낮은 → bear(1), 나머지 변동성으로 구분
    label_map = {}
    label_map[sorted_regimes[0]] = 0  # bull
    label_map[sorted_regimes[-1]] = 1  # bear
    # 나머지 두 개: 변동성 높은 쪽 → volatile(3), 나머지 → sideways(2)
    mid = [sorted_regimes[1], sorted_regimes[2]]
    vol_0 = np.std(X[raw_labels == mid[0], 1]) if (raw_labels == mid[0]).sum() > 0 else 0
    vol_1 = np.std(X[raw_labels == mid[1], 1]) if (raw_labels == mid[1]).sum() > 0 else 0
    if vol_0 > vol_1:
        label_map[mid[0]] = 3  # volatile
        label_map[mid[1]] = 2  # sideways
    else:
        label_map[mid[0]] = 2
        label_map[mid[1]] = 3

    labels = np.array([label_map[r] for r in raw_labels])

    # 앞의 lookback개는 분류 불가
    full_labels = np.concatenate([np.full(lookback, -1, dtype=int), labels])

    # 전이 행렬
    regime_names = {0: "bull", 1: "bear", 2: "sideways", 3: "volatile"}
    transition = np.zeros((4, 4))
    for i in range(1, len(labels)):
        transition[labels[i-1], labels[i]] += 1
    # 정규화
    row_sums = transition.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    transition_norm = transition / row_sums

    # 통계
    stats = {}
    for r in range(4):
        mask = labels == r
        count = int(mask.sum())
        if count > 0:
            stats[regime_names[r]] = {
                "count": count,
                "pct": round(count / len(labels) * 100, 1),
                "avg_return": round(float(np.mean(X[mask, 0])) * 100, 3),
                "avg_volatility": round(float(np.mean(X[mask, 1])) * 100, 3),
            }

    return full_labels, {
        "stats": stats,
        "transition_matrix": transition_norm.tolist(),
        "regime_names": regime_names,
    }


def _phase1_regime_split():
    """Day 1: 180일 4h 캔들 → 레짐 분할"""
    candles = _load_4h_candles(180)
    labels, info = _classify_regimes(candles)

    # 레짐별 캔들 분할 저장
    regime_names = {0: "bull", 1: "bear", 2: "sideways", 3: "volatile"}
    regime_candles = {}
    for r in range(4):
        mask = labels == r
        indices = np.where(mask)[0]
        rc = [candles[i] for i in indices if i < len(candles)]
        regime_candles[regime_names[r]] = rc
        with open(REGIME_DIR / f"{regime_names[r]}_candles.pkl", "wb") as f:
            pickle.dump(rc, f)
        log.info(f"  {regime_names[r]}: {len(rc)}건 저장")

    # 전체 라벨 + 전이 행렬 저장
    with open(REGIME_DIR / "regime_labels.pkl", "wb") as f:
        pickle.dump({"labels": labels, "info": info}, f)

    with open(REGIME_DIR / "regime_report.json", "w") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    return {"regime_stats": info["stats"], "total_candles": len(candles)}


# ═══════════════════════════════════════════════════
# Phase 2-3: 레짐별 전문가 모델
# ═══════════════════════════════════════════════════

def _make_regime_env(regime_name: str):
    """레짐별 캔들로 BitcoinTradingEnvV2 생성"""
    from rl_hybrid.rl.environment_v2 import BitcoinTradingEnvV2

    candle_file = REGIME_DIR / f"{regime_name}_candles.pkl"
    if not candle_file.exists():
        raise FileNotFoundError(f"레짐 캔들 없음: {candle_file}")

    with open(candle_file, "rb") as f:
        candles = pickle.load(f)

    if len(candles) < 100:
        log.warning(f"  {regime_name} 캔들 부족 ({len(candles)}건), 전체 데이터 사용")
        candles = _load_4h_candles(180)

    env = BitcoinTradingEnvV2(candles=candles)
    return env


def _train_specialist(regime: str, algo: str, timesteps: int = 200_000) -> dict:
    """단일 레짐 전문가 모델 훈련"""
    from stable_baselines3 import PPO, SAC
    from stable_baselines3.common.callbacks import EvalCallback

    env = _make_regime_env(regime)
    eval_env = _make_regime_env(regime)

    model_name = f"{algo}_{regime}_{timesteps // 1000}k"
    save_path = SPECIALIST_DIR / model_name

    if algo == "ppo":
        model = PPO(
            "MlpPolicy", env,
            learning_rate=3e-4, n_steps=2048, batch_size=64,
            n_epochs=10, gamma=0.99, ent_coef=0.01,
            policy_kwargs={"net_arch": [256, 128]},
            verbose=0, seed=42,
        )
    elif algo == "sac":
        model = SAC(
            "MlpPolicy", env,
            learning_rate=3e-4, buffer_size=50000, batch_size=256,
            gamma=0.99, tau=0.005, ent_coef="auto",
            policy_kwargs={"net_arch": [256, 128]},
            verbose=0, seed=42,
        )
    else:
        raise ValueError(f"Unknown algo: {algo}")

    eval_cb = EvalCallback(
        eval_env, n_eval_episodes=50, eval_freq=20000,
        best_model_save_path=str(save_path) + "_best",
        deterministic=True, verbose=0,
    )

    log.info(f"  훈련 시작: {model_name}")
    start = time.time()
    model.learn(total_timesteps=timesteps, callback=eval_cb, progress_bar=True)
    elapsed = round(time.time() - start)
    model.save(str(save_path))

    # 평가
    metrics = _eval_4h_model(model, eval_env, 100, model_name)
    metrics["elapsed_sec"] = elapsed
    log.info(f"  {model_name}: return={metrics.get('total_return_pct', 0):.2f}%, "
             f"sharpe={metrics.get('sharpe', 0):.3f}, elapsed={elapsed}s")

    return metrics


def _eval_4h_model(model, env, episodes: int, tag: str) -> dict:
    """4h 환경 모델 평가"""
    returns = []
    trades_list = []
    mdds = []

    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        if "episode_stats" in info:
            stats = info["episode_stats"]
            returns.append(stats.get("total_return_pct", 0))
            trades_list.append(stats.get("total_trades", 0))
            mdds.append(stats.get("max_drawdown", 0))

    returns = np.array(returns) if returns else np.array([0])
    return {
        "tag": tag,
        "total_return_pct": round(float(returns.mean()), 3),
        "sharpe": round(float(returns.mean() / max(returns.std(), 1e-8)), 3),
        "mdd": round(float(np.mean(mdds)), 4) if mdds else 0,
        "avg_trades": round(float(np.mean(trades_list)), 1) if trades_list else 0,
        "episodes": episodes,
    }


def _phase2_specialists():
    """Day 2-3: 4 레짐 × PPO+SAC 200K = 8개 전문가"""
    regimes = ["bull", "bear", "sideways", "volatile"]
    algos = ["ppo", "sac"]
    results = []

    for regime in regimes:
        for algo in algos:
            try:
                metrics = _train_specialist(regime, algo, 200_000)
                results.append({"regime": regime, "algo": algo, **metrics})
                _log_to_db(f"w2_specialist_{algo}_{regime}", "completed", metrics=metrics)
            except Exception as e:
                log.error(f"  {algo}_{regime} 실패: {e}")
                _log_to_db(f"w2_specialist_{algo}_{regime}", "failed", error=str(e))
                results.append({"regime": regime, "algo": algo, "error": str(e)})

    # 결과 저장
    with open(SPECIALIST_DIR / "specialist_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    return {"specialist_count": len([r for r in results if "error" not in r]), "results": results}


# ═══════════════════════════════════════════════════
# Phase 3: 커리큘럼 학습
# ═══════════════════════════════════════════════════

def _phase3_curriculum():
    """Day 4-5: 3가지 커리큘럼 순서로 400K 학습"""
    from stable_baselines3 import PPO

    # 난이도 순서 정의 (변동성 기준)
    # Easy: sideways (낮은 변동성)
    # Medium: bull (일정 방향)
    # Hard: bear + volatile (반전 + 고변동)
    orderings = {
        "easy_to_hard": ["sideways", "bull", "volatile", "bear"],
        "hard_to_easy": ["bear", "volatile", "bull", "sideways"],
        "random": None,  # 매 에폭 랜덤 셔플
    }

    results = {}
    for order_name, regime_order in orderings.items():
        log.info(f"\n  커리큘럼: {order_name}")
        try:
            # 첫 레짐으로 환경 생성 후 시작
            if regime_order:
                env = _make_regime_env(regime_order[0])
            else:
                env = _make_regime_env("sideways")

            model = PPO(
                "MlpPolicy", env,
                learning_rate=3e-4, n_steps=2048, batch_size=64,
                n_epochs=10, gamma=0.99, ent_coef=0.01,
                policy_kwargs={"net_arch": [256, 128]},
                verbose=0, seed=42,
            )

            # 4단계 × 100K = 400K
            steps_per_stage = 100_000
            stage_metrics = []

            if regime_order is None:
                # 랜덤: 4단계, 매번 랜덤 레짐
                import random
                regimes = ["bull", "bear", "sideways", "volatile"]
                regime_order = [random.choice(regimes) for _ in range(4)]

            for stage_idx, regime in enumerate(regime_order):
                env = _make_regime_env(regime)
                model.set_env(env)
                log.info(f"    Stage {stage_idx+1}/4: {regime} ({steps_per_stage//1000}K)")
                model.learn(total_timesteps=steps_per_stage, progress_bar=False, reset_num_timesteps=False)

                # 중간 평가 (전체 데이터)
                eval_env = _make_regime_env("sideways")  # 기본 환경으로 평가
                stage_result = _eval_4h_model(model, eval_env, 50, f"{order_name}_stage{stage_idx+1}")
                stage_metrics.append({"stage": stage_idx+1, "regime": regime, **stage_result})

            # 최종 모델 저장
            save_path = CURRICULUM_DIR / f"ppo_{order_name}_400k"
            model.save(str(save_path))

            # 전체 레짐에서 최종 평가
            final_metrics = {}
            for regime in ["bull", "bear", "sideways", "volatile"]:
                try:
                    eval_env = _make_regime_env(regime)
                    m = _eval_4h_model(model, eval_env, 50, f"{order_name}_final_{regime}")
                    final_metrics[regime] = m
                except Exception:
                    pass

            results[order_name] = {
                "stages": stage_metrics,
                "final": final_metrics,
                "forgetting": _measure_forgetting(stage_metrics),
            }

            _log_to_db(f"w2_curriculum_{order_name}", "completed", metrics=results[order_name])

        except Exception as e:
            log.error(f"  커리큘럼 {order_name} 실패: {e}", exc_info=True)
            results[order_name] = {"error": str(e)}
            _log_to_db(f"w2_curriculum_{order_name}", "failed", error=str(e))

    with open(CURRICULUM_DIR / "curriculum_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    return results


def _measure_forgetting(stage_metrics: list) -> dict:
    """망각 분석: 각 스테이지 후 이전 레짐 성능 하락 측정"""
    if len(stage_metrics) < 2:
        return {"note": "insufficient stages"}
    first = stage_metrics[0].get("total_return_pct", 0)
    last = stage_metrics[-1].get("total_return_pct", 0)
    return {
        "first_stage_return": first,
        "last_stage_return": last,
        "forgetting_gap": round(first - last, 3),
    }


# ═══════════════════════════════════════════════════
# Phase 4: 최적 커리큘럼 장기 훈련
# ═══════════════════════════════════════════════════

def _phase4_best_curriculum():
    """Day 6: 최적 순서로 1M 사이클릭 리플레이"""
    from stable_baselines3 import PPO

    # 커리큘럼 결과에서 최적 순서 선택
    results_file = CURRICULUM_DIR / "curriculum_results.json"
    if results_file.exists():
        with open(results_file) as f:
            results = json.load(f)
        # Sharpe 기준 최적 선택
        best_order = None
        best_sharpe = -999
        for order_name, data in results.items():
            if "error" in data:
                continue
            stages = data.get("stages", [])
            if stages:
                sharpe = stages[-1].get("sharpe", -999)
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_order = order_name
        if best_order is None:
            best_order = "easy_to_hard"
    else:
        best_order = "easy_to_hard"

    log.info(f"  최적 커리큘럼: {best_order} (Sharpe: {best_sharpe:.3f})")

    orderings = {
        "easy_to_hard": ["sideways", "bull", "volatile", "bear"],
        "hard_to_easy": ["bear", "volatile", "bull", "sideways"],
        "random": ["sideways", "bull", "volatile", "bear"],
    }
    regime_order = orderings.get(best_order, orderings["easy_to_hard"])

    # 사이클릭 리플레이: 1M = 10사이클 × 4레짐 × 25K
    env = _make_regime_env(regime_order[0])
    model = PPO(
        "MlpPolicy", env,
        learning_rate=1e-4,  # 장기 학습이므로 작은 lr
        n_steps=2048, batch_size=128,
        n_epochs=10, gamma=0.99, ent_coef=0.005,
        policy_kwargs={"net_arch": [256, 128]},
        verbose=0, seed=42,
    )

    steps_per_regime = 25_000
    total_cycles = 10
    cycle_metrics = []

    for cycle in range(total_cycles):
        for regime in regime_order:
            env = _make_regime_env(regime)
            model.set_env(env)
            model.learn(total_timesteps=steps_per_regime, progress_bar=False, reset_num_timesteps=False)

        # 사이클 종료 시 평가
        eval_env = _make_regime_env("sideways")
        m = _eval_4h_model(model, eval_env, 50, f"cycle_{cycle+1}")
        cycle_metrics.append({"cycle": cycle+1, **m})
        log.info(f"  사이클 {cycle+1}/10: return={m['total_return_pct']:.2f}%, sharpe={m['sharpe']:.3f}")

        # 체크포인트
        if (cycle + 1) % 3 == 0:
            model.save(str(CURRICULUM_DIR / f"ppo_best_cycle{cycle+1}"))

    model.save(str(CURRICULUM_DIR / "ppo_best_1M"))

    with open(CURRICULUM_DIR / "cyclic_replay_results.json", "w") as f:
        json.dump(cycle_metrics, f, indent=2, default=str)

    return {
        "best_curriculum": best_order,
        "cycles": total_cycles,
        "final": cycle_metrics[-1] if cycle_metrics else {},
    }


# ═══════════════════════════════════════════════════
# Phase 5: 통합 — 메타 선택기
# ═══════════════════════════════════════════════════

def _phase5_integration():
    """Day 7: 레짐→모델 라우팅 메타 선택기 + 비교 리포트"""
    from rl_hybrid.rl.environment_v2 import classify_regime

    # 전문가 모델 로드
    specialist_results_file = SPECIALIST_DIR / "specialist_results.json"
    if specialist_results_file.exists():
        with open(specialist_results_file) as f:
            specialist_results = json.load(f)
    else:
        specialist_results = []

    # 레짐별 최적 알고리즘 선택
    best_per_regime = {}
    for r in specialist_results:
        if "error" in r:
            continue
        regime = r["regime"]
        sharpe = r.get("sharpe", -999)
        if regime not in best_per_regime or sharpe > best_per_regime[regime].get("sharpe", -999):
            best_per_regime[regime] = r

    # 커리큘럼 모델 결과
    curriculum_file = CURRICULUM_DIR / "curriculum_results.json"
    curriculum_results = {}
    if curriculum_file.exists():
        with open(curriculum_file) as f:
            curriculum_results = json.load(f)

    cyclic_file = CURRICULUM_DIR / "cyclic_replay_results.json"
    cyclic_results = []
    if cyclic_file.exists():
        with open(cyclic_file) as f:
            cyclic_results = json.load(f)

    # 비교 리포트
    report = {
        "timestamp": datetime.now(KST).isoformat(),
        "best_specialist_per_regime": best_per_regime,
        "curriculum_comparison": {
            k: v.get("stages", [{}])[-1] if isinstance(v, dict) and "stages" in v else {}
            for k, v in curriculum_results.items()
        },
        "cyclic_replay_final": cyclic_results[-1] if cyclic_results else {},
        "meta_selector": {
            "strategy": "regime_to_best_specialist",
            "routing": {regime: data.get("tag", "unknown") for regime, data in best_per_regime.items()},
        },
    }

    with open(W2_MODEL_DIR / "mac_mini_w2_report.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    _telegram(
        f"[Mac Mini W2] 통합 리포트 완료\n"
        f"전문가: {len(best_per_regime)}개 레짐\n"
        f"커리큘럼: {len(curriculum_results)}가지\n"
        f"사이클릭: {len(cyclic_results)}사이클"
    )

    return report


# ═══════════════════════════════════════════════════
# 진입점
# ═══════════════════════════════════════════════════

def run_mac_mini_w2():
    """Mac Mini Week 2 전체 실행"""
    from scalp_ml.distributed_training import _run_phases

    machine = "mac-mini"
    log.info(f"{'='*60}")
    log.info(f"  Mac Mini Week 2 — 레짐 전문가 팩토리")
    log.info(f"{'='*60}")
    _telegram(
        f"[Mac Mini] Week 2 시작\n"
        f"Day 1: 레짐 분할\n"
        f"Day 2-3: 8개 전문가 모델\n"
        f"Day 4-5: 커리큘럼 학습\n"
        f"Day 6: 1M 사이클릭 리플레이\n"
        f"Day 7: 통합 + 리포트"
    )

    phases = [
        ("w2_regime_split", _phase1_regime_split, "레짐 분할 (4h 180일)"),
        ("w2_specialists", _phase2_specialists, "레짐별 전문가 모델 8개"),
        ("w2_curriculum", _phase3_curriculum, "커리큘럼 학습 3가지 순서"),
        ("w2_best_curriculum", _phase4_best_curriculum, "최적 커리큘럼 1M"),
        ("w2_integration", _phase5_integration, "통합 + 메타 선택기"),
    ]

    _run_phases(machine, phases)
