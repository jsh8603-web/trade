# -*- coding: utf-8 -*-
"""collect_aitech_cycle.py — ★AItech 업종 고유 cycle 직접신호 수집 (rotation primary alpha).

team-lead 지시 = AItech rotation = 네 fundamental driver:
  - AI capex (글로벌 빅테크 capex proxy) = NVDA (데이터센터 GPU 수요 = hyperscaler capex 직접 대리)
  - 금리 (growth/long-duration 민감) = ^TNX (10Y) — ★성장주 듀레이션 핵심 driver
  - 나스닥/필라델피아 반도체 상대 = QQQ (글로벌 tech cycle) + SOXX (반도체 cycle)
  - 게임 신작 cycle = 무료 정형 시계열 부재(각사 IR) → momentum proxy (한계 박제)

★source 사전검증 (empirical-claim §1.1-ext): yf.Ticker(t).history(period='max') 1샘플 가용범위 확인.
★PIT: 일별 spot = 실시간(lag 불필요). 월말 resample. 금리 = ^TNX level(yield) → Δ 변형은 measure 단계.

산출: data/cycle_aitech.parquet (Date index, 컬럼 = ai_capex_nvda / nasdaq_qqq / rate_10y / soxx_semi).
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
OUT.mkdir(exist_ok=True)
START = "2018-01-01"   # 2019 측정 + yoy(12M) lookback 여유

# AItech 고유 cycle proxy (fundamental driver, source 사전검증 통과분)
AITECH_CYCLE = {
    "ai_capex_nvda": "NVDA",   # AI capex/데이터센터 GPU 수요 = hyperscaler capex 직접 proxy
    "nasdaq_qqq": "QQQ",       # 글로벌 tech/인터넷 cycle
    "rate_10y": "^TNX",        # ★10Y 금리 (growth/long-duration 민감 = 성장주 핵심 macro)
    "soxx_semi": "SOXX",       # 글로벌 반도체 cycle (AI capex 연동)
}
NO_DIRECT = {
    "game_newrelease": "게임 신작 출시·흥행 = 무료 정형 시계열 부재(각사 IR/앱애니 유료) → momentum proxy 유지(한계 박제)",
    "ad_revenue": "인터넷 광고매출 yoy = 분기 IR 수동 → momentum proxy",
    "saas_arr": "SaaS ARR/구독 = 분기 IR 수동 → momentum proxy",
}


def fetch(ticker):
    h = yf.Ticker(ticker).history(period="max", auto_adjust=True)
    if len(h) == 0:
        return None
    s = h["Close"].copy()
    s.index = pd.to_datetime(s.index).tz_localize(None)
    return s.loc[START:]


def main():
    meta = {"source": "yfinance US-listed = 글로벌 cycle proxy (KR 직접 아님 = proxy 한계 박제)",
            "verified": "source 사전검증(empirical-claim §1.1-ext, history(period=max) 1샘플)",
            "drivers": {"ai_capex_nvda": "NVDA 데이터센터 GPU = hyperscaler AI capex 직접 proxy",
                        "nasdaq_qqq": "QQQ 글로벌 tech/인터넷 cycle",
                        "rate_10y": "^TNX 10Y = ★성장주 long-duration 핵심 macro driver",
                        "soxx_semi": "SOXX 글로벌 반도체 cycle (AI capex 연동)"},
            "no_direct": NO_DIRECT, "fetched": {}}
    cols = {}
    for name, ticker in AITECH_CYCLE.items():
        s = fetch(ticker)
        if s is None or len(s) == 0:
            print(f"  {name} ({ticker}) FAIL/EMPTY")
            meta["fetched"][name] = {"ticker": ticker, "status": "EMPTY"}
            continue
        cols[name] = s
        meta["fetched"][name] = {"ticker": ticker, "n": len(s),
                                 "range": [str(s.index.min().date()), str(s.index.max().date())],
                                 "last": round(float(s.iloc[-1]), 2)}
        print(f"  {name:16s} ({ticker:6s}) n={len(s)} {s.index.min().date()}~{s.index.max().date()} last={s.iloc[-1]:.2f}")
    df = pd.concat(cols, axis=1).sort_index()
    df.index.name = "Date"
    df.to_parquet(OUT / "cycle_aitech.parquet")
    (OUT / "cycle_aitech_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved cycle_aitech.parquet {df.shape}")


if __name__ == "__main__":
    main()
