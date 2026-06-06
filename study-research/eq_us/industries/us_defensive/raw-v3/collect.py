# -*- coding: utf-8 -*-
"""collect.py — us_defensive sleeve §M v3 universe + 가격 + EDGAR 펀더멘털 수집 (★재작업).

frame v3 §M.7 + .dispatch-us-sleeve-role. ★미국 = yfinance(가격) + EDGAR XBRL(valuation PIT) + FRED(거시).
★us_cyclical collect.py 미러 + ★defensive 신규 concept(payout 3 tag + CFO + capex).
★role 지시: foreground 동기 + incremental save (한국 DART background 미유지 교훈). EDGAR rate limit(10 req/s) sleep 0.12.

universe = XLP/XLU/XLV/XLC-mature 4 sub-sector 대표 종목 (기존 universe.json 재사용).
★survivorship-biased 명시(현재 holdings = 생존 종목, 상폐 누락 = collector_plan high).

★기존 자산 재사용/확장:
  - data/prices.parquet (가격, 기존 collect.py 생성, 2010~ 48종) → 재사용
  - data/universe.json (4 sub-sector) → parquet 변환(subcl 컬럼 = measure.py secmap)
  - data/edgar_fundamentals.parquet (기존 3 concept) → 12+payout concept 확장(idempotent)
  - data/macro.parquet (신규 생성: FRED + DXY)
산출: data/{universe.parquet, prices.parquet, edgar_fundamentals.parquet(확장), macro.parquet}
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
FRED_DIR = Path("D:/projects/Inv/study-research/eq_us_defensive/raw/fred")  # 기존 FRED CSV
CYC_DATA = Path("D:/projects/Inv/study-research/eq_us/industries/us_cyclical/raw-v3/data")  # cik_map 재사용
CYC_FRED = Path("D:/projects/Inv/study-research/eq_us_cyclical/raw/fred")

START, END = "2010-01-01", "2026-05-29"
EDGAR_HDR = {"User-Agent": "inv-research research@example.com"}


def build_universe() -> pd.DataFrame:
    """기존 universe.json(49종 4 sub-sector) → parquet (subcl = staples/utilities/healthcare/comm_mature)."""
    cache = DATA / "universe.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    uni = json.loads((DATA / "universe.json").read_text(encoding="utf-8"))
    rows = [dict(ticker=t, subcl=sub) for t, sub in uni["tickers"].items()]
    df = pd.DataFrame(rows)
    df.to_parquet(cache)
    return df


def get_cik_map() -> dict:
    cache = DATA / "cik_map.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    if (CYC_DATA / "cik_map.json").exists():
        m = json.loads((CYC_DATA / "cik_map.json").read_text(encoding="utf-8"))
        cache.write_text(json.dumps(m), encoding="utf-8")
        return m
    import requests
    r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=EDGAR_HDR, timeout=30)
    tmap = {v["ticker"].replace(".", "-"): str(v["cik_str"]).zfill(10) for v in r.json().values()}
    cache.write_text(json.dumps(tmap), encoding="utf-8")
    return tmap


def collect_prices(tickers) -> pd.DataFrame:
    """기존 prices.parquet 재사용 (2010~, 48종)."""
    cache = DATA / "prices.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import yfinance as yf
    closes = {}
    for i, t in enumerate(tickers):
        try:
            h = yf.download(t, start=START, end=END, progress=False, auto_adjust=True)["Close"].squeeze()
            if len(h):
                closes[t] = h; print(f"  [{i}] {t} ok {len(h)} rows")
        except Exception as e:
            print(f"  [{i}] {t} FAIL {repr(e)[:40]}")
        time.sleep(0.2)
    px = pd.DataFrame(closes); px.index = pd.to_datetime(px.index); px = px.sort_index()
    px.to_parquet(cache)
    return px


# ── EDGAR concept 매핑 (key → [후보 태그], unit). ★probe 실측 반영 (research-log) ──
EDGAR_CONCEPTS = [
    ("equity",       "USD",    ["StockholdersEquity"]),
    ("net_income",   "USD",    ["NetIncomeLoss"]),
    # ★shares: us-gaap → dei fallback (probe: dei:EntityCommonStockSharesOutstanding 전종목, 현 30/48 보강)
    ("shares",       "shares", ["CommonStockSharesOutstanding",
                                 "WeightedAverageNumberOfSharesOutstandingBasic",
                                 "dei:EntityCommonStockSharesOutstanding"]),
    ("assets",       "USD",    ["Assets"]),
    ("revenues",     "USD",    ["Revenues",
                                 "RevenueFromContractWithCustomerExcludingAssessedTax",
                                 "RevenueFromContractWithCustomerIncludingAssessedTax",
                                 "SalesRevenueNet"]),
    ("gross_profit", "USD",    ["GrossProfit"]),                 # ★probe: JNJ만 직접, 나머지 fallback
    ("cogs",         "USD",    ["CostOfGoodsAndServicesSold",
                                 "CostOfRevenue",
                                 "CostOfGoodsSold"]),            # ★utilities 404 = gross_prof 부재
    ("op_income",    "USD",    ["OperatingIncomeLoss"]),
    ("dep_amort",    "USD",    ["DepreciationDepletionAndAmortization",
                                 "DepreciationAmortizationAndAccretionNet",
                                 "DepreciationAndAmortization"]),  # ★probe: NEE/VZ 404 → fallback
    ("lt_debt",      "USD",    ["LongTermDebtNoncurrent", "LongTermDebt"]),
    ("st_debt",      "USD",    ["LongTermDebtCurrent", "ShortTermBorrowings", "DebtCurrent"]),
    ("cash",         "USD",    ["CashAndCashEquivalentsAtCarryingValue",
                                 "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"]),
    # ── ★defensive 신규: payout/shareholder yield (Boudoukh 2007) + CFO/capex (accruals/fcf) ──
    ("cfo",          "USD",    ["NetCashProvidedByUsedInOperatingActivities",
                                 "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"]),
    ("dividends",    "USD",    ["PaymentsOfDividends",            # ★probe: PG/NEE/VZ OK
                                 "PaymentsOfDividendsCommonStock",
                                 "Dividends",
                                 "DividendsCommonStockCash"]),    # ★JNJ 추가 탐색
    ("repurchase",   "USD",    ["PaymentsForRepurchaseOfCommonStock",  # ★probe: 전종목 OK
                                 "PaymentsForRepurchaseOfEquity"]),
    ("issuance",     "USD",    ["ProceedsFromIssuanceOfCommonStock",   # ★일부만 (없으면 0)
                                 "ProceedsFromStockOptionsExercised"]),
    ("capex",        "USD",    ["PaymentsToAcquirePropertyPlantAndEquipment",
                                 "PaymentsToAcquireProductiveAssets"]),  # fcf = cfo - capex
]


def collect_edgar(tickers, cik_map) -> pd.DataFrame:
    """EDGAR companyconcept → concept_key (PIT filed date). ★incremental + idempotent (누락 concept만 fetch).
    ★shares 커버 부족(기존 30/48) 시 dei fallback 으로 재수집."""
    import requests
    cache = DATA / "edgar_fundamentals.parquet"
    existing = pd.read_parquet(cache) if cache.exists() else pd.DataFrame()
    have_keys = set(existing["concept"].unique()) if len(existing) else set()
    # ★shares 보강: 기존 커버 < 90% → 재수집(dei fallback)
    if "shares" in have_keys and len(existing):
        sh_cov = existing[existing["concept"] == "shares"]["ticker"].nunique()
        if sh_cov < len(tickers) * 0.9:
            print(f"  shares coverage {sh_cov}/{len(tickers)} < 90% → 재수집(dei fallback)")
            existing = existing[existing["concept"] != "shares"].reset_index(drop=True)
            have_keys = set(existing["concept"].unique()) if len(existing) else set()
    want = [c for c in EDGAR_CONCEPTS if c[0] not in have_keys]
    if not want:
        print(f"  edgar cache complete ({len(have_keys)} concept keys); skip")
        return existing
    print(f"  edgar: {sorted(have_keys)} present, fetching {len(want)}: {[w[0] for w in want]}")

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
                ns, cc = (concept.split(":", 1) if ":" in concept else ("us-gaap", concept))
                try:
                    r = requests.get(
                        f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{ns}/{cc}.json",
                        headers=EDGAR_HDR, timeout=30)
                    time.sleep(0.12)
                    if r.status_code == 200:
                        units = r.json().get("units", {}).get(unit, [])
                        if units:
                            for u in units:
                                rows.append(dict(ticker=t, concept=key, end=u.get("end"),
                                                 val=u.get("val"), filed=u.get("filed"),
                                                 form=u.get("form"), fp=u.get("fp"), src_concept=concept))
                            break
                except Exception as e:
                    print(f"    {t} {concept} FAIL {repr(e)[:40]}")
        print(f"  [{i}] {t} edgar done (cum new rows {len(rows)})")
        if (i + 1) % 10 == 0:
            _flush(rows); print(f"    ...incremental save at {i+1}")
    return _flush(rows)


def _read_fred(fred_id):
    f = FRED_DIR / f"{fred_id}.csv"
    if not f.exists():
        f2 = CYC_FRED / f"{fred_id}.csv"
        f = f2 if f2.exists() else f
    if not f.exists():
        return None
    s = pd.read_csv(f)
    datecol = [c for c in s.columns if c.upper() in ("DATE", "OBSERVATION_DATE")][0]
    valcol = [c for c in s.columns if c != datecol][0]
    return pd.Series(pd.to_numeric(s[valcol], errors="coerce").values, index=pd.to_datetime(s[datecol]))


def load_macro() -> pd.DataFrame:
    """FRED CSV + yfinance DXY. HY OAS/DGS10/DFII10(★real rate, defensive 듀레이션)/VIX/dollar + ★Baa-Aaa(family_2)."""
    cache = DATA / "macro.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    out = {}
    for fred_id, col in [("BAMLH0A0HYM2", "hy_oas"), ("DGS10", "rate10y"), ("DFII10", "real_rate"), ("VIXCLS", "vix")]:
        ser = _read_fred(fred_id)
        if ser is not None:
            out[col] = ser
            print(f"  {col}: {ser.first_valid_index()}~{ser.last_valid_index()} n={ser.notna().sum()}")
    baa, aaa = _read_fred("BAA"), _read_fred("AAA")
    if baa is not None and aaa is not None:
        out["baa_aaa"] = (baa - aaa).dropna()
        print(f"  baa_aaa: {out['baa_aaa'].first_valid_index().date()}~{out['baa_aaa'].last_valid_index().date()} n={out['baa_aaa'].notna().sum()}")
    else:
        print("  ★baa_aaa 미생성 — FRED BAA/AAA CSV 부재 (collector_plan)")
    try:
        import yfinance as yf
        dxy = yf.download("DX-Y.NYB", start=START, end=END, progress=False, auto_adjust=True)["Close"].squeeze()
        dxy.index = pd.to_datetime(dxy.index); out["dollar"] = dxy
    except Exception as e:
        print(f"  DXY fail {repr(e)[:40]}")
    df = pd.concat(out, axis=1).sort_index().ffill(limit=5)
    df.to_parquet(cache)
    return df


if __name__ == "__main__":
    print("[1/4] universe ...")
    uni = build_universe()
    print(f"  {len(uni)} tickers, sub-sectors: {uni['subcl'].value_counts().to_dict()}")
    tickers = uni["ticker"].tolist()

    print(f"\n[2/4] prices ({len(tickers)} tickers, 기존 재사용) ...")
    px = collect_prices(tickers)
    print(f"  price panel: {px.shape}  {px.index.min().date()}~{px.index.max().date()}")

    print("\n[3/4] EDGAR fundamentals (PIT filed date, ★12+payout concept 확장) ...")
    cik_map = get_cik_map()
    edgar = collect_edgar(tickers, cik_map)
    print(f"  edgar rows: {len(edgar)}, tickers covered: {edgar['ticker'].nunique() if len(edgar) else 0}")
    if len(edgar):
        print("  per-concept coverage:")
        for c in sorted(edgar["concept"].unique()):
            print(f"    {c:13} {edgar[edgar['concept']==c]['ticker'].nunique()}/{len(tickers)}")

    print("\n[4/4] macro (FRED + DXY) ...")
    macro = load_macro()
    print(f"  macro: {macro.shape}, cols: {list(macro.columns)}")
    print("DONE")
