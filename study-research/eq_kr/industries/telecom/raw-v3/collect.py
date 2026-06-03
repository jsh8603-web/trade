# -*- coding: utf-8 -*-
"""collect.py — telecom(통신) §M v3 universe + 패널 수집.

★telecom = universe 협소 경계 케이스 (supervisor 경고):
  - 통신서비스(전기통신업) = SKT/KT/LGU+ 3종 = cross-sectional 절대 불가(n=3 종목).
  - 통신서비스+장비 = 13종(서비스 3 + 장비 11). 단 archetype 혼재(service=asset_stable / equipment=cyclical 5G).
  - ★삼성전자/LG전자 = "통신 및 방송 장비" 오분류 → 제외(telecom 아님).
  → cross-sectional 측정은 13종으로 시도하되, service sub(3종) = INSUFFICIENT, 장비 포함 혼재 = 정직 명시.

산출: data/{universe, prices, amount}.parquet
"""
from __future__ import annotations
import sys, io, time
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

START, END = "2019-01-01", "2026-05-29"
MARCAP_FLOOR, ADV_FLOOR = 3e11, 1e9   # ★ADV floor 10억 완화 (장비주 소형 — 협소 universe 보강)

EXCLUDE = ["삼성전자", "LG전자"]  # 오분류 대형주 제외 (telecom 아님)


def build_universe() -> pd.DataFrame:
    cache = DATA / "universe.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import FinanceDataReader as fdr
    desc = fdr.StockListing("KRX-DESC")[["Code", "Name", "Market", "Industry", "Products"]]
    kospi = fdr.StockListing("KOSPI")[["Code", "Marcap", "Amount"]]
    kosdaq = fdr.StockListing("KOSDAQ")[["Code", "Marcap", "Amount"]]
    mc = pd.concat([kospi, kosdaq], ignore_index=True)
    m = desc.merge(mc, on="Code", how="left")
    ind = m["Industry"].fillna("").str.contains("전기 통신업|통신 및 방송 장비")
    is_common = m["Code"].str.match(r"^\d{5}0$")
    mask = ind & is_common & ~m["Name"].isin(EXCLUDE)
    tel = m[mask].copy()
    tel["pass_floor"] = (tel["Marcap"] >= MARCAP_FLOOR) & (tel["Amount"] >= ADV_FLOOR)
    tel["subcl"] = tel["Name"].apply(
        lambda n: "service" if any(k in n for k in ["텔레콤", "KT", "유플러스"]) else "equipment")
    tel = tel.sort_values("Marcap", ascending=False)
    tel.to_parquet(cache)
    return tel


def collect_prices(codes):
    cache_px, cache_amt = DATA / "prices.parquet", DATA / "amount.parquet"
    if cache_px.exists() and cache_amt.exists():
        return pd.read_parquet(cache_px), pd.read_parquet(cache_amt)
    from pykrx import stock as pks
    s, e = START.replace("-", ""), END.replace("-", "")
    closes, amts = {}, {}
    for i, c in enumerate(codes):
        try:
            o = pks.get_market_ohlcv(s, e, c)
            if len(o) == 0:
                print(f"  [{i}] {c} EMPTY"); continue
            closes[c] = o["종가"]; amts[c] = o["종가"] * o["거래량"]
            print(f"  [{i}] {c} ok rows={len(o)}")
        except Exception as ex:
            print(f"  [{i}] {c} FAIL {repr(ex)[:50]}")
        time.sleep(0.3)
    px = pd.DataFrame(closes).sort_index(); amt = pd.DataFrame(amts).sort_index()
    px.index = pd.to_datetime(px.index); amt.index = pd.to_datetime(amt.index)
    px.to_parquet(cache_px); amt.to_parquet(cache_amt)
    return px, amt


if __name__ == "__main__":
    print("[1/2] universe ...")
    uni = build_universe()
    passed = uni[uni["pass_floor"]]
    print(f"  matched={len(uni)} / floor-passed={len(passed)}")
    print(f"  ★sub-cluster: {passed['subcl'].value_counts().to_dict()} (service=asset_stable / equipment=cyclical 혼재)")
    print(passed[["Code", "Name", "Marcap", "subcl"]].to_string(index=False))
    codes = passed["Code"].tolist()
    print(f"\n[2/2] prices ({len(codes)} codes) ...")
    px, amt = collect_prices(codes)
    print(f"  price panel: {px.shape}  {px.index.min().date()}~{px.index.max().date()}")
    print("DONE")
