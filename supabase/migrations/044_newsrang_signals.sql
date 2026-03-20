-- 044: 뉴스랑(NewsRang) 시그널 저장 테이블
-- RSS 뉴스, X 트위터, 소셜 감성, 종합 브리핑 데이터를 기록한다.

-- 뉴스랑 수집 결과 (매 실행마다 1행)
CREATE TABLE IF NOT EXISTS newsrang_signals (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    machine_name    TEXT DEFAULT 'unknown',

    -- 수집 메타
    collection_time_sec NUMERIC(6,1),
    total_articles      INT DEFAULT 0,

    -- RSS 뉴스 감성
    rss_crypto_score    INT,          -- -100 ~ +100
    rss_macro_score     INT,          -- -100 ~ +100
    rss_combined_score  INT,          -- 가중 평균
    rss_article_count   INT DEFAULT 0,
    rss_feed_errors     TEXT[],

    -- X(트위터) 시그널
    x_score             INT,          -- -100 ~ +100
    x_signal            TEXT,         -- strong_bullish/bullish/neutral/bearish/strong_bearish/no_data
    x_tweet_count       INT DEFAULT 0,
    x_bullish_count     INT DEFAULT 0,
    x_bearish_count     INT DEFAULT 0,
    x_whale_summary     JSONB,        -- {total_alerts, sell_pressure, buy_pressure, net_direction}

    -- 소셜 감성
    social_score        INT,          -- -100 ~ +100
    social_signal       TEXT,
    social_sources      INT DEFAULT 0,
    social_components   JSONB,        -- {cryptocompare_news, coingecko_social, social_stats}

    -- Data Fusion 종합
    fusion_total_score  INT,
    fusion_rss_adj      INT,
    fusion_x_adj        INT,
    fusion_social_adj   INT,

    -- 원본 데이터 (디버깅/분석용)
    rss_top_signals     JSONB,        -- 주요 뉴스 헤드라인 (최대 10개)
    x_top_tweets        JSONB,        -- 주요 트윗 (최대 10개)
    social_raw          JSONB         -- CoinGecko/CryptoCompare 원본
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_newsrang_created ON newsrang_signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_newsrang_machine ON newsrang_signals(machine_name);

-- RLS
ALTER TABLE newsrang_signals ENABLE ROW LEVEL SECURITY;

-- owner/coworker 전체 접근
CREATE POLICY newsrang_signals_owner ON newsrang_signals
    FOR ALL USING (true) WITH CHECK (true);

COMMENT ON TABLE newsrang_signals IS '뉴스랑(NewsRang) 외부 시그널 수집 결과 — RSS/X/소셜 감성 종합';
