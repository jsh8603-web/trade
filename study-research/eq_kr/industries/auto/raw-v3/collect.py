# -*- coding: utf-8 -*-
"""collect.py — auto(자동차) §M v3 universe + 횡단면 패널 수집. battery 미러.

frame v3 §M.7 exposure card 계약 데이터 수집 단계.
★universe 화이트리스트 정밀화 (supervisor 지시): FDR 자동차 키워드 매칭 → Industry 기반 화이트리스트
  (완성차/부품/타이어 제조업만) AND 명시 블랙리스트(보험·해운·2차전지·철강·방산·금융 혼입 배제).
  키워드만 쓰면 자동차보험(DB손보)·해운(HMM)·2차전지(LG엔솔)·유통(SK네트웍스)·음료(롯데칠성) 등 부수매칭 오염.

산출:
- data/universe.parquet        — auto universe (Industry 화이트리스트, 시총·ADV floor)  [현재 스냅샷 = PIT 한계]
- data/prices.parquet          — universe 종목 일별 종가 패널 (pykrx ohlcv loop)
- data/amount.parquet          — 일별 거래대금 (ADV 유동성 티어용)
- data/dart_filings.json       — DART 보고서 제출일 (PIT 보고지연 stamp)

★sub-cluster: 완성차(현대차/기아/KG모빌리티) / 부품(현대모비스/HL만도/한온시스템/현대위아/에스엘 등) / 타이어(한국타이어/금호타이어).
"""
from __future__ import annotations
import sys, io, os, json, time
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

ENV = Path("D:/projects/Inv/.env")
if ENV.exists():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

START = "2019-01-01"
END = "2026-05-29"

MARCAP_FLOOR = 3e11   # 3000억원
ADV_FLOOR = 3e9       # 30억원/일

AUTO_KW = ["자동차", "완성차", "자동차부품", "타이어", "자동차용", "차량부품", "파워트레인", "변속기", "내연기관"]

# ★Industry 화이트리스트 (진짜 자동차 = 완성차/부품/타이어 제조업)
INDUSTRY_WHITELIST = [
    "자동차용 엔진 및 자동차 제조업",   # 완성차 (현대차/기아/KG모빌리티)
    "자동차 신품 부품 제조업",          # 부품 (현대모비스/HL만도/현대위아/에스엘 등)
    "자동차 재제조 부품 제조업",
    "고무제품 제조업",                  # 타이어 (한국타이어/금호타이어) — 단 타이어 키워드 AND 조건
]
# ★명시 블랙리스트 (키워드 부수매칭 오염 배제): 보험/해운/금융/2차전지/철강/방산/음료/유통/통신
BLACKLIST_CODE = {
    "373220",  # LG에너지솔루션 (2차전지)
    "011200",  # HMM (해운)
    "086280",  # 현대글로비스 (물류) — 자동차 운송이나 제조업 아님 → 경계, 배제(부품/완성차 아님)
    "005830",  # DB손해보험 (보험)
    "004800",  # 효성 (기타금융/화학)
    "001450",  # 현대해상 (보험)
    "001740",  # SK네트웍스 (유통)
    "007340",  # DN오토모티브 (자동차밧데리 = 2차전지 Industry)
    "001430",  # 세아베스틸지주 (철강)
    "077970",  # STX엔진 (선박/일반기계 엔진)
    "065350",  # 신성델타테크 (가전부품)
    "005300",  # 롯데칠성 (음료, 정비 부수)
    "298050",  # HS효성첨단소재 (화학섬유 타이어코드 = 소재)
    "004490",  # 세방전지 (축전지 = 2차전지)
    "010820",  # 퍼스텍 (방산)
    "107640",  # 한중엔시에스 (ESS)
    "049070",  # 인탑스 (통신/가전부품)
    "448900",  # 한국피아이엠 (분말야금 — IT부품 겸업, 경계 배제)
}


