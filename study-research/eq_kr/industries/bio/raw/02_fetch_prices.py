"""바이오 universe Top 30 일별 수정주가 + 거시 시계열 적재.

목적:
1. 가격 = FDR `data_reader(code, start, end)` → 일별 Close, Volume
2. 거시 = FDR FRED (DGS10, DGS2, BAMLH0A0HYM2) + USDKRW (KRW=X), KOSPI / KOSDAQ index
3. 적재 기간: 2010-01-01 ~ 2026-05-29 (16년 = ~4150 영업일, ~200 월)
4. 산출: data/prices_daily.parquet + data/macro_daily.parquet

Lookback: 5게이트 M4 #1 N gate (월간 N≥24) 확보 위해 16년 데이터 → 월별 N≈196.
"""
from __future__ import annotations
from pathlib import Path
from datetime import date
import time
import sys

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
START = "2010-01-01"
END = "2026-05-29"


def fetch_prices_for_universe(top_n: int = 30) -> pd.DataFrame:
    import FinanceDataReader as fdr
    uni = pd.read_csv(DATA_DIR / "universe_bio_filtered.csv", encoding="utf-8-sig", dtype={"Code": str})
    uni = uni.head(top_n)
    print(f"가격 fetch 대상: {len(uni)} ticker (Top {top_n})")

    frames = []
    for i, row in uni.iterrows():
        tk = row["Code"]
        name = row["Name"]
        try:
            df = fdr.DataReader(tk, START, END)
            if df.empty:
                print(f"  [{i+1}/{len(uni)}] {tk} {name}: empty")
                continue
            df = df[["Close", "Volume"]].copy()
            df.columns = [f"{tk}_close", f"{tk}_vol"]
            frames.append(df)
            print(f"  [{i+1}/{len(uni)}] {tk} {name}: {len(df)} rows ({df.index.min().date()} ~ {df.index.max().date()})")
        except Exception as e:
            print(f"  [{i+1}/{len(uni)}] {tk} {name}: ERROR {e}")
        time.sleep(0.1)  # rate limit

    if not frames:
        print("ERROR: 수집 결과 0개")
        return pd.DataFrame()

    out = pd.concat(frames, axis=1)
    out.index.name = "date"
    return out


def fetch_macro() -> pd.DataFrame:
    """FRED + FDR 거시 시리즈."""
    import FinanceDataReader as fdr

    macro_frames = {}

    # FRED 시리즈
    fred_series = {
        "DGS10": "us_10y",
        "DGS2": "us_2y",
        "BAMLH0A0HYM2": "hy_oas",
        "DEXKOUS": "usdkrw_fred",  # KRW per USD daily noon (Federal Reserve)
    }
    for sid, label in fred_series.items():
        try:
            df = fdr.DataReader(f"FRED:{sid}", START, END)
            if not df.empty:
                df.columns = [label]
                macro_frames[label] = df
                print(f"  FRED:{sid} → {label}: {len(df)} rows")
            else:
                print(f"  FRED:{sid} → {label}: empty")
        except Exception as e:
            print(f"  FRED:{sid} → {label}: ERROR {e}")

    # FDR 한국 시장 지수
    kr_series = {
        "KS11": "kospi",
        "KQ11": "kosdaq",
        "USD/KRW": "usdkrw",
    }
    for sid, label in kr_series.items():
        try:
            df = fdr.DataReader(sid, START, END)
            if not df.empty:
                col = "Close" if "Close" in df.columns else df.columns[0]
                df = df[[col]].copy()
                df.columns = [label]
                macro_frames[label] = df
                print(f"  FDR:{sid} → {label}: {len(df)} rows")
        except Exception as e:
            print(f"  FDR:{sid} → {label}: ERROR {e}")

    if not macro_frames:
        return pd.DataFrame()

    out = pd.concat(macro_frames.values(), axis=1)
    out.index.name = "date"
    return out


if __name__ == "__main__":
    print("=== 1. 가격 시계열 ===")
    prices = fetch_prices_for_universe(top_n=30)
    if not prices.empty:
        out_p = DATA_DIR / "prices_daily.parquet"
        prices.to_parquet(out_p)
        print(f"\n저장: {out_p} (shape={prices.shape})")

    print("\n=== 2. 거시 시계열 ===")
    macro = fetch_macro()
    if not macro.empty:
        out_m = DATA_DIR / "macro_daily.parquet"
        macro.to_parquet(out_m)
        print(f"\n저장: {out_m} (shape={macro.shape})")
        print(macro.tail())
