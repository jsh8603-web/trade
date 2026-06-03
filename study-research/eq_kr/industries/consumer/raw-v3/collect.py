# -*- coding: utf-8 -*-
"""collect.py — consumer(소비재) §M v3 universe + 패널 수집.

frame v3 §M.7 + batch-role. battery 미러 + ★consumer 화이트리스트(financial 교훈).

★consumer universe 결함: 화장품(아모레/LG생건/코스맥스)=「기타 화학제품 제조업」,
  주요식품(CJ제일제당/오리온/농심)=「기타 식품 제조업」 → 핵심 소비재가 화학/식품제조에 묻힘.
  Industry 키워드 + ★이름 화이트리스트(화장품/식품 대표) 병용 필요.

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

# 핵심 소비재 Industry (식품/음료/담배/의복/유통/소매)
CORE_IND = ("식료품|기타 식품|음료|비알코올|알코올음료|담배 제조|의복|봉제|편조|섬유, 의복|신발|"
            "종합 소매|소매업|상품 종합 도매|음·식료품|생활용품 도매|유지 및 낙농|곡물가공|"
            "도축, 육류|수산물|과실|차 및 커피")
# ★이름 화이트리스트 (화학/제조에 묻힌 대표 소비재 — 화장품/식품/생활용품)
NAME_WHITELIST = ["아모레퍼시픽", "LG생활건강", "아모레G", "코스맥스", "한국콜마", "콜마비앤에이치",
                  "CJ제일제당", "오리온", "농심", "오뚜기", "롯데웰푸드", "삼양식품", "대상", "동원F&B",
                  "풀무원", "사조대림", "하림", "롯데칠성", "하이트진로", "무학", "보령메디앙스",
                  "애경산업", "코웨이", "락앤락", "쿠쿠홀딩스", "신세계", "이마트", "BGF리테일", "GS리테일"]
# 명백 비소비재 제외 (소재/B2B 도매)
NAME_EXCLUDE = ["홀딩스", "지주"]  # 단 일부 소비재 지주는 개별 점검 — 보수적으로 순수 소비재 우선


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

    ind_match = m["Industry"].fillna("").str.contains(CORE_IND)
    name_match = m["Name"].isin(NAME_WHITELIST)
    is_common = m["Code"].str.match(r"^\d{5}0$")
    mask = (ind_match | name_match) & is_common

    cons = m[mask].copy().sort_values("Marcap", ascending=False)
    cons["pass_floor"] = (cons["Marcap"] >= MARCAP_FLOOR) & (cons["Amount"] >= ADV_FLOOR)

    def subcl(r):
        n, ind = r["Name"], str(r["Industry"])
        if any(k in n for k in ["아모레", "LG생활", "코스맥스", "한국콜마", "콜마", "애경"]) or "화장품" in ind:
            return "cosmetics"
        if any(k in n for k in ["신세계", "이마트", "롯데쇼핑", "현대백화점", "BGF", "GS리테일", "롯데하이마트"]) or "소매" in ind:
            return "retail"
        if any(k in n for k in ["롯데칠성", "하이트", "진로", "무학"]) or "음료" in ind:
            return "beverage"
        if "의복" in ind or "봉제" in ind or any(k in n for k in ["F&F", "한섬", "영원무역"]):
            return "apparel"
        return "food"
    cons["subcl"] = cons.apply(subcl, axis=1)
    cons.to_parquet(cache)
    return cons


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
