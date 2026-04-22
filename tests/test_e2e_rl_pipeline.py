"""RL 훈련 파이프라인 End-to-End 테스트

전체 RL 파이프라인을 7개 시나리오로 검증:
  1. Full pipeline: 합성 캔들 → 지표 → 환경 → PPO 훈련 → 평가 → 통계
  2. Edge case pipeline: 시나리오 생성 → 지표 → 환경 → 훈련 → 평가
  3. Model save/load round-trip: 훈련 → 저장 → 로드 → 동일 shape 추론
  4. Multi-algorithm: PPO 훈련 후 모델 파일 존재 확인
  5. Environment reset/step loop: 100 랜덤 스텝 크래시 없음
  6. ScenarioGenerator → mix_with_real → 지표 → 환경 동작 E2E
  7. StateEncoder: 모든 시나리오 타입에서 유효한 관측 벡터 생성
"""

import os
import sys
import tempfile
import warnings

import numpy as np
import pytest

warnings.filterwarnings("ignore")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from rl_hybrid.rl.data_loader import HistoricalDataLoader
from rl_hybrid.rl.environment import BitcoinTradingEnv
from rl_hybrid.rl.scenario_generator import ScenarioGenerator
from rl_hybrid.rl.state_encoder import StateEncoder, OBSERVATION_DIM

# SB3 availability check
try:
    from rl_hybrid.rl.policy import PPOTrader, SB3_AVAILABLE
except ImportError:
    SB3_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not SB3_AVAILABLE,
    reason="stable-baselines3 not installed",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_synthetic_candles(n: int = 80, base_price: float = 100_000_000) -> list[dict]:
    """Generate minimal synthetic OHLCV candles for testing."""
    rng = np.random.RandomState(123)
    candles = []
    price = base_price
    for i in range(n):
        change = rng.uniform(-0.015, 0.015)
        open_p = price
        close_p = price * (1 + change)
        high_p = max(open_p, close_p) * (1 + rng.uniform(0, 0.005))
        low_p = min(open_p, close_p) * (1 - rng.uniform(0, 0.005))
        volume = rng.uniform(100, 1000)
        candles.append({
            "timestamp": f"2025-01-{(i // 24) + 1:02d}T{i % 24:02d}:00:00",
            "open": round(open_p),
            "high": round(high_p),
            "low": round(low_p),
            "close": round(close_p),
            "volume": round(volume, 4),
        })
        price = close_p
    return candles


def prepare_env_pair(candles: list[dict], balance: float = 10_000_000):
    """Split candles 80/20 and create train/eval environments."""
    loader = HistoricalDataLoader()
    enriched = loader.compute_indicators(candles)
    split = int(len(enriched) * 0.8)
    train_candles = enriched[:split]
    eval_candles = enriched[split:]
    # Ensure minimum candle count for environment lookback
    if len(eval_candles) < 30:
        eval_candles = enriched[-30:]
    train_env = BitcoinTradingEnv(candles=train_candles, initial_balance=balance)
    eval_env = BitcoinTradingEnv(candles=eval_candles, initial_balance=balance)
    return train_env, eval_env


# ---------------------------------------------------------------------------
# Test 1: Full pipeline — synthetic candles → indicators → env → PPO → eval
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_full_pipeline_synthetic_to_eval():
    """Create synthetic candles, compute indicators, train PPO (500 steps),
    evaluate, and verify episode stats contain expected keys."""
    candles = make_synthetic_candles(100)
    train_env, eval_env = prepare_env_pair(candles)

    trader = PPOTrader(env=train_env)
    trader.train(total_timesteps=500, eval_env=eval_env, save_freq=250)

    # Evaluate 3 episodes
    all_stats = []
    for _ in range(3):
        obs, info = eval_env.reset()
        done = False
        while not done:
            action = trader.predict(obs)
            obs, reward, terminated, truncated, info = eval_env.step(np.array([action]))
            done = terminated or truncated
        stats = eval_env.get_episode_stats()
        all_stats.append(stats)

    assert len(all_stats) == 3
    for stats in all_stats:
        assert "total_return_pct" in stats
        assert "sharpe_ratio" in stats
        assert "max_drawdown" in stats
        assert "trade_count" in stats
        assert isinstance(stats["total_return_pct"], float)
        assert isinstance(stats["max_drawdown"], float)


