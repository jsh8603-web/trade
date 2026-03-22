#!/usr/bin/env python3
"""
v2 vs v3 비교 백테스트 시뮬레이션

동일한 Upbit 히스토리컬 캔들 + FGI + 외부 데이터(시뮬)에서
v2(기존)와 v3(매크로+집중방지+선제매도)를 동시에 돌려 비교한다.

기간: 2024-01-01 ~ 2026-03-22
초기 자금: 500만원 / 1회 매매 상한: 10만원
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
load_dotenv(PROJECT_DIR / ".env")

from agents.conservative import ConservativeAgent
from agents.moderate import ModerateAgent
from agents.aggressive import AggressiveAgent

KST = timezone(timedelta(hours=9))
UTC = timezone.utc

# ── 설정 ──────────────────────────────────────────────
SIM_START = datetime(2024, 1, 1, 0, 0, tzinfo=KST)
SIM_END   = datetime(2026, 3, 22, 0, 0, tzinfo=KST)
INTERVAL_HOURS = 4
INITIAL_KRW = 5_000_000
MAX_TRADE_AMOUNT = 100_000
random.seed(2025_01)  # 재현성


# =====================================================
#  Phase 1: Upbit 히스토리컬 캔들 수집
# =====================================================

def fetch_upbit_candles_4h(to_dt: datetime, count: int = 200) -> list[dict]:
    url = "https://api.upbit.com/v1/candles/minutes/240"
    to_str = to_dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")
    params = {"market": "KRW-BTC", "to": to_str, "count": min(count, 200)}
    for retry in range(3):
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 2 * (retry + 1)))
                print(f"  ! 429 Rate Limit — {wait}초 대기 (재시도 {retry+1}/3)")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            candles = resp.json()
            candles.sort(key=lambda c: c["candle_date_time_kst"])
            return candles
        except Exception as e:
            if retry < 2:
                time.sleep(2 * (retry + 1))
            else:
                print(f"  ! 캔들 수집 실패: {e}")
                return []


def collect_all_candles() -> list[dict]:
    """2024-12-15 ~ 2026-03-22 전체 4시간봉 수집."""
    all_candles = []
    cursor = SIM_END + timedelta(hours=4)
    target_start = datetime(2023, 12, 15, 0, 0, tzinfo=KST)

    print("[1/4] Upbit 4시간봉 캔들 수집 중 (27개월+선행)...")
    batch_count = 0
    while True:
        batch = fetch_upbit_candles_4h(cursor, 200)
        if not batch:
            break
        all_candles = batch + all_candles
        batch_count += 1
        oldest = datetime.fromisoformat(batch[0]["candle_date_time_kst"])
        if oldest.tzinfo is None:
            oldest = oldest.replace(tzinfo=KST)
        if oldest <= target_start:
            break
        cursor = oldest
        time.sleep(0.15)
        if batch_count % 10 == 0:
            print(f"  ... {len(all_candles)}개 수집됨, oldest={oldest.strftime('%Y-%m-%d')}")

    # 기간 필터
    filtered = []
    for c in all_candles:
        dt = datetime.fromisoformat(c["candle_date_time_kst"])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        if target_start <= dt <= SIM_END:
            c["_dt_kst"] = dt
            filtered.append(c)

    print(f"  -> {len(filtered)}개 캔들 수집 완료")
    return filtered


# ── 기술 지표 ────────────────────────────────────────

def calc_rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    recent = deltas[-period:]
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
    # Compute MACD line for enough history to get a 9-period EMA of it
    if len(closes) >= 26:
        macd_history = []
        for i in range(25, len(closes)):
            e12 = ema(closes[:i+1], 12)
            e26 = ema(closes[:i+1], 26)
            macd_history.append(e12 - e26)
        macd_line = macd_history[-1]
        signal = ema(macd_history, 9) if len(macd_history) >= 9 else macd_history[-1]
    else:
        ema12 = ema(closes, 12)
        ema26 = ema(closes, 26) if len(closes) >= 26 else (closes[-1] if closes else 0)
        macd_line = ema12 - ema26
        signal = macd_line
    return {"macd": round(macd_line, 2), "signal": round(signal, 2), "golden_cross": macd_line > signal}


def compute_indicators(candles: list[dict], idx: int) -> dict:
    closes = [c["trade_price"] for c in candles[:idx + 1]]
    rsi = calc_rsi(closes)
    sma20 = calc_sma(closes)
    macd = calc_macd(closes)
    price = closes[-1]
    sma_deviation = ((price - sma20) / sma20 * 100) if sma20 else 0
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
        "price_change_24h": round(change_24h, 2),
        "volume": candles[idx].get("candle_acc_trade_volume", 0),
    }


# =====================================================
#  Phase 2: 히스토리컬 FGI
# =====================================================

def fetch_historical_fgi() -> dict[str, dict]:
    print("[2/4] 히스토리컬 FGI 수집 중...")
    url = "https://api.alternative.me/fng/"
    params = {"limit": 0, "format": "json"}  # limit=0 → 전체
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception as e:
        print(f"  ! FGI 수집 실패: {e}, 더미 데이터 사용")
        return {}

    fgi_map = {}
    for item in data:
        ts = int(item["timestamp"])
        dt = datetime.fromtimestamp(ts, tz=UTC)
        date_str = dt.strftime("%Y-%m-%d")
        fgi_map[date_str] = {"value": int(item["value"]), "classification": item["value_classification"]}

    print(f"  -> {len(fgi_map)}일 FGI 수집 완료")
    return fgi_map


def get_fgi_for_date(fgi_map: dict, dt: datetime) -> dict:
    date_str = dt.strftime("%Y-%m-%d")
    if date_str in fgi_map:
        return fgi_map[date_str]
    for delta in range(1, 7):
        prev = (dt - timedelta(days=delta)).strftime("%Y-%m-%d")
        if prev in fgi_map:
            return fgi_map[prev]
    return {"value": 50, "classification": "Neutral"}


# =====================================================
#  Phase 3: 외부 데이터 시뮬레이션 (backtest_2025h1과 동일)
# =====================================================

def simulate_external_data(dt: datetime, indicators: dict, fgi: dict) -> dict:
    price = indicators["current_price"]
    rsi = indicators["rsi_14"]
    change_24h = indicators["price_change_24h"]
    fgi_val = fgi["value"]

    # 뉴스 감성
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
    if fgi_val < 25:
        news_score -= random.uniform(0.1, 0.3)
    elif fgi_val > 75:
        news_score += random.uniform(0.1, 0.3)
    news_score = max(-1.0, min(1.0, news_score))
    if news_score < -0.3:
        news_sentiment = "negative"
    elif news_score > 0.3:
        news_sentiment = "positive"
    else:
        news_sentiment = "neutral"

    # 김치/롱숏/펀딩
    kimchi_pct = round((fgi_val - 50) * 0.04 + random.uniform(-1.0, 1.0), 2)
    ls_ratio = round(max(0.5, min(2.0, 1.0 + change_24h * 0.03 + random.uniform(-0.15, 0.15))), 2)
    funding_rate = round((ls_ratio - 1.0) * 0.01 + random.uniform(-0.005, 0.005), 5)

    # 매크로
    macro_base = random.uniform(-15, 15)
    if dt.day <= 10:
        macro_base += random.uniform(0, 10)
    elif dt.day >= 20:
        macro_base += random.uniform(-10, 5)
    macro_score = round(max(-30, min(30, macro_base)), 1)

    # Data Fusion
    fusion_score = int(news_score * 10) + int(macro_score * 0.3)
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
            "news_sentiment": {"overall_sentiment": news_sentiment, "score": round(news_score, 2)},
            "binance_sentiment": {
                "kimchi_premium": {"premium_pct": kimchi_pct},
                "top_trader_long_short": {"current_ratio": ls_ratio},
                "funding_rate": {"current_rate": funding_rate},
            },
            "macro": {"analysis": {"macro_score": macro_score, "sentiment": "neutral"}},
        },
        "_external_bonus": external_bonus,
        "_news_negative": news_sentiment == "negative",
        "_fgi_value": fgi_val,
        "_macro_score": macro_score,
    }


# =====================================================
#  Phase 4: 시뮬레이터 (v2와 v3 동시 실행)
# =====================================================

class TradingSimulator:
    """단일 시뮬레이터. version='v2' 또는 'v3'."""

    def __init__(self, initial_krw: int, version: str):
        self.version = version
        self.krw = float(initial_krw)
        self.btc = 0.0
        self.avg_buy_price = 0.0
        self.active_agent_name = "conservative"
        self.consecutive_losses = 0
        self.consecutive_buys = 0
        self.total_trades = 0
        self.total_buys = 0
        self.total_sells = 0
        self.total_holds = 0
        self.win_trades = 0
        self.loss_trades = 0
        self.peak_eval = float(initial_krw)
        self.max_drawdown = 0.0
        self.monthly_stats: dict[str, dict] = {}
        self.agents = {
            "conservative": ConservativeAgent(),
            "moderate": ModerateAgent(),
            "aggressive": AggressiveAgent(),
        }

    @property
    def agent(self):
        return self.agents[self.active_agent_name]

    def get_portfolio(self, price: float) -> dict:
        btc_eval = self.btc * price
        total = self.krw + btc_eval
        btc_ratio = btc_eval / total if total > 0 else 0
        pnl = ((price / self.avg_buy_price) - 1) * 100 if self.avg_buy_price > 0 and self.btc > 0 else 0
        return {
            "total_krw": self.krw, "total_eval": total, "btc_ratio": round(btc_ratio, 4),
            "btc": {"balance": self.btc, "avg_buy_price": self.avg_buy_price, "profit_pct": round(pnl, 2), "eval_amount": btc_eval},
            "krw_balance": self.krw,
        }

    def evaluate_switch(self, danger: int, opportunity: int) -> str | None:
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
        if danger < 25 and opportunity < 25 and current != "moderate":
            return "moderate"
        return None

    def calc_danger(self, indicators: dict, ext: dict, portfolio: dict) -> int:
        score = 0
        fgi_val = ext["_fgi_value"]
        change_24h = indicators["price_change_24h"]
        bs = ext["sources"]["binance_sentiment"]
        kimchi_pct = bs["kimchi_premium"]["premium_pct"]
        ls_ratio = bs["top_trader_long_short"]["current_ratio"]
        macro_score = ext["_macro_score"]

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
        news_s = ext["sources"]["news_sentiment"]["overall_sentiment"]
        if news_s == "negative":
            score += 10
        return min(score, 100)

    def calc_opportunity(self, indicators: dict, ext: dict) -> int:
        score = 0
        fgi_val = ext["_fgi_value"]
        rsi = indicators["rsi_14"]
        change_24h = indicators["price_change_24h"]
        fusion = ext["external_signal"]["fusion"]
        bs = ext["sources"]["binance_sentiment"]
        funding_rate = bs["funding_rate"]["current_rate"]
        kimchi_pct = bs["kimchi_premium"]["premium_pct"]
        macro_score = ext["_macro_score"]

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
        return min(score, 100)

    def step(self, dt: datetime, indicators: dict, fgi: dict, ext: dict) -> dict:
        price = indicators["current_price"]
        portfolio = self.get_portfolio(price)
        macro_score = ext["_macro_score"]

        danger = self.calc_danger(indicators, ext, portfolio)
        opportunity = self.calc_opportunity(indicators, ext)

        new_agent = self.evaluate_switch(danger, opportunity)
        switch_info = None
        if new_agent and new_agent != self.active_agent_name:
            switch_info = {"from": self.active_agent_name, "to": new_agent}
            self.active_agent_name = new_agent

        agent = self.agent

        # ── 매수 점수 계산 ──
        if self.version == "v3":
            buy_score = agent.calculate_buy_score(
                fgi=fgi["value"], rsi=indicators["rsi_14"],
                sma_deviation=indicators["sma_deviation_pct"],
                news_negative=ext["_news_negative"],
                external_bonus=ext["_external_bonus"],
                macd_golden_cross=indicators["macd"]["golden_cross"],
                macro_score=macro_score,
                consecutive_buy_count=self.consecutive_buys,
            )
        else:
            # v2: 기존 코드 (매크로/집중 감점 없음)
            buy_score = agent.calculate_buy_score(
                fgi=fgi["value"], rsi=indicators["rsi_14"],
                sma_deviation=indicators["sma_deviation_pct"],
                news_negative=ext["_news_negative"],
                external_bonus=ext["_external_bonus"],
                macd_golden_cross=indicators["macd"]["golden_cross"],
            )

        decision = "hold"
        reason = ""
        trade_amount = 0
        trade_volume = 0.0

        # ── 매도 조건 (보유 시) ──
        if self.btc > 0:
            pnl_pct = ((price / self.avg_buy_price) - 1) * 100

            # v3: 매도 로직은 v2와 동일 (백테스트에서 추가 매도 트리거는 역효과 확인)
            # v3 차이점은 매수 필터(매크로+집중방지)에만 있음

            # 공통 매도 조건 (v2/v3 모두)
            if decision == "hold":
                if pnl_pct >= agent.target_profit_pct:
                    decision = "sell"
                    reason = f"목표수익 {pnl_pct:.1f}% >= {agent.target_profit_pct}%"
                elif pnl_pct <= agent.forced_stop_loss_pct:
                    decision = "sell"
                    reason = f"강제손절 {pnl_pct:.1f}%"
                elif pnl_pct <= agent.stop_loss_pct and danger >= 50:
                    decision = "sell"
                    reason = f"손절 {pnl_pct:.1f}%, danger={danger}"
                elif indicators["rsi_14"] >= agent.sell_rsi_threshold and fgi["value"] >= agent.sell_fgi_threshold:
                    decision = "sell"
                    reason = f"과매수+탐욕 RSI={indicators['rsi_14']:.0f}, FGI={fgi['value']}"

            if decision == "sell":
                trade_volume = self.btc
                trade_amount = int(trade_volume * price)

        # ── 매수 조건 ──
        if decision == "hold" and buy_score["result"] == "buy":
            available = min(self.krw * agent.max_trade_ratio, MAX_TRADE_AMOUNT)
            if available >= 5000:
                decision = "buy"
                trade_amount = int(available)
                trade_volume = trade_amount / price
                reason = f"매수점수 {buy_score['total']}점 >= {agent.buy_score_threshold}"

        if decision == "hold":
            reason = f"점수 {buy_score['total']}/{agent.buy_score_threshold}, D={danger}, O={opportunity}"

        # ── 실행 ──
        month_key = dt.strftime("%Y-%m")
        if month_key not in self.monthly_stats:
            self.monthly_stats[month_key] = {"buys": 0, "sells": 0, "holds": 0, "pnl": 0.0}
        ms = self.monthly_stats[month_key]

        pnl_realized = 0.0
        if decision == "buy" and trade_amount > 0:
            fee = trade_amount * 0.0005  # 0.05% trading fee
            total_cost = self.avg_buy_price * self.btc + trade_amount
            self.btc += trade_volume
            self.avg_buy_price = total_cost / self.btc if self.btc > 0 else 0
            self.krw -= (trade_amount + fee)
            self.total_trades += 1
            self.total_buys += 1
            self.consecutive_buys += 1
            ms["buys"] += 1
        elif decision == "sell" and trade_volume > 0:
            revenue = trade_volume * price
            fee = revenue * 0.0005  # 0.05% trading fee
            revenue -= fee
            pnl_realized = revenue - (trade_volume * self.avg_buy_price)
            if pnl_realized < 0:
                self.consecutive_losses += 1
                self.loss_trades += 1
            else:
                self.consecutive_losses = 0
                self.win_trades += 1
            self.btc = 0
            self.avg_buy_price = 0
            self.krw += revenue
            self.total_trades += 1
            self.total_sells += 1
            self.consecutive_buys = 0
            ms["sells"] += 1
            ms["pnl"] += pnl_realized
        else:
            self.total_holds += 1
            ms["holds"] += 1

        # drawdown 추적
        current_eval = self.krw + self.btc * price
        if current_eval > self.peak_eval:
            self.peak_eval = current_eval
        dd = (self.peak_eval - current_eval) / self.peak_eval * 100
        if dd > self.max_drawdown:
            self.max_drawdown = dd

        return {
            "dt": dt.isoformat(),
            "decision": decision,
            "reason": reason,
            "price": int(price),
            "trade_amount": trade_amount,
            "pnl_realized": round(pnl_realized),
            "agent": agent.name,
            "switch": switch_info,
            "buy_score_total": buy_score.get("total", 0),
            "fgi": fgi["value"],
            "rsi": round(indicators["rsi_14"], 1),
            "macro_score": round(macro_score, 1),
            "danger": danger,
            "opportunity": opportunity,
            "portfolio_eval": round(self.krw + self.btc * price),
        }


# =====================================================
#  메인 실행
# =====================================================

def main():
    candles = collect_all_candles()
    if not candles:
        print("캔들 수집 실패!")
        return

    fgi_map = fetch_historical_fgi()

    # 시뮬레이션 시점 필터 (SIM_START 이후, INTERVAL_HOURS 간격)
    sim_indices = []
    seen_times = set()
    for i, c in enumerate(candles):
        dt = c["_dt_kst"]
        if dt >= SIM_START:
            # 4시간봉: Upbit은 01, 05, 09, 13, 17, 21시 기준
            dt_key = dt.strftime("%Y-%m-%d %H")
            if dt_key not in seen_times:
                seen_times.add(dt_key)
                sim_indices.append(i)

    print(f"\n[3/4] 시뮬레이션 시점: {len(sim_indices)}개")
    if not sim_indices:
        print("  ! SIM_START 이후 캔들 없음 — 시뮬레이션 불가")
        return
    print(f"  기간: {candles[sim_indices[0]]['_dt_kst'].strftime('%Y-%m-%d')} ~ "
          f"{candles[sim_indices[-1]]['_dt_kst'].strftime('%Y-%m-%d')}")

    # v2 / v3 동시 시뮬레이션
    sim_v2 = TradingSimulator(INITIAL_KRW, "v2")
    sim_v3 = TradingSimulator(INITIAL_KRW, "v3")

    results_v2 = []
    results_v3 = []

    print(f"\n[4/4] v2 vs v3 비교 시뮬레이션 실행 중...")

    prev_externals_for_seed = []
    for step_i, idx in enumerate(sim_indices):
        dt = candles[idx]["_dt_kst"]
        indicators = compute_indicators(candles, idx)
        fgi = get_fgi_for_date(fgi_map, dt)

        # 동일한 시드 기반 외부 데이터 (v2/v3 동일 조건)
        state = random.getstate()
        ext_v2 = simulate_external_data(dt, indicators, fgi)
        random.setstate(state)
        ext_v3 = simulate_external_data(dt, indicators, fgi)

        r_v2 = sim_v2.step(dt, indicators, fgi, ext_v2)
        r_v3 = sim_v3.step(dt, indicators, fgi, ext_v3)

        results_v2.append(r_v2)
        results_v3.append(r_v3)

        if (step_i + 1) % 500 == 0:
            print(f"  ... {step_i + 1}/{len(sim_indices)} 완료 "
                  f"(v2: {sim_v2.get_portfolio(indicators['current_price'])['total_eval']:,.0f}원, "
                  f"v3: {sim_v3.get_portfolio(indicators['current_price'])['total_eval']:,.0f}원)")

    # 최종 가격
    final_price = candles[sim_indices[-1]]["trade_price"]

    # ── 보고서 생성 ──
    print("\n" + "=" * 70)
    print("  v2 vs v3 비교 백테스트 결과 보고서")
    print("=" * 70)

    report_lines = []

    def p(line=""):
        print(line)
        report_lines.append(line)

    p(f"\n기간: {SIM_START.strftime('%Y-%m-%d')} ~ {SIM_END.strftime('%Y-%m-%d')}")
    p(f"시뮬레이션 시점: {len(sim_indices)}개 (4시간 간격)")
    p(f"초기 자금: {INITIAL_KRW:,}원 / 1회 상한: {MAX_TRADE_AMOUNT:,}원")

    for label, sim, results in [("v2 (기존)", sim_v2, results_v2), ("v3 (개선)", sim_v3, results_v3)]:
        port = sim.get_portfolio(final_price)
        total_eval = port["total_eval"]
        roi = (total_eval - INITIAL_KRW) / INITIAL_KRW * 100
        win_rate = (sim.win_trades / (sim.win_trades + sim.loss_trades) * 100) if (sim.win_trades + sim.loss_trades) > 0 else 0

        p(f"\n{'─' * 35}")
        p(f"  [{label}]")
        p(f"{'─' * 35}")
        p(f"  최종 평가액:     {total_eval:>14,.0f}원")
        p(f"  수익률 (ROI):    {roi:>13.2f}%")
        p(f"  최대 낙폭 (MDD): {sim.max_drawdown:>13.2f}%")
        p(f"  총 거래 횟수:    {sim.total_trades:>9}회")
        p(f"    매수:          {sim.total_buys:>9}회")
        p(f"    매도:          {sim.total_sells:>9}회")
        p(f"    관망:          {sim.total_holds:>9}회")
        p(f"  매수 비율:       {sim.total_buys / len(results) * 100:>12.1f}%")
        p(f"  매도 비율:       {sim.total_sells / len(results) * 100:>12.1f}%")
        p(f"  승률:            {win_rate:>12.1f}%")

    # 차이 비교
    eval_v2 = sim_v2.get_portfolio(final_price)["total_eval"]
    eval_v3 = sim_v3.get_portfolio(final_price)["total_eval"]
    roi_v2 = (eval_v2 - INITIAL_KRW) / INITIAL_KRW * 100
    roi_v3 = (eval_v3 - INITIAL_KRW) / INITIAL_KRW * 100

    p(f"\n{'=' * 35}")
    p(f"  [v3 개선 효과]")
    p(f"{'=' * 35}")
    p(f"  수익률 차이:     {roi_v3 - roi_v2:>+13.2f}%p")
    p(f"  평가액 차이:     {eval_v3 - eval_v2:>+14,.0f}원")
    p(f"  MDD 차이:        {sim_v3.max_drawdown - sim_v2.max_drawdown:>+13.2f}%p")
    p(f"  매수 횟수 차이:  {sim_v3.total_buys - sim_v2.total_buys:>+9}회")
    p(f"  매도 횟수 차이:  {sim_v3.total_sells - sim_v2.total_sells:>+9}회")

    # v3는 매수 필터만 다름 (매도 로직 동일)
    p(f"\n  v3 차이: 매수 필터(매크로+집중방지)만 적용, 매도 로직은 v2와 동일")

    # 의사결정 차이 분석
    diff_count = 0
    v2_buy_v3_hold = 0
    v2_hold_v3_sell = 0
    def norm_decision(d):
        return "sell" if d in ("sell", "sell_partial") else d
    for r2, r3 in zip(results_v2, results_v3):
        d2, d3 = norm_decision(r2["decision"]), norm_decision(r3["decision"])
        if d2 != d3:
            diff_count += 1
            if d2 == "buy" and d3 == "hold":
                v2_buy_v3_hold += 1
            elif d2 == "hold" and d3 == "sell":
                v2_hold_v3_sell += 1

    p(f"\n  의사결정 차이:   {diff_count:>9}회 ({diff_count/len(results_v2)*100:.1f}%)")
    p(f"    v2=매수, v3=관망: {v2_buy_v3_hold:>6}회 (과다매수 방지)")
    p(f"    v2=관망, v3=매도: {v2_hold_v3_sell:>6}회 (선제매도)")

    # 월별 비교
    p(f"\n{'=' * 70}")
    p(f"  월별 상세 비교")
    p(f"{'=' * 70}")
    p(f"  {'월':>8} | {'v2 매수':>7} {'v2 매도':>7} {'v2 PnL':>10} | {'v3 매수':>7} {'v3 매도':>7} {'v3 PnL':>10} | {'차이':>10}")
    p(f"  {'-'*8}-+-{'-'*27}-+-{'-'*27}-+-{'-'*10}")

    all_months = sorted(set(list(sim_v2.monthly_stats.keys()) + list(sim_v3.monthly_stats.keys())))
    for m in all_months:
        s2 = sim_v2.monthly_stats.get(m, {"buys": 0, "sells": 0, "pnl": 0})
        s3 = sim_v3.monthly_stats.get(m, {"buys": 0, "sells": 0, "pnl": 0})
        diff = s3["pnl"] - s2["pnl"]
        p(f"  {m:>8} | {s2['buys']:>5}회 {s2['sells']:>5}회 {s2['pnl']:>+10,.0f} | "
          f"{s3['buys']:>5}회 {s3['sells']:>5}회 {s3['pnl']:>+10,.0f} | {diff:>+10,.0f}")

    # BTC 보유 비교 (특정 시점)
    p(f"\n{'=' * 70}")
    p(f"  핵심 개선 포인트 분석")
    p(f"{'=' * 70}")

    # 매크로 부정 구간에서의 매수 차이
    macro_neg_v2_buys = sum(1 for r in results_v2 if r["decision"] == "buy" and r["macro_score"] <= -8)
    macro_neg_v3_buys = sum(1 for r in results_v3 if r["decision"] == "buy" and r["macro_score"] <= -8)
    macro_neg_total = sum(1 for r in results_v2 if r["macro_score"] <= -8)
    p(f"\n  1) 매크로 강한 부정(score<=-8) 구간: {macro_neg_total}회")
    p(f"     v2 매수: {macro_neg_v2_buys}회 ({macro_neg_v2_buys/max(macro_neg_total,1)*100:.1f}%)")
    p(f"     v3 매수: {macro_neg_v3_buys}회 ({macro_neg_v3_buys/max(macro_neg_total,1)*100:.1f}%)")
    p(f"     -> {macro_neg_v2_buys - macro_neg_v3_buys}회 과다매수 방지")

    # 공포 구간 연속 매수 차이
    fear_v2_buys = sum(1 for r in results_v2 if r["decision"] == "buy" and r["fgi"] <= 25)
    fear_v3_buys = sum(1 for r in results_v3 if r["decision"] == "buy" and r["fgi"] <= 25)
    fear_total = sum(1 for r in results_v2 if r["fgi"] <= 25)
    p(f"\n  2) 극공포(FGI<=25) 구간: {fear_total}회")
    p(f"     v2 매수: {fear_v2_buys}회 ({fear_v2_buys/max(fear_total,1)*100:.1f}%)")
    p(f"     v3 매수: {fear_v3_buys}회 ({fear_v3_buys/max(fear_total,1)*100:.1f}%)")
    p(f"     -> {fear_v2_buys - fear_v3_buys}회 집중 방지")

    # 과열 구간 매도 차이
    greed_v2_sells = sum(1 for r in results_v2 if r["decision"] == "sell" and r["fgi"] >= 60)
    greed_v3_sells = sum(1 for r in results_v3 if r["decision"] == "sell" and r["fgi"] >= 60)
    greed_total = sum(1 for r in results_v2 if r["fgi"] >= 60)
    p(f"\n  3) 탐욕(FGI>=60) 구간: {greed_total}회")
    p(f"     v2 매도: {greed_v2_sells}회")
    p(f"     v3 매도: {greed_v3_sells}회")
    p(f"     -> {greed_v3_sells - greed_v2_sells}회 추가 익절")

    p(f"\n{'=' * 70}")
    p(f"  결론")
    p(f"{'=' * 70}")
    if roi_v3 > roi_v2:
        p(f"\n  v3 개선이 수익률을 {roi_v3 - roi_v2:+.2f}%p 향상시켰습니다.")
    elif roi_v3 < roi_v2:
        p(f"\n  v3가 {roi_v2 - roi_v3:.2f}%p 수익률 하락. 추가 조정 필요.")
    else:
        p(f"\n  v2와 v3 수익률 동일. 리스크 관리 면에서 차이를 확인하세요.")

    if sim_v3.max_drawdown < sim_v2.max_drawdown:
        p(f"  MDD가 {sim_v2.max_drawdown - sim_v3.max_drawdown:.2f}%p 개선 (리스크 감소).")
    elif sim_v3.max_drawdown > sim_v2.max_drawdown:
        p(f"  MDD가 {sim_v3.max_drawdown - sim_v2.max_drawdown:.2f}%p 증가. 주의 필요.")

    p("")

    # 보고서 파일 저장
    report_path = PROJECT_DIR / "data" / "backtest_v3_compare_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\n보고서 저장: {report_path}")

    # JSON 결과 저장
    json_path = PROJECT_DIR / "data" / "backtest_v3_compare_results.json"
    summary = {
        "period": f"{SIM_START.strftime('%Y-%m-%d')} ~ {SIM_END.strftime('%Y-%m-%d')}",
        "sim_points": len(sim_indices),
        "v2": {
            "final_eval": round(eval_v2),
            "roi_pct": round(roi_v2, 2),
            "mdd_pct": round(sim_v2.max_drawdown, 2),
            "total_trades": sim_v2.total_trades,
            "buys": sim_v2.total_buys,
            "sells": sim_v2.total_sells,
            "holds": sim_v2.total_holds,
            "win_rate": round((sim_v2.win_trades / max(sim_v2.win_trades + sim_v2.loss_trades, 1)) * 100, 1),
            "monthly": sim_v2.monthly_stats,
        },
        "v3": {
            "final_eval": round(eval_v3),
            "roi_pct": round(roi_v3, 2),
            "mdd_pct": round(sim_v3.max_drawdown, 2),
            "total_trades": sim_v3.total_trades,
            "buys": sim_v3.total_buys,
            "sells": sim_v3.total_sells,
            "holds": sim_v3.total_holds,
            "win_rate": round((sim_v3.win_trades / max(sim_v3.win_trades + sim_v3.loss_trades, 1)) * 100, 1),
            "monthly": sim_v3.monthly_stats,
            "note": "v3 differs from v2 only in buy filters (macro+concentration)",
        },
        "diff": {
            "roi_diff": round(roi_v3 - roi_v2, 2),
            "eval_diff": round(eval_v3 - eval_v2),
            "mdd_diff": round(sim_v3.max_drawdown - sim_v2.max_drawdown, 2),
            "decision_diffs": diff_count,
            "v2_buy_v3_hold": v2_buy_v3_hold,
            "v2_hold_v3_sell": v2_hold_v3_sell,
        },
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    print(f"JSON 저장: {json_path}")


if __name__ == "__main__":
    main()
