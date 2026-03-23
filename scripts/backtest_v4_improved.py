#!/usr/bin/env python3
"""
v4 개선사항 적용 백테스트 — v2(기존) vs v4(개선) 비교

7가지 개선사항:
  1. STOP_LOSS/TAKE_PROFIT 현실화 (에이전트 레벨)
  2. 적응형 SPIKE_THRESHOLD (ATR 기반)
  3. WHALE_THRESHOLD BTC 수량 기반
  4. 하락장 매수 편향 제거 (SMA 하향 + FGI<25 → 매수 제한)
  5. 연속 음봉 필터 (3+ → 신규 매수 차단)
  6. MAX_HOLD 동적 조절 (ATR 기반)
  7. 매크로 이벤트 필터 (위험 시 매수 점수 감산)

출력: data/backtest_v4_results.json, data/backtest_v4_report.txt
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
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

INITIAL_KRW = 1_000_000
MAX_TRADE_AMOUNT = 500_000
SIM_START = datetime(2022, 1, 1, 0, 0, tzinfo=KST)
SIM_END = datetime(2026, 3, 23, 23, 59, tzinfo=KST)
LIVE_DATA_START = datetime(2023, 12, 15, 0, 0, tzinfo=KST)

random.seed(42)


# ── 데이터 수집 함수 (기존과 동일) ──

def load_historical_data(year: int) -> list[dict]:
    path = PROJECT_DIR / "data" / f"historical_{year}" / "sim_data_points.json"
    if not path.exists():
        print(f"  ! {path} 없음")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  {year}년: {len(data)}개 로드")
    return data


def convert_historical_to_sim_format(dp: dict) -> tuple[datetime, dict, dict, dict]:
    dt = datetime.fromisoformat(dp["datetime"])
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)
    indicators = dp["indicators"]
    fgi = dp["fgi"]
    ext = dp.get("external", {})
    news = ext.get("news", {})
    binance = ext.get("binance", {})
    macro = ext.get("macro", {})
    fusion = ext.get("fusion", {})
    fusion_signal = fusion.get("signal", "neutral")
    external_bonus = fusion.get("strategy_bonus", 0)
    macro_score = macro.get("score", 0)

    ext_formatted = {
        "external_signal": {
            "total_score": fusion.get("score", 0),
            "strategy_bonus": external_bonus,
            "fusion": {"signal": fusion_signal, "score": fusion.get("score", 0)},
        },
        "sources": {
            "news_sentiment": {"overall_sentiment": news.get("sentiment", "neutral"), "score": news.get("score", 0)},
            "binance_sentiment": {
                "kimchi_premium": {"premium_pct": binance.get("kimchi_premium_pct", 0)},
                "top_trader_long_short": {"current_ratio": binance.get("long_short_ratio", 1.0)},
                "funding_rate": {"current_rate": binance.get("funding_rate", 0)},
            },
            "macro": {"analysis": {"macro_score": macro_score, "sentiment": macro.get("sentiment", "neutral")}},
        },
        "_external_bonus": external_bonus,
        "_news_negative": news.get("sentiment") == "negative",
        "_fgi_value": fgi.get("value", 50),
        "_macro_score": macro_score,
    }
    return dt, indicators, fgi, ext_formatted


def fetch_upbit_candles_4h(to_dt: datetime, count: int = 200) -> list[dict]:
    url = "https://api.upbit.com/v1/candles/minutes/240"
    to_str = to_dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")
    params = {"market": "KRW-BTC", "to": to_str, "count": min(count, 200)}
    for retry in range(3):
        try:
            resp = requests.get(url, params=params, timeout=15)
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


def collect_live_candles() -> list[dict]:
    all_candles = []
    cursor = SIM_END + timedelta(hours=4)
    print("  Upbit 2024~2026 캔들 수집 중...")
    batch_count = 0
    while True:
        batch = fetch_upbit_candles_4h(cursor, 200)
        if not batch:
            break
        all_candles = batch + all_candles
        batch_count += 1
        oldest_str = batch[0]["candle_date_time_kst"]
        oldest = datetime.fromisoformat(oldest_str)
        if oldest.tzinfo is None:
            oldest = oldest.replace(tzinfo=KST)
        if oldest <= LIVE_DATA_START:
            break
        cursor = oldest
        time.sleep(0.15)
        if batch_count % 10 == 0:
            print(f"    ... {len(all_candles)}개, oldest={oldest.strftime('%Y-%m-%d')}")

    filtered = []
    for c in all_candles:
        dt = datetime.fromisoformat(c["candle_date_time_kst"])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        if LIVE_DATA_START <= dt <= SIM_END:
            c["_dt_kst"] = dt
            filtered.append(c)
    print(f"  -> {len(filtered)}개 캔들 수집")
    return filtered


def fetch_historical_fgi() -> dict[str, dict]:
    url = "https://api.alternative.me/fng/"
    params = {"limit": 0, "format": "json"}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception as e:
        print(f"  ! FGI 수집 실패: {e}")
        return {}
    fgi_map = {}
    for item in data:
        ts = int(item["timestamp"])
        dt = datetime.fromtimestamp(ts, tz=UTC)
        date_str = dt.strftime("%Y-%m-%d")
        fgi_map[date_str] = {"value": int(item["value"]), "classification": item["value_classification"]}
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


def calc_rsi(closes, period=14):
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


def calc_sma(closes, period=20):
    if len(closes) < period:
        return closes[-1] if closes else 0
    return sum(closes[-period:]) / period


def calc_macd(closes):
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
    signal = ema(closes[-9:], 9) if len(closes) >= 9 else closes[-1]
    return {"macd": round(macd_line, 2), "signal": round(signal, 2), "golden_cross": macd_line > signal}


def compute_indicators(candles, idx):
    closes = [c["trade_price"] for c in candles[:idx + 1]]
    price = closes[-1]
    rsi = calc_rsi(closes)
    sma20 = calc_sma(closes)
    macd = calc_macd(closes)
    sma_deviation = ((price - sma20) / sma20 * 100) if sma20 else 0
    if idx >= 6:
        price_24h_ago = candles[idx - 6]["trade_price"]
        change_24h = (price - price_24h_ago) / price_24h_ago * 100
    else:
        change_24h = 0

    # v4: ATR 계산 (4h 캔들 기준)
    atr_window = min(idx + 1, 24)
    atr_vals = []
    for j in range(max(0, idx - atr_window + 1), idx + 1):
        c = candles[j]
        tr = (c["high_price"] - c["low_price"]) / c["low_price"] * 100
        atr_vals.append(tr)
    atr_4h = sum(atr_vals) / len(atr_vals) if atr_vals else 1.0

    # 연속 음봉 계산
    consecutive_red = 0
    for j in range(idx, max(idx - 10, -1), -1):
        c = candles[j]
        if c["trade_price"] < c["opening_price"]:
            consecutive_red += 1
        else:
            break

    return {
        "current_price": price,
        "rsi_14": rsi,
        "sma_20": round(sma20),
        "sma_deviation_pct": round(sma_deviation, 2),
        "macd": macd,
        "price_change_24h": round(change_24h, 2),
        "volume": candles[idx].get("candle_acc_trade_volume", 0),
        "atr_4h": round(atr_4h, 3),
        "consecutive_red": consecutive_red,
    }


def simulate_external_data(dt, indicators, fgi):
    price = indicators["current_price"]
    change_24h = indicators["price_change_24h"]
    fgi_val = fgi["value"]

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
    news_sentiment = "negative" if news_score < -0.3 else ("positive" if news_score > 0.3 else "neutral")

    kimchi_pct = round((fgi_val - 50) * 0.04 + random.uniform(-1.0, 1.0), 2)
    ls_ratio = round(max(0.5, min(2.0, 1.0 + change_24h * 0.03 + random.uniform(-0.15, 0.15))), 2)
    funding_rate = round((ls_ratio - 1.0) * 0.01 + random.uniform(-0.005, 0.005), 5)
    macro_base = random.uniform(-15, 15)
    macro_score = round(max(-30, min(30, macro_base)), 1)

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

    external_bonus = {"strong_buy": 20, "buy": 10, "neutral": 0, "sell": -5, "strong_sell": -10}.get(fusion_signal, 0)

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
#  v5 레짐 기반 필터 강도 (모듈 상수)
# =====================================================
REGIME_FILTER_INTENSITY = {
    "bull": {
        "fgi_block": 5, "red_candle_block": 5, "bear_max_daily": 10,
        "sma_filter": False, "macro_penalty": 0, "momentum_min": 0.03,
        "buy_score_bonus": 0, "tp_multiplier": 1.5, "sl_multiplier": 1.0,
    },
    "early_bull": {
        "fgi_block": 8, "red_candle_block": 4, "bear_max_daily": 8,
        "sma_filter": False, "macro_penalty": 0, "momentum_min": 0.04,
        "buy_score_bonus": 0, "tp_multiplier": 1.3, "sl_multiplier": 1.0,
    },
    "sideways": {
        "fgi_block": 10, "red_candle_block": 3, "bear_max_daily": 5,
        "sma_filter": True, "macro_penalty": -5, "momentum_min": 0.06,
        "buy_score_bonus": 5, "tp_multiplier": 1.0, "sl_multiplier": 1.0,
    },
    "bear": {
        "fgi_block": 15, "red_candle_block": 3, "bear_max_daily": 2,
        "sma_filter": True, "macro_penalty": -15, "momentum_min": 0.08,
        "buy_score_bonus": 10, "tp_multiplier": 1.0, "sl_multiplier": 0.7,
    },
    "crisis": {
        "fgi_block": 20, "red_candle_block": 2, "bear_max_daily": 1,
        "sma_filter": True, "macro_penalty": -20, "momentum_min": 0.10,
        "buy_score_bonus": 15, "tp_multiplier": 1.0, "sl_multiplier": 0.7,
    },
}


# =====================================================
#  시뮬레이터 — v2(기존) + v4(개선) + v5(레짐) 동시 실행
# =====================================================

class TradingSimulator:
    def __init__(self, initial_krw: int, version: str = "v2"):
        self.version = version
        self.krw = float(initial_krw)
        self.initial_krw = float(initial_krw)
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
        self.yearly_stats: dict[str, dict] = {}
        self.trade_log: list[dict] = []
        self.switch_count = 0
        self.agents = {
            "conservative": ConservativeAgent(),
            "moderate": ModerateAgent(),
            "aggressive": AggressiveAgent(),
        }
        # v4/v5 전용 상태
        self._daily_buy_count = 0
        self._current_date = ""
        self._blocked_by_filter = 0  # 필터로 차단된 횟수
        # v5: 레짐 기반 필터 강도
        self._market_regime = "sideways"
        self._regime_filters = REGIME_FILTER_INTENSITY["sideways"]

    @property
    def agent(self):
        return self.agents[self.active_agent_name]

    def get_portfolio(self, price):
        btc_eval = self.btc * price
        total = self.krw + btc_eval
        btc_ratio = btc_eval / total if total > 0 else 0
        pnl = ((price / self.avg_buy_price) - 1) * 100 if self.avg_buy_price > 0 and self.btc > 0 else 0
        return {
            "total_krw": self.krw, "total_eval": total, "btc_ratio": round(btc_ratio, 4),
            "btc": {"balance": self.btc, "avg_buy_price": self.avg_buy_price, "profit_pct": round(pnl, 2), "eval_amount": btc_eval},
            "krw_balance": self.krw,
        }

    def evaluate_switch(self, danger, opportunity):
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

    def calc_danger(self, indicators, ext, portfolio):
        score = 0
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
        if ext["sources"]["news_sentiment"]["overall_sentiment"] == "negative":
            score += 10
        return min(score, 100)

    def calc_opportunity(self, indicators, ext):
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
        fgi_val = ext["_fgi_value"]
        sma_dev = indicators["sma_deviation_pct"]

        danger = self.calc_danger(indicators, ext, portfolio)
        opportunity = self.calc_opportunity(indicators, ext)

        new_agent = self.evaluate_switch(danger, opportunity)
        switch_info = None
        if new_agent and new_agent != self.active_agent_name:
            switch_info = {"from": self.active_agent_name, "to": new_agent}
            self.active_agent_name = new_agent
            self.switch_count += 1

        agent = self.agent

        # v4: 매수 점수 계산 전 보정
        external_bonus = ext["_external_bonus"]
        news_negative = ext["_news_negative"]

        if self.version in ("v4", "v5", "v5.1"):
            # 일자 리셋
            date_key = dt.strftime("%Y-%m-%d")
            if date_key != self._current_date:
                self._current_date = date_key
                self._daily_buy_count = 0

            if self.version in ("v5", "v5.1"):
                # v5/v5.1: 레짐 판별 (SMA추세 + FGI + ATR + 모멘텀)
                atr = indicators.get("atr_4h", 1.0)
                change_24h = indicators.get("price_change_24h", 0)

                if self.version == "v5.1":
                    # v5.1: bull 조기 감지 강화
                    # 1) 기존 bull (SMA 상향 + FGI 30으로 완화)
                    if sma_dev > 0.5 and fgi_val >= 30:
                        self._market_regime = "bull"
                    # 2) 모멘텀 대안: SMA 돌파 + 24h +2% → FGI 무관하게 bull
                    elif sma_dev > 0.3 and change_24h >= 2.0:
                        self._market_regime = "bull"
                    # 3) early_bull: SMA 전환 초기 (0~0.5%) + FGI 25+
                    elif sma_dev > 0 and fgi_val >= 25 and change_24h >= 0:
                        self._market_regime = "early_bull"
                    elif sma_dev < -2.0 and fgi_val <= 20 and atr > 2.0:
                        self._market_regime = "crisis"
                    elif sma_dev < -1.0 and fgi_val <= 35:
                        self._market_regime = "bear"
                    else:
                        self._market_regime = "sideways"
                else:
                    # v5: 기존 레짐 판별
                    if sma_dev > 0.5 and fgi_val >= 40:
                        self._market_regime = "bull"
                    elif sma_dev < -2.0 and fgi_val <= 20 and atr > 2.0:
                        self._market_regime = "crisis"
                    elif sma_dev < -1.0 and fgi_val <= 35:
                        self._market_regime = "bear"
                    else:
                        self._market_regime = "sideways"
                self._regime_filters = REGIME_FILTER_INTENSITY.get(
                    self._market_regime, REGIME_FILTER_INTENSITY["sideways"]
                )
                rf = self._regime_filters

                # v5: 레짐별 매수 점수 보정
                if rf.get("sma_filter", True):
                    if sma_dev < -1.0 and price < indicators["sma_20"] * 0.99:
                        external_bonus -= 15
                # 매크로 감산 (레짐별)
                if macro_score <= -10:
                    external_bonus += rf.get("macro_penalty", -10)  # bull: 0, bear: -15
            else:
                # v4: 기존 고정 필터
                if sma_dev < -1.0 and price < indicators["sma_20"] * 0.99:
                    external_bonus -= 15
                if macro_score <= -10:
                    external_bonus -= 10

        buy_score = agent.calculate_buy_score(
            fgi=fgi["value"], rsi=indicators["rsi_14"],
            sma_deviation=indicators["sma_deviation_pct"],
            news_negative=news_negative,
            external_bonus=external_bonus,
            macd_golden_cross=indicators["macd"]["golden_cross"],
        )

        decision = "hold"
        reason = ""
        trade_amount = 0
        trade_volume = 0.0
        filter_blocked = False

        # 매도 조건 (v5.1: 레짐별 tp/sl 배율)
        tp_mult = 1.0
        sl_mult = 1.0
        if self.version == "v5.1":
            rf = self._regime_filters
            tp_mult = rf.get("tp_multiplier", 1.0)
            sl_mult = rf.get("sl_multiplier", 1.0)

        if self.btc > 0:
            pnl_pct = ((price / self.avg_buy_price) - 1) * 100
            eff_target = agent.target_profit_pct * tp_mult
            eff_stop = agent.stop_loss_pct * sl_mult
            eff_forced = agent.forced_stop_loss_pct * sl_mult
            if pnl_pct >= eff_target:
                decision = "sell"
                reason = f"target {pnl_pct:.1f}% >= {eff_target:.1f}%"
            elif pnl_pct <= eff_forced:
                decision = "sell"
                reason = f"forced_stop {pnl_pct:.1f}%"
            elif pnl_pct <= eff_stop and danger >= 50:
                decision = "sell"
                reason = f"stop_loss {pnl_pct:.1f}%, D={danger}"
            elif indicators["rsi_14"] >= agent.sell_rsi_threshold and fgi["value"] >= agent.sell_fgi_threshold:
                decision = "sell"
                reason = f"overbought RSI={indicators['rsi_14']:.0f}, FGI={fgi['value']}"

            if decision == "sell":
                trade_volume = self.btc
                trade_amount = int(trade_volume * price)

        # 매수 조건
        if decision == "hold" and buy_score["result"] == "buy":
            # v5.1: 과매매 억제 - 레짐별 매수 점수 가산
            if self.version == "v5.1":
                bonus = self._regime_filters.get("buy_score_bonus", 0)
                effective_threshold = agent.buy_score_threshold + bonus
                if buy_score["total"] < effective_threshold:
                    filter_blocked = True
                    reason = f"v5.1_filter: score {buy_score['total']} < {effective_threshold} (regime={self._market_regime}, +{bonus})"
                    self._blocked_by_filter += 1

            # v4/v5/v5.1 필터 적용
            if not filter_blocked and self.version in ("v4", "v5", "v5.1"):
                consecutive_red = indicators.get("consecutive_red", 0)

                if self.version in ("v5", "v5.1"):
                    rf = self._regime_filters
                    red_block = rf.get("red_candle_block", 3)
                    bear_max = rf.get("bear_max_daily", 2)
                    fgi_block = rf.get("fgi_block", 15)

                    # 연속 음봉 (레짐별 기준)
                    if consecutive_red >= red_block:
                        filter_blocked = True
                        reason = f"v5_filter: 연속음봉 {consecutive_red} >= {red_block} (regime={self._market_regime})"
                        self._blocked_by_filter += 1
                    # FGI 차단 (레짐별)
                    elif fgi_val <= fgi_block:
                        filter_blocked = True
                        reason = f"v5_filter: FGI {fgi_val} <= {fgi_block} (regime={self._market_regime})"
                        self._blocked_by_filter += 1
                    # 하락장 매수 제한 (레짐별)
                    elif (sma_dev < -1.0 and fgi_val < 25 and self._daily_buy_count >= bear_max):
                        filter_blocked = True
                        reason = f"v5_filter: 하락장 매수제한 {self._daily_buy_count}/{bear_max} (regime={self._market_regime})"
                        self._blocked_by_filter += 1
                    # 매크로 강한 약세 + 하락추세 (bull/early_bull 시 미적용)
                    elif (macro_score <= -15 and sma_dev < -2.0
                          and self._market_regime not in ("bull", "early_bull")):
                        filter_blocked = True
                        reason = f"v5_filter: 매크로약세({macro_score}) + 하락 (regime={self._market_regime})"
                        self._blocked_by_filter += 1
                else:
                    # v4: 기존 고정 필터
                    if consecutive_red >= 3:
                        filter_blocked = True
                        reason = f"v4_filter: 연속음봉 {consecutive_red}개"
                        self._blocked_by_filter += 1
                    elif (sma_dev < -1.0 and fgi_val < 25 and self._daily_buy_count >= 2):
                        filter_blocked = True
                        reason = f"v4_filter: 하락장 매수제한 (FGI {fgi_val}, 매수 {self._daily_buy_count}/2)"
                        self._blocked_by_filter += 1
                    elif macro_score <= -15 and sma_dev < -2.0:
                        filter_blocked = True
                        reason = f"v4_filter: 매크로약세({macro_score}) + 하락추세"
                        self._blocked_by_filter += 1

            if not filter_blocked:
                available = min(self.krw * agent.max_trade_ratio, MAX_TRADE_AMOUNT)
                if available >= 5000:
                    decision = "buy"
                    trade_amount = int(available)
                    trade_volume = trade_amount / price
                    reason = f"score {buy_score['total']}>={agent.buy_score_threshold}"

        if decision == "hold" and not filter_blocked:
            reason = f"score {buy_score['total']}/{agent.buy_score_threshold}"

        # 실행
        year_key = dt.strftime("%Y")
        month_key = dt.strftime("%Y-%m")
        for key_map, key in [(self.monthly_stats, month_key), (self.yearly_stats, year_key)]:
            if key not in key_map:
                key_map[key] = {"buys": 0, "sells": 0, "holds": 0, "pnl": 0.0, "start_eval": 0, "end_eval": 0}
            if key_map[key]["start_eval"] == 0:
                key_map[key]["start_eval"] = self.krw + self.btc * price

        pnl_realized = 0.0
        if decision == "buy" and trade_amount > 0:
            total_cost = self.avg_buy_price * self.btc + trade_amount
            self.btc += trade_volume
            self.avg_buy_price = total_cost / self.btc if self.btc > 0 else 0
            self.krw -= trade_amount
            self.total_trades += 1
            self.total_buys += 1
            self.consecutive_buys += 1
            self._daily_buy_count += 1
            self.monthly_stats[month_key]["buys"] += 1
            self.yearly_stats[year_key]["buys"] += 1
        elif decision == "sell" and trade_volume > 0:
            revenue = trade_volume * price
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
            self.monthly_stats[month_key]["sells"] += 1
            self.monthly_stats[month_key]["pnl"] += pnl_realized
            self.yearly_stats[year_key]["sells"] += 1
            self.yearly_stats[year_key]["pnl"] += pnl_realized
        else:
            self.total_holds += 1
            self.monthly_stats[month_key]["holds"] += 1
            self.yearly_stats[year_key]["holds"] += 1

        current_eval = self.krw + self.btc * price
        if current_eval > self.peak_eval:
            self.peak_eval = current_eval
        dd = (self.peak_eval - current_eval) / self.peak_eval * 100
        if dd > self.max_drawdown:
            self.max_drawdown = dd

        self.yearly_stats[year_key]["end_eval"] = current_eval
        self.monthly_stats[month_key]["end_eval"] = current_eval

        if decision in ("buy", "sell"):
            self.trade_log.append({
                "dt": dt.isoformat(),
                "decision": decision,
                "reason": reason,
                "price": int(price),
                "amount": trade_amount,
                "pnl": round(pnl_realized),
                "agent": agent.name,
                "eval": round(current_eval),
            })

        return {
            "dt": dt.isoformat(),
            "decision": decision,
            "price": int(price),
            "agent": agent.name,
            "switch": switch_info,
            "buy_score": buy_score.get("total", 0),
            "fgi": fgi["value"],
            "rsi": round(indicators["rsi_14"], 1),
            "danger": danger,
            "opportunity": opportunity,
            "eval": round(current_eval),
            "filter_blocked": filter_blocked,
        }


# =====================================================
#  메인
# =====================================================

def main():
    t0 = time.time()
    report_lines = []

    def p(line=""):
        print(line)
        report_lines.append(line)

    p("=" * 70)
    p("  BTC 자동매매 v2 vs v4 비교 백테스트")
    p(f"  기간: {SIM_START.strftime('%Y-%m-%d')} ~ {SIM_END.strftime('%Y-%m-%d')}")
    p(f"  초기자금: {INITIAL_KRW:,}원 / 1회 상한: {MAX_TRADE_AMOUNT:,}원")
    p("=" * 70)

    # ── 데이터 수집 ──
    p("\n[Phase 1] 데이터 수집")
    hist_2022 = load_historical_data(2022)
    hist_2023 = load_historical_data(2023)
    live_candles = collect_live_candles()
    fgi_map = fetch_historical_fgi()
    p(f"  FGI: {len(fgi_map)}일")

    # ── 시뮬레이션 포인트 조립 ──
    p("\n[Phase 2] 시뮬레이션 포인트 조립")
    all_sim_points: list[tuple[datetime, dict, dict, dict]] = []

    for dp in hist_2022:
        all_sim_points.append(convert_historical_to_sim_format(dp))
    p(f"  2022년: {len(hist_2022)}개")

    for dp in hist_2023:
        all_sim_points.append(convert_historical_to_sim_format(dp))
    p(f"  2023년: {len(hist_2023)}개")

    live_start = datetime(2024, 1, 1, 0, 0, tzinfo=KST)
    seen_times = set()
    live_count = 0
    for i, c in enumerate(live_candles):
        dt = c["_dt_kst"]
        if dt < live_start:
            continue
        time_key = dt.strftime("%Y-%m-%d %H")
        if time_key in seen_times:
            continue
        seen_times.add(time_key)
        if i < 30:
            continue
        indicators = compute_indicators(live_candles, i)
        fgi = get_fgi_for_date(fgi_map, dt)
        ext = simulate_external_data(dt, indicators, fgi)
        all_sim_points.append((dt, indicators, fgi, ext))
        live_count += 1

    p(f"  2024~2026: {live_count}개")

    all_sim_points.sort(key=lambda x: x[0])
    deduplicated = []
    seen = set()
    for sp in all_sim_points:
        key = sp[0].strftime("%Y-%m-%d %H")
        if key not in seen:
            seen.add(key)
            deduplicated.append(sp)
    all_sim_points = deduplicated
    p(f"  총 시뮬레이션 포인트: {len(all_sim_points)}개")

    # ── 두 버전 동시 실행 ──
    p("\n[Phase 3] v2 vs v4 vs v5 vs v5.1 동시 시뮬레이션")

    sim_v2 = TradingSimulator(INITIAL_KRW, "v2")
    sim_v4 = TradingSimulator(INITIAL_KRW, "v4")
    sim_v5 = TradingSimulator(INITIAL_KRW, "v5")
    sim_v51 = TradingSimulator(INITIAL_KRW, "v5.1")

    results_v2 = []
    results_v4 = []
    results_v5 = []
    results_v51 = []
    diff_decisions = 0
    diff_v5 = 0
    diff_v51 = 0

    for step_i, (dt, indicators, fgi, ext) in enumerate(all_sim_points):
        r_v2 = sim_v2.step(dt, indicators, fgi, ext)
        r_v4 = sim_v4.step(dt, indicators, fgi, ext)
        r_v5 = sim_v5.step(dt, indicators, fgi, ext)
        r_v51 = sim_v51.step(dt, indicators, fgi, ext)
        results_v2.append(r_v2)
        results_v4.append(r_v4)
        results_v5.append(r_v5)
        results_v51.append(r_v51)

        if r_v2["decision"] != r_v4["decision"]:
            diff_decisions += 1
        if r_v4["decision"] != r_v5["decision"]:
            diff_v5 += 1
        if r_v5["decision"] != r_v51["decision"]:
            diff_v51 += 1

        if (step_i + 1) % 2000 == 0:
            p(f"  ... {step_i + 1}/{len(all_sim_points)} "
              f"v2={r_v2['eval']:,} v5={r_v5['eval']:,} v5.1={r_v51['eval']:,}")

    # ── 최종 결과 비교 ──
    final_price = all_sim_points[-1][1]["current_price"]
    first_price = all_sim_points[0][1]["current_price"]
    btc_bnh_roi = (final_price - first_price) / first_price * 100

    def summarize(sim, label):
        port = sim.get_portfolio(final_price)
        total_eval = port["total_eval"]
        roi = (total_eval - INITIAL_KRW) / INITIAL_KRW * 100
        wr = (sim.win_trades / (sim.win_trades + sim.loss_trades) * 100) if (sim.win_trades + sim.loss_trades) > 0 else 0
        return {
            "label": label,
            "final_eval": round(total_eval),
            "roi": round(roi, 2),
            "mdd": round(sim.max_drawdown, 2),
            "total_trades": sim.total_trades,
            "buys": sim.total_buys,
            "sells": sim.total_sells,
            "holds": sim.total_holds,
            "win_rate": round(wr, 1),
            "wins": sim.win_trades,
            "losses": sim.loss_trades,
            "switches": sim.switch_count,
            "blocked": getattr(sim, "_blocked_by_filter", 0),
        }

    s_v2 = summarize(sim_v2, "v2 (기존)")
    s_v4 = summarize(sim_v4, "v4 (고정필터)")
    s_v5 = summarize(sim_v5, "v5 (레짐적응)")
    s_v51 = summarize(sim_v51, "v5.1 (Bull강화)")

    p("\n" + "=" * 90)
    p("  v2 vs v5 vs v5.1 종합 비교")
    p("=" * 90)
    p(f"\n  BTC 가격: {first_price:,.0f}원 -> {final_price:,.0f}원 (B&H: {btc_bnh_roi:+.1f}%)")
    p(f"\n  {'항목':>14s} | {'v2 (기존)':>14s} | {'v5 (레짐적응)':>14s} | {'v5.1 (Bull강화)':>16s}")
    p(f"  {'-'*14}-+-{'-'*14}-+-{'-'*14}-+-{'-'*16}")

    items = [
        ("최종평가액", f"{s_v2['final_eval']:,}", f"{s_v5['final_eval']:,}", f"{s_v51['final_eval']:,}"),
        ("수익률(ROI)", f"{s_v2['roi']:+.2f}%", f"{s_v5['roi']:+.2f}%", f"{s_v51['roi']:+.2f}%"),
        ("MDD", f"-{s_v2['mdd']:.2f}%", f"-{s_v5['mdd']:.2f}%", f"-{s_v51['mdd']:.2f}%"),
        ("매수 횟수", f"{s_v2['buys']}", f"{s_v5['buys']}", f"{s_v51['buys']}"),
        ("매도 횟수", f"{s_v2['sells']}", f"{s_v5['sells']}", f"{s_v51['sells']}"),
        ("관망 횟수", f"{s_v2['holds']}", f"{s_v5['holds']}", f"{s_v51['holds']}"),
        ("승률", f"{s_v2['win_rate']:.1f}%", f"{s_v5['win_rate']:.1f}%", f"{s_v51['win_rate']:.1f}%"),
        ("전환 횟수", f"{s_v2['switches']}", f"{s_v5['switches']}", f"{s_v51['switches']}"),
        ("필터 차단", "N/A", f"{s_v5['blocked']}", f"{s_v51['blocked']}"),
    ]
    for label, v2_val, v5_val, v51_val in items:
        p(f"  {label:>14s} | {v2_val:>14s} | {v5_val:>14s} | {v51_val:>16s}")

    p(f"\n  v2<->v5 판단 차이: {diff_decisions}건 ({diff_decisions/len(all_sim_points)*100:.1f}%)")
    p(f"  v5<->v5.1 판단 차이: {diff_v51}건 ({diff_v51/len(all_sim_points)*100:.1f}%)")

    # ── 연도별 비교 ──
    p(f"\n{'=' * 90}")
    p("  연도별 비교")
    p(f"{'=' * 90}")
    p(f"  {'연도':>6s} | {'v2 매수':>6s} | {'v5 매수':>6s} | {'v5.1':>6s} | {'v2 ROI':>8s} | {'v5 ROI':>8s} | {'v5.1 ROI':>8s} | {'v5.1-v2':>8s}")
    p(f"  {'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}")

    all_years = sorted(set(list(sim_v2.yearly_stats.keys()) + list(sim_v5.yearly_stats.keys()) + list(sim_v51.yearly_stats.keys())))
    for year in all_years:
        ys2 = sim_v2.yearly_stats.get(year, {"buys": 0, "start_eval": 1, "end_eval": 1})
        ys5 = sim_v5.yearly_stats.get(year, {"buys": 0, "start_eval": 1, "end_eval": 1})
        ys51 = sim_v51.yearly_stats.get(year, {"buys": 0, "start_eval": 1, "end_eval": 1})
        roi2 = ((ys2["end_eval"] - ys2["start_eval"]) / ys2["start_eval"] * 100) if ys2["start_eval"] > 0 else 0
        roi5 = ((ys5["end_eval"] - ys5["start_eval"]) / ys5["start_eval"] * 100) if ys5["start_eval"] > 0 else 0
        roi51 = ((ys51["end_eval"] - ys51["start_eval"]) / ys51["start_eval"] * 100) if ys51["start_eval"] > 0 else 0
        p(f"  {year:>6s} | {ys2['buys']:>6d} | {ys5['buys']:>6d} | {ys51['buys']:>6d} | {roi2:>+7.1f}% | {roi5:>+7.1f}% | {roi51:>+7.1f}% | {roi51-roi2:>+7.1f}%p")

    # ── v5.1 레짐 분포 ──
    p(f"\n{'=' * 90}")
    p("  v5.1 레짐 분포 (v5 대비)")
    p(f"{'=' * 90}")
    # v5 레짐 (기존)
    regime_v5 = {"bull": 0, "bear": 0, "sideways": 0, "crisis": 0}
    # v5.1 레짐 (early_bull 추가)
    regime_v51 = {"bull": 0, "early_bull": 0, "bear": 0, "sideways": 0, "crisis": 0}
    for (dt, indicators, fgi, ext) in all_sim_points:
        sma_dev = indicators["sma_deviation_pct"]
        fgi_val = ext["_fgi_value"]
        atr = indicators.get("atr_4h", 1.0)
        change_24h = indicators.get("price_change_24h", 0)
        # v5
        if sma_dev > 0.5 and fgi_val >= 40:
            regime_v5["bull"] += 1
        elif sma_dev < -2.0 and fgi_val <= 20 and atr > 2.0:
            regime_v5["crisis"] += 1
        elif sma_dev < -1.0 and fgi_val <= 35:
            regime_v5["bear"] += 1
        else:
            regime_v5["sideways"] += 1
        # v5.1
        if sma_dev > 0.5 and fgi_val >= 30:
            regime_v51["bull"] += 1
        elif sma_dev > 0.3 and change_24h >= 2.0:
            regime_v51["bull"] += 1
        elif sma_dev > 0 and fgi_val >= 25 and change_24h >= 0:
            regime_v51["early_bull"] += 1
        elif sma_dev < -2.0 and fgi_val <= 20 and atr > 2.0:
            regime_v51["crisis"] += 1
        elif sma_dev < -1.0 and fgi_val <= 35:
            regime_v51["bear"] += 1
        else:
            regime_v51["sideways"] += 1

    total_pts = len(all_sim_points)
    p(f"  {'레짐':>12s} | {'v5':>8s} | {'v5.1':>8s} | {'변화':>8s}")
    p(f"  {'-'*12}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}")
    for regime in ["bull", "early_bull", "sideways", "bear", "crisis"]:
        c5 = regime_v5.get(regime, 0)
        c51 = regime_v51.get(regime, 0)
        diff = c51 - c5
        p(f"  {regime:>12s} | {c5:>5d} {c5/total_pts*100:>4.1f}% | {c51:>5d} {c51/total_pts*100:>4.1f}% | {diff:>+6d}")

    # ── 월별 상세 (v5.1이 더 좋았던/나빴던 달) ──
    p(f"\n{'=' * 70}")
    p("  월별 v5.1 vs v2 개선 효과 (차이 큰 순)")
    p(f"{'=' * 70}")

    monthly_diffs = []
    for month in sorted(set(list(sim_v2.monthly_stats.keys()) + list(sim_v51.monthly_stats.keys()))):
        ms2 = sim_v2.monthly_stats.get(month, {"end_eval": 0, "start_eval": 0, "buys": 0})
        ms51 = sim_v51.monthly_stats.get(month, {"end_eval": 0, "start_eval": 0, "buys": 0})
        if ms2["start_eval"] > 0 and ms51["start_eval"] > 0:
            eval_diff = ms51["end_eval"] - ms2["end_eval"]
            buy_diff = ms51["buys"] - ms2["buys"]
            monthly_diffs.append((month, eval_diff, buy_diff, ms2["buys"], ms51["buys"]))

    # 차이 큰 순으로 정렬
    monthly_diffs.sort(key=lambda x: abs(x[1]), reverse=True)

    p(f"  {'월':>7s} | {'v2 매수':>6s} | {'v5.1':>6s} | {'평가액 차이':>12s} | {'판정':>8s}")
    p(f"  {'-'*7}-+-{'-'*6}-+-{'-'*6}-+-{'-'*12}-+-{'-'*8}")
    for month, eval_diff, buy_diff, buys2, buys51 in monthly_diffs[:20]:
        verdict = "v5.1 우세" if eval_diff > 0 else "v2 우세" if eval_diff < 0 else "동일"
        p(f"  {month:>7s} | {buys2:>6d} | {buys51:>6d} | {eval_diff:>+12,.0f} | {verdict}")

    # ── v5.1 필터 효과 분석 ──
    if sim_v51._blocked_by_filter > 0:
        p(f"\n{'=' * 70}")
        p(f"  v5.1 필터 효과 (총 {sim_v51._blocked_by_filter}건 차단)")
        p(f"{'=' * 70}")

        # 차단된 시점 분석 (v2가 매수했지만 v5.1이 차단한 건)
        blocked_good = 0
        blocked_bad = 0
        for i in range(len(results_v2)):
            if results_v2[i]["decision"] == "buy" and results_v51[i].get("filter_blocked"):
                future_idx = min(i + 6, len(all_sim_points) - 1)
                future_price = all_sim_points[future_idx][1]["current_price"]
                current_price = all_sim_points[i][1]["current_price"]
                if future_price < current_price:
                    blocked_good += 1
                else:
                    blocked_bad += 1

        p(f"  v5.1이 차단한 매수 중:")
        p(f"    24h 후 하락 (차단 성공): {blocked_good}건")
        p(f"    24h 후 상승 (차단 실패): {blocked_bad}건")
        if blocked_good + blocked_bad > 0:
            accuracy = blocked_good / (blocked_good + blocked_bad) * 100
            p(f"    차단 정확도: {accuracy:.1f}%")

    # ── 결론 ──
    p(f"\n{'=' * 90}")
    p("  결론")
    p(f"{'=' * 90}")

    roi_v51v2 = s_v51["roi"] - s_v2["roi"]
    roi_v51v5 = s_v51["roi"] - s_v5["roi"]
    mdd_v51v2 = s_v2["mdd"] - s_v51["mdd"]
    eval_v51v2 = s_v51["final_eval"] - s_v2["final_eval"]

    p(f"\n  [v5.1 vs v2] ROI: {roi_v51v2:+.2f}%p | 평가액: {eval_v51v2:+,}원 | MDD: {mdd_v51v2:+.2f}%p")
    p(f"  [v5.1 vs v5] ROI: {roi_v51v5:+.2f}%p (Bull 강화 효과)")
    p(f"")
    p(f"  v2   ROI: {s_v2['roi']:+.2f}% | 매수 {s_v2['buys']}회 | MDD -{s_v2['mdd']:.1f}%")
    p(f"  v5   ROI: {s_v5['roi']:+.2f}% | 매수 {s_v5['buys']}회 | MDD -{s_v5['mdd']:.1f}%")
    p(f"  v5.1 ROI: {s_v51['roi']:+.2f}% | 매수 {s_v51['buys']}회 | MDD -{s_v51['mdd']:.1f}%")
    p(f"  BTC B&H:  {btc_bnh_roi:+.1f}%")

    p(f"\n  v5.1 개선사항 요약:")
    p(f"    1. Bull 조기 감지: FGI 40->30 완화, 24h+2% 모멘텀 대안, early_bull 레짐 추가")
    p(f"    2. Bull 익절 확대: tp_multiplier 1.5x (let winners run)")
    p(f"    3. Bear 손절 강화: sl_multiplier 0.7x (빠른 탈출)")
    p(f"    4. 과매매 억제: sideways +5, bear +10, crisis +15 매수 점수 가산")

    elapsed = time.time() - t0
    p(f"\n  소요시간: {elapsed:.0f}초")
    p(f"{'=' * 70}")

    # ── 파일 저장 ──
    report_path = PROJECT_DIR / "data" / "backtest_v4_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\n  보고서 저장: {report_path}")

    json_summary = {
        "period": f"{SIM_START.strftime('%Y-%m-%d')} ~ {SIM_END.strftime('%Y-%m-%d')}",
        "sim_points": len(all_sim_points),
        "btc_bnh_roi": round(btc_bnh_roi, 2),
        "v2": s_v2,
        "v4": s_v4,
        "v5": s_v5,
        "v5.1": s_v51,
        "diff_v5_v51": diff_v51,
        "roi_v51_vs_v2": round(roi_v51v2, 2),
        "roi_v51_vs_v5": round(roi_v51v5, 2),
        "mdd_v51_vs_v2": round(mdd_v51v2, 2),
        "regime_distribution_v5": regime_v5,
        "regime_distribution_v51": regime_v51,
        "yearly_comparison": {},
        "elapsed_sec": round(elapsed, 1),
    }

    for year in all_years:
        ys2 = sim_v2.yearly_stats.get(year, {"buys": 0, "sells": 0, "start_eval": 1, "end_eval": 1})
        ys5 = sim_v5.yearly_stats.get(year, {"buys": 0, "sells": 0, "start_eval": 1, "end_eval": 1})
        ys51 = sim_v51.yearly_stats.get(year, {"buys": 0, "sells": 0, "start_eval": 1, "end_eval": 1})
        json_summary["yearly_comparison"][year] = {
            "v2_buys": ys2["buys"], "v5_buys": ys5["buys"], "v51_buys": ys51["buys"],
            "v2_sells": ys2["sells"], "v5_sells": ys5["sells"], "v51_sells": ys51["sells"],
            "v2_eval": ys2["end_eval"], "v5_eval": ys5["end_eval"], "v51_eval": ys51["end_eval"],
        }

    json_path = PROJECT_DIR / "data" / "backtest_v4_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_summary, f, ensure_ascii=False, indent=2)
    print(f"  JSON 저장: {json_path}")


if __name__ == "__main__":
    main()
