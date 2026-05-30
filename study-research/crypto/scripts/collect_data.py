"""crypto 2-3 실데이터 수집기 -- 6 무료 API (no synthetic, no simulation).

Run: python collect_data.py
Output: ../raw/data/{source}-{kind}.csv

Sources (모두 무료·공개):
1. CoinMetrics Community v4 -- BTC MVRV (CapMVRVCur), MVRVZ (CapMVRVZ가능여부), realized cap, price (~2010+)
2. alternative.me Fear&Greed Index (FGI) -- 2018-02-01~
3. Binance USDT-M futures public -- BTCUSDT funding history (2019-09~) + OI history (limit window)
4. DefiLlama public -- stablecoin total supply daily (2018~)
5. CoinGecko public /global -- BTC dominance (daily snapshots, history제한)
6. Farside Investors HTML -- BTC spot ETF daily net flow (post-2024)

PIT 원칙:
- knowable_from (publish_time) >= as_of 미사용 (lookahead 차단)
- 모든 timestamp UTC, ISO 8601
- 결측·정정·휴일은 raw 유지 (forward fill X)

[BAN] 합성 데이터 절대 금지. API 실패 시 그 source 만 SKIP, 기록 명시.
"""
from __future__ import annotations
import csv
import json
import time
import datetime as dt
from pathlib import Path
import sys
# Windows cp949 console 우회 -- utf-8 강제
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass
import requests

OUTDIR = Path(__file__).resolve().parent.parent / "raw" / "data"
OUTDIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json", "User-Agent": "Inv-crypto-study/2.3"})

LOG = []
def log(msg):
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG.append(line)


def get(url, params=None, max_retry=3, timeout=30):
    for i in range(max_retry):
        try:
            r = SESSION.get(url, params=params, timeout=timeout)
            if r.status_code == 429:
                wait = 2 ** i
                log(f"  429 rate limit, wait {wait}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except Exception as e:
            log(f"  attempt {i+1}/{max_retry} fail: {e}")
            time.sleep(1 + i)
    return None


# ===========================================================================
# 1. CoinMetrics Community -- BTC MVRV + realized cap + price (~2010+)
# ===========================================================================
def collect_coinmetrics():
    log("[1/6] CoinMetrics Community -- BTC metrics")
    url = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
    # CapMVRVCur 는 일별 MVRV ratio (Market Cap / Realized Cap)
    metrics = "CapMVRVCur,CapRealUSD,CapMrktCurUSD,PriceUSD,ReferenceRateUSD"
    out = OUTDIR / "coinmetrics-btc-daily.csv"
    page_token = None
    rows = []
    page_count = 0
    max_pages = 100  # 안전 cap
    while page_count < max_pages:
        params = {
            "assets": "btc",
            "metrics": metrics,
            "frequency": "1d",
            "page_size": 1000,
        }
        if page_token:
            params["next_page_token"] = page_token
        r = get(url, params=params, timeout=60)
        if not r:
            log(f"  ABORT page {page_count}")
            return None
        j = r.json()
        data = j.get("data", [])
        rows.extend(data)
        page_token = j.get("next_page_token")
        page_count += 1
        log(f"  page {page_count}: {len(data)} rows, total {len(rows)}, next={'yes' if page_token else 'no'}")
        if not page_token:
            break
        time.sleep(0.3)
    if not rows:
        log("  no data")
        return None
    # write CSV
    keys = list(rows[0].keys())
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    log(f"  [OK] saved {len(rows)} rows -> {out.name}")
    return out


# ===========================================================================
# 2. alternative.me Fear&Greed Index -- daily 2018-02~
# ===========================================================================
def collect_fgi():
    log("[2/6] alternative.me Fear&Greed Index")
    url = "https://api.alternative.me/fng/"
    # limit=0 -> all history
    r = get(url, params={"limit": 0, "format": "json"}, timeout=30)
    if not r:
        return None
    j = r.json()
    data = j.get("data", [])
    if not data:
        return None
    out = OUTDIR / "fgi-daily.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp_unix", "date_utc", "value", "classification"])
        for d in data:
            ts = int(d["timestamp"])
            date = dt.datetime.fromtimestamp(ts, dt.timezone.utc).date().isoformat()
            w.writerow([ts, date, int(d["value"]), d["value_classification"]])
    log(f"  [OK] saved {len(data)} rows -> {out.name}")
    return out


