# -*- coding: utf-8 -*-
"""collect_regime.py — financial conditional IC regime 데이터 수집 (S2 신규).

반도체 collect_regime.py 재사용(Macro CLI × KRW × 외국인flow) + ★금융 특화 금리 regime 축 추가.
금융 = 금리·신용 regime 민감 spread_driven 산업 → ★금리 regime 이 NIM 본질 driver (반도체 DRAM cycle 대응).

★데이터 소스 (전부 실재 확인 2026-06-05, 합성 금지):
  - Macro regime: FRED KORLOLITOAASTSAM (한국 OECD CLI amplitude-adj, 월별 2026-04)
  - KRW regime:   FRED DEXKOUS (USDKRW spot, 일별)
  - 외국인flow:    ECOS 802Y001/0030000 (외국인 순매수 유가증권시장, 일별)
  - ★금리 regime (financial 특화, ECOS 817Y002 시장금리 일별):
      국고채10Y(010210000) / 국고채2Y(010195000, 2019초 결측→3Y 대체) / 국고채3Y(010200000)
      회사채AA-3Y(010300000) → term spread(10Y-3Y) + rate momentum(3Y 6M Δ) + credit spread(AA−-국고3Y)

산출: data/regime_series.parquet (일별) + data/regime_labels.parquet (월말 라벨)
      라벨 = macro_regime / krw_regime / flow_regime + ★rate_regime / curve_regime / credit_regime

★regime 라벨링 = ex-ante (진입시점 관측가능, 달력컷·사후분할 금지, frame G1).
★금리 regime 부호 사전확약(theory-notes M1/M2/M4):
  - rate_up (국고3Y 6M Δ > +0.3%p) = 은행/보험 NIM 수혜(+), 증권(−). rate_down 반대.
  - curve_steepen (term spread 상위 30%) = 은행 NIM 개선(+).
  - credit_wide (credit spread 상위 30%) = PF/신용위험(−).
"""
from __future__ import annotations
import sys, io, os, json, time
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
ECOS_KEY = os.environ.get("ECOS_API_KEY", "")
START = "2018-01-01"
END = "2026-05-29"


def fred_series(sid: str) -> pd.Series:
    r = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params=dict(series_id=sid, api_key=FRED_KEY, file_type="json",
                    observation_start=START, observation_end=END),
        timeout=40,
    )
    obs = r.json().get("observations", [])
    idx, val = [], []
    for o in obs:
        v = o["value"]
        if v in (".", ""):
            continue
        idx.append(pd.Timestamp(o["date"])); val.append(float(v))
    return pd.Series(val, index=idx, name=sid).sort_index()


def ecos_daily(stat: str, item: str, name: str) -> pd.Series:
    """ECOS 일별 시리즈 (연도별 분할 fetch)."""
    pieces = []
    for yr in range(2018, 2027):
        url = (f"https://ecos.bok.or.kr/api/StatisticSearch/{ECOS_KEY}/json/kr/1/1000/"
               f"{stat}/D/{yr}0101/{yr}1231/{item}")
        try:
            j = requests.get(url, timeout=40).json()
            rows = j.get("StatisticSearch", {}).get("row", [])
            for row in rows:
                t = row.get("TIME", ""); dv = row.get("DATA_VALUE", "")
                if t and dv not in ("", None):
                    pieces.append((pd.Timestamp(f"{t[:4]}-{t[4:6]}-{t[6:8]}"), float(dv)))
        except Exception as e:
            print(f"  ECOS {name} {yr} FAIL {repr(e)[:50]}")
        time.sleep(0.25)
    if not pieces:
        return pd.Series(dtype=float, name=name)
    s = pd.Series(dict(pieces)).sort_index(); s.name = name
    return s


