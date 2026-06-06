# -*- coding: utf-8 -*-
"""collect_dart_extended.py — 철강 신규 cycle 지표 DART 계정 추가 수집 (S2, ★이연 금지). semiconductor 미러.

사용자 박제(2026-06-05): 신규 발굴 지표(재고순환/CAPEX/R&D) = "나중에 보자" 이연 ⛔금지.
DART 분기 재구성으로 ★지금 측정. 기존 dart_financials.parquet(equity/net_income/assets) 보존, 신규 계정만 추가.

신규 계정 (BS = 계정명 안정적, sj_div 매칭):
  - 재고자산 (재고순환: 재고자산/총자산 = 메모리 cycle 선행, 역상관 prior)
  - 유형자산 (CAPEX/asset growth: 유형자산 yoy + /총자산 = 과잉투자 anomaly, 음 prior)
  - 무형자산 (R&D proxy: 무형자산/총자산 = 기술경쟁력, 양 prior)
  - 매출원가 (재고/매출 보조 정규화 — 매출액 계정명 불안정 회피)

★PIT: rcept_dt(공시일) 이후만. CFS→OFS fallback (collect_dart 동일).
산출: data/dart_extended.parquet (code, year, quarter, rcept_dt, inventory, ppe, intangible, cogs, assets)
"""
from __future__ import annotations
import sys, io, os, json, time
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ENV = Path("D:/projects/Inv/.env")
if ENV.exists():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))
KEY = os.environ.get("DART_API_KEY", "")
REPRT = {"Q1": "11013", "H1": "11012", "Q3": "11014", "FY": "11011"}


def _to_num(s):
    if s is None or s in ("", "-"):
        return None
    try:
        return float(str(s).replace(",", ""))
    except ValueError:
        return None


def fetch_extended(corp_code, year, reprt_code):
    """재고자산/유형자산/무형자산/매출원가/자산총계 + rcept_dt (PIT)."""
    for fs in ("CFS", "OFS"):
        r = requests.get("https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json",
                         params=dict(crtfc_key=KEY, corp_code=corp_code, bsns_year=str(year),
                                     reprt_code=reprt_code, fs_div=fs), timeout=30)
        j = r.json()
        if j.get("status") == "000":
            break
    else:
        return None
    lst = j.get("list", [])
    if not lst:
        return None
    rcept_no = lst[0].get("rcept_no", "")
    out = {"rcept_dt": rcept_no[:8] if len(rcept_no) >= 8 else None,
           "inventory": None, "ppe": None, "intangible": None, "cogs": None, "assets": None}
    for it in lst:
        nm = it.get("account_nm", "").strip()
        sj = it.get("sj_div", "")
        amt = _to_num(it.get("thstrm_amount"))
        if amt is None:
            continue
        if nm == "재고자산" and sj == "BS" and out["inventory"] is None:
            out["inventory"] = amt
        elif nm == "유형자산" and sj == "BS" and out["ppe"] is None:
            out["ppe"] = amt
        elif nm == "무형자산" and sj == "BS" and out["intangible"] is None:
            out["intangible"] = amt
        elif nm == "매출원가" and sj == "IS" and out["cogs"] is None:
            out["cogs"] = amt
        elif nm == "자산총계" and sj == "BS" and out["assets"] is None:
            out["assets"] = amt
    return out


def main():
    if not KEY:
        print("DART_API_KEY MISSING"); return
    uni = pd.read_parquet(DATA / "universe.parquet")
    uni = uni[uni["pass_floor"]]
    codes = uni["Code"].tolist()
    names = dict(zip(uni["Code"], uni["Name"]))
    cmap = json.loads((DATA / "dart_corpcode.json").read_text(encoding="utf-8"))
    print(f"universe {len(codes)} codes")

    cache = DATA / "dart_extended.parquet"
    DONE = DATA / "dart_ext_done.json"
    rows = pd.read_parquet(cache).to_dict("records") if cache.exists() else []
    done = set(json.loads(DONE.read_text())) if DONE.exists() else set()
    if done:
        print(f"resume: {len(rows)} rows, {len(done)}/{len(codes)} done")

    for ci, code in enumerate(codes):
        if code in done:
            continue
        cc = cmap.get(code)
        if not cc:
            done.add(code); continue
        for year in range(2019, 2026):
            for qlabel, rcode in REPRT.items():
                try:
                    fin = fetch_extended(cc, year, rcode)
                    if fin and (fin.get("inventory") is not None or fin.get("ppe") is not None):
                        rows.append(dict(code=code, name=names[code], year=year, quarter=qlabel, **fin))
                except Exception:
                    pass
                time.sleep(0.13)
        done.add(code)
        pd.DataFrame(rows).to_parquet(cache)
        DONE.write_text(json.dumps(sorted(done)))
        print(f"  [{ci+1}/{len(codes)}] {code} {names[code]} done rows={len(rows)}", flush=True)
    df = pd.DataFrame(rows)
    df.to_parquet(cache)
    print(f"\nSaved {cache}: {len(df)} rows, {df['code'].nunique()} codes")
    if len(df):
        cov = df[["inventory", "ppe", "intangible", "cogs"]].notna().mean()
        print("coverage:", cov.round(2).to_dict())


if __name__ == "__main__":
    main()