# ---------------------------------------------------------------------------
# Test 2: Edge case pipeline — scenario generator → indicators → train → eval
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_edge_case_pipeline():
    """Generate edge-case scenarios, compute indicators, train, and evaluate."""
    gen = ScenarioGenerator(base_price=100_000_000, seed=99)
    scenario_candles = gen.generate_all(variations=1)

    # Take a subset (first 100 candles) for speed
    subset = scenario_candles[:100]
    assert len(subset) >= 50, f"Expected >= 50 candles, got {len(subset)}"

    train_env, eval_env = prepare_env_pair(subset)

    trader = PPOTrader(env=train_env)
    trader.train(total_timesteps=300, save_freq=150)

    # Single evaluation episode
    obs, _ = eval_env.reset()
    done = False
    step_count = 0
    while not done:
        action = trader.predict(obs)
        obs, reward, terminated, truncated, _ = eval_env.step(np.array([action]))
        done = terminated or truncated
        step_count += 1

    stats = eval_env.get_episode_stats()
    assert step_count > 0
    assert "total_return_pct" in stats


# ---------------------------------------------------------------------------
# Test 3: Model save/load round-trip
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_model_save_load_roundtrip():
    """Train, save, load, and verify predict output shape matches."""
    candles = make_synthetic_candles(80)
    train_env, eval_env = prepare_env_pair(candles)

    trader = PPOTrader(env=train_env)
    trader.train(total_timesteps=200, save_freq=200)

    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, "test_model")
        trader.save(model_path)

        # Verify file exists
        assert os.path.exists(model_path + ".zip"), "Model .zip file not found"

        # Load into a new trader
        loaded_trader = PPOTrader(env=eval_env)
        loaded_trader.load(model_path)

        # Get an observation and predict with both
        obs, _ = eval_env.reset()
        action_original = trader.predict(obs)
        action_loaded = loaded_trader.predict(obs)

        # Both should return float scalars in [-1, 1]
        assert isinstance(action_original, float)
        assert isinstance(action_loaded, float)
        assert -1.0 <= action_original <= 1.0
        assert -1.0 <= action_loaded <= 1.0


# ---------------------------------------------------------------------------
# Test 4: Multi-algorithm — train PPO and verify model files exist
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_multi_algorithm_ppo_files_exist():
    """Train PPO and verify model files are created."""
    candles = make_synthetic_candles(80)
    train_env, _ = prepare_env_pair(candles)

    with tempfile.TemporaryDirectory() as tmpdir:
        trader = PPOTrader(env=train_env)
        trader.train(total_timesteps=200, save_freq=200)

        model_path = os.path.join(tmpdir, "ppo_test")
        trader.save(model_path)

        assert os.path.exists(model_path + ".zip"), "PPO model file not found"

        # Verify the saved model can be loaded
        reload_env, _ = prepare_env_pair(candles)
        loaded = PPOTrader(env=reload_env)
        loaded.load(model_path)
        assert loaded.model is not None


# ---------------------------------------------------------------------------
# Test 5: Environment reset/step loop — 100 random steps without crash
# ---------------------------------------------------------------------------

