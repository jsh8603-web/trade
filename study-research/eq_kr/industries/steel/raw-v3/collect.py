# -*- coding: utf-8 -*-
"""collect.py — steel(철강·금속) §M v3 universe + 횡단면 패널 수집.

frame v3 §M.7 exposure card 계약 데이터 수집. semiconductor collect.py 미러
(SEMI_KW → STEEL_KW, floor/PIT 로직 동일).

산출:
- data/universe.parquet        — steel universe (FDR 섹터 매칭, 시총·ADV floor) [현 스냅샷 = PIT 멤버십 한계]
- data/prices.parquet          — universe 종목 일별 종가 패널 (pykrx ohlcv loop)
- data/amount.parquet          — 일별 거래대금 (ADV 유동성 티어용)
- data/dart_filings.json       — DART 보고서 제출일 (PIT 보고지연 stamp)

★데이터 제약 (battery/semi pilot 동일):
  - pykrx 시장 스냅샷 API = KRX 인증 없이 빈 응답 → valuation 횡단면 = DART PIT 재구성(collect_dart.py).
  - pykrx OHLCV 개별종목 loop = 작동 → 가격기반 횡단면 신호(momentum/vol) 실측 가능.
  - FDR KRX-DESC = Sector/Industry/Products 보유 → universe (현 스냅샷, PIT 멤버십 아님 = 생존편향 한계).

★철강 universe 협소 주의 (dispatch role): POSCO홀딩스(005490)/현대제철(004020) 등 대형주 소수.
  소형 압연/특수강 종목 포함해도 breadth 작음(반도체 85종 대비). → small-breadth hedge, cap-weighted IC 점검 의무.
★철강 sub-cluster (theory): 고로 일관제철(POSCO/현대제철) / 전기로(특수강·봉형강) / 강관·압연 가공.
  자산집약 장치산업(고로/설비) → capex_ratio 우선 검증(dispatch ★★capex 일반화 가설, asset growth anomaly 음 prior).
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

# 시총·유동성 floor (방법론 방향, CPCV 캘리브레이션 대상 — §M.6).
# ★철강 = 협소·저유동성 산업(dispatch 경고). 반도체 floor(3000억 ∧ ADV30억) 적용시 3~5종 = breadth 붕괴.
#   → small-breadth hedge: Marcap floor 1000억 ∧ ADV floor 1억으로 완화. 그래도 ~28종(반도체 85종의 1/3).
MARCAP_FLOOR = 1e11   # 1000억원 (반도체 3000억 → 철강 협소 완화)
ADV_FLOOR = 1e8       # 1억원/일 (반도체 30억 → 저유동성 철강 완화)

# ★철강 화이트리스트 = "1차 철강 제조업" Industry 중심 (frame §M.11 화이트리스트 의무).
#   FDR 키워드 매칭(STEEL_KW)은 발전설비/상사/전선/조선 혼입 → Industry 정밀 필터 + 명시 제외.
STEEL_KW = ["철강", "제철", "철강금속", "특수강", "스테인리스", "스테인레스",
            "강관", "선재", "봉강", "후판", "열연", "냉연", "도금", "압연",
            "철근", "형강", "코크스", "합금철", "주물", "단조"]
# ★순수 철강 Industry = "1차 철강 제조업" 한정 (frame §M.11 화이트리스트).
#   "기타 금속 가공제품 제조업"은 절삭공구·방산·공작기계·롤러 多 = 철강 본질 아님 → 제외.
#   단 명확한 철강 가공(자유형단조품)만 INCLUDE_EXTRA 화이트리스트로 보완.
STEEL_IND = ["1차 철강 제조업"]
INCLUDE_EXTRA = {"044490"}   # 태웅(자유형단조품=철강 단조, 기타금속가공이나 철강 본질)
# ★명시 제외 (Industry 매칭됐으나 비철강 본질 = 화이트리스트 sanity check):
#   두산에너빌리티(발전설비/원전) / 포스코인터내셔널(상사) / 대한전선(전선/케이블) /
#   SK오션플랜트(해양구조물=조선) / 포스코엠텍(2차전지 소재/포장) / GS글로벌·현대코퍼(상사)
EXCLUDE_CODES = {"034020", "047050", "001440", "100090", "009520",
                 "001250", "011760", "002900", "005720"}


def build_universe() -> pd.DataFrame:
    """FDR Industry 정밀 매칭 + 명시 제외 → steel universe + 시총·ADV floor."""
    cache = DATA / "universe.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import FinanceDataReader as fdr
    desc = fdr.StockListing("KRX-DESC")[["Code", "Name", "Market", "Sector", "Industry", "Products"]]
    kospi = fdr.StockListing("KOSPI")[["Code", "Marcap", "Amount"]]
    kosdaq = fdr.StockListing("KOSDAQ")[["Code", "Marcap", "Amount"]]
    mc = pd.concat([kospi, kosdaq], ignore_index=True)
    m = desc.merge(mc, on="Code", how="left")
    # ★1차 필터 = "1차 철강 제조업" Industry 정밀 매칭 + INCLUDE_EXTRA 화이트리스트.
    ind_mask = m["Industry"].fillna("").isin(STEEL_IND) | m["Code"].isin(INCLUDE_EXTRA)
    mask = ind_mask & ~m["Code"].isin(EXCLUDE_CODES)
    steel = m[mask].copy().sort_values("Marcap", ascending=False)
    steel["pass_floor"] = (steel["Marcap"] >= MARCAP_FLOOR) & (steel["Amount"] >= ADV_FLOOR)
    steel.to_parquet(cache)
    return steel


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
    """DART 정기보고서 제출일 (rcept_dt) — PIT 보고지연 stamp 실측."""
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
    print("[1/3] universe ...")
    uni = build_universe()
    passed = uni[uni["pass_floor"]]
    print(f"  total matched={len(uni)} / floor-passed={len(passed)}")
    print(passed[["Code", "Name", "Market", "Marcap", "Amount"]].head(50).to_string(index=False))

    codes = passed["Code"].tolist()
    print(f"\n[2/3] prices ({len(codes)} codes) ...")
    px, amt = collect_prices(codes)
    print(f"  price panel: {px.shape}  date {px.index.min().date()}~{px.index.max().date()}")

    print("\n[3/3] DART filings (보고지연 stamp) ...")
    dart = collect_dart_filings(codes)
    print(f"  dart years: {list(dart.keys())}")
    print("\nDONE")
