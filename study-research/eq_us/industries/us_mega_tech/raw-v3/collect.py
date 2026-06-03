# -*- coding: utf-8 -*-
"""collect.py — us_mega_tech sleeve §M v3 universe + 가격 + EDGAR 펀더멘털. us_cyclical 미러.

frame v3 §M.7 + .dispatch-us-sleeve-role ({SLEEVE}=us_mega_tech, archetype=compounder).
★미국 = yfinance(가격) + EDGAR XBRL(valuation+capex PIT) + FRED(거시). foreground+incremental(role 교훈).

★universe = Mag7 custom basket (GICS 파편화 = sector ETF 합산 불가 → 사용자 박제 basket):
  Mag7(AAPL/MSFT/NVDA/GOOGL/META/AMZN/TSLA) + AVGO/ORCL/AMD (+ASML US ADR).
  ★survivorship: 현 대형주 basket = 생존(상폐 없음, mega-tech 특성상 생존편향 약하나 명시).
★compounder = expensive_trap(고PER 정상, growth-duration). PER value premium 반대(성장·fwd EPS).

산출: data/{universe.json, prices.parquet, amount.parquet, edgar_fundamentals.parquet}
"""
from __future__ import annotations
import sys, io, time, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

START, END = "2015-01-01", "2026-05-29"   # Mag7 안정 + AI cycle(2023~) 포함
EDGAR_HDR = {"User-Agent": "inv-research research@example.com"}

# ★Mag7 custom basket + AI 반도체/SW 인접 (compounder sleeve, 사용자 박제 T0)
MEGA_TECH = {
    "AAPL": "mag7", "MSFT": "mag7", "NVDA": "mag7", "GOOGL": "mag7",
    "META": "mag7", "AMZN": "mag7", "TSLA": "mag7",
    "AVGO": "ai_semi", "AMD": "ai_semi",  # AI 반도체 인접
    "ORCL": "ai_sw",                       # AI SW/클라우드 인접
    "ASML": "ai_semi_adr",                 # ASML US ADR (±)
}


def build_universe() -> dict:
    cache = DATA / "universe.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    out = {"as_of": END, "sleeve": "us_mega_tech", "archetype": "compounder",
           "n": len(MEGA_TECH),
           "survivorship_note": "Mag7 custom basket = 현 대형주(생존). mega-tech 특성상 상폐 거의 없으나 PIT 멤버십(편입 시점=NVDA AI 이전/이후) = collector_plan.",
           "basket_note": "GICS 파편화(AAPL=IT/AMZN=consumer disc/GOOGL=comm) → sector ETF 합산 불가 = custom basket(사용자 SSOT).",
           "tickers": MEGA_TECH}
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def collect_prices(tickers) -> tuple[pd.DataFrame, pd.DataFrame]:
    cache_px = DATA / "prices.parquet"; cache_amt = DATA / "amount.parquet"
    if cache_px.exists() and cache_amt.exists():
        return pd.read_parquet(cache_px), pd.read_parquet(cache_amt)
    import yfinance as yf
    closes, amts = {}, {}
    for i, t in enumerate(tickers):
        try:
            df = yf.download(t, start=START, end=END, progress=False, auto_adjust=True)
            if len(df) == 0:
                print(f"  [{i}] {t} EMPTY", flush=True); continue
            closes[t] = df["Close"].squeeze()
            amts[t] = (df["Close"] * df["Volume"]).squeeze()
            print(f"  [{i}] {t} ok rows={len(df)}", flush=True)
        except Exception as ex:
            print(f"  [{i}] {t} FAIL {repr(ex)[:60]}", flush=True)
        time.sleep(0.2)
    px = pd.DataFrame(closes).sort_index(); amt = pd.DataFrame(amts).sort_index()
    px.index = pd.to_datetime(px.index); amt.index = pd.to_datetime(amt.index)
    px.to_parquet(cache_px); amt.to_parquet(cache_amt)
    return px, amt


def get_cik_map() -> dict:
    cache = DATA / "cik_map.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    import requests
    r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=EDGAR_HDR, timeout=30)
    j = r.json()
    tmap = {v["ticker"].replace(".", "-"): str(v["cik_str"]).zfill(10) for v in j.values()}
    cache.write_text(json.dumps(tmap), encoding="utf-8")
    return tmap


def collect_edgar(tickers, cik_map) -> pd.DataFrame:
    """EDGAR companyconcept → equity/net_income/shares + ★capex(H6 AI capex) (PIT filed)."""
    cache = DATA / "edgar_fundamentals.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import requests
    rows = []
    # ★capex = PaymentsToAcquirePropertyPlantAndEquipment (H6 AI capex→fwd EPS)
    concepts = [
        ("StockholdersEquity", "USD", "equity"),
        ("NetIncomeLoss", "USD", "net_income"),
        ("CommonStockSharesOutstanding", "shares", "shares"),
        ("PaymentsToAcquirePropertyPlantAndEquipment", "USD", "capex"),
    ]
    for i, t in enumerate(tickers):
        cik = cik_map.get(t.replace("-", "-")) or cik_map.get(t)
        if not cik:
            print(f"  [{i}] {t} no CIK", flush=True); continue
        for concept, unit, key in concepts:
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
                time.sleep(0.12)  # EDGAR 10 req/s
            except Exception as e:
                print(f"    {t} {concept} FAIL {repr(e)[:40]}", flush=True)
        print(f"  [{i}] {t} edgar done (cum {len(rows)})", flush=True)
        if (i + 1) % 5 == 0:
            pd.DataFrame(rows).to_parquet(cache)
    df = pd.DataFrame(rows); df.to_parquet(cache)
    return df


if __name__ == "__main__":
    print("[1/3] universe ...", flush=True)
    uni = build_universe()
    print(f"  mega_tech basket n={uni['n']} ({list(uni['tickers'].keys())})", flush=True)
    tickers = list(uni["tickers"].keys())

    print(f"\n[2/3] prices ({len(tickers)}) ...", flush=True)
    px, amt = collect_prices(tickers)
    print(f"  price panel: {px.shape}  {px.index.min().date()}~{px.index.max().date()}", flush=True)

    print("\n[3/3] EDGAR (equity/net_income/shares/capex, PIT filed) ...", flush=True)
    cik_map = get_cik_map()
    edgar = collect_edgar(tickers, cik_map)
    print(f"  edgar rows: {len(edgar)}, tickers: {edgar['ticker'].nunique() if len(edgar) else 0}", flush=True)
    print("DONE", flush=True)
