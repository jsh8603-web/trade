"""CoinMetrics MVRV 별도 수집기 (anonymous tier 우회).

5 metrics 묶음 호출이 403 -> metric 별로 분리 호출 후 merge.
"""
from __future__ import annotations
import csv
import json
import time
import datetime as dt
from pathlib import Path
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import requests

OUT = Path(__file__).resolve().parent.parent / "raw" / "data" / "coinmetrics-btc-daily.csv"

S = requests.Session()
S.headers.update({"Accept": "application/json", "User-Agent": "Mozilla/5.0 (study-Inv-crypto-2.3)"})

METRICS = ["CapMVRVCur", "CapRealUSD", "CapMrktCurUSD", "PriceUSD", "ReferenceRateUSD"]
URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"


def fetch_metric(metric: str):
    rows = {}
    page_token = None
    page_count = 0
    while page_count < 50:
        params = {"assets": "btc", "metrics": metric, "frequency": "1d", "page_size": 1000}
        if page_token:
            params["next_page_token"] = page_token
        for retry in range(3):
            try:
                r = S.get(URL, params=params, timeout=60)
                if r.status_code == 429:
                    time.sleep(2 ** retry)
                    continue
                if r.status_code != 200:
                    print(f"  {metric} HTTP {r.status_code}", flush=True)
                    return rows
                break
            except Exception as e:
                print(f"  {metric} attempt {retry+1} fail: {e}", flush=True)
                time.sleep(1)
        else:
            return rows
        j = r.json()
        data = j.get("data", [])
        for d in data:
            rows[d["time"]] = d.get(metric)
        page_token = j.get("next_page_token")
        page_count += 1
        if data:
            print(f"  {metric} page {page_count}: {len(data)} rows, total {len(rows)}, earliest {data[0]['time'][:10]}, next={'yes' if page_token else 'no'}", flush=True)
        if not page_token:
            break
        time.sleep(0.3)
    return rows


def main():
    all_data = {}  # time -> {metric: value}
    for m in METRICS:
        print(f"[fetch] {m}", flush=True)
        rows = fetch_metric(m)
        if not rows:
            print(f"  [WARN] {m} 0 rows", flush=True)
            continue
        for t, v in rows.items():
            all_data.setdefault(t, {})[m] = v
        time.sleep(0.5)
    # write CSV
    times = sorted(all_data.keys())
    if not times:
        print("[FATAL] no data collected for any metric", flush=True)
        return
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time"] + METRICS)
        for t in times:
            row = all_data[t]
            w.writerow([t] + [row.get(m, "") for m in METRICS])
    print(f"[OK] saved {len(times)} rows -> {OUT.name}", flush=True)
    print(f"  range: {times[0]} ~ {times[-1]}", flush=True)


if __name__ == "__main__":
    main()
