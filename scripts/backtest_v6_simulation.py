#!/usr/bin/env python3
"""
v6 개선안 시뮬레이션 -v5.1(현행) vs v6(개선) vs BTC B&H 비교

v6 개선사항 3가지:
  1. 매도 점수제 (sell_score): RSI/FGI/수익률/추세이탈 복합 판단
  2. Bear 레짐 매수 완전 차단: 하락장에서 현금 보전
  3. 트레일링 스탑: 최고점 대비 -N% 시 자동 익절

출력: data/backtest_v6_results.json, data/backtest_v6_report.txt
"""

from __future__ import annotations

import json
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

from agents.base_agent import BaseStrategyAgent
from scripts.indicators import IncrementalIndicators
from scripts.sim_engine import BaseSimulator

KST = timezone(timedelta(hours=9))
UTC = timezone.utc

INITIAL_KRW = 1_000_000
MAX_TRADE_AMOUNT = 500_000
FEE_RATE = 0.0005        # Upbit 수수료 0.05% per trade
# v7.2: 레짐별 1회 매매 상한 + 포지션 비율
V7_MAX_TRADE = {"bull": 3_000_000, "early_bull": 2_000_000, "sideways": 300_000,
                "bear": 100_000, "crisis": 0}
V7_RATIOS = {"bull": 0.50, "early_bull": 0.35, "sideways": 0.10,
             "bear": 0.03, "crisis": 0.00}
SIM_START = datetime(2022, 1, 1, 0, 0, tzinfo=KST)
SIM_END = datetime(2026, 3, 23, 23, 59, tzinfo=KST)
LIVE_DATA_START = datetime(2023, 12, 15, 0, 0, tzinfo=KST)

random.seed(42)


# ═══════════════════════════════════════
#  데이터 수집 함수 (기존 backtest_v4와 동일)
# ═══════════════════════════════════════

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

    atr_window = min(idx + 1, 24)
    atr_vals = []
    for j in range(max(0, idx - atr_window + 1), idx + 1):
        c = candles[j]
        tr = (c["high_price"] - c["low_price"]) / c["low_price"] * 100
        atr_vals.append(tr)
    atr_4h = sum(atr_vals) / len(atr_vals) if atr_vals else 1.0

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


# ═══════════════════════════════════════
#  v5.1 레짐 필터 (기존 그대로)
# ═══════════════════════════════════════

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


# ═══════════════════════════════════════
#  v6 핵심: 매도 점수 계산
# ═══════════════════════════════════════

def calc_sell_score(
    pnl_pct: float,
    rsi: float,
    fgi_val: int,
    sma_dev: float,
    change_24h: float,
    danger: int,
    regime: str,
    news_negative: bool,
    macro_score: float,
    kimchi_pct: float,
) -> dict:
    """매도 점수 + 레짐별 임계값. BaseStrategyAgent.calculate_sell_score 위임."""
    base = BaseStrategyAgent.calculate_sell_score(
        pnl_pct=pnl_pct, rsi=rsi, fgi_val=fgi_val, sma_dev=sma_dev,
        change_24h=change_24h, danger=danger, news_negative=news_negative,
        macro_score=macro_score, kimchi_pct=kimchi_pct, fast=True,
    )
    # v8.1 레짐별 매도 임계값
    threshold = 60
    if regime in ("bear", "crisis"):
        threshold = 40
    elif regime == "sideways":
        threshold = 50
    elif regime == "bull":
        threshold = 85
    elif regime == "early_bull":
        threshold = 70  # v8.1: bull 85보다 낮게
    total = base["total"]
    return {"total": total, "threshold": threshold, "result": "sell" if total >= threshold else "hold"}


# ═══════════════════════════════════════
#  시뮬레이터 -v5.1(기존) + v6(개선)
# ═══════════════════════════════════════