# ===========================================================================
# 3. Binance USDT-M futures -- BTCUSDT funding rate (2019-09~) + OI history
# ===========================================================================
def collect_binance_funding():
    log("[3a/6] Binance BTCUSDT funding history")
    url = "https://fapi.binance.com/fapi/v1/fundingRate"
    # startTime 명시 walk-forward (endTime=None 일 때 가장 최근 200 만 반환)
    rows = []
    start_time = int(dt.datetime(2019, 8, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
    now_ms = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)
    call_count = 0
    max_calls = 100
    while call_count < max_calls and start_time < now_ms:
        params = {"symbol": "BTCUSDT", "limit": 1000, "startTime": start_time}
        r = get(url, params=params, timeout=30)
        if not r:
            log(f"  ABORT call {call_count}")
            break
        data = r.json()
        if not data:
            break
        rows.extend(data)
        last_time = max(d["fundingTime"] for d in data)
        start_time = last_time + 1
        call_count += 1
        log(f"  call {call_count}: {len(data)} rows, total {len(rows)}, latest {dt.datetime.fromtimestamp(last_time/1000, dt.timezone.utc).date()}")
        if len(data) < 1000:
            break
        time.sleep(0.2)
    if not rows:
        return None
    # dedup by fundingTime
    seen = set()
    uniq = []
    for r in rows:
        t = r["fundingTime"]
        if t in seen:
            continue
        seen.add(t)
        uniq.append(r)
    out = OUTDIR / "binance-funding-btcusdt.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["funding_time_ms", "datetime_utc", "funding_rate", "mark_price"])
        for d in sorted(uniq, key=lambda x: x["fundingTime"]):
            ts = int(d["fundingTime"])
            iso = dt.datetime.fromtimestamp(ts/1000, dt.timezone.utc).isoformat()
            w.writerow([ts, iso, d["fundingRate"], d.get("markPrice", "")])
    log(f"  [OK] saved {len(uniq)} unique funding rows -> {out.name}")
    return out


def collect_binance_oi_klines():
    """OI history daily 30d max public window. 가능한 만큼 fetch."""
    log("[3b/6] Binance BTCUSDT OI history (recent 30d only public)")
    url = "https://fapi.binance.com/futures/data/openInterestHist"
    params = {"symbol": "BTCUSDT", "period": "1d", "limit": 500}
    r = get(url, params=params, timeout=30)
    if not r:
        return None
    data = r.json()
    out = OUTDIR / "binance-oi-btcusdt.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp_ms", "datetime_utc", "sum_open_interest", "sum_open_interest_value"])
        for d in data:
            ts = int(d["timestamp"])
            iso = dt.datetime.fromtimestamp(ts/1000, dt.timezone.utc).isoformat()
            w.writerow([ts, iso, d["sumOpenInterest"], d["sumOpenInterestValue"]])
    log(f"  [OK] saved {len(data)} OI rows -> {out.name}")
    return out


def collect_binance_klines():
    """BTCUSDT spot klines daily ~2017-08~ ."""
    log("[3c/6] Binance BTCUSDT spot klines (daily)")
    url = "https://api.binance.com/api/v3/klines"
    rows = []
    end_time = None
    call_count = 0
    max_calls = 20  # 20 * 1000 = 20000 days = 충분
    while call_count < max_calls:
        params = {"symbol": "BTCUSDT", "interval": "1d", "limit": 1000}
        if end_time:
            params["endTime"] = end_time
        r = get(url, params=params, timeout=30)
        if not r:
            break
        data = r.json()
        if not data:
            break
        rows.extend(data)
        first_time = data[0][0]
        end_time = first_time - 1
        call_count += 1
        log(f"  call {call_count}: {len(data)} candles, earliest {dt.datetime.fromtimestamp(first_time/1000, dt.timezone.utc).date()}")
        if len(data) < 1000:
            break
        time.sleep(0.2)
    # dedup
    seen = set(); uniq = []
    for r in rows:
        if r[0] in seen:
            continue
        seen.add(r[0]); uniq.append(r)
    out = OUTDIR / "binance-klines-btcusdt-1d.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["open_time_ms", "date_utc", "open", "high", "low", "close", "volume", "close_time_ms", "quote_volume", "trades", "taker_buy_base", "taker_buy_quote"])
        for d in sorted(uniq, key=lambda x: x[0]):
            ts = int(d[0])
            date = dt.datetime.fromtimestamp(ts/1000, dt.timezone.utc).date().isoformat()
            w.writerow([ts, date] + d[1:12])
    log(f"  [OK] saved {len(uniq)} klines -> {out.name}")
    return out


