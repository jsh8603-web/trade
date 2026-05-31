"""PyTrends 'bitcoin' weekly attention z-score fetch (P0-C, 2026-05-31).

theory-notes §6.5 H11: Liu&Tsyvinski 2021 RFS attention predictor.
★PyTrends 정규화 (100 max in window) — 5y 단일 query 사용 의무 (window 비교 일관성).

⚠️ rate-limit 심함 (429). retry 3 + sleep 2s.

데이터 보존: raw/data/pytrends-bitcoin-weekly.csv
"""
from __future__ import annotations
import sys
import time
from pathlib import Path
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from pytrends.request import TrendReq
except ImportError:
    print("[FATAL] pytrends 미설치 — pip install pytrends 의무", flush=True)
    sys.exit(1)

OUT = Path(__file__).resolve().parent.parent / "raw" / "data" / "pytrends-bitcoin-weekly.csv"


def fetch_5y(timeframe: str):
    """5y window single query (normalize 일관성). urllib3>=2 호환 retries=0."""
    for retry in range(3):
        try:
            # urllib3>=2 호환: retries=0 강제 (method_whitelist 회피)
            pt = TrendReq(hl="en-US", tz=0)
            pt.build_payload(kw_list=["bitcoin"], timeframe=timeframe, geo="", gprop="")
            df = pt.interest_over_time()
            return df
        except Exception as e:
            print(f"  attempt {retry+1} fail: {e}", flush=True)
            time.sleep(3 * (retry + 1))
    return None


def main():
    # 2018-01-01 ~ 2026-05-31 = 8.5y → 3 segments (5y, 3.5y) — overlapping rescale
    # 또는 PyTrends 전체 'today 5-y' or 'all'
    print("[fetch] PyTrends 'bitcoin' all-time weekly", flush=True)
    df = fetch_5y("all")
    if df is None or df.empty:
        print("[FAIL] PyTrends fetch 실패 — rate-limit 또는 403", flush=True)
        # 폴백: today 5-y
        print("[fallback] today 5-y", flush=True)
        df = fetch_5y("today 5-y")
        if df is None or df.empty:
            print("[FATAL] PyTrends 본 round 실패. cycle 3 재시도 권고.", flush=True)
            return

    if "isPartial" in df.columns:
        df = df[df["isPartial"] == False].copy()
    df = df.reset_index()
    if "date" in df.columns:
        df.rename(columns={"date": "date_utc"}, inplace=True)
    df["date_utc"] = pd.to_datetime(df["date_utc"]).dt.strftime("%Y-%m-%d")
    df = df.rename(columns={"bitcoin": "trends_bitcoin"})
    keep = ["date_utc", "trends_bitcoin"]
    df[keep].to_csv(OUT, index=False)
    print(f"[OK] saved {len(df)} rows -> {OUT.name}", flush=True)
    print(f"  range: {df['date_utc'].iloc[0]} ~ {df['date_utc'].iloc[-1]}", flush=True)
    print(f"  trends range: [{df['trends_bitcoin'].min()}, {df['trends_bitcoin'].max()}]", flush=True)


if __name__ == "__main__":
    main()