class TradingSimulator(BaseSimulator):
    def __init__(self, initial_krw: int, version: str = "v5.1"):
        super().__init__(float(initial_krw), version)
        # TradingSimulator 전용 필드
        self.consecutive_buys = 0
        self.total_trades = 0
        self.total_holds = 0
        self.monthly_stats: dict[str, dict] = {}
        self.switch_count = 0
        self._blocked_by_filter = 0
        self._regime_filters = REGIME_FILTER_INTENSITY["sideways"]

    def step(self, dt: datetime, indicators: dict, fgi: dict, ext: dict) -> dict:
        price = indicators["current_price"]
        macro_score = ext["_macro_score"]
        fgi_val = ext["_fgi_value"]
        sma_dev = indicators["sma_deviation_pct"]
        change_24h = indicators.get("price_change_24h", 0)

        danger = self.calc_danger(indicators, ext)
        opportunity = self.calc_opportunity(indicators, ext)

        old_agent = self.active_agent_name
        self.apply_switch(danger, opportunity)
        if self.active_agent_name != old_agent:
            self.switch_count += 1

        agent = self.agent

        # v7.2 레짐 판별 — 연속상승 감지
        atr = indicators.get("atr_4h", 1.0)
        consecutive_up_days = self.update_consecutive_up(change_24h)

        self._market_regime = BaseStrategyAgent.detect_regime(
            sma_dev, fgi_val, change_24h, atr,
            consecutive_up_days=consecutive_up_days,
        )
        self._regime_filters = REGIME_FILTER_INTENSITY.get(
            self._market_regime, REGIME_FILTER_INTENSITY["sideways"]
        )
        rf = self._regime_filters

        # 매수 점수 보정
        external_bonus = ext["_external_bonus"]
        news_negative = ext["_news_negative"]
        if rf.get("sma_filter", True):
            if sma_dev < -1.0 and price < indicators["sma_20"] * 0.99:
                external_bonus -= 15
        if macro_score <= -10:
            external_bonus += rf.get("macro_penalty", -10)

        buy_score = agent.calculate_buy_score(
            fgi=fgi["value"], rsi=indicators["rsi_14"],
            sma_deviation=indicators["sma_deviation_pct"],
            news_negative=news_negative,
            external_bonus=external_bonus,
            macd_golden_cross=indicators["macd"]["golden_cross"],
            fast=True,
        )

        self.check_new_date(dt)

        decision = "hold"
        reason = ""
        trade_amount = 0
        trade_volume = 0.0
        filter_blocked = False
        sell_score_info = None

        # ── 매도 로직 ──
        if self.btc > 0:
            pnl_pct = ((price / self.avg_buy_price) - 1) * 100

            # 트레일링 스탑 최고가 갱신
            if price > self._position_peak:
                self._position_peak = price

            if self.version == "v6":
                # ═══ v6 매도: 점수제 + 트레일링 스탑 ═══
                bs = ext["sources"]["binance_sentiment"]
                kimchi_pct = bs["kimchi_premium"]["premium_pct"]

                sell_score_info = calc_sell_score(
                    pnl_pct=pnl_pct,
                    rsi=indicators["rsi_14"],
                    fgi_val=fgi_val,
                    sma_dev=sma_dev,
                    change_24h=change_24h,
                    danger=danger,
                    regime=self._market_regime,
                    news_negative=news_negative,
                    macro_score=macro_score,
                    kimchi_pct=kimchi_pct,
                )

                # 1) 매도 점수제
                if sell_score_info["result"] == "sell":
                    # v7: 상승장에서는 1/3만 부분매도
                    if self._market_regime in ("bull", "early_bull"):
                        decision = "sell_partial"
                    else:
                        decision = "sell"
                    reason = f"v6_sell_score {sell_score_info['total']}>={sell_score_info['threshold']} (regime={self._market_regime})"
                    self._sell_by_score += 1

                # 2) 트레일링 스탑: 최고점 대비 하락 시 익절
                #    레짐별 트레일링 비율 다르게
                if decision == "hold" and self._position_peak > 0 and pnl_pct > 0:
                    trail_from_peak = ((price / self._position_peak) - 1) * 100
                    # 트레일링 기준: bull -7%, sideways -5%, bear -3%
                    # v7.2: 레짐별 트레일링 (early_bull 분리)
                    trail_threshold = {
                        "bull": -15.0, "early_bull": -12.0,
                        "sideways": -4.0, "bear": -1.5, "crisis": -1.5,
                    }.get(self._market_regime, -3.5)
                    if trail_from_peak <= trail_threshold:
                        decision = "sell"
                        reason = f"v6_trailing {trail_from_peak:.1f}% <= {trail_threshold}% (peak={self._position_peak:,.0f})"
                        self._sell_by_trailing += 1

                # 3) 강제 손절 (v5.1과 동일하되 레짐별)
                if decision == "hold":
                    eff_forced = agent.forced_stop_loss_pct * rf.get("sl_multiplier", 1.0)
                    if pnl_pct <= eff_forced:
                        decision = "sell"
                        reason = f"v6_forced_stop {pnl_pct:.1f}% <= {eff_forced:.1f}%"
                        self._sell_by_forced += 1

            else:
                # ═══ v5.1 매도: 기존 로직 ═══
                tp_mult = rf.get("tp_multiplier", 1.0)
                sl_mult = rf.get("sl_multiplier", 1.0)
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

            if decision in ("sell", "sell_partial"):
                if decision == "sell_partial":
                    trade_volume = self.btc / 4  # v7.2: 1/4만 매도
                else:
                    trade_volume = self.btc
                trade_amount = int(trade_volume * price)

        # ── 매수 로직 ──
        if decision == "hold" and buy_score["result"] == "buy":

            # v6 개선 2: Bear/Crisis 레짐 매수 완전 차단
            if self.version == "v6" and self._market_regime in ("bear", "crisis"):
                filter_blocked = True
                reason = f"v6_bear_block: regime={self._market_regime} (매수 완전 차단)"
                self._blocked_by_filter += 1
                self._bear_blocks += 1

            # v5.1 과매매 억제 (v6에서도 동일 적용, bear/crisis는 이미 위에서 차단)
            if not filter_blocked:
                bonus = rf.get("buy_score_bonus", 0)
                effective_threshold = agent.buy_score_threshold + bonus
                if buy_score["total"] < effective_threshold:
                    filter_blocked = True
                    reason = f"filter: score {buy_score['total']} < {effective_threshold} (regime={self._market_regime})"
                    self._blocked_by_filter += 1

            # v5.1/v6 공통 필터
            if not filter_blocked:
                consecutive_red = indicators.get("consecutive_red", 0)
                red_block = rf.get("red_candle_block", 3)
                bear_max = rf.get("bear_max_daily", 2)
                fgi_block = rf.get("fgi_block", 15)

                if consecutive_red >= red_block:
                    filter_blocked = True
                    reason = f"filter: 연속음봉 {consecutive_red} >= {red_block}"
                    self._blocked_by_filter += 1
                elif fgi_val <= fgi_block:
                    filter_blocked = True
                    reason = f"filter: FGI {fgi_val} <= {fgi_block}"
                    self._blocked_by_filter += 1
                elif sma_dev < -1.0 and fgi_val < 25 and self._daily_buy_count >= bear_max:
                    filter_blocked = True
                    reason = f"filter: 하락장 매수제한 {self._daily_buy_count}/{bear_max}"
                    self._blocked_by_filter += 1
                elif (macro_score <= -15 and sma_dev < -2.0
                      and self._market_regime not in ("bull", "early_bull")):
                    filter_blocked = True
                    reason = f"filter: 매크로약세({macro_score})"
                    self._blocked_by_filter += 1
                # v7.2 #3: 횡보장 진입 조건 강화 — RSI 50+ 과매수 진입 방지
                elif (self._market_regime == "sideways"
                      and indicators["rsi_14"] >= 55
                      and fgi_val >= 50):
                    filter_blocked = True
                    reason = f"filter: 횡보 과매수 진입차단 RSI={indicators['rsi_14']:.0f} FGI={fgi_val}"
                    self._blocked_by_filter += 1

            if not filter_blocked:
                if self.version == "v6":
                    _ratio = V7_RATIOS.get(self._market_regime, 0.15)
                    _max = V7_MAX_TRADE.get(self._market_regime, MAX_TRADE_AMOUNT)
                else:
                    _ratio = agent.max_trade_ratio
                    _max = MAX_TRADE_AMOUNT
                available = min(self.krw * _ratio, _max)
                if available >= 5000:
                    decision = "buy"
                    trade_amount = int(available)
                    trade_volume = trade_amount * (1 - FEE_RATE) / price  # 수수료 차감
                    reason = f"score {buy_score['total']}>={agent.buy_score_threshold}"

        if decision == "hold" and not filter_blocked:
            reason = f"score {buy_score['total']}/{agent.buy_score_threshold}"

        # ── 실행 (BaseSimulator 헬퍼 활용) ──
        year_key = dt.strftime("%Y")
        month_key = dt.strftime("%Y-%m")
        for key_map, key in [(self.monthly_stats, month_key), (self.yearly_stats, year_key)]:
            if key not in key_map:
                key_map[key] = {"buys": 0, "sells": 0, "holds": 0, "pnl": 0.0, "start_eval": 0, "end_eval": 0}
            if key_map[key]["start_eval"] == 0:
                key_map[key]["start_eval"] = self.krw + self.btc * price

        pnl_realized = 0.0
        if decision == "buy" and trade_amount > 0:
            self.execute_buy(price, trade_amount)

            self.total_trades += 1
            self.consecutive_buys += 1
            self.monthly_stats[month_key]["buys"] += 1
            self.yearly_stats[year_key]["buys"] += 1
        elif decision in ("sell", "sell_partial") and trade_volume > 0:
            pnl_realized = self.execute_sell(price, trade_volume, partial=(decision == "sell_partial"))

            self.total_trades += 1
            self.consecutive_buys = 0
            self.monthly_stats[month_key]["sells"] += 1
            self.monthly_stats[month_key]["pnl"] += pnl_realized
            self.yearly_stats[year_key]["sells"] += 1
            self.yearly_stats[year_key]["pnl"] += pnl_realized
        else:
            self.total_holds += 1
            self.monthly_stats[month_key]["holds"] += 1
            self.yearly_stats[year_key]["holds"] += 1

        current_eval = self.update_drawdown(price)

        self.yearly_stats[year_key]["end_eval"] = current_eval
        self.monthly_stats[month_key]["end_eval"] = current_eval

        if decision in ("buy", "sell", "sell_partial"):
            self.trade_log.append({
                "dt": dt.isoformat(), "decision": decision, "reason": reason,
                "price": int(price), "amount": trade_amount,
                "pnl": round(pnl_realized), "agent": agent.name,
                "eval": round(current_eval), "regime": self._market_regime,
            })

        return {
            "dt": dt.isoformat(), "decision": decision, "price": int(price),
            "agent": agent.name, "buy_score": buy_score.get("total", 0),
            "sell_score": sell_score_info["total"] if sell_score_info else 0,
            "fgi": fgi["value"], "rsi": round(indicators["rsi_14"], 1),
            "danger": danger, "opportunity": opportunity,
            "eval": round(current_eval), "regime": self._market_regime,
            "filter_blocked": filter_blocked,
        }


