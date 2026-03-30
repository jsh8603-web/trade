#!/usr/bin/env python3
"""
2026년 1월 백테스트 시뮬레이션 — 히스토리컬 데이터 기반 매매 + RAG 임베딩 기록

1. Upbit 4시간봉 캔들 수집 (2025-12-25 ~ 2026-01-31, 지표 계산용 선행 데이터 포함)
2. Alternative.me 히스토리컬 FGI 수집
3. 외부 데이터(뉴스감성, 고래동향, 매크로, SNS) 시장 상황 기반 시뮬레이션
4. 에이전트 점수제 매매 로직으로 4시간 간격 시뮬레이션
5. Gemini embedding-001로 3072d 벡터 생성
6. Supabase decisions + rag_analysis_vectors 테이블 기록
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# ── 프로젝트 루트 설정 ─────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
load_dotenv(PROJECT_DIR / ".env")

# ── Gemini 임베딩 ──────────────────────────────────────
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ── Supabase ───────────────────────────────────────────
from supabase import create_client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── 에이전트 임포트 ────────────────────────────────────
from agents.conservative import ConservativeAgent
from agents.moderate import ModerateAgent
from agents.aggressive import AggressiveAgent

KST = timezone(timedelta(hours=9))
UTC = timezone.utc

# ── 설정 ──────────────────────────────────────────────
SIM_START = datetime(2026, 1, 1, 0, 0, tzinfo=KST)
SIM_END = datetime(2026, 2, 1, 0, 0, tzinfo=KST)
INTERVAL_HOURS = 4
INITIAL_KRW = 5_000_000  # 시뮬레이션 시작 자금 500만원
MAX_TRADE_AMOUNT = 100_000
EMBEDDING_MODEL = "models/gemini-embedding-001"
BATCH_SIZE = 5  # 임베딩 배치 크기 (rate limit 대응)

# ── 시드 고정 (재현성) ─────────────────────────────────
random.seed(2026_01)


# =====================================================
#  Phase 1: Upbit 히스토리컬 캔들 수집
# =====================================================

def fetch_upbit_candles_4h(to_dt: datetime, count: int = 200) -> list[dict]:
    """Upbit 4시간봉 캔들 수집. to_dt(KST) 이전 count개."""
    url = "https://api.upbit.com/v1/candles/minutes/240"
    to_str = to_dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")
    params = {"market": "KRW-BTC", "to": to_str, "count": min(count, 200)}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    candles = resp.json()
    # 오래된 순으로 정렬
    candles.sort(key=lambda c: c["candle_date_time_kst"])
    return candles


def collect_all_candles() -> list[dict]:
    """2025-12-20 ~ 2026-02-01 전체 4시간봉 수집 (지표 계산용 선행 포함)."""
    all_candles = []
    cursor = datetime(2026, 2, 1, 4, 0, tzinfo=KST)  # 약간 여유
    target_start = datetime(2025, 12, 20, 0, 0, tzinfo=KST)

    print("[1/6] Upbit 4시간봉 캔들 수집 중...")
    while True:
        batch = fetch_upbit_candles_4h(cursor, 200)
        if not batch:
            break
        all_candles = batch + all_candles
        oldest = datetime.fromisoformat(batch[0]["candle_date_time_kst"])
        if oldest.tzinfo is None:
            oldest = oldest.replace(tzinfo=KST)
        if oldest <= target_start:
            break
        cursor = oldest
        time.sleep(0.15)  # rate limit

    # 기간 필터
    filtered = []
    for c in all_candles:
        dt = datetime.fromisoformat(c["candle_date_time_kst"])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        if target_start <= dt <= SIM_END:
            c["_dt_kst"] = dt
            filtered.append(c)

    print(f"  → {len(filtered)}개 캔들 수집 완료")
    return filtered


# ── 기술 지표 계산 ────────────────────────────────────

def calc_rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    recent = deltas[-(period):]
    gains = [d for d in recent if d > 0]
    losses = [-d for d in recent if d < 0]
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0.001
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calc_sma(closes: list[float], period: int = 20) -> float:
    if len(closes) < period:
        return closes[-1] if closes else 0
    return sum(closes[-period:]) / period


def calc_macd(closes: list[float]) -> dict:
    def ema(data, period):
        if len(data) < period:
            return data[-1] if data else 0
        k = 2 / (period + 1)
        val = sum(data[:period]) / period
        for d in data[period:]:
            val = d * k + val * (1 - k)
        return val

    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    macd_line = ema12 - ema26
    # 시그널은 간이 계산
    signal = ema(closes[-9:], 9) if len(closes) >= 9 else closes[-1]
    return {
        "macd": round(macd_line, 2),
        "signal": round(signal, 2),
        "golden_cross": macd_line > signal,
    }


def calc_bollinger(closes: list[float], period: int = 20) -> dict:
    if len(closes) < period:
        return {"upper": 0, "middle": 0, "lower": 0}
    sma = sum(closes[-period:]) / period
    variance = sum((c - sma) ** 2 for c in closes[-period:]) / period
    std = math.sqrt(variance)
    return {
        "upper": round(sma + 2 * std, 0),
        "middle": round(sma, 0),
        "lower": round(sma - 2 * std, 0),
    }


def compute_indicators(candles: list[dict], idx: int) -> dict:
    """idx 시점까지의 캔들로 지표 계산."""
    closes = [c["trade_price"] for c in candles[: idx + 1]]
    rsi = calc_rsi(closes)
    sma20 = calc_sma(closes)
    macd = calc_macd(closes)
    bb = calc_bollinger(closes)
    price = closes[-1]
    sma_deviation = ((price - sma20) / sma20 * 100) if sma20 else 0

    # 24시간 변화율 (6개 캔들 전 대비)
    if idx >= 6:
        price_24h_ago = candles[idx - 6]["trade_price"]
        change_24h = (price - price_24h_ago) / price_24h_ago * 100
    else:
        change_24h = 0

    return {
        "current_price": price,
        "rsi_14": rsi,
        "sma_20": round(sma20),
        "sma_deviation_pct": round(sma_deviation, 2),
        "macd": macd,
        "bollinger": bb,
        "price_change_24h": round(change_24h, 2),
        "volume": candles[idx].get("candle_acc_trade_volume", 0),
    }


# =====================================================
#  Phase 2: 히스토리컬 FGI 수집
# =====================================================

def fetch_historical_fgi() -> dict[str, dict]:
    """Alternative.me에서 2026년 1월 FGI 일별 수집."""
    print("[2/6] 히스토리컬 FGI 수집 중...")
    url = "https://api.alternative.me/fng/"
    params = {"limit": 60, "format": "json"}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json().get("data", [])

    fgi_map = {}
    for item in data:
        ts = int(item["timestamp"])
        dt = datetime.fromtimestamp(ts, tz=UTC)
        date_str = dt.strftime("%Y-%m-%d")
        fgi_map[date_str] = {
            "value": int(item["value"]),
            "classification": item["value_classification"],
        }

    print(f"  → {len(fgi_map)}일 FGI 수집 완료")
    return fgi_map


def get_fgi_for_date(fgi_map: dict, dt: datetime) -> dict:
    """해당 날짜의 FGI 반환. 없으면 가장 가까운 이전 날짜 사용."""
    date_str = dt.strftime("%Y-%m-%d")
    if date_str in fgi_map:
        return fgi_map[date_str]

    # 가장 가까운 이전 날짜 찾기
    for delta in range(1, 7):
        prev = (dt - timedelta(days=delta)).strftime("%Y-%m-%d")
        if prev in fgi_map:
            return fgi_map[prev]

    return {"value": 50, "classification": "Neutral"}


# =====================================================
#  Phase 3: 외부 데이터 시뮬레이션
# =====================================================

def simulate_external_data(
    dt: datetime, indicators: dict, fgi: dict, prev_externals: list[dict]
) -> dict:
    """시장 상황 기반 현실적 외부 데이터 생성.

    실제 가격/RSI/FGI 추이를 기반으로 뉴스감성, 고래동향, 매크로 등을
    현실적으로 시뮬레이션한다.
    """
    change_24h = indicators["price_change_24h"]
    fgi_val = fgi["value"]

    # ── 뉴스 감성 (가격 변화 + FGI 상관) ────────────────
    news_score = 0
    if change_24h < -3:
        news_score = random.uniform(-0.8, -0.3)
    elif change_24h < -1:
        news_score = random.uniform(-0.5, 0.1)
    elif change_24h > 3:
        news_score = random.uniform(0.3, 0.8)
    elif change_24h > 1:
        news_score = random.uniform(0.0, 0.5)
    else:
        news_score = random.uniform(-0.3, 0.3)

    # FGI 보정
    if fgi_val < 25:
        news_score -= random.uniform(0.1, 0.3)
    elif fgi_val > 75:
        news_score += random.uniform(0.1, 0.3)

    news_score = max(-1.0, min(1.0, news_score))

    if news_score < -0.3:
        news_sentiment = "negative"
    elif news_score < -0.1:
        news_sentiment = "slightly_negative"
    elif news_score > 0.3:
        news_sentiment = "positive"
    elif news_score > 0.1:
        news_sentiment = "slightly_positive"
    else:
        news_sentiment = "neutral"

    # ── 고래 동향 ─────────────────────────────────────
    # 급락 시 고래 매집, 급등 시 고래 이탈 경향
    if change_24h < -3:
        whale_activity = random.choice(["accumulating", "accumulating", "neutral"])
        whale_net_flow = random.uniform(-500, -50)  # 거래소 유출 (매집)
    elif change_24h > 3:
        whale_activity = random.choice(["distributing", "distributing", "neutral"])
        whale_net_flow = random.uniform(50, 400)  # 거래소 유입 (매도 준비)
    else:
        whale_activity = random.choice(["neutral", "accumulating", "distributing"])
        whale_net_flow = random.uniform(-200, 200)

    # ── 바이낸스 지표 시뮬레이션 ─────────────────────────
    # 김치 프리미엄: 공포 시 음수, 탐욕 시 양수 경향
    kimchi_base = (fgi_val - 50) * 0.04  # FGI 50 → 0%, FGI 80 → 1.2%
    kimchi_pct = round(kimchi_base + random.uniform(-1.0, 1.0), 2)

    # 롱숏비: 가격 상승 시 롱 증가 경향
    ls_base = 1.0 + change_24h * 0.03
    ls_ratio = round(max(0.5, min(2.0, ls_base + random.uniform(-0.15, 0.15))), 2)

    # 펀딩비: 롱숏비에 비례
    funding_rate = round((ls_ratio - 1.0) * 0.01 + random.uniform(-0.005, 0.005), 5)

    # OI 변화
    oi_change = round(change_24h * random.uniform(0.5, 1.5) + random.uniform(-2, 2), 2)

    # ── 매크로 지표 ───────────────────────────────────
    # 1월은 연초 효과 + 미국 경제 지표에 따라 변동
    day_of_month = dt.day
    macro_base = random.uniform(-15, 15)
    # 월 초반 긍정적, 중반 이후 변동성 증가
    if day_of_month <= 10:
        macro_base += random.uniform(0, 10)
    elif day_of_month >= 20:
        macro_base += random.uniform(-10, 5)

    macro_score = round(max(-30, min(30, macro_base)), 1)
    if macro_score > 10:
        macro_sentiment = "positive"
    elif macro_score > 0:
        macro_sentiment = "slightly_positive"
    elif macro_score > -10:
        macro_sentiment = "neutral"
    elif macro_score > -20:
        macro_sentiment = "slightly_negative"
    else:
        macro_sentiment = "negative"

    # S&P500, DXY, 금, 유가 시뮬레이션
    sp500_change = round(macro_score * 0.05 + random.uniform(-0.5, 0.5), 2)
    dxy_value = round(103.5 + random.uniform(-2, 2) - macro_score * 0.05, 2)
    gold_change = round(-macro_score * 0.03 + random.uniform(-0.5, 0.5), 2)

    # ── SNS 감성 (뉴스 감성 + 노이즈) ──────────────────
    sns_score = news_score * 0.7 + random.uniform(-0.3, 0.3)
    sns_score = max(-1.0, min(1.0, round(sns_score, 2)))

    # ── Data Fusion 종합 ──────────────────────────────
    fusion_score = 0
    fusion_score += int(news_score * 10)
    fusion_score += int(-whale_net_flow * 0.02)  # 유출 = 긍정
    fusion_score += int(macro_score * 0.3)
    fusion_score += int(sns_score * 5)
    if kimchi_pct < -1:
        fusion_score += 5  # 디스카운트 = 긍정
    elif kimchi_pct > 3:
        fusion_score -= 5

    fusion_score = max(-30, min(30, fusion_score))

    if fusion_score >= 15:
        fusion_signal = "strong_buy"
    elif fusion_score >= 5:
        fusion_signal = "buy"
    elif fusion_score <= -15:
        fusion_signal = "strong_sell"
    elif fusion_score <= -5:
        fusion_signal = "sell"
    else:
        fusion_signal = "neutral"

    # ── 외부 보너스 점수 (에이전트 매수 점수에 가산) ───────
    external_bonus = 0
    if fusion_signal == "strong_buy":
        external_bonus = 20
    elif fusion_signal == "buy":
        external_bonus = 10
    elif fusion_signal == "strong_sell":
        external_bonus = -10
    elif fusion_signal == "sell":
        external_bonus = -5

    return {
        "external_signal": {
            "total_score": fusion_score,
            "strategy_bonus": external_bonus,
            "fusion": {"signal": fusion_signal, "score": fusion_score},
        },
        "sources": {
            "news_sentiment": {
                "overall_sentiment": news_sentiment,
                "score": round(news_score, 2),
                "article_count": random.randint(5, 25),
            },
            "whale_tracking": {
                "activity": whale_activity,
                "net_flow_btc": round(whale_net_flow, 1),
                "large_tx_count": random.randint(3, 20),
            },
            "binance_sentiment": {
                "kimchi_premium": {"premium_pct": kimchi_pct},
                "top_trader_long_short": {"current_ratio": ls_ratio},
                "funding_rate": {"current_rate": funding_rate},
                "open_interest_change_pct": oi_change,
            },
            "macro": {
                "analysis": {
                    "macro_score": macro_score,
                    "sentiment": macro_sentiment,
                    "sp500_change_pct": sp500_change,
                    "dxy_value": dxy_value,
                    "gold_change_pct": gold_change,
                },
            },
            "social_sentiment": {
                "score": sns_score,
                "volume": random.randint(100, 2000),
            },
            "eth_btc": {
                "eth_btc_z_score": round(random.uniform(-1.5, 1.5), 2),
            },
        },
        "_external_bonus": external_bonus,
        "_news_negative": news_sentiment in ("negative", "slightly_negative"),
    }


# =====================================================
#  Phase 4: 매매 시뮬레이션 엔진
# =====================================================

class TradingSimulator:
    """4시간 간격 매매 시뮬레이션."""

    def __init__(self, initial_krw: int):
        self.krw = float(initial_krw)
        self.btc = 0.0
        self.avg_buy_price = 0.0
        self.active_agent_name = "conservative"
        self.trade_history: list[dict] = []
        self.consecutive_losses = 0
        self.total_trades = 0
        self.daily_trades = {}  # date_str -> count

        # 에이전트 인스턴스
        self.agents = {
            "conservative": ConservativeAgent(),
            "moderate": ModerateAgent(),
            "aggressive": AggressiveAgent(),
        }

    @property
    def agent(self):
        return self.agents[self.active_agent_name]

    def get_portfolio(self, current_price: float) -> dict:
        btc_eval = self.btc * current_price
        total = self.krw + btc_eval
        btc_ratio = btc_eval / total if total > 0 else 0
        pnl_pct = ((current_price / self.avg_buy_price) - 1) * 100 if self.avg_buy_price > 0 and self.btc > 0 else 0

        return {
            "total_krw": self.krw,
            "total_eval": total,
            "btc_ratio": round(btc_ratio, 4),
            "holdings": [{
                "currency": "BTC",
                "balance": self.btc,
                "avg_buy_price": self.avg_buy_price,
                "current_price": current_price,
                "eval_amount": btc_eval,
                "profit_loss_pct": round(pnl_pct, 2),
            }] if self.btc > 0 else [],
            "btc": {"balance": self.btc, "avg_buy_price": self.avg_buy_price},
        }

    def evaluate_switch(self, market_state: dict) -> str | None:
        """간이 전략 전환 로직 (Orchestrator 로직 기반)."""
        danger = market_state["danger_score"]
        opportunity = market_state["opportunity_score"]
        current = self.active_agent_name

        if danger >= 70:
            return "conservative" if current != "conservative" else None
        if danger >= 50 and current == "moderate":
            return "conservative"
        if danger >= 45 and current == "aggressive":
            return "moderate"

        if opportunity >= 60 and danger < 30:
            return "aggressive" if current != "aggressive" else None
        if opportunity >= 40 and danger < 35:
            if current == "conservative":
                return "moderate"
            elif current == "moderate":
                return "aggressive"
        if opportunity >= 25 and danger < 30 and current == "conservative":
            return "moderate"

        # 횡보
        if danger < 25 and opportunity < 25 and current != "moderate":
            return "moderate"

        return None

    def calculate_danger_score(self, indicators: dict, external: dict, portfolio: dict) -> int:
        """위험도 점수 계산."""
        score = 0
        change_24h = indicators["price_change_24h"]
        bs = external["sources"]["binance_sentiment"]
        kimchi_pct = bs["kimchi_premium"]["premium_pct"]
        ls_ratio = bs["top_trader_long_short"]["current_ratio"]
        macro_score = external["sources"]["macro"]["analysis"]["macro_score"]
        news_sentiment = external["sources"]["news_sentiment"]["overall_sentiment"]

        score += min(self.consecutive_losses * 10, 30)

        btc_ratio = portfolio.get("btc_ratio", 0)
        if btc_ratio > 0.3:
            score += min(round((btc_ratio - 0.3) * 100), 20)

        if change_24h < -3:
            score += min(int(abs(change_24h) * 5), 25)

        if kimchi_pct > 3:
            score += min(int((kimchi_pct - 3) * 5), 15)

        if ls_ratio > 1.2:
            score += min(int((ls_ratio - 1.2) * 20), 10)

        if macro_score < -10:
            score += min(int(abs(macro_score) * 0.5), 15)

        if news_sentiment == "negative":
            score += 10
        elif news_sentiment == "slightly_negative":
            score += 5

        return min(score, 100)

    def calculate_opportunity_score(self, indicators: dict, external: dict) -> int:
        """기회 점수 계산."""
        score = 0
        fgi_val = external.get("_fgi_value", 50)
        rsi = indicators["rsi_14"]
        change_24h = indicators["price_change_24h"]
        fusion = external["external_signal"]["fusion"]
        bs = external["sources"]["binance_sentiment"]
        funding_rate = bs["funding_rate"]["current_rate"]
        kimchi_pct = bs["kimchi_premium"]["premium_pct"]
        macro_score = external["sources"]["macro"]["analysis"]["macro_score"]
        news_sentiment = external["sources"]["news_sentiment"]["overall_sentiment"]

        if fgi_val <= 25:
            score += min(int((25 - fgi_val) * 1.5), 25)
        if rsi < 35:
            score += min(int((35 - rsi) * 1.0), 20)
        if change_24h > 1:
            score += min(int(change_24h * 5), 15)
        if fusion["signal"] == "strong_buy":
            score += 20
        elif fusion["signal"] == "buy":
            score += 10
        if funding_rate < 0:
            score += min(int(abs(funding_rate) * 500), 10)
        if kimchi_pct < -1:
            score += min(int(abs(kimchi_pct) * 5), 10)
        if macro_score > 10:
            score += min(int(macro_score * 0.5), 10)
        if news_sentiment in ("positive",):
            score += 5

        return min(score, 100)

    def simulate_step(
        self, dt: datetime, indicators: dict, fgi: dict, external: dict
    ) -> dict:
        """단일 시점 매매 시뮬레이션."""
        price = indicators["current_price"]
        portfolio = self.get_portfolio(price)
        external["_fgi_value"] = fgi["value"]

        # 위험도/기회 점수
        danger = self.calculate_danger_score(indicators, external, portfolio)
        opportunity = self.calculate_opportunity_score(indicators, external)

        market_state = {
            "phase": self._classify_phase(fgi["value"]),
            "fgi": fgi["value"],
            "rsi": indicators["rsi_14"],
            "price_change_24h": indicators["price_change_24h"],
            "btc_ratio": portfolio["btc_ratio"],
            "consecutive_losses": self.consecutive_losses,
            "fusion_signal": external["external_signal"]["fusion"]["signal"],
            "fusion_score": external["external_signal"]["total_score"],
            "kimchi_pct": external["sources"]["binance_sentiment"]["kimchi_premium"]["premium_pct"],
            "ls_ratio": external["sources"]["binance_sentiment"]["top_trader_long_short"]["current_ratio"],
            "funding_rate": external["sources"]["binance_sentiment"]["funding_rate"]["current_rate"],
            "macro_score": external["sources"]["macro"]["analysis"]["macro_score"],
            "macro_sentiment": external["sources"]["macro"]["analysis"]["sentiment"],
            "news_sentiment": external["sources"]["news_sentiment"]["overall_sentiment"],
            "danger_score": danger,
            "opportunity_score": opportunity,
        }

        # 전략 전환
        new_agent = self.evaluate_switch(market_state)
        switch_info = None
        if new_agent and new_agent != self.active_agent_name:
            switch_info = {
                "from": self.active_agent_name,
                "to": new_agent,
                "reason": f"danger={danger}, opportunity={opportunity}",
            }
            self.active_agent_name = new_agent

        agent = self.agent

        # 매수 점수 계산
        buy_score = agent.calculate_buy_score(
            fgi=fgi["value"],
            rsi=indicators["rsi_14"],
            sma_deviation=indicators["sma_deviation_pct"],
            news_negative=external["_news_negative"],
            external_bonus=external["_external_bonus"],
            macd_golden_cross=indicators["macd"]["golden_cross"],
        )

        # 매매 결정
        decision = "관망"
        confidence = 0.5
        reason_parts = []
        trade_amount = 0
        trade_volume = 0.0

        # 매도 조건 체크 (보유 중일 때)
        if self.btc > 0:
            pnl_pct = ((price / self.avg_buy_price) - 1) * 100
            # 이익실현
            if pnl_pct >= agent.target_profit_pct:
                decision = "매도"
                confidence = 0.85
                reason_parts.append(f"목표수익 달성 ({pnl_pct:.1f}% >= {agent.target_profit_pct}%)")
            # 강제 손절
            elif pnl_pct <= agent.forced_stop_loss_pct:
                decision = "매도"
                confidence = 0.95
                reason_parts.append(f"강제손절 ({pnl_pct:.1f}% <= {agent.forced_stop_loss_pct}%)")
            # 손절
            elif pnl_pct <= agent.stop_loss_pct and danger >= 50:
                decision = "매도"
                confidence = 0.75
                reason_parts.append(f"손절 ({pnl_pct:.1f}%, danger={danger})")
            # 과매수 + 탐욕
            elif indicators["rsi_14"] >= agent.sell_rsi_threshold and fgi["value"] >= agent.sell_fgi_threshold:
                decision = "매도"
                confidence = 0.70
                reason_parts.append(f"과매수+탐욕 (RSI={indicators['rsi_14']:.0f}, FGI={fgi['value']})")

            if decision == "매도":
                trade_volume = self.btc  # 전량 매도
                trade_amount = int(trade_volume * price)

        # 매수 조건 체크
        if decision == "관망" and buy_score["result"] == "buy":
            available = min(self.krw * agent.max_trade_ratio, MAX_TRADE_AMOUNT)
            if available >= 5000:
                decision = "매수"
                confidence = min(0.5 + buy_score["total"] / 200, 0.95)
                trade_amount = int(available)
                trade_volume = trade_amount / price
                reason_parts.append(
                    f"매수점수 {buy_score['total']}점 (임계값 {agent.buy_score_threshold})"
                )

        if decision == "관망":
            reason_parts.append(
                f"매수점수 {buy_score['total']}/{agent.buy_score_threshold}, "
                f"danger={danger}, opportunity={opportunity}"
            )

        reason = f"[{agent.emoji}{agent.name}] " + " | ".join(reason_parts)

        # 매매 실행 (시뮬레이션)
        executed = False
        if decision == "매수" and trade_amount > 0:
            cost = trade_amount
            vol = cost / price
            # 평균매수가 갱신
            total_cost = self.avg_buy_price * self.btc + cost
            self.btc += vol
            self.avg_buy_price = total_cost / self.btc if self.btc > 0 else 0
            self.krw -= cost
            executed = True
            self.total_trades += 1

        elif decision == "매도" and trade_volume > 0:
            revenue = trade_volume * price
            pnl = revenue - (trade_volume * self.avg_buy_price)
            if pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
            self.btc = 0
            self.avg_buy_price = 0
            self.krw += revenue
            executed = True
            self.total_trades += 1

        return {
            "timestamp": dt.isoformat(),
            "decision": decision,
            "confidence": round(confidence, 2),
            "reason": reason,
            "current_price": int(price),
            "trade_amount": trade_amount,
            "trade_volume": round(trade_volume, 8),
            "executed": executed,
            "fear_greed_value": fgi["value"],
            "rsi_value": round(indicators["rsi_14"], 2),
            "sma20_price": indicators["sma_20"],
            "market_state": market_state,
            "buy_score": buy_score,
            "external_data": external,
            "portfolio_after": self.get_portfolio(price),
            "agent_name": f"{agent.emoji} {agent.name}",
            "switch": switch_info,
            "indicators": indicators,
        }

    def _classify_phase(self, fgi: int) -> str:
        if fgi <= 20:
            return "extreme_fear"
        elif fgi <= 35:
            return "fear"
        elif fgi <= 60:
            return "neutral"
        elif fgi <= 80:
            return "greed"
        return "extreme_greed"


# =====================================================
#  Phase 5: 임베딩 생성
# =====================================================

def build_embedding_text(result: dict) -> str:
    """임베딩용 텍스트 구성. 시장 상태 + 결정 + 근거를 자연어로."""
    ms = result["market_state"]
    ext = result["external_data"]["sources"]

    text = (
        f"일시: {result['timestamp']} | "
        f"BTC 가격: {result['current_price']:,}원 | "
        f"24h 변화: {ms['price_change_24h']:.1f}% | "
        f"RSI: {ms['rsi']:.1f} | FGI: {ms['fgi']} ({ms['phase']}) | "
        f"위험도: {ms['danger_score']} | 기회: {ms['opportunity_score']} | "
        f"뉴스감성: {ms['news_sentiment']} | "
        f"고래동향: {ext['whale_tracking']['activity']} (순유입 {ext['whale_tracking']['net_flow_btc']:.0f} BTC) | "
        f"김치프리미엄: {ms['kimchi_pct']:.1f}% | 롱숏비: {ms['ls_ratio']:.2f} | "
        f"펀딩비: {ms['funding_rate']:.4f} | "
        f"매크로: {ms['macro_sentiment']} (점수 {ms['macro_score']:.0f}) | "
        f"SNS감성: {ext['social_sentiment']['score']:.2f} | "
        f"퓨전시그널: {ms['fusion_signal']} ({ms['fusion_score']}) | "
        f"에이전트: {result['agent_name']} | "
        f"결정: {result['decision']} (확신도 {result['confidence']:.0%}) | "
        f"근거: {result['reason']} | "
        f"매매금액: {result['trade_amount']:,}원 | "
        f"포트폴리오: KRW {result['portfolio_after']['total_krw']:,.0f}, "
        f"평가액 {result['portfolio_after']['total_eval']:,.0f}"
    )
    return text


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Gemini embedding-001로 배치 임베딩 생성."""
    embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        for text in batch:
            try:
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=text,
                )
                embeddings.append(result["embedding"])
            except Exception as e:
                print(f"  ⚠ 임베딩 실패: {e}")
                embeddings.append(None)
            time.sleep(0.3)  # rate limit
        if i + BATCH_SIZE < len(texts):
            time.sleep(1.0)  # 배치 간 대기
    return embeddings


