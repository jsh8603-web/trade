"""CoinMetrics community API v2 — 신규 5 metric 직접 fetch (P0-A, 2026-05-31).

기존 collect_coinmetrics.py (CapMVRV/CapReal/CapMrkt/Price/Ref) 보존 + 신규 5 metric 별도 CSV.

신규 metric (anonymous tier 시도):
- AdrActCnt   : 활성주소 (H7 network value, Pagnotta&Buraschi 2018)
- TxTfrValAdjUSD : adjusted transfer USD (H8 utility, Catalini&Gans 2020)
- HashRate    : 일별 평균 hashrate (H5 halving conditioning 보강)
- FlowMinerNtv : 채굴자 net flow (BTC native) — 표준명 시도 (실패 시 alternative)
- SOPR        : Spent Output Profit Ratio (anonymous tier 가능성 모름, 실패 시 보고)

⛔ 합성 시뮬 X. 실측 fetch only. fetch 실패 metric 은 명시 보고.
"""
from __future__ import annotations
import csv
import time
from pathlib import Path
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import requests

OUT = Path(__file__).resolve().parent.parent / "raw" / "data" / "coinmetrics-btc-daily-v2.csv"
LOG = Path(__file__).resolve().parent.parent / "raw" / "data" / "coinmetrics-v2-fetch-log.txt"

S = requests.Session()
S.headers.update({"Accept": "application/json", "User-Agent": "Mozilla/5.0 (study-Inv-crypto-2.5-cycle2)"})

URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"

# 신규 4 metric (anonymous tier probe 검증 후 확정, 2026-05-31):
# - AdrActCnt    : 활성주소 (H7 network value, Pagnotta&Buraschi 2018)
# - TxCnt        : transaction count (H8 utility, TxTfrValAdjUSD=403 대체)
# - HashRate     : 일별 평균 hashrate (H5 conditioning 보강)
# - BlkCnt       : block count (mining health 보조)
# ★probe 결과 403/400: TxTfrValAdjUSD / TxTfrValUSD / SOPR / RevUSD / RevNtv / FlowMinerNtv / MinerRev / RevHashRateNtv
#   = community anonymous tier 권한 없음 또는 표준명 비존재. cycle 3 paid tier 또는 main 별도 요청.
NEW_METRICS = [
    "AdrActCnt",
    "TxCnt",
    "HashRate",
    "BlkCnt",
]


def fetch_metric(metric: str, log_lines: list):
    rows = {}
    page_token = None
    page_count = 0
    last_err = None
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
                    msg = f"  {metric} HTTP {r.status_code} body={r.text[:200]}"
                    print(msg, flush=True)
                    log_lines.append(msg)
                    return rows
                break
            except Exception as e:
                last_err = e
                msg = f"  {metric} attempt {retry+1} fail: {e}"
                print(msg, flush=True)
                log_lines.append(msg)
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
            msg = (f"  {metric} page {page_count}: {len(data)} rows, total {len(rows)}, "
                   f"earliest {data[0]['time'][:10]}, next={'yes' if page_token else 'no'}")
            print(msg, flush=True)
            log_lines.append(msg)
        if not page_token:
            break
        time.sleep(0.3)
    return rows


def main():
    log_lines = []
    log_lines.append(f"[start] {time.strftime('%Y-%m-%d %H:%M:%S')} new 5 metric direct fetch")
    all_data = {}
    success = []
    fail = []
    for m in NEW_METRICS:
        print(f"[fetch] {m}", flush=True)
        log_lines.append(f"[fetch] {m}")
        rows = fetch_metric(m, log_lines)
        if not rows:
            print(f"  [WARN] {m} 0 rows -> alternative 시도 권고", flush=True)
            log_lines.append(f"  [WARN] {m} 0 rows -> alternative 시도 권고")
            fail.append(m)
            continue
        for t, v in rows.items():
            all_data.setdefault(t, {})[m] = v
        success.append((m, len(rows)))
        time.sleep(0.5)

    # write CSV (성공한 metric only)
    times = sorted(all_data.keys())
    if not times:
        msg = "[FATAL] no data collected for any new metric"
        print(msg, flush=True)
        log_lines.append(msg)
        with LOG.open("w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
        return
    success_metrics = [m for m, _ in success]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time"] + success_metrics)
        for t in times:
            row = all_data[t]
            w.writerow([t] + [row.get(m, "") for m in success_metrics])
    msg = f"[OK] saved {len(times)} rows -> {OUT.name}"
    print(msg, flush=True)
    log_lines.append(msg)
    msg = f"  range: {times[0]} ~ {times[-1]}"
    print(msg, flush=True)
    log_lines.append(msg)
    msg = f"  success: {success}"
    print(msg, flush=True)
    log_lines.append(msg)
    msg = f"  fail: {fail}"
    print(msg, flush=True)
    log_lines.append(msg)

    with LOG.open("w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))


if __name__ == "__main__":
    main()
