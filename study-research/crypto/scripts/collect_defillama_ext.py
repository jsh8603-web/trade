"""DefiLlama TVL + DEX 확장 fetch (P0-C, 2026-05-31).

기존 stablecoin total 보존 + 추가:
- /v2/historicalChainTvl : 전체 chain TVL daily
- /overview/dexs        : DEX 7d volume

theory-notes §6.6 H12 DeFi utility 검증용. ⛔ 합성 X.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path
import pandas as pd
import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT_DIR = Path(__file__).resolve().parent.parent / "raw" / "data"
S = requests.Session()
S.headers.update({"Accept": "application/json", "User-Agent": "study-Inv-crypto-2.5/cycle2"})


def fetch_tvl():
    url = "https://api.llama.fi/v2/historicalChainTvl"
    r = S.get(url, timeout=60)
    if r.status_code != 200:
        print(f"  TVL HTTP {r.status_code}", flush=True)
        return None
    data = r.json()
    rows = [{"date_utc": pd.to_datetime(d["date"], unit="s").strftime("%Y-%m-%d"), "tvl_total": d["tvl"]} for d in data]
    return pd.DataFrame(rows)


def fetch_dex():
    url = "https://api.llama.fi/overview/dexs?excludeTotalDataChart=false"
    r = S.get(url, timeout=60)
    if r.status_code != 200:
        print(f"  DEX HTTP {r.status_code}", flush=True)
        return None
    data = r.json()
    chart = data.get("totalDataChart", [])
    rows = [{"date_utc": pd.to_datetime(d[0], unit="s").strftime("%Y-%m-%d"), "dex_vol_24h": d[1]} for d in chart]
    return pd.DataFrame(rows)


def main():
    print("[fetch] DefiLlama TVL historical chains", flush=True)
    df_tvl = fetch_tvl()
    if df_tvl is not None and not df_tvl.empty:
        out = OUT_DIR / "defillama-tvl-total.csv"
        df_tvl.to_csv(out, index=False)
        print(f"  TVL {len(df_tvl)} rows, {df_tvl['date_utc'].iloc[0]} ~ {df_tvl['date_utc'].iloc[-1]} -> {out.name}", flush=True)

    time.sleep(0.5)

    print("[fetch] DefiLlama DEX overview", flush=True)
    df_dex = fetch_dex()
    if df_dex is not None and not df_dex.empty:
        out = OUT_DIR / "defillama-dex-total.csv"
        df_dex.to_csv(out, index=False)
        print(f"  DEX {len(df_dex)} rows, {df_dex['date_utc'].iloc[0]} ~ {df_dex['date_utc'].iloc[-1]} -> {out.name}", flush=True)


if __name__ == "__main__":
    main()