def build_regime_labels(reg: pd.DataFrame) -> pd.DataFrame:
    """월말 ex-ante regime 라벨. ★진입시점 관측가능."""
    m = reg.resample("ME").last()

    # ── Macro regime 4 (반도체 미러, CLI amplitude-adj + 2M pub lag) ──
    CLI_PUB_LAG = 2
    cli = m["cli_kr"].ffill().shift(CLI_PUB_LAG)
    cli_chg6 = cli - cli.shift(6)
    macro = pd.Series(index=m.index, dtype=object)
    above = cli >= 100; rising = cli_chg6 > 0
    macro[(~above) & rising] = "Recovery"
    macro[above & rising] = "Reflation"
    macro[above & (~rising)] = "Overheat"
    macro[(~above) & (~rising)] = "Slowdown"

    # ── KRW regime 3 (USDKRW yoy) ──
    usdkrw = m["usdkrw"].ffill()
    krw_yoy = usdkrw / usdkrw.shift(12) - 1
    krw = pd.Series(index=m.index, dtype=object)
    krw[krw_yoy > 0.05] = "KRW_weak"
    krw[krw_yoy < -0.05] = "KRW_strong"
    krw[(krw_yoy >= -0.05) & (krw_yoy <= 0.05)] = "KRW_neutral"

    # ── 외국인 flow regime 3 (28일 누계 z) ──
    fnet = reg["foreign_net_kospi"].ffill()
    flow_28d = fnet.rolling(28).sum()
    flow_z = (flow_28d - flow_28d.rolling(252).mean()) / flow_28d.rolling(252).std()
    flow_z_m = flow_z.resample("ME").last()
    flow = pd.Series(index=m.index, dtype=object)
    flow[flow_z_m > 1.0] = "flow_strong_buy"
    flow[flow_z_m < -1.0] = "flow_sell"
    flow[(flow_z_m >= -1.0) & (flow_z_m <= 1.0)] = "flow_neutral"

    # ── ★금리 rate_regime 3 (국고채3Y 6M Δ, theory M2: 은행/보험+ 증권−) ──
    # ★ex-ante: 진입시점(월말)까지 관측된 금리 변화. 일별 금리 = 실시간(발표지연 無).
    ktb3 = m["ktb3y"].ffill()
    rate_chg6 = ktb3 - ktb3.shift(6)   # 6M 금리변화 (금리 상승 '국면' 포착)
    rate = pd.Series(index=m.index, dtype=object)
    rate[rate_chg6 > 0.3] = "rate_up"       # 6M +0.3%p↑ = 금리 상승 국면
    rate[rate_chg6 < -0.3] = "rate_down"
    rate[(rate_chg6 >= -0.3) & (rate_chg6 <= 0.3)] = "rate_flat"

    # ── ★curve_regime 3 (term spread 10Y-3Y, 과거 1Y 분위, theory M1: steepen→은행NIM+) ──
    # ★국고채2Y 가 2019초 결측 → 10Y-3Y term spread (3Y = 단기 proxy, 일관 가용).
    term = m["ktb10y"].ffill() - m["ktb3y"].ffill()
    term_pct = term.rolling(12).apply(lambda w: (w.iloc[-1] >= np.nanpercentile(w, 70)) * 1.0
                                      if w.notna().sum() >= 6 else np.nan, raw=False)
    term_lo = term.rolling(12).apply(lambda w: (w.iloc[-1] <= np.nanpercentile(w, 30)) * 1.0
                                     if w.notna().sum() >= 6 else np.nan, raw=False)
    curve = pd.Series(index=m.index, dtype=object)
    curve[term_pct == 1.0] = "curve_steepen"   # 상위 30% = steepening
    curve[term_lo == 1.0] = "curve_flatten"     # 하위 30% = flattening/inverted
    curve[(term_pct == 0.0) & (term_lo == 0.0)] = "curve_neutral"

    # ── ★credit_regime 2 (credit spread AA−-국고3Y, 과거 1Y 분위, theory M4: wide→금융−) ──
    cspread = m["corp_aa3y"].ffill() - m["ktb3y"].ffill()
    cs_hi = cspread.rolling(12).apply(lambda w: (w.iloc[-1] >= np.nanpercentile(w, 70)) * 1.0
                                      if w.notna().sum() >= 6 else np.nan, raw=False)
    credit = pd.Series(index=m.index, dtype=object)
    credit[cs_hi == 1.0] = "credit_wide"        # 상위 30% = 신용위험 확대
    credit[cs_hi == 0.0] = "credit_normal"

    return pd.DataFrame({
        "macro_regime": macro, "krw_regime": krw, "flow_regime": flow,
        "rate_regime": rate, "curve_regime": curve, "credit_regime": credit,
        "cli_kr": cli, "krw_yoy": krw_yoy, "flow_z": flow_z_m,
        "ktb3y": ktb3, "ktb10y": m["ktb10y"].ffill(),
        "rate_chg6": rate_chg6, "term_spread": term, "credit_spread": cspread,
    })


