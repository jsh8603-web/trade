#!/usr/bin/env python3
"""
시장 레짐 감지기 — RSI + FGI + 변동성 기반 레짐 분류

레짐 유형:
  - bull_strong:  강한 상승장 (RSI>65, FGI>60, 상승 추세)
  - bull_weak:    약한 상승장 (RSI 50-65, FGI 40-60)
  - sideways:     횡보장 (RSI 40-60, 변동성 낮음)
  - bear_weak:    약한 하락장 (RSI 35-50, FGI 25-40)
  - bear_strong:  강한 하락장 (RSI<35, FGI<25, 하락 추세)
  - volatile:     고변동성 (ATR 높음, 방향 불분명)

각 레짐에 맞는 RL 모델 가중치를 자동 조정한다.

사용법:
  python scripts/regime_detector.py                    # 현재 레짐 출력
  python scripts/regime_detector.py --update-weights   # 모델 가중치 업데이트

파이프라인 통합:
  run_agents.py Phase 2.5에서 모델 가중치 조정에 사용
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
load_dotenv(PROJECT_DIR / ".env")
KST = timezone(timedelta(hours=9))


# ── 레짐 정의 ──────────────────────────────────────────────

REGIME_DEFINITIONS = {
    "bull_strong": {"description": "강한 상승장", "emoji": "🚀"},
    "bull_weak":   {"description": "약한 상승장", "emoji": "📈"},
    "sideways":    {"description": "횡보장",     "emoji": "➡️"},
    "bear_weak":   {"description": "약한 하락장", "emoji": "📉"},
    "bear_strong": {"description": "강한 하락장", "emoji": "💥"},
    "volatile":    {"description": "고변동성",   "emoji": "🌪️"},
}

# 레짐별 RL 모델 가중치 (합계 = 1.0)
# 어떤 시장 상태에서 어떤 모델이 더 잘 맞는지 — 7년 역사 훈련 결과 반영
# historical: 7년 레짐별 전문가 (bull→SAC+66%, sideways→TD3+18%, bear→PPO Sharpe+0.013)
DEFAULT_REGIME_WEIGHTS = {
    "bull_strong": {"sb3": 0.15, "dt": 0.25, "multi_agent": 0.20, "offline": 0.10, "historical": 0.30},
    "bull_weak":   {"sb3": 0.20, "dt": 0.25, "multi_agent": 0.20, "offline": 0.15, "historical": 0.20},
    "sideways":    {"sb3": 0.20, "dt": 0.20, "multi_agent": 0.15, "offline": 0.15, "historical": 0.30},
    "bear_weak":   {"sb3": 0.20, "dt": 0.15, "multi_agent": 0.20, "offline": 0.20, "historical": 0.25},
    "bear_strong": {"sb3": 0.15, "dt": 0.10, "multi_agent": 0.20, "offline": 0.25, "historical": 0.30},
    "volatile":    {"sb3": 0.25, "dt": 0.15, "multi_agent": 0.25, "offline": 0.15, "historical": 0.20},
}


def detect_regime(
    rsi: float | None = None,
    fgi: int | None = None,
    change_rate_24h: float | None = None,
    volume_ratio: float | None = None,
    atr_pct: float | None = None,
) -> dict:
    """현재 시장 지표로 레짐을 분류한다.

    Args:
        rsi: RSI(14) 값
        fgi: Fear & Greed Index (0-100)
        change_rate_24h: 24시간 가격 변동률 (소수, 예: 0.03 = 3%)
        volume_ratio: 현재 거래량 / 평균 거래량 비율
        atr_pct: ATR을 현재가 대비 % 변환 (변동성 지표)

    Returns:
        {"regime": str, "confidence": float, "scores": dict, "weights": dict}
    """
    # 기본값
    rsi = rsi if rsi is not None else 50.0
    fgi = fgi if fgi is not None else 50
    change = (change_rate_24h or 0) * 100 if change_rate_24h is not None and abs(change_rate_24h or 0) < 1 else (change_rate_24h or 0)
    vol_ratio = volume_ratio if volume_ratio is not None else 1.0
    atr = atr_pct if atr_pct is not None else 1.5

    # 각 레짐에 대한 점수 계산 (0~100)
    scores = {}

    # Bull Strong
    bull_s = 0
    if rsi > 65: bull_s += 30
    elif rsi > 55: bull_s += 15
    if fgi > 60: bull_s += 25
    elif fgi > 45: bull_s += 10
    if change > 3: bull_s += 25
    elif change > 1: bull_s += 15
    if vol_ratio > 1.3: bull_s += 20
    scores["bull_strong"] = min(100, bull_s)

    # Bull Weak
    bull_w = 0
    if 50 <= rsi <= 65: bull_w += 30
    elif 45 <= rsi < 50: bull_w += 15
    if 40 <= fgi <= 60: bull_w += 25
    if 0.5 <= change <= 3: bull_w += 25
    if 0.8 <= vol_ratio <= 1.3: bull_w += 20
    scores["bull_weak"] = min(100, bull_w)

    # Sideways
    side = 0
    if 40 <= rsi <= 60: side += 30
    if 35 <= fgi <= 65: side += 20
    if abs(change) < 1.5: side += 30
    if atr < 2.0: side += 20
    scores["sideways"] = min(100, side)

    # Bear Weak
    bear_w = 0
    if 35 <= rsi <= 50: bear_w += 30
    elif 30 <= rsi < 35: bear_w += 15
    if 25 <= fgi <= 40: bear_w += 25
    if -3 <= change <= -0.5: bear_w += 25
    if 0.8 <= vol_ratio <= 1.3: bear_w += 20
    scores["bear_weak"] = min(100, bear_w)

    # Bear Strong
    bear_s = 0
    if rsi < 35: bear_s += 30
    elif rsi < 45: bear_s += 15
    if fgi < 25: bear_s += 25
    elif fgi < 35: bear_s += 10
    if change < -3: bear_s += 25
    elif change < -1: bear_s += 15
    if vol_ratio > 1.5: bear_s += 20
    scores["bear_strong"] = min(100, bear_s)

    # Volatile
    vol = 0
    if atr > 3.0: vol += 35
    elif atr > 2.0: vol += 20
    if vol_ratio > 1.5: vol += 25
    if abs(change) > 4: vol += 25
    if abs(rsi - 50) > 20 and abs(change) > 2: vol += 15
    scores["volatile"] = min(100, vol)

    # 최고 점수 레짐 선택
    best_regime = max(scores, key=scores.get)
    best_score = scores[best_regime]

    # 두 번째 레짐과의 차이로 confidence 계산
    sorted_scores = sorted(scores.values(), reverse=True)
    gap = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else sorted_scores[0]
    confidence = min(1.0, gap / 50.0 + 0.3)  # 최소 0.3

    # 해당 레짐의 모델 가중치 — 학습된 가중치 우선 사용
    weights = None
    try:
        from scripts.regime_learner import get_learned_weights
        weights = get_learned_weights(best_regime)
    except Exception:
        pass
    if not weights:
        weights = DEFAULT_REGIME_WEIGHTS.get(best_regime, DEFAULT_REGIME_WEIGHTS["sideways"])

    return {
        "regime": best_regime,
        "description": REGIME_DEFINITIONS[best_regime]["description"],
        "confidence": round(confidence, 3),
        "scores": scores,
        "weights": weights,
        "indicators": {
            "rsi": rsi,
            "fgi": fgi,
            "change_24h_pct": round(change, 2),
            "volume_ratio": round(vol_ratio, 2),
            "atr_pct": round(atr, 2),
        },
    }


def detect_regime_from_market_data(market_data: dict) -> dict:
    """market_data dict에서 지표를 추출하여 레짐을 감지한다."""
    indicators = market_data.get("indicators", {})
    ticker = market_data.get("ticker", {})
    fgi_data = market_data.get("fear_greed", {})

    rsi = indicators.get("rsi_14")
    fgi = fgi_data.get("value")
    change_rate = ticker.get("signed_change_rate")

    # ATR 계산 (bollinger bandwidth / 4 ≈ ATR proxy, 2σ band → σ/2 근사)
    bollinger = indicators.get("bollinger", {})
    upper = bollinger.get("upper", 0)
    lower = bollinger.get("lower", 0)
    mid = bollinger.get("middle", 1)
    bb_width = ((upper - lower) / mid * 100) if mid > 0 else 6.0
    atr_pct = bb_width / 4  # BB width(8-15%) → ATR proxy(2-3.75%)

    return detect_regime(
        rsi=rsi,
        fgi=fgi,
        change_rate_24h=change_rate,
        atr_pct=atr_pct,
    )


def update_regime_weights_from_history(days: int = 30) -> dict:
    """과거 레짐별 모델 정확도를 분석하여 가중치를 최적화한다."""
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not supabase_url or not supabase_key:
        return DEFAULT_REGIME_WEIGHTS

    # 향후 market_context_log + rl_model_predictions 조인으로 구현
    # 현재는 기본 가중치 반환
    return DEFAULT_REGIME_WEIGHTS


# ── CLI ──────────────────────────────────────────────────

if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # 현재 시장 데이터로 레짐 감지
    try:
        r = requests.get(
            "https://api.upbit.com/v1/ticker",
            params={"markets": "KRW-BTC"},
            timeout=10,
        )
        if r.ok:
            ticker = r.json()[0]
            change = ticker.get("signed_change_rate", 0)

            # RSI는 별도 계산 필요 → 간이 추정
            result = detect_regime(
                change_rate_24h=change,
            )
            info = REGIME_DEFINITIONS[result["regime"]]
            print(f"{info['emoji']} 현재 레짐: {result['regime']} ({info['description']})")
            print(f"   confidence: {result['confidence']:.1%}")
            print(f"   점수: {json.dumps(result['scores'], indent=2)}")
            print(f"   모델 가중치: {json.dumps(result['weights'], indent=2)}")
    except Exception as e:
        print(f"레짐 감지 실패: {e}", file=sys.stderr)
