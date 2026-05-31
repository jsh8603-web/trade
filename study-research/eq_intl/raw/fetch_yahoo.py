"""eq_intl 스터디 ② 실데이터 fetch. Yahoo Finance chart API 무료.

산출: study-research/eq_intl/raw/yahoo_cache/{alias}.csv (date, price[=adj close, TR])
"""
import urllib.request, json, csv, os, time, sys
from datetime import datetime, timezone

OUT = os.path.join(os.path.dirname(__file__), "yahoo_cache")
os.makedirs(OUT, exist_ok=True)

UNIVERSE = {
    "SPY": "us_spy",
    "EFA": "dm_exus",
    "VEA": "dm_exus_v2",
    "EWJ": "japan",
    "EWG": "germany",
    "EWU": "uk",
    "EEM": "em_broad",
    "VWO": "em_v2",
    "EWZ": "brazil",
    "INDA": "india",
    "FXI": "china",
    "EWY": "korea",
    "EWT": "taiwan",
    "EWW": "mexico",
    "VGK": "europe",
    "DX-Y.NYB": "dxy",
    "CL=F": "wti_oil",
    "^VIX": "vix",
    "MCHI": "msci_china",
    "KWEB": "china_internet",
    "EMXC": "em_ex_china",
    "ACWI": "world",
    "^TNX": "tnx_10y_yield",
}

YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5y&interval=1d&includePrePost=false"
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch(symbol):
    url = YAHOO.format(symbol=urllib.parse.quote(symbol))
    req = urllib.request.Request(url, headers=HDR)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
        node = data["chart"]["result"][0]
        ts = node["timestamp"]
        adj = (node.get("indicators", {}).get("adjclose") or [{}])[0].get("adjclose") or []
        close = (node.get("indicators", {}).get("quote") or [{}])[0].get("close") or []
        prices = adj if adj else close
        rows = []
        for t, p in zip(ts, prices):
            if p is None:
                continue
            try:
                pv = float(p)
            except (TypeError, ValueError):
                continue
            if pv <= 0 or pv != pv:
                continue
            d = datetime.fromtimestamp(int(t), tz=timezone.utc).date()
            rows.append((d, pv))
        rows.sort()
        return rows
    except Exception as e:
        print(f"  ERR {symbol}: {e}", file=sys.stderr, flush=True)
        return []


def save_csv(alias, rows):
    path = os.path.join(OUT, f"{alias}.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "price"])
        for d, p in rows:
            w.writerow([d.isoformat(), p])


if __name__ == "__main__":
    counts = {}
    for sym, alias in UNIVERSE.items():
        rows = fetch(sym)
        counts[sym] = len(rows)
        if rows:
            save_csv(alias, rows)
        print(f"{sym} ({alias}): {len(rows)} rows", flush=True)
        time.sleep(0.4)
    print(f"\nTotal: {sum(counts.values())} rows across {len(counts)} series → {OUT}")