def main():
    print("[1/7] FRED Macro CLI (KORLOLITOAASTSAM) ...")
    cli = fred_series("KORLOLITOAASTSAM")
    print(f"  CLI: {cli.index.min().date()}~{cli.index.max().date()} n={len(cli)}")
    print("[2/7] FRED USDKRW (DEXKOUS) ...")
    usdkrw = fred_series("DEXKOUS")
    print(f"  USDKRW: {usdkrw.index.min().date()}~{usdkrw.index.max().date()} n={len(usdkrw)}")
    print("[3/7] ECOS 외국인 순매수 (802Y001/0030000) ...")
    fnet = ecos_daily("802Y001", "0030000", "foreign_net_kospi")
    print(f"  foreign net: {fnet.index.min().date()}~{fnet.index.max().date()} n={len(fnet)}")
    print("[4/7] ECOS 국고채10Y (817Y002/010210000) ...")
    ktb10 = ecos_daily("817Y002", "010210000", "ktb10y")
    print(f"  KTB10Y: {ktb10.index.min().date()}~{ktb10.index.max().date()} n={len(ktb10)}")
    print("[5/7] ECOS 국고채3Y (817Y002/010200000) ...")
    ktb3 = ecos_daily("817Y002", "010200000", "ktb3y")
    print(f"  KTB3Y: {ktb3.index.min().date()}~{ktb3.index.max().date()} n={len(ktb3)}")
    print("[6/7] ECOS 회사채AA-3Y (817Y002/010300000) ...")
    corp = ecos_daily("817Y002", "010300000", "corp_aa3y")
    print(f"  Corp AA-3Y: {corp.index.min().date()}~{corp.index.max().date()} n={len(corp)}")
    print("[7/7] 통합 + 라벨링 ...")

    full_idx = pd.date_range(START, END, freq="D")
    reg = pd.DataFrame(index=full_idx)
    reg["cli_kr"] = cli.reindex(full_idx, method="ffill")
    reg["usdkrw"] = usdkrw.reindex(full_idx, method="ffill")
    reg["foreign_net_kospi"] = fnet.reindex(full_idx)
    reg["ktb10y"] = ktb10.reindex(full_idx, method="ffill")
    reg["ktb3y"] = ktb3.reindex(full_idx, method="ffill")
    reg["corp_aa3y"] = corp.reindex(full_idx, method="ffill")
    reg.to_parquet(DATA / "regime_series.parquet")
    print(f"\nSaved regime_series.parquet {reg.shape}")

    labels = build_regime_labels(reg)
    labels.to_parquet(DATA / "regime_labels.parquet")
    print(f"Saved regime_labels.parquet {labels.shape}")

    sub = labels.loc["2019-01-01":]
    print("\n=== regime 분포 (2019~, 월말) ===")
    for col in ["macro_regime", "krw_regime", "flow_regime",
                "rate_regime", "curve_regime", "credit_regime"]:
        print(f"  {col}: {sub[col].value_counts().to_dict()}")
    # 합성 지문 검사
    print("\n=== 합성 지문 (역사 이벤트 실재) ===")
    print(f"  USDKRW 2022-10 max: {reg['usdkrw'].loc['2022-10-01':'2022-10-31'].max():.1f} (기대 ~1440)")
    print(f"  KTB10Y 2020-08 min: {reg['ktb10y'].loc['2020-07-01':'2020-09-30'].min():.3f} (기대 저금리 ~1.3)")
    print(f"  KTB10Y 2022-10 max: {reg['ktb10y'].loc['2022-09-01':'2022-11-30'].max():.3f} (기대 금리쇼크 ~4.3)")
    print(f"  credit spread 2022-11 max: {(reg['corp_aa3y']-reg['ktb3y']).loc['2022-10-01':'2022-12-31'].max():.3f} (기대 레고랜드 확대)")


if __name__ == "__main__":
    main()
