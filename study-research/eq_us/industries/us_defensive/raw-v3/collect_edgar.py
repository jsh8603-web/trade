# -*- coding: utf-8 -*-
"""collect_edgar.py — us_defensive 48종 EDGAR 펀더멘털 PIT 수집 (valuation 횡단면).
us_cyclical raw-v3/collect.py EDGAR 패턴 미러 (검증본).

★EDGAR companyconcept XBRL → StockholdersEquity/NetIncomeLoss/shares + filed date PIT(lookahead 회피).
★role 지시: foreground 동기 + incremental save (한국 DART background 미유지 교훈). EDGAR 10 req/s sleep.

산출:
- data/cik_map.json            — ticker → CIK 매핑
- data/edgar_fundamentals.parquet — (ticker, concept, end 회계기간말, val, filed 공시일PIT, form)
"""
from __future__ import annotations
import sys, io, json, time
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
EDGAR_HDR = {"User-Agent": "inv-research research@example.com"}


def get_cik_map() -> dict:
    cache = DATA / "cik_map.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=EDGAR_HDR, timeout=30)
    j = r.json()
    tmap = {v["ticker"].replace(".", "-"): str(v["cik_str"]).zfill(10) for v in j.values()}
    cache.write_text(json.dumps(tmap), encoding="utf-8")
    return tmap


def collect_edgar(tickers, cik_map) -> pd.DataFrame:
    """EDGAR companyconcept → equity/net_income/shares (PIT filed date). incremental save."""
    cache = DATA / "edgar_fundamentals.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    rows = []
    for i, t in enumerate(tickers):
        cik = cik_map.get(t.replace("-", "-")) or cik_map.get(t)
        if not cik:
            print(f"  [{i}] {t} no CIK", flush=True); continue
        for concept, unit, key in [
            ("StockholdersEquity", "USD", "equity"),
            ("NetIncomeLoss", "USD", "net_income"),
            ("CommonStockSharesOutstanding", "shares", "shares"),
        ]:
            try:
                r = requests.get(
                    f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json",
                    headers=EDGAR_HDR, timeout=30)
                if r.status_code == 200:
                    units = r.json().get("units", {}).get(unit, [])
                    for u in units:
                        rows.append(dict(ticker=t, concept=key, end=u.get("end"),
                                         val=u.get("val"), filed=u.get("filed"),
                                         form=u.get("form"), fp=u.get("fp")))
                time.sleep(0.12)  # EDGAR 10 req/s limit
            except Exception as e:
                print(f"    {t} {concept} FAIL {repr(e)[:40]}", flush=True)
        print(f"  [{i}] {t} edgar done (cum rows {len(rows)})", flush=True)
        if (i + 1) % 10 == 0:
            pd.DataFrame(rows).to_parquet(cache)
            print(f"    ...incremental save at {i+1}", flush=True)
    df = pd.DataFrame(rows)
    df.to_parquet(cache)
    return df


if __name__ == "__main__":
    uni = json.loads((DATA / "universe.json").read_text(encoding="utf-8"))
    tickers = list(uni["tickers"].keys())
    print(f"universe {len(tickers)} tickers", flush=True)
    print("[1/2] CIK map ...", flush=True)
    cik_map = get_cik_map()
    print(f"  cik_map: {len(cik_map)} listed", flush=True)
    print("\n[2/2] EDGAR fundamentals (PIT filed date) ...", flush=True)
    edgar = collect_edgar(tickers, cik_map)
    print(f"\n  edgar rows: {len(edgar)}, tickers covered: {edgar['ticker'].nunique() if len(edgar) else 0}", flush=True)
    print("DONE", flush=True)
