# -*- coding: utf-8 -*-
"""collect_refining_cycle.py — 정유 cycle driver 수집 (Layer 3 산업특화, frame §3 정유: 정제spread/유가/가동률).

★정유 cycle 본질 = 정제마진(crack spread) — 제품가(휘발유/디젤) − 원유가. 정유사 마진의 직접 driver.
  한국 정유 = 싱가포르 GRM(정제마진)이 표준이나 무료 부재 → ★US Gulf Coast crack spread proxy
  (글로벌 정제마진 동조 — 한국 정유사도 수출 비중 高, 아시아-미국 spread 상관 강).

데이터 소스 (전부 FRED 실데이터, 합성 ⛔):
  - Brent 유가:       DCOILBRENTEU ($/bbl, 일별)
  - WTI 유가:         DCOILWTICO ($/bbl, 일별)
  - Gulf Gasoline:    DGASUSGULF ($/gal, 일별) → ×42 = $/bbl
  - Gulf Diesel:      DDFUELUSGULF ($/gal, 일별) → ×42 = $/bbl
  - 정유 가동률 proxy: IPG32411S (석유·석탄제품 IP, 월별) — refinery throughput proxy
  - Henry Hub NatGas: DHHNGSP (가스유틸 segment driver, $/MMBtu)

산출 시리즈 (일별 index):
  - brent / wti / oil_yoy
  - gasoline_crack = gasoline*42 - brent  ($/bbl, 휘발유 크랙)
  - diesel_crack   = diesel*42 - brent    ($/bbl, 디젤 크랙)
  - blended_crack  = (2*gasoline + diesel)/3 *42 - brent   (3-2-1 근사 정제마진)
  - refinery_ip / natgas

산출: data/refining_cycle.parquet (일별 index, 위 컬럼). 월말 resample 은 측정단계.
"""
from __future__ import annotations
import sys, io, os, time
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
END = "2026-05-29"
GAL_PER_BBL = 42.0


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
    print("[1/6] Brent (DCOILBRENTEU) ...")
    brent = fred_series("DCOILBRENTEU")
    print(f"  brent: {brent.index.min().date()}~{brent.index.max().date()} n={len(brent)}")
    print("[2/6] WTI (DCOILWTICO) ...")
    wti = fred_series("DCOILWTICO")
    print("[3/6] Gulf Gasoline (DGASUSGULF, $/gal) ...")
    gaso = fred_series("DGASUSGULF")
    print("[4/6] Gulf Diesel (DDFUELUSGULF, $/gal) ...")
    diesel = fred_series("DDFUELUSGULF")
    print("[5/6] 정유 가동률 proxy IP (IPG32411S, 월별) ...")
    refip = fred_series("IPG32411S")
    print(f"  refinery IP: {refip.index.min().date()}~{refip.index.max().date()} n={len(refip)}")
    print("[6/6] Henry Hub NatGas (DHHNGSP) ...")
    ng = fred_series("DHHNGSP")

    full = pd.date_range(START, END, freq="D")
    df = pd.DataFrame(index=full)
    df["brent"] = brent.reindex(full, method="ffill")
    df["wti"] = wti.reindex(full, method="ffill")
    gaso_f = gaso.reindex(full, method="ffill")
    diesel_f = diesel.reindex(full, method="ffill")
    df["refinery_ip"] = refip.reindex(full, method="ffill")
    df["natgas"] = ng.reindex(full, method="ffill")

    # ★crack spread ($/bbl) = 제품가($/gal ×42) − 원유가($/bbl)
    df["gasoline_crack"] = gaso_f * GAL_PER_BBL - df["brent"]
    df["diesel_crack"] = diesel_f * GAL_PER_BBL - df["brent"]
    # 3-2-1 근사 정제마진 (2 휘발유 + 1 디젤 per 3 원유)
    df["blended_crack"] = (2 * gaso_f + diesel_f) / 3.0 * GAL_PER_BBL - df["brent"]
    # yoy
    df["oil_yoy"] = df["brent"] / df["brent"].shift(365) - 1

    df.to_parquet(DATA / "refining_cycle.parquet")
    print(f"\nSaved refining_cycle.parquet {df.shape}")

    sub = df.loc["2019-01-01":]
    print("\n=== 정제마진 통계 (2019~, $/bbl) ===")
    for c in ["brent", "gasoline_crack", "diesel_crack", "blended_crack", "refinery_ip"]:
        s = sub[c].dropna()
        print(f"  {c:16s} mean={s.mean():8.2f}  min={s.min():8.2f}  max={s.max():8.2f}  last={s.iloc[-1]:8.2f}")
    # ★합성지문 검사: 2020 covid crack 붕괴 + 2022 우크라 diesel crack 폭등 실재 확인
    print("\n=== 역사 이벤트 실재 (합성지문 검사) ===")
    for dt in ["2020-04-15", "2022-06-15", "2024-09-15"]:
        row = df.loc[df.index <= dt].iloc[-1]
        print(f"  {dt}: brent={row['brent']:.1f} gasoline_crack={row['gasoline_crack']:.1f} diesel_crack={row['diesel_crack']:.1f}")


if __name__ == "__main__":
    main()
