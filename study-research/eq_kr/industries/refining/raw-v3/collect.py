# -*- coding: utf-8 -*-
"""collect.py — refining(정유) §M v3 universe + 패널 수집. auto 미러.

★★CRITICAL data-gate (2026-06-05 실측, FDR KRX-DESC):
  정유 코어 = "석유 정제품 제조업" 5종뿐. 시총3000억∧ADV30억 floor(battery/auto 기준) 통과 = 2종만
  (SK이노096770 / S-Oil010950). 나머지 3종(한국쉘석유/미창석유/극동유화) = microcap·ADV 0.3~1.6억.
  가스유틸/LPG(가스공사/SK가스/E1/삼천리) floor 통과 0종 + archetype 이질(규제 유틸 ≠ 정제마진 cyclical).
  → cross-sectional IC(min 8종) 측정 ⛔불가. capex 횡단면도 n<5 불가.

★수집 전략 = 넓게 수집 후 측정단계 필터 (team-lead 방향 답에 무관하게 데이터 준비):
  - refining 코어 5종(석유 정제품 제조업) 전부 + 가스유틸/LPG floor-완화 주요종.
  - floor = mc≥1e11 ∧ adv≥1e8 (수집용 완화, 측정용 pass_floor 별 컬럼).
  - pass_floor_strict = mc≥3e11 ∧ adv≥3e9 (battery/auto 동일, cross-sectional 자격).
  - is_refining_core = "석유 정제품 제조업" flag (정유 코어 vs 가스 분리 측정용).

산출:
- data/universe.parquet  (Code/Name/Industry/Marcap/Amount/pass_floor/pass_floor_strict/is_refining_core/segment)
- data/prices.parquet    (일별 종가 패널)
- data/amount.parquet    (일별 거래대금)
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

# strict (cross-sectional 자격, battery/auto 동일)
MARCAP_STRICT, ADV_STRICT = 3e11, 3e9
# 수집용 완화 (좁은 universe 전수 확보)
MARCAP_COLLECT, ADV_COLLECT = 1e11, 1e8

# ★Industry 화이트리스트 — 정유 코어 + 가스 유틸/LPG (segment 라벨링)
REFINING_CORE_IND = "석유 정제품 제조업"            # 정유 코어 (SK이노/S-Oil/한국쉘석유/미창석유/극동유화)
GAS_UTIL_IND = "연료용 가스 제조 및 배관공급업"      # 가스 유틸 (한국가스공사/삼천리/대성에너지/도시가스)
# LPG 트레이딩 = 기타 전문 도매업 + LPG/액화석유가스 Products (SK가스/E1)

# ★명시 블랙리스트 (석유/가스 키워드 부수매칭 오염): 특수가스(반도체)·케미칼·조선·방산·정밀기기·가전
BLACKLIST_CODE = {
    "010140",  # 삼성중공업 (조선 — 원유운반선 Products 매칭)
    "047050",  # 포스코인터내셔널 (상품중개/트레이딩, 천연가스 발전 부수)
    "166090",  # 하나머티리얼즈 (반도체 특수가스)
    "281740",  # 레이크머티리얼즈 (석유화학촉매/반도체소재)
    "030530",  # 원익홀딩스 (특수가스 캐비닛)
    "457190",  # 이수스페셜티케미컬 (정밀화학)
    "104830",  # 원익머트리얼즈 (반도체 특수가스)
    "425040",  # 티이엠씨 (반도체 특수가스)
    "097230",  # HJ중공업 (건설/조선)
    "075580",  # 세진중공업 (조선 LPG Tank)
    "488900",  # 비츠로넥스텍 (항공우주 가스발생기)
    "029460",  # 케이씨 (정밀기기 가스공급장치)
    "009450",  # 경동나비엔 (가정용 보일러)
    "037070",  # 파세코 (석유스토브 가전)
}


def build_universe() -> pd.DataFrame:
    cache = DATA / "universe.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import FinanceDataReader as fdr
    desc = fdr.StockListing("KRX-DESC")[["Code", "Name", "Market", "Sector", "Industry", "Products"]]
    kospi = fdr.StockListing("KOSPI")[["Code", "Marcap", "Amount"]]
    kosdaq = fdr.StockListing("KOSDAQ")[["Code", "Marcap", "Amount"]]
    mc = pd.concat([kospi, kosdaq], ignore_index=True)
    m = desc.merge(mc, on="Code", how="left")
    ind = m["Industry"].fillna("")
    prod = m["Products"].fillna("")

    core = ind.str.contains(REFINING_CORE_IND)
    gas_util = ind.str.contains(GAS_UTIL_IND)
    lpg = ind.str.contains("기타 전문 도매업") & prod.str.contains("LPG|액화석유가스|액화천연가스")
    sel = core | gas_util | lpg
    u = m[sel].copy()
    u = u[~u["Code"].isin(BLACKLIST_CODE)]

    u["is_refining_core"] = u["Industry"].fillna("").str.contains(REFINING_CORE_IND)
    u["segment"] = np.where(u["is_refining_core"], "refining",
                            np.where(u["Industry"].fillna("").str.contains(GAS_UTIL_IND), "gas_util", "lpg_trade"))
    u["pass_floor_strict"] = (u["Marcap"] >= MARCAP_STRICT) & (u["Amount"] >= ADV_STRICT)
    u["pass_floor"] = (u["Marcap"] >= MARCAP_COLLECT) & (u["Amount"] >= ADV_COLLECT)
    u = u.sort_values("Marcap", ascending=False)
    u.to_parquet(cache)
    return u


def collect_prices(codes: list[str]):
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


if __name__ == "__main__":
    print("[1/2] universe (정유 코어 + 가스유틸/LPG, segment 라벨) ...")
    uni = build_universe()
    print(f"  total matched={len(uni)}")
    print(uni[["Code", "Name", "Industry", "segment", "Marcap", "Amount",
               "pass_floor", "pass_floor_strict"]].to_string(index=False))
    print(f"\n  ★pass_floor_strict(cross-sectional 자격, mc>=3e11&adv>=3e9) = {int(uni['pass_floor_strict'].sum())}종")
    print(f"  ★refining_core strict = {int((uni['is_refining_core'] & uni['pass_floor_strict']).sum())}종")
    print(f"  pass_floor(완화, mc>=1e11&adv>=1e8) = {int(uni['pass_floor'].sum())}종")

    codes = uni[uni["pass_floor"]]["Code"].tolist()
    print(f"\n[2/2] prices ({len(codes)} codes, 완화 floor 전수 수집) ...")
    px, amt = collect_prices(codes)
    print(f"  price panel: {px.shape}  {px.index.min().date()}~{px.index.max().date()}")
    print("\nDONE")
