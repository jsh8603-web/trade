#!/usr/bin/env python3
"""
2022~2026 전체 기간 통합 백테스트 + 종합 보고서

데이터 소스:
  - 2022년: data/historical_2022/sim_data_points.json (로컬)
  - 2023년: data/historical_2023/sim_data_points.json (로컬)
  - 2024~2026: Upbit API 실시간 수집 + FGI + 외부 시뮬레이션

출력:
  - 콘솔 보고서
  - data/backtest_full_report.txt (텍스트)
  - data/backtest_full_results.json (JSON)
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

# ── 설정 ──
INITIAL_KRW = 1_000_000
MAX_TRADE_AMOUNT = 500_000

SIM_START = datetime(2022, 1, 1, 0, 0, tzinfo=KST)
SIM_END = datetime(2026, 3, 21, 23, 59, tzinfo=KST)
LIVE_DATA_START = datetime(2023, 12, 15, 0, 0, tzinfo=KST)  # API에서 가져올 시작

random.seed(42)


# =====================================================
#  Phase 1: 히스토리컬 데이터 로드 (2022, 2023)
# =====================================================

def load_historical_data(year: int) -> list[dict]:
    """로컬 JSON에서 히스토리컬 시뮬 데이터를 로드한다."""
    path = PROJECT_DIR / "data" / f"historical_{year}" / "sim_data_points.json"
    if not path.exists():
        print(f"  ! {path} 없음")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  {year}년: {len(data)}개 로드")
    return data


def convert_historical_to_sim_format(dp: dict) -> tuple[datetime, dict, dict, dict]:
    """히스토리컬 데이터포인트를 시뮬레이터 입력 형식으로 변환."""
    dt = datetime.fromisoformat(dp["datetime"])
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)

    indicators = dp["indicators"]
    fgi = dp["fgi"]
    ext = dp.get("external", {})

    # 외부 데이터를 시뮬레이터가 기대하는 형식으로 매핑
    news = ext.get("news", {})
    whale = ext.get("whale", {})
    sns = ext.get("sns", {})
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
            "news_sentiment": {
                "overall_sentiment": news.get("sentiment", "neutral"),
                "score": news.get("score", 0),
            },
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


# =====================================================
#  Phase 2: Upbit API 데이터 수집 (2024~2026)
# =====================================================

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
    """2023-12-15 ~ 2026-03-21 Upbit 4시간봉 수집."""
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

    # 기간 필터 + datetime 파싱
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
    """전체 FGI 히스토리."""
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
    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    macd_line = ema12 - ema26
    signal = ema(closes[-9:], 9) if len(closes) >= 9 else closes[-1]
    return {"macd": round(macd_line, 2), "signal": round(signal, 2), "golden_cross": macd_line > signal}


def compute_indicators(candles: list[dict], idx: int) -> dict:
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
    return {
        "current_price": price,
        "rsi_14": rsi,
        "sma_20": round(sma20),
        "sma_deviation_pct": round(sma_deviation, 2),
        "macd": macd,
        "price_change_24h": round(change_24h, 2),
        "volume": candles[idx].get("candle_acc_trade_volume", 0),
    }


def simulate_external_data(dt: datetime, indicators: dict, fgi: dict) -> dict:
    price = indicators["current_price"]
    rsi = indicators["rsi_14"]
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
#  시뮬레이터
# =====================================================

class TradingSimulator:
    def __init__(self, initial_krw: int):
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
            self.switch_count += 1

        agent = self.agent
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

        # 매도 조건
        if self.btc > 0:
            pnl_pct = ((price / self.avg_buy_price) - 1) * 100
            if pnl_pct >= agent.target_profit_pct:
                decision = "sell"
                reason = f"target {pnl_pct:.1f}% >= {agent.target_profit_pct}%"
            elif pnl_pct <= agent.forced_stop_loss_pct:
                decision = "sell"
                reason = f"forced_stop {pnl_pct:.1f}%"
            elif pnl_pct <= agent.stop_loss_pct and danger >= 50:
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
            available = min(self.krw * agent.max_trade_ratio, MAX_TRADE_AMOUNT)
            if available >= 5000:
                decision = "buy"
                trade_amount = int(available)
                trade_volume = trade_amount / price
                reason = f"score {buy_score['total']}>={agent.buy_score_threshold}"

        if decision == "hold":
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

        # drawdown
        current_eval = self.krw + self.btc * price
        if current_eval > self.peak_eval:
            self.peak_eval = current_eval
        dd = (self.peak_eval - current_eval) / self.peak_eval * 100
        if dd > self.max_drawdown:
            self.max_drawdown = dd

        # yearly end_eval 갱신
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
    p("  BTC 자동매매 전체 기간 백테스트 보고서")
    p(f"  기간: {SIM_START.strftime('%Y-%m-%d')} ~ {SIM_END.strftime('%Y-%m-%d')}")
    p(f"  초기자금: {INITIAL_KRW:,}원 / 1회 상한: {MAX_TRADE_AMOUNT:,}원")
    p("=" * 70)

    # ── 데이터 수집 ──
    p("\n[Phase 1] 데이터 수집")

    # 2022, 2023 로컬 데이터
    hist_2022 = load_historical_data(2022)
    hist_2023 = load_historical_data(2023)

    # 2024~2026 Upbit API
    live_candles = collect_live_candles()
    fgi_map = fetch_historical_fgi()
    p(f"  FGI: {len(fgi_map)}일")

    # ── 시뮬레이션 포인트 조립 ──
    p("\n[Phase 2] 시뮬레이션 포인트 조립")

    # 모든 데이터를 (dt, indicators, fgi, ext) 튜플로 통합
    all_sim_points: list[tuple[datetime, dict, dict, dict]] = []

    # 2022
    for dp in hist_2022:
        all_sim_points.append(convert_historical_to_sim_format(dp))
    p(f"  2022년: {len(hist_2022)}개")

    # 2023
    for dp in hist_2023:
        all_sim_points.append(convert_historical_to_sim_format(dp))
    p(f"  2023년: {len(hist_2023)}개")

    # 2024~2026 (Upbit 캔들에서 시뮬레이션 포인트 생성)
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

    # 시간순 정렬
    all_sim_points.sort(key=lambda x: x[0])

    # 중복 제거 (같은 시간대)
    deduplicated = []
    seen = set()
    for sp in all_sim_points:
        key = sp[0].strftime("%Y-%m-%d %H")
        if key not in seen:
            seen.add(key)
            deduplicated.append(sp)
    all_sim_points = deduplicated

    p(f"  총 시뮬레이션 포인트: {len(all_sim_points)}개")
    p(f"  기간: {all_sim_points[0][0].strftime('%Y-%m-%d')} ~ {all_sim_points[-1][0].strftime('%Y-%m-%d')}")

    # ── 시뮬레이션 실행 ──
    p("\n[Phase 3] 시뮬레이션 실행")
    sim = TradingSimulator(INITIAL_KRW)
    all_results = []

    for step_i, (dt, indicators, fgi, ext) in enumerate(all_sim_points):
        result = sim.step(dt, indicators, fgi, ext)
        all_results.append(result)
        if (step_i + 1) % 1000 == 0:
            p(f"  ... {step_i + 1}/{len(all_sim_points)} "
              f"({dt.strftime('%Y-%m')}, eval={result['eval']:,}원, agent={result['agent']})")

    # ── 최종 포트폴리오 ──
    final_price = all_sim_points[-1][1]["current_price"]
    port = sim.get_portfolio(final_price)
    total_eval = port["total_eval"]
    roi = (total_eval - INITIAL_KRW) / INITIAL_KRW * 100
    win_rate = (sim.win_trades / (sim.win_trades + sim.loss_trades) * 100) if (sim.win_trades + sim.loss_trades) > 0 else 0

    # BTC 가격 변동 (Buy & Hold 비교)
    first_price = all_sim_points[0][1]["current_price"]
    btc_bnh_roi = (final_price - first_price) / first_price * 100

    # ── 보고서 출력 ──
    p("\n" + "=" * 70)
    p("  종합 성과 요약")
    p("=" * 70)

    p(f"\n  BTC 가격: {first_price:,.0f}원 -> {final_price:,.0f}원 ({btc_bnh_roi:+.1f}%)")
    p(f"  초기자금: {INITIAL_KRW:,}원")
    p(f"  최종평가: {total_eval:,.0f}원")
    p(f"  수익률(ROI): {roi:+.1f}%")
    p(f"  BTC 단순보유(B&H) 대비: {roi - btc_bnh_roi:+.1f}%p")
    p(f"  최대낙폭(MDD): -{sim.max_drawdown:.1f}%")

    p(f"\n  총 거래: {sim.total_trades}회 (매수 {sim.total_buys}, 매도 {sim.total_sells})")
    p(f"  관망: {sim.total_holds}회")
    p(f"  승률: {win_rate:.1f}% ({sim.win_trades}승 {sim.loss_trades}패)")
    p(f"  에이전트 전환: {sim.switch_count}회")

    # ── 연도별 분석 ──
    p(f"\n{'=' * 70}")
    p("  연도별 성과")
    p(f"{'=' * 70}")
    p(f"  {'연도':>6s} | {'매수':>4s} | {'매도':>4s} | {'관망':>5s} | {'실현손익':>12s} | {'평가액':>14s} | {'연간ROI':>8s}")
    p(f"  {'-'*6}-+-{'-'*4}-+-{'-'*4}-+-{'-'*5}-+-{'-'*12}-+-{'-'*14}-+-{'-'*8}")

    for year in sorted(sim.yearly_stats.keys()):
        ys = sim.yearly_stats[year]
        start = ys.get("start_eval", INITIAL_KRW)
        end = ys.get("end_eval", start)
        yr_roi = ((end - start) / start * 100) if start > 0 else 0
        p(f"  {year:>6s} | {ys['buys']:>4d} | {ys['sells']:>4d} | {ys['holds']:>5d} | "
          f"{ys['pnl']:>+12,.0f} | {end:>14,.0f} | {yr_roi:>+7.1f}%")

    # ── 월별 분석 (각 연도) ──
    for year in sorted(sim.yearly_stats.keys()):
        year_months = sorted([m for m in sim.monthly_stats.keys() if m.startswith(year)])
        if not year_months:
            continue

        p(f"\n  --- {year}년 월별 ---")
        p(f"  {'월':>7s} | {'매수':>3s} | {'매도':>3s} | {'손익':>10s} | {'평가액':>12s}")
        p(f"  {'-'*7}-+-{'-'*3}-+-{'-'*3}-+-{'-'*10}-+-{'-'*12}")
        for m in year_months:
            ms = sim.monthly_stats[m]
            p(f"  {m:>7s} | {ms['buys']:>3d} | {ms['sells']:>3d} | "
              f"{ms['pnl']:>+10,.0f} | {ms['end_eval']:>12,.0f}")

    # ── 주요 거래 하이라이트 ──
    p(f"\n{'=' * 70}")
    p("  주요 거래 하이라이트 (TOP 10 수익 / TOP 5 손실)")
    p(f"{'=' * 70}")

    profit_trades = sorted([t for t in sim.trade_log if t["decision"] == "sell" and t["pnl"] > 0],
                           key=lambda x: x["pnl"], reverse=True)[:10]
    loss_trades = sorted([t for t in sim.trade_log if t["decision"] == "sell" and t["pnl"] < 0],
                         key=lambda x: x["pnl"])[:5]

    if profit_trades:
        p("\n  [수익 TOP 10]")
        for t in profit_trades:
            p(f"    {t['dt'][:10]} | +{t['pnl']:>8,}원 | {t['price']:>12,}원 | {t['agent']} | {t['reason']}")

    if loss_trades:
        p("\n  [손실 TOP 5]")
        for t in loss_trades:
            p(f"    {t['dt'][:10]} | {t['pnl']:>8,}원 | {t['price']:>12,}원 | {t['agent']} | {t['reason']}")

    # ── 에이전트별 통계 ──
    p(f"\n{'=' * 70}")
    p("  에이전트별 거래 분포")
    p(f"{'=' * 70}")

    agent_stats = {}
    for r in all_results:
        an = r["agent"]
        if an not in agent_stats:
            agent_stats[an] = {"count": 0, "buys": 0, "sells": 0, "holds": 0}
        agent_stats[an]["count"] += 1
        if r["decision"] == "buy":
            agent_stats[an]["buys"] += 1
        elif r["decision"] == "sell":
            agent_stats[an]["sells"] += 1
        else:
            agent_stats[an]["holds"] += 1

    for an in ["conservative", "moderate", "aggressive"]:
        if an not in agent_stats:
            continue
        s = agent_stats[an]
        pct = s["count"] / len(all_results) * 100
        p(f"  {an:>12s}: {s['count']:>5d}회 ({pct:>5.1f}%) | 매수 {s['buys']} | 매도 {s['sells']} | 관망 {s['holds']}")

    # ── 시장 구간별 분석 ──
    p(f"\n{'=' * 70}")
    p("  시장 구간별 성과")
    p(f"{'=' * 70}")

    # 주요 시장 이벤트 구간
    market_phases = [
        ("2022-01~06 크립토 겨울 (LUNA/UST)", "2022-01", "2022-06"),
        ("2022-07~12 FTX 붕괴 + 바닥", "2022-07", "2022-12"),
        ("2023-01~06 회복 랠리", "2023-01", "2023-06"),
        ("2023-07~12 ETF 기대 랠리", "2023-07", "2023-12"),
        ("2024-01~06 ETF 승인 + 반감기", "2024-01", "2024-06"),
        ("2024-07~12 사상최고가 랠리", "2024-07", "2024-12"),
        ("2025-01~06 고점 이후", "2025-01", "2025-06"),
        ("2025-07~2026-03 현재", "2025-07", "2026-03"),
    ]

    for name, start_m, end_m in market_phases:
        phase_months = [m for m in sim.monthly_stats.keys() if start_m <= m <= end_m]
        if not phase_months:
            continue
        phase_buys = sum(sim.monthly_stats[m]["buys"] for m in phase_months)
        phase_sells = sum(sim.monthly_stats[m]["sells"] for m in phase_months)
        phase_pnl = sum(sim.monthly_stats[m]["pnl"] for m in phase_months)
        first_m = sorted(phase_months)[0]
        last_m = sorted(phase_months)[-1]
        start_eval = sim.monthly_stats[first_m].get("start_eval", 0)
        end_eval = sim.monthly_stats[last_m].get("end_eval", 0)
        phase_roi = ((end_eval - start_eval) / start_eval * 100) if start_eval > 0 else 0

        p(f"\n  [{name}]")
        p(f"    매수 {phase_buys}회, 매도 {phase_sells}회 | 실현손익: {phase_pnl:+,.0f}원 | 구간ROI: {phase_roi:+.1f}%")

    # ── FGI 구간별 성과 ──
    p(f"\n{'=' * 70}")
    p("  FGI 구간별 매수 성과")
    p(f"{'=' * 70}")

    fgi_ranges = [
        ("극공포 (0-20)", 0, 20),
        ("공포 (21-40)", 21, 40),
        ("중립 (41-60)", 41, 60),
        ("탐욕 (61-80)", 61, 80),
        ("극탐욕 (81-100)", 81, 100),
    ]

    buy_results = [r for r in all_results if r["decision"] == "buy"]
    for name, lo, hi in fgi_ranges:
        range_buys = [r for r in buy_results if lo <= r["fgi"] <= hi]
        p(f"  {name:>16s}: {len(range_buys):>4d}회 매수")

    # ── 결론 ──
    p(f"\n{'=' * 70}")
    p("  결론")
    p(f"{'=' * 70}")

    if roi > 0 and roi > btc_bnh_roi:
        verdict = "v2 전략이 BTC 단순보유보다 우수한 성과"
    elif roi > 0:
        verdict = "v2 전략이 양의 수익이나, BTC 단순보유가 더 좋았음"
    else:
        verdict = "v2 전략이 손실 기록"

    p(f"\n  {verdict}")
    p(f"  4년 2개월간 ROI: {roi:+.1f}% (BTC B&H: {btc_bnh_roi:+.1f}%)")
    p(f"  MDD: -{sim.max_drawdown:.1f}%")
    p(f"  승률: {win_rate:.1f}%")
    p(f"  전략 특징: 소수의 대형 랠리에서 포지션을 유지하는 것이 핵심")

    elapsed = time.time() - t0
    p(f"\n  소요시간: {elapsed:.0f}초")
    p(f"{'=' * 70}")

    # ── 파일 저장 ──
    report_path = PROJECT_DIR / "data" / "backtest_full_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\n  보고서 저장: {report_path}")

    # JSON 요약
    json_summary = {
        "period": f"{SIM_START.strftime('%Y-%m-%d')} ~ {SIM_END.strftime('%Y-%m-%d')}",
        "sim_points": len(all_sim_points),
        "initial_krw": INITIAL_KRW,
        "final_eval": round(total_eval),
        "roi_pct": round(roi, 2),
        "btc_bnh_roi_pct": round(btc_bnh_roi, 2),
        "mdd_pct": round(sim.max_drawdown, 2),
        "total_trades": sim.total_trades,
        "buys": sim.total_buys,
        "sells": sim.total_sells,
        "holds": sim.total_holds,
        "win_rate": round(win_rate, 1),
        "win_trades": sim.win_trades,
        "loss_trades": sim.loss_trades,
        "switch_count": sim.switch_count,
        "yearly_stats": sim.yearly_stats,
        "monthly_stats": sim.monthly_stats,
        "agent_distribution": agent_stats,
        "btc_price_start": first_price,
        "btc_price_end": final_price,
        "elapsed_sec": round(elapsed, 1),
        "top_trades": [t for t in sim.trade_log if t["decision"] == "sell"],
    }
    json_path = PROJECT_DIR / "data" / "backtest_full_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_summary, f, ensure_ascii=False, indent=2)
    print(f"  JSON 저장: {json_path}")


if __name__ == "__main__":
    main()
