# -*- coding: utf-8 -*-
"""collect_rotation_macro.py — auto rotation 고유 driver 추가 수집 (v2 baseline 심화).
team-lead 지시: v2 global_auto_d3(CARZ) STRONG 검증 + v2가 놓친 자동차 고유 driver 측정.

추가 거시 (전부 실데이터, 합성 금지):
  - 미국 금리 DGS2 (2년물, 할부수요 = 음 prior) — FRED
  - 미국 금리 FEDFUNDS — FRED
  - JPYKRW = DEXKOUS/DEXJPUS (엔/원, 한국 경쟁력 = 음 prior 하락 시 OW) — FRED cross
  - 철강원가 = TIO=F(철광석) yfinance (이미 cycle_steel 에 있음 → 재사용)
기존 가용: cli_kr/usdkrw(regime_series) + global_auto(cycle_auto CARZ).
산출: data/rotation_macro.parquet (일별 index, 컬럼 = dgs2/fedfunds/jpykrw)
"""
from __future__ import annotations
import sys, io, os
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pandas as pd, requests

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ENV = Path("D:/projects/Inv/.env")
if ENV.exists():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))
FRED_KEY = os.environ.get("FRED_API_KEY", "")
START, END = "2017-01-01", "2026-06-04"


def fred(sid):
    r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                     params=dict(series_id=sid, api_key=FRED_KEY, file_type="json",
                                 observation_start=START, observation_end=END), timeout=40)
    obs = r.json().get("observations", [])
    idx, val = [], []
    for o in obs:
        if o["value"] not in (".", ""):
            idx.append(pd.Timestamp(o["date"])); val.append(float(o["value"]))
    return pd.Series(val, index=idx, name=sid).sort_index()


def main():
    print("FRED DGS2 (미국 2년물 금리, 할부수요)...")
    dgs2 = fred("DGS2")
    print("FRED FEDFUNDS...")
    ff = fred("FEDFUNDS")
    print("FRED DEXKOUS(USDKRW) + DEXJPUS(USDJPY) → JPYKRW cross...")
    usdkrw = fred("DEXKOUS")   # KRW per USD
    usdjpy = fred("DEXJPUS")   # JPY per USD
    full = pd.date_range(START, END, freq="D")
    dgs2f = dgs2.reindex(full, method="ffill")
    fff = ff.reindex(full, method="ffill")
    ukf = usdkrw.reindex(full, method="ffill")
    ujf = usdjpy.reindex(full, method="ffill")
    jpykrw = ukf / ujf   # (KRW/USD)/(JPY/USD) = KRW per JPY (엔/원). 상승=엔강세/원약세, 하락=한국 경쟁력
    out = pd.DataFrame({"dgs2": dgs2f, "fedfunds": fff, "jpykrw": jpykrw}, index=full)
    out.to_parquet(DATA / "rotation_macro.parquet")
    print(f"\nSaved rotation_macro.parquet {out.shape}")
    print("최근값:", out.dropna().iloc[-1].round(3).to_dict())
    print(f"jpykrw range: {jpykrw.min():.3f} ~ {jpykrw.max():.3f} (엔/원, 합성지문: 2024 엔저 ~9원대 확인)")


if __name__ == "__main__":
    main()