def test_environment_100_random_steps():
    """Run 100 random actions in the environment without any crash."""
    candles = make_synthetic_candles(80)
    loader = HistoricalDataLoader()
    enriched = loader.compute_indicators(candles)
    env = BitcoinTradingEnv(candles=enriched, initial_balance=10_000_000)

    rng = np.random.RandomState(42)
    obs, info = env.reset()

    assert obs.shape == (OBSERVATION_DIM,), f"Expected shape ({OBSERVATION_DIM},), got {obs.shape}"
    assert np.all(np.isfinite(obs)), "Observation contains non-finite values"

    for step in range(100):
        action = rng.uniform(-1, 1, size=(1,)).astype(np.float32)
        obs, reward, terminated, truncated, info = env.step(action)

        assert obs.shape == (OBSERVATION_DIM,), f"Step {step}: wrong obs shape"
        assert np.all(np.isfinite(obs)), f"Step {step}: non-finite obs"
        assert isinstance(reward, float), f"Step {step}: reward not float"
        assert np.isfinite(reward), f"Step {step}: non-finite reward"

        if terminated or truncated:
            obs, info = env.reset()

    # Verify episode stats are accessible
    stats = env.get_episode_stats()
    assert isinstance(stats, dict)
    assert "final_value" in stats


# ---------------------------------------------------------------------------
# Test 6: ScenarioGenerator → mix_with_real → indicators → environment E2E
# ---------------------------------------------------------------------------

def test_scenario_mix_with_real_to_env():
    """Generate scenarios, mix with real (synthetic) candles, compute
    indicators, and verify the environment can run a full episode."""
    real_candles = make_synthetic_candles(60)
    gen = ScenarioGenerator(base_price=real_candles[-1]["close"], seed=7)

    mixed = gen.mix_with_real(real_candles, synthetic_ratio=0.3, variations=1)
    assert len(mixed) > len(real_candles), (
        f"Mixed should be longer than real: {len(mixed)} vs {len(real_candles)}"
    )

    loader = HistoricalDataLoader()
    enriched = loader.compute_indicators(mixed)

    env = BitcoinTradingEnv(candles=enriched, initial_balance=10_000_000)
    obs, _ = env.reset()

    done = False
    steps = 0
    while not done and steps < 200:
        action = np.array([0.0], dtype=np.float32)  # Hold
        obs, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        steps += 1

    assert steps > 0
    stats = env.get_episode_stats()
    assert "total_return_pct" in stats


# ---------------------------------------------------------------------------
# Test 7: StateEncoder produces valid observations for all scenario types
# ---------------------------------------------------------------------------

def test_state_encoder_all_scenario_types():
    """Verify StateEncoder produces valid (finite, [0,1] range) observations
    for candles from every scenario type."""
    gen = ScenarioGenerator(base_price=100_000_000, seed=42)
    loader = HistoricalDataLoader()
    encoder = StateEncoder()

    scenario_funcs = [
        gen.flash_crash,
        gen.dead_cat_bounce,
        gen.parabolic_pump,
        gen.whale_manipulation,
        gen.sideways_trap,
        gen.cascade_liquidation,
        gen.v_shape_recovery,
        gen.slow_bleed,
        gen.fomo_top,
        gen.black_swan,
    ]

    for func in scenario_funcs:
        name = func.__name__
        raw_candles = func()
        assert len(raw_candles) > 0, f"{name}: generated 0 candles"

        enriched = loader.compute_indicators(raw_candles)

        # Test the environment observation for the middle candle
        env = BitcoinTradingEnv(candles=enriched, initial_balance=10_000_000)
        obs, _ = env.reset()

        assert obs.shape == (OBSERVATION_DIM,), f"{name}: wrong obs shape {obs.shape}"
        assert np.all(np.isfinite(obs)), f"{name}: non-finite values in observation"
        assert np.all(obs >= 0.0), f"{name}: obs has values < 0"
        assert np.all(obs <= 1.0), f"{name}: obs has values > 1"

        # Take one step to verify step also works
        action = np.array([0.0], dtype=np.float32)
        obs2, reward, _, _, _ = env.step(action)
        assert obs2.shape == (OBSERVATION_DIM,), f"{name}: wrong obs shape after step"
        assert np.all(np.isfinite(obs2)), f"{name}: non-finite after step"


