# -*- coding: utf-8 -*-
"""collect_aitech_cycle_ext.py — ★AItech rotation 후보 확장 수집 (team-lead 재보강: ≥8-10개 전수).

기존 collect_aitech_cycle.py 4종(NVDA/QQQ/^TNX/SOXX) + ★신규 6종 = 10종 cycle 신호.
증권 IT/AI/게임 리포트의 AItech 업종 driver 망라 (★source 사전검증 통과 = empirical-claim §1.1-ext).

후보 ≥10개 (부호 사전확약은 measure_rotation_ext.py 헤더):
  [기존 4]
  - rate_10y (^TNX)        = 금리 growth duration (음 prior, primary)
  - nasdaq_qqq (QQQ)       = 글로벌 tech cycle (양 prior)
  - ai_capex_nvda (NVDA)   = AI capex/GPU 수요 (양 prior → REJECTED 재검증)
  - soxx_semi (SOXX)       = 반도체 cycle (양 prior → REJECTED 재검증)
  [신규 6]
  - hyperscaler_capex (MSFT+GOOGL+AMZN 평균) = 클라우드 capex 대형주 (양 prior, NVDA와 다른 각도)
  - power_demand_xlu (XLU) = AI 데이터센터 전력수요 = 유틸리티 (양 prior, AI 인프라 cycle)
  - global_sw_igv (IGV)    = 글로벌 SW ETF (양 prior, SaaS 업황)
  - game_espo (ESPO)       = 글로벌 게임/e스포츠 ETF (양 prior, 게임 신작 cycle proxy)
  - vix (^VIX)             = 위험선호 (음 prior, growth 고베타 risk-off)
  - cloud_skyy (SKYY)      = 클라우드 인프라 ETF (양 prior)
  [measure 단계 파생]
  - soxx_qqq_spread        = SOXX/QQQ ratio (반도체 상대강도, measure 에서 계산)
  - usdkrw                 = 환율 (regime_series 재사용, 수출 SW/게임, measure 에서)
  - rel_mom_kr             = AItech 업종 vs KOSPI 상대모멘텀 (measure 에서, 업종수익 자체)

★source 사전검증 (history(period=max)): MSFT 1986~/GOOGL 2004~/AMZN 1997~/XLU 1998~/IGV 2001~/ESPO 2018~/VIX 1990~/SKYY 2011~ = 전부 2019 측정 가용.
★PIT: 일별 spot 실시간. yfinance US-listed = 글로벌 proxy(KR 직접 아님 한계 박제).
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import warnings; warnings.filterwarnings("ignore")
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data"
START = "2018-01-01"

# 신규 단일 ticker 후보
NEW_SINGLE = {
    "power_demand_xlu": "XLU",
    "global_sw_igv": "IGV",
    "game_espo": "ESPO",
    "vix": "^VIX",
    "cloud_skyy": "SKYY",
}
# hyperscaler = 3종 평균 (클라우드 capex 대형주 바스켓)
HYPERSCALER = ["MSFT", "GOOGL", "AMZN"]


def fetch(ticker):
    h = yf.Ticker(ticker).history(period="max", auto_adjust=True)
    if len(h) == 0:
        return None
    s = h["Close"].copy()
    s.index = pd.to_datetime(s.index).tz_localize(None)
    return s.loc[START:]


def main():
    # 기존 4종 로드 (cycle_aitech.parquet)
    base = pd.read_parquet(OUT / "cycle_aitech.parquet"); base.index = pd.to_datetime(base.index)
    cols = {c: base[c] for c in base.columns}
    meta = {"source": "yfinance US-listed = 글로벌 cycle proxy (KR 직접 아님 한계)",
            "base_4": list(base.columns), "new": {}}

    # 신규 단일
    for name, ticker in NEW_SINGLE.items():
        s = fetch(ticker)
        if s is None or len(s) == 0:
            print(f"  {name} ({ticker}) EMPTY"); meta["new"][name] = "EMPTY"; continue
        cols[name] = s
        meta["new"][name] = {"ticker": ticker, "n": len(s), "range": [str(s.index.min().date()), str(s.index.max().date())]}
        print(f"  {name:18s} ({ticker:6s}) n={len(s)} {s.index.min().date()}~{s.index.max().date()}")

    # hyperscaler 바스켓 (3종 정규화 평균 = 동일가중 가격지수)
    hs = {}
    for t in HYPERSCALER:
        s = fetch(t)
        if s is not None and len(s):
            hs[t] = s / s.iloc[0]   # 시작=1 정규화
    if hs:
        hsdf = pd.DataFrame(hs).ffill()
        cols["hyperscaler_capex"] = hsdf.mean(axis=1)   # eq-weight 바스켓
        meta["new"]["hyperscaler_capex"] = {"basket": HYPERSCALER, "n": len(hsdf)}
        print(f"  hyperscaler_capex  (MSFT+GOOGL+AMZN eq-weight) n={len(hsdf)}")

    df = pd.concat(cols, axis=1).sort_index()
    df.index.name = "Date"
    df.to_parquet(OUT / "cycle_aitech_ext.parquet")
    (OUT / "cycle_aitech_ext_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved cycle_aitech_ext.parquet {df.shape} (cols: {list(df.columns)})")


if __name__ == "__main__":
    main()