# =====================================================
#  Phase 6: Supabase 기록
# =====================================================

def save_to_supabase(results: list[dict], embeddings: list, embedding_texts: list[str]):
    """시뮬레이션 결과를 Supabase에 기록."""
    print("[6/6] Supabase에 기록 중...")
    decision_ids = []

    for i, (result, emb, emb_text) in enumerate(zip(results, embeddings, embedding_texts)):
        try:
            # 1) decisions 테이블
            decision_row = {
                "market": "KRW-BTC",
                "decision": result["decision"],
                "confidence": result["confidence"],
                "reason": result["reason"],
                "market_data_snapshot": json.dumps({
                    "indicators": result["indicators"],
                    "buy_score": result["buy_score"],
                }, ensure_ascii=False),
                "fear_greed_value": result["fear_greed_value"],
                "rsi_value": result["rsi_value"],
                "current_price": result["current_price"],
                "sma20_price": result["indicators"]["sma_20"],
                "trade_amount": result["trade_amount"],
                "trade_volume": result["trade_volume"],
                "executed": result["executed"],
                "profit_loss": round(
                    result["portfolio_after"]["total_eval"] - INITIAL_KRW, 2
                ),
                "created_at": result["timestamp"],
                "source": "backtest_jan2026",
                "cycle_id": f"bt_jan2026_{i:03d}",
                "embedding_text": emb_text,
            }

            # 임베딩 추가
            if emb:
                decision_row["state_embedding"] = emb

            resp = sb.table("decisions").insert(decision_row).execute()
            dec_id = resp.data[0]["id"] if resp.data else None
            decision_ids.append(dec_id)

            # 2) rag_analysis_vectors 테이블
            if emb and dec_id:
                rag_row = {
                    "cycle_id": f"bt_jan2026_{i:03d}",
                    "decision_id": dec_id,
                    "analysis_text": emb_text,
                    "analysis_json": {
                        "market_state": result["market_state"],
                        "decision": result["decision"],
                        "confidence": result["confidence"],
                        "agent": result["agent_name"],
                        "portfolio": result["portfolio_after"],
                        "switch": result["switch"],
                    },
                    "market_regime": result["market_state"]["phase"],
                    "embedding": emb,
                    "gemini_model": "gemini-embedding-001",
                    "created_at": result["timestamp"],
                }
                sb.table("rag_analysis_vectors").insert(rag_row).execute()

            # 3) market_data 테이블
            market_row = {
                "market": "KRW-BTC",
                "price": result["current_price"],
                "volume_24h": result["indicators"]["volume"],
                "change_rate_24h": result["indicators"]["price_change_24h"] / 100,
                "fear_greed_value": result["fear_greed_value"],
                "fear_greed_class": result["market_state"]["phase"],
                "rsi_14": result["rsi_value"],
                "sma_20": result["indicators"]["sma_20"],
                "news_sentiment": result["market_state"]["news_sentiment"],
                "created_at": result["timestamp"],
            }
            sb.table("market_data").insert(market_row).execute()

            # 4) portfolio_snapshots
            pf = result["portfolio_after"]
            btc_eval = pf["holdings"][0]["eval_amount"] if pf["holdings"] else 0
            snap_row = {
                "total_krw": int(pf["total_krw"]),
                "total_crypto_value": int(btc_eval),
                "total_value": int(pf["total_eval"]),
                "holdings": json.dumps(pf["holdings"], ensure_ascii=False),
                "cumulative_return": round(
                    (pf["total_eval"] / INITIAL_KRW - 1) * 100, 4
                ),
                "created_at": result["timestamp"],
            }
            sb.table("portfolio_snapshots").insert(snap_row).execute()

            if (i + 1) % 10 == 0:
                print(f"  → {i + 1}/{len(results)} 기록 완료")

        except Exception as e:
            print(f"  ⚠ 기록 실패 (#{i}): {e}")
            decision_ids.append(None)

    return decision_ids