# ═══════════════════════════════════════════════════════════════════════════
#  E4팀 추가: RL 훈련 → ModelRegistry → Ensemble Inference E2E
#
#  - Test 8:  Smoke training (mocked learn to 1 step) — 빠른 smoke
#  - Test 9:  ModelRegistry roundtrip (register → load → predict)
#  - Test 10: Ensemble inference (3 sources → DecisionBlender → 가중치 합 = 1)
#  - Test 11: Auto rollback on performance drop (should_rollback + rollback)
#  - Test 12: Register → predict via path returned from registry (E2E chain)
# ═══════════════════════════════════════════════════════════════════════════

from unittest import mock

from rl_hybrid.rl.decision_blender import BlendedDecision, DecisionBlender
from rl_hybrid.rl.model_registry import ModelRegistry


def _dummy_metrics(sharpe: float = 1.0, ret: float = 5.0, mdd: float = 0.05) -> dict:
    return {
        "sharpe_ratio": sharpe,
        "total_return_pct": ret,
        "max_drawdown": mdd,
        "eval_episodes": 10,
    }


# ---------------------------------------------------------------------------
# Test 8: Smoke training — PPO.learn을 mock하여 1스텝만 실행
# ---------------------------------------------------------------------------

def test_smoke_training_mocked_learn():
    """PPO.learn을 patch하여 실제 스텝 없이 훈련 흐름만 검증."""
    candles = make_synthetic_candles(60)
    train_env, _ = prepare_env_pair(candles)

    trader = PPOTrader(env=train_env)

    # learn을 no-op로 대체 — 훈련 파이프라인 자체만 smoke
    with mock.patch.object(trader.model, "learn", return_value=trader.model) as mk:
        trader.train(total_timesteps=1, save_freq=1)
        assert mk.called, "PPO.learn이 호출되어야 한다"
        call_kwargs = mk.call_args.kwargs
        assert call_kwargs.get("total_timesteps") == 1

    # predict 여전히 작동해야 함 (초기화된 모델)
    obs, _ = train_env.reset()
    action = trader.predict(obs)
    assert isinstance(action, float)
    assert -1.0 <= action <= 1.0


# ---------------------------------------------------------------------------
# Test 9: ModelRegistry roundtrip — 등록 → 로드 → predict
# ---------------------------------------------------------------------------

def test_model_registry_roundtrip(tmp_path):
    """더미 모델 파일을 레지스트리에 등록 → 경로 조회 → 메타데이터 확인."""
    registry = ModelRegistry(base_dir=str(tmp_path / "reg"))

    # 더미 모델 파일 생성
    dummy = tmp_path / "dummy.zip"
    dummy.write_bytes(b"FAKE_MODEL_BYTES_" + b"x" * 64)

    vid = registry.register_model(
        model_path=str(dummy),
        metrics=_dummy_metrics(sharpe=1.23, ret=7.5, mdd=0.04),
        training_config={"algorithm": "ppo", "total_timesteps": 1000, "data_days": 30},
        notes="E4 smoke",
    )
    assert vid == "v001"

    current = registry.get_current_version()
    assert current is not None
    assert current["version_id"] == "v001"
    assert current["metrics"]["sharpe_ratio"] == 1.23

    # 경로 조회 — 파일이 복사되어 있어야 한다
    path = registry.get_model_path()
    assert path is not None
    assert os.path.exists(path), f"등록된 모델 파일 없음: {path}"

    versions = registry.list_versions()
    assert len(versions) == 1
    assert versions[0]["is_current"] is True


