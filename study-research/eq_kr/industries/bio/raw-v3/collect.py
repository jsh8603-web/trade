# -*- coding: utf-8 -*-
"""collect.py — bio(바이오) §M v3 universe + 패널 수집.

frame v3 §M.7 + batch-role. battery 미러 + bio 정밀 필터.

★bio = event_driven: 신약개발 바이오(HLB/펩트론/에이비엘바이오 등) = 적자/임상단계 → PER 무의미.
  멀티플(PBR/PER) 부적합 가설 검증 = 측정 자체가 목적. 의료기기 제외(신약/제약/바이오시밀러/CMO 중심).

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
MARCAP_FLOOR, ADV_FLOOR = 3e11, 3e9

# bio 핵심 Industry (의약품/기초의약물질/의약관련용품 = 신약·제약·바이오시밀러·CMO). 의료기기 제외.
BIO_IND = "의약품 제조업|기초 의약물질|의료용품 및 기타 의약"


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
    mask = m["Industry"].fillna("").str.contains(BIO_IND) & m["Code"].str.match(r"^\d{5}0$")
    bio = m[mask].copy().sort_values("Marcap", ascending=False)
    bio["pass_floor"] = (bio["Marcap"] >= MARCAP_FLOOR) & (bio["Amount"] >= ADV_FLOOR)

    def subcl(n):
        if any(k in n for k in ["삼성바이오", "셀트리온", "에스티팜", "바이오로직스"]): return "biosimilar_cmo"
        if any(k in n for k in ["테라퓨틱", "바이오파마", "에이비엘", "펩트론", "오스코텍", "앱클론", "오름"]): return "novel_drug"
        return "pharma"  # 전통 제약 (유한/한미/녹십자/대웅/종근당)
    bio["subcl"] = bio["Name"].apply(subcl)
    bio.to_parquet(cache)
    return bio


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
    print(f"  sub-cluster: {passed['subcl'].value_counts().to_dict()}")
    print(passed[["Code", "Name", "Marcap", "subcl"]].head(45).to_string(index=False))
    codes = passed["Code"].tolist()
    print(f"\n[2/2] prices ({len(codes)} codes) ...")
    px, amt = collect_prices(codes)
    print(f"  price panel: {px.shape}  {px.index.min().date()}~{px.index.max().date()}")
    print("DONE")
