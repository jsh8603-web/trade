#!/usr/bin/env python3
"""
2024년 히스토리컬 데이터 수집 + Gemini 임베딩 + Supabase 벡터 저장

수집 항목:
  1) Upbit BTC/KRW 4시간봉 (2023-12-15 ~ 2024-11-30)
  2) Yahoo Finance 매크로 일봉 (S&P500, NASDAQ, DXY, Gold, Oil, 10Y)
  3) 히스토리컬 FGI (Fear & Greed Index)
  4) 시뮬레이션 외부 데이터 (뉴스감성, 고래동향, SNS감성)
  5) 기술지표 계산 (RSI, SMA, MACD)
  6) RAG 임베딩용 텍스트 생성
  7) Gemini embedding-001 벡터 생성 (3072d)
  8) Supabase rag_analysis_vectors 테이블에 저장

출력: data/historical_2024/ 디렉토리에 JSON 파일 + Supabase DB
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

KST = timezone(timedelta(hours=9))
UTC = timezone.utc

# ── 설정 ──────────────────────────────────────────────
DATA_START = datetime(2023, 12, 15, 0, 0, tzinfo=KST)  # RSI/SMA 선행 데이터
DATA_END = datetime(2024, 11, 30, 23, 59, tzinfo=KST)
SIM_START = datetime(2024, 1, 1, 0, 0, tzinfo=KST)      # 실제 시뮬 시작

OUTPUT_DIR = PROJECT_DIR / "data" / "historical_2024"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(2024_01)  # 재현성

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
YAHOO_SYMBOLS = {
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "dxy": "DX-Y.NYB",
    "gold": "GC=F",
    "oil": "CL=F",
    "us10y": "^TNX",
}

# Gemini / Supabase 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

EMBEDDING_ENABLED = bool(GEMINI_API_KEY)
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)

# Gemini rate limit (10 RPM 기본)
GEMINI_RPM = 10
_gemini_last_call = 0.0


# =====================================================
#  Phase 1: Upbit 4시간봉 캔들
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


def collect_upbit_candles() -> list[dict]:
    """2023-12-15 ~ 2024-11-30 전체 4시간봉 수집."""
    all_candles = []
    cursor = DATA_END + timedelta(hours=4)

    print("[1/7] Upbit 4시간봉 캔들 수집 중 (2024년)...")
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
        if oldest <= DATA_START:
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
        if DATA_START <= dt <= DATA_END:
            c["_dt_kst"] = dt.isoformat()
            filtered.append(c)

    print(f"  -> {len(filtered)}개 캔들 수집 완료")
    return filtered


# =====================================================
#  Phase 2: Yahoo Finance 매크로 일봉 (2024년 실제 데이터)
# =====================================================

def fetch_yahoo_historical(symbol: str, period1: int, period2: int) -> list[dict]:
    """Yahoo Finance에서 히스토리컬 일봉을 수집한다."""
    url = YAHOO_CHART.format(symbol=symbol)
    params = {
        "period1": period1,
        "period2": period2,
        "interval": "1d",
        "includePrePost": "false",
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    for retry in range(3):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=20)
            if resp.status_code != 200:
                if retry < 2:
                    time.sleep(3 * (retry + 1))
                    continue
                print(f"  ! Yahoo {symbol} HTTP {resp.status_code}")
                return []
            data = resp.json()
            result = data.get("chart", {}).get("result", [])
            if not result:
                return []
            chart = result[0]
            timestamps = chart.get("timestamp", [])
            quotes = chart.get("indicators", {}).get("quote", [{}])[0]
            closes = quotes.get("close", [])
            opens = quotes.get("open", [])
            highs = quotes.get("high", [])
            lows = quotes.get("low", [])

            rows = []
            for i, ts in enumerate(timestamps):
                if i < len(closes) and closes[i] is not None:
                    dt = datetime.fromtimestamp(ts, tz=UTC)
                    rows.append({
                        "date": dt.strftime("%Y-%m-%d"),
                        "timestamp": ts,
                        "open": opens[i] if i < len(opens) else None,
                        "high": highs[i] if i < len(highs) else None,
                        "low": lows[i] if i < len(lows) else None,
                        "close": closes[i],
                    })
            return rows
        except Exception as e:
            if retry < 2:
                time.sleep(3 * (retry + 1))
            else:
                print(f"  ! Yahoo {symbol} 오류: {e}")
                return []
    return []


def collect_yahoo_macro() -> dict[str, list[dict]]:
    """2024년 전체 Yahoo Finance 매크로 일봉 수집."""
    print("[2/7] Yahoo Finance 매크로 수집 중 (2024년 실제 데이터)...")
    period1 = int(datetime(2023, 12, 1, tzinfo=UTC).timestamp())
    period2 = int(datetime(2024, 12, 5, tzinfo=UTC).timestamp())

    all_macro = {}
    for name, symbol in YAHOO_SYMBOLS.items():
        rows = fetch_yahoo_historical(symbol, period1, period2)
        all_macro[name] = rows
        print(f"  {name} ({symbol}): {len(rows)}일")
        time.sleep(0.5)

    return all_macro


def build_macro_daily_map(macro_data: dict[str, list[dict]]) -> dict[str, dict]:
    """날짜별 매크로 스코어를 계산한다 (실제 Yahoo 데이터 기반)."""
    date_map: dict[str, dict[str, float]] = {}
    for name, rows in macro_data.items():
        for row in rows:
            d = row["date"]
            if d not in date_map:
                date_map[d] = {}
            date_map[d][name] = row["close"]

    sorted_dates = sorted(date_map.keys())
    daily_scores = {}

    for i, date in enumerate(sorted_dates):
        vals = date_map[date]
        score = 0
        signals = []
        prev_vals = date_map.get(sorted_dates[i - 1], {}) if i > 0 else {}

        # S&P500
        if "sp500" in vals and "sp500" in prev_vals and prev_vals["sp500"]:
            sp_chg = (vals["sp500"] - prev_vals["sp500"]) / prev_vals["sp500"] * 100
            if sp_chg > 1.0:
                score += 5
                signals.append(f"S&P500 +{sp_chg:.1f}%")
            elif sp_chg < -1.0:
                score -= 5
                signals.append(f"S&P500 {sp_chg:.1f}%")

        # DXY (역상관)
        if "dxy" in vals and "dxy" in prev_vals and prev_vals["dxy"]:
            dxy_chg = (vals["dxy"] - prev_vals["dxy"]) / prev_vals["dxy"] * 100
            if dxy_chg > 0.5:
                score -= 3
                signals.append(f"DXY +{dxy_chg:.1f}% (역상관)")
            elif dxy_chg < -0.5:
                score += 3
                signals.append(f"DXY {dxy_chg:.1f}% (BTC 우호)")

        # Gold
        if "gold" in vals and "gold" in prev_vals and prev_vals["gold"]:
            gold_chg = (vals["gold"] - prev_vals["gold"]) / prev_vals["gold"] * 100
            if gold_chg > 1.0:
                score += 2
            elif gold_chg < -1.0:
                score -= 2

        # 10Y 국채금리 (역상관)
        if "us10y" in vals and "us10y" in prev_vals and prev_vals["us10y"]:
            y10_chg = (vals["us10y"] - prev_vals["us10y"]) / prev_vals["us10y"] * 100
            if y10_chg > 2:
                score -= 4
                signals.append(f"10Y 금리 급등 +{y10_chg:.1f}%")
            elif y10_chg < -2:
                score += 4
                signals.append(f"10Y 금리 하락 {y10_chg:.1f}%")

        # Oil
        if "oil" in vals and "oil" in prev_vals and prev_vals["oil"]:
            oil_chg = (vals["oil"] - prev_vals["oil"]) / prev_vals["oil"] * 100
            if oil_chg > 3:
                score -= 2
            elif oil_chg < -3:
                score += 1

        score = max(-30, min(30, score))

        if score >= 8:
            sentiment = "risk_on"
        elif score >= 3:
            sentiment = "slightly_bullish"
        elif score <= -8:
            sentiment = "risk_off"
        elif score <= -3:
            sentiment = "slightly_bearish"
        else:
            sentiment = "neutral"

        daily_scores[date] = {
            "macro_score": score,
            "sentiment": sentiment,
            "signals": signals,
            "raw_prices": vals,
        }

    return daily_scores


# =====================================================
#  Phase 3: 히스토리컬 FGI
# =====================================================

def fetch_historical_fgi() -> dict[str, dict]:
    print("[3/7] 히스토리컬 FGI 수집 중...")
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

    # 2024년 + 2023-12 필터
    fgi_2024 = {k: v for k, v in fgi_map.items() if k.startswith("2024") or k.startswith("2023-12")}
    print(f"  -> {len(fgi_2024)}일 FGI 수집 완료")
    return fgi_2024


# =====================================================
#  Phase 4: 기술지표 계산
# =====================================================

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


# =====================================================
#  Phase 5: 외부 데이터 시뮬레이션 (뉴스/고래/SNS)
# =====================================================

def simulate_external(dt: datetime, price: float, rsi: float,
                      change_24h: float, fgi_val: int,
                      macro_score: float) -> dict:
    """뉴스 감성, 고래 동향, SNS 감성을 시뮬레이션한다."""

    # ── 뉴스 감성 ──
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

    # ── 고래 동향 ──
    whale_buy = random.randint(0, 5)
    whale_sell = random.randint(0, 4)
    if change_24h < -3:
        whale_buy += random.randint(1, 3)
    elif change_24h > 3:
        whale_sell += random.randint(1, 3)
    whale_direction = "bullish" if whale_buy > whale_sell + 1 else (
        "bearish" if whale_sell > whale_buy + 1 else "neutral"
    )
    net_flow_btc = round((whale_buy - whale_sell) * random.uniform(5, 50), 2)

    # ── SNS 감성 ──
    sns_base = (fgi_val - 50) / 50
    sns_score = sns_base + random.uniform(-0.3, 0.3)
    sns_score = max(-1.0, min(1.0, sns_score))
    sns_sentiment = "bullish" if sns_score > 0.2 else ("bearish" if sns_score < -0.2 else "neutral")

    # ── 김치 프리미엄 / 롱숏비 / 펀딩비 ──
    kimchi_pct = round((fgi_val - 50) * 0.04 + random.uniform(-1.0, 1.0), 2)
    ls_ratio = round(max(0.5, min(2.0, 1.0 + change_24h * 0.03 + random.uniform(-0.15, 0.15))), 2)
    funding_rate = round((ls_ratio - 1.0) * 0.01 + random.uniform(-0.005, 0.005), 5)

    # ── Data Fusion ──
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

    external_bonus = {
        "strong_buy": 20, "buy": 10, "neutral": 0, "sell": -5, "strong_sell": -10
    }.get(fusion_signal, 0)

    return {
        "news": {
            "sentiment": news_sentiment,
            "score": round(news_score, 3),
            "headline_count": random.randint(5, 30),
        },
        "whale": {
            "direction": whale_direction,
            "buy_count": whale_buy,
            "sell_count": whale_sell,
            "net_flow_btc": net_flow_btc,
        },
        "sns": {
            "sentiment": sns_sentiment,
            "score": round(sns_score, 3),
            "post_count": random.randint(50, 500),
        },
        "binance": {
            "kimchi_premium_pct": kimchi_pct,
            "long_short_ratio": ls_ratio,
            "funding_rate": funding_rate,
        },
        "macro": {
            "score": macro_score,
            "source": "yahoo_finance_real",
        },
        "fusion": {
            "signal": fusion_signal,
            "score": fusion_score,
            "strategy_bonus": external_bonus,
        },
    }


# =====================================================
#  Phase 6: RAG 임베딩 텍스트 생성
# =====================================================

def build_embedding_text(dt: datetime, indicators: dict, fgi: dict,
                         external: dict, macro_daily: dict) -> str:
    """RAG 임베딩용 분석 텍스트를 생성한다."""
    date_str = dt.strftime("%Y-%m-%d %H:%M")
    price = indicators["current_price"]
    rsi = indicators["rsi_14"]
    sma_dev = indicators["sma_deviation_pct"]
    fgi_val = fgi["value"]
    fgi_class = fgi.get("classification", "Unknown")
    change_24h = indicators["price_change_24h"]
    macro = external["macro"]
    news = external["news"]
    whale = external["whale"]
    sns = external["sns"]
    fusion = external["fusion"]

    text = f"""[시장 분석 {date_str} KST]