def test_model_registry_ppo_end_to_end(tmp_path):
    """실제 PPO 저장 → ModelRegistry 등록 → 로드 → predict 체인."""
    candles = make_synthetic_candles(60)
    train_env, _ = prepare_env_pair(candles)

    trader = PPOTrader(env=train_env)

    # learn을 mock하여 빠르게 통과
    with mock.patch.object(trader.model, "learn", return_value=trader.model):
        trader.train(total_timesteps=1, save_freq=1)

    # 모델을 임시 경로에 저장
    saved_path = str(tmp_path / "ppo_tiny")
    trader.save(saved_path)
    saved_zip = saved_path + ".zip"
    assert os.path.exists(saved_zip), "PPO 저장 파일이 생성되어야 한다"

    # 레지스트리에 등록
    registry = ModelRegistry(base_dir=str(tmp_path / "reg"))
    vid = registry.register_model(
        model_path=saved_zip,
        metrics=_dummy_metrics(sharpe=0.5, ret=2.0, mdd=0.03),
        training_config={"algorithm": "ppo", "total_timesteps": 1},
    )
    assert vid == "v001"

    # 레지스트리에서 조회한 경로로 재로드
    registered_path = registry.get_model_path()
    # PPOTrader.load는 확장자 없는 경로를 기대
    load_target = registered_path[:-4] if registered_path.endswith(".zip") else registered_path

    reload_env, _ = prepare_env_pair(candles)
    reloaded = PPOTrader(env=reload_env)
    reloaded.load(load_target)
    assert reloaded.model is not None

    obs, _ = reload_env.reset()
    action = reloaded.predict(obs)
    assert isinstance(action, float)
    assert -1.0 <= action <= 1.0


# ---------------------------------------------------------------------------
# Test 10: Ensemble inference — DecisionBlender가 Agent/RL/LLM 융합
# ---------------------------------------------------------------------------

def test_ensemble_inference_weights_sum_to_one():
    """세 소스가 모두 가용할 때 동적 가중치 합 = 1."""
    blender = DecisionBlender()

    agent_result = {"decision": "buy", "confidence": 0.7,
                    "buy_score": {"total": 75, "threshold": 70}}
    rl_prediction = {"action": 0.6, "value": 0.3}
    llm_analysis = {"recommended_action": "buy", "confidence": 0.8}

    result = blender.blend(
        agent_result=agent_result,
        rl_prediction=rl_prediction,
        llm_analysis=llm_analysis,
    )

    assert isinstance(result, BlendedDecision)
    w = result.weights_used
    assert set(w.keys()) == {"agent", "rl", "llm"}
    total_w = w["agent"] + w["rl"] + w["llm"]
    assert abs(total_w - 1.0) < 1e-6, f"가중치 합이 1이 아님: {total_w}"

    # 기본 비율이 대략 40/35/25와 유사해야 한다 (성과 히스토리 없음)
    assert w["agent"] == pytest.approx(0.40, abs=0.05)
    assert w["rl"] == pytest.approx(0.35, abs=0.05)
    assert w["llm"] == pytest.approx(0.25, abs=0.05)

    # 세 소스가 모두 매수 방향 → blended도 매수
    assert result.decision == "buy"
    assert result.confidence > 0
    assert result.action_value > 0


def test_ensemble_inference_with_registry_model():
    """레지스트리에 저장된 모델의 predict 출력을 DecisionBlender에 주입."""
    # 등록된 여러 모델을 시뮬레이션 (더미 predict 결과)
    fake_predictions = [
        {"action": 0.5, "value": 0.2},
        {"action": 0.8, "value": 0.4},
        {"action": 0.3, "value": 0.1},
    ]

    # 앙상블 평균
    ensemble_action = np.mean([p["action"] for p in fake_predictions])
    rl_prediction = {"action": float(ensemble_action), "value": 0.25}

    blender = DecisionBlender()
    result = blender.blend(
        agent_result={"decision": "buy", "confidence": 0.6},
        rl_prediction=rl_prediction,
        llm_analysis={"recommended_action": "cautious_buy", "confidence": 0.5},
    )

    assert result is not None
    # 가중 평균 확인
    w = result.weights_used
    assert abs(sum(w.values()) - 1.0) < 1e-6
    # rl_action은 주입된 평균 그대로여야 함
    assert result.rl_action == pytest.approx(ensemble_action, abs=1e-6)


