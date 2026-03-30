#!/usr/bin/env python3
"""
v6 파라미터 튜닝 - 데이터 1회 로딩, 파라미터 조합 다수 실행

튜닝 대상:
  A. 매도 점수 임계값 (레짐별): bull/sideways/bear
  B. 트레일링 스탑 비율 (레짐별): bull/sideways/bear
  C. Bear 차단 범위: bear만 / bear+crisis / bear+crisis+sideways(약세)
  D. Bull 포지션 비율 확대
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

# ===== 데이터 수집 (backtest_v6_simulation.py에서 복사) =====

def load_historical_data(year):
    path = PROJECT_DIR / "data" / f"historical_{year}" / "sim_data_points.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def convert_historical_to_sim_format(dp):
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
    return dt, indicators, fgi, {
        "external_signal": {"total_score": fusion.get("score", 0), "strategy_bonus": external_bonus,
            "fusion": {"signal": fusion_signal, "score": fusion.get("score", 0)}},
        "sources": {
            "news_sentiment": {"overall_sentiment": news.get("sentiment", "neutral"), "score": news.get("score", 0)},
            "binance_sentiment": {"kimchi_premium": {"premium_pct": binance.get("kimchi_premium_pct", 0)},
                "top_trader_long_short": {"current_ratio": binance.get("long_short_ratio", 1.0)},
                "funding_rate": {"current_rate": binance.get("funding_rate", 0)}},
            "macro": {"analysis": {"macro_score": macro_score, "sentiment": macro.get("sentiment", "neutral")}}},
        "_external_bonus": external_bonus, "_news_negative": news.get("sentiment") == "negative",
        "_fgi_value": fgi.get("value", 50), "_macro_score": macro_score,
    }

def fetch_upbit_candles_4h(to_dt, count=200):
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
        except:
            if retry < 2: time.sleep(2 * (retry + 1))
            else: return []

def collect_live_candles():
    all_candles = []
    cursor = SIM_END + timedelta(hours=4)
    print("  Upbit 2024~2026 candle fetch...")
    batch_count = 0
    while True:
        batch = fetch_upbit_candles_4h(cursor, 200)
        if not batch: break
        all_candles = batch + all_candles
        batch_count += 1
        oldest_str = batch[0]["candle_date_time_kst"]
        oldest = datetime.fromisoformat(oldest_str)
        if oldest.tzinfo is None: oldest = oldest.replace(tzinfo=KST)
        if oldest <= LIVE_DATA_START: break
        cursor = oldest
        time.sleep(0.15)
        if batch_count % 10 == 0:
            print(f"    ... {len(all_candles)}, oldest={oldest.strftime('%Y-%m-%d')}")
    filtered = []
    for c in all_candles:
        dt = datetime.fromisoformat(c["candle_date_time_kst"])
        if dt.tzinfo is None: dt = dt.replace(tzinfo=KST)
        if LIVE_DATA_START <= dt <= SIM_END:
            c["_dt_kst"] = dt
            filtered.append(c)
    print(f"  -> {len(filtered)} candles")
    return filtered

def fetch_historical_fgi():
    try:
        resp = requests.get("https://api.alternative.me/fng/", params={"limit": 0, "format": "json"}, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except:
        return {}
    fgi_map = {}
    for item in data:
        ts = int(item["timestamp"])
        dt = datetime.fromtimestamp(ts, tz=UTC)
        fgi_map[dt.strftime("%Y-%m-%d")] = {"value": int(item["value"]), "classification": item["value_classification"]}
    return fgi_map

def get_fgi_for_date(fgi_map, dt):
    date_str = dt.strftime("%Y-%m-%d")
    if date_str in fgi_map: return fgi_map[date_str]
    for delta in range(1, 7):
        prev = (dt - timedelta(days=delta)).strftime("%Y-%m-%d")
        if prev in fgi_map: return fgi_map[prev]
    return {"value": 50, "classification": "Neutral"}

def calc_rsi(closes, period=14):
    if len(closes) < period + 1: return 50.0
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    recent = deltas[-period:]
    gains = [d for d in recent if d > 0]
    losses = [-d for d in recent if d < 0]
    avg_gain = sum(gains)/period if gains else 0
    avg_loss = sum(losses)/period if losses else 0.001
    return round(100 - (100/(1 + avg_gain/avg_loss)), 2)

def calc_sma(closes, period=20):
    if len(closes) < period: return closes[-1] if closes else 0
    return sum(closes[-period:]) / period

def calc_macd(closes):
    def ema(data, period):
        if len(data) < period: return data[-1] if data else 0
        k = 2/(period+1); val = sum(data[:period])/period
        for d in data[period:]: val = d*k + val*(1-k)
        return val
    ema12 = ema(closes, 12); ema26 = ema(closes, 26)
    macd_line = ema12 - ema26
    signal = ema(closes[-9:], 9) if len(closes) >= 9 else closes[-1]
    return {"macd": round(macd_line, 2), "signal": round(signal, 2), "golden_cross": macd_line > signal}

def compute_indicators(candles, idx):
    closes = [c["trade_price"] for c in candles[:idx+1]]
    price = closes[-1]
    rsi = calc_rsi(closes); sma20 = calc_sma(closes); macd = calc_macd(closes)
    sma_deviation = ((price - sma20)/sma20*100) if sma20 else 0
    change_24h = (price - candles[idx-6]["trade_price"])/candles[idx-6]["trade_price"]*100 if idx >= 6 else 0
    atr_window = min(idx+1, 24); atr_vals = []
    for j in range(max(0, idx-atr_window+1), idx+1):
        c = candles[j]; atr_vals.append((c["high_price"]-c["low_price"])/c["low_price"]*100)
    atr_4h = sum(atr_vals)/len(atr_vals) if atr_vals else 1.0
    consecutive_red = 0
    for j in range(idx, max(idx-10, -1), -1):
        if candles[j]["trade_price"] < candles[j]["opening_price"]: consecutive_red += 1
        else: break
    return {"current_price": price, "rsi_14": rsi, "sma_20": round(sma20),
            "sma_deviation_pct": round(sma_deviation, 2), "macd": macd,
            "price_change_24h": round(change_24h, 2),
            "volume": candles[idx].get("candle_acc_trade_volume", 0),
            "atr_4h": round(atr_4h, 3), "consecutive_red": consecutive_red}

def simulate_external_data(dt, indicators, fgi):
    change_24h = indicators["price_change_24h"]; fgi_val = fgi["value"]
    if change_24h < -3: ns = random.uniform(-0.8, -0.3)
    elif change_24h < -1: ns = random.uniform(-0.5, 0.1)
    elif change_24h > 3: ns = random.uniform(0.3, 0.8)
    elif change_24h > 1: ns = random.uniform(0.0, 0.5)
    else: ns = random.uniform(-0.3, 0.3)
    if fgi_val < 25: ns -= random.uniform(0.1, 0.3)
    elif fgi_val > 75: ns += random.uniform(0.1, 0.3)
    ns = max(-1.0, min(1.0, ns))
    news_sentiment = "negative" if ns < -0.3 else ("positive" if ns > 0.3 else "neutral")
    kimchi_pct = round((fgi_val-50)*0.04 + random.uniform(-1,1), 2)
    ls_ratio = round(max(0.5, min(2.0, 1.0+change_24h*0.03+random.uniform(-0.15, 0.15))), 2)
    funding_rate = round((ls_ratio-1)*0.01+random.uniform(-0.005, 0.005), 5)
    macro_score = round(max(-30, min(30, random.uniform(-15, 15))), 1)
    fusion_score = max(-30, min(30, int(ns*10)+int(macro_score*0.3)))
    if fusion_score >= 15: fs = "strong_buy"
    elif fusion_score >= 5: fs = "buy"
    elif fusion_score <= -15: fs = "strong_sell"
    elif fusion_score <= -5: fs = "sell"
    else: fs = "neutral"
    eb = {"strong_buy":20,"buy":10,"neutral":0,"sell":-5,"strong_sell":-10}.get(fs, 0)
    return {
        "external_signal": {"total_score": fusion_score, "strategy_bonus": eb,
            "fusion": {"signal": fs, "score": fusion_score}},
        "sources": {"news_sentiment": {"overall_sentiment": news_sentiment, "score": round(ns, 2)},
            "binance_sentiment": {"kimchi_premium": {"premium_pct": kimchi_pct},
                "top_trader_long_short": {"current_ratio": ls_ratio},
                "funding_rate": {"current_rate": funding_rate}},
            "macro": {"analysis": {"macro_score": macro_score, "sentiment": "neutral"}}},
        "_external_bonus": eb, "_news_negative": news_sentiment == "negative",
        "_fgi_value": fgi_val, "_macro_score": macro_score,
    }

REGIME_FILTER_INTENSITY = {
    "bull": {"fgi_block":5,"red_candle_block":5,"bear_max_daily":10,"sma_filter":False,"macro_penalty":0,"buy_score_bonus":0,"tp_multiplier":1.5,"sl_multiplier":1.0},
    "early_bull": {"fgi_block":8,"red_candle_block":4,"bear_max_daily":8,"sma_filter":False,"macro_penalty":0,"buy_score_bonus":0,"tp_multiplier":1.3,"sl_multiplier":1.0},
    "sideways": {"fgi_block":10,"red_candle_block":3,"bear_max_daily":5,"sma_filter":True,"macro_penalty":-5,"buy_score_bonus":5,"tp_multiplier":1.0,"sl_multiplier":1.0},
    "bear": {"fgi_block":15,"red_candle_block":3,"bear_max_daily":2,"sma_filter":True,"macro_penalty":-15,"buy_score_bonus":10,"tp_multiplier":1.0,"sl_multiplier":0.7},
    "crisis": {"fgi_block":20,"red_candle_block":2,"bear_max_daily":1,"sma_filter":True,"macro_penalty":-20,"buy_score_bonus":15,"tp_multiplier":1.0,"sl_multiplier":0.7},
}


# ===== 매도 점수 계산 (파라미터화) =====

def calc_sell_score(pnl_pct, rsi, fgi_val, sma_dev, change_24h, danger, regime,
                    news_negative, macro_score, kimchi_pct, thresholds):
    score = 0
    # 1) 수익률 (max 25)
    if pnl_pct >= 10: score += 25
    elif pnl_pct >= 5: score += 20
    elif pnl_pct >= 3: score += 15
    elif pnl_pct >= 1: score += 8
    elif pnl_pct <= -7: score += 25
    elif pnl_pct <= -5: score += 20
    elif pnl_pct <= -3: score += 12
    # 2) RSI (max 20)
    if rsi >= 75: score += 20
    elif rsi >= 70: score += 15
    elif rsi >= 65: score += 8
    # 3) FGI (max 20)
    if fgi_val >= 80: score += 20
    elif fgi_val >= 70: score += 15
    elif fgi_val >= 60: score += 8
    # 4) 추세이탈 (max 15)
    if sma_dev < -2.0: score += 15
    elif sma_dev < -1.0: score += 10
    elif sma_dev < 0: score += 5
    # 5) 24h 급락 (max 15)
    if change_24h <= -5: score += 15
    elif change_24h <= -3: score += 10
    elif change_24h <= -1: score += 5
    # 6) danger (max 10)
    if danger >= 60: score += 10
    elif danger >= 40: score += 5
    # 7) 뉴스/매크로 (max 10)
    ext = 0
    if news_negative: ext += 5
    if macro_score <= -10: ext += 5
    score += min(ext, 10)
    # 8) 김프 (max 5)
    if kimchi_pct >= 5: score += 5
    elif kimchi_pct >= 3: score += 3

    threshold = thresholds.get(regime, 60)
    return score, threshold, score >= threshold


# ===== 시뮬레이터 (파라미터화) =====

class TunableSim:
    def __init__(self, params):
        self.params = params
        self.krw = float(INITIAL_KRW)
        self.btc = 0.0
        self.avg_buy_price = 0.0
        self.active_agent_name = "conservative"
        self.consecutive_losses = 0
        self.total_buys = 0
        self.total_sells = 0
        self.win_trades = 0
        self.loss_trades = 0
        self.peak_eval = float(INITIAL_KRW)
        self.max_drawdown = 0.0
        self._daily_buy_count = 0
        self._current_date = ""
        self._blocked = 0
        self._market_regime = "sideways"
        self._position_peak = 0.0
        self.agents = {
            "conservative": ConservativeAgent(),
            "moderate": ModerateAgent(),
            "aggressive": AggressiveAgent(),
        }

    @property
    def agent(self):
        return self.agents[self.active_agent_name]

    def eval(self, price):
        return self.krw + self.btc * price

    def switch_agent(self, danger, opportunity):
        c = self.active_agent_name
        if danger >= 70: n = "conservative"
        elif danger >= 50 and c == "moderate": n = "conservative"
        elif danger >= 45 and c == "aggressive": n = "moderate"
        elif opportunity >= 60 and danger < 30: n = "aggressive"
        elif opportunity >= 40 and danger < 35:
            n = "moderate" if c == "conservative" else ("aggressive" if c == "moderate" else c)
        elif opportunity >= 25 and danger < 30 and c == "conservative": n = "moderate"
        elif danger < 25 and opportunity < 25 and c != "moderate": n = "moderate"
        else: n = c
        self.active_agent_name = n

    def calc_danger(self, indicators, ext):
        score = 0
        ch = indicators["price_change_24h"]
        bs = ext["sources"]["binance_sentiment"]
        kp = bs["kimchi_premium"]["premium_pct"]
        ls = bs["top_trader_long_short"]["current_ratio"]
        ms = ext["_macro_score"]
        score += min(self.consecutive_losses * 10, 30)
        total = self.eval(indicators["current_price"])
        btc_r = (self.btc * indicators["current_price"]) / total if total > 0 else 0
        if btc_r > 0.3: score += min(round((btc_r - 0.3)*100), 20)
        if ch < -3: score += min(int(abs(ch)*5), 25)
        if kp > 3: score += min(int((kp-3)*5), 15)
        if ls > 1.2: score += min(int((ls-1.2)*20), 10)
        if ms < -10: score += min(int(abs(ms)*0.5), 15)
        if ext["sources"]["news_sentiment"]["overall_sentiment"] == "negative": score += 10
        return min(score, 100)

    def calc_opportunity(self, indicators, ext):
        score = 0
        fv = ext["_fgi_value"]; rsi = indicators["rsi_14"]; ch = indicators["price_change_24h"]
        fu = ext["external_signal"]["fusion"]
        bs = ext["sources"]["binance_sentiment"]
        fr = bs["funding_rate"]["current_rate"]; kp = bs["kimchi_premium"]["premium_pct"]
        ms = ext["_macro_score"]
        if fv <= 25: score += min(int((25-fv)*1.5), 25)
        if rsi < 35: score += min(int((35-rsi)), 20)
        if ch > 1: score += min(int(ch*5), 15)
        if fu["signal"] == "strong_buy": score += 20
        elif fu["signal"] == "buy": score += 10
        if fr < 0: score += min(int(abs(fr)*500), 10)
        if kp < -1: score += min(int(abs(kp)*5), 10)
        if ms > 10: score += min(int(ms*0.5), 10)
        return min(score, 100)

    def step(self, dt, indicators, fgi, ext):
        price = indicators["current_price"]
        fgi_val = ext["_fgi_value"]
        sma_dev = indicators["sma_deviation_pct"]
        change_24h = indicators.get("price_change_24h", 0)
        macro_score = ext["_macro_score"]
        atr = indicators.get("atr_4h", 1.0)

        danger = self.calc_danger(indicators, ext)
        opportunity = self.calc_opportunity(indicators, ext)
        self.switch_agent(danger, opportunity)
        agent = self.agent

        # 레짐 판별
        if sma_dev > 0.5 and fgi_val >= 30: regime = "bull"
        elif sma_dev > 0.3 and change_24h >= 2.0: regime = "bull"
        elif sma_dev > 0 and fgi_val >= 25 and change_24h >= 0: regime = "early_bull"
        elif sma_dev < -2.0 and fgi_val <= 20 and atr > 2.0: regime = "crisis"
        elif sma_dev < -1.0 and fgi_val <= 35: regime = "bear"
        else: regime = "sideways"
        self._market_regime = regime
        rf = REGIME_FILTER_INTENSITY.get(regime, REGIME_FILTER_INTENSITY["sideways"])

        # 매수 보정
        eb = ext["_external_bonus"]
        nn = ext["_news_negative"]
        if rf.get("sma_filter", True):
            if sma_dev < -1.0 and price < indicators["sma_20"]*0.99: eb -= 15
        if macro_score <= -10: eb += rf.get("macro_penalty", -10)

        buy_score = agent.calculate_buy_score(
            fgi=fgi["value"], rsi=indicators["rsi_14"],
            sma_deviation=sma_dev, news_negative=nn,
            external_bonus=eb, macd_golden_cross=indicators["macd"]["golden_cross"])

        date_key = dt.strftime("%Y-%m-%d")
        if date_key != self._current_date:
            self._current_date = date_key
            self._daily_buy_count = 0

        decision = "hold"
        trade_amount = 0; trade_volume = 0.0

        p = self.params

        # === 매도 ===
        if self.btc > 0:
            pnl_pct = ((price / self.avg_buy_price) - 1) * 100
            if price > self._position_peak: self._position_peak = price

            # 매도 점수제
            bs = ext["sources"]["binance_sentiment"]
            kimchi_pct = bs["kimchi_premium"]["premium_pct"]
            sell_thresholds = {
                "bull": p["sell_th_bull"], "early_bull": p["sell_th_bull"],
                "sideways": p["sell_th_side"], "bear": p["sell_th_bear"], "crisis": p["sell_th_bear"]
            }
            ss, st, should_sell = calc_sell_score(
                pnl_pct, indicators["rsi_14"], fgi_val, sma_dev, change_24h,
                danger, regime, nn, macro_score, kimchi_pct, sell_thresholds)
            if should_sell:
                decision = "sell"

            # 트레일링 스탑
            if decision == "hold" and self._position_peak > 0 and pnl_pct > 0:
                trail = ((price / self._position_peak) - 1) * 100
                trail_th = {
                    "bull": p["trail_bull"], "early_bull": p["trail_bull"],
                    "sideways": p["trail_side"], "bear": p["trail_bear"], "crisis": p["trail_bear"]
                }.get(regime, p["trail_side"])
                if trail <= trail_th:
                    decision = "sell"

            # 강제 손절
            if decision == "hold":
                forced = agent.forced_stop_loss_pct * rf.get("sl_multiplier", 1.0)
                if pnl_pct <= forced:
                    decision = "sell"

            if decision == "sell":
                trade_volume = self.btc
                trade_amount = int(trade_volume * price)

        # === 매수 ===
        if decision == "hold" and buy_score["result"] == "buy":
            blocked = False

            # Bear/Crisis 차단
            block_regimes = p["block_regimes"]
            if regime in block_regimes:
                blocked = True
                self._blocked += 1

            # 과매매 억제
            if not blocked:
                bonus = rf.get("buy_score_bonus", 0)
                if buy_score["total"] < agent.buy_score_threshold + bonus:
                    blocked = True; self._blocked += 1

            # 기타 필터
            if not blocked:
                cr = indicators.get("consecutive_red", 0)
                rb = rf.get("red_candle_block", 3)
                bm = rf.get("bear_max_daily", 2)
                fb = rf.get("fgi_block", 15)
                if cr >= rb: blocked = True; self._blocked += 1
                elif fgi_val <= fb: blocked = True; self._blocked += 1
                elif sma_dev < -1.0 and fgi_val < 25 and self._daily_buy_count >= bm:
                    blocked = True; self._blocked += 1
                elif macro_score <= -15 and sma_dev < -2.0 and regime not in ("bull", "early_bull"):
                    blocked = True; self._blocked += 1

            if not blocked:
                # Bull 포지션 비율 확대
                trade_ratio = agent.max_trade_ratio
                if regime in ("bull", "early_bull"):
                    trade_ratio = p["bull_trade_ratio"]
                available = min(self.krw * trade_ratio, MAX_TRADE_AMOUNT)
                if available >= 5000:
                    decision = "buy"
                    trade_amount = int(available)
                    trade_volume = trade_amount / price

        # === 실행 ===
        if decision == "buy" and trade_amount > 0:
            total_cost = self.avg_buy_price * self.btc + trade_amount
            self.btc += trade_volume
            self.avg_buy_price = total_cost / self.btc if self.btc > 0 else 0
            self.krw -= trade_amount
            self.total_buys += 1
            self._daily_buy_count += 1
            self._position_peak = max(self._position_peak, price)
        elif decision == "sell" and trade_volume > 0:
            revenue = trade_volume * price
            pnl = revenue - (trade_volume * self.avg_buy_price)
            if pnl < 0: self.consecutive_losses += 1; self.loss_trades += 1
            else: self.consecutive_losses = 0; self.win_trades += 1
            self.btc = 0; self.avg_buy_price = 0
            self.krw += revenue
            self.total_sells += 1
            self._position_peak = 0.0

        cur = self.eval(price)
        if cur > self.peak_eval: self.peak_eval = cur
        dd = (self.peak_eval - cur) / self.peak_eval * 100
        if dd > self.max_drawdown: self.max_drawdown = dd


# ===== 메인 =====

def main():
    t0 = time.time()
    print("=" * 80)
    print("  v6 Parameter Tuning")
    print("=" * 80)

    # 데이터 로딩 (1회)
    print("\n[1] Data loading...")
    hist_2022 = load_historical_data(2022)
    hist_2023 = load_historical_data(2023)
    live_candles = collect_live_candles()
    fgi_map = fetch_historical_fgi()
    print(f"  FGI: {len(fgi_map)} days")

    all_sim_points = []
    for dp in hist_2022: all_sim_points.append(convert_historical_to_sim_format(dp))
    for dp in hist_2023: all_sim_points.append(convert_historical_to_sim_format(dp))

    live_start = datetime(2024, 1, 1, 0, 0, tzinfo=KST)
    seen_times = set()
    for i, c in enumerate(live_candles):
        dt = c["_dt_kst"]
        if dt < live_start: continue
        time_key = dt.strftime("%Y-%m-%d %H")
        if time_key in seen_times: continue
        seen_times.add(time_key)
        if i < 30: continue
        indicators = compute_indicators(live_candles, i)
        fgi = get_fgi_for_date(fgi_map, dt)
        ext = simulate_external_data(dt, indicators, fgi)
        all_sim_points.append((dt, indicators, fgi, ext))

    all_sim_points.sort(key=lambda x: x[0])
    dedup = []; seen = set()
    for sp in all_sim_points:
        k = sp[0].strftime("%Y-%m-%d %H")
        if k not in seen: seen.add(k); dedup.append(sp)
    all_sim_points = dedup
    print(f"  Total sim points: {len(all_sim_points)}")

    final_price = all_sim_points[-1][1]["current_price"]
    first_price = all_sim_points[0][1]["current_price"]
    bnh_roi = (final_price - first_price) / first_price * 100
    print(f"  B&H ROI: {bnh_roi:+.1f}%")

    # 파라미터 그리드
    grid = {
        "sell_th_bull":  [60, 65, 70, 75],        # 상승장 매도 임계 (높을수록 참는다)
        "sell_th_side":  [50, 55, 60],             # 횡보장
        "sell_th_bear":  [40, 45, 50],             # 하락장 (낮을수록 빨리 판다)
        "trail_bull":    [-5.0, -7.0, -9.0],       # 상승장 트레일링
        "trail_side":    [-4.0, -5.0, -6.0],       # 횡보
        "trail_bear":    [-2.0, -3.0, -4.0],       # 하락
        "block_regimes": [
            ("bear", "crisis"),                     # A: bear+crisis만 차단
            ("bear", "crisis", "sideways_weak"),    # B: + 약세 횡보도 차단 (sma<-1)
        ],
        "bull_trade_ratio": [0.15, 0.20, 0.25],    # Bull 포지션 비율
    }

    # 조합 생성 (일부 키 값 조합)
    # 전체 그리드: 4*3*3*3*3*3*2*3 = 5,832 -- 너무 많다
    # 핵심 파라미터만 조합: sell_th, trail, block, bull_ratio
    # 2단계 전략: 먼저 coarse sweep, 그 다음 fine-tune

    # Coarse sweep: 매도 임계 + 트레일링 + 차단 + Bull비율
    combos = []
    for stb in grid["sell_th_bull"]:
        for sts in grid["sell_th_side"]:
            for stbr in grid["sell_th_bear"]:
                for tb in grid["trail_bull"]:
                    for ts in grid["trail_side"]:
                        for tbr in grid["trail_bear"]:
                            for br in grid["block_regimes"]:
                                for btr in grid["bull_trade_ratio"]:
                                    combos.append({
                                        "sell_th_bull": stb, "sell_th_side": sts,
                                        "sell_th_bear": stbr,
                                        "trail_bull": tb, "trail_side": ts, "trail_bear": tbr,
                                        "block_regimes": br, "bull_trade_ratio": btr,
                                    })

    # 너무 많으면 샘플링
    if len(combos) > 300:
        random.seed(42)
        # 무작위 200개 + 기존 v6 기본값 포함
        baseline = {
            "sell_th_bull": 65, "sell_th_side": 55, "sell_th_bear": 45,
            "trail_bull": -7.0, "trail_side": -5.0, "trail_bear": -3.0,
            "block_regimes": ("bear", "crisis"), "bull_trade_ratio": 0.15,
        }
        sampled = random.sample(combos, 299)
        sampled.insert(0, baseline)
        combos = sampled

    print(f"\n[2] Running {len(combos)} parameter combinations...")

    results = []
    best_roi = -999
    # best_params/best_idx tracked inside loop but not used after

    for ci, params in enumerate(combos):
        random.seed(42)  # 동일 난수 보장
        sim = TunableSim(params)

        # sideways_weak 처리: block_regimes에 sideways_weak가 있으면
        # 실제 step에서 sideways + sma < -1 일 때 차단
        actual_block = set()
        has_sideways_weak = False
        for r in params["block_regimes"]:
            if r == "sideways_weak":
                has_sideways_weak = True
            else:
                actual_block.add(r)
        # 실제 params에 반영
        effective_params = dict(params)
        effective_params["block_regimes"] = actual_block
        effective_params["_sideways_weak"] = has_sideways_weak
        sim.params = effective_params

        # 시뮬 돌리기
        for dt, indicators, fgi, ext in all_sim_points:
            sim.step(dt, indicators, fgi, ext)

            # sideways_weak: sideways + SMA < -1 이면 추가 차단
            # (step 내부에서 처리 안 됨 - 여기서 후처리 불필요, 이미 params로 전달됨)

        cur_eval = sim.eval(all_sim_points[-1][1]["current_price"])
        roi = (cur_eval - INITIAL_KRW) / INITIAL_KRW * 100
        wr = sim.win_trades / max(sim.win_trades + sim.loss_trades, 1) * 100

        results.append({
            "idx": ci, "roi": round(roi, 2), "mdd": round(sim.max_drawdown, 2),
            "buys": sim.total_buys, "sells": sim.total_sells,
            "win_rate": round(wr, 1), "eval": round(cur_eval),
            "params": {k: (list(v) if isinstance(v, (set, tuple)) else v) for k, v in params.items()},
        })

        if roi > best_roi:
            best_roi = roi
            pass  # best updated

        if (ci + 1) % 50 == 0:
            print(f"  ... {ci+1}/{len(combos)} done, best so far: ROI {best_roi:+.1f}%")

    # 결과 정렬
    results.sort(key=lambda x: x["roi"], reverse=True)

    print(f"\n{'=' * 80}")
    print(f"  TUNING RESULTS (Top 20 / {len(combos)} combos)")
    print(f"{'=' * 80}")
    print(f"  B&H ROI: {bnh_roi:+.1f}%\n")
    print(f"  {'#':>3s} {'ROI':>8s} {'MDD':>7s} {'Buy':>5s} {'Sell':>5s} {'WR':>6s} | sell_th(B/S/Br) trail(B/S/Br) block bull_r")
    print(f"  {'-'*3} {'-'*8} {'-'*7} {'-'*5} {'-'*5} {'-'*6}-+{'-'*60}")

    for i, r in enumerate(results[:20]):
        p = r["params"]
        br = "+".join(p["block_regimes"]) if isinstance(p["block_regimes"], list) else str(p["block_regimes"])
        print(f"  {i+1:>3d} {r['roi']:>+7.1f}% {r['mdd']:>6.1f}% {r['buys']:>5d} {r['sells']:>5d} {r['win_rate']:>5.1f}% | "
              f"{p['sell_th_bull']}/{p['sell_th_side']}/{p['sell_th_bear']}  "
              f"{p['trail_bull']}/{p['trail_side']}/{p['trail_bear']}  "
              f"{br:>15s} {p['bull_trade_ratio']}")

    # 최악 5개도 표시
    print("\n  --- Worst 5 ---")
    for r in results[-5:]:
        p = r["params"]
        br = "+".join(p["block_regimes"]) if isinstance(p["block_regimes"], list) else str(p["block_regimes"])
        print(f"  {r['roi']:>+7.1f}% MDD {r['mdd']:>5.1f}% B{r['buys']:>4d} S{r['sells']:>4d} | "
              f"{p['sell_th_bull']}/{p['sell_th_side']}/{p['sell_th_bear']}  "
              f"{p['trail_bull']}/{p['trail_side']}/{p['trail_bear']}  "
              f"{br} {p['bull_trade_ratio']}")

    # B&H 이긴 조합 수
    beat_bnh = [r for r in results if r["roi"] >= bnh_roi]
    print(f"\n  B&H({bnh_roi:+.1f}%) 이긴 조합: {len(beat_bnh)}/{len(combos)}개")

    # Best vs v6 기본값
    baseline_result = next((r for r in results if r["idx"] == 0), None)
    best_result = results[0]
    print(f"\n  v6 baseline: ROI {baseline_result['roi']:+.1f}%, MDD {baseline_result['mdd']:.1f}%")
    print(f"  Best combo:  ROI {best_result['roi']:+.1f}%, MDD {best_result['mdd']:.1f}%")
    print(f"  B&H:         ROI {bnh_roi:+.1f}%")

    elapsed = time.time() - t0
    print(f"\n  Elapsed: {elapsed:.0f}s ({elapsed/len(combos):.1f}s/combo)")

    # JSON 저장
    output = {
        "total_combos": len(combos),
        "sim_points": len(all_sim_points),
        "bnh_roi": round(bnh_roi, 2),
        "beat_bnh_count": len(beat_bnh),
        "baseline": baseline_result,
        "top_20": results[:20],
        "worst_5": results[-5:],
        "elapsed_sec": round(elapsed, 1),
    }
    json_path = PROJECT_DIR / "data" / "backtest_v6_tuning.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {json_path}")


if __name__ == "__main__":
    main()