BTC/KRW 가격: {price:,.0f}원 (24h {change_24h:+.1f}%)
기술지표: RSI {rsi:.1f}, SMA20 이탈 {sma_dev:+.1f}%, MACD {'골든크로스' if indicators.get('macd', {}).get('golden_cross') else '데드크로스'}
공포탐욕지수: {fgi_val} ({fgi_class})
매크로: score {macro['score']} ({macro.get('source', 'simulated')})
뉴스감성: {news['sentiment']} (score {news['score']:.2f})
고래동향: {whale['direction']} (매수{whale['buy_count']}건 vs 매도{whale['sell_count']}건, 순유출 {whale['net_flow_btc']:+.1f}BTC)
SNS감성: {sns['sentiment']} (score {sns['score']:.2f})
바이낸스: 김프 {external['binance']['kimchi_premium_pct']:+.1f}%, L/S {external['binance']['long_short_ratio']:.2f}, 펀딩 {external['binance']['funding_rate']:.4f}
Data Fusion: {fusion['signal']} (score {fusion['score']})"""
    return text


# =====================================================
#  Phase 7: Gemini 임베딩 생성 + Supabase 저장
# =====================================================

def gemini_rate_limit():
    """Gemini RPM 제한 준수."""
    global _gemini_last_call
    min_interval = 60.0 / GEMINI_RPM
    elapsed = time.time() - _gemini_last_call
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    _gemini_last_call = time.time()


def generate_gemini_embedding(text: str) -> list[float] | None:
    """Gemini embedding-001으로 3072차원 벡터 생성."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
    except ImportError:
        print("  ! google-generativeai 패키지 없음, 임베딩 스킵")
        return None

    gemini_rate_limit()
    try:
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document",
        )
        return result["embedding"]
    except Exception as e:
        print(f"  ! Gemini 임베딩 실패: {e}")
        return None