# =====================================================
#  Phase 7: 성과 메트릭 (outcome 업데이트)
# =====================================================

def update_outcomes(results: list[dict], decision_ids: list):
    """각 결정의 1h/4h/24h 후 가격으로 outcome 업데이트."""
    print("  → outcome 업데이트 중...")
    # prices/timestamps dictionaries built but unused

    for i, (result, dec_id) in enumerate(zip(results, decision_ids)):
        if not dec_id:
            continue

        price_now = result["current_price"]
        outcome = {}

        # 1h 후 (가장 가까운 다음 시점)
        if i + 1 < len(results):
            p1h = results[i + 1]["current_price"]
            outcome["outcome_1h_pct"] = round((p1h / price_now - 1) * 100, 4)

        # 4h 후
        if i + 1 < len(results):
            p4h = results[i + 1]["current_price"]
            outcome["outcome_4h_pct"] = round((p4h / price_now - 1) * 100, 4)

        # 24h 후 (6 스텝)
        if i + 6 < len(results):
            p24h = results[i + 6]["current_price"]
            outcome["outcome_24h_pct"] = round((p24h / price_now - 1) * 100, 4)
            # was_correct_24h: 매수→가격상승, 매도→가격하락, 관망→변동적음
            if result["decision"] == "매수":
                outcome["was_correct_24h"] = p24h > price_now
            elif result["decision"] == "매도":
                outcome["was_correct_24h"] = p24h < price_now
            else:
                outcome["was_correct_24h"] = abs(p24h / price_now - 1) < 0.02

        if outcome:
            try:
                sb.table("decisions").update(outcome).eq("id", dec_id).execute()
            except Exception as e:
                print(f"  ⚠ outcome 업데이트 실패 (#{i}): {e}")


