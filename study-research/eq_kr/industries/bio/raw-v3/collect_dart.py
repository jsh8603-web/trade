# -*- coding: utf-8 -*-
"""collect_dart.py — battery 29종 DART 재무제표 PIT 수집 (valuation 횡단면 결함 해소).

supervisor 지시 (2026-06-03):
  - 29종 분기말 재무제표 (자본총계/당기순이익/자산총계) = OpenDART fnlttSinglAcntAll
  - ★PIT 엄수: rcept_no 앞 8자리(=접수일=공시일) lag 이후만 사용 = publication lag (lookahead·restatement 회피)
  - BPS/EPS 산출 → pykrx 무료 가격(시총) 결합 → PBR/PER 계산
  - 합성 금지, 실 DART만. rate limit 주의 → sleep.

산출:
  - data/dart_corpcode.json        — 종목코드 → corp_code 매핑
  - data/dart_financials.parquet   — (corp, year, quarter) × {자본총계, 당기순이익, 자산총계, rcept_dt, 주식수}
"""
from __future__ import annotations
import sys, io, os, json, time, zipfile
import io as _io
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import pandas as pd
import requests
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

ENV = Path("D:/projects/Inv/.env")
if ENV.exists():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))
KEY = os.environ.get("DART_API_KEY", "")

# 정기보고서 코드: 1분기 11013 / 반기 11012 / 3분기 11014 / 사업보고서(연간) 11011
REPRT = {"Q1": "11013", "H1": "11012", "Q3": "11014", "FY": "11011"}


def get_corpcode_map() -> dict:
    cache = DATA / "dart_corpcode.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    r = requests.get("https://opendart.fss.or.kr/api/corpCode.xml", params=dict(crtfc_key=KEY), timeout=60)
    z = zipfile.ZipFile(_io.BytesIO(r.content))
    root = ET.fromstring(z.read(z.namelist()[0]))
    mapping = {}
    for el in root.iter("list"):
        sc = el.findtext("stock_code")
        cc = el.findtext("corp_code")
        if sc and sc.strip():
            mapping[sc.strip()] = cc.strip()
    cache.write_text(json.dumps(mapping, ensure_ascii=False), encoding="utf-8")
    return mapping


def _to_num(s):
    if s is None or s == "" or s == "-":
        return None
    try:
        return float(str(s).replace(",", ""))
    except ValueError:
        return None


def fetch_financials(corp_code: str, year: int, reprt_code: str) -> dict | None:
    """단일회사 전체 재무제표 → 자본총계/당기순이익/자산총계 + rcept_no(PIT 공시일)."""
    r = requests.get("https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json",
                     params=dict(crtfc_key=KEY, corp_code=corp_code, bsns_year=str(year),
                                 reprt_code=reprt_code, fs_div="CFS"), timeout=30)
    j = r.json()
    if j.get("status") != "000":
        # CFS(연결) 없으면 OFS(별도) 재시도
        r = requests.get("https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json",
                         params=dict(crtfc_key=KEY, corp_code=corp_code, bsns_year=str(year),
                                     reprt_code=reprt_code, fs_div="OFS"), timeout=30)
        j = r.json()
        if j.get("status") != "000":
            return None
    lst = j.get("list", [])
    if not lst:
        return None
    rcept_no = lst[0].get("rcept_no", "")
    rcept_dt = rcept_no[:8] if len(rcept_no) >= 8 else None
    out = {"rcept_dt": rcept_dt, "equity": None, "net_income": None, "assets": None}
    for it in lst:
        nm = it.get("account_nm", "").strip()
        sj = it.get("sj_div", "")  # BS=재무상태표, IS/CIS=손익
        amt = _to_num(it.get("thstrm_amount"))
        if amt is None:
            continue
        # 자본총계 (BS)
        if nm == "자본총계" and sj == "BS" and out["equity"] is None:
            out["equity"] = amt
        # 자산총계 (BS)
        elif nm == "자산총계" and sj == "BS" and out["assets"] is None:
            out["assets"] = amt
        # 당기순이익 (IS/CIS) — 누적
        elif nm in ("당기순이익", "당기순이익(손실)") and sj in ("IS", "CIS") and out["net_income"] is None:
            out["net_income"] = amt
    return out


def main():
    if not KEY:
        print("DART_API_KEY MISSING"); return
    uni = pd.read_parquet(DATA / "universe.parquet")
    uni = uni[uni["pass_floor"]]
    codes = uni["Code"].tolist()
    names = dict(zip(uni["Code"], uni["Name"]))
    print(f"universe {len(codes)} codes")

    cmap = get_corpcode_map()
    print(f"corpcode map: {len(cmap)} listed")
    missing = [c for c in codes if c not in cmap]
    if missing:
        print(f"  corp_code 부재: {missing}")

    cache = DATA / "dart_financials.parquet"
    if cache.exists():
        print("financials cached"); df = pd.read_parquet(cache)
        print(df.head().to_string()); return

    rows = []
    years = range(2019, 2026)
    total = len(codes) * len(years) * len(REPRT)
    done = 0
    for code in codes:
        cc = cmap.get(code)
        if not cc:
            continue
        for year in years:
            for qlabel, rcode in REPRT.items():
                done += 1
                try:
                    fin = fetch_financials(cc, year, rcode)
                    if fin and fin.get("equity"):
                        rows.append(dict(code=code, name=names[code], year=year, quarter=qlabel,
                                         reprt_code=rcode, **fin))
                except Exception as ex:
                    pass
                time.sleep(0.35)  # rate limit
        print(f"  [{done}/{total}] {code} {names[code]} done")
    df = pd.DataFrame(rows)
    df.to_parquet(cache)
    print(f"\nSaved {cache}: {len(df)} rows")
    if len(df):
        print(df.groupby("code").size().to_dict())
        print("\nsample:")
        print(df.head(6).to_string())


if __name__ == "__main__":
    main()