def store_to_supabase(cycle_id: str, analysis_text: str, analysis_json: dict,
                      embedding: list[float], market_regime: str) -> bool:
    """Supabase rag_analysis_vectors에 저장."""
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    payload = {
        "cycle_id": cycle_id,
        "analysis_text": analysis_text,
        "analysis_json": analysis_json,
        "market_regime": market_regime,
        "embedding": embedding,
    }
    try:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/rag_analysis_vectors",
            headers=headers,
            json=payload,
            timeout=15,
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


def determine_market_regime(fgi_val: int, rsi: float, change_24h: float,
                            macro_score: float) -> str:
    """시장 체제를 분류한다."""
    if fgi_val <= 20 or change_24h < -5:
        return "extreme_fear"
    elif fgi_val <= 35:
        return "fear"
    elif fgi_val >= 80 or change_24h > 5:
        return "extreme_greed"
    elif fgi_val >= 65:
        return "greed"
    elif abs(change_24h) < 1 and 40 <= rsi <= 60:
        return "sideways"
    elif rsi > 70:
        return "overbought"
    elif rsi < 30:
        return "oversold"
    else:
        return "neutral"


# =====================================================
#  Main: 전체 수집 + 조립 + 임베딩 + 저장
# =====================================================

def main():
    t0 = time.time()

    print(f"  Gemini 임베딩: {'[ON]' if EMBEDDING_ENABLED else '[OFF] (GEMINI_API_KEY 없음)'}")
    print(f"  Supabase 저장: {'[ON]' if SUPABASE_ENABLED else '[OFF] (SUPABASE 키 없음)'}")
    print()

    # 1) Upbit 캔들
    candles = collect_upbit_candles()
    if not candles:
        print("ERROR: 캔들 수집 실패")
        return

    candles_path = OUTPUT_DIR / "candles_4h.json"
    with open(candles_path, "w", encoding="utf-8") as f:
        json.dump(candles, f, ensure_ascii=False, indent=1)
    print(f"  저장: {candles_path} ({len(candles)}개)")

    # 2) Yahoo Finance 매크로
    macro_raw = collect_yahoo_macro()
    macro_path = OUTPUT_DIR / "macro_yahoo_raw.json"
    with open(macro_path, "w", encoding="utf-8") as f:
        json.dump(macro_raw, f, ensure_ascii=False, indent=1)
    print(f"  저장: {macro_path}")

    macro_daily = build_macro_daily_map(macro_raw)
    macro_daily_path = OUTPUT_DIR / "macro_daily_scores.json"
    with open(macro_daily_path, "w", encoding="utf-8") as f:
        json.dump(macro_daily, f, ensure_ascii=False, indent=1)
    print(f"  저장: {macro_daily_path} ({len(macro_daily)}일)")

    # 3) FGI
    fgi_map = fetch_historical_fgi()
    fgi_path = OUTPUT_DIR / "fgi_historical.json"
    with open(fgi_path, "w", encoding="utf-8") as f:
        json.dump(fgi_map, f, ensure_ascii=False, indent=1)
    print(f"  저장: {fgi_path} ({len(fgi_map)}일)")

    # 4) 시뮬레이션 포인트 생성 + 기술지표 + 외부 데이터
    print("[4/7] 시뮬레이션 포인트 생성 중 (기술지표 + 외부 데이터)...")

    sim_points = []
    seen_times = set()
    for i, c in enumerate(candles):
        dt = datetime.fromisoformat(c["_dt_kst"])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        if dt < SIM_START:
            continue
        time_key = dt.strftime("%Y-%m-%d %H")
        if time_key in seen_times:
            continue
        seen_times.add(time_key)
        if i < 30:
            continue
        sim_points.append((i, dt))

    print(f"  시뮬레이션 포인트: {len(sim_points)}개")

    all_data_points = []
    embedding_texts = []

    for seq, (idx, dt) in enumerate(sim_points):
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

        indicators = {
            "current_price": price,
            "rsi_14": rsi,
            "sma_20": round(sma20),
            "sma_deviation_pct": round(sma_deviation, 2),
            "macd": macd,
            "price_change_24h": round(change_24h, 2),
            "volume": candles[idx].get("candle_acc_trade_volume", 0),
        }

        # FGI
        date_str = dt.strftime("%Y-%m-%d")
        fgi = fgi_map.get(date_str)
        if not fgi:
            for delta in range(1, 7):
                prev = (dt - timedelta(days=delta)).strftime("%Y-%m-%d")
                fgi = fgi_map.get(prev)
                if fgi:
                    break
        if not fgi:
            fgi = {"value": 50, "classification": "Neutral"}

        # 매크로 (실제 Yahoo 데이터)
        macro = macro_daily.get(date_str, {})
        if not macro:
            for delta in range(1, 5):
                prev = (dt - timedelta(days=delta)).strftime("%Y-%m-%d")
                macro = macro_daily.get(prev, {})
                if macro:
                    break
        macro_score = macro.get("macro_score", 0) if macro else 0

        # 외부 데이터 시뮬레이션
        external = simulate_external(dt, price, rsi, change_24h, fgi["value"], macro_score)

        # RAG 임베딩 텍스트
        emb_text = build_embedding_text(dt, indicators, fgi, external, macro_daily)

        # 시장 체제 분류
        market_regime = determine_market_regime(fgi["value"], rsi, change_24h, macro_score)

        data_point = {
            "seq": seq,
            "datetime": dt.isoformat(),
            "date": date_str,
            "indicators": indicators,
            "fgi": fgi,
            "macro": {
                "score": macro_score,
                "sentiment": macro.get("sentiment", "neutral") if macro else "neutral",
                "signals": macro.get("signals", []) if macro else [],
                "raw_prices": macro.get("raw_prices", {}) if macro else {},
            },
            "external": external,
            "market_regime": market_regime,
            "embedding_text": emb_text,
        }
        all_data_points.append(data_point)
        embedding_texts.append({"seq": seq, "datetime": dt.isoformat(), "text": emb_text})

        if (seq + 1) % 200 == 0:
            print(f"  ... {seq + 1}/{len(sim_points)} 완료")

    # 5) 로컬 파일 저장
    print(f"[5/7] 로컬 파일 저장 중... ({len(all_data_points)}개 포인트)")

    points_path = OUTPUT_DIR / "sim_data_points.json"
    with open(points_path, "w", encoding="utf-8") as f:
        json.dump(all_data_points, f, ensure_ascii=False, indent=1)
    print(f"  저장: {points_path}")

    emb_path = OUTPUT_DIR / "embedding_texts.json"
    with open(emb_path, "w", encoding="utf-8") as f:
        json.dump(embedding_texts, f, ensure_ascii=False, indent=1)
    print(f"  저장: {emb_path}")

    # 6) Gemini 임베딩 생성
    embeddings_generated = 0
    embeddings_failed = 0
    all_embeddings = []  # (seq, embedding) 튜플

    if EMBEDDING_ENABLED:
        print(f"[6/7] Gemini 임베딩 생성 중... ({len(all_data_points)}개, ~{len(all_data_points) * 6 // 60}분 소요 예상)")
        for i, dp in enumerate(all_data_points):
            emb_text = dp["embedding_text"]
            embedding = generate_gemini_embedding(emb_text)
            if embedding:
                all_embeddings.append((dp["seq"], embedding))
                embeddings_generated += 1
            else:
                embeddings_failed += 1

            if (i + 1) % 50 == 0:
                print(f"  ... {i + 1}/{len(all_data_points)} 임베딩 완료 (성공: {embeddings_generated}, 실패: {embeddings_failed})")

        # 임베딩 벡터를 로컬에도 저장 (재사용용)
        emb_vectors_path = OUTPUT_DIR / "embedding_vectors.json"
        with open(emb_vectors_path, "w", encoding="utf-8") as f:
            json.dump(
                [{"seq": seq, "dim": len(emb), "vector": emb} for seq, emb in all_embeddings],
                f, ensure_ascii=False,
            )
        print(f"  저장: {emb_vectors_path} ({embeddings_generated}개 벡터)")
    else:
        print("[6/7] Gemini 임베딩 스킵 (API 키 없음)")

    # 7) Supabase 저장
    supabase_stored = 0
    supabase_failed = 0

    if SUPABASE_ENABLED and all_embeddings:
        print(f"[7/7] Supabase 벡터 저장 중... ({len(all_embeddings)}건)")
        emb_map = {seq: emb for seq, emb in all_embeddings}

        for i, dp in enumerate(all_data_points):
            seq = dp["seq"]
            if seq not in emb_map:
                continue

            cycle_id = f"hist_2024_{dp['datetime']}"
            analysis_json = {
                "year": 2024,
                "source": "historical_simulation",
                "indicators": dp["indicators"],
                "fgi": dp["fgi"],
                "macro": dp["macro"],
                "external_summary": {
                    "news": dp["external"]["news"]["sentiment"],
                    "whale": dp["external"]["whale"]["direction"],
                    "sns": dp["external"]["sns"]["sentiment"],
                    "fusion": dp["external"]["fusion"]["signal"],
                },
            }

            ok = store_to_supabase(
                cycle_id=cycle_id,
                analysis_text=dp["embedding_text"],
                analysis_json=analysis_json,
                embedding=emb_map[seq],
                market_regime=dp.get("market_regime", "neutral"),
            )
            if ok:
                supabase_stored += 1
            else:
                supabase_failed += 1

            if (i + 1) % 100 == 0:
                print(f"  ... {supabase_stored}건 저장, {supabase_failed}건 실패")

        print(f"  Supabase 완료: {supabase_stored}건 저장, {supabase_failed}건 실패")
    elif not SUPABASE_ENABLED:
        print("[7/7] Supabase 저장 스킵 (키 없음)")
    else:
        print("[7/7] Supabase 저장 스킵 (임베딩 없음)")

    # 요약 통계
    prices = [p["indicators"]["current_price"] for p in all_data_points]
    fgi_vals = [p["fgi"]["value"] for p in all_data_points]
    macro_scores = [p["macro"]["score"] for p in all_data_points]

    # 시장 체제 분포
    regime_dist = {}
    for dp in all_data_points:
        r = dp.get("market_regime", "unknown")
        regime_dist[r] = regime_dist.get(r, 0) + 1

    summary = {
        "period": f"{SIM_START.strftime('%Y-%m-%d')} ~ {DATA_END.strftime('%Y-%m-%d')}",
        "total_candles": len(candles),
        "sim_points": len(all_data_points),
        "price_range": {"min": min(prices), "max": max(prices), "start": prices[0], "end": prices[-1]},
        "fgi_range": {"min": min(fgi_vals), "max": max(fgi_vals), "avg": round(sum(fgi_vals) / len(fgi_vals), 1)},
        "macro_range": {"min": min(macro_scores), "max": max(macro_scores), "avg": round(sum(macro_scores) / len(macro_scores), 1)},
        "market_regime_distribution": regime_dist,
        "macro_source": "yahoo_finance_real",
        "external_source": "simulated (news, whale, sns)",
        "fgi_source": "alternative.me_real",
        "candle_source": "upbit_real",
        "embedding": {
            "model": "gemini-embedding-001",
            "dim": 3072,
            "generated": embeddings_generated,
            "failed": embeddings_failed,
        },
        "supabase": {
            "stored": supabase_stored,
            "failed": supabase_failed,
        },
        "collection_time_sec": round(time.time() - t0, 1),
        "files": [
            "candles_4h.json",
            "macro_yahoo_raw.json",
            "macro_daily_scores.json",
            "fgi_historical.json",
            "sim_data_points.json",
            "embedding_texts.json",
            "embedding_vectors.json",
            "summary.json",
        ],
    }
    summary_path = OUTPUT_DIR / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print("  2024년 데이터 수집 완료!")
    print(f"  기간: {summary['period']}")
    print(f"  캔들: {summary['total_candles']}개")
    print(f"  시뮬 포인트: {summary['sim_points']}개")
    print(f"  BTC 가격: {min(prices):,.0f} ~ {max(prices):,.0f}원")
    print(f"  FGI: {min(fgi_vals)} ~ {max(fgi_vals)} (평균 {summary['fgi_range']['avg']})")
    print(f"  매크로: {min(macro_scores)} ~ {max(macro_scores)} (평균 {summary['macro_range']['avg']}, Yahoo 실제)")
    print(f"  시장체제: {regime_dist}")
    print(f"  Gemini 임베딩: {embeddings_generated}건 생성, {embeddings_failed}건 실패")
    print(f"  Supabase 저장: {supabase_stored}건 저장, {supabase_failed}건 실패")
    print(f"  소요시간: {elapsed:.0f}초")
    print(f"  출력: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
