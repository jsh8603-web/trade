# -*- coding: utf-8 -*-
"""collect.py — AItech(인터넷·게임·소프트웨어) §M v3 universe + 횡단면 패널 수집.

frame v3 §M.7 exposure card 계약 데이터 수집 단계. semiconductor pilot collect.py 미러
(SEMI_KW → AITECH_KW + 핵심종목 화이트리스트 강제포함, 나머지 floor/PIT 로직 동일).

★sub-cluster 이질성 (round-1.md §1, frame line 62 + A-4 부호점검 의무):
  - 인터넷 (NAVER/카카오) = 광고 cycle + 커머스 + 플랫폼. archetype = compounder/asset_stable 경계.
  - 게임 (크래프톤/엔씨/넷마블/펄어비스/카카오게임즈/위메이드/컴투스) = 신작 출시·매출 event_driven + growth.
  - SaaS/SI (더존비즈온/한글과컴퓨터 등) = B2B 구독 + AI capex 수혜 compounder.
  → 광고 vs 게임 vs SaaS = 펀더멘털 driver 이질 → sub-cluster 부호 cancel 점검 의무 (frame A-4).

★성장주(growth) archetype prior (team-lead 지시): battery 동형 = momentum continuation 가능성
  (value 보다 growth metric: 매출성장/DAU). momentum 부호 = battery 양(continuation) vs 반도체 음(reversal)
  어느 쪽인지 ★데이터로 판정 (사전 단정 금지, round-1 H 부호 사전확약 후 측정).

산출:
- data/universe.parquet        — aitech universe (FDR 섹터 매칭 + 핵심종목 화이트리스트, 시총·ADV floor)
- data/prices.parquet          — universe 종목 일별 종가 패널 (pykrx ohlcv loop)
- data/amount.parquet          — 일별 거래대금 (ADV 유동성 티어용)
- data/dart_filings.json       — DART 보고서 제출일 (PIT 보고지연 stamp)

★데이터 제약 (battery/semi pilot 발견 동일):
  - pykrx 시장 스냅샷 API(get_market_cap/fundamental/sector) = KRX 인증 없이 빈 응답.
    → PBR/PER/시총 횡단면 스냅샷 실측 불가. valuation 횡단면 = DART 펀더멘털 PIT 재구성(collect_dart.py).
  - pykrx OHLCV 개별종목 loop = 작동 → 가격기반 횡단면 신호(momentum/vol) 실측 가능.
  - FDR KRX-DESC = Sector/Industry/Products 보유 → universe 멤버십 (현재 스냅샷 = 생존편향 한계).
  - ★게임주 적자/턴어라운드 多 (엔씨/넷마블/펄어비스 2022-24 적자) → PER 무효 가능성(bio 동형 event_driven).
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

# 시총·유동성 floor (방법론 방향, CPCV 캘리브레이션 대상 — §M.6). battery/semi 와 동일 floor.
MARCAP_FLOOR = 3e11   # 3000억원
ADV_FLOOR = 3e9       # 30억원/일

# AItech 키워드: 인터넷서비스/게임/소프트웨어/SI 포괄.
# ⚠️ FDR KRX-DESC Sector/Industry 키워드 부정확(frame M.11) → 키워드 + 핵심종목 화이트리스트 병행.
AITECH_KW = ["소프트웨어", "인터넷", "게임", "온라인", "포털", "검색", "콘텐츠",
             "디지털콘텐츠", "모바일게임", "엔터테인먼트", "응용소프트웨어",
             "시스템소프트웨어", "IT서비스", "전자상거래", "플랫폼", "클라우드"]

# ★핵심 종목 화이트리스트 (frame M.11 = 키워드 오분류 차단, 강제 포함).
# 형식: code → (name, sub_cluster). sub_cluster = internet/game/saas.
WHITELIST = {
    # 인터넷 (광고·플랫폼·커머스)
    "035420": ("NAVER", "internet"),
    "035720": ("카카오", "internet"),
    "181710": ("NHN", "internet"),
    "067160": ("아프리카TV", "internet"),   # SOOP
    "376300": ("디어유", "internet"),
    "121800": ("비덴트", "internet"),
    # 게임 (신작·매출 event_driven, growth)
    "259960": ("크래프톤", "game"),
    "036570": ("엔씨소프트", "game"),
    "251270": ("넷마블", "game"),
    "263750": ("펄어비스", "game"),
    "293490": ("카카오게임즈", "game"),
    "112040": ("위메이드", "game"),
    "078340": ("컴투스", "game"),
    "095660": ("네오위즈", "game"),
    "192080": ("더블유게임즈", "game"),
    "225570": ("넥슨게임즈", "game"),
    "194480": ("데브시스터즈", "game"),
    "069080": ("웹젠", "game"),
    "067000": ("조이시티", "game"),
    "950190": ("미투젠", "game"),
    "201490": ("미투온", "game"),
    "145720": ("덴티움", "game"),  # 오분류 방어용 더미 제거 대상 (아래 정리)
    # SaaS / SI / 솔루션 (B2B 구독 + AI capex 수혜)
    "012510": ("더존비즈온", "saas"),
    "030520": ("한글과컴퓨터", "saas"),
    "053800": ("안랩", "saas"),
    "060250": ("NHN KCP", "saas"),
    "035600": ("KG이니시스", "saas"),
    "047560": ("이스트소프트", "saas"),
    "099430": ("바이오플러스", "saas"),  # 오분류 방어용 더미 (아래 정리)
    "108860": ("셀바스AI", "saas"),
    "018260": ("삼성에스디에스", "saas"),   # 클라우드/물류 외부매출 = SaaS/SI 대표 (그룹 captive 경계지만 외부매출 비중 有)
}
# 오분류/비-aitech 더미 제거 (위 dict 에서 명백히 타산업인 것 정리)
for bad in ["145720", "099430", "240810", "121800"]:
    WHITELIST.pop(bad, None)

# ★EXCLUDE 화이트리스트 (frame M.11 = KRX 키워드 오분류 차단, 명백한 타산업 제거).
#   1차 universe(키워드매칭) 점검에서 발견된 비-AItech 종목:
#   - 지주/통신: SK(지주) KT(통신)
#   - 유통: 롯데쇼핑/GS리테일(오프라인 커머스 = retail, 인터넷플랫폼 아님)
#   - 그룹 captive SI: 현대오토에버/포스코DX/LG씨엔에스/현대무벡스(그룹 내부 SI = 광고/게임/AI SaaS cycle 무관, 모회사 종속)
#     ★삼성에스디에스(018260)는 클라우드/물류 외부매출 비중 → 경계, SaaS 유지 검토
#   - 로봇/하드웨어: 로보티즈/뉴로메카/클로봇/노타/마키나락스/엑스게이트/드림시큐리티(로봇·HW·보안HW = AItech SW 아님)
#   - 의료/바이오 AI: 루닛/로킷헬스케어/인벤티지랩/GC메디아이/케이티알파(의료·헬스케어 = bio 영역)
#   - 결제/핀테크 HW: 코나아이/다날/스피어/아이티센글로벌/포스코 계열(결제단말·핀테크 = 별 cycle)
EXCLUDE = {
    "034730", "030200",                      # SK지주, KT통신
    "023530", "007070",                      # 롯데쇼핑, GS리테일 (유통)
    "307950", "022100", "064400", "319400",  # 현대오토에버, 포스코DX, LG씨엔에스, 현대무벡스 (그룹 captive SI)
    "108490", "348340", "466100", "486990", "477850", "356680", "203650",  # 로봇/HW/보안HW
    "328130", "376900", "389470", "032620", "036030",  # 의료/헬스 AI + 케이티알파
    "052400", "064260", "347700", "124500",  # 결제/핀테크 HW
}


def build_universe() -> pd.DataFrame:
    """FDR 섹터/산업/제품 키워드 + 핵심종목 화이트리스트 → aitech universe + 시총·ADV floor.
    ★EXCLUDE 적용 (frame M.11): 키워드 오분류 비-AItech(지주/통신/유통/captive SI/로봇/의료/결제HW) 제거."""
    cache = DATA / "universe.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    import FinanceDataReader as fdr
    desc = fdr.StockListing("KRX-DESC")[["Code", "Name", "Market", "Sector", "Industry", "Products"]]
    kospi = fdr.StockListing("KOSPI")[["Code", "Marcap", "Amount"]]
    kosdaq = fdr.StockListing("KOSDAQ")[["Code", "Marcap", "Amount"]]
    mc = pd.concat([kospi, kosdaq], ignore_index=True)
    m = desc.merge(mc, on="Code", how="left")
    pat = "|".join(AITECH_KW)
    mask = (
        m["Sector"].fillna("").str.contains(pat)
        | m["Industry"].fillna("").str.contains(pat)
        | m["Products"].fillna("").str.contains(pat)
    )
    # 화이트리스트 강제 포함
    mask = mask | m["Code"].isin(WHITELIST.keys())
    # ★EXCLUDE 적용 (화이트리스트보다 우선 — 명백한 타산업 제거, 단 WHITELIST 명시 종목은 보호)
    mask = mask & ~(m["Code"].isin(EXCLUDE) & ~m["Code"].isin(WHITELIST.keys()))
    at = m[mask].copy()
    # sub_cluster 라벨 부착 (화이트리스트 우선, 나머지는 키워드 기반 추정)
    def label_cluster(row):
        if row["Code"] in WHITELIST:
            return WHITELIST[row["Code"]][1]
        txt = f"{row.get('Sector','')} {row.get('Industry','')} {row.get('Products','')}"
        if "게임" in txt or "온라인게임" in txt or "모바일게임" in txt:
            return "game"
        if "인터넷" in txt or "포털" in txt or "전자상거래" in txt or "검색" in txt:
            return "internet"
        return "saas"
    at["sub_cluster"] = at.apply(label_cluster, axis=1)
    at = at.sort_values("Marcap", ascending=False)
    at["pass_floor"] = (at["Marcap"] >= MARCAP_FLOOR) & (at["Amount"] >= ADV_FLOOR)
    # ★화이트리스트 핵심 종목은 floor 미달이어도 sub-cluster 대표성 위해 pass (소형 게임주 breadth 확보)
    at.loc[at["Code"].isin(WHITELIST.keys()) & (at["Marcap"] >= 1e11), "pass_floor"] = True
    at.to_parquet(cache)
    return at


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
    print(f"  sub_cluster (passed): {passed['sub_cluster'].value_counts().to_dict()}")
    print(passed[["Code", "Name", "Market", "sub_cluster", "Marcap", "Amount"]].head(60).to_string(index=False))

    codes = passed["Code"].tolist()
    print(f"\n[2/3] prices ({len(codes)} codes) ...")
    px, amt = collect_prices(codes)
    print(f"  price panel: {px.shape}  date {px.index.min().date()}~{px.index.max().date()}")

    print("\n[3/3] DART filings (보고지연 stamp) ...")
    dart = collect_dart_filings(codes)
    print(f"  dart years: {list(dart.keys())}")
    print("\nDONE")
