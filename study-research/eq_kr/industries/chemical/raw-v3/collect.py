# -*- coding: utf-8 -*-
"""collect.py — chemical (석유화학·정밀화학) universe 확장 + 횡단면 패널 수집.

semiconductor collect.py 미러 (SEMI_KW → 명시 화이트리스트, 나머지 floor/PIT 로직 동일).
화학 = 자산집약 장치산업(석유화학 NCC/정밀화학) → capex 일반화 가설 우선 검증 대상.

★universe 화이트리스트 (frame M.11 교훈 — KRX FDR 키워드 부정확):
  KSIC Industry "기초/기타 화학물질" 키워드 매칭 시 화장품(아모레/LG생활건강/한국콜마)·
  반도체소재(동진쎄미켐/솔브레인/레이크/티이엠씨)·2차전지소재(코스모신소재/SKC 동박)·정유(S-Oil/SK이노)
  대량 혼입 → 별 archetype/별 capsule 소관이라 ★제외. 순수 석유화학(commodity) + 정밀/스페셜티 화학만.
  - 석유화학 commodity (NCC/유화): LG화학·롯데케미칼·한화솔루션·금호석유화학·대한유화·이수화학
  - 정밀/스페셜티: 한솔케미칼·이수스페셜티케미컬·후성·OCI홀딩스·OCI·롯데정밀화학·휴켐스·애경케미칼·유니드
  - 소재/섬유 화학: 코오롱인더·효성첨단소재·효성화학·국도화학·휴비스·코오롱플라스틱
  - 비료/농약: 남해화학·경농
  ⛔제외: 정유(refining capsule) / 화장품·생활용품(asset_stable 별) / 반도체·디스플레이 소재(semi capsule) /
          2차전지 양극·음극·동박(battery capsule) / 건자재(KCC/LX하우시스) / 지주순수(한화)

산출 (semiconductor 동일):
- data/universe.parquet  — chemical 화이트리스트 universe + 시총·ADV floor
- data/prices.parquet    — 일별 종가 패널
- data/amount.parquet    — 일별 거래대금 (ADV 유동성 티어)
- data/dart_filings.json — DART 제출일 (PIT stamp)

★데이터 제약 (battery/semi pilot 동일): pykrx 시장 스냅샷 API = KRX 인증 차단 빈 응답.
  → valuation 횡단면 = DART fnlttSinglAcntAll PIT 재구성(collect_dart.py). OHLCV loop = 작동.
  → universe = 현재 스냅샷(PIT 멤버십 아님 = 생존편향 한계, collector_plan high).
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

# .env 로드 (DART_API_KEY)
ENV = Path("D:/projects/Inv/.env")
if ENV.exists():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

START = "2019-01-01"
END = "2026-05-29"

# 시총·유동성 floor (battery/semi 와 동일 방향, CPCV 캘리브레이션 대상 §M.6).
# 화학 중형(석유화학 cycle 종목) 포함 위해 약간 완화: 시총 1000억 / ADV 5억.
MARCAP_FLOOR = 1e11   # 1000억원
ADV_FLOOR = 5e8       # 5억원/일

# ★명시 화이트리스트 (석유화학 commodity + 정밀/스페셜티 화학). code: name(검증용 라벨)
CHEM_WHITELIST = {
    # 석유화학 commodity (NCC/유화 — 에틸렌-납사 spread cycle 직접)
    "051910": "LG화학", "011170": "롯데케미칼", "009830": "한화솔루션",
    "011780": "금호석유화학", "006650": "대한유화", "005950": "이수화학",
    # 정밀/스페셜티 화학
    "014680": "한솔케미칼", "457190": "이수스페셜티케미컬", "093370": "후성",
    "010060": "OCI홀딩스", "456040": "OCI", "004000": "롯데정밀화학",
    "069260": "TKG휴켐스", "161000": "애경케미칼", "014830": "유니드",
    # 소재/섬유 화학
    "120110": "코오롱인더", "298050": "HS효성첨단소재", "298000": "효성화학",
    "007690": "국도화학", "079980": "휴비스", "138490": "코오롱플라스틱",
    # 비료/농약
    "025860": "남해화학", "002100": "경농",
}


def build_universe() -> pd.DataFrame:
    """명시 화이트리스트 → chemical universe + 시총·ADV floor."""
    cache = DATA / "universe.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import FinanceDataReader as fdr
    desc = fdr.StockListing("KRX-DESC")[["Code", "Name", "Market", "Sector", "Industry", "Products"]]
    kospi = fdr.StockListing("KOSPI")[["Code", "Marcap", "Amount"]]
    kosdaq = fdr.StockListing("KOSDAQ")[["Code", "Marcap", "Amount"]]
    mc = pd.concat([kospi, kosdaq], ignore_index=True)
    m = desc.merge(mc, on="Code", how="left")
    chem = m[m["Code"].isin(CHEM_WHITELIST.keys())].copy().sort_values("Marcap", ascending=False)
    chem["wl_name"] = chem["Code"].map(CHEM_WHITELIST)
    chem["pass_floor"] = (chem["Marcap"] >= MARCAP_FLOOR) & (chem["Amount"] >= ADV_FLOOR)
    chem.to_parquet(cache)
    return chem


def collect_prices(codes: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """pykrx ohlcv loop → 종가 + 거래대금 패널 (date × ticker)."""
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
                print(f"  [{i}] {c} EMPTY")
                continue
            closes[c] = o["종가"]
            amts[c] = o["종가"] * o["거래량"]  # 거래대금 = ADV proxy
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
    """DART 정기보고서 제출일 (rcept_dt) — PIT 보고지연 stamp 실측 (semi 미러)."""
    cache = DATA / "dart_filings.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    import requests
    key = os.environ.get("DART_API_KEY", "")
    if not key:
        print("  DART_API_KEY MISSING — skip")
        return {}
    out = {}
    for yr in range(2020, 2026):
        try:
            r = requests.get(
                "https://opendart.fss.or.kr/api/list.json",
                params=dict(crtfc_key=key, bgn_de=f"{yr}0101", end_de=f"{yr}1231",
                            pblntf_ty="A", page_count=100, page_no=1),
                timeout=30,
            )
            j = r.json()
            if j.get("status") == "000":
                rows = j.get("list", [])
                out[str(yr)] = {"total_filings": int(j.get("total_count", 0)), "sample": rows[:3]}
                print(f"  DART {yr}: total={j.get('total_count')}")
        except Exception as ex:
            print(f"  DART {yr} FAIL {repr(ex)[:60]}")
        time.sleep(0.5)
    cache.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    print("[1/3] universe (whitelist) ...")
    uni = build_universe()
    passed = uni[uni["pass_floor"]]
    print(f"  whitelist matched={len(uni)} / floor-passed={len(passed)}")
    print(passed[["Code", "wl_name", "Market", "Marcap", "Amount"]].head(40).to_string(index=False))

    codes = passed["Code"].tolist()
    print(f"\n[2/3] prices ({len(codes)} codes) ...")
    px, amt = collect_prices(codes)
    print(f"  price panel: {px.shape}  date {px.index.min().date()}~{px.index.max().date()}")

    print("\n[3/3] DART filings (보고지연 stamp) ...")
    dart = collect_dart_filings(codes)
    print(f"  dart years: {list(dart.keys())}")
    print("\nDONE")