def build_universe() -> pd.DataFrame:
    """FDR 자동차 키워드 → Industry 화이트리스트 AND 블랙리스트 배제 + 시총·ADV floor."""
    cache = DATA / "universe.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import FinanceDataReader as fdr
    desc = fdr.StockListing("KRX-DESC")[["Code", "Name", "Market", "Sector", "Industry", "Products"]]
    kospi = fdr.StockListing("KOSPI")[["Code", "Marcap", "Amount"]]
    kosdaq = fdr.StockListing("KOSDAQ")[["Code", "Marcap", "Amount"]]
    mc = pd.concat([kospi, kosdaq], ignore_index=True)
    m = desc.merge(mc, on="Code", how="left")
    pat = "|".join(AUTO_KW)
    kw_mask = (
        m["Sector"].fillna("").str.contains(pat)
        | m["Industry"].fillna("").str.contains(pat)
        | m["Products"].fillna("").str.contains(pat)
    )
    # Industry 화이트리스트: 완성차/부품 제조업 OR (고무제품 AND 타이어 Products)
    ind = m["Industry"].fillna("")
    prod = m["Products"].fillna("")
    wl_mask = ind.isin(INDUSTRY_WHITELIST[:3]) | (ind.str.contains("고무제품") & prod.str.contains("타이어"))
    auto = m[kw_mask & wl_mask].copy()
    # 블랙리스트 배제
    auto = auto[~auto["Code"].isin(BLACKLIST_CODE)]
    auto = auto.sort_values("Marcap", ascending=False)
    auto["pass_floor"] = (auto["Marcap"] >= MARCAP_FLOOR) & (auto["Amount"] >= ADV_FLOOR)
    auto.to_parquet(cache)
    return auto


def collect_prices(codes: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    cache_px = DATA / "prices.parquet"
    cache_amt = DATA / "amount.parquet"
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
            closes[c] = o["종가"]
            amts[c] = o["종가"] * o["거래량"]
            print(f"  [{i}] {c} ok rows={len(o)}")
        except Exception as ex:
            print(f"  [{i}] {c} FAIL {repr(ex)[:60]}")
        time.sleep(0.3)
    px = pd.DataFrame(closes).sort_index()
    amt = pd.DataFrame(amts).sort_index()
    px.index = pd.to_datetime(px.index)
    amt.index = pd.to_datetime(amt.index)
    px.to_parquet(cache_px)
    amt.to_parquet(cache_amt)
    return px, amt


def collect_dart_filings(codes: list[str]) -> dict:
    cache = DATA / "dart_filings.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    import requests
    key = os.environ.get("DART_API_KEY", "")
    if not key:
        print("  DART_API_KEY MISSING — skip"); return {}
    out = {}
    for yr in range(2020, 2026):
        try:
            r = requests.get("https://opendart.fss.or.kr/api/list.json",
                             params=dict(crtfc_key=key, bgn_de=f"{yr}0101", end_de=f"{yr}1231",
                                         pblntf_ty="A", page_count=100, page_no=1), timeout=30)
            j = r.json()
            if j.get("status") == "000":
                out[str(yr)] = {"total_filings": int(j.get("total_count", 0)), "sample": j.get("list", [])[:3]}
                print(f"  DART {yr}: total={j.get('total_count')}")
        except Exception as ex:
            print(f"  DART {yr} FAIL {repr(ex)[:60]}")
        time.sleep(0.5)
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    print("[1/3] universe ...")
    uni = build_universe()
    passed = uni[uni["pass_floor"]]
    print(f"  total matched(화이트리스트)={len(uni)} / floor-passed={len(passed)}")
    print(passed[["Code", "Name", "Market", "Industry", "Marcap"]].head(50).to_string(index=False))

    codes = passed["Code"].tolist()
    print(f"\n[2/3] prices ({len(codes)} codes) ...")
    px, amt = collect_prices(codes)
    print(f"  price panel: {px.shape}  date {px.index.min().date()}~{px.index.max().date()}")

    print("\n[3/3] DART filings (보고지연 stamp) ...")
    dart = collect_dart_filings(codes)
    print(f"  dart years: {list(dart.keys())}")
    print("\nDONE")
