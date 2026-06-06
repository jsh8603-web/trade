# -*- coding: utf-8 -*-
"""collect.py — shipbuilding(조선) §M v3 universe 확장 + 횡단면 패널 수집.

frame v3 §M.7 exposure card 계약 데이터 수집 단계. semiconductor collect.py 미러
(SEMI_KW → SHIP whitelist/blacklist, 나머지 floor/PIT 로직 동일).

산출:
- data/universe.parquet        — shipbuilding universe (KRX Industry "선박 및 보트 건조업" + 조선기자재 화이트리스트, 시총·ADV floor)
- data/prices.parquet          — universe 종목 일별 종가 패널 (pykrx ohlcv loop)
- data/amount.parquet          — 일별 거래대금 (ADV 유동성 티어용)
- data/dart_filings.json       — DART 보고서 제출일 (PIT 보고지연 stamp)

★조선 universe 정밀화 (frame §M.11 화이트리스트 의무 = KRX FDR 키워드 부정확 대응):
  - 키워드 "조선/선박/해양/플랜트/기자재" 단독은 오분류 大 (현대모비스=자동차부품 / 두산에너빌리티=발전 /
    한국전력=전력 / HMM=해운 / 포스코인터내셔널=상사 / GS건설=건설 등 혼입 — 육안 sanity check 확인).
  - 가장 깨끗한 식별자 = KRX Industry "선박 및 보트 건조업". + 조선기자재(엔진/부품) 핵심 종목 화이트리스트.
  - 명백한 비조선(자동차/발전/전력/해운/상사/건설)은 블랙리스트로 제외.

★조선 집중도: HD현대중공업+HD한국조선해양+한화오션+삼성중공업 4대장 = 조선 시총 대부분 + 협소 universe.
  → 반도체(삼성+SK 50%)와 동형 = cap-weighted IC 로 microcap 지배 점검 의무 + small breadth hedge.

★조선 cycle 특수성 (capex 부호 재검토 = team-lead 박제):
  - 조선은 orderbook(수주잔고) 기반 = asset growth(유형자산↑)가 과잉투자 anomaly(음 prior, Cooper-Gulen-Schill)와
    수주확대 proxy(양 가능) 양쪽 해석 가능 → 부호 prior 데이터로 판정(반도체/auto 의 음 prior 그대로 적용 금지).
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
# ★조선 = 협소 universe(시총 3000억 floor 통과 9종, ADV 30억 4종) = 횡단면 IC 측정 불가능 수준.
#   → floor 완화 (시총 1000억 / ADV 5억) 로 측정 universe 확보(~15-18종). 단 유동성-티어 IC(frame §M.1 ⑱)
#     + cap-weighted IC 로 microcap 지배 별도 점검 + ★small breadth hedge(verdict 명시 의무).
#   semiconductor(85종)/battery(29종) 대비 ★구조적 breadth 부족 = magnitude 보수 cap + 단정 금지.
MARCAP_FLOOR = 1e11   # 1000억원 (조선 협소 universe 대응 완화, 유동성-티어로 별도 점검)
ADV_FLOOR = 5e8       # 5억원/일 (거래 가능 최소선, 초소형 ADV~0 종목 제외)

# ★KRX Industry 정밀 식별자 = "선박 및 보트 건조업" (가장 깨끗).
SHIP_INDUSTRY_CORE = "선박 및 보트 건조업"

# ★조선기자재(엔진/부품/배관/케이블 등) — Industry 가 "선박 건조업" 아니지만 조선 cycle 직접 노출.
#   육안 sanity check (2026-06-05): Products 에 "선박/조선/대형선박용엔진" 명시 + 매출 조선 의존.
SHIP_WHITELIST_NAMES = [
    "HD현대중공업", "한화오션", "삼성중공업", "HD한국조선해양",   # 4대장 (HD한국조선해양 Industry=기타금융업[지주]이나 조선 지주)
    "한화엔진", "HD현대마린엔진",                                # 대형 선박엔진
    "한국카본",                                                # LNG선 보냉재 (탄소섬유)
    "대한조선", "세진중공업", "현대힘스", "HJ중공업",            # 조선·블록·기자재
    "인화정공", "케이프", "한라IMS", "오리엔탈정공",            # 선박엔진부품/기자재
    "대양전기공업", "케이에스피", "동방선기", "삼영이엔씨",       # 선박 전장/밸브/배관/항법
    "STX엔진", "현대힘스", "성광벤드", "태광",                  # 엔진/피팅(조선 수요 비중 高)
    "동성화인텍",                                              # LNG선 보냉재 (한국카본 경쟁사)
]

# ★블랙리스트 (키워드 매칭되나 비조선 = 육안 확인 명백 오분류).
SHIP_BLACKLIST_NAMES = [
    "현대모비스",        # 자동차 신품 부품
    "두산에너빌리티",     # 발전 터빈/플랜트 (선박용엔진 매출 일부지만 주력 발전)
    "한국전력",          # 전력
    "HMM", "KSS해운",    # 해운 (선박 운영, 건조 아님)
    "포스코인터내셔널", "현대코퍼레이션", "STX", "삼미금속",  # 상사/도매/금속
    "GS건설", "코오롱글로벌", "SGC E&C", "금양그린파워",      # 건설/플랜트시공
    "신흥", "SDN", "디엔에프", "강원에너지", "우양에이치씨",  # 치과/태양광/반도체소재/보일러
]

# 1차 광역 매칭 키워드 (whitelist/blacklist 로 후처리).
SHIP_KW = ["조선", "선박", "해양플랜트", "조선기자재", "선박부품",
           "선박엔진", "LNG선", "컨테이너선", "선박용", "함정", "방산함"]


def build_universe() -> pd.DataFrame:
    """KRX Industry "선박 및 보트 건조업" core + 조선기자재 화이트리스트 − 블랙리스트 + 시총·ADV floor."""
    cache = DATA / "universe.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import FinanceDataReader as fdr
    desc = fdr.StockListing("KRX-DESC")[["Code", "Name", "Market", "Sector", "Industry", "Products"]]
    kospi = fdr.StockListing("KOSPI")[["Code", "Marcap", "Amount"]]
    kosdaq = fdr.StockListing("KOSDAQ")[["Code", "Marcap", "Amount"]]
    mc = pd.concat([kospi, kosdaq], ignore_index=True)
    m = desc.merge(mc, on="Code", how="left")

    # (1) Industry core = "선박 및 보트 건조업"
    core = m["Industry"].fillna("").str.contains(SHIP_INDUSTRY_CORE)
    # (2) 키워드 광역 매칭 (Products/Sector/Industry)
    pat = "|".join(SHIP_KW)
    kw = (m["Sector"].fillna("").str.contains(pat)
          | m["Industry"].fillna("").str.contains(pat)
          | m["Products"].fillna("").str.contains(pat))
    # (3) 화이트리스트 이름
    wl = m["Name"].isin(SHIP_WHITELIST_NAMES)

    mask = (core | kw | wl)
    # (4) 블랙리스트 제거
    mask &= ~m["Name"].isin(SHIP_BLACKLIST_NAMES)

    ship = m[mask].copy().sort_values("Marcap", ascending=False)
    ship["pass_floor"] = (ship["Marcap"] >= MARCAP_FLOOR) & (ship["Amount"] >= ADV_FLOOR)
    # ★strict floor (반도체/battery 동일 3000억/30억) 통과 = high-liquidity 티어 라벨 (유동성-티어 IC 점검용).
    ship["tier_strict"] = (ship["Marcap"] >= 3e11) & (ship["Amount"] >= 3e9)
    # ★universe 멤버십 sub-cluster 라벨 (육안 sanity)
    ship["is_core_builder"] = ship["Industry"].fillna("").str.contains(SHIP_INDUSTRY_CORE) | ship["Name"].isin(
        ["HD현대중공업", "한화오션", "삼성중공업", "HD한국조선해양", "대한조선", "HJ중공업"])
    ship.to_parquet(cache)
    return ship


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


if __name__ == "__main__":
    print("[1/2] universe ...")
    uni = build_universe()
    passed = uni[uni["pass_floor"]]
    print(f"  total matched={len(uni)} / floor-passed={len(passed)}")
    print(passed[["Code", "Name", "Market", "Marcap", "Amount", "is_core_builder"]].head(50).to_string(index=False))

    codes = passed["Code"].tolist()
    print(f"\n[2/2] prices ({len(codes)} codes) ...")
    px, amt = collect_prices(codes)
    print(f"  price panel: {px.shape}  date {px.index.min().date()}~{px.index.max().date()}")
    print("\nDONE")
