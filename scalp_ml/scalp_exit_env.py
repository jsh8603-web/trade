#!/usr/bin/env python3
"""
스캘핑 청산 최적화 RL 환경 (ScalpExitEnv)

진입은 규칙 기반(고래/급등/뉴스)이 결정.
RL은 "언제 청산할 것인가"만 학습한다.

Observation: [pnl_pct, hold_min, mom_1m, mom_5m, vol_ratio, rsi, bb_pos, strategy]
Action: 0=HOLD, 1=TAKE_PROFIT, 2=STOP_LOSS
Reward: 실현 PnL 기반 + 시간 비용
"""

from __future__ import annotations

import logging
import math
import pickle
import random
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:
    import gym
    from gym import spaces

log = logging.getLogger("scalp_exit_env")

PROJECT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_DIR / "data" / "scalp_models"

# 스캘핑 파라미터 (v6: 실전과 동일하게 맞춤)
FEE_PCT = 0.1       # 왕복 수수료
MAX_HOLD = 15        # 최대 보유 분 (실전: SHORT_TERM_MAX_HOLD_MIN=15)
TP_DEFAULT = 0.3     # 기본 익절 (실전: SHORT_TERM_TAKE_PROFIT=0.30)
SL_DEFAULT = 0.25    # 기본 손절 (실전: SHORT_TERM_STOP_LOSS=0.25)


@dataclass
class ScalpEpisode:
    """하나의 스캘핑 포지션 에피소드"""
    entry_price: float
    candles: list[dict]  # 진입 이후 1분봉 시퀀스 (최대 MAX_HOLD개)
    strategy: int        # 0=news, 1=spike, 2=whale