def test_ensemble_inference_source_missing_redistributes_weight():
    """소스 일부가 None이면 가용 소스에 가중치 재분배되고 합은 여전히 1."""
    blender = DecisionBlender()

    result = blender.blend(
        agent_result={"decision": "buy", "confidence": 0.7},
        rl_prediction=None,             # RL 없음
        llm_analysis={"recommended_action": "buy", "confidence": 0.6},
    )
    w = result.weights_used
    assert abs(sum(w.values()) - 1.0) < 1e-6
    # RL 가중치는 재분배되어 0일 수도, 기본 0.35가 분산되었을 수도 있음.
    # 핵심은: 합 = 1 그리고 사용 가능한 두 소스가 0보다 커야 함
    assert w["agent"] > 0
    assert w["llm"] > 0


# ---------------------------------------------------------------------------
# Test 11: Auto-rollback on performance drop
# ---------------------------------------------------------------------------

def test_auto_rollback_triggers_on_low_winrate(tmp_path):
    """라이브 승률 < 30%, 10+ 거래 → should_rollback=True."""
    registry = ModelRegistry(base_dir=str(tmp_path / "reg"))

    # v1: 양호한 성능 (롤백 후보)
    m1 = tmp_path / "m1.zip"
    m1.write_bytes(b"model1")
    registry.register_model(
        model_path=str(m1),
        metrics=_dummy_metrics(sharpe=1.8, ret=12.0),
    )

    # v2: 나쁜 라이브 성능
    m2 = tmp_path / "m2.zip"
    m2.write_bytes(b"model2")
    registry.register_model(
        model_path=str(m2),
        metrics=_dummy_metrics(sharpe=0.9, ret=4.0),
    )

    # 라이브 성능 기록 — 승률 저조
    registry.update_live_performance(
        "v002",
        {"trades": 15, "win_rate": 0.2, "avg_return": -1.5, "consecutive_losses": 2},
    )

    should, reason = registry.should_rollback("v002")
    assert should is True, f"롤백 트리거되어야 함: {reason}"
    assert "승률" in reason or "win_rate" in reason.lower()

    # 실제 롤백 실행 — 샤프 최고인 v1으로 돌아가야 한다
    rolled_to = registry.rollback()
    assert rolled_to == "v001"
    assert registry.registry["current_version"] == "v001"
    assert registry.registry["rollback_count"] == 1


def test_auto_rollback_insufficient_data(tmp_path):
    """10거래 미만 → 롤백 트리거 안 됨."""
    registry = ModelRegistry(base_dir=str(tmp_path / "reg"))
    m = tmp_path / "m.zip"
    m.write_bytes(b"x")
    registry.register_model(str(m), _dummy_metrics())

    registry.update_live_performance("v001", {"trades": 3, "win_rate": 0.1})
    should, reason = registry.should_rollback("v001")
    assert should is False
    assert "데이터 부족" in reason or "3" in reason


def test_auto_rollback_consecutive_losses(tmp_path):
    """연속 손실 5회 이상 → 롤백 트리거."""
    registry = ModelRegistry(base_dir=str(tmp_path / "reg"))
    m1 = tmp_path / "m1.zip"
    m1.write_bytes(b"a")
    m2 = tmp_path / "m2.zip"
    m2.write_bytes(b"b")
    registry.register_model(str(m1), _dummy_metrics(sharpe=2.0))
    registry.register_model(str(m2), _dummy_metrics(sharpe=1.0))

    registry.update_live_performance(
        "v002",
        {"trades": 12, "win_rate": 0.6, "avg_return": 0.5, "consecutive_losses": 6},
    )
    should, reason = registry.should_rollback("v002")
    assert should is True
    assert "연속" in reason or "consecutive" in reason.lower()


def test_rollback_impossible_single_version(tmp_path):
    """버전이 1개뿐이면 롤백 불가."""
    registry = ModelRegistry(base_dir=str(tmp_path / "reg"))
    m = tmp_path / "m.zip"
    m.write_bytes(b"x")
    registry.register_model(str(m), _dummy_metrics())

    result = registry.rollback()
    assert result is None
    assert registry.registry["rollback_count"] == 0