# ═══════════════════════════════════════
#  메인
# ═══════════════════════════════════════

def main():
    t0 = time.time()
    report_lines = []

    def p(line=""):
        print(line)
        report_lines.append(line)

    p("=" * 80)
    p("  BTC 자동매매 v5.1 vs v6 시뮬레이션")
    p(f"  기간: {SIM_START.strftime('%Y-%m-%d')} ~ {SIM_END.strftime('%Y-%m-%d')}")
    p(f"  초기자금: {INITIAL_KRW:,}원 / 1회 상한: {MAX_TRADE_AMOUNT:,}원")
    p("=" * 80)
    p("")
    p("  v6 개선사항:")
    p("    1. 매도 점수제 -RSI/FGI/수익률/추세/위험도 복합 판단 (60점 이상 매도)")
    p("    2. Bear/Crisis 매수 완전 차단 -하락장에서 현금 보전")
    p("    3. 트레일링 스탑 -최고점 대비 -5~7% 하락 시 자동 익절")

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
    inc = IncrementalIndicators()
    for i, c in enumerate(live_candles):
        indicators = inc.update(c)  # O(1) 갱신 — warm-up 포함
        dt = c["_dt_kst"]
        if dt < live_start:
            continue
        time_key = dt.strftime("%Y-%m-%d %H")
        if time_key in seen_times:
            continue
        seen_times.add(time_key)
        if i < 30:
            continue
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
    p("\n[Phase 3] v5.1 vs v6 동시 시뮬레이션")

    sim_v51 = TradingSimulator(INITIAL_KRW, "v5.1")
    sim_v6 = TradingSimulator(INITIAL_KRW, "v6")

    # 연결 테스트: 2017-2021 최종 상태 이어받기
    chain_file = PROJECT_DIR / "data" / "backtest_v6_2018_2021.json"
    if chain_file.exists():
        with open(chain_file, "r", encoding="utf-8") as cf:
            prev = json.load(cf)
        fs = prev.get("v6", {}).get("final_state")
        if fs:
            sim_v6_chain = TradingSimulator(fs["total_eval"], "v6")
            sim_v6_chain.krw = float(fs["krw"])
            sim_v6_chain.btc = float(fs["btc"])
            sim_v6_chain.avg_buy_price = float(fs["avg_buy_price"])
            sim_v6_chain.active_agent_name = fs.get("agent", "conservative")
            sim_v6_chain.peak_eval = float(fs.get("peak_eval", fs["total_eval"]))
            sim_v6_chain.consecutive_losses = int(fs.get("consecutive_losses", 0))
            sim_v6_chain.consecutive_buys = int(fs.get("consecutive_buys", 0))
            sim_v6_chain._position_peak = float(fs.get("position_peak_price", 0))
            sim_v6_chain._consecutive_up_candles = int(fs.get("consecutive_up_candles", 0))
            sim_v6_chain._market_regime = fs.get("market_regime", "sideways")
            p("  ** 연결모드: 2017-2021 최종 상태 이어받음 **")
            p(f"     KRW={fs['krw']:,}, BTC={fs['btc']:.8f}, 총={fs['total_eval']:,}")
        else:
            sim_v6_chain = None
            p("  ** 연결모드: final_state 없음 — 독립 실행 **")
    else:
        sim_v6_chain = None
        p("  ** 연결모드: 이전 결과 없음 — 독립 실행 **")

    # 메모리 최적화: 오버라이드 분석에 필요한 필드만 저장
    results_v51_decisions = []
    results_v6_decisions = []
    diff_decisions = 0

    for step_i, (dt, indicators, fgi, ext) in enumerate(all_sim_points):
        r_v51 = sim_v51.step(dt, indicators, fgi, ext)
        r_v6 = sim_v6.step(dt, indicators, fgi, ext)
        if sim_v6_chain:
            sim_v6_chain.step(dt, indicators, fgi, ext)
        results_v51_decisions.append(r_v51["decision"])
        results_v6_decisions.append((r_v6["decision"], r_v6.get("filter_blocked", False)))

        if r_v51["decision"] != r_v6["decision"]:
            diff_decisions += 1

        if (step_i + 1) % 2000 == 0:
            chain_eval = f" chain={sim_v6_chain.krw + sim_v6_chain.btc * indicators['current_price']:,.0f}" if sim_v6_chain else ""
            p(f"  ... {step_i + 1}/{len(all_sim_points)} "
              f"v5.1={r_v51['eval']:,} v6={r_v6['eval']:,}{chain_eval}")

    # ── 최종 결과 ──
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
            "blocked": sim._blocked_by_filter,
        }

    s_v51 = summarize(sim_v51, "v5.1 (현행)")
    s_v6 = summarize(sim_v6, "v6 (개선)")

    p("\n" + "=" * 80)
    p("  * 최종 결과: v5.1 vs v6 vs B&H")
    p("=" * 80)
    p(f"\n  BTC 가격: {first_price:,.0f}원 -> {final_price:,.0f}원")
    p(f"  BTC Buy & Hold: {btc_bnh_roi:+.1f}%\n")

    p(f"  {'항목':>16s} | {'v5.1 (현행)':>14s} | {'v6 (개선)':>14s} | {'B&H':>14s}")
    p(f"  {'-'*16}-+-{'-'*14}-+-{'-'*14}-+-{'-'*14}")

    items = [
        ("최종 평가액", f"{s_v51['final_eval']:,}원", f"{s_v6['final_eval']:,}원",
         f"{int(INITIAL_KRW * (1 + btc_bnh_roi/100)):,}원"),
        ("수익률 (ROI)", f"{s_v51['roi']:+.2f}%", f"{s_v6['roi']:+.2f}%", f"{btc_bnh_roi:+.1f}%"),
        ("MDD", f"-{s_v51['mdd']:.1f}%", f"-{s_v6['mdd']:.1f}%", "-"),
        ("매수 횟수", f"{s_v51['buys']}", f"{s_v6['buys']}", "1"),
        ("매도 횟수", f"{s_v51['sells']}", f"{s_v6['sells']}", "0"),
        ("매수:매도 비율", f"{s_v51['buys']/max(s_v51['sells'],1):.1f}:1",
         f"{s_v6['buys']/max(s_v6['sells'],1):.1f}:1", "-"),
        ("승률", f"{s_v51['win_rate']:.1f}%", f"{s_v6['win_rate']:.1f}%", "-"),
        ("필터 차단", f"{s_v51['blocked']}", f"{s_v6['blocked']}", "-"),
    ]
    for label, v51_val, v6_val, bnh_val in items:
        p(f"  {label:>16s} | {v51_val:>14s} | {v6_val:>14s} | {bnh_val:>14s}")

    # ── v6 매도 분석 ──
    p(f"\n{'=' * 80}")
    p("  v6 매도 유형별 분석")
    p(f"{'=' * 80}")
    p(f"  매도 점수제:     {sim_v6._sell_by_score}건")
    p(f"  트레일링 스탑:   {sim_v6._sell_by_trailing}건")
    p(f"  강제 손절:       {sim_v6._sell_by_forced}건")
    p(f"  Bear 매수 차단:  {sim_v6._bear_blocks}건")
    total_v6_sells = sim_v6._sell_by_score + sim_v6._sell_by_trailing + sim_v6._sell_by_forced
    if total_v6_sells > 0:
        p(f"\n  매도 점수제 비율:   {sim_v6._sell_by_score/total_v6_sells*100:.1f}%")
        p(f"  트레일링 스탑 비율: {sim_v6._sell_by_trailing/total_v6_sells*100:.1f}%")
        p(f"  강제 손절 비율:     {sim_v6._sell_by_forced/total_v6_sells*100:.1f}%")

    # ── B&H 대비 개선 ──
    p(f"\n{'=' * 80}")
    p("  B&H 대비 개선도")
    p(f"{'=' * 80}")
    gap_v51 = s_v51["roi"] - btc_bnh_roi
    gap_v6 = s_v6["roi"] - btc_bnh_roi
    improvement = s_v6["roi"] - s_v51["roi"]
    p(f"  v5.1 vs B&H 격차:  {gap_v51:+.1f}%p")
    p(f"  v6   vs B&H 격차:  {gap_v6:+.1f}%p")
    p(f"  v6   vs v5.1 개선: {improvement:+.1f}%p")
    if gap_v51 != 0:
        gap_reduction = (1 - gap_v6 / gap_v51) * 100
        p(f"  B&H 격차 축소:     {gap_reduction:.1f}%")

    # ── 연도별 비교 ──
    p(f"\n{'=' * 80}")
    p("  연도별 비교")
    p(f"{'=' * 80}")
    p(f"  {'연도':>6s} | {'v5.1 매수':>8s} | {'v6 매수':>7s} | {'v5.1 매도':>8s} | {'v6 매도':>7s} | {'v5.1 ROI':>9s} | {'v6 ROI':>9s} | {'v6-v5.1':>9s}")
    p(f"  {'-'*6}-+-{'-'*8}-+-{'-'*7}-+-{'-'*8}-+-{'-'*7}-+-{'-'*9}-+-{'-'*9}-+-{'-'*9}")

    all_years = sorted(set(list(sim_v51.yearly_stats.keys()) + list(sim_v6.yearly_stats.keys())))
    for year in all_years:
        ys51 = sim_v51.yearly_stats.get(year, {"buys": 0, "sells": 0, "start_eval": 1, "end_eval": 1})
        ys6 = sim_v6.yearly_stats.get(year, {"buys": 0, "sells": 0, "start_eval": 1, "end_eval": 1})
        roi51 = ((ys51["end_eval"] - ys51["start_eval"]) / ys51["start_eval"] * 100) if ys51["start_eval"] > 0 else 0
        roi6 = ((ys6["end_eval"] - ys6["start_eval"]) / ys6["start_eval"] * 100) if ys6["start_eval"] > 0 else 0
        p(f"  {year:>6s} | {ys51['buys']:>8d} | {ys6['buys']:>7d} | {ys51['sells']:>8d} | {ys6['sells']:>7d} | {roi51:>+8.1f}% | {roi6:>+8.1f}% | {roi6-roi51:>+8.1f}%p")

    # ── 월별 v6이 좋았던/나빴던 달 ──
    p(f"\n{'=' * 80}")
    p("  월별 v6 vs v5.1 차이 (차이 큰 순 Top 20)")
    p(f"{'=' * 80}")

    monthly_diffs = []
    for month in sorted(set(list(sim_v51.monthly_stats.keys()) + list(sim_v6.monthly_stats.keys()))):
        ms51 = sim_v51.monthly_stats.get(month, {"end_eval": 0, "start_eval": 0, "buys": 0, "sells": 0})
        ms6 = sim_v6.monthly_stats.get(month, {"end_eval": 0, "start_eval": 0, "buys": 0, "sells": 0})
        if ms51["start_eval"] > 0 and ms6["start_eval"] > 0:
            eval_diff = ms6["end_eval"] - ms51["end_eval"]
            monthly_diffs.append((month, eval_diff, ms51["buys"], ms6["buys"], ms51["sells"], ms6["sells"]))

    monthly_diffs.sort(key=lambda x: abs(x[1]), reverse=True)
    p(f"  {'월':>7s} | {'v5.1 B/S':>10s} | {'v6 B/S':>10s} | {'평가액 차이':>12s} | {'판정':>8s}")
    p(f"  {'-'*7}-+-{'-'*10}-+-{'-'*10}-+-{'-'*12}-+-{'-'*8}")
    for month, eval_diff, b51, b6, s51, s6 in monthly_diffs[:20]:
        verdict = "v6 우세" if eval_diff > 0 else "v5.1 우세" if eval_diff < 0 else "동일"
        p(f"  {month:>7s} | {b51:>4d}/{s51:<4d} | {b6:>4d}/{s6:<4d} | {eval_diff:>+12,.0f} | {verdict}")

    # ── v6 판단 차이 분석 ──
    p(f"\n{'=' * 80}")
    p("  판단 차이 분석")
    p(f"{'=' * 80}")
    p(f"  총 판단 차이: {diff_decisions}건 / {len(all_sim_points)}건 ({diff_decisions/len(all_sim_points)*100:.1f}%)")

    # v6이 매도한 곳에서 v5.1은 hold -이후 가격 변동 분석
    v6_sell_good = 0
    v6_sell_bad = 0
    v6_block_good = 0
    v6_block_bad = 0
    for i in range(len(results_v51_decisions)):
        v51_dec = results_v51_decisions[i]
        v6_dec, v6_blocked = results_v6_decisions[i]
        # v6 매도, v5.1 hold → 24h 후 가격 비교
        if v6_dec == "sell" and v51_dec != "sell":
            future_idx = min(i + 6, len(all_sim_points) - 1)
            future_price = all_sim_points[future_idx][1]["current_price"]
            current_price = all_sim_points[i][1]["current_price"]
            if future_price < current_price:
                v6_sell_good += 1  # 판 뒤에 떨어짐 = 잘 판 것
            else:
                v6_sell_bad += 1
        # v6 bear 차단, v5.1 매수 → 24h 후 비교
        if v6_blocked and v51_dec == "buy":
            future_idx = min(i + 6, len(all_sim_points) - 1)
            future_price = all_sim_points[future_idx][1]["current_price"]
            current_price = all_sim_points[i][1]["current_price"]
            if future_price < current_price:
                v6_block_good += 1
            else:
                v6_block_bad += 1

    if v6_sell_good + v6_sell_bad > 0:
        p("\n  v6 추가 매도 (v5.1은 hold):")
        p(f"    24h 후 하락 (매도 적절): {v6_sell_good}건")
        p(f"    24h 후 상승 (매도 아쉬움): {v6_sell_bad}건")
        p(f"    매도 정확도: {v6_sell_good/(v6_sell_good+v6_sell_bad)*100:.1f}%")

    if v6_block_good + v6_block_bad > 0:
        p("\n  v6 Bear 차단 (v5.1은 매수):")
        p(f"    24h 후 하락 (차단 적절): {v6_block_good}건")
        p(f"    24h 후 상승 (차단 아쉬움): {v6_block_bad}건")
        p(f"    차단 정확도: {v6_block_good/(v6_block_good+v6_block_bad)*100:.1f}%")

    # ── 결론 ──
    p(f"\n{'=' * 80}")
    p("  * 결론")
    p(f"{'=' * 80}")
    p("")
    p(f"  v5.1 ROI: {s_v51['roi']:+.2f}% | 매수 {s_v51['buys']}회, 매도 {s_v51['sells']}회 | MDD -{s_v51['mdd']:.1f}%")
    p(f"  v6   ROI: {s_v6['roi']:+.2f}% | 매수 {s_v6['buys']}회, 매도 {s_v6['sells']}회 | MDD -{s_v6['mdd']:.1f}%")
    p(f"  B&H  ROI: {btc_bnh_roi:+.1f}%")
    p("")

    p(f"  v6 수수료 합계: {sim_v6.total_fees:,.0f}원")

    if s_v6["roi"] > btc_bnh_roi:
        p(f"  [O] v6이 B&H를 {s_v6['roi'] - btc_bnh_roi:.1f}%p 초과 달성!")
    elif s_v6["roi"] > s_v51["roi"]:
        p(f"  [~] v6이 v5.1 대비 {improvement:+.1f}%p 개선, B&H까지 {abs(gap_v6):.1f}%p 남음")
    else:
        p(f"  [X] v6이 v5.1보다 오히려 {abs(improvement):.1f}%p 악화")

    # ── 연결 테스트 결과 (2017→2026) ──
    if sim_v6_chain:
        chain_eval = sim_v6_chain.krw + sim_v6_chain.btc * final_price
        chain_initial = float(prev["v6"]["final_state"]["total_eval"])
        chain_roi_2022 = (chain_eval / chain_initial - 1) * 100
        chain_roi_total = (chain_eval / INITIAL_KRW - 1) * 100
        p(f"\n{'=' * 80}")
        p("  ** 연결 테스트: 2017-2026 (수수료 포함) **")
        p(f"{'=' * 80}")
        p(f"  2017-2021 최종: {chain_initial:,.0f}원")
        p(f"  2022-2026 최종: {chain_eval:,.0f}원")
        p(f"  2022-2026 ROI:  {chain_roi_2022:+.1f}%")
        p(f"  전체 ROI (1M→):  {chain_roi_total:+.1f}%")
        p(f"  수수료 합계:     {sim_v6_chain.total_fees:,.0f}원 (2022-2026)")
        p(f"  MDD:             {sim_v6_chain.max_drawdown:.1f}%")
        p(f"  거래: 매수 {sim_v6_chain.total_buys}회, 매도 {sim_v6_chain.total_sells}회")
        # B&H 2017→2026 비교
        # bh_2017_start = prev["v6"]["final_state"]["last_price"]
        # bh_chain = (final_price / bh_2017_start) * chain_initial
        # bh_chain_roi = (bh_chain / INITIAL_KRW - 1) * 100
        # 실제 BH: 2017 시작가 → 2026 최종가
        p("  B&H 2017→2026: 시작가 기준 ROI 참고용")
        p(f"  최종 평가: v7.2={chain_eval:,.0f}원")

    elapsed = time.time() - t0
    p(f"\n  소요시간: {elapsed:.0f}초")
    p(f"{'=' * 80}")

    # ── 파일 저장 ──
    report_path = PROJECT_DIR / "data" / "backtest_v6_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\n  보고서 저장: {report_path}")

    json_summary = {
        "period": f"{SIM_START.strftime('%Y-%m-%d')} ~ {SIM_END.strftime('%Y-%m-%d')}",
        "sim_points": len(all_sim_points),
        "btc_bnh_roi": round(btc_bnh_roi, 2),
        "v5.1": s_v51,
        "v6": s_v6,
        "v6_sell_breakdown": {
            "sell_by_score": sim_v6._sell_by_score,
            "sell_by_trailing": sim_v6._sell_by_trailing,
            "sell_by_forced": sim_v6._sell_by_forced,
            "bear_buy_blocks": sim_v6._bear_blocks,
        },
        "v6_accuracy": {
            "sell_good": v6_sell_good,
            "sell_bad": v6_sell_bad,
            "block_good": v6_block_good,
            "block_bad": v6_block_bad,
        },
        "improvement_vs_v51": round(improvement, 2),
        "gap_to_bnh": round(gap_v6, 2),
        "yearly_comparison": {},
        "elapsed_sec": round(elapsed, 1),
    }

    for year in all_years:
        ys51 = sim_v51.yearly_stats.get(year, {"buys": 0, "sells": 0, "start_eval": 1, "end_eval": 1})
        ys6 = sim_v6.yearly_stats.get(year, {"buys": 0, "sells": 0, "start_eval": 1, "end_eval": 1})
        json_summary["yearly_comparison"][year] = {
            "v51_buys": ys51["buys"], "v6_buys": ys6["buys"],
            "v51_sells": ys51["sells"], "v6_sells": ys6["sells"],
            "v51_eval": ys51["end_eval"], "v6_eval": ys6["end_eval"],
        }

    json_summary["v6_trade_log"] = sim_v6.trade_log

    json_path = PROJECT_DIR / "data" / "backtest_v6_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_summary, f, ensure_ascii=False, indent=2)
    print(f"  JSON 저장: {json_path}")


if __name__ == "__main__":
    main()
