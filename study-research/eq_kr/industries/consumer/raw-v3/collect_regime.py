# -*- coding: utf-8 -*-
"""collect_regime.py — semiconductor conditional IC 36셀 regime 데이터 수집 (S2 신규).

frame §M3 / plan §2 = regime 36셀 (Macro 4 × KRW 3 × 외국인flow 3).
기존 measure.py 에 conditional IC 분해 없음(SOXX regime 라벨 카운트만) → 본 수집기로 보강.

★데이터 소스 (전부 실재 확인 2026-06-05, 합성 금지):
  - Macro regime: FRED KORLOLITOAASTSAM (한국 OECD CLI amplitude-adjusted, 월별 2026-04까지)
      ★KORLOLITONOSTSAM(normalized)은 2024-01 중단 → amplitude-adj 버전이 대체(2026-04 가용).
  - KRW regime:   FRED DEXKOUS (USDKRW spot, 일별 1981~2026-05)
  - 외국인flow:    ECOS 802Y001 항목 0030000 (외국인 순매수 유가증권시장, 일별 2003~2026-06)
  - 보조(DRAM cycle proxy): FRED PCU334413334413 (반도체 PPI, 월별 2026-04)

산출: data/regime_series.parquet (일별 index, 컬럼 = cli_kr / usdkrw / foreign_net_kospi / semi_ppi)
      + data/regime_labels.parquet (월말 index, macro_regime / krw_regime / flow_regime 라벨)

★regime 라벨링 = ex-ante (진입시점 관측가능, 달력컷·사후분할 금지, frame G1).
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
START = "2018-01-01"   # 1년 lookback (yoy·12M 계산용 buffer)
END = "2026-05-29"


def fred_series(sid: str) -> pd.Series:
    """FRED 시리즈 fetch → date-indexed Series (실데이터)."""
    r = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params=dict(series_id=sid, api_key=FRED_KEY, file_type="json",
                    observation_start=START, observation_end=END),
        timeout=40,
    )
    j = r.json()
    obs = j.get("observations", [])
    idx, val = [], []
    for o in obs:
        v = o["value"]
        if v in (".", ""):
            continue
        idx.append(pd.Timestamp(o["date"]))
        val.append(float(v))
    return pd.Series(val, index=idx, name=sid).sort_index()


def ecos_daily_foreign_net() -> pd.Series:
    """ECOS 802Y001/0030000 외국인 순매수(유가증권시장) 일별 (실데이터)."""
    # ECOS 일별 = bgn/end YYYYMMDD, max 100000 rows. 분할 fetch (연도별).
    pieces = []
    for yr in range(2018, 2027):
        bgn = f"{yr}0101"; end = f"{yr}1231"
        url = (f"https://ecos.bok.or.kr/api/StatisticSearch/{ECOS_KEY}/json/kr/1/1000/"
               f"802Y001/D/{bgn}/{end}/0030000")
        try:
            r = requests.get(url, timeout=40)
            j = r.json()
            rows = j.get("StatisticSearch", {}).get("row", [])
            for row in rows:
                t = row.get("TIME", ""); dv = row.get("DATA_VALUE", "")
                if t and dv not in ("", None):
                    pieces.append((pd.Timestamp(f"{t[:4]}-{t[4:6]}-{t[6:8]}"), float(dv)))
        except Exception as e:
            print(f"  ECOS {yr} FAIL {repr(e)[:60]}")
        time.sleep(0.3)
    if not pieces:
        return pd.Series(dtype=float, name="foreign_net_kospi")
    s = pd.Series(dict(pieces)).sort_index()
    s.name = "foreign_net_kospi"
    return s


def build_regime_labels(reg: pd.DataFrame) -> pd.DataFrame:
    """월말 기준 ex-ante regime 라벨 (Macro 4 × KRW 3 × flow 3).
    ★진입시점 관측가능 = 당월 말까지의 정보만 사용(forward 누설 없음)."""
    m = reg.resample("ME").last()

    # ── Macro regime 4국면 (한국 CLI amplitude-adj level + 6M change) ──
    # OECD CLI 표준: level(100 기준 above/below) × momentum(6M Δ 부호)
    #   Recovery   = below 100 & rising   (저점 통과 회복)
    #   Reflation/Expansion = above 100 & rising (확장)
    #   Overheat   = above 100 & falling  (정점 둔화 시작)
    #   Slowdown   = below 100 & falling  (수축)
    # ★D축 PIT: OECD CLI 는 reference month 후 ~1-2개월 지연 발표(vintage).
    # reference month T 의 CLI 를 T 월말 의사결정에 쓰면 lookahead → 2개월 lag(보수) 적용.
    # (KRW=DEXKOUS 일별 / flow=ECOS 일별 = 실시간이라 lag 불필요, Macro 만 적용.)
    CLI_PUB_LAG = 2
    cli = m["cli_kr"].ffill().shift(CLI_PUB_LAG)
    cli_chg6 = cli - cli.shift(6)
    macro = pd.Series(index=m.index, dtype=object)
    above = cli >= 100
    rising = cli_chg6 > 0
    macro[(~above) & rising] = "Recovery"
    macro[above & rising] = "Reflation"
    macro[above & (~rising)] = "Overheat"
    macro[(~above) & (~rising)] = "Slowdown"

    # ── KRW regime 3 (USDKRW yoy) ──
    usdkrw = m["usdkrw"].ffill()
    krw_yoy = usdkrw / usdkrw.shift(12) - 1
    krw = pd.Series(index=m.index, dtype=object)
    krw[krw_yoy > 0.05] = "KRW_weak"      # 원화 약세 (USDKRW yoy > +5%)
    krw[krw_yoy < -0.05] = "KRW_strong"   # 원화 강세
    krw[(krw_yoy >= -0.05) & (krw_yoy <= 0.05)] = "KRW_neutral"

    # ── 외국인 flow regime 3 (28일 누계 순매수 z-score, frame 신지표#4) ──
    fnet = reg["foreign_net_kospi"].ffill()
    flow_28d = fnet.rolling(28).sum()
    flow_z = (flow_28d - flow_28d.rolling(252).mean()) / flow_28d.rolling(252).std()
    flow_z_m = flow_z.resample("ME").last()
    flow = pd.Series(index=m.index, dtype=object)
    flow[flow_z_m > 1.0] = "flow_strong_buy"
    flow[flow_z_m < -1.0] = "flow_sell"
    flow[(flow_z_m >= -1.0) & (flow_z_m <= 1.0)] = "flow_neutral"

    labels = pd.DataFrame({
        "macro_regime": macro, "krw_regime": krw, "flow_regime": flow,
        "cli_kr": cli, "cli_chg6": cli_chg6, "krw_yoy": krw_yoy, "flow_z": flow_z_m,
    })
    return labels


def main():
    print("[1/4] FRED Macro CLI (KORLOLITOAASTSAM, amplitude-adj 대체) ...")
    cli = fred_series("KORLOLITOAASTSAM")
    print(f"  CLI: {cli.index.min().date()}~{cli.index.max().date()} n={len(cli)}")

    print("[2/4] FRED USDKRW (DEXKOUS) ...")
    usdkrw = fred_series("DEXKOUS")
    print(f"  USDKRW: {usdkrw.index.min().date()}~{usdkrw.index.max().date()} n={len(usdkrw)}")

    print("[3/4] FRED 반도체 PPI (PCU334413334413, DRAM cycle proxy) ...")
    ppi = fred_series("PCU334413334413")
    print(f"  semi PPI: {ppi.index.min().date()}~{ppi.index.max().date()} n={len(ppi)}")

    print("[4/4] ECOS 외국인 순매수 일별 (802Y001/0030000) ...")
    fnet = ecos_daily_foreign_net()
    print(f"  foreign net: {fnet.index.min().date()}~{fnet.index.max().date()} n={len(fnet)}")

    # 일별 index 통합 (forward-fill 월별 시리즈)
    full_idx = pd.date_range(START, END, freq="D")
    reg = pd.DataFrame(index=full_idx)
    reg["cli_kr"] = cli.reindex(full_idx, method="ffill")
    reg["usdkrw"] = usdkrw.reindex(full_idx, method="ffill")
    reg["semi_ppi"] = ppi.reindex(full_idx, method="ffill")
    reg["foreign_net_kospi"] = fnet.reindex(full_idx)  # 일별 raw (ffill 은 라벨링 단계)
    reg.to_parquet(DATA / "regime_series.parquet")
    print(f"\nSaved regime_series.parquet {reg.shape}")

    labels = build_regime_labels(reg)
    labels.to_parquet(DATA / "regime_labels.parquet")
    print(f"Saved regime_labels.parquet {labels.shape}")

    # ── regime 분포 요약 (2019~ 측정구간) ──
    sub = labels.loc["2019-01-01":]
    print("\n=== regime 분포 (2019~, 월말) ===")
    for col in ["macro_regime", "krw_regime", "flow_regime"]:
        print(f"  {col}: {sub[col].value_counts().to_dict()}")
    # 36셀 교차 N
    cross = sub.dropna(subset=["macro_regime", "krw_regime", "flow_regime"])
    cell = cross.groupby(["macro_regime", "krw_regime", "flow_regime"]).size()
    print(f"\n=== 36셀 중 N>0 cell 수: {len(cell)} / 36 ===")
    print(f"  N>=24 cell: {(cell >= 24).sum()} / N>=12: {(cell >= 12).sum()} / N>=6: {(cell >= 6).sum()}")
    print(f"  최대 cell N={cell.max()} / 최소={cell.min()} / 중앙={int(cell.median())}")
    print("  ★N<24 다수 예상 → cell collapse (frame §M3: 인접 merge → flow 3셀 fallback)")


if __name__ == "__main__":
    main()
