"""FRED 무료 3종 macro fetch (P0-B, 2026-05-31).

- DFII10           : 10Y TIPS real rate (Howell Capital Wars + Liu&Tsyvinski 2021 post-2020 macro fit)
- DTWEXBGS         : Broad Trade-Weighted USD index
- M2SL             : USD M2 monetary base
- GOLDAMGBD228NLBM : London Gold AM Fix (H10 digital gold)

pandas_datareader.data.DataReader 사용. FRED 무료 keyless.

⛔ first-release 보장 X (FRED 는 최종 vintage). 단 본 작업 = exploratory. 후속 PIT vintage 적용 가능성 명시.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path
import pandas as pd
from pandas_datareader import data as pdr

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT_DIR = Path(__file__).resolve().parent.parent / "raw" / "data"
SERIES = [
    ("DFII10", "10Y TIPS real rate (daily)"),
    ("DTWEXBGS", "Broad TWI USD index (daily)"),
    ("M2SL", "M2 (monthly)"),
    ("GOLDAMGBD228NLBM", "Gold London AM Fix USD/oz (daily)"),
]
START = "2010-01-01"
END = "2026-05-31"


def fetch_series(code):
    try:
        df = pdr.DataReader(code, "fred", START, END)
        return df
    except Exception as e:
        print(f"  [WARN] {code} fail: {e}", flush=True)
        return None


def main():
    log = []
    for code, name in SERIES:
        print(f"[fetch] {code} ({name})", flush=True)
        df = fetch_series(code)
        if df is None or df.empty:
            print(f"  [WARN] {code} empty", flush=True)
            log.append(f"{code} FAIL")
            time.sleep(0.5)
            continue
        df = df.reset_index()
        df.columns = ["date_utc", code]
        df["date_utc"] = pd.to_datetime(df["date_utc"]).dt.strftime("%Y-%m-%d")
        out = OUT_DIR / f"fred-{code.lower()}.csv"
        df.to_csv(out, index=False)
        msg = f"  {code} {len(df)} rows, {df['date_utc'].iloc[0]} ~ {df['date_utc'].iloc[-1]} -> {out.name}"
        print(msg, flush=True)
        log.append(msg)
        time.sleep(0.3)
    log_p = OUT_DIR / "fred-fetch-log.txt"
    log_p.write_text("\n".join(log), encoding="utf-8")
    print(f"[OK] log -> {log_p.name}", flush=True)


if __name__ == "__main__":
    main()
