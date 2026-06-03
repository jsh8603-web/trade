# -*- coding: utf-8 -*-
"""collect.py — financial(금융) §M v3 universe + 횡단면 패널 수집.

frame v3 §M.7 + .dispatch-v3-batch-role. battery collect.py 미러 + financial 정밀 필터.

★financial universe 결함 (pilot 학습): KRX 표준산업분류 "기타 금융업"에 일반 지주사(CJ/GS/HD현대)가
  금융지주(KB/신한/하나)와 함께 분류됨 → Industry 매칭만으론 노이즈. 정밀 필터 = 은행/보험/증권/카드
  + 금융지주(이름 패턴) 명시 포함, 일반 지주사 제외. 우선주 제거.

산출: data/{universe, prices, amount}.parquet
"""
from __future__ import annotations
import sys, io, os, time
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

START, END = "2019-01-01", "2026-05-29"
MARCAP_FLOOR = 3e11
ADV_FLOOR = 3e9

# 명시 금융지주 (일반 지주사 노이즈 제거 — 이름 화이트리스트)
FIN_HOLDING = ["KB금융", "신한지주", "하나금융지주", "우리금융지주", "메리츠금융지주",
               "BNK금융지주", "JB금융지주", "iM금융지주", "DGB금융지주", "한국금융지주",
               "미래에셋", "키움", "카카오뱅크", "케이뱅크", "기업은행"]


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

    # 순수 금융 Industry (지주사 노이즈 없음)
    pure_ind = m["Industry"].fillna("").str.contains("은행 및 저축기관|보험업|재 보험업|보험 및 연금|신탁업 및 집합투자")
    # 증권사 (이름)
    sec = m["Name"].str.contains("증권")
    # 은행 (이름)
    bank = m["Name"].str.contains("은행|뱅크")
    # 카드/캐피탈
    card = m["Name"].str.contains("카드|캐피탈")
    # 명시 금융지주
    holding = m["Name"].isin(FIN_HOLDING) | m["Name"].str.contains("금융지주")
    mask = pure_ind | sec | bank | card | holding

    # ★우선주 제거: 보통주만 (코드 끝 '0'). 우선주 = 코드 5번째 자리 ≠ 0 (예: 005935 우선주)
    is_common = m["Code"].str.match(r"^\d{5}0$")
    mask = mask & is_common

    fin = m[mask].copy().sort_values("Marcap", ascending=False)
    fin["pass_floor"] = (fin["Marcap"] >= MARCAP_FLOOR) & (fin["Amount"] >= ADV_FLOOR)

    def subcl(n):
        if "증권" in n: return "securities"
        if any(k in n for k in ["생명", "화재", "손해", "해상", "보험", "코리안리"]): return "insurance"
        if any(k in n for k in ["은행", "금융지주", "뱅크", "금융"]): return "bank"
        if any(k in n for k in ["카드", "캐피탈"]): return "credit"
        return "other_fin"
    fin["subcl"] = fin["Name"].apply(subcl)
    fin.to_parquet(cache)
    return fin


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
    print(passed[["Code", "Name", "Market", "Marcap", "subcl"]].head(40).to_string(index=False))

    codes = passed["Code"].tolist()
    print(f"\n[2/2] prices ({len(codes)} codes) ...")
    px, amt = collect_prices(codes)
    print(f"  price panel: {px.shape}  {px.index.min().date()}~{px.index.max().date()}")
    print("DONE")
