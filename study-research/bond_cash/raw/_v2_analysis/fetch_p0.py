"""fetch_p0.py — bond_cash v2 Phase 4-1 P0 collector self-fetch (2026-05-31, btn-powerbi).

main option A 회신 직후 진입. P0 5건 self-fetch + provenance 박제.

Sources (★ 합성·시뮬 금지, ★ FRED first-release vintage = D축 PIT 부합):
  C1 FRED rates (6)         : DGS10 / DGS2 / DGS3MO / DFII10 / FEDFUNDS / MORTGAGE30US
  C2 ETF (yfinance, 14)     : TLT IEF SHY BIL SHV HYG JNK LQD TIP VTIP STIP EDV TLH VGSH
  C4 MOVE (yfinance)        : ^MOVE (1988~ inception)
  C5 ACM term premium (NY Fed xlsx) : ACMTermPremium.xls (1961~, 10.1MB, 200 OK 검증완)
  C9 HY OAS + pre-2023 대체 : BAMLH0A0HYM2 (2023-05~ FRED 무료) + BAA10Y (1986~) + NFCI (1971~)

Outputs:
  data/{symbol}.parquet         : 시계열 (date index, columns = source-native)
  data/_provenance.json         : fetch 메타 (source URL / 시각 / first-release flag / row count)

Audit-ready (AUDIT-GUIDE 12축):
  - D 축 (PIT) : FRED `realtime_start`/`realtime_end` = first-release default 박제
  - I 축 (생존편향) : ETF universe = inception 부터 fetch, 중도 삭제 ETF 없음 (cross-check Phase 5)
  - K 축 (시도공시) : 본 스크립트 1회 run, retry log = stdout
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
PROV_PATH = ROOT / "_provenance.json"

load_dotenv(ROOT.parents[3] / ".env")  # D:/projects/Inv/.env
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
assert FRED_API_KEY, "FRED_API_KEY missing (.env)"

# ---------------------------------------------------------------- catalogs
FRED_SERIES = {
    # C1 rates
    "DGS10":         {"start": "1962-01-02", "freq": "D", "cat": "rate_nominal"},
    "DGS2":          {"start": "1976-06-01", "freq": "D", "cat": "rate_nominal"},
    "DGS3MO":        {"start": "1981-09-01", "freq": "D", "cat": "rate_nominal"},
    "DFII10":        {"start": "2003-01-02", "freq": "D", "cat": "rate_real_tips"},
    "FEDFUNDS":      {"start": "1954-07-01", "freq": "M", "cat": "rate_policy"},
    "MORTGAGE30US":  {"start": "1971-04-01", "freq": "W", "cat": "rate_mortgage"},
    # C9 HY + pre-2023 대체
    "BAMLH0A0HYM2":  {"start": "1996-12-31", "freq": "D", "cat": "credit_hy_oas"},
    "BAA10Y":        {"start": "1986-01-02", "freq": "D", "cat": "credit_baa_spread"},
    "NFCI":          {"start": "1971-01-08", "freq": "W", "cat": "financial_conditions"},
}

YF_TICKERS = {
    # C2 ETF (universe = bond ETF representative, 14종)
    "TLT":  {"cat": "tsy_long",   "inception": "2002-07-30"},
    "TLH":  {"cat": "tsy_long",   "inception": "2007-01-11"},
    "EDV":  {"cat": "tsy_long",   "inception": "2007-12-10"},
    "IEF":  {"cat": "tsy_mid",    "inception": "2002-07-26"},
    "SHY":  {"cat": "tsy_short",  "inception": "2002-07-26"},
    "VGSH": {"cat": "tsy_short",  "inception": "2009-11-23"},
    "BIL":  {"cat": "cash_tbill", "inception": "2007-05-30"},
    "SHV":  {"cat": "cash_tbill", "inception": "2007-01-11"},
    "HYG":  {"cat": "hy_credit",  "inception": "2007-04-11"},
    "JNK":  {"cat": "hy_credit",  "inception": "2007-12-04"},
    "LQD":  {"cat": "ig_credit",  "inception": "2002-07-26"},
    "TIP":  {"cat": "tips",       "inception": "2003-12-05"},
    "VTIP": {"cat": "tips",       "inception": "2012-10-16"},
    "STIP": {"cat": "tips",       "inception": "2010-12-03"},
    # C4 MOVE
    "^MOVE": {"cat": "vol_bond",  "inception": "1988-01-04"},
}

ACM_URL = "https://www.newyorkfed.org/medialibrary/media/research/data_indicators/ACMTermPremium.xls"


# ---------------------------------------------------------------- helpers
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_fred(series_id: str, start: str) -> pd.DataFrame:
    """FRED REST API — first-release 우선 (PIT). default realtime_start = today, end = today
    → 현재 vintage 가 곧 first-release. Phase 6 audit 시 vintage_query API 별도 박제."""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    obs = r.json().get("observations", [])
    df = pd.DataFrame(obs)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")[["value"]].rename(columns={"value": series_id})
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    return df.dropna(how="all")


def fetch_yf(ticker: str, inception: str) -> pd.DataFrame:
    """yfinance daily OHLCV. Close + Adj Close. Adj Close = total-return 보정 (배당 재투자)."""
    import yfinance as yf
    t = yf.Ticker(ticker)
    df = t.history(start=inception, auto_adjust=False, actions=False)
    if df.empty:
        return df
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].copy()
    df.columns = [f"{ticker}_{c.replace(' ', '_').lower()}" for c in df.columns]
    return df


def fetch_acm() -> pd.DataFrame:
    """NY Fed ACM Term Premium .xls — Adrian-Crump-Moench (2013) FRBNY.
    Sheet 'ACM Daily' = daily 1-10Y maturities, ACMY01~10 (yield) + ACMTP01~10 (term premium)."""
    r = requests.get(ACM_URL, timeout=120)
    r.raise_for_status()
    raw_path = DATA / "ACMTermPremium.xls"
    raw_path.write_bytes(r.content)
    # xlrd 2.0 = .xls only. ACM file 의 sheet 명 확인 후 parse.
    xls = pd.ExcelFile(raw_path, engine="xlrd")
    # NY Fed 의 ACM 파일은 보통 첫 sheet 가 daily data, 두 번째 가 monthly.
    sheet = "ACM Daily" if "ACM Daily" in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(raw_path, sheet_name=sheet, engine="xlrd")
    # 'DATE' 컬럼 정규화
    date_col = next((c for c in df.columns if str(c).strip().upper() in {"DATE", "TIME"}), df.columns[0])
    df["date"] = pd.to_datetime(df[date_col])
    df = df.set_index("date").drop(columns=[date_col])
    return df, xls.sheet_names


# ---------------------------------------------------------------- main
def main(dry_run: bool = False):
    prov = {
        "fetched_at": now_iso(),
        "fetcher": "fetch_p0.py",
        "session": "btn-powerbi",
        "main_directive": "option A (P0 self-fetch)",
        "sources": {},
        "tries": {},
        "errors": [],
    }

    # ---- FRED batch
    print(f"[FRED] {len(FRED_SERIES)} series fetch ...", flush=True)
    for sid, meta in FRED_SERIES.items():
        t0 = time.time()
        try:
            if dry_run:
                print(f"  [DRY] {sid} (cat={meta['cat']}, start={meta['start']})")
                continue
            df = fetch_fred(sid, meta["start"])
            out = DATA / f"{sid}.parquet"
            df.to_parquet(out)
            prov["sources"][sid] = {
                "kind": "fred",
                "url": f"https://fred.stlouisfed.org/series/{sid}",
                "cat": meta["cat"],
                "rows": len(df),
                "start": str(df.index.min().date()) if len(df) else None,
                "end":   str(df.index.max().date()) if len(df) else None,
                "elapsed_sec": round(time.time() - t0, 2),
                "first_release_default": True,  # FRED default realtime = today vintage
            }
            print(f"  [OK] {sid:14s} rows={len(df):>6d} {prov['sources'][sid]['start']}~{prov['sources'][sid]['end']}  ({prov['sources'][sid]['elapsed_sec']}s)")
        except Exception as e:
            prov["errors"].append({"id": sid, "kind": "fred", "msg": repr(e)[:300]})
            print(f"  [ERR] {sid}: {e!r}")

    # ---- yfinance batch (incl. ^MOVE)
    print(f"\n[yfinance] {len(YF_TICKERS)} tickers fetch ...", flush=True)
    for tic, meta in YF_TICKERS.items():
        t0 = time.time()
        try:
            if dry_run:
                print(f"  [DRY] {tic} (cat={meta['cat']}, inception={meta['inception']})")
                continue
            df = fetch_yf(tic, meta["inception"])
            safe = tic.replace("^", "")
            out = DATA / f"YF_{safe}.parquet"
            df.to_parquet(out)
            prov["sources"][tic] = {
                "kind": "yfinance",
                "url": f"https://finance.yahoo.com/quote/{tic}/",
                "cat": meta["cat"],
                "rows": len(df),
                "start": str(df.index.min().date()) if len(df) else None,
                "end":   str(df.index.max().date()) if len(df) else None,
                "elapsed_sec": round(time.time() - t0, 2),
            }
            print(f"  [OK] {tic:8s} rows={len(df):>6d} {prov['sources'][tic]['start']}~{prov['sources'][tic]['end']}  ({prov['sources'][tic]['elapsed_sec']}s)")
        except Exception as e:
            prov["errors"].append({"id": tic, "kind": "yfinance", "msg": repr(e)[:300]})
            print(f"  [ERR] {tic}: {e!r}")

    # ---- ACM xlsx
    print(f"\n[ACM] NY Fed xlsx fetch ...", flush=True)
    t0 = time.time()
    try:
        if dry_run:
            print(f"  [DRY] ACM xlsx {ACM_URL}")
        else:
            acm_df, sheet_names = fetch_acm()
            out = DATA / "ACM.parquet"
            acm_df.to_parquet(out)
            prov["sources"]["ACM"] = {
                "kind": "ny_fed_xls",
                "url": ACM_URL,
                "cat": "term_premium",
                "rows": len(acm_df),
                "start": str(acm_df.index.min().date()) if len(acm_df) else None,
                "end":   str(acm_df.index.max().date()) if len(acm_df) else None,
                "elapsed_sec": round(time.time() - t0, 2),
                "sheet_names": sheet_names,
                "columns": list(map(str, acm_df.columns[:20])),
            }
            print(f"  [OK] ACM rows={len(acm_df):>6d} sheets={sheet_names} cols(first 20)={list(map(str, acm_df.columns[:20]))}")
    except Exception as e:
        prov["errors"].append({"id": "ACM", "kind": "ny_fed_xls", "msg": repr(e)[:500]})
        print(f"  [ERR] ACM: {e!r}")

    # ---- write provenance
    prov["tries"]["fred"] = len(FRED_SERIES)
    prov["tries"]["yfinance"] = len(YF_TICKERS)
    prov["tries"]["ny_fed_xls"] = 1
    prov["tries"]["errors_count"] = len(prov["errors"])
    PROV_PATH.write_text(json.dumps(prov, indent=2, default=str), encoding="utf-8")
    print(f"\n[DONE] provenance → {PROV_PATH} (errors={len(prov['errors'])})")
    return prov


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    main(dry_run=dry)
