#!/usr/bin/env python3
"""
Crypto Fear & Greed Index 수집 스크립트

소스: Alternative.me (무료, 인증 불필요)
수집: 현재값 + 최근 7일 추이

출력: JSON (stdout)
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import requests

FGI_API = "https://api.alternative.me/fng/"


def main():
    max_retries = 3
    r = None
    for attempt in range(max_retries):
        r = requests.get(FGI_API, params={"limit": "7", "format": "json"}, timeout=10)
        if r.status_code == 429:
            wait = 2 ** attempt
            print(f"[rate_limit] FGI 429, retrying in {wait}s...", file=sys.stderr)
            time.sleep(wait)
            continue
        r.raise_for_status()
        break
    else:
        if r is not None:
            r.raise_for_status()
        raise requests.exceptions.ConnectionError(f"FGI API request failed after {max_retries} retries")

    data = r.json().get("data", [])

    if not data:
        raise RuntimeError("FGI API가 빈 데이터를 반환했습니다")

    history = [
        {
            "date": datetime.fromtimestamp(
                int(d.get("timestamp", 0)), tz=timezone.utc
            ).strftime("%Y-%m-%d"),
            "value": int(d.get("value", 0)),
            "classification": d.get("value_classification", "Unknown"),
        }
        for d in data
    ]

    if not history:
        raise RuntimeError("FGI history 파싱 결과가 비어 있습니다")

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "current": history[0],
        "history_7d": history,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        json.dump({"error": str(e)}, sys.stdout, ensure_ascii=False)
        sys.exit(1)