# =====================================================
#  Main
# =====================================================

def main():
    print("=" * 60)
    print("  2026년 1월 백테스트 시뮬레이션")
    print(f"  기간: {SIM_START.strftime('%Y-%m-%d %H:%M')} ~ {SIM_END.strftime('%Y-%m-%d %H:%M')}")
    print(f"  초기 자금: {INITIAL_KRW:,}원")
    print(f"  간격: {INTERVAL_HOURS}시간")
    print("=" * 60)

    # Phase 1: 캔들 수집
    candles = collect_all_candles()

    # Phase 2: FGI 수집
    fgi_map = fetch_historical_fgi()

    # 시뮬레이션 대상 캔들 필터 (1월 1일 ~ 1월 31일)
    # Upbit 4시간봉은 1,5,9,13,17,21시 시작
    UPBIT_4H_HOURS = {1, 5, 9, 13, 17, 21}
    sim_candles = []
    for c in candles:
        dt = c["_dt_kst"]
        if SIM_START <= dt < SIM_END and dt.hour in UPBIT_4H_HOURS:
            sim_candles.append(c)

    print(f"\n[3/6] 매매 시뮬레이션 시작 ({len(sim_candles)}개 시점)...")

    # Phase 3-4: 시뮬레이션 실행
    simulator = TradingSimulator(INITIAL_KRW)
    results = []
    prev_externals = []

    for sc in sim_candles:
        dt = sc["_dt_kst"]
        # 해당 캔들의 인덱스 찾기
        idx = candles.index(sc)
        indicators = compute_indicators(candles, idx)
        fgi = get_fgi_for_date(fgi_map, dt)
        external = simulate_external_data(dt, indicators, fgi, prev_externals)

        result = simulator.simulate_step(dt, indicators, fgi, external)
        results.append(result)
        prev_externals.append(external)

        symbol = {"매수": "🟢", "매도": "🔴", "관망": "⚪"}.get(result["decision"], "?")
        print(
            f"  {dt.strftime('%m/%d %H:%M')} {symbol} {result['decision']:2s} | "
            f"BTC={result['current_price']:>12,} | "
            f"RSI={result['rsi_value']:5.1f} FGI={result['fear_greed_value']:2d} | "
            f"D={result['market_state']['danger_score']:2d} O={result['market_state']['opportunity_score']:2d} | "
            f"{result['agent_name']}"
        )

    # 성과 요약
    final_portfolio = simulator.get_portfolio(results[-1]["current_price"])
    pnl = final_portfolio["total_eval"] - INITIAL_KRW
    pnl_pct = (pnl / INITIAL_KRW) * 100
    trades = [r for r in results if r["decision"] != "관망"]

    print(f"\n{'=' * 60}")
    print("  시뮬레이션 완료")
    print(f"  초기: {INITIAL_KRW:>12,}원")
    print(f"  최종: {final_portfolio['total_eval']:>12,.0f}원")
    print(f"  수익: {pnl:>+12,.0f}원 ({pnl_pct:+.2f}%)")
    print(f"  총 매매: {len(trades)}건")
    print(f"{'=' * 60}")

    # Phase 5: 임베딩 생성
    print(f"\n[4/6] Gemini 임베딩 생성 중 ({len(results)}건)...")
    embedding_texts = [build_embedding_text(r) for r in results]
    embeddings = generate_embeddings(embedding_texts)
    valid_count = sum(1 for e in embeddings if e is not None)
    print(f"  → {valid_count}/{len(results)}건 임베딩 생성 완료")

    # Phase 6: DB 기록
    decision_ids = save_to_supabase(results, embeddings, embedding_texts)

    # Phase 7: Outcome 업데이트
    update_outcomes(results, decision_ids)

    print(f"\n✅ 전체 완료! {len(results)}건 시뮬레이션 → DB 기록 + 벡터 임베딩")
    print(f"  - decisions: {sum(1 for d in decision_ids if d)}건")
    print(f"  - rag_analysis_vectors: {valid_count}건")
    print(f"  - market_data: {len(results)}건")
    print(f"  - portfolio_snapshots: {len(results)}건")

    # 결과 로컬 저장
    output_path = PROJECT_DIR / "data" / "backtest_jan2026_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        # 임베딩 제외하고 저장 (용량)
        save_results = []
        for r in results:
            sr = {k: v for k, v in r.items()}
            sr.pop("external_data", None)  # 큰 데이터 제외
            save_results.append(sr)
        json.dump(save_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"  → 로컬: {output_path}")


if __name__ == "__main__":
    main()