# ===========================================================================
# 4. DefiLlama -- stablecoin total supply daily
# ===========================================================================
def collect_defillama_stablecoins():
    log("[4/6] DefiLlama stablecoin charts")
    url = "https://stablecoins.llama.fi/stablecoincharts/all"
    r = get(url, params={"stablecoin": ""}, timeout=60)
    if not r:
        return None
    data = r.json()
    if not data:
        return None
    out = OUTDIR / "defillama-stablecoin-total.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # keys: date, totalCirculating.peggedUSD, ...
        w.writerow(["timestamp_unix", "date_utc", "total_circulating_peggedUSD", "total_minted_peggedUSD", "total_unreleased_peggedUSD"])
        for d in data:
            ts = int(d["date"])
            date = dt.datetime.fromtimestamp(ts, dt.timezone.utc).date().isoformat()
            tc = (d.get("totalCirculating") or {}).get("peggedUSD", "")
            tm = (d.get("totalMintedUSD") or {}).get("peggedUSD", "") if isinstance(d.get("totalMintedUSD"), dict) else ""
            tu = (d.get("totalUnreleased") or {}).get("peggedUSD", "") if isinstance(d.get("totalUnreleased"), dict) else ""
            w.writerow([ts, date, tc, tm, tu])
    log(f"  [OK] saved {len(data)} stablecoin rows -> {out.name}")
    return out


# ===========================================================================
# 5. CoinGecko /global -- current BTC dominance (no free history)
# ===========================================================================
def collect_coingecko_global():
    log("[5/6] CoinGecko /global (current dominance snapshot)")
    url = "https://api.coingecko.com/api/v3/global"
    r = get(url, timeout=30)
    if not r:
        return None
    data = r.json().get("data", {})
    out = OUTDIR / "coingecko-global-snapshot.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump({
            "fetched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "data": data,
        }, f, indent=2)
    log(f"  [OK] saved global snapshot -> {out.name}")
    log(f"     btc dominance: {data.get('market_cap_percentage', {}).get('btc', 'n/a')}")
    return out


# ===========================================================================
# 6. Farside Investors ETF flow (HTML scrape, post-2024-01)
# ===========================================================================
def collect_farside_etf():
    log("[6/6] Farside Investors -- BTC spot ETF daily flow (HTML)")
    url = "https://farside.co.uk/bitcoin-etf-flow-all-data/"
    r = get(url, timeout=60)
    if not r:
        log("  Farside fetch fail (anti-bot 가능)")
        return None
    html = r.text
    out = OUTDIR / "farside-etf-raw.html"
    with out.open("w", encoding="utf-8") as f:
        f.write(html)
    log(f"  [OK] saved raw HTML ({len(html)} chars) -> {out.name} (parse 별도)")
    return out


# ===========================================================================
# Main
# ===========================================================================
def main():
    results = {}
    for name, fn in [
        ("coinmetrics", collect_coinmetrics),
        ("fgi", collect_fgi),
        ("defillama", collect_defillama_stablecoins),
        ("coingecko", collect_coingecko_global),
        ("binance_klines", collect_binance_klines),
        ("binance_funding", collect_binance_funding),
        ("binance_oi", collect_binance_oi_klines),
        ("farside", collect_farside_etf),
    ]:
        try:
            results[name] = str(fn() or "FAIL")
        except Exception as e:
            log(f"  EXCEPTION in {name}: {e}")
            results[name] = f"EXCEPTION: {e}"
    # write log
    log_path = OUTDIR / "collect_log.txt"
    with log_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(LOG))
        f.write("\n\n=== Results ===\n")
        for k, v in results.items():
            f.write(f"{k}: {v}\n")
    log("\n=== DONE ===")
    for k, v in results.items():
        log(f"  {k}: {v}")


if __name__ == "__main__":
    main()
