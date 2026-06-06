# -*- coding: utf-8 -*-
"""collect_chem_rotation.py — 화학 업종 rotation cycle 지표 수집 (NCC spread/중국수요 심화).

team-lead 가설: naphtha 단독(_rotation v2 -0.367 cost-push)보다 NCC spread(에틸렌-납사) 또는
중국 수요가 본질일 수 있음. 에틸렌 spot = 무료 부재(ICIS/Platts 유료) → collector_plan.
가용 proxy로 심화:
  - wti_naphtha (CL=F 유가 = 납사 원가 proxy, _rotation cycle_chemical 재사용)
  - china_demand = FXI (중국 대형주, 화학 전방수요 proxy) — yfinance 일별
  - china_materials = MCHI (중국 전체) 보조
  - ★cost-push(naphtha)와 demand-pull(China) 분리 측정 → 본질 driver 판별
산출: data/chem_rotation_cycle.parquet (Date × {wti_naphtha, china_fxi, china_mchi})
"""
from __future__ import annotations
import sys, io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pandas as pd, yfinance as yf

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"; DATA.mkdir(parents=True, exist_ok=True)
START, END = "2018-01-01", "2026-06-05"

def main():
    out = {}
    for sym, name in [("CL=F","wti_naphtha"), ("FXI","china_fxi"), ("MCHI","china_mchi")]:
        try:
            s = yf.download(sym, start=START, end=END, progress=False, auto_adjust=True)["Close"].squeeze()
            s.index = pd.to_datetime(s.index)
            out[name] = s
            print(f"  {name}({sym}): n={len(s)} {s.index.min().date()}~{s.index.max().date()}")
        except Exception as e:
            print(f"  {name} FAIL {repr(e)[:50]}")
    df = pd.concat(out, axis=1).sort_index()
    df.to_parquet(DATA / "chem_rotation_cycle.parquet")
    print(f"Saved {df.shape}")

if __name__ == "__main__":
    main()
