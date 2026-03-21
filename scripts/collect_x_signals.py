#!/usr/bin/env python3
"""뉴스랑(NewsRang) — X(트위터) 크립토 시그널 수집기 (twikit 기반, 무료)

X 계정 로그인으로 크립토 핵심 계정 + 키워드 검색을 수행한다.
감성 분석은 키워드 기반 + CryptoBERT(선택) 사용.

모니터링 대상:
  - @whale_alert: 대량 송금 알림
  - @lookonchain: 온체인 분석
  - @WatcherGuru: 속보
  - @ArkhamIntel: 기관 지갑 추적
  - @tier10k: 경제 이벤트 속보

필요 환경변수:
  X_USERNAME: X 로그인 아이디
  X_PASSWORD: X 비밀번호
  X_EMAIL: X 등록 이메일 (2FA 인증용)

출력: JSON (stdout)

Usage:
  python scripts/collect_x_signals.py
  python scripts/collect_x_signals.py --search-only
  python scripts/collect_x_signals.py --accounts-only
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# ─── 설정 ──────────────────────────────────────────────────

X_USERNAME = os.getenv("X_USERNAME", "")
X_PASSWORD = os.getenv("X_PASSWORD", "")
X_EMAIL = os.getenv("X_EMAIL", "")

COOKIES_FILE = Path(__file__).resolve().parent.parent / "data" / "x_cookies.json"

# 모니터링 계정 (시그널 가치 높은 순)
SIGNAL_ACCOUNTS = [
    {"username": "whale_alert", "category": "whale", "weight": 3},
    {"username": "lookonchain", "category": "onchain", "weight": 3},
    {"username": "WatcherGuru", "category": "breaking", "weight": 2},
    {"username": "ArkhamIntel", "category": "institution", "weight": 2},
    {"username": "tier10k", "category": "macro", "weight": 2},
    {"username": "BitcoinMagazine", "category": "crypto_news", "weight": 1},
    {"username": "CoinDesk", "category": "crypto_news", "weight": 1},
]

# 검색 키워드
SEARCH_QUERIES = [
    {"query": "bitcoin BTC breaking", "category": "btc_breaking", "max_results": 10},
    {"query": "crypto regulation SEC ETF", "category": "regulation", "max_results": 5},
    {"query": "bitcoin whale transfer", "category": "whale_move", "max_results": 5},
]

# 감성 키워드
BULLISH_KEYWORDS = [
    "bullish", "moon", "pump", "surge", "rally", "breakout", "ath",
    "all time high", "accumulate", "buy", "long", "etf approved",
    "institutional", "inflow", "adoption", "upgrade",
    "상승", "급등", "돌파", "강세", "매수", "반등", "사상최고",
]

BEARISH_KEYWORDS = [
    "bearish", "dump", "crash", "plunge", "liquidation", "hack",
    "scam", "fraud", "ban", "sell", "short", "panic", "collapse",
    "bankruptcy", "sec lawsuit", "exploit",
    "폭락", "급락", "하락", "매도", "해킹", "사기", "파산", "청산",
]

WHALE_KEYWORDS = [
    "transferred", "moved", "whale", "million", "billion",
    "exchange", "deposit", "withdraw", "unknown wallet",
]

# ─── twikit 클라이언트 ────────────────────────────────────────


async def get_client():
    """twikit 클라이언트를 생성하고 로그인한다.
    쿠키 파일이 있으면 재사용하고, 없을 때만 로그인한다.
    """
    try:
        from twikit import Client
    except ImportError:
        print("[X] twikit 미설치. pip install twikit", file=sys.stderr)
        return None

    if not X_USERNAME or not X_PASSWORD:
        return None

    client = Client("en-US")
    COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 저장된 쿠키로 복원 시도
    if COOKIES_FILE.exists():
        try:
            client.load_cookies(str(COOKIES_FILE))
            # 쿠키 유효성 체크: 자신의 프로필 조회로 세션 활성 여부 확인
            try:
                await client.get_user_by_screen_name(X_USERNAME)
            except Exception as validity_err:
                print(f"[X] 쿠키 유효성 검증 실패, 재로그인 시도: {validity_err}", file=sys.stderr)
                raise validity_err
            return client
        except Exception as e:
            print(f"[X] 쿠키 복원 실패, 재로그인 시도: {e}", file=sys.stderr)

    # 새로 로그인 (cookies_file 자동 저장 + UI 메트릭 활성화)
    try:
        await client.login(
            auth_info_1=X_USERNAME,
            auth_info_2=X_EMAIL,
            password=X_PASSWORD,
            cookies_file=str(COOKIES_FILE),
            enable_ui_metrics=True,
        )
        return client
    except Exception as e:
        err_msg = str(e)
        if "KEY_BYTE" in err_msg:
            print(f"[X] 로그인 레이트리밋 — 잠시 후 재시도 필요 (쿠키가 생기면 이후 자동 복원)", file=sys.stderr)
        else:
            print(f"[X] 로그인 실패: {e}", file=sys.stderr)
        return None


# ─── 계정 트윗 수집 ──────────────────────────────────────────


async def fetch_account_tweets(client, account: dict, max_tweets: int = 5) -> list[dict]:
    """특정 계정의 최근 트윗을 수집한다."""
    try:
        user = await client.get_user_by_screen_name(account["username"])
        if not user:
            return []

        tweets = await user.get_tweets("Tweets", count=max_tweets)
        results = []
        for tweet in tweets:
            text = tweet.text if hasattr(tweet, "text") else str(tweet)
            created = tweet.created_at if hasattr(tweet, "created_at") else ""

            # 24시간 이내 트윗만
            if created:
                try:
                    tweet_time = datetime.strptime(str(created), "%a %b %d %H:%M:%S %z %Y")
                    if (datetime.now(timezone.utc) - tweet_time).total_seconds() > 86400:
                        continue
                except (ValueError, TypeError):
                    pass

            sentiment = _analyze_tweet_sentiment(text)
            whale_signal = _detect_whale_signal(text) if account["category"] == "whale" else None

            results.append({
                "account": account["username"],
                "category": account["category"],
                "weight": account["weight"],
                "text": text[:500],
                "created_at": str(created),
                "sentiment": sentiment,
                "whale_signal": whale_signal,
                "likes": tweet.favorite_count if hasattr(tweet, "favorite_count") else 0,
                "retweets": tweet.retweet_count if hasattr(tweet, "retweet_count") else 0,
            })

        return results

    except Exception as e:
        print(f"[X] @{account['username']} 수집 실패: {e}", file=sys.stderr)
        return []


# ─── 키워드 검색 ──────────────────────────────────────────────


async def search_tweets(client, query_info: dict) -> list[dict]:
    """키워드로 트윗을 검색한다."""
    try:
        tweets = await client.search_tweet(
            query_info["query"],
            product="Latest",
            count=query_info["max_results"],
        )

        results = []
        for tweet in tweets:
            text = tweet.text if hasattr(tweet, "text") else str(tweet)
            user = tweet.user.screen_name if hasattr(tweet, "user") and tweet.user else "unknown"
            created = tweet.created_at if hasattr(tweet, "created_at") else ""

            sentiment = _analyze_tweet_sentiment(text)

            results.append({
                "account": user,
                "category": query_info["category"],
                "weight": 1,
                "text": text[:500],
                "created_at": str(created),
                "sentiment": sentiment,
                "whale_signal": None,
                "likes": tweet.favorite_count if hasattr(tweet, "favorite_count") else 0,
                "retweets": tweet.retweet_count if hasattr(tweet, "retweet_count") else 0,
            })

        return results

    except Exception as e:
        print(f"[X] 검색 실패 '{query_info['query'][:30]}': {e}", file=sys.stderr)
        return []


# ─── 감성 분석 ────────────────────────────────────────────────


def _analyze_tweet_sentiment(text: str) -> dict:
    """키워드 기반 트윗 감성 분석"""
    text_lower = text.lower()

    bullish_hits = [kw for kw in BULLISH_KEYWORDS if kw in text_lower]
    bearish_hits = [kw for kw in BEARISH_KEYWORDS if kw in text_lower]

    if bullish_hits and not bearish_hits:
        label = "bullish"
        score = min(100, len(bullish_hits) * 25)
    elif bearish_hits and not bullish_hits:
        label = "bearish"
        score = max(-100, -len(bearish_hits) * 25)
    elif bullish_hits and bearish_hits:
        label = "mixed"
        score = (len(bullish_hits) - len(bearish_hits)) * 15
    else:
        label = "neutral"
        score = 0

    return {"label": label, "score": score}


def _detect_whale_signal(text: str) -> dict | None:
    """고래 알림 트윗에서 금액/방향 추출"""
    text_lower = text.lower()
    if not any(kw in text_lower for kw in WHALE_KEYWORDS):
        return None

    import re

    # 금액 추출 ($XXX,XXX,XXX 패턴)
    amounts = re.findall(r'\$[\d,]+(?:\.\d+)?', text)
    amount_str = amounts[0] if amounts else ""

    # BTC 수량 추출
    btc_amounts = re.findall(r'([\d,]+(?:\.\d+)?)\s*(?:BTC|bitcoin)', text_lower)
    btc_str = btc_amounts[0] if btc_amounts else ""

    # 방향 판단
    direction = "unknown"
    if "deposit" in text_lower or "to exchange" in text_lower or "to binance" in text_lower:
        direction = "sell_pressure"  # 거래소 입금 = 매도 압력
    elif "withdraw" in text_lower or "from exchange" in text_lower or "from binance" in text_lower:
        direction = "buy_pressure"  # 거래소 출금 = 매수 압력
    elif "unknown wallet" in text_lower:
        direction = "accumulation"

    return {
        "amount": amount_str,
        "btc_amount": btc_str,
        "direction": direction,
    }


# ─── 종합 스코어 ─────────────────────────────────────────────


def calculate_x_signal(tweets: list[dict]) -> dict:
    """수집된 트윗에서 종합 시그널을 산출한다."""
    if not tweets:
        return {
            "score": 0,
            "signal": "no_data",
            "tweet_count": 0,
            "bullish_count": 0,
            "bearish_count": 0,
        }

    weighted_score = 0
    total_weight = 0
    bullish = 0
    bearish = 0
    neutral = 0
    whale_signals = []

    for tweet in tweets:
        weight = tweet.get("weight", 1)
        sentiment = tweet.get("sentiment", {})
        label = sentiment.get("label", "neutral")
        s = sentiment.get("score", 0)

        # 인기도 가중 (좋아요+RT 많으면 영향력 높음)
        engagement = tweet.get("likes", 0) + tweet.get("retweets", 0) * 2
        engagement_mult = 1.0 + min(2.0, engagement / 1000)

        weighted_score += s * weight * engagement_mult
        total_weight += weight * engagement_mult

        if label == "bullish":
            bullish += 1
        elif label == "bearish":
            bearish += 1
        else:
            neutral += 1

        if tweet.get("whale_signal"):
            whale_signals.append(tweet["whale_signal"])

    # 정규화 (-100 ~ +100)
    final_score = int(weighted_score / total_weight) if total_weight > 0 else 0
    final_score = max(-100, min(100, final_score))

    # 시그널 판정
    if final_score >= 30:
        signal = "strong_bullish"
    elif final_score >= 10:
        signal = "bullish"
    elif final_score <= -30:
        signal = "strong_bearish"
    elif final_score <= -10:
        signal = "bearish"
    else:
        signal = "neutral"

    # 고래 요약
    whale_summary = None
    if whale_signals:
        sell_pressure = sum(1 for w in whale_signals if w["direction"] == "sell_pressure")
        buy_pressure = sum(1 for w in whale_signals if w["direction"] == "buy_pressure")
        whale_summary = {
            "total_alerts": len(whale_signals),
            "sell_pressure": sell_pressure,
            "buy_pressure": buy_pressure,
            "net_direction": "sell" if sell_pressure > buy_pressure else (
                "buy" if buy_pressure > sell_pressure else "neutral"
            ),
        }

    return {
        "score": final_score,
        "signal": signal,
        "tweet_count": len(tweets),
        "bullish_count": bullish,
        "bearish_count": bearish,
        "neutral_count": neutral,
        "whale_summary": whale_summary,
    }


# ─── 메인 ─────────────────────────────────────────────────────


async def collect_x_signals(accounts_only: bool = False, search_only: bool = False) -> dict:
    """X 시그널 전체 수집"""
    t0 = time.time()

    # X 미설정 시 빈 결과
    if not X_USERNAME:
        return {
            "timestamp": datetime.now(timezone(timedelta(hours=9))).isoformat(),
            "status": "disabled",
            "reason": "X_USERNAME not set in .env",
            "signal": {"score": 0, "signal": "no_data", "tweet_count": 0},
        }

    client = await get_client()
    if not client:
        return {
            "timestamp": datetime.now(timezone(timedelta(hours=9))).isoformat(),
            "status": "login_failed",
            "signal": {"score": 0, "signal": "no_data", "tweet_count": 0},
        }

    all_tweets = []
    errors = []

    # 1. 계정별 트윗 수집
    if not search_only:
        for account in SIGNAL_ACCOUNTS:
            try:
                tweets = await fetch_account_tweets(client, account, max_tweets=5)
                all_tweets.extend(tweets)
                await asyncio.sleep(1)  # 레이트리밋 방지
            except Exception as e:
                errors.append(f"@{account['username']}: {e}")

    # 2. 키워드 검색
    if not accounts_only:
        for query_info in SEARCH_QUERIES:
            try:
                tweets = await search_tweets(client, query_info)
                all_tweets.extend(tweets)
                await asyncio.sleep(1)
            except Exception as e:
                errors.append(f"search '{query_info['query'][:20]}': {e}")

    # 3. 종합 시그널 계산
    signal = calculate_x_signal(all_tweets)

    elapsed = round(time.time() - t0, 1)

    return {
        "timestamp": datetime.now(timezone(timedelta(hours=9))).isoformat(),
        "collection_time_sec": elapsed,
        "status": "ok",
        "signal": signal,
        "tweets_collected": len(all_tweets),
        "accounts_checked": len(SIGNAL_ACCOUNTS) if not search_only else 0,
        "searches_done": len(SEARCH_QUERIES) if not accounts_only else 0,
        "errors": errors,
        "tweets": all_tweets[:30],  # 최대 30개 원본
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="X(트위터) 크립토 시그널 수집")
    parser.add_argument("--accounts-only", action="store_true", help="계정 트윗만 수집")
    parser.add_argument("--search-only", action="store_true", help="키워드 검색만")
    args = parser.parse_args()

    result = asyncio.run(collect_x_signals(
        accounts_only=args.accounts_only,
        search_only=args.search_only,
    ))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
