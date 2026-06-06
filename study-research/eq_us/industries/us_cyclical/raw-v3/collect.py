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


# ── EDGAR concept 매핑 (key → [us-gaap concept 후보들], unit) ──
# ★다중 후보 = sector별 태그 파편화 fallback (S1 실측: GrossProfit/Revenues 일부 sector 결측).
#   각 (ticker, concept_key) 당 첫 가용(200+units) 후보 채택 + src_concept 박제(추적성 C축).
EDGAR_CONCEPTS = [
    ("equity",       "USD",    ["StockholdersEquity"]),
    ("net_income",   "USD",    ["NetIncomeLoss"]),
    # ★shares: us-gaap 우선 → dei 네임스페이스 fallback (V/TXN/COP 등 13종 dei 에만 존재)
    ("shares",       "shares", ["CommonStockSharesOutstanding",
                                 "WeightedAverageNumberOfSharesOutstandingBasic",
                                 "dei:EntityCommonStockSharesOutstanding"]),
    # ── ★신규 (S1 채택 신호) ──
    ("assets",       "USD",    ["Assets"]),                      # asset_growth (전 universe 가용)
    ("revenues",     "USD",    ["Revenues",
                                 "RevenueFromContractWithCustomerExcludingAssessedTax",
                                 "RevenueFromContractWithCustomerIncludingAssessedTax",
                                 "SalesRevenueNet"]),            # sales_yield
    ("gross_profit", "USD",    ["GrossProfit"]),                 # gross_profitability (직접)
    ("cogs",         "USD",    ["CostOfRevenue",
                                 "CostOfGoodsAndServicesSold",
                                 "CostOfGoodsSold"]),            # GP fallback = Revenues - COGS
    # ── ev_ebitda 보조 ──
    ("op_income",    "USD",    ["OperatingIncomeLoss"]),
    ("dep_amort",    "USD",    ["DepreciationDepletionAndAmortization",
                                 "DepreciationAmortizationAndAccretionNet",
                                 "DepreciationAndAmortization"]),
    ("lt_debt",      "USD",    ["LongTermDebtNoncurrent", "LongTermDebt"]),
    ("st_debt",      "USD",    ["LongTermDebtCurrent", "ShortTermBorrowings",
                                 "DebtCurrent"]),
    ("cash",         "USD",    ["CashAndCashEquivalentsAtCarryingValue",
                                 "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"]),
]


def collect_edgar(tickers, cik_map) -> pd.DataFrame:
    """EDGAR companyconcept → 12 concept_key (PIT filed date). ★incremental save (foreground).
    filed date = PIT timestamp(lookahead 회피). ★cache 존재 시 누락 concept_key 만 추가 fetch (idempotent).
    각 concept_key = 후보 us-gaap 태그 순회, 첫 가용 채택 + src_concept 박제(C축 추적성)."""
    import requests
    cache = DATA / "edgar_fundamentals.parquet"
    existing = pd.read_parquet(cache) if cache.exists() else pd.DataFrame()
    have_keys = set(existing["concept"].unique()) if len(existing) else set()
    want = [c for c in EDGAR_CONCEPTS if c[0] not in have_keys]
    if not want:
        print(f"  edgar cache complete ({len(have_keys)} concept keys); skip")
        return existing
    print(f"  edgar: {sorted(have_keys)} present, fetching {len(want)} new: {[w[0] for w in want]}")

    def _flush(rows):
        merged = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True) if len(existing) else pd.DataFrame(rows)
        if "src_concept" not in merged.columns:
            merged["src_concept"] = pd.NA
        merged.to_parquet(cache)
        return merged

    rows = []
    for i, t in enumerate(tickers):
        cik = cik_map.get(t)
        if not cik:
            print(f"  [{i}] {t} no CIK"); continue
        for key, unit, candidates in want:
            for concept in candidates:
                # ★네임스페이스: "dei:X" → dei, 아니면 us-gaap
                ns, cc = (concept.split(":", 1) if ":" in concept else ("us-gaap", concept))
                try:
                    r = requests.get(
                        f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{ns}/{cc}.json",
                        headers=EDGAR_HDR, timeout=30)
                    time.sleep(0.12)  # EDGAR 10 req/s limit
                    if r.status_code == 200:
                        units = r.json().get("units", {}).get(unit, [])
                        if units:
                            for u in units:
                                rows.append(dict(ticker=t, concept=key, end=u.get("end"),
                                                 val=u.get("val"), filed=u.get("filed"),
                                                 form=u.get("form"), fp=u.get("fp"),
                                                 src_concept=concept))
                            break  # 첫 가용 후보 채택 (fallback 순서)
                except Exception as e:
                    print(f"    {t} {concept} FAIL {repr(e)[:40]}")
        print(f"  [{i}] {t} edgar done (cum new rows {len(rows)})")
        if (i + 1) % 10 == 0:
            _flush(rows); print(f"    ...incremental save at {i+1}")
    return _flush(rows)


def _read_fred(fred_id):
    """FRED CSV(기존 재사용) → 단일 시리즈. 없으면 None."""
    f = FRED_DIR / f"{fred_id}.csv"
    if not f.exists():
        return None
    s = pd.read_csv(f)
    datecol = [c for c in s.columns if c.upper() in ("DATE", "OBSERVATION_DATE")][0]
    valcol = [c for c in s.columns if c != datecol][0]
    return pd.Series(pd.to_numeric(s[valcol], errors="coerce").values,
                     index=pd.to_datetime(s[datecol]))


def load_macro() -> pd.DataFrame:
    """FRED CSV(기존 재사용) + yfinance DXY. HY OAS/DGS10/VIX/dollar + ★Baa-Aaa 장기 credit regime proxy.
    ★Baa-Aaa = Fama-French(1989) default spread, FRED BAA/AAA 월별 1919~ (HY OAS 37mo 제약 대체, ρ>0.85)."""
    cache = DATA / "macro.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    out = {}
    for fred_id, col in [("BAMLH0A0HYM2", "hy_oas"), ("DGS10", "rate10y"), ("VIXCLS", "vix")]:
        ser = _read_fred(fred_id)
        if ser is not None:
            out[col] = ser
    # ★Baa-Aaa spread (장기 credit regime proxy)
    baa, aaa = _read_fred("BAA"), _read_fred("AAA")
    if baa is not None and aaa is not None:
        out["baa_aaa"] = (baa - aaa).dropna()
        print(f"  baa_aaa: {out['baa_aaa'].first_valid_index().date()}~{out['baa_aaa'].last_valid_index().date()} n={out['baa_aaa'].notna().sum()}")
    else:
        print("  ★baa_aaa 미생성 — FRED BAA/AAA CSV 부재")
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