class ScalpExitEnv(gym.Env):
    """
    스캘핑 청산 최적화 환경.

    에피소드 = 하나의 포지션 (진입 완료 상태에서 시작)
    각 스텝 = 1분 경과
    RL이 매 분마다 HOLD/TP/SL 결정
    """

    metadata = {"render_modes": []}

    def __init__(self, candle_data: list[dict] = None, candle_path: str = None):
        super().__init__()

        # 캔들 데이터 로드
        if candle_data:
            self.all_candles = candle_data
        elif candle_path:
            with open(candle_path, "rb") as f:
                self.all_candles = pickle.load(f)
        else:
            # candles_cache.pkl → candles_30d.pkl → candles_14d.pkl 순서로 폴백
            candidates = [
                MODEL_DIR / "candles_cache.pkl",
                MODEL_DIR / "candles_30d.pkl",
                MODEL_DIR / "candles_14d.pkl",
            ]
            loaded = False
            for cache in candidates:
                if cache.exists():
                    with open(cache, "rb") as f:
                        self.all_candles = pickle.load(f)
                    log.info(f"캔들 데이터 로드: {cache.name} ({len(self.all_candles)}개)")
                    loaded = True
                    break
            if not loaded:
                raise FileNotFoundError("캔들 데이터가 필요합니다. train_lgbm.py를 먼저 실행하세요.")

        # 행동 공간: 0=HOLD, 1=TAKE_PROFIT, 2=STOP_LOSS
        self.action_space = spaces.Discrete(3)

        # 관측 공간: 8개 피처
        self.observation_space = spaces.Box(
            low=np.array([-10, 0, -5, -5, 0, 0, 0, 0], dtype=np.float32),
            high=np.array([10, MAX_HOLD, 5, 5, 10, 100, 1, 2], dtype=np.float32),
        )

        # 에피소드 상태
        self._entry_price = 0
        self._current_step = 0
        self._episode_candles = []
        self._strategy = 0
        self._done = False
        self._total_reward = 0

        # 통계
        self.episode_count = 0
        self.wins = 0
        self.losses = 0

    def _compute_obs(self) -> np.ndarray:
        """현재 상태 → 관측 벡터"""
        idx = self._current_step
        if idx >= len(self._episode_candles):
            idx = len(self._episode_candles) - 1

        current_price = self._episode_candles[idx]["trade_price"]
        pnl_pct = (current_price / self._entry_price - 1) * 100

        # 모멘텀 (1분, 5분)
        prices = [c["trade_price"] for c in self._episode_candles[:idx + 1]]
        mom_1m = (prices[-1] / prices[-2] - 1) * 100 if len(prices) >= 2 else 0
        mom_5m = (prices[-1] / prices[-6] - 1) * 100 if len(prices) >= 6 else 0

        # 거래량 비율
        vols = [c["candle_acc_trade_volume"] for c in self._episode_candles[:idx + 1]]
        if len(vols) >= 5 and sum(vols[-5:]) > 0:
            vol_recent = sum(vols[-2:])
            vol_prev = sum(vols[-5:-2]) / 3 if sum(vols[-5:-2]) > 0 else 1
            vol_ratio = min(vol_recent / max(vol_prev, 0.001), 10)
        else:
            vol_ratio = 1.0

        # RSI (간이 계산)
        if len(prices) >= 15:
            diffs = [prices[i] - prices[i-1] for i in range(-14, 0)]
            gains = [d for d in diffs if d > 0]
            losses_v = [-d for d in diffs if d < 0]
            avg_g = sum(gains) / 14 if gains else 0
            avg_l = sum(losses_v) / 14 if losses_v else 0.001
            rsi = 100 - (100 / (1 + avg_g / avg_l))
        else:
            rsi = 50.0

        # BB 위치
        if len(prices) >= 20:
            sma = np.mean(prices[-20:])
            std = np.std(prices[-20:])
            bb_pos = (current_price - (sma - 2*std)) / (4*std) if std > 0 else 0.5
            bb_pos = np.clip(bb_pos, 0, 1)
        else:
            bb_pos = 0.5

        return np.array([
            np.clip(pnl_pct, -10, 10),      # 미실현 PnL (%)
            float(self._current_step),        # 보유 시간 (분)
            np.clip(mom_1m, -5, 5),           # 1분 모멘텀
            np.clip(mom_5m, -5, 5),           # 5분 모멘텀
            vol_ratio,                         # 거래량 비율
            rsi,                               # RSI
            bb_pos,                            # BB 위치
            float(self._strategy),             # 전략 타입
        ], dtype=np.float32)

    def _find_signal_entry(self) -> int:
        """실제 시그널과 유사한 진입 시점 찾기 (v7: 강화된 필터)

        실전 조건에 맞춤:
        - 급등/급락: 5분간 0.5%+ 변동 + 거래량 2배+
        - 방향성 확인: 3분 연속 같은 방향 캔들
        - 최소 후행 수익: 진입 후 5분 내 0.15%+ 도달한 구간 우선
        """
        max_start = len(self.all_candles) - MAX_HOLD - 5
        candidates = []

        for _ in range(300):
            idx = random.randint(30, max(31, max_start))
            prices = [c["trade_price"] for c in self.all_candles[idx-5:idx+1]]
            if len(prices) < 6:
                continue

            change = (prices[-1] / prices[0] - 1) * 100  # 방향 유지
            abs_change = abs(change)

            # 거래량 급증
            vols = [c["candle_acc_trade_volume"] for c in self.all_candles[idx-10:idx+1]]
            vol_avg = np.mean(vols[:5]) if len(vols) >= 10 else 1
            vol_recent = np.mean(vols[-3:]) if len(vols) >= 3 else 1
            vol_spike = vol_recent / max(vol_avg, 0.001)

            # v7: 강화된 시그널 조건
            if abs_change < 0.5 or vol_spike < 1.5:
                continue

            # 방향성 확인: 최근 3분 캔들 방향 일치
            direction = 1 if change > 0 else -1
            recent_3 = prices[-3:]
            dir_count = sum(1 for i in range(1, len(recent_3))
                          if (recent_3[i] - recent_3[i-1]) * direction > 0)
            if dir_count < 1:
                continue

            # 진입 후 5분 내 최대 PnL 확인
            future_prices = [c["trade_price"] for c in
                           self.all_candles[idx:min(idx+6, len(self.all_candles))]]
            entry_p = prices[-1]
            best_future = max((p / entry_p - 1) * 100 for p in future_prices)
            worst_future = min((p / entry_p - 1) * 100 for p in future_prices)

            # 수익 가능성이 있는 구간만 (50% 확률로 필터)
            score = abs_change * vol_spike
            if best_future > FEE_PCT:
                score += 5  # 수익 가능 구간 우선
            candidates.append((score, idx))

        if candidates:
            # 상위 30%에서 랜덤 선택 (다양성 유지)
            candidates.sort(key=lambda x: x[0], reverse=True)
            top_n = max(1, len(candidates) // 3)
            return random.choice(candidates[:top_n])[1]

        return random.randint(30, max(31, max_start))

    def reset(self, seed=None, options=None):
        """새 에피소드 시작 — 시그널 조건 진입"""
        super().reset(seed=seed)

        start = self._find_signal_entry()

        self._entry_price = self.all_candles[start]["trade_price"]
        # 진입 전 컨텍스트 + 진입 후 캔들
        self._episode_candles = self.all_candles[start - 15:start + MAX_HOLD + 1]
        self._current_step = 15  # 진입 시점 = index 15
        self._strategy = random.randint(0, 2)
        self._done = False
        self._total_reward = 0
        self._peak_pnl = 0.0

        return self._compute_obs(), {}

    def _future_pnl(self, from_step: int, lookahead: int = 3) -> float:
        """from_step 이후 lookahead분간 최대 PnL (HOLD 가치 추정)"""
        best = 0.0
        for i in range(1, lookahead + 1):
            idx = min(from_step + i, len(self._episode_candles) - 1)
            p = self._episode_candles[idx]["trade_price"]
            pnl = (p / self._entry_price - 1) * 100 - FEE_PCT
            best = max(best, pnl)
        return best

    def step(self, action: int):
        """
        action: 0=HOLD, 1=TAKE_PROFIT, 2=STOP_LOSS

        v7 보상함수 개선:
        - HOLD 중 수익 증가 시 양의 보상 (인내심 보상)
        - 조기 청산 페널티 (hold < 3분이면 벌칙)
        - 모멘텀 방향 반영 (상승 중 TP는 보너스, 하락 중 SL은 보너스)
        - 미래 PnL 대비 현재 청산의 후회 비용
        """
        if self._done:
            return self._compute_obs(), 0.0, True, False, {}

        self._current_step += 1
        hold_min = self._current_step - 15  # 진입 이후 경과 분

        current_idx = min(self._current_step, len(self._episode_candles) - 1)
        current_price = self._episode_candles[current_idx]["trade_price"]
        pnl_pct = (current_price / self._entry_price - 1) * 100 - FEE_PCT

        # 이전 스텝 PnL (모멘텀 계산용)
        prev_idx = max(current_idx - 1, 0)
        prev_price = self._episode_candles[prev_idx]["trade_price"]
        prev_pnl = (prev_price / self._entry_price - 1) * 100 - FEE_PCT
        pnl_delta = pnl_pct - prev_pnl  # 이번 분 PnL 변화량

        # 최고 PnL 추적 (트레일링 스톱 학습용)
        if not hasattr(self, '_peak_pnl'):
            self._peak_pnl = pnl_pct
        self._peak_pnl = max(self._peak_pnl, pnl_pct)

        reward = 0.0
        terminated = False
        info = {}

        if action == 0:  # HOLD
            # v7: 모멘텀 기반 HOLD 보상
            if pnl_pct > 0 and pnl_delta > 0:
                # 수익 중 + 상승 중 → 인내심 보상
                reward = 0.01 + pnl_delta * 0.5
            elif pnl_pct > 0 and pnl_delta <= 0:
                # 수익 중이나 하락 → 약간의 시간비용만
                reward = -0.005
            elif pnl_pct <= 0 and pnl_delta > 0:
                # 손실 중이나 반등 → 약간 양의 보상
                reward = 0.003
            else:
                # 손실 중 + 하락 → 시간비용 가중
                reward = -0.01

            # 강제 청산 조건
            if hold_min >= MAX_HOLD:
                reward = pnl_pct * 0.8
                terminated = True
                info["exit_reason"] = "timeout"
            elif pnl_pct <= -SL_DEFAULT:
                reward = pnl_pct * 1.5  # 강제 손절 큰 벌칙
                terminated = True
                info["exit_reason"] = "forced_sl"

        elif action == 1:  # TAKE_PROFIT
            # v7: 조기 청산 페널티 + 모멘텀 반영
            if hold_min <= 1:
                # 1분 이내 즉시 청산 = 큰 페널티
                reward = pnl_pct * 0.3 - 0.05
            elif pnl_pct > 0:
                # 수익 청산
                reward = pnl_pct * 2.0  # 수익 TP 큰 보너스
                if pnl_pct >= TP_DEFAULT:
                    reward += 0.1  # 목표 익절 달성 추가 보너스
                if pnl_delta > 0:
                    # 아직 상승 중인데 TP → 약간의 후회 비용
                    future = self._future_pnl(current_idx)
                    if future > pnl_pct + 0.05:
                        reward -= 0.03  # 더 갈 수 있었는데 조기 청산
            else:
                # 손실 상태에서 TP → 손절과 동일 취급
                reward = pnl_pct * 0.8
            terminated = True
            info["exit_reason"] = "take_profit"

        elif action == 2:  # STOP_LOSS
            # v7: 상황별 손절 보상
            if pnl_pct < -0.15 and pnl_delta < 0:
                # 하락 중 손절 → 현명한 판단
                reward = pnl_pct + 0.15  # 손실 경감 보상
            elif pnl_pct < -SL_DEFAULT * 0.8:
                # 큰 손실 빠른 손절 → 좋은 판단
                reward = pnl_pct + 0.1
            elif pnl_pct > 0:
                # 수익 중 SL → 벌칙
                reward = -0.1
            else:
                reward = pnl_pct * 0.8
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

        obs = self._compute_obs()
        return obs, reward, terminated, False, info

    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0


class ScalpExitEnvV2(ScalpExitEnv):
    """
    V2: 연속 행동 공간 (SAC용)
    action: [0, 1] → 0=HOLD, 1=전량청산, 중간=부분청산
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.action_space = spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)

    def step(self, action):
        exit_prob = float(action[0])

        if exit_prob < 0.3:
            return super().step(0)   # HOLD
        elif exit_prob < 0.7:
            return super().step(1)   # TAKE_PROFIT (partial → full for now)
        else:
            return super().step(2)   # STOP_LOSS
