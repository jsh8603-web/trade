# -*- coding: utf-8 -*-
"""collect.py — us_defensive sleeve §M v3 universe + 횡단면 패널 수집 (yfinance).

frame v3 §M.7 exposure card 계약. 한국 battery/반도체/auto collect.py 미러 (pykrx → yfinance).
role = .dispatch-us-sleeve-role.md ({SLEEVE}=us_defensive, archetype=asset_stable).

universe: XLP/XLU/XLV/XLC-mature 대표 종목 (defensive sleeve). ETF holdings 상위 시총 종목.
  ★cross-sectional IC 위해 4 ETF 가 아니라 holdings 개별 종목 패널 (한국 universe 대응).
  ★survivorship-biased: 현재 holdings 스냅샷 = 상폐/제외 종목 누락 → collector_plan high.

가격: yfinance (ETF + 종목 OHLCV). 거래대금 = Close × Volume (ADV proxy).
★데이터: 기존 eq_us_defensive/raw/yfinance/sector_etf_close.csv (2000~, 실데이터 §1.7-D 통과) = ETF prior.
  개별 종목 = yfinance 신규 fetch (foreground+incremental, EDGAR background 미유지 교훈).

산출:
- data/universe.json       — defensive 종목 리스트 (sector tag)
- data/prices.parquet      — 종목 일별 종가 패널
- data/amount.parquet      — 일별 거래대금 (ADV 티어)
"""
from __future__ import annotations
import sys, io, json, time
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

START = "2010-01-01"   # ETF holdings 종목 안정 상장 + HY OAS 가용 이후 충분 표본
END = "2026-05-29"

# ── us_defensive universe (asset_stable: XLP/XLU/XLV/XLC-mature 대표 종목) ──
# ETF holdings 상위 + 시총 대형 (yfinance 가용). sector tag = peer-group.
# ★survivorship: 현재 대형주 스냅샷 (상폐/제외 누락 = collector_plan high).
DEFENSIVE_UNIVERSE = {
    # XLP 소비필수 (consumer staples)
    "PG": "staples", "KO": "staples", "PEP": "staples", "COST": "staples", "WMT": "staples",
    "PM": "staples", "MO": "staples", "MDLZ": "staples", "CL": "staples", "KMB": "staples",
    "GIS": "staples", "KHC": "staples", "HSY": "staples", "STZ": "staples", "K": "staples",
    # XLU 유틸리티 (utilities, rate-sensitive)
    "NEE": "utilities", "DUK": "utilities", "SO": "utilities", "D": "utilities", "AEP": "utilities",
    "EXC": "utilities", "XEL": "utilities", "ED": "utilities", "PEG": "utilities", "WEC": "utilities",
    "ES": "utilities", "AEE": "utilities", "DTE": "utilities", "PPL": "utilities", "CMS": "utilities",
    # XLV 헬스케어 (healthcare, defensive)
    "JNJ": "healthcare", "UNH": "healthcare", "LLY": "healthcare", "MRK": "healthcare", "ABBV": "healthcare",
    "PFE": "healthcare", "TMO": "healthcare", "ABT": "healthcare", "DHR": "healthcare", "BMY": "healthcare",
    "AMGN": "healthcare", "MDT": "healthcare", "GILD": "healthcare", "CVS": "healthcare", "CI": "healthcare",
    # XLC-mature 커뮤니케이션 성숙 (telecom-like, dividend) — XLC 中 방어적 성숙주
    "VZ": "comm_mature", "T": "comm_mature", "CMCSA": "comm_mature", "TMUS": "comm_mature",
}


def build_universe() -> dict:
    cache = DATA / "universe.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    out = {"as_of": END, "sleeve": "us_defensive", "archetype": "asset_stable",
           "n": len(DEFENSIVE_UNIVERSE),
           "survivorship_note": "현재 대형주 스냅샷(yfinance). 상폐/제외 종목(예: 과거 staples M&A) 누락 = survivorship-biased = collector_plan high.",
           "tickers": DEFENSIVE_UNIVERSE}
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def collect_prices(tickers: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    cache_px = DATA / "prices.parquet"
    cache_amt = DATA / "amount.parquet"
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
            amts[t] = (df["Close"] * df["Volume"]).squeeze()  # 거래대금 = ADV proxy
            print(f"  [{i}] {t} ok rows={len(df)}", flush=True)
        except Exception as ex:
            print(f"  [{i}] {t} FAIL {repr(ex)[:60]}", flush=True)
        time.sleep(0.2)
        # ★incremental checkpoint (background 미유지 교훈)
        if closes and (i + 1) % 10 == 0:
            pd.DataFrame(closes).sort_index().to_parquet(cache_px)
            pd.DataFrame(amts).sort_index().to_parquet(cache_amt)
    px = pd.DataFrame(closes).sort_index(); amt = pd.DataFrame(amts).sort_index()
    px.index = pd.to_datetime(px.index); amt.index = pd.to_datetime(amt.index)
    px.to_parquet(cache_px); amt.to_parquet(cache_amt)
    return px, amt


if __name__ == "__main__":
    print("[1/2] universe ...", flush=True)
    uni = build_universe()
    print(f"  defensive universe n={uni['n']} (staples/utilities/healthcare/comm_mature)", flush=True)

    tickers = list(uni["tickers"].keys())
    print(f"\n[2/2] prices ({len(tickers)} tickers, yfinance) ...", flush=True)
    px, amt = collect_prices(tickers)
    print(f"  price panel: {px.shape}  date {px.index.min().date()}~{px.index.max().date()}", flush=True)
    print("\nDONE", flush=True)
