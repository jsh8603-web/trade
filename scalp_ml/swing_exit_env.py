#!/usr/bin/env python3
"""
스윙 청산 최적화 RL 환경 (SwingExitEnv)

ScalpExitEnv v3 — 5분봉 기반, TP 0.3~0.5%, 수수료 대비 2배+ 수익 목표

핵심 변경:
- 1분봉 → 5분봉 집계 (더 큰 움직임 포착)
- TP 목표 0.3~0.5% (수수료 0.1% 대비 3~5배)
- SL 0.4% (여유 있는 리스크 한도 — 강제손절 줄이기)
- 최대 보유 60분 (12 스텝 × 5분)
- 조기 손절 적극 학습: 하락 초기(-0.1%) 탈출 시 보상
- 진입 필터: RSI + 거래량 스파이크 + 모멘텀 3중 필터
- 보상함수: 수수료 차감 후 순이익 기반

Observation: [pnl_pct, hold_steps, mom_1bar, mom_3bar, vol_ratio, rsi, bb_pos,
              strategy, trend_strength, entry_quality]
Action: 0=HOLD, 1=TAKE_PROFIT, 2=STOP_LOSS
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

log = logging.getLogger("swing_exit_env")

PROJECT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_DIR / "data" / "scalp_models"

# ── 파라미터 ──────────────────────────────────────────────
FEE_PCT = 0.1        # 왕복 수수료 (%)
BAR_MINUTES = 5      # 1봉 = 5분
MAX_HOLD_BARS = 12   # 최대 보유 = 12봉 = 60분
TP_TARGET = 0.4      # 목표 익절 (%) — 수수료 4배
SL_LIMIT = 0.4       # 손절 한도 (%) — 넓혀서 강제손절 줄이기 (0.25→0.4)
MIN_PROFIT = 0.2     # 최소 수익 목표 (%) — 수수료 2배 = "1000원 내고 2000원 벌기"


def _aggregate_5min(candles_1m: list[dict]) -> list[dict]:
    """1분봉 → 5분봉 집계"""
    bars = []
    for i in range(0, len(candles_1m) - BAR_MINUTES + 1, BAR_MINUTES):
        chunk = candles_1m[i:i + BAR_MINUTES]
        if len(chunk) < BAR_MINUTES:
            break
        bar = {
            "open": chunk[0]["opening_price"],
            "high": max(c["high_price"] for c in chunk),
            "low": min(c["low_price"] for c in chunk),
            "close": chunk[-1]["trade_price"],
            "volume": sum(c["candle_acc_trade_volume"] for c in chunk),
            "trade_value": sum(c["candle_acc_trade_price"] for c in chunk),
            "timestamp": chunk[-1]["timestamp"],
        }
        bars.append(bar)
    return bars


class SwingExitEnv(gym.Env):
    """
    5분봉 기반 스윙 청산 최적화 환경.

    목표: 수수료(0.1%) 대비 2배+ 수익 (순이익 0.2%+)
    """

    metadata = {"render_modes": []}

    def __init__(self, candle_data: list[dict] = None, candle_path: str = None,
                 tp_target: float = TP_TARGET, sl_limit: float = SL_LIMIT):
        super().__init__()

        # 1분봉 로드 → 5분봉 집계
        if candle_data:
            raw = candle_data
        elif candle_path:
            with open(candle_path, "rb") as f:
                raw = pickle.load(f)
        else:
            cache = MODEL_DIR / "candles_cache.pkl"
            if cache.exists():
                with open(cache, "rb") as f:
                    raw = pickle.load(f)
            else:
                raise FileNotFoundError("캔들 데이터 필요. train_lgbm.py 먼저 실행하세요.")

        self.bars_5m = _aggregate_5min(raw)
        log.info(f"5분봉 {len(self.bars_5m)}개 생성 (1분봉 {len(raw)}개에서)")

        self.tp_target = tp_target
        self.sl_limit = sl_limit

        # 행동: 0=HOLD, 1=TAKE_PROFIT, 2=STOP_LOSS
        self.action_space = spaces.Discrete(3)

        # 관측: 10개 피처
        self.observation_space = spaces.Box(
            low=np.array([-10, 0, -5, -5, 0, 0, 0, 0, -1, 0], dtype=np.float32),
            high=np.array([10, MAX_HOLD_BARS, 5, 5, 10, 100, 1, 2, 1, 1], dtype=np.float32),
        )

        # 에피소드 상태
        self._entry_price = 0.0
        self._current_step = 0
        self._context_start = 0
        self._strategy = 0
        self._done = False
        self._total_reward = 0.0
        self._peak_pnl = 0.0
        self._entry_quality = 0.0

        # 통계
        self.episode_count = 0
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0.0
        self.pnl_history = deque(maxlen=1000)

    def _compute_obs(self) -> np.ndarray:
        """현재 상태 → 10차원 관측 벡터"""
        bar_idx = self._context_start + self._current_step
        bar_idx = min(bar_idx, len(self.bars_5m) - 1)

        current_price = self.bars_5m[bar_idx]["close"]
        pnl_pct = (current_price / self._entry_price - 1) * 100

        # 5분봉 가격 시퀀스
        start = max(0, bar_idx - 20)
        prices = [b["close"] for b in self.bars_5m[start:bar_idx + 1]]

        # 모멘텀 (1봉 = 5분, 3봉 = 15분)
        mom_1 = (prices[-1] / prices[-2] - 1) * 100 if len(prices) >= 2 else 0
        mom_3 = (prices[-1] / prices[-4] - 1) * 100 if len(prices) >= 4 else 0

        # 거래량 비율
        vols = [b["volume"] for b in self.bars_5m[start:bar_idx + 1]]
        if len(vols) >= 5:
            vol_recent = np.mean(vols[-2:]) if len(vols) >= 2 else vols[-1]
            vol_prev = np.mean(vols[-5:-2]) if len(vols) >= 5 else 1
            vol_ratio = min(vol_recent / max(vol_prev, 0.001), 10)
        else:
            vol_ratio = 1.0

        # RSI (14봉)
        if len(prices) >= 15:
            diffs = [prices[i] - prices[i - 1] for i in range(-14, 0)]
            gains = [d for d in diffs if d > 0]
            loss_v = [-d for d in diffs if d < 0]
            avg_g = sum(gains) / 14 if gains else 0
            avg_l = sum(loss_v) / 14 if loss_v else 0.001
            rsi = 100 - (100 / (1 + avg_g / avg_l))
        else:
            rsi = 50.0

        # 볼린저밴드 위치
        if len(prices) >= 20:
            sma = np.mean(prices[-20:])
            std = np.std(prices[-20:])
            bb_pos = (current_price - (sma - 2 * std)) / (4 * std) if std > 0 else 0.5
            bb_pos = np.clip(bb_pos, 0, 1)
        else:
            bb_pos = 0.5

        # 추세 강도 (-1 ~ +1): 5봉 SMA 방향
        if len(prices) >= 6:
            sma5_now = np.mean(prices[-5:])
            sma5_prev = np.mean(prices[-6:-1])
            trend = np.clip((sma5_now / sma5_prev - 1) * 100, -1, 1)
        else:
            trend = 0.0

        hold_bars = self._current_step - 20  # 진입 이후 경과 봉 수

        return np.array([
            np.clip(pnl_pct, -10, 10),
            float(max(0, hold_bars)),
            np.clip(mom_1, -5, 5),
            np.clip(mom_3, -5, 5),
            vol_ratio,
            rsi,
            float(bb_pos),
            float(self._strategy),
            float(trend),
            float(self._entry_quality),
        ], dtype=np.float32)

    def _find_quality_entry(self) -> tuple[int, float]:
        """고품질 진입 시점 찾기 — 3중 필터

        조건:
        1. RSI < 40 또는 > 60 (과매도/과매수 반전 포착)
        2. 거래량 스파이크 1.8배+
        3. 15분 모멘텀 0.15%+ (방향성 확인)
        4. 진입 후 30분(6봉) 내 0.2%+ 도달 가능 구간 우선

        Returns:
            (bar_index, entry_quality_score)
        """
        max_start = len(self.bars_5m) - MAX_HOLD_BARS - 25
        if max_start < 25:
            return 25, 0.5

        candidates = []

        for _ in range(500):
            idx = random.randint(25, max_start)

            prices = [b["close"] for b in self.bars_5m[idx - 5:idx + 1]]
            if len(prices) < 6:
                continue

            # 1. 15분 모멘텀 (3봉)
            mom_15m = (prices[-1] / prices[-4] - 1) * 100 if len(prices) >= 4 else 0
            abs_mom = abs(mom_15m)
            if abs_mom < 0.15:
                continue

            # 2. 거래량 스파이크
            vols = [b["volume"] for b in self.bars_5m[idx - 8:idx + 1]]
            if len(vols) < 8:
                continue
            vol_avg = np.mean(vols[:5])
            vol_recent = np.mean(vols[-3:])
            vol_spike = vol_recent / max(vol_avg, 0.001)
            if vol_spike < 1.8:
                continue

            # 3. RSI 조건
            all_prices = [b["close"] for b in self.bars_5m[max(0, idx - 20):idx + 1]]
            if len(all_prices) >= 15:
                diffs = [all_prices[i] - all_prices[i - 1] for i in range(-14, 0)]
                gains = [d for d in diffs if d > 0]
                loss_v = [-d for d in diffs if d < 0]
                avg_g = sum(gains) / 14 if gains else 0
                avg_l = sum(loss_v) / 14 if loss_v else 0.001
                rsi = 100 - (100 / (1 + avg_g / avg_l))
            else:
                rsi = 50.0

            # RSI 극단 시 가산점
            rsi_score = 0
            if rsi < 35 or rsi > 65:
                rsi_score = 0.3
            elif rsi < 40 or rsi > 60:
                rsi_score = 0.15

            # 4. 진입 후 수익 가능성 확인 (6봉 = 30분)
            future = self.bars_5m[idx:min(idx + 7, len(self.bars_5m))]
            entry_p = prices[-1]
            if mom_15m > 0:
                best_pnl = max((b["high"] / entry_p - 1) * 100 for b in future)
            else:
                best_pnl = max((entry_p / b["low"] - 1) * 100 for b in future)

            # 품질 점수 계산 (0~1)
            quality = min(1.0, (
                abs_mom * 0.3 +          # 모멘텀 강도
                min(vol_spike / 3, 1) * 0.3 +  # 거래량
                rsi_score +              # RSI 극단
                (0.2 if best_pnl > MIN_PROFIT else 0)  # 수익 가능성
            ))

            candidates.append((quality, idx))

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            # 상위 25%에서 랜덤 (다양성 유지)
            top_n = max(1, len(candidates) // 4)
            chosen = random.choice(candidates[:top_n])
            return chosen[1], chosen[0]

        # 폴백: 랜덤
        return random.randint(25, max(26, max_start)), 0.3

    def reset(self, seed=None, options=None):
        """새 에피소드: 고품질 시그널 진입"""
        super().reset(seed=seed)

        entry_idx, quality = self._find_quality_entry()

        self._entry_price = self.bars_5m[entry_idx]["close"]
        self._context_start = entry_idx - 20  # 20봉 컨텍스트
        self._current_step = 20  # 진입 시점
        self._strategy = random.randint(0, 2)
        self._done = False
        self._total_reward = 0.0
        self._peak_pnl = 0.0
        self._entry_quality = quality

        return self._compute_obs(), {}

    def _future_pnl(self, bars_ahead: int = 3) -> float:
        """현재부터 bars_ahead봉 후 최대 PnL"""
        best = 0.0
        bar_idx = self._context_start + self._current_step
        for i in range(1, bars_ahead + 1):
            fidx = min(bar_idx + i, len(self.bars_5m) - 1)
            p = self.bars_5m[fidx]["close"]
            pnl = (p / self._entry_price - 1) * 100 - FEE_PCT
            best = max(best, pnl)
        return best

    def step(self, action: int):
        """
        action: 0=HOLD, 1=TAKE_PROFIT, 2=STOP_LOSS

        보상 설계 핵심: 수수료 차감 후 순이익 기반
        - 수수료(0.1%)를 이기는 청산만 보상
        - TP 시 순이익 0.2%+ 달성하면 큰 보너스 ("1000원 내고 2000원 벌기")
        - 무의미한 청산(순이익 < 0.1%) 페널티
        """
        if self._done:
            return self._compute_obs(), 0.0, True, False, {}

        self._current_step += 1
        hold_bars = self._current_step - 20  # 진입 이후 경과 봉

        bar_idx = self._context_start + self._current_step
        bar_idx = min(bar_idx, len(self.bars_5m) - 1)

        current_price = self.bars_5m[bar_idx]["close"]
        gross_pnl = (current_price / self._entry_price - 1) * 100  # 수수료 전
        net_pnl = gross_pnl - FEE_PCT  # 수수료 후 순이익

        # 이전 봉 PnL
        prev_idx = min(bar_idx - 1, len(self.bars_5m) - 1)
        prev_price = self.bars_5m[max(0, prev_idx)]["close"]
        prev_net = (prev_price / self._entry_price - 1) * 100 - FEE_PCT
        pnl_delta = net_pnl - prev_net

        self._peak_pnl = max(self._peak_pnl, net_pnl)

        reward = 0.0
        terminated = False
        info = {}

        if action == 0:  # HOLD
            if net_pnl > 0 and pnl_delta > 0:
                # 수익 + 상승 중 → 인내심 보상
                reward = 0.02 + pnl_delta * 0.8
            elif net_pnl > 0 and pnl_delta <= 0:
                # 수익이나 하락 중 → 피크 대비 하락 경고
                drawdown = self._peak_pnl - net_pnl
                reward = -0.01 * (1 + drawdown)
            elif net_pnl <= 0 and pnl_delta > 0:
                # 손실이나 반등 중 → 약간 보상
                reward = 0.005
            elif net_pnl < -0.1 and pnl_delta < 0:
                # 손실 -0.1% 넘었는데 계속 하락 → 강한 페널티 (빨리 나가라)
                reward = -0.05 - abs(net_pnl) * 0.3
            else:
                # 손실 + 하락 → 비용
                reward = -0.02

            # 강제 청산
            if hold_bars >= MAX_HOLD_BARS:
                reward = net_pnl * 0.5  # 타임아웃: 적당히
                terminated = True
                info["exit_reason"] = "timeout"
            elif net_pnl <= -self.sl_limit:
                reward = net_pnl * 3.0  # 강제 손절: 매우 큰 벌칙 (여기 오면 안됨)
                terminated = True
                info["exit_reason"] = "forced_sl"

        elif action == 1:  # TAKE_PROFIT
            if hold_bars <= 0:
                # 즉시 청산 → 큰 페널티
                reward = -0.1
            elif net_pnl >= MIN_PROFIT:
                # 목표 달성! 수수료 2배+ 벌었다
                reward = net_pnl * 3.0 + 0.2  # 큰 보너스
                if net_pnl >= self.tp_target:
                    reward += 0.3  # 풀 타겟 달성 추가 보너스
            elif net_pnl > 0:
                # 수익이지만 목표 미달 (수수료만 겨우 넘김)
                reward = net_pnl * 0.5 - 0.05  # 약한 페널티
            else:
                # 손실 상태 청산
                reward = net_pnl * 1.5
            terminated = True
            info["exit_reason"] = "take_profit"

        elif action == 2:  # STOP_LOSS
            if net_pnl < -0.05 and pnl_delta < 0:
                # 손실 초기(-0.05%~) + 하락 중 조기 손절 → 큰 보상!
                # 핵심: 작은 손실로 끊는 게 강제손절(-0.4%)보다 훨씬 낫다
                saved = self.sl_limit + net_pnl  # 강제SL 대비 절약한 손실
                reward = 0.2 + saved * 2.0  # 빨리 나갈수록 보상 큼
            elif net_pnl < -0.15 and pnl_delta >= 0:
                # 큰 손실이지만 반등 중 → 약간의 보상 (손실 제한)
                reward = net_pnl + 0.1
            elif net_pnl > MIN_PROFIT:
                # 큰 수익인데 SL? → 큰 벌칙
                reward = -net_pnl - 0.2
            elif net_pnl > 0:
                # 소액 수익 중 SL → 벌칙
                reward = -0.1
            else:
                # 기타 손실 손절 → 적당한 보상
                reward = 0.05 + net_pnl * 0.3
            terminated = True
            info["exit_reason"] = "stop_loss"

        self._total_reward += reward

        if terminated:
            self._done = True
            self.episode_count += 1
            if net_pnl > 0:
                self.wins += 1
            else:
                self.losses += 1
            self.total_pnl += net_pnl
            self.pnl_history.append(net_pnl)
            info["net_pnl_pct"] = round(net_pnl, 4)
            info["gross_pnl_pct"] = round(gross_pnl, 4)
            info["fee_pct"] = FEE_PCT
            info["hold_bars"] = hold_bars
            info["hold_minutes"] = hold_bars * BAR_MINUTES
            info["total_reward"] = round(self._total_reward, 4)

        obs = self._compute_obs()
        return obs, reward, terminated, False, info

    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0

    @property
    def avg_net_pnl(self) -> float:
        return np.mean(self.pnl_history) if self.pnl_history else 0

    @property
    def profit_factor(self) -> float:
        """총이익 / 총손실 비율"""
        wins = [p for p in self.pnl_history if p > 0]
        losses = [abs(p) for p in self.pnl_history if p < 0]
        return sum(wins) / max(sum(losses), 0.001)


class SwingExitEnvV2(SwingExitEnv):
    """V2: 연속 행동 공간 (SAC용)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.action_space = spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)

    def step(self, action):
        exit_prob = float(action[0])
        if exit_prob < 0.3:
            return super().step(0)   # HOLD
        elif exit_prob < 0.7:
            return super().step(1)   # TAKE_PROFIT
        else:
            return super().step(2)   # STOP_LOSS
