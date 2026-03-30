#!/usr/bin/env python3
"""뉴스랑(NewsRang) — RSS 피드 기반 크립토 + 경제 뉴스 수집기 (무료, API 키 불필요)

16개 RSS 피드에서 최신 뉴스를 수집하고, 키워드 기반 감성 점수를 산출한다.
Tavily의 월 999건 한계를 보완하는 무제한 무료 뉴스 소스.

피드 카테고리:
  - crypto_global: CoinDesk, CoinTelegraph, The Block, Decrypt, Bitcoin Magazine
  - crypto_korea: 코인데스크코리아, 토큰포스트, 블록미디어
  - macro_global: 연준(FOMC/연설), Yahoo Finance, CNBC
  - macro_korea: 한국경제, 매일경제

출력: JSON (stdout)

Usage:
  python scripts/collect_rss_news.py
  python scripts/collect_rss_news.py --max-per-feed 10
"""

import json
import re
import sys
import time
from datetime import datetime, timezone, timedelta

try:
    import feedparser
except ImportError:
    print(json.dumps({"error": "feedparser not installed. pip install feedparser", "status": "error", "articles": []}))
    sys.exit(1)

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# ─── RSS 피드 정의 ───────────────────────────────────────────

RSS_FEEDS = {
    # 크립토 글로벌
    "crypto_global": [
        {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "lang": "en"},
        {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss", "lang": "en"},
        {"name": "TheBlock", "url": "https://www.theblock.co/rss.xml", "lang": "en"},
        {"name": "Decrypt", "url": "https://decrypt.co/feed", "lang": "en"},
        {"name": "BitcoinMagazine", "url": "https://bitcoinmagazine.com/feed", "lang": "en"},
    ],
    # 크립토 한국
    "crypto_korea": [
        {"name": "코인데스크코리아", "url": "https://www.coindesk.co.kr/rss", "lang": "ko"},
        {"name": "토큰포스트", "url": "https://www.tokenpost.kr/rss", "lang": "ko"},
        {"name": "블록미디어", "url": "https://www.blockmedia.co.kr/feed", "lang": "ko"},
    ],
    # 경제/매크로 글로벌
    "macro_global": [
        {"name": "Fed_FOMC", "url": "https://www.federalreserve.gov/feeds/press_monetary.xml", "lang": "en"},
        {"name": "Fed_Speeches", "url": "https://www.federalreserve.gov/feeds/speeches.xml", "lang": "en"},
        {"name": "CNBC_Economy", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258", "lang": "en"},
    ],
    # 경제/매크로 한국
    "macro_korea": [
        {"name": "한국경제", "url": "https://www.hankyung.com/feed/all-news", "lang": "ko"},
        {"name": "매일경제", "url": "https://www.mk.co.kr/rss/30000001/", "lang": "ko"},
    ],
}

# ─── 감성 키워드 ──────────────────────────────────────────────

POSITIVE_KEYWORDS = [
    # 영어
    "etf approved", "etf approval", "institutional", "bullish", "rally",
    "adoption", "partnership", "upgrade", "halving", "accumulate",
    "inflow", "break out", "breakout", "all-time high", "ath",
    "buy signal", "recovery", "surge", "soar", "record high",
    "rate cut", "dovish", "stimulus",
    # 한국어
    "승인", "상승", "급등", "반등", "돌파", "강세", "매수",
    "기관투자", "유입", "사상최고", "회복", "금리인하", "완화",
]

NEGATIVE_KEYWORDS = [
    # 영어
    "hack", "hacked", "exploit", "ban", "regulation crackdown",
    "crash", "plunge", "fraud", "scam", "sec lawsuit", "sanctions",
    "war", "bankruptcy", "liquidation", "sell-off", "selloff",
    "bearish", "depeg", "panic", "dump", "collapse",
    "rate hike", "hawkish", "recession", "inflation",
    # 한국어
    "해킹", "폭락", "급락", "하락", "약세", "매도", "사기",
    "규제", "제재", "파산", "청산", "공포", "금리인상",
    "긴축", "경기침체", "인플레이션",
]

# ─── 수집 함수 ────────────────────────────────────────────────


def fetch_feed(feed_info: dict, max_articles: int = 5) -> list[dict]:
    """단일 RSS 피드에서 최신 기사를 수집한다."""
    try:
        parsed = feedparser.parse(feed_info["url"])
        if parsed.bozo and not parsed.entries:
            return []

        articles = []
        for entry in parsed.entries[:max_articles]:
            title = entry.get("title", "").strip()
            if not title:
                continue

            # 발행일 파싱
            published = ""
            for field in ("published", "updated", "created"):
                if hasattr(entry, field) and getattr(entry, field):
                    published = getattr(entry, field)
                    break

            # 요약/본문
            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary[:500]
            elif hasattr(entry, "description"):
                summary = entry.description[:500]

            # HTML 태그 간단 제거
            summary = re.sub(r"<[^>]+>", "", summary).strip()

            link = entry.get("link", "")

            articles.append({
                "title": title,
                "summary": summary[:300],
                "url": link,
                "published": published,
                "source": feed_info["name"],
                "lang": feed_info["lang"],
            })

        return articles

    except Exception as e:
        print(f"[RSS] {feed_info['name']} 실패: {e}", file=sys.stderr)
        return []


def analyze_sentiment(articles: list[dict]) -> dict:
    """키워드 기반 감성 분석 (-100 ~ +100)"""
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    key_signals = []

    for article in articles:
        text = (article.get("title", "") + " " + article.get("summary", "")).lower()

        pos_hits = [kw for kw in POSITIVE_KEYWORDS if kw in text]
        neg_hits = [kw for kw in NEGATIVE_KEYWORDS if kw in text]

        if pos_hits and not neg_hits:
            positive_count += 1
            if len(pos_hits) >= 2:
                key_signals.append(f"+{article['source']}: {article['title'][:60]}")
        elif neg_hits and not pos_hits:
            negative_count += 1
            if len(neg_hits) >= 2:
                key_signals.append(f"-{article['source']}: {article['title'][:60]}")
        else:
            neutral_count += 1

    total = positive_count + negative_count + neutral_count
    if total == 0:
        return {"sentiment_score": 0, "total_articles": 0}

    score = int((positive_count - negative_count) / total * 100)
    score = max(-100, min(100, score))

    return {
        "sentiment_score": score,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "total_articles": total,
        "overall": "bullish" if score > 15 else ("bearish" if score < -15 else "neutral"),
        "key_signals": key_signals[:10],
    }


def collect_all_feeds(max_per_feed: int = 5) -> dict:
    """모든 RSS 피드를 수집하고 감성 분석을 수행한다."""
    t0 = time.time()

    all_articles = []
    by_category = {}
    feed_status = {}
    errors = []

    for category, feeds in RSS_FEEDS.items():
        cat_articles = []
        for feed_info in feeds:
            articles = fetch_feed(feed_info, max_per_feed)
            cat_articles.extend(articles)
            feed_status[feed_info["name"]] = len(articles)
            if not articles:
                errors.append(feed_info["name"])

        by_category[category] = len(cat_articles)
        all_articles.extend(cat_articles)

    # URL 기반 중복 제거
    seen_urls = set()
    unique_articles = []
    for a in all_articles:
        url = a.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(a)
        elif not url:
            unique_articles.append(a)

    # 감성 분석
    crypto_articles = [a for a in unique_articles
                       if any(a.get("source", "").startswith(s)
                              for cat in ("crypto_global", "crypto_korea")
                              for s in [f["name"] for f in RSS_FEEDS[cat]])]
    macro_articles = [a for a in unique_articles if a not in crypto_articles]

    crypto_sentiment = analyze_sentiment(crypto_articles)
    macro_sentiment = analyze_sentiment(macro_articles)

    # 종합 감성 (크립토 70% + 매크로 30%)
    combined_score = int(
        crypto_sentiment["sentiment_score"] * 0.7
        + macro_sentiment["sentiment_score"] * 0.3
    )

    elapsed = round(time.time() - t0, 1)

    return {
        "timestamp": datetime.now(timezone(timedelta(hours=9))).isoformat(),
        "collection_time_sec": elapsed,
        "total_articles": len(unique_articles),
        "by_category": by_category,
        "feed_status": feed_status,
        "errors": errors,
        "sentiment": {
            "combined_score": combined_score,
            "crypto": crypto_sentiment,
            "macro": macro_sentiment,
        },
        "articles": unique_articles[:50],  # 최대 50개
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="RSS 크립토+경제 뉴스 수집")
    parser.add_argument("--max-per-feed", type=int, default=5)
    args = parser.parse_args()

    result = collect_all_feeds(max_per_feed=args.max_per_feed)
    print(json.dumps(result, ensure_ascii=False, indent=2))
