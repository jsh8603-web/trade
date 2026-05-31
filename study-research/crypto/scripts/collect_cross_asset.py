"""yfinance 무료 cross-asset fetch (P0-B, 2026-05-31).

- ^IXIC : Nasdaq Composite (H9 BTC-Nasdaq rolling corr)
- ^GSPC : S&P 500 (H9 macro regime baseline)
- ^VIX  : VIX (H10 risk-off filter)

yfinance 1.4.1 사용. 무료 anonymous. daily close 만.

⛔ 합성 X. 실측 fetch only. fail 시 명시 보고.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path
import pandas as pd
import yfinance as yf

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT_DIR = Path(__file__).resolve().parent.parent / "raw" / "data"
TICKERS = ["^IXIC", "^GSPC", "^VIX"]
START = "2010-01-01"
END = "2026-05-31"


def fetch(ticker):
    try:
        df = yf.download(ticker, start=START, end=END, progress=False, auto_adjust=False)
        return df
    except Exception as e:
        print(f"  [WARN] {ticker} fail: {e}", flush=True)
        return None


def main():
    log = []
    for t in TICKERS:
        print(f"[fetch] {t}", flush=True)
        df = fetch(t)
        if df is None or df.empty:
            print(f"  [WARN] {t} empty", flush=True)
            log.append(f"{t} FAIL")
            continue
        df = df.reset_index()
        # MultiIndex columns 평탄화
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] if c[0] else c[1] for c in df.columns]
        df["date_utc"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        keep_cols = ["date_utc"]
        for col in ["Open", "High", "Low", "Close", "Volume", "Adj Close"]:
            if col in df.columns:
                keep_cols.append(col)
        df = df[keep_cols]
        safe = t.replace("^", "").lower()
        out = OUT_DIR / f"yfinance-{safe}.csv"
        df.to_csv(out, index=False)
        msg = f"  {t} {len(df)} rows, {df['date_utc'].iloc[0]} ~ {df['date_utc'].iloc[-1]} -> {out.name}"
        print(msg, flush=True)
        log.append(msg)
        time.sleep(0.5)
    log_p = OUT_DIR / "yfinance-fetch-log.txt"
    log_p.write_text("\n".join(log), encoding="utf-8")
    print(f"[OK] log -> {log_p.name}", flush=True)


if __name__ == "__main__":
    main()
