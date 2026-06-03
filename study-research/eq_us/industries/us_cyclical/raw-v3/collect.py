# -*- coding: utf-8 -*-
"""collect.py — us_cyclical sleeve §M v3 universe + 가격 + EDGAR 펀더멘털 수집.

frame v3 §M.7 + .dispatch-us-sleeve-role. ★미국 = yfinance(가격) + EDGAR XBRL(valuation PIT) + FRED(거시).
★role 지시: foreground 동기 + incremental save (한국 DART background 미유지 교훈). EDGAR rate limit 주의(10 req/s).

universe = SOXX/XLB/XLI/XLE/XLF 5 sector 대표 종목 (sector ETF top holdings 기반 큐레이션, 시총 floor).
★survivorship-biased 명시(현재 holdings = 생존 종목, 상폐 누락 = collector_plan high).

산출: data/{universe.parquet, prices.parquet, edgar_fundamentals.parquet, macro.parquet}
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
FRED_DIR = Path("D:/projects/Inv/study-research/eq_us_cyclical/raw/fred")  # 기존 FRED CSV 재사용

START, END = "2015-01-01", "2026-05-29"
EDGAR_HDR = {"User-Agent": "inv-research research@example.com"}

# us_cyclical universe = 5 sector × 대표 종목 (sector ETF holdings 큐레이션)
UNIVERSE = {
    "SOXX_semi": ["NVDA", "AVGO", "AMD", "QCOM", "TXN", "MU", "ADI", "LRCX", "KLAC", "AMAT", "INTC", "MCHP"],
    "XLB_materials": ["LIN", "SHW", "FCX", "ECL", "NEM", "APD", "DOW", "DD", "NUE", "PPG", "VMC", "MLM"],
    "XLI_industrials": ["CAT", "GE", "HON", "UNP", "BA", "RTX", "DE", "UPS", "LMT", "ETN", "EMR", "ITW"],
    "XLE_energy": ["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO", "OXY", "WMB", "HAL", "DVN"],
    "XLF_financials": ["JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPGI", "BLK", "C", "AXP", "SCHW"],
}


def build_universe() -> pd.DataFrame:
    cache = DATA / "universe.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    rows = []
    for sector, tickers in UNIVERSE.items():
        for t in tickers:
            rows.append(dict(ticker=t, sector=sector, subcl=sector.split("_")[1]))
    df = pd.DataFrame(rows)
    df.to_parquet(cache)
    return df


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


def collect_prices(tickers) -> pd.DataFrame:
    cache = DATA / "prices.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import yfinance as yf
    closes = {}
    for i, t in enumerate(tickers):
        try:
            h = yf.download(t, start=START, end=END, progress=False, auto_adjust=True)["Close"]
            h = h.squeeze()
            if len(h):
                closes[t] = h
                print(f"  [{i}] {t} ok {len(h)} rows")
            else:
                print(f"  [{i}] {t} EMPTY")
        except Exception as e:
            print(f"  [{i}] {t} FAIL {repr(e)[:40]}")
        time.sleep(0.2)
    px = pd.DataFrame(closes)
    px.index = pd.to_datetime(px.index)
    px = px.sort_index()
    px.to_parquet(cache)
    return px


def collect_edgar(tickers, cik_map) -> pd.DataFrame:
    """EDGAR companyconcept → StockholdersEquity/NetIncomeLoss/shares (PIT filed date).
    ★incremental save (foreground). filed date = PIT timestamp(lookahead 회피)."""
    cache = DATA / "edgar_fundamentals.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import requests
    rows = []
    for i, t in enumerate(tickers):
        cik = cik_map.get(t.replace("-", "-")) or cik_map.get(t)
        if not cik:
            print(f"  [{i}] {t} no CIK"); continue
        rec = {"ticker": t, "cik": cik}
        # 3 concepts: equity, net_income, shares
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
                    # 각 filing = (end 회계기간, val, filed 공시일 PIT, form)
                    for u in units:
                        rows.append(dict(ticker=t, concept=key, end=u.get("end"),
                                         val=u.get("val"), filed=u.get("filed"),
                                         form=u.get("form"), fp=u.get("fp")))
                time.sleep(0.12)  # EDGAR 10 req/s limit
            except Exception as e:
                print(f"    {t} {concept} FAIL {repr(e)[:40]}")
        print(f"  [{i}] {t} edgar done (cum rows {len(rows)})")
        # ★incremental save every 10 tickers
        if (i + 1) % 10 == 0:
            pd.DataFrame(rows).to_parquet(cache)
            print(f"    ...incremental save at {i+1}")
    df = pd.DataFrame(rows)
    df.to_parquet(cache)
    return df


def load_macro() -> pd.DataFrame:
    """FRED CSV(기존 재사용) + yfinance DXY. HY OAS/DGS10/VIX/dollar."""
    cache = DATA / "macro.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    out = {}
    for fred_id, col in [("BAMLH0A0HYM2", "hy_oas"), ("DGS10", "rate10y"), ("VIXCLS", "vix")]:
        f = FRED_DIR / f"{fred_id}.csv"
        if f.exists():
            s = pd.read_csv(f)
            # FRED CSV: DATE, value cols
            datecol = [c for c in s.columns if c.upper() in ("DATE", "OBSERVATION_DATE")][0]
            valcol = [c for c in s.columns if c != datecol][0]
            ser = pd.Series(pd.to_numeric(s[valcol], errors="coerce").values,
                            index=pd.to_datetime(s[datecol]))
            out[col] = ser
    # DXY via yfinance
    try:
        import yfinance as yf
        dxy = yf.download("DX-Y.NYB", start=START, end=END, progress=False, auto_adjust=True)["Close"].squeeze()
        dxy.index = pd.to_datetime(dxy.index)
        out["dollar"] = dxy
    except Exception as e:
        print(f"  DXY fail {repr(e)[:40]}")
    df = pd.concat(out, axis=1).sort_index().ffill(limit=5)
    df.to_parquet(cache)
    return df


if __name__ == "__main__":
    print("[1/4] universe ...")
    uni = build_universe()
    print(f"  {len(uni)} tickers, sectors: {uni['subcl'].value_counts().to_dict()}")
    tickers = uni["ticker"].tolist()

    print(f"\n[2/4] prices ({len(tickers)} tickers) ...")
    px = collect_prices(tickers)
    print(f"  price panel: {px.shape}  {px.index.min().date()}~{px.index.max().date()}")

    print("\n[3/4] EDGAR fundamentals (PIT filed date) ...")
    cik_map = get_cik_map()
    edgar = collect_edgar(tickers, cik_map)
    print(f"  edgar rows: {len(edgar)}, tickers covered: {edgar['ticker'].nunique() if len(edgar) else 0}")

    print("\n[4/4] macro (FRED + DXY) ...")
    macro = load_macro()
    print(f"  macro: {macro.shape}, cols: {list(macro.columns)}")
    print("DONE")
