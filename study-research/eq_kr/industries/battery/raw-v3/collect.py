# -*- coding: utf-8 -*-
"""collect.py — battery §M v3 universe 확장 + 횡단면 패널 수집.

frame v3 §M.7 exposure card 계약 데이터 수집 단계.

산출:
- data/universe.parquet        — battery universe (FDR 섹터 매칭, 시총·ADV floor)  [현재 스냅샷 = PIT 멤버십 한계]
- data/prices.parquet          — universe 종목 일별 종가 패널 (pykrx ohlcv loop)
- data/amount.parquet          — 일별 거래대금 (ADV 유동성 티어용)
- data/dart_filings.json       — DART 보고서 제출일 (PIT 보고지연 stamp)

★데이터 제약 (pilot 발견):
  - pykrx 시장 스냅샷 API (get_market_cap/get_market_fundamental/sector_classifications) = KRX 인증 없이 빈 응답.
    → PBR/PER/시총 횡단면 스냅샷 실측 불가. valuation 횡단면 = DART 펀더멘털 PIT 재구성 또는 격하.
  - pykrx OHLCV 개별종목 loop = 작동 → 가격기반 횡단면 신호 (momentum/vol) 실측 가능.
  - FDR KRX-DESC = Sector/Industry 보유 → universe 멤버십 구성 (단 현재 스냅샷, PIT 멤버십 아님 = 생존편향 한계).
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

# 시총·유동성 floor (방법론 방향, CPCV 캘리브레이션 대상 — §M.6)
MARCAP_FLOOR = 3e11   # 3000억원
ADV_FLOOR = 3e9       # 30억원/일 (listing Amount 스냅샷)

BATTERY_KW = ["2차전지", "이차전지", "배터리", "전지", "양극", "음극", "전해질", "전해액", "분리막"]


def build_universe() -> pd.DataFrame:
    """FDR 섹터/산업/제품 키워드 → battery universe + 시총·ADV floor."""
    cache = DATA / "universe.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import FinanceDataReader as fdr
    desc = fdr.StockListing("KRX-DESC")[["Code", "Name", "Market", "Sector", "Industry", "Products"]]
    kospi = fdr.StockListing("KOSPI")[["Code", "Marcap", "Amount"]]
    kosdaq = fdr.StockListing("KOSDAQ")[["Code", "Marcap", "Amount"]]
    mc = pd.concat([kospi, kosdaq], ignore_index=True)
    m = desc.merge(mc, on="Code", how="left")
    pat = "|".join(BATTERY_KW)
    mask = (
        m["Sector"].fillna("").str.contains(pat)
        | m["Industry"].fillna("").str.contains(pat)
        | m["Products"].fillna("").str.contains(pat)
    )
    bat = m[mask].copy().sort_values("Marcap", ascending=False)
    bat["pass_floor"] = (bat["Marcap"] >= MARCAP_FLOOR) & (bat["Amount"] >= ADV_FLOOR)
    bat.to_parquet(cache)
    return bat


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
    """DART 정기보고서 제출일 (rcept_dt) — PIT 보고지연 stamp 실측.

    fiscal year-end (12-31) vs rcept_dt(제출일) gap = lookahead bias 방지 핵심.
    """
    cache = DATA / "dart_filings.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    import requests
    key = os.environ.get("DART_API_KEY", "")
    if not key:
        print("  DART_API_KEY MISSING — skip")
        return {}
    out = {}
    # 정기보고서 전체 (corp_cls Y=KOSPI, K=KOSDAQ) 2020~2025 사업보고서/분기보고서 제출일 분포
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
                # battery 종목명 매칭 제출 기록만 (corp_name 부분일치 곤란 → 전체 분포 통계로)
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
    print(passed[["Code", "Name", "Market", "Marcap", "Amount"]].head(40).to_string(index=False))

    codes = passed["Code"].tolist()
    print(f"\n[2/3] prices ({len(codes)} codes) ...")
    px, amt = collect_prices(codes)
    print(f"  price panel: {px.shape}  date {px.index.min().date()}~{px.index.max().date()}")

    print("\n[3/3] DART filings (보고지연 stamp) ...")
    dart = collect_dart_filings(codes)
    print(f"  dart years: {list(dart.keys())}")
    print("\nDONE")
