#!/usr/bin/env python3
"""
백테스트 시뮬레이터 — 과거 가상매매 데이터 생성

2026-02-01 ~ 03-08 기간의 과거 시장 데이터를 수집하고,
기존 에이전트 시스템으로 가상매매를 시뮬레이션하여
decisions 테이블에 임베딩과 함께 저장한다.

Usage:
  python scripts/backtest_simulator.py                    # 전체 실행
  python scripts/backtest_simulator.py --dry-run          # DB 저장 없이 테스트
  python scripts/backtest_simulator.py --resume            # 중단점부터 재개
  python scripts/backtest_simulator.py --start 2026-02-15  # 특정 날짜부터
  python scripts/backtest_simulator.py --limit 5           # N포인트만 실행
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
load_dotenv(PROJECT_DIR / ".env")

import requests

# ── 기술지표 함수 재사용 ──
from scripts.collect_market_data import (
    rsi, sma, ema, macd, bollinger, stochastic, calc_adx, calc_atr,
)
from scripts.save_decision import (
    generate_state_embedding, _update_embedding_via_sql,
    supabase_post, save_market_context,
    SUPABASE_URL, SUPABASE_KEY,
)

KST = timezone(timedelta(hours=9))
UPBIT_API = "https://api.upbit.com/v1"
BINANCE_FAPI = "https://fapi.binance.com"
FGI_API = "https://api.alternative.me/fng/"

# Backtest 전용 상태 파일
BACKTEST_STATE_FILE = PROJECT_DIR / "data" / "backtest_agent_state.json"
BACKTEST_EMERGENCY_FILE = PROJECT_DIR / "data" / "backtest_auto_emergency.json"
CHECKPOINT_FILE = PROJECT_DIR / "data" / "backtest_checkpoint.json"

# ── HTTP 세션 ──
_session = requests.Session()
_session.headers.update({"Accept": "application/json"})


def _api_get(url: str, params: dict | None = None, max_retries: int = 3) -> dict | list:
    """범용 GET with 429 재시도."""
    for attempt in range(max_retries):
        r = _session.get(url, params=params, timeout=15)
        if r.status_code == 429:
            wait = 2 ** attempt
            print(f"[rate_limit] 429 at {url}, retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()
    return r.json()


# ═══════════════════════════════════════════════════════════════════
# 1. PRE-FETCH: 전체 기간 데이터 일괄 조회
# ═══════════════════════════════════════════════════════════════════

def prefetch_fgi(days: int = 90) -> dict[str, int]:
    """FGI 전체 이력 → {날짜: 값} dict."""
    print("[prefetch] FGI 이력 조회...", file=sys.stderr)
    data = _api_get(FGI_API, {"limit": "0", "format": "json"})
    result = {}
    for entry in data.get("data", []):
        ts = int(entry["timestamp"])
        dt = datetime.fromtimestamp(ts, tz=KST)
        date_str = dt.strftime("%Y-%m-%d")
        result[date_str] = int(entry["value"])
    print(f"[prefetch] FGI: {len(result)}일 로드", file=sys.stderr)
    return result


def prefetch_binance_funding(start_dt: datetime, end_dt: datetime) -> dict[str, dict]:
    """Binance 펀딩비 이력 → {날짜-시간: {rate, ...}} dict."""
    print("[prefetch] Binance 펀딩비 조회...", file=sys.stderr)
    result = {}
    current = start_dt
    while current < end_dt:
        chunk_end = min(current + timedelta(days=30), end_dt)
        try:
            data = _api_get(
                f"{BINANCE_FAPI}/fapi/v1/fundingRate",
                {
                    "symbol": "BTCUSDT",
                    "startTime": int(current.timestamp() * 1000),
                    "endTime": int(chunk_end.timestamp() * 1000),
                    "limit": 1000,
                },
            )
            for entry in data:
                ts = int(entry["fundingTime"]) / 1000
                dt = datetime.fromtimestamp(ts, tz=KST)
                key = dt.strftime("%Y-%m-%d %H:00")
                result[key] = {
                    "rate": float(entry["fundingRate"]),
                    "timestamp": dt.isoformat(),
                }
        except Exception as e:
            print(f"[prefetch] 펀딩비 조회 실패 ({current.date()}~): {e}", file=sys.stderr)
        current = chunk_end
        time.sleep(0.3)
    print(f"[prefetch] 펀딩비: {len(result)}건 로드", file=sys.stderr)
    return result


def prefetch_binance_ls_ratio(start_dt: datetime, end_dt: datetime) -> dict[str, float]:
    """Binance 롱숏비율 이력 → {날짜-시간: ratio} dict."""
    print("[prefetch] Binance 롱숏비율 조회...", file=sys.stderr)
    result = {}
    current = start_dt
    while current < end_dt:
        chunk_end = min(current + timedelta(days=30), end_dt)
        try:
            data = _api_get(
                f"{BINANCE_FAPI}/futures/data/topLongShortAccountRatio",
                {
                    "symbol": "BTCUSDT",
                    "period": "4h",
                    "startTime": int(current.timestamp() * 1000),
                    "endTime": int(chunk_end.timestamp() * 1000),
                    "limit": 500,
                },
            )
            for entry in data:
                ts = int(entry["timestamp"]) / 1000
                dt = datetime.fromtimestamp(ts, tz=KST)
                key = dt.strftime("%Y-%m-%d %H:00")
                result[key] = float(entry["longShortRatio"])
        except Exception as e:
            print(f"[prefetch] 롱숏비율 조회 실패 ({current.date()}~): {e}", file=sys.stderr)
        current = chunk_end
        time.sleep(0.3)
    print(f"[prefetch] 롱숏비율: {len(result)}건 로드", file=sys.stderr)
    return result


def prefetch_macro(start_date: str, end_date: str) -> dict[str, dict]:
    """Yahoo Finance 매크로 데이터 → {날짜: {sp500, dxy, gold, ...}} dict."""
    print("[prefetch] Yahoo Finance 매크로 조회...", file=sys.stderr)
    result = {}
    tickers = {
        "^GSPC": "sp500",
        "DX-Y.NYB": "dxy",
        "GC=F": "gold",
        "CL=F": "oil",
        "^TNX": "us10y",
        "USDKRW=X": "usdkrw",
    }
    # Yahoo requires proper headers to avoid 429
    yahoo_session = requests.Session()
    yahoo_session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept": "application/json",
    })
    # Get crumb/cookie
    try:
        crumb_resp = yahoo_session.get(
            "https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=10
        )
        crumb = crumb_resp.text.strip() if crumb_resp.ok else ""
    except Exception:
        crumb = ""

    p1 = int(datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=KST).timestamp())
    p2 = int(datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=KST).timestamp())

    for yahoo_sym, name in tickers.items():
        try:
            url = f"https://query2.finance.yahoo.com/v8/finance/chart/{yahoo_sym}"
            params = {"period1": p1, "period2": p2, "interval": "1d"}
            if crumb:
                params["crumb"] = crumb
            r = yahoo_session.get(url, params=params, timeout=15)
            if r.status_code == 429:
                print(f"[prefetch] Yahoo {name} 429 — 스킵", file=sys.stderr)
                time.sleep(2)
                continue
            r.raise_for_status()
            data = r.json()
            chart = data.get("chart", {}).get("result", [{}])[0]
            timestamps = chart.get("timestamp", [])
            closes_list = chart.get("indicators", {}).get("quote", [{}])[0].get("close", [])
            for ts, close in zip(timestamps, closes_list):
                if close is None:
                    continue
                dt = datetime.fromtimestamp(ts, tz=KST)
                date_str = dt.strftime("%Y-%m-%d")
                if date_str not in result:
                    result[date_str] = {}
                result[date_str][name] = round(close, 2)
            time.sleep(1.0)
        except Exception as e:
            print(f"[prefetch] Yahoo {name} 실패: {e}", file=sys.stderr)
    print(f"[prefetch] 매크로: {len(result)}일 로드", file=sys.stderr)
    return result


def prefetch_upbit_daily(start_dt: datetime, end_dt: datetime) -> list[dict]:
    """Upbit BTC/KRW 일봉 전체 조회 (지표 계산용)."""
    print("[prefetch] Upbit 일봉 조회...", file=sys.stderr)
    all_candles = []
    # 과거 200일 추가 필요 (지표 계산 위해)
    fetch_start = start_dt - timedelta(days=230)
    current = end_dt
    while current > fetch_start:
        to_str = current.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            candles = _api_get(
                f"{UPBIT_API}/candles/days",
                {"market": "KRW-BTC", "count": "200", "to": to_str},
            )
            if not candles:
                break
            all_candles.extend(candles)
            # 가장 오래된 캔들 기준으로 다음 배치
            oldest = candles[-1]["candle_date_time_kst"]
            current = datetime.strptime(oldest[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=KST) - timedelta(days=1)
            time.sleep(0.12)
        except Exception as e:
            print(f"[prefetch] 일봉 조회 실패: {e}", file=sys.stderr)
            break

    # 중복 제거 & 정렬 (오래된 순)
    seen = set()
    unique = []
    for c in all_candles:
        key = c["candle_date_time_kst"][:10]
        if key not in seen:
            seen.add(key)
            unique.append(c)
    unique.sort(key=lambda x: x["candle_date_time_kst"])
    print(f"[prefetch] 일봉: {len(unique)}일 로드", file=sys.stderr)
    return unique


# ═══════════════════════════════════════════════════════════════════
# 2. 시뮬레이션 포인트별 데이터 구성
# ═══════════════════════════════════════════════════════════════════

def fetch_4h_candles_at(sim_dt: datetime) -> list[dict]:
    """Upbit 4시간봉 42개 조회 (특정 시점 기준)."""
    to_str = sim_dt.strftime("%Y-%m-%dT%H:%M:%S")
    try:
        candles = _api_get(
            f"{UPBIT_API}/candles/minutes/240",
            {"market": "KRW-BTC", "count": "42", "to": to_str},
        )
        candles.reverse()  # 오래된 순
        time.sleep(0.12)
        return candles
    except Exception as e:
        print(f"  [4h] 조회 실패: {e}", file=sys.stderr)
        return []


def collect_market_data_at(
    sim_dt: datetime,
    daily_candles: list[dict],
    fetch_4h: bool = True,
) -> dict:
    """특정 시점 기준 시장 데이터 + 기술지표 구성."""
    date_str = sim_dt.strftime("%Y-%m-%d")

    # sim_dt 이전 일봉만 필터
    past_candles = [
        c for c in daily_candles
        if c["candle_date_time_kst"][:10] <= date_str
    ]
    if len(past_candles) < 20:
        return {}

    # NULL/0 가격 필터링
    valid_candles = [
        c for c in past_candles
        if c.get("trade_price") and c["trade_price"] > 0
        and c.get("high_price") and c["high_price"] > 0
        and c.get("low_price") and c["low_price"] > 0
    ]
    if len(valid_candles) < 20:
        return {}
    closes = [int(c["trade_price"]) for c in valid_candles]
    highs = [int(c["high_price"]) for c in valid_candles]
    lows = [int(c["low_price"]) for c in valid_candles]
    current_price = closes[-1]
    if current_price <= 0:
        return {}

    # 24h 가격 변화 (전일 대비)
    change_rate_24h = 0.0
    if len(closes) >= 2 and closes[-2] > 0:
        change_rate_24h = (closes[-1] - closes[-2]) / closes[-2]

    # 기술지표
    sma_20 = sma(closes, 20)
    sma_50 = sma(closes, 50)
    sma_200 = sma(closes, 200)
    sma_20_dev = None
    if sma_20 and sma_20 > 0:
        sma_20_dev = round((current_price - sma_20) / sma_20 * 100, 2)

    adx_data = calc_adx(highs, lows, closes)
    atr_val = calc_atr(highs, lows, closes)

    # 일봉 5일 요약
    daily_summary = []
    for c in past_candles[-5:]:
        daily_summary.append({
            "date": c.get("candle_date_time_kst", "")[:10],
            "open": c["opening_price"],
            "high": c["high_price"],
            "low": c["low_price"],
            "close": c["trade_price"],
            "change_pct": round(
                (c["trade_price"] - c["opening_price"]) / max(c["opening_price"], 1) * 100, 2
            ),
            "volume": round(c.get("candle_acc_trade_volume", 0), 2),
        })

    # 4시간봉 조회 (과거 시점 기준)
    closes_4h = closes[-42:]
    highs_4h = highs[-42:]
    lows_4h = lows[-42:]
    if fetch_4h:
        candles_4h = fetch_4h_candles_at(sim_dt)
        if candles_4h:
            closes_4h = [int(c["trade_price"]) for c in candles_4h]
            highs_4h = [int(c["high_price"]) for c in candles_4h]
            lows_4h = [int(c["low_price"]) for c in candles_4h]
            # 4h 마지막 종가를 current_price로 사용 (더 정확한 시점 가격)
            current_price = closes_4h[-1]

    # 거래량 (최근 일봉)
    last_candle = past_candles[-1]
    volume_24h = last_candle.get("candle_acc_trade_volume", 0)

    return {
        "timestamp": sim_dt.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "market": "KRW-BTC",
        "current_price": current_price,
        "change_rate_24h": change_rate_24h,
        "volume_24h": volume_24h,
        "indicators": {
            "sma_20": round(sma_20, 2) if sma_20 else None,
            "sma_50": round(sma_50, 2) if sma_50 else None,
            "sma_200": round(sma_200, 2) if sma_200 else None,
            "sma_20_deviation_pct": sma_20_dev,
            "ema_10": round(ema(closes, 10), 2) if ema(closes, 10) else None,
            "ema_50": round(ema(closes, 50), 2) if len(closes) >= 50 else None,
            "ema_200": round(ema(closes, 200), 2) if len(closes) >= 200 else None,
            "rsi_14": round(rsi(closes, 14), 2),
            "macd": macd(closes),
            "bollinger": bollinger(closes, 20),
            "stochastic": stochastic(highs, lows, closes, 14),
            "adx": adx_data,
            "atr": atr_val,
        },
        "indicators_4h": {
            "rsi_14": round(rsi(closes_4h, 14), 2) if len(closes_4h) > 14 else None,
            "macd": macd(closes_4h) if len(closes_4h) >= 26 else None,
            "stochastic": stochastic(highs_4h, lows_4h, closes_4h, 14),
        },
        "ticker": {
            "trade_price": current_price,
            "signed_change_rate": change_rate_24h,
            "acc_trade_volume_24h": volume_24h,
        },
        # 호가/체결은 과거 조회 불가 → 중립값
        "orderbook": {"bid_total": 100, "ask_total": 100, "ratio": 1.0},
        "trade_pressure": {"buy_volume": 50, "sell_volume": 50},
        "daily_summary_5d": daily_summary,
    }


def build_external_data(
    sim_dt: datetime,
    fgi_cache: dict[str, int],
    funding_cache: dict[str, dict],
    ls_cache: dict[str, float],
    macro_cache: dict[str, dict],
    market_data: dict,
) -> dict:
    """캐시에서 외부 데이터 조합."""
    date_str = sim_dt.strftime("%Y-%m-%d")
    hour_str = sim_dt.strftime("%Y-%m-%d %H:00")

    # FGI
    fgi_value = fgi_cache.get(date_str, 50)
    fgi_class = (
        "Extreme Fear" if fgi_value <= 25
        else "Fear" if fgi_value <= 45
        else "Neutral" if fgi_value <= 55
        else "Greed" if fgi_value <= 75
        else "Extreme Greed"
    )

    # Binance
    funding_data = _find_nearest(funding_cache, hour_str)
    funding_rate = funding_data.get("rate", 0.0001) if funding_data else 0.0001
    ls_ratio = _find_nearest_value(ls_cache, hour_str, default=1.0)

    # 매크로
    macro_data = macro_cache.get(date_str, {})
    usdkrw = macro_data.get("usdkrw", 1350)

    # 김프 추정: Upbit 가격 vs (Binance USDT 가격 추정)
    upbit_price = market_data.get("current_price", 0)
    kimchi_premium = 0.0
    if upbit_price and usdkrw:
        # 실제 김프는 약 1~3% 범위이므로 약간의 랜덤 대신 0으로 처리
        kimchi_premium = 0.0

    # 가격 변동 기반 감성 추정
    change_24h = market_data.get("change_rate_24h", 0)
    sentiment = estimate_sentiment(change_24h)

    # Data Fusion 점수 계산
    fusion_score = _calculate_fusion_score(
        fgi_value, funding_rate, ls_ratio, change_24h, macro_data
    )

    sources = {
        "fear_greed": {
            "current": {"value": fgi_value, "value_classification": fgi_class},
            "value": fgi_value,
            "value_classification": fgi_class,
        },
        "news": sentiment["news"],
        "whale_tracker": sentiment["whale"],
        "binance_sentiment": {
            "funding_rate": {"current_rate": funding_rate, "rate": funding_rate},
            "top_trader_long_short": {"current_ratio": ls_ratio, "ratio": ls_ratio},
            "open_interest": {"value": 0, "change_pct": 0},
            "kimchi_premium": {"premium_pct": kimchi_premium},
        },
        "eth_btc": {"eth_btc_z_score": 0, "signal": "정상 범위"},
        "macro": {
            "analysis": {
                "sp500_trend": _macro_trend(macro_data, "sp500"),
                "dxy_trend": _macro_trend(macro_data, "dxy"),
                "gold_trend": _macro_trend(macro_data, "gold"),
                "macro_sentiment": "neutral",
                "macro_score": 0,
            },
        },
        "crypto_signals": {"anomaly_level": "normal", "change_24h": change_24h * 100},
        "coinmarketcap": {"btc_dominance": 55.0},
        "rss_news": {"sentiment": {"combined_score": sentiment["score"]}},
        "x_signals": {"signal": {"score": 0, "whale_summary": "N/A (backtest)"}},
        "social_sentiment": {"signal": {"total_score": 0}},
    }

    strategy_bonus = _score_to_bonus(fusion_score)

    external_signal = {
        "total_score": fusion_score,
        "strategy_bonus": strategy_bonus,
        "fusion": {
            "signal": (
                "strong_buy" if fusion_score >= 40
                else "buy" if fusion_score >= 15
                else "strong_sell" if fusion_score <= -40
                else "sell" if fusion_score <= -15
                else "neutral"
            ),
        },
        "extra_components": {},
        "extra_details": [f"Backtest fusion score: {fusion_score}"],
    }

    return {
        "timestamp": sim_dt.isoformat(),
        "collection_time_sec": 0.0,
        "sources": sources,
        "external_signal": external_signal,
        "errors": [],
        "warnings": ["backtest mode - estimated data"],
    }


def estimate_sentiment(change_24h: float) -> dict:
    """24h 가격 변동 기반 감성 추정."""
    pct = change_24h * 100 if abs(change_24h) < 1 else change_24h

    if pct >= 5:
        score, label = 0.6, "positive"
    elif pct >= 2:
        score, label = 0.3, "positive"
    elif pct <= -5:
        score, label = -0.6, "negative"
    elif pct <= -2:
        score, label = -0.3, "negative"
    else:
        score, label = 0.0, "neutral"

    return {
        "score": score,
        "news": {
            "sentiment_score": score,
            "overall_sentiment": label,
            "positive": max(0, int(3 + score * 5)),
            "negative": max(0, int(3 - score * 5)),
            "neutral": 2,
        },
        "whale": {
            "whale_score": {"direction": "neutral", "large_tx_count": 0},
            "large_tx_count": 0,
            "exchange_net_flow": 0,
        },
    }


def _calculate_fusion_score(
    fgi: int, funding: float, ls_ratio: float,
    change_24h: float, macro: dict,
) -> int:
    """간이 Data Fusion 점수 계산 (-100 ~ +100)."""
    score = 0.0

    # FGI 기여
    if fgi <= 20:
        score += 30
    elif fgi <= 30:
        score += 20
    elif fgi <= 40:
        score += 10
    elif fgi >= 80:
        score -= 30
    elif fgi >= 70:
        score -= 20
    elif fgi >= 60:
        score -= 10

    # 펀딩비 기여
    if funding < -0.01:
        score += 15  # 숏 과열 → 반등 기대
    elif funding > 0.05:
        score -= 15  # 롱 과열

    # 롱숏비율 기여
    if ls_ratio > 2.0:
        score -= 10
    elif ls_ratio < 0.5:
        score += 10

    # 가격 모멘텀
    pct = change_24h * 100 if abs(change_24h) < 1 else change_24h
    if pct >= 3:
        score += 10
    elif pct <= -3:
        score -= 10

    return max(-100, min(100, int(score)))


def _score_to_bonus(score: int) -> int:
    """fusion score → strategy_bonus (-20 ~ +20)."""
    if score >= 40:
        return 20
    if score >= 25:
        return 15
    if score >= 15:
        return 10
    if score >= 5:
        return 5
    if score <= -40:
        return -20
    if score <= -25:
        return -15
    if score <= -15:
        return -10
    if score <= -5:
        return -5
    return 0


def _macro_trend(macro: dict, key: str) -> str:
    """매크로 데이터에서 트렌드 추정."""
    return "neutral"  # 일간 단일 데이터이므로 중립 고정


def _find_nearest(cache: dict[str, dict], key: str) -> dict | None:
    """캐시에서 가장 가까운 키 찾기."""
    if key in cache:
        return cache[key]
    # ±8시간 범위에서 검색
    try:
        target = datetime.strptime(key, "%Y-%m-%d %H:00")
    except ValueError:
        return None
    for offset in range(1, 9):
        for delta in [timedelta(hours=offset), timedelta(hours=-offset)]:
            k = (target + delta).strftime("%Y-%m-%d %H:00")
            if k in cache:
                return cache[k]
    return None


def _find_nearest_value(cache: dict[str, float], key: str, default: float = 0.0) -> float:
    """캐시에서 가장 가까운 값 찾기."""
    if key in cache:
        return cache[key]
    try:
        target = datetime.strptime(key, "%Y-%m-%d %H:00")
    except ValueError:
        return default
    for offset in range(1, 9):
        for delta in [timedelta(hours=offset), timedelta(hours=-offset)]:
            k = (target + delta).strftime("%Y-%m-%d %H:00")
            if k in cache:
                return cache[k]
    return default


# ═══════════════════════════════════════════════════════════════════
# 3. 가상 포트폴리오
# ═══════════════════════════════════════════════════════════════════

class VirtualPortfolio:
    """매매 시뮬레이션용 가상 포트폴리오."""
    FEE_RATE = 0.0005  # 0.05% 수수료

    def __init__(self, initial_krw: int = 1_000_000):
        self.initial_krw = float(initial_krw)
        self.krw = float(initial_krw)
        self.btc = 0.0
        self.avg_buy_price = 0.0
        self.trade_count = 0
        self.total_fees = 0.0

    def execute_buy(self, amount_krw: float, price: int) -> dict:
        """시장가 매수 시뮬레이션."""
        actual_amount = min(amount_krw, self.krw)
        if actual_amount <= 0:
            return {"executed": False, "reason": "잔고 부족"}
        fee = actual_amount * self.FEE_RATE
        net_amount = actual_amount - fee
        btc_qty = net_amount / price

        # 평균 매수가 갱신
        total_btc = self.btc + btc_qty
        if total_btc > 0:
            self.avg_buy_price = (
                (self.btc * self.avg_buy_price + net_amount) / total_btc
            )
        self.btc = total_btc
        self.krw -= actual_amount
        self.total_fees += fee
        self.trade_count += 1

        return {
            "executed": True,
            "side": "bid",
            "amount": round(actual_amount),
            "volume": round(btc_qty, 8),
            "price": price,
            "fee": round(fee),
        }

    def execute_sell(self, volume_btc: float, price: int) -> dict:
        """시장가 매도 시뮬레이션."""
        actual_volume = min(volume_btc, self.btc)
        if actual_volume <= 0:
            return {"executed": False, "reason": "보유량 부족"}
        gross = actual_volume * price
        fee = gross * self.FEE_RATE
        net = gross - fee

        self.btc -= actual_volume
        self.krw += net
        self.total_fees += fee
        self.trade_count += 1

        if self.btc < 1e-10:
            self.btc = 0.0
            self.avg_buy_price = 0.0

        return {
            "executed": True,
            "side": "ask",
            "amount": round(gross),
            "volume": round(actual_volume, 8),
            "price": price,
            "fee": round(fee),
        }

    def to_dict(self, current_price: int) -> dict:
        """Orchestrator 호환 포트폴리오 dict (get_portfolio.py 형식)."""
        btc_eval = self.btc * current_price
        total_eval = self.krw + btc_eval
        profit_pct = 0.0
        profit_loss = 0
        if self.avg_buy_price > 0 and self.btc > 0:
            profit_pct = (current_price - self.avg_buy_price) / self.avg_buy_price * 100
            profit_loss = round(btc_eval - self.btc * self.avg_buy_price)

        btc_ratio = btc_eval / total_eval if total_eval > 0 else 0.0

        holdings = []
        if self.btc > 0:
            holdings.append({
                "currency": "BTC",
                "balance": round(self.btc, 8),
                "avg_buy_price": round(self.avg_buy_price),
                "eval_amount": round(btc_eval),
                "profit_pct": round(profit_pct, 2),
                "profit_loss": profit_loss,
            })

        return {
            # 에이전트가 기대하는 최상위 키 (get_portfolio.py 형식)
            "krw_balance": round(self.krw),
            "total_eval": round(total_eval),
            "holdings": holdings,
            # Orchestrator가 사용하는 중첩 구조
            "krw": {
                "balance": round(self.krw),
                "eval_amount": round(self.krw),
            },
            "btc": {
                "balance": round(self.btc, 8),
                "avg_buy_price": round(self.avg_buy_price),
                "eval_amount": round(btc_eval),
                "profit_pct": round(profit_pct, 2),
                "profit_loss": profit_loss,
            },
            "btc_ratio": round(btc_ratio, 4),
        }

    def summary(self, current_price: int) -> str:
        """요약 문자열."""
        total = self.krw + self.btc * current_price
        pnl = total - self.initial_krw
        return (
            f"KRW={self.krw:,.0f} | BTC={self.btc:.6f} | "
            f"Total={total:,.0f} | PnL={pnl:+,.0f} ({pnl/10000:+.1f}%)"
        )


# ═══════════════════════════════════════════════════════════════════
# 4. Orchestrator 격리 실행
# ═══════════════════════════════════════════════════════════════════

def run_orchestrator_isolated(
    market_data: dict,
    external_data: dict,
    portfolio: dict,
) -> dict:
    """Orchestrator를 backtest 전용 상태 파일로 격리 실행."""
    import agents.orchestrator as orch_mod

    # STATE_FILE / AUTO_EMERGENCY_FILE 패칭
    original_state_file = orch_mod.STATE_FILE
    original_emergency_file = orch_mod.AUTO_EMERGENCY_FILE

    orch_mod.STATE_FILE = BACKTEST_STATE_FILE
    orch_mod.AUTO_EMERGENCY_FILE = BACKTEST_EMERGENCY_FILE

    # EMERGENCY_STOP 무시
    original_es = os.environ.get("EMERGENCY_STOP")

    try:
        os.environ["EMERGENCY_STOP"] = "false"
        orchestrator = orch_mod.Orchestrator()
        result = orchestrator.run(
            market_data=market_data,
            external_data=external_data,
            portfolio=portfolio,
            past_decisions=None,
        )
        return result
    finally:
        orch_mod.STATE_FILE = original_state_file
        orch_mod.AUTO_EMERGENCY_FILE = original_emergency_file
        if original_es is not None:
            os.environ["EMERGENCY_STOP"] = original_es
        else:
            os.environ.pop("EMERGENCY_STOP", None)


# ═══════════════════════════════════════════════════════════════════
# 5. DB 저장
# ═══════════════════════════════════════════════════════════════════

def save_to_db(
    sim_dt: datetime,
    decision: dict,
    market_data: dict,
    external_data: dict,
    portfolio_dict: dict,
    result: dict,
    cycle_id: str,
    dry_run: bool = False,
) -> str | None:
    """decisions + market_context_log DB 저장. 반환: decision_id."""
    if dry_run:
        print("  [dry-run] DB 저장 스킵", file=sys.stderr)
        return None

    # ── decisions 테이블 ──
    dec_action = decision.get("decision", "hold")
    dec_map = {"buy": "매수", "sell": "매도", "hold": "관망"}
    mapped_decision = dec_map.get(dec_action, "관망")

    confidence = decision.get("confidence", 0.5)
    if isinstance(confidence, (int, float)) and confidence > 1:
        confidence = confidence / 100.0

    buy_score = decision.get("buy_score", {})
    rsi_value = buy_score.get("rsi", {}).get("value") if isinstance(buy_score.get("rsi"), dict) else None
    fgi_value = buy_score.get("fgi", {}).get("value") if isinstance(buy_score.get("fgi"), dict) else None

    indicators = market_data.get("indicators", {})
    if rsi_value is None:
        rsi_value = indicators.get("rsi_14")
    if fgi_value is None:
        fgi = external_data.get("sources", {}).get("fear_greed", {})
        fgi_value = fgi.get("value") or (fgi.get("current", {}) or {}).get("value")

    reason_parts = [decision.get("reason", "")]
    agent_name = decision.get("agent_name", result.get("active_agent", ""))
    if agent_name:
        reason_parts.append(f"Agent: {agent_name}")

    row = {
        "market": "KRW-BTC",
        "decision": mapped_decision,
        "confidence": round(confidence, 2),
        "reason": " | ".join(filter(None, reason_parts)),
        "current_price": int(market_data.get("current_price", 0)),
        "rsi_value": round(float(rsi_value), 2) if rsi_value else None,
        "fear_greed_value": int(fgi_value) if fgi_value else None,
        "sma20_price": int(indicators.get("sma_20") or 0) or None,
        "market_data_snapshot": json.dumps({
            "buy_score": buy_score,
            "external": external_data.get("external_signal", {}),
        }, ensure_ascii=False, default=str),
        "cycle_id": cycle_id,
        "source": "backtest",
        "dry_run": True,
        "machine_name": "backtest",
        "created_at": sim_dt.isoformat(),
    }
    # None 제거
    row = {k: v for k, v in row.items() if v is not None}

    resp = supabase_post("decisions", row)
    if not resp:
        return None

    decision_id = None
    if isinstance(resp, list) and resp:
        decision_id = resp[0].get("id")
    elif isinstance(resp, dict):
        decision_id = resp.get("id")

    # ── market_context_log ──
    if decision_id:
        market_state = result.get("market_state", {})
        agent_state = {
            "active_agent": result.get("active_agent", ""),
            "danger_score": market_state.get("danger_score"),
            "opportunity_score": market_state.get("opportunity_score"),
        }
        # cycle_id 오버라이드를 위해 직접 save_market_context의 내부 _cycle_id를 설정
        import scripts.save_decision as sd_mod
        original_cycle_id = sd_mod._cycle_id
        sd_mod._cycle_id = cycle_id
        try:
            save_market_context(
                decision_id=decision_id,
                market_data=market_data,
                external_data=external_data,
                portfolio=portfolio_dict,
                agent_state=agent_state,
            )
        finally:
            sd_mod._cycle_id = original_cycle_id

    return decision_id


def save_embedding(decision_id: str, market_data: dict, external_data: dict) -> bool:
    """RAG 임베딩 생성 + DB 저장."""
    if not decision_id:
        return False

    # build_embedding_text에 필요한 데이터 조합
    emb_data = {
        "current_price": market_data.get("current_price"),
        "change_rate_24h": market_data.get("change_rate_24h"),
        "rsi_14": (market_data.get("indicators") or {}).get("rsi_14"),
        "fear_greed_value": (
            (external_data.get("sources", {}).get("fear_greed", {}) or {})
            .get("value")
            or (external_data.get("sources", {}).get("fear_greed", {}).get("current", {}) or {})
            .get("value")
        ),
        "sma_20": (market_data.get("indicators") or {}).get("sma_20"),
        "indicators": market_data.get("indicators", {}),
        "fear_greed": external_data.get("sources", {}).get("fear_greed", {}),
        "news_sentiment": (
            external_data.get("sources", {}).get("news", {}).get("sentiment_score")
        ),
        "funding_rate": (
            external_data.get("sources", {}).get("binance_sentiment", {})
            .get("funding_rate", {}).get("current_rate")
        ),
        "volume_24h": market_data.get("volume_24h"),
        "kimchi_premium": (
            external_data.get("sources", {}).get("binance_sentiment", {})
            .get("kimchi_premium", {}).get("premium_pct")
        ),
        "long_short_ratio": (
            external_data.get("sources", {}).get("binance_sentiment", {})
            .get("top_trader_long_short", {}).get("current_ratio")
        ),
    }

    emb_text, emb_vec = generate_state_embedding(emb_data)
    if emb_text and emb_vec:
        _update_embedding_via_sql(decision_id, emb_vec, emb_text)
        return True
    return False


def save_retrospective(
    decision_id: str,
    sim_dt: datetime,
    decision_action: str,
    current_price: int,
    daily_candles: list[dict],
) -> None:
    """사후추적 즉시 계산 (미래 가격 이미 알고 있으므로)."""
    if not decision_id or not SUPABASE_URL:
        return

    updates = {}
    for window, hours in [("1h", 1), ("4h", 4), ("24h", 24)]:
        future_dt = sim_dt + timedelta(hours=hours)
        future_date = future_dt.strftime("%Y-%m-%d")
        # 일봉 기반 가격 추정 (정확한 시간별 가격은 없음)
        # 같은 날 종가 또는 다음날 종가 사용
        future_price = None
        for c in daily_candles:
            if c["candle_date_time_kst"][:10] == future_date:
                future_price = c["trade_price"]
                break
        # 같은 날이면 당일 종가
        if future_price is None:
            sim_date = sim_dt.strftime("%Y-%m-%d")
            for c in daily_candles:
                cdate = c["candle_date_time_kst"][:10]
                if cdate > sim_date:
                    future_price = c["trade_price"]
                    break

        if future_price is None or not current_price or current_price <= 0:
            continue

        outcome_pct = round((future_price - current_price) / current_price * 100, 3)

        # 정확성 판단
        dec_map = {"buy": "매수", "매수": "매수", "sell": "매도", "매도": "매도"}
        mapped = dec_map.get(decision_action, "관망")
        if mapped == "매수":
            was_correct = outcome_pct > 0
        elif mapped == "매도":
            was_correct = outcome_pct < 0
        else:
            threshold = 0.5 if window in ("1h", "4h") else 1.0
            was_correct = abs(outcome_pct) < threshold

        updates[f"price_{window}_after"] = int(future_price)
        updates[f"outcome_{window}_pct"] = outcome_pct
        updates[f"was_correct_{window}"] = was_correct

        # 24h: profit_loss
        if window == "24h":
            if mapped == "매수":
                updates["profit_loss"] = outcome_pct
            elif mapped == "매도":
                updates["profit_loss"] = -outcome_pct
            else:
                updates["profit_loss"] = -outcome_pct

    if not updates:
        return

    try:
        patch_headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
        }
        r = requests.patch(
            f"{SUPABASE_URL}/rest/v1/decisions?id=eq.{decision_id}",
            headers=patch_headers,
            json=updates,
            timeout=10,
        )
        if not r.ok:
            print(f"  [retro] 사후추적 저장 실패 ({r.status_code}): {r.text[:200]}", file=sys.stderr)
    except Exception as e:
        print(f"  [retro] 사후추적 예외: {e}", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════════
# 6. 체크포인트 관리
# ═══════════════════════════════════════════════════════════════════

def load_checkpoint() -> dict:
    try:
        with open(CHECKPOINT_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_checkpoint(data: dict):
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════
# 7. 메인 시뮬레이션
# ═══════════════════════════════════════════════════════════════════

def generate_sim_points(
    start_date: str = "2026-02-01",
    end_date: str = "2026-03-08",
    interval_hours: int = 4,
) -> list[datetime]:
    """시뮬레이션 포인트 생성 (4시간 간격, 0/4/8/12/16/20시)."""
    points = []
    current = datetime.strptime(start_date, "%Y-%m-%d").replace(
        hour=0, tzinfo=KST
    )
    end = datetime.strptime(end_date, "%Y-%m-%d").replace(
        hour=20, tzinfo=KST
    )
    while current <= end:
        points.append(current)
        current += timedelta(hours=interval_hours)
    return points


def main():
    parser = argparse.ArgumentParser(description="백테스트 시뮬레이터")
    parser.add_argument("--dry-run", action="store_true", help="DB 저장 없이 테스트")
    parser.add_argument("--resume", action="store_true", help="중단점부터 재개")
    parser.add_argument("--start", default="2026-02-01", help="시작 날짜 (YYYY-MM-DD)")
    parser.add_argument("--end", default="2026-03-08", help="종료 날짜 (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, default=0, help="실행할 포인트 수 (0=전체)")
    parser.add_argument("--no-embedding", action="store_true", help="임베딩 생성 건너뜀")
    args = parser.parse_args()

    print("=" * 60)
    print("🔬 백테스트 시뮬레이터 시작")
    print(f"  기간: {args.start} ~ {args.end}")
    print(f"  모드: {'DRY-RUN (DB 저장 없음)' if args.dry_run else 'LIVE (DB 저장)'}")
    print(f"  임베딩: {'OFF' if args.no_embedding else 'ON'}")
    print("=" * 60)

    t_start = time.time()

    # ── Phase 1: Pre-fetch ──
    print("\n📥 Phase 1: 데이터 Pre-fetch")
    start_dt = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=KST)
    end_dt = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=KST) + timedelta(days=2)

    fgi_cache = prefetch_fgi()
    funding_cache = prefetch_binance_funding(start_dt, end_dt)
    ls_cache = prefetch_binance_ls_ratio(start_dt, end_dt)
    macro_cache = prefetch_macro(args.start, args.end)
    daily_candles = prefetch_upbit_daily(start_dt, end_dt)

    prefetch_time = time.time() - t_start
    print(f"\n✅ Pre-fetch 완료 ({prefetch_time:.1f}s)")

    # ── Phase 2: 시뮬레이션 루프 ──
    sim_points = generate_sim_points(args.start, args.end)
    print(f"\n🔄 Phase 2: 시뮬레이션 ({len(sim_points)} 포인트)")

    # 체크포인트 & resume
    checkpoint = load_checkpoint() if args.resume else {}
    completed_cycles = set(checkpoint.get("completed_cycles", []))

    # Backtest 상태 파일 초기화
    if not args.resume:
        BACKTEST_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BACKTEST_STATE_FILE, "w") as f:
            json.dump({
                "active_agent": "conservative",
                "transition_from": None,
                "transition_started": None,
                "transition_duration_min": None,
                "last_switch_time": None,
                "last_trade_time": None,
                "consecutive_losses": 0,
                "switch_history": [],
            }, f)
        # auto_emergency 초기화
        try:
            BACKTEST_EMERGENCY_FILE.unlink(missing_ok=True)
        except Exception:
            pass

    portfolio = VirtualPortfolio(initial_krw=1_000_000)

    # 통계
    stats = {"buy": 0, "sell": 0, "hold": 0, "errors": 0, "skipped": 0, "embeddings": 0}
    total = len(sim_points)
    if args.limit > 0:
        sim_points = sim_points[:args.limit]
        total = len(sim_points)

    for i, sim_dt in enumerate(sim_points):
        cycle_id = sim_dt.strftime("%Y%m%d-%H%M") + "-backtest"

        # 이미 처리된 포인트 스킵
        if cycle_id in completed_cycles:
            stats["skipped"] += 1
            continue

        progress = f"[{i+1}/{total}]"
        date_str = sim_dt.strftime("%Y-%m-%d %H:%M")

        try:
            # 시장 데이터 구성
            market_data = collect_market_data_at(sim_dt, daily_candles)
            if not market_data:
                print(f"  {progress} {date_str} - ⚠️ 데이터 부족, 스킵", file=sys.stderr)
                stats["skipped"] += 1
                continue

            current_price = market_data["current_price"]

            # 포트폴리오 구성
            portfolio_dict = portfolio.to_dict(current_price)

            # 외부 데이터 구성
            external_data = build_external_data(
                sim_dt, fgi_cache, funding_cache, ls_cache, macro_cache, market_data
            )

            # FGI/뉴스를 market_data에 주입 (Orchestrator 기대 구조)
            market_data["fear_greed"] = external_data["sources"]["fear_greed"].get("current", {})
            market_data["news"] = external_data["sources"].get("news", {})

            # Orchestrator 실행
            result = run_orchestrator_isolated(market_data, external_data, portfolio_dict)
            decision = result.get("decision", {})
            dec_action = decision.get("decision", "hold")

            # 가상 매매 실행
            exec_result = {"executed": False}
            trade_params = decision.get("trade_params", {})
            if dec_action == "buy" and trade_params:
                amount = trade_params.get("amount", 100000)
                exec_result = portfolio.execute_buy(amount, current_price)
            elif dec_action == "sell" and trade_params:
                volume = trade_params.get("volume", portfolio.btc)
                if volume > 0:
                    exec_result = portfolio.execute_sell(volume, current_price)

            # 통계
            stats[dec_action] = stats.get(dec_action, 0) + 1

            # DB 저장
            decision_id = save_to_db(
                sim_dt, decision, market_data, external_data,
                portfolio_dict, result, cycle_id, dry_run=args.dry_run,
            )

            # 임베딩
            emb_ok = False
            if decision_id and not args.no_embedding and not args.dry_run:
                time.sleep(1.2)  # Gemini rate limit
                emb_ok = save_embedding(decision_id, market_data, external_data)
                if emb_ok:
                    stats["embeddings"] += 1

            # 사후추적
            if decision_id and not args.dry_run:
                save_retrospective(
                    decision_id, sim_dt, dec_action,
                    current_price, daily_candles,
                )

            # 체크포인트 업데이트
            completed_cycles.add(cycle_id)
            if (i + 1) % 10 == 0:
                save_checkpoint({
                    "completed_cycles": list(completed_cycles),
                    "last_completed": cycle_id,
                    "stats": stats,
                })

            # 진행 상황 출력
            agent = result.get("active_agent", "?")
            fgi_val = fgi_cache.get(sim_dt.strftime("%Y-%m-%d"), "?")
            exec_mark = "✅" if exec_result.get("executed") else ""
            emb_mark = "🧠" if emb_ok else ""
            print(
                f"  {progress} {date_str} | {dec_action:4s} {exec_mark}{emb_mark} "
                f"| FGI={fgi_val} RSI={market_data['indicators']['rsi_14']:.0f} "
                f"| {agent} | {portfolio.summary(current_price)}"
            )

        except Exception as e:
            stats["errors"] += 1
            print(f"  {progress} {date_str} - ❌ 에러: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            continue

    # ── Phase 3: 완료 ──
    elapsed = time.time() - t_start

    # 최종 체크포인트 저장
    save_checkpoint({
        "completed_cycles": list(completed_cycles),
        "stats": stats,
        "completed_at": datetime.now(KST).isoformat(),
    })

    # 최종 가격 (마지막 시뮬레이션 포인트)
    last_price = 0
    if sim_points:
        last_date = sim_points[-1].strftime("%Y-%m-%d")
        for c in reversed(daily_candles):
            if c["candle_date_time_kst"][:10] <= last_date:
                last_price = c["trade_price"]
                break

    print("\n" + "=" * 60)
    print("📊 백테스트 완료 요약")
    print("=" * 60)
    print(f"  기간: {args.start} ~ {args.end}")
    print(f"  포인트: {total}개 (스킵: {stats['skipped']})")
    print(f"  매수: {stats['buy']} | 매도: {stats['sell']} | 관망: {stats['hold']}")
    print(f"  에러: {stats['errors']}")
    print(f"  임베딩: {stats['embeddings']}건")
    print(f"  소요: {elapsed:.1f}s ({elapsed/max(total-stats['skipped'],1):.1f}s/포인트)")
    if last_price:
        print(f"  최종 포트폴리오: {portfolio.summary(last_price)}")
    print(f"  총 수수료: {portfolio.total_fees:,.0f} KRW")
    print(f"  매매 횟수: {portfolio.trade_count}")
    print("=" * 60)

    # 텔레그램 알림 (실 실행 시)
    if not args.dry_run:
        try:
            _send_telegram_summary(stats, portfolio, last_price, elapsed, args)
        except Exception as e:
            print(f"[telegram] 알림 실패: {e}", file=sys.stderr)


def _send_telegram_summary(
    stats: dict, portfolio: VirtualPortfolio,
    last_price: int, elapsed: float, args,
):
    """텔레그램 완료 알림."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_USER_ID")
    if not bot_token or not chat_id:
        return

    total_val = portfolio.krw + portfolio.btc * last_price
    pnl = total_val - 1_000_000

    text = (
        f"🔬 *백테스트 완료*\n\n"
        f"📅 기간: {args.start} \\~ {args.end}\n"
        f"📊 매수 {stats['buy']} / 매도 {stats['sell']} / 관망 {stats['hold']}\n"
        f"🧠 임베딩: {stats['embeddings']}건\n"
        f"⏱️ 소요: {elapsed:.0f}s\n\n"
        f"💰 최종: {total_val:,.0f} KRW \\({pnl:+,.0f}\\)\n"
        f"📈 수익률: {pnl/10000:+.1f}%"
    )

    try:
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "MarkdownV2",
            },
            timeout=10,
        )
    except Exception:
        pass


if __name__ == "__main__":
    main()
