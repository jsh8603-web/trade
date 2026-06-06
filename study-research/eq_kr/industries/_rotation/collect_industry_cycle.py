# -*- coding: utf-8 -*-
"""collect_industry_cycle.py — 9업종 고유 cycle 직접신호 수집 (자문 A 본체, 무료 proxy).

★자문 결론 A = "각 업종 고유 cycle 직접신호가 진짜 alpha" (가격 momentum 강등).
source 사전검증 완료(empirical-claim §1.1-ext): yf.Ticker(t).history(period='max') 1샘플 가용범위 확인.
- steel: TIO=F(철광석) + FXI(중국 proxy) | battery: LIT(리튬 ETF) | chemical: CL=F(WTI/나프타) + XLB
- auto: CARZ(글로벌 자동차) | shipbuilding: BDRY(Baltic Dry 운임 2018~) | semiconductor: SOXX
- refining: 기존 refining_cycle.parquet 보유(crack/oil) | telecom: telecom_cycle.parquet 보유
- bio/consumer/financial: 고유 cycle 직접 어려움 → momentum proxy 유지 + "가용 무료 부재" 한계 박제(이연 아님)

⛔ source 출처 명시: yfinance(US-listed ETF/futures = 글로벌 cycle proxy, KR 직접 아님 = proxy 한계 박제).
   ★PIT: 일별 spot = 실시간(lag 불필요). 월말 resample. forward 예측 = 신호 t → 산업 forward t+h.
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)
START = "2018-01-01"   # 2019 측정 + yoy(12M) lookback 여유

# 산업별 고유 cycle proxy (source 사전검증 통과분만)
INDUSTRY_CYCLE = {
    "steel":        {"iron_ore": "TIO=F", "china_proxy": "FXI"},      # 철광석 + 중국 수요
    "battery":      {"lithium": "LIT"},                              # 리튬 ETF
    "chemical":     {"wti_naphtha": "CL=F", "materials": "XLB"},      # 유가(나프타) + 소재
    "auto":         {"global_auto": "CARZ"},                          # 글로벌 자동차 판매 proxy
    "shipbuilding": {"baltic_dry": "BDRY"},                           # 운임(2018~)
    "semiconductor":{"soxx": "SOXX"},                                 # 글로벌 반도체 cycle
}
# 한계 박제 (고유 cycle 직접 부재 → momentum proxy 유지)
NO_DIRECT_CYCLE = {
    "telecom": "telecom_cycle.parquet 보유(별도) + ARPU/5G 무료 API 부재 → momentum/carry 유지",
    "refining": "refining_cycle.parquet 보유(crack/oil 별도 measure_timeseries) → 본 수집 제외",
    "financial": "금리커브(regime_series ktb10y/ktb3y/corp_aa3y) 보유 = cycle 대용",
    "bio": "pipeline/FDA 이벤트 = 무료 정형 시계열 부재 → momentum proxy 유지",
    "consumer": "소매판매/K-food 수출 = 무료 월별 KR 직접 부재(관세청 API 미연동) → momentum/USDKRW 유지",
}


def fetch(ticker):
    h = yf.Ticker(ticker).history(period="max", auto_adjust=True)
    if len(h) == 0:
        return None
    s = h["Close"].copy()
    s.index = pd.to_datetime(s.index).tz_localize(None)
    return s.loc[START:]


def main():
    meta = {"source": "yfinance US-listed ETF/futures = 글로벌 cycle proxy (KR 직접 아님 = proxy 한계)",
            "verified": "source 사전검증 통과(empirical-claim §1.1-ext, history(period=max) 1샘플)",
            "no_direct_cycle": NO_DIRECT_CYCLE, "fetched": {}}
    for sector, tickers in INDUSTRY_CYCLE.items():
        df = {}
        for name, t in tickers.items():
            s = fetch(t)
            if s is None:
                print(f"  [FAIL] {sector}/{name} {t}")
                continue
            df[name] = s
            print(f"  [OK] {sector}/{name:14s} {t:7s} {s.index.min().date()}~{s.index.max().date()} n={len(s)}")
        if not df:
            continue
        cyc = pd.DataFrame(df)
        fp = OUT / f"cycle_{sector}.parquet"
        cyc.to_parquet(fp)
        meta["fetched"][sector] = {"tickers": tickers, "n": len(cyc),
                                   "range": f"{cyc.index.min().date()}~{cyc.index.max().date()}"}
    (OUT / "cycle_collect_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved {len(meta['fetched'])} sector cycle parquets + cycle_collect_meta.json")


if __name__ == "__main__":
    main()
