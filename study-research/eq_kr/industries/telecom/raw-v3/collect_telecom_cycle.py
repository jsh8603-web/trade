# -*- coding: utf-8 -*-
"""collect_telecom_cycle.py — 통신 cycle driver 수집 (Layer 3 산업특화, frame §3 통신).

★통신서비스 = defensive 고배당 = bond-proxy. 핵심 cycle driver = ★금리(배당주 duration).
  - 통신=defensive 배당주 → 금리 상승 시 디레이팅(bond-proxy duration), 금리 하락 시 리레이팅.
  - ★common_factors.parquet 의 rate10y 는 ★US 10Y(^TNX) = 한국 배당주 discount rate 부적합.
    → 한국 배당주 duration mechanism 측정 = ★KR 10Y 국채 yield(IRLTLT01KRM156N) 필수.

데이터 소스 (FRED 실데이터, 합성 ⛔):
  - KR 10Y 국채:     IRLTLT01KRM156N (장기 국채 yield, 월별 2000~) ★배당주 duration 핵심
  - KR 3M 금리:      IR3TIB01KRM156N (단기, 월별) — 커브/통화정책
  - US 10Y:          common_factors.parquet rate10y (이미 존재, 글로벌 금리 spillover 대조)

★ARPU / 5G 가입자 / capex = data-gate (frame §3 통신 후보):
  - ARPU·5G 가입자 = MSIT/통계청 월별 공시, 무료 clean time-series API ⛔부재 → ★collector_plan data-gate.
  - 배당수익률 = DART 배당 line 미수집(dart_financials = equity/net_income/assets 만) → ★배당 직접 부재.
    → 통신 배당주 duration 측정 = ★KR 10Y level/Δ vs 통신패널 forward 로 대리(배당수익률 대신 금리 민감도 직접).

산출: data/telecom_cycle.parquet (월별 index: kr_rate10y, kr_rate3m, kr_curve_10y3m + Δ).
"""
from __future__ import annotations
import sys, io, os
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

ENV = Path("D:/projects/Inv/.env")
if ENV.exists():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))

FRED_KEY = os.environ.get("FRED_API_KEY", "")
START = "2018-01-01"
END = "2026-05-31"


def fred_series(sid: str) -> pd.Series:
    r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                     params=dict(series_id=sid, api_key=FRED_KEY, file_type="json",
                                 observation_start=START, observation_end=END), timeout=40)
    j = r.json()
    idx, val = [], []
    for o in j.get("observations", []):
        v = o["value"]
        if v in (".", ""):
            continue
        idx.append(pd.Timestamp(o["date"])); val.append(float(v))
    return pd.Series(val, index=idx, name=sid).sort_index()


def main():
    print("[1/3] KR 10Y 국채 yield (IRLTLT01KRM156N, 월별) ... ★배당주 duration 핵심")
    kr10 = fred_series("IRLTLT01KRM156N")
    print(f"  KR10Y: {kr10.index.min().date()}~{kr10.index.max().date()} n={len(kr10)} last={kr10.iloc[-1]:.2f}%")
    print("[2/3] KR 3M 금리 (IR3TIB01KRM156N, 월별) ...")
    kr3m = fred_series("IR3TIB01KRM156N")
    print(f"  KR3M: {kr3m.index.min().date()}~{kr3m.index.max().date()} n={len(kr3m)} last={kr3m.iloc[-1]:.2f}%")

    # 월별 index (월초 FRED → 월말 정렬)
    full = pd.date_range(START, END, freq="ME")
    df = pd.DataFrame(index=full)
    # FRED 월별 = 월초 timestamp → 월말 reindex ffill (발표지연 보수: 당월 데이터 = 익월 가용)
    kr10_me = kr10.copy(); kr10_me.index = kr10_me.index + pd.offsets.MonthEnd(0)
    kr3m_me = kr3m.copy(); kr3m_me.index = kr3m_me.index + pd.offsets.MonthEnd(0)
    df["kr_rate10y"] = kr10_me.reindex(full, method="ffill")
    df["kr_rate3m"] = kr3m_me.reindex(full, method="ffill")
    df["kr_curve_10y3m"] = df["kr_rate10y"] - df["kr_rate3m"]
    df["d_kr_rate10y"] = df["kr_rate10y"].diff()
    df["d_kr_rate3m"] = df["kr_rate3m"].diff()
    df["kr_rate10y_yoy"] = df["kr_rate10y"].diff(12)

    df.to_parquet(DATA / "telecom_cycle.parquet")
    print(f"\nSaved telecom_cycle.parquet {df.shape}")

    sub = df.loc["2019-01-01":]
    print("\n=== KR 금리 통계 (2019~, %) ===")
    for c in ["kr_rate10y", "kr_rate3m", "kr_curve_10y3m"]:
        s = sub[c].dropna()
        print(f"  {c:18s} mean={s.mean():6.2f}  min={s.min():6.2f}  max={s.max():6.2f}  last={s.iloc[-1]:6.2f}")
    # ★합성지문 검사: 2020 covid 저금리(KR10Y ~1.4%) + 2022-23 금리인상(~3.7%+) 실재
    print("\n=== 역사 이벤트 실재 (합성지문 검사: KR 금리 사이클) ===")
    for dt in ["2020-08-31", "2022-10-31", "2024-06-30", "2026-04-30"]:
        try:
            row = df.loc[df.index <= dt].iloc[-1]
            print(f"  {dt}: KR10Y={row['kr_rate10y']:.2f}% KR3M={row['kr_rate3m']:.2f}% curve={row['kr_curve_10y3m']:+.2f}")
        except Exception as e:
            print(f"  {dt}: {e}")


if __name__ == "__main__":
    main()
