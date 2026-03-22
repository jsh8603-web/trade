#!/usr/bin/env python3
"""뉴스랑(NewsRang) — 소셜 미디어 감성 수집기 (무료 API 통합)

3개 무료 소스에서 크립토 소셜 감성 데이터를 수집한다:
  1. CryptoCompare — 150개+ 뉴스 소스 집계 (무료 키 필요, 무료 티어)
  2. CoinGecko — 코인별 소셜 지표 (무료, 키 불필요)
  3. Santiment — 소셜 볼륨/감성 (무료 티어, 제한적)

출력: JSON (stdout)

필요 환경변수 (선택):
  CRYPTOCOMPARE_API_KEY: CryptoCompare 무료 API 키 (https://min-api.cryptocompare.com)

Usage:
  python scripts/collect_social_sentiment.py
  python scripts/collect_social_sentiment.py --coins BTC,ETH,XRP
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

CRYPTOCOMPARE_KEY = os.getenv("CRYPTOCOMPARE_API_KEY", "")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "CoinTrading/1.0"})


# ─── 1. CryptoCompare 뉴스 감성 ───────────────────────────────


def fetch_cryptocompare_news(max_articles: int = 20) -> dict:
    """CryptoCompare에서 최신 크립토 뉴스를 수집한다.
    무료 티어: 50-200 요청/시간, 150+ 뉴스 소스 집계.
    """
    if not CRYPTOCOMPARE_KEY:
        return {"status": "disabled", "reason": "CRYPTOCOMPARE_API_KEY not set"}

    try:
        resp = SESSION.get(
            "https://min-api.cryptocompare.com/data/v2/news/",
            params={"lang": "EN", "api_key": CRYPTOCOMPARE_KEY},
            timeout=15,
        )
        if resp.status_code != 200:
            return {"status": "error", "code": resp.status_code}

        data = resp.json()
        if data.get("Response") == "Error":
            return {"status": "error", "message": data.get("Message", "CryptoCompare API error")}

        articles = data.get("Data", [])[:max_articles]

        # 감성 집계
        bullish = 0
        bearish = 0
        neutral = 0
        categorized = []

        for a in articles:
            title = a.get("title", "")
            body = a.get("body", "")[:200]
            source = a.get("source_info", {}).get("name", a.get("source", ""))
            categories = a.get("categories", "")
            published = a.get("published_on", 0)

            # CryptoCompare 자체 감성 태그
            sentiment_tag = ""
            if categories and "bullish" in categories.lower():
                bullish += 1
                sentiment_tag = "bullish"
            elif categories and "bearish" in categories.lower():
                bearish += 1
                sentiment_tag = "bearish"
            else:
                neutral += 1
                sentiment_tag = "neutral"

            categorized.append({
                "title": title[:120],
                "source": source,
                "categories": categories,
                "sentiment": sentiment_tag,
                "published": datetime.fromtimestamp(published, tz=timezone.utc).isoformat() if published else "",
            })

        total = bullish + bearish + neutral
        score = int((bullish - bearish) / total * 100) if total > 0 else 0

        return {
            "status": "ok",
            "total_articles": total,
            "sentiment_score": max(-100, min(100, score)),
            "bullish": bullish,
            "bearish": bearish,
            "neutral": neutral,
            "articles": categorized[:10],
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─── 2. CoinGecko 소셜 지표 ───────────────────────────────────


def fetch_coingecko_social(coins: list[str] = None) -> dict:
    """CoinGecko에서 코인별 소셜/커뮤니티 데이터를 수집한다.
    무료: API 키 불필요, 5-15 요청/분.
    """
    if coins is None:
        coins = ["bitcoin", "ethereum"]

    results = {}

    for coin_id in coins:
        try:
            resp = SESSION.get(
                f"https://api.coingecko.com/api/v3/coins/{coin_id}",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "market_data": "true",
                    "community_data": "true",
                    "developer_data": "false",
                    "sparkline": "false",
                },
                timeout=15,
            )

            if resp.status_code == 429:
                # Retry up to 2 additional attempts with exponential backoff
                retry_success = False
                for _retry in range(2):
                    time.sleep(5 * (3 ** _retry))  # 5s, 15s
                    resp = SESSION.get(
                        f"https://api.coingecko.com/api/v3/coins/{coin_id}",
                        params={
                            "localization": "false",
                            "tickers": "false",
                            "market_data": "true",
                            "community_data": "true",
                            "developer_data": "false",
                            "sparkline": "false",
                        },
                        timeout=15,
                    )
                    if resp.status_code != 429:
                        retry_success = True
                        break
                if not retry_success:
                    results[coin_id] = {"status": "error", "code": 429, "message": "rate limited"}
                    continue
            if resp.status_code != 200:
                results[coin_id] = {"status": "error", "code": resp.status_code}
                continue

            data = resp.json()

            # 커뮤니티 데이터
            community = data.get("community_data") or {}
            market = data.get("market_data") or {}
            sentiment = data.get("sentiment_votes_up_percentage") or 0
            sentiment_down = data.get("sentiment_votes_down_percentage") or 0

            # 가격 변동
            price_change_24h = market.get("price_change_percentage_24h") or 0
            price_change_7d = market.get("price_change_percentage_7d") or 0

            results[coin_id] = {
                "status": "ok",
                "sentiment_up_pct": sentiment or 0,
                "sentiment_down_pct": sentiment_down or 0,
                "twitter_followers": community.get("twitter_followers") or 0,
                "reddit_subscribers": community.get("reddit_subscribers") or 0,
                "reddit_active_48h": community.get("reddit_accounts_active_48h") or 0,
                "telegram_members": community.get("telegram_channel_user_count") or 0,
                "price_change_24h": round(price_change_24h or 0, 2),
                "price_change_7d": round(price_change_7d or 0, 2),
            }

            time.sleep(1.5)  # 레이트리밋 방지

        except Exception as e:
            results[coin_id] = {"status": "error", "message": str(e)}

    # BTC 감성 점수 산출
    btc = results.get("bitcoin", {})
    btc_sentiment = 0
    if btc.get("status") == "ok":
        up = btc.get("sentiment_up_pct", 50)
        down = btc.get("sentiment_down_pct", 50)
        btc_sentiment = int(up - down)  # -100 ~ +100 범위

    return {
        "status": "ok",
        "coins": results,
        "btc_sentiment_score": btc_sentiment,
    }


# ─── 3. CryptoCompare 소셜 통계 ──────────────────────────────


def fetch_social_stats(coin: str = "BTC") -> dict:
    """CryptoCompare 소셜 미디어 통계 (Twitter, Reddit 팔로워 추이)"""
    if not CRYPTOCOMPARE_KEY:
        return {"status": "disabled"}

    try:
        resp = SESSION.get(
            "https://min-api.cryptocompare.com/data/social/coin/latest",
            params={"coinId": 1182 if coin == "BTC" else 7605, "api_key": CRYPTOCOMPARE_KEY},
            timeout=15,
        )
        if resp.status_code != 200:
            return {"status": "error", "code": resp.status_code}

        data = resp.json().get("Data", {})

        twitter = data.get("Twitter", {})
        reddit = data.get("Reddit", {})

        return {
            "status": "ok",
            "coin": coin,
            "twitter": {
                "followers": twitter.get("followers", 0),
                "statuses": twitter.get("statuses", 0),
                "favourites": twitter.get("favourites", 0),
            },
            "reddit": {
                "subscribers": reddit.get("subscribers", 0),
                "active_users": reddit.get("active_users", 0),
                "posts_per_day": reddit.get("posts_per_day", 0),
                "comments_per_day": reddit.get("comments_per_day", 0),
            },
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─── 종합 점수 산출 ──────────────────────────────────────────


def calculate_social_signal(cc_news: dict, cg_social: dict, cc_stats: dict) -> dict:
    """3개 소스를 종합하여 소셜 감성 시그널을 산출한다."""
    scores = []
    components = {}

    # CryptoCompare 뉴스 감성 (가중치 40%)
    if cc_news.get("status") == "ok":
        s = cc_news.get("sentiment_score", 0)
        scores.append(("cc_news", s, 0.4))
        components["cryptocompare_news"] = {
            "score": s,
            "weight": 0.4,
            "articles": cc_news.get("total_articles", 0),
        }

    # CoinGecko 커뮤니티 감성 (가중치 35%)
    if cg_social.get("status") == "ok":
        s = cg_social.get("btc_sentiment_score", 0)
        scores.append(("cg_social", s, 0.35))
        components["coingecko_social"] = {
            "score": s,
            "weight": 0.35,
            "coins_checked": len(cg_social.get("coins", {})),
        }

    # CryptoCompare 소셜 통계 (가중치 25%)
    if cc_stats.get("status") == "ok":
        reddit = cc_stats.get("reddit", {})
        # Reddit 활동 기반 감성 (활동 많으면 관심 높음)
        active = reddit.get("active_users", 0)
        posts = reddit.get("posts_per_day", 0)
        # 평균 이상이면 양수, 이하면 음수 (단순 임계값)
        reddit_score = 10 if active > 5000 else (-10 if active < 1000 else 0)
        scores.append(("cc_stats", reddit_score, 0.25))
        components["social_stats"] = {
            "score": reddit_score,
            "weight": 0.25,
            "reddit_active": active,
            "reddit_posts_day": posts,
        }

    # 가중 평균 점수
    if scores:
        total_weight = sum(w for _, _, w in scores)
        weighted = sum(s * w for _, s, w in scores)
        final_score = int(weighted / total_weight) if total_weight > 0 else 0
    else:
        final_score = 0

    final_score = max(-100, min(100, final_score))

    # 시그널 판정
    if final_score >= 25:
        signal = "strong_bullish"
    elif final_score >= 10:
        signal = "bullish"
    elif final_score <= -25:
        signal = "strong_bearish"
    elif final_score <= -10:
        signal = "bearish"
    else:
        signal = "neutral"

    return {
        "total_score": final_score,
        "signal": signal,
        "sources_available": len(scores),
        "components": components,
    }


# ─── 메인 ──────────────────────────────────────────────────────


def collect_all(coins: list[str] = None) -> dict:
    """모든 소셜 감성 데이터를 수집한다."""
    t0 = time.time()

    if coins is None:
        coins = ["bitcoin", "ethereum"]

    # 3개 소스 수집
    cc_news = fetch_cryptocompare_news()
    cg_social = fetch_coingecko_social(coins)
    cc_stats = fetch_social_stats("BTC")

    # 종합 시그널
    signal = calculate_social_signal(cc_news, cg_social, cc_stats)

    elapsed = round(time.time() - t0, 1)

    return {
        "timestamp": datetime.now(timezone(timedelta(hours=9))).isoformat(),
        "collection_time_sec": elapsed,
        "signal": signal,
        "sources": {
            "cryptocompare_news": cc_news,
            "coingecko_social": cg_social,
            "social_stats": cc_stats,
        },
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="소셜 미디어 감성 수집")
    parser.add_argument("--coins", type=str, default="bitcoin,ethereum",
                        help="CoinGecko 코인 ID (쉼표 구분)")
    args = parser.parse_args()

    coin_list = [c.strip() for c in args.coins.split(",")]
    result = collect_all(coins=coin_list)
    print(json.dumps(result, ensure_ascii=False, indent=2))
